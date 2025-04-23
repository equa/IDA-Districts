from plugins.utility_functions.db import *
from qgis.PyQt import uic, QtWidgets, QtCore
from qgis.PyQt.QtCore import Qt
from qgis.PyQt.QtWidgets import QCheckBox,QComboBox,QHeaderView,QWidget,QMainWindow,QPushButton,QHBoxLayout,QVBoxLayout,QLabel,QLineEdit, QTableWidget,QComboBox,QTableView,QTabWidget,QTableWidgetItem
     
import copy

class ConnectionsDialog(QMainWindow):
    def __init__(self,title,headers):
        """Constructor"""
        super().__init__()
        self.setWindowTitle(title)   
        
        self.assetgroup=title.split(':')[-1].strip()
        #table buttons     
        layout_buttons_table = QHBoxLayout()
        self.btn_add=QPushButton("Add")
        layout_buttons_table.addWidget(self.btn_add)
        self.btn_delete=QPushButton("Delete")
        layout_buttons_table.addWidget(self.btn_delete)
        
        #Table
        layout_table = QHBoxLayout() 
        self.tableWidget = QTableWidget(0,len(headers))   
        self.tableWidget.setHorizontalHeaderLabels(headers)     
        self.tableWidget.setHorizontalScrollBarPolicy(QtCore.Qt.ScrollBarAlwaysOff)
        self.tableWidget.setColumnCount(len(headers))
        layout_table.addWidget(self.tableWidget)
        self.traceChanges=[]

        #buttons     
        layout_buttons = QHBoxLayout()
        self.btn_ok=QPushButton("Save")
        layout_buttons.addWidget(self.btn_ok)
        self.btn_cancel=QPushButton("Cancel")
        layout_buttons.addWidget(self.btn_cancel)
        
        #---------------set layouts together-------------------
        layout_win = QVBoxLayout()
        layout_win.addLayout(layout_buttons_table)
        layout_win.addLayout(layout_table)
        layout_win.addLayout(layout_buttons)
        
        widget=QWidget()
        widget.setLayout(layout_win)
        self.setCentralWidget(widget)
        self.traceTableValues={}      
        self.resize(900, 500)  # Width of 900 pixels, height of 500 pixels        
    
    def changedDropdownItem(self, s):
        print('changed drop down item')
        combo = self.sender()  # Get the combo box that sent the signal
        selected_option = combo.currentText().split(':')[0]
        print(selected_option)

        index = self.tableWidget.indexAt(combo.pos())
        row = index.row()
        print(row)
        self.traceTableValues[row]=[self.traceTableValues[row][0],self.traceTableValues[row][1],self.traceTableValues[row][2],self.traceTableValues[row][3],self.traceTableValues[row][4],self.traceTableValues[row][5],self.traceTableValues[row][6],self.traceTableValues[row][7],self.traceTableValues[row][8],selected_option]
        print(self.traceTableValues[row])
    
    def changedCheckboxState(self,s):
        print('+++changed state++')
        checkbox = self.sender()
        index = self.tableWidget.indexAt(checkbox.pos())
        row = index.row()
        col = index.column()
        print(row)
        print(col)
        print(s)
        if s==2: #checked
            item=QTableWidgetItem('')
            self.tableWidget.setItem(row,5,item)
            item=QTableWidgetItem('')
            item.setFlags(item.flags() & ~Qt.ItemIsEnabled)
            self.tableWidget.setItem(row,4,item)
            try:
                self.traceTableValues[row]=[self.traceTableValues[row][0],'',self.traceTableValues[row][2],self.traceTableValues[row][3],self.traceTableValues[row][4],self.traceTableValues[row][5],self.traceTableValues[row][6],True,self.traceTableValues[row][8],self.traceTableValues[row][9]]
            except:
                pass
        else:
            item=QTableWidgetItem('')
            self.tableWidget.setItem(row,4,item)
            item=QTableWidgetItem('')
            item.setFlags(item.flags() & ~Qt.ItemIsEnabled)
            self.tableWidget.setItem(row,5,item)
            try:
                self.traceTableValues[row]=[self.traceTableValues[row][0],self.traceTableValues[row][1],self.traceTableValues[row][2],'',self.traceTableValues[row][4],self.traceTableValues[row][5],self.traceTableValues[row][6],False,self.traceTableValues[row][8],self.traceTableValues[row][9]]
            except:
                pass
        
        print(self.traceTableValues)
        
    def changedItem(self, item):
        row = item.row()
        print('changed')
        try:
            if self.traceTableValues[row][0]!=self.tableWidget.item(row,4).text(): #p
                self.traceTableValues[row][1]=self.tableWidget.item(row,4).text()
            if self.traceTableValues[row][2]!=self.tableWidget.item(row,5).text(): #m
                self.traceTableValues[row][3]=self.tableWidget.item(row,5).text()
            if self.traceTableValues[row][4]!=self.tableWidget.item(row,3).text(): #T
                self.traceTableValues[row][5]=self.tableWidget.item(row,3).text()
        except:
            pass
        print(self.traceTableValues)

class IDA_Districts_NameDialog(QMainWindow):
    def __init__(self,title,inputs,newConnBundleType,newConnType):
        """Constructor."""
        super().__init__()
        self.setWindowTitle(title)     
        
        #input 
        i=0
        layout_label = QVBoxLayout() 
        layout_input = QVBoxLayout() 
        self.input=[]
        for input in inputs:
            #label 
            label =QLabel(input['label'])
            layout_label.addWidget(label)
            
            #input          
            self.input.append(QLineEdit(input['text']))
            layout_input.addWidget(self.input[i])
            i+=1    

        #connection type
        if newConnBundleType:
            #label 
            label =QLabel('Connection type:')
            layout_label.addWidget(label)
            
            #dropdown
            layout_input_conntype=QHBoxLayout()
            self.ConnectionType =QComboBox()
            layout_input_conntype.addWidget(self.ConnectionType)
            
            #add new connection type
            self.btn_add_conntype =QPushButton("Add")
            layout_input_conntype.addWidget(self.btn_add_conntype)
            
            layout_input.addLayout(layout_input_conntype)
            
        #new connection type
        if newConnType:
            #label 
            label =QLabel('Inlet type:')
            layout_label.addWidget(label)
            
            label =QLabel('Outlet type:')
            layout_label.addWidget(label)
            
            #dropdown
            layout_input_conntype=QVBoxLayout()
            self.inletConnectionType =QComboBox()
            layout_input_conntype.addWidget(self.inletConnectionType)
            
            self.outletConnectionType =QComboBox()
            layout_input_conntype.addWidget(self.outletConnectionType)
            
            #add button for new inlet connection type
            self.btn_add_conntype =QPushButton("Add")
            
            #set connection type settings together
            layout_input_conntype_settings=QHBoxLayout()
            layout_input_conntype_settings.addLayout(layout_input_conntype)
            layout_input_conntype_settings.addWidget(self.btn_add_conntype)
            
            layout_input.addLayout(layout_input_conntype_settings)
                 
        #set name settings together
        layout_name = QHBoxLayout() 
        layout_name.addLayout(layout_label)
        layout_name.addLayout(layout_input)
        
        #buttons     
        layout_buttons = QHBoxLayout()
        self.btn_ok=QPushButton("Ok")
        layout_buttons.addWidget(self.btn_ok)
        self.btn_cancel=QPushButton("Cancel")
        layout_buttons.addWidget(self.btn_cancel)
        
        #---------------set layouts together-------------------
        layout_win = QVBoxLayout()
        layout_win.addLayout(layout_name)
        layout_win.addLayout(layout_buttons)
        layout_win.addStretch()
        
        widget=QWidget()
        widget.setLayout(layout_win)
        self.setCentralWidget(widget)

class DefaultsDialog(QMainWindow):
    def __init__(self,type_name,title,inputs,cur):     
        """Initialize GUI for defaults layers"""
        super().__init__()
        self.setWindowTitle(title) 
        self.cur=cur
        
        layout_input_label_general = QVBoxLayout()
        layout_input_label_physical = QVBoxLayout()
        layout_input_value_general = QVBoxLayout()  
        layout_input_value_physical = QVBoxLayout()  
        self.input={}
        # Initialize tab screen
        self.tabs = QTabWidget()
        self.tab_general = QWidget()
        self.tab_physical = QWidget()
        # Add tabs
        self.tabs.addTab(self.tab_general,"General")
        self.tabs.addTab(self.tab_physical,"Physical Data")
        
        self.tab_general.layout = QVBoxLayout(self)
        self.tab_physical.layout = QVBoxLayout(self)
        
        layout_input_general=QHBoxLayout()
        layout_input_physical=QHBoxLayout()

        for input in inputs:
            #labels
            if input['value'][1]!=2:
                label = QLabel(input['label'])
                if input['value'][2]=='general': 
                    layout_input_label_general.addWidget(label)
                elif input['value'][2]=='physical': 
                    layout_input_label_physical.addWidget(label)    
            
            #values
            if input['value'][1]==0: 
                self.input[input['value'][0]] = QComboBox()
            if input['value'][0]=='assetgroup':
                self.input['assetgroup'].currentTextChanged.connect(lambda signal: self.setAssettypes(signal,type_name))
            if input['value'][1]==1:
                self.input[input['value'][0]] = QLineEdit()
            if input['value'][1]==2:
                self.input[input['value'][0]] = QCheckBox(input['label'])
                if input['value'][2]=='general': 
                    self.tab_general.layout.addWidget(self.input[input['value'][0]])
                elif input['value'][2]=='physical': 
                    self.tab_physical.layout.addWidget(self.input[input['value'][0]])
            else:
                if input['value'][2]=='general': 
                    layout_input_value_general.addWidget(self.input[input['value'][0]])
                elif input['value'][2]=='physical': 
                    layout_input_value_physical.addWidget(self.input[input['value'][0]])
        
        #set name settings together
        layout_input_general.addLayout(layout_input_label_general)
        layout_input_general.addLayout(layout_input_value_general)
        self.tab_general.layout.addLayout(layout_input_general)
        
        layout_input_physical.addLayout(layout_input_label_physical)
        layout_input_physical.addLayout(layout_input_value_physical)
        self.tab_physical.layout.addLayout(layout_input_physical)
        
        self.tab_general.setLayout(self.tab_general.layout)
        self.tab_physical.setLayout(self.tab_physical.layout)
        
        #buttons     
        layout_buttons = QHBoxLayout()
        self.btn_ok=QPushButton("Ok")
        layout_buttons.addWidget(self.btn_ok)
        self.btn_cancel=QPushButton("Cancel")
        layout_buttons.addWidget(self.btn_cancel)
        
        #---------------set layouts together-------------------
        layout_win = QVBoxLayout()
        layout_win.addWidget(self.tabs)
        layout_win.addLayout(layout_buttons)
        layout_win.addStretch()
        
        widget=QWidget()
        widget.setLayout(layout_win)
        self.setCentralWidget(widget)
        
    def setAssettypes(self,s,type_name):
        print('set assettype')
        print(s)
        value=self.input['assetgroup'].currentText().split(':')[0]
        if value=='(no selection)': 
            self.input['assettype'].clear()
            self.input['assettype'].addItems(['(no selection)'])
        else:
            dropdownItems=getFilteredDropDownItems(self.cur,[type_name+'_assettypes','assettype','assettype_name','assetgroup',value])
            self.input['assettype'].clear()
            self.input['assettype'].addItems(['(no selection)']+dropdownItems)

class IDADistrictsDataCenterDialog(QMainWindow):
    def __init__(self):     
        """Initialize GUI for pipe laying algorithm"""
        super().__init__()
        self.setWindowTitle("Data Center")   
        
        #set climate 
        #title
        label_titel =QLabel('Climate data')
        font=label_titel.font()
        font.setPointSize(15)
        label_titel.setFont(font)
        
        #buttons
        self.btn_climate=QPushButton("Climate data")
        
        layout_climate=QVBoxLayout()
        layout_climate.addWidget(label_titel)
        layout_climate.addWidget(self.btn_climate)
        
        #Set defaults
        #title
        label_titel =QLabel('Defaults')
        font=label_titel.font()
        font.setPointSize(15)
        label_titel.setFont(font)
        
        #buttons
        self.btn_defaults_lines=QPushButton("Lines")
        self.btn_defaults_customers=QPushButton("Customers")
        self.btn_defaults_plants=QPushButton("Energy Plants")
        self.btn_defaults_devices=QPushButton("Devices")
        
        layout_defaults=QVBoxLayout()
        layout_defaults.addWidget(label_titel)
        layout_defaults.addWidget(self.btn_defaults_lines)
        layout_defaults.addWidget(self.btn_defaults_customers)
        layout_defaults.addWidget(self.btn_defaults_plants)
        layout_defaults.addWidget(self.btn_defaults_devices)
        
        #DB management
        #title
        label_titel =QLabel('DB management')
        font=label_titel.font()
        font.setPointSize(15)
        label_titel.setFont(font)
        
        #buttons
        self.btn_materials=QPushButton("Materials")
        self.btn_pipe_constructions=QPushButton("Pipe constructions")
        self.btn_pipes=QPushButton("Pipes")
        self.btn_pipe_bundle_types=QPushButton("Pipe bundle types")
        self.btn_dhw_profiles=QPushButton("DHW profiles")
        self.btn_temp_profiles=QPushButton("Temperature profiles")
        self.btn_internal_loads=QPushButton("Internal load profiles")
        self.btn_building_construction_standards=QPushButton("Building construction standards")
        self.btn_building_zone_templates=QPushButton("Building zone templates")
        self.btn_manageLinesAssetgroups=QPushButton("Lines")
        
        layout_DB=QVBoxLayout()
        layout_DB.addWidget(label_titel)
        layout_DB.addWidget(self.btn_materials)
        layout_DB.addWidget(self.btn_pipe_constructions)
        layout_DB.addWidget(self.btn_pipes)
        layout_DB.addWidget(self.btn_pipe_bundle_types)
        layout_DB.addWidget(self.btn_manageLinesAssetgroups)
        layout_DB.addWidget(self.btn_dhw_profiles)
        layout_DB.addWidget(self.btn_temp_profiles)
        layout_DB.addWidget(self.btn_internal_loads)
        layout_DB.addWidget(self.btn_building_construction_standards)
        layout_DB.addWidget(self.btn_building_zone_templates)
        
        #manage connection types
        #title
        label_titel =QLabel('Connection management')
        font=label_titel.font()
        font.setPointSize(15)
        label_titel.setFont(font)
        
        #buttons
        self.btn_connections=QPushButton("Connections")
        self.btn_connection_types=QPushButton("Connection types")
        self.btn_conn_bundle_types=QPushButton("Connection bundles")
        
        layout_connection_types=QVBoxLayout()
        layout_connection_types.addWidget(label_titel)
        layout_connection_types.addWidget(self.btn_connections)
        layout_connection_types.addWidget(self.btn_connection_types)
        layout_connection_types.addWidget(self.btn_conn_bundle_types)
        
        #manage templates
        #title
        label_titel =QLabel('Manage asset types')
        font=label_titel.font()
        font.setPointSize(15)
        label_titel.setFont(font)
        #manage assettype buttons
        layout_manage_btn=QVBoxLayout() 
        
        self.btn_manageCustomerAssetgroups=QPushButton("Customers")
        layout_manage_btn.addWidget(self.btn_manageCustomerAssetgroups)
        
        self.btn_manageEnergyPlantAssetgroups=QPushButton("Energy plants")
        layout_manage_btn.addWidget(self.btn_manageEnergyPlantAssetgroups)
        
        self.btn_manageDevicesAssetgroups=QPushButton("Devices")
        layout_manage_btn.addWidget(self.btn_manageDevicesAssetgroups)
        
        #set manageassettypes together
        layout_manage_assetgroups=QVBoxLayout()
        layout_manage_assetgroups.addWidget(label_titel)
        layout_manage_assetgroups.addLayout(layout_manage_btn)
        
        #manage network
        #title
        label_titel =QLabel('Manage networks')
        font=label_titel.font()
        font.setPointSize(15)
        label_titel.setFont(font)
        
        self.btn_manageNetworks=QPushButton("Networks")

        #set networks together
        layout_networks=QVBoxLayout()
        layout_networks.addWidget(label_titel)
        layout_networks.addWidget(self.btn_manageNetworks)
        
        #manage building templates
        #title
        label_titel =QLabel('Manage building templates')
        font=label_titel.font()
        font.setPointSize(15)
        label_titel.setFont(font)
        
        self.btn_manageBuildingTemplates=QPushButton("Building templates")
        
        #set building templates together
        layout_building_templates=QVBoxLayout()
        layout_building_templates.addWidget(label_titel)
        layout_building_templates.addWidget(self.btn_manageBuildingTemplates)
        
        #contracts
        #title
        label_titel =QLabel('Contracts')
        font=label_titel.font()
        font.setPointSize(15)
        label_titel.setFont(font)
        #manage assettype buttons
        layout_contracts_btn=QVBoxLayout()
                
        self.btn_contracts=QPushButton("Energy contracts")
        layout_contracts_btn.addWidget(self.btn_contracts)
        
        #set manageassettypes together
        layout_contracts=QVBoxLayout()
        layout_contracts.addWidget(label_titel)
        layout_contracts.addLayout(layout_contracts_btn)
        
        #---------------set layouts together-------------------
        layout_win = QVBoxLayout()
        layout_win.addLayout(layout_climate)
        layout_win.addLayout(layout_defaults)
        layout_win.addLayout(layout_DB)
        layout_win.addLayout(layout_connection_types)
        layout_win.addLayout(layout_manage_assetgroups)
        layout_win.addLayout(layout_networks)
        layout_win.addLayout(layout_building_templates)
        layout_win.addLayout(layout_contracts)
        layout_win.addStretch()
        
        widget=QWidget()
        widget.setLayout(layout_win)
        self.setCentralWidget(widget)
