# coding=utf-8
"""Rules of the model checks (OpenSpec change ai-mcp-connection, spec model-checks) on synthetic series, without a
database: thresholds and their sources, load hours, missing outputs, findings. The rules on a real version are in
test_mcp_e2e.py.

    python -m pytest test/test_model_checks.py -v
"""
import datetime

import pytest

from districts.utility_functions import model_checks as mc

T0 = datetime.datetime(2026, 1, 1)


def hours(n):
    return [T0 + datetime.timedelta(hours=h) for h in range(n)]


class FakeContext(mc.CheckContext):
    def __init__(self, conn=None, power=None, plants=None, thresholds=None):
        super().__init__(None, {'versionName': 'v'}, thresholds)
        self.conn = conn or {}
        self.power = power or {}
        self.plants = plants or {}

    def connSeries(self, feature, var):
        return self.conn.get(var, {})

    def powerSeries(self, feature):
        return self.power if feature == 'customer' else self.plants


def series(values):
    return dict(zip(hours(len(values)), values))


def test_low_delta_t_at_load_hours():
    temps = {'temp': {1: (series([70] * 10), series([61] * 10)), 2: (series([70] * 10), series([45] * 10))}}
    ctx = FakeContext(temps, power={1: series([50e3] * 10), 2: series([50e3] * 10)})
    found = mc.ruleDeltaT(ctx)
    assert [f['feature_id'] for f in found] == [1]
    f = found[0]
    assert f['rule'] == 'delta_t_low' and f['severity'] == 'warning'
    assert f['values']['value'] == pytest.approx(9.0) and f['values']['threshold'] == 15.0 and f['values']['source'] == 'default'
    assert f['values']['unit'] == 'K' and f['values']['mode'] == 'heating'


def test_standstill_hours_are_ignored():
    # 2 K only in the steps below 10 % of the peak heat flow
    sup = series([70] * 10)
    ret = series([50] * 8 + [68, 68])
    power = series([50e3] * 8 + [1e3, 1e3])
    assert mc.ruleDeltaT(FakeContext({'temp': {1: (sup, ret)}}, power={1: power})) == []


def test_cooling_uses_its_own_limit():
    sup, ret = series([10] * 4), series([12] * 4)  # 2 K cooling < 4 K
    found = mc.ruleDeltaT(FakeContext({'temp': {3: (sup, ret)}}, power={3: series([-20e3] * 4)}))
    assert found[0]['values']['mode'] == 'cooling' and found[0]['values']['threshold'] == 4.0


def test_threshold_given_as_argument():
    sup, ret = series([70] * 4), series([58] * 4)  # 12 K
    ctx = FakeContext({'temp': {1: (sup, ret)}}, power={1: series([1e3] * 4)}, thresholds={'delta_t_heating_k': 10})
    assert mc.ruleDeltaT(ctx) == []
    assert ctx.limit('delta_t_heating_k') == (10.0, 'argument')
    assert ctx.limit('v_max_m_s') == (3.0, 'default')


def test_substation_dp_below_minimum():
    p = {'p': {5: (series([3.4e5] * 3), series([3.0e5] * 3)), 6: (series([4e5] * 3), series([3e5] * 3))}}
    found = mc.ruleSubstationDp(FakeContext(p, power={5: series([1e4] * 3), 6: series([1e4] * 3)}))
    assert [f['feature_id'] for f in found] == [5]
    assert found[0]['values']['value'] == pytest.approx(0.4) and found[0]['values']['threshold'] == 0.5
    assert found[0]['values']['unit'] == 'bar'


def test_missing_outputs_are_named():
    found = mc.ruleSubstationDp(FakeContext({}, power={}))
    assert found[0]['rule'] == 'outputs_missing' and found[0]['severity'] == 'info'
    assert found[0]['values']['outputs'] == ['p_c', 'power_c'] and found[0]['values']['rule_checked'] == 'substation_dp_low'


def test_supply_temperature_without_project_value_is_info():
    found = mc.ruleSupplyTemp(FakeContext())
    assert len(found) == 1 and found[0]['severity'] == 'info' and found[0]['rule'] == 'supply_temp_low'


def test_plant_that_never_runs():
    plants = {1: series([500e3, 400e3]), 2: series([0.0, 100.0])}
    found = mc.rulePlants(FakeContext(plants=plants))
    assert [f['feature_id'] for f in found] == [2] and found[0]['rule'] == 'plant_never_runs'


def test_line_velocity_and_pressure_loss(monkeypatch):
    pipes = {(1, 1): {'name': 'DN50', 'd': 0.0545, 'k': 0.0001, 'p_max_bar': 16}, (2, 1): {'name': 'DN200', 'd': 0.2101, 'k': 0.0001, 'p_max_bar': 16}}
    mdot = {(1, 1): 8.0, (2, 1): 8.0}
    monkeypatch.setattr(mc, 'linePipeRows', lambda ctx: pipes)
    monkeypatch.setattr(mc, 'lineSeries', lambda ctx, var, aggregate='max': mdot if var == 'mdot' else {})
    found = mc.ruleLineHydraulics(FakeContext())
    assert {(f['rule'], f['feature_id']) for f in found} == {('line_velocity_high', 1), ('line_dp_spec_high', 1)}
    v = next(f for f in found if f['rule'] == 'line_velocity_high')
    assert v['values']['value'] > 3.0 and v['values']['source'] == 'default'
    # with v_max 2 m/s from the caller
    found = mc.ruleLineHydraulics(FakeContext(thresholds={'v_max_m_s': 0.2}))
    assert ('line_velocity_high', 2) in {(f['rule'], f['feature_id']) for f in found}


def test_pipe_pressure_above_rating(monkeypatch):
    monkeypatch.setattr(mc, 'linePipeRows', lambda ctx: {(4, 1): {'name': 'DN80', 'd': 0.08, 'k': 0.0001, 'p_max_bar': 16}})
    monkeypatch.setattr(mc, 'lineSeries', lambda ctx, var, aggregate='max': {(4, 1): 17e5})
    found = mc.rulePipePressure(FakeContext())
    assert found[0]['rule'] == 'pipe_pressure_limit' and found[0]['severity'] == 'error'
    assert found[0]['values']['value'] == pytest.approx(17.0) and found[0]['values']['threshold'] == 16.0
    assert found[0]['values']['source'] == 'project'


def test_rule_ids_and_scopes():
    assert {'topology', 'unconnected_features', 'heights', 'pipe_data_missing', 'delta_t_low', 'substation_dp_low', 'supply_temp_low',
            'pipe_pressure_limit', 'line_velocity_high', 'line_dp_spec_high', 'plant_never_runs', 'plant_power_high', 'outputs_missing',
            'run_errors', 'comfort_deficit', 'energy_use_detection', 'pump_detection'} <= set(mc.RULE_IDS)
    assert {scope for _, scope, _, _ in mc.RULES} == set(mc.SCOPES)
    with pytest.raises(ValueError):
        mc.runChecks(None, {'versionName': 'v'}, scope='everything')


def test_pump_and_energy_lists(tmp_path):
    ctx = FakeContext()
    ctx.config = {'versionName': 'v', 'pathProjects': str(tmp_path) + '\\', 'projectName': 'p'}
    (tmp_path / 'p').mkdir()
    found = {f['rule']: f['severity'] for f in mc.ruleLists(ctx)}
    assert found == {'pump_list': 'warning', 'energy_use_list': 'info'}
    (tmp_path / 'p' / 'networkPumps.json').write_text('{"entries": [{"component": "PUMP2"}]}', encoding='utf-8')
    assert {f['rule'] for f in mc.ruleLists(ctx)} == {'energy_use_list'}


def test_cost_outputs_need_the_plugin_folder():
    assert mc.ruleCostOutputs(FakeContext()) == []


def mapping_finding(mapping_id, count):
    return mc.finding('mapping_expressions', 'error', 'Mapping {}: fails for {} features'.format(mapping_id, count), 'customers',
                      values={'mapping_id': mapping_id, 'count': count})


def fake_run_checks(per_version):
    def run(cur, config, scope='all', thresholds=None, plugin_dir=None):
        version = config['versionName']
        found, rules, errors = per_version[version]
        return {'version': version, 'scope': scope, 'findings': [dict(f) for f in found], 'rules_run': rules,
                'rules_skipped': {}, 'errors': errors}
    return run


def test_checks_over_the_stage_versions(monkeypatch):
    """a finding equal in every stage once with all versions, one of a single stage with its version; skipped rules
    neither as finding nor as run; rule errors per version"""
    pumps = mc.finding('pump_list', 'warning', 'No network pump list')
    pairs = mc.finding('cost_pairs', 'error', 'Network 1: no pair')
    monkeypatch.setattr(mc, 'runChecks', fake_run_checks({
        's1': ([mapping_finding(7, 2), pumps, pairs], ['mapping_expressions', 'pump_list', 'cost_pairs'], {}),
        's2': ([mapping_finding(7, 2), mapping_finding(8, 1), pumps], ['mapping_expressions', 'pump_list', 'cost_pairs'],
               {'climate_file': 'OSError: no such file', 'cost_pairs': 'KeyError: 1'}),
    }))
    result = mc.checkVersions(None, {'versionName': 's1'}, ['s1', 's2'], skip={'cost_pairs'})
    assert [(f['rule'], f['values'].get('mapping_id'), f['versions']) for f in result['findings']] == [
        ('mapping_expressions', 7, ['s1', 's2']), ('mapping_expressions', 8, ['s2']), ('pump_list', None, ['s1', 's2'])]
    assert result['rules_run'] == ['mapping_expressions', 'pump_list']
    assert result['errors'] == {'s2': {'climate_file': 'OSError: no such file'}}
    lines = [mc.findingLine(f, result['versions']) for f in result['findings']]
    assert lines == ['Mapping 7: fails for 2 features', 's2: Mapping 8: fails for 1 features', 'No network pump list']


def test_the_same_mapping_with_other_values_per_stage(monkeypatch):
    """stage 2 has more customers: the counts differ, so each stage keeps its own finding"""
    monkeypatch.setattr(mc, 'runChecks', fake_run_checks({'s1': ([mapping_finding(7, 2)], [], {}), 's2': ([mapping_finding(7, 5)], [], {})}))
    result = mc.checkVersions(None, {'versionName': 's1'}, ['s1', 's2'])
    assert [(f['values']['count'], f['versions']) for f in result['findings']] == [(2, ['s1']), (5, ['s2'])]


def test_one_version_has_no_prefix(monkeypatch):
    monkeypatch.setattr(mc, 'runChecks', fake_run_checks({'s1': ([mapping_finding(7, 2)], [], {})}))
    result = mc.checkVersions(None, {'versionName': 's1'}, ['s1'])
    assert mc.findingLine(result['findings'][0], result['versions']) == 'Mapping 7: fails for 2 features'


def test_start_of_the_cost_optimization_on_the_input_data():
    """errors refuse the start, warnings and infos are logged; pairs and scenario are checked by the dialog, the outputs
    only when the run does not switch them on"""
    from districts.cost_optimization import inputDataMessages, skippedRules
    assert skippedRules({'set_outputs': True}) == {'cost_pairs', 'economic_scenario', 'cost_outputs'}
    assert 'cost_outputs' not in skippedRules({'set_outputs': False})
    found = [dict(mapping_finding(8, 1), versions=['s2']), dict(mc.finding('pump_list', 'warning', 'No pump list'), versions=['s1', 's2']),
             dict(mc.finding('pipe_costs_missing', 'info', 'Example costs'), versions=['s1', 's2'])]
    errors, notes = inputDataMessages({'versions': ['s1', 's2'], 'findings': found, 'errors': {'s2': {'climate_file': 'OSError: x'}}})
    assert errors == ['s2: Mapping 8: fails for 1 features']
    assert notes == ['No pump list', 'Check climate_file of version s2 failed: OSError: x', 'Example costs']


def test_load_steps():
    steps = mc.loadSteps({1: series([100.0, 5.0, 50.0]), 2: series([0.0, 0.0])})
    assert steps[1] == {T0, T0 + datetime.timedelta(hours=2)} and steps[2] == set()
