# coding=utf-8
"""Tool registry of the AI connection (D3, D5). Every tool only reads: it gets a cursor whose transaction is rolled
back (ToolContext.cursor), so no tool can change the project database, even through a helper that writes a temp table."""
import base64
import contextlib
import copy
import datetime
import decimal
import os
import re

import psycopg2.extras
from qgis.core import (
    QgsFeatureRequest, QgsMapRendererParallelJob, QgsMapSettings, QgsProject, QgsRasterLayer, QgsRectangle, QgsVectorLayer, QgsWkbTypes,
)
from qgis.PyQt.QtCore import QBuffer, QByteArray, QIODevice, QSize, QThreadPool

from ..utility_functions.db import dbConnect

MAX_FEATURES = 1000
MAX_SERIES_ROWS = 5000
TOOLS = []


class ToolError(Exception):
    """an error the AI can act on (no traceback)"""


def tool(name, description, properties=None, required=None):
    def register(handler):
        TOOLS.append({'name': name, 'description': description, 'handler': handler,
                      'input_schema': {'type': 'object', 'properties': properties or {}, 'required': required or []}})
        return handler
    return register


VERSION = {'version': {'type': 'string', 'description': 'version name (default: the loaded version)'}}


class ToolContext:
    """access of the tools to the plugin: its settings (never the credentials) and read-only cursors"""

    def __init__(self, plugin):
        self.plugin = plugin

    def config(self, version=None):
        config = copy.deepcopy(self.plugin.config)
        if not config.get('projectName'):
            raise ToolError('no project selected in the Districts Modeler')
        if version:
            config['versionName'] = version
        if not config.get('versionName'):
            raise ToolError('no version loaded; pass a version name or load a version in the Districts Modeler')
        return config

    @contextlib.contextmanager
    def cursor(self, config):
        conn = dbConnect(config, False)
        if not conn:
            raise ToolError('no connection to the project database {}'.format(config.get('projectName')))
        try:
            conn.autocommit = False
            cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
            if config.get('versionName'):
                cur.execute('SELECT 1 FROM public.versionhandling WHERE name = %s;', (config['versionName'],))
                if not cur.fetchone():
                    raise ToolError('version {} does not exist in project {}'.format(config['versionName'], config['projectName']))
            yield cur
        finally:
            conn.rollback()
            conn.close()

    def jobRunning(self):
        return bool(getattr(self.plugin, 'process_running', False)) or QThreadPool.globalInstance().activeThreadCount() > 0


def listTools():
    return [{'name': t['name'], 'description': t['description'], 'inputSchema': t['input_schema']} for t in TOOLS]


def callTool(ctx, name, args):
    for t in TOOLS:
        if t['name'] == name:
            return t['handler'](ctx, args or {})
    raise ToolError('unknown tool {}'.format(name))


# ---------------- state ----------------
@tool('project_state', 'State of the Districts Modeler: project, versions, loaded version, templates, networks, feature counts '
      'and whether a job (simulation, sizing, optimization) is running.', VERSION)
def projectState(ctx, args):
    from ..network_pumps_dialog import projectTemplates
    base = ctx.plugin.config
    if not base.get('projectName'):
        raise ToolError('no project selected in the Districts Modeler')
    config = ctx.config(args.get('version')) if (args.get('version') or base.get('versionName')) else None
    out = {'project': base['projectName'], 'loaded_version': base.get('versionName') or None, 'job_running': ctx.jobRunning()}
    with ctx.cursor(dict(copy.deepcopy(base), versionName='')) as cur:
        cur.execute('SELECT id, id_base, name, description FROM public.versionhandling ORDER BY id;')
        out['versions'] = [{'id': r['id'], 'parent_id': r['id_base'], 'name': r['name'], 'description': r['description']} for r in cur.fetchall()]
        out['templates'] = projectTemplates(cur)
    if config:
        with ctx.cursor(config) as cur:
            counts = {}
            for table in ('customers', 'energy_plants', 'lines', 'junctions', 'buildings', 'streets'):
                cur.execute('SELECT to_regclass(%s) IS NOT NULL AS ok;', ('"{}"."{}"'.format(config['versionName'], table),))
                if cur.fetchone()['ok']:
                    cur.execute('SELECT count(*) AS n FROM "{}"."{}";'.format(config['versionName'], table))  # nosec B608
                    counts[table] = cur.fetchone()['n']
            out['version'] = config['versionName']
            out['feature_counts'] = counts
            if counts.get('lines'):
                cur.execute('SELECT DISTINCT network FROM "{}".lines ORDER BY network;'.format(config['versionName']))  # nosec B608
                out['networks'] = [r['network'] for r in cur.fetchall()]
    return out


@tool('layers', 'Layers of the QGIS project: name, id, type, feature count, visibility, CRS.')
def layers(ctx, args):
    project = QgsProject.instance()
    root = project.layerTreeRoot()
    out = []
    for layer in project.mapLayers().values():
        node = root.findLayer(layer.id())
        entry = {'name': layer.name(), 'id': layer.id(), 'visible': bool(node and node.isVisible()), 'crs': layer.crs().authid(),
                 'provider': layer.providerType()}
        if isinstance(layer, QgsVectorLayer):
            entry.update(type='vector', geometry=QgsWkbTypes.displayString(layer.wkbType()), feature_count=layer.featureCount(),
                         fields=[f.name() for f in layer.fields()])
        else:
            entry['type'] = 'raster' if isinstance(layer, QgsRasterLayer) else type(layer).__name__
        out.append(entry)
    return {'layers': sorted(out, key=lambda e: e['name'])}


def findLayer(name):
    project = QgsProject.instance()
    layer = project.mapLayer(name) or next(iter(project.mapLayersByName(name)), None)
    if not isinstance(layer, QgsVectorLayer):
        raise ToolError('no vector layer {} in the QGIS project (see the tool layers)'.format(name))
    return layer


@tool('features', 'Features of a vector layer: attributes and a geometry summary, optionally filtered with a QGIS expression.',
      {'layer': {'type': 'string', 'description': 'layer name or id'},
       'filter': {'type': 'string', 'description': 'QGIS expression, e.g. "id" IN (3, 7)'},
       'fields': {'type': 'array', 'items': {'type': 'string'}},
       'limit': {'type': 'integer', 'description': 'at most {} (default 100)'.format(MAX_FEATURES)},
       'geometry': {'type': 'boolean', 'description': 'include the geometry as WKT (default false: centroid only)'}}, ['layer'])
def features(ctx, args):
    layer = findLayer(args['layer'])
    limit = max(1, min(int(args.get('limit') or 100), MAX_FEATURES))
    request = QgsFeatureRequest()
    if args.get('filter'):
        request.setFilterExpression(args['filter'])
    names = args.get('fields') or [f.name() for f in layer.fields()]
    unknown = [n for n in names if layer.fields().indexOf(n) < 0]
    if unknown:
        raise ToolError('unknown fields {} of layer {}'.format(', '.join(unknown), layer.name()))
    out, cut = [], False
    for k, feature in enumerate(layer.getFeatures(request)):
        if k >= limit:
            cut = True
            break
        entry = {'fid': feature.id(), 'attributes': {n: jsonValue(feature[n]) for n in names}}
        geom = feature.geometry()
        if geom and not geom.isNull():
            entry['geometry'] = geom.asWkt(2) if args.get('geometry') else {'centroid': geom.centroid().asWkt(2), 'length': round(geom.length(), 2)}
        out.append(entry)
    if request.filterExpression() and request.filterExpression().hasParserError():
        raise ToolError('filter: ' + request.filterExpression().parserErrorString())
    return {'layer': layer.name(), 'features': out, 'cut': cut, 'limit': limit}


def jsonValue(value):
    if value is None or isinstance(value, (bool, int, str)):
        return value
    if isinstance(value, float):
        return round(value, 6)
    if isinstance(value, decimal.Decimal):
        return round(float(value), 6)
    if isinstance(value, (datetime.datetime, datetime.date)):
        return value.isoformat(sep=' ') if isinstance(value, datetime.datetime) else value.isoformat()
    if hasattr(value, 'isNull') and value.isNull():
        return None
    return str(value)


@tool('render_map', 'Image (PNG) of the map with the visible layers, of a layer\'s extent or a given extent.',
      {'layer': {'type': 'string', 'description': 'zoom to this layer (name or id)'},
       'extent': {'type': 'array', 'items': {'type': 'number'}, 'description': '[xmin, ymin, xmax, ymax] in the project CRS'},
       'width': {'type': 'integer'}, 'height': {'type': 'integer'}})
def renderMap(ctx, args):
    project = QgsProject.instance()
    visible = [layer for layer in project.layerTreeRoot().checkedLayers()]
    if not visible:
        raise ToolError('no visible layer in the QGIS project')
    settings = QgsMapSettings()
    settings.setLayers(visible)
    settings.setDestinationCrs(project.crs())
    width, height = min(int(args.get('width') or 800), 2000), min(int(args.get('height') or 600), 2000)
    settings.setOutputSize(QSize(width, height))
    if args.get('extent'):
        settings.setExtent(QgsRectangle(*[float(v) for v in args['extent']]))
    elif args.get('layer'):
        layer = findLayer(args['layer'])
        settings.setExtent(settings.layerExtentToOutputExtent(layer, layer.extent()).buffered(10))
    else:
        canvas = getattr(getattr(ctx.plugin, 'iface', None), 'mapCanvas', lambda: None)()
        settings.setExtent(canvas.extent() if canvas else visible[0].extent())
    job = QgsMapRendererParallelJob(settings)
    job.start()
    job.waitForFinished()
    data = QByteArray()
    buffer = QBuffer(data)
    buffer.open(QIODevice.OpenModeFlag.WriteOnly)
    job.renderedImage().save(buffer, 'PNG')
    return {'image_png_base64': base64.b64encode(bytes(data)).decode('ascii'), 'width': width, 'height': height}


# ---------------- raw data ----------------
@tool('result_tables', 'Result tables of a version (customers, energy plants, lines, KPIs), the simulated time range, the '
      'results basis (full year, representative periods) and whether a job is running (results may be incomplete).', VERSION)
def resultTablesTool(ctx, args):
    from ..utility_functions.version_kpis import resultsBasis
    config = ctx.config(args.get('version'))
    with ctx.cursor(config) as cur:
        cur.execute("""SELECT c.relname AS name, c.reltuples::bigint AS rows FROM pg_class c JOIN pg_namespace n ON n.oid = c.relnamespace
            WHERE n.nspname = %s AND c.relkind = 'r' AND (c.relname LIKE '%%\\_s\\_%%' OR c.relname LIKE 'kpi\\_%%') ORDER BY c.relname;""",
                    (config['versionName'],))
        tables = [{'table': r['name'], 'rows_estimate': max(0, r['rows'])} for r in cur.fetchall()]
        basis = resultsBasis(cur, config)
    out = {'version': config['versionName'], 'tables': tables, 'results_basis': basis, 'job_running': ctx.jobRunning()}
    if out['job_running']:
        out['note'] = 'a job is running: the result tables may be incomplete, figures are provisional'
    return out


AGGREGATIONS = ('summary', 'day', 'raw')


@tool('result_series', 'Values of a result table: per feature min/max/mean (summary), daily min/max/mean (day) or the raw '
      'time steps (raw, limited). Tables: see result_tables.',
      dict(VERSION, table={'type': 'string'}, feature_ids={'type': 'array', 'items': {'type': 'integer'}},
           time_from={'type': 'string', 'description': 'yyyy-mm-dd hh:mm:ss'}, time_to={'type': 'string'},
           aggregation={'type': 'string', 'enum': list(AGGREGATIONS)}, limit={'type': 'integer'}), ['table'])
def resultSeries(ctx, args):
    config = ctx.config(args.get('version'))
    schema = config['versionName']
    aggregation = args.get('aggregation') or 'summary'
    if aggregation not in AGGREGATIONS:
        raise ToolError('aggregation must be one of ' + ', '.join(AGGREGATIONS))
    with ctx.cursor(config) as cur:
        cur.execute("SELECT column_name FROM information_schema.columns WHERE table_schema = %s AND table_name = %s;", (schema, args['table']))
        columns = [r['column_name'] for r in cur.fetchall()]
        if not columns:
            raise ToolError('no table {} in version {} (see result_tables)'.format(args['table'], schema))
        values = [c for c in columns if c.startswith('$')]
        if not values or 'time' not in columns:
            raise ToolError('{} is not a result table with a time column'.format(args['table']))
        keys = [c for c in ('fid', 'component', 'carrier', 'pump') if c in columns]
        where, params = ['true'], []
        if args.get('feature_ids'):
            where.append('fid = ANY(%s)')
            params.append([int(i) for i in args['feature_ids']])
        for key, op in (('time_from', '>='), ('time_to', '<=')):
            if args.get(key):
                where.append('time {} %s'.format(op))
                params.append(args[key])
        table = '"{}"."{}"'.format(schema, args['table'])
        value = '"{}"'.format(values[0])
        group = ', '.join(keys)
        if aggregation == 'summary':
            sql = 'SELECT {g}{c} min({v}) AS min, max({v}) AS max, avg({v}) AS mean, count(*) AS n, min(time) AS t0, max(time) AS t1 FROM {t} WHERE {w}{gb} ORDER BY 1'.format(
                g=group, c=', ' if group else '', v=value, t=table, w=' AND '.join(where), gb=' GROUP BY ' + group if group else '')
        elif aggregation == 'day':
            sql = "SELECT {g}{c} date_trunc('day', time) AS day, min({v}) AS min, max({v}) AS max, avg({v}) AS mean FROM {t} WHERE {w} GROUP BY {g}{c} day ORDER BY {g}{c} day".format(
                g=group, c=', ' if group else '', v=value, t=table, w=' AND '.join(where))
        else:
            # segments of a line are averaged
            sql = 'SELECT {g}{c} time, avg({v}) AS value FROM {t} WHERE {w} GROUP BY {g}{c} time ORDER BY {g}{c} time'.format(
                g=group, c=', ' if group else '', v=value, t=table, w=' AND '.join(where))
        limit = max(1, min(int(args.get('limit') or 1000), MAX_SERIES_ROWS))
        cur.execute(sql + ' LIMIT %s;', params + [limit + 1])  # nosec B608
        rows = [{k: jsonValue(v) for k, v in r.items()} for r in cur.fetchall()]
    return {'table': args['table'], 'column': values[0], 'aggregation': aggregation, 'rows': rows[:limit], 'cut': len(rows) > limit,
            'job_running': ctx.jobRunning()}


@tool('run_log', 'Errors of the IDA runs of a version (result.json) and the end of the newest runner.log.', VERSION)
def runLog(ctx, args):
    from ..utility_functions.model_checks import versionDir
    import json
    config = ctx.config(args.get('version'))
    root = versionDir(config)
    errors, logs = [], []
    for folder, _, files in os.walk(root):
        if 'result.json' in files:
            try:
                with open(os.path.join(folder, 'result.json')) as f:
                    result = json.load(f)
                errors.append({'folder': os.path.relpath(folder, root), 'ok': result.get('ok'), 'errors': result.get('errors') or []})
            except (OSError, ValueError) as e:
                errors.append({'folder': os.path.relpath(folder, root), 'unreadable': str(e)})
        if 'runner.log' in files:
            logs.append(os.path.join(folder, 'runner.log'))
    out = {'version': config['versionName'], 'results': errors}
    if logs:
        newest = max(logs, key=os.path.getmtime)
        with open(newest, errors='replace') as f:
            out['runner_log'] = {'file': os.path.relpath(newest, root), 'tail': f.read()[-4000:]}
    return out


@tool('template_components', 'Components of a customer or energy plant template (IDA .idm): component, type and variables.',
      {'feature': {'type': 'string', 'enum': ['customer', 'energy_plant']}, 'template': {'type': 'string', 'description': 'template name <number>_<name>'}},
      ['feature', 'template'])
def templateComponentsTool(ctx, args):
    from ..utility_functions.network_pumps import templatePath
    from ..utility_functions.template_graph import templateComponents
    if args['feature'] not in ('customer', 'energy_plant') or not re.match(r'^[\w\- .]+$', args['template']):
        raise ToolError('feature must be customer or energy_plant and template a template name')
    path = templatePath(ctx.config(), args['feature'], args['template'])
    if not os.path.exists(path):
        raise ToolError('template file not found: {}'.format(path))
    return {'template': args['template'], 'components': [{'component': c, 'type': t, 'variables': v[:60]} for c, (t, v) in sorted(templateComponents(path).items())]}


# ---------------- checks, guidance, figures ----------------
@tool('run_checks', 'Model checks of a version: findings {rule, severity, feature, values with threshold and source, text} for the QGIS '
      'model, the IDA templates and the results. Thresholds can be given (else the documented defaults).',
      dict(VERSION, scope={'type': 'string', 'enum': ['all', 'qgis', 'templates', 'results']},
           thresholds={'type': 'object', 'description': 'delta_t_heating_k, delta_t_cooling_k, substation_dp_min_bar, v_max_m_s, dp_spec_max_pa_m'}))
def runChecksTool(ctx, args):
    from ..utility_functions.model_checks import DEFAULTS, runChecks
    config = ctx.config(args.get('version'))
    thresholds = args.get('thresholds') or {}
    unknown = [k for k in thresholds if k not in DEFAULTS]
    if unknown:
        raise ToolError('unknown thresholds {}; known: {}'.format(', '.join(unknown), ', '.join(DEFAULTS)))
    with ctx.cursor(config) as cur:
        result = runChecks(cur, config, args.get('scope') or 'all', thresholds)
    result['job_running'] = ctx.jobRunning()
    return result


@tool('workflow_state', 'Workflow steps of a version in order, each done, missing or stale with the reason, its wiki pages and check rules.', VERSION)
def workflowStateTool(ctx, args):
    from .guidance import workflowState
    config = ctx.config(args.get('version'))
    with ctx.cursor(config) as cur:
        return workflowState(cur, config)


@tool('search_help', 'Search the IDA Districts wiki (XWiki space IDA_Districts): titles, page names, URLs.',
      {'query': {'type': 'string'}, 'limit': {'type': 'integer'}}, ['query'])
def searchHelpTool(ctx, args):
    from .guidance import searchHelp
    return searchHelp(args['query'], int(args.get('limit') or 10))


@tool('read_help_page', 'Read a page of the IDA Districts wiki: title, URL and content (xwiki/2.1).',
      {'page': {'type': 'string', 'description': 'full page name, e.g. IDA_Districts.Districts_GS.Districts_Modeler_GS.Sizing_network.WebHome'}}, ['page'])
def readHelpPageTool(ctx, args):
    from .guidance import readHelpPage
    return readHelpPage(args['page'])


def kpisOf(ctx, version, scenario):
    from ..utility_functions.files import loadModellingSettings
    from ..utility_functions.version_kpis import pricesDir, versionKpis
    config = ctx.config(version)
    try:
        settings = loadModellingSettings(ctx.plugin.plugin_dir, config) or {}
    except Exception:
        settings = {}
    with ctx.cursor(config) as cur:
        return versionKpis(cur, config, scenario, settings, pricesDir(config))


SCENARIO = {'scenario_id': {'type': 'integer', 'description': 'economic scenario id (default: the first)'}}


@tool('version_kpis', 'Key figures of a version, the same as in the network report: heat delivered, peak load, length, linear heat '
      'density, losses, pump energy, energy and costs per plant and carrier, NPV, NPV per MWh delivered, results basis.', dict(VERSION, **SCENARIO))
def versionKpisTool(ctx, args):
    out = kpisOf(ctx, args.get('version'), args.get('scenario_id'))
    out['job_running'] = ctx.jobRunning()
    return out


@tool('compare_versions', 'Key figures of two versions and their differences (b - a), with a note when the results bases differ.',
      dict({'a': {'type': 'string'}, 'b': {'type': 'string'}}, **SCENARIO), ['a', 'b'])
def compareVersionsTool(ctx, args):
    from ..utility_functions.version_kpis import compareVersions
    return compareVersions(kpisOf(ctx, args['a'], args.get('scenario_id')), kpisOf(ctx, args['b'], args.get('scenario_id')))
