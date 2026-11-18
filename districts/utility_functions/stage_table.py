# coding=utf-8
"""Table 'Stages' of the cost optimization (OpenSpec change network-stages D1): the stage versions in order with their
start year; the first row is the loaded version in year 0. One row: the optimization of a single version."""
from qgis.PyQt.QtWidgets import (
    QComboBox, QHBoxLayout, QHeaderView, QLabel, QPushButton, QSpinBox, QTableWidget, QVBoxLayout, QWidget,
)

from .translations import tr_msg

PROBLEM_TEXTS = {'empty': 'No stage.', 'first_start': 'The first stage ({}) has to start in year 0.',
                 'start_order': 'The start years have to increase (stage {}).',
                 'not_descendant': 'Stage {} is not a child version of the previous stage.',
                 'lines': 'Lines of the previous stage missing or moved in stage {}.'}


def problemText(problem):
    kind, detail = problem
    return tr_msg(PROBLEM_TEXTS[kind]).format(detail)


class StageTable(QWidget):
    def __init__(self, versions, loaded, info, parent=None):
        super().__init__(parent)
        self.versions = list(versions)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        label = QLabel(info)
        label.setWordWrap(True)
        layout.addWidget(label)
        self.table = QTableWidget(0, 2)
        self.table.setHorizontalHeaderLabels([tr_msg('Version'), tr_msg('Start year [a]')])
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.table.verticalHeader().setVisible(False)
        self.table.setMinimumHeight(110)
        layout.addWidget(self.table)
        buttons = QHBoxLayout()
        self.btn_add = QPushButton(tr_msg('Add a stage'))
        self.btn_remove = QPushButton(tr_msg('Remove'))
        buttons.addWidget(self.btn_add)
        buttons.addWidget(self.btn_remove)
        buttons.addStretch()
        layout.addLayout(buttons)
        self.btn_add.clicked.connect(lambda: self.addRow())
        self.btn_remove.clicked.connect(self.removeRows)
        self.addRow(loaded, 0)

    def addRow(self, version=None, start=None):
        row = self.table.rowCount()
        self.table.insertRow(row)
        combo = QComboBox()
        combo.addItems(self.versions)
        if version in self.versions:
            combo.setCurrentIndex(self.versions.index(version))
        spin = QSpinBox()
        spin.setRange(0, 200)
        spin.setValue(start if start is not None else (self.stages()[-2]['start'] + 10 if row else 0))
        # stage 1 is the loaded version and starts in year 0
        combo.setEnabled(row > 0)
        spin.setEnabled(row > 0)
        self.table.setCellWidget(row, 0, combo)
        self.table.setCellWidget(row, 1, spin)

    def removeRows(self):
        for row in sorted({index.row() for index in self.table.selectedIndexes()}, reverse=True):
            if row > 0:
                self.table.removeRow(row)

    def stages(self):
        """[{'version', 'start'}] in the order of the table"""
        return [{'version': self.table.cellWidget(row, 0).currentText(), 'start': self.table.cellWidget(row, 1).value()}
                for row in range(self.table.rowCount())]

    def setStages(self, stages):
        self.table.setRowCount(0)
        for stage in stages:
            self.addRow(stage['version'], stage['start'])
