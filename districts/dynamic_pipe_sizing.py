"""Dynamic pipe sizing: iteration of building the network model, simulation, loading the results, pipe sizing and
hydraulic balancing (utility_functions.hydraulic_balancing) until the pipe dimensions do not change anymore.
The workflow is described in the info text dynamic_pipe_sizing_info (i18n/districts_*.ts)."""
from qgis.PyQt import uic
from qgis.PyQt.QtCore import QDateTime, QObject, QThreadPool, pyqtSlot
from qgis.PyQt.QtWidgets import (
    QCheckBox, QDateTimeEdit, QDialog, QFrame, QHBoxLayout, QHeaderView, QLabel, QMessageBox, QPushButton, QTableWidget, QTableWidgetItem,
    QVBoxLayout, QWidget,
)
from qgis.core import QgsMessageLog
from qgis.gui import QgsCollapsibleGroupBox
from qgis.utils import iface

from .ida_mosim import runModel
from .ida_mosim_dialog import RunNetworkModelDialog
from .ida_rv import loadResults
from .ida_rv_dialog import LoadResultsDialog
from .invoke_network import WorkerBuildNetworkModel
from .utility_functions.compat import MessageCritical, MessageInfo
from .utility_functions.db import dbConnect, getUsedNetworkSubmodels
from .utility_functions.dialog import infoTextEdit
from .utility_functions.files import loadNetworkSimData
from .utility_functions.dynamic_sizing_results import (
    deleteIterations, iterationRows, iterationSummary, loadIterations, pairSummary, removeSizingLayers, saveIteration, showIteration,
    showIterations,
)
from .utility_functions.hydraulic_balancing import (
    createChildVersion, getCustomerLinePressure, getOrCreatePipeBundles, getPipeBundles, optimizePipeDiameters, saveCLidPressure,
)
from .utility_functions.pipe_pairs import (
    DEFAULT_TEMPS, checkPairs, getNetworkSequences, getPlantConnections, iterationOutcome, mergePairPipes, missingResultTables, pairLabel,
    suggestPairs, targetFlow,
)
from .utility_functions.translations import tr, tr_msg
from .utility_functions.utility import sanitize_pg_identifier, write_plugin_settings
from .utility_functions.workers import WorkerLoadVersion

import datetime
import os
import psycopg2
import psycopg2.extras
import traceback

TIME_MODES = ['customer', 'customer_mdot', 'global']
EP_AGGREGATES = ['max', 'weighted']
DATE_FORMAT = 'yyyy-MM-dd hh:mm:ss'  # as in networkSimData.txt and the simulation dialog
PERIOD_KEYS = ('calc_time_from', 'calc_time_to', 'startup_time_from', 'startup_time_to')


def pipeName(catalog, pipe_id):
    return catalog[pipe_id]['name'] if pipe_id in catalog else str(pipe_id)


def periodErrors(periods):
    """Messages for periods {key of PERIOD_KEYS: 'yyyy-mm-dd hh:mm:ss'} whose start is not before their end."""
    errors = []
    if not periods['calc_time_from'] < periods['calc_time_to']:
        errors.append(tr_msg('The calculation period must end after it begins.'))
    if not periods['startup_time_from'] < periods['startup_time_to']:
        errors.append(tr_msg('The start-up period must end after it begins.'))
    return errors


class DynamicPipeSizingDialog(QDialog):
    def __init__(self, main):
        super().__init__()
        uic.loadUi(os.path.join(os.path.dirname(__file__), 'dynamic_pipe_sizing.ui'), self)
        # all sections are collapsible (state kept in the QGIS settings), the log and the iterations get the remaining height
        self.groupBox_info = QgsCollapsibleGroupBox(tr_msg('Description'))
        self.groupBox_info.setObjectName('groupBox_info')
        self.text_info = infoTextEdit(['dynamic_pipe_sizing_info'], 260)
        QVBoxLayout(self.groupBox_info).addWidget(self.text_info)
        self.groupBox_info.setCollapsed(True)  # default before the first use, afterwards the saved state
        self.verticalLayout_main.insertWidget(0, self.groupBox_info)
        self.verticalLayout_main.setStretchFactor(self.tabWidget_results, 1)
        self.main = main
        self.process_running = False
        self.run = None
        self.filling_pairs = False
        self.setupPairTable()
        self.setupPeriods()
        self.checkBox_presize.toggled.connect(self.updateEnabled)
        self.checkBox_dpSpezMax.toggled.connect(self.updateEnabled)
        self.checkBox_vMax.toggled.connect(self.updateEnabled)
        self.rbtn_newVersion.toggled.connect(self.updateEnabled)
        self.updateEnabled()
        self.btn_start.clicked.connect(self.start)
        self.btn_stop.clicked.connect(self.stop)
        self.btn_cancel.clicked.connect(self.close)
        self.btn_showIterations.clicked.connect(self.showSelectedIterations)
        self.btn_removeIterationLayers.clicked.connect(lambda: removeSizingLayers())
        self.btn_reloadIterations.clicked.connect(self.loadIterationTable)
        self.table_iterations.itemDoubleClicked.connect(lambda item: self.showSelectedIterations())
        self.table_iterations.setColumnCount(len(self.iterationHeaders()))
        self.table_iterations.setHorizontalHeaderLabels(self.iterationHeaders())
        self.table_iterations.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.ResizeToContents)
        self.table_iterations.verticalHeader().setVisible(False)

    # ------------------------------------------------------------------ simulation period and reference run
    def setupPeriods(self):
        """Calculation and start-up period (the settings of the simulation dialog) and the reference run, in the group Iteration."""
        self.dateedit_period = {}
        for row, (label, keys) in enumerate(((tr_msg('Calculation period'), PERIOD_KEYS[:2]), (tr_msg('Start-up period'), PERIOD_KEYS[2:]))):
            container = QWidget()
            layout = QHBoxLayout(container)
            layout.setContentsMargins(0, 0, 0, 0)
            for i, key in enumerate(keys):
                if i:
                    layout.addWidget(QLabel(tr_msg('to')))
                edit = QDateTimeEdit()
                edit.setCalendarPopup(True)
                edit.setDisplayFormat(DATE_FORMAT)
                self.dateedit_period[key] = edit
                layout.addWidget(edit)
            self.formLayout_iteration.insertRow(1 + row, label, container)
        self.checkBox_referenceRun = QCheckBox(tr_msg('Reference run before the sizing (iteration 0)'))
        self.checkBox_referenceRun.setObjectName('checkBox_referenceRun')
        self.checkBox_referenceRun.setToolTip(tr_msg('Simulate with the current pipes and evaluate every pair without changing a pipe, '
            'then stop: check the iteration 0 in the table and on the map, then start the sizing without the reference run.'))
        self.formLayout_iteration.insertRow(3, self.checkBox_referenceRun)

    def fillPeriods(self, config):
        """The periods saved for the version (networkSimData.txt, as shown by the simulation dialog)."""
        try:
            data = loadNetworkSimData(self.main.plugin_dir, config) or {}
        except Exception:
            QgsMessageLog.logMessage(traceback.format_exc(), 'Districts', MessageCritical)
            data = {}
        for key, edit in self.dateedit_period.items():
            if data.get(key):
                edit.setDateTime(QDateTime.fromString(data[key], DATE_FORMAT))

    def periods(self):
        return {key: edit.dateTime().toString(DATE_FORMAT) for key, edit in self.dateedit_period.items()}

    # ------------------------------------------------------------------ supply/return pairs
    def setupPairTable(self):
        self.table_pairs = QTableWidget(0, 4)
        self.table_pairs.setObjectName('table_pairs')
        self.table_pairs.setHorizontalHeaderLabels([tr_msg('Supply'), tr_msg('Return'), tr_msg('Supply temp. [°C]'), tr_msg('Return temp. [°C]')])
        self.table_pairs.setFrameShape(QFrame.Shape.Box)
        header = self.table_pairs.horizontalHeader()
        header.setSectionResizeMode(QHeaderView.ResizeMode.Interactive)
        header.setStretchLastSection(True)
        for col, width in enumerate((60, 60, 110)):
            self.table_pairs.setColumnWidth(col, width)
        self.table_pairs.verticalHeader().setVisible(False)
        self.table_pairs.setMaximumHeight(110)
        self.table_pairs.setToolTip(tr_msg('Supply and return pipe sequence of every circuit, suggested from the connections of the energy plants '
            '(k-th supply with k-th return connection). Every pair is balanced separately. The design temperatures are used for lines '
            'without a temperature result.'))
        self.table_pairs.itemChanged.connect(self.onPairEdited)
        self.btn_addPair = QPushButton('+')
        self.btn_addPair.setToolTip(tr_msg('Add a pair'))
        self.btn_addPair.clicked.connect(lambda: self.addPairRow(None, None, None, None))
        self.btn_removePair = QPushButton('−')
        self.btn_removePair.setToolTip(tr_msg('Remove the selected pairs'))
        self.btn_removePair.clicked.connect(self.removeSelectedPairs)
        buttons = QVBoxLayout()
        buttons.addWidget(self.btn_addPair)
        buttons.addWidget(self.btn_removePair)
        buttons.addStretch()
        container = QWidget()
        layout = QHBoxLayout(container)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(self.table_pairs)
        layout.addLayout(buttons)
        self.formLayout_network.insertRow(1, tr_msg('Supply/return pairs'), container)
        self.combo_network.currentTextChanged.connect(lambda text: self.fillPairs())

    def fillPairs(self):
        """Pairs suggested from the connections of the energy plants of the selected network."""
        if not self.combo_network.currentText():
            return
        try:
            cur = self.main.conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
            pairs, warnings = suggestPairs(getPlantConnections(cur, self.main.config, int(self.combo_network.currentText())))
        except Exception:
            QgsMessageLog.logMessage(traceback.format_exc(), 'Districts', MessageCritical)
            pairs, warnings = [], [tr_msg('The pairs could not be suggested: ') + traceback.format_exc().splitlines()[-1]]
        self.table_pairs.setRowCount(0)
        for pair in pairs:
            self.addPairRow(*pair)
        for warning in warnings:
            self.log(warning)

    def addPairRow(self, supply, ret, t_supply, t_return):
        self.filling_pairs = True
        row = self.table_pairs.rowCount()
        self.table_pairs.insertRow(row)
        for col, value in enumerate((supply, ret, t_supply, t_return)):
            self.table_pairs.setItem(row, col, QTableWidgetItem('' if value is None else '{:g}'.format(value)))
        self.filling_pairs = False

    def removeSelectedPairs(self):
        for row in sorted({index.row() for index in self.table_pairs.selectedIndexes()}, reverse=True):
            self.table_pairs.removeRow(row)

    def onPairEdited(self, item):
        # the design temperatures belong to the suggested connections, not to edited sequences
        if self.filling_pairs or item.column() >= 2:
            return
        self.filling_pairs = True
        for col in (2, 3):
            self.table_pairs.item(item.row(), col).setText('')
        self.filling_pairs = False

    def pairs(self):
        """([(supply, return, t_supply, t_return)], errors) of the pair table; temperatures None if not known."""
        result, errors = [], []
        for row in range(self.table_pairs.rowCount()):
            texts = [self.table_pairs.item(row, col).text().strip() if self.table_pairs.item(row, col) else '' for col in range(4)]
            try:
                supply, ret = int(texts[0]), int(texts[1])
                if supply < 1 or ret < 1:
                    raise ValueError
            except ValueError:
                errors.append(tr_msg('Row {} of the pairs: the sequences must be positive integers.').format(row + 1))
                continue
            try:
                temps = [float(t.replace(',', '.')) if t else None for t in texts[2:]]
            except ValueError:
                errors.append(tr_msg('Row {} of the pairs: the temperatures must be numbers.').format(row + 1))
                continue
            result.append((supply, ret, temps[0], temps[1]))
        if not result and not errors:
            errors.append(tr_msg('Please enter at least one supply/return pair.'))
        return result, errors

    # ------------------------------------------------------------------ iterations
    @staticmethod
    def iterationHeaders():
        return [tr_msg('Iteration'), tr_msg('Pair'), tr_msg('Critical time'), tr_msg('Weak point (plant)'), tr_msg('dp min [bar]'), tr_msg('dp max [bar]'),
            tr_msg('Spread [bar]'), tr_msg('Spread after sizing (est.) [bar]'), tr_msg('Quota [%]'), tr_msg('Changed lines'), tr_msg('Outcome')]

    def loadIterationTable(self):
        """Fills the table with the iterations saved in the loaded version."""
        self.table_iterations.setRowCount(0)
        try:
            summaries = loadIterations(self.main.config)
        except Exception:
            QgsMessageLog.logMessage(traceback.format_exc(), 'Districts', MessageCritical)
            summaries = []
        for summary in summaries:
            self.addIterationRow(summary)

    def addIterationRow(self, summary):
        for values in iterationRows(summary):
            row = self.table_iterations.rowCount()
            self.table_iterations.insertRow(row)
            for col, value in enumerate(values):
                # pressures in bar with 3 decimals (1 mbar)
                text = '' if value is None else '{:.3f}'.format(value) if isinstance(value, float) else str(value)
                self.table_iterations.setItem(row, col, QTableWidgetItem(text))

    def selectedIterations(self):
        """[(iteration, pair label)] of the selected rows"""
        rows = sorted({index.row() for index in self.table_iterations.selectedIndexes()})
        return [(int(self.table_iterations.item(row, 0).text()), self.table_iterations.item(row, 1).text()) for row in rows]

    def showSelectedIterations(self):
        iterations = self.selectedIterations()
        if not iterations:
            iface.messageBar().pushMessage(tr_msg("Info"), tr_msg('Please select one or more iterations in the table.'), level=MessageInfo)
            return
        try:
            cur = self.main.conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
            showIterations(cur, self.main.config, iterations)
            iface.mapCanvas().refresh()
        except Exception:
            QgsMessageLog.logMessage(traceback.format_exc(), 'Districts', MessageCritical)
            iface.messageBar().pushMessage(tr_msg("Error"), tr_msg('The iterations could not be shown: ') + traceback.format_exc().splitlines()[-1],
                level=MessageCritical)

    def updateEnabled(self):
        self.spin_dpSpezSetpoint.setEnabled(self.checkBox_presize.isChecked())
        self.checkBox_presizeOnly.setEnabled(self.checkBox_presize.isChecked())
        if not self.checkBox_presize.isChecked():
            self.checkBox_presizeOnly.setChecked(False)
        self.spin_dpSpezMax.setEnabled(self.checkBox_dpSpezMax.isChecked())
        self.spin_vMax.setEnabled(self.checkBox_vMax.isChecked())
        for widget in (self.lineEdit_versionName, self.lineEdit_versionDescription, self.label_versionName, self.label_versionDescription):
            widget.setEnabled(self.rbtn_newVersion.isChecked())

    def fillCombos(self, cur, config):
        cur.execute("""SELECT network FROM "{}".lines GROUP BY network ORDER BY network;""".format(config['versionName']))  # nosec B608
        self.combo_network.addItems([str(row['network']) for row in cur.fetchall()])
        self.combo_submodel.addItems(getUsedNetworkSubmodels(cur, config))
        self.lineEdit_versionName.setText(config['versionName'] + '_sizing')
        self.lineEdit_versionDescription.setText('Dynamic pipe sizing of version {}'.format(config['versionName']))
        self.fillPeriods(config)
        self.loadIterationTable()

    def parameters(self):
        return {
            'new_version': self.lineEdit_versionName.text().strip() if self.rbtn_newVersion.isChecked() else None,
            'description': self.lineEdit_versionDescription.text().strip(),
            'network': int(self.combo_network.currentText()),
            'submodel': self.combo_submodel.currentText(),
            'time_mode': TIME_MODES[self.combo_timeMode.currentIndex()],
            'ep_aggregate': EP_AGGREGATES[self.combo_epAggregate.currentIndex()],
            'min_share': self.spin_minShare.value() / 100.0,
            'tol_above': self.spin_tolAbove.value(),
            'tol_below': self.spin_tolBelow.value(),
            'weighted': self.checkBox_weighted.isChecked(),
            'dp_spez_setpoint': self.spin_dpSpezSetpoint.value() if self.checkBox_presize.isChecked() else None,
            'presize_only': self.checkBox_presizeOnly.isChecked(),
            'dp_spez_max': self.spin_dpSpezMax.value() if self.checkBox_dpSpezMax.isChecked() else None,
            'v_max': self.spin_vMax.value() if self.checkBox_vMax.isChecked() else None,
            'max_iter': self.spin_maxIter.value(),
            'pairs': self.pairs()[0],
            'build_first': self.checkBox_buildFirst.isChecked(),
            'show_map': self.checkBox_showMap.isChecked(),
            'periods': self.periods(),
            'reference_run': self.checkBox_referenceRun.isChecked(),
        }

    def log(self, message):
        self.textEdit_log.appendPlainText('{}  {}'.format(datetime.datetime.now().strftime('%H:%M:%S'), message))

    def update_progress(self, progress):
        self.progress.setValue(progress)

    def setRunning(self, running):
        self.process_running = running
        self.btn_start.setEnabled(not running)
        self.btn_stop.setEnabled(running)
        # while running the iterations are added to the table and shown by the run itself (option)
        for widget in (self.btn_showIterations, self.btn_reloadIterations):
            widget.setEnabled(not running)
        for box in (self.groupBox_version, self.groupBox_network, self.groupBox_balancing, self.groupBox_sizing, self.groupBox_iteration):
            box.setEnabled(not running)

    def start(self):
        if not self.combo_network.currentText() or not self.combo_submodel.currentText():
            iface.messageBar().pushMessage(tr_msg("Info"), tr_msg('Please select a network and a submodel!'), level=MessageInfo)
            return
        pairs, errors = self.pairs()
        errors += periodErrors(self.periods())
        skipped = {}
        if not errors:
            try:
                cur = self.main.conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
                errors, skipped = checkPairs([(s, r) for s, r, _, _ in pairs], *getNetworkSequences(cur, self.main.config, int(self.combo_network.currentText())))
            except Exception:
                QgsMessageLog.logMessage(traceback.format_exc(), 'Districts', MessageCritical)
                errors = [tr_msg('The pairs could not be checked: ') + traceback.format_exc().splitlines()[-1]]
        if errors:
            QMessageBox.warning(self, self.windowTitle(), '\n'.join(errors))
            return
        version = self.main.config['versionName']
        new_version = self.parameters()['new_version']
        if self.rbtn_newVersion.isChecked():
            if not new_version or sanitize_pg_identifier(new_version) != new_version:
                QMessageBox.warning(self, self.windowTitle(), tr_msg('Please enter a version name with a-z, 0-9 and _ only.'))
                return
            cur = self.main.conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
            cur.execute("""SELECT 1 FROM pg_namespace WHERE nspname = %s UNION SELECT 1 FROM public.versionhandling WHERE name = %s;""", (new_version, new_version))
            if cur.fetchone():
                QMessageBox.warning(self, self.windowTitle(), tr_msg('Version "{}" does already exist.').format(new_version))
                return
            question = tr_msg('A child version "{}" of version "{}" will be created and loaded, its pipes will be sized. Continue?').format(new_version, version)
        else:
            question = tr_msg('The pipe bundles of the lines of the loaded version "{}" will be overridden. Continue?').format(version)
        if self.checkBox_referenceRun.isChecked():
            question = tr_msg('Reference run: the network of version "{}" is simulated with its current pipes, no pipe is changed. Continue?').format(
                new_version if self.rbtn_newVersion.isChecked() else version)
        answer = QMessageBox.question(self, self.windowTitle(), question)
        if answer != QMessageBox.StandardButton.Yes:
            return
        self.textEdit_log.clear()
        for (s, r), n in sorted(skipped.items()):
            if n:
                self.log(tr_msg('Pair {}: {} customers without the connections {} and {} are not included.').format(pairLabel((s, r)), n, s, r))
        self.setRunning(True)
        self.run = DynamicPipeSizingRun(self, self.main, dict(self.parameters(), skipped={pairLabel(pair): n for pair, n in skipped.items()}))
        self.run.start()

    def stop(self):
        if not self.run:
            return
        if self.run.stop_requested:
            self.run.finish(tr_msg('Aborted by the user; a running simulation or worker is not interrupted.'), error=True)
            return
        self.run.stop_requested = True
        self.btn_stop.setText(tr_msg('Abort now'))
        self.log(tr_msg('Stop requested, the iteration stops after the current step (press again to abort now).'))

    def finished(self):
        self.setRunning(False)
        self.btn_stop.setText(tr_msg('Stop after this step'))

    def closeEvent(self, event):
        if self.process_running:
            QMessageBox.information(self, self.windowTitle(), tr_msg('The iteration is still running. Please stop or abort it first.'))
            event.ignore()
        else:
            event.accept()


class DynamicPipeSizingRun(QObject):
    """State machine of the iteration; the steps are started as workers and continued by their signals."""

    def __init__(self, dlg, main, parms):
        super().__init__()
        self.dlg = dlg
        self.main = main
        self.plugin_dir = main.plugin_dir
        self.parms = parms
        self.iteration = 0
        self.stop_requested = False
        self.done = False
        self.stage = None
        self.states = []
        self.sim_failed = False
        self.finished_sims = 0
        self.dlg_run = None
        self.dlg_load = None
        self.worker_build = None

    @property
    def config(self):
        # loading a version replaces main.config, so it is always read from main
        return self.main.config

    # ------------------------------------------------------------------ control
    def start(self):
        p = self.parms
        self.dlg.log(tr_msg('Parameters: ') + ', '.join('{}={}'.format(k, v) for k, v in p.items() if k not in ('network', 'submodel', 'new_version', 'description', 'skipped')))
        if p['new_version']:
            self.createVersion()
        else:
            self.startIteration()

    def startIteration(self):
        p = self.parms
        self.dlg.log(tr_msg('Version {}, network {}, submodel {}').format(self.config['versionName'], p['network'], p['submodel']))
        self.iteration = 0 if p['reference_run'] else 1
        self.started = datetime.datetime.now().isoformat(timespec='seconds')
        # iterations of a previous run (or copied from the parent version) do not belong to this run; the reference
        # run (iteration 0) simulated in this version is kept for the sizing that follows it
        deleteIterations(self.config, keep_reference=not p['reference_run'] and not p['new_version'])
        removeSizingLayers()
        self.dlg.loadIterationTable()
        if p['build_first']:
            self.build()
        else:
            self.simulate()

    # ------------------------------------------------------------------ 0. new child version
    def createVersion(self):
        from .ida_ph import getVersionData, importData
        p = self.parms
        self.stage = 'version'
        base = self.config['versionName']
        self.dlg.log(tr_msg('Creating the child version {} of {} ...').format(p['new_version'], base))
        try:
            createChildVersion(self.main.cur, self.config, self.plugin_dir, p['new_version'], p['description'])
            importData(self.main.model, getVersionData(self.main.cur))
            self.main.dlg.treeViewVersions.expandAll()
            self.main.config['versionName'] = p['new_version']
            write_plugin_settings(self.main.config)
            self.loadVersion()
        except Exception:
            self.onException()

    def loadVersion(self):
        """Loads the new version like ida_ph.loadVersion and continues when the version worker has finished."""
        from .ida_ph import get_item_by_text, highlight_item, loadVersionLayers
        self.dlg.log(tr_msg('Loading version {} ...').format(self.config['versionName']))
        loadVersionLayers(self.config, self.main.cur, self.plugin_dir)
        item = get_item_by_text(self.config['versionName'], self.main)
        if item:
            highlight_item(item, self.main.model.invisibleRootItem())
            self.main.dlg.treeViewVersions.viewport().update()
        self.worker_version = WorkerLoadVersion(config=self.config, cur=self.main.cur, dlg=self.main.dlg)
        self.worker_version.signals.error.connect(self.onError)
        self.worker_version.signals.finished.connect(self.onVersionLoaded)
        QThreadPool.globalInstance().start(self.worker_version)

    @pyqtSlot(str)
    def onVersionLoaded(self, message):
        from .ida_ph import finishedLoadVersion
        if self.done or self.stage != 'version':
            return
        finishedLoadVersion(self.main)
        if self.config['versionName'] != self.parms['new_version']:
            self.finish(tr_msg('The new version {} could not be loaded.').format(self.parms['new_version']), error=True)
            return
        self.startIteration()

    def finish(self, message, error=False):
        if self.done:
            return
        self.done = True
        self.dlg.log(message)
        self.dlg.update_progress(100 if not error else 0)
        iface.messageBar().pushMessage(tr_msg("Error") if error else tr_msg("Info"), tr_msg('Dynamic pipe sizing: ') + message, level=MessageCritical if error else MessageInfo)
        self.dlg.finished()

    def checkStop(self):
        if self.done:
            return True
        if self.stop_requested:
            self.finish(tr_msg('Stopped by the user after iteration {}.').format(self.iteration))
            return True
        return False

    def progress(self, step):
        """step 0..3 within the iteration"""
        if self.iteration == 0:
            self.dlg.update_progress(int(step / 4 * 100))
            return
        self.dlg.update_progress(int(((self.iteration - 1) * 4 + step) / (self.parms['max_iter'] * 4) * 100))

    # ------------------------------------------------------------------ 1. build network model
    def build(self):
        if self.checkStop():
            return
        self.progress(0)
        self.stage = 'build'
        self.dlg.log(tr_msg('Iteration {}: building the network model ...').format(self.iteration))
        try:
            self.worker_build = WorkerBuildNetworkModel(main=self.main, config=self.config, plugin_dir=self.plugin_dir, dlg=self.dlg,
                networks=[str(self.parms['network'])], submodels=[self.parms['submodel']])
            self.worker_build.signals.error.connect(self.onError)
            self.worker_build.signals.finished.connect(self.onBuildFinished)
            QThreadPool.globalInstance().start(self.worker_build)
        except Exception:
            self.onException()

    @pyqtSlot(str)
    def onBuildFinished(self, message):
        if self.done or self.stage != 'build':
            return
        self.dlg.log('  ' + message)
        self.simulate()

    # ------------------------------------------------------------------ 2. simulation
    def simulate(self):
        if self.checkStop():
            return
        self.progress(1)
        self.stage = 'simulate'
        self.dlg.log(tr_msg('Iteration {}: running the simulation ...').format(self.iteration))
        try:
            self.sim_failed = False
            self.finished_sims = 0
            self.dlg_run = RunNetworkModelDialog(self.plugin_dir, self.config)
            self.dlg_run.combo_submodels.addItem(tr('@default', 'check_all_items'))
            self.dlg_run.combo_submodels.addItem(self.parms['submodel'])
            self.dlg_run.combo_submodels.setItemChecked(1, True)
            # the periods of the sizing dialog; runModel saves them with the other settings of the version
            for key, attr in zip(PERIOD_KEYS, ('dateedit_calcFrom', 'dateedit_calcTo', 'dateedit_startupFrom', 'dateedit_startupTo')):
                getattr(self.dlg_run, attr).setDateTime(QDateTime.fromString(self.parms['periods'][key], DATE_FORMAT))
            # redirect the signals of the simulation workers to this object
            self.dlg_run.updateStatusBar = self.onSimStatus
            self.dlg_run.show_error_message = self.onSimError
            self.dlg_run.update_finished = self.onSimFinished
            runModel(self.dlg_run, self.plugin_dir, self.config)
            if not self.dlg_run.process_running:
                self.finish(tr_msg('The simulation could not be started (see message bar).'), error=True)
        except Exception:
            self.onException()

    @pyqtSlot(str)
    def onSimStatus(self, message):
        if message == tr_msg('Simulation failed'):
            self.sim_failed = True
        if message != tr_msg('Running'):
            self.dlg.log('  ' + message)

    @pyqtSlot(str)
    def onSimError(self, message):
        self.sim_failed = True
        self.dlg.log(tr_msg('  Error: ') + message)

    @pyqtSlot(str)
    def onSimFinished(self, message):
        if self.done or self.stage != 'simulate':
            return
        self.finished_sims += 1
        if self.finished_sims < getattr(self.dlg_run, 'n_sims', 1):
            return
        if self.sim_failed:
            self.finish(tr_msg('The simulation failed in iteration {}.').format(self.iteration), error=True)
        else:
            self.load()

    # ------------------------------------------------------------------ 3. load results
    def load(self):
        if self.checkStop():
            return
        self.progress(2)
        self.stage = 'load'
        self.dlg.log(tr_msg('Iteration {}: loading the results ...').format(self.iteration))
        try:
            self.dlg_load = LoadResultsDialog(self.main.dlg)
            self.dlg_load.combo_submodels.addItem(tr('@default', 'check_all_items'))
            self.dlg_load.combo_submodels.addItem(self.parms['submodel'])
            self.dlg_load.combo_submodels.setItemChecked(1, True)
            self.dlg_load.update_finished = self.onLoadFinished
            loadResults(self.dlg_load, self.main)
            if not self.dlg_load.process_running:
                self.finish(tr_msg('The results could not be loaded (see message bar).'), error=True)
        except Exception:
            self.onException()

    @pyqtSlot(str)
    def onLoadFinished(self, message):
        if self.done or self.stage != 'load':
            return
        self.dlg.log('  ' + message)
        self.evaluate()

    # ------------------------------------------------------------------ 4. pipe sizing and hydraulic balancing
    def evaluate(self):
        if self.checkStop():
            return
        self.progress(3)
        self.stage = 'evaluate'
        p = self.parms
        self.dlg.log(tr_msg('Iteration {}: flow tracing, pipe sizing and hydraulic balancing ...').format(self.iteration))
        try:
            conn = dbConnect(self.config, True)
            cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
            missing = missingResultTables(cur, self.config, [(s, r) for s, r, _, _ in p['pairs']])
            if missing:
                conn.close()
                self.finish(tr_msg('Line results missing: {}. Request the line mass flow and temperature outputs of the network and run again.').format(
                    ', '.join(missing)), error=True)
                return
            results = []
            for s, r, t_s, t_r in p['pairs']:
                results.append(self.evaluatePair(cur, (s, r), (DEFAULT_TEMPS[0] if t_s is None else t_s, DEFAULT_TEMPS[1] if t_r is None else t_r)))
            if self.iteration == 0:
                conn.close()
                self.saveIteration(results, 'reference', {}, {})
                self.finishReference()
                return

            # one decision over all pairs: the lines get the new pipes of every pair, the other pipes of the bundle stay
            bundles = getPipeBundles(cur)
            line_bundles = {lid: line['bundle'] for _, _, res, _ in results for lid, line in res['lines'].items()}
            current = {lid: dict(bundles.get(bid, {})) for lid, bid in line_bundles.items()}
            merged = mergePairPipes(current, [opt['pipes'] for _, _, _, opt in results])
            outcome, changed, state = iterationOutcome(current, merged, self.states, self.iteration, p['max_iter'])
            self.saveIteration(results, outcome, current, changed if outcome in ('changed', 'max_iter') else {})
            if outcome == 'converged':
                self.finish(tr_msg('Converged in iteration {}: the pipe dimensions do not change anymore.').format(self.iteration))
                return
            catalog = results[0][2]['catalog']
            for lid, new in sorted(changed.items()):
                seqs = [seq for seq in sorted(new) if new[seq] != current[lid].get(seq)]
                self.dlg.log(tr_msg('    line {}: {} -> {}').format(lid, ', '.join(pipeName(catalog, current[lid].get(seq)) for seq in seqs),
                    ', '.join(pipeName(catalog, new[seq]) for seq in seqs)))
            if outcome == 'oscillation':
                self.finish(tr_msg('Stopped in iteration {}: the pipe dimensions repeat a previous iteration (oscillation), the lines are not changed.').format(self.iteration), error=True)
                return
            self.states.append(state)

            line_bundles, new_bundles = getOrCreatePipeBundles(cur, line_bundles, {lid: merged[lid] for lid in changed})
            for lid, bid in line_bundles.items():
                cur.execute("""UPDATE "{}".lines SET pipe_bundle_type_id = %s WHERE id = %s;""".format(self.config['versionName']), (bid, lid))  # nosec B608
            self.dlg.log(tr_msg('  {} lines changed{}').format(len(line_bundles), tr_msg(', new pipe bundle types: {}').format(new_bundles) if new_bundles else ''))
            conn.close()
            iface.mapCanvas().refreshAllLayers()

            if self.iteration >= p['max_iter']:
                self.finish(tr_msg('Maximal number of iterations reached; the lines contain the pipes of iteration {}, the network model is not yet built and simulated with them.').format(self.iteration))
                return
            self.iteration += 1
            self.build()
        except Exception:
            self.onException()

    def evaluatePair(self, cur, pair, temps):
        """Flow tracing, pipe sizing and hydraulic balancing of one pair (circuit). Returns (pair, temps, res, opt)."""
        p = self.parms
        label = pairLabel(pair)
        res = getCustomerLinePressure(cur, self.config, network=p['network'], pair=pair, default_temps=temps, time_mode=p['time_mode'],
            ep_aggregate=p['ep_aggregate'], min_share=p['min_share'])
        lines, catalog = res['lines'], res['catalog']
        opt = optimizePipeDiameters(res['c_lid'], lines, catalog, tol_above=p['tol_above'], tol_below=p['tol_below'],
            weighted=p['weighted'], v_max=p['v_max'], dp_spez_max=p['dp_spez_max'],
            dp_spez_setpoint=p['dp_spez_setpoint'], presize_only=p['presize_only'])
        dps = [val[0] for val in res['c_lid'].values() if val[0] is not None]
        self.dlg.log(tr_msg('  pair {}: {} lines, {} customers').format(label, len(lines), len(res['c_lid'])))
        self.dlg.log(tr_msg('  simulated: critical time {}, weak point customer {} (plant {}), dp substations {:.0f} ... {:.0f} Pa').format(
            res['time'], res['cid_dp'], res['epid_dp'], min(dps), max(dps)))
        self.dlg.log(tr_msg('  estimated after sizing: weak point customer {}, quota {:.0%}, spread {:.0f} Pa, pre-sized {}, hydraulic balancing steps {}').format(
            opt['cid_weak'], opt['quota'], opt['spread'], len(opt['presize']), len(opt['history'])))
        n_default = sum(1 for line in lines.values() if any(pipe['temp_default'] for pipe in line['pipes'].values()))
        if n_default:
            self.dlg.log(tr_msg('  pair {}: {} lines without a temperature result, {:g} / {:g} °C used').format(label, n_default, temps[0], temps[1]))
        mdot, peak, res['target_no_flow'] = targetFlow(res, opt['cid_weak'])
        if res['target_no_flow']:
            self.dlg.log(tr_msg('  Warning: pair {}: target customer {} has almost no flow at its critical time ({:.3g} of {:.3g} kg/s); check the simulation period.').format(
                label, opt['cid_weak'], mdot, peak))
        self.saveResult(res, opt, pair)
        return pair, temps, res, opt

    def finishReference(self):
        """End of the reference run: the sizing is a second start in the same version, without the reference run."""
        if self.parms['new_version']:
            self.dlg.rbtn_overrideVersion.setChecked(True)
            self.dlg.log(tr_msg('The sizing continues in version {}: "Override the pipes of the loaded version" is selected.').format(self.config['versionName']))
        self.dlg.checkBox_referenceRun.setChecked(False)
        self.finish(tr_msg('Reference run finished: check the iterations, then start the sizing without the reference run.'))

    def saveIteration(self, results, outcome, current, changed):
        """Saves the summary of the iteration in the version folder, adds it to the table and shows it on the map (option).
        results = [(pair, temps, res, opt)], current = pipes of the lines before the sizing, changed = lines with new pipes."""
        try:
            pairs = []
            for pair, temps, res, opt in results:
                changed_pair = {lid for lid, new in opt['pipes'].items() if lid in changed and any(current[lid].get(seq) != pid for seq, pid in new.items())}
                pairs.append(pairSummary(pair, temps, res, opt, changed_pair, self.parms['skipped'].get(pairLabel(pair), 0),
                    reference=outcome == 'reference', target_no_flow=res.get('target_no_flow', False)))
            summary = iterationSummary(self.iteration, self.started, pairs, outcome, len(changed))
            saveIteration(self.config, summary)
            self.dlg.addIterationRow(summary)
            if self.parms['show_map']:
                cur = self.main.conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
                # the class bounds of all iterations so far; the earlier iterations stay in the layer tree, hidden
                summaries = loadIterations(self.config)
                for earlier in summaries[:-1]:
                    showIteration(cur, self.config, earlier, summaries, visible=False)
                showIteration(cur, self.config, summary, summaries)
        except Exception:
            QgsMessageLog.logMessage(traceback.format_exc(), 'Districts', MessageCritical)
            self.dlg.log(tr_msg('  the results of the iteration could not be saved or shown: ') + traceback.format_exc().splitlines()[-1])

    def saveResult(self, res, opt, pair):
        """Saves c_lid of the pair of the simulated state and after the sizing in the version directory."""
        try:
            path = os.path.join(self.config['pathProjects'], self.config['projectName'], 'versions', self.config['versionName'])
            saveCLidPressure(res['c_lid'], os.path.join(path, 'dynamic_sizing_iter{}_c_lid_{}_{}.json'.format(self.iteration, *pair)))
            saveCLidPressure(opt['c_lid'], os.path.join(path, 'dynamic_sizing_iter{}_c_lid_sized_{}_{}.json'.format(self.iteration, *pair)))
        except Exception:
            self.dlg.log(tr_msg('  c_lid could not be saved: ') + traceback.format_exc().splitlines()[-1])

    # ------------------------------------------------------------------ errors
    @pyqtSlot(str)
    def onError(self, message):
        """Errors of the network model build: the worker does not emit finished, so the iteration is stopped."""
        self.dlg.log(tr_msg('  Error: ') + message)
        if self.stage == 'build':
            self.finish(tr_msg('Building the network model failed in iteration {}.').format(self.iteration), error=True)

    def onException(self):
        QgsMessageLog.logMessage(traceback.format_exc(), 'Districts', MessageCritical)
        self.finish(tr_msg('Error in iteration {}: {}').format(self.iteration, traceback.format_exc().splitlines()[-1]), error=True)
