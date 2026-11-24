# coding=utf-8
"""Network built in stages (OpenSpec change network-stages): NPV by stage years; e2e the stage check, the input check
of every stage version and the report."""
import contextlib
import os

import pytest

from districts.utility_functions.economics import netPresentValue, rangeFactor, stageYears, stagedNetPresentValue


def scenario(interest=3.0, period=40, residual=True):
    groups = {g: {'cost_group': g, 'start_price': 0.25 if g == 'electricity' else None, 'escalation_pct': 0.0}
              for g in ('electricity', 'heat', 'cold', 'maintenance', 'investment', 'fuel')}
    return {'scenario': {'interest_pct': interest, 'period_a': period, 'residual_value': residual}, 'groups': groups, 'levels': {}}


def test_stage_years():
    assert stageYears([0, 10, 20], 40) == [(1, 10), (11, 20), (21, 40)]
    assert stageYears([0], 40) == [(1, 40)]


def test_one_stage_is_the_npv_of_the_version():
    sc = scenario()
    items = [{'cost': 100000.0, 'lifetime': 40, 'maintenance_pct': 1.0}, {'cost': 3000.0, 'lifetime': 15, 'maintenance_pct': 2.5}]
    yearly = {'pump_energy': 800.0}
    single = netPresentValue(sc, items, yearly, {'plant_energy': {'fuel': 5000.0}})
    staged = stagedNetPresentValue(sc, [{'start': 0, 'investments': items, 'yearly': yearly, 'by_carrier': {'plant_energy': {'fuel': 5000.0}}}])
    assert staged['npv'] == pytest.approx(single['npv'])


def test_line_of_a_later_stage_and_operating_costs_per_stage():
    sc = scenario(residual=False)
    # stage 2 (from year 10) adds a line of 10 000 € (lifetime 40) and raises the pump energy from 1000 to 1500 €/a
    stages = [{'start': 0, 'investments': [], 'yearly': {'pump_energy': 1000.0}},
              {'start': 10, 'investments': [{'cost': 10000.0, 'lifetime': 40, 'maintenance_pct': 0.0}], 'yearly': {'pump_energy': 1500.0}}]
    result = stagedNetPresentValue(sc, stages)
    assert result['split']['investment'] == pytest.approx(10000 / 1.03 ** 10)
    expected = 1000 * rangeFactor(3.0, 1, 10) + 1500 * rangeFactor(3.0, 11, 40)
    assert result['split']['pump_energy'] == pytest.approx(expected)
    assert len(result['stages']) == 2


def test_replacement_and_residual_value_count_from_the_stage_start():
    sc = scenario(interest=0.0, period=40)
    # pumps of a stage from year 20 with a lifetime of 15: bought in 20 and 35, 10 of 15 years left at the end
    result = stagedNetPresentValue(sc, [{'start': 0, 'investments': []},
                                        {'start': 20, 'investments': [{'cost': 1500.0, 'lifetime': 15, 'maintenance_pct': 0.0}]}])
    assert result['split']['investment'] == pytest.approx(3000.0)
    assert result['split']['residual'] == pytest.approx(-1500.0 * 10 / 15)


def test_coupled_step_equals_one_model_for_identical_stages():
    """two identical stages (years 1-10 and 11-40): the investment counts once, the operating costs over both ranges,
    so the step equals the step of one model over the whole period"""
    from districts.utility_functions.cost_model import stagedStep
    from .test_cost_model import model
    single, _ = model().step()
    first, second = model(), model()
    first.operating, second.operating, second.start_year = (1, 10), (11, 40), 10
    staged, _ = stagedStep([first, second])
    # the step is keyed by the line groups (root: stage 1, line ID)
    assert set(staged) == {(0, lid) for lid in single}
    for lid in single:
        assert staged[(0, lid)]['dnpv'] == pytest.approx(single[lid]['dnpv'])
        assert staged[(0, lid)]['pipes'] == single[lid]['pipes']


def test_a_limit_in_a_later_stage_rejects_the_change():
    from districts.utility_functions.cost_model import stagedStep
    from .test_cost_model import model
    free, limited = model(pipes=3), model(pipes=3, p_plant=None)
    limited.dp_spez_max = 0.0  # every smaller pipe exceeds the peak limit in this stage
    _, rejected = stagedStep([free, limited])
    assert any('peak' in reasons for reasons in rejected.values())


def evaluation(pipe_cost, pump_kw, pump_eur, penalty_base=None):
    pump = {'cost': pump_kw * 100.0, 'lifetime': 40, 'maintenance_pct': 0.0, 'name': 'pumps'}
    return {'items': {('pipe', 1): {'cost': pipe_cost, 'lifetime': 40, 'maintenance_pct': 0.0, 'name': 'DN 50'}}, 'pump_item': pump,
            'pump_kw': pump_kw, 'costs': {'pump_energy': pump_eur}, 'npv_yearly': {'pump_energy': pump_eur}, 'by_carrier': None}


def test_npv_of_two_stage_versions():
    """stage 2 (year 10) adds 50 000 € of pipes and 5 kW of pumps; its pump energy is higher; a penalty only in stage 2"""
    from districts.utility_functions.network_stages import stagesNpv
    sc = scenario(residual=False)
    stages = [{'version': 'base1', 'start': 0}, {'version': 'base1_s2', 'start': 10}]
    result = stagesNpv(sc, stages, [evaluation(100000.0, 10.0, 1000.0), evaluation(150000.0, 15.0, 1500.0)], [0.0, 200.0])
    assert result['split']['investment'] == pytest.approx(100000 + 1000 + (50000 + 500) / 1.03 ** 10)
    assert result['split']['pump_energy'] == pytest.approx(1000 * rangeFactor(3.0, 1, 10) + 1500 * rangeFactor(3.0, 11, 40))
    assert result['split']['penalties'] == pytest.approx(200 * rangeFactor(3.0, 11, 40))
    assert result['npv'] == pytest.approx(sum(result['split'].values()))


def test_report_terms_of_each_stage_add_up_to_its_npv():
    """the terms saved per stage for the report (npvRecord with stagesNpv's inputs): their sum and the penalty are the
    stage's NPV; the first purchase in the stage's start year, replacements and residual value of its pumps"""
    from districts.cost_optimization import npvRecord
    from districts.utility_functions.network_stages import stagesNpv
    sc = scenario(residual=True)
    evaluations = [dict(evaluation(100000.0, 10.0, 1000.0), scenario=sc, energy={}), dict(evaluation(150000.0, 15.0, 1500.0), scenario=sc, energy={})]
    for e in evaluations:
        e['pump_item']['lifetime'] = 20
    stages = [{'version': 'base1', 'start': 0}, {'version': 'base1_s2', 'start': 10}]
    result = stagesNpv(sc, stages, evaluations, [0.0, 200.0])
    for part, e, penalty, inputs in zip(result['stages'], evaluations, [0.0, 200.0], result['inputs']):
        record = npvRecord(e, penalty, part['split']['penalties'], stage=inputs)
        assert sum(t['value'] for t in record['terms']) + record['penalties'] == pytest.approx(part['npv'])
        assert record['factors']['penalties'] == pytest.approx(rangeFactor(3.0, *inputs['operating']))
    stage2 = npvRecord(evaluations[1], 200.0, result['stages'][1]['split']['penalties'], stage=result['inputs'][1])
    pumps = next(t for t in stage2['terms'] if t['group'] == 'investment' and t['kind'] == 'pumps')
    # 500 € of pumps bought in year 10, replaced in 30; 10 of 20 years left at year 40
    assert pumps['years'] == [10, 30] and pumps['power_kw'] == pytest.approx(5.0)
    assert pumps['first_value'] == pytest.approx(500 / 1.03 ** 10) and pumps['replacement_value'] == pytest.approx(500 / 1.03 ** 30)
    residual = next(t for t in stage2['terms'] if t['group'] == 'residual' and t['kind'] == 'pumps')
    assert residual['value'] == pytest.approx(-500 * 10 / 20 / 1.03 ** 40)


def test_report_of_a_staged_run_shows_the_terms_per_stage():
    """the report of a run over stages: the calculation per iteration and stage (not 'not saved'), the investment table
    with first purchase, replacements and residual value, the parts per stage and the stage timing"""
    from districts.cost_optimization import npvRecord
    from districts.utility_functions.iteration_report import Report, investmentSections, npvCalculation, stageSections
    from districts.utility_functions.network_stages import stagesNpv
    sc = scenario(residual=True)
    stages = [{'version': 'base1', 'start': 0}, {'version': 'base1_s2', 'start': 10}]
    rows = []
    for k, cost in enumerate((150000.0, 140000.0)):
        evaluations = [dict(evaluation(100000.0, 10.0, 1000.0), scenario=sc, energy={}), dict(evaluation(cost, 15.0, 1500.0), scenario=sc, energy={})]
        result = stagesNpv(sc, stages, evaluations, [0.0, 200.0])
        rows.append({'iteration': k, 'npv': result['npv'], 'split': result['split'], 'economics': None,
                     'stages': [{'version': s['version'], 'start': s['start'], 'npv': part['npv'], 'split': part['split'], 'climate': '',
                                 'economics': npvRecord(e, p, part['split']['penalties'], stage=inputs)}
                                for s, part, e, p, inputs in zip(stages, result['stages'], evaluations, [0.0, 200.0], result['inputs'])]})
    report = Report('t', 's')
    npvCalculation(report, rows)
    investmentSections(report, rows)
    stageSections(report, rows, {'stages': stages})
    page = report.html()
    assert 'were not saved' not in page
    assert 'Iteration 1 / stage 2' in page and 'Investment, replacements and residual value' in page
    assert 'Net present value per stage and part [€]' in page and 'Investment year [a]' in page
    assert 'operating years' in page and '11…40' in page


def test_lines_new_in_stage_2_are_their_own_groups():
    """a stage 2 whose lines lie on no stage-1 line: each is its own group, its investment from year 10"""
    from districts.utility_functions.cost_model import stagedStep
    from .test_cost_model import model
    first, second = model(), model()
    first.operating, second.operating, second.start_year = (1, 10), (11, 40), 10
    second.root = {lid: (1, lid) for lid in second.lines}
    chosen, _ = stagedStep([first, second])
    assert all(root[0] in (0, 1) for root in chosen)
    assert any(root[0] == 1 for root in chosen) or not chosen


# ---------------------------------------------------------------- e2e: stage check and report on a project
@contextlib.contextmanager
def stage2_mappings(cur, stage2, expressions):
    """customer mapping expressions {key: expression} in public.model_parms and submodel 0 for the first customer of
    stage 2 only (an expression dividing by "submodel" fails there); removed and restored afterwards: ({key: id}, cid)"""
    ids = {}
    cur.execute('SELECT id, submodel FROM "{}".customers ORDER BY id LIMIT 1;'.format(stage2))  # nosec B608
    customer = cur.fetchone()
    assert customer, 'stage 2 has no customer'
    try:
        for key, expression in expressions.items():
            # explicit id as the mapping dialog writes it: the rows of the project template are inserted with ids, the serial lags behind
            cur.execute("INSERT INTO public.model_parms (id, type, parm_name, model_name, mapping_expression, macro_name, mapping_direction) "
                        "SELECT COALESCE(max(id), 0) + 1, 1, 'P_' || %s, 'MODEL', %s, ':FEATURE', '-->' FROM public.model_parms RETURNING id;",
                        (key, expression))
            ids[key] = cur.fetchone()['id']
        cur.execute('UPDATE "{}".customers SET submodel = 0 WHERE id = %s;'.format(stage2), (customer['id'],))  # nosec B608
        yield ids, customer['id']
    finally:
        cur.execute('UPDATE "{}".customers SET submodel = %s WHERE id = %s;'.format(stage2), (customer['submodel'], customer['id']))  # nosec B608
        cur.execute('DELETE FROM public.model_parms WHERE id = ANY(%s);', (list(ids.values()),))


def getPipeBundlesOf(cur, bid):
    """the pipe ids of a bundle"""
    from districts.utility_functions.hydraulic_balancing import getPipeBundles
    return list((getPipeBundles(cur).get(bid) or {}).values())


@pytest.fixture(scope='class')
def staged(request, districts_plugin, errors):
    from types import SimpleNamespace
    from .test_workflow import delete_project, project_name_for
    state = SimpleNamespace(plugin=districts_plugin, project_name=project_name_for('stages'))
    yield state
    if not request.config.getoption('--keep-projects'):
        delete_project(districts_plugin, errors, state.project_name)


@pytest.mark.e2e
@pytest.mark.incremental
class TestStages:
    def test_create_project_and_stage_2(self, staged, errors):
        from districts.utility_functions.hydraulic_balancing import createChildVersion
        from .test_workflow import HEATING, create_project
        plugin = staged.plugin
        create_project(plugin, errors, staged.project_name, HEATING)
        errors.check()
        staged.stage1 = plugin.config['versionName']
        staged.stage2 = staged.stage1 + '_s2'
        createChildVersion(plugin.cur, plugin.config, plugin.plugin_dir, staged.stage2, 'stage 2')
        assert plugin.config['versionName'] == staged.stage1

    def test_stage_check(self, staged):
        from districts.utility_functions.network_stages import stageProblems
        cur = staged.plugin.cur
        stages = [{'version': staged.stage1, 'start': 0}, {'version': staged.stage2, 'start': 10}]
        assert stageProblems(cur, stages) == []
        assert [p[0] for p in stageProblems(cur, list(reversed(stages)))] == ['first_start', 'start_order', 'not_descendant']
        cur.execute('SELECT min(id) AS id FROM "{}".lines;'.format(staged.stage2))  # nosec B608
        lid = cur.fetchone()['id']
        cur.execute('UPDATE "{}".lines SET geom = ST_Translate(geom, 5, 0) WHERE id = %s;'.format(staged.stage2), (lid,))  # nosec B608
        problems = stageProblems(cur, stages)
        assert problems and problems[0][0] == 'lines' and str(lid) in problems[0][1]

    def test_lines_split_and_renumbered_by_a_pipe_laying(self, staged):
        """a pipe laying in stage 2 splits a line and gives another a new ID: matched by geometry (network-stages D7);
        the segments inherit the pipes of the stage-1 line; a write into stage 1 is not copied by ID into stage 2 (D8)"""
        from districts.utility_functions.network_stages import inheritPipes, stageProblems, stageRoots, writeBundles
        cur = staged.plugin.cur
        s1, s2 = staged.stage1, staged.stage2
        cur.execute('UPDATE "{b}".lines n SET geom = o.geom FROM "{a}".lines o WHERE o.id = n.id;'.format(a=s1, b=s2))  # nosec B608
        cur.execute('SELECT id, pipe_bundle_type_id AS bid FROM "{}".lines ORDER BY ST_Length(geom) DESC LIMIT 2;'.format(s1))  # nosec B608
        split_line, renumbered = [row['id'] for row in cur.fetchall()]
        cur.execute('SELECT COALESCE(max(id), 0) + 1000 AS id FROM "{}".lines;'.format(s2))  # nosec B608
        new_id = cur.fetchone()['id']
        cur.execute("""INSERT INTO "{b}".lines (id, geom, pipe_bundle_type_id)
            SELECT %s, ST_LineSubstring(geom, 0.5, 1), NULL FROM "{b}".lines WHERE id = %s;
            UPDATE "{b}".lines SET geom = ST_LineSubstring(geom, 0, 0.5), pipe_bundle_type_id = NULL WHERE id = %s;
            UPDATE "{b}".lines SET id = %s WHERE id = %s;""".format(b=s2), (new_id, split_line, split_line, new_id + 1, renumbered))  # nosec B608
        stages = [{'version': s1, 'start': 0}, {'version': s2, 'start': 10}]
        assert stageProblems(cur, stages) == []
        roots = stageRoots(cur, [s1, s2])
        assert roots[1][new_id] == (0, split_line) and roots[1][split_line] == (0, split_line) and roots[1][new_id + 1] == (0, renumbered)
        assert inheritPipes(cur, [s1, s2], roots) >= 2
        cur.execute('SELECT id, pipe_bundle_type_id AS bid FROM "{}".lines WHERE id IN (%s, %s);'.format(s2), (split_line, new_id))  # nosec B608
        cur.execute('SELECT pipe_bundle_type_id AS bid FROM "{}".lines WHERE id = %s;'.format(s1), (split_line,))  # nosec B608
        root_bid = cur.fetchone()['bid']
        cur.execute('SELECT pipe_bundle_type_id AS bid FROM "{}".lines WHERE id IN (%s, %s);'.format(s2), (split_line, new_id))  # nosec B608
        assert {row['bid'] for row in cur.fetchall()} == {root_bid}
        # stage 1 is the loaded version with the triggers of the version handling: the write stays in stage 1
        cur.execute('SELECT id, pipe_bundle_type_id AS bid FROM "{}".lines WHERE id = %s;'.format(s2), (split_line,))  # nosec B608
        before = cur.fetchone()['bid']
        cur.execute('SELECT id FROM public.pipe_bundle_types WHERE id <> %s ORDER BY id LIMIT 1;', (root_bid,))
        other = cur.fetchone()['id']
        writeBundles(cur, s1, {split_line: other})
        cur.execute('SELECT pipe_bundle_type_id AS bid FROM "{}".lines WHERE id = %s;'.format(s2), (split_line,))  # nosec B608
        assert cur.fetchone()['bid'] == before
        cur.execute('SELECT count(*) AS n FROM pg_trigger t JOIN pg_class c ON c.oid = t.tgrelid JOIN pg_namespace n ON n.oid = c.relnamespace '
                    "WHERE n.nspname = %s AND c.relname = 'lines' AND t.tgname = 'column_update_trigger' AND t.tgenabled = 'D';", (s1,))
        assert cur.fetchone()['n'] == 0  # enabled again
        staged.split = (split_line, new_id)

    def test_map_of_each_stage(self, staged):
        """'Show on map' of a run over stages: a group per stage version with its own lines and pipes; the step on the
        stage-1 line shows on both segments of the split in stage 2; the new deficit in the stage it occurs in"""
        from qgis.core import QgsProject
        from districts.cost_optimization import lineState
        from districts.utility_functions.cost_optimization_layers import costGroup, removeCostLayers, showCostIterations
        plugin = staged.plugin
        cur = plugin.cur
        s1, s2 = staged.stage1, staged.stage2
        split_line, new_id = staged.split
        states = {v: {str(lid): bid for lid, bid in lineState(cur, v).items()} for v in (s1, s2)}
        cur.execute('SELECT min(id) AS id FROM "{}".customers;'.format(s2))  # nosec B608
        cid = cur.fetchone()['id']
        pid = next(iter(getPipeBundlesOf(cur, states[s1][str(split_line)])))
        rows = [{'iteration': 0, 'npv': 2.0, 'split': {}, 'state': states[s2], 'stage_states': states, 'stage_penalty': {s1: [], s2: []},
                 'steps': [{'line': split_line, 'stage': 1, 'larger': True, 'before': {'1': pid}, 'after': {'1': pid}, 'dnpv': -1.0}]},
                {'iteration': 1, 'npv': 1.0, 'split': {}, 'state': states[s2], 'stage_states': states, 'stage_penalty': {s1: [], s2: [cid]}}]
        try:
            showCostIterations(cur, plugin.config, [1], rows)
            group = costGroup(1)
            assert [child.name() for child in group.children()] == [s1, s2]
            assert [child.isVisible() for child in group.children()] == [False, True]

            def layer(stage, name):
                found = [n.layer() for n in group.findGroup(stage).findLayers() if n.layer().name() == name]
                return found[0] if found else None
            changed = 'Lines – changed for this iteration'
            assert {f['id'] for f in layer(s1, changed).getFeatures()} == {split_line}
            assert {f['id'] for f in layer(s2, changed).getFeatures()} == {split_line, new_id}
            assert layer(s1, 'Customers – new deficit (penalty)') is None
            assert {f['id'] for f in layer(s2, 'Customers – new deficit (penalty)').getFeatures()} == {cid}
            cur.execute('SELECT count(*) AS n FROM "{}".lines;'.format(s2))  # nosec B608
            assert layer(s2, 'Lines – inner diameter [mm]').featureCount() == cur.fetchone()['n']
        finally:
            removeCostLayers()
        assert QgsProject.instance().layerTreeRoot().findGroup('Cost optimization') is None

    def test_version_handling_between_stages(self, staged):
        """network-stages D11: the triggers of the loaded stage off and on again; the stage versions linked into one
        chain; the lines the version handling would copy wrongly by ID (the split and the renumbered line)"""
        from districts.utility_functions.db import getParentVersion
        from districts.utility_functions.hydraulic_balancing import createChildVersion
        from districts.utility_functions.network_stages import VERSION_TRIGGERS, isDescendant, linkStages, stageLinks, versionTriggers
        plugin = staged.plugin
        cur = plugin.cur
        s1, s2 = staged.stage1, staged.stage2
        split_line, new_id = staged.split

        def disabled():
            cur.execute("""SELECT count(*) FILTER (WHERE t.tgenabled = 'D') AS off, count(*) AS n FROM pg_trigger t
                JOIN pg_class c ON c.oid = t.tgrelid JOIN pg_namespace n ON n.oid = c.relnamespace
                WHERE n.nspname = %s AND t.tgname = ANY(%s);""", (s1, list(VERSION_TRIGGERS)))
            row = cur.fetchone()
            return row['off'], row['n']
        cur.execute('SELECT p.id FROM "{a}".lines p JOIN "{b}".lines n ON n.id = p.id AND ST_Equals(n.geom, p.geom) ORDER BY p.id LIMIT 1;'.format(a=s1, b=s2))  # nosec B608
        same = cur.fetchone()['id']
        cur.execute('SELECT id FROM public.pipe_bundle_types ORDER BY id DESC LIMIT 1;')
        bid = cur.fetchone()['id']
        cur.execute('SELECT pipe_bundle_type_id AS bid FROM "{}".lines WHERE id = %s;'.format(s2), (same,))  # nosec B608
        before = cur.fetchone()['bid']
        assert versionTriggers(cur, s1, False) > 0 and disabled()[0] == disabled()[1]
        try:
            cur.execute('UPDATE "{}".lines SET pipe_bundle_type_id = %s WHERE id = %s;'.format(s1), (bid, same))  # nosec B608
            cur.execute('SELECT pipe_bundle_type_id AS bid FROM "{}".lines WHERE id = %s;'.format(s2), (same,))  # nosec B608
            assert cur.fetchone()['bid'] == before  # stays in stage 1
        finally:
            versionTriggers(cur, s1, True)
        assert disabled()[0] == 0 and versionTriggers(cur, s1, True) == 0
        s3 = s1 + '_s3'
        createChildVersion(cur, plugin.config, plugin.plugin_dir, s3, 'stage 3')
        assert getParentVersion(cur, s3) == s1
        linkStages(cur, [s2, s3])
        assert getParentVersion(cur, s3) == s2 and isDescendant(cur, s3, s1)
        links = stageLinks(cur, s1, s2)
        assert split_line in links['other'] and same not in links['other']
        assert {new_id, new_id + 1} <= set(links['not_reached']) and split_line not in links['not_reached']

    def test_input_data_of_all_stages(self, staged):
        """the input check of the cost optimization over both stage versions: a mapping expression failing in both is
        one finding with both versions; one failing only for a customer of stage 2 names stage 2 only"""
        from collections import defaultdict
        from districts.cost_optimization import inputDataMessages, skippedRules
        from districts.utility_functions.model_checks import checkVersions
        plugin = staged.plugin
        cur = plugin.cur
        s1, s2 = staged.stage1, staged.stage2
        with stage2_mappings(cur, s2, {'both': '"id" / 0', 'stage2': '100 / "submodel"', 'valid': '"id" * 2'}) as (ids, cid):
            result = checkVersions(cur, plugin.config, [s1, s2], plugin_dir=plugin.plugin_dir, skip=skippedRules({'set_outputs': True}))
        assert not result['errors'], result['errors']
        mapping = defaultdict(list)
        for f in result['findings']:
            if f['rule'] == 'mapping_expressions':
                mapping[f['values']['mapping_id']].append(f)
        assert ids['valid'] not in mapping
        assert [f['versions'] for f in mapping[ids['both']]] == [[s1, s2]]
        [only] = mapping[ids['stage2']]
        assert only['versions'] == [s2] and only['severity'] == 'error' and only['values']['count'] == 1
        assert only['values']['examples'][0]['id'] == cid and only['values']['examples'][0]['error'].startswith('ZeroDivisionError')
        assert {'cost_pairs', 'economic_scenario', 'cost_outputs'}.isdisjoint(f['rule'] for f in result['findings'])
        assert {'cost_pairs', 'economic_scenario', 'cost_outputs'}.isdisjoint(result['rules_run'])
        assert 'mapping_expressions' in result['rules_run']
        errors, _ = inputDataMessages(result)
        assert any(line.startswith('{}: Mapping {} '.format(s2, ids['stage2'])) for line in errors)
        assert any(line.startswith('Mapping {} '.format(ids['both'])) for line in errors)

    def test_start_refused_by_the_input_data_of_stage_2(self, staged):
        """a mapping expression failing only for a customer of stage 2: the start is refused before any simulation, the
        log names stage 2"""
        from .conftest import wait_until
        plugin = staged.plugin
        s2 = staged.stage2
        with stage2_mappings(plugin.cur, s2, {'stage2': '100 / "submodel"'}) as (ids, _):
            plugin.showCostOptimization()
            dlg = plugin.dlg_costOptimization
            try:
                wait_until(lambda: dlg.periods.ready, 120, 'choosing the weeks')
                dlg.stage_table.addRow(s2, 10)
                dlg.start()
                log = dlg.log_edit.toPlainText()
                assert not dlg.process_running
            finally:
                dlg.close()
        assert 'The input data of the versions has errors, the run does not start:' in log, log
        assert any(line.startswith('{}: Mapping {} '.format(s2, ids['stage2'])) for line in log.splitlines()), log

    def test_start_refused_visibly(self, staged):
        """a refused start opens the log with the reason (it was written into the collapsed results before)"""
        from .conftest import wait_until
        plugin = staged.plugin
        # a stage-1 line moved in stage 2: the stage check refuses the start
        plugin.cur.execute('UPDATE "{b}".lines SET geom = ST_Translate(geom, 5, 0) WHERE id = (SELECT min(id) FROM "{a}".lines);'.format(  # nosec B608
            a=staged.stage1, b=staged.stage2))
        plugin.showCostOptimization()
        dlg = plugin.dlg_costOptimization
        wait_until(lambda: dlg.periods.ready, 120, 'choosing the weeks')
        dlg.stage_table.addRow(staged.stage2, 10)
        dlg.start()
        assert not dlg.process_running and not dlg.box_results.isCollapsed()
        assert dlg.results_tabs.currentWidget() is dlg.log_edit and dlg.log_edit.toPlainText().strip()
        dlg.close()

    def test_report_of_the_stages(self, staged):
        from districts.utility_functions.iteration_report import Report, stageSections
        rows = [{'iteration': k, 'npv': 1000.0 - k,
                 'stages': [{'version': staged.stage1, 'start': 0, 'npv': 400.0, 'split': {'investment': 300.0, 'pump_energy': 100.0}, 'climate': 'C:/clim/ZURICH.prn'},
                            {'version': staged.stage2, 'start': 10, 'npv': 600.0 - k, 'split': {'investment': 500.0, 'pump_energy': 100.0 - k},
                             'climate': 'C:/clim/ZURICH_2050.prn'}]} for k in (0, 1)]
        report = Report('t', 's')
        stageSections(report, rows, {'stages': [{'version': staged.stage1, 'start': 0}, {'version': staged.stage2, 'start': 10}]})
        page = report.html()
        assert 'Net present value per stage [€]' in page and staged.stage2 in page
        # operating years, climate file per stage, the parts per stage of the iteration with the least NPV
        assert '11–' in page and 'ZURICH_2050.prn' in page and 'Net present value per stage and part, iteration 1' in page

    def test_sensitivity_section_and_basis_refused(self, staged):
        """cost-sensitivity: the section lists the parameters of the scenario; the estimate refuses without a run and
        when a stage's pipes differ from the best iteration (D4)"""
        from districts.cost_optimization import lineState
        from districts.utility_functions.sensitivity import estimateBasis
        from .conftest import wait_until
        plugin = staged.plugin
        cur = plugin.cur
        s1, s2 = staged.stage1, staged.stage2
        plugin.showCostOptimization()
        dlg = plugin.dlg_costOptimization
        try:
            wait_until(lambda: dlg.periods.ready, 120, 'choosing the weeks')
            keys = [r['key'] for r in dlg.sensitivity.rows(all_rows=True)]
            assert {'interest_pct', 'period_a', 'price:electricity', 'factor:pipe', 'dp_spez_max', 'v_max'} <= set(keys)
            assert dlg.sensitivity.label_count.text() == 'No parameter marked to vary.'
        finally:
            dlg.close()
        with pytest.raises(ValueError, match='no cost optimization run'):
            estimateBasis(cur, [], {})
        states = {v: {str(lid): bid for lid, bid in lineState(cur, v).items()} for v in (s1, s2)}
        rows = [{'iteration': 0, 'npv': 10.0, 'stage_states': states}]
        parms = {'stage_versions': [s1, s2], 'stages': [{'version': s1, 'start': 0}, {'version': s2, 'start': 10}]}
        basis = estimateBasis(cur, rows, parms)
        assert basis['versions'] == [s1, s2] and basis['stages'][1] == {'version': s2, 'start': 10}
        lid, bid = next(iter(lineState(cur, s2).items()))
        cur.execute('SELECT id FROM public.pipe_bundle_types WHERE id <> %s ORDER BY id LIMIT 1;', (bid,))
        cur.execute('UPDATE "{}".lines SET pipe_bundle_type_id = %s WHERE id = %s;'.format(s2), (cur.fetchone()['id'], lid))  # nosec B608
        with pytest.raises(ValueError, match='differ from the best iteration'):
            estimateBasis(cur, rows, parms)


# ---------------------------------------------------------------- ida: a run over two stages
@pytest.fixture(scope='class')
def staged_run(request, districts_plugin, errors):
    from types import SimpleNamespace
    from .test_dynamic_optimization import skip_without_template
    from .test_workflow import delete_project, project_name_for
    skip_without_template(districts_plugin)
    state = SimpleNamespace(plugin=districts_plugin, project_name=project_name_for('stagerun'))
    yield state
    if not request.config.getoption('--keep-projects'):
        delete_project(districts_plugin, errors, state.project_name)


@pytest.mark.e2e
@pytest.mark.ida
@pytest.mark.incremental
class TestStagedRun:
    def test_project_and_stage_2(self, staged_run, errors):
        from districts.utility_functions.economic_data import examplePipeCosts
        from districts.utility_functions.hydraulic_balancing import createChildVersion
        from .test_dynamic_optimization import create_dynopt_project
        plugin = staged_run.plugin
        create_dynopt_project(plugin, errors, staged_run.project_name)
        plugin.cur.execute('SELECT id, innerpipediameter FROM public.pipes;')
        for row in plugin.cur.fetchall():
            plugin.cur.execute('UPDATE public.pipes SET costs = %s, maintenance_pct = 1, lifetime_a = 40, p_max_bar = 16 WHERE id = %s;',
                               (examplePipeCosts(round(float(row['innerpipediameter']) * 1000)), row['id']))
        staged_run.stage1 = plugin.config['versionName']
        staged_run.stage2 = staged_run.stage1 + '_s2'
        createChildVersion(plugin.cur, plugin.config, plugin.plugin_dir, staged_run.stage2, 'stage 2')

    def test_run_over_two_stages(self, staged_run, errors):
        from districts.cost_optimization import iterationPath
        from .conftest import wait, wait_until
        from .test_dynamic_optimization import TIMEOUT, bundles
        import json
        import os
        plugin = staged_run.plugin
        plugin.showCostOptimization()
        dlg = plugin.dlg_costOptimization
        periods = dlg.periods
        wait_until(lambda: periods.ready, 120, 'choosing the weeks')
        periods.spin_days.setValue(1)
        periods.spin_startup.setValue(1)
        periods.chooseWeeks()
        wait_until(lambda: periods.ready, 120, 'choosing the weeks')
        dlg.stage_table.addRow(staged_run.stage2, 10)
        dlg.spin_iter.setValue(1)
        dlg.edit_version.setText(staged_run.stage1 + '_co')
        dlg.btn_start.click()
        wait_until(lambda: not dlg.process_running, TIMEOUT, lambda: 'still running:\n' + dlg.log_edit.toPlainText()[-3000:])
        wait(500)
        log = dlg.log_edit.toPlainText()
        print('\n' + log)
        errors.check()
        assert dlg.progress.value() == 100, log
        assert 'stage 2 ({}_co)'.format(staged_run.stage2) in log
        assert plugin.config['versionName'] == staged_run.stage1 + '_co'
        with open(iterationPath(plugin.config, 0), encoding='utf-8') as f:
            row = json.load(f)
        assert [s['version'] for s in row['stages']] == [staged_run.stage1 + '_co', staged_run.stage2 + '_co']
        assert row['npv'] == pytest.approx(sum(s['npv'] for s in row['stages']))
        # both stages carry the pipes of the best iteration; the stage versions themselves are unchanged
        assert bundles(plugin, staged_run.stage1 + '_co') == bundles(plugin, staged_run.stage2 + '_co')
        assert os.path.exists(iterationPath(plugin.config, 1))
        # D11: the versions of the run in one chain, the version handling of the loaded stage on again, the ID check saved
        from districts.utility_functions.db import getParentVersion
        from districts.utility_functions.iteration_report import loadRunParameters
        from districts.utility_functions.network_stages import versionTriggers
        assert getParentVersion(plugin.cur, staged_run.stage2 + '_co') == staged_run.stage1 + '_co'
        from districts.ida_ph import get_item_by_text
        item = get_item_by_text(staged_run.stage2 + '_co', plugin)
        assert item is not None and item.parent() is not None and item.parent().text() == staged_run.stage1 + '_co'  # the tree shows the link
        assert versionTriggers(plugin.cur, staged_run.stage1 + '_co', True) == 0
        assert [link['after'] for link in loadRunParameters(plugin.config, 'cost')['stage_links']] == [staged_run.stage2 + '_co']

    def test_sensitivity_estimate(self, staged_run, errors):
        """cost-sensitivity D4: the interest varied ±50 % one at a time on the best iteration of the run over both stages:
        the base variant reproduces the best NPV, a higher interest gives a lower NPV, the scenario stays unchanged; the
        result file, the tab, the robustness layers per stage and the report section"""
        from qgis.core import QgsProject
        from qgis.PyQt.QtCore import Qt
        from districts.utility_functions.cost_optimization_layers import loadCostIterations
        from districts.utility_functions.economic_data import loadScenario
        from districts.utility_functions.iteration_report import writeReport
        from districts.utility_functions.sensitivity import loadAnalysis
        from .conftest import wait_until
        from .test_dynamic_optimization import TIMEOUT
        plugin = staged_run.plugin
        dlg = plugin.dlg_costOptimization
        scenario_id = dlg.combo_scenario.currentData()
        interest = loadScenario(plugin.cur, scenario_id)['scenario']['interest_pct']
        widget = dlg.sensitivity
        widget.fill()
        row = next(k for k in range(widget.table.rowCount()) if widget.table.item(k, 0).data(Qt.ItemDataRole.UserRole) == 'interest_pct')
        widget.table.item(row, 0).setCheckState(Qt.CheckState.Checked)
        widget.table.item(row, 5).setText('-50')
        widget.table.item(row, 6).setText('50')
        assert widget.label_count.text().startswith('3 variants')
        widget.startAnalysis()
        wait_until(lambda: not dlg.process_running, TIMEOUT, lambda: 'still running:\n' + dlg.log_edit.toPlainText()[-3000:])
        errors.check()
        analysis = loadAnalysis(plugin.config)
        log = dlg.log_edit.toPlainText()
        assert analysis and all(v.get('result') for v in analysis['variants']), log
        by_name = {v['name']: v['result'] for v in analysis['variants']}
        best = min(loadCostIterations(plugin.config), key=lambda r: r['npv'])
        assert by_name['base']['npv'] == pytest.approx(best['npv'], rel=1e-6)
        assert by_name['interest_pct +']['npv'] < by_name['base']['npv'] < by_name['interest_pct -']['npv']
        assert loadScenario(plugin.cur, scenario_id)['scenario']['interest_pct'] == interest
        results = dlg.sensitivity_results
        assert results.table_variants.rowCount() == 3
        # selecting a variant in the table selects it in the plot; a filter greys the variants outside
        results.table_variants.selectRow(2)
        assert results.state['selected'] == results.table_variants.item(2, 0).text()
        results.state['brushes'][0] = (0.9, 1.0)
        results.filtered()
        assert results.label_filter.text() == '1 of 3 variants in the filter'
        results.resetFilter()
        assert results.label_filter.text() == ''
        dlg.sensitivity_results.showMap()
        group = QgsProject.instance().layerTreeRoot().findGroup('Sensitivity – robustness')
        assert group is not None and [child.name() for child in group.children()] == analysis['basis']['versions']
        with open(writeReport(plugin.cur, plugin.config, 'cost'), encoding='utf-8') as f:
            page = f.read()
        assert 'Sensitivity analysis' in page and 'Tornado chart' in page

    @pytest.mark.skipif(not os.environ.get('DISTRICTS_TEST_SENSITIVITY_FULL'), reason='three cost optimizations (about 20 min): DISTRICTS_TEST_SENSITIVITY_FULL=1')
    def test_sensitivity_full_optimization(self, staged_run, errors, monkeypatch):
        """cost-sensitivity D5: the interest varied one at a time with a cost optimization per variant (one iteration
        each, the loaded version alone): a child version per variant, the base version loaded again at the end, the
        scenario unchanged"""
        from qgis.PyQt.QtCore import Qt
        from qgis.PyQt.QtWidgets import QMessageBox
        from districts.utility_functions.economic_data import loadScenario
        from districts.utility_functions.sensitivity import loadAnalysis
        from .conftest import wait, wait_until
        from .test_dynamic_optimization import TIMEOUT
        plugin = staged_run.plugin
        base = plugin.config['versionName']
        monkeypatch.setattr(QMessageBox, 'question', lambda *args, **kwargs: QMessageBox.StandardButton.Yes)
        plugin.dlg_costOptimization.close()
        plugin.showCostOptimization()
        dlg = plugin.dlg_costOptimization
        periods = dlg.periods
        wait_until(lambda: periods.ready, 120, 'choosing the weeks')
        periods.spin_days.setValue(1)
        periods.spin_startup.setValue(1)
        periods.chooseWeeks()
        wait_until(lambda: periods.ready, 120, 'choosing the weeks')
        dlg.spin_iter.setValue(1)
        scenario_id = dlg.combo_scenario.currentData()
        interest = loadScenario(plugin.cur, scenario_id)['scenario']['interest_pct']
        widget = dlg.sensitivity
        widget.fill()
        widget.combo_mode.setCurrentIndex(widget.combo_mode.findData('full'))
        row = next(k for k in range(widget.table.rowCount()) if widget.table.item(k, 0).data(Qt.ItemDataRole.UserRole) == 'interest_pct')
        widget.table.item(row, 0).setCheckState(Qt.CheckState.Checked)
        widget.startAnalysis()
        wait_until(lambda: widget.run is not None and not widget.run.active and not dlg.process_running, 3 * TIMEOUT,
                   lambda: 'still running:\n' + dlg.log_edit.toPlainText()[-3000:])
        wait(500)
        errors.check()
        log = dlg.log_edit.toPlainText()
        print('\n' + log)
        assert plugin.config['versionName'] == base, log
        analysis = loadAnalysis(plugin.config)
        assert [v['version'] for v in analysis['variants']] == ['{}_s{}'.format(base, k) for k in range(3)]
        assert all(v.get('result') for v in analysis['variants']), log
        plugin.cur.execute('SELECT count(*) AS n FROM public.versionhandling WHERE name = ANY(%s);', ([v['version'] for v in analysis['variants']],))
        assert plugin.cur.fetchone()['n'] == 3
        by_name = {v['name']: v['result'] for v in analysis['variants']}
        assert by_name['interest_pct +']['npv'] < by_name['interest_pct -']['npv']
        assert loadScenario(plugin.cur, scenario_id)['scenario']['interest_pct'] == interest
        dlg.close()


def test_add_stage_button():
    """'Add a stage' twice: the rows follow the loaded version, each 10 years after the previous one"""
    from districts.utility_functions.stage_table import StageTable
    table = StageTable(['base1', 'base1_s2', 'base1_s3'], 'base1', 'info')
    table.btn_add.click()
    table.btn_add.click()
    assert [s['start'] for s in table.stages()] == [0, 10, 20]
    assert table.stages()[0]['version'] == 'base1'
    table.table.selectRow(2)
    table.removeRows()
    assert len(table.stages()) == 2
