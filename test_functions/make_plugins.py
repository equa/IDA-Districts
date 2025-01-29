from plugins.utility_functions.files import *
from plugins.utility_functions.db import *
from datetime import datetime
import shutil

plugin_dir="""C:\\Users\\Peter\\AppData\\Roaming\\QGIS\\QGIS3\\profiles\\default\\python\\plugins\\"""

current_date = datetime.now().strftime('%Y-%m-%d-%H%M')
target_dir=r'C:\EQUA\Projekte\DistrictEnergySystemModelling\QGIS plugin developement'+'\\'+current_date+'\\'

# Check if the folder exists and delete it
if os.path.exists(target_dir) and os.path.isdir(target_dir):
    shutil.rmtree(target_dir)

#------------plugins--------------
target_plugin_dir=target_dir+'plugins\\'
print(target_plugin_dir)

def copyMetaFiles(src_dir,trg_dir):
    os.mkdir(trg_dir+'__pycache__')
    for file_name in ['__init__.py','Makefile','metadata.txt','pb_tool.cfg','pylintrc','resources.py','resources.qrc']:
        shutil.copy(src_dir+file_name, trg_dir+file_name)
        
    
#utility functions
shutil.copytree(plugin_dir+'utility_functions',target_plugin_dir+'utility_functions')

#data center
src_dir=plugin_dir+'ida_districts_data_center\\'
trg_dir=target_plugin_dir+'ida_districts_data_center\\'
os.mkdir(trg_dir)
shutil.copytree(src_dir+'config',trg_dir+'config')
shutil.copytree(src_dir+'help',trg_dir+'help')
shutil.copytree(src_dir+'Samples',trg_dir+'Samples')
shutil.copytree(src_dir+'scripts',trg_dir+'scripts')
shutil.copytree(src_dir+'i18n',trg_dir+'i18n')
shutil.copy(src_dir+'icon-data-center.png', trg_dir+'icon-data-center.png')
shutil.copy(src_dir+'ida_districts_data_center.py', trg_dir+'ida_districts_data_center.py')
shutil.copy(src_dir+'ida_districts_data_center_dialog.py', trg_dir+'ida_districts_data_center_dialog.py')
shutil.copy(src_dir+'update_boundaries.py', trg_dir+'update_boundaries.py')
copyMetaFiles(src_dir,trg_dir)

#modelling
src_dir=plugin_dir+'\ida_districts_modeling_simulation\\'
trg_dir=target_plugin_dir+'\ida_districts_modeling_simulation\\'
os.mkdir(trg_dir)
os.mkdir(trg_dir+'network_models')
shutil.copytree(src_dir+'help',trg_dir+'help')
shutil.copytree(src_dir+'scripts',trg_dir+'scripts')
shutil.copytree(src_dir+'i18n',trg_dir+'i18n')
shutil.copytree(src_dir+'graphics',trg_dir+'graphics')
shutil.copy(src_dir+'icon-mo-sim.png', trg_dir+'icon-mo-sim.png')
shutil.copy(src_dir+'calibrate_customers.py', trg_dir+'calibrate_customers.py')
shutil.copy(src_dir+'calibrate_features.py', trg_dir+'calibrate_features.py')
shutil.copy(src_dir+'cosim.py', trg_dir+'cosim.py')
shutil.copy(src_dir+'ida_districts_modeling_simulation.py', trg_dir+'ida_districts_modeling_simulation.py')
shutil.copy(src_dir+'ida_districts_modeling_simulation_dialog.py', trg_dir+'ida_districts_modeling_simulation_dialog.py')
shutil.copy(src_dir+'invoke.py', trg_dir+'invoke.py')
shutil.copy(src_dir+'invoke_network.py', trg_dir+'invoke_network.py')
shutil.copy(src_dir+'outputs.py', trg_dir+'outputs.py')
shutil.copy(src_dir+'invoke_sensors.py', trg_dir+'invoke_sensors.py')
shutil.copy(src_dir+'load_results.py', trg_dir+'load_results.py')
shutil.copy(src_dir+'supervisory_control.py', trg_dir+'supervisory_control.py')
shutil.copy(src_dir+'update_sensors.py', trg_dir+'update_sensors.py')
copyMetaFiles(src_dir,trg_dir)


#preprocessing
src_dir=plugin_dir+'ida_districts_preprocessing\\'
trg_dir=target_plugin_dir+'ida_districts_preprocessing\\'
os.mkdir(trg_dir)
shutil.copytree(src_dir+'help',trg_dir+'help')
shutil.copytree(src_dir+'scripts',trg_dir+'scripts')
shutil.copytree(src_dir+'i18n',trg_dir+'i18n')
shutil.copy(src_dir+'icon-pre-processing.png', trg_dir+'icon-pre-processing.png')
shutil.copy(src_dir+'elevation_data.py', trg_dir+'elevation_data.py')
shutil.copy(src_dir+'GenerateNetworkTopology.py', trg_dir+'GenerateNetworkTopology.py')
shutil.copy(src_dir+'ida_districts_preprocessing.py', trg_dir+'ida_districts_preprocessing.py')
shutil.copy(src_dir+'ida_districts_preprocessing_dialog.py', trg_dir+'ida_districts_preprocessing_dialog.py')
shutil.copy(src_dir+'osm.py', trg_dir+'osm.py')
shutil.copy(src_dir+'pipe_sizing.py', trg_dir+'pipe_sizing.py')
shutil.copy(src_dir+'PipeLayingAlgorithm.py', trg_dir+'PipeLayingAlgorithm.py')
copyMetaFiles(src_dir,trg_dir)

#project handling
src_dir=plugin_dir+'ida_districts_project_handling\\'
trg_dir=target_plugin_dir+'ida_districts_project_handling\\'
os.mkdir(trg_dir)
shutil.copytree(src_dir+'help',trg_dir+'help')
shutil.copytree(src_dir+'scripts',trg_dir+'scripts')
shutil.copytree(src_dir+'i18n',trg_dir+'i18n')
shutil.copytree(src_dir+'icons',trg_dir+'icons')
shutil.copytree(src_dir+'templates',trg_dir+'templates')
shutil.copy(src_dir+'configIDADistricts.txt', trg_dir+'configIDADistricts.txt')
shutil.copy(src_dir+'DB_projectTablesDefault.txt', trg_dir+'DB_projectTablesDefault.txt')
shutil.copy(src_dir+'DB_projectTablesDefault_data.txt', trg_dir+'DB_projectTablesDefault_data.txt')
shutil.copy(src_dir+'DB_versionTablesDefault.txt', trg_dir+'DB_versionTablesDefault.txt')
shutil.copy(src_dir+'DB_versionTablesDefault_data.txt', trg_dir+'DB_versionTablesDefault_data.txt')
shutil.copy(src_dir+'dbSettings.txt', trg_dir+'dbSettings.txt')
shutil.copy(src_dir+'dbSettings_lastLoad.txt', trg_dir+'dbSettings_lastLoad.txt')
shutil.copy(src_dir+'Dialogs.py', trg_dir+'Dialogs.py')
shutil.copy(src_dir+'IDA_districts_project_handling.py', trg_dir+'IDA_districts_project_handling.py')
shutil.copy(src_dir+'IDA_districts_project_handling_dialog.py', trg_dir+'IDA_districts_project_handling_dialog.py')
copyMetaFiles(src_dir,trg_dir)

#result visualization
src_dir=plugin_dir+'ida_districts_result_visualization\\'
trg_dir=target_plugin_dir+'ida_districts_result_visualization\\'
os.mkdir(trg_dir)
shutil.copytree(src_dir+'help',trg_dir+'help')
shutil.copytree(src_dir+'scripts',trg_dir+'scripts')
shutil.copytree(src_dir+'i18n',trg_dir+'i18n')
shutil.copy(src_dir+'icon-result-visualization.png', trg_dir+'icon-result-visualization.png')
shutil.copy(src_dir+'ida_districts_result_visualization.py', trg_dir+'ida_districts_result_visualization.py')
shutil.copy(src_dir+'ida_districts_result_visualization_dialog.py', trg_dir+'ida_districts_result_visualization_dialog.py')
shutil.copy(src_dir+'show_on_map.py', trg_dir+'show_on_map.py')
copyMetaFiles(src_dir,trg_dir)

#------------models--------------
target_model_dir=r'C:\EQUA\Projekte\DistrictEnergySystemModelling\QGIS plugin developement'+'\\'+current_date+'\\models\\'
print(target_model_dir)
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

#documentation
target_doc_dir=r'C:\EQUA\Projekte\DistrictEnergySystemModelling\QGIS plugin developement'+'\\'+current_date+'\\documentation\\'
print(target_doc_dir)
os.mkdir(target_doc_dir)
src_dir=r'G:\Projekt\Districts\Dokumentation'+'\\'
shutil.copy(src_dir+'IDA Districts Getting Started Guide.docx', target_doc_dir+'IDA Districts Getting Started Guide.docx')

#installation
target_install_dir=r'C:\EQUA\Projekte\DistrictEnergySystemModelling\QGIS plugin developement'+'\\'+current_date+'\\installation\\'
print(target_install_dir)
os.mkdir(target_install_dir)
src_dir=r'C:\Users\Peter\AppData\Roaming\QGIS\QGIS3\profiles\default\python\plugins\test_functions'+'\\'
shutil.copy(src_dir+'plugin_installer.py', target_install_dir+'plugin_installer.py')