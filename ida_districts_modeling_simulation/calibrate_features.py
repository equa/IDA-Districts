from plugins.utility_functions.files import *
from plugins.utility_functions.db import *
from plugins.utility_functions.dialog import *
from .invoke import *
from qgis.utils import iface

def openResult(dlg,plugin_dir,conn,cur):
    """ Open the selected result"""
    print('Open result')
    print(dlg.list_tableWidgetResults[dlg.tabwidget.currentIndex()])
    idx=dlg.list_tableWidgetResults[dlg.tabwidget.currentIndex()].currentRow()
    print(idx)
    if idx!=-1:
        if conn:
            cur=conn.cursor(cursor_factory = psycopg2.extras.RealDictCursor) 
            
            id=dlg.list_tableWidgetResults[dlg.tabwidget.currentIndex()].item(idx,0).text()
            parmRun_name=[dlg.tableWidget_customer.cellWidget(idx, 3).currentText() for idx in range(0,dlg.tableWidget_customer.rowCount()) if dlg.tableWidget_customer.item(idx, 0).text()==id][0]
            print(parmRun_name)

            name='Customer_'+id
            dir=plugin_dir.replace('/','\\')+"\\network_models\\{}\\{}\\invoked_customers\\".format(dictDB['projectName'],dictDB['versionName'])
            file=dir+"{}.idm".format(name)
            
            # Open the building with the IDA ICE Python API
            print('**********************************')
            print(file)
            process = Process(target=WorkerOpenParRunAPI(file,plugin_dir,parmRun_name))
            
            print('finished open assettype')
    else:
        iface.messageBar().pushMessage("Info", "No item selected!", level=Qgis.Info)
            
def openTemplate(dlg,plugin_dir,conn):
    """ Open the selected template"""
    print('Open template')
    print(dlg.tableWidget_templates)
    row_index=dlg.tableWidget_templates.currentRow()
    print(row_index)
    if row_index!=-1:
        if conn:
            cur=conn.cursor(cursor_factory = psycopg2.extras.RealDictCursor) 
            assettype=dlg.tableWidget_templates.item(row_index, 0).text()
            sql="""SELECT id AS assetgroup_id FROM customer_assetgroups WHERE assetgroup='{}';""".format(dlg.tableWidget_templates.item(row_index, 2).text())
            cur.execute(sql)
            assetgroup=cur.fetchone()['assetgroup_id']
            assettype_name=dlg.tableWidget_templates.item(row_index, 1).text()
            parmRun_name=dlg.tableWidget_templates.cellWidget(row_index, 3).currentText()

            name=str(assetgroup)+'_'+assettype+'_'+assettype_name
            dir=getDataCenterDir(plugin_dir).replace('/','\\')+"\\{}\\customer_assettypes\\".format(dictDB['projectName'])
            file=dir+"{}.idm".format(name)
            
            # Open the building with the IDA ICE Python API
            print('**********************************')
            print(file)
            #process = Process(target=WorkerOpenParRunAPI(file,plugin_dir,parmRun_name))
            openModelCmd(loadIDADistrictsConfig(plugin_dir)['path_ice'],file)
            
            print('finished open assettype')
    else:
        iface.messageBar().pushMessage("Info", "No item selected!", level=Qgis.Info)

def startCallibration(dlg,plugin_dir,conn,dictDB,iface):
    """Start the czustomer calibration. Seperate between calibration with annual energy consumption or load profile. Invoke each customer with ParmRun Macro for Error calculation. 
    Start each selected customer in a loop per API script and write results back to form."""
    print('Start customer calibration')
    print(dlg.tableWidget_customer.selectedIndexes())

    if conn:
        cur=conn.cursor(cursor_factory = psycopg2.extras.RealDictCursor)
        print('invoke')
        parmRuns_cids={}
        for index in dlg.tableWidget_customer.selectedIndexes():
            print(index.row())
            
            idx=index.row()
            parmRun_name=dlg.tableWidget_customer.cellWidget(index.row(), 3).currentText()
            if parmRun_name:   
                try:
                    parmRuns_cids[parmRun_name]=parmRuns_cids[parmRun_name]+[idx]
                except:
                    parmRuns_cids[parmRun_name]=[idx]
        
        print(parmRuns_cids)
        dlg.tabwidget.clear()
        dlg.list_tableWidgetResults=[]
        list_counter=0
        for parmRun_cids in parmRuns_cids:
            #add parm run result tab
            dlg.list_tableWidgetResults.append(QTableWidget(0,1))   
            dlg.list_tableWidgetResults[list_counter].setHorizontalHeaderLabels(["ID"]) 
            dlg.tabwidget.addTab(dlg.list_tableWidgetResults[list_counter], parmRun_cids)
            i=0
            for idx in parmRuns_cids[parmRun_cids]:
                id=dlg.tableWidget_customer.item(idx, 0).text() 
                parmRun_name=dlg.tableWidget_customer.cellWidget(idx, 3).currentText()
                print('++++id:'+id)
                #invoke customer
                invokeOneFeature(dlg,idx,plugin_dir,cur,dictDB,'customer',iface,False,parmRun=True)
                process = Process(target=WorkerRunAutoMooAPI(plugin_dir+'\\network_models\\{}\\{}\\invoked_customers\\Customer_{}.idm'.format(dictDB['projectName'],dictDB['versionName'],id),plugin_dir,parmRun_name))
                
                #get best results
                parmRun_file_data=readFileToList(plugin_dir+'\\network_models\\{}\\{}\\invoked_customers\\Customer_{}\\{}.idm'.format(dictDB['projectName'],dictDB['versionName'],id,parmRun_name))
                bestParmRuns=getBestParmRunsInputs(parmRun_file_data)
                print(bestParmRuns)
                #write best results to Outputs table
                dlg.list_tableWidgetResults[list_counter].insertRow(i)
                columns=['ID']+getParmRunsInputNames(parmRun_file_data)+['']+getParmRunsOutputNames(parmRun_file_data)
                print(columns)
                print(len(columns))
                dlg.list_tableWidgetResults[list_counter].setColumnCount(len(columns)) 
                print(getParmRunsInputNames(parmRun_file_data))                
                print(getParmRunsOutputNames(parmRun_file_data))                
                dlg.list_tableWidgetResults[list_counter].setHorizontalHeaderLabels(columns)
                                                
                item=QTableWidgetItem(id)
                item.setFlags(Qt.ItemIsSelectable | Qt.ItemIsEnabled)
                dlg.list_tableWidgetResults[list_counter].setItem(i,0,item)
        
                input_counter=0
                for input in bestParmRuns[1]:
                    item=QTableWidgetItem(str(input))
                    item.setFlags(Qt.ItemIsSelectable | Qt.ItemIsEnabled)
                    dlg.list_tableWidgetResults[list_counter].setItem(i,1 + input_counter,item)
                    input_counter+=1

                item=QTableWidgetItem('')
                item.setFlags(Qt.ItemIsSelectable | Qt.ItemIsEnabled)
                dlg.list_tableWidgetResults[list_counter].setItem(i,1+input_counter,item)
                
                output_counter=0
                for output in bestParmRuns[0]:
                    dlg.list_tableWidgetResults[list_counter].setItem(i,1+input_counter+1+output_counter,QTableWidgetItem(str(output)))
                    output_counter+=1
                i+=1   
            list_counter+=1
            
def saveCallibValues(dlg,dictDB,conn,plugin_dir):
    """Save the callibration values from dlg table (tableWidget_outputs) to customers layer"""
    if conn:
        cur=conn.cursor(cursor_factory = psycopg2.extras.RealDictCursor)
        layer =QgsProject.instance().mapLayersByName('customers')
        if layer:
            print('save results')
            print(dlg.tabwidget.currentIndex())
            print(dlg.list_tableWidgetResults[dlg.tabwidget.currentIndex()])
            print(dlg.list_tableWidgetResults[dlg.tabwidget.currentIndex()].selectedIndexes())
            
            idxs=[]              
            [idxs.append(idx.row()) for idx in dlg.list_tableWidgetResults[dlg.tabwidget.currentIndex()].selectedIndexes() if idx.row() not in idxs]
            print(idxs)
                    
            if idxs:      
                for idx in idxs:
                    id=dlg.list_tableWidgetResults[dlg.tabwidget.currentIndex()].item(idx,0).text()
                    print(id)
                    
                    parmRun_name=[dlg.tableWidget_customer.cellWidget(idx, 3).currentText() for idx in range(0,dlg.tableWidget_customer.rowCount()) if dlg.tableWidget_customer.item(idx, 0).text()==id][0]
                    print(parmRun_name)

                    file_data=readFileToList(plugin_dir+'\\network_models\\{}\\{}\\invoked_customers\\Customer_{}\\{}.idm'.format(dictDB['projectName'],dictDB['versionName'],id,parmRun_name))
                    names_target=getParmRunsInputNamesTargets(file_data)
                    print(names_target)             
                    names_target.update(getParmRunsOutputNamesTargets(file_data))
                    print(names_target)

                    layer_fields= [str(i.name()) for i in layer[0].fields()]
                    unique_field_names={}
                    cur.execute("""SELECT * FROM "{}".customer_model_parms WHERE mapping_direction IN ('<--','<-->');""".format(dictDB['versionName']))
                    
                    for parm in cur.fetchall():
                        #print(parm)
                        field_name=[i for i in re.findall(r'[^|]+', parm['mapping_expression']) if i in layer_fields]
                        #print(field_name)
                        if len(field_name)==1 and field_name[0] not in unique_field_names:
                            unique_field_names[field_name[0]]=[parm['model_name'], parm['parm_name']]
                    print(unique_field_names)

                    labels=[]
                    for c in range(dlg.list_tableWidgetResults[dlg.tabwidget.currentIndex()].columnCount()):
                        it = dlg.list_tableWidgetResults[dlg.tabwidget.currentIndex()].horizontalHeaderItem(c)
                        labels.append(str(c+1) if it is None else it.text())

                    print(labels)
                
                    print('unique_field_names')
                    for unique_field_name in unique_field_names:
                        for name_target in names_target:
                            if [i.replace('"','') for i in names_target[name_target]]==unique_field_names[unique_field_name]:
                                print('++++++') 
                                print(unique_field_name)
                                print(unique_field_names[unique_field_name])
                                print(name_target)
                            
                                for col in range(0,len(labels)):
                                    if labels[col]==name_target:
                                        value=dlg.list_tableWidgetResults[dlg.tabwidget.currentIndex()].item(idx,col).text()
                                        break
                                print(col)
                                print(value)

                                #update layers
                                sql="""UPDATE "{}".customers SET "{}"={} WHERE id={};\n""".format(dictDB['versionName'],unique_field_name,value,id)
                                print(sql)
                                cur.execute(sql)    

                    #invoke customers with callib values
                    invokeOneFeature(dlg,dlg.list_tableWidgetResults[dlg.tabwidget.currentIndex()].item(idx,0).text(),plugin_dir,cur,dictDB,'customer',iface,False,parmRun=True,saveParmRunResults=True)