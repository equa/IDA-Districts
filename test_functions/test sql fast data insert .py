from plugins.utility_functions.files import *
#from plugins.utility_functions.db import *
from plugins.utility_functions.sensor_signals import *
from plugins.utility_functions.topology import *
import psycopg2.extras
import psycopg2
from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT
plugin_dir="""C:\\Users\\Peter\\AppData\\Roaming\\QGIS\\QGIS3\\profiles\\default\\python\\plugins\\"""
dictDB={'pwd' : 'p3t3r' , 'host' : 'localhost','port':'5433', 'user' : 'postgres', 'projectName' : 'test15', 'versionName' : 'a'}
source_dir=plugin_dir+"ida_districts_modeling_simulation\\network_models\\test15\\a\\invoked_customers"

#dictDB=getDBConnectionData(plugin_dir)
conn=dbConnect(dictDB,True)
cur=conn.cursor(cursor_factory = psycopg2.extras.RealDictCursor)
#print(cur)


def getMinTimeTableValue(mode,cur,dictDB,table,colmn,starttime,endtime):
    if mode=='Min':
        return getMinMinTimeValue(cur,dictDB,table,colmn,starttime,endtime)
    elif mode=='Max':
        return getMinMaxTimeValue(cur,dictDB,table,colmn,starttime,endtime)
    elif mode=='Average':
        return getMinValueAvgTimeValue(cur,dictDB,table,colmn,starttime,endtime)
    elif mode=='Sum':
        return getMinSumTimeValue(cur,dictDB,table,colmn,starttime,endtime)
    elif mode=='Last value':
        return getMinLastTimeValue(cur,dictDB,table,colmn,endtime)
    elif mode=='First value':
        return getMinFirstTimeValue(cur,dictDB,table,colmn,starttime)
    elif mode=='Hourly average':
        return getMinAvgTimeValue('hour',cur,dictDB,table,colmn,starttime,endtime)
    elif mode=='Values':
        return getMinMinTimeValue(cur,dictDB,table,colmn,starttime,endtime)
    elif mode=='Daily average':
        return getMinAvgTimeValue('day',cur,dictDB,table,colmn,starttime,endtime)
    elif mode=='Monthly average':
        return getMinAvgTimeValue('month',cur,dictDB,table,colmn,starttime,endtime)

def getMaxTimeTableValue(mode,cur,dictDB,table,colmn,starttime,endtime):
    if mode=='Min':
        return getMaxMinTimeValue(cur,dictDB,table,colmn,starttime,endtime)
    elif mode=='Max':
        return getMaxMaxTimeValue(cur,dictDB,table,colmn,starttime,endtime)
    elif mode=='Average':
        return getMaxValueAvgTimeValue(cur,dictDB,table,colmn,starttime,endtime)
    elif mode=='Sum':
        return getMaxSumTimeValue(cur,dictDB,table,colmn,starttime,endtime)
    elif mode=='Last value':
        return getMaxLastTimeValue(cur,dictDB,table,colmn,endtime)
    elif mode=='First value':
        return getMaxFirstTimeValue(cur,dictDB,table,colmn,starttime)
    elif mode=='Values':
        return getMaxMaxTimeValue(cur,dictDB,table,colmn,starttime,endtime)
    elif mode=='Hourly average':
        return getMaxAvgTimeValue('hour',cur,dictDB,table,colmn,starttime,endtime)
    elif mode=='Daily average':
        return getMaxAvgTimeValue('day',cur,dictDB,table,colmn,starttime,endtime)
    elif mode=='Monthly average':
        return getMaxAvgTimeValue('month',cur,dictDB,table,colmn,starttime,endtime)
        
def getMinValueAvgTimeValue(cur,dictDB,table,colmn,starttime,endtime):
    sql="""WITH sub AS(
    SELECT fid,avg("${}") AS value FROM "{}".{} WHERE time>='{}' AND time <='{}' GROUP BY fid
)
SELECT min(value) AS value FROM sub;""".format(colmn,dictDB['versionName'],table,starttime,endtime)
    cur.execute(sql)
    return cur.fetchone()['value']

def getMaxSumTimeValue(cur,dictDB,table,colmn,starttime,endtime):
    sql="""WITH sub AS(
    SELECT fid,sum("${}") AS value FROM "{}".{} WHERE time>='{}' AND time <='{}' GROUP BY fid,segment
)
SELECT max(value) AS value FROM sub;""".format(colmn,dictDB['versionName'],table,starttime,endtime)
    cur.execute(sql)
    #print(sql)
    return cur.fetchone()['value']
    
def getMinSumTimeValue(cur,dictDB,table,colmn,starttime,endtime):
    sql="""WITH sub AS(
    SELECT fid,sum("${}") AS value FROM "{}".{} WHERE time>='{}' AND time <='{}' GROUP BY fid,segment
)
SELECT min(value) AS value FROM sub;""".format(colmn,dictDB['versionName'],table,starttime,endtime)
    #print(sql)
    cur.execute(sql)
    return cur.fetchone()['value']
    
vars={'color': {'mode': 'var', 'name': 't$1', 'var_function': 'Max', 'table_name': 'line_s_t$1_vis'}, 'size': {'mode': 'var', 'name': 't$1', 'var_function': 'Sum', 'table_name': 'line_s_t$1_vis'}, 'rotation': {'mode': False, 'name': '', 'var_function': '', 'table_name': ''}, 
        'time': {'starttime': '2024-01-01 00:00:00', 'endtime': '2024-01-01 01:30:00', 'dt': 0.5, 'first_time_var': False}, 
    'data': [
    {'fid': 1, 'geom': 'LINESTRING Z (-790745.1792399928 23104.177583574485 0,-790811.7750067215 23076.42934743752 0)', 'color': 69.6898411122872763, 'size': 3413.5368024105713289687704466}, 
    {'fid': 1, 'geom': 'LINESTRING Z (-790811.7750067215 23076.42934743752 0,-790878.3707734502 23048.681111300553 0)', 'color': 69.5775805614363838, 'size': 3407.6964686120168762022648413750}, 
    {'fid': 2, 'geom': 'LINESTRING Z (-790525.8830417219 22721.68786040916 0,-790432.2538013184 22747.552291459826 0)', 'color': 69.4752000000000000, 'size': 3401.2439941089250640654521571600}, 
    {'fid': 2, 'geom': 'LINESTRING Z (-790595.539639057 22745.04254132876 0,-790579.6229852312 22706.84257214693 0,-790525.8830417219 22721.68786040916 0)', 'color': 69.6009090909090909, 'size': 3408.0409649966886315233805180000}, 
    {'fid': 2, 'geom': 'LINESTRING Z (-790632.8996409499 22834.706545871697 0,-790595.539639057 22745.04254132876 0)', 'color': 69.7335454545454545, 'size': 3415.1932153486950657233805180000}, 
    {'fid': 2, 'geom': 'LINESTRING Z (-790670.2596428428 22924.370550414635 0,-790632.8996409499 22834.706545871697 0)', 'color': 69.8599000000000000, 'size': 3421.9845804749637328469600823}, 
    {'fid': 3, 'geom': 'LINESTRING Z (-790728.1081998143 22900.266985009846 0,-790670.2596428428 22924.370550414635 0)', 'color': 69.9470000000000000, 'size': 3426.6271364095282995302432757714}, 
    {'fid': 3, 'geom': 'LINESTRING Z (-790785.9567567857 22876.163419605058 0,-790728.1081998143 22900.266985009846 0)', 'color': 69.9787142857142857, 'size': 3428.23966641159551226249461258}, 
    {'fid': 4, 'geom': 'LINESTRING Z (-790670.2596428428 22924.370550414635 0,-790705.086699447 23007.95548626471 0,-790707.7194414178 23014.27406699456 0)', 'color': 69.8843000000000000, 'size': 3423.4925290625540019869398698}, 
    {'fid': 4, 'geom': 'LINESTRING Z (-790707.7194414178 23014.27406699456 0,-790745.1792399928 23104.177583574485 0)', 'color': 69.7974899400729330, 'size': 3419.1140922617511875075237962600}, 
    {'fid': 5, 'geom': 'LINESTRING Z (-790592.4088185075 23286.820065901647 0,-790536.4706827593 23346.799359745575 0)', 'color': 69.2617835563209044, 'size': 3390.2620349689588970578647619667}, 
    {'fid': 5, 'geom': 'LINESTRING Z (-790648.3469542556 23226.840772057723 0,-790592.4088185075 23286.820065901647 0)', 'color': 69.3980000000000000, 'size': 3397.7598990264446877233805180000}, 
    {'fid': 5, 'geom': 'LINESTRING Z (-790704.2850900037 23166.861478213796 0,-790648.3469542556 23226.840772057723 0)', 'color': 69.5343850799117567, 'size': 3405.2351795546802057233805180000}, 
    {'fid': 5, 'geom': 'LINESTRING Z (-790745.1792399928 23104.177583574485 0,-790750.6038063454 23117.196542820897 0,-790704.2850900037 23166.861478213796 0)', 'color': 69.6722052885377267, 'size': 3412.6814498476039684286210190}]}

#print(vars)
#print([var for var in vars if var not in ['time','data']and vars[var]['mode']])
value=getMinTimeTableValue(vars['size']['var_function'],cur,dictDB,vars['size']['table_name'],vars['size']['name'].split('$')[0],vars['time']['starttime'],vars['time']['endtime'])
#print(value)

value=getMaxTimeTableValue(vars['size']['var_function'],cur,dictDB,vars['size']['table_name'],vars['size']['name'].split('$')[0],vars['time']['starttime'],vars['time']['endtime'])
#print(value)
