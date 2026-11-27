from .utility_functions.translations import tr_msg
from qgis.PyQt.QtWidgets import QMessageBox
from qgis.core import Qgis, QgsMessageLog

import os
from qgis.PyQt.QtCore import QRunnable, pyqtSlot
from .cosim import writeCosimMacroIdc, writeCosimMacroIdm
from .ida_resources import KUSUDA_KEYS, updateClimateTemplate
from .invoke_sensors import (
    sensorMacroIdcData, sensorMacroIdmData, sensorProjectIdmConns, sensorProjectIdmMacro,
)
from .outputs import addRequestedOutputsSensors, writeMacroResultsIdc, writeMacroResultsIdm
from .update_sensors import removeResultSensors
from .utility_functions.compat import MessageCritical
from .utility_functions.db import cleanupResultsSensors, dbConnect, getClimateData, getUsedSubmodels
from .utility_functions.dialog import checkState
from .utility_functions.files import (
    copyFile, createDir, loadInvokedOutputs, loadModellingSettings, loadNetworkSimData, loadProjectConfig,
    loadRequestedOutputs, removeFilesInDir, writeInvokedOutputs, writeMacroSFIdc, writeMacroSFIdm,
    writeToFile,
)
from .utility_functions.ida_components import getSimData
from .utility_functions.sensor_signals import getResultSensorData, getSensorData, getSensorDecData
from .utility_functions.twin_pipe import twinPipeEquivalent
from .utility_functions.templateFiles import (
    CopyDecoupledTemplateMacro, CopyTemplateMacro, readDecoupledFeatureSensorSignals,
)
from .utility_functions.utility import getDatetimeFromString, getIDADistrictsVersion, getIDAVersion
from .utility_functions.ground_collector_contract import CONTRACT_VERSION
from .utility_functions.ground_collectors import (
    collectorLines, fitFor, groundMoContractVersion, groundParameters, lineTerminals, liquidNames, loopPipe, readCollectors,
    startValues,
)
from .utility_functions.workers import closesOwnConnection, APISignals
from .utility_functions.workers import WorkerOpenAPI
from .utility_functions.zeta import hasConnectionZetaColumn
from .supervisory_control import Supervisory_control, CopySupervisoryControl


from multiprocessing import Process

import math
import psycopg2.extras
import traceback
from .utility_functions.debug_log import dprint, debug_enabled


class WorkerBuildNetworkModel(QRunnable):
    """Worker thread
    Inherits from QRunnable to handle worker thread setup, signals and wrap-up."""
    def __init__(self,*args,**kwargs):
        super().__init__()
        dprint('--WorkerBuildNetworkModel--')
        self.signals=APISignals()
        self.config=kwargs['config']
        self.dlg=kwargs['dlg']
        self.conn=""
        self.cur=""
        self.plugin_dir=kwargs['plugin_dir']
        self.conn = dbConnect(self.config,True)
        self.networks=kwargs['networks']
        self.submodels=kwargs['submodels']
        self.exclude_features=kwargs.get('exclude_features')
        self.main=kwargs['main']
        self.dlg.process_running=True

        if self.conn:
            self.cur=self.conn.cursor(cursor_factory = psycopg2.extras.RealDictCursor)
            
    @pyqtSlot()
    @closesOwnConnection
    def run(self):
        dprint('run worker invoke network')
        self.progress_value=1
        self.signals.progress.emit(self.progress_value)
        
        self.requestedOutputs=loadRequestedOutputs(self.plugin_dir,self.config)
        self.modellingSettings=loadModellingSettings(self.plugin_dir,self.config)
        self.networkSimData=loadNetworkSimData(self.plugin_dir,self.config)
        InvokeNetworkModel(self.main,self.config,self.plugin_dir,self.requestedOutputs,self.modellingSettings,self.networks,self.submodels,self.networkSimData,self.dlg.checkbox_reinvokeFeatures.checkState() == checkState(),self.signals,
            exclude_features=self.exclude_features)
        
class PageSettings:
    def __init__(self,cur,submodel,versionName,networks):
        sql="""WITH sub AS(    
    SELECT ST_XMin(ST_Union(geom)) as xmin, ST_YMin(ST_Union(geom)) as ymin,ST_XMax(ST_Union(geom)) as xmax, ST_YMax(ST_Union(geom)) as ymax FROM "{}".lines  WHERE {} = ANY (submodel) AND network IN ({})
    UNION
    SELECT ST_XMin(ST_Union(geom)) as xmin, ST_YMin(ST_Union(geom)) as ymin,ST_XMax(ST_Union(geom)) as xmax, ST_YMax(ST_Union(geom)) as ymax FROM "{}".customers WHERE {} = submodel AND network <@ array[{}] 
    UNION
    SELECT ST_XMin(ST_Union(geom)) as xmin, ST_YMin(ST_Union(geom)) as ymin,ST_XMax(ST_Union(geom)) as xmax, ST_YMax(ST_Union(geom)) as ymax FROM "{}".energy_plants WHERE {} = submodel AND network <@ array[{}] 
)
SELECT min(xmin) AS xmin, min(ymin) AS ymin ,max(xmax) AS xmax, max(ymax) AS ymax FROM sub;""".format(versionName,str(submodel),','.join([str(i) for i in networks]),versionName,str(submodel),','.join([str(i) for i in networks]),versionName,str(submodel),','.join([str(i) for i in networks])) # nosec B608
        dprint(sql)
        cur.execute(sql)
        settings=cur.fetchone()
        self.xmin=settings['xmin']
        self.ymin=settings['ymin']
        self.xmax=settings['xmax']
        self.ymax=settings['ymax']

        sql="""WITH sub AS(
    SELECT Min(ST_Length(geom)) AS lmin FROM "{}".lines WHERE {} = ANY (submodel) AND network IN ({})
    UNION
    SELECT min(ST_Distance(c1.geom, c2.geom)) AS lmin FROM "{}".customers c1, "{}".customers c2 WHERE c1.id <> c2.id AND {} = c1.submodel AND {} = c2.submodel
    UNION
    SELECT min(ST_Distance(ep1.geom, ep2.geom)) AS lmin FROM "{}".energy_plants ep1, "{}".energy_plants ep2 WHERE ep1.id <> ep2.id AND {} = ep1.submodel AND {} = ep2.submodel
    UNION
    SELECT min(ST_Distance(ep.geom, c.geom)) AS lmin FROM "{}".energy_plants ep, "{}".customers c WHERE {} = ep.submodel AND {} = c.submodel
)
SELECT min(lmin) AS lmin FROM sub;""".format(versionName,submodel,','.join([str(i) for i in networks]),versionName,versionName,submodel,submodel,versionName,versionName,submodel,submodel,versionName,versionName,submodel,submodel) # nosec B608
        dprint(sql)
        cur.execute(sql)
        self.lmin=cur.fetchone()
        if self.lmin['lmin']:
            self.lmin=self.lmin['lmin']
            if self.lmin<15:
                self.lmin=15
        else:
            self.lmin=15
            
        self.pageHeight=self.getPageHeight()
        self.pageWidth=self.getPageWidth()
        dprint({'xmin': self.xmin,'ymin': self.ymin,'xmax': self.xmax,'ymax': self.xmax,'pageHeight': self.pageHeight,'pageWidth': self.pageWidth})
            
    def getPageSettings(self):
        return {'xmin':self.xmin,'ymin':self.ymin,'xmax':self.xmax,'ymax':self.xmax,'pageHeight':self.pageHeight,'pageWidth':self.pageWidth,'lmin':self.lmin}
    
    def getPageHeight(self):
        dymax=50+(self.ymax-self.ymin)/self.lmin*150
        pageHeight=(108+dymax+50+50)*0.2575
        return pageHeight                  
    
    def getPageWidth(self):
        dxmax=(self.xmax-self.xmin)/self.lmin*150
        pageWidth=(dxmax+100+150)*0.2575
        if pageWidth<197:
            pageWidth=197
        return pageWidth               
  
    
class InvokeNetworkModel:
    """ Builds an IDA network model; steps:
        1) insert nodes
        2) insert customers
        3) insert energy plants
        4) insert pipes between customers and nodes
        5) insert pipes between nodes"""

    # progress bar: share of the preparation (climate, sensor data) and of the final step (saving outputs)
    PROGRESS_PREPARATION=7
    PROGRESS_END=99
    # relative duration of the build steps of one submodel in 0.1 s: (key, status text, weight, weight if the feature templates are reinvoked)
    # (measured with 999 substations / 12 pipe bundles; the feature templates are copied per feature and report their own progress,
    # copying took 1.4-16 s depending on the file system, invoking and copying 27 s)
    PROGRESS_STEPS=[
        ('network_templates','writing network templates',3,3),
        ('supervisory','supervisory control',1,1),
        ('sensors','sensor macros',38,35),
        ('customers_templates','customer templates',40,265),
        ('energy_plants_templates','energy plant templates',1,1),
        ('result_macros','result macros',1,1),
        ('lines','lines',6,6),
        ('features','customers and energy plants',1,1),
        ('connections','connections',2,2),
        ('junctions','junctions',1,1),
        ('write','writing model files',1,1),
    ]

    def setProgress(self,value,text=None):
        """emit the progress (never backwards, max. 99 until finished) and the status text"""
        value=int(max(self.progress_value,min(99,value)))
        if value!=self.progress_value:
            self.progress_value=value
            self.signals.progress.emit(value)
        if text is not None and text!=self.progress_text:
            self.progress_text=text
            self.signals.status.emit(text)

    def setStepProgress(self,step,fraction=0.0,detail=''):
        """progress of a build step (PROGRESS_STEPS) of the current submodel; fraction: part of the step which is done"""
        weights=[i[3] if self.reinvoke else i[2] for i in self.PROGRESS_STEPS]
        keys=[i[0] for i in self.PROGRESS_STEPS]
        idx=keys.index(step)
        step_start=sum(weights[:idx])/sum(weights)
        step_end=sum(weights[:idx+1])/sum(weights)
        submodel_fraction=step_start+(step_end-step_start)*fraction
        span=(self.PROGRESS_END-self.PROGRESS_PREPARATION)/self.n_submodels
        text=tr_msg(self.PROGRESS_STEPS[idx][1])+(' '+detail if detail else '')
        if self.n_submodels>1:
            text=tr_msg('submodel {} ({}/{}): {}').format(self.submodel,self.submodel_counter+1,self.n_submodels,text)
        self.setProgress(self.PROGRESS_PREPARATION+span*(self.submodel_counter+submodel_fraction),text)

    def featureProgressFn(self,step):
        """callback for CopyTemplateMacro: progress per feature, status text e.g. 'customer templates 120/999'"""
        def progress_fn(done,total):
            if total and (done==total or done%max(1,total//200)==0):
                self.setStepProgress(step,done/total,'{}/{}'.format(done,total))
        return progress_fn

    def __init__(self,main,config,plugin_dir,requestedOutputs,modellingSettings,networks,submodels,networkSimData,reinvoke,signals,exclude_features=None):
        """exclude_features: {'customers': [ids], 'energy_plants': [ids]} features which are neglected in the model
        (not connected to the network: they are no model components, here they are also removed from the sensor signals)"""
        dprint('**********invoke network*********')
        dprint(submodels)
        self.networkSimData=networkSimData
        self._collectors=None
        self.plugin_dir=plugin_dir
        self.config=config
        self.signals=signals
        self.reinvoke=reinvoke
        self.progress_value=0
        self.progress_text=None
        self.n_submodels=max(1,len(submodels))
        self.submodel_counter=0
        self.submodel=''
        self.setProgress(1,tr_msg('connecting to the database'))
        self.conn=dbConnect(self.config,True)
        if self.conn:
            self.cur=self.conn.cursor(cursor_factory = psycopg2.extras.RealDictCursor)

            try:
                self.setProgress(2,tr_msg('climate data'))
                climate_file=getClimateData(self.cur,self.config,True)['filename']
                if os.path.exists(climate_file):
                    try:
                        updateClimateTemplate(main,climate_file)
                    except ValueError as e:
                        # a climate file without one of the quantities the climate macro needs
                        self.signals.error.emit(tr_msg("The climate file cannot be used: {}").format(e))
                        return
                    # the Kusuda wave was just recalculated from the climate file: the collector fits must use the
                    # wave of the climate macro, not the one loaded before the build
                    saved=loadModellingSettings(plugin_dir,config)
                    modellingSettings=dict(modellingSettings,**{k:saved[k] for k in KUSUDA_KEYS if k in saved})
                else:
                    self.signals.error.emit(tr_msg("Climate file could not be found: ") + climate_file)
                    return
                
                self.projectConfig=loadProjectConfig(self.config,signals=self.signals)
                
                dir=self.config['pathProjects']+self.config['projectName']+"\\versions\\"
                createDir(dir,config['versionName'])
                dir+=self.config['versionName']
                
                #clean dir
                for submodel in submodels:
                    self.buildingDirPath = """{}\\{}""".format(dir.replace('/','\\'),'network_'+str(submodel))
                    removeFilesInDir(self.buildingDirPath)
                    
                #simulated outputs
                self.invokedOutputs=loadInvokedOutputs(self.config)
                dprint(self.invokedOutputs)
                self.invokedOutputs['lines'] = {'v_lines': True if requestedOutputs['v_lines'] else False, 'mdot_lines': True if requestedOutputs['mdot_lines'] else False, 'p_lines': True if requestedOutputs['p_lines'] else False, 'temp_lines': True if requestedOutputs['temp_lines'] else False}
                dprint(self.invokedOutputs)
   
                #setSubnetwork(self.cur,self.config)
                feature_dec_irefs=[]
                resources=[]
                
                self.setProgress(4,tr_msg('sensor data'))
                cleanupResultsSensors(self.cur)
                added_sensor_info=addRequestedOutputsSensors(self.cur,self.config,requestedOutputs)
                dprint('---added-----')
                filter=''
                sensor_data=getSensorData(self.cur,self.config,target_types=[1,2,3],filter=filter,networks=networks,exclude_features=exclude_features)
                for network in networks:
                    sensor_data+=getResultSensorData(self.cur,self.config,network=network)
                dprint('---sensor-data-----')
                dprint(sensor_data)                

                if debug_enabled(): dprint(getUsedSubmodels(self.cur, self.config))
                for submodel in getUsedSubmodels(self.cur, self.config):
                    #decoupling: make macro with import/export connections for features which are connected to the submodel lines but not in the submodel  
                    dprint('//////************------//////*------')
                    for i in readDecoupledFeatureSensorSignals(submodel,dir,self.config,self.cur,sensor_data):
                        dprint(i)
                        if i not in feature_dec_irefs:
                            feature_dec_irefs.append(i)
                dprint(feature_dec_irefs)
                
                self.setProgress(6,tr_msg('sensor data'))
                sensor_dec_data=getSensorDecData(sensor_data,feature_dec_irefs,self.cur,self.config)
                dprint(sensor_dec_data)

                #supervisory_submodel=str(getSupervisorySubmodel(self.cur,self.config)['submodel'])
                supervisory_submodel=str(submodels[0])

                for self.submodel_counter,submodel in enumerate(submodels):
                    self.submodel=submodel
                    self.setStepProgress('network_templates')
                    self.pageSettings=PageSettings(self.cur,submodel,self.config['versionName'],networks).getPageSettings()
                    idm=self.writeNetworkTemplateIdm(submodel,dir,requestedOutputs,networkSimData,sensor_dec_data,networks)
                    dec_templates=CopyDecoupledTemplateMacro(submodel,dir,self.config,self.cur,sensor_data)

                    resources.extend(dec_templates.resources)
                    dprint(dec_templates.resources)
                    
                    import_counter=dec_templates.import_counter
                    dprint(import_counter)
                    
                    idc=self.writeNetworkTemplateIdc(submodel,dir,networks,supervisory_submodel)
                    createDir(dir,'network_'+str(submodel))
                    
                    #climate
                    source_dir_climateMacro=self.config['pathProjects']+self.config['projectName']+'\\climate\\climate\\'
                    target_dir_climateMacro=dir+'\\network_'+str(submodel)+'\\'
                    copyFile(source_dir_climateMacro+'climate-macro.idm',target_dir_climateMacro,target_dir_climateMacro+'climate-macro.idm')
                    copyFile(source_dir_climateMacro+'climate-macro.idc',target_dir_climateMacro,target_dir_climateMacro+'climate-macro.idc')

                    #decoupling
                    idm+=writeCosimMacroIdm(self.config,self.cur,submodel,dir,sensor_data,sensor_dec_data)
                    writeCosimMacroIdc(self.config,self.cur,submodel,dir)
                    self.setStepProgress('supervisory')

                    idm_conn="\n(CONNECTIONS"
                    idc_conn=""
                    
                    #supervisory control
                    sql="""SELECT COALESCE(
    (SELECT submodel FROM supervisory_ctrl LIMIT 1),
    '1'
) AS submodel;"""
                    self.cur.execute(sql)
                    if submodel==str(self.cur.fetchone()['submodel']):
                        dprint("""*-*-*-*-copy supervisory*-*-*-*-""")
                        if not os.path.exists(self.config['pathProjects']+self.config['projectName']+'\\versions\\{}\\supervisory_control\\supervisory_control.idm'.format(self.config['versionName'])):
                            Supervisory_control(self.plugin_dir,self.config,exclude_features=exclude_features)                     
                        resources.extend(CopySupervisoryControl(self.config['pathProjects']+self.config['projectName'],self.config,self.cur,submodel).resources)
                    self.setStepProgress('sensors')

                    #Sensors
                    #NetworkSensorSignals(self.cur,self.config,dir+'\\network_'+str(submodel))
                    dir_network=dir+'\\network_'+str(submodel)
                    dprint('%%%%%%%&&&&&&&&&&&&&&&&%%%%%%%%%%%%%%%')
                    sensorMacroIdmData(submodel,supervisory_submodel,sensor_dec_data,sensor_data,self.cur,self.config,dir_network,import_counter)
                    sensorMacroIdcData(submodel,supervisory_submodel,sensor_dec_data,sensor_data,self.cur,self.config,dir_network,self.plugin_dir)
                    
                    idm_conn=sensorProjectIdmConns(submodel,supervisory_submodel,sensor_dec_data,idm_conn)
                    idm=sensorProjectIdmMacro(submodel,supervisory_submodel,sensor_dec_data,idm)

                    #----------------supervisory ctrl------------------------
                    if submodel==supervisory_submodel:
                        idm+="""\n((MACRO-OBJECT :N "Supervisory_control" :T DISTRICTS-MACRO){}{}{})""".format(
                            #iref sources if source type is supervisory ctrl (3) and function == Same signal for all targets (5))
                            ''.join(["""\n (:IREF :N "Int_Ref_Sensor_Source_{}" :T OUT :F 224)""".format(j['iref']) 
                                for i in sensor_dec_data if i['source_type']==3 and i['function']==5 for j in i['irefs_source']]),  
                            #iref sources if source type is supervisory ctrl (3) and function == Individual signals for each target (6)
                            ''.join(["""\n (:IREF :N "Int_Ref_Sensor_Source_{}" :T OUT :F 224)""".format(j['iref']) 
                                for i in sensor_dec_data if i['source_type']==3 and i['function']==6 for j in i['irefs_target']]),  
                            #iref targets connections from Sensor to feature if type Supervisory Ctrl (3) 
                            ''.join(["""\n (:IREF :N "Int_Ref_Sensor_Target_{}" :T IN :F 208)""".format(j['iref']) 
                                for i in sensor_dec_data if i['target_type']==3 for j in i['irefs_target']]))

                    for type in ["customers","energy_plants"]:
                        self.setStepProgress(type+'_templates')
                        if reinvoke:
                            sql="""DELETE FROM "{}".invoked_sf WHERE type='{}';""".format(self.config['versionName'],type[:-1])# nosec B608
                            self.cur.execute(sql)
                        dprint(self.signals)
                        copyTemplateMacro=CopyTemplateMacro(submodel,dir,type,self.config,self.cur,self.plugin_dir,reinvoke,self.invokedOutputs,requestedOutputs,parallize=True,signals=self.signals,
                            progress_fn=self.featureProgressFn(type+'_templates'))
                        self.invokedOutputs[type]=copyTemplateMacro.invokedFeatureOutputs
                        resources.extend(copyTemplateMacro.resources)
                    self.setStepProgress('result_macros')
                    dprint('&&&&&&&&&&&&&&&&&&&&&&')
                    if debug_enabled(): dprint(set(resources))
                    idm+=''.join(["\n"+i for i in set(resources)])
                    
                    #sf-macro
                    writeMacroSFIdm(self.config,self.cur,dir_network)
                    writeMacroSFIdc(self.config,self.cur,dir_network)

                    #results-macro
                    for network in networks:
                        writeMacroResultsIdm(self.config,self.cur,dir_network,requestedOutputs,sensor_dec_data,added_sensor_info,network)
                        writeMacroResultsIdc(self.config,self.cur,dir_network,requestedOutputs,added_sensor_info,network)
                    self.setStepProgress('lines')
                    
                    # Define the path to the building idm file
                    self.buildingDirPath = """{}\\{}\\""".format(dir.replace('/','\\'),'network_'+str(submodel))
                    self.buildingIdmFilePath = """{}\\{}.idm""".format(dir.replace('/','\\'),'network_'+str(submodel))
                    self.buildingIdcFilePath = """{}\\{}.idc""".format(dir.replace('/','\\'),'network_'+str(submodel))
                    
                    self.collectorConns=[]
                    idm,idc=self.insertLines(submodel,requestedOutputs,modellingSettings,idm,idc,networks)
                    if getattr(self,'buildError',False):
                        return
                    self.setStepProgress('features')
                    idm,idc=self.insertCustomers(submodel,idm,idc,sensor_dec_data,networks,feature_dec_irefs)
                    idm,idc=self.insertPlants(submodel,idm,idc,sensor_dec_data,networks)

                    self.setStepProgress('connections')
                    idm_conn,idc_conn=self.insertConnections(submodel,'customers',idm_conn,idc_conn,networks)
                    idm_conn,idc_conn=self.insertConnections(submodel,'energy_plants',idm_conn,idc_conn,networks)
                    idm_conn,idc_conn=self.insertJunctionConnections(submodel,idm_conn,idc_conn,networks)
                    idm_conn,idc_conn,plug_dict=self.insertJunctionPlugConnections(submodel,idm_conn,idc_conn,networks)
                    self.setStepProgress('junctions')
                    idm,idc=self.insertJunctions(submodel,requestedOutputs,modellingSettings,idm,idc,networks)
                    idm,idc=self.insertPlugJunctions(submodel,requestedOutputs,modellingSettings,idm,idc,networks,plug_dict)
                    self.setStepProgress('write')
                    idm_conn+=''.join(self.collectorConns)
                    idm_conn+=")"
                    idm+=idm_conn
                    idc+=idc_conn
                    writeToFile(idm,self.buildingDirPath,self.buildingIdmFilePath)
                    writeToFile(idc,self.buildingDirPath,self.buildingIdcFilePath)
                self.setProgress(self.PROGRESS_END,tr_msg('saving outputs'))
                writeInvokedOutputs(self.config,self.invokedOutputs)
                removeResultSensors(self.cur,added_sensor_info.values())
                self.signals.progress.emit(100)
                self.signals.status.emit(tr_msg('finished'))
                self.signals.finished.emit(tr_msg('Network model has been build successfully!'))

            except Exception:
                QgsMessageLog.logMessage(
                    traceback.format_exc(),
                    "Districts",
                    MessageCritical
                )
                
            
    def insertLines(self,submodel,requestedOutputs,modellingSettings,idm,idc,networks):
        """ Inserts the lines in the submodel.
        zeta of a line: lines.zeta + per junction junctions.zeta/2 + junction_connections.zeta (textbook values, see utility_functions/zeta.py)"""
        #old projects have no zeta in junction_connections (the build does not change the tables)
        zeta_conn='COALESCE(jc.zeta,0)' if hasConnectionZetaColumn(self.cur,self.config['versionName']) else '0'
        sql="""WITH sub AS (
    SELECT l.id, ST_3DLength(l.geom) AS length,
           ST_Z(ST_EndPoint(l.geom))-ST_Z(St_StartPoint(l.geom)) AS height_diff,
           COALESCE(l.zeta,0) + COALESCE(zeta.zeta_j,0) AS zeta,
           l.pipe_bundle_type_id, 
           c.counter, 
           ST_asText(ST_LineInterpolatePoint(l.geom,0.5)) AS point_pipe,
           ST_AsText(ST_StartPoint(l.geom)) AS point_start,
           ST_AsText(ST_EndPoint(l.geom)) AS point_end,
           n.t_ref, n.t_freeze, liq.liquid
    FROM "{}".lines l
    JOIN (SELECT count(*) AS counter, pipe_bundle_type_id
          FROM public.bundle_pipes GROUP BY pipe_bundle_type_id) c
      ON c.pipe_bundle_type_id = l.pipe_bundle_type_id
    JOIN "{}".network n
      ON l.network=n.id
    JOIN liquids liq
      ON n.liq_type=liq.id
    JOIN (SELECT l.id, sum(COALESCE(j.zeta,0)/2 + {zeta_conn}) AS zeta_j
          FROM "{}".lines l
          JOIN "{}".junction_connections jc ON jc.lid = l.id
          JOIN "{}".junctions j ON j.id = jc.jid
          GROUP BY l.id) zeta
      ON zeta.id = l.id
    WHERE {} = ANY (l.submodel) AND l.network IN ({})
),
all_lines AS (
    SELECT l.id, ST_3DLength(l.geom) AS length,
           ST_Z(ST_EndPoint(l.geom))-ST_Z(St_StartPoint(l.geom)) AS height_diff,
           l.pipe_bundle_type_id, 
           c.counter, 
           ST_asText(ST_LineInterpolatePoint(l.geom,0.5)) AS point_pipe,
           ST_AsText(ST_StartPoint(l.geom)) AS point_start,
           ST_AsText(ST_EndPoint(l.geom)) AS point_end,
           l.zeta,
           n.t_ref, n.t_freeze, liq.liquid
    FROM "{}".lines l
    JOIN (SELECT count(*) AS counter, pipe_bundle_type_id
          FROM public.bundle_pipes GROUP BY pipe_bundle_type_id) c
      ON c.pipe_bundle_type_id = l.pipe_bundle_type_id
    JOIN "{}".network n
      ON l.network=n.id
    JOIN liquids liq
      ON n.liq_type=liq.id
    WHERE {} = ANY (l.submodel) AND l.network IN ({})
),
merged AS (
    -- compare without zeta
    SELECT id, length, height_diff, pipe_bundle_type_id, counter, point_pipe, point_start, point_end, t_ref, t_freeze, liquid
    FROM all_lines
    EXCEPT
    SELECT id, length, height_diff, pipe_bundle_type_id, counter, point_pipe, point_start, point_end, t_ref, t_freeze, liquid
    FROM sub
    
    UNION
    SELECT id, length, height_diff, pipe_bundle_type_id, counter, point_pipe, point_start, point_end, t_ref, t_freeze, liquid
    FROM sub
)
-- finally, re-attach the correct zeta:
SELECT m.id, m.length, m.height_diff, m.t_ref,m.t_freeze,m.liquid,
       COALESCE(s.zeta, a.zeta, 0) AS zeta,
       m.pipe_bundle_type_id, m.counter,
       m.point_pipe, m.point_start, m.point_end
FROM merged m
LEFT JOIN sub s ON s.id = m.id
LEFT JOIN all_lines a ON a.id = m.id
ORDER BY m.id;
""".format(self.config['versionName'],self.config['versionName'],self.config['versionName'],self.config['versionName'],self.config['versionName'], submodel,','.join([str(i) for i in networks]),self.config['versionName'],self.config['versionName'], submodel,','.join([str(i) for i in networks]),zeta_conn=zeta_conn) # nosec B608
        dprint(sql)

        self.cur.execute(sql)
        i=1
        alpha_i=4000
        pipe_info_cache={} #pipe data per pipe bundle type (query once per type instead of once per line)
        twin_casing_cache={} #layers per casing construction of the twin pipes
        for pipe_bundle in self.cur.fetchall():
            dprint(pipe_bundle)
            lid=pipe_bundle['id']
            length=pipe_bundle['length']
            bunde_type=pipe_bundle['pipe_bundle_type_id']
            npipes = pipe_bundle['counter']
            point_pipe = pipe_bundle['point_pipe'].split("(")[1][:-1].split(' ')
            point_start = pipe_bundle['point_start'].split("(")[1][:-1].split(' ')
            point_end = pipe_bundle['point_end'].split("(")[1][:-1].split(' ')
            coordinates=self.getSymbolCoordinatesAngle(point_start,point_pipe,point_end)
            zeta=pipe_bundle['zeta']
            dprint(coordinates)
            
            if bunde_type not in pipe_info_cache:
                sql="""SELECT p.innerpipediameter,p.piperoughnessfactor, p.casing_construction_id, bp.sequence AS se_pipe, bp.ambient, bp.x, bp.y AS depth, ARRAY_AGG(pl.sequence::text||':'|| round(pl.thickness,4)::text||':'||m.thermal_conductivity_w7mkelvin::text||':'||m.specific_heat_j7kgkelvin::text||':'||m.density_kg7m3 ORDER BY pl.sequence) AS layers
    FROM public.bundle_pipes bp, public.pipes p, public.pipe_layers pl, public.materials m
    WHERE bp.pipe_bundle_type_id={} AND bp.pipe_id=p.id AND pl.pipe_construction_id=p.pipe_construction_id AND m.id=pl.materialid
    GROUP BY p.innerpipediameter,p.piperoughnessfactor, p.casing_construction_id, se_pipe,bp.ambient, bp.x, bp.y
    ORDER BY bp.sequence;""".format(bunde_type) # nosec B608
                dprint(sql)
                self.cur.execute(sql)
                pipe_info_cache[bunde_type]=self.cur.fetchall()
            pipe_info=pipe_info_cache[bunde_type]
            if not pipe_info:
                self.signals.error.emit(tr_msg("Pipe construction data corrupted! PLease check construction data."))
                return idm,idc
            dPipes=[i['innerpipediameter'] for i in pipe_info]
            roughness=' '.join(str(i['piperoughnessfactor']) for i in pipe_info)
            layers=pipe_info[0]['layers']
            pipe=[{'thickness': pipe['layers'][0].split(':')[1], 'lambda': pipe['layers'][0].split(':')[2], 'cp': pipe['layers'][0].split(':')[3], 'rho': pipe['layers'][0].split(':')[4]} for pipe in pipe_info]
            if len(pipe_info[0]['layers'])>1:
                insulation=[{'thickness': pipe['layers'][1].split(':')[1], 'lambda': pipe['layers'][1].split(':')[2], 'cp': pipe['layers'][1].split(':')[3], 'rho': pipe['layers'][1].split(':')[4]} for pipe in pipe_info]
            else:
                insulation=[{'thickness': '0', 'lambda': '0', 'cp': '0', 'rho': '0'} for pipe in pipe_info]
            
            x_coord=[i['x'] for i in pipe_info]
            depth=[i['depth'] for i in pipe_info]
            twin_error=self.convertTwinPipes(pipe_info,pipe,insulation,x_coord,depth,modellingSettings['ground_lambda'],twin_casing_cache)
            if twin_error:
                self.signals.error.emit(tr_msg('Twin pipe of the pipe bundle {}: {}').format(bunde_type,twin_error))
                return idm,idc

            #ground collector line: the loop pipe as GroundCollector with its GroundSurface, the other pipes stay a bundle
            collectors=self.collectorContext(modellingSettings)
            if collectors is None:
                self.buildError=True
                return idm,idc
            if lid in collectors['lines']:
                collectors['log']=bool(requestedOutputs.get('coll_lines'))
                models=self.collectorModels(collectors,lid,collectors['lines'][lid],pipe_info,pipe_bundle,coordinates)
                if models is None:
                    self.buildError=True
                    return idm,idc
                collector_idm,collector_idc,keep=models
                idm+=collector_idm
                idc+=collector_idc
                if not keep:
                    continue
                pipe_info=[pipe_info[k] for k in keep]
                dPipes=[dPipes[k] for k in keep]
                roughness=' '.join(str(i['piperoughnessfactor']) for i in pipe_info)
                pipe=[pipe[k] for k in keep]
                insulation=[insulation[k] for k in keep]
                x_coord=[x_coord[k] for k in keep]
                depth=[depth[k] for k in keep]
                npipes=len(keep)

            
            if pipe_info[0]['ambient']==1: #air
                tamb_conn=' (:VAR :N |TAmb| :B (1 "Climate-macro" "climate_processor" TAIR2))'
            elif pipe_info[0]['ambient']==2: #ground
                tamb_conn=' (:VAR :N |TAmb| :B (1 "Climate-macro" "TGround" OUTSIGNAL))'
            elif pipe_info[0]['ambient']==3: #duct
                tamb_conn=' (:VAR :N |TAmb| :B (1 "Climate-macro" "TDuct" OUTSIGNAL))'
            if requestedOutputs['temp_lines']:
                idm+="""\n(output-file :sf "self:\\Line_temp_{}.prn" :n "Line_temp_{}" :t output-file)""".format(lid,lid)
                temp="""\n  (:VAR :N |Temp| :L "Line_temp_{}")""".format(lid)
            else:
                temp=""
            if requestedOutputs['v_lines']: 
                idm+="""\n(output-file :sf "self:\\Line_v_{}.prn" :n "Line_v_{}" :t output-file)""".format(lid,lid)
                vel="""\n  (:VAR :N |Vel| :L "Line_v_{}")""".format(lid)
            else:
                vel=""
            if requestedOutputs['mdot_lines']: 
                idm+="""\n(output-file :sf "self:\\Line_mdot_{}.prn" :n "Line_mdot_{}" :t output-file)""".format(lid,lid)
                mdot="""\n  (:VAR :N |mLiq| :L "Line_mdot_{}")""".format(lid)
            else:
                mdot=""
            if requestedOutputs['qamb_lines']: 
                idm+="""\n(output-file :sf "self:\\Line_qamb_{}.prn" :n "Line_qamb_{}" :t output-file)""".format(lid,lid)
                qamb="""\n  (:VAR :N |QAmbtotal| :L "Line_qamb_{}")""".format(lid)
            else:
                qamb=""
            if requestedOutputs['p_lines']: 
                idm+="""\n(output-file :sf "self:\\Line_p_{}.prn" :n "Line_p_{}" :t output-file)""".format(lid,lid)
                p="""\n ((CONNECTOR :N |liq1|)
  (:VAR :N P :L "Line_p_{}" :AS #S(MS-SPARSE DEFAULT-VALUE NIL DIMENSION 1 VALUE ({}))))
 ((CONNECTOR :N |liq2|)
  (:VAR :N P :L "Line_p_{}" :AS #S(MS-SPARSE DEFAULT-VALUE NIL DIMENSION 1 VALUE ({}))))""".format(lid,''.join(["""({} . "L_{}")""".format(i+1,i+1) for i in range(npipes)]),lid,''.join(["""({} . "R_{}")""".format(i+1,i+1) for i in range(npipes)]))
            else:
                p=""
                                  
            idm+="""\n((MODEL :N "Pipebundle_{}" :T |FDpipebundle|)
 (:PAR :N |npipes| :V {})
 (:PAR :N |lcell| :V {})
 (:PAR :N |l| :V {})
 (:PAR :N |depth| :V #({}))
 (:PAR :N |x_coordinates| :V #({}))
 (:PAR :N |ambientType| :V |{}|)
 (:PAR :N |lambdaSoil| :V {})
{}
 (:PAR :N |nK| :V {})
 ((RECORD :N |pipen|)
  (:PAR :N |k| :V #2A({}))
  (:PAR :N |h| :V #({}))
  (:PAR :N |liqType| :V #({}))
  (:PAR :N |TFreeze| :V #({}))
  (:PAR :N |TliqRef| :V #({}))
  (:PAR :N |dPipe| :V #({}))
  (:PAR :N |aPipe| :V #({}))
  (:PAR :N |cpPipe| :V #({}))
  (:PAR :N |rhoPipe| :V #({}))
  (:PAR :N |lambdaPipe| :V #({}))
  (:PAR :N |aIns| :V #({}))
  (:PAR :N |cpIns| :V #({}))
  (:PAR :N |rhoIns| :V #({}))
  (:PAR :N |lambdaIns| :V #({}))
  (:PAR :N |epsilon| :V #({})){}{}{}{}){})""".format(lid,
                                                npipes,
                                                modellingSettings['fd_meterPerNode'],
                                                length,
                                                ' '.join([str(i) for i in depth]),
                                                ' '.join([str(i) for i in x_coord]),
                                                'Air' if pipe_info[0]['ambient']==1 else ('Ground' if pipe_info[0]['ambient']==2 else 'Duct'),
                                                modellingSettings['ground_lambda'],
                                                tamb_conn, 
                                                1 if zeta else 0,
                                                ' '.join(['('+str(zeta)+')' for i in dPipes if zeta]),
                                                ' '.join([str(pipe_bundle['height_diff']) for i in dPipes]),
                                                ' '.join(['|'+str(pipe_bundle['liquid'])+'|' for i in dPipes]),
                                                ' '.join([str(pipe_bundle['t_freeze']) for i in dPipes]),
                                                ' '.join([str(pipe_bundle['t_ref']) for i in dPipes]),
                                                ' '.join([str(i) for i in dPipes]),
                                                ' '.join([i['thickness'] for i in pipe]),
                                                ' '.join([i['cp'] for i in pipe]),
                                                ' '.join([i['rho'] for i in pipe]),
                                                ' '.join([i['lambda'] for i in pipe]),
                                                ' '.join([i['thickness'] for i in insulation]),
                                                ' '.join([i['cp'] for i in insulation]),
                                                ' '.join([i['rho'] for i in insulation]),
                                                ' '.join([i['lambda'] for i in insulation]),
                                                roughness,
                                                temp,
                                                vel,
                                                mdot,
                                                qamb,
                                                p)
            idc+="""(EQUATION-FRAME :AT (({} {})) :R (10 10) :ICON "sys:Components/DistrictsMo/symbols/FDpipebundle.ids" :SYMMETRY {} :SLOT ("Pipebundle_{}") :NAME "Pipebundle_{}" :DATA MODEL) 
""".format(coordinates['x_pipe'],coordinates['y_pipe'],coordinates['angle'],lid,lid)
        
        return idm,idc
    
    def collectorContext(self,modellingSettings):
        """Collector lines of the version, their resources and fits, site and start day; once per build. Checks before
        the build (design R5): GroundMo of the contract version installed, IGlob in the climate macro. None after an
        error (already reported)."""
        if self._collectors is not None:
            return self._collectors
        context: dict={'lines':collectorLines(self.cur,self.config['versionName']),'fits':{},'terminals':{},'settings':modellingSettings}
        if context['lines']:
            version=groundMoContractVersion(self.config['pathDistricts'])
            if version!=CONTRACT_VERSION:
                self.signals.error.emit(tr_msg("Ground collectors need the IDA Districts library GroundMo with contract version {} (installed: {}).").format(
                    CONTRACT_VERSION,version if version is not None else '-'))
                return None
            macro=os.path.join(self.config['pathProjects']+self.config['projectName'],'climate','climate','climate-macro.idm')
            text=open(macro,encoding='utf-8',errors='replace').read() if os.path.exists(macro) else ''
            if '"IGlob"' not in text:
                self.signals.error.emit(tr_msg("The climate macro has no global radiation IGlob needed by the ground collectors."))
                return None
            climate=getClimateData(self.cur,self.config,True)
            context['resources']=readCollectors(self.cur)
            context['liquids']=liquidNames(self.cur)
            context['climate_file']=climate['filename']
            context['site']={'lat':float(climate['latitude']),'long':float(climate['longitude']),'long_timezone':float(climate['timezone'])*15}
            context['albedo_signal']='"albedo"' in text
            start=getDatetimeFromString(self.networkSimData['startup_time_from'])
            context['start_day']=start.timetuple().tm_yday-1+start.hour/24
        self._collectors=context
        return context

    def collectorModels(self,context,lid,line,pipe_info,pipe_bundle,coordinates):
        """GroundCollector "Collector_<lid>" and GroundSurface "CollectorSurface_<lid>" of a collector line (design R4,
        R7); returns (idm, idc, indexes of the bundle's other pipes) or None after an error."""
        resource=context['resources'][line['collector_id']]
        modellingSettings=context['settings']
        liquid=context['liquids'].get(resource['liquid_id'])
        if liquid is None:
            self.signals.error.emit(tr_msg("Ground collector {}: its liquid {} is not in the list of liquids.").format(resource['name'],resource['liquid_id']))
            return None
        sequences=[i['se_pipe'] for i in pipe_info]
        loop_sequence=resource['loop_sequence']
        if loop_sequence not in sequences:
            self.signals.error.emit(tr_msg("Ground collector line {}: its pipe bundle has no pipe of sequence {}.").format(lid,loop_sequence))
            return None
        if line['collector_id'] not in context['fits']:
            try:
                context['fits'][line['collector_id']]=fitFor(self.cur,resource,modellingSettings,
                    progress=lambda name: self.signals.status.emit(tr_msg('Fitting the ground collector {}').format(name)))
            except ValueError as e:
                self.signals.error.emit(tr_msg("Ground collector {}: {}").format(resource['name'],e))
                return None
        entry,geometry,soil,surface=context['fits'][line['collector_id']]
        if not entry['accepted']:
            self.signals.error.emit(tr_msg("The fit of the ground collector {} is not accepted (errors {}).").format(
                resource['name'],', '.join('{} {:.0%}'.format(k,v) for k,v in entry['errors'].items())))
            return None
        params=groundParameters(entry,geometry,soil,surface)
        start=startValues(self.cur,resource,entry,geometry,soil,params,line['t_mean_init'],context['climate_file'],
                          context['site'],context['start_day'])
        pipe=loopPipe(self.cur,resource['pipe_id'])
        sections=int(resource['n_sections'])
        vec=lambda value: '#('+' '.join([str(value)]*sections)+')'
        surface_names=('epsilon','hConv','dLayer','rhoCLayer','spacing')
        ground=''.join('\n (:PAR :N |{}| :V {})'.format(k,v) for k,v in params.items() if k not in surface_names)
        #states start from their :V, not from the start parameters; TLoc and TNear get theirs with their logging
        starts=''.join('\n (:PAR :N |{}| :V {})'.format(k,vec(start[k]))
                       for k in ('TStartTop','TStartTop2','TStartLoc','TStartNear','TStartFar','TStartFar2'))
        starts+=''.join('\n (:VAR :N |T{}| :V {})'.format(k[6:],vec(start[k])) for k in ('TStartTop','TStartTop2','TStartFar','TStartFar2'))
        out="Line_coll_{}".format(lid)
        #requested output coll_lines: the collector's results in Line_coll_<lid>.prn (logged by :L on the variables)
        log_parts={'file':'','l_tin':'','l_tout':'','l_qextracted':'','l_qsurface':'','l_tloc':'','l_tnear':'','l_ice':''}
        if context.get('log'):
            cols=self.sparse('OFF',['({} . "{}")'.format(j,out) for j in range(1,sections+1)])
            names=lambda prefix: self.sparse('NIL',['({} . "{}_{}")'.format(j,prefix,j) for j in range(1,sections+1)])
            log_parts={'file':'\n(output-file :sf "self:\\{0}.prn" :n "{0}" :t output-file)'.format(out),
                     'l_tin':' :L "{}" :AS "TIn"'.format(out),'l_tout':' :L "{}" :AS "TOut"'.format(out),
                     'l_qextracted':' :L "{}" :AS "QExtracted"'.format(out),'l_qsurface':' :L "{}" :AS "QSurface"'.format(out),
                     'l_tloc':' :L {} :AS {}'.format(cols,names('TLoc')),'l_tnear':' :L {} :AS {}'.format(cols,names('TNear')),
                     'l_ice':' :L {} :AS {}'.format(cols,names('ice'))}
        idm="""{file}
((MODEL :N "Collector_{lid}" :T |GroundCollector|)
 (:PAR :N |nSections| :V {sections})
 (:PAR :N |nLoops| :V {loops})
 (:PAR :N |lTrench| :V {length})
 (:PAR :N |nCellsSection| :V 10)
 (:PAR :N |loopLengthPerM| :V {per_m})
 (:PAR :N |dInner| :V {d_in})
 (:PAR :N |dOuter| :V {d_out})
 (:PAR :N |lambdaWall| :V {lam})
 (:PAR :N |roughness| :V {rough})
 (:PAR :N |liqType| :V |{liquid}|)
 (:PAR :N |TFreeze| :V {t_freeze}){ground}{starts}
 (:VAR :N |TIn|{l_tin})
 (:VAR :N |TOut|{l_tout})
 (:VAR :N |QExtracted|{l_qextracted})
 (:VAR :N |QSurface|{l_qsurface})
 (:VAR :N |TLoc| :V {v_loc}{l_tloc})
 (:VAR :N |TNear| :V {v_near}{l_tnear})
 (:VAR :N |iceFraction|{l_ice}))
((MODEL :N "CollectorSurface_{lid}" :T |GroundSurface|)
 (:PAR :N |epsilon| :V {eps})
 (:PAR :N |hConv| :V {h})
 (:PAR :N |dLayer| :V {d_layer})
 (:PAR :N |rhoCLayer| :V {rho_c_layer})
 (:PAR :N |spacing| :V {spacing})
 (:PAR :N |TStart| :V {t_surf})
 (:VAR :N |TSurface| :V {t_surf})
 (:VAR :N |TAir| :B (1 "Climate-macro" "climate_processor" TAIR2))
 (:VAR :N |TSky| :B (1 "Climate-macro" "climate_processor" TSKY))
 (:VAR :N |IGlob| :B (1 "Climate-macro" "IGlob" OUTSIGNAL))
 (:VAR :N |albedo| :B {albedo}))""".format(
            lid=lid,sections=sections,loops=line['n_loops'],length=pipe_bundle['length'],
            per_m=geometry.loop_length_per_m,d_in=pipe['d_inner'],d_out=pipe['d_outer'],lam=pipe['lambda_wall'],
            rough=pipe['roughness'],liquid=liquid,t_freeze=resource['t_freeze_liquid_c'],ground=ground,
            starts=starts,v_loc=vec(start['TStartLoc']),v_near=vec(start['TStartNear']),
            file=log_parts['file'],l_tin=log_parts['l_tin'],l_tout=log_parts['l_tout'],l_qextracted=log_parts['l_qextracted'],
            l_qsurface=log_parts['l_qsurface'],l_tloc=log_parts['l_tloc'],l_tnear=log_parts['l_tnear'],l_ice=log_parts['l_ice'],
            eps=params['epsilon'],h=params['hConv'],d_layer=params['dLayer'],rho_c_layer=params['rhoCLayer'],
            spacing=params['spacing'],t_surf=start['TStartSurface'],
            albedo='(1 "Climate-macro" "albedo" |y_var|)' if context['albedo_signal'] else resource['albedo'])
        idc="""(EQUATION-FRAME :AT (({} {})) :R (20 10) :ICON "sys:Components/GroundMo/symbols/GroundCollector.ids" :SYMMETRY {} :SLOT ("Collector_{}") :NAME "Collector_{}" :DATA MODEL)
(EQUATION-FRAME :AT (({} {})) :R (8 6) :ICON "sys:Components/GroundMo/symbols/GroundSurface.ids" :SLOT ("CollectorSurface_{}") :NAME "CollectorSurface_{}" :DATA MODEL)
""".format(coordinates['x_pipe'],coordinates['y_pipe'],coordinates['angle'],lid,lid,coordinates['x_pipe'],coordinates['y_pipe']-25,lid,lid)
        self.collectorConns.append('\n (("Collector_{}" |surface|) ("CollectorSurface_{}" |ground|) 0 0 NIL)'.format(lid,lid))
        terminals=lineTerminals(lid,sequences,loop_sequence)
        #the connection writers address a pipe by its position in the bundle (1..n in sequence order)
        context['terminals'][lid]={k+1:terminals[seq] for k,seq in enumerate(sorted(sequences))}
        keep=[k for k,i in enumerate(pipe_info) if i['se_pipe']!=loop_sequence]
        return idm,idc,keep

    @staticmethod
    def sparse(default,items):
        return '#S(MS-SPARSE DEFAULT-VALUE {} DIMENSION 1 VALUE ({}))'.format(default,' '.join(items))

    def pipeTerminal(self,lid,direction,k):
        """Model name and connector of the k-th pipe (1..n) of a line at its end direction (liq1/liq2): the loop pipe of
        a collector line is the collector's scalar connector, the others the remaining bundle's, renumbered."""
        terminals=self._collectors['terminals'].get(lid) if self._collectors else None
        if not terminals:
            return 'Pipebundle_{}'.format(lid),'(|{}| {})'.format(direction,k)
        model,index=terminals[k]
        return model,('|{}|'.format(direction) if index is None else '(|{}| {})'.format(direction,index))

    def convertTwinPipes(self,pipe_info,pipe,insulation,x_coord,depth,lambda_soil,casing_cache):
        """Twin pipes of a pipe bundle (two pipes with the same casing_construction_id): insulation, x coordinates and depth
        of the two pipes are replaced by the values of two separately insulated pipes with the same heat loss
        (utility_functions.twin_pipe). Returns an error text or None."""
        casings={}
        for idx,info in enumerate(pipe_info):
            if info['casing_construction_id'] is not None:
                casings.setdefault(info['casing_construction_id'],[]).append(idx)
        for casing_id,idxs in casings.items():
            if len(idxs)!=2:
                return 'the casing construction {} is used by {} pipe(s) of the bundle instead of 2'.format(casing_id,len(idxs))
            if casing_id not in casing_cache:
                self.cur.execute("""SELECT pl.thickness, m.thermal_conductivity_w7mkelvin AS lambda, m.specific_heat_j7kgkelvin AS cp, m.density_kg7m3 AS rho
    FROM public.pipe_layers pl, public.materials m WHERE pl.pipe_construction_id=%s AND m.id=pl.materialid ORDER BY pl.sequence;""",(casing_id,))
                casing_cache[casing_id]=self.cur.fetchall()
            layers=casing_cache[casing_id]
            if not layers:
                return 'the casing construction {} has no layers'.format(casing_id)
            foam=layers[0]
            a,b=idxs
            #positions relative to the casing centre (the middle of the two pipe centres), y downwards
            x_casing=(float(x_coord[a])+float(x_coord[b]))/2
            depth_casing=(float(depth[a])+float(depth[b]))/2
            pipes=[(float(x_coord[i])-x_casing,float(depth[i])-depth_casing,float(pipe_info[i]['innerpipediameter'])/2+float(pipe[i]['thickness'])) for i in idxs]
            try:
                thicknesses,dx=twinPipeEquivalent(pipes,float(foam['thickness']),depth_casing,float(foam['lambda']),float(lambda_soil),ground=pipe_info[0]['ambient']==2)
            except ValueError as e:
                return str(e)
            for i,thickness in zip(idxs,thicknesses):
                insulation[i]={'thickness': str(round(thickness,5)), 'lambda': str(foam['lambda']), 'cp': str(foam['cp']), 'rho': str(foam['rho'])}
                depth[i]=depth_casing
            #only the differences of the x coordinates count: a bundle of one twin pipe is centred (the equivalent distance is tiny)
            x_centre=0.0 if len(pipe_info)==2 else x_casing
            dx=max(dx,abs(x_centre)*1e-9)
            sign=1 if float(x_coord[b])>=float(x_coord[a]) else -1
            x_coord[a]=x_centre-sign*dx/2
            x_coord[b]=x_centre+sign*dx/2
        return None

    def insertJunctionPlugConnections(self,submodel,idm_conn,idc_conn,networks):
        """Insert the junction connections between plants or customers and pipes"""
        sql="""WITH q AS (
    SELECT
        j.id AS jid,
        l.id AS lid,
        ST_AsText(j.geom) AS j_point,
        b_pipes.sequence AS seq,
        j.n_connections,
        pipe_lids.lids,
        c.numb_seq AS max_seq,
        CASE
            WHEN ST_DWithin(ST_StartPoint(l.geom), j.geom, 0.0001)
            THEN 'liq1'
            ELSE 'liq2'
        END AS dir,
        ST_AsText(ST_LineInterpolatePoint(l.geom, 0.5)) AS l_point

    FROM "{}".junctions j,
         "{}".junction_connections jc,
         "{}".lines l,
         (
             SELECT
                 pipe_bundle_type_id,
                 count(sequence) AS numb_seq
             FROM bundle_pipes
             GROUP BY pipe_bundle_type_id
         ) c,
         (
             SELECT
                 pipe_bundle_type_id,
                 sequence
             FROM public.bundle_pipes
         ) b_pipes,
         (
             SELECT
                 jid,
                 array_agg(lid ORDER BY lid) AS lids
             FROM "{}".junction_connections
             GROUP BY jid
         ) pipe_lids

    WHERE pipe_lids.jid = jc.jid
      AND l.id = jc.lid
      AND j.id = jc.jid
      AND j.submodel = {}
      AND l.network IN ({})
      AND c.pipe_bundle_type_id = l.pipe_bundle_type_id
      AND b_pipes.pipe_bundle_type_id = c.pipe_bundle_type_id
)

SELECT *
FROM q
WHERE jid IN (
    SELECT jid
    FROM q
    GROUP BY jid
    HAVING COUNT(DISTINCT max_seq) >= 2
)
ORDER BY jid, seq, lid;""".format(self.config['versionName'],self.config['versionName'],self.config['versionName'],self.config['versionName'],submodel,','.join([str(i) for i in networks])) # nosec B608
        dprint(sql)
        self.cur.execute(sql)

        conns=self.cur.fetchall()
        plug_dict={}
        if not conns:
            dprint('No nodes in network or wrong junction constructions!')
            #self.signals.error.emit(tr_msg("No junctions in network or wrong constructions!"))
            return idm_conn,idc_conn, plug_dict
            
        jid_old=0
        lid_old=0
        seq_old=0
        seq_counter=0
        seq_lids=[]
        lids=[]
        for conn in conns:
            try:
                dprint(conn)
                point_pipe = self.getSymbolCoordinate(conn['l_point'].split("(")[1][:-1].split(' '))
                point_j = self.getSymbolCoordinate(conn['j_point'].split("(")[1][:-1].split(' '))
                    
                if conn['seq']!=seq_old:
                    dprint('--new seq--')
                    if seq_counter!=0:
                        #plugs
                        idm_conn+="".join(["""\n (("NodeBundle_{}" (|term| {} {})) ((:LIB WATPLUG) OUTLET) 0 0 NIL)""".format(jid_old,seq_counter,lids.index(i)+1) for i in lids if i not in seq_lids])
                        plugs=[i for i, x in enumerate(lids) if x not in seq_lids]
                        dprint(plugs)
                        for plug in plugs:
                            dprint(plug_dict)
                            dprint(plug)
                            if jid_old in plug_dict and lids[plug] in plug_dict[jid_old]:
                                plug_dict[jid_old][lids[plug]].append(seq_counter)
                            else:
                                plug_dict[jid_old]={lids[plug] : [seq_counter]}
                    seq_lids=[conn['lid']]
                    seq_counter+=1
                    conn_counter=1
                else:
                    seq_lids.append(conn['lid'])

                    
                if conn['jid']!=jid_old:
                    dprint('++new jid++')
                    lids=conn['lids']
                    dprint(lids)
                    conn_counter=1
                    seq_counter=1
                    max_seq=conn['max_seq']
                    pipe_counter={}
                    for lid in lids:
                        pipe_counter[lid]=0                  
                
                pipe_counter[conn['lid']]=pipe_counter[conn['lid']]+1
                
                model,terminal=self.pipeTerminal(conn['lid'],conn['dir'],pipe_counter[conn['lid']])
                idm_conn+="""\n (("NodeBundle_{}" (|term| {} {})) ("{}" {}) 0 0 NIL)""".format(conn['jid'],seq_counter,lids.index(conn['lid'])+1,model,terminal)
                idc_conn+="""(CONNECTION-LINE :AT (({} {}) ({} {})) :LINE-COLOR (:CALL PMT-COLOR [@ 1] [@ 2]) :LINE-STYLE 3 :FIRST-LINK ("NodeBundle_{}" 0.5 (|term| {} {})) :LAST-LINK ("{}" 0.5 {}))\n""".format(point_j['x'],point_j['y'],point_pipe['x'],point_pipe['y'],conn['jid'],seq_counter,lids.index(conn['lid'])+1,model,terminal)


                seq_old=conn['seq']
                jid_old=conn['jid']
                lid_old=conn['lid']
                conn_old=conn
                dprint("seq: {}; conn: {}".format(seq_counter,conn_counter))
                conn_counter+=1
            except Exception as e:
                self.signals.error.emit(tr_msg("Junction connections do not match with pipe bundle sequences. Please check your pipe bundle sequences in data center --> pipe bundles."))

        #plugs
        plugs=[i for i, x in enumerate(lids) if x not in seq_lids]
        dprint(plugs)
        for plug in plugs:
            if jid_old in plug_dict and lids[plug] in plug_dict[jid_old]:
                plug_dict[jid_old][lids[plug]].append(seq_counter)
            else:
                plug_dict[jid_old]={lids[plug] : [seq_counter]}
        idm_conn+="".join(["""\n (("NodeBundle_{}" (|term| {} {})) ((:LIB WATPLUG) OUTLET) 0 0 NIL)""".format(conn['jid'],seq_old,lids.index(i)+1) for i in lids if i not in seq_lids])
            
        return idm_conn,idc_conn, plug_dict

    def insertJunctionConnections(self,submodel,idm_conn,idc_conn,networks):
        """Insert the junction connections between plants or customers and pipes"""
        sql="""WITH q AS (
    SELECT
        j.id AS jid,
        l.id AS lid,
        ST_AsText(j.geom) AS j_point,
        DENSE_RANK() OVER (
            PARTITION BY j.id, l.id
            ORDER BY b_pipes.sequence
        ) AS seq,
        j.n_connections,
        pipe_lids.lids,
        c.numb_seq AS max_seq,
        CASE
            WHEN ST_DWithin(ST_StartPoint(l.geom), j.geom, 0.0001)
            THEN 'liq1'
            ELSE 'liq2'
        END AS dir,
        ST_AsText(ST_LineInterpolatePoint(l.geom, 0.5)) AS l_point

    FROM "{}".junctions j,
         "{}".junction_connections jc,
         "{}".lines l,
         (
             SELECT
                 pipe_bundle_type_id,
                 count(sequence) AS numb_seq
             FROM bundle_pipes
             GROUP BY pipe_bundle_type_id
         ) c,
         (
             SELECT
                 pipe_bundle_type_id,
                 sequence
             FROM public.bundle_pipes
         ) b_pipes,
         (
             SELECT
                 jid,
                 array_agg(lid ORDER BY lid) AS lids
             FROM "{}".junction_connections
             GROUP BY jid
         ) pipe_lids

    WHERE pipe_lids.jid = jc.jid
      AND l.id = jc.lid
      AND j.id = jc.jid
      AND j.submodel = {}
      AND l.network IN ({})
      AND c.pipe_bundle_type_id = l.pipe_bundle_type_id
      AND b_pipes.pipe_bundle_type_id = c.pipe_bundle_type_id
)

SELECT *
FROM q
WHERE jid IN (
    SELECT jid
    FROM q
    GROUP BY jid
    HAVING COUNT(DISTINCT max_seq) = 1
)
ORDER BY jid, seq, lid;""".format(self.config['versionName'],self.config['versionName'],self.config['versionName'],self.config['versionName'],submodel,','.join([str(i) for i in networks])) # nosec B608
        dprint(sql)
        self.cur.execute(sql)

        conns=self.cur.fetchall()
        if not conns:
            dprint('No nodes in network or wrong junction constructions!')
            #self.signals.error.emit(tr_msg("No junctions in network or wrong constructions!"))
            return idm_conn,idc_conn
            
        jid_old=0
        lid_old=0
        seq_old=0
        seq_counter=0
        for conn in conns:
            try:
                dprint(conn)
                point_pipe = self.getSymbolCoordinate(conn['l_point'].split("(")[1][:-1].split(' '))
                point_j = self.getSymbolCoordinate(conn['j_point'].split("(")[1][:-1].split(' '))
                    
                if conn['seq']!=seq_old:
                    dprint('--new seq--')
                    seq_counter+=1
                    conn_counter=1

                if conn['jid']!=jid_old:
                    dprint('++new jid++')
                    lids=conn['lids']
                    dprint(lids)
                    conn_counter=1
                    seq_counter=1
                    pipe_counter={}
                    for lid in lids:
                        pipe_counter[lid]=0                  
                
                pipe_counter[conn['lid']]=pipe_counter[conn['lid']]+1
                
                model,terminal=self.pipeTerminal(conn['lid'],conn['dir'],pipe_counter[conn['lid']])
                idm_conn+="""\n (("NodeBundle_{}" (|term| {} {})) ("{}" {}) 0 0 NIL)""".format(conn['jid'],seq_counter,lids.index(conn['lid'])+1,model,terminal)
                idc_conn+="""(CONNECTION-LINE :AT (({} {}) ({} {})) :LINE-COLOR (:CALL PMT-COLOR [@ 1] [@ 2]) :LINE-STYLE 3 :FIRST-LINK ("NodeBundle_{}" 0.5 (|term| {} {})) :LAST-LINK ("{}" 0.5 {}))\n""".format(point_j['x'],point_j['y'],point_pipe['x'],point_pipe['y'],conn['jid'],seq_counter,lids.index(conn['lid'])+1,model,terminal)


                seq_old=conn['seq']
                jid_old=conn['jid']
                lid_old=conn['lid']
                conn_old=conn
                dprint("seq: {}; conn: {}".format(seq_counter,conn_counter))
                conn_counter+=1
            except Exception as e:
                self.signals.error.emit(tr_msg("Junction connections do not match with pipe bundle sequences. Please check your pipe bundle sequences in data center --> pipe bundles."))

        return idm_conn,idc_conn
    
    def insertConnections(self,submodel,type,idm_conn,idc_conn,networks):
        """Insert the connections between features and the pipe"""
        dprint("********insertConnections:"+type)
        if type=='customers':
            id_name='cid'
            seq_name='c_seq'
        elif type=='energy_plants':
            id_name='epid'
            seq_name='ep_seq'
        sql="""SELECT l.id AS lid,ST_AsText(ST_LineInterpolatePoint(l.geom,0.5)) AS l_point,f.id AS fid, ST_AsText(f.geom) AS f_point, conn_b_t.conn_bundle_type_id,conn_b_t.sequence AS conn_bundl_type_seq, conn_t_conns.connection_type_id, conn_t_conns.sequence AS conn_type_seq, conn.temp, CASE WHEN ST_dWithIn(st_startpoint(l.geom),f.geom,0.01) THEN 'liq1' ELSE 'liq2' END AS dir
    FROM "{}".{} f, "{}".{}_connections fc, "{}".lines l, public.bundle_type_conns conn_b_t, public.{}_templates f_t, public.connections conn, public.connection_type_connections conn_t_conns
    WHERE conn_t_conns.connection_id=conn.id AND conn_t_conns.connection_type_id=conn_b_t.conn_type_id AND conn_b_t.conn_bundle_type_id=f_t.conn_bundle_type AND fc.{}=conn_b_t.sequence AND f_t.template=f.template AND l.id=fc.lid AND f.id=fc.{} AND {} =ANY(l.submodel) AND l.network IN ({})
    ORDER BY f.id, conn_b_t.sequence, conn_type_seq;""".format(self.config['versionName'],type,self.config['versionName'],type[:-1],self.config['versionName'],type[:-1],seq_name,id_name,submodel,','.join([str(i) for i in networks])) # nosec B608
        dprint(sql)
        
        self.cur.execute(sql)
        seq_counter=1
        lid_old=0
        conn_bundl_type_old=0
        for conn in self.cur.fetchall():
            dprint(conn)
            lid=conn['lid']
            fid=conn['fid']
            conn_bundl_type=conn['conn_bundle_type_id']
            if lid!=lid_old or conn_bundl_type!=conn_bundl_type_old:
                seq_counter=1
            point_pipe = self.getSymbolCoordinate(conn['l_point'].split("(")[1][:-1].split(' '))
            point_d = self.getSymbolCoordinate(conn['f_point'].split("(")[1][:-1].split(' '))
            conn_bundl_type_seq=conn['conn_bundl_type_seq']
            conn_type=conn['connection_type_id']
            conn_type_seq=conn['conn_type_seq']
            conn_temp=conn['temp']
            conn_dir=conn['dir']
            
            name_conn="{}_{}_{}_{}".format(conn_bundl_type,conn_bundl_type_seq,conn_type,conn_type_seq)

            model,terminal=self.pipeTerminal(lid,conn_dir,seq_counter)
            idm_conn+="""\n (("{}_{}" "{}") ("{}" {}) 0 0 NIL)""".format(type[:-1].capitalize(),fid,name_conn,model,terminal)
            idc_conn+="""(CONNECTION-LINE :AT (({} {}) ({} {})) :LINE-COLOR (:CALL PMT-COLOR [@ 1] [@ 2]) :LINE-STYLE 3 :FIRST-LINK ("{}_{}" 0.5 "{}") :LAST-LINK ("{}" 0.5 {}))\n""".format(point_d['x'],point_d['y'],point_pipe['x'],point_pipe['y'],type[:-1].capitalize(),fid,name_conn,model,terminal)

            seq_counter+=1
            lid_old=lid
            conn_bundl_type_old=conn_bundl_type
            
        return idm_conn,idc_conn
    
    def getSymbolCoordinate(self,point):
        """Get the IDA x and y coordinates of a georeferenced point in a dict """
        y=round(float(self.pageSettings['pageHeight'])/0.2575-50-((float(point[1])-float(self.pageSettings['ymin']))/float(self.pageSettings['lmin'])*150),0)
        x=round(150+50+(float(point[0])-float(self.pageSettings['xmin']))/float(self.pageSettings['lmin'])*150,0)
        return {'x':x,'y':y}
    
    def getSymbolCoordinatesAngle(self,point_nstart,point_pipe,point_nend):
        """ return dict with coordinates and angle of symbol"""
        y_pipe=round(float(self.pageSettings['pageHeight'])/0.2575-50-((float(point_pipe[1])-float(self.pageSettings['ymin']))/float(self.pageSettings['lmin'])*150),0)
        x_pipe=round(150+50+(float(point_pipe[0])-float(self.pageSettings['xmin']))/float(self.pageSettings['lmin'])*150,0)
        y_nstart=round(float(self.pageSettings['pageHeight'])/0.2575-50-((float(point_nstart[1])-float(self.pageSettings['ymin']))/float(self.pageSettings['lmin'])*150),0)
        x_nstart=round(150+50+(float(point_nstart[0])-float(self.pageSettings['xmin']))/float(self.pageSettings['lmin'])*150,0)
        y_nend=round(float(self.pageSettings['pageHeight'])/0.2575-50-((float(point_nend[1])-float(self.pageSettings['ymin']))/float(self.pageSettings['lmin'])*150),0)
        x_nend=round(150+50+(float(point_nend[0])-float(self.pageSettings['xmin']))/float(self.pageSettings['lmin'])*150,0) 
        if -0.001 < (x_nstart-x_nend) < 0.001:
            angle=90
        else:
            angle=math.atan((y_nend-y_nstart)/(x_nstart-x_nend))*180/math.pi
        dprint(angle)
        dict={'angle':angle,'y_pipe':y_pipe,'x_pipe':x_pipe,'y_nstart':y_nstart,'x_nstart':x_nstart,'y_nend':y_nend,'x_nend':x_nend}
        return dict
        
    #duplicated code     
    def checkDBConnected(self):
        """ Check if connected to DB"""
        dprint('check connection')
        if self.config['pwd'] and self.config['user'] and self.config['host'] and self.config['port'] and self.config['projectName'] and self.config['versionName']:
            dprint('connected!')
            return True
        else:
            dprint('not connected!')
            return False
 
    def writeNetworkTemplateIdm(self,submodel,dir,requestedOutputs,networkSimData,sensor_dec_data,networks):    
        """ write idm file with """
        dprint('write idm network model')
        dprint(networkSimData)
        simulation_data=getSimData(requestedOutputs,networkSimData)
        data=""";IDA {} Data UTF-8
(DOCUMENT-HEADER :TYPE |districts| :N \"network_{}\" :PARENT DISTRICTS :APP (DISTRICTS :VER {}))
((SCHEDULE-DATA :N "Shading" :T SCHEDULE-DATA :QT GENERIC)
 (SCHEDULE-RULE :N "rule-2" :D "rule-2" :START-DATE (NIL 5 1) :END-DATE (NIL 9 30) :VALUE ((24.0 0.86)))
 (SCHEDULE-RULE :N "default" :VALUE ((24 1)) :INDEX 1))
{}
(AGGREGATE :N GLOBAL)
((OUTPUT-FILE :N "climate" :T OUTPUT-FILE :RP T :COL T :STM 3857530591)
 (:VAR :N DIFFUSEHOR :T RADA :D "diffuseHorRad" :U |W/m2| :IV NIL :B (1 "Climate-macro" "climate_processor" IDIFFHOR))
 (:VAR :N DIRECTNORM :T RADA :D "directNormalRad" :U |W/m2| :IV NIL :B (1 "Climate-macro" "climate_processor" IDIRNORM))
 (:VAR :N IDIFF :T GENERIC :D "IDiff" :U || :IV NIL :B (1 "Climate-macro" "ISolar" INSIGNAL 1))
 (:VAR :N IDIR :T GENERIC :D "IDir" :U || :IV NIL :B (1 "Climate-macro" "Idir" INSIGNAL 1))
 (:VAR :N IDIR_VERT :T GENERIC :D "IDir_vert" :U || :IV NIL :B (1 "Climate-macro" "ISolar" INSIGNAL 2))
 (:VAR :N ITOT :T GENERIC :D "ITot" :U || :IV NIL :B (1 "Climate-macro" "ISolar" OUTSIGNAL))
 (:VAR :N TAIR :T TEMP :D "Tair" :U |Deg-C| :IV NIL :B (1 "Climate-macro" "climate_processor" TAIR))
 (:VAR :N VELOCITY :T GENERIC :D "velocity" :U || :IV NIL :B (1 "Climate-macro" "vel" |y_var|)))
((MACRO-OBJECT :N "Climate-macro" :T DISTRICTS-MACRO))
((MACRO-OBJECT :N "sf-macro" :T DISTRICTS-MACRO)){}
((MACRO-OBJECT :N "Co-simulation-macro" :T DISTRICTS-MACRO))""".format(getIDAVersion(self.config),submodel,getIDADistrictsVersion(self.config),simulation_data,
    ''.join(["""\n((MACRO-OBJECT :N "Results-macro_{}" :T DISTRICTS-MACRO){})""".format(network,
        ''.join(["""\n(:IREF :N "Int_Ref_Sensor_Target_{}" :T IN :F 208)""".format(j['iref']) 
                            for i in sensor_dec_data  if i['target_type'] ==4 
                            for j in i['irefs_target'] if j['iref'].split('_')[-1]==network]))
        for network in networks])
        )
        return data
            
    def writeNetworkTemplateIdc(self,submodel,dir,networks,supervisory_submodel):    
        """ write idc file with """
        dprint('write idc network model')
        pageSettings=PageSettings(self.cur,submodel,self.config['versionName'],networks).getPageSettings()
        dprint(pageSettings)
        data=""";IDA {} Form UTF-8
(DOCUMENT-HEADER :TYPE SCHEMA :PAGE-WIDTH {} :PAGE-HEIGHT {}){} 
(EQUATION-FRAME :AT ((265 144)) :R (20 20) :ICON "sys:eo.ids" :SLOT ("sf-macro") :NAME "sf-macro" :DATA MACRO-OBJECT) 
(EQUATION-FRAME :AT ((26 144)) :R (20 20) :ICON "sys:eo.ids" :SLOT ("Climate-macro") :NAME "Climate-macro" :DATA MACRO-OBJECT)  
(EQUATION-FRAME :AT ((170 144)) :R (20 20) :ICON "sys:eo.ids" :SLOT ("Co-simulation-macro") :NAME "Co-simulation-macro" :DATA MACRO-OBJECT)  
(EQUATION-FRAME :AT ((75 144)) :R (20 20) :ICON "sys:eo.ids" :SLOT ("Sensor-macro") :NAME "Sensor-macro" :DATA MACRO-OBJECT) 
(TEXT-OBJECT :VALUE \"Results\" :AT ((504 4) (565 18)) :STYLE LABEL) 
(LIST-FIELD :AT ((504 20) (762 100)) :SLOT (:RESULTS) :TEXT-COLOR #S(RGB RED 0 GREEN 0 BLUE 0)) 
(LABEL-TEXT :VALUE \"Project:\" :FONT (:SWISS :ARIAL 11 1) :VERTICAL :CENTER :WRAP-P NIL :AT ((12 8) (96 24))) 
(FIELD :AT ((100 8) (496 29)) :SLOT (NAME) :TEXT-COLOR #S(RGB RED 0 GREEN 0 BLUE 160) :FONT (:SWISS :ARIAL 17 2) :HELP-STRING \"NAME\" :TYPE SYMBOL) 
(LABEL-TEXT :VALUE \"Description:\" :FONT (:SWISS :ARIAL 11 1) :VERTICAL :CENTER :WRAP-P NIL :AT ((13 33) (96 53))) 
(FIELD :AT ((96 32) (496 100)) :SLOT (DESCRIPTION) :TEXT-COLOR #S(RGB RED 0 GREEN 0 BLUE 0)) 
(LINE :AT ((6 112) (743 112))){}
""".format(getIDAVersion(self.config),self.pageSettings['pageWidth'],self.pageSettings['pageHeight'],
    ''.join(["""\n(EQUATION-FRAME :AT ((218 {})) :R (20 20) :ICON "sys:eo.ids" :SLOT ("Results-macro_{}") :NAME "Results-macro_{}" :DATA MACRO-OBJECT)""".format(144+counter*50,network,network) for counter,network in enumerate(networks)]),
    """\n(EQUATION-FRAME :AT ((120 144)) :R (20 20) :ICON "sys:eo.ids" :SLOT ("Supervisory_control") :NAME "Supervisory_control" :DATA MACRO-OBJECT)""" if submodel==supervisory_submodel else '')
        return data
        #writeToFile(data,dir,dir+"""\\network_{}.idc""".format(submodel))
        
    def insertJunctions(self,submodel,requestedOutputs,modellingSettings,idm,idc,networks):
        """ Insert junctions"""
        dprint('**************insert junctions*************************')
        sql="""WITH c_counter AS (
    SELECT
        pipe_bundle_type_id,
        count(*) AS max_sequences
    FROM public.bundle_pipes
    GROUP BY pipe_bundle_type_id
),
b_pipes AS (
    SELECT
        pipe_bundle_type_id,
        count(sequence) AS numb_seq
    FROM public.bundle_pipes
    GROUP BY pipe_bundle_type_id
),
pipe_lids AS (
    SELECT
        jc.jid,
        array_agg(jc.lid ORDER BY jc.lid) AS lids,
        max(cc.max_sequences) AS max_sequences
    FROM "{}".junction_connections jc
    JOIN "{}".lines l
        ON l.id = jc.lid
    JOIN c_counter cc
        ON cc.pipe_bundle_type_id = l.pipe_bundle_type_id
    GROUP BY jc.jid
)
SELECT 
    j.id AS jid,
    ST_AsText(j.geom) AS j_point,
    j.n_connections,
    MIN(b_pipes.numb_seq) AS numb_seq,
    pipe_lids.max_sequences,
    pipe_lids.lids
FROM "{}".junctions j
JOIN "{}".junction_connections jc
    ON j.id = jc.jid
JOIN "{}".lines l
    ON l.id = jc.lid
JOIN b_pipes
    ON b_pipes.pipe_bundle_type_id = l.pipe_bundle_type_id
JOIN pipe_lids
    ON pipe_lids.jid = j.id
WHERE j.submodel = {}
  AND l.network IN ({})
GROUP BY
    j.id,
    j.geom,
    j.n_connections,
    pipe_lids.lids,
    pipe_lids.max_sequences
HAVING COUNT(DISTINCT b_pipes.numb_seq) = 1
ORDER BY j.id;""".format(self.config['versionName'],self.config['versionName'],self.config['versionName'],self.config['versionName'],self.config['versionName'],submodel,','.join([str(i) for i in networks]))# nosec B608    
        dprint(sql)
        self.cur.execute(sql)
        dprint(requestedOutputs)

        conns=self.cur.fetchall()
        if not conns:
            dprint('No nodes in network or wrong junction constructions!')
            #self.signals.error.emit(tr_msg("No junctions in network or wrong constructions!"))
            return idm,idc
            
        idm_parts=[idm]
        idc_parts=[idc]
        for conn in conns:
            dprint(conn)
            dim='('+str(conn['max_sequences'])+' '+str(conn['n_connections'])+')'
            idm_node,idc_node=self.makeNodeComponent(conn,modellingSettings,'','',dim,conn['max_sequences'],conn['jid'])
            idm_parts.append(idm_node)
            idc_parts.append(idc_node)

        return ''.join(idm_parts),''.join(idc_parts)

    def insertPlugJunctions(self,submodel,requestedOutputs,modellingSettings,idm,idc,networks,plug_dict):
        """ Insert plug junctions"""
        dprint('**************insert junctions with plugs*************************')
        sql="""WITH c_counter AS (
    SELECT
        pipe_bundle_type_id,
        count(*) AS max_sequences
    FROM public.bundle_pipes
    GROUP BY pipe_bundle_type_id
),
b_pipes AS (
    SELECT
        pipe_bundle_type_id,
        count(sequence) AS numb_seq
    FROM public.bundle_pipes
    GROUP BY pipe_bundle_type_id
),
pipe_lids AS (
    SELECT
        jc.jid,
        array_agg(jc.lid ORDER BY jc.lid) AS lids,
        max(cc.max_sequences) AS max_sequences
    FROM "{}".junction_connections jc
    JOIN "{}".lines l
        ON l.id = jc.lid
    JOIN c_counter cc
        ON cc.pipe_bundle_type_id = l.pipe_bundle_type_id
    GROUP BY jc.jid
)
SELECT 
    j.id AS jid,
    ST_AsText(j.geom) AS j_point,
    j.n_connections,
    MIN(b_pipes.numb_seq) AS numb_seq,
    pipe_lids.max_sequences,
    pipe_lids.lids
FROM "{}".junctions j
JOIN "{}".junction_connections jc
    ON j.id = jc.jid
JOIN "{}".lines l
    ON l.id = jc.lid
JOIN b_pipes
    ON b_pipes.pipe_bundle_type_id = l.pipe_bundle_type_id
JOIN pipe_lids
    ON pipe_lids.jid = j.id
WHERE j.submodel = {}
  AND l.network IN ({})
GROUP BY
    j.id,
    j.geom,
    j.n_connections,
    pipe_lids.lids,
    pipe_lids.max_sequences
HAVING COUNT(DISTINCT b_pipes.numb_seq) != 1
ORDER BY j.id;""".format(self.config['versionName'],self.config['versionName'],self.config['versionName'],self.config['versionName'],self.config['versionName'],submodel,','.join([str(i) for i in networks]))# nosec B608        
        dprint(sql)
        self.cur.execute(sql)
        dprint(requestedOutputs)
        dprint(plug_dict)

        conns=self.cur.fetchall()
        if not conns:
            dprint('No nodes in network or wrong junction constructions!')
            #self.signals.error.emit(tr_msg("No junctions in network or wrong constructions!"))
            return idm,idc

        idm_parts=[idm]
        idc_parts=[idc]
        for conn in conns:
            dprint(conn)
            m_dot=''
            if conn['jid'] in plug_dict:
                m_dot=''.join(['({} ({} -2 (|term| {} {}) 1))'.format(seq,conn['lids'].index(lid)+1,seq,conn['lids'].index(lid)+1) for lid,seqs in plug_dict[conn['jid']].items() for seq in seqs])
            dprint('m_dot: '+m_dot)
                
            inStreamT=''.join(["({} {})".format(seq,' '.join(["({})".format(str(counter_conn) + ' . 0.0' if conn['jid'] in plug_dict and [True for lid in conn['lids'] if lid in plug_dict[conn['jid']] and seq in plug_dict[conn['jid']][lid] and counter_conn == conn['lids'].index(lid)+1] else counter_conn) 
                for counter_conn in range(1,conn['n_connections']+1)])) 
                for seq in range(1,conn['max_sequences']+1)])
            dprint('instreamT: '+inStreamT)
            
            dim='('+str(conn['max_sequences'])+' '+str(conn['n_connections'])+')'
            idm_node,idc_node=self.makeNodeComponent(conn,modellingSettings,inStreamT,m_dot,dim,conn['max_sequences'],conn['jid'])
            idm_parts.append(idm_node)
            idc_parts.append(idc_node)

        return ''.join(idm_parts),''.join(idc_parts)
     
    def makeNodeComponent(self,junction,modellingSettings,inStreamT,m_dot,dim,max_seq,jid):
        """Makes the node bundle componenent; returns the idm and idc text of the component
        (the callers join all components once: appending to the whole model text per junction copies it each time)"""
        dprint(junction)
        points = junction['j_point'].split("(")[1].replace('(','').replace(')','').split(' ')
        y=round(float(self.pageSettings['pageHeight'])/0.2575-50-((float(points[1])-float(self.pageSettings['ymin']))/float(self.pageSettings['lmin'])*150),0)
        x=round(150+50+(float(points[0])-float(self.pageSettings['xmin']))/float(self.pageSettings['lmin'])*150,0)
        connector=""" ((CONNECTOR :N |term|)
  (:VAR :N |m_dot| :DIM {} :B #S(MS-SPARSE DEFAULT-VALUE NIL DIMENSION 2 VALUE ({})))
  (:VAR :N |inStream(T)| :DIM {} :B #S(MS-SPARSE DEFAULT-VALUE nil DIMENSION 2 VALUE ({}))))""".format(dim,m_dot,dim,inStreamT)
        idm="""\n((MODEL :N "NodeBundle_{}" :T |nodebundle|)
 (:par :N |n| :v {})
 (:par :N |nnodes| :v {})
{}
 ((RECORD :N |nodebdl|)
  (:PAR :N |vol| :DIM ({}) :V #({})))) """.format(jid,junction['n_connections'],max_seq,connector,max_seq,' '.join(modellingSettings['node_vol'] for x in range(0,max_seq)))
        idc="""(EQUATION-FRAME :AT (({} {})) :R (10 10) :ICON "sys:Components/DistrictsMo/symbols/nodebundle.ids" :SLOT ("NodeBundle_{}") :NAME "NodeBundle_{}" :DATA MODEL)\n""".format(x,y,jid,jid)
        return idm,idc
                
    def insertCustomers(self,submodel,idm,idc,sensor_dec_data,networks,feature_dec_irefs):
        """ insert customers; take the macro template and copy it to the IDA project"""
        dprint('****************insert customers******************')
        sql="""SELECT c.id AS cid, CASE WHEN {} = ANY(l.submodel) THEN 'same-model' ELSE 'decoupled' END AS model, ST_asText(c.geom) AS point,ca.conn_bundle_type, ca.template_name, conn_b_t.conn_bundle_type_id,conn_b_t.sequence AS conn_bundl_type_seq, conn_t_conns.connection_type_id, conn_t_conns.sequence AS conn_type_seq, conn.temp
    FROM "{}".customers c, customer_templates ca, bundle_type_conns conn_b_t, connection_type_connections conn_t_conns, connections conn, "{}".customer_connections c_conns, "{}".lines l
    WHERE c.id=c_conns.cid AND l.id=c_conns.lid AND ca.template=c.template AND
        (c.submodel={} OR {} != c.submodel AND {} = ANY (l.submodel)) AND c.network && ARRAY[{}] AND
        conn_b_t.conn_bundle_type_id=ca.conn_bundle_type AND conn_t_conns.connection_type_id=conn_b_t.conn_type_id AND
        conn_t_conns.connection_id=conn.id
    ORDER BY c.id,conn_b_t.sequence;""".format(submodel, self.config['versionName'],self.config['versionName'],self.config['versionName'],submodel,submodel,submodel,','.join([str(i) for i in networks])) # nosec B608
        dprint(sql)
        self.cur.execute(sql)
        iref=""
        i=0
        x_old=""
        y_old=""
        template_name_old=""
        cid_old=0
        customer_old=None
        iref_old=""
        cid=-1
        for customer in self.cur.fetchall():
            cid=customer['cid']
            template_name=customer['template_name']
            dprint(template_name)
            points = customer['point'].split("(")[1].replace('(','').replace(')','').split(' ')
            y=round(float(self.pageSettings['pageHeight'])/0.2575-50-((float(points[1])-float(self.pageSettings['ymin']))/float(self.pageSettings['lmin'])*150),0)
            x=round(150+50+(float(points[0])-float(self.pageSettings['xmin']))/float(self.pageSettings['lmin'])*150,0)
            
            conn_bundl_type=customer['conn_bundle_type_id']
            conn_bundl_type_seq=customer['conn_bundl_type_seq']
            conn_type=customer['connection_type_id']
            conn_type_seq=customer['conn_type_seq']
            conn_temp=customer['temp']
            
            name_conn="{}_{}_{}_{}".format(conn_bundl_type,conn_bundl_type_seq,conn_type,conn_type_seq)
            iref+="""\n (:IREF :N "{}" :F 192)""".format(name_conn)
            if cid!=cid_old and i!=0:
                dprint(cid_old)
                dprint(feature_dec_irefs)
                dprint(customer)
                dprint(conn_bundl_type)
                dprint(name_conn)
                
                idm+="""\n((MACRO-OBJECT :N "Customer_{}" :T DISTRICTS-MACRO :D "Districts macro"){}{}{})""".format(cid_old,iref_old if customer_old['model']=='same-model' else'',
                ''.join(["""\n (:IREF :N "Int_Ref_Sensor_Source_{}" :T OUT :F 224)""".format(str(i['sensor_id'])) 
                    for i in sensor_dec_data if i['measure']==5 and i['source_type']==1 for j in i['irefs_source'] if j['iref'].split('_')[1]==str(cid_old) and (j['submodel']==submodel and not j['network_side'] or j['cosim']==submodel and j['network_side'])]),
                ''.join(["""\n (:IREF :N "Int_Ref_Sensor_Target_{}" :T IN :F 208)""".format(i['sensor_id']) 
                    for i in sensor_dec_data if i['target_type']==1 for j in i['irefs_target'] if j['iref'].split('_')[1]==str(cid_old) and (j['submodel']==submodel and not j['network_side'] or j['cosim']==submodel and j['network_side'])]))
                idc+="""(EQUATION-FRAME :AT (({} {})) :R (20 20) :ICON "sys:Components/Macros/symbols/customer.ids" :SLOT ("customer_{}") :NAME "customer_{}" :DATA MACRO-OBJECT)\n""".format(x_old,y_old,cid_old,cid_old)
                iref="""\n (:IREF :N "{}" :F 192)""".format(name_conn)
            cid_old=cid
            iref_old=iref
            template_name_old=template_name
            x_old=x
            y_old=y
            customer_old=customer
            i+=1
        if cid!=-1:
            idm+="""\n((MACRO-OBJECT :N "Customer_{}" :T DISTRICTS-MACRO :D "Districts macro"){}{}{})""".format(cid,iref if customer['model']=='same-model' else'',
                    ''.join(["""\n (:IREF :N "Int_Ref_Sensor_Source_{}" :T OUT :F 224)""".format(str(i['sensor_id'])) 
                        for i in sensor_dec_data if i['measure']==5 and i['source_type']==1 for j in i['irefs_source'] if j['iref'].split('_')[1]==str(cid_old) and (j['submodel']==submodel and not j['network_side'] or j['cosim']==submodel and j['network_side'])]),
                    ''.join(["""\n (:IREF :N "Int_Ref_Sensor_Target_{}" :T IN :F 208)""".format(i['sensor_id']) 
                        for i in sensor_dec_data if i['target_type']==1 for j in i['irefs_target'] if j['iref'].split('_')[1]==str(cid_old) and (j['submodel']==submodel and not j['network_side'] or j['cosim']==submodel and j['network_side'])]))
            idc+="""(EQUATION-FRAME :AT (({} {})) :R (20 20) :ICON "sys:Components/Macros/symbols/customer.ids" :SLOT ("Customer_{}") :NAME "Customer_{}" :DATA MACRO-OBJECT)\n""".format(x,y,cid,cid)
        
        return idm,idc
        
    def insertPlants(self,submodel,idm,idc,sensor_dec_data,networks):
        """ insert plants; take the macro template and copy it to the IDA project"""
        sql="""SELECT ep.id AS epid, ST_asText(ep.geom) AS point, epa.template_name, conn_b_t.conn_bundle_type_id,conn_b_t.sequence AS conn_bundl_type_seq, conn_t_conns.connection_type_id, conn_t_conns.sequence AS conn_type_seq, conn.temp
    FROM "{}".energy_plants ep, energy_plant_templates epa, bundle_type_conns conn_b_t, connection_type_connections conn_t_conns, connections conn, "{}".lines l, "{}".energy_plant_connections ep_conns
    WHERE l.id=ep_conns.lid AND ep.id=ep_conns.epid AND epa.template=ep.template AND 
        (ep.submodel={} OR {} != ep.submodel AND {} = ANY (l.submodel)) AND
        conn_b_t.conn_bundle_type_id=epa.conn_bundle_type AND conn_t_conns.connection_type_id=conn_b_t.conn_type_id AND
        conn_t_conns.connection_id=conn.id AND ep.network && ARRAY[{}]
    ORDER BY ep.id,conn_b_t.sequence;""".format(self.config['versionName'],self.config['versionName'],self.config['versionName'],submodel,submodel,submodel,','.join([str(i) for i in networks]))# nosec B608
        dprint(sql)
        self.cur.execute(sql)
        epid=""
        iref=""
        i=0
        x_old=""
        y_old=""
        template_name_old=""
        epid_old=0
        iref_old=""
        epid=-1
        for plant in self.cur.fetchall():
            epid=plant['epid']
            points = plant['point'].split("(")[1].replace('(','').replace(')','').split(' ')
            y=round(float(self.pageSettings['pageHeight'])/0.2575-50-((float(points[1])-float(self.pageSettings['ymin']))/float(self.pageSettings['lmin'])*150),0)
            x=round(150+50+(float(points[0])-float(self.pageSettings['xmin']))/float(self.pageSettings['lmin'])*150,0)
            template_name=plant['template_name']
            conn_bundl_type=plant['conn_bundle_type_id']
            conn_bundl_type_seq=plant['conn_bundl_type_seq']
            conn_type=plant['connection_type_id']
            conn_type_seq=plant['conn_type_seq']
            conn_temp=plant['temp']
            
            name_conn="{}_{}_{}_{}".format(conn_bundl_type,conn_bundl_type_seq,conn_type,conn_type_seq)
            iref+="""\n (:IREF :N "{}" :F 192)""".format(name_conn)
            if epid!=epid_old and i!=0:
                idm+="""\n((MACRO-OBJECT :N "Energy_plant_{}" :T DISTRICTS-MACRO :D "Districts macro"){}{}{})""".format(epid_old,iref_old,
                    ''.join(["""\n (:IREF :N "Int_Ref_Sensor_Source_{}" :T OUT :F 224)""".format(str(i['sensor_id'])) 
                        for i in sensor_dec_data if i['measure']==5 and i['source_type']==2 for j in i['irefs_source'] if j['iref'].split('_')[1]==str(epid_old) and (j['submodel']==submodel and not j['network_side'] or j['cosim']==submodel and j['network_side'])]),
                    ''.join(["""\n (:IREF :N "Int_Ref_Sensor_Target_{}" :T IN :F 208)""".format(i['sensor_id']) 
                        for i in sensor_dec_data if i['target_type']==2 for j in i['irefs_target'] if j['iref'].split('_')[1]==str(epid_old) and (j['submodel']==submodel and not j['network_side'] or j['cosim']==submodel and j['network_side'])]))
                idc+="""(EQUATION-FRAME :AT (({} {})) :R (20 20) :ICON "sys:Components/EsboNmf/symbols/boil1circ.ids" :SLOT ("Energy_plant_{}") :NAME "Energy_plant_{}" :DATA MACRO-OBJECT)\n""".format(x_old,y_old,epid_old,epid_old) 
                iref="""\n (:IREF :N "{}" :F 192)""".format(name_conn)
            epid_old=epid
            iref_old=iref
            template_name_old=template_name
            x_old=x
            y_old=y
            i+=1    
        if epid!=-1:
            idm+="""\n((MACRO-OBJECT :N "Energy_plant_{}" :T DISTRICTS-MACRO :D "Districts macro"){}{}{})""".format(epid,iref,
                    ''.join(["""\n (:IREF :N "Int_Ref_Sensor_Source_{}" :T OUT :F 224)""".format(str(i['sensor_id'])) 
                        for i in sensor_dec_data if i['measure']==5 and i['source_type']==2 for j in i['irefs_source'] if j['iref'].split('_')[1]==str(epid_old) and (j['submodel']==submodel and not j['network_side'] or j['cosim']==submodel and j['network_side'])]),
                    ''.join(["""\n (:IREF :N "Int_Ref_Sensor_Target_{}" :T IN :F 208)""".format(i['sensor_id']) 
                        for i in sensor_dec_data if i['target_type']==2 for j in i['irefs_target'] if j['iref'].split('_')[1]==str(epid_old) and (j['submodel']==submodel and not j['network_side'] or j['cosim']==submodel and j['network_side'])]))
            idc+="""(EQUATION-FRAME :AT (({} {})) :R (20 20) :ICON "sys:Components/EsboNmf/symbols/boil1circ.ids" :SLOT ("energy_plant_{}") :NAME "energy_plant_{}" :DATA MACRO-OBJECT)\n""".format(x,y,epid,epid)                   
        return idm,idc


        