from qgis.PyQt.QtCore import QObject,pyqtSignal,Qt
from qgis.PyQt import uic, QtWidgets, QtCore
from qgis.PyQt.QtWidgets import QTableWidget,QTreeView,QAction,QMainWindow,QWidget,QPushButton,QHBoxLayout,QVBoxLayout,QLabel,QLineEdit,QCheckBox,QComboBox, QProgressBar
from qgis.utils import iface
from qgis.core import Qgis

def deleteTableRow (dlg):
    """ Delete selected assettype and refresh table"""
    print('delete row')
    row_index=dlg.tableWidget.currentRow()
    print (row_index)
    if row_index!=-1:
        dlg.tableWidget.removeRow(row_index)
    else:
        self.iface.messageBar().pushMessage("Info", "No item selected!", level=Qgis.Info)
            
class TableDialog(QMainWindow):
    def __init__(self,title,headers,openBtn,importBtn,saveAsBtn,trace):
        """Constructor"""
        super().__init__()
        self.setWindowTitle(title)   
        
        self.trace_type=trace
        self.assetgroup=title.split(':')[-1].strip()
        #table buttons     
        layout_buttons_table = QHBoxLayout()
        self.btn_add=QPushButton("Add")
        layout_buttons_table.addWidget(self.btn_add)
        self.btn_delete=QPushButton("Delete")
        layout_buttons_table.addWidget(self.btn_delete)
        if openBtn:
            self.btn_open=QPushButton("Open and Save")
            layout_buttons_table.addWidget(self.btn_open)
        if importBtn:
            self.btn_import=QPushButton("Import")
            layout_buttons_table.addWidget(self.btn_import)
        if saveAsBtn:
            self.btn_saveAs=QPushButton("Copy")
            layout_buttons_table.addWidget(self.btn_saveAs)
        
        #Table
        layout_table = QHBoxLayout() 
        self.tableWidget = QTableWidget(0,len(headers))   
        self.tableWidget.setHorizontalHeaderLabels(headers)     
        #self.tableWidget.setHorizontalScrollBarPolicy(QtCore.Qt.ScrollBarAlwaysOff)
        #self.tableWidget.horizontalHeader().sectionResized.connect(self.fitToTable)
        #self.tableWidget.verticalHeader().sectionResized.connect(self.fitToTable)
        self.tableWidget.setColumnCount(len(headers))
        layout_table.addWidget(self.tableWidget)
        self.traceChanges=[]

        #buttons     
        layout_buttons = QHBoxLayout()
        self.btn_ok=QPushButton("Ok")
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
        #self.fitToTable()
        self.traceTableValues=[] 
    
    def changedDropdownItem(self, s, row,col):
        print('+++++')
        print(col)
        if self.trace_type in ['conn_type_trace','bt_conns_trace']:
            self.traceTableValues[row]=[self.traceTableValues[row][0],self.tableWidget.item(row,0).text(),self.traceTableValues[row][2],self.tableWidget.cellWidget(row,1).currentText().split(':')[0]]
        elif self.trace_type:
            if col==2:
                print(col)
                self.traceTableValues[row]=[self.traceTableValues[row][0],self.traceTableValues[row][1],self.traceTableValues[row][2],s.split(':')[0]]
        print(self.traceTableValues)
        
    def changeItem(self, item):
        row = item.row()
        print('changed')
        print(row)
        print(self.traceTableValues)
        if self.trace_type in ['conn_type_trace','bt_conns_trace']:
            try:
                self.traceTableValues[row]=[self.traceTableValues[row][0],self.tableWidget.item(row,0).text(),self.traceTableValues[row][2],self.tableWidget.cellWidget(row,1).currentText().split(':')[0]]
            except:
                pass
        elif self.trace_type:
            changedValue=self.assetgroup+'_'
            if self.tableWidget.item(row,0):
                changedValue+=self.tableWidget.item(row,0).text()+'_'
            if self.tableWidget.item(row,1):
                changedValue+=self.tableWidget.item(row,1).text()
            try:
                print(changedValue)
                self.tableWidget.cellWidget(row,2).currentText()
                self.traceTableValues[row]=[self.traceTableValues[row][0],changedValue,self.traceTableValues[row][2],self.tableWidget.cellWidget(row,2).currentText().split(':')[0]]
            except:
                pass
        print(self.traceTableValues)
        
    
    """@QtCore.pyqtSlot()
    def fitToTable(self):
        x = self.tableWidget.verticalHeader().size().width()
        for i in range(self.tableWidget.columnCount()):
            x += self.tableWidget.columnWidth(i)

        y = self.tableWidget.horizontalHeader().size().height()
        for i in range(self.tableWidget.rowCount()):
            y += self.tableWidget.rowHeight(i)

        self.setFixedSize(min(x+100,1500),min(1200,y+500))"""
        
class CheckableComboBox(QComboBox):  
    def __init__(self):
        super().__init__()
        self._changed =False
        self.view().pressed.connect(self.handleItemPressed)
        
    def setItemChecked(self, index, checked=False):
        item=self.model().item(index,self.modelColumn())
        
        if checked:
            item.setCheckState(Qt.Checked)
        else:
            item.setCheckState(Qt.Unchecked)
            
    def handleItemPressed(self, index):
        item=self.model().itemFromIndex(index)
        if item.row()==0:
            for i in range(1,self.model().rowCount()):
                self.model().item(i,0).setCheckState(Qt.Checked)
        else:
            if item.checkState()==Qt.Checked:
                item.setCheckState(Qt.Unchecked)
            else:
                item.setCheckState(Qt.Checked)
                
        self._changed=True
        
    def hidePopup(self):
        if not self._changed:
            super().hidePopup()
        self._changed=False
        
    def itemChecked(self,index):
        item=self.model().item(index,self.modelColumn())
        return item.checkState()==Qt.Checked
        
def closeDialog(dlg):
    """ close dialog window"""
    dlg.close()
    
def getMaxTableId(table):
    """ Count the rows without empty key rows"""
    maxId=0
    for row_index in range(table.rowCount()): 
        if table.item(row_index,0):
            if int(table.item(row_index,0).text()) > maxId:
                maxId=int(table.item(row_index,0).text())
    #print(maxId)
    return maxId
        
class LabelTextOkCancelDialog(QMainWindow):
    def __init__(self,title,inputs):
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
        
        #set name settings together
        layout_settings = QHBoxLayout() 
        layout_settings.addLayout(layout_label)
        layout_settings.addLayout(layout_input)
        
        #buttons     
        layout_buttons = QHBoxLayout()
        self.btn_ok=QPushButton("Ok")
        layout_buttons.addWidget(self.btn_ok)
        self.btn_cancel=QPushButton("Cancel")
        layout_buttons.addWidget(self.btn_cancel)
        
        #---------------set layouts together-------------------
        layout_win = QVBoxLayout()
        layout_win.addLayout(layout_settings)
        layout_win.addLayout(layout_buttons)
        
        widget=QWidget()
        widget.setLayout(layout_win)
        self.setCentralWidget(widget)

def addTableRow(table):
    """A new table row is added at top of the table"""
    table.insertRow(0)
    
def deleteSelectedTableRow (table):
    """Selected table row is deleted"""
    print('delete row')
    row_index=table.currentRow()
    print (row_index)
    if row_index!=-1:
        table.removeRow(row_index)
    else:
        iface.messageBar().pushMessage("Info", "No item selected!", level=Qgis.Info)
