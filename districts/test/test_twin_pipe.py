# coding=utf-8
"""Twin pipes: thermal resistances of pipes in a common casing (utility_functions/pipe_resistances.py), conversion for
the pipe bundle model (utility_functions/twin_pipe.py) and the pipe series of the pipe sizing
(utility_functions/hydraulic_balancing.py). No database, no QGIS."""
import math

import numpy as np
import pytest

from districts.utility_functions.hydraulic_balancing import getNextSmallerPipe, presizePipes
from districts.utility_functions.pipe_resistances import casingResistanceMatrix
from districts.utility_functions.twin_pipe import bundleResistances, twinPipeCoefficients, twinPipeEquivalent, twinPipeResistances

LAMBDA_PUR = 0.027
# isoplus twin pipes, insulation class Standard: DN: (steel outer diameter, casing outer diameter, casing wall, clear pipe distance) [mm]
DRD = {20: (26.9, 125, 3.0, 19), 25: (33.7, 140, 3.0, 19), 32: (42.4, 160, 3.0, 19), 40: (48.3, 160, 3.0, 19), 50: (60.3, 200, 3.2, 20),
       65: (76.1, 225, 3.4, 20), 80: (88.9, 250, 3.6, 25), 100: (114.3, 315, 4.1, 25), 125: (139.7, 400, 4.8, 30), 150: (168.3, 450, 5.2, 40),
       200: (219.1, 560, 6.0, 45)}
# heat transfer coefficient u_DRD [W/(m K)] of the catalogue (chapter 2.3.5): supply and return together, 0.8 m cover,
# thermal conductivity of the ground 1.0 W/(m K)
U_CATALOGUE = {20: 0.1830, 25: 0.1981, 32: 0.2154, 40: 0.2573, 50: 0.2495, 65: 0.2923, 80: 0.3343, 100: 0.3348, 125: 0.3100, 150: 0.3763,
               200: 0.4115}


def geometry(dn):
    """(outer radius of the carrier pipes, radius of the foam body, distance of the pipe centres) [m]"""
    da, dc, casing, hs = DRD[dn]
    return da / 2000.0, dc / 2000.0 - casing / 1000.0, (da + hs) / 1000.0


def side_by_side(dn):
    r_pipe, r_casing, distance = geometry(dn)
    return ((-distance / 2, 0.0, r_pipe), (distance / 2, 0.0, r_pipe)), r_casing


# ---------------- resistance matrix: exact solutions ----------------
@pytest.mark.parametrize('depth', [0.25, 0.5, 2.0])
def test_buried_cylinder(depth):
    """a pipe in the homogeneous ground with the ground surface: acosh(H / r) / (2 pi lambda)"""
    matrix = casingResistanceMatrix([(0.0, 0.0, 0.1)], 0.2, depth, 1.3, 1.3)
    assert matrix[0, 0] == pytest.approx(math.acosh(depth / 0.1) / (2 * math.pi * 1.3), rel=1e-6)


@pytest.mark.parametrize('eccentricity', [0.0, 0.03, 0.06])
def test_eccentric_pipe_in_a_casing_of_uniform_temperature(eccentricity):
    matrix = casingResistanceMatrix([(eccentricity, 0.0, 0.03)], 0.1, 1.0, LAMBDA_PUR, 1.0, ground=False)
    exact = math.acosh((0.1 ** 2 + 0.03 ** 2 - eccentricity ** 2) / (2 * 0.1 * 0.03)) / (2 * math.pi * LAMBDA_PUR)
    assert matrix[0, 0] == pytest.approx(exact, rel=1e-6)


def test_two_pipes_in_a_homogeneous_medium():
    """heat exchange between two pipes far below the surface: acosh(D / r) / (2 pi lambda)"""
    matrix = casingResistanceMatrix([(-0.05, 0.0, 0.03), (0.05, 0.0, 0.03)], 0.2, 500.0, 1.0, 1.0)
    assert matrix[0, 0] - matrix[0, 1] == pytest.approx(math.acosh(0.05 / 0.03) / (2 * math.pi), rel=1e-6)
    assert matrix[0, 0] == pytest.approx(matrix[1, 1])


def test_concentric_pipe_in_a_buried_casing():
    """foam and ground in series; the ground resistance of the casing is between the mean value and the exact
    value of a casing of uniform temperature"""
    matrix = casingResistanceMatrix([(0.0, 0.0, 0.03)], 0.1, 1.0, LAMBDA_PUR, 1.0)
    foam = math.log(0.1 / 0.03) / (2 * math.pi * LAMBDA_PUR)
    assert matrix[0, 0] == pytest.approx(foam + math.log(2 * 1.0 / 0.1) / (2 * math.pi), rel=1e-3)


# ---------------- resistance matrix: twin pipes ----------------
@pytest.mark.parametrize('dn', sorted(DRD))
def test_twin_pipe_matrix_and_wallenten(dn):
    """the heat loss at equal temperatures is the one of the formula of Wallenten, the heat exchange between supply and
    return is somewhat higher (resistance up to 8 % smaller)"""
    pipes, r_casing = side_by_side(dn)
    depth = 0.8 + DRD[dn][1] / 2000.0
    matrix = casingResistanceMatrix(pipes, r_casing, depth, LAMBDA_PUR, 1.0)
    a11, a12 = twinPipeResistances(pipes[0][2], r_casing, pipes[1][0] - pipes[0][0], depth, LAMBDA_PUR, 1.0)
    assert matrix[0, 0] == pytest.approx(matrix[1, 1], rel=1e-6)
    assert matrix[0, 0] + matrix[0, 1] == pytest.approx(a11 + a12, rel=0.005)
    assert 0.92 < (matrix[0, 0] - matrix[0, 1]) / (a11 - a12) <= 1.0


@pytest.mark.parametrize('dn', sorted(DRD))
def test_heat_transfer_coefficient_of_the_catalogue(dn):
    """the heat loss at the mean temperature of supply and return is 0 - 9 % above the catalogue"""
    pipes, r_casing = side_by_side(dn)
    matrix = casingResistanceMatrix(pipes, r_casing, 0.8 + DRD[dn][1] / 2000.0, LAMBDA_PUR, 1.0)
    assert 1.0 < 2.0 / (matrix[0, 0] + matrix[0, 1]) / U_CATALOGUE[dn] < 1.09


def test_pipes_one_above_the_other():
    """the lower pipe has the higher resistance to the surface; the total heat loss at equal temperatures stays the same"""
    pipes, r_casing = side_by_side(50)
    distance = pipes[1][0] - pipes[0][0]
    vertical = casingResistanceMatrix(((0.0, -distance / 2, pipes[0][2]), (0.0, distance / 2, pipes[0][2])), r_casing, 1.0, LAMBDA_PUR, 1.18)
    horizontal = casingResistanceMatrix(pipes, r_casing, 1.0, LAMBDA_PUR, 1.18)
    assert vertical[1, 1] > vertical[0, 0]
    assert np.linalg.inv(vertical).sum() == pytest.approx(np.linalg.inv(horizontal).sum(), rel=0.005)


def test_twin_pipe_heat_loss_plausible():
    """DRD-50 at 1 m depth, supply 80 degC, return 50 degC, ground 10 degC: the losses of both pipes are positive, the
    supply loses more, and the twin pipe loses less than two single pipes DRE-50 Standard (125 mm casing) at 0.25 m distance"""
    pipes, r_casing = side_by_side(50)
    q_supply, q_return = np.linalg.solve(casingResistanceMatrix(pipes, r_casing, 1.0, LAMBDA_PUR, 1.18), [70.0, 40.0])
    assert q_supply > q_return > 0
    single = np.linalg.solve(bundleResistances([pipes[0][2]] * 2, [0.0625 - 0.003] * 2, 0.25, 1.0, LAMBDA_PUR, 1.18), [70.0, 40.0]).sum()
    assert 0.5 * single < q_supply + q_return < single
    assert 10 < q_supply + q_return < 30  # W/m


@pytest.mark.parametrize('pipes, r_casing, depth', [
    (((-0.03, 0.0, 0.03), (0.03, 0.0, 0.03)), 0.059, 1.0),   # pipes touch the casing
    (((-0.02, 0.0, 0.03), (0.02, 0.0, 0.03)), 0.10, 1.0),    # pipes overlap
    (((-0.04, 0.0, 0.03), (0.04, 0.0, 0.03)), 0.10, 0.05),   # casing not covered
])
def test_invalid_geometry(pipes, r_casing, depth):
    with pytest.raises(ValueError):
        casingResistanceMatrix(pipes, r_casing, depth, LAMBDA_PUR, 1.18)
    with pytest.raises(ValueError):
        twinPipeEquivalent(pipes, r_casing, depth, LAMBDA_PUR, 1.18)


# ---------------- conversion for the pipe bundle model ----------------
@pytest.mark.parametrize('dn', [20, 50, 100, 200])
@pytest.mark.parametrize('lambda_soil', [0.8, 1.18, 2.5])
@pytest.mark.parametrize('depth', [0.6, 1.0, 2.0])
def test_bundle_model_reproduces_twin_pipe(dn, lambda_soil, depth):
    """the two separately insulated pipes have the resistance matrix of the twin pipe"""
    pipes, r_casing = side_by_side(dn)
    r_pipe = pipes[0][2]
    thicknesses, dx = twinPipeEquivalent(pipes, r_casing, depth, LAMBDA_PUR, lambda_soil)
    assert thicknesses[0] == pytest.approx(thicknesses[1])
    assert 0 < thicknesses[0] < r_casing - r_pipe  # less insulation than a concentric pipe in the casing
    assert 0 < dx < pipes[1][0] - pipes[0][0]
    model = bundleResistances([r_pipe] * 2, [r_pipe + t for t in thicknesses], dx, depth, LAMBDA_PUR, lambda_soil)
    assert model == pytest.approx(casingResistanceMatrix(pipes, r_casing, depth, LAMBDA_PUR, lambda_soil), rel=1e-6)


def test_bundle_model_reproduces_unequal_pipes():
    """supply DN 50 and return DN 40 one above the other in a 200 mm casing"""
    pipes, r_casing = ((0.0, -0.04, 0.03015), (0.0, 0.035, 0.02415)), 0.0968
    thicknesses, dx = twinPipeEquivalent(pipes, r_casing, 1.0, LAMBDA_PUR, 1.18)
    model = bundleResistances([p[2] for p in pipes], [p[2] + t for p, t in zip(pipes, thicknesses)], dx, 1.0, LAMBDA_PUR, 1.18)
    matrix = casingResistanceMatrix(pipes, r_casing, 1.0, LAMBDA_PUR, 1.18)
    assert matrix[0, 0] != pytest.approx(matrix[1, 1], rel=0.01)
    assert model == pytest.approx(matrix, rel=1e-6)


def test_twin_pipe_in_air_keeps_distance():
    """in air only the insulation is converted: heat loss at equal temperatures for a casing of uniform temperature"""
    pipes, r_casing = side_by_side(50)
    r_pipe = pipes[0][2]
    thicknesses, dx = twinPipeEquivalent(pipes, r_casing, 1.0, LAMBDA_PUR, 1.18, ground=False)
    assert dx == pytest.approx(pipes[1][0] - pipes[0][0])
    matrix = casingResistanceMatrix(pipes, r_casing, 1.0, LAMBDA_PUR, 1.18, ground=False)
    assert math.log((r_pipe + thicknesses[0]) / r_pipe) / (2 * math.pi * LAMBDA_PUR) == pytest.approx(matrix[0, 0] + matrix[0, 1], rel=1e-6)
    # the formula of Wallenten for a casing of uniform temperature (sigma = -1) gives the same within 1 %
    assert math.log((r_pipe + thicknesses[0]) / r_pipe) == pytest.approx(twinPipeCoefficients(r_pipe, r_casing, pipes[1][0] - pipes[0][0], -1.0)[0], rel=0.01)


def test_extreme_soil_conductivity_stays_finite():
    pipes, r_casing = side_by_side(200)
    thicknesses, dx = twinPipeEquivalent(pipes, r_casing, 5.0, 0.005, 5.0)
    assert min(thicknesses) > 0 and dx > 0 and math.isfinite(math.log(dx))


def test_foam_must_insulate_better_than_the_ground():
    pipes, r_casing = side_by_side(50)
    with pytest.raises(ValueError):
        twinPipeEquivalent(pipes, r_casing, 1.0, 1.5, 1.18)


# ---------------- pipe series of the pipe sizing ----------------
def catalog():
    """two series with a construction per pipe and two pipes without a series sharing a construction"""
    pipes = {1: (0.05, 'single', 1), 2: (0.07, 'single', 2), 3: (0.08, 'single', 3), 4: (0.05, 'twin', 4), 5: (0.07, 'twin', 5),
             6: (0.04, None, 9), 7: (0.06, None, 9)}
    return {pid: {'d': d, 'k': 0.000045, 'construction': c, 'series': series or ('construction', c), 'name': str(pid)}
            for pid, (d, series, c) in pipes.items()}


def test_next_smaller_pipe_of_the_series():
    cat = catalog()
    assert getNextSmallerPipe(3, cat) == 2
    assert getNextSmallerPipe(2, cat) == 1
    assert getNextSmallerPipe(1, cat) is None
    assert getNextSmallerPipe(5, cat) == 4  # twin pipes stay twin pipes
    assert getNextSmallerPipe(7, cat) == 6  # without a series: the pipes of the same construction
    assert getNextSmallerPipe(6, cat) is None


def test_presize_within_the_series():
    cat = catalog()
    lines = {1: {'length': 10.0, 'bundle': 1, 'pipes': {1: {'pipe_id': 5, 'mdot': 1.0, 'temp': 70.0, 'mdot_max': 1.0},
                                                         2: {'pipe_id': 5, 'mdot': 1.0, 'temp': 40.0, 'mdot_max': 1.0}}}}
    pipes = presizePipes({1: [1000.0, {1: [50.0, 1.0]}]}, lines, cat, 1e6)
    assert pipes[1] == {1: 4, 2: 4}  # the smallest twin pipe, not the smaller pipe 6 of another series
