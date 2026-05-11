from .db import *
from .files import *
from .macros import *
from .dialog import *


import psycopg2
from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT
from qgis.PyQt.QtWidgets import QTableWidgetItem

from qgis.PyQt.QtCore import QSettings, QTranslator, QCoreApplication,QThreadPool, pyqtSlot, QRunnable
from .util import *
from .workers import WorkerOpenAPI
    
def getSubmodelFromSensorSource(cur,config,sensor,source):
    try:
        return str((getSupervisorySubmodel(cur,config) if sensor['source_type']==3 else getSubmodelPerFeatureIdTypename(source.split('_')[1],sensor['source_type_name'],cur,config))['submodel'])
    except:
        return str(getDrawnSubmodels(cur,config)[0])
        
def getSubmodelFromSensorTarget(cur,config,sensor,target):
    try:
        return str((getSupervisorySubmodel(cur,config) if sensor['target_type']==3 else getSubmodelPerFeatureIdTypename(target.split('_')[1],sensor['target_type_name'],cur,config))['submodel'])
    except:
        return str(getDrawnSubmodels(cur,config)[0]) 
        
def getSensorDecData(sensor_data,feature_dec_irefs,cur,config):
    sensor_dec_data=[]
    #print(sensor_data)
    for sensor in sensor_data:
        irefs_source=[]
        for source in sensor['irefs_source']:
            dec=False
            for dec_irefs in feature_dec_irefs:                
                for dec_feature_iref in dec_irefs['irefs_source']:
                    if '"Int_Ref_Sensor_Source_{}"'.format(source.split('_')[0]) == dec_feature_iref and str(dec_irefs['id'])==source.split('_')[1]:
                        irefs_source.append({'submodel':str(dec_irefs['submodel']),'cosim':dec_irefs['cosim'],'network_side':dec_irefs['network_side'],'iref':source})
            if not dec and source not in [i['iref'] for i in irefs_source]:
                irefs_source.append({'submodel':getSubmodelFromSensorSource(cur,config,sensor,source),'cosim': '','network_side': '','iref':source})
        irefs_target=[]
        for target in sensor['irefs_target']:
            dec=False
            for dec_irefs in feature_dec_irefs:                
                for dec_feature_iref in dec_irefs['irefs_target']:
                    if '"Int_Ref_Sensor_Target_{}"'.format(target.split('_')[0]) == dec_feature_iref and str(dec_irefs['id'])==target.split('_')[1]:
                        irefs_target.append({'submodel':str(dec_irefs['submodel']),'cosim':dec_irefs['cosim'],'network_side':dec_irefs['network_side'],'iref':target})
            if not dec and target not in [i['iref'] for i in irefs_target]:
                irefs_target.append({'submodel':getSubmodelFromSensorTarget(cur,config,sensor,target),'cosim': '','network_side': '','iref':target})

        sensor_dec_data.append({'sensor_id':sensor['sensor_id'],'source_type':sensor['source_type'],'source_type_name':sensor['source_type_name'],'source_template_names':sensor['source_template_names'],'target_type':sensor['target_type'],'target_type_name':sensor['target_type_name'],'target_template_names':sensor['target_template_names'],'function':sensor['function'],'function_name':sensor['function_name'],'measure':sensor['measure'],'measure_name':sensor['measure_name'],'irefs_source':irefs_source,'irefs_target':irefs_target,'test_value':sensor['test_value'],'description_source':sensor['description_source'],'description_target':sensor['description_target']})
    #print(sensor_dec_data)
    return sensor_dec_data

def getLength(sensor,submodel):
    return len([j for j in sensor['irefs_source'] 
                    if [True for j in sensor['irefs_target'] if j['submodel']==submodel and not j['network_side'] or submodel==j['cosim'] and j['network_side']]
                        or j['submodel']==submodel and not j['network_side'] or j['cosim']==submodel and j['network_side']])
                        
def getCosimImportSourceSignals(sensor_dec_data,submodel,cur,config,cosim):
    return [j for i in sensor_dec_data if 
            [True for j in i['irefs_target'] if submodel==j['submodel'] and j['cosim']=='']
                for j in i['irefs_source'] 
                    if j['cosim']==submodel and j['submodel']==cosim and not j['network_side']]

                    
def getCosimExportSignals(sensor_dec_data,submodel,exportVarsCounter,cosim,supervisory_submodel):
    exportVars=["""({} :SYSTEM "Sensor-macro" "Sensor_{}" INSIGNAL {})""".format(i[0]+exportVarsCounter,i[1][1],i[1][0] if i[1][2]==0 else 1)
    for i in enumerate([[j,k[0],k[1]] for i in sensor_dec_data if 
            [True for j in i['irefs_target'] if submodel==j['cosim'] and j['submodel']==cosim and not j['network_side']]
            for j,k in enumerate(
                [[j['iref'].split('_')[0],0] for j in i['irefs_source'] 
                    if j['cosim']=='' and j['submodel']==submodel and not (i['source_type']==3 and i['function']==6)]+
                [[j['iref'],1] for j in i['irefs_target'] 
                    if i['source_type']==3 and i['function']==6 and cosim==j['submodel'] and supervisory_submodel==submodel and supervisory_submodel!=j['submodel'] and not j['network_side']]
                    ,1)],1)]
    return exportVars
    
def getCosimExportTargetSignals(sensor_dec_data,submodel,exportVarsCounter,cosim):
    exportVars=["""({} :SYSTEM "Sensor-macro" "Sensor_{}" OUTSIGNAL)""".format(i[0]+exportVarsCounter,i[1][1])
        for i in enumerate([j for i in [[[k,l['iref'].split('_')[0]] for k,l in enumerate([j for j in i['irefs_target'] 
                    if ([True for j in i['irefs_target'] if j['submodel']==submodel and j['network_side'] or submodel==j['cosim'] and not j['network_side']]
                    or [True for j in i['irefs_target'] if j['submodel']==cosim and j['network_side']=='' and j['cosim']==''])
                    and (j['submodel']==submodel and not j['network_side'] or j['cosim']==submodel and j['network_side'])],1)]
                    for i in sensor_dec_data if ([True for j in i['irefs_target'] if submodel==j['submodel'] and submodel!=j['cosim']]) and not ([True for j in i['irefs_source'] if submodel==j['submodel'] and submodel!=j['cosim']])] for j in i],1)]
    return exportVars
                
def getCosimCounter(sensor_dec_data,iref,submodel,cur,config):
    counters={}
    for i,target_type,function,source_type in [[j,i['target_type'],i['function'],i['source_type']] for i in sensor_dec_data 
                for j in i['irefs_source']
                    if [True for j in i['irefs_target'] if j['submodel']==submodel and not j['network_side'] or submodel==j['cosim'] and j['network_side']] 
                    and not j['submodel']==submodel and not (j['cosim']==submodel and j['network_side'])]:
        if iref==i['iref']:
            try:
                return counters[i['submodel']]+1
            except:
                return 1
        if not (function==6 and source_type==3) or i['iref'].split('_')[1] in [str(k['id']) for k in getFeatureIdsPerSubmodel(submodel,cur,config) if k['feature']==target_type]:
            try:
                counters[i['submodel']]=counters[i['submodel']]+1
            except:
                counters[i['submodel']]=1

def getCosimVarCounter(sensor_dec_data,iref,submodel):
    #print(iref)
    #print('////')
    counter=0
    for i in [j for i in sensor_dec_data 
                for j in i['irefs_source']
                    if [True for j in i['irefs_target'] if j['submodel']==submodel and not j['network_side'] or submodel==j['cosim'] and j['network_side']] 
                    and not j['submodel']==submodel and not (j['cosim']==submodel and j['network_side'])]:
        #print(i)
        if iref==i['iref']:
            return counter+1
        counter+=1
        
def getSensorIrefsSource(sensor_data,submodel,cur,config,feature):
    feature_ids_per_submodel=getFeatureIdsPerSubmodel(submodel,cur,config)
    feature_type=getFeatureIdFromName(config,cur,feature)
    return [j for i in sensor_data for j in i['irefs_source'] if [True for k in feature_ids_per_submodel if k['feature']==feature_type and k['feature']==i['source_type'] and j.split('_')[1]==str(k['id'])]]

def getSensorIrefsSourceDec(sensor_dec_data,submodel,cur,config,feature):
    feature_ids_per_submodel=getFeatureIdsPerSubmodel(submodel,cur,config)
    feature_type=getFeatureIdFromName(config,cur,feature)
    return [j['iref'] for i in sensor_dec_data for j in i['irefs_source'] if [True for k in feature_ids_per_submodel if k['feature']==feature_type and k['feature']==i['source_type'] and j['iref'].split('_')[1]==str(k['id']) or j['network_side'] and j['submodel']==submodel]]

def getSensorIrefsFeatureTarget(sensor_data,submodel,feature_id,cur,config,feature):
    feature_ids_per_submodel=getFeatureIdsPerSubmodel(submodel,cur,config)
    feature_type=getFeatureIdFromName(config,cur,feature)
    return [j for i in sensor_data for j in i['irefs_target'] if [True for k in feature_ids_per_submodel if k['feature']==feature_type and k['feature']==i['target_type'] and j.split('_')[1]==str(k['id']) and j.split('_')[1]==str(feature_id)]]
    
def getSensorIrefsTarget(sensor_data,submodel,cur,config,feature):
    feature_ids_per_submodel=getFeatureIdsPerSubmodel(submodel,cur,config)
    feature_type=getFeatureIdFromName(config,cur,feature)
    return [j for i in sensor_data for j in i['irefs_target'] if [True for k in feature_ids_per_submodel if k['feature']==feature_type and k['feature']==i['target_type'] and j.split('_')[1]==str(k['id'])]]
    
def getSensorIrefsFeatureSource(sensor_data,submodel,feature_id,cur,config,feature):
    feature_ids_per_submodel=getFeatureIdsPerSubmodel(submodel,cur,config)
    feature_type=getFeatureIdFromName(config,cur,feature)
    return [j for i in sensor_data for j in i['irefs_source'] if [True for k in feature_ids_per_submodel if k['feature']==feature_type and k['feature']==i['source_type'] and j.split('_')[1]==str(k['id']) and j.split('_')[1]==str(feature_id)]]

def getSensorDescriptionsSupervisory(sensor_data_source,sensor_data_target):
    #print('*/-')
    #print(sensor_data_target)
    sensor_description="""(TEXT-OBJECT :VALUE (ENGLISH "<meta name=\\"sensor-description\\"><b>Sensor descriptions:</b><br>"""
    sensor_description+="<br>".join(["<b>Int_Ref_Sensor_Source_"+j +"</b> --> "+"Source description='"+(i['description_source'] if i['description_source'] else "")+"'; Sensor ID='"+str(i['sensor_id'])+"'; Target feature ID`s='{}'".format(','.join([id.split('_')[1] for id in ([j] if i['function']==6 else i['irefs_target'])]))
                                        for i in sensor_data_source for j in i['irefs_source']])
    sensor_description+="<br>"
    sensor_description+="<br>".join(["<b>Int_Ref_Sensor_Target_"+j +"</b> --> "+"'; Target description='"+(i['description_target'] if i['description_target'] else "")+"'; Sensor ID='"+str(i['sensor_id'])+"'; Source feature ID`s='{}'".format(','.join([id.split('_')[1] for id in ([j] if i['function']==6 else i['irefs_source'])]))
                                    for i in sensor_data_target for j in i['irefs_target']])
    
    sensor_description+="""\") :AT ((8 380) (694 {})) :STYLE NOTE :MARKUP HTML)\n """.format(str((len(sensor_data_source)+len(sensor_data_target))*30+400))
    return sensor_description

def getSensorDescriptionsTemplate(sensor_data_source,sensor_data_target):
    sensor_description="""(TEXT-OBJECT :VALUE (ENGLISH "<meta name=\\"sensor-description\\"><b>Sensor descriptions:</b><br>"""
    sensor_description+="<br>".join(["<b>Int_Ref_Sensor_Source_"+str(i['sensor_id']) +"</b> --> "+"Source description='"+i['description_source']+"'; Sensor ID='"+str(i['sensor_id'])+"'; Source function='"+i['function_name']+"'; Source measure='"+i['measure_name']+"'; Target type='"+i['target_type_name']+
        "'; Target feature ID`s='" + ','.join(['Supervisory control' if iref.split('_')[1]=='X' else iref.split('_')[1] for iref in i['irefs_target']]) +"'"  
        for i in sensor_data_source])
    sensor_description+="<br>"
    sensor_description+="<br>".join(["<b>Int_Ref_Sensor_Target_"+str(i['sensor_id']) +"</b> --> "+"'; Target description='"+i['description_target']+"'; Sensor ID='"+str(i['sensor_id'])+"'; Source function='"+i['function_name']+"'; Source measure='"+i['measure_name']+"'; Source type='"+i['source_type_name']+
        "'; Source feature ID´s='"+','.join(['Supervisory control' if iref.split('_')[1]=='X' else iref.split('_')[1] for iref in i['irefs_source']]) +"'" 
        for i in sensor_data_target])
    sensor_description+="""\") :AT ((8 380) (694 {})) :STYLE NOTE :MARKUP HTML)\n """.format(str((len(sensor_data_source)+len(sensor_data_target))*30+400))
    return sensor_description
    
def delSensorConnection(file_data,remove_sensor_ids,type):
    data=[]
    for line in file_data:
        if [True for iref in ["""\"Int_Ref_Sensor_{}_{}""".format(str(type),str(sensor['sensor_id'])) for sensor in remove_sensor_ids] if iref in line]:
            data[-1]=data[-1].replace('\n','')+''.join([')' for i in range(line.count(')')-line.count('('))])+'\n'
        else:
            data.append(line)
    return data
    
def delSensorConnectionPList(plist,remove_sensor_ids,type):
    data=[]
    remove_sensor_names=["""\"Int_Ref_Sensor_{}_{}\"""".format(str(type),str(sensor['sensor_id'])) for sensor in remove_sensor_ids]
    #print(plist)
    for comp in plist:
        if getCompClass(comp)=='CONNECTIONS':
            new_conns=[]
            for conn in comp[':CONNS']:
                if conn[0][0] in remove_sensor_names or conn[1][0] in remove_sensor_names:
                    pass
                else:
                    new_conns.append(conn)
            comp[':CONNS']=new_conns
            data.append(comp)
        elif getCompClass(comp)==':IREF' and getCompName(comp) in remove_sensor_names:
            pass
        else: 
            data.append(comp)
    return data

def setPageHeightSensorDescription(file_data,sensors):
    data=[]
    for line in file_data:
        if """:PAGE-HEIGHT""" in line:
            old_height=float(line.split(':PAGE-HEIGHT')[1].strip().replace(')',''))
            height=sensors*30+old_height
            data.append(line.split(':PAGE-HEIGHT')[0]+":PAGE-HEIGHT "+str(height)+') \n')
        else:
            data.append(line)
    return data
    
def delSensorComp(file_data,remove_sensor_ids,type):
    data=[]
    del_index=[]
    counter=0
    while counter < len(file_data):
        while [True for iref in ["""\"Sensor_{}_{}""".format(str(type),str(sensor['sensor_id'])) for sensor in remove_sensor_ids] if iref in file_data[counter]]:
            data[-1]=data[-1].replace('\n','')+''.join([')' for i in range(file_data[counter].count(')')-file_data[counter].count('('))])+'\n'
            openCloseBracktesCounter=file_data[counter].count('(')-file_data[counter].count(')')
            counter+=1
            while openCloseBracktesCounter>0:
                openCloseBracktesCounter+=file_data[counter].count('(')-file_data[counter].count(')')
                counter+=1
                if counter>=len(file_data):
                    break
            if counter>=len(file_data):
                break
        if counter>=len(file_data):
            break
        data.append(file_data[counter])
        counter+=1
    return data
    
def getRemovedSensorSourceData(cur,config,source_types=[1,2,3],filter=""):
    #print('--------------getRemovedSensorSourceData------------')
    sql="""{}{}{}
EXCEPT
{}{}{};""".format("""SELECT sensor_id,type,unnest(templates) AS template, multi_signal FROM invoked_sensor_source_signals s WHERE s.type IN ({})""".format(','.join([str(i) for i in source_types])) if [True for i in source_types if i in [1,2]] else "", # nosec B608
        "\nUNION\n" if [True for i in source_types if i in [1,2]] and 3 in source_types else "", # nosec B608
        """SELECT sensor_id,type,NULL AS template,multi_signal FROM invoked_sensor_source_signals s WHERE s.type IN (3)""" if 3 in source_types else "", # nosec B608
        """SELECT s.sensor_id,s.type,t.template, False AS multi_signal
    FROM source_template t, sensor_source s
    WHERE t.source_id=s.sensor_id AND t.active=True AND s.type IN ({}) {}""".format(','.join([str(i) for i in source_types if i!=3]),filter) if [True for i in source_types if i in [1,2]] else "", # nosec B608
        "\nUNION\n" if [True for i in source_types if i in [1,2]] and 3 in source_types else "", # nosec B608
        """SELECT s.sensor_id,s.type,NULL AS template,CASE WHEN function=6 THEN True ELSE False END AS multi_signal
    FROM sensor_source s 
    WHERE s.type IN (3)""" if 3 in source_types else "") # nosec B608
    #print(sql)
    cur.execute(sql)
    return cur.fetchall()   

def getRemovedSensorTargetData(cur,config,target_types=[1,2,3],filter=""):
    #print('--------------getRemovedSensorTargetData------------')
    sql="""{}{}{}
EXCEPT
{}{}{};""".format("""SELECT sensor_id,type,unnest(templates) AS template, multi_signal FROM invoked_sensor_target_signals t WHERE t.type IN ({}) {}""".format(','.join([str(i) for i in target_types]),filter) if [True for i in target_types if i in [1,2]] else "", # nosec B608
        "\nUNION\n" if [True for i in target_types if i in [1,2]] and 3 in target_types else "", # nosec B608
        """SELECT sensor_id,type,NULL AS template,multi_signal FROM invoked_sensor_target_signals t WHERE t.type IN (3)""" if 3 in target_types else "", # nosec B608
        """SELECT t.sensor_id,t.type,t_temp.template, False AS multi_signal
    FROM target_template t_temp, sensor_target t, sensor_source s
    WHERE s.sensor_id=t.sensor_id AND t_temp.target_id=t.sensor_id AND t_temp.active=True AND t.type IN ({}) {}""".format(','.join([str(i) for i in target_types if i!=3]),filter) if [True for i in target_types if i in [1,2]] else "", # nosec B608
        "\nUNION\n" if [True for i in target_types if i in [1,2]] and 3 in target_types else "", # nosec B608
        """SELECT t.sensor_id,t.type,NULL AS template,CASE WHEN s.function=6 and t.type=3 THEN True ELSE False END AS multi_signal
    FROM sensor_target t, sensor_source s
    WHERE s.sensor_id=t.sensor_id AND t.type IN (3)""" if 3 in target_types else "") # nosec B608
    #print(sql)
    cur.execute(sql)
    return cur.fetchall()    

def getAddedSensorSourceData(cur,config,source_types=[1,2,3],filter=""):
    #print('--------------getAddedSensorSourceData------------')
    sql="""{}{}{}
EXCEPT
{}{}{};""".format("""SELECT s.sensor_id,s.type,t.template,s.test_value, False AS multi_signal
    FROM source_template t, sensor_source s
    WHERE t.source_id=s.sensor_id AND t.active=True AND s.type IN ({}) {}""".format(','.join([str(i) for i in source_types if i!=3]),filter) if [True for i in source_types if i in [1,2]] else "", # nosec B608
        "\nUNION\n" if [True for i in source_types if i in [1,2]] and 3 in source_types else "", # nosec B608
        """SELECT s.sensor_id,s.type,NULL AS template,s.test_value, CASE WHEN function=6 THEN True ELSE False END AS multi_signal
    FROM sensor_source s 
    WHERE s.type IN (3) """ if 3 in source_types else "", # nosec B608
        """SELECT sensor_id,type,unnest(templates) AS template,test_value,multi_signal FROM invoked_sensor_source_signals s WHERE s.type IN ({})""".format(','.join([str(i) for i in source_types])) if [True for i in source_types if i in [1,2]] else "", # nosec B608
        "\nUNION\n" if [True for i in source_types if i in [1,2]] and 3 in source_types else "", # nosec B608
        """SELECT sensor_id,type,NULL AS template,test_value,multi_signal FROM invoked_sensor_source_signals s WHERE s.type IN (3)""" if 3 in source_types else "") # nosec B608
    #print(sql)
    cur.execute(sql)
    return cur.fetchall()

def getAddedSensorTargetData(cur,config,target_types=[1,2,3],filter=""):
    #print('-------------getAddedSensorTargetData-----------------')
    sql="""{}{}{}
EXCEPT
{}{}{};""".format(
    """SELECT t.sensor_id,t.type,t_temp.template, t.test_value, False AS multi_signal
    FROM target_template t_temp, sensor_target t
    WHERE t_temp.target_id=t.sensor_id AND t_temp.active=True AND t.type IN ({}) {}""".format(','.join([str(i) for i in target_types if i!=3]),filter) if [True for i in target_types if i in [1,2]] else "", # nosec B608
    "\nUNION\n" if [True for i in target_types if i in [1,2]] and 3 in target_types else "", # nosec B608
        """SELECT t.sensor_id,t.type,NULL AS template,t.test_value, CASE WHEN s.function=6 and t.type=3 THEN True ELSE False END AS multi_signal
    FROM sensor_target t, sensor_source s
    WHERE s.sensor_id=t.sensor_id AND t.type IN (3)""" if 3 in target_types else "", # nosec B608
        """SELECT sensor_id,type,unnest(templates) AS template,test_value,multi_signal FROM invoked_sensor_target_signals t WHERE t.type IN ({}) {}""".format(','.join([str(i) for i in target_types]),filter) if [True for i in target_types if i in [1,2]] else "", # nosec B608
        "\nUNION\n" if [True for i in target_types if i in [1,2]] and 3 in target_types else "", # nosec B608
        """SELECT sensor_id,type,NULL AS template,test_value,multi_signal FROM invoked_sensor_target_signals t WHERE t.type IN (3)""" if 3 in target_types else "") # nosec B608
    #print(sql)
    cur.execute(sql)
    return cur.fetchall()

def writeInvokedSensorSourceSignals (cur,config,add_sensor_source_idsValues):
    #print(add_sensor_source_idsValues)
    if add_sensor_source_idsValues:
        sensor_data = {}
        for entry in add_sensor_source_idsValues:
            sensor_id = entry['sensor_id']
            template = entry['template']
            if sensor_id not in sensor_data:
                sensor_data[sensor_id]={'templates':[template],'source_type':entry['type'],'test_value': entry['test_value'],'multi_signal': entry['multi_signal']}
            else:
                if template not in sensor_data[sensor_id]['templates']:
                    sensor_data[sensor_id]['templates'].append(template)
        #print(sensor_data)
                
        for sensor in sensor_data:
            #print(sensor)
            sql="\n".join(["""INSERT INTO invoked_sensor_source_signals(sensor_id,type,templates,multi_signal,test_value) VALUES ({},{},array{}::INTEGER[],{},{})
    ON CONFLICT (sensor_id)
    DO UPDATE SET
        templates = invoked_sensor_source_signals.templates || EXCLUDED.templates,
        multi_signal = EXCLUDED.multi_signal,
        test_value = EXCLUDED.test_value;""".format( # nosec B608
                sensor,sensor_data[sensor]['source_type'],sensor_data[sensor]['templates'] if sensor_data[sensor]['templates']!=[None] else '[]',sensor_data[sensor]['multi_signal'],'NULL' if not sensor_data[sensor]['test_value'] else sensor_data[sensor]['test_value'])]) # nosec B608
        #print(sql)
        cur.execute(sql)
  
def writeInvokedSensorTargetSignals (cur,config,add_target_idsValues):
    if add_target_idsValues:
        sensor_data = {}
        for entry in add_target_idsValues:
            sensor_id = entry['sensor_id']
            template = entry['template']
            if sensor_id not in sensor_data:
                sensor_data[sensor_id]={'templates':[template],'target_type':entry['type'],'test_value': entry['test_value'],'multi_signal': entry['multi_signal']}
            else:
                if template not in sensor_data[sensor_id]['templates']:
                    sensor_data[sensor_id]['templates'].append(template)
        for sensor in sensor_data:
            #print(sensor)
            #print(sensor_data[sensor])
            sql="\n".join(["""INSERT INTO invoked_sensor_target_signals(sensor_id,type,templates,multi_signal,test_value) VALUES ({},{},array{}::INTEGER[],{},{})
    ON CONFLICT (sensor_id)
    DO UPDATE SET
        templates = invoked_sensor_target_signals.templates || EXCLUDED.templates,
        multi_signal = EXCLUDED.multi_signal,
        test_value = EXCLUDED.test_value;""".format( # nosec B608
                sensor,sensor_data[sensor]['target_type'],sensor_data[sensor]['templates'] if sensor_data[sensor]['templates']!=[None] else '[]',sensor_data[sensor]['multi_signal'],'NULL' if not sensor_data[sensor]['test_value'] else sensor_data[sensor]['test_value'])]) # nosec B608
        #print(sql)
        cur.execute(sql) 

def getSensorData(cur,config,execute_query=True,source_types=[1,2,3],target_types=[1,2,3],filter=""):
    sql="""WITH sub AS(
	WITH sub AS(
		WITH sub AS(
			WITH sub AS(
			     --customer (type:1); temp,mass,p(measure:1,2,3) 
                (SELECT s.sensor_id, f.id::text  AS feature_id, b_t_conns.conn_bundle_type_id::text, b_t_conns.conn_type_id::text, c_t_conns.connection_id::text
                        FROM {}.customers f, customer_templates f_t, bundle_type_conns b_t_conns, connection_type_connections c_t_conns, sensor_source s,
                            (SELECT source_id, conn_type FROM source_conn_type WHERE active=True GROUP BY source_id,conn_type) s_ct, 
                            (SELECT source_id, connection_id FROM source_conns 
                                WHERE active=True  
                                GROUP BY source_id,connection_id)  s_c
                        WHERE f.template=f_t.template AND b_t_conns.conn_bundle_type_id=f_t.conn_bundle_type
                            AND b_t_conns.conn_type_id=s_ct.conn_type AND s.sensor_id=s_ct.source_id AND s_c.source_id=s.sensor_id 
                            AND s_c.connection_id=c_t_conns.connection_id AND c_t_conns.connection_type_id=b_t_conns.conn_type_id AND s_c.source_id=s.sensor_id AND s.type=1
                        GROUP BY s.sensor_id, f.id, b_t_conns.conn_bundle_type_id, b_t_conns.conn_type_id, c_t_conns.connection_id
                        ORDER BY s.sensor_id, f.id)
				UNION
                --plant (type:2); temp,mass,p(measure:1,2,3) 
                (SELECT s.sensor_id, f.id::text, b_t_conns.conn_bundle_type_id::text, b_t_conns.conn_type_id::text, c_t_conns.connection_id::text
                        FROM {}.energy_plants f, energy_plant_templates f_t, bundle_type_conns b_t_conns, connection_type_connections c_t_conns, sensor_source s,
                            (SELECT source_id, conn_type FROM source_conn_type WHERE active=True GROUP BY source_id,conn_type) s_ct, 
                            (SELECT source_id, connection_id FROM source_conns 
                                WHERE active=True  
                                GROUP BY source_id,connection_id)  s_c
                        WHERE f.template=f_t.template AND b_t_conns.conn_bundle_type_id=f_t.conn_bundle_type
                            AND b_t_conns.conn_type_id=s_ct.conn_type AND s.sensor_id=s_ct.source_id AND s_c.source_id=s.sensor_id AND s.sensor_id=s.sensor_id
                            AND s_c.connection_id=c_t_conns.connection_id AND c_t_conns.connection_type_id=b_t_conns.conn_type_id AND s_c.source_id=s.sensor_id AND s.type=2
                        GROUP BY s.sensor_id, f.id, b_t_conns.conn_bundle_type_id, b_t_conns.conn_type_id, c_t_conns.connection_id
                        ORDER BY s.sensor_id, f.id)
                UNION
				--customer (type:1); power(measure:4) 
                (SELECT s.sensor_id, f.id::text, b_t_conns.conn_bundle_type_id::text, b_t_conns.conn_type_id::text,'X'
                        FROM {}.customers f, customer_templates f_t, bundle_type_conns b_t_conns, sensor_source s,
                            (SELECT source_id, conn_type FROM source_conn_type WHERE active=True GROUP BY source_id,conn_type) s_ct
                        WHERE f.template=f_t.template AND b_t_conns.conn_bundle_type_id=f_t.conn_bundle_type
                            AND b_t_conns.conn_type_id=s_ct.conn_type AND s.sensor_id=s_ct.source_id AND s.measure=4 AND s.type=1
                        GROUP BY s.sensor_id, f.id, b_t_conns.conn_bundle_type_id, b_t_conns.conn_type_id
                        ORDER BY s.sensor_id, f.id)
				UNION
                --plant (type:2); power(measure:4) 
                (SELECT s.sensor_id, f.id::text, b_t_conns.conn_bundle_type_id::text, b_t_conns.conn_type_id::text,'X'
                        FROM {}.energy_plants f, energy_plant_templates f_t, bundle_type_conns b_t_conns, sensor_source s,
                            (SELECT source_id, conn_type FROM source_conn_type WHERE active=True GROUP BY source_id,conn_type) s_ct
                        WHERE f.template=f_t.template AND b_t_conns.conn_bundle_type_id=f_t.conn_bundle_type
                            AND b_t_conns.conn_type_id=s_ct.conn_type AND s.sensor_id=s_ct.source_id AND s.measure=4 AND s.type=2
                        GROUP BY s.sensor_id, f.id, b_t_conns.conn_bundle_type_id, b_t_conns.conn_type_id
                        ORDER BY s.sensor_id, f.id)
                UNION
				--customer; custom (measure:5) 
                (SELECT s.sensor_id, f.id::text, 'X', 'X','X'
                        FROM  sensor_source s,{}.customers f
                        WHERE s.measure=5 AND s.type=1
                        GROUP BY s.sensor_id, f.id
                        ORDER BY s.sensor_id, f.id)
				UNION
				--plant; custom (measure:5) 
                (SELECT s.sensor_id, f.id::text, 'X', 'X','X'
                        FROM  sensor_source s,{}.energy_plants f
                        WHERE s.measure=5 AND s.type=2
                        GROUP BY s.sensor_id, f.id
                        ORDER BY s.sensor_id, f.id)
				--supervisory ctrl source ;customer target; custom (measure:5) 
                UNION
                (SELECT s.sensor_id, CASE WHEN s.function=6 THEN f.id::text ELSE 'X' END AS feature_id, 'X', 'X','X'
                        FROM sensor_source s, sensor_target t,target_template t_t, {}.customers f
                        WHERE s.type=3 AND s.sensor_id=t.sensor_id AND t_t.target_id=t.sensor_id AND t_t.active =True AND f.template = t_t.template AND t.type=1
                        GROUP BY s.sensor_id,s.function,f.id
                        ORDER BY s.sensor_id,f.id)
				--supervisory ctrl source ;energy_plants target; custom (measure:5) 
                UNION
                (SELECT s.sensor_id, CASE WHEN s.function=6 THEN f.id::text ELSE 'X' END AS feature_id, 'X', 'X','X'
                        FROM sensor_source s, sensor_target t,target_template t_t, {}.energy_plants f
                        WHERE s.type=3 AND s.sensor_id=t.sensor_id AND t_t.target_id=t.sensor_id AND t_t.active =True AND f.template = t_t.template AND t.type=2
                        GROUP BY s.sensor_id,s.function,f.id
                        ORDER BY s.sensor_id,f.id)
			)
            SELECT sub.sensor_id, s.function, s.type, sub.feature_id,
                replace(replace(ARRAY_AGG(sub.sensor_id||'_'||sub.feature_id||'_'||conn_type_id||'_'||connection_id)::text,'{{',''),'}}','') AS irefs_source 
                FROM sub, sensor_source s WHERE s.sensor_id=sub.sensor_id GROUP BY s.function,sub.sensor_id,sub.feature_id,conn_type_id, s.type

		)		        
		SELECT sub.sensor_id, function, unnest(string_to_array(irefs_source,',')) AS irefs_source, sub.feature_id,sub.type,at_names.template_name,at_names.type AS at_names_type, at_names.feature_id AS at_names_feature_id
            FROM sub,
                (SELECT at.type, f.feature_id, at.template_name 
                                        FROM
                                            (SELECT 1 AS type,template,'1'||':'||template::text||'_'||template_name AS template_name FROM customer_templates
                                            UNION
                                            SELECT 2 AS type,template,'2'||':'||template::text||'_'||template_name AS template_name FROM energy_plant_templates) at,
                                            (SELECT 1 AS type,id::text AS feature_id,template FROM {}.customers
                                            UNION
                                            SELECT 2 AS type,id::text AS feature_id,template FROM {}.energy_plants) f
                                        WHERE at.type=f.type AND at.template=f.template) at_names
            GROUP BY at_names.type,at_names.feature_id,at_names.template_name,sub.type,sub.sensor_id, sub.feature_id,function,unnest(string_to_array(irefs_source,',')) 
	)
	SELECT b.sensor_id, sub.type,b.function, CASE WHEN sub.function=6 AND a.target_type=3 THEN b.irefs_source ELSE a.irefs_target END AS irefs_target, b.irefs_source, c.source_template_name, d.target_template_name
        FROM sub,
            (--Customer target irefs
                SELECT t.sensor_id, ARRAY_AGG(t.sensor_id::text||'_'||f.id::text||'_X_X'::text ORDER BY t.sensor_id,f.id) AS irefs_target, t.type AS target_type
                FROM sensor_target t, {}.customers f
                WHERE  t.type =1
                GROUP BY t.sensor_id,t.type
            UNION
            --Energy plants target irefs
            SELECT t.sensor_id, ARRAY_AGG(t.sensor_id::text||'_'||f.id::text||'_X_X'::text ORDER BY t.sensor_id,f.id) AS irefs_target, t.type AS target_type
                FROM sensor_target t, {}.energy_plants f
                WHERE  t.type =2
                GROUP BY t.sensor_id,t.type
            UNION
            SELECT t.sensor_id, ARRAY_AGG(t.sensor_id::text||'_X_X_X'::text ORDER BY t.sensor_id) AS irefs_target, t.type AS target_type
                FROM sensor_target t
                WHERE t.type IN (3,4)  
                GROUP BY t.sensor_id,t.type
            ) a,
            (WITH sub AS (SELECT sub.sensor_id, sub.function, sub.irefs_source FROM sub GROUP BY sub.sensor_id, sub.function, sub.irefs_source)
            SELECT  sub.sensor_id, sub.function, ARRAY_AGG(sub.irefs_source ORDER BY CASE WHEN split_part(irefs_source,'_',1) ~ '^[0-9\.]+$' THEN split_part(irefs_source,'_',1)::integer ELSE 0 END) AS irefs_source FROM sub GROUP BY sub.sensor_id, sub.function) b,
            (WITH sub2 AS(WITH sub1 AS (SELECT sub.sensor_id, sub.function, sub.feature_id,sub.type,sub.template_name FROM sub 
                                        WHERE (sub.at_names_type=sub.type AND sub.at_names_feature_id=sub.feature_id) OR sub.type=3
                                        GROUP BY sub.template_name,sub.type,sub.sensor_id, sub.function,sub.feature_id)
                            SELECT sub1.sensor_id, sub1.function,CASE WHEN sub1.type=3 THEN 'X' ELSE sub1.template_name END AS source_template_name FROM sub1
                                GROUP BY sub1.sensor_id, sub1.function,sub1.type,sub1.template_name)
            SELECT sub2.sensor_id, sub2.function,ARRAY_AGG(sub2.source_template_name) AS source_template_name FROM sub2 GROUP BY sub2.sensor_id, sub2.function) c,    
            (WITH sub AS(
                SELECT t.sensor_id,sub.template_name AS target_template_name
                    FROM sub, sensor_target t
                    WHERE  t.sensor_id=sub.sensor_id AND sub.at_names_type=t.type --AND sub.at_names_feature_id=t_ids.feature_id::text
                    GROUP BY t.sensor_id,sub.feature_id,sub.template_name
                UNION
                SELECT t.sensor_id, 'supervisory_control' AS target_template_name
                    FROM sub, sensor_target t
                    WHERE t.type =3 AND t.sensor_id=sub.sensor_id
                    GROUP BY t.sensor_id
                UNION
                SELECT t.sensor_id, 'results' AS target_template_name
                    FROM sub, sensor_target t
                    WHERE t.type =4 AND t.sensor_id=sub.sensor_id
                    GROUP BY t.sensor_id
                )
            SELECT sub.sensor_id,ARRAY_AGG(sub.target_template_name::text) AS target_template_name FROM sub GROUP BY sub.sensor_id) d   
        WHERE c.sensor_id=d.sensor_id AND c.sensor_id=a.sensor_id AND a.sensor_id=b.sensor_id AND sub.sensor_id=a.sensor_id
        GROUP BY sub.type,c.source_template_name, d.target_template_name, b.sensor_id, b.function, a.irefs_target,b.irefs_source,sub.function, target_type
)
SELECT sub.sensor_id AS sensor_id, s.type AS source_type, type2.name AS source_type_name, sub.source_template_name AS source_template_names, t.type AS target_type, type1.name AS target_type_name, sub.target_template_name AS target_template_names,
    sub.function, s_f.function AS function_name, s.measure, m.measure AS measure_name, 
    sub.irefs_source,sub.irefs_target, s.test_value,s.description AS description_source, t.description AS description_target
    FROM sub, sensor_source s, sensor_target t, signal_function s_f, measure m, type type1, type type2
    WHERE s.sensor_id=sub.sensor_id AND t.sensor_id=s.sensor_id AND m.id=s.measure 
	AND s_f.id=s.function AND type1.id=t.type AND type2.id=s.type AND s.type IN ({}) AND t.type IN ({}) 
    GROUP BY sub.source_template_name, sub.target_template_name, s.measure,sub.function,sub.sensor_id, s.type, t.type, type1.name, type2.name, s_f.function, m.measure, s.test_value,sub.irefs_source,s.description, t.description,irefs_target
    ORDER BY sub.sensor_id;""".format( # nosec B608
    config['versionName'],config['versionName'],config['versionName'],config['versionName'],config['versionName'], # nosec B608
    config['versionName'],config['versionName'],config['versionName'],config['versionName'],config['versionName'], # nosec B608
    config['versionName'],config['versionName'], # nosec B608
    ','.join([str(i) for i in source_types]),','.join([str(i) for i in target_types]),filter) # nosec B608
    #print(sql)   
    if execute_query:
        cur.execute(sql)
        return cur.fetchall()  
    else:
        return sql

def delSensorDescription(file_data):
    data=[]
    for line in file_data:
        if not """<meta name=\\"sensor-description\\">""" in line:
            data.append(line)
    return data
        
class NetworkSensorSignals():
    def __init__(self,cur,config,dir):
    
        #print('%%%%%%%&&&&&&&&&&&&&&&&%%%%%%%%%%%%%%%')
        sensor_source_ids=getTableIds(cur,config['versionName'],'sensor_source','sensor_id')
        #print(sensor_source_ids)
        
        sensor_target_ids=getTableIds(cur,config['versionName'],'sensor_target','sensor_id')
        #print(sensor_target_ids)
        
        #sensor idm macro file
        file=dir+"""\\Sensor-macro.idm"""
        data=[""";IDA {} Data UTF-8\n""".format(getIDAVersion(config)),"""(DOCUMENT-HEADER :TYPE DISTRICTS-MACRO :D "Districts macro" :APP (DISTRICTS :VER {}))\n""".format(getIDADistrictsVersion(config))]
        writeToFileFromList(data,dir,file)
        
        #sensor idc macro file
        file=dir+"""\\Sensor-macro.idc"""
        data=[""";IDA {} Form UTF-8\n""".format(getIDAVersion(config)),"""(DOCUMENT-HEADER :TYPE SCHEMA :PAGE-WIDTH 178 :PAGE-HEIGHT 97)\n""","""(SELF-FRAME :AT ((352 190)) :R (342 176) :SLOT (:SELF) :DATA MACRO-OBJECT)\n"""]
        writeToFileFromList(data,dir,file)
        
class templatesensorSignals():
    def __init__(self,cur,config,dir,template_name,type,add_sensor_source_idsValues,add_sensor_target_idsValues,remove_sensor_source_ids,remove_sensor_target_ids):
        #print('&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&')
        #print(dir)
        #print(template_name)
        
        #get number of old sensor target signals --> for component placement in .idc
        sql="""WITH sub AS(
    SELECT sensor_id,unnest(templates) AS template
        FROM invoked_sensor_target_signals
        WHERE type = {}
)
SELECT count(sub.template) FROM sub WHERE sub.template={};""".format(type,template_name.split('_')[0]) # nosec B608
        #print(sql)
        #cur.execute(sql)
        #numberOf_oldSensorTargets=cur.fetchone()['count']      
        numberOf_oldSensorTargets=1        
        
        #print(add_sensor_source_idsValues)
        #print(remove_sensor_source_ids)            
        #print(add_sensor_target_idsValues)
        #print(remove_sensor_target_ids)      
        
        #template idm project file
        #print(dir)
        file=dir+'\\'+template_name+'.idm'
        #print(file)
        file_data=""
        if os.path.exists(file):
            #read file --> remove deleted connections --> add new connections
            file_data=readFileToList(file)
            #print(file_data)
            file_data=delSensorConnection(file_data,remove_sensor_target_ids,'Target')    
            file_data=delSensorConnection(file_data,remove_sensor_source_ids,'Source')              
            
            #print(file_data)
            #print('++++++++++++++---------+++++/////////')
            if add_sensor_source_idsValues or add_sensor_target_idsValues:
                data=[]
                connections=False
                for line in file_data:
                    data.append(line)
                    if """(MACRO-OBJECT :N "{}\"""".format(template_name) in line:
                        idx=file_data.index(line)
                        if file_data[idx].count('(')-file_data[idx].count(')')==0:
                            data[-1]=data[-1].replace('\n','').rstrip()[:-1]+'\n'
                            data.append(''.join([""" (:IREF :N "Int_Ref_Sensor_Source_{}" :T OUT :F 224)\n""".format(str(i['sensor_id'])) for i in add_sensor_source_idsValues]))
                            data.append(''.join([""" (:IREF :N "Int_Ref_Sensor_Target_{}" :T IN :F 208)\n""".format(str(i['sensor_id'])) for i in add_sensor_target_idsValues]))
                            data[-1]+=")\n"
                        else:
                            data.append(''.join([""" (:IREF :N "Int_Ref_Sensor_Source_{}" :T OUT :F 224)\n""".format(str(i['sensor_id'])) for i in add_sensor_source_idsValues]))
                            data.append(''.join([""" (:IREF :N "Int_Ref_Sensor_Target_{}" :T IN :F 208)\n""".format(str(i['sensor_id'])) for i in add_sensor_target_idsValues]))
                    if """(MACRO-OBJECT :N "Sensor-macro\"""" in line:
                        idx=file_data.index(line)
                        if file_data[idx].count('(')-file_data[idx].count(')')==0:
                            data[-1]=data[-1].replace('\n','').rstrip()[:-1]+'\n'
                            data.append('\n'.join([""" (:IREF :N "Int_Ref_Sensor_Target_{}" :T OUT :F 224)""".format(str(i['sensor_id'])) for i in add_sensor_target_idsValues]))
                            data[-1]+=")\n"
                        else:
                            data.append('\n'.join([""" (:IREF :N "Int_Ref_Sensor_Target_{}" :T OUT :F 224)""".format(str(i['sensor_id'])) for i in add_sensor_target_idsValues]))
                    if """(CONNECTIONS""" in line:
                        connections=True
                        idx=file_data.index(line)
                        if file_data[idx].count('(')-file_data[idx].count(')')==0:
                            if data[-1].replace('\n','').rstrip()[:-1].split('CONNECTIONS')[1]:
                                data[-1]='(CONNECTIONS \n'+data[-1].replace('\n','').rstrip()[:-1].split('CONNECTIONS')[1]+'\n'
                            else:
                                data[-1]='(CONNECTIONS \n'                               
                            data.append('\n'.join([""" (("Sensor-macro" "Int_Ref_Sensor_Target_{}") ("{}" "Int_Ref_Sensor_Target_{}") 0 0 NIL)""".format(str(i['sensor_id']),template_name,str(i['sensor_id'])) for i in add_sensor_target_idsValues]))
                            data[-1]+=")"
                        else:
                            data.append(''.join([""" (("Sensor-macro" "Int_Ref_Sensor_Target_{}") ("{}" "Int_Ref_Sensor_Target_{}") 0 0 NIL)\n""".format(str(i['sensor_id']),template_name,str(i['sensor_id'])) for i in add_sensor_target_idsValues]))
                if not connections and [True for i in add_sensor_target_idsValues if i[4]==1]:
                    connections="(CONNECTIONS \n"
                    connections+='\n'.join([""" (("Sensor-macro" "Int_Ref_Sensor_Target_{}") ("{}" "Int_Ref_Sensor_Target_{}") 0 0 NIL)""".format(str(i['sensor_id']),template_name,str(i['sensor_id'])) for i in add_sensor_target_idsValues])+')'
                    data.append(connections)
                writeToFileFromList(data,dir,file)
            else:
                writeToFileFromList(file_data,dir,file)
                
        dir+='\\'+template_name
        
        #template macro idm
        file=dir+'\\'+template_name+'.idm'
        file_data=""
        if os.path.exists(file):
            #read file --> remove deleted connections --> add new connections
            file_data=readFileToList(file)
            file_data=delSensorConnection(file_data,remove_sensor_source_ids,'Source')
            file_data=delSensorConnection(file_data,remove_sensor_target_ids,'Target')
            file_data=self.removeHCModeLink(file_data,remove_sensor_target_ids)
            #todo if needed
            #if [True for i in add_sensor_target_idsValues if i['target']==2]:
            #    file_data=self.removeHCModeConnection(file_data)
            #    file_data=self.addHCModeLink(file_data,add_sensor_target_idsValues)
            if add_sensor_source_idsValues:
                file_data.insert(2,''.join(["""(:IREF :N "Int_Ref_Sensor_Source_{}" :T OUT :F 224)\n""".format(str(i['sensor_id'])) for i in add_sensor_source_idsValues]))
            if add_sensor_target_idsValues:
                file_data.insert(2,''.join(["""(:IREF :N "Int_Ref_Sensor_Target_{}" :T IN :F 208)\n""".format(str(i['sensor_id'])) for i in add_sensor_target_idsValues]))
            writeToFileFromList(file_data,dir,file)
            
        #template macro idc
        file=dir+'\\'+template_name+'.idc'
        file_data=""
        if os.path.exists(file):
            #read file --> remove deleted connections --> add new connections
            file_data=readFileToList(file)
            file_data=delSensorConnection(file_data,remove_sensor_source_ids,'Source')
            file_data=delSensorConnection(file_data,remove_sensor_target_ids,'Target')
            file_data=delSensorDescription(file_data)
            file_data=setPageHeightSensorDescription(file_data,(len(add_sensor_source_idsValues)+len(add_sensor_target_idsValues)-len(remove_sensor_source_ids)-len(remove_sensor_target_ids)))
            
            #todo: update if still needed
            #if [True for i in add_sensor_target_idsValues if i['target']==2]:
            #    file_data=self.removeHCModeConnection(file_data)
                
            sensor_data_source=getSensorData(cur,config,source_types=[type],filter=" AND s.measure=5")
            sensor_data_target=getSensorData(cur,config,target_types=[type],filter="")
            #print('---------------------------+++++++++++++++-----------------------')

            #print(sensor_data_source)
            #print(sensor_data_target)
            #print('++')
            sensor_data_source=[sensor for sensor in sensor_data_source for at_name in sensor['source_template_names'] if at_name==str(type)+':'+template_name]
            sensor_data_target=[sensor for sensor in sensor_data_target for at_name in sensor['target_template_names'] if at_name==str(type)+':'+template_name]
            #print(sensor_data_source)
            #print(sensor_data_target)
                
            
            sensor_description=getSensorDescriptionsTemplate(sensor_data_source,sensor_data_target)
            file_data.append(sensor_description)
            writeToFileFromList(file_data,dir,file)
      
        #sensor idm macro file
        file=dir+"""\\Sensor-macro.idm"""
        if os.path.exists(file):
            #read file --> remove deleted connections --> add new connections
            file_data=readFileToList(file)
            file_data=delSensorConnection(file_data,remove_sensor_target_ids,'Target')
            file_data=delSensorComp(file_data,remove_sensor_target_ids,'Target')
            if add_sensor_target_idsValues:
                file_data.insert(2,''.join(["""((:EO :N "Sensor_Target_{}" :T ADDER)
 (:VAR :N INSIGNAL :B #S(MS-SPARSE DEFAULT-VALUE NIL DIMENSION 1 VALUE ((1 . {}))))
 (:PAR :N N_IN :V 1))\n""".format(str(i['sensor_id']),str(i['test_value'])) for i in add_sensor_target_idsValues]))
                file_data.insert(2,''.join(["""(:IREF :N "Int_Ref_Sensor_Target_{}" :T OUT :F 224)\n""".format(str(i['sensor_id'])) for i in add_sensor_target_idsValues]))
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
                            data.append('\n'.join([""" (("Sensor_Target_{}" OUTSIGNALLINK) "Int_Ref_Sensor_Target_{}" 0 0 NIL)""".format(str(i['sensor_id']),str(i['sensor_id'])) for i in add_sensor_target_idsValues])) 
                            data[-1]+=")"
                            
                        else:
                            data.append(''.join([""" (("Sensor_Target_{}" OUTSIGNALLINK) "Int_Ref_Sensor_Target_{}" 0 0 NIL)\n""".format(str(i['sensor_id']),str(i['sensor_id'])) for i in add_sensor_target_idsValues]))  
                if not connections and [True for i in add_sensor_target_idsValues]:
                    connections="(CONNECTIONS \n"
                    connections+='\n'.join([""" (("Sensor_Target_{}" OUTSIGNALLINK) "Int_Ref_Sensor_Target_{}" 0 0 NIL)""".format(str(i['sensor_id']),str(i['sensor_id'])) for i in add_sensor_target_idsValues])+')'
                    data.append(connections)
                writeToFileFromList(data,dir,file)
            else:
                writeToFileFromList(file_data,dir,file)
                
        #sensor idc macro file
        file=dir+"""\\Sensor-macro.idc"""
        if os.path.exists(file):
            #read file --> remove deleted connections --> add new connections
            file_data=readFileToList(file)
            file_data=delSensorConnection(file_data,remove_sensor_target_ids,'Target')
            file_data=delSensorComp(file_data,remove_sensor_target_ids,'Target')
            if add_sensor_target_idsValues:
                file_data.insert(2,''.join(["""(EQUATION-FRAME :AT ((643 {})) :R (16 16) :ICON "lib:adder.ids" :SLOT ("Sensor_Target_{}") :NAME "Sensor_Target_{}" :PADDING 3 :DATA :EO)\n""".format(str(50+35*i[0]),i[1],i[1]) for i in enumerate([i['sensor_id'] for i in add_sensor_target_idsValues],numberOf_oldSensorTargets+1)]))
                file_data.insert(2,''.join(["""(CONNECTION-LINE :AT ((660 {}) (694 {})) :FIRST-LINK ("Sensor_Target_{}" (0 0.491) OUTSIGNALLINK) :LAST-LINK (:SELF (0.0 0.144) "Int_Ref_Sensor_Target_{}") :DIR :RIGHT :ARROW (19 8 8))\n""".format(str(50+35*(i[0])),str(50+35*(i[0])),i[1],i[1]) for i in enumerate([i['sensor_id'] for i in add_sensor_target_idsValues],numberOf_oldSensorTargets+1)]))
            writeToFileFromList(file_data,dir,file)            

    def removeHCModeConnection(self,file_data):
        return [line for line in file_data if not '|HCMode|' in line]
        
    def removeHCModeLink(self,file_data,remove_sensor_target_ids):
        counter=0
        data=[]
        while counter < len(file_data):
            if [True for sensor in ["""|HCMode_var| :B (:SYSTEM "Sensor-macro" "Sensor_Target_{}\"""".format(str(i['sensor_id'])) for i in remove_sensor_target_ids] if sensor in file_data[counter]]:
                counter+=1
            data.append(file_data[counter])
            counter+=1
        return data
        
    def addHCModeLink(self,file_data,add_sensor_target_idsValues):
        #print('--------------++++++++++/////////')
        data=[]
        for line in file_data:
            data.append(line)
            if """((MODEL :N "load model" :T""" in line:
                data.append(""" (:VAR :N |HCMode_var| :B (:SYSTEM "Sensor-macro" "Sensor_Target_{}" OUTSIGNAL))\n""".format(str([i['sensor_id'] for i in add_sensor_target_idsValues if i['target']==2])))
        return data  
        
        
        
            
            
            