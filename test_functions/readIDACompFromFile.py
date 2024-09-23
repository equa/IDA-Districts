from pyparsing import OneOrMore, nestedExpr
from plugins.utility_functions.files import *
from plugins.utility_functions.ida_components import *
from plugins.utility_functions.db import *
import psycopg2.extras
import psycopg2
from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT
plugin_dir="""C:\\Users\\Peter\\AppData\\Roaming\\QGIS\\QGIS3\\profiles\\default\\python\\plugins\\"""
dictDB={'pwd' : 'p3t3r' , 'host' : 'localhost','port':'5433', 'user' : 'postgres', 'projectName' : 'cosim_test1', 'versionName' : 'b'}
#dictDB=getDBConnectionData(plugin_dir)
conn=dbConnect(dictDB,True)
cur=conn.cursor(cursor_factory = psycopg2.extras.RealDictCursor)
import math
import os


datacenter_dir=getDataCenterDir(plugin_dir)
usedFeatureAssettypes=getUsedFeatureAssettypes(cur,dictDB)

submodel=1
submodels=getSubmodels(cur,dictDB)
submodels.remove(str(submodel))
print(submodels)

usedDecoupledFeatureAssettypes=getUsedDecoupledFeatureAssettypes(usedFeatureAssettypes,cur,dictDB,submodel,submodels)
print(usedDecoupledFeatureAssettypes)

#print(usedFeatureAssettypes)    

                

    

    
file_data=""

    
#print(readIDMFileToPropertyList('C:\\Users\\Peter\\AppData\\Roaming\\QGIS\\QGIS3\\profiles\\default\\python\\plugins\\ida_districts_data_center\\cosim_test1\\customer_assettypes\\1_1_Heating 1 Supply & 1 Return\\1_1_Heating 1 Supply & 1 Return.idm'))

        
    
dec_models=['tbout_setpoint','q_limit','HX_substation','PMT2mux_1_1_1_2_T30','PMT2mux_1_1_1_1_T70',':SELF']


assettype_dec_conns=[]
for assettype in usedDecoupledFeatureAssettypes:
    assettype_dir=datacenter_dir+'\\{}\\{}_assettypes\\{}_{}_{}\\'.format(dictDB['projectName'],assettype['feature'],assettype['assetgroup'],assettype['assettype'],assettype['assettype_name'])
    assettype_idm=assettype_dir+'{}_{}_{}.idm'.format(assettype['assetgroup'],assettype['assettype'],assettype['assettype_name'])
    assettype_idc=assettype_dir+'{}_{}_{}.idc'.format(assettype['assetgroup'],assettype['assettype'],assettype['assettype_name'])
    #print(assettype_idm)

    data_idm=OneOrMore(nestedExpr()).parseString(readFileToString(assettype_idm))
    data_idc=OneOrMore(nestedExpr()).parseString(readFileToString(assettype_idc))
    #print(data_idc)
    #print(data[5])
    #print(data[5].asList())
    #print(propertyListIDM(data[12]))
    #print(data)
    components_idm=[propertyListIDM(comp.asList()) for comp in data_idm]
    components_idc=[propertyListIDC(comp.asList()) for comp in data_idc]
    
    #print(getCompPerName(components_idm,'"HX_substation"'))
    #print(getCompTemplate(getCompPerName(components_idm,'"HX_substation"')))
    #print(getModelInterfaces(getCompTemplate(getCompPerName(components_idm,'"HX_substation"'))))    
    #print(components_idm)
    #print(components_idc)
    
    #getConnections
       
    conns_idm=[comp[':CONNS'] for comp in components_idm if getCompClass(comp)=='CONNECTIONS'][0]
    #print(conns_idm)
    
    conns_idc=[comp for comp in components_idc if comp[':C']=='CONNECTION-LINE']
    #print(conns_idc)
    
    dec_conns=decConnData(conns_idc,dec_models,components_idm)
    
    #print(dec_conns)
    assettype_dec_conns.append({'feature':assettype['feature'],'assetgroup':assettype['assetgroup'],'assettype':assettype['assettype'],'dec_conns':dec_conns})
    #print(file_data)
    #writePropertyListIDMToFile(components,'C:\\Users\\Peter\\Documents\\','C:\\Users\\Peter\\Documents\\test_ida_comp.idm')
    #writePropertyListIDCToFile(components,'C:\\Users\\Peter\\Documents\\','C:\\Users\\Peter\\Documents\\test_ida_comp.idc')

print(assettype_dec_conns)

        
f_ids=getFeatureIds(dictDB,cur,submodel,submodels)
print(f_ids)


    
importVars=getImportVars(f_ids,assettype_dec_conns)
print(importVars)

exportVars=getExportVars(f_ids,assettype_dec_conns)
print(exportVars)

for cosim in submodels:
    submodel_ids=[int(submodel),int(cosim)]
    submodel_ids.sort(reverse=True if int(submodel)>int(cosim) else False)

    print("""((MODEL :N "{}<--{}" :T |Import|)
 (:PAR :N |data_1dim| :V {})
 (:PAR :N |channel| :V "{}")
 (:PAR :N |extrapolationLimit| :V 7200)
 (:PAR :N |order| :DIM ({}) :V #({}))
 (:PAR :N |vars| :DIM ({}))
 (:PAR :N |deadBand| :V 0)
 (:VAR :N |data_var| :DIM ({}) :L "{}<--{}_data"))\n""".format(
        submodel,cosim,len(importVars),'-'.join([str(i) for i in submodel_ids]),len(importVars), " ".join(['0' for i in range(len(importVars))]),
        len(importVars),len(importVars),submodel,cosim))

    submodel_ids.sort(reverse=True if int(submodel)<int(cosim) else False)    
    print("""((MODEL :N "{}-->{}" :T |Export|)
 (:PAR :N |data_1dim| :V {})
 (:PAR :N |channel| :V "{}")
 (:VAR :N |data_var| :DIM ({}) :B #S(MS-SPARSE DEFAULT-VALUE NIL DIMENSION 1 VALUE ({})){})
 (:PAR :N |extrapolationLimit| :V 7200)
 (:PAR :N |order| :DIM ({}) :V #({}))
 (:PAR :N |vars| :DIM ({}))
 (:PAR :N |deadBand| :V 0))\n""".format(submodel,cosim,len(exportVars),'-'.join([str(i) for i in submodel_ids]),len(exportVars), 
           ' '.join([var for var in exportVars]),
                    """ :L "{}-->{}_data\"""".format(submodel,cosim),
                    len(exportVars)," ".join(['0' for i in range(len(exportVars))]),len(exportVars)))
