# coding=utf-8
"""'Set pipes' of the cost optimization and the hydraulic balancing (OpenSpec change cost-optimization, D24): the pipes
simulated in a selected iteration, into a new child version (default) or into the loaded version. Nothing is simulated."""
import glob
import os
import traceback

import psycopg2.extras
from qgis.core import QgsMessageLog
from qgis.PyQt.QtCore import QObject, QThreadPool, pyqtSlot
from qgis.PyQt.QtWidgets import (
    QDialog, QDialogButtonBox, QHBoxLayout, QLabel, QLineEdit, QMessageBox, QRadioButton, QVBoxLayout,
)

from .compat import MessageCritical
from .hydraulic_balancing import createChildVersion, getOrCreatePipeBundles, getPipeCatalog
from .network_stages import writeBundles
from .translations import tr_msg
from .utility import sanitize_pg_identifier

# files of a run that belong to the parent version, not to a child made from one of its iterations
RUN_FILE_PATTERNS = ('cost_optimization_iter*.json', 'dynamic_sizing_iter*.json', 'cost_optimization_run.json', 'dynamic_sizing_run.json')


def costIterationPipes(row):
    """{'bundles': {lid: bid}} simulated in a cost optimization iteration, or None (file without a state)"""
    state = row.get('state') or {}
    bundles = {int(lid): int(bid) for lid, bid in state.items() if bid is not None}
    return {'bundles': bundles} if bundles else None


def balancingIterationPipes(cur, summary):
    """{'pipes': {lid: {seq: pipe_id}}} simulated in a hydraulic balancing iteration. Iterations saved before the state
    existed have only the supply pipe name per pair: that pipe then stands for both pipes of the pair ('by_name')."""
    state = summary.get('state') or {}
    if state:
        return {'pipes': {int(lid): {int(seq): int(pid) for seq, pid in seqs.items()} for lid, seqs in state.items()}}
    by_name = {p['name']: pid for pid, p in getPipeCatalog(cur).items()}
    pipes = {}
    for pair in summary.get('pairs', []):
        for lid, line in pair.get('lines', {}).items():
            pid = by_name.get(line.get('pipe'))
            if pid is not None:
                pipes.setdefault(int(lid), {}).update({int(pair['supply']): pid, int(pair['return']): pid})
    return {'pipes': pipes, 'by_name': True} if pipes else None


def applyPipes(cur, schema, target):
    """sets the pipes of target ({'bundles'} or {'pipes'}) on the lines of the schema; returns (lines changed, new bundle ids)"""
    from .ground_collectors import notCollector
    cur.execute('SELECT id, pipe_bundle_type_id AS bid FROM "{}".lines l WHERE {};'.format(schema, notCollector('l')))  # nosec B608
    current = {row['id']: row['bid'] for row in cur.fetchall()}
    if 'bundles' in target:
        new = {lid: bid for lid, bid in target['bundles'].items() if lid in current and current[lid] != bid}
        new_ids = []
    else:
        pipes = {lid: p for lid, p in target['pipes'].items() if lid in current}
        new, new_ids = getOrCreatePipeBundles(cur, {lid: current[lid] for lid in pipes}, pipes)
    if new:
        psycopg2.extras.execute_values(cur, 'UPDATE "{}".lines l SET pipe_bundle_type_id = v.bid FROM (VALUES %s) AS v(id, bid) WHERE l.id = v.id;'.format(schema),  # nosec B608
                                       sorted(new.items()))
    return len(new), new_ids


def removeRunFiles(config, version):
    folder = os.path.join(config['pathProjects'] + config['projectName'], 'versions', version)
    for pattern in RUN_FILE_PATTERNS:
        for path in glob.glob(os.path.join(folder, pattern)):
            os.remove(path)


def createVersionWithIteration(cur, config, plugin_dir, name, iteration, feature, target):
    createChildVersion(cur, config, plugin_dir, name, '{} of version {}, iteration {}'.format(feature, config['versionName'], iteration))
    removeRunFiles(config, name)
    return applyPipes(cur, name, target)


class SetPipesDialog(QDialog):
    def __init__(self, parent, version, iteration):
        super().__init__(parent)
        self.setWindowTitle(tr_msg('Set the pipes of iteration {}').format(iteration))
        layout = QVBoxLayout(self)
        layout.addWidget(QLabel(tr_msg('The pipes simulated in iteration {} are set on the lines; nothing is simulated.').format(iteration)))
        self.rbtn_child = QRadioButton(tr_msg('Into a new child version'))
        self.rbtn_child.setChecked(True)
        self.edit_name = QLineEdit('{}_it{}'.format(version, iteration))
        row = QHBoxLayout()
        row.addWidget(self.rbtn_child)
        row.addWidget(self.edit_name, 1)
        layout.addLayout(row)
        self.rbtn_this = QRadioButton(tr_msg('Into this version ({})').format(version))
        layout.addWidget(self.rbtn_this)
        self.label_warning = QLabel(tr_msg('The current pipes of the version are overwritten; its results do not match the pipes until it is simulated again.'))
        self.label_warning.setWordWrap(True)
        self.label_warning.setStyleSheet('color: #a05000;')
        layout.addWidget(self.label_warning)
        self.rbtn_this.toggled.connect(self.update)
        buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)
        self.update()

    def update(self):
        self.edit_name.setEnabled(self.rbtn_child.isChecked())
        self.label_warning.setVisible(self.rbtn_this.isChecked())

    def childName(self):
        return self.edit_name.text().strip() if self.rbtn_child.isChecked() else None


class SetPipes(QObject):
    """the flow of 'Set pipes': dialog, then the update of this version or a child version created and loaded in the
    background; log(message) reports, done() follows a successful end (e.g. to reload the dialog)"""

    def __init__(self, owner, main, feature, log, done=None):
        super().__init__(owner)
        self.owner, self.main, self.feature, self.log, self.done = owner, main, feature, log, done

    def run(self, iteration, target, ask=True, stages=None):
        """stages: [(version, target)] of the other stages of a network built in stages (network-stages D4, D7): each gets
        its own pipes (the line IDs differ), into itself or into a child version, the version handling trigger off"""
        self.stages = [(v, t) for v, t in (stages or []) if v != self.main.config['versionName']]
        if not target:
            QMessageBox.information(self.owner, self.feature, tr_msg('Iteration {} has no saved pipes (run before this was saved).').format(iteration))
            return
        dlg = SetPipesDialog(self.owner, self.main.config['versionName'], iteration)
        if ask and not dlg.exec():
            return
        if target.get('by_name'):
            self.log(tr_msg('Iteration {} saved only the supply pipe of each pair; it is set for both pipes of the pair.').format(iteration))
        name = dlg.childName()
        if name is None:
            if ask and QMessageBox.question(self.owner, self.feature, tr_msg('Overwrite the pipes of version {} with those of iteration {}?').format(
                    self.main.config['versionName'], iteration)) != QMessageBox.StandardButton.Yes:
                return
            try:
                n, new_ids = applyPipes(self.main.cur, self.main.config['versionName'], target)
                for version, stage_target in self.stages:
                    writeBundles(self.main.cur, version, stage_target['bundles'])
            except Exception:
                QgsMessageLog.logMessage(traceback.format_exc(), 'Districts', MessageCritical)
                self.log(tr_msg('The pipes could not be set: ') + traceback.format_exc().splitlines()[-1])
                return
            self.finished(iteration, n, new_ids, self.main.config['versionName'])
            return
        if sanitize_pg_identifier(name) != name:
            self.log(tr_msg('Invalid version name "{}" (only a-z, 0-9 and _)').format(name))
            return
        from ..representative_periods import startTask
        self.name, self.iteration = name, iteration
        self.log(tr_msg('Creating the child version {} of {} with the pipes of iteration {} ...').format(name, self.main.config['versionName'], iteration))
        config, plugin_dir, feature = dict(self.main.config), self.main.plugin_dir, self.feature
        stages = list(self.stages)

        def create(cur):
            # the other stages first: their child versions are not loaded
            for version, stage_target in stages:
                createVersionWithIteration(cur, dict(config, versionName=version), plugin_dir, '{}_it{}'.format(version, iteration), iteration, feature, stage_target)
            return createVersionWithIteration(cur, config, plugin_dir, name, iteration, feature, target)
        startTask(self, config, create,
                  self.onCreated, lambda message: self.log(tr_msg('The child version could not be created: ') + message))

    def finished(self, iteration, n, new_ids, version):
        self.log(tr_msg('{} lines of version {} have the pipes of iteration {}{}; simulate the version for results that match them.').format(
            n, version, iteration, tr_msg(', new pipe bundle types: {}').format(new_ids) if new_ids else ''))
        from qgis.utils import iface
        iface.mapCanvas().refreshAllLayers()

    @pyqtSlot(object)
    def onCreated(self, result):
        from ..ida_ph import getVersionData, importData, loadVersionLayers
        from .utility import write_plugin_settings
        from .workers import WorkerLoadVersion
        n, new_ids = result
        try:
            importData(self.main.model, getVersionData(self.main.cur))
            self.main.config['versionName'] = self.name
            write_plugin_settings(self.main.config)
            loadVersionLayers(self.main.config, self.main.cur, self.main.plugin_dir)
            self.worker = WorkerLoadVersion(config=self.main.config, cur=self.main.cur, dlg=self.main.dlg)
            self.worker.signals.error.connect(self.log)
            self.worker.signals.finished.connect(lambda _: self.onLoaded(n, new_ids))
            QThreadPool.globalInstance().start(self.worker)
        except Exception:
            QgsMessageLog.logMessage(traceback.format_exc(), 'Districts', MessageCritical)
            self.log(tr_msg('The child version could not be loaded: ') + traceback.format_exc().splitlines()[-1])

    def onLoaded(self, n, new_ids):
        from ..ida_ph import finishedLoadVersion
        finishedLoadVersion(self.main)
        self.finished(self.iteration, n, new_ids, self.name)
        if self.done:
            self.done()
