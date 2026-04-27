from qgis.utils import iface
from qgis.PyQt import uic
from qgis.PyQt import QtWidgets
from qgis.PyQt.QtCore import Qt
from qgis.PyQt.QtWidgets import QStatusBar,QDialog,QSpacerItem,QGroupBox, QButtonGroup,QSpinBox,QShortcut,QListWidgetItem,QListWidget, QTabWidget, QTableWidgetItem,QTableWidget,QTreeView,QPushButton,QHBoxLayout,QVBoxLayout,QLabel,QLineEdit,QCheckBox,QComboBox, QProgressBar, QCheckBox,QRadioButton
from qgis.PyQt import QtCore,QtGui
from qgis.PyQt.QtGui import QIcon

from .utility_functions.dialog import *
from .utility_functions.files import *
from .utility_functions.db import *

import os
import psycopg2
import psycopg2.extras
from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT
from qgis.utils import iface
from qgis.core import Qgis
from qgis.PyQt.QtGui import QKeySequence
import matplotlib.pyplot as plt      
        
class SensorSignalsDialog(QDialog):
    def __init__(self,config,plugin_dir,dlg_main):     
        """Initialize GUI for sensor signals"""
        super().__init__()
        self.plugin_dir=plugin_dir
        self.config=config
        self.conn=dbConnect(self.config,True)
        self.cur=self.conn.cursor(cursor_factory = psycopg2.extras.RealDictCursor)
        self.process_running=False
        self.dlg_main=dlg_main
        self.setWindowTitle(self.tr("sensor_signals_dlg"))
        myBoldFont=QtGui.QFont('Arial', 12)
        myBoldFont.setBold(True)

        #action buttons     
        layout_action_buttons = QHBoxLayout()
        self.btn_add=QPushButton("")
        self.btn_add.setIcon(QIcon(":/images/themes/default/symbologyAdd.svg"))

        layout_action_buttons.addWidget(self.btn_add)
        self.btn_del=QPushButton("")
        self.btn_del.setIcon(QIcon(":/images/themes/default/symbologyRemove.svg"))
        
        layout_action_buttons.addWidget(self.btn_del)
        layout_action_buttons.addItem(QSpacerItem(0,0,QSizePolicy.Policy.Expanding,QSizePolicy.Policy.Minimum))
        
        #source
        label_source =QLabel(self.tr("sensor_source"))
        label_source.setFont(myBoldFont)
        
        #table
        self.tableWidget_source = QTableWidget(0,9)   
        self.tableWidget_source.setHorizontalHeaderLabels([self.tr('sensor_id'),self.tr('type'),self.tr('templates'),self.tr('connection_types'),self.tr('connections'),self.tr('measure'),self.tr('apply_function'),self.tr('test_value'),self.tr('description')])     
        
        #target
        label_target =QLabel(self.tr("sensor_target"))
        label_target.setFont(myBoldFont)
        
        #table
        self.tableWidget_target = QTableWidget(0,4)   
        self.tableWidget_target.setHorizontalHeaderLabels([self.tr('sensor_id'),self.tr('type'),self.tr('templates'),self.tr('description')])     
        
        #buttons     
        layout_buttons = QHBoxLayout()
        self.btn_ok=QPushButton(self.tr("ok"))
        layout_buttons.addWidget(self.btn_ok)
        self.btn_cancel=QPushButton(self.tr("cancel"))
        layout_buttons.addWidget(self.btn_cancel)
        
        #progress bar
        self.progress=QProgressBar()
        
        #set layouts together        
        layout_win = QVBoxLayout()
        layout_win.addLayout(layout_action_buttons)
        layout_win.addWidget(label_source)
        layout_win.addWidget(self.tableWidget_source)
        layout_win.addWidget(label_target)
        layout_win.addWidget(self.tableWidget_target)
        layout_win.addLayout(layout_buttons)
        layout_win.addWidget(self.progress)
        layout_win.addStretch()
        
        self.setLayout(layout_win)

    def update_progress(self,progress):
        self.progress.setValue(progress)

    def update_finished(self,message):
        closeDialog(self)
        self.dlg_main.statusMessage.setText(message)
        self.process_running=False

class RequestedOutputsDialog(QDialog):
    def __init__(self,requestedOutputs):
        """Constructor."""
        super().__init__()
        self.setWindowTitle(self.tr("requested_outputs")) 
        self.process_running=False
        self.requestedOutputs_old=requestedOutputs.copy()
        
        #------------------temporal results----------------------
        #titel
        label_temporal =QLabel(self.tr("temporal_results"))
        font=label_temporal.font()
        font.setPointSize(15)
        label_temporal.setFont(font)
        
        #--Customers--
        #titel
        label_customer_title =QLabel(self.tr("customers"))
        font=label_customer_title.font()
        font.setPointSize(12)
        label_customer_title.setFont(font)
        
        #checkbox for drop old features
        layout_customer_checkbox = QVBoxLayout()      
        
        self.checkBoxSubstationPower=QCheckBox(self.tr("substation_power"))
        if requestedOutputs['power_c']:
            self.checkBoxSubstationPower.setChecked(True)
        self.checkBoxSubstationConnTemp=QCheckBox(self.tr("substation_connection_temperatures"))
        if requestedOutputs['temp_c']:
            self.checkBoxSubstationConnTemp.setChecked(True)
        self.checkBoxSubstationPressure=QCheckBox(self.tr("substation_pressure"))
        if requestedOutputs['p_c']:
            self.checkBoxSubstationPressure.setChecked(True)
        self.checkBoxSubstationMassflow=QCheckBox(self.tr("substation_massflow"))
        if requestedOutputs['mdot_c']:
            self.checkBoxSubstationMassflow.setChecked(True)
        self.checkBoxSubstationHeatbalance=QCheckBox(self.tr("heat_balance_building"))
        if requestedOutputs['heatbalance_c']:
            self.checkBoxSubstationHeatbalance.setChecked(True)
        self.checkBoxSubstationTair=QCheckBox(self.tr("room_air_temperature"))
        if requestedOutputs['troom_c']:
            self.checkBoxSubstationTair.setChecked(True)
        layout_customer_checkbox.addWidget(self.checkBoxSubstationPower)
        layout_customer_checkbox.addWidget(self.checkBoxSubstationConnTemp)
        layout_customer_checkbox.addWidget(self.checkBoxSubstationPressure)
        layout_customer_checkbox.addWidget(self.checkBoxSubstationMassflow)
        layout_customer_checkbox.addWidget(self.checkBoxSubstationHeatbalance)
        layout_customer_checkbox.addWidget(self.checkBoxSubstationTair)
        
        #------------------Network----------------------
        #titel
        label_network_title =QLabel(self.tr("network"))
        font=label_network_title.font()
        font.setPointSize(12)
        label_network_title.setFont(font)
        
        #checkboxes 
        layout_network_checkbox = QVBoxLayout()      
        #print(requestedOutputs)
        self.checkBoxMdotNode=QCheckBox(self.tr("massflows_pipes"))
        if requestedOutputs['mdot_lines']:
            self.checkBoxMdotNode.setChecked(True)
        self.checkBoxVPipe=QCheckBox(self.tr("velocity_pipes"))
        if requestedOutputs['v_lines']:
            self.checkBoxVPipe.setChecked(True)
        self.checkBoxPressureDistribution=QCheckBox(self.tr("pressure_distribution"))
        if requestedOutputs['p_lines']:
            self.checkBoxPressureDistribution.setChecked(True)
        self.checkBoxTempPipe=QCheckBox(self.tr("temperature_pipes"))
        if requestedOutputs['temp_lines']:
            self.checkBoxTempPipe.setChecked(True)
        self.checkBoxQambPipe=QCheckBox(self.tr("qamb_pipes"))
        if requestedOutputs['qamb_lines']:
            self.checkBoxQambPipe.setChecked(True)
            
        layout_network_checkbox.addWidget(self.checkBoxPressureDistribution)
        layout_network_checkbox.addWidget(self.checkBoxMdotNode)
        layout_network_checkbox.addWidget(self.checkBoxVPipe)
        layout_network_checkbox.addWidget(self.checkBoxTempPipe)
        layout_network_checkbox.addWidget(self.checkBoxQambPipe)
        layout_network_checkbox.addItem(QSpacerItem(0, 0, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Expanding))


        #------------------System----------------------
        #titel
        label_system_title =QLabel(self.tr("system"))
        font=label_system_title.font()
        font.setPointSize(12)
        label_system_title.setFont(font)
        
        #checkboxes 
        layout_system_checkbox = QVBoxLayout()  
        self.heatbalance_system=QCheckBox(self.tr("heatbalance_system"))
        if requestedOutputs['heatbalance_system']:
            self.heatbalance_system.setChecked(True)
        self.massbalance_system=QCheckBox(self.tr("massbalance_system"))
        if requestedOutputs['massbalance_system']:
            self.massbalance_system.setChecked(True)

        self.checkBoxMeanSupplyTempCSystem=QCheckBox(self.tr("mean_supply_temp_customer"))
        if requestedOutputs['tsup_mean_c_system']:
            self.checkBoxMeanSupplyTempCSystem.setChecked(True)
        self.checkBoxMaxSupplyTempCSystem=QCheckBox(self.tr("maximum_supply_temp_customer"))
        if requestedOutputs['tsup_max_c_system']:
            self.checkBoxMaxSupplyTempCSystem.setChecked(True)
        self.checkBoxMinSupplyTempCSystem=QCheckBox(self.tr("minimum_supply_temp_customer"))
        if requestedOutputs['tsup_min_c_system']:
            self.checkBoxMinSupplyTempCSystem.setChecked(True)
        self.checkBoxMeanSupplyTempEpSystem=QCheckBox(self.tr("mean_supply_temp_plant"))
        if requestedOutputs['tsup_mean_ep_system']:
            self.checkBoxMeanSupplyTempEpSystem.setChecked(True)
        self.checkBoxMaxSupplyTempEpSystem=QCheckBox(self.tr("maximum_supply_temp_plant"))
        if requestedOutputs['tsup_max_ep_system']:
            self.checkBoxMaxSupplyTempEpSystem.setChecked(True)
        self.checkBoxMinSupplyTempEpSystem=QCheckBox(self.tr("minimum_supply_temp_plant"))
        if requestedOutputs['tsup_min_ep_system']:
            self.checkBoxMinSupplyTempEpSystem.setChecked(True)
        self.checkBoxMeanReturnTempCSystem=QCheckBox(self.tr("mean_return_temp_customer"))
        if requestedOutputs['tret_mean_c_system']:
            self.checkBoxMeanReturnTempCSystem.setChecked(True)
        self.checkBoxMaxReturnTempCSystem=QCheckBox(self.tr("maximum_return_temp_customer"))
        if requestedOutputs['tret_max_c_system']:
            self.checkBoxMaxReturnTempCSystem.setChecked(True)
        self.checkBoxMinReturnTempCSystem=QCheckBox(self.tr("minimum_retrun_temp_customer"))
        if requestedOutputs['tret_min_c_system']:
            self.checkBoxMinReturnTempCSystem.setChecked(True)
        self.checkBoxMeanReturnTempEpSystem=QCheckBox(self.tr("mean_return_temp_plant"))
        if requestedOutputs['tret_mean_ep_system']:
            self.checkBoxMeanReturnTempEpSystem.setChecked(True)
        self.checkBoxMaxReturnTempEpSystem=QCheckBox(self.tr("maximum_return_temp_plant"))
        if requestedOutputs['tret_max_ep_system']:
            self.checkBoxMaxReturnTempEpSystem.setChecked(True)
        self.checkBoxMinReturnTempEpSystem=QCheckBox(self.tr("minimum_return_temp_plant"))
        if requestedOutputs['tret_min_ep_system']:
            self.checkBoxMinReturnTempEpSystem.setChecked(True)
            
        layout_system_checkbox.addWidget(self.heatbalance_system)
        layout_system_checkbox.addWidget(self.massbalance_system)
        layout_system_checkbox.addWidget(self.checkBoxMeanSupplyTempCSystem)
        layout_system_checkbox.addWidget(self.checkBoxMaxSupplyTempCSystem)
        layout_system_checkbox.addWidget(self.checkBoxMinSupplyTempCSystem)
        layout_system_checkbox.addWidget(self.checkBoxMeanSupplyTempEpSystem)
        layout_system_checkbox.addWidget(self.checkBoxMaxSupplyTempEpSystem)
        layout_system_checkbox.addWidget(self.checkBoxMinSupplyTempEpSystem)
        layout_system_checkbox.addWidget(self.checkBoxMeanReturnTempCSystem)
        layout_system_checkbox.addWidget(self.checkBoxMaxReturnTempCSystem)
        layout_system_checkbox.addWidget(self.checkBoxMinReturnTempCSystem)
        layout_system_checkbox.addWidget(self.checkBoxMeanReturnTempEpSystem)
        layout_system_checkbox.addWidget(self.checkBoxMaxReturnTempEpSystem)
        layout_system_checkbox.addWidget(self.checkBoxMinReturnTempEpSystem)
        
        #------------------Energy plants----------------------
        #titel
        label_plants_title =QLabel(self.tr("energy_plants"))
        font=label_plants_title.font()
        font.setPointSize(12)
        label_plants_title.setFont(font)
        
        #checkbox for drop old features
        layout_plants_checkbox = QVBoxLayout()      
        
        self.checkBoxPlantPower=QCheckBox(self.tr("plant_power"))
        if requestedOutputs['power_ep']:
            self.checkBoxPlantPower.setChecked(True)
        self.checkBoxPlantConnTemp=QCheckBox(self.tr("plant_connection_temp"))
        if requestedOutputs['temp_ep']:
            self.checkBoxPlantConnTemp.setChecked(True)
        self.checkBoxPlantPressure=QCheckBox(self.tr("plant_pressure"))
        if requestedOutputs['p_ep']:
            self.checkBoxPlantPressure.setChecked(True)
        self.checkBoxPlantMassflow=QCheckBox(self.tr("plant_massflow"))
        if requestedOutputs['mdot_ep']:
            self.checkBoxPlantMassflow.setChecked(True)
        layout_plants_checkbox.addWidget(self.checkBoxPlantPower)
        layout_plants_checkbox.addWidget(self.checkBoxPlantConnTemp)
        layout_plants_checkbox.addWidget(self.checkBoxPlantPressure)
        layout_plants_checkbox.addWidget(self.checkBoxPlantMassflow)
        layout_plants_checkbox.addItem(QSpacerItem(0, 0, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Expanding))

        
        #------------------KPI`s----------------------
        #titel
        label_kpi_title =QLabel(self.tr("kpi_s"))
        font=label_kpi_title.font()
        font.setPointSize(15)
        label_kpi_title.setFont(font)
        
        layout_outputs_kpi_c = QVBoxLayout()
        layout_outputs_kpi_ep = QVBoxLayout()
        layout_outputs_kpi_lines_system = QVBoxLayout()
        
        #customer
        #title
        label_customer_title_ =QLabel(self.tr("customers"))
        font=label_customer_title_.font()
        font.setPointSize(12)
        label_customer_title_.setFont(font)
        layout_outputs_kpi_c.addWidget(label_customer_title_)
        
        self.checkBoxMeanSupplyTempC=QCheckBox(self.tr("mean_supply_temp"))
        if requestedOutputs['tsup_mean_c_kpi']:
            self.checkBoxMeanSupplyTempC.setChecked(True)
        self.checkBoxMaxSupplyTempC=QCheckBox(self.tr("maximum_supply_temp"))
        if requestedOutputs['tsup_max_c_kpi']:
            self.checkBoxMaxSupplyTempC.setChecked(True)
        self.checkBoxMinSupplyTempC=QCheckBox(self.tr("minimum_supply_temp"))
        if requestedOutputs['tsup_min_c_kpi']:
            self.checkBoxMinSupplyTempC.setChecked(True)
        self.checkBoxMeanRetTempC=QCheckBox(self.tr("mean_return_temp"))
        if requestedOutputs['tret_mean_c_kpi']:
            self.checkBoxMeanRetTempC.setChecked(True)
        self.checkBoxMaxRetTempC=QCheckBox(self.tr("maximum_return_temp"))
        if requestedOutputs['tret_max_c_kpi']:
            self.checkBoxMaxRetTempC.setChecked(True)
        self.checkBoxMinRetTempC=QCheckBox(self.tr("minimum_return_temp"))
        if requestedOutputs['tret_min_c_kpi']:
            self.checkBoxMinRetTempC.setChecked(True)
        
        self.checkBoxQsupHeatC=QCheckBox(self.tr("qsup_heat"))
        if requestedOutputs['qsup_heat_c_kpi']:
            self.checkBoxQsupHeatC.setChecked(True)
        self.checkBoxQsupColdC=QCheckBox(self.tr("qsup_cold"))
        if requestedOutputs['qsup_cold_c_kpi']:
            self.checkBoxQsupColdC.setChecked(True)
        self.checkBoxQsupEnergyC=QCheckBox(self.tr("qsup_energy"))
        if requestedOutputs['qsup_c_kpi']:
            self.checkBoxQsupEnergyC.setChecked(True)
        
        #self.checkBoxDpMinC=QCheckBox(self.tr("dp_min"))
        #if requestedOutputs['dpmin_c_kpi']:
        #    self.checkBoxDpMinC.setChecked(True)
        
        layout_outputs_kpi_c.addWidget(self.checkBoxMeanSupplyTempC)
        layout_outputs_kpi_c.addWidget(self.checkBoxMaxSupplyTempC)
        layout_outputs_kpi_c.addWidget(self.checkBoxMinSupplyTempC)
        layout_outputs_kpi_c.addWidget(self.checkBoxMeanRetTempC)
        layout_outputs_kpi_c.addWidget(self.checkBoxMaxRetTempC)
        layout_outputs_kpi_c.addWidget(self.checkBoxMinRetTempC)

        layout_outputs_kpi_c.addWidget(self.checkBoxQsupHeatC)
        layout_outputs_kpi_c.addWidget(self.checkBoxQsupColdC)
        layout_outputs_kpi_c.addWidget(self.checkBoxQsupEnergyC)

        #layout_outputs_kpi_c.addWidget(self.checkBoxDpMinC)
        layout_outputs_kpi_c.addItem(QSpacerItem(0, 0, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Expanding))


        #Energy plant
        #titel
        label_plants_title_ =QLabel(self.tr("energy_plants"))
        font=label_plants_title_.font()
        font.setPointSize(12)
        label_plants_title_.setFont(font)
        layout_outputs_kpi_ep.addWidget(label_plants_title_)
        self.checkBoxMeanSupplyTempEp=QCheckBox(self.tr("mean_supply_temp"))
        if requestedOutputs['tsup_mean_ep_kpi']:
            self.checkBoxMeanSupplyTempEp.setChecked(True)
        self.checkBoxMaxSupplyTempEp=QCheckBox(self.tr("maximum_supply_temp"))
        if requestedOutputs['tsup_max_ep_kpi']:
            self.checkBoxMaxSupplyTempEp.setChecked(True)
        self.checkBoxMinSupplyTempEp=QCheckBox(self.tr("minimum_supply_temp"))
        if requestedOutputs['tsup_min_ep_kpi']:
            self.checkBoxMinSupplyTempEp.setChecked(True)
        self.checkBoxMeanRetTempEp=QCheckBox(self.tr("mean_return_temp"))
        if requestedOutputs['tret_mean_ep_kpi']:
            self.checkBoxMeanRetTempEp.setChecked(True)
        self.checkBoxMaxRetTempEp=QCheckBox(self.tr("maximum_return_temp"))
        if requestedOutputs['tret_max_ep_kpi']:
            self.checkBoxMaxRetTempEp.setChecked(True)
        self.checkBoxMinRetTempEp=QCheckBox(self.tr("minimum_return_temp"))
        if requestedOutputs['tret_min_ep_kpi']:
            self.checkBoxMinRetTempEp.setChecked(True)
        
        self.checkBoxQsupHeatEp=QCheckBox(self.tr("qsup_heat"))
        if requestedOutputs['qsup_heat_ep_kpi']:
            self.checkBoxQsupHeatEp.setChecked(True)
        self.checkBoxQsupColdEp=QCheckBox(self.tr("qsup_cold"))
        if requestedOutputs['qsup_cold_ep_kpi']:
            self.checkBoxQsupColdEp.setChecked(True)
        self.checkBoxQsupEnergyEp=QCheckBox(self.tr("qsup_energy"))
        if requestedOutputs['qsup_ep_kpi']:
            self.checkBoxQsupEnergyEp.setChecked(True)
        
        #self.checkBoxDpMaxEp=QCheckBox(self.tr("dp_max"))
        #if requestedOutputs['dpmax_ep_kpi']:
        #    self.checkBoxDpMaxEp.setChecked(True)

        layout_outputs_kpi_ep.addWidget(self.checkBoxMeanSupplyTempEp)
        layout_outputs_kpi_ep.addWidget(self.checkBoxMaxSupplyTempEp)
        layout_outputs_kpi_ep.addWidget(self.checkBoxMinSupplyTempEp)
        layout_outputs_kpi_ep.addWidget(self.checkBoxMeanRetTempEp)
        layout_outputs_kpi_ep.addWidget(self.checkBoxMaxRetTempEp)
        layout_outputs_kpi_ep.addWidget(self.checkBoxMinRetTempEp)

        layout_outputs_kpi_ep.addWidget(self.checkBoxQsupHeatEp)
        layout_outputs_kpi_ep.addWidget(self.checkBoxQsupColdEp)
        layout_outputs_kpi_ep.addWidget(self.checkBoxQsupEnergyEp)

        layout_outputs_kpi_ep.addItem(QSpacerItem(0, 0, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Expanding))

         
        #lines
        #title
        label_network_title_ =QLabel(self.tr("network"))
        font=label_network_title_.font()
        font.setPointSize(12)
        label_network_title_.setFont(font)
        layout_outputs_kpi_lines_system.addWidget(label_network_title_)
        
        self.checkBoxQambLines=QCheckBox(self.tr("qamb_lines"))
        if requestedOutputs['qamb_kpi']:
            self.checkBoxQambLines.setChecked(True)
        self.checkBoxVolumeLines=QCheckBox(self.tr("network_volume"))
        if requestedOutputs['volume_kpi']:
            self.checkBoxVolumeLines.setChecked(True)
            
        layout_outputs_kpi_lines_system.addWidget(self.checkBoxQambLines)
        layout_outputs_kpi_lines_system.addWidget(self.checkBoxVolumeLines)

        #System
        #titel
        label_system_title_ =QLabel(self.tr("system"))
        font=label_system_title_.font()
        font.setPointSize(12)
        label_system_title_.setFont(font)
        layout_outputs_kpi_lines_system.addWidget(label_system_title_)
        
        self.checkBoxQsupHeatSpec=QCheckBox(self.tr("specific_heat_supply"))
        if requestedOutputs['qsup_heat_spec_c_kpi']:
            self.checkBoxQsupHeatSpec.setChecked(True)
        self.checkBoxQsupColdSpec=QCheckBox(self.tr("specific_cold_supply"))
        if requestedOutputs['qsup_cold_spec_c_kpi']:
            self.checkBoxQsupColdSpec.setChecked(True)
        self.checkBoxQsupEnergySpec=QCheckBox(self.tr("specific_energy_supply"))
        if requestedOutputs['qsup_spec_c_kpi']:
            self.checkBoxQsupEnergySpec.setChecked(True)
        
        self.checkBoxQsupHeatDensity=QCheckBox(self.tr("density_heat_supply"))
        if requestedOutputs['qsup_heat_density_c_kpi']:
            self.checkBoxQsupHeatDensity.setChecked(True)
        self.checkBoxQsupColdDensity=QCheckBox(self.tr("density_cold_supply"))
        if requestedOutputs['qsup_cold_density_c_kpi']:
            self.checkBoxQsupColdDensity.setChecked(True)
        self.checkBoxQsupEnergyDensity=QCheckBox(self.tr("density_energy_supply"))
        if requestedOutputs['qsup_density_c_kpi']:
            self.checkBoxQsupEnergyDensity.setChecked(True)
        
        self.checkBoxQsupHeatLineDensity=QCheckBox(self.tr("line_density_heat_supply"))
        if requestedOutputs['qsup_heat_linedensity_c_kpi']:
            self.checkBoxQsupHeatLineDensity.setChecked(True)
        self.checkBoxQsupColdLineDensity=QCheckBox(self.tr("line_density_cold_supply"))
        if requestedOutputs['qsup_cold_linedensity_c_kpi']:
            self.checkBoxQsupColdLineDensity.setChecked(True)
        self.checkBoxQsupEnergyLineDensity=QCheckBox(self.tr("line_density_energy_supply"))
        if requestedOutputs['qsup_linedensity_c_kpi']:
            self.checkBoxQsupEnergyLineDensity.setChecked(True)
        
        self.checkBoxQEffWidth=QCheckBox(self.tr("effWidth"))
        if requestedOutputs['eff_width']:
            self.checkBoxQEffWidth.setChecked(True)
        
        layout_outputs_kpi_lines_system.addWidget(self.checkBoxQsupHeatSpec)
        layout_outputs_kpi_lines_system.addWidget(self.checkBoxQsupColdSpec)
        layout_outputs_kpi_lines_system.addWidget(self.checkBoxQsupEnergySpec)

        layout_outputs_kpi_lines_system.addWidget(self.checkBoxQsupHeatDensity)
        layout_outputs_kpi_lines_system.addWidget(self.checkBoxQsupColdDensity)
        layout_outputs_kpi_lines_system.addWidget(self.checkBoxQsupEnergyDensity)

        layout_outputs_kpi_lines_system.addWidget(self.checkBoxQsupHeatLineDensity)
        layout_outputs_kpi_lines_system.addWidget(self.checkBoxQsupColdLineDensity)
        layout_outputs_kpi_lines_system.addWidget(self.checkBoxQsupEnergyLineDensity)

        layout_outputs_kpi_lines_system.addWidget(self.checkBoxQEffWidth)
        
        #timestep for output
        layout_outputTimestep = QHBoxLayout()      
        label_outputTimestep =QLabel(self.tr("dt_output_hr"))
        self.outputTimestep=QLineEdit(requestedOutputs['dt_outputs'])
        layout_outputTimestep.addWidget(label_outputTimestep)
        layout_outputTimestep.addWidget(self.outputTimestep)
        
        #buttons     
        layout_buttons = QHBoxLayout()
        self.btn_ok=QPushButton(self.tr("ok"))
        layout_buttons.addWidget(self.btn_ok)
        self.btn_cancel=QPushButton(self.tr("cancel"))
        layout_buttons.addWidget(self.btn_cancel)
        
        #progress bar
        self.progress=QProgressBar()
        
        #---------------set layouts together-------------------
        layout_win = QVBoxLayout()
        #temporal
        layout_win.addWidget(label_temporal)
        layout_outputs_c_ep_lines = QHBoxLayout()
        layout_outputs_c_ep = QVBoxLayout()
        layout_outputs_lines = QVBoxLayout()
        layout_outputs_system = QVBoxLayout()
        
        
        layout_outputs_c_ep.addWidget(label_customer_title)
        layout_outputs_c_ep.addLayout(layout_customer_checkbox)
        layout_outputs_c_ep.addWidget(label_plants_title)
        layout_outputs_c_ep.addLayout(layout_plants_checkbox)
        layout_outputs_lines.addWidget(label_network_title)
        layout_outputs_lines.addLayout(layout_network_checkbox)
        layout_outputs_system.addWidget(label_system_title)
        layout_outputs_system.addLayout(layout_system_checkbox)
        
        layout_outputs_c_ep_lines.addLayout(layout_outputs_c_ep)
        layout_outputs_c_ep_lines.addLayout(layout_outputs_lines)
        layout_outputs_c_ep_lines.addLayout(layout_outputs_system)
           
        layout_win.addLayout(layout_outputs_c_ep_lines)
        
        #kpi
        layout_win.addWidget(label_kpi_title)
        layout_outputs_kpi = QHBoxLayout()
        layout_outputs_kpi.addLayout(layout_outputs_kpi_ep)
        layout_outputs_kpi.addLayout(layout_outputs_kpi_c)
        layout_outputs_kpi.addLayout(layout_outputs_kpi_lines_system)
        layout_win.addLayout(layout_outputs_kpi)

        layout_win.addLayout(layout_outputTimestep)
        layout_win.addLayout(layout_buttons)
        layout_win.addWidget(self.progress)
        
        self.setLayout(layout_win)
        
    def update_progress(self,progress):
        self.progress.setValue(progress)

    def update_finished(self,message):
        self.process_running=False
        closeDialog(self)

class BuildNetworkModelDialog(QDialog):
    def __init__(self,dlg_main):
        """Constructor."""
        super().__init__()
        self.setWindowTitle("Build network model") 
        self.process_running=False
        self.dlg_main=dlg_main
        
        #networks
        layout_networks=QVBoxLayout()
        label_networks =QLabel("Networks")
        font=label_networks.font()
        font.setPointSize(15)
        label_networks.setFont(font)
        self.combo_network_models = CheckableComboBox()
        layout_networks.addWidget(label_networks)
        layout_networks.addWidget(self.combo_network_models)
        
        #self.checkBoxCosim=QCheckBox("Apply decoupling")
        #self.checkBoxCosim.stateChanged.connect(self.cosim_state)
        self.label_submodels =QLabel("Submodels")
        self.label_submodels.setFont(font)
        #self.label_submodels.setHidden(True)
        #layout_networks.addWidget(self.checkBoxCosim)
        #layout_networks.addWidget(self.label_submodels)
        self.combo_submodels = CheckableComboBox()
        self.combo_submodels.addItem('1')
        self.combo_submodels.setItemChecked(0,checked=True)
        #self.combo_submodels.setHidden(True)
        #layout_networks.addWidget(self.combo_submodels)
        
        #reinvoke feature templates
        self.checkbox_reinvokeFeatures = QCheckBox("Reinvoke feature templates")
        self.checkbox_reinvokeFeatures.setChecked(True)
        
        #buttons     
        layout_buttons = QHBoxLayout()
        self.btn_buildNetworkModel=QPushButton("Build network model")
        layout_buttons.addWidget(self.btn_buildNetworkModel)
        self.btn_cancel=QPushButton("Cancel")
        layout_buttons.addWidget(self.btn_cancel)
        
        #progress bar
        self.progress=QProgressBar()
        
        #---------------set layouts together-------------------
        layout_win = QVBoxLayout()
        layout_win.addLayout(layout_networks)
        layout_win.addWidget(self.checkbox_reinvokeFeatures)
        layout_win.addLayout(layout_buttons)
        layout_win.addWidget(self.progress)
        
        self.setLayout(layout_win)
                  
    def update_progress(self,progress):
        self.progress.setValue(progress)

    def update_finished(self,message):
        self.process_running=False
        self.dlg_main.statusMessage.setText(message)
        
class BuildBuildingModelDialog(QDialog):
    def __init__(self):
        """Constructor."""
        super().__init__()
        self.setWindowTitle("Build building model") 

        layout_buttons_table = QHBoxLayout()
        self.btn_add=QPushButton("Add")
        layout_buttons_table.addWidget(self.btn_add)
        self.btn_delete=QPushButton("Delete")
        layout_buttons_table.addWidget(self.btn_delete)
        
        #Table
        layout_table = QHBoxLayout() 
        self.tableWidget = QTableWidget(0,2)
        self.tableWidget.setHorizontalHeaderLabels(['Submodel','Building template'])     
        layout_table.addWidget(self.tableWidget)
        
        #reinvoke feature templates
        self.checkbox_reinvokeFeatures = QCheckBox("Reinvoke substation templates")
        self.checkbox_reinvokeFeatures.setChecked(True)
        
        #Co-sim
        self.checkbox_cosim = QCheckBox("Co-simulation to network model")
        self.checkbox_cosim.setChecked(False)
        
        #buttons     
        layout_buttons = QHBoxLayout()
        self.btn_buildBuildingModel=QPushButton("Build building model")
        layout_buttons.addWidget(self.btn_buildBuildingModel)
        self.btn_cancel=QPushButton("Cancel")
        layout_buttons.addWidget(self.btn_cancel)
        
        #progress bar
        self.progress=QProgressBar()
        
        #---------------set layouts together-------------------
        layout_win = QVBoxLayout()
        layout_win.addLayout(layout_buttons_table)
        layout_win.addLayout(layout_table)
        layout_win.addWidget(self.checkbox_reinvokeFeatures)
        layout_win.addWidget(self.checkbox_cosim)
        layout_win.addLayout(layout_buttons)
        layout_win.addWidget(self.progress)
        
        self.setLayout(layout_win)
                  
    def update_progress(self,progress):
        self.progress.setValue(progress)

class OpenModelDialog(QDialog):
    def __init__(self,dlg_main,mode):
        """Constructor."""
        super().__init__()
        self.setWindowTitle("Open {} submodels".format(mode)) 
        self.dlg_main=dlg_main
        #submodels
        layout_submodels=QVBoxLayout()
        label_submodels =QLabel("Submodels")
        font=label_submodels.font()
        font.setPointSize(12)
        label_submodels.setFont(font)
        self.combo_submodels = CheckableComboBox()
        layout_submodels.addWidget(label_submodels)
        layout_submodels.addWidget(self.combo_submodels)
        
        #buttons     
        layout_buttons = QHBoxLayout()
        self.btn_openModel=QPushButton("Open {} submodels".format(mode))
        layout_buttons.addWidget(self.btn_openModel)
        self.btn_cancel=QPushButton("Cancel")
        layout_buttons.addWidget(self.btn_cancel)
        
        #progress bar
        self.progress=QProgressBar()
        
        #---------------set layouts together-------------------
        layout_win = QVBoxLayout()
        layout_win.addLayout(layout_submodels)
        layout_win.addLayout(layout_buttons)
        layout_win.addWidget(self.progress)
        
        self.setLayout(layout_win)
        
    def update_progress(self,progress):
        self.progress.setValue(progress)
        
    def update_finished(self,message):
        #self.process_running=False
        self.dlg_main.statusMessage.setText(message)
            
class LoadResultsDialog(QDialog):
    def __init__(self,dlg_main):
        """Constructor."""
        super().__init__()
        self.setWindowTitle("Load simulation results") 
        self.process_running=False
        self.dlg_main=dlg_main
        
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
        self.interpolation_dt.setHidden(s != checkState())
    
    def update_progress(self,progress):
        self.progress.setValue(progress)

    def update_finished(self,message):
        self.process_running=False
        self.dlg_main.statusMessage.setText(message)

        
class RunNetworkModelDialog(QDialog):
    def __init__(self,plugin_dir,config):
        """Constructor."""
        super().__init__()
        self.setWindowTitle("Run network model") 
        self.networkSimData=loadNetworkSimData(plugin_dir,config)
        #print(self.networkSimData)
        self.finished_sims=0
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
        
        #------simulation------------
        layout_simtime=QVBoxLayout()
        label_simtime =QLabel("Simulation")
        font=label_simtime.font()
        font.setPointSize(12)
        label_simtime.setFont(font)      
      
        #radio buttons calc type
        self.btngroup_calc_type = QButtonGroup()
        layout_rbtn_calc_type = QHBoxLayout()
        self.rbtn_calc_type_periodic = QRadioButton('Periodic')
        self.rbtn_calc_type_dynamic = QRadioButton('Dynamic')
        self.btngroup_calc_type.addButton(self.rbtn_calc_type_periodic)
        self.btngroup_calc_type.addButton(self.rbtn_calc_type_dynamic)
        layout_rbtn_calc_type.addWidget(self.rbtn_calc_type_periodic)
        layout_rbtn_calc_type.addWidget(self.rbtn_calc_type_dynamic)

        
        #maximal timestep
        layout_max_timestep = QHBoxLayout()
        label_max_timestep =QLabel("Maximal timestep, h")
        layout_max_timestep.addWidget(label_max_timestep)
        self.max_timestep=QLineEdit(self.networkSimData['max_timestep'])
        layout_max_timestep.addWidget(self.max_timestep)
        
        #startup time
        layout_startup = QVBoxLayout()
        self.label_startup =QLabel("Startup")
        font=self.label_startup.font()
        font.setPointSize(10)
        self.label_startup.setFont(font)
        layout_startupDate = QHBoxLayout()
        self.label_calcStartupFrom =QLabel("From")
        layout_startupDate.addWidget(self.label_calcStartupFrom)
        
        #radio buttons startup type
        self.btngroup_startup_type = QButtonGroup()
        layout_rbtn_startup_type = QHBoxLayout()
        self.rbtn_startup_type_periodic = QRadioButton('Periodic')
        self.rbtn_startup_type_dynamic = QRadioButton('Dynamic')
        self.btngroup_startup_type.addButton(self.rbtn_startup_type_periodic)
        self.btngroup_startup_type.addButton(self.rbtn_startup_type_dynamic)
        layout_rbtn_startup_type.addWidget(self.rbtn_startup_type_periodic)
        layout_rbtn_startup_type.addWidget(self.rbtn_startup_type_dynamic)
        
        self.dateedit_startupFrom = QtWidgets.QDateTimeEdit(calendarPopup=True)
        if self.networkSimData['startup_time_from']:
            date_time=self.networkSimData['startup_time_from']
        else:
            date_time=str(QtCore.QDate.currentDate().year())+'-01-01 00:00:00'
        self.dateedit_startupFrom.setDateTime(QtCore.QDateTime.fromString(date_time, 'yyyy-MM-dd hh:mm:ss'))
        self.dateedit_startupFrom.setDisplayFormat("yyyy-MM-dd hh:mm:ss")
        layout_startupDate.addWidget(self.dateedit_startupFrom)

        self.label_calcStartupTo =QLabel("To")
        layout_startupDate.addWidget(self.label_calcStartupTo)
                
        self.dateedit_startupTo = QtWidgets.QDateTimeEdit(calendarPopup=True)
        if self.networkSimData['startup_time_to']:
            date_time=self.networkSimData['startup_time_to']
        else:
            date_time=str(QtCore.QDate.currentDate().year())+'-12-31 23:59:59'
        self.dateedit_startupTo.setDateTime(QtCore.QDateTime.fromString(date_time, 'yyyy-MM-dd hh:mm:ss'))
        self.dateedit_startupTo.setDisplayFormat("yyyy-MM-dd hh:mm:ss")
        layout_startupDate.addWidget(self.dateedit_startupTo)

        layout_startup.addWidget(self.label_startup)
        layout_startup.addLayout(layout_rbtn_startup_type)
        layout_startup.addLayout(layout_startupDate)

        #number of periods
        layout_numb_periods = QHBoxLayout()
        self.label_numb_periods =QLabel("Number of periods")
        layout_numb_periods.addWidget(self.label_numb_periods)    
        self.numb_periods =QSpinBox()
        self.numb_periods.setValue(int(self.networkSimData['numb_of_periods']))
        self.numb_periods.setMinimum(1) 
        layout_numb_periods.addWidget(self.numb_periods)        

        #simulation time
        layout_calctime = QVBoxLayout()
        label_calctime =QLabel("Simulation time")
        font=label_calctime.font()
        font.setPointSize(12)
        label_calctime.setFont(font)
        
        layout_calcdate = QHBoxLayout()
        label_calcFrom =QLabel("From")
        layout_calcdate.addWidget(label_calcFrom)
                
        self.dateedit_calcFrom = QtWidgets.QDateTimeEdit(calendarPopup=True)
        if self.networkSimData['calc_time_from']:
            #print(self.networkSimData['calc_time_from'])
            date_time=self.networkSimData['calc_time_from']
        else:
            date_time=str(QtCore.QDate.currentDate().year())+'-01-01 00:00:00'
        self.dateedit_calcFrom.setDateTime(QtCore.QDateTime.fromString(date_time, 'yyyy-MM-dd hh:mm:ss'))
        self.dateedit_calcFrom.setDisplayFormat("yyyy-MM-dd hh:mm:ss")
        layout_calcdate.addWidget(self.dateedit_calcFrom)

        label_calcTo =QLabel("To")
        layout_calcdate.addWidget(label_calcTo)
                
        self.dateedit_calcTo = QtWidgets.QDateTimeEdit(calendarPopup=True)
        if self.networkSimData['calc_time_to']:
            #print(self.networkSimData['calc_time_to'])
            date_time=self.networkSimData['calc_time_to']
        else:
            date_time=str(QtCore.QDate.currentDate().year())+'-12-31 23:59:59'
        self.dateedit_calcTo.setDateTime(QtCore.QDateTime.fromString(date_time, 'yyyy-MM-dd hh:mm:ss'))
        self.dateedit_calcTo.setDisplayFormat("yyyy-MM-dd hh:mm:ss")
        layout_calcdate.addWidget(self.dateedit_calcTo)
        
        layout_calctime.addWidget(label_calctime)
        layout_calctime.addLayout(layout_calcdate)
                
        layout_simtime.addWidget(label_simtime)
        layout_simtime.addLayout(layout_max_timestep)
        layout_simtime.addLayout(layout_rbtn_calc_type)
        layout_simtime.addLayout(layout_startup)
        layout_simtime.addLayout(layout_numb_periods)
        layout_simtime.addLayout(layout_calctime)
        
        #status bar
        self.status_bar = QStatusBar()
        self.status_bar.setStyleSheet("""
    QStatusBar {
                background-color: white;
                color: black;
                border-radius: 5px;
                border: 1px solid grey;
            }
""")
        self.status_bar.showMessage("Ready")
        
        #buttons     
        layout_buttons = QHBoxLayout()
        self.btn_runModel=QPushButton("Run network submodels")
        layout_buttons.addWidget(self.btn_runModel)
        self.btn_cancel=QPushButton("Cancel")
        layout_buttons.addWidget(self.btn_cancel)
        
        #---------------set layouts together-------------------
        layout_win = QVBoxLayout()
        #layout_win.addLayout(layout_submodels)
        layout_win.addLayout(layout_simtime)
        layout_win.addLayout(layout_buttons)
        layout_win.addWidget(self.status_bar)
        
        self.setLayout(layout_win)
        
        self.rbtn_calc_type_periodic.toggled.connect(self.onClickedRadioCalcType)
        self.rbtn_calc_type_dynamic.toggled.connect(self.onClickedRadioCalcType)
        self.rbtn_startup_type_periodic.toggled.connect(self.onClickedRadioStartupType)
        self.rbtn_startup_type_dynamic.toggled.connect(self.onClickedRadioStartupType)
        if self.networkSimData['calc_type']=='periodic':
            self.rbtn_calc_type_periodic.setChecked(True)
        else:
            self.rbtn_calc_type_dynamic.setChecked(True)
        if self.networkSimData['startup_type']=='periodic':
            self.rbtn_startup_type_periodic.setChecked(True)
        else:
            self.rbtn_startup_type_dynamic.setChecked(True)
        
    def onClickedRadioCalcType(self,s):
        #print(s)
        
        if self.rbtn_calc_type_dynamic.isChecked():
            self.label_startup.setHidden(False)
            self.label_calcStartupFrom.setHidden(False)
            self.dateedit_startupFrom.setHidden(False)
            self.label_calcStartupTo.setHidden(False)
            self.dateedit_startupTo.setHidden(False)
            self.rbtn_startup_type_dynamic.setHidden(False)    
            self.rbtn_startup_type_periodic.setHidden(False)  
            if self.rbtn_startup_type_dynamic.isChecked():
                self.numb_periods.setHidden(True)
                self.label_numb_periods.setHidden(True)
                
        else:
            self.label_startup.setHidden(True)
            self.label_calcStartupFrom.setHidden(True)
            self.dateedit_startupFrom.setHidden(True)
            self.label_calcStartupTo.setHidden(True)
            self.dateedit_startupTo.setHidden(True)
            self.rbtn_startup_type_dynamic.setHidden(True)    
            self.rbtn_startup_type_periodic.setHidden(True) 
            self.label_numb_periods.setHidden(False)
            self.numb_periods.setHidden(False)    

    def onClickedRadioStartupType(self,s):
        #print(s)
        if self.rbtn_startup_type_dynamic.isChecked():
            self.label_calcStartupFrom.setHidden(False)
            self.dateedit_startupFrom.setHidden(False)
            self.label_calcStartupTo.setHidden(False)
            self.dateedit_startupTo.setHidden(False)
            if self.rbtn_calc_type_dynamic.isChecked():
                self.label_numb_periods.setHidden(True)
                self.numb_periods.setHidden(True)
        else:
            self.label_numb_periods.setHidden(False)
            self.numb_periods.setHidden(False)
            
    def updateStatusBar(self,message):
        #print(f"signal:{message}")
        if message=="Simulation finished" and self.status_bar.currentMessage()!="Simulation failed":
            self.finished_sims+=1
            #print(f'finished_sims: {self.finished_sims}; n_sims: {self.n_sims}')
            if self.finished_sims==self.n_sims:
                self.status_bar.showMessage(message) 
        else:
            self.status_bar.showMessage(message)
    
    def show_error_message(self,message):
        self.status_bar.showMessage("Simulation failed")
        
    def update_finished(self,message):
        self.process_running=False
        
class CalibrateCustomers(QDialog):
    def __init__(self,config,conn):
        """Constructor."""
        super().__init__()
        self.setWindowTitle("Customer model calibration") 
        self.cur=conn.cursor(cursor_factory = psycopg2.extras.RealDictCursor)          
        
        #radio buttons 
        layout_rbtn = QHBoxLayout()
        self.rbtn_annualConumtion = QRadioButton('Use annual consumption data')
        self.rbtn_annualConumtion.setChecked(True)
        #self.rbtn_loadProfile = QRadioButton('Use load profile')
           
        layout_rbtn.addWidget(self.rbtn_annualConumtion)
        #layout_rbtn.addWidget(self.rbtn_loadProfile)
        
        #table templates
        layout_templates = QVBoxLayout()
        label_templates_title =QLabel("Templates")
        font=label_templates_title.font()
        font.setPointSize(15)
        label_templates_title.setFont(font)
        layout_templates.addWidget(label_templates_title)

        self.btn_openTemplate=QPushButton("Open Parametric Run")
        layout_templates.addWidget(self.btn_openTemplate)
        
        self.tableWidget_templates = QTableWidget(0,5)   
        self.tableWidget_templates.setHorizontalHeaderLabels(["Id","Template name","Asset group","Parametric Runs","Used"]) 
        layout_templates.addWidget(self.tableWidget_templates)
        
        #table select customers
        layout_selectCustomers = QVBoxLayout()
        label_selCust_title =QLabel("Customers")
        font=label_selCust_title.font()
        font.setPointSize(15)
        label_selCust_title.setFont(font)
        layout_selectCustomers.addWidget(label_selCust_title)
        self.tableWidget_customer = QTableWidget(0,4)   
        self.tableWidget_customer.setHorizontalHeaderLabels(["ID","Template name","Asset group","Parametric Runs"]) 
        layout_selectCustomers.addWidget(self.tableWidget_customer)

        #Results
        layout_results = QVBoxLayout()
        label_results_title =QLabel("Results (sorted by leftmost output parameter)")
        font=label_results_title.font()
        font.setPointSize(15)
        label_results_title.setFont(font)
        layout_results.addWidget(label_results_title)
        
        
        self.tabwidget = QTabWidget()
        layout_results.addWidget(self.tabwidget)
        
    
        #buttons     
        layout_buttons = QHBoxLayout()
        self.btn_startCallibration=QPushButton("Callibrate selected customers")
        layout_buttons.addWidget(self.btn_startCallibration)
        self.btn_showCallibCust=QPushButton("Open selected results")
        layout_buttons.addWidget(self.btn_showCallibCust)
        self.btn_saveCallibration=QPushButton("Save selected results/Invoke customers")
        layout_buttons.addWidget(self.btn_saveCallibration)
        self.btn_cancel=QPushButton("Cancel")
        layout_buttons.addWidget(self.btn_cancel)
        
        #---------------set layouts together-------------------
        layout_win = QVBoxLayout()
        layout_win.addLayout(layout_rbtn)
        layout_win.addLayout(layout_templates)
        layout_win.addLayout(layout_selectCustomers)
        layout_win.addLayout(layout_results)
        layout_win.addLayout(layout_buttons)
        
        self.setLayout(layout_win)
        
class FeatureModelParmDlg(QDialog):
    def __init__(self,cur,config):
        """Constructor."""
        super().__init__()
        self.setWindowTitle("Feature model parameter mapping") 
        self.loadedMappingParms={}
        self.cur=cur
        self.config=config
        
        #radio buttons
        layout_rbtn = QHBoxLayout()
        self.rbtn_customers = QRadioButton('Customers')
        self.rbtn_customers.setChecked(True)
        self.rbtn_plants = QRadioButton('Energy plants')
        self.rbtn_customers.toggled.connect(self.onClickedRadio)
        self.rbtn_plants.toggled.connect(self.onClickedRadio)
        
        layout_rbtn.addWidget(self.rbtn_customers)
        layout_rbtn.addWidget(self.rbtn_plants)
        
        layout_list=QHBoxLayout()
        #list widget for layer attributes
        layout_listWidget_featureFields = QVBoxLayout()
        label_listWidget_featureFields=QLabel("Fields")
        layout_listWidget_featureFields.addWidget(label_listWidget_featureFields)
        self.listWidget_featureFields = QListWidget()
        layout_listWidget_featureFields.addWidget(self.listWidget_featureFields)
        self.listWidget_featureFields.itemDoubleClicked.connect(self.mapAttributesDoubleClick)
        
        label_list_helptext=QLabel('Info: Double click on the \nfield in order to map it to \nthe selected mapping expression.\nYou can use also dictionaries in the form: {key: entry}[value/attribute]')
        layout_list.addLayout(layout_listWidget_featureFields)
        layout_list.addWidget(label_list_helptext)
       
        #---------------ok/cancel buttons     
        layout_buttons_conns = QHBoxLayout()
        self.btn_add=QPushButton("")
        self.btn_add.setIcon(QIcon(":/images/themes/default/symbologyAdd.svg"))

        layout_buttons_conns.addWidget(self.btn_add)
        self.btn_remove=QPushButton("")
        self.btn_remove.setIcon(QIcon(":/images/themes/default/symbologyRemove.svg"))
        layout_buttons_conns.addWidget(self.btn_remove)
        layout_buttons_conns.addItem(QSpacerItem(0,0,QSizePolicy.Policy.Expanding,QSizePolicy.Policy.Minimum))

        #table for mapped attributes  
        self.tableWidget_parameters = QTableWidget(0,6)   
        self.tableWidget_parameters.setHorizontalHeaderLabels(['Id','Mapping expression','Mapping direction','Parameter name','Model name','Macro name'])
        
        #---------------ok/cancel buttons     
        layout_buttons = QHBoxLayout()
        self.btn_ok=QPushButton("Save")
        layout_buttons.addWidget(self.btn_ok)
        self.btn_cancel=QPushButton("Cancel")
        layout_buttons.addWidget(self.btn_cancel)
        
        #---------------set layouts together-------------------
        layout_win = QVBoxLayout()
        layout_win.addLayout(layout_rbtn)
        layout_win.addLayout(layout_list)
        layout_win.addLayout(layout_buttons_conns)
        layout_win.addWidget(self.tableWidget_parameters)
        layout_win.addLayout(layout_buttons)
        
        self.loadParm()
        self.loadFieldAttributes()
        
        self.setLayout(layout_win)
        
    def mapAttributesDoubleClick(self,s):
        table_index=self.tableWidget_parameters.currentRow()
        if table_index!=-1:
            self.tableWidget_parameters.setItem(table_index,1,QTableWidgetItem('"'+s.text()+'"'))
        else:
            iface.messageBar().pushMessage("Info", "No model parameter selected!", level=Qgis.Info)
            
    def onClickedRadio(self,s):
        #print(s)
        self.loadedMappingParms={}
        self.loadParm()
        self.loadFieldAttributes()
        
    def loadFieldAttributes(self):
        self.listWidget_featureFields.clear()
        attrs=getTableAttr(self.cur,self.config,'customer' if self.rbtn_customers.isChecked() else 'energy_plant')
        self.listWidget_featureFields.addItems(attrs)

    def loadParm(self):
        self.tableWidget_parameters.setRowCount(0)

        sql="""SELECT * FROM model_parms WHERE type={} ORDER BY id;""".format(1 if self.rbtn_customers.isChecked() else 2)
        self.cur.execute(sql)
        table=self.tableWidget_parameters
        for i,parm in enumerate(self.cur.fetchall()):
            self.loadedMappingParms[parm['id']]={'parm_name' : parm['parm_name'],'model_name' : parm['model_name'],'mapping_expression' : parm['mapping_expression'],'macro_name' : parm['macro_name'],'mapping_direction' : parm['mapping_direction']}
            table.insertRow(i)
            item = QTableWidgetItem(str(parm['id']))
            item.setFlags(item.flags() & ~qt_item_flag("ItemIsEditable"))

            table.setItem(i,0,item)
            table.setItem(i,1,QTableWidgetItem(parm['mapping_expression']))
                        
            comboBox = QComboBox()
            comboBox.addItems(['<-->','<--','-->'])
            comboBox.setCurrentText(parm['mapping_direction'])
            table.setCellWidget(i, 2, comboBox)  
            
            table.setItem(i,3,QTableWidgetItem(parm['parm_name']))
            table.setItem(i,4,QTableWidgetItem(parm['model_name']))
            table.setItem(i,5,QTableWidgetItem(parm['macro_name'])) 

class FeatureDecouplingDlg(QDialog):
    def __init__(self,plugin_dir,cur,config):
        """List the feature model names, which belongs to network side in decoupling mode"""
        super().__init__()
        self.cur=cur
        self.config=config
        self.setWindowTitle("Feature decoupling")   

        #Radio buttons customers, plants
        layout_rbtn = QHBoxLayout()
        self.rbtn_customers = QRadioButton('Customers')
        self.rbtn_customers.setChecked(True)
        self.rbtn_plants = QRadioButton('Energy plants')
        self.rbtn_customers.toggled.connect(self.onClickedRadio)
        self.rbtn_plants.toggled.connect(self.onClickedRadio)
        layout_rbtn.addWidget(self.rbtn_customers)
        layout_rbtn.addWidget(self.rbtn_plants)

        #Number of feature submodels
        layout_no_submodels = QHBoxLayout()
        label_no_submodels =QLabel("Number of decoupled feature submodels (Equal count of feature per submodel if set): ")
        layout_no_submodels.addWidget(label_no_submodels)
        self.no_submodels = QLineEdit()
        layout_no_submodels.addWidget(self.no_submodels)
        
        #combo templates
        self.feature_template = QComboBox()
        self.feature_template.currentIndexChanged.connect(self.onClickedTemplate)
        
        #label list
        label_list =QLabel("Component names, which belongs to the network side in decoupling mode")
        
        #list model names
        self.listWidget_featureModels = QListWidget()
        
        #buttons add/delete
        #table buttons     
        layout_buttons_action = QHBoxLayout()
        self.btn_add=QPushButton("Add")
        self.btn_add.clicked.connect(self.addListItem)
        layout_buttons_action.addWidget(self.btn_add)
        self.btn_delete=QPushButton("Delete")
        self.btn_delete.clicked.connect(self.removeSel)
        layout_buttons_action.addWidget(self.btn_delete)
                       
        #---------------ok/cancel buttons     
        layout_buttons = QHBoxLayout()
        self.btn_save=QPushButton("Save/Update")
        self.btn_save.clicked.connect(self.saveListContent)
        self.btn_cancel=QPushButton("Cancel")
        layout_buttons.addWidget(self.btn_save)
        layout_buttons.addWidget(self.btn_cancel)
        
        #---------------set layouts together-------------------
        layout_win = QVBoxLayout()
        layout_win.addLayout(layout_rbtn)
        layout_win.addLayout(layout_no_submodels)
        layout_win.addWidget(self.feature_template)
        layout_win.addWidget(label_list)
        layout_win.addWidget(self.listWidget_featureModels)
        layout_win.addLayout(layout_buttons_action)
        layout_win.addLayout(layout_buttons) 
        
        self.setLayout(layout_win)
        self.onClickedRadio('')
        self.no_submodels.setText(str(len([i for i in getFeatureSubmodels(self.cur,self.config,'customer' if self.rbtn_customers.isChecked() else 'energy_plant') if i not in getLineSubmodels(self.cur,self.config)])))

    def addListItem(self):
        item=QListWidgetItem('New entry')
        item.setFlags(item.flags() | QtCore.Qt.ItemIsEditable)
        self.listWidget_featureModels.insertItem(0, item)    
        
    def onClickedRadio(self,s):
        #print(s)
        self.listWidget_featureModels.clear()
        self.feature_template.clear()
        
        if self.rbtn_customers.isChecked():
            sql="""SELECT template,template_name FROM customer_templates ORDER BY template;"""
        else:
            sql="""SELECT template,template_name FROM energy_plant_templates ORDER BY template;"""
        #print(sql)
        self.cur.execute(sql)
        self.feature_template.addItems([i['template_name'] for i in self.cur.fetchall()])

    def onClickedTemplate(self,s):
        #print(s)
        self.listWidget_featureModels.clear()
        if self.rbtn_customers.isChecked():
            sql="""SELECT f_dec.comp_name
    FROM customer_templates c_t,  "{}".feature_decoupling f_dec
    WHERE c_t.template_name='{}' AND f_dec.template=c_t.template AND type='customer';
""".format(self.config['versionName'],self.feature_template.itemText(s))
        else:
            sql="""SELECT f_dec.comp_name
    FROM energy_plant_templates ep_t, "{}".feature_decoupling f_dec
    WHERE ep_t.template_name='{}' AND f_dec.template=ep_t.template AND type='energy_plant';
""".format(self.config['versionName'],self.feature_template.itemText(s))
        #print(sql)
        self.cur.execute(sql)
        self.listWidget_featureModels.addItems([i['comp_name'] for i in self.cur.fetchall()])
        
    def saveListContent(self):
        #print('Save list conetent')
        if self.rbtn_customers.isChecked():
            type='customer'
        else:
            type='energy_plant'

        sql="""SELECT template FROM public.{}_templates WHERE template_name='{}';""".format(type,template)
        #print(sql)
        self.cur.execute(sql)
        template_id=self.cur.fetchone()['template']
        #print(template_id)
        
        sql="""DELETE FROM "{}".feature_decoupling WHERE template={};\n""".format(self.config['versionName'],template_id)
        sql+='\n'.join(["""INSERT INTO "{}".feature_decoupling (template,comp_name,type) VALUES ({},'{}','{}');""".format(self.config['versionName'],template_id,self.listWidget_featureModels.item(i).text(),type) for i in range(self.listWidget_featureModels.count())])

        try:
            no_submodels=int(self.no_submodels.text())
            self.cur.execute('SELECT row_number() OVER(ORDER BY id) enum, id FROM "{}".{}s;'.format(self.config['versionName'],type))
            f_ids=self.cur.fetchall()
            submodel_counter=(getLineNetworks(self.cur,self.config)[-1] if getLineNetworks(self.cur,self.config) else 0)
            if no_submodels>0:
                self.cur.execute('SELECT count(*) AS count FROM "{}".{}s;'.format(self.config['versionName'],type))
                no_features=self.cur.fetchone()['count']
                f_per_submodel=int(no_features/no_submodels)
                rest=no_features%no_submodels
                                
                for f_id in f_ids:
                    if f_id['enum']>submodel_counter*f_per_submodel+(no_features%no_submodels-rest+1 if rest>0 else no_features%no_submodels):
                        submodel_counter+=1
                        rest-=1
                    sql+='UPDATE "{}".{}s SET submodel={} WHERE id={};'.format(self.config['versionName'],type,submodel_counter+1,f_id['id'])
            elif no_submodels==0:
                sql+='UPDATE "{}".{}s f SET submodel = s_m.submodel::int FROM (SELECT * FROM "{}".submodels) s_m WHERE ST_DWithin(s_m.geom,f.geom,0.001);'.format(self.config['versionName'],type,self.config['versionName'])
            else:
                iface.messageBar().pushMessage("Error", "Please enter a positive integer number in number of feature submodels!", level=Qgis.Critical)
        except:
           pass

        
        #print(sql)
        if sql:
            self.cur.execute(sql)
            
    def removeSel(self):
        listItems=self.listWidget_featureModels.selectedItems()
        if not listItems: 
            return        
        for item in listItems:
            self.listWidget_featureModels.takeItem(self.listWidget_featureModels.row(item))

class InvokeFeaturesDlg(QDialog):
    def __init__(self):
        """Constructor."""
        super().__init__()
        self.setWindowTitle("Invoke feature models from template")
        self.type=""        
        
        #-------------Invoke---------------
               
        #invoke buttons       
        layout_invoke_btn = QHBoxLayout()      
        
        self.btn_invokeOne=QPushButton("Invoke selected feature")
        layout_invoke_btn.addWidget(self.btn_invokeOne)
        
        self.btn_invokeAll=QPushButton("Invoke all features")
        layout_invoke_btn.addWidget(self.btn_invokeAll)
        
        #radio buttons
        layout_rbtn = QHBoxLayout()
        self.rbtn_customers = QRadioButton('Customers')
        self.rbtn_customers.setChecked(True)
        self.rbtn_plants = QRadioButton('Energy plants')
           
        layout_rbtn.addWidget(self.rbtn_customers)
        layout_rbtn.addWidget(self.rbtn_plants)
        
        #table
        self.tableWidget_customer = QTableWidget(0,2)   
        self.tableWidget_customer.setHorizontalHeaderLabels(["  ID    ","Feature is invoked"])      

        #---------------ok/Open buttons     
        layout_buttons = QHBoxLayout()
        self.btn_ok=QPushButton("Ok")
        layout_buttons.addWidget(self.btn_ok)
        self.btn_openInvoked=QPushButton("Open invoked feature")
        layout_buttons.addWidget(self.btn_openInvoked)      
        self.btn_simulateInvoked=QPushButton("Simulate invoked features")
        layout_buttons.addWidget(self.btn_simulateInvoked)      
        self.btn_showFeatureLoad=QPushButton("Plot selected features load/energy")
        layout_buttons.addWidget(self.btn_showFeatureLoad)    

        #progress bar
        self.progress=QProgressBar()        
        
        #---------------set layouts together-------------------
        layout_win = QVBoxLayout()
        layout_win.addLayout(layout_invoke_btn)
        layout_win.addLayout(layout_rbtn)
        layout_win.addWidget(self.tableWidget_customer)
        layout_win.addLayout(layout_buttons)
        layout_win.addWidget(self.progress)
        
        self.setLayout(layout_win)         
        
    def show_error_message(self, message):
        # Show the error message in a messageBar
        #iface.messageBar().pushMessage("Error", message, level=Qgis.Critical)
        pass
        
    def update_progress(self,progress):
        self.progress.setValue(progress)

    def show_plots(self,plot):
        if plot:
            self.ax.set_title('Load profiles {}'.format(self.type))
            self.ax2.set_title('Cumulated energy {}'.format(self.type))
            self.ax.set_xlabel('Time, h')
            self.ax2.set_xlabel('Time, h')
            self.ax.set_ylabel('Power, W')
            self.ax2.set_ylabel('Energy, kWh')
        
            self.fig.legend()
            self.fig2.legend()
            self.fig.show()            
            self.fig2.show()  
        
    def plot_data(self, data):
        # Plotting in the main thread, which is non-blocking
        time=data[0]['time']
        valuesPowerInt=data[0]['data']
        label=data[0]['label']
        self.ax.plot(time, valuesPowerInt,label=label)
        time=data[1]['time']
        valuesEnergyInt=data[1]['data']
        label=data[1]['label']
        self.ax2.plot(time, valuesEnergyInt,label=label)
        
    def plot_total_data(self, data):
        try:
            fig1, ax1 = plt.subplots(layout='constrained')
            time=data[0]['time']
            power_sum=data[0]['data']
            ax1.plot(time, power_sum, label='Total power, W')
            time=data[1]['time']
            energy_sum=data[1]['data']
            ax1.plot(time, energy_sum, label='Total energy, kWh')
            ax1.set_title('Total load profiles')
            plt.legend()
            fig1.show()
        except:
            pass

#dublicated code
class ComboBox(QComboBox):
    popupAboutToBeShown = QtCore.pyqtSignal()

    def showPopup(self):
        self.popupAboutToBeShown.emit()
        super(ComboBox, self).showPopup()
        
class ModellingSettings(QDialog):
    def __init__(self,plugin_dir,modellingSettings,cur):
        """Constructor."""
        super().__init__()
        self.setWindowTitle("Modelling settings")    
        self.plugin_dir=plugin_dir
        self.cur=cur
        #-------------Settings FD pipe ---------------
        #titel
        label_fd_pipe_title =QLabel("Finite difference pipe model")
        font=label_fd_pipe_title.font()
        font.setPointSize(15)
        label_fd_pipe_title.setFont(font)
        
        #labels
        layout_fd_pipe_label = QVBoxLayout()
        
        label_fd_pipe_discretization =QLabel("Meter per node ")
        layout_fd_pipe_label.addWidget(label_fd_pipe_discretization)
        
        #values
        layout_fd_pipe_value = QVBoxLayout()
        
        self.fd_meterPerNode = QLineEdit(modellingSettings['fd_meterPerNode'])
        layout_fd_pipe_value.addWidget(self.fd_meterPerNode) 
        
        #set labes & values together
        layout_fd_pipe = QHBoxLayout() 
        layout_fd_pipe.addLayout(layout_fd_pipe_label)
        layout_fd_pipe.addLayout(layout_fd_pipe_value)     

        #-------------Settings node model---------------
        #titel
        label_node_title =QLabel("Node model")
        font=label_node_title.font()
        font.setPointSize(15)
        label_node_title.setFont(font)
        
        #labels
        layout_node_label = QVBoxLayout()
        
        label_node_vol =QLabel("Node volume, m3 ")
        layout_node_label.addWidget(label_node_vol)
        
        #values
        layout_node_value = QVBoxLayout()
        
        self.node_vol = QLineEdit(modellingSettings['node_vol'])
        layout_node_value.addWidget(self.node_vol) 
        
        #set labes & values together
        layout_node = QHBoxLayout() 
        layout_node.addLayout(layout_node_label)
        layout_node.addLayout(layout_node_value)     
        
        #-------------Ambient settings---------------
        #titel
        label_ambient_title =QLabel("Ambient temperatur settings")
        font=label_ambient_title.font()
        font.setPointSize(15)
        label_ambient_title.setFont(font)
        
        #titel
        label_ground_title =QLabel("Ground")
        font=label_ground_title.font()
        font.setPointSize(12)
        label_ground_title.setFont(font)
        
        #labels
        layout_ground_label = QVBoxLayout()
        
        label_ground_conductivity =QLabel("Thermal conductivity of the soil/trench, W/(m*K):")
        layout_ground_label.addWidget(label_ground_conductivity)

        label_ground_model =QLabel("Ground surface layer temperature model:")
        layout_ground_label.addWidget(label_ground_model)
        
        
        self.label_amb_kusuda_tsurfmean =QLabel("Annual mean temperature, °C:")
        layout_ground_label.addWidget(self.label_amb_kusuda_tsurfmean)
        
        self.label_amb_kusuda_tsurfampl =QLabel("Daily mean temperature amplitude, K:")
        layout_ground_label.addWidget(self.label_amb_kusuda_tsurfampl)
        
        self.label_amb_kusuda_theta =QLabel("Phase shift of monthly minimum temperatur, days:")
        layout_ground_label.addWidget(self.label_amb_kusuda_theta)
        
        self.label_amb_kusuda_rho =QLabel("Surface layer density, kg/m3:")
        layout_ground_label.addWidget(self.label_amb_kusuda_rho)
        
        self.label_amb_kusuda_cp =QLabel("Specific heat capacity of the surface layer, J/(kg*K):")
        layout_ground_label.addWidget(self.label_amb_kusuda_cp)
        
        self.label_amb_kusuda_lambda =QLabel("Thermal conductivity of the surface layer, W/(m*K):")
        layout_ground_label.addWidget(self.label_amb_kusuda_lambda)
        
        self.label_amb_kusuda_depth =QLabel("Surface layer depth, m:")
        layout_ground_label.addWidget(self.label_amb_kusuda_depth)
        
        
        self.label_amb_ground_profile =QLabel("Ground temperatur timeseries:")
        layout_ground_label.addWidget(self.label_amb_ground_profile)
        
        
        self.label_amb_ground_temp =QLabel("Constant ground temperatur:")
        layout_ground_label.addWidget(self.label_amb_ground_temp)
        
        #values
        layout_ground_value = QVBoxLayout()
        
        self.ground_lambda = QLineEdit(modellingSettings['ground_lambda'])
        layout_ground_value.addWidget(self.ground_lambda) 
        
        self.amb_ground_model = QComboBox()
        #self.amb_ground_model.addItems(['Kusuda','Timeseries','Constant'])
        self.amb_ground_model.addItems(['Kusuda','Constant'])
        self.amb_ground_model.setCurrentText(modellingSettings['ground_model'])
        layout_ground_value.addWidget(self.amb_ground_model) 
        
        self.amb_kusuda_tsurfmean = QLineEdit(modellingSettings['kusuda_tsurfmean'])
        layout_ground_value.addWidget(self.amb_kusuda_tsurfmean) 
        
        self.amb_kusuda_tsurfampl = QLineEdit(modellingSettings['kusuda_tsurfampl'])
        layout_ground_value.addWidget(self.amb_kusuda_tsurfampl) 
        
        self.amb_kusuda_theta = QLineEdit(modellingSettings['kusuda_theta'])
        layout_ground_value.addWidget(self.amb_kusuda_theta) 
        
        self.amb_kusuda_rho = QLineEdit(modellingSettings['kusuda_rho'])
        layout_ground_value.addWidget(self.amb_kusuda_rho) 
        
        self.amb_kusuda_cp = QLineEdit(modellingSettings['kusuda_cp'])
        layout_ground_value.addWidget(self.amb_kusuda_cp) 
        
        self.amb_kusuda_lambda = QLineEdit(modellingSettings['kusuda_lambda'])
        layout_ground_value.addWidget(self.amb_kusuda_lambda) 
        
        self.amb_kusuda_depth = QLineEdit(modellingSettings['kusuda_depth'])
        layout_ground_value.addWidget(self.amb_kusuda_depth) 
        
        
        self.amb_ground_profile = ComboBox()
        layout_ground_value.addWidget(self.amb_ground_profile) 
        
        
        self.amb_ground_temp = QLineEdit(modellingSettings['ground_temp'])
        layout_ground_value.addWidget(self.amb_ground_temp) 
        
        #set labes & values together
        layout_ground = QHBoxLayout() 
        layout_ground.addLayout(layout_ground_label)
        layout_ground.addLayout(layout_ground_value) 
        
        
        #titel
        label_duct_title =QLabel("Duct temperatur")
        font=label_duct_title.font()
        font.setPointSize(12)
        label_duct_title.setFont(font)
        
        #labels
        layout_duct_label = QVBoxLayout()
        
        label_duct_model =QLabel("Duct model:")
        layout_duct_label.addWidget(label_duct_model)            
        
        self.label_amb_duct_profile =QLabel("Duct temperatur timeseries:")
        layout_duct_label.addWidget(self.label_amb_duct_profile)
        
        self.label_amb_duct_temp =QLabel("Constant duct temperatur:")
        layout_duct_label.addWidget(self.label_amb_duct_temp)
        
        #values
        layout_duct_value = QVBoxLayout()
        
        self.amb_duct_model = QComboBox()
        #self.amb_duct_model.addItems(['Timeseries','Constant'])
        self.amb_duct_model.addItems(['Constant'])
        self.amb_duct_model.setCurrentText(modellingSettings['duct_model'])
        layout_duct_value.addWidget(self.amb_duct_model)        
        
        self.amb_duct_profile = ComboBox()
        layout_duct_value.addWidget(self.amb_duct_profile) 
        
        self.amb_duct_temp = QLineEdit(modellingSettings['duct_temp'])
        layout_duct_value.addWidget(self.amb_duct_temp) 
        
        #set labes & values together
        layout_duct = QHBoxLayout() 
        layout_duct.addLayout(layout_duct_label)
        layout_duct.addLayout(layout_duct_value)   
        
        #titel
        label_air_title =QLabel("Ambient air temperatur")
        font=label_air_title.font()
        font.setPointSize(12)
        label_air_title.setFont(font)
        
        #labels
        layout_air_label = QVBoxLayout()
        
        label_amb_ambient_air_model =QLabel("Ambient air model:")
        layout_air_label.addWidget(label_amb_ambient_air_model)            
        
        #values
        layout_air_value = QVBoxLayout()
        
        self.amb_ambient_air_model = QComboBox()
        self.amb_ambient_air_model.addItems(['Climate'])
        self.amb_ambient_air_model.setCurrentText(modellingSettings['ambient_air_model'])
        layout_air_value.addWidget(self.amb_ambient_air_model)        

        
        #set labes & values together
        layout_air = QHBoxLayout() 
        layout_air.addLayout(layout_air_label)
        layout_air.addLayout(layout_air_value)     
        
        #set settings layout together
        layout_fd_pipe_settings = QVBoxLayout()
        layout_fd_pipe_settings.addWidget(label_fd_pipe_title)
        layout_fd_pipe_settings.addLayout(layout_fd_pipe)
        layout_fd_pipe_settings.addWidget(label_node_title)
        layout_fd_pipe_settings.addLayout(layout_node)
        layout_fd_pipe_settings.addWidget(label_ambient_title)
        layout_fd_pipe_settings.addWidget(label_ground_title)
        layout_fd_pipe_settings.addLayout(layout_ground)
        layout_fd_pipe_settings.addWidget(label_duct_title)
        layout_fd_pipe_settings.addLayout(layout_duct)
        layout_fd_pipe_settings.addWidget(label_air_title)
        layout_fd_pipe_settings.addLayout(layout_air)
        
        
        #---------------ok/cancel buttons     
        layout_buttons = QHBoxLayout()
        self.btn_ok=QPushButton("Ok")
        layout_buttons.addWidget(self.btn_ok)
        self.btn_cancel=QPushButton("Cancel")
        layout_buttons.addWidget(self.btn_cancel)
        
        #---------------set layouts together-------------------
        layout_win = QVBoxLayout()
        layout_win.addLayout(layout_fd_pipe_settings)
        layout_win.addLayout(layout_buttons)
        layout_win.addStretch()
        
        #trigger show/hide labels and value fields
        self.showGroundModelParameter(modellingSettings['ground_model'])
        self.showDuctModelParameter(modellingSettings['duct_model'])

        #connect signals
        self.amb_duct_model.currentTextChanged.connect(self.showDuctModelParameter)
        self.amb_ground_model.currentTextChanged.connect(self.showGroundModelParameter)

        self.setLayout(layout_win)
    
    def setTimeseriesIds(self,combobox,table_name):
        ids=self.getTimeseriesIds(table_name)
        combobox.clear()
        combobox.addItems(ids)
        
    def getTimeseriesIds(self,table_name):
        sql="""SELECT id FROM {} ORDER BY id;""".format(table_name)
        #print(sql)
        self.cur.execute(sql)
        return [str(i['id']) for i in self.cur.fetchall()]
              
    def showDuctModelParameter(self,s):
        #print(s)
        if s=='Timeseries':
            self.amb_duct_profile.setHidden(False)
            self.label_amb_duct_profile.setHidden(False)
        
            self.amb_duct_temp.setHidden(True)
            self.label_amb_duct_temp.setHidden(True)
        elif 'Constant':
            self.amb_duct_temp.setHidden(False)
            self.label_amb_duct_temp.setHidden(False)
            self.amb_duct_profile.setHidden(True)
            self.label_amb_duct_profile.setHidden(True)
        self.adjustSize()
                
    def showGroundModelParameter(self,s):
        #print(s)
        if s=='Kusuda':
            self.amb_kusuda_tsurfmean.setHidden(False)
            self.amb_kusuda_tsurfampl.setHidden(False)
            self.amb_kusuda_theta.setHidden(False)
            self.amb_kusuda_rho.setHidden(False)
            self.amb_kusuda_cp.setHidden(False)
            self.amb_kusuda_lambda.setHidden(False)
            self.amb_kusuda_depth.setHidden(False)
            self.label_amb_kusuda_tsurfmean.setHidden(False)
            self.label_amb_kusuda_tsurfampl.setHidden(False)
            self.label_amb_kusuda_theta.setHidden(False)
            self.label_amb_kusuda_rho.setHidden(False)
            self.label_amb_kusuda_cp.setHidden(False)
            self.label_amb_kusuda_lambda.setHidden(False)
            self.label_amb_kusuda_depth.setHidden(False)
            
            self.amb_ground_profile.setHidden(True)
            self.amb_ground_temp.setHidden(True)
            self.label_amb_ground_profile.setHidden(True)
            self.label_amb_ground_temp.setHidden(True)
        elif s=='Timeseries':
            self.amb_ground_profile.setHidden(False)
            self.label_amb_ground_profile.setHidden(False)
            
            self.amb_kusuda_tsurfmean.setHidden(True)
            self.amb_kusuda_tsurfampl.setHidden(True)
            self.amb_kusuda_theta.setHidden(True)
            self.amb_kusuda_rho.setHidden(True)
            self.amb_kusuda_cp.setHidden(True)
            self.amb_kusuda_lambda.setHidden(True)
            self.amb_kusuda_depth.setHidden(True)
            self.label_amb_kusuda_tsurfmean.setHidden(True)
            self.label_amb_kusuda_tsurfampl.setHidden(True)
            self.label_amb_kusuda_theta.setHidden(True)
            self.label_amb_kusuda_rho.setHidden(True)
            self.label_amb_kusuda_cp.setHidden(True)
            self.label_amb_kusuda_lambda.setHidden(True)
            self.label_amb_kusuda_depth.setHidden(True)
            self.amb_ground_temp.setHidden(True)
            self.label_amb_ground_temp.setHidden(True)
        elif s=='Constant':
            self.amb_ground_temp.setHidden(False)
            self.label_amb_ground_temp.setHidden(False)

            self.amb_ground_profile.setHidden(True)
            self.amb_kusuda_tsurfmean.setHidden(True)
            self.amb_kusuda_tsurfampl.setHidden(True)
            self.amb_kusuda_theta.setHidden(True)
            self.amb_kusuda_rho.setHidden(True)
            self.amb_kusuda_cp.setHidden(True)
            self.amb_kusuda_lambda.setHidden(True)
            self.amb_kusuda_depth.setHidden(True)
            self.label_amb_ground_profile.setHidden(True)
            self.label_amb_kusuda_tsurfmean.setHidden(True)
            self.label_amb_kusuda_tsurfampl.setHidden(True)
            self.label_amb_kusuda_theta.setHidden(True)
            self.label_amb_kusuda_rho.setHidden(True)
            self.label_amb_kusuda_cp.setHidden(True)
            self.label_amb_kusuda_lambda.setHidden(True)
            self.label_amb_kusuda_depth.setHidden(True)
            
class SupervisoryCtrlDlg(QDialog):
    def __init__(self,cur,config):
        """Constructor."""
        super().__init__()
        self.setWindowTitle("Supervisory control") 
        
        #networks
        layout_submodel=QHBoxLayout()
        label_submodel =QLabel("Submodel")
        layout_submodel.addWidget(label_submodel)
        self.combo_submodel = QComboBox()
        submodels=getUsedNetworkSubmodels(cur,config)
        self.combo_submodel.addItems(submodels)
        if getSupervisorySubmodel(cur,config) in submodels:
            self.combo_submodel.setCurrentText(getSupervisorySubmodel(cur,config))
        layout_submodel.addWidget(self.combo_submodel)
            
        #buttons     
        layout_buttons = QHBoxLayout()
        self.btn_ok=QPushButton("Ok")
        layout_buttons.addWidget(self.btn_ok)
        self.btn_open=QPushButton("Open")
        layout_buttons.addWidget(self.btn_open)
        self.btn_cancel=QPushButton("Cancel")
        layout_buttons.addWidget(self.btn_cancel)
        
        #---------------set layouts together-------------------
        layout_win = QVBoxLayout()
        #layout_win.addLayout(layout_submodel)
        layout_win.addLayout(layout_buttons)
        
        self.setLayout(layout_win)
