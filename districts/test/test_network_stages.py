# coding=utf-8
"""Network built in stages (OpenSpec change network-stages): NPV by stage years."""
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
