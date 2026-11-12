# coding=utf-8
"""Supply/return pairs of the dynamic pipe sizing (OpenSpec change balance-pipe-pairs): pair suggestion from the
plant connections, checks, merge of the pair pipes, pipe bundles of changed lines, iteration files per pair.
The unit tests need no database; the e2e tests read the project DISTRICTS_TEST_PAIRS_PROJECT (default hc_network:
2-pipe lines 1/3, 4-pipe lines 1-4) if it exists on the test server."""
import os

import pytest

from districts.utility_functions.dynamic_sizing_results import iterationRows, normalizedSummary
from districts.utility_functions.hydraulic_balancing import getLineData, getPairLines, planPipeBundles
from districts.utility_functions.pipe_pairs import (
    checkPairs, getNetworkSequences, getPlantConnections, iterationOutcome, mergePairPipes, missingResultTables, suggestPairs,
)

# connections of the energy plant of hc_network (template 2): 1 supply 70, 2 supply 10, 3 return 30, 4 return 18
HC_PLANT = [{'epid': 1, 'conn_seq': 1, 'type': 1, 'temp': 70}, {'epid': 1, 'conn_seq': 2, 'type': 1, 'temp': 10},
            {'epid': 1, 'conn_seq': 3, 'type': 2, 'temp': 30}, {'epid': 1, 'conn_seq': 4, 'type': 2, 'temp': 18}]

POS = {1: (-0.6, 1.0, 2), 2: (-0.2, 1.0, 2), 3: (0.2, 1.0, 2), 4: (0.6, 1.0, 2)}


def bundle(pipes):
    return {seq: {'pipe_id': pid, 'x': POS[seq][0], 'y': POS[seq][1], 'ambient': POS[seq][2]} for seq, pid in pipes.items()}


# ---------------------------------------------------------------- pipe bundles of changed lines
def test_four_pipe_line_keeps_the_pipes_of_the_other_pair():
    # heating 1/3 reduced from pipe 5 to 4, cooling 2/4 (pipe 6) not sized in this pair
    rows = {9: bundle({1: 5, 2: 6, 3: 5, 4: 6}), 2: bundle({1: 4, 3: 4})}
    assign, new = planPipeBundles(rows, {10: 9}, {10: {1: 4, 3: 4}})
    assert assign == {10: ('new', 0)}
    assert {seq: row['pipe_id'] for seq, row in new[0].items()} == {1: 4, 2: 6, 3: 4, 4: 6}
    assert all((row['x'], row['y'], row['ambient']) == POS[seq] for seq, row in new[0].items())


def test_unpaired_sequence_is_kept():
    rows = {1: bundle({1: 5, 2: 5, 3: 7})}
    assign, new = planPipeBundles(rows, {10: 1}, {10: {1: 4, 2: 4}})
    assert {seq: row['pipe_id'] for seq, row in new[assign[10][1]].items()} == {1: 4, 2: 4, 3: 7}


def test_existing_bundle_is_reused():
    rows = {9: bundle({1: 5, 2: 6, 3: 5, 4: 6}), 11: bundle({1: 4, 2: 6, 3: 4, 4: 6})}
    assert planPipeBundles(rows, {10: 9}, {10: {1: 4, 3: 4}}) == ({10: ('bundle', 11)}, [])


def test_unchanged_line_gets_no_bundle():
    rows = {9: bundle({1: 5, 2: 6, 3: 5, 4: 6})}
    assert planPipeBundles(rows, {10: 9}, {10: {1: 5, 3: 5}}) == ({}, [])


def test_lines_with_the_same_new_pipes_share_one_new_bundle():
    rows = {9: bundle({1: 5, 2: 6, 3: 5, 4: 6})}
    assign, new = planPipeBundles(rows, {10: 9, 11: 9}, {10: {1: 4, 3: 4}, 11: {1: 4, 3: 4}})
    assert assign == {10: ('new', 0), 11: ('new', 0)} and len(new) == 1


# ---------------------------------------------------------------- pair suggestion
def test_heating_and_cooling_pairs_from_the_plant_connections():
    assert suggestPairs(HC_PLANT) == ([(1, 3, 70.0, 30.0), (2, 4, 10.0, 18.0)], [])


def test_single_circuit():
    rows = [{'epid': 5, 'conn_seq': 1, 'type': 1, 'temp': 75}, {'epid': 5, 'conn_seq': 2, 'type': 2, 'temp': 45}]
    assert suggestPairs(rows) == ([(1, 2, 75.0, 45.0)], [])


def test_two_plants_with_the_same_pairs_and_one_with_unequal_counts():
    second = [dict(row, epid=2) for row in HC_PLANT]
    third = [{'epid': 3, 'conn_seq': 1, 'type': 1, 'temp': 70}]
    pairs, warnings = suggestPairs(HC_PLANT + second + third)
    assert pairs == [(1, 3, 70.0, 30.0), (2, 4, 10.0, 18.0)]
    assert len(warnings) == 1 and '3' in warnings[0]


def test_contradicting_plants():
    other = [{'epid': 2, 'conn_seq': 1, 'type': 1, 'temp': 70}, {'epid': 2, 'conn_seq': 4, 'type': 2, 'temp': 30}]
    pairs, warnings = suggestPairs(HC_PLANT + other)
    # 1 is paired with 3 and with 4, 4 with 1 and with 2: every pair touches an ambiguous sequence
    assert pairs == []
    assert len(warnings) == 2


def test_connections_without_type_give_no_pair():
    rows = [{'epid': 1, 'conn_seq': 1, 'type': None, 'temp': None}, {'epid': 1, 'conn_seq': 2, 'type': 2, 'temp': 40}]
    pairs, warnings = suggestPairs(rows)
    assert pairs == [] and len(warnings) == 1


# ---------------------------------------------------------------- checks
LINES = {1: {1, 3}, 2: {1, 3}, 3: {1, 2, 3, 4}}
PLANTS = {1: {1, 2, 3, 4}}
CUSTOMERS = {10: {1, 3}, 11: {1, 3}, 12: {1, 2, 3, 4}}


def test_valid_pairs_count_the_skipped_customers():
    assert checkPairs([(1, 3), (2, 4)], LINES, PLANTS, CUSTOMERS) == ([], {(1, 3): 0, (2, 4): 2})


@pytest.mark.parametrize('pairs, expected', [
    ([(1, 3), (3, 4)], 'Sequence 3'),
    ([(1, 1)], 'same sequence'),
    ([(5, 6)], 'no energy plant'),
])
def test_invalid_pairs(pairs, expected):
    errors, _ = checkPairs(pairs, LINES, PLANTS, CUSTOMERS)
    assert any(expected in e for e in errors), errors


def test_pair_without_line():
    errors, _ = checkPairs([(2, 4)], {1: {1, 3}, 2: {1, 3}}, PLANTS, CUSTOMERS)
    assert any('no line' in e for e in errors), errors


def test_pair_without_customer():
    errors, _ = checkPairs([(2, 4)], LINES, PLANTS, {10: {1, 3}})
    assert any('no customer' in e for e in errors)


# ---------------------------------------------------------------- merge and outcome
CURRENT = {1: {1: 5, 3: 5}, 3: {1: 5, 2: 6, 3: 5, 4: 6}}


def test_merge_of_the_pairs():
    merged = mergePairPipes(CURRENT, [{1: {1: 4, 3: 4}, 3: {1: 5, 3: 5}}, {3: {2: 5, 4: 5}}])
    assert merged == {1: {1: 4, 3: 4}, 3: {1: 5, 2: 5, 3: 5, 4: 5}}
    assert CURRENT[3] == {1: 5, 2: 6, 3: 5, 4: 6}  # not modified


def test_only_one_pair_changes():
    merged = mergePairPipes(CURRENT, [{1: {1: 5, 3: 5}, 3: {1: 5, 3: 5}}, {3: {2: 5, 4: 5}}])
    outcome, changed, _ = iterationOutcome(CURRENT, merged, [], 1, 5)
    assert outcome == 'changed' and set(changed) == {3}


def test_no_pair_changes():
    merged = mergePairPipes(CURRENT, [{1: {1: 5, 3: 5}}, {3: {2: 6, 4: 6}}])
    assert iterationOutcome(CURRENT, merged, [], 2, 5)[0] == 'converged'


def test_oscillation_and_max_iter():
    merged = mergePairPipes(CURRENT, [{1: {1: 4, 3: 4}}])
    _, _, state = iterationOutcome(CURRENT, merged, [], 1, 5)
    assert iterationOutcome(CURRENT, merged, [state], 2, 5)[0] == 'oscillation'
    assert iterationOutcome(CURRENT, merged, [], 5, 5)[0] == 'max_iter'


# ---------------------------------------------------------------- iteration files
def pair_result(supply, ret, n_changed):
    return {'supply': supply, 'return': ret, 'temps': [None, None], 'time': '2026-01-01 12:00', 'cid_weak': 10, 'epid_weak': 1,
            'dp_net_weak': 5e4, 'cid_target': 10, 'dp_target': 1e5, 'quota': 0.5, 'spread_sized': 2e4, 'n_presized': 0,
            'n_balancing_steps': 3, 'n_changed': n_changed, 'n_customers_skipped': 0,
            'customers': {'10': {'dp': 1e5, 'dp_sized': 1e5, 'dp_net': 5e4, 'epid': 1, 'time': ''},
                          '11': {'dp': 1.5e5, 'dp_sized': 1.2e5, 'dp_net': 3e4, 'epid': 1, 'time': ''}},
            'lines': {}}


def test_file_of_an_earlier_run_is_read_as_pair_1_2():
    old = {k: v for k, v in pair_result(1, 2, 4).items() if k not in ('supply', 'return', 'temps', 'n_customers_skipped')}
    old.update(iteration=2, started='2026-01-01T10:00:00', outcome='changed')
    summary = normalizedSummary(old)
    assert summary['iteration'] == 2 and summary['outcome'] == 'changed' and len(summary['pairs']) == 1
    pair = summary['pairs'][0]
    assert (pair['supply'], pair['return'], pair['cid_weak'], pair['n_changed']) == (1, 2, 10, 4)
    assert iterationRows(summary)[0][:10] == (2, '1/2', '2026-01-01 12:00', '10 (1)', 1.0, 1.5, 0.5, 0.2, 50, 4)


def test_table_rows_per_pair():
    summary = {'iteration': 1, 'started': '', 'outcome': 'changed', 'n_changed': 3, 'pairs': [pair_result(1, 3, 2), pair_result(2, 4, 1)]}
    rows = iterationRows(summary)
    assert [(row[0], row[1], row[-2]) for row in rows] == [(1, '1/3', 2), (1, '2/4', 1)]
    assert normalizedSummary(summary) is summary


# ---------------------------------------------------------------- pair table of the dialog
@pytest.fixture
def pair_dialog(qgis_app):
    from districts.dynamic_pipe_sizing import DynamicPipeSizingDialog
    dlg = DynamicPipeSizingDialog(main=None)  # no network in the combo, so no DB access
    yield dlg
    dlg.close()


def test_pair_table_temperatures_are_editable(pair_dialog):
    dlg = pair_dialog
    dlg.addPairRow(1, 3, 70.0, 30.0)
    dlg.table_pairs.item(0, 2).setText('65,5')
    assert dlg.pairs() == ([(1, 3, 65.5, 30.0)], [])
    dlg.table_pairs.item(0, 1).setText('4')  # other sequence: the suggested temperatures do not belong to it
    assert dlg.pairs() == ([(1, 4, None, None)], [])


def test_pair_table_invalid_input(pair_dialog):
    dlg = pair_dialog
    assert dlg.pairs()[1]  # no pair
    dlg.addPairRow(1, 3, None, None)
    dlg.table_pairs.item(0, 3).setText('warm')
    assert len(dlg.pairs()[1]) == 1
    dlg.table_pairs.item(0, 3).setText('')
    dlg.table_pairs.item(0, 0).setText('0')
    assert len(dlg.pairs()[1]) == 1


# ---------------------------------------------------------------- e2e: project with heating and cooling pairs
PAIRS_PROJECT = os.environ.get('DISTRICTS_TEST_PAIRS_PROJECT', 'hc_network')
PAIRS_VERSION = os.environ.get('DISTRICTS_TEST_PAIRS_VERSION', 'base1')


@pytest.fixture(scope='module')
def hc_cursor():
    """Read-only cursor of the project with heating (1/3) and cooling (2/4) pipes; skipped if it does not exist."""
    import psycopg2
    import psycopg2.extras
    user, password = os.environ.get('DISTRICTS_TEST_DB_USER'), os.environ.get('DISTRICTS_TEST_DB_PASSWORD')
    if not user or password is None:
        pytest.skip('DISTRICTS_TEST_DB_USER / DISTRICTS_TEST_DB_PASSWORD not set')
    try:
        conn = psycopg2.connect(host=os.environ.get('DISTRICTS_TEST_DB_HOST', 'localhost'), port=int(os.environ.get('DISTRICTS_TEST_DB_PORT', '5432')),
            user=user, password=password, dbname=PAIRS_PROJECT, connect_timeout=5)
    except psycopg2.OperationalError as e:
        pytest.skip('project {} not available: {}'.format(PAIRS_PROJECT, str(e).splitlines()[0]))
    conn.set_session(readonly=True, autocommit=True)
    yield conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor), {'versionName': PAIRS_VERSION}
    conn.close()


@pytest.mark.e2e
def test_hc_network_pairs_and_checks(hc_cursor):
    cur, config = hc_cursor
    pairs, warnings = suggestPairs(getPlantConnections(cur, config, 1))
    assert [(s, r) for s, r, _, _ in pairs] == [(1, 3), (2, 4)] and not warnings
    errors, skipped = checkPairs([(1, 3), (2, 4)], *getNetworkSequences(cur, config, 1))
    assert not errors
    assert skipped[(1, 3)] == 0 and skipped[(2, 4)] > 0  # heating-only customers are not part of the cooling pair


@pytest.mark.e2e
def test_hc_network_cooling_pair_only_on_the_four_pipe_lines(hc_cursor):
    cur, config = hc_cursor
    heating, cooling = getPairLines(cur, config, 1, (1, 3)), getPairLines(cur, config, 1, (2, 4))
    assert cooling and cooling < heating
    lines = getLineData(cur, config, None, 1, (2, 4), (10.0, 18.0))
    assert set(lines) == cooling and all(set(line['pipes']) == {2, 4} for line in lines.values())


@pytest.mark.e2e
def test_hc_network_missing_line_results(hc_cursor):
    cur, config = hc_cursor
    cur.execute("""SELECT table_name FROM information_schema.tables WHERE table_schema = %s AND table_name LIKE 'line_s_%%';""", (PAIRS_VERSION,))
    present = {row['table_name'] for row in cur.fetchall()}
    expected = [t for t in ('line_s_mdot$1', 'line_s_temp$1', 'line_s_temp$3', 'line_s_mdot$2', 'line_s_temp$2', 'line_s_temp$4') if t not in present]
    assert missingResultTables(cur, config, [(1, 3), (2, 4)]) == expected
