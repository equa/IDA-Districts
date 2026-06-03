from qgis.core import QgsProperty,QgsVectorLayer,QgsProject,QgsApplication, QgsAuthMethodConfig,QgsDataSourceUri,QgsVectorLayer
from qgis.PyQt.QtWidgets import QButtonGroup

from qgis.PyQt.QtCore import QThreadPool
from qgis.utils import iface
from qgis.PyQt.QtGui import QColor,QStandardItem

from .utility_functions.dialog import *
from .utility_functions.workers import *
from .utility_functions.layer_visualization import *
from .utility_functions.reports import *
from .utility_functions.files import *

import datetime
import tempfile
import shutil
from collections import deque

from qgis._3d import (
    QgsVectorLayer3DRenderer,
    QgsPolygon3DSymbol,
    QgsPhongMaterialSettings
)
from qgis.PyQt.QtGui import QColor

class ShowLoadAttributeDialog:
    def __init__(self,fid):
        self.dlg=LoadAttributeDialog()

        self.dlg.btn_ok.clicked.connect(lambda: setLoadAttribute(self.dlg,fid))
        self.dlg.btn_cancel.clicked.connect(lambda: closeDialog(self.dlg))
        self.dlg.show()
        
class ShowGFAAttributeDialog:
    def __init__(self,fid):
        self.dlg=GFAAttributeDialog()

        self.dlg.btn_ok.clicked.connect(lambda: setGFAAttribute(self.dlg,fid))
        self.dlg.btn_cancel.clicked.connect(lambda: closeDialog(self.dlg))
        self.dlg.show()
    
def setLoadAttribute(dlg,fid):
    sql=""
    if dlg.radioButton_existingAttribute.isChecked():
        attribute_name=dlg.comboBox_attribute.currentData()
    else:
        attribute_name=dlg.lineEdit_newAttribute.text()
        sql+="""ALTER TABLE {}.customers ADD COLUMN "{}" NUMERIC;\n""".format(dlg.config['versionName'],attribute_name)# nosec B608
        
        layersConfig=loadLayersConfig(dlg.config,get_districts_plugin_dir(),dlg.config['projectName'])
        layer =QgsProject.instance().mapLayersByName(tr('@default','customers'))
        if layer:
            data = extract_group_fields(layer[0])
            data[tr('@default','physical_data')].append(attribute_name)
            #print(data)
            layersConfig[layer[0].name()]=data
            writeLayersConfig(dlg.config,dlg.config['projectName'],layersConfig)
        
    sql+="""WITH sub AS(
	SELECT b_id,substation_id,sum(ST_Area(geom))*{} AS load FROM {}.buildings GROUP BY b_id,substation_id
)
UPDATE {}.customers c SET {} = sub.load 
	FROM sub
	WHERE c.id=sub.substation_id{};""".format(dlg.lineEdit_specificLoad.text(),dlg.config['versionName'],dlg.config['versionName'],attribute_name,"" if dlg.checkBox_allCustomers.isChecked() else " AND c.id = {}".format(fid)) # nosec B608
    #print(sql)
    dlg.cur.execute(sql)
    
    if dlg.radioButton_newAttribute.isChecked():
        setupFeatureLayerDialog('customers',dlg.cur,dlg.config,get_districts_plugin_dir())
    
    closeDialog(dlg)
    
def setGFAAttribute(dlg,fid):
    sql=""
    if dlg.radioButton_existingAttribute.isChecked():
        attribute_name=dlg.comboBox_attribute.currentData()
    else:
        attribute_name=dlg.lineEdit_newAttribute.text()
        sql+="""ALTER TABLE {}.customers ADD COLUMN "{}" NUMERIC;\n""".format(dlg.config['versionName'],attribute_name)# nosec B608
        
        layersConfig=loadLayersConfig(dlg.config,get_districts_plugin_dir(),dlg.config['projectName'])
        layer =QgsProject.instance().mapLayersByName(tr('@default','customers'))
        if layer:
            data = extract_group_fields(layer[0])
            data[tr('@default','physical_data')].append(attribute_name)
            #print(data)
            layersConfig[layer[0].name()]=data
            writeLayersConfig(dlg.config,dlg.config['projectName'],layersConfig)
        
    sql+="""WITH sub AS(
	SELECT b_id,substation_id,sum(ST_Area(geom)) AS gfa FROM {}.buildings GROUP BY b_id,substation_id
)
UPDATE {}.customers c SET {} = sub.gfa 
	FROM sub
	WHERE c.id=sub.substation_id{};""".format(dlg.config['versionName'],dlg.config['versionName'],attribute_name,"" if dlg.checkBox_allCustomers.isChecked() else " AND c.id = {}".format(fid)) # nosec B608
    #print(sql)
    dlg.cur.execute(sql)
    
    if dlg.radioButton_newAttribute.isChecked():
        setupFeatureLayerDialog('customers',dlg.cur,dlg.config,get_districts_plugin_dir())
    
    closeDialog(dlg)
    
class LoadAttributeDialog(QDialog):
    def __init__(self):
        super().__init__()

        self.config=load_plugin_settings()
        self.conn=dbConnect(self.config,True)
        if self.conn:
            self.cur=self.conn.cursor(cursor_factory = psycopg2.extras.RealDictCursor)
        
        # Load UI
        ui_path = os.path.join(os.path.dirname(__file__), "districts_setLoadAttribute.ui")
        uic.loadUi(ui_path, self)
        self.lineEdit_specificLoad.setText('30')
        self.group_attribute=QButtonGroup(self)
        self.group_attribute.addButton(self.radioButton_existingAttribute) 
        self.radioButton_existingAttribute.setChecked(True)
        self.label_newAttribute.setHidden(True)
        self.lineEdit_newAttribute.setHidden(True)
        self.group_attribute.addButton(self.radioButton_newAttribute) 
        self.group_attribute.buttonClicked.connect(self.attributeChanged)
        

        existing_attributes=getTableAttr(self.cur,self.config,'customer',withoutID=True)
        items={attribute : tr("@default",attribute) for attribute in existing_attributes}
        
        # Add items to the combobox, storing the original key as user data
        for original_key, translated_text in items.items():
            self.comboBox_attribute.addItem(translated_text, original_key) # The second argument is the userData
                    
        self.comboBox_attribute

    def attributeChanged(self,radioButton):
        if self.radioButton_existingAttribute.isChecked():
            showExistingAttribute=True
        else:
            showExistingAttribute=False
        self.label_attribute.setHidden(not showExistingAttribute)
        self.comboBox_attribute.setHidden(not showExistingAttribute)
        self.label_newAttribute.setHidden(showExistingAttribute)
        self.lineEdit_newAttribute.setHidden(showExistingAttribute)
        
class GFAAttributeDialog(QDialog):
    def __init__(self):
        super().__init__()

        self.config=load_plugin_settings()
        self.conn=dbConnect(self.config,True)
        if self.conn:
            self.cur=self.conn.cursor(cursor_factory = psycopg2.extras.RealDictCursor)
        
        # Load UI
        ui_path = os.path.join(os.path.dirname(__file__), "districts_setGFAAttribute.ui")
        uic.loadUi(ui_path, self)
        self.group_attribute=QButtonGroup(self)
        self.group_attribute.addButton(self.radioButton_existingAttribute) 
        self.radioButton_existingAttribute.setChecked(True)
        self.label_newAttribute.setHidden(True)
        self.lineEdit_newAttribute.setHidden(True)
        self.group_attribute.addButton(self.radioButton_newAttribute) 
        self.group_attribute.buttonClicked.connect(self.attributeChanged)
        

        existing_attributes=getTableAttr(self.cur,self.config,'customer',withoutID=True)
        items={attribute : tr("@default",attribute) for attribute in existing_attributes}
        
        # Add items to the combobox, storing the original key as user data
        for original_key, translated_text in items.items():
            self.comboBox_attribute.addItem(translated_text, original_key) # The second argument is the userData
                    
        self.comboBox_attribute

    def attributeChanged(self,radioButton):
        if self.radioButton_existingAttribute.isChecked():
            showExistingAttribute=True
        else:
            showExistingAttribute=False
        self.label_attribute.setHidden(not showExistingAttribute)
        self.comboBox_attribute.setHidden(not showExistingAttribute)
        self.label_newAttribute.setHidden(showExistingAttribute)
        self.lineEdit_newAttribute.setHidden(showExistingAttribute)
        
def loadBuildingsLayer(uri,config,view,username):
    uri.setDataSource(config['versionName'], "buildings", "geom")
    vlayer = QgsVectorLayer(uri.uri(False), tr('@default',"buildings"), username)
    QgsProject.instance().addMapLayer(vlayer)
    """
    target_layer = QgsProject.instance().mapLayersByName('room_units')[0]
    config_layer = {'AllowMulti': False,
              'AllowNull': True,
              'FilterExpression': '',
              'Key': 'id',
              'Layer': target_layer.id(),
              'NofColumns': 1,
              'OrderByValue': False,
              'UseCompleter': False,
              'Value': 'name'}
    widget_setup = QgsEditorWidgetSetup('ValueRelation',config_layer)
    fields=vlayer.fields()
    field_idx = fields.indexOf('room_unit')
    vlayer.setEditorWidgetSetup(field_idx, widget_setup) 

    target_layer = QgsProject.instance().mapLayersByName('building_construction_standard')[0]
    config_layer = {'AllowMulti': False,
              'AllowNull': True,
              'FilterExpression': '',
              'Key': 'id',
              'Layer': target_layer.id(),
              'NofColumns': 1,
              'OrderByValue': False,
              'UseCompleter': False,
              'Value': 'construction_standard_name'}
    widget_setup = QgsEditorWidgetSetup('ValueRelation',config_layer)
    fields=vlayer.fields()
    field_idx = fields.indexOf('z_construction')
    vlayer.setEditorWidgetSetup(field_idx, widget_setup) 

    target_layer = QgsProject.instance().mapLayersByName('zone_templates')[0]
    config_layer = {'AllowMulti': False,
              'AllowNull': True,
              'FilterExpression': '',
              'Key': 'id',
              'Layer': target_layer.id(),
              'NofColumns': 1,
              'OrderByValue': False,
              'UseCompleter': False,
              'Value': 'name'}
    widget_setup = QgsEditorWidgetSetup('ValueRelation',config_layer)
    fields=vlayer.fields()
    field_idx = fields.indexOf('z_template')
    vlayer.setEditorWidgetSetup(field_idx, widget_setup) 
    """
    single_symbol_renderer = vlayer.renderer()
    symbol = single_symbol_renderer.symbol()
    symbol.setColor(QColor.fromRgb(25, 25, 25))
    
    vlayer.triggerRepaint()  # Refresh the layer to apply the changes
    view.refreshLayerSymbology(vlayer.id())
    
    # Create the 3D symbol
    symbol = QgsPolygon3DSymbol()

    # Set height offset and extrusion based on attribute fields
    ddp = symbol.dataDefinedProperties()
    ddp.setProperty(QgsPolygon3DSymbol.PropertyHeight, QgsProperty.fromField('z_bh_m'))
    ddp.setProperty(QgsPolygon3DSymbol.PropertyExtrusionHeight, QgsProperty.fromField('z_height_m'))
    symbol.setDataDefinedProperties(ddp)

    # Create material and set color
    material = QgsPhongMaterialSettings()
    material.setDiffuse(QColor('lightgray'))
    symbol.setMaterialSettings(material)

    # Create renderer (no layer argument anymore!)
    renderer3d = QgsVectorLayer3DRenderer(symbol)

    # Apply the 3D renderer to the layer
    vlayer.setRenderer3D(renderer3d)

    # Refresh the map canvas to apply changes
    iface.mapCanvas().refresh()
    
    target_action_name = "New &3D Map View"
    
    #open 3D map view
    """
    for action in iface.mainWindow().findChildren(QAction):
        if action.text() == target_action_name:
            action.trigger()
            break
    else:
        #print(f"Could not find '{target_action_name}' action")
    """
    
def treeItem_add(level, mdlIdx,dlg,main):
    """Function to add new project version and add child item to treeview"""
    main.dlg.update_progress(0)
    versionName=dlg.input.text()
    description=dlg.input_description.text()
    #print('****************add version*****************')
    if versionName:
        newVersionName=checkIfVersionIsNew(main.cur,versionName)
        if newVersionName:
            if checkString(versionName):
                main.dlg.update_progress(1)
                #Creating version --> new schema in project        
                idBase=0
                item = main.model.itemFromIndex(mdlIdx)
                if item:
                    baseName=item.text()
                    sql="SELECT id FROM public.versionhandling WHERE name = '"+baseName+"';" # nosec B608
                    #print(sql)
                    main.cur.execute(sql)
                    for base in main.cur.fetchall():
                        idBase = base['id']         
                sql = 'INSERT INTO public.versionhandling (name,id_base,description) VALUES (\''+versionName+'\','+str(idBase)+',\''+description+'\');' # nosec B608
                #print(sql)
                main.cur.execute(sql)

                temp_key = QStandardItem(versionName)
                temp_value1 = QStandardItem('')
                main.model.itemFromIndex(mdlIdx).appendRow([temp_key, temp_value1])
                    
                auth_cfg = QgsAuthMethodConfig()
                QgsApplication.authManager().loadAuthenticationConfig(main.config["auth_id"], auth_cfg, True)
                copy_schema(item.text(),versionName,main.config,main.cur,main.plugin_dir,auth_cfg.config("username"), auth_cfg.config("password"))       
                
                data=getVersionData(main.cur)
                importData(main.model,data)
                main.dlg.treeViewVersions.expandAll()   
                main.config['versionName']=versionName
                write_plugin_settings(main.config)
                
                createNewVersionFiles(main.config,main.plugin_dir)
                
                loadVersion(main=main)
                item=get_item_by_text(versionName,main)
                highlight_item(item,main.model.invisibleRootItem())
                main.dlg.treeViewVersions.viewport().update()
                main.dlg.statusMessage.setText('New child version created: '+versionName)
                main.dlg.update_progress(100)
                closeDialog(dlg)
        else:
            main.dlg.update_progress(0)
            iface.messageBar().pushMessage("Info", "Base version {} does already exist!".format(versionName), level=Qgis.Info)
    else:
        main.dlg.update_progress(0)
        iface.messageBar().pushMessage("Info", "Please enter a version name!", level=Qgis.Info)

def treeItem_saveAs(level, mdlIdx,main,dlg):
    """Function to save project version As and add base item to treeview"""
    main.dlg.update_progress(0)
    versionName=main.dlg_saveAsVersion.input.text()
    description=main.dlg_saveAsVersion.input_description.text()
    if versionName:
        newVersionName=checkIfVersionIsNew(main.cur,versionName)
        if newVersionName:
            #Creating version --> new schema in project        
            item = main.model.itemFromIndex(mdlIdx)

            sql = 'INSERT INTO public.versionhandling (name,id_base,description) VALUES (\''+versionName+'\',0,\''+description+'\');' # nosec B608
            #print(sql)
            main.cur.execute(sql)

            temp_key = QStandardItem(versionName)
            temp_value1 = QStandardItem('')
            main.model.itemFromIndex(mdlIdx).appendRow([temp_key, temp_value1])
                
            auth_cfg = QgsAuthMethodConfig()
            QgsApplication.authManager().loadAuthenticationConfig(main.config["auth_id"], auth_cfg, True)

            copy_schema(item.text(),versionName,main.config,main.cur,main.plugin_dir,auth_cfg.config("username"), auth_cfg.config("password"))
            data=getVersionData(main.cur)
            importData(main.model,data)
            
            highlight_item(get_item_by_text(main.config['versionName'],main),main.model.invisibleRootItem())
        
            main.dlg.treeViewVersions.expandAll()   
            main.dlg.statusMessage.setText('New base version created: '+versionName)
            main.dlg.update_progress(100)
            closeDialog(dlg)
        else:
            main.dlg.update_progress(0)
            iface.messageBar().pushMessage("Error", "Base version {} does already exist!".format(versionName), level=Qgis.Critical)
    else:
        main.dlg.update_progress(0)
        iface.messageBar().pushMessage("Error", "Please enter a version name!", level=Qgis.Critical)

def getDescription(versionName,cur):
    sql='SELECT description FROM public.versionhandling WHERE name=\''+versionName+'\';' # nosec B608
    cur.execute(sql)
    return cur.fetchone()['description']   
   
def treeItem_rename(level,mdlIdx,main,dlg): 
    """ Renames a project version, if the version name does not exist and is not empty"""
    #print('Rename')
    versionName=main.dlg_renameVersion.input.text()
    description=main.dlg_renameVersion.input_description.text()
    if versionName:
        try:
            newVersionName=checkIfVersionIsNew(main.cur,versionName)
            item = main.model.itemFromIndex(mdlIdx)
            oldSchemaName=item.text()
            if newVersionName:
                #print(oldSchemaName)
                newSchemaName=versionName
                #print(newSchemaName)
                main.model.setData(mdlIdx, versionName)
                sql = 'ALTER SCHEMA "'+oldSchemaName+'" RENAME TO "'+newSchemaName+'";' # nosec B608
                #print(sql)
                main.cur.execute(sql)
                sql = 'UPDATE public.versionhandling SET name= \''+newSchemaName+'\' WHERE name= \''+oldSchemaName+'\';'# nosec B608
                #print(sql)
                main.cur.execute(sql)
            else:
                iface.messageBar().pushMessage("Error", "Version {} does already exist!".format(versionName), level=Qgis.Critical)
            sql = 'UPDATE public.versionhandling SET description = \''+description+'\' WHERE name= \''+versionName+'\';'# nosec B608
            #print(sql)
            main.cur.execute(sql)
            data=getVersionData(main.cur)
            importData(main.model,data)
            if oldSchemaName==main.config['versionName']:
                main.config['versionName']=versionName
                write_plugin_settings(main.config)
                loadVersion(main=main)
            highlight_item(get_item_by_text(main.config['versionName'],main),main.model.invisibleRootItem())            
            main.dlg.treeViewVersions.expandAll()
            closeDialog(dlg)
            
            main.dlg.statusMessage.setText(f'Rename verion "{oldSchemaName}" to "{versionName}" completed!')
        except Exception as e:
            main.dlg.statusMessage.setText(f'Rename verion "{oldSchemaName}" to "{versionName}" falied!')
    else:
        iface.messageBar().pushMessage("Error", "Please enter a version name!", level=Qgis.Critical)           
        
def treeItem_delete(item,dlg,main):
    """Function to delete project version and removes it from the tree"""
    #print('--treeItem_delete--')
    main.dlg.update_progress(1)
    try:
        sql = 'DROP SCHEMA "'+item.text()+'" CASCADE;'
        #print(sql)
        main.cur.execute(sql)
    except:
        pass
    try:
        idBase=''
        sql="SELECT id, id_base FROM public.versionhandling WHERE name = '"+item.text()+"';" # nosec B608
        #print(sql)
        main.cur.execute(sql)
        sql=''
        for base in main.cur.fetchall():
            #print(base)
            sql += 'UPDATE public.versionhandling SET id_base = {} WHERE id_base ='.format(base['id_base'])+str(base['id'])+';\n' # nosec B608
        #print(sql)
        main.cur.execute(sql)         
        
        sql = 'DELETE FROM public.versionhandling WHERE name = \''+item.text()+'\';'# nosec B608
        #print(sql)
        main.cur.execute(sql)
        
        #delete modelling plugin folder if exists
        if os.path.exists(main.config['pathProjects']+'{}\\versions\\{}\\'.format(main.config['projectName'],item.text())):
            shutil.rmtree(main.config['pathProjects']+'{}\\versions\\{}\\'.format(main.config['projectName'],item.text()))
        if item.parent():
            main.config['versionName']=item.parent().text()
        else:
            main.config['versionName']=''
        write_plugin_settings(main.config)
        removeLayers() 
        main.dlg.update_progress(100)
    except:
        main.dlg.update_progress(0)

    if item.parent():
        item.parent().removeRow(item.row())
    else:
        main.model.removeRow(item.row())
    data=getVersionData(main.cur)
    importData(main.model,data)
    main.dlg.treeViewVersions.expandAll() 
    closeDialog(dlg)
        
def getVersionData(cur):
    data=[]
    try:
        sql = 'SELECT id ,id_base ,name ,description FROM public.versionhandling;'
        cur.execute(sql)
        for version in cur.fetchall():
            data.append({'unique_id': version['id'], 'parent_id': version['id_base'], 'name': version['name'], 'description': version['description']})
    except:
        pass
    #print(data)
    return data
        
def checkIfVersionIsNew(cur,versionName):
    sql='SELECT schema_name FROM information_schema.schemata;'
    cur.execute(sql)
    newVersionName=True
    for schema in cur.fetchall():
        if schema['schema_name']==versionName:
            newVersionName=False   
    return newVersionName
        
def addBaseVersion(dlg,main):
    """add new base version to DB if a version name is entered and version does not exists in DB"""
    main.config['versionName']=dlg.input.text()
    description=dlg.input_description.text()
    #print(main.config['versionName'])
    if main.config['versionName']:
        #check if version name exists
        newVersionName=checkIfVersionIsNew(main.cur,main.config['versionName'])
        #print(newVersionName)        
        if newVersionName:
            if checkString(main.config['versionName']):
                main.dlg.update_progress(1)

                #Creating version --> new schema in project      
                sql = 'CREATE SCHEMA IF NOT EXISTS "'+main.config['versionName']+'";'
                #print(sql)
                main.cur.execute(sql) 

                idBase=0
                sql = 'INSERT INTO public.versionhandling (name,id_base,description) VALUES (\''+main.config['versionName']+'\','+str(idBase)+',\''+description+'\');' # nosec B608
                #print(sql)
                main.cur.execute(sql) 
                
                #create tables in new schema
                filedata=""
                temp_folder = districtsModelerTempDir()
                if os.path.exists(main.plugin_dir+"\\DB_versionTablesDefault.txt"):
                    with open(main.plugin_dir+"\\DB_versionTablesDefault.txt", "r") as myfile:
                        for line in myfile:
                            filedata=filedata+line
                    newdata = filedata.replace("$versionName$", main.config['versionName'])
                    newdata = newdata.replace("$srid$", main.projectConfig['srid'])
                    newdata = newdata.replace("$plugins_path$", main.plugin_dir)
                    newdata = newdata.replace("$districts_path$", main.config['pathDistricts'])
                    
                    with open(temp_folder+"DB_versionTables.txt",'w') as myfile:
                        myfile.write(newdata)   
                    #print(newdata)
                    main.cur.execute(newdata)
                    
                #insert data in new schema
                filedata=""
                if os.path.exists(main.plugin_dir+"\\DB_versionTablesDefault_data.txt"):
                    with open(main.plugin_dir+"\\DB_versionTablesDefault_data.txt", "r") as myfile:
                        for line in myfile:
                            filedata=filedata+line
                    newdata = filedata.replace("$versionName$", main.config['versionName'])
                    newdata = newdata.replace("$plugins_path$", main.plugin_dir)
                    
                    with open(temp_folder+"DB_versionTables_data.txt",'w') as myfile:
                        myfile.write(newdata)     
                    main.cur.execute(newdata)
                    
                #create version directory & copy climate files
                createNewVersionFiles(main.config,main.plugin_dir)

                data=getVersionData(main.cur)
                importData(main.model,data)
                main.dlg.treeViewVersions.expandAll() 
                loadVersion(main=main)
                closeDialog(dlg)
        else:
            iface.messageBar().pushMessage("Error", "Base version {} does already exist!".format(main.config['versionName']), level=Qgis.Critical)
    else:
        iface.messageBar().pushMessage("Error", "Please enter a version name!", level=Qgis.Critical)

def createNewVersionFiles(config,plugin_dir):
    versions_dir=config['pathProjects']+'{}\\versions'.format(config['projectName'])
    createDir(versions_dir,config['versionName'])             
                
# Function to load version from treeview
def treeItem_load(item, mdlIdx,main):
    main.config['versionName'] = item.text()
    write_plugin_settings(main.config)
    loadVersion(item=item,main=main)
        
def showProjectConfigData(dlg,main):
    """ Show the onfiguration data from file configIDADistricts.txt"""
    #print('--showProjectConfigData--')
    if main.conn:
        main.projectConfig=loadProjectConfig(main.config)       
        #print(main.projectConfig)
        if main.projectConfig:
            dlg.srid.setText(main.projectConfig['srid'])
        else:
            iface.messageBar().pushMessage("Warning", "Project config not found!", level=Qgis.Info)        
    else:
        iface.messageBar().pushMessage("Info", tr('@default','no_db_connection'), level=Qgis.Info)        

def saveProjectConfigSettings(dlg,main):
    """ save project config data to file projectConfig.txt"""
    #print('saveProjectConfigSettings')    
    srid_old=main.projectConfig['srid']        
    main.projectConfig['srid']=dlg.srid.text()

    if main.conn:
        writeProjectConfig(main.config,main.config['projectName'],main.projectConfig)
        projectVersions=getProjectVersionNames(main.cur)
        
        if srid_old!=main.projectConfig['srid']:
            updateTableSrid(projectVersions,main.cur,main.projectConfig['srid'])
        if checkDBVersionConnected(main.config,False) and srid_old!=main.projectConfig['srid']:
            loadVersionLayers(main.config,main.cur,main.plugin_dir)
        main.dlg.btn_sridProject.setText('EPSG: '+str(main.projectConfig['srid']))

            
    dlg.close()
        
def importData(model, data, root=None):
    #print(model)
    if model:
        model.setRowCount(0)
        if root is None:
            root = model.invisibleRootItem()
        seen = {}   # List of  QStandardItem
        values = deque(data)
        while values:
            value = values.popleft()
            if value['parent_id'] == 0:
                parent = root
            else:
                pid = value['parent_id']
                if pid not in seen:
                    values.append(value)
                    continue
                parent = seen[pid]
            unique_id = value['unique_id']
            parent.appendRow([
                QStandardItem(value['name']),
                QStandardItem(value['description'])
            ])
            seen[unique_id] = parent.child(parent.rowCount() - 1)
            
def deleteProject(projectName,main_dlg,cur_postgres,plugin_dir,config,model,dlg=None):
    """Drop selected DB """
    index=main_dlg.selectProject.findText(projectName)
    if index!=-1:
        #print('Delete DB: {}'.format(projectName))
        main_dlg.update_progress(1)
        
        #close open connections
        sql="""SELECT pg_terminate_backend(pg_stat_activity.pid)
FROM pg_stat_activity
WHERE pg_stat_activity.datname = '{}'
  AND pid <> pg_backend_pid();""".format(projectName) # nosec B608
        #print(sql)
        cur_postgres.execute(sql)

        sql='DROP DATABASE IF EXISTS {};'.format(projectName) # nosec B608
        cur_postgres.execute(sql)
        main_dlg.selectProject.removeItem(index)
        
        #delete folders
        dir = os.path.normpath(os.path.join(config['pathProjects'], projectName))
        #print(dir)
        try:
            shutil.rmtree(dir)
        except:
            pass
  
        main_dlg.projectNames=[i for i in main_dlg.projectNames if i!=projectName]
        if projectName==config['projectName']:
            config['projectName']=''
            config['versionName']=''
            write_plugin_settings(config)
            removeLayers()
            data=[]
            importData(data,model)
        try: 
           dlg.close()
        except:
            pass
        main_dlg.update_progress(100)
        main_dlg.statusMessage.setText(tr('@default','project_deleted').format(projectName))

            
def loadVersionLayers(config,cur,plugin_dir):
    """Loads the layers in QGIS"""
    removeLayers()    
            
    #print(config['projectName'])
    
    auth_cfg = QgsAuthMethodConfig()
    QgsApplication.authManager().loadAuthenticationConfig(config["auth_id"], auth_cfg, True)

    uri = QgsDataSourceUri()
    uri.setConnection(config['host'], config['port'], config['projectName'], auth_cfg.config("username"), auth_cfg.config("password"))
    #print(uri)

    view = iface.layerTreeView()
    loadTopologyLayers(config['versionName'],uri,config,auth_cfg.config("username"))   
    loadBuildingsLayer(uri,config,view,auth_cfg.config("username"))    
    try: 
        #uri.setDataSource(config['versionName'], "submodels", "geom")
        #vlayer = QgsVectorLayer(uri.uri(False), "submodels", auth_cfg.config("username"))
        #QgsProject.instance().addMapLayer(vlayer)
        #single_symbol_renderer = vlayer.renderer()
        #symbol = single_symbol_renderer.symbol()
        #symbol.setColor(QColor.fromRgb(255, 0, 0))
        #view.refreshLayerSymbology(vlayer.id())

        uri.setDataSource(config['versionName'], "streets", "geom")
        vlayer = QgsVectorLayer(uri.uri(False), tr('@default',"streets"), auth_cfg.config("username"))
        QgsProject.instance().addMapLayer(vlayer) 
        single_symbol_renderer = vlayer.renderer()
        symbol = single_symbol_renderer.symbol()
        symbol.setColor(QColor.fromRgb(131, 131, 131))
        symbol.setWidth(0.75)  
        view.refreshLayerSymbology(vlayer.id())
        
        
    except Exception as e:
        #print(f'error: {e}')
        pass
    
    loadProjectLayers(config['versionName'],uri,config,plugin_dir,cur,auth_cfg.config("username"))
    view = iface.layerTreeView()
    #view.setLayerVisible(QgsProject.instance().mapLayersByName('submodels')[0], False)    
    view.setLayerVisible(QgsProject.instance().mapLayersByName(tr('@default','streets'))[0], False)    
    view.setLayerVisible(QgsProject.instance().mapLayersByName(tr('@default','junctions'))[0], False)    

    
    #loadBoreholesLayer(config['versionName'],uri,config,plugin_dir,cur,auth_cfg.config("username"))

   
    versionLayersAliasNames()
    setupVersionForm(cur,plugin_dir,config)
    setupCustomerDataSheet(config,plugin_dir,loadProjectConfig(config))
    setupCustomerLoadValue(config,plugin_dir,loadProjectConfig(config))
    setupCustomerGFAValue(config,plugin_dir,loadProjectConfig(config))
      
    valueRelationPipeBundleType()    
    zoomToLayer('customers')
    
def finishedImportProject(dlg=None,main=None,projectName=''):
    #print('+++finished import project+++')
    
    if main:
        #print(main.config)
        #print(projectName)
        main.dlg.projectNames.append(main.config['projectName'])
        main.dlg.selectProject.addItem(main.config['projectName'])
        main.dlg.selectProject.setCurrentText(main.config['projectName'])
        main.loadProject()
        if dlg and dlg.selectTemplate.currentData() in ['heating_network']:
            main.config['versionName']='base1'
            loadVersion(main=main)
        else:
            main.config['versionName']=''
            removeLayers()
        main.dlg.statusMessage.setText('New project created!')
        main.process_running=False
    if dlg==None:
        main.config['versionName']=''
        
    setDistrictsModelerVersion2DB(main.cur,main.config)
    write_plugin_settings(main.config)
    
    if dlg:
        dlg.process_running=False
        closeDialog(dlg)

def get_item_by_text(text,main):
    # Iterate over all the items in the model and find the one with the given text
    root_node = main.model.invisibleRootItem()
    
    def find_item_by_text(item, text):
        if item.text() == text:
            return item
        for row in range(item.rowCount()):
            child = item.child(row)
            found = find_item_by_text(child, text)
            if found:
                return found
        return None
    
    return find_item_by_text(root_node, text)  

# Function to highlight a specific item
def highlight_item(item,root_item):
    # Reset background of all items first
    reset_items_background(root_item)
    # Highlight the specific item
    item.setBackground(QColor(211, 211, 211))  # Bright Grey (RGB)

def reset_items_background(item):
    # Set the background of the current item to white
    item.setBackground(QColor(255, 255, 255))  # White color

    # Recursively reset the background of child items
    for row in range(item.rowCount()):
        reset_items_background(item.child(row))    

def finishedLoadVersion(main):
    main.config=load_plugin_settings()
    main.dlg.labelActiveProject.setText(main.config['projectName'])
    main.dlg.label_activeVersion.setText(main.config['versionName'])
    main.dlg.statusMessage.setText(tr('@default','version_loaded').format(main.config['versionName']))


def loadVersion(main=None,item=None):
    #print('loadVersion')
    if main and main.conn:
        if item==None:
            item=get_item_by_text(main.config['versionName'],main)
            
        auth_cfg = QgsAuthMethodConfig()
        QgsApplication.authManager().loadAuthenticationConfig(main.config["auth_id"], auth_cfg, True)
  
        uri = QgsDataSourceUri()
        uri.setConnection(main.config['host'], main.config['port'], main.config['projectName'], auth_cfg.config("username"), auth_cfg.config("password"))
        loadVersionLayers(main.config,main.cur,main.plugin_dir)
        
        highlight_item(item,main.model.invisibleRootItem())
        main.dlg.treeViewVersions.viewport().update()
            
        worker_loadVersion = WorkerLoadVersion(config=main.config,cur=main.cur,dlg=main.dlg)
        worker_loadVersion.signals.error.connect(main.dlg.show_error_message)
        worker_loadVersion.signals.progress.connect(main.dlg.update_progress)      
        worker_loadVersion.signals.finished.connect(lambda: finishedLoadVersion(main))                
                    
        QThreadPool.globalInstance().start(worker_loadVersion)
    else:
        iface.messageBar().pushMessage("Info", tr('@default','no_db_connection'), level=Qgis.Info)        
    
    
def createNewProject(dlg,main):
    #print('--create new project--')
    dlg.update_progress(0)
    if checkString(dlg.project_name.text()):
        if checkDBName(dlg.project_name.text(),main.dlg.projectNames):
            dlg.update_progress(1)
            main.config['projectName']=dlg.project_name.text()
            if dlg.selectTemplate.currentData() in ['db_default_values','empty_project']:
                main.config['versionName']=''
                versionNames=[]
            else:
                main.config['versionName']='base1'
                versionNames=['base1']
            #print(main.plugin_dir)
            project_name=dlg.selectTemplate.currentText().lower().replace(' ','_')
            if dlg.selectTemplate.currentData() in ['db_default_values','empty_project','heating_network']:
                filename=main.plugin_dir+'\\templates\\'+dlg.selectTemplate.currentData()
                filename=filename.replace('/','\\')
            else:
                filename=main.config['pathDistricts']+'samples\\districts\\'+dlg.selectTemplate.currentData()
                filename=filename.replace('/','\\')
            #print(filename)

            if dlg.checkbox_DBResults.isChecked():
                no_db_results=False
            else:
                no_db_results=True
            if dlg.checkbox_prn.isChecked():
                filter_extensions=[]
            else:
                filter_extensions=['.prn']
            filter_folders=[]
            if not dlg.checkbox_invokedFeatures.isChecked():
                filter_folders.append('invoked_customers')
                filter_folders.append('invoked_energy_plants')
                
            auth_cfg = QgsAuthMethodConfig()
            QgsApplication.authManager().loadAuthenticationConfig(main.config["auth_id"], auth_cfg, True)  
            dlg.update_progress(10)
            main.worker_newProject = WorkerImportProject(versionNames=versionNames,projectNames=main.dlg.projectNames,project_name=main.config['projectName'],filename=filename,config=main.config,password=auth_cfg.config("password"),username=auth_cfg.config("username"),plugin_dir=main.plugin_dir,cur=main.cur_postgres,dlg=dlg,filter_extensions=filter_extensions,filter_folders=filter_folders,no_db_results=no_db_results)
            main.worker_newProject.signals.progress.connect(dlg.update_progress)
            main.worker_newProject.signals.error.connect(dlg.show_error_message)
            main.worker_newProject.signals.finished.connect(lambda: finishedImportProject(dlg=dlg,main=main))                
            QThreadPool.globalInstance().start(main.worker_newProject)    
            
def exportProject(config=None,plugin_dir=None,filename=None,dlg=None,exportPrn=None,exportInvokedFeatures=None,exportDBResults=None,main_dlg=None,autosave=None):
    """Export the DB to a sql file and write the data center and modelling files to the folders + dDB description file --> zip"""
    #print("Export project")
    #print(filename)

    if not filename:
        # Get current date and time
        current_datetime = datetime.datetime.now()
        # Format the datetime to 'Year-Month-Day-HourMinuteSecond'
        formatted_datetime = current_datetime.strftime('%Y_%m_%d_%H%M%S')

        filename=tempfile.gettempdir()+'\\ida_districts\\'+config['projectName']+'_'+formatted_datetime
        
    if filename.split('\\') and filename.split('\\')[-1].split('.') and checkString(filename.split('\\')[-1].split('.')[0]):
        filter_extensions=[]
        if not exportPrn:
            filter_extensions.append('.prn')
        filter_folders=[]
        if not exportInvokedFeatures:
            filter_folders.append('invoked_customers')
            filter_folders.append('invoked_energy_plants')
        if not exportDBResults:
            no_db_results=True
        else:
            no_db_results=False

        if filename:
            auth_cfg = QgsAuthMethodConfig()
            QgsApplication.authManager().loadAuthenticationConfig(config["auth_id"], auth_cfg, True)
            worker_export = WorkerExportProject(plugin_dir=plugin_dir, filename=filename,config=config,password=auth_cfg.config("password"),username=auth_cfg.config("username"),filter_extensions=filter_extensions,filter_folders=filter_folders,no_db_results=no_db_results,autosave=autosave)
            if dlg:
                worker_export.signals.progress.connect(dlg.update_progress)
                worker_export.signals.error.connect(dlg.show_error_message)      
            worker_export.signals.finished.connect(lambda: finishedExportProject(config,filename,main_dlg))
            
            QThreadPool.globalInstance().start(worker_export)   
            
def finishedExportProject(config,filename,main_dlg):
    msg="Districts project ({}) saved: ".format(config['projectName'])+filename
    iface.messageBar().pushMessage("Info", msg, level=Qgis.Info)
    if main_dlg:    
        main_dlg.statusMessage.setText(msg)


