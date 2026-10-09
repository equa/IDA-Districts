from qgis.PyQt.QtCore import Qt
from qgis.PyQt.QtWidgets import QButtonGroup, QFileDialog, QDialog, QTableWidgetItem, QCheckBox, QComboBox, QHeaderView, QWidget, QPushButton, QHBoxLayout, QVBoxLayout, QLabel, QLineEdit, QTableWidget, QComboBox, QTableView, QTabWidget
from qgis.PyQt.QtGui import QIcon
from qgis.core import QgsMessageLog, Qgis

from .utility_functions.dialog import *
from .utility_functions.utility import *

import traceback

class ExportResourcesDialog(QDialog):
    def __init__(self,cur,config):
        super().__init__()

        # Load UI
        ui_path = os.path.join(os.path.dirname(__file__), "ExportResources_dialog.ui")
        uic.loadUi(ui_path, self)
        self.cur=cur
        self.config=config
        self.table_columns={}
        self.tables={
            self.tableWidget_connections : 'connections',
            self.tableWidget_materials : 'materials'}
            
                
        self.tabWidget.setCurrentWidget(self.tab_connections) 
        
        #rbtn connections
        self.rbtn_connections.toggled.connect(self.onClickedRadioConnections)
        self.rbtn_conntypes.toggled.connect(self.onClickedRadioConnectiontypes)
        self.rbtn_conn_bundles.toggled.connect(self.onClickedRadioConnectionbundles)

        self.rbtn_materials.toggled.connect(self.onClickedRadioMaterials)
        self.rbtn_constructions.toggled.connect(self.onClickedRadioConstructions)
        self.rbtn_pipes.toggled.connect(self.onClickedRadioPipes)
        self.rbtn_pipe_bundles.toggled.connect(self.onClickedRadioPipebundles)

        self.rbtn_customers.toggled.connect(self.onClickedRadioCustomerTemplates)
        self.rbtn_energy_plants.toggled.connect(self.onClickedRadioEnergyplantsTemplates)    

        #btn tables
        self.btn_select_all_connections.clicked.connect(lambda: self.select_all(True))
        self.btn_select_all_pipes.clicked.connect(lambda: self.select_all(True))
        self.btn_select_all_templates.clicked.connect(lambda: self.select_all(True))

        self.btn_unselect_all_connections.clicked.connect(lambda: self.select_all(False))
        self.btn_unselect_all_pipes.clicked.connect(lambda: self.select_all(False))
        self.btn_unselect_all_templates.clicked.connect(lambda: self.select_all(False))
        
        #load data
        self.loadTableData(self.tableWidget_connections,self.tables[self.tableWidget_connections])
        self.loadTableData(self.tableWidget_connection_types,'connection_types')
        self.loadTableData(self.tableWidget_connection_bundles,'conn_bundle_types')

        self.loadTableData(self.tableWidget_materials,self.tables[self.tableWidget_materials])
        self.loadTableData(self.tableWidget_constructions,'pipe_constructions')
        self.loadTableData(self.tableWidget_pipes,'pipes')
        self.loadTableData(self.tableWidget_pipe_bundles,'pipe_bundle_types')

        self.loadTableData(self.tableWidget_customer_templates,'customer_templates')
        self.loadTableData(self.tableWidget_energy_plant_templates,'energy_plant_templates')
        
        self.rbtn_connections.setChecked(True)
        self.rbtn_materials.setChecked(True)
        self.rbtn_customers.setChecked(True)
        
    def select_all(self,check):
        tab_name = self.tabWidget.currentWidget().objectName()
        if tab_name=='tab_connections':
            if self.rbtn_connections.isChecked():
                self.checkTableEntries(self.tableWidget_connections,check)
            elif self.rbtn_conntypes.isChecked():
                self.checkTableEntries(self.tableWidget_connection_types,check)
            else:
                self.checkTableEntries(self.tableWidget_connection_bundles,check)
        elif tab_name=='tab_pipes':
            if self.rbtn_materials.isChecked():
                self.checkTableEntries(self.tableWidget_materials,check)
            elif self.rbtn_constructions.isChecked():
                self.checkTableEntries(self.tableWidget_constructions,check)
            elif self.rbtn_pipes.isChecked():
                self.checkTableEntries(self.tableWidget_pipes,check)
            else:
                self.checkTableEntries(self.tableWidget_pipe_bundles,check)
        else:
            if self.rbtn_customers.isChecked():
                self.checkTableEntries(self.tableWidget_customer_templates,check)
            else:
                self.checkTableEntries(self.tableWidget_energy_plant_templates,check)
            
    def checkTableEntries(self,table,check=True):        
        for row in range(table.rowCount()):
            checkbox = table.cellWidget(row, 0)

            if checkbox is not None:
                checkbox.setChecked(check)
    
    def loadTableData(self,table,db_table):
        table.setRowCount(0)
        if db_table in ['customer_templates','energy_plant_templates']:
            sql="""SELECT template, template_name, conn_bundle_type, description  FROM {} ORDER BY template;""".format(db_table) # nosec B608
        else:
            sql="""SELECT * FROM {} ORDER BY id;""".format(db_table) # nosec B608
        self.cur.execute(sql)
        result = self.cur.fetchall()
        if result:
            self.table_columns[table]=['selection']+list(result[0].keys())
            table.setColumnCount(len(self.table_columns[table]))
            table.setHorizontalHeaderLabels([tr('@default',i) for i in self.table_columns[table]])
            for i,entry in enumerate(result):
                table.insertRow(i)
                checkbox = QCheckBox()
                table.setCellWidget(i, 0, checkbox)
                for j,col in enumerate(self.table_columns[table][1:],1):
                    item=QTableWidgetItem()
                    item.setText(tr('@default',str(entry[self.table_columns[table][j]])))
                    item.setData(Qt.ItemDataRole.UserRole ,str(entry[self.table_columns[table][j]]))
                    item.setFlags(ItemIsSelectable | ItemIsEnabled)
                    table.setItem(i,j,item)           
       
    #connections
    def onClickedRadioConnections(self):
        if self.rbtn_connections.isChecked():
            self.tableWidget_connections.show()
            self.tableWidget_connection_types.hide()
            self.tableWidget_connection_bundles.hide()
 
    def onClickedRadioConnectiontypes(self):
        if self.rbtn_conntypes.isChecked():
            self.tableWidget_connection_types.show()
            self.tableWidget_connections.hide()
            self.tableWidget_connection_bundles.hide()

    def onClickedRadioConnectionbundles(self):
        if self.rbtn_conn_bundles.isChecked():
            self.tableWidget_connection_bundles.show()
            self.tableWidget_connections.hide()
            self.tableWidget_connection_types.hide()

    #pipes
    def onClickedRadioMaterials(self):
        if self.rbtn_materials.isChecked():
            self.tableWidget_materials.show()
            self.tableWidget_constructions.hide()
            self.tableWidget_pipes.hide()
            self.tableWidget_pipe_bundles.hide()

    def onClickedRadioConstructions(self):
        if self.rbtn_constructions.isChecked():
            self.tableWidget_constructions.show()
            self.tableWidget_materials.hide()
            self.tableWidget_pipes.hide()
            self.tableWidget_pipe_bundles.hide()

    def onClickedRadioPipes(self):
        if self.rbtn_pipes.isChecked():
            self.tableWidget_pipes.show()
            self.tableWidget_materials.hide()
            self.tableWidget_constructions.hide()
            self.tableWidget_pipe_bundles.hide()

    def onClickedRadioPipebundles(self):
        if self.rbtn_pipe_bundles.isChecked():
            self.tableWidget_pipe_bundles.show()
            self.tableWidget_materials.hide()
            self.tableWidget_constructions.hide()
            self.tableWidget_pipes.hide()

    #templates
    def onClickedRadioCustomerTemplates(self):
        if self.rbtn_customers.isChecked():
            self.tableWidget_customer_templates.show()
            self.tableWidget_energy_plant_templates.hide()

    def onClickedRadioEnergyplantsTemplates(self):
        if self.rbtn_energy_plants.isChecked():
            self.tableWidget_energy_plant_templates.show()
            self.tableWidget_customer_templates.hide()
            
class ImportResourcesDialog(QDialog):
    def __init__(self,config,projectNames):
        super().__init__()

        # Load UI
        ui_path = os.path.join(os.path.dirname(__file__), "ImportResources_dialog.ui")
        uic.loadUi(ui_path, self)
        self.conn=''
        self.cur=''
        self.config=config
        self.projectNames=projectNames
        self.table_columns={}
        self.tables={
            self.tableWidget_connections : 'connections',
            self.tableWidget_materials : 'materials'}
            
                
        self.tabWidget.setCurrentWidget(self.tab_connections) 
        
        #rbtn connections
        self.radio_group_import = QButtonGroup(self)
        self.radio_group_import.setExclusive(True)

        self.radio_group_import.addButton(self.rbtn_file)
        self.radio_group_import.addButton(self.rbtn_db)
        
        self.rbtn_connections.toggled.connect(self.onClickedRadioConnections)
        self.rbtn_conntypes.toggled.connect(self.onClickedRadioConnectiontypes)
        self.rbtn_conn_bundles.toggled.connect(self.onClickedRadioConnectionbundles)

        self.rbtn_materials.toggled.connect(self.onClickedRadioMaterials)
        self.rbtn_constructions.toggled.connect(self.onClickedRadioConstructions)
        self.rbtn_pipes.toggled.connect(self.onClickedRadioPipes)
        self.rbtn_pipe_bundles.toggled.connect(self.onClickedRadioPipebundles)

        self.rbtn_customers.toggled.connect(self.onClickedRadioCustomerTemplates)
        self.rbtn_energy_plants.toggled.connect(self.onClickedRadioEnergyplantsTemplates)   

        #combobox
        self.comboBox_db.currentTextChanged.connect(self.dbConnect)

        #btn tables
        self.btn_select_all_connections.clicked.connect(lambda: self.select_all(True))
        self.btn_select_all_pipes.clicked.connect(lambda: self.select_all(True))
        self.btn_select_all_templates.clicked.connect(lambda: self.select_all(True))

        self.btn_unselect_all_connections.clicked.connect(lambda: self.select_all(False))
        self.btn_unselect_all_pipes.clicked.connect(lambda: self.select_all(False))
        self.btn_unselect_all_templates.clicked.connect(lambda: self.select_all(False))
        
        self.rbtn_connections.setChecked(True)
        self.rbtn_materials.setChecked(True)
        self.rbtn_customers.setChecked(True)
        
        self.rbtn_file.toggled.connect(self.onClickedRadioFileImport)
        self.rbtn_db.toggled.connect(self.onClickedRadioDBImport)
        self.rbtn_file.setChecked(True)

    def loadTablesData(self):
        #load data
        self.loadTableData(self.tableWidget_connections,self.tables[self.tableWidget_connections])
        self.loadTableData(self.tableWidget_connection_types,'connection_types')
        self.loadTableData(self.tableWidget_connection_bundles,'conn_bundle_types')

        self.loadTableData(self.tableWidget_materials,self.tables[self.tableWidget_materials])
        self.loadTableData(self.tableWidget_constructions,'pipe_constructions')
        self.loadTableData(self.tableWidget_pipes,'pipes')
        self.loadTableData(self.tableWidget_pipe_bundles,'pipe_bundle_types')

        self.loadTableData(self.tableWidget_customer_templates,'customer_templates')
        self.loadTableData(self.tableWidget_energy_plant_templates,'energy_plant_templates')
        
    def select_all(self,check):
        tab_name = self.tabWidget.currentWidget().objectName()
        if tab_name=='tab_connections':
            if self.rbtn_connections.isChecked():
                self.checkTableEntries(self.tableWidget_connections,check)
            elif self.rbtn_conntypes.isChecked():
                self.checkTableEntries(self.tableWidget_connection_types,check)
            else:
                self.checkTableEntries(self.tableWidget_connection_bundles,check)
        elif tab_name=='tab_pipes':
            if self.rbtn_materials.isChecked():
                self.checkTableEntries(self.tableWidget_materials,check)
            elif self.rbtn_constructions.isChecked():
                self.checkTableEntries(self.tableWidget_constructions,check)
            elif self.rbtn_pipes.isChecked():
                self.checkTableEntries(self.tableWidget_pipes,check)
            else:
                self.checkTableEntries(self.tableWidget_pipe_bundles,check)
        else:
            if self.rbtn_customers.isChecked():
                self.checkTableEntries(self.tableWidget_customer_templates,check)
            else:
                self.checkTableEntries(self.tableWidget_energy_plant_templates,check)
            
    def checkTableEntries(self,table,check=True):        
        for row in range(table.rowCount()):
            checkbox = table.cellWidget(row, 0)

            if checkbox is not None:
                checkbox.setChecked(check)
    
    def loadTableData(self,table,db_table):
        table.setRowCount(0)
        if db_table in ['customer_templates','energy_plant_templates']:
            sql="""SELECT template, template_name, conn_bundle_type, description  FROM {} ORDER BY template;""".format(db_table) # nosec B608
        else:
            sql="""SELECT * FROM {} ORDER BY id;""".format(db_table) # nosec B608
        self.cur.execute(sql)
        result = self.cur.fetchall()
        if result:
            self.table_columns[table]=['selection']+list(result[0].keys())
            table.setColumnCount(len(self.table_columns[table]))
            table.setHorizontalHeaderLabels([tr('@default',i) for i in self.table_columns[table]])
            for i,entry in enumerate(result):
                table.insertRow(i)
                checkbox = QCheckBox()
                table.setCellWidget(i, 0, checkbox)
                for j,col in enumerate(self.table_columns[table][1:],1):
                    item=QTableWidgetItem()
                    item.setText(tr('@default',str(entry[self.table_columns[table][j]])))
                    item.setData(Qt.ItemDataRole.UserRole ,str(entry[self.table_columns[table][j]]))
                    item.setFlags(ItemIsSelectable | ItemIsEnabled)
                    table.setItem(i,j,item)            
       
    #import
    def onClickedRadioFileImport(self):
        if self.rbtn_file.isChecked():
            self.groupBox_file.show()
            self.groupBox_db.hide()
            self.btn_import_selection.setEnabled(False)            

    def dbConnect(self,projectName):
        if projectName:
            self.conn=dbConnectPerName(self.config,projectName,True)
            if self.conn:
                self.cur=self.conn.cursor(cursor_factory = psycopg2.extras.RealDictCursor)  
                self.loadTablesData()
            
    def onClickedRadioDBImport(self):
        if self.rbtn_db.isChecked():
            self.groupBox_file.hide()

            self.comboBox_db.addItems(self.projectNames)
            if self.comboBox_db.currentText():
                self.dbConnect(self.comboBox_db.currentText())
            
            self.groupBox_db.show()    
            self.btn_import_selection.setEnabled(True)              
            
    #connections
    def onClickedRadioConnections(self):
        if self.rbtn_connections.isChecked():
            self.tableWidget_connections.show()
            self.tableWidget_connection_types.hide()
            self.tableWidget_connection_bundles.hide()
 
    def onClickedRadioConnectiontypes(self):
        if self.rbtn_conntypes.isChecked():
            self.tableWidget_connection_types.show()
            self.tableWidget_connections.hide()
            self.tableWidget_connection_bundles.hide()

    def onClickedRadioConnectionbundles(self):
        if self.rbtn_conn_bundles.isChecked():
            self.tableWidget_connection_bundles.show()
            self.tableWidget_connections.hide()
            self.tableWidget_connection_types.hide()

    #pipes
    def onClickedRadioMaterials(self):
        if self.rbtn_materials.isChecked():
            self.tableWidget_materials.show()
            self.tableWidget_constructions.hide()
            self.tableWidget_pipes.hide()
            self.tableWidget_pipe_bundles.hide()

    def onClickedRadioConstructions(self):
        if self.rbtn_constructions.isChecked():
            self.tableWidget_constructions.show()
            self.tableWidget_materials.hide()
            self.tableWidget_pipes.hide()
            self.tableWidget_pipe_bundles.hide()

    def onClickedRadioPipes(self):
        if self.rbtn_pipes.isChecked():
            self.tableWidget_pipes.show()
            self.tableWidget_materials.hide()
            self.tableWidget_constructions.hide()
            self.tableWidget_pipe_bundles.hide()

    def onClickedRadioPipebundles(self):
        if self.rbtn_pipe_bundles.isChecked():
            self.tableWidget_pipe_bundles.show()
            self.tableWidget_materials.hide()
            self.tableWidget_constructions.hide()
            self.tableWidget_pipes.hide()

    #templates
    def onClickedRadioCustomerTemplates(self):
        if self.rbtn_customers.isChecked():
            self.tableWidget_customer_templates.show()
            self.tableWidget_energy_plant_templates.hide()

    def onClickedRadioEnergyplantsTemplates(self):
        if self.rbtn_energy_plants.isChecked():
            self.tableWidget_energy_plant_templates.show()
            self.tableWidget_customer_templates.hide()

            
class ClimateDialog(QDialog):
    def __init__(self,data):
        super().__init__()

        # Load UI
        ui_path = os.path.join(os.path.dirname(__file__), "districts_climate_dialog.ui")
        uic.loadUi(ui_path, self)
        self.lineEdit_location.setText(data['name'])
        self.lineEdit_latitude.setText(str(data['latitude']))
        self.lineEdit_longitude.setText(str(data['longitude']))
        self.lineEdit_filePath.setText(data['filename'])
        self.spinBox_timeZone.setValue(data['timezone'])
        self.lineEdit_elevationHeight.setText(str(data['height']))  
                
    def fileDialog(self):
        dir=os.path.dirname(self.lineEdit_filePath.text())
        filename, _filter = QFileDialog.getOpenFileName(
            self, self.tr("select_climate_data"),dir, "PRN files (*.prn)")
        if filename:
            self.lineEdit_filePath.setText(standardizePath(filename,trailingBackSlash=False))
            
class ConnectionsDialog(QDialog):
    def __init__(self,title,headers):
        """Constructor"""
        super().__init__()
        self.setWindowTitle(title)   
        
        #table buttons     
        layout_buttons_table = QHBoxLayout()
        self.btn_add=QPushButton(tr('@default','add_btn'))
        layout_buttons_table.addWidget(self.btn_add)
        self.btn_delete=QPushButton(tr('@default','delete'))
        layout_buttons_table.addWidget(self.btn_delete)
        
        #Table
        layout_table = QHBoxLayout() 
        self.tableWidget = QTableWidget(0,len(headers))   
        self.tableWidget.setHorizontalHeaderLabels(headers)     
        self.tableWidget.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.tableWidget.setColumnCount(len(headers))
        layout_table.addWidget(self.tableWidget)
        self.traceChanges=[]

        #buttons     
        layout_buttons = QHBoxLayout()
        self.btn_ok=QPushButton(tr('@default','save'))
        layout_buttons.addWidget(self.btn_ok)
        self.btn_cancel=QPushButton(tr('@default','cancel'))
        layout_buttons.addWidget(self.btn_cancel)
        
        #---------------set layouts together-------------------
        layout_win = QVBoxLayout()
        layout_win.addLayout(layout_buttons_table)
        layout_win.addLayout(layout_table)
        layout_win.addLayout(layout_buttons)
        
        self.setLayout(layout_win)
        self.traceTableValues={}      
        self.resize(900, 500)  # Width of 900 pixels, height of 500 pixels        
    
    def changedDropdownItem(self, s):
        #print('changed drop down item')
        combo = self.sender()  # Get the combo box that sent the signal
        selected_option = combo.currentText().split(':')[0]
        #print(selected_option)

        index = self.tableWidget.indexAt(combo.pos())
        row = index.row()
        #print(row)
        self.traceTableValues[row]=[self.traceTableValues[row][0],self.traceTableValues[row][1],self.traceTableValues[row][2],self.traceTableValues[row][3],self.traceTableValues[row][4],self.traceTableValues[row][5],self.traceTableValues[row][6],self.traceTableValues[row][7],self.traceTableValues[row][8],selected_option]
        #print(self.traceTableValues[row])
    
    def changedCheckboxState(self,s):
        #print('+++changed state++')
        checkbox = self.sender()
        index = self.tableWidget.indexAt(checkbox.pos())
        row = index.row()
        col = index.column()
        #print(row)
        #print(col)
        #print(s)
        if s==2: #checked
            item=QTableWidgetItem('')
            self.tableWidget.setItem(row,5,item)
            item=QTableWidgetItem('')
            item.setFlags(item.flags() & ~qt_item_flag("ItemIsEnabled"))

            self.tableWidget.setItem(row,4,item)
            try:
                self.traceTableValues[row]=[self.traceTableValues[row][0],'',self.traceTableValues[row][2],self.traceTableValues[row][3],self.traceTableValues[row][4],self.traceTableValues[row][5],self.traceTableValues[row][6],True,self.traceTableValues[row][8],self.traceTableValues[row][9]]
            except:
                QgsMessageLog.logMessage(
                    traceback.format_exc(),
                    "Districts",
                    MessageCritical
                )
        else:
            item=QTableWidgetItem('')
            self.tableWidget.setItem(row,4,item)
            item=QTableWidgetItem('')
            item.setFlags(item.flags() & ~qt_item_flag("ItemIsEnabled"))

            self.tableWidget.setItem(row,5,item)
            try:
                self.traceTableValues[row]=[self.traceTableValues[row][0],self.traceTableValues[row][1],self.traceTableValues[row][2],'',self.traceTableValues[row][4],self.traceTableValues[row][5],self.traceTableValues[row][6],False,self.traceTableValues[row][8],self.traceTableValues[row][9]]
            except:
                QgsMessageLog.logMessage(
                    traceback.format_exc(),
                    "Districts",
                    MessageCritical
                )
        
        #print(self.traceTableValues)
        
    def changedItem(self, item):
        row = item.row()
        #print('changed')
        try:
            if self.tableWidget.item(row,4) and self.traceTableValues[row][0]!=self.tableWidget.item(row,4).text(): #p
                self.traceTableValues[row][1]=self.tableWidget.item(row,4).text()
            if self.tableWidget.item(row,5) and self.traceTableValues[row][2]!=self.tableWidget.item(row,5).text(): #m
                self.traceTableValues[row][3]=self.tableWidget.item(row,5).text()
            if self.tableWidget.item(row,3) and self.traceTableValues[row][4]!=self.tableWidget.item(row,3).text(): #T
                self.traceTableValues[row][5]=self.tableWidget.item(row,3).text()
        except:
            QgsMessageLog.logMessage(
                traceback.format_exc(),
                "Districts",
                MessageCritical
            )
        #print(self.traceTableValues)

class DefaultsDialog(QDialog):
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
        self.tabs.addTab(self.tab_general,tr('@default',"general"))
        self.tabs.addTab(self.tab_physical,tr('@default',"physical_data"))
        
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
        self.btn_ok=QPushButton(tr('@default','ok'))
        layout_buttons.addWidget(self.btn_ok)
        self.btn_cancel=QPushButton(tr('@default','cancel'))
        layout_buttons.addWidget(self.btn_cancel)
        
        #---------------set layouts together-------------------
        layout_win = QVBoxLayout()
        layout_win.addWidget(self.tabs)
        layout_win.addLayout(layout_buttons)
        layout_win.addStretch()
        
        self.setLayout(layout_win)
