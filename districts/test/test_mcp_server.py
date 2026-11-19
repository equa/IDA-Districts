# coding=utf-8
"""MCP server of the AI connection (OpenSpec change ai-mcp-connection, spec ai-bridge): JSON-RPC over stdio without
QGIS, forwarding to a bridge (here a plain socket fake), the tool snapshot.

    python -m pytest test/test_mcp_server.py -v
"""
import io
import json
import os
import socket
import subprocess  # nosec B404
import sys
import threading

import pytest

from districts.mcp import server as mcp_server

SERVER = mcp_server.__file__


def run(messages, bridge):
    out = io.StringIO()
    mcp_server.serve(io.StringIO(''.join(json.dumps(m) + '\n' for m in messages)), out, mcp_server.Server(bridge))
    return [json.loads(line) for line in out.getvalue().splitlines()]


def init(mid=1, version='2025-06-18'):
    return {'jsonrpc': '2.0', 'id': mid, 'method': 'initialize',
            'params': {'protocolVersion': version, 'capabilities': {}, 'clientInfo': {'name': 'test', 'version': '1'}}}


def call(mid, name, arguments=None):
    return {'jsonrpc': '2.0', 'id': mid, 'method': 'tools/call', 'params': {'name': name, 'arguments': arguments or {}}}


class FakeBridgeServer:
    """a socket server answering like the bridge, with the state file of a running QGIS"""

    def __init__(self, tmp_path, answers):
        self.answers = answers
        self.requests = []
        self.sock = socket.socket()
        self.sock.bind(('127.0.0.1', 0))
        self.sock.listen()
        self.state = tmp_path / 'districts_mcp.json'
        self.state.write_text(json.dumps({'port': self.sock.getsockname()[1], 'token': 'secret'}), encoding='utf-8')
        self.thread = threading.Thread(target=self.serve, daemon=True)
        self.thread.start()

    def serve(self):
        while True:
            try:
                conn, _ = self.sock.accept()
            except OSError:
                return
            with conn:
                data = b''
                while not data.endswith(b'\n'):
                    data += conn.recv(65536)
                request = json.loads(data)
                self.requests.append(request)
                answer = self.answers(request)
                conn.sendall((json.dumps(dict(answer, id=request['id'])) + '\n').encode('utf-8'))

    def close(self):
        self.sock.close()


def test_initialize_negotiates_the_version():
    responses = run([init(1, '2025-06-18'), init(2, '1999-01-01')], mcp_server.BridgeClient('missing.json'))
    assert responses[0]['result']['protocolVersion'] == '2025-06-18'
    assert responses[0]['result']['serverInfo']['name'] == 'districts-modeler'
    assert set(responses[0]['result']['capabilities']) == {'tools', 'resources'}
    assert responses[1]['result']['protocolVersion'] == mcp_server.PROTOCOL_VERSIONS[0]


def test_qgis_not_running_gives_a_hint_and_the_server_keeps_running(tmp_path):
    bridge = mcp_server.BridgeClient(str(tmp_path / 'districts_mcp.json'))
    responses = run([init(), {'jsonrpc': '2.0', 'method': 'notifications/initialized'}, call(2, 'run_checks'),
                     {'jsonrpc': '2.0', 'id': 3, 'method': 'ping'}], bridge)
    assert [r['id'] for r in responses] == [1, 2, 3]  # no answer to the notification
    result = responses[1]['result']
    assert result['isError'] and 'switch on the AI connection' in result['content'][0]['text']
    assert responses[2]['result'] == {}


def test_tool_list_without_qgis_is_the_snapshot_of_the_registry(tmp_path):
    from districts.mcp.tools import listTools
    responses = run([{'jsonrpc': '2.0', 'id': 1, 'method': 'tools/list'}], mcp_server.BridgeClient(str(tmp_path / 'missing.json')))
    assert responses[0]['result']['tools'] == listTools(), 'regenerate mcp/tools_snapshot.json (see test_snapshot_file)'


def test_snapshot_file():
    from districts.mcp.tools import listTools
    with open(mcp_server.SNAPSHOT_FILE, encoding='utf-8') as f:
        assert json.load(f) == listTools(), 'tools_snapshot.json differs from the registry: write json.dumps(listTools(), indent=1) to it'


def test_tool_call_through_the_bridge(tmp_path):
    def answers(request):
        if request['tool'] == 'render_map':
            return {'ok': True, 'result': {'image_png_base64': 'iVBORw0KGgo=', 'width': 10, 'height': 5}}
        if request['tool'] == 'broken':
            return {'ok': False, 'error': 'no version loaded'}
        return {'ok': True, 'result': {'tool': request['tool'], 'args': request['args']}}

    fake = FakeBridgeServer(tmp_path, answers)
    try:
        responses = run([call(1, 'project_state', {'version': 'base1'}), call(2, 'render_map'), call(3, 'broken')],
                        mcp_server.BridgeClient(str(fake.state)))
    finally:
        fake.close()
    assert json.loads(responses[0]['result']['content'][0]['text']) == {'tool': 'project_state', 'args': {'version': 'base1'}}
    assert fake.requests[0]['token'] == 'secret'
    image = responses[1]['result']['content'][0]
    assert image == {'type': 'image', 'data': 'iVBORw0KGgo=', 'mimeType': 'image/png'}
    assert responses[2]['result']['isError'] and responses[2]['result']['content'][0]['text'] == 'no version loaded'


def test_qgis_restart_is_found_without_new_configuration(tmp_path):
    first = FakeBridgeServer(tmp_path, lambda r: {'ok': True, 'result': 'first'})
    bridge = mcp_server.BridgeClient(str(first.state))
    assert bridge.call('project_state') == 'first'
    first.close()
    second = FakeBridgeServer(tmp_path, lambda r: {'ok': True, 'result': 'second'})  # new port and token, same file
    try:
        assert bridge.call('project_state') == 'second'
    finally:
        second.close()


def test_resources_are_the_workflow_steps():
    responses = run([{'jsonrpc': '2.0', 'id': 1, 'method': 'resources/list'},
                     {'jsonrpc': '2.0', 'id': 2, 'method': 'resources/read', 'params': {'uri': 'districts://workflow/topology'}},
                     {'jsonrpc': '2.0', 'id': 3, 'method': 'resources/read', 'params': {'uri': 'districts://workflow/nothing'}}],
                    mcp_server.BridgeClient('missing.json'))
    uris = [r['uri'] for r in responses[0]['result']['resources']]
    assert 'districts://workflow/topology' in uris
    step = json.loads(responses[1]['result']['contents'][0]['text'])
    assert step['step'] == 'topology' and 'topology' in step['rules']
    assert responses[2]['error']['code'] == -32602


def test_protocol_errors():
    out = io.StringIO()
    mcp_server.serve(io.StringIO('not json\n{"jsonrpc": "2.0", "id": 1, "method": "nothing"}\n'), out,
                     mcp_server.Server(mcp_server.BridgeClient('missing.json')))
    lines = [json.loads(line) for line in out.getvalue().splitlines()]
    assert lines[0]['error']['code'] == -32700 and lines[1]['error']['code'] == -32601


def test_server_imports_only_the_standard_library():
    with open(SERVER, encoding='utf-8') as f:
        source = f.read()
    assert 'qgis' not in [line.split()[1].split('.')[0] for line in source.splitlines() if line.startswith(('import ', 'from '))]


def test_stdio_of_the_real_process(tmp_path):
    messages = [init(), call(2, 'project_state')]
    proc = subprocess.run([sys.executable, SERVER, '--state', str(tmp_path / 'none.json')],  # nosec B603
                          input=''.join(json.dumps(m) + '\n' for m in messages), capture_output=True, text=True, timeout=60,
                          env=dict(os.environ, PYTHONIOENCODING='utf-8'))
    lines = [json.loads(line) for line in proc.stdout.splitlines()]
    assert [r['id'] for r in lines] == [1, 2] and lines[1]['result']['isError']


@pytest.mark.parametrize('argv, expected', [(['--state', 'x.json'], 'x.json')])
def test_state_file_argument(argv, expected):
    assert mcp_server.stateFileFromArgs(argv) == expected
