from qgis.PyQt.QtCore import QThreadPool

from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT
from qgis.PyQt.QtWidgets import QTableWidgetItem,QWidget,QPushButton,QCheckBox,QComboBox
from qgis.PyQt.QtCore import Qt
from qgis.core import Qgis, QgsMessageLog

from .utility_functions.invoke import *
from .utility_functions.files import *
from .utility_functions.workers import *
from .utility_functions.dialog import *
from .utility_functions.compat import *

import psycopg2
import psycopg2.extras
import os
import traceback
import re

def getCustomerModelParameter(sim_model_id):
    if sim_model_id==1:
        return []
    elif sim_model_id==2:
        return ["FloorArea","U","tau","MHs","PhiRadH_nom","SolarAperture","WinIntShading","ela","ACH","TSetH","TBalance","PBand","N_value","KV_max","KV_small","dPNom"]    
    elif sim_model_id==3:
        return ["FloorArea","U","tau","MHs","PhiRadH_nom","SolarAperture","WinIntShading","ela","ACH","TSetH","TBalance","PBand","N_value","KV_max","KV_small","dPNom","TSetC","PhiRadC_nom"]
    elif sim_model_id==4:
        return ["FloorArea","U","tau","MHs","PhiRadH_nom","SolarAperture","WinIntShading","ela","ACH","TSetH","TBalance","PBand","N_value","KV_max","KV_small","dPNom","TSetC","PhiRadC_nom","N_value_C","MCoolDev"]
    elif sim_model_id==5:
        return ["FloorArea","U","tau","MHs","PhiRadH_nom","SolarAperture","WinIntShading","ela","ACH","TSetH","TBalance","PBand","N_value","KV_max","KV_small","dPNom","TSetC","PhiRadC_nom","N_value_C","MCoolDev","hx_eff","TSetDhw","TSupNomH","TSupNomC","TimeConst"]
    elif sim_model_id==6:
        return ["FloorArea","U","tau","MHs","PhiRadH_nom","SolarAperture","WinIntShading","ela","ACH","TSetH","TBalance","PBand","N_value","KV_max","KV_small","dPNom","TSetC","PhiRadC_nom","N_value_C","MCoolDev","hx_eff","TSetDhw","TSupNomH","TSupNomC","TimeConst","mNomTank","mNomDhw","mTank"]      
    elif sim_model_id==7:
        return ["FloorArea","U","tau","MHs","PhiRadH_nom","SolarAperture","WinIntShading","ela","ACH","TSetH","TBalance","PBand","N_value","KV_max","KV_small","dPNom","TSupNomH"]      
    elif sim_model_id==8:
        return ["FloorArea","U","tau","MHs","PhiRadH_nom","SolarAperture","ela","ACH","TSetH","TBalance","PBand","N_value","KV_max","KV_small","dPNom","TSupNomH","TSupNomH","TSetC","PhiRadC_nom","TSupNomC"]      
     
def getParmRuns(template_name,config,file=None):
    """screen parm runs id the directory"""
    new_parametric_runs=False
    if not file:
        file = config['pathProjects']+config['projectName']+"\\customer_templates\\"+template_name+".idm"
        new_parametric_runs=True
    data=readFileToList(file)
    parmRuns=[line.split(':N "')[1].split('" :T')[0] for line in data if ":T PARMRUN-INFO" in line]    
    if new_parametric_runs:
        parmRuns.append(tr('@default','new_parametric_run'))
    return parmRuns
    
def updateParmruns(dlg,result):
    match = re.search(r'-r\s+"([^"]+)"', result)

    if match:
        file = match.group(1)
        if os.path.exists(file):
            file_name = '_'.join(os.path.splitext(os.path.basename(file))[0].split('_')[1:])
            parmRuns=getParmRuns("","",file)
            for row in range(0,dlg.tableWidget_customer.rowCount()):
                if dlg.tableWidget_customer.item(row,1).text()==file_name:
                    comboBox = QComboBox()
                    comboBox.addItems(parmRuns)
                    dlg.tableWidget_customer.setCellWidget(row, 2, comboBox)

            parmRuns.append(tr('@default','new_parametric_run'))
            for row in range(0,dlg.tableWidget_templates.rowCount()):
                if dlg.tableWidget_templates.item(row,1).text()==file_name:
                    comboBox = QComboBox()
                    comboBox.addItems(parmRuns)
                    dlg.tableWidget_templates.setCellWidget(row, 2, comboBox)
    
def openResult(dlg,plugin_dir,conn,cur):
    """ Open the selected result"""
    #print('Open result')
    #print(idx)
    idxs=dlg.tableWidget_customer.selectedIndexes()
            
    if not idxs:
        if conn:
            cur=conn.cursor(cursor_factory = psycopg2.extras.RealDictCursor) 
            for idx in idxs:
                id=dlg.list_tableWidgetResults[dlg.tabwidget.currentIndex()].item(idx.row(),0).text()
                parmRun_name=[dlg.tableWidget_customer.cellWidget(idx, 2).currentText() for idx in range(0,dlg.tableWidget_customer.rowCount()) if dlg.tableWidget_customer.item(idx, 0).text()==id][0]
                #print(parmRun_name)

                name='Customer_'+id
                dir=dlg.config['pathProjects']+"{}\\versions\\{}\\invoked_customers\\".format(dlg.config['projectName'], dlg.config['versionName'])            
                file=dir+"{}.idm".format(name)
                if os.path.exists(file):
                    script="""(:set parm_name (:call find "{}" (:call :parmruns [@ :SYSTEM]) :key 'name :test 'equalp))
(open-as parm_name 'form)""".format(parmRun_name)
                    worker_openParmrunResult = WorkerOpenModelCmd(file,dlg.config,script=script)
                    QThreadPool.globalInstance().start(worker_openParmrunResult) 
                    worker_openParmrunResult.signals.error.connect(dlg.show_error_message)
                    worker_openParmrunResult.signals.progress.connect(dlg.update_progress)   
                    worker_openParmrunResult.signals.finished.connect(dlg.update_finished)              
                    #print('finished open assettype')
            else:
                iface.messageBar().pushMessage("Info", "File not exists!", level=Qgis.Info)  
    else:
        iface.messageBar().pushMessage("Info", "No item selected!", level=Qgis.Info)
        
def openTemplateParmrun(dlg,plugin_dir,conn):
    """ Open the selected template"""
    #print('Open template')
    row_index=dlg.tableWidget_templates.currentRow()
    if row_index!=-1:
        if conn:
            template_id=dlg.tableWidget_templates.item(row_index, 0).text()
            template_name=dlg.tableWidget_templates.item(row_index, 1).text()
            parmRun_name=dlg.tableWidget_templates.cellWidget(row_index, 2).currentText()

            name=template_id+'_'+template_name
            dir=dlg.config['pathProjects']+"{}\\customer_templates\\".format(dlg.config['projectName'])            
            file=dir+"{}.idm".format(name)
            
            # Open the building with the IDA ICE Python API
            #print(file)
            if os.path.exists(file):
                if parmRun_name==tr('@default','new_parametric_run'):
                    script="""(:set name (:call get-unique-component-name "ParmRun_1" [@ :SYSTEM]))
(:set value (:call make-component [@ :SYSTEM] '(macro-object :t parmrun-info :n (:eval name))))
(on-add-component value)
(log-add-object value [@ :SYSTEM])
(if (:call object-p value)
  (:call open-as value 'form))"""
                else:
                    script="""(:set parm_name (:call find "{}" (:call :parmruns [@ :SYSTEM]) :key 'name :test 'equalp))
(open-as parm_name 'form)""".format(parmRun_name)
                #print(script)
                worker_openParmrun = WorkerOpenModelCmd(file,dlg.config,script=script)
                QThreadPool.globalInstance().start(worker_openParmrun) 
                worker_openParmrun.signals.error.connect(dlg.show_error_message)
                worker_openParmrun.signals.progress.connect(dlg.update_progress)   
                worker_openParmrun.signals.finished.connect(dlg.update_finished)   
                #print('finished open parmruns template')
            else:
                iface.messageBar().pushMessage("Info", "File not exists!", level=Qgis.Info)   
    else:
        iface.messageBar().pushMessage("Info", "No item selected!", level=Qgis.Info)
        
def loadCustomerCalibrationData(dlg,config,conn):
    """Load the customers in the customer table with ID, model, Annual energy conumption (heating and cooling)"""
    #print('load customer model calibration data')
    if conn:
        cur=conn.cursor(cursor_factory = psycopg2.extras.RealDictCursor)
        
        #load data to table templates tableWidget_templates
        sql="""WITH sub AS(
    SELECT array(SELECT template FROM "{}".customers GROUP BY template) used_ids
)
SELECT template AS id, template_name, template_name, CASE WHEN template = ANY (sub.used_ids) THEN TRUE ELSE FALSE END AS used 
    FROM customer_templates, sub 
    ORDER BY template;""".format(config['versionName']) # nosec B608

        #print(sql)
        cur.execute(sql)
        i=0
        parmRuns={}
        for template in cur.fetchall():
            #print(template)
            dlg.tableWidget_templates.insertRow(i)
            item=QTableWidgetItem(str(template['id']))
            item.setFlags(ItemIsSelectable | ItemIsEnabled)
            dlg.tableWidget_templates.setItem(i,0,item)
            
            item=QTableWidgetItem(template['template_name'])
            item.setFlags(ItemIsSelectable | ItemIsEnabled)
            dlg.tableWidget_templates.setItem(i,1,item)
            
                        
            comboBox = QComboBox()
            parm_items=getParmRuns(str(template['id'])+"_"+template['template_name'],config)
            parmRuns[str(template['id'])]=parm_items[:-1]
            comboBox.addItems(parm_items)
            dlg.tableWidget_templates.setCellWidget(i, 2, comboBox)
                
            item=QTableWidgetItem(str(template['used']))
            item.setFlags(ItemIsSelectable | ItemIsEnabled)
            dlg.tableWidget_templates.setItem(i,3,item)

            i+=1    

        #print(parmRuns)
        sql="""SELECT c.id AS c_id, c_t.template_name, c_t.template
    FROM "{}".customers c, customer_templates c_t
    WHERE c.template=c_t.template
    ORDER BY c.id;""".format(config['versionName']) # nosec B608
        #print(sql)
        cur.execute(sql)
        i=0
        for customer in cur.fetchall():
            #print(customer)
            dlg.tableWidget_customer.insertRow(i)
            item=QTableWidgetItem(str(customer['c_id']))
            item.setFlags(ItemIsSelectable | ItemIsEnabled)
            dlg.tableWidget_customer.setItem(i,0,item)
            
            item=QTableWidgetItem(customer['template_name'])
            item.setFlags(ItemIsSelectable | ItemIsEnabled)
            dlg.tableWidget_customer.setItem(i,1,item)
            
            comboBox = QComboBox()
            #print(str(customer['template']))
            parm_items=parmRuns[str(customer['template'])]
            comboBox.addItems(parm_items)
            dlg.tableWidget_customer.setCellWidget(i, 2, comboBox)
            i+=1
            
        
def getDefaultDBColumnValue(cur,config,table,column):
    sql="""SELECT column_name, column_default
    FROM information_schema.columns
    WHERE (table_schema, table_name) = ('{}', '{}') AND column_name='{}'
    ORDER BY ordinal_position;""".format(config['versionName'],table,column) # nosec B608
    cur.execute(sql)
    return float(cur.fetchone()['column_default'])
    
def addParamTable(s,dlg,cur,config):
    #print(s.text())
    #input table
    i=dlg.tableWidget_inputs.rowCount()
    dlg.tableWidget_inputs.insertRow(i)
    dlg.tableWidget_inputs.setItem(i,0,QTableWidgetItem(s.text()))
    default_value=getDefaultDBColumnValue(cur,config,'customers',s.text())
    dlg.tableWidget_inputs.setItem(i,1,QTableWidgetItem('[0 '+str(default_value*2)+']'))
    dlg.tableWidget_inputs.setItem(i,2,QTableWidgetItem('10'))
    dlg.tableWidget_inputs.setItem(i,3,QTableWidgetItem(str(default_value)))
    
    #Output table
    dlg.tableWidget_outputs.setColumnCount(dlg.tableWidget_outputs.columnCount()+1) 
    headers=[dlg.tableWidget_outputs.horizontalHeaderItem(i).text() for i in range(0,dlg.tableWidget_outputs.columnCount()-1)]+[s.text()]
    dlg.tableWidget_outputs.setHorizontalHeaderLabels(headers) 
    
    
def startCalibration(dlg,conn,config,plugin_dir):
    """Start the customer calibration. Seperate between calibration with annual energy consumption or load profile. Invoke each customer with ParmRun Macro for Error calculation. 
    Start each selected customer in a loop per API script and write results back to form."""
    #print('Start customer calibration')

    if conn:
        cur=conn.cursor(cursor_factory = psycopg2.extras.RealDictCursor)
        parmRuns_cids={}
        for index in dlg.tableWidget_customer.selectedIndexes():
            
            idx=index.row()
            parmRun_name=dlg.tableWidget_customer.cellWidget(index.row(), 2).currentText()
            if parmRun_name:   
                if parmRun_name in parmRuns_cids:
                    if idx not in parmRuns_cids[parmRun_name]:
                        parmRuns_cids[parmRun_name].append(idx)
                else:
                    parmRuns_cids[parmRun_name]=[idx]
        
        #print(parmRuns_cids)
        dlg.tabwidget.clear()
        dlg.list_tableWidgetResults=[]
        list_counter=0
        total_length = sum(len(v) for v in parmRuns_cids.values())
        dlg.progress.setValue(1)
        counter=0
        for parmRun_cids in parmRuns_cids:
            i=0
            for idx in parmRuns_cids[parmRun_cids]:
                id=dlg.tableWidget_customer.item(idx, 0).text() 
                parmRun_name=dlg.tableWidget_customer.cellWidget(idx, 2).currentText()
                #print('++++id:'+id)
                #invoke customer
                invokeOneFeature(dlg,idx,cur,config,'customer',False,parmRun=True)
                
                dlg.process_running=True
                #worker_Parmrun = WorkerRunAutoMooAPI(config['pathProjects']+'\\{}\\versions\\{}\\invoked_customers\\Customer_{}.idm'.format(config['projectName'],config['versionName'],id),plugin_dir,config,parmRun_name)
                script="""(:set parmrun_ [@ "{}"])
(:set parm_name (:call find "{}" (:call :parmruns [@ :SYSTEM]) :key 'name :test 'equalp))
(open-as parm_name 'form)
(parmrun-init-summary parmrun_)
(parmrun-common-check parmrun_ t)
(PARMRUN-SKOPT parmrun_)
(:save [@ :SYSTEM])
(exit-ida)
""".format(parmRun_name,parmRun_name)
                #print(script)
                worker_Parmrun =  WorkerOpenModelCmd(config['pathProjects']+'{}\\versions\\{}\\invoked_customers\\Customer_{}.idm'.format(config['projectName'],config['versionName'],id),config,script=script,progress=False)
                QThreadPool.globalInstance().start(worker_Parmrun) 
                worker_Parmrun.signals.error.connect(dlg.show_error_message)
                worker_Parmrun.signals.progress.connect(dlg.update_progress)   
                worker_Parmrun.signals.finished.connect(dlg.update_finished)   
                process_wait(dlg,max_sec=1000)
                
                #get best results
                parmRun_file_data=readFileToList(config['pathProjects']+'{}\\versions\\{}\\invoked_customers\\Customer_{}\\{}.idm'.format(config['projectName'],config['versionName'],id,parmRun_name))
                #print(parmRun_file_data)
                bestParmRuns=getBestParmRunsInputs(parmRun_file_data)
                #print(bestParmRuns)
                columns=[tr('@default','ID')]+getParmRunsInputNames(parmRun_file_data)+['']+getParmRunsOutputNames(parmRun_file_data)
                #print(columns)
                
                if i==0:
                    #add parm run result tab
                    dlg.list_tableWidgetResults.append(QTableWidget(0,len(columns)))   
                    dlg.list_tableWidgetResults[list_counter].setHorizontalHeaderLabels(columns)
                    dlg.list_tableWidgetResults[list_counter].setSelectionBehavior(SelectRows)
                    dlg.tabwidget.addTab(dlg.list_tableWidgetResults[list_counter], parmRun_cids)
            
                #write best results to Outputs table
                dlg.list_tableWidgetResults[list_counter].insertRow(i)
                                                
                item=QTableWidgetItem(id)
                item.setFlags(ItemIsEnabled | ItemIsSelectable)
                dlg.list_tableWidgetResults[list_counter].setItem(i,0,item)
        
                input_counter=0
                for input in bestParmRuns[1]:
                    item=QTableWidgetItem(str(input))
                    item.setFlags(ItemIsEnabled | ItemIsSelectable)
                    dlg.list_tableWidgetResults[list_counter].setItem(i,1 + input_counter,item)
                    input_counter+=1

                item=QTableWidgetItem('')
                item.setFlags(ItemIsEnabled | ItemIsSelectable)
                dlg.list_tableWidgetResults[list_counter].setItem(i,1+input_counter,item)
                
                output_counter=0
                for output in bestParmRuns[0]:
                    item=QTableWidgetItem(str(output))
                    item.setFlags(ItemIsEnabled | ItemIsSelectable)
                    dlg.list_tableWidgetResults[list_counter].setItem(i,1+input_counter+1+output_counter,item)
                    output_counter+=1
                i+=1   
                counter+=1
                dlg.progress.setValue(int(counter/total_length*100))
            list_counter+=1
        dlg.progress.setValue(100)
            
def saveCalibValues(dlg,config,conn,cur):
    """Save the callibration values from dlg table (tableWidget_outputs) to customers layer"""
    if conn:
        layer =QgsProject.instance().mapLayersByName(tr('@default','customers'))
        if layer:
            #print('save results')
            table = dlg.list_tableWidgetResults[dlg.tabwidget.currentIndex()]

            idxs = sorted(set(index.row() for index in table.selectedIndexes()))
                    
            if idxs:
                layer_fields= [str(i.name()) for i in layer[0].fields()]
                unique_field_names={}
                cur.execute("""SELECT * FROM model_parms WHERE mapping_direction IN ('<--','<-->') AND type=1;""")
                mapping_parameters=cur.fetchall()
                
                for parm in mapping_parameters:
                    field_name = parm['mapping_expression'].replace('"','')
                    if field_name in layer_fields and field_name not in unique_field_names:
                        unique_field_names[field_name]=[parm['model_name'], parm['parm_name']]
                #print(unique_field_names)
                if not unique_field_names:
                    iface.messageBar().pushMessage("Info", "No parameters mapped to layer customers!", level=Qgis.Info)  
                    return
                    
                for idx in idxs:
                    id=dlg.list_tableWidgetResults[dlg.tabwidget.currentIndex()].item(idx,0).text()
                    #print(id)
                    
                    parmRun_name=[dlg.tableWidget_customer.cellWidget(idx, 2).currentText() for idx in range(0,dlg.tableWidget_customer.rowCount()) if dlg.tableWidget_customer.item(idx, 0).text()==id][0]
                    #print(parmRun_name)

                    file_data=readFileToList(config['pathProjects']+'{}\\versions\\{}\\invoked_customers\\Customer_{}\\{}.idm'.format(config['projectName'],config['versionName'],id,parmRun_name))
                    names_target=getParmRunsInputNamesTargets(file_data)
                    names_target.update(getParmRunsOutputNamesTargets(file_data))
                    #print(names_target)

                    labels=[]
                    for c in range(dlg.list_tableWidgetResults[dlg.tabwidget.currentIndex()].columnCount()):
                        it = dlg.list_tableWidgetResults[dlg.tabwidget.currentIndex()].horizontalHeaderItem(c)
                        labels.append(str(c+1) if it is None else it.text())

                    #print(labels)
                
                    for unique_field_name in unique_field_names:
                        for name_target in names_target:
                            if [i.replace('"','').replace('|','') for i in names_target[name_target]]==unique_field_names[unique_field_name]:
                                for col in range(0,len(labels)):
                                    if labels[col]==name_target:
                                        value=dlg.list_tableWidgetResults[dlg.tabwidget.currentIndex()].item(idx,col).text()
                                        break

                                #update layers
                                sql="""UPDATE "{}".customers SET "{}"={} WHERE id={};\n""".format(config['versionName'],unique_field_name,value,id)
                                #print(sql)
                                cur.execute(sql)    

                    #invoke customers with callib values
                    invokeOneFeature(dlg,dlg.list_tableWidgetResults[dlg.tabwidget.currentIndex()].item(idx,0).text(),cur,config,'customer',False,parmRun=True,saveParmRunResults=True)  
            else:
                iface.messageBar().pushMessage("Info", "No items selected!", level=Qgis.Info)                      