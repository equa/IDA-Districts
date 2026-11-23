# coding=utf-8
"""Map layers of the cost optimization iterations (as the iterations of the hydraulic balancing): per iteration a
group with the inner diameters of the simulated pipes, the lines changed for it (larger/smaller, 'before → after')
and the customers with a new deficit (penalty). The diameter categories are those of all shown iterations."""
import glob
import json
import os
import re

from qgis.core import (
    QgsCategorizedSymbolRenderer, QgsFeature, QgsGeometry, QgsLayerTreeRegistryBridge, QgsProject, QgsRendererCategory, QgsSingleSymbolRenderer,
    QgsVectorLayer,
)
from qgis.utils import iface

from .dynamic_sizing_results import diameterRenderer, lineSymbol, mm, pointSymbol, setLabels
from .hydraulic_balancing import getPipeBundles, getPipeCatalog
from .network_stages import stageRoots
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


def costGroup(iteration, stage=None):
    root = QgsProject.instance().layerTreeRoot()
    group = root.findGroup(groupName()) or root.insertGroup(0, groupName())
    name = tr_msg('Iteration {}').format(iteration)
    sub = group.findGroup(name)
    if sub is None:
        index = len([c for c in group.children() if int(re.sub(r'\D', '', c.name()) or 0) < iteration])
        sub = group.insertGroup(index, name)
    if stage is None:
        return sub
    return sub.findGroup(stage) or sub.addGroup(stage)


def layerInsertionAtTop():
    """new layers at the top of the layer tree: QGIS inserts them next to the current layer of the layer panel, so
    after an iteration layer the layers of a loaded version would land in that iteration's group"""
    view = iface.layerTreeView() if iface else None
    if view is not None and hasattr(view, 'setCurrentLayer'):
        view.setCurrentLayer(None)
    bridge = QgsProject.instance().layerTreeRegistryBridge()
    if bridge is not None:
        bridge.setLayerInsertionPoint(QgsLayerTreeRegistryBridge.InsertionPoint(QgsProject.instance().layerTreeRoot(), 0))


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


def _layer(name, geom, srid, fields, rows, iteration, collect=None, stage=None):
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
    if collect is not None:
        collect.append(layer)
        return layer
    QgsProject.instance().addMapLayer(layer, False)
    costGroup(iteration, stage).addLayer(layer)
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


def rowStates(row):
    """{version: {lid: bundle}} of an iteration row: one per stage of a run over stages (network-stages), else
    {None: state}"""
    return row.get('stage_states') or {None: row.get('state') or {}}


def iterationDiameters(cur, rows):
    """catalog, {(iteration, version): {lid: (d [mm], pipe name)}} (version None without stages) and all diameters of
    the iteration rows"""
    bundles, catalog = getPipeBundles(cur), getPipeCatalog(cur)
    diameters = {(row['iteration'], version): _diameters(state, bundles, catalog) for row in rows for version, state in rowStates(row).items()}
    all_d = sorted({d for values in diameters.values() for d, _ in values.values()})
    return catalog, diameters, all_d


def stageViews(cur, schema, row, cache=None):
    """[(stage version or None, schema, {lid: root} or None, customers with a new deficit)] of an iteration row, one per
    stage of a run over stages; a stage version that no longer exists is left out. cache: {versions: roots}, the
    matching of the lines is the same in every iteration of a run."""
    states = row.get('stage_states')
    if not states:
        return [(None, schema, None, row.get('penalty_customers') or [])]
    versions = list(states)
    cur.execute('SELECT nspname FROM pg_namespace WHERE nspname = ANY(%s);', (versions,))
    existing = {r['nspname'] for r in cur.fetchall()}
    roots: list = [{}] * len(versions)
    if existing == set(versions):
        key = tuple(versions)
        if cache is None:
            cache = {}
        if key not in cache:
            cache[key] = stageRoots(cur, versions)
        roots = cache[key]
    per_stage = row.get('stage_penalty')
    views = []
    for j, version in enumerate(versions):
        if version not in existing:
            continue
        if per_stage is not None:
            penalty = per_stage.get(version) or []
        else:
            # iteration files from before the deficits were kept per stage: all of them in the last stage
            penalty = (row.get('penalty_customers') or []) if j == len(versions) - 1 else []
        views.append((version, version, roots[j], penalty))
    return views


def iterationLayers(cur, schema, k, rows, catalog, diameters, all_d, collect=None, view=None):
    """layers of iteration k, top to bottom: customers with a deficit, diameters, changed lines as a halo below them.
    collect: a list that takes the layers instead of the project (report). view: one of stageViews (a stage of a run
    over stages), else the loaded version."""
    by_iteration = {row['iteration']: row for row in rows}
    row = by_iteration.get(k)
    if row is None:
        return []
    version, schema, roots, penalty = view or (None, schema, None, row.get('penalty_customers') or [])
    current = diameters.get((k, version)) or {}
    wkt, srid = _geometries(cur, schema, 'lines', current)
    if srid is None:
        return []
    line_fields = [('id', 'integer'), ('pipe', 'string'), ('d_new', 'double'), ('pipe_before', 'string'), ('change', 'string')]
    # the step into an iteration is saved with the iteration before it
    steps = (by_iteration.get(k - 1) or {}).get('steps') or []
    # a step of a run over stages names the root (stage, line) of a line group: the change is on every segment of it
    lines_of: dict = {}
    for lid, root in (roots or {}).items():
        lines_of.setdefault(root, []).append(lid)
    changes = {}
    for step in steps:
        before = step['before'][min(step['before'])] if step.get('before') else None
        change = ('larger' if step.get('larger') else 'smaller', catalog.get(int(before), {}).get('name', '') if before else '')
        targets = lines_of.get((int(step.get('stage') or 1) - 1, int(step['line'])), []) if roots is not None else [int(step['line'])]
        for lid in targets:
            changes[lid] = change
    line_rows = [{'id': lid, 'pipe': name, 'd_new': d, 'pipe_before': changes.get(lid, ('', ''))[1], 'change': changes.get(lid, ('', ''))[0],
                  'wkt': wkt[lid]} for lid, (d, name) in current.items() if lid in wkt]
    group_layers = []
    if penalty:
        cwkt, csrid = _geometries(cur, schema, 'customers', penalty)
        customers = _layer(tr_msg('Customers – new deficit (penalty)'), 'Point', csrid, [('id', 'integer')],
                           [{'id': cid, 'wkt': w} for cid, w in cwkt.items()], k, collect, version)
        customers.setRenderer(QgsSingleSymbolRenderer(pointSymbol('#d7301f', 3.0)))
        setLabels(customers, '"id"', '#b30000')
        group_layers.append(customers)
    layer = _layer(tr_msg('Lines – inner diameter [mm]'), 'LineString', srid, line_fields, line_rows, k, collect, version)
    layer.setRenderer(diameterRenderer(all_d))
    group_layers.append(layer)
    changed_rows = [r for r in line_rows if r['change']]
    if changed_rows:
        changed = _layer(tr_msg('Lines – changed for this iteration'), 'LineString', srid, line_fields, changed_rows, k, collect, version)
        categories = [QgsRendererCategory('larger', lineSymbol('#1a9850', 3.0, opacity=0.45), tr_msg('larger')),
                      QgsRendererCategory('smaller', lineSymbol('#d73027', 3.0, opacity=0.45), tr_msg('smaller'))]
        changed.setRenderer(QgsCategorizedSymbolRenderer('change', categories))
        setLabels(changed, "\"pipe_before\" || ' → ' || \"pipe\"", '#404040')
        group_layers.append(changed)
    return group_layers


def showCostIterations(cur, config, selected, rows):
    """layers of the selected iterations; rows = all iteration rows (diameter categories). Only the last selected
    iteration is visible (switch in the layer tree to compare)."""
    catalog, diameters, all_d = iterationDiameters(cur, rows)
    by_iteration = {row['iteration']: row for row in rows}
    layers: list = []
    cache: dict = {}
    for k in sorted(selected):
        removeCostLayers(k)
        if k not in by_iteration:
            continue
        views = stageViews(cur, config['versionName'], by_iteration[k], cache)
        for view in views:
            group_layers = iterationLayers(cur, config['versionName'], k, rows, catalog, diameters, all_d, view=view)
            for item in group_layers:
                item.triggerRepaint()
            layers += group_layers
        if views and views[0][0] is not None:
            # the stages lie on top of each other: the last one (the whole network) is shown, the others to switch on
            for child in costGroup(k).children():
                child.setItemVisibilityChecked(child.name() == views[-1][0])
    group = QgsProject.instance().layerTreeRoot().findGroup(groupName())
    if group is not None and selected:
        last = tr_msg('Iteration {}').format(max(selected))
        for child in group.children():
            child.setItemVisibilityChecked(child.name() == last)
    layerInsertionAtTop()
    return layers
