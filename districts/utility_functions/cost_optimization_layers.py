# coding=utf-8
"""Map layers of the cost optimization iterations (as the iterations of the hydraulic balancing): per iteration a
group with the inner diameters of the simulated pipes, the lines changed for it (larger/smaller, 'before → after')
and the customers with a new deficit (penalty). The diameter categories are those of all shown iterations."""
import glob
import json
import os
import re

from qgis.core import (
    QgsCategorizedSymbolRenderer, QgsFeature, QgsGeometry, QgsProject, QgsRendererCategory, QgsSingleSymbolRenderer, QgsVectorLayer,
)

from .dynamic_sizing_results import diameterRenderer, lineSymbol, mm, pointSymbol, setLabels
from .hydraulic_balancing import getPipeBundles, getPipeCatalog
from .translations import tr_msg

ITER_PREFIX = 'cost_optimization_iter'
COST_PROPERTY = 'districts_cost_optimization'


def iterationPath(config, k):
    return os.path.join(config['pathProjects'] + config['projectName'], 'versions', config['versionName'], '{}{}.json'.format(ITER_PREFIX, k))


def loadCostIterations(config):
    """the saved iteration rows of the version, ascending"""
    rows = []
    for path in glob.glob(iterationPath(config, '*')):
        if re.search(r'{}\d+\.json$'.format(ITER_PREFIX), path):
            with open(path, encoding='utf-8') as f:
                rows.append(json.load(f))
    return sorted(rows, key=lambda row: row['iteration'])


def groupName():
    return tr_msg('Cost optimization')


def costGroup(iteration):
    root = QgsProject.instance().layerTreeRoot()
    group = root.findGroup(groupName()) or root.insertGroup(0, groupName())
    name = tr_msg('Iteration {}').format(iteration)
    sub = group.findGroup(name)
    if sub is None:
        index = len([c for c in group.children() if int(re.sub(r'\D', '', c.name()) or 0) < iteration])
        sub = group.insertGroup(index, name)
    return sub


def removeCostLayers(iteration=None):
    root = QgsProject.instance().layerTreeRoot()
    group = root.findGroup(groupName())
    if group is None:
        return
    subs = [group.findGroup(tr_msg('Iteration {}').format(iteration))] if iteration is not None else [group]
    for sub in [s for s in subs if s is not None]:
        for node in sub.findLayers():
            QgsProject.instance().removeMapLayer(node.layerId())
        (group if sub is not group else root).removeChildNode(sub)


def _layer(name, geom, srid, fields, rows, iteration):
    uri = '{}?crs=EPSG:{}&{}'.format(geom, srid, '&'.join('field={}:{}'.format(n, t) for n, t in fields))
    layer = QgsVectorLayer(uri, name, 'memory')
    features = []
    for row in rows:
        feature = QgsFeature(layer.fields())
        feature.setGeometry(QgsGeometry.fromWkt(row['wkt']))
        feature.setAttributes([row.get(n) for n, _ in fields])
        features.append(feature)
    layer.dataProvider().addFeatures(features)
    layer.updateExtents()
    layer.setCustomProperty(COST_PROPERTY, iteration)
    QgsProject.instance().addMapLayer(layer, False)
    costGroup(iteration).addLayer(layer)
    return layer


def _diameters(state, bundles, catalog):
    """{lid: (d [mm], pipe name)} of the first pipe of each line's bundle"""
    result = {}
    for lid, bid in state.items():
        pipes = bundles.get(bid) or {}
        if pipes:
            pid = pipes[min(pipes)]
            if pid in catalog:
                result[int(lid)] = (mm(catalog[pid]['d']), catalog[pid]['name'])
    return result


def _geometries(cur, schema, table, ids):
    cur.execute('SELECT id, ST_AsText(geom) AS wkt, ST_SRID(geom) AS srid FROM "{}"."{}" WHERE id = ANY(%s);'.format(schema, table),  # nosec B608
                ([int(i) for i in ids],))
    rows = cur.fetchall()
    return {row['id']: row['wkt'] for row in rows}, (rows[0]['srid'] if rows else None)


def showCostIterations(cur, config, selected, rows):
    """layers of the selected iterations; rows = all iteration rows (diameter categories, the step into an iteration
    is saved with the iteration before it). Only the last selected iteration is visible."""
    schema = config['versionName']
    bundles, catalog = getPipeBundles(cur), getPipeCatalog(cur)
    by_iteration = {row['iteration']: row for row in rows}
    diameters = {row['iteration']: _diameters(row.get('state') or {}, bundles, catalog) for row in rows}
    all_d = sorted({d for values in diameters.values() for d, _ in values.values()})
    layers = []
    for k in sorted(selected):
        row = by_iteration.get(k)
        if row is None:
            continue
        removeCostLayers(k)
        current = diameters[k]
        wkt, srid = _geometries(cur, schema, 'lines', current)
        if srid is None:
            continue
        line_fields = [('id', 'integer'), ('pipe', 'string'), ('d_new', 'double'), ('pipe_before', 'string'), ('change', 'string')]
        steps = (by_iteration.get(k - 1) or {}).get('steps') or []
        changes = {}
        for step in steps:
            before = step['before'][min(step['before'])] if step.get('before') else None
            changes[int(step['line'])] = ('larger' if step.get('larger') else 'smaller', catalog.get(int(before), {}).get('name', '') if before else '')
        line_rows = [{'id': lid, 'pipe': name, 'd_new': d, 'pipe_before': changes.get(lid, ('', ''))[1], 'change': changes.get(lid, ('', ''))[0],
                      'wkt': wkt[lid]} for lid, (d, name) in current.items() if lid in wkt]
        group_layers = []
        # top to bottom: customers with a deficit, diameters, changed lines as a halo below them
        penalty = row.get('penalty_customers') or []
        if penalty:
            cwkt, csrid = _geometries(cur, schema, 'customers', penalty)
            customers = _layer(tr_msg('Customers – new deficit (penalty)'), 'Point', csrid, [('id', 'integer')],
                               [{'id': cid, 'wkt': w} for cid, w in cwkt.items()], k)
            customers.setRenderer(QgsSingleSymbolRenderer(pointSymbol('#d7301f', 3.0)))
            setLabels(customers, '"id"', '#b30000')
            group_layers.append(customers)
        layer = _layer(tr_msg('Lines – inner diameter [mm]'), 'LineString', srid, line_fields, line_rows, k)
        layer.setRenderer(diameterRenderer(all_d))
        group_layers.append(layer)
        changed_rows = [r for r in line_rows if r['change']]
        if changed_rows:
            changed = _layer(tr_msg('Lines – changed for this iteration'), 'LineString', srid, line_fields, changed_rows, k)
            categories = [QgsRendererCategory('larger', lineSymbol('#1a9850', 3.0, opacity=0.45), tr_msg('larger')),
                          QgsRendererCategory('smaller', lineSymbol('#d73027', 3.0, opacity=0.45), tr_msg('smaller'))]
            changed.setRenderer(QgsCategorizedSymbolRenderer('change', categories))
            setLabels(changed, "\"pipe_before\" || ' → ' || \"pipe\"", '#404040')
            group_layers.append(changed)
        for item in group_layers:
            item.triggerRepaint()
        layers += group_layers
    # only the last selected iteration visible (switch in the layer tree to compare)
    group = QgsProject.instance().layerTreeRoot().findGroup(groupName())
    if group is not None and selected:
        last = tr_msg('Iteration {}').format(max(selected))
        for child in group.children():
            child.setItemVisibilityChecked(child.name() == last)
    return layers
