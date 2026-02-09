from PyQt6 import QtWidgets, QtCore, uic
from qgis.PyQt.QtCore import QSettings,QObject,pyqtSignal
import os
from qgis.core import QgsApplication
from .utility_functions.utility import *
from qgis.PyQt.QtCore import QSize,QRectF
from PyQt6.QtGui import QIcon,QPixmap
from qgis.PyQt.QtWidgets import QSizePolicy


from qgis.PyQt.QtSvg import QSvgRenderer
from qgis.PyQt.QtWidgets import QWidget
from qgis.PyQt.QtGui import QPainter

class SvgWidget(QWidget):
    def __init__(self, svg_file, parent=None):
        super().__init__(parent)
        self.renderer = QSvgRenderer(svg_file, self)
        self.setSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Preferred)

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.SmoothPixmapTransform)
        
        rect = self.rect()
        svg_size = self.renderer.defaultSize()
        if svg_size.width() == 0 or svg_size.height() == 0:
            return
        
        scale = min(rect.width() / svg_size.width(), rect.height() / svg_size.height())
        w = svg_size.width() * scale
        h = svg_size.height() * scale
        x = (rect.width() - w) / 2
        y = (rect.height() - h) / 2
        
        self.renderer.render(painter, QRectF(x, y, w, h))
        
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


class DistrictsSettingsDialog(QtWidgets.QDialog):
    def __init__(self):
        super().__init__()

        # Load UI
        ui_path = os.path.join(os.path.dirname(__file__), "districts_settings_dialog.ui")
        uic.loadUi(ui_path, self)
        
        config=load_plugin_settings()
        self.lineEdit_pathDistricts.setText(config["pathDistricts"])
        self.lineEdit_districts_api_delay.setText(config["districts_api_delay"])
        self.lineEdit_pathPostgres.setText(config["pathPostgres"])
        self.checkBox_debug.setChecked(config["debug"])
        self.groupBox_autosave.setChecked(config["autosave"])
        self.lineEdit_autosave_dt.setText(config["autosave_dt"])
        self.checkBox_exportInvokedFeatures.setChecked(config["exportInvokedFeatures"])
        self.checkBox_exportPrn.setChecked(config["exportPrn"])
        self.checkBox_exportDbResults.setChecked(config["exportDbResults"])
        self.lineEdit_host.setText(config["host"])
        self.lineEdit_port.setText(config["port"])
        
        self.auth_dict=getAuthNames()
        self.comboBox_AuthId.addItems(self.auth_dict)
        auth_name=[i for i in config["auth_id"] if i==config["auth_id"]]
        if auth_name:
            self.comboBox_AuthId.setCurrentText(auth_name)   

class CloseSignals(QObject):
    close=pyqtSignal(bool)
        
class DistrictsDialog(QtWidgets.QDialog):
    def __init__(self,plugin_dir):
        super().__init__()

        # Load UI
        ui_path = os.path.join(os.path.dirname(__file__), "districts_dialog_base.ui")
        uic.loadUi(ui_path, self)

        # Wrap it in a QIcon
        #project handling icons
        self.btn_settings.setIcon(QIcon(":/images/themes/default/mActionOptions.svg"))
        self.btn_createProject.setIcon(QIcon(":/images/themes/default/symbologyAdd.svg"))
        self.btn_addVersion.setIcon(QIcon(":/images/themes/default/symbologyAdd.svg"))
        self.btn_deleteProject.setIcon(QIcon(":/images/themes/default/symbologyRemove.svg"))
        self.btn_deleteVersion.setIcon(QIcon(":/images/themes/default/symbologyRemove.svg"))
        self.btn_sridProject.setIcon(QIcon(":/images/themes/default/mActionCustomProjection.svg"))
        self.btn_importProject.setIcon(QIcon(":/images/themes/default/mActionSharingImport.svg"))
        self.btn_exportProject.setIcon(QIcon(":/images/themes/default/mActionSharingExport.svg"))
        self.btn_loadVersion.setIcon(QIcon(":/images/themes/default/mActionRefresh.svg"))
        self.btn_help.setIcon(QIcon(":/images/themes/default/mActionHelpContents.svg"))
        
        #resource icons
        self.btn_connections.setIcon(QIcon(os.path.join(plugin_dir, "icons/Connection.svg")))
        self.btn_connections.setIconSize(QSize(24, 24))
        self.btn_connection_types.setIcon(QIcon(os.path.join(plugin_dir, "icons/Connection_type.svg")))
        self.btn_connection_types.setIconSize(QSize(24, 24))
        self.btn_conn_bundle_types.setIcon(QIcon(os.path.join(plugin_dir, "icons/Connection_bundle_type.svg")))
        self.btn_conn_bundle_types.setIconSize(QSize(24, 24))
        
        old = self.svg_connBundleImage
        self.svg_connBundleImage = SvgWidget(os.path.join(plugin_dir, "icons/Connections.svg"), parent=old.parent())
        old.parent().layout().replaceWidget(old, self.svg_connBundleImage)
        old.deleteLater()

        
        #import icons
        self.btn_importElevationData.setIcon(QIcon(":/images/themes/default/mActionElevationProfile.svg"))
        self.btn_importPointLayer.setIcon(QIcon(":/images/themes/default/mIconPointLayer.svg"))
        self.btn_importNetworkTopologyFromLayer.setIcon(QIcon(":/images/themes/default/mIconLineLayer.svg"))
        self.btn_importMeasurements.setIcon(QIcon(":/images/themes/default/mActionMeasure.svg"))
        
        old_osm = self.svg_osm
        self.svg_osm = SvgWidget(os.path.join(plugin_dir, "icons/Openstreetmap.svg"), parent=old_osm.parent())
        self.svg_osm.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        old_osm.parent().layout().replaceWidget(old_osm, self.svg_osm)
        old_osm.deleteLater()

        self.btn_importStreetsFromOSM.setIcon(QIcon(os.path.join(plugin_dir, "icons/Streets.svg")))
        self.btn_importStreetsFromOSM.setIconSize(QSize(20, 20))
        self.btn_importBuildingsFromOSM.setIcon(QIcon(os.path.join(plugin_dir, "icons/Buildings.svg")))
        self.btn_importBuildingsFromOSM.setIconSize(QSize(20, 20))

        #self.label_connBundleImage.setScaledContents(True)


        # Drag state
        self._drag_start_pos = None
        self._floating_tabs = {}  # title -> (FloatingTabDialog, original_index)

        # Install event filter on tab bar for drag
        self.tabWidget.tabBar().installEventFilter(self)
        self.signals=CloseSignals()
        self.projetNames=[]
        

    def update_progress(self,progress):
        self.progress.setValue(progress)
        
    def show_error_message(self, message):
        # Show the error message in a messageBar
        iface.messageBar().pushMessage("Error", message, level=Qgis.Critical)
        
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
