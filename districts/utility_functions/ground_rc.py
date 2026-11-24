#RC ground model of a collector section, its fit to the 2D reference, and the start state (change
#ground-collector-model, design G5-G9); the equations are those of the Modelica GroundCollector/GroundSurface
#(ground part, contract ground_collector_contract.py); plain Python with numpy/scipy
import hashlib
import json
import math
from dataclasses import asdict, dataclass, field, replace

import numpy as np
from scipy.optimize import least_squares

from .ground_climate import ABS_ZERO, SIGMA
from .ground_collector_contract import checkGroundParameters
from .ground_collector_geometry import (LATENT_HEAT_J7KG, RHO_WATER_KG7M3, deepTemperature, localResistance,
                                        nodeDepths, undisturbedTemperature, wallResistance)
from .ground_reference import (DAMPING, MAX_ITERATIONS, TOLERANCE_K, UNDAMPED_ITERATIONS, buildGrid,
                               frequencyResponse, linearSystem)

#raised whenever the reference or the fit change their results: invalidates stored fits
FIT_VERSION = 5

#ground nodes (design G5); the surface node follows them
TOP, LOC, NEAR, FAR, TOP2, FAR2 = 0, 1, 2, 3, 4, 5
N_GROUND = 6
SURF = N_GROUND
CAPACITIES = ('cTop', 'cLoc', 'cNear', 'cFar', 'cTop2', 'cFar2')
#(node, node, resistance); 'SURF' is the surface port, 'DEEP' the lower boundary, 'WALL' the pipe wall
EDGES = (('SURF', TOP, 'rSt'), (TOP, TOP2, 'rTt'), (TOP2, NEAR, 'rTn'), (TOP, FAR, 'rTf'), (LOC, NEAR, 'rLn'),
         (NEAR, FAR, 'rNf'), (FAR, FAR2, 'rFf'), (FAR2, 'DEEP', 'rFd'), (LOC, 'WALL', 'rLoc'))
FITTED = CAPACITIES + tuple(e[2] for e in EDGES)
#the soil that freezes in the 2D reference lies in these nodes; with loc and near alone the winter heat was 16-29 % low
LATENT_NODES = (LOC, NEAR, TOP2, FAR)
START_NAMES = ('TStartTop', 'TStartLoc', 'TStartNear', 'TStartFar', 'TStartTop2', 'TStartFar2')

#periods of the frequency fit [h]; the steady state is added as period infinity
PERIODS_H = np.geomspace(2.0, 2 * 8760.0, 24)
#start scalings of cNear and cLoc: the fast and the slow nodes can swap roles, so the fit keeps the best of these
START_SCALES = (0.1, 1.0, 10.0)
#starting region around a resolved pipe: its own region is the pipe, far smaller than the soil the nodes stand for
RESOLVED_GUESS_REGION_M = 0.4


@dataclass(frozen=True)
class FitSettings:
    regularization: float = 0.01        # pull of the log values toward the geometric guess
    steady_weight: float = 10.0
    band_weight: float = 3.0            # periods from 3 days to a year: where the winter heat is decided
    band_h: tuple = (72.0, 8760.0)
    #catches a failed fit, not the accuracy (that is the validation's)
    error_limit: float = 0.15           # largest error of a heat-into-fluid response / its largest value, all periods
    steady_limit: float = 0.01


@dataclass
class RcFit:
    values: dict                        # the fifteen fitted values, contract names
    t_deep: float
    errors: dict                        # largest relative error per response ('outside', 'wall')
    steady_error: float                 # relative error of the steady heat flow into the fluid
    accepted: bool
    fingerprint: str
    fit_version: int = FIT_VERSION
    inputs: dict = field(default_factory=dict)


def fingerprint(geometry, soil, surface, settings):
    data = json.dumps({'geometry': asdict(geometry), 'soil': asdict(soil), 'surface': asdict(surface),
                       'settings': asdict(settings), 'fit_version': FIT_VERSION}, sort_keys=True, default=str)
    return hashlib.md5(data.encode('utf-8'), usedforsecurity=False).hexdigest()


def linearSurface(surface, soil):
    """The surface of the fit: convection plus radiation linearized at the mean surface temperature, no sun
    (G7: the fit sees the kind of boundary the simulation has, a heat transfer, not a prescribed temperature)."""
    t_mean = soil.t_mean_surface_c - ABS_ZERO
    h_total = surface.h_conv_w7m2k + 4 * surface.epsilon * SIGMA * t_mean ** 3
    return replace(surface, h_conv_w7m2k=h_total, epsilon=0.0)


def groundParameters(fit, soil, surface, geometry):
    """The ground and surface parameters of the contract (names of GroundCollector and GroundSurface)."""
    params = dict(fit.values)
    params.update(TDeep=fit.t_deep, rhoCSoil=soil.rho_c_j7m3k, waterContent=soil.water_content,
                  TFreezeSoil=soil.t_freeze_c, freezeRange=soil.freeze_range_k,
                  lambdaFrozenRatio=soil.lambda_frozen_ratio, albedo=surface.albedo, epsilon=surface.epsilon,
                  hConv=surface.h_conv_w7m2k, dLayer=surface.d_layer_m, rhoCLayer=surface.rho_c_j7m3k,
                  spacing=geometry.spacing_m)
    return {k: float(v) for k, v in params.items()}


def _network(p, ice=None, ratio=1.0, r_series=0.0, wall=True, h_surface=0.0):
    """Capacities c, conductance matrix K and input matrix B of the six ground nodes and the surface node, for the
    inputs (T_outside, T_deep, T_wall, q into loc). h_surface [W/(m2 K)]: heat transfer of the surface node to
    T_outside (0 when the surface balance is added by the caller). With wall=False the loc node gets q instead."""
    ice = np.zeros(N_GROUND + 1) if ice is None else ice
    scale = lambda i, j: 1 + (ratio - 1) * (ice[i] + ice[j]) / 2
    size = N_GROUND + 1
    k_mat = np.zeros((size, size))
    b_mat = np.zeros((size, 4))
    g_w = g_st = 0.0
    for a, b, r in EDGES:
        i = SURF if a == 'SURF' else int(a)
        if b == 'DEEP':
            g = 1 / p[r]
            k_mat[i, i] += g
            b_mat[i, 1] += g
        elif b == 'WALL':
            if wall:
                g_w = 1 / (p[r] / (1 + (ratio - 1) * ice[LOC]) + r_series)
                k_mat[i, i] += g_w
                b_mat[i, 2] += g_w
        else:
            j = int(b)
            g = (1 / p[r]) * (scale(i, j) if i != SURF else 1.0)
            if i == SURF:
                g_st = g
            k_mat[i, i] += g
            k_mat[j, j] += g
            k_mat[i, j] -= g
            k_mat[j, i] -= g
    g_h = h_surface * p['spacing']
    k_mat[SURF, SURF] += g_h
    b_mat[SURF, 0] = g_h
    b_mat[LOC, 3] = 1.0
    c = np.array([p[k] for k in CAPACITIES] + [p['rhoCLayer'] * p['dLayer'] * p['spacing']])
    return c, k_mat, b_mat, g_w, g_st


def _response(p, h_surface, omegas, surface=False):
    """Heat into the fluid per input (outside, deep, wall) at the angular frequencies omegas: H[k, input]; with
    surface=True also the heat from the surface into the ground: H[k, output, input]."""
    c, k_mat, b_mat, g_w, g_st = _network(p, h_surface=h_surface)
    b3 = b_mat[:, :3]
    out = np.zeros((2, N_GROUND + 1))
    out[0, LOC] = g_w
    out[1, SURF], out[1, TOP] = g_st, -g_st
    d = np.array([[0.0, 0.0, -g_w], [0.0, 0.0, 0.0]])
    h = np.array([out @ np.linalg.solve(k_mat + np.diag(1j * w * c), b3) + d for w in omegas])
    return h if surface else h[:, 0, :]


def _initialGuess(geometry, soil):
    lam, rc = soil.lambda_w7mk, soil.rho_c_j7m3k
    s, deep = geometry.spacing_m, soil.depth_deep_m
    if geometry.pipe_resolved:
        w = h = RESOLVED_GUESS_REGION_M
    else:
        w, h = geometry.source_width_m, geometry.source_height_m
    zt, zb = max(geometry.source_depth_m - h / 2, 0.1), geometry.source_depth_m + h / 2
    we = max(w, 0.3)
    return {
        'cTop': rc * s * zt / 2, 'cTop2': rc * s * zt / 2,
        'cLoc': rc * max(w, 0.1) * max(h, 0.1) * 2,
        'cNear': rc * (w + 0.5) * (h + 0.5),
        'cFar': rc * s * (deep - zb) / 4, 'cFar2': rc * s * (deep - zb) / 2,
        'rSt': zt / 2 / (lam * s), 'rTt': zt / 2 / (lam * s),
        'rLn': 0.05,
        'rTn': (zt / 2 + 0.25) / (lam * we),
        'rTf': (zt + (deep - zb) / 2) / (lam * s),
        'rNf': 0.5 / (lam * 2 * we),
        'rFf': (deep - zb) / 3 / (lam * s), 'rFd': (deep - zb) / 3 / (lam * s),
        'rLoc': max(localResistance(geometry, soil), 0.02),
    }


def fitRc(geometry, soil, surface, settings=None):
    """Fit the fifteen RC values in the frequency domain (design G7): the heat into the fluid as a response to the
    outside and to the wall temperature, over periods from 2 hours to 2 years and the steady state, matched to the
    unfrozen 2D reference with the given surface linearized; a weak pull toward the geometric guess makes the
    solution unique. Fits outside the limits are returned flagged."""
    settings = settings or FitSettings()
    lin = linearSurface(surface, soil)
    grid = buildGrid(geometry, soil)
    periods = np.concatenate([[np.inf], PERIODS_H])
    omegas = np.concatenate([[0.0], 2 * math.pi / (PERIODS_H * 3600.0)])
    h_full = frequencyResponse(linearSystem(geometry, soil, lin, localResistance(geometry, soil), grid), omegas)
    h_ref = h_full[:, 0, :]
    deep_steady = h_full[0, :, 1].real
    deep_scale = max(float(np.abs(deep_steady).max()), 1e-12)
    weight = np.where((periods >= settings.band_h[0]) & (periods <= settings.band_h[1]), settings.band_weight, 1.0)
    weight[0] = settings.steady_weight
    scale = {i: max(float(np.abs(h_ref[:, i]).max()), 1e-12) for i in range(3)}
    fixed = {'rhoCLayer': surface.rho_c_j7m3k, 'dLayer': surface.d_layer_m, 'spacing': geometry.spacing_m}
    guess = _initialGuess(geometry, soil)
    x0 = np.log([guess[k] for k in FITTED])

    def residuals(x):
        hh = _response(dict(zip(FITTED, np.exp(x)), **fixed), lin.h_conv_w7m2k, omegas, surface=True)
        h = hh[:, 0, :]
        res = []
        for i in (0, 2):
            e = (h[:, i] - h_ref[:, i]) / scale[i] * weight
            res += [e.real, e.imag]
        #the deep boundary only enters the steady state; how its heat splits between the fluid and the surface pins
        #the long periods (without the surface part the meander's 2-year response was 6 % weak, winter 10 % low)
        res.append((hh[0, :, 1].real - deep_steady) / deep_scale * settings.steady_weight)
        res.append(settings.regularization * (x - x0))
        return np.concatenate(res)

    result = None
    for near_scale in START_SCALES:
        for loc_scale in START_SCALES:
            start = x0.copy()
            start[FITTED.index('cNear')] += math.log(near_scale)
            start[FITTED.index('cLoc')] += math.log(loc_scale)
            candidate = least_squares(residuals, start, bounds=(x0 - 8, x0 + 8), xtol=1e-10, ftol=1e-10, max_nfev=3000)
            if result is None or candidate.cost < result.cost:
                result = candidate
    assert result is not None
    values = {k: float(v) for k, v in zip(FITTED, np.exp(result.x))}
    h = _response(dict(values, **fixed), lin.h_conv_w7m2k, omegas)
    #relative to the largest response of the pair: the outside barely reaches the coil at short periods, an error
    #relative to that near-zero response would mean nothing
    errors = {name: float(np.max(np.abs(h[:, i] - h_ref[:, i])) / scale[i]) for name, i in (('outside', 0), ('wall', 2))}
    steady_error = float(abs(h[0, 2] - h_ref[0, 2]) / abs(h_ref[0, 2]))
    accepted = max(errors.values()) <= settings.error_limit and steady_error <= settings.steady_limit
    return RcFit(values, deepTemperature(soil), errors, steady_error, accepted,
                 fingerprint(geometry, soil, surface, settings),
                 inputs={'geometry': asdict(geometry), 'soil': asdict(soil), 'surface': asdict(surface),
                         'settings': asdict(settings)})


@dataclass
class GroundResult:
    t_top: np.ndarray
    t_loc: np.ndarray
    t_near: np.ndarray
    t_far: np.ndarray
    t_surface: np.ndarray
    q_surface: np.ndarray       # W/m trench from the surface into the ground
    q_wall: np.ndarray          # W/m trench from the pipe into the ground (negative = extraction)
    ice: np.ndarray             # ice fraction of the freezing nodes, weighted by their latent volumes
    state: dict = field(default_factory=dict)   # start values of the state after the last step


def runGroundModel(params, steps, *, start, surface_temperature=None, weather=None, q_wall=None, t_wall=None,
                   r_series=0.0, freezing=True, dt_h=1.0):
    """One section of the ground model over steps time steps (inputs per step, value at its end).
    params: ground parameters of the contract; start: the six TStart values (and TStartSurface with weather).
    The surface: weather (dict TAir, IGlob, TSky) through the GroundSurface balance, or surface_temperature at the
    surface node. The source: q_wall [W/m trench into the ground] or t_wall [degC] behind rLoc + r_series [K m/W]."""
    checkGroundParameters(params)
    p = params
    if (surface_temperature is None) == (weather is None):
        raise ValueError('give either surface_temperature or weather')
    if (q_wall is None) == (t_wall is None):
        raise ValueError('give either q_wall or t_wall')
    dt = dt_h * 3600.0
    use_wall = t_wall is not None
    use_surface = weather is not None
    c, k0, _, _, _ = _network(p, r_series=r_series, wall=use_wall)
    n_sub = int(min(max(math.ceil(dt / float(np.min(c[:N_GROUND] / np.diag(k0)[:N_GROUND]))), 1), 240))
    h = dt / n_sub
    size = N_GROUND + 1
    freeze = freezing and p['waterContent'] > 0
    per_kelvin = p['waterContent'] * RHO_WATER_KG7M3 * LATENT_HEAT_J7KG / p['rhoCSoil']
    latent = np.zeros(size)
    if freeze:
        latent[list(LATENT_NODES)] = c[list(LATENT_NODES)] * per_kelvin
    t_low, width = p['TFreezeSoil'] - p['freezeRange'], p['freezeRange']
    f_tolerance = TOLERANCE_K / 10 * float(np.min(c[list(LATENT_NODES)])) / max(latent.max(), 1.0)
    ratio = p['lambdaFrozenRatio']
    x = np.array([start[name] for name in START_NAMES]
                 + [start.get('TStartSurface', start['TStartTop']) if use_surface else 0.0], dtype=float)
    liquid = np.ones(size)
    if freeze:
        liquid = np.where(latent > 0, np.clip((x - t_low) / width, 0.0, 1.0), 1.0)
    out = {k: np.zeros(steps) for k in ('t_top', 't_loc', 't_near', 't_far', 't_surface', 'q_surface', 'q_wall', 'ice')}
    g_w = g_st = 0.0
    for k in range(steps):
        u = np.array([0.0, p['TDeep'], t_wall[k] if use_wall else 0.0, q_wall[k] if not use_wall else 0.0])
        for _ in range(n_sub):
            x_old, f_old = x.copy(), liquid.copy()
            x_it, f_it = x_old.copy(), f_old.copy()
            for iteration in range(MAX_ITERATIONS):
                c, k_mat, b_mat, g_w, g_st = _network(p, 1.0 - f_it, ratio, r_series, use_wall)
                #liquid fraction iterated as in the 2D reference (Swaminathan and Voller)
                mushy = (latent > 0) & (f_it > 0.0) & (f_it < 1.0)
                slope = np.where(mushy, 1.0 / width, 0.0)
                t_star = t_low + f_it * width
                a = np.diag(c / h + latent / h * slope) + k_mat
                r = c / h * x_old + b_mat @ u - latent / h * (f_it - slope * t_star - f_old)
                if use_surface:
                    #GroundSurface: convection, absorbed global radiation, long-wave exchange with the sky
                    tsk = x_it[SURF] - ABS_ZERO
                    h_rad = 4 * p['epsilon'] * SIGMA * tsk ** 3
                    a[SURF, SURF] += p['spacing'] * (p['hConv'] + h_rad)
                    r[SURF] += p['spacing'] * (
                        p['hConv'] * weather['TAir'][k] + (1 - p['albedo']) * weather['IGlob'][k]
                        + p['epsilon'] * SIGMA * ((weather['TSky'][k] - ABS_ZERO) ** 4 - tsk ** 4) + h_rad * x_it[SURF])
                else:
                    #a prescribed surface: the surface node is held at the given temperature
                    a[SURF, :] = 0.0
                    a[SURF, SURF] = 1.0
                    r[SURF] = surface_temperature[k]
                sol = np.linalg.solve(a, r)
                change = float(np.max(np.abs(sol - x_it)))
                f_change = 0.0
                if freeze:
                    f_new = np.where(mushy, np.clip(f_it + slope * (sol - t_star), 0.0, 1.0),
                                     np.clip((sol - t_low) / width, 0.0, 1.0))
                    f_new = np.where(latent > 0, f_new, 1.0)
                    if iteration >= UNDAMPED_ITERATIONS:
                        f_new = f_it + DAMPING * (f_new - f_it)
                    f_change = float(np.max(np.abs(f_new - f_it)))
                    f_it = f_new
                done = (change < TOLERANCE_K / 10 and f_change < f_tolerance) or (not freeze and not use_surface)
                if not done and iteration >= UNDAMPED_ITERATIONS:
                    sol = x_it + DAMPING * (sol - x_it)
                x_it = sol
                if done:
                    break
            else:
                raise RuntimeError('ground model: iteration did not converge in step {} (change {:.3f} K)'.format(k, change))
            x, liquid = x_it, f_it
        ice = 1.0 - liquid
        out['t_top'][k], out['t_loc'][k], out['t_near'][k], out['t_far'][k] = x[[TOP, LOC, NEAR, FAR]]
        out['t_surface'][k] = x[SURF]
        out['q_surface'][k] = g_st * (x[SURF] - x[TOP])
        out['q_wall'][k] = g_w * (t_wall[k] - x[LOC]) if use_wall else q_wall[k]
        out['ice'][k] = float(np.sum(latent * ice) / latent.sum()) if freeze else 0.0
    state = {name: float(x[i]) for i, name in enumerate(START_NAMES)}
    state['TStartSurface'] = float(x[SURF])
    return GroundResult(**out, state=state)


def startState(params, geometry, soil, weather_year=None, t_mean_fluid=None, *, years=5, start_day=0,
               r_conv_nominal=0.1, undisturbed=False):
    """Start values of a section (the same for every section): the undisturbed profile at the node depths, or the
    state at start_day after `years` repeated climate years with the wall at t_mean_fluid behind the wall and a nominal
    convection resistance r_conv_nominal [K m/W per meter of loop pipe] (design G9)."""
    if undisturbed:
        state = {n: undisturbedTemperature(soil, z, start_day) for n, z in zip(START_NAMES, nodeDepths(geometry, soil))}
        state['TStartSurface'] = undisturbedTemperature(soil, 0.0, start_day)
        return state
    if weather_year is None or t_mean_fluid is None:
        raise ValueError('the pre-calculated start state needs the climate year and the mean fluid temperature')
    n_year = len(weather_year['TAir'])
    steps = years * n_year + int(round(start_day * 24))
    idx = np.arange(steps) % n_year
    weather = {k: np.asarray(weather_year[k], dtype=float)[idx] for k in ('TAir', 'IGlob', 'TSky')}
    r_series = wallResistance(geometry) + r_conv_nominal / geometry.loop_length_per_m
    start = startState(params, geometry, soil, undisturbed=True, start_day=0)
    return runGroundModel(params, steps, start=start, weather=weather, t_wall=np.full(steps, float(t_mean_fluid)),
                          r_series=r_series).state
