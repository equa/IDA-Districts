from plugins.utility_functions.files import *
from plugins.utility_functions.db import *
from datetime import datetime
import shutil
import subprocess
import os

plugin_dir="""C:\\Users\\Peter\\AppData\\Roaming\\QGIS\\QGIS3\\profiles\\default\\python\\plugins\\"""

current_date = datetime.now().strftime('%Y-%m-%d-%H%M')
target_dir=r'C:\EQUA\Projekte\DistrictEnergySystemModelling\QGIS plugin developement'+'\\'+current_date+'\\'
new_version ='5.18002' 
# Check if the folder exists and delete it
if os.path.exists(target_dir) and os.path.isdir(target_dir):
    shutil.rmtree(target_dir)

#------------plugins--------------
target_plugin_dir=target_dir+'plugins\\'
#print(target_plugin_dir)

def copyMetaFiles(src_dir,trg_dir):
    os.mkdir(trg_dir+'__pycache__')
    for file_name in ['__init__.py','Makefile','metadata.txt','pb_tool.cfg','pylintrc']:
        shutil.copy(src_dir+file_name, trg_dir+file_name)

def replace_text_in_file(file_path):
    try:
        with open(file_path, 'r', encoding='utf-8') as file:
            content = file.read()
        new_content = content.replace(";IDA 5.18002", ";IDA 5.11").replace(":VER 5.18002", ":VER 5.11")
        if new_content != content:
            with open(file_path, 'w', encoding='utf-8') as file:
                file.write(new_content)
            #print(f"Updated: {file_path}")
    except Exception as e:
        pass
        #print(f"Error processing {file_path}: {e}")

def process_folder(folder_path):
    for root, dirs, files in os.walk(folder_path):
        for filename in files:
            if filename.endswith('.idc') or filename.endswith('.idm'):
                file_path = os.path.join(root, filename)
                replace_text_in_file(file_path)
        
    
#utility functions
shutil.copytree(plugin_dir+'utility_functions',target_plugin_dir+'utility_functions')

#data center
src_dir=plugin_dir+'ida_data\\'
trg_dir=target_plugin_dir+'ida_data\\'
os.mkdir(trg_dir)
shutil.copytree(src_dir+'config',trg_dir+'config')
shutil.copytree(src_dir+'help',trg_dir+'help')
shutil.copytree(src_dir+'Samples',trg_dir+'Samples')
shutil.copytree(src_dir+'scripts',trg_dir+'scripts')
shutil.copytree(src_dir+'i18n',trg_dir+'i18n')
shutil.copy(src_dir+'icon-data-center.png', trg_dir+'icon-data-center.png')
shutil.copy(src_dir+'ida_data.py', trg_dir+'ida_data.py')
shutil.copy(src_dir+'ida_data_dialog.py', trg_dir+'ida_data_dialog.py')
shutil.copy(src_dir+'update_boundaries.py', trg_dir+'update_boundaries.py')
copyMetaFiles(src_dir,trg_dir)

#modelling
src_dir=plugin_dir+'\ida_mosim\\'
trg_dir=target_plugin_dir+'\ida_mosim\\'
os.mkdir(trg_dir)
os.mkdir(trg_dir+'models')
shutil.copytree(src_dir+'help',trg_dir+'help')
shutil.copytree(src_dir+'scripts',trg_dir+'scripts')
shutil.copytree(src_dir+'i18n',trg_dir+'i18n')
shutil.copytree(src_dir+'graphics',trg_dir+'graphics')
shutil.copy(src_dir+'icon-mo-sim.png', trg_dir+'icon-mo-sim.png')
shutil.copy(src_dir+'calibrate_customers.py', trg_dir+'calibrate_customers.py')
shutil.copy(src_dir+'calibrate_features.py', trg_dir+'calibrate_features.py')
shutil.copy(src_dir+'cosim.py', trg_dir+'cosim.py')
shutil.copy(src_dir+'ida_mosim.py', trg_dir+'ida_mosim.py')
shutil.copy(src_dir+'ida_mosim_dialog.py', trg_dir+'ida_mosim_dialog.py')
shutil.copy(src_dir+'invoke.py', trg_dir+'invoke.py')
shutil.copy(src_dir+'invoke_network.py', trg_dir+'invoke_network.py')
shutil.copy(src_dir+'outputs.py', trg_dir+'outputs.py')
shutil.copy(src_dir+'invoke_sensors.py', trg_dir+'invoke_sensors.py')
shutil.copy(src_dir+'load_results.py', trg_dir+'load_results.py')
shutil.copy(src_dir+'supervisory_control.py', trg_dir+'supervisory_control.py')
shutil.copy(src_dir+'update_sensors.py', trg_dir+'update_sensors.py')
copyMetaFiles(src_dir,trg_dir)


#preprocessing
src_dir=plugin_dir+'ida_pp\\'
trg_dir=target_plugin_dir+'ida_pp\\'
os.mkdir(trg_dir)
shutil.copytree(src_dir+'help',trg_dir+'help')
shutil.copytree(src_dir+'scripts',trg_dir+'scripts')
shutil.copytree(src_dir+'i18n',trg_dir+'i18n')
shutil.copy(src_dir+'icon-pre-processing.png', trg_dir+'icon-pre-processing.png')
shutil.copy(src_dir+'elevation_data.py', trg_dir+'elevation_data.py')
shutil.copy(src_dir+'GenerateNetworkTopology.py', trg_dir+'GenerateNetworkTopology.py')
shutil.copy(src_dir+'ida_pp.py', trg_dir+'ida_pp.py')
shutil.copy(src_dir+'ida_pp_dialog.py', trg_dir+'ida_pp_dialog.py')
shutil.copy(src_dir+'osm.py', trg_dir+'osm.py')
shutil.copy(src_dir+'pipe_sizing.py', trg_dir+'pipe_sizing.py')
shutil.copy(src_dir+'PipeLayingAlgorithm.py', trg_dir+'PipeLayingAlgorithm.py')
copyMetaFiles(src_dir,trg_dir)

#project handling
#print('project plugin')
src_dir=plugin_dir+'ida_ph\\'
trg_dir=target_plugin_dir+'ida_ph\\'
os.mkdir(trg_dir)
shutil.copytree(src_dir+'help',trg_dir+'help')
shutil.copytree(src_dir+'scripts',trg_dir+'scripts')
shutil.copytree(src_dir+'i18n',trg_dir+'i18n')
shutil.copytree(src_dir+'icons',trg_dir+'icons')
os.mkdir(trg_dir+'templates')
for template in ['heating_network.ida','empty_project.ida','db_default_values.ida','co-sim_buildings_with_heating_network.ida']:
    filename=src_dir+'templates\\'+template
    dir=src_dir+'templates\\'+template.split('.')[0]
    if not os.path.exists(dir):
        cmd="""\"{}bin\\7za.exe" x "{}" -o"{}\"""".format(loadIDADistrictsConfig(plugin_dir)['path_ice'],filename,dir)
        #print(cmd)
        subprocess.call(cmd, shell=True)
    process_folder(dir)
    
    cmd="""\"{}bin\\7za.exe" a -t7z -r "{}_temp.ida" "{}/*.*\"""".format(loadIDADistrictsConfig(plugin_dir)['path_ice'],dir,dir)
    #print(cmd)
    subprocess.call(cmd, shell=True) 
    
    shutil.copy(src_dir+'templates\\'+template.split('.')[0]+'_temp.ida', trg_dir+'templates\\'+template)
    shutil.rmtree( '\\\\?\\'+dir if os.name == 'nt' else dir) 
    os.remove(src_dir+'templates\\'+template.split('.')[0]+'_temp.ida')

#shutil.copytree(src_dir+'templates',trg_dir+'templates')
shutil.copy(src_dir+'configIDADistricts.txt', trg_dir+'configIDADistricts.txt')
shutil.copy(src_dir+'DB_projectTablesDefault.txt', trg_dir+'DB_projectTablesDefault.txt')
shutil.copy(src_dir+'DB_projectTablesDefault_data.txt', trg_dir+'DB_projectTablesDefault_data.txt')
shutil.copy(src_dir+'DB_versionTablesDefault.txt', trg_dir+'DB_versionTablesDefault.txt')
shutil.copy(src_dir+'DB_versionTablesDefault_data.txt', trg_dir+'DB_versionTablesDefault_data.txt')
shutil.copy(src_dir+'SQL_scripts.txt', trg_dir+'SQL_scripts.txt')
shutil.copy(src_dir+'dbSettings.txt', trg_dir+'dbSettings.txt')
shutil.copy(src_dir+'dbSettings_lastLoad.txt', trg_dir+'dbSettings_lastLoad.txt')
shutil.copy(src_dir+'Dialogs.py', trg_dir+'Dialogs.py')
shutil.copy(src_dir+'ida_ph.py', trg_dir+'ida_ph.py')
shutil.copy(src_dir+'ida_ph_dialog.py', trg_dir+'ida_ph_dialog.py')
copyMetaFiles(src_dir,trg_dir)

#result visualization
#print('result visualization')
src_dir=plugin_dir+'ida_rv\\'
trg_dir=target_plugin_dir+'ida_rv\\'
os.mkdir(trg_dir)
shutil.copytree(src_dir+'help',trg_dir+'help')
shutil.copytree(src_dir+'scripts',trg_dir+'scripts')
shutil.copytree(src_dir+'i18n',trg_dir+'i18n')
shutil.copy(src_dir+'icon-result-visualization.png', trg_dir+'icon-result-visualization.png')
shutil.copy(src_dir+'ida_rv.py', trg_dir+'ida_rv.py')
shutil.copy(src_dir+'ida_rv_dialog.py', trg_dir+'ida_rv_dialog.py')
copyMetaFiles(src_dir,trg_dir)

#------------models--------------
"""
target_model_dir=r'C:\EQUA\Projekte\DistrictEnergySystemModelling\QGIS plugin developement'+'\\'+current_date+'\\models\\'
#print(target_model_dir)
os.mkdir(target_model_dir)

#kusuda
src_dir=r'C:\EQUA\Projekte\DistrictEnergySystemModelling\Ground Temperature Modelling\Kusuda'+'\\'
trg_dir=target_model_dir+'kusuda\\'
os.mkdir(trg_dir)
shutil.copy(src_dir+'kusuda.mo', trg_dir+'kusuda.mo')
shutil.copy(src_dir+'kusuda.eo', trg_dir+'kusuda.eo')
shutil.copy(src_dir+'kusuda.dll', trg_dir+'kusuda.dll')
os.mkdir(trg_dir+'x64')
shutil.copy(src_dir+'x64\\kusuda.dll', trg_dir+'x64\\kusuda.dll')

#Flowmeter2
src_dir=r'C:\EQUA\Projekte\DistrictEnergySystemModelling\FlowMeter2'+'\\'
trg_dir=target_model_dir+'FlowMeter2\\'
os.mkdir(trg_dir)
shutil.copy(src_dir+'FlowMeter2.nmf', trg_dir+'FlowMeter2.nmf')
shutil.copy(src_dir+'flowmeter2.eo', trg_dir+'flowmeter2.eo')
shutil.copy(src_dir+'flowmeter2.dll', trg_dir+'flowmeter2.dll')
os.mkdir(trg_dir+'x64')
shutil.copy(src_dir+'x64\\flowmeter2.dll', trg_dir+'x64\\flowmeter2.dll')

#MinMax continious
src_dir=r'C:\EQUA\Projekte\DistrictEnergySystemModelling\MinMaxD_continuous'+'\\'
trg_dir=target_model_dir+'MinMaxD_continuous\\'
os.mkdir(trg_dir)
shutil.copy(src_dir+'minmaxd_cont.nmf', trg_dir+'minmaxd_cont.nmf')
shutil.copy(src_dir+'minmaxd_cont.eo', trg_dir+'minmaxd_cont.eo')
shutil.copy(src_dir+'minmaxd_cont.dll', trg_dir+'minmaxd_cont.dll')
os.mkdir(trg_dir+'x64')
shutil.copy(src_dir+'x64\\minmaxd_cont.dll', trg_dir+'x64\\minmaxd_cont.dll')

#Adder continious
src_dir=r'C:\EQUA\Projekte\DistrictEnergySystemModelling\Adder_continuous'+'\\'
trg_dir=target_model_dir+'Adder_continuous\\'
os.mkdir(trg_dir)
shutil.copy(src_dir+'Adder_cont.nmf', trg_dir+'Adder_cont.nmf')
shutil.copy(src_dir+'Adder_cont.eo', trg_dir+'Adder_cont.eo')
shutil.copy(src_dir+'Adder_cont.dll', trg_dir+'Adder_cont.dll')
os.mkdir(trg_dir+'x64')
shutil.copy(src_dir+'x64\\Adder_cont.dll', trg_dir+'x64\\Adder_cont.dll')

#pipe bundle
src_dir=r'C:\EQUA\Projekte\DistrictEnergySystemModelling\PipeBundle\Bundle18_7_2023'+'\\'
trg_dir=target_model_dir+'pipebundlef\\'
os.mkdir(trg_dir)
shutil.copy(src_dir+'pipebundlef.mo', trg_dir+'pipebundlef.mo')
shutil.copy(src_dir+'PipeBiFD.mo', trg_dir+'PipeBiFD.mo')
shutil.copy(src_dir+'pipebundlef.eo', trg_dir+'pipebundlef.eo')
shutil.copy(src_dir+'pipebundlef.dll', trg_dir+'pipebundlef.dll')
os.mkdir(trg_dir+'x64')
shutil.copy(src_dir+'x64\\pipebundlef.dll', trg_dir+'x64\\pipebundlef.dll')

#node bundle
src_dir=r'C:\EQUA\Projekte\DistrictEnergySystemModelling\PipeBundle\nodebundle'+'\\'
trg_dir=target_model_dir+'nodebundle\\'
os.mkdir(trg_dir)
shutil.copy(src_dir+'nodebundle.mo', trg_dir+'nodebundle.mo')
shutil.copy(src_dir+'nodebundle.eo', trg_dir+'nodebundle.eo')
shutil.copy(src_dir+'nodebundle.dll', trg_dir+'nodebundle.dll')
os.mkdir(trg_dir+'x64')
shutil.copy(src_dir+'x64\\nodebundle.dll', trg_dir+'x64\\nodebundle.dll')

#customer models
#lm_h_g_l
src_dir=r'C:\EQUA\Projekte\DistrictEnergySystemModelling\Customermodel\development\loadModel_H_gains_limit'+'\\'
trg_dir=target_model_dir+'lm_h_g_l\\'
os.mkdir(trg_dir)
shutil.copy(src_dir+'lm_h_g_l.mo', trg_dir+'lm_h_g_l.mo')
shutil.copy(src_dir+'lM_base_v1.mo', trg_dir+'lM_base_v1.mo')
shutil.copy(src_dir+'lm_h_g_l.eo', trg_dir+'lm_h_g_l.eo')
shutil.copy(src_dir+'lm_h_g_l.dll', trg_dir+'lm_h_g_l.dll')
os.mkdir(trg_dir+'x64')
shutil.copy(src_dir+'x64\\lm_h_g_l.dll', trg_dir+'x64\\lm_h_g_l.dll')

#lm_hc_g_l
src_dir=r'C:\EQUA\Projekte\DistrictEnergySystemModelling\Customermodel\development\loadModel_HC_gains_limit'+'\\'
trg_dir=target_model_dir+'lm_hc_g_l\\'
os.mkdir(trg_dir)
shutil.copy(src_dir+'lm_hc_g_l.mo', trg_dir+'lm_hc_g_l.mo')
shutil.copy(src_dir+'lM_base_v1.mo', trg_dir+'lM_base_v1.mo')
shutil.copy(src_dir+'lm_hc_g_l.eo', trg_dir+'lm_hc_g_l.eo')
shutil.copy(src_dir+'lm_hc_g_l.dll', trg_dir+'lm_hc_g_l.dll')
os.mkdir(trg_dir+'x64')
shutil.copy(src_dir+'x64\\lm_hc_g_l.dll', trg_dir+'x64\\lm_hc_g_l.dll')

#lm_hc_4_g_l
src_dir=r'C:\EQUA\Projekte\DistrictEnergySystemModelling\Customermodel\development\loadModel_HC_4_gains_limit'+'\\'
trg_dir=target_model_dir+'lm_hc_4_g_l\\'
os.mkdir(trg_dir)
shutil.copy(src_dir+'lm_hc_4_g_l.mo', trg_dir+'lm_hc_4_g_l.mo')
shutil.copy(src_dir+'lM_base_v1.mo', trg_dir+'lM_base_v1.mo')
shutil.copy(src_dir+'lm_hc_4_g_l.eo', trg_dir+'lm_hc_4_g_l.eo')
shutil.copy(src_dir+'lm_hc_4_g_l.dll', trg_dir+'lm_hc_4_g_l.dll')
os.mkdir(trg_dir+'x64')
shutil.copy(src_dir+'x64\\lm_hc_4_g_l.dll', trg_dir+'x64\\lm_hc_4_g_l.dll')

#lm_h_g_l_mctrl
src_dir=r'C:\EQUA\Projekte\DistrictEnergySystemModelling\Customermodel\development\loadModel_H_gains_noHs_idealMdot'+'\\'
trg_dir=target_model_dir+'lm_h_g_l_mctrl\\'
os.mkdir(trg_dir)
shutil.copy(src_dir+'lm_h_g_l_mctrl.mo', trg_dir+'lm_h_g_l_mctrl.mo')
shutil.copy(src_dir+'lM_base_v1.mo', trg_dir+'lM_base_v1.mo')
shutil.copy(src_dir+'lm_h_g_l_mctrl.eo', trg_dir+'lm_h_g_l_mctrl.eo')
shutil.copy(src_dir+'lm_h_g_l_mctrl.dll', trg_dir+'lm_h_g_l_mctrl.dll')
os.mkdir(trg_dir+'x64')
shutil.copy(src_dir+'x64\\lm_h_g_l_mctrl.dll', trg_dir+'x64\\lm_h_g_l_mctrl.dll')

#hx
src_dir=r'C:\EQUA\Projekte\DistrictEnergySystemModelling\Customermodel\development\hx'+'\\'
trg_dir=target_model_dir+'hx\\'
os.mkdir(trg_dir)
shutil.copy(src_dir+'hx.mo', trg_dir+'hx.mo')
shutil.copy(src_dir+'hx.eo', trg_dir+'hx.eo')
shutil.copy(src_dir+'hx.dll', trg_dir+'hx.dll')
os.mkdir(trg_dir+'x64')
shutil.copy(src_dir+'x64\\hx.dll', trg_dir+'x64\\hx.dll')
"""

#documentation
target_doc_dir=r'C:\EQUA\Projekte\DistrictEnergySystemModelling\QGIS plugin developement'+'\\'+current_date+'\\documentation\\'
#print(target_doc_dir)
os.mkdir(target_doc_dir)
src_dir=r'G:\Projekt\Districts\Dokumentation'+'\\'
shutil.copy(src_dir+'IDA Districts Getting Started Guide.docx', target_doc_dir+'IDA Districts Getting Started Guide.docx')

#installation
target_install_dir=r'C:\EQUA\Projekte\DistrictEnergySystemModelling\QGIS plugin developement'+'\\'+current_date+'\\installation\\'
#print(target_install_dir)
os.mkdir(target_install_dir)
src_dir=r'C:\Users\Peter\AppData\Roaming\QGIS\QGIS3\profiles\default\python\plugins\test_functions'+'\\'
shutil.copy(src_dir+'plugin_installer.py', target_install_dir+'plugin_installer.py')

#print('finished')