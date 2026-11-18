# coding=utf-8
"""Energy-use list of the plant and customer templates (OpenSpec change plant-energy-costs, D1-D2): detection on
synthetic templates, merge with removed entries, conflicts with the network pump list."""
import json

from districts.utility_functions.energy_use import (
    detectEnergy, detectProject, ensureEnergyList, entryKey, loadEnergyList, mergeDetection, newEntry, outputVariables,
    pumpConflicts, removeEntry, saveEnergyList,
)

PLANT = """;IDA 5.0 Data UTF-8
((:EO :N "BOIL1CIRC" :T BOIL1CIRC)
 (:PAR :N QMAX :V 3000.0)
 (:VAR :N Q :V 2092248)
 (:VAR :N QSUP :V 3170073)
 (:VAR :N BOILEFF :V 0.66))
((:EO :N "PUMP" :T PUMP)
 (:VAR :N PPUMP :V 0.0))
((MODEL :N "hx" :T |hx| :X (MODEL :N "hx2" :T |hx2|))
 (:VAR :N |PhiHx| :V -0.4507 :IV 0.0))
"""
CUSTOMER = """;IDA 5.0 Data UTF-8
((MODEL :N "HP_B2B_substation" :T HP_B2B)
 (:RES :N |model| :V "HP_B2B_MODEL")
 (:VAR :N |P_el_total| :V 41.41))
((MODEL :N "hx_cooling_substation" :T |hx| :X (MODEL :N "hx2" :T |hx2|))
 (:VAR :N |PhiHx| :V -0.4507 :IV 0.0))
"""


def project(tmp_path):
    config = {'pathProjects': str(tmp_path) + '\\', 'projectName': 'p'}
    for feature, t_name, text in (('energy_plant', '1_plant', PLANT), ('customer', '2_hp', CUSTOMER)):
        folder = tmp_path / 'p' / (feature + '_templates') / t_name
        folder.mkdir(parents=True)
        (folder / (t_name + '.idm')).write_text(text, encoding='utf-8')
    return config, {'energy_plant': ['1_plant'], 'customer': ['2_hp']}


def test_detection_of_boiler_and_heat_pump(tmp_path):
    config, templates = project(tmp_path)
    found, warnings = detectProject(config, templates)
    entries = sorted(found.values(), key=lambda e: e['feature'])
    entries = sorted(entries, key=lambda e: (e['feature'], e['component']))
    # the customer's heat exchanger (direct cooling) delivers energy; the plant's is left out
    assert [(e['feature'], e['component'], e['variable'], e['carrier'], e['absolute']) for e in entries] == [
        ('customer', 'HP_B2B_substation', '|P_el_total|', 'electricity', False), ('customer', 'hx_cooling_substation', '|PhiHx|', 'delivered', False),
        ('energy_plant', 'BOIL1CIRC', 'QSUP', 'fuel', False)]
    assert not warnings


def test_macro_component_is_warned(tmp_path):
    config, templates = project(tmp_path)
    folder = tmp_path / 'p' / 'energy_plant_templates' / '1_plant'
    (folder / 'sf-macro.idm').write_text(CUSTOMER, encoding='utf-8')
    _, warnings = detectEnergy(str(folder / '1_plant.idm'))
    assert warnings == [('macro_energy', 'sf-macro.idm', 'HP_B2B_substation')]


def test_list_saved_and_removed_entry_stays_removed(tmp_path):
    config, templates = project(tmp_path)
    data = ensureEnergyList(config, templates)
    assert len(data['entries']) == 3 and not any(e['missing'] for e in data['entries'])
    boiler = next(e for e in data['entries'] if e['component'] == 'BOIL1CIRC')
    boiler['carrier'] = 'purchased_heat'
    data = removeEntry(data, next(e for e in data['entries'] if e['component'] == 'HP_B2B_substation'))
    saveEnergyList(config, data)
    data = mergeDetection(loadEnergyList(config), detectProject(config, templates)[0])
    assert sorted((e['component'], e['carrier']) for e in data['entries']) == [('BOIL1CIRC', 'purchased_heat'), ('hx_cooling_substation', 'delivered')]
    with open(tmp_path / 'p' / 'energyUse.json', encoding='utf-8') as f:
        assert json.load(f)['removed'] == [['customer', '2_hp', 'HP_B2B_substation']]
    assert outputVariables(data, 'energy_plant', '1_plant') == {'"BOIL1CIRC"': ('QSUP', '"E1"')}


def test_component_in_the_pump_list_conflicts():
    hp = newEntry('customer', '2_hp', 'HP_B2B_substation', '|P_el_total|', 'electricity')
    pumps = {'entries': [{'feature': 'customer', 'template': '2_hp', 'component': 'HP_B2B_substation'}]}
    assert pumpConflicts({'entries': [hp]}, pumps) == {entryKey(hp)}
    assert newEntry('customer', 't', 'c', 'V', 'gas')['carrier'] == 'electricity'


def test_energy_output_set_beside_a_pump_output_and_removed():
    from districts.outputs import listOutputComp, pumpPowerComp
    boiler = [{':C': ':EO', ':N': '"BOIL1CIRC"', ':T': 'BOIL1CIRC'}, {':C': ':VAR', ':N': 'QSUP', ':V': 3170073},
              {':C': ':VAR', ':N': 'PPUMP', ':L': '"PumpPower"', ':AS': '"BOIL1CIRC"'}]
    boiler = listOutputComp(boiler, {'"BOIL1CIRC"': ('QSUP', '"E1"')}, True, '"EnergyUse"')
    by_name = {i[':N']: i for i in boiler[1:]}
    # the column is the alias: IDA cuts column names to 10 characters
    assert (by_name['QSUP'][':L'], by_name['QSUP'][':AS']) == ('"EnergyUse"', '"E1"')
    assert by_name['PPUMP'][':L'] == '"PumpPower"'  # the pump output stays
    boiler = listOutputComp(boiler, {'"BOIL1CIRC"': ('QSUP', '"E1"')}, False, '"EnergyUse"')
    assert ':L' not in {i[':N']: i for i in boiler[1:]}['QSUP']
    assert pumpPowerComp(boiler, {'"BOIL1CIRC"': 'PPUMP'}, True)[2][':L'] == '"PumpPower"'


def test_every_optimization_output_has_its_checkbox():
    """the cost optimization switches its outputs on through the checkboxes of the requested-outputs dialog"""
    import os
    from districts.cost_optimization import OPTIMIZATION_OUTPUTS, OUTPUT_CHECKBOXES
    assert {'energy_ep', 'energy_c', 'mdot_ep'} <= set(OPTIMIZATION_OUTPUTS)
    assert set(OPTIMIZATION_OUTPUTS) <= set(OUTPUT_CHECKBOXES)
    with open(os.path.join(os.path.dirname(os.path.dirname(__file__)), 'RequestedOutputs_dialog.ui'), encoding='utf-8') as f:
        ui = f.read()
    assert all('name="{}"'.format(name) in ui for name in OUTPUT_CHECKBOXES.values())


def test_dialog_changes_the_carrier_and_marks_a_pump_conflict(tmp_path, monkeypatch):
    import districts.energy_use_dialog as dialog_module
    from districts.utility_functions.network_pumps import newEntry as pumpEntry, savePumpList
    config, templates = project(tmp_path)
    monkeypatch.setattr(dialog_module, 'projectTemplates', lambda cur: templates)
    savePumpList(config, {'entries': [pumpEntry('energy_plant', '1_plant', 'BOIL1CIRC')], 'removed': []})
    dlg = dialog_module.EnergyUseDialog(config, None)
    row = next(r for r, e in enumerate(dlg.data['entries']) if e['component'] == 'BOIL1CIRC')
    assert 'network pump' in dlg.log.toPlainText()
    combo = dlg.table.cellWidget(row, dialog_module.COL_CARRIER)
    combo.setCurrentIndex(combo.findData('purchased_heat'))
    dlg.table.item(row, dialog_module.COL_NAME).setText('waste heat')
    dlg.accept()
    assert dlg.changed
    saved = {e['component']: e for e in loadEnergyList(config)['entries']}
    assert (saved['BOIL1CIRC']['carrier'], saved['BOIL1CIRC']['name']) == ('purchased_heat', 'waste heat')


def test_system_boundary_from_the_setting_or_the_customers_heat_pumps():
    from districts.utility_functions.economic_data import systemBoundary
    hp = newEntry('customer', '2_hp', 'HP_B2B_substation', '|P_el_total|', 'electricity')
    boiler = newEntry('energy_plant', '1_plant', 'BOIL1CIRC', 'QSUP', 'fuel')
    assert systemBoundary({'scenario': {'system_boundary': 'automatic'}}, {'entries': [hp, boiler]}) == 'system'
    assert systemBoundary({'scenario': {'system_boundary': None}}, {'entries': [boiler]}) == 'operator'
    assert systemBoundary({'scenario': {'system_boundary': 'operator'}}, {'entries': [hp]}) == 'operator'
