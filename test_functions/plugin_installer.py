from datetime import datetime
import shutil
import os
from pathlib import Path

installation_dir='\\'.join(str(Path(__file__).resolve()).split('\\')[:-2])+'\\plugin\\'
print(installation_dir)

plugins_dir = QgsApplication.qgisSettingsDirPath().replace('/','\\') + "python\\plugins\\"
print(plugins_dir)

plugin_dir = QgsApplication.qgisSettingsDirPath().replace('/','\\') + "python\\plugins\\districts\\"
print(plugin_dir)

def rmtree_long_path(dir):
    if os.path.exists(dir) and os.path.isdir(dir):
        if os.name == 'nt':
            dir='\\\\?\\'+dir
        shutil.rmtree(dir)

def copy_tree_filter_extensions_and_folders(src, dst, signals=None, exclude_extensions=None, exclude_folders=None):
    # Set defaults
    if exclude_extensions is None:
        exclude_extensions = []
    if exclude_folders is None:
        exclude_folders = []
    if signals is None:
        signals = False

    # Normalize to lowercase
    exclude_extensions = [ext.lower() for ext in exclude_extensions]
    exclude_folders = [folder.lower() for folder in exclude_folders]

    for root, dirs, files in os.walk(src):
        # Remove excluded directories from traversal
        dirs[:] = [d for d in dirs if d.lower() not in exclude_folders]

        # Compute destination directory path
        relative_dir = os.path.relpath(root, src)
        destination_dir = os.path.join(dst, relative_dir)

        try:
            # Ensure directory exists (this is what enables empty folder copying)
            os.makedirs(destination_dir, exist_ok=True)
        except Exception as e:
            if signals:
                signals.error.emit(f"Failed to create directory: {destination_dir} | {e}")
            continue

        # Filter files by extension
        files_to_copy = [
            f for f in files
            if not any(f.lower().endswith(ext) for ext in exclude_extensions)
        ]

        for file in files_to_copy:
            full_file_path = os.path.join(root, file)
            destination_file_path = os.path.join(destination_dir, file)

            try:
                # Windows long path handling
                if os.name == 'nt':
                    if not destination_file_path.startswith('\\\\?\\'):
                        destination_file_path = '\\\\?\\' + os.path.abspath(destination_file_path)
                    if not full_file_path.startswith('\\\\?\\'):
                        full_file_path = '\\\\?\\' + os.path.abspath(full_file_path)

                shutil.copy2(full_file_path, destination_file_path)

            except Exception as e:
                if signals:
                    signals.error.emit(f"Failed to copy file: {destination_file_path} | {e}")

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


#remove old files
rmtree_long_path(plugin_dir)

#copy files
print('------'+installation_dir+'districts------')
copy_tree_filter_extensions_and_folders(installation_dir+'districts',plugin_dir)

#check QGIS.ini
qgis_ini_dir = os.path.join(QgsApplication.qgisSettingsDirPath().replace('/','\\'),'QGIS')
for file in os.listdir(qgis_ini_dir):
    data=''
    with open(os.path.join(qgis_ini_dir,file), "r") as myfile:
        for line in myfile:
            data+=line
    data=data.replace('districts=true','').replace('districts=false','').replace('[PythonPlugins]','[PythonPlugins]\ndistricts=true')
    with open(os.path.join(qgis_ini_dir,file),'w') as myfile:
        myfile.write(data) 
    
print('installation finished')
