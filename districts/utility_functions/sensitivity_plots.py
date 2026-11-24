# coding=utf-8
"""Plots of the sensitivity analysis (OpenSpec change cost-sensitivity D7): parallel coordinates and the tornado chart
(rank correlations for combinations and samples), drawn on matplotlib axes for the dialog and the report."""
from matplotlib.lines import Line2D
from matplotlib.patches import Rectangle
from matplotlib.ticker import FuncFormatter

from .sensitivity import correlations, resultNpv, tornado
from .translations import tr_msg

ENERGY_PARTS = ('pump_energy', 'heat_losses', 'cold_losses', 'plant_energy', 'customer_energy', 'maintenance')


def money(value):
    return '{:,.0f}'.format(value).replace(',', "'")


def resultAxes(variant):
    """the result axes of a variant: NPV, investment (with replacements and residual value), operating costs, changed lines"""
    result = variant.get('result') or {}
    split = result.get('split_after') or result.get('split') or {}
    return {'npv': resultNpv(variant), 'investment': split.get('investment', 0.0) + split.get('residual', 0.0),
            'operating': sum(split.get(g, 0.0) for g in ENERGY_PARTS), 'changed': float(result.get('n_changed', len(result.get('changes', []))))}


RESULT_LABELS = (('npv', 'NPV [€]'), ('investment', 'Investment [€]'), ('operating', 'Operating costs [€]'), ('changed', 'Changed lines'))


def parallelData(analysis):
    """the axes of the parallel coordinates: (column names, the ranges, {variant name: scaled values 0..1}) of the
    variants with a result"""
    done = [v for v in analysis['variants'] if v.get('result')]
    labels = analysis.get('labels') or {}
    keys = list(analysis['bounds'])
    columns = [(labels.get(k, k), [float(v['values'][k]) for v in done]) for k in keys]
    columns += [(tr_msg(label), [resultAxes(v)[key] for v in done]) for key, label in RESULT_LABELS]
    ranges = [(min(values), max(values)) for _, values in columns]

    def scaled(value, bounds):
        low, high = bounds
        return 0.5 if high == low else (value - low) / (high - low)
    scaled_values = {v['name']: [scaled(values[k], bounds) for (_, values), bounds in zip(columns, ranges)] for k, v in enumerate(done)}
    return [name for name, _ in columns], ranges, scaled_values


def passesBrushes(values, brushes):
    """a variant's scaled values lie within every brush {column: (low, high)}"""
    return all(low <= values[column] <= high for column, (low, high) in brushes.items())


def parallelCoordinates(ax, analysis, selected=None, brushes=None):
    """a line per variant over the varied parameters and the results, each axis scaled to its range; the base black.
    selected: a variant drawn on top in red; brushes {column: (low, high)} of the scaled values: the variants outside
    drawn light. Returns {variant name: Line2D}."""
    names, ranges, scaled_values = parallelData(analysis)
    brushes = brushes or {}
    npv_column = len(analysis['bounds'])
    cmap = colormap('viridis')
    x = list(range(len(names)))
    lines = {}
    for name, y in scaled_values.items():
        inside = passesBrushes(y, brushes)
        if name == selected:
            style = {'color': '#e31a1c', 'linewidth': 3.0, 'alpha': 1.0, 'zorder': 6}
        elif not inside:
            style = {'color': '#cccccc', 'linewidth': 0.8, 'alpha': 0.35, 'zorder': 1}
        elif name == 'base':
            style = {'color': 'k', 'linewidth': 2.2, 'alpha': 1.0, 'zorder': 5}
        else:
            style = {'color': cmap(y[npv_column]), 'linewidth': 1.0, 'alpha': 0.85, 'zorder': 3}
        lines[name] = ax.plot(x, y, **style)[0]
    for column, (low, high) in brushes.items():
        ax.add_patch(Rectangle((column - 0.12, low), 0.24, high - low, facecolor='#2171b5', alpha=0.18, edgecolor='#2171b5', zorder=7))
    for xi, (name, (lo, hi)) in enumerate(zip(names, ranges)):
        ax.axvline(xi, color='#888888', linewidth=0.8)
        ax.text(xi, -0.06, number(lo), ha='center', va='top', fontsize=6)
        ax.text(xi, 1.06, number(hi), ha='center', va='bottom', fontsize=6)
    ax.set_xticks(x)
    ax.set_xticklabels(names, rotation=30, ha='right', fontsize=7)
    ax.set_yticks([])
    ax.set_ylim(-0.15, 1.15)
    ax.set_xlim(-0.3, len(names) - 0.7)
    for side in ('top', 'right', 'left'):
        ax.spines[side].set_visible(False)
    # a legend of its own entries: a selected or filtered base carries none
    entries = [Line2D([], [], color='k', linewidth=2.2, label=tr_msg('base'))] if 'base' in scaled_values else []
    if selected in scaled_values:
        entries.append(Line2D([], [], color='#e31a1c', linewidth=3.0, label=selected))
    if entries:
        ax.legend(handles=entries, fontsize=7, loc='upper left', bbox_to_anchor=(1.0, 1.0))
    return lines


def colormap(name):
    # matplotlib.cm.get_cmap is gone from 3.9; colormaps exists from 3.5 (QGIS 3.44 and 4.2 ship newer)
    from matplotlib import colormaps
    return colormaps[name]


def number(value):
    if abs(value) >= 1000:
        return money(value)
    return '{:.3g}'.format(value)


def tornadoChart(ax, analysis):
    """NPV at − and + per parameter against the base (one at a time), else the rank correlations with the NPV"""
    labels = analysis.get('labels') or {}
    rows = tornado(analysis)
    if rows:
        base = next((resultNpv(v) for v in analysis['variants'] if v['name'] == 'base' and v.get('result')), None)
        rows = list(reversed(rows))
        for y, (key, low, high) in enumerate(rows):
            ax.barh(y, low - base, left=base, color='#2171b5', label=tr_msg('− value') if y == 0 else None)
            ax.barh(y, high - base, left=base, color='#d7301f', label=tr_msg('+ value') if y == 0 else None)
        ax.axvline(base, color='k', linewidth=1.0)
        ax.set_yticks(range(len(rows)))
        ax.set_yticklabels([labels.get(key, key) for key, _, _ in rows], fontsize=7)
        ax.set_xlabel(tr_msg('NPV [€]'))
        ax.xaxis.set_major_formatter(FuncFormatter(lambda value, _: money(value)))
        ax.legend(fontsize=7, loc='lower right')
        return
    ranked = list(reversed(correlations(analysis)))
    ax.barh(range(len(ranked)), [rho for _, rho in ranked], color=['#d7301f' if rho > 0 else '#2171b5' for _, rho in ranked])
    ax.set_yticks(range(len(ranked)))
    ax.set_yticklabels([labels.get(key, key) for key, _ in ranked], fontsize=7)
    ax.set_xlim(-1, 1)
    ax.axvline(0, color='k', linewidth=1.0)
    ax.set_xlabel(tr_msg('rank correlation with the NPV'))
