# coding=utf-8
"""Ground collector routes without a database (change ground-collector-routes, task 8.1): fit cache, start values,
terminals, costs, the GroundMo check, the preset inputs and the result file header."""
import json
from types import SimpleNamespace

import pytest

from districts.utility_functions import ground_collectors as gc
from districts.utility_functions import ground_rc as rc
from districts.utility_functions.network_economics import investments

SETTINGS = {'kusuda_tsurfmean': 9.0, 'kusuda_tsurfampl': 10.0, 'kusuda_theta': 30.0}


class FakeCursor:
    """answers the loop pipe query and records the stored fits"""

    def __init__(self):
        self.stored = []
        self.row = None

    def execute(self, sql, params=None):
        if 'FROM public.pipes p' in sql:
            self.row = {'innerpipediameter': 0.0326, 'piperoughnessfactor': 7e-6, 'thickness': 0.003,
                        'thermal_conductivity_w7mkelvin': 0.4}
        elif sql.startswith('UPDATE public.ground_collectors SET fits'):
            self.stored.append(json.loads(params[0]))
            self.row = None

    def fetchone(self):
        return self.row


def resource(**changes):
    row = {'id': 1, 'name': 'ring', 'preset': 'horizontal_ring', 'preset_inputs': dict(gc.PRESET_DEFAULTS['horizontal_ring']),
           'pipe_id': 7, 'loop_sequence': 1, 'liquid_id': 1, 't_freeze_liquid_c': 0, 'lambda_w7mk': 1.5, 'rho_c_j7m3k': 2.2e6, 'water_content': 0.25, 't_freeze_c': 0,
           'freeze_range_k': 1, 'lambda_frozen_ratio': 1.2, 'albedo': 0.2, 'epsilon': 0.95, 'h_conv_w7m2k': 10,
           'd_layer_m': 0.05, 'rho_c_layer_j7m3k': 2.2e6, 'n_loops': 1, 't_mean_init': 5, 'start_mode': 'undisturbed',
           'start_years': 5, 'n_sections': 3, 'fits': {}}
    row.update(changes)
    return row


@pytest.fixture
def fake_fit(monkeypatch):
    calls = []

    def fitRc(geometry, soil, surface, settings=None):
        calls.append(soil.water_content)
        return SimpleNamespace(values={'cTop': 1.0}, t_deep=9.0, errors={'outside': 0.01, 'wall': 0.02},
                               steady_error=0.001, accepted=True)
    monkeypatch.setattr(rc, 'fitRc', fitRc)
    return calls


def test_fit_is_cached_by_fingerprint(fake_fit):
    cur, res = FakeCursor(), resource()
    entry = gc.fitFor(cur, res, SETTINGS)[0]
    assert fake_fit == [0.0]  # fitted on dry soil, the freezing comes with the parameters
    assert entry['accepted'] and entry['fit_version'] == rc.FIT_VERSION
    assert len(cur.stored) == 1 and entry['fingerprint'] in cur.stored[0]
    assert gc.cachedFit(cur, res, SETTINGS)['values'] == {'cTop': 1.0}
    gc.fitFor(cur, res, SETTINGS)
    assert len(fake_fit) == 1 and len(cur.stored) == 1  # the second call takes the cache
    # another soil is another fingerprint: fitted again, the old entry (same fit version) kept
    other = dict(res, lambda_w7mk=2.0)
    gc.fitFor(cur, other, SETTINGS)
    assert len(fake_fit) == 2 and len(cur.stored[-1]) == 2


def test_stale_fit_versions_are_dropped(fake_fit):
    cur = FakeCursor()
    res = resource(fits={'old': {'fit_version': -1, 'accepted': True}})
    gc.fitFor(cur, res, SETTINGS)
    assert 'old' not in cur.stored[-1]


def test_water_content_does_not_change_the_fingerprint(fake_fit):
    cur = FakeCursor()
    a = gc.fitKey(cur, resource(water_content=0.1), SETTINGS)[0]
    b = gc.fitKey(cur, resource(water_content=0.4), SETTINGS)[0]
    assert a == b


def test_precalculated_start_values_are_cached(monkeypatch, fake_fit, tmp_path):
    cur, res = FakeCursor(), resource(start_mode='precalculated')
    entry, geometry, soil, surface = gc.fitFor(cur, res, SETTINGS)
    climate = tmp_path / 'climate.prn'
    climate.write_text('x')
    calls = []
    monkeypatch.setattr('districts.utility_functions.ground_climate.weatherFromFile', lambda *a, **k: 'year')
    def startState(*a, **k):
        calls.append((a, k))
        return {'TStartLoc': 4.0}
    monkeypatch.setattr(rc, 'startState', startState)
    site = {'lat': 47.0, 'long': 8.0, 'long_timezone': 15.0}
    first = gc.startValues(cur, res, entry, geometry, soil, {}, 5.0, str(climate), site, 10.0)
    again = gc.startValues(cur, res, entry, geometry, soil, {}, 5.0, str(climate), site, 10.0)
    assert first == again == {'TStartLoc': 4.0} and len(calls) == 1
    assert calls[0][1]['years'] == 5 and calls[0][1]['start_day'] == 10.0
    gc.startValues(cur, res, entry, geometry, soil, {}, 7.0, str(climate), site, 10.0)
    assert len(calls) == 2  # another mean temperature, another state
    assert any(entry['starts'] for entry in cur.stored[-1].values())


def test_line_terminals_four_pipes_loop_two():
    terminals = gc.lineTerminals(12, [1, 2, 3, 4], 2)
    assert terminals == {1: ('Pipebundle_12', 1), 2: ('Collector_12', None), 3: ('Pipebundle_12', 2), 4: ('Pipebundle_12', 3)}


def test_collector_item_17024():
    info = {'name': 'ring', 'n_loops': 4, 'loop_length_per_m': 6.28, 'cost_trench_eur7m': 30.0, 'cost_loop_eur7m': 2.0,
            'maintenance_pct': 1.0, 'lifetime_a': 50.0, 'loop_sequence': 1}
    item = gc.collectorItem(info, 100.0)
    assert item['cost'] == pytest.approx(17024.0)
    assert item['length'] == 400.0 and item['loop_m'] == pytest.approx(2512.0)


def test_investments_with_a_collector_line():
    pipe = {'pipe_id': 1, 'name': 'PE 32', 'costs': 10.0, 'lifetime_a': 50, 'maintenance_pct': 1, 'example': False,
            'description': 'DN 25', 'innerpipediameter': 0.026}
    other = dict(pipe, pipe_id=2, name='DN 100', costs=500.0, description='DN 100', innerpipediameter=0.1)
    lines = {5: {'length': 100.0, 'pipes': {1: pipe, 2: other}}}
    trench = {5: {'paved': 100.0}}
    scenario = {'trench': {'paved': (100.0, 1.0)}, 'scenario': {}}
    info = {'name': 'ring', 'n_loops': 4, 'loop_length_per_m': 6.28, 'cost_trench_eur7m': 30.0, 'cost_loop_eur7m': 2.0,
            'maintenance_pct': 1.0, 'lifetime_a': 50.0, 'loop_sequence': 1}
    items = investments(scenario, lines, trench, {5: info})[0]
    assert items[('collector', 'ring')]['cost'] == pytest.approx(17024.0)
    assert ('pipe', 1) not in items  # the loop pipe is the collector item
    assert items[('pipe', 2)]['cost'] == pytest.approx(50000.0)
    assert not any(key[0] == 'trench' for key in items)  # the other pipe lies in the collector trench
    plain = investments(scenario, lines, trench)[0]
    assert ('pipe', 1) in plain and ('trench', 'paved') in plain


def test_groundmo_contract_version(tmp_path):
    assert gc.groundMoContractVersion(str(tmp_path)) is None
    folder = tmp_path / 'lib' / 'Components' / 'GroundMo'
    folder.mkdir(parents=True)
    eo = folder / 'GroundMo.eo'
    eo.write_text('((:par :n |nLoops| :t INTEGER :v 1)\n (:par :n |contractVersion| :t INTEGER  :v 2 :kv INTEGER :x (C_P contractVe) :f #x160 :d "Version of the parameter contract"))')
    assert gc.groundMoContractVersion(str(tmp_path)) == 2
    eo.write_text('(:par :n |nLoops| :t INTEGER :v 1)')
    assert gc.groundMoContractVersion(str(tmp_path)) is None


def test_every_preset_builds_its_geometry():
    for preset, inputs in gc.PRESET_DEFAULTS.items():
        geometry = gc.collectorModel(resource(preset=preset, preset_inputs=inputs),
                                     {'d_inner': 0.0326, 'd_outer': 0.04, 'lambda_wall': 0.4}, SETTINGS)[0]
        assert geometry.loop_length_per_m > 0, preset


class DialogCursor(FakeCursor):
    """the queries of the resource dialog: one stored type, two pipes"""

    def __init__(self, stored):
        super().__init__()
        self.stored_rows, self.rows = stored, []
        self.connection = SimpleNamespace(autocommit=True)

    def execute(self, sql, params=None):
        super().execute(sql, params)
        if sql.startswith('SELECT id, name FROM public.pipes'):
            self.rows = [{'id': 7, 'name': 'PE 40'}, {'id': 8, 'name': 'PE 32'}]
        elif sql.startswith('SELECT id, liquid FROM public.liquids'):
            self.rows = [{'id': 1, 'liquid': 'Water'}, {'id': 2, 'liquid': 'Freezium'}]
        elif sql.startswith('SELECT * FROM public.ground_collectors'):
            self.rows = self.stored_rows

    def fetchall(self):
        return self.rows


def test_resource_dialog(qgis_app, tmp_path, fake_fit):
    from districts.ground_collectors_dialog import GroundCollectorsDialog
    from districts.utility_functions.dialog import qt_item_flag
    from districts.utility_functions.translations import tr_msg
    stored = [resource(fits={})]
    main = SimpleNamespace(cur=DialogCursor(stored), iface=None, plugin_dir=str(tmp_path),
                           config={'projectName': '', 'versionName': 'v'})
    dlg = GroundCollectorsDialog(main)
    dlg.settings = dict(SETTINGS)
    assert dlg.table.rowCount() == 1 and dlg.rowId(0) == 1
    assert dlg.rowValues(0)['preset_inputs'] == gc.PRESET_DEFAULTS['horizontal_ring']
    assert dlg.table.cellWidget(0, dlg.keys.index('pipe_id')).currentData() == 7
    row = dlg.addRow()
    assert dlg.cellText(row, 'name') == tr_msg('Collector') and dlg.rowId(row) is None
    assert 'n_loops' not in dlg.keys  # the loops belong to the line
    assert 'freeze_range_k' not in dlg.keys and 't_freeze_c' not in dlg.keys  # soil water: 0 degC, 1 K
    values = dlg.rowValues(row)
    assert (values['liquid_id'], values['t_freeze_liquid_c']) == (1, 0.0)
    liquid = dlg.table.cellWidget(row, dlg.keys.index('liquid_id'))
    liquid.setCurrentIndex(liquid.findData(2))
    assert liquid.currentText() == 'Freezium' and dlg.rowValues(row)['liquid_id'] == 2
    preset = dlg.table.cellWidget(row, dlg.keys.index('preset'))
    preset.setCurrentIndex(preset.findData('bare_pipe'))
    assert dlg.rowValues(row)['preset_inputs'] == gc.PRESET_DEFAULTS['bare_pipe']
    pitch = dlg.table.item(row, dlg.keys.index('pitch_m'))
    assert pitch.text() == '' and not pitch.flags() & qt_item_flag('ItemIsEditable')  # not an input of a bare pipe
    preset.setCurrentIndex(preset.findData('flat_meander'))
    assert dlg.rowValues(row)['preset_inputs'] == gc.PRESET_DEFAULTS['flat_meander']
    dlg.table.item(row, dlg.keys.index('layer_width_m')).setText('')
    with pytest.raises(ValueError):
        dlg.rowValues(row)
    dlg.table.setCurrentCell(row, 0)
    dlg.copyRow()
    copy = dlg.table.rowCount() - 1
    assert dlg.cellText(copy, 'name') == tr_msg('Collector') + ' 2'
    assert dlg.table.cellWidget(copy, dlg.keys.index('preset')).currentData() == 'flat_meander'
    assert dlg.cellText(copy, 'layer_width_m') == '' and dlg.cellText(copy, 'pipe_spacing_m') == '0.5'
    dlg.close()


def test_line_form_fields_at_the_end_of_the_physical_data():
    from districts.utility_functions.layer_visualization import addMissingFormFields
    old = {'lines': {'general': ['type', 'n_loops', 't_mean_init', 'network'], 'physical_data': ['length', 'zeta']}}
    assert addMissingFormFields(old)
    assert old['lines'] == {'general': ['type', 'network'], 'physical_data': ['length', 'zeta', 'n_loops', 't_mean_init']}
    assert not addMissingFormFields(old)  # a second load changes nothing


def test_result_columns_from_the_header():
    header = '#      time         order        ice_1        ice_2        qextracted   qsurface     tin          tloc_1       tloc_2       tnear_1      tnear_2      tout\n'
    columns = gc.collectorResultColumns(header, 2)
    assert columns['coll_tin'] == [6] and columns['coll_tout'] == [11]
    assert columns['coll_tloc'] == [7, 8] and columns['coll_ice'] == [2, 3]
    assert 'coll_tloc' not in gc.collectorResultColumns(header, 3)  # a section missing in the file
