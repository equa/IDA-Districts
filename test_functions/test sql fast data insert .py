from plugins.utility_functions.files import *
from plugins.utility_functions.sensor_signals import *
from plugins.utility_functions.topology import *
import psycopg2.extras
import psycopg2
from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT
plugin_dir="""C:\\Users\\Peter\\AppData\\Roaming\\QGIS\\QGIS3\\profiles\\default\\python\\plugins\\"""
dictDB={'pwd' : 'p3t3r' , 'host' : 'localhost','port':'5433', 'user' : 'postgres', 'projectName' : 'reidling_v4', 'versionName' : 'a'}
source_dir=plugin_dir+"ida_districts_modeling_simulation\\network_models\\reidling_v4\\a\\invoked_customers"

from typing import Iterator, Optional,Dict, Any
import io

import pandas as pd
import numpy as np

#dictDB=getDBConnectionData(plugin_dir)
conn=dbConnect(dictDB,True)
cur=conn.cursor(cursor_factory = psycopg2.extras.RealDictCursor)
print(cur)

def getAvergageByMode(mode):
    """return value in seconds"""
    if mode=='Hourly average':
        return 'hour'
    elif mode=='Daily average':
        return 'day'
    elif mode=='Monthly average':
        return 'month'
        
def getNonTimeVarFunctionValue(var,time):
    if var['var_function']=='Max':
        sql="""SELECT fid,max({}) AS {} FROM {}.{} WHERE time BETWEEN '{}' AND '{}' GROUP BY fid,geom ORDER BY fid""".format(var['name'],var['name'],dictDB['versionName'],var['table_name'],time['starttime'],time['endtime'])
    elif var['var_function']=='Min':
        sql="""SELECT fid,min({}) AS {} FROM {}.{} WHERE time BETWEEN '{}' AND '{}' GROUP BY fid,geom ORDER BY fid""".format(var['name'],var['name'],dictDB['versionName'],var['table_name'],time['starttime'],time['endtime'])
    elif var['var_function']=='Average':
        sql="""SELECT fid,avg({}) AS {} FROM {}.{} WHERE time BETWEEN '{}' AND '{}' GROUP BY fid,geom ORDER BY fid""".format(var['name'],var['name'],dictDB['versionName'],var['table_name'],time['starttime'],time['endtime'])
    elif var['var_function']=='Last value':
        sql="""SELECT DISTINCT ON (fid) 
    fid,{},time
FROM {}.{}
WHERE time <= '{}'
ORDER BY fid,time DESC""".format(var['name'],dictDB['versionName'],var['table_name'],time['endtime'])
    elif var['var_function']=='Sum':
         sql="""SELECT fid,sum({}) AS {} FROM {}.{} WHERE time BETWEEN '{}' AND '{}' GROUP BY fid,geom ORDER BY fid""".format(var['name'],var['name'],dictDB['versionName'],var['table_name'],time['starttime'],time['endtime'])
    elif var['var_function']=='First value':
        sql="""SELECT DISTINCT ON (fid) 
    fid,{},time
FROM {}.{}
WHERE time >= '{}'
ORDER BY fid,time ASC""".format(var['name'],dictDB['versionName'],var['table_name'],time['starttime'])
    elif var['var_function'] in time_values:
        print('Hourly average')
        sql="""SELECT fid,geom,{} AS {},time FROM {}.{} WHERE time BETWEEN '{}' AND '{}' ORDER BY fid, time""".format(var['name'],var['name'],dictDB['versionName'],var['table_name'],time['starttime'],time['endtime'])
    return sql
        
time_values=['Values','Hourly average','Daily average','Monthly average']
vars={'color': {'mode': 'var', 'name': 'load', 'var_function': 'Hourly average', 'table_name': 'customer_m_load'}, 
    'size': {'mode': 'var', 'name': 'load', 'var_function': 'Hourly average', 'table_name': 'customer_m_load'}, 
    'rotation': {'mode': 'par', 'name': 'id', 'var_function': '', 'table_name': 'dhc_customers'}, 
    'time': {'starttime': '2022-01-01 00:00:00', 'endtime': '2022-01-01 01:00:00'}, 
    'data': ''}
    
vars={'color': {'mode': 'var', 'name': 'vdot', 'var_function': 'Last value', 'table_name': 'customer_m_vdot'}, 
    'size': {'mode': 'var', 'name': 'load', 'var_function': 'Sum', 'table_name': 'customer_m_load'}, 
    'rotation': {'mode': False, 'name': 'id', 'var_function': '', 'table_name': 'dhc_customers'}, 
    'time': {'starttime': '2022-01-01 00:00:00', 'endtime': '2022-01-01 01:00:00'}, 
    'data': ''}
    
vars={'color': {'mode': 'var', 'name': 'load', 'var_function': 'Hourly average', 'table_name': 'customer_m_load'}, 'size': {'mode': False, 'name': '', 'var_function': '', 'table_name': ''}, 'rotation': {'mode': False, 'name': '', 'var_function': '', 'table_name': ''}, 'time': {'starttime': '2022-01-01 00:00:00', 'endtime': '2022-01-01 01:00:00'}, 'data': ''}

    
color=True
size=True
rotation=False
if vars['color']['var_function'] in time_values:
    time_color=True
else:
    time_color=False
if vars['size']['var_function'] in time_values:
    time_size=True
else:
    time_size=False  
if vars['rotation']['var_function'] in time_values:
    time_rotation=True
else:
    time_rotation=False
    
first_time_var='color' if time_color else ('size' if time_size else ('rotation' if time_rotation else False))
first_par_var='color' if vars['color']['mode'] else ('size' if vars['size']['mode'] else ('rotation' if vars['rotation']['mode'] else False))
print(first_time_var)
print(first_par_var)
first_group=first_time_var if first_time_var else first_par_var

print('+++++time++++++')
if first_time_var or first_par_var:
    sql="""SELECT {}.fid {}, {}
    FROM {}
    WHERE {}
    GROUP BY {}
    ORDER BY {} {}.fid;""".format(first_time_var if first_time_var else first_par_var,
        """,date_trunc('{}', {}.time) AS time""".format(getAvergageByMode(vars[first_time_var]['var_function']),first_time_var) if first_time_var else '',
        ','.join([i for i in
        ['avg(color.{}) AS color'.format(vars['color']['name']) if time_color else ('color.'+vars['color']['name'] if vars['color']['mode'] else '' ),
        'avg(size.{}) AS size'.format(vars['size']['name']) if time_size else ('size.'+vars['size']['name'] if vars['size']['mode'] else '' ),
        'avg(rotation.{}) AS rotation'.format(vars['rotation']['name']) if time_rotation else ('rotation.'+vars['rotation']['name'] if vars['rotation']['mode'] else '' )] 
        if i]),
        ','.join([i for i in  #from
            ["""{}.{} AS color""".format(dictDB['versionName'],vars['color']['table_name']) if time_color else (
            """({}) color""".format(getNonTimeVarFunctionValue(vars['color'],vars['time'])) 
            if vars['color']['mode']=='var' else ("{}.{} AS color".format(dictDB['versionName'],vars['color']['table_name']) if vars['color']['mode']=='par' else '')),
            """{}.{} AS size""".format(dictDB['versionName'],vars['size']['table_name']) if time_size else (
            """({}) size""".format(getNonTimeVarFunctionValue(vars['size'],vars['time']))  
            if vars['size']['mode']=='var'else ("{}.{} AS size".format(dictDB['versionName'],vars['size']['table_name']) if vars['size']['mode']=='par' else '')),
            """{}.{} AS rotation""".format(dictDB['versionName'],vars['rotation']['table_name']) if time_rotation else (
            """({}) rotation""".format(getNonTimeVarFunctionValue(vars['rotation'],vars['time'])) 
            if vars['rotation']['mode']=='var' else ("{}.{} AS rotation".format(dictDB['versionName'],vars['rotation']['table_name']) if vars['rotation']['mode']=='par' else ''))] 
            if i]),
        ' AND '.join([i for i in #where
            [' AND '.join([first_group+'.fid='+var+('.fid' if vars[var]['mode']=='var' else '.id') for var in vars if var not in ['time','data']+([first_time_var] if first_time_var else []) and vars[var]['mode']]),
            ' AND '.join([first_time_var+'.time='+var+'.time' for var in vars if var not in ['time','data']+[first_time_var] and vars[var]['var_function'] in time_values]),
            """{}.time <= '{}' AND {}.time >= '{}'""".format(first_time_var,vars['time']['endtime'],first_time_var,vars['time']['starttime']) if first_time_var else ''] if i]),
        ','.join([i for i in #group by
            ["""date_trunc('{}', {}.time)""".format(getAvergageByMode(vars[first_time_var]['var_function']),first_time_var) if first_time_var else '',
            first_group+'.fid',
            ','.join([var+'.'+vars[var]['name'] for var in vars if var not in ['time','data'] and vars[var]['mode'] and vars[var]['var_function'] not in time_values])] if i]),
        """date_trunc('{}', {}.time),""".format(getAvergageByMode(vars[first_time_var]['var_function']),first_time_var) if first_time_var else '',
        first_group,first_group)
        
    print(sql)
    