from plugins.utility_functions.files import *
from plugins.utility_functions.sensor_signals import *
from plugins.utility_functions.topology import *
from plugins.utility_functions.db import *
from plugins.utility_functions.ida_components import *
from plugins.utility_functions.templateFiles import *
from plugins.ida_mosim.cosim import *


import psycopg2.extras
import psycopg2
import copy
from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT
plugin_dir="""C:\\Users\\Peter\\AppData\\Roaming\\QGIS\\QGIS3\\profiles\\default\\python\\plugins\\"""
dictDB={'pwd' : 'p3t3r' , 'host' : 'localhost','port':'5433', 'user' : 'postgres', 'projectName' : 'test00001', 'versionName' : 'base1'}
#dictDB=getDBConnectionData(plugin_dir)
conn=dbConnect(dictDB,True)
cur=conn.cursor(cursor_factory = psycopg2.extras.RealDictCursor)
#print(cur)
         
sensor_data=getSensorData(cur,dictDB)
#print(sensor_data)
    
submodel='1'
#import_counter={'2':2,'3':2}
#exportVarsCounter=2
dir=plugin_dir+"ida_mosim\\models\\{}\\{}".format(dictDB['projectName'],dictDB['versionName'])


class CopyDecoupledTemplateMacro:
    """ Copy invoked assettype macros to IDA network project (customers and plants):
        * remove everything without interfaces
        * import/export:
            -sensor signals
            -connections"""
    def __init__(self,submodel,dir,dictDB,cur,plugin_dir,sensor_data,mode='network'):
        #print('copy decoupled feature macro')
        target_dir=dir+"\\{}_".format(mode)+str(submodel)+("\\plant" if mode=='building' else "")
        #print(target_dir)  
        submodels=getUsedSubmodels(cur,dictDB)
        submodels.remove(str(submodel))
        #print(submodels)
        
        features=getFeatureDecIds(dictDB,cur,submodel,submodels)
        self.import_counter={}
        self.resources=[]
        self.data_ex_f=[]
        for feature in features: 
            #print(feature)
            try:
                self.import_counter[str(feature['submodel'])]=self.import_counter[str(feature['submodel'])]
            except:
                self.import_counter[str(feature['submodel'])]=0
            f_idc_target=target_dir+'\\'+(feature['feature'].capitalize()+"_" if mode=='network' else 'substation b')+str(feature['id'])+".idc"
            f_idm_target=target_dir+'\\'+(feature['feature'].capitalize()+"_" if mode=='network' else 'substation b')+str(feature['id'])+".idm"
            #print(f_idm_target)
            source_dir=dir+'\\invoked_'+feature['feature']+'s'

            if not os.path.exists("{}\\{}_{}.idm".format(source_dir,feature['feature'].lower(),str(feature['id']))):
                invokeOneFeature(False,str(feature['id']),plugin_dir,cur,dictDB,feature['feature'],False)
            
            file_data=readFileToList("{}\\{}_{}.idm".format(source_dir,feature['feature'].lower(),str(feature['id'])))
            resource=getResourcesFromFileDataList(file_data)

            if resource not in self.resources:
                self.resources+=resource

            #idm
            source_f="{}\\{}_{}\\{}_{}.idm".format(source_dir,feature['feature'].lower(),str(feature['id']),feature['feature'].capitalize(),str(feature['id']))     
            #print('++++++++++++++++start read file components ++++++++++++++++++++++++ ')
            components_idm=propertyListCompsIDM(getIDAListComponents(readFileToString(source_f)))
            components_idc=propertyListCompsIDC(getIDAListComponents(readFileToString("{}\\{}_{}\\{}_{}.idc".format(source_dir,feature['feature'].lower(),str(feature['id']),feature['feature'].capitalize(),str(feature['id'])))))
            #print('++++++++++++++++end read file components  ++++++++++++++++++++++++ ')

            conns_idc=[comp for comp in components_idc if comp[':C']=='CONNECTION-LINE']

            keep_class=['DOCUMENT-HEADER','CONNECTIONS','\ufeff;IDA','SELF-FRAME','LIST-FIELD']
                
            #idc
            #print(source_f)
            data_idc=[]
                  
            dec_models=getDecoupledFeatureCompPerFeature(feature,cur,dictDB)
            #print(dec_models)
            pmtmux_names=[getPMT2muxName(cur,i['conn_bundle_type_id'],i['conn_id']) for i in getConnsValuesByFeature(feature['feature'],str(feature['id']),cur,dictDB) if i['type'] in [1,2]]
            #print(pmtmux_names)
            building_pmt2s=['"'+getPMT2muxName(cur,i['conn_bundle_type_id'],i['conn_id'])+'"' for i in getConnsValuesByFeature(feature['feature'],str(feature['id']),cur,dictDB) if i['type'] not in [1,2]]
            building_irefs=['"'+i.split('PMT2mux_')[1] for i in building_pmt2s]
            dec_models.extend(pmtmux_names)
            dec_models.extend([i.split('PMT2mux_')[1] for i in pmtmux_names])
            for emeter in [getMeterName(cur,i['conn_bundle_type_id'],i['conn_type_id']) for i in getConnsValuesByFeature(feature['feature'],str(feature['id']),cur,dictDB) if i['type'] in [1,2]]:
                if emeter not in dec_models:
                    dec_models.append(emeter)
            dec_models.append(':SELF')
            #print(dec_models)
            
            #idc
            data_ex=getDataExFeature(conns_idc,dec_models,components_idm,feature['network_side'],sensor_data,submodel,feature['id'],cur,dictDB)
            #print(data_ex)
            irefs=getSensorIrefsFeatureSource(sensor_data,feature['submodel'],feature['id'],cur,dictDB,feature['feature'])
            irefs_target=getSensorIrefsFeatureTarget(sensor_data,feature['submodel'],feature['id'],cur,dictDB,feature['feature'])
            
            dec_models_idc=copy.copy(dec_models)
            #print(irefs)
            dec_models_idc.extend(['Int_Ref_Sensor_Source_'+i.split('_')[0] for i in irefs])
            #print(dec_models_idc)
            dec_models_idc.extend(['Int_Ref_Sensor_Target_'+i.split('_')[0] for i in irefs_target])
            dec_models_idc=['"'+i+'"' if i != ':SELF' else i for i in dec_models_idc]
            #print(dec_models_idc)
            
            keep_irefs=[]
            hx=[j[':N'] for j in data_ex if j[':T']=='|hx|']
            dec_models_idc_=[i for i in dec_models_idc if i not in hx]
            #print(dec_models_idc_)
            PhiHxLimit_signal=False
            TbSet_signal=False
            #print(feature['network_side'])
            #print(building_irefs)
            
            for comp in components_idc:
                #print(comp)
                comp_class=getCompClass(comp)
                if comp_class=='CONNECTION-LINE':
                    
                    #print((comp[':LAST-LINK'][2] in dec_models_idc or comp[':LAST-LINK'][2] in building_irefs             
                            if comp[':LAST-LINK'][0]==':SELF' else
                                (comp[':LAST-LINK'][0] in dec_models_idc 
                                if feature['network_side'] else 
                                comp[':LAST-LINK'][0] not in dec_models_idc_)))
                    #print((comp[':FIRST-LINK'][2] in dec_models_idc or comp[':FIRST-LINK'][2] in building_irefs              
                            if comp[':FIRST-LINK'][0]==':SELF' else
                                (comp[':FIRST-LINK'][0] in dec_models_idc 
                                if feature['network_side'] else 
                                comp[':FIRST-LINK'][0] not in dec_models_idc_)))
                    #print((True if feature['network_side'] else 
                                not (comp[':FIRST-LINK'][0] ==':SELF' and comp[':LAST-LINK'][0] in hx or
                                comp[':LAST-LINK'][0] ==':SELF' and comp[':FIRST-LINK'][0] in hx )))
                    
                                
                    if (comp[':FIRST-LINK'][0] ==':SELF' and comp[':LAST-LINK'][0] in hx or
                        comp[':LAST-LINK'][0] ==':SELF' and comp[':FIRST-LINK'][0] in hx):
                        if '|PhiHxLimit|' in str(comp):
                            PhiHxLimit_signal=True
                        if '|TbSet|' in str(comp):
                            TbSet_signal=True
                    if (        
                                (comp[':LAST-LINK'][2] in dec_models_idc or comp[':LAST-LINK'][2] in building_irefs             
                            if comp[':LAST-LINK'][0]==':SELF' else
                                (comp[':LAST-LINK'][0] in dec_models_idc 
                                if feature['network_side'] else 
                                comp[':LAST-LINK'][0] not in dec_models_idc_))
                        and 
                                (comp[':FIRST-LINK'][2] in dec_models_idc or comp[':FIRST-LINK'][2] in building_irefs              
                            if comp[':FIRST-LINK'][0]==':SELF' else
                                (comp[':FIRST-LINK'][0] in dec_models_idc 
                                if feature['network_side'] else 
                                comp[':FIRST-LINK'][0] not in dec_models_idc_))
                        and 
                            (True if feature['network_side'] else 
                                not (comp[':FIRST-LINK'][0] ==':SELF' and comp[':LAST-LINK'][0] in hx or
                                comp[':LAST-LINK'][0] ==':SELF' and comp[':FIRST-LINK'][0] in hx ))):
                        #print('keep conn line')
                        #print(comp)                       
                        data_idc.append(comp)
                        if comp[':FIRST-LINK'][0]==':SELF':
                            keep_irefs.append(comp[':FIRST-LINK'][2])   
                        if comp[':LAST-LINK'][0]==':SELF':
                            keep_irefs.append(comp[':LAST-LINK'][2])
                elif (comp_class=='EQUATION-FRAME' or comp_class=='LINK-FRAME') and ((comp[':NAME'] in dec_models_idc if feature['network_side'] else comp[':NAME'] not in dec_models_idc or comp[':NAME'] in hx) ):
                    #print('keep EQUATION-FRAME')
                    #print(comp[':NAME'])
                    data_idc.append(comp)
                elif comp_class in keep_class:
                    #print('keep')
                    data_idc.append(comp)
            #print(data_idc)
            writePropertyListIDCToFile(data_idc,target_dir,f_idc_target)  
            
            
            #idm
            dec_models=['"'+i+'"' if i != ':SELF' else i for i in dec_models]
            dec_models_=[i for i in dec_models if i not in hx]
            data_idm=[]
            for comp in components_idm:
                comp_name=getCompName(comp)
                if (comp_name in dec_models if feature['network_side'] else comp_name not in dec_models or comp_name in hx) and getCompClass(comp) not in keep_class or comp_name in keep_irefs:
                    #print('++++**++++')
                    #print('keep: '+comp_name)
                    if getCompName(comp) in building_pmt2s:
                        data=[]
                        for i in comp:
                            if getCompName(i)=='|M_var|':
                                #print('|M_var|')
                                i[':B']=['-1','|term_b|','1']
                                data.append(i)
                            elif getCompName(i)=='|term_b|':
                                instream_data=[]
                                for j in i:
                                    if getCompName(j)=='|inStream(T)|':
                                        #print('|inStream(T)|')
                                        j[':B']=['-1','|term_b|','2']
                                    instream_data.append(j)
                                data.append(instream_data)
                            else:
                                data.append(i)
                        data_idm.append(data)
                    if getCompTemplate(comp)=='|hx|':
                        data_idm.append({':C':'OUTPUT-FILE',':N': '"HX decoupling"',':T':'OUTPUT-FILE', ':COL':'T',':STM':'1'})
                        if feature['network_side']:
                            #print('network side; |hx| comp')
                            data_idm.append([{':C':'Model', ':N': comp_name, ':T': '|hx_ASide|'},
                                             {':C':':VAR', ':N': '|mLiqB|', ':B': [':SYSTEM','"Co-simulation-macro"','"{}<--{}"'.format(feature['cosim'],feature['submodel']),'|data_var|',
                                            str(self.import_counter[str(feature['submodel'])]+getCompImportPos(comp_name,'|mLiqB|',data_ex))],':L':'"HX decoupling"', ':AS':'"mLiqB"'},
                                            {':C':':VAR', ':N': '|PhiHxLimit_var|', ':B': [':SYSTEM','"Co-simulation-macro"','"{}<--{}"'.format(feature['cosim'],feature['submodel']),'|data_var|',
                                            str(self.import_counter[str(feature['submodel'])]+getCompImportPos(comp_name,'|PhiHxLimit_var|',data_ex))] if not PhiHxLimit_signal else ['-1','|PhiHxLimit|','0']},
                                            {':C':':VAR', ':N': '|TbSet_var|', ':B': [':SYSTEM','"Co-simulation-macro"','"{}<--{}"'.format(feature['cosim'],feature['submodel']),'|data_var|',
                                            str(self.import_counter[str(feature['submodel'])]+getCompImportPos(comp_name,'|TbSet_var|',data_ex))] if not TbSet_signal else ['-1','|TbSet|','0']},
                                            {':C':':VAR', ':N': '|TsupB|', ':B': [':SYSTEM','"Co-simulation-macro"','"{}<--{}"'.format(feature['cosim'],feature['submodel']),'|data_var|',
                                            str(self.import_counter[str(feature['submodel'])]+getCompImportPos(comp_name,'|TsupB|',data_ex))],':L':'"HX decoupling"', ':AS':'"TbIn"'},
                                            {':C':':VAR',':N': '|PhiHx|',':L':'"HX decoupling"', ':AS':'"PhiHX"'},
                                            {':C':':VAR',':N': '|TaOut|',':L':'"HX decoupling"', ':AS':'"TaOut"'},
                                            {':C':':VAR',':N': '|TbOut|',':L':'"HX decoupling"', ':AS':'"TbOut"'},
                                            {':C':':VAR',':N': '|TsupA|',':L':'"HX decoupling"', ':AS':'"TaIn"'},
                                            {':C':':VAR',':N': '|TbSet_var|',':L':'"HX decoupling"', ':AS':'"TbSet"'},
                                            {':C':':VAR',':N': '|mLiqA|',':L':'"HX decoupling"', ':AS':'"mLiqA"'}])
                        else:
                            #print('substation side; |hx| comp')
                            data_idm.append([{':C':'Model', ':N': comp_name, ':T': '|hx_BSide|'},
                                             {':C':':VAR', ':N': '|PhiHxLimit_var|', ':B': '-1' if PhiHxLimit_signal else ['-1','|PhiHxLimit|','0']},
                                             {':C':':VAR', ':N': '|TbSet_var|', ':B': '-1' if TbSet_signal else ['-1','|TbSet|','0'],':L':'"HX decoupling"', ':AS':'"TbSet"'},
                                             {':C':':VAR', ':N': '|TbOut|', ':B': [':SYSTEM' if mode=='network' else ':PLANT','"Co-simulation-macro"','"{}<--{}"'.format(feature['submodel'],
                                            feature['cosim']),'|data_var|',
                                            str(self.import_counter[str(feature['submodel'])]+getCompImportPos(comp_name,'|TbOut|',data_ex))],':L':'"HX decoupling"', ':AS':'"TbOut"'},
                                            {':C':':VAR',':N': '|PhiHx|',':L':'"HX decoupling"', ':AS':'"PhiHX"'},
                                            {':C':':VAR',':N': '|TaOut|',':L':'"HX decoupling"', ':AS':'"TaOut"'},
                                            {':C':':VAR',':N': '|TsupA|',':L':'"HX decoupling"', ':AS':'"TaIn"'},
                                            {':C':':VAR',':N': '|TsupB|',':L':'"HX decoupling"', ':AS':'"TbIn"'},
                                            {':C':':VAR',':N': '|mLiqB|',':L':'"HX decoupling"', ':AS':'"mLiqB"'}])
                    else:
                        data_idm.append(comp)
                if getCompClass(comp) in keep_class:
                    #print(getCompClass(comp))
                    if getCompClass(comp)=='CONNECTIONS':
                        #print('++++---++++')
                        #print('keep: '+getCompClass(comp))
                        dec_models.extend(keep_irefs)

                        conns=[]
                        for conn in comp[':CONNS']:
                            #print('++++++++')
                            #print(conn)
                            #print(feature['network_side'])
                            #print([conn[0][0],conn[1][0]])
                            if          (((conn[0][0] in dec_models
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
                                            (True if feature['network_side'] else 
                                            not((conn[0][0] in hx if type(conn[0])==list else True) and (conn[1][0] in hx if type(conn[1])==list else True) or
                                                (conn[1][0] in hx if type(conn[1])==list else True) and (conn[0][0] in hx if type(conn[0])==list else True)))):
                                #print('keep conn')
                                conns.append(conn)
                            #elif len([True for keep in dec_models if keep in [conn[0][0],conn[1][0]]])==1 and (conn[0] in iref_names or conn[1] in iref_names):
                            #    #print('keep iref conn')
                            #    conns.append(conn)
                            #    data_idm.insert(1,getCompPerName(components_idm,conn[0] if conn[0] in iref_names else conn[1]))
                        comp[':CONNS']=conns
                        #print(data_idm)

                        data_idm.append(comp)
                        #print(comp)
                        #print(data_idm)
                        
                    else:
                        #print('keep: '+getCompClass(comp))
                        data_idm.append(comp)
                
                self.import_counter[str(feature['submodel'])]+=len([j for i in data_ex if getCompName(comp)==i[':N'] for j in i[':IMPORT']])
                #self.import_counter[str(feature['submodel'])]+=len(keep_irefs)
            #print('++'+str(self.import_counter))          
            #print(data_idm)
            
             
            writePropertyListIDMToFile(data_idm,target_dir,f_idm_target)
            
            #check if folder contains macros
            #print('----------------------------------------check if macros exist----------------------')
            #print(source_dir+'\\'+feature['feature'].capitalize()+"_"+str(feature['id'])+'\\'+feature['feature'].capitalize()+"_"+str(feature['id']))
            if os.path.exists(source_dir+'\\'+feature['feature'].capitalize()+"_"+str(feature['id'])+'\\'+feature['feature'].capitalize()+"_"+str(feature['id'])):
                for root, dirs, files in os.walk(source_dir+'\\'+feature['feature'].capitalize()+"_"+str(feature['id'])+'\\'+feature['feature'].capitalize()+"_"+str(feature['id'])):
                    for file in files:
                        if file.endswith('.idm') or file.endswith('.idc'):
                            #print('---------macro exists: '+file)
                            subfolder=os.path.dirname(os.path.join(root, file)).replace('/','\\').split(feature['feature'].capitalize()+"_"+str(feature['id'])+'\\'+feature['feature'].capitalize()+"_"+str(feature['id']))[1]
                            path=target_dir+'\\'+(feature['feature'].capitalize()+"_" if mode=='network' else 'substation b')+str(feature['id'])+subfolder
                            createSubDir(path)
                            copyFile(os.path.join(root, file),path,path+'\\'+file)

dec_templates=CopyDecoupledTemplateMacro(submodel,dir,dictDB,cur,plugin_dir,sensor_data,mode='network')
#print('finished dec')
# #print(dec_templates.resources)
# if dec_templates.resources:
#     file_data=readFileToList("{}\\building_{}.idm".format(dir,submodel))
#     file_data[2:2]=dec_templates.resources


# #decoupling
# feature_dec_irefs=[]
# for submodel_ in getUsedSubmodels(cur, dictDB):
#     #decoupling: make macro with import/export connections for features which are connected to the submodel lines but not in the submodel  
#     #print('//////************------//////*------')
#     for i in readDecoupledFeatureSensorSignals(submodel_,dir,dictDB,cur,plugin_dir,sensor_data):
#         #print('++++++++--++')
#         #print(i)
#         if i not in feature_dec_irefs:
#             feature_dec_irefs.append(i)
# #print(feature_dec_irefs)

# sensor_dec_data=getSensorDecData(sensor_data,feature_dec_irefs,cur,dictDB)   
# #print(sensor_dec_data)
# sdf

# #print(dir)
# #print(type(submodel))
# data_dec_idm=writeCosimMacroIdm(dictDB,cur,submodel,dir,plugin_dir,sensor_data,sensor_dec_data,mode='building')
# #print(data_dec_idm)

# writeCosimMacroIdc(dictDB,cur,submodel,dir,plugin_dir,mode='building')
    
    
    