from plugins.utility_functions.files import *
from plugins.utility_functions.sensor_signals import *
from plugins.utility_functions.topology import *
from plugins.ida_mosim.invoke import *
import psycopg2.extras
import psycopg2
from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT
plugin_dir="""C:\\Users\\Peter\\AppData\\Roaming\\QGIS\\QGIS3\\profiles\\default\\python\\plugins"""
dictDB={'pwd' : 'p3t3r' , 'host' : 'localhost','port':'5432', 'user' : 'postgres', 'projectName' : 'zollikon', 'versionName' : 'a'}
#dictDB=getDBConnectionData(plugin_dir)
conn=dbConnect(dictDB,True)
cur=conn.cursor(cursor_factory = psycopg2.extras.RealDictCursor)
#print(cur)

def getBestParmRunsInputs (file_data):
    min_error=[0,0,1000000000000000000,10000000000000000]
    min_inputs=''
    i=0
    while i < len(file_data):
        if ":T PARMRUN-SUMMARY-ITEM" in file_data[i]:
            i+=1
            inputs=file_data[i].split('INPUT :V (')[1].strip().strip(')').split(' ')
            i+=1
            error=[float(i) for i in file_data[i].split('OUTPUT :V (')[1].strip().strip(')').split(' ')]
            if error[2]+error[3]<min_error[2]+min_error[3]:
                min_error=error
                min_inputs=inputs
        i+=1
        
    return [min_error,min_inputs]

#ids=[93]
ids=[94,95,96,97,98,104,107,108,109,110,113,115,116,117,121,122,123,125,127,128,129,130,131,132,133,135,136,137,138,140,141,142,143]
for id in ids:
    file=plugin_dir+'\\ida_mosim\\models\\{}\\{}\\invoked_customers\\Customer_{}\\parmrun_annualcallib.idm'.format(dictDB['projectName'],dictDB['versionName'],id)
    parmRun_file_data=readFileToList(file)
    bestParmRuns=getBestParmRunsInputs(parmRun_file_data)
    #print(bestParmRuns)
                
    if conn:
        cur=conn.cursor(cursor_factory = psycopg2.extras.RealDictCursor)
        
        #update layers
        sql=""
        outputs=[]
        outputs.append('\n  "U" ='+str(bestParmRuns[1][0]))
        outputs.append('\n  heat_p_kw ='+str(bestParmRuns[0][0]))
        outputs.append('\n  cool_p_kw ='+str(bestParmRuns[0][1]))
        sql+="""UPDATE "{}".customers SET {} WHERE id={};\n""".format(dictDB['versionName'],','.join([output for output in outputs]),id)
        #print(sql)
        cur.execute(sql)     

        sql="""UPDATE "{}".customers SET "PhiRadH_nom" = "U"*100 WHERE id ={};""".format(dictDB['versionName'],id)
        #print(sql)
        cur.execute(sql) 
        
        #invoke customers with callib values
        invokeOneFeature('',str(id),plugin_dir+'\\ida_mosim',cur,dictDB,'customer',iface,False,parmRun=True,saveParmRunResults=True) 


