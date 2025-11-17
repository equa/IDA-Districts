from datetime import datetime
import shutil
import os
from pathlib import Path

installation_dir='\\'.join(str(Path(__file__).resolve()).split('\\')[:-2])+'\\plugins\\'
print(installation_dir)

plugin_dir = QgsApplication.qgisSettingsDirPath().replace('/','\\') + "python\\plugins\\"
print(plugin_dir)

def rmtree_long_path(dir):
    if os.path.exists(dir) and os.path.isdir(dir):
        if os.name == 'nt':
            dir='\\\\?\\'+dir
        shutil.rmtree(dir)

def copy_tree_filter_extensions_and_folders(src, dst, signals=None,exclude_extensions=None, exclude_folders=None):
    # Set default values if no extensions or folders are provided
    if exclude_extensions is None:
        exclude_extensions = []
    if exclude_folders is None:
        exclude_folders = []
    if exclude_folders is None:
        signals = False

    # Ensure the extensions and folder names are in lowercase for case-insensitive comparison
    exclude_extensions = [ext.lower() for ext in exclude_extensions]
    exclude_folders = [folder.lower() for folder in exclude_folders]

    # Walk through the source directory
    for root, dirs, files in os.walk(src):
        # Filter out files with the specified extensions
        files_to_copy = [f for f in files if not any(f.lower().endswith(ext) for ext in exclude_extensions)]
        
        # Copy each file to the destination, skipping excluded extensions
        for file in files_to_copy:
            full_file_path = os.path.join(root, file)
            relative_path = os.path.relpath(full_file_path, src)
            destination_file_path = os.path.join(dst, relative_path)
            try:
                if os.name == 'nt':  # Windows OS
                    destination_file_path = '\\\\?\\' + os.path.abspath(destination_file_path)
                if os.name == 'nt':  # Windows OS
                    full_file_path = '\\\\?\\' + os.path.abspath(full_file_path)
                # Make sure the destination directory exists
                os.makedirs(os.path.dirname(destination_file_path), exist_ok=True)
                
                # Copy the file to the destination
                shutil.copy2(full_file_path, destination_file_path)
            except:
                if signals:
                    signals.error.emit("Failed to copy file (file path probably to long):"+destination_file_path)
        
        # Prevent os.walk from traversing excluded directories
        for dir_name in dirs[:]:
            if dir_name.lower() in exclude_folders:
                dirs.remove(dir_name)  # Remove directory from traversal list

def find_folders_not_in_list(directory, name_list):
    # List to store folders not in name_list
    folders_not_in_list = []
    if os.path.isdir(directory):
        # Loop through all the items in the directory
        for item in os.listdir(directory):
            # Construct the full path of the item
            item_path = os.path.join(directory, item)

            # Check if the item is a directory and if its name is not in name_list
            if os.path.isdir(item_path) and item not in name_list:
                folders_not_in_list.append(item)

    return folders_not_in_list

def strToDict(str):
    str=str.replace('"','').replace("'",'')
    dict={}
    try:
        for i in str[1:-1].split(","):
            entry=i.split(": ")[1].strip()
            if entry == "True" or entry == "False":
                if entry == "True":
                    dict[i.split(": ")[0].strip()]=True
                else:
                    dict[i.split(": ")[0].strip()]=False
            else:
                dict[i.split(": ")[0].strip()]=entry
    except:
        pass
    return dict
    
def loadIDADistrictsConfig(plugin_dir):
    """ load IDA Districts config data from configIDADistrict.txt in project handling"""
    config_f=plugin_dir+"\\ida_ph\\configIDADistricts.txt"
    config=""
    if os.path.exists(config_f):
        with open(config_f, "r") as myfile:   
            for line in myfile:        
                config+=line
    config=strToDict(config)
    return config

def getQGISPluginsDir(plugin_dir):
    """ get directory of QGIS plugins"""
    dir=plugin_dir.replace("/","\\")
    dir="\\".join(i for i in dir.split("\\")[0:-1])
    return dir
    
def getProjectHandlingDir(plugin_dir):
    """ get directory of project handling plugin"""
    dir=getQGISPluginsDir(plugin_dir)
    dir+='\\ida_ph'
    return dir
    
def getDBConnectionData(plugin_dir,filename='dbSettings'):
    """ load the DB connection data from file dbSettings.txt"""
    dbSettings=""
    dir=getProjectHandlingDir(plugin_dir)
    file="{}\\{}.txt".format(dir,filename)
    if os.path.exists(file):
        with open(file, "r") as myfile:   
            for line in myfile:        
                dbSettings+=line
    return strToDict(dbSettings)
    
def copyProjectFolders(dir,plugin_dir,name_list):
    project_folders = find_folders_not_in_list(dir, name_list)
    print(project_folders)
    for folder in project_folders:
        copy_tree_filter_extensions_and_folders(dir+folder,plugin_dir+'\\'+folder)
        
#utility functions
print('------'+installation_dir+'utility_functions------')
rmtree_long_path(plugin_dir+'utility_functions')
copy_tree_filter_extensions_and_folders(installation_dir+'utility_functions',plugin_dir+'utility_functions')

#data center
print('------'+installation_dir+'ida_data------')
dir=plugin_dir+'ida_data\\'
name_list = ['config', 'help', 'Samples','scripts','i18n','__pycache__']
copyProjectFolders(dir,plugin_dir+'dc_temp',name_list)
rmtree_long_path(dir)
copy_tree_filter_extensions_and_folders(installation_dir+'ida_data',dir)
copy_tree_filter_extensions_and_folders(plugin_dir+'dc_temp',dir)
rmtree_long_path(plugin_dir+'dc_temp')

#modelling
print('------'+installation_dir+'ida_mosim------')
dir=plugin_dir+'ida_mosim\\'
copyProjectFolders(dir+'models',plugin_dir+'mosim_temp',[])
rmtree_long_path(dir)
os.makedirs(dir+'models')
copy_tree_filter_extensions_and_folders(installation_dir+'ida_mosim',dir)
copy_tree_filter_extensions_and_folders(plugin_dir+'mosim_temp',dir)
rmtree_long_path(plugin_dir+'mosim_temp')

#preprocessing
print('------'+installation_dir+'ida_pp------')
dir=plugin_dir+'ida_pp\\'
rmtree_long_path(dir)
copy_tree_filter_extensions_and_folders(installation_dir+'ida_pp',dir)

#project handling
print('------'+installation_dir+'ida_ph------')
dir=plugin_dir+'ida_ph\\'
name_list = ['config', 'help', 'Samples','scripts','i18n','__pycache__','templates','icons']
copyProjectFolders(dir,plugin_dir+'pro_temp',name_list)
if os.path.isdir(dir):
    if len(getDBConnectionData(dir))==7:
        shutil.copy2(dir+'dbSettings.txt',plugin_dir+'dbSettings.txt')
    if len(loadIDADistrictsConfig(dir))==9:
        shutil.copy2(dir+'configIDADistricts.txt',plugin_dir+'configIDADistricts.txt')
rmtree_long_path(dir)
copy_tree_filter_extensions_and_folders(installation_dir+'ida_ph',dir)
copy_tree_filter_extensions_and_folders(plugin_dir+'pro_temp',dir)
if os.path.exists(plugin_dir+'dbSettings.txt'):
    shutil.copy2(plugin_dir+'dbSettings.txt',dir+'dbSettings.txt')
    os.remove(plugin_dir+'dbSettings.txt')
if os.path.exists(plugin_dir+'dbSettings_lastLoad.txt'):
    shutil.copy2(plugin_dir+'dbSettings_lastLoad.txt',dir+'dbSettings_lastLoad.txt')
    os.remove(plugin_dir+'dbSettings_lastLoad.txt')
if os.path.exists(plugin_dir+'configIDADistricts.txt'):
    shutil.copy2(plugin_dir+'configIDADistricts.txt',dir+'configIDADistricts.txt')
    os.remove(plugin_dir+'configIDADistricts.txt')
rmtree_long_path(plugin_dir+'pro_temp')

#result visualization
print('------'+installation_dir+'ida_rv------')
dir=plugin_dir+'ida_rv\\'
rmtree_long_path(dir)
copy_tree_filter_extensions_and_folders(installation_dir+'ida_rv',dir)

print('installation finished')
