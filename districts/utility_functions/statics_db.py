#tables, build, fingerprint and report of the statics model (change statics-model)
import json
from collections import OrderedDict

from . import statics_model as sm
from . import statics_checks as sc

POINT_KINDS = ('fixed_point', 'compensator', 'one_time_compensator', 'valve', 'bend')
#friction_coefficient is the upper value (statics-steel-solver D5); kept instead of being dropped from old versions
SECTION_OVERRIDE_COLUMNS = ['cover_m', 'soil_unit_weight_kn_m3', 'friction_angle_deg', 'friction_coefficient',
                            'groundwater_depth_m', 'traffic_load_kn_m2', 'laying_temperature_c', 'laying_method',
                            'friction_coefficient_min', 'design_temperature_c', 'design_pressure_bar',
                            'preheat_temperature_c', 'prestressed_legs']
POINT_OVERRIDE_COLUMNS = ['max_travel_mm', 'spring_rate_n_mm', 'bellows_area_cm2']
#columns added by statics-steel-solver, for versions created before it
ADDED_COLUMNS = {
    'statics_sections': {'friction_coefficient_min': 'numeric CHECK (friction_coefficient_min >= 0)',
                         'design_temperature_c': 'numeric', 'design_pressure_bar': 'numeric CHECK (design_pressure_bar >= 0)',
                         'preheat_temperature_c': 'numeric', 'prestressed_legs': 'boolean'},
    'statics_model_sections': {'friction_coefficient_min': 'numeric', 'design_temperature_c': 'numeric',
                               'design_pressure_bar': 'numeric', 'preheat_temperature_c': 'numeric',
                               'prestressed_legs': 'boolean'},
    'statics_points': {'max_travel_mm': 'numeric CHECK (max_travel_mm > 0)', 'spring_rate_n_mm': 'numeric CHECK (spring_rate_n_mm > 0)',
                       'bellows_area_cm2': 'numeric CHECK (bellows_area_cm2 > 0)'},
    'statics_model_nodes': {'max_travel_mm': 'numeric', 'spring_rate_n_mm': 'numeric', 'bellows_area_cm2': 'numeric'},
}
MODEL_TABLES = ('statics_model_nodes', 'statics_model_sections', 'statics_model_pipes')
RESULT_TABLES = ('statics_result_run', 'statics_result_elements', 'statics_result_nodes', 'statics_result_findings')
VERSION_TABLES = MODEL_TABLES + ('statics_model_build', 'statics_points', 'statics_sections') + RESULT_TABLES
STATE_MISSING, STATE_CURRENT, STATE_OUT_OF_DATE = 'missing', 'current', 'out of date'

#the same SQL as the statics block of DB_versionTablesDefault.txt ($versionName$, $srid$); test_statics_build checks it
STATICS_TABLES_SQL = """CREATE TABLE IF NOT EXISTS "$versionName$".statics_model_nodes
(
  id serial,
  geom geometry(PointZ,$srid$),
  line_ids integer[],
  vertex_index integer,
  kind text,
  junction_id integer,
  junction_type text,
  angle_deg numeric,
  bend_class text,
  radius_m numeric,
  bend_id integer,
  source text,
  override_id integer,
  override_kind text,
  max_travel_mm numeric,
  spring_rate_n_mm numeric,
  bellows_area_cm2 numeric,
  CONSTRAINT statics_model_nodes_pkey PRIMARY KEY (id)
);
CREATE TABLE IF NOT EXISTS "$versionName$".statics_model_sections
(
  id serial,
  geom geometry(LineStringZ,$srid$),
  line_id integer,
  node_from integer,
  node_to integer,
  length_m numeric,
  line_type integer,
  override_id integer,
  cover_m numeric,
  soil_unit_weight_kn_m3 numeric,
  friction_angle_deg numeric,
  friction_coefficient numeric,
  groundwater_depth_m numeric,
  traffic_load_kn_m2 numeric,
  laying_temperature_c numeric,
  laying_method text,
  friction_coefficient_min numeric,
  design_temperature_c numeric,
  design_pressure_bar numeric,
  preheat_temperature_c numeric,
  prestressed_legs boolean,
  CONSTRAINT statics_model_sections_pkey PRIMARY KEY (id)
);
CREATE TABLE IF NOT EXISTS "$versionName$".statics_model_pipes
(
  id serial,
  geom geometry(LineStringZ,$srid$),
  section_id integer,
  line_id integer,
  sequences integer[],
  pipe_ids integer[],
  twin boolean,
  system_type text,
  series_id integer,
  d_inner_m numeric[],
  d_outer_m numeric[],
  wall_m numeric[],
  casing_d_m numeric,
  cover_m numeric,
  x_m numeric,
  y_m numeric,
  min_bend_radius_m numeric,
  CONSTRAINT statics_model_pipes_pkey PRIMARY KEY (id)
);
CREATE TABLE IF NOT EXISTS "$versionName$".statics_model_build
(
  id serial,
  built_at timestamp without time zone DEFAULT now(),
  fingerprint text,
  report jsonb,
  CONSTRAINT statics_model_build_pkey PRIMARY KEY (id)
);
CREATE TABLE IF NOT EXISTS "$versionName$".statics_points
(
  id serial,
  geom geometry(Point,$srid$),
  kind text CHECK (kind IN ('fixed_point','compensator','one_time_compensator','valve','bend')),
  bend_class text CHECK (bend_class IN ('none','kink','bend','elastic')),
  radius_m numeric CHECK (radius_m > 0),
  max_travel_mm numeric CHECK (max_travel_mm > 0),
  spring_rate_n_mm numeric CHECK (spring_rate_n_mm > 0),
  bellows_area_cm2 numeric CHECK (bellows_area_cm2 > 0),
  note text,
  CONSTRAINT statics_points_pkey PRIMARY KEY (id)
);
CREATE TABLE IF NOT EXISTS "$versionName$".statics_sections
(
  id serial,
  geom geometry(LineString,$srid$),
  cover_m numeric,
  soil_unit_weight_kn_m3 numeric CHECK (soil_unit_weight_kn_m3 > 0),
  friction_angle_deg numeric CHECK (friction_angle_deg >= 0),
  friction_coefficient numeric CHECK (friction_coefficient >= 0),
  groundwater_depth_m numeric,
  traffic_load_kn_m2 numeric CHECK (traffic_load_kn_m2 >= 0),
  laying_temperature_c numeric,
  laying_method text,
  friction_coefficient_min numeric CHECK (friction_coefficient_min >= 0),
  design_temperature_c numeric,
  design_pressure_bar numeric CHECK (design_pressure_bar >= 0),
  preheat_temperature_c numeric,
  prestressed_legs boolean,
  note text,
  CONSTRAINT statics_sections_pkey PRIMARY KEY (id)
);
CREATE TABLE IF NOT EXISTS "$versionName$".statics_result_run
(
  id serial,
  run_at timestamp without time zone DEFAULT now(),
  model_fingerprint text,
  solver_fingerprint text,
  parameters jsonb,
  summary jsonb,
  status text,
  CONSTRAINT statics_result_run_pkey PRIMARY KEY (id)
);
CREATE TABLE IF NOT EXISTS "$versionName$".statics_result_elements
(
  id serial,
  geom geometry(LineStringZ,$srid$),
  model_pipe_id integer,
  carrier integer,
  load_step text,
  friction_case text,
  kind text,
  sif numeric,
  sigma_ax_n7mm2 numeric,
  sigma_bend_n7mm2 numeric,
  sigma_hoop_n7mm2 numeric,
  sigma_eq_n7mm2 numeric,
  stress_range_n7mm2 numeric,
  utilisation numeric,
  governing_check text,
  CONSTRAINT statics_result_elements_pkey PRIMARY KEY (id)
);
CREATE TABLE IF NOT EXISTS "$versionName$".statics_result_nodes
(
  id serial,
  geom geometry(PointZ,$srid$),
  model_node_id integer,
  model_pipe_id integer,
  load_step text,
  friction_case text,
  ux_mm numeric,
  uy_mm numeric,
  uz_mm numeric,
  axial_mm numeric,
  lateral_mm numeric,
  axial_friction_n numeric,
  pad_thickness_mm numeric,
  pad_length_m numeric,
  CONSTRAINT statics_result_nodes_pkey PRIMARY KEY (id)
);
CREATE TABLE IF NOT EXISTS "$versionName$".statics_result_findings
(
  id serial,
  geom geometry(PointZ,$srid$),
  rule text,
  severity text,
  model_node_id integer,
  model_pipe_id integer,
  line_id integer,
  "values" jsonb,
  text text,
  CONSTRAINT statics_result_findings_pkey PRIMARY KEY (id)
);"""

STATICS_PARAMETERS_SQL = """CREATE TABLE IF NOT EXISTS public.statics_parameters
(
  id serial,
  key text NOT NULL UNIQUE,
  value numeric,
  unit text,
  description text,
  source text,
  CONSTRAINT statics_parameters_pkey PRIMARY KEY (id)
);"""
MODEL_PARAMETER_SOURCE = 'plugin default (statics-model)'


def staticsTablesSql(schema, srid):
    return STATICS_TABLES_SQL.replace('$versionName$', schema).replace('$srid$', str(int(srid)))


def versionSrid(cur, schema):
    cur.execute("""SELECT coalesce(nullif(Find_SRID(%s, 'lines', 'geom'), 0),
        (SELECT ST_SRID(geom) FROM "{}".lines WHERE geom IS NOT NULL LIMIT 1)) AS srid;""".format(schema), (schema,))  # nosec B608
    return int(cur.fetchone()['srid'] or 0)


def ensureStaticsTables(cur, schema):
    """Creates the missing statics tables of a version and adds the columns of later changes (versions created
    before statics-model or statics-steel-solver)."""
    cur.execute("""SELECT count(*) AS n FROM information_schema.tables WHERE table_schema = %s AND table_name = ANY(%s);""",
                (schema, list(VERSION_TABLES)))
    if cur.fetchone()['n'] < len(VERSION_TABLES):
        cur.execute(staticsTablesSql(schema, versionSrid(cur, schema)))
    for table, columns in ADDED_COLUMNS.items():
        cur.execute("""SELECT column_name FROM information_schema.columns WHERE table_schema = %s AND table_name = %s;""",
                    (schema, table))
        existing = {r['column_name'] for r in cur.fetchall()}
        missing = ['ADD COLUMN IF NOT EXISTS {} {}'.format(c, t) for c, t in columns.items() if c not in existing]
        if missing:
            #one ALTER TABLE per statement: the event trigger restrict_column_alterations fails on several
            cur.execute('ALTER TABLE "{}".{} {};'.format(schema, table, ', '.join(missing)))  # nosec B608


def parameterDefaults():
    """{key: (default or None, unit, description, source)} of the model and the solver."""
    out: dict = {k: (v, u, d, MODEL_PARAMETER_SOURCE) for k, (v, u, d) in sm.PARAMETER_DEFAULTS.items()}
    out.update(sc.SOLVER_PARAMETERS)
    return out


def ensureStaticsParameters(cur):
    """Creates public.statics_parameters and adds missing keys with their default and source; existing values are
    kept. Older tables get the column source and an optional value (empty = limit not set)."""
    cur.execute(STATICS_PARAMETERS_SQL)
    cur.execute("""SELECT column_name, is_nullable FROM information_schema.columns
        WHERE table_schema = 'public' AND table_name = 'statics_parameters';""")
    columns = {r['column_name']: r['is_nullable'] for r in cur.fetchall()}
    if 'source' not in columns:
        cur.execute("""ALTER TABLE public.statics_parameters ADD COLUMN IF NOT EXISTS source text;""")
    if columns.get('value') == 'NO':
        cur.execute("""ALTER TABLE public.statics_parameters ALTER COLUMN value DROP NOT NULL;""")
    for key, (value, unit, description, source) in parameterDefaults().items():
        cur.execute("""INSERT INTO public.statics_parameters (key, value, unit, description, source) VALUES (%s, %s, %s, %s, %s)
            ON CONFLICT (key) DO NOTHING;""", (key, value, unit, description, source))
        cur.execute("""UPDATE public.statics_parameters SET source = %s WHERE key = %s AND source IS NULL;""", (source, key))


def readParameters(cur, with_sources=False):
    """{key: value} of the model and solver keys (None = not set); with_sources: also {key: source}."""
    defaults = parameterDefaults()
    params = {k: v[0] for k, v in defaults.items()}
    sources = {k: v[3] for k, v in defaults.items()}
    cur.execute("""SELECT * FROM public.statics_parameters;""")
    for row in cur.fetchall():
        if row['key'] in params:
            params[row['key']] = float(row['value']) if row['value'] is not None else None
            if row.get('source'):
                sources[row['key']] = row['source']
    return (params, sources) if with_sources else params


def modelParameters(cur):
    """The keys of the statics model only, with their defaults where a value is missing."""
    params = readParameters(cur)
    return {k: (params[k] if params.get(k) is not None else v[0]) for k, v in sm.PARAMETER_DEFAULTS.items()}


# ---------------------------------------------------------------- fingerprint
#(schema or None for the version, table, select list); all rows count, ordered by their text
FINGERPRINT_INPUTS = [
    (None, 'lines', 'id, ST_AsEWKT(geom), type, pipe_bundle_type_id'),
    (None, 'junctions', 'id, ST_AsEWKT(geom), type'),
    (None, 'junction_connections', 'jid, lid'),
    (None, 'statics_points', 'id, ST_AsEWKT(geom), kind, bend_class, radius_m, ' + ', '.join(POINT_OVERRIDE_COLUMNS)),
    (None, 'statics_sections', 'id, ST_AsEWKT(geom), ' + ', '.join(SECTION_OVERRIDE_COLUMNS)),
    ('public', 'bundle_pipes', 'pipe_bundle_type_id, sequence, pipe_id, x, y'),
    ('public', 'pipes', 'id, innerpipediameter, pipe_construction_id, series, casing_construction_id, min_bend_radius_m'),
    ('public', 'pipe_layers', 'pipe_construction_id, materialid, thickness, sequence'),
    ('public', 'pipe_series', 'id, name, system_type'),
    ('public', 'junction_types', 'id, type'),
    #only the model's keys: a solver parameter must not put the model out of date
    ('public', 'statics_parameters', 'key, value', "key IN ('{}')".format("', '".join(sm.PARAMETER_DEFAULTS))),
]
#inputs of a calculation beyond the model: solver parameters, material values, allowed axial stress of the series
SOLVER_FINGERPRINT_INPUTS = [
    #as float: numeric keeps the written scale ('0.40' and '0.4' would hash differently)
    ('public', 'statics_parameters', 'key, value::float8', None),
    ('public', 'materials', 'id, youngs_modulus_n7mm2, thermal_expansion_17kelvin, yield_strength_n7mm2, poissons_ratio, density_kg7m3', None),
    ('public', 'pipe_series', 'id, sigma_ax_max_n7mm2', None),
]


def _hash(cur, schema, inputs):
    parts = []
    for item in inputs:
        table_schema, table, columns = item[:3]
        where = item[3] if len(item) > 3 and item[3] else 'true'
        s = table_schema or schema
        cur.execute("""SELECT md5(coalesce(string_agg(t::text, '|' ORDER BY t::text), '')) AS h
            FROM (SELECT {} FROM "{}".{} WHERE {}) t;""".format(columns, s, table, where))  # nosec B608
        parts.append(cur.fetchone()['h'])
    cur.execute("""SELECT md5(%s) AS h;""", ('/'.join(parts),))
    return cur.fetchone()['h']


def fingerprint(cur, schema):
    """md5 over the inputs of the model, computed in the DB."""
    return _hash(cur, schema, FINGERPRINT_INPUTS)


def solverFingerprint(cur, schema):
    """md5 over the inputs of a calculation that the model does not cover."""
    return _hash(cur, schema, SOLVER_FINGERPRINT_INPUTS)


def lastBuild(cur, schema):
    cur.execute("""SELECT id, built_at, fingerprint, report FROM "{}".statics_model_build ORDER BY id DESC LIMIT 1;""".format(schema))  # nosec B608
    return cur.fetchone()


def modelState(cur, schema):
    """missing, current or out of date; code that uses the model refuses a model that is not current."""
    build = lastBuild(cur, schema)
    if build is None:
        return STATE_MISSING
    return STATE_CURRENT if build['fingerprint'] == fingerprint(cur, schema) else STATE_OUT_OF_DATE


# ---------------------------------------------------------------- inputs
def _lines(cur, schema):
    cur.execute("""SELECT l.id, l.type, l.pipe_bundle_type_id, (dp).path[1] AS i,
        ST_X((dp).geom) AS x, ST_Y((dp).geom) AS y, ST_Z((dp).geom) AS z
        FROM (SELECT id, type, pipe_bundle_type_id, ST_DumpPoints(geom) AS dp FROM "{}".lines WHERE geom IS NOT NULL) l
        ORDER BY l.id, i;""".format(schema))  # nosec B608
    lines = OrderedDict()
    for row in cur.fetchall():
        line = lines.setdefault(row['id'], {'type': row['type'], 'bundle': row['pipe_bundle_type_id'], 'coords': []})
        line['coords'].append((row['x'], row['y'], row['z']))
    for line in lines.values():
        line['coords'] = sm.cleanCoordinates(line['coords'])
    return lines


def _junctionEnds(cur, schema):
    """{(line_id, 'start'|'end'): junction row} from junction_connections."""
    cur.execute("""SELECT jc.lid, j.id AS jid, jt.type AS jtype, ST_X(j.geom) AS x, ST_Y(j.geom) AS y, ST_Z(j.geom) AS z,
        CASE WHEN ST_Distance(ST_StartPoint(l.geom), j.geom) <= ST_Distance(ST_EndPoint(l.geom), j.geom) THEN 'start' ELSE 'end' END AS side
        FROM "{0}".junction_connections jc
        JOIN "{0}".junctions j ON j.id = jc.jid
        JOIN "{0}".lines l ON l.id = jc.lid
        LEFT JOIN public.junction_types jt ON jt.id = j.type;""".format(schema))  # nosec B608
    return {(row['lid'], row['side']): row for row in cur.fetchall()}


def _constructionLayers(cur):
    cur.execute("""SELECT pipe_construction_id AS cid, thickness FROM public.pipe_layers ORDER BY pipe_construction_id, sequence;""")
    layers = {}
    for row in cur.fetchall():
        layers.setdefault(row['cid'], []).append(float(row['thickness'] or 0))
    return layers


def _bundles(cur, bundle_ids):
    """{bundle id: [pipe rows ordered by sequence]} with series and system type."""
    if not bundle_ids:
        return {}
    cur.execute("""SELECT bp.pipe_bundle_type_id AS bid, bp.sequence, bp.x, bp.y, p.id AS pipe_id, p.innerpipediameter,
        p.pipe_construction_id, p.casing_construction_id, p.min_bend_radius_m, s.id AS series_id, s.system_type
        FROM public.bundle_pipes bp
        JOIN public.pipes p ON p.id = bp.pipe_id
        LEFT JOIN public.pipe_series s ON s.name = p.series
        WHERE bp.pipe_bundle_type_id = ANY(%s) ORDER BY bp.pipe_bundle_type_id, bp.sequence;""", (list(bundle_ids),))
    bundles = {}
    for row in cur.fetchall():
        bundles.setdefault(row['bid'], []).append(row)
    return bundles


def bundleChains(pipes, layers):
    """Pipe chains of a bundle: one per single pipe, one per twin (two pipes with the same casing construction).
    Returns (chains, error); error is a text when the bundle cannot be modelled."""
    if not pipes:
        return [], 'bundle without pipes'
    singles, twins = [], OrderedDict()
    for p in pipes:
        if p['casing_construction_id'] is not None:
            twins.setdefault(p['casing_construction_id'], []).append(p)
        else:
            singles.append([p])
    for cid, group in twins.items():
        if len(group) != 2:
            return [], 'casing construction {} is used by {} pipes of the bundle instead of 2'.format(cid, len(group))
    chains = []
    for group in singles + list(twins.values()):
        twin = len(group) == 2
        carriers = []
        for p in group:
            own = layers.get(p['pipe_construction_id'])
            if p['innerpipediameter'] is None or not own:
                return [], 'pipe {} has no construction'.format(p['pipe_id'])
            d_inner = float(p['innerpipediameter'])
            carriers.append({'d_inner': d_inner, 'd_outer': d_inner + 2 * own[0], 'wall': own[0],
                             'casing_d': d_inner + 2 * sum(own)})
        if twin:
            casing = layers.get(group[0]['casing_construction_id'])
            if not casing:
                return [], 'casing construction {} has no layers'.format(group[0]['casing_construction_id'])
            #the first casing layer is the foam radius from the casing centre (twin_pipe, flexible_pipe_catalog)
            casing_d = 2 * sum(casing)
        else:
            casing_d = carriers[0]['casing_d']
        x = sum(float(p['x'] or 0) for p in group) / len(group)
        y = sum(float(p['y'] or 0) for p in group) / len(group)
        systems = [p['system_type'] for p in group]
        chains.append({
            'sequences': [p['sequence'] for p in group], 'pipe_ids': [p['pipe_id'] for p in group], 'twin': twin,
            'system_type': systems[0], 'series_id': group[0]['series_id'],
            'd_inner': [c['d_inner'] for c in carriers], 'd_outer': [c['d_outer'] for c in carriers],
            'wall': [c['wall'] for c in carriers], 'casing_d': casing_d, 'x': x, 'y': y,
            'cover': y - casing_d / 2, 'rigid': any(sm.isRigid(s) for s in systems),
            'without_series': [p['pipe_id'] for p in group if not p['system_type']],
            'min_bend_radius_m': max((float(p['min_bend_radius_m']) for p in group if p['min_bend_radius_m'] is not None), default=None),
        })
    return chains, None


def _overrides(cur, schema):
    cur.execute("""SELECT id, ST_X(geom) AS x, ST_Y(geom) AS y, kind, bend_class, radius_m, {} FROM "{}".statics_points
        WHERE geom IS NOT NULL;""".format(', '.join(POINT_OVERRIDE_COLUMNS), schema))  # nosec B608
    points = {row['id']: row for row in cur.fetchall()}
    cur.execute("""SELECT s.id, {}, array_agg(ARRAY[ST_X(dp.geom), ST_Y(dp.geom)] ORDER BY dp.path) AS coords
        FROM "{}".statics_sections s, ST_DumpPoints(s.geom) dp GROUP BY s.id;""".format(
        ', '.join('s.' + c for c in SECTION_OVERRIDE_COLUMNS), schema))  # nosec B608
    sections = {row['id']: row for row in cur.fetchall()}
    return points, sections


# ---------------------------------------------------------------- build
def buildModel(cur, schema):
    """Builds the statics model of the version: replaces the model rows in one transaction and stores the build row
    with fingerprint and report. A failed build leaves the previous model. Returns the report."""
    ensureStaticsParameters(cur)
    ensureStaticsTables(cur, schema)
    params = modelParameters(cur)
    srid = versionSrid(cur, schema)
    lines = _lines(cur, schema)
    ends = _junctionEnds(cur, schema)
    layers = _constructionLayers(cur)
    bundles = _bundles(cur, {line['bundle'] for line in lines.values() if line['bundle'] is not None})
    points, section_overrides = _overrides(cur, schema)

    report = {'parameters': params, 'skipped_lines': [], 'negative_cover': [], 'runs_not_merged': [],
              'tight_bends': [], 'pipes_without_series': [], 'points_applied': [], 'points_ambiguous': [],
              'points_unmatched': [], 'sections_applied': [], 'sections_unmatched': []}
    nodes = OrderedDict()   #key -> node dict
    sections = []           #section dicts
    pipe_rows = []          #(section index, chain)
    without_series = set()
    bend_ids = {}           #(line id, run of the line) -> merged bend id of the version

    def endNode(lid, side, coord):
        junction = ends.get((lid, side))
        if junction is not None:
            key: tuple = ('j', junction['jid'])
            node = nodes.setdefault(key, {'coord': (junction['x'], junction['y'], junction['z'] or 0.0), 'line_ids': [],
                                          'kind': 'junction', 'junction_id': junction['jid'], 'junction_type': junction['jtype']})
        else:
            key = ('p', round(coord[0], 3), round(coord[1], 3))
            node = nodes.setdefault(key, {'coord': coord, 'line_ids': [], 'kind': 'end'})
            if node['line_ids'] and lid not in node['line_ids']:
                node['kind'] = 'vertex'   #lines joined without a junction
        if lid not in node['line_ids']:
            node['line_ids'].append(lid)
        return key

    for lid, line in lines.items():
        coords = line['coords']
        if line['bundle'] is None:
            report['skipped_lines'].append({'line_id': lid, 'reason': 'no pipe bundle'})
            continue
        if len(coords) < 2:
            report['skipped_lines'].append({'line_id': lid, 'reason': 'line without length'})
            continue
        chains, error = bundleChains(bundles.get(line['bundle'], []), layers)
        if error:
            report['skipped_lines'].append({'line_id': lid, 'reason': error})
            continue
        rigid = [c for c in chains if c['rigid']]
        d_outer = max((max(c['d_outer']) for c in rigid), default=None)
        vertices, not_merged = sm.classifyVertices(coords, bool(rigid), d_outer, params)
        for run in not_merged:
            report['runs_not_merged'].append(dict(run, line_id=lid))
        keys = [endNode(lid, 'start', coords[0])]
        for i, v in enumerate(vertices, 1):
            key = ('v', lid, i)
            if v['bend_id'] is not None:
                v['bend_id'] = bend_ids.setdefault((lid, v['bend_id']), len(bend_ids) + 1)
            nodes[key] = dict(v, coord=coords[i], line_ids=[lid], kind='vertex', vertex_index=i)
            keys.append(key)
        keys.append(endNode(lid, 'end', coords[-1]))
        for i in range(len(coords) - 1):
            sections.append({'line_id': lid, 'line_type': line['type'], 'coords': coords[i:i + 2],
                             'from': keys[i], 'to': keys[i + 1]})
            for chain in chains:
                pipe_rows.append((len(sections) - 1, chain))
        for chain in chains:
            without_series.update(chain['without_series'])

    #overrides
    key_ids = {k: n for n, k in enumerate(nodes, 1)}
    applied, ambiguous, unmatched = sm.snapPoints({pid: (p['x'], p['y']) for pid, p in points.items()},
                                                  {key_ids[k]: n['coord'][:2] for k, n in nodes.items()},
                                                  params['snap_tolerance_m'])
    id_keys = {n: k for k, n in key_ids.items()}
    for pid, nid in applied.items():
        node, point = nodes[id_keys[nid]], points[pid]
        node['override_id'], node['override_kind'] = pid, point['kind']
        for c in POINT_OVERRIDE_COLUMNS:
            node[c] = point.get(c)
        if point['bend_class']:
            node['bend_class'], node['source'] = point['bend_class'], 'override'
            node['radius_m'] = float(point['radius_m']) if point['radius_m'] is not None else node.get('radius_m')
    report['points_applied'], report['points_ambiguous'], report['points_unmatched'] = sorted(applied), ambiguous, unmatched
    midpoints = {i: ((s['coords'][0][0] + s['coords'][1][0]) / 2, (s['coords'][0][1] + s['coords'][1][1]) / 2)
                 for i, s in enumerate(sections)}
    sec_applied, sec_unmatched = sm.snapSections({oid: [tuple(c) for c in o['coords']] for oid, o in section_overrides.items()},
                                                 midpoints, params['snap_tolerance_m'])
    for i, oid in sec_applied.items():
        sections[i]['override'] = section_overrides[oid]
    report['sections_applied'] = sorted(set(sec_applied.values()))
    report['sections_unmatched'] = sec_unmatched

    #pipe checks
    negative, tight = OrderedDict(), OrderedDict()
    for si, chain in pipe_rows:
        override = sections[si].get('override')
        cover = float(override['cover_m']) if override and override['cover_m'] is not None else chain['cover']
        if cover < 0:
            negative.setdefault((sections[si]['line_id'], tuple(chain['pipe_ids'])), cover)
        if chain['min_bend_radius_m'] is not None:
            for key in (sections[si]['from'], sections[si]['to']):
                node = nodes[key]
                radius = node.get('radius_m')
                if node.get('bend_class') == sm.BEND_ELASTIC and radius is not None and radius < chain['min_bend_radius_m']:
                    tight.setdefault((sections[si]['line_id'], tuple(chain['pipe_ids']), key_ids[key]),
                                     (radius, chain['min_bend_radius_m']))
    report['negative_cover'] = [{'line_id': l, 'pipe_ids': list(p), 'cover_m': c} for (l, p), c in negative.items()]
    report['tight_bends'] = [{'line_id': l, 'pipe_ids': list(p), 'node': n, 'radius_m': r, 'min_bend_radius_m': m}
                             for (l, p, n), (r, m) in tight.items()]
    report['pipes_without_series'] = sorted(without_series)
    classes = OrderedDict((c, 0) for c in sm.BEND_CLASSES)
    for n in nodes.values():
        if n.get('bend_class') in classes:
            classes[n['bend_class']] += 1
    report['counts'] = {'nodes': len(nodes), 'nodes_by_class': classes, 'sections': len(sections), 'pipes': len(pipe_rows),
                        'lines': len(lines) - len(report['skipped_lines'])}
    report['parameters'] = params

    _write(cur, schema, srid, nodes, key_ids, sections, pipe_rows, report)
    return report


def _pointZ(c, srid):
    return 'SRID={};POINT Z ({} {} {})'.format(srid, c[0], c[1], c[2])


def _lineZ(coords, srid):
    return 'SRID={};LINESTRING Z ({})'.format(srid, ', '.join('{} {} {}'.format(*c) for c in coords))


def _write(cur, schema, srid, nodes, key_ids, sections, pipe_rows, report):
    cur.execute('BEGIN;')
    try:
        for table in MODEL_TABLES:
            cur.execute("""TRUNCATE "{}".{} RESTART IDENTITY;""".format(schema, table))  # nosec B608
        for key, n in nodes.items():
            cur.execute("""INSERT INTO "{}".statics_model_nodes (id, geom, line_ids, vertex_index, kind, junction_id, junction_type,
                angle_deg, bend_class, radius_m, bend_id, source, override_id, override_kind, {})
                VALUES (%s, ST_GeomFromEWKT(%s), %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, {});""".format(
                schema, ', '.join(POINT_OVERRIDE_COLUMNS), ', '.join(['%s'] * len(POINT_OVERRIDE_COLUMNS))),  # nosec B608
                        (key_ids[key], _pointZ(n['coord'], srid), n['line_ids'], n.get('vertex_index'), n['kind'],
                         n.get('junction_id'), n.get('junction_type'), n.get('angle_deg'), n.get('bend_class'),
                         n.get('radius_m'), n.get('bend_id'), n.get('source'), n.get('override_id'), n.get('override_kind'))
                        + tuple(n.get(c) for c in POINT_OVERRIDE_COLUMNS))
        for i, s in enumerate(sections, 1):
            o = s.get('override') or {}
            cur.execute("""INSERT INTO "{}".statics_model_sections (id, geom, line_id, node_from, node_to, length_m, line_type,
                override_id, {}) VALUES (%s, ST_GeomFromEWKT(%s), %s, %s, %s, ST_3DLength(ST_GeomFromEWKT(%s)), %s, %s, {});""".format(
                schema, ', '.join(SECTION_OVERRIDE_COLUMNS), ', '.join(['%s'] * len(SECTION_OVERRIDE_COLUMNS))),  # nosec B608
                (i, _lineZ(s['coords'], srid), s['line_id'], key_ids[s['from']], key_ids[s['to']], _lineZ(s['coords'], srid),
                 s['line_type'], o.get('id')) + tuple(o.get(c) for c in SECTION_OVERRIDE_COLUMNS))
        for si, chain in pipe_rows:
            o = sections[si].get('override') or {}
            cover = float(o['cover_m']) if o.get('cover_m') is not None else chain['cover']
            cur.execute("""INSERT INTO "{}".statics_model_pipes (geom, section_id, line_id, sequences, pipe_ids, twin, system_type,
                series_id, d_inner_m, d_outer_m, wall_m, casing_d_m, cover_m, x_m, y_m, min_bend_radius_m)
                VALUES (ST_Force3D(ST_OffsetCurve(ST_Force2D(ST_GeomFromEWKT(%s)), %s)), %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s);""".format(schema),  # nosec B608
                        (_lineZ(sections[si]['coords'], srid), chain['x'], si + 1, sections[si]['line_id'],
                         chain['sequences'], chain['pipe_ids'], chain['twin'], chain['system_type'], chain['series_id'],
                         chain['d_inner'], chain['d_outer'], chain['wall'], chain['casing_d'], cover, chain['x'],
                         chain['y'], chain['min_bend_radius_m']))
        cur.execute("""INSERT INTO "{}".statics_model_build (fingerprint, report) VALUES (%s, %s);""".format(schema),  # nosec B608
                    (fingerprint(cur, schema), json.dumps(report, default=float)))
        cur.execute('COMMIT;')
    except Exception:
        cur.execute('ROLLBACK;')
        raise



# ---------------------------------------------------------------- report text
def formatReport(report):
    """(summary, details) texts of a build report for the user."""
    from .translations import tr_msg
    counts = report['counts']
    classes = ', '.join('{}: {}'.format(tr_msg(BEND_CLASS_NAMES[c]), n) for c, n in counts['nodes_by_class'].items())
    summary = tr_msg('Statics model built: {} lines, {} nodes ({}), {} sections, {} pipe rows.').format(
        counts['lines'], counts['nodes'], classes, counts['sections'], counts['pipes'])
    issues = sum(len(report[k]) for k in ('skipped_lines', 'negative_cover', 'runs_not_merged', 'tight_bends',
                                           'points_ambiguous', 'points_unmatched', 'sections_unmatched'))
    if issues:
        summary += '\n' + tr_msg('{} findings, see the details.').format(issues)
    lines = [tr_msg('Parameters') + ': ' + ', '.join('{} = {:g}'.format(k, v) for k, v in report['parameters'].items())]

    def section(title, items, fmt):
        if items:
            lines.append('')
            lines.append('{} ({})'.format(title, len(items)))
            lines.extend('  ' + fmt(i) for i in items)

    section(tr_msg('Skipped lines'), report['skipped_lines'], lambda i: tr_msg('line {}: {}').format(i['line_id'], i['reason']))
    section(tr_msg('Negative cover'), report['negative_cover'],
            lambda i: tr_msg('line {}, pipes {}: {:.3f} m').format(i['line_id'], i['pipe_ids'], i['cover_m']))
    section(tr_msg('Runs of small kinks not merged (radius below the elastic limit)'), report['runs_not_merged'],
            lambda i: tr_msg('line {}, vertices {}: radius {:.1f} m').format(i['line_id'], i['vertex_indexes'], i['radius_m']))
    section(tr_msg('Bends below the minimum bend radius'), report['tight_bends'],
            lambda i: tr_msg('line {}, pipes {}, node {}: radius {:.2f} m < {:.2f} m').format(
                i['line_id'], i['pipe_ids'], i['node'], i['radius_m'], i['min_bend_radius_m']))
    section(tr_msg('Pipes without series (treated as rigid)'), report['pipes_without_series'], str)
    section(tr_msg('Point overrides applied'), report['points_applied'], str)
    section(tr_msg('Point overrides ambiguous (not applied)'), report['points_ambiguous'], str)
    section(tr_msg('Point overrides without a match'), report['points_unmatched'], str)
    section(tr_msg('Section overrides applied'), report['sections_applied'], str)
    section(tr_msg('Section overrides without a match'), report['sections_unmatched'], str)
    return summary, '\n'.join(lines)


BEND_CLASS_NAMES = {sm.BEND_NONE: 'no bend', sm.BEND_KINK: 'small-angle kink', sm.BEND_PREFAB: 'prefabricated bend',
                    sm.BEND_ELASTIC: 'elastic bend'}
