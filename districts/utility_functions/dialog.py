from qgis.PyQt.QtCore import QObject,pyqtSignal,Qt
from qgis.PyQt import uic, QtWidgets, QtCore
from qgis.PyQt.QtWidgets import QTextBrowser,QDialog,QSpacerItem,QSizePolicy,QTableWidgetItem,QTableWidget,QTreeView,QPushButton,QHBoxLayout,QVBoxLayout,QLabel,QLineEdit,QCheckBox,QComboBox, QProgressBar
from qgis.utils import iface
from qgis.core import Qgis
from qgis.PyQt.QtGui import QIcon,QPixmap

from .db import *
from .utility import *

import copy

def checkIDADistrictsInstallation(config):
    if not os.path.exists(f"{config['pathDistricts']}bin\\ida-districts.exe"):
        #print('--IDA Districts does not exists--')
        dialog=IDADistrictsPleaseContactDialog()
        # Wait for user response
        result = dialog.exec()
        return False
    else:
        return True
        
def get_item_flag(name):
    try:
        # Qt6 style
        return getattr(QtCore.Qt.ItemFlag, name)
    except AttributeError:
        # Qt5 style
        return getattr(QtCore.Qt, name)

def qt_item_flag(flag_name):
    """
    Returns a Qt.ItemFlag that works in both Qt5 and Qt6.
    """
    from qgis.PyQt import QtCore

    Qt = QtCore.Qt

    # Qt6: Qt.ItemFlag.<Flag>
    if hasattr(Qt, "ItemFlag"):
        return getattr(Qt.ItemFlag, flag_name)

    # Qt5: Qt.<Flag>
    return getattr(Qt, flag_name)
    
def checkState():
    try:
        # Qt6
        checked = Qt.CheckState.Checked
    except AttributeError:
        # Qt5
        checked = Qt.Checked
    return checked
    
def uncheckState():
    try:
        # Qt6
        checked = Qt.CheckState.Unchecked
    except AttributeError:
        # Qt5
        checked = Qt.Unchecked
    return checked

class IDADistrictsPleaseContactDialog(QDialog):
    """
    Dialog informing the user that the requested functionality
    cannot be used because IDA Districts is not installed.
    The user is asked to contact EQUA or install IDA Districts.
    Compatible with PyQt6 and Qt5/QGIS environments.
    """

    def __init__(self,parent=None):
        super().__init__(parent)

        self.setWindowTitle(
            self.tr("ida_districts_not_available")
        )

        self.setMinimumWidth(500)
        self.setModal(True)

        icon_path=os.path.join(get_districts_plugin_dir(),'icons','IDA_Districts_Icon_QGIS.png')
        if os.path.exists(icon_path):
            self.setWindowIcon(QIcon(icon_path))

        self._build_ui()

    def _build_ui(self):
        layout = QVBoxLayout(self)

        title_label = QLabel(
            self.tr("ida_districts_is_not_installed")
        )

        title_label.setStyleSheet(
            "font-size: 16px; font-weight: bold; margin-bottom: 10px;"
        )

        # Qt5 + Qt6 compatible
        try:
            title_label.setAlignment(Qt.AlignmentFlag.AlignLeft)
        except AttributeError:
            title_label.setAlignment(Qt.AlignLeft)

        message_label = QLabel(
            self.tr("this_functionality_cannot_currently_be_used_because_ida_districts_is_not_installed")
            + "<br><br>"
            + self.tr("please_contact_equa_or_install_ida_districts_to_use_this_functionality")
            + "<br><br>"
            + self.tr("more_information")
            + ":<br>"
            + '<a href="https://equa.se/software/ida-districts">'
              "https://equa.se/software/ida-districts"
              "</a>"
        )

        message_label.setOpenExternalLinks(True)
        message_label.setWordWrap(True)

        button_layout = QHBoxLayout()
        button_layout.addStretch()

        close_button = QPushButton(
            self.tr("close")
        )

        close_button.clicked.connect(self.accept)

        button_layout.addWidget(close_button)

        layout.addWidget(title_label)
        layout.addWidget(message_label)
        layout.addLayout(button_layout)
        
class SvgLabel(QLabel):
    """
    QLabel subclass to display an SVG at high quality, scaled proportionally
    and optionally limited by a maximum height.
    Designed for QGIS Plugins with Qt Designer promote.
    """
    def __init__(self, svg_path=None, max_height=None, parent=None):
        super().__init__(parent)
        self._max_height = max_height
        self._svg_renderer = None
        self.setAlignment(Qt.AlignmentFlag.AlignCenter)
        if svg_path:
            self.load_svg(svg_path)

    def load_svg(self, svg_path):
        """Load an SVG file."""
        self._svg_renderer = QSvgRenderer(svg_path)
        self.update_pixmap()

    def set_max_height(self, max_height):
        """Optionally set a maximum height for the SVG."""
        self._max_height = max_height
        self.update_pixmap()

    def resizeEvent(self, event):
        """Render SVG into QPixmap whenever the label resizes."""
        self.update_pixmap()
        super().resizeEvent(event)

    def update_pixmap(self):
        if self._svg_renderer and self._svg_renderer.isValid():
            # Determine target size
            width = self.width()
            height = self.height()
            if self._max_height and height > self._max_height:
                height = self._max_height
            # Preserve aspect ratio of the SVG
            size_ratio = self._svg_renderer.defaultSize().width() / self._svg_renderer.defaultSize().height()
            width = int(height * size_ratio)
            # Render SVG to QPixmap
            pixmap = QPixmap(width, height)
            pixmap.fill(Qt.GlobalColor.transparent)
            painter = QPainter(pixmap)
            self._svg_renderer.render(painter)
            painter.end()
            super().setPixmap(pixmap)
            
class ScaledLabel(QLabel):
    def __init__(self, parent=None, max_height=None):
        super().__init__(parent)
        self._original_pixmap = None  # Originalbild behalten
        self._max_height = max_height
        self.setAlignment(Qt.AlignmentFlag.AlignCenter)

    def setPixmap(self, pixmap):
        self._original_pixmap = pixmap  # niemals überschreiben!
        self.updatePixmap()

    def resizeEvent(self, event):
        self.updatePixmap()
        super().resizeEvent(event)

    def updatePixmap(self):
        if self._original_pixmap and not self._original_pixmap.isNull():
            # Berechne Zielgröße
            target_height = self._max_height if self._max_height else self.height()
            scaled = self._original_pixmap.scaled(
                target_height, 
                target_height * self._original_pixmap.width() / self._original_pixmap.height(),
                Qt.AspectRatioMode.KeepAspectRatio,
                Qt.TransformationMode.SmoothTransformation
            )
            super().setPixmap(scaled)
            
def load_image(path,label,scale=False,size=False):
    pixmap = QPixmap(path)

    if pixmap.isNull():
        #print("Image failed to load")
        return
    #print(pixmap.size())
    
        
    if scale:
        pixmap = pixmap.scaled(
            label.size(),
            Qt.AspectRatioMode.KeepAspectRatio,
            Qt.TransformationMode.SmoothTransformation
        )

    label.setPixmap(pixmap)
        
def addParmTableRow(dlg,cur,config):
    
    maxId=getMaxId(cur,'model_parms')+1
    dlg.tableWidget_parameters.insertRow(0)
        
    item = QTableWidgetItem(str(maxId))
    item.setFlags(item.flags() & ~Qt.ItemFlag.ItemIsEditable)

    dlg.tableWidget_parameters.setItem(0 , 0, item)
    dlg.tableWidget_parameters.setItem(0 , 1, QTableWidgetItem(''))
    comboBox = QComboBox()
    #comboBox.addItems(['<-->','<--','-->'])
    comboBox.addItems(['-->'])
    comboBox.setCurrentText('-->')
    dlg.tableWidget_parameters.setCellWidget(0, 2, comboBox)  
    dlg.tableWidget_parameters.setItem(0 , 3, QTableWidgetItem(''))
    dlg.tableWidget_parameters.setItem(0 , 4, QTableWidgetItem(''))        
    dlg.tableWidget_parameters.setItem(0 , 5, QTableWidgetItem(''))        
    dlg.tableWidget_parameters.setItem(0 , 6, QTableWidgetItem(''))        
  
def copyTableRow(cur,dlg,row_idx,dropdowns,openFn,openFnArg):
    #print('copyTableRow')
    #print(row_idx)
    if row_idx!=-1: 
        maxId=getMaxTableId(dlg.tableWidget)
        addTableRowTrace(dlg,dropdowns,True,[],cur)
        #print('row added')
        for col in range(dlg.tableWidget.columnCount())[1:]:
            if dlg.tableWidget.item(row_idx+1,col):
                #print(dlg.tableWidget.item(row_idx+1,col).text())
                dlg.tableWidget.setItem(0,col,QTableWidgetItem(dlg.tableWidget.item(row_idx+1,col).text()))
            else:
                dlg.tableWidget.cellWidget(0, col).setCurrentText(dlg.tableWidget.cellWidget(row_idx+1,col).currentText())
        if openFn:
            #print(openFnArg)
            id=dlg.tableWidget.item(row_idx+1,0).text()
            table=openFnArg[0]
            columns=openFnArg[1]
            filter=openFnArg[3]+id
            orderby=openFnArg[4]
            sql="""INSERT INTO public.{} (id,{},{})
    WITH sub AS(
        SELECT max(id) AS max_id FROM public.{}
    )
    SELECT ROW_NUMBER() OVER (ORDER BY {}) + max_id AS row_number,{},{} FROM public.{},sub {} {} ;""".format(table,filter.split('WHERE ')[1].split('=')[0].strip(),','.join(i for i in columns),table,columns[0],str(maxId+1),','.join(i for i in columns),table,filter,orderby) # nosec B608
            #print(sql)
            cur.execute(sql)
    else:
        iface.messageBar().pushMessage("Info", tr('@default','no_item_selected'), level=Qgis.Info) 
    
def addTableRowTrace(dlg,dropdowns,trace,deactivated,cur):
    """Insert table row"""
    rowPosition = 0
    traceTableValues=copy.deepcopy(dlg.traceTableValues)
    #print('-------insert row---------------')
    dlg.tableWidget.insertRow(rowPosition)
    dropdownItems=getDropDownItems(cur,dropdowns)
    for col in range(dlg.tableWidget.columnCount()):
        if col in list([i[0] for i in dropdowns]):
            comboBox = QComboBox()
            for original_key, translated_text in dropdownItems[col].items():
                comboBox.addItem(translated_text, original_key) # The second argument is the userData 
            dlg.tableWidget.setCellWidget(rowPosition, col, comboBox)
            if trace:
                comboBox.currentTextChanged.connect(dlg.changedDropdownItem)
        else:
            if col==0:
                item=QTableWidgetItem(str(getMaxTableId(dlg.tableWidget)+1))
            else:
                item=QTableWidgetItem('')
            if col in deactivated:
                item.setFlags(Qt.ItemFlag.ItemIsSelectable | Qt.ItemFlag.ItemIsEnabled)

            dlg.tableWidget.setItem(0,col,item)
            
    #add row to dlg.traceTableValues in order to trace the changed values     
    if trace:
        #print('----------trace-------'+str(trace))
        for row in reversed(sorted(traceTableValues)):
            #print(row)
            #print(traceTableValues[row])
            dlg.traceTableValues[row+1]=traceTableValues[row]
        try:
            #print('--add trace values of row 0--')
            if trace=='building_template':
                dlg.traceTableValues[0]={i: ['',str(getMaxTableId(dlg.tableWidget)) if i==0 else ''] for i in range(dlg.tableWidget.columnCount())}            
            elif trace in ['conn_type_trace','bt_conns_trace']:
                #print('conn_type_trace or bt_conns_trace')
                #print(dlg.tableWidget.item(0,0).text())
                #print(dlg.tableWidget.cellWidget(0,1).currentText())
                dlg.traceTableValues[0]= ['',dlg.tableWidget.item(0,0).text(),'',dlg.tableWidget.cellWidget(0,1).currentText().split(':')[0]]
            elif trace:                   
                #print(dlg.tableWidget.item(0,1))
                #print(dlg.tableWidget.item(0,1).text())
                #print(dlg.tableWidget.item(0,0).text()+'_'+dlg.tableWidget.item(0,1).text())
                dlg.traceTableValues[0]=['',dlg.tableWidget.item(0,0).text()+'_'+dlg.tableWidget.item(0,1).text(),'',dlg.tableWidget.cellWidget(0,2).currentText().split(':')[0]]
            #print(dlg.traceTableValues)
            #print('--finished trace values of row 0--')
        except:
            pass
        #print(dlg.traceTableValues)

def deleteTableRowTrace (dlg,trace):
    """ Delete selected template and refresh table"""
    #print('delete row')
    row_index=dlg.tableWidget.currentRow()
    #print(row_index)
    if row_index!=-1:
        dlg.tableWidget.removeRow(row_index)
    else:
        iface.messageBar().pushMessage("Info", tr('@default','no_item_selected'), level=Qgis.Info)
            
    #delete row to dlg.traceTableValues in order to trace the changed values         
    if trace:
        for row in sorted(dlg.traceTableValues):
            if row>row_index:
                dlg.traceTableValues[row-1]=dlg.traceTableValues[row]
        dlg.traceTableValues.pop(len(dlg.traceTableValues)-1,None)
        #print(dlg.traceTableValues)
            
def deleteTableRow (dlg):
    """ Delete selected template and refresh table"""
    #print('delete row')
    row_index=dlg.tableWidget.currentRow()
    #print(row_index)
    if row_index!=-1:
        dlg.tableWidget.removeRow(row_index)
    else:
        self.iface.messageBar().pushMessage("Info", tr('@default','no_item_selected'), level=Qgis.Info)
            
class TableDialog(QDialog):
    def __init__(self,title,headers,openBtn,importBtn,saveAsBtn,trace,addBtn=True,deleteBtn=True,type=''):
        """Constructor"""
        super().__init__()
        self.setWindowTitle(title)   
        
        self.trace_type=trace
        #print('++++++trace: '+str(trace))
        self.type=type
        #table buttons     
        layout_buttons_table = QHBoxLayout()
        if addBtn:
            self.btn_add=QPushButton("")
            self.btn_add.setIcon(QIcon(":/images/themes/default/symbologyAdd.svg"))
            layout_buttons_table.addWidget(self.btn_add)
        if deleteBtn:
            self.btn_delete=QPushButton("")
            self.btn_delete.setIcon(QIcon(":/images/themes/default/symbologyRemove.svg"))
            layout_buttons_table.addWidget(self.btn_delete)
        if openBtn:
            self.btn_open=QPushButton("")
            self.btn_open.setIcon(QIcon(":/images/themes/default/mActionFileOpen.svg"))
            layout_buttons_table.addWidget(self.btn_open)
        if importBtn:
            self.btn_import=QPushButton("")
            self.btn_import.setIcon(QIcon(":/images/themes/default/mActionSharingImport.svg"))
            layout_buttons_table.addWidget(self.btn_import)
        if saveAsBtn:
            self.btn_saveAs=QPushButton("")
            self.btn_saveAs.setIcon(QIcon(":/images/themes/default/mActionEditCopy.svg"))
            layout_buttons_table.addWidget(self.btn_saveAs)
            
        layout_buttons_table.addItem(QSpacerItem(0,0,QSizePolicy.Policy.Expanding,QSizePolicy.Policy.Minimum))
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
        self.btn_ok=QPushButton(tr('@default','ok'))
        layout_buttons.addWidget(self.btn_ok)
        self.btn_cancel=QPushButton(tr('@default','cancel'))
        layout_buttons.addWidget(self.btn_cancel)
        
        #---------------set layouts together-------------------
        layout_win = QVBoxLayout()
        layout_win.addLayout(layout_buttons_table)
        layout_win.addLayout(layout_table)
        layout_win.addLayout(layout_buttons)
        
        self.setLayout(layout_win)
        #self.fitToTable()
        self.traceTableValues=[] 
    
    def changedDropdownItem(self, s):
        #print('+++++')
        combo = self.sender()  # Get the combo box that sent the signal
        index = self.tableWidget.indexAt(combo.pos())
        row = index.row()
        col = index.column()
        #print(row)
        #print(col)
        if self.trace_type in ['conn_type_trace','bt_conns_trace']:
            self.traceTableValues[row]=[self.traceTableValues[row][0],self.tableWidget.item(row,0).text(),self.traceTableValues[row][2],self.tableWidget.cellWidget(row,1).currentText().split(':')[0]]
        elif self.trace_type:
            if col==2:
                #print(col)
                self.traceTableValues[row]=[self.traceTableValues[row][0],self.traceTableValues[row][1],self.traceTableValues[row][2],s.split(':')[0]]
        #print(self.traceTableValues)
        
    def changeItem(self, item):
        row = item.row()
        #print('changed')
        #print(row)
        #print(item)
        #print(self.traceTableValues)
        if self.trace_type in ['conn_type_trace','bt_conns_trace']:
            try:
                self.traceTableValues[row]=[self.traceTableValues[row][0],self.tableWidget.item(row,0).text(),self.traceTableValues[row][2],self.tableWidget.cellWidget(row,1).currentText().split(':')[0]]
            except:
                pass
        elif self.trace_type == 'building_template':
            #print(item.text())
            self.traceTableValues[row][item.column()][1]=item.text()
        elif self.trace_type:
            changedValue=''
            if self.tableWidget.item(row,0):
                changedValue+=self.tableWidget.item(row,0).text()+'_'
            if self.tableWidget.item(row,1):
                changedValue+=self.tableWidget.item(row,1).text()
            try:
                #print(changedValue)
                self.tableWidget.cellWidget(row,2).currentText()
                self.traceTableValues[row]=[self.traceTableValues[row][0],changedValue,self.traceTableValues[row][2],self.tableWidget.cellWidget(row,2).currentText().split(':')[0]]
            except:
                pass
            item.setData(
                Qt.ItemDataRole.UserRole,
                item.text()
            )
        #print(self.traceTableValues)
        
    
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
            item.setCheckState(checkState())
        else:
            item.setCheckState(uncheckState())
            
    def setAllItemsChecked(self,checked=False):
        [self.setItemChecked(i,checked=checked) for i in range(self.count()) if not self.itemText(i)==tr('@default','check_all_items')]
        
    def getItemsDict(self,exclude=[tr('@default','check_all_items')]):
        items = {i : self.itemText(i) for i in range(self.count()) if self.itemText(i) not in exclude}
        return items

    def getItems(self,exclude=[tr('@default','check_all_items')]):
        items = [self.itemText(i) for i in range(self.count()) if self.itemText(i) not in exclude]
        return items

    def getCheckItems(self,exclude=[tr('@default','check_all_items')]):
        items = [self.itemText(i) for i in range(self.count()) if self.itemText(i) not in exclude and self.itemChecked(i)]
        return items
            
    def handleItemPressed(self, index):
        self._changed=True
        item=self.model().itemFromIndex(index)
        if item.row()==0:
            for i in range(1,self.model().rowCount()):
                self.model().item(i,0).setCheckState(Qt.CheckState.Checked)
        else:
            if item.checkState()==checkState():
                item.setCheckState(uncheckState())
            else:
                item.setCheckState(checkState())
                
    def hidePopup(self):
        if not self._changed:
            super().hidePopup()
        self._changed=False
        
    def itemChecked(self,index):
        item=self.model().item(index,self.modelColumn())
        return item.checkState()==checkState()
        
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
        
class LabelTextOkCancelDialog(QDialog):
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
        
        self.setLayout(layout_win)

def addTableRow(table):
    """A new table row is added at top of the table"""
    table.insertRow(0)
    
def deleteSelectedTableRow (table):
    """Selected table row is deleted"""
    #print('delete row')
    row_index=table.currentRow()
    #print(row_index)
    if row_index!=-1:
        table.removeRow(row_index)
    else:
        iface.messageBar().pushMessage("Info", tr('@default','no_item_selected'), level=Qgis.Info)
