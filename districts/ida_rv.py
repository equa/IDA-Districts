from qgis.utils import iface
from qgis.PyQt.QtCore import Qt,QThreadPool
from qgis.PyQt.QtWidgets import QListWidgetItem

from .utility_functions.workers import *
from .load_results import *
from .path_report import *

def getType(dlg):
    if dlg.rbtn_customer.isChecked():
        type='customer'
    elif dlg.rbtn_energy_plant.isChecked():
        type='energy_plant'
    return type

def getFeatureIds(dlg,cur,config):
    networks=[dlg.combo_networks.itemText(i) for i in range(dlg.combo_networks.count()) if dlg.combo_networks.itemChecked(i)]
    if networks:
        type=getType(dlg)
        sql="""SELECT id FROM "{}".{}s{} ORDER BY id;""".format(config['versionName'],type,' WHERE network && ARRAY['+','.join(networks)+']')
        cur.execute(sql)
        return [str(i['id']) for i in cur.fetchall()]
    else:
        return []
            
def loadFeatureIds(dlg,cur,config):
    dlg.listWidget_ids.clear()
    ids=getFeatureIds(dlg,cur,config)
    print(ids)
    dlg.listWidget_ids.addItems(ids)
        
def addSelectedIDs(dlg):
    """Adds all selected lines to list dlg.listWidget_ids"""
    print('add selected lines')
    layer = iface.activeLayer()
    if layer:
        print(layer.name())
        if layer.name()=='lines' and dlg.rbtn_lineIds.isChecked() or layer.name()=='customers' and dlg.rbtn_customer.isChecked():
            features = layer.selectedFeatures()
            print(features)
            for f in features:
                print(f['id'])
                item = QListWidgetItem(str(f['id']))
                item.setFlags(item.flags() | QtCore.Qt.ItemFlag.ItemIsEditable)
                dlg.listWidget_ids.addItem(item)

def addID(dlg):
    """Add id to list dlg.listWidget_ids"""
    print('add id')
    item = QListWidgetItem('')
    item.setFlags(item.flags() | QtCore.Qt.ItemFlag.ItemIsEditable)
    dlg.listWidget_ids.addItem(item)
            
def deleteIDs(dlg):
    listItems=dlg.listWidget_ids.selectedItems()
    if not listItems: return        
    for item in listItems:
        dlg.listWidget_ids.takeItem(dlg.listWidget_ids.row(item))
            
def loadResults(dlg,plugin_dir,config):
    submodels=[dlg.combo_submodels.itemText(i) for i in range(dlg.combo_submodels.count()) if dlg.combo_submodels.itemText(i) != 'Check all items' and dlg.combo_submodels.itemChecked(i)]
    
    simulatedOutputs=loadSimulatedOutputs(plugin_dir,config)
    if not simulatedOutputs:
        iface.messageBar().pushMessage("Info", "The project version is not yet simulated!", level=Qgis.Info)
        return False
        
    if dlg.checkbox_timestep.checkState() == Qt.CheckState.Checked:
        if not is_number(dlg.interpolation_dt.text()):
            iface.messageBar().pushMessage("Info", "Please enter a numerical interpolation time!", level=Qgis.Info)
            return False
        
    if submodels:
        worker_loadResults = WorkerLoadResults(config=config,plugin_dir=plugin_dir,dlg=dlg,submodels=submodels,simulatedOutputs=simulatedOutputs)
        threadpool_loadResults = QThreadPool()
        threadpool_loadResults.start(worker_loadResults) 
        worker_loadResults.signals.error.connect(show_error_message)
        worker_loadResults.signals.progress.connect(dlg.update_progress)   
        worker_loadResults.signals.finished.connect(dlg.update_finished)   
    else:
        iface.messageBar().pushMessage("Info", "Please select one or more submodels!", level=Qgis.Info)
  
def runPathReports(dlg,plugin_dir,config):
    worker_pathReport = WorkerPathReport(config=config,plugin_dir=plugin_dir,dlg=dlg)
            
    threadpool_pathReport = QThreadPool()
    worker_pathReport.signals.error.connect(show_error_message)
    worker_pathReport.signals.progress.connect(dlg.update_progress)  
    worker_pathReport.signals.finished.connect(dlg.update_finished)  
    threadpool_pathReport.start(worker_pathReport)   