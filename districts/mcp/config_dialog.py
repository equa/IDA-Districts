# coding=utf-8
"""Dialog 'MCP configuration' (OpenSpec change ai-mcp-connection, D4): the registration of the MCP server for Claude Code
(one command) and for Claude Desktop (JSON), with the paths of this computer, and whether the claude command is found."""
import json

from qgis.PyQt.QtGui import QFontDatabase
from qgis.PyQt.QtWidgets import QApplication, QDialog, QDialogButtonBox, QHBoxLayout, QLabel, QPlainTextEdit, QPushButton, QVBoxLayout

from ..utility_functions.translations import tr_msg
from .bridge import claudeCli, claudeCodeCommand, claudeDesktopConfig, mcpConfiguration

CLAUDE_CODE_INSTALL = 'irm https://claude.ai/install.ps1 | iex'


class McpConfigDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle(tr_msg('MCP configuration'))
        self.resize(820, 520)
        layout = QVBoxLayout(self)
        self.code_command = claudeCodeCommand()
        self.desktop_json = json.dumps(mcpConfiguration(), indent=2)
        cli = claudeCli()

        layout.addWidget(self.heading(tr_msg('Claude Code: run this command once in a terminal (PowerShell)')))
        self.edit_code = self.textBox(self.code_command, 70)
        layout.addWidget(self.edit_code)
        if cli:
            status = tr_msg('The claude command is found: {}').format(cli)
        else:
            status = tr_msg('The claude command is not found on this computer. Install Claude Code ({}), open a new terminal, '
                            'then run the command; or use Claude Desktop below.').format(CLAUDE_CODE_INSTALL)
        self.label_cli = QLabel(status)
        self.label_cli.setWordWrap(True)
        layout.addWidget(self.label_cli)
        layout.addLayout(self.copyRow(self.code_command, tr_msg('Copy command')))

        layout.addWidget(self.heading(tr_msg('Claude Desktop: Settings → Developer → Edit Config, add the entry "districts" under "mcpServers", '
                                             'then quit Claude Desktop completely and start it again')))
        layout.addWidget(QLabel(tr_msg('Configuration file: {}').format(claudeDesktopConfig())))
        self.edit_desktop = self.textBox(self.desktop_json, 200)
        layout.addWidget(self.edit_desktop)
        layout.addLayout(self.copyRow(self.desktop_json, tr_msg('Copy JSON')))

        layout.addWidget(self.heading(tr_msg('Then switch on Plugins → Districts Modeler → AI connection (MCP) in every QGIS session. '
                                             'Everything a tool returns is sent to Anthropic.')))
        buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Close)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

    def heading(self, text):
        label = QLabel(text)
        label.setWordWrap(True)
        font = label.font()
        font.setBold(True)
        label.setFont(font)
        return label

    def textBox(self, text, height):
        edit = QPlainTextEdit(text)
        edit.setReadOnly(True)
        edit.setFont(QFontDatabase.systemFont(QFontDatabase.SystemFont.FixedFont))
        edit.setMinimumHeight(height)
        return edit

    def copyRow(self, text, label):
        row = QHBoxLayout()
        button = QPushButton(label)
        button.clicked.connect(lambda: QApplication.clipboard().setText(text))
        row.addStretch()
        row.addWidget(button)
        return row
