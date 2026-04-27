from districts.utility_functions.files import *
from districts.utility_functions.db import *
from qgis.core import QgsApplication

from datetime import datetime
import shutil
import subprocess
import os

plugin_dir = QgsApplication.qgisSettingsDirPath() + "python/plugins/districts/"
print(plugin_dir)
current_date = datetime.now().strftime('%Y-%m-%d-%H%M')
target_dir=r'C:\EQUA\Projekte\DistrictEnergySystemModelling\QGIS plugin developement'+'\\'+current_date+'\\'

# Check if the folder exists and delete it
if os.path.exists(target_dir) and os.path.isdir(target_dir):
    shutil.rmtree(target_dir)

#------------plugins--------------
target_plugin_dir=target_dir+'plugin\\districts\\'
print(target_plugin_dir)

def copyMetaFiles(src_dir,trg_dir):
    os.mkdir(trg_dir+'__pycache__')
    for file_name in ['__init__.py','Makefile','metadata.txt','pb_tool.cfg','pylintrc']:
        shutil.copy(src_dir+file_name, trg_dir+file_name)

#districts
shutil.copytree(plugin_dir+'utility_functions',target_plugin_dir+'utility_functions')
shutil.copytree(plugin_dir+'config',target_plugin_dir+'config')
shutil.copytree(plugin_dir+'help',target_plugin_dir+'help')
shutil.copytree(plugin_dir+'samples',target_plugin_dir+'samples')
shutil.copytree(plugin_dir+'scripts',target_plugin_dir+'scripts')
shutil.copytree(plugin_dir+'i18n',target_plugin_dir+'i18n')
shutil.copytree(plugin_dir+'templates',target_plugin_dir+'templates')
shutil.copytree(plugin_dir+'test',target_plugin_dir+'test')
shutil.copytree(plugin_dir+'icons',target_plugin_dir+'icons')
shutil.copytree(plugin_dir+'licenses',target_plugin_dir+'licenses')
shutil.copytree(plugin_dir+'postgreSQL',target_plugin_dir+'postgreSQL')
shutil.copytree(plugin_dir+'climate',target_plugin_dir+'climate')


copyMetaFiles(plugin_dir,target_plugin_dir)

#project
os.mkdir(target_plugin_dir+'projects')

#python 
shutil.copy(plugin_dir+'calibrate_customers.py', target_plugin_dir+'calibrate_customers.py')
shutil.copy(plugin_dir+'cosim.py', target_plugin_dir+'cosim.py')
shutil.copy(plugin_dir+'districts.py', target_plugin_dir+'districts.py')
shutil.copy(plugin_dir+'districts_dialog.py', target_plugin_dir+'districts_dialog.py')
shutil.copy(plugin_dir+'elevation_data.py', target_plugin_dir+'elevation_data.py')
shutil.copy(plugin_dir+'GenerateNetworkTopology.py', target_plugin_dir+'GenerateNetworkTopology.py')
shutil.copy(plugin_dir+'ida_import.py', target_plugin_dir+'ida_import.py')
shutil.copy(plugin_dir+'ida_import_dialog.py', target_plugin_dir+'ida_import_dialog.py')
shutil.copy(plugin_dir+'ida_mosim.py', target_plugin_dir+'ida_mosim.py')
shutil.copy(plugin_dir+'ida_mosim_dialog.py', target_plugin_dir+'ida_mosim_dialog.py')
shutil.copy(plugin_dir+'ida_ph.py', target_plugin_dir+'ida_ph.py')
shutil.copy(plugin_dir+'ida_ph_dialog.py', target_plugin_dir+'ida_ph_dialog.py')
shutil.copy(plugin_dir+'ida_pp.py', target_plugin_dir+'ida_pp.py')
shutil.copy(plugin_dir+'ida_pp_dialog.py', target_plugin_dir+'ida_pp_dialog.py')
shutil.copy(plugin_dir+'ida_resources.py', target_plugin_dir+'ida_resources.py')
shutil.copy(plugin_dir+'ida_resources_dialog.py', target_plugin_dir+'ida_resources_dialog.py')
shutil.copy(plugin_dir+'ida_rv.py', target_plugin_dir+'ida_rv.py')
shutil.copy(plugin_dir+'ida_rv_dialog.py', target_plugin_dir+'ida_rv_dialog.py')
shutil.copy(plugin_dir+'invoke_network.py', target_plugin_dir+'invoke_network.py')
shutil.copy(plugin_dir+'invoke_sensors.py', target_plugin_dir+'invoke_sensors.py')
shutil.copy(plugin_dir+'load_results.py', target_plugin_dir+'load_results.py')
shutil.copy(plugin_dir+'osm.py', target_plugin_dir+'osm.py')
shutil.copy(plugin_dir+'outputs.py', target_plugin_dir+'outputs.py')
shutil.copy(plugin_dir+'path_report.py', target_plugin_dir+'path_report.py')
shutil.copy(plugin_dir+'pipe_sizing.py', target_plugin_dir+'pipe_sizing.py')
shutil.copy(plugin_dir+'PipeLayingAlgorithm.py', target_plugin_dir+'PipeLayingAlgorithm.py')
shutil.copy(plugin_dir+'plugin_upload.py', target_plugin_dir+'plugin_upload.py')
shutil.copy(plugin_dir+'supervisory_control.py', target_plugin_dir+'supervisory_control.py')
shutil.copy(plugin_dir+'svg_label.py', target_plugin_dir+'svg_label.py')
shutil.copy(plugin_dir+'update_boundaries.py', target_plugin_dir+'update_boundaries.py')
shutil.copy(plugin_dir+'update_sensors.py', target_plugin_dir+'update_sensors.py')

#.ui files
shutil.copy(plugin_dir+'network_report.ui', target_plugin_dir+'network_report.ui')
shutil.copy(plugin_dir+'districts_dialog_base.ui', target_plugin_dir+'districts_dialog_base.ui')
shutil.copy(plugin_dir+'districts_settings_dialog.ui', target_plugin_dir+'districts_settings_dialog.ui')
shutil.copy(plugin_dir+'districts_climate_dialog.ui', target_plugin_dir+'districts_climate_dialog.ui')
shutil.copy(plugin_dir+'districts_setLoadAttribute.ui', target_plugin_dir+'districts_setLoadAttribute.ui')



#DB
shutil.copy(plugin_dir+'DB_projectTablesDefault.txt', target_plugin_dir+'DB_projectTablesDefault.txt')
shutil.copy(plugin_dir+'DB_versionTablesDefault.txt', target_plugin_dir+'DB_versionTablesDefault.txt')
shutil.copy(plugin_dir+'DB_versionTablesDefault_data.txt', target_plugin_dir+'DB_versionTablesDefault_data.txt')
shutil.copy(plugin_dir+'SQL_scripts.txt', target_plugin_dir+'SQL_scripts.txt')

#installation
target_install_dir=r'C:\EQUA\Projekte\DistrictEnergySystemModelling\QGIS plugin developement'+'\\'+current_date+'\\installation\\'
print(target_install_dir)
os.mkdir(target_install_dir)
src_dir=QgsApplication.qgisSettingsDirPath() + "python/plugins/test_functions/"
shutil.copy(src_dir+'plugin_installer.py', target_install_dir+'plugin_installer.py')

print('finished')