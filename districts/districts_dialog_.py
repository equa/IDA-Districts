import os
from PyQt6 import QtWidgets, QtCore, uic


# ---------------- Floating Window ----------------

class FloatingTabDialog(QtWidgets.QDialog):
    def __init__(self, title, page_widget, parent_dialog):
        super().__init__(parent_dialog)
        self.setWindowTitle(title)
        self.setAttribute(QtCore.Qt.WidgetAttribute.WA_DeleteOnClose)
        self.parent_dialog = parent_dialog
        self.page_widget = page_widget

        layout = QtWidgets.QVBoxLayout(self)
        self.tabs = QtWidgets.QTabWidget()
        layout.addWidget(self.tabs)

        # echtes Tab-Gefühl
        self.tabs.addTab(page_widget, title)

    def closeEvent(self, event):
        self.parent_dialog.return_tab(self.page_widget, self.windowTitle())
        super().closeEvent(event)


# ---------------- Drag-fähige Tab-Liste ----------------

class TabListWidget(QtWidgets.QListWidget):
    tabDragged = QtCore.pyqtSignal(int)

    def __init__(self, parent=None):
        super().__init__(parent)
        self._dragStartPos = None

    def mousePressEvent(self, event):
        super().mousePressEvent(event)
        if self.itemAt(event.position().toPoint()):
            self._dragStartPos = event.position().toPoint()

    def mouseMoveEvent(self, event):
        super().mouseMoveEvent(event)
        if not self._dragStartPos:
            return

        distance = (event.position().toPoint() - self._dragStartPos).manhattanLength()
        if distance > QtWidgets.QApplication.startDragDistance():
            row = self.currentRow()
            if row >= 0:
                self.tabDragged.emit(row)
                self._dragStartPos = None


# ---------------- Hauptdialog ----------------

class DistrictsDialog(QtWidgets.QDialog):
    def __init__(self):
        super().__init__()

        ui_path = os.path.join(os.path.dirname(__file__), "districts_dialog_base.ui")
        uic.loadUi(ui_path, self)

        # tabList ersetzen (für Drag)
        self._replace_tablist()

        # Tab-Titel initialisieren
        self.tabList.addItem("Project Handling")
        self.tabList.addItem("Import")
        self.tabList.addItem("Data Center")

        self.tabList.currentRowChanged.connect(self.stackedContent.setCurrentIndex)
        self.tabList.setCurrentRow(0)

        self.tabList.tabDragged.connect(self.float_tab)

        self._floating = {}

        self._style_tabs()

    def _replace_tablist(self):
        layout = self.tabList.parent().layout()
        index = layout.indexOf(self.tabList)
        layout.removeWidget(self.tabList)
        self.tabList.deleteLater()

        self.tabList = TabListWidget()
        layout.insertWidget(index, self.tabList)

    def _style_tabs(self):
        self.tabList.setStyleSheet("""
        QListWidget::item {
            padding: 8px;
            border-bottom: 1px solid #ccc;
        }
        /* Item wenn ausgewählt */
        QListWidget::item:selected {
            background: #e6f0ff;       /* farbliche Hervorhebung */
            font-weight: bold;          /* optional */
            border: none;               /* kein inneres Rechteck */
            color: #000000;
        }
        """)

    def float_tab(self, row):
        page = self.stackedContent.widget(row)
        title = self.tabList.item(row).text()

        floating = FloatingTabDialog(title, page, self)
        floating.show()

        self.tabList.takeItem(row)
        self.stackedContent.removeWidget(page)

        self._floating[title] = page

    def return_tab(self, page, title):
        self.stackedContent.addWidget(page)
        self.tabList.addItem(title)
        self.tabList.setCurrentRow(self.tabList.count() - 1)
        self._floating.pop(title, None)
