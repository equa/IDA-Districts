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
from .energy_use import CARRIER_LABELS
from .hydraulic_balancing import getPipeBundles
from .network_economics import nominalDiameter, trenchLengths
from .pipe_pairs import pairLabel
from .translations import tr, tr_msg

RUN_FILES = {'balancing': 'dynamic_sizing_run.json', 'cost': 'cost_optimization_run.json'}
MAX_MAPS = 10  # maps per pair; more iterations: the first, the best, the last and evenly spread ones
MAP_WIDTH = 900
NPV_GROUPS = ('investment', 'pump_energy', 'heat_losses', 'cold_losses', 'plant_energy', 'customer_energy', 'maintenance', 'residual', 'penalties')


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
    body = ''.join('<tr{}>{}</tr>'.format(' class="total"' if isinstance(row, TotalRow) else '',
                                          ''.join('<td{}>{}</td>'.format(' class="num"' if i in numeric else '', cellHtml(cell))
                                                  for i, cell in enumerate(row))) for row in rows)
    return '<table><thead><tr>{}</tr></thead><tbody>{}</tbody></table>'.format(head, body)


class Html(str):
    """a table cell that is html already"""


class TotalRow(list):
    """a table row shown in bold"""


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
.eq {{ font-family: 'Cambria Math', 'Times New Roman', serif; font-size: 11.5pt; margin: 3px 0 3px 18px; }}
tr.total td {{ font-weight: bold; background: #f4f4f4; }}
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
               ('mode_deadband_pct', 'Deadband heating/cooling [%]'), ('max_iter', 'Max. number of iterations'), ('set_outputs', 'Outputs switched on'),
               ('protected', 'Protected lines'))


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

    stageSections(report, rows, parms)

    # cost analysis
    report.section(tr_msg('Cost analysis'))
    iterations = [r['iteration'] for r in rows]
    split_rows = [[groupLabel(g)] + [round(by_iteration[k]['split'].get(g, 0.0)) for k in iterations] for g in NPV_GROUPS]
    split_rows.append([tr_msg('Net present value')] + [round(by_iteration[k]['npv']) for k in iterations])
    report.section(tr_msg('Net present value per part [€]'), table([tr_msg('Part')] + [tr_msg('Iteration {}').format(k) for k in iterations], split_rows), 3)
    npvCalculation(report, rows)
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
    deficit_rows = [[r['iteration'], len(r.get('deficit_customers') or []), round(sum(v[0] for v in (r.get('deficits') or {}).values())),
                     round(sum(v[1] for v in (r.get('deficits') or {}).values())), ', '.join(str(c) for c in (r.get('deficit_customers') or [])[:15]),
                     ', '.join(str(c) for c in r.get('penalty_customers') or [])] for r in rows if 'deficit_customers' in r]
    if deficit_rows:
        note = ''
        if deficit_rows[0][1]:
            note = '<p class="note">{}</p>'.format(esc(tr_msg('Iteration {} has comfort violations already; mostly hydraulic: balance the network '
                                                              'first. They count in the NPV of every iteration.').format(deficit_rows[0][0])))
        report.section(tr_msg('Comfort violations per iteration'), table(
            [tr_msg('Iteration'), tr_msg('Customers'), tr_msg('Kh/a'), tr_msg('Unmet kWh/a'), tr_msg('Customers with a deficit'),
             tr_msg('New against iteration 0')], deficit_rows) + note, 3)
    reasons = {}
    for row in rows:
        for lid_reasons in (row.get('rejected') or {}).values():
            for reason in (lid_reasons if isinstance(lid_reasons, list) else [lid_reasons]):
                text = reasonText(reason)
                reasons[text] = reasons.get(text, 0) + 1
    if reasons:
        report.section(tr_msg('Rejected changes'), table([tr_msg('Reason'), tr_msg('Number')], sorted(([r, n] for r, n in reasons.items()), key=lambda x: -x[1])), 3)
    return report


# ---------------------------------------------------------------- net present value: equations and numbers
def eq(formula):
    return '<div class="eq">{}</div>'.format(formula)


PV = 'Σ<sub><i>t</i>=1…<i>N</i></sub> <i>L</i><sub>{g}</sub>(<i>t</i>) / (1+<i>i</i>)<sup><i>t</i></sup>'
EQUATIONS = (
    ('Net present value', '<i>NPV</i> = Σ<sub><i>k</i></sub> (<i>I</i><sub><i>k</i></sub> + <i>M</i><sub><i>k</i></sub> + <i>R</i><sub><i>k</i></sub>)'
                          ' + <i>E</i><sub>pump</sub> + <i>E</i><sub>heat</sub> + <i>E</i><sub>cold</sub> + <i>S</i>'),
    ('Investment of item k, bought in year 0 and replaced at the end of its lifetime',
     '<i>I</i><sub><i>k</i></sub> = <i>K</i><sub><i>k</i></sub> · Σ<sub><i>t</i> ∈ {0, <i>n</i><sub><i>k</i></sub>, 2<i>n</i><sub><i>k</i></sub>, … &lt; <i>N</i>}</sub>'
     ' <i>L</i><sub>inv</sub>(<i>t</i>) / (1+<i>i</i>)<sup><i>t</i></sup>'),
    ('Maintenance', '<i>M</i><sub><i>k</i></sub> = <i>K</i><sub><i>k</i></sub> · <i>m</i><sub><i>k</i></sub> · ' + PV.format(g='maint')),
    ('Residual value (negative, only if the scenario counts it)',
     '<i>R</i><sub><i>k</i></sub> = −<i>K</i><sub><i>k</i></sub> · <i>L</i><sub>inv</sub>(<i>t</i><sub>last</sub>) · '
     '(<i>t</i><sub>last</sub> + <i>n</i><sub><i>k</i></sub> − <i>N</i>) / <i>n</i><sub><i>k</i></sub> / (1+<i>i</i>)<sup><i>N</i></sup>'),
    ('Energy costs of the cost group g (pump energy: electricity, heat losses: heat, cold losses: cold)',
     '<i>E</i><sub><i>g</i></sub> = <i>C</i><sub><i>g</i>,0</sub> · ' + PV.format(g='<i>g</i>')),
    ('Price level of a cost group (the factor of the year instead, if the price levels give one)',
     '<i>L</i><sub><i>g</i></sub>(<i>t</i>) = (1 + <i>e</i><sub><i>g</i></sub>)<sup><i>t</i></sup>'),
    ('Comfort violations: present value of the yearly penalty', '<i>S</i> = <i>P</i> · ((1+<i>i</i>)<sup><i>N</i></sup> − 1) / (<i>i</i> · (1+<i>i</i>)<sup><i>N</i></sup>)'),
    ('Investment in year 0 per item', '<i>K</i><sub>pipe</sub> = Σ<sub>lines</sub> <i>c</i><sub>pipe</sub> · <i>l</i> ; '
                                      '<i>K</i><sub>trench,<i>s</i></sub> = Σ<sub>lines</sub> (<i>a</i><sub><i>s</i></sub> + <i>b</i><sub><i>s</i></sub> · DN) · <i>l</i><sub><i>s</i></sub> ; '
                                      '<i>K</i><sub>pumps</sub> = <i>c</i><sub>pump</sub> · Σ<sub>pumps</sub> <i>P</i><sub>peak</sub>'),
    ('Energy costs of year 0', '<i>C</i><sub>pump,0</sub> = <i>c</i><sub>el</sub> · Σ<sub><i>h</i></sub> <i>w</i><sub><i>h</i></sub> · <i>P</i><sub>pump,<i>h</i></sub> · <i>s</i><sub><i>h</i></sub>'),
    ('', '<i>C</i><sub>heat,0</sub> = Σ<sub><i>h</i></sub> <i>w</i><sub><i>h</i></sub> · <i>Q</i><sub>heat,<i>h</i></sub> · <i>c</i><sub>heat</sub>(<i>T</i><sub>heat,<i>h</i></sub>)'),
    ('', '<i>C</i><sub>cold,0</sub> = −Σ<sub><i>h</i></sub> <i>w</i><sub><i>h</i></sub> · <i>Q</i><sub>cold,<i>h</i></sub> · <i>c</i><sub>cold</sub>(<i>T</i><sub>cold,<i>h</i></sub>)'),
    ('Heat leaving the pipes of a mode', '<i>Q</i><sub><i>h</i></sub> = Σ<sub>pipes</sub> <i>U</i>′ · <i>l</i> · (<i>T</i><sub>pipe,<i>h</i></sub> − <i>T</i><sub>amb,<i>h</i></sub>)'),
    ('Mode of a supply/return pair per step: heat the plants put into the network; heating above +band, cooling below −band, the previous mode inside',
     '<i>Φ</i><sub><i>h</i></sub> = <i>c</i><sub>p</sub> · Σ<sub>plants</sub> Σ<sub>supply, return</sub> <i>ṁ</i> · <i>T</i> ; '
     'band = <i>x</i> · (max(<i>Φ</i>, 0) − min(<i>Φ</i>, 0))'),
    ('Sign of the heat flows: Q > 0 the pipes give heat off to the ground or air, Q < 0 they take heat up. Heating: heat given off costs, '
     'heat taken up saves. Cooling: heat taken up costs, heat given off saves (the plant rejects less heat).', ''),
    ('With energy results: the energy the plants (and, for the whole system, the customers) buy replaces the priced pipe losses',
     '<i>NPV</i> = Σ<sub><i>k</i></sub> (<i>I</i><sub><i>k</i></sub> + <i>M</i><sub><i>k</i></sub> + <i>R</i><sub><i>k</i></sub>) + <i>E</i><sub>pump</sub> + '
     'Σ<sub><i>c</i></sub> <i>E</i><sub>plants,<i>c</i></sub> + Σ<sub><i>c</i></sub> <i>E</i><sub>customers,<i>c</i></sub> + <i>S</i> ; '
     '<i>C</i><sub><i>c</i>,0</sub> = Σ<sub><i>h</i></sub> <i>w</i><sub><i>h</i></sub> · <i>P</i><sub><i>c</i>,<i>h</i></sub> · <i>p</i><sub><i>c</i></sub> · <i>s</i><sub><i>h</i></sub>'),
    ('Marginal price of a pipe loss per step and pair: the most expensive plant running above the threshold of its peak heat flow',
     '<i>p</i><sub>marg,<i>h</i></sub> = max<sub>plants</sub> Σ<sub><i>c</i></sub> <i>P</i><sub><i>c</i>,<i>h</i></sub> · <i>p</i><sub><i>c</i></sub> · <i>s</i><sub><i>h</i></sub> / |<i>Φ</i><sub>plant,<i>h</i></sub>|'),
    ('Yearly penalty: the comfort violations against the setpoint and the required load, of every customer',
     '<i>P</i> = Σ<sub>customers</sub> [<i>p</i><sub>Kh</sub> · <i>Kh</i> + <i>p</i><sub>kWh</sub> · <i>kWh</i>]'),
)
SYMBOLS = (
    ('<i>i</i>, <i>N</i>', 'interest rate and amortization period of the scenario'),
    ('<i>k</i>', 'investment item: a pipe type, the trench of a surface, the pumps'),
    ('<i>K</i><sub><i>k</i></sub>, <i>n</i><sub><i>k</i></sub>, <i>m</i><sub><i>k</i></sub>', 'investment in year 0, lifetime and maintenance share per year of the item'),
    ('<i>t</i><sub>last</sub>', 'last purchase year of the item within the period'),
    ('<i>e</i><sub><i>g</i></sub>', 'escalation of the cost group'),
    ('<i>h</i>, <i>w</i><sub><i>h</i></sub>', 'simulated time step and its weight in hours per year (time step, times the weight of its representative week)'),
    ('<i>s</i><sub><i>h</i></sub>', 'electricity price profile, scaled to mean 1 (1 without a profile)'),
    ('<i>c</i><sub>el</sub>, <i>c</i><sub>heat</sub>(<i>T</i>), <i>c</i><sub>cold</sub>(<i>T</i>)', 'start price of electricity and the price curves of heat and cold over the supply temperature'),
    ('<i>P</i><sub>pump,<i>h</i></sub>', 'pump power of the energy plants and customers (outputs ppump_ep, ppump_c)'),
    ('<i>Q</i><sub>heat,<i>h</i></sub>, <i>Q</i><sub>cold,<i>h</i></sub>', 'heat leaving the heating and the cooling pipes; a cooling pipe gaining heat gives a negative Q, so a cost'),
    ('<i>T</i><sub>heat,<i>h</i></sub>, <i>T</i><sub>cold,<i>h</i></sub>', 'mean supply temperature of the plants per mode'),
    ('<i>U</i>′, <i>T</i><sub>amb</sub>', 'heat loss coefficient per metre of the pipe and the ground or air temperature'),
    ('<i>Kh</i>, <i>kWh</i>', 'degree hours of the load models (beyond the tolerance) and unmet load of the source-file customers per year'),
    ('<i>ṁ</i>, <i>x</i>', 'mass flow at a plant connection (leaving the plant positive) and the deadband of the run'),
    ('<i>c</i>, <i>P</i><sub><i>c</i>,<i>h</i></sub>, <i>p</i><sub><i>c</i></sub>', 'carrier (electricity, fuel, purchased heat), the power bought (energy-use list) and its start price; s_h only for electricity'),
)


def factorText(value):
    return '{:.4f}'.format(value)


def termItem(term):
    kind = term.get('kind')
    if kind == 'trench':
        return tr_msg('Trench') + ' ' + tr_msg(term.get('name') or '')
    if kind == 'pumps':
        return tr_msg('Pumps')
    if term['group'] in ('pump_energy', 'heat_losses', 'cold_losses', 'plant_energy', 'customer_energy'):
        return tr_msg(CARRIER_LABELS.get(term.get('kind'), term.get('kind') or ''))
    return term.get('name') or ''


def termDetail(term, energy):
    group = term['group']
    if group == 'investment':
        text = 'n = {:g} a, t = {}'.format(term.get('lifetime') or 0, ', '.join(str(t) for t in term.get('years', [])))
        if term.get('length'):
            text = '{} m; '.format(number(term['length'])) + text
        if term.get('power_kw') is not None:
            text = '{} kW; '.format(number(term['power_kw'], 1)) + text
        return text
    if group == 'maintenance':
        return 'm = {:g} %/a'.format(term.get('maintenance_pct') or 0)
    if group == 'residual':
        return 't_last = {}, {} = {:.3f}'.format(term.get('last'), tr_msg('remaining share'), term.get('remaining') or 0)
    if group in ('plant_energy', 'customer_energy'):
        kwh = (((energy or {}).get('energy_basis') or {}).get('kwh') or {}).get(group, {}).get(term.get('kind'), 0.0)
        return '{} kWh/a, {:.4f} €/kWh'.format(number(kwh), term['base'] / kwh) if kwh else ''
    kwh = (energy or {}).get({'pump_energy': 'pump_kwh', 'heat_losses': 'heat_kwh', 'cold_losses': 'cold_kwh'}.get(group, ''), 0.0)
    if not kwh:
        return ''
    return '{} kWh/a, {:.4f} €/kWh'.format(number(kwh), abs(term['base'] / kwh))




def energySections(report, saved):
    """basis of the NPV, energy and costs per plant (customers per carrier) and the hours per marginal plant
    (plant-energy-costs D7)"""
    with_energy = [r for r in saved if (r['economics'].get('energy_basis') or {}).get('features') is not None]
    if not with_energy:
        report.section(tr_msg('Basis of the net present value'), '<p class="note">{}</p>'.format(esc(tr_msg(
            'Price curves: the version has no energy-use results (outputs energy_ep, energy_c); the pipe losses are priced with the curves.'))), 3)
        return
    first = with_energy[0]['economics']['energy_basis']
    text = tr_msg('Energy use of the plants and customers (system boundary: {}); the pipe losses are shown for information.').format(
        tr_msg('whole system') if first.get('boundary') == 'system' else tr_msg('network operator'))
    if first.get('no_price'):
        text += ' ' + tr_msg('Carriers in use without a price (valued with 0): {}').format(', '.join(tr_msg(CARRIER_LABELS.get(c, c)) for c in first['no_price']))
    report.section(tr_msg('Basis of the net present value'), '<p>{}</p>'.format(esc(text)), 3)
    rows = []
    for r in with_energy:
        basis = r['economics']['energy_basis']
        customers: dict = {}
        for feature, fid, carrier, kwh, eur in basis['features']:
            if feature == 'customer':
                kwh0, eur0 = customers.get(carrier, (0.0, 0.0))
                customers[carrier] = (kwh0 + kwh, eur0 + eur)
            else:
                rows.append([r['iteration'], '{} {}'.format(tr_msg('Plant'), fid), tr_msg(CARRIER_LABELS.get(carrier, carrier)), round(kwh), round(eur)])
        counted = basis.get('boundary') == 'system'
        for carrier, (kwh, eur) in sorted(customers.items()):
            label = tr_msg('Customers') + ('' if counted else ' ({})'.format(tr_msg('information')))
            rows.append([r['iteration'], label, tr_msg(CARRIER_LABELS.get(carrier, carrier)), round(kwh), round(eur)])
        losses = basis.get('losses') or {}
        rows.append([r['iteration'], tr_msg('Pipe losses (information)'), tr_msg('heating') + ' / ' + tr_msg('cooling'), '',
                     round(losses.get('heat', 0.0) + losses.get('cold', 0.0))])
    report.section(tr_msg('Energy use and costs of year 0'), table([tr_msg('Iteration'), tr_msg('Plant or customers'), tr_msg('Carrier'),
                                                                     tr_msg('Energy [kWh/a]'), tr_msg('Costs [€/a]')], rows), 3)
    delivered_rows = []
    for r in with_energy:
        delivered = r['economics']['energy_basis'].get('delivered') or {}
        total = delivered.get('heat', 0.0) + delivered.get('cold', 0.0)
        if total:
            delivered_rows.append([r['iteration'], round(delivered.get('heat', 0.0)), round(delivered.get('cold', 0.0)), round(r['npv'] / (total / 1000), 1)])
    if delivered_rows:
        report.section(tr_msg('Energy delivered to the customers'), table(
            [tr_msg('Iteration'), tr_msg('Heat [kWh/a]'), tr_msg('Cold [kWh/a]'), tr_msg('NPV per MWh delivered per year [€]')], delivered_rows) +
            '<p class="note">{}</p>'.format(esc(tr_msg('Delivered through the entries of kind "delivered" (e.g. the heat exchanger of a substation); '
                                                       'not bought and not in the NPV, whose energy costs already cover it.'))), 3)
    hour_rows = [[r['iteration'], '{} {}'.format(tr_msg('Plant'), fid), round(h)] for r in with_energy
                 for fid, h in sorted(r['economics']['energy_basis'].get('marginal_hours', {}).items(), key=lambda x: int(x[0]))]
    hour_rows += [[r['iteration'], tr_msg('price curves'), round(r['economics']['energy_basis'].get('curve_hours', 0.0))] for r in with_energy]
    report.section(tr_msg('Hours per marginal plant'), table([tr_msg('Iteration'), tr_msg('Marginal'), tr_msg('Hours [h/a]')], hour_rows) +
                   '<p class="note">{}</p>'.format(esc(tr_msg('A plant running above {:g} % of its peak heat flow; steps without one are priced with the curves.').format(
                       first.get('threshold_pct', 5.0)))), 3)


def stageSections(report, rows, parms):
    """the stages of a network built in stages (network-stages D6): versions and years, the NPV per stage and iteration"""
    staged = [r for r in rows if r.get('stages')]
    if not staged:
        return
    first = staged[0]['stages']
    inputs = parms.get('stages') or []
    stage_rows = [[k, s['version'], (inputs[k - 1]['version'] if k - 1 < len(inputs) else ''), s['start']] for k, s in enumerate(first, 1)]
    report.section(tr_msg('Stages'), table([tr_msg('Stage'), tr_msg('Version of the run'), tr_msg('Stage version'), tr_msg('Start year [a]')], stage_rows) +
                   '<p class="note">{}</p>'.format(esc(tr_msg('The pipes of a line are sized for all stages it exists in; the operating costs of a '
                                                              'stage count in its years, an investment from the start of the stage it first appears in.'))), 3)
    npv_rows = [[r['iteration']] + [round(s['npv']) for s in r['stages']] + [round(r['npv'])] for r in staged]
    report.section(tr_msg('Net present value per stage [€]'), table(
        [tr_msg('Iteration')] + [tr_msg('Stage {}').format(k) for k in range(1, len(first) + 1)] + [tr_msg('Total')], npv_rows), 3)


def npvCalculation(report, rows):
    """the equations of the NPV and, per iteration, the terms with their numbers"""
    body = ''.join(('<p>{}</p>'.format(esc(tr_msg(text))) if text else '') + (eq(formula) if formula else '') for text, formula in EQUATIONS)
    body += table([tr_msg('Symbol'), tr_msg('Meaning')], [[Html(symbol), tr_msg(text)] for symbol, text in SYMBOLS])
    report.section(tr_msg('Net present value: equations'), body, 3)
    saved = [r for r in rows if r.get('economics')]
    if not saved:
        report.section(tr_msg('Net present value: calculation per iteration'), '<p class="note">{}</p>'.format(
            esc(tr_msg('The terms of the net present value were not saved (run before this report showed them).'))), 3)
        return
    first = saved[0]['economics']
    f = first['factors']
    factor_rows = [[Html(PV.format(g=g)), tr_msg(label), factorText(f[key])] for g, label, key in (
        ('el', 'electricity (pump energy)', 'electricity'), ('heat', 'heat (heat losses)', 'heat'), ('cold', 'cold (cold losses)', 'cold'),
        ('maint', 'maintenance', 'maintenance'))]
    factor_rows.append([Html('((1+<i>i</i>)<sup><i>N</i></sup> − 1) / (<i>i</i> · (1+<i>i</i>)<sup><i>N</i></sup>)'), tr_msg('comfort violations'), factorText(f['penalties'])])
    report.section(tr_msg('Present value factors of the scenario'), '<p>i = {:g} %/a, N = {} a, {}</p>'.format(
        first['interest_pct'], first['period_a'], esc(tr_msg('residual value counted') if first.get('residual_value') else tr_msg('no residual value'))) +
        table([tr_msg('Factor'), tr_msg('Cost group'), tr_msg('Value')], factor_rows, numeric={2}), 3)

    def kSum(econ, kind):
        return sum(t['base'] for t in econ['terms'] if t['group'] == 'investment' and t.get('kind') == kind)

    def base(econ, group):
        return next((t['base'] for t in econ['terms'] if t['group'] == group), 0.0)

    amounts = (
        ('Pump energy [kWh/a]', lambda e: e['energy'].get('pump_kwh', 0.0)), ('C_pump,0 [€/a]', lambda e: base(e, 'pump_energy')),
        ('Heat losses [kWh/a]', lambda e: e['energy'].get('heat_kwh', 0.0)), ('C_heat,0 [€/a]', lambda e: base(e, 'heat_losses')),
        ('Cold losses [kWh/a]', lambda e: e['energy'].get('cold_kwh', 0.0)), ('C_cold,0 [€/a]', lambda e: base(e, 'cold_losses')),
        ('K pipes [€]', lambda e: kSum(e, 'pipe')), ('K trench [€]', lambda e: kSum(e, 'trench')), ('K pumps [€]', lambda e: kSum(e, 'pumps')),
        ('Peak pump power [kW]', lambda e: next((t.get('power_kw', 0.0) for t in e['terms'] if t.get('kind') == 'pumps'), 0.0)),
        ('P comfort violations [€/a]', lambda e: e.get('yearly_penalty', 0.0)))
    amount_rows = [[tr_msg(label)] + [round(fn(r['economics'])) for r in saved] for label, fn in amounts]
    flow_rows = []
    for r in saved:
        e = r['economics'].get('energy') or {}
        if 'heat_out_kwh' not in e:
            continue
        for mode, label in (('heat', 'heating'), ('cold', 'cooling')):
            flow_rows.append([r['iteration'], tr_msg(label), round(e[mode + '_out_kwh']), round(e[mode + '_out_eur']),
                              round(e[mode + '_in_kwh']), round(e[mode + '_in_eur']), round(e[mode + '_kwh']), round(e[mode + '_out_eur'] + e[mode + '_in_eur'])])
    if flow_rows:
        report.section(tr_msg('Heat flows of the pipes per mode'), table(
            [tr_msg('Iteration'), tr_msg('Mode'), tr_msg('Given off [kWh/a]'), tr_msg('Given off [€/a]'), tr_msg('Taken up [kWh/a]'),
             tr_msg('Taken up [€/a]'), tr_msg('Net [kWh/a]'), tr_msg('Net [€/a]')], flow_rows) +
            '<p class="note">{}</p>'.format(esc(tr_msg('Per pipe sequence and step: given off Q > 0, taken up Q < 0. Net heating = C_heat,0, '
                                                       'net cooling = C_cold,0; a negative value is a saving.'))), 3)
    mode_rows = []
    for r in saved:
        for pair, m in sorted((r['economics'].get('modes') or {}).items()):
            source = tr_msg('plant heat flows') if m.get('source') == 'plants' else tr_msg('plant template (no results mdot_ep)')
            mode_rows.append([r['iteration'], pair, source, tr_msg(m.get('template') or ''), '' if m.get('heat_h') is None else round(m['heat_h']),
                              '' if m.get('cold_h') is None else round(m['cold_h']), '' if m.get('q_max') is None else round(m['q_max'] / 1000, 1),
                              '' if m.get('q_min') is None else round(m['q_min'] / 1000, 1), m.get('deadband_pct')])
    if mode_rows:
        report.section(tr_msg('Heating and cooling per pair'), table(
            [tr_msg('Iteration'), tr_msg('Pair'), tr_msg('Mode from'), tr_msg('Template mode'), tr_msg('Heating [h/a]'), tr_msg('Cooling [h/a]'),
             tr_msg('Max. heat into the network [kW]'), tr_msg('Min. heat into the network [kW]'), tr_msg('Deadband [%]')], mode_rows) +
            '<p class="note">{}</p>'.format(esc(tr_msg('Hours weighted to a year; losses of the pipes of a pair are priced with the heat price '
                                                       'in its heating hours and with the cold price in its cooling hours.'))), 3)
    report.section(tr_msg('Amounts of year 0 per iteration'), table([tr_msg('Amount')] + [tr_msg('Iteration {}').format(r['iteration']) for r in saved], amount_rows), 3)
    energySections(report, saved)

    report.section(tr_msg('Net present value: calculation per iteration'), '<p class="note">{}</p>'.format(esc(tr_msg(
        'Each term is base × factor; the base is K, K · m, C_0 or P of the equations, the factor the discounted price levels. '
        'Saved at the run, with the scenario of the run.'))), 3)
    order = {g: n for n, g in enumerate(NPV_GROUPS)}
    for row in saved:
        econ = row['economics']
        terms = sorted(econ['terms'], key=lambda t: order.get(t['group'], 99))
        table_rows: list = []
        for group in NPV_GROUPS:
            group_terms = [t for t in terms if t['group'] == group]
            if group == 'penalties':
                table_rows.append(TotalRow([groupLabel(group), '', tr_msg('P [€/a]'), round(econ.get('yearly_penalty', 0.0)),
                                            factorText(econ['factors']['penalties']), round(econ.get('penalties', 0.0))]))
                continue
            for t in group_terms:
                table_rows.append([groupLabel(group), termItem(t), termDetail(t, dict(econ.get('energy') or {}, energy_basis=econ.get('energy_basis'))), round(t['base']), factorText(t['factor']), round(t['value'])])
            if len(group_terms) > 1:
                table_rows.append(TotalRow([groupLabel(group), tr_msg('Total'), '', '', '', round(sum(t['value'] for t in group_terms))]))
            elif group_terms:
                table_rows[-1] = TotalRow(table_rows[-1])
        total = sum(t['value'] for t in terms) + econ.get('penalties', 0.0)
        table_rows.append(TotalRow([tr_msg('Net present value'), '', '', '', '', round(total)]))
        body = table([tr_msg('Part'), tr_msg('Item'), tr_msg('Detail'), tr_msg('Base [€]'), tr_msg('Factor'), tr_msg('Value [€]')], table_rows, numeric={3, 4, 5})
        if abs(total - row['npv']) > max(1.0, 1e-6 * abs(row['npv'])):
            body += '<p class="note">{}</p>'.format(esc(tr_msg('The sum of the terms differs from the net present value of the iteration ({}).').format(money(row['npv']))))
        report.section(tr_msg('Iteration {}').format(row['iteration']) + ' – ' + money(row['npv']), body, 4)


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
