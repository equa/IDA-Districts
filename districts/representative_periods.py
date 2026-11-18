# coding=utf-8
"""The periods widget and the period run (OpenSpec change representative-periods): three weeks simulated in parallel
(or a year), the results of each week kept as copies of the result tables (suffix
_period<k>), the weeks and weights in versions/<version>/periods.json."""
import ctypes
import datetime
import os
import re
import shutil
import time
import traceback

import psycopg2.extras

from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg
from matplotlib.figure import Figure
from qgis.PyQt.QtCore import QDate, QDateTime, QObject, QRunnable, QThreadPool, QTimer, pyqtSignal, pyqtSlot
from qgis.PyQt.QtWidgets import (
    QCheckBox, QDateEdit, QFormLayout, QHBoxLayout, QLabel, QPushButton, QSpinBox, QVBoxLayout, QWidget,
)
from qgis.core import QgsMessageLog
from qgis.utils import iface

from .ida_mosim import checkSimOutputs, runModel
from .ida_mosim_dialog import RunNetworkModelDialog
from .ida_rv import loadResults
from .ida_rv_dialog import LoadResultsDialog
from .invoke_network import WorkerBuildNetworkModel
from .simulate_process import simulateInProcess, solverStarted
from .utility_functions.compat import MessageCritical, MessageInfo
from .utility_functions.db import dbConnect
from .utility_functions.files import (
    loadInvokedOutputs, loadNetworkSimData, loadRequestedOutputs, readFileToString, writeNetworkSimData, writePropertyListIDMToFile,
    writeSimulatedOutputs,
)
from .utility_functions.ida_components import getCompClass, getIDAListComponents, getSimData, propertyListCompsIDM
from .utility_functions.network_economics import plantModes
from .utility_functions.periods import (
    COVERAGE_WARNING, chooseWeeks, climateFile, deletePeriods, readClimate, savePeriods, weekDates, weekHours, weights,
)
from .utility_functions.translations import tr, tr_msg

DATE_FORMAT = 'yyyy-MM-dd hh:mm:ss'
PERIOD_KEYS = ('calc_time_from', 'calc_time_to', 'startup_time_from', 'startup_time_to')
# result tables the economic evaluation reads (prefixes; '$' tables per connection or pipe)
KEPT_PREFIXES = ('line_s_temp$', 'line_s_mdot$', 'line_s_p$', 'line_s_qamb', 'energy_plant_s_temp$', 'energy_plant_s_mdot$',
                 'energy_plant_s_p$', 'energy_plant_s_power$', 'energy_plant_s_ppump', 'customer_s_ppump', 'customer_s_troom',
                 'customer_s_tset', 'customer_s_hcmode', 'customer_s_power$')
NEEDED_OUTPUTS = ('ppump_ep', 'temp_lines', 'qamb_lines', 'temp_ep')
PERIOD_SUFFIX = re.compile(r'_period\d+$')


def dominantMode(cur, config):
    """('heat'|'cold', combined): heating if the plants have a heating pair."""
    modes = set(plantModes(cur, config['versionName'])[0].values())
    return ('heat' if 'heat' in modes or not modes else 'cold'), modes == {'heat', 'cold'}


def keptTables(cur, schema):
    """result tables of the last loading that a period run keeps (without earlier copies)"""
    cur.execute("SELECT table_name FROM information_schema.tables WHERE table_schema = %s;", (schema,))
    names = [row['table_name'] for row in cur.fetchall()]
    return sorted(n for n in names if not PERIOD_SUFFIX.search(n) and any(n == p or (p.endswith('$') and n.startswith(p)) for p in KEPT_PREFIXES))


def deletePeriodTables(cur, schema):
    cur.execute("SELECT table_name FROM information_schema.tables WHERE table_schema = %s;", (schema,))
    for name in [row['table_name'] for row in cur.fetchall() if PERIOD_SUFFIX.search(row['table_name'])]:
        cur.execute('DROP TABLE IF EXISTS "{}"."{}";'.format(schema, name))  # nosec B608


def copyPeriodTables(cur, schema, k):
    tables = keptTables(cur, schema)
    for name in tables:
        copy = '{}_period{}'.format(name, k)
        cur.execute('DROP TABLE IF EXISTS "{s}"."{c}"; CREATE TABLE "{s}"."{c}" AS SELECT * FROM "{s}"."{t}";'.format(s=schema, c=copy, t=name))  # nosec B608
    return tables


class PeriodsWidget(QWidget):
    """The periods of a check, shared by the dialogs of the representative periods and the cost optimization: length
    and start-up of the weeks, the warmest week, the annual option, the diagram with the weeks (movable) and the
    coverage. With the annual option the week settings, the diagram and the coverage are hidden."""

    def __init__(self, main, log=None):
        super().__init__()
        self.log = log or (lambda message: None)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        self.check_annual = QCheckBox(tr_msg('Annual simulation instead of the weeks'))
        layout.addWidget(self.check_annual)
        self.weeks_box = QWidget()
        weeks = QVBoxLayout(self.weeks_box)
        weeks.setContentsMargins(0, 0, 0, 0)
        form = QFormLayout()
        self.spin_days = QSpinBox()
        self.spin_days.setRange(1, 28)
        self.spin_days.setValue(7)
        self.check_warmest = QCheckBox(tr_msg('Add the warmest week'))
        self.btn_choose = QPushButton(tr_msg('Choose the weeks'))
        row = QHBoxLayout()
        row.addWidget(self.spin_days)
        row.addWidget(self.check_warmest)
        row.addWidget(self.btn_choose)
        form.addRow(tr_msg('Length of a week [days]'), row)
        weeks.addLayout(form)
        self.figure = Figure(figsize=(9, 3.2))
        self.canvas = FigureCanvasQTAgg(self.figure)
        self.canvas.setMinimumHeight(260)
        weeks.addWidget(self.canvas)
        self.weeks_layout = QHBoxLayout()
        weeks.addLayout(self.weeks_layout)
        self.label_coverage = QLabel()
        weeks.addWidget(self.label_coverage)
        layout.addWidget(self.weeks_box)
        form = QFormLayout()
        self.spin_startup = QSpinBox()
        self.spin_startup.setRange(0, 28)
        self.spin_startup.setValue(3)
        form.addRow(tr_msg('Start-up before each period [days]'), self.spin_startup)
        layout.addLayout(form)
        self.btn_choose.clicked.connect(self.chooseWeeks)
        self.check_annual.toggled.connect(self.updateVisible)
        self.canvas.mpl_connect('button_press_event', self.onCanvasClick)
        self.date_edits, self.roles = [], []
        self.t_year, self.climate, self.year = None, '', 2026
        cur, config = main.cur, main.config
        self.mode, combined = dominantMode(cur, config)
        # low-temperature networks heat and cool through the same pair, so the option stays available for every network
        if self.mode == 'cold':
            self.check_warmest.setText(tr_msg('Add the coldest week'))
        self.check_warmest.setToolTip(tr_msg('The extreme week of the main mode is the anchor (coldest week for heating, warmest for cooling); '
                                             'this adds the opposite extreme week, e.g. the cooling peak of a network that heats and cools, '
                                             'also through the same pipes as a low-temperature network.'))
        self.ready = False
        try:
            self.year = int(loadNetworkSimData(main.plugin_dir, config)['calc_time_from'][:4])
            self.climate = climateFile(config)
        except Exception as error:
            self.log(tr_msg('The climate file cannot be read: {}').format(error))
        self.chooseWeeks()
        self.updateVisible()

    def chooseWeeks(self):
        """reading the climate file and the search take seconds: they run in the thread pool, the widget shows the
        weeks when they are found"""
        if not self.climate:
            return
        self.ready = False
        self.btn_choose.setEnabled(False)
        self.label_coverage.setText(tr_msg('Choosing the weeks ...'))
        t_year, climate, year, days, mode, warmest = self.t_year, self.climate, self.year, self.spin_days.value(), self.mode, self.check_warmest.isChecked()

        def work():
            t = t_year if t_year is not None else readClimate(climate)
            return t, chooseWeeks(t, year, days, mode, warmest)

        self.task = CalcTask(work)
        self.task.signals.done.connect(self.onWeeks)
        self.task.signals.failed.connect(lambda message: self.label_coverage.setText(tr_msg('The climate file cannot be read: {}').format(message)))
        QThreadPool.globalInstance().start(self.task)

    @pyqtSlot(object)
    def onWeeks(self, result):
        self.t_year, weeks = result
        while self.weeks_layout.count():
            self.weeks_layout.takeAt(0).widget().deleteLater()
        self.date_edits, self.roles = [], []
        for start_day, role in weeks:
            edit = QDateEdit(QDate(self.year, 1, 1).addDays(start_day))
            edit.setDisplayFormat('yyyy-MM-dd')
            edit.setToolTip(tr_msg('anchor week') if role == 'anchor' else tr_msg('opposite extreme week') if role in ('warmest', 'coldest') else tr_msg('week for the coverage'))
            edit.dateChanged.connect(self.updateCoverage)
            self.weeks_layout.addWidget(edit)
            self.date_edits.append(edit)
            self.roles.append(role)
        self.ready = True
        self.btn_choose.setEnabled(True)
        self.updateCoverage()

    def startDays(self):
        first = QDate(self.year, 1, 1)
        return [max(0, min(365 - self.spin_days.value(), first.daysTo(edit.date()))) for edit in self.date_edits]

    def simHours(self):
        return [h for s in self.startDays() for h in weekHours(s, self.spin_days.value())]

    def updateCoverage(self):
        if self.t_year is None or not self.date_edits:
            return
        _, coverage = weights(self.t_year, self.year, self.simHours())
        warning = coverage > COVERAGE_WARNING
        self.label_coverage.setText(tr_msg('{:.0%} of the hours of the year are more than 1 K from a simulated hour{}').format(
            coverage, tr_msg(' – the weeks represent the year poorly') if warning else ''))
        self.plot()

    def plot(self):
        t_year = self.t_year
        if t_year is None:
            return
        self.figure.clear()
        ax = self.figure.add_subplot(111)
        ax.plot([h / 24 for h in range(len(t_year))], t_year, linewidth=0.4, color='grey')
        days = self.spin_days.value()
        for s, role in zip(self.startDays(), self.roles):
            ax.axvspan(s, s + days, color='tab:blue' if role == 'anchor' else 'tab:orange', alpha=0.4)
        ax.set_xlabel(tr_msg('day of the year'))
        ax.set_ylabel(tr_msg('air temperature [°C]'))
        self.figure.tight_layout()
        self.canvas.draw()

    def onCanvasClick(self, event):
        """a click moves the nearest coverage week (the anchor stays) to the clicked day"""
        if event.xdata is None or not self.date_edits:
            return
        candidates = [k for k, role in enumerate(self.roles) if role != 'anchor'] or list(range(len(self.roles)))
        days = self.startDays()
        k = min(candidates, key=lambda k: abs(days[k] - event.xdata))
        self.date_edits[k].setDate(QDate(self.year, 1, 1).addDays(int(event.xdata)))

    def updateVisible(self):
        self.weeks_box.setVisible(not self.check_annual.isChecked())

    def setRunning(self, running):
        self.setEnabled(not running)

    def parameters(self):
        """the periods of a PeriodRun: dates, roles, length, start-up and start days"""
        days = self.spin_days.value()
        if self.check_annual.isChecked():
            start = datetime.datetime(self.year, 1, 1)
            periods = [(start, datetime.datetime(self.year + 1, 1, 1), start, start + datetime.timedelta(days=self.spin_startup.value() or 1))]
            return {'annual': True, 'periods': periods, 'roles': ['annual'], 'days': days, 'startup_days': self.spin_startup.value(), 'start_days': []}
        return {'annual': False, 'periods': [weekDates(self.year, s, days, self.spin_startup.value()) for s in self.startDays()],
                'roles': list(self.roles), 'days': days, 'startup_days': self.spin_startup.value(), 'start_days': self.startDays()}


PERIOD_DIR = 'period_{}'
SIM_START_POLL_MS = 500
# a week whose solver start is not seen (other IDA version, slow start) holds the next one back at most this long
SIM_START_MAX_WAIT_S = 120


# one week (IDA + solver) of low_temperature_network and dynamic_optimization: 3.4 GB committed, mostly the solver's
# fixed block; replaced by the measured need after the first week's solver runs
WEEK_MEMORY_MB = 3500
WEEK_MEMORY_FACTOR = 1.1
MIN_PLAUSIBLE_WEEK_MB = 300
# left for QGIS and the other programs
MEMORY_RESERVE_MB = 1000


class _MemoryStatus(ctypes.Structure):
    _fields_ = [('dwLength', ctypes.c_ulong), ('dwMemoryLoad', ctypes.c_ulong),
                ('ullTotalPhys', ctypes.c_ulonglong), ('ullAvailPhys', ctypes.c_ulonglong),
                ('ullTotalPageFile', ctypes.c_ulonglong), ('ullAvailPageFile', ctypes.c_ulonglong),
                ('ullTotalVirtual', ctypes.c_ulonglong), ('ullAvailVirtual', ctypes.c_ulonglong),
                ('ullAvailExtendedVirtual', ctypes.c_ulonglong)]


def freeMemoryMB():
    """free commit (RAM + page file) [MB], None if unknown. The solver's allocation (SUPERLU_MALLOC) fails when the
    commit is used up; free RAM would be too strict, the solver commits far more than it touches."""
    try:
        status = _MemoryStatus()
        status.dwLength = ctypes.sizeof(_MemoryStatus)
        if not ctypes.windll.kernel32.GlobalMemoryStatusEx(ctypes.byref(status)):
            return None
        return status.ullAvailPageFile / 2**20
    except Exception:
        return None


def versionDir(config):
    return os.path.join(config['pathProjects'] + config['projectName'], 'versions', config['versionName'])


def removePeriodModels(config):
    """the model copies of a parallel period run"""
    for name in os.listdir(versionDir(config)) if os.path.isdir(versionDir(config)) else []:
        if re.match(r'^period_\d+$', name):
            shutil.rmtree(os.path.join(versionDir(config), name), ignore_errors=True)


def preparePeriodModels(config, submodel, sim_data, requested):
    """one copy of the network model per period (versions/<version>/period_<k>), each with the dates of its period;
    returns the model files (worker thread: file work only)"""
    vdir = versionDir(config)
    name = 'network_{}'.format(submodel)
    removePeriodModels(config)
    files = []
    for k, data in enumerate(sim_data, 1):
        pdir = os.path.join(vdir, PERIOD_DIR.format(k))
        shutil.copytree(os.path.join(vdir, name), os.path.join(pdir, name))
        for ext in ('.idm', '.idc'):
            if os.path.exists(os.path.join(vdir, name + ext)):
                shutil.copyfile(os.path.join(vdir, name + ext), os.path.join(pdir, name + ext))
        fname = os.path.join(pdir, name + '.idm')
        components = propertyListCompsIDM(getIDAListComponents(readFileToString(fname)))
        data_idm = [propertyListCompsIDM(getIDAListComponents(getSimData(requested, data))) if getCompClass(comp) == 'SIMULATION_DATA' else comp
                    for comp in components]
        writePropertyListIDMToFile(data_idm, pdir + '\\', fname, config)
        files.append(fname)
    return files


def copyResultsBack(config, submodel, k):
    """the model of period k as IDA saved it (results .prn and the macros IDA rewrote, which the loading parses) into
    the version's model folder; returns the number of .prn files"""
    name = 'network_{}'.format(submodel)
    pdir = os.path.join(versionDir(config), PERIOD_DIR.format(k))
    source, target = os.path.join(pdir, name), os.path.join(versionDir(config), name)
    count = 0
    for folder, _, files in os.walk(source):
        destination = os.path.join(target, os.path.relpath(folder, source))
        os.makedirs(destination, exist_ok=True)
        for file in files:
            shutil.copyfile(os.path.join(folder, file), os.path.join(destination, file))
            count += file.lower().endswith('.prn')
    for ext in ('.idm', '.idc'):
        if os.path.exists(os.path.join(pdir, name + ext)):
            shutil.copyfile(os.path.join(pdir, name + ext), os.path.join(versionDir(config), name + ext))
    return count


class _TaskSignals(QObject):
    done = pyqtSignal(object)
    failed = pyqtSignal(str)


class CalcTask(QRunnable):
    """runs fn() in the thread pool (a calculation without DB access); the result comes back by signal"""

    def __init__(self, fn):
        super().__init__()
        self.fn = fn
        self.signals = _TaskSignals()

    def run(self):
        try:
            result = self.fn()
        except Exception as error:
            QgsMessageLog.logMessage(traceback.format_exc(), 'Districts', MessageCritical)
            self.signals.failed.emit(str(error))
            return
        self.signals.done.emit(result)


class DBTask(QRunnable):
    """runs fn(cursor) in the thread pool with its own DB connection, so the dialog stays responsive; the result
    (or the error) comes back to the main thread by signal"""

    def __init__(self, config, fn):
        super().__init__()
        self.config, self.fn = dict(config), fn
        self.signals = _TaskSignals()

    def run(self):
        conn = dbConnect(self.config, False)
        if not conn:
            self.signals.failed.emit(tr_msg('No database connection'))
            return
        try:
            result = self.fn(conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor))
        except Exception:
            QgsMessageLog.logMessage(traceback.format_exc(), 'Districts', MessageCritical)
            self.signals.failed.emit(traceback.format_exc().splitlines()[-1])
            return
        finally:
            conn.close()
        self.signals.done.emit(result)


def startTask(owner, config, fn, done, failed):
    """starts a DBTask; owner keeps the reference (a task without one may be collected before it reports)"""
    task = DBTask(config, fn)
    task.signals.done.connect(done)
    task.signals.failed.connect(failed)
    owner.task = task
    QThreadPool.globalInstance().start(task)


class _BuildSettings:
    """the settings the network model build reads from a dialog: the customer and plant models are invoked again only
    when asked (the first run of an optimization; pipe changes do not need it)"""

    def __init__(self, reinvoke=False):
        self.process_running = False
        self.checkbox_reinvokeFeatures = QCheckBox()
        self.checkbox_reinvokeFeatures.setChecked(reinvoke)


class _PeriodRelay(QObject):
    """carries the signals of one week's simulation worker to the main thread, with the week's index"""

    def __init__(self, run, k):
        super().__init__()
        self.run, self.k = run, k

    @pyqtSlot(object)
    def done(self, result):
        self.run.onPeriodResult(self.k, result)

    @pyqtSlot(str)
    def failed(self, message):
        self.run.onPeriodResult(self.k, {'ok': False, 'errors': [message]})


class PeriodRun(QObject):
    """Build (option), the periods simulated in parallel (own model copies), then for each period: loading and copies of
    the result tables; finally periods.json and the dates of the version as before the run. Reused by the cost optimization for its checks."""

    def __init__(self, dlg, main, parms, on_finished=None):
        super().__init__()
        self.dlg = dlg
        self.main = main
        self.plugin_dir = main.plugin_dir
        self.parms = parms
        self.on_finished = on_finished
        self.k = 0
        self.stage = None
        self.done = False
        self.stop_requested = False
        self.sim_failed = False
        self.finished_sims = 0
        self.kept = []

    @property
    def config(self):
        return self.main.config

    def start(self):
        self.started = datetime.datetime.now().isoformat(timespec='seconds')
        self.sim_data_before = dict(loadNetworkSimData(self.plugin_dir, self.config))
        schema = self.config['versionName']
        try:
            deletePeriodTables(self.main.cur, schema)
            deletePeriods(self.config)
        except Exception:
            self.onException()
            return
        if self.parms['build_first']:
            self.build()
        else:
            self.simulate()

    def progress(self, step):
        n = len(self.parms['periods'])
        if self.parms['annual']:
            self.dlg.update_progress((self.k * 3 + step) / (n * 3) * 100)
        else:
            # the parallel simulations take the first half
            self.dlg.update_progress(50 + (self.k * 2 + step - 1) / (n * 2) * 50)

    def checkStop(self):
        if self.done:
            return True
        if self.stop_requested:
            self.finish(tr_msg('Stopped by the user.'), error=True)
            return True
        return False

    def finish(self, message, error=False):
        if self.done:
            return
        self.done = True
        try:
            writeNetworkSimData(self.config, self.sim_data_before)
            removePeriodModels(self.config)
        except Exception:
            QgsMessageLog.logMessage(traceback.format_exc(), 'Districts', MessageCritical)
        self.dlg.log(message)
        self.dlg.update_progress(0 if error else 100)
        iface.messageBar().pushMessage(tr_msg('Error') if error else tr_msg('Info'), tr_msg('Representative periods: ') + message,
                                       level=MessageCritical if error else MessageInfo)
        self.dlg.finished()
        if self.on_finished:
            self.on_finished(not error)

    def build(self):
        self.stage = 'build'
        self.dlg.log(tr_msg('Building the network model ...'))
        try:
            self.worker_build = WorkerBuildNetworkModel(main=self.main, config=self.config, plugin_dir=self.plugin_dir, dlg=_BuildSettings(reinvoke=self.parms.get('reinvoke', False)),
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
        self.simulate()

    def simulate(self):
        if self.parms['annual']:
            self.simulateOne()
        else:
            self.simulateParallel()

    def weekSimData(self, k):
        data = dict(self.sim_data_before)
        for key, value in zip(PERIOD_KEYS, self.parms['periods'][k]):
            data[key] = value.strftime('%Y-%m-%d %H:%M:%S')
        return data

    def simulateParallel(self):
        """all weeks at once, each in its own copy of the model (versions/<version>/period_<k>)"""
        if self.checkStop():
            return
        self.stage = 'simulate'
        self.dlg.update_progress(5)
        requested = loadRequestedOutputs(self.plugin_dir, self.config)
        if not checkSimOutputs(loadInvokedOutputs(self.config), requested):
            self.finish(tr_msg('The requested outputs differ from the invoked ones: please build the network model with the features invoked again.'), error=True)
            return
        n = len(self.parms['periods'])
        self.dlg.log(tr_msg('Simulating {} periods in parallel ...').format(n))
        sim_data = [self.weekSimData(k) for k in range(n)]
        config, submodel = dict(self.config), self.parms['submodel']
        self.requested = requested
        self.prepare_task = CalcTask(lambda: preparePeriodModels(config, submodel, sim_data, requested))
        self.prepare_task.signals.done.connect(self.startPeriodSims)
        self.prepare_task.signals.failed.connect(self.onTaskFailed)
        QThreadPool.globalInstance().start(self.prepare_task)

    @pyqtSlot(str)
    def onTaskFailed(self, message):
        self.finish(tr_msg('Error: {}').format(message), error=True)

    @pyqtSlot(object)
    def startPeriodSims(self, files):
        if self.checkStop():
            return
        try:
            writeSimulatedOutputs(self.config, self.requested)
            self.files = files
            self.work_dirs = [os.path.dirname(fname) for fname in files]
            self.started_periods, self.finished_periods, self.failed_periods = set(), set(), set()
            self.relays = []
            self.queue = list(range(len(files)))
            self.retry = False
            self.week_memory, self.week_measured = WEEK_MEMORY_MB, False
            self.startNextSim()
        except Exception:
            self.onException()

    def makeWorker(self, k):
        """each week in its own process: one IDA connection per process (simulate_process.py)"""
        fname, path_districts = self.files[k], self.config['pathDistricts']
        worker = CalcTask(lambda: simulateInProcess(fname, os.path.dirname(fname), path_districts))
        relay = _PeriodRelay(self, k)
        worker.signals.done.connect(relay.done)
        worker.signals.failed.connect(relay.failed)
        self.relays.append(relay)
        return worker

    def running(self):
        return self.started_periods - self.finished_periods

    def startNextSim(self):
        """IDA sessions starting at the same moment disturb each other (session lock, a solver without its modules);
        a fixed gap does not prevent it, the start of a week's process varies by seconds: the next week starts when
        the solver of the previous one runs and enough memory is free for one more"""
        if self.done or not self.queue:
            return
        k = self.queue.pop(0)
        self.started_periods.add(k)
        self.finished_periods.discard(k)
        self.memory_before = freeMemoryMB()
        QThreadPool.globalInstance().start(self.makeWorker(k))
        # the retry runs one week at a time: the next starts from onPeriodResult
        if self.queue and not self.retry:
            self.waiting, self.wait_start = k, time.monotonic()
            self.measured = self.timeout_logged = self.memory_logged = False
            QTimer.singleShot(SIM_START_POLL_MS, self.waitForSolver)

    def measureWeek(self, k):
        """the solver commits its memory at once, before its start is logged: the drop of the free memory since the
        start of week k is what one more week needs"""
        free = freeMemoryMB()
        if free is None or self.memory_before is None or self.memory_before - free < MIN_PLAUSIBLE_WEEK_MB:
            return
        used = (self.memory_before - free) * WEEK_MEMORY_FACTOR
        self.week_memory = max(self.week_memory, used) if self.week_measured else used
        self.week_measured = True

    def waitForSolver(self):
        if self.done:
            return
        k = self.waiting
        finished = k in self.finished_periods
        solver = finished or solverStarted(self.work_dirs[k])
        if solver and not finished and not self.measured:
            self.measured = True
            self.measureWeek(k)
        if not solver:
            if time.monotonic() - self.wait_start < SIM_START_MAX_WAIT_S:
                QTimer.singleShot(SIM_START_POLL_MS, self.waitForSolver)
                return
            if not self.timeout_logged:
                self.timeout_logged = True
                self.dlg.log(tr_msg('Period {}: start of the solver not seen after {} s, the next period starts').format(k + 1, SIM_START_MAX_WAIT_S))
        free = freeMemoryMB()
        if not self.running() or free is None or free >= self.week_memory + MEMORY_RESERVE_MB:
            self.startNextSim()
            return
        if not self.memory_logged:
            self.memory_logged = True
            self.dlg.log(tr_msg('Period {}: waiting for free memory ({} MB free, {} MB needed)').format(
                self.queue[0] + 1, round(free), round(self.week_memory + MEMORY_RESERVE_MB)))
        QTimer.singleShot(SIM_START_POLL_MS, self.waitForSolver)

    def onPeriodResult(self, k, result):
        if self.done or self.stage != 'simulate':
            return
        self.finished_periods.add(k)
        if result.get('ok'):
            self.failed_periods.discard(k)
            self.dlg.log(tr_msg('Period {}: simulated').format(k + 1))
        else:
            self.failed_periods.add(k)
            for message in result.get('errors') or [tr_msg('Simulation failed')]:
                self.dlg.log(tr_msg('Period {}: ').format(k + 1) + message)
        n = len(self.files)
        self.dlg.update_progress(5 + 45 * len(self.finished_periods - self.failed_periods) / n)
        if self.retry and self.queue:
            self.startNextSim()
            return
        if self.running() or self.queue:
            return
        if self.failed_periods and not self.retry:
            # mostly a lack of memory or a disturbed start: alone, the week gets the whole machine
            self.retry = True
            self.queue = sorted(self.failed_periods)
            self.dlg.log(tr_msg('Simulating period {} again, one at a time ...').format(', '.join(str(j + 1) for j in self.queue)))
            for j in self.queue:
                shutil.rmtree(os.path.join(self.work_dirs[j], 'tmp'), ignore_errors=True)
            self.startNextSim()
            return
        if self.failed_periods:
            self.finish(tr_msg('The simulation of period {} failed.').format(', '.join(str(k + 1) for k in sorted(self.failed_periods))), error=True)
            return
        self.k = 0
        self.loadPeriod()

    def loadPeriod(self):
        """the results of week k into the version's model folder, then loaded like a single simulation"""
        if self.checkStop():
            return
        self.stage = 'copy'
        config, submodel, k = dict(self.config), self.parms['submodel'], self.k + 1
        self.copy_task = CalcTask(lambda: copyResultsBack(config, submodel, k))
        self.copy_task.signals.done.connect(self.onResultsCopied)
        self.copy_task.signals.failed.connect(self.onTaskFailed)
        QThreadPool.globalInstance().start(self.copy_task)

    @pyqtSlot(object)
    def onResultsCopied(self, count):
        if self.done or self.stage != 'copy':
            return
        if not count:
            self.finish(tr_msg('Period {}: no results found.').format(self.k + 1), error=True)
            return
        try:
            writeNetworkSimData(self.config, self.weekSimData(self.k))
        except Exception:
            self.onException()
            return
        self.load()

    def simulateOne(self):
        if self.checkStop():
            return
        self.progress(0)
        self.stage = 'simulate'
        calc_from, calc_to, startup_from, startup_to = self.parms['periods'][self.k]
        self.dlg.log(tr_msg('Period {}: simulating {} to {} ...').format(self.k + 1, calc_from.date(), calc_to.date()))
        try:
            self.sim_failed = False
            self.finished_sims = 0
            self.dlg_run = RunNetworkModelDialog(self.plugin_dir, self.config)
            self.dlg_run.combo_submodels.addItem(tr('@default', 'check_all_items'))
            self.dlg_run.combo_submodels.addItem(self.parms['submodel'])
            self.dlg_run.combo_submodels.setItemChecked(1, True)
            for value, attr in zip((calc_from, calc_to, startup_from, startup_to), ('dateedit_calcFrom', 'dateedit_calcTo', 'dateedit_startupFrom', 'dateedit_startupTo')):
                getattr(self.dlg_run, attr).setDateTime(QDateTime.fromString(value.strftime('%Y-%m-%d %H:%M:%S'), DATE_FORMAT))
            self.dlg_run.updateStatusBar = self.onSimStatus  # type: ignore[method-assign]
            self.dlg_run.show_error_message = self.onSimError  # type: ignore[method-assign]
            self.dlg_run.update_finished = self.onSimFinished  # type: ignore[method-assign]
            runModel(self.dlg_run, self.plugin_dir, self.config)
            if not self.dlg_run.process_running:
                self.finish(tr_msg('The simulation could not be started (see message bar).'), error=True)
        except Exception:
            self.onException()

    @pyqtSlot(str)
    def onSimStatus(self, message):
        if message == tr_msg('Simulation failed'):
            self.sim_failed = True

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
            self.finish(tr_msg('The simulation of period {} failed.').format(self.k + 1), error=True)
        else:
            self.load()

    def load(self):
        if self.checkStop():
            return
        self.progress(1)
        self.stage = 'load'
        try:
            self.dlg_load = LoadResultsDialog(self.main.dlg)
            self.dlg_load.combo_submodels.addItem(tr('@default', 'check_all_items'))
            self.dlg_load.combo_submodels.addItem(self.parms['submodel'])
            self.dlg_load.combo_submodels.setItemChecked(1, True)
            self.dlg_load.update_finished = self.onLoadFinished  # type: ignore[method-assign]
            loadResults(self.dlg_load, self.main)
            if not self.dlg_load.process_running:
                self.finish(tr_msg('The results could not be loaded (see message bar).'), error=True)
        except Exception:
            self.onException()

    @pyqtSlot(str)
    def onLoadFinished(self, message):
        if self.done or self.stage != 'load':
            return
        self.progress(2)
        if self.parms['annual']:
            self.onKept(None)
            return
        schema, k = self.config['versionName'], self.k + 1
        startTask(self, self.config, lambda cur: copyPeriodTables(cur, schema, k), self.onKept,
                  lambda message: self.finish(tr_msg('Error: {}').format(message), error=True))

    @pyqtSlot(object)
    def onKept(self, kept):
        if self.done:
            return
        try:
            if kept is not None:
                self.kept = kept
                self.dlg.log(tr_msg('  {} result tables kept').format(len(kept)))
            self.k += 1
            if self.k < len(self.parms['periods']):
                self.loadPeriod()
            else:
                self.writePeriods()
        except Exception:
            self.onException()

    def writePeriods(self):
        p = self.parms
        data = {'run_time': self.started, 'year': self.dlg.year, 'climate_file': getattr(self.dlg, 'climate', ''), 'annual': p['annual'],
                'days': p['days'], 'startup_days': p['startup_days'], 'tables': self.kept,
                'weeks': [{'period': k + 1, 'role': role, 'start_day': (p['start_days'] or [0])[k] if not p['annual'] else 0,
                           'calc_from': str(dates[0]), 'calc_to': str(dates[1]), 'startup_from': str(dates[2]), 'startup_to': str(dates[3])}
                          for k, (dates, role) in enumerate(zip(p['periods'], p['roles']))]}
        if not p['annual'] and self.dlg.t_year is not None:
            sim = [(k + 1, h) for k, s in enumerate(p['start_days']) for h in weekHours(s, p['days'])]
            w, coverage = weights(self.dlg.t_year, self.dlg.year, [h for _, h in sim])
            data['hours'] = [[k, h, w[h][0]] for k, h in sim]
            data['coverage'] = coverage
        savePeriods(self.config, data)
        self.finish(tr_msg('Finished: {} periods simulated and kept.').format(len(p['periods'])))

    @pyqtSlot(str)
    def onError(self, message):
        self.dlg.log(tr_msg('  Error: ') + message)
        if self.stage == 'build':
            self.finish(tr_msg('Building the network model failed.'), error=True)

    def onException(self):
        QgsMessageLog.logMessage(traceback.format_exc(), 'Districts', MessageCritical)
        self.finish(tr_msg('Error: {}').format(traceback.format_exc().splitlines()[-1]), error=True)
