from plugins.utility_functions.files import *
from plugins.utility_functions.sensor_signals import *
from plugins.utility_functions.topology import *
import psycopg2.extras
import psycopg2
from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT
plugin_dir="""C:\\Users\\Peter\\AppData\\Roaming\\QGIS\\QGIS3\\profiles\\default\\python\\plugins\\"""
dictDB={'pwd' : 'p3t3r' , 'host' : 'localhost','port':'5433', 'user' : 'postgres', 'projectName' : 'cosim_test1', 'versionName' : 'b'}
#dictDB=getDBConnectionData(plugin_dir)
conn=dbConnect(dictDB,True)
cur=conn.cursor(cursor_factory = psycopg2.extras.RealDictCursor)
#print(cur)
         
sensor_data=getSensorData(cur,dictDB)
#print(sensor_data)
    
submodel='2'
import_counter={'2':2,'3':2}
exportVarsCounter=2
source_dir=plugin_dir+"ida_mosim\\models\\cosim_test1\\b\\invoked_customers"

feature_dec_irefs=[{'feature': 'customer', 'id': 9, 'submodel': 2, 'cosim': '1', 'network_side': False, 'irefs_source': ['"Int_Ref_Sensor_Source_6"', '"Int_Ref_Sensor_Source_5"', '"Int_Ref_Sensor_Source_1"'], 'irefs_target': ['"Int_Ref_Sensor_Target_4"', '"Int_Ref_Sensor_Target_3"', '"Int_Ref_Sensor_Target_2"']}, 
    {'feature': 'customer', 'id': 15, 'submodel': 2, 'cosim': '1', 'network_side': False, 'irefs_source': ['"Int_Ref_Sensor_Source_1"'], 'irefs_target': ['"Int_Ref_Sensor_Target_4"', '"Int_Ref_Sensor_Target_3"', '"Int_Ref_Sensor_Target_2"']}, 
    {'feature': 'customer', 'id': 16, 'submodel': 3, 'cosim': '1', 'network_side': False, 'irefs_source': ['"Int_Ref_Sensor_Source_6"', '"Int_Ref_Sensor_Source_1"'], 'irefs_target': ['"Int_Ref_Sensor_Target_4"', '"Int_Ref_Sensor_Target_3"', '"Int_Ref_Sensor_Target_2"']}, 
    {'feature': 'customer', 'id': 17, 'submodel': 3, 'cosim': '1', 'network_side': False, 'irefs_source': ['"Int_Ref_Sensor_Source_5"', '"Int_Ref_Sensor_Source_1"'], 'irefs_target': ['"Int_Ref_Sensor_Target_4"', '"Int_Ref_Sensor_Target_3"', '"Int_Ref_Sensor_Target_2"']}]

sensor_dec_data=getSensorDecData(sensor_data,feature_dec_irefs,cur,dictDB)

cosim='2'
cosims=['1','3']
supervisory_submodel=str(getSupervisorySubmodel(cur,dictDB)['submodel'])

features=getFeatureIds(dictDB,cur,submodel,cosims)
keep_class=['DOCUMENT-HEADER','CONNECTIONS','\ufeff;IDA','SELF-FRAME']

for feature in [features[0]]:
    #print(feature)
    irefs=getSensorIrefsFeatureSource(sensor_data,feature['submodel'],feature['id'],cur,dictDB,feature['feature'])
    irefs_target=getSensorIrefsFeatureTarget(sensor_data,feature['submodel'],feature['id'],cur,dictDB,feature['feature'])
    #print(irefs_target)
    
    #print(irefs)
    components_idc=propertyListCompsIDC(getIDAListComponents(readFileToString("{}\\{}_{}\\{}_{}.idc".format(source_dir,feature['feature'].lower(),str(feature['id']),feature['feature'].capitalize(),str(feature['id'])))))
    components_idm=propertyListCompsIDM(getIDAListComponents(readFileToString("{}\\{}_{}\\{}_{}.idm".format(source_dir,feature['feature'].lower(),str(feature['id']),feature['feature'].capitalize(),str(feature['id'])))))
    dec_models=getDecoupledFeatureCompPerFeature(feature,cur,dictDB)
    #print(dec_models)
    dec_models.append(':SELF')
    conns_idc=[comp for comp in components_idc if comp[':C']=='CONNECTION-LINE']

    data_ex=getDataExFeature(conns_idc,dec_models,components_idm,feature['network_side'],getSensorData(cur,dictDB),submodel,feature['id'],cur,dictDB)
    #print(data_ex)
    
    dec_models.extend(['Int_Ref_Sensor_Source_'+i.split('_')[0] for i in irefs])
    
    dec_models.extend(['Int_Ref_Sensor_Target_'+i.split('_')[0] for i in irefs_target])
    dec_models=['"'+i+'"' if i != ':SELF' else i for i in dec_models]
    #print(dec_models)
    

    #print(getCompImportPos('"HX_substation"','|TsupB|',data_ex))
    keep_irefs=[]
    hx=[j[':N'] for j in data_ex if j[':T']=='|hx|']
    dec_models_=[i for i in dec_models if i not in hx]
    #print(dec_models_)
    
    
    for comp in components_idc:
        comp_class=getCompClass(comp)
        if comp_class=='CONNECTION-LINE':
            if (        
                        (comp[':LAST-LINK'][2] in dec_models             
                    if comp[':LAST-LINK'][0]==':SELF' else
                        (comp[':LAST-LINK'][0] in dec_models 
                        if feature['network_side'] else 
                        comp[':LAST-LINK'][0] not in dec_models_))
                and 
                        (comp[':FIRST-LINK'][2] in dec_models             
                    if comp[':FIRST-LINK'][0]==':SELF' else
                        (comp[':FIRST-LINK'][0] in dec_models 
                        if feature['network_side'] else 
                        comp[':FIRST-LINK'][0] not in dec_models_))
                and 
                    (True if feature['network_side'] else 
                        not (comp[':FIRST-LINK'][0] ==':SELF' and comp[':LAST-LINK'][0] in hx or
                        comp[':LAST-LINK'][0] ==':SELF' and comp[':FIRST-LINK'][0] in hx ))):
                #print(comp)
                if comp[':FIRST-LINK'][0]==':SELF':
                    keep_irefs.append(comp[':FIRST-LINK'][2])   
                if comp[':LAST-LINK'][0]==':SELF':
                    keep_irefs.append(comp[':LAST-LINK'][2])
                
    #print(keep_irefs)
    
    
    

    dec_models=getDecoupledFeatureCompPerFeature(feature,cur,dictDB)
    dec_models.append(':SELF')
    dec_models=['"'+i+'"' if i != ':SELF' else i for i in dec_models]
    dec_models_=[i for i in dec_models if i not in hx]
    #print(dec_models_)
    
    #dec_models.extend(keep_irefs)
    for comp in components_idm:
        comp_name=getCompName(comp)
        if (comp_name in dec_models if feature['network_side'] else comp_name not in dec_models) or comp_name in keep_irefs:
            #print(comp)
            if getCompTemplate(comp)=='|hx|':
                pass
        if getCompClass(comp) in keep_class:
            if getCompClass(comp)=='CONNECTIONS':
                #print('++++---++++')
                #print('keep: '+getCompClass(comp))
                dec_models.extend(keep_irefs)
                dec_models_.extend(keep_irefs)

                conns=[]
                for conn in comp[':CONNS']:

                    if conn[0][0] in hx or conn[1][0] in hx:
                        #print(type(conn[0])==list)
                        #print(type(conn[1])==list)
                        #print(conn[0][0] in hx if type(conn[0])==list else True)
                        #print(conn[1][0] in hx if type(conn[1])==list else True)
                        #print(not((conn[0][0] in hx if type(conn[0])==list else True) and (conn[1][0] in hx if type(conn[1])==list else True) or
                                    (conn[1][0] in hx if type(conn[1])==list else True) and (conn[0][0] in hx if type(conn[0])==list else True)))
                        #print(not(conn[0][0] in hx if type(conn[0])==list else True) and not(conn[1][0] in hx if type(conn[1])==list else True))
                        #print(conn)
                                     
                    
                    if (((
                                        conn[0][0] in dec_models
                                    if feature['network_side'] else
                                        conn[0][0] not in dec_models_)    
                                if type(conn[0])==list else 
                                    conn[0] in dec_models)
                                and
                                ((
                                        conn[1][0] in dec_models
                                    if feature['network_side'] else
                                        conn[1][0] not in dec_models_)    
                                if type(conn[1])==list else 
                                    conn[1] in dec_models)
                                and 
                                    not((conn[0][0] in hx if type(conn[0])==list else True) and (conn[1][0] in hx if type(conn[1])==list else True) or
                                    (conn[1][0] in hx if type(conn[1])==list else True) and (conn[0][0] in hx if type(conn[0])==list else True))):
                        if 'HX_' in str(conn):
                            #print(conn)

                        # #print(type(conn[0])==list)
                        # #print(conn[0][0] in dec_models)
                        # #print(type(conn[1])==list)
                        # #print(conn[1][0] in dec_models)
                        # #print((
                        #         conn[1][0] in dec_models
                        #     if feature['network_side'] else
                        #         conn[1][0] not in dec_models    
                        # if type(conn[1])==list else 
                        #     conn[1] in dec_models))
                    
            
            
        
    
    
    
    
