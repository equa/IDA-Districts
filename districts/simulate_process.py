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


def simulateInProcess(model, work_dir, path_districts):
    """blocks until the child process ends; returns {'ok': bool, 'errors': [...]}"""
    os.makedirs(work_dir, exist_ok=True)
    result_file = os.path.join(work_dir, 'result.json')
    log_file = os.path.join(work_dir, 'runner.log')
    if os.path.exists(result_file):
        os.remove(result_file)
    cmd = pythonCommand() + [os.path.abspath(__file__), model, work_dir, result_file, path_districts]
    flags = getattr(subprocess, 'CREATE_NO_WINDOW', 0)
    with open(log_file, 'w') as log:
        process = subprocess.run(cmd, stdout=log, stderr=subprocess.STDOUT, creationflags=flags)  # nosec B603
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
