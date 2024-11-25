from plugins.utility_functions.db import *
from plugins.utility_functions.files import *
from plugins.utility_functions.topology import *
from plugins.utility_functions.macros import *
from plugins.utility_functions.dialog import *
from plugins.utility_functions.sensor_signals import AssettypeSensorSignals


import psycopg2
from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT
import psycopg2.extras
from .ida_districts_modeling_simulation_dialog import InvokeFeaturesDlg
from .calibrate_customers import *
from plugins.utility_functions.sensor_signals import *
from qgis.PyQt.QtWidgets import QTableWidgetItem,QTableWidget, QTabWidget

from qgis.PyQt.QtCore import QSettings, QTranslator, QCoreApplication,Qt,QThreadPool
from plugins.utility_functions.util import *
from plugins.utility_functions.layer_visualization import *
from plugins.utility_functions.workers import *
from qgis.utils import iface
from qgis.core import  QgsCredentials,QgsDataSourceUri, QgsExpression, QgsOptionalExpression,QgsAttributeEditorField,QgsAttributeEditorContainer, QgsEditFormConfig, QgsProject, QgsSvgMarkerSymbolLayer, QgsEditorWidgetSetup, QgsVectorLayer, QgsSymbol, QgsRendererCategory, QgsCategorizedSymbolRenderer
import math
import copy
import numpy as np
import matplotlib.pyplot as plt
import re

import datetime
import matplotlib.dates as mdates
from matplotlib.ticker import AutoMinorLocator
from plugins.utility_functions.ida_components import *  

class WorkerInvokeFeatures(QRunnable):
    """Worker thread
    Inherits from QRunnable to handle worker thread setup, signals and wrap-up."""
    def __init__(self,*args,**kwargs):
        super().__init__()
        self.args=args
        print(args)
        self.signals=APISignals()
        self.dictDB=kwargs['dictDB']
        self.dlg=kwargs['dlg']
        self.type=kwargs['type']
        self.conn=""
        self.cur=""
        self.plugin_dir=kwargs['plugin_dir']
        self.conn = dbConnect(self.dictDB,True)
        self.rows=kwargs['rows']
        if self.conn:
            self.cur=self.conn.cursor(cursor_factory = psycopg2.extras.RealDictCursor)
            
    @pyqtSlot()
    def run(self):
        print('Generate network topology')
        self.progress_value=1
        self.signals.progress.emit(self.progress_value)
        
        requestedOutputs=loadRequestedOutputs(self.plugin_dir,self.dictDB)
        invokedOutputs=loadInvokedOutputs(self.plugin_dir,self.dictDB)
        sql="""TRUNCATE {}.invoked_sf;
SELECT setval('{}.invoked_sf_id_seq', 1, false);""".format(self.dictDB['versionName'],self.dictDB['versionName'])
        self.cur.execute(sql)
        
        rows_count=len(self.rows)
        for idx in self.rows:
            print(idx)
            invokeOneFeature(self.dlg,idx,self.plugin_dir,self.cur,self.dictDB,self.type,invoked=True,parallize=True)
            if self.type=='energy_plant':
                invokedOutputs[self.type+'s'][int(self.dlg.tableWidget_customer.item(idx,0).text())]={'power_ep': True if requestedOutputs['power_ep'] else False, 'temp_ep': True if requestedOutputs['temp_ep'] else False, 'p_ep': True if requestedOutputs['p_ep'] else False, 'mdot_ep': True if requestedOutputs['mdot_ep'] else False}
            elif self.type=='customer':
                invokedOutputs[self.type+'s'][int(self.dlg.tableWidget_customer.item(idx,0).text())]={'power_c': True if requestedOutputs['power_c'] else False, 'temp_c': True if requestedOutputs['temp_c'] else False, 'p_c': True if requestedOutputs['p_c'] else False, 'mdot_c': True if requestedOutputs['mdot_c'] else False, 'heatbalance_c': True if requestedOutputs['heatbalance_c'] else False, 'troom_c': True if requestedOutputs['troom_c'] else False}
            self.progress_value=int((idx+1)/rows_count*98)
            self.signals.progress.emit(self.progress_value)
        writeInvokedOutputs(self.plugin_dir,self.dictDB,invokedOutputs)
        self.signals.progress.emit(100)  
            
def loadCustomerParm(dlg,cur,dictDB):
    sql="""SELECT * FROM "{}".customer_model_parms ORDER BY id;""".format(dictDB['versionName'])
    cur.execute(sql)
    i=0
    table=dlg.tableWidget_parameters
    for parm in cur.fetchall():
        table.insertRow(i)
            
        table.setItem(i,0,QTableWidgetItem(parm['mapping_expression']))
                    
        comboBox = QComboBox()
        comboBox.addItems(['<-->','<--','-->'])
        comboBox.setCurrentText(parm['mapping_direction'])
        table.setCellWidget(i, 1, comboBox)  
        
        table.setItem(i,2,QTableWidgetItem(parm['parm_name']))
        table.setItem(i,3,QTableWidgetItem(parm['model_name']))
        table.setItem(i,4,QTableWidgetItem(parm['macro_name']))

        i+=1
        
def loadLayerFieldsToList(list,layer_name):
    layer=QgsProject.instance().mapLayersByName(layer_name)
    print(layer)
    if layer:
        layer=layer[0]
        attributes=layer.fields()
        attributes=[str(i.name()) for i in attributes]
        list.addItems(attributes)
        
def setCustParm(dlg,conn,dictDB,plugin_dir):
    """" Save table to DB an close dialog"""
    if conn:
        cur=conn.cursor(cursor_factory = psycopg2.extras.RealDictCursor)   
        
        sql="""TRUNCATE "{}".customer_model_parms CASCADE;\n""".format(dictDB['versionName'])
        columns='id,mapping_expression,parm_name,model_name,macro_name,mapping_direction'
        table=dlg.tableWidget_parameters
        
        i=0
        for row in range(table.rowCount()):
            #write data to DB table customer_model_parms
            values=str(row)+", '"+(table.item(row, 0).text().replace("'","''") if table.item(row, 0) else '') +"', '"+(table.item(row, 2).text() if table.item(row, 2) else '')+"', '"+(table.item(row, 3).text() if table.item(row, 3) else '')+"', '"+(table.item(row, 4).text() if table.item(row, 4) else '')+"', '"+table.cellWidget(row, 1).currentText()+"'"
            sql+="""INSERT INTO "{}".customer_model_parms ({}) VALUES ({});\n""".format(dictDB['versionName'],columns,values)
            
        print(sql)
        cur.execute(sql)
 
        dlg.close()
    
def setupCustomerVersionForm(cur,dictDB,plugin_dir):  
    """ setup form for customer layer"""
    vlayerName='customers'
    removeLayer(vlayerName)
    loadFeatureLayer(dictDB['versionName'],dictDB,plugin_dir,vlayerName,cur)
    
    vlayer=QgsProject.instance().mapLayersByName(vlayerName)[0] 
    fields=vlayer.fields()
    fc = vlayer.editFormConfig()
    fc.clearTabs()
    fc.setLayout(QgsEditFormConfig.TabLayout)
    modelParm=getALiasNameCustParm(cur,dictDB)
    
    attrNamesTabs= [['id','assetgroup','assettype','network'],
                    ['heat_e_kwh','heat_p_kw','tsup_h_deg','cool_e_kwh','cool_p_kw','tsup_c_deg'],
                    ['dhw_id', 'dhw_scale','internal_load_id','submodel',modelParm],
                    ['owner','building_nr','street','street_nr','zip','location','usage','energy_carrier','qdot_heat_kw','heat_kwh7a','full_load_hours_h7a','Tsup_max_deg','Tret_max_deg','connection','connection_since']]
    for tab,attrNamesTab in zip(['General','Physical data','Simulation data','Metadata'],attrNamesTabs):
        if attrNamesTab:
            c = QgsAttributeEditorContainer(tab, fc.invisibleRootContainer())
            c.setIsGroupBox(False) # a tab
            for attrName in attrNamesTab:
                print (attrName)
                if type(attrName) is list:
                    print(attrName)
                    c1 = QgsAttributeEditorContainer("Modelparameter", fc.invisibleRootContainer())
                    c1.setIsGroupBox(True)
                    for i in range(0,len(attrName)):
                        field_idx = fields.indexOf(attrName[i])
                        c1.addChildElement(QgsAttributeEditorField(attrName[i], field_idx, c1))
                    c.addChildElement(c1)
                else:    
                    field_idx = fields.indexOf(attrName)
                    c.addChildElement(QgsAttributeEditorField(attrName, field_idx, c))
            fc.addTab(c)
    vlayer.setEditFormConfig(fc)

def addParmTableRow(dlg):
    addTableRow(dlg.tableWidget_parameters)
    dlg.tableWidget_parameters.setItem(0 , 0, QTableWidgetItem(''))
    comboBox = QComboBox()
    comboBox.addItems(['<-->','<--','-->'])
    comboBox.setCurrentText('<-->')
    dlg.tableWidget_parameters.setCellWidget(0, 1, comboBox)  
    dlg.tableWidget_parameters.setItem(0 , 2, QTableWidgetItem(''))
    dlg.tableWidget_parameters.setItem(0 , 3, QTableWidgetItem(''))        
    dlg.tableWidget_parameters.setItem(0 , 4, QTableWidgetItem(''))        
        
def invokeOneFeature(dlg,idx,plugin_dir,cur,dictDB,type,invoked,parmRun=False,saveParmRunResults=False,parallize=False):
    """Invoke the selected feature. Copy the files from the assettype templates to ida_districts_modeling_simulation\invoked_"feature"s
        If dlg is not given the id is the idx"""    
    print('idx='+str(idx))
    print(parmRun)
    if idx !=-1:
        if dlg and not saveParmRunResults:
            id=dlg.tableWidget_customer.item(idx,0).text()  
        else:
            id=idx
        print('id='+id)            
        dir=plugin_dir+"\\network_models\\{}\\{}\\invoked_{}s\\".format(dictDB['projectName'],dictDB['versionName'],type)
            
        sql="""SELECT c.assetgroup, c.assettype, at.assettype_name, at.conn_bundle_type 
            FROM "{}".{}s c,{}_assettypes at 
            WHERE c.assetgroup=at.assetgroup AND c.assettype=at.assettype AND c.id={};""".format(dictDB['versionName'],type,type,id)
        print(sql)
        cur.execute(sql)
        type_old=""
        assetgroup_old=""
        assettype_old=""
        for feature in cur.fetchall():
            print(feature)
            assettype_name=str(feature['assetgroup'])+'_'+str(feature['assettype'])+'_'+str(feature['assettype_name'])
    
            dir_assettype=getDataCenterDir(plugin_dir).replace('/','\\')+"\\{}\\{}_assettypes".format(dictDB['projectName'],type)            
            
            #create directory and files in modelling plugin folder
            dir=plugin_dir+'\\network_models'
            createDir(dir,dictDB['projectName'])
            dir+='\\'+dictDB['projectName']
            createDir(dir,dictDB['versionName'])
            dir+='\\'+dictDB['versionName']
            createDir(dir,'invoked_{}s'.format(type)) 
            dir+='\\'+'invoked_{}s'.format(type)
            createDir(dir,type.capitalize()+"_"+id)
            
            replaceDict={}
            
            if type=='customer':
                #dhw
                sql="""SELECT dhw.id, dhw.description FROM "{}".customers c, public.dhw_timeseries dhw WHERE dhw.id=c.dhw_id AND c.id={};""".format(dictDB['versionName'],id)
                print(sql)
                cur.execute(sql)
                dhw=cur.fetchone()
                dhw_file=False
                if dhw:
                    dhw_name=dhw['description']
                    dir_dhw=plugin_dir+'\\network_models'+'\\'+dictDB['projectName']+'\\'+dictDB['versionName']
                    createDir(dir_dhw,'dhw_profiles')
                    dir_dhw+='\\dhw_profiles'                                            
                    dhw_file=dir_dhw+"\\{}.prn".format(dhw_name.split('/')[-1])

                    if not os.path.exists(dhw_file): 
                        sql="""SELECT time_h, round(kg7s,6) AS kg7s FROM public.dhw WHERE dhw_id={} ORDER BY time_h;""".format(dhw['id'])
                        print(sql)
                        cur.execute(sql)
                        
                        data="# Time mdot\n"
                        for line in cur.fetchall():
                            data+= str(line['time_h'])+ ' '+ str(line['kg7s']) +"\n"
                        writeToFile(data,dir_dhw,dhw_file)
                    
                    dhw_file=dhw_file.replace('/','\\').replace('\\','\\\\')
                    print(dhw_file)
                    
                #internal loads
                sql="""SELECT l.id, l.description FROM "{}".customers c, public.internal_loads_profiles l WHERE l.id=c.internal_load_id AND c.id={};""".format(dictDB['versionName'],id)
                cur.execute(sql)
                internal_load=cur.fetchone()
                internal_loads_file=False
                if internal_load:
                    internal_load_name=internal_load['description']
                    dir_internal_loads=plugin_dir+'\\network_models'+'\\'+dictDB['projectName']+'\\'+dictDB['versionName']
                    createDir(dir_internal_loads,'internal_loads_profiles')
                    dir_internal_loads+='\\internal_loads_profiles'                                            
                    internal_loads_file=dir_internal_loads+"\\{}.prn".format(internal_load_name.split('/')[-1])

                    if not os.path.exists(internal_loads_file): 
                        sql="""SELECT time_h, round(person_w7m2,4) AS person_w7m2, round(electricity_w7m2,4) AS electricity_w7m2 FROM public.internal_load WHERE internal_load_id={} ORDER BY time_h;""".format(internal_load['id'])
                        print(sql)
                        cur.execute(sql)
                        
                        data="# Time person_w7m2 electricity_w7m2\n"
                        for line in cur.fetchall():
                            data+= str(line['time_h'])+ ' '+ str(line['person_w7m2']) +' '+ str(line['electricity_w7m2']) +"\n"
                        writeToFile(data,dir_internal_loads,internal_loads_file)
                    
                    internal_loads_file=internal_loads_file.replace('/','\\').replace('\\','\\\\')
                    print(internal_loads_file)
                    
                #get model parameter
                sql="""SELECT * FROM "{}".customer_model_parms ORDER BY id;""".format(dictDB['versionName'])
                print(sql)
                cur.execute(sql)
                parms=cur.fetchall()
                print(parms)
                sql="""SELECT * FROM "{}".customers WHERE id={};""".format(dictDB['versionName'],id)
                print(sql)
                cur.execute(sql)
                fields=cur.fetchone()
                print(fields)
                
                for parm in parms:
                    mapping_expression=parm['mapping_expression']
                    for field in fields:
                        if '|'+field+'|'=='|dhw_id|' and mapping_expression=='|dhw_id|':
                            if not dhw_file:
                                if parallize:
                                    dlg.signals.error.emit("No DHW file selected for {} {}!".format(type.capitalize(),id))
                                else:
                                    iface.messageBar().pushMessage("Error", "No DHW file selected for {} {}!".format(type.capitalize(),id), level=Qgis.Critical)
                                return False
                            mapping_expression=dhw_file
                        elif '|'+field+'|'=='|internal_load_id|' and mapping_expression=='|internal_load_id|':
                            if not internal_loads_file:
                                if parallize:
                                    dlg.signals.error.emit("No internal load file selected for {} {}!".format(type.capitalize(),id))
                                else:
                                    iface.messageBar().pushMessage("Error", "No internal load file selected for {} {}!".format(type.capitalize(),id), level=Qgis.Critical)
                                return False
                            mapping_expression=internal_loads_file
                        else:
                            mapping_expression=mapping_expression.replace('|'+field+'|',str(fields[field]))
                    try:
                        mapping_expression=eval(mapping_expression)
                    except:
                        pass
                    print('++++++++'+parm['model_name'])
                    if parm['macro_name'] and parm['parm_name'] and parm['model_name'] and parm['mapping_direction'] in ['<-->','-->']:
                        print(parm['model_name'])
                        try:
                            replaceDict[parm['macro_name']][parm['model_name']][parm['parm_name']]= mapping_expression
                        except:
                            try:
                                replaceDict[parm['macro_name']].update({parm['model_name']:{parm['parm_name']: mapping_expression}})
                            except:
                                replaceDict[parm['macro_name']]={parm['model_name']:{parm['parm_name']: mapping_expression}}
            print(replaceDict)
            CopyAssettypeFiles(source_dir=dir_assettype,source_name=assettype_name,target_dir=dir,target_name=type.capitalize()+'_'+id,update_sensors=True,type=type,assetgroup=str(feature['assetgroup']),assettype=str(feature['assettype']),id=id,cur=cur,dictDB=dictDB,replaceDict=replaceDict,parmRun=parmRun,update_sf=True)
            dir+="\\"+type.capitalize()+"_"+id+"\\"
            f_idc=dir+type.capitalize()+"_"+id+".idc"
            f_idm=dir+type.capitalize()+"_"+id+".idm"
            
            try:
                if invoked:
                    dlg.tableWidget_customer.setItem(idx,1,QTableWidgetItem('True'))
            except:
                pass
            type_old=type
            assetgroup_old=feature['assetgroup']
            assettype_old=feature['assettype']
    else:
        iface.messageBar().pushMessage("Info", "No item selected!", level=Qgis.Info) 

class InvokeFeatures():
    def __init__(self,plugin_dir,dictDB,iface):
        self.iface = iface
        self.plugin_dir=plugin_dir
        self.dictDB=dictDB
        self.conn=dbConnect(self.dictDB,True)
        if self.conn:
            self.cur=self.conn.cursor(cursor_factory = psycopg2.extras.RealDictCursor)
            self.type='customer'
            self.dlg_invokeFeatures=InvokeFeaturesDlg()
            print(self.dlg_invokeFeatures.rbtn_customers)  
            
            self.dlg_invokeFeatures.rbtn_customers.toggled.connect(self.updateFeatureLists)
            self.dlg_invokeFeatures.rbtn_devices.toggled.connect(self.updateFeatureLists)
            self.dlg_invokeFeatures.rbtn_plants.toggled.connect(self.updateFeatureLists)   
            
            self.dlg_invokeFeatures.btn_invokeOne.clicked.connect(self.invokeSelectedFeatures)
            self.dlg_invokeFeatures.btn_invokeAll.clicked.connect(self.invokeAllFeatures)
            self.dlg_invokeFeatures.btn_openInvoked.clicked.connect(lambda: self.openInvokedFeature(self.dlg_invokeFeatures))
            self.dlg_invokeFeatures.btn_simulateInvoked.clicked.connect(lambda: self.simulateInvokedFeatures(self.dlg_invokeFeatures))
            self.dlg_invokeFeatures.btn_showFeatureLoad.clicked.connect(lambda: self.showFeatureLoad(self.dlg_invokeFeatures))
            self.dlg_invokeFeatures.btn_ok.clicked.connect(lambda: closeDialog(self.dlg_invokeFeatures))
            self.loadInvokeFeatureData(self.dlg_invokeFeatures)
            self.dlg_invokeFeatures.show()
            
    def invokeSelectedFeatures(self):
        #invokeOneFeature(self.dlg_invokeFeatures,self.dlg_invokeFeatures.tableWidget_customer.currentRow(),self.plugin_dir,self.cur,self.dictDB,self.type,self.iface,True,parallize=False)
        selected_indexes = self.dlg_invokeFeatures.tableWidget_customer.selectedIndexes()
        rows=[i.row() for i in selected_indexes]
        print(rows)
        self.startInvokeFeaturesWorker(rows)
        
    def updateFeatureLists(self,s):
        """Update the list of customers, devices or plants based on the radio button """
        print('Update customers/devices/plants list')
        print(s)
        if self.dlg_invokeFeatures.sender()==self.dlg_invokeFeatures.rbtn_customers:
            self.type='customer'
        elif self.dlg_invokeFeatures.sender()==self.dlg_invokeFeatures.rbtn_devices:
            self.type='device'
        elif self.dlg_invokeFeatures.sender()==self.dlg_invokeFeatures.rbtn_plants:
            self.type='energy_plant'
        sql='SELECT array_agg(id::TEXT ORDER BY id) AS ids FROM "{}".{}s;'.format(self.dictDB['versionName'],self.type)
        print(sql)
        self.cur.execute(sql)
        ids=self.cur.fetchall()[0]['ids']
        print(ids)
        self.dlg_invokeFeatures.tableWidget_customer.setRowCount(0)
        i=0
        if ids:
            for id in ids:
                print(id)
                self.dlg_invokeFeatures.tableWidget_customer.insertRow(i)
                self.dlg_invokeFeatures.tableWidget_customer.setItem(i,0,QTableWidgetItem(id))
                if os.path.exists(self.plugin_dir+"\\network_models\\{}\\{}\\invoked_{}s\\{}_{}.idm".format(self.dictDB['projectName'],self.dictDB['versionName'],self.type,self.type.capitalize(),id)): 
                    exists=True
                else:
                    exists=False
                self.dlg_invokeFeatures.tableWidget_customer.setItem(i,1,QTableWidgetItem(str(exists)))
                i+=1        
            
    def loadInvokeFeatureData(self,dlg):
        """Collect all feature ids and check if they are already invoked"""
        sql="""SELECT id FROM "{}".{}s ORDER BY id;""".format(self.dictDB['versionName'],self.type)
        print(sql)
        self.cur.execute(sql)
        i=0
        for id in self.cur.fetchall():
            print(str(id['id']))
            dlg.tableWidget_customer.insertRow(i)
            dlg.tableWidget_customer.setItem(i,0,QTableWidgetItem(str(id['id'])))
            if os.path.exists(self.plugin_dir+"\\network_models\\{}\\{}\\invoked_{}s\\{}_{}.idm".format(self.dictDB['projectName'],self.dictDB['versionName'],self.type,self.type.capitalize(),str(id['id']))): 
                exists=True
            else:
                exists=False
            dlg.tableWidget_customer.setItem(i,1,QTableWidgetItem(str(exists)))
            i+=1
                  
    def openInvokedFeature(self,dlg):
        """Open the invoked feature in IDA. Changes can be saved"""  
        idx=dlg.tableWidget_customer.currentRow()
        print(idx)
        if idx!=-1:
            id=dlg.tableWidget_customer.item(idx,0).text()
            file_path=self.plugin_dir+"\\network_models\\{}\\{}\\invoked_{}s\\{}_{}.idm".format(self.dictDB['projectName'],self.dictDB['versionName'],self.type,self.type.capitalize(),id)  
            if os.path.exists(file_path):
                print(file_path)
                self.worker_openInvoked = WorkerOpenAPI(file_path,self.plugin_dir)
                self.threadpool_openInvoked = QThreadPool()
                self.threadpool_openInvoked.start(self.worker_openInvoked) 
                self.worker_openInvoked.signals.error.connect(show_error_message)
                self.worker_openInvoked.signals.progress.connect(self.dlg_invokeFeatures.update_progress)  

                print('finished open feature')
                
            else:
                self.iface.messageBar().pushMessage("Info", "Feature not yet invoked!", level=Qgis.Info)
        else:
            self.iface.messageBar().pushMessage("Info", "No item selected!", level=Qgis.Info)

    def simulateInvokedFeatures(self,dlg):
        """Simulate the invoked features in IDA."""  
        print('Simulate invoked features')
        ids=[dlg.tableWidget_customer.item(idx,0).text() for idx in range(0,dlg.tableWidget_customer.rowCount())]
        print(ids)
        if ids:
            file_pathes=[self.plugin_dir.replace('/','\\')+"\\network_models\\{}\\{}\\invoked_{}s\\{}_{}.idm".format(self.dictDB['projectName'],self.dictDB['versionName'],self.type,self.type.capitalize(),i)  for i in ids]
            print(file_pathes)

            self.worker_simInvoked = WorkerSimulateFilesAPI(file_pathes,self.plugin_dir)
            self.threadpool_simInvoked = QThreadPool()
            self.threadpool_simInvoked.start(self.worker_simInvoked) 
            self.worker_simInvoked.signals.error.connect(self.dlg_invokeFeatures.show_error_message)
            self.worker_simInvoked.signals.progress.connect(self.dlg_invokeFeatures.update_progress)         
        else:
            self.iface.messageBar().pushMessage("Info", "No item selected!", level=Qgis.Info)
        print('simulation finished')

    def showFeatureLoad(self,dlg):
        """Show feature load"""  
        idxs=[index.row() for index in dlg.tableWidget_customer.selectedIndexes()]
        print(idxs)
        count=0
        if idxs:
            dlg.type=self.type
            dlg.fig, dlg.ax = plt.subplots(layout='constrained')
            dlg.fig2, dlg.ax2 = plt.subplots(layout='constrained')
            self.worker_plotLoad = WorkerPlotInvokedFeatureLoad(plugin_dir=self.plugin_dir,rows=idxs,type=self.type,dlg=dlg,dictDB=self.dictDB)
            self.threadpool_plotLoad = QThreadPool()
            self.threadpool_plotLoad.start(self.worker_plotLoad) 
            self.worker_plotLoad.signals.error.connect(dlg.show_error_message)
            self.worker_plotLoad.signals.progress.connect(dlg.update_progress)        
            self.worker_plotLoad.signals.dataProcessed.connect(dlg.plot_data) #matplotlib is not thread save; data is plotted in main thread instead
            self.worker_plotLoad.signals.plot_total.connect(dlg.plot_total_data)
            self.worker_plotLoad.signals.plot.connect(dlg.show_plots)
            
        else:
            self.iface.messageBar().pushMessage("Info", "No feature selected or not invoked!", level=Qgis.Info)
                       
    def getSensorComp(self,sensor_comp_idm,sensor_comp_idc,function,sensor_id,n_in,conns,i):
        if function in ['Max','Min']:
            if function=='Max':
                selector='1'
            else:
                selector='0'
            sensor_comp_idm+="""((:EO :N "Sensor_{}" :T MINMAXD)
 (:PAR :N N_IN :V {})
 (:PAR :N SELECTOR :V {})
 (:VAR :N INSIGNAL :B #S(MS-SPARSE DEFAULT-VALUE NIL DIMENSION 1 VALUE ({}))))\n""".format(sensor_id,n_in,selector,conns)
            sensor_comp_idc+="""\n(EQUATION-FRAME :AT ((41 {})) :R (16 16) :ICON "lib:minmaxd.ids" :SLOT ("Sensor_{}") :NAME "Sensor_{}" :DATA :EO) """.format(str(50+35*i),sensor_id,sensor_id)
        elif function in ['Add','Average']:
            if function=='Add':
                coeff=' '.join(['1' for i in range(n_in)])
            elif function=='Average':
                coeff=' '.join([str(1/n_in) for i in range(n_in)])
            sensor_comp_idm+="""\n((:EO :N "Sensor_{}" :T ADDER)
 (:PAR :N N_IN :V {})
 (:PAR :N COEFF :DIM ({}) :V #({}))
 (:VAR :N INSIGNAL :B #S(MS-SPARSE DEFAULT-VALUE NIL DIMENSION 1 VALUE ({})))) """.format(sensor_id,n_in,n_in,coeff,conns)
            sensor_comp_idc+="""\n(EQUATION-FRAME :AT ((41 {})) :R (16 16) :ICON "lib:adder.ids" :SLOT ("Sensor_{}") :NAME "Sensor_{}" :PADDING 3 :DATA :EO) """.format(str(50+35*i),sensor_id,sensor_id)
        return sensor_comp_idm,sensor_comp_idc
            
    def invokeAllFeatures(self):
        """Invoke all features using a worker and calling invokeOneFeatures in a loop"""
        rows=[i for i in range(self.dlg_invokeFeatures.tableWidget_customer.rowCount())]
        self.startInvokeFeaturesWorker(rows)
        
    def startInvokeFeaturesWorker(self,rows):
        self.dictDB=getDBConnectionData(self.plugin_dir)
        self.worker_invokeFeature = WorkerInvokeFeatures(dictDB=self.dictDB,plugin_dir=self.plugin_dir,dlg=self.dlg_invokeFeatures,type=self.type,rows=rows)
        self.threadpool_invokeFeature = QThreadPool()
        self.threadpool_invokeFeature.start(self.worker_invokeFeature) 
        self.worker_invokeFeature.signals.error.connect(show_error_message)
        self.worker_invokeFeature.signals.progress.connect(self.dlg_invokeFeatures.update_progress)      

               
class CopyAssettypeFiles:
    """ Copy the files and rename it"""
    def __init__(self,source_dir='',source_name='',target_dir='',target_name='',update_sensors=False,type='',assetgroup='',assettype='',id='',cur='',dictDB='',replaceDict='',parmRun='',update_sf=False):
        print('++++++++++++++++++++++++++CopyAssettypeFiles++++++++++++++')
        print(parmRun)
        self.dictDB=dictDB
        if update_sensors:
            type=getTypeIdByName(type)
            sql="""SELECT s.sensor_id, s_ids.feature_id 
        FROM {}.sensor_source s, {}.source_assetgroups s_ag, {}.source_assettype s_at, {}.source_ids s_ids
        WHERE s.sensor_id=s_ag.source_id AND s.sensor_id=s_at.source_id AND s_ag.assetgroup={} AND s_at.assettype={} AND s.measure=5 AND s.type={} AND
            s.sensor_id=s_ids.source_id AND s_at.active=true AND s_ag.active=true AND s_ids.active=false AND s_ids.feature_id={};""".format(
                self.dictDB['versionName'],self.dictDB['versionName'],self.dictDB['versionName'],self.dictDB['versionName'],assetgroup,assettype,type,str(id))
            print(sql)
            cur.execute(sql)
            remove_sensor_source_ids=cur.fetchall()
            print(remove_sensor_source_ids)
            
            sql="""SELECT t.sensor_id, t_ids.feature_id 
        FROM {}.sensor_target t,{}.target_ids t_ids
        WHERE t.type={} AND t.sensor_id=t_ids.target_id AND t_ids.active=false AND t_ids.feature_id={};""".format(
                self.dictDB['versionName'],self.dictDB['versionName'],type,str(id))
            print(sql)
            cur.execute(sql)
            remove_sensor_target_ids=cur.fetchall()
            print(remove_sensor_target_ids)
        
        print(source_name)
        print(target_name)
        #project idm
        filedata=readAndReplaceFileToList(source_dir+'\\'+source_name+'.idm',{'"'+source_name+'"': '"'+target_name+'"'})
        
        if replaceDict:
            print({j : replaceDict[i][j] for i in replaceDict if i in [':BUILDING',':SYSTEM'] for j in replaceDict[i]})
            filedata=replaceKeywordsInFiledata(filedata,{j : replaceDict[i][j] for i in replaceDict if i in [':BUILDING',':SYSTEM'] for j in replaceDict[i]})
        if update_sensors:
            filedata=delSensorConnection(filedata,remove_sensor_source_ids,'Source')
            filedata=delSensorConnection(filedata,remove_sensor_target_ids,'Target')
        writeToFileFromList(filedata,target_dir,target_dir+'\\'+target_name+'.idm')     
        
        #project idc
        filedata=readAndReplaceFileToList(source_dir+'\\'+source_name+'.idc',{'"'+source_name+'"': '"'+target_name+'"'})           
        if update_sensors:
            filedata=delSensorConnection(filedata,remove_sensor_source_ids,'Source')
            filedata=delSensorConnection(filedata,remove_sensor_target_ids,'Target')
        writeToFileFromList(filedata,target_dir,target_dir+'\\'+target_name+'.idc')     
      
        createDir(target_dir,target_name)
        dir_macro=target_dir+'\\'+target_name
        print(source_dir+'\\'+source_name+'\\'+source_name+'.idm')
        
        #feature
        #make subset of replaceDict based on macro name
        pList=propertyListCompsIDM(getIDAListComponents(readFileToString(source_dir+'\\'+source_name+'\\'+source_name+'.idm')))
        if replaceDict:
            print(replaceDict)
            pList=replaceKeywordsInPList(pList,{j : replaceDict[i][j] for i in replaceDict if i in [source_name, ':FEATURE'] for j in replaceDict[i]})
        if update_sf:
            print('**************************sf********************')        
            sf=getSFList(pList,[])

            if sf:
                sql='\n'.join(["""INSERT INTO {}.invoked_sf (sf,vars)
    SELECT '{}', ARRAY[{}] WHERE NOT EXISTS (
        SELECT 1 FROM {}.invoked_sf WHERE sf = '{}'
    );""".format(self.dictDB['versionName'],i[0][':SF'],','.join(["'"+getSFLinkRefs(i)[j]+"'" for j in getSFLinkRefs(i)]),self.dictDB['versionName'],i[0][':SF'])  for i in sf])
                print(sql)
                cur.execute(sql)
            sql="SELECT id,sf FROM {}.invoked_sf;".format(self.dictDB['versionName'])
            cur.execute(sql)
            sf_ids=cur.fetchall()
            pList=delSFAndConnsAddLinks(pList,sf,sf_ids)
        else:
            sf=[]

        if update_sensors:
            pList=delSensorConnectionPList(pList,remove_sensor_source_ids,'Source')
            pList=delSensorConnectionPList(pList,remove_sensor_target_ids,'Target')
        writePropertyListIDMToFile(pList,dir_macro,dir_macro+'\\'+target_name+'.idm')

        filedata=readFileToList(source_dir+'\\'+source_name+'\\'+source_name+'.idc')
        if update_sensors:
            filedata=delSensorConnection(filedata,remove_sensor_source_ids,'Source')
            filedata=delSensorConnection(filedata,remove_sensor_target_ids,'Target')
        if update_sf:
            sf_names=[i[0][':N'] for i in sf]
            print(sf_names)
            filedata=[i for i in filedata if not [True for j in sf_names if j in i]]
        writeToFileFromList(filedata,dir_macro,dir_macro+'\\'+target_name+'.idc')   
        
        #sf-macro.idm
        filedata=[""";IDA 5.09001 Data UTF-8
(DOCUMENT-HEADER :TYPE ICE-MACRO :D "ICE macro" :ETM 3857463573 :APP (ICE :VER 5.09001)) """]
        for i in sf:
            i[0][':N']='"SOURCE-FILE-{}"'.format([j['id'] for j in sf_ids if i[0][':SF']==j['sf']][0])
            filedata+=["""\n{}""".format(pListToCompString(i,0))]
        writeToFileFromList(filedata,dir_macro,dir_macro+'\\sf-macro.idm')

        #sf-macro.idc
        filedata=[""";IDA 5.09001 Data UTF-8
(DOCUMENT-HEADER :TYPE SCHEMA :PAGE-WIDTH 178 :PAGE-HEIGHT 97) 
(SELF-FRAME :AT ((352 190)) :R (342 176) :SLOT (:SELF) :DATA MACRO-OBJECT) """]
        filedata+=["""\n(EQUATION-FRAME :AT ((50 {})) :R (20 20) :ICON "sys:source-file.ids" :SLOT ("SOURCE-FILE-{}") :NAME "SOURCE-FILE-{}" :DATA SOURCE-FILE :D "SOURCE-FILE")""".format(30+counter*48,i['id'],i['id']) for counter,i in enumerate([j for i in sf for j in sf_ids if i[0][':SF']==j['sf']],1)]
        writeToFileFromList(filedata,dir_macro,dir_macro+'\\sf-macro.idc')
        
        #sensor-macro.idm
        filedata=readAndReplaceFileToList(source_dir+'\\'+source_name+'\\Sensor-macro.idm',{'"'+source_name+'"': '"'+target_name+'"'}) 
        filedata=replaceKeywordsInFiledata(filedata,{j : replaceDict[i][j] for i in replaceDict if 'Sensor-macro'==i for j in replaceDict[i]})
        writeToFileFromList(filedata,dir_macro,dir_macro+'\\Sensor-macro.idm')   
                
        #check if folder contains macros
        print('+++check if folder contains macros+++')
        print(source_dir+'\\'+source_name)
        if os.path.exists(source_dir+'\\'+source_name):
            for root, dirs, files in os.walk(source_dir+'\\'+source_name):
                for file in files:
                    if (file.endswith('.idm') or file.endswith('.idc')) and file not in ['sensor-macro.idm',source_name+'.idm',source_name+'.idc','sf-macro.idm','sf-macro.idc']:
                        print('---------copy file---------')
                        print(file)
                        print(os.path.join(root, file))
                        #subfolder=os.path.dirname(os.path.join(root, file)).replace('/','\\').split(source_name+'\\'+source_name)[1]
                        #print(path)
                        #print(os.path.splitext(os.path.basename(file))[0])
                        path_target=dir_macro+os.path.join(root, file).split(source_dir+'\\'+source_name)[1].split(file)[0]
                        print(path_target)
                        print({j : replaceDict[i][j] for i in replaceDict if file.lower().split('.')[0]==i.lower() for j in replaceDict[i]})
                        copyFileReplaceStr(os.path.join(root, file),path_target,path_target+file,[source_name],[target_name],{j : replaceDict[i][j] for i in replaceDict if file.lower().split('.')[0]==i.lower() for j in replaceDict[i]})

                        #copyFile(os.path.join(root, file),path_target,path_target+'\\'+file)
                        
                for dir in dirs: 
                    print('+++create subdir++++')
                    print(dir_macro+os.path.join(root, dir).split(source_dir+'\\'+source_name)[1])
                    createSubDir(dir_macro+os.path.join(root, dir).split(source_dir+'\\'+source_name)[1])
                                
        