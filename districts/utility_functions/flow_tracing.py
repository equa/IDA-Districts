"""Attribution of customer mass flows to the supplying pipes (flow tracing).

Result: c_lid = {cid : {lid : mdot}}
    cid  ... customer id
    lid  ... line id
    mdot ... part of the customer mass flow [kg/s] which is transported through line lid

The attribution assumes complete mixing at every node (proportional split, as used for
water quality / source tracing). At every node the outflow of a customer is distributed to
the incoming lines in proportion to their mass flows. Therefore, for every customer the sum
of all parallel supply strands (any cut between the customer and the energy plants) equals
the mass flow at the substation, also for meshed networks and several energy plants.

Sign convention of the line results (IDA ICE pipes): liq1 = start point, liq2 = end point
of the line geometry, a positive mass flow runs from the start to the end point.
"""
import json
import pickle  # nosec B403
from collections import defaultdict, deque


def getNetworkGraph(cur, config, network=None):
    """Returns the topology of the network as {lid: (start_node, end_node)}.

    Nodes are tuples: ('j', jid), ('c', cid), ('ep', epid). Line ends without an entry in the
    connection tables (e.g. direct line-line connections) get a virtual node ('v', x, y)
    from the rounded end point coordinates."""
    v = config['versionName']
    line_filter = ' WHERE l.network = {}'.format(int(network)) if network is not None else ''
    sql = """SELECT l.id AS lid,
        round(ST_X(ST_StartPoint(l.geom))::numeric, 3) AS xs, round(ST_Y(ST_StartPoint(l.geom))::numeric, 3) AS ys,
        round(ST_X(ST_EndPoint(l.geom))::numeric, 3) AS xe, round(ST_Y(ST_EndPoint(l.geom))::numeric, 3) AS ye
    FROM "{}".lines l{};""".format(v, line_filter)  # nosec B608
    cur.execute(sql)
    graph = {row['lid']: [('v', float(row['xs']), float(row['ys'])), ('v', float(row['xe']), float(row['ye']))]
        for row in cur.fetchall()}

    sql = """WITH nodes AS (
    SELECT 'j' AS kind, jc.jid AS nid, jc.lid, j.geom FROM "{}".junction_connections jc, "{}".junctions j WHERE j.id = jc.jid
    UNION ALL
    SELECT 'c' AS kind, cc.cid AS nid, cc.lid, c.geom FROM "{}".customer_connections cc, "{}".customers c WHERE c.id = cc.cid
    UNION ALL
    SELECT 'ep' AS kind, epc.epid AS nid, epc.lid, ep.geom FROM "{}".energy_plant_connections epc, "{}".energy_plants ep WHERE ep.id = epc.epid
)
SELECT n.kind, n.nid, n.lid,
        ST_Distance(ST_StartPoint(l.geom), n.geom) <= ST_Distance(ST_EndPoint(l.geom), n.geom) AS at_start
    FROM nodes n, "{}".lines l
    WHERE l.id = n.lid{};""".format(v, v, v, v, v, v, v, line_filter.replace('WHERE', 'AND'))  # nosec B608
    cur.execute(sql)
    for row in cur.fetchall():
        if row['lid'] in graph:
            graph[row['lid']][0 if row['at_start'] else 1] = (row['kind'], row['nid'])
    return {lid: tuple(nodes) for lid, nodes in graph.items()}


def getMdotAtTime(cur, config, table, time):
    """Returns {fid: mdot} of a result table (line_s_mdot$x, customer_s_mdot$x) at the given time.
    Line results with several segments are averaged."""
    sql = """SELECT fid, AVG("$mdot") AS mdot FROM "{}"."{}" WHERE time = %s GROUP BY fid;""".format(config['versionName'], table)  # nosec B608
    cur.execute(sql, (time,))
    return {row['fid']: float(row['mdot']) for row in cur.fetchall() if row['mdot'] is not None}


def traceCustomerSupply(graph, mdot_lines, mdot_customers, eps=1e-9):
    """Core algorithm (without DB access).

    graph:          {lid: (start_node, end_node)}
    mdot_lines:     {lid: mdot} positive from start to end node
    mdot_customers: {cid: mdot} mass flow at the substations
    Returns (c_lid, warnings) with c_lid = {cid: {lid: mdot}}."""
    warnings = []
    inflow = defaultdict(list)       # node -> [(lid, upstream node, mdot)]
    out_sum = defaultdict(float)     # node -> sum of outgoing line mass flows
    in_sum = defaultdict(float)      # node -> sum of incoming line mass flows
    succ = defaultdict(set)          # node -> downstream nodes
    nodes = set()
    for lid, (n_start, n_end) in graph.items():
        nodes.update((n_start, n_end))
        mdot = mdot_lines.get(lid)
        if mdot is None:
            warnings.append('No mass flow result for line {}'.format(lid))
            continue
        if abs(mdot) <= eps:
            continue
        up, down = (n_start, n_end) if mdot > 0 else (n_end, n_start)
        inflow[down].append((lid, up, abs(mdot)))
        in_sum[down] += abs(mdot)
        out_sum[up] += abs(mdot)
        succ[up].add(down)

    # demand composition per node: node -> {cid: mdot}
    demand = defaultdict(lambda: defaultdict(float))
    for cid, mdot in mdot_customers.items():
        node = ('c', cid)
        if node not in nodes:
            warnings.append('Customer {} is not connected to the network'.format(cid))
            continue
        if abs(mdot) > eps:
            demand[node][cid] += abs(mdot)

    # reverse topological order: a node is processed after all of its downstream nodes
    n_succ = {n: len(succ[n]) for n in nodes}
    pred = defaultdict(set)
    for up, downs in succ.items():
        for down in downs:
            pred[down].add(up)
    queue = deque(n for n in nodes if n_succ[n] == 0)
    order = []
    while queue:
        n = queue.popleft()
        order.append(n)
        for up in pred[n]:
            n_succ[up] -= 1
            if n_succ[up] == 0:
                queue.append(up)
    if len(order) < len(nodes):
        cyclic = [n for n in nodes if n_succ[n] > 0]
        warnings.append('Flow cycle detected at {} nodes, attribution in this part is approximate: {}'.format(len(cyclic), cyclic[:10]))
        order.extend(cyclic)

    c_lid = defaultdict(lambda: defaultdict(float))
    for node in order:
        comp = demand.pop(node, None)
        if not comp or not inflow[node]:
            continue  # energy plant (source) or node without demand
        # total outflow of the node = outgoing lines + own consumption; the difference to the
        # incoming lines is fed in by the node itself (energy plant), it is not passed upstream
        consumption = abs(mdot_customers.get(node[1], 0.0)) if node[0] == 'c' else 0.0
        total = max(in_sum[node], out_sum[node] + consumption)
        for lid, up, mdot in inflow[node]:
            share = mdot / total
            for cid, m in comp.items():
                m_line = m * share
                c_lid[cid][lid] += m_line
                demand[up][cid] += m_line
    return {cid: dict(lids) for cid, lids in c_lid.items()}, warnings


def getFeatureConnTables(cur, config, feature, var='p', network=1, conn_type_seq=1, sup_seq=1, ret_seq=2):
    """Returns {fid: (sup_table, ret_table)} of the result tables (e.g. energy_plant_s_p$7_1_6_1) of every
    customer / energy plant of the network, derived from the connection bundle of its template
    (conn_bundle_type_id _ conn_type_seq _ conn_type_id _ conn_seq, see topology.getPMT2muxIdents).
    feature: 'customer' or 'energy_plant'."""
    if feature not in ('customer', 'energy_plant'):
        raise ValueError("feature must be 'customer' or 'energy_plant'")
    sql = """SELECT f.id AS fid, b.conn_bundle_type_id, b.sequence AS conn_type_seq, b.conn_type_id, ctc.sequence AS conn_seq
    FROM "{}".{}s f, public.{}_templates t, public.bundle_type_conns b, public.connection_type_connections ctc
    WHERE t.template = f.template AND b.conn_bundle_type_id = t.conn_bundle_type AND ctc.connection_type_id = b.conn_type_id
        AND b.sequence = %s AND ctc.sequence IN (%s, %s) AND %s = ANY(f.network);""".format(config['versionName'], feature, feature)  # nosec B608
    cur.execute(sql, (conn_type_seq, sup_seq, ret_seq, int(network)))
    tables = defaultdict(dict)
    for row in cur.fetchall():
        tables[row['fid']][row['conn_seq']] = '{}_s_{}${}_{}_{}_{}'.format(feature, var, row['conn_bundle_type_id'], row['conn_type_seq'], row['conn_type_id'], row['conn_seq'])
    return {fid: (t[sup_seq], t[ret_seq]) for fid, t in tables.items() if sup_seq in t and ret_seq in t}


def getTimeSeries(cur, config, fid_tables, column, time=None):
    """Returns {time: {fid: value}} of column (e.g. '$p', '$mdot') from the tables {fid: table}.
    Values of several segments (lines) are averaged. With time only this time is loaded."""
    v = config['versionName']
    by_table = defaultdict(list)
    for fid, table in fid_tables.items():
        by_table[table].append(fid)
    cur.execute("""SELECT table_name FROM information_schema.tables WHERE table_schema = %s;""", (v,))
    existing = {row['table_name'] for row in cur.fetchall()}
    series = defaultdict(dict)
    for table, fids in by_table.items():
        if table not in existing:
            continue
        sql = """SELECT fid, time, AVG("{}") AS val FROM "{}"."{}" WHERE fid = ANY(%s){} GROUP BY fid, time;""".format(column, v, table, ' AND time = %s' if time is not None else '')  # nosec B608
        cur.execute(sql, (fids, time) if time is not None else (fids,))
        for row in cur.fetchall():
            if row['val'] is not None:
                series[row['time']][row['fid']] = float(row['val'])
    return series


def getCustomerPlantShares(graph, c_lid):
    """Returns {cid: {epid: mdot}}, the share of every energy plant in the customer mass flow
    (sum over the plant lines = mdot of the customer)."""
    ep_lids = {lid: node[1] for lid, nodes in graph.items() for node in nodes if node[0] == 'ep'}
    c_ep = {}
    for cid, lids in c_lid.items():
        c_ep[cid] = defaultdict(float)
        for lid, m in lids.items():
            if lid in ep_lids:
                c_ep[cid][ep_lids[lid]] += m
        c_ep[cid] = dict(c_ep[cid])
    return c_ep


def networkPressureLoss(c_ep, p_c, p_ep, ep_aggregate='max', min_share=0.01):
    """Returns {cid: (dvar, epid)} with the network pressure loss dvar = (p_ep_sup - p_c_sup) + (p_c_ret - p_ep_ret)
    between every customer and the energy plants supplying it (share of the customer mass flow >= min_share).
    p_c / p_ep: {fid: (p_sup, p_ret)}.
    ep_aggregate: 'max' -> plant with the maximal dvar; 'weighted' -> dvar weighted with the mass flow shares
    (epid = plant with the largest share)."""
    result = {}
    for cid, shares in c_ep.items():
        total = sum(shares.values())
        if cid not in p_c or total <= 0:
            continue
        dvars = {ep: (p_ep[ep][0] - p_c[cid][0] + p_c[cid][1] - p_ep[ep][1], m / total)
            for ep, m in shares.items() if m / total >= min_share and ep in p_ep}
        if not dvars:
            continue
        if ep_aggregate == 'weighted':
            share_sum = sum(s for _, s in dvars.values())
            result[cid] = (sum(d * s for d, s in dvars.values()) / share_sum, max(dvars, key=lambda ep: dvars[ep][1]))
        else:
            ep = max(dvars, key=lambda ep: dvars[ep][0])
            result[cid] = (dvars[ep][0], ep)
    return result


def getTimeMaxNetworkPressureLoss(cur, config, network=1, line_mdot_table='line_s_mdot$1', ep_aggregate='max', min_share=0.01, eps=1e-9):
    """Returns the simulation time with the maximal network pressure loss between a customer and the energy
    plant(s) supplying it: dvar = (p_ep_sup - p_c_sup) + (p_c_ret - p_ep_ret).

    For every time step the supplying plants are determined by flow tracing, so every customer is compared
    with the plant on its supply strand (see networkPressureLoss for ep_aggregate / min_share).
    The pressure difference at the substations alone is not suitable, because it is also small
    when the network pump is switched off.
    Returns dict {'time', 'dp', 'cid', 'epid'} of the weak point or None."""
    graph = getNetworkGraph(cur, config, network)
    c_tables = getFeatureConnTables(cur, config, 'customer', 'p', network)
    ep_tables = getFeatureConnTables(cur, config, 'energy_plant', 'p', network)
    c_mdot_tables = {cid: t[0] for cid, t in getFeatureConnTables(cur, config, 'customer', 'mdot', network).items()}

    p_c_sup = getTimeSeries(cur, config, {cid: t[0] for cid, t in c_tables.items()}, '$p')
    p_c_ret = getTimeSeries(cur, config, {cid: t[1] for cid, t in c_tables.items()}, '$p')
    p_ep_sup = getTimeSeries(cur, config, {ep: t[0] for ep, t in ep_tables.items()}, '$p')
    p_ep_ret = getTimeSeries(cur, config, {ep: t[1] for ep, t in ep_tables.items()}, '$p')
    mdot_lines = getTimeSeries(cur, config, {lid: line_mdot_table for lid in graph}, '$mdot')
    mdot_customers = getTimeSeries(cur, config, c_mdot_tables, '$mdot')

    best = None
    for time in sorted(p_c_sup):
        if time not in mdot_lines:
            continue
        c_lid, _ = traceCustomerSupply(graph, mdot_lines[time], mdot_customers.get(time, {}), eps)
        p_c = {cid: (p, p_c_ret[time][cid]) for cid, p in p_c_sup[time].items() if cid in p_c_ret.get(time, {})}
        p_ep = {ep: (p, p_ep_ret[time][ep]) for ep, p in p_ep_sup.get(time, {}).items() if ep in p_ep_ret.get(time, {})}
        for cid, (dvar, ep) in networkPressureLoss(getCustomerPlantShares(graph, c_lid), p_c, p_ep, ep_aggregate, min_share).items():
            if best is None or dvar > best['dp']:
                best = {'time': time, 'dp': dvar, 'cid': cid, 'epid': ep}
    return best


def getCustomerLineMdot(cur, config, network=1, line_mdot_table='line_s_mdot$1', time=None, ep_aggregate='max', min_share=0.01, eps=1e-9):
    """Determines c_lid = {cid: {lid: mdot}} for the time with the maximal network pressure loss between the
    customers and the energy plants supplying them (or for the given time). The result tables of the customers
    and energy plants are derived from their templates (getFeatureConnTables).
    Returns dict {'time', 'dp', 'cid_dp', 'epid_dp', 'c_lid', 'c_ep', 'dvar', 'mdot_customers', 'warnings'}
    with dvar = {cid: (network pressure loss to the supplying plant, epid)} at this time."""
    dp = cid_dp = epid_dp = None
    if time is None:
        crit = getTimeMaxNetworkPressureLoss(cur, config, network, line_mdot_table, ep_aggregate, min_share, eps)
        if not crit:
            raise ValueError('No pressure results found for network {}'.format(network))
        time, dp, cid_dp, epid_dp = crit['time'], crit['dp'], crit['cid'], crit['epid']

    graph = getNetworkGraph(cur, config, network)
    c_tables = getFeatureConnTables(cur, config, 'customer', 'p', network)
    ep_tables = getFeatureConnTables(cur, config, 'energy_plant', 'p', network)
    c_mdot_tables = {cid: t[0] for cid, t in getFeatureConnTables(cur, config, 'customer', 'mdot', network).items()}
    mdot_lines = getTimeSeries(cur, config, {lid: line_mdot_table for lid in graph}, '$mdot', time).get(time, {})
    mdot_customers = getTimeSeries(cur, config, c_mdot_tables, '$mdot', time).get(time, {})
    c_lid, warnings = traceCustomerSupply(graph, mdot_lines, mdot_customers, eps)
    c_ep = getCustomerPlantShares(graph, c_lid)

    p_c_sup = getTimeSeries(cur, config, {cid: t[0] for cid, t in c_tables.items()}, '$p', time).get(time, {})
    p_c_ret = getTimeSeries(cur, config, {cid: t[1] for cid, t in c_tables.items()}, '$p', time).get(time, {})
    p_ep_sup = getTimeSeries(cur, config, {ep: t[0] for ep, t in ep_tables.items()}, '$p', time).get(time, {})
    p_ep_ret = getTimeSeries(cur, config, {ep: t[1] for ep, t in ep_tables.items()}, '$p', time).get(time, {})
    dvar = networkPressureLoss(c_ep, {cid: (p, p_c_ret[cid]) for cid, p in p_c_sup.items() if cid in p_c_ret},
        {ep: (p, p_ep_ret[ep]) for ep, p in p_ep_sup.items() if ep in p_ep_ret}, ep_aggregate, min_share)
    return {'time': time, 'dp': dp, 'cid_dp': cid_dp, 'epid_dp': epid_dp, 'c_lid': c_lid, 'c_ep': c_ep, 'dvar': dvar,
        'mdot_customers': mdot_customers, 'warnings': warnings}


def saveCLid(c_lid, path):
    """Saves c_lid as .json (keys as strings) or .pkl (keys as integers)."""
    if path.lower().endswith('.json'):
        with open(path, 'w', encoding='utf-8') as f:
            json.dump({str(cid): {str(lid): m for lid, m in lids.items()} for cid, lids in c_lid.items()}, f, indent=1)
    else:
        with open(path, 'wb') as f:
            pickle.dump(c_lid, f)


def loadCLid(path):
    """Loads c_lid saved with saveCLid, keys are returned as integers."""
    if path.lower().endswith('.json'):
        with open(path, encoding='utf-8') as f:
            return {int(cid): {int(lid): m for lid, m in lids.items()} for cid, lids in json.load(f).items()}
    with open(path, 'rb') as f:
        return pickle.load(f)  # nosec B301
