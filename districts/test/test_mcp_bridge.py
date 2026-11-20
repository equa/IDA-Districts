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
    # the interpreter itself, not the python-qgis.bat launcher (MCP clients cannot reliably start a .bat)
    assert os.path.isfile(config['command']) and os.path.basename(config['command']).lower().startswith('python')
    assert not config['command'].lower().endswith('.bat')
    assert os.path.exists(config['args'][0]) and config['args'][0].endswith('server.py')
    assert config['args'][1:] == ['--state', str(tmp_path / 'districts_mcp.json')]


def test_configured_command_starts_the_server(tmp_path):
    import subprocess  # nosec B404
    config = mcpConfiguration(state_file=str(tmp_path / 'none.json'))['mcpServers']['districts']
    request = json.dumps({'jsonrpc': '2.0', 'id': 1, 'method': 'initialize', 'params': {'protocolVersion': '2025-06-18'}}) + '\n'
    proc = subprocess.run([config['command']] + config['args'], input=request, capture_output=True, text=True, timeout=60)  # nosec B603
    assert json.loads(proc.stdout.splitlines()[0])['result']['serverInfo']['name'] == 'districts-modeler'


def test_claude_code_command_with_the_paths_of_this_computer(tmp_path):
    from districts.mcp.bridge import claudeCodeCommand
    state = str(tmp_path / 'districts_mcp.json')
    entry = mcpConfiguration(state_file=state)['mcpServers']['districts']
    assert claudeCodeCommand(state_file=state) == 'claude mcp add districts --scope user -- "{}" "{}" --state "{}"'.format(
        entry['command'], entry['args'][0], state)


CLI = r'C:\Users\x\.local\bin\claude.exe'


@pytest.mark.parametrize('cli', [None, (CLI, True), (CLI, False)])
def test_configuration_dialog_says_whether_claude_is_found(monkeypatch, cli):
    from districts.mcp import config_dialog
    monkeypatch.setattr(config_dialog, 'claudeCli', lambda: cli)
    dlg = config_dialog.McpConfigDialog()
    try:
        command = dlg.edit_code.toPlainText()
        assert json.loads(dlg.edit_desktop.toPlainText())['mcpServers']['districts']['args'][0].endswith('server.py')
        if cli is None:
            assert command.startswith('claude mcp add districts --scope user -- ')
            assert config_dialog.CLAUDE_CODE_INSTALL in dlg.label_cli.text() and 'Code tab' in dlg.label_cli.text()
        elif cli[1]:
            assert command.startswith('claude mcp add') and CLI in dlg.label_cli.text()
        else:
            # installed but not on the PATH of the terminal: the command calls it with its full path
            assert command.startswith('& "{}" mcp add districts --scope user -- '.format(CLI)) and CLI in dlg.label_cli.text()
    finally:
        dlg.close()


def test_claude_found_off_the_path(monkeypatch, tmp_path):
    from districts.mcp import bridge
    monkeypatch.setattr(bridge.shutil, 'which', lambda name: None)
    real = bridge.os.path.expanduser
    monkeypatch.setattr(bridge.os.path, 'expanduser', lambda p: str(tmp_path) if p == '~' else real(p))
    assert bridge.claudeCli() is None
    exe = tmp_path / '.local' / 'bin' / ('claude.exe' if bridge.sys.platform == 'win32' else 'claude')
    exe.parent.mkdir(parents=True)
    exe.write_bytes(b'')
    assert bridge.claudeCli() == (str(exe), False)


def test_write_mcp_json_keeps_other_servers(tmp_path):
    from districts.mcp.bridge import writeMcpJson
    path = tmp_path / '.mcp.json'
    path.write_text(json.dumps({'mcpServers': {'other': {'command': 'x'}}, 'note': 1}), encoding='utf-8')
    assert writeMcpJson(str(tmp_path), state_file='s.json') == str(path)
    data = json.loads(path.read_text(encoding='utf-8'))
    assert data['mcpServers']['other'] == {'command': 'x'} and data['note'] == 1
    assert data['mcpServers']['districts']['args'][1:] == ['--state', 's.json']
    writeMcpJson(str(tmp_path), state_file='t.json')  # replaced, not added twice
    assert json.loads(path.read_text(encoding='utf-8'))['mcpServers']['districts']['args'][-1] == 't.json'


def test_write_mcp_json_new_and_invalid(tmp_path, monkeypatch):
    from districts.mcp import config_dialog
    from districts.mcp.bridge import writeMcpJson
    with open(writeMcpJson(str(tmp_path)), encoding='utf-8') as f:
        assert set(json.load(f)['mcpServers']) == {'districts'}
    broken = tmp_path / 'b'
    broken.mkdir()
    (broken / '.mcp.json').write_text('{not json', encoding='utf-8')
    with pytest.raises(ValueError):
        writeMcpJson(str(broken))
    assert (broken / '.mcp.json').read_text(encoding='utf-8') == '{not json'
    # the dialog reports it instead of raising
    shown = []
    monkeypatch.setattr(config_dialog.QMessageBox, 'warning', lambda *a: shown.append(a[2]))
    dlg = config_dialog.McpConfigDialog()
    try:
        assert dlg.writeTo(str(broken)) is None and shown and 'not written' in shown[0]
    finally:
        dlg.close()


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
