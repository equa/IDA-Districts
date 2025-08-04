import psycopg2
import psycopg2.extras
from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT
from qgis.PyQt.QtWidgets import QTableWidgetItem,QWidget,QPushButton,QCheckBox,QComboBox
from qgis.PyQt.QtCore import Qt
from plugins.utility_functions.files import *
import os


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
     
def getParmRuns(template_name,dir,dictDB):
    """screen parm runs id the directory"""
    print('++++++++')
    file=dir+"\\"+dictDB['projectName']+"\\customer_templates\\"+template_name+".idm"
    print(file)
    data=readFileToList(file)
    parmRuns=[line.split(':N "')[1].split('" :T')[0] for line in data if ":T PARMRUN-INFO" in line]    
    parmRuns.append('New Parametric Run')
    print(parmRuns)
    return parmRuns
     
def loadCustomerCalibrationData(dlg,dictDB,conn,plugin_dir):
    """Load the customers in the customer table with ID, model, Annual energy conumption (heating and cooling)"""
    print('load customer model calibration data')
    if conn:
        cur=conn.cursor(cursor_factory = psycopg2.extras.RealDictCursor)
        
        #load data to table templates tableWidget_templates
        sql="""WITH sub AS(
    SELECT array(SELECT template FROM "{}".customers GROUP BY template) used_ids
)
SELECT template AS id, template_name, template_name, CASE WHEN template = ANY (sub.used_ids) THEN TRUE ELSE FALSE END AS used 
    FROM customer_templates 
    ORDER BY template;""".format(dictDB['versionName'])

        print(sql)
        cur.execute(sql)
        i=0
        parmRuns={}
        for template in cur.fetchall():
            print(template)
            dlg.tableWidget_templates.insertRow(i)
            item=QTableWidgetItem(str(template['id']))
            item.setFlags(Qt.ItemIsSelectable | Qt.ItemIsEnabled)
            dlg.tableWidget_templates.setItem(i,0,item)
            
            item=QTableWidgetItem(str(template['template_name']))
            item.setFlags(Qt.ItemIsSelectable | Qt.ItemIsEnabled)
            dlg.tableWidget_templates.setItem(i,1,item)
            
                        
            comboBox = QComboBox()
            parm_items=getParmRuns(str(template['id'])+"_"+template['template_name'],getDataCenterDir(plugin_dir),dictDB)
            parmRuns[str(template['id'])]=parm_items[:-1]
            comboBox.addItems(parm_items)
            dlg.tableWidget_templates.setCellWidget(i, 3, comboBox)
                
            item=QTableWidgetItem(str(template['used']))
            item.setFlags(Qt.ItemIsSelectable | Qt.ItemIsEnabled)
            dlg.tableWidget_templates.setItem(i,4,item)

            i+=1    

        print(parmRuns)
        sql="""SELECT c.id AS c_id, c_t.template_name, c_t.template
    FROM "{}".customers c, customer_templates c_t
    WHERE c.template=c_t.template
    ORDER BY c.id;""".format(dictDB['versionName'])
        print(sql)
        cur.execute(sql)
        i=0
        for customer in cur.fetchall():
            print(customer)
            dlg.tableWidget_customer.insertRow(i)
            item=QTableWidgetItem(str(customer['c_id']))
            item.setFlags(Qt.ItemIsSelectable | Qt.ItemIsEnabled)
            dlg.tableWidget_customer.setItem(i,0,item)
            
            item=QTableWidgetItem(str(customer['template_name']))
            item.setFlags(Qt.ItemIsSelectable | Qt.ItemIsEnabled)
            dlg.tableWidget_customer.setItem(i,1,item)
            
            comboBox = QComboBox()
            print(str(customer['template']))
            parm_items=parmRuns[str(customer['template'])]
            comboBox.addItems(parm_items)
            dlg.tableWidget_customer.setCellWidget(i, 3, comboBox)
            i+=1
            
        
def getDefaultDBColumnValue(cur,dictDB,table,column):
    sql="""SELECT column_name, column_default
    FROM information_schema.columns
    WHERE (table_schema, table_name) = ('{}', '{}') AND column_name='{}'
    ORDER BY ordinal_position;""".format(dictDB['versionName'],table,column)
    cur.execute(sql)
    return float(cur.fetchone()['column_default'])
    
def addParamTable(s,dlg,cur,dictDB):
    print(s.text())
    #input table
    i=dlg.tableWidget_inputs.rowCount()
    dlg.tableWidget_inputs.insertRow(i)
    dlg.tableWidget_inputs.setItem(i,0,QTableWidgetItem(s.text()))
    default_value=getDefaultDBColumnValue(cur,dictDB,'customers',s.text())
    dlg.tableWidget_inputs.setItem(i,1,QTableWidgetItem('[0 '+str(default_value*2)+']'))
    dlg.tableWidget_inputs.setItem(i,2,QTableWidgetItem('10'))
    dlg.tableWidget_inputs.setItem(i,3,QTableWidgetItem(str(default_value)))
    
    #Output table
    dlg.tableWidget_outputs.setColumnCount(dlg.tableWidget_outputs.columnCount()+1) 
    headers=[dlg.tableWidget_outputs.horizontalHeaderItem(i).text() for i in range(0,dlg.tableWidget_outputs.columnCount()-1)]+[s.text()]
    dlg.tableWidget_outputs.setHorizontalHeaderLabels(headers) 
    
    
    