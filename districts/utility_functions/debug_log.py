"""Debug log of the Districts Modeler plugin.

``dprint(...)`` is a drop-in replacement for the former debug prints (``#print(...)``
that the old debug mode uncommented in the source files). It takes the same
positional arguments as ``print`` and writes them, with time stamp, thread and
source location, to a rotating log file when the debug mode is switched on in the
plugin settings; optionally they are also printed to the Python console.
With the debug mode off ``dprint`` returns at once.

The log file is kept in the QGIS profile (``<profile>/districts/logs``), so it
survives plugin updates.
"""
import logging
import logging.handlers
import os
import sys
import tempfile
import threading

LOGGER_NAME = 'districts'
LOG_FILE_NAME = 'districts_debug.log'
MAX_BYTES = 10 * 1024 * 1024
BACKUP_COUNT = 5
LOG_FORMAT = '%(asctime)s.%(msecs)03d [%(threadName)s] %(module)s.%(funcName)s:%(lineno)d  %(message)s'
DATE_FORMAT = '%Y-%m-%d %H:%M:%S'

_logger = logging.getLogger(LOGGER_NAME)
_logger.propagate = False  # not into the root logger / QGIS
_logger.setLevel(logging.WARNING)
# plugin reload: the logger outlives this module, close the handlers of the previous load
for _old in list(_logger.handlers):
    _logger.removeHandler(_old)
    try:
        _old.close()
    except Exception:
        pass

_lock = threading.Lock()
_enabled = False
_console = False
_handler = None


class _QuietRotatingFileHandler(logging.handlers.RotatingFileHandler):
    """Rotating file handler that never raises or prints tracebacks
    (e.g. when a second QGIS instance holds the file during the rotation on Windows)."""

    def handleError(self, record):
        pass


def log_dir():
    """Folder of the debug log files (created if missing); environment variable
    DISTRICTS_DEBUG_LOG_DIR overrides <profile>/districts/logs (tests, CI)."""
    override = os.environ.get('DISTRICTS_DEBUG_LOG_DIR')
    if override:
        os.makedirs(override, exist_ok=True)
        return override
    try:
        from qgis.core import QgsApplication
        base = QgsApplication.qgisSettingsDirPath()
    except Exception:
        base = ''
    if not base:
        base = tempfile.gettempdir()
    path = os.path.join(base, 'districts', 'logs')
    os.makedirs(path, exist_ok=True)
    return path


def log_file():
    """Path of the current debug log file."""
    return os.path.join(log_dir(), LOG_FILE_NAME)


def debug_enabled():
    """True while the debug mode is on (guard for debug output with expensive arguments)."""
    return _enabled


def get_logger():
    """The plugin logger (logger.debug/info/... are written while the debug mode is on,
    warnings and errors always once a log file was opened)."""
    return _logger


def _header():
    lines = ['=' * 80, 'Districts Modeler debug log started (pid {})'.format(os.getpid())]
    try:
        from qgis.core import Qgis
        lines.append('QGIS {} / Python {}'.format(Qgis.version(), sys.version.split()[0]))
    except Exception:
        lines.append('Python {}'.format(sys.version.split()[0]))
    try:
        from .utility import get_districts_plugin_dir
        lines.append('plugin folder {}'.format(get_districts_plugin_dir()))
    except Exception:
        pass
    return '\n'.join(lines)


def configure(debug, console=False):
    """Switch the debug log on or off (called with the plugin settings).

    debug: write the dprint output (and logger.debug/info) to the log file
    console: additionally print the dprint output to the Python console
    """
    global _enabled, _console, _handler
    debug = bool(debug)
    with _lock:
        _console = bool(console) and debug
        if debug and _handler is None:
            try:
                handler = _QuietRotatingFileHandler(
                    log_file(), maxBytes=MAX_BYTES, backupCount=BACKUP_COUNT, encoding='utf-8')
                handler.setFormatter(logging.Formatter(LOG_FORMAT, DATE_FORMAT))
                _logger.addHandler(handler)
                _handler = handler
            except Exception as e:
                # no log file possible -> fall back to the console
                sys.stderr.write('Districts: debug log file could not be opened: {}\n'.format(e))
                _console = True
        was_enabled = _enabled
        _enabled = debug
        _logger.setLevel(logging.DEBUG if debug else logging.WARNING)
    if debug and not was_enabled and _handler is not None:
        _logger.info(_header())


def shutdown():
    """Close the log file (plugin unload / reload)."""
    global _enabled, _console, _handler
    with _lock:
        _enabled = False
        _console = False
        _logger.setLevel(logging.WARNING)
        if _handler is not None:
            _logger.removeHandler(_handler)
            try:
                _handler.close()
            except Exception:
                pass
            _handler = None


def dprint(*args, sep=' ', end=None, file=None, flush=False):
    """Debug print: like print, written to the debug log (only in debug mode)."""
    if not _enabled:
        return
    try:
        msg = (' ' if sep is None else sep).join(str(a) for a in args)
    except Exception as e:
        msg = '<debug message could not be formatted: {!r}>'.format(e)
    try:
        _logger.debug(msg, stacklevel=2)
    except Exception:
        pass
    if _console:
        try:
            print(msg)
        except Exception:
            pass
