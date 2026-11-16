# coding=utf-8
"""Heat flow of every pipe from its insulation, its position in the bundle, the simulated pipe temperature and the
ambient (OpenSpec change network-cost-data). Q > 0 leaves the pipe.

Each pipe is treated as a single buried pipe: the heat exchange between the pipes of a bundle and the shared casing of
twin pipes are ignored; the sum per line is checked against the simulated QAmbtotal of the bundle."""
import math

AMBIENT_AIR, AMBIENT_GROUND, AMBIENT_DUCT = 1, 2, 3
H_AIR = 10.0  # W/(m2 K), outer surface in air or duct
CHECK_TOLERANCE = 0.15  # share of the yearly simulated loss


def uPrime(d_inner, layers, depth, ambient, lambda_soil):
    """Heat transfer per metre [W/(m K)]: layers [(thickness m, lambda W/(m K))] from the axis outwards;
    buried: ground resistance ln(4H/D)/(2 pi lambda_soil); air or duct: 1/(h pi D)."""
    r = d_inner / 2
    resistance = 0.0
    for thickness, lam in layers:
        if thickness and lam:
            resistance += math.log((r + thickness) / r) / (2 * math.pi * lam)
        r += thickness or 0
    if ambient == AMBIENT_GROUND:
        depth = max(depth or 1.0, 2 * r)
        resistance += math.log(4 * depth / (2 * r)) / (2 * math.pi * lambda_soil)
    else:
        resistance += 1 / (H_AIR * math.pi * 2 * r)
    return 1 / resistance


def kusuda(day_of_year, settings):
    """Ground temperature [°C] after Kusuda at the depth of the modelling settings."""
    tm = float(settings.get('kusuda_tsurfmean', settings.get('ground_temp', 10)))
    amplitude = float(settings.get('kusuda_tsurfampl', 0))
    theta = float(settings.get('kusuda_theta', 0))
    depth = float(settings.get('kusuda_depth', 1))
    alpha = float(settings.get('kusuda_lambda', 1.0)) / (float(settings.get('kusuda_rho', 1500)) * float(settings.get('kusuda_cp', 1000))) * 86400
    damping = depth * math.sqrt(math.pi / (365 * alpha))
    return tm - amplitude * math.exp(-damping) * math.cos(2 * math.pi / 365 * (day_of_year - theta - depth / 2 * math.sqrt(365 / (math.pi * alpha))))


def ambientTemperature(ambient, day_of_year, settings, t_air=None):
    """Ambient of a pipe: ground (Kusuda or constant), duct (constant), air (t_air; the ground if unknown)."""
    if ambient == AMBIENT_DUCT:
        return float(settings.get('duct_temp', 20))
    if ambient == AMBIENT_AIR and t_air is not None:
        return t_air
    if str(settings.get('ground_model', '')).lower() == 'kusuda':
        return kusuda(day_of_year, settings)
    return float(settings.get('ground_temp', 10))


def pipeHeatFlow(u, length, t_pipe, t_ambient):
    return u * length * (t_pipe - t_ambient)


def sequenceModes(connections):
    """{sequence: 'heat'|'cold'} from the plant connections [{'conn_seq', 'type' (1 supply, 2 return), 'temp'}]:
    the k-th supply with the k-th return; heat if the supply is warmer than the return."""
    supplies = sorted({c['conn_seq']: c for c in connections if c['type'] == 1}.values(), key=lambda c: c['conn_seq'])
    returns = sorted({c['conn_seq']: c for c in connections if c['type'] == 2}.values(), key=lambda c: c['conn_seq'])
    modes = {}
    for s, r in zip(supplies, returns):
        mode = 'heat' if float(s.get('temp') or 0) >= float(r.get('temp') or 0) else 'cold'
        modes[s['conn_seq']] = modes[r['conn_seq']] = mode
    return modes


def checkLines(calculated, simulated):
    """Lines whose yearly calculated loss (sum of the pipes) deviates from the simulated one by more than the tolerance:
    {lid: (calculated, simulated)}; both in the same unit."""
    off = {}
    for lid, value in calculated.items():
        sim = simulated.get(lid)
        if sim is None:
            continue
        if abs(value - sim) > CHECK_TOLERANCE * max(abs(sim), 1e-9):
            off[lid] = (value, sim)
    return off
