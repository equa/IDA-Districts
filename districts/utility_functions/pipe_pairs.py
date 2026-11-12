"""Supply/return pairs of pipe sequences for the dynamic pipe sizing: every pair (s, r) is a hydraulic circuit with
the line results line_s_mdot$s / line_s_temp$s / $r, the pipes s and r of the bundles containing both, and the
connections conn_seq s / r (conn_type_seq 1) of the customers and energy plants (OpenSpec change balance-pipe-pairs)."""
from collections import defaultdict

from .translations import tr_msg

DEFAULT_TEMPS = (70.0, 40.0)
SUPPLY, RETURN = 1, 2  # public.connections.type


def pairLabel(pair):
    return '{}/{}'.format(pair[0], pair[1])


# ---------------------------------------------------------------- suggestion
def suggestPairs(rows):
    """Pairs from the connections of the energy plants (without DB access).
    rows: [{'epid', 'conn_seq', 'type', 'temp'}] (type 1 supply, 2 return, temp = design temperature).
    Per plant the k-th supply is paired with the k-th return in conn_seq order; the pairs of all plants are united.
    Returns (pairs, warnings) with pairs = [(s, r, t_s, t_r)] sorted by s."""
    by_plant = defaultdict(list)
    for row in rows:
        by_plant[row['epid']].append(row)
    warnings = []
    found = {}
    for epid, conns in sorted(by_plant.items()):
        conns = sorted(conns, key=lambda c: c['conn_seq'])
        sup = [c for c in conns if c['type'] == SUPPLY]
        ret = [c for c in conns if c['type'] == RETURN]
        if len(sup) != len(ret):
            warnings.append(tr_msg('Energy plant {}: {} supply and {} return connections, no pair suggested from it.').format(epid, len(sup), len(ret)))
            continue
        for s, r in zip(sup, ret):
            found.setdefault((s['conn_seq'], r['conn_seq']), (temp(s['temp']), temp(r['temp'])))
    # a sequence paired differently by two plants is ambiguous
    count = defaultdict(set)
    for s, r in found:
        count[s].add((s, r))
        count[r].add((s, r))
    ambiguous = {seq for seq, pairs in count.items() if len(pairs) > 1}
    for seq in sorted(ambiguous):
        warnings.append(tr_msg('Sequence {} is paired differently by the energy plants ({}), no pair suggested for it.').format(
            seq, ', '.join(pairLabel(p) for p in sorted(count[seq]))))
    pairs = [(s, r) + found[(s, r)] for s, r in sorted(found) if s not in ambiguous and r not in ambiguous]
    return pairs, warnings


def temp(value):
    return float(value) if value is not None else None


def getPlantConnections(cur, config, network):
    """Connections (conn_type_seq 1) of the energy plants of the network for suggestPairs."""
    cur.execute("""SELECT ep.id AS epid, ctc.sequence AS conn_seq, c.type, c.temp
    FROM "{}".energy_plants ep, public.energy_plant_templates t, public.bundle_type_conns b,
        public.connection_type_connections ctc, public.connections c
    WHERE t.template = ep.template AND b.conn_bundle_type_id = t.conn_bundle_type AND b.sequence = 1
        AND ctc.connection_type_id = b.conn_type_id AND c.id = ctc.connection_id AND %s = ANY(ep.network);""".format(config['versionName']),  # nosec B608
        (int(network),))
    return [dict(row) for row in cur.fetchall()]


# ---------------------------------------------------------------- checks
def checkPairs(pairs, line_seqs, plant_seqs, customer_seqs):
    """Checks the pairs before the first simulation (without DB access).
    pairs: [(s, r)]; line_seqs / plant_seqs / customer_seqs: {id: set of sequences} of the network's lines (pipe
    sequences of the bundle) and energy plants / customers (conn_seq of conn_type_seq 1).
    Returns (errors, skipped) with skipped = {(s, r): number of customers without the connections s and r}."""
    errors = []
    used = defaultdict(int)
    for pair in pairs:
        for seq in pair:
            used[seq] += 1
    for seq in sorted(s for s, n in used.items() if n > 1):
        errors.append(tr_msg('Sequence {} is used in more than one pair.').format(seq))
    skipped = {}
    for s, r in pairs:
        label = pairLabel((s, r))
        if s == r:
            errors.append(tr_msg('Pair {}: supply and return are the same sequence.').format(label))
            continue
        if not any({s, r} <= seqs for seqs in line_seqs.values()):
            errors.append(tr_msg('Pair {}: no line of the network has a pipe bundle with both sequences.').format(label))
        if not any({s, r} <= seqs for seqs in plant_seqs.values()):
            errors.append(tr_msg('Pair {}: no energy plant of the network has the connections {} and {}.').format(label, s, r))
        n_customers = sum(1 for seqs in customer_seqs.values() if {s, r} <= seqs)
        if not n_customers:
            errors.append(tr_msg('Pair {}: no customer of the network has the connections {} and {}.').format(label, s, r))
        skipped[(s, r)] = len(customer_seqs) - n_customers
    return errors, skipped


def getNetworkSequences(cur, config, network):
    """({lid: pipe sequences}, {epid: conn_seq}, {cid: conn_seq}) of the network for checkPairs."""
    v = config['versionName']
    cur.execute("""SELECT l.id, bp.sequence FROM "{}".lines l LEFT JOIN public.bundle_pipes bp ON bp.pipe_bundle_type_id = l.pipe_bundle_type_id
    WHERE l.network = %s;""".format(v), (int(network),))  # nosec B608
    lines: dict = {}
    for row in cur.fetchall():
        seqs = lines.setdefault(row['id'], set())
        if row['sequence'] is not None:
            seqs.add(row['sequence'])
    result = [lines]
    for feature in ('energy_plant', 'customer'):
        cur.execute("""SELECT f.id, ctc.sequence FROM "{}".{}s f
        LEFT JOIN public.{}_templates t ON t.template = f.template
        LEFT JOIN public.bundle_type_conns b ON b.conn_bundle_type_id = t.conn_bundle_type AND b.sequence = 1
        LEFT JOIN public.connection_type_connections ctc ON ctc.connection_type_id = b.conn_type_id
        WHERE %s = ANY(f.network);""".format(v, feature, feature), (int(network),))  # nosec B608
        features: dict = {}
        for row in cur.fetchall():
            seqs = features.setdefault(row['id'], set())
            if row['sequence'] is not None:
                seqs.add(row['sequence'])
        result.append(features)
    return tuple(result)


def missingResultTables(cur, config, pairs):
    """Names of the line result tables of the pairs that do not exist in the version (the line temperatures are
    needed for the specific pressure loss, the mass flows for the flow tracing)."""
    cur.execute("""SELECT table_name FROM information_schema.tables WHERE table_schema = %s;""", (config['versionName'],))
    tables = {row['table_name'] for row in cur.fetchall()}
    needed = []
    for s, r in pairs:
        for table in ('line_s_mdot${}'.format(s), 'line_s_temp${}'.format(s), 'line_s_temp${}'.format(r)):
            if table not in needed:
                needed.append(table)
    return [t for t in needed if t not in tables]


# ---------------------------------------------------------------- merge of the pairs
def mergePairPipes(current, pair_pipes):
    """{lid: {seq: pipe_id}}: the current pipes of the lines (all sequences of the bundle), overwritten with the new
    pipes of every pair (pair_pipes = [{lid: {seq: pipe_id}}])."""
    merged = {lid: dict(pipes) for lid, pipes in current.items()}
    for pipes in pair_pipes:
        for lid, new in pipes.items():
            merged.setdefault(lid, {}).update(new)
    return merged


def iterationOutcome(current, merged, states, iteration, max_iter):
    """Outcome of an iteration from the merged pipes of all pairs.
    Returns (outcome, changed {lid: merged pipes}, state); state is the comparable state for the oscillation check."""
    changed = {lid: new for lid, new in merged.items() if new != current.get(lid)}
    state = sorted((lid, sorted(pipes.items())) for lid, pipes in merged.items())
    if not changed:
        outcome = 'converged'
    elif state in states:
        outcome = 'oscillation'
    else:
        outcome = 'max_iter' if iteration >= max_iter else 'changed'
    return outcome, changed, state
