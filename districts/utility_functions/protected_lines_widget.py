# coding=utf-8
"""List of the protected lines (OpenSpec change protect-lines) for the cost optimization dialog: line IDs entered or
taken from the selection on the map; the list is the one of the hydraulic balancing (protected_lines.py)."""
from qgis.core import QgsProject
from qgis.PyQt.QtWidgets import QHBoxLayout, QListWidget, QListWidgetItem, QPushButton, QVBoxLayout, QWidget
from qgis.utils import iface

from .compat import MessageInfo
from .dialog import qt_item_flag
from .protected_lines import parseProtectedEntries
from .translations import tr, tr_msg


def linesLayer():
    """the active layer if it is the lines layer, otherwise the project's layer lines"""
    name = tr('@default', 'lines')
    layer = iface.activeLayer() if iface else None
    if layer is not None and layer.name() == name:
        return layer
    layers = QgsProject.instance().mapLayersByName(name)
    return layers[0] if layers else None


class ProtectedLinesWidget(QWidget):
    def __init__(self, tooltip=''):
        super().__init__()
        self.list = QListWidget()
        self.list.setMaximumHeight(90)
        self.list.setSelectionMode(QListWidget.SelectionMode.ExtendedSelection)
        self.list.setToolTip(tooltip)
        self.btn_add = QPushButton('+')
        self.btn_add.setToolTip(tr_msg('Add a line ID'))
        self.btn_add.clicked.connect(lambda: self.addEntry().setSelected(True))
        self.btn_remove = QPushButton('−')
        self.btn_remove.setToolTip(tr_msg('Remove the selected line IDs'))
        self.btn_remove.clicked.connect(self.removeSelected)
        self.btn_addSelected = QPushButton(tr_msg('Add selected lines'))
        self.btn_addSelected.setToolTip(tr_msg('Add the lines selected on the map (layer lines)'))
        self.btn_addSelected.clicked.connect(self.addSelected)
        buttons = QVBoxLayout()
        for button in (self.btn_add, self.btn_remove, self.btn_addSelected):
            buttons.addWidget(button)
        buttons.addStretch()
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(self.list, 1)
        layout.addLayout(buttons)

    def addEntry(self, text=''):
        item = QListWidgetItem(str(text))
        item.setFlags(item.flags() | qt_item_flag('ItemIsEditable'))
        self.list.addItem(item)
        return item

    def removeSelected(self):
        for item in self.list.selectedItems():
            self.list.takeItem(self.list.row(item))

    def setLines(self, lids):
        self.list.clear()
        for lid in lids:
            self.addEntry(lid)

    def texts(self):
        return [self.list.item(row).text() for row in range(self.list.count())]

    def entries(self):
        """(line ids, invalid entries)"""
        return parseProtectedEntries(self.texts())

    def addSelected(self):
        layer = linesLayer()
        features = layer.selectedFeatures() if layer is not None else []
        if not features:
            iface.messageBar().pushMessage(tr_msg('Info'), tr_msg('Please select lines in the layer lines.'), level=MessageInfo)
            return
        existing = {text.strip() for text in self.texts()}
        for lid in sorted(f['id'] for f in features):
            if str(lid) not in existing:
                self.addEntry(lid)
                existing.add(str(lid))
