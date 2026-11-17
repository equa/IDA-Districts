# coding=utf-8
"""Supply/return pairs chosen with dropdowns of the network's pipe sequences (hydraulic balancing, cost optimization);
the sequences come from pipe_pairs.networkSequences."""
from qgis.PyQt.QtWidgets import QAbstractItemView, QComboBox, QHBoxLayout, QHeaderView, QPushButton, QTableWidget, QVBoxLayout, QWidget

from .translations import tr_msg


def sequenceText(seq, label):
    return '{} – {}'.format(seq, label) if label else str(seq)


def setSequence(combo, value):
    """selects the sequence; one the network does not have (e.g. of a saved pair) is added and marked"""
    if value is None:
        combo.setCurrentIndex(-1)
        return
    index = combo.findData(int(value))
    if index < 0:
        combo.addItem(sequenceText(int(value), tr_msg('not in the network')), int(value))
        index = combo.count() - 1
    combo.setCurrentIndex(index)


def sequenceCombo(sequences, value=None):
    """dropdown of the sequences {seq: label}, the data is the sequence"""
    combo = QComboBox()
    combo.setPlaceholderText('–')
    for seq, label in sequences.items():
        combo.addItem(sequenceText(seq, label), seq)
    setSequence(combo, value)
    return combo


def comboRow(table, combo):
    """row of the table holding the combo as a cell widget (rows move when others are removed)"""
    for row in range(table.rowCount()):
        for col in range(table.columnCount()):
            if table.cellWidget(row, col) is combo:
                return row
    return -1


def rowsToRemove(table):
    """the selected rows, otherwise the current one (a click into a dropdown selects no row)"""
    rows = {index.row() for index in table.selectedIndexes()}
    if not rows and table.currentRow() >= 0:
        rows = {table.currentRow()}
    return sorted(rows, reverse=True)


class PairTable(QWidget):
    """Rows of supply and return dropdowns with + / −."""

    def __init__(self, tooltip=''):
        super().__init__()
        self.sequences = {}
        self.table = QTableWidget(0, 2)
        self.table.setHorizontalHeaderLabels([tr_msg('Supply'), tr_msg('Return')])
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.table.verticalHeader().setVisible(False)
        self.table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.table.setMaximumHeight(90)
        self.table.setToolTip(tooltip)
        self.btn_add = QPushButton('+')
        self.btn_add.setToolTip(tr_msg('Add a pair'))
        self.btn_add.clicked.connect(lambda: self.addRow(None, None))
        self.btn_remove = QPushButton('−')
        self.btn_remove.setToolTip(tr_msg('Remove the selected pairs'))
        self.btn_remove.clicked.connect(self.removeRows)
        buttons = QVBoxLayout()
        buttons.addWidget(self.btn_add)
        buttons.addWidget(self.btn_remove)
        buttons.addStretch()
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(self.table, 1)
        layout.addLayout(buttons)

    def setPairs(self, sequences, pairs):
        """the network's sequences {seq: label} and the pairs [(s, r, ...)]"""
        self.sequences = dict(sequences)
        self.table.setRowCount(0)
        for pair in pairs:
            self.addRow(pair[0], pair[1])

    def addRow(self, supply, ret):
        row = self.table.rowCount()
        self.table.insertRow(row)
        for col, value in enumerate((supply, ret)):
            combo = sequenceCombo(self.sequences, value)
            combo.activated.connect(lambda _, c=combo: self.table.setCurrentCell(comboRow(self.table, c), 0))
            self.table.setCellWidget(row, col, combo)

    def removeRows(self):
        for row in rowsToRemove(self.table):
            self.table.removeRow(row)

    def pairs(self):
        """[(s, r)] of the rows with both sequences chosen"""
        result = []
        for row in range(self.table.rowCount()):
            s, r = (self.table.cellWidget(row, col).currentData() for col in (0, 1))
            if s is not None and r is not None:
                result.append((int(s), int(r)))
        return result

    def incomplete(self):
        return self.table.rowCount() - len(self.pairs())
