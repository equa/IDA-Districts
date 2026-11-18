# coding=utf-8
"""Heating or cooling mode of every supply/return pair per simulated time step (OpenSpec change cost-optimization, D23):
from the heat the plants of the pair put into the network, c_p * sum(mdot * T) over the pair's connections (the
supply mass flow leaves the plant positive, the return enters negative), with a deadband. Without plant results the
mode of the plant template (supply warmer than return) holds for every step."""
import numpy as np

CP = 4186.0  # J/(kg K), only the sign and the band of the heat flow matter
DEFAULT_DEADBAND_PCT = 5.0
TABLE_TEMP, TABLE_MDOT = 'energy_plant_s_temp$', 'energy_plant_s_mdot$'


def plantPairs(connections):
    """[(supply seq, return seq, template mode)] from the plant connections [{'conn_seq', 'type' (1 supply, 2 return),
    'temp'}]: the k-th supply with the k-th return, heat if the supply is warmer than the return."""
    supplies = sorted({c['conn_seq']: c for c in connections if c['type'] == 1}.values(), key=lambda c: c['conn_seq'])
    returns = sorted({c['conn_seq']: c for c in connections if c['type'] == 2}.values(), key=lambda c: c['conn_seq'])
    return [(s['conn_seq'], r['conn_seq'], 'heat' if float(s.get('temp') or 0) >= float(r.get('temp') or 0) else 'cold')
            for s, r in zip(supplies, returns)]


def segmentStarts(times, dt_hours):
    """indices where a new run of consecutive steps begins (the weeks of a period run)"""
    starts = [0]
    for k in range(1, len(times)):
        if (times[k] - times[k - 1]).total_seconds() / 3600 > 1.5 * dt_hours:
            starts.append(k)
    return starts


def deadbandModes(q, deadband_pct, fallback='heat', starts=(0,)):
    """True (heating) per step from the heat flow into the network q (W): heating above +band, cooling below -band,
    the previous mode inside; band = pct of the range between the largest heating and the largest cooling flow.
    Each segment begins with the mode of its first step outside the band (fallback if it has none)."""
    q = np.asarray(q, dtype=float)
    n = len(q)
    heat = np.full(n, fallback == 'heat')
    if not n:
        return heat
    band = deadband_pct / 100 * (max(float(q.max()), 0.0) - min(float(q.min()), 0.0))
    bounds = list(starts) + [n]
    for a, b in zip(bounds, bounds[1:]):
        outside = np.flatnonzero(np.abs(q[a:b]) > band)
        state = bool(q[a + outside[0]] > 0) if len(outside) else fallback == 'heat'
        for k in range(a, b):
            if q[k] > band:
                state = True
            elif q[k] < -band:
                state = False
            heat[k] = state
    return heat


def connectionHeatFlows(cur, schema, tables, sources, index, n, per_plant=False):
    """{conn_seq: array (n)}: c_p * sum over the plants of mdot * T of the connection, from the result tables
    energy_plant_s_temp$<ident> and energy_plant_s_mdot$<ident> (ident ends with the connection sequence);
    per_plant: {(fid, conn_seq): array (n)} instead"""
    flows: dict = {}
    for table in tables:
        ident = table[len(TABLE_TEMP):]
        seq = int(ident.split('_')[-1])
        for t_source, m_source in zip(sources(table), sources(TABLE_MDOT + ident)):
            cur.execute("SELECT to_regclass(%s) IS NOT NULL AS ok;", ('"{}"."{}"'.format(schema, m_source),))
            if not cur.fetchone()['ok']:
                continue
            cur.execute('SELECT t.fid, t.time, sum(t."$temp" * m."$mdot") AS q FROM "{s}"."{t}" t JOIN "{s}"."{m}" m ON m.fid = t.fid AND m.time = t.time '
                        'GROUP BY t.fid, t.time;'.format(s=schema, t=t_source, m=m_source))  # nosec B608
            for row in cur.fetchall():
                k = index.get(row['time'])
                if k is not None and row['q'] is not None:
                    arr = flows.setdefault((row['fid'], seq) if per_plant else seq, np.zeros(n))
                    arr[k] += CP * float(row['q'])
    return flows


def sequenceModes(pairs, flows, deadband_pct, starts, weights=None):
    """({seq: bool array (heating)}, {'s/r': summary}) for the pairs [(s, r, template mode)] and the connection heat flows;
    a pair without flows keeps its template mode in every step"""
    masks, summary = {}, {}
    for s, r, template in pairs:
        n = len(next(iter(flows.values()))) if flows else 0
        if s in flows and r in flows:
            q = flows[s] + flows[r]
            heat = deadbandModes(q, deadband_pct, template, starts)
            source = 'plants'
        else:
            q, heat, source = None, None, 'template'
        masks[s] = masks[r] = heat if heat is not None else template
        w = np.ones(n) if weights is None else np.asarray(weights, dtype=float)
        summary['{}/{}'.format(s, r)] = {'source': source, 'template': template, 'deadband_pct': deadband_pct,
                                         'heat_h': float(np.sum(w[heat])) if heat is not None else None,
                                         'cold_h': float(np.sum(w[~heat])) if heat is not None else None,
                                         'q_max': float(q.max()) if q is not None and len(q) else None,
                                         'q_min': float(q.min()) if q is not None and len(q) else None}
    return masks, summary


def heatMask(masks, seq, n):
    """bool array (n) of a sequence: its mask, its template mode as a constant, heating if unknown"""
    m = masks.get(seq, 'heat')
    if isinstance(m, str):
        return np.full(n, m == 'heat')
    return np.asarray(m, dtype=bool)
