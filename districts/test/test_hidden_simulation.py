"""Option 'Hide the simulation run': IDA Districts started with -W hidden."""
import sys

from qgis.PyQt.QtCore import QSettings

from districts import simulate_process
from districts.utility_functions import hidden_simulation, workers
from districts.utility_functions.hidden_simulation import SETTING, hideSimulationCheckBox, windowOptions


def test_window_options(monkeypatch):
    monkeypatch.delenv(hidden_simulation.ENV_HIDE, raising=False)
    assert windowOptions(True) == ['-W', 'hidden']
    assert windowOptions(False) == []


def test_checkbox_keeps_the_choice_of_the_user(qgis_app):
    before = QSettings().value(SETTING)
    try:
        QSettings().setValue(SETTING, False)
        check = hideSimulationCheckBox()
        assert not check.isChecked()
        check.click()
        assert QSettings().value(SETTING, type=bool) is True
        assert hideSimulationCheckBox().isChecked()
        # set by a run from its parameters: the setting stays
        check.setChecked(False)
        assert QSettings().value(SETTING, type=bool) is True
    finally:
        if before is None:
            QSettings().remove(SETTING)
        else:
            QSettings().setValue(SETTING, before)


def test_batch_call_of_the_calibration(monkeypatch, tmp_path):
    monkeypatch.delenv(hidden_simulation.ENV_HIDE, raising=False)
    calls = []

    class Result:
        returncode = 0
        args = ''

    def run(cmd, **kw):
        calls.append(cmd)
        return Result()

    monkeypatch.setattr(workers.subprocess, 'run', run)
    config = {'pathDistricts': 'C:\\IDA\\'}
    workers.WorkerOpenModelCmd(str(tmp_path / 'c.idm'), config, progress=False, hidden=True).run()
    workers.WorkerOpenModelCmd(str(tmp_path / 'c.idm'), config, progress=False).run()
    assert ' -G1 -W hidden ' in calls[0]
    assert '-W' not in calls[1]


def test_worker_starts_ida_hidden(monkeypatch, tmp_path):
    started = []

    class FakeUtil:
        pid = '1'

        def __init__(self, plugin_dir, config, submodel='1', hidden=False):
            started.append(hidden)

        def open_document(self, path):
            raise RuntimeError

        def exit_ida(self, doc=None, timeout=30):
            pass

    monkeypatch.setattr(workers, 'Util_api', FakeUtil)
    model = tmp_path / 'network_1.idm'
    model.write_text('')
    workers.WorkerSimulateAPI(str(model), '', {}, hidden=True).run()
    workers.WorkerSimulateAPI(str(model), '', {}).run()
    workers.WorkerSimulateFilesAPI([str(model)], '', {}, hidden=True).run()
    workers.WorkerSimulateFilesAPI([str(model)], '', {}).run()
    assert started == [True, False, True, False]


# the week's process: sys.argv = [-c, simulate_process.py, model, work_dir, result_file, path, hidden]
ARGV = "import sys, json; json.dump({'ok': sys.argv[6] == '1', 'errors': []}, open(sys.argv[4], 'w'))"


def test_week_process_gets_the_option(tmp_path, monkeypatch):
    monkeypatch.setattr(simulate_process, 'pythonCommand', lambda: [sys.executable, '-c', ARGV])
    monkeypatch.setattr(simulate_process, 'POLL_S', 0.1)
    assert simulate_process.simulateInProcess('model.idm', str(tmp_path / 'a'), 'C:/IDA', hidden=True)['ok']
    assert not simulate_process.simulateInProcess('model.idm', str(tmp_path / 'b'), 'C:/IDA')['ok']


def test_hidden_by_default(qgis_app, monkeypatch):
    before = QSettings().value(SETTING)
    try:
        QSettings().remove(SETTING)
        assert hideSimulationCheckBox().isChecked()
    finally:
        if before is not None:
            QSettings().setValue(SETTING, before)

    class Broken:
        def value(self, *args, **kwargs):
            raise RuntimeError

    monkeypatch.setattr(hidden_simulation, 'QSettings', Broken)
    assert hidden_simulation.hideSimulationDefault() is True


def test_environment_hides_every_start(monkeypatch):
    """CI sets DISTRICTS_HIDE_IDA=1: also the IDA starts without a dialog run hidden"""
    monkeypatch.setenv(hidden_simulation.ENV_HIDE, '1')
    assert windowOptions(False) == ['-W', 'hidden']
    monkeypatch.setenv(hidden_simulation.ENV_HIDE, '0')
    assert windowOptions(False) == []
