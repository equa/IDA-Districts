# coding=utf-8
"""Dialog 'MCP configuration' (OpenSpec change ai-mcp-connection, D4): the registration of the MCP server for the Claude
Code CLI (one command), for the Chat tab of Claude Desktop (JSON) and for the Code tab of Claude Desktop and the VS Code
extension (.mcp.json in the folder opened there), with the paths of this computer."""
import json
import os

from qgis.PyQt.QtGui import QFontDatabase
from qgis.PyQt.QtWidgets import (
    QApplication, QDialog, QDialogButtonBox, QFileDialog, QHBoxLayout, QLabel, QMessageBox, QPlainTextEdit, QPushButton, QVBoxLayout,
)

from ..utility_functions.translations import tr_msg
from .bridge import claudeCli, claudeCodeCommand, claudeDesktopConfig, mcpConfiguration, writeMcpJson

CLAUDE_CODE_INSTALL = 'irm https://claude.ai/install.ps1 | iex'


class McpConfigDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle(tr_msg('MCP configuration'))
        self.resize(820, 640)
        layout = QVBoxLayout(self)
        cli = claudeCli()
        self.code_command = claudeCodeCommand(cli=cli)
        self.desktop_json = json.dumps(mcpConfiguration(), indent=2)

        layout.addWidget(self.heading(tr_msg('Claude Code (command line): run this command once in a terminal (PowerShell)')))
        self.edit_code = self.textBox(self.code_command, 70)
        layout.addWidget(self.edit_code)
        if cli and cli[1]:
            status = tr_msg('The claude command is found: {}').format(cli[0])
        elif cli:
            status = tr_msg('Claude Code is installed ({}) but not on the PATH of a terminal opened before the installation: '
                            'the command calls it with its full path.').format(cli[0])
        else:
            status = tr_msg('The claude command is not installed. Claude Desktop (also its Code tab) and the VS Code extension do not need it: '
                            'use the sections below. To install the command line: {} (then open a new terminal).').format(CLAUDE_CODE_INSTALL)
        self.label_cli = QLabel(status)
        self.label_cli.setWordWrap(True)
        layout.addWidget(self.label_cli)
        layout.addLayout(self.buttonRow(self.copyButton(self.code_command, tr_msg('Copy command'))))

        layout.addWidget(self.heading(tr_msg('Claude Desktop, Chat tab: Settings → Developer → Edit Config, add the entry "districts" under "mcpServers", '
                                             'then quit Claude Desktop completely and start it again')))
        layout.addWidget(QLabel(tr_msg('Configuration file: {}').format(claudeDesktopConfig())))
        self.edit_desktop = self.textBox(self.desktop_json, 180)
        layout.addWidget(self.edit_desktop)
        layout.addLayout(self.buttonRow(self.copyButton(self.desktop_json, tr_msg('Copy JSON'))))

        layout.addWidget(self.heading(tr_msg('Claude Desktop, Code tab, and the VS Code extension: a file .mcp.json in the folder you open there')))
        note = QLabel(tr_msg('Writes the entry "districts" into .mcp.json of the chosen folder (other entries are kept). Claude Code asks once '
                             'whether to use the servers of that folder. The file holds paths of this computer: do not commit it to a repository.'))
        note.setWordWrap(True)
        layout.addWidget(note)
        self.btn_write = QPushButton(tr_msg('Write .mcp.json ...'))
        self.btn_write.clicked.connect(self.chooseFolder)
        layout.addLayout(self.buttonRow(self.btn_write))

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

    def copyButton(self, text, label):
        button = QPushButton(label)
        button.clicked.connect(lambda: QApplication.clipboard().setText(text))
        return button

    def buttonRow(self, button):
        row = QHBoxLayout()
        row.addStretch()
        row.addWidget(button)
        return row

    def chooseFolder(self):
        folder = QFileDialog.getExistingDirectory(self, tr_msg('Folder you open in Claude Code'), os.path.expanduser('~'))
        if folder:
            self.writeTo(folder)

    def writeTo(self, folder):
        """writes .mcp.json and tells the result; returns the path or None"""
        try:
            path = writeMcpJson(folder)
        except (OSError, ValueError) as e:
            QMessageBox.warning(self, tr_msg('MCP configuration'), tr_msg('.mcp.json was not written: {}').format(e))
            return None
        QMessageBox.information(self, tr_msg('MCP configuration'), tr_msg('Written: {}. Open this folder in Claude Code and allow the server districts.').format(path))
        return path
