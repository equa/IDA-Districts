
from plugins.ida_districts_project_handling.IDA_districts_project_handling import *
from plugins.ida_districts_preprocessing.ida_districts_preprocessing import *
from plugins.ida_districts_preprocessing.osm import *
from plugins.ida_districts_preprocessing.GenerateNetworkTopology import *
from plugins.ida_districts_modeling_simulation.ida_districts_modeling_simulation import *

from qgis.PyQt.QtCore import Qt
from qgis.PyQt.QtCore import QTimer,QEventLoop
import psycopg2.extras
import psycopg2
import copy
from plugins.utility_functions.db import *
import sys, os, importlib

from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT
            
class Autotest:
    def __init__(self):
        self.plugin_dir="""C:\\Users\\Peter\\AppData\\Roaming\\QGIS\\QGIS3\\profiles\\default\\python\\plugins\\"""
        self.dictDB={'pwd' : 'p3t3r' , 'host' : 'localhost','port':'5433', 'user' : 'postgres', 'projectName' : 'owa24062025', 'versionName' : 'd_opt_v5'}
        #dictDB=getDBConnectionData(plugin_dir)
        self.conn=dbConnect(self.dictDB,True)
        self.cur=self.conn.cursor(cursor_factory = psycopg2.extras.RealDictCursor)
        print(self.cur)
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
        self.ph=IDA_Districts_ProjectHandling(iface)
        self.ph.first_start=True
        self.ph.run()

        templates=['Heating network','Empty project','DB default values','Co-sim buildings with heating network']
        for project in [templates[0]]:
            print('++++++++++++'+project+'+++++++++++++')
            
            #test create project
            self.ph.showCreateNewProject()
            projectName='autotest_'+project.replace(' ','_').lower()
            self.ph.dlg_createNewProject.project_name.setText(projectName)
            self.ph.dlg_createNewProject.selectTemplate.setCurrentText(project)
            if project in ['DB default values','Empty project']:
                self.ph.dlg_createNewProject.checkbox_db_defaultValues.setCheckState(Qt.Checked)
                self.ph.dlg_createNewProject.checkbox_invokedFeatures.setCheckState(Qt.Unchecked)
                self.ph.dlg_createNewProject.checkbox_prn.setCheckState(Qt.Unchecked)
                self.ph.dlg_createNewProject.checkbox_DBResults.setCheckState(Qt.Unchecked)
            else:
                self.ph.dlg_createNewProject.checkbox_db_defaultValues.setCheckState(Qt.Unchecked)
                self.ph.dlg_createNewProject.checkbox_invokedFeatures.setCheckState(Qt.Checked)
                self.ph.dlg_createNewProject.checkbox_prn.setCheckState(Qt.Checked)
                self.ph.dlg_createNewProject.checkbox_DBResults.setCheckState(Qt.Checked)
            
            self.ph.createNewProject(self.ph.dlg_createNewProject)
            self.process_wait(self.ph,max_sec=60)
            print('++create project finished++')
            
            
            #test preprocessing
            self.pp=IdaDistrictsPreProcessing(iface)
            self.pp.first_start=True
            self.pp.run()
            
            if project in ['DB default values']:
                print('--Start import streets--')
                self.pp.openImportDlg(default_path=getDataCenterDir(self.plugin_dir)+"/Samples/OSM/map_1.osm",title='Streets from OSM',ok_fn=self.pp.importStreetsFromOSM,extensions='*.osm')
                self.pp.dlg_import.checkBoxClearOldFeatures.setCheckState(Qt.Checked)
                self.pp.importStreetsFromOSM(self.pp.dlg_import)
                closeDialog(self.pp.dlg_import)
                
                print('--Start import buildings--')
                self.pp.openImportDlg(default_path=getDataCenterDir(self.plugin_dir)+"/Samples/OSM/map_1.osm",title='Buildings from OSM',ok_fn=self.pp.importBuildingsFromOSM,extensions='*.osm')
                self.pp.dlg_import.checkBoxClearOldFeatures.setCheckState(Qt.Checked)
                self.pp.importStreetsFromOSM(self.pp.dlg_import)
                closeDialog(self.pp.dlg_import)
                
                print('--Start import eleveation data--')
                self.pp.openImportDlg(default_path=getDataCenterDir(self.plugin_dir)+"/Samples/elevation_data/N59E017.hgt",title='Elevation data',ok_fn=self.pp.importElevationData,extensions='*.hgt;*.tif;*.tiff')
                self.pp.dlg_import.checkBoxClearOldFeatures.setCheckState(Qt.Checked)
                self.pp.importStreetsFromOSM(self.pp.dlg_import)
                closeDialog(self.pp.dlg_import)
                print('++import finished++')
            
            if project in ['Heating network','Co-sim buildings with heating network']:
                print('--start generate network topology--')
                self.pp.generateNetworkTopology()
                self.pp.window_topology.rbtn_override_templates.setChecked(True)
                self.pp.window_topology.check_del_network_ends.setCheckState(Qt.Checked)
                self.pp.window_topology.check_connectCustomers.setCheckState(Qt.Checked)
                self.pp.window_topology.check_connectPlants.setCheckState(Qt.Checked)
                self.pp.window_topology.check_deleteUnconnectedCustomers.setCheckState(Qt.Checked)
                self.pp.window_topology.check_deleteUnconnectedLines.setCheckState(Qt.Checked)
                self.pp.window_topology.check_connectPlants.setCheckState(Qt.Checked)
                self.pp.window_topology.combo_network_models.setItemChecked(1,True) 
                
                self.pp.window_topology.execute()
                self.process_wait(self.pp.window_topology,max_sec=10)
                self.pp.window_topology.saveResults()
                closeDialog(self.pp.window_topology)
                print('++generate network topology finished++')
            
            
            #test modelling and simulation          
            self.mosim= IDADistrictsModelingSimulation(iface)
            self.mosim.first_start=True
            self.mosim.run()
            
            print('--start build network model--')
            self.mosim.showBuildModel()
            self.mosim.dlg_buildModel.combo_network_models.setItemChecked(1,True) 
            self.mosim.dlg_buildModel.combo_submodels.setItemChecked(1,True) 
            self.mosim.buildModel(self.mosim.dlg_buildModel)
            self.process_wait(self.mosim.dlg_buildModel,max_sec=10)      
            closeDialog(self.mosim.dlg_buildModel)
            print('++build network model finished++')
            
            
            print('--start load results--')
            self.mosim.showLoadResults()
            self.mosim.dlg_loadResults.combo_submodels.setItemChecked(1,True) 
            self.mosim.loadResults(self.mosim.dlg_loadResults)
            self.process_wait(self.mosim.dlg_loadResults,max_sec=10)      
            closeDialog(self.mosim.dlg_loadResults)
            print('++load results finished++')
            

            #test delete project
            
            print('--delete project started--')
            self.ph.deleteProject(projectName)
            print('++delete project finished++')
            
            

Autotest()
print('--finished testing--')
