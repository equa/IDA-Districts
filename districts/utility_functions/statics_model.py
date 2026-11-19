#geometry rules of the statics model (change statics-model): plain coordinates, no DB and no QGIS
import math

#bend classes of a route node
BEND_NONE = 'none'
BEND_KINK = 'kink'          #small-angle kink (rigid pipes)
BEND_PREFAB = 'bend'        #prefabricated bend (rigid pipes)
BEND_ELASTIC = 'elastic'    #elastic bend (flexible and plastic pipes, merged runs)
BEND_CLASSES = (BEND_NONE, BEND_KINK, BEND_PREFAB, BEND_ELASTIC)

RIGID_SYSTEMS = ('rigid_single', 'rigid_twin')

PARAMETER_DEFAULTS = {
    'bend_ignore_deg': (1.0, 'deg', 'angle below which a vertex is no bend'),
    'kink_max_deg': (5.0, 'deg', 'rigid pipes: largest angle of a small-angle kink'),
    'bend_radius_factor': (1.5, '-', 'rigid pipes: radius of a prefabricated bend / steel outer diameter'),
    'elastic_radius_factor': (1000.0, '-', 'rigid pipes: smallest radius of an elastic bend / steel outer diameter'),
    'merge_distance_m': (5.0, 'm', 'largest spacing of the vertices of a run merged into an elastic bend'),
    'snap_tolerance_m': (0.5, 'm', 'distance within which an override matches a model node or section'),
}


def defaultParameters():
    return {key: value for key, (value, _, _) in PARAMETER_DEFAULTS.items()}


def isRigid(system_type):
    #pipes without series data count as rigid steel pipes (the conservative case for bends)
    return system_type in RIGID_SYSTEMS or not system_type


def _sub(a, b):
    return (a[0] - b[0], a[1] - b[1], a[2] - b[2])


def _norm(v):
    return math.sqrt(v[0] * v[0] + v[1] * v[1] + v[2] * v[2])


def _dist2d(a, b):
    return math.hypot(a[0] - b[0], a[1] - b[1])


def cleanCoordinates(coords, tolerance=1e-6):
    """Coordinates (x, y, z) without consecutive duplicates; a missing z counts as 0."""
    result = []
    for c in coords:
        p = (float(c[0]), float(c[1]), float(c[2]) if len(c) > 2 and c[2] is not None else 0.0)
        if not result or _norm(_sub(p, result[-1])) > tolerance:
            result.append(p)
    return result


def vertexAngle(a, b, c):
    """3D deflection angle in degrees at b between the segments a-b and b-c."""
    u, v = _sub(b, a), _sub(c, b)
    nu, nv = _norm(u), _norm(v)
    if nu == 0 or nv == 0:
        return 0.0
    cos = (u[0] * v[0] + u[1] * v[1] + u[2] * v[2]) / (nu * nv)
    return math.degrees(math.acos(max(-1.0, min(1.0, cos))))


def _turnSign(a, b, c, tolerance=1e-9):
    #plan turning direction; 0 for a pure vertical bend, which fits into a run of either direction
    cross = (b[0] - a[0]) * (c[1] - b[1]) - (b[1] - a[1]) * (c[0] - b[0])
    return 0 if abs(cross) < tolerance else (1 if cross > 0 else -1)


def vertexAngles(coords):
    """Angles in degrees of the interior vertices 1..n-2 of a cleaned coordinate list."""
    return [vertexAngle(coords[i - 1], coords[i], coords[i + 1]) for i in range(1, len(coords) - 1)]


def classifyVertices(coords, rigid, d_outer_m, params):
    """Bend class of each interior vertex of a cleaned coordinate list.
    rigid: a rigid pipe lies in the line; d_outer_m: largest steel outer diameter of the rigid pipes.
    Returns (vertices, runs_not_merged): vertices[i-1] for vertex i is a dict with angle_deg, bend_class, radius_m,
    bend_id (index of the merged run or None) and source ('rule' or 'merge'); runs_not_merged lists
    {'vertex_indexes', 'radius_m'} of rigid runs whose radius is below the elastic limit."""
    angles = vertexAngles(coords)
    ignore, kink_max = params['bend_ignore_deg'], params['kink_max_deg']
    vertices = []
    for i, angle in enumerate(angles, 1):
        if angle < ignore:
            cls, radius = BEND_NONE, None
        elif rigid and angle <= kink_max:
            cls, radius = BEND_KINK, None
        elif rigid:
            cls, radius = BEND_PREFAB, params['bend_radius_factor'] * d_outer_m if d_outer_m else None
        else:
            spacing = (_norm(_sub(coords[i], coords[i - 1])) + _norm(_sub(coords[i + 1], coords[i]))) / 2
            cls, radius = BEND_ELASTIC, spacing / math.radians(angle)
        vertices.append({'angle_deg': angle, 'bend_class': cls, 'radius_m': radius, 'bend_id': None, 'source': 'rule'})

    runs_not_merged = []
    run_id = 0
    for run in smallKinkRuns(coords, angles, params):
        total = sum(angles[i - 1] for i in run)
        if total < ignore:
            continue
        spacing = sum(_norm(_sub(coords[run[k + 1]], coords[run[k]])) for k in range(len(run) - 1)) / (len(run) - 1)
        radius = spacing / math.radians(total / len(run))
        if rigid and d_outer_m and radius < params['elastic_radius_factor'] * d_outer_m:
            runs_not_merged.append({'vertex_indexes': list(run), 'radius_m': radius})
            continue
        run_id += 1
        for i in run:
            vertices[i - 1].update(bend_class=BEND_ELASTIC, radius_m=radius, bend_id=run_id, source='merge')
    return vertices, runs_not_merged


def smallKinkRuns(coords, angles, params):
    """Runs (lists of vertex indexes, at least two) of consecutive vertices with an angle above 0 and up to kink_max_deg,
    spaced at most merge_distance_m and turning in the same plan direction."""
    runs, current, sign = [], [], 0
    for i, angle in enumerate(angles, 1):
        s = _turnSign(coords[i - 1], coords[i], coords[i + 1])
        fits = 1e-9 < angle <= params['kink_max_deg']
        joins = (fits and current and _norm(_sub(coords[i], coords[current[-1]])) <= params['merge_distance_m']
                 and (s == 0 or sign == 0 or s == sign))
        if joins:
            current.append(i)
            sign = sign or s
        else:
            if len(current) > 1:
                runs.append(current)
            current, sign = ([i], s) if fits else ([], 0)
    if len(current) > 1:
        runs.append(current)
    return runs


def distancePointPolyline2d(p, coords):
    """Plan distance of the point p to the polyline coords."""
    best = math.inf
    for a, b in zip(coords, coords[1:]):
        dx, dy = b[0] - a[0], b[1] - a[1]
        length2 = dx * dx + dy * dy
        t = 0.0 if length2 == 0 else max(0.0, min(1.0, ((p[0] - a[0]) * dx + (p[1] - a[1]) * dy) / length2))
        best = min(best, math.hypot(p[0] - a[0] - t * dx, p[1] - a[1] - t * dy))
    if len(coords) == 1:
        best = _dist2d(p, coords[0])
    return best


def snapPoints(points, nodes, tolerance):
    """Matches override points to model nodes by plan distance.
    points, nodes: {id: (x, y)}. Returns (applied {point_id: node_id}, ambiguous [point_id], unmatched [point_id]);
    a point with two or more nodes within the tolerance is ambiguous."""
    applied, ambiguous, unmatched = {}, [], []
    for pid, p in sorted(points.items()):
        near = [nid for nid, n in nodes.items() if _dist2d(p, n) <= tolerance]
        if len(near) == 1:
            applied[pid] = near[0]
        elif near:
            ambiguous.append(pid)
        else:
            unmatched.append(pid)
    return applied, ambiguous, unmatched


def snapSections(overrides, midpoints, tolerance):
    """Matches override sections to model sections: a model section whose midpoint lies within the tolerance of an
    override line. overrides: {id: [(x, y), ...]}, midpoints: {section_id: (x, y)}.
    Returns (applied {section_id: override_id}, unmatched [override_id]); the override with the highest id wins."""
    applied, matched = {}, set()
    for oid, coords in sorted(overrides.items()):
        for sid, m in midpoints.items():
            if coords and distancePointPolyline2d(m, coords) <= tolerance:
                applied[sid] = oid
                matched.add(oid)
    return applied, sorted(set(overrides) - matched)
