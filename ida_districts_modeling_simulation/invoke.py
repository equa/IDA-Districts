from plugins.utility_functions.db import *
from plugins.utility_functions.files import *
from plugins.utility_functions.macros import *
from plugins.utility_functions.dialog import *
from plugins.utility_functions.sensor_signals import AssettypeSensorSignals


import psycopg2
from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT
import psycopg2.extras
from .ida_districts_modeling_simulation_dialog import InvokeFeaturesFromTemplate
from .calibrate_customers import *
from plugins.utility_functions.sensor_signals import *
from qgis.PyQt.QtWidgets import QTableWidgetItem,QTableWidget, QTabWidget

from qgis.PyQt.QtCore import QSettings, QTranslator, QCoreApplication,Qt
from plugins.utility_functions.util import *
from plugins.utility_functions.layer_visualization import *
from plugins.utility_functions.workerOpenAPI import WorkerOpenAPI, WorkerRunAutoMooAPI, WorkerSimulateAPI
from qgis.utils import iface
from multiprocessing import Process
from qgis.core import  QgsCredentials,QgsDataSourceUri, QgsExpression, QgsOptionalExpression,QgsAttributeEditorField,QgsAttributeEditorContainer, QgsEditFormConfig, QgsProject, QgsSvgMarkerSymbolLayer, QgsEditorWidgetSetup, QgsVectorLayer, QgsSymbol, QgsRendererCategory, QgsCategorizedSymbolRenderer
import math

import numpy as np
import matplotlib.pyplot as plt
import re

import datetime
import matplotlib.dates as mdates
from matplotlib.ticker import AutoMinorLocator
from plugins.utility_functions.ida_components import *

   
def loadCustomerParm(dlg,cur,dictDB):
    sql="""SELECT * FROM {}.customer_model_parms ORDER BY id;""".format(dictDB['versionName'])
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
        
def loadLayerFieldsToList(list,dhc_layer_name):
    layer=QgsProject.instance().mapLayersByName(dhc_layer_name)
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
        
        sql="""TRUNCATE {}.customer_model_parms CASCADE;\n""".format(dictDB['versionName'])
        columns='id,mapping_expression,parm_name,model_name,macro_name,mapping_direction'
        table=dlg.tableWidget_parameters
        
        i=0
        for row in range(table.rowCount()):
            #write data to DB table customer_model_parms
            values=str(row)+", '"+(table.item(row, 0).text().replace("'","''") if table.item(row, 0) else '') +"', '"+(table.item(row, 2).text() if table.item(row, 2) else '')+"', '"+(table.item(row, 3).text() if table.item(row, 3) else '')+"', '"+(table.item(row, 4).text() if table.item(row, 4) else '')+"', '"+table.cellWidget(row, 1).currentText()+"'"
            sql+="""INSERT INTO {}.customer_model_parms ({}) VALUES ({});\n""".format(dictDB['versionName'],columns,values)
            
        print(sql)
        cur.execute(sql)
 
        dlg.close()
    
def setupCustomerVersionForm(cur,dictDB,plugin_dir):  
    """ setup form for customer layer"""
    vlayerName='dhc_customers'
    removeLayer(vlayerName)
    loadFeatureLayer(dictDB['versionName'],dictDB,plugin_dir,vlayerName,cur)
    
    vlayer=QgsProject.instance().mapLayersByName(vlayerName)[0] 
    fields=vlayer.fields()
    fc = vlayer.editFormConfig()
    fc.clearTabs()
    fc.setLayout(QgsEditFormConfig.TabLayout)
    modelParm=getALiasNameCustParm(cur,dictDB)
    
    attrNamesTabs= [['id','assetgroup','assettype','network'],
                    ['heat_e_kwh','heat_p_kw','tsup_h_deg','cool_e_kwh','cool_p_kw','tsup_c_deg','asl_m'],
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
        
def invokeOneFeature(dlg,idx,plugin_dir,cur,dictDB,type,iface,invoked,parmRun=False,saveParmRunResults=False):
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
            FROM {}.dhc_{}s c,{}_assettypes at 
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
                sql="""SELECT dhw.id, dhw.description FROM {}.dhc_customers c, public.dhw_timeseries dhw WHERE dhw.id=c.dhw_id AND c.id={};""".format(dictDB['versionName'],id)
                cur.execute(sql)
                dhw=cur.fetchone()
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
                    #replaceDict["$SOURCE-FILE_DHW$"]=dhw_file
                    
                #internal loads
                sql="""SELECT l.id, l.description FROM {}.dhc_customers c, public.internal_loads_profiles l WHERE l.id=c.internal_load_id AND c.id={};""".format(dictDB['versionName'],id)
                cur.execute(sql)
                internal_load=cur.fetchone()
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
                    
                #get model parameter
                sql="""SELECT * FROM {}.customer_model_parms ORDER BY id;""".format(dictDB['versionName'])
                print(sql)
                cur.execute(sql)
                parms=cur.fetchall()
                print(parms)
                sql="""SELECT * FROM {}.dhc_customers WHERE id={};""".format(dictDB['versionName'],id)
                print(sql)
                cur.execute(sql)
                fields=cur.fetchone()
                print(fields)
                
                for parm in parms:
                    mapping_expression=parm['mapping_expression']
                    for field in fields:
                        if '|'+field+'|'=='|dhw_id|' and mapping_expression=='|dhw_id|':
                            mapping_expression=dhw_file
                        elif '|'+field+'|'=='|internal_load_id|' and mapping_expression=='|internal_load_id|':
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
                            replaceDict[parm['macro_name']][parm['model_name']].append({parm['parm_name']: mapping_expression})
                        except:
                            try:
                                replaceDict[parm['macro_name']].update({parm['model_name']:[{parm['parm_name']: mapping_expression}]})
                            except:
                                replaceDict[parm['macro_name']]={parm['model_name']:[{parm['parm_name']: mapping_expression}]}
            print(replaceDict)
            CopyAssettypeFiles(dir_assettype,assettype_name,dir,type.capitalize()+'_'+id,True,type,str(feature['assetgroup']),str(feature['assettype']),id,cur,dictDB,replaceDict,parmRun=parmRun)
            dir+="\\"+type.capitalize()+"_"+id+"\\"
            f_idc=dir+type.capitalize()+"_"+id+".idc"
            f_idm=dir+type.capitalize()+"_"+id+".idm"
            
            if invoked:
                dlg.tableWidget_customer.setItem(idx,1,QTableWidgetItem('True'))
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
            self.dlg_invokeFeatures=InvokeFeaturesFromTemplate()
            print(self.dlg_invokeFeatures.rbtn_customers)  
            
            self.dlg_invokeFeatures.rbtn_customers.toggled.connect(self.updateFeatureLists)
            self.dlg_invokeFeatures.rbtn_devices.toggled.connect(self.updateFeatureLists)
            self.dlg_invokeFeatures.rbtn_plants.toggled.connect(self.updateFeatureLists)   
            
            self.dlg_invokeFeatures.btn_invokeOne.clicked.connect(lambda: self.invokeOneFeature_())
            self.dlg_invokeFeatures.btn_invokeAll.clicked.connect(lambda: self.invokeAllFeatures(self.dlg_invokeFeatures))
            self.dlg_invokeFeatures.btn_openInvoked.clicked.connect(lambda: self.openInvokedFeature(self.dlg_invokeFeatures))
            self.dlg_invokeFeatures.btn_simulateInvoked.clicked.connect(lambda: self.simulateInvokedFeatures(self.dlg_invokeFeatures))
            self.dlg_invokeFeatures.btn_showFeatureLoad.clicked.connect(lambda: self.showFeatureLoad(self.dlg_invokeFeatures))
            self.dlg_invokeFeatures.btn_ok.clicked.connect(lambda: closeDialog(self.dlg_invokeFeatures))
            self.loadInvokeFeatureData(self.dlg_invokeFeatures)
            self.dlg_invokeFeatures.show()
            
    def invokeOneFeature_(self):
        requestedOutputs=loadRequestedOutputs(self.plugin_dir,self.dictDB)
        invokedOutputs=loadInvokedOutputs(self.plugin_dir,self.dictDB)
        if self.type=='energy_plant':
            invokedOutputs['dhc_'+self.type+'s'][int(self.dlg_invokeFeatures.tableWidget_customer.item(self.dlg_invokeFeatures.tableWidget_customer.currentRow(),0).text())]={'power_ep': True if requestedOutputs['power_ep'] else False, 'temp_ep': True if requestedOutputs['temp_ep'] else False, 'p_ep': True if requestedOutputs['p_ep'] else False, 'mdot_ep': True if requestedOutputs['mdot_ep'] else False}
        elif self.type=='customer':
            invokedOutputs['dhc_'+self.type+'s'][int(self.dlg_invokeFeatures.tableWidget_customer.item(self.dlg_invokeFeatures.tableWidget_customer.currentRow(),0).text())]={'power_c': True if requestedOutputs['power_c'] else False, 'temp_c': True if requestedOutputs['temp_c'] else False, 'p_c': True if requestedOutputs['p_c'] else False, 'mdot_c': True if requestedOutputs['mdot_c'] else False, 'heatbalance_c': True if requestedOutputs['heatbalance_c'] else False, 'troom_c': True if requestedOutputs['troom_c'] else False}
        elif self.type=='device':
            pass #todo
        invokeOneFeature(self.dlg_invokeFeatures,self.dlg_invokeFeatures.tableWidget_customer.currentRow(),self.plugin_dir,self.cur,self.dictDB,self.type,self.iface,True)
        
        writeInvokedOutputs(self.plugin_dir,self.dictDB,invokedOutputs)
        
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
        sql="SELECT array_agg(id::TEXT ORDER BY id) AS ids FROM {}.dhc_{}s;".format(self.dictDB['versionName'],self.type)
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
        sql="""SELECT id FROM {}.dhc_{}s ORDER BY id;""".format(self.dictDB['versionName'],self.type)
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
        id=dlg.tableWidget_customer.item(idx,0).text()
        file_path=self.plugin_dir+"\\network_models\\{}\\{}\\invoked_{}s\\{}_{}.idm".format(self.dictDB['projectName'],self.dictDB['versionName'],self.type,self.type.capitalize(),id)  
        if os.path.exists(file_path):
            print(file_path)
            process = Process(target=WorkerOpenAPI(file_path,self.plugin_dir))


            print('finished open assettype')
        else:
            self.iface.messageBar().pushMessage("Info", "No feature selected or not invoked!", level=Qgis.Info)

    def simulateInvokedFeatures(self,dlg):
        """Simulate the invoked features in IDA."""  
        print('Simulate invoked features')
        ids=[dlg.tableWidget_customer.item(idx,0).text() for idx in range(0,dlg.tableWidget_customer.rowCount())]
        print(ids)
        for id in ids:
            file_path=self.plugin_dir+"\\network_models\\{}\\{}\\invoked_{}s\\{}_{}.idm".format(self.dictDB['projectName'],self.dictDB['versionName'],self.type,self.type.capitalize(),id)  
            if os.path.exists(file_path):
                print(file_path)
                process = Process(target=WorkerSimulateAPI(file_path,self.plugin_dir))
            else:
                self.iface.messageBar().pushMessage("Info", "Sim model does not exist!", level=Qgis.Info)
        #os.system("taskkill /f /im ida-ice.exe")

        print('simulation finished')

    def showFeatureLoad(self,dlg):
        """Show feature load"""  
        idxs=[index.row() for index in dlg.tableWidget_customer.selectedIndexes()]
        print(idxs)
        count=0
        if idxs:
            fig, ax = plt.subplots(layout='constrained')
            fig2, ax2 = plt.subplots(layout='constrained')
            
            for idx in idxs:
                id=dlg.tableWidget_customer.item(idx,0).text()
                file_path=self.plugin_dir+"\\network_models\\{}\\{}\\invoked_{}s\\{}_{}\\{}_{}\\Hx.prn".format(self.dictDB['projectName'],self.dictDB['versionName'],self.type,self.type.capitalize(),id,self.type,id)  
                print(file_path)
                if os.path.exists(file_path):
                    legend='Customer_'+id

                    print(file_path)
                    filedata=readFileToList(file_path)

                    #print(filedata)
                    i=0
                    time=[]
                    power=[]
                    energy=[]
                    for line in filedata:
                        if i>0:
                            data=line.strip().split()
                            power.append([float(data[0]),float(data[3])])
                            energy.append([float(data[0]),float(data[4])])
                        i+=1    
                    
                    power=np.array(power)  
                    energy=np.array(energy)    
                    #print(power)

                    time=np.arange(0,8760,0.1)
                    #print(time)

                    #linear interpolation
                    valuesPowerInt = np.interp(time, power[:,0], power[:,1])
                    valuesEnergyInt = np.interp(time, power[:,0], energy[:,1])
                    
                    if count==0:
                        power_sum=valuesPowerInt
                        energy_sum=valuesEnergyInt
                    else:
                        power_sum=np.add(power_sum,valuesPowerInt)
                        energy_sum=np.add(energy_sum,valuesEnergyInt)

                    #plotting
                    ax.plot(time, valuesPowerInt,label='Customer ID='+str(id))
                    ax2.plot(time, valuesEnergyInt,label='Customer ID='+str(id))

                    count+=1
                    
            ax.set_title('Load profiles customers')
            ax2.set_title('Cumulated energy customers')
            ax.set_xlabel('Time, h')
            ax2.set_xlabel('Time, h')
            ax.set_ylabel('Power, W')
            ax2.set_ylabel('Energy, kWh')

            plt.xticks([0,744,1416,2160,2880,3624,4344,5088,5832,6552,7296,8016,8760])
            fig.legend()
            fig2.legend()
            fig.show()            
            fig2.show()            
            if count>1:
                fig1, ax1 = plt.subplots(layout='constrained')
                ax1.plot(time, power_sum, label='Total power, W')
                ax1.plot(time, energy_sum, label='Total energy, kWh')
                ax1.set_xlabel('Time, h')
                #ax1.set_ylabel('Power, W')
                ax1.set_title('Total load profiles')
                #ax1.set_title('Total load profiles Fohrbach')
                plt.xticks([0,744,1416,2160,2880,3624,4344,5088,5832,6552,7296,8016,8760])
                plt.legend()
                fig1.show()
                
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
            
    def invokeAllFeatures(self,dlg):
        """Invoke all features by calling invokeOneFeatures in a loop"""
        requestedOutputs=loadRequestedOutputs(self.plugin_dir,self.dictDB)
        invokedOutputs=loadInvokedOutputs(self.plugin_dir,self.dictDB)
        
        for idx in range(dlg.tableWidget_customer.rowCount()):
            print(idx)
            invokeOneFeature(dlg,idx,self.plugin_dir,self.cur,self.dictDB,self.type,self.iface,True)
            if self.type=='energy_plant':
                invokedOutputs['dhc_'+self.type+'s'][int(self.dlg_invokeFeatures.tableWidget_customer.item(idx,0).text())]={'power_ep': True if requestedOutputs['power_ep'] else False, 'temp_ep': True if requestedOutputs['temp_ep'] else False, 'p_ep': True if requestedOutputs['p_ep'] else False, 'mdot_ep': True if requestedOutputs['mdot_ep'] else False}
            elif self.type=='customer':
                invokedOutputs['dhc_'+self.type+'s'][int(self.dlg_invokeFeatures.tableWidget_customer.item(idx,0).text())]={'power_c': True if requestedOutputs['power_c'] else False, 'temp_c': True if requestedOutputs['temp_c'] else False, 'p_c': True if requestedOutputs['p_c'] else False, 'mdot_c': True if requestedOutputs['mdot_c'] else False, 'heatbalance_c': True if requestedOutputs['heatbalance_c'] else False, 'troom_c': True if requestedOutputs['troom_c'] else False}

        writeInvokedOutputs(self.plugin_dir,self.dictDB,invokedOutputs)

               
class CopyAssettypeFiles:
    """ Copy the files and rename it"""
    def __init__(self,source_dir,source_name,target_dir,target_name,update_sensors=False,type='',assetgroup='',assettype='',id='',cur='',dictDB='',replaceDict='',parmRun=''):
        print('copy file')
        print(parmRun)
        if update_sensors:
            self.dictDB=dictDB
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
        print(replaceDict)
        print({j : replaceDict[i][j] for i in replaceDict if source_name==i for j in replaceDict[i]})
        filedata=readFileToList(source_dir+'\\'+source_name+'\\'+source_name+'.idm')
        filedata=replaceKeywordsInFiledata(filedata,{j : replaceDict[i][j] for i in replaceDict if i in [source_name, ':FEATURE'] for j in replaceDict[i]})
        if update_sensors:
            filedata=delSensorConnection(filedata,remove_sensor_source_ids,'Source')
            filedata=delSensorConnection(filedata,remove_sensor_target_ids,'Target')
        writeToFileFromList(filedata,dir_macro,dir_macro+'\\'+target_name+'.idm')     

        filedata=readFileToList(source_dir+'\\'+source_name+'\\'+source_name+'.idc')
        if update_sensors:
            filedata=delSensorConnection(filedata,remove_sensor_source_ids,'Source')
            filedata=delSensorConnection(filedata,remove_sensor_target_ids,'Target')
        writeToFileFromList(filedata,dir_macro,dir_macro+'\\'+target_name+'.idc')   
        
        #sensor-macro.idm
        filedata=[]
        with open(source_dir+'\\'+source_name+'\\Sensor-macro.idm', "r") as myfile:
            for line in myfile:
                line=line.replace('"'+source_name+'"','"'+target_name+'"')                
                filedata.append(line)  
        filedata=replaceKeywordsInFiledata(filedata,{j : replaceDict[i][j] for i in replaceDict if 'Sensor-macro'==i for j in replaceDict[i]})
        writeToFileFromList(filedata,dir_macro,dir_macro+'\\Sensor-macro.idm')   
                
        #check if folder contains macros
        print('+++check if folder contains macros+++')
        print(source_dir+'\\'+source_name)
        if os.path.exists(source_dir+'\\'+source_name):
            for root, dirs, files in os.walk(source_dir+'\\'+source_name):
                for file in files:
                    if (file.endswith('.idm') or file.endswith('.idc')) and file not in ['sensor-macro.idm',source_name+'.idm',source_name+'.idc',]:
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
                                
        