from qgis.PyQt.QtWidgets import QMessageBox

from .outputs import *
from .utility_functions.dialog import *
from .utility_functions.util import *
from .utility_functions.db import *
from .utility_functions.files import *
from .utility_functions.macros import *
from .utility_functions.topology import *
from .utility_functions.ida_components import *
from .utility_functions.sensor_signals import *
from .utility_functions.workers import WorkerOpenAPI
from .utility_functions.templateFiles import *
from .utility_functions.invoke import *
from .supervisory_control import Supervisory_control, CopySupervisoryControl

from .invoke_sensors import *
from .cosim import *

from multiprocessing import Process

import math
import psycopg2.extras

class WorkerBuildNetworkModel(QRunnable):
    """Worker thread
    Inherits from QRunnable to handle worker thread setup, signals and wrap-up."""
    def __init__(self,*args,**kwargs):
        super().__init__()
        #print('--WorkerBuildNetworkModel--')
        self.signals=APISignals()
        self.config=kwargs['config']
        self.dlg=kwargs['dlg']
        self.conn=""
        self.cur=""
        self.plugin_dir=kwargs['plugin_dir']
        self.conn = dbConnect(self.config,True)
        self.networks=kwargs['networks']
        self.submodels=kwargs['submodels']
        self.dlg.process_running=True

        if self.conn:
            self.cur=self.conn.cursor(cursor_factory = psycopg2.extras.RealDictCursor)
            
    @pyqtSlot()
    def run(self):
        #print('run worker invoke network')
        self.progress_value=1
        self.signals.progress.emit(self.progress_value)
        
        self.requestedOutputs=loadRequestedOutputs(self.plugin_dir,self.config)
        self.modellingSettings=loadModellingSettings(self.plugin_dir,self.config)
        self.networkSimData=loadNetworkSimData(self.plugin_dir,self.config)
        InvokeNetworkModel(self.config,self.plugin_dir,self.requestedOutputs,self.modellingSettings,self.networks,self.submodels,self.networkSimData,self.dlg.checkbox_reinvokeFeatures.checkState() == checkState(),self.signals)
        
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
        #print(sql)
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
        #print(sql)
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
        #print({'xmin': self.xmin,'ymin': self.ymin,'xmax': self.xmax,'ymax': self.xmax,'pageHeight': self.pageHeight,'pageWidth': self.pageWidth})
            
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
    def __init__(self,config,plugin_dir,requestedOutputs,modellingSettings,networks,submodels,networkSimData,reinvoke,signals):
        #print('**********invoke network*********')
        #print(submodels)
        self.plugin_dir=plugin_dir
        self.config=config
        self.conn=dbConnect(self.config,True)
        self.signals=signals
        if self.conn:
            self.cur=self.conn.cursor(cursor_factory = psycopg2.extras.RealDictCursor)

            try:
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
                #print(self.invokedOutputs)
                self.invokedOutputs['lines'] = {'v_lines': True if requestedOutputs['v_lines'] else False, 'mdot_lines': True if requestedOutputs['mdot_lines'] else False, 'p_lines': True if requestedOutputs['p_lines'] else False, 'temp_lines': True if requestedOutputs['temp_lines'] else False}
                #print(self.invokedOutputs)
   
                #setSubnetwork(self.cur,self.config)
                feature_dec_irefs=[]
                resources=[]
                
                cleanupResultsSensors(self.cur)
                added_sensor_info=addRequestedOutputsSensors(self.cur,self.config,requestedOutputs)
                #print('---added-----')
                filter=''
                sensor_data=getSensorData(self.cur,self.config,target_types=[1,2,3,4],filter=filter)               
                #print('---sensor-data-----')
                #print(sensor_data)
                

                #print(getUsedSubmodels(self.cur, self.config))
                for submodel in getUsedSubmodels(self.cur, self.config):
                    #decoupling: make macro with import/export connections for features which are connected to the submodel lines but not in the submodel  
                    #print('//////************------//////*------')
                    for i in readDecoupledFeatureSensorSignals(submodel,dir,self.config,self.cur,sensor_data):
                        #print('++++++++--++')
                        #print(i)
                        if i not in feature_dec_irefs:
                            feature_dec_irefs.append(i)
                #print(feature_dec_irefs)
                
                self.signals.progress.emit(2)
                sensor_dec_data=getSensorDecData(sensor_data,feature_dec_irefs,self.cur,self.config)      
                #print(sensor_dec_data)
                
                self.signals.progress.emit(3)
                #supervisory_submodel=str(getSupervisorySubmodel(self.cur,self.config)['submodel'])
                supervisory_submodel=str(submodels[0])
                self.signals.progress.emit(4)

                for submodel in submodels: 
                    self.pageSettings=PageSettings(self.cur,submodel,self.config['versionName'],networks).getPageSettings()
                    idm=self.writeNetworkTemplateIdm(submodel,dir,requestedOutputs,networkSimData,sensor_dec_data)
                    dec_templates=CopyDecoupledTemplateMacro(submodel,dir,self.config,self.cur,sensor_data)
                   
                    self.signals.progress.emit(int(2+3*(submodels.index(submodel)+1)/len(submodels)*97))
                    resources.extend(dec_templates.resources)
                    #print('*****************************************************************')
                    #print(dec_templates.resources)
                    
                    import_counter=dec_templates.import_counter
                    #print(import_counter)
                    
                    idc=self.writeNetworkTemplateIdc(submodel,dir,networks,supervisory_submodel)
                    createDir(dir,'network_'+str(submodel))
                    
                    #climate
                    source_dir_climateMacro=self.config['pathProjects']+self.config['projectName']+'\\climate\\climate\\'
                    target_dir_climateMacro=dir+'\\network_'+str(submodel)+'\\'
                    copyFile(source_dir_climateMacro+'climate-macro.idm',target_dir_climateMacro,target_dir_climateMacro+'climate-macro.idm')
                    copyFile(source_dir_climateMacro+'climate-macro.idc',target_dir_climateMacro,target_dir_climateMacro+'climate-macro.idc')
            
                    self.signals.progress.emit(int(2+4*(submodels.index(submodel)+1)/len(submodels)*97))
                    
                    #decoupling
                    idm+=writeCosimMacroIdm(self.config,self.cur,submodel,dir,sensor_data,sensor_dec_data)
                    writeCosimMacroIdc(self.config,self.cur,submodel,dir)
                    self.signals.progress.emit(int(2+8*(submodels.index(submodel)+1)/len(submodels)*97))
                    
                    idm_conn="\n(CONNECTIONS"
                    idc_conn=""
                    
                    #supervisory control
                    sql="""SELECT COALESCE(
    (SELECT submodel FROM supervisory_ctrl LIMIT 1),
    '1'
) AS submodel;"""
                    self.cur.execute(sql)
                    if submodel==str(self.cur.fetchone()['submodel']):
                        #print("""*-*-*-*-copy supervisory*-*-*-*-""")
                        if not os.path.exists(self.config['pathProjects']+self.config['projectName']+'\\supervisory_control\\supervisory_control.idm'):
                            Supervisory_control(self.plugin_dir,self.config)                     
                        resources.extend(CopySupervisoryControl(self.config['pathProjects']+self.config['projectName'],self.config,self.cur,submodel).resources)
                    self.signals.progress.emit(int(2+10*(submodels.index(submodel)+1)/len(submodels)*97))

                    #Sensors
                    #NetworkSensorSignals(self.cur,self.config,dir+'\\network_'+str(submodel))
                    dir_network=dir+'\\network_'+str(submodel)
                    #print('%%%%%%%&&&&&&&&&&&&&&&&%%%%%%%%%%%%%%%')
                    sensorMacroIdmData(submodel,supervisory_submodel,sensor_dec_data,sensor_data,self.cur,self.config,dir_network,import_counter)
                    sensorMacroIdcData(submodel,supervisory_submodel,sensor_dec_data,sensor_data,self.cur,self.config,dir_network,self.plugin_dir)
                    self.signals.progress.emit(int(2+12*(submodels.index(submodel)+1)/len(submodels)*97))
                    
                    #print('--')
                    idm_conn=sensorProjectIdmConns(submodel,supervisory_submodel,sensor_dec_data,idm_conn)
                    idm=sensorProjectIdmMacro(submodel,supervisory_submodel,sensor_dec_data,idm)
                    #print('-++-')

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
                        if reinvoke:
                            sql="""DELETE FROM "{}".invoked_sf WHERE type='{}';""".format(self.config['versionName'],type[:-1])# nosec B608
                            self.cur.execute(sql)
                        #print(self.signals)
                        copyTemplateMacro=CopyTemplateMacro(submodel,dir,type,self.config,self.cur,self.plugin_dir,reinvoke,self.invokedOutputs,requestedOutputs,parallize=True,signals=self.signals)
                        self.invokedOutputs[type]=copyTemplateMacro.invokedFeatureOutputs
                        resources.extend(copyTemplateMacro.resources)
                    self.signals.progress.emit(int(2+15*(submodels.index(submodel)+1)/len(submodels)*97))
                    #print('&&&&&&&&&&&&&&&&&&&&&&')
                    #print(set(resources))
                    idm+=''.join(["\n"+i for i in set(resources)])
                    
                    #sf-macro
                    writeMacroSFIdm(self.config,self.cur,dir_network)
                    writeMacroSFIdc(self.config,self.cur,dir_network)
                    self.signals.progress.emit(int(2+16*(submodels.index(submodel)+1)/len(submodels)*97))

                    #results-macro
                    writeMacroResultsIdm(self.config,self.cur,dir_network,requestedOutputs,sensor_dec_data,added_sensor_info)
                    writeMacroResultsIdc(self.config,self.cur,dir_network,requestedOutputs,sensor_dec_data,added_sensor_info)
                    self.signals.progress.emit(int(2+17*(submodels.index(submodel)+1)/len(submodels)*97))
                    
                    # Define the path to the building idm file
                    self.buildingDirPath = """{}\\{}\\""".format(dir.replace('/','\\'),'network_'+str(submodel))
                    self.buildingIdmFilePath = """{}\\{}.idm""".format(dir.replace('/','\\'),'network_'+str(submodel))
                    self.buildingIdcFilePath = """{}\\{}.idc""".format(dir.replace('/','\\'),'network_'+str(submodel))
                    
                    idm,idc=self.insertLines(submodel,requestedOutputs,modellingSettings,idm,idc,networks)
                    self.signals.progress.emit(int(2+25*(submodels.index(submodel)+1)/len(submodels)*97))
                    idm,idc=self.insertJunctions(submodel,requestedOutputs,modellingSettings,idm,idc,networks)
                    self.signals.progress.emit(int(2+35*(submodels.index(submodel)+1)/len(submodels)*97))
                    idm,idc=self.insertCustomers(submodel,idm,idc,sensor_dec_data,networks,feature_dec_irefs)
                    self.signals.progress.emit(int(2+45*(submodels.index(submodel)+1)/len(submodels)*97))
                    idm,idc=self.insertPlants(submodel,idm,idc,sensor_dec_data,networks)
                    self.signals.progress.emit(int(2+65*(submodels.index(submodel)+1)/len(submodels)*97))
                    
                    idm_conn,idc_conn=self.insertConnections(submodel,'customers',idm_conn,idc_conn,networks)
                    self.signals.progress.emit(int(2+75*(submodels.index(submodel)+1)/len(submodels)*97))
                    idm_conn,idc_conn=self.insertConnections(submodel,'energy_plants',idm_conn,idc_conn,networks)
                    self.signals.progress.emit(int(2+95*(submodels.index(submodel)+1)/len(submodels)*97))
                    idm_conn,idc_conn=self.insertJunctionConnections(submodel,idm_conn,idc_conn,networks)
                    self.signals.progress.emit(int(2+97*(submodels.index(submodel)+1)/len(submodels)*97))
                    idm_conn+=")"
                    idm+=idm_conn
                    idc+=idc_conn
                    writeToFile(idm,self.buildingDirPath,self.buildingIdmFilePath)
                    writeToFile(idc,self.buildingDirPath,self.buildingIdcFilePath)
                writeInvokedOutputs(self.config,self.invokedOutputs)
                removeResultSensors(self.cur,added_sensor_info.values())
                self.signals.progress.emit(100)  
                self.signals.finished.emit('Network model has been build successfully!')

            except Exception as e:
                self.signals.error.emit(str(e))
                #self.signals.progress.emit(0)
                
            
    def closeDocument(self):
        """Close IDA project"""
        script="""((close-document [@])
(close-unused-documents))"""
        #print(script)
        changeWallFlag = self.util.call_ida_api_function(self.util.ida_lib.runIDAScript, self.building, script.encode('utf-8'))   
    
    def openFile(self):
        """ Save the file"""
        # Open the building with the IDA Districts Python API
        self.building = self.util.call_ida_api_function(self.util.ida_lib.openDocument, self.buildingIdmFilePath.encode('utf-8'))
    
    def saveFile(self):
        """ Save the file"""
        # Save the new building using the API
        savedFile = self.util.call_ida_api_function(self.util.ida_lib.saveDocument, self.building, self.buildingFilePath.encode('utf-8'), 1) 
        
    def replaceFile(self,dir,file):
        dir_plugin_split=self.plugin_dir.split('\\')
        dir_plugins=''
        for x in range(len(dir_plungin_split)-1):
            if x!=0:
                dir_plugins+='//'
            dir_plugins+=dir_plugin_split[x]
        #print(dir_plugins)
        os.popen('copy source.txt destination.txt')         
    
    def insertLines (self,submodel,requestedOutputs,modellingSettings,idm,idc,networks):
        """ Inserts the lines in the submodel"""
        sql="""WITH sub AS (
    SELECT l.id, ST_3DLength(l.geom) AS length,
           ST_Z(ST_EndPoint(l.geom))-ST_Z(St_StartPoint(l.geom)) AS height_diff,
           COALESCE(l.zeta,0) + COALESCE(zeta.zeta_j,0) AS zeta,
           l.pipe_bundle_type_id, 
           c.counter, 
           ST_asText(ST_LineInterpolatePoint(l.geom,0.5)) AS point_pipe,
           ST_AsText(ST_StartPoint(l.geom)) AS point_start,
           ST_AsText(ST_EndPoint(l.geom)) AS point_end
    FROM "{}".lines l
    JOIN (SELECT count(*) AS counter, pipe_bundle_type_id
          FROM public.bundle_pipes GROUP BY pipe_bundle_type_id) c
      ON c.pipe_bundle_type_id = l.pipe_bundle_type_id
    JOIN (SELECT l.id, sum(j.zeta/2) AS zeta_j
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
           l.zeta
    FROM "{}".lines l
    JOIN (SELECT count(*) AS counter, pipe_bundle_type_id
          FROM public.bundle_pipes GROUP BY pipe_bundle_type_id) c
      ON c.pipe_bundle_type_id = l.pipe_bundle_type_id
    WHERE {} = ANY (l.submodel) AND l.network IN ({})
),
merged AS (
    -- compare without zeta
    SELECT id, length, height_diff, pipe_bundle_type_id, counter, point_pipe, point_start, point_end
    FROM all_lines
    EXCEPT
    SELECT id, length, height_diff, pipe_bundle_type_id, counter, point_pipe, point_start, point_end
    FROM sub
    
    UNION
    SELECT id, length, height_diff, pipe_bundle_type_id, counter, point_pipe, point_start, point_end
    FROM sub
)
-- finally, re-attach the correct zeta:
SELECT m.id, m.length, m.height_diff,
       COALESCE(s.zeta, a.zeta, 0) AS zeta,
       m.pipe_bundle_type_id, m.counter,
       m.point_pipe, m.point_start, m.point_end
FROM merged m
LEFT JOIN sub s ON s.id = m.id
LEFT JOIN all_lines a ON a.id = m.id
ORDER BY m.id;
""".format(self.config['versionName'],self.config['versionName'],self.config['versionName'],self.config['versionName'], submodel,','.join([str(i) for i in networks]),self.config['versionName'], submodel,','.join([str(i) for i in networks])) # nosec B608
        #print(sql)

        self.cur.execute(sql)
        i=1
        alpha_i=4000
        for pipe_bundle in self.cur.fetchall():
            #print(pipe_bundle)
            lid=pipe_bundle['id']
            length=pipe_bundle['length']
            bunde_type=pipe_bundle['pipe_bundle_type_id']
            npipes = pipe_bundle['counter']
            point_pipe = pipe_bundle['point_pipe'].split("(")[1][:-1].split(' ')
            point_start = pipe_bundle['point_start'].split("(")[1][:-1].split(' ')
            point_end = pipe_bundle['point_end'].split("(")[1][:-1].split(' ')
            coordinates=self.getSymbolCoordinatesAngle(point_start,point_pipe,point_end)
            zeta=pipe_bundle['zeta']
            #print(coordinates)
            
            sql="""SELECT p.innerpipediameter,p.piperoughnessfactor, bp.sequence AS se_pipe, bp.ambient, bp.x, bp.y AS depth, ARRAY_AGG(pl.sequence::text||':'|| round(pl.thickness,4)::text||':'||m.thermal_conductivity_w7mkelvin::text||':'||m.specific_heat_j7kgkelvin::text||':'||m.density_kg7m3 ORDER BY pl.sequence) AS layers
    FROM public.bundle_pipes bp, public.pipes p, public.pipe_layers pl, public.materials m
    WHERE bp.pipe_bundle_type_id={} AND bp.pipe_id=p.id AND pl.pipe_construction_id=p.pipe_construction_id AND m.id=pl.materialid
    GROUP BY p.innerpipediameter,p.piperoughnessfactor, se_pipe,bp.ambient, bp.x, bp.y
    ORDER BY bp.sequence;""".format(bunde_type) # nosec B608
            #print(sql)
            self.cur.execute(sql)
            pipe_info=self.cur.fetchall()
            if not pipe_info:
                self.signals.error.emit("Pipe construction data corrupted! PLease check construction data.")
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
            idc+="""(EQUATION-FRAME :AT (({} {})) :R (10 10) :ICON "lib:FDpipebundle.ids" :SYMMETRY {} :SLOT ("Pipebundle_{}") :NAME "Pipebundle_{}" :DATA MODEL) 
""".format(coordinates['x_pipe'],coordinates['y_pipe'],coordinates['angle'],lid,lid)
        
        return idm,idc
    
    def insertJunctionConnections(self,submodel,idm_conn,idc_conn,networks):
        """Insert the junction connections between plants or customers and pipes"""
        sql="""SELECT l.id AS lid,j.id AS jid, ST_AsText(j.geom) AS j_point,b_pipes.sequence AS seq, j.n_connections,pipe_lids.lids, c.counter AS max_seq, CASE WHEN ST_dWithIn(ST_StartPoint(l.geom),j.geom,0.0001) THEN 'liq1' ELSE 'liq2' END AS dir, ST_AsText(ST_LineInterpolatePoint(l.geom,0.5)) AS l_point
    FROM"{}".junctions j, "{}".junction_connections jc, "{}".lines l, 
        (SELECT count(*) AS counter,pipe_bundle_type_id FROM public.bundle_pipes GROUP BY pipe_bundle_type_id) c,
        (SELECT pipe_bundle_type_id,sequence FROM public.bundle_pipes) b_pipes,
        (SELECT jid, array_agg(lid ORDER BY lid) AS lids FROM "{}".junction_connections jc GROUP BY jid) pipe_lids
    WHERE pipe_lids.jid=jc.jid AND l.id=jc.lid AND j.id=jc.jid AND j.submodel={} AND l.network IN ({}) AND c.pipe_bundle_type_id=l.pipe_bundle_type_id AND b_pipes.pipe_bundle_type_id=c.pipe_bundle_type_id
    ORDER BY j.id,b_pipes.sequence, l.id;""".format(self.config['versionName'],self.config['versionName'],self.config['versionName'],self.config['versionName'],submodel,','.join([str(i) for i in networks])) # nosec B608
        #print(sql)
        self.cur.execute(sql)

        conns=self.cur.fetchall()
        if not conns:
            #print('No nodes in network or wrong junction constructions!')
            #self.signals.error.emit("No junctions in network or wrong constructions!")
            return idm_conn,idc_conn
            
        jid_old=0
        lid_old=0
        seq_old=0
        seq_counter=0
        seq_lids=[]
        for conn in conns:
            try:
                #print(conn)
                point_pipe = self.getSymbolCoordinate(conn['l_point'].split("(")[1][:-1].split(' '))
                point_j = self.getSymbolCoordinate(conn['j_point'].split("(")[1][:-1].split(' '))
                    
                if conn['seq']!=seq_old:
                    #print('--new seq--')
                    if seq_counter!=0:
                        #print(seq_lids)
                        #print([i for i in lids if i not in seq_lids])
                        #print([lids.index(i)+1 for i in lids if i not in seq_lids])
                        #print("".join(["""\n (("NodeBundle_{}" (|term| {} {})) ((:LIB WATPLUG) OUTLET) 0 0 NIL)""".format(jid_old,seq_counter,lids.index(i)+1) for i in lids if i not in seq_lids]))
                        idm_conn+="".join(["""\n (("NodeBundle_{}" (|term| {} {})) ((:LIB WATPLUG) OUTLET) 0 0 NIL)""".format(jid_old,seq_counter,lids.index(i)+1) for i in lids if i not in seq_lids])
                    seq_lids=[conn['lid']]
                    seq_counter+=1
                    conn_counter=1
                else:
                    seq_lids.append(conn['lid'])

                    
                if conn['jid']!=jid_old:
                    #print('++new jid++')
                    lids=conn['lids']
                    #print(lids)
                    conn_counter=1
                    seq_counter=1
                    max_seq=conn['max_seq']
                    pipe_counter={}
                    for lid in lids:
                        pipe_counter[lid]=0                  
                
                pipe_counter[conn['lid']]=pipe_counter[conn['lid']]+1
                
                idm_conn+="""\n (("NodeBundle_{}" (|term| {} {})) ("Pipebundle_{}" (|{}| {})) 0 0 NIL)""".format(conn['jid'],seq_counter,lids.index(conn['lid'])+1,conn['lid'],conn['dir'],pipe_counter[conn['lid']])
                idc_conn+="""\n(CONNECTION-LINE :AT (({} {}) ({} {})) :LINE-COLOR (:CALL PMT-COLOR [@ 1] [@ 2]) :LINE-STYLE 3 :FIRST-LINK ("NodeBundle_{}" 0.5 (|term| {} {})) :LAST-LINK ("Pipebundle_{}" 0.5 (|{}| {})))""".format(point_j['x'],point_j['y'],point_pipe['x'],point_pipe['y'],conn['jid'],seq_counter,lids.index(conn['lid'])+1,conn['lid'],conn['dir'],pipe_counter[conn['lid']])


                seq_old=conn['seq']
                jid_old=conn['jid']
                lid_old=conn['lid']
                conn_old=conn
                #print("seq: {}; conn: {}".format(seq_counter,conn_counter))
                conn_counter+=1
            except Exception as e:
                self.signals.error.emit("Junction connections do not match with pipe bundle sequences. Please check your pipe bundle sequences in data center --> pipe bundles.")

        idm_conn+="".join(["""\n (("NodeBundle_{}" (|term| {} {})) ((:LIB WATPLUG) OUTLET) 0 0 NIL)""".format(conn['jid'],seq_old,lids.index(i)+1) for i in lids if i not in seq_lids])
            
        return idm_conn,idc_conn
    
    def insertConnections(self,submodel,type,idm_conn,idc_conn,networks):
        """Insert the connections between features and the pipe"""
        #print("********insertConnections:"+type)
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
        #print(sql)
        
        self.cur.execute(sql)
        seq_counter=1
        lid_old=0
        for conn in self.cur.fetchall():
            #print(conn)
            lid=conn['lid']
            did=conn['fid']
            if lid!=lid_old:
                seq_counter=1
            point_pipe = self.getSymbolCoordinate(conn['l_point'].split("(")[1][:-1].split(' '))
            point_d = self.getSymbolCoordinate(conn['f_point'].split("(")[1][:-1].split(' '))
            conn_bundl_type=conn['conn_bundle_type_id']
            conn_bundl_type_seq=conn['conn_bundl_type_seq']
            conn_type=conn['connection_type_id']
            conn_type_seq=conn['conn_type_seq']
            conn_temp=conn['temp']
            conn_dir=conn['dir']
            
            name_conn="{}_{}_{}_{}".format(conn_bundl_type,conn_bundl_type_seq,conn_type,conn_type_seq)

            idm_conn+="""\n (("{}_{}" "{}") ("Pipebundle_{}" (|{}| {})) 0 0 NIL)""".format(type[:-1].capitalize(),did,name_conn,lid,conn_dir,seq_counter)
            idc_conn+="""\n(CONNECTION-LINE :AT (({} {}) ({} {})) :LINE-COLOR (:CALL PMT-COLOR [@ 1] [@ 2]) :LINE-STYLE 3 :FIRST-LINK ("{}_{}" 0.5 "{}") :LAST-LINK ("Pipebundle_{}" 0.5 (|{}| {})))""".format(point_d['x'],point_d['y'],point_pipe['x'],point_pipe['y'],type[:-1].capitalize(),did,name_conn,lid,conn_dir,seq_counter)

            seq_counter+=1
            lid_old=lid
            
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
        #print(angle)
        dict={'angle':angle,'y_pipe':y_pipe,'x_pipe':x_pipe,'y_nstart':y_nstart,'x_nstart':x_nstart,'y_nend':y_nend,'x_nend':x_nend}
        return dict
        
    #duplicated code     
    def checkDBConnected(self):
        """ Check if connected to DB"""
        #print('check connection')
        if self.config['pwd'] and self.config['user'] and self.config['host'] and self.config['port'] and self.config['projectName'] and self.config['versionName']:
            #print('connected!')
            return True
        else:
            #print('not connected!')
            return False
 
    def writeNetworkTemplateIdm(self,submodel,dir,requestedOutputs,networkSimData,sensor_dec_data):    
        """ write idm file with """
        #print('write idm network model')
        #print(networkSimData)
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
((MACRO-OBJECT :N "sf-macro" :T DISTRICTS-MACRO))
((MACRO-OBJECT :N "Results-macro" :T DISTRICTS-MACRO){})
((MACRO-OBJECT :N "Co-simulation-macro" :T DISTRICTS-MACRO))""".format(getIDAVersion(self.config),submodel,getIDADistrictsVersion(self.config),simulation_data,
    ''.join(["""\n(:IREF :N "Int_Ref_Sensor_Target_{}" :T IN :F 208)""".format(j['iref']) 
                        for i in sensor_dec_data  if i['target_type'] ==4 
                        for j in i['irefs_target']]))
        return data
            
    def writeNetworkTemplateIdc(self,submodel,dir,networks,supervisory_submodel):    
        """ write idc file with """
        #print('write idc network model')
        pageSettings=PageSettings(self.cur,submodel,self.config['versionName'],networks).getPageSettings()
        #print(pageSettings)
        data=""";IDA {} Form UTF-8
(DOCUMENT-HEADER :TYPE SCHEMA :PAGE-WIDTH {} :PAGE-HEIGHT {})
(EQUATION-FRAME :AT ((218 144)) :R (20 20) :ICON "sys:eo.ids" :SLOT ("Results-macro") :NAME "Results-macro" :DATA MACRO-OBJECT) 
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
""".format(getIDAVersion(self.config),self.pageSettings['pageWidth'],self.pageSettings['pageHeight'],"""\n(EQUATION-FRAME :AT ((120 144)) :R (20 20) :ICON "sys:eo.ids" :SLOT ("Supervisory_control") :NAME "Supervisory_control" :DATA MACRO-OBJECT)""" if submodel==supervisory_submodel else '')
        return data
        #writeToFile(data,dir,dir+"""\\network_{}.idc""".format(submodel))
        
    def insertJunctions(self,submodel,requestedOutputs,modellingSettings,idm,idc,networks):
        """ Insert junctions"""
        #print('**************insert junctions*************************')
        sql="""SELECT l.id AS lid,j.id AS jid, ST_AsText(j.geom) AS j_point,b_pipes.sequence AS seq, j.n_connections,pipe_lids.lids, c.counter AS max_seq
    FROM"{}".junctions j, "{}".junction_connections jc, "{}".lines l, 
        (SELECT count(*) AS counter,pipe_bundle_type_id FROM public.bundle_pipes GROUP BY pipe_bundle_type_id) c,
        (SELECT pipe_bundle_type_id,sequence FROM public.bundle_pipes) b_pipes,
        (SELECT jid, array_agg(lid ORDER BY lid) AS lids FROM "{}".junction_connections jc GROUP BY jid) pipe_lids
    WHERE pipe_lids.jid=jc.jid AND l.id=jc.lid AND j.id=jc.jid AND j.submodel={} AND l.network IN ({}) AND c.pipe_bundle_type_id=l.pipe_bundle_type_id AND b_pipes.pipe_bundle_type_id=c.pipe_bundle_type_id
    ORDER BY j.id,b_pipes.sequence, l.id;""".format(self.config['versionName'],self.config['versionName'],self.config['versionName'],self.config['versionName'],submodel,','.join([str(i) for i in networks]))# nosec B608
        #print(sql)
        self.cur.execute(sql)
        #print(requestedOutputs)

        conns=self.cur.fetchall()
        if not conns:
            #print('No nodes in network or wrong junction constructions!')
            #self.signals.error.emit("No junctions in network or wrong constructions!")
            return idm,idc
            
        inStreamT=''
        m_dot=''
        jid_old=0
        lid_old=0
        seq_old=0
        seq_counter=0
        for conn in conns:
            try:
                #print(conn)
                #print('instreamT: '+inStreamT)
                #print('m_dot: '+m_dot)
                    
                if conn['seq']!=seq_old:
                    #print('--new seq--')
                    if seq_counter!=0:
                        #print('--conn_counter: {}; len(lids): {}'.format(conn_counter,len(lids)))
                        for i in range(conn_counter,len(lids)+1):
                            #print('--add connection: '+str(i))
                            inStreamT+=" ("+str(conn_counter)+" . 0.0)"
                            m_dot+='({} ({} -2 (|term| {} {}) 1))'.format(seq_counter,conn_counter,seq_counter,conn_counter)
                    seq_counter+=1
                    conn_counter=1
                    if seq_counter!=1:
                        inStreamT+=')'
                    if conn['jid']==jid_old:
                        inStreamT+='('+str(seq_counter)   
                    
                if conn['jid']!=jid_old:
                    #print('++new jid++')
                    lids=conn['lids']
                    #print(lids)
                    if jid_old!=0:
                        dim='('+str(seq_counter-1)+' '+str(len(lids))+')'
                        idm,idc=self.makeNodeComponent(conn_old,idm,idc,modellingSettings,inStreamT,m_dot,dim,max_seq,jid_old)
                    conn_counter=1
                    seq_counter=1
                    max_seq=conn['max_seq']
                    inStreamT='('+str(seq_counter)
                    m_dot=''
                  
                if lids[conn_counter-1]!=conn['lid']:
                    #print('++lids[conn_counter-1]: {}; conn[lid]: {}'.format(lids[conn_counter-1],conn['lid']))
                    #print('++conn_counter: {}; lids.index(conn[lid]): {}'.format(conn_counter,lids.index(conn['lid'])))
                    for i in range(conn_counter,lids.index(conn['lid'])+1):
                        #print('++'+str(i))
                        inStreamT+=" ("+str(conn_counter)+" . 0.0)"
                        m_dot+='({} ({} -2 (|term| {} {}) 1))'.format(seq_counter,conn_counter,seq_counter,conn_counter)
                        conn_counter+=1
                
                inStreamT+=" ("+str(conn_counter)+")"

                seq_old=conn['seq']
                jid_old=conn['jid']
                lid_old=conn['lid']
                if max_seq<conn['max_seq']:
                    max_seq=conn['max_seq']
                conn_old=conn
                #print("seq: {}; conn: {}".format(seq_counter,conn_counter))
                conn_counter+=1
            except Exception as e:
                self.signals.error.emit(str(e))
        
        #print(inStreamT)
        #print('--conn_counter: {}; len(lids): {}'.format(conn_counter,len(lids)))
        for i in range(conn_counter,len(lids)+1):
            #print('--add connection: '+str(i))
            inStreamT+=" ("+str(conn_counter)+" . 0.0)"
            m_dot+='({} ({} -2 (|term| {} {}) 1))'.format(seq_counter,conn_counter,seq_counter,conn_counter)
        inStreamT+=')'
        #print(inStreamT)
        #print(m_dot)
        dim='('+str(seq_counter)+' '+str(len(lids))+')'
        idm,idc=self.makeNodeComponent(conn,idm,idc,modellingSettings,inStreamT,m_dot,dim,max_seq,jid_old)
        return idm,idc
     
    def makeNodeComponent(self,junction,idm,idc,modellingSettings,inStreamT,m_dot,dim,max_seq,jid):
        """Makes the node bundle componenent"""
        #print(junction)
        points = junction['j_point'].split("(")[1].replace('(','').replace(')','').split(' ')
        y=round(float(self.pageSettings['pageHeight'])/0.2575-50-((float(points[1])-float(self.pageSettings['ymin']))/float(self.pageSettings['lmin'])*150),0)
        x=round(150+50+(float(points[0])-float(self.pageSettings['xmin']))/float(self.pageSettings['lmin'])*150,0)
        connector=""" ((CONNECTOR :N |term|)
  (:VAR :N |m_dot| :DIM {} :B #S(MS-SPARSE DEFAULT-VALUE NIL DIMENSION 2 VALUE ({})))
  (:VAR :N |inStream(T)| :DIM {} :B #S(MS-SPARSE DEFAULT-VALUE nil DIMENSION 2 VALUE ({}))))""".format(dim,m_dot,dim,inStreamT)
        idm+="""\n((MODEL :N "NodeBundle_{}" :T |nodebundle|)
 (:par :N |n| :v {})
 (:par :N |nnodes| :v {})
{}
 ((RECORD :N |nodebdl|)
  (:PAR :N |vol| :DIM ({}) :V #({})))) """.format(jid,junction['n_connections'],max_seq,connector,max_seq,' '.join(modellingSettings['node_vol'] for x in range(0,max_seq)))
        idc+="""\n(EQUATION-FRAME :AT (({} {})) :R (10 10) :ICON "lib:nodebundle.ids" :SLOT ("NodeBundle_{}") :NAME "NodeBundle_{}" :DATA MODEL)""".format(x,y,jid,jid)
        return idm,idc
                
    def insertCustomers(self,submodel,idm,idc,sensor_dec_data,networks,feature_dec_irefs):
        """ insert customers; take the macro template and copy it to the IDA project"""
        #print('****************insert customers******************')
        sql="""SELECT c.id AS cid, CASE WHEN {} = ANY(l.submodel) THEN 'same-model' ELSE 'decoupled' END AS model, ST_asText(c.geom) AS point,ca.conn_bundle_type, ca.template_name, conn_b_t.conn_bundle_type_id,conn_b_t.sequence AS conn_bundl_type_seq, conn_t_conns.connection_type_id, conn_t_conns.sequence AS conn_type_seq, conn.temp
	FROM "{}".customers c, customer_templates ca, bundle_type_conns conn_b_t, connection_type_connections conn_t_conns, connections conn, "{}".customer_connections c_conns, "{}".lines l
	WHERE c.id=c_conns.cid AND l.id=c_conns.lid AND ca.template=c.template AND
        (c.submodel={} OR {} != c.submodel AND {} = ANY (l.submodel)) AND c.network && ARRAY[{}] AND
        conn_b_t.conn_bundle_type_id=ca.conn_bundle_type AND conn_t_conns.connection_type_id=conn_b_t.conn_type_id AND
        conn_t_conns.connection_id=conn.id
	ORDER BY c.id,conn_b_t.sequence;""".format(submodel, self.config['versionName'],self.config['versionName'],self.config['versionName'],submodel,submodel,submodel,','.join([str(i) for i in networks])) # nosec B608
        #print(sql)
        self.cur.execute(sql)
        iref=""
        i=0
        x_old=""
        y_old=""
        template_name_old=""
        cid_old=0
        iref_old=""
        cid=-1
        for customer in self.cur.fetchall():
            cid=customer['cid']
            template_name=customer['template_name']
            #print(template_name)
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
                #print('#####++++++-------------------------')
                #print(cid_old)
                #print(feature_dec_irefs)
                #print(customer)
                #print(conn_bundl_type)
                #print(name_conn)
                
                idm+="""\n((MACRO-OBJECT :N "Customer_{}" :T DISTRICTS-MACRO :D "Districts macro"){}{}{})""".format(cid_old,iref_old if customer_old['model']=='same-model' else'',
                ''.join(["""\n (:IREF :N "Int_Ref_Sensor_Source_{}" :T OUT :F 224)""".format(str(i['sensor_id'])) 
                    for i in sensor_dec_data if i['measure']==5 and i['source_type']==1 for j in i['irefs_source'] if j['iref'].split('_')[1]==str(cid_old) and (j['submodel']==submodel and not j['network_side'] or j['cosim']==submodel and j['network_side'])]),
                ''.join(["""\n (:IREF :N "Int_Ref_Sensor_Target_{}" :T IN :F 208)""".format(i['sensor_id']) 
                    for i in sensor_dec_data if i['target_type']==1 for j in i['irefs_target'] if j['iref'].split('_')[1]==str(cid_old) and (j['submodel']==submodel and not j['network_side'] or j['cosim']==submodel and j['network_side'])]))
                idc+="""\n(EQUATION-FRAME :AT (({} {})) :R (20 20) :ICON "lib:customer.ids" :SLOT ("customer_{}") :NAME "customer_{}" :DATA MACRO-OBJECT)""".format(x_old,y_old,cid_old,cid_old)
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
            idc+="""\n(EQUATION-FRAME :AT (({} {})) :R (20 20) :ICON "lib:customer.ids" :SLOT ("Customer_{}") :NAME "Customer_{}" :DATA MACRO-OBJECT)""".format(x,y,cid,cid)
        
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
        #print(sql)
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
                idc+="""\n(EQUATION-FRAME :AT (({} {})) :R (20 20) :ICON "lib:boil1circ.ids" :SLOT ("Energy_plant_{}") :NAME "Energy_plant_{}" :DATA MACRO-OBJECT) """.format(x_old,y_old,epid_old,epid_old) 
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
            idc+="""\n(EQUATION-FRAME :AT (({} {})) :R (20 20) :ICON "lib:boil1circ.ids" :SLOT ("energy_plant_{}") :NAME "energy_plant_{}" :DATA MACRO-OBJECT) """.format(x,y,epid,epid)                   
        return idm,idc


        