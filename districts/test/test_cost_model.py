# coding=utf-8
"""Cost model of the cost optimization (OpenSpec change cost-optimization) on a synthetic network without a database:
plant -> line 1 -> junction -> line 2 -> customer 1 (1.5 kg/s), line 3 -> customer 2 (0.5 kg/s)."""
import numpy as np
import pytest

from districts.utility_functions.cost_model import CostModel, nextPipe, pressureLoss, upstreamPaths
from districts.utility_functions.hydraulic_balancing import specificPressureLoss

CATALOG = {pid: {'d': d, 'k': 2e-5, 'construction': pid, 'series': 'S', 'name': 'DN{}'.format(dn), 'dn': dn,
                 'costs': cost, 'lifetime_a': 40, 'maintenance_pct': 1.0}
           for pid, (dn, d, cost) in {1: (40, 0.0419, 70), 2: (50, 0.0539, 85), 3: (65, 0.0697, 110), 4: (80, 0.0825, 130)}.items()}
LAYERS = {pid: [(0.003, 55.2), (0.03, 0.027), (0.003, 0.4)] for pid in CATALOG}
GRAPH = {1: (('ep', 1), ('j', 1)), 2: (('j', 1), ('c', 1)), 3: (('j', 1), ('c', 2))}
FLOWS = {1: 2.0, 2: 1.5, 3: 0.5}


def scenario():
    groups = {g: {'cost_group': g, 'start_price': 0.25 if g == 'electricity' else None, 'escalation_pct': 0.0}
              for g in ('electricity', 'heat', 'cold', 'maintenance', 'investment')}
    return {'scenario': {'interest_pct': 0.0, 'period_a': 40, 'residual_value': False, 'default_surface': 'paved'},
            'groups': groups, 'levels': {}, 'curves': {'heat': [(70, 0.10)], 'cold': [(6, 0.06)]}, 'trench': {'paved': (155, 9.4)}}


def model(pipes=3, decentral=None, p_plant=None, p_max=None, eta=0.5):
    n = 2
    lines = {lid: {'length': 100.0, 'pipes': {1: pipes, 2: pipes}, 'surface': {'paved': 100.0}} for lid in GRAPH}
    mdot = {}
    for lid, flow in FLOWS.items():
        mdot[(lid, 1)] = np.full(n, flow)
        mdot[(lid, 2)] = np.full(n, -flow)
    temp = {(lid, seq): np.full(n, 70.0 if seq == 1 else 40.0) for lid in GRAPH for seq in (1, 2)}
    m = CostModel(scenario(), CATALOG, LAYERS, lines, [(1, 2)], [4380, 4380], mdot, temp, GRAPH, [1, 2],
                  central=np.ones(n), decentral=decentral, v_plant={(1, 2): np.full(n, 2.0 / 990)},
                  v_customer={1: np.full(n, 1.5 / 990), 2: np.full(n, 0.5 / 990)}, p_plant=p_plant,
                  t_amb={2: np.full(n, 10.0)}, t_supply={'heat': np.full(n, 70.0), 'cold': np.zeros(n)}, modes={1: 'heat', 2: 'heat'},
                  p_max=p_max)
    # central power so that eta is the given value
    if m.central is not None and eta:
        hydraulic = m.v_plant[(1, 2)] * m.heads((1, 2))
        m.central = hydraulic / eta
        m._calibrate()
    return m


def test_pressure_loss_against_colebrook():
    for mdot in (0.2, 1.5, 6.0):
        colebrook = specificPressureLoss(mdot, 0.0697, 2e-5, 60)[0]
        assert float(pressureLoss([mdot], 0.0697, 2e-5)[0]) == pytest.approx(colebrook, rel=0.06)


def test_next_pipe_and_paths():
    assert (nextPipe(3, CATALOG, True), nextPipe(3, CATALOG, False), nextPipe(4, CATALOG, True)) == (4, 2, None)
    paths = upstreamPaths(GRAPH, {1: 1, 2: 1, 3: 1}, [1, 2])
    assert paths == {1: {1, 2}, 2: {1, 3}}


def test_calibration():
    m = model()
    assert m.eta_central == pytest.approx(0.5)


def test_larger_pipe_on_the_critical_path_saves_pump_energy():
    m = model()
    on = m.change(2, larger=True)
    assert on['yearly']['pump_energy'] < 0 and on['split']['investment'] > 0
    assert on['dnpv'] == pytest.approx(sum(on['split'].values()))


def test_larger_pipe_off_the_critical_path_saves_nothing():
    m = model()
    off = m.change(3, larger=True)
    assert off['yearly']['pump_energy'] == pytest.approx(0.0, abs=1e-9)
    assert off['dnpv'] > 0


def test_decentral_pump():
    m = model(decentral={2: np.full(2, 50.0)})
    assert m.eta_decentral[2] > 0
    change = m.change(3, larger=False)
    assert change['yearly']['pump_energy'] > 0  # the pump of customer 2 lifts more
    p, _ = m.pumpPowerChange(2, (1, 2), {1: 2, 2: 2})
    # line 2 is not on the path of customer 2: only the central pumps (for customer 1) change
    central_only = model().pumpPowerChange(2, (1, 2), {1: 2, 2: 2})[0]
    assert np.allclose(p, central_only)


def test_pressure_limit():
    m = model(p_plant=np.full(2, 15.95e5), p_max={pid: 16 for pid in CATALOG})
    assert m.change(2, larger=False)['reason'] == 'p_max'
    assert m.change(2, larger=True)['reason'] is None


def test_peak_limit_of_smaller_pipes():
    m = model(pipes=2)
    assert m.change(1, larger=False)['reason'] == 'peak'  # 2 kg/s in DN40


def test_step_changes_one_size_at_most():
    m = model(pipes=2)
    chosen, rejected = m.step()
    assert chosen and all(set(c['pipes'].values()) <= {nextPipe(2, CATALOG, True), nextPipe(2, CATALOG, False)} for c in chosen.values())
    assert all(c['dnpv'] < 0 for c in chosen.values())


def test_protected_line():
    m = model()
    m.lines[2]['protected'] = True
    assert m.change(2, larger=True) == {'reason': 'protected'}
