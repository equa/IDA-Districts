from pyparsing import OneOrMore, nestedExpr
from plugins.utility_functions.files import *
from plugins.utility_functions.sensor_signals import *
from plugins.utility_functions.ida_components import *
from plugins.utility_functions.db import *
import psycopg2.extras
import psycopg2
from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT
dictDB={'pwd' : 'p3t3r' , 'host' : 'localhost','port':'5433', 'user' : 'postgres', 'projectName' : 'cosim_test1', 'versionName' : 'b'}
conn=dbConnect(dictDB,True)
cur=conn.cursor(cursor_factory = psycopg2.extras.RealDictCursor)
import math
import os

plugin_dir="""C:\\Users\\Peter\\AppData\\Roaming\\QGIS\\QGIS3\\profiles\\default\\python\\plugins\\"""
source_dir=plugin_dir+"ida_districts_modeling_simulation\\network_models\\cosim_test1\\b\\invoked_customers"
 
def getDecoupledFeatureCompPerFeature(feature,cur,dictDB):
    sql="""SELECT f_dec.comp_name
    FROM {}.{}s f, {}.feature_decoupling f_dec
    WHERE f.id={} AND f.assettype=f_dec.assettype AND f.assetgroup=f_dec.assetgroup AND f_dec.type='{}';""".format(
        dictDB['versionName'],feature['feature'],dictDB['versionName'],feature['id'],feature['feature'])
    print(sql)
    cur.execute(sql)
    return [i['comp_name'] for i in cur.fetchall()]

def getModelInterfaces(model):
    """from network view"""
    models={'|hx|': {'import':['|mLiqB|','|TsupB|','|PhiHxLimit_var|','|TbSet_var|'],'export':['|TbOut|']}}
    try:
        return models[model] 
    except:
        return ''

    
def getDataEx(conns_idc,dec_models,components_idm,network_side,sensor_data,submodel,feature_id):
    data_ex=[]
    print(network_side)

    for conn_idc in conns_idc:
        #print(conn_idc)
        if conn_idc[':FIRST-LINK'][0].replace('"','') in dec_models and conn_idc[':LAST-LINK'][0].replace('"','') not in dec_models or conn_idc[':FIRST-LINK'][0].replace('"','') not in dec_models and conn_idc[':LAST-LINK'][0].replace('"','') in dec_models:
            if conn_idc[':FIRST-LINK'][0].replace('"','') in dec_models and conn_idc[':LAST-LINK'][0].replace('"','') not in dec_models:
                model_name=conn_idc[':FIRST-LINK'][0]
                link=conn_idc[':FIRST-LINK'][2]
                model_name_connected=conn_idc[':LAST-LINK'][0]
                link_connected=conn_idc[':LAST-LINK'][2]
            else:
                model_name=conn_idc[':LAST-LINK'][0]
                link=conn_idc[':LAST-LINK'][2]
                model_name_connected=conn_idc[':FIRST-LINK'][0]
                link_connected=conn_idc[':FIRST-LINK'][2]
            #print(model_name)
            if not [True for model in data_ex if model[':N']==model_name]:
                comp=getCompPerName(components_idm,model_name)
                link_data = getModelInterfaces(getCompTemplate(comp))
                if link_data:
                    data_ex+=[{':N':model_name,':T': getCompTemplate(comp),
                        ':IMPORT': (link_data['import'] if network_side else link_data['export']),
                        ':EXPORT':(link_data['export'] if network_side else link_data['import']),
                        ':CONN-IDC':conn_idc}]
                elif model_name==':SELF' and link in ['"Int_Ref_Sensor_Source_{}"'.format(i['sensor_id']) for i in sensor_data for j in i['irefs_source'] if j[1].split('_')[1]==str(feature_id) and (model_name_connected not in dec_models and str(submodel)==j[0] and network_side==False or model_name_connected in dec_models and str(submodel)!=j[0] and network_side)]:
                    data_ex+=[{':N':model_name,':T': 'OUT',
                        ':IMPORT': [],
                        ':EXPORT': [link],
                        ':CONN-IDC':conn_idc}]
                elif model_name==':SELF' and link in ['"Int_Ref_Sensor_Target_{}"'.format(i['sensor_id']) for i in sensor_data for j in i['irefs_source'] if j[1].split('_')[1]==str(feature_id) and (model_name_connected not in dec_models and str(submodel)==j[0] and network_side==False or model_name_connected in dec_models and str(submodel)!=j[0] and network_side)]:
                    data_ex+=[{':N':model_name,':T': 'IN',
                        ':IMPORT': [link],
                        ':EXPORT': [],
                        ':CONN-IDC':conn_idc}]
    return data_ex

submodel=2
submodels=getUsedSubmodels(cur,dictDB)
submodels.remove(str(submodel))
features=getFeatureIds(dictDB,cur,submodel,submodels)
#print(features)
import_counter=0

seq=['EQUATION-FRAME', ':AT', [['818', '345']], ':FILL-COLOR', '#S', ['RGB', 'RED', '245', 'GREEN', '245', 'BLUE', '245'], ':FILL-TEXTURE', ':SOLID', ':R', ['14', '14'], ':ICON', '"lib:emeter.ids"', ':SLOT', ['"EmeterHotTank1"'], ':NAME', '"EmeterHotTank1"', ':DATA', ':CEO']
print(propertyListIDC(seq))

def getSensorIrefsSource(sensor_data):
    return [j for i in sensor_data for j in i['irefs_source'] if j[0]==1]
    
for feature in [features[0]]: 
           
    data_idm=OneOrMore(nestedExpr()).parseString(readFileToString("{}\\{}_{}\\{}_{}.idm".format(source_dir,feature['feature'].capitalize(),str(feature['id']),feature['feature'].capitalize(),str(feature['id']))))
    data_idc=OneOrMore(nestedExpr()).parseString(readFileToString("{}\\{}_{}\\{}_{}.idc".format(source_dir,feature['feature'].capitalize(),str(feature['id']),feature['feature'].capitalize(),str(feature['id']))))

    components_idm=[propertyListIDM(comp.asList()) for comp in data_idm]
    components_idc=[propertyListIDC(comp.asList()) for comp in data_idc]

    conns_idc=[comp for comp in components_idc if comp[':C']=='CONNECTION-LINE']

    dec_models=getDecoupledFeatureCompPerFeature(feature,cur,dictDB)
    dec_models.append(':SELF')
    print(dec_models)
    sensorIrefsSource=getSensorIrefsSource(getSensorData(cur,dictDB))
    print(sensorIrefsSource)
    dec_models.extend(sensorIrefsSource)
    data_ex=getDataEx(conns_idc,dec_models,components_idm,feature['network_side'],getSensorData(cur,dictDB),submodel,feature['id'])
    print(data_ex)
    dsf
    dec_models=['"'+i+'"' if i != ':SELF' else i for i in dec_models ]
    print(dec_models)
    
    keep_class=['DOCUMENT-HEADER','CONNECTIONS','\ufeff;IDA']
    #idm
    data_idm=[]
    iref_names=[getCompName(i) for i in components_idm if getCompClass(i)==':IREF']
    #print(iref_names)
    for comp in components_idm:
        #print('+++')
        #print(comp)
        #print(getCompName(comp))
        #print(getCompClass(comp))
        #print([i[':T'] for i in data_ex])
        #print(getCompTemplate(comp))
        comp_name=getCompName(comp)
        print(comp_name)
        if comp_name in dec_models and getCompTemplate(comp) not in [i[':T'] for i in data_ex] if feature['network_side'] else comp_name and comp_name not in dec_models:
            print('++++**++++')
            print('keep: '+comp_name)
            data_idm.append(comp)
        else:
            if getCompTemplate(comp)=='|hx|':
                if feature['network_side']:
                    print('network side; |hx| comp')
                    data_idm.append([{':C':'Model', ':N': comp_name, ':T': '|hx_ASide|'},
                                     {':C':':VAR', ':N': '|mLiqB|', ':B': [':SYSTEM','"Co-simulation-macro"','"{}<--{}"'.format(feature['cosim'],feature['submodel']),'|data_var|',
                                    str(import_counter+getCompImportPos(comp_name,'|mLiqB|',data_ex))]},
                                     {':C':':VAR', ':N': '|PhiHxLimit_var|', ':B': [':SYSTEM','"Co-simulation-macro"','"{}<--{}"'.format(feature['cosim'],feature['submodel']),'|data_var|',
                                    str(import_counter+getCompImportPos(comp_name,'|PhiHxLimit_var|',data_ex))]},
                                    {':C':':VAR', ':N': '|TbSet_var|', ':B': [':SYSTEM','"Co-simulation-macro"','"{}<--{}"'.format(feature['cosim'],feature['submodel']),'|data_var|',
                                    str(import_counter+getCompImportPos(comp_name,'|TbSet_var|',data_ex))]},
                                    {':C':':VAR', ':N': '|TsupB|', ':B': [':SYSTEM','"Co-simulation-macro"','"{}<--{}"'.format(feature['cosim'],feature['submodel']),'|data_var|',
                                    str(import_counter+getCompImportPos(comp_name,'|TsupB|',data_ex))]}])                            
                else:
                    print('substation side; |hx| comp')
                    data_idm.append([{':C':'Model', ':N': comp_name, ':T': '|hx_BSide|'},
                                     {':C':':VAR', ':N': '|TbOut|', ':B': [':SYSTEM','"Co-simulation-macro"','"{}<--{}"'.format(feature['submodel'],
                                    feature['cosim']),'|data_var|',
                                    str(import_counter+getCompImportPos(comp_name,'|TbOut|',data_ex))]}])
        if getCompClass(comp) in keep_class:
            if getCompClass(comp)=='CONNECTIONS':
                print('++++---++++')
                #print('keep: '+getCompClass(comp))
                [dec_models.remove(i[':N']) for j in dec_models for i in data_ex if i[':N']==j and not feature['network_side']]
                conns=[]
                for conn in comp[':CONNS']:
                    #print('++++++++')
                    #print(conn)
                    #print(feature['network_side'])
                    #print([conn[0][0],conn[1][0]])
                    if len([True for keep in dec_models if keep in [conn[0][0] if type(conn[0])==list else conn[0],conn[1][0] if type(conn[1])==list else conn[1]]])== (2 if feature['network_side'] else 0):
                        print('keep conn')
                        conns.append(conn)
                    #elif len([True for keep in dec_models if keep in [conn[0][0],conn[1][0]]])==1 and (conn[0] in iref_names or conn[1] in iref_names):
                    #    #print('keep iref conn')
                    #    conns.append(conn)
                    #    data_idm.insert(1,getCompPerName(components_idm,conn[0] if conn[0] in iref_names else conn[1]))
                comp[':CONNS']=conns
                data_idm.append(comp)
                #print(comp)
                
            else:
                #print('keep: '+getCompClass(comp))
                data_idm.append(comp)
        import_counter+=len([j for i in data_ex if getCompName(comp)==i[':N'] for j in i[':IMPORT']])
    print('++'+str(import_counter))          
    #print(data_idm)
    
    data_idc=[]
    for comp in components_idc:
        #print(comp)
        comp_class=getCompClass(comp)
        if comp_class=='CONNECTION-LINE' and len([True for keep in dec_models if comp[':LAST-LINK'][0]==keep or comp[':FIRST-LINK'][0]==keep])==(2 if feature['network_side'] else 0):
            #print('keep conn line')
            #print(comp)
            data_idc.append(comp)
        elif comp_class=='EQUATION-FRAME' and ((comp[':NAME'] in dec_models if feature['network_side'] else comp[':NAME'] not in dec_models) ):#or [True for i in data_ex if i[':N']==comp[':NAME']]):
            #print('keep EQUATION-FRAME')
            #print(comp[':NAME'])
            data_idc.append(comp)
        elif comp_class in keep_class:
            #print('keep')
            data_idc.append(comp)
            
    #print(data_idc)
            