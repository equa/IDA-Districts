from qgis.PyQt.QtCore import Qt
from qgis.PyQt.QtWidgets import QFileDialog,QDialog,QTableWidgetItem,QCheckBox,QComboBox,QHeaderView,QWidget,QPushButton,QHBoxLayout,QVBoxLayout,QLabel,QLineEdit, QTableWidget,QComboBox,QTableView,QTabWidget
from qgis.PyQt.QtGui import QIcon

from .utility_functions.dialog import *
from .utility_functions.utility import *

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
                pass
        else:
            item=QTableWidgetItem('')
            self.tableWidget.setItem(row,4,item)
            item=QTableWidgetItem('')
            item.setFlags(item.flags() & ~qt_item_flag("ItemIsEnabled"))

            self.tableWidget.setItem(row,5,item)
            try:
                self.traceTableValues[row]=[self.traceTableValues[row][0],self.traceTableValues[row][1],self.traceTableValues[row][2],'',self.traceTableValues[row][4],self.traceTableValues[row][5],self.traceTableValues[row][6],False,self.traceTableValues[row][8],self.traceTableValues[row][9]]
            except:
                pass
        
        #print(self.traceTableValues)
        
    def changedItem(self, item):
        row = item.row()
        #print('changed')
        try:
            if self.traceTableValues[row][0]!=self.tableWidget.item(row,4).text(): #p
                self.traceTableValues[row][1]=self.tableWidget.item(row,4).text()
            if self.traceTableValues[row][2]!=self.tableWidget.item(row,5).text(): #m
                self.traceTableValues[row][3]=self.tableWidget.item(row,5).text()
            if self.traceTableValues[row][4]!=self.tableWidget.item(row,3).text(): #T
                self.traceTableValues[row][5]=self.tableWidget.item(row,3).text()
        except:
            pass
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
