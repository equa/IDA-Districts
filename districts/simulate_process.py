# coding=utf-8
"""Simulate one IDA Districts model in its own process (the parallel weeks of a period run).

    python-qgis.bat simulate_process.py <model.idm> <work_dir> <result.json> <path IDA Districts>

Own process: idaapi2.dll holds one IDA connection per process, so parallel simulations in the QGIS process would
switch each other's connection. Own TEMP folder (<work_dir>/tmp): parallel IDA sessions would overwrite each other's
files in %TEMP%/idamod* otherwise.
"""
import glob
import json
import os
import subprocess  # nosec B404
import sys
import threading
import time
import traceback

# after IDA ended, the simulation call gets this long to return before the process gives up
IDA_ENDED_GRACE_S = 60
SOLVER_TAIL_LINES = 12
# IDA writes this line into its log in the week's TEMP folder when the solver runs; undocumented, as the broker log
SOLVER_STARTED = 'Service subscriber connected'
# an IDA that hangs at its start stays alive without an answer (seen when another IDA started at the same moment);
# the week is stopped after this long without a solver and fails, the period run simulates it again
SOLVER_START_TIMEOUT_S = 600
POLL_S = 2


def solverStarted(work_dir):
    for path in glob.glob(os.path.join(work_dir, 'tmp', 'ida_log_*.txt')):
        try:
            with open(path, errors='replace') as f:
                if SOLVER_STARTED in f.read():
                    return True
        except OSError:
            pass
    return False


def killTree(pid):
    """the week's process with its children (IDA Districts is started by it)"""
    subprocess.run(['taskkill', '/T', '/F', '/PID', str(pid)], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,  # nosec B603 B607
                   creationflags=getattr(subprocess, 'CREATE_NO_WINDOW', 0))


def solverTail(tmp):
    """the last lines of the solver output (SCREEN.TXT in IDA's folder in the week's TEMP), the reason of an abort"""
    lines = []
    for path in glob.glob(os.path.join(tmp, 'idamod*', 'SCREEN.TXT')):
        try:
            with open(path, errors='replace') as f:
                lines += [line.strip() for line in f if line.strip()]
        except OSError:
            pass
    return lines[-SOLVER_TAIL_LINES:]


def writeResult(result_file, ok, errors):
    with open(result_file, 'w') as f:
        json.dump({'ok': ok, 'errors': errors}, f)


def watchIda(worker, result_file, tmp):
    """an IDA that crashed or was closed leaves a call into idaapi2.dll waiting; the week then fails instead of hanging"""
    ended_at = None
    while True:
        time.sleep(1)
        util = getattr(worker, 'util', None)
        if util is None or not util.process_ended():
            continue
        ended_at = ended_at or time.monotonic()
        if time.monotonic() - ended_at >= IDA_ENDED_GRACE_S:
            writeResult(result_file, False, ['IDA Districts (pid {}) ended without an answer'.format(util.pid)] + solverTail(tmp))
            os._exit(1)


def pythonCommand():
    """the QGIS Python for a child process: python-qgis*.bat sets the environment of QGIS' Python"""
    if os.path.basename(sys.executable).lower().startswith('python'):
        return [sys.executable]
    folders = [os.path.dirname(sys.executable)]
    try:
        from qgis.core import QgsApplication
        folders.append(os.path.join(QgsApplication.prefixPath(), '..', '..', 'bin'))
    except Exception:  # nosec B110
        pass
    for folder in folders:
        found = sorted(glob.glob(os.path.join(folder, 'python-qgis*.bat')))
        if found:
            return [os.path.normpath(found[0])]
    raise RuntimeError('QGIS Python (python-qgis.bat) not found next to {}'.format(sys.executable))


def simulateInProcess(model, work_dir, path_districts, start_timeout=SOLVER_START_TIMEOUT_S):
    """blocks until the child process ends; returns {'ok': bool, 'errors': [...]}; a week whose solver has not started
    after start_timeout seconds is stopped and fails"""
    os.makedirs(work_dir, exist_ok=True)
    result_file = os.path.join(work_dir, 'result.json')
    log_file = os.path.join(work_dir, 'runner.log')
    if os.path.exists(result_file):
        os.remove(result_file)
    cmd = pythonCommand() + [os.path.abspath(__file__), model, work_dir, result_file, path_districts]
    flags = getattr(subprocess, 'CREATE_NO_WINDOW', 0)
    with open(log_file, 'w') as log:
        process = subprocess.Popen(cmd, stdout=log, stderr=subprocess.STDOUT, creationflags=flags)  # nosec B603
        start, started = time.monotonic(), False
        while process.poll() is None:
            time.sleep(POLL_S)
            started = started or solverStarted(work_dir)
            if not started and time.monotonic() - start > start_timeout:
                killTree(process.pid)
                process.wait()
                return {'ok': False, 'errors': ['IDA Districts did not start the solver within {} s, stopped'.format(start_timeout)]}
    if not os.path.exists(result_file):
        with open(log_file, errors='replace') as log:
            return {'ok': False, 'errors': ['simulation process failed (exit code {}): {}'.format(process.returncode, log.read()[-2000:])]}
    with open(result_file) as f:
        return json.load(f)


def main(model, work_dir, result_file, path_districts):
    errors: list = []
    ok = False
    tmp = os.path.join(work_dir, 'tmp')
    try:
        # before IDA is started: IDA inherits the environment of this process
        os.makedirs(tmp, exist_ok=True)
        os.environ['TEMP'] = tmp
        os.environ['TMP'] = tmp

        plugin_dir = os.path.dirname(os.path.abspath(__file__))
        sys.path.insert(0, os.path.dirname(plugin_dir))
        from qgis.core import QgsApplication
        app = QgsApplication([], False)
        app.initQgis()
        messages = []
        QgsApplication.messageLog().messageReceived.connect(
            lambda message, tag, level: messages.append(message) if tag == 'Districts' else None)

        from districts.utility_functions.translations import tr_msg
        from districts.utility_functions.workers import WorkerSimulateAPI

        status = []
        worker = WorkerSimulateAPI(model, plugin_dir, {'pathDistricts': os.path.join(path_districts, '')})
        worker.signals.status.connect(status.append)
        worker.signals.error.connect(errors.append)
        threading.Thread(target=watchIda, args=(worker, result_file, tmp), daemon=True).start()
        worker.run()  # synchronously in this process
        app.processEvents()
        # compared here: the parent may translate the status text
        ok = tr_msg('Simulation finished') in status and not errors
        if not ok:
            errors += messages + solverTail(tmp)
    except Exception:
        errors.append(traceback.format_exc())
    writeResult(result_file, ok, errors)


if __name__ == '__main__':
    main(*sys.argv[1:])
    # no Qt/QGIS cleanup to wait for (exit_ida already closed IDA)
    os._exit(0)
