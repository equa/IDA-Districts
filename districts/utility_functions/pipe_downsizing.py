"""Pressure balancing of customers by reducing pipe diameters.

Extended result structure:
    c_lid = {cid : [dp, {lid : [dp_spez, mdot]}]}
    dp      ... pressure difference over the substation p_sup - p_ret [Pa]
    dp_spez ... specific friction pressure loss of the line (supply + return pipe) [Pa/m]
    mdot    ... part of the customer mass flow transported through the line [kg/s]

Procedure (optimizePipeDiameters):
    0. optional pre-sizing: smallest pipe with a specific pressure loss <= dp_spez_setpoint for the
       mass flow of the line (sum of the customer mass flows in c_lid); presize_only=True stops here
    1. customer with the highest dp
    2. line of this customer with the lowest dp_spez
    3. next smaller pipe dimension (same pipe construction) for supply and return pipe
    4. new pressure loss of the line with unchanged mass flow, the difference is subtracted from
       dp of all customers supplied via this line
    5. repeat until dp of all customers is within the tolerance above the minimal dp (tol_above); customers
       which cannot be balanced because of the discrete pipe dimensions remain above (see quota)
The specific pressure loss is calculated with Darcy-Weisbach / Colebrook, because the simulated
line pressures contain the geodetic pressure difference.
"""
import json
import math
from collections import defaultdict

from .flow_tracing import getCustomerLineMdot, getFeatureConnTables, getTimeSeries


def waterProperties(temp):
    """Returns density [kg/m3] and dynamic viscosity [Pa s] of water at temp [degC]."""
    rho = 1000.0 * (1 - (temp + 288.9414) / (508929.2 * (temp + 68.12963)) * (temp - 3.9863) ** 2)
    mu = 2.414e-5 * 10 ** (247.8 / (temp + 273.15 - 140.0))
    return rho, mu


def frictionFactor(Re, eps_rel):
    """Darcy friction factor (laminar 64/Re, turbulent Colebrook-White)."""
    if Re <= 0:
        return 0.0
    if Re < 2300:
        return 64.0 / Re
    f = 0.25 / math.log10(eps_rel / 3.7 + 5.74 / Re ** 0.9) ** 2  # Swamee-Jain as start value
    for _ in range(20):
        f_new = (-2.0 * math.log10(eps_rel / 3.7 + 2.51 / (Re * math.sqrt(f)))) ** -2
        if abs(f_new - f) < 1e-10:
            break
        f = f_new
    return f_new


def specificPressureLoss(mdot, d, k, temp):
    """Returns (friction pressure loss [Pa/m], velocity [m/s]) of a pipe."""
    mdot = abs(mdot)
    if mdot <= 0 or d <= 0:
        return 0.0, 0.0
    rho, mu = waterProperties(temp)
    v = mdot / (rho * math.pi * d ** 2 / 4)
    Re = rho * v * d / mu
    return frictionFactor(Re, k / d) / d * rho * v ** 2 / 2, v


def getPipeCatalog(cur):
    """Returns {pipe_id: {'d', 'k', 'construction', 'name'}} of the table pipes."""
    cur.execute("""SELECT id, name, innerpipediameter, piperoughnessfactor, pipe_construction_id FROM public.pipes WHERE innerpipediameter > 0;""")
    return {int(row['id']): {'d': float(row['innerpipediameter']), 'k': float(row['piperoughnessfactor'] or 0.0),
        'construction': row['pipe_construction_id'], 'name': row['name']} for row in cur.fetchall()}


def getNextSmallerPipe(pipe_id, catalog):
    """Next smaller inner diameter of the same pipe construction or None."""
    pipe = catalog[pipe_id]
    smaller = [(p['d'], pid) for pid, p in catalog.items() if p['construction'] == pipe['construction'] and p['d'] < pipe['d']]
    return max(smaller)[1] if smaller else None


def getPipeBundles(cur):
    """Returns {pipe_bundle_type_id: {sequence: pipe_id}}."""
    cur.execute("""SELECT pipe_bundle_type_id, sequence, pipe_id FROM public.bundle_pipes;""")
    bundles = defaultdict(dict)
    for row in cur.fetchall():
        bundles[row['pipe_bundle_type_id']][row['sequence']] = int(row['pipe_id'])
    return dict(bundles)


def getLineData(cur, config, time, network=1, sequences=(1, 2), default_temps=(70.0, 40.0)):
    """Returns {lid: {'length', 'bundle', 'pipes': {seq: {'pipe_id', 'mdot', 'temp'}}}} at the given time."""
    v = config['versionName']
    cur.execute("""SELECT l.id, ST_3DLength(l.geom) AS length, l.pipe_bundle_type_id, bp.sequence, bp.pipe_id
    FROM "{}".lines l, public.bundle_pipes bp
    WHERE bp.pipe_bundle_type_id = l.pipe_bundle_type_id AND l.network = {} AND bp.sequence IN ({});""".format(v, int(network), ','.join(str(int(s)) for s in sequences)))  # nosec B608
    lines = {}
    for row in cur.fetchall():
        line = lines.setdefault(row['id'], {'length': float(row['length']), 'bundle': row['pipe_bundle_type_id'], 'pipes': {}})
        line['pipes'][row['sequence']] = {'pipe_id': int(row['pipe_id']), 'mdot': 0.0, 'temp': None}

    cur.execute("""SELECT table_name FROM information_schema.tables WHERE table_schema = %s;""", (v,))
    tables = {row['table_name'] for row in cur.fetchall()}
    for i, seq in enumerate(sequences):
        for var in ('mdot', 'temp'):
            table = 'line_s_{}${}'.format(var, seq)
            if table not in tables:
                continue
            cur.execute("""SELECT fid, AVG("${}") AS val FROM "{}"."{}" WHERE time = %s GROUP BY fid;""".format(var, v, table), (time,))  # nosec B608
            for row in cur.fetchall():
                if row['fid'] in lines and seq in lines[row['fid']]['pipes'] and row['val'] is not None:
                    lines[row['fid']]['pipes'][seq][var] = float(row['val'])
        for line in lines.values():
            if seq in line['pipes'] and line['pipes'][seq]['temp'] is None:
                line['pipes'][seq]['temp'] = default_temps[min(i, len(default_temps) - 1)]
    return lines


def lineSpecificPressureLoss(line, catalog, pipe_ids=None):
    """Returns (dp_spez supply + return [Pa/m], max. velocity [m/s]); pipe_ids={seq: pipe_id} overrides the actual pipes."""
    dp_spez = 0.0
    v_max = 0.0
    for seq, pipe in line['pipes'].items():
        p = catalog[pipe_ids[seq] if pipe_ids else pipe['pipe_id']]
        r, v = specificPressureLoss(pipe['mdot'], p['d'], p['k'], pipe['temp'])
        dp_spez += r
        v_max = max(v_max, v)
    return dp_spez, v_max


def getCustomerDp(cur, config, time, network=1):
    """Returns {cid: p_sup - p_ret} at the substations (result tables derived from the customer templates)."""
    c_tables = getFeatureConnTables(cur, config, 'customer', 'p', network)
    p_sup = getTimeSeries(cur, config, {cid: t[0] for cid, t in c_tables.items()}, '$p', time).get(time, {})
    p_ret = getTimeSeries(cur, config, {cid: t[1] for cid, t in c_tables.items()}, '$p', time).get(time, {})
    return {cid: p - p_ret[cid] for cid, p in p_sup.items() if cid in p_ret}


def buildCLid(c_lid_mdot, dp_c, dp_spez):
    """Combines to c_lid = {cid: [dp, {lid: [dp_spez, mdot]}]}."""
    return {cid: [dp_c.get(cid), {lid: [dp_spez.get(lid), m] for lid, m in lids.items()}] for cid, lids in c_lid_mdot.items()}


def getCustomerLinePressure(cur, config, network=1, **kwargs):
    """Flow tracing (see flow_tracing.getCustomerLineMdot) extended by dp of the customers and dp_spez of the lines.
    Returns the result dict of getCustomerLineMdot with c_lid = {cid: [dp, {lid: [dp_spez, mdot]}]}
    and additionally 'c_lid_mdot', 'lines', 'catalog', 'dp_spez'."""
    res = getCustomerLineMdot(cur, config, network=network, **kwargs)
    catalog = getPipeCatalog(cur)
    lines = getLineData(cur, config, res['time'], network)
    dp_spez = {lid: lineSpecificPressureLoss(line, catalog)[0] for lid, line in lines.items()}
    dp_c = getCustomerDp(cur, config, res['time'], network)
    res['c_lid_mdot'] = res['c_lid']
    res['c_lid'] = buildCLid(res['c_lid_mdot'], dp_c, dp_spez)
    res.update({'lines': lines, 'catalog': catalog, 'dp_spez': dp_spez})
    return res


def presizePipes(c_lid, lines, catalog, dp_spez_setpoint):
    """Pre-sizing: for every line the smallest pipe of the same construction whose specific pressure loss [Pa/m]
    does not exceed dp_spez_setpoint in each pipe (supply and return get the same dimension; largest pipe if none
    fits). The mass flow of a line is the sum of the customer mass flows in c_lid = {cid: [dp, {lid: [dp_spez, mdot]}]}.
    Lines without mass flow keep their pipes. Returns {lid: {seq: pipe_id}}."""
    mdot = defaultdict(float)
    for _, lids in c_lid.values():
        for lid, (_, m) in lids.items():
            mdot[lid] += m
    pipes = {}
    for lid, line in lines.items():
        pipes[lid] = {seq: pipe['pipe_id'] for seq, pipe in line['pipes'].items()}
        if mdot.get(lid, 0.0) <= 0:
            continue
        constructions = {catalog[pipe['pipe_id']]['construction'] for pipe in line['pipes'].values()}
        candidates = sorted((p['d'], pid) for pid, p in catalog.items() if p['construction'] in constructions)
        fitting = [pid for d, pid in candidates
            if all(specificPressureLoss(mdot[lid], d, catalog[pid]['k'], pipe['temp'])[0] <= dp_spez_setpoint for pipe in line['pipes'].values())]
        pid = fitting[0] if fitting else candidates[-1][1]
        pipes[lid] = {seq: pid for seq in line['pipes']}
    return pipes


def optimizePipeDiameters(c_lid, lines, catalog, tol_above=500.0, tol_below=0.0, dp_target=None, cid_weak=None, weighted=False, v_max=None, dp_spez_max=None,
        dp_spez_setpoint=None, presize_only=False, max_iter=1000):
    """Iterative reduction of pipe diameters until dp of all customers is within dp_target ... dp_target + tol_above
    (dp_target default: minimal dp of all customers). The mass flows are kept constant.

    tol_above:   tolerance of exceedance [Pa]: a customer with dp <= dp_target + tol_above is balanced.
    tol_below:   tolerance of undershoot [Pa]: a change is rejected if dp of an affected customer would fall
                 below dp_target - tol_below (0 -> no customer gets worse than the weak point).

    weighted:    False -> the additional pressure loss of a line is subtracted completely from dp of every
                 customer supplied via the line; True -> weighted with the share mdot_line / mdot_customer
                 (for customers supplied via parallel strands).
    v_max, dp_spez_max: optional limits [m/s], [Pa/m] for the new pipe.
    cid_weak:    weak point customer (default: customer with the minimal dp after the pre-sizing); the lines
                 supplying it are not changed.
    dp_spez_setpoint: optional pre-sizing [Pa/m per pipe] (see presizePipes) before the iteration; dp of the
                 customers is corrected by the changed pressure losses of the lines.
    presize_only: True -> only the pre-sizing with dp_spez_setpoint is done, no iterative balancing.
    The line changed last is only changed again if no other line of the customer is possible.
    Returns dict {'c_lid', 'pipes', 'presize', 'history', 'converged', 'dp_target', 'cid_weak', 'spread', 'blocked',
    'quota'} with quota = share of customers within dp_target - tol_below ... dp_target + tol_above."""
    dp = {cid: val[0] for cid, val in c_lid.items() if val[0] is not None}
    pipes = {lid: {seq: p['pipe_id'] for seq, p in line['pipes'].items()} for lid, line in lines.items()}
    dp_spez = {lid: lineSpecificPressureLoss(lines[lid], catalog, pipes[lid])[0] for lid in lines}
    # customers per line with their mdot share (the house connection line carries the full customer mass flow)
    line_customers = defaultdict(dict)
    for cid, (_, lids) in c_lid.items():
        mdot_tot = max(abs(m) for _, m in lids.values()) if lids else 0.0
        for lid, (_, m) in lids.items():
            line_customers[lid][cid] = m / mdot_tot if mdot_tot else 0.0

    presize = []
    if dp_spez_setpoint:
        for lid, new in presizePipes(c_lid, lines, catalog, dp_spez_setpoint).items():
            if new == pipes[lid]:
                continue
            dp_spez_new = lineSpecificPressureLoss(lines[lid], catalog, new)[0]
            ddp = (dp_spez_new - dp_spez[lid]) * lines[lid]['length']
            for c, share in line_customers[lid].items():
                if c in dp:
                    dp[c] -= ddp * (share if weighted else 1.0)
            presize.append({'lid': lid, 'pipes_old': [catalog[p]['name'] for p in pipes[lid].values()], 'pipes_new': [catalog[p]['name'] for p in new.values()],
                'dp_spez_old': dp_spez[lid], 'dp_spez_new': dp_spez_new, 'ddp_line': ddp, 'customers': sorted(line_customers[lid])})
            pipes[lid] = new
            dp_spez[lid] = dp_spez_new

    if cid_weak is None:
        cid_weak = min(dp, key=dp.get)
    if dp_target is None:
        dp_target = dp[cid_weak]
    lids_weak = set(c_lid[cid_weak][1]) if cid_weak in c_lid else set()
    lid_last = None
    history = []
    blocked = set()
    converged = False
    if presize_only and not dp_spez_setpoint:
        raise ValueError('presize_only needs dp_spez_setpoint')
    for it in range(1, (0 if presize_only else max_iter) + 1):
        if max(dp.values()) - dp_target <= tol_above:
            converged = True
            break
        applied = False
        for cid in sorted((c for c in dp if dp[c] - dp_target > tol_above and c not in blocked), key=dp.get, reverse=True):
            for lid in sorted((lid for lid in c_lid[cid][1] if lid in lines and lid not in lids_weak), key=lambda lid: (lid == lid_last, dp_spez[lid])):
                new = {seq: getNextSmallerPipe(pid, catalog) for seq, pid in pipes[lid].items()}
                if None in new.values():
                    continue
                dp_spez_new, v_new = lineSpecificPressureLoss(lines[lid], catalog, new)
                if (v_max and v_new > v_max) or (dp_spez_max and dp_spez_new > dp_spez_max):
                    continue
                ddp = (dp_spez_new - dp_spez[lid]) * lines[lid]['length']
                delta = {c: ddp * (share if weighted else 1.0) for c, share in line_customers[lid].items() if c in dp}
                if any(dp[c] - d < dp_target - tol_below for c, d in delta.items()):
                    continue
                for c, d in delta.items():
                    dp[c] -= d
                history.append({'iter': it, 'cid': cid, 'lid': lid,
                    'pipes_old': [catalog[p]['name'] for p in pipes[lid].values()], 'pipes_new': [catalog[p]['name'] for p in new.values()],
                    'dp_spez_old': dp_spez[lid], 'dp_spez_new': dp_spez_new, 'ddp_line': ddp, 'v_new': v_new, 'customers': sorted(delta)})
                pipes[lid] = new
                dp_spez[lid] = dp_spez_new
                lid_last = lid
                applied = True
                break
            if applied:
                break
            blocked.add(cid)  # no feasible line left for this customer (dp only decreases, so it stays blocked)
        if not applied:
            break

    converged = max(dp.values()) - dp_target <= tol_above
    c_lid_new = {cid: [dp.get(cid), {lid: [dp_spez.get(lid, val), m] for lid, (val, m) in lids.items()}] for cid, (_, lids) in c_lid.items()}
    return {'c_lid': c_lid_new, 'pipes': pipes, 'presize': presize, 'history': history, 'converged': converged, 'dp_target': dp_target, 'cid_weak': cid_weak,
        'spread': max(dp.values()) - min(dp.values()), 'blocked': sorted(blocked),
        'quota': sum(1 for val in dp.values() if dp_target - tol_below <= val <= dp_target + tol_above) / len(dp)}


def changedPipeBundles(lines, pipes, bundles):
    """Returns {lid: (bundle_old, bundle_new or None, {seq: pipe_id})} for all changed lines; bundle_new is
    None if no existing pipe bundle type matches the new pipes."""
    result = {}
    for lid, new in pipes.items():
        if new != {seq: p['pipe_id'] for seq, p in lines[lid]['pipes'].items()}:
            match = [bid for bid, b in bundles.items() if b == new]
            result[lid] = (lines[lid]['bundle'], match[0] if match else None, new)
    return result


def saveCLidPressure(c_lid, path):
    """Saves c_lid = {cid: [dp, {lid: [dp_spez, mdot]}]} as .json."""
    with open(path, 'w', encoding='utf-8') as f:
        json.dump({str(cid): [dp, {str(lid): val for lid, val in lids.items()}] for cid, (dp, lids) in c_lid.items()}, f, indent=1)


def loadCLidPressure(path):
    """Loads c_lid saved with saveCLidPressure, keys are returned as integers."""
    with open(path, encoding='utf-8') as f:
        return {int(cid): [dp, {int(lid): val for lid, val in lids.items()}] for cid, (dp, lids) in json.load(f).items()}


def getOrCreatePipeBundles(cur, lines, pipes):
    """Returns {lid: pipe_bundle_type_id} for all lines whose pipes changed. Missing pipe bundle types are created
    in public.pipe_bundle_types / public.bundle_pipes (x, y, ambient taken over from the original bundle).
    Returns (line_bundles, new_bundle_ids)."""
    cur.execute("""SELECT pipe_bundle_type_id, sequence, pipe_id, x, y, ambient FROM public.bundle_pipes;""")
    bundle_rows = defaultdict(dict)
    for row in cur.fetchall():
        bundle_rows[row['pipe_bundle_type_id']][row['sequence']] = row
    bundles = {bid: {seq: int(row['pipe_id']) for seq, row in seqs.items()} for bid, seqs in bundle_rows.items()}
    line_bundles = {}
    new_bundle_ids = []
    for lid, new in pipes.items():
        if new == {seq: p['pipe_id'] for seq, p in lines[lid]['pipes'].items()}:
            continue
        match = [bid for bid, b in sorted(bundles.items()) if b == new]
        if match:
            line_bundles[lid] = match[0]
            continue
        cur.execute("""SELECT COALESCE(MAX(id), 0) + 1 AS id FROM public.pipe_bundle_types;""")
        bid = cur.fetchone()['id']
        cur.execute("""INSERT INTO public.pipe_bundle_types (id, description) VALUES (%s, %s);""", (bid, 'pipes: ' + ','.join(str(new[seq]) for seq in sorted(new))))
        orig = bundle_rows.get(lines[lid]['bundle'], {})
        for seq in sorted(new):
            cur.execute("""SELECT COALESCE(MAX(id), 0) + 1 AS id FROM public.bundle_pipes;""")
            bp_id = cur.fetchone()['id']
            o = orig.get(seq) or {'x': 0.25 * (seq - 1), 'y': 1, 'ambient': 2}
            cur.execute("""INSERT INTO public.bundle_pipes (id, pipe_bundle_type_id, sequence, pipe_id, x, y, ambient) VALUES (%s, %s, %s, %s, %s, %s, %s);""",
                (bp_id, bid, seq, new[seq], o['x'], o['y'], o['ambient']))
        bundles[bid] = dict(new)
        bundle_rows[bid] = {seq: {'x': orig.get(seq, {}).get('x', 0.25 * (seq - 1)), 'y': 1, 'ambient': 2, 'pipe_id': new[seq]} for seq in new}
        new_bundle_ids.append(bid)
        line_bundles[lid] = bid
    return line_bundles, new_bundle_ids


def createVersionWithPipes(cur, config, plugin_dir, lines, pipes, new_version, description='', username=None, password=None):
    """Creates a child version of config['versionName'] (like 'add version' in the project handling dialog) and
    assigns the new pipe bundles to the lines of the new version. Missing pipe bundle types are created.
    Needs a DB user with write permissions and the PostgreSQL binaries (pg_dump, psql) of config['pathPostgresql'].
    Note: the result tables of the base version are copied as well, they do not match the new pipes until
    the new version is simulated.
    Returns (line_bundles, new_bundle_ids)."""
    from .db import copy_schema
    from .utility import sanitize_pg_identifier
    from ..ida_ph import checkIfVersionIsNew, copyVersionFiles

    base_version = config['versionName']
    if sanitize_pg_identifier(new_version) != new_version:
        raise ValueError('Invalid version name: {}'.format(new_version))
    if not checkIfVersionIsNew(cur, new_version):
        raise ValueError('Version {} does already exist'.format(new_version))
    if username is None or password is None:
        from qgis.core import QgsApplication, QgsAuthMethodConfig
        auth_cfg = QgsAuthMethodConfig()
        QgsApplication.authManager().loadAuthenticationConfig(config['auth_id'], auth_cfg, True)
        username, password = auth_cfg.config('username'), auth_cfg.config('password')

    line_bundles, new_bundle_ids = getOrCreatePipeBundles(cur, lines, pipes)

    cur.execute("""SELECT id FROM public.versionhandling WHERE name = %s;""", (base_version,))
    row = cur.fetchone()
    cur.execute("""INSERT INTO public.versionhandling (name, id_base, description) VALUES (%s, %s, %s);""", (new_version, row['id'] if row else 0, description))
    copy_schema(base_version, new_version, config, cur, plugin_dir, username, password)
    copyVersionFiles(config, plugin_dir, base_version, new_version)

    for lid, bid in line_bundles.items():
        cur.execute("""UPDATE "{}".lines SET pipe_bundle_type_id = %s WHERE id = %s;""".format(new_version), (bid, lid))  # nosec B608
    return line_bundles, new_bundle_ids
