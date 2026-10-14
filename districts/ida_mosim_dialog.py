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
from .calibrate_customers import *

import os
import psycopg2
import psycopg2.extras
from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT
from qgis.utils import iface
from qgis.core import Qgis,QgsMessageLog
from qgis.PyQt.QtGui import QKeySequence
import matplotlib.pyplot as plt   
import traceback
  
        
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

        #info
        info_sensors=QTextEdit(tr('@default','info_sensors'))
        info_sensors.setReadOnly(True)
        
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
        layout_win.addWidget(info_sensors)
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
        super().__init__()

        self.process_running=False
        self.requestedOutputs_old=requestedOutputs.copy()
        
        # Load UI
        ui_path = os.path.join(os.path.dirname(__file__), "RequestedOutputs_dialog.ui")
        uic.loadUi(ui_path, self)
        self.info_requested_ouputs.setReadOnly(True)
        
        #------------------temporal results----------------------        
        #--Customers--  
        if requestedOutputs['power_c']:
            self.checkBoxSubstationPower.setChecked(True)
        if requestedOutputs['temp_c']:
            self.checkBoxSubstationConnTemp.setChecked(True)
        if requestedOutputs['p_c']:
            self.checkBoxSubstationPressure.setChecked(True)
        if requestedOutputs['mdot_c']:
            self.checkBoxSubstationMassflow.setChecked(True)
        if requestedOutputs['heatbalance_c']:
            self.checkBoxSubstationHeatbalance.setChecked(True)
        if requestedOutputs['troom_c']:
            self.checkBoxSubstationTair.setChecked(True)
            
        #------------------Energy plants----------------------      
        if requestedOutputs['power_ep']:
            self.checkBoxPlantPower.setChecked(True)
        if requestedOutputs['temp_ep']:
            self.checkBoxPlantConnTemp.setChecked(True)
        if requestedOutputs['p_ep']:
            self.checkBoxPlantPressure.setChecked(True)
        if requestedOutputs['mdot_ep']:
            self.checkBoxPlantMassflow.setChecked(True)
        
        #------------------Network----------------------
        if requestedOutputs['p_lines']:
            self.checkBoxPressureDistribution.setChecked(True)
        if requestedOutputs['mdot_lines']:
            self.checkBoxMdotNode.setChecked(True)
        if requestedOutputs['v_lines']:
            self.checkBoxVPipe.setChecked(True)
        if requestedOutputs['temp_lines']:
            self.checkBoxTempPipe.setChecked(True)
        if requestedOutputs['qamb_lines']:
            self.checkBoxQambPipe.setChecked(True)
            
        #------------------System----------------------
        if requestedOutputs['heatbalance_system']:
            self.heatbalance_system.setChecked(True)
        if requestedOutputs['massbalance_system']:
            self.massbalance_system.setChecked(True)
        if requestedOutputs['tsup_mean_c_system']:
            self.checkBoxMeanSupplyTempCSystem.setChecked(True)
        if requestedOutputs['tsup_max_c_system']:
            self.checkBoxMaxSupplyTempCSystem.setChecked(True)
        if requestedOutputs['tsup_min_c_system']:
            self.checkBoxMinSupplyTempCSystem.setChecked(True)
        if requestedOutputs['tsup_mean_ep_system']:
            self.checkBoxMeanSupplyTempEpSystem.setChecked(True)
        if requestedOutputs['tsup_max_ep_system']:
            self.checkBoxMaxSupplyTempEpSystem.setChecked(True)
        if requestedOutputs['tsup_min_ep_system']:
            self.checkBoxMinSupplyTempEpSystem.setChecked(True)
        if requestedOutputs['tret_mean_c_system']:
            self.checkBoxMeanReturnTempCSystem.setChecked(True)
        if requestedOutputs['tret_max_c_system']:
            self.checkBoxMaxReturnTempCSystem.setChecked(True)
        if requestedOutputs['tret_min_c_system']:
            self.checkBoxMinReturnTempCSystem.setChecked(True)
        if requestedOutputs['tret_mean_ep_system']:
            self.checkBoxMeanReturnTempEpSystem.setChecked(True)
        if requestedOutputs['tret_max_ep_system']:
            self.checkBoxMaxReturnTempEpSystem.setChecked(True)
        if requestedOutputs['tret_min_ep_system']:
            self.checkBoxMinReturnTempEpSystem.setChecked(True)
            
        #------------------KPI`s----------------------            
        #customer
        if requestedOutputs['tsup_mean_c_kpi']:
            self.checkBoxMeanSupplyTempC.setChecked(True)
        if requestedOutputs['tsup_max_c_kpi']:
            self.checkBoxMaxSupplyTempC.setChecked(True)
        if requestedOutputs['tsup_min_c_kpi']:
            self.checkBoxMinSupplyTempC.setChecked(True)
        if requestedOutputs['tret_mean_c_kpi']:
            self.checkBoxMeanRetTempC.setChecked(True)
        if requestedOutputs['tret_max_c_kpi']:
            self.checkBoxMaxRetTempC.setChecked(True)
        if requestedOutputs['tret_min_c_kpi']:
            self.checkBoxMinRetTempC.setChecked(True)
        if requestedOutputs['qsup_heat_c_kpi']:
            self.checkBoxQsupHeatC.setChecked(True)
        if requestedOutputs['qsup_cold_c_kpi']:
            self.checkBoxQsupColdC.setChecked(True)
        if requestedOutputs['qsup_c_kpi']:
            self.checkBoxQsupEnergyC.setChecked(True)
            
        #Energy plant
        if requestedOutputs['tsup_mean_ep_kpi']:
            self.checkBoxMeanSupplyTempEp.setChecked(True)
        if requestedOutputs['tsup_max_ep_kpi']:
            self.checkBoxMaxSupplyTempEp.setChecked(True)
        if requestedOutputs['tsup_min_ep_kpi']:
            self.checkBoxMinSupplyTempEp.setChecked(True)
        if requestedOutputs['tret_mean_ep_kpi']:
            self.checkBoxMeanRetTempEp.setChecked(True)
        if requestedOutputs['tret_max_ep_kpi']:
            self.checkBoxMaxRetTempEp.setChecked(True)
        if requestedOutputs['tret_min_ep_kpi']:
            self.checkBoxMinRetTempEp.setChecked(True)
        if requestedOutputs['qsup_heat_ep_kpi']:
            self.checkBoxQsupHeatEp.setChecked(True)
        if requestedOutputs['qsup_cold_ep_kpi']:
            self.checkBoxQsupColdEp.setChecked(True)
        if requestedOutputs['qsup_ep_kpi']:
            self.checkBoxQsupEnergyEp.setChecked(True)
            
        #lines
        if requestedOutputs['qamb_kpi']:
            self.checkBoxQambLines.setChecked(True)
        if requestedOutputs['volume_kpi']:
            self.checkBoxVolumeLines.setChecked(True)
            
        #System
        if requestedOutputs['qsup_heat_spec_c_kpi']:
            self.checkBoxQsupHeatSpec.setChecked(True)
        if requestedOutputs['qsup_cold_spec_c_kpi']:
            self.checkBoxQsupColdSpec.setChecked(True)
        if requestedOutputs['qsup_spec_c_kpi']:
            self.checkBoxQsupEnergySpec.setChecked(True)      
        if requestedOutputs['qsup_heat_density_c_kpi']:
            self.checkBoxQsupHeatDensity.setChecked(True)
        if requestedOutputs['qsup_cold_density_c_kpi']:
            self.checkBoxQsupColdDensity.setChecked(True)
        if requestedOutputs['qsup_density_c_kpi']:
            self.checkBoxQsupEnergyDensity.setChecked(True)   
        if requestedOutputs['qsup_heat_linedensity_c_kpi']:
            self.checkBoxQsupHeatLineDensity.setChecked(True)
        if requestedOutputs['qsup_cold_linedensity_c_kpi']:
            self.checkBoxQsupColdLineDensity.setChecked(True)
        if requestedOutputs['qsup_linedensity_c_kpi']:
            self.checkBoxQsupEnergyLineDensity.setChecked(True)
        if requestedOutputs['eff_width']:
            self.checkBoxQEffWidth.setChecked(True)
            
        self.outputTimestep.setValue(float(requestedOutputs['dt_outputs']))
        self.progress.setValue(0)
            
        #rbtn temporal/kpis
        self.rbtn_temporal.toggled.connect(self.onClickedRadio)
        self.rbtn_kpis.toggled.connect(self.onClickedRadio)
        
        self.rbtn_temporal.setChecked(True)
        
        #btn select/unselect
        self.btn_select_all_customers.clicked.connect(lambda: self.select_all(True))
        self.btn_select_all_ep.clicked.connect(lambda: self.select_all(True))
        self.btn_select_all_network.clicked.connect(lambda: self.select_all(True))
        self.btn_select_all_system.clicked.connect(lambda: self.select_all(True))

        self.btn_unselect_all_customers.clicked.connect(lambda: self.select_all(False))
        self.btn_unselect_all_ep.clicked.connect(lambda: self.select_all(False))
        self.btn_unselect_all_network.clicked.connect(lambda: self.select_all(False))
        self.btn_unselect_all_system.clicked.connect(lambda: self.select_all(False))
            
    def onClickedRadio(self):
        if self.rbtn_temporal.isChecked():
            self.groupBox_customer_temporal.show()
            self.groupBox_ep_temporal.show()
            self.groupBox_network_temporal.show()
            self.groupBox_system_temporal.show()
            self.groupBox_customer_kpis.hide()
            self.groupBox_ep_kpis.hide()
            self.groupBox_network_kpis.hide()
            self.groupBox_system_kpis.hide()
        else:
            self.groupBox_customer_temporal.hide()
            self.groupBox_ep_temporal.hide()
            self.groupBox_network_temporal.hide()
            self.groupBox_system_temporal.hide()  
            self.groupBox_customer_kpis.show()
            self.groupBox_ep_kpis.show()
            self.groupBox_network_kpis.show()
            self.groupBox_system_kpis.show()
            
    def select_all(self,check):
        tab_name = self.tabWidget.currentWidget().objectName()        
        if tab_name=='tab_customers':
            if self.rbtn_temporal.isChecked():
                checkboxes = self.groupBox_customer_temporal.findChildren(QCheckBox)
            else:
                checkboxes = self.groupBox_customer_kpis.findChildren(QCheckBox)
            for checkbox in checkboxes:
                checkbox.setChecked(check)
        elif tab_name=='tab_energy_plants':
            if self.rbtn_temporal.isChecked():
                checkboxes = self.groupBox_ep_temporal.findChildren(QCheckBox)
            else:
                checkboxes = self.groupBox_ep_kpis.findChildren(QCheckBox)
            for checkbox in checkboxes:
                checkbox.setChecked(check)
        elif tab_name=='tab_network':
            if self.rbtn_temporal.isChecked():
                checkboxes = self.groupBox_network_temporal.findChildren(QCheckBox)
            else:
                checkboxes = self.groupBox_network_kpis.findChildren(QCheckBox)
            for checkbox in checkboxes:
                checkbox.setChecked(check)
        else:
            if self.rbtn_temporal.isChecked():
                checkboxes = self.groupBox_system_temporal.findChildren(QCheckBox)
            else:
                checkboxes = self.groupBox_system_kpis.findChildren(QCheckBox)
            for checkbox in checkboxes:
                checkbox.setChecked(check)
    
    def update_progress(self,progress):
        self.progress.setValue(progress)

    def update_finished(self,message):
        self.process_running=False
        closeDialog(self)            
            

class BuildNetworkModelDialog(QDialog):
    def __init__(self,dlg_main):
        """Constructor."""
        super().__init__()
        self.setWindowTitle(self.tr("build_network_model")) 
        self.process_running=False
        self.dlg_main=dlg_main
        
        #networks
        layout_networks=QVBoxLayout()
        label_networks =QLabel(tr('@default',"networks"))
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
        self.checkbox_reinvokeFeatures = QCheckBox(self.tr("reinvoke_feature_templates"))
        self.checkbox_reinvokeFeatures.setChecked(True)
        
        #buttons     
        layout_buttons = QHBoxLayout()
        self.btn_buildNetworkModel=QPushButton(self.tr("build_network_model"))
        layout_buttons.addWidget(self.btn_buildNetworkModel)
        self.btn_cancel=QPushButton(tr('@default',"cancel"))
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
        
class RunNetworkModelDialog(QDialog):
    def __init__(self,plugin_dir,config):
        """Constructor."""
        super().__init__()
        self.setWindowTitle(self.tr("run_network_model")) 
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
        label_simtime =QLabel(self.tr("simulation"))
        font=label_simtime.font()
        font.setPointSize(12)
        label_simtime.setFont(font)      
      
        #radio buttons calc type
        self.btngroup_calc_type = QButtonGroup()
        layout_rbtn_calc_type = QHBoxLayout()
        self.rbtn_calc_type_periodic = QRadioButton(self.tr('periodic'))
        self.rbtn_calc_type_dynamic = QRadioButton(self.tr('dynamic'))
        self.btngroup_calc_type.addButton(self.rbtn_calc_type_periodic)
        self.btngroup_calc_type.addButton(self.rbtn_calc_type_dynamic)
        layout_rbtn_calc_type.addWidget(self.rbtn_calc_type_periodic)
        layout_rbtn_calc_type.addWidget(self.rbtn_calc_type_dynamic)

        
        #maximal timestep
        layout_max_timestep = QHBoxLayout()
        label_max_timestep =QLabel(self.tr("maximal_timestep"))
        layout_max_timestep.addWidget(label_max_timestep)
        self.max_timestep=QLineEdit(self.networkSimData['max_timestep'])
        layout_max_timestep.addWidget(self.max_timestep)
        
        #startup time
        layout_startup = QVBoxLayout()
        self.label_startup =QLabel(self.tr("startup"))
        font=self.label_startup.font()
        font.setPointSize(10)
        self.label_startup.setFont(font)
        layout_startupDate = QHBoxLayout()
        self.label_calcStartupFrom =QLabel(self.tr("from"))
        layout_startupDate.addWidget(self.label_calcStartupFrom)
        
        #radio buttons startup type
        self.btngroup_startup_type = QButtonGroup()
        layout_rbtn_startup_type = QHBoxLayout()
        self.rbtn_startup_type_periodic = QRadioButton(self.tr('periodic'))
        self.rbtn_startup_type_dynamic = QRadioButton(self.tr('dynamic'))
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

        self.label_calcStartupTo =QLabel(self.tr("to"))
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
        self.label_numb_periods =QLabel(self.tr("no_periods"))
        layout_numb_periods.addWidget(self.label_numb_periods)    
        self.numb_periods =QSpinBox()
        self.numb_periods.setValue(int(self.networkSimData['numb_of_periods']))
        self.numb_periods.setMinimum(1) 
        layout_numb_periods.addWidget(self.numb_periods)        

        #simulation time
        layout_calctime = QVBoxLayout()
        label_calctime =QLabel(self.tr("simulation_time"))
        font=label_calctime.font()
        font.setPointSize(12)
        label_calctime.setFont(font)
        
        layout_calcdate = QHBoxLayout()
        label_calcFrom =QLabel(self.tr("from"))
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

        label_calcTo =QLabel(self.tr("to"))
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
        self.btn_runModel=QPushButton(self.tr("run_network"))
        layout_buttons.addWidget(self.btn_runModel)
        self.btn_cancel=QPushButton(tr('@default','cancel'))
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
        if self.rbtn_calc_type_dynamic.isChecked():
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
    def __init__(self,config,conn,plugin_dir):
        """Constructor."""
        super().__init__()
        self.setWindowTitle(tr('@default',"customer_model_calibration")) 
        self.cur=conn.cursor(cursor_factory = psycopg2.extras.RealDictCursor)   
        self.config=config
        self.process_running=False
        
        self.textEdit=QTextEdit(tr('@default','info_calibration'))
        self.textEdit.setReadOnly(True)

            
        #table templates
        layout_templates = QVBoxLayout()
        label_templates_title =QLabel(tr('@default',"templates"))
        font=label_templates_title.font()
        font.setPointSize(15)
        label_templates_title.setFont(font)
        layout_templates.addWidget(label_templates_title)

        self.btn_openTemplate=QPushButton()
        layout_template_btn=QHBoxLayout()
        self.btn_openTemplate.setIcon(QIcon(":/images/themes/default/mActionFileOpen.svg"))
        self.btn_openTemplate.setToolTip(tr('@default','tooltip_openParmrunTemplate'))
        layout_template_btn.addWidget(self.btn_openTemplate)
        layout_template_btn.addItem(QSpacerItem(0,0,QSizePolicy.Policy.Expanding,QSizePolicy.Policy.Minimum))
        layout_templates.addLayout(layout_template_btn)
        
        self.tableWidget_templates = QTableWidget(0,4)   
        self.tableWidget_templates.setHorizontalHeaderLabels([tr('@default','id'),tr('@default','template'),tr('@default',"parametric_runs"),tr('@default',"used")]) 
        layout_templates.addWidget(self.tableWidget_templates)
        
        #table select customers
        layout_selectCustomers = QVBoxLayout()
        label_selCust_title =QLabel(tr('@default',"customers"))
        font=label_selCust_title.font()
        font.setPointSize(15)
        label_selCust_title.setFont(font)
        layout_selectCustomers.addWidget(label_selCust_title)
        layout_customer_btn=QHBoxLayout()
        self.btn_startCallibration=QPushButton()
        self.btn_startCallibration.setIcon(QIcon(os.path.join(plugin_dir, "icons/Calibration.png")))
        self.btn_startCallibration.setToolTip(tr('@default','tooltip_startCallibration'))
        layout_customer_btn.addWidget(self.btn_startCallibration)
        layout_customer_btn.addItem(QSpacerItem(0,0,QSizePolicy.Policy.Expanding,QSizePolicy.Policy.Minimum))
        layout_selectCustomers.addLayout(layout_customer_btn)
        self.tableWidget_customer = QTableWidget(0,3)   
        self.tableWidget_customer.setHorizontalHeaderLabels([tr('@default','id'),tr('@default','template'),tr('@default',"parametric_runs")]) 
        layout_selectCustomers.addWidget(self.tableWidget_customer)

        #Results
        layout_results = QVBoxLayout()
        label_results_title =QLabel(tr('@default','parmrun_results'))#"Results (sorted by leftmost output parameter)")
        font=label_results_title.font()
        font.setPointSize(15)
        label_results_title.setFont(font)
        layout_results.addWidget(label_results_title)
                
        layout_result_btn = QHBoxLayout()
        self.btn_showCallibCust=QPushButton()
        self.btn_showCallibCust.setIcon(QIcon(":/images/themes/default/mActionFileOpen.svg"))
        self.btn_showCallibCust.setToolTip(tr('@default','tooltip_openParmrunResult'))
        layout_result_btn.addWidget(self.btn_showCallibCust)
        self.btn_saveCallibration=QPushButton()
        self.btn_saveCallibration.setIcon(QIcon(":/images/themes/default/mActionFileSave.svg"))
        self.btn_saveCallibration.setToolTip(tr('@default','tooltip_saveParmrunResult'))
        layout_result_btn.addWidget(self.btn_saveCallibration)
        layout_result_btn.addItem(QSpacerItem(0,0,QSizePolicy.Policy.Expanding,QSizePolicy.Policy.Minimum))
        layout_results.addLayout(layout_result_btn)
        self.tabwidget = QTabWidget()
        layout_results.addWidget(self.tabwidget)
        
            
        #progress bar
        self.progress=QProgressBar()       
        
        #---------------set layouts together-------------------
        layout_win = QVBoxLayout()
        layout_win.addWidget(self.textEdit)
        layout_win.addLayout(layout_templates)
        layout_win.addLayout(layout_selectCustomers)
        layout_win.addLayout(layout_results)
        layout_win.addWidget(self.progress)
        
        self.setLayout(layout_win)
        
    def update_finished(self,message):
        updateParmruns(self,message)
        self.process_running=False
                
    def update_progress(self,progress):
        self.progress.setValue(progress)
        
    def show_error_message(self, message):
        # Show the error message in a messageBar
        iface.messageBar().pushMessage("Error", message, level=MessageCritical)
        
class FeatureModelParmDlg(QDialog):
    def __init__(self,cur,config):
        """Constructor."""
        super().__init__()
        self.setWindowTitle(tr('@default',"title_feature_model_parameter_mapping")) 
        self.loadedMappingParms={}
        self.cur=cur
        self.config=config
        
        #radio buttons
        layout_rbtn = QHBoxLayout()
        self.rbtn_customers = QRadioButton(tr('@default','customers'))
        self.rbtn_customers.setChecked(True)
        self.rbtn_plants = QRadioButton(tr('@default','energy_plants'))
        self.rbtn_customers.toggled.connect(self.onClickedRadio)
        self.rbtn_plants.toggled.connect(self.onClickedRadio)
        
        layout_rbtn.addWidget(self.rbtn_customers)
        layout_rbtn.addWidget(self.rbtn_plants)
        
        #list widget for layer attributes
        layout_listWidget_featureFields = QVBoxLayout()
        label_listWidget_featureFields=QLabel(tr('@default',"fields"))
        layout_listWidget_featureFields.addWidget(label_listWidget_featureFields)
        self.listWidget_featureFields = QListWidget()
        layout_listWidget_featureFields.addWidget(self.listWidget_featureFields)
        self.listWidget_featureFields.itemDoubleClicked.connect(self.mapAttributesDoubleClick)
        
        info_feature_parm_mapping=QTextEdit(tr('@default','info_feature_parm_mapping'))
        info_feature_parm_mapping.setReadOnly(True)

       
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
        self.tableWidget_parameters = QTableWidget(0,7)   
        self.tableWidget_parameters.setHorizontalHeaderLabels([tr('@default','id'),tr('@default','mapping_expression'),tr('@default','mapping_direction'),tr('@default','parameter_name'),tr('@default','model_name'),tr('@default','macro_name'),tr('@default','description')])
        
        #---------------ok/cancel buttons     
        layout_buttons = QHBoxLayout()
        self.btn_ok=QPushButton(tr('@default',"ok"))
        layout_buttons.addWidget(self.btn_ok)
        self.btn_cancel=QPushButton(tr('@default',"cancel"))
        layout_buttons.addWidget(self.btn_cancel)
        
        #---------------set layouts together-------------------
        layout_win = QVBoxLayout()
        layout_win.addWidget(info_feature_parm_mapping)
        layout_win.addLayout(layout_rbtn)
        layout_win.addLayout(layout_listWidget_featureFields)
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
            iface.messageBar().pushMessage("Info", "No model parameter selected!", level=MessageInfo)
            
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

        sql="""SELECT * FROM model_parms WHERE type={} ORDER BY id;""".format(1 if self.rbtn_customers.isChecked() else 2) # nosec B608
        self.cur.execute(sql)
        table=self.tableWidget_parameters
        for i,parm in enumerate(self.cur.fetchall()):
            self.loadedMappingParms[parm['id']]={'parm_name' : parm['parm_name'],'model_name' : parm['model_name'],'mapping_expression' : parm['mapping_expression'],'macro_name' : parm['macro_name'],'mapping_direction' : parm['mapping_direction'],'description' : parm['description']}
            table.insertRow(i)
            item = QTableWidgetItem(str(parm['id']))
            item.setFlags(item.flags() & ~qt_item_flag("ItemIsEditable"))

            table.setItem(i,0,item)
            table.setItem(i,1,QTableWidgetItem(parm['mapping_expression']))
                        
            comboBox = QComboBox()
            comboBox.addItems(['<-->','<--','-->'])
            #comboBox.addItems(['-->'])
            comboBox.setCurrentText(parm['mapping_direction'])
            table.setCellWidget(i, 2, comboBox)  
            
            table.setItem(i,3,QTableWidgetItem(parm['parm_name']))
            table.setItem(i,4,QTableWidgetItem(parm['model_name']))
            table.setItem(i,5,QTableWidgetItem(parm['macro_name'])) 
            table.setItem(i,6,QTableWidgetItem(parm['description'])) 

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
""".format(self.config['versionName'],self.feature_template.itemText(s)) # nosec B608
        else:
            sql="""SELECT f_dec.comp_name
    FROM energy_plant_templates ep_t, "{}".feature_decoupling f_dec
    WHERE ep_t.template_name='{}' AND f_dec.template=ep_t.template AND type='energy_plant';
""".format(self.config['versionName'],self.feature_template.itemText(s)) # nosec B608
        #print(sql)
        self.cur.execute(sql)
        self.listWidget_featureModels.addItems([i['comp_name'] for i in self.cur.fetchall()])
        
    def saveListContent(self):
        #print('Save list conetent')
        if self.rbtn_customers.isChecked():
            type='customer'
        else:
            type='energy_plant'

        sql="""SELECT template FROM public.{}_templates WHERE template_name='{}';""".format(type,template)# nosec B608
        #print(sql)
        self.cur.execute(sql)
        template_id=self.cur.fetchone()['template']
        #print(template_id)
        
        sql="""DELETE FROM "{}".feature_decoupling WHERE template={};\n""".format(self.config['versionName'],template_id) # nosec B608
        sql+='\n'.join(["""INSERT INTO "{}".feature_decoupling (template,comp_name,type) VALUES ({},'{}','{}');""".format(self.config['versionName'],template_id,self.listWidget_featureModels.item(i).text(),type) for i in range(self.listWidget_featureModels.count())]) # nosec B608

        try:
            no_submodels=int(self.no_submodels.text())
            self.cur.execute('SELECT row_number() OVER(ORDER BY id) enum, id FROM "{}".{}s;'.format(self.config['versionName'],type)) # nosec B608
            f_ids=self.cur.fetchall()
            submodel_counter=(getLineNetworks(self.cur,self.config)[-1] if getLineNetworks(self.cur,self.config) else 0)
            if no_submodels>0:
                self.cur.execute('SELECT count(*) AS count FROM "{}".{}s;'.format(self.config['versionName'],type)) # nosec B608
                no_features=self.cur.fetchone()['count']
                f_per_submodel=int(no_features/no_submodels)
                rest=no_features%no_submodels
                                
                for f_id in f_ids:
                    if f_id['enum']>submodel_counter*f_per_submodel+(no_features%no_submodels-rest+1 if rest>0 else no_features%no_submodels):
                        submodel_counter+=1
                        rest-=1
                    sql+='UPDATE "{}".{}s SET submodel={} WHERE id={};'.format(self.config['versionName'],type,submodel_counter+1,f_id['id']) # nosec B608
            elif no_submodels==0:
                sql+='UPDATE "{}".{}s f SET submodel = s_m.submodel::int FROM (SELECT * FROM "{}".submodels) s_m WHERE ST_DWithin(s_m.geom,f.geom,0.001);'.format(self.config['versionName'],type,self.config['versionName']) # nosec B608
            else:
                iface.messageBar().pushMessage("Error", "Please enter a positive integer number in number of feature submodels!", level=MessageCritical)
        except:
            QgsMessageLog.logMessage(
                traceback.format_exc(),
                "Districts",
                MessageCritical
            )

        
        #print(sql)
        if sql:
            self.cur.execute(sql)
            
    def removeSel(self):
        listItems=self.listWidget_featureModels.selectedItems()
        if not listItems: 
            return        
        for item in listItems:
            self.listWidget_featureModels.takeItem(self.listWidget_featureModels.row(item))

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
        self.setWindowTitle(self.tr("modelling_settings"))    
        self.plugin_dir=plugin_dir
        self.cur=cur
        #-------------Settings FD pipe ---------------
        #titel
        label_fd_pipe_title =QLabel(self.tr("finite_difference_pipe_model"))
        font=label_fd_pipe_title.font()
        font.setPointSize(15)
        label_fd_pipe_title.setFont(font)
        
        #labels
        layout_fd_pipe_label = QVBoxLayout()
        
        label_fd_pipe_discretization =QLabel(self.tr("meter_per_node"))
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
        label_node_title =QLabel(self.tr("node_model"))
        font=label_node_title.font()
        font.setPointSize(15)
        label_node_title.setFont(font)
        
        #labels
        layout_node_label = QVBoxLayout()
        
        label_node_vol =QLabel(self.tr("node_volume"))
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
        label_ambient_title =QLabel(self.tr("ambient_temperatur_settings"))
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
        
        label_ground_conductivity =QLabel(self.tr('ground_thermal_conductivity'))
        layout_ground_label.addWidget(label_ground_conductivity)

        label_ground_model =QLabel(self.tr("ground_surface_layer_temperature_model"))
        layout_ground_label.addWidget(label_ground_model)
        
        
        self.label_amb_kusuda_rho =QLabel(self.tr("surface_layer_density"))
        layout_ground_label.addWidget(self.label_amb_kusuda_rho)
        
        self.label_amb_kusuda_cp =QLabel(self.tr("specific_heat_capacity_surface_layer"))
        layout_ground_label.addWidget(self.label_amb_kusuda_cp)
        
        self.label_amb_kusuda_lambda =QLabel(self.tr("thermal_conductivity_surface_layer"))
        layout_ground_label.addWidget(self.label_amb_kusuda_lambda)
        
        self.label_amb_kusuda_depth =QLabel(self.tr("surface_layer_depth"))
        layout_ground_label.addWidget(self.label_amb_kusuda_depth)
        
        
        self.label_amb_ground_profile =QLabel(self.tr("ground_temperatur_timeseries"))
        layout_ground_label.addWidget(self.label_amb_ground_profile)
        
        
        self.label_amb_ground_temp =QLabel(self.tr("constant_ground_temperatur"))
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
        
        label_duct_model =QLabel(self.tr("duct_model"))
        layout_duct_label.addWidget(label_duct_model)            
        
        self.label_amb_duct_profile =QLabel(self.tr("duct_temperatur_timeseries"))
        layout_duct_label.addWidget(self.label_amb_duct_profile)
        
        self.label_amb_duct_temp =QLabel(self.tr("constant_duct_temperatur"))
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
        label_air_title =QLabel(self.tr("ambient_air_temperatur"))
        font=label_air_title.font()
        font.setPointSize(12)
        label_air_title.setFont(font)
        
        #labels
        layout_air_label = QVBoxLayout()
        
        label_amb_ambient_air_model =QLabel(self.tr("ambient_air_model"))
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
        sql="""SELECT id FROM {} ORDER BY id;""".format(table_name)# nosec B608
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
            self.amb_kusuda_rho.setHidden(False)
            self.amb_kusuda_cp.setHidden(False)
            self.amb_kusuda_lambda.setHidden(False)
            self.amb_kusuda_depth.setHidden(False)
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
            
            self.amb_kusuda_rho.setHidden(True)
            self.amb_kusuda_cp.setHidden(True)
            self.amb_kusuda_lambda.setHidden(True)
            self.amb_kusuda_depth.setHidden(True)
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
            self.amb_kusuda_rho.setHidden(True)
            self.amb_kusuda_cp.setHidden(True)
            self.amb_kusuda_lambda.setHidden(True)
            self.amb_kusuda_depth.setHidden(True)
            self.label_amb_ground_profile.setHidden(True)
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
