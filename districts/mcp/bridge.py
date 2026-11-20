# coding=utf-8
"""Bridge of the AI connection (D1, D2): a QTcpServer on 127.0.0.1 in the QGIS main thread (the tools use the QGIS API,
which is not thread-safe). Requests are newline-delimited JSON {id, token, tool, args}; answers {id, ok, result|error}.
The port and a per-session token are written to districts_mcp.json in the QGIS settings folder while it runs."""
import hmac
import json
import os
import secrets
import shutil
import sys
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


def serverPath():
    return os.path.join(os.path.dirname(os.path.abspath(__file__)), 'server.py')


def mcpPython():
    """the QGIS Python interpreter itself: server.py needs only the standard library, and MCP clients cannot reliably
    start the python-qgis.bat launcher (a .bat needs a shell, and its output would mix into the protocol)"""
    for path in (os.path.join(sys.base_prefix, 'python.exe'), os.path.join(sys.base_prefix, 'bin', 'python3'), sys.executable):
        if os.path.isfile(path) and os.path.basename(path).lower().startswith('python'):
            return path
    from ..simulate_process import pythonCommand
    return pythonCommand()[0]


def mcpConfiguration(server_path=None, state_file=None):
    """{'mcpServers': {'districts': {command, args}}} for Claude Desktop (claude_desktop_config.json)"""
    return {'mcpServers': {'districts': {'command': mcpPython(), 'args': [server_path or serverPath(), '--state', state_file or stateFilePath()]}}}


def claudeCodeCommand(server_path=None, state_file=None, cli=None):
    """the command registering the server in Claude Code for every folder of the user; cli = (path, on_path) of
    claudeCli(): a claude.exe that is installed but not on the PATH is called with its full path (PowerShell)"""
    entry = mcpConfiguration(server_path, state_file)['mcpServers']['districts']
    program = '& "{}"'.format(cli[0]) if cli and not cli[1] else 'claude'
    return '{} mcp add districts --scope user -- "{}" "{}" --state "{}"'.format(program, entry['command'], *[entry['args'][i] for i in (0, 2)])


def claudeCli():
    """(path, on_path) of the claude command (Claude Code CLI), None when it is not installed. The installer puts it
    into ~/.local/bin, which a terminal opened before the installation does not have on its PATH. Claude Desktop runs
    its own copy of Claude Code and has no claude command."""
    found = shutil.which('claude')
    if found:
        return found, True
    path = os.path.join(os.path.expanduser('~'), '.local', 'bin', 'claude.exe' if sys.platform == 'win32' else 'claude')
    return (path, False) if os.path.isfile(path) else None


def writeMcpJson(folder, server_path=None, state_file=None):
    """the entry districts in <folder>/.mcp.json, read by Claude Code in that folder (also the Code tab of Claude Desktop
    and the VS Code extension, which have no claude command); other servers of the file are kept, a file that is not
    valid JSON is not overwritten (ValueError). Returns the path."""
    path = os.path.join(folder, '.mcp.json')
    data = {}
    if os.path.exists(path):
        with open(path, encoding='utf-8') as f:
            text = f.read()
        if text.strip():
            data = json.loads(text)
            if not isinstance(data, dict):
                raise ValueError('{} is not a JSON object'.format(path))
    servers = data.setdefault('mcpServers', {})
    servers['districts'] = mcpConfiguration(server_path, state_file)['mcpServers']['districts']
    with open(path, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2)
        f.write('\n')
    return path


def claudeDesktopConfig():
    """path of Claude Desktop's configuration file (it may not exist yet)"""
    if sys.platform == 'win32':
        return os.path.join(os.environ.get('APPDATA', ''), 'Claude', 'claude_desktop_config.json')
    if sys.platform == 'darwin':
        return os.path.expanduser('~/Library/Application Support/Claude/claude_desktop_config.json')
    return os.path.expanduser('~/.config/Claude/claude_desktop_config.json')
