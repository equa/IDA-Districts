import os
import shutil
from plugins.utility_functions.utility import *
from plugins.utility_functions.ida_components import *
from qgis.core import Qgis, QgsMessageLog


def getQGISPluginsDir(plugin_dir):
    """ get directory of QGIS plugins"""
    dir=plugin_dir.replace("/","\\")
    dir="\\".join(i for i in dir.split("\\")[0:-1])
    return dir

def getProjectHandlingDir(plugin_dir):
    """ get directory of project handling plugin"""
    dir=getQGISPluginsDir(plugin_dir)
    dir+='\\ida_districts_project_handling'
    return dir
    
def getDataCenterDir(plugin_dir):
    """ get directory of data center plugin"""
    dir=getQGISPluginsDir(plugin_dir)
    dir+='\\ida_districts_data_center'
    return dir
    
def getModellingDir(plugin_dir):
    """ get directory of modelling and simulation plugin"""
    dir=getQGISPluginsDir(plugin_dir)
    dir+='\\ida_districts_modeling_simulation'
    return dir

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

    
def getDBConnectionData(plugin_dir):
    """ load the DB connection data from file dbSettings.txt"""
    print('get DB settings')
    dbSettings=""
    dir=getProjectHandlingDir(plugin_dir)
    file="{}\\dbSettings.txt".format(dir)
    if os.path.exists(file):
        with open(file, "r") as myfile:   
            for line in myfile:        
                dbSettings+=line
    print(strToDict(dbSettings))
    return strToDict(dbSettings)

def loadProjectConfig(plugin_dir,db_name):
    """ load project config data from configProject.txt in project handling"""
    config=""
    if db_name:
        dir=getProjectHandlingDir(plugin_dir)
        config_f="{}\\{}\\configProject.txt".format(dir,db_name)
        print(config_f)
        if os.path.exists(config_f):
            print(config_f)
            with open(config_f, "r") as myfile:   
                for line in myfile:        
                    config+=line
        print(config)
        config=strToDict(config)
    else:
        print('No project name')
    return config
    
def writeProjectConfig(plugin_dir,db_name,configProject):
    """ write project config data from configProject.txt in project handling"""
    dir=getProjectHandlingDir(plugin_dir)
    config_path=config_f="{}\\{}".format(dir,db_name)
    config_f=config_path+"\\configProject.txt"
    if os.path.exists(config_path):
        with open(config_f, "w") as myfile:   
            myfile.write(str(configProject))
            
def writeRequestedOutputs(plugin_dir,dictDB,requestedOutputs):
    """Writes the requested outputs to file in the modelling & simulation plugin -->  network_models  --> projet name --> version name"""
    dir=plugin_dir+"\\network_models\\"
    createDir(dir,dictDB['projectName'])
    dir+=dictDB['projectName']+"\\"
    createDir(dir,dictDB['versionName'])
    file=dir+dictDB['versionName']+"\\requestedOutputs.txt"
    with open(file, "w") as myfile:   
        myfile.write(str(requestedOutputs))
        
def writeSimulatedOutputs(plugin_dir,dictDB,simulatedOutputs):
    """Writes the simulated outputs to file in the modelling & simulation plugin -->  network_models  --> projet name --> version name"""
    dir=plugin_dir+"\\network_models\\"
    createDir(dir,dictDB['projectName'])
    dir+=dictDB['projectName']+"\\"
    createDir(dir,dictDB['versionName'])
    file=dir+dictDB['versionName']+"\\simulatedOutputs.txt"
    with open(file, "w") as myfile:   
        myfile.write(str(simulatedOutputs))
        
def writeInvokedOutputs(plugin_dir,dictDB,invokedOutputs):
    """Writes the invoked outputs to file in the modelling & simulation plugin -->  network_models  --> projet name --> version name"""
    dir=plugin_dir+"\\network_models\\"
    createDir(dir,dictDB['projectName'])
    dir+=dictDB['projectName']+"\\"
    createDir(dir,dictDB['versionName'])
    file=dir+dictDB['versionName']+"\\invokedOutputs.txt"
    with open(file, "w") as myfile:   
        myfile.write(str(invokedOutputs))
            
def loadRequestedOutputs(plugin_dir,dictDB):
    """ load requested outputs from requestedOutputs.txt in modelling & simulation plugin -->  network_models  --> projet name --> version name"""
    requestedOutputs=""
    if dictDB['projectName']:
        dir=plugin_dir+"\\network_models\\"+dictDB['projectName']+"\\"+dictDB['versionName']
        file="{}\\requestedOutputs.txt".format(dir)
        if os.path.exists(file):
            print(file)
            with open(file, "r") as myfile:   
                for line in myfile:        
                    requestedOutputs+=line
        else:
            #load from template in data center plugin if file does not exists
            file_template=getDataCenterDir(plugin_dir)+"\\config\\requestedOutputs_template.txt"
            if os.path.exists(file_template):
                print(file_template)
                with open(file_template, "r") as myfile:   
                    for line in myfile:        
                        requestedOutputs+=line
        print(requestedOutputs)
        requestedOutputs=strToDict(requestedOutputs)
    else:
        print('No project name')
    return requestedOutputs
    
def loadSimulatedOutputs(plugin_dir,dictDB):
    """ load simulated outputs from simulatedOutputs.txt in modelling & simulation plugin -->  network_models  --> projet name --> version name"""
    simulatedOutputs=""
    if dictDB['projectName']:
        dir=plugin_dir+"\\network_models\\"+dictDB['projectName']+"\\"+dictDB['versionName']
        file="{}\\simulatedOutputs.txt".format(dir)
        if os.path.exists(file):
            print(file)
            with open(file, "r") as myfile:   
                for line in myfile:        
                    simulatedOutputs+=line
        else:
            return False
        print(simulatedOutputs)
        simulatedOutputs=strToDict(simulatedOutputs)
    else:
        print('No project name')
    return simulatedOutputs
    
def loadInvokedOutputs(plugin_dir,dictDB):
    """ load invoked outputs from invokedOutputs.txt in modelling & simulation plugin -->  network_models  --> projet name --> version name"""
    invokedOutputs=""
    if dictDB['projectName']:
        dir=plugin_dir+"\\network_models\\"+dictDB['projectName']+"\\"+dictDB['versionName']
        file="{}\\invokedOutputs.txt".format(dir)
        if os.path.exists(file):
            print(file)
            with open(file, "r") as myfile:   
                for line in myfile:        
                    invokedOutputs+=line
        else:
            return {'dhc_customers': {}, 'dhc_lines': {}, 'dhc_energy_plants': {}}
        invokedOutputs=eval(invokedOutputs)
        print(invokedOutputs)
    else:
        print('No project name')
    return invokedOutputs
    
def writeModellingSettings(plugin_dir,dictDB,modellingSettings):
    """Writes the modelling settings to file in the modelling & simulation plugin -->  network_models  --> projet name --> version name"""   
    dir=plugin_dir+"\\network_models\\"
    createDir(dir,dictDB['projectName'])
    dir+=dictDB['projectName']+"\\"
    createDir(dir,dictDB['versionName'])
    file=dir+dictDB['versionName']+"\\modellingSettings.txt"
    with open(file, "w") as myfile:   
        myfile.write(str(modellingSettings))
        
def writeNetworkSimData(plugin_dir,dictDB,modellingSettings):
    """Writes the network simulation settings to file in the modelling & simulation plugin -->  network_models  --> projet name --> version name"""   
    dir=plugin_dir+"\\network_models\\"
    createDir(dir,dictDB['projectName'])
    dir+=dictDB['projectName']+"\\"
    createDir(dir,dictDB['versionName'])
    file=dir+dictDB['versionName']+"\\networkSimData.txt"
    with open(file, "w") as myfile:   
        myfile.write(str(modellingSettings))
            
def loadModellingSettings(plugin_dir,dictDB):
    """ load modelling settings from modellingSettings.txt in modelling & simulation plugin -->  network_models  --> projet name --> version name"""
    modellingSettings=""
    if dictDB['projectName']:
        dir=plugin_dir+"\\network_models\\"+dictDB['projectName']+"\\"+dictDB['versionName']
        file="{}\\modellingSettings.txt".format(dir)
        if os.path.exists(file):
            print(file)
            with open(file, "r") as myfile:   
                for line in myfile:        
                    modellingSettings+=line
        else:
            #load from template in data center plugin if file does not exists
            file_template=getDataCenterDir(plugin_dir)+"\\config\\modellingSettings_template.txt"
            if os.path.exists(file_template):
                print(file_template)
                with open(file_template, "r") as myfile:   
                    for line in myfile:        
                        modellingSettings+=line
        print(modellingSettings)
        modellingSettings=strToDict(modellingSettings)
    else:
        print('No project name')
    return modellingSettings
    
def loadNetworkSimData(plugin_dir,dictDB):
    """ load modelling settings from modellingSettings.txt in modelling & simulation plugin -->  network_models  --> projet name --> version name"""
    networkSimData=""
    if dictDB['projectName']:
        dir=plugin_dir+"\\network_models\\"+dictDB['projectName']+"\\"+dictDB['versionName']
        file="{}\\networkSimData.txt".format(dir)
        if os.path.exists(file):
            print(file)
            with open(file, "r") as myfile:   
                for line in myfile:        
                    networkSimData+=line
        else:
            #load from template in data center plugin if file does not exists
            file_template=getDataCenterDir(plugin_dir)+"\\config\\networkSimData_template.txt"
            if os.path.exists(file_template):
                print(file_template)
                with open(file_template, "r") as myfile:   
                    for line in myfile:        
                        networkSimData+=line
        print(networkSimData)
        networkSimData=strToDict(networkSimData)
    else:
        print('No project name')
    return networkSimData
            
def writeDBSettings(plugin_dir,dictDB):
    """ write db settings to file dbSettings.txt in project handling."""
    dir=getProjectHandlingDir(plugin_dir)
    file=dir+"\\dbSettings.txt"
    if os.path.exists(dir):
        with open(file, "w") as myfile:   
            myfile.write(str(dictDB))
        
def writeIDADistrictsConfig(plugin_dir,configIDADistricts):
    """ write project config data from configProject.txt in project handling"""
    dir=getProjectHandlingDir(plugin_dir)
    config_f="{}\\configIDADistricts.txt".format(dir)
    if os.path.exists(config_f):
        if checkDirExists("IDA Path",configIDADistricts['path_ice']) and checkDirExists("PostgreSQL Path",configIDADistricts['path_postgresql']):
            if configIDADistricts['path_ice'][-1]!="\\":
                configIDADistricts['path_ice']=configIDADistricts['path_ice']+"\\"
            if configIDADistricts['path_postgresql'][-1]!="\\":
                configIDADistricts['path_postgresql']=configIDADistricts['path_postgresql']+"\\"
            with open(config_f, "w") as myfile:   
                myfile.write(str(configIDADistricts).replace('\\\\','\\'))
            return True
        else:
            return False
        
def loadIDADistrictsConfig(plugin_dir):
    """ load IDA Districts config data from configIDADistrict.txt in project handling"""
    project_dir=getProjectHandlingDir(plugin_dir)
    config_f="{}\\configIDADistricts.txt".format(project_dir)
    config=""
    if os.path.exists(config_f):
        with open(config_f, "r") as myfile:   
            for line in myfile:        
                config+=line
    config=strToDict(config)
    print(config)
    return config
    
def createDir(dir,name):
    """ makes a new folder if it does not exists"""
    if os.path.exists(dir):
        dir = os.path.join(dir,name)
        if not os.path.exists(dir):
            os.mkdir(dir)  

def getDirFiles(dir,extension):
    return [f for f in os.listdir(dir) if os.path.isfile(os.path.join(dir, f)) and os.path.join(dir, f).endswith(extension)]

def getNetworkFileSubmodels(dir):
    return [f.split('_')[1].split('.')[0] for f in getDirFiles(dir,'.idm')]

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
                
def writePropertyListIDMToFile(plist,dir,file):
    print (dir)
    if os.path.exists(dir):
        print (file)
        with open(file,'w') as myfile:
            myfile.write(';IDA '+plist[0][':APP'].split(':VER ')[1].split(')')[0]+' Data UTF-8\n')
            for comp in plist:
                #print(comp)
                myfile.write(pListToCompString(comp,0)+'\n')
 
def writePropertyListIDCToFile(plist,dir,file):
    print (dir)
    if os.path.exists(dir):
        print (file)
        with open(file,'w') as myfile:
            myfile.write(';IDA 5.09001 Form UTF-8\n')
            for comp in plist:
                myfile.write(pListToCompString(comp,0)+'\n')
                
def readFileToString(file):
    data=''
    i=0
    if os.path.exists(file):
        with open(file, "r") as myfile:
            for line in myfile:
                if i!=0:
                    data+=line
                i+=1
    return data
    
def writeToFile(data,dir,file):
    """ write data to file in dir"""
    print (dir)
    if os.path.exists(dir):
        print (file)
        with open(file,'w') as myfile:
            myfile.write(data) 
            
def writeToFileFromList(data,dir,file):
    """ write data to file in dir"""
    print (dir)
    if os.path.exists(dir):
        print (file)
        with open(file,'w') as myfile:
            for line in data:
                myfile.write(line) 
            
def appendToFile(data,dir,file):
    """ write data to file in dir"""
    print (dir)
    if os.path.exists(dir):
        print (file)
        with open(file,'a') as myfile:
            myfile.write(data) 
            
def checkFilePathExists(title,file_path):
    if not title:
        title="ERROR"
    if os.path.exists(file_path):
        return True
    else:
        iface.messageBar().pushMessage(title, "File not found: {}!".format(file_path), level=Qgis.Critical)
        return False
 
def checkDirExists(title,dir):
    if not title:
        title="ERROR"
    if os.path.exists(dir):
        return True
    else:
        iface.messageBar().pushMessage(title, "Directory not found: {}!".format(dir), level=Qgis.Critical)
        return False
        
def copyFile(src_file,dst_dir,dst_file):
    """Copy a file within given directory"""
    if checkFilePathExists(False,src_file):
        if checkDirExists(False,dst_dir):
            shutil.copy(src_file,dst_file)
    
def replaceKeywordsInFiledata(file_data,replaceDict):
    data=[]
    counter=0
    print('--------replace keywords-------------')
    print(replaceDict)
    while counter < len(file_data):
        replace=[key for key in replaceDict if ':N "'+key+'"' in file_data[counter]]
        if replace:
            print('Replace model parm: '+replace[0])
            openCloseBracketsCounter=countOpenCloseBrackets(file_data[counter])
            print('openCloseBracketsCounter='+str(openCloseBracketsCounter))
            model_type=getModelType(file_data[counter])
            print(model_type)
            model_language=modelLanguage(model_type)
            modelicaLabelling='|' if model_language=='MODELICA' else ''
            print(model_language)
            if openCloseBracketsCounter>0:
                print(file_data[counter])
                parms=[]
                if ':T SOURCE-FILE' in file_data[counter] and ':SOURCE-FILE' in [par for parDict in replaceDict[replace[0]] for par in parDict]:
                    path=[i[j] for i in replaceDict[replace[0]] for j in i if j==':SOURCE-FILE'][0]
                    data.append("""((SOURCE-FILE :DOCUMENT-PATH "{}" :SF "{}" :N "{}" :T SOURCE-FILE :COL T){}\n""".format(path,path,replace[0],')' if openCloseBracketsCounter==0 else ''))
                    parms.append(':SOURCE-FILE')
                else:
                    data.append(file_data[counter])
                counter+=1
                while openCloseBracketsCounter>0:
                    openCloseBracketsCounter+=countOpenCloseBrackets(file_data[counter])
                    if "(:PAR :N " in file_data[counter]:
                        par_name=getParName(file_data[counter],model_language)
                        print(par_name)

                        if par_name in [par for parDict in replaceDict[replace[0]] for par in parDict]:
                            print('replace parm')
                            print(' (:PAR :N {}{}{} :V {})\n'.format(modelicaLabelling,par_name,modelicaLabelling,[parDict[par] for parDict in replaceDict[replace[0]] for par in parDict if par==par_name][0]))
                            data.append(' (:PAR :N {}{}{} :V {})\n'.format(modelicaLabelling,par_name,modelicaLabelling,[parDict[par] for parDict in replaceDict[replace[0]] for par in parDict if par==par_name][0]))
                            parms.append(par_name)
                            exchangeParmValue=True
                        else:
                            data.append(file_data[counter])
                            exchangeParmValue=False
                    else:
                        data.append(file_data[counter])
                        exchangeParmValue=False
                    if openCloseBracketsCounter==0:
                        print('counter = 0')
                        if not exchangeParmValue:
                            data[-1]=data[-1].rstrip()[:-1]+"\n"
                        
                        data+=[" (:PAR :N {}{}{} :V {})\n".format(modelicaLabelling,par,modelicaLabelling,parDict[par]) 
                            for parDict in replaceDict[replace[0]] for par in parDict if par not in parms]
                        data[-1]=data[-1].rstrip()+')\n'                    

                    if openCloseBracketsCounter!=0:
                        counter+=1
                    if counter>=len(file_data):
                        print('break')
                        break       
            else:
                #only default parm values in model --> 1) add additional bracket to start, 2) add parm to model and 3) add closing bracket
                print('only default parm values in model')
                data.append('('+file_data[counter].rstrip()+'\n')
                data+=[" (:PAR :N {}{}{} :V {})\n".format(modelicaLabelling,par,modelicaLabelling,parDict[par]) 
                    for parDict in replaceDict[replace[0]] for par in parDict]
                data[-1]=data[-1].rstrip()+')\n'  
        else:
            data.append(file_data[counter])
        counter+=1
        
    return data
            
def copyFileReplaceStr(src_file,dst_dir,dst_file,list_oldString,list_newString,replaceDict=False):
    """Copy a file within given directory and replace strings in a list"""
    if checkFilePathExists(False,src_file):
        filedata=[]
        with open(src_file, "r") as myfile:
            for line in myfile:
                for oldString,newString in zip(list_oldString,list_newString):
                    line=line.replace('"'+oldString+'"','"'+newString+'"')                
                    filedata.append(line)  
        extension=src_file.split('.')[-1]
        if replaceDict and extension == 'idm':
            filedata=replaceKeywordsInFiledata(filedata,replaceDict)
        writeToFileFromList(filedata,dst_dir,dst_file)

def writeTempTimeseries(dir,id,name,cur):
    createDir(dir,'timeseries')
    dir+='\\timeseries'
    sql="""SELECT time_h, round(temp,3) FROM public.temp WHERE temp_id={} ORDER BY time_h;""".format(id)
    cur.execute(sql)      
    
    data="# Time T\n"
    for line in cur.fetchall():
        data+= str(line[0])+ ' '+ str(line[1]) +"\n"
    file=dir+"\\"+name+'.prn'
    writeToFile(data,dir,file)
    return file.replace('/','\\').replace('\\','\\\\')
    
def getResourcesFromFileDataList(file_data):
    i=0
    ressources=[]
    while i < len(file_data):
        if "(SCHEDULE-DATA :N" in file_data[i] and file_data[i] not in ressources: #or ":T PLINSEGM" in file_data[i]: #todo check for more ressources 
            print('ressource exists: '+file_data[i])
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
                    print('---------macro exists: '+file)
                    subfolder=os.path.dirname(os.path.join(root, file)).replace('/','\\').split('Supervisory_control\\Supervisory_control')[1]
                    path=target_dir+'\\'+'Supervisory_control'+subfolder
                    createSubDir(path)
                    copyFile(os.path.join(root, file),path,path+'\\'+file)
        
    

            