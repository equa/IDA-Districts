"""Twin pipe (two carrier pipes in one casing) in the pipe bundle model FDpipebundle.

FDpipebundle describes n separately insulated pipes in the ground by the resistance matrix A [K*m/W] (A*q = dT):
    A_ii = R_i + ln(r_o / r_p) / (2 pi lambda_ins) + ln(2 H / r_o) / (2 pi lambda_soil)
    A_ij = ln(sqrt(dx^2 + (H_i + H_j)^2) / sqrt(dx^2 + (H_i - H_j)^2)) / (2 pi lambda_soil)
(r_p outer radius of the carrier pipe, r_o outer radius of the insulation, H depth, dx distance of the pipes).

The resistance matrix of the twin pipe is calculated numerically (utility_functions.pipe_resistances: any position and
diameter of the two pipes in the casing). FDpipebundle gets the same matrix for two pipes at the depth H of the casing
centre with the equivalent insulation radii r_o,i and the equivalent distance dx:
    ln r_o,i = (2 pi A_ii + ln(r_p,i) / lambda_ins - ln(2 H) / lambda_soil) / (1 / lambda_ins - 1 / lambda_soil)
    dx       = 2 H / sqrt(K^2 - 1),  ln K = 2 pi lambda_soil A_12
The equivalent distance is far smaller than the real one (the foam between the pipes insulates much better than the
ground would) and only describes the heat exchange between supply and return; it has no geometric meaning.

twinPipeCoefficients / twinPipeResistances are the formulas of Wallenten (Steady-state heat loss from insulated pipes,
Lund 1991, multipole method of first order) for two equal pipes side by side, kept as a reference for the tests:
    q_s = (T_s - T_ground) / R_s  with T_s = (T_1 + T_2) / 2,   q_a = T_a / R_a  with T_a = (T_1 - T_2) / 2,
    A_11 = (R_s + R_a) / 2,  A_12 = (R_s - R_a) / 2,  R = 1 / (2 pi lambda_ins h)
The numerical matrix has the same R_s (within 0.3 %) and an R_a up to 7 % smaller for the isoplus twin pipes.

With the assumptions of the isoplus catalogue (0.8 m cover, lambda_soil 1.0 W/(m K), lambda_PUR 0.027 W/(m K)) the heat
transfer coefficients 2 / R_s of the twin pipes DRD-20 ... DRD-200 are 2 - 9 % above the values of the catalogue
(chapter 2.3.5); the ones of the single pipes are above the catalogue too (test/test_twin_pipe.py)."""
import functools
import math

import numpy as np

from .pipe_resistances import casingResistanceMatrix

LN_K_MAX = 150.0  # dx^2 must not underflow


def twinPipeCoefficients(r_pipe, r_casing, distance, sigma):
    """(1/h_s without the ground term, 1/h_a) of a twin pipe by Wallenten (dimensionless):
    1/h_s = 2 lambda_ins / lambda_soil ln(2 H / r_c) + ln(r_c^2 / (2 D r_p)) + sigma ln(r_c^4 / (r_c^4 - D^4))
            - (r_p / (2 D) - 2 sigma r_p D^3 / (r_c^4 - D^4))^2 / (1 + (r_p / (2 D))^2 + sigma (2 r_p r_c^2 D / (r_c^4 - D^4))^2)
    1/h_a = ln(2 D / r_p) + sigma ln((r_c^2 + D^2) / (r_c^2 - D^2))
            - (r_p / (2 D) + 2 sigma r_p r_c^2 D / (r_c^4 - D^4))^2
              / (1 - (r_p / (2 D))^2 + 2 sigma r_p^2 r_c^2 (r_c^4 + D^4) / (r_c^4 - D^4)^2)
    (D half distance of the pipe centres, sigma = (lambda_ins - lambda_soil) / (lambda_ins + lambda_soil); the terms of
    1/h_a with (D / 2H)^2 and (r_p / 2H)^2 are left out)."""
    d = distance / 2.0
    x = r_pipe / (2.0 * d)
    c4 = r_casing ** 4 - d ** 4
    hs = (math.log(r_casing ** 2 / (2.0 * d * r_pipe)) + sigma * math.log(r_casing ** 4 / c4)
          - (x - 2.0 * sigma * r_pipe * d ** 3 / c4) ** 2 / (1.0 + x ** 2 + sigma * (2.0 * r_pipe * r_casing ** 2 * d / c4) ** 2))
    ha = (math.log(2.0 * d / r_pipe) + sigma * math.log((r_casing ** 2 + d ** 2) / (r_casing ** 2 - d ** 2))
          - (x + 2.0 * sigma * r_pipe * r_casing ** 2 * d / c4) ** 2
          / (1.0 - x ** 2 + 2.0 * sigma * r_pipe ** 2 * r_casing ** 2 * (r_casing ** 4 + d ** 4) / c4 ** 2))
    return hs, ha


def twinPipeResistances(r_pipe, r_casing, distance, depth, lambda_ins, lambda_soil):
    """(A_11, A_12) [K*m/W] of a buried twin pipe by Wallenten (two equal pipes side by side)."""
    hs, ha = twinPipeCoefficients(r_pipe, r_casing, distance, (lambda_ins - lambda_soil) / (lambda_ins + lambda_soil))
    r_s = (2.0 * lambda_ins / lambda_soil * math.log(2.0 * depth / r_casing) + hs) / (2.0 * math.pi * lambda_ins)
    r_a = ha / (2.0 * math.pi * lambda_ins)
    return (r_s + r_a) / 2.0, (r_s - r_a) / 2.0


def bundleResistances(r_pipes, r_insulations, distance, depth, lambda_ins, lambda_soil):
    """Matrix [[A_11, A_12], [A_12, A_22]] [K*m/W] of two pipes at the same depth as FDpipebundle calculates it (see above)."""
    a12 = math.log(math.sqrt(distance ** 2 + 4.0 * depth ** 2) / distance) / (2.0 * math.pi * lambda_soil)
    a11, a22 = (math.log(r_o / r_p) / (2.0 * math.pi * lambda_ins) + math.log(2.0 * depth / r_o) / (2.0 * math.pi * lambda_soil)
                for r_p, r_o in zip(r_pipes, r_insulations))
    return np.array([[a11, a12], [a12, a22]])


@functools.lru_cache(maxsize=256)
def _equivalent(pipes, r_casing, depth, lambda_ins, lambda_soil, ground):
    if len(pipes) != 2:
        raise ValueError('a twin pipe has two pipes')
    if lambda_ins <= 0:
        raise ValueError('thermal conductivities must be positive')
    radii = [r for _, _, r in pipes]
    if not ground:
        matrix = casingResistanceMatrix(pipes, r_casing, depth, lambda_ins, lambda_soil, ground=False)
        losses = np.linalg.solve(matrix, np.ones(2))  # both pipes 1 K above the casing
        return tuple(float(r * math.exp(2.0 * math.pi * lambda_ins / q) - r) for r, q in zip(radii, losses)), math.hypot(pipes[0][0] - pipes[1][0], pipes[0][1] - pipes[1][1])
    if lambda_ins >= lambda_soil:
        raise ValueError('the thermal conductivity of the foam ({:.4g} W/(m K)) must be below the one of the ground ({:.4g} W/(m K))'.format(lambda_ins, lambda_soil))
    matrix = casingResistanceMatrix(pipes, r_casing, depth, lambda_ins, lambda_soil)
    insulations = [math.exp((2.0 * math.pi * matrix[i, i] + math.log(r) / lambda_ins - math.log(2.0 * depth) / lambda_soil) / (1.0 / lambda_ins - 1.0 / lambda_soil))
                   for i, r in enumerate(radii)]
    ln_k = min(2.0 * math.pi * lambda_soil * matrix[0, 1], LN_K_MAX)
    if ln_k <= 0 or any(r_o <= r for r_o, r in zip(insulations, radii)):
        raise ValueError('the twin pipe cannot be converted to two separately insulated pipes')
    return tuple(float(r_o - r) for r_o, r in zip(insulations, radii)), float(2.0 * depth / math.sqrt(math.expm1(2.0 * ln_k)))


def twinPipeEquivalent(pipes, r_casing, depth, lambda_ins, lambda_soil, ground=True):
    """Returns ((insulation thickness of pipe 1, of pipe 2), distance of the pipes) of two separately insulated pipes at the
    depth of the casing centre which FDpipebundle calculates like the twin pipe.

    pipes: ((x, y, r), (x, y, r)) position of the pipe centres relative to the casing centre (x to the right, y downwards)
    and outer radius of the carrier pipes [m]; r_casing: radius of the foam body; depth: depth of the casing centre;
    ground=False: pipe in air or in a duct (FDpipebundle has no heat exchange between the pipes there: the insulations
    give the heat losses of the twin pipe at equal temperatures of supply and return for a casing of uniform
    temperature, the distance is kept).
    ValueError if the pipes do not fit into the casing, the casing is not covered or the values cannot be converted."""
    return _equivalent(tuple((float(x), float(y), float(r)) for x, y, r in pipes), float(r_casing), float(depth), float(lambda_ins), float(lambda_soil), bool(ground))
