# coding=utf-8
"""MCP server of the Districts Modeler (OpenSpec change ai-mcp-connection, D4), started by an MCP client:

    python-qgis.bat server.py [--state <QGIS settings folder>/districts_mcp.json]

Standard library only and no qgis import: it runs before QGIS and outlives it. It speaks MCP (JSON-RPC 2.0, one message
per line on stdin/stdout) and forwards tool calls to the bridge of the running QGIS, whose port and token it reads from
the state file at every call, so a restarted QGIS needs no new client configuration."""
import json
import os
import socket
import sys

SERVER_NAME = 'districts-modeler'
SERVER_VERSION = '1.0'
# newest first; a client asking for another version gets the newest
PROTOCOL_VERSIONS = ('2025-11-25', '2025-06-18', '2025-03-26', '2024-11-05')
CALL_TIMEOUT_S = 600
MAP_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'wiki_map.json')
SNAPSHOT_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'tools_snapshot.json')
RESOURCE_PREFIX = 'districts://workflow/'
HINT = 'Start QGIS, open the Districts Modeler and switch on the AI connection (menu Districts Modeler).'


def defaultStateFile():
    # <profile>/python/plugins/districts/mcp/server.py -> <profile>/districts_mcp.json
    here = os.path.dirname(os.path.abspath(__file__))
    return os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(here)))), 'districts_mcp.json')


class BridgeUnavailable(Exception):
    pass


class BridgeClient:
    def __init__(self, state_file):
        self.state_file = state_file
        self.counter = 0

    def call(self, tool, args=None):
        """result of a bridge tool; raises BridgeUnavailable (no QGIS) or RuntimeError (tool error)"""
        try:
            with open(self.state_file, encoding='utf-8') as f:
                state = json.load(f)
        except (OSError, ValueError) as e:
            raise BridgeUnavailable('the AI connection of QGIS is not switched on ({}). {}'.format(type(e).__name__, HINT)) from e
        self.counter += 1
        request = {'id': self.counter, 'token': state.get('token'), 'tool': tool, 'args': args or {}}
        try:
            with socket.create_connection(('127.0.0.1', int(state['port'])), timeout=CALL_TIMEOUT_S) as conn:
                conn.sendall((json.dumps(request) + '\n').encode('utf-8'))
                data = b''
                while not data.endswith(b'\n'):
                    chunk = conn.recv(65536)
                    if not chunk:
                        break
                    data += chunk
        except (OSError, KeyError, ValueError) as e:
            raise BridgeUnavailable('QGIS does not answer ({}). {}'.format(e, HINT)) from e
        try:
            answer = json.loads(data.decode('utf-8'))
        except ValueError as e:
            raise BridgeUnavailable('QGIS closed the connection without an answer. ' + HINT) from e
        if not answer.get('ok'):
            raise RuntimeError(answer.get('error') or 'tool failed')
        return answer.get('result')


def loadMap():
    with open(MAP_FILE, encoding='utf-8') as f:
        return json.load(f)


def toolContent(result):
    """MCP content of a bridge result: a map image becomes image content"""
    if isinstance(result, dict) and 'image_png_base64' in result:
        meta = {k: v for k, v in result.items() if k != 'image_png_base64'}
        return [{'type': 'image', 'data': result['image_png_base64'], 'mimeType': 'image/png'},
                {'type': 'text', 'text': json.dumps(meta)}]
    return [{'type': 'text', 'text': json.dumps(result, ensure_ascii=False)}]


class Server:
    def __init__(self, bridge):
        self.bridge = bridge

    def handle(self, message):
        """response of one JSON-RPC message, None for a notification"""
        if not isinstance(message, dict) or message.get('jsonrpc') != '2.0' or 'method' not in message:
            return error(message.get('id') if isinstance(message, dict) else None, -32600, 'invalid request')
        mid, method, params = message.get('id'), message['method'], message.get('params') or {}
        if 'id' not in message:
            return None  # notifications/initialized, notifications/cancelled, ...
        try:
            if method == 'initialize':
                return result(mid, self.initialize(params))
            if method == 'ping':
                return result(mid, {})
            if method == 'tools/list':
                return result(mid, self.toolsList())
            if method == 'tools/call':
                return result(mid, self.toolsCall(params))
            if method == 'resources/list':
                return result(mid, self.resourcesList())
            if method == 'resources/read':
                return result(mid, self.resourcesRead(params))
            if method == 'resources/templates/list':
                return result(mid, {'resourceTemplates': []})
            if method == 'prompts/list':
                return result(mid, {'prompts': []})
            return error(mid, -32601, 'method not found: ' + method)
        except InvalidParams as e:
            return error(mid, -32602, str(e))
        except Exception as e:  # the server keeps running
            return error(mid, -32603, '{}: {}'.format(type(e).__name__, e))

    def initialize(self, params):
        asked = params.get('protocolVersion')
        version = asked if asked in PROTOCOL_VERSIONS else PROTOCOL_VERSIONS[0]
        return {'protocolVersion': version, 'capabilities': {'tools': {}, 'resources': {}},
                'serverInfo': {'name': SERVER_NAME, 'version': SERVER_VERSION},
                'instructions': 'Tools of the Districts Modeler (QGIS plugin for district energy systems). They only read: state, '
                                'model checks (run_checks), key figures (version_kpis, compare_versions), workflow_state and the '
                                'IDA Districts wiki (search_help, read_help_page). ' + HINT}

    def toolsList(self):
        try:
            tools = self.bridge.call('list_tools')
        except BridgeUnavailable:
            # clients list the tools once at their start, often before QGIS runs: the snapshot of the registry
            # (test_mcp_server.py keeps it equal to tools.py); a call then explains how to switch QGIS on
            with open(SNAPSHOT_FILE, encoding='utf-8') as f:
                tools = json.load(f)
        return {'tools': tools}

    def toolsCall(self, params):
        name = params.get('name')
        if not isinstance(name, str):
            raise InvalidParams('tools/call needs a name')
        try:
            return {'content': toolContent(self.bridge.call(name, params.get('arguments') or {})), 'isError': False}
        except (BridgeUnavailable, RuntimeError) as e:
            return {'content': [{'type': 'text', 'text': str(e)}], 'isError': True}

    def resourcesList(self):
        return {'resources': [{'uri': RESOURCE_PREFIX + s['step'], 'name': s['step'], 'title': s['title'], 'mimeType': 'application/json',
                               'description': 'Workflow step {}: wiki pages and check rules'.format(s['title'])} for s in loadMap()['steps']]}

    def resourcesRead(self, params):
        uri = params.get('uri') or ''
        step = next((s for s in loadMap()['steps'] if RESOURCE_PREFIX + s['step'] == uri), None)
        if step is None:
            raise InvalidParams('unknown resource ' + uri)
        return {'contents': [{'uri': uri, 'mimeType': 'application/json', 'text': json.dumps(step)}]}


class InvalidParams(Exception):
    pass


def result(mid, value):
    return {'jsonrpc': '2.0', 'id': mid, 'result': value}


def error(mid, code, text):
    return {'jsonrpc': '2.0', 'id': mid, 'error': {'code': code, 'message': text}}


def stateFileFromArgs(argv):
    if '--state' in argv:
        return argv[argv.index('--state') + 1]
    return os.environ.get('DISTRICTS_MCP_STATE') or defaultStateFile()


def serve(stdin, stdout, server):
    for line in stdin:
        line = line.strip()
        if not line:
            continue
        try:
            message = json.loads(line)
        except ValueError:
            responses = [error(None, -32700, 'parse error')]
        else:
            batch = message if isinstance(message, list) else [message]
            responses = [r for r in (server.handle(m) for m in batch) if r is not None]
        for response in responses:
            stdout.write(json.dumps(response, ensure_ascii=False) + '\n')
        stdout.flush()


def main(argv=None):
    argv = sys.argv[1:] if argv is None else argv
    # stdout carries only protocol messages
    stdin = open(sys.stdin.fileno(), encoding='utf-8', closefd=False)
    stdout = open(sys.stdout.fileno(), 'w', encoding='utf-8', newline='\n', closefd=False)
    serve(stdin, stdout, Server(BridgeClient(stateFileFromArgs(argv))))


if __name__ == '__main__':
    main()
