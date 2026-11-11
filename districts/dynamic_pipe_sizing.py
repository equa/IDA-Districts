"""Dynamic pipe sizing: iteration of building the network model, simulation, loading the results, pipe sizing and
hydraulic balancing (utility_functions.hydraulic_balancing) until the pipe dimensions do not change anymore.
The workflow is described in the info text dynamic_pipe_sizing_info (i18n/districts_*.ts)."""
from qgis.PyQt import uic
from qgis.PyQt.QtCore import QObject, QThreadPool, pyqtSlot
from qgis.PyQt.QtWidgets import QDialog, QHeaderView, QMessageBox, QTableWidgetItem, QVBoxLayout
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
from .utility_functions.dynamic_sizing_results import (
    deleteIterations, iterationRow, iterationSummary, loadIterations, removeSizingLayers, saveIteration, showIteration, showIterations,
)
from .utility_functions.hydraulic_balancing import (
    createChildVersion, getCustomerLinePressure, getOrCreatePipeBundles, optimizePipeDiameters, saveCLidPressure,
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

    @staticmethod
    def iterationHeaders():
        return [tr_msg('Iteration'), tr_msg('Critical time'), tr_msg('Weak point (plant)'), tr_msg('dp min [bar]'), tr_msg('dp max [bar]'),
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
        row = self.table_iterations.rowCount()
        self.table_iterations.insertRow(row)
        for col, value in enumerate(iterationRow(summary)):
            # pressures in bar with 3 decimals (1 mbar)
            text = '' if value is None else '{:.3f}'.format(value) if isinstance(value, float) else str(value)
            self.table_iterations.setItem(row, col, QTableWidgetItem(text))

    def selectedIterations(self):
        rows = sorted({index.row() for index in self.table_iterations.selectedIndexes()})
        return [int(self.table_iterations.item(row, 0).text()) for row in rows]

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
            'build_first': self.checkBox_buildFirst.isChecked(),
            'show_map': self.checkBox_showMap.isChecked(),
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
        answer = QMessageBox.question(self, self.windowTitle(), question)
        if answer != QMessageBox.StandardButton.Yes:
            return
        self.textEdit_log.clear()
        self.setRunning(True)
        self.run = DynamicPipeSizingRun(self, self.main, self.parameters())
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
        self.dlg.log(tr_msg('Parameters: ') + ', '.join('{}={}'.format(k, v) for k, v in p.items() if k not in ('network', 'submodel', 'new_version', 'description')))
        if p['new_version']:
            self.createVersion()
        else:
            self.startIteration()

    def startIteration(self):
        p = self.parms
        self.dlg.log(tr_msg('Version {}, network {}, submodel {}').format(self.config['versionName'], p['network'], p['submodel']))
        self.iteration = 1
        self.started = datetime.datetime.now().isoformat(timespec='seconds')
        # iterations of a previous run (or copied from the parent version) do not belong to this run
        deleteIterations(self.config)
        removeSizingLayers()
        self.dlg.table_iterations.setRowCount(0)
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
            res = getCustomerLinePressure(cur, self.config, network=p['network'], time_mode=p['time_mode'],
                ep_aggregate=p['ep_aggregate'], min_share=p['min_share'])
            lines, catalog = res['lines'], res['catalog']
            opt = optimizePipeDiameters(res['c_lid'], lines, catalog, tol_above=p['tol_above'], tol_below=p['tol_below'],
                weighted=p['weighted'], v_max=p['v_max'], dp_spez_max=p['dp_spez_max'],
                dp_spez_setpoint=p['dp_spez_setpoint'], presize_only=p['presize_only'])
            dps = [val[0] for val in res['c_lid'].values() if val[0] is not None]
            self.dlg.log(tr_msg('  simulated: critical time {}, weak point customer {} (plant {}), dp substations {:.0f} ... {:.0f} Pa').format(
                res['time'], res['cid_dp'], res['epid_dp'], min(dps), max(dps)))
            self.dlg.log(tr_msg('  estimated after sizing: weak point customer {}, quota {:.0%}, spread {:.0f} Pa, pre-sized {}, hydraulic balancing steps {}').format(
                opt['cid_weak'], opt['quota'], opt['spread'], len(opt['presize']), len(opt['history'])))
            self.saveResult(res, opt)

            current = {lid: {seq: pipe['pipe_id'] for seq, pipe in line['pipes'].items()} for lid, line in lines.items()}
            changed = {lid: new for lid, new in opt['pipes'].items() if new != current[lid]}
            state = sorted((lid, sorted(pipes.items())) for lid, pipes in opt['pipes'].items())
            if not changed:
                outcome = 'converged'
            elif state in self.states:
                outcome = 'oscillation'
            else:
                outcome = 'max_iter' if self.iteration >= p['max_iter'] else 'changed'
            self.saveIteration(res, opt, outcome, changed if outcome in ('changed', 'max_iter') else {})
            if outcome == 'converged':
                self.finish(tr_msg('Converged in iteration {}: the pipe dimensions do not change anymore.').format(self.iteration))
                return
            for lid, new in sorted(changed.items()):
                self.dlg.log(tr_msg('    line {}: {} -> {}').format(lid, catalog[current[lid][min(current[lid])]]['name'], catalog[new[min(new)]]['name']))
            if outcome == 'oscillation':
                self.finish(tr_msg('Stopped in iteration {}: the pipe dimensions repeat a previous iteration (oscillation), the lines are not changed.').format(self.iteration), error=True)
                return
            self.states.append(state)

            line_bundles, new_bundles = getOrCreatePipeBundles(cur, lines, opt['pipes'])
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

    def saveIteration(self, res, opt, outcome, changed):
        """Saves the summary of the iteration in the version folder, adds it to the table and shows it on the map (option)."""
        try:
            summary = iterationSummary(self.iteration, self.started, res, opt, outcome, changed)
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

    def saveResult(self, res, opt):
        """Saves c_lid of the simulated state and after the sizing in the version directory."""
        try:
            path = os.path.join(self.config['pathProjects'], self.config['projectName'], 'versions', self.config['versionName'])
            saveCLidPressure(res['c_lid'], os.path.join(path, 'dynamic_sizing_iter{}_c_lid.json'.format(self.iteration)))
            saveCLidPressure(opt['c_lid'], os.path.join(path, 'dynamic_sizing_iter{}_c_lid_sized.json'.format(self.iteration)))
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
