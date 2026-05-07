from qgis.PyQt.QtCore import QThreadPool

from .utility_functions.files import *
from .utility_functions.dialog import *
from .utility_functions.workers import *
from .supervisory_control import Supervisory_control

from .outputs import WorkerSetRequestedOutputs
from .invoke_network import WorkerBuildNetworkModel

def openSupervisoryCtrl(cur,plugin_dir,config):
    Supervisory_control(plugin_dir,config)
    #setSupervisoryCrtlSubmodel(dlg,cur)
    file = config['pathProjects']+'{}\\supervisory_control\\supervisory_control.idm'.format(config['projectName'])
    #print(file)
    worker_openSupervisory = WorkerOpenModelCmd(file,config)
    QThreadPool.globalInstance().start(worker_openSupervisory)
    worker_openSupervisory.signals.error.connect(show_error_message)
        
def setSupervisoryCrtlSubmodel(dlg,cur):
    sql="""UPDATE supervisory_ctrl SET submodel={};""".format(dlg.combo_submodel.currentText())
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
WHERE submodel={};""".format(config['versionName'],submodel)
                    cur.execute(sql)
                    center=cur.fetchone()
                    #print(center)
                    
                    sql="""SELECT b.id,b_id,z_id,ST_AsText(geom) AS geom,z_height_m,z_bh_m, win_facade_ratio, z_construction, zt.name AS z_template, u.name AS room_unit 
    FROM {}.buildings b, room_units u, zone_templates zt
    WHERE b.submodel={} AND u.id=b.room_unit AND zt.id=b.z_template
    ORDER BY b_id,z_id;""".format(config['versionName'],submodel)
                    #print(sql)
                    cur.execute(sql)
                    zones=cur.fetchall()
                    b_ids=set(str(zone["b_id"]) for zone in zones)
                    sql="""SELECT b.b_id,t.conn_bundle_type 
    FROM {}.buildings b,{}.customers c, customer_templates t
    WHERE b.b_id IN ({}) AND c.id=b.substation_id AND c.template=t.template
    GROUP BY t.conn_bundle_type, b.b_id;""".format(config['versionName'],config['versionName'],','.join(b_ids))
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
    ORDER BY bc.construction_type_id;""".format(zone['z_construction'])
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
            iface.messageBar().pushMessage("Info", "You are not connected to the DB!", level=Qgis.Info)  
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