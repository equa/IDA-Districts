from PyQt6 import QtWidgets, QtCore, uic
import os

class FloatingTabDialog(QtWidgets.QDialog):
    """Floating window holding a detached tab"""

    def __init__(self, title, widget, parent_dialog):
        super().__init__(parent_dialog)
        self.setWindowTitle(title.replace("&&", "&"))
        self.setAttribute(QtCore.Qt.WidgetAttribute.WA_DeleteOnClose)
        self.parent_dialog = parent_dialog
        self.content_widget = widget

        # Set widget parent to this dialog and show it
        widget.setParent(self)
        widget.show()

    def closeEvent(self, event):
        # Return tab to the main dialog
        self.parent_dialog.return_tab(self.content_widget, self.windowTitle().replace("&", "&&"))
        super().closeEvent(event)


class DistrictsDialog(QtWidgets.QDialog):
    def __init__(self):
        super().__init__()

        # Load UI
        ui_path = os.path.join(os.path.dirname(__file__), "districts_dialog_base.ui")
        uic.loadUi(ui_path, self)

        # Drag state
        self._drag_start_pos = None
        self._floating_tabs = {}  # title -> (FloatingTabDialog, original_index)

        # Install event filter on tab bar for drag
        self.tabWidget.tabBar().installEventFilter(self)

    # ---------------- DRAG TAB TO FLOAT ----------------
    def eventFilter(self, source, event):
        tabbar = self.tabWidget.tabBar()
        if source is tabbar:
            if event.type() == QtCore.QEvent.Type.MouseButtonPress:
                if event.buttons() & QtCore.Qt.MouseButton.LeftButton:
                    self._drag_start_pos = event.position().toPoint()

            elif event.type() == QtCore.QEvent.Type.MouseMove:
                if not self._drag_start_pos:
                    return False
                if not (event.buttons() & QtCore.Qt.MouseButton.LeftButton):
                    return False
                if (event.position().toPoint() - self._drag_start_pos).manhattanLength() \
                        < QtWidgets.QApplication.startDragDistance():
                    return False

                index = self.tabWidget.currentIndex()
                if index < 0:
                    return False

                widget = self.tabWidget.widget(index)
                title = self.tabWidget.tabText(index)

                # --- Remove the tab completely and remember index ---
                self.tabWidget.removeTab(index)

                # --- Create floating window with the same widget ---
                floating = FloatingTabDialog(title, widget, self)
                floating.show()

                self._floating_tabs[title] = (floating, index)
                self._drag_start_pos = None
                return True

        return super().eventFilter(source, event)

    # ---------------- RETURN TAB FROM FLOATING ----------------
    def return_tab(self, widget, title):
        if title not in self._floating_tabs:
            return
        floating, index = self._floating_tabs[title]

        # Reparent the widget back to tabWidget
        widget.setParent(self.tabWidget)
        self.tabWidget.insertTab(index, widget, title)
        self.tabWidget.setCurrentWidget(widget)

        # Close floating window and remove from dict
        floating.close()
        self._floating_tabs.pop(title)
