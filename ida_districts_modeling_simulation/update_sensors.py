from .ida_districts_modeling_simulation_dialog import SensorSignalsDialog
from plugins.utility_functions.sensor_signals import *
from plugins.utility_functions.db import *
from .supervisory_control import Supervisory_control
        
class UpdateSensors():
    def __init__(self,*args, **kwargs):
        self.dictDB=kwargs['dictDB']
        self.cur=kwargs['cur']
        self.plugin_dir=kwargs['plugin_dir']
        
        self.dlg=SensorSignalsDialog(self.dictDB,self.plugin_dir)
        self.dlg.btn_ok.clicked.connect(self.btn_ok_sensonorSignals)
        self.dlg.btn_cancel.clicked.connect(lambda: closeDialog(self.dlg))
        self.dlg.btn_add.clicked.connect(self.addSensor)
        self.dlg.btn_del.clicked.connect(self.delSensor)
        self.dlg.tableWidget_source.currentCellChanged.connect(self.dlg.tableWidget_target.selectRow)
        self.dlg.tableWidget_target.currentCellChanged.connect(self.dlg.tableWidget_source.selectRow)
        self.loadSensorTableValues()
        self.dlg.show()  

    def writeSensorsToDB(self):
        """Write sensor data to the DB"""
        print('Save table to DB an close dialog')
        sql="""TRUNCATE {}.sensors, {}.sensor_source,{}.source_assetgroups, {}.source_assettype, {}.source_ids, {}.source_conn_type, {}.source_conns,
        {}.sensor_target,{}.target_assetgroups, {}.target_assettype, {}.target_ids
        CASCADE;""".format(
            self.dictDB['versionName'],self.dictDB['versionName'],self.dictDB['versionName'], self.dictDB['versionName'],self.dictDB['versionName'],self.dictDB['versionName'],self.dictDB['versionName'],self.dictDB['versionName'],self.dictDB['versionName'],self.dictDB['versionName'],self.dictDB['versionName'])
        print(sql)
        self.cur.execute(sql)
        dropDown=self.dlg.tableWidget_source.cellWidget(0, 2)

        for row in range(self.dlg.tableWidget_source.rowCount()):
            sensor_id=self.dlg.tableWidget_source.item(row,0).text()
            self.insertIntoSensorsTable(self.dlg.tableWidget_source,row,sensor_id)
            
            #source
            self.insertIntoSensorSourceTable(self.dlg.tableWidget_source,row,sensor_id)
            self.insertIntoSensorAssetgroupsTable(self.dlg.tableWidget_source,row,sensor_id,'source')
            self.insertIntoSensorAssettypesTable(self.dlg.tableWidget_source,row,sensor_id,'source')
            self.insertIntoSensorIdsTable(self.dlg.tableWidget_source,row,sensor_id,'source')
            self.insertIntoSensorSourceConntypesTable(self.dlg.tableWidget_source,row,sensor_id)
            self.insertIntoSensorSourceConnsTable(self.dlg.tableWidget_source,row,sensor_id)
            
            #target
            self.insertIntoSensorTargetTable(self.dlg.tableWidget_target,row,sensor_id)
            self.insertIntoSensorAssetgroupsTable(self.dlg.tableWidget_target,row,sensor_id,'target')
            self.insertIntoSensorAssettypesTable(self.dlg.tableWidget_target,row,sensor_id,'target')
            self.insertIntoSensorIdsTable(self.dlg.tableWidget_target,row,sensor_id,'target')

        closeDialog(self.dlg)

    def insertIntoSensorsTable(self,table,row,sensor_id):
        sql="""INSERT INTO {}.sensors(id) VALUES ({});""".format(self.dictDB['versionName'],sensor_id)
        print(sql)
        self.cur.execute(sql)
        
    def insertIntoSensorSourceTable(self,table,row,sensor_id):
        if table.cellWidget(row, 8).currentIndex()==-1:
            function=1
        else:
            function=table.cellWidget(row, 8).currentIndex()+1
        if table.cellWidget(row, 1).currentIndex()==3:
            measure=table.cellWidget(row, 7).currentIndex()+5
            function+=4
        else:
            measure=table.cellWidget(row, 7).currentIndex()+1
        if table.cellWidget(row, 8).currentText()=='Individual signals for each target':
            function=6
        sql="""INSERT INTO {}.sensor_source(sensor_id,type,assetgroup,assettype,measure,function,conn_type,conns,ids,test_value,description) VALUES ({},{},{},{},{},{},{},{},{},{},'{}');""".format(
            self.dictDB['versionName'],sensor_id,table.cellWidget(row, 1).currentText().split(':')[0],sensor_id,sensor_id,measure,function,sensor_id,sensor_id,sensor_id,table.item(row,9).text(),table.item(row,10).text())
        print(sql)
        self.cur.execute(sql)

    def insertIntoSensorTargetTable(self,table,row,sensor_id):
        sql="""INSERT INTO {}.sensor_target(sensor_id,type,assetgroup,assettype,target,description) VALUES ({},{},{},{},{},'{}');""".format(
            self.dictDB['versionName'],sensor_id,table.cellWidget(row, 1).currentText().split(':')[0],sensor_id,sensor_id,table.cellWidget(row, 5).currentIndex()+1,table.item(row,6).text())
        print(sql)
        self.cur.execute(sql)
        
    def insertIntoSensorAssetgroupsTable(self,table,row,sensor_id,sensor):
        dropDown=table.cellWidget(row, 2)
        if dropDown!=None:
            for i in range(dropDown.count()):
                if dropDown.itemText(i) != 'Check all items':        
                    sql="""INSERT INTO "{}".{}_assetgroups({}_id,assetgroup,active) VALUES ({},{},{});""".format(
                        self.dictDB['versionName'],sensor,sensor,sensor_id,dropDown.itemText(i).split(':')[0],dropDown.itemChecked(i))
                    print(sql)
                    self.cur.execute(sql)
        
    def insertIntoSensorAssettypesTable(self,table,row,sensor_id,sensor):
        dropDown=table.cellWidget(row, 3)
        if dropDown!=None:
            for i in range(dropDown.count()):
                if dropDown.itemText(i) != 'Check all items': 
                    assetgroup=dropDown.itemText(i).split('(')[1][:-1]
                    type=table.cellWidget(row, 1).currentText()
                    print(type)
                    sql="""SELECT id AS assetgroup FROM public.{}_assetgroups WHERE assetgroup='{}';""".format(type.split(':')[1].replace(' ','_'),assetgroup)
                    print(sql)
                    self.cur.execute(sql)
                    assetgroup_id=self.cur.fetchone()['assetgroup']
                    print(assetgroup_id)                
                    sql="""INSERT INTO "{}".{}_assettype({}_id,assetgroup,assettype,active) VALUES ({},{},{},{});""".format(
                    self.dictDB['versionName'],sensor,sensor,sensor_id,assetgroup_id,dropDown.itemText(i).split(':')[0],dropDown.itemChecked(i))
                    print(sql)
                    self.cur.execute(sql)
                    
    def insertIntoSensorIdsTable(self,table,row,sensor_id,sensor):
        dropDown=table.cellWidget(row, 4)
        if dropDown!=None:
            for i in range(dropDown.count()):
                if dropDown.itemText(i) != 'Check all items':  
                    sql="""INSERT INTO "{}".{}_ids({}_id,feature_id,active) VALUES ({},{},{});""".format(
                        self.dictDB['versionName'],sensor,sensor,sensor_id,dropDown.itemText(i).split('(')[0],dropDown.itemChecked(i))
                    print(sql)
                    self.cur.execute(sql)
                    
    def insertIntoSensorSourceConntypesTable(self,table,row,sensor_id):
        dropDown=table.cellWidget(row, 5)
        if dropDown!=None:
            for i in range(dropDown.count()):
                if dropDown.itemText(i) != 'Check all items':  
                    sql="""INSERT INTO "{}".source_conn_type(source_id,conn_type,active) VALUES ({},{},{});""".format(
                        self.dictDB['versionName'],sensor_id,dropDown.itemText(i).split(':')[0],dropDown.itemChecked(i))
                    print(sql)
                    self.cur.execute(sql)    
                    
    def insertIntoSensorSourceConnsTable(self,table,row,sensor_id):
        dropDown=table.cellWidget(row, 6)
        if dropDown!=None:
            for i in range(dropDown.count()):
                if dropDown.itemText(i) != 'Check all items':  
                    sql="""INSERT INTO {}.source_conns(source_id,connection_id,active) VALUES ({},{},{});""".format(
                        self.dictDB['versionName'],sensor_id,dropDown.itemText(i).split(':')[0],dropDown.itemChecked(i))
                    print(sql)
                    self.cur.execute(sql)
       
    def addSensor(self):
        """INSERT a sensor to the source and target table"""
        rowPosition = self.dlg.tableWidget_source.rowCount()
        print('&&&&&&&&&&&&&&&&&&&&&&&&&')
        print(rowPosition)
        maxId=getMaxTableId(self.dlg.tableWidget_source)
        
        #source table
        self.dlg.tableWidget_source.insertRow(rowPosition)
        self.dlg.tableWidget_source.setItem(rowPosition,0,QTableWidgetItem(str(maxId+1)))
        for i in range(2,7):
            self.setCheckableDropDownItemsTable(self.dlg.tableWidget_source,[],rowPosition,i,[])
        self.setTableDropDown(self.dlg.tableWidget_source,getFilteredDropDownItemNames(self.cur,[[1,'public','measure','measure',[1,2,3,4,6]]]),'1',7,rowPosition,self.measureChanged)
        self.setTableDropDown(self.dlg.tableWidget_source,getDropDownItemNames(self.cur,[[1,'public','signal_function','function']]),'1',8,rowPosition,False)
        self.dlg.tableWidget_source.setItem(rowPosition,9,QTableWidgetItem('1'))
        self.dlg.tableWidget_source.setItem(rowPosition,10,QTableWidgetItem(''))
        self.setTableDropDown(self.dlg.tableWidget_source,getDropDownItems(self.cur,[[1,'public','type','id','name']]),'1:Customer',1,rowPosition,self.sourceTypeChanged) #dropdown type
        self.sourceTypeChanged(self.dlg.tableWidget_source,'',1,rowPosition)
        self.dlg.tableWidget_source.selectRow(rowPosition)       
        
        #target table
        self.dlg.tableWidget_target.insertRow(rowPosition)
        self.dlg.tableWidget_target.setItem(rowPosition,0,QTableWidgetItem(str(maxId+1)))
        for i in range(2,5):
            self.setCheckableDropDownItemsTable(self.dlg.tableWidget_target,[],rowPosition,i,[])
        self.setTableDropDown(self.dlg.tableWidget_target,getDropDownItems(self.cur,[[1,'public','type','id','name']]),'4:Supervisory control',1,rowPosition,self.targetTypeChanged) #dropdown type
        self.setTableDropDown(self.dlg.tableWidget_target,getFilteredDropDownItemNames(self.cur,[[1,'public','target','target',[1]]]),'1',5,rowPosition,False)
        self.dlg.tableWidget_target.setItem(rowPosition,6,QTableWidgetItem(''))
        self.targetTypeChanged(self.dlg.tableWidget_target,'',1,rowPosition)
        self.dlg.tableWidget_target.selectRow(rowPosition)

    def delSensor(self):
        """Delete a sensor from a table"""
        row_index=self.dlg.tableWidget_source.currentRow()
        print (row_index)
        if row_index!=-1:
            self.dlg.tableWidget_source.removeRow(row_index)
            self.dlg.tableWidget_target.removeRow(row_index)
        else:
            self.iface.messageBar().pushMessage("Info", "No item selected!", level=Qgis.Info)
        
    def loadSensorTableValues(self):
        """Load the sensor table values """
        sql="""SELECT s_s.sensor_id, s_s.type AS source_type, type.name AS source_type_name, s_s.assetgroup AS source_assetgroup, s_s.assettype AS source, m.measure, f.function, s_s.test_value, s_s.description AS description_source, s_t.type AS target_type
    FROM {}.sensor_source s_s, public.type, public.measure m, public.signal_function f, {}.sensor_target s_t
    WHERE s_s.type=type.id AND s_s.measure=m.id AND s_s.function=f.id AND s_t.sensor_id=s_s.sensor_id
    ORDER BY s_s.sensor_id;""".format(self.dictDB['versionName'],self.dictDB['versionName'])
        i=0
        self.cur.execute(sql)
        for sensor_data in self.cur.fetchall():
            self.dlg.tableWidget_source.insertRow(i)
            self.dlg.tableWidget_source.setItem(i,0,QTableWidgetItem(str(sensor_data['sensor_id'])))
            self.setTableDropDown(self.dlg.tableWidget_source,getDropDownItems(self.cur,[[1,'public','type','id','name']]),str(sensor_data['source_type'])+':'+sensor_data['source_type_name'],1,i,self.sourceTypeChanged) #dropdown type
            if sensor_data['source_type']==4:
                self.setTableDropDown(self.dlg.tableWidget_source,getFilteredDropDownItemNames(self.cur,[[1,'public','measure','measure',[5]]]),sensor_data['measure'],7,i,self.measureChanged)
                self.setTableDropDown(self.dlg.tableWidget_source,getFilteredDropDownItemNames(self.cur,[[1,'public','signal_function','function',[5,6]]]),sensor_data['function'],8,i,False)
                for col in range(2,7):
                    self.setCheckableDropDownItemsTable(self.dlg.tableWidget_source,[],i,col,[]) 
            else:
                self.setTableDropDown(self.dlg.tableWidget_source,getFilteredDropDownItemNames(self.cur,[[1,'public','measure','measure',[1,2,3,4,5]]]),sensor_data['measure'],7,i,self.measureChanged)
                self.setFilteredAssetgroupDropdownItems(self.dlg.tableWidget_source,sensor_data['source_type_name'].replace(' ','_'),sensor_data['sensor_id'],i,'source')
                self.setFilteredAssettypeDropdownItems(self.dlg.tableWidget_source,sensor_data['source_type_name'].replace(' ','_'),sensor_data['sensor_id'],i,'source')
                self.setFilteredIdsDropdownItems(self.dlg.tableWidget_source,sensor_data['source_type_name'].replace(' ','_'),sensor_data['sensor_id'],i,'source')
                self.setFilteredConnTypesDropdownItems(sensor_data['source_type_name'].replace(' ','_'),sensor_data['sensor_id'],i)
                self.setFilteredConnsDropdownItems(sensor_data['source_type_name'].replace(' ','_'),sensor_data['sensor_id'],i)
                if sensor_data['source_type']==4 or sensor_data['target_type']==4: #source type==supervisory control or target type==supervisory control
                    if sensor_data['source_type']==4: #source type==supervisory control
                        self.setTableDropDown(self.dlg.tableWidget_source,getFilteredDropDownItemNames(self.cur,[[1,'public','signal_function','function',[5,6]]]),sensor_data['function'],8,i,False)
                    else:
                        self.setTableDropDown(self.dlg.tableWidget_source,getFilteredDropDownItemNames(self.cur,[[1,'public','signal_function','function',[1,2,3,4,6]]]),sensor_data['function'],8,i,False)
                else:
                    self.setTableDropDown(self.dlg.tableWidget_source,getFilteredDropDownItemNames(self.cur,[[1,'public','signal_function','function',[1,2,3,4]]]),sensor_data['function'],8,i,False)
            self.dlg.tableWidget_source.setItem(i,9,QTableWidgetItem(str(sensor_data['test_value'])))
            self.dlg.tableWidget_source.setItem(i,10,QTableWidgetItem(sensor_data['description_source']))
            i+=1            
        
        i=0  
        sql="""SELECT s_t.sensor_id, s_t.type AS target_type, type.name AS target_type_name, s_t.assetgroup, s_t.assettype, t.target AS target_name, s_t.description AS description_target
    FROM {}.sensor_target s_t, public.type, public.target t
    WHERE s_t.type=type.id AND t.id=s_t.target
    ORDER BY s_t.sensor_id;""".format(self.dictDB['versionName'])
        self.cur.execute(sql)
        for sensor_data in self.cur.fetchall():
            self.dlg.tableWidget_target.insertRow(i)
            self.dlg.tableWidget_target.setItem(i,0,QTableWidgetItem(str(sensor_data['sensor_id'])))
            self.setTableDropDown(self.dlg.tableWidget_target,getDropDownItems(self.cur,[[1,'public','type','id','name']]),str(sensor_data['target_type'])+':'+sensor_data['target_type_name'],1,i,self.targetTypeChanged) #dropdown type
            if sensor_data['target_type']==4:
                for col in range(2,5):
                    self.setCheckableDropDownItemsTable(self.dlg.tableWidget_target,[],i,col,[]) 
            else:
                self.setFilteredAssetgroupDropdownItems(self.dlg.tableWidget_target,sensor_data['target_type_name'].replace(' ','_'),sensor_data['sensor_id'],i,'target')
                self.setFilteredAssettypeDropdownItems(self.dlg.tableWidget_target,sensor_data['target_type_name'].replace(' ','_'),sensor_data['sensor_id'],i,'target')
                self.setFilteredIdsDropdownItems(self.dlg.tableWidget_target,sensor_data['target_type_name'].replace(' ','_'),sensor_data['sensor_id'],i,'target')
            if sensor_data['target_type']==1: #Customer
                self.setTableDropDown(self.dlg.tableWidget_target,getFilteredDropDownItemNames(self.cur,[[1,'public','target','target',[1,2]]]),sensor_data['target_name'],5,i,False)
            else:
                self.setTableDropDown(self.dlg.tableWidget_target,getFilteredDropDownItemNames(self.cur,[[1,'public','target','target',[1]]]),sensor_data['target_name'],5,i,False)
            self.dlg.tableWidget_target.setItem(i,6,QTableWidgetItem(sensor_data['description_target']))
            i+=1

    def setTableDropDown(self,table,dropdownItems,currentValue,col,row,signal_function):
        print(dropdownItems)
        print(row)
        print(col)
        comboBox = QComboBox()
        comboBox.addItems(dropdownItems[1])
        comboBox.setCurrentText(currentValue)
        if signal_function:
            comboBox.currentIndexChanged.connect(lambda selected_index, column=col,row=row: signal_function(table,selected_index,column,row))
        table.setCellWidget(row, col, comboBox)   
    
    def measureChanged(self,table,selected_index,column,row): 
        print('************&&&***************')
        type=table.cellWidget(row, 1).currentText().split(':')[1].replace(' ','_')
        target_type=self.dlg.tableWidget_target.cellWidget(row, 1).currentText().split(':')[1].replace(' ','_')
        if table.cellWidget(row,7).currentText() =='Custom':
            print('deactivate conn type')
            self.setCheckableDropDownItemsTable(table,[],row,5,[]) 
            self.setCheckableDropDownItemsTable(table,[],row,6,[]) 
            if type =='Supervisory_control' or target_type=='Supervisory_control':
                if target_type=='Supervisory_control':
                    self.setTableDropDown(table,getFilteredDropDownItemNames(self.cur,[[1,'public','signal_function','function',[1,2,3,4,6]]]),'',8,row,False)
                else:
                    self.setTableDropDown(table,getFilteredDropDownItemNames(self.cur,[[1,'public','signal_function','function',[5,6]]]),'',8,row,False)
            else:
                self.setTableDropDown(table,getFilteredDropDownItemNames(self.cur,[[1,'public','signal_function','function',[1,2,3,4]]]),'',8,row,False)
        else:
            self.setDropDownConntypes(table,5,row,table.cellWidget(row,1).currentText().split(':')[1].replace(' ','_'))
            self.setDropDownConns(table,6,row,table.cellWidget(row,1).currentText().split(':')[1].replace(' ','_'))
            if target_type=='Supervisory_control':
                self.setTableDropDown(table,getFilteredDropDownItemNames(self.cur,[[1,'public','signal_function','function',[1,2,3,4,6]]]),'',8,row,False)
            else:
                self.setTableDropDown(table,getFilteredDropDownItemNames(self.cur,[[1,'public','signal_function','function',[1,2,3,4]]]),'',8,row,False)
        
    def setFilteredConnTypesDropdownItems(self,type,id,row):
        sql="""SELECT c_type.id AS conn_type_id, c_type.description, s_ct.active
    FROM {}.source_conn_type s_ct, {}.source_ids s_id, public.connection_types c_type
    WHERE s_ct.source_id=s_id.source_id AND c_type.id=s_ct.conn_type AND s_id.source_id={}
    GROUP BY c_type.id, c_type.description, s_ct.active
    ORDER BY c_type.id;""".format(self.dictDB['versionName'],self.dictDB['versionName'],id)
        print(sql)
        self.cur.execute(sql)
        source_conn_types=self.cur.fetchall()
        print(source_conn_types)
        comboBoxCheckable = CheckableComboBox()
        comboBoxCheckable.addItem('Check all items')
        comboBoxCheckable.addItems([str(i['conn_type_id'])+':'+i['description'] for i in source_conn_types])
        for i in range(len(source_conn_types)):
            comboBoxCheckable.setItemChecked(i+1,source_conn_types[i]['active'])
        if self.dlg.tableWidget_source.cellWidget(row,7).currentText()!='Power':
            comboBoxCheckable.activated.connect(lambda signal, column=6,row=row: self.setDropDownConns(self.dlg.tableWidget_source,column,row,type))
        self.dlg.tableWidget_source.setCellWidget(row, 5, comboBoxCheckable) 
        
    def setFilteredConnsDropdownItems(self,type,id,row):
        sql="""SELECT conns.id AS conn_id, conns.description, s_conns.active
    FROM {}.source_conns s_conns, public.connections conns
    WHERE s_conns.connection_id=conns.id AND s_conns.source_id={}
    GROUP BY conns.id, conns.description, s_conns.active
    ORDER BY conns.id;""".format(self.dictDB['versionName'],id)
        print(sql)
        self.cur.execute(sql)
        source_conns=self.cur.fetchall()
        print(source_conns)
        comboBoxCheckable = CheckableComboBox()
        comboBoxCheckable.addItem('Check all items')
        comboBoxCheckable.addItems([str(i['conn_id'])+':'+i['description'] for i in source_conns])
        for i in range(len(source_conns)):
            comboBoxCheckable.setItemChecked(i+1,source_conns[i]['active'])
        self.dlg.tableWidget_source.setCellWidget(row, 6, comboBoxCheckable) 
        
        
    def setFilteredAssetgroupDropdownItems(self,table,type,id,row,sensor):
        sql="""SELECT s_ag.assetgroup AS assetgroup, ag.assetgroup AS assetgroup_name, s_ag.active 
        FROM "{}".{}_assetgroups s_ag, public.{}_assetgroups ag 
        WHERE s_ag.{}_id={} AND ag.id=s_ag.assetgroup
        ORDER BY s_ag.assetgroup;""".format(self.dictDB['versionName'],sensor,type,sensor,id)
        print(sql)
        self.cur.execute(sql)
        source_assetgroups=self.cur.fetchall()
        print(source_assetgroups)
        comboBoxCheckable = CheckableComboBox()
        comboBoxCheckable.addItem('Check all items')
        comboBoxCheckable.addItems([str(i['assetgroup'])+':'+i['assetgroup_name'] for i in source_assetgroups])
        for i in range(len(source_assetgroups)):
            comboBoxCheckable.setItemChecked(i+1,source_assetgroups[i]['active'])
        comboBoxCheckable.activated.connect(lambda signal, column=2,row=row: self.setDropDownAssettypes(table,column,row,type))
        table.setCellWidget(row, 2, comboBoxCheckable) 
        
    def getAssetgroupsFromTable(self,dropDown):
        assetgroups=[]
        for i in range(dropDown.count()):
            if dropDown.itemText(i) != 'Check all items' and dropDown.itemChecked(i)==True:
                assetgroups.append(dropDown.itemText(i).split(':')[0])
        return assetgroups
        
    def setDropDownAssettypes(self,table,col,row,type):
        print('set assettypes')
        dropDown=table.cellWidget(row, col)
        if dropDown!=None:
            assetgroups=self.getAssetgroupsFromTable(dropDown)
            if assetgroups:
                sql="""SELECT ag.assetgroup, at.assettype, at.assettype_name
    FROM "{}".{}s f, public.{}_assettypes at, public.{}_assetgroups ag
    WHERE at.assetgroup=f.assetgroup AND at.assettype=f.assettype AND ag.id=f.assetgroup AND f.assetgroup IN ({})
    GROUP BY ag.assetgroup, at.assettype, at.assettype_name
    ORDER BY ag.assetgroup, at.assettype; """.format(self.dictDB['versionName'],type,type,type,','.join(assetgroups))
                print(sql)
                self.cur.execute(sql)
                assettypes=self.cur.fetchall()
                print(assettypes)
                dropdownItems=[str(i['assettype'])+':'+i['assettype_name']+'('+i['assetgroup']+')' for i in assettypes]
                print(dropdownItems)
                self.setCheckableDropDownItemsTable(table,dropdownItems,row,3,[self.setDropDownIds,4,type])
                if not dropdownItems:
                    for i in range(4,7):
                        if table.cellWidget(row, i).__class__.__name__=='CheckableComboBox': 
                            self.setCheckableDropDownItemsTable(table,[],row,i,[]) 
            else:
                for i in range(3,7):
                    if table.cellWidget(row, i).__class__.__name__=='CheckableComboBox': 
                        self.setCheckableDropDownItemsTable(table,[],row,i,[]) 

    def setDropDownAssettypesTarget(self,table,col,row,type):
        print('set assettypes')
        dropDown=table.cellWidget(row, col)
        if dropDown!=None:
            assetgroups=self.getAssetgroupsFromTable(dropDown)
            if assetgroups:
                sql="""SELECT ag.assetgroup, at.assettype, at.assettype_name
    FROM "{}".{}s f, public.{}_assettypes at, public.{}_assetgroups ag
    WHERE at.assetgroup=f.assetgroup AND at.assettype=f.assettype AND ag.id=f.assetgroup AND f.assetgroup IN ({})
    GROUP BY ag.assetgroup, at.assettype, at.assettype_name
    ORDER BY ag.assetgroup, at.assettype; """.format(self.dictDB['versionName'],type,type,type,','.join(assetgroups))
                print(sql)
                self.cur.execute(sql)
                assettypes=self.cur.fetchall()
                print(assettypes)
                dropdownItems=[str(i['assettype'])+':'+i['assettype_name']+'('+i['assetgroup']+')' for i in assettypes]
                print(dropdownItems)
                self.setCheckableDropDownItemsTable(table,dropdownItems,row,3,[self.setDropDownIds,4,type])
                if not dropdownItems:
                    for i in range(4,5):
                        if table.cellWidget(row, i).__class__.__name__=='CheckableComboBox': 
                            self.setCheckableDropDownItemsTable(table,[],row,i,[]) 
            else:
                for i in range(3,5):
                    self.setCheckableDropDownItemsTable(table,[],row,i,[]) 
                        
    def setDropDownIds(self,table,col,row,type):
        print('set ids')
        dropDown=table.cellWidget(row, col-1)

        if dropDown!=None:
            assettypes=[]
            for i in range(dropDown.count()):
                if dropDown.itemChecked(i):
                    assettypes.append(dropDown.itemText(i))
            if assettypes:
                sql="""WITH sub AS(
    SELECT ag.id, at.assettype, at.assettype_name
        FROM "{}".{}s f, public.{}_assettypes at, public.{}_assetgroups ag
        WHERE at.assetgroup=f.assetgroup AND at.assettype=f.assettype AND ag.id=f.assetgroup
            AND at.assettype || ':' || at.assettype_name || '(' || ag.assetgroup ||')' IN ({})
        GROUP BY ag.id, at.assettype, at.assettype_name
)    
SELECT f.id AS f_id,sub.assettype_name FROM "{}".{}s f, sub WHERE f.assetgroup=sub.id AND f.assettype=sub.assettype ORDER BY f.id;""".format(self.dictDB['versionName'],type,type,type,','.join(["'" + i + "'" for i in assettypes]),self.dictDB['versionName'],type)
                print(sql)
                self.cur.execute(sql)
                ids=self.cur.fetchall()
                print(ids)
                dropdownItems=[str(i['f_id'])+'('+i['assettype_name'] + ')' for i in ids]
                print(dropdownItems)
                if table.cellWidget(row, 5).__class__.__name__=='CheckableComboBox': 
                    self.setCheckableDropDownItemsTable(table,dropdownItems,row,4,[self.setDropDownConntypes,5,type])
                else:
                    self.setCheckableDropDownItemsTable(table,dropdownItems,row,4,[])
            else:
                for i in range(4,7):
                    if table.cellWidget(row, i).__class__.__name__=='CheckableComboBox': 
                        self.setCheckableDropDownItemsTable(table,[],row,i,[]) 

    def setDropDownConntypes(self,table,col,row,type):
        print('set conn types')
        dropDown=table.cellWidget(row, col-1)
        #print(str(row) +';'+str(col))
        if dropDown!=None:
            print('+++++++++++++++++++++++')
            ids=[]
            for i in range(dropDown.count()):
                if dropDown.itemChecked(i):
                    ids.append(dropDown.itemText(i).split('(')[0])
            print(ids)
            if ids and table.cellWidget(row, 7).currentText()!='Custom':
                sql="""SELECT conn_t.id AS conn_type_id, conn_t.description
    FROM public.bundle_type_conns b_t_conns, "{}".{}s f, public.{}_assettypes at, public.connection_types conn_t
    WHERE at.conn_bundle_type=b_t_conns.conn_bundle_type_id AND f.assetgroup=at.assetgroup AND f.assettype=at.assettype AND f.id IN ({}) AND conn_t.id=b_t_conns.conn_type_id
    GROUP BY conn_t.id,conn_t.description;""".format(self.dictDB['versionName'],type,type,','.join(ids))
                print(sql)
                self.cur.execute(sql)
                conntypes=self.cur.fetchall()
                print(conntypes)
                dropdownItems=[str(i['conn_type_id']) + ':' + str(i['description']) for i in conntypes]
                print(dropdownItems)
                self.setCheckableDropDownItemsTable(table,dropdownItems,row,5,[self.setDropDownConns,6,type])

            else:
                for i in range(5,7):
                    self.setCheckableDropDownItemsTable(table,[],row,i,[]) 

    def setDropDownConns(self,table,col,row,type):
        print('set conns')
        dropDown=table.cellWidget(row, col-1)
        #print(str(row) +';'+str(col))
        if dropDown!=None:
            print('+++++++++++++++++++++++')
            print(dropDown.itemText(0))
            conn_types=[]
            for i in range(dropDown.count()):
                if dropDown.itemChecked(i):
                    conn_types.append(dropDown.itemText(i).split(':')[0])
            print(conn_types)
            if conn_types:
                sql="""SELECT conns.id AS conn_id, conns.description
    FROM public.connections conns, public.connection_types conn_t, public.connection_type_connections c_t_conns
    WHERE c_t_conns.connection_id=conns.id AND conn_t.id=c_t_conns.connection_type_id AND conn_t.id IN ({}) 
    GROUP BY conns.id, conns.description
    ORDER BY conns.id;""".format(','.join(conn_types))
                print(sql)
                self.cur.execute(sql)
                conns=self.cur.fetchall()
                print(conns)
                dropdownItems=[str(i['conn_id']) + ':' + str(i['description']) for i in conns]
                print(dropdownItems)
                if table.cellWidget(row,7).currentText() in ['Power','Custom']:
                    print('deactivated dropdown conns')
                    self.setCheckableDropDownItemsTable(table,[],row,6,[])
                else:
                    print('activated dropdown conns') 
                    self.setCheckableDropDownItemsTable(table,dropdownItems,row,6,[])
            else:
                for i in range(6,7):
                    self.setCheckableDropDownItemsTable(table,[],row,i,[]) 
                    
    def setFilteredAssettypeDropdownItems(self,table,type,id,row,sensor):
        sql="""SELECT s_at.assetgroup, c_ag.assetgroup AS assetgroup_name,s_at.active, c_at.assettype, c_at.assettype_name
    FROM "{}".{}_assettype s_at, public.{}_assettypes c_at, public.{}_assetgroups c_ag
    WHERE s_at.{}_id={} AND c_at.assetgroup=s_at.assetgroup AND c_at.assettype=s_at.assettype AND c_ag.id=s_at.assetgroup
    ORDER BY s_at.assetgroup, s_at.assettype;""".format(self.dictDB['versionName'],sensor,type,type,sensor,id)
        print(sql)
        self.cur.execute(sql)
        assettypes=self.cur.fetchall()
        print(assettypes)
        comboBoxCheckable = CheckableComboBox()
        comboBoxCheckable.addItem('Check all items')
        comboBoxCheckable.addItems([str(i['assettype'])+':'+i['assettype_name']+'('+i['assetgroup_name']+')' for i in assettypes])
        for i in range(len(assettypes)):
            comboBoxCheckable.setItemChecked(i+1,assettypes[i]['active'])
        comboBoxCheckable.activated.connect(lambda signal, column=4,row=row: self.setDropDownIds(table,column,row,type))
        table.setCellWidget(row, 3, comboBoxCheckable) 

    def setFilteredIdsDropdownItems(self,table,type,id,row,sensor):
        sql="""SELECT s_id.feature_id, s_id.active, at.assettype_name
    FROM "{}".{}_ids s_id, "{}".{}s f, public.{}_assettypes at
    WHERE s_id.{}_id={} AND f.id=s_id.feature_id AND f.assetgroup=at.assetgroup AND f.assettype=at.assettype
    ORDER BY s_id.feature_id;""".format(self.dictDB['versionName'],sensor,self.dictDB['versionName'],type,type,sensor,id)
        print(sql)
        self.cur.execute(sql)
        ids=self.cur.fetchall()
        print(ids)
        comboBoxCheckable = CheckableComboBox()
        comboBoxCheckable.addItem('Check all items')
        comboBoxCheckable.addItems([str(i['feature_id'])+'('+str(i['assettype_name'])+')' for i in ids])
        for i in range(len(ids)):
            comboBoxCheckable.setItemChecked(i+1,ids[i]['active'])
        print('+++++++++********++++++++~~~~~')
        print(type)
        if sensor=='source':
            comboBoxCheckable.activated.connect(lambda signal, column=5,row=row: self.setDropDownConntypes(table,column,row,type))
        table.setCellWidget(row, 4, comboBoxCheckable) 
    
    def setCheckableDropDownItemsTable(self,table,dropdownItems,row,col,signal_args):
        oldDropdown=table.cellWidget(row, col)
        oldTrueItems=[]
        if oldDropdown!=None:
            for i in range(oldDropdown.count()):
                if table.cellWidget(row, col).__class__.__name__=='CheckableComboBox':
                    if oldDropdown.itemChecked(i)==True:
                        oldTrueItems.append(oldDropdown.itemText(i))
        
        comboBoxCheckable = CheckableComboBox()
        comboBoxCheckable.addItem('Check all items')
        comboBoxCheckable.addItems(dropdownItems)
        for i in range(len(dropdownItems)):
            print(i)
            if dropdownItems[i] in oldTrueItems:
                comboBoxCheckable.setItemChecked(i+1,True) 
            else:
                print(row)
                print(col)
                print(dropdownItems)
                comboBoxCheckable.setItemChecked(i+1,False)
        if signal_args:
            comboBoxCheckable.activated.connect(lambda signal, column=signal_args[1],row=row: signal_args[0](table,column,row,signal_args[2]))
        table.setCellWidget(row, col, comboBoxCheckable) 
        
    def sourceTypeChanged(self,table,selected_index,column,row):
        type=table.cellWidget(row, column).currentText().split(':')[1].replace(' ','_')
        if self.dlg.tableWidget_target.cellWidget(row, column):
            target_type=self.dlg.tableWidget_target.cellWidget(row, column).currentText()
            if type==target_type.split(':')[1].replace(' ','_' )and type=='Supervisory_control':
                print('+++source type==target type+++')
                print(getFilteredDropDownItems(self.cur,['type','id','name','id',int(table.cellWidget(row, column).currentText().split(':')[0])%4+1])[0])
                self.setTableDropDown(self.dlg.tableWidget_target,getDropDownItems(self.cur,[[1,'public','type','id','name']]),getFilteredDropDownItems(self.cur,['type','id','name','id',int(table.cellWidget(row, column).currentText().split(':')[0])%4+1])[0],1,row,self.targetTypeChanged)
                self.targetTypeChanged(self.dlg.tableWidget_target,'',1,row)
        else:
            target_type='1:Supervisory_control'
        print('+++++'+target_type+'++++')
        
        if type=='Supervisory_control':
            print('supervisory')
            self.setCheckableDropDownItemsTable(table,[],row,column+1,[])
            for i in range(2,7):
                self.setCheckableDropDownItemsTable(table,[],row,i,[])  
            self.setTableDropDown(table,getFilteredDropDownItemNames(self.cur,[[1,'public','measure','measure',[5]]]),'1',7,row,self.measureChanged)
            self.setTableDropDown(table,getFilteredDropDownItemNames(self.cur,[[1,'public','signal_function','function',[5,6]]]),'1:Customer',8,row,False)
        else:
            sql="""SELECT ag.id AS assetgroup, ag.assetgroup AS assetgroup_name
    FROM "{}".{}s f, public.{}_assetgroups ag
    WHERE ag.id=f.assetgroup
    GROUP BY ag.assetgroup, ag.id
    ORDER BY ag.id;""".format(self.dictDB['versionName'],type,type)
            self.cur.execute(sql)
            assetgroups=self.cur.fetchall()
            dropdownItems=[str(i['assetgroup'])+':'+i['assetgroup_name'] for i in assetgroups]  
            print(dropdownItems)

            self.setCheckableDropDownItemsTable(table,dropdownItems,row,column+1,[self.setDropDownAssettypes,2,type])
            self.setTableDropDown(table,getFilteredDropDownItemNames(self.cur,[[1,'public','measure','measure',[1,2,3,4,5]]]),'1',7,row,self.measureChanged)
            self.setTableDropDown(table,getFilteredDropDownItemNames(self.cur,[[1,'public','signal_function','function',[1,2,3,4,6] if target_type=='4:Supervisory control' else [1,2,3,4]]]),'Min',8,row,False)
            for i in range(3,7):
                self.setCheckableDropDownItemsTable(table,[],row,i,[])  

    def targetTypeChanged(self,table,selected_index,column,row):
        print('target type changed')
        type=table.cellWidget(row, column).currentText().split(':')[1].replace(' ','_')
        if self.dlg.tableWidget_source.cellWidget(row, column):
            source_type=self.dlg.tableWidget_source.cellWidget(row, column).currentText()
            if type==source_type.split(':')[1].replace(' ','_') and type=='Supervisory_control':
                print('+++source type==target type+++')
                print(getFilteredDropDownItems(self.cur,['type','id','name','id',int(table.cellWidget(row, column).currentText().split(':')[0])%4+1])[0])
                self.setTableDropDown(self.dlg.tableWidget_source,getDropDownItems(self.cur,[[1,'public','type','id','name']]),getFilteredDropDownItems(self.cur,['type','id','name','id',int(table.cellWidget(row, column).currentText().split(':')[0])%4+1])[0],1,row,self.sourceTypeChanged)
                self.sourceTypeChanged(self.dlg.tableWidget_source,'',1,row)
        else:
            source_type='1:Customer'
        print('+++++'+source_type+'++++')
        print(type)
        if type=='Supervisory_control':
            print('supervisory')
            self.setCheckableDropDownItemsTable(table,[],row,column+1,[])
            for i in range(2,5):
                self.setCheckableDropDownItemsTable(table,[],row,i,[])  
        else:
            sql="""SELECT ag.id AS assetgroup, ag.assetgroup AS assetgroup_name
    FROM "{}".{}s f, public.{}_assetgroups ag
    WHERE ag.id=f.assetgroup
    GROUP BY ag.assetgroup, ag.id
    ORDER BY ag.id;""".format(self.dictDB['versionName'],type,type)
            self.cur.execute(sql)
            assetgroups=self.cur.fetchall()
            dropdownItems=[str(i['assetgroup'])+':'+i['assetgroup_name'] for i in assetgroups]  
            print(dropdownItems)
            self.setCheckableDropDownItemsTable(table,dropdownItems,row,column+1,[self.setDropDownAssettypesTarget,2,type])
            for i in range(3,5):
                self.setCheckableDropDownItemsTable(table,[],row,i,[])  
        if type=='Customer':
            print('target --> type --> Customer')
            self.setTableDropDown(table,getFilteredDropDownItemNames(self.cur,[[1,'public','target','target',[1,2]]]),'Custom',5,row,False)
        else:
            self.setTableDropDown(table,getFilteredDropDownItemNames(self.cur,[[1,'public','target','target',[1]]]),'Custom',5,row,False)
        self.measureChanged(self.dlg.tableWidget_source,selected_index,column,row)

    def btn_ok_sensonorSignals(self):
        self.writeSensorsToDB()
        self.processingSensonorSignals()
        
    def processingSensonorSignals(self):
        """Check sensor updates with getSensorData()
            * Loop over effected templates of Customers (1), Energy Plants (2), Devices (3) --> Update sensor targets and sources & sensor_infos
            * Update Supervisory Control (4) if effected"""
        #get sensor data of assettypes (type,assetgroup,assettype)
        add_sensor_source_idsValues=getAddedSensorSourceData(self.cur,self.dictDB,source_types=[1,2,3],filter=" AND s.measure=5")
        add_sensor_target_idsValues=getAddedSensorTargetData(self.cur,self.dictDB,target_types=[1,2,3],filter=" AND t.target=1")
        remove_sensor_source_ids=getRemovedSensorSourceData(self.cur,self.dictDB,source_types=[1,2,3],filter=" AND s.measure=5")
        remove_sensor_target_ids=getRemovedSensorTargetData(self.cur,self.dictDB,target_types=[1,2,3],filter=" AND t.target=1")
        print(add_sensor_source_idsValues)
        print(add_sensor_target_idsValues)
        print(remove_sensor_source_ids)
        print(remove_sensor_target_ids)
        
        assettypes={}
        for sensor in add_sensor_source_idsValues:
            for at in sensor['source_assettype_names']:
                if at in assettypes:
                    assettypes[at]['source_add'].append(sensor)
                else:
                    assettypes[at]={'source_add': [sensor], 'target_add':[],'source_remove':[],'target_remove':[]}
        for sensor in add_sensor_target_idsValues:
            for at in sensor['target_assettype_names']:
                if at in assettypes:
                    assettypes[at]['target_add'].append(sensor)
                else:
                    assettypes[at]={'source_add': [], 'target_add':[sensor],'source_remove':[],'target_remove':[]}
        for sensor in remove_sensor_source_ids:
            for at in sensor['source_assettype_names']:
                if at in assettypes:
                    assettypes[at]['source_remove'].append(sensor)
                else:
                    assettypes[at]={'source_add': [], 'target_add': [],'source_remove':[sensor],'target_remove':[]}
        for sensor in remove_sensor_target_ids:
            for at in sensor['target_assettype_names']:
                if at in assettypes:
                    assettypes[at]['target_remove'].append(sensor)
                else:
                    assettypes[at]={'source_add': [], 'target_add': [],'source_remove': [],'target_remove': [sensor]}
                
        print('++++++++++++++---------+++++/////////')
        print('--------------add_sensor_source_idsValues------------')
        print(add_sensor_source_idsValues)
        print('--------------add_sensor_target_idsValues--------------')
        print(add_sensor_target_idsValues)
        print('----------remove_sensor_source_ids------------')
        print(remove_sensor_source_ids)
        print('------------remove_sensor_target_ids--------------')
        print(remove_sensor_target_ids)
        
        for at in assettypes:
            print('++++++++++++++----AssettypeSensorSignals-----+++++/////////')
            print(at)
            print(assettypes[at])
            AssettypeSensorSignals(self.cur,self.dictDB,getDataCenterDir(self.plugin_dir)+'\\'+self.dictDB['projectName']+'\\'+getAssettypeNameById(int(at.split(':')[0])),at,at.split(':')[0],assettypes[at]['source_add'],assettypes[at]['target_add'],assettypes[at]['source_remove'],assettypes[at]['target_remove'])
                
        #delete from invoked tables in DB
        if remove_sensor_source_ids:
            sql="""DELETE FROM {}.invoked_sensor_source_signals WHERE sensor_id IN ({});""".format(self.dictDB['versionName'],','.join([str(sensor['sensor_id']) for sensor in remove_sensor_source_ids]))
            print(sql)
            self.cur.execute(sql)
        if remove_sensor_target_ids:
            sql="""DELETE FROM {}.invoked_sensor_target_signals WHERE sensor_id IN ({});""".format(self.dictDB['versionName'],','.join([str(sensor['sensor_id']) for sensor in remove_sensor_target_ids]))
            print(sql)
            self.cur.execute(sql)  
        
        #write to invoked table in DB    
        writeInvokedSensorSourceSignals(self.cur,self.dictDB,add_sensor_source_idsValues)
        writeInvokedSensorTargetSignals(self.cur,self.dictDB,add_sensor_target_idsValues)  
        
        Supervisory_control(getModellingDir(self.plugin_dir),update_sensors=True)