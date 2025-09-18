from qgis.core import QgsFeature, QgsGeometry, QgsPointXY, QgsWkbTypes

from plugins.ida_ph.ida_ph import *
from plugins.ida_pp.ida_pp import *
from plugins.ida_pp.osm import *
from plugins.ida_pp.GenerateNetworkTopology import *
from plugins.ida_mosim.ida_mosim import *
from plugins.ida_rv.ida_rv import *


from qgis.PyQt.QtCore import Qt
from qgis.PyQt.QtCore import QTimer,QEventLoop
import psycopg2.extras
import psycopg2
import copy
from plugins.utility_functions.db import *
import sys, os, importlib

from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT

def addMainPlant():
    # Get the layer by name
    layer = QgsProject.instance().mapLayersByName('energy_plants')
    if not layer:
        print("Layer 'energy_plants' not found")
    else:
        layer = layer[0]

        # Check if layer is a point layer
        if layer.geometryType() != QgsWkbTypes.PointGeometry:
            print("Layer is not a point layer")
        else:
            # Create new feature with the layer fields
            feature = QgsFeature(layer.fields())

            # Set the geometry (example coordinates, change as needed)
            point = QgsPointXY(1010365 , 6615369)
            feature.setGeometry(QgsGeometry.fromPointXY(point))

            # Set the attributes by field name
            # Make sure these fields exist in the layer!
            feature['template'] = 1

            # For the array attribute, set as a Python list
            feature['network'] = [1]

            # Start editing the layer and add the feature
            layer.startEditing()
            res, out_feats = layer.dataProvider().addFeatures([feature])
            if res:
                layer.commitChanges()
                print("Feature added successfully.")
            else:
                layer.rollBack()
                print("Failed to add feature.")
    
class Autotest:
    def __init__(self):
        self.plugin_dir="""C:\\Users\\Peter\\AppData\\Roaming\\QGIS\\QGIS3\\profiles\\default\\python\\plugins\\"""
        self.conn=''
        self.cur=''
        self.progress=0

        try:
            self.runTest()
        except Exception as e:
            print('ERROR: '+str(e)+'!!!!!!!!!!!!')
                    
    def wait(self,ms):
        loop = QEventLoop()
        QTimer.singleShot(ms, loop.quit)
        loop.exec_()
    
    def process_wait(self,plugin,max_sec=60):
        counter=0
        while plugin.process_running==True and counter<max_sec:
            self.wait(1000)
            counter+=1
            print('-wait: '+str(counter)+'s')
        
    def show_error_message(self, message):
        self.error.append(message)
        
    def runTest(self):            
        # self.ph=IDA_Districts_ProjectHandling(iface)
        # self.ph.first_start=True
        # self.ph.run()
        # self.ph.dictDB['pwd']='p3t3r'
        # self.ph.dictDB['port']='5433'
        # self.ph.dictDB['user']='postgres'
        # self.ph.dictDB['host']='localhost'
        # self.ph.dictDB['storeCredentials']=True
        # writeDBSettings(self.plugin_dir,self.ph.dictDB)
        # self.ph.connectDBPostgres()

        templates=['Heating network','Empty project','DB default values','Co-sim buildings with heating network']
        for project in [templates[0]]:
            print('++++++++++++'+project+'+++++++++++++')
            
            # #test create project
            # print('--start create project--')
            # self.ph.showCreateNewProject()
            # projectName='autotest_'+project.replace(' ','_').lower()
            # print(projectName)
            # self.ph.dlg_createNewProject.project_name.setText(projectName)
            # self.ph.dlg_createNewProject.selectTemplate.setCurrentText(project)
            # if project in ['DB default values','Empty project']:
            #     self.ph.dlg_createNewProject.checkbox_db_defaultValues.setCheckState(Qt.Checked)
            #     self.ph.dlg_createNewProject.checkbox_invokedFeatures.setCheckState(Qt.Unchecked)
            #     self.ph.dlg_createNewProject.checkbox_prn.setCheckState(Qt.Unchecked)
            #     self.ph.dlg_createNewProject.checkbox_DBResults.setCheckState(Qt.Unchecked)
            # else:
            #     self.ph.dlg_createNewProject.checkbox_db_defaultValues.setCheckState(Qt.Unchecked)
            #     self.ph.dlg_createNewProject.checkbox_invokedFeatures.setCheckState(Qt.Checked)
            #     self.ph.dlg_createNewProject.checkbox_prn.setCheckState(Qt.Checked)
            #     self.ph.dlg_createNewProject.checkbox_DBResults.setCheckState(Qt.Checked)
            
            # self.ph.createNewProject(self.ph.dlg_createNewProject)
            # self.process_wait(self.ph,max_sec=30)
            # print('++create project finished++')

            # self.dictDB=getDBConnectionData(self.plugin_dir)
            # print(self.dictDB)            
            # try:
            #     self.conn=dbConnect(self.ph.dictDB,True)
            # except:
            #     self.conn=dbConnect(self.dictDB,True)
            # self.cur=self.conn.cursor(cursor_factory = psycopg2.extras.RealDictCursor)
            # print(self.cur)
            
            # if project in ['DB default values','Empty project']:
            #     print('--Start create version: base1--')
            #     self.ph.dlg_addBase=IDA_Districts_NameDialog('Add base version','Add base version:','','')
            #     self.ph.dlg_addBase.input.setText('base1')
            #     self.ph.addBaseVersion(self.ph.dlg_addBase)
            #     print('++Create version finished++')
        
            # #test preprocessing
            # self.pp=IdaDistrictsPreProcessing(iface)
            # self.pp.first_start=True
            # self.pp.run()

            # if project in ['DB default values','Empty project']:
            #     print('--Start import streets--')
            #     self.pp.openImportDlg(default_path=getDataCenterDir(self.plugin_dir)+"/Samples/OSM/map_1.osm",title='Streets from OSM',ok_fn=self.pp.importStreetsFromOSM,extensions='*.osm')
            #     self.pp.dlg_import.checkBoxClearOldFeatures.setCheckState(Qt.Checked)
            #     self.pp.importStreetsFromOSM(self.pp.dlg_import)
            #     self.process_wait(self.pp.dlg_import,max_sec=10)
            #     closeDialog(self.pp.dlg_import)
            #     print('--Import streets finished--')
                
            #     print('--Start import buildings--')
            #     self.pp.openImportDlg(default_path=getDataCenterDir(self.plugin_dir)+"/Samples/OSM/map_1.osm",title='Buildings from OSM',ok_fn=self.pp.importBuildingsFromOSM,extensions='*.osm')
            #     self.pp.dlg_import.checkBoxClearOldFeatures.setCheckState(Qt.Checked)
            #     self.pp.importBuildingsFromOSM(self.pp.dlg_import)
            #     self.process_wait(self.pp.dlg_import,max_sec=10)
            #     closeDialog(self.pp.dlg_import)
            #     print('--Import buildings finished--')
                
            #     print('--Start import eleveation data--')
            #     self.pp.openImportDlg(default_path=getDataCenterDir(self.plugin_dir)+"/Samples/elevation_data/N59E017.hgt",title='Elevation data',ok_fn=self.pp.importElevationData,extensions='*.hgt;*.tif;*.tiff')
            #     self.pp.dlg_import.checkBoxClearOldFeatures.setCheckState(Qt.Checked)
            #     self.pp.importElevationData(self.pp.dlg_import)
            #     self.process_wait(self.pp.dlg_import,max_sec=30)
            #     print('++import N59E017.hgt finished++')
            #     self.pp.openImportDlg(default_path=getDataCenterDir(self.plugin_dir)+"/Samples/elevation_data/N59E018.hgt",title='Elevation data',ok_fn=self.pp.importElevationData,extensions='*.hgt;*.tif;*.tiff')
            #     self.pp.dlg_import.checkBoxClearOldFeatures.setCheckState(Qt.Checked)
            #     self.pp.importElevationData(self.pp.dlg_import)
            #     self.process_wait(self.pp.dlg_import,max_sec=30)
            #     closeDialog(self.pp.dlg_import)
            #     print('++import N59E018.hgt finished++')
                
            #     #place main energy plant
            #     addMainPlant()
            
            #     print('--start pipe laying algorithm--')
            #     self.pp.pipeLayingAlgorithm()
            #     self.pp.dlg_pipeLayingAlgorithm.check_heating_network.setCheckState(Qt.Checked)
            #     self.pp.dlg_pipeLayingAlgorithm.execute()
            #     self.process_wait(self.pp.dlg_pipeLayingAlgorithm,max_sec=10)
            #     self.pp.dlg_pipeLayingAlgorithm.saveResults()
            #     closeDialog(self.pp.dlg_pipeLayingAlgorithm)
            #     print('++pipe laying algorithm finished++')
                
            
            # if project in ['Heating network','Co-sim buildings with heating network']:
            #     print('--start generate network topology--')
            #     self.pp.generateNetworkTopology()
            #     self.pp.window_topology.rbtn_override_templates.setChecked(True)
            #     self.pp.window_topology.check_del_network_ends.setCheckState(Qt.Checked)
            #     self.pp.window_topology.check_connectCustomers.setCheckState(Qt.Checked)
            #     self.pp.window_topology.check_connectPlants.setCheckState(Qt.Checked)
            #     self.pp.window_topology.check_deleteUnconnectedCustomers.setCheckState(Qt.Checked)
            #     self.pp.window_topology.check_deleteUnconnectedLines.setCheckState(Qt.Checked)
            #     self.pp.window_topology.check_connectPlants.setCheckState(Qt.Checked)
            #     self.pp.window_topology.combo_network_models.setItemChecked(1,True) 
                
            #     self.pp.window_topology.execute()
            #     self.process_wait(self.pp.window_topology,max_sec=10)
            #     self.pp.window_topology.saveResults()
            #     closeDialog(self.pp.window_topology)
            #     print('++generate network topology finished++')
            
            # #pipe sizing
            # print('--start pipe sizing--')
            # self.pp.pipeSizing()
            # self.pp.dlg_pipeSizing.addRow()
            # self.pp.dlg_pipeSizing.table_circuits.item(0,1).setText('70')
            # self.pp.dlg_pipeSizing.table_circuits.item(0,4).setText('40')
            # self.pp.dlg_pipeSizing.table_circuits.selectRow(0)
            # self.pp.dlg_pipeSizing.table_circuits.selectColumn(3)
            # self.pp.dlg_pipeSizing.table_circuits.cellWidget(0,3).setCurrentText('2')
            # self.pp.dlg_pipeSizing.table_circuits.cellWidget(0,5).setCurrentText('load_w')
            # for row in range(self.pp.dlg_pipeSizing.table_sequences.rowCount()):
            #     self.pp.dlg_pipeSizing.table_sequences.cellWidget(row,1).setAllItemsChecked(checked=True)
            # startPipeSizing(self.dictDB,self.pp.dlg_pipeSizing,self.plugin_dir)
            # self.process_wait(self.pp.dlg_pipeSizing,max_sec=10)
            # #savePipeSizingResults(self.dictDB,self.conn,self.pp.dlg_pipeSizing)
            # closeDialog(self.pp.dlg_pipeSizing)
            # print('--pipe sizing finished--')
            
            
            
            
            # #test modelling and simulation          
            # self.mosim= IDADistrictsModelingSimulation(iface)
            # self.mosim.first_start=True
            # self.mosim.run()
            
            # if project in ['DB default values','Empty project']:
            #     #set requested outputs
            #     print('--start set requested outputs--')
            #     self.mosim.showRequestedOutputs()
            #     self.mosim.dlg_outputs.checkBoxSubstationPower.setChecked(True)
            #     self.mosim.dlg_outputs.checkBoxSubstationConnTemp.setChecked(True)
            #     self.mosim.dlg_outputs.checkBoxSubstationPressure.setChecked(True)
            #     self.mosim.dlg_outputs.checkBoxSubstationMassflow.setChecked(True)
            #     self.mosim.dlg_outputs.checkBoxSubstationHeatbalance.setChecked(True)
            #     self.mosim.dlg_outputs.checkBoxSubstationTair.setChecked(True)
            #     self.mosim.dlg_outputs.checkBoxPressureDistribution.setChecked(True)
            #     self.mosim.dlg_outputs.checkBoxMdotNode.setChecked(True)
            #     self.mosim.dlg_outputs.checkBoxVPipe.setChecked(True)
            #     self.mosim.dlg_outputs.checkBoxTempPipe.setChecked(True)
            #     self.mosim.dlg_outputs.checkBoxPlantPower.setChecked(True)
            #     self.mosim.dlg_outputs.checkBoxPlantConnTemp.setChecked(True)
            #     self.mosim.dlg_outputs.checkBoxPlantPressure.setChecked(True)
            #     self.mosim.dlg_outputs.checkBoxPlantMassflow.setChecked(True)
            #     self.mosim.dlg_outputs.outputTimestep.setText('0.25')
            #     self.mosim.setRequestedOutputs(self.mosim.dlg_outputs,self.mosim.requestedOutputs)
            #     self.process_wait(self.mosim.dlg_outputs,max_sec=10)      
            #     closeDialog(self.mosim.dlg_outputs)
            #     print('++set requested outputs finished++')
            
            # if project in ['Heating network','Co-sim buildings with heating network']:
            #     #feature parameter mapping
            #     print('--start feature parameter mapping--')
            #     self.mosim.showFeatureParm()
            #     self.mosim.dlg_featureParm.tableWidget_parameters.setRowCount(0)
            #     setFeatureParm(self.mosim.dlg_featureParm,self.conn,self.dictDB,self.plugin_dir)
            #     addParmTableRow(self.mosim.dlg_featureParm,self.cur,self.dictDB)
            #     self.mosim.dlg_featureParm.tableWidget_parameters.item(0,1).setText('"load_w"')
            #     self.mosim.dlg_featureParm.tableWidget_parameters.item(0,3).setText('FloorArea')
            #     self.mosim.dlg_featureParm.tableWidget_parameters.item(0,4).setText('Lm_H_G_L_Mctrl')
            #     self.mosim.dlg_featureParm.tableWidget_parameters.item(0,5).setText(':FEATURE')
                
            #     addParmTableRow(self.mosim.dlg_featureParm,self.cur,self.dictDB)
            #     self.mosim.dlg_featureParm.tableWidget_parameters.item(0,1).setText('"gfa"')
            #     self.mosim.dlg_featureParm.tableWidget_parameters.item(0,3).setText('X')
            #     self.mosim.dlg_featureParm.tableWidget_parameters.item(0,4).setText('Load limit')
            #     self.mosim.dlg_featureParm.tableWidget_parameters.item(0,5).setText(':FEATURE')
            #     setFeatureParm(self.mosim.dlg_featureParm,self.conn,self.dictDB,self.plugin_dir)
            #     closeDialog(self.mosim.dlg_featureParm)
            #     print('++feature parameter mapping finished++')
                
            
            # print('--start build network model--')
            # self.mosim.showBuildModel()
            # self.mosim.dlg_buildModel.combo_network_models.setItemChecked(1,True) 
            # self.mosim.dlg_buildModel.combo_submodels.setItemChecked(1,True) 
            # self.mosim.buildModel(self.mosim.dlg_buildModel)
            # self.process_wait(self.mosim.dlg_buildModel,max_sec=10)      
            # closeDialog(self.mosim.dlg_buildModel)
            # print('++build network model finished++')
            
            
            # #test run simulation
            # print('--start simulation--')
            # #batch mode: "C:\Program Files (x86)\IDA52\bin\ida-ice.exe" "C:\Program Files (x86)\IDA52\bin\ida.img" -C ida1 -W hidden -B "C:\Users\Peter\AppData\Roaming\QGIS\QGIS3\profiles\default\python\plugins\ida_mosim\models\test0013\base1\log.txt" -X "C:\Users\Peter\AppData\Roaming\QGIS\QGIS3\profiles\default\python\plugins\ida_mosim\models\test0013\base1\network_1_script.txt"
            # #(:set doc_ (:call get-document "C:\\Users\\Peter\\AppData\\Roaming\\QGIS\\QGIS3\\profiles\\default\\python\\plugins\\ida_mosim\\models\\test0013\\base1\\network_1.idm"))  
            # #(:show doc_)
            # #(ICE-RUN-BUILDING-EX doc_)
            # #(save-document doc_ )
            # #(exit-ida)
            # self.mosim.showRunModel()
            # self.mosim.dlg_runModel.combo_submodels.setItemChecked(1,checked=True)
            # self.mosim.runModel(self.mosim.dlg_runModel)
            # self.process_wait(self.mosim.dlg_runModel,max_sec=70)
            # print('--simulation finished--')

            # print('--start load results--')
            # self.mosim.showLoadResults()
            # self.mosim.dlg_loadResults.combo_submodels.setItemChecked(1,True) 
            # self.mosim.loadResults(self.mosim.dlg_loadResults)
            # self.process_wait(self.mosim.dlg_loadResults,max_sec=10)      
            # closeDialog(self.mosim.dlg_loadResults)
            # print('++load results finished++')
            
            
            #test result visualization          
            self.rv= IDADistrictsResultVisualization(iface)
            self.rv.first_start=True
            self.rv.run()
            
            # print('--start show data on map--')
            # self.rv.btn_showDataOnMap()
            # #customer load values
            # self.rv.dlg_showOnMap.rbtn_customers.setChecked(True)
            # self.rv.dlg_showOnMap.checkbox_varColor.setChecked(True)
            # self.rv.dlg_showOnMap.color_var.setCurrentText('power$1_1')
            # self.rv.dlg_showOnMap.color_function.setCurrentText('Values')
            # self.rv.dlg_showOnMap.checkbox_varSize.setChecked(True)
            # self.rv.dlg_showOnMap.rbtn_sizePar.setChecked(True)
            # self.rv.dlg_showOnMap.size_par.setCurrentText('gfa')
            # self.rv.dlg_showOnMap.layer_name.setText('customer_results_load_values')
            # self.wait(1000)
            # self.rv.showOnMap(self.rv.dlg_showOnMap)
            # self.process_wait(self.rv.dlg_showOnMap,max_sec=10)
            # closeDialog(self.rv.dlg_showOnMap)
            
            # #lines supply temperature
            # self.rv.btn_showDataOnMap()
            # self.rv.dlg_showOnMap.rbtn_lines.setChecked(True)
            # self.rv.dlg_showOnMap.checkbox_varColor.setChecked(True)
            # self.rv.dlg_showOnMap.featureGroupChanged(self.rv.dlg_showOnMap.rbtn_lines)
            # self.rv.dlg_showOnMap.color_var.setCurrentText('temp$1')
            # self.rv.dlg_showOnMap.color_function.setCurrentText('Values')
            # self.rv.dlg_showOnMap.layer_name.setText('lines_results_supply_temperature_values')
            # self.wait(2000)
            # self.rv.showOnMap(self.rv.dlg_showOnMap)
            # self.process_wait(self.rv.dlg_showOnMap,max_sec=10)
            # #closeDialog(self.rv.dlg_showOnMap)
            # print('++show data on map finished++')
            
            print('--start path report--')
            self.rv.showPathReports()
            self.rv.dlg_pathReports.rbtn_pathPressure.setChecked(True)
            self.rv.dlg_pathReports.rbtn_weakPoint.setChecked(True)
            self.rv.dlg_pathReports.rbtn_Date.setChecked(True)
            self.rv.dlg_pathReports.date_input.setText('2025-01-21 14:15:00')
            self.rv.dlg_pathReports.dp_recalc.setChecked(True)
            self.rv.dlg_pathReports.dp_min_recalc.setText('0.8')
            
            self.rv.dlg_pathReports.sup_sequence.setCurrentIndex(0)
            self.rv.dlg_pathReports.ret_sequence.setCurrentIndex(2)
            self.rv.generatePathReport(self.rv.dlg_pathReports)
            print('++path report 1 finished++')
                        
            # self.rv.showPathReports()
            # self.rv.dlg_pathReports.rbtn_pathPressure.setChecked(True)
            # self.rv.dlg_pathReports.rbtn_weakPoint.setChecked(True)
            # self.rv.dlg_pathReports.rbtn_Date.setChecked(True)
            # self.rv.dlg_pathReports.date_input.setText('2025-08-15 21:00:00')
            # self.rv.dlg_pathReports.dp_recalc.setChecked(True)
            # self.rv.dlg_pathReports.dp_min_recalc.setText('0.8')
            
            # self.rv.dlg_pathReports.sup_sequence.setCurrentIndex(1)
            # self.rv.dlg_pathReports.ret_sequence.setCurrentIndex(3)
            # self.rv.generatePathReport(self.rv.dlg_pathReports)
            
            # #test delete project
            # print('--delete project started--')
            # self.ph.deleteProject(projectName)
            # print('++delete project finished++')
            

Autotest()
print('--finished testing--')
