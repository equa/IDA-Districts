# coding=utf-8
"""Shared fixtures for the Districts Modeler tests.

The tests can run in two ways:

* headless from the command line (pytest-qgis starts a QgsApplication with an
  isolated profile in .qgis-settings). The plugin settings and the DB
  credentials are set up by the fixture districts_settings from environment
  variables (DISTRICTS_TEST_DB_USER, DISTRICTS_TEST_DB_PASSWORD, ...).
* inside a running QGIS with test/run_in_qgis.py. The real iface, the plugin
  settings and the authentication DB of the current QGIS profile are used.
"""
import os
import sys
import time
import traceback

import pytest
from qgis.core import QgsApplication, QgsAuthMethodConfig, QgsTemporalNavigationObject
from qgis.PyQt.QtCore import QEventLoop, QSettings, QThreadPool, QTimer
from qgis.PyQt.QtWidgets import QAbstractButton, QDialog, QMessageBox

from districts.utility_functions.compat import MessageCritical

IN_QGIS = os.environ.get("DISTRICTS_TEST_IN_QGIS") == "1"

if not IN_QGIS:
    # pytest-qgis uses an isolated profile (.qgis-settings), but the plugin locates its own
    # files with qgisSettingsDirPath() + python/plugins/districts (e.g. get_districts_plugin_dir()):
    # point it to the profile which contains this plugin. Must happen before the plugin modules are imported.
    _profile_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "..", "..")
    _profile_dir = os.path.join(os.path.normpath(_profile_dir), "")
    QgsApplication.qgisSettingsDirPath = staticmethod(lambda: _profile_dir)

# outdated Plugin Builder boilerplate: Qt4 imports, own QgsApplication, missing i18n/af.qm
collect_ignore = ["test_districts_dialog.py", "test_qgis_environment.py", "test_translations.py"]

TEST_AUTH_ID = "dstest1"
TEST_MASTER_PASSWORD = "districts_test"


def _slow_default():
    try:
        return float(os.environ.get("DISTRICTS_TEST_SLOW") or 0)
    except ValueError:
        return 0.0


def pytest_addoption(parser):
    parser.addoption("--keep-projects", action="store_true",
                     help="do not delete the autotest_* projects after the workflow tests")
    parser.addoption("--slow", type=float, default=_slow_default(), metavar="SECONDS",
                     help="slow mode to watch the tests: pause SECONDS before each button click, "
                          "after a dialog opens and after each test step (default: DISTRICTS_TEST_SLOW or 0). "
                          "Needs the GUI: -o qgis_gui_enabled=true")


# ---------------- slow mode ----------------
SLOW = 0.0  # seconds, set in pytest_configure


def pytest_configure(config):
    global SLOW
    SLOW = max(0.0, config.getoption("--slow") or 0.0)
    if SLOW and os.environ.get("QT_QPA_PLATFORM") == "offscreen":
        print("\n--slow {}: the GUI is off (qgis_gui_enabled = false), nothing to watch; "
              "add -o qgis_gui_enabled=true".format(SLOW))
        SLOW = 0.0


def slow_pause(factor=1.0):
    """Slow mode: process events for SLOW*factor seconds (no-op without --slow)."""
    if SLOW > 0:
        wait(int(SLOW * factor * 1000))


# ---------------- incremental steps ----------------
# Steps of a class marked with @pytest.mark.incremental build on each other:
# after the first failing step the remaining steps of the same parametrization are skipped.
_failed_steps = {}


def _incremental_key(item):
    params = tuple(item.callspec.indices.values()) if hasattr(item, "callspec") else ()
    return (str(item.cls), params)


def pytest_runtest_makereport(item, call):
    if "incremental" in item.keywords and call.excinfo is not None \
            and not call.excinfo.errisinstance(pytest.skip.Exception):
        _failed_steps.setdefault(_incremental_key(item), item.originalname or item.name)


def pytest_runtest_setup(item):
    if "incremental" in item.keywords:
        failed = _failed_steps.get(_incremental_key(item))
        if failed:
            pytest.skip("previous step failed ({})".format(failed))


# ---------------- helpers ----------------
def wait(ms):
    """Process Qt events for ms milliseconds."""
    loop = QEventLoop()
    QTimer.singleShot(ms, loop.quit)
    loop.exec()


_collector = None  # ErrorCollector of the session (fixture errors)


def wait_until(condition, timeout, what):
    """Process events until condition() is True, fail the test after timeout seconds
    or as soon as an error was collected (e.g. a worker died with an exception)."""
    deadline = time.monotonic() + timeout
    while not condition():
        if _collector is not None and _collector.all():
            _collector.check()
        if time.monotonic() > deadline:
            pytest.fail("timeout after {}s: {}".format(timeout, what() if callable(what) else what))
        wait(100)


def wait_for_process(dlg, timeout, what=None):
    """Wait until the worker of a plugin dialog has finished (dlg.process_running==False)."""
    wait(200)
    progress = getattr(dlg, "progress", None)
    wait_until(lambda: not getattr(dlg, "process_running", False), timeout,
               what or (lambda: "{} still running (progress: {}, active worker threads: {})".format(
                   type(dlg).__name__, progress.value() if progress is not None else "-",
                   QThreadPool.globalInstance().activeThreadCount())))
    wait_until(lambda: QThreadPool.globalInstance().activeThreadCount() == 0, timeout,
               "worker threads still running")
    wait(200)


class ErrorCollector:
    """Collects critical messages of the message bar and the 'Districts' message log
    and modal dialogs which would block the test run."""

    def __init__(self, message_bar):
        self.message_bar = message_bar
        self.messages = []
        # QGIS 4 emits messageReceivedWithFormat instead of messageReceived(message, tag, level)
        log = QgsApplication.messageLog()
        self.log_signal = getattr(log, "messageReceivedWithFormat", log.messageReceived)
        self.log_signal.connect(self._on_log)
        # pytest-qgis MockMessageBar stores the pushed messages itself
        self.is_mock_bar = hasattr(message_bar, "get_messages")
        if not self.is_mock_bar:
            message_bar.widgetAdded.connect(self._on_bar_item)

    def _on_log(self, message, tag, level, *args):
        if tag == "Districts" and level == MessageCritical:
            self.messages.append("message log: " + message)

    def _on_bar_item(self, item):
        if item.level() == MessageCritical:
            self.messages.append("message bar: {} {}".format(item.title(), item.text()))

    def add(self, message):
        self.messages.append(message)

    def all(self):
        msgs = list(self.messages)
        if self.is_mock_bar:
            msgs += ["message bar: " + str(m) for m in self.message_bar.get_messages(MessageCritical)]
        return msgs

    def clear(self):
        self.messages.clear()
        if self.is_mock_bar:
            self.message_bar.clear_messages()

    def check(self):
        """Fail the test if critical messages were collected since the last clear()."""
        msgs = self.all()
        self.clear()
        if msgs:
            pytest.fail("critical messages:\n" + "\n".join(msgs), pytrace=False)

    def disconnect(self):
        self.log_signal.disconnect(self._on_log)
        if not self.is_mock_bar:
            self.message_bar.widgetAdded.disconnect(self._on_bar_item)


# ---------------- fixtures ----------------
@pytest.fixture(scope="session")
def iface(request):
    if IN_QGIS:
        from qgis.utils import iface as qgis_iface
        return qgis_iface
    qgis_iface = request.getfixturevalue("qgis_iface")
    # the canvas of QGIS gets its temporal controller from the temporal controller dock (used by show on map)
    canvas = qgis_iface.mapCanvas()
    if canvas.temporalController() is None:
        canvas.setTemporalController(QgsTemporalNavigationObject(canvas))
    if SLOW > 0:
        _show_map_window(request.getfixturevalue("qgis_parent"), canvas)
    return qgis_iface


_map_bridge = None


def _show_map_window(parent, canvas):
    """Slow mode: show the map canvas of pytest-qgis (hidden without the qgis_show_map marker)
    with the layers of the layer tree like in QGIS, zoomed to the layers of a newly loaded version."""
    global _map_bridge
    from qgis.core import QgsProject
    from qgis.gui import QgsLayerTreeMapCanvasBridge

    _map_bridge = QgsLayerTreeMapCanvasBridge(QgsProject.instance().layerTreeRoot(), canvas)

    def zoom_to_new_layers(layers):
        if layers and len(canvas.layers()) <= len(layers) + 1:
            canvas.zoomToFullExtent()
            canvas.refresh()

    QgsProject.instance().legendLayersAdded.connect(zoom_to_new_layers)
    parent.setWindowTitle("Districts tests: map (slow mode)")
    parent.resize(900, 700)
    parent.show()


@pytest.fixture(scope="session")
def districts_settings():
    """Plugin settings for the headless run (in QGIS the settings of the profile are used).

    Environment variables:
        DISTRICTS_TEST_DB_USER, DISTRICTS_TEST_DB_PASSWORD  (required for the e2e tests)
        DISTRICTS_TEST_DB_HOST (localhost), DISTRICTS_TEST_DB_PORT (5432)
        DISTRICTS_TEST_PATH_PROJECTS (temporary folder), DISTRICTS_TEST_PATH_DISTRICTS,
        DISTRICTS_TEST_PATH_POSTGRESQL
        DISTRICTS_TEST_DEBUG=1: plugin debug log (DISTRICTS_DEBUG_LOG_DIR, default <projects>_logs)
    """
    if IN_QGIS:
        return
    settings = QSettings()
    settings.setValue("locale/userLocale", "en_US")

    user = os.environ.get("DISTRICTS_TEST_DB_USER")
    password = os.environ.get("DISTRICTS_TEST_DB_PASSWORD")
    if not user or password is None:
        pytest.skip("DISTRICTS_TEST_DB_USER / DISTRICTS_TEST_DB_PASSWORD not set")

    # store the credentials in the isolated auth DB of the test profile
    auth_manager = QgsApplication.authManager()
    if not auth_manager.setMasterPassword(TEST_MASTER_PASSWORD, True):
        pytest.fail("could not set the master password of the test auth DB (.qgis-settings)")
    if TEST_AUTH_ID in auth_manager.configIds():
        auth_manager.removeAuthenticationConfig(TEST_AUTH_ID)
    auth_cfg = QgsAuthMethodConfig("Basic")
    auth_cfg.setId(TEST_AUTH_ID)
    auth_cfg.setName("districts_test")
    auth_cfg.setConfig("username", user)
    auth_cfg.setConfig("password", password)
    auth_manager.storeAuthenticationConfig(auth_cfg)

    path_projects = os.environ.get("DISTRICTS_TEST_PATH_PROJECTS")
    if not path_projects:
        import tempfile
        path_projects = os.path.join(tempfile.gettempdir(), "districts_autotest")
    os.makedirs(path_projects, exist_ok=True)
    # debug log of the test run beside the test projects folder (not in it: every folder there is
    # taken as a project) and not in the QGIS profile
    os.environ.setdefault("DISTRICTS_DEBUG_LOG_DIR", os.path.normpath(path_projects) + "_logs")

    settings.beginGroup("districts")
    for key, value in {
        "host": os.environ.get("DISTRICTS_TEST_DB_HOST", "localhost"),
        "port": os.environ.get("DISTRICTS_TEST_DB_PORT", "5432"),
        "auth_id": TEST_AUTH_ID,
        "pathProjects": os.path.join(path_projects, ""),
        "pathDistricts": os.environ.get("DISTRICTS_TEST_PATH_DISTRICTS", "C:\\Program Files (x86)\\IDA Districts\\"),
        "pathPostgresql": os.environ.get("DISTRICTS_TEST_PATH_POSTGRESQL", "C:\\Program Files\\PostgreSQL\\18\\"),
        # DISTRICTS_TEST_DEBUG=1: debug log file of the plugin (DISTRICTS_DEBUG_LOG_DIR)
        "debug": os.environ.get("DISTRICTS_TEST_DEBUG", "0") == "1",
        "debug_console": False,
        "autosave": False,
        "projectName": "",
        "versionName": "",
        "lastVersionName": "",
    }.items():
        settings.setValue(key, value)
    settings.endGroup()


@pytest.fixture(scope="session")
def errors(iface):
    collector = ErrorCollector(iface.messageBar())

    # PyQt aborts the process on unhandled exceptions in slots/QRunnables (workers) if the
    # default excepthook is active (QGIS shows them in its Python error dialog instead)
    def excepthook(exc_type, exc_value, exc_tb):
        collector.add("unhandled exception:\n" + "".join(traceback.format_exception(exc_type, exc_value, exc_tb)))

    global _collector
    previous_excepthook = sys.excepthook
    sys.excepthook = excepthook
    _collector = collector
    yield collector
    _collector = None
    sys.excepthook = previous_excepthook
    collector.disconnect()


@pytest.fixture(autouse=True)
def no_modal_dialogs(monkeypatch, errors):
    """Modal dialogs would block the test run: record them as errors and reject them."""
    def fake_exec(dlg, *args):
        text = dlg.text() if isinstance(dlg, QMessageBox) else ""
        errors.add("modal dialog: {} {}".format(dlg.windowTitle(), text))
        return 0

    def fake_static(*args, **kwargs):
        errors.add("message box: {}".format(" ".join(str(a) for a in args[1:3])))
        return QMessageBox.StandardButton.Cancel

    monkeypatch.setattr(QDialog, "exec", fake_exec)
    monkeypatch.setattr(QMessageBox, "exec", fake_exec)
    for name in ["critical", "warning", "question", "information"]:
        monkeypatch.setattr(QMessageBox, name, fake_static)


@pytest.fixture(autouse=True)
def slow_mode(monkeypatch):
    """--slow SECONDS: pause before each button click (the filled dialog stays visible),
    after a dialog opens and after each test step (result visible)."""
    if SLOW <= 0:
        yield
        return
    original_click = QAbstractButton.click
    original_show = QDialog.show

    def click(button):
        if button.isVisible():
            button.window().raise_()
            button.setFocus()
            slow_pause()
        original_click(button)

    def show(dlg):
        original_show(dlg)
        dlg.raise_()
        dlg.activateWindow()
        slow_pause(0.5)

    monkeypatch.setattr(QAbstractButton, "click", click)
    monkeypatch.setattr(QDialog, "show", show)
    yield
    slow_pause()


@pytest.fixture(scope="session")
def districts_plugin(iface, districts_settings, errors):
    """Started Districts plugin (main dialog open, like a click on the plugin icon)."""
    from districts.districts import Districts

    plugin = Districts(iface)
    plugin.first_start = True
    plugin.run()
    wait(500)
    if plugin.dlg.projectNames is None:
        pytest.fail("no connection to the PostgreSQL server (host, port, credentials?):\n"
                    + "\n".join(errors.all()), pytrace=False)
    errors.clear()
    yield plugin

    # remove the shortcuts of this second plugin instance (in QGIS the loaded plugin keeps its own)
    for shortcut in getattr(plugin, "my_shortcuts", []):
        shortcut.setEnabled(False)
        shortcut.setParent(None)
    try:
        plugin.dlg.close()
    except Exception:
        pass


@pytest.fixture(scope="session")
def samples_dir():
    path = os.environ.get("DISTRICTS_TEST_SAMPLES", "C:\\EQUA\\Projekte\\districts\\samples")
    if not os.path.isdir(path):
        pytest.skip("sample data not found: {} (set DISTRICTS_TEST_SAMPLES)".format(path))
    return path
