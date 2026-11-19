# coding=utf-8
"""AI assistant on a project (OpenSpec change ai-chat-panel, spec ai-access): the table public.ai_settings in a new and
an old project, the permission and the switched-off tools for the chat and the MCP bridge, the same decision for a
second connection, the API key in the QGIS authentication database.

    python -m pytest test/test_ai_e2e.py -v -s   (--keep-projects)
"""
from types import SimpleNamespace

import psycopg2.extras
import pytest

from districts.ai import access
from districts.ida_ph import addBaseVersion
from districts.ida_ph_dialog import IDA_Districts_NameDialog
from districts.mcp import tools as mcp_tools
from districts.upgrade import upgradeProjectDB
from districts.utility_functions.db import dbConnect
from districts.utility_functions.translations import tr

from .conftest import wait
from .test_workflow import DB_DEFAULTS, create_project, delete_project, project_name_for

pytestmark = [pytest.mark.e2e]


@pytest.fixture(scope='class')
def ai(request, districts_plugin, errors):
    state = SimpleNamespace(plugin=districts_plugin, project_name=project_name_for('ai_access'))
    yield state
    if not request.config.getoption('--keep-projects'):
        delete_project(districts_plugin, errors, state.project_name)


@pytest.mark.incremental
class TestAiAccess:
    def test_new_project_is_not_allowed(self, ai, errors):
        plugin = ai.plugin
        create_project(plugin, errors, ai.project_name, DB_DEFAULTS)
        plugin.dlg_addBase = IDA_Districts_NameDialog(tr('@default', 'add_base_version'), tr('@default', 'add_base_version'), '', '')
        plugin.dlg_addBase.input.setText('base1')
        addBaseVersion(plugin.dlg_addBase, plugin)
        wait(500)
        errors.check()
        assert access.loadAiSettings(plugin.cur) == {'allowed': False, 'disabled_tools': [], 'changed_by': None, 'changed_at': None}

    def test_old_project_gets_the_table(self, ai):
        cur = ai.plugin.cur
        cur.execute('DROP TABLE public.ai_settings;')
        assert access.loadAiSettings(cur)['allowed'] is False
        upgradeProjectDB(cur)
        cur.execute("SELECT to_regclass('public.ai_settings') IS NOT NULL AS ok;")
        assert cur.fetchone()['ok'] and access.loadAiSettings(cur)['allowed'] is False

    def test_not_allowed_for_chat_and_bridge(self, ai):
        ctx = mcp_tools.ToolContext(ai.plugin)
        with pytest.raises(mcp_tools.ToolError, match='not allowed'):
            mcp_tools.callTool(ctx, 'run_checks', {})
        mcp_tools.checkPermission(ctx, 'search_help')  # the public wiki stays available
        assert {t['name'] for t in mcp_tools.allowedTools(ctx)} == set(access.ALWAYS_ALLOWED)

    def test_allowed_with_a_tool_switched_off(self, ai):
        plugin = ai.plugin
        access.saveAiSettings(plugin.cur, True, ['render_map'])
        ctx = mcp_tools.ToolContext(plugin)
        names = {t['name'] for t in mcp_tools.allowedTools(ctx)}
        assert 'render_map' not in names and 'run_checks' in names
        with pytest.raises(mcp_tools.ToolError, match='switched off'):
            mcp_tools.checkPermission(ctx, 'render_map')
        assert mcp_tools.callTool(ctx, 'run_checks', {'scope': 'qgis'})['version'] == 'base1'

    def test_same_decision_for_a_second_connection(self, ai):
        conn = dbConnect(dict(ai.plugin.config), False)
        try:
            settings = access.loadAiSettings(conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor))
        finally:
            conn.close()
        assert settings['allowed'] and settings['disabled_tools'] == ['render_map'] and settings['changed_by']

    def test_api_key_in_the_authentication_database(self, ai, monkeypatch):
        monkeypatch.delenv('ANTHROPIC_API_KEY', raising=False)
        config = dict(ai.plugin.config, ai_auth_id='')
        auth_id = access.storeApiKey(config, 'sk-ant-test-key')
        try:
            config['ai_auth_id'] = auth_id
            assert auth_id and access.storedApiKey(config) == 'sk-ant-test-key'
            assert access.keySource(config) == ('settings', 'sk-ant-test-key')
        finally:
            assert access.storeApiKey(config, '') == ''
        assert access.storedApiKey(config) is None
