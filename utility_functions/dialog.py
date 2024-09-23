from qgis.PyQt.QtCore import QObject,pyqtSignal,Qt
from qgis.PyQt.QtWidgets import QTreeView,QAction,QMainWindow,QWidget,QPushButton,QHBoxLayout,QVBoxLayout,QLabel,QLineEdit,QCheckBox,QComboBox, QProgressBar
from qgis.utils import iface
from qgis.core import Qgis


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
