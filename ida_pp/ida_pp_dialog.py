""" This file contains the dialog code for IDA Districts Preprocessing"""

from plugins.utility_functions.db import *
from plugins.utility_functions.topology import *
from plugins.utility_functions.dialog import *
from plugins.utility_functions.error_handling import *
from plugins.utility_functions.layer_visualization import *
from .PipeLayingAlgorithm import WorkerPipeLaying 
from .pipe_sizing import * 
from .GenerateNetworkTopology import WorkerGenerateNetworkTopology 
from qgis.PyQt.QtCore import Qt, QThreadPool
from qgis.PyQt.QtWidgets import QSpacerItem,QSizePolicy,QGroupBox,QMessageBox,QButtonGroup, QInputDialog, QTableWidgetItem,QTableWidget, QTreeView,QAction,QMainWindow,QWidget,QPushButton,QHBoxLayout,QVBoxLayout,QLabel,QLineEdit,QComboBox, QProgressBar, QComboBox, QCheckBox, QRadioButton, QListWidget
import psycopg2
import psycopg2.extras
from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT  
from qgis.core import QgsProject, QgsMessageLog, QgsVectorLayer, QgsWkbTypes
from qgis.utils import iface 
from PyQt5 import QtGui, QtCore


def checkPipeLayingLayerData(dictDB,cur,network):   
    if featureCount(cur,dictDB,network,'customer')==0:
        return 'no_customers'
    if featureCount(cur,dictDB,network,'energy_plant')==0:
        return 'no_plants'
    if streetsCount(cur,dictDB)==0:
        return 'no_streets'
    #check intersecting features
    if checkIntersectingFeatures(cur,dictDB):
        return True
    return False
        
def removeLayers():
    layers = QgsProject.instance().mapLayers().values()
    for layer in layers:
        if layer.name() in ['customers_temp','lines_temp','lines_heating_temp','lines_cooling_temp','junctions_temp','energy_plants_temp']:
            QgsProject.instance().removeMapLayer(layer)

class ImportGeoDataDlg(QMainWindow):
    def __init__(self,title='',default_path=''):        
        super().__init__()
        self.setWindowTitle(title) 
        self.process_running=False
               
        #file path
        layout_file = QHBoxLayout()      
        
        self.lineEditFileName =QLineEdit(default_path)
        layout_file.addWidget(self.lineEditFileName)
        
        self.btn_fileDialog=QPushButton("...")
        layout_file.addWidget(self.btn_fileDialog)
        
        
        #checkbox for drop old features
        self.checkBoxClearOldFeatures=QCheckBox("drop old features")
        
        #buttons     
        layout_btn=QHBoxLayout()
        self.btn_import=QPushButton("Import")
        self.btn_cancel=QPushButton("Cancel")
        layout_btn.addWidget(self.btn_import)
        layout_btn.addWidget(self.btn_cancel)
        
        #progress bar
        self.progress=QProgressBar()
        
        layout_win = QVBoxLayout()
        layout_win.addLayout(layout_file)
        layout_win.addWidget(self.checkBoxClearOldFeatures)
        layout_win.addLayout(layout_btn)
        layout_win.addWidget(self.progress)

        widget=QWidget()
        widget.setLayout(layout_win)
        self.setCentralWidget(widget)
        
    def update_progress(self,progress):
        self.progress.setValue(progress)

    def update_finished(self,message):
        self.process_running=False
        
class IdaDistrictsPreProcessingDialog(QMainWindow):
    def __init__(self,plugins_dir):
        """Constructor."""
        super().__init__()
        self.setWindowTitle("IDA Districts Preprocessing")     
        
        #-------------Data import---------------
        #titel
        label_import_title =QLabel("Data import")
        font=label_import_title.font()
        font.setPointSize(15)
        label_import_title.setFont(font)
                
        #import buttons
        layout_data_btn_import = QVBoxLayout()      
        
        self.btn_importStreetsFromOSM=QPushButton("Streets")
        layout_data_btn_import.addWidget(self.btn_importStreetsFromOSM)
        
        self.btn_importBuildingsFromOSM=QPushButton("Buildings")
        layout_data_btn_import.addWidget(self.btn_importBuildingsFromOSM)
        
        self.btn_importElevationData=QPushButton("Elevation data")
        layout_data_btn_import.addWidget(self.btn_importElevationData)
        
             
        #set data import layout together
        layout_import = QVBoxLayout()
        layout_import.addWidget(label_import_title)
        layout_import.addLayout(layout_data_btn_import)
        
        #---------------Network topology---------------
        #titel
        label_topology_title =QLabel("Network topology")
        label_topology_title.setFont(font)
        
        #buttons
        layout_topology_buttons = QVBoxLayout()
        
        self.btn_importPointLayer=QPushButton("Import plant or customer from layer")
        layout_topology_buttons.addWidget(self.btn_importPointLayer)
        
        self.btn_importNetworkTopologyFromLayer=QPushButton("Import network topology from layer")
        layout_topology_buttons.addWidget(self.btn_importNetworkTopologyFromLayer)

        self.btn_pipeLayingAlgorithm=QPushButton("Pipe laying algorithm")
        layout_topology_buttons.addWidget(self.btn_pipeLayingAlgorithm)
        
        self.btn_generateTopology=QPushButton("Generate Topology")
        layout_topology_buttons.addWidget(self.btn_generateTopology)
        
        #set network topology layout together
        layout_topology = QVBoxLayout()
        layout_topology.addWidget(label_topology_title)
        layout_topology.addLayout(layout_topology_buttons)
        
        #---------------Sizing---------------
        #titel
        label_sizing_title =QLabel("Sizing")
        label_sizing_title.setFont(font)
        
        #buttons
        layout_sizing_buttons = QVBoxLayout()
        
        self.btn_pipeSizing=QPushButton("Pipe sizing")
        layout_sizing_buttons.addWidget(self.btn_pipeSizing)
        
        #set sizing layout together
        layout_sizing = QVBoxLayout()
        layout_sizing.addWidget(label_sizing_title)
        layout_sizing.addLayout(layout_sizing_buttons)
        
        #---------------Sizing---------------
        #titel
        label_mapping_title =QLabel("Mapping")
        label_mapping_title.setFont(font)
        
        #buttons
        layout_mapping_buttons = QVBoxLayout()
        
        self.btn_mapPlants=QPushButton("Map connection types to lines")
        layout_mapping_buttons.addWidget(self.btn_mapPlants)
        
        #set sizing layout together
        layout_mapping = QVBoxLayout()
        layout_mapping.addWidget(label_mapping_title)
        layout_mapping.addLayout(layout_mapping_buttons)
        
        #---------------set layouts together-------------------
        layout_win = QVBoxLayout()
        layout_win.addLayout(layout_import)
        layout_win.addLayout(layout_topology)
        layout_win.addLayout(layout_sizing)
        layout_win.addLayout(layout_mapping)
        
        widget=QWidget()
        widget.setLayout(layout_win)
        self.setCentralWidget(widget)
        
class PipeLayingDialog(QMainWindow):
    def __init__(self,dictDB,plugin_dir,iface):     
        """Initialize GUI for pipe laying algorithm"""
        super().__init__()
        self.iface=iface
        self.plugin_dir=plugin_dir
        self.dictDB=dictDB
        self.conn=dbConnect(self.dictDB,True)
        self.cur=self.conn.cursor(cursor_factory = psycopg2.extras.RealDictCursor)
        self.setWindowTitle("Pipe laying algorithm")      
        columns=getTableAttr(self.cur,self.dictDB,'customer')
        self.process_running=False
        
        #heating network
        self.check_heating_network =QCheckBox("Generate heating network")
        self.check_heating_network.stateChanged.connect(self.heating_network_generation_state)
        
        self.group_box_heating_constr = QGroupBox("Constraints")
        self.group_box_heating_constr.setStyleSheet("""QGroupBox {font-weight: bold;}""")
        
        #connection constraints: maximum supply temperature,
        #constraints for algoritmn: minimum linear heat density,
        
        #checkboxes
        layout_constr_heating_checkbox = QVBoxLayout()
        self.checkbox_tsup_max =QCheckBox("Maximum supply temperature, °C")
        layout_constr_heating_checkbox.addWidget(self.checkbox_tsup_max)                   
               
        self.checkbox_linearHeatDensity_min =QCheckBox("Minimum linear heat density, kWh/m trench/a")
        layout_constr_heating_checkbox.addWidget(self.checkbox_linearHeatDensity_min)

        self.checkbox_heat_demand_min =QCheckBox("Minimum heat demand, kWh/a")
        layout_constr_heating_checkbox.addWidget(self.checkbox_heat_demand_min)
        
        self.checkbox_heating_load_min =QCheckBox("Minimum heating load, kW")
        layout_constr_heating_checkbox.addWidget(self.checkbox_heating_load_min)
        
        #values
        layout_constr_heating_input = QVBoxLayout()
        self.tsup_max =QLineEdit("100")
        layout_constr_heating_input.addWidget(self.tsup_max)
        
        self.linearHeatDensity_min =QLineEdit("0")
        layout_constr_heating_input.addWidget(self.linearHeatDensity_min)    

        self.heat_demand_min =QLineEdit("0")
        layout_constr_heating_input.addWidget(self.heat_demand_min)    

        self.heating_load_min =QLineEdit("0")
        layout_constr_heating_input.addWidget(self.heating_load_min)    

        #column
        layout_constr_heating_col = QVBoxLayout()
        self.tsup_max_col =QComboBox()
        self.tsup_max_col.addItems(columns)
        layout_constr_heating_col.addWidget(self.tsup_max_col)
        
        self.linearHeatDensity_min_col =QComboBox()
        self.linearHeatDensity_min_col.addItems(columns)
        layout_constr_heating_col.addWidget(self.linearHeatDensity_min_col)    

        self.heat_demand_min_col =QComboBox()
        self.heat_demand_min_col.addItems(columns)
        layout_constr_heating_col.addWidget(self.heat_demand_min_col)    

        self.heating_load_min_col =QComboBox()
        self.heating_load_min_col.addItems(columns)
        layout_constr_heating_col.addWidget(self.heating_load_min_col)    

        #Heating type seetings
        self.group_box_heating_type_settings = QGroupBox("Type settings")
        self.group_box_heating_type_settings.setStyleSheet("""QGroupBox {font-weight: bold;}""") 

        #labels
        layout_settings_heating_label = QVBoxLayout()
        self.label_heating_template_customer =QLabel("Customer template")
        layout_settings_heating_label.addWidget(self.label_heating_template_customer)
        
        self.label_heating_type_lines =QLabel("Lines type")
        layout_settings_heating_label.addWidget(self.label_heating_type_lines)
                
        self.label_heating_pipe_bundle =QLabel("Pipe bundle")
        layout_settings_heating_label.addWidget(self.label_heating_pipe_bundle)    
        
        #values
        layout_settings_heating_input = QVBoxLayout()
        self.heating_template_customer =QComboBox()
        try:
            templates=getTemplatesInfo('customer',self.cur)
        except:
            templates=[]
        self.heating_template_customer.addItems(['keep type']+[i['name'] for i in templates])
        self.heating_template_customer.setCurrentText('keep type')
        self.heating_template_customer.setStyleSheet("padding-left: 30")
        layout_settings_heating_input.addWidget(self.heating_template_customer)  

        self.heating_type_lines =QComboBox()
        templates=getTemplatesInfo('line',self.cur)
        self.heating_type_lines.addItems([i['name'] for i in templates])
        if templates:
            self.heating_type_lines.setCurrentText(templates[0]['name'])
        self.heating_type_lines.setStyleSheet("padding-left: 30")
        layout_settings_heating_input.addWidget(self.heating_type_lines)  


        self.heating_pipe_bundle =QComboBox()
        pipe_bundles=getPipeBundleNames(self.cur)
        self.heating_pipe_bundle.addItems([str(i) for i in pipe_bundles])
        if pipe_bundles:
            self.heating_pipe_bundle.setCurrentText(str(list(pipe_bundles)[0]))
        self.heating_pipe_bundle.setStyleSheet("padding-left: 30")
        layout_settings_heating_input.addWidget(self.heating_pipe_bundle)           
        
        
        #costs
        self.group_box_heating_costs = QGroupBox("")
        #labels
        self.check_heating_network_costs =QCheckBox("consider trench and pipe costs")
        self.check_heating_network_costs.stateChanged.connect(self.heating_network_costs_state)
        self.check_heating_network_costs.setHidden(True)
        
        layout_constr_heating_costs_label = QVBoxLayout()
        layout_constr_heating_costs_label.setContentsMargins(30, 0, 0, 0)  # (left, top, right, bottom) 
        self.label_heat_loss =QLabel("Heat loss, kWh/m trench/a")
        layout_constr_heating_costs_label.addWidget(self.label_heat_loss) 
        
        self.label_heat_costs =QLabel("Heat costs, €/kWh")
        layout_constr_heating_costs_label.addWidget(self.label_heat_costs) 

        self.label_amortization_period_heat =QLabel("Amortization period, a")
        layout_constr_heating_costs_label.addWidget(self.label_amortization_period_heat) 
        
        #values
        layout_constr_heating_costs_input = QVBoxLayout()
                
        self.heat_loss = QLineEdit("100")
        layout_constr_heating_costs_input.addWidget(self.heat_loss) 
        
        self.heat_costs = QLineEdit("0.1")
        layout_constr_heating_costs_input.addWidget(self.heat_costs) 
        
        self.amortization_period_heat = QLineEdit("30")
        layout_constr_heating_costs_input.addWidget(self.amortization_period_heat) 
        
        #cooling network
        #connection constraints: minimum supply temperature,
        #constraints for algoritmn: minimum linear cold density,
        self.check_cooling_network =QCheckBox("Generate cooling network")
        self.check_cooling_network.stateChanged.connect(self.cooling_network_generation_state)
        
        self.group_box_cooling_constr = QGroupBox("Constraints")
        self.group_box_cooling_constr.setStyleSheet("""QGroupBox {font-weight: bold;}""")
  
        #checkbox
        layout_constr_cooling_checkbox = QVBoxLayout()
        self.checkbox_tsup_min =QCheckBox("Minimum supply temperature, °C")
        layout_constr_cooling_checkbox.addWidget(self.checkbox_tsup_min)                   
               
        self.checkbox_linearColdDensity_min =QCheckBox("Minimum linear cold density, kWh/m trench/a")
        layout_constr_cooling_checkbox.addWidget(self.checkbox_linearColdDensity_min)

        self.checkbox_cold_demand_min =QCheckBox("Minimum cold demand, kWh/a")
        layout_constr_cooling_checkbox.addWidget(self.checkbox_cold_demand_min)
        
        self.checkbox_cooling_load_min =QCheckBox("Minimum cooling load, kW")
        layout_constr_cooling_checkbox.addWidget(self.checkbox_cooling_load_min)
        
        #values
        layout_constr_cooling_input = QVBoxLayout()
        self.tsup_min =QLineEdit("15")
        layout_constr_cooling_input.addWidget(self.tsup_min)
        
        self.linearColdDensity_min =QLineEdit("0")
        layout_constr_cooling_input.addWidget(self.linearColdDensity_min)    

        self.cold_demand_min =QLineEdit("0")
        layout_constr_cooling_input.addWidget(self.cold_demand_min)    

        self.cooling_load_min =QLineEdit("0")
        layout_constr_cooling_input.addWidget(self.cooling_load_min)    

        #column
        layout_constr_cooling_col = QVBoxLayout()
        self.tsup_min_col =QComboBox()
        self.tsup_min_col.addItems(columns)
        layout_constr_cooling_col.addWidget(self.tsup_min_col)
        
        self.linearColdDensity_min_col =QComboBox()
        self.linearColdDensity_min_col.addItems(columns)
        layout_constr_cooling_col.addWidget(self.linearColdDensity_min_col)    

        self.cold_demand_min_col =QComboBox()
        self.cold_demand_min_col.addItems(columns)
        layout_constr_cooling_col.addWidget(self.cold_demand_min_col)    

        self.cooling_load_min_col =QComboBox()
        self.cooling_load_min_col.addItems(columns)
        layout_constr_cooling_col.addWidget(self.cooling_load_min_col)    

        self.group_box_cooling_type_settings = QGroupBox("Type settings")
        self.group_box_cooling_type_settings.setStyleSheet("""QGroupBox {font-weight: bold;}""")

        #labels
        layout_settings_cooling_label = QVBoxLayout()
        self.label_cooling_template_customer =QLabel("Customer template")
        layout_settings_cooling_label.addWidget(self.label_cooling_template_customer)

        self.label_cooling_type_lines =QLabel("Line type")
        layout_settings_cooling_label.addWidget(self.label_cooling_type_lines)
        
        self.label_cooling_pipe_bundle =QLabel("Pipe bundle")
        layout_settings_cooling_label.addWidget(self.label_cooling_pipe_bundle)    
        
        #values
        layout_settings_cooling_input = QVBoxLayout()
        self.cooling_template_customer =QComboBox()
        try:
            templates=getTemplatesInfo('customer',self.cur)
        except:
            templates=[]
        self.cooling_template_customer.addItems(['keep type']+[i['name'] for i in templates])
        self.cooling_template_customer.setCurrentText('keep type')
        self.cooling_template_customer.setStyleSheet("padding-left: 30")
        layout_settings_cooling_input.addWidget(self.cooling_template_customer)  

        self.cooling_type_lines =QComboBox()
        templates=getTemplatesInfo('line',self.cur)
        self.cooling_type_lines.addItems([i['name'] for i in templates])
        if templates:
            self.cooling_type_lines.setCurrentText(templates[0]['name'])
        self.cooling_type_lines.setStyleSheet("padding-left: 30")
        layout_settings_cooling_input.addWidget(self.cooling_type_lines)  

        self.cooling_pipe_bundle =QComboBox()
        pipe_bundles=getPipeBundleNames(self.cur)
        self.cooling_pipe_bundle.addItems([str(i) for i in pipe_bundles])
        if pipe_bundles:
            self.cooling_pipe_bundle.setCurrentText(str(list(pipe_bundles)[0]))
        self.cooling_pipe_bundle.setStyleSheet("padding-left: 30")
        layout_settings_cooling_input.addWidget(self.cooling_pipe_bundle)           
        
        
        #costs
        self.group_box_cooling_costs = QGroupBox("")
        #labels
        self.check_cooling_network_costs =QCheckBox("consider trench and pipe costs")
        self.check_cooling_network_costs.stateChanged.connect(self.cooling_network_costs_state)
        self.check_cooling_network_costs.setHidden(True)
        
        layout_constr_cooling_costs_label = QVBoxLayout()
        layout_constr_cooling_costs_label.setContentsMargins(30, 0, 0, 0)  # (left, top, right, bottom) 
        self.label_cold_loss =QLabel("Cold loss, kWh/m trench/a")
        layout_constr_cooling_costs_label.addWidget(self.label_cold_loss) 
        
        self.label_cold_costs =QLabel("Cold costs, €/kWh")
        layout_constr_cooling_costs_label.addWidget(self.label_cold_costs) 

        self.label_amortization_period_cold =QLabel("Amortization period, a")
        layout_constr_cooling_costs_label.addWidget(self.label_amortization_period_cold) 
        
        #values
        layout_constr_cooling_costs_input = QVBoxLayout()
                
        self.cold_loss = QLineEdit("100")
        layout_constr_cooling_costs_input.addWidget(self.cold_loss) 
        
        self.cold_costs = QLineEdit("0.1")
        layout_constr_cooling_costs_input.addWidget(self.cold_costs) 
        
        self.amortization_period_cold = QLineEdit("30")
        layout_constr_cooling_costs_input.addWidget(self.amortization_period_cold) 

        #extend network ?
        self.check_extend_network =QCheckBox("Extend an existing network")
        
        #keep unconnected customers?
        self.keep_unconnected_customers =QCheckBox("Keep unconnected customers")
        self.keep_unconnected_customers.setChecked(True)

        #redraw submodel polygon including all streets
        self.redraw_submodels_polygons =QCheckBox("Redraw submodel polygon including all features and lines")
        self.redraw_submodels_polygons.setChecked(True)
        
        #customer connection mode
        self.customer_connection_mode=QComboBox()
        #self.customer_connection_mode.addItems(['shortest-way-connection','loop-in-connection'])
        self.customer_connection_mode.addItems(['shortest-way-connection'])
        
        #tolerance
        layout_tolerance=QHBoxLayout()
        label=QLabel('Snapping tolerance, m: ')
        layout_tolerance.addWidget(label)
        self.tolerance=QLineEdit('0.01')
        layout_tolerance.addWidget(self.tolerance)
        
        #networks
        layout_networks=QHBoxLayout()
        label_network =QLabel("Network")
        networks=getNetworks(self.cur,self.dictDB)
        print(networks)
        self.combo_network = QComboBox()
        self.combo_network.addItems(networks)
        layout_networks.addWidget(label_network)
        layout_networks.addWidget(self.combo_network)


        #Heating/Cooling type settings
        self.group_box_hc_type_settings = QGroupBox("Type settings for heating and cooling")
        self.group_box_hc_type_settings.setStyleSheet("""QGroupBox {font-weight: bold;}""")

        #labels right
        layout_settings_hc_label = QVBoxLayout()
        self.label_hc_template_customer =QLabel("Customer template")
        layout_settings_hc_label.addWidget(self.label_hc_template_customer)
        
        self.label_type_lines =QLabel("Lines template")
        layout_settings_hc_label.addWidget(self.label_type_lines)
        
        self.label_hc_pipe_bundle =QLabel("Pipe bundle")
        layout_settings_hc_label.addWidget(self.label_hc_pipe_bundle)    
        
        #values right
        layout_settings_hc_input = QVBoxLayout()
        self.hc_template_customer =QComboBox()
        try:
            templates=getTemplatesInfo('customer',self.cur)
        except:
            templates=[]
        self.hc_template_customer.addItems(['keep type']+[i['name'] for i in templates])
        self.hc_template_customer.setCurrentText('keep type')
        self.hc_template_customer.setStyleSheet("padding-left: 30")
        layout_settings_hc_input.addWidget(self.hc_template_customer)  

        self.hc_type_lines =QComboBox()
        templates=getTemplatesInfo('line',self.cur)
        self.hc_type_lines.addItems([i['name'] for i in templates])
        if templates:
            self.hc_type_lines.setCurrentText(templates[0]['name'])
        self.hc_type_lines.setStyleSheet("padding-left: 30")
        layout_settings_hc_input.addWidget(self.hc_type_lines)  

        self.hc_pipe_bundle =QComboBox()
        pipe_bundles=getPipeBundleNames(self.cur)
        self.hc_pipe_bundle.addItems([str(i) for i in pipe_bundles])
        if pipe_bundles:
            self.hc_pipe_bundle.setCurrentText(str(list(pipe_bundles)[0]))
        self.hc_pipe_bundle.setStyleSheet("padding-left: 30")
        layout_settings_hc_input.addWidget(self.hc_pipe_bundle)
        
        #action buttons
        layout_actionButtons = QHBoxLayout()
        
        btn_start=QPushButton("Start")
        btn_start.pressed.connect(self.execute)
        layout_actionButtons.addWidget(btn_start)
        
        self.btn_stop=QPushButton("Stop")
        layout_actionButtons.addWidget(self.btn_stop)
        
        self.btn_pause=QPushButton("Pause/Resume")
        layout_actionButtons.addWidget(self.btn_pause)
        
        #progress bar
        self.progress=QProgressBar()
        
        #save reject buttons
        layout_saveButtons = QHBoxLayout()
        btn_save=QPushButton("Save")
        btn_save.pressed.connect(self.saveResults)
        layout_saveButtons.addWidget(btn_save)
        
        btn_reject=QPushButton("Reject")
        btn_reject.pressed.connect(self.rejectResults)
        layout_saveButtons.addWidget(btn_reject)
        
        #set layouts together
        #heating
        layout_heating=QVBoxLayout()
        layout_heating.setContentsMargins(30, 0, 0, 0)  # (left, top, right, bottom)
        #heating constraints
        layout_constr_heating = QHBoxLayout()
        layout_constr_heating.addLayout(layout_constr_heating_checkbox)
        layout_constr_heating.addLayout(layout_constr_heating_input)   
        layout_constr_heating.addLayout(layout_constr_heating_col)   
        
        self.group_box_heating_constr.setLayout(layout_constr_heating)
        self.group_box_heating_constr.hide()        
        layout_heating.addWidget(self.group_box_heating_constr)

        #heating type settings
        layout_settings_heating = QHBoxLayout()
        layout_settings_heating.addLayout(layout_settings_heating_label)
        layout_settings_heating.addLayout(layout_settings_heating_input)   
        
        
        self.group_box_heating_type_settings.setLayout(layout_settings_heating)
        self.group_box_heating_type_settings.hide()
        layout_heating.addWidget(self.group_box_heating_type_settings)

        layout_constr_heating_costs = QHBoxLayout()
        layout_constr_heating_costs.addLayout(layout_constr_heating_costs_label)
        layout_constr_heating_costs.addLayout(layout_constr_heating_costs_input)     

        layout_heating.addWidget(self.check_heating_network_costs)
 
        self.group_box_heating_costs.setLayout(layout_constr_heating_costs)     
        self.group_box_heating_costs.hide()        
        layout_heating.addWidget(self.group_box_heating_costs)
        
        #cooling
        layout_cooling=QVBoxLayout()
        layout_cooling.setContentsMargins(30, 0, 0, 0)  # (left, top, right, bottom)
        #cooling constraints
        layout_constr_cooling = QHBoxLayout()
        layout_constr_cooling.addLayout(layout_constr_cooling_checkbox)
        layout_constr_cooling.addLayout(layout_constr_cooling_input)   
        layout_constr_cooling.addLayout(layout_constr_cooling_col)   
        
        self.group_box_cooling_constr.setLayout(layout_constr_cooling)
        self.group_box_cooling_constr.hide()        
        layout_cooling.addWidget(self.group_box_cooling_constr)

        #cooling type settings
        layout_settings_cooling = QHBoxLayout() 
        layout_settings_cooling.addLayout(layout_settings_cooling_label)
        layout_settings_cooling.addLayout(layout_settings_cooling_input)   
        
        self.group_box_cooling_type_settings.setLayout(layout_settings_cooling)
        self.group_box_cooling_type_settings.hide()
        layout_cooling.addWidget(self.group_box_cooling_type_settings)

        layout_constr_cooling_costs = QHBoxLayout()
        layout_constr_cooling_costs.addLayout(layout_constr_cooling_costs_label)
        layout_constr_cooling_costs.addLayout(layout_constr_cooling_costs_input)     

        layout_cooling.addWidget(self.check_cooling_network_costs)
 
        self.group_box_cooling_costs.setLayout(layout_constr_cooling_costs)     
        self.group_box_cooling_costs.hide()        
        layout_cooling.addWidget(self.group_box_cooling_costs)
             
        #hc type settings
        layout_settings_hc = QHBoxLayout()
        layout_settings_hc.addLayout(layout_settings_hc_label)
        layout_settings_hc.addLayout(layout_settings_hc_input)   
        
        self.group_box_hc_type_settings.setLayout(layout_settings_hc)
        self.group_box_hc_type_settings.hide()
        
        #main layout
        layout_win = QVBoxLayout()
        layout_win.addWidget(self.check_heating_network)
        layout_win.addLayout(layout_heating)
        layout_win.addWidget(self.check_cooling_network)
        layout_win.addLayout(layout_cooling)
        layout_win.addWidget(self.group_box_hc_type_settings)
        layout_win.addWidget(self.check_extend_network)
        layout_win.addWidget(self.keep_unconnected_customers)
        layout_win.addWidget(self.redraw_submodels_polygons)
        layout_win.addWidget(self.customer_connection_mode)
        layout_win.addLayout(layout_tolerance)
        layout_win.addLayout(layout_networks)
        layout_win.addLayout(layout_actionButtons)
        layout_win.addWidget(self.progress)
        layout_win.addLayout(layout_saveButtons)
        layout_win.addStretch()
        
        widget=QWidget()
        widget.setLayout(layout_win)
        self.setCentralWidget(widget)
        self.threadpool = QThreadPool()
        print("Multithreading with maximum %d threads" % self.threadpool.maxThreadCount())
        
    def heating_type_lines_state_changed(self,text):
        type=text.split(':')[0]
        templates=getTemplatesInfo('line',type,self.cur)
        self.heating_type_lines.clear()
        self.heating_type_lines.addItems([i['name'] for i in templates])
        if templates:
            self.heating_type_lines.setCurrentText(templates[0]['name'])

    def hc_type_lines_state_changed(self,text):
        type=text.split(':')[0]
        templates=getTemplatesInfo('line',type,self.cur)
        self.hc_type_lines.clear()
        self.hc_type_lines.addItems([i['name'] for i in templates])
        if templates:
            self.hc_type_lines.setCurrentText(templates[0]['name'])

    def hc_template_customers_state_changed(self,text):
        try:
            type=text.split(':')[0]
            templates=getTemplatesInfo('customer',type,self.cur)
        except:
            templates=[]
        self.hc_template_customer.clear()
        self.hc_template_customer.addItems(['keep type']+[i['name'] for i in templates])
        self.hc_template_customer.setCurrentText('keep type')

    def cooling_type_lines_state_changed(self,text):
        type=text.split(':')[0]
        templates=getTemplatesInfo('line',type,self.cur)
        self.cooling_type_lines.clear()
        self.cooling_type_lines.addItems([i['name'] for i in templates])
        if templates:
            self.cooling_type_lines.setCurrentText(templates[0]['name'])

    def cooling_template_customers_state_changed(self,text):
        try:
            templates=getTemplatesInfo('customer',self.cur)
        except:
            templates=[]
        self.cooling_template_customer.clear()
        self.cooling_template_customer.addItems(['keep type']+[i['name'] for i in templates])
        self.cooling_template_customer.setCurrentText('keep type')
        
    def execute(self):  
        layerCheck=checkPipeLayingLayerData(self.dictDB,self.cur,self.combo_network.currentText())
        if layerCheck=='no_streets':
            self.iface.messageBar().pushMessage("Error", "Please insert streets into the streets layer.", level=Qgis.Critical)
        elif layerCheck=='no_plants':
            self.iface.messageBar().pushMessage("Error", f"Please insert a main energy plant of network: {self.combo_network.currentText()} into the energy_plants layer.", level=Qgis.Critical)
        elif layerCheck=='no_customers':
            self.iface.messageBar().pushMessage("Error", f"Please insert customers of network: {self.combo_network.currentText()} into the customers layer.", level=Qgis.Critical)
        elif not layerCheck:
            self.process_running=True
            worker = WorkerPipeLaying(tsup_max_col=self.tsup_max_col.currentText(),linearHeatDensity_min_col=self.linearHeatDensity_min_col.currentText(),heat_demand_min_col=self.heat_demand_min_col.currentText(),heating_load_min_col=self.heating_load_min_col.currentText(),
                tsup_min_col=self.tsup_min_col.currentText(),linearColdDensity_min_col=self.linearColdDensity_min_col.currentText(),cold_demand_min_col=self.cold_demand_min_col.currentText(),cooling_load_min_col=self.cooling_load_min_col.currentText(),
                checkbox_tsup_min=self.checkbox_tsup_min.isChecked(),checkbox_linearColdDensity_min=self.checkbox_linearColdDensity_min.isChecked(),checkbox_cold_demand_min=self.checkbox_cold_demand_min.isChecked(),checkbox_cooling_load_min=self.checkbox_cooling_load_min.isChecked(),  
                checkbox_tsup_max=self.checkbox_tsup_max.isChecked(),checkbox_linearHeatDensity_min=self.checkbox_linearHeatDensity_min.isChecked(),checkbox_heat_demand_min=self.checkbox_heat_demand_min.isChecked(),checkbox_heating_load_min=self.checkbox_heating_load_min.isChecked(),  
                tolerance=self.tolerance.text(), network=self.combo_network.currentText(),iface=self.iface, check_heating_network=self.check_heating_network.isChecked(),tsup_max=self.tsup_max.text(),
                heat_demand_min=self.heat_demand_min.text(),heating_load_min=self.heating_load_min.text(),pipe_bundle_heating=self.heating_pipe_bundle.currentText(),
                heating_template_customer=self.heating_template_customer.currentText(),heating_type_lines=self.heating_type_lines.currentText().split(':')[0],
                hc_type_lines=self.hc_type_lines.currentText().split(':')[0],
                linearHeatDensity_min=self.linearHeatDensity_min.text(),check_heating_network_costs=self.check_heating_network_costs.isChecked(),
                heat_loss=self.heat_loss.text(),heat_costs=self.heat_costs.text(),amortization_period_heat=self.amortization_period_heat.text(),
                check_cooling_network=self.check_cooling_network.isChecked(),tsup_min=self.tsup_min.text(),cold_demand_min=self.cold_demand_min.text(),pipe_bundle_cooling=self.cooling_pipe_bundle.currentText(),pipe_bundle_hc=self.hc_pipe_bundle.currentText(),
                cooling_load_min=self.cooling_load_min.text(),cooling_template_customer=self.cooling_template_customer.currentText(),cooling_type_lines=self.cooling_type_lines.currentText(),
                linearColdDensity_min=self.linearColdDensity_min.text(),check_cooling_network_costs=self.check_cooling_network_costs.isChecked(),cold_loss=self.cold_loss.text(),cold_costs=self.cold_costs.text(),
                amortization_period_cold=self.amortization_period_cold.text(),hc_template_customer=self.hc_template_customer.currentText(),
                customer_connection_mode=self.customer_connection_mode.currentText(),keep_unconnected_customers=self.keep_unconnected_customers.isChecked(),redraw_submodels_polygons=self.redraw_submodels_polygons.isChecked(),dictDB=self.dictDB,plugin_dir=self.plugin_dir)
            worker.signals.progress.connect(self.update_progress)
            worker.signals.error.connect(self.show_error_message)       
            worker.signals.finished.connect(self.update_finished)       
            #execute
            self.threadpool.start(worker) 
            self.btn_stop.pressed.connect(worker.kill)
            self.btn_pause.pressed.connect(worker.pauseResume)
        
    def show_error_message(self, message):
        # Show the error message in a messageBar
        self.iface.messageBar().pushMessage("Error", message, level=Qgis.Critical)
        
    def update_progress(self,progress):
        self.progress.setValue(progress)
    
    def update_finished(self,message):
        self.process_running=False
        
    def heating_network_generation_state(self,s):
        print('change heating network generation state')
        print(s)
        if Qt.Checked==s:
            print('checked')
            self.group_box_heating_constr.show()
            self.group_box_heating_type_settings.show()
            self.check_heating_network_costs.setHidden(False)
            if self.check_cooling_network.isChecked():
                self.group_box_hc_type_settings.show()
            if self.check_heating_network_costs.isChecked():
                self.group_box_heating_costs.show()
        else:
            print('unchecked')
            self.group_box_heating_constr.hide()
            self.group_box_heating_type_settings.hide()
            self.group_box_heating_costs.hide()
            self.check_heating_network_costs.setHidden(True)
            self.group_box_hc_type_settings.hide()

    
    def cooling_network_generation_state(self,s):
        print('change cooling network generation state')
        print(s)
        print(Qt.Checked)
        if Qt.Checked==s:
            print('checked')
            self.group_box_cooling_constr.show()
            self.group_box_cooling_type_settings.show()
            self.check_cooling_network_costs.setHidden(False)
            if self.check_heating_network.isChecked():
                self.group_box_hc_type_settings.show()
            if self.check_cooling_network_costs.isChecked():
                self.group_box_cooling_costs.show()
        else:
            print('unchecked')
            self.group_box_cooling_constr.hide()
            self.group_box_cooling_type_settings.hide()
            self.group_box_cooling_costs.hide()
            self.check_cooling_network_costs.setHidden(True)
            self.group_box_hc_type_settings.hide()
            
    def heating_network_costs_state(self,s):
        print('change heating network costs state')
        if Qt.Checked==s:
            print('costs checked')
            self.group_box_heating_costs.show()
        else:
            print('costs unchecked')
            self.group_box_heating_costs.hide()

            
    def cooling_network_costs_state(self,s):
        print('change cooling network costs state')
        if Qt.Checked==s:
            print('costs checked')
            self.group_box_cooling_costs.show()
        else:
            print('costs unchecked')
            self.group_box_cooling_costs.hide()
    
    def saveResults(self):
        """Writes results (lines, customers, junctions) from temp schema to version schema"""
        print('save Results')
        self.conn=dbConnect(self.dictDB,True)
        if self.conn:
            self.cur=self.conn.cursor(cursor_factory = psycopg2.extras.RealDictCursor)
            dropDBTriggers(self.cur,self.dictDB) #child versions are not updated
            sql="""TRUNCATE "{}".lines, "{}".customers, "{}".junctions, "{}".customer_connections, "{}".junction_connections, "{}".energy_plant_connections, "{}".energy_plants CASCADE;\n""".format(self.dictDB['versionName'],self.dictDB['versionName'],self.dictDB['versionName'],self.dictDB['versionName'],self.dictDB['versionName'],self.dictDB['versionName'],self.dictDB['versionName'])
            sql+=""" INSERT INTO "{}".lines SELECT * FROM temp.lines ORDER BY id;\n""".format(self.dictDB['versionName'])
            sql+=""" INSERT INTO "{}".customers SELECT * FROM temp.customers ORDER BY id;\n""".format(self.dictDB['versionName'])
            sql+=""" INSERT INTO "{}".energy_plants SELECT * FROM temp.energy_plants ORDER BY id;\n""".format(self.dictDB['versionName'])
            sql+=""" INSERT INTO "{}".junctions SELECT * FROM temp.junctions ORDER BY id;\n""".format(self.dictDB['versionName'])
            sql+=""" INSERT INTO "{}".junction_connections SELECT * FROM temp.junction_connections ORDER BY id;\n""".format(self.dictDB['versionName']) 
            sql+=""" INSERT INTO "{}".customer_connections SELECT * FROM temp.customer_connections ORDER BY id;\n""".format(self.dictDB['versionName'])  
            sql+=""" INSERT INTO "{}".energy_plant_connections SELECT * FROM temp.energy_plant_connections ORDER BY id;\n""".format(self.dictDB['versionName'])
            print(sql) 
            self.cur.execute(sql)  
            insertDBTriggers(self.cur,self.dictDB)

            removeLayers()
            layerTreeRoot = QgsProject.instance().layerTreeRoot()  
            iface.mapCanvas().snappingUtils().setIndexingStrategy(iface.mapCanvas().snappingUtils().IndexingStrategy.IndexExtent)
            for layer in ['lines','junctions','customers','energy_plants']:
                vlayer= QgsProject.instance().mapLayersByName(layer)[0]
                layerTreeRoot.findLayer(vlayer).setItemVisibilityChecked(True)
                vlayer.emitDataChanged()
            refreshMap()
        
    def rejectResults(self):
        """keep old topology"""
        print('Reject Results')
        removeLayers()
        layerTreeRoot = QgsProject.instance().layerTreeRoot()  
        for layer in ['lines','junctions','customers','energy_plants']:
            if QgsProject.instance().mapLayersByName(layer):
                vlayer= QgsProject.instance().mapLayersByName(layer)[0]
                layerTreeRoot.findLayer(vlayer).setItemVisibilityChecked(True)
            
    def closeEvent(self, *args, **kwargs):
        print("you just closed the PipeLayingWindow!!!")
        self.rejectResults()
        

class NetworkTopologyDialog(QMainWindow):
    def __init__(self,dictDB,plugin_dir,iface):     
        """Initialize GUI for Network generation"""
        super().__init__()
        self.plugin_dir=plugin_dir
        self.dictDB=dictDB
        self.conn=dbConnect(self.dictDB,True)
        self.cur=self.conn.cursor(cursor_factory = psycopg2.extras.RealDictCursor)
        self.iface=iface
        self.setWindowTitle("Generate Topology")
        #todo get values from data center
        customer_templates=getTemplateNames(self.cur,'customer')
        pipeBundleTypes=getPipeBundleNames(self.cur)

        #templates
        self.rbtn_keep_templates = QRadioButton('Keep templates')
        self.rbtn_keep_templates.setChecked(True)
        self.rbtn_override_templates = QRadioButton('Override templates')
        
        self.rbtn_keep_templates.toggled.connect(self.keep_template_state)
        self.rbtn_override_templates.toggled.connect(self.override_template_state)        
        
        #labels
        layout_overrideTemplate_label = QVBoxLayout()
        
        self.label_overrideTemplate_customer =QLabel("Customer template")
        self.label_overrideTemplate_customer.setHidden(True)
        self.label_overrideTemplate_customer.setStyleSheet("padding-left: 30")
        layout_overrideTemplate_label.addWidget(self.label_overrideTemplate_customer)
        
        self.label_overrideTemplate_pipeBundle =QLabel("Pipe bundle type")
        self.label_overrideTemplate_pipeBundle.setHidden(True)
        self.label_overrideTemplate_pipeBundle.setStyleSheet("padding-left: 30")
        layout_overrideTemplate_label.addWidget(self.label_overrideTemplate_pipeBundle)
        
        #values
        layout_overrideTemplate_input = QVBoxLayout() 

        self.overrideTemplate_customer =QComboBox()
        self.overrideTemplate_customer.addItems(customer_templates)
        self.overrideTemplate_customer.setCurrentText(customer_templates[0])
        self.overrideTemplate_customer.setHidden(True)
        self.overrideTemplate_customer.setStyleSheet("padding-left: 30")
        layout_overrideTemplate_input.addWidget(self.overrideTemplate_customer)  
        
        self.overrideTemplate_pipeBundle =QComboBox()
        self.overrideTemplate_pipeBundle.addItems(pipeBundleTypes)
        self.overrideTemplate_pipeBundle.setCurrentText(pipeBundleTypes[0])
        self.overrideTemplate_pipeBundle.setHidden(True)
        self.overrideTemplate_pipeBundle.setStyleSheet("padding-left: 30")
        layout_overrideTemplate_input.addWidget(self.overrideTemplate_pipeBundle) 

        #additional options
        layout_additional_options = QVBoxLayout()
        #delete unconnected network ends
        self.check_del_network_ends =QCheckBox("Delete unconnected network ends")
        
        #add customers unconnected network ends
        self.check_add_customers_network_ends =QCheckBox("Add customers to unconnected network ends")
        self.check_add_customers_network_ends.stateChanged.connect(self.addCustomers_network_ends_state)
        #labels
        layout_addCustomers_template_label = QVBoxLayout()
        
        self.label_addCustomers_template_customers =QLabel("Customer template")
        self.label_addCustomers_template_customers.setHidden(True)
        self.label_addCustomers_template_customers.setStyleSheet("padding-left: 30")
        layout_addCustomers_template_label.addWidget(self.label_addCustomers_template_customers)
        
        #values
        layout_addCustomers_template_input = QVBoxLayout() 

        self.addCustomers_template_customers =QComboBox()
        self.addCustomers_template_customers.addItems(customer_templates)
        self.addCustomers_template_customers.setCurrentText(customer_templates[0])
        self.addCustomers_template_customers.setHidden(True)
        self.addCustomers_template_customers.setStyleSheet("padding-left: 30")
        layout_addCustomers_template_input.addWidget(self.addCustomers_template_customers)  
        
        #connect unconnected customers to network
        self.check_connectCustomers =QCheckBox("Connect unconnected customers to network")
        self.check_connectCustomers.stateChanged.connect(self.connectCustomers_state)
        #labels
        layout_connectCustomers_template_label = QVBoxLayout()
                
        self.label_connectCustomers_template_pipeBundle =QLabel("Pipe bundle type")
        self.label_connectCustomers_template_pipeBundle.setHidden(True)
        self.label_connectCustomers_template_pipeBundle.setStyleSheet("padding-left: 30")
        layout_connectCustomers_template_label.addWidget(self.label_connectCustomers_template_pipeBundle)
        
        #values
        layout_connectCustomers_template_input = QVBoxLayout()

        self.connectCustomers_template_pipeBundle =QComboBox()
        self.connectCustomers_template_pipeBundle.addItems(pipeBundleTypes)
        self.connectCustomers_template_pipeBundle.setCurrentText(pipeBundleTypes[0])
        self.connectCustomers_template_pipeBundle.setHidden(True)
        self.connectCustomers_template_pipeBundle.setStyleSheet("padding-left: 30")
        layout_connectCustomers_template_input.addWidget(self.connectCustomers_template_pipeBundle)          
        
        #connect unconnected plants to network
        self.check_connectPlants =QCheckBox("Connect unconnected plants to network")
        self.check_connectPlants.stateChanged.connect(self.connectPlants_state)
        #labels
        layout_connectPlants_template_label = QVBoxLayout()
        
        self.label_connectPlants_template_pipeBundle =QLabel("Pipe bundle type")
        self.label_connectPlants_template_pipeBundle.setHidden(True)
        self.label_connectPlants_template_pipeBundle.setStyleSheet("padding-left: 30")
        layout_connectPlants_template_label.addWidget(self.label_connectPlants_template_pipeBundle)
        
        #values
        layout_connectPlants_template_input = QVBoxLayout()  

        self.connectPlants_template_pipeBundle =QComboBox()
        self.connectPlants_template_pipeBundle.addItems(pipeBundleTypes)
        self.connectPlants_template_pipeBundle.setCurrentText(pipeBundleTypes[0])
        self.connectPlants_template_pipeBundle.setHidden(True)
        self.connectPlants_template_pipeBundle.setStyleSheet("padding-left: 30")
        layout_connectPlants_template_input.addWidget(self.connectPlants_template_pipeBundle)          

        #delete unconnected customers
        self.check_deleteUnconnectedCustomers =QCheckBox("Delete unconnected customers")
        
        #delete unconnected network lines
        self.check_deleteUnconnectedLines =QCheckBox("Delete unconnected lines")
        
        #redraw submodel polygon including all streets
        self.redraw_submodels_polygons =QCheckBox("Redraw submodel polygon including all features and lines and set submodel to 1")
        self.redraw_submodels_polygons.setChecked(True)
        
        #tolerance
        layout_tolerance=QHBoxLayout()
        label=QLabel('Snapping tolerance, m: ')
        layout_tolerance.addWidget(label)
        self.tolerance=QLineEdit('0.01')
        layout_tolerance.addWidget(self.tolerance)
        
        #checkable combobox networks
        layout_networks=QHBoxLayout()
        layout_networks.addWidget(QLabel("Networks"))
        
        self.combo_network_models = CheckableComboBox()     
        self.combo_network_models.addItem('Check all items')
        networks=getNetworks(self.cur,self.dictDB)
        self.combo_network_models.addItems(networks)  
        for i in range(len(networks)):
            self.combo_network_models.setItemChecked(i+1,False) 
        layout_networks.addWidget(self.combo_network_models)   
        
        #buttons
        layout_buttons = QHBoxLayout()
        
        btn_start=QPushButton("Start")
        btn_start.pressed.connect(self.execute)
        layout_buttons.addWidget(btn_start)
               
        btn_save=QPushButton("Save")
        btn_save.pressed.connect(self.saveResults)
        layout_buttons.addWidget(btn_save)
        
        btn_reject=QPushButton("Reject")
        btn_reject.pressed.connect(self.rejectResults)
        layout_buttons.addWidget(btn_reject)
        
        #progress bar
        self.progress=QProgressBar()
        
        #set layouts together
        layout_overrideTemplate = QHBoxLayout()
        layout_overrideTemplate.addLayout(layout_overrideTemplate_label)
        layout_overrideTemplate.addLayout(layout_overrideTemplate_input)  
        
        layout_addCustomers_template = QHBoxLayout()
        layout_addCustomers_template.addLayout(layout_addCustomers_template_label)
        layout_addCustomers_template.addLayout(layout_addCustomers_template_input) 
        
        layout_connectCustomers_template = QHBoxLayout()
        layout_connectCustomers_template.addLayout(layout_connectCustomers_template_label)
        layout_connectCustomers_template.addLayout(layout_connectCustomers_template_input) 
        
        layout_connectPlants_template = QHBoxLayout()
        layout_connectPlants_template.addLayout(layout_connectPlants_template_label)
        layout_connectPlants_template.addLayout(layout_connectPlants_template_input) 
        
        layout_additional_options.addWidget(self.check_del_network_ends)
        layout_additional_options.addWidget(self.check_add_customers_network_ends)
        layout_additional_options.addLayout(layout_addCustomers_template)
        layout_additional_options.addWidget(self.check_connectPlants)
        layout_additional_options.addLayout(layout_connectPlants_template)
        layout_additional_options.addWidget(self.check_connectCustomers)
        layout_additional_options.addLayout(layout_connectCustomers_template)
        layout_additional_options.addWidget(self.check_deleteUnconnectedCustomers)
        layout_additional_options.addWidget(self.check_deleteUnconnectedLines)
        layout_additional_options.addWidget(self.redraw_submodels_polygons)
        
        layout_win = QVBoxLayout()
        layout_win.addWidget(self.rbtn_keep_templates)
        layout_win.addWidget(self.rbtn_override_templates)
        layout_win.addLayout(layout_overrideTemplate)
        layout_win.addLayout(layout_additional_options)
        layout_win.addLayout(layout_tolerance)
        layout_win.addLayout(layout_networks)
        layout_win.addWidget(self.progress)
        layout_win.addLayout(layout_buttons)
        layout_win.addStretch()
        
        widget=QWidget()
        widget.setLayout(layout_win)
        self.setCentralWidget(widget)
        self.threadpool = QThreadPool()
        print("Multithreading with maximum %d threads" % self.threadpool.maxThreadCount())

    def show_error_message(self, message):
        # Show the error message in a messageBar
        self.iface.messageBar().pushMessage("Error", message, level=Qgis.Critical)
        
    def execute(self):  
        self.conn=dbConnect(self.dictDB,True)
        if self.conn:
            self.cur=self.conn.cursor(cursor_factory = psycopg2.extras.RealDictCursor)
            networks=[self.combo_network_models.itemText(i) for i in range(self.combo_network_models.count()) if self.combo_network_models.itemText(i) != 'Check all items' and self.combo_network_models.itemChecked(i)]
            if checkNetwork(self.cur,self.dictDB['versionName'],networks):
                self.process_running=True
                worker = WorkerGenerateNetworkTopology(iface=self.iface,dictDB=self.dictDB,plugin_dir=self.plugin_dir, networks=networks ,redraw_submodels_polygons=self.redraw_submodels_polygons, deleteUnconnectedCustomers=self.check_deleteUnconnectedCustomers.isChecked(), deleteUnconnectedLines=self.check_deleteUnconnectedLines.isChecked(),
                    connectCustomers=self.check_connectCustomers.isChecked(),connectCustomers_template_pipeBundle=self.connectCustomers_template_pipeBundle.currentText(),
                    addCustomers=self.check_add_customers_network_ends.isChecked(),addCustomers_template_customers=self.addCustomers_template_customers.currentText(),
                    connectPlants=self.check_connectPlants.isChecked(),connectPlants_template_pipeBundle=self.connectPlants_template_pipeBundle.currentText(),
                    deleteUnconnectedNetworkEnds=self.check_del_network_ends.isChecked(),
                    keepTemplates=self.rbtn_keep_templates.isChecked(),
                    overrideTemplates=self.rbtn_override_templates.isChecked(),overrideTemplates_customers=self.overrideTemplate_customer.currentText(),overrideTemplates_pipeBundle=self.overrideTemplate_pipeBundle.currentText(),tolerance=self.tolerance.text(),
                    showTempTables=True)
                worker.signals.error.connect(self.show_error_message)
                worker.signals.progress.connect(self.update_progress)
                worker.signals.finished.connect(self.update_finished)
                self.threadpool.start(worker)  
                
    def update_progress(self,progress):
        self.progress.setValue(progress)

    def update_finished(self,message):
        self.process_running=False
        
    def addCustomers_network_ends_state(self,s):
        print('add customers to network ends state')
        
        if Qt.Checked==s:
            print('checked')
            self.label_addCustomers_template_customers.setHidden(False)
            self.addCustomers_template_customers.setHidden(False)
        else:
            print('unchecked')
            self.label_addCustomers_template_customers.setHidden(True)
            self.addCustomers_template_customers.setHidden(True)
            
    def connectCustomers_state(self,s):
        print('connect customers to network state')
        
        if Qt.Checked==s:
            print('checked')
            self.label_connectCustomers_template_pipeBundle.setHidden(False)
            self.connectCustomers_template_pipeBundle.setHidden(False)
        else:
            print('unchecked')
            self.label_connectCustomers_template_pipeBundle.setHidden(True)
            self.connectCustomers_template_pipeBundle.setHidden(True)
            
    def connectPlants_state(self,s):
        print('connect plants to network state')
        
        if Qt.Checked==s:
            print('checked')
            self.label_connectPlants_template_pipeBundle.setHidden(False)
            self.connectPlants_template_pipeBundle.setHidden(False)
        else:
            print('unchecked')
            self.label_connectPlants_template_pipeBundle.setHidden(True)
            self.connectPlants_template_pipeBundle.setHidden(True)
            
    def override_template_state(self,s):
        print('override template state')
        if True==s:
            print('checked')
            self.label_overrideTemplate_customer.setHidden(False)
            self.label_overrideTemplate_pipeBundle.setHidden(False)
            self.overrideTemplate_customer.setHidden(False)
            self.overrideTemplate_pipeBundle.setHidden(False)
        else:
            print('unchecked')
            self.label_overrideTemplate_customer.setHidden(True)
            self.label_overrideTemplate_pipeBundle.setHidden(True)
            self.overrideTemplate_customer.setHidden(True)
            self.overrideTemplate_pipeBundle.setHidden(True)
       
    def keep_template_state(self,s):
        print('keep template state')
        if True==s:
            print('checked')
            self.label_overrideTemplate_customer.setHidden(True)
            self.label_overrideTemplate_pipeBundle.setHidden(True)
            self.overrideTemplate_customer.setHidden(True)
            self.overrideTemplate_pipeBundle.setHidden(True)
        else:
            print('unchecked')
            self.label_overrideTemplate_customer.setHidden(False)
            self.label_overrideTemplate_pipeBundle.setHidden(False)
            self.overrideTemplate_customer.setHidden(False)
            self.overrideTemplate_pipeBundle.setHidden(False)

    def saveResults(self):
        """Writes results (lines, customers, junctions) from temp schema to version schema"""
        self.conn=dbConnect(self.dictDB,True)
        if self.conn:
            self.cur=self.conn.cursor(cursor_factory = psycopg2.extras.RealDictCursor)
            print('save Results')
            dropDBTriggers(self.cur,self.dictDB) #child versions are not updated
            sql="""TRUNCATE "{}".lines, "{}".customers, "{}".junctions, "{}".customer_connections, "{}".junction_connections, "{}".energy_plant_connections, "{}".energy_plants CASCADE;\n""".format(self.dictDB['versionName'],self.dictDB['versionName'],self.dictDB['versionName'],self.dictDB['versionName'],self.dictDB['versionName'],self.dictDB['versionName'],self.dictDB['versionName'])
            sql+=""" INSERT INTO "{}".lines SELECT * FROM temp.lines ORDER BY id;\n""".format(self.dictDB['versionName'])
            sql+=""" INSERT INTO "{}".customers SELECT * FROM temp.customers ORDER BY id;\n""".format(self.dictDB['versionName'])
            sql+=""" INSERT INTO "{}".energy_plants SELECT * FROM temp.energy_plants ORDER BY id;\n""".format(self.dictDB['versionName'])
            sql+=""" INSERT INTO "{}".junctions SELECT * FROM temp.junctions ORDER BY id;\n""".format(self.dictDB['versionName'])
            sql+=""" INSERT INTO "{}".junction_connections SELECT * FROM temp.junction_connections ORDER BY id;\n""".format(self.dictDB['versionName']) 
            sql+=""" INSERT INTO "{}".customer_connections SELECT * FROM temp.customer_connections ORDER BY id;\n""".format(self.dictDB['versionName'])  
            sql+=""" INSERT INTO "{}".energy_plant_connections SELECT * FROM temp.energy_plant_connections ORDER BY id;\n""".format(self.dictDB['versionName'])
            print(sql)
            #update next value
            sql+="""SELECT setval('"{}".lines_id_seq', (SELECT MAX(id) FROM "{}".lines));""".format(self.dictDB['versionName'],self.dictDB['versionName'])
            sql+="""SELECT setval('"{}".customers_id_seq', (SELECT MAX(id) FROM "{}".customers));""".format(self.dictDB['versionName'],self.dictDB['versionName'])
            sql+="""SELECT setval('"{}".energy_plants_id_seq', (SELECT MAX(id) FROM "{}".energy_plants));""".format(self.dictDB['versionName'],self.dictDB['versionName'])

            self.cur.execute(sql)  
            insertDBTriggers(self.cur,self.dictDB) 
            removeLayers()
            layerTreeRoot = QgsProject.instance().layerTreeRoot()  
            iface.mapCanvas().snappingUtils().setIndexingStrategy(iface.mapCanvas().snappingUtils().IndexingStrategy.IndexExtent)
            for layer in ['lines','junctions','customers','energy_plants']:
                vlayer= QgsProject.instance().mapLayersByName(layer)[0]
                layerTreeRoot.findLayer(vlayer).setItemVisibilityChecked(True)
                vlayer.emitDataChanged()
            refreshMap()
        
    def rejectResults(self):
        """keep old topolgy"""
        print('Reject Results')
        removeLayers()
        layerTreeRoot = QgsProject.instance().layerTreeRoot()  
        for layer in ['lines','junctions','customers','energy_plants']:
            if QgsProject.instance().mapLayersByName(layer):
                vlayer= QgsProject.instance().mapLayersByName(layer)[0]
                layerTreeRoot.findLayer(vlayer).setItemVisibilityChecked(True)
            
    def closeEvent(self, *args, **kwargs):
        print("you just closed the PipeLayingWindow!!!")
        self.rejectResults()
        
class MapPlantsDialog(QMainWindow):
    def __init__(self,dictDB,plugin_dir):     
        """Initialize GUI for mapping plants connection types to lines id"""
        super().__init__()
        self.plugin_dir=plugin_dir
        self.dictDB=dictDB
        self.conn=dbConnect(self.dictDB,True)
        self.cur=self.conn.cursor(cursor_factory = psycopg2.extras.RealDictCursor)
        self.setWindowTitle("Map energy plants/customers connection types to lines")
        myBoldFont=QtGui.QFont('Arial', 12)
        myBoldFont.setBold(True)

        #radio buttons
        layout_rbtn = QHBoxLayout()
        self.rbtn_plants = QRadioButton('Energy plants')
        self.rbtn_customers = QRadioButton('Customers')
        
        self.rbtn_plants.toggled.connect(self.updatePlantsCustomersLists)        
        self.rbtn_customers.toggled.connect(self.updatePlantsCustomersLists)        
        layout_rbtn.addWidget(self.rbtn_plants)
        layout_rbtn.addWidget(self.rbtn_customers)

        ##list widgets for plants; --||-- connection types; line id`s
        #list widgets input
        #lists plants
        layout_plants = QVBoxLayout()
        self.label_listWidget_Plants=QLabel("Plants/Customers")
        self.label_listWidget_Plants.setAlignment(QtCore.Qt.AlignCenter)
        self.label_listWidget_Plants.setFont(myBoldFont)
        layout_plants.addWidget(self.label_listWidget_Plants)
        layout_listWidget_plants = QHBoxLayout()
        #list widget for plants
        listWidget_plants_connTypes_ids = QVBoxLayout()
        label_listWidget_Plants_ids=QLabel("Id`s")
        listWidget_plants_connTypes_ids.addWidget(label_listWidget_Plants_ids)
        self.listWidget_plants_ids = QListWidget()
        self.listWidget_plants_ids.itemClicked.connect(self.clickedPlantsId)
        listWidget_plants_connTypes_ids.addWidget(self.listWidget_plants_ids)
        layout_listWidget_plants.addLayout(listWidget_plants_connTypes_ids)
        
        #list widget for plants
        listWidget_plants_connTypes_connTypes = QVBoxLayout()
        label_listWidget_Plants_connTypes=QLabel("Connection types")
        listWidget_plants_connTypes_connTypes.addWidget(label_listWidget_Plants_connTypes)
        self.listWidget_plants_connTypes = QListWidget()
        listWidget_plants_connTypes_connTypes.addWidget(self.listWidget_plants_connTypes)
        layout_listWidget_plants.addLayout(listWidget_plants_connTypes_connTypes)
        
        layout_plants.addLayout(layout_listWidget_plants)
        
        #list widget for plants               
        layout_listWidget_lines = QVBoxLayout()
        label_listWidget_lines=QLabel("Lines")
        label_listWidget_lines.setFont(myBoldFont)
        label_listWidget_lines_ids=QLabel("Id`s")
        layout_listWidget_lines.addWidget(label_listWidget_lines)
        layout_listWidget_lines.addWidget(label_listWidget_lines_ids)
        self.listWidget_lines = QListWidget()
        layout_listWidget_lines.addWidget(self.listWidget_lines)
        
        #list widgets connections
        layout_table_connections = QVBoxLayout()
        label_tableWidget_connections=QLabel("Connections")
        label_tableWidget_connections.setFont(myBoldFont)
        layout_table_connections.addWidget(label_tableWidget_connections)
        self.tableWidget = QTableWidget(0,2)
        self.tableWidget.setHorizontalHeaderLabels(['Sequence','Connection'])   
        
        layout_table_connections.addWidget(self.tableWidget)
        
        #buttons
        layout_buttons = QHBoxLayout()
        
        btn_connect=QPushButton("Connect")
        btn_connect.pressed.connect(self.connect)
        layout_buttons.addWidget(btn_connect)
               
        btn_disconnect=QPushButton("Disconnect")
        btn_disconnect.pressed.connect(self.disconnect)
        layout_buttons.addWidget(btn_disconnect)
        
        #set layouts together
        #list Widgets input
        layout_lists_input = QHBoxLayout()
        layout_lists_input.addLayout(layout_plants)
        layout_lists_input.addLayout(layout_listWidget_lines)
        
        layout_lists = QVBoxLayout()
        layout_lists.addLayout(layout_lists_input)
        layout_lists.addLayout(layout_table_connections)
        
        layout_win = QVBoxLayout()
        layout_win.addLayout(layout_rbtn)
        layout_win.addLayout(layout_lists)
        layout_win.addLayout(layout_buttons)
        layout_win.addStretch()
        
        widget=QWidget()
        widget.setLayout(layout_win)
        self.setCentralWidget(widget)
        
    def clickedPlantsId(self, item):
        print(item.text())
        table_name=self.getTypeTableName()
        print(table_name)
        #add connection type items to listWidget_plants_connTypes
        self.listWidget_plants_connTypes.clear()
        sql="""SELECT conn_b_t.conn_type_id, conn_b_t.description 
    FROM public.bundle_type_conns conn_b_t, "{}".{} b, public.{}_templates a
    WHERE conn_b_t.conn_bundle_type_id =a.conn_bundle_type AND b.id={} AND a.template=b.template 
    ORDER BY conn_b_t.sequence;""".format(self.dictDB['versionName'],table_name,table_name[:-1],item.text())
        print(sql)
        self.cur.execute(sql)
        conn_ids=[]
        for conn_type in self.cur.fetchall():
            conn_ids.append(str(conn_type['conn_type_id'])+':'+conn_type['description'])
        if conn_ids:
            self.listWidget_plants_connTypes.addItems(conn_ids)
          
        #add connection type items to listWidget_lines
        self.listWidget_lines.clear()
        sql='SELECT array_agg(l.id::text) AS lid FROM "{}".lines l, "{}".{} a WHERE ST_dWithIn(l.geom,a.geom,0.001) AND a.id={};'.format(self.dictDB['versionName'],self.dictDB['versionName'],table_name,item.text())
        self.cur.execute(sql)
        l_ids=self.cur.fetchone()['lid']
        print(l_ids)
        if l_ids:
            self.listWidget_lines.addItems(l_ids)
            
        #add connections to self.tableWidget
        self.updateConnections(table_name,item.text())
            
    def updateConnections(self,table_name,id): 
        """Update the connections in  tableWidget"""
        self.tableWidget.setRowCount(0)
        if table_name=='energy_plants':
            sql="""SELECT conn_b_t.sequence AS sequence, CONCAT(conn_b_t.conn_type_id, ':', conn_b_t.description, '  -->  ', ep_conn.lid) AS connection
        FROM "{}".energy_plant_connections ep_conn, "{}".energy_plants ep, public.energy_plant_templates epa, public.bundle_type_conns conn_b_t
        WHERE ep.id={} AND ep.id=ep_conn.epid AND epa.template=ep.template AND epa.conn_bundle_type=conn_b_t.conn_bundle_type_id AND conn_b_t.sequence=ep_conn.ep_seq
        ORDER BY conn_b_t.sequence;""".format(self.dictDB['versionName'],self.dictDB['versionName'],id)
            print(sql)
        elif table_name=='customers':
            sql="""SELECT conn_b_t.sequence AS sequence, CONCAT(conn_b_t.conn_type_id, ':', conn_b_t.description, '  -->  ', c_conn.lid) AS connection
    FROM "{}".customer_connections c_conn, "{}".customers c, public.customer_templates ca, public.bundle_type_conns conn_b_t
    WHERE c.id={} AND c.id=c_conn.cid AND ca.template=c.template AND ca.conn_bundle_type=conn_b_t.conn_bundle_type_id AND conn_b_t.sequence=c_conn.c_seq 
    ORDER BY conn_b_t.sequence;""".format(self.dictDB['versionName'],self.dictDB['versionName'],id)
        self.cur.execute(sql)
        conns=self.cur.fetchall()
        print(conns)
        
        rowPosition = 0
        for conn in conns:
            print(conn)
            print(conn['connection'])
            self.tableWidget.insertRow(rowPosition)
            item=QTableWidgetItem(str(conn['sequence']))
            item.setFlags(item.flags() & ~Qt.ItemIsEnabled)
            self.tableWidget.setItem(rowPosition,0,item)
            item=QTableWidgetItem(conn['connection'])
            item.setFlags(item.flags() & ~Qt.ItemIsEnabled)
            self.tableWidget.setItem(rowPosition,1,item)
            rowPosition+=1
        
    def getTypeTableName(self):
        """ return the table name: devide or plant from the sender"""
        if self.rbtn_plants.isChecked()==True:
            return 'energy_plants'
        elif self.rbtn_customers.isChecked()==True:
            return 'customers'
                 
    def updatePlantsCustomersLists(self,s):
        """Update the list of plants or customer based on the radio button """
        print('Update feature list')
        print(self.sender())
        if self.sender()==self.rbtn_plants:
            table='energy_plants'
            text='Energy plants'
        elif self.sender()==self.rbtn_customers:
            table='customers'
            text='Customers'
        self.label_listWidget_Plants.setText(text)
        sql='SELECT array_agg(id::TEXT ORDER BY id) AS ids FROM "{}".{};'.format(self.dictDB['versionName'],table)
        print(sql)
        self.cur.execute(sql)
        ids=self.cur.fetchone()['ids']
        print(ids)
        self.listWidget_plants_ids.clear()
        self.listWidget_plants_connTypes.clear()
        self.listWidget_lines.clear()
        self.tableWidget.setRowCount(0)
        if ids:
            self.listWidget_plants_ids.addItems(ids)
            
    def checkListSelection(self, id, conn_type, lid):
        """ Check if all list items are selected"""
        if id:
            id=id.text()
        else:
            iface.messageBar().pushMessage("Info", "No energy plant selected!", level=Qgis.Info)
            return False
        if conn_type:
            conn_type=conn_type.text().split(':')[0]
        else:
            iface.messageBar().pushMessage("Info", "No connection type selected!", level=Qgis.Info)
            return False
        if lid:
            lid=lid.text()
        else:
            iface.messageBar().pushMessage("Info", "No line selected!", level=Qgis.Info)
            return False
        print(id)
        print(conn_type)
        print(lid)
        return [id, conn_type, lid]
        
    def connect(self):
        """Connects the connection types with the lid`s """
        print('Connects the connection types with the lid`s')
        table_name=self.getTypeTableName()
        id=self.listWidget_plants_ids.currentItem()
        conn_type=self.listWidget_plants_connTypes.currentItem()
        lid=self.listWidget_lines.currentItem()
        if self.checkListSelection(id,conn_type,lid):
            id,conn_type,lid=self.checkListSelection(id,conn_type,lid)
        else:
            return
        seq=self.listWidget_plants_connTypes.currentRow()+1
        print(seq)
        if seq:
            if table_name=="energy_plants":
                sql="""SELECT count(*) FROM "{}".energy_plant_connections WHERE lid={} AND epid={} AND ep_seq={};""".format(self.dictDB['versionName'],lid,id,seq)
            elif table_name=="customers":
                sql="""SELECT count(*) FROM "{}".customer_connections WHERE lid={} AND cid={} AND c_seq={};""".format(self.dictDB['versionName'],lid,id,seq)
            print(sql)
            self.cur.execute(sql)
            if self.cur.fetchone()['count']!=0: 
                iface.messageBar().pushMessage("Info", "Already connected!", level=Qgis.Info)
                return
            else:
                if seq and id and lid:
                    if table_name=="energy_plants":
                        sql="""INSERT INTO "{}".energy_plant_connections (epid,ep_seq,lid) VALUES({},{},{});""".format(self.dictDB['versionName'],id,seq,lid)
                    elif table_name=="customers":
                        sql="""INSERT INTO "{}".customer_connections (cid,c_seq,lid) VALUES({},{},{});""".format(self.dictDB['versionName'],id,seq,lid)
                    
                    print(sql)
                    self.cur.execute(sql)
                    self.updateConnections(table_name,id)    
     
    def getConnTypeSeq(self,table_name,id,conn_type):
        """get the sequence of the connection type in the connection bundle """
        sql="""SELECT conn_b_t.sequence
    FROM public.bundle_type_conns conn_b_t, "{}".{} a, public.{}_templates b 
    WHERE a.id={} AND b.template=a.template AND b.conn_bundle_type=conn_b_t.conn_bundle_type_id AND conn_b_t.conn_type_id={}
    ORDER BY conn_b_t.sequence;""".format(self.dictDB['versionName'],table_name,table_name[:-1],id,conn_type)
        print(sql)
        self.cur.execute(sql)
        seq=self.cur.fetchone()
        if seq:
            return seq['sequence']
        else:
            False
        
    def disconnect(self):
        """Disconnects the connection types with the lid`s """
        print('Disconnects the connection types with the lid`s')
        table_name=self.getTypeTableName()
        conn=self.tableWidget.item(self.tableWidget.currentRow(),1)
        if conn:
            conn=conn.text()
        else:
            iface.messageBar().pushMessage("Info", "No connection selected!", level=Qgis.Info)
            return False
        id=self.listWidget_plants_ids.currentItem().text()
        conn_type=conn.split(':')[0]
        lid=conn.split('-->  ')[1]
        
        seq=self.getConnTypeSeq(table_name,id,conn_type)
        if table_name=="energy_plants":
            sql="""DELETE FROM "{}".energy_plant_connections WHERE lid={} AND epid={} AND ep_seq={};""".format(self.dictDB['versionName'],lid,id,seq)
        elif table_name=="customers":
            sql="""DELETE FROM "{}".customer_connections WHERE lid={} AND cid={} AND c_seq={};""".format(self.dictDB['versionName'],lid,id,seq)
        print(sql)
        self.cur.execute(sql)
        self.updateConnections(table_name,id) 
        
class ComboBox(QComboBox):
    popupAboutToBeShown = QtCore.pyqtSignal()

    def showPopup(self):
        self.popupAboutToBeShown.emit()
        super(ComboBox, self).showPopup()
        
class ImportNetworkTopologyFromLayer(QMainWindow):
    def __init__(self,dictDB,plugin_dir):     
        """Initialize GUI to Import Network Topology From Layer"""
        super().__init__()
        self.plugin_dir=plugin_dir
        self.dictDB=dictDB
        self.conn=dbConnect(self.dictDB,True)
        self.cur=self.conn.cursor()
        self.mappedAttributes={}
        
        self.setWindowTitle("Import Network Topology From Layer")
        myBoldFont=QtGui.QFont('Arial', 12)
        myBoldFont.setBold(True)
        
        #Select Layer
        layout_layer=QHBoxLayout()
        label_layer =QLabel("Network layer:")
        layout_layer.addWidget(label_layer) 
        
        self.selectLayer =ComboBox()
        loadLayers(self,'line')
        self.selectLayer.setCurrentIndex(-1)
        self.selectLayer.popupAboutToBeShown.connect(lambda: loadLayers(self,'line'))
        layout_layer.addWidget(self.selectLayer)
        
        #Radio Buttons 
        layout_radio=QHBoxLayout()
        self.rbtn_extend = QRadioButton('Extend topology')
        self.rbtn_extend.setChecked(True)
        layout_radio.addWidget(self.rbtn_extend)
        self.rbtn_truncate = QRadioButton('Truncate existing topology')
        layout_radio.addWidget(self.rbtn_truncate)
        
        ##list widgets for attributes
        layout_listWidget_attributes = QHBoxLayout()
        #list widget for layer attributes
        layout_listWidget_layerAttributes = QVBoxLayout()
        label_listWidget_layerAttributes=QLabel("Layer fields")
        layout_listWidget_layerAttributes.addWidget(label_listWidget_layerAttributes)
        self.listWidget_layerAttributes = QListWidget()
        layout_listWidget_layerAttributes.addWidget(self.listWidget_layerAttributes)
        layout_listWidget_attributes.addLayout(layout_listWidget_layerAttributes)
       
        #list widget for lines attributes
        layout_listWidget_attributes = QVBoxLayout()
        label_listWidget_attributes=QLabel("fields")
        layout_listWidget_attributes.addWidget(label_listWidget_attributes)
        self.listWidget_attributes = QListWidget()
        layout_listWidget_attributes.addWidget(self.listWidget_attributes)
        layout_listWidget_attributes.addLayout(layout_listWidget_attributes)
        
        #table for mapped attributes  
        self.tableWidget = QTableWidget(0,3)   
        self.tableWidget.setHorizontalHeaderLabels(['Expression','','fields'])     
        self.tableWidget.itemChanged.connect(lambda: addExpressionToMappedAttributes(self,False))

        #buttons
        #connection buttons
        layout_buttons_connect = QHBoxLayout()
        
        btn_connect=QPushButton("Map layer fields")
        btn_connect.pressed.connect(lambda: mapAttributes(self))
        layout_buttons_connect.addWidget(btn_connect)
               
        btn_disconnect=QPushButton("Disconnect")
        btn_disconnect.pressed.connect(lambda: disconnectAttributes(self))
        layout_buttons_connect.addWidget(btn_disconnect)
        
        self.btn_generate_pipe_bundles=QPushButton("Pipe bundle type editor")
        layout_buttons_connect.addWidget(self.btn_generate_pipe_bundles)
        
        #connection buttons
        layout_buttons_import = QHBoxLayout()
        self.btn_import=QPushButton("Import")
        layout_buttons_import.addWidget(self.btn_import)
               
        self.btn_cancel=QPushButton("Cancel")
        layout_buttons_import.addWidget(self.btn_cancel)
        
        #set buttons layout together
        layout_buttons=QVBoxLayout()
        layout_buttons.addLayout(layout_buttons_connect)
        layout_buttons.addLayout(layout_buttons_import)
        
        #set layouts together
        layout_win = QVBoxLayout()
        layout_win.addLayout(layout_layer)
        layout_win.addLayout(layout_radio)
        layout_win.addLayout(layout_listWidget_attributes)
        layout_win.addWidget(self.tableWidget)
        layout_win.addLayout(layout_buttons)
        
        setDHCLayerListAttributes(self,'line')

        widget=QWidget()
        widget.setLayout(layout_win)
        self.setCentralWidget(widget)
        
def loadLayers(dlg,type):
    """Load layers when combobox is clicked"""
    if type=='line':
        line_check=QgsWkbTypes.LineGeometry
    else:
        line_check=QgsWkbTypes.PointGeometry
        
    oldLayerNames=[dlg.selectLayer.itemText(i) for i in range(dlg.selectLayer.count())]
    layers=QgsProject.instance().mapLayers().values()
    layers=[i.name() for i in layers if i.name() not in getDHCLayerNames() and isinstance(i, QgsVectorLayer) and i.name() not in oldLayerNames
        and i.isSpatial() and i.name() not in ['streets','buildings','subnetwork'] and i.geometryType() == line_check]
    dlg.selectLayer.addItems(layers)
    
def addExpressionToMappedAttributes(dlg,dropdown):
    print('---------------------')
    
    currentRow=dlg.tableWidget.currentRow()
    if currentRow!=-1:
        if dropdown:
            expression=dlg.tableWidget.cellWidget(currentRow, 0).currentText().split(':')[0]
        else:
            expression=dlg.tableWidget.item(currentRow, 0).text()
        attribute=dlg.tableWidget.item(currentRow, 2).text()
        dlg.mappedAttributes[attribute]=expression
        print(dlg.mappedAttributes)

def setDHCLayerListAttributes(dlg,type):
    """Sets the layer attributes"""
    if type=='line':
        layer_name='lines'
    else:
        if dlg.rbtn_plant.isChecked():
            layer_name='energy_plants'
        else:
            layer_name='customers'
    layer=QgsProject.instance().mapLayersByName(layer_name)
    print(layer)
    if layer:
        layer=layer[0]
        attributes=layer.fields()
        attributes=[str(i.name()) for i in attributes]
        dlg.listWidget_attributes.addItems(attributes)
        for attribute in attributes:
            dlg.mappedAttributes[attribute]=''
    
def disconnectAttributes(dlg):
    """Disconnect the attributes from layer to layer"""
    print("Disconnect the attributes from layer to layer")
    row=dlg.tableWidget.currentRow()
    if row!=-1:
        print(row)
        attribute=dlg.tableWidget.item(row,2).text()
        print(attribute)
        dlg.mappedAttributes[attribute]=''
        dlg.tableWidget.removeRow(row)

def mapAttributes(dlg):
    """Map the attributes from layer to layer"""
    print("Map the attributes from layer to layer")
    currentLayerAttribute=dlg.listWidget_layerAttributes.currentItem()
    currentLayer_attribute=dlg.listWidget_attributes.currentItem()
    if currentLayerAttribute:
        currentLayerAttribute='"'+currentLayerAttribute.text()+'"'
    else:
        currentLayerAttribute="1"
        
    if currentLayer_attribute:
        currentLayer_attribute=currentLayer_attribute.text()
    else:
        iface.messageBar().pushMessage("Info", "No layer field selected!", level=Qgis.Info)
        return False
    rowPosition = dlg.tableWidget.rowCount()
    
    if not dlg.mappedAttributes[currentLayer_attribute]:
        dlg.mappedAttributes[currentLayer_attribute]=currentLayerAttribute
        dlg.tableWidget.insertRow(rowPosition)
        dlg.tableWidget.setItem(rowPosition,0,QTableWidgetItem(currentLayerAttribute))            
        item=QTableWidgetItem('-->')
        item.setFlags(Qt.ItemIsSelectable | Qt.ItemIsEnabled)
        dlg.tableWidget.setItem(rowPosition,1,item)
        item=QTableWidgetItem(currentLayer_attribute)
        item.setFlags(Qt.ItemIsSelectable | Qt.ItemIsEnabled)
        dlg.tableWidget.setItem(rowPosition,2,item)
    else:            
        iface.messageBar().pushMessage("Info", "Layer field already mapped!", level=Qgis.Info)  
    print(dlg.mappedAttributes)
            
class ImportPointLayer(QMainWindow):
    def __init__(self,dictDB,plugin_dir):     
        """Initialize GUI to Import Network Topology From Point Layer"""
        super().__init__()
        self.plugin_dir=plugin_dir
        self.dictDB=dictDB
        self.conn=dbConnect(self.dictDB,True)
        self.cur=self.conn.cursor(cursor_factory = psycopg2.extras.RealDictCursor)
        self.mappedAttributes={}

        self.setWindowTitle("Import Plants or Customers From Layer")
        myBoldFont=QtGui.QFont('Arial', 12)
        myBoldFont.setBold(True)
        
        #Select Layer
        layout_layer=QHBoxLayout()
        label_layer =QLabel("Point layer:")
        layout_layer.addWidget(label_layer) 
        
        self.selectLayer =ComboBox()
        loadLayers(self,'point')
        self.selectLayer.setCurrentIndex(-1)
        self.selectLayer.popupAboutToBeShown.connect(lambda: loadLayers(self,'point'))
        layout_layer.addWidget(self.selectLayer)
        
        #radio buttons
        self.btngroup_type = QButtonGroup()
        self.btngroup_extend = QButtonGroup()
        #Radio Buttons type
        layout_radio_type=QHBoxLayout()
        self.rbtn_plant = QRadioButton('Energy plant')
        layout_radio_type.addWidget(self.rbtn_plant)
        self.btngroup_type.addButton(self.rbtn_plant)
        self.rbtn_plant.toggled.connect(lambda: setDHCLayerListAttributes(self,'point'))
        
        self.rbtn_customer = QRadioButton('Customer')
        layout_radio_type.addWidget(self.rbtn_customer)
        self.btngroup_type.addButton(self.rbtn_customer)
        self.rbtn_customer.toggled.connect(lambda: setDHCLayerListAttributes(self,'point'))
        
        #Radio Buttons extend option
        layout_radio=QHBoxLayout()
        self.rbtn_extend = QRadioButton('Extend layer')
        self.rbtn_extend.setChecked(True)
        layout_radio.addWidget(self.rbtn_extend)
        self.btngroup_extend.addButton(self.rbtn_extend)
        self.rbtn_truncate= QRadioButton('Truncate existing layer')
        layout_radio.addWidget(self.rbtn_truncate)
        self.btngroup_extend.addButton(self.rbtn_truncate)
        
        ##list widgets for attributes
        layout_listWidget_attributes = QHBoxLayout()
        #list widget for layer attributes
        layout_listWidget_layerAttributes = QVBoxLayout()
        label_listWidget_layerAttributes=QLabel("Layer fields")
        layout_listWidget_layerAttributes.addWidget(label_listWidget_layerAttributes)
        self.listWidget_layerAttributes = QListWidget()
        layout_listWidget_layerAttributes.addWidget(self.listWidget_layerAttributes)
        layout_listWidget_attributes.addLayout(layout_listWidget_layerAttributes)
       
        #list widget for lines attributes
        layout_listWidget_attributes = QVBoxLayout()
        label_listWidget_attributes=QLabel("Fields")
        layout_listWidget_attributes.addWidget(label_listWidget_attributes)
        self.listWidget_attributes = QListWidget()
        layout_listWidget_attributes.addWidget(self.listWidget_attributes)
        layout_listWidget_attributes.addLayout(layout_listWidget_attributes)
        
        #table for mapped attributes  
        self.tableWidget = QTableWidget(0,3)   
        self.tableWidget.setHorizontalHeaderLabels(['Expression','','Fields'])     
        self.tableWidget.itemChanged.connect(lambda: addExpressionToMappedAttributes(self,False))
          
        #buttons
        #connection buttons
        layout_buttons_connect = QHBoxLayout()
        
        btn_connect=QPushButton("Map to layer field")
        btn_connect.pressed.connect(lambda: mapAttributes(self))
        layout_buttons_connect.addWidget(btn_connect)
               
        btn_disconnect=QPushButton("Disconnect")
        btn_disconnect.pressed.connect(lambda: disconnectAttributes(self))
        layout_buttons_connect.addWidget(btn_disconnect)
        
        #connection buttons
        layout_buttons_import = QHBoxLayout()
        self.btn_import=QPushButton("Import")
        layout_buttons_import.addWidget(self.btn_import)
               
        self.btn_cancel=QPushButton("Cancel")
        layout_buttons_import.addWidget(self.btn_cancel)
        
        #set buttons layout together
        layout_buttons=QVBoxLayout()
        layout_buttons.addLayout(layout_buttons_connect)
        layout_buttons.addLayout(layout_buttons_import)
        
        #set layouts together
        layout_win = QVBoxLayout()
        layout_win.addLayout(layout_layer)
        layout_win.addLayout(layout_radio_type)
        layout_win.addLayout(layout_radio)
        layout_win.addLayout(layout_listWidget_attributes)
        layout_win.addWidget(self.tableWidget)
        layout_win.addLayout(layout_buttons)
        
        widget=QWidget()
        widget.setLayout(layout_win)
        self.setCentralWidget(widget)
        
class PipeBundleEditor(QMainWindow):
    def __init__(self,dictDB,plugin_dir,layer,layer_attributes):     
        """Initialize GUI to Import Network Topology From Point Layer"""
        super().__init__()
        self.plugin_dir=plugin_dir
        self.dictDB=dictDB
        self.conn=dbConnect(self.dictDB,True)
        self.cur=self.conn.cursor(cursor_factory = psycopg2.extras.RealDictCursor)
        self.mappedAttributes={}
        self.activeTable={'general':False,'construction':False }
        
        print(layer)
        print(layer_attributes)
        
        self.setWindowTitle("Pipe bundle type editor")
        myBoldFont=QtGui.QFont('Arial', 12)
        myBoldFont.setBold(True)      
        
        #Radio Buttons extend option
        layout_radio=QHBoxLayout()
        self.rbtn_extend = QRadioButton('Extend pipe bundle types')
        self.rbtn_extend.setChecked(True)
        layout_radio.addWidget(self.rbtn_extend)
        self.rbtn_truncate= QRadioButton('Truncate existing pipe bundle types, pipes and their constructions')
        layout_radio.addWidget(self.rbtn_truncate)
        
        #CheckBox add pipe bundle type field 
        layout_addField=QVBoxLayout()
        self.addPipeBundleTypeField=QCheckBox("Add Pipe bundle type field to layer: {}".format(layer.name()))
        self.addPipeBundleTypeField.setChecked(True)
        layout_addField.addWidget(self.addPipeBundleTypeField)
        self.newFieldName=QLineEdit('')
        layout_addField.addWidget(self.newFieldName)
        
        
        layout_list=QHBoxLayout()
        #list widget for layer attributes
        layout_listWidget_layerAttributes = QVBoxLayout()
        label_listWidget_layerAttributes=QLabel("Fields of {} with name:".format(layer.name()))
        layout_listWidget_layerAttributes.addWidget(label_listWidget_layerAttributes)
        self.listWidget_layerAttributes = QListWidget()
        self.listWidget_layerAttributes.addItems(layer_attributes)
        layout_listWidget_layerAttributes.addWidget(self.listWidget_layerAttributes)
        self.listWidget_layerAttributes.itemDoubleClicked.connect(self.mapAttributesDoubleClick)

        
        label_list_helptext=QLabel('Info: Double click on the \nfield in order to map it to \nthe selected field item.\nYou can use also dictionaries in the form: {key: entry}[value/attribut]')
        layout_list.addLayout(layout_listWidget_layerAttributes)
        layout_list.addWidget(label_list_helptext)

       
        #table for mapped attributes  
        self.tableWidget = QTableWidget(0,3)   
        self.tableWidget.setHorizontalHeaderLabels(['Expression','','Pipe Bundle type attributes'])
        self.pipe_bundle_type_attributes=['Pipe inner diameter, m','Number of construction layer sequences','Horizontal distance, m','Depth, m','Number of parallel pipes','Pipe ambient (1-->Ambient; 2-->Ground; 3-->Duct)','Roughness, m']
        self.mappedAttributes=dict([(i,'') for i in self.pipe_bundle_type_attributes])
        self.mappedAttributes['layer_constr']={}
        self.setPipeBundleTypeAttributes()
        self.tableWidget.itemChanged.connect(lambda: self.tableWidgetTextChanged(self))
        self.tableWidget.itemClicked.connect(lambda: self.setActiveTable('general'))
        
        #table Pipe constructions  
        layout_pipe_constr=QVBoxLayout()
        label_pipe_constr_title=QLabel('Pipe constructions')
        font=label_pipe_constr_title.font()
        font.setPointSize(12)
        label_pipe_constr_title.setFont(font)
        layout_pipe_constr.addWidget(label_pipe_constr_title)
        self.tableWidget_pipe = QTableWidget(0,3)   
        self.tableWidget_pipe.setHorizontalHeaderLabels(['Layer sequence','Material','Layer thickness, m'])
        layout_pipe_constr.addWidget(self.tableWidget_pipe)
        self.tableWidget_pipe.itemClicked.connect(lambda: self.setActiveTable('pipe'))
        self.tableWidget_pipe.itemChanged.connect(self.constrTableTextChanged)

          
        #buttons       
        #connection buttons
        layout_buttons = QHBoxLayout()
        self.btn_generate=QPushButton("Generate pipe bundle types")
        layout_buttons.addWidget(self.btn_generate)
               
        self.btn_cancel=QPushButton("Cancel")
        layout_buttons.addWidget(self.btn_cancel)
        
        
        #set layouts together
        layout_win = QVBoxLayout()
        layout_win.addLayout(layout_radio)
        layout_win.addLayout(layout_addField)
        layout_win.addLayout(layout_list)
        layout_win.addWidget(self.tableWidget)
        layout_win.addLayout(layout_pipe_constr)
        layout_win.addLayout(layout_buttons)
        
        widget=QWidget()
        widget.setLayout(layout_win)
        self.setCentralWidget(widget)
    
    def constrTableTextChanged(self,s):
        if self.activeTable['general']==True:
            table=self.tableWidget
        else:
            table=self.tableWidget_pipe
        table_index=table.currentRow()
        try:
            print(table_index)
            seq_constr=table.item(table_index,0).text()
            print(seq_constr)
            material=table.cellWidget(table_index, 1).currentText()
            print(material)
            thickness=table.item(table_index,2).text()
            print(thickness)
            self.mappedAttributes['layer_constr'][seq_constr]=[material, thickness]
            print(self.mappedAttributes)
        except:
            pass
        
    def setActiveTable(self,s):
        print(s)
        if s=='general':
            self.activeTable['general']=True
            self.activeTable['pipe']=False
        if s=='pipe':
            self.activeTable['general']=False
            self.activeTable['pipe']=True
    
    def tableWidgetTextChanged(self,dlg):
        addExpressionToMappedAttributes(dlg,False)
        current_index=self.tableWidget.currentRow()
        if current_index==1: #connect number of construction layer sequences with pipe constructions table
            self.updateSequences(self.tableWidget.item(current_index,0).text())
    
    def setPipeBundleTypeAttributes(self):
        for i in range(0,len(self.pipe_bundle_type_attributes)):
            self.tableWidget.insertRow(i)
            item=QTableWidgetItem('-->')
            item.setFlags(Qt.ItemIsSelectable | Qt.ItemIsEnabled)
            self.tableWidget.setItem(i,1,item)
            item=QTableWidgetItem(self.pipe_bundle_type_attributes[i])
            item.setFlags(Qt.ItemIsSelectable | Qt.ItemIsEnabled)
            self.tableWidget.setItem(i,2,item)
            item=QTableWidgetItem('')
            self.tableWidget.setItem(i,0,item)

    def updateSequences(self,sequences):
        """Updates the number of rows in Tabale self.tableWidget_pipe"""
        print(sequences)
        if sequences.isdigit():
            self.tableWidget_pipe.setRowCount(0)
            for i in range(0,int(sequences)):
                self.tableWidget_pipe.insertRow(i)
                item=QTableWidgetItem(str(i+1))
                item.setFlags(Qt.ItemIsSelectable | Qt.ItemIsEnabled)
                self.tableWidget_pipe.setItem(i,0,item)
                comboBox = QComboBox()
                comboBox.addItems(getDropDownItems(self.cur,[[1,'public','materials','id','name']])[1])
                comboBox.currentTextChanged.connect(self.constrTableTextChanged)
                self.tableWidget_pipe.setCellWidget(i,1,comboBox)
                self.tableWidget_pipe.setItem(i,2,QTableWidgetItem(''))
        else:
            self.iface.messageBar().pushMessage("Error", "Please enter an integer number!", level=Qgis.Critical)


    def mapAttributesDoubleClick(self,s):
        print(s.text())
        if self.activeTable['general']==True:
            table=self.tableWidget
        else:
            table=self.tableWidget_pipe
        table_index=table.currentRow()
        if table_index!=-1:
            if self.activeTable['general']==True:
                if table_index not in [1,4]: 
                    self.mappedAttributes[table.item(table_index,2).text()]=self.mappedAttributes[table.item(table_index,2).text()]+'"'+s.text()+'"'
                    table.setItem(table_index,0,QTableWidgetItem(self.mappedAttributes[table.item(table_index,2).text()]))
                else:
                    iface.messageBar().pushMessage("Info", "This attribut cannot be mapped. Please enter an integer number.", level=Qgis.Info)
            else:
                seq_constr=table.item(table_index,0).text()
                material=table.cellWidget(table_index, 1).currentText()
                try:
                    self.mappedAttributes['layer_constr'][seq_constr]=[material, self.mappedAttributes['layer_constr'][seq_constr][1]+'"'+s.text()+'"']
                except:
                    self.mappedAttributes['layer_constr'][seq_constr]=[material, '"'+s.text()+'"']
                table.setItem(table_index,2,QTableWidgetItem(self.mappedAttributes['layer_constr'][seq_constr][1]))
        else:
            iface.messageBar().pushMessage("Info", "No pipe bundle type attribute selected!", level=Qgis.Info)

class PipeSizingDlg(QMainWindow):
    def __init__(self,dictDB,plugin_dir,cur):     
        """Initialize GUI to Import Network Topology From Point Layer"""
        super().__init__()
        self.plugin_dir=plugin_dir
        self.dictDB=dictDB
        self.conn=dbConnect(self.dictDB,True)
        self.cur=self.conn.cursor(cursor_factory = psycopg2.extras.RealDictCursor)
        self.process_running=False
        self.pipes={}
        self.pipes_list=[]
        self.new_pipe_bundles=[]
        self.sequences=[]
        self.used_sequences=[]
        
        
        self.setWindowTitle("Pipe sizing")
        myBoldFont=QtGui.QFont('Arial', 12)
        myBoldFont.setBold(True)               
        
        #labels
        layout_label = QVBoxLayout()
        self.label_dp =QLabel("Specific pressure drop, m pipe")
        layout_label.addWidget(self.label_dp)                 

        self.label_epsilon =QLabel("Absolute roughness, m")
        layout_label.addWidget(self.label_epsilon)    

        self.label_rho =QLabel("Density, kg/m3")
        layout_label.addWidget(self.label_rho)      

        self.label_cp =QLabel("Specific heat, J/(kg*K)")
        layout_label.addWidget(self.label_cp)   

        self.label_ambient =QLabel("Pipe ambient (1-->Ambient; 2-->Ground; 3-->Duct)")
        layout_label.addWidget(self.label_ambient)          
        
        self.label_kin_viscosity =QLabel("Kinematic viscosity, m2/s")
        layout_label.addWidget(self.label_kin_viscosity)  

        layout_label.addWidget(QLabel("Network"))
        
        self.label_main_plant = QLabel("Main energy plant")
        layout_label.addWidget(self.label_main_plant)
        
        
        #values
        layout_values = QVBoxLayout()
        self.dp =QLineEdit("100")
        layout_values.addWidget(self.dp)
        
        self.epsilon =QLineEdit("0.000045")
        layout_values.addWidget(self.epsilon)
        
        self.rho =QLineEdit("988")
        layout_values.addWidget(self.rho)     

        self.cp =QLineEdit("4181")
        layout_values.addWidget(self.cp)       

        self.ambient =QLineEdit("2")
        layout_values.addWidget(self.ambient)  
        
        self.kin_viscosity =QLineEdit("")
        layout_values.addWidget(self.kin_viscosity)     
        
        self.combo_network_models = QComboBox()     
        networks=getNetworks(cur,dictDB)
        self.combo_network_models.addItems(networks)      
        layout_values.addWidget(self.combo_network_models)    

        self.combo_main_plants = QComboBox()     
        plants=getPlantIds(cur,dictDB)
        self.combo_main_plants.addItems(plants)      
        layout_values.addWidget(self.combo_main_plants)        

        layout_inputs = QHBoxLayout()
        layout_inputs.addLayout(layout_label)
        layout_inputs.addLayout(layout_values)
        
        #radio sizing option
        self.rbtn_customers = QRadioButton('Sizing according to customer`s energy demand and shortest path from customer to main energy plant')
        self.rbtn_customers.setChecked(True)
        self.rbtn_lines = QRadioButton('Line`s energy demand')
        
        self.rbtn_customers.toggled.connect(self.updateSizingOption)
        
        layout_sizing_options = QHBoxLayout()
        layout_sizing_options.addWidget(self.rbtn_customers)
        layout_sizing_options.addWidget(self.rbtn_lines)
        
        #simultaneity
        self.checkBoxSimultaneity=QCheckBox("Consider the simultaneity of energy consumption")
        self.checkBoxSimultaneity.setChecked(True) 
        self.checkBoxSimultaneity.stateChanged.connect(lambda: self.updateSimultaneity())
        self.combo_simultaneity=QComboBox(self)
        self.combo_simultaneity.addItems(getTableAttr(self.cur,self.dictDB,'line'))
        self.combo_simultaneity.setHidden(True)

        
        #------liquid circuits----
        #label water circuits
        self.label_circuits =QLabel("Liquid circuits")
        font=self.label_circuits.font()
        font.setPointSize(15)
        self.label_circuits.setFont(font)
        
        #circuits buttons options
        layout_buttons_circuits = QHBoxLayout()
        
        self.btn_add_circuit=QPushButton("Add circuit")
        layout_buttons_circuits.addWidget(self.btn_add_circuit)
        self.btn_add_circuit.clicked.connect(self.addRow)
        
        self.btn_del_circuit=QPushButton("Delete circuit")
        layout_buttons_circuits.addWidget(self.btn_del_circuit)
        self.btn_del_circuit.clicked.connect(self.deleteRow)
        
        #table
        #table for circuits mapping 
        self.table_circuits = QTableWidget(0,6)   
        self.table_circuits.setHorizontalHeaderLabels(['Supply','T supply, °C','','Return','T return, °C','Load column, W'])     
        #self.tableWidget.itemChanged.connect(lambda: addExpressionToMappedAttributes(self,False))
        
        #label select pipes
        self.label_sequences =QLabel("Select considerable pipes per sequence")
        font=self.label_sequences.font()
        font.setPointSize(15)
        self.label_sequences.setFont(font)
        
        #table in order to chack selectable pipes per sequence 
        self.table_sequences = QTableWidget(0,2)   
        self.table_sequences.setHorizontalHeaderLabels(['Sequence','Select considered pipes'])   
          
        #buttons       
        #save reject buttons
        layout_buttons = QHBoxLayout()
        
        self.btn_start=QPushButton("Start")
        layout_buttons.addWidget(self.btn_start)
        
        self.btn_save=QPushButton("Save")
        layout_buttons.addWidget(self.btn_save)
        
        self.btn_reject=QPushButton("Reject")
        layout_buttons.addWidget(self.btn_reject)
        
        #progress bar
        self.progress=QProgressBar()
        
        
        #set layouts together
        layout_win = QVBoxLayout()
        layout_win.addLayout(layout_inputs)
        layout_win.addLayout(layout_sizing_options)
        layout_win.addWidget(self.checkBoxSimultaneity)
        layout_win.addWidget(self.combo_simultaneity)
        layout_win.addWidget(self.label_circuits)
        layout_win.addLayout(layout_buttons_circuits)
        layout_win.addWidget(self.table_circuits)
        layout_win.addWidget(self.label_sequences)
        layout_win.addWidget(self.table_sequences)
        layout_win.addLayout(layout_buttons)
        layout_win.addWidget(self.progress)
        
        widget=QWidget()
        widget.setLayout(layout_win)
        self.setCentralWidget(widget)
        self.threadpool = QThreadPool()
        
    def closeEvent(self, *args, **kwargs):
        print("you just closed the PipeSizingWindow!!!")
        rejectPipeSizingResults(self.dictDB,self.conn,self)
        
    def updateSizingOption(self): 
        self.updateSimultaneity()
        self.updateMainEnergyPlant()
            
        for row in range(self.table_circuits.rowCount()):
            energy_demand_colmn = QComboBox(self)
            energy_demand_colmn.addItems(getTableAttr(self.cur,self.dictDB,'customer' if self.rbtn_customers.isChecked() else 'line'))    
            self.table_circuits.setCellWidget(row, 5, energy_demand_colmn)
            
    def updateSimultaneity(self): 
        if self.rbtn_lines.isChecked() and self.checkBoxSimultaneity.isChecked():
            self.combo_simultaneity.setHidden(False)
        else:
            self.combo_simultaneity.setHidden(True)

    def updateMainEnergyPlant(self): 
        if self.rbtn_lines.isChecked():
            self.combo_main_plants.setHidden(True)
            self.label_main_plant.setHidden(True)
        else:
            self.combo_main_plants.setHidden(False)
            self.label_main_plant.setHidden(False)
            
    def addRow(self):
        self.table_circuits.insertRow(0)
        self.sequences=getNetworkSequences(self.cur,self.dictDB,self.combo_network_models.currentText())
        self.combo_box_seq_sup = QComboBox(self)
        self.combo_box_seq_sup.addItems(self.sequences)
        self.table_circuits.setCellWidget(0, 0, self.combo_box_seq_sup)
        self.combo_box_seq_sup.currentIndexChanged.connect(self.on_combo_changed)
        if self.sequences[0] not in self.getTableSequences():
            self.addSequenceRow(self.sequences[0])
        
        self.table_circuits.setItem(0, 1, QTableWidgetItem(""))
 
        item = QTableWidgetItem("-->")
        # Make the item non-editable by setting its flags
        item.setFlags(item.flags() & ~Qt.ItemIsEditable)
        self.table_circuits.setItem(0, 2, item)
        
        self.combo_box_seq_ret = QComboBox(self)
        self.combo_box_seq_ret.addItems(self.sequences)
        self.table_circuits.setCellWidget(0, 3, (self.combo_box_seq_ret))
        self.combo_box_seq_ret.currentIndexChanged.connect(self.on_combo_changed)
        
        self.table_circuits.setItem(0, 4, QTableWidgetItem(""))

        #energy demand
        energy_demand_colmn = QComboBox(self)
        energy_demand_colmn.addItems(getTableAttr(self.cur,self.dictDB,'customer' if self.rbtn_customers.isChecked() else 'line'))            
        self.table_circuits.setCellWidget(0, 5, energy_demand_colmn)

    def on_combo_changed(self, index):
        print(f"ComboBox index changed to: {index}")
        sequence=self.table_circuits.cellWidget(self.table_circuits.currentRow(), self.table_circuits.currentColumn()).currentText()
        self.getUsedSequences()
        if sequence not in self.getTableSequences():
            self.addSequenceRow(sequence)
            
        for row,table_seq in enumerate(self.getTableSequences()):
            if table_seq not in self.used_sequences:
                self.table_sequences.removeRow(row)
        
    def getUsedSequences(self):
        self.used_sequences=[]
        for row in range(self.table_circuits.rowCount()):
            for col in [0,3]:
                sequence=self.table_circuits.cellWidget(row,col).currentText()
                if sequence not in self.used_sequences:
                    self.used_sequences.append(sequence)
                    
    def getTableSequences(self):
        table_sequences=[]
        for row in range(self.table_sequences.rowCount()):
            sequence=self.table_sequences.item(row,0).text()
            table_sequences.append(sequence)
        return table_sequences
        
    def addSequenceRow(self,sequence):
        print('--new sequence--')
        new_row=self.table_sequences.rowCount()
        self.table_sequences.insertRow(new_row)
        self.table_sequences.setItem(new_row, 0, QTableWidgetItem(sequence))
        pipes_combo = CheckableComboBox()
        pipes_combo.addItem('Check all items')
        pipes_combo.addItems(self.pipes_list)
        for i in range(len(self.pipes_list)):
            pipes_combo.setItemChecked(i+1,False) 
        self.table_sequences.setCellWidget(new_row, 1, pipes_combo)   

        
    def deleteRow(self):
        selected_indexes = self.table_sequences.selectedIndexes()
        if selected_indexes:
            # Find the row of the first selected index (all selected indexes in the same row)
            selected_row = selected_indexes[0].row()

            # Remove the row
            self.table_sequences.removeRow(selected_row)
        else:
            iface.messageBar().pushMessage("Info", "No row selected!", level=Qgis.Info)
            
    def update_progress(self,progress):
        self.progress.setValue(progress)

    def update_finished(self,message):
        self.process_running=False
        
    def show_error_message(self, message):
        # Show the error message in a messageBar
        iface.messageBar().pushMessage("Error", message, level=Qgis.Critical)
        
    def execute(self,networks):  
        if self.conn:
            if checkNetwork(self.cur,self.dictDB['versionName'],networks):                 
                self.worker = WorkerGenerateNetworkTopology(iface=iface,dictDB=self.dictDB,plugin_dir=self.plugin_dir, networks=networks ,redraw_submodels_polygons=False, deleteUnconnectedCustomers=False, deleteUnconnectedLines=False,
                    connectCustomers=False,connectCustomers_template_pipeBundle='0',
                    addCustomers=False,addCustomers_template_customers='0',
                    connectPlants=False,connectPlants_template_pipeBundle='0',
                    deleteUnconnectedNetworkEnds=False,
                    keepTemplates=True,
                    overrideTemplates=False,overrideTemplates_customers='0',overrideTemplates_pipeBundle='0',tolerance=0.001,
                    showTempTables=False)
                self.worker.signals.error.connect(self.show_error_message)
                self.worker.signals.progress.connect(self.update_progress)
                self.threadpool.start(self.worker) 

    def doSizing(self,cur,dictDB,dlg,network,plugin_dir,dp,epsilon,rho,cp,kin_viscosity,ambient,pipe_bundles):
        print('++do-sizing++')
        worker_pipeSizing=WorkerPipeSizing(cur=cur,dictDB=dictDB,dlg=dlg,network=network,plugin_dir=plugin_dir,dp=dp,epsilon=epsilon,rho=rho,cp=cp,kin_viscosity=kin_viscosity,ambient=ambient,pipe_bundles=pipe_bundles)
        worker_pipeSizing.signals.error.connect(dlg.show_error_message)
        worker_pipeSizing.signals.progress.connect(dlg.update_progress)
        worker_pipeSizing.signals.finished.connect(self.update_finished)
        self.threadpool.start(worker_pipeSizing) 
