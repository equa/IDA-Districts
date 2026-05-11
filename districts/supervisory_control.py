from .utility_functions.db import *
from .utility_functions.files import *
from .utility_functions.macros import *
from .utility_functions.sensor_signals import *

import psycopg2
from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT

class CopySupervisoryControl:
    """ Copy supervisory control with resources and macros"""
    def __init__(self,dir,config,cur,submodel):
        #print('copy supervisory control')
        
        target_dir=dir+'\\versions\\'+config['versionName']+"\\network_"+str(submodel)
        source_dir=dir+'\\supervisory_control'

        f_idc_target=target_dir+'\\Supervisory_control.idc'
        f_idm_target=target_dir+'\\Supervisory_control.idm'
        
        #collect ressources
        source_f="{}\\Supervisory_control.idm".format(source_dir)     
        file_data=readFileToList(source_f)
        self.resources = getResourcesFromFileDataList(file_data)
        
        
        #idm
        source_f="{}\\Supervisory_control\\Supervisory_control.idm".format(source_dir)     
        copyFile(source_f,target_dir,f_idm_target)
        
        #idc            
        source_f="{}\\Supervisory_control\\Supervisory_control.idc".format(source_dir)     
        copyFile(source_f,target_dir,f_idc_target)
        
        #check if folder contains macros
        copyNestedSupervisoryMacros(source_dir+'\\Supervisory_control\\Supervisory_control',target_dir)

class Supervisory_control():
    def __init__(self,plugin_dir,config,update_sensors=False):
        """1) Check for new sensor sources and targets --> moved to sensors dialog
           2) Check if a supervisory control is already there 
                --if not create a directory and an IDA file with a supervisory control macro 
                --if yes add to IDA files
           3) Open IDA file"""
        #print('++++++++++++++Supervisory+++++++++++++++++++')
        self.config=config
        self.conn=dbConnect(self.config,True)
        if self.conn:
            self.cur=self.conn.cursor(cursor_factory = psycopg2.extras.RealDictCursor)
            
            dir=config['pathProjects']+config['projectName']+"\\"
            createDir(dir,'supervisory_control')
            dir+='supervisory_control'
            #print(dir)
            
            #supervisory idm project file
            file=dir+"""\\supervisory_control.idm"""
            
            
            #1)
            
            #get sensor data
            sensor_data_source=getSensorData(self.cur,self.config,source_types=[3])
            sensor_data_target=getSensorData(self.cur,self.config,target_types=[3])

            if update_sensors:
                #print('--update_sensors--')
                #Get all removed sensor sources (table invoked_sensor_source_signals in DB) with supervisory contrl and delete the IREF of the signal in the supervisory control macro. Afterwards an Adder comp. (n_in=1) is removed in the sensor macro.
                remove_sensor_source_ids=getRemovedSensorSourceData(self.cur,self.config,source_types=[3])
                #print(remove_sensor_source_ids)
                if remove_sensor_source_ids:
                    sql="""DELETE FROM invoked_sensor_source_signals WHERE sensor_id IN ({});""".format(','.join([str(sensor['sensor_id']) for sensor in remove_sensor_source_ids])) # nosec B608
                    #print(sql)
                    self.cur.execute(sql)
                    
                #Get all new sensor sources (table invoked_sensor_source_signals in DB) with supervisory contrl and make a IREF of each signal in the supervisory control macro. Afterwards an Adder comp. (n_in=1) is inserted in the sensor macro with the signal.
                add_sensor_source_idsValues=getAddedSensorSourceData(self.cur,self.config,source_types=[3])
                #print(add_sensor_source_idsValues)
                writeInvokedSensorSourceSignals(self.cur,self.config,add_sensor_source_idsValues)
                    
                #Get all removed sensor targets (table $versionName$.invoked_sensor_target_signals in DB) with supervisory contrl and delete the IREF of the signal in the supervisory control macro. Afterwards an Adder comp. (n_in=1) is removed in the sensor macro.
                remove_sensor_target_ids=getRemovedSensorTargetData(self.cur,self.config,target_types=[3])
                
                if remove_sensor_target_ids:
                    sql="""DELETE FROM invoked_sensor_target_signals WHERE sensor_id IN ({});""".format(','.join([str(sensor['sensor_id']) for sensor in remove_sensor_target_ids])) # nosec B608
                    #print(sql)
                    self.cur.execute(sql)
                    
                #Get all new sensor targets (table $versionName$.invoked_sensor_targets_signals in DB) with supervisory contrl and make a IREF of each signal in the supervisory control macro. Afterwards an Adder comp. (n_in=1) is inserted in the sensor macro with the signal.
                add_sensor_target_idsValues=getAddedSensorTargetData(self.cur,self.config,target_types=[3])
                #print(add_sensor_target_idsValues)
                writeInvokedSensorTargetSignals(self.cur,self.config,add_sensor_target_idsValues)
            else:
                remove_sensor_source_ids=[]
                remove_sensor_target_ids=[]
                if os.path.exists(file):
                    add_sensor_source_idsValues=[]
                    add_sensor_target_idsValues=[]
                else:
                    add_sensor_source_idsValues=getSensorData(self.cur,self.config,source_types=[3])
                    add_sensor_target_idsValues=getSensorData(self.cur,self.config,target_types=[3])
                
            #print('++++++Supervisory sensor data+++++++++')
            #print(add_sensor_source_idsValues)
            #print(add_sensor_target_idsValues)
            #print(sensor_data_source)
            #print(sensor_data_target)
            #print([k for i in add_sensor_source_idsValues for j in sensor_data_source if j['sensor_id']==i['sensor_id'] for k in j['irefs_source']])
            #print([k for i in add_sensor_target_idsValues for j in sensor_data_target if j['sensor_id']==i['sensor_id'] for k in j['irefs_target']])
            
            #2)
            #supervisory idm project file
            file_data=""
            if os.path.exists(file):
                #read file --> remove deleted connections --> add new connections
                file_data=readFileToList(file)
                lines_del=[]
                #print(file_data)
                file_data=delSensorConnection(file_data,remove_sensor_source_ids,'Source')
                file_data=delSensorConnection(file_data,remove_sensor_target_ids,'Target')
                
                #todo get number of old sensor source signals --> for component placement in .idc
                sql="""SELECT count(templates) FROM invoked_sensor_source_signals WHERE type=3;"""
                #print(sql)
                self.cur.execute(sql)
                numberOf_oldSensorSources=self.cur.fetchone()['count']
                
                #todo get number of old sensor target signals --> for component placement in .idc
                sql="""SELECT count(templates) FROM invoked_sensor_source_signals WHERE type=3;"""
                #print(sql)
                self.cur.execute(sql)
                numberOf_oldSensorTargets=self.cur.fetchone()['count'] 
                
                if add_sensor_source_idsValues or add_sensor_target_idsValues:
                    data=[]
                    connections=False
                    for line in file_data:
                        data.append(line)
                        if '(MACRO-OBJECT :N "Supervisory_control\"' in line:
                            idx=file_data.index(line)
                            if file_data[idx].count('(')-file_data[idx].count(')')==0:
                                data[-1]=data[-1].replace('\n','').rstrip()[:-1]+'\n'
                                data.append('\n'.join([""" (:IREF :N "Int_Ref_Sensor_Source_{}" :T OUT :F 224)""".format(k) for i in add_sensor_source_idsValues for j in sensor_data_source if j['sensor_id']==i['sensor_id'] for k in j['irefs_source']]))
                                if add_sensor_target_idsValues and add_sensor_source_idsValues:
                                    data[-1]+='\n'
                                data.append('\n'.join([""" (:IREF :N "Int_Ref_Sensor_Target_{}" :T IN :F 208)""".format(k) for i in add_sensor_target_idsValues for j in sensor_data_target if j['sensor_id']==i['sensor_id'] for k in j['irefs_target']]))
                                data[-1]+=")\n"
                            else:
                                data.append('\n'.join([""" (:IREF :N "Int_Ref_Sensor_Source_{}" :T OUT :F 224)""".format(k) for i in add_sensor_source_idsValues for j in sensor_data_source if j['sensor_id']==i['sensor_id'] for k in j['irefs_source']]))
                                data.append('\n'.join([""" (:IREF :N "Int_Ref_Sensor_Target_{}" :T IN :F 208)""".format(k) for i in add_sensor_target_idsValues for j in sensor_data_target if j['sensor_id']==i['sensor_id'] for k in  j['irefs_target']]))
                        if '(MACRO-OBJECT :N "Sensor-macro\"' in line:
                            idx=file_data.index(line)
                            if file_data[idx].count('(')-file_data[idx].count(')')==0:
                                data[-1]=data[-1].replace('\n','').rstrip()[:-1]+'\n'
                                data.append('\n'.join([""" (:IREF :N "Int_Ref_Sensor_Source_{}" :T IN :F 208)""".format(k) for i in add_sensor_source_idsValues for j in sensor_data_source if j['sensor_id']==i['sensor_id'] for k in j['irefs_source']]))
                                if add_sensor_target_idsValues and add_sensor_source_idsValues:
                                    data[-1]+='\n'
                                data.append('\n'.join([""" (:IREF :N "Int_Ref_Sensor_Target_{}" :T OUT :F 224)""".format(k) for i in add_sensor_target_idsValues for j in sensor_data_target if j['sensor_id']==i['sensor_id'] for k in  j['irefs_target']]))
                                data[-1]+=")\n"
                            else:
                                data.append('\n'.join([""" (:IREF :N "Int_Ref_Sensor_Source_{}" :T IN :F 208)""".format(k) for i in add_sensor_source_idsValues for j in sensor_data_source if j['sensor_id']==i['sensor_id'] for k in j['irefs_source']]))  
                                data.append('\n'.join([""" (:IREF :N "Int_Ref_Sensor_Target_{}" :T OUT :F 224)""".format(k) for i in add_sensor_target_idsValues for j in sensor_data_target if j['sensor_id']==i['sensor_id'] for k in  j['irefs_target']]))
                        if """(CONNECTIONS""" in line:
                            connections=True
                            idx=file_data.index(line)
                            if file_data[idx].count('(')-file_data[idx].count(')')==0:
                                if data[-1].replace('\n','').rstrip()[:-1].rstrip().split('CONNECTIONS')[1]:
                                    data[-1]='(CONNECTIONS \n'+data[-1].replace('\n','').rstrip()[:-1].rstrip().split('CONNECTIONS')[1]+'\n'
                                else:
                                    data[-1]='(CONNECTIONS \n'
                                data.append('\n'.join([""" (("Sensor-macro" "Int_Ref_Sensor_Source_{}") ("Supervisory_control" "Int_Ref_Sensor_Source_{}") 0 0 NIL)""".format(k,k) for i in add_sensor_source_idsValues for j in sensor_data_source if j['sensor_id']==i['sensor_id'] for k in j['irefs_source']])) 
                                if add_sensor_target_idsValues and add_sensor_source_idsValues:
                                    data[-1]+='\n'                                
                                data.append('\n'.join([""" (("Sensor-macro" "Int_Ref_Sensor_Target_{}") ("Supervisory_control" "Int_Ref_Sensor_Target_{}") 0 0 NIL)""".format(k,k) for i in add_sensor_target_idsValues for j in sensor_data_target if j['sensor_id']==i['sensor_id'] for k in  j['irefs_target']]))
                                data[-1]+=")"
                            else:
                                data.append('\n'.join([""" (("Sensor-macro" "Int_Ref_Sensor_Source_{}") ("Supervisory_control" "Int_Ref_Sensor_Source_{}") 0 0 NIL)""".format(k,k) for i in add_sensor_source_idsValues for j in sensor_data_source if j['sensor_id']==i['sensor_id'] for k in j['irefs_source']]))   
                                data.append('\n'.join([""" (("Sensor-macro" "Int_Ref_Sensor_Target_{}") ("Supervisory_control" "Int_Ref_Sensor_Target_{}") 0 0 NIL)""".format(k,k) for i in add_sensor_target_idsValues for j in sensor_data_target if j['sensor_id']==i['sensor_id'] for k in  j['irefs_target']]))   
                    if not connections and (add_sensor_source_idsValues or add_sensor_target_idsValues):
                        connections="(CONNECTIONS \n"
                        if add_sensor_source_idsValues:
                            connections+="""(CONNECTIONS \n{})""".format('\n'.join([""" (("Sensor-macro" "Int_Ref_Sensor_Source_{}") ("Supervisory_control" "Int_Ref_Sensor_Source_{}") 0 0 NIL)""".format(k,k) for i in add_sensor_source_idsValues for j in sensor_data_source if j['sensor_id']==i['sensor_id'] for k in j['irefs_source']]))
                            if add_sensor_target_idsValues:
                                connections+="\n"
                            else:
                                connections+=")"
                        if add_sensor_target_idsValues:
                            connections+='\n'.join([""" (("Sensor-macro" "Int_Ref_Sensor_Target_{}") ("Supervisory_control" "Int_Ref_Sensor_Target_{}") 0 0 NIL)""".format(k,k) for i in add_sensor_target_idsValues for j in sensor_data_target if j['sensor_id']==i['sensor_id'] for k in  j['irefs_target']])+')'
                        data.append(connections)
                    writeToFileFromList(data,dir,file)
                else:
                    writeToFileFromList(file_data,dir,file)
            else:
                supervisory_conns=""
                sensor_conns=""
                connections=""
                numberOf_oldSensorSources=0
                numberOf_oldSensorTargets=0
                if add_sensor_source_idsValues or add_sensor_target_idsValues:
                    if add_sensor_source_idsValues:
                        supervisory_conns='\n'+'\n'.join([""" (:IREF :N "Int_Ref_Sensor_Source_{}" :T OUT :F 224)""".format(k) for i in add_sensor_source_idsValues for j in sensor_data_source if j['sensor_id']==i['sensor_id'] for k in j['irefs_source']])
                        sensor_conns='\n'+'\n'.join([""" (:IREF :N "Int_Ref_Sensor_Source_{}" :T IN :F 208)""".format(k) for i in add_sensor_source_idsValues for j in sensor_data_source if j['sensor_id']==i['sensor_id'] for k in j['irefs_source']])
                        connections='\n'+'\n'.join([""" (("Sensor-macro" "Int_Ref_Sensor_Source_{}") ("Supervisory_control" "Int_Ref_Sensor_Source_{}") 0 0 NIL)""".format(j,j) for i in add_sensor_source_idsValues for j in i['irefs_source']])
                    if add_sensor_target_idsValues:
                        supervisory_conns+='\n'+'\n'.join([""" (:IREF :N "Int_Ref_Sensor_Target_{}" :T IN :F 208)""".format(k) for i in add_sensor_target_idsValues for j in sensor_data_target if j['sensor_id']==i['sensor_id'] for k in  j['irefs_target']])
                        sensor_conns+='\n'+'\n'.join([""" (:IREF :N "Int_Ref_Sensor_Target_{}" :T OUT :F 224)""".format(k) for i in add_sensor_target_idsValues for j in sensor_data_target if j['sensor_id']==i['sensor_id'] for k in  j['irefs_target']])
                        connections+='\n'+'\n'.join([""" (("Sensor-macro" "Int_Ref_Sensor_Target_{}") ("Supervisory_control" "Int_Ref_Sensor_Target_{}") 0 0 NIL)""".format(k,k) for i in add_sensor_target_idsValues for j in sensor_data_target if j['sensor_id']==i['sensor_id'] for k in  j['irefs_target']])
                file_data=""";IDA {} Data UTF-8
(DOCUMENT-HEADER :TYPE |districts| :N "supervisory_control" :PARENT DISTRICTS :APP (DISTRICTS :VER {})) 
((SCHEDULE-DATA :N "Shading" :T SCHEDULE-DATA :QT GENERIC)
 (SCHEDULE-RULE :N "rule-2" :D "rule-2" :START-DATE (NIL 5 1) :END-DATE (NIL 9 30) :VALUE ((24.0 0.86)))
 (SCHEDULE-RULE :N "default" :VALUE ((24 1)) :INDEX 1))
((SIMULATION_DATA :N SIMULATION_DATA)
 ((SIMULATION_PHASE :N STARTUP-PHASE)
  (:PAR :N FROM-TIME :V 3849984000)
  (:PAR :N TO-TIME :V 3850070400))
 ((SIMULATION_PHASE :N CALCULATION-PHASE)
  (:PAR :N FROM-TIME :V 3849984000)
  (:PAR :N TO-TIME :V 3850070400)))
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
((MACRO-OBJECT :N "Supervisory_control" :T DISTRICTS-MACRO){})
((MACRO-OBJECT :N "Climate-macro" :T DISTRICTS-MACRO))
((MACRO-OBJECT :N "Sensor-macro" :T DISTRICTS-MACRO){})
(CONNECTIONS {})""".format(getIDAVersion(config),getIDADistrictsVersion(config),supervisory_conns,sensor_conns,connections)
            
                writeToFile(file_data,dir,file)
            
            #supervisory idc project file
            file=dir+"""\\supervisory_control.idc"""
            file_data=''
            if os.path.exists(file):
                pass
            else:
                file_data=""";IDA {} Form UTF-8
(DOCUMENT-HEADER :TYPE SCHEMA :PAGE-WIDTH 197 :PAGE-HEIGHT 290) 
(EQUATION-FRAME :AT ((63 145)) :R (20 20) :ICON "sys:eo.ids" :SLOT ("Climate-macro") :NAME "Climate-macro" :DATA MACRO-OBJECT) 
(EQUATION-FRAME :AT ((352 348)) :R (203.5 126.5) :ICON "sys:eo.ids" :SLOT ("Supervisory_control") :NAME "Supervisory_control" :DATA MACRO-OBJECT) 
(EQUATION-FRAME :AT ((116 145)) :R (20 20) :ICON "sys:eo.ids" :SLOT ("Sensor-macro") :NAME "Sensor-macro" :DATA MACRO-OBJECT) 
(TEXT-OBJECT :VALUE "Results" :AT ((504 4) (565 18)) :STYLE LABEL) 
(LIST-FIELD :AT ((504 20) (763 100)) :SLOT (:RESULTS) :TEXT-COLOR #S(RGB RED 0 GREEN 0 BLUE 0)) 
(LABEL-TEXT :VALUE "Project:" :FONT (:SWISS :ARIAL 11 1) :VERTICAL :CENTER :WRAP-P NIL :AT ((12 8) (96 24))) 
(FIELD :AT ((100 8) (496 29)) :SLOT (NAME) :TEXT-COLOR #S(RGB RED 0 GREEN 0 BLUE 160) :FONT (:SWISS :ARIAL 17 2) :HELP-STRING "NAME" :TYPE SYMBOL) 
(LABEL-TEXT :VALUE "Description:" :FONT (:SWISS :ARIAL 11 1) :VERTICAL :CENTER :WRAP-P NIL :AT ((13 33) (96 53))) 
(FIELD :AT ((96 32) (496 100)) :SLOT (DESCRIPTION) :TEXT-COLOR #S(RGB RED 0 GREEN 0 BLUE 0)) 
(LINE :AT ((21 108) (760 108))) """.format(getIDAVersion(config))
                writeToFile(file_data,dir,file)
                
            #print(dir)
            createDir(dir,'Supervisory_control')
            dir+='\\Supervisory_control'
            
            #supervisory idm macro file
            file=dir+"""\\Supervisory_control.idm"""
            file_data=''
            if os.path.exists(file):
                #read file --> remove deleted connections --> add new connections
                file_data=readFileToList(file)
                file_data=delSensorConnection(file_data,remove_sensor_source_ids,'Source')
                file_data=delSensorConnection(file_data,remove_sensor_target_ids,'Target')
                if add_sensor_source_idsValues:
                    file_data.insert(2,''.join(["""(:IREF :N "Int_Ref_Sensor_Source_{}" :T OUT :F 224)\n""".format(k) for i in add_sensor_source_idsValues for j in sensor_data_source if j['sensor_id']==i['sensor_id'] for k in j['irefs_source']]))
                if add_sensor_target_idsValues:
                    file_data.insert(2,''.join(["""(:IREF :N "Int_Ref_Sensor_Target_{}" :T IN :F 208)\n""".format(k) for i in add_sensor_target_idsValues for j in sensor_data_target if j['sensor_id']==i['sensor_id'] for k in  j['irefs_target']]))
                writeToFileFromList(file_data,dir,file)
            else:
                file_data=""";IDA {} Data UTF-8
(DOCUMENT-HEADER :TYPE DISTRICTS-MACRO :D "Districts macro" :APP (DISTRICTS :VER {}))\n{}{}""".format(getIDAVersion(config),getIDADistrictsVersion(config),
                    ''.join(["""(:IREF :N "Int_Ref_Sensor_Source_{}" :T OUT :F 224)\n""".format(k) for i in add_sensor_source_idsValues for j in sensor_data_source if j['sensor_id']==i['sensor_id'] for k in j['irefs_source']]),
                    ''.join(["""(:IREF :N "Int_Ref_Sensor_Target_{}" :T IN :F 208)\n""".format(k) for i in add_sensor_target_idsValues for j in sensor_data_target if j['sensor_id']==i['sensor_id'] for k in  j['irefs_target']]))                
                writeToFile(file_data,dir,file)
                
            #supervisory idc macro file
            file=dir+"""\\Supervisory_control.idc"""
            file_data=[]
            #print('-----------------sensor-description-------------------')
            sensor_description=getSensorDescriptionsSupervisory(sensor_data_source,sensor_data_target)
            #print(sensor_description)
            if os.path.exists(file):
                #read file --> remove deleted connections --> add new connections
                file_data=readFileToList(file)
                file_data=delSensorConnection(file_data,remove_sensor_source_ids,'Source')
                file_data=delSensorConnection(file_data,remove_sensor_target_ids,'Target')
                file_data=delSensorDescription(file_data)
                file_data=setPageHeightSensorDescription(file_data,(len(add_sensor_source_idsValues)+len(add_sensor_target_idsValues)-len(remove_sensor_source_ids)-len(remove_sensor_target_ids)))
                file_data.append(sensor_description)
                writeToFileFromList(file_data,dir,file)
            else:
                file_data.append(""";IDA {} Form UTF-8
(DOCUMENT-HEADER :TYPE SCHEMA :PAGE-WIDTH 178 :PAGE-HEIGHT 140) 
(SELF-FRAME :AT ((352 190)) :R (342 176) :SLOT (:SELF) :DATA MACRO-OBJECT)\n""".format(getIDAVersion(config)))
                file_data.append(sensor_description)
                writeToFileFromList(file_data,dir,file)
                
            #sensor idm macro file
            file=dir+"""\\Sensor-macro.idm"""
            if os.path.exists(file):
                #read file --> remove deleted connections --> add new connections
                file_data=readFileToList(file)
                file_data=delSensorConnection(file_data,remove_sensor_source_ids,'Source')
                file_data=delSensorConnection(file_data,remove_sensor_target_ids,'Target')
                file_data=delSensorComp(file_data,remove_sensor_target_ids,'Target')
                if add_sensor_target_idsValues:
                    file_data.insert(2,''.join(["""((:EO :N "Sensor_Target_{}" :T ADDER)
 (:VAR :N INSIGNAL :B #S(MS-SPARSE DEFAULT-VALUE NIL DIMENSION 1 VALUE ((1 . {}))))
 (:PAR :N N_IN :V 1))\n""".format(k,str(i['test_value'])) for i in add_sensor_target_idsValues for j in sensor_data_target if j['sensor_id']==i['sensor_id'] for k in  j['irefs_target']]))
                    file_data.insert(2,''.join(["""(:IREF :N "Int_Ref_Sensor_Target_{}" :T OUT :F 224)\n""".format(k) for i in add_sensor_target_idsValues for j in sensor_data_target if j['sensor_id']==i['sensor_id'] for k in  j['irefs_target']]))
                    connections=False
                    data=[]
                    for line in file_data:
                        data.append(line)
                        if """(CONNECTIONS""" in line:
                            connections=True
                            idx=file_data.index(line)
                            if file_data[idx].count('(')-file_data[idx].count(')')==0:
                                if data[-1].replace('\n','').rstrip()[:-1].rstrip().split('CONNECTIONS')[1]:
                                    data[-1]='(CONNECTIONS \n'+data[-1].replace('\n','').rstrip()[:-1].rstrip().split('CONNECTIONS')[1]+'\n'
                                else:
                                    data[-1]='(CONNECTIONS \n'                            
                                data.append('\n'.join([""" (("Sensor_Target_{}" OUTSIGNALLINK) "Int_Ref_Sensor_Target_{}" 0 0 NIL)""".format(k,k) for i in add_sensor_target_idsValues for j in sensor_data_target if j['sensor_id']==i['sensor_id'] for k in  j['irefs_target']])) 
                                data[-1]+=")"
                                
                            else:
                                data.append(''.join([""" (("Sensor_Target_{}" OUTSIGNALLINK) "Int_Ref_Sensor_Target_{}" 0 0 NIL)\n""".format(k,k) for i in add_sensor_target_idsValues for j in sensor_data_target if j['sensor_id']==i['sensor_id'] for k in  j['irefs_target']]))  
                    if not connections and [True for i in add_sensor_target_idsValues] :
                        connections="(CONNECTIONS"
                        connections+='\n'.join([""" (("Sensor_Target_{}" OUTSIGNALLINK) "Int_Ref_Sensor_Target_{}" 0 0 NIL)""".format(k,k) for i in add_sensor_target_idsValues for j in sensor_data_target if j['sensor_id']==i['sensor_id'] for k in  j['irefs_target']])+')'
                        data.append(connections)
                    writeToFileFromList(data,dir,file)
                else:
                    writeToFileFromList(file_data,dir,file)
            else:
                conns=""
                if add_sensor_target_idsValues:
                    conns="(CONNECTIONS"
                    conns+='\n'+'\n'.join([""" (("Sensor_Target_{}" OUTSIGNALLINK) "Int_Ref_Sensor_Target_{}" 0 0 NIL)""".format(k,k) for i in add_sensor_target_idsValues for j in sensor_data_target if j['sensor_id']==i['sensor_id'] for k in  j['irefs_target']])                          
                    conns+=')'

                file_data=""";IDA {} Data UTF-8
(DOCUMENT-HEADER :TYPE DISTRICTS-MACRO :D "Districts macro" :APP (DISTRICTS :VER {}))\n{}{}{}""".format(getIDAVersion(config),getIDADistrictsVersion(config),
                    ''.join(["""(:IREF :N "Int_Ref_Sensor_Target_{}" :T OUT :F 224)\n""".format(k) for i in add_sensor_target_idsValues for j in sensor_data_target if j['sensor_id']==i['sensor_id'] for k in  j['irefs_target']]),
                    ''.join(["""((:EO :N "Sensor_Target_{}" :T ADDER)
 (:VAR :N INSIGNAL :B #S(MS-SPARSE DEFAULT-VALUE NIL DIMENSION 1 VALUE ((1 . {}))))
 (:PAR :N N_IN :V 1))\n""".format(k,i['test_value']) for i in add_sensor_target_idsValues for j in sensor_data_target if j['sensor_id']==i['sensor_id'] for k in  j['irefs_target']]),conns)
                writeToFile(file_data,dir,file)
                
            #sensor idc macro file
            file=dir+"""\\Sensor-macro.idc"""
            if os.path.exists(file):
                #read file --> remove deleted connections --> add new connections
                file_data=readFileToList(file)
                file_data=delSensorConnection(file_data,remove_sensor_target_ids,'Target')
                file_data=delSensorComp(file_data,remove_sensor_target_ids,'Target')
                if add_sensor_target_idsValues:
                    file_data.insert(2,''.join(["""(EQUATION-FRAME :AT ((643 {})) :R (16 16) :ICON "lib:adder.ids" :SLOT ("Sensor_Target_{}") :NAME "Sensor_Target_{}" :PADDING 3 :DATA :EO)\n""".format(str(50+35*i[0]),i[1],i[1]) 
                        for i in enumerate([k for i in add_sensor_target_idsValues for j in sensor_data_target if j['sensor_id']==i['sensor_id'] for k in  j['irefs_target']],numberOf_oldSensorTargets+1)]))
                    file_data.insert(2,''.join(["""(CONNECTION-LINE :AT ((660 {}) (694 {})) :FIRST-LINK ("Sensor_Target_{}" (0 0.491) OUTSIGNALLINK) :LAST-LINK (:SELF (0.0 0.144) "Int_Ref_Sensor_Target_{}") :DIR :RIGHT :ARROW (19 8 8))\n""".format(str(50+35*i[0]),str(50+35*i[0]),i[1],i[1]) 
                        for i in enumerate([k for i in add_sensor_target_idsValues for j in sensor_data_target if j['sensor_id']==i['sensor_id'] for k in  j['irefs_target']],numberOf_oldSensorTargets+1)]))
                    file_data[1]=file_data[1].split(':PAGE-HEIGHT ')[0]+':PAGE-HEIGHT '+str(50+50+35*max(list(enumerate([k for i in add_sensor_target_idsValues for j in sensor_data_target if j['sensor_id']==i['sensor_id'] for k in  j['irefs_target']],numberOf_oldSensorTargets+1)))[0])+')\n'
                writeToFileFromList(file_data,dir,file)  
            else:
                file_data=""";IDA {} Form UTF-8
(DOCUMENT-HEADER :TYPE SCHEMA :PAGE-WIDTH 178 :PAGE-HEIGHT 97) 
(SELF-FRAME :AT ((352 190)) :R (342 176) :SLOT (:SELF) :DATA MACRO-OBJECT)\n{}{}""".format(getIDAVersion(config),
                    ''.join(["""(EQUATION-FRAME :AT ((643 {})) :R (16 16) :ICON "lib:adder.ids" :SLOT ("Sensor_Target_{}") :NAME "Sensor_Target_{}" :PADDING 3 :DATA :EO)\n""".format(str(50+35*i[0]),i[1],i[1])
                        for i in enumerate([k for i in add_sensor_target_idsValues for j in sensor_data_target if j['sensor_id']==i['sensor_id'] for k in  j['irefs_target']],numberOf_oldSensorTargets+1)]),
                    ''.join(["""(CONNECTION-LINE :AT ((660 {}) (694 {})) :FIRST-LINK ("Sensor_Target_{}" (0 0.491) OUTSIGNALLINK) :LAST-LINK (:SELF (0.0 0.144) "Int_Ref_Sensor_Target_{}") :DIR :RIGHT :ARROW (19 8 8))\n""".format(str(50+35*i[0]),str(50+35*i[0]),i[1],i[1]) 
                        for i in enumerate([k for i in add_sensor_target_idsValues for j in sensor_data_target if j['sensor_id']==i['sensor_id'] for k in  j['irefs_target']],numberOf_oldSensorTargets+1)]))
                writeToFile(file_data,dir,file)
                
            #climate macro
            source_dir_climateMacro=self.config['pathProjects']+self.config['projectName']+'\\climate\\climate\\'
            copyFile(source_dir_climateMacro+'climate-macro.idm',dir,dir+'\\climate-macro.idm')
            copyFile(source_dir_climateMacro+'climate-macro.idc',dir,dir+'\\climate-macro.idc')
   
