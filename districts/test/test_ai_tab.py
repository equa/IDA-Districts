# coding=utf-8
"""Tab 'AI assistant' (OpenSpec change ai-chat-panel, spec ai-chat): a question with a tool call through the worker thread
and back to the main thread, Stop, the model change, the install box without the SDK. The project permission and the
tools are replaced here; test_ai_e2e.py runs them on a project.

    python -m pytest test/test_ai_tab.py -v
"""
from types import SimpleNamespace

import pytest
from qgis.PyQt.QtWidgets import QMessageBox

from districts.ai import access, chat_widget
from districts.mcp import tools as mcp_tools

from .conftest import wait_until
from .test_ai_chat import FakeBackend, message, text, tool_use

ALLOWED = {'allowed': True, 'disabled_tools': [], 'changed_by': None, 'changed_at': None}


def clear_choices():
    from qgis.PyQt.QtCore import QSettings
    QSettings().remove(chat_widget.SETTINGS_GROUP)


@pytest.fixture
def tab(monkeypatch):
    clear_choices()
    plugin = SimpleNamespace(config={'projectName': 'p', 'versionName': 'v', 'ai_auth_id': ''}, cur=None, plugin_dir='', process_running=False)
    monkeypatch.setattr(chat_widget.AiAssistantTab, 'projectSettings', lambda self: dict(ALLOWED))
    monkeypatch.setattr(mcp_tools, 'allowedTools', lambda ctx: mcp_tools.listTools())
    calls = []

    def call(ctx, name, args):
        calls.append((name, args))
        return {'findings': []}

    monkeypatch.setattr(mcp_tools, 'callTool', call)
    backend = FakeBackend([])
    widget = chat_widget.AiAssistantTab(plugin, backend_factory=lambda config: backend)
    widget.calls, widget.script = calls, backend.script
    yield widget
    if widget.worker is not None:
        widget.worker.wait(5000)
    widget.close()
    clear_choices()


def ask(widget, question):
    widget.input.setPlainText(question)
    widget.send()
    wait_until(lambda: widget.worker is None, 30, 'the answer of the fake backend')


def test_question_with_a_tool_call(tab):
    tab.script += [message([tool_use('t1', 'run_checks', {'scope': 'qgis'})], 'tool_use'), message([text('No findings.')], 'end_turn')]
    ask(tab, 'Check the version')
    assert tab.calls == [('run_checks', {'scope': 'qgis'})]
    assert [e['role'] for e in tab.conversation.transcript] == ['user', 'tool', 'assistant']
    page = tab.view.toPlainText()
    assert 'Check the version' in page and 'run_checks' in page and 'No findings.' in page
    assert 'session' in tab.label_cost.text() and tab.btn_export.isEnabled()
    # the result is collapsed until its line is clicked
    from qgis.PyQt.QtCore import QUrl
    assert '"findings"' not in page
    tab.toggleTool(QUrl('tool:1'))
    assert '"findings"' in tab.view.toPlainText()


def test_conversation_is_kept_and_continued(tab):
    tab.script += [message([text('First.')], 'end_turn'), message([text('Second.')], 'end_turn')]
    ask(tab, 'one')
    tab.hide()
    tab.show()
    ask(tab, 'two')
    assert [e['text'] for e in tab.conversation.transcript if e['role'] == 'assistant'] == ['First.', 'Second.']


def test_model_change_asks_and_starts_anew(tab, monkeypatch):
    tab.script.append(message([text('hi')], 'end_turn'))
    ask(tab, 'q')
    monkeypatch.setattr(QMessageBox, 'question', lambda *a, **k: QMessageBox.StandardButton.No)
    tab.combo_model.setCurrentIndex(1)
    assert tab.combo_model.currentData() == 'claude-opus-5-5' and tab.conversation.transcript
    monkeypatch.setattr(QMessageBox, 'question', lambda *a, **k: QMessageBox.StandardButton.Yes)
    tab.combo_model.setCurrentIndex(2)
    assert tab.conversation.model == 'claude-haiku-5-5' and not tab.conversation.transcript


def test_not_allowed_project_disables_send(tab, monkeypatch):
    monkeypatch.setattr(chat_widget.AiAssistantTab, 'projectSettings', lambda self: dict(ALLOWED, allowed=False))
    tab.refresh()
    assert not tab.btn_send.isEnabled() and 'not allowed' in tab.label_status.text()


def test_without_sdk_the_install_box(monkeypatch):
    monkeypatch.setattr(access, 'sdkVersion', lambda: None)
    monkeypatch.setattr(chat_widget.AiAssistantTab, 'projectSettings', lambda self: dict(ALLOWED))
    plugin = SimpleNamespace(config={'projectName': 'p', 'versionName': 'v', 'ai_auth_id': ''}, cur=None, plugin_dir='', process_running=False)
    widget = chat_widget.AiAssistantTab(plugin)
    widget.show()
    try:
        assert widget.install_box.isVisible() and not widget.btn_send.isEnabled()
        assert 'pip install --user --upgrade anthropic' in widget.label_install.text()
    finally:
        widget.close()


def test_permission_dialog_lists_the_data_of_each_tool():
    dlg = chat_widget.PermissionDialog(dict(ALLOWED, disabled_tools=['render_map']), 'p')
    names = {dlg.list_tools.item(k).text().split(' – ')[0] for k in range(dlg.list_tools.count())}
    assert 'render_map' in names and 'search_help' not in names
    assert dlg.disabledTools() == ['render_map'] and dlg.check_allowed.isChecked()
