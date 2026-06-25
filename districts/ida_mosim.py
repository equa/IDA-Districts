from qgis.PyQt.QtCore import QThreadPool

from .utility_functions.files import *
from .utility_functions.dialog import *
from .utility_functions.workers import *
from .supervisory_control import Supervisory_control

from .outputs import WorkerSetRequestedOutputs
from .invoke_network import WorkerBuildNetworkModel
    
import pandas as pd
import numpy as np

def addBoreholefieldTableRow(dlg,main):
    """Insert table row"""
    print('-------insert row---------------')
    dropdowns=[[20,'public','liquids','id','liquid']]

    maxId=max([getMaxIdAcrossSchemas(main.config,main.cur,'borehole_fields')+1]+[int(dlg.tableWidget.item(i,0).text())+1 for i in range(dlg.tableWidget.rowCount())])
    dlg.tableWidget.insertRow(0)
    dropdownItems=getDropDownItems(main.cur,dropdowns)

    item = QTableWidgetItem(str(maxId))
    try:
        item_is_editable = Qt.ItemFlag.ItemIsEditable  # Qt6
    except AttributeError:
        item_is_editable = Qt.ItemIsEditable           # Qt5

    item.setFlags(item.flags() & ~item_is_editable)
    dlg.tableWidget.setItem(0 , 0, item)
    
    comboBox = QComboBox()
    comboBox.addItems([str(i['id']) for i in getTableIds(main.cur,main.config['versionName'],'energy_plants','id')])
    dlg.tableWidget.setCellWidget(0, 1, comboBox) #plant id
    dlg.tableWidget.setItem(0,2,QTableWidgetItem('190')) #zhole
    dlg.tableWidget.setItem(0,3,QTableWidgetItem('0.0575')) #rhole
    dlg.tableWidget.setItem(0,4,QTableWidgetItem('0.039')) #RB
    dlg.tableWidget.setItem(0,5,QTableWidgetItem('0.001')) #RPIPEGROUT
    dlg.tableWidget.setItem(0,6,QTableWidgetItem('100')) #RPIPEEARTH
    dlg.tableWidget.setItem(0,7,QTableWidgetItem('0.0147')) #RGROUTGROUT
    dlg.tableWidget.setItem(0,8,QTableWidgetItem('0.0423')) #RGROUTEARTH
    dlg.tableWidget.setItem(0,9,QTableWidgetItem('0.0147')) #RRINGEARTH
    dlg.tableWidget.setItem(0,10,QTableWidgetItem('840')) #cpgrd
    dlg.tableWidget.setItem(0,11,QTableWidgetItem('3.8')) #lambgrd
    dlg.tableWidget.setItem(0,12,QTableWidgetItem('2880')) #rhogrd
    dlg.tableWidget.setItem(0,13,QTableWidgetItem('4180')) #cpgrout
    dlg.tableWidget.setItem(0,14,QTableWidgetItem('0.6')) #lambgrout
    dlg.tableWidget.setItem(0,15,QTableWidgetItem('1000')) #rhogrout
    dlg.tableWidget.setItem(0,16,QTableWidgetItem('0.016')) #rpipe
    dlg.tableWidget.setItem(0,17,QTableWidgetItem('0.0026')) #thickpipe
    dlg.tableWidget.setItem(0,18,QTableWidgetItem('2200')) #cppipe
    dlg.tableWidget.setItem(0,19,QTableWidgetItem('0.42')) #lambpipe
    comboBox = QComboBox()
    try:
        items={dropdownItems[20][i].split(':')[0] : tr("@default",dropdownItems[20][i].split(':')[1]) for i in dropdownItems[20]}
        # Add items to the comboBox, storing the original key as user data
        for original_key, translated_text in items.items():
            comboBox.addItem(translated_text, original_key) # The second argument is the userData
    except:
        comboBox.addItems(dropdownItems)
    dlg.tableWidget.setCellWidget(0, 20, comboBox) #liquid
    dlg.tableWidget.setItem(0,21,QTableWidgetItem('0')) #Tfreeze
    dlg.tableWidget.setItem(0,22,QTableWidgetItem('0.42')) #lambliq
    dlg.tableWidget.setItem(0,23,QTableWidgetItem('2')) #lcasting
    dlg.tableWidget.setItem(0,24,QTableWidgetItem('0.1')) #lambda
    dlg.tableWidget.setItem(0,25,QTableWidgetItem('1000')) #rhosurface
    dlg.tableWidget.setItem(0,26,QTableWidgetItem('4180')) #cpsurface
    dlg.tableWidget.setItem(0,27,QTableWidgetItem('0')) #mir
    dlg.tableWidget.setItem(0,28,QTableWidgetItem('100')) #rmax
    dlg.tableWidget.setItem(0,29,QTableWidgetItem('10')) #nring
    dlg.tableWidget.setItem(0,30,QTableWidgetItem('10')) #nzhole
    dlg.tableWidget.setItem(0,31,QTableWidgetItem('12')) #nlayt
    dlg.tableWidget.setItem(0,32,QTableWidgetItem('0')) #n1
    dlg.tableWidget.setItem(0,33,QTableWidgetItem('0')) #n2
    dlg.tableWidget.setItem(0,34,QTableWidgetItem('0')) #n3
    dlg.tableWidget.setItem(0,35,QTableWidgetItem('0')) #toutput
    dlg.tableWidget.setItem(0,36,QTableWidgetItem('5')) #tmean
    dlg.tableWidget.setItem(0,37,QTableWidgetItem('0')) #geotgrad

def setBoreholeFieldSettings(dlg):
    table=dlg.tableWidget
    boreholefieldsData={}
    
    sql=""
    for row in range(dlg.tableWidget.rowCount()):
        boreholefieldsData[int(table.item(row, 0).text())]={'ep_id': dlg.tableWidget.cellWidget(row, 1).currentText(),'zhole': table.item(row,2).text(),'rhole': table.item(row,3).text(),'rb': table.item(row,4).text(),
            'rpipegrout': table.item(row,5).text(),'rpipeearth': table.item(row,6).text(),'rgroutgrout': table.item(row,7).text(),'rgroutearth': table.item(row,8).text(), 'rringearth': table.item(row,9).text(),
            'cpgrd': table.item(row,10).text(),'lambgrd': table.item(row,11).text(),'rhogrd': table.item(row,12).text(),'cpgrout': table.item(row,13).text(),
            'lambgrout': table.item(row,14).text(),'rhogrout': table.item(row,15).text(),'rpipe': table.item(row,16).text(),'thickpipe': table.item(row,17).text(),
            'cppipe': table.item(row,18).text(),'lambpipe': table.item(row,19).text(),'liqtype': table.cellWidget(row, 20).currentText().split(':')[0],'tfreeze': table.item(row,21).text(),
            'lambliq': table.item(row,22).text(),'lcasting': table.item(row,23).text(),'lambda': table.item(row,24).text(),'rhosurface': table.item(row,25).text(),
            'cpsurface': table.item(row,26).text(),'mir': table.item(row,27).text(),'rmax': table.item(row,28).text(),'nring': table.item(row,29).text(),
            'nzhole': table.item(row,30).text(),'nlayt': table.item(row,31).text(),'n1': table.item(row,32).text(),'n2': table.item(row,33).text(),
            'n3': table.item(row,34).text(),'toutput': table.item(row,35).text(),'tmean': table.item(row,36).text(),'geotgrad': table.item(row,37).text()}
    
    print(self.loadedBoreholefieldsData)
    print(boreholefieldsData)
    
    #deleted
    for key_loaded in self.loadedBoreholefieldsData:
        if key_loaded not in boreholefieldsData: 
            print('removed sensor')
            sql+="""DELETE FROM "{}".borehole_fields WHERE id={};""".format(self.dictDB['versionName'],key_loaded)
    
    #added
    for key_table in boreholefieldsData:
        if key_table not in self.loadedBoreholefieldsData: 
            print('added field data')
            sql+="""INSERT INTO "{}".borehole_fields (id,ep_id,zhole,rhole,rb,rpipeearth,rpipegrout,rringearth,rgroutearth,rgroutgrout,mir,rmax,nring,nzhole,nlayt,n1,n2,n3,toutput,cpgrd,lambgrd,rhogrd,cpgrout,lambgrout,rhogrout,rpipe,thickpipe,cppipe,lambpipe,lcasting,lambda,rhosurface,cpsurface,liqtype,tfreeze,lambliq,tmean,geotgrad) VALUES({},{},{},{},{},{},{},{},{},{},{},{},{},{},{},{},{},{},{},{},{},{},{},{},{},{},{},{},{},{},{},{},{},'{}',{},{},{},{});\n""".format(
                self.dictDB['versionName'],key_table,boreholefieldsData[key_table]['ep_id'],boreholefieldsData[key_table]['zhole'],boreholefieldsData[key_table]['rhole'],
                boreholefieldsData[key_table]['rb'],boreholefieldsData[key_table]['rpipeearth'],boreholefieldsData[key_table]['rpipegrout'],boreholefieldsData[key_table]['rringearth'],
                boreholefieldsData[key_table]['rgroutearth'],boreholefieldsData[key_table]['rgroutgrout'],boreholefieldsData[key_table]['mir'],boreholefieldsData[key_table]['rmax'],
                boreholefieldsData[key_table]['nring'],boreholefieldsData[key_table]['nzhole'],boreholefieldsData[key_table]['nlayt'],boreholefieldsData[key_table]['n1'],
                boreholefieldsData[key_table]['n2'],boreholefieldsData[key_table]['n3'],boreholefieldsData[key_table]['toutput'],boreholefieldsData[key_table]['cpgrd'],
                boreholefieldsData[key_table]['lambgrd'],boreholefieldsData[key_table]['rhogrd'],boreholefieldsData[key_table]['cpgrout'],boreholefieldsData[key_table]['lambgrout'],
                boreholefieldsData[key_table]['rhogrout'],boreholefieldsData[key_table]['rpipe'],boreholefieldsData[key_table]['thickpipe'],
                boreholefieldsData[key_table]['cppipe'],boreholefieldsData[key_table]['lambpipe'],boreholefieldsData[key_table]['lcasting'],boreholefieldsData[key_table]['lambda'],               
                boreholefieldsData[key_table]['rhosurface'],boreholefieldsData[key_table]['cpsurface'],boreholefieldsData[key_table]['liqtype'],boreholefieldsData[key_table]['tfreeze'],               
                boreholefieldsData[key_table]['lambliq'],boreholefieldsData[key_table]['tmean'],boreholefieldsData[key_table]['geotgrad'])               
        else:   
            #Check for updated columns
            for col in ['ep_id','zhole','rhole','rb','rpipeearth','rpipegrout','rringearth','rgroutearth','rgroutgrout','mir','rmax','nring','nzhole','nlayt','n1','n2','n3','toutput','cpgrd','lambgrd','rhogrd','cpgrout','lambgrout','rhogrout','rpipe','thickpipe','cppipe','lambpipe','lcasting','lambda','rhosurface','cpsurface','liqtype','tfreeze','lambliq','tmean','geotgrad']:
                if self.loadedBoreholefieldsData[key_table][col]!=boreholefieldsData[key_table][col]:
                    sql+="""UPDATE "{}".borehole_fields SET {} = {} WHERE id = {} ;\n""".format(self.dictDB['versionName'],col,boreholefieldsData[key_table][col],key_table)   
    
    try:
        print(sql)
        self.cur.execute(sql)
        closeDialog(dlg)
    except Exception as e:
        self.iface.messageBar().pushMessage("Error", str(e), level=Qgis.Critical)

def showBoreholeFieldSettingsData(dlg,main):
    sql="""SELECT * FROM "{}".borehole_fields;""".format(main.config['versionName'])
    main.cur.execute(sql)
    boreholes_data=main.cur.fetchall()
    dropdowns=[[20,'public','liquids','id','liquid']]
    dlg.tableWidget.setRowCount(len(boreholes_data))
    boreholefieldsData={}

    for counter,i in enumerate(boreholes_data):
        print(counter)
        print(i)
        boreholefieldsData[i['id']]={'ep_id': str(i['id']),'zhole': str(i['zhole']),'rhole': str(i['rhole']),'rb': str(i['rb']),'rpipegrout': str(i['rpipegrout']),'rgroutearth': str(['rgroutearth']),'rpipeearth': str(i['rpipeearth']),
            'rgroutgrout': str(i['rgroutgrout']),'rringearth': str(i['rringearth']),'cpgrd': str(i['cpgrd']),'lambgrd': str(i['lambgrd']),'rhogrd': str(i['rhogrd']),'cpgrout': str(i['cpgrout']),'lambgrout': str(i['lambgrout']),
            'rhogrout': str(i['rhogrout']),'rpipe': str(i['rpipe']),'thickpipe': str(i['thickpipe']),'cppipe': str(i['cppipe']),'lambpipe': str(i['lambpipe']),'liqtype': str(i['liqtype']),'tfreeze': str(i['tfreeze']),
            'lambliq': str(i['lambliq']),'lcasting': str(i['lcasting']),'lambda': str(i['lambda']),'rhosurface': str(i['rhosurface']),'cpsurface': str(i['cpsurface']),'mir': str(i['mir']),'rmax': str(i['rmax']),
            'nring': str(i['nring']),'nzhole': str(i['nzhole']),'nlayt': str(i['nlayt']),'n1': str(i['n1']),'n2': str(i['n2']),'n3': str(i['n3']),'toutput': str(i['toutput']),'tmean': str(i['tmean']),'geotgrad': str(i['geotgrad'])}
        dropdownItems=getDropDownItems(main.cur,dropdowns)
        
        item = QTableWidgetItem(str(i['id'])) #id
        item.setFlags(item.flags() & ~Qt.ItemIsEditable)
        dlg.tableWidget.setItem(counter,0,item)
        comboBox = QComboBox()
        comboBox.addItems([str(ids['id']) for ids in getTableIds(main.cur,main.config['versionName'],'energy_plants','id')])
        comboBox.setCurrentText(str(i['id']))
        dlg.tableWidget.setCellWidget(counter, 1, comboBox) #plant id
        dlg.tableWidget.setItem(counter,2,QTableWidgetItem(str(i['zhole']))) #zhole
        dlg.tableWidget.setItem(counter,3,QTableWidgetItem(str(i['rhole']))) #rhole
        dlg.tableWidget.setItem(counter,4,QTableWidgetItem(str(i['rb']))) #RB
        dlg.tableWidget.setItem(counter,5,QTableWidgetItem(str(i['rpipegrout']))) #RPIPEGROUT
        dlg.tableWidget.setItem(counter,6,QTableWidgetItem(str(i['rpipeearth']))) #RPIPEEARTH
        dlg.tableWidget.setItem(counter,7,QTableWidgetItem(str(i['rgroutgrout']))) #RGROUTGROUT
        dlg.tableWidget.setItem(counter,8,QTableWidgetItem(str(i['rgroutearth']))) #RGROUTEARTH
        dlg.tableWidget.setItem(counter,9,QTableWidgetItem(str(i['rringearth']))) #RRINGEARTH
        dlg.tableWidget.setItem(counter,10,QTableWidgetItem(str(i['cpgrd']))) #cpgrd
        dlg.tableWidget.setItem(counter,11,QTableWidgetItem(str(i['lambgrd']))) #lambgrd
        dlg.tableWidget.setItem(counter,12,QTableWidgetItem(str(i['rhogrd']))) #rhogrd
        dlg.tableWidget.setItem(counter,13,QTableWidgetItem(str(i['cpgrout']))) #cpgrout
        dlg.tableWidget.setItem(counter,14,QTableWidgetItem(str(i['lambgrout']))) #lambgrout
        dlg.tableWidget.setItem(counter,15,QTableWidgetItem(str(i['rhogrout']))) #rhogrout
        dlg.tableWidget.setItem(counter,16,QTableWidgetItem(str(i['rpipe']))) #rpipe
        dlg.tableWidget.setItem(counter,17,QTableWidgetItem(str(i['thickpipe']))) #thickpipe
        dlg.tableWidget.setItem(counter,18,QTableWidgetItem(str(i['cppipe']))) #cppipe
        dlg.tableWidget.setItem(counter,19,QTableWidgetItem(str(i['lambpipe']))) #lambpipe
        comboBox = QComboBox()
        comboBox.addItems(dropdownItems[20])
        sql="SELECT liquid FROM liquids WHERE id = {};".format(i['liqtype'])
        main.cur.execute(sql)
        comboBox.setCurrentText(str(i['liqtype'])+':'+main.cur.fetchone()['liquid'])
        dlg.tableWidget.setCellWidget(counter, 20, comboBox) #liquid
        dlg.tableWidget.setItem(counter,21,QTableWidgetItem(str(i['tfreeze']))) #tfreeze
        dlg.tableWidget.setItem(counter,22,QTableWidgetItem(str(i['lambliq']))) #lambliq
        dlg.tableWidget.setItem(counter,23,QTableWidgetItem(str(i['lcasting']))) #lcasting
        dlg.tableWidget.setItem(counter,24,QTableWidgetItem(str(i['lambda']))) #lambda
        dlg.tableWidget.setItem(counter,25,QTableWidgetItem(str(i['rhosurface']))) #rhosurface
        dlg.tableWidget.setItem(counter,26,QTableWidgetItem(str(i['cpsurface']))) #cpsurface
        dlg.tableWidget.setItem(counter,27,QTableWidgetItem(str(i['mir']))) #mir
        dlg.tableWidget.setItem(counter,28,QTableWidgetItem(str(i['rmax']))) #rmax
        dlg.tableWidget.setItem(counter,29,QTableWidgetItem(str(i['nring']))) #nring
        dlg.tableWidget.setItem(counter,30,QTableWidgetItem(str(i['nzhole']))) #nzhole
        dlg.tableWidget.setItem(counter,31,QTableWidgetItem(str(i['nlayt']))) #nlayt
        dlg.tableWidget.setItem(counter,32,QTableWidgetItem(str(i['n1']))) #n1
        dlg.tableWidget.setItem(counter,33,QTableWidgetItem(str(i['n2']))) #n2
        dlg.tableWidget.setItem(counter,34,QTableWidgetItem(str(i['n3']))) #n3
        dlg.tableWidget.setItem(counter,35,QTableWidgetItem(str(i['toutput']))) #toutput
        dlg.tableWidget.setItem(counter,36,QTableWidgetItem(str(i['tmean']))) #tmean
        dlg.tableWidget.setItem(counter,37,QTableWidgetItem(str(i['geotgrad']))) #geotgrad
    return boreholefieldsData  
            
def openSupervisoryCtrl(cur,plugin_dir,config):
    Supervisory_control(plugin_dir,config)
    #setSupervisoryCrtlSubmodel(dlg,cur)
    file = config['pathProjects']+'{}\\versions\\{}\\supervisory_control\\supervisory_control.idm'.format(config['projectName'],config['versionName'])
    #print(file)
    worker_openSupervisory = WorkerOpenModelCmd(file,config)
    QThreadPool.globalInstance().start(worker_openSupervisory)
    worker_openSupervisory.signals.error.connect(show_error_message)
        
def setSupervisoryCrtlSubmodel(dlg,cur):
    sql="""UPDATE supervisory_ctrl SET submodel={};""".format(dlg.combo_submodel.currentText()) # nosec B608
    cur.execute(sql)
    closeDialog(dlg)
        
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
    #print('-***-')
    if len([i for i in range(dlg.combo_submodels.count()) if dlg.combo_submodels.itemText(i) != tr('@default','check_all_items') and dlg.combo_submodels.itemChecked(i)])==0:
        iface.messageBar().pushMessage("Info", "Please select one or more submodels!", level=Qgis.Info)
        return False
    requestedOutputs=loadRequestedOutputs(plugin_dir,config)
    for i in range(dlg.combo_submodels.count()):
        if dlg.combo_submodels.itemText(i) != tr('@default','check_all_items') and dlg.combo_submodels.itemChecked(i):        
            submodel=dlg.combo_submodels.itemText(i)
            #print(submodel)
            dir=config['pathProjects']+'{}\\versions\\{}\\'.format(config['projectName'],config['versionName'])
            fname=dir+'{}_{}.idm'.format(mode,submodel)
            #print(fname)
            worker_openNetwork = WorkerOpenModelCmd(fname,config,submodel=submodel)
            QThreadPool.globalInstance().start(worker_openNetwork) 
            worker_openNetwork.signals.error.connect(show_error_message)
            worker_openNetwork.signals.progress.connect(dlg.update_progress)
            worker_openNetwork.signals.finished.connect(dlg.update_finished)

def setNetworkSimData(dlg,plugin_dir,config):
    """run network simulation"""
    #print("run network simulation")
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
    #print(networkSimData)                
    writeNetworkSimData(config,networkSimData)
    return networkSimData
        
def runModel(dlg,plugin_dir,config):
    networkSimData=setNetworkSimData(dlg,plugin_dir,config)
    if networkSimData:
        dlg.n_sims=len([i for i in range(dlg.combo_submodels.count()) if dlg.combo_submodels.itemText(i) != tr('@default','check_all_items') and dlg.combo_submodels.itemChecked(i)])
        if dlg.n_sims==0:
            iface.messageBar().pushMessage("Info", "Please select one or more submodels!", level=Qgis.Info)
            return False
        requestedOutputs=loadRequestedOutputs(plugin_dir,config)
        invokedOutputs=loadInvokedOutputs(config)
        if checkSimOutputs(invokedOutputs,requestedOutputs):
            dlg.updateStatusBar('Running')
            worker_runNetwork={}
            dlg.finished_sims=0
            dlg.process_running=True
            for i in range(dlg.combo_submodels.count()):
                if dlg.combo_submodels.itemText(i) != tr('@default','check_all_items') and dlg.combo_submodels.itemChecked(i):        
                    submodel=dlg.combo_submodels.itemText(i)
            
                    #print('----Update simulation data----')
                    dir=config['pathProjects']+'{}\\versions\\{}\\'.format(config['projectName'],config['versionName'])
                    fname=dir+'network_{}.idm'.format(submodel)
                    #print(fname)
                    components_idm=propertyListCompsIDM(getIDAListComponents(readFileToString(fname)))
                    
                    data_idm=[]
                    for comp in components_idm:
                        #print(comp)
                        if getCompClass(comp)=='SIMULATION_DATA':
                            #print('++++++++simulation data+++++++')
                            data_idm.append(propertyListCompsIDM(getIDAListComponents(getSimData(requestedOutputs,networkSimData))))             
                        else:
                            data_idm.append(comp) 
                    
                    writePropertyListIDMToFile(data_idm,dir,fname,config)
                    writeSimulatedOutputs(config,requestedOutputs)
                    
                    worker_runNetwork[i] = WorkerSimulateAPI(fname,plugin_dir,config)
                    QThreadPool.globalInstance().start(worker_runNetwork[i]) 
                    worker_runNetwork[i].signals.error.connect(dlg.show_error_message)
                    worker_runNetwork[i].signals.status.connect(dlg.updateStatusBar)   
                    worker_runNetwork[i].signals.finished.connect(dlg.update_finished)   
        else:
            iface.messageBar().pushMessage("Info", "The requested outputs differ from the invoked outputs. Please reinvoke the templates.", level=Qgis.Info)

def buildModel(dlg,main):
    networks=[]
    for i in range(dlg.combo_network_models.count()):
        if dlg.combo_network_models.itemText(i) != tr('@default','check_all_items') and dlg.combo_network_models.itemChecked(i):        
            networks.append(dlg.combo_network_models.itemText(i))
                
    #print(networks)
    submodels=[dlg.combo_submodels.itemText(i) for i in range(dlg.combo_submodels.count()) if dlg.combo_submodels.itemText(i) != tr('@default','check_all_items') and dlg.combo_submodels.itemChecked(i)]
    #print(submodels)
    if networks and submodels:
        main.worker_invokeNetwork = WorkerBuildNetworkModel(config=main.config,plugin_dir=main.plugin_dir,dlg=dlg,networks=networks,submodels=submodels)
        QThreadPool.globalInstance().start(main.worker_invokeNetwork) 
        main.worker_invokeNetwork.signals.error.connect(show_error_message)
        main.worker_invokeNetwork.signals.progress.connect(dlg.update_progress)   
        main.worker_invokeNetwork.signals.finished.connect(dlg.update_finished)   
    else:
        iface.messageBar().pushMessage("Info", "Please select one or more submodels and one or more networks!", level=Qgis.Info)

def setRequestedOutputs(config,plugin_dir,dlg,requestedOutputs):
    """set requested outputs"""
    #print("set requested outputs")
    #print(config)
    worker_setRequestedOutputs = WorkerSetRequestedOutputs(config=config,plugin_dir=plugin_dir,dlg=dlg,requestedOutputs=requestedOutputs)
    worker_setRequestedOutputs.signals.error.connect(show_error_message)
    worker_setRequestedOutputs.signals.progress.connect(dlg.update_progress)   
    worker_setRequestedOutputs.signals.finished.connect(dlg.update_finished)  
    QThreadPool.globalInstance().start(worker_setRequestedOutputs) 

def calculateKusudaSettings(file,modellingSettings):
    # --------------------------------------------------
    # Read climate file
    # --------------------------------------------------

    # Try reading with header
    df = pd.read_csv(file, sep=r"\s+")

    # If no recognizable header exists,
    # assume:
    #   column 0 = time
    #   column 1 = ambient air temperature
    if "#Time" not in df.columns and "TAir" not in df.columns:

        df = pd.read_csv(
            file,
            sep=r"\s+",
            header=None
        )

        df = df.rename(
            columns={
                0: "#Time",
                1: "TAir"
            }
        )

    else:

        # Handle possible variations
        time_col = df.columns[0]

        tair_col = None
        for c in df.columns:
            if c.lower() in ["tair", "tair", "airtemp", "temperature"]:
                tair_col = c
                break

        if tair_col is None:
            raise ValueError("Could not identify air temperature column.")

        df = df.rename(
            columns={
                time_col: "#Time",
                tair_col: "TAir"
            }
        )

    # --------------------------------------------------
    # Create datetime index
    # --------------------------------------------------

    start = pd.Timestamp("2024-01-01 00:00:00")
    df["datetime"] = start + pd.to_timedelta(df["#Time"], unit="h")

    # Remove only the extra endpoint of the next year
    df = df[df["datetime"] < "2025-01-01"]

    df = df.set_index("datetime")

    # --------------------------------------------------
    # 1. Annual mean air temperature
    # --------------------------------------------------

    Tm = df["TAir"].mean()
    modellingSettings['TSurfMean']=round(Tm,2)

    # --------------------------------------------------
    # 2. Mean daily temperature amplitude
    # --------------------------------------------------

    daily_max = df["TAir"].resample("D").max()
    daily_min = df["TAir"].resample("D").min()

    mean_daily_amplitude = (daily_max - daily_min).mean() / 2
    modellingSettings['TSurfAmpl']=round(mean_daily_amplitude,2)

    # --------------------------------------------------
    # 3. Kusuda phase shift
    #    (2628000 s = 730 h trailing moving average)
    # --------------------------------------------------

    window_hours = int(2628000 / 3600)  # 730

    T = df["TAir"].values

    # cyclic extension using end of previous year
    T_ext = np.concatenate([
        T[-(window_hours - 1):],
        T
    ])

    moving_avg = (
        pd.Series(T_ext)
          .rolling(
              window=window_hours,
              min_periods=window_hours
          )
          .mean()
          .values
    )

    moving_avg = moving_avg[
        window_hours - 1 :
        window_hours - 1 + len(T)
    ]

    idx_min = np.nanargmin(moving_avg)

    phase_date = df.index[idx_min]
    phase_shift = (
        phase_date.dayofyear
        + phase_date.hour / 24
        + phase_date.minute / 1440
    )

    modellingSettings['Theta']=round(phase_shift,2)

    # --------------------------------------------------
    # Results
    # --------------------------------------------------
    #print(f"Annual mean temperature     = {Tm:.2f} °C")
    #print(f"Mean daily amplitude        = {mean_daily_amplitude:.2f} °C")
    #print(f"Kusuda phase shift          = {phase_shift:.2f} d")
    #print(f"Minimum date               = {phase_date}")
    
    return modellingSettings

def setModellingSettings(plugin_dir,config,dlg):
    """set modelling settings"""
    #print("set modelling settings")
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
    
    writeModellingSettings(config,modellingSettings)
    closeDialog(dlg)    
  
def buildBuildingModel(dlg):
                
    submodel_templates={dlg.tableWidget.cellWidget(i,0).currentText(): dlg.tableWidget.cellWidget(i,1).currentText() for i in range(dlg.tableWidget.rowCount())}

    if submodel_templates:
        #print(submodel_templates)
        config=getDBConnectionData(plugin_dir)
        conn=dbConnect(config,False)
        if conn:
            if config['versionName']:
                cur=conn.cursor(cursor_factory = psycopg2.extras.RealDictCursor)  
                for submodel in submodel_templates:
                    ida_scripts=[]
                    #print(submodel)
                    sql="""SELECT 
  (ST_XMax(ST_Extent(geom))-ST_XMin(ST_Extent(geom)))/2 + ST_XMin(ST_Extent(geom)) AS x_center, 
  (ST_YMax(ST_Extent(geom))-ST_YMin(ST_Extent(geom)))/2 + ST_YMin(ST_Extent(geom)) AS y_center
FROM {}.buildings
WHERE submodel={};""".format(config['versionName'],submodel) # nosec B608
                    cur.execute(sql)
                    center=cur.fetchone()
                    #print(center)
                    
                    sql="""SELECT b.id,b_id,z_id,ST_AsText(geom) AS geom,z_height_m,z_bh_m, win_facade_ratio, z_construction, zt.name AS z_template, u.name AS room_unit 
    FROM {}.buildings b, room_units u, zone_templates zt
    WHERE b.submodel={} AND u.id=b.room_unit AND zt.id=b.z_template
    ORDER BY b_id,z_id;""".format(config['versionName'],submodel) # nosec B608
                    #print(sql)
                    cur.execute(sql)
                    zones=cur.fetchall()
                    b_ids=set(str(zone["b_id"]) for zone in zones)
                    sql="""SELECT b.b_id,t.conn_bundle_type 
    FROM {}.buildings b,{}.customers c, customer_templates t
    WHERE b.b_id IN ({}) AND c.id=b.substation_id AND c.template=t.template
    GROUP BY t.conn_bundle_type, b.b_id;""".format(config['versionName'],config['versionName'],','.join(b_ids)) # nosec B608
                    cur.execute(sql)
                    conn_data={i['b_id']: getConnsValuesIdentTypeDict(cur,i['conn_bundle_type']) for i in cur.fetchall()}
                    #print(conn_data)
                    conn_data_alist="""'({})""".format(' '.join(["""({} . ({}))""".format(i,' '.join(['(:N "'+j +
                                                                                            '" :T ' + str(conn_data[i][j][':T'])+
                                                                                            ' :V-VAR '+str(conn_data[i][j][':V-VAR'])+
                                                                                            ' :VAR "'+str(conn_data[i][j][':VAR'])+
                                                                                            '" :V-T '+str(conn_data[i][j][':V-T'])+')' for j in conn_data[i]])) for i in conn_data]))
                    #print(conn_data_alist)
                    ida_script="""(set-slot [@] 'name "building_{}")
(apply 'delete-components (:call :sections [@]))
(insert-district-distr [@] '({}))
(invoke-esbo-plant [@ plant])
(add-substations-to-plant [@] {} {})
(:UPDATE [@ plant]
{}
  (:ADD (:CEO :SYMBOL '(:AT ((36 24)) :R (14 14) :ICON "lib:emeter.ids" :SLOT ("EmeterWater") :NAME "EmeterWater" :DATA :CEO :D (:DICT (ICE DESCRIPTIONS EMETER))) :N "EmeterWater" :T EMETER)
   (:PAR :N N_IN :V 0)
   (:PAR :N N_MONTH :V 13))
  (:ADD (:CEO :SYMBOL '(:AT ((104 24)) :R (14 14) :ICON "lib:emeter.ids" :SLOT ("EmeterLocalChil") :NAME "EmeterLocalChil" :DATA :CEO :D (:DICT (ICE DESCRIPTIONS EMETER))) :N "EmeterLocalChil" :T EMETER)
   (:PAR :N N_IN :V 0)
   (:PAR :N N_MONTH :V 13))
  (:ADD (:CEO :SYMBOL '(:AT ((70 24)) :R (14 14) :ICON "lib:emeter.ids" :SLOT ("EmeterLocalBoil") :NAME "EmeterLocalBoil" :DATA :CEO :D (:DICT (ICE DESCRIPTIONS EMETER))) :N "EmeterLocalBoil" :T EMETER)
   (:PAR :N N_IN :V 0)
   (:PAR :N N_MONTH :V 13))
  (:ADD MACRO-OBJECT SCHEMA '((FORM-DOCUMENT :TYPE SCHEMA :PAGE-WIDTH 178 :PAGE-HEIGHT 97) (SELF-FRAME :AT ((352 190)) :R (342 176) :SLOT (:SELF) :DATA MACRO-OBJECT)) :SYMBOL '(:AT ((46 74)) :R (20 20) :ICON "sys:eo.ids" :SLOT ("Co-simulation-macro") :NAME "Co-simulation-macro" :DATA MACRO-OBJECT) :N "Co-simulation-macro" :T ICE-MACRO :D "ICE macro"))\n""".format(
    submodel,' '.join(b_ids),conn_data_alist,'T' if dlg.checkbox_cosim.isChecked() else 'nil',
  '\n'.join(["""  (:REMOVE "Emeterlocchil_{}")
  (:REMOVE "Emeterlocboil_{}")""".format(counter,counter) for counter,b_id in enumerate(b_ids,1)]) )
                    
                    zone_win_dict={}
                    for counter,zone in enumerate(zones):
                        #print(zone)
                        wkt_string=zone['geom']
                        
                        # Regular expression to match coordinates in the format (x y)
                        pattern = r"(\d+\.\d+ \d+\.\d+)"

                        # Find all the coordinates
                        coordinates = re.findall(pattern, wkt_string)
                        #print(coordinates)

                        corners = []
                        for coordinate in coordinates:
                            # Split each coordinate pair and adjust with the center
                            x, y = coordinate.split(' ')
                            corners.append((round(float(x) - center['x_center'],2), round(float(y) - center['y_center'],2)))

                        # Format the corners with brackets but no commas between coordinates
                        corners_str = f"({') ('.join([f'{x} {y}' for x, y in corners[:-1]])})"
                        #print(corners_str)
                        
                        #constructions
                        sql="""SELECT bc.construction_type_id, bc.construction_name,bct.type AS construction_type
    FROM building_constructions bc, building_construction_types bct
    WHERE bc.construction_standard_id={} AND bc.construction_type_id=bct.id 
    ORDER BY bc.construction_type_id;""".format(zone['z_construction']) # nosec B608
                        cur.execute(sql)
                        constructions=cur.fetchall()
                        constructions_dict={i['construction_type'] : i['construction_name'] for i in constructions}
                        #print(constructions)
                        #print(constructions_dict)
                        zone_win_dict["Zone_{}_{}".format(zone['b_id'],zone['z_id'])]={'temp_name':constructions_dict['win_template'],'win_facade_ratio':zone['win_facade_ratio']}
                        
                        ida_script_="""(make-zone-from-qgis [@] "Zone_{}_{}" {} {} {} #2A({}))\n""".format(
                            zone['b_id'],zone['z_id'],zone['z_bh_m'],zone['z_height_m'],str(len(corners)-1),corners_str)
                        
                        #internal loads (reset templates)
                        ida_script_+="""(apply-zone-template [@] "Zone_{}_{}" "{}" '(:SETPOINTS :CONSTRUCTIONS :INTERNAL-MASSES :INTERNAL-GAINS :vent-system-type :vent-air-flows))\n""".format(
                            zone['b_id'],zone['z_id'],zone['z_template'])
                        
                        ida_script_+="""(:SET z_ [@ "Zone_{}_{}"])\n""".format(zone['b_id'],zone['z_id'])
                        #constructions
                        construction_plist="'("+' '.join([":" + i + ' "' +constructions_dict[i]+'"' for i in constructions_dict])+")"
                        #print(construction_plist)
                        ida_script_+="""(set-zone-constructions [@ z_] {})\n""".format(construction_plist)
                        
                        #room units
                        if zone['room_unit']=='Ideal units':
                            ida_script_+="""(make-component z_ '((HC-UNIT :N "Ideal heater" :T IDEAL-HEATER)
  (:PAR :N PMAX :V (:EVAL (* [z_ GEOMETRY NET_FLOOR_AREA VALUE] [z_ zone-usage 'heating-power VALUE])))))
(make-component z_ '((HC-UNIT :N "Ideal cooler" :T IDEAL-COOLER)
  (:PAR :N PMAX :V (:EVAL (* [z_ GEOMETRY NET_FLOOR_AREA VALUE] [z_ zone-usage 'cooling-power VALUE])))))\n"""
                        elif zone['room_unit']=='Radiator':
                            ida_script_+="""(make-component z_ '((HC-UNIT :N "WatRad" :T WATER_HEATER)
  (:PAR :N CONTROLLER :V PI_CONTR)             
  (:PAR :N PMAX :V (:EVAL (* [z_ GEOMETRY NET_FLOOR_AREA VALUE] [z_ zone-usage 'heating-power VALUE])))
  (:RES :N MODEL :F 2560)
  (:PAR :N HEAT_SUP :V (:EVAL (:CALL ESBO-ADV-DISTR-KEY [@ :building PLANT DISTRIBUTION HEAT TO-ZONE "heat{}"])))))\n""".format(zone['b_id'])
                        elif zone['room_unit']=='Heating/cooling floor':
                            ida_script_+="""(make-component [z_ FLOOR] '((floor-heat :n "hc-floor" :t therm_floor)
  (:par :n pheat :v (:eval (* [z_ zone-usage 'heating-power VALUE]))))
  (:PAR :N HEAT_SUP :V (:EVAL (:CALL ESBO-ADV-DISTR-KEY [@ :building PLANT DISTRIBUTION HEAT TO-ZONE "heat{}"])))
  (:PAR :N HEAT_SUP :V (:EVAL (:CALL ESBO-ADV-DISTR-KEY[@ :building PLANT DISTRIBUTION COLD TO-ZONE "cold{}"]))))
(:set hc_ [z_ FLOOR "hc-floor"])
(make-component hc_ '(aggregate :n shape :t shape2d))
(:set corn (:call ice-surface-offset (:call ice-3d-pane hc_ t t) (or (:call :wall (:call parent hc_)) (:call parent hc_)) 0 (:zone hc_) 0))
(:set ncorn (:call length corn))
(:set corn-array (:call make-array (:call list ncorn 2) :initial-contents corn))
(set-values [hc_ SHAPE] 'ncorn ncorn 'CORNERS corn-array)\n""".format(zone['b_id'],zone['b_id'])

                        if len(ida_script_)+len(ida_script)<32000:
                            ida_script+=ida_script_
                            #print(len(ida_script))
                        else:
                            ida_scripts.append('('+ida_script+')')
                            ida_script=ida_script_
                    for zone in zone_win_dict:
                        ida_script_="""(insert-win-by-ratio [@] {} :zones (:call list [@ "{}"]) :sia_380_1 nil :win-template "{}")\n""".format(zone_win_dict[zone]['win_facade_ratio'],zone,zone_win_dict[zone]['temp_name'])
                        if len(ida_script_)+len(ida_script)<32000:
                            ida_script+=ida_script_
                            #print(len(ida_script))
                        else:
                            ida_scripts.append('('+ida_script+')')
                            ida_script=ida_script_
                    
                    ida_script+="""(:for (load  (:call :loads [@]))
  (move-internal-gain-to-center load))\n"""
                            
                    ida_script+="""(save-document [@])"""
                    ida_scripts.append('('+ida_script+')')
                    
                    src_dir=getDataCenterDir(plugin_dir)+"\\{}\\building_templates\\".format(config['projectName'])
                    #print(src_dir)
                    buildingModel_dir=plugin_dir+'\\versions\\{}\\{}\\'.format(config['projectName'],config['versionName'])
                    #print(buildingModel_dir)
                    file_path=buildingModel_dir+'building_{}.idm'.format(submodel)
                    #print(file_path)
                    copyFile(src_dir+submodel_templates[submodel]+'.idm',buildingModel_dir,file_path)
                    copy_tree_filter_extensions_and_folders(src_dir+submodel_templates[submodel], buildingModel_dir+'building_'+str(submodel))
                
                    
                    worker_buildBuildingModel = WorkerOpenRunScriptAPI(file_path,plugin_dir,ida_scripts,exit_ida=False,finished_fn=finishedBuildBuildingModel,finished_fn_args={'dlg': dlg,'submodel': submodel,'conn_data': conn_data})
                    QThreadPool.globalInstance().start(worker_buildBuildingModel)
                    worker_buildBuildingModel.signals.error.connect(show_error_message)
                    worker_buildBuildingModel.signals.progress.connect(dlg.update_progress)
                    #self.finishedBuildBuildingModel({'dlg': dlg,'submodel': submodel,'conn_data': conn_data})

                    
                    """self.util=Util_api(self.plugin_dir)
                    #print(self.util.pid)
                    # IDA Districts connection test
                    connectionTest = self.util.ida_lib.connect_to_ida(b"5945", self.util.pid.encode())
                    #print(connectionTest)
                    self.building = self.util.call_ida_api_function(self.util.ida_lib.openDocument, file_path.encode('utf-8'))
                    #print(self.building)
                    changeWallFlag = self.util.call_ida_api_function(self.util.ida_lib.runIDAScript, self.building, ida_script.encode('utf-8'))"""          

            else:
                iface.messageBar().pushMessage("Info", "No project version is loaded!", level=Qgis.Info)
        else:
            iface.messageBar().pushMessage("Info", tr('@default','no_db_connection'), level=Qgis.Info)  
    else:
        iface.messageBar().pushMessage("Info", "Please select one or more submodels!", level=Qgis.Info)

def finishedBuildBuildingModel(args):
    #print('------finished build building model----------')
    try:
        dlg=args['dlg']
        submodel=args['submodel']
        conn_data=args['conn_data']
        co_sim=dlg.checkbox_cosim.isChecked()
        reinvoke=dlg.checkbox_reinvokeFeatures.isChecked()
        #print(co_sim)
        #print(reinvoke)    
        #print(submodel)    
        #print(conn_data) 
        source_dir=config['pathProjects']+config['projectName']+'\\versions\\{}\\{}\\invoked_customers\\'.format(config['projectName'],config['versionName'])
        target_dir=config['pathProjects']+config['projectName']+'\\versions\\{}\\{}\\building_{}\\plant\\'.format(config['projectName'],config['versionName'],submodel)
        #print(source_dir) 
        sensor_data=getSensorData(cur,config,filter='')
        #print(sensor_data)

                    
        for b_id in conn_data:
            #print(b_id)
            #idm
            source_f="{}\\Customer_{}\\Customer_{}.idm".format(source_dir,b_id,b_id)
            #print(source_f)
            if not os.path.exists(source_f) or reinvoke:
                #print('reinvoke')
                invokeOneFeature(False,str(b_id),cur,config,'customer',False)
        
        dir=config['pathProjects']+config['projectName']+'\\versions\\{}\\{}'.format(config['projectName'],config['versionName'])
        #print(dir)
            
        if co_sim:
            #print('+++++++cosim++++++')
            dec_templates=CopyDecoupledTemplateMacro(str(submodel),dir,config,cur,sensor_data,mode='building')
            #print('---finished dec---')
            #print(dec_templates.resources)
            if dec_templates.resources:
                file_data=readFileToList("{}\\building_{}.idm".format(dir,submodel))
                file_data[2:2]=dec_templates.resources
                writeToFileFromList(file_data,dir,"{}\\building_{}.idm".format(dir,submodel))
                
            #decoupling
            feature_dec_irefs=[]
            for submodel_ in getUsedSubmodels(cur, config):
                #decoupling: make macro with import/export connections for features which are connected to the submodel lines but not in the submodel  
                #print('//////************------//////*------')
                for i in readDecoupledFeatureSensorSignals(submodel_,dir,config,cur,sensor_data):
                    #print('++++++++--++')
                    #print(i)
                    if i not in feature_dec_irefs:
                        feature_dec_irefs.append(i)
            #print(feature_dec_irefs)

            sensor_dec_data=getSensorDecData(sensor_data,feature_dec_irefs,cur,config)   
            #print(sensor_dec_data)

            #print(dir)
            #print(type(submodel))
            data_dec_idm=writeCosimMacroIdm(config,cur,submodel,dir,sensor_data,sensor_dec_data,mode='building')
            #print(data_dec_idm)

            writeCosimMacroIdc(config,cur,submodel,dir,mode='building')
    
        else:
            #resources
            template_names=getTemplateNamesFilteredByCustomerIds(cur,config,conn_data) 
            resources=[]        
            for template in template_names:
                #print('+++++resource: '+template)
                source_f_idm="{}{}\\customer_templates\\{}.idm".format(config['pathProjects'],config['projectName'],template)
                #print(source_f_idm)
                file_data=readFileToList(source_f_idm)
                resource=getResourcesFromFileDataList(file_data)
                #print(resource)
                if resource not in resources:
                    resources+=resource
            #print(resources)
                    
            if resources:
                file_data=readFileToList("{}\\building_{}.idm".format(dir,submodel))
                file_data[2:2]=resources
                writeToFileFromList(file_data,dir,"{}\\building_{}.idm".format(dir,submodel))
                    
            for b_id in conn_data:
                #print(b_id)
                #idm
                source_f_idm="{}Customer_{}\\Customer_{}.idm".format(source_dir,b_id,b_id)
                #print(source_f_idm)
                
                components_idm=propertyListCompsIDM(getIDAListComponents(readFileToString(source_f_idm)))
                #print(getConnsValuesByFeature(1,str(b_id),cur,config))
                building_pmt2s=['"'+getPMT2muxName(cur,i['conn_bundle_type_id'],i['conn_id'])+'"' for i in getConnsValuesByFeature(1,str(b_id),cur,config) if i['type'] not in [1,2]]
                #print(building_pmt2s)
                data_idm=[]
                for comp in components_idm:
                    if getCompName(comp) in building_pmt2s:
                        data=[]
                        for i in comp:
                            if getCompName(i)=='|M_var|':
                                #print('|M_var|')
                                i[':B']=['-1','|term_b|','1']
                                data.append(i)
                            elif getCompName(i)=='|term_b|':
                                instream_data=[]
                                for j in i:
                                    if getCompName(j)=='|inStream(T)|':
                                        #print('|inStream(T)|')
                                        j[':B']=['-1','|term_b|','2']
                                    instream_data.append(j)
                                data.append(instream_data)
                            else:
                                data.append(i)
                        data_idm.append(data)
                    else:
                        data_idm.append(comp)
                writePropertyListIDMToFile(data_idm,target_dir,target_dir+'substation b{}.idm'.format(b_id),config)


                source_f_idc="{}Customer_{}\\Customer_{}.idc".format(source_dir,b_id,b_id)
                #print(source_f_idc)
                copyFile(source_f_idc,target_dir,target_dir+'substation b{}.idc'.format(b_id))
                if os.path.exists("{}\\Customer_{}\\Customer_{}".format(source_dir,b_id,b_id)):
                    copy_tree_filter_extensions_and_folders("{}\\Customer_{}\\Customer_{}".format(source_dir,b_id,b_id),target_dir+'substation b{}'.format(b_id),exclude_extensions=['prn'])
    except Exception as e:
        #print(e)
        pass