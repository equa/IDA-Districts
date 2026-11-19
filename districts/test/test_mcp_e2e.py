# coding=utf-8
"""AI connection on a real version (OpenSpec change ai-mcp-connection): the rules on a project from the template
db_default_values, every tool leaves the version unchanged, the workflow state, the key figures equal to the report's
economics and the height check unchanged by the split.

    python -m pytest test/test_mcp_e2e.py -v -s   (--keep-projects)
"""
from types import SimpleNamespace

import pytest

from districts.ida_ph import addBaseVersion
from districts.ida_ph_dialog import IDA_Districts_NameDialog
from districts.mcp import tools as mcp_tools
from districts.mcp.guidance import workflowState
from districts.utility_functions.files import loadProjectConfig
from districts.utility_functions.height_check import HEIGHT_CHECK_LAYERS, heightConsistency, heightConsistencyRows, removeHeightCheckLayers
from districts.utility_functions.model_checks import runChecks
from districts.utility_functions.network_economics import evaluateVersion
from districts.utility_functions.translations import tr
from districts.utility_functions.version_kpis import compareVersions, versionKpis

from .conftest import wait
from .test_network_cost_data import SETTINGS, base_id, synthetic_results
from .test_workflow import DB_DEFAULTS, create_project, delete_project, project_name_for

pytestmark = [pytest.mark.e2e]


@pytest.fixture(scope='class')
def ai(request, districts_plugin, errors):
    state = SimpleNamespace(plugin=districts_plugin, project_name=project_name_for('ai'))
    yield state
    if not request.config.getoption('--keep-projects'):
        delete_project(districts_plugin, errors, state.project_name)


def version_rows(plugin):
    """{table: row count} of every table of the loaded version and of public"""
    cur = plugin.cur
    cur.execute("SELECT table_schema, table_name FROM information_schema.tables WHERE table_schema IN (%s, 'public') "
                "AND table_type = 'BASE TABLE' ORDER BY 1, 2;", (plugin.config['versionName'],))
    counts = {}
    for row in cur.fetchall():
        cur.execute('SELECT count(*) AS n FROM "{}"."{}";'.format(row['table_schema'], row['table_name']))  # nosec B608
        counts['{}.{}'.format(row['table_schema'], row['table_name'])] = cur.fetchone()['n']
    return counts


def step(state, name):
    return next(s for s in state['steps'] if s['step'] == name)


@pytest.mark.incremental
class TestAiConnection:
    def test_create_project(self, ai, errors):
        plugin = ai.plugin
        create_project(plugin, errors, ai.project_name, DB_DEFAULTS)
        plugin.dlg_addBase = IDA_Districts_NameDialog(tr('@default', 'add_base_version'), tr('@default', 'add_base_version'), '', '')
        plugin.dlg_addBase.input.setText('base1')
        addBaseVersion(plugin.dlg_addBase, plugin)
        wait(500)
        errors.check()
        assert plugin.config['versionName'] == 'base1'

    def test_workflow_state_of_a_new_version(self, ai):
        plugin = ai.plugin
        state = workflowState(plugin.cur, plugin.config)
        assert not [s['step'] for s in state['steps'] if s['state'] == 'unknown'], state
        assert step(state, 'version')['state'] == 'done'
        assert step(state, 'pipe_laying')['state'] == 'missing'
        assert step(state, 'cost_optimization')['wiki'] == 'missing' and 'no page' in step(state, 'cost_optimization')['note']
        assert state['next_step'] in ('import', 'location_climate', 'features')

    def test_rules_on_the_qgis_model(self, ai):
        plugin = ai.plugin
        v = plugin.config['versionName']
        srid = loadProjectConfig(plugin.config)['srid']
        # line 1 with a pipe bundle, line 2 with a bundle without pipes, a customer far from the lines, a customer without height
        plugin.cur.execute("""DELETE FROM "{v}".lines; DELETE FROM "{v}".customers;
            INSERT INTO "{v}".lines (id, geom, pipe_bundle_type_id) VALUES
                (1, ST_SetSRID(ST_MakeLine(ST_MakePoint(0, 0, 400), ST_MakePoint(100, 0, 400)), {s}), 1),
                (2, ST_SetSRID(ST_MakeLine(ST_MakePoint(100, 0, 400), ST_MakePoint(200, 0, 400)), {s}), 999999);
            INSERT INTO "{v}".customers (id, geom) VALUES (1, ST_SetSRID(ST_MakePoint(500, 500, 400), {s})),
                (2, ST_SetSRID(ST_MakePoint(600, 500, 0), {s}));""".format(v=v, s=srid))  # nosec B608
        result = runChecks(plugin.cur, plugin.config, 'qgis')
        rules = {(f['rule'], f['feature_id']) for f in result['findings']}
        assert ('pipe_data_missing', 2) in rules and ('pipe_data_missing', 1) not in rules
        unconnected = [f for f in result['findings'] if f['rule'] == 'unconnected_features']
        assert unconnected and 1 in unconnected[0]['values']['ids']
        assert any(f['rule'] == 'heights' and f['values']['issue'] == 'z_missing' for f in result['findings'])
        assert not result['errors']

    def test_results_rules_without_results(self, ai):
        plugin = ai.plugin
        result = runChecks(plugin.cur, plugin.config, 'results')
        assert result['rules_skipped'].get('delta_t_low') == 'no results'
        assert result['rules_skipped']['plant_power_high'].startswith('no nominal power')

    def test_height_check_unchanged_by_the_split(self, ai):
        plugin = ai.plugin
        v = plugin.config['versionName']
        point_rows, line_rows = heightConsistencyRows(plugin.cur, v, HEIGHT_CHECK_LAYERS)
        expected = {}
        for r in point_rows + line_rows:
            expected[r['issue']] = expected.get(r['issue'], 0) + 1
        try:
            assert heightConsistency(plugin.cur, v, HEIGHT_CHECK_LAYERS) == expected
        finally:
            removeHeightCheckLayers()

    def test_tools_leave_the_version_unchanged(self, ai):
        plugin = ai.plugin
        ctx = mcp_tools.ToolContext(plugin)
        before = version_rows(plugin)
        calls = {'project_state': {}, 'layers': {}, 'result_tables': {}, 'run_log': {}, 'run_checks': {},
                 'workflow_state': {}, 'version_kpis': {}, 'compare_versions': {'a': 'base1', 'b': 'base1'}}
        for name, args in calls.items():
            result = mcp_tools.callTool(ctx, name, args)
            assert result is not None, name
        assert version_rows(plugin) == before
        state = mcp_tools.callTool(ctx, 'project_state', {})
        assert state['loaded_version'] == 'base1' and state['feature_counts']['lines'] == 2
        assert {v['name'] for v in state['versions']} >= {'base1'}

    def test_tool_errors(self, ai):
        ctx = mcp_tools.ToolContext(ai.plugin)
        with pytest.raises(mcp_tools.ToolError, match='does not exist'):
            mcp_tools.callTool(ctx, 'run_checks', {'version': 'no_such_version'})
        with pytest.raises(mcp_tools.ToolError, match='no table'):
            mcp_tools.callTool(ctx, 'result_series', {'table': 'nothing'})
        with pytest.raises(mcp_tools.ToolError, match='unknown thresholds'):
            mcp_tools.callTool(ctx, 'run_checks', {'thresholds': {'speed': 1}})

    def test_kpis_without_results(self, ai):
        plugin = ai.plugin
        kpis = versionKpis(plugin.cur, plugin.config, base_id(plugin), SETTINGS)
        assert kpis['results_basis']['basis'] == 'none'
        assert kpis['network_length']['value'] == pytest.approx(200.0)
        assert kpis['peak_load']['value'] is None and kpis['peak_load']['reason']
        assert kpis['comfort_deficits']['value'] is None and 'troom_c' in kpis['comfort_deficits']['reason']
        assert kpis['economics']['reason'].startswith('results needed')

    def test_kpis_equal_the_evaluation_of_the_report(self, ai):
        plugin = ai.plugin
        synthetic_results(plugin, 8760)
        evaluation = evaluateVersion(plugin.cur, plugin.config, base_id(plugin), SETTINGS)
        kpis = versionKpis(plugin.cur, plugin.config, base_id(plugin), SETTINGS)
        assert kpis['results_basis']['basis'] == 'full_year'
        assert kpis['economics']['npv']['value'] == pytest.approx(round(evaluation['npv']['npv'], 0))
        assert kpis['economics']['heat_losses']['value'] == pytest.approx(round(evaluation['energy']['heat_kwh'], 0))
        assert kpis['economics']['pump_energy']['value'] == pytest.approx(round(evaluation['energy']['pump_kwh'], 0))
        comparison = compareVersions(kpis, dict(kpis, results_basis={'basis': 'periods', 'days': 28}))
        assert 'note' in comparison and comparison['differences']['economics.npv']['diff'] == 0

    def test_results_step_and_outputs_missing(self, ai):
        plugin = ai.plugin
        state = workflowState(plugin.cur, plugin.config)
        assert step(state, 'results')['state'] in ('done', 'stale')
        result = runChecks(plugin.cur, plugin.config, 'results')
        missing = {f['values'].get('rule_checked') for f in result['findings'] if f['rule'] == 'outputs_missing'}
        assert {'delta_t_low', 'substation_dp_low', 'pipe_pressure_limit'} <= missing
        assert not result['errors']
