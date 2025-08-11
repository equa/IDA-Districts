from plugins.utility_functions.files import *
import psycopg2.extras
import psycopg2
from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT
plugin_dir="""C:\\Users\\Peter\\AppData\\Roaming\\QGIS\\QGIS3\\profiles\\default\\python\\plugins\\"""
dictDB={'pwd' : 'p3t3r' , 'host' : 'localhost','port':'5433', 'user' : 'postgres', 'projectName' : 'test4', 'versionName' : 'a'}


#dictDB=getDBConnectionData(plugin_dir)
conn=dbConnect(dictDB,True)
cur=conn.cursor(cursor_factory = psycopg2.extras.RealDictCursor)
#print(cur)

def getSFDict(pList,sf={}):
    for comp in pList:
        #print(comp)
        if getCompClass(comp)=='SOURCE-FILE':
            #print(line)
            key=comp[0][':SF']
            entry=getCompName(comp)
            try:
                sf[key]=sf[key]+[entry]
            except:
                sf[key]=[entry]
                    
    sf={i: set(sf[i])for i in sf}
    return sf


def replaceKeywordsInPList(plist,replaceDict):
    data=[]
    #print('--------replace keywords-------------')
    #print(replaceDict)
    for comp in plist:
        comp_name=getCompName(comp)[1:-1]
        #print(comp_name)
        if comp_name in replaceDict:
            #print('---replace---')
            model_type=getCompTemplate(comp)
            #print(model_type)
            model_language=modelLanguage(model_type)
            pre_suffix='|' if model_language=='MODELICA' else ''
            if getCompClass(comp)=='SOURCE-FILE':
                comp[0][':DOCUMENT-PATH']=replaceDict[comp_name][':SOURCE-FILE'].replace('\\','\\\\')
                comp[0][':SF']=replaceDict[comp_name][':SOURCE-FILE'].replace('\\','\\\\')
                data.append(comp)
            else:
                new_comp=[]            
                for i in comp:
                    i_name=getCompName(i).replace('|','')
                    if i_name in replaceDict[comp_name]:
                        i[':V']=replaceDict[comp_name][i_name]
                        parms.append(getCompName(i))
                        new_comp.append(i)
                    else:
                        new_comp.append(i)
                for i in replaceDict[comp_name]:
                    if i not in parms:
                        new_comp.append({':C':':PAR', ':N': pre_suffix+i+pre_suffix,':V': replaceDict[comp_name][i]})
                data.append(new_comp)
        else:
            data.append(comp)
        
    return data
    
template_name="1_1_Heating 1 Supply & 1 Return"
source_file=plugin_dir+"""ida_data\\{}\\{}_templates""".format(dictDB['projectName'],'customer')+'\\'+template_name+'\\'+template_name+'.idm'
#print(source_file)
components_idm=propertyListCompsIDM(getIDAListComponents(readFileToString(source_file)))
replaceDict={}
dhw_file="C:\\lkjdfg.prn"

#get model parameter
sql="""SELECT * FROM "{}".model_parms ORDER BY id;""".format(dictDB['versionName'])
#print(sql)
cur.execute(sql)
parms=cur.fetchall()
#print(parms)
sql="""SELECT * FROM "{}".customers WHERE id={};""".format(dictDB['versionName'],1)
#print(sql)
cur.execute(sql)
fields=cur.fetchone()
#print(fields)
                
for parm in parms:
    mapping_expression=parm['mapping_expression']
    for field in fields:
        if '"'+field+'"'=='"dhw_id"' and mapping_expression=='"dhw_id"':
            mapping_expression=dhw_file
        elif '"'+field+'"'=='"internal_load_id"' and mapping_expression=='"internal_load_id"':
            mapping_expression=internal_loads_file
        else:
            mapping_expression=mapping_expression.replace('"'+field+'"',str(fields[field]))
    try:
        mapping_expression=eval(mapping_expression)
    except:
        pass
    #print('++++++++'+parm['model_name'])
    if parm['macro_name'] and parm['parm_name'] and parm['model_name'] and parm['mapping_direction'] in ['<-->','-->']:
        #print(parm['model_name'])
        try:
            replaceDict[parm['macro_name']][parm['model_name']][parm['parm_name']]= mapping_expression
        except:
            try:
                replaceDict[parm['macro_name']].update({parm['model_name']:{parm['parm_name']: mapping_expression}})
            except:
                replaceDict[parm['macro_name']]={parm['model_name']:{parm['parm_name']: mapping_expression}}
#print(replaceDict)

replaceDict={j : replaceDict[i][j] for i in replaceDict if i in [':FEATURE'] for j in replaceDict[i]}
#print(replaceDict)

components_idm=replaceKeywordsInPList(components_idm,replaceDict)
sf=getSFDict(components_idm,sf={})
#print(sf)
for comp in components_idm:
    #print(comp)
    pass





        