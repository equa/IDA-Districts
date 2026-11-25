"""The generated climate macro in IDA Districts (change climate-macro-build): a system with the macro for a climate file
without a header (BROMMA.PRN) and one with a header, wind components and extra columns (ABO_dry_NORMAL.prn) simulates
one year, and its global horizontal radiation IGlob agrees with the Python radiation within 1 %."""
import os
import shutil

import numpy as np
import pytest

from districts.simulate_process import simulateInProcess
from districts.utility_functions import climate_macro as cm
from districts.utility_functions import ground_climate as gc

pytestmark = pytest.mark.ida

PATH_DISTRICTS = os.environ.get('DISTRICTS_TEST_PATH_DISTRICTS', r'C:\Program Files (x86)\IDA Districts')
PLUGIN = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
FILES = {'bromma': (os.path.join(PATH_DISTRICTS, 'climate', 'BROMMA.PRN'), 59.366, -17.9999),
         'abo': (r'C:\Program Files (x86)\IDA52\ex\local-ch\Climate\ABO_dry_NORMAL.prn', 46.38, -7.13)}
SETTINGS = {'ground_model': 'Kusuda', 'kusuda_tsurfmean': 7, 'kusuda_tsurfampl': 8, 'kusuda_theta': 30,
            'kusuda_rho': 1387, 'kusuda_cp': 1344, 'kusuda_lambda': 1.18, 'kusuda_depth': 1, 'ground_temp': 10,
            'duct_temp': 18}
YEAR = ':V 3881520000)'


def _system(folder):
    """the project template's climate system, run for a year with IGlob in its output file"""
    with open(os.path.join(PLUGIN, 'templates', 'empty_project', 'climate', 'climate.idm'), encoding='utf-8') as f:
        text = f.read()
    text = text.replace(':V 3850070400)', YEAR).replace('(:PAR :N OUTPUT-STEP :V 0.1)', '(:PAR :N OUTPUT-STEP :V 1)')
    text = text.replace(':B (1 "Climate-macro" "vel" |y_var|) :S (:DEFAULT NIL 2)))',
                        ':B (1 "Climate-macro" "vel" |y_var|) :S (:DEFAULT NIL 2))\n'
                        ' (:VAR :N IGLOB :T GENERIC :D "IGlob" :U || :IV NIL :B (1 "Climate-macro" "IGlob" OUTSIGNAL)))')
    with open(os.path.join(folder, 'climate.idm'), 'w', encoding='utf-8') as f:
        f.write(text)
    shutil.copy(os.path.join(PLUGIN, 'templates', 'empty_project', 'climate', 'climate.idc'), folder)


@pytest.mark.parametrize('name', list(FILES))
def test_generated_macro_simulates(tmp_path, name):
    path, lat, lon = FILES[name]
    if not os.path.exists(path):
        pytest.skip('climate file {} not found'.format(path))
    _system(str(tmp_path))
    cm.writeClimateMacro(str(tmp_path / 'climate'), {'file_name': path, 'latitude': lat, 'longitude': lon,
                                                      'timezone': -1, 'height': 300}, SETTINGS)
    result = simulateInProcess(str(tmp_path / 'climate.idm'), str(tmp_path / 'work'), PATH_DISTRICTS)
    assert result['ok'], result['errors']
    prn = [os.path.join(r, f) for r, _, fs in os.walk(str(tmp_path)) for f in fs if f.lower() == 'climate.prn']
    assert prn, 'no climate.prn'
    with open(prn[0]) as f:
        head = f.readline().lstrip('#').split()
    data = np.loadtxt(prn[0], comments='#', ndmin=2)
    ida = {h.lower(): data[:, i] for i, h in enumerate(head)}
    weather = gc.weatherFromFile(path, {'lat': lat, 'long': lon, 'long_timezone': -15}, hours=8760)
    ida_kwh = np.trapezoid(ida['iglob'], ida['time']) / 1000
    assert abs(ida_kwh / (weather['IGlob'].sum() / 1000) - 1) < 0.01
