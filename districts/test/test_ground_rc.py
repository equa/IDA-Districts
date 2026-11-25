"""RC fit, Python ground model and start state of the ground collector model (change ground-collector-model, design
G5-G9): validated against the 2D reference. The surface here is a heat transfer to the air with sun but without the
long-wave term, so the reference stays linear and fast; the full surface balance is checked with the validation cases
(test_ground_collector_cases.py). No DB, no IDA; about two minutes."""
import dataclasses
import math

import numpy as np
import pytest

from districts.utility_functions import ground_collector_geometry as gg
from districts.utility_functions import ground_rc as rc
from districts.utility_functions import ground_reference as gr

PIPE = (0.026, 0.032, 0.4)
SOIL = gg.SoilProperties()
DRY = dataclasses.replace(SOIL, water_content=0.0)
#heat transfer of convection and radiation together, no long-wave term: the reference stays linear
SURFACE = gg.SurfaceProperties(epsilon=0.0, h_conv_w7m2k=15.0)
PRESETS = {
    'horizontal_ring': lambda: gg.horizontalRing(1.0, 0.5, 1.5, 3.0, *PIPE),
    'vertical_ring': lambda: gg.verticalRing(1.0, 0.5, 1.5, 3.0, *PIPE),
    'flat_meander': lambda: gg.flatMeander(2.0, 0.3, 1.5, 3.0, *PIPE),
    'bare_pipe': lambda: gg.barePipe(1.0, 20.0, 0.09, 0.11, 0.4),
}
#validation limits (design G9): heat into the fluid against the reference, RMS relative to its mean; measured with
#six nodes: annual -0.6 to +0.6 %, winter -5.8 to +2.4 % (meander), RMS seasonal up to 4 %, daily cycling up to 36 %
#(bare pipe), frozen winter -3.2 % (ring)
ANNUAL_LIMIT = 0.03
WINTER_LIMIT = 0.07
SEASONAL_RMS_LIMIT = 0.10
DAILY_RMS_LIMIT = 0.40
FROZEN_WINTER_LIMIT = 0.07


@pytest.fixture(scope='module')
def fits():
    return {name: (make(), rc.fitRc(make(), DRY, SURFACE)) for name, make in PRESETS.items()}


def _days(years):
    days = np.arange(1, years * 8760 + 1) / 24
    return days, days % 365, (days * 24) % 24


def _weather(days):
    """Air with annual and daily wave, sun in the day with a summer maximum (about 110 W/m2 on average)."""
    hod = (days * 24) % 24
    t_air = 8.0 - 9.0 * np.cos(2 * math.pi * (days - 20) / 365) - 3.0 * np.cos(2 * math.pi * (hod - 3) / 24)
    sun = np.clip(np.sin(math.pi * (hod - 6) / 12), 0, None) * (300 - 200 * np.cos(2 * math.pi * (days - 10) / 365))
    return {'TAir': t_air, 'IGlob': sun, 'TSky': t_air - 5.0, 'albedo': SURFACE.albedo}


def test_presets_accepted(fits):
    for name, (_, fit) in fits.items():
        assert fit.accepted, (name, fit.errors, fit.steady_error)
        assert all(v > 0 for v in fit.values.values()), name
        assert set(fit.values) == set(rc.FITTED)


def test_fit_is_robust():
    """A slightly different soil gives nearly the same behaviour (the time-domain fit scattered by 26 % in winter)."""
    geometry = PRESETS['horizontal_ring']()
    a = rc.fitRc(geometry, DRY, SURFACE)
    b = rc.fitRc(geometry, dataclasses.replace(DRY, t_mean_surface_c=DRY.t_mean_surface_c + 0.3), SURFACE)
    omegas = np.concatenate([[0.0], 2 * math.pi / (rc.PERIODS_H * 3600.0)])
    fixed = {'rhoCLayer': SURFACE.rho_c_j7m3k, 'dLayer': SURFACE.d_layer_m, 'spacing': geometry.spacing_m}
    ha = rc._response(dict(a.values, **fixed), 15.0, omegas)[:, 2]
    hb = rc._response(dict(b.values, **fixed), 15.0, omegas)[:, 2]
    assert np.max(np.abs(ha - hb)) / np.max(np.abs(ha)) < 0.02


def test_not_accepted_is_returned():
    geometry = PRESETS['horizontal_ring']()
    fit = rc.fitRc(geometry, DRY, SURFACE, rc.FitSettings(error_limit=1e-6))
    assert not fit.accepted
    assert fit.errors['wall'] > 0


def test_fingerprint():
    a = PRESETS['horizontal_ring']()
    settings = rc.FitSettings()
    b = gg.horizontalRing(1.0, 0.5, 1.5, 3.5, *PIPE)
    other_surface = dataclasses.replace(SURFACE, h_conv_w7m2k=20.0)
    assert rc.fingerprint(a, DRY, SURFACE, settings) == rc.fingerprint(PRESETS['horizontal_ring'](), DRY, SURFACE, settings)
    assert rc.fingerprint(a, DRY, SURFACE, settings) != rc.fingerprint(b, DRY, SURFACE, settings)
    assert rc.fingerprint(a, DRY, SURFACE, settings) != rc.fingerprint(a, SOIL, SURFACE, settings)
    assert rc.fingerprint(a, DRY, SURFACE, settings) != rc.fingerprint(a, DRY, other_surface, settings)


def test_linear_surface():
    full = gg.SurfaceProperties()
    lin = rc.linearSurface(full, SOIL)
    assert lin.epsilon == 0.0
    assert lin.h_conv_w7m2k == pytest.approx(full.h_conv_w7m2k + 4 * full.epsilon * 5.670374419e-8 * (SOIL.t_mean_surface_c + 273.15) ** 3)


@pytest.mark.parametrize('name', list(PRESETS))
def test_ground_model_against_the_reference(fits, name):
    """Three years with the surface balance: annual heat and hourly heat flow into the fluid of the third year."""
    geometry, fit = fits[name]
    params = rc.groundParameters(fit, DRY, SURFACE, geometry)
    days, doy, hod = _days(3)
    n = len(days)
    weather = _weather(days)
    ramp = lambda a, b, x: a + (b - a) * np.clip(x, 0, 1)
    seasonal = np.where(doy < 90, ramp(0, 8, (doy - 83) / 7), np.where(doy >= 305, ramp(8, 0, (doy - 305) / 7), 8.0))
    daily = np.interp(hod, [0, 5, 7, 21, 23, 24], [8, 8, 0, 0, 8, 8])
    grid = gr.buildGrid(geometry, DRY)
    last = slice(2 * 8760, None)
    winter = 2 * 8760 + np.flatnonzero((doy[last] < 90) | (doy[last] >= 305))
    for label, t_wall, rms_limit in (('seasonal', seasonal, SEASONAL_RMS_LIMIT), ('daily', daily, DAILY_RMS_LIMIT)):
        ref = gr.runReference(geometry, DRY, n, weather=weather, surface=SURFACE, t_wall=t_wall,
                              r_loc=gg.localResistance(geometry, DRY), freezing=False, grid=grid,
                              start=gr.undisturbedState(grid, DRY, 0.0))
        model = rc.runGroundModel(params, n, start=rc.startState(params, geometry, DRY, undisturbed=True),
                                  weather=weather, t_wall=t_wall, freezing=False)
        q_ref, q = ref.q_source[last], model.q_wall[last]
        mean = np.mean(np.abs(q_ref))
        assert abs(q.sum() / q_ref.sum() - 1) <= ANNUAL_LIMIT, (name, label, q.sum() / q_ref.sum())
        assert abs(model.q_wall[winter].sum() / ref.q_source[winter].sum() - 1) <= WINTER_LIMIT, (name, label)
        assert np.sqrt(np.mean((q - q_ref) ** 2)) <= rms_limit * mean, (name, label)


def test_frozen_winter(fits):
    """-4 degC at the wall Nov-Mar: the coil region freezes; the winter heat of the second year."""
    geometry, fit = fits['horizontal_ring']
    params = rc.groundParameters(fit, SOIL, SURFACE, geometry)
    days, doy, _ = _days(2)
    n = len(days)
    weather = _weather(days)
    t_wall = np.where((doy < 90) | (doy >= 305), -4.0, 8.0)
    winter = 8760 + np.flatnonzero((doy[8760:] < 90) | (doy[8760:] >= 305))
    grid = gr.buildGrid(geometry, SOIL)
    ref = gr.runReference(geometry, SOIL, n, weather=weather, surface=SURFACE, t_wall=t_wall,
                          r_loc=gg.localResistance(geometry, SOIL), freezing=True, grid=grid,
                          start=gr.undisturbedState(grid, SOIL, 0.0))
    model = rc.runGroundModel(params, n, start=rc.startState(params, geometry, SOIL, undisturbed=True),
                              weather=weather, t_wall=t_wall, freezing=True)
    #the model's ice is averaged over all freezing nodes, the reference's over the coil region only
    assert ref.ice_region.max() > 0.5 and model.ice.max() > 0.1
    assert abs(model.q_wall[winter].sum() / ref.q_source[winter].sum() - 1) <= FROZEN_WINTER_LIMIT


def test_start_state(fits):
    geometry, fit = fits['horizontal_ring']
    params = rc.groundParameters(fit, SOIL, SURFACE, geometry)
    days, _, _ = _days(1)
    weather = _weather(days)
    a = rc.startState(params, geometry, SOIL, weather, 2.0, years=2)
    b = rc.startState(params, geometry, SOIL, weather, 2.0, years=2)
    assert a == b
    undisturbed = rc.startState(params, geometry, SOIL, undisturbed=True)
    assert set(a) == set(undisturbed) == set(rc.START_NAMES) | {'TStartSurface'}
    assert a['TStartLoc'] < undisturbed['TStartLoc']
    with pytest.raises(ValueError, match='mean fluid temperature'):
        rc.startState(params, geometry, SOIL, weather)


def test_ground_model_inputs_checked(fits):
    geometry, fit = fits['horizontal_ring']
    params = rc.groundParameters(fit, SOIL, SURFACE, geometry)
    start = rc.startState(params, geometry, SOIL, undisturbed=True)
    with pytest.raises(ValueError, match='surface_temperature or weather'):
        rc.runGroundModel(params, 2, start=start, q_wall=[0.0, 0.0])
    with pytest.raises(ValueError, match='q_wall or t_wall'):
        rc.runGroundModel(params, 2, start=start, surface_temperature=[9.0, 9.0])
    with pytest.raises(ValueError, match='missing'):
        rc.runGroundModel({k: v for k, v in params.items() if k != 'cFar2'}, 2, start=start,
                          surface_temperature=[9.0, 9.0], q_wall=[0.0, 0.0])
    with pytest.raises(ValueError, match=r"GroundSurface inputs \['albedo'\]"):
        rc.runGroundModel(params, 2, start=start, weather={'TAir': [9.0, 9.0], 'IGlob': [0.0, 0.0], 'TSky': [4.0, 4.0]},
                          q_wall=[0.0, 0.0])
