# coding=utf-8
"""The cost model of a check from the result tables of the version (OpenSpec change cost-optimization): the kept
weeks of a period run with their weights, or the results of an annual simulation."""
import datetime

import numpy as np

from .cost_model import RHO, CostModel, catalogWithCosts
from .economic_data import loadScenario
from .economics import normalizedProfile, readProfile
from .flow_tracing import getNetworkGraph
from .network_economics import linePipes, periodSources, plantModes, resultTables, tableExists, timeSteps, trenchLengths
from .periods import readClimate, weights as periodWeights
from .pipe_losses import ambientTemperature

try:
    from .protected_lines import loadProtectedLines
except ImportError:  # change protect-lines not installed
    def loadProtectedLines(config, version=None):
        return []


def series(cur, schema, sources, column, times, index, key='fid', aggregate='avg'):
    """{fid: array over times} of a result column from the source tables (segments averaged)."""
    out = {}
    for source in sources:
        if not tableExists(cur, schema, source):
            continue
        cur.execute('SELECT {k} AS k, time, {a}("{c}") AS v FROM "{s}"."{t}" GROUP BY {k}, time;'.format(k=key, a=aggregate, c=column, s=schema, t=source))  # nosec B608
        for row in cur.fetchall():
            if row['v'] is None or row['time'] not in index:
                continue
            arr = out.setdefault(row['k'], np.zeros(len(times)))
            arr[index[row['time']]] = float(row['v'])
    return out


def checkSources(cur, config):
    """(sources(table) -> [tables], times, weights [h per year per step], shape per step for a profile, periods)"""
    schema = config['versionName']
    temp_tables = resultTables(cur, schema, 'line_s_temp$')
    times = timeSteps(cur, schema, temp_tables[0]) if temp_tables else []
    span = (times[-1] - times[0]).total_seconds() / 86400 if len(times) > 1 else 0
    run = periodSources(cur, config) if span < 364 else None
    if span < 364 and not run:
        return None

    def sources(table):
        return ['{}_period{}'.format(table, k) for k in run[0]] if run else [table]

    if run:
        times = sorted({t for source in sources(temp_tables[0]) for t in timeSteps(cur, schema, source)})
    dt = (times[1] - times[0]).total_seconds() / 3600 if len(times) > 1 else 1.0
    year_start = datetime.datetime(times[0].year, 1, 1)
    hours = [int((t - year_start).total_seconds() // 3600) for t in times]
    w = np.array([run[1].get(h, 0.0) * dt if run else dt for h in hours])
    years = 1 if run else max(1, round(len(times) * dt / 8760))
    return sources, times, w / years, hours, run


def buildModel(cur, config, scenario_id, pairs, settings, profile_dir=None):
    """CostModel of the loaded version from its kept results; None without results of a period run or a full year."""
    schema = config['versionName']
    check = checkSources(cur, config)
    if not check:
        return None
    sources, times, w, hours, run = check
    n = len(times)
    index = {t: k for k, t in enumerate(times)}
    scenario = loadScenario(cur, scenario_id)
    sc = scenario['scenario']
    cur.execute('SELECT * FROM public.pipes WHERE innerpipediameter > 0;')
    rows = [dict(r) for r in cur.fetchall()]
    catalog = catalogWithCosts(rows)
    p_max = {int(r['id']): float(r['p_max_bar']) for r in rows if r.get('p_max_bar')}
    cur.execute("""SELECT pl.pipe_construction_id AS cid, pl.thickness, m.thermal_conductivity_w7mkelvin AS lam
        FROM public.pipe_layers pl JOIN public.materials m ON m.id = pl.materialid ORDER BY pl.pipe_construction_id, pl.sequence;""")
    layers = {}
    for row in cur.fetchall():
        layers.setdefault(row['cid'], []).append((float(row['thickness'] or 0), float(row['lam'] or 0)))

    trench = trenchLengths(cur, schema, sc.get('default_surface') or 'paved')
    protected = set(loadProtectedLines(config))
    lines = {}
    for lid, line in linePipes(cur, schema).items():
        lines[lid] = {'length': line['length'], 'pipes': {seq: int(p['pipe_id']) for seq, p in line['pipes'].items()},
                      'ambient': {seq: int(p['ambient'] or 2) for seq, p in line['pipes'].items()},
                      'depth': {seq: float(p['depth'] or 1) for seq, p in line['pipes'].items()},
                      'surface': trench.get(lid, {}), 'protected': lid in protected}

    mdot, temp = {}, {}
    sequences = sorted({seq for pair in pairs for seq in pair})
    for seq in sequences:
        for lid, arr in series(cur, schema, sources('line_s_mdot${}'.format(seq)), '$mdot', times, index).items():
            mdot[(lid, seq)] = arr
        for lid, arr in series(cur, schema, sources('line_s_temp${}'.format(seq)), '$temp', times, index).items():
            temp[(lid, seq)] = arr
    graph = getNetworkGraph(cur, config)
    cur.execute('SELECT id FROM "{}".customers ORDER BY id;'.format(schema))  # nosec B608
    customers = [row['id'] for row in cur.fetchall()]

    central = None
    if any(tableExists(cur, schema, s) for s in sources('energy_plant_s_ppump')):
        central = sum(series(cur, schema, sources('energy_plant_s_ppump'), '$ppump', times, index, aggregate='sum').values(), np.zeros(n))
    decentral = {cid: p for cid, p in series(cur, schema, sources('customer_s_ppump'), '$ppump', times, index, aggregate='sum').items()
                 if float(np.max(p)) > 0}

    # volume flows: the supply pipes of the lines at the plants and at every customer
    v_plant, v_customer = {}, {}
    for pair in pairs:
        flow = np.zeros(n)
        for lid, (start, end) in graph.items():
            if (start[0] == 'ep' or end[0] == 'ep') and (lid, pair[0]) in mdot:
                flow += np.abs(mdot[(lid, pair[0])])
        v_plant[pair] = flow / RHO
    for cid in customers:
        flow = np.zeros(n)
        for lid, (start, end) in graph.items():
            if ('c', cid) in (start, end) and pairs and (lid, pairs[0][0]) in mdot:
                flow += np.abs(mdot[(lid, pairs[0][0])])
        v_customer[cid] = flow / RHO

    modes, conn_types = plantModes(cur, schema)
    t_supply, p_plant = {'heat': np.zeros(n), 'cold': np.zeros(n)}, None
    counts = {'heat': np.zeros(n), 'cold': np.zeros(n)}
    for table in resultTables(cur, schema, 'energy_plant_s_temp$'):
        conn_seq = int(table.split('_')[-1])
        if conn_types.get(conn_seq) == 1:
            mode = modes.get(conn_seq, 'heat')
            for arr in series(cur, schema, sources(table), '$temp', times, index).values():
                t_supply[mode] += arr
                counts[mode] += arr != 0
    for mode in t_supply:
        t_supply[mode] = np.divide(t_supply[mode], counts[mode], out=np.zeros(n), where=counts[mode] > 0)
    for table in resultTables(cur, schema, 'energy_plant_s_p$'):
        if conn_types.get(int(table.split('_')[-1])) == 1:
            for arr in series(cur, schema, sources(table), '$p', times, index).values():
                p_plant = arr if p_plant is None else np.maximum(p_plant, arr)

    year_start = datetime.datetime(times[0].year, 1, 1)
    days = [(t - year_start).total_seconds() / 86400 for t in times]
    t_amb = {a: np.array([ambientTemperature(a, d, settings) for d in days]) for a in (1, 2, 3)}

    shape = None
    if sc.get('el_profile_file') and profile_dir:
        import os
        profile = normalizedProfile(readProfile(os.path.join(profile_dir, sc['el_profile_file'])))
        if run:
            sums = periodWeights(readClimate(run[2]['climate_file']), run[2]['year'], sorted(run[1]), profile)[0]
            shape = np.array([(sums[h][1] / sums[h][0]) if sums.get(h) and sums[h][0] else 1.0 for h in hours])
        else:
            shape = np.array([profile[h % len(profile)] for h in hours])
    return CostModel(scenario, catalog, layers, lines, [tuple(p) for p in pairs], w, mdot, temp, graph, customers,
                     central=central, decentral=decentral, v_plant=v_plant, v_customer=v_customer, p_plant=p_plant,
                     t_amb=t_amb, t_supply=t_supply, modes=modes, shape=shape, lambda_soil=float(settings.get('ground_lambda', 1.2)),
                     p_max=p_max)
