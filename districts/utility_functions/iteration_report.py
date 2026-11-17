# coding=utf-8
"""HTML report of a hydraulic balancing or a cost optimization run (OpenSpec change cost-optimization, D22): one
self-contained file in versions/<version>/reports with the inputs (run parameters, pipes, trenches, for the cost
optimization the economic scenario), the outputs per iteration (tables, diagrams, maps rendered from the iteration
layers) and, for the cost optimization, the cost analysis. The run parameters are saved by the run in
versions/<version>/<feature>_run.json, as the dialog's settings may have changed since."""
import base64
import datetime
import html
import io
import json
import os

from matplotlib.backends.backend_agg import FigureCanvasAgg
from matplotlib.figure import Figure
from matplotlib.ticker import FuncFormatter
from qgis.core import Qgis, QgsMapRendererParallelJob, QgsMapSettings, QgsProject, QgsRectangle
from qgis.PyQt.QtCore import QBuffer, QByteArray, QIODevice, QSize
from qgis.PyQt.QtGui import QColor

from .cost_optimization_layers import iterationDiameters, iterationLayers, loadCostIterations
from .dynamic_sizing_results import bar, iterationHeaders, iterationRows, loadIterations, outcomeText, showPair
from .economic_data import loadScenario
from .economics import trenchCostPerMetre
from .hydraulic_balancing import getPipeBundles
from .network_economics import nominalDiameter, trenchLengths
from .pipe_pairs import pairLabel
from .translations import tr, tr_msg

RUN_FILES = {'balancing': 'dynamic_sizing_run.json', 'cost': 'cost_optimization_run.json'}
MAX_MAPS = 10  # maps per pair; more iterations: the first, the best, the last and evenly spread ones
MAP_WIDTH = 900
NPV_GROUPS = ('investment', 'pump_energy', 'heat_losses', 'cold_losses', 'maintenance', 'residual', 'penalties')


# ---------------------------------------------------------------- run parameters
def versionDir(config):
    return os.path.join(config['pathProjects'], config['projectName'], 'versions', config['versionName'])


def saveRunParameters(config, kind, parms):
    """the settings of a run, read by its report"""
    data = dict(parms, saved=datetime.datetime.now().isoformat(timespec='seconds'), version=config['versionName'])
    with open(os.path.join(versionDir(config), RUN_FILES[kind]), 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=1, default=str)


def loadRunParameters(config, kind):
    path = os.path.join(versionDir(config), RUN_FILES[kind])
    if not os.path.exists(path):
        return {}
    with open(path, encoding='utf-8') as f:
        return json.load(f)


# ---------------------------------------------------------------- html
def esc(value):
    return html.escape('' if value is None else str(value))


def number(value, decimals=0):
    if value is None or value == '':
        return ''
    if isinstance(value, bool):
        return tr_msg('yes') if value else tr_msg('no')
    if isinstance(value, (int, float)):
        return '{:,.{d}f}'.format(value, d=decimals).replace(',', "'")
    return str(value)


def money(value):
    return number(value) + ' €' if value is not None else ''


def table(headers, rows, numeric=None):
    """an html table; numeric: the columns aligned right (default: those whose values are numbers)"""
    if not rows:
        return '<p class="empty">{}</p>'.format(esc(tr_msg('none')))
    if numeric is None:
        numeric = {i for i in range(len(headers)) if all(isinstance(r[i], (int, float)) or r[i] in ('', None) for r in rows)}
    head = ''.join('<th>{}</th>'.format(esc(h)) for h in headers)
    body = ''.join('<tr>{}</tr>'.format(''.join('<td{}>{}</td>'.format(' class="num"' if i in numeric else '', cellHtml(cell))
                                                for i, cell in enumerate(row))) for row in rows)
    return '<table><thead><tr>{}</tr></thead><tbody>{}</tbody></table>'.format(head, body)


class Html(str):
    """a table cell that is html already"""


def cellHtml(cell):
    if isinstance(cell, Html):
        return cell
    if isinstance(cell, bool):
        return esc(tr_msg('yes') if cell else tr_msg('no'))
    if isinstance(cell, int):
        return esc(number(cell))
    if isinstance(cell, float):
        # large values with a thousands separator, small ones with up to 3 decimals
        return esc(number(cell) if abs(cell) >= 1000 else '{:g}'.format(round(cell, 3)))
    return esc(cell)


def pngTag(data, alt='', width=None):
    return '<img src="data:image/png;base64,{}" alt="{}"{}>'.format(base64.b64encode(data).decode('ascii'), esc(alt),
                                                                    ' width="{}"'.format(width) if width else '')


def figureTag(fig, alt=''):
    FigureCanvasAgg(fig)
    buffer = io.BytesIO()
    fig.savefig(buffer, format='png', dpi=110, bbox_inches='tight')
    return pngTag(buffer.getvalue(), alt)


def imageBytes(image):
    data = QByteArray()
    buffer = QBuffer(data)
    buffer.open(QIODevice.OpenModeFlag.WriteOnly)
    image.save(buffer, 'PNG')
    buffer.close()
    return bytes(data)


class Report:
    def __init__(self, title, subtitle):
        self.title, self.subtitle = title, subtitle
        self.sections = []  # (anchor, title, level, html)

    def section(self, title, body='', level=2):
        self.sections.append(('s{}'.format(len(self.sections)), title, level, body))

    def html(self):
        toc = ''.join('<li class="l{}"><a href="#{}">{}</a></li>'.format(level, anchor, esc(title)) for anchor, title, level, _ in self.sections if level <= 3)
        body = ''.join('<h{l} id="{a}">{t}</h{l}>{b}'.format(l=level, a=anchor, t=esc(title), b=content) for anchor, title, level, content in self.sections)
        return PAGE.format(title=esc(self.title), subtitle=esc(self.subtitle), toc=toc, body=body)

    def save(self, path):
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, 'w', encoding='utf-8') as f:
            f.write(self.html())
        return path


PAGE = """<!DOCTYPE html>
<html><head><meta charset="utf-8"><title>{title}</title>
<style>
body {{ font-family: 'Segoe UI', Arial, sans-serif; font-size: 10pt; color: #222; margin: 24px auto; max-width: 1000px; padding: 0 16px; }}
h1 {{ font-size: 18pt; margin-bottom: 2px; }} h2 {{ font-size: 14pt; border-bottom: 2px solid #4a7bb7; padding-bottom: 3px; margin-top: 32px; }}
h3 {{ font-size: 12pt; margin-top: 22px; }} h4 {{ font-size: 10.5pt; margin: 16px 0 6px; }}
.subtitle {{ color: #666; margin-top: 0; }}
table {{ border-collapse: collapse; margin: 6px 0 12px; }} th, td {{ border: 1px solid #ccc; padding: 3px 7px; vertical-align: top; }}
th {{ background: #eef3f9; text-align: left; }} td.num {{ text-align: right; white-space: nowrap; }}
tr.best td {{ background: #e3f2e1; }} .empty {{ color: #888; font-style: italic; }}
.legend {{ display: flex; flex-wrap: wrap; gap: 4px 18px; margin: 4px 0 14px; }} .legend div {{ white-space: nowrap; }}
.legend img {{ vertical-align: middle; margin-right: 4px; }} .legend b {{ display: block; width: 100%; margin-top: 4px; }}
nav ol {{ padding-left: 18px; }} nav li.l3 {{ margin-left: 18px; font-size: 9pt; }}
img {{ max-width: 100%; }} .note {{ color: #555; }}
@media print {{ nav {{ display: none; }} h2 {{ page-break-before: always; }} }}
</style></head>
<body><h1>{title}</h1><p class="subtitle">{subtitle}</p><nav><ol>{toc}</ol></nav>{body}</body></html>
"""


# ---------------------------------------------------------------- maps
def legendHtml(layers):
    parts = []
    for layer in layers:
        renderer = layer.renderer()
        items = renderer.legendSymbolItems() if renderer else []
        parts.append('<b>{}</b>'.format(esc(layer.name())))
        for item in items:
            if item.symbol() is None:
                continue
            parts.append('<div>{}{}</div>'.format(pngTag(imageBytes(item.symbol().asImage(QSize(22, 12)))), esc(item.label())))
    return '<div class="legend">{}</div>'.format(''.join(parts))


def contextLayers():
    """the energy plants of the loaded version, for the orientation"""
    return [layer for layer in QgsProject.instance().mapLayersByName(tr('@default', 'energy_plants')) if layer.isValid()]


def renderMap(layers, width=MAP_WIDTH):
    """PNG of the layers (top first) on a white background, with their labels"""
    extent = QgsRectangle()
    extent.setNull()
    for layer in layers:
        if layer.featureCount():
            extent.combineExtentWith(layer.extent())
    if extent.isNull() or extent.width() <= 0:
        return None
    extent.scale(1.06)
    height = int(min(max(width * extent.height() / extent.width(), 320), 1000))
    settings = QgsMapSettings()
    settings.setLayers(layers + contextLayers())
    settings.setDestinationCrs(layers[-1].crs())
    settings.setOutputSize(QSize(width, height))
    settings.setExtent(extent)
    settings.setBackgroundColor(QColor('#ffffff'))
    settings.setFlag(Qgis.MapSettingsFlag.DrawLabeling, True)
    settings.setFlag(Qgis.MapSettingsFlag.Antialiasing, True)
    job = QgsMapRendererParallelJob(settings)
    job.start()
    job.waitForFinished()
    return imageBytes(job.renderedImage())


def mapHtml(layers, alt):
    image = renderMap(layers)
    if image is None:
        return '<p class="empty">{}</p>'.format(esc(tr_msg('no geometries')))
    return pngTag(image, alt) + legendHtml(layers)


def mapIterations(iterations, best=None):
    """the iterations that get a map: all, or at most MAX_MAPS with the first, the best and the last"""
    if len(iterations) <= MAX_MAPS:
        return list(iterations)
    keep = {iterations[0], iterations[-1]} | ({best} if best is not None else set())
    step = (len(iterations) - 1) / (MAX_MAPS - len(keep) + 1)
    k = 1
    while len(keep) < MAX_MAPS:
        keep.add(iterations[min(int(round(k * step)), len(iterations) - 1)])
        k += 1
    return sorted(keep)


# ---------------------------------------------------------------- pipes and trenches
def pipeInfo(cur):
    """{pipe id: row} of public.pipes"""
    cur.execute('SELECT * FROM public.pipes;')
    return {int(row['id']): dict(row) for row in cur.fetchall()}


def lineLengths(cur, schema):
    cur.execute('SELECT id, ST_Length(geom) AS length FROM "{}".lines;'.format(schema))  # nosec B608
    return {int(row['id']): float(row['length'] or 0) for row in cur.fetchall()}


def pipeRows(pipes, ids):
    """input table of the pipes in use"""
    rows = []
    for pid in sorted(ids, key=lambda i: (pipes[i].get('series') or '', float(pipes[i].get('innerpipediameter') or 0))):
        p = pipes[pid]
        rows.append([p['name'], nominalDiameter(p), round(float(p.get('innerpipediameter') or 0) * 1000, 1), p.get('series') or '',
                     None if p.get('costs') is None else float(p['costs']), None if p.get('maintenance_pct') is None else float(p['maintenance_pct']),
                     None if p.get('lifetime_a') is None else float(p['lifetime_a']), None if p.get('p_max_bar') is None else float(p['p_max_bar']),
                     tr_msg('yes') if p.get('example') else ''])
    return rows


PIPE_HEADERS = ('Pipe', 'DN', 'd_i [mm]', 'Series', 'Costs [€/m]', 'Maintenance [%/a]', 'Lifetime [a]', 'p_max [bar]', 'Example value')


def lengthsPerPipe(line_pipes, lengths, pipes):
    """{pipe name: length [m]} of {lid: [pipe id]}"""
    result = {}
    for lid, ids in line_pipes.items():
        for pid in ids:
            name = pipes[pid]['name'] if pid in pipes else str(pid)
            result[name] = result.get(name, 0.0) + lengths.get(lid, 0.0)
    return result


def trenchPerSurfaceDn(trench, dn_of_line):
    """{(surface, DN): length [m]} of the trench parts {lid: {surface: length}} and the DN of the lines"""
    result = {}
    for lid, per in trench.items():
        if lid not in dn_of_line:
            continue
        for surface, length in per.items():
            key = (surface, dn_of_line[lid])
            result[key] = result.get(key, 0.0) + length
    return result


def perIterationTable(first_header, keys, values_by_iteration, decimals=0, key_text=str):
    """rows = keys, columns = iterations"""
    iterations = sorted(values_by_iteration)
    headers = [first_header] + [tr_msg('Iteration {}').format(k) for k in iterations]
    rows = [[key_text(key)] + [round(values_by_iteration[k].get(key, 0.0), decimals) for k in iterations] for key in keys]
    return table(headers, rows)


def defaultSurface(cur, scenario_id=None):
    try:
        if scenario_id is not None:
            cur.execute('SELECT default_surface FROM public.economic_scenarios WHERE id = %s;', (scenario_id,))
        else:
            cur.execute('SELECT default_surface FROM public.economic_scenarios ORDER BY id LIMIT 1;')
        row = cur.fetchone()
    except Exception:  # a project without economic tables
        row = None
    return (row or {}).get('default_surface') or 'paved'


def trenchInputRows(trench, lids):
    per_surface = {}
    for lid in lids:
        for surface, length in trench.get(lid, {}).items():
            per_surface[surface] = per_surface.get(surface, 0.0) + length
    return [[tr_msg(surface), round(length)] for surface, length in sorted(per_surface.items())]


def parameterRows(parms, labels):
    rows = []
    for key, label in labels:
        if key in parms and parms[key] not in (None, '', [], {}):
            value = parms[key]
            if isinstance(value, bool):
                value = tr_msg('yes') if value else tr_msg('no')
            elif isinstance(value, list):
                value = ', '.join(str(v) for v in value)
            rows.append([tr_msg(label), value])
    return rows


def header(config, title):
    return title, '{} {} · {} {} · {}'.format(tr_msg('Project'), config['projectName'], tr_msg('Version'), config['versionName'],
                                              datetime.datetime.now().strftime('%Y-%m-%d %H:%M'))


# ---------------------------------------------------------------- hydraulic balancing
BALANCING_LABELS = (('started', 'Started'), ('network', 'Network'), ('submodel', 'Submodel'), ('time_mode', 'Time step per customer'),
                    ('ep_aggregate', 'Several energy plants'), ('min_share', 'Min. share of a plant'), ('tol_above', 'Tolerance exceedance [Pa]'),
                    ('tol_below', 'Tolerance undershoot [Pa]'), ('weighted', 'Weighted with the mass flow shares'),
                    ('dp_spez_setpoint', 'Pre-sizing with setpoint [Pa/m]'), ('presize_only', 'Only pre-sizing'),
                    ('dp_spez_max', 'Max. specific pressure loss at peak flow [Pa/m]'), ('v_max', 'Max. velocity at peak flow [m/s]'),
                    ('max_iter', 'Max. number of iterations'), ('reference_run', 'Reference run'))


def balancingReport(cur, config):
    """the report of the hydraulic balancing iterations of the loaded version; returns the Report"""
    summaries = loadIterations(config)
    if not summaries:
        raise ValueError(tr_msg('The loaded version has no iterations.'))
    parms = loadRunParameters(config, 'balancing')
    schema = config['versionName']
    pipes = pipeInfo(cur)
    by_name = {p['name']: pid for pid, p in pipes.items()}
    lengths = lineLengths(cur, schema)
    report = Report(*header(config, tr_msg('Hydraulic balancing – report')))

    last = summaries[-1]
    overview = [[tr_msg('Iterations'), len(summaries)], [tr_msg('Outcome of the last iteration'), outcomeText(last['outcome'])],
                [tr_msg('Started'), summaries[0].get('started', '')]]
    if parms.get('saved'):
        overview.append([tr_msg('Run parameters saved'), parms['saved']])
    report.section(tr_msg('Overview'), table([tr_msg('Item'), tr_msg('Value')], overview))

    # inputs
    report.section(tr_msg('Inputs'))
    run_rows = parameterRows(dict(parms, started=summaries[0].get('started')), BALANCING_LABELS)
    periods = parms.get('periods') or {}
    if periods.get('calc_time_from'):
        run_rows.append([tr_msg('Calculation period'), '{} – {}'.format(periods['calc_time_from'], periods.get('calc_time_to', ''))])
    if periods.get('startup_time_from'):
        run_rows.append([tr_msg('Start-up period'), '{} – {}'.format(periods['startup_time_from'], periods.get('startup_time_to', ''))])
    report.section(tr_msg('Run parameters'), table([tr_msg('Parameter'), tr_msg('Value')], run_rows) if parms else
                   '<p class="note">{}</p>'.format(esc(tr_msg('The run parameters were not saved (run before this report existed).'))), 3)
    pair_rows = []
    for pair in last['pairs']:
        temps = pair.get('temps') or [None, None]
        pair_rows.append([pairLabel((pair['supply'], pair['return'])), pair['supply'], pair['return'], temps[0], temps[1],
                          pair.get('n_customers_skipped', 0), pair.get('n_protected', 0)])
    report.section(tr_msg('Supply/return pairs'), table([tr_msg('Pair'), tr_msg('Supply'), tr_msg('Return'), tr_msg('T supply [°C]'), tr_msg('T return [°C]'),
                                                         tr_msg('Customers not included'), tr_msg('Protected lines')], pair_rows), 3)
    if parms.get('protected'):
        report.section(tr_msg('Protected lines'), '<p>{}</p>'.format(esc(', '.join(str(lid) for lid in parms['protected']))), 3)
    used = {by_name[line[k]] for s in summaries for p in s['pairs'] for line in p['lines'].values() for k in ('pipe', 'pipe_new') if line.get(k) in by_name}
    report.section(tr_msg('Pipes in use'), table([tr_msg(h) for h in PIPE_HEADERS], pipeRows(pipes, used)), 3)
    lids = {int(lid) for s in summaries for p in s['pairs'] for lid in p['lines']}
    trench = trenchLengths(cur, schema, defaultSurface(cur))
    report.section(tr_msg('Trench lengths per surface'), table([tr_msg('Surface'), tr_msg('Length [m]')], trenchInputRows(trench, lids)) +
                   '<p class="note">{}</p>'.format(esc(tr_msg('Overlap of the lines with the streets (1 m), the rest with the default surface of the first scenario.'))), 3)

    # outputs
    report.section(tr_msg('Outputs'))
    rows = [list(r) for s in summaries for r in iterationRows(s)]
    report.section(tr_msg('Iterations'), table(iterationHeaders(), rows), 3)
    report.section(tr_msg('Differential pressure at the substations'), balancingDiagram(summaries), 3)
    pipe_lengths, trenches, keys_pipe, keys_trench = {}, {}, set(), set()
    for s in summaries:
        line_pipes, dn = {}, {}
        for p in s['pairs']:
            for lid, line in p['lines'].items():
                pid = by_name.get(line.get('pipe_new') or line.get('pipe'))
                if pid is not None:
                    line_pipes.setdefault(int(lid), []).append(pid)
                    dn[int(lid)] = max(dn.get(int(lid), 0), nominalDiameter(pipes[pid]))
        pipe_lengths[s['iteration']] = lengthsPerPipe(line_pipes, lengths, pipes)
        trenches[s['iteration']] = trenchPerSurfaceDn(trench, dn)
        keys_pipe |= set(pipe_lengths[s['iteration']])
        keys_trench |= set(trenches[s['iteration']])
    report.section(tr_msg('Pipe lengths per iteration [m]'), perIterationTable(tr_msg('Pipe'), sorted(keys_pipe), pipe_lengths) +
                   '<p class="note">{}</p>'.format(esc(tr_msg('Supply pipe of every pair after the sizing of the iteration.'))), 3)
    report.section(tr_msg('Trench lengths per surface and DN per iteration [m]'),
                   perIterationTable(tr_msg('Surface, DN'), sorted(keys_trench), trenches, key_text=lambda k: '{}, DN {}'.format(tr_msg(k[0]), k[1])), 3)

    # per iteration: map and changed lines per pair
    for s in summaries:
        body = ''
        for p in s['pairs']:
            label = pairLabel((p['supply'], p['return']))
            same = [q for t in summaries for q in t['pairs'] if pairLabel((q['supply'], q['return'])) == label]
            if s['iteration'] in mapIterations([t['iteration'] for t in summaries]):
                layers = []
                showPair(cur, config, s['iteration'], label, p, same, new_pipes=s['outcome'] != 'reference', collect=layers)
                body += '<h4>{}</h4>{}'.format(esc(tr_msg('Pair {}').format(label)), mapHtml(layers, label))
            changed = [[int(lid), line['pipe'], line['pipe_new'], line.get('d'), line.get('d_new'), round(line['mdot'], 3),
                        None if line.get('dp_spez') is None else round(line['dp_spez'], 1)]
                       for lid, line in sorted(p['lines'].items(), key=lambda item: int(item[0])) if line.get('changed')]
            if changed:
                body += '<h4>{}</h4>'.format(esc(tr_msg('Lines with new pipes, pair {}').format(label)))
                body += table([tr_msg('Line'), tr_msg('Pipe before'), tr_msg('Pipe after'), tr_msg('d_i before [mm]'), tr_msg('d_i after [mm]'),
                               tr_msg('Design mass flow [kg/s]'), tr_msg('Specific pressure loss [Pa/m]')], changed)
        report.section(tr_msg('Iteration {}').format(s['iteration']) + ' – ' + outcomeText(s['outcome']), body, 3)
    return report


def balancingDiagram(summaries):
    fig = Figure(figsize=(8, 3.2))
    ax = fig.add_subplot(111)
    labels = sorted({pairLabel((p['supply'], p['return'])) for s in summaries for p in s['pairs']})
    for label in labels:
        x, lo, hi = [], [], []
        for s in summaries:
            for p in s['pairs']:
                dps = [c['dp'] for c in p['customers'].values() if c['dp'] is not None]
                if pairLabel((p['supply'], p['return'])) == label and dps:
                    x.append(s['iteration'])
                    lo.append(bar(min(dps)))
                    hi.append(bar(max(dps)))
        line, = ax.plot(x, hi, '-o', label='{} {}'.format(tr_msg('Pair {}').format(label), tr_msg('dp max')))
        ax.plot(x, lo, '--o', color=line.get_color(), label='{} {}'.format(tr_msg('Pair {}').format(label), tr_msg('dp min')))
        ax.fill_between(x, lo, hi, color=line.get_color(), alpha=0.12)
    ax.set_xlabel(tr_msg('iteration'))
    ax.set_ylabel('bar')
    ax.grid(True, linewidth=0.3)
    ax.legend(fontsize=7)
    return figureTag(fig, tr_msg('Differential pressure at the substations'))


# ---------------------------------------------------------------- cost optimization
COST_LABELS = (('scenario_name', 'Scenario'), ('network', 'Network'), ('submodel', 'Submodel'), ('pairs', 'Supply/return pairs'),
               ('periods_text', 'Simulated periods'), ('price_kh', 'Price of a degree hour [€/Kh]'), ('tolerance', 'Tolerance of the room temperature [K]'),
               ('price_kwh', 'Price of unmet load [€/kWh]'), ('unmet_tolerance', 'Tolerance of unmet load [%]'),
               ('dp_spez_max', 'Max. specific pressure loss at peak flow [Pa/m]'), ('v_max', 'Max. velocity at peak flow [m/s]'),
               ('max_iter', 'Max. number of iterations'), ('set_outputs', 'Outputs switched on'), ('protected', 'Protected lines'))


def npvBars(ax, rows):
    """stacked NPV parts per iteration and the NPV estimated by the cost model (dialog and report)"""
    x = [row['iteration'] for row in rows]
    bottom_pos, bottom_neg = [0.0] * len(rows), [0.0] * len(rows)
    for group in NPV_GROUPS:
        values = [row['split'].get(group, 0.0) for row in rows]
        base = [bp if v >= 0 else bn for v, bp, bn in zip(values, bottom_pos, bottom_neg)]
        # the key 'penalties' stays in the iteration files of earlier runs
        ax.bar(x, values, bottom=base, label=groupLabel(group))
        bottom_pos = [bp + max(v, 0) for v, bp in zip(values, bottom_pos)]
        bottom_neg = [bn + min(v, 0) for v, bn in zip(values, bottom_neg)]
    model = [(row['iteration'], row['npv_model']) for row in rows if row.get('npv_model') is not None]
    if model:
        ax.plot([m[0] for m in model], [m[1] for m in model], 'k--o', label=tr_msg('model'))
    ax.set_xticks(x)
    ax.set_xlabel(tr_msg('iteration'))
    ax.set_ylabel(tr_msg('net present value [€]'))
    ax.yaxis.set_major_formatter(FuncFormatter(lambda value, _: '{:,.0f}'.format(value).replace(',', "'")))
    ax.grid(True, axis='y', linewidth=0.3)
    # beside the bars, not over them
    ax.legend(fontsize=7, loc='upper left', bbox_to_anchor=(1.01, 1.0))


def groupLabel(group):
    if group == 'penalties':
        return tr_msg('comfort violations')
    text = tr_msg(group)
    # the keys have no English text of their own
    return text.replace('_', ' ').capitalize() if text == group else text


def periodsText(periods):
    if not periods:
        return ''
    if periods.get('annual'):
        return tr_msg('a year')
    return ', '.join(str(p[0])[:10] for p in periods.get('periods', []))


def linePipesOfState(state, bundles):
    """{lid: [pipe id]} of an iteration's state {lid: bundle}"""
    return {int(lid): list((bundles.get(int(bid)) or bundles.get(bid) or {}).values()) for lid, bid in (state or {}).items() if bid is not None}


def investmentOf(line_pipes, lengths, pipes, trench, scenario):
    """({pipe name: (length, cost)}, {surface: (length, cost)}) of an iteration (cost without replacements)"""
    per_pipe, per_surface = {}, {}
    for lid, ids in line_pipes.items():
        length = lengths.get(lid, 0.0)
        for pid in ids:
            p = pipes.get(pid)
            if p is None:
                continue
            l0, c0 = per_pipe.get(p['name'], (0.0, 0.0))
            per_pipe[p['name']] = (l0 + length, c0 + float(p.get('costs') or 0) * length)
        dn = max([nominalDiameter(pipes[pid]) for pid in ids if pid in pipes] or [0])
        for surface, part in trench.get(lid, {}).items():
            l0, c0 = per_surface.get(surface, (0.0, 0.0))
            per_surface[surface] = (l0 + part, c0 + trenchCostPerMetre(scenario, surface, dn) * part)
    return per_pipe, per_surface


def costReport(cur, config):
    """the report of the cost optimization iterations of the loaded version; returns the Report"""
    rows = loadCostIterations(config)
    if not rows:
        raise ValueError(tr_msg('The loaded version has no iterations.'))
    parms = loadRunParameters(config, 'cost')
    schema = config['versionName']
    scenario_id = parms.get('scenario')
    if scenario_id is None:
        cur.execute('SELECT id FROM public.economic_scenarios ORDER BY id LIMIT 1;')
        found = cur.fetchone()
        scenario_id = found['id'] if found else None
    scenario = loadScenario(cur, scenario_id) if scenario_id is not None else None
    if scenario is None:
        raise ValueError(tr_msg('The economic scenario of the run does not exist anymore.'))
    sc = scenario['scenario']
    pipes, bundles = pipeInfo(cur), getPipeBundles(cur)
    lengths = lineLengths(cur, schema)
    trench = trenchLengths(cur, schema, sc.get('default_surface') or 'paved')
    best = min(rows, key=lambda r: r['npv'])
    reference = rows[0]
    report = Report(*header(config, tr_msg('Cost optimization – report')))

    overview = [[tr_msg('Iterations'), len(rows)], [tr_msg('Outcome of the last iteration'), rows[-1].get('outcome', '')],
                [tr_msg('Net present value of iteration {}').format(reference['iteration']), money(reference['npv'])],
                [tr_msg('Least net present value: iteration {}').format(best['iteration']), money(best['npv'])],
                [tr_msg('Difference to iteration {}').format(reference['iteration']), money(best['npv'] - reference['npv'])]]
    if parms.get('saved'):
        overview.append([tr_msg('Run parameters saved'), parms['saved']])
    report.section(tr_msg('Overview'), table([tr_msg('Item'), tr_msg('Value')], overview, numeric={1}))

    # inputs
    report.section(tr_msg('Inputs'))
    shown = dict(parms, scenario_name=sc.get('name'), periods_text=periodsText(parms.get('periods')),
                 pairs=[pairLabel(tuple(p)) for p in parms.get('pairs') or []])
    report.section(tr_msg('Run parameters'), table([tr_msg('Parameter'), tr_msg('Value')], parameterRows(shown, COST_LABELS)) if parms else
                   '<p class="note">{}</p>'.format(esc(tr_msg('The run parameters were not saved (run before this report existed).'))), 3)
    report.section(tr_msg('Economic scenario'), table([tr_msg('Parameter'), tr_msg('Value')], [
        [tr_msg('Name'), sc.get('name')], [tr_msg('Interest [%/a]'), sc.get('interest_pct')], [tr_msg('Period [a]'), sc.get('period_a')],
        [tr_msg('Residual value'), tr_msg('yes') if sc.get('residual_value') else tr_msg('no')], [tr_msg('Default surface'), tr_msg(sc.get('default_surface') or '')],
        [tr_msg('Electricity profile file'), sc.get('el_profile_file') or tr_msg('flat')], [tr_msg('Pumps [€/kW]'), sc.get('pump_costs_eur7kw')],
        [tr_msg('Pump maintenance [%/a]'), sc.get('pump_maintenance_pct')], [tr_msg('Pump lifetime [a]'), sc.get('pump_lifetime_a')],
        [tr_msg('Example values'), tr_msg('yes') if sc.get('example') else tr_msg('no')]], numeric={1}), 3)
    group_rows = [[tr_msg(g), None if r.get('start_price') is None else float(r['start_price']), None if r.get('escalation_pct') is None else float(r['escalation_pct']),
                   r.get('description') or ''] for g, r in sorted(scenario['groups'].items())]
    report.section(tr_msg('Prices per cost group'), table([tr_msg('Cost group'), tr_msg('Start price [€/kWh]'), tr_msg('Escalation [%/a]'), tr_msg('Description')],
                                                          group_rows) + '<p class="note">{}</p>'.format(esc(tr_msg(
                                                              'The start price is used for electricity; heat and cold are valued with the price curves, '
                                                              'the investment with the pipe, trench and pump costs. Escalation applies to every group.'))), 3)
    if scenario['levels']:
        level_rows = [[tr_msg(g), year, factor] for g, years in sorted(scenario['levels'].items()) for year, factor in sorted(years.items())]
        report.section(tr_msg('Price levels per year'), table([tr_msg('Cost group'), tr_msg('Year'), tr_msg('Factor')], level_rows), 3)
    report.section(tr_msg('Price curves heat and cold'), priceCurves(scenario['curves']), 3)
    report.section(tr_msg('Trench costs per surface'), table([tr_msg('Surface'), tr_msg('a [€/m]'), tr_msg('b [€/m per DN]')],
                                                             [[tr_msg(s), a, b] for s, (a, b) in sorted(scenario['trench'].items())]), 3)
    used = {pid for row in rows for ids in linePipesOfState(row.get('state'), bundles).values() for pid in ids}
    report.section(tr_msg('Pipes in use'), table([tr_msg(h) for h in PIPE_HEADERS], pipeRows(pipes, used & set(pipes))), 3)
    lids = {lid for row in rows for lid in linePipesOfState(row.get('state'), bundles)}
    report.section(tr_msg('Trench lengths per surface'), table([tr_msg('Surface'), tr_msg('Length [m]')], trenchInputRows(trench, lids)) +
                   '<p class="note">{}</p>'.format(esc(tr_msg('Overlap of the lines with the streets (1 m), the rest with the default surface of the scenario.'))), 3)

    # outputs
    report.section(tr_msg('Outputs'))
    iteration_rows = [[r['iteration'], round(r['npv']), None if r.get('npv_model') is None else round(r['npv_model']),
                       '' if r.get('model_error') is None else '{:.1%}'.format(r['model_error']), r.get('n_larger', ''), r.get('n_smaller', ''),
                       r.get('n_rejected', ''), len(r.get('penalty_customers') or []), r.get('outcome', '')] for r in rows]
    report.section(tr_msg('Iterations'), table([tr_msg('Iteration'), tr_msg('NPV simulated'), tr_msg('NPV model'), tr_msg('Model error'), tr_msg('larger'),
                                                tr_msg('smaller'), tr_msg('rejected'), tr_msg('Customers with deficit'), tr_msg('Outcome')], iteration_rows) +
                   '<p class="note">{}</p>'.format(esc(tr_msg('Iteration {} has the least net present value.').format(best['iteration']))), 3)
    fig = Figure(figsize=(8, 3.6))
    npvBars(fig.add_subplot(111), rows)
    report.section(tr_msg('Net present value'), figureTag(fig, tr_msg('Net present value')), 3)
    pipe_lengths, trenches, invest = {}, {}, {}
    for row in rows:
        line_pipes = linePipesOfState(row.get('state'), bundles)
        dn = {lid: max([nominalDiameter(pipes[pid]) for pid in ids if pid in pipes] or [0]) for lid, ids in line_pipes.items()}
        pipe_lengths[row['iteration']] = lengthsPerPipe(line_pipes, lengths, pipes)
        trenches[row['iteration']] = trenchPerSurfaceDn(trench, dn)
        invest[row['iteration']] = investmentOf(line_pipes, lengths, pipes, trench, scenario)
    report.section(tr_msg('Pipe lengths per iteration [m]'), perIterationTable(tr_msg('Pipe'), sorted({k for v in pipe_lengths.values() for k in v}), pipe_lengths) +
                   '<p class="note">{}</p>'.format(esc(tr_msg('Every pipe of the bundles (supply and return), so about twice the trench length.'))), 3)
    report.section(tr_msg('Trench lengths per surface and DN per iteration [m]'),
                   perIterationTable(tr_msg('Surface, DN'), sorted({k for v in trenches.values() for k in v}), trenches,
                                     key_text=lambda k: '{}, DN {}'.format(tr_msg(k[0]), k[1])), 3)
    catalog, diameters, all_d = iterationDiameters(cur, rows)
    by_iteration = {row['iteration']: row for row in rows}
    for row in rows:
        k = row['iteration']
        body = ''
        if k in mapIterations([r['iteration'] for r in rows], best['iteration']):
            layers = []
            iterationLayers(cur, schema, k, rows, catalog, diameters, all_d, collect=layers)
            body += mapHtml(layers, tr_msg('Iteration {}').format(k))
        steps = (by_iteration.get(k - 1) or {}).get('steps') or []
        if steps:
            step_rows = []
            for step in sorted(steps, key=lambda s: int(s['line'])):
                before = [catalog.get(int(pid), {}).get('name', pid) for _, pid in sorted(step['before'].items())]
                after = [catalog.get(int(pid), {}).get('name', pid) for _, pid in sorted(step['after'].items())]
                step_rows.append([int(step['line']), ', '.join(str(b) for b in before), ', '.join(str(a) for a in after),
                                  tr_msg('larger') if step.get('larger') else tr_msg('smaller'), round(step.get('dnpv') or 0)])
            body += '<h4>{}</h4>'.format(esc(tr_msg('Lines changed for this iteration')))
            body += table([tr_msg('Line'), tr_msg('Pipes before'), tr_msg('Pipes after'), tr_msg('Change'), tr_msg('NPV change estimated [€]')], step_rows)
        if row.get('penalty_customers'):
            body += '<p>{}: {}</p>'.format(esc(tr_msg('Customers with a new deficit')), esc(', '.join(str(c) for c in row['penalty_customers'])))
        title = tr_msg('Iteration {}').format(k) + (' – ' + row['outcome'] if row.get('outcome') else '')
        report.section(title, body or '<p class="empty">{}</p>'.format(esc(tr_msg('no change'))), 3)

    # cost analysis
    report.section(tr_msg('Cost analysis'))
    iterations = [r['iteration'] for r in rows]
    split_rows = [[groupLabel(g)] + [round(by_iteration[k]['split'].get(g, 0.0)) for k in iterations] for g in NPV_GROUPS]
    split_rows.append([tr_msg('Net present value')] + [round(by_iteration[k]['npv']) for k in iterations])
    report.section(tr_msg('Net present value per part [€]'), table([tr_msg('Part')] + [tr_msg('Iteration {}').format(k) for k in iterations], split_rows), 3)
    diff_rows = [[groupLabel(g), round(reference['split'].get(g, 0.0)), round(best['split'].get(g, 0.0)),
                  round(best['split'].get(g, 0.0) - reference['split'].get(g, 0.0))] for g in NPV_GROUPS]
    diff_rows.append([tr_msg('Net present value'), round(reference['npv']), round(best['npv']), round(best['npv'] - reference['npv'])])
    headers = [tr_msg('Part'), tr_msg('Iteration {}').format(reference['iteration']), tr_msg('Iteration {}').format(best['iteration']), tr_msg('Difference')]
    report.section(tr_msg('Least net present value against the first iteration [€]'), table(headers, diff_rows), 3)
    inv_rows = [[k, round(sum(c for _, c in invest[k][0].values())), round(sum(c for _, c in invest[k][1].values())),
                 round(sum(c for _, c in invest[k][0].values()) + sum(c for _, c in invest[k][1].values()))] for k in iterations]
    report.section(tr_msg('Investment per iteration [€]'), table([tr_msg('Iteration'), tr_msg('Pipes'), tr_msg('Trench'), tr_msg('Total')], inv_rows) +
                   '<p class="note">{}</p>'.format(esc(tr_msg('Initial investment without the pumps and the replacements; the pumps are sized from the simulated peak power.'))), 3)
    names = sorted(set(invest[reference['iteration']][0]) | set(invest[best['iteration']][0]))
    pipe_rows = []
    for name in names:
        l0, c0 = invest[reference['iteration']][0].get(name, (0.0, 0.0))
        l1, c1 = invest[best['iteration']][0].get(name, (0.0, 0.0))
        pipe_rows.append([name, round(l0), round(l1), round(c0), round(c1), round(c1 - c0)])
    report.section(tr_msg('Pipes: first iteration and least net present value'), table(
        [tr_msg('Pipe'), tr_msg('Length {} [m]').format(reference['iteration']), tr_msg('Length {} [m]').format(best['iteration']),
         tr_msg('Investment {} [€]').format(reference['iteration']), tr_msg('Investment {} [€]').format(best['iteration']), tr_msg('Difference [€]')], pipe_rows), 3)
    surfaces = sorted(set(invest[reference['iteration']][1]) | set(invest[best['iteration']][1]))
    surface_rows = []
    for surface in surfaces:
        l0, c0 = invest[reference['iteration']][1].get(surface, (0.0, 0.0))
        _, c1 = invest[best['iteration']][1].get(surface, (0.0, 0.0))
        surface_rows.append([tr_msg(surface), round(l0), round(c0), round(c1), round(c1 - c0),
                             '' if surface in scenario['trench'] else tr_msg('no trench costs: default surface')])
    report.section(tr_msg('Trench: first iteration and least net present value'), table(
        [tr_msg('Surface'), tr_msg('Length [m]'), tr_msg('Investment {} [€]').format(reference['iteration']),
         tr_msg('Investment {} [€]').format(best['iteration']), tr_msg('Difference [€]'), tr_msg('Note')], surface_rows), 3)
    reasons = {}
    for row in rows:
        for lid_reasons in (row.get('rejected') or {}).values():
            for reason in (lid_reasons if isinstance(lid_reasons, list) else [lid_reasons]):
                text = reasonText(reason)
                reasons[text] = reasons.get(text, 0) + 1
    if reasons:
        report.section(tr_msg('Rejected changes'), table([tr_msg('Reason'), tr_msg('Number')], sorted(([r, n] for r, n in reasons.items()), key=lambda x: -x[1])), 3)
    return report


REASONS = {'protected': 'protected line', 'penalty': 'smaller pipe made a customer fall short before', 'no pair': 'not in a pair',
           'no larger pipe': 'no larger pipe in the series', 'no smaller pipe': 'no smaller pipe in the series',
           'p_max': 'pressure above p_max of the pipe', 'peak': 'specific pressure loss or velocity at peak flow above the limit'}


def reasonText(reason):
    return tr_msg(REASONS.get(str(reason), str(reason)))


def priceCurves(curves):
    rows = [[tr_msg(mode), t, price] for mode in ('heat', 'cold') for t, price in curves.get(mode, [])]
    if not rows:
        return '<p class="empty">{}</p>'.format(esc(tr_msg('no curve: the losses cost nothing')))
    fig = Figure(figsize=(6, 2.6))
    ax = fig.add_subplot(111)
    for mode, color in (('heat', '#d7301f'), ('cold', '#2171b5')):
        points = curves.get(mode, [])
        if points:
            ax.plot([p[0] for p in points], [p[1] for p in points], '-o', color=color, label=tr_msg(mode))
    ax.set_xlabel(tr_msg('supply temperature [°C]'))
    ax.set_ylabel('€/kWh')
    ax.grid(True, linewidth=0.3)
    ax.legend(fontsize=7)
    return table([tr_msg('Mode'), tr_msg('supply temperature [°C]'), tr_msg('Price [€/kWh]')], rows) + figureTag(fig, tr_msg('Price curves heat and cold'))


# ---------------------------------------------------------------- entry
def writeReport(cur, config, kind):
    """builds the report of the loaded version and returns the path of the html file"""
    report = balancingReport(cur, config) if kind == 'balancing' else costReport(cur, config)
    name = '{}_{}.html'.format('hydraulic_balancing' if kind == 'balancing' else 'cost_optimization', datetime.datetime.now().strftime('%Y%m%d_%H%M%S'))
    return report.save(os.path.join(versionDir(config), 'reports', name))


def openReport(parent, cur, config, kind):
    """writes the report of the loaded version and opens it in the browser; errors in a message box"""
    import traceback
    from qgis.core import QgsMessageLog
    from qgis.PyQt.QtCore import QUrl, Qt
    from qgis.PyQt.QtGui import QDesktopServices
    from qgis.PyQt.QtWidgets import QApplication, QMessageBox
    from .compat import MessageCritical
    QApplication.setOverrideCursor(Qt.CursorShape.WaitCursor)
    try:
        path = writeReport(cur, config, kind)
    except ValueError as error:
        QApplication.restoreOverrideCursor()
        QMessageBox.information(parent, tr_msg('Report'), str(error))
        return None
    except Exception:
        QApplication.restoreOverrideCursor()
        QgsMessageLog.logMessage(traceback.format_exc(), 'Districts', MessageCritical)
        QMessageBox.warning(parent, tr_msg('Report'), tr_msg('The report could not be written: ') + traceback.format_exc().splitlines()[-1])
        return None
    QApplication.restoreOverrideCursor()
    QDesktopServices.openUrl(QUrl.fromLocalFile(path))
    return path
