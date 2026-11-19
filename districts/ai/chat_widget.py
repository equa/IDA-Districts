# coding=utf-8
"""Tab 'AI assistant' of the main dialog (OpenSpec change ai-chat-panel, D4, D5): the conversation runs in a worker
thread; every tool call is handed to the main thread (QGIS API and layers), and the worker waits for its result."""
import html
import json
import threading
import traceback

from qgis.core import QgsMessageLog
from qgis.PyQt.QtCore import QProcess, QSettings, QThread, pyqtSignal
from qgis.PyQt.QtWidgets import (
    QCheckBox, QComboBox, QDialog, QDialogButtonBox, QFileDialog, QHBoxLayout, QLabel, QListWidget, QListWidgetItem,
    QMessageBox, QPlainTextEdit, QPushButton, QTextBrowser, QVBoxLayout, QWidget,
)
from qgis.PyQt.QtCore import Qt

from ..utility_functions.compat import MessageCritical
from ..utility_functions.translations import tr_msg
from . import access
from .conversation import DEFAULT_EFFORT, EFFORTS, NO_KEY_TEXT, Callbacks, Conversation, errorText
from .costs import DEFAULT_LIMIT_USD, DEFAULT_MODEL, MODELS, PRICES_DATE, SessionCosts

SETTINGS_GROUP = 'districts/ai'
MODEL_LABELS = {'claude-opus-5-5': 'Claude Opus 5.5', 'claude-sonnet-5-5': 'Claude Sonnet 5.5', 'claude-haiku-5-5': 'Claude Haiku 5.5'}
TOOL_DATA = {
    'project_state': 'project and version names, feature counts, template names',
    'layers': 'names and fields of the QGIS layers',
    'features': 'attribute values and geometries of the chosen features',
    'render_map': 'an image of the visible map (base map, streets, network)',
    'result_tables': 'names and sizes of the result tables',
    'result_series': 'simulation results of chosen features',
    'run_log': 'errors and the end of the IDA run log',
    'template_components': 'component names and variables of the IDA templates',
    'run_checks': 'findings with feature ids and measured values',
    'workflow_state': 'which workflow steps are done',
    'version_kpis': 'key figures: heat, losses, pump energy, costs, NPV',
    'compare_versions': 'key figures of two versions',
}


class Worker(QThread):
    """one question; the signals cross to the main thread, the worker waits on an event for tool results and answers"""
    text = pyqtSignal(str)
    toolDone = pyqtSignal(object)
    note = pyqtSignal(str)
    cost = pyqtSignal(object)
    toolRequest = pyqtSignal(str, object)
    askContinue = pyqtSignal(object)
    failed = pyqtSignal(str)

    def __init__(self, conversation, question, context, tools, key_source):
        super().__init__()
        self.conversation, self.question, self.context, self.tools, self.key_source = conversation, question, context, tools, key_source
        self.stop_requested = False
        self.event = threading.Event()
        self.reply = None

    def wait_for_main(self):
        self.event.wait()
        self.event.clear()
        return self.reply

    def answer(self, reply):
        self.reply = reply
        self.event.set()

    def run(self):
        worker = self

        class Hooks(Callbacks):
            def text(self, delta):
                worker.text.emit(delta)

            def tool(self, entry):
                worker.toolDone.emit(entry)

            def note(self, text):
                worker.note.emit(text)

            def cost(self, costs):
                worker.cost.emit(costs)

            def confirmContinue(self, costs):
                worker.askContinue.emit(costs)
                return bool(worker.wait_for_main())

            def stopped(self):
                return worker.stop_requested

        def run_tool(name, args):
            worker.toolRequest.emit(name, args)
            return worker.wait_for_main()

        try:
            self.conversation.ask(self.question, self.context, self.tools, run_tool, Hooks())
        except Exception as e:
            QgsMessageLog.logMessage(traceback.format_exc(), 'Districts AI', MessageCritical)
            self.failed.emit(errorText(e, self.key_source))


class PermissionDialog(QDialog):
    """allowing the assistant in a project names what is sent to Anthropic; tools can be switched off"""

    def __init__(self, settings, project, parent=None):
        super().__init__(parent)
        from ..mcp.tools import listTools
        self.setWindowTitle(tr_msg('AI assistant in project {}').format(project))
        layout = QVBoxLayout(self)
        text = QLabel(tr_msg('When the AI assistant is allowed, everything a tool returns is sent to Anthropic (Claude API) as part '
                             'of the conversation: only what the tool returns, never the database credentials. Allowing it decides '
                             'for everyone working on this project. Check whether your contracts and data protection rules allow it.'))
        text.setWordWrap(True)
        layout.addWidget(text)
        self.check_allowed = QCheckBox(tr_msg('Allow the AI assistant in this project'))
        self.check_allowed.setChecked(settings['allowed'])
        layout.addWidget(self.check_allowed)
        layout.addWidget(QLabel(tr_msg('Tools and the data they send (uncheck to switch a tool off):')))
        self.list_tools = QListWidget()
        for tool in listTools():
            if tool['name'] in access.ALWAYS_ALLOWED:
                continue
            item = QListWidgetItem('{} – {}'.format(tool['name'], TOOL_DATA.get(tool['name'], '')))
            item.setData(Qt.ItemDataRole.UserRole, tool['name'])
            item.setFlags(item.flags() | Qt.ItemFlag.ItemIsUserCheckable)
            item.setCheckState(Qt.CheckState.Unchecked if tool['name'] in settings['disabled_tools'] else Qt.CheckState.Checked)
            self.list_tools.addItem(item)
        layout.addWidget(self.list_tools)
        buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

    def disabledTools(self):
        return [self.list_tools.item(k).data(Qt.ItemDataRole.UserRole) for k in range(self.list_tools.count())
                if self.list_tools.item(k).checkState() != Qt.CheckState.Checked]


class AiAssistantTab(QWidget):
    def __init__(self, plugin, backend_factory=None, parent=None):
        """backend_factory(config) -> backend with step(params, on_text); default: the anthropic SDK (tests pass a fake)"""
        super().__init__(parent)
        self.plugin = plugin
        self.backend_factory = backend_factory
        self.worker = None
        self.process = None
        self.expanded = set()
        self.streaming = ''
        settings = QSettings()
        settings.beginGroup(SETTINGS_GROUP)
        model = settings.value('model', DEFAULT_MODEL)
        effort = settings.value('effort', DEFAULT_EFFORT)
        self.limit = float(settings.value('limit_usd', DEFAULT_LIMIT_USD))
        settings.endGroup()
        self.conversation = Conversation(None, model if model in MODELS else DEFAULT_MODEL, effort if effort in EFFORTS else DEFAULT_EFFORT,
                                         SessionCosts(self.limit))

        layout = QVBoxLayout(self)
        self.label_status = QLabel()
        self.label_status.setWordWrap(True)
        layout.addWidget(self.label_status)
        row = QHBoxLayout()
        self.combo_model = QComboBox()
        for m in MODELS:
            self.combo_model.addItem(MODEL_LABELS[m], m)
        self.combo_model.setCurrentIndex(MODELS.index(self.conversation.model))
        self.combo_effort = QComboBox()
        for e in EFFORTS:
            self.combo_effort.addItem(e, e)
        self.combo_effort.setCurrentIndex(EFFORTS.index(self.conversation.effort))
        self.btn_permission = QPushButton(tr_msg('Permission ...'))
        for widget in (QLabel(tr_msg('Model')), self.combo_model, QLabel(tr_msg('Effort')), self.combo_effort):
            row.addWidget(widget)
        row.addStretch()
        row.addWidget(self.btn_permission)
        layout.addLayout(row)

        # without the SDK: install
        self.install_box = QWidget()
        install = QVBoxLayout(self.install_box)
        self.label_install = QLabel(tr_msg('The AI assistant needs the Python package anthropic. Install it with:') + '\n' + access.installCommandText())
        self.label_install.setWordWrap(True)
        self.btn_install = QPushButton(tr_msg('Install AI support'))
        self.text_install = QPlainTextEdit()
        self.text_install.setReadOnly(True)
        self.text_install.setVisible(False)
        for widget in (self.label_install, self.btn_install, self.text_install):
            install.addWidget(widget)
        layout.addWidget(self.install_box)

        self.view = QTextBrowser()
        self.view.setOpenLinks(False)
        layout.addWidget(self.view, 1)
        self.input = QPlainTextEdit()
        self.input.setPlaceholderText(tr_msg('Ask about the loaded project, e.g. "Check the loaded version" (Ctrl+Enter sends)'))
        self.input.setMaximumHeight(90)
        layout.addWidget(self.input)
        buttons = QHBoxLayout()
        self.btn_send, self.btn_stop = QPushButton(tr_msg('Send')), QPushButton(tr_msg('Stop'))
        self.btn_new, self.btn_export = QPushButton(tr_msg('New conversation')), QPushButton(tr_msg('Export ...'))
        self.label_cost = QLabel()
        for widget in (self.btn_send, self.btn_stop, self.btn_new, self.btn_export):
            buttons.addWidget(widget)
        buttons.addStretch()
        buttons.addWidget(self.label_cost)
        layout.addLayout(buttons)

        self.btn_send.clicked.connect(self.send)
        self.btn_stop.clicked.connect(self.stop)
        self.btn_new.clicked.connect(self.newConversation)
        self.btn_export.clicked.connect(self.export)
        self.btn_install.clicked.connect(self.install)
        self.btn_permission.clicked.connect(self.editPermission)
        self.combo_model.currentIndexChanged.connect(self.modelChanged)
        self.combo_effort.currentIndexChanged.connect(self.effortChanged)
        self.view.anchorClicked.connect(self.toggleTool)
        self.input.installEventFilter(self)
        self.refresh()

    def showEvent(self, event):
        # project, version, key or permission may have changed while the tab was hidden
        self.refresh()
        super().showEvent(event)

    # ---------------- state ----------------
    def sdkReady(self):
        return self.backend_factory is not None or access.sdkVersion() is not None

    def projectSettings(self):
        from ..mcp.tools import ToolContext
        if not self.plugin.config.get('projectName'):
            return None
        try:
            return ToolContext(self.plugin).aiSettings()
        except Exception:
            QgsMessageLog.logMessage(traceback.format_exc(), 'Districts AI', MessageCritical)
            return None

    def refresh(self):
        """status line and enabled buttons"""
        ready = self.sdkReady()
        self.install_box.setVisible(not ready)
        settings = self.projectSettings()
        source, _ = access.keySource(self.plugin.config)
        parts = [tr_msg('SDK {}').format(access.sdkVersion() or ('test' if self.backend_factory else tr_msg('not installed'))),
                 tr_msg('key: {}').format({'settings': tr_msg('QGIS settings'), 'environment': tr_msg('environment'),
                                           'profile': tr_msg('ant login profile')}.get(source, tr_msg('none')))]
        if settings is None:
            parts.append(tr_msg('no project'))
        elif not settings['allowed']:
            parts.append(tr_msg('AI assistant not allowed in this project'))
        else:
            parts.append(tr_msg('allowed in this project') + (tr_msg(', switched off: {}').format(', '.join(settings['disabled_tools']))
                                                              if settings['disabled_tools'] else ''))
        self.label_status.setText(' · '.join(parts))
        busy = self.worker is not None
        allowed = bool(settings and settings['allowed'])
        self.btn_send.setEnabled(ready and allowed and not busy)
        self.btn_stop.setEnabled(busy)
        self.btn_new.setEnabled(not busy)
        self.btn_export.setEnabled(not busy and bool(self.conversation.transcript))
        self.btn_permission.setEnabled(settings is not None and not busy)
        self.combo_model.setEnabled(not busy)
        self.combo_effort.setEnabled(not busy)
        self.showCost()

    def showCost(self):
        costs = self.conversation.costs
        self.label_cost.setText(tr_msg('this answer {:.2f} USD · session {:.2f} of {:.2f} USD (estimated, prices of {})').format(
            costs.answer, costs.total, costs.limit, PRICES_DATE))

    def eventFilter(self, obj, event):
        from qgis.PyQt.QtCore import QEvent
        if obj is self.input and event.type() == QEvent.Type.KeyPress and event.key() in (Qt.Key.Key_Return, Qt.Key.Key_Enter) \
                and event.modifiers() & Qt.KeyboardModifier.ControlModifier:
            self.send()
            return True
        return super().eventFilter(obj, event)

    # ---------------- conversation ----------------
    def context(self):
        config = self.plugin.config
        if config.get('versionName'):
            return 'Loaded in the Districts Modeler: project {}, version {}.'.format(config['projectName'], config['versionName'])
        return 'Loaded in the Districts Modeler: project {}, no version loaded.'.format(config.get('projectName') or '(none)')

    def send(self):
        from ..mcp.tools import ToolContext, allowedTools
        question = self.input.toPlainText().strip()
        if not question or self.worker is not None or not self.btn_send.isEnabled():
            return
        source, _ = access.keySource(self.plugin.config)
        if self.backend_factory is None and source is None:
            self.addNote(tr_msg(NO_KEY_TEXT))
            return
        try:
            tools = allowedTools(ToolContext(self.plugin))
            if self.backend_factory is not None:
                backend = self.backend_factory(self.plugin.config)
            else:
                from .conversation import AnthropicBackend
                backend = AnthropicBackend(access.createClient(self.plugin.config))
        except Exception as e:
            QgsMessageLog.logMessage(traceback.format_exc(), 'Districts AI', MessageCritical)
            self.addNote(errorText(e, source))
            return
        self.conversation.backend = backend
        self.input.clear()
        self.streaming = ''
        self.worker = Worker(self.conversation, question, self.context(), tools, source)
        self.worker.text.connect(self.onText)
        self.worker.toolDone.connect(lambda entry: self.render())
        self.worker.note.connect(lambda text: self.render())
        self.worker.cost.connect(lambda costs: self.showCost())
        self.worker.toolRequest.connect(self.onToolRequest)
        self.worker.askContinue.connect(self.onAskContinue)
        self.worker.failed.connect(self.addNote)
        self.worker.finished.connect(self.onFinished)
        self.render()
        self.worker.start()
        self.refresh()

    def onText(self, delta):
        self.streaming += delta
        self.render()

    def onToolRequest(self, name, args):
        """main thread: the tool with the plugin's tool context (rolled-back transaction, project permission)"""
        from ..mcp.tools import ToolContext, ToolError, callTool
        self.streaming = ''
        try:
            reply = (callTool(ToolContext(self.plugin), name, args or {}), False)
        except ToolError as e:
            reply = (str(e), True)
        except Exception as e:
            QgsMessageLog.logMessage(traceback.format_exc(), 'Districts AI', MessageCritical)
            reply = ('{}: {}'.format(type(e).__name__, e) if type(e).__name__ != 'WikiError' else str(e), True)
        if self.worker is not None:
            self.worker.answer(reply)

    def onAskContinue(self, costs):
        button = QMessageBox.question(self, tr_msg('AI assistant'), tr_msg(
            'The estimated cost of this session reached {:.2f} USD (limit {:.2f} USD). Continue, which raises the limit by {:.2f} USD?').format(
            costs.total, costs.limit, costs.step), QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
        if self.worker is not None:
            self.worker.answer(button == QMessageBox.StandardButton.Yes)

    def onFinished(self):
        self.worker = None
        self.streaming = ''
        self.render()
        self.refresh()

    def stop(self):
        if self.worker is not None:
            self.worker.stop_requested = True

    def addNote(self, text):
        self.conversation.transcript.append({'role': 'note', 'text': text})
        self.render()

    def newConversation(self):
        if self.worker is not None:
            return
        self.conversation = Conversation(None, self.combo_model.currentData(), self.combo_effort.currentData(), SessionCosts(self.limit))
        self.expanded.clear()
        self.render()
        self.refresh()

    def modelChanged(self):
        model = self.combo_model.currentData()
        if model == self.conversation.model:
            return
        if self.conversation.transcript:
            button = QMessageBox.question(self, tr_msg('AI assistant'), tr_msg(
                'Another model cannot continue this conversation. Start a new conversation with {}?').format(MODEL_LABELS[model]),
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
            if button != QMessageBox.StandardButton.Yes:
                self.combo_model.blockSignals(True)
                self.combo_model.setCurrentIndex(MODELS.index(self.conversation.model))
                self.combo_model.blockSignals(False)
                return
        self.saveChoice('model', model)
        self.newConversation()

    def effortChanged(self):
        self.conversation.effort = self.combo_effort.currentData()
        self.saveChoice('effort', self.conversation.effort)

    def saveChoice(self, key, value):
        settings = QSettings()
        settings.setValue('{}/{}'.format(SETTINGS_GROUP, key), value)

    # ---------------- view ----------------
    def render(self):
        parts = []
        for k, entry in enumerate(self.conversation.transcript):
            role = entry['role']
            if role == 'user':
                parts.append('<p style="background:#eef3fb;padding:4px"><b>{}</b><br>{}</p>'.format(
                    tr_msg('You'), html.escape(entry['text']).replace('\n', '<br>')))
            elif role == 'assistant':
                parts.append('<p>{}</p>'.format(html.escape(entry['text']).replace('\n', '<br>')))
            elif role == 'tool':
                mark = '▾' if k in self.expanded else '▸'
                color = '#b00' if entry.get('is_error') else '#555'
                parts.append('<p style="color:{}"><a href="tool:{}">{} {}</a> {}</p>'.format(
                    color, k, mark, html.escape(entry['name']), html.escape(json.dumps(entry.get('input') or {}, ensure_ascii=False))))
                if k in self.expanded:
                    result = entry.get('result')
                    shown = '[map image]' if isinstance(result, dict) and 'image_png_base64' in result else \
                        json.dumps(result, ensure_ascii=False, indent=1, default=str)
                    parts.append('<pre style="color:#555">{}</pre>'.format(html.escape(shown[:20000])))
            else:
                parts.append('<p style="color:#777"><i>{}</i></p>'.format(html.escape(entry['text'])))
        if self.streaming:
            parts.append('<p>{}</p>'.format(html.escape(self.streaming).replace('\n', '<br>')))
        if self.worker is not None and not self.streaming:
            parts.append('<p style="color:#777"><i>{}</i></p>'.format(tr_msg('working ...')))
        self.view.setHtml(''.join(parts))
        self.view.verticalScrollBar().setValue(self.view.verticalScrollBar().maximum())

    def toggleTool(self, url):
        text = url.toString()
        if text.startswith('tool:'):
            k = int(text[5:])
            self.expanded.symmetric_difference_update({k})
            self.render()

    # ---------------- permission, install, export ----------------
    def editPermission(self):
        settings = self.projectSettings()
        if settings is None or self.plugin.cur is None:
            return
        dlg = PermissionDialog(settings, self.plugin.config['projectName'], self)
        if dlg.exec():
            access.saveAiSettings(self.plugin.cur, dlg.check_allowed.isChecked(), dlg.disabledTools())
            self.refresh()

    def install(self):
        self.text_install.setVisible(True)
        self.text_install.setPlainText(access.installCommandText() + '\n')
        self.btn_install.setEnabled(False)
        self.process = QProcess(self)
        self.process.setProcessChannelMode(QProcess.ProcessChannelMode.MergedChannels)
        self.process.readyReadStandardOutput.connect(
            lambda: self.text_install.appendPlainText(bytes(self.process.readAllStandardOutput()).decode('utf-8', 'replace').rstrip()))
        self.process.finished.connect(self.installFinished)
        self.process.start(access.pythonExecutable(), access.installArguments())

    def installFinished(self, code, status=None):
        access.refreshImportPath()
        self.btn_install.setEnabled(True)
        if code == 0 and access.sdkVersion():
            self.text_install.appendPlainText(tr_msg('Installed.'))
        elif code == 0:
            self.text_install.appendPlainText(tr_msg('Installed; restart QGIS to use the AI assistant.'))
        else:
            self.text_install.appendPlainText(tr_msg('The installation failed (exit code {}). Run the command above by hand, or use the MCP connection.').format(code))
        self.refresh()

    def export(self):
        from .export import defaultExportPath, exportConversation
        config = self.plugin.config
        default = defaultExportPath(config) if config.get('versionName') else ''
        path, _ = QFileDialog.getSaveFileName(self, tr_msg('Export conversation'), default, 'HTML (*.html)')
        if path:
            exportConversation(path, self.conversation.transcript, self.conversation.model, self.conversation.costs,
                               config.get('projectName'), config.get('versionName'))
