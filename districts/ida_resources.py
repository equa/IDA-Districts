from qgis.PyQt.QtWidgets import QTableWidgetItem,QComboBox,QCheckBox
from qgis.PyQt.QtCore import Qt,QThreadPool
from qgis.core import QgsDataSourceUri,QgsAuthMethodConfig
from qgis.utils import iface

from .update_boundaries import *
from .utility_functions.db import *
from .utility_functions.dialog import *
from .utility_functions.templateFiles import ExchangeConntypeFiles,WriteTemplateFiles, RenameTemplateFiles
from .utility_functions.workers import *
from .utility_functions.invoke import CopyTemplateFiles
from .utility_functions.layer_visualization import *
from .utility_functions.reports import *

def writeClimateDataToDB(dlg,main):
    """ write climate data into DB"""
    #print('Write climate data to DB')
    main.dlg.update_progress(100)
    try:
        name=dlg.lineEdit_location.text()
        latitude=dlg.lineEdit_latitude.text()
        longitude=dlg.lineEdit_longitude.text()
        fileName=dlg.lineEdit_filePath.text()
        timezone=dlg.spinBox_timeZone.value()
        height=dlg.lineEdit_elevationHeight.text()
        sql="""UPDATE "{}".climate SET
        name = \'{}\',
        latitude = {},
        longitude = {},
        file_name = \'{}\',
        timezone = {},
        height = {};""".format(main.config['versionName'],name,latitude,longitude,fileName,timezone,height) # nosec B608
        #print(sql)
        main.cur.execute(sql)
        main.dlg.statusMessage.setText('Climate data is successfully updated!')
        main.dlg.update_progress(100)
        closeDialog(dlg)
    except Exception as e:
        main.dlg.statusMessage.setText('Climate data update failed: '+str(e))
        main.dlg.update_progress(0)
        
def updateClimateMacro(data,dir,config):
    fname=dir+'climate-macro.idm'
    components_idm=propertyListCompsIDM(getIDAListComponents(readFileToString(fname)))
    idm=[]
    for comp in components_idm:
        #print(getCompTemplate(comp))
        if getCompTemplate(comp)=='ENVIRONMENT':
            new_comp=[]
            for i in comp:
                if getCompName(i)=='LAT':
                    i=setCompValue(i,data['latitude'])
                elif getCompName(i)=='LONG':
                    i=setCompValue(i,data['longitude'])
                elif getCompName(i)=='LONGTIMEZONE':
                    i=setCompValue(i,float(data['timezone'])*15)
                elif getCompName(i)=='HEIGHT':
                    i=setCompValue(i,data['height'])
                new_comp.append(i)
            idm.append(new_comp)
        elif getCompTemplate(comp)=='SOURCE-FILE':
            #print(comp)
            new_comp=[]
            for i in comp:
                if getCompClass(i)=='SOURCE-FILE':
                    i[':DOCUMENT-PATH']='"'+data['filename'].replace('\\','\\\\')+'"'
                    i[':SF']='"'+data['filename'].replace('\\','\\\\')+'"'
                new_comp.append(i)
            idm.append(new_comp)
        else:
            idm.append(comp)
    writePropertyListIDMToFile(idm,dir,fname,config)

def openClimateMacro(main):
    dir_project=main.config['pathProjects']+main.config['projectName']
    dir_climate=dir_project+'\\climate\\'
    dir_climateMacro=dir_climate+'climate\\'
    if main.config['versionName']:
        data=getClimateData(main.cur,main.config,True)
        #update climate template
        updateClimateMacro(data,dir_climateMacro,main.config)
        
        #update customer and energy plant templates
        for feature in ['customer','energy_plant']:
            sql="""Select * from {}_templates;""".format(feature) # nosec B608
            main.cur.execute(sql)
            for template in main.cur.fetchall():
                template_name=str(template['template'])+'_'+template['template_name']
                target_dir=dir_project+'\\{}_templates\\'.format(feature)+template_name+'\\'
                copyFile(dir_climateMacro+'climate-macro.idm',target_dir,target_dir+'climate-macro.idm')
                copyFile(dir_climateMacro+'climate-macro.idc',target_dir,target_dir+'climate-macro.idc')

    
    main.worker_openClimate = WorkerOpenModelCmd(dir_climate+'climate.idm',main.config)
    QThreadPool.globalInstance().start(main.worker_openClimate) 
    main.worker_openClimate.signals.error.connect(show_error_message)
    main.worker_openClimate.signals.progress.connect(main.dlg.update_progress)  
    main.worker_openClimate.signals.finished.connect(main.dlg.modelOpeningFinished)  
    #print('--open climate macro finished--')
    

    
def writeRenameExchangeConntype(config,cur,dlg,traceValue,table_name,plugin_dir):
    #print('--writeRenameExchangeConntype--')
    #print(table_name)
    wroteTemplate=False
    if dlg.traceTableValues[traceValue][1]:
        if dlg.traceTableValues[traceValue][0]!=dlg.traceTableValues[traceValue][1]:
            #print(dlg.traceTableValues[traceValue])
            if not dlg.traceTableValues[traceValue][0]:
                if dlg.traceTableValues[traceValue][3]:
                    WriteTemplateFiles(config,dlg.traceTableValues[traceValue][1],table_name,cur,dlg.traceTableValues[traceValue][3],plugin_dir)
                else:
                    iface.messageBar().pushMessage("Error", "No template is set in: "+str(dlg.traceTableValues[traceValue]), level=Qgis.Critical)
                    return False
                wroteTemplate=True
            else:
                RenameTemplateFiles(config,dlg.traceTableValues[traceValue][0],table_name,dlg.traceTableValues[traceValue][1],cur)
    if dlg.traceTableValues[traceValue][3] and dlg.traceTableValues[traceValue][2] and not wroteTemplate:
        if dlg.traceTableValues[traceValue][2]!=dlg.traceTableValues[traceValue][3]:
            #print('Changed conn bundle type')
            #print(dlg.traceTableValues[traceValue])
            if dlg.traceTableValues[traceValue][1]:
                name=dlg.traceTableValues[traceValue][1]
            else:
                name=dlg.traceTableValues[traceValue][0]
            ExchangeConntypeFiles(config,name,table_name,dlg.traceTableValues[traceValue][3],dlg.traceTableValues[traceValue][2],cur)
  
def saveAsTemplate(cur,config,dlg,table_name,dropdowns,trace):
    """Save as the template"""
    #print('--saveAsTemplate--')
    row_idx=dlg.tableWidget.currentRow()
    
    if row_idx!=-1:
        description=""
        if dlg.tableWidget.item(row_idx,3):
            description=dlg.tableWidget.item(row_idx,3).text()
        sql=""
        template_id=int(dlg.tableWidget.item(row_idx,0).text())
        maxId=getMaxTableId(dlg.tableWidget)
        template_name=dlg.tableWidget.item(row_idx, 1).text()+' (copy)'
        conn_bundle_type_old=dlg.tableWidget.cellWidget(row_idx, 2).currentText()
        #print(conn_bundle_type_old)
        file_name_old=str(template_id)+'_'+dlg.tableWidget.item(row_idx, 1).data(Qt.ItemDataRole.UserRole)
        file_name_new=str(maxId+1)+'_'+template_name
        if not os.path.exists(config['pathProjects']+"{}\\{}\\{}.idm".format(config['projectName'],table_name,file_name_new)): 
            CopyTemplateFiles(source_dir=config['pathProjects']+"{}\\{}".format(config['projectName'],table_name),source_name=file_name_old,target_dir=config['pathProjects']+"{}\\{}".format(config['projectName'],table_name),target_name=file_name_new,config=config)

        addTableRowTrace(dlg,dropdowns,True,[],cur)
        dlg.tableWidget.setItem(0,0,QTableWidgetItem(str(maxId+1)))
        dlg.tableWidget.setItem(0,1,QTableWidgetItem(template_name))
        dlg.tableWidget.cellWidget(0, 2).setCurrentText(conn_bundle_type_old)
        dlg.tableWidget.setItem(0,3,QTableWidgetItem(description))
        
        #replace values of dlg.traceTableValues [0] in order to trace the changed values         
        dlg.traceTableValues[0]=[file_name_new,'',conn_bundle_type_old.split(':')[0],'']
        #print(dlg.traceTableValues)
        
        #add sensor data to source and target templates and invoked signals
        sql="""INSERT INTO target_template(target_id,template,active) 
    SELECT templ.target_id,{},templ.active FROM target_template templ, sensor_target t 
        WHERE templ.template = {} AND templ.target_id=t.sensor_id AND t.type = {};
INSERT INTO source_template(source_id,template,active) 
    SELECT templ.source_id,{},templ.active FROM source_template templ, sensor_source s 
        WHERE templ.template = {} AND templ.source_id=s.sensor_id AND s.type = {};
UPDATE invoked_sensor_source_signals
    SET templates = templates || {}
    WHERE {} = ANY(templates)  AND type = {};
UPDATE invoked_sensor_target_signals
    SET templates = templates || {}
    WHERE {} = ANY(templates) AND type = {};""".format(# nosec B608
    str(maxId+1),template_id,dlg.type,# nosec B608
    str(maxId+1),template_id,dlg.type,# nosec B608
    str(maxId+1),template_id,dlg.type,# nosec B608
    str(maxId+1),template_id,dlg.type) # nosec B608
        #print(sql)
        cur.execute(sql)

    else:
        iface.messageBar().pushMessage("Info", tr('@default','no_item_selected'), level=Qgis.Info) 


def openTemplate(main,type,dlg):
    """ Open an template macro in IDA; copy the template from the installation folder"""
    #print('Open Template')
    row_index=dlg.tableWidget.currentRow()
    if row_index!=-1:
        template=dlg.tableWidget.item(row_index, 0).text()
        sql="SELECT template_name,conn_bundle_type FROM public.{}_templates WHERE template={};".format(type,template) # nosec B608
        #print(sql)
        main.cur.execute(sql)
        template_=main.cur.fetchone()
        if template_:
            template_name=template_['template_name']
            conn_bundle_type=template_['conn_bundle_type']
        else:
            if dlg.tableWidget.item(row_index, 1) and dlg.tableWidget.item(row_index, 1).text():
                template_name=dlg.tableWidget.item(row_index, 1).text()
            else:
                iface.messageBar().pushMessage("Info", "Please enter an template name!", level=Qgis.Info)
                return False
            conn_bundle_type=dlg.tableWidget.cellWidget(row_index, 2).currentText()
            conn_bundle_type=conn_bundle_type.split(":")[0]
        name=template+'_'+template_name
        dir=main.config['pathProjects']+"{}\\{}_templates\\".format(main.config['projectName'],type)
        file=dir+"{}.idm".format(name)
        #print(file)
        #print(dlg.traceTableValues)
        
        if dlg.traceTableValues[row_index][1] and dlg.traceTableValues[row_index][0]:
            if dlg.traceTableValues[row_index][0]!=dlg.traceTableValues[row_index][1]:
                #print('~~~~~~~~~~~~~~~rename~~~~~~~~~~')
                RenameTemplateFiles(main.config,dlg.traceTableValues[row_index][0],type,dlg.traceTableValues[row_index][1],main.cur)
                dlg.traceTableValues[row_index][0]=dlg.traceTableValues[row_index][1]
                dlg.traceTableValues[row_index][1]=''
                file=dir+"{}.idm".format(dlg.traceTableValues[row_index][0])
                template_name=dlg.traceTableValues[row_index][1]
            else:
                template_name=template_name
        else:
            template_name=template_name
                
        wroteTemplate=False
        if not os.path.exists(file): 
            WriteTemplateFiles(main.config,name,type,main.cur,conn_bundle_type,main.plugin_dir)
            dlg.traceTableValues[row_index][0]=dlg.traceTableValues[row_index][1]
            dlg.traceTableValues[row_index][1]=''
            wroteTemplate=True
        
        if dlg.traceTableValues[row_index][3] and dlg.traceTableValues[row_index][2] and not wroteTemplate: # override connection bundle only if template exists before
            if dlg.traceTableValues[row_index][2]!=dlg.traceTableValues[row_index][3]:
                #print('Changed conn bundle type')
                #print(dlg.traceTableValues[row_index])
                ExchangeConntypeFiles(main.config,name,type,dlg.traceTableValues[row_index][3],dlg.traceTableValues[row_index][2],main.cur)
                dlg.traceTableValues[row_index][2]=dlg.traceTableValues[row_index][3]
                dlg.traceTableValues[row_index][3]=''
                #print(dlg.traceTableValues[row_index])                

        #write to DB
        sql="DELETE FROM public.{}_templates WHERE template={};".format(type,template) # nosec B608
        #print(sql)
        main.cur.execute(sql)
        if type=='customer':
            description_index=4
        else:
            description_index=3
        if dlg.tableWidget.item(row_index, description_index):
            description=dlg.tableWidget.item(row_index, description_index).text()
        else:
            description=''

        sql="""INSERT INTO public.{}_templates (id, template,template_name,conn_bundle_type,description) VALUES({},{},'{}',{},'{}');\n""".format(# nosec B608
            type,getMaxId(main.cur,type+'_templates')+1,template,template_name,dlg.traceTableValues[row_index][3] if dlg.traceTableValues[row_index][3] else dlg.traceTableValues[row_index][2],description) # nosec B608
        #print(sql)
        main.cur.execute(sql)
        
        #print(file)
        main.worker_openTemplate = WorkerOpenModelCmd(file,main.config)
        QThreadPool.globalInstance().start(main.worker_openTemplate) 
        main.worker_openTemplate.signals.error.connect(show_error_message)
        main.worker_openTemplate.signals.progress.connect(main.dlg.update_progress)  
        main.worker_openTemplate.signals.finished.connect(main.dlg.modelOpeningFinished)  
        
        #print('finished open template')
    else:
        iface.messageBar().pushMessage("Info", tr('@default','no_item_selected'), level=Qgis.Info)
        
def show_templateDialog(main=False,type=False):
    #print('Open current row dialog started: ')
    columns=['template','template_name','conn_bundle_type','description']
    headers=[tr('@default','id'), tr('@default','template'),tr('@default','connection_bundles'), tr('@default','description')]
    filter=''
    orderby='ORDER BY template'
    dropdowns=[[2,'public','conn_bundle_types','id','description']]
    trace=True
    save_as=True
    deactivated=[0]
    title=tr('@default','templates')+': '+tr('@default',type)
    table='{}_templates'.format(type)
    
    dlg = TableDialog(title,headers,True,False,save_as,trace,type=getTypeIdByName(type))    
    dlg.btn_open.clicked.connect(lambda: openTemplate(main,type,dlg))

    dlg.btn_add.clicked.connect(lambda: addTableRowTrace(dlg,dropdowns,trace,deactivated,main.cur))
    dlg.btn_cancel.clicked.connect(lambda: closeDialog(dlg))   
    dlg.btn_ok.clicked.connect(lambda: saveContent(main.plugin_dir,main.cur,main.config,dlg,'',table,columns,filter,dropdowns,trace))
    if save_as:
        dlg.btn_saveAs.clicked.connect(lambda: saveAsTemplate(main.cur,main.config,dlg,table,dropdowns,trace))
    
    dlg.btn_delete.clicked.connect(lambda: deleteTableRowTrace(dlg,trace))
    dlg.traceTableValues=showFilteredTableContent(main.cur,main.conn,dlg,table,columns,'',orderby,dropdowns,trace,deactivated)
   
    if trace:
        dlg.tableWidget.itemChanged.connect(dlg.changeItem)
    dlg.show() 
        
def saveContent(plugin_dir,cur,config,dlg,id,table,columns,filter,dropdowns,trace):
    """" Save table to DB an close dialog"""
    #print('Save table content to DB an close dialog')
    #print(trace)
    table_name="_".join(table.split('_')[0:-1])
    if trace in ['conn_type_trace','bt_conns_trace']:
        oldConnValues_dict={}
        templates=getTemplatesByConnType(cur,config,id) if trace=='conn_type_trace' else getTemplatesByConnBundleType(cur,config,id)
        for template in templates:
            oldConnValues_dict[template['t_name']]=getConnsValues(template['conn_bundle_type_id'],cur)
    
    sql="""DELETE FROM public.{} {} {};\n""".format(table,filter,id) # nosec B608
    #print(sql)
    maxId=getMaxId(cur,table)
    counter=1
    for row in range(dlg.tableWidget.rowCount()):
        values=getValuesFromTableRow(dlg,dropdowns,row,columns,[])
        #print(values)
        if not values:
            iface.messageBar().pushMessage("Error", "Invalid input!", level=Qgis.Critical)
            return False
        sql+="""INSERT INTO public.{} (id{},{}) VALUES({}{}{},{});\n""".format(table,','+filter.split(' ')[1] if id else '',','.join(i for i in columns),maxId+counter,',' if id else '',id,values) # nosec B608
        counter+=1
    #print(sql)
    try:
        cur.execute(sql)
    except Exception as e:
        iface.messageBar().pushMessage("Error", str(e), level=Qgis.Critical)
        return False
    
    if trace in ['conn_type_trace','bt_conns_trace']:
        #print(dlg.traceTableValues)
        if [True for traceValue in dlg.traceTableValues if 
            dlg.traceTableValues[traceValue][1] and dlg.traceTableValues[traceValue][3] and (dlg.traceTableValues[traceValue][0]!=dlg.traceTableValues[traceValue][1] or dlg.traceTableValues[traceValue][2]!=dlg.traceTableValues[traceValue][3]) or
            dlg.traceTableValues[traceValue][1] and not dlg.traceTableValues[traceValue][0] or 
            dlg.traceTableValues[traceValue][3] and not dlg.traceTableValues[traceValue][2]]:
            #print('ExchangeConntypeFiles')
            #get changed conn bundle types --> get changed templates
            templates=getTemplatesByConnType(cur,config,id) if trace=='conn_type_trace' else getTemplatesByConnBundleType(cur,config,id)
            for template in templates:
                #print('*****************************************************************************')
                #print(template['t_name'])
                #print(oldConnValues_dict[template['t_name']])
                ExchangeConntypeFiles(config,template['t_name'],template['type'],template['conn_bundle_type_id'],template['conn_bundle_type_id'],cur,oldConnValues=oldConnValues_dict[template['t_name']])
        
    elif trace:
        #print(dlg.traceTableValues)
        for traceValue in dlg.traceTableValues:
            writeRenameExchangeConntype(config,cur,dlg,traceValue,table_name,plugin_dir)
        
        #delete templates in directory if they are not in dlg.traceTableValues[traceValue][0]
        dir=config['pathProjects']+config['projectName']+"\\{}_templates".format(table_name)
        files = []
        for file in os.listdir(dir):
            # check only .idm files
            if file.split('.')[0] not in files:
                files.append(file.split('.')[0])
        traceTableFiles=[]
        for traceValue in dlg.traceTableValues: 
            if dlg.traceTableValues[traceValue][1]:
                traceTableFiles.append(dlg.traceTableValues[traceValue][1])
            else:
                traceTableFiles.append(dlg.traceTableValues[traceValue][0])
        #print(traceTableFiles)
        sql="""SELECT template::text || '_' || template_name AS template_name FROM {}_templates;""".format(table_name) # nosec B608
        cur.execute(sql)
        list_template_names=[i['template_name'] for i in cur.fetchall()]
        #print(list_template_names)
        for file in files:
            if file not in traceTableFiles and file not in list_template_names:
                if os.path.exists(dir+'\\'+file+'.idm'):
                    os.remove(dir+'\\'+file+'.idm')
                if os.path.exists(dir+'\\'+file+'.idc'):
                    os.remove(dir+'\\'+file+'.idc')
                if os.path.exists(dir+'\\'+file+'.#f.idc'):
                    os.remove(dir+'\\'+file+'.#f.idc')
                if os.path.exists(dir+'\\'+file):
                    shutil.rmtree(dir+'\\'+file)
        
        auth_cfg = QgsAuthMethodConfig()
        QgsApplication.authManager().loadAuthenticationConfig(config["auth_id"], auth_cfg, True)
 
        uri = QgsDataSourceUri()
        uri.setConnection(config['host'], config['port'], config['projectName'], auth_cfg.config("username"), auth_cfg.config("password"))
        removeLayers()
        loadProjectLayers(config['versionName'],uri,config,plugin_dir,cur,auth_cfg.config("username"))
    dlg.close()

def show_TableCurrentRowDialog(main,table,columns,dropdowns,dlg,id,openFnArg,trace=False):
    """ Show current row in table; openFnArg: 0) table; 1) columns in String; 2) headers in list; 3) filter in String; 4) dropdowns """
    #print('Open current row dialog started: ')
    columns=openFnArg[1]
    headers=openFnArg[2]
    filter=openFnArg[3]
    orderby=openFnArg[4]
    dropdowns=openFnArg[5]
    trace=openFnArg[8]
    save_as=openFnArg[9]
    deactivated=openFnArg[10]
    if id!=-1:
        id=dlg.tableWidget.item(id, 0).text()
        title=tr('@default',openFnArg[0])+': ' + id
        dlg = TableDialog(title,headers,openFnArg[6],False,save_as,trace,type=getTypeIdByName(openFnArg[7]))           
        if openFnArg[6]:
            dlg.btn_open.clicked.connect(lambda: openFnArg[6](openFnArg[7],dlg,id))
        if columns[0]=='time_h':
            dlg.btn_add.clicked.connect(lambda: addTableRowTrace(dlg,dropdowns,trace,[],main.cur))
        else:
            dlg.btn_add.clicked.connect(lambda: addTableRowTrace(dlg,dropdowns,trace,deactivated,main.cur))
        dlg.btn_cancel.clicked.connect(lambda: closeDialog(dlg,table,openFnArg))   
        dlg.btn_ok.clicked.connect(lambda: saveContent(main.plugin_dir,main.cur,main.config,dlg,id,openFnArg[0],columns,filter,dropdowns,trace))
        if save_as:
            dlg.btn_saveAs.clicked.connect(lambda: saveAsTemplate(main.cur,main.config,dlg,openFnArg[0],dropdowns,trace))
        
        dlg.btn_delete.clicked.connect(lambda: deleteTableRowTrace(dlg,trace))
        dlg.traceTableValues=showFilteredTableContent(main.cur,main.conn,dlg,openFnArg[0],columns,filter+id,orderby,dropdowns,trace,deactivated)
       
        if trace:
            dlg.tableWidget.itemChanged.connect(dlg.changeItem)
        dlg.show() 
    else:
        iface.messageBar().pushMessage("Info", tr('@default','no_item_selected'), level=Qgis.Info) 

def showTableContent(cur_dict,conn,dlg,table,dropdowns,columns=None,deactivated=[0]):
    """show table content"""
    #print('show table content')
    sql='SELECT {} FROM {} ORDER BY id;'.format('*' if columns==None else columns[1:-1],table)# nosec B608
    cur=conn.cursor()
    cur.execute(sql) 
    data = cur.fetchall()
    
    dlg.tableWidget.setRowCount(rowCountDB(table,'',cur_dict))
    
    dropdownItems=getDropDownItems(cur_dict,dropdowns)
    rowPosition = 0
    traceTableValues={}
    for row in data:
        #print(row)
        if dlg.trace_type:
            traceTableValues[rowPosition]={}
        for col in range(len(row)):
            if col in list([i[0] for i in dropdowns]):
                #print('dropdown: '+str(col))
                comboBox = QComboBox()
                comboBox.addItems(dropdownItems[col].values())
                currentText=str([i for i in dropdownItems[col].values() if str(row[col]) == i.split(':')[0]][0])
                comboBox.setCurrentText(currentText)
                dlg.tableWidget.setCellWidget(rowPosition, col, comboBox)   
                if dlg.trace_type:
                    traceTableValues[rowPosition][col]=[currentText,'']
            else:
                if row[col]==None:
                    value=''
                else:
                    value=str(row[col])
                item=QTableWidgetItem(value)
                if col in deactivated:
                    item.setFlags(get_item_flag("ItemIsSelectable") | get_item_flag("ItemIsEnabled"))

                dlg.tableWidget.setItem(rowPosition , col, item)
                if dlg.trace_type:
                    traceTableValues[rowPosition][col]=[value,'']
        rowPosition+=1
    return traceTableValues

def showFilteredTableContent(cur_dict,conn,dlg,table,columns,filter,orderby,dropdowns,trace,deactivated):
    """show filtered table content"""
    #print('show filtered table content')
    #print(f'trace:{trace}')
    cur=conn.cursor()
    dlg.tableWidget.setRowCount(rowCountDB(table,filter,cur_dict))
    sql='SELECT {} FROM public.{} {} {} ;'.format(','.join(i for i in columns),table,filter,orderby) # nosec B608
    #print(sql)
    cur.execute(sql) 
    data = cur.fetchall()
    #print(data)
    dropdownItems=getDropDownItems(cur_dict,dropdowns)
    rowCount=0
    table_trace={}
    changedConnectionBundleType=''
    changedSimModel=''
    for row in data:
        for col in range(len(row)):
            if col in list([i[0] for i in dropdowns]):
                comboBox = QComboBox()
                for original_key, translated_text in dropdownItems[col].items():
                    comboBox.addItem(translated_text, original_key) # The second argument is the userData
                currentText=''
                if dropdownItems[col]:
                    for original_key, translated_text in dropdownItems[col].items():
                        if translated_text.split(':')[0]==str(row[col]):
                            currentText=translated_text
                comboBox.setCurrentText(currentText)
                if trace in ['conn_type_trace','bt_conns_trace']:
                    changedConnectionBundleType=currentText
                    comboBox.currentTextChanged.connect(dlg.changedDropdownItem)
                elif trace:
                    if col in [2,3]:
                        if col==2:
                            changedConnectionBundleType=currentText
                        if col==3:
                            changedSimModel=currentText
                        comboBox.currentTextChanged.connect(dlg.changedDropdownItem)
                dlg.tableWidget.setCellWidget(rowCount, col, comboBox)   
            else:
                item=QTableWidgetItem()
                #print(str(row[col]))
                #print(tr('@default',str(row[col])))
                item.setText(tr('@default',str(row[col])))
                item.setData(Qt.ItemDataRole.UserRole ,str(row[col]))
                if col in deactivated:
                    item.setFlags(get_item_flag("ItemIsSelectable") | get_item_flag("ItemIsEnabled"))
                dlg.tableWidget.setItem(rowCount , col, item)
        if trace in ['conn_type_trace','bt_conns_trace']:
            table_trace[rowCount]= [str(row[0]),'',changedConnectionBundleType.split(':')[0],'']
        elif trace:
            table_trace[rowCount]= [str(row[0])+'_'+str(row[1]),'',changedConnectionBundleType.split(':')[0],'']
            #print(table_trace)
        rowCount+=1
    #print(table_trace)
    return table_trace
        
def show_TableDialog(main=False,title='',table='',headers=[],columns='',dropdowns='',importFn=False,ok_fn=False,ok_fn_arg=[],openFn=False,openFnArg=['',[],[],'','',[],False,'',False,False,[0]],trace=False,deactivated=[0]):
    """Show types from table in DB"""
    #print('Manage connection types')
    openBtn=False
    if openFn:
        openBtn=True
    importBtn=False
    if importFn:
        importBtn=True
        
    dlg = TableDialog(title,headers,openBtn,importFn,True,trace)
    dlg.btn_saveAs.clicked.connect(lambda: copyTableRow(main.cur,dlg,dlg.tableWidget.currentRow(),dropdowns,openFn,openFnArg))
    if openFn:
        dlg.btn_open.clicked.connect(lambda: openFn(main,table,columns,dropdowns,dlg,dlg.tableWidget.currentRow(),openFnArg,trace=trace))
    if importFn:
        dlg.btn_import.clicked.connect(lambda: importFn(dlg,table,openFnArg,dropdowns))
    dlg.btn_ok.clicked.connect(lambda: saveTable(main.config,dlg,table,columns,dropdowns,openFnArg,[],ok_fn,ok_fn_arg,trace=trace,main=main))
    dlg.btn_cancel.clicked.connect(lambda: closeDialog(dlg))
    dlg.btn_delete.clicked.connect(lambda: deleteTableRowTrace(dlg,trace))
    dlg.btn_add.clicked.connect(lambda: addTableRowTrace(dlg,dropdowns,trace,[0],main.cur))
    dlg.traceTableValues=showTableContent(main.cur,main.conn,dlg,table,dropdowns,columns=columns,deactivated=deactivated)
    #print(dlg.traceTableValues)
    if trace:
        dlg.tableWidget.itemChanged.connect(dlg.changeItem)
    dlg.show()
    
def getValuesFromTableRow(dlg,dropdowns,row,columns,checkBoxes):
    values=[]
    p=False
    mdot=False
    #print(row)
    for col in range(dlg.tableWidget.columnCount()):
        if col in list([i[0] for i in dropdowns]):
            value=dlg.tableWidget.cellWidget(row, col).currentData()
            if not value:
                value=dlg.tableWidget.cellWidget(row, col).currentText()
                
            #print(value)
        elif col in checkBoxes:
            #print('check box')
            value=dlg.tableWidget.cellWidget(row, col).isChecked()
            #print(value)
        else:
            if dlg.tableWidget.item(row,col):
                value=dlg.tableWidget.item(row,col).data(Qt.ItemDataRole.UserRole)
                if not value:
                    value=dlg.tableWidget.item(row,col).text()
                #print(value)
                if value and columns[col]=='p':
                    p=True
                if value and columns[col]=='mdot':
                    mdot=True
                if not value and (columns[col].lower() in ['p','mdot','costs','invest_costs','operation_costs']):
                    value='Null'
            else:
                if columns[col].lower() in ['p','mdot','costs','invest_costs','operation_costs']:
                    value='Null'
                else:
                    value=''
        if isinstance(value, str) and ':' in value and value.split(':')[0].isnumeric():
            value=value.split(':')[0]
        if col not in checkBoxes and not value and columns[col] not in ['description']:
            return False
        if not isFloat(value) and value!='Null' or columns[col] in ['description']:
            value="'"+value + "'" 
        values.append(value)
    #print(values)
    if mdot and p:
        iface.messageBar().pushMessage("Error", "It is not possible to set the pressure and mass flow as boundary!", level=Qgis.Critical)
        return False
    return ','.join(str(i) for i in values)
 
 
def saveTable(config,dlg,table,columns,dropdowns,openFnArg,checkBoxes,ok_fn,ok_fn_arg,trace=False,main=None):
    """" Save table to DB an close dialog"""
    #print('Save table to DB an close dialog')
    sql="""TRUNCATE {} CASCADE;\n""".format(table)# nosec B608
    for row in range(dlg.tableWidget.rowCount()):
        values= getValuesFromTableRow(dlg,dropdowns,row,columns[1:-1].split(','),checkBoxes)
        if not values:
            #print('return')
            return False
        sql+="""INSERT INTO {} {} VALUES ({});\n""".format(table,columns,values)# nosec B608
    try:
        main.cur.execute(sql)
    except Exception as e:
        iface.messageBar().pushMessage("Error", f"An error occurred: {str(e)}", level=Qgis.Critical)
        return False
    delIfNotInDBIds(table,openFnArg,main.cur)
    if ok_fn:
        #print('----ok-fn---')
        ok_fn(ok_fn_arg[0],ok_fn_arg[1])
        
    if trace =='building_template':
        #print(dlg.traceTableValues)
        for row in dlg.traceTableValues:
            if not dlg.traceTableValues[row][1][0] and dlg.traceTableValues[row][1][1]:
                #add default building (located project handling)
                #print('***added building type***')
                src_dir=config['pathDistricts']+'lib\\ice\\building\\'
                templates_dir=main.plugin_dir+'\\{}\\building_templates\\'.format(main.config['projectName'])
                copyFile(src_dir+'default.idm',templates_dir,templates_dir+'{}.idm'.format(dlg.traceTableValues[row][1][1]))
                copy_tree_filter_extensions_and_folders(src_dir+'default', templates_dir+dlg.traceTableValues[row][1][1])

            elif dlg.traceTableValues[row][1][0] and dlg.traceTableValues[row][1][1]:
                if dlg.traceTableValues[row][1][0]!= dlg.traceTableValues[row][1][1]:
                    #rename building template
                    #print('***updated building type name***')
                    templates_dir=main.plugin_dir+'\\{}\\building_templates\\'.format(main.config['projectName'])
                    if os.path.exists(templates_dir):
                        file_src=templates_dir+'{}.idm'.format(dlg.traceTableValues[row][1][0])
                        file_tar=templates_dir+'{}.idm'.format(dlg.traceTableValues[row][1][1])
                        try:
                            os.rename(file_src, file_tar)
                            os.rename(templates_dir+'{}'.format(dlg.traceTableValues[row][1][0]), templates_dir+'{}'.format(dlg.traceTableValues[row][1][1]))
                        except:
                            iface.messageBar().pushMessage("Error", tr('@default','file_not_found!').format(file_src), level=Qgis.Critical)     
    main.dlg.statusMessage.setText(tr('@default','data_saved_successfully'))
    dlg.close()
        
def saveConnectionsTable(dlg,table,columns,dropdowns,openFnArg,checkBoxes,main):
    """ 1) check entries: is value (p,m,T)
        2) updates the changed boundary values in the templates
        3) save the table content in table public.connections"""
    if checkConnsInputValues(dlg):
        updateTemplateBoundaryValues(dlg,main.config,main.cur)
        saveTable(main.config,dlg,table,columns,dropdowns,openFnArg,checkBoxes,False,False,main=main)
        main.dlg.statusMessage.setText(tr('@default','connections_saved_successfully'))
        
def checkConnsInputValues(dlg):
    """is value (p,m,T)"""
    for row in range(dlg.tableWidget.rowCount()):
        if (dlg.tableWidget.cellWidget(row,2).isChecked() and not isNumber(dlg.tableWidget.item(row,5).text()) or #m
            not dlg.tableWidget.cellWidget(row,2).isChecked() and not isNumber(dlg.tableWidget.item(row,4).text()) or #p
            not isNumber(dlg.tableWidget.item(row,3).text())): #T
                iface.messageBar().pushMessage("Error", tr('@default','please_enter_number_table_row').format(row), level=Qgis.Critical)
                return False
    return True
         
def addConnectionsTableRow(dlg,dropdowns,row,cur):
    """Insert table row"""
    rowPosition = 0
    dlg.tableWidget.insertRow(rowPosition)
    dropdownItems=getDropDownItems(cur,dropdowns)
    values=[]
    for col in range(dlg.tableWidget.columnCount()):
        values.append('')
        if col in list([i[0] for i in dropdowns]):
            comboBox = QComboBox()
            for original_key, translated_text in dropdownItems[col].items():
                comboBox.addItem(translated_text, original_key) # The second argument is the userData
            dlg.tableWidget.setCellWidget(rowPosition, col, comboBox)
            comboBox.currentIndexChanged.connect(dlg.changedDropdownItem)            
        elif col==2:
            checkBox=QCheckBox()
            dlg.tableWidget.setCellWidget(0, col, checkBox)
            checkBox.stateChanged.connect(dlg.changedCheckboxState)
        else:
            if col in [0,5]:
                if col==0:
                    item=QTableWidgetItem(str(getMaxTableId(dlg.tableWidget)+1))
                    item.setFlags(get_item_flag("ItemIsSelectable") | get_item_flag("ItemIsEnabled"))
                else:
                    item=QTableWidgetItem('')
                    item.setFlags(item.flags() & ~qt_item_flag("ItemIsEnabled"))

                dlg.tableWidget.setItem(0,col,item)
            else:
                item=QTableWidgetItem('')
                dlg.tableWidget.setItem(0,col,item)
    #add row to dlg.traceTableValues in order to trace the changed values     
    for row in reversed(sorted(dlg.traceTableValues)):
        dlg.traceTableValues[row+1]=dlg.traceTableValues[row]
    #print(dlg.traceTableValues)
    dlg.traceTableValues[0]=['',dlg.tableWidget.item(0,4).text(),'',dlg.tableWidget.item(0,5).text(),'',dlg.tableWidget.item(0,3).text(),'',False,dlg.tableWidget.cellWidget(0,1).currentText().split(':')[0],''] #p_old,p_new,m_old,m_new,t_old,t_new,ctrl_old,ctrl_new,type_old,type_new
    #print(dlg.traceTableValues)
        
def showConnectionsContent(dlg,dropdowns,conn,cur_dict): 
    """show connections table content"""
    #print('show connections table content')
    table='connections'
    dlg.tableWidget.setRowCount(rowCountDB(table,'',cur_dict))
    sql='SELECT id,type,p_ctrl,temp,p,mdot,description FROM public.connections ORDER BY id;'
    #print(sql)
    cur=conn.cursor()
    cur.execute(sql) 
    data = cur.fetchall()
    dropdowns=[[1,'public','prefered_conn_dir','id','name']]
    dropdownItems=getDropDownItems(cur_dict,dropdowns)
    #print(dropdownItems)
    #print(list([i[0] for i in dropdowns]))
    rowCount=0

    for row in data:
        #print('--row--')
        #print(row)
        for col in range(len(row)):
            #print('--col--')
            #print(col)
            if col in list([i[0] for i in dropdowns]):
                comboBox = QComboBox()
                comboBox.addItems(dropdownItems[col].values())
                currentText=''
                if dropdownItems[col]:
                    for dropDownItem in dropdownItems[col].values():
                        if dropDownItem.split(':')[0]==str(row[col]):
                            currentText=dropDownItem
                comboBox.setCurrentText(currentText)
                dlg.tableWidget.setCellWidget(rowCount, col, comboBox)   
                comboBox.currentIndexChanged.connect(dlg.changedDropdownItem)            
            elif col==2:
                checkBox=QCheckBox()
                if row[col]==True:
                    checkBox.setChecked(True)
                checkBox.stateChanged.connect(dlg.changedCheckboxState)
                dlg.tableWidget.setCellWidget(rowCount, col, checkBox)
            else:
                #print('--else--')
                #print(col)
                #print(row[col])
                item=QTableWidgetItem('' if row[col]==None else str(row[col]))
                if col == 0:
                    item.setFlags(get_item_flag("ItemIsSelectable") | get_item_flag("ItemIsEnabled"))
                elif col == 4 and row[2]==True:
                    item.setFlags(item.flags() & ~qt_item_flag("ItemIsEnabled"))

                elif col == 5 and row[2]==False:
                    item.setFlags(item.flags() & ~qt_item_flag("ItemIsEnabled"))

                dlg.tableWidget.setItem(rowCount , col, item)
        
        dlg.traceTableValues[rowCount]= ['' if row[4]==None else str(row[4]),'','' if row[5]==None else str(row[5]),'',str(row[3]),'',row[2],'',str(row[1]),''] #p_old,p_new,m_old,m_new,t_old,t_new,ctrl_old,ctrl_new,type_old,type_new
        rowCount+=1
    #print(dlg.traceTableValues)
        
def showDefaults(dlg,defaults,template_name,cur,config):
    """show the default values of a table in the GUI"""
    #print('--showDefaults--')
    #print(defaults)
    for default in defaults:
        if default['column_name'] in ['template','pipe_bundle_type_id','network','type']:
            if default['column_name'] =='template':
                dropdownItems=getDropDownItems(cur,[[0,'public','{}_templates'.format(template_name),'template','template_name']])
            elif default['column_name'] =='type':
                dropdownItems=getDropDownItems(cur,[[0,'public','{}_types'.format(template_name),'id','type']])
            elif default['column_name'] =='pipe_bundle_type_id':
                dropdownItems=getDropDownItems(cur,[[0,'public','pipe_bundle_types','id','description']])
            elif default['column_name'] =='network':  
                dropdownItems=getDropDownItems(cur,[[0,config['versionName'],'network','id','description']])
            try:
                dlg.input[default['column_name']].clear()    
                
                try:
                    items={key : text.split(':')[0]+':'+tr("@default",text.split(':')[1]) for key,text in dropdownItems[0].items()}
                except:
                    items={key : tr("@default",text) for key,text in dropdownItems[0].items()}
                
                # Add items to the combobox, storing the original key as user data
                for original_key, translated_text in items.items():
                    dlg.input[default['column_name']].addItem(translated_text, original_key) # The second argument is the userData
                dlg.input[default['column_name']].setCurrentText("".join(i for i in dropdownItems[0].values() if i[0]==default['column_default']))
        
            except:
                pass

def writeDefaultsToDB(dlg,table,cur,config,plugin_dir,main):
    """Write default values to DB """
    for input in dlg.input:
        value=""
        try:
            value=dlg.input[input].currentText()
        except:
            if dlg.input[input].text().isnumeric():
                value=dlg.input[input].text()
        try:
            value=value.split(':')[0]
        except:
            pass
        if value:
            if value==tr("@default",'no_selection'):
                sql='ALTER TABLE "{}".{} ALTER COLUMN {} DROP DEFAULT;'.format(config['versionName'],table,input,value) # nosec B608
                #print(sql)
                cur.execute(sql)    
            else:
                sql='ALTER TABLE "{}".{} ALTER COLUMN {} SET DEFAULT {};'.format(config['versionName'],table,input,value) # nosec B608
                #print(sql)
                cur.execute(sql)
    dlg.close()

    setupFeatureLayerDialog(table,cur,config,plugin_dir)
    main.dlg.statusMessage.setText(tr('@default','data_saved_successfully'))

