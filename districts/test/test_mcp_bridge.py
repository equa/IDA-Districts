# coding=utf-8
"""Bridge of the AI connection in QGIS (OpenSpec change ai-mcp-connection, spec ai-bridge): switched on and off, the
state file, the token, the tool registry, errors of a tool; the menu actions of the plugin.

    python -m pytest test/test_mcp_bridge.py -v
"""
import json
import os
import socket
import threading
from types import SimpleNamespace

import pytest

from districts.mcp import tools as mcp_tools
from districts.mcp.bridge import Bridge, mcpConfiguration

from .conftest import wait_until


def plugin_without_project():
    return SimpleNamespace(config={'projectName': '', 'versionName': ''}, process_running=False, plugin_dir='', iface=None)


class Client:
    """requests from a thread: the bridge answers in the main thread's event loop"""

    def __init__(self, port):
        self.sock = socket.create_connection(('127.0.0.1', port), timeout=30)
        self.file = self.sock.makefile('rb')

    def ask(self, request):
        result = {}

        def work():
            self.sock.sendall((json.dumps(request) + '\n').encode('utf-8'))
            result['answer'] = json.loads(self.file.readline())

        thread = threading.Thread(target=work, daemon=True)
        thread.start()
        wait_until(lambda: 'answer' in result, 30, 'answer of the bridge')
        return result['answer']

    def close(self):
        self.file.close()
        self.sock.close()


@pytest.fixture
def bridge(tmp_path):
    b = Bridge(plugin_without_project(), state_file=str(tmp_path / 'districts_mcp.json'))
    yield b
    b.stop()


def test_switched_on_and_off(bridge):
    port = bridge.start()
    state = json.loads(open(bridge.state_file, encoding='utf-8').read())
    assert state['port'] == port and len(state['token']) == 32 and state['pid'] == os.getpid()
    assert bridge.server.serverAddress().toString() == '127.0.0.1'
    bridge.stop()
    assert not os.path.exists(bridge.state_file) and not bridge.isRunning()
    with pytest.raises(OSError):
        socket.create_connection(('127.0.0.1', port), timeout=2).close()


def test_wrong_token_is_refused_and_no_tool_runs(bridge, monkeypatch):
    called = []
    monkeypatch.setattr(mcp_tools, 'callTool', lambda *a: called.append(a))
    client = Client(bridge.start())
    try:
        answer = client.ask({'id': 7, 'token': 'wrong', 'tool': 'project_state'})
        assert answer == {'id': 7, 'ok': False, 'error': 'invalid token'}
        assert not called
    finally:
        client.close()


def test_list_tools_and_errors(bridge):
    client = Client(bridge.start())
    try:
        answer = client.ask({'id': 1, 'token': bridge.token, 'tool': 'list_tools'})
        names = {t['name'] for t in answer['result']}
        assert answer['ok'] and {'project_state', 'run_checks', 'workflow_state', 'version_kpis', 'search_help'} <= names
        assert not names & {'execute_code', 'exec', 'python', 'sql'}
        # a tool error (no project) is an answer, and the next request is served
        answer = client.ask({'id': 2, 'token': bridge.token, 'tool': 'run_checks'})
        assert answer == {'id': 2, 'ok': False, 'error': 'no project selected in the Districts Modeler'}
        answer = client.ask({'id': 3, 'token': bridge.token, 'tool': 'nothing'})
        assert not answer['ok'] and 'unknown tool' in answer['error']
    finally:
        client.close()


def test_exception_of_a_tool_does_not_stop_the_bridge(bridge, monkeypatch):
    def broken(ctx, args):
        raise ZeroDivisionError('division by zero')
    monkeypatch.setattr(mcp_tools, 'TOOLS', mcp_tools.TOOLS + [{'name': 'broken', 'description': '', 'handler': broken, 'input_schema': {}}])
    client = Client(bridge.start())
    try:
        answer = client.ask({'id': 1, 'token': bridge.token, 'tool': 'broken'})
        assert answer == {'id': 1, 'ok': False, 'error': 'ZeroDivisionError: division by zero'}
        assert client.ask({'id': 2, 'token': bridge.token, 'tool': 'list_tools'})['ok']
    finally:
        client.close()


def test_invalid_json_line(bridge):
    assert bridge.handle(b'{no json') == {'id': None, 'ok': False, 'error': 'invalid JSON'}


def test_every_tool_has_a_description_and_schema():
    for t in mcp_tools.listTools():
        assert t['description'] and t['inputSchema']['type'] == 'object', t['name']
        assert set(t['inputSchema'].get('required', [])) <= set(t['inputSchema']['properties']), t['name']


def test_mcp_configuration_names_existing_files(tmp_path):
    config = mcpConfiguration(state_file=str(tmp_path / 'districts_mcp.json'))['mcpServers']['districts']
    assert os.path.exists(config['command'])
    server = [a for a in config['args'] if a.endswith('server.py')][0]
    assert os.path.exists(server)
    assert config['args'][-2:] == ['--state', str(tmp_path / 'districts_mcp.json')]


def test_menu_actions_off_at_start(iface):
    from districts.districts import Districts
    plugin = Districts(iface)
    plugin.initGui()
    try:
        assert plugin.action_ai.isCheckable() and not plugin.action_ai.isChecked()
        assert plugin.ai_bridge is None
    finally:
        plugin.unload()
        for shortcut in getattr(plugin, 'my_shortcuts', []):
            shortcut.setEnabled(False)
            shortcut.setParent(None)
