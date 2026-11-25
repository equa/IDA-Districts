"""Generated IDA climate macro (change climate-macro-build): columns of the climate file, the macro's objects for both
file layouts, ground and duct temperature from the settings, the backup of a hand-made macro, where the macros are
written. No DB, no IDA (the IDA run is test_climate_macro_ida.py)."""
import os
import re

import numpy as np
import pytest

from districts.utility_functions import climate_macro as cm
from districts.utility_functions import ground_climate as gc

DATA = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'data')
BROMMA = os.path.join(DATA, 'climate_bromma_excerpt.prn')     # IDA layout, no header (IDA 5.2 climate folder)
ABO = os.path.join(DATA, 'climate_abo_excerpt.prn')           # header, WindX/WindY, SkyCover, PRECIPITATION, ALBEDO
SETTINGS = {'ground_model': 'Kusuda', 'kusuda_tsurfmean': 7, 'kusuda_tsurfampl': 8, 'kusuda_theta': 30,
            'kusuda_rho': 1387, 'kusuda_cp': 1344, 'kusuda_lambda': 1.18, 'kusuda_depth': 1, 'ground_temp': 10,
            'duct_temp': 18}
PLUGIN = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def _climate(path):
    return {'file_name': path, 'latitude': 59.366, 'longitude': -17.9999, 'timezone': -1, 'height': 27}


def _objects(folder):
    with open(os.path.join(folder, 'climate-macro.idm'), encoding='utf-8') as f:
        text = f.read()
    return text, set(re.findall(r'^\(+\S+[^\n]*?:N "([^"]+)"', text, re.M))


def test_columns_without_header():
    columns = cm.climateColumns(BROMMA)
    assert not columns.header
    assert [k for _, k, _ in columns.columns] == list(cm.IDA_LAYOUT)
    assert columns.wind == 'dirvel' and columns.extra == []


def test_columns_with_header():
    columns = cm.climateColumns(ABO)
    assert columns.header and columns.wind == 'xy'
    assert (columns.number('windx'), columns.number('windy')) == (4, 5)
    assert columns.extra == [(8, 'SkyCover'), (9, 'PRECIPITATION'), (10, 'ALBEDO')]


def test_required_quantity_missing(tmp_path):
    path = tmp_path / 'no_tair.prn'
    path.write_text('#Time RelHum WindDir WindVel IDirNorm IDiffHor\n0 80 140 3 0 0\n', encoding='utf-8')
    with pytest.raises(ValueError, match=r'missing tair; its columns are Time, RelHum'):
        cm.climateColumns(str(path))


def test_macro_ida_layout(tmp_path):
    signals = cm.writeClimateMacro(str(tmp_path), _climate(BROMMA), SETTINGS)
    text, names = _objects(str(tmp_path))
    assert cm.MARKER in text
    assert {'climate_file', 'climate_processor', 'vel', 'ISolar', 'IGlob', 'TGround', 'Kusuda', 'TDuct',
            'TDuct-Const', 'Schedule1'} <= names
    assert '(:VAR :N WINDDIR :B (:MACRO "climate_file" WINDDIR))' in text
    assert '((MODEL :N "vel" :T |Gain|)' in text and 'vel2' not in names
    assert '(:VAR :N SKYCOVER :B :IV)' in text and 'PRECIPITATION' not in text
    assert '(:RES :N SCHEDULE-DATA :V "Shading")' in text
    assert set(signals) == {'TAIR2', 'TSKY', 'ELEVSUN', 'vel', 'ISolar', 'IGlob', 'TGround', 'TDuct'}
    assert os.path.exists(tmp_path / 'climate-macro.idc')


def test_macro_wind_components_and_extra_columns(tmp_path):
    signals = cm.writeClimateMacro(str(tmp_path), _climate(ABO), SETTINGS)
    text, names = _objects(str(tmp_path))
    assert '(:VAR :N WINDX :B (:MACRO "climate_file" WINDX))' in text
    assert '((MODEL :N "vel" :T |Sqrt|)' in text and {'v_dx2', 'v_dy2', 'vel2'} <= names
    assert '(:VAR :N SKYCOVER :B (:MACRO "climate_file" SKYCOVER))' in text
    assert '(:VAR :N PRECIPITATION :B (:MACRO "climate_file" PRECIPITATION))' in text
    assert '((MODEL :N "albedo" :T |Gain|)\n (:PAR :N |k| :V 0.01)' in text
    assert {'SkyCover', 'PRECIPITATION', 'albedo'} <= set(signals)
    # IDA compares names without case: no second object ALBEDO next to albedo
    lower = [n.lower() for n in names]
    assert len(lower) == len(set(lower))


def test_constant_ground_and_duct_temperature(tmp_path):
    cm.writeClimateMacro(str(tmp_path), _climate(BROMMA), dict(SETTINGS, ground_model='Constant', ground_temp=9,
                                                               duct_temp=18))
    text, names = _objects(str(tmp_path))
    assert 'Kusuda' not in names and 'TGround-Const' in names
    assert '((SOURCE-CONSTANT :N "TGround-Const" :T CONSTANT)\n (:PAR :N X :V 9))' in text
    assert '((SOURCE-CONSTANT :N "TDuct-Const" :T CONSTANT)\n (:PAR :N X :V 18))' in text


def test_hand_made_macro_kept_once(tmp_path):
    (tmp_path / 'climate-macro.idm').write_text(';IDA 5.21801 Data UTF-8\n(DOCUMENT-HEADER :TYPE DISTRICTS-MACRO)\n'
                                                ';hand made\n', encoding='utf-8')
    cm.writeClimateMacro(str(tmp_path), _climate(BROMMA), SETTINGS)
    cm.writeClimateMacro(str(tmp_path), _climate(ABO), SETTINGS)
    assert 'hand made' in (tmp_path / 'climate-macro.idm.bak').read_text(encoding='utf-8')
    (tmp_path / 'climate-macro.idm.bak').unlink()
    cm.writeClimateMacro(str(tmp_path), _climate(BROMMA), SETTINGS)
    assert not (tmp_path / 'climate-macro.idm.bak').exists()


class _Cursor:
    """the climate row of the version and the template tables, as writeProjectClimateMacros reads them"""

    def __init__(self, climate):
        self.climate = climate
        self.rows = []

    def execute(self, sql, *args):
        if 'climate' in sql:
            self.rows = [self.climate]
        elif 'customer_templates' in sql:
            self.rows = [{'template': 1, 'template_name': 'simplified_consumer'}]
        else:
            self.rows = [{'template': 2, 'template_name': 'ideal_heat_source'}, {'template': 3, 'template_name': 'gone'}]

    def fetchone(self):
        return self.rows[0]

    def fetchall(self):
        return self.rows


def test_project_and_template_macros_written(tmp_path, monkeypatch):
    from districts import ida_resources
    monkeypatch.setattr(ida_resources, 'getClimateData', lambda cur, config, msg: {
        'filename': ABO, 'latitude': 46.38, 'longitude': -7.13, 'timezone': -1, 'height': 300})
    project = tmp_path / 'p'
    for folder in ('customer_templates/1_simplified_consumer', 'energy_plant_templates/2_ideal_heat_source'):
        (project / folder).mkdir(parents=True)
    config = {'pathProjects': str(tmp_path), 'projectName': 'p', 'versionName': 'base1'}
    ida_resources.writeProjectClimateMacros(_Cursor({}), config, SETTINGS)
    for folder in ('climate/climate', 'customer_templates/1_simplified_consumer',
                   'energy_plant_templates/2_ideal_heat_source'):
        text = (project / folder / 'climate-macro.idm').read_text(encoding='utf-8')
        assert cm.MARKER in text and 'climate_abo_excerpt.prn' in text, folder
    # a template without a folder (deleted) gets nothing
    assert not (project / 'energy_plant_templates' / '3_gone').exists()


def test_every_parent_defines_the_shading_data():
    """the macro's schedule reads the schedule data "Shading" from its parent document"""
    for module in ('invoke_network.py', 'supervisory_control.py', os.path.join('utility_functions', 'templateFiles.py')):
        with open(os.path.join(PLUGIN, module), encoding='utf-8') as f:
            assert '(SCHEDULE-DATA :N "Shading"' in f.read(), module


def test_no_shipped_climate_macros():
    shipped = [os.path.join(r, f) for r, _, fs in os.walk(PLUGIN) for f in fs if f.lower().startswith('climate-macro.id')]
    assert shipped == []


def test_weather_from_a_header_file():
    """sky cover and albedo come from the file, as in the generated macro"""
    site = {'lat': 46.38, 'long': -7.13, 'long_timezone': -15}
    w = gc.weatherFromFile(ABO, site)
    columns = np.loadtxt(ABO, comments='#')
    np.testing.assert_allclose(w['albedo'], columns[:, 9] / 100)
    np.testing.assert_allclose(w['TSky'], gc.skyTemperature(columns[:, 1], columns[:, 2], columns[:, 7]))
    assert not np.allclose(w['TSky'], columns[:, 1] - 5.0)
    bromma = gc.weatherFromFile(BROMMA, site, albedo=0.3)
    assert np.all(bromma['albedo'] == 0.3)
    np.testing.assert_allclose(bromma['TSky'], np.loadtxt(BROMMA)[:, 1] - 5.0)
