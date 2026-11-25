#2D reference of the ground around a collector trench (change ground-collector-model, design G7): finite volumes over
#half a trench cell (symmetry at the trench centre and at half the spacing), implicit Euler; the RC values of the
#Modelica model are fitted to it and the Python ground model is checked against it; plain Python with numpy/scipy
import math
from dataclasses import dataclass

import numpy as np
import scipy.sparse as sp
import scipy.sparse.linalg as spla

from .ground_collector_geometry import MIN_CELL_M, PIPE_CELL_M, deepTemperature, undisturbedTemperature
from .ground_climate import ABS_ZERO, SIGMA

TOLERANCE_K = 0.01
MAX_ITERATIONS = 50
#cells crossing the freezing range can make the secant capacity jump between iterations: damp after a few
UNDAMPED_ITERATIONS = 5
DAMPING = 0.5
#a step that does not converge is halved, at most this often (2**6 = 64 parts)
MAX_SPLITS = 6


def _graded(a, b, fine_a, fine_b, min_cell, growth, max_cell):
    """Edges from a to b, cells min_cell at a fine end growing by growth up to max_cell."""
    length = b - a
    if length <= 0:
        return np.array([a, b])
    if not fine_a and not fine_b:
        n = max(1, math.ceil(length / max_cell))
        return np.linspace(a, b, n + 1)

    def sizes(total):
        out, h = [], min_cell
        while sum(out) < total:
            out.append(h)
            h = min(h * growth, max_cell)
        return np.array(out) * total / sum(out)

    if fine_a and fine_b:
        half = sizes(length / 2)
        cells = np.concatenate([half, half[::-1]])
    elif fine_a:
        cells = sizes(length)
    else:
        cells = sizes(length)[::-1]
    return a + np.concatenate([[0.0], np.cumsum(cells)])


@dataclass
class Grid:
    x_edges: np.ndarray
    z_edges: np.ndarray
    dx: np.ndarray          # per cell (flattened, row-major: z outer, x inner)
    dz: np.ndarray
    zc: np.ndarray          # cell centre depth
    volume: np.ndarray      # per meter of trench, half cell
    region: np.ndarray      # bool, source region
    nx: int
    nz: int


def buildGrid(geometry, soil, min_cell=None, growth=None, max_cell=1.0, region_cell=None):
    """The grid of the reference: about 400 cells for a region, about 3000 for a resolved pipe (1 cm at the pipe)."""
    fine = geometry.pipe_resolved
    min_cell = min_cell or (PIPE_CELL_M if fine else MIN_CELL_M)
    growth = growth or (1.2 if fine else 1.4)
    region_cell = region_cell or (PIPE_CELL_M if fine else 0.1)
    half_w, half_s = geometry.source_width_m / 2, geometry.spacing_m / 2
    x_parts = [_graded(0.0, half_w, False, False, min_cell, growth, min(region_cell, max(half_w, min_cell)))]
    if half_s > half_w + 1e-9:
        x_parts.append(_graded(half_w, half_s, True, False, min_cell, growth, max_cell)[1:])
    top, bottom = geometry.source_top_m, geometry.source_bottom_m
    z_parts = [_graded(0.0, top, True, True, min_cell, growth, max_cell),
               _graded(top, bottom, False, False, min_cell, growth, min(region_cell, bottom - top))[1:],
               _graded(bottom, soil.depth_deep_m, True, False, min_cell, growth, max_cell)[1:]]
    x_edges, z_edges = np.concatenate(x_parts), np.concatenate(z_parts)
    dx1, dz1 = np.diff(x_edges), np.diff(z_edges)
    xc1, zc1 = (x_edges[:-1] + x_edges[1:]) / 2, (z_edges[:-1] + z_edges[1:]) / 2
    nx, nz = len(dx1), len(dz1)
    dx, dz = np.tile(dx1, nz), np.repeat(dz1, nx)
    xc, zc = np.tile(xc1, nz), np.repeat(zc1, nx)
    region = (xc < half_w) & (zc > top) & (zc < bottom)
    if not region.any():
        raise ValueError('source region has no grid cell')
    return Grid(x_edges, z_edges, dx, dz, zc, dx * dz, region, nx, nz)


def _ice(t, soil):
    if soil.water_content <= 0:
        return np.zeros_like(t)
    return np.clip((soil.t_freeze_c - t) / soil.freeze_range_k, 0.0, 1.0)


def _enthalpy(t, soil):
    """J/m3: sensible plus the latent heat of the liquid part of the soil water."""
    return soil.rho_c_j7m3k * t + soil.latent_j7m3 * (1.0 - _ice(t, soil))


@dataclass
class ReferenceResult:
    t_region: np.ndarray        # mean temperature of the source region per step
    q_source: np.ndarray        # W/m trench into the ground at the source
    q_surface: np.ndarray       # W/m trench from the surface into the ground
    q_bottom: np.ndarray        # W/m trench from the lower boundary into the ground
    ice_region: np.ndarray
    t_surface: np.ndarray       # surface temperature (prescribed or the surface layer)
    energy: np.ndarray          # J/m trench stored, before the first step and after each step (n + 1 values)
    state: np.ndarray           # cell temperatures after the last step


def undisturbedState(grid, soil, day):
    return np.array([undisturbedTemperature(soil, z, day) for z in grid.zc])


def runReference(geometry, soil, steps, *, surface_temperature=None, weather=None, surface=None, q_wall=None,
                 t_wall=None, r_loc=None, freezing=True, start=None, start_day=0.0, dt_h=1.0, grid=None):
    """Run the reference over steps time steps of dt_h hours. Inputs are per step (value at the step's end).
    The surface: surface_temperature (prescribed), or weather (dict TAir, IGlob, TSky, optionally albedo per step or
    one value; without it surface.albedo) with surface (SurfaceProperties).
    The source: q_wall [W/m trench, positive = into the ground], or t_wall [degC] behind r_loc [K m/W per trench m]."""
    if (surface_temperature is None) == (weather is None):
        raise ValueError('give either surface_temperature or weather')
    if weather is not None and surface is None:
        raise ValueError('weather needs the surface properties')
    if t_wall is not None and r_loc is None:
        raise ValueError('t_wall needs r_loc')
    if weather is not None:
        albedo = np.asarray(weather.get('albedo', surface.albedo), dtype=float)
        albedo = np.broadcast_to(albedo, (steps,)) if albedo.ndim == 0 else albedo
    grid = grid or buildGrid(geometry, soil)
    n = len(grid.dx)
    use_surface_node = weather is not None
    m = n + 1 if use_surface_node else n
    dt = dt_h * 3600.0
    freeze = freezing and soil.water_content > 0
    t_deep = deepTemperature(soil)
    lam0 = soil.lambda_w7mk
    ratio = soil.lambda_frozen_ratio
    variable_lambda = freeze and ratio != 1.0
    q_wall = None if q_wall is None else np.asarray(q_wall, dtype=float)
    t_wall = None if t_wall is None else np.asarray(t_wall, dtype=float)
    if surface_temperature is not None:
        surface_temperature = np.asarray(surface_temperature, dtype=float)
    reg_frac = np.where(grid.region, grid.volume, 0.0) / grid.volume[grid.region].sum()

    #faces: horizontal neighbours (x direction) and vertical neighbours (z direction)
    idx = np.arange(n).reshape(grid.nz, grid.nx)
    fx_i, fx_j = idx[:, :-1].ravel(), idx[:, 1:].ravel()
    fz_i, fz_j = idx[:-1, :].ravel(), idx[1:, :].ravel()
    top_cells, bottom_cells = idx[0, :], idx[-1, :]

    def conductances(lam):
        gx = grid.dz[fx_i] / (grid.dx[fx_i] / 2 / lam[fx_i] + grid.dx[fx_j] / 2 / lam[fx_j])
        gz = grid.dx[fz_i] / (grid.dz[fz_i] / 2 / lam[fz_i] + grid.dz[fz_j] / 2 / lam[fz_j])
        g_top = grid.dx[top_cells] * lam[top_cells] / (grid.dz[top_cells] / 2)
        g_bot = grid.dx[bottom_cells] * lam[bottom_cells] / (grid.dz[bottom_cells] / 2)
        return gx, gz, g_top, g_bot

    def laplacian(gx, gz, g_top, g_bot, g_wall):
        rows = np.concatenate([fx_i, fx_j, fz_i, fz_j])
        cols = np.concatenate([fx_j, fx_i, fz_j, fz_i])
        vals = np.concatenate([gx, gx, gz, gz])
        diag = np.zeros(m)
        np.add.at(diag, fx_i, gx)
        np.add.at(diag, fx_j, gx)
        np.add.at(diag, fz_i, gz)
        np.add.at(diag, fz_j, gz)
        diag[top_cells] += g_top
        diag[bottom_cells] += g_bot
        diag[:n] += g_wall
        if use_surface_node:
            rows = np.concatenate([rows, top_cells, np.full(len(top_cells), n)])
            cols = np.concatenate([cols, np.full(len(top_cells), n), top_cells])
            vals = np.concatenate([vals, g_top, g_top])
            diag[n] += g_top.sum()
        return sp.csc_matrix((-vals, (rows, cols)), shape=(m, m)) + sp.diags(diag, format='csc')

    if start is None:
        t = undisturbedState(grid, soil, start_day)
    else:
        t = np.array(start, dtype=float)
        if t.shape != (n,):
            raise ValueError('start state has {} values, the grid {} cells'.format(t.size, n))
    t_s = undisturbedTemperature(soil, 0.0, start_day) if use_surface_node else None
    if use_surface_node:
        c_surface = surface.rho_c_j7m3k * surface.d_layer_m * geometry.spacing_m / 2
        area = geometry.spacing_m / 2

    def stored(temps):
        #the ground only: q_surface is the heat crossing from the surface (layer) into it
        e = float(np.sum(grid.volume * _enthalpy(temps, soil))) if freeze else float(np.sum(grid.volume * soil.rho_c_j7m3k * temps))
        return 2 * e

    lam_const = np.full(n, lam0)
    g_const = conductances(lam_const)
    wall_total = 0.0 if t_wall is None else 1.0 / r_loc / 2
    #a surface without radiation (epsilon 0) is a linear heat transfer to TAir: the fit's linearized surface (G7)
    linear = not freeze and (not use_surface_node or surface.epsilon == 0)
    if linear:
        g_wall = wall_total * reg_frac
        c_cells = grid.volume * soil.rho_c_j7m3k / dt
        diag_lin = np.zeros(m)
        diag_lin[:n] = c_cells
        if use_surface_node:
            diag_lin[n] = c_surface / dt + area * surface.h_conv_w7m2k
        lu = spla.splu((laplacian(g_const[0], g_const[1], g_const[2], g_const[3], g_wall)
                        + sp.diags(diag_lin, format='csc')).tocsc())

    def nonlinearStep(t_old, ts_old, k, dt_loc):
        """(t, ts, g_top, g_bot, g_wall) after dt_loc seconds, or None when the iteration does not converge."""
        rhs_base = np.zeros(m)
        if q_wall is not None:
            rhs_base[:n] += q_wall[k] / 2 * reg_frac
        t_it, ts_it = t_old.copy(), ts_old
        #liquid fraction iterated directly (Swaminathan and Voller): its slope in the freezing range goes into the
        #matrix, cells outside the range are updated from their temperature
        f_old = 1.0 - _ice(t_old, soil) if freeze else np.ones(n)
        f_it = f_old.copy()
        t_low, width = soil.t_freeze_c - soil.freeze_range_k, soil.freeze_range_k
        latent = grid.volume * soil.latent_j7m3 / dt_loc
        c_cells = grid.volume * soil.rho_c_j7m3k / dt_loc
        f_tolerance = TOLERANCE_K * soil.rho_c_j7m3k / max(soil.latent_j7m3, 1.0)
        for iteration in range(MAX_ITERATIONS):
            ice = 1.0 - f_it
            lam = lam0 * (1 + (ratio - 1) * ice) if variable_lambda else lam_const
            gx, gz, g_top, g_bot = conductances(lam) if variable_lambda else g_const
            g_wall = wall_total * reg_frac * ((1 + (ratio - 1) * ice) if variable_lambda else 1.0)
            diag_extra = np.zeros(m)
            diag_extra[:n] = c_cells
            rhs = rhs_base.copy()
            rhs[bottom_cells] += g_bot * t_deep
            rhs[:n] += g_wall * (t_wall[k] if t_wall is not None else 0.0) + c_cells * t_old
            if freeze:
                mushy = (f_it > 0.0) & (f_it < 1.0)
                slope = np.where(mushy, 1.0 / width, 0.0)
                t_star = t_low + f_it * width
                diag_extra[:n] += latent * slope
                rhs[:n] -= latent * (f_it - slope * t_star - f_old)
            if surface_temperature is not None:
                rhs[top_cells] += g_top * surface_temperature[k]
            else:
                tsk = ts_it - ABS_ZERO
                h_rad = 4 * surface.epsilon * SIGMA * tsk ** 3
                diag_extra[n] = c_surface / dt_loc + area * (surface.h_conv_w7m2k + h_rad)
                rhs[n] = (c_surface / dt_loc * ts_old + area * (surface.h_conv_w7m2k * weather['TAir'][k]
                          + (1 - albedo[k]) * weather['IGlob'][k]
                          + surface.epsilon * SIGMA * ((weather['TSky'][k] - ABS_ZERO) ** 4 - tsk ** 4)
                          + h_rad * ts_it))
            sol = spla.spsolve((laplacian(gx, gz, g_top, g_bot, g_wall) + sp.diags(diag_extra, format='csc')).tocsc(), rhs)
            t_new = sol[:n]
            ts_new = float(sol[n]) if use_surface_node else None
            change = np.max(np.abs(t_new - t_it))
            if use_surface_node:
                change = max(change, abs(ts_new - ts_it))
            f_change = 0.0
            if freeze:
                f_new = np.where(mushy, np.clip(f_it + slope * (t_new - t_star), 0.0, 1.0),
                                 np.clip((t_new - t_low) / width, 0.0, 1.0))
                if iteration >= UNDAMPED_ITERATIONS:
                    f_new = f_it + DAMPING * (f_new - f_it)
                f_change = float(np.max(np.abs(f_new - f_it)))
                f_it = f_new
            if change < TOLERANCE_K and f_change < f_tolerance:
                return t_new, ts_new, g_top, g_bot, g_wall
            if iteration >= UNDAMPED_ITERATIONS:
                t_new = t_it + DAMPING * (t_new - t_it)
                if use_surface_node:
                    ts_new = ts_it + DAMPING * (ts_new - ts_it)
            t_it, ts_it = t_new, ts_new
        return None

    def advance(t_old, ts_old, k, dt_loc, depth):
        """[(t, ts, g_top, g_bot, g_wall, share of the step)]: the step, split into halves where it does not converge."""
        result = nonlinearStep(t_old, ts_old, k, dt_loc)
        if result is not None:
            return [result + (dt_loc / dt,)]
        if depth >= MAX_SPLITS:
            raise RuntimeError('2D reference: freezing iteration did not converge in step {} even in {} parts'.format(
                k, 2 ** MAX_SPLITS))
        first = advance(t_old, ts_old, k, dt_loc / 2, depth + 1)
        return first + advance(first[-1][0], first[-1][1], k, dt_loc / 2, depth + 1)

    res = {k: np.zeros(steps) for k in ('t_region', 'q_source', 'q_surface', 'q_bottom', 'ice_region', 't_surface')}
    energy = np.zeros(steps + 1)
    energy[0] = stored(t)
    for k in range(steps):
        t_old, ts_old = t, t_s
        rhs_base = np.zeros(m)
        if q_wall is not None:
            rhs_base[:n] += q_wall[k] / 2 * reg_frac
        if linear:
            rhs = rhs_base.copy()
            if use_surface_node:
                rhs[n] = c_surface / dt * ts_old + area * (surface.h_conv_w7m2k * weather['TAir'][k]
                                                          + (1 - albedo[k]) * weather['IGlob'][k])
            else:
                rhs[top_cells] += g_const[2] * surface_temperature[k]
            rhs[bottom_cells] += g_const[3] * t_deep
            rhs[:n] += g_wall * (t_wall[k] if t_wall is not None else 0.0) + c_cells * t_old
            sol = lu.solve(rhs)
            t_new = sol[:n]
            if use_surface_node:
                t_s = float(sol[n])
            gx, gz, g_top, g_bot = g_const
        else:
            pieces = advance(t_old, ts_old, k, dt, 0)
            t_new, t_s = pieces[-1][0], pieces[-1][1]
        t = t_new
        ts_now = t_s if use_surface_node else surface_temperature[k]
        if linear:
            pieces = [(t, t_s, g_top, g_bot, g_wall, 1.0)]
        #a split step reports the mean flux of its parts, so the energy balance holds over the step
        q_src = q_sur = q_bot = 0.0
        for t_p, ts_p, g_top_p, g_bot_p, g_wall_p, share in pieces:
            ts_p = ts_p if use_surface_node else surface_temperature[k]
            if q_wall is not None:
                q_src += share * q_wall[k]
            elif t_wall is not None:
                q_src += share * 2 * float(np.sum(g_wall_p * (t_wall[k] - t_p)))
            q_sur += share * 2 * float(np.sum(g_top_p * (ts_p - t_p[top_cells])))
            q_bot += share * 2 * float(np.sum(g_bot_p * (t_deep - t_p[bottom_cells])))
        res['q_source'][k] = q_src
        res['q_surface'][k] = q_sur
        res['q_bottom'][k] = q_bot
        res['t_region'][k] = float(np.sum(reg_frac * t))
        res['ice_region'][k] = float(np.sum(reg_frac * _ice(t, soil))) if freeze else 0.0
        res['t_surface'][k] = ts_now
        energy[k + 1] = stored(t)
    return ReferenceResult(res['t_region'], res['q_source'], res['q_surface'], res['q_bottom'], res['ice_region'],
                           res['t_surface'], energy, t)


def linearSystem(geometry, soil, surface, r_loc, grid=None):
    """The unfrozen reference as a linear system with a surface node that exchanges heat with an outside temperature
    through surface.h_conv_w7m2k (no radiation): capacities c, conductance matrix L, input matrix B for the inputs
    (T_outside, T_deep, T_wall) and output rows (heat into the fluid, heat from the surface into the ground; whole
    trench cell). C dT/dt = -L T + B u."""
    grid = grid or buildGrid(geometry, soil)
    n = len(grid.dx)
    m = n + 1
    lam = soil.lambda_w7mk
    idx = np.arange(n).reshape(grid.nz, grid.nx)
    fx_i, fx_j = idx[:, :-1].ravel(), idx[:, 1:].ravel()
    fz_i, fz_j = idx[:-1, :].ravel(), idx[1:, :].ravel()
    top, bot = idx[0, :], idx[-1, :]
    gx = grid.dz[fx_i] / (grid.dx[fx_i] / 2 / lam + grid.dx[fx_j] / 2 / lam)
    gz = grid.dx[fz_i] / (grid.dz[fz_i] / 2 / lam + grid.dz[fz_j] / 2 / lam)
    g_top = grid.dx[top] * lam / (grid.dz[top] / 2)
    g_bot = grid.dx[bot] * lam / (grid.dz[bot] / 2)
    reg_frac = np.where(grid.region, grid.volume, 0.0) / grid.volume[grid.region].sum()
    g_wall = 1.0 / r_loc / 2 * reg_frac
    area = geometry.spacing_m / 2
    g_out = area * surface.h_conv_w7m2k
    rows = np.concatenate([fx_i, fx_j, fz_i, fz_j, top, np.full(len(top), n)])
    cols = np.concatenate([fx_j, fx_i, fz_j, fz_i, np.full(len(top), n), top])
    vals = np.concatenate([gx, gx, gz, gz, g_top, g_top])
    diag = np.zeros(m)
    for i, j, g in ((fx_i, fx_j, gx), (fz_i, fz_j, gz)):
        np.add.at(diag, i, g)
        np.add.at(diag, j, g)
    diag[top] += g_top
    diag[n] += g_top.sum() + g_out
    diag[bot] += g_bot
    diag[:n] += g_wall
    L = (sp.csc_matrix((-vals, (rows, cols)), shape=(m, m)) + sp.diags(diag, format='csc')).tocsc()
    c = np.concatenate([grid.volume * soil.rho_c_j7m3k, [surface.rho_c_j7m3k * surface.d_layer_m * area]])
    B = np.zeros((m, 3))
    B[n, 0] = g_out
    B[bot, 1] = g_bot
    B[:n, 2] = g_wall
    out = np.zeros((2, m))
    d = np.zeros((2, 3))
    out[0, :n] = 2 * g_wall
    d[0, 2] = -2 * g_wall.sum()
    out[1, n] = 2 * g_top.sum()
    out[1, top] = -2 * g_top
    return c, L, B, out, d


def frequencyResponse(system, omegas):
    """H[k] (2 outputs x 3 inputs, complex) of linearSystem at the angular frequencies omegas [1/s]; 0 = steady."""
    c, L, B, out, d = system
    H = []
    for w in omegas:
        lu = spla.splu((L + sp.diags(1j * w * c, format='csc')).tocsc())
        X = np.column_stack([lu.solve(B[:, i].astype(complex)) for i in range(B.shape[1])])
        H.append(out @ X + d)
    return np.array(H)
