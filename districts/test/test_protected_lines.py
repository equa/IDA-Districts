# coding=utf-8
"""Protected lines of the dynamic pipe sizing (OpenSpec change protect-lines). No database, no IDA Districts."""
import json

import pytest

from districts.utility_functions.dynamic_sizing_results import pairSummary
from districts.utility_functions.hydraulic_balancing import optimizePipeDiameters
from districts.utility_functions.protected_lines import FILE_NAME, loadProtectedLines, parseProtectedEntries, saveProtectedLines

CATALOG: dict = {pid: {'d': d, 'k': 1e-5, 'construction': 1, 'series': 'A', 'name': 'P{}'.format(pid)}
           for pid, d in ((1, 0.03), (2, 0.04), (3, 0.05), (4, 0.065))}


def network(pipe_line2=4):
    """Trunk 1 to both customers, branch 2 to customer 10 (dp 100 kPa), branch 3 to the weak point 20 (dp 50 kPa)."""
    def line(length, mdot, pid):
        return {'length': length, 'bundle': 1, 'pipes': {seq: {'pipe_id': pid, 'mdot': mdot, 'temp': temp, 'mdot_max': mdot, 'temp_default': False}
                                                        for seq, temp in ((1, 70.0), (2, 40.0))}}
    lines = {1: line(100.0, 2.0, 4), 2: line(50.0, 1.0, pipe_line2), 3: line(200.0, 1.0, 4)}
    c_lid = {10: [100000.0, {1: [0.0, 1.0], 2: [0.0, 1.0]}], 20: [50000.0, {1: [0.0, 1.0], 3: [0.0, 1.0]}]}
    return c_lid, lines


def pipes_of(opt, lid):
    return set(opt['pipes'][lid].values())


# ---------------------------------------------------------------- sizing and balancing
def test_balancing_reduces_an_unprotected_line():
    c_lid, lines = network()
    opt = optimizePipeDiameters(c_lid, lines, CATALOG, dp_spez_max=None)
    assert pipes_of(opt, 2) != {4} and opt['protected'] == []


def test_protected_line_is_not_reduced():
    c_lid, lines = network()
    opt = optimizePipeDiameters(c_lid, lines, CATALOG, dp_spez_max=None, protected={2, 99})
    assert pipes_of(opt, 2) == {4}
    assert opt['protected'] == [2]  # 99 is no line of the circuit
    assert 10 in opt['blocked']  # its only line outside the weak point's path is protected
    assert opt['c_lid'][10][0] == pytest.approx(100000.0)


def test_protected_line_is_not_presized():
    c_lid, lines = network()
    opt = optimizePipeDiameters(c_lid, lines, CATALOG, dp_spez_max=None, dp_spez_setpoint=100.0, presize_only=True, protected={2})
    assert pipes_of(opt, 2) == {4}
    assert pipes_of(opt, 3) == {3}
    assert all(entry['lid'] != 2 for entry in opt['presize'])


def test_protected_line_is_not_enlarged_and_reported():
    c_lid, lines = network(pipe_line2=1)
    opt = optimizePipeDiameters(c_lid, lines, CATALOG, dp_spez_max=300.0)
    assert CATALOG[next(iter(pipes_of(opt, 2)))]['d'] > 0.03 and opt['protected_over_max'] == []
    opt = optimizePipeDiameters(c_lid, lines, CATALOG, dp_spez_max=300.0, protected={2})
    assert pipes_of(opt, 2) == {1}
    assert opt['protected_over_max'] == [2]


# ---------------------------------------------------------------- list entries and the file
@pytest.mark.parametrize('texts, ids, invalid', [
    (['12', ' 15 ', '', '12'], [12, 15], []),
    (['12a', '0', '-3', '7'], [7], ['12a', '0', '-3']),
    ([], [], []),
])
def test_parse_entries(texts, ids, invalid):
    assert parseProtectedEntries(texts) == (ids, invalid)


@pytest.fixture
def config(tmp_path):
    (tmp_path / 'p' / 'versions' / 'v').mkdir(parents=True)
    return {'pathProjects': str(tmp_path), 'projectName': 'p', 'versionName': 'v'}


def test_save_and_load(config, tmp_path):
    assert loadProtectedLines(config) == []
    saveProtectedLines(config, [12, 15])
    assert json.loads((tmp_path / 'p' / 'versions' / 'v' / FILE_NAME).read_text()) == {'lines': [12, 15]}
    assert loadProtectedLines(config) == [12, 15]


# ---------------------------------------------------------------- iteration file
def test_pair_summary_marks_protected_lines():
    res = {'catalog': CATALOG, 'c_lid': {10: [1e5, {}]}, 'dvar': {}, 'times': {}, 'time': 't', 'cid_dp': 10, 'epid_dp': 1, 'dp': 4e4,
           'dp_spez': {}, 'lines': network()[1]}
    opt = {'c_lid': {}, 'pipes': {}, 'cid_weak': 10, 'dp_target': 1e5, 'quota': 1.0, 'spread': 0.0, 'presize': [], 'history': [], 'protected': [2]}
    pair = pairSummary((1, 2), (70.0, 40.0), res, opt, set())
    assert pair['n_protected'] == 1 and pair['lines']['2']['protected'] and not pair['lines']['3']['protected']
    del opt['protected']  # result without protection (as in files of earlier runs)
    assert pairSummary((1, 2), (70.0, 40.0), res, opt, set())['n_protected'] == 0


# ---------------------------------------------------------------- dialog
@pytest.fixture
def sizing_dialog(qgis_app):
    from districts.dynamic_pipe_sizing import DynamicPipeSizingDialog
    dlg = DynamicPipeSizingDialog(main=None)
    yield dlg
    dlg.close()


def test_dialog_add_and_remove(sizing_dialog):
    dlg = sizing_dialog
    assert dlg.protectedTexts() == []
    dlg.btn_addProtected.click()
    dlg.list_protectedLines.item(0).setText('12')
    dlg.addProtectedEntry(15)
    assert dlg.protectedTexts() == ['12', '15']
    dlg.list_protectedLines.clearSelection()
    dlg.list_protectedLines.item(0).setSelected(True)
    dlg.btn_removeProtected.click()
    assert dlg.protectedTexts() == ['15']


def test_dialog_adds_selected_lines(sizing_dialog):
    from qgis.core import QgsFeature, QgsProject, QgsVectorLayer
    from districts.utility_functions.translations import tr
    layer = QgsVectorLayer('LineString?field=id:integer', tr('@default', 'lines'), 'memory')
    features = []
    for lid in (12, 15, 18):
        f = QgsFeature(layer.fields())
        f['id'] = lid
        features.append(f)
    layer.dataProvider().addFeatures(features)
    QgsProject.instance().addMapLayer(layer)
    try:
        layer.selectByExpression('"id" IN (12, 15)')
        dlg = sizing_dialog
        dlg.addProtectedEntry(12)
        dlg.btn_addSelectedProtected.click()
        assert dlg.protectedTexts() == ['12', '15']
    finally:
        QgsProject.instance().removeMapLayer(layer.id())


def test_dialog_filled_from_the_version_file(sizing_dialog, config):
    saveProtectedLines(config, [12, 15])
    sizing_dialog.fillProtectedLines(config)
    assert sizing_dialog.protectedTexts() == ['12', '15']
