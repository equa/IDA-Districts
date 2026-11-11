"""Results of the iterations of the dynamic pipe sizing (dynamic_pipe_sizing.py).

Every iteration is saved as dynamic_sizing_iter<n>.json in the version folder:
    {'iteration', 'started', 'time', 'cid_weak', 'epid_weak', 'dp_net_weak', 'cid_target', 'dp_target', 'quota',
     'spread_sized', 'n_presized', 'n_balancing_steps', 'n_changed', 'outcome',
     'customers': {cid: {'dp', 'dp_sized', 'dp_net', 'epid', 'time'}},
     'lines': {lid: {'mdot', 'mdot_max', 'dp_spez', 'pipe', 'pipe_new', 'changed'}}}
    dp, dp_sized ... differential pressure at the substation simulated / estimated after the sizing [Pa]
    dp_net       ... network pressure loss to the supplying plant [Pa] (the weak point has the largest one)
    mdot         ... design mass flow of the line (sum of the customer mass flows of the flow tracing) [kg/s]
    mdot_max     ... peak mass flow of the line over the whole simulation period [kg/s]
They are shown on the map as memory layers in the group 'dynamic pipe sizing' (one subgroup per iteration):
customers with graduated colors of dp (weak point as bigger point) and lines with graduated colors and widths
of the design mass flow; lines with new pipes are labelled. The class bounds are the same for all iterations.
"""
import glob
import json
import os
import re

from qgis.core import (
    Qgis, QgsFeature, QgsGeometry, QgsPalLayerSettings, QgsProject, QgsRuleBasedRenderer, QgsStyle, QgsSymbol,
    QgsProperty, QgsSingleSymbolRenderer, QgsTextFormat, QgsVectorLayer, QgsVectorLayerSimpleLabeling,
)
from qgis.PyQt.QtCore import Qt
from qgis.PyQt.QtGui import QColor

from .translations import tr_msg

SIZING_PROPERTY = 'districts_dynamic_pipe_sizing'
ITERATION_FILE = 'dynamic_sizing_iter{}.json'
OUTCOMES = ('changed', 'converged', 'oscillation', 'max_iter')
N_CLASSES = 7


# ---------------------------------------------------------------- files
def versionPath(config):
    return os.path.join(config['pathProjects'], config['projectName'], 'versions', config['versionName'])


def iterationSummary(iteration, started, res, opt, outcome, changed):
    """Summary of an iteration (see the module doc) from the results of getCustomerLinePressure (res) and
    optimizePipeDiameters (opt); changed = {lid: {seq: pipe_id}} of the lines with new pipes."""
    catalog, lines = res['catalog'], res['lines']
    customers = {}
    for cid, (dp, _) in res['c_lid'].items():
        dp_net, epid = res['dvar'].get(cid, (None, None))
        customers[str(cid)] = {'dp': dp, 'dp_sized': opt['c_lid'].get(cid, [None])[0], 'dp_net': dp_net, 'epid': epid,
            'time': str(res['times'].get(cid, ''))}
    line_rows = {}
    for lid, line in lines.items():
        seq = min(line['pipes'])
        pipe = line['pipes'][seq]
        new = opt['pipes'].get(lid, {}).get(seq, pipe['pipe_id'])
        line_rows[str(lid)] = {'mdot': abs(pipe['mdot']), 'mdot_max': max(abs(p.get('mdot_max', 0.0)) for p in line['pipes'].values()),
            'dp_spez': res['dp_spez'].get(lid), 'pipe': catalog[pipe['pipe_id']]['name'], 'pipe_new': catalog[new]['name'],
            'changed': lid in changed}
    return {'iteration': iteration, 'started': started, 'time': str(res['time']), 'cid_weak': res['cid_dp'], 'epid_weak': res['epid_dp'],
        'dp_net_weak': res['dp'], 'cid_target': opt['cid_weak'], 'dp_target': opt['dp_target'], 'quota': opt['quota'],
        'spread_sized': opt['spread'], 'n_presized': len(opt['presize']), 'n_balancing_steps': len(opt['history']),
        'n_changed': len(changed), 'outcome': outcome, 'customers': customers, 'lines': line_rows}


def saveIteration(config, summary):
    with open(os.path.join(versionPath(config), ITERATION_FILE.format(summary['iteration'])), 'w', encoding='utf-8') as f:
        json.dump(summary, f, indent=1)


def loadIterations(config):
    """Returns the saved iterations of the loaded version sorted by their number."""
    result = []
    for path in glob.glob(os.path.join(versionPath(config), ITERATION_FILE.format('*'))):
        if re.fullmatch(ITERATION_FILE.format(r'\d+'), os.path.basename(path)):
            with open(path, encoding='utf-8') as f:
                result.append(json.load(f))
    return sorted(result, key=lambda s: s['iteration'])


def deleteIterations(config):
    """Removes the iteration files of a previous run (also the ones copied from the parent version)."""
    for pattern in (ITERATION_FILE.format('*'), 'dynamic_sizing_iter*_c_lid*.json'):
        for path in glob.glob(os.path.join(versionPath(config), pattern)):
            os.remove(path)


def iterationRow(summary):
    """Values of the iteration table: (iteration, critical time, weak point, dp min, dp max, spread, spread sized,
    quota, changed lines, outcome); pressures in bar."""
    dps = [c['dp'] for c in summary['customers'].values() if c['dp'] is not None]
    dp_min, dp_max = (min(dps), max(dps)) if dps else (None, None)
    return (summary['iteration'], summary['time'], '{} ({})'.format(summary['cid_weak'], summary['epid_weak']),
        bar(dp_min), bar(dp_max), bar(dp_max - dp_min) if dps else None, bar(summary['spread_sized']),
        round(100 * summary['quota']), summary['n_changed'], outcomeText(summary['outcome']))


def bar(value):
    return round(value / 1e5, 4) if value is not None else None


def outcomeText(outcome):
    return {'changed': tr_msg('pipes changed'), 'converged': tr_msg('converged'), 'oscillation': tr_msg('oscillation'),
        'max_iter': tr_msg('pipes changed, max. iterations')}.get(outcome, outcome)


# ---------------------------------------------------------------- map layers
def removeSizingLayers(iteration=None):
    """Removes the layers of the given iteration (or all) and the empty groups."""
    project = QgsProject.instance()
    for layer in list(project.mapLayers().values()):
        prop = layer.customProperty(SIZING_PROPERTY)
        if prop is not None and (iteration is None or str(prop) == str(iteration)):
            project.removeMapLayer(layer.id())
    group = project.layerTreeRoot().findGroup(tr_msg('Dynamic pipe sizing'))
    if group is not None:
        for child in list(group.children()):
            if not child.children():
                group.removeChildNode(child)
        if not group.children():
            group.parent().removeChildNode(group)


def sizingGroup(iteration):
    root = QgsProject.instance().layerTreeRoot()
    group = root.findGroup(tr_msg('Dynamic pipe sizing'))
    if group is None:
        group = root.insertGroup(0, tr_msg('Dynamic pipe sizing'))
    name = tr_msg('Iteration {}').format(iteration)
    sub = group.findGroup(name)
    if sub is None:
        # iterations in ascending order
        index = len([c for c in group.children() if (int(re.sub(r'\D', '', c.name()) or 0)) < iteration])
        sub = group.insertGroup(index, name)
    return sub


def createLayer(name, geom_type, srid, fields, rows, iteration):
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
    layer.setCustomProperty(SIZING_PROPERTY, iteration)
    QgsProject.instance().addMapLayer(layer, False)
    sizingGroup(iteration).addLayer(layer)
    return layer


def classBounds(values, n_classes=N_CLASSES):
    values = [v for v in values if v is not None]
    if not values:
        return [(0.0, 0.0)]
    lo, hi = min(values), max(values)
    if hi <= lo:
        return [(lo, hi)]
    step = (hi - lo) / n_classes
    return [(lo + i * step, lo + (i + 1) * step) for i in range(n_classes)]


def classColors(n, ramp_name, invert=False, t_min=0.0, t_max=1.0):
    """n colors of the ramp between t_min and t_max (e.g. without the almost white start of a single hue ramp)"""
    from .layer_visualization import turboColor
    ramp = QgsStyle.defaultStyle().colorRamp(ramp_name)
    colors = []
    for i in range(n):
        t = i / (n - 1) if n > 1 else 0.5
        t = 1.0 - t if invert else t
        t = t_min + t * (t_max - t_min)
        colors.append(ramp.color(t) if ramp else turboColor(t))
    return colors


def classRules(field, bounds, unit, decimals):
    """(filter expression, label) per class; the first and the last class are open."""
    rules = []
    for i, (lo, hi) in enumerate(bounds):
        conds = ['"{}" IS NOT NULL'.format(field)]
        if i > 0:
            conds.append('"{}" >= {!r}'.format(field, lo))
        if i < len(bounds) - 1:
            conds.append('"{}" < {!r}'.format(field, hi))
        rules.append((' AND '.join(conds), '{:.{d}f} – {:.{d}f} {}'.format(lo, hi, unit, d=decimals)))
    return rules


def pointSymbol(color, size, stroke='#202020', stroke_width=0.2):
    symbol = QgsSymbol.defaultSymbol(Qgis.GeometryType.Point)
    symbol.setColor(QColor(color))
    symbol.setSize(size)
    sl = symbol.symbolLayer(0)
    sl.setStrokeColor(QColor(stroke))
    sl.setStrokeWidth(stroke_width)
    return symbol


def lineSymbol(color, width, opacity=1.0):
    symbol = QgsSymbol.defaultSymbol(Qgis.GeometryType.Line)
    symbol.setColor(QColor(color))
    symbol.setWidth(width)
    symbol.setOpacity(opacity)
    symbol.symbolLayer(0).setPenCapStyle(Qt.PenCapStyle.RoundCap)
    return symbol


def customerRenderer(bounds):
    """graduated colors of dp [bar] (red = low, blue = high); the weak point is drawn as a bigger point (and labelled)"""
    colors = classColors(len(bounds), 'Spectral')
    root = QgsRuleBasedRenderer.Rule(None)
    for (exp, label), color in zip(classRules('dp_bar', bounds, 'bar', 3), colors):
        symbol = pointSymbol(color, 3)
        symbol.setDataDefinedSize(QgsProperty.fromExpression('if("weak", 7, 3)'))
        root.appendChild(QgsRuleBasedRenderer.Rule(symbol, filterExp=exp, label=label))
    root.appendChild(QgsRuleBasedRenderer.Rule(pointSymbol('#9e9e9e', 2), filterExp='"dp_bar" IS NULL', label=tr_msg('no result')))
    return QgsRuleBasedRenderer(root)


def lineRenderer(bounds):
    """graduated colors and widths of the design mass flow [kg/s]"""
    colors = classColors(len(bounds), 'Blues', t_min=0.35)
    root = QgsRuleBasedRenderer.Rule(None)
    n = len(bounds)
    for i, ((exp, label), color) in enumerate(zip(classRules('mdot', bounds, 'kg/s', 2), colors)):
        root.appendChild(QgsRuleBasedRenderer.Rule(lineSymbol(color, 0.4 + 1.6 * i / max(n - 1, 1)), filterExp='"mdot" > 0 AND ' + exp, label=label))
    root.appendChild(QgsRuleBasedRenderer.Rule(lineSymbol('#bdbdbd', 0.3), filterExp='coalesce("mdot", 0) = 0', label=tr_msg('no flow')))
    return QgsRuleBasedRenderer(root)


def setLabels(layer, expression, color='#000000', size=8):
    settings = QgsPalLayerSettings()
    settings.fieldName = expression
    settings.isExpression = True
    text_format = QgsTextFormat()
    text_format.setSize(size)
    text_format.setColor(QColor(color))
    buffer = text_format.buffer()
    buffer.setEnabled(True)
    buffer.setSize(0.8)
    text_format.setBuffer(buffer)
    settings.setFormat(text_format)
    layer.setLabeling(QgsVectorLayerSimpleLabeling(settings))
    layer.setLabelsEnabled(True)


def geometries(cur, config, table, ids):
    """{id: wkt (2D)} of the features of the loaded version"""
    cur.execute("""SELECT id, ST_AsText(ST_Force2D(geom)) AS wkt FROM "{}".{} WHERE id = ANY(%s) AND geom IS NOT NULL;""".format(config['versionName'], table),  # nosec B608
        ([int(i) for i in ids],))
    return {str(row['id']): row['wkt'] for row in cur.fetchall()}


def srid(cur, config, table):
    cur.execute("""SELECT ST_SRID(geom) AS srid FROM "{}".{} WHERE geom IS NOT NULL LIMIT 1;""".format(config['versionName'], table))  # nosec B608
    row = cur.fetchone()
    return int(row['srid']) if row else 0


def showIteration(cur, config, summary, all_summaries=None, visible=True):
    """Memory layers of an iteration (customers: dp at the substation, lines: design mass flow, changed pipes).
    The class bounds are taken from all_summaries (default: this one), so the iterations can be compared.
    Returns the created layers."""
    iteration = summary['iteration']
    removeSizingLayers(iteration)
    all_summaries = all_summaries or [summary]
    dp_bounds = classBounds([bar(c['dp']) for s in all_summaries for c in s['customers'].values()])
    mdot_bounds = classBounds([line['mdot'] for s in all_summaries for line in s['lines'].values() if line['mdot'] > 0])

    # layer order (top to bottom): customers, lines, changed lines as a halo below the lines
    wkt = geometries(cur, config, 'customers', summary['customers'])
    customer_rows = [{'id': int(cid), 'dp_bar': bar(c['dp']), 'dp_sized_bar': bar(c['dp_sized']), 'dp_net_bar': bar(c['dp_net']),
        'epid': c['epid'], 'time': c['time'], 'weak': str(summary['cid_weak']) == cid, 'wkt': wkt[cid]}
        for cid, c in summary['customers'].items() if cid in wkt]
    customer_fields = [('id', 'integer'), ('dp_bar', 'double'), ('dp_sized_bar', 'double'), ('dp_net_bar', 'double'), ('epid', 'integer'),
        ('time', 'string'), ('weak', 'boolean')]
    customers = createLayer(tr_msg('Customers – dp substation [bar]'), 'Point', srid(cur, config, 'customers'), customer_fields, customer_rows, iteration)
    customers.setRenderer(customerRenderer(dp_bounds))
    setLabels(customers, "if(\"weak\", '{} ' || \"id\" || ': ' || format_number(\"dp_bar\", 3) || ' bar', '')".format(tr_msg('weak point')))

    wkt = geometries(cur, config, 'lines', summary['lines'])
    line_rows = [dict(line, id=int(lid), wkt=wkt[lid]) for lid, line in summary['lines'].items() if lid in wkt]
    line_fields = [('id', 'integer'), ('mdot', 'double'), ('mdot_max', 'double'), ('dp_spez', 'double'), ('pipe', 'string'),
        ('pipe_new', 'string'), ('changed', 'boolean')]
    lines = createLayer(tr_msg('Lines – design mass flow [kg/s]'), 'LineString', srid(cur, config, 'lines'), line_fields, line_rows, iteration)
    lines.setRenderer(lineRenderer(mdot_bounds))

    changed_rows = [row for row in line_rows if row['changed']]
    changed = createLayer(tr_msg('Lines – new pipes'), 'LineString', srid(cur, config, 'lines'), line_fields, changed_rows, iteration)
    changed.setRenderer(QgsSingleSymbolRenderer(lineSymbol('#e31a1c', 3.0, opacity=0.4)))
    setLabels(changed, "\"pipe\" || ' → ' || \"pipe_new\"", '#b30000')

    group = sizingGroup(iteration)
    group.setItemVisibilityChecked(visible)
    for layer in (customers, changed, lines):
        layer.triggerRepaint()
    return [customers, changed, lines]


def showIterations(cur, config, iterations):
    """Shows the given iteration numbers; only the last one is visible (switch in the layer tree to compare)."""
    summaries = loadIterations(config)
    selected = [s for s in summaries if s['iteration'] in iterations]
    layers = []
    for i, summary in enumerate(selected):
        layers += showIteration(cur, config, summary, summaries, visible=i == len(selected) - 1)
    return layers
