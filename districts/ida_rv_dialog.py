from qgis.PyQt.QtWidgets import QTextEdit,QDialog,QGroupBox, QButtonGroup,QSpinBox,QShortcut,QListWidgetItem,QListWidget, QTabWidget, QTableWidgetItem,QTableWidget,QTreeView,QPushButton,QHBoxLayout,QVBoxLayout,QLabel,QLineEdit,QCheckBox,QComboBox, QProgressBar, QCheckBox,QRadioButton
from qgis.utils import iface
from qgis.core import QgsWkbTypes,QgsProperty,QgsSymbolLayer,QgsLineSymbol,QgsSymbol,QgsGraduatedSymbolRenderer,QgsStyle,QgsTemplatedLineSymbolLayerBase,QgsMarkerSymbol,QgsSimpleMarkerSymbolLayer,QgsMarkerLineSymbolLayer,QgsRuleBasedRenderer,QgsClassificationQuantile,QgsTextFormat,QgsInterval,QgsDateTimeRange,QgsTemporalNavigationObject,QgsVectorLayerSimpleLabeling,QgsPalLayerSettings

from .utility_functions.dialog import *
from .utility_functions.translations import *
from .utility_functions.topology import *
from .utility_functions.show_on_map import *

from decimal import Decimal
from qgis.PyQt.QtGui import QFont, QColor

import matplotlib.pyplot as plt

class ImportMeasuremntsDialog(QDialog):
    def __init__(self):     
        """Initialize GUI for plotting load profiles"""
        super().__init__()
        self.setWindowTitle("Import measurement data into DB")   
        
        self.label_description=QTextEdit(tr('@default','description_importPRNData'))
        
        #radio buttons features
        layout_rbtn_feature = QHBoxLayout()
        self.group_feature=QButtonGroup(self)
        self.rbtn_customers = QRadioButton(tr('@default','customers'))
        self.rbtn_customers.setChecked(True)
        self.rbtn_plants = QRadioButton(tr('@default','energy_plants'))
        self.rbtn_lines = QRadioButton(tr('@default','lines'))
        layout_rbtn_feature.addWidget(self.rbtn_customers)
        layout_rbtn_feature.addWidget(self.rbtn_plants)
        layout_rbtn_feature.addWidget(self.rbtn_lines)
        
        layout_data_source=QHBoxLayout()
        label_source =QLabel("Data source")
        layout_data_source.addWidget(label_source) 
        
        self.lineEditSourceName =QLineEdit("")
        layout_data_source.addWidget(self.lineEditSourceName)
        self.btn_file_source=QPushButton("Select a file")
        layout_data_source.addWidget(self.btn_file_source)
        self.btn_dir_source=QPushButton("Select a directory")
        layout_data_source.addWidget(self.btn_dir_source)
        
        self.tableVars = QTableWidget(0,4)  
        self.tableVars.setHorizontalHeaderLabels(['Variables','Alias','min','max'])     
        
        #interpolate timestep
        layout_interpolation=QVBoxLayout()
        self.checkbox_timestep=QCheckBox('data interpolation, s')
        self.checkbox_timestep.stateChanged.connect(self.interpolation_dt_state)
        layout_interpolation.addWidget(self.checkbox_timestep)
        self.interpolation_dt=QLineEdit('')
        self.interpolation_dt.setHidden(True)
        layout_interpolation.addWidget(self.interpolation_dt)

        #delete existing data
        self.delete_existing_data=QCheckBox('Delete data of selected variables')
        self.delete_existingID_data=QCheckBox('Delete data of selected variables with present feature ID')
        
        #buttons     
        layout_btn=QHBoxLayout()
        self.btn_import=QPushButton("Import")
        self.btn_cancel=QPushButton("Cancel")
        layout_btn.addWidget(self.btn_import)
        layout_btn.addWidget(self.btn_cancel)
        
        #---------------set layouts together-------------------
        layout = QVBoxLayout()
        layout.addWidget(self.label_description)
        layout.addLayout(layout_rbtn_feature)
        layout.addLayout(layout_data_source)
        layout.addWidget(self.tableVars)
        layout.addLayout(layout_interpolation)
        layout.addWidget(self.delete_existing_data)
        layout.addWidget(self.delete_existingID_data)
        layout.addLayout(layout_btn)
        layout.addStretch()
        
        self.setLayout(layout)
        
    def interpolation_dt_state(self, s):
        self.interpolation_dt.setHidden(s != checkState())
            
class NetworkReportDialog(QDialog):
    def __init__(self,plugin_dir):
        super().__init__()

        # Load UI
        ui_path = os.path.join(os.path.dirname(__file__), "network_report.ui")
        uic.loadUi(ui_path, self)
        self.btn_addPlot.setIcon(QIcon(":/images/themes/default/symbologyAdd.svg"))
        self.btn_deletePlot.setIcon(QIcon(":/images/themes/default/symbologyRemove.svg"))
        self.data=[]
    
    def deleteTableRow(self):
        """ Delete selected template and refresh table"""
        #print('delete row')
        row_index=self.tableWidget_diagrams.currentRow()
        #print(row_index)
        if row_index!=-1:
            self.data = [i for i in self.data if i.get("name") != self.tableWidget_diagrams.item(row_index,0).text()]
            self.tableWidget_diagrams.removeRow(row_index)
        else:
            self.iface.messageBar().pushMessage("Info", "No item selected!", level=Qgis.Info)
        

class PlotLoadProfilesDialog(QDialog):
    def __init__(self):     
        """Initialize GUI for plotting load profiles"""
        super().__init__()
        self.setWindowTitle("Plot features load profiles")   
        
        #Select network with checkable combobox
        layout_network=QHBoxLayout()
        label_network =QLabel("Network")
        layout_network.addWidget(label_network)
        self.combo_networks = CheckableComboBox()
        layout_network.addWidget(self.combo_networks)       
        
        #Select feature type by radio button 
        layout_rbtn_feature_type = QHBoxLayout()
        self.rbtn_customer = QRadioButton('Customers')
        self.rbtn_customer.setChecked(True)
        self.rbtn_energy_plant = QRadioButton('Energy plants')
           
        layout_rbtn_feature_type.addWidget(self.rbtn_customer)
        layout_rbtn_feature_type.addWidget(self.rbtn_energy_plant)
        
        #Feature ID`s list
        self.listWidget_ids= QListWidget()
        self.listWidget_ids.setSelectionMode(QtWidgets.QAbstractItemView.SelectionMode.ExtendedSelection)
        
        #buttons     
        layout_btn=QHBoxLayout()
        self.btn_plot=QPushButton("Plot selected features data")
        self.btn_cancel=QPushButton("Cancel")
        layout_btn.addWidget(self.btn_plot)
        layout_btn.addWidget(self.btn_cancel)
        
        #---------------set layouts together-------------------
        layout = QVBoxLayout()
        layout.addLayout(layout_network)
        layout.addLayout(layout_rbtn_feature_type)
        layout.addWidget(self.listWidget_ids)
        layout.addLayout(layout_btn)
        layout.addStretch()
        
        self.setLayout(layout)
        
class ShowOnMapDialog(QDialog):
    def __init__(self,cur,config,plugin_dir,dlg_main,networkReportDlg=None,function_items=None,time_values=None):     
        """Initialize GUI for path reports"""
        super().__init__()
        
        self.dlg_main=dlg_main
        self.config=config
        self.plugin_dir=plugin_dir
        self.cur=cur
        self.type=''
        self.feature=''
        self.color_table_name=''
        self.size_table_name=''
        if function_items:
            self.function_items=function_items
        else:    
            self.function_items=['Max','Min','Values','Hourly average','Daily average','Monthly average','Average','Sum','Last value','First value']
        
        if time_values:
            self.time_values=time_values
        else: 
            self.time_values=['Values','Hourly average','Daily average','Monthly average']
        self.colorramps=['Magma','Blues','Cividis','Greens','Greys','Mako','RdGy','Reds','Rocket','Spectral','Turbo','Viridis']
        self.colormodes=['Equal Count','Equal Interval']
        self.process_running=False
        self.networkReportDlg=networkReportDlg
        
        self.setWindowTitle("Show data on map")   

        #radio buttons Measurement data/Simulation data
        layout_rbtn_dataGroup = QHBoxLayout()
        self.group_dataGroup=QButtonGroup(self)
        self.rbtn_simData = QRadioButton('Simulation data')
        self.rbtn_simData.setChecked(True)
        self.rbtn_mDatap = QRadioButton('Measurement data')
        #self.rbtn_mDatap.toggled.connect(self.dataGroupChanged)
        self.group_dataGroup.buttonClicked.connect(self.dataGroupChanged)

        layout_rbtn_dataGroup.addWidget(self.rbtn_simData)             
        layout_rbtn_dataGroup.addWidget(self.rbtn_mDatap)
        self.group_dataGroup.addButton(self.rbtn_simData)  
        self.group_dataGroup.addButton(self.rbtn_mDatap)      
        
        #radio buttons features
        layout_rbtn_feature = QHBoxLayout()
        self.group_feature=QButtonGroup(self)
        self.rbtn_customers = QRadioButton('Customers')
        self.rbtn_customers.setChecked(True)
        self.rbtn_plants = QRadioButton('Energy plants')
        self.rbtn_lines = QRadioButton('Lines')
           
        layout_rbtn_feature.addWidget(self.rbtn_customers)
        layout_rbtn_feature.addWidget(self.rbtn_plants)  
        layout_rbtn_feature.addWidget(self.rbtn_lines)  
        self.group_feature.addButton(self.rbtn_customers)      
        self.group_feature.addButton(self.rbtn_plants)      
        self.group_feature.addButton(self.rbtn_lines)  
        self.group_feature.buttonClicked.connect(self.featureGroupChanged)
        
        layout_lineSegVis = QHBoxLayout()
        self.label_lineSegVis=QLabel('Line segment length for visualization, m')
        self.label_lineSegVis.setHidden(True)
        self.lineSegVis=QSpinBox()
        self.lineSegVis.setHidden(True)
        self.lineSegVis.setValue(int(loadModellingSettings(self.plugin_dir,self.config)['fd_meterPerNode']))
        self.lineSegVis.setMinimum(0) 
        self.lineSegVis.setMaximum(1000) 
        layout_lineSegVis.addWidget(self.label_lineSegVis)
        layout_lineSegVis.addWidget(self.lineSegVis)
        
        
        #----Use Color ramp for GraduatedSymbolRenderer----
        layout_varColor = QVBoxLayout()
        self.checkbox_varColor=QCheckBox('Color')
        self.checkbox_varColor.stateChanged.connect(self.colorStateChanged)
        layout_varColor.addWidget(self.checkbox_varColor)
        
        #---radio buttons var/par selection---
        #--var--
        layout_colorVarSelection = QHBoxLayout()
        self.group_colorVarSelection=QButtonGroup(self)
        self.rbtn_colorVar = QRadioButton('Variable')
        self.rbtn_colorVar.setChecked(True)
        self.rbtn_colorVar.setStyleSheet("padding-left: 30")
        self.rbtn_colorVar.setHidden(True)

        
        #variable selection
        self.color_var = QComboBox()
        self.color_var.currentTextChanged.connect(lambda signal: self.color_varChanged(signal))
        self.color_var.setHidden(True)
        #Select a function
        self.color_function = QComboBox()
        self.color_function.addItems(self.function_items)
        self.color_function.currentTextChanged.connect(lambda signal: self.color_function_Changed(signal))
        self.color_function.setHidden(True)
        
        #--par--
        self.rbtn_colorPar = QRadioButton('Parameter')
        self.rbtn_colorPar.setHidden(True)
        #parameter selection
        self.color_par = QComboBox()
        self.color_par.setHidden(True)
           
        layout_colorVarSelection.addWidget(self.rbtn_colorVar)
        layout_colorVarSelection.addWidget(self.color_var)
        layout_colorVarSelection.addWidget(self.color_function)
        layout_colorVarSelection.addWidget(self.rbtn_colorPar)  
        layout_colorVarSelection.addWidget(self.color_par)  
        self.group_colorVarSelection.addButton(self.rbtn_colorVar)      
        self.group_colorVarSelection.addButton(self.rbtn_colorPar)      
        self.group_colorVarSelection.buttonClicked.connect(self.varSelectionGroupChanged)
        layout_varColor.addLayout(layout_colorVarSelection)      

        #additional color settings
        layout_additional_colorSettings=QHBoxLayout()

        layout_label_additional_colorSettings=QVBoxLayout()
        self.label_colorramp =QLabel('Color ramp')
        self.label_colorramp.setHidden(True)
        self.label_colorramp.setStyleSheet("padding-left: 30")
        self.label_color_classes =QLabel('Classes')
        self.label_color_classes.setStyleSheet("padding-left: 30")
        self.label_color_classes.setHidden(True)
        self.label_color_mode =QLabel('Mode')
        self.label_color_mode.setStyleSheet("padding-left: 30")
        self.label_color_mode.setHidden(True)
        self.label_color_label =QLabel('Label')
        self.label_color_label.setStyleSheet("padding-left: 30")
        self.label_color_label.setHidden(True)
        layout_label_additional_colorSettings.addWidget(self.label_colorramp)
        layout_label_additional_colorSettings.addWidget(self.label_color_classes)
        layout_label_additional_colorSettings.addWidget(self.label_color_mode)
        layout_label_additional_colorSettings.addWidget(self.label_color_label)

        layout_values_additional_colorSettings=QVBoxLayout()
        self.colorramp =QComboBox()
        self.colorramp.setHidden(True)
        self.colorramp.addItems(self.colorramps)
        self.color_classes =QSpinBox()
        self.color_classes.setHidden(True)
        self.color_classes.setValue(10)
        self.color_classes.setMinimum(1) 
        self.colormode =QComboBox()
        self.colormode.setHidden(True)
        self.colormode.addItems(self.colormodes)        
        self.colorlabel =QCheckBox()
        self.colorlabel.setHidden(True)
        layout_values_additional_colorSettings.addWidget(self.colorramp)
        layout_values_additional_colorSettings.addWidget(self.color_classes)
        layout_values_additional_colorSettings.addWidget(self.colormode)
        layout_values_additional_colorSettings.addWidget(self.colorlabel)
        
        layout_additional_colorSettings.addLayout(layout_label_additional_colorSettings)
        layout_additional_colorSettings.addLayout(layout_values_additional_colorSettings)
        layout_varColor.addLayout(layout_additional_colorSettings)

        #----Use Size for GraduatedSymbolRenderer----
        layout_varSize = QVBoxLayout()
        self.checkbox_varSize=QCheckBox('Size')
        self.checkbox_varSize.stateChanged.connect(self.sizeStateChanged)
        layout_varSize.addWidget(self.checkbox_varSize)
        
        #---radio buttons var/par selection---
        #--var--
        layout_sizeVarSelection = QHBoxLayout()
        self.group_sizeVarSelection=QButtonGroup(self)
        self.rbtn_sizeVar = QRadioButton('Variable')
        self.rbtn_sizeVar.setChecked(True)
        self.rbtn_sizeVar.setStyleSheet("padding-left: 30")
        self.rbtn_sizeVar.setHidden(True)

        
        #variable selection
        self.size_var = QComboBox()
        self.size_var.currentTextChanged.connect(lambda signal: self.size_varChanged(signal))
        self.size_var.setHidden(True)
        #Select a function
        self.size_function = QComboBox()
        self.size_function.addItems(self.function_items)
        self.size_function.setHidden(True)
        self.size_function.currentTextChanged.connect(lambda signal: self.size_function_Changed(signal))

        
        #--par--
        self.rbtn_sizePar = QRadioButton('Parameter')
        self.rbtn_sizePar.setHidden(True)
        #parameter selection
        self.size_par = QComboBox()
        self.size_par.setHidden(True)
           
        layout_sizeVarSelection.addWidget(self.rbtn_sizeVar)
        layout_sizeVarSelection.addWidget(self.size_var)
        layout_sizeVarSelection.addWidget(self.size_function)
        layout_sizeVarSelection.addWidget(self.rbtn_sizePar)  
        layout_sizeVarSelection.addWidget(self.size_par)  
        self.group_sizeVarSelection.addButton(self.rbtn_sizeVar)      
        self.group_sizeVarSelection.addButton(self.rbtn_sizePar)      
        self.group_sizeVarSelection.buttonClicked.connect(self.varSelectionGroupChanged)
        layout_varSize.addLayout(layout_sizeVarSelection)      

        #additional size settings
        layout_additional_sizeSettings=QHBoxLayout()

        layout_label_additional_sizeSettings=QVBoxLayout()
        self.label_size_symbolMax =QLabel('Symbol size max')
        self.label_size_symbolMax.setHidden(True)
        self.label_size_symbolMax.setStyleSheet("padding-left: 30")
        self.label_size_symbolMin =QLabel('Symbol size min')
        self.label_size_symbolMin.setHidden(True)
        self.label_size_symbolMin.setStyleSheet("padding-left: 30")

        layout_label_additional_sizeSettings.addWidget(self.label_size_symbolMax)
        layout_label_additional_sizeSettings.addWidget(self.label_size_symbolMin)


        layout_values_additional_sizeSettings=QVBoxLayout()
        self.size_symbolMax=QLineEdit('10')
        self.size_symbolMax.setHidden(True)
        self.size_symbolMin=QLineEdit('1')
        self.size_symbolMin.setHidden(True)
        layout_values_additional_sizeSettings.addWidget(self.size_symbolMax)
        layout_values_additional_sizeSettings.addWidget(self.size_symbolMin)
        
        layout_additional_sizeSettings.addLayout(layout_label_additional_sizeSettings)
        layout_additional_sizeSettings.addLayout(layout_values_additional_sizeSettings)
        layout_varSize.addLayout(layout_additional_sizeSettings)

        #----Use Rotation for GraduatedSymbolRenderer----
        layout_varRotation = QVBoxLayout()
        self.checkbox_varRotation=QCheckBox('Rotation')
        self.checkbox_varRotation.stateChanged.connect(self.rotationStateChanged)
        layout_varRotation.addWidget(self.checkbox_varRotation)
        
        #---radio buttons var/par selection---
        #--var--
        layout_rotationVarSelection = QHBoxLayout()
        self.group_rotationVarSelection=QButtonGroup(self)
        self.rbtn_rotationVar = QRadioButton('Variable')
        self.rbtn_rotationVar.setChecked(True)
        self.rbtn_rotationVar.setStyleSheet("padding-left: 30")
        self.rbtn_rotationVar.setHidden(True)
        
        #variable selection
        self.rotation_var = QComboBox()
        self.rotation_var.currentTextChanged.connect(lambda signal: self.rotation_varChanged(signal))
        self.rotation_var.setHidden(True)
        #Select a function
        self.rotation_function = QComboBox()
        self.rotation_function.addItems(self.function_items)
        self.rotation_function.setHidden(True)
        self.rotation_function.currentTextChanged.connect(lambda signal: self.rotation_function_Changed(signal))

        
        #--par--
        self.rbtn_rotationPar = QRadioButton('Parameter')
        self.rbtn_rotationPar.setHidden(True)
        #parameter selection
        self.rotation_par = QComboBox()
        self.rotation_par.setHidden(True)
           
        layout_rotationVarSelection.addWidget(self.rbtn_rotationVar)
        layout_rotationVarSelection.addWidget(self.rotation_var)
        layout_rotationVarSelection.addWidget(self.rotation_function)
        layout_rotationVarSelection.addWidget(self.rbtn_rotationPar)  
        layout_rotationVarSelection.addWidget(self.rotation_par)  
        self.group_rotationVarSelection.addButton(self.rbtn_rotationVar)      
        self.group_rotationVarSelection.addButton(self.rbtn_rotationPar)      
        self.group_rotationVarSelection.buttonClicked.connect(self.varSelectionGroupChanged)
        layout_varRotation.addLayout(layout_rotationVarSelection)      

        #additional rotation settings
        layout_additional_rotationSettings=QHBoxLayout()

        layout_label_additional_rotationSettings=QVBoxLayout()
        self.label_rotation_symbolMax =QLabel('Rotation at max value, °')
        self.label_rotation_symbolMax.setHidden(True)
        self.label_rotation_symbolMax.setStyleSheet("padding-left: 30")
        self.label_rotation_symbolMin =QLabel('Rotation at min value, °')
        self.label_rotation_symbolMin.setHidden(True)
        self.label_rotation_symbolMin.setStyleSheet("padding-left: 30")

        layout_label_additional_rotationSettings.addWidget(self.label_rotation_symbolMax)
        layout_label_additional_rotationSettings.addWidget(self.label_rotation_symbolMin)


        layout_values_additional_rotationSettings=QVBoxLayout()
        self.rotation_symbolMax =QSpinBox()
        self.rotation_symbolMax.setHidden(True)
        self.rotation_symbolMax.setMinimum(0) 
        self.rotation_symbolMax.setMaximum(360) 
        self.rotation_symbolMax.setValue(350)
        self.rotation_symbolMin =QSpinBox()
        self.rotation_symbolMin.setHidden(True)
        self.rotation_symbolMin.setMinimum(0) 
        self.rotation_symbolMin.setMaximum(360) 
        self.rotation_symbolMin.setValue(0)
        
        layout_values_additional_rotationSettings.addWidget(self.rotation_symbolMax)
        layout_values_additional_rotationSettings.addWidget(self.rotation_symbolMin)
        
        layout_additional_rotationSettings.addLayout(layout_label_additional_rotationSettings)
        layout_additional_rotationSettings.addLayout(layout_values_additional_rotationSettings)
        layout_varRotation.addLayout(layout_additional_rotationSettings)
        
        #Layer name
        layout_layer_name=QHBoxLayout()
        label_layer_name=QLabel('Layer name')
        layout_layer_name.addWidget(label_layer_name)
        self.layer_name=QLineEdit()
        layout_layer_name.addWidget(self.layer_name)
        
        #time vor variables
        layout_timeSettings=QHBoxLayout()

        layout_label_timeSettings=QVBoxLayout()
        self.label_starttime =QLabel('Start date')
        self.label_starttime.setHidden(True)
        self.label_endtime =QLabel('End date')
        self.label_endtime.setHidden(True)
        layout_label_timeSettings.addWidget(self.label_starttime)
        layout_label_timeSettings.addWidget(self.label_endtime)
        
        layout_value_timeSettings=QVBoxLayout()
        self.starttime=QLineEdit(str(QtCore.QDate.currentDate().year())+'-01-01 00:00:00')
        self.starttime.setHidden(True)
        self.endtime=QLineEdit(str(QtCore.QDate.currentDate().year())+'-01-02 00:00:00')
        self.endtime.setHidden(True)
        layout_value_timeSettings.addWidget(self.starttime)
        layout_value_timeSettings.addWidget(self.endtime)
        
        layout_timeSettings.addLayout(layout_label_timeSettings)
        layout_timeSettings.addLayout(layout_value_timeSettings)

        
        #buttons     
        layout_btn=QHBoxLayout()
        self.btn_showOnMap=QPushButton("Show on map")
        self.btn_cancel=QPushButton("Cancel")
        layout_btn.addWidget(self.btn_showOnMap)
        layout_btn.addWidget(self.btn_cancel)
        
        #progress bar
        self.progress=QProgressBar()
        
        #---------------set layouts together-------------------
        layout = QVBoxLayout()
        layout.addLayout(layout_rbtn_dataGroup)
        layout.addLayout(layout_rbtn_feature)      
        layout.addLayout(layout_lineSegVis)      
        layout.addLayout(layout_varColor)      
        layout.addLayout(layout_varSize)      
        layout.addLayout(layout_varRotation)      
        layout.addLayout(layout_layer_name)
        layout.addLayout(layout_timeSettings)
        layout.addLayout(layout_btn)
        if not networkReportDlg:
            layout.addWidget(self.progress)
        layout.addStretch()
        
        self.setLayout(layout)
        
    def update_progress(self,progress):
        self.progress.setValue(progress)

    def update_finished(self, message, worker):
        """
        Called in main thread when worker finished.
        Signature: (message: str, worker: WorkerShowOnMap)
        """
        
        #print("=== update_finished START ===", message)
        try:
            # convenience
            layer = worker.temp_layer
        except:
            layer=None

        # 0) make sure layer exists
        if layer is None:
            #print("No layer returned from worker.")
            self.process_running = False
            addTableRow(self.networkReportDlg.tableWidget_diagrams)
            self.networkReportDlg.tableWidget_diagrams.setItem(0, 0, QTableWidgetItem(self.layer_name.text()))
            self.networkReportDlg.data.append({'name':self.layer_name.text(),'data' : worker.vars,'feature': 'customer' if self.rbtn_customers.isChecked() else ('line' if self.rbtn_lines.isChecked() else 'energy_plant'),
                'first_time_var': worker.first_time_var,'colorlabel': self.colorlabel.isChecked(),'varRotation': self.checkbox_varRotation.isChecked(),
                'color_classes': self.color_classes.text(),'colormode': self.colormode.currentText(),'colorramp': self.colorramp.currentText(),
                'size_symbolMin': self.size_symbolMin.text(),'size_symbolMax': self.size_symbolMax.text(),'rotation_symbolMin': self.rotation_symbolMin.text(),'rotation_symbolMax': self.rotation_symbolMax.text()})
            return False

        # 1) Ensure no edit session is open
        if layer and layer.isEditable():
            try:
                layer.commitChanges()
                #print("Committed pending edits.")
            except Exception as e:
                #print("Commit error:", e)
                layer.rollBack()
        
        if layer:
            renderMapPlot(layer,worker.vars,self.cur,self.config,first_time_var=worker.first_time_var,colorlabel=self.colorlabel.isChecked(),varRotation=self.checkbox_varRotation.isChecked(),
                color_classes=self.color_classes.text(),colormode=self.colormode.currentText(),colorramp=self.colorramp.currentText(),feature=self.feature,
                size_symbolMin=self.size_symbolMin.text(),size_symbolMax=self.size_symbolMax.text(),rotation_symbolMin=self.rotation_symbolMin.text(),rotation_symbolMax=self.rotation_symbolMax.text())

        #print("=== update_finished END ===")
        self.dlg_main.statusMessage.setText(message)        
        self.process_running = False

        
    def colorStateChanged(self,s):
        if checkState()==s:
            #print('checked')
            self.rbtn_colorVar.setHidden(False)
            self.color_var.setHidden(False)
            self.color_function.setHidden(False)
            self.rbtn_colorPar.setHidden(False)
            self.color_par.setHidden(False)
            self.label_colorramp.setHidden(False)
            self.label_color_classes.setHidden(False)
            self.label_color_mode.setHidden(False)
            self.label_color_label.setHidden(False)
            self.colorramp.setHidden(False)
            self.color_classes.setHidden(False)
            self.colormode.setHidden(False)
            self.colorlabel.setHidden(False)
                
        else:
            #print('unckecked')
            self.rbtn_colorVar.setHidden(True)
            self.color_var.setHidden(True)
            self.color_function.setHidden(True)
            self.color_par.setHidden(True)
            self.rbtn_colorPar.setHidden(True)
            self.label_colorramp.setHidden(True)
            self.label_color_classes.setHidden(True)
            self.label_color_mode.setHidden(True)
            self.label_color_label.setHidden(True)
            self.colorramp.setHidden(True)
            self.color_classes.setHidden(True)
            self.colormode.setHidden(True)
            self.colorlabel.setHidden(True)
        self.varSelectionGroupChanged(False)

    def varSelectionGroupChanged(self,radioButton):
        #print('radio var/par changed')
        if self.rbtn_colorVar.isChecked() and self.checkbox_varColor.isChecked() or self.rbtn_sizeVar.isChecked() and self.checkbox_varSize.isChecked() or self.rbtn_rotationVar.isChecked() and self.checkbox_varRotation.isChecked():
            if self.label_endtime.isHidden():
                self.label_endtime.setHidden(False)
                self.label_starttime.setHidden(False)
                self.starttime.setHidden(False)
                self.endtime.setHidden(False)
        else:
            if not self.label_endtime.isHidden():
                self.label_endtime.setHidden(True)
                self.label_starttime.setHidden(True)
                self.starttime.setHidden(True)
                self.endtime.setHidden(True)

    def sizeStateChanged(self,s):
        if checkState()==s:
            #print('checked')
            self.rbtn_sizeVar.setHidden(False)
            self.size_var.setHidden(False)
            self.size_function.setHidden(False)
            self.rbtn_sizePar.setHidden(False)
            self.size_par.setHidden(False)
            self.label_size_symbolMax.setHidden(False)
            self.label_size_symbolMin.setHidden(False)
            self.size_symbolMax.setHidden(False)
            self.size_symbolMin.setHidden(False)

        else:
            #print('unckecked')
            self.rbtn_sizeVar.setHidden(True)
            self.size_var.setHidden(True)
            self.size_function.setHidden(True)
            self.rbtn_sizePar.setHidden(True)
            self.size_par.setHidden(True)
            self.label_size_symbolMax.setHidden(True)
            self.label_size_symbolMin.setHidden(True)
            self.size_symbolMax.setHidden(True)
            self.size_symbolMin.setHidden(True)
        self.varSelectionGroupChanged(False)

    def rotationStateChanged(self,s):
        if checkState()==s:
            #print('checked')
            self.rbtn_rotationVar.setHidden(False)
            self.rotation_var.setHidden(False)
            self.rotation_function.setHidden(False)
            self.rbtn_rotationPar.setHidden(False)
            self.rotation_par.setHidden(False)
            self.label_rotation_symbolMax.setHidden(False)
            self.label_rotation_symbolMin.setHidden(False)
            self.rotation_symbolMax.setHidden(False)
            self.rotation_symbolMin.setHidden(False)

        else:
            #print('unckecked')
            self.rbtn_rotationVar.setHidden(True)
            self.rotation_var.setHidden(True)
            self.rotation_function.setHidden(True)
            self.rbtn_rotationPar.setHidden(True)
            self.rotation_par.setHidden(True)
            self.label_rotation_symbolMax.setHidden(True)
            self.label_rotation_symbolMin.setHidden(True)
            self.rotation_symbolMax.setHidden(True)
            self.rotation_symbolMin.setHidden(True)
        self.varSelectionGroupChanged(False)
            
    def hideRotationWidgets(self):
        self.rbtn_rotationVar.setHidden(True)
        self.rotation_var.setHidden(True)
        self.rotation_function.setHidden(True)
        self.rbtn_rotationPar.setHidden(True)
        self.rotation_par.setHidden(True)
        self.label_rotation_symbolMax.setHidden(True)
        self.label_rotation_symbolMin.setHidden(True)
        self.rotation_symbolMax.setHidden(True)
        self.rotation_symbolMin.setHidden(True)
            
    def displayRotationWidgets(self):
        self.rbtn_rotationVar.setHidden(False)
        self.rotation_var.setHidden(False)
        self.rotation_function.setHidden(False)
        self.rbtn_rotationPar.setHidden(False)
        self.rotation_par.setHidden(False)
        self.label_rotation_symbolMax.setHidden(False)
        self.label_rotation_symbolMin.setHidden(False)
        self.rotation_symbolMax.setHidden(False)
        self.rotation_symbolMin.setHidden(False)

    def hideSizeWidgets(self):
        self.rbtn_sizeVar.setHidden(True)
        self.size_var.setHidden(True)
        self.size_function.setHidden(True)
        self.rbtn_sizePar.setHidden(True)
        self.size_par.setHidden(True)
        self.label_size_symbolMax.setHidden(True)
        self.label_size_symbolMin.setHidden(True)
        self.size_symbolMax.setHidden(True)
        self.size_symbolMin.setHidden(True)
            
    def displaySizeWidgets(self):
        self.rbtn_sizeVar.setHidden(False)
        self.size_var.setHidden(False)
        self.size_function.setHidden(False)
        self.rbtn_sizePar.setHidden(False)
        self.size_par.setHidden(False)
        self.label_size_symbolMax.setHidden(False)
        self.label_size_symbolMin.setHidden(False)
        self.size_symbolMax.setHidden(False)
        self.size_symbolMin.setHidden(False)
            
    def hideRotationLayout(self):
        self.checkbox_varRotation.setHidden(True)
        self.hideRotationWidgets()

    def hideSizeLayout(self):
        self.checkbox_varSize.setHidden(True)
        self.checkbox_varSize.setChecked(False)
        self.hideSizeWidgets()

    def displayRotationLayout(self):
        self.checkbox_varRotation.setHidden(False)
        if self.checkbox_varRotation.isChecked():
            self.displayRotationWidgets()
    
    def displaySizeLayout(self):
        self.checkbox_varSize.setHidden(False)
        if self.checkbox_varSize.isChecked():
            self.displaySizeWidgets()
        
    def color_function_Changed(self,s):
        if s in self.time_values:
            if self.size_function.currentText() in self.time_values:
                self.size_function.setCurrentText(s) 
            if self.rotation_function.currentText() in self.time_values:
                self.rotation_function.setCurrentText(s) 
    
    def size_function_Changed(self,s):
        if s in self.time_values:
            if self.color_function.currentText() in self.time_values:
                self.color_function.setCurrentText(s) 
            if self.rotation_function.currentText() in self.time_values:
                self.rotation_function.setCurrentText(s) 
            
    def rotation_function_Changed(self,s):
        if s in self.time_values:
            if self.size_function.currentText() in self.time_values:
                self.size_function.setCurrentText(s) 
            if self.color_function.currentText() in self.time_values:
                self.color_function.setCurrentText(s) 
        
    def color_varChanged(self,s):
        self.color_function.clear()
        self.color_function.addItems(self.function_items)
        if s.split('$')[0]=='p':
            self.color_function.addItem('specific dp')
                
        if s.split('$')[0]=='mdot' and self.rbtn_lines.isChecked():
            self.hideSizeLayout()
        else:
            self.displaySizeLayout()
            
        self.color_table_name=self.feature+'_'+self.type+'_'+s
        sql="""SELECT min(time), max(time) FROM "{}".{};""".format(self.config['versionName'],self.color_table_name)
        try:
            self.cur.execute(sql)
            time=self.cur.fetchone()
            try:
                current_min_time=getDatetimeFromString(self.label_starttime.text().split('min value=')[1][:-1])
                current_max_time=getDatetimeFromString(self.label_endtime.text().split('max value=')[1][:-1])
                if current_min_time>time['min']:
                    self.label_starttime.setText('Start time, h (min value='+str(time['min'])+')')
                    self.starttime.setText(str(time['min']))
                if current_max_time<time['min']:
                    self.label_endtime.setText('End time, h (max value='+str(time['max'])+')')
                    self.endtime.setText(str(time['max']))
            except:
                self.label_starttime.setText('Start time, h (min value='+str(time['min'])+')')
                self.starttime.setText(str(time['min']))
                self.label_endtime.setText('End time, h (max value='+str(time['max'])+')')
                self.endtime.setText(str(time['max']))
        except:
            self.label_starttime.setText('Start time, h')
            self.label_endtime.setText('End time, h')
            
    def size_varChanged(self,s):
        self.size_table_name=self.feature+'_'+self.type+'_'+s
        sql="""SELECT min(time), max(time) FROM "{}".{};""".format(self.config['versionName'],self.size_table_name)
        try:
            self.cur.execute(sql)
            time=self.cur.fetchone()
            try:
                current_min_time=getDatetimeFromString(self.label_starttime.text().split('min value=')[1][:-1])
                current_max_time=getDatetimeFromString(self.label_endtime.text().split('max value=')[1][:-1])
                if current_min_time>time['min']:
                    self.label_starttime.setText('Start time, h (min value='+str(time['min'])+')')
                    self.starttime.setText(str(time['min']))
                if current_max_time<time['min']:
                    self.label_endtime.setText('End time, h (max value='+str(time['max'])+')')
                    self.endtime.setText(str(time['max']))
            except:
                self.label_starttime.setText('Start time, h (min value='+str(time['min'])+')')
                self.starttime.setText(str(time['min']))
                self.label_endtime.setText('End time, h (max value='+str(time['max'])+')')
                self.endtime.setText(str(time['max']))
        except:
            self.label_starttime.setText('Start time, h')
            self.label_endtime.setText('End time, h')
            
    def rotation_varChanged(self,s):
        self.rotation_table_name=self.feature+'_'+self.type+'_'+s
        sql="""SELECT min(time), max(time) FROM "{}".{};""".format(self.config['versionName'],self.rotation_table_name)
        try:
            self.cur.execute(sql)
            time=self.cur.fetchone()
            try:
                current_min_time=getDatetimeFromString(self.label_starttime.text().split('min value=')[1][:-1])
                current_max_time=getDatetimeFromString(self.label_endtime.text().split('max value=')[1][:-1])
                if current_min_time>time['min']:
                    self.label_starttime.setText('Start time, h (min value='+str(time['min'])+')')
                    self.starttime.setText(str(time['min']))
                if current_max_time<time['min']:
                    self.label_endtime.setText('End time, h (max value='+str(time['max'])+')')
                    self.endtime.setText(str(time['max']))
            except:
                self.label_starttime.setText('Start time, h (min value='+str(time['min'])+')')
                self.starttime.setText(str(time['min']))
                self.label_endtime.setText('End time, h (max value='+str(time['max'])+')')
                self.endtime.setText(str(time['max']))
        except:
            self.label_starttime.setText('Start time, h')
            self.label_endtime.setText('End time, h')

    def dataGroupChanged(self,radioButto):
        self.featureGroupChanged(False)

    def featureGroupChanged(self,radioButto):
        self.color_var.clear()
        self.color_par.clear()
        self.size_var.clear()
        self.size_par.clear()
        self.rotation_var.clear()
        self.rotation_par.clear()
        if self.rbtn_mDatap.isChecked():
            #print('Measurement data')
            self.type='m'
        elif self.rbtn_simData.isChecked():
            self.type='s'
        if self.rbtn_customers.isChecked():
            #print('Customers')
            self.feature='customer'
            vars=getResultVars(self.cur,self.config,self.feature,self.type)
            pars=getTableAttr(self.cur,self.config,self.feature)
            #print(vars)
            self.displayRotationLayout()
            self.label_lineSegVis.setHidden(True)
            self.lineSegVis.setHidden(True)
            self.displaySizeLayout()
        elif self.rbtn_plants.isChecked():
            #print('Energy plants')
            self.feature='energy_plant'
            vars=getResultVars(self.cur,self.config,self.feature,self.type)
            pars=getTableAttr(self.cur,self.config,self.feature)
            self.displayRotationLayout()
            self.label_lineSegVis.setHidden(True)
            self.lineSegVis.setHidden(True)
            self.displaySizeLayout()
        elif self.rbtn_lines.isChecked():
            #print('Lines')
            self.feature='line'
            vars=getResultVars(self.cur,self.config,self.feature,self.type)
            pars=getTableAttr(self.cur,self.config,self.feature)
            self.label_lineSegVis.setHidden(False)
            self.lineSegVis.setHidden(False)
            #hide rotation
            self.hideRotationLayout()
            self.checkbox_varRotation.setChecked(False)
            
        self.color_var.addItems(vars)
        self.color_par.addItems(pars)
        self.size_var.addItems(vars)
        self.size_par.addItems(pars)
        self.rotation_var.addItems(vars)
        self.rotation_par.addItems(pars)
        
class IDADistrictsPathReportsDialog(QDialog):
    def __init__(self,cur,config,dlg_main):     
        """Initialize GUI for path reports"""
        super().__init__()
        self.setWindowTitle("Path reports")   
        self.cur=cur
        self.config=config
        self.dlg_main=dlg_main
        self.title=None
        self.lids=None
        self.weak_point=None
        self.path=None
        self.line_data=None

        #set quantity 
        #title
        label_titel =QLabel('Quantity')
        font=label_titel.font()
        font.setPointSize(15)
        label_titel.setFont(font)
        #radio buttons Temp/pressure
        layout_rbtn_quantity = QHBoxLayout()
        group_quantity=QButtonGroup(self)
        self.rbtn_pathTemp = QRadioButton('Temperature')
        self.rbtn_pathPressure = QRadioButton('Pressure')
        self.rbtn_pathPressure.setChecked(True)
           
        layout_rbtn_quantity.addWidget(self.rbtn_pathPressure)  
        layout_rbtn_quantity.addWidget(self.rbtn_pathTemp)
        group_quantity.addButton(self.rbtn_pathTemp)      
        group_quantity.addButton(self.rbtn_pathPressure)      
        
        quantity_info=QLabel('Info: Please select Pressure distribution/temperature in nodes, Substation pressure/Substation connection temperatures and Plant pressure/Plant connection temperatures before simulation in order to generate path reports.')
        
        layout_quantity = QVBoxLayout()
        layout_quantity.addWidget(label_titel)
        layout_quantity.addLayout(layout_rbtn_quantity)
        layout_quantity.addWidget(quantity_info)
        
        #Date 
        #title
        label_titel =QLabel('Date')
        font=label_titel.font()
        font.setPointSize(15)
        label_titel.setFont(font)
        #radio buttons Date/Max value
        layout_rbtn_date = QHBoxLayout()
        self.rbtn_maxValue = QRadioButton('Max value')
        self.rbtn_maxValue.setChecked(True)
        self.rbtn_Date = QRadioButton('Date (yyyy-MM-dd HH:mm:ss)')
           
        layout_rbtn_date.addWidget(self.rbtn_maxValue)
        layout_rbtn_date.addWidget(self.rbtn_Date) 
        group_date=QButtonGroup(self)
        group_date.addButton(self.rbtn_maxValue)      
        group_date.addButton(self.rbtn_Date)  

        self.date_input = QLineEdit()

        layout_date = QVBoxLayout()
        layout_date.addWidget(label_titel)
        layout_date.addLayout(layout_rbtn_date)        
        layout_date.addWidget(self.date_input)        
        
        #Path 
        #title
        label_titel =QLabel('Path')
        font=label_titel.font()
        font.setPointSize(15)
        label_titel.setFont(font)
        #radio buttons Line ID/Weak point
        layout_rbtn_path = QHBoxLayout()
        self.rbtn_weakPoint = QRadioButton('Weak point (customers)')
        self.rbtn_weakPoint.setChecked(True)
        self.rbtn_lineIds = QRadioButton('Line ID`s')
        self.rbtn_customer = QRadioButton('Customer ID`s')
        self.rbtn_energy_plant = QRadioButton('Energy plant ID`s')
           
        layout_rbtn_path.addWidget(self.rbtn_weakPoint) 
        layout_rbtn_path.addWidget(self.rbtn_lineIds)
        layout_rbtn_path.addWidget(self.rbtn_customer) 
        layout_rbtn_path.addWidget(self.rbtn_energy_plant) 
        self.group_path=QButtonGroup(self)
        self.group_path.addButton(self.rbtn_weakPoint,1)  
        self.group_path.addButton(self.rbtn_lineIds,2)      
        self.group_path.addButton(self.rbtn_customer,3)  
        self.group_path.addButton(self.rbtn_energy_plant,4)  
        #self.group_path.buttonClicked[int].connect(self.on_group_path_clicked)
        self.group_path.buttonClicked.connect(self.on_group_path_clicked)
        
        
        self.listWidget_ids= QListWidget()
        self.listWidget_ids.setSelectionMode(QtWidgets.QAbstractItemView.SelectionMode.ExtendedSelection)
        
        layout_network_settings=QHBoxLayout()
        #labels
        layout_network_settings_labels=QVBoxLayout()
        label_network =QLabel('Network')
        layout_network_settings_labels.addWidget(label_network)
        label_main_plant =QLabel('Plant')
        layout_network_settings_labels.addWidget(label_main_plant)
        label_conntype =QLabel('Connection type')
        layout_network_settings_labels.addWidget(label_conntype)
        label_sup_sequences =QLabel('Supply sequence')
        layout_network_settings_labels.addWidget(label_sup_sequences)
        label_ret_sequences =QLabel('Return sequence')
        layout_network_settings_labels.addWidget(label_ret_sequences)
        label_conntype =QLabel('Feature connection bundle type')
        layout_network_settings_labels.addWidget(label_conntype)
        label_conntype =QLabel('Feature connection type')
        layout_network_settings_labels.addWidget(label_conntype)
        self.dp_recalc =QCheckBox('Recalculate supply pressure value with dp min, bar')
        layout_network_settings_labels.addWidget(self.dp_recalc)
        
        #input
        layout_network_settings_values=QVBoxLayout()
        self.network = QComboBox()
        self.network.currentTextChanged.connect(self.network_changed)
        layout_network_settings_values.addWidget(self.network)
        self.main_plant = QComboBox()
        self.main_plant.currentTextChanged.connect(self.main_plant_changed)
        layout_network_settings_values.addWidget(self.main_plant)
        self.conn_type = QComboBox()
        self.conn_type.currentTextChanged.connect(self.conn_type_changed)
        layout_network_settings_values.addWidget(self.conn_type)
        self.sup_sequence =QComboBox()
        layout_network_settings_values.addWidget(self.sup_sequence)
        self.ret_sequence =QComboBox()
        layout_network_settings_values.addWidget(self.ret_sequence)
        self.f_conn_bundle_type = QComboBox()
        layout_network_settings_values.addWidget(self.f_conn_bundle_type)
        self.f_conn_bundle_type.currentTextChanged.connect(self.f_conn_bundle_type_changed)
        self.f_conn_type = QComboBox()
        layout_network_settings_values.addWidget(self.f_conn_type)
        self.dp_min_recalc = QLineEdit()
        layout_network_settings_values.addWidget(self.dp_min_recalc)
        
        layout_network_settings.addLayout(layout_network_settings_labels)
        layout_network_settings.addLayout(layout_network_settings_values)
        
        #buttons
        layout_btn_list = QHBoxLayout()
        self.btn_addID=QPushButton("Add ID")
        self.btn_addSelectedIDs=QPushButton("Add selected ID`s from map")
        self.btn_deleteIDs=QPushButton("Delete ID`s")
        layout_btn_list.addWidget(self.btn_addID)
        layout_btn_list.addWidget(self.btn_addSelectedIDs)
        layout_btn_list.addWidget(self.btn_deleteIDs)
        
        layout_path = QVBoxLayout()
        layout_path.addWidget(label_titel)
        layout_path.addLayout(layout_rbtn_path)  
        layout_path.addWidget(self.listWidget_ids)
        layout_path.addLayout(layout_network_settings)
        layout_path.addLayout(layout_btn_list)

        
        #buttons     
        layout_btn=QHBoxLayout()
        self.btn_ok=QPushButton("Ok")
        self.btn_cancel=QPushButton("Cancel")
        layout_btn.addWidget(self.btn_ok)
        layout_btn.addWidget(self.btn_cancel)
        
        #progress bar
        self.progress=QProgressBar()
        
        #---------------set layouts together-------------------
        layout = QVBoxLayout()
        layout.addLayout(layout_quantity)
        layout.addLayout(layout_date)      
        layout.addLayout(layout_path)      
        layout.addLayout(layout_btn)
        layout.addWidget(self.progress)
        layout.addStretch()
        
        self.setLayout(layout)
        
        f_conn_types = getConnBundlesByType(self.cur,self.config,'customer')
        self.f_conn_bundle_type.addItems(f_conn_types)

    def add_combo_items(self, combo, new_items):
        #print('add combo:'+str(new_items))

        # Add missing items
        for item in new_items:
            if combo.findText(item) == -1:
                combo.addItem(item)
 
    #def on_group_path_clicked(self,id):
    def on_group_path_clicked(self,button):
        id = self.group_path.id(button)
        #print('on_group_path_clicked: '+str(id))
        
        self.f_conn_bundle_type.clear()
        f_conn_types = getConnBundlesByType(self.cur,self.config,'customer' if id in (1,2,3) else 'energy_plant')
        self.add_combo_items(self.f_conn_bundle_type,f_conn_types)
        if id==2:
            f_conn_types = getConnBundlesByType(self.cur,self.config,'energy_plant')
            self.add_combo_items(self.f_conn_bundle_type,f_conn_types)
    
    def f_conn_bundle_type_changed(self,s):
        #print('f_conn_bundle_type changed: '+str(s))
        if self.f_conn_bundle_type.currentText():
            self.f_conn_type.clear() 
            self.f_conn_type.addItems(getConnTypesByConnBundleType(self.cur,self.config,self.f_conn_bundle_type.currentText()))    
        
    def network_changed(self,s):
        #print(s)
        epids=getPlantIds(self.cur,self.config,network=s)
        #print(epids)
        self.main_plant.clear()
        self.main_plant.addItems(epids)

    def main_plant_changed(self,s):
        #print(s)
        conn_types=getConnTypesByFeature(self.cur,self.config,'energy_plant',s)
        #print(conn_types)
        self.conn_type.clear()
        self.conn_type.addItems(conn_types)
        
    def conn_type_changed(self,s):
        #print(s)
        sequences=getConnSequencesByConnType(self.cur,s)
        #print(sequences)
        self.sup_sequence.clear()
        self.sup_sequence.addItems(sequences)
        self.ret_sequence.clear()
        self.ret_sequence.addItems(sequences)
        
    def update_progress(self,progress):
        self.progress.setValue(progress)
        
    def show_error_message(self, message):
        # Show the error message in a messageBar
        iface.messageBar().pushMessage("Error", message, level=Qgis.Critical)
        
    def update_finished(self,message):
        if str(message)=='finished':
            self.showplot()
            #select lids in lines
            lines_layer=QgsProject.instance().mapLayersByName(tr('@default','lines'))   
            if lines_layer:             
                lines_layer[0].selectByExpression("id in {}".format(tuple([lid[0] for lid in self.lids])))
        
        self.dlg_main.statusMessage.setText(message)        
        self.process_running=False
        
    def showplot(self):
        #print('show plot')
        if self.dp_recalc.isChecked() and self.rbtn_pathPressure.isChecked():
            #print(self.dp_min_recalc.text())
            ddp=self.weak_point['sup_f'] - self.weak_point['ret_f']-Decimal(self.dp_min_recalc.text())*100000
        else:
            ddp=0
        #print(ddp)

        #print(self.weak_point)
        #print(self.line_data)
        quantity_data_sup=[self.weak_point['sup_ep']-ddp]+[lid['var1']-ddp for lid in self.line_data]+[self.weak_point['sup_f']-ddp]
        quantity_data_ret=[self.weak_point['ret_ep']]+[lid['var2'] for lid in self.line_data]+[self.weak_point['ret_f']]
        height=[self.weak_point['height_ep']]+[lid['height_j'] for lid in self.line_data]+[self.weak_point['height_f']]

        #print(height)
        #print(quantity_data_sup)
        #print(quantity_data_ret)
        #print(self.path)
        
        SMALL_SIZE = 15
        MEDIUM_SIZE = 20
        BIGGER_SIZE = 25

        plt.rc('font', size=SMALL_SIZE)          # controls default text sizes
        plt.rc('axes', titlesize=SMALL_SIZE)     # fontsize of the axes title
        plt.rc('axes', labelsize=MEDIUM_SIZE)    # fontsize of the x and y labels
        plt.rc('xtick', labelsize=SMALL_SIZE)    # fontsize of the tick labels
        plt.rc('ytick', labelsize=SMALL_SIZE)    # fontsize of the tick labels
        plt.rc('legend', fontsize=SMALL_SIZE)    # legend fontsize
        plt.rc('figure', titlesize=MEDIUM_SIZE)  # fontsize of the figure title
        plt.rc('figure', figsize=(30.0, 20.0))  # fontsize of the figure title
        
        fig, (ax1, ax2) = plt.subplots(2, 1)
        fig.suptitle(self.title)
        ax1.plot(self.path, quantity_data_sup, linewidth=4.0)
        ax1.plot(self.path, quantity_data_ret, linewidth=4.0)
        ax1.grid(True)
        
        #ax1.set_xlabel('Length, m')
        ax1.set_xlabel('Trasse, m')
        if self.rbtn_pathPressure.isChecked():
            #ax1.set_ylabel('Pressure, Pa')
            ax1.set_ylabel('Druck, Pa')
        else:
            #ax1.set_ylabel('Temperature, °C')
            ax1.set_ylabel('Temperatur, °C')
            
        ax2.plot(self.path, height,linewidth=3.0)    
        #ax2.set_xlabel('Length, m')
        ax2.set_xlabel('Trasse, m')
        #ax2.set_ylabel('Height level, m')
        ax2.set_ylabel('Höhenprofil, m')
        ax2.grid(True)
        
        manager = plt.get_current_fig_manager()
        manager.window.showMaximized()
        plt.show() 
        
class LoadResultsDialog(QDialog):
    def __init__(self,dlg_main):
        """Constructor."""
        super().__init__()
        self.setWindowTitle("Load simulation results") 
        self.dlg_main=dlg_main
        self.process_running=False
        
        #submodels
        layout_submodels=QVBoxLayout()
        label_submodels =QLabel("Submodels")
        font=label_submodels.font()
        font.setPointSize(12)
        label_submodels.setFont(font)
        self.combo_submodels = CheckableComboBox()
        layout_submodels.addWidget(label_submodels)
        layout_submodels.addWidget(self.combo_submodels)
        
        #interpolate timestep
        layout_interpolation=QVBoxLayout()
        self.checkbox_timestep=QCheckBox('data interpolation, s')
        self.checkbox_timestep.stateChanged.connect(self.interpolation_dt_state)
        layout_interpolation.addWidget(self.checkbox_timestep)
        self.interpolation_dt=QLineEdit('')
        self.interpolation_dt.setHidden(True)
        layout_interpolation.addWidget(self.interpolation_dt)
        
        #buttons     
        layout_buttons = QHBoxLayout()
        self.btn_loadResults=QPushButton("Load results")
        layout_buttons.addWidget(self.btn_loadResults)
        self.btn_cancel=QPushButton("Cancel")
        layout_buttons.addWidget(self.btn_cancel)
        
        #progress bar
        self.progress=QProgressBar()
        
        #---------------set layouts together-------------------
        layout_win = QVBoxLayout()
        layout_win.addLayout(layout_submodels)
        layout_win.addLayout(layout_interpolation)
        layout_win.addLayout(layout_buttons)
        layout_win.addWidget(self.progress)
        
        self.setLayout(layout_win)
        
    def interpolation_dt_state(self,s):
        if checkState()==s:
            self.interpolation_dt.setHidden(False)
        else:
            self.interpolation_dt.setHidden(True)
    
    def update_progress(self,progress):
        self.progress.setValue(progress)

    def update_finished(self,message):
        self.process_running=False
        self.dlg_main.statusMessage.setText(message)