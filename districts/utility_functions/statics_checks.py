#loads, laying methods, checks and pads of the statics of rigid steel pipes (change statics-steel-solver); pure
#functions on plain values, no QGIS, no DB
import math

from . import statics_catalog as cat

TO_CONFIRM = 'to be confirmed: '
#key: (default or None, unit, description, source); None = no default, the check gives utilisation only
SOLVER_PARAMETERS = {
    'design_temperature_c': (120.0, 'degC', 'design temperature of the pipes', 'EN 253 continuous limit'),
    'design_pressure_bar': (16.0, 'bar', 'design pressure of the pipes', 'project choice'),
    'laying_temperature_c': (10.0, 'degC', 'laying temperature, lowest temperature of the cycle', 'isoplus PHB 10/31 example'),
    'soil_unit_weight_kn_m3': (19.0, 'kN/m3', 'unit weight of the soil', 'isoplus PHB 9/12, 12/4'),
    'friction_angle_deg': (32.5, 'deg', 'internal friction angle of the soil', 'isoplus PHB 9/12, 12/4'),
    'friction_max': (0.40, '-', 'upper friction coefficient casing/soil (stresses, forces)', 'fit to isoplus PHB 12/4'),
    'friction_min': (0.20, '-', 'lower friction coefficient casing/soil (displacements, legs, pads)', TO_CONFIRM + 'FW 401'),
    'axial_slip_m': (0.0005, 'm', 'axial displacement at which the friction is fully mobilised', TO_CONFIRM + 'EN 13941'),
    'lateral_slip_m': (0.02, 'm', 'lateral displacement at which the passive earth pressure is reached', TO_CONFIRM + 'EN 13941'),
    'traffic_load_kn_m2': (33.3, 'kN/m2', 'traffic area load for the minimum cover', 'isoplus PHB 9/11 (SLW 60)'),
    'sigma_ax_allow_n7mm2': (190.0, 'N/mm2', 'allowed axial stress of the straight steel pipe when the series has none', 'isoplus PHB 12/4'),
    'tau_pur_max_n7mm2': (0.04, 'N/mm2', 'allowed shear stress of the PUR foam', 'isoplus PHB 9/12'),
    'pressure_max_bar': (25.0, 'bar', 'nominal pressure of the rigid system', 'isoplus PHB 12/4'),
    'stress_range_allow_n7mm2': (None, 'N/mm2', 'allowed stress range at bends, tees and kinks', TO_CONFIRM + 'EN 13941-1'),
    'hoop_stress_allow_n7mm2': (None, 'N/mm2', 'allowed hoop stress', TO_CONFIRM + 'EN 13941-1'),
    'buckling_safety': (None, '-', 'required safety against upheaval buckling', TO_CONFIRM + 'FW 401'),
    'cold_laying_max_single_c': (85.0, 'degC', 'highest temperature of cold laying without length limit, single pipe', 'isoplus PHB 12/2'),
    'cold_laying_max_twin_c': (70.0, 'degC', 'highest temperature of cold laying without length limit, twin pipe', 'isoplus PHB 12/2'),
    'movement_prestress_mm': (80.0, 'mm', 'leg movement above which the legs must be prestressed', 'isoplus PHB 12/4'),
    'pad_layer_mm': (40.0, 'mm', 'thickness of one pad layer', 'isoplus PHB 7/8'),
    'pad_piece_m': (1.0, 'm', 'length of one pad piece', 'isoplus PHB 7/8'),
    'pad_max_thickness_mm': (120.0, 'mm', 'largest pad thickness (casing at most 60 degC)', 'isoplus PHB 12/4'),
    'pad_max_compression': (0.5, '-', 'largest pad compression', 'isoplus PHB 7/9 (curve ends at 50 %)'),
    'element_length_m': (1.0, 'm', 'largest FE element length', 'solver'),
    'load_increment_k': (10.0, 'K', 'largest temperature increment of a load step', 'solver'),
    'max_iterations': (50.0, '-', 'largest number of iterations per increment', 'solver'),
}

LAYING_METHODS = ('cold', 'conventional', 'thermal_prestress', 'one_time_compensator', 'self_prestress')
SOURCE_PARAMETER, SOURCE_SECTION, SOURCE_SIMULATION = 'parameter', 'section', 'simulation'


def confirmed(params, sources, key):
    """True when the limit has a value and its source is not 'to be confirmed'."""
    return params.get(key) is not None and not (sources.get(key) or '').startswith(TO_CONFIRM)


def sectionValue(override, column, params, key):
    """(value, source) of a section override column, else the parameter."""
    if override and override.get(column) is not None:
        return float(override[column]), SOURCE_SECTION
    return params.get(key), SOURCE_PARAMETER


# ---------------------------------------------------------------- loads (D2)
def pipeLoads(params, override, sequences, sim_temp, sim_pressure, line_id):
    """Temperature per carrier and pressure of a pipe row with their sources: the higher of the design value and
    the simulated maximum. sim_temp / sim_pressure: {(line id, sequence): max} (degC, Pa)."""
    t_design, t_src = sectionValue(override, 'design_temperature_c', params, 'design_temperature_c')
    p_design, p_src = sectionValue(override, 'design_pressure_bar', params, 'design_pressure_bar')
    temps, t_sources = [], []
    for seq in sequences:
        sim = sim_temp.get((line_id, seq))
        if sim is not None and sim > t_design:
            temps.append(sim)
            t_sources.append(SOURCE_SIMULATION)
        else:
            temps.append(t_design)
            t_sources.append(t_src)
    p = p_design * 1e5
    p_source = p_src
    sims = [sim_pressure.get((line_id, s)) for s in sequences]
    sims = [s for s in sims if s is not None]
    if sims and max(sims) > p:
        p, p_source = max(sims), SOURCE_SIMULATION
    return {'temps': temps, 'temp_sources': t_sources, 'pressure': p, 'pressure_source': p_source,
            'simulated': any(s == SOURCE_SIMULATION for s in t_sources) or bool(sims)}


# ---------------------------------------------------------------- laying methods (D6)
def stressFreeTemperature(method, t_laying, t_design, t_preheat=None):
    """Temperature at which the section is stress-free; None for a method that is not calculated."""
    if method in (None, '', 'cold', 'conventional'):
        return t_laying
    if method in ('thermal_prestress', 'one_time_compensator'):
        return t_preheat if t_preheat is not None else (t_laying + t_design) / 2.0
    return None


def fictitiousPreheat(t_laying, t_operating):
    """VTf = T_E + (T_B - T_E) / 3 for prestressed legs and pads (isoplus PHB 10/31)."""
    return t_laying + (t_operating - t_laying) / 3.0


def layingFindings(method, t_max, twin, params, leg_movement_mm, prestressed_legs):
    """Findings of the laying method of one section: unknown or unsupported method, cold laying too hot, movement
    that needs prestressed legs."""
    out = []
    if method not in (None, '') and method not in LAYING_METHODS:
        out.append(('laying_method_unknown', 'error', {'method': method}))
    elif method == 'self_prestress':
        out.append(('laying_method_unsupported', 'error', {'method': method}))
    if method == 'cold':
        key = 'cold_laying_max_twin_c' if twin else 'cold_laying_max_single_c'
        if params.get(key) is not None and t_max > params[key]:
            out.append(('cold_laying_too_hot', 'error', {'value': t_max, 'limit': params[key], 'key': key}))
    if (leg_movement_mm is not None and not prestressed_legs and params.get('movement_prestress_mm') is not None
            and leg_movement_mm > params['movement_prestress_mm']):
        out.append(('legs_need_prestress', 'warning', {'value': leg_movement_mm, 'limit': params['movement_prestress_mm']}))
    return out


def compensatorTravel(alpha, t_preheat, t_laying, length_left, length_right):
    """Travel a one-time compensator takes until the preheating temperature: the free expansion of half of the
    restrained pipe on each side."""
    return alpha * (t_preheat - t_laying) * (length_left + length_right) / 2.0


def compensatorFindings(travel_m, max_travel_m, in_restrained_zone, straight_left, straight_right, in_bend, ends_ok):
    out = []
    if max_travel_m is not None and travel_m > max_travel_m:
        out.append(('compensator_travel', 'error', {'value': travel_m * 1000, 'limit': max_travel_m * 1000}))
    if not in_restrained_zone:
        out.append(('compensator_not_restrained', 'error', {}))
    if min(straight_left, straight_right) < 6.0:
        out.append(('compensator_straight_length', 'error', {'value': min(straight_left, straight_right), 'limit': 6.0}))
    if in_bend:
        out.append(('compensator_in_bend', 'error', {}))
    if not ends_ok:
        out.append(('compensator_stretch_ends', 'error', {}))
    return out


# ---------------------------------------------------------------- checks (D9)
def utilisation(value, limit):
    return abs(value) / limit if limit else None


def check(rule, value, params, sources, key, yield_strength=None, limit=None, limit_source=None):
    """A check result: verdict when the limit has a confirmed source, otherwise utilisation against Re.
    limit/limit_source override the parameter (e.g. the series' allowed axial stress)."""
    if limit is None:
        limit = params.get(key)
        limit_source = sources.get(key)
        ok_source = confirmed(params, sources, key)
    else:
        ok_source = bool(limit_source) and not limit_source.startswith(TO_CONFIRM)
    if limit is not None and ok_source:
        u = utilisation(value, limit)
        return {'rule': rule, 'value': value, 'limit': limit, 'source': limit_source, 'utilisation': u,
                'verdict': 'pass' if u <= 1.0 + 1e-9 else 'fail'}
    u = utilisation(value, yield_strength) if yield_strength else None
    return {'rule': rule, 'value': value, 'limit': limit, 'source': limit_source or sources.get(key), 'utilisation': u,
            'verdict': 'not confirmed'}


def purShear(friction_n_m, steel_outer_diameters):
    """Shear stress of the PUR foam at the steel pipe(s) from the axial friction, N/mm2. The inner interface governs:
    with it the maximum cover of isoplus PHB 9/12 is reproduced, with the casing it is not."""
    return friction_n_m / (math.pi * sum(steel_outer_diameters)) / 1e6


def minimumCoverCheck(cover, d_outer_m, twin, traffic_load):
    """Check of the minimum cover of PHB 9/11; None when the DN is outside the table."""
    limit = cat.minimumCover(cat.nominalDiameter(d_outer_m), twin, traffic_load)
    if limit is None:
        return None
    return {'rule': 'cover_minimum', 'value': cover, 'limit': limit, 'source': cat.SOURCE_MIN_COVER,
            'utilisation': limit / cover if cover > 0 else float('inf'), 'verdict': 'pass' if cover >= limit - 1e-9 else 'fail'}


# ---------------------------------------------------------------- pads (D8)
def padThickness(movement_m, params):
    """Pad thickness (m) for a lateral movement: layers until the compression stays within the maximum."""
    layer = params['pad_layer_mm'] / 1000.0
    need = abs(movement_m) / params['pad_max_compression']
    return layer * max(1, math.ceil(need / layer - 1e-9))


def padRuns(positions, movements, threshold, params):
    """Pads along one leg: positions (m along the leg, ascending) with lateral movements; the stretch where the
    movement exceeds the threshold, in whole pieces, with the thickness for its largest movement. Returns
    (start m, length m, thickness m) or None."""
    over = [(s, abs(m)) for s, m in zip(positions, movements) if abs(m) > threshold]
    if not over:
        return None
    piece = params['pad_piece_m']
    start, end = min(s for s, _ in over), max(s for s, _ in over)
    length = piece * max(1, math.ceil((end - start) / piece - 1e-9))
    return start, length, padThickness(max(m for _, m in over), params)
