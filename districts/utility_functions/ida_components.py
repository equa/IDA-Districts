from .utility import *
from .db import *

import re
import ast

def getSimData(requestedOutputs,networkSimData):
    #print(networkSimData)
    calc_from_time=getNTPTimeFromString(networkSimData['calc_time_from'])
    calc_to_time=getNTPTimeFromString(networkSimData['calc_time_to'])
    startup_from_time=getNTPTimeFromString(networkSimData['startup_time_from'])
    startup_to_time=getNTPTimeFromString(networkSimData['startup_time_to'])
    
    return """((SIMULATION_DATA :N SIMULATION_DATA)
 (:PAR :N HMAX :V {})
 ((SIMULATION_PHASE :N STARTUP-PHASE)
  (:PAR :N FROM-TIME :V {})
  (:PAR :N TO-TIME :V {})
  (:PAR :N PERIODS :V {})
  (:PAR :N PERIODIC-P :V {}))
 ((SIMULATION_PHASE :N CALCULATION-PHASE)
  (:PAR :N FROM-TIME :V {})
  (:PAR :N TO-TIME :V {})
  (:PAR :N PERIODS :V {})
  (:PAR :N OUTPUT-STEP :V {})
  (:PAR :N PERIODIC-P :V {})))""".format(networkSimData['max_timestep'],startup_from_time,startup_to_time,networkSimData['numb_of_periods'],networkSimData['startup_type'],calc_from_time,calc_to_time,networkSimData['numb_of_periods'],requestedOutputs['dt_outputs'],networkSimData['calc_type'])
         
def parse_bracketsBetweenAlphanumericCharAndOpenBracket(match_obj):
    return match_obj[0][0]+"',("
    
def parse_hashtagS(match_obj):
    return "#S',("
    
def parse_hashtag(match_obj):
    return "#',("
    
def parse_hashtag2dimArray(match_obj):
    return "#2A',("
    
def parse_hashtag3dimArray(match_obj):
    return "#3A',("
 
def parse_closingBracketsConnectedToDigit(match_obj):
    return "),'"+match_obj[0][-1]

def parse_AlphanumericCharSeparatedOpeningBrackets(match_obj):
    return match_obj[0][0]+"',("
    
def parse_ClosingBracketsConnectedToAlphanumericChar(match_obj):
    return "),'" +match_obj[0][-1]

def getIDAListComponents(data):
    data=data.replace('""','$empty_str$')
    string_list = re.findall(r"\"([^\"]+)\"", data)    
    string_list=set(string_list)
    #print(string_list)
    # value_str=re.findall(r"\:VALUE\s+\(([A-Za-z0-9_\s+\-\$\\\<\>\=\:\"\/\'\;\,]+)\)", data)
    
    value_list=[]
    for value in re.findall(r"\:VALUE\s+\(([^\)]+)*\)", data):
        #print(value)
        if ':DICT ' not in value and re.search('[a-zA-Z]', value):
            value_list.append(value)
            data=data.replace(' ('+value+')','')
            #print(data)

    #print(data)
    
    def replace_func(x):
        if x.group(1):
            return x.group(1)
        elif x.group(2):
            return x.group(2)
        elif x.group(3):
            return ':VALUE\',"""'+value_list.pop()+' """'

    for i,s in enumerate(sorted(list(string_list),key=len,reverse=True)):
        #print(s)
        data=data.replace('"'+s+'"','"${}$"'.format(i))
    #print(data)

    data=data.replace('\n',',')
    data=re.sub(r"\s+", " ", data)

    #print(data)
    #data=re.sub(r"\w\s+\(", parse_bracketsBetweenAlphanumericCharAndOpenBracket, data)
    data=re.sub(r'(\w\s+\()|(\"\s+\()|(\|\s+\()', parse_bracketsBetweenAlphanumericCharAndOpenBracket, data)
    #print(data)

    data=re.sub(r"\w,\s+\(", parse_AlphanumericCharSeparatedOpeningBrackets, data)
    #print(data)
    
    data=re.sub(r"(\)\s+\w)|(\)\s+\")|(\)\s+\|)", parse_ClosingBracketsConnectedToAlphanumericChar, data)
    #print(data)

    data=re.sub(r"\#\(", parse_hashtag, data)
    #print(data)
    
    data=re.sub(r"\#2A\(", parse_hashtag2dimArray, data)
    #print(data)

    data=re.sub(r"\#3A\(", parse_hashtag3dimArray, data)
    #print(data)

    data=re.sub(r"\#S\(", parse_hashtagS, data)
    #print(data)

    data=re.sub(r"\)\s+\:", "),':", data)
    #print(data)

    data=re.sub(r"\)\s+\d", parse_closingBracketsConnectedToDigit, data)

    data=re.sub(r"\)\s+", ")", data)

    data=re.sub(r"\s+\(", '(', data)
    #print(data)

    data=data.replace("(((","[[[\'").replace("((","[[\'").replace("(","[\'").replace("))))))","\']]]]]]").replace(")))))","\']]]]]").replace("))))","\']]]]").replace(")))","\']]]").replace("))","\']]").replace(")","\']").replace(" ","\',\'")
    data=data.replace("|inStream['","|inStream(").replace("']|",")|").replace('][','],[')

    for i,s in enumerate(sorted(list(string_list),key=len,reverse=True)):
        data=data.replace('"${}$"'.format(i),'"'+s.replace('\n',' ')+'"')

    #print(data)
    data=data.replace('\\','\\\\')
    #print(data)
    i=0
    
    value_list.reverse()
    if value_list:
        #print(value_list)
        # Pattern to match `:VALUE` followed by a quoted string (Group 3)
        pattern = r"(:VALUE','\")|(:VALUE',\[':DICT)|(:VALUE')"
        data = re.sub(pattern, replace_func, data)
    #print(data)
    data=data.replace('$empty_str$','""')
    #print(data)

    return safe_eval(data)
    
def propertyListCompsIDM(comps):
    return [propertyListIDM(comp) for comp in comps]
    
def propertyListCompsIDC(comps):
    return [propertyListIDC(comp) for comp in comps]

def getImportVars(f_ids,template_data_ex,sensor_dec_data):
    importVars=[]
    importSignals=[]
    for f in f_ids:
        #print(f)
        for t_d_conn in template_data_ex:
            if t_d_conn['feature']==f['feature'] and t_d_conn['template']==f['template']:
                for data_ex in t_d_conn['data_ex']:
                    for var in data_ex[':IMPORT']:
                        #print(var)
                        #print(var.replace('"','').split('_')[-1])
                        if not data_ex[':N']==':SELF':
                            importVars.append(var)
                        elif [True for i in sensor_dec_data for j in i['irefs_target'] if str(i['sensor_id'])==var.replace('"','').split('_')[-1] and j['iref'].split('_')[1]==str(f['id'])]:
                            importSignals.append(var)
    #print(importSignals)
    #print([j for i in sensor_dec_data for j in i['irefs_source'] if (j['iref'].split('_')[1] in [str(f['id']) for f in f_ids] or not(i['function']==6 and i['source_type']==3)) and str(i['sensor_id']) in [var.replace('"','').split('_')[-1] for var in importSignals]])
    return importVars+[j for i in sensor_dec_data for j in i['irefs_source'] if (j['iref'].split('_')[1] in [str(f['id']) for f in f_ids] or not(i['function']==6 and i['source_type']==3)) and str(i['sensor_id']) in [var.replace('"','').split('_')[-1] for var in importSignals]]

def getExportVars(f_ids,template_data_ex,sensor_dec_data,mode):
    exportVars=[]
    counter = alt_count(start=1)
    #print(template_data_ex)
    exportSignalDict={}

    for f in f_ids:
        for t_d_conn in template_data_ex:
            if t_d_conn['feature']==f['feature'] and t_d_conn['template']==f['template']:
                for data_ex in t_d_conn['data_ex']:
                    for var in data_ex[':EXPORT']:
                        sensor_id=var.replace('"','').split('_')[-1]
                        if not data_ex[':N']==':SELF':
                            exportVars.append("""({} {} "{}{}" {} {})""".format(next(counter),':SYSTEM' if mode=='network' else ":PLANT",'{}_'.format(f['feature'].capitalize()) if mode=='network' else 'substation b',f['id'],data_ex[':N'],var))
                        elif [True for i in sensor_dec_data for j in i['irefs_source'] if str(i['sensor_id'])==sensor_id and j['iref'].split('_')[1]==str(f['id'])]:
                            #print(var)
                            sensor_id=int(sensor_id)

                            #check if target type ==supervisory ctrl (3) and measure==5 and function ==individual signals for each target (6)
                            iref=[j['iref'] if i['target_type']==3 and i['measure']==5 and i['function']==6  else sensor_id
                                for i in sensor_dec_data if i['sensor_id']==sensor_id
                                for j in i['irefs_source'] if j['iref'].split('_')[1]==str(f['id'])]
                            try:
                                if iref in [j for i in exportSignalDict[sensor_id] for j in i['iref']]:
                                    exportSignalDict[sensor_id]=[{'iref':iref,'counter': j['counter']+1} for i in exportSignalDict[sensor_id] for j in i if j['iref']==iref]
                                else:
                                    exportSignalDict[sensor_id]=exportSignalDict[sensor_id]+[{'iref':iref,'counter':1}]
                            except:
                                exportSignalDict[sensor_id]=[{'iref':iref,'counter':1}]
    for k in dict(sorted(exportSignalDict.items())):
        exportVars.extend(["""({} :SYSTEM "Sensor-macro" "Sensor_{}" INSIGNAL {})""".format(next(counter),iref,l) 
            for m in exportSignalDict[k]
            for l in range(1,m['counter']+1) for iref in m['iref']])
    #print(exportVars)
    return exportVars

def propertyListIDM(seq):
    #print(seq)
    i=0
    comp_list=[]
    dict_={}
    while i<len(seq):
        #print(i)
        #print(seq[i])
        if type(seq[i])==list:
            #print('recursive call')
            comp_list.append(propertyListIDM(seq[i]))
            i+=1
        else:
            if i==0:
                dict_[':C']=seq[0]
                i+=1
            if dict_[':C']=='CONNECTIONS':
               # #print('!!CONNECTIONS!!')
                conns=[]
                while i<len(seq):
                    conns.append(seq[i])
                    i+=1
                dict_[':CONNS']=conns
            else:    
                value=''
                key=seq[i]
                #print('key: '+str(key))
                #print('length: '+str(len(seq))+'; i: '+str(i))
                while i<len(seq)-1:
                    if i<len(seq)-2 and seq[i+2][0]==':':
                        try:
                            if type(seq[i+1])==list:
                                value+=listToBracketsString(seq[i+1])
                            else:
                                value+=seq[i+1]
                        except:
                            pass
                        #print('break loop: '+str(value))
                        break
                    else:
                        #print('concatenate')
                        if type(seq[i+1])==list:
                            value+=listToBracketsString(seq[i+1])
                        else:
                            value+=seq[i+1]
                        #print(value)
                        i+=1
                try:
                    if value:
                        dict_[key]=value
                    else:
                        dict_[seq[i]]=seq[i+1]#.asList()
                except:
                    dict_[seq[i]]=seq[i+1]
                #print(dict)
                i+=2
        
    if comp_list:
        #print('return list:' + str(comp_list))
        return comp_list
    else:
        #print('return dict:' + str(dict)) 
        return dict_    

def propertyListIDC(seq):
    #print(seq)
    i=0
    dict_={}
    while i<len(seq):
        if i==0:
            dict_[':C']=seq[0]
            i+=1
        else:
            value=''
            value_list=[]
            key=seq[i]
            #print('key: '+str(key))
            #print('length: '+str(len(seq))+'; i: '+str(i))
            while i<len(seq)-1:
                if i==len(seq)-2 or i<len(seq)-2 and seq[i+2][0]==':':
                    try:
                        if type(seq[i+1])==list:
                            if value:
                                value_list.append(value)
                                value=''
                            value_list.append(seq[i+1])
                        else:
                            value+=seq[i+1]
                    except:
                        pass
                    #print('break loop: '+str(value))
                    break
                else:
                    #print('concatenate')
                    if type(seq[i+1])==list:
                        if value:
                            value_list.append(value)
                            value=''
                        value_list.append(seq[i+1])
                    else:
                        value+=seq[i+1]
                    i+=1
            #print(value_list)
            #print(value)
            try:
                if value_list:
                    if value:
                        value_list.append(value)
                    if len(value_list)==1:
                        dict_[key]=value_list[0]
                    else:
                        if value_list[0][0]=='#':
                            dict_[key]=value_list[0]+listToBracketsString(value_list[1])
                        else:    
                            dict_[key]=listToBracketsString(value_list)
                elif value:
                    dict_[key]=value
                else:
                    dict_[seq[i]]=seq[i+1]#.asList()
            except:
                dict_[seq[i]]=seq[i+1]
            #print(dict_)
            i+=2
        
    return dict_ 
        
def pListToCompString(pList,level):
    r = ''
    i=0
    if type(pList)==dict:
        if pList[':C']=='CONNECTIONS':
            return '(CONNECTIONS{})'.format(''.join(['\n '+listToBracketsString(conn) for conn in pList[':CONNS']]))
    for item in pList:
        if isinstance(item,list): 
            r+= ('(' if i==0 else '\n'+''.join([" " for j in range(level+1)]))+pListToCompString(item,level+1)+(')' if i==len(pList)-1 else '')
        elif isinstance(item,dict):
            r+= ('(' if i==0 else '\n'+''.join([" " for j in range(level+1)]))+pListToCompString(item,level+1)+(')' if i==len(pList)-1 else '')
        else:
            if isinstance(pList[item],list):
                value=listToBracketsString(pList[item])
            else:
                value=pList[item]
            if item[0]==':':
                r+=('(' if i==0 else ' ') +('' if i==0 else item+' ')+value+(')' if i==len(pList)-1 else '')
            else:
                r+=('(' if i==0 else ' ') +item+(')' if i==len(pList)-1 else '')
        i+=1
    return r

    
def modelLanguage(model):
    if model in ('TANKSTRAT','PUMPCIRC','CONSTANT','BOIL1CIRC','CHIL1CIRC','MULTIPLIER','ADDER','SCRIPT-OUTPUT','PUMPMCTRL'):
        return 'NMF'
    else:
        return 'MODELICA'

def getModelInterfaces(model):
    """from network view"""
    models={'|hx|': {'import':['|mLiqB|','|TsupB|','|PhiHxLimit_var|','|TbSet_var|'],'export':['|TbOut|']}}
    try:
        return models[model] 
    except:
        return ''                 

def checkFeatureSubmodel(id,submodel,feature,feature_ids_per_submodel,cur,config):
    return [True for k in feature_ids_per_submodel if str(k['id'])==str(id) and k['feature']==feature]

def getFeatureIdsPerSubmodel(submodel,cur,config):
    sql="""(
    SELECT 1 AS feature, id FROM "{}".customers WHERE submodel={}
    UNION
    SELECT 2 AS feature, id FROM "{}".energy_plants WHERE submodel={}
)
ORDER BY feature,id;""".format(config['versionName'],submodel,config['versionName'],submodel,submodel) # nosec B608
    cur.execute(sql)
    return cur.fetchall()
    
def getDataExFeature(conns_idc,dec_models,components_idm,network_side,sensor_data,submodel,feature_id,cur,config):
    data_ex=[]
    feature_ids_per_submodel=getFeatureIdsPerSubmodel(str(submodel),cur,config)
    PhiHxLimit_signal=False
    TbSet_signal=False
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
            if model_name==':SELF' and link in ['"Int_Ref_Sensor_Source_{}"'.format(i['sensor_id']) for i in sensor_data for j in i['irefs_source'] if j.split('_')[1]==str(feature_id) and (model_name_connected not in dec_models and checkFeatureSubmodel(j.split('_')[1],submodel,i['source_type'],feature_ids_per_submodel,cur,config) and network_side==False or model_name_connected in dec_models and not checkFeatureSubmodel(j.split('_')[1],submodel,i['source_type'],feature_ids_per_submodel,cur,config) and network_side)]:
                data_ex+=[{':N':model_name,':T': 'OUT',
                    ':IMPORT': [],
                    ':EXPORT': [link],
                    ':CONN-IDC':conn_idc}]
            if model_name==':SELF' and link in ['"Int_Ref_Sensor_Target_{}"'.format(i['sensor_id']) for i in sensor_data for j in i['irefs_target'] if j.split('_')[1]==str(feature_id) and (model_name_connected not in dec_models and checkFeatureSubmodel(j.split('_')[1],submodel,i['target_type'],feature_ids_per_submodel,cur,config) and network_side==False or model_name_connected in dec_models and not checkFeatureSubmodel(j.split('_')[1],submodel,i['target_type'],feature_ids_per_submodel,cur,config) and network_side)]:
                data_ex+=[{':N':model_name,':T': 'IN',
                    ':IMPORT': [link],
                    ':EXPORT': [],
                    ':CONN-IDC':conn_idc}]
    hx=[j[':N'] for j in data_ex if j[':T']=='|hx|']
    for conn_idc in conns_idc:
        if (conn_idc[':FIRST-LINK'][0] ==':SELF' and conn_idc[':LAST-LINK'][0] in hx or
            conn_idc[':LAST-LINK'][0] ==':SELF' and conn_idc[':FIRST-LINK'][0] in hx ):
            if '|PhiHxLimit|' in str(conn_idc):
                PhiHxLimit_signal=True
            if '|TbSet|' in str(conn_idc):
                TbSet_signal=True
    for ex in data_ex:
        if ex[':N'] in hx:
            if PhiHxLimit_signal:
                ex[':EXPORT']=[i for i in ex[':EXPORT'] if not i=='|PhiHxLimit_var|']
                ex[':IMPORT']=[i for i in ex[':IMPORT'] if not i=='|PhiHxLimit_var|']
                #print(ex[':EXPORT'])
            if TbSet_signal:
                ex[':EXPORT']=[i for i in ex[':EXPORT'] if not i=='|TbSet_var|']
                ex[':IMPORT']=[i for i in ex[':IMPORT'] if not i=='|TbSet_var|']
                #print(ex[':EXPORT'])
    return data_ex

def getDataExTemplate(conns_idc,dec_models,components_idm,network_side,sensor_dec_data,submodel,cur,config):
    data_ex=[]
    PhiHxLimit_signal=False
    TbSet_signal=False
    for conn_idc in conns_idc:
        #print(conn_idc)
        if conn_idc[':FIRST-LINK'][0] in dec_models and conn_idc[':LAST-LINK'][0] not in dec_models or conn_idc[':FIRST-LINK'][0] not in dec_models and conn_idc[':LAST-LINK'][0] in dec_models:           
            #print(conn_idc)
            if conn_idc[':FIRST-LINK'][0] in dec_models and conn_idc[':LAST-LINK'][0] not in dec_models:
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
            #print('***')
            #print(link)
            #print(model_name)
            #print(model_name_connected)
            #print(link_connected)

            if not [True for model in data_ex if model[':N']==model_name]:
                comp=getCompPerName(components_idm,model_name)
                link_data = getModelInterfaces(getCompTemplate(comp))
                if link_data:
                    data_ex+=[{':N':model_name,':T': getCompTemplate(comp),
                        ':IMPORT': (link_data['import'] if network_side else link_data['export']),
                        ':EXPORT':(link_data['export'] if network_side else link_data['import']),
                        ':CONN-IDC':conn_idc}]
            if model_name==':SELF' and link in ['"Int_Ref_Sensor_Source_{}"'.format(i['sensor_id']) for i in sensor_dec_data for j in i['irefs_source'] if (model_name_connected not in dec_models and str(submodel)==j['submodel'] and not network_side or model_name_connected in dec_models and str(submodel)!=j['submodel'] and network_side)]:
                data_ex+=[{':N':model_name,':T': 'OUT',
                    ':IMPORT': [],
                    ':EXPORT': [link],
                    ':CONN-IDC':conn_idc}]
            if model_name==':SELF' and link in ['"Int_Ref_Sensor_Target_{}"'.format(i['sensor_id']) for i in sensor_dec_data if i['source_type']==3 and i['function']==5 and submodel==str(getSupervisorySubmodel(cur,config)['submodel']) 
                and [True for j in i['irefs_target'] if j['cosim']==submodel and not j['network_side']]]:
                #print('supervisory target')
                data_ex+=[{':N':model_name,':T': 'OUT',
                    ':IMPORT': [],
                    ':EXPORT': [link],
                    ':CONN-IDC':conn_idc}]
            if model_name==':SELF' and link in ['"Int_Ref_Sensor_Target_{}"'.format(i['sensor_id']) for i in sensor_dec_data for j in i['irefs_target'] if (model_name_connected not in dec_models and str(submodel)==j['submodel'] and not network_side or model_name_connected in dec_models and str(submodel)!=j['submodel'] and network_side)]:
                #print('target')
                data_ex+=[{':N':model_name,':T': 'IN',
                    ':IMPORT': [link],
                    ':EXPORT': [],
                    ':CONN-IDC':conn_idc}]
    hx=[j[':N'] for j in data_ex if j[':T']=='|hx|']
    for conn_idc in conns_idc:
        if (conn_idc[':FIRST-LINK'][0] ==':SELF' and conn_idc[':LAST-LINK'][0] in hx or
                conn_idc[':LAST-LINK'][0] ==':SELF' and conn_idc[':FIRST-LINK'][0] in hx ):
            if '|PhiHxLimit|' in str(conn_idc):
                PhiHxLimit_signal=True
            if '|TbSet|' in str(conn_idc):
                TbSet_signal=True
    for ex in data_ex:
        if ex[':N'] in hx:
            if PhiHxLimit_signal:
                ex[':EXPORT']=[i for i in ex[':EXPORT'] if not i=='|PhiHxLimit_var|']
                ex[':IMPORT']=[i for i in ex[':IMPORT'] if not i=='|PhiHxLimit_var|']
                #print(ex[':EXPORT'])
                #print(ex[':IMPORT'])
            if TbSet_signal:
                ex[':EXPORT']=[i for i in ex[':EXPORT'] if not i=='|TbSet_var|']
                ex[':IMPORT']=[i for i in ex[':IMPORT'] if not i=='|TbSet_var|']
                #print(ex[':EXPORT'])
                #print(ex[':IMPORT'])
                
    return data_ex
    
def getCompImportPos(comp_name,var_name,data_ex):
    #print('--getCompImportPos--')
    #print(comp_name)
    #print(var_name)
    var_counter=1
    i=0
    for comp_ex in data_ex:
        if comp_name==data_ex[i][':N']:
            #print(i)
            break
        var_counter+=len(comp_ex[':IMPORT'])  
        i+=1
    for imp in data_ex[i][':IMPORT']:
        if imp==var_name:
    #        #print(imp)
            break
        var_counter+=1
    #print(var_counter)
    #print('++')
    return var_counter
    
def getCompPerName(pList,name):
    return next(iter([comp for comp in pList if getCompName(comp)==name]),'')
    
def getCompPerTemplate(pList,template):
    return next(iter([comp for comp in pList if getCompTemplate(comp)==template]),'')

def setCompValue(pList,value):
    pList[':V']=str(value)
    return pList
    
def getCompClass(pList):    
    try:
        return pList[':C']
    except:
        return pList[0][':C']
        
def getCompName(pList):    
    try:
        return pList[':N']
    except:
        try:
            return pList[0][':N']
        except:
            return ''
            
def renameCompName(pList,new_name):    
    try:
        pList[':N']=new_name
        return pList
    except:
        try:
            pList[0][':N']=new_name
            return
        except:
            return ''

def getCompTemplate(pList):    
    try:
        return pList[':T']
    except:
        try:
            return pList[0][':T']
        except:
            return ''
            
def getModelType(line):
    type=''
    for char in line.split(':T ')[1]:
        if char==' ' or char==')':
            break
        else:
            type+=char
    return type

def getParName(line,model_language):
    try:
        return line.split(':N {}'.format('|' if model_language=='MODELICA' else ''))[1].strip().split('|' if model_language=='MODELICA' else ' ')[0]
    except:
        #Modelica names just with upper case have no '|'
        return line.split(':N ')[1].strip().split(' ')[0]
    
def countOpenCloseBrackets(line):
    return line.count('(')-line.count(')')
    
def getParmRunsInputNames(file_data):      
    input_names=[]
    i=0
    while i < len(file_data):
        if "((AGGREGATE :N INPUT)" in file_data[i]:
            openCloseBracketsCounter=countOpenCloseBrackets(file_data[i])
            i+=1
            while openCloseBracketsCounter>0:
                openCloseBracketsCounter+=countOpenCloseBrackets(file_data[i])
                try:
                    input_names.append(file_data[i].split(':PAR :N "')[1].split('"')[0])
                except:
                    #print('failed')
                    pass
                if openCloseBracketsCounter==0:
                    break
                i+=1
        i+=1
    return input_names

def getParmRunsOutputNames(file_data):      
    output_names=[]
    i=0
    while i < len(file_data):
        if "((AGGREGATE :N OUTPUT)" in file_data[i]:
            openCloseBracketsCounter=countOpenCloseBrackets(file_data[i])
            i+=1
            while openCloseBracketsCounter>0:
                openCloseBracketsCounter+=countOpenCloseBrackets(file_data[i])
                try:
                    output_names.append(file_data[i].split(':PAR :N "')[1].split('"')[0])
                except:
                    #print('failed')
                    pass
                if openCloseBracketsCounter==0:
                    break
                i+=1
        i+=1
    return output_names
    
def getParmRunsInputNamesTargets(file_data):
    input_names_target={}
    i=0
    while i < len(file_data):
        if "((AGGREGATE :N INPUT)" in file_data[i]:
            openCloseBracketsCounter=countOpenCloseBrackets(file_data[i])
            i+=1
            while openCloseBracketsCounter>0:
                openCloseBracketsCounter+=countOpenCloseBrackets(file_data[i])
                try:
                    input_names_target[file_data[i].split(':PAR :N "')[1].split('"')[0]]=(file_data[i].split('TARGET (')[1].split(')')[0].split()[-2:])
                except:
                    #print('failed')
                    pass
                if openCloseBracketsCounter==0:
                    break
                i+=1
        i+=1
    return input_names_target

def getParmRunsOutputNamesTargets(file_data):
    output_names_target={}
    i=0
    while i < len(file_data):
        if "((AGGREGATE :N OUTPUT)" in file_data[i]:
            openCloseBracketsCounter=countOpenCloseBrackets(file_data[i])
            i+=1
            while openCloseBracketsCounter>0:
                openCloseBracketsCounter+=countOpenCloseBrackets(file_data[i])
                try:
                    output_names_target[file_data[i].split(':PAR :N "')[1].split('"')[0]]=(file_data[i].split('TARGET (')[1].split(')')[0].split()[-2:])
                except:
                    #print('failed')
                    pass
                if openCloseBracketsCounter==0:
                    break
                i+=1
        i+=1
    return output_names_target

def getBestParmRunsInputs (file_data):
    min_error=[1000000000000000000]
    min_inputs=''
    i=0
    while i < len(file_data):
        if ":T PARMRUN-SUMMARY-ITEM" in file_data[i]:
            i+=1
            inputs=file_data[i].split('INPUT :V (')[1].strip().strip(')').split(' ')
            #print(inputs)
            i+=1
            try:
                #print(file_data[i].split('OUTPUT :V (')[1].strip())
                #print(file_data[i].split('OUTPUT :V (')[1].strip().strip(')'))
                #print(file_data[i].split('OUTPUT :V (')[1].strip().strip(')').split(' '))
                error=[float(i) for i in file_data[i].split('OUTPUT :V (')[1].strip().strip(')').split(' ')]
                #print(error)
                if error[0]<min_error[0]:
                    min_error=error
                    min_inputs=inputs
            except:
                #print('failed')
                pass
        i+=1
        
    return [min_error,min_inputs]