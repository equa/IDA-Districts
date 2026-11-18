# coding=utf-8
"""Economic evaluation of a simulated version for a scenario (OpenSpec change network-cost-data): investment of the
pipes, trench and pumps in use, yearly pump energy, heat and cold losses and maintenance, net present value.

Hourly quantities come from the result tables with a weight per time step (the time step in hours); change
representative-periods supplies other weights. Without results covering a full year the evaluation names what is
missing instead of values."""
import datetime
import os
import re

from .economic_data import loadScenario
from .economics import netPresentValue, normalizedProfile, readProfile, trenchCostPerMetre, yearlyEnergyCosts
from .network_modes import (
    DEFAULT_DEADBAND_PCT, TABLE_TEMP, connectionHeatFlows, heatMask, plantPairs, segmentStarts, sequenceModes as modesOfSequences,
)
from .periods import loadPeriods, readClimate, weights as periodWeights
from .pipe_losses import ambientTemperature, checkLines, sequenceModes, uPrime

TRENCH_TOLERANCE = 1.0  # m, a line lies on a street within this distance
FULL_YEAR_DAYS = 364


def tableExists(cur, schema, table):
    cur.execute("SELECT to_regclass(%s) IS NOT NULL AS ok;", ('"{}"."{}"'.format(schema, table),))
    return cur.fetchone()['ok']


def resultTables(cur, schema, prefix):
    cur.execute("SELECT table_name FROM information_schema.tables WHERE table_schema = %s AND table_name LIKE %s ORDER BY table_name;",
                (schema, prefix.replace('_', '\\_') + '%'))
    # without the copies of a period run (representative-periods)
    return [row['table_name'] for row in cur.fetchall() if not re.search(r'_period\d+$', row['table_name'])]


def nominalDiameter(pipe):
    match = re.match(r'\s*DN\s*(\d+)', pipe.get('description') or '')
    return int(match.group(1)) if match else round(float(pipe.get('innerpipediameter') or 0) * 1000)


def linePipes(cur, schema):
    """{lid: {'length', 'bundle', 'pipes': {seq: pipe row with layers, depth, ambient}}} of the lines with a bundle."""
    cur.execute("""SELECT l.id AS lid, ST_Length(l.geom) AS length, l.pipe_bundle_type_id AS bundle, bp.sequence AS seq,
        bp.y AS depth, bp.ambient, p.id AS pipe_id, p.name, p.innerpipediameter, p.description, p.costs, p.maintenance_pct,
        p.lifetime_a, p.p_max_bar, p.example, p.pipe_construction_id
        FROM "{}".lines l JOIN public.bundle_pipes bp ON bp.pipe_bundle_type_id = l.pipe_bundle_type_id
        JOIN public.pipes p ON p.id = bp.pipe_id ORDER BY l.id, bp.sequence;""".format(schema))  # nosec B608
    lines = {}
    for row in cur.fetchall():
        line = lines.setdefault(row['lid'], {'length': float(row['length'] or 0), 'bundle': row['bundle'], 'pipes': {}})
        line['pipes'][row['seq']] = dict(row)
    cur.execute("""SELECT pl.pipe_construction_id AS cid, pl.thickness, m.thermal_conductivity_w7mkelvin AS lam
        FROM public.pipe_layers pl JOIN public.materials m ON m.id = pl.materialid ORDER BY pl.pipe_construction_id, pl.sequence;""")
    layers = {}
    for row in cur.fetchall():
        layers.setdefault(row['cid'], []).append((float(row['thickness'] or 0), float(row['lam'] or 0)))
    for line in lines.values():
        for pipe in line['pipes'].values():
            pipe['layers'] = layers.get(pipe['pipe_construction_id'], [])
    return lines


def trenchLengths(cur, schema, default_surface):
    """{lid: {surface: length}}: the overlap of a line with the streets per surface, the rest with the default surface."""
    cur.execute("""SELECT l.id AS lid, ST_Length(l.geom) AS length, COALESCE(s.surface, %s) AS surface,
        ST_Length(ST_Intersection(l.geom, ST_Buffer(s.geom, %s, 'endcap=flat'))) AS overlap
        FROM "{schema}".lines l LEFT JOIN "{schema}".streets s ON ST_DWithin(l.geom, s.geom, %s);""".format(schema=schema),  # nosec B608
                (default_surface, TRENCH_TOLERANCE, TRENCH_TOLERANCE))
    lengths, totals = {}, {}
    for row in cur.fetchall():
        totals[row['lid']] = float(row['length'] or 0)
        if row['overlap']:
            per = lengths.setdefault(row['lid'], {})
            per[row['surface']] = per.get(row['surface'], 0.0) + float(row['overlap'])
    for lid, total in totals.items():
        per = lengths.setdefault(lid, {})
        on_streets = sum(per.values())
        if on_streets > total:  # crossing streets overlap twice
            for surface in per:
                per[surface] *= total / on_streets
        elif total - on_streets > 0:
            per[default_surface] = per.get(default_surface, 0.0) + total - on_streets
    return lengths


def investments(scenario, lines, trench):
    """Investment items (pipes per pipe type, trench per line, without pumps), pipes in use without costs, example flag."""
    items, no_costs, example = {}, set(), False
    for lid, line in lines.items():
        dn = max([nominalDiameter(p) for p in line['pipes'].values()] or [0])
        for pipe in line['pipes'].values():
            if pipe['costs'] is None:
                no_costs.add(pipe['name'])
                continue
            example = example or bool(pipe['example'])
            item = items.setdefault(('pipe', pipe['pipe_id']), {'cost': 0.0, 'lifetime': float(pipe['lifetime_a'] or 0),
                                                                'maintenance_pct': float(pipe['maintenance_pct'] or 0), 'name': pipe['name']})
            item['cost'] += float(pipe['costs']) * line['length']
            item['length'] = item.get('length', 0.0) + line['length']
        for surface, length in trench.get(lid, {}).items():
            item = items.setdefault(('trench', surface), {'cost': 0.0, 'lifetime': lifetimeOfLine(line), 'maintenance_pct': 0.0, 'name': surface})
            item['cost'] += trenchCostPerMetre(scenario, surface, dn) * length
            item['length'] = item.get('length', 0.0) + length
    return items, sorted(no_costs), example


def surfacesWithoutTrenchCosts(scenario, trench):
    """Surfaces in use that have no trench costs in the scenario (their trench is valued with the default surface,
    or with 0 if that has none either)."""
    known = scenario.get('trench', {})
    return sorted({surface for per in trench.values() for surface in per if surface not in known})


def lifetimeOfLine(line):
    lifetimes = [float(p['lifetime_a']) for p in line['pipes'].values() if p['lifetime_a']]
    return max(lifetimes) if lifetimes else 0.0


def plantConnections(cur, schema):
    """[{'conn_seq', 'type', 'temp'}] of the energy plant connections of the version"""
    cur.execute("""SELECT DISTINCT ctc.sequence AS conn_seq, c.type, c.temp
        FROM "{}".energy_plants ep, public.energy_plant_templates t, public.bundle_type_conns b,
            public.connection_type_connections ctc, public.connections c
        WHERE t.template = ep.template AND b.conn_bundle_type_id = t.conn_bundle_type
            AND ctc.connection_type_id = b.conn_type_id AND c.id = ctc.connection_id;""".format(schema))  # nosec B608
    return [dict(row) for row in cur.fetchall()]


def plantModes(cur, schema):
    """({conn_seq: template mode}, {conn_seq: type}) of the energy plant connections of the version."""
    rows = plantConnections(cur, schema)
    return sequenceModes(rows), {row['conn_seq']: row['type'] for row in rows}


def stepModes(cur, schema, sources, times, dt, weights, settings):
    """({seq: bool array per step (heating)}, summary per pair) from the plants' heat flows (network_modes)"""
    connections = plantConnections(cur, schema)
    index = {t: k for k, t in enumerate(times)}
    flows = connectionHeatFlows(cur, schema, resultTables(cur, schema, TABLE_TEMP), sources, index, len(times))
    return modesOfSequences(plantPairs(connections), flows, float(settings.get('mode_deadband_pct', DEFAULT_DEADBAND_PCT)),
                            segmentStarts(times, dt), weights)


def timeSteps(cur, schema, table):
    cur.execute('SELECT DISTINCT time FROM "{}"."{}" ORDER BY time;'.format(schema, table))  # nosec B608
    return [row['time'] for row in cur.fetchall()]


def missingResults(cur, schema):
    """Result tables the evaluation needs, by output name."""
    missing = []
    if not (tableExists(cur, schema, 'energy_plant_s_ppump') or tableExists(cur, schema, 'customer_s_ppump')):
        missing.append('pump power')
    if not resultTables(cur, schema, 'line_s_temp$'):
        missing.append('line temperature')
    if not resultTables(cur, schema, 'energy_plant_s_temp$'):
        missing.append('energy plant temperature')
    if not tableExists(cur, schema, 'line_s_qamb'):
        missing.append('line heat loss')
    return missing


def periodSources(cur, config):
    """(sources, weight per hour of the year, periods data) of a period run with kept tables, else None."""
    periods = loadPeriods(config)
    if not periods or periods.get('annual') or not periods.get('hours'):
        return None
    ks = sorted({k for k, _, _ in periods['hours']})
    if not all(tableExists(cur, config['versionName'], 'line_s_qamb_period{}'.format(k)) for k in ks):
        return None
    return ks, {h: w for _, h, w in periods['hours']}, periods


def evaluateVersion(cur, config, scenario_id, settings, profile_dir=None):
    """Economic evaluation of the loaded version. Returns {'missing': [...]} or {'short': days} without results of a
    full year or of a period run, otherwise the investment, energy, NPV and checks."""
    schema = config['versionName']
    scenario = loadScenario(cur, scenario_id)
    missing = missingResults(cur, schema)
    if missing:
        return {'scenario': scenario, 'missing': missing}
    temp_tables = resultTables(cur, schema, 'line_s_temp$')
    times = timeSteps(cur, schema, temp_tables[0])
    span = (times[-1] - times[0]).total_seconds() / 86400 if len(times) > 1 else 0
    run = None
    if span < FULL_YEAR_DAYS:
        run = periodSources(cur, config)
        if not run:
            return {'scenario': scenario, 'short': span}
    dt = (times[1] - times[0]).total_seconds() / 3600 if len(times) > 1 else 1.0

    def sources(table):
        return ['{}_period{}'.format(table, k) for k in run[0]] if run else [table]

    if run:
        times = sorted({t for source in sources(temp_tables[0]) for t in timeSteps(cur, schema, source)})
    year_start = datetime.datetime(times[0].year, 1, 1)

    def hourOf(time):
        return int((time - year_start).total_seconds() // 3600)

    def weight(time):
        return run[1].get(hourOf(time), 0.0) * dt if run else dt

    lines = linePipes(cur, schema)
    sc = scenario['scenario']
    trench = trenchLengths(cur, schema, sc.get('default_surface') or 'paved')
    items, no_costs, example = investments(scenario, lines, trench)
    no_trench = surfacesWithoutTrenchCosts(scenario, trench)
    _, conn_types = plantModes(cur, schema)

    # pump power per time step and the peak per pump
    pump_power, peaks = {}, {}
    for table in ('energy_plant_s_ppump', 'customer_s_ppump'):
        for source in sources(table):
            if not tableExists(cur, schema, source):
                continue
            cur.execute('SELECT time, sum("$ppump") AS p FROM "{}"."{}" GROUP BY time;'.format(schema, source))  # nosec B608
            for row in cur.fetchall():
                pump_power[row['time']] = pump_power.get(row['time'], 0.0) + float(row['p'] or 0)
            cur.execute('SELECT fid, pump, max("$ppump") AS p FROM "{}"."{}" GROUP BY fid, pump;'.format(schema, source))  # nosec B608
            for row in cur.fetchall():
                key = (table, row['fid'], row['pump'])
                peaks[key] = max(peaks.get(key, 0.0), float(row['p'] or 0))
    pump_kw = sum(peaks.values()) / 1000
    pump_item = {'cost': pump_kw * float(sc.get('pump_costs_eur7kw') or 0), 'lifetime': float(sc.get('pump_lifetime_a') or 0),
                 'maintenance_pct': float(sc.get('pump_maintenance_pct') or 0), 'name': 'pumps'}

    # U' * L per pipe; per mode and time sum(U'L * T_pipe), per mode and ambient sum(U'L)
    ul = {}
    for lid, line in lines.items():
        for seq, pipe in line['pipes'].items():
            u = uPrime(float(pipe['innerpipediameter'] or 0.05), pipe['layers'], float(pipe['depth'] or 1),
                       int(pipe['ambient'] or 2), float(settings.get('ground_lambda', 1.2)))
            ul[(lid, seq)] = (u * line['length'], int(pipe['ambient'] or 2), seq)
    ul_t = {}  # per sequence and time
    ul_ambient = {}  # per (sequence, ambient)
    line_t_sum = {}
    for table in temp_tables:
        seq = int(table.split('$')[1])
        for source in sources(table):
            cur.execute('SELECT fid, time, avg("$temp") AS t FROM "{}"."{}" GROUP BY fid, time;'.format(schema, source))  # nosec B608
            for row in cur.fetchall():
                entry = ul.get((row['fid'], seq))
                if not entry or row['t'] is None:
                    continue
                value = entry[0] * float(row['t'])
                per_seq = ul_t.setdefault(entry[2], {})
                per_seq[row['time']] = per_seq.get(row['time'], 0.0) + value
                line_t_sum[row['fid']] = line_t_sum.get(row['fid'], 0.0) + value * weight(row['time'])
    for (lid, seq), (value, ambient, _) in ul.items():
        ul_ambient[(seq, ambient)] = ul_ambient.get((seq, ambient), 0.0) + value

    # mean supply temperature of the plants per supply connection and time
    t_parts = {}
    for table in resultTables(cur, schema, 'energy_plant_s_temp$'):
        conn_seq = int(table.split('_')[-1])
        if conn_types.get(conn_seq) != 1:
            continue
        sums, counts = t_parts.setdefault(conn_seq, ({}, {}))
        for source in sources(table):
            if not tableExists(cur, schema, source):
                continue
            cur.execute('SELECT time, avg("$temp") AS t FROM "{}"."{}" GROUP BY time;'.format(schema, source))  # nosec B608
            for row in cur.fetchall():
                if row['t'] is not None:
                    sums[row['time']] = sums.get(row['time'], 0.0) + float(row['t'])
                    counts[row['time']] = counts.get(row['time'], 0) + 1
    t_seq = {seq: {time: total / counts[time] for time, total in sums.items()} for seq, (sums, counts) in t_parts.items()}
    masks, mode_summary = stepModes(cur, schema, sources, times, dt, [weight(t) for t in times], settings)
    heat_of = {seq: heatMask(masks, seq, len(times)) for seq in set(ul_t) | set(t_seq) | {s for s, _ in ul_ambient}}

    profile = None
    if sc.get('el_profile_file') and profile_dir:
        profile = normalizedProfile(readProfile(os.path.join(profile_dir, sc['el_profile_file'])))
    shapes = {}
    if run and profile:
        # the price shape of a simulated hour: the profile of the year hours it stands for
        periods = run[2]
        t_year = readClimate(periods['climate_file'])
        sums = periodWeights(t_year, periods['year'], sorted(run[1]), profile)[0]
        shapes = {h: (s / w if w else 1.0) for h, (w, s) in sums.items()}

    hours, amb_sum = [], {}
    sequences = set(ul_t) | {s for s, _ in ul_ambient}
    for k, time in enumerate(times):
        day = (time - year_start).total_seconds() / 86400
        w = weight(time)
        t_amb = {ambient: ambientTemperature(ambient, day, settings) for ambient in {a for _, a in ul_ambient}}
        for ambient, t in t_amb.items():
            amb_sum[ambient] = amb_sum.get(ambient, 0.0) + t * w
        # each sequence counts for the mode of its pair in this step
        q = {'heat': 0.0, 'cold': 0.0}
        q_out = {'heat': 0.0, 'cold': 0.0}  # the sequences giving heat off (> 0) and taking it up (rest), for the report
        for seq in sequences:
            mode = 'heat' if heat_of[seq][k] else 'cold'
            value = ul_t.get(seq, {}).get(time, 0.0) - sum(v * t_amb[a] for (s, a), v in ul_ambient.items() if s == seq)
            q[mode] += value
            q_out[mode] += max(value, 0.0)
        t_mode = {}
        for mode in ('heat', 'cold'):
            temps = [t_seq[seq][time] for seq in t_seq if time in t_seq[seq] and bool(heat_of[seq][k]) == (mode == 'heat')]
            t_mode[mode] = sum(temps) / len(temps) if temps else 0.0
        hour = {'weight': w, 'hour': hourOf(time), 'p_pump': pump_power.get(time, 0.0),
                'q_heat': q['heat'], 'q_cold': q['cold'], 't_heat': t_mode['heat'], 't_cold': t_mode['cold'],
                'q_heat_out': q_out['heat'], 'q_cold_out': q_out['cold']}
        if run:
            hour['shape'] = shapes.get(hourOf(time), 1.0)
        hours.append(hour)
    line_amb = {}
    for (lid, seq), (value, ambient, mode) in ul.items():
        line_amb[lid] = line_amb.get(lid, 0.0) + value * amb_sum.get(ambient, 0.0)
    costs, energy = yearlyEnergyCosts(scenario, hours, None if run else profile)
    years_simulated = 1 if run else max(1, round(len(times) * dt / 8760))
    costs = {key: value / years_simulated for key, value in costs.items()}
    energy = {key: value / years_simulated for key, value in energy.items()}

    # check of the calculated losses against the simulated QAmbtotal of every line (weighted Wh)
    simulated = {}
    for source in sources('line_s_qamb'):
        cur.execute('SELECT fid, time, "$qamb" AS q FROM "{}"."{}";'.format(schema, source))  # nosec B608
        for row in cur.fetchall():
            simulated[row['fid']] = simulated.get(row['fid'], 0.0) + float(row['q'] or 0) * weight(row['time'])
    calculated = {lid: line_t_sum.get(lid, 0.0) - line_amb.get(lid, 0.0) for lid in lines}
    result = netPresentValue(scenario, list(items.values()) + [pump_item], costs)
    evaluation = {'scenario': scenario, 'items': items, 'pump_item': pump_item, 'pump_kw': pump_kw, 'no_costs': no_costs, 'no_trench': no_trench,
                  'example': example or bool(sc.get('example')), 'costs': costs, 'energy': energy, 'npv': result,
                  'loss_check': checkLines(calculated, simulated), 'n_lines': len(lines), 'dt': dt, 'modes': mode_summary}
    if run:
        periods = run[2]
        evaluation['periods'] = {'weeks': [w['calc_from'][:10] for w in periods['weeks']], 'coverage': periods.get('coverage'),
                                 'run_time': periods.get('run_time')}
    return evaluation
