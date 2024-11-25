""" This file contains the dialog code for IDA Districts Preprocessing"""

from plugins.utility_functions.db import *
from plugins.utility_functions.dialog import *
from plugins.utility_functions.error_handling import *
from plugins.utility_functions.layer_visualization import *
from .PipeLayingAlgorithm import WorkerPipeLaying 
from .pipe_sizing import * 
from .GenerateNetworkTopology import WorkerGenerateNetworkTopology 
from qgis.PyQt.QtCore import Qt, QThreadPool
from qgis.PyQt.QtWidgets import QMessageBox,QButtonGroup, QInputDialog, QTableWidgetItem,QTableWidget, QTreeView,QAction,QMainWindow,QWidget,QPushButton,QHBoxLayout,QVBoxLayout,QLabel,QLineEdit,QCheckBox,QComboBox, QProgressBar, QComboBox, QCheckBox, QRadioButton, QListWidget
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
        
        self.btn_importPointLayer=QPushButton("Import plant, device or customer from layer")
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
        
        self.btn_mapDevicesPlants=QPushButton("Map connection types to lines")
        layout_mapping_buttons.addWidget(self.btn_mapDevicesPlants)
        
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
        
        #heating network
        self.check_heating_network =QCheckBox("Generate heating network")
        self.check_heating_network.stateChanged.connect(self.heating_network_generation_state)
        
        #connection constraints: maximum supply temperature,
        #constraints for algoritmn: minimum linear heat density,
        
        #labels
        layout_constr_heating_label = QVBoxLayout()
        self.label_tsup_max =QLabel("Maximum supply temperature, °C")
        self.label_tsup_max.setHidden(True)
        self.label_tsup_max.setStyleSheet("padding-left: 30")
        layout_constr_heating_label.addWidget(self.label_tsup_max)                   
               
        self.label_linearHeatDensity_min =QLabel("Minimum linear heat density, kWh/m trench/a")
        self.label_linearHeatDensity_min.setHidden(True)
        self.label_linearHeatDensity_min.setStyleSheet("padding-left: 30")
        layout_constr_heating_label.addWidget(self.label_linearHeatDensity_min)

        self.label_heat_demand_min =QLabel("Minimum heat demand, kWh/a")
        self.label_heat_demand_min.setHidden(True)
        self.label_heat_demand_min.setStyleSheet("padding-left: 30")
        layout_constr_heating_label.addWidget(self.label_heat_demand_min)
        
        self.label_heating_load_min =QLabel("Minimum heating load, kW")
        self.label_heating_load_min.setHidden(True)
        self.label_heating_load_min.setStyleSheet("padding-left: 30")
        layout_constr_heating_label.addWidget(self.label_heating_load_min)
        
        self.label_heating_assettype_customer =QLabel("Customer asset type")
        self.label_heating_assettype_customer.setHidden(True)
        self.label_heating_assettype_customer.setStyleSheet("padding-left: 30")
        layout_constr_heating_label.addWidget(self.label_heating_assettype_customer)
        
        self.label_heating_assettype_lines =QLabel("Lines asset type")
        self.label_heating_assettype_lines.setHidden(True)
        self.label_heating_assettype_lines.setStyleSheet("padding-left: 30")
        layout_constr_heating_label.addWidget(self.label_heating_assettype_lines)
        
        #values
        layout_constr_heating_input = QVBoxLayout()
        self.tsup_max =QLineEdit("100")
        self.tsup_max.setHidden(True)
        layout_constr_heating_input.addWidget(self.tsup_max)
        
        self.linearHeatDensity_min =QLineEdit("0")
        self.linearHeatDensity_min.setHidden(True)
        layout_constr_heating_input.addWidget(self.linearHeatDensity_min)    

        self.heat_demand_min =QLineEdit("0")
        self.heat_demand_min.setHidden(True)
        layout_constr_heating_input.addWidget(self.heat_demand_min)    

        self.heating_load_min =QLineEdit("0")
        self.heating_load_min.setHidden(True)
        layout_constr_heating_input.addWidget(self.heating_load_min)    

        self.heating_assettype_customer =QComboBox()
        self.heating_assettype_customer.addItems(['1'])
        self.heating_assettype_customer.setCurrentText('1')
        self.heating_assettype_customer.setHidden(True)
        self.heating_assettype_customer.setStyleSheet("padding-left: 30")
        layout_constr_heating_input.addWidget(self.heating_assettype_customer)  

        self.heating_assettype_lines =QComboBox()
        self.heating_assettype_lines.addItems(['7'])
        self.heating_assettype_lines.setCurrentText('7')
        self.heating_assettype_lines.setHidden(True)
        self.heating_assettype_lines.setStyleSheet("padding-left: 30")
        layout_constr_heating_input.addWidget(self.heating_assettype_lines)           
        
        #costs
        #labels
        self.check_heating_network_costs =QCheckBox("consider trench and pipe costs")
        self.check_heating_network_costs.stateChanged.connect(self.heating_network_costs_state)
        self.check_heating_network_costs.setStyleSheet("padding-left: 30")
        self.check_heating_network_costs.setHidden(True)
        
        layout_constr_heating_costs_label = QVBoxLayout()
                
        self.label_heat_loss =QLabel("Heat loss, kWh/m trench/a")
        self.label_heat_loss.setHidden(True)
        self.label_heat_loss.setStyleSheet("padding-left: 60")
        layout_constr_heating_costs_label.addWidget(self.label_heat_loss) 
        
        self.label_heat_costs =QLabel("Heat costs, €/kWh")
        self.label_heat_costs.setHidden(True)
        self.label_heat_costs.setStyleSheet("padding-left: 60")
        layout_constr_heating_costs_label.addWidget(self.label_heat_costs) 

        self.label_amortization_period_heat =QLabel("Amortization period, a")
        self.label_amortization_period_heat.setHidden(True)
        self.label_amortization_period_heat.setStyleSheet("padding-left: 60")
        layout_constr_heating_costs_label.addWidget(self.label_amortization_period_heat) 
        
        #values
        layout_constr_heating_costs_input = QVBoxLayout()
                
        self.heat_loss = QLineEdit("100")
        self.heat_loss.setHidden(True)
        layout_constr_heating_costs_input.addWidget(self.heat_loss) 
        
        self.heat_costs = QLineEdit("0.1")
        self.heat_costs.setHidden(True)
        layout_constr_heating_costs_input.addWidget(self.heat_costs) 
        
        self.amortization_period_heat = QLineEdit("30")
        self.amortization_period_heat.setHidden(True)
        layout_constr_heating_costs_input.addWidget(self.amortization_period_heat) 
        
        #cooling network
        #connection constraints: maximum supply temperature,
        #constraints for algoritmn: minimum linear heat density,
        self.check_cooling_network =QCheckBox("Generate cooling network")
        self.check_cooling_network.stateChanged.connect(self.cooling_network_generation_state)
        
        #labels
        layout_constr_cooling_label = QVBoxLayout()
        self.label_tsup_min =QLabel("Minimum supply temperature, °C")
        self.label_tsup_min.setHidden(True)
        self.label_tsup_min.setStyleSheet("padding-left: 30")
        layout_constr_cooling_label.addWidget(self.label_tsup_min)                   
        
        self.label_linearColdDensity_min =QLabel("Minimum linear cold density, kWh/m trench/a")
        self.label_linearColdDensity_min.setHidden(True)
        self.label_linearColdDensity_min.setStyleSheet("padding-left: 30")
        layout_constr_cooling_label.addWidget(self.label_linearColdDensity_min)
        
        self.label_cold_demand_min =QLabel("Minimum cold demand, kWh/a")
        self.label_cold_demand_min.setHidden(True)
        self.label_cold_demand_min.setStyleSheet("padding-left: 30")
        layout_constr_cooling_label.addWidget(self.label_cold_demand_min)
        
        self.label_cooling_load_min =QLabel("Minimum cooling load, kW")
        self.label_cooling_load_min.setHidden(True)
        self.label_cooling_load_min.setStyleSheet("padding-left: 30")
        layout_constr_cooling_label.addWidget(self.label_cooling_load_min)
        
        self.label_cooling_assettype_customer =QLabel("Customer asset type")
        self.label_cooling_assettype_customer.setHidden(True)
        self.label_cooling_assettype_customer.setStyleSheet("padding-left: 30")
        layout_constr_cooling_label.addWidget(self.label_cooling_assettype_customer)
        
        self.label_cooling_assettype_lines =QLabel("Lines asset type")
        self.label_cooling_assettype_lines.setHidden(True)
        self.label_cooling_assettype_lines.setStyleSheet("padding-left: 30")
        layout_constr_cooling_label.addWidget(self.label_cooling_assettype_lines)
        
        #values
        layout_constr_cooling_input = QVBoxLayout()
        self.tsup_min =QLineEdit("15")
        self.tsup_min.setHidden(True)
        layout_constr_cooling_input.addWidget(self.tsup_min)
        
        self.linearColdDensity_min =QLineEdit("0")
        self.linearColdDensity_min.setHidden(True)
        layout_constr_cooling_input.addWidget(self.linearColdDensity_min) 
        
        self.cold_demand_min =QLineEdit("0")
        self.cold_demand_min.setHidden(True)
        layout_constr_cooling_input.addWidget(self.cold_demand_min)    

        self.cooling_load_min =QLineEdit("0")
        self.cooling_load_min.setHidden(True)
        layout_constr_cooling_input.addWidget(self.cooling_load_min) 
        
        self.cooling_assettype_customer =QComboBox()
        self.cooling_assettype_customer.addItems(['2'])
        self.cooling_assettype_customer.setCurrentText('2')
        self.cooling_assettype_customer.setHidden(True)
        self.cooling_assettype_customer.setStyleSheet("padding-left: 30")
        layout_constr_cooling_input.addWidget(self.cooling_assettype_customer)  

        self.cooling_assettype_lines =QComboBox()
        self.cooling_assettype_lines.addItems(['12'])
        self.cooling_assettype_lines.setCurrentText('12')
        self.cooling_assettype_lines.setHidden(True)
        self.cooling_assettype_lines.setStyleSheet("padding-left: 30")
        layout_constr_cooling_input.addWidget(self.cooling_assettype_lines)  
        
        #costs
        #labels
        self.check_cooling_network_costs =QCheckBox("consider trench and pipe costs")
        self.check_cooling_network_costs.stateChanged.connect(self.cooling_network_costs_state)
        self.check_cooling_network_costs.setStyleSheet("padding-left: 30")
        self.check_cooling_network_costs.setHidden(True)
        
        layout_constr_cooling_costs_label = QVBoxLayout()
                
        self.label_cold_loss =QLabel("Heat loss, kWh/m trench/a")
        self.label_cold_loss.setHidden(True)
        self.label_cold_loss.setStyleSheet("padding-left: 60")
        layout_constr_cooling_costs_label.addWidget(self.label_cold_loss) 
        
        self.label_cold_costs =QLabel("Heat costs, €/kWh")
        self.label_cold_costs.setHidden(True)
        self.label_cold_costs.setStyleSheet("padding-left: 60")
        layout_constr_cooling_costs_label.addWidget(self.label_cold_costs) 

        self.label_amortization_period_cold =QLabel("Amortization period, a")
        self.label_amortization_period_cold.setHidden(True)
        self.label_amortization_period_cold.setStyleSheet("padding-left: 60")
        layout_constr_cooling_costs_label.addWidget(self.label_amortization_period_cold) 
        
        #values
        layout_constr_cooling_costs_input = QVBoxLayout()
                
        self.cold_loss = QLineEdit("100")
        self.cold_loss.setHidden(True)
        layout_constr_cooling_costs_input.addWidget(self.cold_loss) 
        
        self.cold_costs = QLineEdit("0.1")
        self.cold_costs.setHidden(True)
        layout_constr_cooling_costs_input.addWidget(self.cold_costs) 
        
        self.amortization_period_cold = QLineEdit("30")
        self.amortization_period_cold.setHidden(True)
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
        layout_tolarance=QHBoxLayout()
        label=QLabel('Snapping tolerance, m: ')
        layout_tolarance.addWidget(label)
        self.tolerance=QLineEdit('0.01')
        layout_tolarance.addWidget(self.tolerance)
        
        #networks
        layout_networks=QHBoxLayout()
        label_network =QLabel("Network")
        networks=getNetworks(self.cur,self.dictDB)
        print(networks)
        self.combo_network = QComboBox()
        self.combo_network.addItems(networks)
        layout_networks.addWidget(label_network)
        layout_networks.addWidget(self.combo_network)
        
        #asset type if heating and cooling
        layout_hc_label_assettype = QVBoxLayout()
        self.label_hc_assettype_customer =QLabel("Heating/cooling customer asset type")
        self.label_hc_assettype_customer.setHidden(True)
        self.label_hc_assettype_customer.setStyleSheet("padding-left: 30")
        layout_hc_label_assettype.addWidget(self.label_hc_assettype_customer)
        
        
        self.label_hc_assettype_lines =QLabel("Heating/cooling lines asset type")
        self.label_hc_assettype_lines.setHidden(True)
        self.label_hc_assettype_lines.setStyleSheet("padding-left: 30")
        layout_hc_label_assettype.addWidget(self.label_hc_assettype_lines)
        
        layout_hc_input_assettype = QVBoxLayout()
        self.hc_assettype_customer =QComboBox()
        self.hc_assettype_customer.addItems(['3','5'])
        self.hc_assettype_customer.setCurrentText('3')
        self.hc_assettype_customer.setHidden(True)
        self.hc_assettype_customer.setStyleSheet("padding-left: 30")
        layout_hc_input_assettype.addWidget(self.hc_assettype_customer)  

        self.hc_assettype_lines =QComboBox()
        self.hc_assettype_lines.addItems(['8','9'])
        self.hc_assettype_lines.setCurrentText('8')
        self.hc_assettype_lines.setHidden(True)
        self.hc_assettype_lines.setStyleSheet("padding-left: 30")
        layout_hc_input_assettype.addWidget(self.hc_assettype_lines)   
        
        layout_hc_assettype_type = QHBoxLayout()
        layout_hc_assettype_type.addLayout(layout_hc_label_assettype)
        layout_hc_assettype_type.addLayout(layout_hc_input_assettype)
        
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
        layout_constr_heating = QHBoxLayout()
        layout_constr_heating.addLayout(layout_constr_heating_label)
        layout_constr_heating.addLayout(layout_constr_heating_input)   

        layout_constr_heating_costs = QHBoxLayout()
        layout_constr_heating_costs.addLayout(layout_constr_heating_costs_label)
        layout_constr_heating_costs.addLayout(layout_constr_heating_costs_input)         
        
        layout_constr_cooling = QHBoxLayout()
        layout_constr_cooling.addLayout(layout_constr_cooling_label)
        layout_constr_cooling.addLayout(layout_constr_cooling_input) 
        
        layout_constr_cooling_costs = QHBoxLayout()
        layout_constr_cooling_costs.addLayout(layout_constr_cooling_costs_label)
        layout_constr_cooling_costs.addLayout(layout_constr_cooling_costs_input) 
        
        layout_win = QVBoxLayout()
        layout_win.addWidget(self.check_heating_network)
        layout_win.addLayout(layout_constr_heating)
        layout_win.addWidget(self.check_heating_network_costs)
        layout_win.addLayout(layout_constr_heating_costs)
        layout_win.addWidget(self.check_cooling_network)
        layout_win.addLayout(layout_constr_cooling)
        layout_win.addWidget(self.check_cooling_network_costs)
        layout_win.addLayout(layout_constr_cooling_costs)
        layout_win.addWidget(self.check_extend_network)
        layout_win.addWidget(self.keep_unconnected_customers)
        layout_win.addWidget(self.redraw_submodels_polygons)
        layout_win.addWidget(self.customer_connection_mode)
        layout_win.addLayout(layout_tolarance)
        layout_win.addLayout(layout_networks)
        layout_win.addLayout(layout_hc_assettype_type)
        layout_win.addLayout(layout_actionButtons)
        layout_win.addWidget(self.progress)
        layout_win.addLayout(layout_saveButtons)
        layout_win.addStretch()
        
        widget=QWidget()
        widget.setLayout(layout_win)
        self.setCentralWidget(widget)
        self.threadpool = QThreadPool()
        print("Multithreading with maximum %d threads" % self.threadpool.maxThreadCount())
        
    def execute(self):  
        print(self.dictDB)
        layerCheck=checkPipeLayingLayerData(self.dictDB,self.cur,self.combo_network.currentText())
        if layerCheck=='no_streets':
            self.iface.messageBar().pushMessage("Error", "Please insert streets into the streets layer.", level=Qgis.Critical)
        elif layerCheck=='no_plants':
            self.iface.messageBar().pushMessage("Error", f"Please insert a main energy plant of network: {self.combo_network.currentText()} into the energy_plants layer.", level=Qgis.Critical)
        elif layerCheck=='no_customers':
            self.iface.messageBar().pushMessage("Error", f"Please insert customers of network: {self.combo_network.currentText()} into the customers layer.", level=Qgis.Critical)
        elif not layerCheck:
            worker = WorkerPipeLaying(tolerance=self.tolerance.text(), network=self.combo_network.currentText(),iface=self.iface, check_heating_network=self.check_heating_network.isChecked(),tsup_max=self.tsup_max.text(),heat_demand_min=self.heat_demand_min.text(),heating_load_min=self.heating_load_min.text(),heating_assettype_customer=self.heating_assettype_customer.currentText(),heating_assettype_lines=self.heating_assettype_lines.currentText(),linearHeatDensity_min=self.linearHeatDensity_min.text(),check_heating_network_costs=self.check_heating_network_costs.isChecked(),heat_loss=self.heat_loss.text(),heat_costs=self.heat_costs.text(),amortization_period_heat=self.amortization_period_heat.text(),check_cooling_network=self.check_cooling_network.isChecked(),tsup_min=self.tsup_min.text(),cold_demand_min=self.cold_demand_min.text(),cooling_load_min=self.cooling_load_min.text(),cooling_assettype_customer=self.cooling_assettype_customer.currentText(),cooling_assettype_lines=self.cooling_assettype_lines.currentText(),linearColdDensity_min=self.linearColdDensity_min.text(),check_cooling_network_costs=self.check_cooling_network_costs.isChecked(),cold_loss=self.cold_loss.text(),cold_costs=self.cold_costs.text(),amortization_period_cold=self.amortization_period_cold.text(),hc_assettype_customer=self.hc_assettype_customer.currentText(),hc_assettype_lines=self.hc_assettype_lines.currentText(),customer_connection_mode=self.customer_connection_mode.currentText(),keep_unconnected_customers=self.keep_unconnected_customers.isChecked(),redraw_submodels_polygons=self.redraw_submodels_polygons.isChecked(),dictDB=self.dictDB,plugin_dir=self.plugin_dir)
            worker.signals.progress.connect(self.update_progress)
            worker.signals.error.connect(self.show_error_message)       
            #execute
            self.threadpool.start(worker) 
            self.btn_stop.pressed.connect(worker.kill)
            self.btn_pause.pressed.connect(worker.pauseResume)
        
    def show_error_message(self, message):
        # Show the error message in a messageBar
        self.iface.messageBar().pushMessage("Error", message, level=Qgis.Critical)
        
    def update_progress(self,progress):
        self.progress.setValue(progress)
        
    def heating_network_generation_state(self,s):
        print('change heating network generation state')
        print(s)
        if Qt.Checked==s:
            print('checked')
            self.label_tsup_max.setHidden(False)
            self.tsup_max.setHidden(False)
            self.label_linearHeatDensity_min.setHidden(False)
            self.linearHeatDensity_min.setHidden(False)
            self.check_heating_network_costs.setHidden(False)
            self.label_heat_demand_min.setHidden(False)
            self.heat_demand_min.setHidden(False)
            self.label_heating_load_min.setHidden(False)
            self.heating_load_min.setHidden(False)
            self.label_heating_assettype_customer.setHidden(False)
            self.label_heating_assettype_lines.setHidden(False)
            self.heating_assettype_customer.setHidden(False)
            self.heating_assettype_lines.setHidden(False)
            if self.check_heating_network_costs.isChecked():
                self.label_heat_loss.setHidden(False)
                self.heat_loss.setHidden(False)
                self.label_heat_costs.setHidden(False)
                self.heat_costs.setHidden(False)
                self.label_amortization_period_heat.setHidden(False)
                self.amortization_period_heat.setHidden(False)
            if self.check_cooling_network.isChecked():
                self.label_hc_assettype_customer.setHidden(False)
                self.label_hc_assettype_lines.setHidden(False)
                self.hc_assettype_customer.setHidden(False)
                self.hc_assettype_lines.setHidden(False)
        else:
            print('unchecked')
            self.label_tsup_max.setHidden(True)
            self.tsup_max.setHidden(True)
            self.label_linearHeatDensity_min.setHidden(True)
            self.linearHeatDensity_min.setHidden(True)
            self.label_heat_demand_min.setHidden(True)
            self.heat_demand_min.setHidden(True)
            self.label_heating_load_min.setHidden(True)
            self.heating_load_min.setHidden(True)
            self.label_heating_assettype_customer.setHidden(True)
            self.label_heating_assettype_lines.setHidden(True)
            self.heating_assettype_customer.setHidden(True)
            self.heating_assettype_lines.setHidden(True)
            self.check_heating_network_costs.setHidden(True)
            self.label_heat_loss.setHidden(True)
            self.heat_loss.setHidden(True)
            self.label_heat_costs.setHidden(True)
            self.heat_costs.setHidden(True)
            self.label_amortization_period_heat.setHidden(True)
            self.amortization_period_heat.setHidden(True)
            self.label_hc_assettype_customer.setHidden(True)
            self.label_hc_assettype_lines.setHidden(True)
            self.hc_assettype_customer.setHidden(True)
            self.hc_assettype_lines.setHidden(True)
    
    def cooling_network_generation_state(self,s):
        print('change cooling network generation state')
        print(s)
        print(Qt.Checked)
        if Qt.Checked==s:
            print('checked')
            self.label_tsup_min.setHidden(False)
            self.tsup_min.setHidden(False)
            self.label_linearColdDensity_min.setHidden(False)
            self.linearColdDensity_min.setHidden(False)
            self.check_cooling_network_costs.setHidden(False)
            self.label_cold_demand_min.setHidden(False)
            self.cold_demand_min.setHidden(False)
            self.label_cooling_load_min.setHidden(False)
            self.cooling_load_min.setHidden(False)
            self.label_cooling_assettype_customer.setHidden(False)
            self.label_cooling_assettype_lines.setHidden(False)
            self.cooling_assettype_customer.setHidden(False)
            self.cooling_assettype_lines.setHidden(False)
            if self.check_heating_network.isChecked():
                self.label_hc_assettype_customer.setHidden(False)
                self.label_hc_assettype_lines.setHidden(False)
                self.hc_assettype_customer.setHidden(False)
                self.hc_assettype_lines.setHidden(False)
            if self.check_cooling_network_costs.isChecked():
                print('costs cooling checked')
                self.label_cold_loss.setHidden(False)
                self.cold_loss.setHidden(False)
                self.label_cold_costs.setHidden(False)
                self.cold_costs.setHidden(False)
                self.label_amortization_period_cold.setHidden(False)
                self.amortization_period_cold.setHidden(False)
        else:
            print('unchecked')
            self.label_tsup_min.setHidden(True)
            self.tsup_min.setHidden(True)
            self.label_linearColdDensity_min.setHidden(True)
            self.linearColdDensity_min.setHidden(True)
            self.label_cold_demand_min.setHidden(True)
            self.cold_demand_min.setHidden(True)
            self.label_cooling_load_min.setHidden(True)
            self.cooling_load_min.setHidden(True)
            self.check_cooling_network_costs.setHidden(True)
            self.label_cooling_assettype_customer.setHidden(True)
            self.label_cooling_assettype_lines.setHidden(True)
            self.cooling_assettype_customer.setHidden(True)
            self.cooling_assettype_lines.setHidden(True)
            self.label_cold_loss.setHidden(True)
            self.cold_loss.setHidden(True)
            self.label_cold_costs.setHidden(True)
            self.cold_costs.setHidden(True)
            self.label_amortization_period_cold.setHidden(True)
            self.amortization_period_cold.setHidden(True)
            
    def heating_network_costs_state(self,s):
        print('change heating network costs state')
        if Qt.Checked==s:
            print('costs checked')
            self.label_heat_loss.setHidden(False)
            self.heat_loss.setHidden(False)
            self.label_heat_costs.setHidden(False)
            self.heat_costs.setHidden(False)
            self.label_amortization_period_heat.setHidden(False)
            self.amortization_period_heat.setHidden(False)
        else:
            print('costs unchecked')
            self.label_heat_loss.setHidden(True)
            self.heat_loss.setHidden(True)
            self.label_heat_costs.setHidden(True)
            self.heat_costs.setHidden(True)
            self.label_amortization_period_heat.setHidden(True)
            self.amortization_period_heat.setHidden(True)
            
    def cooling_network_costs_state(self,s):
        print('change cooling network costs state')
        if Qt.Checked==s:
            print('costs checked')
            self.label_cold_loss.setHidden(False)
            self.cold_loss.setHidden(False)
            self.label_cold_costs.setHidden(False)
            self.cold_costs.setHidden(False)
            self.label_amortization_period_cold.setHidden(False)
            self.amortization_period_cold.setHidden(False)
        else:
            print('costs unchecked')
            self.label_cold_loss.setHidden(True)
            self.cold_loss.setHidden(True)
            self.label_cold_costs.setHidden(True)
            self.cold_costs.setHidden(True)
            self.label_amortization_period_cold.setHidden(True)
            self.amortization_period_cold.setHidden(True) 
    
    def saveResults(self):
        """Writes results (lines, customers, junctions) from temp schema to version schema"""
        print('save Results')

        sql=""" TRUNCATE "{}".lines, "{}".customers,"{}".junctions,"{}".customer_connections, "{}".junction_connections, "{}".energy_plant_connections, "{}".device_connections,"{}".energy_plants CASCADE;""".format(self.dictDB['versionName'],self.dictDB['versionName'],self.dictDB['versionName'],self.dictDB['versionName'],self.dictDB['versionName'],self.dictDB['versionName'],self.dictDB['versionName'],self.dictDB['versionName'])
        sql+=""" INSERT INTO "{}".lines SELECT * FROM temp.lines;""".format(self.dictDB['versionName'])
        sql+=""" INSERT INTO "{}".customers SELECT * FROM temp.customers;""".format(self.dictDB['versionName'])
        sql+=""" INSERT INTO "{}".energy_plants SELECT * FROM temp.energy_plants;""".format(self.dictDB['versionName'])
        sql+=""" INSERT INTO"{}".junctions SELECT * FROM temp.junctions;""".format(self.dictDB['versionName'])
        sql+=""" INSERT INTO {}.junction_connections SELECT * FROM temp.junction_connections;""".format(self.dictDB['versionName']) 
        sql+=""" INSERT INTO "{}".customer_connections SELECT * FROM temp.customer_connections;""".format(self.dictDB['versionName'])  
        sql+=""" INSERT INTO "{}".energy_plant_connections SELECT * FROM temp.energy_plant_connections;""".format(self.dictDB['versionName'])
        print(sql) 
        self.cur.execute(sql)  
        removeLayers()
        layerTreeRoot = QgsProject.instance().layerTreeRoot()  
        iface.mapCanvas().snappingUtils().setIndexingStrategy(iface.mapCanvas().snappingUtils().IndexingStrategy.IndexExtent)
        for layer in ['lines','junctions','customers','energy_plants']:
            vlayer= QgsProject.instance().mapLayersByName(layer)[0]
            layerTreeRoot.findLayer(vlayer).setItemVisibilityChecked(True)
            vlayer.emitDataChanged()
        refreshMap()
        
    def rejectResults(self):
        """Writes results (lines, customers, junctions) from temp schema to version schema"""
        print('Reject Results')
        removeLayers()
        layerTreeRoot = QgsProject.instance().layerTreeRoot()  
        for layer in ['lines','junctions','customers','energy_plants']:
            if QgsProject.instance().mapLayersByName(layer):
                vlayer= QgsProject.instance().mapLayersByName(layer)[0]
                layerTreeRoot.findLayer(vlayer).setItemVisibilityChecked(True)
            
    def closeEvent(self, *args, **kwargs):
        print ("you just closed the PipeLayingWindow!!!")
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
        customer_assettypes=['1','2','3','4','5','6','7','8']
        cusomer_assettype='1'
        lines_assettypes=['7','8','9','12']
        line_assettype='7'
        pipeBundleTypes=['1','2']
        pipeBundleType='1'

        #assettypes
        self.rbtn_keep_assettypes = QRadioButton('Keep asset types')
        self.rbtn_keep_assettypes.setChecked(True)
        self.rbtn_override_assettypes = QRadioButton('Override asset types')
        
        self.rbtn_keep_assettypes.toggled.connect(self.keep_assettype_state)
        self.rbtn_override_assettypes.toggled.connect(self.override_assettype_state)        
        
        #labels
        layout_overrideAssettype_label = QVBoxLayout()
        
        self.label_overrideAssettype_customer =QLabel("Customer asset type")
        self.label_overrideAssettype_customer.setHidden(True)
        self.label_overrideAssettype_customer.setStyleSheet("padding-left: 30")
        layout_overrideAssettype_label.addWidget(self.label_overrideAssettype_customer)
        
        self.label_overrideAssettype_lines =QLabel("Lines asset type")
        self.label_overrideAssettype_lines.setHidden(True)
        self.label_overrideAssettype_lines.setStyleSheet("padding-left: 30")
        layout_overrideAssettype_label.addWidget(self.label_overrideAssettype_lines)
        
        self.label_overrideAssettype_pipeBundle =QLabel("Pipe bundle type")
        self.label_overrideAssettype_pipeBundle.setHidden(True)
        self.label_overrideAssettype_pipeBundle.setStyleSheet("padding-left: 30")
        layout_overrideAssettype_label.addWidget(self.label_overrideAssettype_pipeBundle)
        
        #values
        layout_overrideAssettype_input = QVBoxLayout() 

        self.overrideAssettype_customer =QComboBox()
        self.overrideAssettype_customer.addItems(customer_assettypes)
        self.overrideAssettype_customer.setCurrentText(cusomer_assettype)
        self.overrideAssettype_customer.setHidden(True)
        self.overrideAssettype_customer.setStyleSheet("padding-left: 30")
        layout_overrideAssettype_input.addWidget(self.overrideAssettype_customer)  

        self.overrideAssettype_lines =QComboBox()
        self.overrideAssettype_lines.addItems(lines_assettypes)
        self.overrideAssettype_lines.setCurrentText(line_assettype)
        self.overrideAssettype_lines.setHidden(True)
        self.overrideAssettype_lines.setStyleSheet("padding-left: 30")
        layout_overrideAssettype_input.addWidget(self.overrideAssettype_lines) 
        
        self.overrideAssettype_pipeBundle =QComboBox()
        self.overrideAssettype_pipeBundle.addItems(pipeBundleTypes)
        self.overrideAssettype_pipeBundle.setCurrentText(pipeBundleType)
        self.overrideAssettype_pipeBundle.setHidden(True)
        self.overrideAssettype_pipeBundle.setStyleSheet("padding-left: 30")
        layout_overrideAssettype_input.addWidget(self.overrideAssettype_pipeBundle) 

        #additional options
        layout_additional_options = QVBoxLayout()
        #delete unconnected network ends
        self.check_del_network_ends =QCheckBox("Delete unconnected network ends")
        
        #add customers unconnected network ends
        self.check_add_customers_network_ends =QCheckBox("Add customers to unconnected network ends")
        self.check_add_customers_network_ends.stateChanged.connect(self.addCustomers_network_ends_state)
        #labels
        layout_addCustomers_assettype_label = QVBoxLayout()
        
        self.label_addCustomers_assettype_customers =QLabel("Customer asset type")
        self.label_addCustomers_assettype_customers.setHidden(True)
        self.label_addCustomers_assettype_customers.setStyleSheet("padding-left: 30")
        layout_addCustomers_assettype_label.addWidget(self.label_addCustomers_assettype_customers)
        
        #values
        layout_addCustomers_assettype_input = QVBoxLayout() 

        self.addCustomers_assettype_customers =QComboBox()
        self.addCustomers_assettype_customers.addItems(customer_assettypes)
        self.addCustomers_assettype_customers.setCurrentText(cusomer_assettype)
        self.addCustomers_assettype_customers.setHidden(True)
        self.addCustomers_assettype_customers.setStyleSheet("padding-left: 30")
        layout_addCustomers_assettype_input.addWidget(self.addCustomers_assettype_customers)  
        
        #connect unconnected customers to network
        self.check_connectCustomers =QCheckBox("Connect unconnected customers to network")
        self.check_connectCustomers.stateChanged.connect(self.connectCustomers_state)
        #labels
        layout_connectCustomers_assettype_label = QVBoxLayout()
        
        self.label_connectCustomers_assettype_lines =QLabel("Lines asset type")
        self.label_connectCustomers_assettype_lines.setHidden(True)
        self.label_connectCustomers_assettype_lines.setStyleSheet("padding-left: 30")
        layout_connectCustomers_assettype_label.addWidget(self.label_connectCustomers_assettype_lines)
        
        self.label_connectCustomers_assettype_pipeBundle =QLabel("Pipe bundle type")
        self.label_connectCustomers_assettype_pipeBundle.setHidden(True)
        self.label_connectCustomers_assettype_pipeBundle.setStyleSheet("padding-left: 30")
        layout_connectCustomers_assettype_label.addWidget(self.label_connectCustomers_assettype_pipeBundle)
        
        #values
        layout_connectCustomers_assettype_input = QVBoxLayout()

        self.connectCustomers_assettype_lines =QComboBox()
        self.connectCustomers_assettype_lines.addItems(lines_assettypes)
        self.connectCustomers_assettype_lines.setCurrentText(line_assettype)
        self.connectCustomers_assettype_lines.setHidden(True)
        self.connectCustomers_assettype_lines.setStyleSheet("padding-left: 30")
        layout_connectCustomers_assettype_input.addWidget(self.connectCustomers_assettype_lines)  

        self.connectCustomers_assettype_pipeBundle =QComboBox()
        self.connectCustomers_assettype_pipeBundle.addItems(pipeBundleTypes)
        self.connectCustomers_assettype_pipeBundle.setCurrentText(pipeBundleType)
        self.connectCustomers_assettype_pipeBundle.setHidden(True)
        self.connectCustomers_assettype_pipeBundle.setStyleSheet("padding-left: 30")
        layout_connectCustomers_assettype_input.addWidget(self.connectCustomers_assettype_pipeBundle)          
        
        #connect unconnected plants to network
        self.check_connectPlants =QCheckBox("Connect unconnected plants to network")
        self.check_connectPlants.stateChanged.connect(self.connectPlants_state)
        #labels
        layout_connectPlants_assettype_label = QVBoxLayout()
              
        self.label_connectPlants_assettype_lines =QLabel("Lines asset type")
        self.label_connectPlants_assettype_lines.setHidden(True)
        self.label_connectPlants_assettype_lines.setStyleSheet("padding-left: 30")
        layout_connectPlants_assettype_label.addWidget(self.label_connectPlants_assettype_lines)
        
        self.label_connectPlants_assettype_pipeBundle =QLabel("Pipe bundle type")
        self.label_connectPlants_assettype_pipeBundle.setHidden(True)
        self.label_connectPlants_assettype_pipeBundle.setStyleSheet("padding-left: 30")
        layout_connectPlants_assettype_label.addWidget(self.label_connectPlants_assettype_pipeBundle)
        
        #values
        layout_connectPlants_assettype_input = QVBoxLayout() 

        self.connectPlants_assettype_lines =QComboBox()
        self.connectPlants_assettype_lines.addItems(lines_assettypes)
        self.connectPlants_assettype_lines.setCurrentText(line_assettype)
        self.connectPlants_assettype_lines.setHidden(True)
        self.connectPlants_assettype_lines.setStyleSheet("padding-left: 30")
        layout_connectPlants_assettype_input.addWidget(self.connectPlants_assettype_lines)    

        self.connectPlants_assettype_pipeBundle =QComboBox()
        self.connectPlants_assettype_pipeBundle.addItems(pipeBundleTypes)
        self.connectPlants_assettype_pipeBundle.setCurrentText(pipeBundleType)
        self.connectPlants_assettype_pipeBundle.setHidden(True)
        self.connectPlants_assettype_pipeBundle.setStyleSheet("padding-left: 30")
        layout_connectPlants_assettype_input.addWidget(self.connectPlants_assettype_pipeBundle)          

        #delete unconnected customers
        self.check_deleteUnconnectedCustomers =QCheckBox("Delete unconnected customers")
        
        #delete unconnected network lines
        self.check_deleteUnconnectedLines =QCheckBox("Delete unconnected lines")
        
        #redraw submodel polygon including all streets
        self.redraw_submodels_polygons =QCheckBox("Redraw submodel polygon including all features and lines & set submodel to 1")
        self.redraw_submodels_polygons.setChecked(True)
        
        #tolerance
        layout_tolarance=QHBoxLayout()
        label=QLabel('Snapping tolerance, m: ')
        layout_tolarance.addWidget(label)
        self.tolerance=QLineEdit('0.01')
        layout_tolarance.addWidget(self.tolerance)
        
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
        layout_overrideAssettype = QHBoxLayout()
        layout_overrideAssettype.addLayout(layout_overrideAssettype_label)
        layout_overrideAssettype.addLayout(layout_overrideAssettype_input)  
        
        layout_addCustomers_assettype = QHBoxLayout()
        layout_addCustomers_assettype.addLayout(layout_addCustomers_assettype_label)
        layout_addCustomers_assettype.addLayout(layout_addCustomers_assettype_input) 
        
        layout_connectCustomers_assettype = QHBoxLayout()
        layout_connectCustomers_assettype.addLayout(layout_connectCustomers_assettype_label)
        layout_connectCustomers_assettype.addLayout(layout_connectCustomers_assettype_input) 
        
        layout_connectPlants_assettype = QHBoxLayout()
        layout_connectPlants_assettype.addLayout(layout_connectPlants_assettype_label)
        layout_connectPlants_assettype.addLayout(layout_connectPlants_assettype_input) 
        
        layout_additional_options.addWidget(self.check_del_network_ends)
        layout_additional_options.addWidget(self.check_add_customers_network_ends)
        layout_additional_options.addLayout(layout_addCustomers_assettype)
        layout_additional_options.addWidget(self.check_connectPlants)
        layout_additional_options.addLayout(layout_connectPlants_assettype)
        layout_additional_options.addWidget(self.check_connectCustomers)
        layout_additional_options.addLayout(layout_connectCustomers_assettype)
        layout_additional_options.addWidget(self.check_deleteUnconnectedCustomers)
        layout_additional_options.addWidget(self.check_deleteUnconnectedLines)
        layout_additional_options.addWidget(self.redraw_submodels_polygons)
        
        layout_win = QVBoxLayout()
        layout_win.addWidget(self.rbtn_keep_assettypes)
        layout_win.addWidget(self.rbtn_override_assettypes)
        layout_win.addLayout(layout_overrideAssettype)
        layout_win.addLayout(layout_additional_options)
        layout_win.addLayout(layout_tolarance)
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
        print(self.dictDB)
        
        if self.conn:
            print(self.dictDB)
            if self.checkNetworkAttribute(self.dictDB['versionName']): 
                networks=[self.combo_network_models.itemText(i) for i in range(self.combo_network_models.count()) if self.combo_network_models.itemText(i) != 'Check all items' and self.combo_network_models.itemChecked(i)]
                
                worker = WorkerGenerateNetworkTopology(iface=self.iface,dictDB=self.dictDB,plugin_dir=self.plugin_dir, networks=networks ,redraw_submodels_polygons=self.redraw_submodels_polygons, deleteUnconnectedCustomers=self.check_deleteUnconnectedCustomers.isChecked(), deleteUnconnectedLines=self.check_deleteUnconnectedLines.isChecked(),
                    connectCustomers=self.check_connectCustomers.isChecked(),connectCustomers_assettype_lines=self.connectCustomers_assettype_lines.currentText(),connectCustomers_assettype_pipeBundle=self.connectCustomers_assettype_pipeBundle.currentText(),
                    addCustomers=self.check_add_customers_network_ends.isChecked(),addCustomers_assettype_customers=self.addCustomers_assettype_customers.currentText(),
                    connectPlants=self.check_connectPlants.isChecked(),connectPlants_assettype_lines=self.connectPlants_assettype_lines.currentText(),connectPlants_assettype_pipeBundle=self.connectPlants_assettype_pipeBundle.currentText(),
                    deleteUnconnectedNetworkEnds=self.check_del_network_ends.isChecked(),
                    keepAssettypes=self.rbtn_keep_assettypes.isChecked(),
                    overrideAssettypes=self.rbtn_override_assettypes.isChecked(),overrideAssettypes_customers=self.overrideAssettype_customer.currentText(), overrideAssettypes_lines=self.overrideAssettype_lines.currentText(),overrideAssettypes_pipeBundle=self.overrideAssettype_pipeBundle.currentText(),tolerance=self.tolerance.text())
                self.threadpool.start(worker) 
                worker.signals.error.connect(self.show_error_message)
                worker.signals.progress.connect(self.update_progress)

    def checkNetworkAttribute(self,version):
        sql="""SELECT count(*) FROM "{}".lines WHERE network IS NULL;""".format(version)
        self.cur.execute(sql)
        networkNullCount=self.cur.fetchone()['count']
        if networkNullCount>0:
            print('Network attribute not set!')

            dlg_question = QMessageBox(self)
            dlg_question.setWindowTitle('Network attribute value missing!')
            dlg_question.setText("""{} network attribute(s) in lines are not set. Should the attribute(s) be set to 1?""".format(networkNullCount))
            dlg_question.setStandardButtons(QMessageBox.Yes | QMessageBox.Cancel)
            dlg_question.setIcon(QMessageBox.Question)
            button = dlg_question.exec()

            if button == QMessageBox.Yes:
                sql="""UPDATE "{}".lines SET network=1 WHERE network IS NULL;""".format(version)
                print(sql)
                self.cur.execute(sql)
                return True
            else:
                print("Cancel!")
                return False
        else:
            return True
                
    def update_progress(self,progress):
        self.progress.setValue(progress)
        
    def addCustomers_network_ends_state(self,s):
        print('add customers to network ends state')
        
        if Qt.Checked==s:
            print('checked')
            self.label_addCustomers_assettype_customers.setHidden(False)
            self.addCustomers_assettype_customers.setHidden(False)
        else:
            print('unchecked')
            self.label_addCustomers_assettype_customers.setHidden(True)
            self.addCustomers_assettype_customers.setHidden(True)
            
    def connectCustomers_state(self,s):
        print('connect customers to network state')
        
        if Qt.Checked==s:
            print('checked')
            self.label_connectCustomers_assettype_lines.setHidden(False)
            self.label_connectCustomers_assettype_pipeBundle.setHidden(False)
            self.connectCustomers_assettype_lines.setHidden(False)
            self.connectCustomers_assettype_pipeBundle.setHidden(False)
        else:
            print('unchecked')
            self.label_connectCustomers_assettype_lines.setHidden(True)
            self.label_connectCustomers_assettype_pipeBundle.setHidden(True)
            self.connectCustomers_assettype_lines.setHidden(True)
            self.connectCustomers_assettype_pipeBundle.setHidden(True)
            
    def connectPlants_state(self,s):
        print('connect plants to network state')
        
        if Qt.Checked==s:
            print('checked')
            self.label_connectPlants_assettype_lines.setHidden(False)
            self.label_connectPlants_assettype_pipeBundle.setHidden(False)
            self.connectPlants_assettype_lines.setHidden(False)
            self.connectPlants_assettype_pipeBundle.setHidden(False)
        else:
            print('unchecked')
            self.label_connectPlants_assettype_lines.setHidden(True)
            self.label_connectPlants_assettype_pipeBundle.setHidden(True)
            self.connectPlants_assettype_lines.setHidden(True)
            self.connectPlants_assettype_pipeBundle.setHidden(True)
            
    def override_assettype_state(self,s):
        print('override assettype state')
        if True==s:
            print('checked')
            self.label_overrideAssettype_customer.setHidden(False)
            self.label_overrideAssettype_lines.setHidden(False)
            self.label_overrideAssettype_pipeBundle.setHidden(False)
            self.overrideAssettype_customer.setHidden(False)
            self.overrideAssettype_lines.setHidden(False)
            self.overrideAssettype_pipeBundle.setHidden(False)
        else:
            print('unchecked')
            self.label_overrideAssettype_customer.setHidden(True)
            self.label_overrideAssettype_lines.setHidden(True)
            self.label_overrideAssettype_pipeBundle.setHidden(True)
            self.overrideAssettype_customer.setHidden(True)
            self.overrideAssettype_lines.setHidden(True)
            self.overrideAssettype_pipeBundle.setHidden(True)
       
    def keep_assettype_state(self,s):
        print('keep assettype state')
        if True==s:
            print('checked')
            self.label_overrideAssettype_customer.setHidden(True)
            self.label_overrideAssettype_lines.setHidden(True)
            self.label_overrideAssettype_pipeBundle.setHidden(True)
            self.overrideAssettype_customer.setHidden(True)
            self.overrideAssettype_lines.setHidden(True)
            self.overrideAssettype_pipeBundle.setHidden(True)
        else:
            print('unchecked')
            self.label_overrideAssettype_customer.setHidden(False)
            self.label_overrideAssettype_lines.setHidden(False)
            self.label_overrideAssettype_pipeBundle.setHidden(False)
            self.overrideAssettype_customer.setHidden(False)
            self.overrideAssettype_lines.setHidden(False)
            self.overrideAssettype_pipeBundle.setHidden(False)
    
    def saveResults(self):
        """Writes results (lines, customers, junctions) from temp schema to version schema"""
        print('save Results')

        sql=""" TRUNCATE "{}".lines, "{}".customers,"{}".energy_plants,"{}".devices,"{}".junctions,"{}".customer_connections, {}.junction_connections, "{}".energy_plant_connections, "{}".device_connections CASCADE;""".format(self.dictDB['versionName'],self.dictDB['versionName'],self.dictDB['versionName'],self.dictDB['versionName'],self.dictDB['versionName'],self.dictDB['versionName'],self.dictDB['versionName'],self.dictDB['versionName'],self.dictDB['versionName'])
        print(sql) 
        self.cur.execute(sql)  
        sql=""" INSERT INTO "{}".lines SELECT * FROM temp.lines;""".format(self.dictDB['versionName'])
        print(sql) 
        self.cur.execute(sql)  
        sql=""" INSERT INTO "{}".customers SELECT * FROM temp.customers;""".format(self.dictDB['versionName'])
        print(sql) 
        self.cur.execute(sql)  
        sql=""" INSERT INTO "{}".devices SELECT * FROM temp.devices;""".format(self.dictDB['versionName'])
        print(sql) 
        self.cur.execute(sql)  
        sql=""" INSERT INTO "{}".energy_plants SELECT * FROM temp.energy_plants;""".format(self.dictDB['versionName'])
        print(sql) 
        self.cur.execute(sql)  
        sql=""" INSERT INTO"{}".junctions SELECT * FROM temp.junctions;""".format(self.dictDB['versionName'])
        print(sql) 
        self.cur.execute(sql)  
        sql=""" INSERT INTO {}.junction_connections SELECT * FROM temp.junction_connections;""".format(self.dictDB['versionName'])
        print(sql) 
        self.cur.execute(sql)  
        sql=""" INSERT INTO "{}".customer_connections SELECT * FROM temp.customer_connections;""".format(self.dictDB['versionName'])
        print(sql) 
        self.cur.execute(sql)  
        sql=""" INSERT INTO "{}".energy_plant_connections SELECT * FROM temp.energy_plant_connections;""".format(self.dictDB['versionName'])
        print(sql) 
        self.cur.execute(sql)  
        sql=""" INSERT INTO "{}".device_connections SELECT * FROM temp.device_connections;""".format(self.dictDB['versionName'])
        print(sql) 
        self.cur.execute(sql) 
        removeLayers()
        layerTreeRoot = QgsProject.instance().layerTreeRoot()  
        iface.mapCanvas().snappingUtils().setIndexingStrategy(iface.mapCanvas().snappingUtils().IndexingStrategy.IndexExtent)
        for layer in ['lines','junctions','customers','energy_plants']:
            vlayer= QgsProject.instance().mapLayersByName(layer)
            if vlayer:
                vlayer=vlayer[0]
                layerTreeRoot.findLayer(vlayer).setItemVisibilityChecked(True)
                vlayer.emitDataChanged()
        refreshMap()
        
    def rejectResults(self):
        """Writes results (lines, customers, junctions) from temp schema to version schema"""
        print('Reject Results')
        removeLayers()
        layerTreeRoot = QgsProject.instance().layerTreeRoot()  
        for layer in ['lines','junctions','customers']:
            if QgsProject.instance().mapLayersByName(layer):
                vlayer= QgsProject.instance().mapLayersByName(layer)[0]
                layerTreeRoot.findLayer(vlayer).setItemVisibilityChecked(True)
            
    def closeEvent(self, *args, **kwargs):
        print ("you just closed the PipeLayingWindow!!!")
        self.rejectResults()
        
class MapDevicesPlantsDialog(QMainWindow):
    def __init__(self,dictDB,plugin_dir):     
        """Initialize GUI for mapping devices/plants connection types to lines id"""
        super().__init__()
        self.plugin_dir=plugin_dir
        self.dictDB=dictDB
        self.conn=dbConnect(self.dictDB,True)
        self.cur=self.conn.cursor(cursor_factory = psycopg2.extras.RealDictCursor)
        self.setWindowTitle("Map devices/energy plants/customers connection types to lines")
        myBoldFont=QtGui.QFont('Arial', 12)
        myBoldFont.setBold(True)

        #radio buttons devices/plants
        layout_rbtn = QHBoxLayout()
        self.rbtn_devices = QRadioButton('Devices')
        self.rbtn_plants = QRadioButton('Energy plants')
        self.rbtn_customers = QRadioButton('Customers')
        
        self.rbtn_devices.toggled.connect(self.updateDevicesPlantsCustomersLists)
        self.rbtn_plants.toggled.connect(self.updateDevicesPlantsCustomersLists)        
        self.rbtn_customers.toggled.connect(self.updateDevicesPlantsCustomersLists)        
        layout_rbtn.addWidget(self.rbtn_devices)
        layout_rbtn.addWidget(self.rbtn_plants)
        layout_rbtn.addWidget(self.rbtn_customers)

        ##list widgets for devices/plants; --||-- connection types; line id`s
        #list widgets input
        #lists devices/plants
        layout_devicesPlants = QVBoxLayout()
        self.label_listWidget_devicesPlants=QLabel("Devices/Plants/Customers")
        self.label_listWidget_devicesPlants.setAlignment(QtCore.Qt.AlignCenter)
        self.label_listWidget_devicesPlants.setFont(myBoldFont)
        layout_devicesPlants.addWidget(self.label_listWidget_devicesPlants)
        layout_listWidget_devicesPlants = QHBoxLayout()
        #list widget for devices/plants
        layout_listWidget_devicesPlants_ids = QVBoxLayout()
        label_listWidget_devicesPlants_ids=QLabel("Id`s")
        layout_listWidget_devicesPlants_ids.addWidget(label_listWidget_devicesPlants_ids)
        self.listWidget_devicesPlants_ids = QListWidget()
        self.listWidget_devicesPlants_ids.itemClicked.connect(self.clickedDevicesPlantsId)
        layout_listWidget_devicesPlants_ids.addWidget(self.listWidget_devicesPlants_ids)
        layout_listWidget_devicesPlants.addLayout(layout_listWidget_devicesPlants_ids)
        
        #list widget for devices/plants
        layout_listWidget_devicesPlants_connTypes = QVBoxLayout()
        label_listWidget_devicesPlants_connTypes=QLabel("Connection types")
        layout_listWidget_devicesPlants_connTypes.addWidget(label_listWidget_devicesPlants_connTypes)
        self.listWidget_devicesPlants_connTypes = QListWidget()
        layout_listWidget_devicesPlants_connTypes.addWidget(self.listWidget_devicesPlants_connTypes)
        layout_listWidget_devicesPlants.addLayout(layout_listWidget_devicesPlants_connTypes)
        
        layout_devicesPlants.addLayout(layout_listWidget_devicesPlants)
        
        #list widget for devices/plants               
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
        layout_lists_input.addLayout(layout_devicesPlants)
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
        
    def clickedDevicesPlantsId(self, item):
        print(item.text())
        table_name=self.getTypeTableName()
        print(table_name)
        #add connection type items to listWidget_devicesPlants_connTypes
        self.listWidget_devicesPlants_connTypes.clear()
        sql="""SELECT conn_b_t.conn_type_id, conn_b_t.description 
    FROM public.bundle_type_conns conn_b_t, "{}".{} b, public.{}_assettypes a
    WHERE conn_b_t.conn_bundle_type_id =a.conn_bundle_type AND b.id={} AND a.assetgroup=b.assetgroup AND a.assettype=b.assettype 
    ORDER BY conn_b_t.sequence;""".format(self.dictDB['versionName'],table_name,table_name[:-1],item.text())
        print(sql)
        self.cur.execute(sql)
        conn_ids=[]
        for conn_type in self.cur.fetchall():
            conn_ids.append(str(conn_type['conn_type_id'])+':'+conn_type['description'])
        if conn_ids:
            self.listWidget_devicesPlants_connTypes.addItems(conn_ids)
          
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
        FROM "{}".energy_plant_connections ep_conn, "{}".energy_plants ep, public.energy_plant_assettypes epa, public.bundle_type_conns conn_b_t
        WHERE ep.id={} AND ep.id=ep_conn.epid AND epa.assetgroup=ep.assetgroup AND epa.assettype=ep.assettype AND epa.conn_bundle_type=conn_b_t.conn_bundle_type_id AND conn_b_t.sequence=ep_conn.ep_seq
        ORDER BY conn_b_t.sequence;""".format(self.dictDB['versionName'],self.dictDB['versionName'],id)
            print(sql)
        elif table_name=='devices':
            sql="""SELECT conn_b_t.sequence AS sequence, CONCAT(conn_b_t.conn_type_id, ':', conn_b_t.description, '  -->  ', d_conn.lid) AS connection
    FROM "{}".device_connections d_conn, "{}".devices d, public.device_assettypes da, public.bundle_type_conns conn_b_t
    WHERE d.id={} AND d.id=d_conn.did AND da.assetgroup=d.assetgroup AND da.assettype=d.assettype  AND da.conn_bundle_type=conn_b_t.conn_bundle_type_id AND conn_b_t.sequence=d_conn.d_seq 
    ORDER BY conn_b_t.sequence;""".format(self.dictDB['versionName'],self.dictDB['versionName'],id)
        elif table_name=='customers':
            sql="""SELECT conn_b_t.sequence AS sequence, CONCAT(conn_b_t.conn_type_id, ':', conn_b_t.description, '  -->  ', c_conn.lid) AS connection
    FROM "{}".customer_connections c_conn, "{}".customers c, public.customer_assettypes ca, public.bundle_type_conns conn_b_t
    WHERE c.id={} AND c.id=c_conn.cid AND ca.assetgroup=c.assetgroup AND ca.assettype=c.assettype AND ca.conn_bundle_type=conn_b_t.conn_bundle_type_id AND conn_b_t.sequence=c_conn.c_seq 
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
            item.setFlags(QtCore.Qt.ItemIsEnabled)
            self.tableWidget.setItem(rowPosition,0,item)
            item=QTableWidgetItem(conn['connection'])
            item.setFlags(QtCore.Qt.ItemIsEnabled)
            self.tableWidget.setItem(rowPosition,1,item)
            rowPosition+=1
        
    def getTypeTableName(self):
        """ return the table name: devide or plant from the sender"""
        print(self.rbtn_devices.isChecked())
        if self.rbtn_devices.isChecked()==True:
            return 'devices'
        elif self.rbtn_plants.isChecked()==True:
            return 'energy_plants'
        elif self.rbtn_customers.isChecked()==True:
            return 'customers'
                 
    def updateDevicesPlantsCustomersLists(self,s):
        """Update the list of devices, plants or customer based on the radio button """
        print('Update devices/plants list')
        print(self.sender())
        if self.sender()==self.rbtn_devices:
            table='devices'
            text='Devices'
        elif self.sender()==self.rbtn_plants:
            table='energy_plants'
            text='Energy plants'
        elif self.sender()==self.rbtn_customers:
            table='customers'
            text='Customers'
        self.label_listWidget_devicesPlants.setText(text)
        sql='SELECT array_agg(id::TEXT ORDER BY id) AS ids FROM "{}".{};'.format(self.dictDB['versionName'],table)
        print(sql)
        self.cur.execute(sql)
        ids=self.cur.fetchone()['ids']
        print(ids)
        self.listWidget_devicesPlants_ids.clear()
        self.listWidget_devicesPlants_connTypes.clear()
        self.listWidget_lines.clear()
        self.tableWidget.setRowCount(0)
        if ids:
            self.listWidget_devicesPlants_ids.addItems(ids)
            
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
        id=self.listWidget_devicesPlants_ids.currentItem()
        conn_type=self.listWidget_devicesPlants_connTypes.currentItem()
        lid=self.listWidget_lines.currentItem()
        if self.checkListSelection(id,conn_type,lid):
            id,conn_type,lid=self.checkListSelection(id,conn_type,lid)
        else:
            return
        seq=self.listWidget_devicesPlants_connTypes.currentRow()+1
        print(seq)
        if seq:
            if table_name=="energy_plants":
                sql="""SELECT count(*) FROM "{}".energy_plant_connections WHERE lid={} AND epid={} AND ep_seq={};""".format(self.dictDB['versionName'],lid,id,seq)
            elif table_name=="devices":
                sql="""SELECT count(*) FROM "{}".device_connections WHERE lid={} AND did={} AND d_seq={};""".format(self.dictDB['versionName'],lid,id,seq)
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
                    elif table_name=="devices":
                        sql="""INSERT INTO "{}".device_connections (did,d_seq,lid) VALUES({},{},{});""".format(self.dictDB['versionName'],id,seq,lid)
                    elif table_name=="customers":
                        sql="""INSERT INTO "{}".customer_connections (cid,c_seq,lid) VALUES({},{},{});""".format(self.dictDB['versionName'],id,seq,lid)
                    
                    print(sql)
                    self.cur.execute(sql)
                    self.updateConnections(table_name,id)    
     
    def getConnTypeSeq(self,table_name,id,conn_type):
        """get the sequence of the connection type in the connection bundle """
        sql="""SELECT conn_b_t.sequence
    FROM public.bundle_type_conns conn_b_t, "{}".{} a, public.{}_assettypes b 
    WHERE a.id={} AND b.assetgroup=a.assetgroup AND b.assettype=a.assettype AND b.conn_bundle_type=conn_b_t.conn_bundle_type_id AND conn_b_t.conn_type_id={}
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
        id=self.listWidget_devicesPlants_ids.currentItem().text()
        conn_type=conn.split(':')[0]
        lid=conn.split('-->  ')[1]
        
        seq=self.getConnTypeSeq(table_name,id,conn_type)
        if table_name=="energy_plants":
            sql="""DELETE FROM "{}".energy_plant_connections WHERE lid={} AND epid={} AND ep_seq={};""".format(self.dictDB['versionName'],lid,id,seq)
        elif table_name=="devices":
            sql="""DELETE FROM "{}".device_connections WHERE lid={} AND did={} AND d_seq={};""".format(self.dictDB['versionName'],lid,id,seq)
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
        elif dlg.rbtn_device.isChecked():
            layer_name='devices'
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
        currentLayerAttribute='|'+currentLayerAttribute.text()+'|'
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
        item.setFlags(QtCore.Qt.ItemIsEnabled)
        dlg.tableWidget.setItem(rowPosition,1,item)
        item=QTableWidgetItem(currentLayer_attribute)
        item.setFlags(QtCore.Qt.ItemIsEnabled)
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

        self.setWindowTitle("Import Plants, Devices or Customers From Layer")
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

        self.rbtn_device = QRadioButton('Device')
        layout_radio_type.addWidget(self.rbtn_device)
        self.btngroup_type.addButton(self.rbtn_device)
        self.rbtn_device.toggled.connect(lambda: setDHCLayerListAttributes(self,'point'))
        
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
            item.setFlags(QtCore.Qt.ItemIsEnabled)
            self.tableWidget.setItem(i,1,item)
            item=QTableWidgetItem(self.pipe_bundle_type_attributes[i])
            item.setFlags(QtCore.Qt.ItemIsEnabled)
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
                item.setFlags(QtCore.Qt.ItemIsEnabled)
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
                    self.mappedAttributes[table.item(table_index,2).text()]=self.mappedAttributes[table.item(table_index,2).text()]+'|'+s.text()+'|'
                    table.setItem(table_index,0,QTableWidgetItem(self.mappedAttributes[table.item(table_index,2).text()]))
                else:
                    iface.messageBar().pushMessage("Info", "This attribut cannot be mapped. Please enter an integer number.", level=Qgis.Info)
            else:
                seq_constr=table.item(table_index,0).text()
                material=table.cellWidget(table_index, 1).currentText()
                try:
                    self.mappedAttributes['layer_constr'][seq_constr]=[material, self.mappedAttributes['layer_constr'][seq_constr][1]+'|'+s.text()+'|']
                except:
                    self.mappedAttributes['layer_constr'][seq_constr]=[material, '|'+s.text()+'|']
                table.setItem(table_index,2,QTableWidgetItem(self.mappedAttributes['layer_constr'][seq_constr][1]))
        else:
            iface.messageBar().pushMessage("Info", "No pipe bundle type attribute selected!", level=Qgis.Info)

class PipeSizing(QMainWindow):
    def __init__(self,dictDB,plugin_dir,cur):     
        """Initialize GUI to Import Network Topology From Point Layer"""
        super().__init__()
        self.plugin_dir=plugin_dir
        self.dictDB=dictDB
        self.conn=dbConnect(self.dictDB,True)
        self.cur=self.conn.cursor(cursor_factory = psycopg2.extras.RealDictCursor)
        self.pipes={}
        self.new_pipe_bundles=[]
        
        
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

        layout_label.addWidget(QLabel("Networks"))
        
        
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
        
        self.combo_network_models = CheckableComboBox()     
        self.combo_network_models.addItem('Check all items')
        networks=getNetworks(cur,dictDB)
        self.combo_network_models.addItems(networks)  
        for i in range(len(networks)):
            self.combo_network_models.setItemChecked(i+1,False)        
        layout_values.addWidget(self.combo_network_models)        
    

        layout_inputs = QHBoxLayout()
        layout_inputs.addLayout(layout_label)
        layout_inputs.addLayout(layout_values)
        
                
        #list of considered pipes
        label_pipes_list =QLabel("Check considered pipes")
        self.pipes_list=QListWidget()
          
        #buttons       
        #save reject buttons
        layout_buttons = QHBoxLayout()
        
        self.btn_start=QPushButton("Start")
        layout_buttons.addWidget(self.btn_start)
        
        self.btn_save=QPushButton("Save")
        layout_buttons.addWidget(self.btn_save)
        
        self.btn_reject=QPushButton("Reject")
        layout_buttons.addWidget(self.btn_reject)
        
        
        #set layouts together
        layout_win = QVBoxLayout()
        layout_win.addLayout(layout_inputs)
        layout_win.addWidget(label_pipes_list)
        layout_win.addWidget(self.pipes_list)
        layout_win.addLayout(layout_buttons)
        
        widget=QWidget()
        widget.setLayout(layout_win)
        self.setCentralWidget(widget)
        
    def closeEvent(self, *args, **kwargs):
        print ("you just closed the PipeSizingWindow!!!")
        rejectPipeSizingResults(self.dictDB,self.conn,self)