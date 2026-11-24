"""Geometry, presets and parameter contract of the ground collector model (change ground-collector-model): no DB, no IDA."""
import math
import os
import subprocess
import sys

import pytest

from districts.utility_functions import ground_collector_contract as contract
from districts.utility_functions import ground_collector_geometry as gg
from districts.utility_functions import ground_rc as rc

PIPE = (0.026, 0.032, 0.4)


def test_horizontal_ring():
    g = gg.horizontalRing(1.0, 0.5, 1.5, 3.0, *PIPE)
    assert g.loop_length_per_m == pytest.approx(2 * math.pi, rel=1e-9)
    assert g.source_width_m == pytest.approx(1.0)
    assert g.source_depth_m == pytest.approx(1.5)
    assert g.spacing_m == pytest.approx(3.0)
    # one pipe high, widened to one grid cell
    assert g.source_height_m == pytest.approx(gg.MIN_CELL_M)
    assert dict(g.preset_inputs)['pitch_m'] == 0.5


def test_vertical_ring():
    g = gg.verticalRing(1.0, 0.5, 1.2, 3.0, *PIPE)
    assert g.source_height_m == pytest.approx(1.0)
    assert g.source_width_m == pytest.approx(max(0.032, gg.MIN_CELL_M))
    assert g.loop_length_per_m == pytest.approx(2 * math.pi, rel=1e-9)


def test_local_spacing_from_pipe_density():
    """Distance between pipe passes = region extent / pipe per trench meter, not the pitch (design G6)."""
    g = gg.horizontalRing(1.0, 0.5, 1.5, 3.0, *PIPE)
    assert g.local_spacing_m == pytest.approx(1.0 / (2 * math.pi))
    sparse = gg.horizontalRing(1.0, 3.0, 1.5, 3.0, *PIPE)
    assert sparse.local_spacing_m == pytest.approx(1.0 / (math.pi / 3.0))
    assert gg.localResistance(sparse, gg.SoilProperties()) > gg.localResistance(g, gg.SoilProperties())


def test_flat_meander_and_bare_pipe():
    m = gg.flatMeander(2.0, 0.25, 1.5, 3.0, *PIPE)
    assert m.loop_length_per_m == pytest.approx(8.0)
    b = gg.barePipe(1.0, 20.0, 0.09, 0.11, 0.4)
    assert b.pipe_resolved and b.loop_length_per_m == 1.0
    assert b.source_width_m == pytest.approx(0.055 / 0.5902)
    assert gg.localResistance(b, gg.SoilProperties()) == gg.RESOLVED_R_LOC


@pytest.mark.parametrize('call, match', [
    (lambda: gg.verticalRing(2.0, 0.5, 0.8, 3.0, *PIPE), 'source region'),
    (lambda: gg.horizontalRing(4.0, 0.5, 1.5, 3.0, *PIPE), 'source region'),
    (lambda: gg.horizontalRing(-1.0, 0.5, 1.5, 3.0, *PIPE), 'ring_diameter_m'),
    (lambda: gg.barePipe(1.0, 20.0, 0.11, 0.09, 0.4), 'inner diameter'),
])
def test_invalid_inputs(call, match):
    with pytest.raises(ValueError, match=match):
        call()


def _fakeFit():
    return rc.RcFit({k: 1.0 for k in rc.FITTED}, 10.0, {}, 0.0, True, '')


def test_ground_model_takes_the_contract_parameters():
    g = gg.horizontalRing(1.0, 0.5, 1.5, 3.0, *PIPE)
    params = rc.groundParameters(_fakeFit(), gg.SoilProperties(), gg.SurfaceProperties(), g)
    assert sorted(params) == sorted(contract.groundParameterNames())
    contract.checkGroundParameters(params)
    for name in contract.groundParameterNames():
        entry = next(e for c in contract.COMPONENTS for e in contract.entries(c) if e.name == name)
        assert entry.kind == contract.PARAMETER and entry.shape == contract.SCALAR and entry.unit


def test_contract_check_refuses():
    g = gg.horizontalRing(1.0, 0.5, 1.5, 3.0, *PIPE)
    params = rc.groundParameters(_fakeFit(), gg.SoilProperties(), gg.SurfaceProperties(), g)
    with pytest.raises(ValueError, match='missing'):
        contract.checkGroundParameters({k: v for k, v in params.items() if k != 'rTt'})
    with pytest.raises(ValueError, match='unknown'):
        contract.checkGroundParameters({**params, 'rExtra': 1.0})
    with pytest.raises(ValueError, match='finite'):
        contract.checkGroundParameters({**params, 'cLoc': float('nan')})


def test_contract_names_unique_and_fitted_values_in_it():
    for component in contract.COMPONENTS:
        names = [e.name for e in contract.entries(component)]
        assert len(names) == len(set(names))
    collector = {e.name for e in contract.entries('GroundCollector', contract.PARAMETER)}
    assert set(rc.FITTED) <= collector
    assert len(rc.FITTED) == 15
    assert set(rc.START_NAMES) <= collector


def test_plain_python_import():
    """The modules run without QGIS, Qt or the DB (for the Modelica developer)."""
    blocked = ['qgis', 'PyQt5', 'PyQt6', 'psycopg2']
    code = ('import sys\n' + ''.join("sys.modules['{}'] = None\n".format(m) for m in blocked) +
            'from districts.utility_functions import ground_collector_contract, ground_collector_geometry, '
            'ground_climate, ground_reference, ground_rc\n')
    plugins = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    proc = subprocess.run([sys.executable, '-c', code], cwd=plugins, capture_output=True, text=True, timeout=120)
    assert proc.returncode == 0, proc.stderr
