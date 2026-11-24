"""Validation cases of the ground collector model (change ground-collector-model, design G9) for the Python ground
model and the Modelica GroundCollector/GroundSurface: per case case.json (inputs, fitted values, start state, contract
version) and series.csv.gz (one hour per row: wall temperature and weather, the Python ground model's and the 2D
reference's outputs). The weather is a real climate year (KALMAR.PRN of IDA 5.2, sky and radiation as IDA computes
them), run three times; the third year is stored, with the Python model's state at its start as the case's start, so a
case starts settled. Regenerate after a change of the model or the fit (about 15 minutes, the 2D reference with the
surface balance is the slow part):
    python -m districts.test.make_ground_collector_cases [folder] [climate file]
"""
import dataclasses
import gzip
import io
import json
import os
import sys

import numpy as np

from districts.utility_functions import ground_climate as gc
from districts.utility_functions import ground_collector_geometry as gg
from districts.utility_functions import ground_rc as rc
from districts.utility_functions import ground_reference as gr
from districts.utility_functions.ground_collector_contract import CONTRACT_VERSION

CASES_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'data', 'ground_collector_cases')
CLIMATE_FILE = r'C:\Program Files (x86)\IDA52\climate\KALMAR.PRN'
SITE = {'name': 'Kalmar (KALMAR.PRN, IDA 5.2)', 'lat': 56.73, 'long': -16.3, 'long_timezone': -15}
HOURS = 8760
RUN_IN_YEARS = 2
PIPE = (0.026, 0.032, 0.4)
COLUMNS = ('hour', 'T_wall', 'TAir', 'IGlob', 'TSky',
           'model_q_wall', 'model_T_loc', 'model_T_near', 'model_T_surface', 'model_ice',
           'ref_q_wall', 'ref_T_surface', 'ref_ice')


def weather(climate_file=CLIMATE_FILE):
    """One climate year: TAir, IGlob and TSky as IDA's ENVIRONMENT model computes them (columns of IDA's PRN files:
    hour, TAIR, RELHUM, wind direction, wind speed, IDIRNORM, IDIFFHOR)."""
    clim = np.loadtxt(climate_file)[:HOURS]
    return gc.weatherFromClimate(clim[:, 0], clim[:, 1], clim[:, 2], clim[:, 5], clim[:, 6], SITE)


def caseSoil():
    """Default soil with the undisturbed wave of the Kalmar climate (mean of the air plus about 1 K)."""
    return gg.SoilProperties(t_mean_surface_c=7.9, amplitude_surface_k=9.0, phase_day=30.0)


def seasonalWall(hours=HOURS, cold=0.0, warm=8.0):
    """Collector operation: cold Nov-Mar, warm otherwise, one-week ramps between."""
    day = (np.arange(1, hours + 1) / 24) % 365
    ramp = lambda a, b, x: a + (b - a) * np.clip(x, 0, 1)
    return np.where(day < 90, ramp(cold, warm, (day - 83) / 7), np.where(day >= 305, ramp(warm, cold, (day - 305) / 7), warm))


def caseDefinitions():
    soil = caseSoil()
    hour = np.arange(1, HOURS + 1)
    step = np.where((hour >= 30 * 24) & (hour < 90 * 24), soil.t_mean_surface_c - 8.0, soil.t_mean_surface_c)
    ring = lambda: gg.horizontalRing(1.0, 0.5, 1.5, 3.0, *PIPE)
    return {
        'horizontal_ring': (ring(), soil, seasonalWall(), False),
        'vertical_ring': (gg.verticalRing(1.0, 0.5, 1.5, 3.0, *PIPE), soil, seasonalWall(), False),
        'flat_meander': (gg.flatMeander(2.0, 0.3, 1.5, 3.0, *PIPE), soil, seasonalWall(), False),
        'bare_pipe': (gg.barePipe(1.0, 20.0, 0.09, 0.11, 0.4), soil, seasonalWall(), False),
        'horizontal_ring_frozen': (ring(), soil, seasonalWall(cold=-4.0), True),
        'horizontal_ring_wall_step': (ring(), soil, step, False),
    }


def runModel(case, series):
    """The Python ground model's outputs for a case (case.json content) and its inputs."""
    w = {k: series[k] for k in ('TAir', 'IGlob', 'TSky')}
    result = rc.runGroundModel(case['parameters'], len(series['T_wall']), start=case['start'], weather=w,
                               t_wall=series['T_wall'], freezing=case['freezing'])
    return {'model_q_wall': result.q_wall, 'model_T_loc': result.t_loc, 'model_T_near': result.t_near,
            'model_T_surface': result.t_surface, 'model_ice': result.ice}


def buildCase(name, geometry, soil, t_wall, freezing, fit_cache, year):
    surface = gg.SurfaceProperties()
    dry = dataclasses.replace(soil, water_content=0.0)
    use_soil = soil if freezing else dry
    key = repr(geometry)
    if key not in fit_cache:
        fit_cache[key] = rc.fitRc(geometry, dry, surface)
    fit = fit_cache[key]
    params = rc.groundParameters(fit, use_soil, surface, geometry)
    years = RUN_IN_YEARS + 1
    w = {k: np.tile(v, years) for k, v in year.items()}
    walls = np.tile(np.asarray(t_wall, dtype=float), years)
    n = len(walls)
    run_in = RUN_IN_YEARS * HOURS
    model = rc.runGroundModel(params, run_in, start=rc.startState(params, geometry, use_soil, undisturbed=True),
                              weather={k: v[:run_in] for k, v in w.items()}, t_wall=walls[:run_in], freezing=freezing)
    grid = gr.buildGrid(geometry, use_soil)
    ref = gr.runReference(geometry, use_soil, n, weather=w, surface=surface, t_wall=walls,
                          r_loc=gg.localResistance(geometry, use_soil), freezing=freezing, grid=grid,
                          start=gr.undisturbedState(grid, use_soil, 0.0))
    start = model.state
    case = {'name': name, 'contract_version': CONTRACT_VERSION, 'fit_version': rc.FIT_VERSION,
            'preset': geometry.preset, 'preset_inputs': dict(geometry.preset_inputs),
            'geometry': fit.inputs['geometry'], 'soil': dataclasses.asdict(use_soil),
            'surface': dataclasses.asdict(surface), 'site': SITE, 'freezing': freezing, 'parameters': params,
            'start': start, 'run_in_years': RUN_IN_YEARS,
            'fit': {'accepted': fit.accepted, 'errors': fit.errors, 'steady_error': fit.steady_error,
                    'fingerprint': fit.fingerprint},
            'units': {'T': 'degC', 'q_wall': 'W per m of trench, positive = from the pipe into the ground',
                      'IGlob': 'W/m2', 'ice': 'fraction'}}
    last = slice(RUN_IN_YEARS * HOURS, None)
    series = {'hour': np.arange(1, HOURS + 1, dtype=float), 'T_wall': walls[last],
              **{k: v[last] for k, v in w.items()}}
    series.update(runModel(case, series))
    series.update({'ref_q_wall': ref.q_source[last], 'ref_T_surface': ref.t_surface[last],
                   'ref_ice': ref.ice_region[last]})
    return case, series


def writeCase(folder, case, series):
    os.makedirs(folder, exist_ok=True)
    with open(os.path.join(folder, 'case.json'), 'w', encoding='utf-8', newline='\n') as f:
        json.dump(case, f, indent=1, sort_keys=True)
    text = io.StringIO()
    text.write(','.join(COLUMNS) + '\n')
    for i in range(len(series['hour'])):
        text.write(','.join('{:.0f}'.format(series[c][i]) if c == 'hour' else '{:.4f}'.format(series[c][i]) for c in COLUMNS) + '\n')
    #mtime 0: the same content gives the same file
    with gzip.GzipFile(os.path.join(folder, 'series.csv.gz'), 'wb', mtime=0) as f:
        f.write(text.getvalue().encode('ascii'))


def readCase(folder):
    with open(os.path.join(folder, 'case.json'), encoding='utf-8') as f:
        case = json.load(f)
    with gzip.open(os.path.join(folder, 'series.csv.gz'), 'rt', encoding='ascii') as f:
        data = np.genfromtxt(f, delimiter=',', names=True)
    return case, {name: np.asarray(data[name], dtype=float) for name in data.dtype.names or ()}


def main(target=CASES_DIR, climate_file=CLIMATE_FILE):
    year = weather(climate_file)
    fit_cache = {}
    for name, (geometry, soil, t_wall, freezing) in caseDefinitions().items():
        case, series = buildCase(name, geometry, soil, t_wall, freezing, fit_cache, year)
        writeCase(os.path.join(target, name), case, series)
        print('{}: written'.format(name), flush=True)


if __name__ == '__main__':
    main(*sys.argv[1:])
