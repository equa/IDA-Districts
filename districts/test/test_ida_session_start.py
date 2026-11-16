# coding=utf-8
"""Start of an IDA Districts API session: waiting for the broker registration, opening the first model with retry,
the workers' error and the removed API delay setting (OpenSpec change wait-for-ida-start).
No IDA Districts: a fake clock, fake API answers and a temporary broker log."""
from typing import Any

import pytest

from districts.utility_functions import util as util_module
from districts.utility_functions.util import OPEN_MAX_WAIT, REGISTER_MAX_WAIT, IdaOpenError, Util_api

PID = '7180'
MODEL = 'C:\\models\\network_1.idm'
IDA_TIMEOUT = 15  # the answer time of a call sent before IDA is ready (inside idaapi2.dll)


class Clock:
    """time.monotonic / time.sleep of util.py; the IDA process starts at 0."""
    def __init__(self):
        self.now = 0.0

    def monotonic(self):
        return self.now

    def sleep(self, seconds):
        self.now += seconds


class FakeLib:
    def __init__(self):
        self.connects = 0

    def connect_to_ida(self, port, pid):
        self.connects += 1
        return True

    def openDocument(self, *args):  # only passed on to call_ida_api_function
        raise AssertionError('called directly')


class Session:
    """A Util_api without a started process: broker log, process state and openDocument answers are scripted."""
    def __init__(self, tmp_path, monkeypatch, answers=(), log='existing', register_at=None, line=None, ends_at=None):
        self.clock = Clock()
        monkeypatch.setattr(util_module, 'time', self.clock)
        self.messages = []
        messages = self.messages

        class Log:
            @staticmethod
            def logMessage(message, tag, level):
                messages.append(message)
        monkeypatch.setattr(util_module, 'QgsMessageLog', Log)
        self.log = tmp_path / 'ida_message_broker_log.txt'
        if log == 'existing':
            self.log.write_text('Registering...: 3696\nNumber of connected: 1\n')
        self.register_at = register_at
        self.line = line or 'Registering...: {}'.format(PID)
        self.ends_at = ends_at
        self.answers = list(answers)
        self.opened_at = []
        u: Any = Util_api.__new__(Util_api)
        u.broker_log = str(self.log)
        u.log_offset = util_module.fileSize(u.broker_log)
        u.start_time = 0.0
        u.pid = PID
        u.process_handle = None
        u.ida_lib = FakeLib()
        u.process_ended = lambda: self.ends_at is not None and self.clock.now >= self.ends_at
        u.call_ida_api_function = self.call
        self.util = u
        self.registered = False

    def tick(self):
        """The broker writes the registration line when its time has come."""
        if self.register_at is not None and not self.registered and self.clock.now >= self.register_at:
            with open(self.log, 'a') as f:
                f.write('{}\nNumber of connected: 2\n'.format(self.line))
            self.registered = True

    def call(self, fun, path):
        self.opened_at.append(self.clock.now)
        answer = self.answers.pop(0)
        if answer == 'Timeout...':
            self.clock.now += IDA_TIMEOUT
        else:
            self.clock.now += 0.5
        return answer


@pytest.fixture
def session(tmp_path, monkeypatch):
    def make(**kw):
        s = Session(tmp_path, monkeypatch, **kw)
        clock: Any = s.clock
        sleep = s.clock.sleep

        def sleep_and_tick(seconds):
            sleep(seconds)
            s.tick()
        clock.sleep = sleep_and_tick
        return s
    return make


# ---------------------------------------------------------------- registration
def test_registered_opens_once(session):
    s = session(answers=[1], register_at=8.0)
    assert s.util.open_document(MODEL) == 1
    assert len(s.opened_at) == 1 and 8.0 <= s.opened_at[0] < 8.5
    assert s.messages == []


def test_registration_already_in_the_log_before_the_start_is_not_taken(session):
    s = session(answers=[1], register_at=8.0)
    s.log.write_text('Registering...: {}\n'.format(PID))  # an earlier IDA process with the same pid
    s.util.log_offset = util_module.fileSize(s.util.broker_log)
    s.util.open_document(MODEL)
    assert s.opened_at[0] >= 8.0


def test_longer_pid_is_not_taken(session):
    s = session(answers=['Timeout...', 1], register_at=5.0, line='Registering...: {}1'.format(PID))
    assert s.util.open_document(MODEL) == 1
    # the line of pid 71801 did not end the wait: the call went out after REGISTER_MAX_WAIT
    assert s.opened_at[0] >= REGISTER_MAX_WAIT
    assert any('registration not found' in m for m in s.messages)


def test_partial_line_waits_for_its_end(session):
    s = session(answers=[1])
    with open(s.log, 'a') as f:
        f.write('Registering...: {}'.format(PID[:2]))  # the broker is still writing the line
    assert s.util.new_log_lines() == []
    with open(s.log, 'a') as f:
        f.write('{}\n'.format(PID[2:]))
    assert s.util.new_log_lines() == ['Registering...: {}'.format(PID)]


def test_no_broker_log_opens_at_once_and_retries(session):
    s = session(answers=['Timeout...', 1], log='missing')
    assert s.util.open_document(MODEL) == 1
    assert s.opened_at == [0.0, IDA_TIMEOUT]
    assert s.util.ida_lib.connects == 2
    assert any('registration not found' in m for m in s.messages)
    assert any('not ready' in m for m in s.messages)


def test_process_ended_during_the_start(session):
    s = session(answers=[], ends_at=3.0)
    with pytest.raises(IdaOpenError) as e:
        s.util.open_document(MODEL)
    assert e.value.path == MODEL and 'ended during the start' in e.value.text
    assert s.opened_at == [] and s.clock.now < 4.0


# ---------------------------------------------------------------- opening with retry
def test_timeout_then_handle(session):
    s = session(answers=['Timeout...', 'Timeout...', 1], register_at=8.0)
    assert s.util.open_document(MODEL) == 1
    assert len(s.opened_at) == 3 and s.util.ida_lib.connects == 3
    assert sum('not ready' in m for m in s.messages) == 2


def test_error_text_fails_at_once(session):
    s = session(answers=['File not found'], register_at=8.0)
    with pytest.raises(IdaOpenError) as e:
        s.util.open_document(MODEL)
    assert (e.value.path, e.value.text) == (MODEL, 'File not found')
    assert len(s.opened_at) == 1


def test_maximum_wait(session):
    s = session(answers=['Timeout...'] * 50, register_at=8.0)
    with pytest.raises(IdaOpenError) as e:
        s.util.open_document(MODEL)
    assert e.value.text == 'Timeout...'
    assert OPEN_MAX_WAIT <= s.clock.now < OPEN_MAX_WAIT + IDA_TIMEOUT + 1


# ---------------------------------------------------------------- workers
class FakeUtil:
    """Util_api of a worker: the opening fails, exit_ida is recorded."""
    instances = []

    def __init__(self, plugin_dir, config, submodel='1'):
        self.pid = PID
        self.exited = False
        FakeUtil.instances.append(self)

    def open_document(self, path):
        raise IdaOpenError(path, 'Timeout...')

    def exit_ida(self, doc=None, timeout=30):
        self.exited = True


@pytest.mark.parametrize('worker_name', ['WorkerSimulateAPI', 'WorkerSimulateFilesAPI', 'WorkerOpenAPI',
                                         'WorkerOpenRunScriptAPI'])
def test_worker_reports_failed_opening(worker_name, monkeypatch, tmp_path):
    from districts.utility_functions import workers
    from districts.utility_functions.translations import tr_msg
    monkeypatch.setattr(workers, 'Util_api', FakeUtil)
    FakeUtil.instances = []
    model = tmp_path / 'network_1.idm'
    model.write_text('')
    path = str(model)
    worker: Any = {
        'WorkerSimulateAPI': lambda: workers.WorkerSimulateAPI(path, '', {}),
        'WorkerSimulateFilesAPI': lambda: workers.WorkerSimulateFilesAPI([path], '', {}),
        'WorkerOpenAPI': lambda: workers.WorkerOpenAPI(path, '', {}),
        'WorkerOpenRunScriptAPI': lambda: workers.WorkerOpenRunScriptAPI(path, '', {}, '(nil)', exit_ida=True),
    }[worker_name]()
    errors, status = [], []
    worker.signals.error.connect(errors.append)
    worker.signals.status.connect(status.append)
    worker.run()
    assert errors == [tr_msg('IDA Districts could not open {}: {}').format(path, 'Timeout...')]
    if worker_name in ('WorkerSimulateAPI', 'WorkerSimulateFilesAPI'):
        assert status == [tr_msg('Simulation failed')]
    assert FakeUtil.instances[0].exited


# ---------------------------------------------------------------- setting removed
def test_no_api_delay_setting(qgis_iface):
    from districts.districts_dialog import DistrictsSettingsDialog
    from districts.utility_functions.utility import load_plugin_settings
    assert 'districts_api_delay' not in load_plugin_settings()
    dlg = DistrictsSettingsDialog(None)
    assert not hasattr(dlg, 'lineEdit_districts_api_delay')
