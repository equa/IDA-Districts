"""Local loss coefficients (zeta) at the junctions: tee and cross with constant values of the flow paths (typical orders
of magnitude as default values, set by the user in the dialogs), reducer from the sudden contraction/expansion.

Every connection of a junction (junction_connections) gets the zeta value that is added to its line in the network model,
referenced to the velocity of that line. The model adds to a line: lines.zeta (user values, free) + sum over its junctions
of junctions.zeta / 2 (user values, as before) + junction_connections.zeta (calculated here).

A flow through a junction passes two of its connections, so it sees the sum of their values:
  - tee / cross: straight run (Durchgang, the two pipes in line) ZETA_RUN, branch (Abzweig) ZETA_BRANCH.
    The run lines get ZETA_RUN/2 each, a branch line ZETA_BRANCH - ZETA_RUN/2 (path branch + run = ZETA_BRANCH).
  - reducer (2 connections with different diameters, only these are left after merging the lines):
    the smaller line gets the loss of the sudden contraction/expansion, the larger one 0.
  - a run of a tee/cross with different diameters: the smaller run line gets the reducer loss in addition.
The tee/cross values are constant (real values depend on the flow ratio and the area ratio, see e.g. Idelchik) and the
same for diverging and combining flow (supply and return of a pipe bundle flow in opposite directions); the reducer value
is the mean of the contraction and the expansion (sharp-edged fittings, conical reducers have lower losses).
The run is the pair of lines with the largest diameters, with equal diameters the pair that is the most in line."""
import math
from decimal import Decimal

import psycopg2.extras
from qgis.core import (
    Qgis, QgsFeature, QgsGeometry, QgsPalLayerSettings, QgsProject, QgsRuleBasedRenderer, QgsStyle, QgsSymbol,
    QgsTextFormat, QgsVectorLayer, QgsVectorLayerSimpleLabeling,
)
from qgis.PyQt.QtGui import QColor

from .translations import tr

# default values (typical orders of magnitude, no table values; the user can change them in the dialogs):
# number of connections -> zeta of the flow path; 4 is used for all junctions with more than 4 connections
ZETA_RUN = {3: 0.4, 4: 0.5}        # straight run (Durchgang) of a tee / cross
ZETA_BRANCH = {3: 1.4, 4: 1.5}     # branch (Abzweig) of a tee / cross
# keys of the values in the dialogs and the settings
ZETA_VALUE_KEYS = {'tee_run': (ZETA_RUN, 3), 'tee_branch': (ZETA_BRANCH, 3), 'cross_run': (ZETA_RUN, 4),
                   'cross_branch': (ZETA_BRANCH, 4)}
ZETA_DEFAULTS = {key: table[n] for key, (table, n) in ZETA_VALUE_KEYS.items()}
ZETA_SETTINGS_PREFIX = 'districts/junction_zeta/'
DIAMETER_EQUAL_RTOL = 0.01         # diameters within 1 % are equal (no reducer, run chosen by the geometry)


def zetaTables(values=None):
    """(run, branch) tables {number of connections: zeta} from the values {'tee_run', 'tee_branch', 'cross_run',
    'cross_branch'} (missing keys: default values)"""
    values = dict(ZETA_DEFAULTS, **(values or {}))
    return ({3: values['tee_run'], 4: values['cross_run']}, {3: values['tee_branch'], 4: values['cross_branch']})


def loadZetaValues():
    """values last used in the dialogs (QgsSettings), default values otherwise"""
    from qgis.core import QgsSettings
    settings = QgsSettings()
    values = {}
    for key, default in ZETA_DEFAULTS.items():
        try:
            values[key] = float(settings.value(ZETA_SETTINGS_PREFIX + key, default))
        except (TypeError, ValueError):
            values[key] = default
    return values


def saveZetaValues(values):
    from qgis.core import QgsSettings
    settings = QgsSettings()
    for key in ZETA_DEFAULTS:
        if key in values:
            settings.setValue(ZETA_SETTINGS_PREFIX + key, float(values[key]))

ZETA_PROPERTY = 'districts_zeta'
ZETA_LAYERS = ['lines', 'connections']
# translation keys of the layer names
ZETA_LAYER_NAMES = {'lines': 'lines', 'connections': 'junction_connections'}
ZERO_COLOR = '#b4b4b4'


# ---------------------------------------------------------------- calculation
def reducerZeta(d_small, d_large):
    """mean of the sudden contraction 0.5*(1-b) and expansion (1-b)^2 (b = area ratio), referenced to the velocity in the small pipe"""
    if not d_small or not d_large or d_small >= d_large * (1 - DIAMETER_EQUAL_RTOL):
        return 0.0
    b = (d_small / d_large) ** 2
    return (0.5 * (1 - b) + (1 - b) ** 2) / 2


def _equal(d1, d2):
    if not d1 or not d2:
        return True  # unknown diameter: no reducer
    return abs(d1 - d2) <= DIAMETER_EQUAL_RTOL * max(d1, d2)


def _straightness(az1, az2):
    """1 if the lines leave the junction in opposite directions (in line), -1 if they overlap"""
    if az1 is None or az2 is None:
        return 0.0
    return -math.cos(az1 - az2)


def connectionZetas(connections, values=None):
    """connections of one junction: [{'id', 'd' (inner diameter or None), 'az' (azimuth of the line leaving the junction)}].
    values: zeta of the flow paths {'tee_run', 'tee_branch', 'cross_run', 'cross_branch'} (default values if missing).
    Returns {connection id: (zeta, role)}, role: 'end', 'none', 'reducer_small', 'reducer_large', 'run', 'branch'."""
    zeta_run, zeta_branch = zetaTables(values)
    n = len(connections)
    if n <= 1:
        return {c['id']: (0.0, 'end') for c in connections}
    if n == 2:
        c1, c2 = sorted(connections, key=lambda c: c['d'] or 0)
        if _equal(c1['d'], c2['d']):
            return {c1['id']: (0.0, 'none'), c2['id']: (0.0, 'none')}
        return {c1['id']: (reducerZeta(c1['d'], c2['d']), 'reducer_small'), c2['id']: (0.0, 'reducer_large')}
    k = min(n, 4)
    # run: the pairs with the largest diameters (the smaller one of the pair, equal within the tolerance), of these the most in line
    pairs = [(a, b) for i, a in enumerate(connections) for b in connections[i + 1:]]
    d_pair = {id(p): min(p[0]['d'] or 0, p[1]['d'] or 0) for p in pairs}
    d_best = max(d_pair.values())
    candidates = [p for p in pairs if d_pair[id(p)] >= d_best * (1 - DIAMETER_EQUAL_RTOL)]
    run = max(candidates, key=lambda p: _straightness(p[0]['az'], p[1]['az']))
    result = {}
    for c in connections:
        if c in run:
            result[c['id']] = (zeta_run[k] / 2, 'run')
        else:
            # never negative (a branch value smaller than half of the run value)
            result[c['id']] = (max(0.0, zeta_branch[k] - zeta_run[k] / 2), 'branch')
    small, large = sorted(run, key=lambda c: c['d'] or 0)
    if not _equal(small['d'], large['d']):
        zeta, role = result[small['id']]
        result[small['id']] = (zeta + reducerZeta(small['d'], large['d']), role)
    return result


def ensureConnectionZetaColumn(cur, schema):
    """add the column zeta to junction_connections of the schema (projects created before it existed)"""
    if hasConnectionZetaColumn(cur, schema):
        return  # no ALTER TABLE (it waits for the locks of the loaded layers)
    cur.execute('ALTER TABLE "{}".junction_connections ADD COLUMN IF NOT EXISTS zeta numeric;'.format(schema))  # nosec B608


def hasConnectionZetaColumn(cur, schema):
    cur.execute("""SELECT EXISTS (SELECT 1 FROM information_schema.columns
    WHERE table_schema = %s AND table_name = 'junction_connections' AND column_name = 'zeta') AS e;""", (schema,))
    return cur.fetchone()['e']


def hasCalculatedJunctionZeta(cur, schema):
    """True if junction connections of the schema have calculated zeta values"""
    if not hasConnectionZetaColumn(cur, schema):
        return False
    cur.execute('SELECT EXISTS (SELECT 1 FROM "{}".junction_connections WHERE zeta IS NOT NULL) AS e;'.format(schema))  # nosec B608
    return cur.fetchone()['e']


def connectionRows(cur, schema, network=None):
    """connections of the junctions (of the network) with the inner diameter and the direction of the line at the junction"""
    cur.execute("""SELECT jc.id, jc.jid, jc.lid, d.d,
       CASE WHEN ST_Distance(ST_StartPoint(l.geom), j.geom) <= ST_Distance(ST_EndPoint(l.geom), j.geom)
            THEN ST_Azimuth(ST_Force2D(ST_PointN(l.geom, 1)), ST_Force2D(ST_PointN(l.geom, 2)))
            ELSE ST_Azimuth(ST_Force2D(ST_PointN(l.geom, ST_NPoints(l.geom))), ST_Force2D(ST_PointN(l.geom, ST_NPoints(l.geom) - 1)))
       END AS az
FROM "{s}".junction_connections jc
JOIN "{s}".junctions j ON j.id = jc.jid
JOIN "{s}".lines l ON l.id = jc.lid
LEFT JOIN (SELECT bp.pipe_bundle_type_id, max(p.innerpipediameter) AS d
           FROM public.bundle_pipes bp JOIN public.pipes p ON p.id = bp.pipe_id
           GROUP BY bp.pipe_bundle_type_id) d ON d.pipe_bundle_type_id = l.pipe_bundle_type_id
WHERE %(network)s IS NULL OR j.network = %(network)s
ORDER BY jc.jid, jc.id;""".format(s=schema),  # nosec B608
                {'network': None if network is None else int(network)})
    junctions = {}
    for row in cur.fetchall():
        junctions.setdefault(row['jid'], []).append({'id': row['id'], 'lid': row['lid'],
                                                     'd': float(row['d']) if row['d'] is not None else None,
                                                     'az': row['az']})
    return junctions


def updateJunctionZeta(cur, schema='temp', network=None, values=None):
    """calculate junction_connections.zeta of the junctions (of the network) from the zeta values of the tee and cross
    (values {'tee_run', 'tee_branch', 'cross_run', 'cross_branch'}, default values if None) and the reducer equation.
    Run after the lines are merged and the pipe bundles are final. Returns the number of junctions."""
    ensureConnectionZetaColumn(cur, schema)
    junctions = connectionRows(cur, schema, network)
    rows = []
    for connections in junctions.values():
        for cid, (zeta, _role) in connectionZetas(connections, values).items():
            rows.append((cid, round(zeta, 4)))
    if rows:
        psycopg2.extras.execute_values(cur, """UPDATE "{}".junction_connections jc SET zeta = v.zeta::numeric
FROM (VALUES %s) AS v(id, zeta) WHERE jc.id = v.id;""".format(schema), rows, page_size=5000)  # nosec B608
    return len(junctions)


# ---------------------------------------------------------------- visualization
def removeZetaLayers():
    """remove the zeta layers and the group if it is empty"""
    project = QgsProject.instance()
    for layer in list(project.mapLayers().values()):
        if layer.customProperty(ZETA_PROPERTY):
            project.removeMapLayer(layer.id())
    group = project.layerTreeRoot().findGroup(tr('@default', 'zeta_values'))
    if group is not None and not group.children():
        group.parent().removeChildNode(group)


def zetaGroup():
    root = QgsProject.instance().layerTreeRoot()
    group = root.findGroup(tr('@default', 'zeta_values'))
    if group is None:
        group = root.insertGroup(0, tr('@default', 'zeta_values'))
    return group


def createZetaLayer(name, geom_type, srid, fields, rows):
    uri = "{}?crs=EPSG:{}&{}".format(geom_type, srid, '&'.join('field={}:{}'.format(n, t) for n, t in fields))
    layer = QgsVectorLayer(uri, name, 'memory')
    features = []
    for row in rows:
        f = QgsFeature(layer.fields())
        f.setGeometry(QgsGeometry.fromWkt(row['wkt']))
        f.setAttributes([float(row[n]) if isinstance(row[n], Decimal) else row[n] for n, _ in fields])
        features.append(f)
    layer.dataProvider().addFeatures(features)
    layer.updateExtents()
    layer.setCustomProperty(ZETA_PROPERTY, True)
    QgsProject.instance().addMapLayer(layer, False)
    zetaGroup().addLayer(layer)
    return layer


def zetaRenderer(geometry_type, value_field, bounds, ramp_name, invert_ramp, unit=''):
    """rule based renderer with the class bounds, value 0 (or missing) gray"""
    from .layer_visualization import turboColor
    ramp = QgsStyle.defaultStyle().colorRamp(ramp_name)
    root = QgsRuleBasedRenderer.Rule(None)
    n = len(bounds)
    for i, (lo, hi) in enumerate(bounds):
        t = i / (n - 1) if n > 1 else 0.5
        if invert_ramp:
            t = 1.0 - t
        symbol = QgsSymbol.defaultSymbol(geometry_type)
        symbol.setColor(ramp.color(t) if ramp else turboColor(t))
        conds = ['"{}" > 0'.format(value_field)]
        if i > 0:
            conds.append('"{}" >= {!r}'.format(value_field, lo))
        if i < n - 1:
            conds.append('"{}" < {!r}'.format(value_field, hi))
        if geometry_type == Qgis.GeometryType.Line:
            symbol.setWidth(1.2)
        else:
            symbol.setSize(3)
        root.appendChild(QgsRuleBasedRenderer.Rule(symbol, filterExp=' AND '.join(conds), label='{:.2f} – {:.2f}{}'.format(lo, hi, unit)))
    symbol = QgsSymbol.defaultSymbol(geometry_type)
    symbol.setColor(QColor(ZERO_COLOR))
    if geometry_type == Qgis.GeometryType.Line:
        symbol.setWidth(0.6)
    else:
        symbol.setSize(2)
    root.appendChild(QgsRuleBasedRenderer.Rule(symbol, filterExp='coalesce("{}", 0) <= 0'.format(value_field), label='0'))
    return QgsRuleBasedRenderer(root)


def setValueLabels(layer, field):
    settings = QgsPalLayerSettings()
    settings.fieldName = 'format_number("{}", 2)'.format(field)
    settings.isExpression = True
    text_format = QgsTextFormat()
    text_format.setSize(8)
    buffer = text_format.buffer()
    buffer.setEnabled(True)
    buffer.setSize(0.8)
    text_format.setBuffer(buffer)
    settings.setFormat(text_format)
    if layer.geometryType() == Qgis.GeometryType.Line:
        settings.placement = Qgis.LabelPlacement.Line
    layer.setLabeling(QgsVectorLayerSimpleLabeling(settings))
    layer.setLabelsEnabled(True)


def frictionFactor(d, roughness, velocity, viscosity):
    """Darcy friction factor: laminar 64/Re, turbulent Swamee-Jain (explicit approximation of Colebrook-White)"""
    if not d or not velocity or not viscosity:
        return None
    re = velocity * d / viscosity
    if re < 2300:
        return 64 / re
    return 0.25 / math.log10((roughness or 0) / (3.7 * d) + 5.74 / re ** 0.9) ** 2


def zetaLineRows(cur, schema, friction=None):
    """lines with the zeta values used in the network model.
    friction {'velocity': m/s, 'viscosity': m2/s}: also the pipe friction as zeta (lambda * L / d, largest pipe of the bundle)
    and the share of the local losses (zeta_total) in % of it"""
    cur.execute("""SELECT l.id, l.network, l.pipe_bundle_type_id, coalesce(l.zeta, 0) AS zeta_line,
       coalesce(z.zeta_j, 0) AS zeta_junctions, coalesce(z.zeta_c, 0) AS zeta_connections,
       coalesce(l.zeta, 0) + coalesce(z.zeta_j, 0) + coalesce(z.zeta_c, 0) AS zeta_total,
       ST_3DLength(l.geom) AS length_m, p.d AS d_m, p.roughness, ST_AsText(l.geom) AS wkt
FROM "{s}".lines l
LEFT JOIN (SELECT jc.lid, sum(coalesce(j.zeta, 0) / 2) AS zeta_j, sum(coalesce(jc.zeta, 0)) AS zeta_c
           FROM "{s}".junction_connections jc JOIN "{s}".junctions j ON j.id = jc.jid GROUP BY jc.lid) z ON z.lid = l.id
LEFT JOIN (SELECT DISTINCT ON (bp.pipe_bundle_type_id) bp.pipe_bundle_type_id, p.innerpipediameter AS d, p.piperoughnessfactor AS roughness
           FROM public.bundle_pipes bp JOIN public.pipes p ON p.id = bp.pipe_id
           ORDER BY bp.pipe_bundle_type_id, p.innerpipediameter DESC) p ON p.pipe_bundle_type_id = l.pipe_bundle_type_id
WHERE l.geom IS NOT NULL ORDER BY l.id;""".format(s=schema))  # nosec B608
    rows = [dict(r) for r in cur.fetchall()]
    if friction:
        for r in rows:
            d = float(r['d_m']) if r['d_m'] is not None else None
            lam = frictionFactor(d, float(r['roughness'] or 0), friction['velocity'], friction['viscosity'])
            r['lambda'] = lam
            r['zeta_friction'] = lam * float(r['length_m']) / d if lam else None
            r['local_share_pct'] = float(r['zeta_total']) / r['zeta_friction'] * 100 if r['zeta_friction'] else None
    return rows


def zetaConnectionRows(cur, schema):
    """one point per connection on its line near the junction (1/4 of the line, at most 3 m) with the zeta added to the line"""
    cur.execute("""SELECT jc.id, jc.jid, jc.lid, coalesce(jc.zeta, 0) AS zeta_connection, coalesce(j.zeta, 0) / 2 AS zeta_junction_half,
       coalesce(jc.zeta, 0) + coalesce(j.zeta, 0) / 2 AS zeta,
       ST_AsText(ST_LineInterpolatePoint(l.geom,
           CASE WHEN ST_Distance(ST_StartPoint(l.geom), j.geom) <= ST_Distance(ST_EndPoint(l.geom), j.geom)
                THEN f.f ELSE 1 - f.f END)) AS wkt
FROM "{s}".junction_connections jc
JOIN "{s}".junctions j ON j.id = jc.jid
JOIN "{s}".lines l ON l.id = jc.lid
CROSS JOIN LATERAL (SELECT least(0.25, 3.0 / nullif(ST_Length(l.geom), 0)) AS f) f
WHERE l.geom IS NOT NULL AND f.f IS NOT NULL
ORDER BY jc.id;""".format(s=schema))  # nosec B608
    return cur.fetchall()


def classBounds(values, n_classes, quantile=False):
    """equal intervals or quantiles (equal count: short lines with a high share don't squeeze all other lines into one class)
    of the values > 0"""
    values = sorted(v for v in values if v and v > 0)
    if not values:
        return [(0.0, 0.0)]
    lo, hi = values[0], values[-1]
    if hi <= lo:
        return [(lo, hi)]
    if quantile:
        cuts = [values[min(len(values) - 1, round(i * len(values) / n_classes))] for i in range(n_classes + 1)]
        cuts[0], cuts[-1] = lo, hi
        bounds = [(a, b) for a, b in zip(cuts, cuts[1:]) if b > a]
        return bounds or [(lo, hi)]
    step = (hi - lo) / n_classes
    return [(lo + i * step, lo + (i + 1) * step) for i in range(n_classes)]


def showZetaValues(cur, schema, layer_names, ramp_name='Turbo', invert_ramp=False, n_classes=5, labels=True,
                   friction=None, color_by_share=False):
    """memory layers in the group 'zeta values': lines colored by the total zeta of the network model,
    connections (points on the lines near the junctions) by the zeta added to the line (the junctions are no layer: the
    sum of their connections is no loss of a flow path and is not used in the simulation).
    friction {'velocity': m/s, 'viscosity': m2/s}: the lines also get the pipe friction as zeta (lambda * L / d) and the share
    of the local losses in % of it (color_by_share: lines colored by this share, quantile classes).
    Returns {layer_name: (n_features, n_with_value, max_value)} and with friction 'local_share_median' (%)."""
    from .height_check import getSrid
    removeZetaLayers()
    ensureConnectionZetaColumn(cur, schema)
    result = {}
    # points on top of the lines
    for layer_name in [n for n in ['connections', 'lines'] if n in layer_names]:
        unit, quantile = '', False
        if layer_name == 'lines':
            rows = zetaLineRows(cur, schema, friction)
            fields = [('id', 'integer'), ('network', 'integer'), ('pipe_bundle_type_id', 'integer'), ('zeta_line', 'double'),
                      ('zeta_junctions', 'double'), ('zeta_connections', 'double'), ('zeta_total', 'double')]
            geom_type, value_field, srid_table = 'LineStringZ', 'zeta_total', 'lines'
            if friction:
                fields += [('length_m', 'double'), ('d_m', 'double'), ('lambda', 'double'), ('zeta_friction', 'double'),
                           ('local_share_pct', 'double')]
                shares = sorted(r['local_share_pct'] for r in rows if r['local_share_pct'] is not None)
                if shares:
                    result['local_share_median'] = shares[len(shares) // 2]
                if color_by_share:
                    value_field, unit, quantile = 'local_share_pct', ' %', True
        else:
            rows = zetaConnectionRows(cur, schema)
            fields = [('id', 'integer'), ('jid', 'integer'), ('lid', 'integer'), ('zeta_connection', 'double'),
                      ('zeta_junction_half', 'double'), ('zeta', 'double')]
            geom_type, value_field, srid_table = 'PointZ', 'zeta', 'lines'
        values = [float(r[value_field]) if r[value_field] is not None else 0.0 for r in rows]
        name = '{} – {}'.format(tr('@default', ZETA_LAYER_NAMES[layer_name]), tr('@default', 'zeta'))
        layer = createZetaLayer(name, geom_type, getSrid(cur, schema, srid_table), fields, rows)
        layer.setRenderer(zetaRenderer(layer.geometryType(), value_field, classBounds(values, n_classes, quantile), ramp_name,
                                       invert_ramp, unit))
        if labels and layer_name == 'connections':
            setValueLabels(layer, value_field)
        layer.triggerRepaint()
        result[layer_name] = (len(rows), sum(1 for v in values if v > 0), max(values) if values else 0.0)
    return result
