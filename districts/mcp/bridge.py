# coding=utf-8
"""Bridge of the AI connection (D1, D2): a QTcpServer on 127.0.0.1 in the QGIS main thread (the tools use the QGIS API,
which is not thread-safe). Requests are newline-delimited JSON {id, token, tool, args}; answers {id, ok, result|error}.
The port and a per-session token are written to districts_mcp.json in the QGIS settings folder while it runs."""
import hmac
import json
import os
import secrets
import traceback

from qgis.core import QgsApplication, QgsMessageLog
from qgis.PyQt.QtCore import QObject
from qgis.PyQt.QtNetwork import QHostAddress, QTcpServer

from ..utility_functions.compat import MessageCritical, MessageWarning
from .tools import ToolContext, ToolError, callTool, jsonValue, listTools

STATE_FILE = 'districts_mcp.json'
MAX_REQUEST_BYTES = 1024 * 1024
LOG_TAG = 'Districts AI'


def stateFilePath():
    return os.path.join(QgsApplication.qgisSettingsDirPath(), STATE_FILE)


class Bridge(QObject):
    def __init__(self, plugin, state_file=None, parent=None):
        super().__init__(parent)
        self.plugin = plugin
        self.state_file = state_file or stateFilePath()
        self.server = None
        self.token = None
        self.buffers = {}
        self.context = ToolContext(plugin)

    def isRunning(self):
        return self.server is not None and self.server.isListening()

    def start(self):
        if self.server is not None and self.server.isListening():
            return self.server.serverPort()
        server = self.server = QTcpServer(self)
        if not server.listen(QHostAddress(QHostAddress.SpecialAddress.LocalHost), 0):
            self.server = None
            raise RuntimeError('the AI connection cannot listen: ' + server.errorString())
        server.newConnection.connect(self.onConnection)
        self.token = secrets.token_hex(16)
        state = {'port': server.serverPort(), 'token': self.token, 'pid': os.getpid(), 'plugin_version': pluginVersion()}
        with open(self.state_file, 'w', encoding='utf-8') as f:
            json.dump(state, f)
        return server.serverPort()

    def stop(self):
        if self.server is not None:
            self.server.close()
            for socket in list(self.buffers):
                socket.abort()
            self.buffers.clear()
            self.server.deleteLater()
            self.server = None
        self.token = None
        try:
            os.remove(self.state_file)
        except FileNotFoundError:
            pass

    def onConnection(self):
        while self.server is not None and self.server.hasPendingConnections():
            socket = self.server.nextPendingConnection()
            self.buffers[socket] = b''
            socket.readyRead.connect(lambda s=socket: self.onReadyRead(s))
            socket.disconnected.connect(lambda s=socket: self.onDisconnected(s))

    def onDisconnected(self, socket):
        self.buffers.pop(socket, None)
        socket.deleteLater()

    def onReadyRead(self, socket):
        if socket not in self.buffers:
            return
        self.buffers[socket] += bytes(socket.readAll())
        if len(self.buffers[socket]) > MAX_REQUEST_BYTES:
            self.send(socket, {'id': None, 'ok': False, 'error': 'request too large'})
            socket.disconnectFromHost()
            return
        while b'\n' in self.buffers.get(socket, b''):
            line, self.buffers[socket] = self.buffers[socket].split(b'\n', 1)
            if line.strip():
                self.send(socket, self.handle(line))

    def send(self, socket, answer):
        socket.write((json.dumps(answer, default=jsonValue) + '\n').encode('utf-8'))
        socket.flush()

    def handle(self, line):
        """answer of one request line (never raises)"""
        try:
            request = json.loads(line.decode('utf-8'))
        except (UnicodeDecodeError, ValueError):
            return {'id': None, 'ok': False, 'error': 'invalid JSON'}
        rid = request.get('id') if isinstance(request, dict) else None
        if not isinstance(request, dict) or not self.token or not hmac.compare_digest(str(request.get('token', '')), self.token):
            QgsMessageLog.logMessage('refused a request with an invalid token', LOG_TAG, MessageWarning)
            return {'id': rid, 'ok': False, 'error': 'invalid token'}
        name = request.get('tool')
        try:
            if name == 'list_tools':
                return {'id': rid, 'ok': True, 'result': listTools()}
            return {'id': rid, 'ok': True, 'result': callTool(self.context, name, request.get('args') or {})}
        except ToolError as e:
            return {'id': rid, 'ok': False, 'error': str(e)}
        except Exception as e:
            QgsMessageLog.logMessage('tool {} failed:\n{}'.format(name, traceback.format_exc()), LOG_TAG, MessageCritical)
            if type(e).__name__ == 'WikiError':
                return {'id': rid, 'ok': False, 'error': str(e)}
            return {'id': rid, 'ok': False, 'error': '{}: {}'.format(type(e).__name__, e)}


def pluginVersion():
    path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'metadata.txt')
    try:
        with open(path, encoding='utf-8') as f:
            for line in f:
                if line.startswith('version='):
                    return line.split('=', 1)[1].strip()
    except OSError:
        pass
    return None


def mcpConfiguration(server_path=None, state_file=None):
    """{'mcpServers': {'districts': {command, args}}} for an MCP client: the QGIS Python runs server.py"""
    from ..simulate_process import pythonCommand
    server_path = server_path or os.path.join(os.path.dirname(os.path.abspath(__file__)), 'server.py')
    command = pythonCommand()
    return {'mcpServers': {'districts': {'command': command[0], 'args': command[1:] + [server_path, '--state', state_file or stateFilePath()]}}}
