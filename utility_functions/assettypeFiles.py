from plugins.utility_functions.db import *
from plugins.utility_functions.files import *
from plugins.utility_functions.macros import *
import os.path
import psycopg2
import psycopg2.extras
from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT
import os

from plugins.ida_districts_modeling_simulation.invoke import *
from plugins.utility_functions.topology import *

def readDecoupledFeatureSensorSignals(submodel,dir,dictDB,cur,plugin_dir,sensor_data):
    target_dir=dir+"\\network_"+str(submodel)
                    
    submodels=getUsedSubmodels(cur,dictDB)
    submodels.remove(str(submodel))
    print(submodels)
    
    features=getFeatureIds(dictDB,cur,submodel,submodels)
    print(features)
        
    feature_dec_irefs=[]
    for feature in features: 
        print(feature)
        source_dir=dir+'\\invoked_'+feature['feature']+'s'

        #idm
        source_f="{}\\{}_{}\\{}_{}.idm".format(source_dir,feature['feature'].lower(),str(feature['id']),feature['feature'].capitalize(),str(feature['id']))     
        print(source_f)
        if not os.path.exists(source_f):
            invokeOneFeature(False,str(feature['id']),plugin_dir,cur,dictDB,feature['feature'],False)
        
        components_idm=propertyListCompsIDM(getIDAListComponents(readFileToString(source_f)))
        components_idc=propertyListCompsIDC(getIDAListComponents(readFileToString("{}\\{}_{}\\{}_{}.idc".format(source_dir,feature['feature'].lower(),str(feature['id']),feature['feature'].capitalize(),str(feature['id'])))))

        conns_idc=[comp for comp in components_idc if comp[':C']=='CONNECTION-LINE']

        
        
        dec_models=getDecoupledFeatureCompPerFeature(feature,cur,dictDB)
        print(feature['feature'])
        pmtmux_names=[getPMT2muxName(cur,i['conn_bundle_type_id'],i['conn_id']) for i in getConnsValuesByFeature(feature['feature'],str(feature['id']),cur,dictDB)]
        dec_models.extend(pmtmux_names)
        dec_models.extend([i.split('PMT2mux_')[1] for i in pmtmux_names])
        for emeter in [getMeterName(cur,i['conn_bundle_type_id'],i['conn_type_id']) for i in getConnsValuesByFeature(feature['feature'],str(feature['id']),cur,dictDB)]:
            if emeter not in dec_models:
                dec_models.append(emeter)
        dec_models.append(':SELF')
        irefs=getSensorIrefsSource(sensor_data,feature['submodel'],cur,dictDB,feature['feature'])
        irefs_target=getSensorIrefsFeatureTarget(sensor_data,feature['submodel'],feature['id'],cur,dictDB,feature['feature'])
        dec_models.extend(['Int_Ref_Sensor_Source_'+i.split('_')[0] for i in irefs])
        dec_models.extend(['Int_Ref_Sensor_Target_'+i.split('_')[0] for i in irefs_target])
        print(dec_models)
        
        
        data_ex=getDataExFeature(conns_idc,dec_models,components_idm,feature['network_side'],sensor_data,submodel,feature['id'],cur,dictDB)
        print(data_ex)
            
        dec_models=['"'+i+'"' if i != ':SELF' else i for i in dec_models]
        print(dec_models)
        hx=[j[':N'] for j in data_ex if j[':T']=='|hx|']
        dec_models_=[i for i in dec_models if i not in hx]
              
        print(dec_models)
        irefs=getSensorIrefsFeatureSource(sensor_data,feature['submodel'],feature['id'],cur,dictDB,feature['feature']) if feature['network_side'] else [j for i in data_ex for j in i[':EXPORT'] if i[':N']==':SELF']+[j for i in data_ex for j in i[':IMPORT'] if i[':N']==':SELF']
        print(irefs)
        
        irefs_source=[]
        irefs_target=[]
        for comp in components_idc:
            #print(comp)
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
                    if comp[':LAST-LINK'][0]==':SELF' or comp[':FIRST-LINK'][0]==':SELF':
                        #print('++++++++++dec++++++++++++++')
                        #print(comp)
                        if 'Target' in comp[':FIRST-LINK'][2]:
                            irefs_target.append(comp[':FIRST-LINK'][2])
                        elif 'Target' in comp[':LAST-LINK'][2]:
                            irefs_target.append(comp[':LAST-LINK'][2])
                        elif 'Source' in comp[':FIRST-LINK'][2]:
                            irefs_source.append(comp[':FIRST-LINK'][2])
                        elif 'Source' in comp[':LAST-LINK'][2]:
                            irefs_source.append(comp[':LAST-LINK'][2])                            
        if irefs_source or irefs_target:
            print('****--***')
            #print(irefs_source)
            #print(irefs_target)
            feature_dec_irefs+=[{'feature':feature['feature'],'id':feature['id'],'submodel':feature['submodel'],'cosim':feature['cosim'],'network_side':feature['network_side'],'irefs_source':irefs_source,'irefs_target': irefs_target}]
            print(feature_dec_irefs)
    return feature_dec_irefs
    
class CopyDecoupledAssettypeMacro:
    """ Copy invoked assettype macros to IDA network project (customers and plants):
        * remove everything without interfaces
        * import/export:
            -sensor signals
            -connections"""
    def __init__(self,submodel,dir,dictDB,cur,plugin_dir,sensor_data,mode='network'):
        print('copy decoupled feature macro')
        target_dir=dir+"\\{}_".format(mode)+str(submodel)+("\\plant" if mode=='building' else "")
        print(target_dir)  
        submodels=getUsedSubmodels(cur,dictDB)
        submodels.remove(str(submodel))
        print(submodels)
        
        features=getFeatureIds(dictDB,cur,submodel,submodels)
        self.import_counter={}
        self.resources=[]
        self.data_ex_f=[]
        for feature in features: 
            print(feature)
            try:
                self.import_counter[str(feature['submodel'])]=self.import_counter[str(feature['submodel'])]
            except:
                self.import_counter[str(feature['submodel'])]=0
            f_idc_target=target_dir+'\\'+(feature['feature'].capitalize()+"_" if mode=='network' else 'substation b')+str(feature['id'])+".idc"
            f_idm_target=target_dir+'\\'+(feature['feature'].capitalize()+"_" if mode=='network' else 'substation b')+str(feature['id'])+".idm"
            print(f_idm_target)
            source_dir=dir+'\\invoked_'+feature['feature']+'s'

            if not os.path.exists("{}\\{}_{}.idm".format(source_dir,feature['feature'].lower(),str(feature['id']))):
                invokeOneFeature(False,str(feature['id']),plugin_dir,cur,dictDB,feature['feature'],False)
            
            file_data=readFileToList("{}\\{}_{}.idm".format(source_dir,feature['feature'].lower(),str(feature['id'])))
            resource=getResourcesFromFileDataList(file_data)

            if resource not in self.resources:
                self.resources+=resource

            #idm
            source_f="{}\\{}_{}\\{}_{}.idm".format(source_dir,feature['feature'].lower(),str(feature['id']),feature['feature'].capitalize(),str(feature['id']))     
            print('++++++++++++++++start read file components ++++++++++++++++++++++++ ')
            components_idm=propertyListCompsIDM(getIDAListComponents(readFileToString(source_f)))
            components_idc=propertyListCompsIDC(getIDAListComponents(readFileToString("{}\\{}_{}\\{}_{}.idc".format(source_dir,feature['feature'].lower(),str(feature['id']),feature['feature'].capitalize(),str(feature['id'])))))
            print('++++++++++++++++end read file components  ++++++++++++++++++++++++ ')

            conns_idc=[comp for comp in components_idc if comp[':C']=='CONNECTION-LINE']

            keep_class=['DOCUMENT-HEADER','CONNECTIONS','\ufeff;IDA','SELF-FRAME','LIST-FIELD']
                
            #idc
            print(source_f)
            data_idc=[]
                  
            dec_models=getDecoupledFeatureCompPerFeature(feature,cur,dictDB)
            print(dec_models)
            pmtmux_names=[getPMT2muxName(cur,i['conn_bundle_type_id'],i['conn_id']) for i in getConnsValuesByFeature(feature['feature'],str(feature['id']),cur,dictDB) if i['type'] in [1,2]]
            print(pmtmux_names)
            building_pmt2s=['"'+getPMT2muxName(cur,i['conn_bundle_type_id'],i['conn_id'])+'"' for i in getConnsValuesByFeature(feature['feature'],str(feature['id']),cur,dictDB) if i['type'] not in [1,2]]
            building_irefs=['"'+i.split('PMT2mux_')[1] for i in building_pmt2s]
            dec_models.extend(pmtmux_names)
            dec_models.extend([i.split('PMT2mux_')[1] for i in pmtmux_names])
            for emeter in [getMeterName(cur,i['conn_bundle_type_id'],i['conn_type_id']) for i in getConnsValuesByFeature(feature['feature'],str(feature['id']),cur,dictDB) if i['type'] in [1,2]]:
                if emeter not in dec_models:
                    dec_models.append(emeter)
            dec_models.append(':SELF')
            print(dec_models)
            
            #idc
            data_ex=getDataExFeature(conns_idc,dec_models,components_idm,feature['network_side'],sensor_data,submodel,feature['id'],cur,dictDB)
            print(data_ex)
            irefs=getSensorIrefsFeatureSource(sensor_data,feature['submodel'],feature['id'],cur,dictDB,feature['feature'])
            irefs_target=getSensorIrefsFeatureTarget(sensor_data,feature['submodel'],feature['id'],cur,dictDB,feature['feature'])
            
            dec_models_idc=copy.copy(dec_models)
            dec_models_idc.extend(['Int_Ref_Sensor_Source_'+i.split('_')[0] for i in irefs])
            print(dec_models_idc)
            dec_models_idc.extend(['Int_Ref_Sensor_Target_'+i.split('_')[0] for i in irefs_target])
            dec_models_idc=['"'+i+'"' if i != ':SELF' else i for i in dec_models]
            print(dec_models_idc)
            keep_irefs=[]
            hx=[j[':N'] for j in data_ex if j[':T']=='|hx|']
            dec_models_idc_=[i for i in dec_models_idc if i not in hx]
            PhiHxLimit_signal=False
            TbSet_signal=False
            print(feature['network_side'])
            print(building_irefs)
            
            for comp in components_idc:
                comp_class=getCompClass(comp)
                if comp_class=='CONNECTION-LINE':
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
                                print('|M_var|')
                                i[':B']=['-1','|term_b|','1']
                                data.append(i)
                            elif getCompName(i)=='|term_b|':
                                instream_data=[]
                                for j in i:
                                    if getCompName(j)=='|inStream(T)|':
                                        print('|inStream(T)|')
                                        j[':B']=['-1','|term_b|','2']
                                    instream_data.append(j)
                                data.append(instream_data)
                            else:
                                data.append(i)
                        data_idm.append(data)
                    if getCompTemplate(comp)=='|hx|':
                        data_idm.append({':C':'OUTPUT-FILE',':N': '"HX decoupling"',':T':'OUTPUT-FILE', ':COL':'T',':STM':'1'})
                        if feature['network_side']:
                            print('network side; |hx| comp')
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
                            print('substation side; |hx| comp')
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
                            print('---------macro exists: '+file)
                            subfolder=os.path.dirname(os.path.join(root, file)).replace('/','\\').split(feature['feature'].capitalize()+"_"+str(feature['id'])+'\\'+feature['feature'].capitalize()+"_"+str(feature['id']))[1]
                            path=target_dir+'\\'+(feature['feature'].capitalize()+"_" if mode=='network' else 'substation b')+str(feature['id'])+subfolder
                            createSubDir(path)
                            copyFile(os.path.join(root, file),path,path+'\\'+file)
        
class ExchangeConntypeFiles:
    """ Exchanges connection types: 1) Removes the old connection type; 2) add the new connection type !!!!To do!!!!"""
    def __init__(self,plugin_dir,name,type,b_conn_t,b_conn_t_old,cur,oldConnValues=[]):
        print('*********ExchangeConntypeFiles********')
        self.plugin_dir=plugin_dir
        self.dictDB=getDBConnectionData(self.plugin_dir)
        dir=self.plugin_dir+"\\"+self.dictDB['projectName']+"\\{}_assettypes".format(type)
        
        if not oldConnValues:
            oldConnValues=getConnsValues(b_conn_t_old,cur)
        connValues=getConnsValues(b_conn_t,cur)
        print(oldConnValues)
        
        file_data=readFileToList(dir+'\\'+name+'.idm')
        file_data=self.delPMT2Comp(file_data,oldConnValues)
        file_data=self.delConnection(file_data,oldConnValues)

        data=[]
        connections=False
        for line in file_data:
            data.append(line)
            if """(MACRO-OBJECT :N "{}\"""".format(name) in line:
                idx=file_data.index(line)
                if file_data[idx].count('(')-file_data[idx].count(')')==0:
                    data[-1]=data[-1].replace('\n','').rstrip()[:-1]+'\n'
                    data.append('\n'.join([""" (:IREF :N "{}_{}_{}_{}" :F 192)""".format(conn['conn_bundle_type_id'],conn['conn_type_seq'],conn['conn_type_id'],conn['conn_seq']) for conn in connValues]))
                    data[-1]+=")\n"
                else:
                    data.append(''.join([""" (:IREF :N "{}_{}_{}_{}" :F 192)\n""".format(conn['conn_bundle_type_id'],conn['conn_type_seq'],conn['conn_type_id'],conn['conn_seq']) for conn in connValues]))
            if """(CONNECTIONS""" in line:
                print('***Connections***')
                openCloseBracktesCounter=line.count('(')-line.count(')')
                connections=True
                del data[-1]
                for conn in connValues:
                    name_pmtmux="{}_{}_{}_{}".format(conn['conn_bundle_type_id'],conn['conn_type_seq'],conn['conn_type_id'],conn['conn_seq'])
                    if conn['p']!=None:
                        variable="P"
                        var_value=conn['p']
                        
                    if conn['mdot']!=None:
                        variable="M"
                        inverse_value=-1 if conn['type'] in [1,3,5,7,9] else 1
                        var_value=conn['mdot'] * inverse_value
                    data.append("""((MODEL :N "{}" :T PMT2\\m\\u\\x)
 (:VAR :N |{}_var| :B (-1 {} 0))
 ((CONNECTOR :N |term_a|)
  (:VAR :N |inStream(T)| :B {})))\n""".format(name_pmtmux,variable,variable,conn['temp']))
                    name_const="{}_{}_{}_{}_{}".format(conn['conn_bundle_type_id'],conn['conn_type_seq'],conn['conn_type_id'],conn['conn_seq'],variable)
                    data.append("""((SOURCE-CONSTANT :N "{}" :T CONSTANT)
 (:PAR :N X :V {}))  \n""".format(name_const,var_value))
 
                data.append("(CONNECTIONS\n")
                for value in connValues:
                    name_pmtmux="{}_{}_{}_{}".format(value['conn_bundle_type_id'],value['conn_type_seq'],value['conn_type_id'],value['conn_seq'])
                    if value['p']!=None:
                        name_const="{}_{}_{}_{}_P".format(value['conn_bundle_type_id'],value['conn_type_seq'],value['conn_type_id'],value['conn_seq'])
                        variable="P"
                    else:
                        name_const="{}_{}_{}_{}_M".format(value['conn_bundle_type_id'],value['conn_type_seq'],value['conn_type_id'],value['conn_seq'])
                        variable="M"
                    data.append(""" (("{}" "{}") ("{}" |term_b|) 0 2 NIL)
 (("{}" {}) ("{}" LINK) 0 0 NIL)\n""".format(name,name_pmtmux,name_pmtmux,name_pmtmux,variable,name_const))
                if openCloseBracktesCounter==0:
                    data[-1]=data[-1].rstrip()+")"

        if not connections:  
            for conn in connValues:
                name_pmtmux="{}_{}_{}_{}".format(conn['conn_bundle_type_id'],conn['conn_type_seq'],conn['conn_type_id'],conn['conn_seq'])
                if conn['p']!=None:
                    variable="P"
                    var_value=conn['p']
                    
                if conn['mdot']!=None:
                    variable="M"
                    inverse_value=-1 if conn['type'] in [1,3,5,7,9] else 1
                    var_value=conn['mdot'] * inverse_value
                data.append("""((MODEL :N "{}" :T PMT2\\m\\u\\x)
 (:VAR :N |{}_var| :B (-1 {} 0))
 ((CONNECTOR :N |term_a|)
  (:VAR :N |inStream(T)| :B {})))\n""".format(name_pmtmux,variable,variable,conn['temp']))
                name_const="{}_{}_{}_{}_{}".format(conn['conn_bundle_type_id'],conn['conn_type_seq'],conn['conn_type_id'],conn['conn_seq'],variable)
                data.append("""((SOURCE-CONSTANT :N "{}" :T CONSTANT)
 (:PAR :N X :V {}))  \n""".format(name_const,var_value))        
            data.append("(CONNECTIONS\n")
            for value in connValues:
                name_pmtmux="{}_{}_{}_{}".format(value['conn_bundle_type_id'],value['conn_type_seq'],value['conn_type_id'],value['conn_seq'])
                if value['p']!=None:
                    name_const="{}_{}_{}_{}_P".format(value['conn_bundle_type_id'],value['conn_type_seq'],value['conn_type_id'],value['conn_seq'])
                    variable="P"
                else:
                    name_const="{}_{}_{}_{}_M".format(value['conn_bundle_type_id'],value['conn_type_seq'],value['conn_type_id'],value['conn_seq'])
                    variable="M"
                data.append(""" (("{}" "{}") ("{}" |term_b|) 0 2 NIL)
 (("{}" {}) ("{}" LINK) 0 0 NIL)\n""".format(name,name_pmtmux,name_pmtmux,name_pmtmux,variable,name_const))
            data[-1]=data[-1].rstrip()+")"
        writeToFileFromList(data,dir,dir+'\\'+name+'.idm')    

        
        filedata=readFileToList(dir+'\\'+name+'.idc')
        filedata=self.delConnection(filedata,oldConnValues)
        counter_p=0
        counter_mdot=0
        for value in connValues:
            name_pmtmux="{}_{}_{}_{}".format(value['conn_bundle_type_id'],value['conn_type_seq'],value['conn_type_id'],value['conn_seq'])
            if value['p']!=None:
                name_const="{}_{}_{}_{}_P".format(value['conn_bundle_type_id'],value['conn_type_seq'],value['conn_type_id'],value['conn_seq'])
                variable="p"
                y=240+counter_p*40
                filedata.append("""(EQUATION-FRAME :AT ((96 {})) :R (9 18.5) :ICON "lib:pmt2mux.ids" :SYMMETRY (180.0) :SLOT ("{}") :NAME "{}" :DATA :EO)\n""".format(y,name_pmtmux,name_pmtmux))
                y=227+counter_p*40
                filedata.append("""(EQUATION-FRAME :AT ((29 {})) :R (28 10) :ICON "sys:constant.ids" :SLOT ("{}") :NAME "{}" :DATA SOURCE-CONSTANT)\n""".format(y,name_const,name_const))
                y=232+counter_p*40
                filedata.append("""(CONNECTION-LINE :AT ((106 {}) (148 {})) :LINE-COLOR (:CALL PMT-COLOR [@ 1] [@ 2]) :LINE-STYLE 3 :FIRST-LINK ("{}" (1 0.278) |term_b|) :LAST-LINK ("{}" (0.0 0.04) "{}"))\n""".format(y,y,name_pmtmux,name,name_pmtmux))
                y=227+counter_p*40
                filedata.append("""(CONNECTION-LINE :AT ((307/5 {}) (87 {})) :FIRST-LINK ("{}" (1 0.5) LINK) :LAST-LINK ("{}" (0.0 0.139) {}) :DIR :RIGHT :ARROW (19 8 8))\n""".format(y,y,name_const,name_pmtmux,variable))
                counter_p+=1
            else:
                name_const="{}_{}_{}_{}_M".format(value['conn_bundle_type_id'],value['conn_type_seq'],value['conn_type_id'],value['conn_seq'])
                variable="M"
                y=240+counter_mdot*40
                filedata.append("""(EQUATION-FRAME :AT ((597 {})) :R (9 18.5) :ICON "lib:pmt2mux.ids" :SLOT ("{}") :NAME "{}" :DATA :EO)\n""".format(y,name_pmtmux,name_pmtmux))
                filedata.append("""(EQUATION-FRAME :AT ((667 {})) :R (28 10) :ICON "sys:constant.ids" :SYMMETRY (180.0) :SLOT ("{}") :NAME "{}" :DATA SOURCE-CONSTANT)\n""".format(y,name_const,name_const))
                filedata.append("""(CONNECTION-LINE :AT ((635 {}) (606 {})) :FIRST-LINK ("{}" (1.0 0.5) {}) :LAST-LINK ("{}" (0 0.5) LINK) :DIR :LEFT :ARROW (19 8 8))\n""".format(y,y,name_pmtmux,variable,name_const))
                y=232+counter_mdot*40
                filedata.append("""(CONNECTION-LINE :AT ((587 {}) (556 {})) :LINE-COLOR (:CALL PMT-COLOR [@ 1] [@ 2]) :LINE-STYLE 3 :FIRST-LINK ("{}" (1 0.278) |term_b|) :LAST-LINK ("{}" (0.0 0.04) "{}"))\n""".format(y,y,name_pmtmux,name,name_pmtmux))
                counter_mdot+=1
        writeToFileFromList(filedata,dir,dir+'\\'+name+'.idc') 

        #assettype macro
        dir=dir+'\\'+name
        filedata=readFileToList(dir+'\\'+name+'.idm')
        filedata=self.delPMT2Comp(filedata,oldConnValues)
        filedata=self.delConnection(filedata,oldConnValues)
        
        meters=[]
        meter={'name':'','n_sup':0,'n_ret':0,'sup_conn':[],'ret_conn':[],'p':True}
        conn_type_old=0        
        i=0
        p_old=True
        p_old_old=True
        for value in connValues:
            name_pmtmux="{}_{}_{}_{}".format(value['conn_bundle_type_id'],value['conn_type_seq'],value['conn_type_id'],value['conn_seq'])
            filedata.insert(2,"""(:IREF :N "{}" :F 192)\n""".format(name_pmtmux))
            filedata.insert(2,"""(MODEL :N "PMT2mux_{}" :T PMT2\\m\\u\\x)\n""".format(name_pmtmux))
            if value['mdot']!=None:
                meter['p']=False
            if value['type'] in [1,3,5,7,9]:
                meter['n_sup']+=1
                meter['sup_conn'].append('PMT2mux_{}'.format(name_pmtmux))
            elif value['type'] in [2,4,6,8,10]:
                meter['n_ret']+=1
                meter['ret_conn'].append('PMT2mux_{}'.format(name_pmtmux))
            meter['name']=str(value['conn_bundle_type_id'])+'_'+str(value['conn_type_seq'])
            if value['conn_type_id']!=conn_type_old and i!=0:
                if value['type']==1:
                    meters.append({'name': meter_name_old_old,'n_sup':meter['n_sup']-1,'n_ret':meter['n_ret'],'sup_conn':meter['sup_conn'][:-1],'ret_conn':meter['sup_conn'],'p': p_old_old})
                    meter={'name':'','n_sup':1,'n_ret':0,'sup_conn':[meter['sup_conn'][-1]],'ret_conn':[],'p':True}
                elif value['type']==2:
                    meters.append({'name': meter_name_old_old,'n_sup':meter['n_sup'],'n_ret':meter['n_ret']-1,'sup_conn':meter['sup_conn'],'ret_conn':meter['sup_conn'][:-1],'p': p_old_old})
                    meter={'name':'','n_sup':0,'n_ret':1,'sup_conn':[],'ret_conn': [meter['ret_conn'][-1]],'p':True}
                if value['mdot']!=None:
                    meter['p']=False
            i+=1
            conn_type_old=value['conn_type_id']
            p_old=meter['p']
            p_old_old=p_old
            meter_name_old=meter['name']
            meter_name_old_old=meter_name_old
        meters.append(meter)   
        print(meters)
        for meter in meters:
            sup_m_conn=' '.join(['('+str(meter['sup_conn'].index(i)+1)+' :MACRO "'+i+'" |M_var|)' for i in meter['sup_conn']])
            sup_t_conn=sup_m_conn.replace('|M_var|','|T_var|')
            ret_m_conn=' '.join(['('+str(meter['ret_conn'].index(i)+1)+' :MACRO "'+i+'" |M_var|)' for i in meter['ret_conn']])
            ret_t_conn=ret_m_conn.replace('|M_var|','|T_var|')
            filedata.insert(2,"""((:EO :N "{}_Flowmeter2" :T FLOWMETER2)
 (:PAR :N N_SUP :V {})
 (:PAR :N N_RET :V {})
 (:VAR :N FLOW_SUP :DIM ({}) :B #S(MS-SPARSE DEFAULT-VALUE NIL DIMENSION 1 VALUE ({})))
 (:VAR :N TSUP :DIM ({}) :B #S(MS-SPARSE DEFAULT-VALUE NIL DIMENSION 1 VALUE ({})))
 (:VAR :N FLOW_RET :DIM ({}) :B #S(MS-SPARSE DEFAULT-VALUE NIL DIMENSION 1 VALUE ({})))
 (:VAR :N TRET :DIM ({}) :B #S(MS-SPARSE DEFAULT-VALUE NIL DIMENSION 1 VALUE ({}))))\n""".format(meter['name'],meter['n_sup'],meter['n_ret'],meter['n_sup'],sup_m_conn,meter['n_sup'],sup_t_conn,meter['n_ret'],ret_m_conn,meter['n_ret'],ret_t_conn))
        
        data=[]
        connections=False
        for line in filedata:
            data.append(line)
            if """(CONNECTIONS""" in line:
                openCloseBracktesCounter=line.count('(')-line.count(')')
                connections=True
                del data[-1]
                data.append('(CONNECTIONS\n')
                for value in connValues:
                    name_pmtmux="{}_{}_{}_{}".format(value['conn_bundle_type_id'],value['conn_type_seq'],value['conn_type_id'],value['conn_seq'])
                    data+="""(("PMT2mux_{}" |term_b|) "{}" 0 0 NIL)\n""".format(name_pmtmux,name_pmtmux)
                if openCloseBracktesCounter==0:
                    data[-1]=data[-1].rstrip()+")"
        if not connections: 
            data.append('(CONNECTIONS\n')
            for value in connValues:
                name_pmtmux="{}_{}_{}_{}".format(value['conn_bundle_type_id'],value['conn_type_seq'],value['conn_type_id'],value['conn_seq'])
                data+="""(("PMT2mux_{}" |term_b|) "{}" 0 0 NIL)\n""".format(name_pmtmux,name_pmtmux)
            data[-1]=data[-1].rstrip()+")"    
        
        writeToFileFromList(data,dir,dir+'\\'+name+'.idm')     
        
        filedata=readFileToList(dir+'\\'+name+'.idc')
        filedata=self.delPMT2Comp(filedata,oldConnValues)
        filedata=self.delConnection(filedata,oldConnValues)
        counter_p=0
        counter_mdot=0
        for value in connValues:
            name_pmtmux="{}_{}_{}_{}".format(value['conn_bundle_type_id'],value['conn_type_seq'],value['conn_type_id'],value['conn_seq'])
            if value['p']!=None:
                name_const="{}_{}_{}_{}_P".format(value['conn_bundle_type_id'],value['conn_type_seq'],value['conn_type_id'],value['conn_seq'])
                variable="P"
                y=37+counter_p*45
                filedata.append("""(CONNECTION-LINE :AT ((10 {}) (50 {})) :LINE-COLOR (:CALL PMT-COLOR [@ 1] [@ 2]) :LINE-STYLE 3 :FIRST-LINK (:SELF (0.0 0.094) "{}") :LAST-LINK ("PMT2mux_{}" (0 0.278) |term_b|))\n""".format(y,y,name_pmtmux,name_pmtmux))
                y=45+counter_p*45
                filedata.append("""(EQUATION-FRAME :AT ((59 {})) :R (8 18) :ICON "lib:pmt2mux.ids" :SLOT ("PMT2mux_{}") :NAME "PMT2mux_{}" :DATA :EO)\n""".format(y,name_pmtmux,name_pmtmux))
                counter_p+=1
            else:
                name_const="{}_{}_{}_{}_M".format(value['conn_bundle_type_id'],value['conn_type_seq'],value['conn_type_id'],value['conn_seq'])
                variable="M"
                y=37+counter_mdot*45
                filedata.append("""(CONNECTION-LINE :AT ((694 {}) (641 {})) :LINE-COLOR (:CALL PMT-COLOR [@ 1] [@ 2]) :LINE-STYLE 3 :FIRST-LINK (:SELF (0.0 0.094) "{}") :LAST-LINK ("PMT2mux_{}" (0 0.278) |term_b|))\n""".format(y,y,name_pmtmux,name_pmtmux))
                y=45+counter_mdot*45
                filedata.append("""(EQUATION-FRAME :AT ((636 {})) :R (8 18) :ICON "lib:pmt2mux.ids" :SYMMETRY (180) :SLOT ("PMT2mux_{}") :NAME "PMT2mux_{}" :DATA :EO)\n""".format(y,name_pmtmux,name_pmtmux))
                counter_mdot+=1
                
        counter_emeter=0
        for meter in meters:
            x=29+counter_emeter*35
            filedata.append("""\n(EQUATION-FRAME :AT (({} 346)) :R (13.5 13.0) :ICON "sys:eo.ids" :SLOT ("{}_Flowmeter2") :NAME "{}_Flowmeter2" :DATA :EO) """.format(x,meter['name'],meter['name']))    
            counter_emeter+=1                
        writeToFileFromList(filedata,dir,dir+'\\'+name+'.idc') 
        print('exchange conn bundle type finished')
        
    def delConnection(self,file_data,oldConnValues):
        data=[]
        print('del Connection')
        for line in file_data:
            if [True for conn in 
                ["""\"{}_{}_{}_{}_M\"""".format(conn['conn_bundle_type_id'],conn['conn_type_seq'],conn['conn_type_id'],conn['conn_seq']) for conn in oldConnValues]+
                ["""\"{}_{}_{}_{}_P\"""".format(conn['conn_bundle_type_id'],conn['conn_type_seq'],conn['conn_type_id'],conn['conn_seq']) for conn in oldConnValues]+
                ["""\"{}_{}_{}_{}\"""".format(conn['conn_bundle_type_id'],conn['conn_type_seq'],conn['conn_type_id'],conn['conn_seq']) for conn in oldConnValues]+
                ["""\"PMT2mux_{}_{}_{}_{}\"""".format(conn['conn_bundle_type_id'],conn['conn_type_seq'],conn['conn_type_id'],conn['conn_seq']) for conn in oldConnValues]+ 
                ["""\"{}_{}_Flowmeter2\"""".format(conn['conn_bundle_type_id'],conn['conn_type_seq']) for conn in oldConnValues]
                if conn in line]:
                print('del connection')
                print(line)
                data[-1]=data[-1].replace('\n','')+''.join([')' for i in range(line.count(')')-line.count('('))])+'\n'
            else:
                data.append(line)
        return data
    
    def delPMT2Comp(self,file_data,oldConnValues):
        data=[]
        del_index=[]
        counter=0
        print('-------------del comp----------')
        while counter < len(file_data):
            while [True for conn in 
                ["""SOURCE-CONSTANT :N "{}_{}_{}_{}_M\"""".format(conn['conn_bundle_type_id'],conn['conn_type_seq'],conn['conn_type_id'],conn['conn_seq']) for conn in oldConnValues]+
                ["""SOURCE-CONSTANT :N "{}_{}_{}_{}_P\"""".format(conn['conn_bundle_type_id'],conn['conn_type_seq'],conn['conn_type_id'],conn['conn_seq']) for conn in oldConnValues]+
                ["""(MODEL :N "{}_{}_{}_{}\"""".format(conn['conn_bundle_type_id'],conn['conn_type_seq'],conn['conn_type_id'],conn['conn_seq']) for conn in oldConnValues]+
                ["""(MODEL :N "PMT2mux_{}_{}_{}_{}\"""".format(conn['conn_bundle_type_id'],conn['conn_type_seq'],conn['conn_type_id'],conn['conn_seq']) for conn in oldConnValues]+
                ["""(:EO :N "{}_{}_Flowmeter2" :T FLOWMETER2)""".format(conn['conn_bundle_type_id'],conn['conn_type_seq']) for conn in oldConnValues]
                if conn in file_data[counter]]:
                data[-1]=data[-1].replace('\n','')+''.join([')' for i in range(file_data[counter].count(')')-file_data[counter].count('('))])+'\n'
                openCloseBracktesCounter=file_data[counter].count('(')-file_data[counter].count(')')
                print(openCloseBracktesCounter)
                counter+=1
                while openCloseBracktesCounter>0:
                    print(file_data[counter])
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

class RenameAssettypeFiles:
    """ Rename the assettypes"""
    def __init__(self,plugin_dir,name,type,new_name,cur):
        self.plugin_dir=plugin_dir
        self.dictDB=getDBConnectionData(self.plugin_dir)
        dir=self.plugin_dir+"\\"+self.dictDB['projectName']+"\\{}_assettypes".format(type)
        filedata=""
        if not os.path.exists(dir+'\\'+name+'.idm') or not os.path.exists(dir+'\\'+name+'.idc'):
            sql=f"""DELETE FROM {type}_assettypes WHERE assetgroup={name.split('_')[0]} AND assettype={name.split('_')[1]};"""
            cur.execute(sql)
            return False
               
        moveFileReplaceStr(dir+'\\'+name+'.idm',dir,dir+'\\'+new_name+'.idm',[name],[new_name],replaceDict=False)     
        moveFileReplaceStr(dir+'\\'+name+'.idc',dir,dir+'\\'+new_name+'.idc',[name],[new_name],replaceDict=False)           
        
        dir_macro_new=dir+'\\'+new_name
        print(dir_macro_new)
        dir_macro=dir+'\\'+name
        print(dir_macro)
        os.rename(dir_macro,dir_macro_new)
        #os.rename(dir_macro_new+'\\'+name+'.idm',dir_macro_new+'\\'+new_name+'.idm')
        moveFileReplaceStr(dir_macro_new+'\\'+name+'.idm',dir_macro_new,dir_macro_new+'\\'+new_name+'.idm',[name],[new_name],replaceDict=False)   
        os.rename(dir_macro_new+'\\'+name+'.idc',dir_macro_new+'\\'+new_name+'.idc')
        
        print('should rename:'+dir_macro_new+'\\'+name)
        if os.path.exists(dir_macro_new+'\\'+name):
            print('rename to: '+dir_macro_new+'\\'+new_name)
            os.rename(dir_macro_new+'\\'+name,dir_macro_new+'\\'+new_name)
            for root, dirs, files in os.walk(dir_macro_new+'\\'+new_name):
                for file in files:
                    if file.endswith('.idm') or file.endswith('.idc'):
                        copyFileReplaceStr(os.path.join(root, file),root,os.path.join(root, file),[name],[new_name],replaceDict=False)
        print('rename finished')

class CopyAssettypeMacro:
    """ Copy invoked assettype macros to IDA network project: customers,plants and devices"""
    def __init__(self,submodel,dir,type,dictDB,cur,plugin_dir,reinvoke,invokedOutputs,requestedOutputs,parallize=False,signals=False):
        print('copy {} macro'.format(type))
        print(f"---------------reinvoke: {reinvoke}----------------")
        print(plugin_dir)
        print(parallize)
        print(signals)
        #print(invokedOutputs)
        type_name=type[:-1]
        target_dir=dir+"\\network_"+str(submodel)
        source_dir=dir+'\\invoked_'+type_name+'s'
                            
        sql="""SELECT f.id, CASE WHEN {} = ANY(l.submodel) THEN 'same-model' ELSE 'decoupled' END AS model, l.submodel
    FROM "{}".{} f, "{}".lines l, "{}".{}_connections conn 
    WHERE f.submodel={} AND l.id=conn.lid AND f.id=conn.{}id AND f.submodel = ANY(l.submodel)
    ORDER BY id;""".format(submodel,dictDB['versionName'],type,dictDB['versionName'],dictDB['versionName'],type_name,submodel, 'c' if type_name=='customer' else 'd' if type_name=='device' else 'ep')
        print(sql)
        cur.execute(sql)
        #collect resources from project files only once
        self.resources=[]
        if reinvoke:
            self.invokedFeatureOutputs={}
        else:
            try: 
                self.invokedFeatureOutputs=invokedOutputs[type]
            except:
                self.invokedFeatureOutputs={}
        self.decoupled_counter=0        
        for feature in cur.fetchall():
            f_idc_target=target_dir+'\\'+type_name.capitalize()+"_"+str(feature['id'])+".idc"
            f_idm_target=target_dir+'\\'+type_name.capitalize()+"_"+str(feature['id'])+".idm"
            print(f_idm_target)

            #idm
            source_f_idm="{}\\{}_{}\\{}_{}.idm".format(source_dir,type_name.capitalize(),str(feature['id']),type_name.capitalize(),str(feature['id']))  
            source_f_idc="{}\\{}_{}\\{}_{}.idc".format(source_dir,type_name.capitalize(),str(feature['id']),type_name.capitalize(),str(feature['id']))     
            
            print(source_f_idm)
            if not os.path.exists(source_f_idm) or reinvoke:
                invokeOneFeature(False,str(feature['id']),plugin_dir,cur,dictDB,type_name,False,False,parallize=parallize,signals=signals)
                if type=='energy_plants':
                    self.invokedFeatureOutputs[feature['id']]={'power_ep': True if requestedOutputs['power_ep'] else False, 'temp_ep': True if requestedOutputs['temp_ep'] else False, 'p_ep': True if requestedOutputs['p_ep'] else False, 'mdot_ep': True if requestedOutputs['mdot_ep'] else False}
                elif type=='customers':
                    self.invokedFeatureOutputs[feature['id']]={'power_c': True if requestedOutputs['power_c'] else False, 'temp_c': True if requestedOutputs['temp_c'] else False, 'p_c': True if requestedOutputs['p_c'] else False, 'mdot_c': True if requestedOutputs['mdot_c'] else False, 'heatbalance_c': True if requestedOutputs['heatbalance_c'] else False, 'troom_c': True if requestedOutputs['troom_c'] else False}

            #collect resources
            source_f="{}\\{}_{}.idm".format(source_dir,type_name.capitalize(),str(feature['id']))     
            file_data=readFileToList(source_f)
            resource=getResourcesFromFileDataList(file_data)
            if resource not in self.resources:
                self.resources+=resource
                
            if feature['model']=='decoupled':
                sql="""SELECT conn_bundle_type FROM "{}".{} f ,{}_assettypes f_at WHERE f.id={} AND f.assettype=f_at.assettype;""".format(dictDB['versionName'],type,type_name,str(feature['id']))
                print(sql)
                cur.execute(sql)
                bundle=cur.fetchone()['conn_bundle_type']
                print(bundle)
                connValues=getConnsValues(bundle,cur)
                #idm
                file_data=readFileToList(source_f_idm)
                file_data=self.delConnection(file_data,connValues)
                file_data=self.connectionImportData(file_data,connValues,submodel,feature['submodel'])
                writeToFileFromList(file_data,target_dir,f_idm_target)

                #idc
                file_data=readFileToList(source_f_idc)
                file_data=self.delConnection(file_data,connValues)
                writeToFileFromList(file_data,target_dir,f_idc_target)
                
            else:
                #idm
                copyFile(source_f_idm,target_dir,f_idm_target)
                #idc            
                copyFile(source_f_idc,target_dir,f_idc_target)
            
            #check if folder contains macros
            #print('----------------------------------------check if macros exist----------------------')
            #print(source_dir+'\\'+type_name.capitalize()+"_"+str(feature['id'])+'\\'+type_name.capitalize()+"_"+str(feature['id']))
            if os.path.exists(source_dir+'\\'+type_name.capitalize()+"_"+str(feature['id'])+'\\'+type_name.capitalize()+"_"+str(feature['id'])):
                for root, dirs, files in os.walk(source_dir+'\\'+type_name.capitalize()+"_"+str(feature['id'])+'\\'+type_name.capitalize()+"_"+str(feature['id'])):
                    for file in files:
                        if file.endswith('.idm') or file.endswith('.idc'):
                            #print('---------macro exists: '+file)
                            subfolder=os.path.dirname(os.path.join(root, file)).replace('/','\\').split(type_name.capitalize()+"_"+str(feature['id'])+'\\'+type_name.capitalize()+"_"+str(feature['id']))[1]
                            path=target_dir+'\\'+type_name.capitalize()+"_"+str(feature['id'])+subfolder
                            createSubDir(path)
                            copyFile(os.path.join(root, file),path,path+'\\'+file)
        print('%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%')
        
    def connectionImportData(self,file_data,conn_values,submodel,cosim):
        """read components :n equals conn_value --> del comp and write new comp with same name and connections"""
        data=[]
        counter=0
        while counter < len(file_data):
            line=file_data[counter]
            pmt2_name=[conn for conn in 
                [[""":N \"PMT2mux_{}_{}_{}_{}\"""".format(conn['conn_bundle_type_id'],conn['conn_type_seq'],conn['conn_type_id'],conn['conn_seq']),conn['p'],conn['mdot']] for conn in conn_values]
                if conn[0] in line]
            if pmt2_name:
                openCloseBracktesCounter=line.count('(')-line.count(')')
                while openCloseBracktesCounter>0:
                    counter+=1
                    openCloseBracktesCounter+=file_data[counter].count('(')-file_data[counter].count(')')
                    if counter>len(file_data):
                        break
                data.append("""((MODEL {} :T PMT2\\m\\u\\x)
 (:VAR :N |P_var| :V 100000{})
 (:VAR :N |M_var| :V -0.01655{})
 (:VAR :N |T_var| :V 70.0)
 ((CONNECTOR :N |term_a|)
  (:VAR :N |inStream(T)| :V 70.0))
 ((CONNECTOR :N |term_b|)
  (:VAR :N |inStream(T)| :V 70.0{})))\n""".format(
                    pmt2_name[0][0],
                    """ :B (:SYSTEM "Co-simulation-macro" "{}<--{}" |data_var| {})""".format(submodel,cosim[0],self.decoupled_counter*2+1) if not pmt2_name[0][1]==None else '',
                    """ :B (:SYSTEM "Co-simulation-macro" "{}<--{}" |data_var| {})""".format(submodel,cosim[0],self.decoupled_counter*2+1) if pmt2_name[0][1]==None else '',
                    """ :B (:SYSTEM "Co-simulation-macro" "{}<--{}" |data_var| {})""".format(submodel,cosim[0],self.decoupled_counter*2+2)
                    ))
                counter+=1
                self.decoupled_counter+=1
            else:
               data.append(file_data[counter]) 
               counter+=1   
        return data
    
    def delConnection(self,file_data,delConns):
        data=[]
        print('del Connection')
        for line in file_data:
            if [True for conn in 
                ["""\"{}_{}_{}_{}\"""".format(conn['conn_bundle_type_id'],conn['conn_type_seq'],conn['conn_type_id'],conn['conn_seq']) for conn in delConns]
                if conn in line]:
                print('del connection')
                print(line)
                data[-1]=data[-1].replace('\n','')+''.join([')' for i in range(line.count(')')-line.count('('))])+'\n'
            else:
                data.append(line)
        return data
        
            
class WriteAssettypeFiles:
    """ writes the .idm and .idc to the plugin folder and adds a macro to define and test assettypes """
    def __init__(self,plugin_dir,name,type,cur,bundle):
        print('write assettype {}'.format(type))
        print('+++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++--------------------')
        self.cur=cur
        self.plugin_dir=plugin_dir
        self.dictDB=getDBConnectionData(self.plugin_dir)
        self.dir=self.plugin_dir+"\\"+self.dictDB['projectName']+"\\{}_assettypes".format(type)
        print('bundle: {}'.format(bundle))
        connValues=getConnsValues(bundle,self.cur)
        print(connValues)
        self.writeIdm(self.dir,name,connValues)
        self.writeIdc(self.dir,name,connValues)
        self.createMacroDir(self.dir,name)
        meters=self.writeMacroIdm(self.dir,name,connValues)
        self.writeMacroIdc(self.dir,name,connValues,meters)
        
        writeSensorMacroIdm(self.dir,name)
        writeSensorMacroIdc(self.dir,name)
        
        writeMacroClimateIdm(self.dictDB,self.cur,name,self.dir,self.plugin_dir,loadModellingSettings(self.plugin_dir,self.dictDB),getClimateData(self.cur,self.dictDB,True))
        writeMacroClimateIdc(name,self.dir,loadModellingSettings(self.plugin_dir,self.dictDB))
        
    def createMacroDir(self,dir,name):
        """ makes a new folder for the assettype macro if it does not exists"""
        createDir(dir,name)
    
    def writeMacroIdm(self,dir,name,connValues):
        data=""";IDA 5.11 Data UTF-8
(DOCUMENT-HEADER :TYPE ICE-MACRO :D "ICE macro" :ETM 3857463573 :APP (ICE :VER 5.11)) """
        meters=[]
        meter={'name':'','n_sup':0,'n_ret':0,'sup_conn':[],'ret_conn':[],'p':True}
        sequence_old=0        
        i=0
        p_old=True
        p_old_old=True
        
        print('***********************************************')
        for value in connValues:
            print(value)
            name_pmtmux="{}_{}_{}_{}".format(value['conn_bundle_type_id'],value['conn_type_seq'],value['conn_type_id'],value['conn_seq'])
            data+="""\n(:IREF :N "{}" :F 192)""".format(name_pmtmux)
            data+="""\n(MODEL :N "PMT2mux_{}" :T PMT2\\m\\u\\x)""".format(name_pmtmux)
            if value['mdot']!=None:
                meter['p']=False
            if value['type'] in [1,3,5,7,9]:
                meter['n_sup']+=1
                meter['sup_conn'].append('PMT2mux_{}'.format(name_pmtmux))
            elif value['type'] in [2,4,6,8,10]:
                meter['n_ret']+=1
                meter['ret_conn'].append('PMT2mux_{}'.format(name_pmtmux))
            meter['name']=str(value['conn_bundle_type_id'])+'_'+str(value['conn_type_seq'])
            if value['conn_type_seq']!=sequence_old and i!=0:
                if value['type'] in [1,3,5,7,9]:
                    meters.append({'name': meter_name_old_old,'n_sup':meter['n_sup']-1,'n_ret':meter['n_ret'],'sup_conn':meter['sup_conn'][:-1],'ret_conn':meter['sup_conn'],'p': p_old_old})
                    meter={'name':'','n_sup':1,'n_ret':0,'sup_conn':[meter['sup_conn'][-1]],'ret_conn':[],'p':True}
                elif value['type'] in [2,4,6,8,10]:
                    meters.append({'name': meter_name_old_old,'n_sup':meter['n_sup'],'n_ret':meter['n_ret']-1,'sup_conn':meter['sup_conn'],'ret_conn':meter['sup_conn'][:-1],'p': p_old_old})
                    meter={'name':'','n_sup':0,'n_ret':1,'sup_conn':[],'ret_conn': [meter['ret_conn'][-1]],'p':True}
                if value['mdot']!=None:
                    meter['p']=False
            i+=1
            sequence_old=value['conn_type_seq']
            p_old=meter['p']
            p_old_old=p_old
            meter_name_old=meter['name']
            meter_name_old_old=meter_name_old
        meters.append(meter)   
        print(meters)

        for meter in meters:
            sup_m_conn=' '.join(['('+str(meter['sup_conn'].index(i)+1)+' :MACRO "'+i+'" |M_var|)' for i in meter['sup_conn']])
            sup_t_conn=sup_m_conn.replace('|M_var|','|T_var|')
            ret_m_conn=' '.join(['('+str(meter['ret_conn'].index(i)+1)+' :MACRO "'+i+'" |M_var|)' for i in meter['ret_conn']])
            ret_t_conn=ret_m_conn.replace('|M_var|','|T_var|')
            data+="""\n((:EO :N "{}_Flowmeter2" :T FLOWMETER2)
 (:PAR :N N_SUP :V {})
 (:PAR :N N_RET :V {})
 (:VAR :N FLOW_SUP :DIM ({}) :B #S(MS-SPARSE DEFAULT-VALUE NIL DIMENSION 1 VALUE ({})))
 (:VAR :N TSUP :DIM ({}) :B #S(MS-SPARSE DEFAULT-VALUE NIL DIMENSION 1 VALUE ({})))
 (:VAR :N FLOW_RET :DIM ({}) :B #S(MS-SPARSE DEFAULT-VALUE NIL DIMENSION 1 VALUE ({})))
 (:VAR :N TRET :DIM ({}) :B #S(MS-SPARSE DEFAULT-VALUE NIL DIMENSION 1 VALUE ({}))))""".format(meter['name'],meter['n_sup'],meter['n_ret'],meter['n_sup'],sup_m_conn,meter['n_sup'],sup_t_conn,meter['n_ret'],ret_m_conn,meter['n_ret'],ret_t_conn)
        data+="\n(CONNECTIONS "   
        for value in connValues:
            name_pmtmux="{}_{}_{}_{}".format(value['conn_bundle_type_id'],value['conn_type_seq'],value['conn_type_id'],value['conn_seq'])
            data+="""\n(("PMT2mux_{}" |term_b|) "{}" 0 0 NIL)""".format(name_pmtmux,name_pmtmux)
        data+=")" 
        writeToFile(data,dir,dir+"""\\{}\\{}.idm""".format(name,name))  
        return meters

    def writeMacroIdc(self,dir,name,connValues,meters):
        data=""";IDA 5.11 Form UTF-8
(DOCUMENT-HEADER :TYPE SCHEMA :PAGE-WIDTH 178 :PAGE-HEIGHT 97) 
(SELF-FRAME :AT ((352 190)) :R (342 176) :SLOT (:SELF) :DATA MACRO-OBJECT) """
        counter_p=0
        counter_mdot=0
        for value in connValues:
            name_pmtmux="{}_{}_{}_{}".format(value['conn_bundle_type_id'],value['conn_type_seq'],value['conn_type_id'],value['conn_seq'])
            if value['p']!=None:
                y=37+counter_p*45
                data+="""\n(CONNECTION-LINE :AT ((10 {}) (50 {})) :LINE-COLOR (:CALL PMT-COLOR [@ 1] [@ 2]) :LINE-STYLE 3 :FIRST-LINK (:SELF (0.0 0.094) "{}") :LAST-LINK ("PMT2mux_{}" (0 0.278) |term_b|))""".format(y,y,name_pmtmux,name_pmtmux)
                y=45+counter_p*45
                data+="""\n(EQUATION-FRAME :AT ((59 {})) :R (8 18) :ICON "lib:pmt2mux.ids" :SLOT ("PMT2mux_{}") :NAME "PMT2mux_{}" :DATA :EO) """.format(y,name_pmtmux,name_pmtmux)
                counter_p+=1
            else:
                y=37+counter_mdot*45
                data+="""\n(CONNECTION-LINE :AT ((694 {}) (641 {})) :LINE-COLOR (:CALL PMT-COLOR [@ 1] [@ 2]) :LINE-STYLE 3 :FIRST-LINK (:SELF (0.0 0.094) "{}") :LAST-LINK ("PMT2mux_{}" (0 0.278) |term_b|))""".format(y,y,name_pmtmux,name_pmtmux)
                y=45+counter_mdot*45
                data+="""\n(EQUATION-FRAME :AT ((636 {})) :R (8 18) :ICON "lib:pmt2mux.ids" :SYMMETRY (180) :SLOT ("PMT2mux_{}") :NAME "PMT2mux_{}" :DATA :EO) """.format(y,name_pmtmux,name_pmtmux)
                counter_mdot+=1
        counter_emeter=0
        for meter in meters:
            x=29+counter_emeter*35
            data+="""\n(EQUATION-FRAME :AT (({} 346)) :R (13.5 13.0) :ICON "sys:eo.ids" :SLOT ("{}_Flowmeter2") :NAME "{}_Flowmeter2" :DATA :EO) """.format(x,meter['name'],meter['name'])    
            counter_emeter+=1
        writeToFile(data,dir,dir+"""\\{}\\{}.idc""".format(name,name))         
    
    def writeIdm(self,dir,name,connValues):    
        data=""";IDA 5.11 Data UTF-8
(DOCUMENT-HEADER :TYPE ICE-SYSTEM :N "{}" :ETM 3856940957 :MS 4 :PARENT ICE :APP (ICE :VER 5.11)) 
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
((MACRO-OBJECT :N "{}" :T ICE-MACRO :ETM 3857461881 :STM 3857461887)""".format(name,name)
        for value in connValues:
            name_pmtmux="{}_{}_{}_{}".format(value['conn_bundle_type_id'],value['conn_type_seq'],value['conn_type_id'],value['conn_seq'])
            data+="""\n (:IREF :N "{}" :F 192)""".format(name_pmtmux)
        data+=")"  
        for value in connValues:
            name_pmtmux="{}_{}_{}_{}".format(value['conn_bundle_type_id'],value['conn_type_seq'],value['conn_type_id'],value['conn_seq'])
            if value['p']!=None:
                variable="P"
                var_value=value['p']
                
            if value['mdot']!=None:
                variable="M"
                inverse_value=-1 if value['type'] in [1,3,5,7,9] else 1
                var_value=value['mdot']*inverse_value
            data=data+"""\n((MODEL :N "{}" :T PMT2\\m\\u\\x)
 (:VAR :N |{}_var| :B (-1 {} 0))
 ((CONNECTOR :N |term_a|)
  (:VAR :N |inStream(T)| :B {})))""".format(name_pmtmux,variable,variable,value['temp'])
            name_const="{}_{}_{}_{}_{}".format(value['conn_bundle_type_id'],value['conn_type_seq'],value['conn_type_id'],value['conn_seq'],variable)
            data=data+"""\n((SOURCE-CONSTANT :N "{}" :T CONSTANT)
 (:PAR :N X :V {}))  """.format(name_const,var_value)
        data+="""\n((MACRO-OBJECT :N "Climate-macro" :T ICE-MACRO :ETM 3857526820 :STM 3857526845))"""
        data+="""\n((MACRO-OBJECT :N "Sensor-macro" :T ICE-MACRO :ETM 3857526820 :STM 3857526845))"""
        data+="""\n(CONNECTIONS"""
        for value in connValues:
            name_pmtmux="{}_{}_{}_{}".format(value['conn_bundle_type_id'],value['conn_type_seq'],value['conn_type_id'],value['conn_seq'])
            if value['p']!=None:
                name_const="{}_{}_{}_{}_P".format(value['conn_bundle_type_id'],value['conn_type_seq'],value['conn_type_id'],value['conn_seq'])
                variable="P"
            else:
                name_const="{}_{}_{}_{}_M".format(value['conn_bundle_type_id'],value['conn_type_seq'],value['conn_type_id'],value['conn_seq'])
                variable="M"
            data+="""\n (("{}" "{}") ("{}" |term_b|) 0 2 NIL)
 (("{}" {}) ("{}" LINK) 0 0 NIL)""".format(name,name_pmtmux,name_pmtmux,name_pmtmux,variable,name_const)
        data+=""")"""
        writeToFile(data,dir,dir+"""\\{}.idm""".format(name))

    def writeIdc(self,dir,name,connValues):
        data=""";IDA 5.11 Form UTF-8
(DOCUMENT-HEADER :TYPE SCHEMA :PAGE-WIDTH 197 :PAGE-HEIGHT 290) 
(EQUATION-FRAME :AT ((63 145)) :R (20 20) :ICON "sys:eo.ids" :SLOT ("Climate-macro") :NAME "Climate-macro" :DATA MACRO-OBJECT) 
(EQUATION-FRAME :AT ((352 348)) :R (203.5 126.5) :ICON "sys:eo.ids" :SLOT ("{}") :NAME "{}" :DATA MACRO-OBJECT)
(EQUATION-FRAME :AT ((116 145)) :R (20 20) :ICON "sys:eo.ids" :SLOT ("Sensor-macro") :NAME "Sensor-macro" :DATA MACRO-OBJECT) 
(TEXT-OBJECT :VALUE "Results" :AT ((504 4) (565 18)) :STYLE LABEL) 
(LIST-FIELD :AT ((504 20) (763 100)) :SLOT (:RESULTS) :TEXT-COLOR #S(RGB RED 0 GREEN 0 BLUE 0)) 
(LABEL-TEXT :VALUE "Project:" :FONT (:SWISS :ARIAL 11 1) :VERTICAL :CENTER :WRAP-P NIL :AT ((12 8) (96 24))) 
(FIELD :AT ((100 8) (496 29)) :SLOT (NAME) :TEXT-COLOR #S(RGB RED 0 GREEN 0 BLUE 160) :FONT (:SWISS :ARIAL 17 2) :HELP-STRING "NAME" :TYPE SYMBOL) 
(LABEL-TEXT :VALUE "Description:" :FONT (:SWISS :ARIAL 11 1) :VERTICAL :CENTER :WRAP-P NIL :AT ((13 33) (96 53))) 
(FIELD :AT ((96 32) (496 100)) :SLOT (DESCRIPTION) :TEXT-COLOR #S(RGB RED 0 GREEN 0 BLUE 0)) 
(LINE :AT ((21 108) (760 108))) """.format(name,name)
        counter_p=0
        counter_mdot=0
        for value in connValues:
            name_pmtmux="{}_{}_{}_{}".format(value['conn_bundle_type_id'],value['conn_type_seq'],value['conn_type_id'],value['conn_seq'])
            if value['p']!=None:
                name_const="{}_{}_{}_{}_P".format(value['conn_bundle_type_id'],value['conn_type_seq'],value['conn_type_id'],value['conn_seq'])
                variable="p"
                y=240+counter_p*40
                data+="""\n(EQUATION-FRAME :AT ((96 {})) :R (9 18.5) :ICON "lib:pmt2mux.ids" :SYMMETRY (180.0) :SLOT ("{}") :NAME "{}" :DATA :EO) """.format(y,name_pmtmux,name_pmtmux)
                y=227+counter_p*40
                data+="""\n(EQUATION-FRAME :AT ((29 {})) :R (28 10) :ICON "sys:constant.ids" :SLOT ("{}") :NAME "{}" :DATA SOURCE-CONSTANT) """.format(y,name_const,name_const)
                y=232+counter_p*40
                data+="""\n(CONNECTION-LINE :AT ((106 {}) (148 {})) :LINE-COLOR (:CALL PMT-COLOR [@ 1] [@ 2]) :LINE-STYLE 3 :FIRST-LINK ("{}" (1 0.278) |term_b|) :LAST-LINK ("{}" (0.0 0.04) "{}")) """.format(y,y,name_pmtmux,name,name_pmtmux)
                y=227+counter_p*40
                data+="""\n(CONNECTION-LINE :AT ((307/5 {}) (87 {})) :FIRST-LINK ("{}" (1 0.5) LINK) :LAST-LINK ("{}" (0.0 0.139) {}) :DIR :RIGHT :ARROW (19 8 8)) """.format(y,y,name_const,name_pmtmux,variable)
                counter_p+=1
            else:
                name_const="{}_{}_{}_{}_M".format(value['conn_bundle_type_id'],value['conn_type_seq'],value['conn_type_id'],value['conn_seq'])
                variable="M"
                y=240+counter_mdot*40
                data+="""\n(EQUATION-FRAME :AT ((597 {})) :R (9 18.5) :ICON "lib:pmt2mux.ids" :SLOT ("{}") :NAME "{}" :DATA :EO) """.format(y,name_pmtmux,name_pmtmux)
                data+="""\n(EQUATION-FRAME :AT ((667 {})) :R (28 10) :ICON "sys:constant.ids" :SYMMETRY (180.0) :SLOT ("{}") :NAME "{}" :DATA SOURCE-CONSTANT) """.format(y,name_const,name_const)
                data+="""\n(CONNECTION-LINE :AT ((635 {}) (606 {})) :FIRST-LINK ("{}" (1.0 0.5) {}) :LAST-LINK ("{}" (0 0.5) LINK) :DIR :LEFT :ARROW (19 8 8)) """.format(y,y,name_pmtmux,variable,name_const)
                y=232+counter_mdot*40
                data+="""\n(CONNECTION-LINE :AT ((587 {}) (556 {})) :LINE-COLOR (:CALL PMT-COLOR [@ 1] [@ 2]) :LINE-STYLE 3 :FIRST-LINK ("{}" (1 0.278) |term_b|) :LAST-LINK ("{}" (0.0 0.04) "{}")) """.format(y,y,name_pmtmux,name,name_pmtmux)
                counter_mdot+=1


        #print (data)
        writeToFile(data,dir,dir+"\\{}.idc".format(name))