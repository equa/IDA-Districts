from qgis.PyQt.QtWidgets import  QTextEdit,QDialog, QTableWidgetItem,QButtonGroup,QComboBox,QPushButton,QHBoxLayout,QVBoxLayout,QLabel,QLineEdit, QProgressBar, QCheckBox, QRadioButton, QListWidget
from qgis.PyQt import QtGui, QtCore
from qgis.core import QgsProject, QgsMessageLog, QgsVectorLayer, QgsWkbTypes

from .utility_functions.db import *
from .utility_functions.dialog import *
from .utility_functions.layer_visualization import *

class ComboBox(QComboBox):
    popupAboutToBeShown = QtCore.pyqtSignal()

    def showPopup(self):
        self.popupAboutToBeShown.emit()
        super(ComboBox, self).showPopup()

class PipeBundleEditor(QDialog):
    def __init__(self,config,plugin_dir,layer,layer_attributes):     
        """Initialize GUI to Import Network Topology From Point Layer"""
        super().__init__()
        self.plugin_dir=plugin_dir
        self.config=config
        self.conn=dbConnect(self.config,True)
        self.cur=self.conn.cursor(cursor_factory = psycopg2.extras.RealDictCursor)
        self.mappedAttributes={}
        self.activeTable={'general':False,'construction':False }
        
        #print(layer)
        #print(layer_attributes)
        
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

        
        label_list_helptext=QLabel('Info: Double click on the \nfield in order to map it to \nthe selected field item.\nYou can use also dictionaries in the form: {key: entry}[value/attribute]')
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
        
        self.setLayout(layout_win)
    
    def constrTableTextChanged(self,s):
        if self.activeTable['general']==True:
            table=self.tableWidget
        else:
            table=self.tableWidget_pipe
        table_index=table.currentRow()
        try:
            #print(table_index)
            seq_constr=table.item(table_index,0).text()
            #print(seq_constr)
            material=table.cellWidget(table_index, 1).currentText()
            #print(material)
            thickness=table.item(table_index,2).text()
            #print(thickness)
            self.mappedAttributes['layer_constr'][seq_constr]=[material, thickness]
            #print(self.mappedAttributes)
        except:
            pass
        
    def setActiveTable(self,s):
        #print(s)
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
            item.setFlags(get_item_flag("ItemIsSelectable") | get_item_flag("ItemIsEnabled"))
            self.tableWidget.setItem(i,1,item)
            item=QTableWidgetItem(self.pipe_bundle_type_attributes[i])
            item.setFlags(get_item_flag("ItemIsSelectable") | get_item_flag("ItemIsEnabled"))
            self.tableWidget.setItem(i,2,item)
            item=QTableWidgetItem('')
            self.tableWidget.setItem(i,0,item)

    def updateSequences(self,sequences):
        """Updates the number of rows in Tabale self.tableWidget_pipe"""
        #print(sequences)
        if sequences.isdigit():
            self.tableWidget_pipe.setRowCount(0)
            for i in range(0,int(sequences)):
                self.tableWidget_pipe.insertRow(i)
                item=QTableWidgetItem(str(i+1))
                item.setFlags(get_item_flag("ItemIsSelectable") | get_item_flag("ItemIsEnabled"))
                self.tableWidget_pipe.setItem(i,0,item)
                comboBox = QComboBox()
                comboBox.addItems(getDropDownItems(self.cur,[[1,'public','materials','id','name']])[1].values())
                comboBox.currentTextChanged.connect(self.constrTableTextChanged)
                self.tableWidget_pipe.setCellWidget(i,1,comboBox)
                self.tableWidget_pipe.setItem(i,2,QTableWidgetItem(''))
        else:
            self.iface.messageBar().pushMessage("Error", "Please enter an integer number!", level=Qgis.Critical)


    def mapAttributesDoubleClick(self,s):
        #print(s.text())
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

class ImportNetworkTopologyFromLayer(QDialog):
    def __init__(self,config,plugin_dir):     
        """Initialize GUI to Import Network Topology From Layer"""
        super().__init__()
        self.plugin_dir=plugin_dir
        self.config=config
        self.conn=dbConnect(self.config,True)
        self.cur=self.conn.cursor()
        self.mappedAttributes={}
        
        self.setWindowTitle(tr('@default','import_network_topology_from_layer'))
        myBoldFont=QtGui.QFont('Arial', 12)
        myBoldFont.setBold(True)
        
        self.description_importLineFeature=QTextEdit(tr('@default','description_importLineFeature'))

        #Select Layer
        layout_layer=QHBoxLayout()
        label_layer =QLabel(tr('@default','network_layer'))
        layout_layer.addWidget(label_layer) 
        
        self.selectLayer =ComboBox()
        self.selectLayer.setCurrentIndex(-1)
        self.selectLayer.popupAboutToBeShown.connect(lambda: loadLayers(self,'line'))
        layout_layer.addWidget(self.selectLayer)
        
        #Radio Buttons 
        layout_radio=QHBoxLayout()
        self.rbtn_extend = QRadioButton(tr('@default','extend_topology'))
        self.rbtn_extend.setChecked(True)
        layout_radio.addWidget(self.rbtn_extend)
        self.rbtn_truncate = QRadioButton(tr('@default','truncate_existing_topology'))
        layout_radio.addWidget(self.rbtn_truncate)
        
        ##list widgets for attributes
        layout_listWidget_attributes = QHBoxLayout()
        #list widget for layer attributes
        layout_listWidget_layerAttributes = QVBoxLayout()
        label_listWidget_layerAttributes=QLabel(tr('@default','layer_fields'))
        layout_listWidget_layerAttributes.addWidget(label_listWidget_layerAttributes)
        self.listWidget_layerAttributes = QListWidget()
        layout_listWidget_layerAttributes.addWidget(self.listWidget_layerAttributes)
        layout_listWidget_attributes.addLayout(layout_listWidget_layerAttributes)
       
        #list widget for lines attributes
        layout_listWidget_FeatureAttributes = QVBoxLayout()
        label_listWidget_attributes=QLabel(tr('@default','line_fields'))
        layout_listWidget_FeatureAttributes.addWidget(label_listWidget_attributes)
        self.listWidget_attributes = QListWidget()
        layout_listWidget_FeatureAttributes.addWidget(self.listWidget_attributes)
        layout_listWidget_attributes.addLayout(layout_listWidget_FeatureAttributes)
        
        #table for mapped attributes  
        self.tableWidget = QTableWidget(0,3)   
        self.tableWidget.setHorizontalHeaderLabels([tr('@default','expression'),'',tr('@default','fields')])     
        self.tableWidget.itemChanged.connect(lambda: addExpressionToMappedAttributes(self,False))

        #buttons
        #connection buttons
        layout_buttons_connect = QHBoxLayout()
        
        btn_connect=QPushButton(tr('@default','map_layer_fields'))
        btn_connect.pressed.connect(lambda: mapAttributes(self))
        layout_buttons_connect.addWidget(btn_connect)
               
        btn_disconnect=QPushButton(tr('@default','disconnect'))
        btn_disconnect.pressed.connect(lambda: disconnectAttributes(self))
        layout_buttons_connect.addWidget(btn_disconnect)
        
        self.btn_generate_pipe_bundles=QPushButton(tr('@default','pipe_bundle_type_editor'))
        layout_buttons_connect.addWidget(self.btn_generate_pipe_bundles)
        
        #connection buttons
        layout_buttons_import = QHBoxLayout()
        self.btn_import=QPushButton(tr('@default','import'))
        layout_buttons_import.addWidget(self.btn_import)
               
        self.btn_cancel=QPushButton(tr('@default','cancel'))
        layout_buttons_import.addWidget(self.btn_cancel)
        
        #set buttons layout together
        layout_buttons=QVBoxLayout()
        layout_buttons.addLayout(layout_buttons_connect)
        layout_buttons.addLayout(layout_buttons_import)
        
        #set layouts together
        layout_win = QVBoxLayout()
        layout_win.addWidget(self.description_importLineFeature)
        layout_win.addLayout(layout_layer)
        layout_win.addLayout(layout_radio)
        layout_win.addLayout(layout_listWidget_attributes)
        layout_win.addWidget(self.tableWidget)
        layout_win.addLayout(layout_buttons)
        
        setDHCLayerListAttributes(self,'line')

        self.setLayout(layout_win)
        
def loadLayers(dlg,type):
    """Load layers when combobox is clicked"""
    if type=='line':
        line_check=QgsWkbTypes.LineGeometry
    else:
        line_check=QgsWkbTypes.PointGeometry
        
    oldLayerNames=[dlg.selectLayer.itemText(i) for i in range(dlg.selectLayer.count())]
    layers=QgsProject.instance().mapLayers().values()
    layers=[i.name() for i in layers if i.name() not in getDHCLayerNames() and isinstance(i, QgsVectorLayer) and i.name() not in oldLayerNames
        and i.isSpatial() and i.name() not in [tr('@default','streets'),tr('@default','buildings'),tr('@default','subnetwork'),tr('@default','lines'),tr('@default','customers'),tr('@default','energy_plants'),tr('@default','junctions')] and i.geometryType() == line_check]
    dlg.selectLayer.addItems(layers)
    
def addExpressionToMappedAttributes(dlg,dropdown):
    #print('---------------------')
    
    currentRow=dlg.tableWidget.currentRow()
    if currentRow!=-1:
        if dropdown:
            expression=dlg.tableWidget.cellWidget(currentRow, 0).currentText().split(':')[0]
        else:
            expression=dlg.tableWidget.item(currentRow, 0).text()
        attribute=dlg.tableWidget.item(currentRow, 2).text()
        dlg.mappedAttributes[attribute]=expression
        #print(dlg.mappedAttributes)

def setDHCLayerListAttributes(dlg,type):
    """Sets the layer attributes"""
    if type=='line':
        layer_name='lines'
    else:
        if dlg.rbtn_plant.isChecked():
            layer_name='energy_plants'
        else:
            layer_name='customers'
    layer=QgsProject.instance().mapLayersByName(tr('@default',layer_name))
    #print(layer)
    if layer:
        layer=layer[0]
        attributes=layer.fields()
        attributes=[str(i.name()) for i in attributes]
        dlg.listWidget_attributes.clear()
        dlg.listWidget_attributes.addItems(attributes)
        for attribute in attributes:
            dlg.mappedAttributes[attribute]=''
    
def disconnectAttributes(dlg):
    """Disconnect the attributes from layer to layer"""
    #print("Disconnect the attributes from layer to layer")
    row=dlg.tableWidget.currentRow()
    if row!=-1:
        #print(row)
        attribute=dlg.tableWidget.item(row,2).text()
        #print(attribute)
        dlg.mappedAttributes[attribute]=''
        dlg.tableWidget.removeRow(row)

def mapAttributes(dlg):
    """Map the attributes from layer to layer"""
    #print("Map the attributes from layer to layer")
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
        item.setFlags(get_item_flag("ItemIsSelectable") | get_item_flag("ItemIsEnabled"))
        dlg.tableWidget.setItem(rowPosition,1,item)
        item=QTableWidgetItem(currentLayer_attribute)
        item.setFlags(get_item_flag("ItemIsSelectable") | get_item_flag("ItemIsEnabled"))
        dlg.tableWidget.setItem(rowPosition,2,item)
    else:            
        iface.messageBar().pushMessage("Info", "Layer field already mapped!", level=Qgis.Info)  
    #print(dlg.mappedAttributes)
               
class ImportPointLayer(QDialog):
    def __init__(self,config,plugin_dir):     
        """Initialize GUI to Import Network Topology From Point Layer"""
        super().__init__()
        self.plugin_dir=plugin_dir
        self.config=config
        self.conn=dbConnect(self.config,True)
        self.cur=self.conn.cursor(cursor_factory = psycopg2.extras.RealDictCursor)
        self.mappedAttributes={}

        self.setWindowTitle(tr('@default',"import_plants_or_customers_from_layer"))
        myBoldFont=QtGui.QFont('Arial', 12)
        myBoldFont.setBold(True)
        
        self.description_importFeaturePoint=QTextEdit(tr('@default','description_importFeaturePoint'))
        
        #Select Layer
        layout_layer=QHBoxLayout()
        label_layer =QLabel(tr('@default',"point_layer"))
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
        self.rbtn_plant = QRadioButton(tr('@default','energy_plant'))
        layout_radio_type.addWidget(self.rbtn_plant)
        self.btngroup_type.addButton(self.rbtn_plant)
        self.rbtn_plant.toggled.connect(lambda: setDHCLayerListAttributes(self,'point'))
        
        self.rbtn_customer = QRadioButton(tr('@default','customer'))
        layout_radio_type.addWidget(self.rbtn_customer)
        self.btngroup_type.addButton(self.rbtn_customer)
        self.rbtn_customer.toggled.connect(lambda: setDHCLayerListAttributes(self,'point'))
        
        #Radio Buttons extend option
        layout_radio=QHBoxLayout()
        self.rbtn_extend = QRadioButton(tr('@default','extend_layer'))
        self.rbtn_extend.setChecked(True)
        layout_radio.addWidget(self.rbtn_extend)
        self.btngroup_extend.addButton(self.rbtn_extend)
        self.rbtn_truncate= QRadioButton(tr('@default','truncate_existing_layer'))
        layout_radio.addWidget(self.rbtn_truncate)
        self.btngroup_extend.addButton(self.rbtn_truncate)
        
        ##list widgets for attributes
        layout_listWidget_attributes = QHBoxLayout()
        #list widget for layer attributes
        layout_listWidget_layerAttributes = QVBoxLayout()
        label_listWidget_layerAttributes=QLabel(tr('@default','layer_fields'))
        layout_listWidget_layerAttributes.addWidget(label_listWidget_layerAttributes)
        self.listWidget_layerAttributes = QListWidget()
        layout_listWidget_layerAttributes.addWidget(self.listWidget_layerAttributes)
        layout_listWidget_attributes.addLayout(layout_listWidget_layerAttributes)
       
        #list widget for lines attributes
        layout_listWidget_FeatureAttributes = QVBoxLayout()
        label_listWidget_attributes=QLabel(tr('@default','feature_fields'))
        layout_listWidget_FeatureAttributes.addWidget(label_listWidget_attributes)
        self.listWidget_attributes = QListWidget()
        layout_listWidget_FeatureAttributes.addWidget(self.listWidget_attributes)
        layout_listWidget_attributes.addLayout(layout_listWidget_FeatureAttributes)
        
        #table for mapped attributes  
        self.tableWidget = QTableWidget(0,3)   
        self.tableWidget.setHorizontalHeaderLabels([tr('@default','expression'),'',tr('@default','fields')])     
        self.tableWidget.itemChanged.connect(lambda: addExpressionToMappedAttributes(self,False))
          
        #buttons
        #connection buttons
        layout_buttons_connect = QHBoxLayout()
        
        btn_connect=QPushButton(tr('@default','map_layer_fields'))
        btn_connect.pressed.connect(lambda: mapAttributes(self))
        layout_buttons_connect.addWidget(btn_connect)
               
        btn_disconnect=QPushButton(tr('@default','disconnect'))
        btn_disconnect.pressed.connect(lambda: disconnectAttributes(self))
        layout_buttons_connect.addWidget(btn_disconnect)
        
        #connection buttons
        layout_buttons_import = QHBoxLayout()
        self.btn_import=QPushButton(tr('@default','import'))
        layout_buttons_import.addWidget(self.btn_import)
               
        self.btn_cancel=QPushButton(tr('@default','cancel'))
        layout_buttons_import.addWidget(self.btn_cancel)
        
        #set buttons layout together
        layout_buttons=QVBoxLayout()
        layout_buttons.addLayout(layout_buttons_connect)
        layout_buttons.addLayout(layout_buttons_import)
        
        #set layouts together
        layout_win = QVBoxLayout()
        layout_win.addWidget(self.description_importFeaturePoint)
        layout_win.addLayout(layout_layer)
        layout_win.addLayout(layout_radio_type)
        layout_win.addLayout(layout_radio)
        layout_win.addLayout(layout_listWidget_attributes)
        layout_win.addWidget(self.tableWidget)
        layout_win.addLayout(layout_buttons)
        
        self.setLayout(layout_win)
        
class IDA_Districts_InputsDialog(QDialog):
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
        
        self.setLayout(layout_win)
        
class ImportGeoDataDlg(QDialog):
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

        self.setLayout(layout_win)
        
    def update_progress(self,progress):
        self.progress.setValue(progress)

    def update_finished(self,feature,main_dlg):
        #print(feature)
        refreshMap()
        if feature in ('customers','streets'):
            zoomToLayer(tr('@default',feature))
            
        if feature=='streets':
            layer = QgsProject.instance().mapLayersByName(tr('@default','streets'))
            if layer:
                node = QgsProject.instance().layerTreeRoot().findLayer(layer[0].id())
                if node:
                    node.setItemVisibilityChecked(True)
        main_dlg.statusMessage.setText('Import {} completed!'.format(feature))
        self.process_running=False
 