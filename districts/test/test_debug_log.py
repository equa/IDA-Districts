"""Debug log (utility_functions/debug_log.py) and its settings in the settings dialog."""
import os
import threading

import pytest

from districts.utility_functions import debug_log


@pytest.fixture
def log_folder(tmp_path, monkeypatch):
    monkeypatch.setattr(debug_log, 'log_dir', lambda: str(tmp_path))
    debug_log.shutdown()
    yield tmp_path
    debug_log.shutdown()


def read_log(folder):
    path = os.path.join(str(folder), debug_log.LOG_FILE_NAME)
    if not os.path.exists(path):
        return ''
    with open(path, encoding='utf-8') as f:
        return f.read()


def test_off_writes_nothing(log_folder, capsys):
    debug_log.configure(False)
    debug_log.dprint('should not appear')
    assert not debug_log.debug_enabled()
    assert read_log(log_folder) == ''
    assert 'should not appear' not in capsys.readouterr().out


def test_on_writes_file_with_location(log_folder, capsys):
    debug_log.configure(True)
    assert debug_log.debug_enabled()
    debug_log.dprint('value', 42, {'a': 1})
    debug_log.dprint('a', 'b', sep='|')
    debug_log.shutdown()
    text = read_log(log_folder)
    assert 'Districts Modeler debug log started' in text
    assert "value 42 {'a': 1}" in text
    assert 'a|b' in text
    # source location of the caller, not of dprint
    assert 'test_debug_log.test_on_writes_file_with_location:' in text
    assert 'value 42' not in capsys.readouterr().out  # no console output without the option


def test_console_echo(log_folder, capsys):
    debug_log.configure(True, console=True)
    debug_log.dprint('to console')
    assert 'to console' in capsys.readouterr().out
    assert 'to console' in read_log(log_folder)


def test_switch_off_again(log_folder):
    debug_log.configure(True)
    debug_log.dprint('first')
    debug_log.configure(False)
    debug_log.dprint('second')
    debug_log.configure(True)
    debug_log.dprint('third')
    debug_log.shutdown()
    text = read_log(log_folder)
    assert 'first' in text and 'third' in text and 'second' not in text


def test_unprintable_argument_does_not_raise(log_folder):
    class Bad:
        def __str__(self):
            raise ValueError('no str')
    debug_log.configure(True)
    debug_log.dprint(Bad())
    debug_log.shutdown()
    assert 'could not be formatted' in read_log(log_folder)


def test_threads(log_folder):
    debug_log.configure(True)
    threads = [threading.Thread(target=lambda k=k: [debug_log.dprint('thread', k, i) for i in range(50)], name='worker{}'.format(k))
               for k in range(4)]
    for t in threads:
        t.start()
    for t in threads:
        t.join()
    debug_log.shutdown()
    text = read_log(log_folder)
    for k in range(4):
        assert '[worker{}]'.format(k) in text
        assert 'thread {} 49'.format(k) in text


def test_log_dir_override(tmp_path, monkeypatch):
    monkeypatch.setenv('DISTRICTS_DEBUG_LOG_DIR', str(tmp_path / 'logs'))
    assert debug_log.log_dir() == str(tmp_path / 'logs')
    assert os.path.isdir(str(tmp_path / 'logs'))
    assert debug_log.log_file() == os.path.join(str(tmp_path / 'logs'), debug_log.LOG_FILE_NAME)


def test_settings_dialog(qgis_app, log_folder, monkeypatch):
    from districts import districts_dialog

    monkeypatch.setattr(districts_dialog, 'debug_log_dir', lambda: str(log_folder))
    monkeypatch.setattr(districts_dialog, 'debug_log_file', lambda: os.path.join(str(log_folder), debug_log.LOG_FILE_NAME))

    class Main:
        def folderDialog(self, *args):
            pass

    dlg = districts_dialog.DistrictsSettingsDialog(Main())
    assert dlg.lineEdit_debugLogFile.text().endswith(debug_log.LOG_FILE_NAME)
    dlg.checkBox_debug.setChecked(False)
    assert not dlg.checkBox_debug_console.isEnabled()
    dlg.checkBox_debug.setChecked(True)
    assert dlg.checkBox_debug_console.isEnabled()
    dlg.close()
