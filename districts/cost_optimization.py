# coding=utf-8
"""Dialog "Cost optimization" and its run (OpenSpec change cost-optimization): iteration 0 simulates the version's
pipes as reference; each iteration changes every line with a negative model ΔNPV by one size of its series, writes
the pipes, builds the network model and simulates the periods (PeriodRun); the run ends without improvement, on
oscillation, without an improving step or at max. iterations and restores the best simulated iteration."""
import glob
import html
import json
import os
import traceback

import psycopg2.extras

from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg
from matplotlib.figure import Figure
from qgis.PyQt.QtCore import QObject, Qt, QThreadPool, QTimer, pyqtSlot
from qgis.PyQt.QtGui import QColor, QGuiApplication
from qgis.PyQt.QtWidgets import (
    QAbstractItemView, QCheckBox, QComboBox, QDialog, QDoubleSpinBox, QFormLayout, QFrame, QHBoxLayout, QHeaderView, QLabel, QLineEdit,
    QProgressBar, QPushButton, QRadioButton, QScrollArea, QSpinBox, QTableWidget, QTableWidgetItem, QTabWidget, QTextEdit, QVBoxLayout,
    QWidget,
)
from qgis.core import QgsMessageLog
from qgis.gui import QgsCollapsibleGroupBox
from qgis.utils import iface

from .representative_periods import NEEDED_OUTPUTS, PeriodRun, PeriodsWidget, startTask
from .utility_functions.compat import MessageCritical, MessageInfo
from .utility_functions.cost_model_data import buildModel, checkSources, series
from .utility_functions.cost_optimization_layers import iterationPath, loadCostIterations, removeCostLayers, showCostIterations
from .utility_functions.db import getUsedNetworkSubmodels
from .utility_functions.dynamic_sizing_results import loadIterations
from .utility_functions.files import loadModellingSettings, loadRequestedOutputs
from .utility_functions.hydraulic_balancing import createChildVersion, getOrCreatePipeBundles, getPipeBundles
from .utility_functions.network_economics import evaluateVersion, resultTables
from .utility_functions.penalties import customerValues, penaltyCost, penaltyNpv
from .utility_functions.pipe_pairs import getPlantConnections, suggestPairs
from .utility_functions.reports import fillScenarioCombo
from .utility_functions.required_load import ensureRequired, saveRequired
from .utility_functions.translations import tr_msg
from .utility_functions.utility import write_plugin_settings
from .utility_functions.workers import WorkerLoadVersion

NO_IMPROVEMENT = 2
OPTIMIZATION_OUTPUTS = NEEDED_OUTPUTS + ('ppump_c', 'troom_c', 'power_c', 'mdot_lines')
# the checkbox of each output in the requested outputs dialog
OUTPUT_CHECKBOXES = {'ppump_ep': 'checkBoxPlantPumpPower', 'ppump_c': 'checkBoxSubstationPumpPower', 'temp_lines': 'checkBoxTempPipe',
                     'qamb_lines': 'checkBoxQambPipe', 'temp_ep': 'checkBoxPlantConnTemp', 'troom_c': 'checkBoxSubstationTair',
                     'power_c': 'checkBoxSubstationPower', 'mdot_lines': 'checkBoxMdotNode'}
BALANCING_LINK = 'balancing'


def missingOutputs(plugin_dir, config):
    outputs = loadRequestedOutputs(plugin_dir, config) or {}
    return [key for key in OPTIMIZATION_OUTPUTS if not outputs.get(key)]


def deleteIterationFiles(config):
    for path in glob.glob(iterationPath(config, '*')):
        os.remove(path)


def lineState(cur, schema):
    cur.execute('SELECT id, pipe_bundle_type_id AS bid FROM "{}".lines;'.format(schema))  # nosec B608
    return {row['id']: row['bid'] for row in cur.fetchall()}


def penaltyValues(cur, config, required, submodel, tolerance):
    """{cid: (Kh, unmet kWh)} per year of the checked iteration (worker thread: only the given cursor)"""
    check = checkSources(cur, config)
    if not check:
        return {}
    sources, times, w, hours, _ = check
    index = {t: k for k, t in enumerate(times)}
    schema = config['versionName']
    data = {var: series(cur, schema, sources('customer_s_' + var), '$' + var, times, index) for var in ('troom', 'tset', 'hcmode')}
    power = {}
    for table in resultTables(cur, schema, 'customer_s_power$'):
        for cid, arr in series(cur, schema, sources(table), '$power', times, index).items():
            power[cid] = power.get(cid, 0) + arr
    data['power'] = power
    cur.execute("""SELECT c.id, t.template::text || '_' || t.template_name AS t_name FROM "{}".customers c, customer_templates t
        WHERE c.template = t.template;""".format(schema))  # nosec B608
    templates = {row['id']: row['t_name'] for row in cur.fetchall()}
    return customerValues(data, hours, w, required, templates, config, submodel, tolerance)


def modelStep(cur, config, parms, settings, prices, no_smaller):
    """the cost model of the checked iteration, its step and the new pipes written into the version (worker thread):
    {'steps', 'rejected', 'state', 'n_changed'}, or None without a model"""
    model = buildModel(cur, config, parms['scenario'], parms['pairs'], settings, profile_dir=prices)
    if model is None:
        return None
    for lid in no_smaller:
        if lid in model.lines:
            model.lines[lid]['no_smaller'] = True
    chosen, rejected = model.step()
    steps = []
    for lid, c in sorted(chosen.items()):
        before = {seq: model.lines[lid]['pipes'][seq] for seq in c['pipes']}
        seq, pid = next(iter(c['pipes'].items()))
        steps.append({'line': lid, 'before': before, 'after': c['pipes'], 'dnpv': c['dnpv'], 'split': c['split'],
                      'larger': model.catalog[pid]['d'] > model.catalog[before[seq]]['d']})
    result = {'steps': steps, 'rejected': rejected, 'state': None, 'n_changed': 0}
    if not chosen:
        return result
    schema = config['versionName']
    current = lineState(cur, schema)
    bundles = getPipeBundles(cur)
    pipes = {lid: {**bundles.get(current[lid], {}), **c['pipes']} for lid, c in chosen.items()}
    new_bundles, _ = getOrCreatePipeBundles(cur, {lid: current[lid] for lid in chosen}, pipes)
    for lid, bid in new_bundles.items():
        cur.execute('UPDATE "{}".lines SET pipe_bundle_type_id = %s WHERE id = %s;'.format(schema), (bid, lid))  # nosec B608
    result['state'] = tuple(sorted(lineState(cur, schema).items()))
    result['n_changed'] = len(new_bundles)
    return result


class CostOptimizationDialog(QDialog):
    def __init__(self, main):
        super().__init__()
        self.main = main
        self.process_running = False
        self.run = None
        cur, config = main.cur, main.config
        self.setWindowTitle(tr_msg('Cost optimization'))
        self.resize(1100, 850)
        layout = QVBoxLayout(self)
        form = QFormLayout()
        self.combo_scenario = QComboBox()
        fillScenarioCombo(cur, self.combo_scenario)
        self.combo_network = QComboBox()
        cur.execute('SELECT network FROM "{}".lines GROUP BY network ORDER BY network;'.format(config['versionName']))  # nosec B608
        self.combo_network.addItems([str(row['network']) for row in cur.fetchall()])
        self.combo_submodel = QComboBox()
        self.combo_submodel.addItems(getUsedNetworkSubmodels(cur, config))
        self.edit_pairs = QLineEdit()
        self.edit_pairs.setToolTip(tr_msg('Supply/return pairs, e.g. 1/2, 3/4'))
        self.spin_price_kh = QDoubleSpinBox()
        self.spin_price_kh.setRange(0, 1000)
        self.spin_price_kh.setValue(0.5)
        self.spin_tolerance = QDoubleSpinBox()
        self.spin_tolerance.setRange(0, 5)
        self.spin_tolerance.setValue(0.5)
        self.spin_price_kwh = QDoubleSpinBox()
        self.spin_price_kwh.setRange(0, 1000)
        self.spin_price_kwh.setValue(1.0)
        self.spin_iter = QSpinBox()
        self.spin_iter.setRange(1, 100)
        self.spin_iter.setValue(10)
        self.rbtn_new = QRadioButton(tr_msg('New child version'))
        self.rbtn_override = QRadioButton(tr_msg('Override the pipes of the loaded version'))
        self.rbtn_new.setChecked(True)
        self.edit_version = QLineEdit(config['versionName'] + '_costopt')
        self.check_outputs = QCheckBox(tr_msg('Switch on the requested outputs the optimization needs at the start'))
        self.check_outputs.setToolTip(tr_msg('Pump power of the customers and energy plants, temperatures and losses of the lines, plant temperatures, '
                                             'room temperatures and power of the customers; written into the templates of the project, '
                                             'the first run invokes the features again'))
        self.check_outputs.setChecked(True)
        penalties = QHBoxLayout()
        for widget in (QLabel(tr_msg('€/Kh')), self.spin_price_kh, QLabel(tr_msg('tolerance [K]')), self.spin_tolerance, QLabel(tr_msg('€/kWh unmet')), self.spin_price_kwh):
            penalties.addWidget(widget)
        version = QHBoxLayout()
        for widget in (self.rbtn_new, self.edit_version, self.rbtn_override):
            version.addWidget(widget)
        form.addRow(tr_msg('Scenario'), self.combo_scenario)
        form.addRow(tr_msg('Network'), self.combo_network)
        form.addRow(tr_msg('Submodel'), self.combo_submodel)
        form.addRow(tr_msg('Pairs'), self.edit_pairs)
        form.addRow(tr_msg('Penalties'), penalties)
        form.addRow(tr_msg('Max. iterations'), self.spin_iter)
        form.addRow(tr_msg('Outputs'), self.check_outputs)
        form.addRow(tr_msg('Version'), version)
        self.label_hints = QLabel()
        self.label_hints.setWordWrap(True)
        self.label_hints.setTextFormat(Qt.TextFormat.RichText)
        self.label_hints.linkActivated.connect(self.onHintLink)
        layout.addWidget(self.label_hints)
        # the sections scroll, so the progress bar and the buttons stay visible on any screen
        sections = QWidget()
        outer = layout
        layout = QVBoxLayout(sections)
        layout.setContentsMargins(0, 0, 0, 0)
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.Shape.NoFrame)
        scroll.setWidget(sections)
        outer.addWidget(scroll, 1)
        self.box_settings = self.section(tr_msg('Settings'), form)
        layout.addWidget(self.box_settings)
        self.log_edit = QTextEdit()
        self.log_edit.setReadOnly(True)
        # the weeks shown here are the weeks every check simulates
        self.periods = PeriodsWidget(main, self.log)
        self.box_periods = self.section(tr_msg('Periods'), self.periods)
        layout.addWidget(self.box_periods)
        self.table_required = QTableWidget(0, 4)
        self.table_required.setHorizontalHeaderLabels([tr_msg('Template'), tr_msg('Column'), tr_msg('Unit'), tr_msg('Mode')])
        self.table_required.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Interactive)
        self.table_required.setMaximumHeight(120)
        self.box_required = self.section(tr_msg('Required load of source-file customers (column of the source file)'), self.table_required, collapsed=True)
        layout.addWidget(self.box_required)
        self.table_iterations = QTableWidget(0, 9)
        self.table_iterations.setHorizontalHeaderLabels([tr_msg('Iteration'), tr_msg('NPV simulated'), tr_msg('NPV model'), tr_msg('Model error'),
                                                         tr_msg('larger'), tr_msg('smaller'), tr_msg('rejected'), tr_msg('Customers with deficit'),
                                                         tr_msg('Outcome')])
        self.table_iterations.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Interactive)
        self.table_iterations.verticalHeader().setVisible(False)
        self.table_iterations.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.table_iterations.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.table_iterations.setToolTip(tr_msg('Iterations of the last run in the loaded version. Select one or more iterations and show them on the map '
                                                '(inner diameters, lines changed for the iteration, customers with a new deficit).'))
        self.table_iterations.itemDoubleClicked.connect(lambda item: self.showSelectedIterations())
        self.btn_showIterations = QPushButton(tr_msg('Show selected iterations on the map'))
        self.btn_removeLayers = QPushButton(tr_msg('Remove the iteration layers'))
        self.btn_reload = QPushButton(tr_msg('Reload'))
        self.btn_showIterations.clicked.connect(self.showSelectedIterations)
        self.btn_removeLayers.clicked.connect(lambda: removeCostLayers())
        self.btn_reload.clicked.connect(self.loadIterationTable)
        tab_iterations = QWidget()
        inner = QVBoxLayout(tab_iterations)
        inner.addWidget(self.table_iterations)
        row_buttons = QHBoxLayout()
        for button in (self.btn_showIterations, self.btn_removeLayers, self.btn_reload):
            row_buttons.addWidget(button)
        inner.addLayout(row_buttons)
        self.figure = Figure(figsize=(9, 4))
        self.canvas = FigureCanvasQTAgg(self.figure)
        self.canvas.setMinimumHeight(250)
        results = QTabWidget()
        results.addTab(tab_iterations, tr_msg('Iterations'))
        results.addTab(self.canvas, tr_msg('Net present value'))
        results.addTab(self.log_edit, tr_msg('Log'))
        results.setMinimumHeight(330)
        self.tabs_results = results
        # opened when a run starts; before, the settings and periods have the room
        self.box_results = self.section(tr_msg('Results'), results, collapsed=True)
        layout.addWidget(self.box_results, 1)
        layout.addStretch()
        self.progress = QProgressBar()
        outer.addWidget(self.progress)
        buttons = QHBoxLayout()
        self.btn_start, self.btn_stop, self.btn_close = QPushButton(tr_msg('Start')), QPushButton(tr_msg('Stop')), QPushButton(tr_msg('Close'))
        for button in (self.btn_start, self.btn_stop, self.btn_close):
            buttons.addWidget(button)
        outer.addLayout(buttons)
        screen = QGuiApplication.primaryScreen()
        if screen:
            available = screen.availableGeometry()
            self.resize(min(1100, available.width() - 40), min(850, available.height() - 80))
        self.btn_start.clicked.connect(self.start)
        self.btn_stop.clicked.connect(self.stop)
        self.btn_close.clicked.connect(self.close)
        self.combo_network.currentIndexChanged.connect(self.suggestPairs)
        self.suggestPairs()
        self.check_outputs.toggled.connect(self.updateHints)
        self.fillRequired()
        self.updateHints()
        self.updateEnabled()
        self.loadIterationTable()

    # ---------------------------------------------------------------- settings
    def section(self, title, content, collapsed=False):
        """a collapsible section with a layout or a widget"""
        box = QgsCollapsibleGroupBox(title)
        box.setSaveCollapsedState(False)
        if isinstance(content, QWidget):
            inner = QVBoxLayout()
            inner.setContentsMargins(4, 4, 4, 4)
            inner.addWidget(content)
            box.setLayout(inner)
        else:
            box.setLayout(content)
        box.setCollapsed(collapsed)
        return box

    def log(self, message):
        self.log_edit.append(message)

    def update_progress(self, value):
        self.progress.setValue(int(value))

    def suggestPairs(self):
        try:
            pairs, _ = suggestPairs(getPlantConnections(self.main.cur, self.main.config, int(self.combo_network.currentText() or 1)))
            self.edit_pairs.setText(', '.join('{}/{}'.format(p[0], p[1]) for p in pairs))
        except Exception:
            QgsMessageLog.logMessage(traceback.format_exc(), 'Districts', MessageCritical)

    def pairs(self):
        pairs = []
        for text in self.edit_pairs.text().split(','):
            if '/' in text:
                s, r = text.split('/')
                pairs.append((int(s), int(r)))
        return pairs

    def fillRequired(self):
        from .utility_functions.db import getTemplateNames
        entries = ensureRequired(self.main.config, getTemplateNames(self.main.cur, 'customer', seperator='_'))
        self.table_required.setRowCount(0)
        for entry in entries:
            row = self.table_required.rowCount()
            self.table_required.insertRow(row)
            for col, key in enumerate(('template', 'column', 'unit', 'mode')):
                self.table_required.setItem(row, col, QTableWidgetItem(str(entry[key])))

    def requiredEntries(self):
        entries = []
        for row in range(self.table_required.rowCount()):
            text = [self.table_required.item(row, col).text() if self.table_required.item(row, col) else '' for col in range(4)]
            try:
                entries.append({'template': text[0], 'column': int(text[1]), 'unit': text[2] or 'W', 'mode': text[3] or 'heating'})
            except ValueError:
                continue
        return entries

    def updateHints(self):
        hints = []
        if not loadIterations(self.main.config):
            hints.append('<a href="{}">{}</a>'.format(BALANCING_LINK, html.escape(
                tr_msg('The version has no iterations of the hydraulic balancing; run it first for a balanced start.'))))
        missing = missingOutputs(self.main.plugin_dir, self.main.config)
        if missing:
            state = tr_msg('switched on at the start') if self.check_outputs.isChecked() else tr_msg('switched off')
            hints.append(html.escape(tr_msg('Requested outputs the optimization needs ({}): {}').format(state, ', '.join(missing))))
        self.label_hints.setText('<br>'.join(hints))

    def onHintLink(self, link):
        if link == BALANCING_LINK:
            self.main.showDynamicPipeSizing()

    def updateEnabled(self):
        self.periods.setRunning(self.process_running)
        self.btn_start.setEnabled(not self.process_running)
        self.btn_stop.setEnabled(self.process_running)
        # while running the run adds and shows the iterations itself
        for button in (self.btn_showIterations, self.btn_reload):
            button.setEnabled(not self.process_running)

    def parameters(self):
        return {'scenario': self.combo_scenario.currentData(), 'network': self.combo_network.currentText(), 'submodel': self.combo_submodel.currentText(),
                'pairs': self.pairs(), 'periods': self.periods.parameters(),
                'price_kh': self.spin_price_kh.value(), 'tolerance': self.spin_tolerance.value(), 'price_kwh': self.spin_price_kwh.value(),
                'max_iter': self.spin_iter.value(), 'new_version': self.edit_version.text().strip() if self.rbtn_new.isChecked() else None,
                'set_outputs': self.check_outputs.isChecked()}

    # ---------------------------------------------------------------- run
    def start(self):
        if not self.periods.ready and not self.periods.check_annual.isChecked():
            self.log(tr_msg('The weeks are still being chosen; start again in a moment.'))
            return
        p = self.parameters()
        if p['scenario'] is None or not p['pairs'] or not p['submodel']:
            self.log(tr_msg('Choose a scenario, a submodel and at least one pair.'))
            return
        saveRequired(self.main.config, self.requiredEntries())
        self.process_running = True
        self.updateEnabled()
        self.table_iterations.setRowCount(0)
        self.log_edit.clear()
        # during the run the results need the room
        for box in (self.box_settings, self.box_periods, self.box_required):
            box.setCollapsed(True)
        self.box_results.setCollapsed(False)
        self.log(tr_msg('Starting ...'))
        self.run = CostOptimizationRun(self, self.main, p)
        # the start (child version, first simulation) blocks for a moment: first let the dialog show the greyed button
        QTimer.singleShot(50, self.run.start)

    def stop(self):
        if self.run:
            self.run.stop_requested = True
            self.log(tr_msg('Stopping after the current step ...'))

    def finished(self):
        self.process_running = False
        self.updateEnabled()
        self.updateHints()

    def loadIterationTable(self):
        """the iterations saved in the loaded version"""
        self.table_iterations.setRowCount(0)
        try:
            rows = loadCostIterations(self.main.config)
        except Exception:
            QgsMessageLog.logMessage(traceback.format_exc(), 'Districts', MessageCritical)
            rows = []
        for row in rows:
            self.addRow(row)
        if rows:
            self.plot(rows)
            self.markBest(min(rows, key=lambda r: r['npv'])['iteration'])
            self.box_results.setCollapsed(False)

    def selectedIterations(self):
        return sorted({int(self.table_iterations.item(index.row(), 0).text()) for index in self.table_iterations.selectedIndexes()})

    def showSelectedIterations(self):
        selected = self.selectedIterations()
        if not selected:
            iface.messageBar().pushMessage(tr_msg('Info'), tr_msg('Please select one or more iterations in the table.'), level=MessageInfo)
            return
        try:
            showCostIterations(self.main.cur, self.main.config, selected, loadCostIterations(self.main.config))
            iface.mapCanvas().refresh()
        except Exception:
            QgsMessageLog.logMessage(traceback.format_exc(), 'Districts', MessageCritical)
            iface.messageBar().pushMessage(tr_msg('Error'), tr_msg('The iterations could not be shown: ') + traceback.format_exc().splitlines()[-1],
                                           level=MessageCritical)

    def addRow(self, row):
        r = self.table_iterations.rowCount()
        self.table_iterations.insertRow(r)
        values = [row['iteration'], '{:,.0f}'.format(row['npv']).replace(',', "'"), '' if row.get('npv_model') is None else '{:,.0f}'.format(row['npv_model']).replace(',', "'"),
                  '' if row.get('model_error') is None else '{:.1%}'.format(row['model_error']), row.get('n_larger', ''), row.get('n_smaller', ''),
                  row.get('n_rejected', ''), len(row.get('penalty_customers') or []), row.get('outcome', '')]
        for col, value in enumerate(values):
            self.table_iterations.setItem(r, col, QTableWidgetItem(str(value)))

    def markBest(self, iteration):
        for r in range(self.table_iterations.rowCount()):
            best = self.table_iterations.item(r, 0).text() == str(iteration)
            for col in range(self.table_iterations.columnCount()):
                item = self.table_iterations.item(r, col)
                if item:
                    item.setBackground(QColor('#c8e6c9') if best else QColor(0, 0, 0, 0))

    def plot(self, rows):
        self.figure.clear()
        ax = self.figure.add_subplot(111)
        groups = ('investment', 'pump_energy', 'heat_losses', 'cold_losses', 'maintenance', 'residual', 'penalties')
        x = [row['iteration'] for row in rows]
        bottom_pos, bottom_neg = [0.0] * len(rows), [0.0] * len(rows)
        for group in groups:
            values = [row['split'].get(group, 0.0) for row in rows]
            base = [bp if v >= 0 else bn for v, bp, bn in zip(values, bottom_pos, bottom_neg)]
            ax.bar(x, values, bottom=base, label=tr_msg(group))
            bottom_pos = [bp + max(v, 0) for v, bp in zip(values, bottom_pos)]
            bottom_neg = [bn + min(v, 0) for v, bn in zip(values, bottom_neg)]
        model = [(row['iteration'], row['npv_model']) for row in rows if row.get('npv_model') is not None]
        if model:
            ax.plot([m[0] for m in model], [m[1] for m in model], 'k--o', label=tr_msg('model'))
        ax.set_xlabel(tr_msg('iteration'))
        ax.set_ylabel(tr_msg('net present value [€]'))
        ax.legend(fontsize=6, ncol=4)
        self.figure.tight_layout()
        self.canvas.draw()


class _CheckDialog:
    """what PeriodRun needs of a dialog, for a check inside the optimization"""

    def __init__(self, dlg, year, t_year, climate):
        self.dlg, self.year, self.t_year, self.climate = dlg, year, t_year, climate

    def log(self, message):
        self.dlg.log('  ' + message)

    def update_progress(self, value):
        pass

    def finished(self):
        pass


class CostOptimizationRun(QObject):
    def __init__(self, dlg, main, parms):
        super().__init__()
        self.dlg, self.main, self.parms = dlg, main, parms
        self.plugin_dir = main.plugin_dir
        self.iteration = 0
        self.rows, self.states, self.line_states = [], [], {}
        self.reference = None
        self.no_smaller = set()
        self.done = False
        self.stop_requested = False
        self.final_check = False

    @property
    def config(self):
        return self.main.config

    @property
    def cur(self):
        return self.main.cur

    # ---------------------------------------------------------------- start
    def start(self):
        try:
            self.settings = loadModellingSettings(self.plugin_dir, self.config)
            self.prices = os.path.join(self.config['pathProjects'] + self.config['projectName'], 'prices')
            self.year, self.t_year, self.climate = self.dlg.periods.year, self.dlg.periods.t_year, self.dlg.periods.climate
            missing = missingOutputs(self.plugin_dir, self.config) if self.parms.get('set_outputs') else []
        except Exception:
            self.onException()
            return
        if missing:
            self.setOutputs(missing)
        else:
            self.afterOutputs()

    def setOutputs(self, missing):
        """the missing outputs switched on as in the requested outputs dialog (written into the project's templates)"""
        from .ida_mosim_dialog import RequestedOutputsDialog
        from .outputs import WorkerSetRequestedOutputs
        self.dlg.log(tr_msg('Switching on the requested outputs: {} ...').format(', '.join(missing)))
        try:
            requested = loadRequestedOutputs(self.plugin_dir, self.config)
            self.dlg_outputs = RequestedOutputsDialog(requested, self.config, self.cur)
            for key in missing:
                getattr(self.dlg_outputs, OUTPUT_CHECKBOXES[key]).setChecked(True)
            self.worker_outputs = WorkerSetRequestedOutputs(config=self.config, plugin_dir=self.plugin_dir, dlg=self.dlg_outputs, requestedOutputs=requested)
            self.worker_outputs.signals.error.connect(self.onOutputsError)
            self.worker_outputs.signals.finished.connect(self.onOutputsSet)
            QThreadPool.globalInstance().start(self.worker_outputs)
        except Exception:
            self.onException()

    @pyqtSlot(str)
    def onOutputsError(self, message):
        self.dlg.log('  ' + message)

    @pyqtSlot(str)
    def onOutputsSet(self, message):
        if self.done:
            return
        self.main.requestedOutputs = loadRequestedOutputs(self.plugin_dir, self.config)
        still = missingOutputs(self.plugin_dir, self.config)
        if still:
            self.finish(tr_msg('The requested outputs could not be switched on: {}').format(', '.join(still)), error=True)
            return
        self.dlg.updateHints()
        self.afterOutputs()

    def afterOutputs(self):
        if self.stopCheck():
            return
        if self.parms['new_version']:
            self.createVersion()
        else:
            self.begin()

    def createVersion(self):
        name = self.parms['new_version']
        self.dlg.log(tr_msg('Creating the child version {} of {} ...').format(name, self.config['versionName']))
        config, plugin_dir, description = dict(self.config), self.plugin_dir, 'Cost optimization of version {}'.format(self.config['versionName'])
        startTask(self, self.config, lambda cur: createChildVersion(cur, config, plugin_dir, name, description), self.onVersionCreated, self.onTaskFailed)

    @pyqtSlot(object)
    def onVersionCreated(self, _):
        from .ida_ph import getVersionData, importData
        if self.done:
            return
        name = self.parms['new_version']
        try:
            importData(self.main.model, getVersionData(self.cur))
            self.main.config['versionName'] = name
            write_plugin_settings(self.main.config)
            from .ida_ph import loadVersionLayers
            loadVersionLayers(self.config, self.cur, self.plugin_dir)
            self.worker_version = WorkerLoadVersion(config=self.config, cur=self.cur, dlg=self.main.dlg)
            self.worker_version.signals.error.connect(lambda m: self.dlg.log(m))
            self.worker_version.signals.finished.connect(self.onVersionLoaded)
            QThreadPool.globalInstance().start(self.worker_version)
        except Exception:
            self.onException()

    @pyqtSlot(str)
    def onVersionLoaded(self, message):
        from .ida_ph import finishedLoadVersion
        if self.done:
            return
        finishedLoadVersion(self.main)
        self.begin()

    def begin(self):
        deleteIterationFiles(self.config)
        removeCostLayers()
        self.periods = self.parms['periods']
        if not self.periods['annual']:
            self.dlg.log(tr_msg('Weeks from {}').format(', '.join(str(d[0].date()) for d in self.periods['periods'])))
        self.check(build=True)

    # ---------------------------------------------------------------- checks
    def check(self, build):
        if self.stopCheck():
            return
        self.dlg.log(tr_msg('Iteration {}: simulating the periods ...').format(self.iteration))
        parms = {'network': self.parms['network'], 'submodel': self.parms['submodel'], 'build_first': build,
                 # the first run invokes the customers and plants again, so their outputs match the requested ones
                 'reinvoke': self.iteration == 0 and not self.final_check, **self.periods}
        self.period_run = PeriodRun(_CheckDialog(self.dlg, self.year, self.t_year, self.climate), self.main, parms, on_finished=self.onChecked)
        self.period_run.start()

    def onChecked(self, ok):
        if self.done:
            return
        if not ok:
            self.finish(tr_msg('The check of iteration {} failed.').format(self.iteration), error=True)
            return
        try:
            if self.final_check:
                self.finish(tr_msg('Finished: the pipes of iteration {} are in the version and simulated.').format(self.best()['iteration']))
                return
            self.evaluate()
        except Exception:
            self.onException()

    def onTaskFailed(self, message):
        self.finish(tr_msg('Error in iteration {}: {}').format(self.iteration, message), error=True)

    def evaluate(self):
        """the NPV and the penalties of the checked iteration, in a worker thread"""
        self.dlg.log(tr_msg('Iteration {}: evaluating the results ...').format(self.iteration))
        config, p, settings, prices, required = dict(self.config), dict(self.parms), self.settings, self.prices, self.dlg.requiredEntries()

        def work(cur):
            evaluation = evaluateVersion(cur, config, p['scenario'], settings, profile_dir=prices)
            if 'npv' not in evaluation:
                return evaluation, None, None
            return evaluation, penaltyValues(cur, config, required, p['submodel'], p['tolerance']), lineState(cur, config['versionName'])

        startTask(self, self.config, work, self.onEvaluated, self.onTaskFailed)

    @pyqtSlot(object)
    def onEvaluated(self, result):
        if self.done:
            return
        try:
            self.evaluated(*result)
        except Exception:
            self.onException()

    def evaluated(self, evaluation, values, state):
        p = self.parms
        if 'npv' not in evaluation:
            self.finish(tr_msg('The results of iteration {} cannot be evaluated: {}').format(self.iteration, evaluation.get('missing') or evaluation.get('short')), error=True)
            return
        if self.reference is None:
            self.reference = values
        sc = evaluation['scenario']['scenario']
        yearly_penalty = penaltyCost(values, self.reference, p['price_kh'], p['price_kwh'])
        split = dict(evaluation['npv']['split'])
        split['penalties'] = penaltyNpv(yearly_penalty, float(sc.get('interest_pct') or 0), int(sc.get('period_a') or 0))
        npv = sum(split.values())
        previous = self.rows[-1] if self.rows else None
        npv_model = previous.get('npv_next') if previous else None
        row = {'iteration': self.iteration, 'npv': npv, 'split': split, 'npv_model': npv_model,
               'model_error': None if npv_model is None or not npv else (npv_model - npv) / abs(npv),
               'penalty_customers': sorted(cid for cid, v in values.items() if v[0] > self.reference.get(cid, (0, 0))[0] + 1e-6 or v[1] > self.reference.get(cid, (0, 0))[1] + 1e-6),
               'state': state}
        if previous:
            # a new deficit: the lines made smaller in the last step stay as they are now
            row['penalty_reverted'] = [lid for lid in previous.get('smaller', []) if row['penalty_customers']]
            self.no_smaller.update(row['penalty_reverted'])
        self.rows.append(row)
        self.nextStep(row)

    # ---------------------------------------------------------------- steps
    def nextStep(self, row):
        p = self.parms
        best = self.best()
        if self.iteration >= p['max_iter']:
            row['outcome'] = tr_msg('max. iterations')
            self.saveRow(row, [], {})
            return self.end(tr_msg('Maximal number of iterations reached.'))
        if len(self.rows) > NO_IMPROVEMENT and all(r['npv'] >= best['npv'] for r in self.rows[-NO_IMPROVEMENT:]) and best is not self.rows[-1]:
            row['outcome'] = tr_msg('no improvement')
            self.saveRow(row, [], {})
            return self.end(tr_msg('No improvement of the simulated NPV for {} iterations.').format(NO_IMPROVEMENT))
        self.dlg.log(tr_msg('Iteration {}: cost model and step ...').format(self.iteration))
        config, settings, prices, no_smaller = dict(self.config), self.settings, self.prices, set(self.no_smaller)
        startTask(self, self.config, lambda cur: modelStep(cur, config, p, settings, prices, no_smaller), self.onStep, self.onTaskFailed)

    @pyqtSlot(object)
    def onStep(self, result):
        if self.done:
            return
        try:
            self.stepped(result)
        except Exception:
            self.onException()

    def stepped(self, result):
        row = self.rows[-1]
        if result is None:
            return self.finish(tr_msg('The cost model could not be built from the results.'), error=True)
        row['n_rejected'] = sum(len(v) for v in result['rejected'].values())
        if not result['steps']:
            row['outcome'] = tr_msg('no improving change')
            self.saveRow(row, [], result['rejected'])
            return self.end(tr_msg('No change improves the costs.'))
        row['npv_next'] = row['npv'] + sum(s['dnpv'] for s in result['steps'])
        row['larger'] = sorted(s['line'] for s in result['steps'] if s['larger'])
        row['smaller'] = sorted(s['line'] for s in result['steps'] if not s['larger'])
        row['n_larger'], row['n_smaller'] = len(row['larger']), len(row['smaller'])
        self.dlg.log(tr_msg('  {} lines changed').format(result['n_changed']))
        iface.mapCanvas().refreshAllLayers()
        state = result['state']
        if state in self.states:
            row['outcome'] = tr_msg('oscillation')
            self.saveRow(row, result['steps'], result['rejected'])
            return self.end(tr_msg('The pipes repeat an earlier iteration (oscillation).'))
        self.states.append(state)
        row['outcome'] = tr_msg('changed')
        self.saveRow(row, result['steps'], result['rejected'])
        self.iteration += 1
        self.check(build=True)

    def saveRow(self, row, steps, rejected):
        data = {k: v for k, v in row.items() if k != 'state'}
        data.update({'steps': steps, 'rejected': {str(lid): reasons for lid, reasons in rejected.items()}, 'state': {str(k): v for k, v in row['state'].items()}})
        with open(iterationPath(self.config, row['iteration']), 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=1, default=str)
        self.dlg.addRow(row)
        self.dlg.plot(self.rows)
        self.dlg.update_progress(min(99, (row['iteration'] + 1) / (self.parms['max_iter'] + 1) * 100))
        try:
            showCostIterations(self.cur, self.config, [row['iteration']], loadCostIterations(self.config))
        except Exception:
            QgsMessageLog.logMessage(traceback.format_exc(), 'Districts', MessageCritical)

    # ---------------------------------------------------------------- end
    def best(self):
        return min(self.rows, key=lambda r: r['npv']) if self.rows else None

    def end(self, message):
        best = self.best()
        self.dlg.log(message)
        self.dlg.markBest(best['iteration'])
        schema = self.config['versionName']
        if best['state']:
            # one statement: a row per line would block the dialog on large networks
            psycopg2.extras.execute_values(self.cur, 'UPDATE "{}".lines l SET pipe_bundle_type_id = v.bid FROM (VALUES %s) AS v(id, bid) WHERE l.id = v.id;'.format(schema),  # nosec B608
                                           [(int(lid), bid) for lid, bid in best['state'].items()])
        if best is self.rows[-1] and lineState(self.cur, schema) == best['state']:
            self.finish(tr_msg('Finished: iteration {} has the least NPV ({:,.0f} €).').format(best['iteration'], best['npv']).replace(',', "'"))
            return
        self.dlg.log(tr_msg('The pipes of iteration {} are restored and simulated again.').format(best['iteration']))
        self.final_check = True
        self.check(build=True)

    def stopCheck(self):
        if self.done:
            return True
        if self.stop_requested:
            self.finish(tr_msg('Stopped by the user after iteration {}.').format(self.iteration), error=True)
            return True
        return False

    def finish(self, message, error=False):
        if self.done:
            return
        self.done = True
        self.dlg.log(message)
        self.dlg.update_progress(0 if error else 100)
        iface.messageBar().pushMessage(tr_msg('Error') if error else tr_msg('Info'), tr_msg('Cost optimization: ') + message,
                                       level=MessageCritical if error else MessageInfo)
        self.dlg.finished()

    def onException(self):
        QgsMessageLog.logMessage(traceback.format_exc(), 'Districts', MessageCritical)
        self.finish(tr_msg('Error in iteration {}: {}').format(self.iteration, traceback.format_exc().splitlines()[-1]), error=True)
