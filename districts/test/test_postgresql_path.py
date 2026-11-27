"""The PostgreSQL path of the plugin settings is checked before psql / pg_dump are needed (new project, new version,
settings), and copy_schema refuses before it renames the base schema. No database."""
import pytest

from districts.utility_functions import dialog
from districts.utility_functions.db import copy_schema
from districts.utility_functions.utility import missingPostgresqlTools


def postgresql(tmp_path, tools=('psql.exe', 'pg_dump.exe')):
    (tmp_path / 'bin').mkdir()
    for tool in tools:
        (tmp_path / 'bin' / tool).write_bytes(b'')
    return str(tmp_path) + '\\'


def test_complete_installation(tmp_path):
    assert missingPostgresqlTools(postgresql(tmp_path)) == []


def test_missing_tools_are_named(tmp_path):
    assert missingPostgresqlTools(postgresql(tmp_path, ['psql.exe'])) == ['pg_dump.exe']
    assert missingPostgresqlTools(str(tmp_path / 'nowhere')) == ['psql.exe', 'pg_dump.exe']
    assert missingPostgresqlTools('') == ['psql.exe', 'pg_dump.exe']


@pytest.fixture
def warnings(monkeypatch):
    shown = []
    monkeypatch.setattr(dialog.QMessageBox, 'warning', lambda parent, title, text: shown.append(text))
    return shown


def test_check_passes_without_message(tmp_path, warnings):
    assert dialog.checkPostgresqlInstallation({'pathPostgresql': postgresql(tmp_path)})
    assert warnings == []


def test_check_warns_with_the_folder(tmp_path, warnings):
    path = str(tmp_path / 'PostgreSQL' / '18') + '\\'
    assert not dialog.checkPostgresqlInstallation({'pathPostgresql': path})
    assert len(warnings) == 1
    assert 'psql.exe, pg_dump.exe' in warnings[0] and path + 'bin' in warnings[0]


class NoCursor:
    def execute(self, sql):
        raise AssertionError('no SQL may run: ' + sql)


def test_copy_schema_refuses_before_any_sql(tmp_path):
    config = {'pathPostgresql': str(tmp_path) + '\\', 'host': 'localhost', 'port': '5432', 'projectName': 'p'}
    with pytest.raises(RuntimeError, match='psql.exe, pg_dump.exe'):
        copy_schema('base1', 'child', config, NoCursor(), '', 'user', 'secret')
