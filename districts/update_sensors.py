from qgis.utils import iface
from qgis.PyQt.QtCore import QObject, pyqtSlot, pyqtSignal,QRunnable

from .ida_mosim_dialog import SensorSignalsDialog
from .utility_functions.sensor_signals import *
from .utility_functions.db import *
from .utility_functions.translations import *
from .utility_functions.dialog import *
from .supervisory_control import Supervisory_control

from .utility_functions.workers import APISignals,show_error_message
        
class UpdateSensors():
    def __init__(self,*args, **kwargs):
        self.config=kwargs['config']
        self.cur=kwargs['cur']
        self.dlg_main=kwargs['dlg_main']
        self.plugin_dir=kwargs['plugin_dir']
        self.loadedSensorData={} #{'source' : {'type' : sensor_data['type'],'templates' : [],'ids' : [],'conn_types' : [],'conns' : [],'measure' : sensor_data['measure'],'function' : sensor_data['function'],'test_value' : sensor_data['test_value'],'description' : sensor_data['description_source']}, 'target': {'type' : sensor_data['target_type'],'templates' : [],'ids' : [],'target' : None,'description' : ''}}
        self.sensorData={} #{'source' : {'type' : sensor_data['type'],'templates' : [],'ids' : [],'conn_types' : [],'conns' : [],'measure' : sensor_data['measure'],'function' : sensor_data['function'],'test_value' : sensor_data['test_value'],'description' : sensor_data['description_source']}, 'target': {'type' : sensor_data['target_type'],'templates' : [],'ids' : [],'target' : None,'description' : ''}}
        
        self.dlg=SensorSignalsDialog(self.config,self.plugin_dir,self.dlg_main)
        self.dlg.btn_ok.clicked.connect(self.runSensorSignals)
        self.dlg.btn_cancel.clicked.connect(lambda: closeDialog(self.dlg))
        self.dlg.btn_add.clicked.connect(self.addSensor)
        self.dlg.btn_del.clicked.connect(self.delSensor)
        self.dlg.tableWidget_source.currentCellChanged.connect(self.dlg.tableWidget_target.selectRow)
        self.dlg.tableWidget_target.currentCellChanged.connect(self.dlg.tableWidget_source.selectRow)
        self.loadSensorTableValues()
        #print(self.loadedSensorData)
        self.dlg.show()  

    def insertIntoSensorsTable(self,table,row,sensor_id):
        sql="""INSERT INTO sensors(sensor_id) VALUES ({});""".format(sensor_id)# nosec B608
        #print(sql)
        self.cur.execute(sql)
             
    def collectSensortemplatesTableData(self,table,row,sensor_id,sensor):
        dropDown=table.cellWidget(row, 2)
        if dropDown!=None:
            self.sensorData[int(sensor_id)][sensor]['templates']=[{dropDown.itemText(i).split(':')[0] : dropDown.itemChecked(i)} for i in range(dropDown.count()) if dropDown.itemData(i) != 'check_all_items']                 
                    
    def insertIntoSensorSourceConntypesTable(self,table,row,sensor_id):
        dropDown=table.cellWidget(row, 3)
        if dropDown!=None:
            self.sensorData[int(sensor_id)][sensor]['conn_types']=[{dropDown.itemText(i).split(':')[0] : dropDown.itemChecked(i)} for i in range(dropDown.count()) if dropDown.itemData(i) != 'check_all_items']                  
                    
    def insertIntoSensorSourceConnsTable(self,table,row,sensor_id):
        dropDown=table.cellWidget(row, 4)

    def addSensor(self):
        """INSERT a sensor to the source and target table"""
        rowPosition = self.dlg.tableWidget_source.rowCount()
        #print('&&&&&&&&&&&&&&&&&&&&&&&&&')
        #print(rowPosition)
        
        try:
            maxId=max([int(self.dlg.tableWidget_source.item(i,0).text())+1 for i in range(self.dlg.tableWidget_source.rowCount())])     
        except:
            maxId=1
        
        #source table
        self.dlg.tableWidget_source.insertRow(rowPosition)
        item = QTableWidgetItem(str(maxId))
        item.setFlags(item.flags() & ~qt_item_flag("ItemIsEditable"))

        self.dlg.tableWidget_source.setItem(rowPosition,0,item)
        for i in range(2,5):
            self.setCheckableDropDownItemsTable(self.dlg.tableWidget_source,[],rowPosition,i,[])
        self.setTableDropDown(self.dlg.tableWidget_source,getFilteredDropDownItemNames(self.cur,[[1,'public','measure','measure',[1,2,3,4,6]]]),'1',5,rowPosition,self.measureChanged)
        self.setTableDropDown(self.dlg.tableWidget_source,getFilteredDropDownItemNames(self.cur,[[1,'public','signal_function','function',[1,2,3,4]]]),'1',6,i,False)
        self.dlg.tableWidget_source.setItem(rowPosition,7,QTableWidgetItem('1.0'))
        self.dlg.tableWidget_source.setItem(rowPosition,8,QTableWidgetItem(''))
        self.setTableDropDown(self.dlg.tableWidget_source,getFilteredDropDownItemNames(self.cur,[[1,'public','type','name',[1,2,3]]]),'customer',1,rowPosition,self.sourceTypeChanged) #dropdown type
        self.sourceTypeChanged(self.dlg.tableWidget_source,0,1,rowPosition)
        self.dlg.tableWidget_source.selectRow(rowPosition)
        
        #target table
        self.dlg.tableWidget_target.insertRow(rowPosition)
        item = QTableWidgetItem(str(maxId))
        item.setFlags(item.flags() & ~qt_item_flag("ItemIsEditable"))

        self.dlg.tableWidget_target.setItem(rowPosition,0,item)
        for i in range(2,3):
            self.setCheckableDropDownItemsTable(self.dlg.tableWidget_target,[],rowPosition,i,[])
        self.setTableDropDown(self.dlg.tableWidget_target,getFilteredDropDownItemNames(self.cur,[[1,'public','type','name',[1,2,3]]]),'supervisory',1,rowPosition,self.targetTypeChanged) #dropdown type
        self.dlg.tableWidget_target.setItem(rowPosition,3,QTableWidgetItem(''))
        self.targetTypeChanged(self.dlg.tableWidget_target,0,1,rowPosition)
        self.dlg.tableWidget_target.selectRow(rowPosition)

    def delSensor(self):
        """Delete a sensor from a table"""
        row_index=self.dlg.tableWidget_source.currentRow()
        #print(row_index)
        if row_index!=-1:
            self.dlg.tableWidget_source.removeRow(row_index)
            self.dlg.tableWidget_target.removeRow(row_index)
        else:
            iface.messageBar().pushMessage("Info", "No item selected!", level=Qgis.Info)
        
    def loadSensorTableValues(self):
        """Load the sensor table values """
        sql="""SELECT s_s.sensor_id, s_s.type AS source_type, type.name AS source_type_name, s_s.template AS source, m.measure, m.id AS measure_id, f.function, f.id AS function_id, s_s.test_value, s_s.description AS description_source, s_t.type AS target_type
    FROM sensor_source s_s, public.type, public.measure m, public.signal_function f, sensor_target s_t
    WHERE s_s.type=type.id AND s_s.measure=m.id AND s_s.function=f.id AND s_t.sensor_id=s_s.sensor_id
    ORDER BY s_s.sensor_id;"""
        #print(sql)
        i=0
        self.cur.execute(sql)
        for sensor_data in self.cur.fetchall():
            self.loadedSensorData[sensor_data['sensor_id']]={'source' : {'type' : sensor_data['source_type'],'templates' : [],'conn_types' : [],'conns' : [],'measure' : sensor_data['measure_id'],'function' : sensor_data['function_id'],'test_value' : float(sensor_data['test_value']),'description' : sensor_data['description_source']}, 
                'target': {'type' : sensor_data['target_type'],'templates' : [],'target' : None,'description' : ''}}
            self.dlg.tableWidget_source.insertRow(i)
            item = QTableWidgetItem(str(sensor_data['sensor_id']))
            item.setFlags(item.flags() & ~qt_item_flag("ItemIsEditable"))

            self.dlg.tableWidget_source.setItem(i , 0, item)
            self.setTableDropDown(self.dlg.tableWidget_source,getFilteredDropDownItemNames(self.cur,[[1,'public','type','name',[1,2,3]]]),sensor_data['source_type_name'],1,i,self.sourceTypeChanged) #dropdown type
            if sensor_data['source_type']==3:
                self.setTableDropDown(self.dlg.tableWidget_source,getFilteredDropDownItemNames(self.cur,[[1,'public','measure','measure',[5]]]),sensor_data['measure'],5,i,self.measureChanged)
                self.setTableDropDown(self.dlg.tableWidget_source,getFilteredDropDownItemNames(self.cur,[[1,'public','signal_function','function',[5,6]]]),sensor_data['function'],6,i,False)
                for col in range(2,6):
                    self.setCheckableDropDownItemsTable(self.dlg.tableWidget_source,[],i,col,[]) 
            else:
                self.setTableDropDown(self.dlg.tableWidget_source,getFilteredDropDownItemNames(self.cur,[[1,'public','measure','measure',[1,2,3,4,5]]]),sensor_data['measure'],5,i,self.measureChanged)
                self.setFilteredTemplateDropdownItems(self.dlg.tableWidget_source,sensor_data['source_type_name'].replace(' ','_'),sensor_data['sensor_id'],i,'source')
                self.setFilteredConnTypesDropdownItems(sensor_data['source_type_name'].replace(' ','_'),sensor_data['sensor_id'],i)
                self.setFilteredConnsDropdownItems(sensor_data['source_type_name'].replace(' ','_'),sensor_data['sensor_id'],i)
                if sensor_data['source_type']==3 or sensor_data['target_type']==3: #source type==supervisory control or target type==supervisory control
                    if sensor_data['source_type']==3: #source type==supervisory control
                        self.setTableDropDown(self.dlg.tableWidget_source,getFilteredDropDownItemNames(self.cur,[[1,'public','signal_function','function',[5,6]]]),sensor_data['function'],6,i,False)
                    else:
                        self.setTableDropDown(self.dlg.tableWidget_source,getFilteredDropDownItemNames(self.cur,[[1,'public','signal_function','function',[1,2,3,4,6]]]),sensor_data['function'],6,i,False)
                else:
                    self.setTableDropDown(self.dlg.tableWidget_source,getFilteredDropDownItemNames(self.cur,[[1,'public','signal_function','function',[1,2,3,4]]]),sensor_data['function'],6,i,False)
            self.dlg.tableWidget_source.setItem(i,7,QTableWidgetItem(str(sensor_data['test_value'])))
            self.dlg.tableWidget_source.setItem(i,8,QTableWidgetItem(sensor_data['description_source']))
            i+=1            
        
        i=0  
        sql="""SELECT s_t.sensor_id, s_t.type AS target_type, type.name AS target_type_name, s_t.template, s_t.description AS description_target
    FROM sensor_target s_t, public.type
    WHERE s_t.type=type.id
    ORDER BY s_t.sensor_id;"""
        self.cur.execute(sql)
        for sensor_data in self.cur.fetchall():
            self.loadedSensorData[sensor_data['sensor_id']]['target']['description']=sensor_data['description_target']
            self.dlg.tableWidget_target.insertRow(i)
            item = QTableWidgetItem(str(sensor_data['sensor_id']))
            item.setFlags(item.flags() & ~qt_item_flag("ItemIsEditable"))

            self.dlg.tableWidget_target.setItem(i , 0, item)
            self.setTableDropDown(self.dlg.tableWidget_target,getFilteredDropDownItemNames(self.cur,[[1,'public','type','name',[1,2,3]]]),sensor_data['target_type_name'],1,i,self.targetTypeChanged) #dropdown type
            if sensor_data['target_type']==3:
                for col in range(2,3):
                    self.setCheckableDropDownItemsTable(self.dlg.tableWidget_target,[],i,col,[]) 
            else:
                self.setFilteredTemplateDropdownItems(self.dlg.tableWidget_target,sensor_data['target_type_name'].replace(' ','_'),sensor_data['sensor_id'],i,'target')
            self.dlg.tableWidget_target.setItem(i,3,QTableWidgetItem(sensor_data['description_target']))
            i+=1
        #print(self.loadedSensorData)

    def setTableDropDown(self,table,dropdownItems,currentData,col,row,signal_function):

        try:
            items={key : text.split(':')[0]+':'+tr("@default",text.split(':')[1]) for key,text in dropdownItems[1].items()}
        except:
            items={key : tr("@default",text) for key,text in dropdownItems[1].items()}
        comboBox = QComboBox()
        
        # Add items to the combobox, storing the original key as user data
        for original_key, translated_text in items.items():
            comboBox.addItem(translated_text, original_key) # The second argument is the userData
        index = comboBox.findData(currentData)
        if index != -1:
            comboBox.setCurrentIndex(index)
        if signal_function:
            comboBox.currentIndexChanged.connect(lambda selected_index, column=col,row=row: signal_function(table,selected_index,column,row))
        table.setCellWidget(row, col, comboBox)   
    
    def measureChanged(self,table,selected_index,column,row): 
        #print('************measure changed***************')
        source_type=table.cellWidget(row, 1).currentData()
        target_type=self.dlg.tableWidget_target.cellWidget(row, 1).currentData()
        if table.cellWidget(row,5).currentData() =='custom':
            #print('deactivate conn type')
            self.setCheckableDropDownItemsTable(table,[],row,3,[]) 
            self.setCheckableDropDownItemsTable(table,[],row,4,[]) 
            if source_type =='supervisory' or target_type=='supervisory':
                if target_type=='supervisory':
                    self.setTableDropDown(table,getFilteredDropDownItemNames(self.cur,[[1,'public','signal_function','function',[1,2,3,4,6]]]),'',6,row,False)
                else:
                    self.setTableDropDown(table,getFilteredDropDownItemNames(self.cur,[[1,'public','signal_function','function',[5,6]]]),'',6,row,False)
            else:
                self.setTableDropDown(table,getFilteredDropDownItemNames(self.cur,[[1,'public','signal_function','function',[1,2,3,4]]]),'',6,row,False)
        else:
            self.setDropDownConntypes(table,3,row,source_type)
            self.setDropDownConns(table,4,row,source_type)
            if target_type=='supervisory':
                self.setTableDropDown(table,getFilteredDropDownItemNames(self.cur,[[1,'public','signal_function','function',[1,2,3,4,6]]]),'',6,row,False)
            else:
                self.setTableDropDown(table,getFilteredDropDownItemNames(self.cur,[[1,'public','signal_function','function',[1,2,3,4]]]),'',6,row,False)
        
    def setFilteredConnTypesDropdownItems(self,type,id,row):
        sql="""SELECT c_type.id AS conn_type_id, c_type.description, s_ct.active
    FROM source_conn_type s_ct, public.connection_types c_type
    WHERE c_type.id=s_ct.conn_type AND s_ct.source_id={}
    GROUP BY c_type.id, c_type.description, s_ct.active
    ORDER BY c_type.id;""".format(id) # nosec B608
        #print(sql)
        self.cur.execute(sql)
        source_conn_types=self.cur.fetchall()
        #print(source_conn_types)
        comboBoxCheckable = CheckableComboBox()
        comboBoxCheckable.addItem(tr("@default",'check_all_items'),'check_all_items')
        comboBoxCheckable.addItems([str(i['conn_type_id'])+':'+i['description'] for i in source_conn_types])
        self.loadedSensorData[id]['source']['conn_types']={i['conn_type_id'] : i['active'] for i in source_conn_types}

        for i in range(len(source_conn_types)):
            comboBoxCheckable.setItemChecked(i+1,source_conn_types[i]['active'])
        if self.dlg.tableWidget_source.cellWidget(row,5).currentData()!='power':
            comboBoxCheckable.activated.connect(lambda signal, column=4,row=row: self.setDropDownConns(self.dlg.tableWidget_source,column,row,type))
        self.dlg.tableWidget_source.setCellWidget(row, 3, comboBoxCheckable) 
        
    def setFilteredConnsDropdownItems(self,type,id,row):
        sql="""SELECT conns.id AS conn_id, conns.description, s_conns.active
    FROM source_conns s_conns, public.connections conns
    WHERE s_conns.connection_id=conns.id AND s_conns.source_id={}
    GROUP BY conns.id, conns.description, s_conns.active
    ORDER BY conns.id;""".format(id) # nosec B608
        #print(sql)
        self.cur.execute(sql)
        source_conns=self.cur.fetchall()
        #print(source_conns)
        comboBoxCheckable = CheckableComboBox()
        comboBoxCheckable.addItem(tr("@default",'check_all_items'),'check_all_items')
        comboBoxCheckable.addItems([str(i['conn_id'])+':'+i['description'] for i in source_conns])
        self.loadedSensorData[id]['source']['conns']={i['conn_id'] : i['active'] for i in source_conns}
        for i in range(len(source_conns)):
            comboBoxCheckable.setItemChecked(i+1,source_conns[i]['active'])
        self.dlg.tableWidget_source.setCellWidget(row, 4, comboBoxCheckable) 
        
    def getCheckedItemsFromTable(self,dropDown):
        items=[]
        for i in range(dropDown.count()):
            if dropDown.itemData(i) != 'check_all_items' and dropDown.itemChecked(i)==True:
                items.append(dropDown.itemText(i).split(':')[0])
        return items
        
    def setDropDowntemplates(self,table,col,row,type):
        #print('set templates')
        dropDown=table.cellWidget(row, col)
        if dropDown!=None:
            templates=self.getCheckedItemsFromTable(dropDown)
            #print(templates)
            if templates:
                dropdownItems=[i['name'] for i in getTemplatesInfo(type,self.cur)]  
                self.setCheckableDropDownItemsTable(table,dropdownItems,row,2,[self.setDropDownConntypes,3,type])
                if not dropdownItems:
                    for i in range(3,5):
                        if table.cellWidget(row, i).__class__.__name__=='CheckableComboBox': 
                            self.setCheckableDropDownItemsTable(table,[],row,i,[]) 
            else:
                for i in range(2,5):
                    if table.cellWidget(row, i).__class__.__name__=='CheckableComboBox': 
                        self.setCheckableDropDownItemsTable(table,[],row,i,[]) 

    def setDropDowntemplatesTarget(self,table,col,row,type):
        #print('set templates target')
        dropDown=table.cellWidget(row, col)
        if dropDown!=None:
            templates=self.getCheckedItemsFromTable(dropDown)
            if templates:
                dropdownItems=[i['name'] for i in getTemplatesInfo(type,self.cur)]
                #print(dropdownItems)
                #self.setCheckableDropDownItemsTable(table,dropdownItems,row,2,[self.setDropDownIds,3,type])
                if not dropdownItems:
                    for i in range(3,3):
                        if table.cellWidget(row, i).__class__.__name__=='CheckableComboBox': 
                            self.setCheckableDropDownItemsTable(table,[],row,i,[]) 
            else:
                for i in range(2,3):
                    self.setCheckableDropDownItemsTable(table,[],row,i,[]) 

    def setDropDownConntypes(self,table,col,row,type):
        #print('set conn types')
        dropDown=table.cellWidget(row, 2)
        #print(str(row) +';'+str(col))
        if dropDown!=None:
            #print('+++++++++++++++++++++++')
            templates=[]
            for i in range(dropDown.count()):
                if dropDown.itemChecked(i):
                    templates.append(dropDown.itemText(i).split(':')[0])
            #print(templates)
            if templates and table.cellWidget(row, 5).currentData()!='custom':
                #print('!=custom')
                sql="""SELECT conn_t.id AS conn_type_id, conn_t.description
    FROM public.bundle_type_conns b_t_conns, "{}".{}s f, public.{}_templates t, public.connection_types conn_t
    WHERE t.template IN ({}) AND t.conn_bundle_type=b_t_conns.conn_bundle_type_id AND f.template=t.template AND conn_t.id=b_t_conns.conn_type_id
    GROUP BY conn_t.id,conn_t.description;""".format(self.config['versionName'],type,type,','.join(templates)) # nosec B608
                self.cur.execute(sql)
                conntypes=self.cur.fetchall()
                #print(conntypes)
                dropdownItems=[str(i['conn_type_id']) + ':' + str(i['description']) for i in conntypes]
                #print(dropdownItems)
                self.setCheckableDropDownItemsTable(table,dropdownItems,row,3,[self.setDropDownConns,4,type])

            else:
                for i in range(3,5):
                    self.setCheckableDropDownItemsTable(table,[],row,i,[]) 

    def setDropDownConns(self,table,col,row,type):
        #print('set conns')
        dropDown=table.cellWidget(row, col-1)
        #print(str(row) +';'+str(col))
        if dropDown!=None:
            #print('+++++++++++++++++++++++')
            #print(dropDown.itemText(0))
            conn_types=[]
            for i in range(dropDown.count()):
                if dropDown.itemChecked(i):
                    conn_types.append(dropDown.itemText(i).split(':')[0])
            #print(conn_types)
            if conn_types:
                sql="""SELECT conns.id AS conn_id, conns.description
    FROM public.connections conns, public.connection_types conn_t, public.connection_type_connections c_t_conns
    WHERE c_t_conns.connection_id=conns.id AND conn_t.id=c_t_conns.connection_type_id AND conn_t.id IN ({}) 
    GROUP BY conns.id, conns.description
    ORDER BY conns.id;""".format(','.join(conn_types)) # nosec B608
                #print(sql)
                self.cur.execute(sql)
                conns=self.cur.fetchall()
                #print(conns)
                dropdownItems=[str(i['conn_id']) + ':' + str(i['description']) for i in conns]
                #print(dropdownItems)
                if table.cellWidget(row,5).currentData() in ['power','custom']:
                    #print('deactivated dropdown conns')
                    self.setCheckableDropDownItemsTable(table,[],row,4,[])
                else:
                    #print('activated dropdown conns') 
                    self.setCheckableDropDownItemsTable(table,dropdownItems,row,4,[])
            else:
                for i in range(4,5):
                    self.setCheckableDropDownItemsTable(table,[],row,i,[]) 
                    
    def setFilteredTemplateDropdownItems(self,table,type,id,row,sensor,checkActive=True):
        #print('--setFilteredTemplateDropdownItems--')
        sql="""SELECT s_t.active, f_t.template, f_t.template_name
    FROM {}_template s_t, {}_templates f_t
    WHERE s_t.{}_id={} AND f_t.template=s_t.template
    ORDER BY s_t.template;""".format(sensor,type,sensor,id) # nosec B608
        #print(sql)
        self.cur.execute(sql)
        templates=self.cur.fetchall()
        #print(templates)
        
        #print(sensor)
        #print(self.loadedSensorData)
        comboBoxCheckable = CheckableComboBox()
        comboBoxCheckable.addItem(tr("@default",'check_all_items'),'check_all_items')
        
        items={template['template_name'] : str(template['template'])+':'+tr("@default",template['template_name']) for template in templates}
        # Add items to the comboBoxCheckable, storing the original key as user data
        for original_key, translated_text in items.items():
            comboBoxCheckable.addItem(translated_text, original_key) # The second argument is the userData
                    
        self.loadedSensorData[id][sensor]['templates']={i['template'] : i['active'] for i in templates}
        for i in range(len(templates)):
            comboBoxCheckable.setItemChecked(i+1,templates[i]['active'] if checkActive else False)
        comboBoxCheckable.activated.connect(lambda signal, column=3,row=row: self.setDropDownConntypes(table,column,row,type))
        table.setCellWidget(row, 2, comboBoxCheckable) 
    
    def setCheckableDropDownItemsTable(self,table,dropdownItems,row,col,signal_args):
        #print('--setCheckableDropDownItemsTable--')
        oldDropdown=table.cellWidget(row, col)
        oldTrueItems=[]
        if oldDropdown!=None:
            for i in range(oldDropdown.count()):
                if table.cellWidget(row, col).__class__.__name__=='CheckableComboBox':
                    if oldDropdown.itemChecked(i)==True:
                        oldTrueItems.append(oldDropdown.itemText(i))
        #print(oldTrueItems)
        comboBoxCheckable = CheckableComboBox()
        comboBoxCheckable.addItem(tr("@default",'check_all_items'),'check_all_items')
        
        try:
            items={i : i.split(':')[0]+':'+tr("@default",i.split(':')[1]) for i in dropdownItems}
            # Add items to the comboBoxCheckable, storing the original key as user data
            for original_key, translated_text in items.items():
                comboBoxCheckable.addItem(translated_text, original_key) # The second argument is the userData
        except:
            comboBoxCheckable.addItems(dropdownItems)
            
                
        #print(dropdownItems)

        for i in range(len(dropdownItems)):
            #print(i)
            if dropdownItems[i] in oldTrueItems:
                comboBoxCheckable.setItemChecked(i+1,True) 
            else:
                #print(row)
                #print(col)
                comboBoxCheckable.setItemChecked(i+1,False)
        if signal_args:
            #print('----')
            #print(signal_args)
            comboBoxCheckable.activated.connect(lambda signal, column=signal_args[1],row=row: signal_args[0](table,column,row,signal_args[2]))
        table.setCellWidget(row, col, comboBoxCheckable) 
        #print('setCheckableDropDownItemsTable finished')
        

        
    def sourceTypeChanged(self,table,selected_index,column,row):
        #print('source type changed')
        source_type=table.cellWidget(row, column).currentData()
        if self.dlg.tableWidget_target.cellWidget(row, column):
            target_type=self.dlg.tableWidget_target.cellWidget(row, column).currentData()
            if source_type==target_type and source_type=='supervisory':
                #print('+++source source_type==target type+++')
                self.setTableDropDown(self.dlg.tableWidget_target,getFilteredDropDownItemNames(self.cur,[[1,'public','type','name',[1,2,3]]]),getFilteredDropDownItems(self.cur,['type','id','name','id',int(getTypeIdByName(table.cellWidget(row, column).currentData()))%3+1])[0],1,row,self.targetTypeChanged)
                self.targetTypeChanged(self.dlg.tableWidget_target,'',1,row)
        else:
            target_type='supervisory'
        #print('+++++target type:'+target_type+'++++')
        
        if source_type=='supervisory':
            #print('supervisory')
            self.setCheckableDropDownItemsTable(table,[],row,column+1,[])
            for i in range(2,5):
                self.setCheckableDropDownItemsTable(table,[],row,i,[])  
            self.setTableDropDown(table,getFilteredDropDownItemNames(self.cur,[[1,'public','measure','measure',[5]]]),'1',5,row,self.measureChanged)
            self.setTableDropDown(table,getFilteredDropDownItemNames(self.cur,[[1,'public','signal_function','function',[5,6]]]),'customer',6,row,False)
        else:
            dropdownItems=[i['name'] for i in getTemplatesInfo(source_type,self.cur)]
            #print('row:'+str(row))
            #print('column:'+str(column))
            self.setCheckableDropDownItemsTable(table,dropdownItems,row,column+1,[self.setDropDownConntypes,2,source_type])
            self.setTableDropDown(table,getFilteredDropDownItemNames(self.cur,[[1,'public','measure','measure',[1,2,3,4,5]]]),'1',5,row,self.measureChanged)
            self.setTableDropDown(table,getFilteredDropDownItemNames(self.cur,[[1,'public','signal_function','function',[1,2,3,4,6] if target_type=='supervisory' else [1,2,3,4]]]),'min',6,row,False)
            for i in range(3,5):
                self.setCheckableDropDownItemsTable(table,[],row,i,[])  

    def targetTypeChanged(self,table,selected_index,column,row):
        #print('target type changed')
        target_type=table.cellWidget(row, column).currentData()
        if self.dlg.tableWidget_source.cellWidget(row, column):
            source_type=self.dlg.tableWidget_source.cellWidget(row, column).currentData()
            if target_type==source_type and target_type=='supervisory':
                #print('+++source type==target type+++')
                self.setTableDropDown(self.dlg.tableWidget_source,getFilteredDropDownItemNames(self.cur,[[1,'public','type','name',[1,2,3]]]),getFilteredDropDownItems(self.cur,['type','id','name','id',int(getTypeIdByName(table.cellWidget(row, column).currentData()))%3+1])[0],1,row,self.sourceTypeChanged)
                self.sourceTypeChanged(self.dlg.tableWidget_source,'',1,row)
        else:
            source_type='customer'
        #print('+++++'+source_type+'++++')
        #print(type)
        if target_type=='supervisory':
            #print('supervisory')
            self.setCheckableDropDownItemsTable(table,[],row,column+1,[])
        else:
            dropdownItems=[i['name'] for i in getTemplatesInfo(target_type,self.cur)]
            #print(dropdownItems)
            self.setCheckableDropDownItemsTable(table,dropdownItems,row,column+1,[self.setDropDowntemplatesTarget,2,target_type])
        self.measureChanged(self.dlg.tableWidget_source,selected_index,column,row)

    def runSensorSignals(self):
        self.worker_sensors = WorkerSensors(config=self.config,plugin_dir=self.plugin_dir,dlg=self.dlg,loadedSensorData=self.loadedSensorData,sensorData=self.sensorData)
        QThreadPool.globalInstance().start(self.worker_sensors) 
        self.worker_sensors.signals.error.connect(show_error_message)
        self.worker_sensors.signals.progress.connect(self.dlg.update_progress)   
        self.worker_sensors.signals.finished.connect(self.dlg.update_finished)   
        

def getStoredSensorTableValues(cur):
    """Load the sensor table values """
    sql="""SELECT s_s.sensor_id, s_s.type AS source_type, type.name AS source_type_name, s_s.template AS source, m.measure, m.id AS measure_id, f.function, f.id AS function_id, s_s.test_value, s_s.description AS description_source, s_t.type AS target_type
    FROM sensor_source s_s, public.type, public.measure m, public.signal_function f, sensor_target s_t
    WHERE s_s.type=type.id AND s_s.measure=m.id AND s_s.function=f.id AND s_t.sensor_id=s_s.sensor_id
    ORDER BY s_s.sensor_id;"""
    #print(sql)
    cur.execute(sql)
    loadedSensorData={}
    for sensor_data in cur.fetchall():
        loadedSensorData[sensor_data['sensor_id']]={'source' : {'type' : sensor_data['source_type'],'templates' : {},'conn_types' : [],'conns' : [],'measure' : sensor_data['measure_id'],'function' : sensor_data['function_id'],'test_value' : float(sensor_data['test_value']),'description' : sensor_data['description_source']}, 
            'target': {'type' : sensor_data['target_type'],'templates' : {},'description' : ''}}
        loadedSensorData=getFilteredTemplates(cur,sensor_data['source_type_name'],sensor_data['sensor_id'],'source',loadedSensorData=loadedSensorData)
        loadedSensorData=getFilteredConnTypes(cur,sensor_data['sensor_id'],loadedSensorData=loadedSensorData)
        loadedSensorData=getFilteredConns(cur,sensor_data['sensor_id'],loadedSensorData=loadedSensorData)        
    
    sql="""SELECT s_t.sensor_id, s_t.type AS target_type, type.name AS target_type_name, s_t.template, s_t.description AS description_target
    FROM sensor_target s_t, public.type
    WHERE s_t.type=type.id
    ORDER BY s_t.sensor_id;"""
    #print(sql)
    cur.execute(sql)
    for sensor_data in cur.fetchall():
        try:
            loadedSensorData[sensor_data['sensor_id']]['target']['description']=sensor_data['description_target']
            loadedSensorData=getFilteredTemplates(cur,sensor_data['target_type_name'],sensor_data['sensor_id'],'target',loadedSensorData=loadedSensorData)
        except:
            pass

    #print(loadedSensorData)
    return loadedSensorData

def getFilteredTemplates(cur,feature_type,id,sensor_type,loadedSensorData=None):
    if feature_type in ('customer','energy_plant'):
        sql="""SELECT s_t.active, f_t.template, f_t.template_name
        FROM {}_template s_t, {}_templates f_t
        WHERE s_t.{}_id={} AND f_t.template=s_t.template
        ORDER BY s_t.template;""".format(sensor_type,feature_type,sensor_type,id) # nosec B608
        #print(sql)
        cur.execute(sql)
        templates=cur.fetchall()
        #print(templates)
        if loadedSensorData:
            loadedSensorData[id][sensor_type]['templates']={i['template'] : i['active'] for i in templates}
            #print(loadedSensorData)
            return loadedSensorData
        else:
            return templates
    else:
        return loadedSensorData


def getFilteredConnTypes(cur,id,loadedSensorData=None):
    sql="""SELECT c_type.id AS conn_type_id, c_type.description, s_ct.active
    FROM source_conn_type s_ct, public.connection_types c_type
    WHERE c_type.id=s_ct.conn_type AND s_ct.source_id={}
    GROUP BY c_type.id, c_type.description, s_ct.active
    ORDER BY c_type.id;""".format(id) # nosec B608
    #print(sql)
    cur.execute(sql)
    source_conn_types=cur.fetchall()
    #print(source_conn_types)
    if loadedSensorData:
        loadedSensorData[id]['source']['conn_types']={i['conn_type_id'] : i['active'] for i in source_conn_types}
        #print(loadedSensorData)
        return loadedSensorData
    else:
        return source_conn_types

        
def getFilteredConns(cur,id,loadedSensorData=None):
    sql="""SELECT conns.id AS conn_id, conns.description, s_conns.active
    FROM source_conns s_conns, public.connections conns
    WHERE s_conns.connection_id=conns.id AND s_conns.source_id={}
    GROUP BY conns.id, conns.description, s_conns.active
    ORDER BY conns.id;""".format(id) # nosec B608
    #print(sql)
    cur.execute(sql)
    source_conns=cur.fetchall()
    #print(source_conns)
    if loadedSensorData:
        loadedSensorData[id]['source']['conns']={i['conn_id'] : i['active'] for i in source_conns}
        #print(loadedSensorData)
        return loadedSensorData
    else:
        return source_conns

def removeResultSensors(cur,added_sensor_ids):
    sql=''
    for i in added_sensor_ids:
        #print(i)
        if isinstance(i,list):
            sql+=''.join(["""DELETE FROM sensors WHERE id={};\n""".format(j['id']) for j in i]) # nosec B608
        else:
            sql+="""DELETE FROM sensors WHERE id={};\n""".format(i) # nosec B608
    #print(sql)
    if sql:
        cur.execute(sql)
        
def collectSensorSourceTableData(sensorData,table,row,sensor_id):
    if table.cellWidget(row, 6).currentIndex()==-1:
        function=1
    else:
        function=table.cellWidget(row, 6).currentIndex()+1
    if table.cellWidget(row, 1).currentIndex()==2:
        measure=5
        function+=4
    else:
        measure=table.cellWidget(row, 5).currentIndex()+1
    if table.cellWidget(row, 6).currentData()=='individual_signals':
        function=6
    if table.cellWidget(row, 6).currentData()=='same_signal':
        function=5
    sensorData[int(sensor_id)]['source']['type']=int(getTypeIdByName(table.cellWidget(row, 1).currentData()))
    sensorData[int(sensor_id)]['source']['measure']=measure
    sensorData[int(sensor_id)]['source']['function']=function
    sensorData[int(sensor_id)]['source']['test_value']=float(table.item(row,7).text())
    sensorData[int(sensor_id)]['source']['description']=table.item(row,8).text()
    return sensorData
    
def collectCheckableDropdownTableData(table,row,sensor_id,table_col):
    dropDown=table.cellWidget(row, table_col)
    return {int(dropDown.itemText(i).split(':')[0].split('(')[0]) : dropDown.itemChecked(i) for i in range(dropDown.count()) if dropDown.itemData(i) != 'check_all_items'}
    
def collectSensorTargetTableData(sensorData,table,row,sensor_id):
    sensorData[int(sensor_id)]['target']['type']=int(getTypeIdByName(table.cellWidget(row, 1).currentData()))
    sensorData[int(sensor_id)]['target']['description']=table.item(row,3).text()
    return sensorData
    
def writeSensorsToDB(cur,config,dlg=None,sensorData={},loadedSensorData={}):
    """Write sensor data to the DB"""
    #print('Save table to DB an close dialog')
    
    #get sensorData
    if dlg:
        print(dlg)
        for row in range(dlg.tableWidget_source.rowCount()):
            print(row)
            sensor_id=dlg.tableWidget_source.item(row,0).text()
            sensorData[int(sensor_id)]={'source' : {'type' : None,'templates' : [],'conn_types' : [],'conns' : [],'measure' : None,'function' : None,'test_value' : None,'description' : None}, 
                'target': {'type' : None,'templates' : [],'description' : ''}}
            
            #source
            sensorData=collectSensorSourceTableData(sensorData,dlg.tableWidget_source,row,sensor_id)
            sensorData[int(sensor_id)]['source']['templates']=collectCheckableDropdownTableData(dlg.tableWidget_source,row,sensor_id,2)
            sensorData[int(sensor_id)]['source']['conn_types']=collectCheckableDropdownTableData(dlg.tableWidget_source,row,sensor_id,3)
            sensorData[int(sensor_id)]['source']['conns']=collectCheckableDropdownTableData(dlg.tableWidget_source,row,sensor_id,4)   
            #target
            sensorData=collectSensorTargetTableData(sensorData,dlg.tableWidget_target,row,sensor_id)
            sensorData[int(sensor_id)]['target']['templates']=collectCheckableDropdownTableData(dlg.tableWidget_target,row,sensor_id,2)
    #print('--')
    sql=""
    #deleted
    #print(loadedSensorData)
    #print(sensorData)
    for key_loaded in loadedSensorData:
        if key_loaded not in sensorData: 
            print('removed sensor')
            sql+="""DELETE FROM sensors WHERE id={};""".format(key_loaded) # nosec B608
    
    #added
    for row,key_table in enumerate(sensorData):
        if key_table not in loadedSensorData: 
            print('added sensor:'+str(key_table))
            sql+="""INSERT INTO sensors (id) VALUES({});\n""".format(key_table) # nosec B608

            #source
            sql+="""INSERT INTO sensor_source(sensor_id,type,template,measure,function,conn_type,conns,test_value,description) VALUES ({},{},{},{},{},{},{},{},'{}');\n""".format(# nosec B608
                key_table,sensorData[key_table]['source']['type'],key_table,sensorData[key_table]['source']['measure'],sensorData[key_table]['source']['function'],key_table,key_table,sensorData[key_table]['source']['test_value'],sensorData[key_table]['source']['description']) # nosec B608
            for i,(key_template,value_template) in enumerate(sensorData[key_table]['source']['templates'].items(),1):  
                sql+="""INSERT INTO source_template(source_id,template,active) VALUES ({},{},{});\n""".format(key_table,key_template,value_template)  # nosec B608               
            sql+="".join(["""INSERT INTO source_conn_type(source_id,conn_type,active) VALUES ({},{},{});\n""".format(key_table,key_conn_types,value_conn_types) for key_conn_types,value_conn_types in sensorData[key_table]['source']['conn_types'].items()])   # nosec B608               
            sql+="".join(["""INSERT INTO source_conns(source_id,connection_id,active) VALUES ({},{},{});\n""".format(key_table,key_conns,value_conns) for key_conns,value_conns in sensorData[key_table]['source']['conns'].items()])   # nosec B608               
            
            #target
            sql+="""INSERT INTO sensor_target(sensor_id,type,template,description,test_value) VALUES ({},{},{},'{}',{});\n""".format(# nosec B608
                key_table,sensorData[key_table]['target']['type'],key_table,sensorData[key_table]['target']['description'],sensorData[key_table]['source']['test_value']) # nosec B608
            for i,(key_template,value_template) in enumerate(sensorData[key_table]['target']['templates'].items(),1):  
                sql+="""INSERT INTO target_template(target_id,template,active) VALUES ({},{},{});\n""".format(key_table,key_template,value_template)       # nosec B608          
        else:   
            for table in {'source','target'}:                            
                #added template of existing sensors
                for i,(key,value) in enumerate(sensorData[key_table][table]['templates'].items(),1):
                    if key not in loadedSensorData[key_table][table]['templates']:
                        sql+="""INSERT INTO {}_template({}_id,template,active) VALUES ({},{},{});\n""".format(table,table,key_table,key,value) # nosec B608
                    else:
                        #print(key)
                        #print(loadedSensorData[key_table][table]['templates'])
                        if value!=loadedSensorData[key_table][table]['templates'][key]:
                            sql+="""UPDATE {}_template SET active = {} WHERE {}_id = {} AND template = {};\n""".format(table,value,table,key_table,key) # nosec B608

                #deleted template of existing sensors
                for key in loadedSensorData[key_table][table]['templates']:
                    if key not in sensorData[key_table][table]['templates']:
                        sql+="""DELETE FROM {}_template WHERE {}_id = {} AND template = {};\n""".format(table,table,key_table, key) # nosec B608
                        
                #description
                if loadedSensorData[key_table][table]['description']!=sensorData[key_table][table]['description']:
                    sql+="""UPDATE sensor_{} SET description = '{}' WHERE sensor_id = {} ;\n""".format(table,sensorData[key_table][table]['description'],key_table) # nosec B608

                #type
                if loadedSensorData[key_table][table]['type']!=sensorData[key_table][table]['type']:
                    sql+="""UPDATE sensor_{} SET type = {} WHERE sensor_id = {} ;\n""".format(table,sensorData[key_table][table]['type'],key_table) # nosec B608

            #test value
            if loadedSensorData[key_table]['source']['test_value']!=sensorData[key_table]['source']['test_value']:
                sql+="""UPDATE sensor_source SET test_value = '{}' WHERE sensor_id = {} ;\n""".format(sensorData[key_table]['source']['test_value'],key_table)  # nosec B608       

            #measure
            if loadedSensorData[key_table]['source']['measure']!=sensorData[key_table]['source']['measure']:
                sql+="""UPDATE sensor_source SET measure = '{}' WHERE sensor_id = {} ;\n""".format(sensorData[key_table]['source']['measure'],key_table)    # nosec B608    

            #function
            if loadedSensorData[key_table]['source']['function']!=sensorData[key_table]['source']['function']:
                sql+="""UPDATE sensor_source SET function = '{}' WHERE sensor_id = {} ;\n""".format(sensorData[key_table]['source']['function'],key_table)    # nosec B608     
                        
            #added conn_types of existing sensors
            for key,value in sensorData[key_table]['source']['conn_types'].items():
                if key not in loadedSensorData[key_table]['source']['conn_types']:
                    sql+="""INSERT INTO source_conn_type(source_id,conn_type,active) VALUES ({},{},{});\n""".format(key_table,key,value) # nosec B608
                else:
                    if value!=loadedSensorData[key_table]['source']['conn_types'][key]:
                        sql+="""UPDATE source_conn_type SET active = {} WHERE source_id = {} AND conn_type = {};\n""".format(value,key_table,key) # nosec B608

            #deleted conn_types of existing sensors
            for key in loadedSensorData[key_table]['source']['conn_types']:
                if key not in sensorData[key_table]['source']['conn_types']:
                    sql+="""DELETE FROM source_conn_type WHERE source_id = {} AND conn_type = {};\n""".format(key_table,key) # nosec B608

            #added conns of existing sensors
            for key,value in sensorData[key_table]['source']['conns'].items():
                if key not in loadedSensorData[key_table]['source']['conns']:
                    sql+="""INSERT INTO source_conns(source_id,connection_id,active) VALUES ({},{},{});\n""".format(key_table,key,value) # nosec B608
                else:
                    if value!=loadedSensorData[key_table]['source']['conns'][key]:
                        sql+="""UPDATE source_conns SET active = {} WHERE source_id = {} AND connection_id = {};\n""".format(value,key_table,key) # nosec B608

            #deleted conns of existing sensors
            for key in loadedSensorData[key_table]['source']['conns']:
                if key not in sensorData[key_table]['source']['conns']:
                    sql+="""DELETE FROM source_conns WHERE source_id = {} AND connection_id = {};\n""".format(key_table,key) # nosec B608
    
    #print(sql)
    if sql:
        cur.execute(sql)
            
class WorkerSensors(QRunnable):      
    """Worker thread
    Inherits from QRunnable to handle worker thread setup, signals and wrap-up."""
    def __init__(self,*args,**kwargs):
        super().__init__()
        self.args=args
        #print(args)
        self.signals=APISignals()
        self.config=kwargs['config']
        self.dlg=kwargs['dlg']
        self.loadedSensorData=kwargs['loadedSensorData']
        self.sensorData=kwargs['sensorData']
        self.dlg.process_running=True
        self.conn=""
        self.cur=""
        self.plugin_dir=kwargs['plugin_dir']
        self.conn = dbConnect(self.config,True)
        if self.conn:
            self.cur=self.conn.cursor(cursor_factory = psycopg2.extras.RealDictCursor)
            
    @pyqtSlot()
    def run(self):
        #print('run worker update sensors')
        try:
            self.progress_value=1
            self.signals.progress.emit(self.progress_value)
            writeSensorsToDB(self.cur,self.config,dlg=self.dlg,sensorData=self.sensorData,loadedSensorData=self.loadedSensorData)
            self.signals.progress.emit(50)  
            self.processingSensorSignals()
            self.signals.progress.emit(100)  
            self.signals.finished.emit('Sensor signals successfully updated!')  
        except Exception as e:
            self.signals.progress.emit(0)
            self.signals.error.emit(str(e))  
            
        
    def processingSensorSignals(self):
        """Check sensor updates with getSensorData()
            * Loop over effected templates of Customers (1), Energy Plants (2) --> Update sensor targets and sources & sensor_infos
            * Update Supervisory Control (3) if effected"""
        #get sensor data of templates
        add_sensor_source_idsValues=getAddedSensorSourceData(self.cur,self.config,source_types=[1,2],filter=" AND s.measure=5")
        add_sensor_target_idsValues=getAddedSensorTargetData(self.cur,self.config,target_types=[1,2],filter="")
        remove_sensor_source_ids=getRemovedSensorSourceData(self.cur,self.config,source_types=[1,2],filter=" AND s.measure=5")
        remove_sensor_target_ids=getRemovedSensorTargetData(self.cur,self.config,target_types=[1,2],filter="")

        #print('-+sensor data+-')
        #print(add_sensor_source_idsValues)
        #print(add_sensor_target_idsValues)
        #print(remove_sensor_source_ids)
        #print(remove_sensor_target_ids)

        templates={}
        for sensor in add_sensor_source_idsValues:
            #print(sensor)
            #print(getTemplateNameById(sensor['type']))
            template_name=getTemplateName(self.cur,getTemplateNameById(sensor['type']),sensor['template'])
            #print(template_name)
            if sensor['type'] not in templates:
                templates[sensor['type']]={}
            if template_name:
                if template_name[0] in templates[sensor['type']]:
                    templates[sensor['type']][template_name[0]]['source_add'].append(sensor)
                else:
                    templates[sensor['type']][template_name[0]]={'source_add': [sensor], 'target_add':[],'source_remove':[],'target_remove':[]}
        for sensor in add_sensor_target_idsValues:
            template_name=getTemplateName(self.cur,getTemplateNameById(sensor['type']),sensor['template'])
            #print(template_name)
            if sensor['type'] not in templates:
                templates[sensor['type']]={}
            if template_name:
                if template_name[0] in templates[sensor['type']]:
                    templates[sensor['type']][template_name[0]]['target_add'].append(sensor)
                else:
                    templates[sensor['type']][template_name[0]]={'source_add': [], 'target_add':[sensor],'source_remove':[],'target_remove':[]}
        for sensor in remove_sensor_source_ids:
            template_name=getTemplateName(self.cur,getTemplateNameById(sensor['type']),sensor['template'])
            #print(template_name)
            if sensor['type'] not in templates:
                templates[sensor['type']]={}
            if template_name:
                if template_name[0] in templates[sensor['type']]:
                    templates[sensor['type']][template_name[0]]['source_remove'].append(sensor)
                else:
                    templates[sensor['type']][template_name[0]]={'source_add': [], 'target_add': [],'source_remove':[sensor],'target_remove':[]}
        for sensor in remove_sensor_target_ids:
            template_name=getTemplateName(self.cur,getTemplateNameById(sensor['type']),sensor['template'])
            #print(template_name)
            if sensor['type'] not in templates:
                templates[sensor['type']]={}
            if template_name:
                if template_name[0] in templates[sensor['type']]:
                    templates[sensor['type']][template_name[0]]['target_remove'].append(sensor)
                else:
                    templates[sensor['type']][template_name[0]]={'source_add': [], 'target_add': [],'source_remove': [],'target_remove': [sensor]}
                
        #print('++++++++++++++---------+++++/////////')
        #print('--------------add_sensor_source_idsValues------------')
        #print(add_sensor_source_idsValues)
        #print('--------------add_sensor_target_idsValues--------------')
        #print(add_sensor_target_idsValues)
        #print('----------remove_sensor_source_ids------------')
        #print(remove_sensor_source_ids)
        #print('------------remove_sensor_target_ids--------------')
        #print(remove_sensor_target_ids)
        
        for type in templates:
            for at in templates[type]:
                #print('++++++++++++++----templatesensorSignals-----+++++/////////')
                #print(at)
                #print(templates[type][at])
                templatesensorSignals(self.cur,self.config,self.config['pathProjects']+self.config['projectName']+'\\'+getTemplateNameById(type),at,type,templates[type][at]['source_add'],templates[type][at]['target_add'],templates[type][at]['source_remove'],templates[type][at]['target_remove'])
                
        #delete from invoked tables in DB
        if remove_sensor_source_ids:
            sql="""DELETE FROM invoked_sensor_source_signals WHERE sensor_id IN ({});""".format(','.join([str(sensor['sensor_id']) for sensor in remove_sensor_source_ids])) # nosec B608
            #print(sql)
            self.cur.execute(sql)
        if remove_sensor_target_ids:
            sql="""DELETE FROM invoked_sensor_target_signals WHERE sensor_id IN ({});""".format(','.join([str(sensor['sensor_id']) for sensor in remove_sensor_target_ids])) # nosec B608
            #print(sql)
            self.cur.execute(sql)  
        
        #write to invoked table in DB    
        writeInvokedSensorSourceSignals(self.cur,self.config,add_sensor_source_idsValues)
        writeInvokedSensorTargetSignals(self.cur,self.config,add_sensor_target_idsValues)  
        
        Supervisory_control(self.plugin_dir,self.config,update_sensors=True)
     
 