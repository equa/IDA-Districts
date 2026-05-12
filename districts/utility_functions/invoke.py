from qgis.PyQt.QtWidgets import QTableWidgetItem,QTableWidget, QTabWidget
from qgis.PyQt.QtCore import QSettings, QTranslator, QCoreApplication,Qt,QThreadPool
from qgis.utils import iface
from qgis.core import  QgsCredentials,QgsDataSourceUri, QgsExpression, QgsOptionalExpression,QgsAttributeEditorField,QgsAttributeEditorContainer, QgsEditFormConfig, QgsProject, QgsSvgMarkerSymbolLayer, QgsEditorWidgetSetup, QgsVectorLayer, QgsSymbol, QgsRendererCategory, QgsCategorizedSymbolRenderer

from .db import *
from .files import *
from .topology import *
from .macros import *
from .dialog import *
from .ida_components import *  
from .sensor_signals import *
from .util import *
from .layer_visualization import *
from .workers import *
from ..ida_mosim_dialog import InvokeFeaturesDlg
from ..calibrate_customers import *

import psycopg2
from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT
import psycopg2.extras
import math
import copy
import numpy as np
import matplotlib.pyplot as plt
import re
import ast
import datetime
import matplotlib.dates as mdates
from matplotlib.ticker import AutoMinorLocator

class WorkerInvokeFeatures(QRunnable):
    """Worker thread
    Inherits from QRunnable to handle worker thread setup, signals and wrap-up."""
    def __init__(self,*args,**kwargs):
        super().__init__()
        self.args=args
        #print(args)
        self.signals=APISignals()
        self.config=kwargs['config']
        self.dlg=kwargs['dlg']
        self.type=kwargs['type']
        self.conn=""
        self.cur=""
        self.plugin_dir=kwargs['plugin_dir']
        self.conn = dbConnect(self.config,True)
        self.rows=kwargs['rows']
        if self.conn:
            self.cur=self.conn.cursor(cursor_factory = psycopg2.extras.RealDictCursor)
            
    @pyqtSlot()
    def run(self):
        #print('Generate network topology')
        self.progress_value=1
        self.signals.progress.emit(self.progress_value)
        
        requestedOutputs=loadRequestedOutputs(self.plugin_dir,self.config)
        invokedOutputs=loadInvokedOutputs(self.config)
        sql="""DELETE FROM "{}".invoked_sf WHERE type='{}';""".format(self.config['versionName'],self.type[:-1]) # nosec B608
        self.cur.execute(sql)
        
        rows_count=len(self.rows)
        for idx in self.rows:
            #print(idx)
            invokeOneFeature(self.dlg,idx,self.cur,self.config,self.type,True,parallize=True,signals=self.signals)
            if self.type=='energy_plant':
                invokedOutputs[self.type+'s'][int(self.dlg.tableWidget_customer.item(idx,0).text())]={'power_ep': True if requestedOutputs['power_ep'] else False, 'temp_ep': True if requestedOutputs['temp_ep'] else False, 'p_ep': True if requestedOutputs['p_ep'] else False, 'mdot_ep': True if requestedOutputs['mdot_ep'] else False}
            elif self.type=='customer':
                invokedOutputs[self.type+'s'][int(self.dlg.tableWidget_customer.item(idx,0).text())]={'power_c': True if requestedOutputs['power_c'] else False, 'temp_c': True if requestedOutputs['temp_c'] else False, 'p_c': True if requestedOutputs['p_c'] else False, 'mdot_c': True if requestedOutputs['mdot_c'] else False, 'heatbalance_c': True if requestedOutputs['heatbalance_c'] else False, 'troom_c': True if requestedOutputs['troom_c'] else False}
            self.progress_value=int((idx+1)/rows_count*98)
            self.signals.progress.emit(self.progress_value)
        writeInvokedOutputs(self.config,invokedOutputs)
        self.signals.progress.emit(100)  
         
def setFeatureParm(dlg,conn,config,plugin_dir):
    """" Save table to DB an close dialog"""
    if conn:
        cur=conn.cursor(cursor_factory = psycopg2.extras.RealDictCursor)   
        table=dlg.tableWidget_parameters
        mappingParms={}
        
        for row in range(table.rowCount()):
            mappingParms[int(table.item(row, 0).text())]={'parm_name' : table.item(row, 3).text(),'model_name' : table.item(row, 4).text(),'mapping_expression' : table.item(row, 1).text().replace("'","''"),'macro_name' : table.item(row, 5).text() ,'mapping_direction' : table.cellWidget(row, 2).currentText(), 'description' : table.item(row, 6).text()}

        #print(dlg.loadedMappingParms)
        #print(mappingParms)
        
        sql=""
        #deleted
        for key_loaded in dlg.loadedMappingParms:
            if key_loaded not in mappingParms: 
                #print('removed sensor')
                sql+="""DELETE FROM model_parms WHERE id={};""".format(key_loaded) # nosec B608
        
        #added
        for key_table in mappingParms:
            if key_table not in dlg.loadedMappingParms: 
                #print('added parm')
                sql+="""INSERT INTO model_parms (id, type, mapping_expression, parm_name, model_name, macro_name, mapping_direction, description) VALUES({},{},'{}','{}','{}','{}','{}','{}');\n""".format(# nosec B608
                    key_table,1 if dlg.rbtn_customers.isChecked() else 2,mappingParms[key_table]['mapping_expression'], mappingParms[key_table]['parm_name'],mappingParms[key_table]['model_name'],mappingParms[key_table]['macro_name'],mappingParms[key_table]['mapping_direction'],mappingParms[key_table]['description']) # nosec B608             
            else:   
                #Check for updated columns
                for col in ['mapping_expression','parm_name','model_name','macro_name','mapping_direction','description']:
                    if dlg.loadedMappingParms[key_table][col]!=mappingParms[key_table][col]:
                        sql+="""UPDATE model_parms SET {} = '{}' WHERE id = {} ;\n""".format(col,mappingParms[key_table][col],key_table) # nosec B608
        
        if sql:
            #print(sql)
            cur.execute(sql)
        
        closeDialog(dlg)
   
def invokeOneFeature(dlg,idx,cur,config,type,invoked,parmRun=False,saveParmRunResults=False,parallize=False,signals=False):
    """Invoke the selected feature. Copy the files from the templates to ida_mosim\invoked_"feature"s
        If dlg is not given the id is the idx"""    
    #print('idx='+str(idx))
    if idx !=-1:
        if dlg and not saveParmRunResults:
            id=dlg.tableWidget_customer.item(idx,0).text()  
        else:
            id=idx
        #print('id='+id)     
       
        #create directory and files in modelling plugin folder if not exists
        dir=config['pathProjects']+config['projectName']+"\\versions\\"
        createDir(dir,config['versionName'])
        dir+=config['versionName']+"\\"
        createDir(dir,'invoked_{}s'.format(type)) 
        dir+='invoked_{}s'.format(type)
        #print(dir)
            
        sql="""SELECT f.template, t.template_name, t.conn_bundle_type 
            FROM "{}".{}s f,{}_templates t 
            WHERE f.template=t.template AND f.id={};""".format(config['versionName'],type,type,id) # nosec B608
        #print(sql)
        cur.execute(sql)
        type_old=""
        template_old=""
        for feature in cur.fetchall():
            #print(feature)
            template_name=str(feature['template'])+'_'+str(feature['template_name'])
    
            dir_template=config['pathProjects']+"{}\\{}_templates".format(config['projectName'],type)            
            
            createDir(dir,type.capitalize()+"_"+id)
            
            replaceDict={}
            
            if type=='customer':
                pass  
            elif type=='energy_plant':
                sql="""WITH sub AS(
    WITH sub AS(
        SELECT count(mir) AS mir_counter,geom AS mir_point FROM "{}".boreholes WHERE plant_id={} AND mir=TRUE GROUP BY geom
    )
    SELECT CASE WHEN sub.mir_counter>0 THEN ST_X(sub.mir_point) ELSE (max(st_x(geom))-min(st_x(geom)))/2 + min(st_x(geom)) END AS x_center, 
           CASE WHEN sub.mir_counter>0 THEN ST_Y(sub.mir_point) ELSE (max(st_y(geom))-min(st_y(geom)))/2 + min(st_y(geom)) END AS y_center
        FROM "{}".boreholes 
        LEFT JOIN sub ON true WHERE plant_id={} GROUP BY sub.mir_counter, sub.mir_point
)
SELECT id,round((st_x(geom) - x_center)::numeric,2) AS x, round((st_y(geom) - y_center)::numeric,2) AS y, "group" FROM "{}".boreholes,sub WHERE plant_id={} AND mir=FALSE ORDER BY "group",id;""".format(config['versionName'],id,config['versionName'],id,config['versionName'],id) # nosec B608
                cur.execute(sql)
                boreholes=cur.fetchall()
                #print(boreholes)
                if boreholes:
                    x="#("+" ".join([str(i['x']) for i in boreholes])+")"
                    x_source="(:DEFAULT #S (MS-SPARSE DEFAULT-VALUE T DIMENSION 1 VALUE ("+" ".join(['('+str(counter)+')' for counter,i in enumerate(boreholes,1)])+")) 2)"
                    y="#("+" ".join([str(i['y']) for i in boreholes])+")"
                    nholes=len([str(i['x']) for i in boreholes])
                    ngroups=len(set([str(i['group']) for i in boreholes]))
                    ng_dict={}
                    for i in boreholes:
                        try:
                            ng_dict[i['group']]=ng_dict[i['group']]+1
                        except:
                            ng_dict[i['group']]=1
                    #print(ng_dict)

                    ng='#('+' '.join([str(ng_dict[i]) for i in ng_dict])+')'
                    
                    sql='SELECT * FROM "{}".borehole_fields WHERE id={};'.format(config['versionName'],id) # nosec B608
                    #print(sql)
                    cur.execute(sql)
                    field_data=cur.fetchone()
                    #print(field_data)
                    if not field_data:
                        if parallize:
                            signals.error.emit("No borehole field data for plant id={} (layer boreholes) available!".format(id))
                        else:
                            iface.messageBar().pushMessage("Critical", "No borehole field data for plant id={} (layer boreholes) available!".format(id), level=Qgis.Critical)
                        return False
                    sql="SELECT liquid FROM liquids WHERE id={};".format(field_data['liqtype']) # nosec B608
                    cur.execute(sql)
                    liqtype='|'+cur.fetchone()['liquid']+'|'
                    replaceDict={':FEATURE': {'GHX_MANY': {
                        #'X': {':V' : x, ':S': x_source},
                        'X': x,
                        'Y' : y,'NHOLE': nholes,'NGROUPS':ngroups,'NG':ng,
                        'ZHOLE':field_data['zhole'],'RHOLE':field_data['rhole'],
                        'RB':field_data['rb'],'RPIPEEARTH':field_data['rpipeearth'],'RPIPEGROUT':field_data['rpipegrout'],'RRINGEARTH':field_data['rringearth'],'RGROUTEARTH':field_data['rgroutearth'],'RGROUTGROUT':field_data['rgroutgrout'],
                        'MIR':field_data['mir'],'RMAX':field_data['rmax'],'NRING':field_data['nring'],'NZHOLE':field_data['nzhole'],'NLAYT':field_data['nlayt'],'N1':field_data['n1'],'N2':field_data['n2'],'N3':field_data['n3'],'TOUTPUT':field_data['toutput'],
                        'CPGRD':field_data['cpgrd'],'LAMBGRD':field_data['lambgrd'],'RHOGRD':field_data['rhogrd'],
                        'CPGROUT':field_data['cpgrout'],'LAMBGROUT':field_data['lambgrout'],'RHOGROUT':field_data['rhogrout'],
                        'RPIPE':field_data['rpipe'],'THICKPIPE':field_data['thickpipe'],'CPPIPE':field_data['cppipe'],'LAMBPIPE':field_data['lambpipe'],
                        'LCASING':field_data['lcasting'],'LAMBDA':field_data['lambda'],'RHOSURFLAY':field_data['rhosurface'],'CPSURFLAY':field_data['cpsurface'],
                        'LIQTYPE':liqtype,'TFREEZE':field_data['tfreeze'],'LAMBLIQ':field_data['lambliq'],
                        'TMEAN':field_data['tmean'],'GEOTGRAD':field_data['geotgrad']}}}
            #print(replaceDict)
            
            #get model parameter
            sql="""SELECT * FROM model_parms WHERE type = {} ORDER BY id;""".format(1 if type=='customer' else 2) # nosec B608
            #print(sql)
            cur.execute(sql)
            parms=cur.fetchall()
            #print(parms)
            sql="""SELECT * FROM "{}".{}s WHERE id={};""".format(config['versionName'],type,id) # nosec B608
            #print(sql)
            cur.execute(sql)
            fields=cur.fetchone()
            #print(fields)
            
            for parm in parms:
                mapping_expression=parm['mapping_expression']
                for field in fields:
                    mapping_expression=mapping_expression.replace('"'+field+'"',str(fields[field]))
                #print(mapping_expression)
                try:
                    mapping_expression=ast.literal_eval(mapping_expression)
                except:
                    #print('Failed eval!')
                    signals.error.emit("Failed to evaluate mapping expression for feature id={}: {}".format(id,mapping_expression))
                #print('++++++++'+parm['model_name'])
                if parm['macro_name'] and parm['parm_name'] and parm['model_name'] and parm['mapping_direction'] in ['<-->','-->']:
                    #print(parm['model_name'])
                    try:
                        replaceDict[parm['macro_name']][parm['model_name']][parm['parm_name']]= mapping_expression
                    except:
                        try:
                            replaceDict[parm['macro_name']].update({parm['model_name']:{parm['parm_name']: mapping_expression}})
                        except:
                            replaceDict[parm['macro_name']]={parm['model_name']:{parm['parm_name']: mapping_expression}}
            
            #print(replaceDict)
            
            CopyTemplateFiles(source_dir=dir_template,source_name=template_name,target_dir=dir,target_name=type.capitalize()+'_'+id,update_sensors=True,type=type,template=str(feature['template']),id=id,cur=cur,config=config,replaceDict=replaceDict,parmRun=parmRun,update_sf=True)
            dir+="\\"+type.capitalize()+"_"+id+"\\"
            f_idc=dir+type.capitalize()+"_"+id+".idc"
            f_idm=dir+type.capitalize()+"_"+id+".idm"
            
            try:
                if invoked:
                    dlg.tableWidget_customer.setItem(idx,1,QTableWidgetItem('Yes'))
                    dlg.tableWidget_customer.viewport().update()
            except:
                pass
            type_old=type
            template_old=feature['template']
    else:
        iface.messageBar().pushMessage("Info", "No item selected!", level=Qgis.Info) 

class InvokeFeatures():
    def __init__(self,plugin_dir,config):
        self.plugin_dir=plugin_dir
        self.config=config
        self.conn=dbConnect(self.config,True)
        if self.conn:
            self.cur=self.conn.cursor(cursor_factory = psycopg2.extras.RealDictCursor)
            self.type='customer'
            self.dlg_invokeFeatures=InvokeFeaturesDlg()
            #print(self.dlg_invokeFeatures.rbtn_customers)  
            
            self.dlg_invokeFeatures.rbtn_customers.toggled.connect(self.updateFeatureLists)
            self.dlg_invokeFeatures.rbtn_plants.toggled.connect(self.updateFeatureLists)   
            
            self.dlg_invokeFeatures.btn_invokeOne.clicked.connect(self.invokeSelectedFeatures)
            self.dlg_invokeFeatures.btn_invokeAll.clicked.connect(self.invokeAllFeatures)
            self.dlg_invokeFeatures.btn_openInvoked.clicked.connect(self.openInvokedFeature)
            self.dlg_invokeFeatures.btn_simulateInvoked.clicked.connect(lambda: self.simulateInvokedFeatures(self.dlg_invokeFeatures,config))
            self.dlg_invokeFeatures.btn_showFeatureLoad.clicked.connect(lambda: self.showFeatureLoad(self.dlg_invokeFeatures))
            self.dlg_invokeFeatures.btn_ok.clicked.connect(lambda: closeDialog(self.dlg_invokeFeatures))
            self.loadInvokeFeatureData(self.dlg_invokeFeatures)
            self.dlg_invokeFeatures.tableWidget_customer.resizeColumnsToContents()
            self.dlg_invokeFeatures.show()
            
    def invokeSelectedFeatures(self):
        #invokeOneFeature(self.dlg_invokeFeatures,self.dlg_invokeFeatures.tableWidget_customer.currentRow(),self.cur,self.config,self.type,self.iface,True,parallize=False)
        selected_indexes = self.dlg_invokeFeatures.tableWidget_customer.selectedIndexes()
        rows=[i.row() for i in selected_indexes]
        #print(rows)
        self.startInvokeFeaturesWorker(rows)
        
    def updateFeatureLists(self,s):
        """Update the list of customers or plants based on the radio button """
        #print('Update customers/plants list')
        #print(s)
        if self.dlg_invokeFeatures.sender()==self.dlg_invokeFeatures.rbtn_customers:
            self.type='customer'
        elif self.dlg_invokeFeatures.sender()==self.dlg_invokeFeatures.rbtn_plants:
            self.type='energy_plant'
        sql='SELECT array_agg(id::TEXT ORDER BY id) AS ids FROM "{}".{}s;'.format(self.config['versionName'],self.type)# nosec B608
        #print(sql)
        self.cur.execute(sql)
        ids=self.cur.fetchall()[0]['ids']
        #print(ids)
        self.dlg_invokeFeatures.tableWidget_customer.setRowCount(0)
        i=0
        if ids:
            for id in ids:
                #print(id)
                self.dlg_invokeFeatures.tableWidget_customer.insertRow(i)
                self.dlg_invokeFeatures.tableWidget_customer.setItem(i,0,QTableWidgetItem(id))
                if os.path.exists(self.config['pathProjects']+"{}\\versions\\{}\\invoked_{}s\\{}_{}.idm".format(self.config['projectName'],self.config['versionName'],self.type,self.type.capitalize(),id)): 
                    exists='Yes'
                else:
                    exists='No'
                self.dlg_invokeFeatures.tableWidget_customer.setItem(i,1,QTableWidgetItem(exists))
                i+=1        
            
    def loadInvokeFeatureData(self,dlg):
        """Collect all feature ids and check if they are already invoked"""
        sql="""SELECT id FROM "{}".{}s ORDER BY id;""".format(self.config['versionName'],self.type) # nosec B608
        #print(sql)
        self.cur.execute(sql)
        i=0
        for id in self.cur.fetchall():
            #print(str(id['id']))
            dlg.tableWidget_customer.insertRow(i)
            dlg.tableWidget_customer.setItem(i,0,QTableWidgetItem(str(id['id'])))
            if os.path.exists(self.config['pathProjects']+"{}\\versions\\{}\\invoked_{}s\\{}_{}.idm".format(self.config['projectName'],self.config['versionName'],self.type,self.type.capitalize(),str(id['id']))): 
                exists='Yes'
            else:
                exists='No'
            dlg.tableWidget_customer.setItem(i,1,QTableWidgetItem(str(exists)))
            i+=1
                  
    def openInvokedFeature(self):
        """Open the invoked feature in IDA. Changes can be saved"""  
        idx=self.dlg_invokeFeatures.tableWidget_customer.currentRow()
        #print(idx)
        if idx!=-1:
            id=self.dlg_invokeFeatures.tableWidget_customer.item(idx,0).text()
            file_path=self.config['pathProjects']+"{}\\versions\\{}\\invoked_{}s\\{}_{}.idm".format(self.config['projectName'],self.config['versionName'],self.type,self.type.capitalize(),id)  
            if os.path.exists(file_path):
                #print(file_path)
                self.worker_openInvoked = WorkerOpenModelCmd(file_path,self.config)
                QThreadPool.globalInstance().start(self.worker_openInvoked) 
                self.worker_openInvoked.signals.error.connect(show_error_message)
                self.worker_openInvoked.signals.progress.connect(self.dlg_invokeFeatures.update_progress)  

                #print('finished open feature')
                
            else:
                iface.messageBar().pushMessage("Info", "Feature not yet invoked!", level=Qgis.Info)
        else:
            iface.messageBar().pushMessage("Info", "No item selected!", level=Qgis.Info)

    def simulateInvokedFeatures(self,dlg,config):
        """Simulate the invoked features in IDA."""  
        #print('Simulate invoked features')
        ids=[dlg.tableWidget_customer.item(idx,0).text() for idx in range(0,dlg.tableWidget_customer.rowCount())]
        #print(ids)
        if ids:
            file_pathes=[config['pathProjects']+"{}\\versions\\{}\\invoked_{}s\\{}_{}.idm".format(self.config['projectName'],self.config['versionName'],self.type,self.type.capitalize(),i)  for i in ids]
            #print(file_pathes)

            self.worker_simInvoked = WorkerSimulateFilesAPI(file_pathes,self.plugin_dir,config)
            QThreadPool.globalInstance().start(self.worker_simInvoked) 
            self.worker_simInvoked.signals.error.connect(self.dlg_invokeFeatures.show_error_message)
            self.worker_simInvoked.signals.progress.connect(self.dlg_invokeFeatures.update_progress)         
        else:
            iface.messageBar().pushMessage("Info", "No item selected!", level=Qgis.Info)
        #print('simulation finished')

    def showFeatureLoad(self,dlg):
        """Show feature load"""  
        idxs=[index.row() for index in dlg.tableWidget_customer.selectedIndexes()]
        #print(idxs)
        count=0
        if idxs:
            dlg.type=self.type
            dlg.fig, dlg.ax = plt.subplots(layout='constrained')
            dlg.fig2, dlg.ax2 = plt.subplots(layout='constrained')
            self.worker_plotLoad = WorkerPlotInvokedFeatureLoad(rows=idxs,type=self.type,dlg=dlg,config=self.config)
            QThreadPool.globalInstance().start(self.worker_plotLoad) 
            self.worker_plotLoad.signals.error.connect(dlg.show_error_message)
            self.worker_plotLoad.signals.progress.connect(dlg.update_progress)        
            self.worker_plotLoad.signals.dataProcessed.connect(dlg.plot_data) #matplotlib is not thread save; data is plotted in main thread instead
            self.worker_plotLoad.signals.plot_total.connect(dlg.plot_total_data)
            self.worker_plotLoad.signals.plot.connect(dlg.show_plots)
            
        else:
            iface.messageBar().pushMessage("Info", "No feature selected or not invoked!", level=Qgis.Info)
                       
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
        self.worker_invokeFeature = WorkerInvokeFeatures(config=self.config,plugin_dir=self.plugin_dir,dlg=self.dlg_invokeFeatures,type=self.type,rows=rows)
        QThreadPool.globalInstance().start(self.worker_invokeFeature) 
        self.worker_invokeFeature.signals.error.connect(show_error_message)
        self.worker_invokeFeature.signals.progress.connect(self.dlg_invokeFeatures.update_progress)      

               
class CopyTemplateFiles:
    """ Copy the files and rename it"""
    def __init__(self,source_dir='',source_name='',target_dir='',target_name='',update_sensors=False,type='',template='',id='',cur='',config='',replaceDict='',parmRun='',update_sf=False):
        #print('++++++++++++++++++++++++++CopyTemplateFiles++++++++++++++')
        #print(parmRun)
        self.config=config
        type_name=type
        if update_sensors:
            type=getTypeIdByName(type)
            sql="""SELECT s.sensor_id
    FROM sensor_source s, source_template s_t
    WHERE s.sensor_id=s_t.source_id AND s_t.template={} AND s.measure=5 AND s.type={} AND s_t.active=false;""".format(template,type) # nosec B608
            #print(sql)
            cur.execute(sql)
            remove_sensor_source_ids=cur.fetchall()
            #print(remove_sensor_source_ids)
        
        #print(source_dir)
        #print(source_name)
        #print(target_name)
        #project idm
        filedata=readAndReplaceFileToList(source_dir+'\\'+source_name+'.idm',{'"'+source_name+'"': '"'+target_name+'"'})
        
        if replaceDict:
            #print({j : replaceDict[i][j] for i in replaceDict if i in [':BUILDING',':SYSTEM'] for j in replaceDict[i]})
            filedata=replaceKeywordsInFiledata(filedata,{j : replaceDict[i][j] for i in replaceDict if i in [':BUILDING',':SYSTEM'] for j in replaceDict[i]})
        if update_sensors:
            filedata=delSensorConnection(filedata,remove_sensor_source_ids,'Source')
        writeToFileFromList(filedata,target_dir,target_dir+'\\'+target_name+'.idm')     
        
        #project idc
        filedata=readAndReplaceFileToList(source_dir+'\\'+source_name+'.idc',{'"'+source_name+'"': '"'+target_name+'"'})           
        if update_sensors:
            filedata=delSensorConnection(filedata,remove_sensor_source_ids,'Source')
        writeToFileFromList(filedata,target_dir,target_dir+'\\'+target_name+'.idc')     
      
        if os.path.exists(target_dir+'\\'+target_name):
            shutil.rmtree(target_dir+'\\'+target_name)
        createDir(target_dir,target_name)
        dir_macro=target_dir+'\\'+target_name
        #print(source_dir+'\\'+source_name+'\\'+source_name+'.idm')
        
        #feature
        #make subset of replaceDict based on macro name
        pList=propertyListCompsIDM(getIDAListComponents(readFileToString(source_dir+'\\'+source_name+'\\'+source_name+'.idm')))
        if replaceDict:
            #print(replaceDict)
            pList=replaceKeywordsInPList(pList,{j : replaceDict[i][j] for i in replaceDict if i in [source_name, ':FEATURE'] for j in replaceDict[i]})
        if update_sf:
            #print('**************************sf********************')        
            sf=getSFList(pList,[])

            if sf:
                sql='\n'.join(["""INSERT INTO "{}".invoked_sf (sf,vars,type)
    SELECT '{}', ARRAY[{}], '{}' WHERE NOT EXISTS (
        SELECT 1 FROM "{}".invoked_sf WHERE sf = '{}' AND type='{}'
    );""".format(self.config['versionName'],i[0][':SF'],','.join(["'"+getSFLinkRefs(i)[j]+"'" for j in getSFLinkRefs(i)]),type_name,self.config['versionName'],i[0][':SF'],type_name)  for i in sf]) # nosec B608
                #print(sql)
                cur.execute(sql)
            sql="""SELECT id,sf FROM "{}".invoked_sf WHERE type='{}';""".format(self.config['versionName'],type_name)# nosec B608
            cur.execute(sql)
            sf_ids=cur.fetchall()
            pList=delSFAndConnsAddLinks(pList,sf,sf_ids)
        else:
            sf=[]

        if update_sensors:
            pList=delSensorConnectionPList(pList,remove_sensor_source_ids,'Source')
        #print(pList)
        writePropertyListIDMToFile(pList,dir_macro,dir_macro+'\\'+target_name+'.idm',self.config)

        filedata=readFileToList(source_dir+'\\'+source_name+'\\'+source_name+'.idc')
        if update_sensors:
            filedata=delSensorConnection(filedata,remove_sensor_source_ids,'Source')
        if update_sf:
            sf_names=[i[0][':N'] for i in sf]
            #print(sf_names)
            filedata=[i for i in filedata if not [True for j in sf_names if j in i]]
        writeToFileFromList(filedata,dir_macro,dir_macro+'\\'+target_name+'.idc')   
        
        #sf-macro.idm
        filedata=[""";IDA {} Data UTF-8
(DOCUMENT-HEADER :TYPE DISTRICTS-MACRO :D "Districts macro" :APP (DISTRICTS :VER {})) """.format(getIDAVersion(self.config),getIDADistrictsVersion(self.config))]
        for i in sf:
            i[0][':N']='"SOURCE-FILE-{}"'.format([j['id'] for j in sf_ids if i[0][':SF']==j['sf']][0])
            filedata+=["""\n{}""".format(pListToCompString(i,0))]
        writeToFileFromList(filedata,dir_macro,dir_macro+'\\sf-macro.idm')

        #sf-macro.idc
        filedata=[""";IDA {} Data UTF-8
(DOCUMENT-HEADER :TYPE SCHEMA :PAGE-WIDTH 178 :PAGE-HEIGHT 97) 
(SELF-FRAME :AT ((352 190)) :R (342 176) :SLOT (:SELF) :DATA MACRO-OBJECT) """.format(getIDAVersion(self.config))]
        filedata+=["""\n(EQUATION-FRAME :AT ((50 {})) :R (20 20) :ICON "sys:source-file.ids" :SLOT ("SOURCE-FILE-{}") :NAME "SOURCE-FILE-{}" :DATA SOURCE-FILE :D "SOURCE-FILE")""".format(30+counter*48,i['id'],i['id']) for counter,i in enumerate([j for i in sf for j in sf_ids if i[0][':SF']==j['sf']],1)]
        writeToFileFromList(filedata,dir_macro,dir_macro+'\\sf-macro.idc')
        
        #sensor-macro.idm
        filedata=readAndReplaceFileToList(source_dir+'\\'+source_name+'\\Sensor-macro.idm',{'"'+source_name+'"': '"'+target_name+'"'}) 
        filedata=replaceKeywordsInFiledata(filedata,{j : replaceDict[i][j] for i in replaceDict if 'Sensor-macro'==i for j in replaceDict[i]})
        writeToFileFromList(filedata,dir_macro,dir_macro+'\\Sensor-macro.idm')   

        #check if folder contains macros
        #print('+++check if folder contains macros+++')
        #print(dir_macro)
        #print(source_dir)
        if os.path.exists(source_dir+'\\'+source_name):
            for root, dirs, files in os.walk(source_dir+'\\'+source_name):
                for file in files:
                    if (file.endswith('.idm') or file.endswith('.idc')) and file.lower() not in ['sensor-macro.idm',source_name.lower()+'.idm',source_name.lower()+'.idc','sf-macro.idm','sf-macro.idc']:
                        #subfolder=os.path.dirname(os.path.join(root, file)).replace('/','\\').split(source_name+'\\'+source_name)[1]
                        #print(os.path.splitext(os.path.basename(file))[0])
                        path_target=dir_macro+os.path.join(root, file).split(source_dir+'\\'+source_name)[1].split(file)[0]
                        copyFileReplaceStr(os.path.join(root, file),path_target,path_target+file,[source_name],[target_name],{j : replaceDict[i][j] for i in replaceDict if file.lower().split('.')[0]==i.lower() for j in replaceDict[i]})

                        #copyFile(os.path.join(root, file),path_target,path_target+'\\'+file)
                        
                #print(dirs)
                for dir in dirs: 
                    #print(os.path.join(root, dir).split(source_dir+'\\'+source_name)[1])
                    createSubDir(dir_macro+os.path.join(root, dir).split(source_dir+'\\'+source_name)[1])
                    #print(dir_macro+os.path.join(root, dir).split(source_dir+'\\'+source_name)[1])
            try:
                os.rename(dir_macro+'\\'+source_name.lower(), dir_macro+'\\'+target_name)
            except:
                try:
                    os.rename(dir_macro+'\\'+source_name, dir_macro+'\\'+target_name)
                except:
                    pass
                                
        