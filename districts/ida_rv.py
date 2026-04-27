from qgis.utils import iface
from qgis.PyQt.QtCore import Qt,QThreadPool
from qgis.PyQt.QtWidgets import QListWidgetItem,QFileDialog

from .utility_functions.workers import *
from .utility_functions.show_on_map import *
from .utility_functions.plots import *
from .utility_functions.dialog import *
from .utility_functions.translations import *

from .load_results import *
from .path_report import *
from datetime import datetime, timedelta

def getSourceVars(source):
    if os.path.isfile(source):
        vars=readFileToList(source)[0].split()
        #print(vars)
    elif os.path.exists(source):
        #print(os.listdir(source))
        vars=readFileToList(source+'/'+os.listdir(source)[0])[0].split()
        #print(vars)
    return [var for var in vars if var not in ['#','time','order']]
        
def dataSourceDialog(dlg,title,open_type):
    if open_type=='file':
        source, _ = QFileDialog.getOpenFileName(
            dlg, title,'', '*.prn')
    else:
        source = QFileDialog.getExistingDirectory(
            None, title)
    #print(source)
    
    if source:
        dlg.lineEditSourceName.setText(source)
        dlg.tableVars.setRowCount(0)
        if os.path.isdir(source):
            source=[source+'/'+i for i in os.listdir(source)][0]
        vars=getSourceVars(source)
        dlg.checked_vars={i: False for i in vars}
        for counter,var in enumerate(vars):
            dlg.tableVars.insertRow(counter)

            chkBoxItem=QTableWidgetItem(var)
            chkBoxItem.setFlags(qt_item_flag("ItemIsUserCheckable") | qt_item_flag("ItemIsEnabled"))
            chkBoxItem.setCheckState(uncheckState())  

            dlg.tableVars.setItem(counter,0,chkBoxItem)
            comboBox = QComboBox()
            items={i: tr('@default',i) for i in ['customer','energy_plant','line']}
            #print(items)
            # Add items to the combobox, storing the original key as user data
            for original_key, translated_text in items.items():
                comboBox.addItem(translated_text, original_key) # The second argument is the userData
            dlg.tableVars.setCellWidget(counter, 1, comboBox)
            dlg.tableVars.setItem(counter, 2, QTableWidgetItem(''))
            dlg.tableVars.setItem(counter, 3, QTableWidgetItem(''))
            dlg.tableVars.setItem(counter, 4, QTableWidgetItem(''))
    
def importMeasurementData(dlg,config,cur,plugin_dir,conn):
    var_dict=[{'var':dlg.tableVars.item(i,0).text(),
                'colmn':i+2,
                'feature':dlg.tableVars.cellWidget(i,1).currentData().replace(' ','_'),
                'alias':(dlg.tableVars.item(i,2).text() if dlg.tableVars.item(i,2).text() else dlg.tableVars.item(i,0).text()),
                'min': float(dlg.tableVars.item(i,3).text()) if dlg.tableVars.item(i,3).text().isnumeric() else False,
                'max': float(dlg.tableVars.item(i,4).text()) if dlg.tableVars.item(i,4).text().isnumeric() else False} 
                for i in range(dlg.tableVars.rowCount()) if dlg.tableVars.item(i,0).checkState() == checkState()]
    #print(var_dict)
    
    srid=loadProjectConfig(config)['srid']
    source=dlg.lineEditSourceName.text()
    if os.path.isfile(source):
        files=[source]
    elif os.path.exists(source):
        files=[source+'/'+i for i in os.listdir(source)]
    
    for counter,file in enumerate(files):
        filedata=readFileToList(file)
        #print(filedata)
            
        for var in var_dict:
            #print(var)
            id=file.split('/')[-1].split('.')[0]
            #print(id)
            table_name=var['feature']+'_m_'+var['alias']
            #print(table_name)
            #print(checkTableNameExists(cur,config,table_name))
            if not checkTableNameExists(cur,config,table_name):
                sql="""CREATE TABLE IF NOT EXISTS "{}".{}
(
    id serial,
    fid INTEGER,
    time timestamp,
    geom geometry({},{}),
    "${}" numeric,
    CONSTRAINT {}_pkey PRIMARY KEY (id));""".format(config['versionName'],table_name,'LineStringZ' if var['feature']=='Line' else 'PointZ', srid,var['alias'],table_name)
                #print(sql)
                cur.execute(sql)
            elif dlg.delete_existing_data.checkState() == checkState() and counter==0:
                sql="""TRUNCATE "{}".{};""".format(config['versionName'],table_name)
                cur.execute(sql)
            elif dlg.delete_existingID_data.checkState() == checkState():
                sql="""DELETE FROM "{}".{} WHERE fid={};""".format(config['versionName'],table_name,id)
                cur.execute(sql)
                
        vars_data={var['colmn']:[] for var in var_dict}
        #print(vars_data)
        
        # Base datetime: Jan 1 of the current year
        base_time = datetime(datetime.now().year, 1, 1)
        for i,line in enumerate(filedata):
            if i>0:
                data=line.strip().split()
                for colmn,max_value,min_value in [[i['colmn'],i['max'],i['min']] for i in var_dict]:
                    time=base_time+timedelta(hours=float(data[0]))
                    vars_data[colmn].append([time,min(max(float(data[colmn]),min_value),max_value) if max_value and min_value else ((min(float(data[colmn]),max_value) if max_value else max(float(data[colmn]),min_value)) if max_value or min_value else float(data[colmn]))])
                    

        vars_data_np={i:np.array(vars_data[i]) for i in vars_data} 
        #print(vars_data_np)
        start_time_m=vars_data_np[[i for i in vars_data_np][0]][0][0]
        end_time_m=vars_data_np[[i for i in vars_data_np][0]][-1][0]


        if dlg.checkbox_timestep.checkState() == checkState():
            #print(dlg.interpolation_dt.text())

            if is_number(dlg.interpolation_dt.text()):
                dt = float(dlg.interpolation_dt.text())  # hours

                if vars_data_np:

                    first_key = list(vars_data_np.keys())[0]

                    # Convert source time to hours since base_time
                    src_time_dict = {}

                    for k in vars_data_np:
                        src_time_dict[k] = np.array([
                            (t[0] - base_time).total_seconds() / 3600
                            for t in vars_data_np[k]
                        ])

                    start_time_m = src_time_dict[first_key][0]
                    end_time_m = src_time_dict[first_key][-1]

                    start_time_h = start_time_m - (start_time_m % dt)
                    end_time_h = end_time_m - (end_time_m % dt) + dt

                    time_hours = np.arange(start_time_h, end_time_h, dt)

                else:
                    iface.messageBar().pushMessage(
                        "Info", "Please select a variable!", level=Qgis.Info
                    )
                    return
            else:
                iface.messageBar().pushMessage(
                    "Info", "Please enter a numerical interpolation time!", level=Qgis.Info
                )
                return


        # ----------------------------
        # PROCESS EACH VARIABLE
        # ----------------------------

        for var in var_dict:

            key = var['colmn']
            table_name = var['feature'] + '_m_' + var['alias']

            if dlg.checkbox_timestep.checkState() == checkState():

                src_time = src_time_dict[key]
                src_values = np.array([v[1] for v in vars_data_np[key]], dtype=float)

                var_interp = np.interp(time_hours, src_time, src_values)

                time_out = np.datetime64(base_time) + (time_hours * 3600).astype('timedelta64[s]')

            else:
                time_out = np.array([t[0] for t in vars_data_np[key]])
                var_interp = np.array([t[1] for t in vars_data_np[key]], dtype=float)

            #print(time_out)
            #print(var_interp)

            sql = 'SELECT geom FROM "{}".{}s WHERE id={};'.format(
                config['versionName'], var['feature'], id
            )
            cur.execute(sql)
            fid_geom = cur.fetchone()

            if fid_geom:
                fid_geom = fid_geom['geom']
            else:
                fid_geom = None

            copy_string_iterator_mData(
                conn,
                var_interp,
                getMaxIdSchema(cur, table_name, config['versionName']) + 1,
                id,
                time_out,
                fid_geom,
                table_name,
                dlg,
                config
            )    
    closeDialog(dlg)
        
def copy_string_iterator_mData(connection, mdata, id_max,fid,time,geom,table_name,dlg,config) -> None:
    with connection.cursor() as cursor:
        mdata_string_iterator = StringIteratorIO((
            '|'.join(map(clean_csv_value, (
                id,
                fid,
                data[0],
                geom,
                data[1]
            ))) + '\n'
            for id,data in enumerate(zip(time,mdata),id_max)
        ))
        cursor.copy_expert("""COPY "{}".{} FROM STDIN WITH (FORMAT csv, DELIMITER '|')""".format(config['versionName'],table_name),mdata_string_iterator)
                

def showOnMap(dlg,main,networkReportDlg=None):
    fd_meterPerNode=float(loadModellingSettings(main.plugin_dir,main.config)['fd_meterPerNode'])
    if int(dlg.lineSegVis.text())==0:
        iface.messageBar().pushMessage("Info", f"The line segment length for visualization should be greater than 0.", level=Qgis.Info)
        return False
    main.worker_showOnMap = WorkerShowOnMap(networkReportDlg=networkReportDlg,dlg_main=main.dlg,config=main.config,plugin_dir=main.plugin_dir,dlg=dlg,vars=None,feature=dlg.feature,layer_name=dlg.layer_name.text(),
        lineSegVis=int(dlg.lineSegVis.text()),simData=dlg.rbtn_simData.isChecked(),enable=True)
            
    main.worker_showOnMap.signals.error.connect(show_error_message)
    main.worker_showOnMap.signals.progress.connect(dlg.update_progress)  
    main.worker_showOnMap.signals.finished.connect(dlg.update_finished)  
    QThreadPool.globalInstance().start(main.worker_showOnMap) 
        
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
    #print(ids)
    dlg.listWidget_ids.addItems(ids)
        
def addSelectedIDs(dlg):
    """Adds all selected lines to list dlg.listWidget_ids"""
    #print('add selected lines')
    layer = iface.activeLayer()
    if layer:
        #print(layer.name())
        if layer.name()==tr('@default','lines') and dlg.rbtn_lineIds.isChecked() or layer.name()==tr('@default','customers') and dlg.rbtn_customer.isChecked():
            features = layer.selectedFeatures()
            #print(features)
            for f in features:
                #print(f['id'])
                item = QListWidgetItem(str(f['id']))
                item.setFlags(item.flags() | qt_item_flag("ItemIsEditable"))
                dlg.listWidget_ids.addItem(item)

def addID(dlg):
    """Add id to list dlg.listWidget_ids"""
    #print('add id')
    item = QListWidgetItem('')
    item.setFlags(item.flags() | qt_item_flag("ItemIsEditable"))
    dlg.listWidget_ids.addItem(item)
            
def deleteIDs(dlg):
    listItems=dlg.listWidget_ids.selectedItems()
    if not listItems: return        
    for item in listItems:
        dlg.listWidget_ids.takeItem(dlg.listWidget_ids.row(item))
            
def loadResults(dlg,main):
    submodels=[dlg.combo_submodels.itemText(i) for i in range(dlg.combo_submodels.count()) if dlg.combo_submodels.itemText(i) != 'Check all items' and dlg.combo_submodels.itemChecked(i)]
    
    simulatedOutputs=loadSimulatedOutputs(main.config)
    if not simulatedOutputs:
        iface.messageBar().pushMessage("Info", "The project version is not yet simulated!", level=Qgis.Info)
        return False
        
    if dlg.checkbox_timestep.checkState() == checkState():
        if not is_number(dlg.interpolation_dt.text()):
            iface.messageBar().pushMessage("Info", "Please enter a numerical interpolation time!", level=Qgis.Info)
            return False
        
    if submodels:
        main.worker_loadResults = WorkerLoadResults(config=main.config,plugin_dir=main.plugin_dir,dlg=dlg,submodels=submodels,simulatedOutputs=simulatedOutputs)
        QThreadPool.globalInstance().start(main.worker_loadResults) 
        main.worker_loadResults.signals.error.connect(show_error_message)
        main.worker_loadResults.signals.progress.connect(dlg.update_progress)   
        main.worker_loadResults.signals.finished.connect(dlg.update_finished)   
    else:
        iface.messageBar().pushMessage("Info", "Please select one or more submodels!", level=Qgis.Info)
  
def runPathReports(dlg,main):
    main.worker_pathReport = WorkerPathReport(config=main.config,plugin_dir=main.plugin_dir,dlg=dlg)
            
    main.worker_pathReport.signals.error.connect(show_error_message)
    main.worker_pathReport.signals.progress.connect(dlg.update_progress)  
    main.worker_pathReport.signals.finished.connect(dlg.update_finished)  
    QThreadPool.globalInstance().start(main.worker_pathReport)   
                    
def plotLoadProfiles(dlg,plugin_dir,config,cur):
    simulatedOutputs=loadSimulatedOutputs(config)
    if simulatedOutputs['power_c']==True:
        selected_items=dlg.listWidget_ids.selectedItems()
        if selected_items:
            for item in dlg.listWidget_ids.selectedItems():
                id=item.text()
                #print(id)
                matplotlibPowerPlots(plugin_dir,config,cur,id,feature_type='customer' if dlg.rbtn_customer.isChecked() else 'energy_plant',show_plot=True,save_plot=False)
        else:
            iface.messageBar().pushMessage("Info", "Please select an item in the list!!", level=Qgis.Info)    
    else:
        iface.messageBar().pushMessage("Info", "The customer`s load is not yet simulated in the current project version!", level=Qgis.Info)
        
        