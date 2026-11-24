# coding=utf-8
"""Sensitivity analysis in the cost optimization dialog (OpenSpec change cost-sensitivity D1, D3–D7): the section with
the parameter table, the results tab and the run of the variants (estimate in worker tasks, or one cost optimization
per variant, one after another)."""
import datetime
import glob
import os
import traceback

import numpy as np
from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg
from matplotlib.figure import Figure
from matplotlib.patches import Rectangle
from qgis.PyQt.QtCore import QObject, QSize, Qt, pyqtSlot
from qgis.PyQt.QtGui import QColor
from qgis.PyQt.QtWidgets import (
    QAbstractItemView, QComboBox, QDialog, QHBoxLayout, QHeaderView, QLabel, QMessageBox, QPushButton, QSpinBox, QSplitter, QTableWidget,
    QTableWidgetItem, QVBoxLayout, QWidget,
)
from qgis.core import QgsMessageLog

from .representative_periods import startTask
from .utility_functions.compat import MessageCritical
from .utility_functions.cost_optimization_layers import iterationPath, loadCostIterations
from .utility_functions.economic_data import loadScenario
from .utility_functions.iteration_report import loadRunParameters
from .utility_functions.sensitivity import (
    CONFIRM_SECONDS, DESIGN_LABELS, DESIGNS, MODE_LABELS, ESTIMATE_SECONDS_PER_STAGE, MODES, designVariants, estimateBasis, estimateVariant, flips, loadAnalysis,
    parameterRows, saveAnalysis, variantCount, variantParameters, variedBounds,
)
from .utility_functions.sensitivity_plots import money, parallelCoordinates, parallelData, passesBrushes, resultAxes, tornadoChart
from .utility_functions.translations import tr_msg

DEFAULT_RELATIVE = 20.0


class _Canvas(FigureCanvasQTAgg):
    # a fixed hint: matplotlib's is the current size, which only grows in the dialog's scroll area
    def sizeHint(self):
        return QSize(600, 300)

    def minimumSizeHint(self):
        return QSize(200, 220)


class SensitivityWidget(QWidget):
    """the section 'Sensitivity': parameter table, design, mode, number of variants and duration, start"""

    def __init__(self, dlg):
        super().__init__()
        self.dlg = dlg
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        info = QLabel(tr_msg('How the NPV and the pipes of the last run depend on uncertain inputs. Mark the parameters to vary and give their − and + '
                             'values (absolute, or relative in % of the base). The scenario stays unchanged.'))
        info.setWordWrap(True)
        layout.addWidget(info)
        self.table = QTableWidget(0, 7)
        self.table.setHorizontalHeaderLabels([tr_msg('Vary'), tr_msg('Parameter'), tr_msg('Base'), tr_msg('Unit'), tr_msg('Mode'), '−', '+'])
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Interactive)
        self.table.verticalHeader().setVisible(False)
        self.table.setMinimumHeight(180)
        layout.addWidget(self.table)
        row = QHBoxLayout()
        self.combo_design = QComboBox()
        for design in DESIGNS:
            self.combo_design.addItem(tr_msg(DESIGN_LABELS[design]), design)
        self.spin_size = QSpinBox()
        self.spin_size.setRange(2, 500)
        self.spin_size.setValue(20)
        self.spin_size.setToolTip(tr_msg('Number of variants of the sample (the base is added)'))
        self.spin_seed = QSpinBox()
        self.spin_seed.setRange(0, 999999)
        self.spin_seed.setToolTip(tr_msg('Seed of the sample: the same seed gives the same variants'))
        self.combo_mode = QComboBox()
        for mode in MODES:
            self.combo_mode.addItem(tr_msg(MODE_LABELS[mode]), mode)
        self.combo_mode.setToolTip(tr_msg('Estimate: the best iteration of the last run valued with each variant and one step of the cost model, '
                                          'seconds per variant. Full: a cost optimization per variant into new child versions, as long as a run each.'))
        for widget in (QLabel(tr_msg('Design')), self.combo_design, QLabel(tr_msg('Sample size')), self.spin_size, QLabel(tr_msg('Seed')),
                       self.spin_seed, QLabel(tr_msg('Each variant')), self.combo_mode):
            row.addWidget(widget)
        row.addStretch()
        layout.addLayout(row)
        row = QHBoxLayout()
        self.label_count = QLabel()
        self.btn_reload = QPushButton(tr_msg('Parameters from the scenario'))
        self.btn_reload.setToolTip(tr_msg('The base values from the chosen scenario and the settings above'))
        self.btn_start = QPushButton(tr_msg('Start sensitivity analysis'))
        row.addWidget(self.label_count, 1)
        row.addWidget(self.btn_reload)
        row.addWidget(self.btn_start)
        layout.addLayout(row)
        self.btn_reload.clicked.connect(self.fill)
        self.btn_start.clicked.connect(self.startAnalysis)
        for signal in (self.combo_design.currentIndexChanged, self.spin_size.valueChanged, self.combo_mode.currentIndexChanged):
            signal.connect(self.updateCount)
        self.table.itemChanged.connect(lambda _: self.updateCount())
        self.run = None
        self.fill()

    def fill(self):
        """the rows from the chosen scenario and the dialog's settings; earlier choices kept by key"""
        previous = {r['key']: r for r in self.rows(all_rows=True)}
        try:
            scenario = loadScenario(self.dlg.main.cur, self.dlg.combo_scenario.currentData()) if self.dlg.combo_scenario.currentData() is not None else None
        except Exception:
            QgsMessageLog.logMessage(traceback.format_exc(), 'Districts', MessageCritical)
            scenario = None
        rows = parameterRows(scenario, self.dlg.parameters()) if scenario else []
        self.table.blockSignals(True)
        self.table.setRowCount(0)
        for r in rows:
            k = self.table.rowCount()
            self.table.insertRow(k)
            old = previous.get(r['key'], {})
            check = QTableWidgetItem()
            check.setFlags(check.flags() & ~_editable())
            check.setCheckState(_checked(old.get('varied', False)))
            check.setData(Qt.ItemDataRole.UserRole, r['key'])
            self.table.setItem(k, 0, check)
            for col, value in ((1, r['label']), (2, '{:g}'.format(r['base'])), (3, r['unit'])):
                item = QTableWidgetItem(value)
                item.setFlags(item.flags() & ~_editable())
                self.table.setItem(k, col, item)
            mode = QComboBox()
            mode.addItem(tr_msg('relative [%]'), 'rel')
            mode.addItem(tr_msg('absolute'), 'abs')
            mode.setCurrentIndex(1 if old.get('mode') == 'abs' else 0)
            self.table.setCellWidget(k, 4, mode)
            self.table.setItem(k, 5, QTableWidgetItem('{:g}'.format(old.get('minus', -DEFAULT_RELATIVE))))
            self.table.setItem(k, 6, QTableWidgetItem('{:g}'.format(old.get('plus', DEFAULT_RELATIVE))))
        self.table.blockSignals(False)
        self.table.resizeColumnsToContents()
        self.updateCount()

    def rows(self, all_rows=False):
        """[{'key', 'label', 'base', 'mode', 'minus', 'plus', 'varied'}] of the table (the varied ones unless all_rows)"""
        result = []
        for k in range(self.table.rowCount()):
            check = self.table.item(k, 0)
            try:
                minus, plus = float(self.table.item(k, 5).text().replace(',', '.')), float(self.table.item(k, 6).text().replace(',', '.'))
            except (ValueError, AttributeError):
                minus, plus = None, None
            row = {'key': check.data(Qt.ItemDataRole.UserRole), 'label': self.table.item(k, 1).text(), 'base': float(self.table.item(k, 2).text()),
                   'mode': self.table.cellWidget(k, 4).currentData(), 'minus': minus, 'plus': plus, 'varied': check.checkState() == _checked(True)}
            if all_rows or row['varied']:
                result.append(row)
        return result

    def design(self):
        return self.combo_design.currentData()

    def mode(self):
        return self.combo_mode.currentData()

    def stageCount(self):
        return max(1, len(self.dlg.stage_table.stages()))

    def estimatedSeconds(self, n):
        if self.mode() == 'estimate':
            return n * ESTIMATE_SECONDS_PER_STAGE * self.stageCount()
        return n * lastRunSeconds(self.dlg.main.config)

    def updateCount(self):
        varied = self.rows()
        self.spin_size.setEnabled(self.design() == 'sample')
        self.spin_seed.setEnabled(self.design() == 'sample')
        if not varied:
            self.label_count.setText(tr_msg('No parameter marked to vary.'))
            return
        n = variantCount(len(varied), self.design(), self.spin_size.value())
        seconds = self.estimatedSeconds(n)
        self.label_count.setText(tr_msg('{} variants, about {}').format(n, durationText(seconds)) if seconds else tr_msg('{} variants').format(n))

    def startAnalysis(self):
        if self.dlg.process_running:
            return
        varied = self.rows()
        if not varied:
            self.dlg.refuse([tr_msg('Mark at least one parameter to vary.')])
            return
        if any(r['minus'] is None or r['plus'] is None for r in varied):
            self.dlg.refuse([tr_msg('Give a number as − and + value of every varied parameter.')])
            return
        bounds = variedBounds(varied)
        variants = designVariants(bounds, self.design(), self.spin_size.value(), self.spin_seed.value())
        seconds = self.estimatedSeconds(len(variants))
        if seconds > CONFIRM_SECONDS and QMessageBox.question(self, tr_msg('Sensitivity analysis'), tr_msg(
                '{} variants take about {}. Start?').format(len(variants), durationText(seconds))) != QMessageBox.StandardButton.Yes:
            return
        analysis = {'design': self.design(), 'mode': self.mode(), 'seed': self.spin_seed.value(), 'size': self.spin_size.value(),
                    'table': self.rows(all_rows=True), 'bounds': {k: list(v) for k, v in bounds.items()},
                    'labels': {r['key']: r['label'] for r in varied}, 'variants': variants,
                    'started': datetime.datetime.now().isoformat(timespec='seconds'), 'version': self.dlg.main.config['versionName']}
        self.run = SensitivityRun(self.dlg, analysis, self.dlg.parameters())
        self.run.start()


class ParallelPlot(QWidget):
    """the interactive parallel coordinates: a click on a line selects its variant, a drag along an axis draws a filter
    rectangle (the variants outside are drawn light), a double click on an axis removes its rectangle. state =
    {'selected': name, 'brushes': {column: (low, high)}} is the tab's."""

    def __init__(self, state, on_select, on_filter, size=(9, 3.6)):
        super().__init__()
        self.state, self.on_select, self.on_filter = state, on_select, on_filter
        self.analysis = None
        self.figure = Figure(figsize=size)
        self.canvas = _Canvas(self.figure)
        self.canvas.setToolTip(tr_msg('Click a line to select its variant; drag along an axis to filter; double-click an axis to remove its filter'))
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(self.canvas)
        self.ax = None
        self.press = None
        self.drag = None
        self.canvas.mpl_connect('button_press_event', self.onPress)
        self.canvas.mpl_connect('motion_notify_event', self.onMotion)
        self.canvas.mpl_connect('button_release_event', self.onRelease)

    def setAnalysis(self, analysis):
        self.analysis = analysis
        self.redraw()

    def redraw(self):
        self.figure.clear()
        self.ax = None
        if self.analysis and sum(1 for v in self.analysis['variants'] if v.get('result')) > 1:
            self.ax = self.figure.add_subplot(111)
            parallelCoordinates(self.ax, self.analysis, self.state.get('selected'), self.state['brushes'])
            # fixed margins: tight_layout gives up (with a warning) when the canvas is low for the rotated axis names
            self.figure.subplots_adjust(left=0.04, right=0.9, top=0.9, bottom=0.3)
        self.canvas.draw()

    def column(self, x):
        names, _, _ = parallelData(self.analysis)
        return min(max(int(round(x)), 0), len(names) - 1)

    def onPress(self, event):
        if self.ax is None or event.inaxes is not self.ax or event.button != 1 or event.xdata is None:
            return
        column = self.column(event.xdata)
        if event.dblclick:
            self.press = None
            if column in self.state['brushes']:
                del self.state['brushes'][column]
                self.redraw()
                self.on_filter()
            return
        self.press = (event.xdata, event.ydata, column)

    def onMotion(self, event):
        if self.press is None or event.inaxes is not self.ax or event.ydata is None:
            return
        _, y0, column = self.press
        if abs(event.ydata - y0) < 0.02:
            return
        if self.drag is None:
            self.drag = Rectangle((column - 0.12, y0), 0.24, 0, facecolor='#2171b5', alpha=0.25, edgecolor='#2171b5', zorder=8)
            self.ax.add_patch(self.drag)
        self.drag.set_y(min(y0, event.ydata))
        self.drag.set_height(abs(event.ydata - y0))
        self.canvas.draw_idle()

    def onRelease(self, event):
        if self.press is None:
            return
        x0, y0, column = self.press
        self.press = None
        if self.drag is not None:
            low, high = self.drag.get_y(), self.drag.get_y() + self.drag.get_height()
            self.drag = None
            self.state['brushes'][column] = (max(0.0, low), min(1.0, high))
            self.redraw()
            self.on_filter()
            return
        name = self.nearest(x0, y0)
        if name is not None:
            self.on_select(name)

    def nearest(self, x, y):
        """the variant whose line passes closest to (x, y), within a twentieth of the height; light ones count too"""
        _, _, scaled = parallelData(self.analysis)
        best, distance = None, 0.05
        for name, values in scaled.items():
            d = abs(float(np.interp(x, range(len(values)), values)) - y)
            if d < distance:
                best, distance = name, d
        return best

    def passing(self):
        _, _, scaled = parallelData(self.analysis)
        return [name for name, values in scaled.items() if passesBrushes(values, self.state['brushes'])]


class SensitivityResults(QWidget):
    """the tab 'Sensitivity': the interactive parallel coordinates and the tornado chart, the variants and the lines
    that flip one above the other, the robustness on the map"""

    def __init__(self, dlg):
        super().__init__()
        self.dlg = dlg
        self.analysis = None
        self.state: dict = {'selected': None, 'brushes': {}}
        layout = QVBoxLayout(self)
        splitter = QSplitter(Qt.Orientation.Vertical)
        splitter.setChildrenCollapsible(False)
        plots = QWidget()
        row = QHBoxLayout(plots)
        row.setContentsMargins(0, 0, 0, 0)
        self.parallel = ParallelPlot(self.state, self.select, self.filtered)
        self.tornado_figure = Figure(figsize=(4, 3.6))
        self.tornado_canvas = _Canvas(self.tornado_figure)
        row.addWidget(Detachable(tr_msg('Parallel coordinates'), self.parallel), 3)
        row.addWidget(Detachable(tr_msg('Tornado chart'), self.tornado_canvas), 2)
        splitter.addWidget(plots)
        self.table_variants = _table()
        self.table_variants.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.table_variants.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)
        self.table_variants.itemSelectionChanged.connect(self.onTableSelection)
        splitter.addWidget(_titled(tr_msg('Variants: the varied values and the results; select a row to highlight its line'), self.table_variants)[0])
        self.table_flips = _table()
        box, self.label_flips = _titled('', self.table_flips)
        splitter.addWidget(box)
        # minimum heights: the tab sits in the results section of a scroll area, which grows instead of squeezing them
        plots.setMinimumHeight(280)
        self.table_variants.setMinimumHeight(180)
        self.table_flips.setMinimumHeight(180)
        splitter.setStretchFactor(0, 3)
        splitter.setStretchFactor(1, 2)
        splitter.setStretchFactor(2, 2)
        layout.addWidget(splitter, 1)
        row = QHBoxLayout()
        self.label = QLabel()
        # wrapped: an unwrapped status line made the page, and with it every tab, wider than the dialog
        self.label.setWordWrap(True)
        self.label_filter = QLabel()
        self.btn_reset = QPushButton(tr_msg('Reset the filter'))
        self.btn_reset.clicked.connect(self.resetFilter)
        self.btn_map = QPushButton(tr_msg('Show the robustness on the map'))
        self.btn_map.clicked.connect(self.showMap)
        row.addWidget(self.label, 1)
        row.addWidget(self.label_filter)
        for button in (self.btn_reset, self.btn_map):
            row.addWidget(button)
        layout.addLayout(row)
        self.show(loadSaved(dlg.main.config))

    def show(self, analysis):
        self.analysis = analysis
        self.state['selected'] = None
        self.state['brushes'].clear()
        self.tornado_figure.clear()
        self.table_variants.setRowCount(0)
        self.table_flips.setRowCount(0)
        done = [v for v in (analysis or {}).get('variants', []) if v.get('result')]
        for button in (self.btn_map, self.btn_reset):
            button.setEnabled(bool(done))
        self.parallel.setAnalysis(analysis if done else None)
        if not done:
            self.label.setText(tr_msg('No sensitivity analysis in this version yet.'))
            self.label_flips.setText('')
            self.label_filter.setText('')
            self.tornado_canvas.draw()
            return
        self.label.setText(tr_msg('{} of {} variants, {} ({}), started {}').format(
            len(done), len(analysis['variants']), tr_msg(DESIGN_LABELS.get(analysis['design'], analysis['design'])),
            tr_msg(MODE_LABELS.get(analysis['mode'], analysis['mode'])), analysis.get('started', '')))
        if len(done) > 1:
            tornadoChart(self.tornado_figure.add_subplot(111), analysis)
            self.tornado_figure.subplots_adjust(left=0.38, right=0.97, top=0.95, bottom=0.2)
        self.tornado_canvas.draw()
        fillVariantTable(self.table_variants, analysis)
        fillFlipTable(self.table_flips, analysis, self.dlg.main.cur)
        from .utility_functions.iteration_report import flipNote
        from .utility_functions.sensitivity import baseStep, baseStepText
        try:
            step = baseStepText(baseStep(analysis, loadCostIterations(dict(self.dlg.main.config, versionName=analysis.get('version') or self.dlg.main.config['versionName']))))
        except Exception:
            QgsMessageLog.logMessage(traceback.format_exc(), 'Districts', MessageCritical)
            step = ''
        self.label_flips.setText(tr_msg('Lines where a variant ends with other pipes than the base variant, one column per such variant (the rows '
                                        'of the selected variant highlighted).') + ' ' + flipNote(analysis) + (' ' + step if step else ''))
        self.filtered()

    # ---------------------------------------------------------------- selection and filter
    def select(self, name):
        """a variant selected in a plot or the table: its line red, its table row selected, its flips highlighted"""
        self.state['selected'] = name
        self.table_variants.blockSignals(True)
        self.table_variants.clearSelection()
        for k in range(self.table_variants.rowCount()):
            if self.table_variants.item(k, 0).text() == name:
                self.table_variants.selectRow(k)
                self.table_variants.scrollToItem(self.table_variants.item(k, 0))
        self.table_variants.blockSignals(False)
        for k in range(self.table_flips.rowCount()):
            names = self.table_flips.item(k, 0).data(Qt.ItemDataRole.UserRole) or []
            for col in range(self.table_flips.columnCount()):
                self.table_flips.item(k, col).setBackground(QColor('#fde0dd') if name in names else QColor(0, 0, 0, 0))
        self.parallel.redraw()

    def onTableSelection(self):
        rows = {index.row() for index in self.table_variants.selectedIndexes()}
        if rows:
            self.select(self.table_variants.item(min(rows), 0).text())

    def filtered(self):
        """the variants inside the filter rectangles: the others greyed in the table"""
        if not self.parallel.analysis:
            return
        inside = set(self.parallel.passing())
        for k in range(self.table_variants.rowCount()):
            color = QColor('#000000') if self.table_variants.item(k, 0).text() in inside else QColor('#aaaaaa')
            for col in range(self.table_variants.columnCount()):
                self.table_variants.item(k, col).setForeground(color)
        total = self.table_variants.rowCount()
        self.label_filter.setText(tr_msg('{} of {} variants in the filter').format(len(inside), total) if self.state['brushes'] else '')

    def resetFilter(self):
        self.state['brushes'].clear()
        self.parallel.redraw()
        self.filtered()

    def showMap(self):
        from qgis.utils import iface
        from .utility_functions.cost_optimization_layers import showRobustness
        try:
            showRobustness(self.dlg.main.cur, self.analysis)
            iface.mapCanvas().refresh()
        except Exception:
            QgsMessageLog.logMessage(traceback.format_exc(), 'Districts', MessageCritical)
            self.dlg.refuse([tr_msg('The robustness could not be shown: ') + traceback.format_exc().splitlines()[-1]])


class SensitivityRun(QObject):
    """the variants one after another: estimate tasks, or one cost optimization each (design D4, D5)"""

    def __init__(self, dlg, analysis, parms):
        super().__init__()
        self.dlg, self.analysis, self.parms = dlg, analysis, parms
        self.main = dlg.main
        self.base_version = self.main.config['versionName']
        self.k = 0
        self.stop_requested = False
        self.active = False
        self.task = None

    @property
    def config(self):
        return self.main.config

    def start(self):
        self.dlg.process_running = True
        self.dlg.updateEnabled()
        self.dlg.box_results.setCollapsed(False)
        self.dlg.results_tabs.setCurrentWidget(self.dlg.sensitivity_page)
        self.dlg.log(tr_msg('Sensitivity analysis: {} variants').format(len(self.analysis['variants'])))
        self.active = True
        try:
            if self.analysis['mode'] == 'estimate':
                self.startEstimate()
            else:
                self.startFull()
        except Exception:
            self.onException()

    # ---------------------------------------------------------------- estimate
    def startEstimate(self):
        rows = loadCostIterations(self.config)
        run_parms = loadRunParameters(self.config, 'cost')
        basis = estimateBasis(self.main.cur, rows, dict(run_parms, version=run_parms.get('version') or self.base_version))
        self.analysis['basis'] = {k: basis[k] for k in ('iteration', 'npv', 'versions', 'stages', 'no_smaller')}
        self.basis = basis
        # the run's own settings: the variant changes only the varied values
        self.parms = dict(self.parms, **{k: run_parms[k] for k in ('scenario', 'pairs', 'submodel', 'price_kh', 'price_kwh', 'tolerance', 'unmet_tolerance',
                                                                  'dp_spez_max', 'v_max', 'mode_deadband_pct') if k in run_parms})
        # JSON gives the pairs as lists; the cost model keys by them
        self.parms['pairs'] = [tuple(pair) for pair in self.parms.get('pairs') or []]
        self.dlg.log(tr_msg('Basis: iteration {} of the last run, NPV {} €').format(basis['iteration'], money(basis['npv'])))
        from .utility_functions.files import loadModellingSettings
        from .utility_functions.network_modes import DEFAULT_DEADBAND_PCT
        self.settings = dict(loadModellingSettings(self.main.plugin_dir, self.config), mode_deadband_pct=self.parms.get('mode_deadband_pct', DEFAULT_DEADBAND_PCT))
        self.prices = os.path.join(self.config['pathProjects'] + self.config['projectName'], 'prices')
        config, parms, required = dict(self.config), dict(self.parms), self.dlg.requiredEntries()

        def prepare(cur):
            from .cost_optimization import penaltyValues
            from .utility_functions.network_stages import stageRoots
            values = {v: penaltyValues(cur, dict(config, versionName=v), required, parms['submodel'], parms['tolerance'], parms['unmet_tolerance'] / 100)
                      for v in basis['versions']}
            return values, (stageRoots(cur, basis['versions']) if basis['stages'] else None)
        startTask(self, self.config, prepare, self.onPrepared, self.onFailed)

    @pyqtSlot(object)
    def onPrepared(self, result):
        self.penalty_values, self.roots = result
        self.nextEstimate()

    def nextEstimate(self):
        if self.stop_requested or self.k >= len(self.analysis['variants']):
            return self.finish()
        variant = self.analysis['variants'][self.k]
        parms = variantParameters(self.parms, variant['values'])
        config, settings, prices, basis, values, roots = dict(self.config), self.settings, self.prices, self.basis, self.penalty_values, self.roots
        self.dlg.update_progress(100 * self.k / len(self.analysis['variants']))
        startTask(self, self.config, lambda cur: estimateVariant(cur, config, parms, settings, prices, basis, values, roots), self.onEstimated, self.onFailed)

    @pyqtSlot(object)
    def onEstimated(self, result):
        variant = self.analysis['variants'][self.k]
        variant['result'] = result
        self.dlg.log(tr_msg('  {}: NPV {} €, after the step {} €, {} lines changed').format(
            variant['name'], money(result['npv']), money(result['npv_after']), result['n_changed']))
        self.k += 1
        self.save()
        self.nextEstimate()

    # ---------------------------------------------------------------- full optimization per variant
    def startFull(self):
        from .cost_optimization import lineState
        stages = self.parms.get('stages') or []
        versions = [s['version'] for s in stages] if len(stages) > 1 else [self.base_version]
        self.analysis['basis'] = {'versions': versions, 'states': {v: {str(k): b for k, b in lineState(self.main.cur, v).items()} for v in versions}}
        self.nextFull()

    def nextFull(self):
        if self.stop_requested or self.k >= len(self.analysis['variants']):
            return self.finish()
        variant = self.analysis['variants'][self.k]
        parms = variantParameters(self.parms, variant['values'])
        parms['new_version'] = '{}_s{}'.format(self.base_version, self.k)
        variant['version'] = parms['new_version']
        self.dlg.log(tr_msg('Variant {} ({} of {}) into version {}').format(variant['name'], self.k + 1, len(self.analysis['variants']), parms['new_version']))
        self.save()
        self.dlg.update_progress(100 * self.k / len(self.analysis['variants']))
        if not self.dlg.start(parms, sensitivity=True):
            self.dlg.log(tr_msg('The variant could not be started; the analysis stops.'))
            self.finish()

    def onRunFinished(self):
        """called by the dialog when a variant's cost optimization has ended: its result, then the base version again"""
        variant = self.analysis['variants'][self.k]
        try:
            variant['result'] = fullResult(self.main.cur, self.config, variant['version'], self.analysis['basis'])
        except Exception:
            QgsMessageLog.logMessage(traceback.format_exc(), 'Districts', MessageCritical)
        self.k += 1
        self.save()
        self.loadBase(self.nextFull)

    def loadBase(self, then):
        """the base version loaded again (a run loads its new child version)"""
        if self.main.config['versionName'] == self.base_version:
            then()
            return
        from qgis.PyQt.QtCore import QThreadPool
        from .ida_ph import finishedLoadVersion, getVersionData, importData, loadVersionLayers
        from .utility_functions.utility import write_plugin_settings
        from .utility_functions.workers import WorkerLoadVersion
        self.main.config['versionName'] = self.base_version
        write_plugin_settings(self.main.config)
        importData(self.main.model, getVersionData(self.main.cur))
        loadVersionLayers(self.main.config, self.main.cur, self.main.plugin_dir)
        self.worker_version = WorkerLoadVersion(config=self.main.config, cur=self.main.cur, dlg=self.main.dlg)
        self.worker_version.signals.error.connect(lambda m: self.dlg.log(m))

        def loaded(_message):
            finishedLoadVersion(self.main)
            then()
        self.worker_version.signals.finished.connect(loaded)
        QThreadPool.globalInstance().start(self.worker_version)

    # ---------------------------------------------------------------- end
    def save(self):
        try:
            saveAnalysis(dict(self.main.config, versionName=self.base_version), self.analysis)
        except Exception:
            QgsMessageLog.logMessage(traceback.format_exc(), 'Districts', MessageCritical)

    def finish(self):
        self.active = False
        self.save()
        done = sum(1 for v in self.analysis['variants'] if v.get('result'))
        self.dlg.log(tr_msg('Sensitivity analysis: {} of {} variants done.').format(done, len(self.analysis['variants'])))
        self.dlg.update_progress(100)
        self.dlg.process_running = False
        self.dlg.updateEnabled()
        self.dlg.sensitivity_results.show(self.analysis)
        self.dlg.results_tabs.setCurrentWidget(self.dlg.sensitivity_page)

    def onFailed(self, message):
        self.dlg.log(tr_msg('Sensitivity analysis: error in variant {}: {}').format(self.k + 1, message))
        self.finish()

    def onException(self):
        QgsMessageLog.logMessage(traceback.format_exc(), 'Districts', MessageCritical)
        message = traceback.format_exc().splitlines()[-1]
        self.dlg.refuse([tr_msg('Sensitivity analysis: ') + message.split(': ', 1)[-1]])
        self.active = False
        self.dlg.process_running = False
        self.dlg.updateEnabled()


def fullResult(cur, config, version, basis):
    """the result of a variant's cost optimization: its best iteration's NPV and parts, the lines whose pipes differ from
    the base (per stage, the variant's stage versions in the order of the base's)"""
    from .utility_functions.hydraulic_balancing import getPipeBundles
    rows = loadCostIterations(dict(config, versionName=version))
    if not rows:
        return None
    best = min(rows, key=lambda r: r['npv'])
    states = best.get('stage_states') or {version: best.get('state') or {}}
    bundles = getPipeBundles(cur)

    def pipes(bid):
        return sorted((bundles.get(bid) or bundles.get(int(bid)) or {}).values()) if bid is not None else []
    changes = []
    for base_version, (_, state) in zip(basis['versions'], states.items()):
        base_state = basis['states'].get(base_version, {})
        for lid, bid in state.items():
            before = base_state.get(str(lid))
            if before is not None and before != bid:
                old, new = pipes(before), pipes(bid)
                changes.append({'version': base_version, 'line': int(lid), 'before': old, 'after': new, 'larger': None})
    return {'npv': best['npv'], 'split': best['split'], 'iteration': best['iteration'], 'changes': changes,
            'n_changed': len({(c['version'], c['line']) for c in changes})}


def fillVariantTable(table, analysis):
    keys = list(analysis['bounds'])
    labels = analysis.get('labels') or {}
    from .utility_functions.sensitivity import differences
    different = differences(analysis)
    headers = [tr_msg('Variant')] + [labels.get(k, k) for k in keys] + [tr_msg('NPV [€]'), tr_msg('NPV change by the step [€]'), tr_msg('Investment [€]'),
                                                                        tr_msg('Operating costs [€]'), tr_msg('Comfort penalties [€]'), tr_msg('Lines changed by the step'),
                                                                        tr_msg('Lines different from the base')]
    table.setColumnCount(len(headers))
    table.setHorizontalHeaderLabels(headers)
    for v in analysis['variants']:
        if not v.get('result'):
            continue
        axes = resultAxes(v)
        result = v['result']
        step = money(result['npv_after'] - result['npv']) if 'npv_after' in result else ''
        values = [v['name']] + ['{:.4g}'.format(v['values'][k]) for k in keys] + [money(axes['npv']), step, money(axes['investment']), money(axes['operating']),
                                                                                 money(axes['penalties']),
                                                                                 str(int(axes['changed'])), str(different.get(v['name'], 0))]
        k = table.rowCount()
        table.insertRow(k)
        for col, value in enumerate(values):
            table.setItem(k, col, QTableWidgetItem(value))
    table.resizeColumnsToContents()


def fillFlipTable(table, analysis, cur):
    """one row per line a variant changes: the pipe in the base and, per variant changing a line, its new pipe with ↑ or ↓"""
    from .utility_functions.hydraulic_balancing import getPipeCatalog
    from .utility_functions.sensitivity import flipColumns, pipeText
    catalog = getPipeCatalog(cur)
    columns = flipColumns(analysis)
    entries = sorted(flips(analysis).items())
    versions = {version for (version, _), _ in entries}
    headers = [tr_msg('Line')] + ([tr_msg('Version')] if len(versions) > 1 else []) + [tr_msg('Pipe of the run'), tr_msg('base')] + columns
    table.setColumnCount(len(headers))
    table.setHorizontalHeaderLabels(headers)
    for (version, line), entry in entries:
        values = [str(line)] + ([version] if len(versions) > 1 else []) + [pipeText(entry['before'], catalog)]
        values.append(pipeText(entry['base'], catalog, entry['before']) if entry['base'] is not None else '')
        values += [pipeText(entry['after'][name], catalog, entry['before']) if name in entry['after'] else '' for name in columns]
        k = table.rowCount()
        table.insertRow(k)
        for col, value in enumerate(values):
            table.setItem(k, col, QTableWidgetItem(value))
        table.item(k, 0).setData(Qt.ItemDataRole.UserRole, list(entry['after']))
    table.resizeColumnsToContents()


def loadSaved(config):
    try:
        return loadAnalysis(config)
    except Exception:
        QgsMessageLog.logMessage(traceback.format_exc(), 'Districts', MessageCritical)
        return None


def lastRunSeconds(config):
    """the duration of the last run of the loaded version: from its run parameters to its last iteration file"""
    try:
        parms = loadRunParameters(config, 'cost')
        files = glob.glob(iterationPath(config, '*'))
        if not parms.get('saved') or not files:
            return 0
        started = datetime.datetime.fromisoformat(parms['saved']).timestamp()
        return max(0, max(os.path.getmtime(f) for f in files) - started)
    except Exception:
        return 0


def durationText(seconds):
    if seconds < 90:
        return tr_msg('{:.0f} s').format(seconds)
    if seconds < 5400:
        return tr_msg('{:.0f} min').format(seconds / 60)
    return tr_msg('{:.1f} h').format(seconds / 3600)


def _titled(title, widget):
    """(the widget under a wrapped title, the title label)"""
    box = QWidget()
    layout = QVBoxLayout(box)
    layout.setContentsMargins(0, 4, 0, 0)
    label = QLabel(title)
    label.setWordWrap(True)
    layout.addWidget(label)
    layout.addWidget(widget)
    return box, label


class Detachable(QWidget):
    """a plot that can be undocked into a window of its own (moved, resized, maximized) and docked back by the button
    or by closing that window; the same widget moves, so its interaction stays"""

    def __init__(self, title, content):
        super().__init__()
        self.title, self.content, self.window_ = title, content, None
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        header = QHBoxLayout()
        header.addWidget(QLabel('<b>{}</b>'.format(title)))
        header.addStretch()
        self.button = QPushButton(tr_msg('Undock'))
        self.button.setToolTip(tr_msg('Show the plot in a window of its own; closing it docks the plot again'))
        self.button.clicked.connect(self.toggle)
        header.addWidget(self.button)
        layout.addLayout(header)
        self.placeholder = QLabel(tr_msg('Shown in its own window.'))
        self.placeholder.hide()
        layout.addWidget(self.placeholder)
        layout.addWidget(content, 1)

    def toggle(self):
        if self.window_ is not None:
            self.window_.close()
        else:
            self.undock()

    def undock(self):
        window = QDialog(self)
        window.setWindowTitle(self.title)
        window.setWindowFlags(Qt.WindowType.Window)
        QVBoxLayout(window).addWidget(self.content)
        window.finished.connect(lambda _: self.dock())
        window.resize(1000, 600)
        self.window_ = window
        self.placeholder.show()
        self.button.setText(tr_msg('Dock'))
        window.show()

    def dock(self):
        if self.window_ is None:
            return
        self.layout().addWidget(self.content, 1)
        self.placeholder.hide()
        self.button.setText(tr_msg('Undock'))
        self.window_ = None


def _table():
    table = QTableWidget(0, 0)
    table.verticalHeader().setVisible(False)
    table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
    table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Interactive)
    return table


def _editable():
    return Qt.ItemFlag.ItemIsEditable


def _checked(on):
    return Qt.CheckState.Checked if on else Qt.CheckState.Unchecked
