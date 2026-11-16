# coding=utf-8
"""Network pumps and pump power outputs (OpenSpec change pump-power-outputs): detection in the templates, the pump
list of the project, the outputs written into the templates, the estimate and the reading of the output files.
No database; the IDA Districts samples are used if installed (DISTRICTS_TEST_PATH_DISTRICTS)."""
import os
import shutil

import numpy as np
import pytest

from districts.ida_mosim import checkSimOutputs
from districts.outputs import pumpPowerComp, setpointOutputsComp, withEstimateConnectionOutputs
from districts.utility_functions.files import readFileToString, withDefaultOutputs
from districts.utility_functions.ida_components import getCompName, getIDAListComponents, propertyListCompsIDM
from districts.utility_functions.network_pumps import (
    DEFAULT_DP_INT, DEFAULT_ETA, ensurePumpList, estimateFromConnections, estimatePumpPower, estimateSeries,
    loadPumpList, markMissing, mergeDetection, newEntry, prnColumns, pumpFilePath, removeEntry, savePumpList,
    templateEntries, variableSeries, detectProject,
)
from districts.utility_functions.template_graph import detectPumps, isFluidPort, portSide

PLUGIN_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DEFAULTS = os.path.join(PLUGIN_DIR, 'templates', 'db_default_values')
SAMPLES = os.path.join(os.environ.get('DISTRICTS_TEST_PATH_DISTRICTS', 'C:\\Program Files (x86)\\IDA Districts\\'),
                       'Samples', 'districts')


def template_file(root, feature, name):
    return os.path.join(root, feature + '_templates', name, name + '.idm')


def network_pumps(root, feature, name):
    return [p['component'] for p in detectPumps(template_file(root, feature, name))[0]]


def sample(name):
    path = os.path.join(SAMPLES, name)
    if not os.path.isdir(path):
        pytest.skip('IDA Districts sample {} not found'.format(path))
    return path


# ---------------------------------------------------------------- template graph
def test_ports():
    assert isFluidPort('INLET') and isFluidPort('|liqA1|') and isFluidPort('(|term| 2)') and isFluidPort('(HXIN 1)')
    assert not isFluidPort('OUTSIGNALLINK') and not isFluidPort('(INCONSUMLINK 1)') and not isFluidPort('TMEASURE')
    assert (portSide('|liqA2|'), portSide('|liqB1|'), portSide('|liqL|')) == ('a', 'b', '')
    assert (portSide('|evapIn|'), portSide('|condOut|')) == ('evap', 'cond')
    assert (portSide('(HXIN 1)'), portSide('(OUT 1)')) == ('coil1', 'tank')


@pytest.mark.parametrize('name, pumps', [
    ('1_ideal_heat_source', ['PUMP2']), ('2_ideal_cooling_source', ['PUMP2']),
    ('3_ideal_heat_cooling_source_2sup_2ret', ['PUMP2', 'PUMP3']), ('4_ideal_heat_cooling_source_2sup_1ret', ['PUMP2', 'PUMP3']),
])
def test_plant_pumps_found(name, pumps):
    assert network_pumps(DEFAULTS, 'energy_plant', name) == pumps


@pytest.mark.parametrize('name', ['1_simplified_consumer', '2_simplified_consumer_2sup_2ret', '3_simplified_consumer_2sup_1ret'])
def test_building_circuit_pump_not_found(name):
    # the PUMP behind side B of the substation heat exchanger moves building water
    assert network_pumps(DEFAULTS, 'customer', name) == []


def test_decentral_pumps_of_the_heat_pump_customer():
    # PUMP (heating, through the evaporator) and PUMP1 (cooling, side A of hx_cooling_substation) move network water;
    # dhw_pump_sub behind the condenser does not
    assert network_pumps(DEFAULTS, 'customer', '4_simplified_consumer_hp') == ['PUMP', 'PUMP1']


def test_low_temperature_sample():
    root = sample('low_temperature_network')
    assert network_pumps(root, 'customer', '4_simplified_consumer_hp') == ['PUMP', 'PUMP1']
    # the waste heat pump is on side B of the plant's heat exchanger
    assert network_pumps(root, 'energy_plant', '3_waste heat source') == []
    assert network_pumps(root, 'energy_plant', '2_borehole field') == []


def test_pressure_holding_pump_of_the_dynamic_optimization_sample():
    assert network_pumps(sample('dynamic_optimization'), 'energy_plant', '2_topup') == ['PUMP']


# ---------------------------------------------------------------- pump list
@pytest.fixture
def project(tmp_path):
    """a project folder with two plugin templates"""
    for feature, name in (('energy_plant', '1_ideal_heat_source'), ('customer', '4_simplified_consumer_hp')):
        shutil.copytree(os.path.dirname(template_file(DEFAULTS, feature, name)), os.path.dirname(template_file(str(tmp_path / 'p'), feature, name)))
    config = {'pathProjects': str(tmp_path) + os.sep, 'projectName': 'p'}
    templates = {'energy_plant': ['1_ideal_heat_source'], 'customer': ['4_simplified_consumer_hp']}
    return config, templates


def test_pump_list_detected_and_saved_in_the_project(project):
    config, templates = project
    data = ensurePumpList(config, templates)
    assert os.path.exists(pumpFilePath(config))
    assert os.path.dirname(pumpFilePath(config)) == os.path.join(str(config['pathProjects']) + 'p')
    assert sorted((e['feature'], e['component']) for e in data['entries']) == [
        ('customer', 'PUMP'), ('customer', 'PUMP1'), ('energy_plant', 'PUMP2')]
    assert all(e['kind'] == 'variable' and e['variable'] == 'PPUMP' and e['source'] == 'found' for e in data['entries'])


def test_removed_entry_stays_removed(project):
    config, templates = project
    data = ensurePumpList(config, templates)
    data = removeEntry(data, [e for e in data['entries'] if e['component'] == 'PUMP1'][0])
    savePumpList(config, data)
    found, _ = detectProject(config, templates)
    data = mergeDetection(loadPumpList(config), found)
    assert 'PUMP1' not in [e['component'] for e in data['entries']]


def test_added_entry_with_defaults_and_missing_component(project):
    config, templates = project
    data = ensurePumpList(config, templates)
    data['entries'].append(newEntry('customer', '4_simplified_consumer_hp', 'HP_B2B_substation', kind='estimate', source='added', eta=0.4))
    data['entries'].append(newEntry('customer', '4_simplified_consumer_hp', 'NO_SUCH_PUMP', source='added'))
    savePumpList(config, data)
    data = markMissing(config, loadPumpList(config))
    added = {e['component']: e for e in data['entries'] if e['source'] == 'added'}
    assert (added['HP_B2B_substation']['eta'], added['HP_B2B_substation']['dp_int']) == (0.4, DEFAULT_DP_INT)
    assert not added['HP_B2B_substation']['missing'] and added['NO_SUCH_PUMP']['missing']
    assert [e['component'] for e in templateEntries(data, 'customer', '4_simplified_consumer_hp')] == ['PUMP', 'PUMP1', 'HP_B2B_substation']
    assert DEFAULT_ETA == 0.5


def test_network_pumps_dialog(project, monkeypatch):
    from districts import network_pumps_dialog
    config, templates = project
    monkeypatch.setattr(network_pumps_dialog, 'projectTemplates', lambda cur: templates)
    dlg = network_pumps_dialog.NetworkPumpsDialog(config, None)
    assert dlg.table.rowCount() == 3
    components = [dlg.table.item(row, 2).text() for row in range(dlg.table.rowCount())]
    dlg.table.selectRow(components.index('PUMP1'))
    dlg.remove()
    add = network_pumps_dialog.AddPumpDialog(config, templates, dlg)
    add.combo_template.setCurrentIndex(add.combo_template.findData(network_pumps_dialog.templateKey('customer', '4_simplified_consumer_hp')))
    add.combo_component.setCurrentIndex(add.combo_component.findData('HP_B2B_substation'))
    add.combo_kind.setCurrentIndex(add.combo_kind.findData('estimate'))
    assert not add.combo_variable.isEnabled() and add.spin_eta.isEnabled()
    entry = add.entry()
    assert (entry['kind'], entry['variable'], entry['source']) == ('estimate', '', 'added')
    dlg.data['entries'].append(entry)
    dlg.fill()
    dlg.table.item(dlg.table.rowCount() - 1, 6).setText('35')
    dlg.accept()
    assert dlg.changed
    saved = loadPumpList(config)
    assert sorted(e['component'] for e in saved['entries']) == ['HP_B2B_substation', 'PUMP', 'PUMP2']
    assert [e['dp_int'] for e in saved['entries'] if e['kind'] == 'estimate'] == [35000.0]
    assert ['customer', '4_simplified_consumer_hp', 'PUMP1'] in saved['removed']


# ---------------------------------------------------------------- outputs in the templates
def template_components(root, feature, name):
    return propertyListCompsIDM(getIDAListComponents(readFileToString(template_file(root, feature, name))))


def component(comps, name):
    return [c for c in comps if getCompName(c) == '"{}"'.format(name)][0]


def var(comp, name):
    return [i for i in comp[1:] if isinstance(i, dict) and i.get(':N') == name]


def test_pump_power_output_set_and_removed():
    pump = component(template_components(DEFAULTS, 'energy_plant', '1_ideal_heat_source'), 'PUMP2')
    pump = pumpPowerComp(pump, {'"PUMP2"': 'PPUMP'}, True)
    assert [(v[':L'], v[':AS']) for v in var(pump, 'PPUMP')] == [('"PumpPower"', '"PUMP2"')]
    pump = pumpPowerComp(pump, {'"PUMP2"': 'PPUMP'}, False)
    assert all(':L' not in v for v in var(pump, 'PPUMP'))


def test_pump_without_power_variable_gets_one():
    # the pressure-holding pump of 2_topup lists only PUMPON
    pump = [{':C': ':EO', ':N': '"PUMP"', ':T': 'PUMP'}, {':C': ':VAR', ':N': 'PUMPON', ':B': '(-1 PUMPCTR 0)'}]
    pump = pumpPowerComp(pump, {'"PUMP"': 'PPUMP'}, True)
    assert var(pump, 'PPUMP') == [{':C': ':VAR', ':N': 'PPUMP', ':L': '"PumpPower"', ':AS': '"PUMP"'}]


def test_pump_no_longer_listed_loses_its_output():
    pump = [{':C': ':EO', ':N': '"PUMP"', ':T': 'PUMP'}, {':C': ':VAR', ':N': 'PPUMP', ':L': '"PumpPower"', ':AS': '"PUMP"'}]
    pump = pumpPowerComp(pump, {}, True)
    assert ':L' not in var(pump, 'PPUMP')[0]


def test_setpoint_outputs_of_the_load_model():
    loadmodel = component(template_components(DEFAULTS, 'customer', '1_simplified_consumer'), 'loadmodel')
    loadmodel = setpointOutputsComp(loadmodel, True)
    assert [(v[':L'], v[':AS']) for v in var(loadmodel, '|TSet_var|') + var(loadmodel, '|HCMode_var|')] == [
        ('"TRoom"', '"tset"'), ('"TRoom"', '"hcmode"')]
    loadmodel = setpointOutputsComp(loadmodel, False)
    assert all(':L' not in v for v in var(loadmodel, '|TSet_var|') + var(loadmodel, '|HCMode_var|'))


def test_estimates_switch_on_the_connection_outputs():
    pumps = {'entries': [newEntry('customer', 't', 'HP', kind='estimate', source='added')]}
    outputs = withEstimateConnectionOutputs({'ppump_c': True, 'ppump_ep': True, 'mdot_c': False, 'p_c': False, 'mdot_ep': False, 'p_ep': False}, pumps)
    assert (outputs['mdot_c'], outputs['p_c'], outputs['mdot_ep'], outputs['p_ep']) == (True, True, False, False)


# ---------------------------------------------------------------- requested outputs of existing projects
def test_missing_keys_are_false():
    old = {'power_c': True, 'troom_c': True}
    outputs = withDefaultOutputs(old, PLUGIN_DIR)
    assert outputs['power_c'] and outputs['troom_c'] and outputs['ppump_c'] is False and outputs['ppump_ep'] is False


def test_check_of_simulated_outputs_with_an_old_file():
    invoked = {'customers': {1: {'power_c': True, 'ppump_c': False}}, 'lines': {'temp_lines': True}}
    assert checkSimOutputs(invoked, {'power_c': True, 'temp_lines': True})


# ---------------------------------------------------------------- estimate and output files
def test_estimate_formula():
    # 0.2 kg/s, 30 kPa, dp_int 20 kPa, eta 0.5, rho 1000 -> 0.0002 m3/s * 50 kPa / 0.5 = 20 W
    assert estimatePumpPower(0.2, 100000, 130000, 20000, 0.5) == pytest.approx(20.0)


def test_estimate_from_connections():
    # a pump lifting from the inflow connection (mdot < 0 into the feature) to the outflow connection
    assert estimateFromConnections({'1': -0.2, '2': 0.2}, {'1': 100000, '2': 130000}, 20000, 0.5) == pytest.approx(20.0)
    # a classic substation: the network pushes the flow (100 kPa more at the inflow), no pump power
    assert estimateFromConnections({'1': -0.64, '2': 0.64}, {'1': 351000, '2': 251000}) == 0.0
    assert estimateFromConnections({'1': 0.0, '2': 0.0}, {'1': 1, '2': 2}) == 0.0


def test_output_files_are_read_by_header():
    columns = prnColumns('#      time         order        PUMP2        PUMP3     ')
    assert columns == {'time': 0, 'order': 1, 'pump2': 2, 'pump3': 3}
    data = np.array([[0.0, 1, 100.0, 50.0], [0.1, 1, 110.0, 55.0]])
    series = variableSeries(columns, data, [newEntry('energy_plant', 't', 'PUMP3'), newEntry('energy_plant', 't', 'PUMP9')])
    assert [(e['component'], list(v)) for e, v in series] == [('PUMP3', [50.0, 55.0])]
    conn = (prnColumns('# time order mdot_1 mdot_2 p_1 p_2 power'), np.array([[0, 1, -0.2, 0.2, 1e5, 1.3e5, 9]]))
    assert estimateSeries([conn], newEntry('customer', 't', 'HP', kind='estimate')) == [pytest.approx(20.0)]
    assert estimateSeries([], newEntry('customer', 't', 'HP', kind='estimate')) is None
