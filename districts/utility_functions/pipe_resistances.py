"""Steady state thermal resistances of carrier pipes in a common casing (twin pipe, any number and position of pipes).

casingResistanceMatrix returns the matrix A [K*m/W] with  T_pipe - T_ambient = A * q  (q heat loss of the pipes [W/m],
T_pipe temperature of the outer surface of the carrier pipes; the resistances of the liquid film and the pipe wall are
not included). The casing wall is not modelled: the foam body borders on the ground.

Method: multipole expansion, the coefficients by least squares collocation on the boundaries. The temperature is the
real part of analytic functions, so the heat equation is fulfilled exactly and only the boundary conditions are
approximated:
  foam (|z| < r_casing):  for every pipe n the line source -q_n / (2 pi lambda_ins) ln|z - z_n| and the multipoles
                          Re, Im (r_n / (z - z_n))^j,  and the regular terms Re, Im (z / r_casing)^j
  ground (buried casing): the line source -Q / (2 pi lambda_soil) ln|z| of the total heat loss Q and the multipoles
                          Re, Im (r_casing / z)^j, each minus its mirror image at the ground surface (temperature of
                          the ground surface = T_ambient)
  conditions:             uniform temperature on every pipe, continuous temperature and heat flux at the casing
  casing in air or duct:  uniform temperature T_ambient on the casing (no ground)
The order of the expansion is raised until the matrix changes by less than the tolerance."""
import math

import numpy as np

ORDERS = (10, 16, 24, 36)


def checkGeometry(pipes, r_casing, depth=None):
    """ValueError if the pipes (x, y, r) do not fit into the casing or the casing is not covered."""
    if r_casing <= 0 or any(r <= 0 for _, _, r in pipes):
        raise ValueError('radii must be positive')
    for i, (x, y, r) in enumerate(pipes):
        if math.hypot(x, y) + r >= r_casing:
            raise ValueError('the pipe {} (outer diameter {:.4g} m, {:.4g} m from the centre) does not fit into the casing (foam diameter {:.4g} m)'.format(
                i + 1, 2 * r, math.hypot(x, y), 2 * r_casing))
        for j, (x2, y2, r2) in enumerate(pipes[:i]):
            if math.hypot(x - x2, y - y2) <= r + r2:
                raise ValueError('the pipes {} and {} overlap (distance of the centres {:.4g} m)'.format(j + 1, i + 1, math.hypot(x - x2, y - y2)))
    if depth is not None and depth <= r_casing:
        raise ValueError('the laying depth {:.4g} m does not cover the casing (foam diameter {:.4g} m)'.format(depth, 2 * r_casing))


def _solve(centres, radii, r_casing, depth, lambda_ins, lambda_soil, ground, order):
    """Resistance matrix for one order of the expansion."""
    n = len(centres)
    points = 4 * order + 8
    angles = np.exp(2j * np.pi * (np.arange(points) + 0.5) / points)
    orders = np.arange(1, order + 1)

    def mirror(z):
        return np.conj(z) + 2j * depth

    def inner(z, direction=None):
        """Columns of the unknown terms of the foam at the points z: values, or derivatives along direction."""
        cols = []
        for centre, radius in zip(centres, radii):
            f = (radius / (z[:, None] - centre)) ** orders
            if direction is not None:
                f = -orders * f / (z[:, None] - centre) * direction[:, None]
            cols += [f.real, (-1j * f).real]
        f = (z[:, None] / r_casing) ** orders
        if direction is None:
            cols += [np.ones((len(z), 1)), f.real, (-1j * f).real]
        else:
            f = orders * f / z[:, None] * direction[:, None]
            cols += [np.zeros((len(z), 1)), f.real, (-1j * f).real]
        return np.hstack(cols)

    def outer(z, direction=None):
        """Columns of the unknown terms of the ground (multipoles minus their mirror images)."""
        w = mirror(z)
        f, g = (r_casing / z[:, None]) ** orders, (r_casing / w[:, None]) ** orders
        if direction is not None:
            f = -orders * f / z[:, None] * direction[:, None]
            g = -orders * g / w[:, None] * np.conj(direction)[:, None]
        return np.hstack([f.real - g.real, (-1j * f).real - (-1j * g).real])

    def source(z, k, direction=None):
        """Line source of the pipe k with q = 1 W/m in the foam."""
        if direction is None:
            return -np.log(np.abs(z - centres[k]) / radii[k]) / (2 * np.pi * lambda_ins)
        return (-direction / (z - centres[k])).real / (2 * np.pi * lambda_ins)

    def groundSource(z, direction=None):
        """Line source of the total heat loss 1 W/m at the casing centre with its mirror image."""
        w = mirror(z)
        if direction is None:
            return np.log(np.abs(w) / np.abs(z)) / (2 * np.pi * lambda_soil)
        return ((np.conj(direction) / w).real - (direction / z).real) / (2 * np.pi * lambda_soil)

    n_inner = 2 * order * n + 2 * order + 1
    n_outer = 2 * order if ground else 0
    rows, rhs = [], []
    for p, (centre, radius) in enumerate(zip(centres, radii)):  # uniform temperature T_p on the pipe
        z = centre + radius * angles
        temperature = np.zeros((points, n))
        temperature[:, p] = -1.0
        rows.append(np.hstack([inner(z), np.zeros((points, n_outer)), temperature]))
        rhs.append(np.column_stack([-source(z, k) for k in range(n)]))
    z = r_casing * angles
    if ground:  # continuous temperature and heat flux at the casing
        scale = r_casing / lambda_ins
        rows.append(np.hstack([inner(z), -outer(z), np.zeros((points, n))]))
        rhs.append(np.column_stack([groundSource(z) - source(z, k) for k in range(n)]))
        rows.append(scale * np.hstack([lambda_ins * inner(z, angles), -lambda_soil * outer(z, angles), np.zeros((points, n))]))
        rhs.append(scale * np.column_stack([lambda_soil * groundSource(z, angles) - lambda_ins * source(z, k, angles) for k in range(n)]))
    else:  # casing of uniform temperature
        rows.append(np.hstack([inner(z), np.zeros((points, n))]))
        rhs.append(np.column_stack([-source(z, k) for k in range(n)]))
    solution = np.linalg.lstsq(np.vstack(rows), np.vstack(rhs), rcond=None)[0]
    matrix = solution[n_inner + n_outer:, :]
    return (matrix + matrix.T) / 2.0


def casingResistanceMatrix(pipes, r_casing, depth, lambda_ins, lambda_soil, ground=True, tolerance=1e-5):
    """Resistance matrix A [K*m/W] of the carrier pipes in a common casing (see above).

    pipes: [(x, y, r)] position of the pipe centres relative to the casing centre (x to the right, y downwards) and outer
    radius of the carrier pipes [m]; r_casing: radius of the foam body; depth: depth of the casing centre below the
    ground surface; ground=False: casing of uniform ambient temperature (depth and lambda_soil are not used).
    ValueError for an invalid geometry."""
    pipes = [(float(x), float(y), float(r)) for x, y, r in pipes]
    checkGeometry(pipes, r_casing, depth if ground else None)
    if lambda_ins <= 0 or (ground and lambda_soil <= 0):
        raise ValueError('thermal conductivities must be positive')
    centres = [complex(x, -y) for x, y, _ in pipes]  # the ground surface is the line Im z = depth
    radii = [r for _, _, r in pipes]
    matrix = None
    for order in ORDERS:
        previous, matrix = matrix, _solve(centres, radii, r_casing, depth, lambda_ins, lambda_soil, ground, order)
        if previous is not None and np.max(np.abs(matrix - previous)) <= tolerance * np.max(np.abs(matrix)):
            break
    return matrix
