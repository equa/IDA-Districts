# coding=utf-8
"""Sensitivity analysis in the cost optimization dialog (OpenSpec change cost-sensitivity D1, D3–D7): the section with
the parameter table, the results tab and the run of the variants (estimate in worker tasks, or one cost optimization
per variant, one after another)."""
import datetime
import glob
import os
import traceback

from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg
from matplotlib.figure import Figure
from qgis.PyQt.QtCore import QObject, QSize, Qt, pyqtSlot
from qgis.PyQt.QtWidgets import (
    QAbstractItemView, QComboBox, QDialog, QHBoxLayout, QHeaderView, QLabel, QMessageBox, QPushButton, QSpinBox, QTableWidget,
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
from .utility_functions.sensitivity_plots import money, parallelCoordinates, resultAxes, tornadoChart
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


class SensitivityResults(QWidget):
    """the tab 'Sensitivity': plots, the variants and the lines that flip, the robustness on the map"""

    def __init__(self, dlg):
        super().__init__()
        self.dlg = dlg
        self.analysis = None
        layout = QVBoxLayout(self)
        self.figure = Figure(figsize=(9, 3.6))
        self.canvas = _Canvas(self.figure)
        self.canvas.setToolTip(tr_msg('Click for a larger view'))
        self.canvas.mpl_connect('button_press_event', lambda _: self.enlarge())
        layout.addWidget(self.canvas, 2)
        self.table_variants = _table()
        self.table_flips = _table()
        tables = QHBoxLayout()
        tables.addWidget(self.table_variants, 3)
        tables.addWidget(self.table_flips, 2)
        layout.addLayout(tables, 1)
        row = QHBoxLayout()
        self.label = QLabel()
        self.btn_map = QPushButton(tr_msg('Show the robustness on the map'))
        self.btn_map.clicked.connect(self.showMap)
        row.addWidget(self.label, 1)
        row.addWidget(self.btn_map)
        layout.addLayout(row)
        self.show(loadSaved(dlg.main.config))

    def show(self, analysis):
        self.analysis = analysis
        self.figure.clear()
        self.table_variants.setRowCount(0)
        self.table_flips.setRowCount(0)
        done = [v for v in (analysis or {}).get('variants', []) if v.get('result')]
        self.btn_map.setEnabled(bool(done))
        if not done:
            self.label.setText(tr_msg('No sensitivity analysis in this version yet.'))
            self.canvas.draw()
            return
        self.label.setText(tr_msg('{} of {} variants, {} ({}), started {}').format(
            len(done), len(analysis['variants']), tr_msg(DESIGN_LABELS.get(analysis['design'], analysis['design'])),
            tr_msg(MODE_LABELS.get(analysis['mode'], analysis['mode'])), analysis.get('started', '')))
        if len(done) > 1:
            parallelCoordinates(self.figure.add_subplot(121), analysis)
            tornadoChart(self.figure.add_subplot(122), analysis)
            self.figure.tight_layout()
        self.canvas.draw()
        fillVariantTable(self.table_variants, analysis)
        fillFlipTable(self.table_flips, analysis, self.dlg.main.cur)

    def enlarge(self):
        if not self.analysis:
            return
        dialog = QDialog(self)
        dialog.setWindowTitle(tr_msg('Sensitivity analysis'))
        figure = Figure(figsize=(12, 6))
        parallelCoordinates(figure.add_subplot(111), self.analysis)
        figure.tight_layout()
        QVBoxLayout(dialog).addWidget(FigureCanvasQTAgg(figure))
        dialog.resize(1200, 650)
        dialog.exec()

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
        self.dlg.results_tabs.setCurrentWidget(self.dlg.sensitivity_results)
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
        self.dlg.results_tabs.setCurrentWidget(self.dlg.sensitivity_results)

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
    headers = [tr_msg('Variant')] + [labels.get(k, k) for k in keys] + [tr_msg('NPV [€]'), tr_msg('Investment [€]'), tr_msg('Operating costs [€]'),
                                                                        tr_msg('Changed lines')]
    table.setColumnCount(len(headers))
    table.setHorizontalHeaderLabels(headers)
    for v in analysis['variants']:
        if not v.get('result'):
            continue
        axes = resultAxes(v)
        values = [v['name']] + ['{:.4g}'.format(v['values'][k]) for k in keys] + [money(axes['npv']), money(axes['investment']), money(axes['operating']),
                                                                                 str(int(axes['changed']))]
        k = table.rowCount()
        table.insertRow(k)
        for col, value in enumerate(values):
            table.setItem(k, col, QTableWidgetItem(value))
    table.resizeColumnsToContents()


def fillFlipTable(table, analysis, cur):
    from .utility_functions.hydraulic_balancing import getPipeCatalog
    catalog = getPipeCatalog(cur)

    def names(ids):
        return ', '.join(str(catalog.get(int(i), {}).get('name', i)) for i in ids)
    table.setColumnCount(4)
    table.setHorizontalHeaderLabels([tr_msg('Line'), tr_msg('Version'), tr_msg('Pipe in the base'), tr_msg('Changed in')])
    for (version, line), entry in sorted(flips(analysis).items()):
        changed = ['{}: {}'.format(name, names(after)) for name, after in entry['after'].items()]
        k = table.rowCount()
        table.insertRow(k)
        for col, value in enumerate([str(line), version, names(entry['before']), '; '.join(changed)]):
            table.setItem(k, col, QTableWidgetItem(value))
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
