#FE solver of the pipe statics of rigid steel pipes (change statics-steel-solver): 3D beam elements on non-linear
#soil springs, twin cross-sections, bends with flexibility and stress intensification (EN 13480-3 formulas),
#load steps with sticking/sliding friction. numpy and scipy only; no QGIS, no DB.
import math
from typing import Any

import numpy as np
from scipy import sparse
from scipy.sparse import csgraph
from scipy.sparse.linalg import spsolve

GAMMA_WATER = 10000.0     # N/m3, buoyancy below the groundwater
RHO_WATER = 1000.0
G = 9.81
STEP_NAMES = ('heat_up', 'cooling', 'reheat')


# ---------------------------------------------------------------- cross-section and soil
def carrierProps(c):
    """Area, second moment, inner area and hoop stress factor of one carrier pipe {E, alpha, nu, d_o, wall}."""
    ro, ri = c['d_o'] / 2.0, c['d_o'] / 2.0 - c['wall']
    return {'A': math.pi * (ro ** 2 - ri ** 2), 'I': math.pi / 4.0 * (ro ** 4 - ri ** 4), 'Ai': math.pi * ri ** 2,
            'ro': ro, 'ri': ri}


def hoopStress(p, c):
    """p * d_i / (2 s), Pa."""
    return p * (c['d_o'] - 2 * c['wall']) / (2.0 * c['wall'])


def pressureStrain(p, c):
    """Axial strain of a closed pipe under internal pressure; the wall then carries sigma_hoop / 2 axially."""
    return hoopStress(p, c) / c['E'] * (0.5 - c.get('nu', 0.3))


def section(carriers):
    """Section of a single pipe or a twin about its elastic centroid. carriers: [{E, alpha, nu, d_o, wall, y, z,
    rho}], y/z: offset of the carrier from the casing axis in the local horizontal/vertical direction."""
    props = [carrierProps(c) for c in carriers]
    EA = sum(c['E'] * p['A'] for c, p in zip(carriers, props))
    yc = sum(c['E'] * p['A'] * c.get('y', 0.0) for c, p in zip(carriers, props)) / EA
    zc = sum(c['E'] * p['A'] * c.get('z', 0.0) for c, p in zip(carriers, props)) / EA
    offs = [(c.get('y', 0.0) - yc, c.get('z', 0.0) - zc) for c in carriers]
    EIy = sum(c['E'] * (p['I'] + p['A'] * o[1] ** 2) for c, p, o in zip(carriers, props, offs))
    EIz = sum(c['E'] * (p['I'] + p['A'] * o[0] ** 2) for c, p, o in zip(carriers, props, offs))
    GJ = sum(c['E'] / (2 * (1 + c.get('nu', 0.3))) * 2 * p['I'] for c, p in zip(carriers, props))
    return {'carriers': carriers, 'props': props, 'offsets': offs, 'EA': EA, 'EIy': EIy, 'EIz': EIz, 'GJ': GJ}


def pipeWeight(carriers, casing_d):
    """Weight per metre (N/m) of steel, water, foam and casing; the casing wall is estimated as max(3 mm, 1.1 % Da)
    and the foam at 60 kg/m3 because the model carries no layer masses (reproduces PHB 12/4 with mu 0.40)."""
    e = max(0.003, 0.011 * casing_d)
    w = 0.0
    steel_outer = 0.0
    for c in carriers:
        p = carrierProps(c)
        w += p['A'] * c.get('rho', 7850.0) + p['Ai'] * RHO_WATER
        steel_outer += math.pi * p['ro'] ** 2
    w += math.pi / 4 * (casing_d ** 2 - (casing_d - 2 * e) ** 2) * 950.0
    w += max(0.0, math.pi / 4 * (casing_d - 2 * e) ** 2 - steel_outer) * 60.0
    return w * G


def soil(cover, casing_d, weight, mu, gamma_kn, phi_deg, groundwater=None, axial_slip=0.002, lateral_slip=0.02):
    """Soil springs per metre: axial friction limit and stiffness (FW 401: mu [(1+K0)/2 gamma Z pi Da + G]),
    lateral passive limit (K_p gamma Z Da) and stiffness, upward limit (soil above + G)."""
    gamma = gamma_kn * 1000.0
    z = cover + casing_d / 2.0
    phi = math.radians(phi_deg)
    if groundwater is not None and groundwater < z:
        sigma_v = gamma * max(groundwater, 0.0) + (gamma - GAMMA_WATER) * (z - max(groundwater, 0.0))
    else:
        sigma_v = gamma * z
    k0 = 1 - math.sin(phi)
    f_ax = mu * ((1 + k0) / 2.0 * sigma_v * math.pi * casing_d + weight)
    kp = math.tan(math.radians(45) + phi / 2.0) ** 2
    p_lat = kp * sigma_v * casing_d
    p_up = sigma_v * casing_d + weight
    return {'f_ax': f_ax, 'k_ax': f_ax / axial_slip, 'p_lat': p_lat, 'k_lat': p_lat / lateral_slip,
            'p_up': p_up, 'k_v': p_lat / lateral_slip, 'sigma_v': sigma_v, 'z': z}


def lateralCurve(p_lat, k_lat, casing_d, pad=0.0, pad_strain=None, samples=12):
    """Force-displacement points (per metre, symmetric) of the soil, with an expansion pad of thickness pad (m) in
    series; the last point is the plateau at the passive limit."""
    if pad <= 0 or pad_strain is None:
        return [(0.0, 0.0), (p_lat / k_lat, p_lat)]
    pts = [(0.0, 0.0)]
    for n in range(1, samples + 1):
        f = p_lat * n / samples
        stress = f / casing_d / 1e6                  # N/mm2 on the casing height
        pts.append((f / k_lat + pad * pad_strain(stress), f))
    return pts


# ---------------------------------------------------------------- stress intensification and flexibility
def bendFactors(d_o, wall, radius):
    """(flexibility k, stress intensification i) of a bend, EN 13480-3: h = s R / r_m^2, k = 1.65/h, i = 0.9/h^(2/3)."""
    rm = (d_o - wall) / 2.0
    h = wall * radius / rm ** 2
    return max(1.0, 1.65 / h), max(1.0, 0.9 / h ** (2.0 / 3.0))


def mitreFactor(d_o, wall, angle_deg):
    """Stress intensification of a single mitre (kink), EN 13480-3: h = (1 + cot theta) s / (2 r_m), theta half the
    deflection; never below 1."""
    theta = math.radians(max(angle_deg, 1e-6)) / 2.0
    rm = (d_o - wall) / 2.0
    h = (1 + 1 / math.tan(theta)) * wall / (2 * rm)
    return max(1.0, 0.9 / h ** (2.0 / 3.0))


def teeFactor(d_o, wall):
    """Stress intensification of an unreinforced fabricated tee, EN 13480-3: h = s / r_m."""
    rm = (d_o - wall) / 2.0
    return max(1.0, 0.9 / (wall / rm) ** (2.0 / 3.0))


# ---------------------------------------------------------------- mesh
def _unit(v):
    n = np.linalg.norm(v)
    return v / n if n > 0 else v


def localFrame(direction):
    """Rows x (axis), y (horizontal), z (vertical-ish) of the element frame."""
    x = _unit(np.asarray(direction, float))
    ref = np.array([0.0, 0.0, 1.0]) if abs(x[2]) < 0.99 else np.array([1.0, 0.0, 0.0])
    y = _unit(np.cross(ref, x))
    z = np.cross(x, y)
    return np.vstack([x, y, z])


REFINE_DISTANCE = 3.0   # m
REFINE_FACTOR = 4


def gradedStations(length, element_length, fine_start, fine_end):
    """Positions 0..length of the element nodes: element_length / REFINE_FACTOR within REFINE_DISTANCE of a fine
    end, element_length elsewhere."""
    fine = element_length / REFINE_FACTOR
    a = min(REFINE_DISTANCE, length / 2) if fine_start else 0.0
    b = length - (min(REFINE_DISTANCE, length / 2) if fine_end else 0.0)
    out = [0.0]

    def fill(x0, x1, h):
        n = max(1, int(math.ceil((x1 - x0) / h - 1e-9)))
        out.extend(x0 + (x1 - x0) * k / n for k in range(1, n + 1))
    if a > 0:
        fill(0.0, a, fine)
    if b > a + 1e-9:
        fill(a, b, element_length)
    if length > b + 1e-9:
        fill(b, length, fine)
    return out


class Mesh:
    """Nodes and elements built from route points and straight members.
    points: {pid: {'xyz', 'fixed', 'bend': {'class', 'radius', 'angle'} | None, 'tee', 'link': {'k_axial'} | None}}
    members: [{'id', 'from', 'to', 'section' (from section()), 'casing_d', 'soil' (from soil()), 'pad',
               'temps': [[T per carrier] per state], 'pressure': [p per state], 't0': [T per carrier]}]"""

    def __init__(self, points, members, element_length=1.0, arc_segments_per_90=8):
        self.points, self.members = points, members
        #lists while building, numpy arrays afterwards
        self.xyz: Any = []
        self.el_nodes: Any = []
        self.node_of_point, self.node_point = {}, []
        self.el_member, self.el_k, self.el_i, self.el_kind = [], [], [], []
        self.links = []
        self.notes = []
        self._build(element_length, arc_segments_per_90)

    def _node(self, xyz, point=None):
        if point is not None and point in self.node_of_point:
            return self.node_of_point[point]
        self.xyz.append(np.asarray(xyz, float))
        self.node_point.append(point)
        n = len(self.xyz) - 1
        if point is not None:
            self.node_of_point[point] = n
        return n

    def _build(self, element_length, arc_n90):
        incident = {}
        for mi, m in enumerate(self.members):
            incident.setdefault(m['from'], []).append(mi)
            incident.setdefault(m['to'], []).append(mi)
        #trim the members at prefabricated bends and remember the arcs
        trim = {}   # (member index, point) -> trimmed end coordinate
        arcs = []
        for pid, p in self.points.items():
            bend = p.get('bend') or {}
            mems = incident.get(pid, [])
            if bend.get('class') != 'bend' or len(mems) != 2:
                continue
            c = np.asarray(p['xyz'], float)
            ends = []
            for mi in mems:
                m = self.members[mi]
                other = m['to'] if m['from'] == pid else m['from']
                ends.append(np.asarray(self.points[other]['xyz'], float))
            d1, d2 = _unit(c - ends[0]), _unit(ends[1] - c)
            theta = math.acos(max(-1.0, min(1.0, float(np.dot(d1, d2)))))
            if theta < 1e-4:
                continue
            radius = float(bend.get('radius') or 0)
            if radius <= 0:
                continue
            l1, l2 = np.linalg.norm(c - ends[0]), np.linalg.norm(ends[1] - c)
            t = radius * math.tan(theta / 2)
            t_max = 0.45 * float(min(l1, l2))
            if t > t_max:
                self.notes.append(('bend_radius_reduced', pid, radius, t_max / math.tan(theta / 2)))
                radius, t = t_max / math.tan(theta / 2), t_max
            a, b = c - d1 * t, c + d2 * t
            trim[(mems[0], pid)], trim[(mems[1], pid)] = a, b
            n_seg = max(2, int(math.ceil(theta / (math.pi / 2) * arc_n90)))
            arcs.append((pid, mems, a, b, d1, d2, theta, radius, n_seg))
        #straight members, finer within REFINE_DISTANCE of bends, tees and points (the bending length of the soil
        #reaction near a bend is about one metre)
        def special(pid, mi):
            p = self.points[pid]
            bend = (p.get('bend') or {}).get('class')
            return ((mi, pid) in trim or bend in ('bend', 'kink') or p.get('tee') or p.get('fixed') or p.get('link')
                    or len(incident.get(pid, [])) != 2)
        for mi, m in enumerate(self.members):
            pa = np.asarray(self.points[m['from']]['xyz'], float)
            pb = np.asarray(self.points[m['to']]['xyz'], float)
            na = self._node(pa, m['from']) if (mi, m['from']) not in trim else self._node(trim[(mi, m['from'])], ('t', mi, m['from']))
            nb = self._node(pb, m['to']) if (mi, m['to']) not in trim else self._node(trim[(mi, m['to'])], ('t', mi, m['to']))
            a, b = self.xyz[na], self.xyz[nb]
            length = float(np.linalg.norm(b - a))
            stations = gradedStations(length, element_length, special(m['from'], mi), special(m['to'], mi))
            prev = na
            for k, s in enumerate(stations[1:], 1):
                nxt = nb if k == len(stations) - 1 else self._node(a + (b - a) * s / length)
                self._element(prev, nxt, mi, 1.0, 1.0, 'pipe')
                prev = nxt
        #arcs: node at the bend point is not used; arc nodes between the two trimmed ends
        for pid, mems, a, b, d1, d2, theta, radius, n_seg in arcs:
            m = self.members[mems[0]]
            c0 = m['section']['carriers'][0]
            k, i = bendFactors(c0['d_o'], c0['wall'], radius)
            normal = _unit(d2 - d1)                     # towards the centre of the arc
            centre = a + normal * radius
            na, nb = self.node_of_point[('t', mems[0], pid)], self.node_of_point[('t', mems[1], pid)]
            u = _unit(a - centre)
            w = d1                                     # tangent at a
            prev = na
            for s in range(1, n_seg + 1):
                phi = theta * s / n_seg
                nxt = nb if s == n_seg else self._node(centre + radius * (math.cos(phi) * u + math.sin(phi) * w))
                self._element(prev, nxt, mems[0], k, i, 'bend')
                prev = nxt
            self.node_of_point[pid] = self.node_of_point[('t', mems[0], pid)]
        #kinks and tees: stress intensification on the elements at the point
        for pid, p in self.points.items():
            bend = p.get('bend') or {}
            n = self.node_of_point.get(pid)
            if n is None:
                continue
            factor = 1.0
            if bend.get('class') == 'kink':
                c0 = self.members[incident[pid][0]]['section']['carriers'][0]
                factor = mitreFactor(c0['d_o'], c0['wall'], bend.get('angle') or 0.0)
            elif p.get('tee') or len(incident.get(pid, [])) >= 3:
                c0 = self.members[incident[pid][0]]['section']['carriers'][0]
                factor = teeFactor(c0['d_o'], c0['wall'])
            if factor > 1.0:
                for e, (n1, n2) in enumerate(self.el_nodes):
                    if n in (n1, n2):
                        self.el_i[e] = max(self.el_i[e], factor)
                        self.el_kind[e] = 'kink' if bend.get('class') == 'kink' else 'tee'
        #links (compensators): the point's node is split; the second node takes the members of one side
        for pid, p in self.points.items():
            if p.get('link') and pid in self.node_of_point:
                mems = incident.get(pid, [])
                if len(mems) != 2:
                    self.notes.append(('link_not_between_two_members', pid))
                    continue
                n0 = self.node_of_point[pid]
                n1 = self._node(self.xyz[n0])
                second = mems[1]
                for e in range(len(self.el_nodes)):
                    if self.el_member[e] == second and n0 in self.el_nodes[e]:
                        a, b = self.el_nodes[e]
                        self.el_nodes[e] = (n1 if a == n0 else a, n1 if b == n0 else b)
                axis = _unit(np.asarray(self.points[self.members[mems[0]]['to' if self.members[mems[0]]['from'] == pid else 'from']]['xyz'], float) - self.xyz[n0])
                self.links.append((n0, n1, axis, float(p['link']['k_axial'])))
        self.xyz = np.array(self.xyz)
        self.el_nodes = np.array(self.el_nodes, dtype=int).reshape(-1, 2)

    def _element(self, n1, n2, member, k, i, kind):
        if n1 == n2:
            return
        self.el_nodes.append((n1, n2))
        self.el_member.append(member)
        self.el_k.append(k)
        self.el_i.append(i)
        self.el_kind.append(kind)


# ---------------------------------------------------------------- element matrices
def beamStiffness(L, EA, EIy, EIz, GJ):
    k = np.zeros((12, 12))
    k[0, 0] = k[6, 6] = EA / L
    k[0, 6] = k[6, 0] = -EA / L
    k[3, 3] = k[9, 9] = GJ / L
    k[3, 9] = k[9, 3] = -GJ / L
    a, b, c, d = 12 * EIz / L ** 3, 6 * EIz / L ** 2, 4 * EIz / L, 2 * EIz / L
    for (r, s, v) in ((1, 1, a), (1, 5, b), (1, 7, -a), (1, 11, b), (5, 5, c), (5, 7, -b), (5, 11, d),
                      (7, 7, a), (7, 11, -b), (11, 11, c)):
        k[r, s] = k[s, r] = v
    a, b, c, d = 12 * EIy / L ** 3, 6 * EIy / L ** 2, 4 * EIy / L, 2 * EIy / L
    for (r, s, v) in ((2, 2, a), (2, 4, -b), (2, 8, -a), (2, 10, -b), (4, 4, c), (4, 8, b), (4, 10, d),
                      (8, 8, a), (8, 10, b), (10, 10, c)):
        k[r, s] = k[s, r] = v
    return k


def freeThermal(L, eps0, kz0, ky0):
    """Nodal displacements (local) of an element with node 1 held under initial strain and curvatures:
    v'' = kz0 (theta_z = v'), w'' = ky0 (theta_y = -w')."""
    d = np.zeros(12)
    d[6] = eps0 * L
    d[7], d[11] = kz0 * L ** 2 / 2, kz0 * L
    d[8], d[10] = ky0 * L ** 2 / 2, -ky0 * L
    return d


def transform(frame):
    t = np.zeros((12, 12))
    for b in range(4):
        t[3 * b:3 * b + 3, 3 * b:3 * b + 3] = frame
    return t


# ---------------------------------------------------------------- springs
class Springs:
    """Lumped soil springs per node in its frame (axial, lateral, vertical). The axial spring is elastoplastic with
    history (friction), lateral and vertical are non-linear elastic."""

    def __init__(self, frames, trib, f_ax, k_ax, lat_curves, k_v, p_up):
        self.frames = frames                 # (n, 3, 3)
        self.f_ax = f_ax * trib
        self.k_ax = k_ax * trib
        #lateral curves as arrays of equal length (padded with the last point) so they evaluate vectorised
        width = max(len(c) for c in lat_curves) if lat_curves else 2
        self.lat_u = np.array([[p[0] for p in c] + [c[-1][0] + 1.0 + k for k in range(width - len(c))] for c in lat_curves])
        self.lat_f = np.array([[p[1] * t for p in c] + [c[-1][1] * t] * (width - len(c)) for c, t in zip(lat_curves, trib)])
        self.k_v = k_v * trib
        self.p_up = p_up * trib
        self.slip = np.zeros(len(trib))      # committed plastic axial slip
        self.trial_slip = self.slip.copy()

    def _lateral(self, u):
        """Force and tangent of the symmetric piecewise-linear lateral curves; constant beyond the last point."""
        s = np.abs(u)
        U, F = self.lat_u, self.lat_f
        rows = np.arange(len(s))
        seg = np.clip((U[:, 1:] < s[:, None]).sum(axis=1), 0, U.shape[1] - 2)
        u0, u1, f0, f1 = U[rows, seg], U[rows, seg + 1], F[rows, seg], F[rows, seg + 1]
        slope = np.where(u1 > u0, (f1 - f0) / np.where(u1 > u0, u1 - u0, 1.0), 0.0)
        beyond = s > U[:, -1]
        first = np.where(U[:, 1] > 0, F[:, 1] / np.where(U[:, 1] > 0, U[:, 1], 1.0), 0.0)
        f = np.where(beyond, F[:, -1], f0 + slope * (s - u0))
        kt = np.where(beyond | (slope <= 0), first * 1e-6, slope)
        return np.sign(u) * f, kt

    def evaluate(self, u_trans):
        """(forces (n,3) global, tangents (n,3,3) global) for nodal translations (n,3)."""
        loc = np.einsum('nij,nj->ni', self.frames, u_trans)
        f = np.zeros_like(loc)
        kt = np.zeros_like(loc)
        trial = self.k_ax * (loc[:, 0] - self.slip)
        #a node that slid stays exactly on the limit; without the margin rounding gives it the sliding tangent and
        #Newton diverges when the load reverses (it unloads elastically)
        over = np.abs(trial) > self.f_ax * (1 + 1e-6)
        f[:, 0] = np.where(over, np.sign(trial) * self.f_ax, trial)
        kt[:, 0] = np.where(over, self.k_ax * 1e-6, self.k_ax)
        self.trial_slip = np.where(over, loc[:, 0] - f[:, 0] / np.where(self.k_ax > 0, self.k_ax, 1.0), self.slip)
        f[:, 1], kt[:, 1] = self._lateral(loc[:, 1])
        up = loc[:, 2] > 0
        f_v = self.k_v * loc[:, 2]
        capped = up & (f_v > self.p_up)
        f[:, 2] = np.where(capped, self.p_up, f_v)
        kt[:, 2] = np.where(capped, self.k_v * 1e-6, self.k_v)
        fg = np.einsum('nji,nj->ni', self.frames, f)
        kg = np.einsum('nki,nk,nkj->nij', self.frames, kt, self.frames)
        return fg, kg

    def commit(self):
        self.slip = self.trial_slip.copy()


def elementPosition(mesh, e, member):
    """Distance of the element's midpoint from the member's start point."""
    a, b = mesh.el_nodes[e]
    start = np.asarray(mesh.points[member['from']]['xyz'], float)
    return float(np.linalg.norm((mesh.xyz[a] + mesh.xyz[b]) / 2.0 - start))


def elementPad(mesh, e, member):
    """Pad thickness of an element: the member's pad, or the pad run (start, length, thickness) it lies in."""
    pad = member.get('pad') or 0.0
    runs = member.get('pad_runs') or ()
    if runs:
        s = elementPosition(mesh, e, member)
        for start, length, thickness in runs:
            if start - 1e-6 <= s <= start + length + 1e-6:
                pad = max(pad, thickness)
    return pad


# ---------------------------------------------------------------- model and solution
class Model:
    """Assembled FE model of one mesh. states: list of load states; each member has 'temps' (per state, per
    carrier), 'pressure' (per state) and 't0' (stress-free temperature per carrier)."""

    def __init__(self, mesh, fixed_points=(), pad_strain=None):
        self.mesh = mesh
        n = len(mesh.xyz)
        self.n = n
        self.ndof = 6 * n
        members = mesh.members
        ne = len(mesh.el_nodes)
        self.frames = np.zeros((ne, 3, 3))
        self.L = np.zeros(ne)
        rows, cols, vals = [], [], []
        self.k_local = []
        for e, (a, b) in enumerate(mesh.el_nodes):
            d = mesh.xyz[b] - mesh.xyz[a]
            L = float(np.linalg.norm(d))
            fr = localFrame(d)
            self.frames[e], self.L[e] = fr, L
            s = members[mesh.el_member[e]]['section']
            kf = mesh.el_k[e]
            kl = beamStiffness(L, s['EA'], s['EIy'] / kf, s['EIz'] / kf, s['GJ'])
            self.k_local.append(kl)
            T = transform(fr)
            kg = T.T @ kl @ T
            dofs = np.r_[6 * a:6 * a + 6, 6 * b:6 * b + 6]
            rows.append(np.repeat(dofs, 12))
            cols.append(np.tile(dofs, 12))
            vals.append(kg.ravel())
        k_big = 1e3 * max((members[mesh.el_member[e]]['section']['EA'] / self.L[e] for e in range(ne)), default=1.0)
        for (a, b, axis, k_axial) in mesh.links:
            P = np.outer(axis, axis)
            kt = k_axial * P + k_big * (np.eye(3) - P)
            blk = np.zeros((12, 12))
            blk[0:3, 0:3], blk[0:3, 6:9], blk[6:9, 0:3], blk[6:9, 6:9] = kt, -kt, -kt, kt
            r = k_big * np.eye(3)
            blk[3:6, 3:6], blk[3:6, 9:12], blk[9:12, 3:6], blk[9:12, 9:12] = r, -r, -r, r
            dofs = np.r_[6 * a:6 * a + 6, 6 * b:6 * b + 6]
            rows.append(np.repeat(dofs, 12))
            cols.append(np.tile(dofs, 12))
            vals.append(blk.ravel())
        #tiny rotational springs at every node keep twist and free rotations of straight parts non-singular
        ei = max((members[m]['section']['EIy'] for m in set(mesh.el_member)), default=1.0)
        rot = np.arange(n)[:, None] * 6 + np.array([3, 4, 5])
        rows.append(rot.ravel())
        cols.append(rot.ravel())
        vals.append(np.full(rot.size, 1e-6 * ei))
        self.K = sparse.csr_matrix((np.concatenate(vals), (np.concatenate(rows), np.concatenate(cols))),
                                   shape=(self.ndof, self.ndof))
        self.fixed = np.zeros(self.ndof, bool)
        for pid in fixed_points:
            nd = mesh.node_of_point.get(pid)
            if nd is not None:
                self.fixed[6 * nd:6 * nd + 6] = True
        self._springs(pad_strain)

    def _springs(self, pad_strain):
        mesh, members = self.mesh, self.mesh.members
        n = self.n
        trib = np.zeros(n)
        direction = np.zeros((n, 3))
        acc = {k: np.zeros(n) for k in ('f_ax', 'k_ax', 'k_v', 'p_up', 'p_lat', 'k_lat', 'casing', 'pad')}
        for e, (a, b) in enumerate(mesh.el_nodes):
            m = members[mesh.el_member[e]]
            sl, half = m['soil'], self.L[e] / 2
            pad = elementPad(mesh, e, m)
            for nd in (a, b):
                trib[nd] += half
                #members meeting head to head must not cancel each other's direction
                d = self.frames[e][0]
                direction[nd] += d if np.dot(direction[nd], d) >= 0 else -d
                for k in ('f_ax', 'k_ax', 'k_v', 'p_up', 'p_lat', 'k_lat'):
                    acc[k][nd] += sl[k] * half
                acc['casing'][nd] += m['casing_d'] * half
                acc['pad'][nd] = max(acc['pad'][nd], pad)
        safe = np.where(trib > 0, trib, 1.0)
        for k in ('f_ax', 'k_ax', 'k_v', 'p_up', 'p_lat', 'k_lat', 'casing'):
            acc[k] = acc[k] / safe
        frames = np.array([localFrame(d if np.linalg.norm(d) > 0 else (1, 0, 0)) for d in direction])
        curves = [lateralCurve(acc['p_lat'][i], acc['k_lat'][i], acc['casing'][i], acc['pad'][i], pad_strain)
                  if acc['k_lat'][i] > 0 else [(0.0, 0.0), (1.0, 0.0)] for i in range(n)]
        self.node_frames = frames
        self.trib = trib
        self.springs = Springs(frames, trib, acc['f_ax'], acc['k_ax'], curves, acc['k_v'], acc['p_up'])

    # ---------------------------------------------------------------- loads
    def elementLoads(self, state_temps, state_p):
        """Initial strain and curvatures per element for member temperatures (per carrier, relative to t0) and
        pressures. state_temps: {member index: [T per carrier]}, state_p: {member index: p}."""
        mesh, members = self.mesh, self.mesh.members
        ne = len(mesh.el_nodes)
        eps, kz, ky = np.zeros(ne), np.zeros(ne), np.zeros(ne)
        cache = {}
        for e in range(ne):
            mi = mesh.el_member[e]
            if mi not in cache:
                m = members[mi]
                s = m['section']
                n_t = my_t = mz_t = 0.0
                for c, p, (oy, oz), T, T0 in zip(s['carriers'], s['props'], s['offsets'], state_temps[mi], m['t0']):
                    strain = c['alpha'] * (T - T0) + pressureStrain(state_p[mi], c)
                    ea = c['E'] * p['A'] * strain
                    n_t += ea
                    mz_t += -oy * ea
                    my_t += -oz * ea
                #fibre strain -y*kz - z*ky: the hotter carrier makes the free twin curve away from it
                cache[mi] = (n_t / s['EA'], mz_t / s['EIz'], my_t / s['EIy'])
            k = mesh.el_k[e]
            e0, z0, y0 = cache[mi]
            eps[e], kz[e], ky[e] = e0, z0, y0
        return eps, kz, ky

    def loadVector(self, eps, kz, ky):
        F = np.zeros(self.ndof)
        for e, (a, b) in enumerate(self.mesh.el_nodes):
            if eps[e] == 0 and kz[e] == 0 and ky[e] == 0:
                continue
            fl = self.k_local[e] @ freeThermal(self.L[e], eps[e], kz[e], ky[e])
            fg = transform(self.frames[e]).T @ fl
            F[6 * a:6 * a + 6] += fg[:6]
            F[6 * b:6 * b + 6] += fg[6:]
        return F

    # ---------------------------------------------------------------- solution
    def solve(self, states, increment=10.0, max_iterations=50, tol=1e-6, progress=None, cancelled=None):
        """Runs the load states in sequence from the stress-free state (all members at t0, no pressure). states:
        [{'temps': {member: [T per carrier]}, 'p': {member: p}}]. Returns {'converged', 'states': [results per
        state], 'message'}."""
        members = self.mesh.members
        prev_t = {mi: list(m['t0']) for mi, m in enumerate(members)}
        prev_p = {mi: 0.0 for mi in range(len(members))}
        u = np.zeros(self.ndof)
        free = ~self.fixed
        out = []
        for si, st in enumerate(states):
            dT = max((abs(a - b) for mi in st['temps'] for a, b in zip(st['temps'][mi], prev_t[mi])), default=0.0)
            n_inc = max(1, int(math.ceil(dT / increment - 1e-9)))
            for inc in range(1, n_inc + 1):
                f = inc / n_inc
                temps = {mi: [a + (b - a) * f for a, b in zip(prev_t[mi], st['temps'][mi])] for mi in st['temps']}
                pres = {mi: prev_p[mi] + (st['p'][mi] - prev_p[mi]) * f for mi in st['p']}
                eps, kz, ky = self.elementLoads(temps, pres)
                F = self.loadVector(eps, kz, ky)
                ref = max(np.abs(F).max(), 1.0)
                ok = False
                nodes = np.arange(self.n)
                r = (nodes[:, None, None] * 6 + np.arange(3)[None, :, None]).repeat(3, axis=2)
                c = (nodes[:, None, None] * 6 + np.arange(3)[None, None, :]).repeat(3, axis=1)
                R, ks = self._residual(u, F)
                for it in range(max_iterations):
                    norm = np.abs(R).max()
                    if norm <= tol * ref + 1e-3:
                        ok = True
                        break
                    Kt = self.K + sparse.csr_matrix((ks.ravel(), (r.ravel(), c.ravel())), shape=self.K.shape)
                    du = np.zeros(self.ndof)
                    du[free] = spsolve(Kt[free][:, free].tocsc(), -R[free])
                    #line search: halve the step while the residual grows (sticking/sliding switches overshoot)
                    step = 1.0
                    for _ in range(8):
                        R_new, ks_new = self._residual(u + step * du, F)
                        if np.abs(R_new).max() < norm:
                            break
                        step /= 2.0
                    u += step * du
                    R, ks = R_new, ks_new
                if not ok:
                    return {'converged': False, 'states': out,
                            'message': 'no convergence in state {} increment {}'.format(si + 1, inc)}
                self.springs.commit()
                if cancelled is not None and cancelled():
                    return {'converged': False, 'states': out, 'message': 'cancelled'}
            prev_t, prev_p = {mi: list(v) for mi, v in st['temps'].items()}, dict(st['p'])
            out.append(self.results(u.copy(), st))
            if progress is not None:
                progress((si + 1) / len(states))
        return {'converged': True, 'states': out, 'message': ''}

    def _residual(self, u, F):
        """Residual and spring tangents at u (the springs' trial slip follows u; commit() takes it over)."""
        fs, ks = self.springs.evaluate(u.reshape(-1, 6)[:, :3])
        R = self.K @ u - F
        R.reshape(-1, 6)[:, :3] += fs
        R[self.fixed] = 0.0
        return R, ks

    def results(self, u, state):
        """Per element and carrier: axial force share, stresses; per node: displacement and axial spring force."""
        mesh, members = self.mesh, self.mesh.members
        eps, kz, ky = self.elementLoads(state['temps'], state['p'])
        ne = len(mesh.el_nodes)
        elements = []
        for e, (a, b) in enumerate(mesh.el_nodes):
            m = members[mesh.el_member[e]]
            s = m['section']
            T = transform(self.frames[e])
            d = T @ np.r_[u[6 * a:6 * a + 6], u[6 * b:6 * b + 6]]
            L = self.L[e]
            ex = (d[6] - d[0]) / L
            #curvatures at both ends (cubic Hermite); theta_y = -w'
            v1, t1, v2, t2 = d[1], d[5], d[7], d[11]
            w1, s1, w2, s2 = d[2], -d[4], d[8], -d[10]
            kz_ends = ((-6 * v1 - 4 * L * t1 + 6 * v2 - 2 * L * t2) / L ** 2, (6 * v1 + 2 * L * t1 - 6 * v2 + 4 * L * t2) / L ** 2)
            ky_ends = ((-6 * w1 - 4 * L * s1 + 6 * w2 - 2 * L * s2) / L ** 2, (6 * w1 + 2 * L * s1 - 6 * w2 + 4 * L * s2) / L ** 2)
            kf, sif = mesh.el_k[e], mesh.el_i[e]
            N = s['EA'] * (ex - eps[e])
            carriers = []
            for c, p, (oy, oz), Tc, T0 in zip(s['carriers'], s['props'], s['offsets'],
                                               state['temps'][mesh.el_member[e]], m['t0']):
                pr = state['p'][mesh.el_member[e]]
                hoop = hoopStress(pr, c)
                strain_free = c['alpha'] * (Tc - T0) + pressureStrain(pr, c)
                best: Any = None
                for kze, kye in zip(kz_ends, ky_ends):
                    mech = ex - oy * (kze - 0.0) - oz * (kye - 0.0) - strain_free
                    sigma_ax = c['E'] * mech + hoop / 2.0
                    #the carrier bends with the section; on a bend with flexibility k the moment is EI/k
                    kap = math.hypot(kze - kz[e], kye - ky[e])
                    sigma_b = sif * c['E'] / kf * kap * p['ro']
                    cand = (abs(sigma_ax) + sigma_b, sigma_ax, sigma_b)
                    if best is None or cand[0] > best[0]:
                        best = cand
                _, sigma_ax, sigma_b = best
                fibres = (sigma_ax + sigma_b, sigma_ax - sigma_b)
                sigma_eq = max(max(abs(f - hoop), abs(f), abs(hoop)) for f in fibres)
                carriers.append({'sigma_ax': sigma_ax, 'sigma_b': sigma_b, 'sigma_hoop': hoop, 'sigma_eq': sigma_eq,
                                 'fibres': fibres})
            elements.append({'N': N, 'carriers': carriers})
        fs, _ = self.springs.evaluate(u.reshape(-1, 6)[:, :3])
        loc = np.einsum('nij,nj->ni', self.node_frames, u.reshape(-1, 6)[:, :3])
        floc = np.einsum('nij,nj->ni', self.node_frames, fs)
        return {'u': u.reshape(-1, 6)[:, :3].copy(), 'u_full': u.copy(), 'u_local': loc, 'spring_local': floc,
                'elements': elements}

    def reactions(self, u):
        """Forces at the fixed degrees of freedom (global)."""
        return (self.K @ u)[self.fixed]


def parts(mesh):
    """Connected parts: list of (point ids, member indexes)."""
    n = len(mesh.xyz)
    if n == 0:
        return []
    a, b = mesh.el_nodes[:, 0], mesh.el_nodes[:, 1]
    la = [l[0] for l in mesh.links]
    lb = [l[1] for l in mesh.links]
    adj = sparse.coo_matrix((np.ones(len(a) + len(la)), (np.r_[a, la].astype(int), np.r_[b, lb].astype(int))), shape=(n, n))
    count, labels = csgraph.connected_components(adj, directed=False)
    groups = []
    for g in range(count):
        members = sorted({mesh.el_member[e] for e in range(len(a)) if labels[a[e]] == g})
        pts = sorted({p for nd, p in enumerate(mesh.node_point) if labels[nd] == g and p is not None and not isinstance(p, tuple)}, key=str)
        if members:
            groups.append((pts, members))
    return groups
