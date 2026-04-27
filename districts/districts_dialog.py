from qgis.PyQt import QtWidgets, QtCore, uic
from qgis.PyQt.QtCore import QSettings,QObject,pyqtSignal
import os
from qgis.core import QgsApplication
from qgis.PyQt.QtCore import QSize,QRectF
from qgis.PyQt.QtGui import QIcon,QPixmap
from qgis.PyQt.QtWidgets import QSizePolicy


from qgis.PyQt.QtSvg import QSvgRenderer
from qgis.PyQt.QtWidgets import QWidget
from qgis.PyQt.QtGui import QPainter

from .utility_functions.compat import *
from .utility_functions.utility import *
from .utility_functions.dialog import *
import sys

current_dir = os.path.dirname(__file__)
if current_dir not in sys.path:
    sys.path.insert(0, current_dir)

from svg_label import SvgLabel

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
        self.lineEdit_pathProjects.setText(config["pathProjects"].replace('////','//'))
        self.lineEdit_pathDistricts.setText(config["pathDistricts"].replace('////','//'))
        self.lineEdit_districts_api_delay.setText(config["districts_api_delay"])
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
        btn_size=30
        self.btn_manageEnergyPlantTemplates.setIcon(QIcon(os.path.join(plugin_dir, "icons/Plant.svg")))
        self.btn_manageEnergyPlantTemplates.setIconSize(QSize(btn_size, btn_size))
        self.btn_manageCustomerTemplates.setIcon(QIcon(os.path.join(plugin_dir, "icons/Customer.svg")))
        self.btn_manageCustomerTemplates.setIconSize(QSize(btn_size, btn_size))

        self.btn_defaults_plants.setIcon(QIcon(os.path.join(plugin_dir, "icons/Plant.svg")))
        self.btn_defaults_plants.setIconSize(QSize(btn_size, btn_size))
        self.btn_defaults_customers.setIcon(QIcon(os.path.join(plugin_dir, "icons/Customer.svg")))
        self.btn_defaults_customers.setIconSize(QSize(btn_size, btn_size))
        self.btn_defaults_lines.setIcon(QIcon(":/images/themes/default/mIconLineLayer.svg"))
        self.btn_defaults_lines.setIconSize(QSize(btn_size, btn_size))
        
        self.btn_connections.setIcon(QIcon(os.path.join(plugin_dir, "icons/Connection.svg")))
        self.btn_connections.setIconSize(QSize(btn_size, btn_size))
        self.btn_connection_types.setIcon(QIcon(os.path.join(plugin_dir, "icons/Connection_type.svg")))
        self.btn_connection_types.setIconSize(QSize(btn_size, btn_size))
        self.btn_conn_bundle_types.setIcon(QIcon(os.path.join(plugin_dir, "icons/Connection_bundle_type.svg")))
        self.btn_conn_bundle_types.setIconSize(QSize(btn_size, btn_size))
        self.label_connBundleImage.set_min_height(200)
        self.label_connBundleImage.set_min_width(300)
        self.label_connBundleImage.load_svg(os.path.join(plugin_dir, "icons/Connections.svg"))
        
        self.btn_materials.setIcon(QIcon(os.path.join(plugin_dir, "icons/materials.png")))
        self.btn_materials.setIconSize(QSize(btn_size, btn_size))
        self.btn_pipe_constructions.setIcon(QIcon(os.path.join(plugin_dir, "icons/Pipe Construction.png")))
        self.btn_pipe_constructions.setIconSize(QSize(btn_size, btn_size))
        self.btn_pipes.setIcon(QIcon(os.path.join(plugin_dir, "icons/pipe.png")))
        self.btn_pipes.setIconSize(QSize(btn_size, btn_size))
        self.btn_pipe_bundle_types.setIcon(QIcon(os.path.join(plugin_dir, "icons/pipebundle.png")))
        self.btn_pipe_bundle_types.setIconSize(QSize(btn_size, btn_size))


        
        #import icons
        btn_size=30
        self.btn_importElevationData.setIcon(QIcon(":/images/themes/default/mActionElevationProfile.svg"))
        self.btn_importElevationData.setIconSize(QSize(btn_size, btn_size))
        self.btn_importPointLayer.setIcon(QIcon(":/images/themes/default/mIconPointLayer.svg"))
        self.btn_importPointLayer.setIconSize(QSize(btn_size, btn_size))
        self.btn_importNetworkTopologyFromLayer.setIcon(QIcon(":/images/themes/default/mIconLineLayer.svg"))
        self.btn_importNetworkTopologyFromLayer.setIconSize(QSize(btn_size, btn_size))
        self.btn_importMeasurements.setIcon(QIcon(":/images/themes/default/mActionMeasure.svg"))  
        self.btn_importMeasurements.setIconSize(QSize(btn_size, btn_size))
        self.btn_climate.setIcon(QIcon(os.path.join(plugin_dir, "icons/climate.svg")))  
        self.btn_climate.setIconSize(QSize(btn_size, btn_size))
        
        self.btn_importStreetsFromOSM.setIcon(QIcon(os.path.join(plugin_dir, "icons/streets.png")))
        self.btn_importStreetsFromOSM.setIconSize(QSize(btn_size, btn_size))
        self.btn_importBuildingsFromOSM.setIcon(QIcon(os.path.join(plugin_dir, "icons/Customer.svg")))
        self.btn_importBuildingsFromOSM.setIconSize(QSize(btn_size, btn_size))

        #preprocessing
        self.btn_manageNetworks.setIcon(QIcon(os.path.join(plugin_dir, "icons/Manage Networks_v2.svg")))
        self.btn_manageNetworks.setIconSize(QSize(200, 200))          
        
        btn_size=150
        self.btn_pipeLayingAlgorithm.setIcon(QIcon(os.path.join(plugin_dir, "icons/Pipe_Laying_Algo__.svg")))
        self.btn_pipeLayingAlgorithm.setIconSize(QSize(btn_size, btn_size))
        self.btn_mapFeatures.setIcon(QIcon(os.path.join(plugin_dir, "icons/LineMapping.svg")))
        self.btn_mapFeatures.setIconSize(QSize(btn_size, btn_size))   
        self.btn_generateTopology.setIcon(QIcon(os.path.join(plugin_dir, "icons/Generate_Topology_v2.svg")))
        self.btn_generateTopology.setIconSize(QSize(btn_size, btn_size))
        self.btn_pipeSizing.setIcon(QIcon(os.path.join(plugin_dir, "icons/Pipe_sizing.svg")))
        self.btn_pipeSizing.setIconSize(QSize(btn_size, btn_size))        

        #modeling & simulation
        btn_size=100
        self.btn_modellingSettings.setIcon(QIcon(":/images/themes/default/propertyicons/settings.svg"))
        self.btn_modellingSettings.setIconSize(QSize(btn_size, btn_size))   
        self.btn_requestedOutputs.setIcon(QIcon(os.path.join(plugin_dir, "icons/Checkliste.png")))
        self.btn_requestedOutputs.setIconSize(QSize(btn_size, btn_size))   
        
        self.btn_parmMapping.setIcon(QIcon(os.path.join(plugin_dir, "icons/ParameterMapping.png")))
        self.btn_parmMapping.setIconSize(QSize(btn_size, btn_size))   
        self.btn_sensorSignals.setIcon(QIcon(":/images/themes/default/propertyicons/sensor.svg"))
        self.btn_sensorSignals.setIconSize(QSize(btn_size, btn_size))   
        self.btn_supervisory.setIcon(QIcon(os.path.join(plugin_dir, "icons/SupervisoryCTRL.png")))
        self.btn_supervisory.setIconSize(QSize(btn_size, btn_size))   
        
        self.btn_buildModel.setIcon(QIcon(os.path.join(plugin_dir, "icons/BuildModel.png")))
        self.btn_buildModel.setIconSize(QSize(btn_size, btn_size))   
        self.btn_openModel.setIcon(QIcon(":/images/themes/default/mActionFileOpen.svg"))
        self.btn_openModel.setIconSize(QSize(btn_size, btn_size))   
        self.btn_featureModels.setIcon(QIcon(os.path.join(plugin_dir, "icons/FeatureModels.png")))
        self.btn_featureModels.setIconSize(QSize(btn_size, btn_size))   
        self.btn_runModel.setIcon(QIcon(":/images/themes/default/mTemporalNavigationAnimated.svg"))
        self.btn_runModel.setIconSize(QSize(btn_size, btn_size))   
        
        #results & visualization
        btn_size=100
        self.btn_loadResults.setIcon(QIcon(":/images/themes/default/dbmanager.svg"))
        self.btn_loadResults.setIconSize(QSize(btn_size, btn_size))   
        
        self.btn_path_reports.setIcon(QIcon(os.path.join(plugin_dir, "icons/pathreport.png")))
        self.btn_path_reports.setIconSize(QSize(btn_size, btn_size))  
        self.btn_plotLoadProfiles.setIcon(QIcon(os.path.join(plugin_dir, "icons/loadprofile.png")))
        self.btn_plotLoadProfiles.setIconSize(QSize(btn_size, btn_size))  
        
        self.btn_networkReport.setIcon(QIcon(":/images/themes/default/mIconReport.svg"))
        self.btn_networkReport.setIconSize(QSize(btn_size, btn_size))   
        
        self.btn_showDataOnMap.setIcon(QIcon(os.path.join(plugin_dir, "icons/map_plots.png")))
        self.btn_showDataOnMap.setIconSize(QSize(btn_size, btn_size))   
        
        # Drag state
        self._drag_start_pos = None
        self._floating_tabs = {}  # title -> (FloatingTabDialog, original_index)

        # Install event filter on tab bar for drag
        self.tabWidget.tabBar().installEventFilter(self)
        self.signals=CloseSignals()
        self.projetNames=[]
        
        font = self.projectNameLabel.font()
        font.setBold(True)
        self.projectNameLabel.setFont(font)
        font = self.versionNameLabel.font()
        font.setBold(True)
        self.versionNameLabel.setFont(font)
        
    def modelOpeningFinished(self,message):
        self.statusMessage.setText(message)
        
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
                    self._drag_start_pos = get_event_pos(event)

            elif event.type() == QtCore.QEvent.Type.MouseMove:
                if not self._drag_start_pos:
                    return False
                if not (event.buttons() & QtCore.Qt.MouseButton.LeftButton):
                    return False
                if (get_event_pos(event) - self._drag_start_pos).manhattanLength() \
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
