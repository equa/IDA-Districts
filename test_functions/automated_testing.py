#execute the automated test in debug mode==False

from qgis.core import QgsFeature, QgsGeometry, QgsPointXY, QgsWkbTypes

from plugins.districts.districts import *
from plugins.districts.ida_ph import *
from plugins.districts.ida_pp import *
from plugins.districts.osm import *
from plugins.districts.GenerateNetworkTopology import *
from plugins.districts.ida_mosim import *
from plugins.districts.ida_rv import *
from plugins.districts.utility_functions.db import *
from plugins.districts.utility_functions.translations import *



from qgis.PyQt.QtCore import Qt
from qgis.PyQt.QtCore import QTimer,QEventLoop
import psycopg2.extras
import psycopg2
import copy
import sys, os, importlib

from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT

def addMainPlant():
    # Get the layer by name
    layer = QgsProject.instance().mapLayersByName(tr('@default','energy_plants'))
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
            feature['submodel'] = 1

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
        self.plugin_dir=QgsApplication.qgisSettingsDirPath() + "python/plugins/"""
        self.progress=0

        #try:
        self.runTest()
        #except Exception as e:
            #print('ERROR: '+str(e)+'!!!!!!!!!!!!')
                    
    def wait(self,ms):
        loop = QEventLoop()
        QTimer.singleShot(ms, loop.quit)
        loop.exec()
    
    def process_wait(self,plugin,max_sec=60):
        counter=0
        while plugin.process_running==True and counter<max_sec:
            self.wait(1000)
            counter+=1
            print('-wait: '+str(counter)+'s')
        
    def show_error_message(self, message):
        self.error.append(message)
        
    def runTest(self):           
        self.districts=Districts(iface)
        self.districts.first_start=True
        self.districts.run()

        templates=['Heating network','Empty project','DB default values']
        for project in [templates[0]]:
            print('++++++++++++'+project+'+++++++++++++')
            
            #test create project
            print('--start create project--')
            self.districts.showCreateNewProject()
            projectName='autotest_'+time.strftime("%m%d%H%M%S", time.localtime())+'_'+project.replace(' ','_').lower()
            print(projectName)
            self.districts.dlg_createNewProject.project_name.setText(projectName)
            self.districts.dlg_createNewProject.selectTemplate.setCurrentText(project)
            if project in ['DB default values','Empty project']:
                self.districts.dlg_createNewProject.checkbox_db_defaultValues.setCheckState(checkState())
                self.districts.dlg_createNewProject.checkbox_invokedFeatures.setCheckState(uncheckState())
                self.districts.dlg_createNewProject.checkbox_prn.setCheckState(uncheckState())
                self.districts.dlg_createNewProject.checkbox_DBResults.setCheckState(uncheckState())
            else:
                self.districts.dlg_createNewProject.checkbox_db_defaultValues.setCheckState(uncheckState())
                self.districts.dlg_createNewProject.checkbox_invokedFeatures.setCheckState(checkState())
                self.districts.dlg_createNewProject.checkbox_prn.setCheckState(checkState())
                self.districts.dlg_createNewProject.checkbox_DBResults.setCheckState(checkState())
            
            createNewProject(self.districts.dlg_createNewProject,self.districts)
            self.process_wait(self.districts.dlg_createNewProject,max_sec=15)
            print('++create project finished++')

            print(self.districts.config)
            print(self.districts.cur)
            

            
            if project in ['DB default values','Empty project']:
                print('--Start create version: base1--')
                self.districts.dlg_addBase=IDA_Districts_NameDialog('Add base version','Add base version:','','')
                self.districts.dlg_addBase.input.setText('base1')
                addBaseVersion(self.districts.dlg_addBase,self.districts)
                print('++Create version finished++')
        
            #test preprocessing
            if project in ['DB default values','Empty project']:
                print('--Start import streets--')
                self.districts.openImportDlg(default_path=self.districts.plugin_dir+"/samples/OSM/map_1.osm",title='Streets from OSM',ok_fn=self.districts.importStreetsFromOSM,extensions='*.osm')
                self.districts.dlg_import.checkBoxClearOldFeatures.setCheckState(checkState())
                self.districts.importStreetsFromOSM(self.districts.dlg_import)
                self.process_wait(self.districts.dlg_import,max_sec=10)
                closeDialog(self.districts.dlg_import)
                print('--Import streets finished--')
                
                print('--Start import buildings--')
                self.districts.openImportDlg(default_path=self.districts.plugin_dir+"/samples/OSM/map_1.osm",title='Buildings from OSM',ok_fn=self.districts.importBuildingsFromOSM,extensions='*.osm')
                self.districts.dlg_import.checkBoxClearOldFeatures.setCheckState(checkState())
                self.districts.importBuildingsFromOSM(self.districts.dlg_import)
                self.process_wait(self.districts.dlg_import,max_sec=10)
                closeDialog(self.districts.dlg_import)
                print('--Import buildings finished--')
                
                print('--Start import eleveation data--')
                self.districts.openImportDlg(default_path=self.plugin_dir+"/samples/elevation_data/N59E017.hgt",title='Elevation data',ok_fn=self.districts.importElevationData,extensions='*.hgt;*.tif;*.tiff')
                self.districts.dlg_import.checkBoxClearOldFeatures.setCheckState(checkState())
                self.districts.importElevationData(self.districts.dlg_import)
                self.process_wait(self.districts.dlg_import,max_sec=30)
                print('++import N59E017.hgt finished++')
                self.districts.openImportDlg(default_path=self.plugin_dir+"/samples/elevation_data/N59E018.hgt",title='Elevation data',ok_fn=self.districts.importElevationData,extensions='*.hgt;*.tif;*.tiff')
                self.districts.dlg_import.checkBoxClearOldFeatures.setCheckState(uncheckState())
                self.districts.importElevationData(self.districts.dlg_import)
                self.process_wait(self.districts.dlg_import,max_sec=30)
                closeDialog(self.districts.dlg_import)
                print('++import N59E018.hgt finished++')
                
                #place main energy plant
                addMainPlant()
            
                print('--start pipe laying algorithm--')
                self.districts.pipeLayingAlgorithm()
                self.districts.dlg_pipeLayingAlgorithm.check_heating_network.setCheckState(checkState())
                self.districts.dlg_pipeLayingAlgorithm.execute()
                self.process_wait(self.districts.dlg_pipeLayingAlgorithm,max_sec=10)
                self.districts.dlg_pipeLayingAlgorithm.saveResults()
                closeDialog(self.districts.dlg_pipeLayingAlgorithm)
                print('++pipe laying algorithm finished++')
                
            
            if project in ['Heating network']:
                print('--start generate network topology--')
                self.districts.generateNetworkTopology()
                self.districts.window_topology.rbtn_override_templates.setChecked(True)
                self.districts.window_topology.check_del_network_ends.setCheckState(checkState())
                self.districts.window_topology.check_connectCustomers.setCheckState(checkState())
                self.districts.window_topology.check_connectPlants.setCheckState(checkState())
                self.districts.window_topology.check_deleteUnconnectedCustomers.setCheckState(checkState())
                self.districts.window_topology.check_deleteUnconnectedLines.setCheckState(checkState())
                self.districts.window_topology.check_connectPlants.setCheckState(checkState())
                self.districts.window_topology.combo_network_models.setItemChecked(1,True) 
                
                self.districts.window_topology.execute()
                self.process_wait(self.districts.window_topology,max_sec=10)
                self.districts.window_topology.saveResults()
                closeDialog(self.districts.window_topology)
                print('++generate network topology finished++')
            
            #pipe sizing
            print('--start pipe sizing--')
            if project in ['DB default values','Empty project']:
                fid=1
                self.loadAttribute=ShowLoadAttributeDialog(fid)
                self.loadAttribute.dlg.radioButton_newAttribute.setChecked(True)
                self.loadAttribute.dlg.lineEdit_newAttribute.setText('load_w')
                self.loadAttribute.dlg.checkBox_allCustomers.setChecked(True)
                setLoadAttribute(self.loadAttribute.dlg,fid)
                
            self.districts.pipeSizing()
            self.districts.dlg_pipeSizing.addRow()
            self.districts.dlg_pipeSizing.table_circuits.item(0,1).setText('70')
            self.districts.dlg_pipeSizing.table_circuits.item(0,4).setText('40')
            self.districts.dlg_pipeSizing.table_circuits.selectRow(0)
            self.districts.dlg_pipeSizing.table_circuits.selectColumn(3)
            self.districts.dlg_pipeSizing.table_circuits.cellWidget(0,3).setCurrentText('2')
            self.districts.dlg_pipeSizing.table_circuits.cellWidget(0,5).setCurrentText('load_w')
            for row in range(self.districts.dlg_pipeSizing.table_sequences.rowCount()):
                self.districts.dlg_pipeSizing.table_sequences.cellWidget(row,1).setAllItemsChecked(checked=True)
            startPipeSizing(self.districts.config,self.districts.dlg_pipeSizing,self.districts.plugin_dir)
            self.process_wait(self.districts.dlg_pipeSizing,max_sec=10)
            savePipeSizingResults(self.districts.config,self.districts.conn,self.districts.dlg_pipeSizing)
            closeDialog(self.districts.dlg_pipeSizing)
            print('--pipe sizing finished--')
            
            #test modelling and simulation          
            if project in ['DB default values','Empty project']:
                #set requested outputs
                print('--start set requested outputs--')
                self.districts.showRequestedOutputs()
                self.districts.dlg_outputs.checkBoxSubstationPower.setChecked(True)
                self.districts.dlg_outputs.checkBoxSubstationConnTemp.setChecked(True)
                self.districts.dlg_outputs.checkBoxSubstationPressure.setChecked(True)
                self.districts.dlg_outputs.checkBoxSubstationMassflow.setChecked(True)
                self.districts.dlg_outputs.checkBoxSubstationHeatbalance.setChecked(True)
                self.districts.dlg_outputs.checkBoxSubstationTair.setChecked(True)
                self.districts.dlg_outputs.checkBoxPressureDistribution.setChecked(True)
                self.districts.dlg_outputs.checkBoxMdotNode.setChecked(True)
                self.districts.dlg_outputs.checkBoxVPipe.setChecked(True)
                self.districts.dlg_outputs.checkBoxTempPipe.setChecked(True)
                self.districts.dlg_outputs.checkBoxPlantPower.setChecked(True)
                self.districts.dlg_outputs.checkBoxPlantConnTemp.setChecked(True)
                self.districts.dlg_outputs.checkBoxPlantPressure.setChecked(True)
                self.districts.dlg_outputs.checkBoxPlantMassflow.setChecked(True)
                self.districts.dlg_outputs.outputTimestep.setText('0.25')
                setRequestedOutputs(self.districts.config,self.plugin_dir,self.districts.dlg_outputs,self.districts.requestedOutputs)
                self.process_wait(self.districts.dlg_outputs,max_sec=10)      
                closeDialog(self.districts.dlg_outputs)
                print('++set requested outputs finished++')
            
            if project in ['Heating network']:
                #feature parameter mapping
                print('--start feature parameter mapping--')
                self.districts.showParmMapping()
                self.districts.dlg_featureParm.tableWidget_parameters.setRowCount(0)
                setFeatureParm(self.districts.dlg_featureParm,self.districts.conn,self.districts.config,self.plugin_dir)
                addParmTableRow(self.districts.dlg_featureParm,self.districts.cur,self.districts.config)
                self.districts.dlg_featureParm.tableWidget_parameters.item(0,1).setText('"load_w"')
                self.districts.dlg_featureParm.tableWidget_parameters.item(0,3).setText('FloorArea')
                self.districts.dlg_featureParm.tableWidget_parameters.item(0,4).setText('Lm_H_G_L_Mctrl')
                self.districts.dlg_featureParm.tableWidget_parameters.item(0,5).setText(':FEATURE')
                
                addParmTableRow(self.districts.dlg_featureParm,self.districts.cur,self.districts.config)
                self.districts.dlg_featureParm.tableWidget_parameters.item(0,1).setText('"gfa"')
                self.districts.dlg_featureParm.tableWidget_parameters.item(0,3).setText('X')
                self.districts.dlg_featureParm.tableWidget_parameters.item(0,4).setText('Load limit')
                self.districts.dlg_featureParm.tableWidget_parameters.item(0,5).setText(':FEATURE')
                setFeatureParm(self.districts.dlg_featureParm,self.districts.conn,self.districts.config,self.plugin_dir)
                closeDialog(self.districts.dlg_featureParm)
                print('++feature parameter mapping finished++')
                
            
            print('--start build network model--')
            self.districts.showBuildModel()
            self.districts.dlg_buildModel.combo_network_models.setItemChecked(1,True) 
            self.districts.dlg_buildModel.combo_submodels.setItemChecked(1,True) 
            buildModel(self.districts.dlg_buildModel,self.districts)
            self.process_wait(self.districts.dlg_buildModel,max_sec=10)      
            closeDialog(self.districts.dlg_buildModel)
            self.wait(1000)
            print('++build network model finished++')
            
            
            #test run simulation
            print('--start simulation--')
            #batch mode: "C:\Program Files (x86)\IDA52\bin\ida-ice.exe" "C:\Program Files (x86)\IDA52\bin\ida.img" -C ida1 -W hidden -B "C:\Users\Peter\AppData\Roaming\QGIS\QGIS3\profiles\default\python\plugins\ida_mosim\models\test0013\base1\log.txt" -X "C:\Users\Peter\AppData\Roaming\QGIS\QGIS3\profiles\default\python\plugins\ida_mosim\models\test0013\base1\network_1_script.txt"
            #(:set doc_ (:call get-document "C:\\Users\\Peter\\AppData\\Roaming\\QGIS\\QGIS3\\profiles\\default\\python\\plugins\\ida_mosim\\models\\test0013\\base1\\network_1.idm"))  
            #(:show doc_)
            #(RUN-SIMULATION doc_)
            #(save-document doc_ )
            #(exit-ida)
            self.districts.showRunModel()
            self.districts.dlg_runModel.combo_submodels.setItemChecked(1,checked=True)
            runModel(self.districts.dlg_runModel,self.districts.plugin_dir,self.districts.config)
            self.process_wait(self.districts.dlg_runModel,max_sec=70)
            print('--simulation finished--')

            print('--start load results--')
            self.districts.showLoadResults()
            self.districts.dlg_loadResults.combo_submodels.setItemChecked(1,True) 
            loadResults(self.districts.dlg_loadResults,self.districts)
            self.process_wait(self.districts.dlg_loadResults,max_sec=55)      
            closeDialog(self.districts.dlg_loadResults)
            print('++load results finished++')
            
            
            #test result visualization                    
            print('--start show data on map--')
            self.districts.showDataOnMap()
            #customer load values
            self.districts.dlg_showOnMap.rbtn_customers.setChecked(True)
            self.districts.dlg_showOnMap.checkbox_varColor.setChecked(True)
            self.districts.dlg_showOnMap.color_var.setCurrentText('power$1_1')
            self.districts.dlg_showOnMap.color_function.setCurrentText('Values')
            self.districts.dlg_showOnMap.checkbox_varSize.setChecked(True)
            self.districts.dlg_showOnMap.rbtn_sizePar.setChecked(True)
            self.districts.dlg_showOnMap.size_par.setCurrentText('gfa')
            self.districts.dlg_showOnMap.layer_name.setText('customer_results_load_values')
            self.wait(1000)
            showOnMap(self.districts.dlg_showOnMap,self.districts)
            self.process_wait(self.districts.dlg_showOnMap,max_sec=15)
            closeDialog(self.districts.dlg_showOnMap)
            
            #lines supply temperature
            self.districts.showDataOnMap()
            self.districts.dlg_showOnMap.rbtn_lines.setChecked(True)
            self.districts.dlg_showOnMap.checkbox_varColor.setChecked(True)
            self.districts.dlg_showOnMap.featureGroupChanged(self.districts.dlg_showOnMap.rbtn_lines)
            self.districts.dlg_showOnMap.color_var.setCurrentText('temp$1')
            self.districts.dlg_showOnMap.color_function.setCurrentText('Values')
            self.districts.dlg_showOnMap.layer_name.setText('lines_results_supply_temperature_values')
            self.wait(2000)
            showOnMap(self.districts.dlg_showOnMap,self.districts)
            self.process_wait(self.districts.dlg_showOnMap,max_sec=15)
            #closeDialog(self.districts.dlg_showOnMap)
            print('++show data on map finished++')
            
            print('--start path report--')
            self.districts.showPathReports()
            self.districts.dlg_pathReports.rbtn_pathPressure.setChecked(True)
            self.districts.dlg_pathReports.rbtn_weakPoint.setChecked(True)
            self.districts.dlg_pathReports.rbtn_Date.setChecked(True)
            self.districts.dlg_pathReports.date_input.setText('2024-01-01 07:00:00')
            self.districts.dlg_pathReports.dp_recalc.setChecked(True)
            self.districts.dlg_pathReports.dp_min_recalc.setText('0.8')
            
            self.districts.dlg_pathReports.sup_sequence.setCurrentIndex(0)
            self.districts.dlg_pathReports.ret_sequence.setCurrentIndex(1)
            runPathReports(self.districts.dlg_pathReports,self.districts)
            self.process_wait(self.districts.dlg_loadResults,max_sec=10)
            print('++path report finished++')
            self.wait(1000)         
            
            # #test delete project
            # print('--delete project started--')
            # deleteProject(projectName,self.districts.dlg,self.districts.cur_postgres,self.districts.plugin_dir,self.districts.config,self.districts.model)
            # print('++delete project finished++')
            
Autotest()
print('--finished testing--')
