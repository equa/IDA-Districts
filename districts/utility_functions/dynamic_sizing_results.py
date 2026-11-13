"""Results of the iterations of the dynamic pipe sizing (dynamic_pipe_sizing.py).

Every iteration is saved as dynamic_sizing_iter<n>.json in the version folder, with the results of every
supply/return pair (circuit, see pipe_pairs.py):
    {'iteration', 'started', 'outcome', 'n_changed',
     'pairs': [{'supply', 'return', 'temps', 'time', 'cid_weak', 'epid_weak', 'dp_net_weak', 'cid_target', 'dp_target',
                'quota', 'spread_sized', 'n_presized', 'n_balancing_steps', 'n_changed', 'n_customers_skipped',
                'customers': {cid: {'dp', 'dp_sized', 'dp_net', 'epid', 'time'}},
                'lines': {lid: {'mdot', 'mdot_max', 'dp_spez', 'pipe', 'pipe_new', 'd', 'd_new', 'changed'}}}]}
    temps        ... design temperatures of supply and return (fallback for lines without a temperature result) [degC]
    pipe, pipe_new ... pipe of the supply sequence before / after the sizing
    d, d_new     ... its inner diameter before / after the sizing [mm] (missing in files of earlier runs)
Files of earlier runs have the results of the pair 1/2 at the top level instead of 'pairs' (see loadIterations).
    dp, dp_sized ... differential pressure at the substation simulated / estimated after the sizing [Pa]
    dp_net       ... network pressure loss to the supplying plant [Pa] (the weak point has the largest one)
    mdot         ... design mass flow of the line (sum of the customer mass flows of the flow tracing) [kg/s]
    mdot_max     ... peak mass flow of the line over the whole simulation period [kg/s]
They are shown on the map as memory layers in the group 'dynamic pipe sizing' (one subgroup per iteration and in it
one per pair), top to bottom: customers with graduated colors of dp (weak point as bigger point), lines categorized
by the inner diameter after the sizing, lines with new pipes (labelled), lines with graduated colors and widths of
the design mass flow (switched off). The classes and categories of a pair are the same for all iterations.
"""
import glob
import json
import os
import re

from qgis.core import (
    Qgis, QgsCategorizedSymbolRenderer, QgsFeature, QgsGeometry, QgsLayerTree, QgsPalLayerSettings, QgsProject, QgsRendererCategory,
    QgsRuleBasedRenderer, QgsStyle, QgsSymbol, QgsProperty, QgsSingleSymbolRenderer, QgsTextFormat, QgsVectorLayer,
    QgsVectorLayerSimpleLabeling,
)
from qgis.PyQt.QtCore import Qt
from qgis.PyQt.QtGui import QColor

from .pipe_pairs import pairLabel
from .translations import tr_msg

SIZING_PROPERTY = 'districts_dynamic_pipe_sizing'
PAIR_PROPERTY = 'districts_dynamic_pipe_sizing_pair'
ITERATION_FILE = 'dynamic_sizing_iter{}.json'
OUTCOMES = ('changed', 'converged', 'oscillation', 'max_iter')
N_CLASSES = 7


# ---------------------------------------------------------------- files
def versionPath(config):
    return os.path.join(config['pathProjects'], config['projectName'], 'versions', config['versionName'])


def mm(d):
    """inner diameter [m] -> [mm], rounded to 0.1 mm"""
    return round(d * 1000, 1)


def pairSummary(pair, temps, res, opt, changed, n_skipped=0, reference=False, target_no_flow=False):
    """Results of a pair in an iteration (see the module doc) from getCustomerLinePressure (res) and
    optimizePipeDiameters (opt); pair = (supply, return), changed = lines whose pipes of the pair changed.
    reference: reference run (iteration 0), the pipes are not changed (pipe_new = pipe)."""
    catalog, lines = res['catalog'], res['lines']
    supply = pair[0]
    customers = {}
    for cid, (dp, _) in res['c_lid'].items():
        dp_net, epid = res['dvar'].get(cid, (None, None))
        customers[str(cid)] = {'dp': dp, 'dp_sized': opt['c_lid'].get(cid, [None])[0], 'dp_net': dp_net, 'epid': epid,
            'time': str(res['times'].get(cid, ''))}
    line_rows = {}
    for lid, line in lines.items():
        pipe = line['pipes'][supply]
        new = pipe['pipe_id'] if reference else opt['pipes'].get(lid, {}).get(supply, pipe['pipe_id'])
        line_rows[str(lid)] = {'mdot': abs(pipe['mdot']), 'mdot_max': max(abs(p.get('mdot_max', 0.0)) for p in line['pipes'].values()),
            'dp_spez': res['dp_spez'].get(lid), 'pipe': catalog[pipe['pipe_id']]['name'], 'pipe_new': catalog[new]['name'],
            'd': mm(catalog[pipe['pipe_id']]['d']), 'd_new': mm(catalog[new]['d']), 'changed': lid in changed and not reference}
    return {'supply': pair[0], 'return': pair[1], 'temps': list(temps), 'time': str(res['time']), 'cid_weak': res['cid_dp'],
        'epid_weak': res['epid_dp'], 'dp_net_weak': res['dp'], 'cid_target': opt['cid_weak'], 'dp_target': opt['dp_target'],
        'quota': opt['quota'], 'spread_sized': opt['spread'], 'n_presized': len(opt['presize']), 'n_balancing_steps': len(opt['history']),
        'n_changed': 0 if reference else len(changed), 'n_customers_skipped': n_skipped, 'target_no_flow': target_no_flow,
        'customers': customers, 'lines': line_rows}


def iterationSummary(iteration, started, pairs, outcome, n_changed):
    """Summary of an iteration (see the module doc); pairs = [pairSummary], n_changed = lines with a new pipe bundle."""
    return {'iteration': iteration, 'started': started, 'outcome': outcome, 'n_changed': n_changed, 'pairs': pairs}


ITERATION_KEYS = ('iteration', 'started', 'outcome', 'n_changed')


def normalizedSummary(summary):
    """A file of an earlier run (results of the pair 1/2 at the top level) as a summary with 'pairs'."""
    if 'pairs' in summary:
        return summary
    pair = {k: v for k, v in summary.items() if k not in ITERATION_KEYS}
    pair.update({'supply': 1, 'return': 2, 'temps': [None, None], 'n_changed': summary.get('n_changed', 0), 'n_customers_skipped': 0})
    return dict({k: summary[k] for k in ITERATION_KEYS if k in summary}, pairs=[pair])


def saveIteration(config, summary):
    with open(os.path.join(versionPath(config), ITERATION_FILE.format(summary['iteration'])), 'w', encoding='utf-8') as f:
        json.dump(summary, f, indent=1)


def loadIterations(config):
    """Returns the saved iterations of the loaded version sorted by their number (with 'pairs', see normalizedSummary)."""
    result = []
    for path in glob.glob(os.path.join(versionPath(config), ITERATION_FILE.format('*'))):
        if re.fullmatch(ITERATION_FILE.format(r'\d+'), os.path.basename(path)):
            with open(path, encoding='utf-8') as f:
                result.append(normalizedSummary(json.load(f)))
    return sorted(result, key=lambda s: s['iteration'])


def deleteIterations(config, keep_reference=False):
    """Removes the iteration files of a previous run (also the ones copied from the parent version); with
    keep_reference the files of the reference run (iteration 0) are kept."""
    for pattern in (ITERATION_FILE.format('*'), 'dynamic_sizing_iter*_c_lid*.json'):
        for path in glob.glob(os.path.join(versionPath(config), pattern)):
            if not (keep_reference and re.match(r'dynamic_sizing_iter0[._]', os.path.basename(path))):
                os.remove(path)


def iterationRows(summary):
    """Rows of the iteration table, one per pair: (iteration, pair, critical time, weak point, dp min, dp max, spread,
    spread sized, quota, changed lines of the pair, outcome); pressures in bar."""
    rows = []
    for pair in summary['pairs']:
        dps = [c['dp'] for c in pair['customers'].values() if c['dp'] is not None]
        rows.append((summary['iteration'], pairLabel((pair['supply'], pair['return'])), pair['time'],
            '{} ({})'.format(pair['cid_weak'], pair['epid_weak']), bar(min(dps)) if dps else None, bar(max(dps)) if dps else None,
            bar(max(dps) - min(dps)) if dps else None, bar(pair['spread_sized']), round(100 * pair['quota']), pair['n_changed'],
            outcomeText(summary['outcome'])))
    return rows


def bar(value):
    return round(value / 1e5, 4) if value is not None else None


def outcomeText(outcome):
    return {'changed': tr_msg('pipes changed'), 'converged': tr_msg('converged'), 'oscillation': tr_msg('oscillation'),
        'max_iter': tr_msg('pipes changed, max. iterations'), 'reference': tr_msg('reference')}.get(outcome, outcome)


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
        removeEmptyGroups(group)
        if not group.children():
            group.parent().removeChildNode(group)


def removeEmptyGroups(group):
    for child in list(group.children()):
        if QgsLayerTree.isGroup(child):
            removeEmptyGroups(child)
            if not child.children():
                group.removeChildNode(child)


def sizingGroup(iteration, label=None):
    """Subgroup of the iteration, or with label (pair 's/r') its subgroup of the pair."""
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
    if label is None:
        return sub
    name = tr_msg('Pair {}').format(label)
    return sub.findGroup(name) or sub.addGroup(name)


def createLayer(name, geom_type, srid, fields, rows, iteration, label):
    uri = "{}?crs=EPSG:{}&{}".format(geom_type, srid, '&'.join('field={}:{}'.format(n, t) for n, t in fields))
    layer = QgsVectorLayer(uri, name, 'memory')
    features = []
    for row in rows:
        f = QgsFeature(layer.fields())
        f.setGeometry(QgsGeometry.fromWkt(row['wkt']))
        f.setAttributes([row.get(n) for n, _ in fields])
        features.append(f)
    layer.dataProvider().addFeatures(features)
    layer.updateExtents()
    layer.setCustomProperty(SIZING_PROPERTY, iteration)
    layer.setCustomProperty(PAIR_PROPERTY, label)
    QgsProject.instance().addMapLayer(layer, False)
    sizingGroup(iteration, label).addLayer(layer)
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


def diameterRenderer(diameters, width=1.2):
    """one category per inner diameter [mm] of d_new (colors as in the pipe diameter style of the lines layer);
    grey for lines without a diameter (files of earlier runs)"""
    from .layer_visualization import diameterColors, diameterLabel
    categories = [QgsRendererCategory(d, lineSymbol(color, width), diameterLabel(d))
        for d, color in diameterColors([d for d in diameters if d is not None]).items()]
    categories.append(QgsRendererCategory('', lineSymbol('#bdbdbd', 0.6), tr_msg('no diameter')))
    return QgsCategorizedSymbolRenderer('d_new', categories)


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


def showIteration(cur, config, summary, all_summaries=None, visible=True, labels=None):
    """Memory layers of an iteration, per pair (customers: dp at the substation, lines: design mass flow, changed pipes).
    The class bounds of a pair are taken from the same pair in all_summaries (default: this one), so the iterations can
    be compared. labels: the pairs ('s/r') to show, None -> all. Returns the created layers."""
    iteration = summary['iteration']
    removeSizingLayers(iteration)
    all_summaries = all_summaries or [summary]
    layers = []
    for pair in summary['pairs']:
        label = pairLabel((pair['supply'], pair['return']))
        if labels is None or label in labels:
            same = [p for s in all_summaries for p in s['pairs'] if pairLabel((p['supply'], p['return'])) == label]
            layers += showPair(cur, config, iteration, label, pair, same, new_pipes=summary['outcome'] != 'reference')
    sizingGroup(iteration).setItemVisibilityChecked(visible)
    return layers


def showPair(cur, config, iteration, label, pair, all_pairs, new_pipes=True):
    """Layers of a pair of an iteration (top to bottom: customers, diameters, new pipes, mass flow); classes and
    diameter categories from all_pairs (the same pair in all iterations).
    new_pipes=False: without the layer of the lines with new pipes (reference run)."""
    dp_bounds = classBounds([bar(c['dp']) for p in all_pairs for c in p['customers'].values()])
    mdot_bounds = classBounds([line['mdot'] for p in all_pairs for line in p['lines'].values() if line['mdot'] > 0])

    # the layers are added in their order in the layer tree, top to bottom
    wkt = geometries(cur, config, 'customers', pair['customers'])
    customer_rows = [{'id': int(cid), 'dp_bar': bar(c['dp']), 'dp_sized_bar': bar(c['dp_sized']), 'dp_net_bar': bar(c['dp_net']),
        'epid': c['epid'], 'time': c['time'], 'weak': str(pair['cid_weak']) == cid, 'wkt': wkt[cid]}
        for cid, c in pair['customers'].items() if cid in wkt]
    customer_fields = [('id', 'integer'), ('dp_bar', 'double'), ('dp_sized_bar', 'double'), ('dp_net_bar', 'double'), ('epid', 'integer'),
        ('time', 'string'), ('weak', 'boolean')]
    customers = createLayer(tr_msg('Customers – dp substation [bar]'), 'Point', srid(cur, config, 'customers'), customer_fields, customer_rows, iteration, label)
    customers.setRenderer(customerRenderer(dp_bounds))
    setLabels(customers, "if(\"weak\", '{} ' || \"id\" || ': ' || format_number(\"dp_bar\", 3) || ' bar', '')".format(tr_msg('weak point')))

    # created top to bottom: diameters, the changed lines as a halo below them, the mass flow (switched off)
    wkt = geometries(cur, config, 'lines', pair['lines'])
    line_rows = [dict(line, id=int(lid), wkt=wkt[lid]) for lid, line in pair['lines'].items() if lid in wkt]
    line_fields = [('id', 'integer'), ('mdot', 'double'), ('mdot_max', 'double'), ('dp_spez', 'double'), ('pipe', 'string'),
        ('pipe_new', 'string'), ('d', 'double'), ('d_new', 'double'), ('changed', 'boolean')]
    line_srid = srid(cur, config, 'lines')
    name = tr_msg('Lines – inner diameter after sizing [mm]') if new_pipes else tr_msg('Lines – inner diameter [mm]')
    diameters = createLayer(name, 'LineString', line_srid, line_fields, line_rows, iteration, label)
    diameters.setRenderer(diameterRenderer([line.get(k) for p in all_pairs for line in p['lines'].values() for k in ('d', 'd_new')]))
    layers = [customers, diameters]
    if new_pipes:
        changed_rows = [row for row in line_rows if row['changed']]
        changed = createLayer(tr_msg('Lines – new pipes'), 'LineString', line_srid, line_fields, changed_rows, iteration, label)
        changed.setRenderer(QgsSingleSymbolRenderer(lineSymbol('#e31a1c', 3.0, opacity=0.4)))
        setLabels(changed, "\"pipe\" || ' → ' || \"pipe_new\"", '#b30000')
        layers.append(changed)
    lines = createLayer(tr_msg('Lines – design mass flow [kg/s]'), 'LineString', line_srid, line_fields, line_rows, iteration, label)
    lines.setRenderer(lineRenderer(mdot_bounds))
    sizingGroup(iteration, label).findLayer(lines.id()).setItemVisibilityChecked(False)
    layers.append(lines)
    for layer in layers:
        layer.triggerRepaint()
    return layers


def showIterations(cur, config, selection):
    """Shows the selected iterations: selection = [(iteration, pair label 's/r' or None for all pairs)]. Only the last
    iteration is visible (switch in the layer tree to compare)."""
    wanted: dict = {}
    for iteration, label in selection:
        if label is None:
            wanted[iteration] = None
        elif wanted.get(iteration, set()) is not None:
            wanted.setdefault(iteration, set()).add(label)
    summaries = loadIterations(config)
    selected = [s for s in summaries if s['iteration'] in wanted]
    layers = []
    for i, summary in enumerate(selected):
        layers += showIteration(cur, config, summary, summaries, visible=i == len(selected) - 1, labels=wanted[summary['iteration']])
    return layers
