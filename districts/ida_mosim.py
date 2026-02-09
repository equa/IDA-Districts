from qgis.PyQt.QtCore import QThreadPool

from .utility_functions.files import *
from .utility_functions.dialog import *
from .utility_functions.workers import *
from .outputs import WorkerSetRequestedOutputs
from .invoke_network import WorkerBuildNetworkModel

def checkSimOutputs(invokedOutputs,requestedOutputs):
    #check customers plants
    for type in ['customers','energy_plants']:
        for i in invokedOutputs['customers']:
            for j in invokedOutputs['customers'][i]:
                if invokedOutputs['customers'][i][j]!=requestedOutputs[j]:
                    return False
    
    #check lines
    for i in invokedOutputs['lines']:
        if invokedOutputs['lines'][i]!=requestedOutputs[i]:
            return False
    
    return True
        
def openModel(dlg,plugin_dir,config,mode='network'):
    print('-***-')
    if len([i for i in range(dlg.combo_submodels.count()) if dlg.combo_submodels.itemText(i) != 'Check all items' and dlg.combo_submodels.itemChecked(i)])==0:
        iface.messageBar().pushMessage("Info", "Please select one or more submodels!", level=Qgis.Info)
        return False
    requestedOutputs=loadRequestedOutputs(plugin_dir,config)
    for i in range(dlg.combo_submodels.count()):
        if dlg.combo_submodels.itemText(i) != 'Check all items' and dlg.combo_submodels.itemChecked(i):        
            submodel=dlg.combo_submodels.itemText(i)
            print(submodel)
            dir=plugin_dir+'\\projects\\{}\\models\\{}\\'.format(config['projectName'],config['versionName'])
            fname=dir+'{}_{}.idm'.format(mode,submodel)
            print(fname)
            worker_openNetwork = WorkerOpenModelCmd(fname,plugin_dir,config,submodel=submodel)
            threadpool_openNetwork = QThreadPool()
            threadpool_openNetwork.start(worker_openNetwork) 
            worker_openNetwork.signals.error.connect(show_error_message)
            worker_openNetwork.signals.progress.connect(dlg.update_progress)
            worker_openNetwork.signals.finished.connect(dlg.update_finished)

def setNetworkSimData(dlg,plugin_dir,config):
    """run network simulation"""
    print("run network simulation")
    networkSimData={}
    #-----------calc type------------
    if dlg.rbtn_calc_type_periodic.isChecked():
        networkSimData['calc_type']='periodic'
    else:
        networkSimData['calc_type']='dynamic'
    
    #-----------startup type------------
    if dlg.rbtn_startup_type_periodic.isChecked():
        networkSimData['startup_type']='periodic'
    else:
        networkSimData['startup_type']='dynamic'

    networkSimData['numb_of_periods']=dlg.numb_periods.text()
    networkSimData['startup_time_from']=dlg.dateedit_startupFrom.text()
    networkSimData['startup_time_to']=dlg.dateedit_startupTo.text()
    networkSimData['calc_time_from']=dlg.dateedit_calcFrom.text()
    networkSimData['calc_time_to']=dlg.dateedit_calcTo.text()
    if not is_number(dlg.max_timestep.text()):
        iface.messageBar().pushMessage("Warning", "Please enter a number as maximal timestep!", level=Qgis.Warning)
        return False
    else:
        networkSimData['max_timestep']=dlg.max_timestep.text()
    print(networkSimData)                
    writeNetworkSimData(plugin_dir,config,networkSimData)
    return networkSimData
        
def runModel(dlg,plugin_dir,config):
    networkSimData=setNetworkSimData(dlg,plugin_dir,config)
    if networkSimData:
        print('-***-')
        dlg.n_sims=len([i for i in range(dlg.combo_submodels.count()) if dlg.combo_submodels.itemText(i) != 'Check all items' and dlg.combo_submodels.itemChecked(i)])
        if dlg.n_sims==0:
            iface.messageBar().pushMessage("Info", "Please select one or more submodels!", level=Qgis.Info)
            return False
        requestedOutputs=loadRequestedOutputs(plugin_dir,config)
        invokedOutputs=loadInvokedOutputs(plugin_dir,config)
        if checkSimOutputs(invokedOutputs,requestedOutputs):
            dlg.updateStatusBar('Running')
            worker_runNetwork={}
            threadpool_runNetwork = QThreadPool()
            dlg.finished_sims=0
            dlg.process_running=True
            for i in range(dlg.combo_submodels.count()):
                if dlg.combo_submodels.itemText(i) != 'Check all items' and dlg.combo_submodels.itemChecked(i):        
                    submodel=dlg.combo_submodels.itemText(i)
                    print(submodel)
            
                    print('----Update simulation data----')
                    dir=plugin_dir+'\\projects\\{}\\models\\{}\\'.format(config['projectName'],config['versionName'])
                    fname=dir+'network_{}.idm'.format(submodel)
                    print(fname)
                    components_idm=propertyListCompsIDM(getIDAListComponents(readFileToString(fname)))
                    
                    data_idm=[]
                    for comp in components_idm:
                        print(comp)
                        if getCompClass(comp)=='SIMULATION_DATA':
                            print('++++++++simulation data+++++++')
                            data_idm.append(propertyListCompsIDM(getIDAListComponents(getSimData(requestedOutputs,networkSimData))))             
                        else:
                            data_idm.append(comp) 
                    
                    writePropertyListIDMToFile(data_idm,dir,fname)
                    writeSimulatedOutputs(plugin_dir,config,requestedOutputs)
                    
                    worker_runNetwork[i] = WorkerSimulateAPI(fname,plugin_dir,config)
                    threadpool_runNetwork.start(worker_runNetwork[i]) 
                    worker_runNetwork[i].signals.error.connect(dlg.show_error_message)
                    worker_runNetwork[i].signals.status.connect(dlg.updateStatusBar)   
                    worker_runNetwork[i].signals.finished.connect(dlg.update_finished)   
        else:
            iface.messageBar().pushMessage("Info", "The requested outputs differ from the invoked outputs. Please reinvoke the templates.", level=Qgis.Info)

def buildModel(dlg,main):
    networks=[]
    for i in range(dlg.combo_network_models.count()):
        if dlg.combo_network_models.itemText(i) != 'Check all items' and dlg.combo_network_models.itemChecked(i):        
            networks.append(dlg.combo_network_models.itemText(i))
                
    print(networks)
    submodels=[dlg.combo_submodels.itemText(i) for i in range(dlg.combo_submodels.count()) if dlg.combo_submodels.itemText(i) != 'Check all items' and dlg.combo_submodels.itemChecked(i)]
    print(submodels)
    if networks and submodels:
        worker_invokeNetwork = WorkerBuildNetworkModel(config=main.config,plugin_dir=main.plugin_dir,dlg=dlg,networks=networks,submodels=submodels)
        threadpool_invokeNetwork = QThreadPool()
        threadpool_invokeNetwork.start(worker_invokeNetwork) 
        worker_invokeNetwork.signals.error.connect(show_error_message)
        worker_invokeNetwork.signals.progress.connect(dlg.update_progress)   
        worker_invokeNetwork.signals.finished.connect(dlg.update_finished)   
    else:
        iface.messageBar().pushMessage("Info", "Please select one or more submodels and one or more networks!", level=Qgis.Info)

def setRequestedOutputs(config,plugin_dir,dlg,requestedOutputs):
    """set requested outputs"""
    print("set requested outputs")
    print(config)
    worker_setRequestedOutputs = WorkerSetRequestedOutputs(config=config,plugin_dir=plugin_dir,dlg=dlg,requestedOutputs=requestedOutputs)
    worker_setRequestedOutputs.signals.error.connect(show_error_message)
    worker_setRequestedOutputs.signals.progress.connect(dlg.update_progress)   
    #worker_setRequestedOutputs.signals.finished.connect(dlg.update_finished)  
    threadpool_requestedOutputs = QThreadPool()
    threadpool_requestedOutputs.start(worker_setRequestedOutputs) 

def setModellingSettings(plugin_dir,config,dlg):
    """set modelling settings"""
    print("set modelling settings")
    modellingSettings={}
    #pipe settings
    #-------------fd pipe------------
    modellingSettings['fd_meterPerNode']=dlg.fd_meterPerNode.text()
    #-------------node------------
    modellingSettings['node_vol']=dlg.node_vol.text()
    
    #ambient settings
    #ground settings
    modellingSettings['ground_lambda']=dlg.ground_lambda.text() 
    #-------------ground model------------
    modellingSettings['ground_model']=dlg.amb_ground_model.currentText() 

    #-------------kusuda------------
    #-------------tsurfmean------------
    modellingSettings['kusuda_tsurfmean']=dlg.amb_kusuda_tsurfmean.text()
    #-------------tsurfampl------------
    modellingSettings['kusuda_tsurfampl']=dlg.amb_kusuda_tsurfampl.text()  
    #-------------theta------------
    modellingSettings['kusuda_theta']=dlg.amb_kusuda_theta.text()     
    #-------------rho------------
    modellingSettings['kusuda_rho']=dlg.amb_kusuda_rho.text()       
    #-------------cp------------
    modellingSettings['kusuda_cp']=dlg.amb_kusuda_cp.text()  
    #-------------lambda------------
    modellingSettings['kusuda_lambda']=dlg.amb_kusuda_lambda.text()   
    #-------------depth------------
    modellingSettings['kusuda_depth']=dlg.amb_kusuda_depth.text()

    #-------------profile------------
    modellingSettings['ground_timeseries']=dlg.amb_ground_profile.currentText()
    
    #-------------temperatur------------
    modellingSettings['ground_temp']=dlg.amb_ground_temp.text()
    
    #duct settings
    #-------------duct model------------
    modellingSettings['duct_model']=dlg.amb_duct_model.currentText() 
    
    #-------------profile------------
    modellingSettings['duct_timeseries']=dlg.amb_duct_profile.currentText()
    
    #-------------temperatur------------
    modellingSettings['duct_temp']=dlg.amb_duct_temp.text()

    #ambient air settings
    #-------------air model------------
    modellingSettings['ambient_air_model']=dlg.amb_ambient_air_model.currentText()
    
    writeModellingSettings(plugin_dir,config,modellingSettings)
    closeDialog(dlg)    