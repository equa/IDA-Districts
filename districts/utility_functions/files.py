import os
import shutil
from .utility import *
from .ida_components import *
from qgis.core import Qgis, QgsMessageLog

def collect_files_by_extension(root_folder: str, extension: str):
    """
    Recursively collect all files with a specific extension from a folder tree.

    Args:
        root_folder (str): Root directory to start searching from.
        extension (str): File extension (e.g. '.txt' or 'txt').

    Returns:
        List[str]: List of full file paths matching the extension.
    """
    if not extension.startswith('.'):
        extension = '.' + extension

    matched_files = []

    for dirpath, _, filenames in os.walk(root_folder):
        for filename in filenames:
            if filename.endswith(extension):
                full_path = os.path.join(dirpath, filename)
                matched_files.append(full_path)

    return matched_files
    
def replace_in_files(folder_path, filename, replace_string, new_string):
    for root, dirs, files in os.walk(folder_path):
        for file in files:
            if file == filename:
                file_path = os.path.join(root, file)

                try:
                    with open(file_path, 'r', encoding='utf-8') as f:
                        content = f.read()

                    new_content = content.replace(replace_string, new_string)

                    if content != new_content:
                        with open(file_path, 'w', encoding='utf-8') as f:
                            f.write(new_content)
                        #print(f"Ersetzt in: {file_path}")
                    else:
                        pass
                        #print(f"Kein Treffer in: {file_path}")

                except Exception as e:
                    pass
                    #print(f"Fehler bei {file_path}: {e}")
                    
def replace_in_file(file_path, old_string, new_string):
    try:
        with open(file_path, 'r', encoding='utf-8') as file:
            content = file.read()

        if old_string in content:
            content = content.replace(old_string, new_string)
            with open(file_path, 'w', encoding='utf-8') as file:
                file.write(content)
            #print(f"Updated: {file_path}")
    except Exception as e:
        pass

def replace_in_folder(root_folder, old_string, new_string, file_extensions=None, exclude_filenames=None):
    for dirpath, _, filenames in os.walk(root_folder):
        for filename in filenames:
            if exclude_filenames and filename in exclude_filenames:
                continue
            if file_extensions is None or filename.endswith(tuple(file_extensions)):
                full_path = os.path.join(dirpath, filename)
                replace_in_file(full_path, old_string, new_string)
                
def writeMacroSFIdm(config,cur,dir):
    sql='SELECT id,sf,vars FROM "{}".invoked_sf;'.format(config['versionName'])
    cur.execute(sql)
    sf_ids=cur.fetchall()     
    #print(sf_ids)

    filedata=[""";IDA {} Data UTF-8
(DOCUMENT-HEADER :TYPE DISTRICTS-MACRO :D "Districts macro" :APP (DISTRICTS :VER {})) """.format(getIDAVersion(config),getIDADistrictsVersion(config))]
    filedata+=["""\n((SOURCE-FILE :DOCUMENT-PATH {} :SF {} :N "SOURCE-FILE-{}" :T SOURCE-FILE :COL T){})""".format(i['sf'],i['sf'],i['id'],''.join([" (:VAR :N {} :T GENERIC)".format(j) for j in i['vars'] ])) for i in sf_ids if i['vars']!=None]
    writeToFileFromList(filedata,dir,dir+'\\sf-macro.idm') 
    #print(dir)
                
def writeMacroSFIdc(config,cur,dir):
    sql='SELECT id,sf FROM "{}".invoked_sf;'.format(config['versionName'])
    cur.execute(sql)
    sf_ids=cur.fetchall()
        
    filedata=[""";IDA {} Data UTF-8
(DOCUMENT-HEADER :TYPE SCHEMA :PAGE-WIDTH 178 :PAGE-HEIGHT 97) 
(SELF-FRAME :AT ((352 190)) :R (342 176) :SLOT (:SELF) :DATA MACRO-OBJECT) """.format(getIDAVersion(config))]
    filedata+=["""\n(EQUATION-FRAME :AT ((50 {})) :R (20 20) :ICON "sys:source-file.ids" :SLOT ("SOURCE-FILE-{}") :NAME "SOURCE-FILE-{}" :DATA SOURCE-FILE :D "SOURCE-FILE")""".format(30+counter*48,i['id'],i['id']) for counter,i in enumerate(sf_ids,1)]
    writeToFileFromList(filedata,dir,dir+'\\sf-macro.idc')
    
def readAndReplaceFileToList(file,replaceDict):
    data=[]
    if os.path.exists(file):
        with open(file, "r") as myfile:   
            for line in myfile:
                if line:
                    for replaceKey in replaceDict:
                        line=line.replace(replaceKey,replaceDict[replaceKey])
                    if line.endswith('\n'):            
                        data.append(line)
                    else:
                        data.append(line+'\n')
    return data
    
def readFileToList(file):
    data=[]
    if os.path.exists(file):
        with open(file, "r") as myfile:   
            for line in myfile:
                if line:
                    if line.endswith('\n'):            
                        data.append(line)
                    else:
                        data.append(line+'\n')
    return data
        
def loadProjectConfig(config,project_name=None,signals=False):
    project_config=''
    name=project_name if project_name else config['projectName']
    if name:
        config_f="{}{}\\configProject.txt".format(config['pathProjects'],name)
        #print(config_f)
        if os.path.exists(config_f):
            #print(config_f)
            with open(config_f, "r") as myfile:   
                for line in myfile:        
                    project_config+=line
        else:
            #print('Failed to load project config!')
            if signals:
                signals.error.emit('Failed to load project config!')
            return {'srid':''}
        project_config=strToDict(project_config)
    else:
        #print('No project name')
        pass
    #print(project_config)    
    return project_config
            
def writeProjectConfig(config,db_name,configProject):
    config_path=config_f="{}{}".format(config['pathProjects'],db_name)
    config_f=config_path+"\\configProject.txt"
    if os.path.exists(config_path):
        with open(config_f, "w") as myfile:   
            myfile.write(str(configProject))
            
def writeRequestedOutputs(config,requestedOutputs):
    file=config['pathProjects']+config['projectName']+"\\requestedOutputs.txt"
    with open(file, "w") as myfile:   
        myfile.write(str(requestedOutputs))
        
def writeSimulatedOutputs(config,simulatedOutputs):
    file=config['pathProjects']+config['projectName']+"\\versions\\"+config['versionName']+"\\simulatedOutputs.txt"
    with open(file, "w") as myfile:   
        myfile.write(str(simulatedOutputs))
        
def writeInvokedOutputs(config,invokedOutputs):
    file=config['pathProjects']+config['projectName']+"\\versions\\"+config['versionName']+"\\invokedOutputs.txt"
    with open(file, "w") as myfile:   
        myfile.write(str(invokedOutputs))
            
def loadRequestedOutputs(plugin_dir,config):
    requestedOutputs=""
    if config['projectName']:
        dir=config['pathProjects']+config['projectName']
        file="{}\\requestedOutputs.txt".format(dir)
        if os.path.exists(file):
            #print(file)
            with open(file, "r") as myfile:   
                for line in myfile:        
                    requestedOutputs+=line
        else:
            #load from template in data center plugin if file does not exists
            file_template=plugin_dir+"\\config\\requestedOutputs_template.txt"
            if os.path.exists(file_template):
                #print(file_template)
                with open(file_template, "r") as myfile:   
                    for line in myfile:        
                        requestedOutputs+=line
        #print(requestedOutputs)
        requestedOutputs=strToDict(requestedOutputs)
    else:
        #print('No project name')
        pass
    return requestedOutputs
    
def loadSimulatedOutputs(config):
    simulatedOutputs=""
    if config['projectName']:
        dir=config['pathProjects']+config['projectName']+"\\versions\\"+config['versionName']
        file="{}\\simulatedOutputs.txt".format(dir)
        if os.path.exists(file):
            #print(file)
            with open(file, "r") as myfile:   
                for line in myfile:        
                    simulatedOutputs+=line
        else:
            return False
        #print(simulatedOutputs)
        simulatedOutputs=strToDict(simulatedOutputs)
    else:
        #print('No project name')
        pass
    return simulatedOutputs
    
def loadInvokedOutputs(config):
    invokedOutputs=""
    if config['projectName']:
        dir=config['pathProjects']+config['projectName']+"\\versions\\"+config['versionName']
        file="{}\\invokedOutputs.txt".format(dir)
        if os.path.exists(file):
            #print(file)
            with open(file, "r") as myfile:   
                for line in myfile:        
                    invokedOutputs+=line
        else:
            return {'customers': {}, 'lines': {}, 'energy_plants': {}}
        invokedOutputs=eval(invokedOutputs)
        #print(invokedOutputs)
    else:
        #print('No project name')
        pass
    return invokedOutputs
    
def writeModellingSettings(config,modellingSettings):
    file=config['pathProjects']+config['projectName']+"\\versions\\"+config['versionName']+"\\modellingSettings.txt"
    with open(file, "w") as myfile:   
        myfile.write(str(modellingSettings))
        
def writeNetworkSimData(config,modellingSettings):
    file=config['pathProjects']+config['projectName']+"\\versions\\"+config['versionName']+"\\networkSimData.txt"
    with open(file, "w") as myfile:   
        myfile.write(str(modellingSettings))
            
def loadModellingSettings(plugin_dir,config):
    modellingSettings=""
    if config['projectName']:
        dir=config['pathProjects']+config['projectName']+"\\versions\\"+config['versionName']
        file="{}\\modellingSettings.txt".format(dir)
        if os.path.exists(file):
            #print(file)
            with open(file, "r") as myfile:   
                for line in myfile:        
                    modellingSettings+=line
        else:
            #load from template in data center plugin if file does not exists
            file_template=plugin_dir+"\\config\\modellingSettings_template.txt"
            if os.path.exists(file_template):
                #print(file_template)
                with open(file_template, "r") as myfile:   
                    for line in myfile:        
                        modellingSettings+=line
        #print(modellingSettings)
        modellingSettings=strToDict(modellingSettings)
    else:
        #print('No project name')
        pass
    return modellingSettings
    
def loadNetworkSimData(plugin_dir,config):
    networkSimData=""
    if config['projectName']:
        dir=config['pathProjects']+config['projectName']+"\\versions\\"+config['versionName']
        file="{}\\networkSimData.txt".format(dir)
        if os.path.exists(file):
            #print(file)
            with open(file, "r") as myfile:   
                for line in myfile:        
                    networkSimData+=line
        else:
            #load from template in data center plugin if file does not exists
            file_template=plugin_dir+"\\config\\networkSimData_template.txt"
            if os.path.exists(file_template):
                #print(file_template)
                with open(file_template, "r") as myfile:   
                    for line in myfile:        
                        networkSimData+=line
        #print(networkSimData)
        networkSimData=strToDict(networkSimData)
    else:
        #print('No project name')
        pass
    return networkSimData    
        
def createDir(dir,name):
    """ makes a new folder if it does not exists"""
    if os.path.exists(dir):
        dir = os.path.join(dir,name)
        if not os.path.exists(dir):
            os.mkdir(dir)  

def getDirFiles(dir,extension):
    return [f for f in os.listdir(dir) if os.path.isfile(os.path.join(dir, f)) and os.path.join(dir, f).endswith(extension)]

def getNetworkFileSubmodels(dir):
    return ['_'.join(f.split('_')[1:]).split('.idm')[0] for f in getDirFiles(dir,'.idm') if f.split('_')[0]=='network']
    
def getBuildingFileSubmodels(dir):
    return ['_'.join(f.split('_')[1:]).split('.idm')[0] for f in getDirFiles(dir,'.idm') if f.split('_')[0]=='building']

def createSubDir(dir):
    """ makes a new folder and subfolders if it does not exists"""
    if not os.path.exists(dir):
        os.makedirs(dir)  
            
def removeFilesInDir(dir):
    if os.path.exists(dir):
        for root, dirs, files in os.walk(dir, topdown=False):
            for name in files:
                os.remove(os.path.join(root, name))
            for name in dirs:
                os.rmdir(os.path.join(root, name))
                
def writePropertyListIDMToFile(plist,dir,file,config):
    #print(dir)
    if os.path.exists(dir):
        #print(file)
        with open(file,'w') as myfile:
            myfile.write(';IDA {} Data UTF-8\n'.format(getIDAVersion(config)))
            for comp in plist:
                #print(comp)
                myfile.write(pListToCompString(comp,0)+'\n')
 
def writePropertyListIDCToFile(plist,dir,file,config):
    #print(dir)
    if os.path.exists(dir):
        #print(file)
        with open(file,'w') as myfile:
            myfile.write(';IDA {} Form UTF-8\n'.format(getIDAVersion(config)))
            for comp in plist:
                myfile.write(pListToCompString(comp,0)+'\n')
                
def readFileToString(file,skipFirstLine=True):
    data=''
    i=0 if skipFirstLine else 1
    if os.path.exists(file):
        with open(file, "r") as myfile:
            for line in myfile:
                if i!=0:
                    data+=line
                i+=1
    #print(data)
    return data
    
def writeToFile(data,dir,file):
    """ write data to file in dir"""
    #print(dir)
    if os.path.exists(dir):
        #print(file)
        with open(file,'w') as myfile:
            myfile.write(data) 
            
def writeToFileFromList(data,dir,file):
    """ write data to file in dir"""
    #print(dir)
    if os.path.exists(dir):
        #print(file)
        with open(file,'w') as myfile:
            for line in data:
                myfile.write(line) 
            
def appendToFile(data,dir,file):
    """ write data to file in dir"""
    #print(dir)
    if os.path.exists(dir):
        #print(file)
        with open(file,'a') as myfile:
            myfile.write(data) 
            
def checkFilePathExists(title,file_path):
    if not title:
        title="ERROR"
    if os.path.exists(file_path):
        return True
    else:
        #iface.messageBar().pushMessage(title, "File not found: {}!".format(file_path), level=Qgis.Critical)
        return False
 
def checkDirExists(title,dir):
    if not title:
        title="ERROR"
    if os.path.exists(dir):
        return True
    else:
        #iface.messageBar().pushMessage(title, "Directory not found: {}!".format(dir), level=Qgis.Critical)
        return False
        
def copyFile(src_file,dst_dir,dst_file):
    """Copy a file within given directory"""
    if checkFilePathExists(False,src_file):
        if checkDirExists(False,dst_dir):
            shutil.copy(src_file,dst_file)

def getSFList(pList,sf=[]):
    for comp in pList:
        #print(comp)
        if getCompClass(comp)=='SOURCE-FILE':
            #print('++++SF++++')
            #print(comp)
            if comp not in sf:
                sf.append(comp)
    #print(sf)                
    return sf
    
def getUsedtemplatesFDict(plugin_dir,cur,config):
    usedFeaturetemplates=getUsedFeatureTemplates(cur,config)
    #print(usedFeaturetemplates)

    sf={}
    for template in usedFeaturetemplates:
        #print(template)
        template_name="{}_{}".format(template['template'],template['template_name'])
        #print(template_name)
        dir=plugin_dir+"""\\{}\\{}_templates""".format(config['projectName'],template['feature'])
        filedata=readFileToList(dir+'\\'+template_name+'\\'+template_name+'.idm')
        
        for line in filedata:
            #print(line)
            if ':SF' in line and ':DOCUMENT-PATH' in line:
                #print(line)
                key=line.split(':DOCUMENT-PATH "')[1].split('"')[0]
                entry=line.split(':N "')[1].split('"')[0]
                try:
                    sf[key]=sf[key]+[entry]
                except:
                        sf[key]=[entry]
                    
    sf={i: set(sf[i])for i in sf}
    #print(sf)
    return sf
    
def replaceKeywordsInFiledata(file_data,replaceDict):
    data=[]
    counter=0
    #print('--------replace keywords-------------')
    #print(replaceDict)
    while counter < len(file_data):
        replace=[key for key in replaceDict if ':N "'+key+'"' in file_data[counter]]
        if replace:
            #print('Replace model parm: '+replace[0])
            openCloseBracketsCounter=countOpenCloseBrackets(file_data[counter])
            #print('openCloseBracketsCounter='+str(openCloseBracketsCounter))
            model_type=getModelType(file_data[counter])
            #print(model_type)
            model_language=modelLanguage(model_type)
            modelicaLabelling='|' if model_language=='MODELICA' else ''
            #print(model_language)
            if openCloseBracketsCounter>0:
                #print(file_data[counter])
                parms=[]
                if ':T SOURCE-FILE' in file_data[counter] and ':SOURCE-FILE' in [parDict for parDict in replaceDict[replace[0]]]:
                    #print(':SF')
                    path=[replaceDict[replace[0]][i] for i in replaceDict[replace[0]] if i==':SOURCE-FILE'][0]
                    data.append("""((SOURCE-FILE :DOCUMENT-PATH "{}" :SF "{}" :N "{}" :T SOURCE-FILE :COL T){}\n""".format(path,path,replace[0],')' if openCloseBracketsCounter==0 else ''))
                    parms.append(':SOURCE-FILE')
                else:
                    data.append(file_data[counter])
                counter+=1
                while openCloseBracketsCounter>0:
                    openCloseBracketsCounter+=countOpenCloseBrackets(file_data[counter])
                    if "(:PAR :N " in file_data[counter]:
                        par_name=getParName(file_data[counter],model_language)
                        #print(par_name)

                        if par_name in [parDict for parDict in replaceDict[replace[0]]]:
                            #print('replace parm')
                            data.append(' (:PAR :N {}{}{} :V {})\n'.format(modelicaLabelling,par_name,modelicaLabelling,replaceDict[replace[0]][par_name]))
                            parms.append(par_name)
                            exchangeParmValue=True
                        else:
                            data.append(file_data[counter])
                            exchangeParmValue=False
                    else:
                        data.append(file_data[counter])
                        exchangeParmValue=False
                    if openCloseBracketsCounter==0:
                        #print('counter = 0')
                        if not exchangeParmValue:
                            data[-1]=data[-1].rstrip()[:-1]+"\n"
                        data+=[" (:PAR :N {}{}{} :V {})\n".format(modelicaLabelling,par,modelicaLabelling,replaceDict[replace[0]][parDict]) 
                            for parDict in replaceDict[replace[0]] if parDict not in parms]
                        data[-1]=data[-1].rstrip()+')\n'                    

                    if openCloseBracketsCounter!=0:
                        counter+=1
                    if counter>=len(file_data):
                        #print('break')
                        break       
            else:
                #only default parm values in model --> 1) add additional bracket to start, 2) add parm to model and 3) add closing bracket
                #print('only default parm values in model')
                data.append('('+file_data[counter].rstrip()+'\n')
                data+=[" (:PAR :N {}{}{} :V {})\n".format(modelicaLabelling,parDict,modelicaLabelling,replaceDict[replace[0]][parDict]) 
                    for parDict in replaceDict[replace[0]]]
                data[-1]=data[-1].rstrip()+')\n'  
        else:
            data.append(file_data[counter])
        counter+=1
        
    return data

def getSFLinkRefs(sf):
    refs={}
    for i in sf:
        if getCompClass(i)==':INT':
            refs[i[':N']]=i[':V'][1:-1]
            #print(sf)
    return refs
    
def delSFAndConnsAddLinks(plist,sf,sf_ids):
    data=[]
    sf_names_dict={i[0][':N']: {'link_refs':getSFLinkRefs(i),'path':i[0][':SF']} for i in sf}
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
                sf_link=sf_names_dict[sf_name]['link_refs'][i[0][1]]
                path=sf_names_dict[sf_name]['path']
            else:
                model_name=i[0][0]
                model_link=listToBracketsString(i[0][1]) if isinstance(i[0][1],list) else i[0][1]
                sf_name=i[1][0]
                sf_link=sf_names_dict[sf_name]['link_refs'][i[1][1]]
                path=sf_names_dict[sf_name]['path']
            try:
                link_dict[model_name][model_link]={'sf_name': sf_name, 'sf_link': sf_link,'path':path}
            except:
                link_dict[model_name]={model_link:{'sf_name': sf_name, 'sf_link': sf_link,'path':path}}
    #print(link_dict)    
       
    for comp in plist:
        if getCompClass(comp)=='SOURCE-FILE':
            pass
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
                                i[':B']="""(:SYSTEM "sf-macro" "SOURCE-FILE-{}" {})""".format([j['id'] for j in sf_ids if j['sf']==link_dict[getCompName(comp)][binding]['path']][0],link_dict[getCompName(comp)][binding]['sf_link'])
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
                                        try:
                                            new_bindings.append([binding[0],':SYSTEM','"sf-macro"', '"SOURCE-FILE-{}"'.format([j['id'] for j in sf_ids if j['sf']==link_dict[getCompName(comp)][binding_name]['path']][0]),link_dict[getCompName(comp)][binding_name]['sf_link']])
                                        except:
                                            new_bindings.append(binding)
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
                #print('****')
                for i in comp[':CONNS']:
                    #print(i)
                    #print(i[1][0])
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

def replaceKeywordsInPList(plist,replaceDict):
    data=[]
    #print('--------replace keywords-------------')
    #print(replaceDict)
    for comp in plist:
        comp_name=getCompName(comp)[1:-1]
        if comp_name in replaceDict:
            #print('---replace---')
            model_type=getCompTemplate(comp)
            model_language=modelLanguage(model_type)
            pre_suffix='|' if model_language=='MODELICA' else ''
            if getCompClass(comp)=='SOURCE-FILE':
                #print('--SF--')
                comp[0][':DOCUMENT-PATH']='"{}"'.format(replaceDict[comp_name][':SOURCE-FILE'])
                comp[0][':SF']='"{}"'.format(replaceDict[comp_name][':SOURCE-FILE'])
                data.append(comp)
            else:
                new_comp=[]     
                parms=[]
                #print(comp_name)
                #print(comp)
                #print(replaceDict[comp_name])
                for i in comp:
                    i_name=getCompName(i).replace('|','')
                    #print(i_name)
                    if i_name in replaceDict[comp_name]:
                        if isinstance(replaceDict[comp_name][i_name], dict):
                            #print("It's a dictionary!")
                            for key,value in replaceDict[comp_name][i_name].items():
                                i[key]=str(value)
                        else:
                            i[':V']=str(replaceDict[comp_name][i_name])
                        parms.append(i_name)
                        new_comp.append(i)
                    else:
                        new_comp.append(i)
                #print(parms)
                for i in replaceDict[comp_name]:
                    #print(i)
                    if i not in parms:
                        #print('not in parms')
                        new_comp.append({':C':':PAR', ':N': pre_suffix+i+pre_suffix,':V': str(replaceDict[comp_name][i])})
                data.append(new_comp)
        else:
            data.append(comp)
    #print('---finish replace kewords----')    
    return data
    
def copyFileReplaceStr(src_file,dst_dir,dst_file,list_oldString,list_newString,replaceDict=False,doubleQuotes=True):
    """Copy a file within given directory and replace strings in a list"""
    quotes='"' if doubleQuotes else ''
    if checkFilePathExists(False,src_file):
        filedata=[]
        with open(src_file, "r") as myfile:
            for line in myfile:
                for oldString,newString in zip(list_oldString,list_newString):
                    line=line.replace(quotes+oldString+quotes,quotes+newString+quotes)                
                    filedata.append(line)  
        extension=src_file.split('.')[-1]
        if replaceDict and extension == 'idm':
            filedata=replaceKeywordsInFiledata(filedata,replaceDict)
        writeToFileFromList(filedata,dst_dir,dst_file)

def moveFileReplaceStr(src_file,dst_dir,dst_file,list_oldString,list_newString,replaceDict=False):
    """move a file within given directory and replace strings in a list"""
    copyFileReplaceStr(src_file,dst_dir,dst_file,list_oldString,list_newString,replaceDict=replaceDict)
    if os.path.exists(src_file):
        os.remove(src_file)

def getResourcesFromFileDataList(file_data):
    i=0
    ressources=[]
    while i < len(file_data):
        if "(SCHEDULE-DATA :N" in file_data[i] and file_data[i] not in ressources: #or ":T PLINSEGM" in file_data[i]: #todo check for more ressources 
            #print('ressource exists: '+file_data[i])
            ressource=[file_data[i].replace('\n','')]
            openCloseBracktesCounter=file_data[i].count('(')-file_data[i].count(')')
            i+=1
            while openCloseBracktesCounter>0:
                openCloseBracktesCounter+=file_data[i].count('(')-file_data[i].count(')')
                ressource.append(file_data[i].replace('\n',''))
                i+=1
                if i>=len(file_data):
                    break
            ressources.append('\n'.join(ressource))
        else:
            i+=1
    return ressources
    
def copyNestedSupervisoryMacros(source_dir,target_dir):
    if os.path.exists(source_dir):
        for root, dirs, files in os.walk(source_dir):
            for file in files:
                if file.endswith('.idm') or file.endswith('.idc'):
                    #print('---------macro exists: '+file)
                    subfolder=os.path.dirname(os.path.join(root, file)).replace('/','\\').split('Supervisory_control\\Supervisory_control')[1]
                    path=target_dir+'\\'+'Supervisory_control'+subfolder
                    createSubDir(path)
                    copyFile(os.path.join(root, file),path,path+'\\'+file)
        
    

            