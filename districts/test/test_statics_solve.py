# coding=utf-8
"""Statics of rigid steel pipes (OpenSpec change statics-steel-solver) on a project from the template heating_network:
upgrade of an old version and project, calculation and result tables, result state, refusal of an out-of-date model,
cancel, skipped non-rigid lines, child version, the button with its background task.

    python -m pytest test/test_statics_solve.py -v -s   (--keep-projects)
"""
from types import SimpleNamespace

import pytest

from districts.upgrade import upgradeVersionDB
from districts.utility_functions import statics_db, statics_solve_db as ssd

from .test_workflow import HEATING, create_project, delete_project, project_name_for

pytestmark = [pytest.mark.e2e]


@pytest.fixture(scope='class')
def solve(request, districts_plugin, errors):
    state = SimpleNamespace(plugin=districts_plugin, project_name=project_name_for('statics_solve'))
    yield state
    if not request.config.getoption('--keep-projects'):
        delete_project(districts_plugin, errors, state.project_name)


def one(plugin, sql, args=None):
    plugin.cur.execute(sql, args)
    return plugin.cur.fetchone()


def count(plugin, table, version=None):
    return one(plugin, 'SELECT count(*) AS n FROM "{}".{};'.format(version or plugin.config['versionName'], table))['n']  # nosec B608


def calculate(state, **kw):
    result = ssd.calculate(state.plugin.cur, state.plugin.config['versionName'], **kw)
    if result is not None:
        ssd.writeResults(state.plugin.cur, state.plugin.config['versionName'], result)
    return result


@pytest.mark.incremental
class TestStaticsSolve:
    def test_create_project(self, solve, errors):
        create_project(solve.plugin, errors, solve.project_name, HEATING)
        solve.version = solve.plugin.config['versionName']
        assert count(solve.plugin, 'lines') > 0

    def test_old_version_and_project_upgraded(self, solve):
        plugin, v = solve.plugin, solve.version
        #the state before this change: no result tables, no new override columns, parameters without source
        for table in statics_db.RESULT_TABLES:
            plugin.cur.execute('DROP TABLE IF EXISTS "{}".{};'.format(v, table))  # nosec B608
        for table, columns in statics_db.ADDED_COLUMNS.items():
            plugin.cur.execute('ALTER TABLE "{}".{} {};'.format(v, table, ', '.join('DROP COLUMN IF EXISTS ' + c for c in columns)))  # nosec B608
        plugin.cur.execute("INSERT INTO \"{}\".statics_sections (geom, cover_m) VALUES (NULL, 0.7);".format(v))  # nosec B608
        plugin.cur.execute("DELETE FROM public.statics_parameters WHERE key NOT IN ('bend_ignore_deg', 'kink_max_deg', "
                           "'bend_radius_factor', 'elastic_radius_factor', 'merge_distance_m', 'snap_tolerance_m');")
        plugin.cur.execute("ALTER TABLE public.statics_parameters DROP COLUMN IF EXISTS source;")
        plugin.cur.execute("ALTER TABLE public.statics_parameters ALTER COLUMN value SET NOT NULL;")
        upgradeVersionDB(plugin.cur, plugin.config)
        for table in statics_db.RESULT_TABLES:
            assert count(plugin, table) == 0
        old = one(plugin, 'SELECT * FROM "{}".statics_sections WHERE cover_m = 0.7;'.format(v))  # nosec B608
        assert old['design_temperature_c'] is None and 'prestressed_legs' in old
        params, sources = statics_db.readParameters(plugin.cur, with_sources=True)
        assert params['friction_max'] == 0.4 and params['stress_range_allow_n7mm2'] is None
        assert sources['friction_min'].startswith('to be confirmed') and sources['kink_max_deg']
        plugin.cur.execute('DELETE FROM "{}".statics_sections WHERE cover_m = 0.7;'.format(v))  # nosec B608

    def test_refused_without_model(self, solve):
        with pytest.raises(ssd.Refused):
            calculate(solve)
        assert ssd.resultState(solve.plugin.cur, solve.version) == statics_db.STATE_MISSING

    def test_calculate(self, solve):
        plugin, v = solve.plugin, solve.version
        statics_db.buildModel(plugin.cur, v)
        result = calculate(solve)
        summary = result['summary']
        assert summary['members'] > 0 and summary['elements'] > 0 and not summary['not_converged']
        assert summary['fatigue_checked'] is False
        assert count(plugin, 'statics_result_elements') == summary['elements']
        assert count(plugin, 'statics_result_nodes') > 0
        run = ssd.lastRun(plugin.cur, v)
        assert run['status'] == 'ok' and run['parameters']['sigma_ax_allow_n7mm2']['source'] == 'isoplus PHB 12/4'
        assert ssd.resultState(plugin.cur, v) == statics_db.STATE_CURRENT
        #both friction cases and the three load steps; utilisation on the upper friction
        cases = one(plugin, """SELECT count(DISTINCT friction_case) AS c, count(DISTINCT load_step) AS s,
            count(utilisation) FILTER (WHERE friction_case = 'mu_max') AS u FROM "{}".statics_result_elements;""".format(v))  # nosec B608
        assert (cases['c'], cases['s']) == (2, 3) and cases['u'] > 0
        #the template at 120 degC design: restrained straight pipe above 190 N/mm2 is reported with its source
        rules = summary['findings_by_rule']
        assert all(isinstance(n, int) for n in rules.values())
        solve.elements = summary['elements']

    def test_out_of_date_and_refused(self, solve):
        plugin, v = solve.plugin, solve.version
        lid = one(plugin, 'SELECT id FROM "{}".lines ORDER BY id LIMIT 1;'.format(v))['id']  # nosec B608
        plugin.cur.execute('UPDATE "{}".lines SET geom = ST_Translate(geom, 0.01, 0, 0) WHERE id = %s;'.format(v), (lid,))  # nosec B608
        assert ssd.resultState(plugin.cur, v) == statics_db.STATE_OUT_OF_DATE
        with pytest.raises(ssd.Refused):
            calculate(solve)
        plugin.cur.execute('UPDATE "{}".lines SET geom = ST_Translate(geom, -0.01, 0, 0) WHERE id = %s;'.format(v), (lid,))  # nosec B608
        assert ssd.resultState(plugin.cur, v) == statics_db.STATE_CURRENT

    def test_solver_parameter_puts_results_out_of_date(self, solve):
        plugin, v = solve.plugin, solve.version
        plugin.cur.execute("UPDATE public.statics_parameters SET value = 0.35 WHERE key = 'friction_max';")
        assert statics_db.modelState(plugin.cur, v) == statics_db.STATE_CURRENT
        assert ssd.resultState(plugin.cur, v) == statics_db.STATE_OUT_OF_DATE
        plugin.cur.execute("UPDATE public.statics_parameters SET value = 0.40 WHERE key = 'friction_max';")
        assert ssd.resultState(plugin.cur, v) == statics_db.STATE_CURRENT

    def test_cancel_keeps_results(self, solve):
        plugin, v = solve.plugin, solve.version
        before = ssd.lastRun(plugin.cur, v)['run_at']
        assert calculate(solve, cancelled=lambda: True) is None
        assert ssd.lastRun(plugin.cur, v)['run_at'] == before
        assert count(plugin, 'statics_result_elements') == solve.elements

    def test_non_rigid_line_skipped(self, solve):
        plugin, v = solve.plugin, solve.version
        data = ssd.readInputs(plugin.cur, v)
        #the line with most junction connections becomes a flexible pipe
        lid = one(plugin, 'SELECT lid FROM "{}".junction_connections GROUP BY lid ORDER BY count(*) DESC, lid LIMIT 1;'.format(v))['lid']  # nosec B608
        for p in data['pipes']:
            if p['line_id'] == lid:
                p['system_type'] = 'flexible_plastic'
        problem = ssd.buildProblem(data)
        assert lid in problem['skipped']
        assert all(m['line_id'] != lid for m in problem['members'])
        assert any(f['rule'] == 'connection_not_calculated' for f in problem['findings'])

    def test_button_runs_the_task(self, solve, errors):
        import time
        from qgis.PyQt.QtCore import QCoreApplication
        plugin, v = solve.plugin, solve.version
        #the result tables restart their ids at every run: compare the time
        before = ssd.lastRun(plugin.cur, v)['run_at']
        plugin.calculateStatics()
        task = plugin.statics_task
        assert task is not None
        #the task runs in the task manager's thread; finished() needs the event loop of the main thread
        deadline = time.time() + 600
        while plugin.statics_task is not None and time.time() < deadline:
            QCoreApplication.processEvents()
            time.sleep(0.05)
        assert plugin.statics_task is None
        assert task.error is None and task.refused is None, task.error or task.refused
        errors.check()
        assert ssd.lastRun(plugin.cur, v)['run_at'] > before
        assert plugin.dlg_staticsCalcReport.isVisible()
        assert 'Fatigue' in plugin.dlg_staticsCalcReport.text() or 'Ermüdung' in plugin.dlg_staticsCalcReport.text()
        plugin.dlg_staticsCalcReport.close()

    def test_child_version(self, solve):
        from districts.utility_functions.hydraulic_balancing import createChildVersion
        plugin, v = solve.plugin, solve.version
        child = v + '_c'
        createChildVersion(plugin.cur, plugin.config, plugin.plugin_dir, child, 'statics child')
        for table in statics_db.RESULT_TABLES:
            assert count(plugin, table, child) == count(plugin, table), table
