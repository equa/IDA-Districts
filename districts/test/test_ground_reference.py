"""2D reference of the ground collector model (change ground-collector-model): no DB, no IDA."""
import numpy as np
import pytest

from districts.utility_functions import ground_collector_geometry as gg
from districts.utility_functions import ground_reference as gr

PIPE = (0.026, 0.032, 0.4)


def test_undisturbed_ground():
    """No source, surface prescribed with the annual wave: the ground follows the analytic wave."""
    soil = gg.SoilProperties()
    geometry = gg.horizontalRing(1.0, 0.5, 2.0, 3.0, *PIPE)
    steps = 3 * 8760
    days = np.arange(1, steps + 1) / 24
    surface = np.array([gg.undisturbedTemperature(soil, 0.0, d) for d in days])
    ref = gr.runReference(geometry, soil, steps, surface_temperature=surface, freezing=False)
    analytic = np.array([gg.undisturbedTemperature(soil, 2.0, d) for d in days[-8760:]])
    assert np.max(np.abs(ref.t_region[-8760:] - analytic)) <= 0.2


@pytest.mark.parametrize('freezing', [False, True])
def test_energy_balance(freezing):
    soil = gg.SoilProperties()
    geometry = gg.horizontalRing(1.0, 0.5, 1.5, 3.0, *PIPE)
    steps = 8760
    days = np.arange(1, steps + 1) / 24
    surface = np.array([gg.undisturbedTemperature(soil, 0.0, d) for d in days])
    q = np.where(np.arange(steps) < 2500, -25.0, 5.0)
    ref = gr.runReference(geometry, soil, steps, surface_temperature=surface, q_wall=q, freezing=freezing)
    stored = ref.energy[-1] - ref.energy[0]
    through = np.sum(ref.q_source + ref.q_surface + ref.q_bottom) * 3600
    assert abs(stored - through) <= 0.005 * np.sum(np.abs(ref.q_source)) * 3600
    if freezing:
        assert ref.ice_region.max() > 0


def test_latent_heat_slows_the_cooling():
    soil = gg.SoilProperties(water_content=0.25)
    dry = gg.SoilProperties(water_content=0.0)
    geometry = gg.horizontalRing(1.0, 0.5, 1.5, 3.0, *PIPE)
    steps = 60 * 24
    surface = np.full(steps, soil.t_mean_surface_c)
    q = np.full(steps, -40.0)
    wet = gr.runReference(geometry, soil, steps, surface_temperature=surface, q_wall=q)
    no_water = gr.runReference(geometry, dry, steps, surface_temperature=surface, q_wall=q)
    assert wet.ice_region.max() > 0
    #the iteration with water stops within its tolerance (0.01 K), the dry run is solved exactly
    assert np.all(wet.t_region >= no_water.t_region - 2 * gr.TOLERANCE_K)
    #the latent heat holds the region near the freezing range: it reaches -0.5 degC far later
    assert np.argmax(wet.t_region < -0.5) > 2 * np.argmax(no_water.t_region < -0.5)


def test_wall_temperature_source():
    soil = gg.SoilProperties(water_content=0.0)
    geometry = gg.horizontalRing(1.0, 0.5, 1.5, 3.0, *PIPE)
    steps = 30 * 24
    ref = gr.runReference(geometry, soil, steps, surface_temperature=np.full(steps, 9.0), t_wall=np.full(steps, 0.0),
                          r_loc=gg.localResistance(geometry, soil), freezing=False)
    assert np.all(ref.q_source < 0)          # the cold wall takes heat from the ground
    assert ref.q_source[0] < ref.q_source[-1]  # strongest at the start, while the ground is still warm


def test_not_converging_raises(monkeypatch):
    monkeypatch.setattr(gr, 'MAX_ITERATIONS', 1)
    monkeypatch.setattr(gr, 'MAX_SPLITS', 0)
    soil = gg.SoilProperties()
    geometry = gg.horizontalRing(1.0, 0.5, 1.5, 3.0, *PIPE)
    with pytest.raises(RuntimeError, match='did not converge'):
        gr.runReference(geometry, soil, 48, surface_temperature=np.full(48, 9.0), q_wall=np.full(48, -200.0))


def test_inputs_checked():
    soil = gg.SoilProperties()
    geometry = gg.horizontalRing(1.0, 0.5, 1.5, 3.0, *PIPE)
    with pytest.raises(ValueError, match='either'):
        gr.runReference(geometry, soil, 2)
    with pytest.raises(ValueError, match='r_loc'):
        gr.runReference(geometry, soil, 2, surface_temperature=[9.0, 9.0], t_wall=[0.0, 0.0])


def test_frequency_response_steady_equals_the_steady_run():
    """The linear system of the frequency fit is the reference: at frequency 0 it gives the steady heat flows."""
    soil = gg.SoilProperties(water_content=0.0)
    surface = gg.SurfaceProperties(epsilon=0.0, h_conv_w7m2k=15.0)
    geometry = gg.horizontalRing(1.0, 0.5, 1.5, 3.0, *PIPE)
    grid = gr.buildGrid(geometry, soil)
    r_loc = gg.localResistance(geometry, soil)
    t_out, t_wall = 9.0, 1.0
    steady = gr.runReference(geometry, soil, 1, weather={'TAir': [t_out], 'IGlob': [0.0], 'TSky': [t_out]}, surface=surface,
                             t_wall=[t_wall], r_loc=r_loc, freezing=False, grid=grid, dt_h=1e9)
    H = gr.frequencyResponse(gr.linearSystem(geometry, soil, surface, r_loc, grid), [0.0])[0].real
    u = np.array([t_out, gg.deepTemperature(soil), t_wall])
    #one step of 1e9 h is steady to about 1e-6
    assert H[0] @ u == pytest.approx(-steady.q_source[0], rel=1e-5)
    assert H[1] @ u == pytest.approx(steady.q_surface[0], rel=1e-5)
    #a faster wall change reaches less deep: the response to the wall grows with the frequency
    Hf = gr.frequencyResponse(gr.linearSystem(geometry, soil, surface, r_loc, grid), [2 * np.pi / (24 * 3600.0), 2 * np.pi / (3600.0)])
    assert abs(Hf[1][0, 2]) > abs(Hf[0][0, 2]) > abs(H[0, 2])
