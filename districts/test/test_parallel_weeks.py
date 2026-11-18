# coding=utf-8
"""Start of the parallel weeks of a period run and an IDA that ends without an answer (OpenSpec change
representative-periods, D5). No IDA Districts: fake timers, workers, IDA logs and API answers."""
import json
import os
from types import SimpleNamespace
from typing import Any

import pytest

from districts import representative_periods as rp
from districts import simulate_process
from districts.utility_functions import util as util_module
from districts.utility_functions.util import Util_api

FIRST_LINE = 'MSG 15:59:14.806 zmq_get_solver_socket() [...] Listvar requester connected to tcp://127.0.0.1:62540.\n'
SOLVER_LINE = 'MSG 15:59:23.437 zmq_subscribe_solver() [...] Service subscriber connected to  tcp://127.0.0.1:62598.\n'


def ida_log(work_dir, solver=False):
    tmp = work_dir / 'tmp'
    tmp.mkdir(parents=True, exist_ok=True)
    (tmp / 'ida_log_32.txt').write_text('Tue Nov 17 14:59:14 2026\n' + FIRST_LINE + (SOLVER_LINE if solver else ''))


def test_solver_started(tmp_path):
    assert not rp.solverStarted(str(tmp_path))
    ida_log(tmp_path)
    assert not rp.solverStarted(str(tmp_path))
    ida_log(tmp_path, solver=True)
    assert rp.solverStarted(str(tmp_path))


class Timers:
    def __init__(self):
        self.pending = []

    def singleShot(self, ms, fn):
        self.pending.append(fn)

    def fire(self):
        pending, self.pending = self.pending, []
        for fn in pending:
            fn()


class Pool:
    def __init__(self):
        self.started = []

    def start(self, k):
        self.started.append(k)


class Clock:
    def __init__(self):
        self.now = 0.0

    def monotonic(self):
        return self.now


class Memory:
    """free commit [MB] as GlobalMemoryStatusEx would report it"""
    def __init__(self):
        self.free = 100000.0

    def __call__(self):
        return self.free


@pytest.fixture
def run(tmp_path, monkeypatch):
    timers, pool, clock, memory = Timers(), Pool(), Clock(), Memory()
    monkeypatch.setattr(rp, 'QTimer', timers)
    monkeypatch.setattr(rp, 'QThreadPool', type('P', (), {'globalInstance': staticmethod(lambda: pool)}))
    monkeypatch.setattr(rp, 'time', clock)
    monkeypatch.setattr(rp, 'freeMemoryMB', memory)
    # PeriodRun's methods on a plain object: a QObject without its __init__ takes no attributes
    r: Any = SimpleNamespace(done=False, stage='simulate', retry=False, relays=[], week_memory=rp.WEEK_MEMORY_MB, week_measured=False)
    for name in ('startNextSim', 'waitForSolver', 'running', 'measureWeek', 'onPeriodResult'):
        setattr(r, name, (lambda name: lambda *a: getattr(rp.PeriodRun, name)(r, *a))(name))
    r.makeWorker = lambda k: k
    r.files = [str(tmp_path / 'period_{}'.format(k) / 'network_1.idm') for k in (1, 2, 3)]
    r.work_dirs = [str(tmp_path / 'period_{}'.format(k)) for k in (1, 2, 3)]
    r.started_periods, r.finished_periods, r.failed_periods = set(), set(), set()
    r.queue = [0, 1, 2]
    r.lines, r.ends = [], []
    r.dlg = SimpleNamespace(log=r.lines.append, update_progress=lambda v: None)
    r.loadPeriod = lambda: r.ends.append('loaded')
    r.finish = lambda message, error=False: r.ends.append(message)
    r.timers, r.pool, r.clock, r.tmp, r.memory = timers, pool, clock, tmp_path, memory
    return r


def test_next_week_starts_when_the_solver_runs(run):
    run.startNextSim()
    assert run.pool.started == [0]
    # IDA started, its solver not yet
    ida_log(run.tmp / 'period_1')
    for _ in range(5):
        run.timers.fire()
    assert run.pool.started == [0]
    ida_log(run.tmp / 'period_1', solver=True)
    run.timers.fire()
    assert run.pool.started == [0, 1]
    ida_log(run.tmp / 'period_2', solver=True)
    run.timers.fire()
    assert run.pool.started == [0, 1, 2]
    # the last week: nothing left to wait for
    assert not run.timers.pending


def test_a_finished_week_releases_the_next(run):
    run.startNextSim()
    run.onPeriodResult(0, {'ok': True})
    run.timers.fire()
    assert run.pool.started == [0, 1]


def test_without_the_solver_line_the_next_week_starts_after_the_max_wait(run):
    run.startNextSim()
    run.clock.now = rp.SIM_START_MAX_WAIT_S - 1
    run.timers.fire()
    assert run.pool.started == [0]
    run.clock.now = rp.SIM_START_MAX_WAIT_S
    run.timers.fire()
    assert run.pool.started == [0, 1]
    assert run.lines and 'Period 1' in run.lines[0]


def test_a_finished_run_starts_no_more_weeks(run):
    run.startNextSim()
    ida_log(run.tmp / 'period_1', solver=True)
    run.done = True
    run.timers.fire()
    assert run.pool.started == [0]


def test_the_next_week_waits_for_free_memory(run):
    """8 GB PC: about 8 GB free commit, a week takes 3.4 GB"""
    run.memory.free = 8000
    run.startNextSim()
    # the solver of week 1 committed its memory: the measured need replaces the estimate
    run.memory.free = 4600
    ida_log(run.tmp / 'period_1', solver=True)
    run.timers.fire()
    assert run.week_memory == pytest.approx(3400 * rp.WEEK_MEMORY_FACTOR)
    assert run.pool.started == [0]
    assert any('Period 2' in line and 'memory' in line for line in run.lines)
    for _ in range(3):
        run.timers.fire()
    assert run.pool.started == [0]
    # week 1 done: nothing runs, week 2 starts whatever the memory
    run.memory.free = 8000
    run.onPeriodResult(0, {'ok': True})
    run.timers.fire()
    assert run.pool.started == [0, 1]


def test_enough_memory_for_all_weeks(run):
    run.memory.free = 20000
    run.startNextSim()
    run.memory.free = 16600
    ida_log(run.tmp / 'period_1', solver=True)
    run.timers.fire()
    run.memory.free = 13200
    ida_log(run.tmp / 'period_2', solver=True)
    run.timers.fire()
    assert run.pool.started == [0, 1, 2]


def test_a_failed_week_is_simulated_again_alone(run):
    for _ in range(3):
        run.startNextSim()
    run.onPeriodResult(0, {'ok': True})
    run.onPeriodResult(1, {'ok': False, 'errors': ['SUPERLU_MALLOC fails']})
    assert run.pool.started == [0, 1, 2]
    run.onPeriodResult(2, {'ok': True})
    assert run.pool.started == [0, 1, 2, 1]
    assert any('again' in line for line in run.lines)
    assert not run.ends
    run.onPeriodResult(1, {'ok': True})
    assert run.ends == ['loaded']


def test_a_week_failing_again_fails_the_run(run):
    for _ in range(3):
        run.startNextSim()
    run.onPeriodResult(0, {'ok': False})
    run.onPeriodResult(1, {'ok': False})
    run.onPeriodResult(2, {'ok': True})
    # one at a time: week 2 waits for week 1
    assert run.pool.started == [0, 1, 2, 0]
    run.onPeriodResult(0, {'ok': True})
    assert run.pool.started == [0, 1, 2, 0, 1]
    run.onPeriodResult(1, {'ok': False})
    assert len(run.ends) == 1 and '2' in run.ends[0] and run.ends[0] != 'loaded'


class FakeLib:
    def __init__(self, replies):
        self.replies = list(replies)

    def pollForQueuedResults(self, buffer, size):
        buffer.value = (self.replies.pop(0) if self.replies else '').encode()
        return 0


def session(monkeypatch, replies, ended):
    messages = []
    monkeypatch.setattr(util_module.time, 'sleep', lambda s: None)
    monkeypatch.setattr(util_module, 'QgsMessageLog', type('L', (), {'logMessage': staticmethod(lambda m, *a: messages.append(m))}))
    u: Any = Util_api.__new__(Util_api)
    u.pid = '14520'
    u.ida_lib = FakeLib(replies)
    u.process_ended = lambda: len(u.ida_lib.replies) == 0 and ended
    return u, messages


def test_poll_returns_when_ida_ended_without_an_answer(monkeypatch):
    u, messages = session(monkeypatch, [], ended=True)
    assert u.ida_poll_results_queue(0) == ''
    assert u.ida_poll_results_queue_j(0) == ''
    assert any('14520' in m and 'without an answer' in m for m in messages)


def test_poll_waits_through_empty_replies_while_ida_runs(monkeypatch):
    answer = json.dumps([{'value': True}, {'value': 42}])
    u, messages = session(monkeypatch, ['', '', answer], ended=False)
    assert u.ida_poll_results_queue(0) == 42
    # an empty reply is no error
    assert not messages


def test_solver_tail(tmp_path):
    folder = tmp_path / 'idamod52'
    folder.mkdir()
    (folder / 'SCREEN.TXT').write_text('\n'.join(['line {}'.format(i) for i in range(30)] + ['', ' Unknown module type: ', '   Flowmeter2', ' Run aborted']))
    tail = simulate_process.solverTail(str(tmp_path))
    assert len(tail) == simulate_process.SOLVER_TAIL_LINES
    assert tail[-3:] == ['Unknown module type:', 'Flowmeter2', 'Run aborted']
    assert simulate_process.solverTail(str(tmp_path / 'missing')) == []


def test_watchdog_ends_the_week_when_ida_ended(tmp_path, monkeypatch):
    class Exit(Exception):
        pass

    def exit_(code):
        raise Exit(code)
    monkeypatch.setattr(simulate_process, 'IDA_ENDED_GRACE_S', 0)
    monkeypatch.setattr(simulate_process.time, 'sleep', lambda s: None)
    monkeypatch.setattr(simulate_process.os, '_exit', exit_)
    worker = type('W', (), {})()
    worker.util = type('U', (), {'pid': '14520', 'process_ended': lambda self: True})()
    result = tmp_path / 'result.json'
    with pytest.raises(Exit):
        simulate_process.watchIda(worker, str(result), str(tmp_path))
    data = json.loads(result.read_text())
    assert data['ok'] is False and '14520' in data['errors'][0]
    assert os.path.exists(result)


def test_free_memory_is_read():
    free = rp.freeMemoryMB()
    assert free is not None and free > 0
