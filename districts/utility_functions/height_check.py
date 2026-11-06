"""Height check of the network features (z values of the geometries):
graduated colors by height or a consistency check (missing heights, height jumps at connections and along the lines).
The results are memory layers in the layer group 'height check' (snapshot of the DB, run the check again after edits)."""
from qgis.core import (
    Qgis, QgsCategorizedSymbolRenderer, QgsFeature, QgsGeometry, QgsProject, QgsRendererCategory, QgsRuleBasedRenderer,
    QgsStyle, QgsSymbol, QgsVectorLayer,
)
from qgis.PyQt.QtCore import Qt
from qgis.PyQt.QtGui import QColor

from .translations import tr

HEIGHT_CHECK_PROPERTY = 'districts_height_check'
HEIGHT_CHECK_LAYERS = ['customers', 'energy_plants', 'lines', 'junctions']
POINT_LAYERS = ['customers', 'energy_plants', 'junctions']
MODE_GRADUATED = 'graduated'
MODE_CONSISTENCY = 'consistency'
# same default tolerance as the network topology (lines/nodes closer than this are connected)
CONNECT_TOLERANCE = 0.01
MISSING_COLOR = '#ff00ff'
ISSUE_COLOR = '#e31a1c'


def missingSql(z, zero_is_missing=True):
    """SQL condition: height z missing (NULL, NaN and optionally 0)"""
    cond = "{z} IS NULL OR {z} = 'NaN'::float8".format(z=z)
    if zero_is_missing:
        cond += " OR {z} = 0".format(z=z)
    return "(" + cond + ")"


def getSrid(cur, schema, table):
    """SRID of the geometry column (from the data if the column has no SRID constraint)"""
    cur.execute("""SELECT coalesce(nullif(Find_SRID(%s, %s, 'geom'), 0),
                    (SELECT ST_SRID(geom) FROM "{}".{} WHERE geom IS NOT NULL LIMIT 1)) AS srid;""".format(schema, table),  # nosec B608
                (schema, table))
    return int(cur.fetchone()['srid'] or 0)


def tableExists(cur, schema, table):
    cur.execute("SELECT to_regclass(%s) IS NOT NULL AS e;", ('"{}".{}'.format(schema, table),))
    return cur.fetchone()['e']


# ---------------------------------------------------------------- layers
def removeHeightCheckLayers(mode=None):
    """Remove the height check layers (of the given mode or all) and the group if it is empty"""
    project = QgsProject.instance()
    for layer in list(project.mapLayers().values()):
        prop = layer.customProperty(HEIGHT_CHECK_PROPERTY)
        if prop and (mode is None or prop == mode):
            project.removeMapLayer(layer.id())
    group = project.layerTreeRoot().findGroup(tr('@default', 'height_check'))
    if group is not None and not group.children():
        group.parent().removeChildNode(group)


def heightCheckGroup():
    root = QgsProject.instance().layerTreeRoot()
    group = root.findGroup(tr('@default', 'height_check'))
    if group is None:
        group = root.insertGroup(0, tr('@default', 'height_check'))
    return group


def createMemoryLayer(name, geom_type, srid, fields, rows, mode):
    """memory layer with the fields [(name, type)] and rows (dicts with the field values and 'wkt')"""
    uri = "{}?crs=EPSG:{}&{}".format(geom_type, srid, '&'.join('field={}:{}'.format(n, t) for n, t in fields))
    layer = QgsVectorLayer(uri, name, 'memory')
    features = []
    for row in rows:
        f = QgsFeature(layer.fields())
        f.setGeometry(QgsGeometry.fromWkt(row['wkt']))
        f.setAttributes([row[n] for n, _ in fields])
        features.append(f)
    layer.dataProvider().addFeatures(features)
    layer.updateExtents()
    layer.setCustomProperty(HEIGHT_CHECK_PROPERTY, mode)
    QgsProject.instance().addMapLayer(layer, False)
    heightCheckGroup().addLayer(layer)
    return layer


def baseSymbol(geometry_type, color, issue=None):
    symbol = QgsSymbol.defaultSymbol(geometry_type)
    symbol.setColor(QColor(color))
    if geometry_type == Qgis.GeometryType.Line:
        symbol.setWidth(1.5 if issue else 1.0)
        if issue == 'z_missing':
            symbol.symbolLayer(0).setPenStyle(Qt.PenStyle.DashLine)
    else:
        symbol.setSize(4 if issue else 3)
        sl = symbol.symbolLayer(0)
        if issue == 'z_missing':
            sl.setShape(Qgis.MarkerShape.Cross2)
            sl.setStrokeColor(QColor(color))
            sl.setStrokeWidth(0.6)
        else:
            sl.setStrokeColor(QColor('#202020'))
    return symbol


# ---------------------------------------------------------------- graduated
def graduatedRows(cur, schema, layer_name, zero_is_missing):
    if layer_name == 'lines':
        # one row per segment between two vertices with the attributes of its line and of the segment
        sql = """WITH line AS (
    SELECT l.id, ST_Z(ST_StartPoint(l.geom)) AS z_start, ST_Z(ST_EndPoint(l.geom)) AS z_end,
           s.z_min, s.z_max, s.z_mean, ST_Z(ST_EndPoint(l.geom)) - ST_Z(ST_StartPoint(l.geom)) AS dz,
           s.n_missing > 0 AS z_missing
    FROM "{s}".lines l
    CROSS JOIN LATERAL (
        SELECT min(z) FILTER (WHERE NOT {m}) AS z_min, max(z) FILTER (WHERE NOT {m}) AS z_max,
               avg(z) FILTER (WHERE NOT {m}) AS z_mean, count(*) FILTER (WHERE {m}) AS n_missing
        FROM (SELECT ST_Z(d.geom) AS z FROM ST_DumpPoints(l.geom) d) p
    ) s
    WHERE l.geom IS NOT NULL
), vertex AS (
    SELECT l.id, d.path[1] AS n, lag(d.geom) OVER w AS g0, d.geom AS g1
    FROM "{s}".lines l, ST_DumpPoints(l.geom) d
    WHERE l.geom IS NOT NULL
    WINDOW w AS (PARTITION BY l.id ORDER BY d.path[1])
)
SELECT line.*, v.n - 1 AS seg, (ST_Z(v.g0) + ST_Z(v.g1)) / 2 AS z_seg, ST_Z(v.g1) - ST_Z(v.g0) AS seg_dz,
       abs(ST_Z(v.g1) - ST_Z(v.g0)) / nullif(ST_Distance(v.g0, v.g1), 0) * 100 AS seg_slope_pct,
       ({m0} OR {m1}) AS seg_missing, ST_AsText(ST_MakeLine(v.g0, v.g1)) AS wkt
FROM vertex v JOIN line ON line.id = v.id
WHERE v.g0 IS NOT NULL
ORDER BY v.id, v.n;""".format(s=schema, m=missingSql('z', zero_is_missing), m0=missingSql('ST_Z(v.g0)', zero_is_missing),  # nosec B608
                              m1=missingSql('ST_Z(v.g1)', zero_is_missing))
    else:
        sql = """SELECT id, ST_Z(geom) AS z, {m} AS z_missing, ST_AsText(geom) AS wkt
FROM "{s}".{t} WHERE geom IS NOT NULL ORDER BY id;""".format(s=schema, t=layer_name, m=missingSql('ST_Z(geom)', zero_is_missing))  # nosec B608
    cur.execute(sql)
    return cur.fetchall()


def classBounds(z_min, z_max, n_classes):
    if z_max <= z_min:
        return [(z_min, z_max)]
    step = (z_max - z_min) / n_classes
    return [(z_min + i * step, z_min + (i + 1) * step) for i in range(n_classes)]


def heightRenderer(geometry_type, value_field, bounds, ramp_name, invert_ramp, missing_field='z_missing'):
    """rule based renderer like a graduated one with equal intervals and an extra rule for the missing heights
    (the class bounds are the same for all layers, so equal colors mean equal heights)"""
    from .layer_visualization import turboColor
    ramp = QgsStyle.defaultStyle().colorRamp(ramp_name)
    root = QgsRuleBasedRenderer.Rule(None)
    n = len(bounds)
    for i, (lo, hi) in enumerate(bounds):
        t = i / (n - 1) if n > 1 else 0.5
        if invert_ramp:
            t = 1.0 - t
        color = ramp.color(t) if ramp else turboColor(t)
        conds = ['NOT "{}"'.format(missing_field), '"{}" IS NOT NULL'.format(value_field)]
        # first/last class open, so rounding never drops a feature
        if i > 0:
            conds.append('"{}" >= {!r}'.format(value_field, lo))
        if i < n - 1:
            conds.append('"{}" < {!r}'.format(value_field, hi))
        label = '{:.1f} – {:.1f} m'.format(lo, hi)
        root.appendChild(QgsRuleBasedRenderer.Rule(baseSymbol(geometry_type, color), filterExp=' AND '.join(conds), label=label))
    root.appendChild(QgsRuleBasedRenderer.Rule(baseSymbol(geometry_type, MISSING_COLOR, 'z_missing'), filterExp='"{}"'.format(missing_field),
                                               label=tr('@default', 'z_missing')))
    return QgsRuleBasedRenderer(root)


def heightGraduated(cur, schema, layer_names, ramp_name='Turbo', invert_ramp=False, n_classes=10, zero_is_missing=True):
    """Memory layers of the selected layers colored by height. The lines are split into their segments between two vertices
    (colored by the mean height of the segment, with the attributes of the line and of the segment).
    Returns {layer_name: (n_features, n_missing)} (lines: number of lines, not segments) or None if no layer has a height."""
    removeHeightCheckLayers(MODE_GRADUATED)
    rows = {}
    for layer_name in layer_names:
        if tableExists(cur, schema, layer_name):
            rows[layer_name] = graduatedRows(cur, schema, layer_name, zero_is_missing)
    values = []
    for layer_name, layer_rows in rows.items():
        for r in layer_rows:
            if layer_name == 'lines':
                # min/max of the vertices with a height (also the valid segments of lines with missing heights are colored)
                values += [r['z_min'], r['z_max']]
            elif not r['z_missing']:
                values.append(r['z'])
    values = [v for v in values if v is not None]
    bounds = classBounds(min(values), max(values), n_classes) if values else [(0.0, 0.0)]

    result = {}
    # points on top of the lines
    for layer_name in sorted(rows, key=lambda n: n != 'lines', reverse=True):
        layer_rows = rows[layer_name]
        if layer_name == 'lines':
            fields = [('id', 'integer'), ('z_mean', 'double'), ('z_min', 'double'), ('z_max', 'double'), ('z_start', 'double'),
                      ('z_end', 'double'), ('dz', 'double'), ('z_missing', 'boolean'),
                      ('seg', 'integer'), ('z_seg', 'double'), ('seg_dz', 'double'), ('seg_slope_pct', 'double'), ('seg_missing', 'boolean')]
            geom_type, value_field, missing_field = 'LineStringZ', 'z_seg', 'seg_missing'
            lines = {r['id']: r['z_missing'] for r in layer_rows}
            result[layer_name] = (len(lines), sum(1 for m in lines.values() if m))
        else:
            fields = [('id', 'integer'), ('z', 'double'), ('z_missing', 'boolean')]
            geom_type, value_field, missing_field = 'PointZ', 'z', 'z_missing'
            result[layer_name] = (len(layer_rows), sum(1 for r in layer_rows if r['z_missing']))
        name = '{} – {}'.format(tr('@default', layer_name), tr('@default', 'height'))
        layer = createMemoryLayer(name, geom_type, getSrid(cur, schema, layer_name), fields, layer_rows, MODE_GRADUATED)
        layer.setRenderer(heightRenderer(layer.geometryType(), value_field, bounds, ramp_name, invert_ramp, missing_field))
        layer.triggerRepaint()
    return result if values else None


# ---------------------------------------------------------------- consistency
def missingPointRows(cur, schema, layer_name, zero_is_missing):
    cur.execute("""SELECT 'z_missing' AS issue, %s AS layer, id AS feature_id, NULL::int AS line_id, ST_Z(geom) AS z,
       NULL::float8 AS z_line, NULL::float8 AS dz, ST_AsText(geom) AS wkt
FROM "{s}".{t} WHERE geom IS NOT NULL AND {m} ORDER BY id;""".format(  # nosec B608
        s=schema, t=layer_name, m=missingSql('ST_Z(geom)', zero_is_missing)), (layer_name,))
    return cur.fetchall()


CHECK_LINES = 'pg_temp.height_check_lines'


def createCheckLines(cur, schema, zero_is_missing):
    """session temp table of the lines without missing heights, with a spatial index
    (the version tables have none: 1000 customers 4.5 s -> 0.1 s)"""
    cur.execute("DROP TABLE IF EXISTS {t}; CREATE TEMP TABLE {t} AS SELECT l.id, l.geom FROM \"{s}\".lines l "
                "WHERE l.geom IS NOT NULL AND NOT EXISTS (SELECT 1 FROM ST_DumpPoints(l.geom) d WHERE {m}); "
                "CREATE INDEX ON {t} USING gist (geom); ANALYZE {t};".format(  # nosec B608
                    t=CHECK_LINES, s=schema, m=missingSql('ST_Z(d.geom)', zero_is_missing)))


def nodeLineRows(cur, schema, layer_name, dz_tolerance, zero_is_missing):
    """nodes (customers, energy plants, junctions) whose height differs from the connected line at the node"""
    cur.execute("""SELECT 'dz_node_line' AS issue, %(layer)s AS layer, n.id AS feature_id, l.id AS line_id, ST_Z(n.geom) AS z,
       lz.z_line, ST_Z(n.geom) - lz.z_line AS dz, ST_AsText(n.geom) AS wkt
FROM "{s}".{t} n
JOIN {lines} l ON ST_DWithin(n.geom, l.geom, %(tol)s)
CROSS JOIN LATERAL (SELECT ST_Z(ST_LineInterpolatePoint(l.geom, ST_LineLocatePoint(l.geom, n.geom))) AS z_line) lz
WHERE NOT {mn} AND abs(ST_Z(n.geom) - lz.z_line) > %(dz)s
ORDER BY n.id, l.id;""".format(  # nosec B608
        s=schema, t=layer_name, lines=CHECK_LINES, mn=missingSql('ST_Z(n.geom)', zero_is_missing)),
        {'layer': layer_name, 'tol': CONNECT_TOLERANCE, 'dz': dz_tolerance})
    return cur.fetchall()


def lineLineRows(cur, dz_tolerance):
    """line ends whose height differs from the connected line (end to end pairs reported once)"""
    cur.execute("""WITH ends AS (
    SELECT id, ST_StartPoint(geom) AS g FROM {lines}
    UNION ALL
    SELECT id, ST_EndPoint(geom) FROM {lines}
)
SELECT 'dz_line_line' AS issue, 'lines' AS layer, e.id AS feature_id, l.id AS line_id, ST_Z(e.g) AS z, lz.z_line,
       ST_Z(e.g) - lz.z_line AS dz, ST_AsText(e.g) AS wkt
FROM ends e
JOIN {lines} l ON l.id <> e.id AND ST_DWithin(e.g, l.geom, %(tol)s)
CROSS JOIN LATERAL (SELECT ST_Z(ST_LineInterpolatePoint(l.geom, ST_LineLocatePoint(l.geom, e.g))) AS z_line) lz
WHERE abs(ST_Z(e.g) - lz.z_line) > %(dz)s
  AND (e.id < l.id OR (NOT ST_DWithin(e.g, ST_StartPoint(l.geom), %(tol)s) AND NOT ST_DWithin(e.g, ST_EndPoint(l.geom), %(tol)s)))
ORDER BY e.id, l.id;""".format(lines=CHECK_LINES),  # nosec B608
        {'tol': CONNECT_TOLERANCE, 'dz': dz_tolerance})
    return cur.fetchall()


def lineIssueRows(cur, schema, dz_tolerance, max_slope_pct, zero_is_missing):
    """lines with missing heights, vertical jumps (height change without horizontal distance) or too steep segments"""
    cur.execute("""WITH v AS (
    SELECT l.id, d.path[1] AS n, d.geom AS g, {m} AS missing FROM "{s}".lines l, ST_DumpPoints(l.geom) d
), seg AS (
    -- segment from the previous vertex to this vertex (dz/dxy NULL for the first vertex)
    SELECT id, missing AS v_missing, missing OR lag(missing) OVER w AS missing, ST_Distance(lag(g) OVER w, g) AS dxy,
           ST_Z(g) - ST_Z(lag(g) OVER w) AS dz
    FROM v WINDOW w AS (PARTITION BY id ORDER BY n)
), per_line AS (
    SELECT id,
           count(*) FILTER (WHERE v_missing) AS n_missing,
           coalesce(bool_or(NOT missing AND abs(dz) > %(dz)s AND dxy <= %(tol)s), false) AS vertical_jump,
           coalesce(bool_or(NOT missing AND abs(dz) > %(dz)s AND dxy > %(tol)s AND abs(dz) / dxy * 100 > %(slope)s), false) AS too_steep,
           max(abs(dz)) FILTER (WHERE NOT missing) AS max_dz,
           max(abs(dz) / dxy * 100) FILTER (WHERE NOT missing AND dxy > %(tol)s) AS max_slope_pct
    FROM seg GROUP BY id
)
SELECT p.id AS line_id,
       CASE WHEN p.n_missing > 0 THEN 'z_missing' WHEN p.vertical_jump THEN 'vertical_jump' ELSE 'too_steep' END AS issue,
       p.n_missing, p.max_dz, p.max_slope_pct, ST_AsText(l.geom) AS wkt
FROM per_line p JOIN "{s}".lines l ON l.id = p.id
WHERE p.n_missing > 0 OR p.vertical_jump OR p.too_steep
ORDER BY p.id;""".format(s=schema, m=missingSql('ST_Z(d.geom)', zero_is_missing)),  # nosec B608
        {'dz': dz_tolerance, 'tol': CONNECT_TOLERANCE, 'slope': max_slope_pct})
    return cur.fetchall()


def issueRenderer(geometry_type, issues):
    categories = []
    for issue in issues:
        color = MISSING_COLOR if issue == 'z_missing' else ISSUE_COLOR
        categories.append(QgsRendererCategory(issue, baseSymbol(geometry_type, color, issue), tr('@default', issue)))
    return QgsCategorizedSymbolRenderer('issue', categories)


def heightConsistency(cur, schema, layer_names, dz_tolerance=0.1, max_slope_pct=20.0, zero_is_missing=True):
    """Marks missing heights, height differences between connected features and jumps/steep segments along the lines.
    Returns {issue: count}."""
    removeHeightCheckLayers(MODE_CONSISTENCY)
    has_lines = tableExists(cur, schema, 'lines')
    point_rows, line_rows = [], []
    if has_lines:
        createCheckLines(cur, schema, zero_is_missing)
    try:
        for layer_name in layer_names:
            if not tableExists(cur, schema, layer_name):
                continue
            if layer_name in POINT_LAYERS:
                point_rows += missingPointRows(cur, schema, layer_name, zero_is_missing)
                if has_lines:
                    point_rows += nodeLineRows(cur, schema, layer_name, dz_tolerance, zero_is_missing)
            elif layer_name == 'lines':
                point_rows += lineLineRows(cur, dz_tolerance)
                line_rows += lineIssueRows(cur, schema, dz_tolerance, max_slope_pct, zero_is_missing)
    finally:
        if has_lines:
            cur.execute("DROP TABLE IF EXISTS {};".format(CHECK_LINES))

    counts = {}
    for r in point_rows + line_rows:
        counts[r['issue']] = counts.get(r['issue'], 0) + 1

    # points first: the first layer of the group is drawn on top
    if point_rows:
        fields = [('issue', 'string'), ('layer', 'string'), ('feature_id', 'integer'), ('line_id', 'integer'), ('z', 'double'),
                  ('z_line', 'double'), ('dz', 'double')]
        srid_table = next(n for n in HEIGHT_CHECK_LAYERS if n in layer_names and tableExists(cur, schema, n))
        layer = createMemoryLayer('{} – {}'.format(tr('@default', 'height_check'), tr('@default', 'points')), 'PointZ',
                                  getSrid(cur, schema, srid_table), fields, point_rows, MODE_CONSISTENCY)
        layer.setRenderer(issueRenderer(layer.geometryType(), ['z_missing', 'dz_node_line', 'dz_line_line']))
    if line_rows:
        fields = [('line_id', 'integer'), ('issue', 'string'), ('n_missing', 'integer'), ('max_dz', 'double'), ('max_slope_pct', 'double')]
        layer = createMemoryLayer('{} – {}'.format(tr('@default', 'height_check'), tr('@default', 'lines')), 'LineStringZ',
                                  getSrid(cur, schema, 'lines'), fields, line_rows, MODE_CONSISTENCY)
        layer.setRenderer(issueRenderer(layer.geometryType(), ['z_missing', 'vertical_jump', 'too_steep']))
    return counts
