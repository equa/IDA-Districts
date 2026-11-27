#calculation of the rigid steel pipes of a version's statics model (change statics-steel-solver): read the model and
#the results of the simulation, build the FE problem, solve each part, check, write the result tables
import json
import math
import re
from collections import OrderedDict
from typing import Any, Optional

from . import statics_catalog as cat
from . import statics_checks as sc
from . import statics_db as sdb
from . import statics_fe as fe
from . import statics_model as sm

TEE_TYPES = ('tee', 'cross', 'y_connector')
CASE_MAX, CASE_MIN = 'mu_max', 'mu_min'


class Refused(Exception):
    """The calculation cannot start (model missing or out of date); the text says why."""


# ---------------------------------------------------------------- inputs
def simulatedMaxima(cur, schema, var):
    """{(line id, sequence): maximum} over all times and segments of line_s_<var>$<seq>, including the tables of a
    period run (<table>_period<k>); temperature as is, pressure as absolute value."""
    cur.execute("""SELECT table_name FROM information_schema.tables WHERE table_schema = %s AND table_name LIKE %s;""",
                (schema, 'line\\_s\\_{}$%'.format(var)))
    out = {}
    for row in cur.fetchall():
        m = re.match(r'line_s_{}\$(\d+)(_period\d+)?$'.format(var), row['table_name'])
        if not m:
            continue
        seq = int(m.group(1))
        agg = 'max("${}")'.format(var) if var == 'temp' else 'max(abs("${}"))'.format(var)
        cur.execute('SELECT fid, {} AS v FROM "{}"."{}" GROUP BY fid;'.format(agg, schema, row['table_name']))  # nosec B608
        for r in cur.fetchall():
            if r['v'] is not None:
                key = (r['fid'], seq)
                out[key] = max(out.get(key, float('-inf')), float(r['v']))
    return out


def readInputs(cur, schema):
    """Everything the calculation needs, as plain dicts. Raises Refused when the model is not current."""
    state = sdb.modelState(cur, schema)
    if state != sdb.STATE_CURRENT:
        raise Refused(state)
    params, sources = sdb.readParameters(cur, with_sources=True)
    cur.execute("""SELECT id, ST_X(geom) AS x, ST_Y(geom) AS y, ST_Z(geom) AS z, kind, junction_type, angle_deg, bend_class,
        radius_m, override_kind, {} FROM "{}".statics_model_nodes;""".format(', '.join(sdb.POINT_OVERRIDE_COLUMNS), schema))  # nosec B608
    nodes = {r['id']: r for r in cur.fetchall()}
    cur.execute("""SELECT id, line_id, node_from, node_to, length_m, {} FROM "{}".statics_model_sections;""".format(
        ', '.join(sdb.SECTION_OVERRIDE_COLUMNS), schema))  # nosec B608
    sections = {r['id']: r for r in cur.fetchall()}
    cur.execute("""SELECT id, section_id, line_id, sequences, pipe_ids, twin, system_type, series_id, d_inner_m, d_outer_m,
        wall_m, casing_d_m, cover_m, x_m, y_m FROM "{}".statics_model_pipes ORDER BY id;""".format(schema))  # nosec B608
    pipes = cur.fetchall()
    cur.execute("""SELECT p.id, m.youngs_modulus_n7mm2 AS e, m.thermal_expansion_17kelvin AS alpha, m.yield_strength_n7mm2 AS re,
        m.poissons_ratio AS nu, m.density_kg7m3 AS rho
        FROM public.pipes p
        JOIN public.pipe_layers pl ON pl.pipe_construction_id = p.pipe_construction_id
        JOIN public.materials m ON m.id = pl.materialid
        WHERE pl.sequence = (SELECT min(sequence) FROM public.pipe_layers WHERE pipe_construction_id = p.pipe_construction_id);""")
    materials = {r['id']: r for r in cur.fetchall()}
    cur.execute("""SELECT id, sigma_ax_max_n7mm2 FROM public.pipe_series;""")
    series = {r['id']: r['sigma_ax_max_n7mm2'] for r in cur.fetchall()}
    cur.execute("""SELECT l.id AS lid, bp.sequence, bp.x, bp.y FROM "{}".lines l
        JOIN public.bundle_pipes bp ON bp.pipe_bundle_type_id = l.pipe_bundle_type_id;""".format(schema))  # nosec B608
    positions = {(r['lid'], r['sequence']): (float(r['x'] or 0), float(r['y'] or 0)) for r in cur.fetchall()}
    return {'params': params, 'sources': sources, 'nodes': nodes, 'sections': sections, 'pipes': pipes,
            'materials': materials, 'series': series, 'positions': positions,
            'sim_temp': simulatedMaxima(cur, schema, 'temp'), 'sim_p': simulatedMaxima(cur, schema, 'p')}


# ---------------------------------------------------------------- problem
def _f(v, default=None):
    return float(v) if v is not None else default


def groupPoints(pipes, nodes_of):
    """FE point key per (pipe row, route node): pipes meeting at a node are joined when their sequences intersect
    (the network model connects the bundles by sequence). nodes_of: {pipe id: (node_from, node_to)}."""
    at = {}
    for p in pipes:
        for n in nodes_of[p['id']]:
            at.setdefault(n, []).append(p)
    key = {}
    for n, rows in at.items():
        groups = []
        for p in rows:
            seqs = set(p['sequences'])
            hit = [g for g in groups if g[0] & seqs]
            merged = (set(seqs), [p['id']])
            for g in hit:
                merged[0].update(g[0])
                merged[1].extend(g[1])
                groups.remove(g)
            groups.append(merged)
        for seqs, ids in groups:
            rep = min(ids)
            for pid in ids:
                key[(pid, n)] = (n, rep)
    return key


def buildProblem(data):
    """Members and points of the FE problem with their meta data, and the findings found before solving."""
    params, sources = data['params'], data['sources']
    nodes, sections = data['nodes'], data['sections']
    findings, skipped = [], OrderedDict()
    nodes_of = {p['id']: (sections[p['section_id']]['node_from'], sections[p['section_id']]['node_to']) for p in data['pipes']}
    keys = groupPoints(data['pipes'], nodes_of)
    rigid_keys, other_keys = set(), set()
    members = []
    for p in data['pipes']:
        sec = sections[p['section_id']]
        if not sm.isRigid(p['system_type']):
            skipped.setdefault(p['line_id'], 'not a rigid steel pipe ({})'.format(p['system_type']))
            other_keys.update(keys[(p['id'], n)] for n in nodes_of[p['id']])
            continue
        mats = [data['materials'].get(pid) for pid in p['pipe_ids']]
        if any(m is None or m['e'] is None or m['alpha'] is None for m in mats):
            skipped.setdefault(p['line_id'], 'no mechanical values of the steel')
            continue
        method = sec.get('laying_method') or 'conventional'
        t_lay, _ = sc.sectionValue(sec, 'laying_temperature_c', params, 'laying_temperature_c')
        t_design, _ = sc.sectionValue(sec, 'design_temperature_c', params, 'design_temperature_c')
        loads = sc.pipeLoads(params, sec, p['sequences'], data['sim_temp'], data['sim_p'], p['line_id'])
        t0 = sc.stressFreeTemperature(method, t_lay, t_design, _f(sec.get('preheat_temperature_c')))
        for rule, severity, values in sc.layingFindings(method, max(loads['temps']), p['twin'], params, None, True):
            findings.append({'rule': rule, 'severity': severity, 'model_pipe_id': p['id'], 'line_id': p['line_id'], 'values': values})
        if t0 is None:
            skipped.setdefault(p['line_id'], 'laying method {} not calculated'.format(method))
            continue
        positions = [data['positions'].get((p['line_id'], s), (0.0, 0.0)) for s in p['sequences']]
        mx = sum(x for x, _ in positions) / len(positions)
        my = sum(y for _, y in positions) / len(positions)
        carriers = []
        for k, m in enumerate(mats):
            carriers.append({'E': float(m['e']) * 1e6, 'alpha': float(m['alpha']), 'nu': _f(m['nu'], 0.3),
                             'rho': _f(m['rho'], 7850.0), 're': _f(m['re']) and float(m['re']) * 1e6,
                             'd_o': float(p['d_outer_m'][k]), 'wall': float(p['wall_m'][k]),
                             # depth y grows downwards; the local z points up
                             'y': positions[k][0] - mx if p['twin'] else 0.0, 'z': -(positions[k][1] - my) if p['twin'] else 0.0})
        sigma_allow = data['series'].get(p['series_id'])
        members.append({
            'id': p['id'], 'from': keys[(p['id'], sec['node_from'])], 'to': keys[(p['id'], sec['node_to'])],
            'model_pipe_id': p['id'], 'line_id': p['line_id'], 'section_id': sec['id'], 'twin': bool(p['twin']),
            'carriers': carriers, 'casing_d': float(p['casing_d_m']), 'cover': float(p['cover_m']),
            'gamma': sc.sectionValue(sec, 'soil_unit_weight_kn_m3', params, 'soil_unit_weight_kn_m3')[0],
            'phi': sc.sectionValue(sec, 'friction_angle_deg', params, 'friction_angle_deg')[0],
            'groundwater': _f(sec.get('groundwater_depth_m')),
            'mu_max': sc.sectionValue(sec, 'friction_coefficient', params, 'friction_max')[0],
            'mu_min': sc.sectionValue(sec, 'friction_coefficient_min', params, 'friction_min')[0],
            'traffic': sc.sectionValue(sec, 'traffic_load_kn_m2', params, 'traffic_load_kn_m2')[0],
            'loads': loads, 't_lay': t_lay, 't0': t0, 'method': method, 'prestressed_legs': bool(sec.get('prestressed_legs')),
            't_preheat': t0 if method in ('thermal_prestress', 'one_time_compensator') else None,
            'sigma_allow': (float(sigma_allow) * 1e6, 'pipe series') if sigma_allow is not None else None,
        })
        rigid_keys.update([members[-1]['from'], members[-1]['to']])
    points = {}
    for key in rigid_keys:
        n = nodes[key[0]]
        bend = None
        if n['bend_class'] in (sm.BEND_PREFAB, sm.BEND_KINK, sm.BEND_ELASTIC):
            bend = {'class': n['bend_class'], 'radius': _f(n['radius_m']), 'angle': _f(n['angle_deg'], 0.0)}
        pt = {'xyz': (float(n['x']), float(n['y']), float(n['z'] or 0.0)), 'bend': bend,
              'tee': n['junction_type'] in TEE_TYPES, 'fixed': n['override_kind'] == 'fixed_point',
              'node_id': key[0], 'override_kind': n['override_kind'], 'node': n}
        points[key] = pt
    for key in rigid_keys & other_keys:
        findings.append({'rule': 'connection_not_calculated', 'severity': 'warning', 'model_node_id': key[0], 'values': {}})
    #compensators: the axial spring of the point, or of the isoplus one-time compensator table by DN
    incident = {}
    for mi, m in enumerate(members):
        incident.setdefault(m['from'], []).append(mi)
        incident.setdefault(m['to'], []).append(mi)
    for key, pt in points.items():
        if pt['override_kind'] != 'compensator':
            continue
        n = pt['node']
        rate = _f(n.get('spring_rate_n_mm'))
        if rate is None and incident.get(key):
            row = cat.oneTimeCompensator(cat.nominalDiameter(members[incident[key][0]]['carriers'][0]['d_o']))
            rate = row[1] / 1000.0 if row else None
        if rate is None:
            findings.append({'rule': 'compensator_without_spring_rate', 'severity': 'warning', 'model_node_id': key[0], 'values': {}})
        else:
            pt['link'] = {'k_axial': rate * 1000.0}
    return {'members': members, 'points': points, 'incident': incident, 'findings': findings, 'skipped': skipped}


def partsOf(problem):
    """Connected parts as lists of member indexes."""
    parent = {}

    def find(a):
        while parent.setdefault(a, a) != a:
            parent[a] = parent[parent[a]]
            a = parent[a]
        return a
    for m in problem['members']:
        ra, rb = find(m['from']), find(m['to'])
        if ra != rb:
            parent[ra] = rb
    groups = OrderedDict()
    for mi, m in enumerate(problem['members']):
        groups.setdefault(find(m['from']), []).append(mi)
    return list(groups.values())


# ---------------------------------------------------------------- solving one part
def feMembers(problem, part, mu_key, pads=None, prestress_legs=False):
    """Member dicts for statics_fe with soil of the friction case; prestress_legs: stress-free at VTf where the
    section has prestressed legs (design of legs and pads, isoplus PHB 10/31)."""
    params = problem['params']
    out = []
    for mi in part:
        m = problem['members'][mi]
        weight = fe.pipeWeight(m['carriers'], m['casing_d'])
        soil = fe.soil(m['cover'], m['casing_d'], weight, m[mu_key], m['gamma'], m['phi'], m['groundwater'],
                       params['axial_slip_m'], params['lateral_slip_m'])
        t0 = m['t0']
        if prestress_legs and m['prestressed_legs']:
            t0 = sc.fictitiousPreheat(m['t_lay'], max(m['loads']['temps']))
        out.append({'id': m['id'], 'from': m['from'], 'to': m['to'], 'section': fe.section(m['carriers']),
                    'casing_d': m['casing_d'], 'soil': soil, 't0': [t0] * len(m['carriers']),
                    'pad_runs': (pads or {}).get(mi, ()), 'index': mi})
    return out


def states(problem, part):
    heat = {'temps': {}, 'p': {}}
    cool = {'temps': {}, 'p': {}}
    for k, mi in enumerate(part):
        m = problem['members'][mi]
        heat['temps'][k] = list(m['loads']['temps'])
        cool['temps'][k] = [m['t_lay']] * len(m['carriers'])
        heat['p'][k] = cool['p'][k] = m['loads']['pressure']
    return [heat, cool, heat]


def solvePart(problem, part, mu_key, pads=None, prestress_legs=False, cancelled=None):
    params = problem['params']
    fem = feMembers(problem, part, mu_key, pads, prestress_legs)
    pts = {}
    for m in fem:
        for key in (m['from'], m['to']):
            pts[key] = problem['points'][key]
    mesh = fe.Mesh(pts, fem, params['element_length_m'] or 1.0)
    fixed = [k for k, p in pts.items() if p.get('fixed')]
    model = fe.Model(mesh, fixed_points=fixed, pad_strain=cat.padStrain)
    res = model.solve(states(problem, part), increment=params['load_increment_k'] or 10.0,
                      max_iterations=int(params['max_iterations'] or 50), cancelled=cancelled)
    return model, res


def placePads(problem, part, model, res):
    """{member index: [(start, length, thickness)]} where the lateral movement with the lower friction exceeds the
    movement at which the soil reaches its limit."""
    params = problem['params']
    mesh = model.mesh
    lateral: Any = None
    for st in res['states']:
        lat = abs(st['u_local'][:, 1])
        lateral = lat if lateral is None else lateral.clip(min=lat)
    pads = {}
    by_member = {}
    for e, (a, b) in enumerate(mesh.el_nodes):
        k = mesh.el_member[e]
        s = fe.elementPosition(mesh, e, mesh.members[k])
        by_member.setdefault(k, []).append((s, max(lateral[a], lateral[b])))
    for k, rows in by_member.items():
        rows.sort()
        run = sc.padRuns([r[0] for r in rows], [r[1] for r in rows], params['lateral_slip_m'], params)
        if run:
            pads[part[k]] = [run]
    return pads


# ---------------------------------------------------------------- checks
def elementChecks(problem, m, kind, carrier, c_res, stress_range):
    """Check results of one element and carrier (stresses in Pa)."""
    params, sources = problem['params'], problem['sources']
    re_ = carrier.get('re')
    out = []
    if kind == 'pipe':
        if m['sigma_allow']:
            out.append(sc.check('axial_stress', abs(c_res['sigma_ax']) / 1e6, params, sources, 'sigma_ax_allow_n7mm2',
                                re_ and re_ / 1e6, limit=m['sigma_allow'][0] / 1e6, limit_source=m['sigma_allow'][1]))
        else:
            out.append(sc.check('axial_stress', abs(c_res['sigma_ax']) / 1e6, params, sources, 'sigma_ax_allow_n7mm2', re_ and re_ / 1e6))
    else:
        out.append(sc.check('stress_range', stress_range / 1e6, params, sources, 'stress_range_allow_n7mm2', re_ and re_ / 1e6))
    out.append(sc.check('hoop_stress', abs(c_res['sigma_hoop']) / 1e6, params, sources, 'hoop_stress_allow_n7mm2', re_ and re_ / 1e6))
    return out


def governing(checks):
    verdicts = [c for c in checks if c['verdict'] in ('pass', 'fail') and c['utilisation'] is not None]
    pool = verdicts or [c for c in checks if c['utilisation'] is not None]
    if not pool:
        return None, None, None
    g = max(pool, key=lambda c: c['utilisation'])
    return g['utilisation'], g['rule'], g['verdict']


def memberChecks(problem, m):
    """Checks per member that do not need the FE results: PUR shear, minimum cover, pressure."""
    params, sources = problem['params'], problem['sources']
    weight = fe.pipeWeight(m['carriers'], m['casing_d'])
    soil = fe.soil(m['cover'], m['casing_d'], weight, m['mu_max'], m['gamma'], m['phi'], m['groundwater'])
    out = [sc.check('pur_shear', sc.purShear(soil['f_ax'], [c['d_o'] for c in m['carriers']]), params, sources, 'tau_pur_max_n7mm2')]
    cover = sc.minimumCoverCheck(m['cover'], m['carriers'][0]['d_o'], m['twin'], m['traffic'])
    if cover:
        out.append(cover)
    out.append(sc.check('pressure', m['loads']['pressure'] / 1e5, params, sources, 'pressure_max_bar'))
    return out


def walk(problem, start_key, first_member):
    """Length along the route from a point through straight points until a bend, tee, fixed point, compensator or
    free end; returns (length, stop kind)."""
    members, points, incident = problem['members'], problem['points'], problem['incident']
    length, key, mi = 0.0, start_key, first_member
    for _ in range(100000):
        m = members[mi]
        other = m['to'] if m['from'] == key else m['from']
        a, b = points[key]['xyz'], points[other]['xyz']
        length += math.dist(a, b)
        pt = points[other]
        nxt = [i for i in incident.get(other, []) if i != mi]
        if pt.get('fixed'):
            return length, 'fixed'
        if pt['override_kind'] in ('compensator', 'one_time_compensator'):
            return length, 'compensator'
        if not nxt:
            return length, 'end'
        if len(nxt) > 1 or pt['tee']:
            return length, 'bend'
        if pt['bend'] and pt['bend']['class'] in (sm.BEND_PREFAB, sm.BEND_KINK):
            return length, 'bend'
        key, mi = other, nxt[0]
    return length, 'end'


def compensatorChecks(problem, key, restrained):
    params = problem['params']
    pt = problem['points'][key]
    mems = problem['incident'].get(key, [])
    if len(mems) != 2:
        return [('compensator_stretch_ends', 'error', {})]
    (l1, s1), (l2, s2) = walk(problem, key, mems[0]), walk(problem, key, mems[1])
    m = problem['members'][mems[0]]
    c = m['carriers'][0]
    t_pre = m['t_preheat'] if m['t_preheat'] is not None else (m['t_lay'] + max(m['loads']['temps'])) / 2.0
    travel = sc.compensatorTravel(c['alpha'], t_pre, m['t_lay'], l1, l2)
    n = pt['node']
    max_travel: Optional[float] = None
    if n.get('max_travel_mm') is not None:
        max_travel = float(n['max_travel_mm']) / 1000.0
    else:
        row = cat.oneTimeCompensator(cat.nominalDiameter(c['d_o']))
        max_travel = row[0] if row else None
    in_bend = bool(pt['bend'] and pt['bend']['class'] in (sm.BEND_PREFAB, sm.BEND_KINK))
    return sc.compensatorFindings(travel, max_travel, restrained, l1, l2, in_bend, s1 != 'end' and s2 != 'end')


# ---------------------------------------------------------------- calculation
def calculate(cur, schema, progress=None, cancelled=None):
    """Calculates the version and writes the results; returns the summary. Raises Refused when the model is not
    current. A cancelled or failed calculation writes nothing."""
    data = readInputs(cur, schema)
    problem = buildProblem(data)
    problem['params'], problem['sources'] = data['params'], data['sources']
    params = data['params']
    parts = partsOf(problem)
    findings = list(problem['findings'])
    element_rows, node_rows, pad_list, not_converged = [], [], [], []
    total = max(1, len(parts))
    for pi, part in enumerate(parts):
        if cancelled is not None and cancelled():
            return None
        #lower friction: displacements, legs and pads; then the upper friction with the pads for the stresses
        model_min, res_min = solvePart(problem, part, 'mu_min', None, True, cancelled)
        pads = {}
        if res_min['converged']:
            for _ in range(5):
                new = placePads(problem, part, model_min, res_min)
                if new == pads:
                    break
                pads = new
                model_min, res_min = solvePart(problem, part, 'mu_min', pads, True, cancelled)
                if not res_min['converged']:
                    break
        model_max, res_max = solvePart(problem, part, 'mu_max', pads, False, cancelled)
        if res_max.get('message') == 'cancelled' or res_min.get('message') == 'cancelled':
            return None
        if not (res_min['converged'] and res_max['converged']):
            not_converged.append({'members': [problem['members'][i]['model_pipe_id'] for i in part],
                                  'message': res_max['message'] or res_min['message']})
            findings.append({'rule': 'not_converged', 'severity': 'error',
                             'model_pipe_id': problem['members'][part[0]]['model_pipe_id'],
                             'values': {'message': res_max['message'] or res_min['message']}})
            continue
        for mi, runs in pads.items():
            for start, length, thickness in runs:
                m = problem['members'][mi]
                pad_list.append({'model_pipe_id': m['model_pipe_id'], 'line_id': m['line_id'], 'start_m': start,
                                 'length_m': length, 'thickness_mm': thickness * 1000})
                if params['pad_max_thickness_mm'] is not None and thickness * 1000 > params['pad_max_thickness_mm']:
                    findings.append({'rule': 'pad_too_thick', 'severity': 'error', 'model_pipe_id': m['model_pipe_id'],
                                     'line_id': m['line_id'], 'values': {'value': thickness * 1000,
                                     'limit': params['pad_max_thickness_mm'], 'source': data['sources'].get('pad_max_thickness_mm')}})
        _collect(problem, part, model_max, res_max, CASE_MAX, pads, element_rows, node_rows, findings)
        _collect(problem, part, model_min, res_min, CASE_MIN, pads, element_rows, node_rows, findings)
        if progress is not None:
            progress(100.0 * (pi + 1) / total)
    for m in problem['members']:
        for chk in memberChecks(problem, m):
            if chk['verdict'] == 'fail':
                findings.append({'rule': chk['rule'], 'severity': 'error', 'model_pipe_id': m['model_pipe_id'],
                                 'line_id': m['line_id'], 'values': _values(chk)})
    summary = {'parts': len(parts), 'members': len(problem['members']), 'elements': len(element_rows),
               'skipped_lines': [{'line_id': k, 'reason': v} for k, v in problem['skipped'].items()],
               'not_converged': not_converged, 'pads': pad_list,
               'findings_by_rule': _countRules(findings), 'fatigue_checked': False,
               'twin_without_results': any(m['twin'] and not m['loads']['simulated'] for m in problem['members']),
               'parameters': {k: {'value': v, 'source': data['sources'].get(k)} for k, v in params.items()}}
    return {'summary': summary, 'element_rows': element_rows, 'node_rows': node_rows, 'findings': findings,
            'model_fingerprint': sdb.lastBuild(cur, schema)['fingerprint'], 'solver_fingerprint': sdb.solverFingerprint(cur, schema)}


def _values(chk):
    return {'value': chk['value'], 'limit': chk['limit'], 'source': chk['source'], 'utilisation': chk['utilisation']}


def _countRules(findings):
    out = OrderedDict()
    for f in findings:
        out[f['rule']] = out.get(f['rule'], 0) + 1
    return out


def _collect(problem, part, model, res, case, pads, element_rows, node_rows, findings):
    """Result rows of one part and friction case, and the findings of the element checks (worst per member)."""
    mesh = model.mesh
    members = problem['members']
    worst = {}
    heat, cool = res['states'][0], res['states'][1]
    for e, (a, b) in enumerate(mesh.el_nodes):
        k = mesh.el_member[e]
        m = members[part[k]]
        kind = mesh.el_kind[e]
        for ci, carrier in enumerate(m['carriers']):
            f1, f2 = heat['elements'][e]['carriers'][ci]['fibres'], cool['elements'][e]['carriers'][ci]['fibres']
            stress_range = max(abs(x - y) for x, y in zip(f1, f2))
            for step, st in zip(fe.STEP_NAMES, res['states']):
                c_res = st['elements'][e]['carriers'][ci]
                checks = elementChecks(problem, m, kind, carrier, c_res, stress_range) if case == CASE_MAX else []
                util, rule, verdict = governing(checks)
                element_rows.append((mesh.xyz[a], mesh.xyz[b], m['model_pipe_id'], ci + 1, step, case, kind,
                                     mesh.el_i[e], c_res['sigma_ax'] / 1e6, c_res['sigma_b'] / 1e6,
                                     c_res['sigma_hoop'] / 1e6, c_res['sigma_eq'] / 1e6, stress_range / 1e6, util, rule))
                for chk in checks:
                    if chk['verdict'] == 'fail':
                        key = (chk['rule'], m['model_pipe_id'])
                        if key not in worst or chk['utilisation'] > worst[key]['utilisation']:
                            worst[key] = dict(chk, line_id=m['line_id'])
    for (rule, pid), chk in worst.items():
        findings.append({'rule': rule, 'severity': 'error', 'model_pipe_id': pid, 'line_id': chk['line_id'], 'values': _values(chk)})
    #nodes: model node where the FE node is a route point
    node_member = {}
    for e, (a, b) in enumerate(mesh.el_nodes):
        node_member.setdefault(a, part[mesh.el_member[e]])
        node_member.setdefault(b, part[mesh.el_member[e]])
    pad_at = {}
    for e, (a, b) in enumerate(mesh.el_nodes):
        mi = part[mesh.el_member[e]]
        for start, length, thickness in pads.get(mi, ()):
            s = fe.elementPosition(mesh, e, mesh.members[mesh.el_member[e]])
            if start - 1e-6 <= s <= start + length + 1e-6:
                for nd in (a, b):
                    pad_at[nd] = (thickness * 1000, length)
    for nd in range(model.n):
        point = mesh.node_point[nd]
        model_node = point[0] if isinstance(point, tuple) and len(point) == 2 and point[0] != 't' else None
        mi = node_member.get(nd)
        pid = members[mi]['model_pipe_id'] if mi is not None else None
        pad = pad_at.get(nd, (None, None))
        for step, st in zip(fe.STEP_NAMES, res['states']):
            u, ul, fl = st['u'][nd], st['u_local'][nd], st['spring_local'][nd]
            node_rows.append((mesh.xyz[nd], model_node, pid, step, case, u[0] * 1000, u[1] * 1000, u[2] * 1000,
                              ul[0] * 1000, ul[1] * 1000, fl[0], pad[0], pad[1]))
    #laying: leg movement at the ends of each member (lower friction), compensators (upper friction, sticking)
    if case == CASE_MIN:
        params = problem['params']
        for k, mi in enumerate(part):
            m = members[mi]
            ends = [mesh.node_of_point.get(m['from']), mesh.node_of_point.get(m['to'])]
            movement = max(abs(heat['u_local'][nd][0]) for nd in ends if nd is not None) * 1000
            for rule, severity, values in sc.layingFindings(None, max(m['loads']['temps']), m['twin'], params,
                                                            movement, m['prestressed_legs']):
                findings.append({'rule': rule, 'severity': severity, 'model_pipe_id': m['model_pipe_id'],
                                 'line_id': m['line_id'], 'values': values})
    else:
        slip = problem['params']['axial_slip_m'] or 0.0
        keys = {mesh.members[k]['from'] for k in range(len(mesh.members))} | {mesh.members[k]['to'] for k in range(len(mesh.members))}
        for key in keys:
            pt = problem['points'][key]
            if pt['override_kind'] != 'one_time_compensator':
                continue
            nd = mesh.node_of_point.get(key)
            restrained = nd is not None and abs(heat['u_local'][nd][0]) <= slip
            for rule, severity, values in compensatorChecks(problem, key, restrained):
                findings.append({'rule': rule, 'severity': severity, 'model_node_id': key[0], 'values': values})


# ---------------------------------------------------------------- write and state
def writeResults(cur, schema, result):
    """Replaces the result tables of the version in one transaction."""
    from psycopg2.extras import execute_values
    srid = sdb.versionSrid(cur, schema)

    def pz(c):
        return 'SRID={};POINT Z ({} {} {})'.format(srid, float(c[0]), float(c[1]), float(c[2]))

    def lz(a, b):
        return 'SRID={};LINESTRING Z ({} {} {}, {} {} {})'.format(srid, *[float(v) for v in (*a, *b)])
    cur.execute('BEGIN;')
    try:
        for table in sdb.RESULT_TABLES:
            cur.execute('TRUNCATE "{}".{} RESTART IDENTITY;'.format(schema, table))  # nosec B608
        execute_values(cur, """INSERT INTO "{}".statics_result_elements (geom, model_pipe_id, carrier, load_step, friction_case,
            kind, sif, sigma_ax_n7mm2, sigma_bend_n7mm2, sigma_hoop_n7mm2, sigma_eq_n7mm2, stress_range_n7mm2, utilisation,
            governing_check) VALUES %s;""".format(schema),  # nosec B608
            [(lz(r[0], r[1]),) + tuple(_py(v) for v in r[2:]) for r in result['element_rows']],
            template='(ST_GeomFromEWKT(%s), %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)', page_size=2000)
        execute_values(cur, """INSERT INTO "{}".statics_result_nodes (geom, model_node_id, model_pipe_id, load_step, friction_case,
            ux_mm, uy_mm, uz_mm, axial_mm, lateral_mm, axial_friction_n, pad_thickness_mm, pad_length_m) VALUES %s;""".format(schema),  # nosec B608
            [(pz(r[0]),) + tuple(_py(v) for v in r[1:]) for r in result['node_rows']],
            template='(ST_GeomFromEWKT(%s), %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)', page_size=2000)
        for f in result['findings']:
            cur.execute("""INSERT INTO "{}".statics_result_findings (rule, severity, model_node_id, model_pipe_id, line_id, "values", text)
                VALUES (%s, %s, %s, %s, %s, %s, %s);""".format(schema),  # nosec B608
                        (f['rule'], f['severity'], f.get('model_node_id'), f.get('model_pipe_id'), f.get('line_id'),
                         json.dumps(f.get('values') or {}, default=_py), findingText(f)))
        cur.execute("""INSERT INTO "{}".statics_result_run (model_fingerprint, solver_fingerprint, parameters, summary, status)
            VALUES (%s, %s, %s, %s, %s);""".format(schema),  # nosec B608
                    (result['model_fingerprint'], result['solver_fingerprint'],
                     json.dumps(result['summary']['parameters'], default=_py), json.dumps(result['summary'], default=_py),
                     'partial' if result['summary']['not_converged'] else 'ok'))
        cur.execute('COMMIT;')
    except Exception:
        cur.execute('ROLLBACK;')
        raise


def _py(v):
    """numpy scalars to Python numbers for psycopg2 and json."""
    if hasattr(v, 'item'):
        return v.item()
    return v


def lastRun(cur, schema):
    cur.execute("""SELECT * FROM "{}".statics_result_run ORDER BY id DESC LIMIT 1;""".format(schema))  # nosec B608
    return cur.fetchone()


def resultState(cur, schema):
    """missing, current or out of date (the model is not current, or the model or the solver inputs changed)."""
    run = lastRun(cur, schema)
    if run is None:
        return sdb.STATE_MISSING
    build = sdb.lastBuild(cur, schema)
    if (sdb.modelState(cur, schema) != sdb.STATE_CURRENT or build is None or build['fingerprint'] != run['model_fingerprint']
            or sdb.solverFingerprint(cur, schema) != run['solver_fingerprint']):
        return sdb.STATE_OUT_OF_DATE
    return sdb.STATE_CURRENT


# ---------------------------------------------------------------- texts
def findingText(f):
    from .translations import tr_msg
    v = f.get('values') or {}
    rule = f['rule']
    where = tr_msg('line {}').format(f['line_id']) if f.get('line_id') is not None else tr_msg('node {}').format(f.get('model_node_id'))
    texts = {
        'axial_stress': tr_msg('{}: axial stress {:.0f} N/mm2 above {:.0f} N/mm2 ({}).'),
        'stress_range': tr_msg('{}: stress range {:.0f} N/mm2 above {:.0f} N/mm2 ({}).'),
        'hoop_stress': tr_msg('{}: hoop stress {:.0f} N/mm2 above {:.0f} N/mm2 ({}).'),
        'pur_shear': tr_msg('{}: PUR shear stress {:.3f} N/mm2 above {:.3f} N/mm2 ({}), the cover is too deep.'),
        'cover_minimum': tr_msg('{}: cover {:.2f} m below the minimum {:.2f} m ({}).'),
        'pressure': tr_msg('{}: pressure {:.1f} bar above {:.1f} bar ({}).'),
    }
    if rule in texts:
        return texts[rule].format(where, v.get('value') or 0, v.get('limit') or 0, v.get('source') or '')
    other = {
        'pad_too_thick': tr_msg('{}: pad of {:.0f} mm needed, more than {:.0f} mm; prestress the legs or lengthen the leg.'),
        'cold_laying_too_hot': tr_msg('{}: cold laying at {:.0f} degC above {:.0f} degC.'),
        'legs_need_prestress': tr_msg('{}: leg movement {:.0f} mm above {:.0f} mm; the legs must be prestressed.'),
        'compensator_travel': tr_msg('{}: one-time compensator travel {:.0f} mm above {:.0f} mm.'),
        'compensator_straight_length': tr_msg('{}: one-time compensator with {:.1f} m straight pipe on a side, at least {:.0f} m needed.'),
    }
    if rule in other:
        return other[rule].format(where, v.get('value') or 0, v.get('limit') or 0)
    plain = {
        'laying_method_unknown': tr_msg('{}: unknown laying method {}.').format(where, v.get('method')),
        'laying_method_unsupported': tr_msg('{}: laying method {} is not supported, the section is not calculated.').format(where, v.get('method')),
        'connection_not_calculated': tr_msg('{}: connection to a pipe that is not rigid steel, not calculated (free end).').format(where),
        'compensator_without_spring_rate': tr_msg('{}: compensator without spring rate, treated as rigid pipe.').format(where),
        'compensator_not_restrained': tr_msg('{}: one-time compensator outside the restrained zone.').format(where),
        'compensator_in_bend': tr_msg('{}: one-time compensator in a bend.').format(where),
        'compensator_stretch_ends': tr_msg('{}: one-time compensator stretch without an expansion leg or fixed point at both ends.').format(where),
        'not_converged': tr_msg('{}: the part was not calculated ({}).').format(where, v.get('message')),
    }
    return plain.get(rule, '{}: {}'.format(where, rule))


def formatReport(summary, findings):
    """(summary text, details) of a calculation for the user."""
    from .translations import tr_msg
    by_rule = summary['findings_by_rule']
    text = tr_msg('Statics calculated: {} parts, {} pipe rows, {} element results, {} findings.').format(
        summary['parts'], summary['members'], summary['elements'], sum(by_rule.values()))
    text += '\n' + tr_msg('Fatigue not checked.')
    lines = [tr_msg('Parameters') + ':']
    lines.extend('  {} = {} ({})'.format(k, '' if v['value'] is None else '{:g}'.format(v['value']), v['source'] or '')
                 for k, v in summary['parameters'].items())
    if summary['twin_without_results']:
        lines.append('')
        lines.append(tr_msg('Twin pipes without simulation results: both carriers at the design temperature, the bending from their temperature difference is not included.'))
    if summary['skipped_lines']:
        lines.append('')
        lines.append('{} ({})'.format(tr_msg('Skipped lines'), len(summary['skipped_lines'])))
        lines.extend('  ' + tr_msg('line {}: {}').format(s['line_id'], s['reason']) for s in summary['skipped_lines'])
    if summary['not_converged']:
        lines.append('')
        lines.append('{} ({})'.format(tr_msg('Parts not converged'), len(summary['not_converged'])))
        lines.extend('  {}: {}'.format(p['members'][:10], p['message']) for p in summary['not_converged'])
    if summary['pads']:
        lines.append('')
        lines.append('{} ({})'.format(tr_msg('Expansion pads'), len(summary['pads'])))
        lines.extend('  ' + tr_msg('line {}, pipe row {}: {:.0f} mm over {:.0f} m from {:.1f} m').format(
            p['line_id'], p['model_pipe_id'], p['thickness_mm'], p['length_m'], p['start_m']) for p in summary['pads'])
    if findings:
        lines.append('')
        lines.append('{} ({})'.format(tr_msg('Findings'), len(findings)))
        lines.extend('  ' + findingText(f) for f in findings)
    return text, '\n'.join(lines)
