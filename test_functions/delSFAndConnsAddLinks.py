from plugins.utility_functions.files import *
import psycopg2.extras
import psycopg2
from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT
plugin_dir="""C:\\Users\\Peter\\AppData\\Roaming\\QGIS\\QGIS3\\profiles\\default\\python\\plugins\\"""
dictDB={'pwd' : 'p3t3r' , 'host' : 'localhost','port':'5433', 'user' : 'postgres', 'projectName' : 'test4', 'versionName' : 'a'}


sf=[[{':C': 'SOURCE-FILE', ':DOCUMENT-PATH': 'C:\\\\Users\\\\Peter\\\\AppData\\\\Roaming\\\\QGIS\\\\QGIS3\\\\profiles\\\\default\\\\python\\\\plugins\\\\ida_mosim\\\\models\\\\test4\\\\a\\\\dhw_profiles\\\\dhw_150_l7day.prn', ':SF': 'C:\\\\Users\\\\Peter\\\\AppData\\\\Roaming\\\\QGIS\\\\QGIS3\\\\profiles\\\\default\\\\python\\\\plugins\\\\ida_mosim\\\\models\\\\test4\\\\a\\\\dhw_profiles\\\\dhw_150_l7day.prn', ':N': '"SOURCE-FILE_DHW"', ':T': 'SOURCE-FILE', ':COL': 'T'}, {':C': ':INT', ':N': '"DHW"', ':F': '32', ':V': '(MDOT)'}, {':C': ':VAR', ':N': 'MDOT', ':T': 'GENERIC', ':U': '||', ':S': '(:DEFAULT T 2)', ':AS': '2'}], 
    [{':C': 'SOURCE-FILE', ':DOCUMENT-PATH': '"C:\\\\Users\\\\Peter\\\\AppData\\\\Roaming\\\\QGIS\\\\QGIS3\\\\profiles\\\\default\\\\python\\\\plugins\\\\ida_data\\\\Samples\\\\internal_loads\\\\01_OIB_residential_1_2.prn"', ':SF': '"C:\\\\Users\\\\Peter\\\\AppData\\\\Roaming\\\\QGIS\\\\QGIS3\\\\profiles\\\\default\\\\python\\\\plugins\\\\ida_data\\\\Samples\\\\internal_loads\\\\01_OIB_residential_1_2.prn"', ':N': '"SOURCE-FILE_internal_loads"', ':T': 'SOURCE-FILE', ':COL': 'T'}, {':C': ':INT', ':N': '"DHW"', ':F': '32', ':V': '(MDOT)'}, {':C': ':INT', ':N': '"Occupancy_load"', ':F': '32', ':V': '(PERSON_W7M2)'}, {':C': ':INT', ':N': '"Electricity_load"', ':F': '32', ':V': '(ELECTRICITY_W7M2)'}, {':C': ':VAR', ':N': 'PERSON_W7M2', ':T': 'GENERIC', ':U': '||', ':S': '(:DEFAULT T 2)', ':AS': '2'}, {':C': ':VAR', ':N': 'ELECTRICITY_W7M2', ':T': 'GENERIC', ':U': '||', ':S': '(:DEFAULT T 2)', ':AS': '3'}]]
template_name="1_1_heating 1 supply & 1 return"
source_file=plugin_dir+"""ida_data\\{}\\{}_templates""".format(dictDB['projectName'],'customer')+'\\'+template_name+'\\'+template_name+'.idm'
#print(source_file)
plist=propertyListCompsIDM(getIDAListComponents(readFileToString(source_file)))
#print(plist)

def getSFLinkRefs(sf):
    refs={}
    for i in sf:
        #print(i)
        if getCompClass(i)==':INT':
            refs[i[':N']]=i[':V'][1:-1]
            #print(sf)
    return refs
    
#print(getSFLinkRefs(sf))

def delSFAndConnsAddLinks(plist,sf):
    data=[]
    sf_names_dict={i[0][':N']: getSFLinkRefs(i) for i in sf}
    #print(sf_names_dict)
    sf_names=[i[0][':N'] for i in sf]
    #print(sf_names)
    
    link_dict={}
    
    for i in plist[-1][':CONNS']:
        if i[0][0] in sf_names or i[1][0] in sf_names:
            #print(i)
            if i[0][0] in sf_names:
                model_name=i[1][0]
                model_link=listToBracketsString(i[1][1]) if isinstance(i[1][1],list) else i[1][1]
                sf_name=i[0][0]
                sf_link=sf_names_dict[sf_name][i[0][1]]
            else:
                model_name=i[0][0]
                model_link=listToBracketsString(i[0][1]) if isinstance(i[0][1],list) else i[0][1]
                sf_name=i[1][0]
                sf_link=sf_names_dict[sf_name][i[1][1]]
            try:
                link_dict[model_name][model_link]={'sf_name': sf_name, 'sf_link': sf_link}
            except:
                link_dict[model_name]={model_link:{'sf_name': sf_name, 'sf_link': sf_link}}
    #print(link_dict)
    
       
    for comp in plist:
        if getCompClass(comp)=='SOURCE-FILE':
            #print('ssssssssssssssffffffffffffffffffffffffffff')
        else:
            #print(getCompName(comp))
            if getCompName(comp) in link_dict:
                #print('++++++++update++++++++++++')
                try:
                    var_names=[j.split()[0][1:] for j in link_dict[getCompName(comp)] if len(j.split())>1]
                except:
                    var_names=[]
                #print(var_names)
                new_comp=[]
                for i in comp:
                    #print(i)
                    if getCompClass(i)==':VAR':
                        try:                        
                            if i[':B'].split()[1] in link_dict[getCompName(comp)]:
                                #print('***binding value****')
                                binding=i[':B'].split()[1]
                                #print(binding)
                                #print(link_dict[getCompName(comp)][binding]['sf_link'])
                                i[':B']="""(:SYSTEM "sf-macro" "SOURCE-FILE-{}" {})""".format(sf_names.index(link_dict[getCompName(comp)][binding]['sf_name'])+1,link_dict[getCompName(comp)][binding]['sf_link'])
                                #print(i)
                            elif 'MS-SPARSE' in i[':B'] and [True for j in var_names if j in i[':B'].split(' VALUE ')[1][:-1]]:
                                #print('---binding matrix---')
                                #print(i)
                                bindings=getIDAListComponents(i[':B'].split(' VALUE ')[1][:-1])
                                #print(bindings)
                                new_bindings=[]
                                for binding in bindings:
                                    #print(binding)
                                    if binding[2][0] in var_names:
                                        #print(binding[2][0])
                                        binding_name='({} {})'.format(binding[2][0],binding[2][1])
                                        #print(binding_name)
                                        new_bindings.append([binding[0],':SYSTEM','"sf-macro"', '"SOURCE-FILE-{}"'.format(sf_names.index(link_dict[getCompName(comp)][binding_name]['sf_name'])+1),link_dict[getCompName(comp)][binding_name]['sf_link']])
                                    else:
                                        new_bindings.append(binding)
                                #print(new_bindings)
                                #print(listToBracketsString(new_bindings))
                                i[':B']="#S(MS-SPARSE {} VALUE {})".format(i[':B'].split('MS-SPARSE ')[1].split(' VALUE ')[0],listToBracketsString(new_bindings))
                                
                            new_comp.append(i)
                        except:
                            new_comp.append(i)  
                    else:
                        new_comp.append(i)                              
                data.append(new_comp)
            elif getCompClass(comp)=='CONNECTIONS':
                new_conns=[]
                for i in comp[':CONNS']:
                    if i[0][0] in sf_names or i[1][0] in sf_names:
                        #print('++del conn++')
                        pass
                    else:
                        new_conns.append(i)
                comp[':CONNS']=new_conns
                data.append(comp)
            else:
                data.append(comp)
    return data
    
plist=delSFAndConnsAddLinks(plist,sf)

#print(plist)