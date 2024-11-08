from plugins.utility_functions.util import *
from plugins.utility_functions.db import *
from plugins.utility_functions.files import *
from plugins.utility_functions.macros import *
from plugins.utility_functions.topology import *
from plugins.utility_functions.ida_components import *

from plugins.utility_functions.assettypeFiles import *
from .supervisory_control import Supervisory_control, CopySupervisoryControl
from .invoke_sensors import *
from .cosim import *
from .invoke import *
from plugins.utility_functions.sensor_signals import *
from plugins.utility_functions.workerOpenAPI import WorkerOpenAPI

from multiprocessing import Process
from qgis.PyQt.QtWidgets import QMessageBox

import math
import psycopg2.extras

class PageSettings:
    def __init__(self,cur,submodel,versionName,networks):
        sql="""WITH sub AS(    
    SELECT ST_XMin(ST_Union(geom)) as xmin, ST_YMin(ST_Union(geom)) as ymin,ST_XMax(ST_Union(geom)) as xmax, ST_YMax(ST_Union(geom)) as ymax FROM {}.dhc_lines  WHERE {} = ANY (submodel) AND network IN ({})
    UNION
    SELECT ST_XMin(ST_Union(geom)) as xmin, ST_YMin(ST_Union(geom)) as ymin,ST_XMax(ST_Union(geom)) as xmax, ST_YMax(ST_Union(geom)) as ymax FROM {}.dhc_customers WHERE {} = submodel AND network <@ array[{}] 
    UNION
    SELECT ST_XMin(ST_Union(geom)) as xmin, ST_YMin(ST_Union(geom)) as ymin,ST_XMax(ST_Union(geom)) as xmax, ST_YMax(ST_Union(geom)) as ymax FROM {}.dhc_energy_plants WHERE {} = submodel AND network <@ array[{}] 
)
SELECT min(xmin) AS xmin, min(ymin) AS ymin ,max(xmax) AS xmax, max(ymax) AS ymax FROM sub;""".format(versionName,str(submodel),','.join([str(i) for i in networks]),versionName,str(submodel),','.join([str(i) for i in networks]),versionName,str(submodel),','.join([str(i) for i in networks]));
        print(sql)
        cur.execute(sql)
        settings=cur.fetchone()
        self.xmin=settings['xmin']
        self.ymin=settings['ymin']
        self.xmax=settings['xmax']
        self.ymax=settings['ymax']

        sql="""WITH sub AS(
    SELECT Min(ST_Length(geom)) AS lmin FROM {}.dhc_lines WHERE {} = ANY (submodel) AND network IN ({})
    UNION
    SELECT min(ST_Distance(c1.geom, c2.geom)) AS lmin FROM {}.dhc_customers c1, {}.dhc_customers c2 WHERE c1.id <> c2.id AND {} = c1.submodel AND {} = c2.submodel
    UNION
    SELECT min(ST_Distance(ep1.geom, ep2.geom)) AS lmin FROM {}.dhc_energy_plants ep1, {}.dhc_energy_plants ep2 WHERE ep1.id <> ep2.id AND {} = ep1.submodel AND {} = ep2.submodel
    UNION
    SELECT min(ST_Distance(ep.geom, c.geom)) AS lmin FROM {}.dhc_energy_plants ep, {}.dhc_customers c WHERE {} = ep.submodel AND {} = c.submodel
)
SELECT min(lmin) AS lmin FROM sub;""".format(versionName,submodel,','.join([str(i) for i in networks]),versionName,versionName,submodel,submodel,versionName,versionName,submodel,submodel,versionName,versionName,submodel,submodel);
        print(sql)
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
        #print({'xmin':xmin,'ymin':ymin,'xmax':xmax,'ymax':xmax,'pageHeight':pageHeight,'pageWidth':pageWidth})
            
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
    def __init__(self,dir,requestedOutputs,modellingSettings,iface,networks,submodels,networkSimData,reinvoke):
        print('**********invoke network*********')
        self.plugin_dir=dir
        self.dictDB=getDBConnectionData(self.plugin_dir)
        self.conn=dbConnect(self.dictDB,True)
        if self.conn:
            self.cur=self.conn.cursor(cursor_factory = psycopg2.extras.RealDictCursor)
            self.projectConfig=loadProjectConfig(self.plugin_dir,self.dictDB['projectName'])
            self.configIDADistricts=loadIDADistrictsConfig(self.plugin_dir)
            dir+='\\network_models'
            createDir(dir,self.dictDB['projectName'])
            dir+='\\'+self.dictDB['projectName']
            createDir(dir,self.dictDB['versionName'])
            dir+='\\'+self.dictDB['versionName']
            
            #clean dir
            for submodel in submodels:
                self.buildingDirPath = """{}\\{}""".format(dir.replace('/','\\'),'network_'+str(submodel))
                removeFilesInDir(self.buildingDirPath)
                
            #simulated outputs
            self.invokedOutputs=loadInvokedOutputs(self.plugin_dir,self.dictDB)
            print(self.invokedOutputs)
            self.invokedOutputs['dhc_lines'] = {'v_lines': True if requestedOutputs['v_lines'] else False, 'mdot_lines': True if requestedOutputs['mdot_lines'] else False, 'p_lines': True if requestedOutputs['p_lines'] else False, 'temp_lines': True if requestedOutputs['temp_lines'] else False}
            print(self.invokedOutputs)


                
            #setSubnetwork(self.cur,self.dictDB)
            feature_dec_irefs=[]
            resources=[]
            filter=''
            sensor_data=getSensorData(self.cur,self.dictDB,filter=filter)
            print(sensor_data)

            print(getUsedSubmodels(self.cur, self.dictDB))
            for submodel in getUsedSubmodels(self.cur, self.dictDB):
                self.buildingDirPath = """{}\\{}\\""".format(dir.replace('/','\\'),'network_'+str(submodel))
                #decoupling: make macro with import/export connections for features which are connected to the submodel lines but not in the submodel  
                print('//////************------//////*------')
                for i in readDecoupledFeatureSensorSignals(submodel,dir,self.dictDB,self.cur,iface,self.plugin_dir,sensor_data):
                    print('++++++++--++')
                    print(i)
                    if i not in feature_dec_irefs:
                        feature_dec_irefs.append(i)
                
            print(feature_dec_irefs)
            
            sensor_dec_data=getSensorDecData(sensor_data,feature_dec_irefs,self.cur,self.dictDB)      
            supervisory_submodel=str(getSupervisorySubmodel(self.cur,self.dictDB)['submodel'])
            
            for submodel in submodels: 
                print(submodel)
                self.pageSettings=PageSettings(self.cur,submodel,self.dictDB['versionName'],networks).getPageSettings()
                idm=self.writeNetworkTemplateIdm(submodel,dir,requestedOutputs,networkSimData)
                dec_assettypes=CopyDecoupledAssettypeMacro(submodel,dir,self.dictDB,self.cur,iface,self.plugin_dir,sensor_data)
                resources.extend(dec_assettypes.resources)
                print('*****************************************************************')
                print(dec_assettypes.resources)
                
                import_counter=dec_assettypes.import_counter
                print('*-+')
                print(import_counter)
                
                idc=self.writeNetworkTemplateIdc(submodel,dir,networks,supervisory_submodel)
                
                createDir(dir,'network_'+str(submodel))
                #climate
                writeMacroClimateIdm(self.dictDB,self.cur,'network_'+str(submodel),dir,self.plugin_dir,loadModellingSettings(self.plugin_dir,self.dictDB),getClimateData(self.cur,self.dictDB,True))
                writeMacroClimateIdc('network_'+str(submodel),dir,loadModellingSettings(self.plugin_dir,self.dictDB))
                
                #sf-macro
                self.writeMacroSFIdm(dir+'\\'+'network_'+str(submodel))
                self.writeMacroSFIdc(dir+'\\'+'network_'+str(submodel))
                
                #decoupling
                idm+=writeCosimMacroIdm(self.dictDB,self.cur,submodel,dir,self.plugin_dir,sensor_data,sensor_dec_data)
                writeCosimMacroIdc(self.dictDB,self.cur,submodel,dir,self.plugin_dir)
                
                idm_conn="\n(CONNECTIONS"
                idc_conn=""
                
                #supervisory control
                sql="""SELECT submodel from {}.supervisory_ctrl;""".format(self.dictDB['versionName'])
                self.cur.execute(sql)
                if submodel==str(self.cur.fetchone()['submodel']):
                    """*-*-*-*-copy supervisory*-*-*-*-"""
                    if not os.path.exists(dir+'\\supervisory_control\\supervisory_control.idm'):
                        Supervisory_control(self.plugin_dir)                     
                    resources.extend(CopySupervisoryControl(dir,self.dictDB,self.cur,submodel).resources)
               
                #Sensors
                #NetworkSensorSignals(self.cur,self.dictDB,dir+'\\network_'+str(submodel))
                dir=dir+'\\network_'+str(submodel)
                print('%%%%%%%&&&&&&&&&&&&&&&&%%%%%%%%%%%%%%%')
                sensorMacroIdmData(submodel,supervisory_submodel,sensor_dec_data,sensor_data,self.cur,self.dictDB,dir)
                sensorMacroIdcData(submodel,supervisory_submodel,sensor_dec_data,sensor_data,self.cur,self.dictDB,dir,self.plugin_dir)
                
                dir=self.plugin_dir+"""\\network_models\\{}\\{}""".format(self.dictDB['projectName'],self.dictDB['versionName'])
                idm_conn=sensorProjectIdmConns(submodel,supervisory_submodel,sensor_dec_data,idm_conn)
                idm=sensorProjectIdmMacro(submodel,supervisory_submodel,sensor_dec_data,idm)
                 
                #----------------supervisory ctrl------------------------
                if submodel==supervisory_submodel:
                    idm+="""\n((MACRO-OBJECT :N "Supervisory_control" :T ICE-MACRO :ETM 3857526820 :STM 3857526845){}{}{})""".format(
                        #iref sources if source type is supervisory ctrl (4) and function == Same signal for all targets (5))
                        ''.join(["""\n (:IREF :N "Int_Ref_Sensor_Source_{}" :T OUT :F 224)""".format(j['iref']) 
                            for i in sensor_dec_data if i['source_type']==4 and i['function']==5 for j in i['irefs_source']]),  
                        #iref sources if source type is supervisory ctrl (4) and function == Individual signals for each target (6)
                        ''.join(["""\n (:IREF :N "Int_Ref_Sensor_Source_{}" :T OUT :F 224)""".format(j['iref']) 
                            for i in sensor_dec_data if i['source_type']==4 and i['function']==6 for j in i['irefs_target']]),  
                        #iref targets connections from Sensor to feature if type Supervisory Ctrl (4) 
                        ''.join(["""\n (:IREF :N "Int_Ref_Sensor_Target_{}" :T IN :F 208)""".format(j['iref']) 
                            for i in sensor_dec_data if i['target_type']==4 for j in i['irefs_target']]))                

                if reinvoke:
                    sql="""TRUNCATE {}.invoked_sf;
SELECT setval('{}.invoked_sf_id_seq', 1, false);""".format(self.dictDB['versionName'],self.dictDB['versionName'])
                    self.cur.execute(sql)
                for type in ["dhc_customers","dhc_energy_plants","dhc_devices"]:
                    copyAssettypeMacro=CopyAssettypeMacro(submodel,dir,type,self.dictDB,self.cur,iface,self.plugin_dir,reinvoke,self.invokedOutputs,requestedOutputs)
                    if type!="dhc_devices":
                        self.invokedOutputs[type]=copyAssettypeMacro.invokedFeatureOutputs
                    resources.extend(copyAssettypeMacro.resources)                   
                print('&&&&&&&&&&&&&&&&&&&&&&')
                print(set(resources))
                idm+=''.join(["\n"+i for i in set(resources)])
                
                # Define the path to the building idm file
                self.buildingIdmFilePath = """{}\\{}.idm""".format(dir.replace('/','\\'),'network_'+str(submodel))
                self.buildingIdcFilePath = """{}\\{}.idc""".format(dir.replace('/','\\'),'network_'+str(submodel))
                
                idm,idc=self.insertLines(submodel,requestedOutputs,modellingSettings,idm,idc,networks)
                idm,idc=self.insertJunctions(submodel,requestedOutputs,modellingSettings,idm,idc,networks)
                idm,idc=self.insertCustomers(submodel,idm,idc,sensor_dec_data,networks,feature_dec_irefs)
                idm,idc=self.insertDevices(submodel,idm,idc,networks)
                idm,idc=self.insertPlants(submodel,idm,idc,sensor_dec_data,networks)
                
                idm_conn,idc_conn=self.insertConnections(submodel,'dhc_customers',idm_conn,idc_conn,networks)
                idm_conn,idc_conn=self.insertConnections(submodel,'dhc_devices',idm_conn,idc_conn,networks)
                idm_conn,idc_conn=self.insertConnections(submodel,'dhc_energy_plants',idm_conn,idc_conn,networks)
                idm_conn,idc_conn=self.insertJunctionConnections(submodel,idm_conn,idc_conn,networks)
                idm_conn+=")"
                idm+=idm_conn
                idc+=idc_conn
                writeToFile(idm,self.buildingDirPath,self.buildingIdmFilePath)
                writeToFile(idc,self.buildingDirPath,self.buildingIdcFilePath)  
                    
            writeInvokedOutputs(self.plugin_dir,self.dictDB,self.invokedOutputs)
            
    def closeDocument(self):
        """Close IDA project"""
        script="""((close-document [@])
(close-unused-documents))"""
        print(script)
        changeWallFlag = self.util.call_ida_api_function(self.util.ida_lib.runIDAScript, self.building, script.encode('ascii'))   
    
    def openFile(self):
        """ Save the file"""
        # Open the building with the IDA ICE Python API
        self.building = self.util.call_ida_api_function(self.util.ida_lib.openDocument, self.buildingIdmFilePath.encode('ascii'))
    
    def saveFile(self):
        """ Save the file"""
        # Save the new building using the API
        savedFile = self.util.call_ida_api_function(self.util.ida_lib.saveDocument, self.building, self.buildingFilePath.encode('ascii'), 1) 
        
    def replaceFile(self,dir,file):
        dir_plugin_split=self.plugin_dir.split('\\')
        dir_plugins=''
        for x in range(len(dir_plungin_split)-1):
            if x!=0:
                dir_plugins+='//'
            dir_plugins+=dir_plugin_split[x]
        #print (dir_plugins)
        os.popen('copy source.txt destination.txt')         
    
    def insertLines (self,submodel,requestedOutputs,modellingSettings,idm,idc,networks):
        """ Inserts the lines in the submodel"""
        sql="""WITH sub AS(
    SELECT l.id, l.length,ST_Z(ST_EndPoint(l.geom))-ST_Z(St_StartPoint(l.geom)) AS height_diff, l.zeta +zeta.zeta_j AS zeta, l.pipe_bundle_type_id, c.counter, 
        ST_asText(ST_LineInterpolatePoint(l.geom,0.5)) AS point_pipe,ST_AsText(ST_StartPoint(l.geom)) AS point_start,ST_AsText(ST_EndPoint(l.geom)) AS point_end
    FROM {}.dhc_lines l,
    (SELECT count(*) AS counter,pipe_bundle_type_id FROM public.bundle_pipes GROUP BY pipe_bundle_type_id) c,
    (SELECT l.id, sum(j.zeta/2) AS zeta_j FROM {}.dhc_lines l, {}.dhc_junctions j, {}.junction_connections jc WHERE l.id=jc.lid AND jc.jid=j.id GROUP BY l.id) zeta
    WHERE {} = ANY (l.submodel) AND c.pipe_bundle_type_id = l.pipe_bundle_type_id AND zeta.id=l.id AND l.network IN ({})
)
--get line id`s without connection to dhc_junctions
SELECT l.id, l.length,ST_Z(ST_EndPoint(l.geom))-ST_Z(St_StartPoint(l.geom)) AS height_diff, l.zeta AS zeta, l.pipe_bundle_type_id, c.counter, 
        ST_asText(ST_LineInterpolatePoint(l.geom,0.5)) AS point_pipe,ST_AsText(ST_StartPoint(l.geom)) AS point_start,ST_AsText(ST_EndPoint(l.geom)) AS point_end
    FROM {}.dhc_lines l,
    (SELECT count(*) AS counter,pipe_bundle_type_id FROM public.bundle_pipes GROUP BY pipe_bundle_type_id) c
    WHERE {} = ANY (l.submodel) AND c.pipe_bundle_type_id = l.pipe_bundle_type_id AND l.network IN ({})
EXCEPT  
SELECT * FROM sub
--merge with line id`s, which are connected to dhc_junctions
UNION
SELECT * FROM sub
ORDER BY id;""".format(self.dictDB['versionName'],self.dictDB['versionName'],self.dictDB['versionName'],self.dictDB['versionName'], submodel,','.join([str(i) for i in networks]),self.dictDB['versionName'], submodel,','.join([str(i) for i in networks]))
        print(sql)
        self.cur.execute(sql)
        i=1
        alpha_i=4000 #alpha_water=4000 W/m2K ; 1 m/s Strömung
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
            
            sql="""SELECT p.innerpipediameter,p.piperoughnessfactor, bp.sequence AS se_pipe, bp.ambient, ARRAY_AGG(pl.sequence::text||':'|| round(pl.thickness,4)::text||':'||m.thermal_conductivity_w7mkelvin::text||':'||m.specific_heat_j7kgkelvin::text||':'||m.density_kg7m3 ORDER BY pl.sequence) AS layers
    FROM public.bundle_pipes bp, public.pipes p, public.pipe_layers pl, public.materials m
    WHERE bp.pipe_bundle_type_id={} AND bp.pipe_id=p.id AND pl.pipe_construction_id=p.pipe_construction_id AND m.id=pl.materialid
    GROUP BY p.innerpipediameter,p.piperoughnessfactor, se_pipe,bp.ambient
    ORDER BY bp.sequence;""".format(bunde_type)
            print(sql)
            self.cur.execute(sql)
            pipe_info=self.cur.fetchall()
            dPipes=[i['innerpipediameter'] for i in pipe_info]
            roughness=' '.join(str(i['piperoughnessfactor']) for i in pipe_info)
            layers=pipe_info[0]['layers']
            thickness=layers[0].split(':')[1]
            lambda_=layers[0].split(':')[2]
            cp=layers[0].split(':')[3]
            rho=layers[0].split(':')[4]                   
            
            if pipe_info[0]['ambient']==1: #air
                alpha_o=20 #air
                tamb_conn=' (:VAR :N |TAmb| :B (1 "Climate-macro" "climate_processor" TAIR2))'
            elif pipe_info[0]['ambient']==2: #ground
                alpha_o=100000 #duct
                tamb_conn=' (:VAR :N |TAmb| :B (1 "Climate-macro" "TGround" OUTSIGNAL))'
            elif pipe_info[0]['ambient']==3: #duct
                alpha_o=5 #duct
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
            if requestedOutputs['p_lines']: 
                idm+="""\n(output-file :sf "self:\\Line_p_{}.prn" :n "Line_p_{}" :t output-file)""".format(lid,lid)
                p="""\n ((CONNECTOR :N |liqL|)
  (:VAR :N P :L "Line_p_{}" :AS #S(MS-SPARSE DEFAULT-VALUE NIL DIMENSION 1 VALUE ({}))))
 ((CONNECTOR :N |liqR|)
  (:VAR :N P :L "Line_p_{}" :AS #S(MS-SPARSE DEFAULT-VALUE NIL DIMENSION 1 VALUE ({}))))""".format(lid,''.join(["""({} . "L_{}")""".format(i+1,i+1) for i in range(npipes)]),lid,''.join(["""({} . "R_{}")""".format(i+1,i+1) for i in range(npipes)]))
            else:
                p=""
                
                
            Rij=[]
            for row in range(0,npipes):
                R_pipe=0
                di=float(dPipes[row])
                di_layer=di
                for layer in layers:
                    layer_info=layer.split(':')
                    R_pipe+=di/(2*float(layer_info[2]))*math.log((di_layer+2*float(layer_info[1]))/di_layer)
                    di_layer+=2*float(layer_info[1])
                R=1/alpha_i+R_pipe+di/(di_layer*alpha_o)
                row_list=[]
                for col in range(0,npipes):
                    if row==col:
                        row_list.append(str(R))
                    else:
                        row_list.append('10000')
                Rij.append('('+' '.join(row_list)+')')
                                  
            idm+="""\n((MODEL :N "Pipebundlef_{}" :T |pipebundlef|)
 (:PAR :N |npipes| :V {})
 (:PAR :N |lcell| :V {})
 (:PAR :N |l| :V {})
{}
 (:PAR :N |nK| :V {})
 (:PAR :N |Rij| :V #2A({}))
 ((RECORD :N |pipen|)
  (:PAR :N |k| :V #2A({}))
  (:PAR :N |h| :V #({}))
  (:PAR :N |dPipe| :V #({}))
  (:PAR :N |aWall| :V #({}))
  (:PAR :N |cp_pipe| :V #({}))
  (:PAR :N |rhoPipe| :V #({}))
  (:PAR :N |lambdawall| :V #({}))
  (:PAR :N |epsilon| :V #({})){}{}{}){})""".format(lid,
                                                npipes,
                                                modellingSettings['fd_meterPerNode'],
                                                length,tamb_conn, 
                                                1 if zeta else 0,
                                                ' '.join(Rij),
                                                ' '.join(['('+str(zeta)+')' for i in dPipes if zeta]),
                                                ' '.join([str(pipe_bundle['height_diff']) for i in dPipes]),
                                                ' '.join([str(i) for i in dPipes]),
                                                ' '.join([str(thickness) for i in dPipes]),
                                                ' '.join([str(cp) for i in dPipes]),
                                                ' '.join([str(rho) for i in dPipes]),
                                                ' '.join([str(lambda_) for i in dPipes]),
                                                roughness,
                                                temp,
                                                vel,
                                                mdot,
                                                p)
            idc+="""(EQUATION-FRAME :AT (({} {})) :R (10 10) :ICON "{}\\\\graphics\\\\pipebifd_bundle.ids" :SYMMETRY {} :SLOT ("Pipebundlef_{}") :NAME "Pipebundlef_{}" :DATA MODEL) 
""".format(coordinates['x_pipe'],coordinates['y_pipe'],self.plugin_dir.replace("\\","\\\\"),coordinates['angle'],lid,lid)
        
        return idm,idc
    
    def insertJunctionConnections(self,submodel,idm_conn,idc_conn,networks):
        """Insert the junction connections between devices, plants or customers and pipes"""
        sql="""SELECT l.id AS lid,j.id AS jid, ST_AsText(j.geom) AS j_point,b_pipes.sequence AS seq, j.n_connections,pipe_lids.lids, c.counter AS max_seq, CASE WHEN ST_dWithIn(ST_StartPoint(l.geom),j.geom,0.0001) THEN 'liqL' ELSE 'liqR' END AS dir, ST_AsText(ST_LineInterpolatePoint(l.geom,0.5)) AS l_point
    FROM {}.dhc_junctions j, {}.junction_connections jc, {}.dhc_lines l, 
        (SELECT count(*) AS counter,pipe_bundle_type_id FROM public.bundle_pipes GROUP BY pipe_bundle_type_id) c,
        (SELECT pipe_bundle_type_id,sequence FROM public.bundle_pipes) b_pipes,
        (SELECT jid, array_agg(lid ORDER BY lid) AS lids FROM {}.junction_connections jc GROUP BY jid) pipe_lids
    WHERE pipe_lids.jid=jc.jid AND l.id=jc.lid AND j.id=jc.jid AND j.submodel={} AND l.network IN ({}) AND c.pipe_bundle_type_id=l.pipe_bundle_type_id AND b_pipes.pipe_bundle_type_id=c.pipe_bundle_type_id
    ORDER BY j.id,b_pipes.sequence, c.counter DESC, l.id;""".format(self.dictDB['versionName'],self.dictDB['versionName'],self.dictDB['versionName'],self.dictDB['versionName'],submodel,','.join([str(i) for i in networks]))
        print(sql)
        self.cur.execute(sql)

        conns=self.cur.fetchall()
        if not conns:
            print('No nodes in network or wrong junction constructions!')
            #iface.messageBar().pushMessage("Error", "No junctions in network or wrong constructions!!", level=Qgis.Critical)
            return idm,idc
            
        jid_old=0
        lid_old=0
        seq_old=0
        seq_counter=0
        for conn in conns:
            #print(conn)
            point_pipe = self.getSymbolCoordinate(conn['l_point'].split("(")[1][:-1].split(' '))
            point_j = self.getSymbolCoordinate(conn['j_point'].split("(")[1][:-1].split(' '))
                
            if conn['seq']!=seq_old:
                #print('--new seq--')
                if seq_counter!=0:
                    #print('--conn_counter: {}; len(lids): {}'.format(conn_counter,len(lids)))
                    for i in range(conn_counter,len(lids)+1):
                       # print('--add waterplug: '+str(i))
                        idm_conn+="""\n (("NodeBundle_{}" (|term| {} {})) ((:LIB WATPLUG) OUTLET) 2 0 NIL)""".format(conn['jid'],max(pipe_counter.values()),conn_counter)
                seq_counter+=1
                conn_counter=1
                
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
              
            if lids[conn_counter-1]!=conn['lid']:
                #print('++lids[conn_counter] != conn[lid]--')
                #print('++lids[conn_counter-1]: {}; conn[lid]: {}'.format(lids[conn_counter-1],conn['lid']))
                #print('++conn_counter: {}; lids.index(conn[lid]): {}'.format(conn_counter,lids.index(conn['lid'])))
                for i in range(conn_counter,lids.index(conn['lid'])+1):
                    #print('++'+str(i))
                    idm_conn+="""\n (("NodeBundle_{}" (|term| {} {})) ((:LIB WATPLUG) OUTLET) 2 0 NIL)""".format(conn['jid'],max(pipe_counter.values()),conn_counter)
                    conn_counter+=1
            
            pipe_counter[conn['lid']]=pipe_counter[conn['lid']]+1
            
            idm_conn+="""\n (("NodeBundle_{}" (|term| {} {})) ("Pipebundlef_{}" (|{}| {})) 0 0 NIL)""".format(conn['jid'],max(pipe_counter.values()),conn_counter,conn['lid'],conn['dir'],pipe_counter[conn['lid']])
            idc_conn+="""\n(CONNECTION-LINE :AT (({} {}) ({} {})) :LINE-COLOR (:CALL PMT-COLOR [@ 1] [@ 2]) :LINE-STYLE 3 :FIRST-LINK ("NodeBundle_{}" 0.5 (|term| {} {})) :LAST-LINK ("Pipebundlef_{}" 0.5 (|{}| {})))""".format(point_j['x'],point_j['y'],point_pipe['x'],point_pipe['y'],conn['jid'],max(pipe_counter.values()),conn_counter,conn['lid'],conn['dir'],pipe_counter[conn['lid']])


            seq_old=conn['seq']
            jid_old=conn['jid']
            lid_old=conn['lid']
            conn_old=conn
            #print("seq: {}; conn: {}".format(seq_counter,conn_counter))
            conn_counter+=1
        

        print('--conn_counter: {}; len(lids): {}'.format(conn_counter,len(lids)))
        for i in range(conn_counter,len(lids)+1):
            print('--add waterplug: '+str(i))
            idm_conn+="""\n (("NodeBundle_{}" (|term| {} {})) ((:LIB WATPLUG) OUTLET) 2 0 NIL)""".format(conn['jid'],i,conn_counter)
            
        return idm_conn,idc_conn
    
    def insertConnections(self,submodel,type,idm_conn,idc_conn,networks):
        """Insert the connections between devices and the pipe"""
        print(type)
        if type=='dhc_customers':
            id_name='cid'
            seq_name='c_seq'
        if type=='dhc_devices':
            id_name='did'
            seq_name='d_seq'
        if type=='dhc_energy_plants':
            id_name='epid'
            seq_name='ep_seq'
        sql="""SELECT l.id AS lid,ST_AsText(ST_LineInterpolatePoint(l.geom,0.5)) AS l_point,d.id AS did, ST_AsText(d.geom) AS d_point, conn_b_t.conn_bundle_type_id,conn_b_t.sequence AS conn_bundl_type_seq, conn_t_conns.connection_type_id, conn_t_conns.sequence AS conn_type_seq, conn.temp, CASE WHEN conn.p IS NULL THEN 'liqL' ELSE 'liqR' END AS dir
    FROM {}.{} d, {}.{}_connections dc, {}.dhc_lines l, public.bundle_type_conns conn_b_t, public.{}_assettypes da, public.connections conn, public.connection_type_connections conn_t_conns
    WHERE conn_t_conns.connection_id=conn.id AND conn_t_conns.connection_type_id=conn_b_t.conn_type_id AND conn_b_t.conn_bundle_type_id=da.conn_bundle_type AND dc.{}=conn_b_t.sequence AND da.assettype=d.assettype AND da.assetgroup=d.assetgroup AND l.id=dc.lid AND d.id=dc.{} AND {} =ANY(l.submodel) AND l.network IN ({})
    ORDER BY d.id, conn_b_t.sequence;""".format(self.dictDB['versionName'],type,self.dictDB['versionName'],type[4:-1],self.dictDB['versionName'],type[4:-1],seq_name,id_name,submodel,','.join([str(i) for i in networks]))
        print(sql)
        self.cur.execute(sql)
        for conn in self.cur.fetchall():
            #print(conn)
            lid=conn['lid']
            did=conn['did']
            point_pipe = self.getSymbolCoordinate(conn['l_point'].split("(")[1][:-1].split(' '))
            point_d = self.getSymbolCoordinate(conn['d_point'].split("(")[1][:-1].split(' '))
            conn_bundl_type=conn['conn_bundle_type_id']
            conn_bundl_type_seq=conn['conn_bundl_type_seq']
            conn_type=conn['connection_type_id']
            conn_type_seq=conn['conn_type_seq']
            conn_temp=conn['temp']
            conn_dir=conn['dir']
            
            name_conn="{}_{}_{}_{}".format(conn_bundl_type,conn_bundl_type_seq,conn_type,conn_type_seq)

            idm_conn+="""\n (("{}_{}" "{}") ("Pipebundlef_{}" (|{}| {})) 0 0 NIL)""".format(type[4:-1].capitalize(),did,name_conn,lid,conn_dir,conn_type_seq)
            idc_conn+="""\n(CONNECTION-LINE :AT (({} {}) ({} {})) :LINE-COLOR (:CALL PMT-COLOR [@ 1] [@ 2]) :LINE-STYLE 3 :FIRST-LINK ("{}_{}" 0.5 "{}") :LAST-LINK ("Pipebundlef_{}" 0.5 (|{}| {})))""".format(point_d['x'],point_d['y'],point_pipe['x'],point_pipe['y'],type[4:-1].capitalize(),did,name_conn,lid,conn_dir,conn_type_seq)
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
        print('check connection')
        if self.dictDB['pwd'] and self.dictDB['user'] and self.dictDB['host'] and self.dictDB['port'] and self.dictDB['projectName'] and self.dictDB['versionName']:
            print('connected!')
            return True
        else:
            print('not connected!')
            return False
 
    def writeNetworkTemplateIdm(self,submodel,dir,requestedOutputs,networkSimData):    
        """ write idm file with """
        print('write idm network model')
        print(networkSimData)
        simulation_data=getSimData(requestedOutputs,networkSimData)
        data=""";IDA 4.9902 Data UTF-8
(DOCUMENT-HEADER :TYPE ICE-SYSTEM :N \"network_{}\" :ETM 3728281380 :MS 6 :PARENT ICE :APP (ICE :VER 4.9902))
((SCHEDULE-DATA :N "Shading" :T SCHEDULE-DATA :QT GENERIC)
 (SCHEDULE-RULE :N "rule-2" :D "rule-2" :START-DATE (NIL 5 1) :END-DATE (NIL 9 30) :VALUE ((24.0 0.86)))
 (SCHEDULE-RULE :N "default" :VALUE ((24 1)) :INDEX 1))
((DB-RESOURCE :N "B2BHPVS-ThemiaMegaM" :T B2B_HP_VS_MODEL :D "B2B  heatpump with variable speed compressor developed by Thermia with capacity modulation in range of 11-44 KW in B0/W35 operating condition. The compressor speed is changing between 1500-6000 rpm.")
 (:PAR :N P_H :V 44)
 (:PAR :N COP :V 4.6)
 (:PAR :N |dTlog_evap| :V 2.688)
 (:PAR :N |dTlog_cond| :V 5.025)
 (:PAR :N |liqTypeE| :V |Ethanol|)
 (:PAR :N |TFreezeE| :V -17)
 (:PAR :N |T_brineC_in| :V 27)
 (:PAR :N |nTeEnvDim| :V 8)
 (:PAR :N |TeEnv| :DIM (8) :V #(-25 -22.5 -20 -5 -2.8 2.8 5 15) :S (:DEFAULT #S(MS-SPARSE DEFAULT-VALUE T DIMENSION 1 VALUE ((1) (2) (3) (4) (5) (6) (7) (8))) 2))
 (:PAR :N |TcMinEnv| :DIM (8) :V #(20 20 20 20 20 20 20 30) :S (:DEFAULT #S(MS-SPARSE DEFAULT-VALUE T DIMENSION 1 VALUE ((1) (2) (3) (4) (5) (6) (7) (8))) 2))
 (:PAR :N |TcMaxEnv| :DIM (4 8) :V #2A((45 45 45 60 60 60 60 60) (37 43 45 60 68 68 68 68) (37 43 45 60 68 68 68 68) (45 45 45 60 60 60 60 60)) :S (:DEFAULT #S(MS-SPARSE DEFAULT-VALUE T DIMENSION 2 VALUE ((1 (1) (2) (3) (4) (5) (6) (7) (8)) (2 (1) (2) (3) (4) (5) (6) (7) (8)) (3 (1) (2) (3) (4) (5) (6) (7) (8)) (4 (1) (2) (3) (4) (5) (6) (7) (8)))) 2))
 (:PAR :N |QevpPowCoef| :V #2A((13527 462 -94.62 6.816 -1.495 0.5516 0.02378 -0.06059 -0.02743 -0.01308) (29151.2 957.2 -262 13.78 -3.921 1.694 0.05946 -0.09987 -0.04839 -0.02332) (43044.9 1425.7 -353.1 20.81 -5.37 1.827 0.09078 -0.1498 -0.08177 -0.0305) (55208.1 1867.5 -368 27.91 -5.841 0.9502 0.1178 -0.2104 -0.1276 -0.03461)) :S (:DEFAULT #S(MS-SPARSE DEFAULT-VALUE T DIMENSION 2 VALUE ((1 (1) (2) (3) (4) (5) (6) (7) (8) (9) (10)) (2 (1) (2) (3) (4) (5) (6) (7) (8) (9) (10)) (3 (1) (2) (3) (4) (5) (6) (7) (8) (9) (10)) (4 (1) (2) (3) (4) (5) (6) (7) (8) (9) (10)))) 2))
 (:PAR :N |CompPowCoef| :V #2A((925.1 -61.88 39.02 -3.991 3.367 -0.3195 -0.05092 0.09563 -0.04246 0.01091) (2381.6 2.276 73.9 -0.4297 0.8279 -0.7697 -0.006913 0.01524 -0.01366 0.01933) (4565.2 68.67 90.51 1.537 -0.867 -0.9323 0.01428 -0.02403 -0.001693 0.02594) (7475.7 137.3 88.87 1.909 -1.717 -0.8073 0.01267 -0.02219 -0.006557 0.03072)) :S (:DEFAULT #S(MS-SPARSE DEFAULT-VALUE T DIMENSION 2 VALUE ((1 (1) (2) (3) (4) (5) (6) (7) (8) (9) (10)) (2 (1) (2) (3) (4) (5) (6) (7) (8) (9) (10)) (3 (1) (2) (3) (4) (5) (6) (7) (8) (9) (10)) (4 (1) (2) (3) (4) (5) (6) (7) (8) (9) (10)))) 2)))
{}
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
((MACRO-OBJECT :N "Climate-macro" :T ICE-MACRO :ETM 3857461881 :STM 3857461887))
((MACRO-OBJECT :N "sf-macro" :T ICE-MACRO :ETM 3857461881 :STM 3857461887))
((MACRO-OBJECT :N "Co-simulation-macro" :T ICE-MACRO :ETM 3857461881 :STM 3857461887))""".format(submodel,self.getResources(),simulation_data)
        return data
        
    def getResources(self):
        return """((TEMPLATE :N "B2B_HP_VS4" :T B2B_HP_VS :D "")
 ((DB-RESOURCE :N "B2BHPVS1" :T B2B_HP_VS_MODEL :D "This is a test sample1 for B2B  heatpump for parameter filling and .....")
  (:PAR :N P_H :V 44)
  (:PAR :N COP :V 4.6)
  (:PAR :N |liqTypeE| :V |Ethanol|)
  (:PAR :N |TFreezeE| :V -17))
 ((DB-RESOURCE :N "B2BHPVS-ThemiaMegaM" :T B2B_HP_VS_MODEL :D "B2B  heatpump with variable speed compressor developed by Thermia with capacity modulation in range of 11-44 KW in B0/W35 operating condition. The compressor speed is changing between 1500-6000 rpm.")
  (:PAR :N P_H :V 44)
  (:PAR :N COP :V 4.6)
  (:PAR :N |dTlog_evap| :V 2.688)
  (:PAR :N |dTlog_cond| :V 5.025)
  (:PAR :N |liqTypeE| :V |Ethanol|)
  (:PAR :N |TFreezeE| :V -17)
  (:PAR :N |T_brineC_in| :V 27)
  (:PAR :N |nTeEnvDim| :V 8)
  (:PAR :N |TeEnv| :DIM (8) :V #(-25 -22.5 -20 -5 -2.8 2.8 5 15) :S (:DEFAULT #S(MS-SPARSE DEFAULT-VALUE T DIMENSION 1 VALUE ((1) (2) (3) (4) (5) (6) (7) (8))) 2))
  (:PAR :N |TcMinEnv| :DIM (8) :V #(20 20 20 20 20 20 20 30) :S (:DEFAULT #S(MS-SPARSE DEFAULT-VALUE T DIMENSION 1 VALUE ((1) (2) (3) (4) (5) (6) (7) (8))) 2))
  (:PAR :N |TcMaxEnv| :DIM (4 8) :V #2A((45 45 45 60 60 60 60 60) (37 43 45 60 68 68 68 68) (37 43 45 60 68 68 68 68) (45 45 45 60 60 60 60 60)) :S (:DEFAULT #S(MS-SPARSE DEFAULT-VALUE T DIMENSION 2 VALUE ((1 (1) (2) (3) (4) (5) (6) (7) (8)) (2 (1) (2) (3) (4) (5) (6) (7) (8)) (3 (1) (2) (3) (4) (5) (6) (7) (8)) (4 (1) (2) (3) (4) (5) (6) (7) (8)))) 2))
  (:PAR :N |QevpPowCoef| :V #2A((13527 462 -94.62 6.816 -1.495 0.5516 0.02378 -0.06059 -0.02743 -0.01308) (29151.2 957.2 -262 13.78 -3.921 1.694 0.05946 -0.09987 -0.04839 -0.02332) (43044.9 1425.7 -353.1 20.81 -5.37 1.827 0.09078 -0.1498 -0.08177 -0.0305) (55208.1 1867.5 -368 27.91 -5.841 0.9502 0.1178 -0.2104 -0.1276 -0.03461)) :S (:DEFAULT #S(MS-SPARSE DEFAULT-VALUE T DIMENSION 2 VALUE ((1 (1) (2) (3) (4) (5) (6) (7) (8) (9) (10)) (2 (1) (2) (3) (4) (5) (6) (7) (8) (9) (10)) (3 (1) (2) (3) (4) (5) (6) (7) (8) (9) (10)) (4 (1) (2) (3) (4) (5) (6) (7) (8) (9) (10)))) 2))
  (:PAR :N |CompPowCoef| :V #2A((925.1 -61.88 39.02 -3.991 3.367 -0.3195 -0.05092 0.09563 -0.04246 0.01091) (2381.6 2.276 73.9 -0.4297 0.8279 -0.7697 -0.006913 0.01524 -0.01366 0.01933) (4565.2 68.67 90.51 1.537 -0.867 -0.9323 0.01428 -0.02403 -0.001693 0.02594) (7475.7 137.3 88.87 1.909 -1.717 -0.8073 0.01267 -0.02219 -0.006557 0.03072)) :S (:DEFAULT #S(MS-SPARSE DEFAULT-VALUE T DIMENSION 2 VALUE ((1 (1) (2) (3) (4) (5) (6) (7) (8) (9) (10)) (2 (1) (2) (3) (4) (5) (6) (7) (8) (9) (10)) (3 (1) (2) (3) (4) (5) (6) (7) (8) (9) (10)) (4 (1) (2) (3) (4) (5) (6) (7) (8) (9) (10)))) 2)))
 (:RES :N |model| :V "B2BHPVS-ThemiaMegaM")
 ((RECORD :N |evaporator|)
  (:VAR :N |mLiq| :V 2.753 :B (-2 |brineEOut| 1))
  (:VAR :N |CapLiq| :V 11590)
  (:VAR :N |Effectiveness| :V 0.5874)
  (:VAR :N Q :V -34771)
  (:VAR :N |dP| :V 0.01019)
  ((RECORD :N |hx|)
   (:VAR :N T :V #(-5.107 -5.107) :IV #S(MS-SPARSE DEFAULT-VALUE 55.0 DIMENSION 1 VALUE NIL))
   (:VAR :N Q :V #(-34771) :IV #S(MS-SPARSE DEFAULT-VALUE 2000.0 DIMENSION 1 VALUE NIL))))
 ((RECORD :N |heatPump|)
  (:VAR :N |TEvap| :V -5.107)
  (:VAR :N |TCond| :V 35.17)
  (:VAR :N |TEvap_min| :V -25.0)
  (:VAR :N |TCond_max| :V 59.89)
  (:VAR :N |TcMin| :V 20.0)
  (:VAR :N |TevapLim| :V -5.107)
  (:VAR :N |Qevap1| :V 26152)
  (:VAR :N |Qevap2| :V 34771)
  (:VAR :N |Qevap| :V 34771)
  (:VAR :N |Pcomp1| :V 7556)
  (:VAR :N |Pcomp2| :V 10616)
  (:VAR :N |Pcomp| :V 10616)
  (:VAR :N |iSpd1| :V #(0.75 3.0) :IV #S(MS-SPARSE DEFAULT-VALUE 0.0 DIMENSION 1 VALUE NIL))
  (:VAR :N |iSpd2| :V #(1.0 4.0) :IV #S(MS-SPARSE DEFAULT-VALUE 0.0 DIMENSION 1 VALUE NIL))
  (:VAR :N PL :V 1.0)
  (:VAR :N PLF :V 1.0 :L "PLF")
  (:VAR :N PLR :V 4.0)
  (:VAR :N |Te1j| :V #(-20.0 3.0) :IV #S(MS-SPARSE DEFAULT-VALUE 0.0 DIMENSION 1 VALUE NIL))
  (:VAR :N |Te2j| :V #(-5.0 4.0) :IV #S(MS-SPARSE DEFAULT-VALUE 0.0 DIMENSION 1 VALUE NIL))
  (:VAR :N |TEvapOld| :V -5.107)
  (:VAR :N |TCondOld| :V 35.17)
  (:VAR :N |Power_c| :V 10616)
  (:VAR :N COP :V 4.275 :L "EER. COP")
  (:VAR :N EER :V 3.275)
  (:VAR :N DT :V 19.89)
  (:VAR :N |DTOld| :V 19.89)
  ((RECORD :N |cond|)
   (:VAR :N T :IV #S(MS-SPARSE DEFAULT-VALUE 0.0 DIMENSION 1 VALUE NIL))
   (:VAR :N Q :V #(-45387) :IV #S(MS-SPARSE DEFAULT-VALUE 0.0 DIMENSION 1 VALUE NIL))
   (:VAR :N |CapFlow| :V 0.0))
  ((RECORD :N |evap|)
   (:VAR :N T :IV #S(MS-SPARSE DEFAULT-VALUE 0.0 DIMENSION 1 VALUE NIL))
   (:VAR :N Q :V #(34771) :IV #S(MS-SPARSE DEFAULT-VALUE 0.0 DIMENSION 1 VALUE NIL))
   (:VAR :N |CapFlow| :V 0.0)))
 ((RECORD :N |condenser|)
  (:VAR :N |mLiq| :V 1.358 :B (-2 |brineCOut| 1))
  (:VAR :N |CapLiq| :V 5675)
  (:VAR :N |Effectiveness| :V 0.979)
  (:VAR :N Q :V 45387)
  (:VAR :N |dP| :V 0.01031)
  ((RECORD :N |hx|)
   (:VAR :N T :V #(35.17 35.17) :IV #S(MS-SPARSE DEFAULT-VALUE 55.0 DIMENSION 1 VALUE NIL))
   (:VAR :N Q :V #(45387) :IV #S(MS-SPARSE DEFAULT-VALUE 2000.0 DIMENSION 1 VALUE NIL))))
 ((CONNECTOR :N |brineCIn|)
  (:VAR :N T :V 27.0 :B (-2 |brineCIn| 2)))
 ((CONNECTOR :N |brineCOut|)
  (:VAR :N P :V -0.01031)
  (:VAR :N T :V 35.0))
 ((CONNECTOR :N |brineEIn|)
  (:VAR :N P :V 0.01019)
  (:VAR :N T :V 0.0 :B (-2 |brineEIn| 2)))
 ((CONNECTOR :N |brineEOut|)
  (:VAR :N T :V -3.0))
 (:VAR :N |ctrl_var| :B (-1 |ctrl| 0))
 (:VAR :N |CompPow_var| :IV #S(MS-SPARSE DEFAULT-VALUE 0.0 DIMENSION 1 VALUE NIL)))
((DB-RESOURCE :N "Thermia:MegaM_44kW (example)" :T B2B_HP_VS_MODEL :D "Thermia:MegaM is  a heat pump with an inverter-controlled compressor. The inverter continuously adjusts the heat pump’s
output to current demand. It can also be operated in installations with different heating and hot water demands without the need for additional volume tanks." :MF "Thermia")
 (:PAR :N P_H :V 44)
 (:PAR :N COP :V 4.2)
 (:PAR :N |dTlog_evap| :V 4)
 (:PAR :N |dTlog_cond| :V 4)
 (:PAR :N |liqTypeE| :V |Ethanol|)
 (:PAR :N |TFreezeE| :V -17)
 (:PAR :N |liqTypeC| :V |Water|)
 (:PAR :N |TFreezeC| :V 0)
 (:PAR :N |T_brineE_in| :V 0)
 (:PAR :N |T_brineE_out| :V -3)
 (:PAR :N |T_brineC_in| :V 27)
 (:PAR :N |T_brineC_out| :V 35)
 (:PAR :N |DT_lim| :V 10.0)
 (:PAR :N |Cc| :V 0.9)
 (:PAR :N |Cd| :V 0.25)
 (:PAR :N |HPtype| :V 1)
 (:PAR :N |nSpdDim| :V 4)
 (:PAR :N |Spd| :V #(0.25 0.5 0.75 1.0))
 (:PAR :N |nTeEnvDim| :V 5)
 (:PAR :N |TeEnv| :V #(-24 -18 4 10 14))
 (:PAR :N |TcMinEnv| :V #(20 20 20 22.5 25))
 (:PAR :N |TcMaxEnv| :V #2A((45 47 60.1 60.12 60.13) (40 46 67.23 67.24 60.25) (38 47 67.33 67.34 60.35) (40 43 60 60 60)))
 (:PAR :N |QevpPowCoef| :V #2A((13527.0 462.0 -94.62 6.816 -1.495 0.5516 0.02378 -0.06059 -0.02743 -0.01308) (29151.2 957.2 -262.0 13.78 -3.921 1.694 0.05946 -0.09987 -0.04839 -0.02332) (43044.9 1425.7 -353.1 20.81 -5.37 1.827 0.09078 -0.1498 -0.08177 -0.0305) (55208.1 1867.5 -368.0 27.91 -5.841 0.9502 0.1178 -0.2104 -0.1276 -0.03461)))
 (:PAR :N |CompPowCoef| :V #2A((925.1 -61.88 39.02 -3.991 3.367 -0.3195 -0.05092 0.09563 -0.04246 0.01091) (2381.6 2.276 73.9 -0.4297 0.8279 -0.7697 -0.006913 0.01524 -0.01366 0.01933) (4565.2 68.67 90.51 1.537 -0.867 -0.9323 0.01428 -0.02403 -0.001693 0.02594) (7475.7 137.3 88.87 1.909 -1.717 -0.8073 0.01267 -0.02219 -0.006557 0.03072))))"""
    
    def writeNetworkTemplateIdc(self,submodel,dir,networks,supervisory_submodel):    
        """ write idc file with """
        print('write idc network model')
        pageSettings=PageSettings(self.cur,submodel,self.dictDB['versionName'],networks).getPageSettings()
        print(pageSettings)
        data=""";IDA 4.9902 Form UTF-8
(DOCUMENT-HEADER :TYPE SCHEMA :PAGE-WIDTH {} :PAGE-HEIGHT {})
(EQUATION-FRAME :AT ((218 144)) :R (20 20) :ICON "sys:eo.ids" :SLOT ("sf-macro") :NAME "sf-macro" :DATA MACRO-OBJECT) 
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
""".format(self.pageSettings['pageWidth'],self.pageSettings['pageHeight'],"""\n(EQUATION-FRAME :AT ((120 144)) :R (20 20) :ICON "sys:eo.ids" :SLOT ("Supervisory_control") :NAME "Supervisory_control" :DATA MACRO-OBJECT)""" if submodel==supervisory_submodel else '')
        return data
        #writeToFile(data,dir,dir+"""\\network_{}.idc""".format(submodel))
        
    def insertJunctions(self,submodel,requestedOutputs,modellingSettings,idm,idc,networks):
        """ Insert junctions"""
        print('insert junctions')
        sql="""SELECT l.id AS lid,j.id AS jid, ST_AsText(j.geom) AS j_point,b_pipes.sequence AS seq, j.n_connections,pipe_lids.lids, c.counter AS max_seq
    FROM {}.dhc_junctions j, {}.junction_connections jc, {}.dhc_lines l, 
        (SELECT count(*) AS counter,pipe_bundle_type_id FROM public.bundle_pipes GROUP BY pipe_bundle_type_id) c,
        (SELECT pipe_bundle_type_id,sequence FROM public.bundle_pipes) b_pipes,
        (SELECT jid, array_agg(lid ORDER BY lid) AS lids FROM {}.junction_connections jc GROUP BY jid) pipe_lids
    WHERE pipe_lids.jid=jc.jid AND l.id=jc.lid AND j.id=jc.jid AND j.submodel={} AND l.network IN ({}) AND c.pipe_bundle_type_id=l.pipe_bundle_type_id AND b_pipes.pipe_bundle_type_id=c.pipe_bundle_type_id
    ORDER BY j.id,b_pipes.sequence, c.counter DESC, l.id;""".format(self.dictDB['versionName'],self.dictDB['versionName'],self.dictDB['versionName'],self.dictDB['versionName'],submodel,','.join([str(i) for i in networks]))
        print(sql)
        self.cur.execute(sql)
        #print(requestedOutputs)

        conns=self.cur.fetchall()
        if not conns:
            print('No nodes in network or wrong junction constructions!')
            #iface.messageBar().pushMessage("Error", "No junctions in network or wrong constructions!!", level=Qgis.Critical)
            return idm,idc
            
        inStreamT=''
        m_dot=''
        jid_old=0
        lid_old=0
        seq_old=0
        seq_counter=0
        for conn in conns:
            #print(conn)
            #print('instreamT: '+inStreamT)
            #print('m_dot: '+m_dot)
                
            if conn['seq']!=seq_old:
                print('--new seq--')
                if seq_counter!=0:
                    #print('--conn_counter: {}; len(lids): {}'.format(conn_counter,len(lids)))
                    for i in range(conn_counter,len(lids)+1):
                        print('--add connection: '+str(i))
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
                #print('++lids[conn_counter] != conn[lid]--')
                #print('++lids[conn_counter-1]: {}; conn[lid]: {}'.format(lids[conn_counter-1],conn['lid']))
                #print('++conn_counter: {}; lids.index(conn[lid]): {}'.format(conn_counter,lids.index(conn['lid'])))
                for i in range(conn_counter,lids.index(conn['lid'])+1):
                    print('++'+str(i))
                    inStreamT+=" ("+str(conn_counter)+" . 0.0)"
                    m_dot+='({} ({} -2 (|term| {} {}) 1))'.format(seq_counter,conn_counter,seq_counter,conn_counter)
                    conn_counter+=1
            
            inStreamT+=" ("+str(conn_counter)+")"

            seq_old=conn['seq']
            jid_old=conn['jid']
            lid_old=conn['lid']
            conn_old=conn
            #print("seq: {}; conn: {}".format(seq_counter,conn_counter))
            conn_counter+=1
        
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
        print(junction)
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
        idc+="""(EQUATION-FRAME :AT (({} {})) :R (10 10) :ICON "lib:brinenode.ids" :SLOT ("NodeBundle_{}") :NAME "NodeBundle_{}" :DATA MODEL)""".format(x,y,jid,jid)
        return idm,idc
                
    def insertCustomers(self,submodel,idm,idc,sensor_dec_data,networks,feature_dec_irefs):
        """ insert customers; take the macro template and copy it to the IDA project"""
        sql="""SELECT c.id AS cid, CASE WHEN {} = ANY(l.submodel) THEN 'same-model' ELSE 'decoupled' END AS model, ST_asText(c.geom) AS point, c.dhw_id,ca.conn_bundle_type, ca.assettype_name, conn_b_t.conn_bundle_type_id,conn_b_t.sequence AS conn_bundl_type_seq, conn_t_conns.connection_type_id, conn_t_conns.sequence AS conn_type_seq, conn.temp
	FROM {}.dhc_customers c, customer_assettypes ca, bundle_type_conns conn_b_t, connection_type_connections conn_t_conns, connections conn, {}.customer_connections c_conns, {}.dhc_lines l
	WHERE c.id=c_conns.cid AND l.id=c_conns.lid AND ca.assettype=c.assettype AND ca.assetgroup=c.assetgroup AND c.assetgroup=ca.assetgroup AND ca.assettype=c.assettype AND 
        (c.submodel={} OR {} != c.submodel AND {} = ANY (l.submodel)) AND c.network && ARRAY[{}] AND
        conn_b_t.conn_bundle_type_id=ca.conn_bundle_type AND conn_t_conns.connection_type_id=conn_b_t.conn_type_id AND
        conn_t_conns.connection_id=conn.id
	ORDER BY c.id,conn_b_t.sequence;""".format(submodel, self.dictDB['versionName'],self.dictDB['versionName'],self.dictDB['versionName'],submodel,submodel,submodel,','.join([str(i) for i in networks]))
        print(sql)
        self.cur.execute(sql)
        iref=""
        i=0
        x_old=""
        y_old=""
        assettype_name_old=""
        cid_old=0
        iref_old=""
        cid=-1
        for customer in self.cur.fetchall():          
            dhw_id=customer['dhw_id']
            cid=customer['cid']
            assettype_name=customer['assettype_name']
            #print(assettype_name)
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
                print('#####++++++-------------------------')
                print(cid_old)
                print(feature_dec_irefs)
                
                idm+="""\n((MACRO-OBJECT :N "Customer_{}" :T ICE-MACRO :D "ICE macro"){}{}{})""".format(cid_old,iref_old if customer_old['model']=='same-model' else'',
                ''.join(["""\n (:IREF :N "Int_Ref_Sensor_Source_{}" :T OUT :F 224)""".format(str(i['sensor_id'])) 
                    for i in sensor_dec_data if i['measure']==5 and i['source_type']==1 for j in i['irefs_source'] if j['iref'].split('_')[1]==str(cid_old) and (j['submodel']==submodel and not j['network_side'] or j['cosim']==submodel and j['network_side'])]),
                ''.join(["""\n (:IREF :N "Int_Ref_Sensor_Target_{}" :T IN :F 208)""".format(i['sensor_id']) 
                    for i in sensor_dec_data if i['target_type']==1 and i['target']==1 for j in i['irefs_target'] if j['iref'].split('_')[1]==str(cid_old) and (j['submodel']==submodel and not j['network_side'] or j['cosim']==submodel and j['network_side'])]))
                idc+="""\n(EQUATION-FRAME :AT (({} {})) :R (20 20) :ICON "{}\\\\graphics\\\\customer_assettypes\\\\{}.ids" :SLOT ("customer_{}") :NAME "customer_{}" :DATA MACRO-OBJECT)""".format(x_old,y_old,self.plugin_dir.replace('\\','\\\\'),assettype_name_old,cid_old,cid_old)
                iref="""\n (:IREF :N "{}" :F 192)""".format(name_conn)
            cid_old=cid
            iref_old=iref
            assettype_name_old=assettype_name
            x_old=x
            y_old=y
            customer_old=customer
            i+=1
        if cid!=-1:
            idm+="""\n((MACRO-OBJECT :N "Customer_{}" :T ICE-MACRO :D "ICE macro"){}{}{})""".format(cid,iref if customer['model']=='same-model' else'',
                    ''.join(["""\n (:IREF :N "Int_Ref_Sensor_Source_{}" :T OUT :F 224)""".format(str(i['sensor_id'])) 
                        for i in sensor_dec_data if i['measure']==5 and i['source_type']==1 for j in i['irefs_source'] if j['iref'].split('_')[1]==str(cid_old) and (j['submodel']==submodel and not j['network_side'] or j['cosim']==submodel and j['network_side'])]),
                    ''.join(["""\n (:IREF :N "Int_Ref_Sensor_Target_{}" :T IN :F 208)""".format(i['sensor_id']) 
                        for i in sensor_dec_data if i['target_type']==1 and i['target']==1 for j in i['irefs_target'] if j['iref'].split('_')[1]==str(cid_old) and (j['submodel']==submodel and not j['network_side'] or j['cosim']==submodel and j['network_side'])]))
            idc+="""\n(EQUATION-FRAME :AT (({} {})) :R (20 20) :ICON "{}\\\\graphics\\\\customer_assettypes\\\\{}.ids" :SLOT ("Customer_{}") :NAME "Customer_{}" :DATA MACRO-OBJECT)""".format(x,y,self.plugin_dir.replace('\\','\\\\'),assettype_name,cid,cid)
        
        return idm,idc
        
    def insertDevices(self,submodel,idm,idc,networks):
        """ insert customers; take the macro template and copy it to the IDA project"""
        sql="""SELECT d.id AS did, ST_asText(d.geom) AS point, da.assettype_name, conn_b_t.conn_bundle_type_id,conn_b_t.sequence AS conn_bundl_type_seq, conn_t_conns.connection_type_id, conn_t_conns.sequence AS conn_type_seq, conn.temp
	FROM {}.dhc_devices d, device_assettypes da, bundle_type_conns conn_b_t, connection_type_connections conn_t_conns, connections conn
	WHERE da.assettype=d.assettype AND da.assetgroup=d.assetgroup AND d.assetgroup=da.assetgroup AND da.assettype=d.assettype AND d.submodel={} AND d.network && ARRAY[{}] AND
	conn_b_t.conn_bundle_type_id=da.conn_bundle_type AND conn_t_conns.connection_type_id=conn_b_t.conn_type_id AND
	conn_t_conns.connection_id=conn.id
	ORDER BY d.id,conn_b_t.sequence;""".format(self.dictDB['versionName'],submodel,','.join([str(i) for i in networks]))
        print(sql)
        self.cur.execute(sql)
        iref=""
        i=0
        x_old=""
        y_old=""
        assettype_name_old=""
        did_old=0
        iref_old=""
        for device in self.cur.fetchall():
            did=device['did']
            assettype_name=device['assettype_name']
            #print(assettype_name)
            points = device['point'].split("(")[1].replace('(','').replace(')','').split(' ')
            y=round(float(self.pageSettings['pageHeight'])/0.2575-50-((float(points[1])-float(self.pageSettings['ymin']))/float(self.pageSettings['lmin'])*150),0)
            x=round(150+50+(float(points[0])-float(self.pageSettings['xmin']))/float(self.pageSettings['lmin'])*150,0)
            
            conn_bundl_type=device['conn_bundle_type_id']
            conn_bundl_type_seq=device['conn_bundl_type_seq']
            conn_type=device['connection_type_id']
            conn_type_seq=device['conn_type_seq']
            conn_temp=device['temp']
            
            name_conn="{}_{}_{}_{}".format(conn_bundl_type,conn_bundl_type_seq,conn_type,conn_type_seq)
            iref+="""\n (:IREF :N "{}" :F 192)""".format(name_conn)
            if did!=did_old and i!=0:
                idm+="""\n((MACRO-OBJECT :N "Device_{}" :T ICE-MACRO :D "ICE macro"){})""".format(did_old,iref_old)
                idc+="""\n(EQUATION-FRAME :AT (({} {})) :R (20 20) :ICON "sys:eo.ids" :SLOT ("Device_{}") :NAME "Device_{}" :DATA MACRO-OBJECT) """.format(x_old,y_old,did_old,did_old)
                iref="""\n (:IREF :N "{}" :F 192)""".format(name_conn)
            did_old=did
            iref_old=iref
            assettype_name_old=assettype_name
            x_old=x
            y_old=y
            i+=1
        
        if i>0:        
            idm+="""\n((MACRO-OBJECT :N "Device_{}" :T ICE-MACRO :D "ICE macro"){})""".format(did,iref)
            idc+="""\n(EQUATION-FRAME :AT (({} {})) :R (20 20) :ICON "sys:eo.ids" :SLOT ("Device_{}") :NAME "Device_{}" :DATA MACRO-OBJECT) """.format(x,y,did,did)
        return idm,idc
        
    def insertPlants(self,submodel,idm,idc,sensor_dec_data,networks):
        """ insert plants; take the macro template and copy it to the IDA project"""
        sql="""SELECT ep.id AS epid, ST_asText(ep.geom) AS point, epa.assettype_name, conn_b_t.conn_bundle_type_id,conn_b_t.sequence AS conn_bundl_type_seq, conn_t_conns.connection_type_id, conn_t_conns.sequence AS conn_type_seq, conn.temp
	FROM {}.dhc_energy_plants ep, energy_plant_assettypes epa, bundle_type_conns conn_b_t, connection_type_connections conn_t_conns, connections conn, {}.dhc_lines l, {}.energy_plant_connections ep_conns
	WHERE l.id=ep_conns.lid AND ep.id=ep_conns.epid AND epa.assettype=ep.assettype AND epa.assetgroup=ep.assetgroup AND ep.assetgroup=epa.assetgroup AND epa.assettype=ep.assettype AND 
        (ep.submodel={} OR {} != ep.submodel AND {} = ANY (l.submodel)) AND
        conn_b_t.conn_bundle_type_id=epa.conn_bundle_type AND conn_t_conns.connection_type_id=conn_b_t.conn_type_id AND
        conn_t_conns.connection_id=conn.id AND ep.network && ARRAY[{}]
	ORDER BY ep.id,conn_b_t.sequence;""".format(self.dictDB['versionName'],self.dictDB['versionName'],self.dictDB['versionName'],submodel,submodel,submodel,','.join([str(i) for i in networks]))
        print(sql)
        self.cur.execute(sql)
        epid=""
        iref=""
        i=0
        x_old=""
        y_old=""
        assettype_name_old=""
        epid_old=0
        iref_old=""
        epid=-1
        for plant in self.cur.fetchall():
            epid=plant['epid']
            points = plant['point'].split("(")[1].replace('(','').replace(')','').split(' ')
            y=round(float(self.pageSettings['pageHeight'])/0.2575-50-((float(points[1])-float(self.pageSettings['ymin']))/float(self.pageSettings['lmin'])*150),0)
            x=round(150+50+(float(points[0])-float(self.pageSettings['xmin']))/float(self.pageSettings['lmin'])*150,0)
            assettype_name=plant['assettype_name']
            conn_bundl_type=plant['conn_bundle_type_id']
            conn_bundl_type_seq=plant['conn_bundl_type_seq']
            conn_type=plant['connection_type_id']
            conn_type_seq=plant['conn_type_seq']
            conn_temp=plant['temp']
            
            name_conn="{}_{}_{}_{}".format(conn_bundl_type,conn_bundl_type_seq,conn_type,conn_type_seq)
            iref+="""\n (:IREF :N "{}" :F 192)""".format(name_conn)
            if epid!=epid_old and i!=0:
                idm+="""\n((MACRO-OBJECT :N "Energy_plant_{}" :T ICE-MACRO :D "ICE macro"){}{}{})""".format(epid_old,iref_old,
                    ''.join(["""\n (:IREF :N "Int_Ref_Sensor_Source_{}" :T OUT :F 224)""".format(str(i['sensor_id'])) 
                        for i in sensor_dec_data if i['measure']==5 and i['source_type']==2 for j in i['irefs_source'] if j['iref'].split('_')[1]==str(epid_old) and (j['submodel']==submodel and not j['network_side'] or j['cosim']==submodel and j['network_side'])]),
                    ''.join(["""\n (:IREF :N "Int_Ref_Sensor_Target_{}" :T IN :F 208)""".format(i['sensor_id']) 
                        for i in sensor_dec_data if i['target_type']==2 and i['target']==1 for j in i['irefs_target'] if j['iref'].split('_')[1]==str(epid_old) and (j['submodel']==submodel and not j['network_side'] or j['cosim']==submodel and j['network_side'])]))
                idc+="""\n(EQUATION-FRAME :AT (({} {})) :R (20 20) :ICON "lib:boil1circ.ids" :SLOT ("Energy_plant_{}") :NAME "Energy_plant_{}" :DATA MACRO-OBJECT) """.format(x_old,y_old,epid_old,epid_old) 
                iref="""\n (:IREF :N "{}" :F 192)""".format(name_conn)
            epid_old=epid
            iref_old=iref
            assettype_name_old=assettype_name
            x_old=x
            y_old=y
            i+=1    
        if epid!=-1:
            idm+="""\n((MACRO-OBJECT :N "Energy_plant_{}" :T ICE-MACRO :D "ICE macro"){}{}{})""".format(epid,iref,
                    ''.join(["""\n (:IREF :N "Int_Ref_Sensor_Source_{}" :T OUT :F 224)""".format(str(i['sensor_id'])) 
                        for i in sensor_dec_data if i['measure']==5 and i['source_type']==2 for j in i['irefs_source'] if j['iref'].split('_')[1]==str(epid_old) and (j['submodel']==submodel and not j['network_side'] or j['cosim']==submodel and j['network_side'])]),
                    ''.join(["""\n (:IREF :N "Int_Ref_Sensor_Target_{}" :T IN :F 208)""".format(i['sensor_id']) 
                        for i in sensor_dec_data if i['target_type']==2 and i['target']==1 for j in i['irefs_target'] if j['iref'].split('_')[1]==str(epid_old) and (j['submodel']==submodel and not j['network_side'] or j['cosim']==submodel and j['network_side'])]))
            idc+="""\n(EQUATION-FRAME :AT (({} {})) :R (20 20) :ICON "lib:boil1circ.ids" :SLOT ("energy_plant_{}") :NAME "energy_plant_{}" :DATA MACRO-OBJECT) """.format(x,y,epid,epid)                   
        return idm,idc
        
    def writeMacroSFIdm(self,dir):
        sql="SELECT id,sf,vars FROM {}.invoked_sf;".format(self.dictDB['versionName'])
        self.cur.execute(sql)
        sf_ids=self.cur.fetchall()     
        print(sf_ids)

        filedata=[""";IDA 5.09001 Data UTF-8
(DOCUMENT-HEADER :TYPE ICE-MACRO :D "ICE macro" :ETM 3857463573 :APP (ICE :VER 5.09001)) """]
        filedata+=["""\n((SOURCE-FILE :DOCUMENT-PATH {} :SF {} :N "SOURCE-FILE-{}" :T SOURCE-FILE :COL T){})""".format(i['sf'],i['sf'],i['id'],''.join([" (:VAR :N {} :T GENERIC)".format(j) for j in i['vars'] ])) for i in sf_ids if i['vars']!=None]
        writeToFileFromList(filedata,dir,dir+'\\sf-macro.idm')        
                
    def writeMacroSFIdc(self,dir):
        sql="SELECT id,sf FROM {}.invoked_sf;".format(self.dictDB['versionName'])
        self.cur.execute(sql)
        sf_ids=self.cur.fetchall()
            
        filedata=[""";IDA 5.09001 Data UTF-8
(DOCUMENT-HEADER :TYPE SCHEMA :PAGE-WIDTH 178 :PAGE-HEIGHT 97) 
(SELF-FRAME :AT ((352 190)) :R (342 176) :SLOT (:SELF) :DATA MACRO-OBJECT) """]
        filedata+=["""\n(EQUATION-FRAME :AT ((50 {})) :R (20 20) :ICON "sys:source-file.ids" :SLOT ("SOURCE-FILE-{}") :NAME "SOURCE-FILE-{}" :DATA SOURCE-FILE :D "SOURCE-FILE")""".format(30+counter*48,i['id'],i['id']) for counter,i in enumerate(sf_ids,1)]
        writeToFileFromList(filedata,dir,dir+'\\sf-macro.idc')


        