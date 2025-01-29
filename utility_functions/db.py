#from plugins.utility_functions.files import *
import psycopg2
from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT   
from qgis.utils import iface
from qgis.core import Qgis, QgsMessageLog
from typing import Iterator, Optional,Dict, Any
import io
import subprocess
import os
from plugins.utility_functions.files import *

def dbColumnDataType(cur,version,table,col):
    sql="""SELECT column_name, data_type 
    FROM information_schema.columns 
    WHERE table_schema = '{}' 
    AND table_name = '{}' 
    AND column_name = '{}';""".format(version,table,col)
    cur.execute(sql)
    return cur.fetchone()['data_type']
    
def dbColumnIsNumeric(cur,version,table,col):
    if dbColumnDataType(cur,version,table,col) in ['integer', 'numeric', 'decimal', 'double precision', 'real', 'smallint']:
        return True
    else:
        return False
    
def copy_schema(baseName,new_versionName,dictDB,cur,plugin_dir):
    """copy schema"""
    os.environ['PGPASSWORD'] = dictDB['pwd']
    path_postgres=loadIDADistrictsConfig(plugin_dir)['path_postgresql']
    cmd=' "{}bin\\pg_dump" -U {} -h {} -p {} -d {} -n """{}""" > "{}\\dump_schema.sql" '.format(path_postgres,dictDB['user'],dictDB['host'],dictDB['port'],dictDB['projectName'],baseName,plugin_dir)
    print(cmd)
    subprocess.call(cmd, shell=True)  
    
    sql = 'ALTER SCHEMA "'+baseName+'" RENAME TO "'+new_versionName+'" ;'
    print(sql)
    cur.execute(sql)           
    
    cmd = ' "{}bin\\psql" -d {} -h {} -p {} -U {} < "{}\\dump_schema.sql"'.format(path_postgres,dictDB['projectName'],dictDB['host'],dictDB['port'], dictDB['user'],plugin_dir)
    print(cmd)
    subprocess.call(cmd, shell=True)  
        
def setSeqIdToMax(seq,table,col,cur):
    sql="""SELECT setval('{}', (SELECT COALESCE(MAX({}), 0) FROM {}) + 1);""".format(seq,col,table)
    print(sql)
    cur.execute(sql)

def getTimeDiff(cur,dictDB,table,col,order_col):
    sql="""SELECT EXTRACT(EPOCH FROM (next_time.time-start_time.time)) AS diff 
    FROM (SELECT {} AS time FROM "{}".{} ORDER BY {},{}{} LIMIT 1) start_time,
        (SELECT {}  AS time FROM "{}".{} ORDER BY {},{}{} LIMIT 1 OFFSET 1) next_time;""".format(col,dictDB['versionName'],table,order_col,'segment,' if 'line_' in table and col in ['p','temp'] else '',col,col,dictDB['versionName'],table,order_col,'segment,' if 'line_' in table and col in ['p','temp'] else '',col)
    print(sql)
    cur.execute(sql)
    return cur.fetchone()['diff']
    
def getAvergageByMode(mode,cur,dictDB,table):
    """return value in seconds"""
    if mode=='Hourly average':
        return 'hour'
    elif mode=='Daily average':
        return 'day'
    elif mode=='Monthly average':
        return 'month'
    elif mode=='Values':
        return getTimeDiff(cur,dictDB,table,'time','fid')/3600
        
def featureCount(cur,dictDB,network,type):
    sql="""SELECT count(*) FROM "{}".{}s WHERE network=array[{}];""".format(dictDB['versionName'],type,network)
    cur.execute(sql)
    return cur.fetchone()['count']

def streetsCount(cur,dictDB):
    sql="""SELECT count(*) FROM "{}".streets;""".format(dictDB['versionName'])
    cur.execute(sql)
    return cur.fetchone()['count']

def getDecoupledFeatureCompPerFeature(feature,cur,dictDB):
    sql="""SELECT f_dec.comp_name
    FROM "{}".{}s f, "{}".feature_decoupling f_dec
    WHERE f.id={} AND f.assettype=f_dec.assettype AND f.assetgroup=f_dec.assetgroup AND f_dec.type='{}';""".format(dictDB['versionName'],feature['feature'],dictDB['versionName'],feature['id'],feature['feature'])
    print(sql)
    cur.execute(sql)
    return [i['comp_name'] for i in cur.fetchall()]
    
def getDecoupledFeatureCompPerAssettype(dictDB,cur,assettype,assetgroup):
    sql="""SELECT f_dec.comp_name
    FROM "{}".feature_decoupling f_dec
    WHERE {}=f_dec.assettype AND {}=f_dec.assetgroup AND f_dec.type='customer';""".format(dictDB['versionName'],assettype,assetgroup)
    print(sql)
    cur.execute(sql)
    return [i['comp_name'] for i in cur.fetchall()]

def getUsedDecoupledFeatureAssettypes(usedFeatureAssettypes,cur,dictDB,submodel,cosims):
    assettypes=[]
    for cosim in cosims:
        sql="""(SELECT 'customer' AS feature,f.assettype, f.assetgroup, CASE WHEN s_m.submodel::int={} THEN TRUE ELSE FALSE END AS network_side
    FROM "{}".customers f, "{}".lines l,"{}".submodels s_m
    WHERE ({} = f.submodel AND {} = ANY (l.submodel) OR {} = f.submodel AND {} = ANY (l.submodel)) AND ST_DWithin(l.geom,s_m.geom,0.001)
    GROUP BY feature,f.assettype, f.assetgroup, network_side)
UNION 
(SELECT 'energy_plant' AS feature,f.assettype, f.assetgroup, CASE WHEN s_m.submodel::int={} THEN TRUE ELSE FALSE END AS network_side
    FROM "{}".energy_plants f, "{}".lines l,"{}".submodels s_m
    WHERE ({} = f.submodel AND {} = ANY (l.submodel) OR {} = f.submodel AND {} = ANY (l.submodel)) AND ST_DWithin(l.geom,s_m.geom,0.001)
    GROUP BY feature,f.assettype, f.assetgroup, network_side)
ORDER BY feature,assetgroup,assettype;""".format(submodel,dictDB['versionName'],dictDB['versionName'],dictDB['versionName'],cosim,submodel,submodel,cosim,
            submodel,dictDB['versionName'],dictDB['versionName'],dictDB['versionName'],cosim,submodel,submodel,cosim)
        print(sql)
        cur.execute(sql)
        decoupled_assettypes=[{'feature': i['feature'], 'assetgroup': i['assetgroup'], 'assettype': i['assettype'], 'assettype_name':j['assettype_name'], 'network_side': i['network_side']} 
            for i in cur.fetchall() for j in usedFeatureAssettypes if i['feature']==j['feature'] and i['assetgroup']==j['assetgroup'] and i['assettype']==j['assettype']]
        assettypes.extend([at for at in decoupled_assettypes if at not in assettypes])
    print(assettypes)
    return assettypes
    
def getFeatureIds(dictDB,cur,submodel,cosims):
    fids=[]
    for cosim in cosims:
        sql="""(SELECT 'customer' AS feature, f.assettype, f.assetgroup, f.id, f.submodel, s_m.submodel AS cosim, CASE WHEN s_m.submodel::int={} THEN TRUE ELSE FALSE END AS network_side
    FROM "{}".customers f, "{}".customer_connections f_conns, "{}".lines l, "{}".submodels s_m
    WHERE ST_DWithin(l.geom,s_m.geom,0.001) AND f.id=f_conns.cid AND l.id=f_conns.lid AND ({} = f.submodel AND {} = ANY (l.submodel) OR {} = f.submodel AND {} = ANY (l.submodel)))
UNION 
(SELECT 'energy_plant' AS feature, f.assettype, f.assetgroup, f.id, f.submodel, s_m.submodel AS cosim, CASE WHEN s_m.submodel::int={} THEN TRUE ELSE FALSE END AS network_side
    FROM "{}".energy_plants f, "{}".energy_plant_connections f_conns, "{}".lines l, "{}".submodels s_m
    WHERE ST_DWithin(l.geom,s_m.geom,0.001) AND f.id=f_conns.epid AND l.id=f_conns.lid AND ({} = f.submodel AND {} = ANY (l.submodel) OR {} = f.submodel AND {} = ANY (l.submodel)))
ORDER BY feature,id;""".format(submodel,dictDB['versionName'],dictDB['versionName'],dictDB['versionName'],dictDB['versionName'],cosim,submodel,submodel,cosim,
            submodel,dictDB['versionName'],dictDB['versionName'],dictDB['versionName'],dictDB['versionName'],cosim,submodel,submodel,cosim)
        print(sql)
        
        cur.execute(sql)
        fids.extend([i for i in cur.fetchall() if i not in fids])
    return fids

def getFeatureIdFromName(dictDB,cur,feature):
    sql="""SELECT id FROM type WHERE replace(lower(name),' ','_')='{}';""".format(feature)
    print(sql)
    cur.execute(sql)
    return cur.fetchone()['id']
    
def getNetworks(cur,dictDB):
    sql="""SELECT id AS network FROM "{}".network;""".format(dictDB['versionName'])
    cur.execute(sql)
    networks=[str(i['network']) for i in cur.fetchall()]
    return networks
    
def getUsedNetworks(cur,dictDB):
    sql="""(
    SELECT network FROM "{}".lines GROUP BY network
    UNION
    SELECT unnest(network) AS network FROM "{}".customers GROUP BY network
    UNION
    SELECT unnest(network) AS network FROM "{}".energy_plants GROUP BY network
    UNION
    SELECT unnest(network) AS network FROM "{}".devices GROUP BY network
)
ORDER BY network;""".format(dictDB['versionName'],dictDB['versionName'],dictDB['versionName'],dictDB['versionName'])
    cur.execute(sql)
    networks=[str(i['network']) for i in cur.fetchall()]
    return networks
    
def getLineNetworks(cur,dictDB):
    sql="""SELECT network FROM "{}".lines GROUP BY network ORDER BY network;""".format(dictDB['versionName'])
    cur.execute(sql)
    networks=[i['network'] for i in cur.fetchall()]
    return networks

def getLineSubmodels(cur,dictDB):
    sql="""SELECT unnest(submodel) as submodels FROM "{}".lines GROUP BY submodels ORDER BY submodels;""".format(dictDB['versionName'])
    cur.execute(sql)
    submodels=[i['submodels'] for i in cur.fetchall()]
    return submodels
    
def getFeatureSubmodels(cur,dictDB,type):
    sql="""SELECT submodel FROM "{}".{}s GROUP BY submodel ORDER BY submodel;""".format(dictDB['versionName'],type)
    cur.execute(sql)
    submodels=[i['submodel'] for i in cur.fetchall()]
    return submodels

def getUsedFeatureAssettypes(cur,dictDB):
    sql="""(SELECT 'customer' AS feature, f.assetgroup,f.assettype, f_at.assettype_name
    FROM "{}".customers f,customer_assettypes f_at 
    WHERE f.assetgroup=f_at.assetgroup AND f.assettype=f_at.assettype
    GROUP BY f.assetgroup,f.assettype,f_at.assettype_name)
UNION
(SELECT 'energy_plant' AS feature, f.assetgroup,f.assettype,f_at.assettype_name
    FROM "{}".energy_plants f, energy_plant_assettypes f_at
     WHERE f.assetgroup=f_at.assetgroup AND f.assettype=f_at.assettype
    GROUP BY f.assetgroup,f.assettype,f_at.assettype_name)
ORDER BY feature, assetgroup,assettype;""".format(dictDB['versionName'],dictDB['versionName'])
    cur.execute(sql)
    return cur.fetchall()
    
def getUsedSubmodels(cur,dictDB):
    sql="""(
    SELECT unnest(submodel) AS submodel FROM "{}".lines GROUP BY submodel
    UNION
    SELECT submodel FROM "{}".customers GROUP BY submodel
    UNION
    SELECT submodel FROM "{}".energy_plants GROUP BY submodel
    UNION
    SELECT submodel FROM "{}".devices GROUP BY submodel
)
ORDER BY submodel;""".format(dictDB['versionName'],dictDB['versionName'],dictDB['versionName'],dictDB['versionName'])
    cur.execute(sql)
    submodels=[str(i['submodel']) for i in cur.fetchall()]
    return submodels

def getFeatureIdsPerSubmodel(submodel,cur,dictDB):
    sql="""(
    SELECT 1 AS feature, id FROM "{}".customers WHERE submodel={}
    UNION
    SELECT 2 AS feature, id FROM "{}".energy_plants WHERE submodel={}
    UNION
    SELECT 3 AS feature, id FROM "{}".devices WHERE submodel={}
)
ORDER BY feature,id;""".format(dictDB['versionName'],submodel,dictDB['versionName'],submodel,dictDB['versionName'],submodel)
    cur.execute(sql)
    return cur.fetchall()
    
def getFeatureIdsPerSubmodelAndTypename(submodel,type,cur,dictDB):
    sql="""SELECT id FROM "{}".{}s WHERE submodel={};""".format(dictDB['versionName'],submodel)
    cur.execute(sql)
    return [id['id'] for id in cur.fetchall()]

def getSubmodelPerFeatureIdTypename(id,feature,cur,dictDB):
    sql="""SELECT submodel FROM "{}".{}s WHERE id={};""".format(dictDB['versionName'],feature.replace(" ","_"),id)
    cur.execute(sql)
    return cur.fetchone()
    
def getDrawnSubmodels(cur,dictDB):
    sql="""SELECT id FROM "{}".submodels;""".format(dictDB['versionName'])
    cur.execute(sql)
    submodels=[i['id'] for i in cur.fetchall()]
    if len(submodels)==0:
        iface.messageBar().pushMessage("Info", "No simulation model has been build yet!", level=Qgis.Info)
        return False
    else:
        return submodels
        
def getSupervisorySubmodel(cur,dictDB):
    sql="""SELECT submodel FROM "{}".supervisory_ctrl;""".format(dictDB['versionName'])
    cur.execute(sql)
    return cur.fetchone()
            
def getNetworkSubmodels(cur,dictDB,networks):
    """Get submodels of a list of networks based on lines"""
    sql="""SELECT unnest(submodel) AS submodel FROM "{}".lines WHERE network IN ({}) GROUP BY submodel ORDER BY submodel;""".format(dictDB['versionName'], ','.join([i for i in networks]))
    print(sql)
    cur.execute(sql)
    submodels=[str(i['submodel']) for i in cur.fetchall()]
    return submodels
      
def checkTableNameExists(cur,dictDB,table):
    sql="""SELECT EXISTS (
    SELECT FROM information_schema.tables 
    WHERE  table_schema = '{}'
    AND    table_name   = '{}'
    );""".format(dictDB['versionName'],table)
    cur.execute(sql)
    return cur.fetchone()['exists']
   
def getProjectVersionNames(cur):
    sql="SELECT nspname FROM pg_catalog.pg_namespace WHERE nspname NOT IN ('topology','temp','streets_help_topo','public','pg_toast','pg_catalog','information_schema');"
    cur.execute(sql)
    versionNames=[]
    for version in cur.fetchall():
        versionNames.append(version['nspname'])
    return versionNames
    
def getClimateData(cur,dictDB,errorMsg):
    """ get climate data from DB"""
    print('get climate data')
    if checkDBVersionConnected(dictDB,errorMsg):
        sql='SELECT name, longitude, latitude,file_name AS filename ,timezone,height FROM "{}".climate;'.format(dictDB['versionName'])
        print (sql)
        cur.execute(sql)
        return cur.fetchone()

def getMaxTableValue(cur,dictDB,table,colmn):
    sql="""SELECT max("{}") AS value FROM "{}".{};""".format(colmn,dictDB['versionName'],table)
    cur.execute(sql)
    return cur.fetchone()['value']
    
def getMinTableValue(cur,dictDB,table,colmn):
    sql="""SELECT min("{}") AS value FROM "{}".{};""".format(colmn,dictDB['versionName'],table)
    cur.execute(sql)
    return cur.fetchone()['value']
    
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
        
def getMinMinTimeValue(cur,dictDB,table,colmn,starttime,endtime):
    sql="""WITH sub AS(
    SELECT fid,min("${}") AS value FROM "{}".{} WHERE time>='{}' AND time <='{}' GROUP BY fid{}
)
SELECT min(value) AS value FROM sub;""".format(colmn,dictDB['versionName'],table,starttime,endtime,', segment' if 'line_' in table and colmn in ['p','temp'] else '')
    cur.execute(sql)
    return cur.fetchone()['value']

def getMinMaxTimeValue(cur,dictDB,table,colmn,starttime,endtime):
    sql="""WITH sub AS(
    SELECT fid,max("${}") AS value FROM "{}".{} WHERE time>='{}' AND time <='{}' GROUP BY fid{}
)
SELECT min(value) AS value FROM sub;""".format(colmn,dictDB['versionName'],table,starttime,endtime,', segment' if 'line_' in table and colmn in ['p','temp'] else '')
    cur.execute(sql)
    return cur.fetchone()['value']
    
def getMinValueAvgTimeValue(cur,dictDB,table,colmn,starttime,endtime):
    sql="""WITH sub AS(
    SELECT fid,avg("${}") AS value FROM "{}".{} WHERE time>='{}' AND time <='{}' GROUP BY fid{}
)
SELECT min(value) AS value FROM sub;""".format(colmn,dictDB['versionName'],table,starttime,endtime,', segment' if 'line_' in table and colmn in ['p','temp'] else '')
    cur.execute(sql)
    return cur.fetchone()['value']
    
def getMinSumTimeValue(cur,dictDB,table,colmn,starttime,endtime):
    sql="""WITH sub AS(
    SELECT fid,sum("${}") AS value FROM "{}".{} WHERE time>='{}' AND time <='{}' GROUP BY fid{}
)
SELECT min(value) AS value FROM sub;""".format(colmn,dictDB['versionName'],table,starttime,endtime,', segment' if 'line_' in table and colmn in ['p','temp'] else '')
    cur.execute(sql)
    return cur.fetchone()['value']
    
def getMinLastTimeValue(cur,dictDB,table,colmn,endtime):
    sql="""WITH sub AS(
    SELECT DISTINCT ON (fid) 
        fid,"${}" AS value
    FROM "{}".{}
    WHERE time = '{}'
    ORDER BY fid,time DESC
)
SELECT min(value) AS value FROM sub;""".format(colmn,dictDB['versionName'],table,endtime)
    cur.execute(sql)
    return cur.fetchone()['value']
    
def getMinFirstTimeValue(cur,dictDB,table,colmn,starttime):
    sql="""WITH sub AS(
    SELECT DISTINCT ON (fid) 
        fid,"${}" AS value
    FROM "{}".{}
    WHERE time = '{}'
    ORDER BY fid,time ASC
)
SELECT min(value) AS value FROM sub;""".format(colmn,dictDB['versionName'],table,starttime)
    cur.execute(sql)
    return cur.fetchone()['value']
    
def getMinAvgTimeValue(mode,cur,dictDB,table,colmn,starttime,endtime):
    sql="""WITH sub AS(
    SELECT fid,date_trunc('{}', time) AS time, avg("${}") AS value
        FROM "{}".{}
        WHERE time BETWEEN '{}' AND '{}'
        GROUP BY date_trunc('{}', time),fid{}
        ORDER BY date_trunc('{}', time), fid
)
SELECT min(value) AS value FROM sub;""".format(mode,colmn,dictDB['versionName'],table,starttime,endtime,mode,', segment' if 'line_' in table and colmn in ['p','temp'] else '',mode)
    print(sql)
    cur.execute(sql)
    return cur.fetchone()['value']
    
def getMaxMinTimeValue(cur,dictDB,table,colmn,starttime,endtime):
    sql="""WITH sub AS(
    SELECT fid,min("${}") AS value FROM "{}".{} WHERE time>='{}' AND time <='{}' GROUP BY fid{}
)
SELECT max(value) AS value FROM sub;""".format(colmn,dictDB['versionName'],table,starttime,endtime,', segment' if 'line_' in table and colmn in ['p','temp'] else '')
    cur.execute(sql)
    return cur.fetchone()['value']

def getMaxMaxTimeValue(cur,dictDB,table,colmn,starttime,endtime):
    sql="""WITH sub AS(
    SELECT fid,max("${}") AS value FROM "{}".{} WHERE time>='{}' AND time <='{}' GROUP BY fid{}
)
SELECT max(value) AS value FROM sub;""".format(colmn,dictDB['versionName'],table,starttime,endtime,', segment' if 'line_' in table and colmn in ['p','temp'] else '')
    cur.execute(sql)
    return cur.fetchone()['value']
    
def getMaxValueAvgTimeValue(cur,dictDB,table,colmn,starttime,endtime):
    sql="""WITH sub AS(
    SELECT fid,avg("${}") AS value FROM "{}".{} WHERE time>='{}' AND time <='{}' GROUP BY fid{}
)
SELECT max(value) AS value FROM sub;""".format(colmn,dictDB['versionName'],table,starttime,endtime,', segment' if 'line_' in table and colmn in ['p','temp'] else '')
    cur.execute(sql)
    return cur.fetchone()['value']
    
def getMaxSumTimeValue(cur,dictDB,table,colmn,starttime,endtime):
    sql="""WITH sub AS(
    SELECT fid,sum("${}") AS value FROM "{}".{} WHERE time>='{}' AND time <='{}' GROUP BY fid{}
)
SELECT max(value) AS value FROM sub;""".format(colmn,dictDB['versionName'],table,starttime,endtime,', segment' if 'line_' in table and colmn in ['p','temp'] else '')
    cur.execute(sql)
    return cur.fetchone()['value']
    
def getMaxLastTimeValue(cur,dictDB,table,colmn,endtime):
    sql="""WITH sub AS(
    SELECT DISTINCT ON (fid) 
        fid,"${}" AS value
    FROM "{}".{}
    WHERE time = '{}'
    ORDER BY fid,time DESC
)
SELECT max(value) AS value FROM sub;""".format(colmn,dictDB['versionName'],table,endtime)
    cur.execute(sql)
    return cur.fetchone()['value']
    
def getMaxFirstTimeValue(cur,dictDB,table,colmn,starttime):
    sql="""WITH sub AS(
    SELECT DISTINCT ON (fid) 
        fid,"${}" AS value
    FROM "{}".{}
    WHERE time = '{}'
    ORDER BY fid,time ASC
)
SELECT max(value) AS value FROM sub;""".format(colmn,dictDB['versionName'],table,starttime)
    cur.execute(sql)
    return cur.fetchone()['value']

def getMaxAvgTimeValue(mode,cur,dictDB,table,colmn,starttime,endtime):
    sql="""WITH sub AS(
    SELECT fid,date_trunc('{}', time) AS time, avg("${}") AS value
        FROM "{}".{}
        WHERE time BETWEEN '{}' AND '{}'
        GROUP BY date_trunc('{}', time),fid{}
        ORDER BY date_trunc('{}', time), fid
)
SELECT max(value) AS value FROM sub;""".format(mode,colmn,dictDB['versionName'],table,starttime,endtime,mode,', segment' if 'line_' in table and colmn in ['p','temp'] else '',mode)
    print(sql)
    cur.execute(sql)
    return cur.fetchone()['value']
    
def getMaxId(cur,table_name):
    """return highest connections id"""
    sql="SELECT max(id) AS max FROM public.{};".format(table_name)
    cur.execute(sql)
    id=cur.fetchone()
    if id['max']!=None:
        return id['max']
    else:
        return 0
        
def getMaxIdSchema(cur,table_name,schema):
    """return highest connections id"""
    sql="""SELECT max(id) AS max_id FROM "{}".{};""".format(schema,table_name)
    cur.execute(sql)
    id=cur.fetchone()
    if id['max_id']!=None:
        return id['max_id']
    else:
        return 0

def checkDBProjectConnected(dictDB,errorMsg):
    """ Check if connected to DB project"""
    print('check project connection')
    if dictDB['pwd'] and dictDB['user'] and dictDB['host'] and dictDB['port'] and dictDB['projectName']:
        print('connected to project!')
        return True
    else:
        print('not connected to project!')
        if errorMsg:
            iface.messageBar().pushMessage("ERROR", "Not connected to DB!", level=Qgis.Critical)
        return False
        
def checkDBVersionConnected(dictDB,errorMsg):
    """ Check if connected to DB version"""
    print('check version connection')
    if dictDB['pwd'] and dictDB['user'] and dictDB['host'] and dictDB['port'] and dictDB['projectName'] and dictDB['versionName']:
        print('connected to version!')
        return True
    else:
        print('not connected to version!')
        if errorMsg:
            iface.messageBar().pushMessage("WARNING", "Not connected to DB!", level=Qgis.Warning)
        return False
        
def dbConnect(dictDB,errorMsg):
    conn=""      
    if checkDBProjectConnected(dictDB,errorMsg):
        try:
            conn = psycopg2.connect(
                host=dictDB['host'],
                database=dictDB['projectName'],
                port=int(dictDB['port']),
                user=dictDB['user'],
                password=dictDB['pwd'])       
            conn.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
        except:
            print("DB connection has failed")
            if errorMsg:
                iface.messageBar().pushMessage("ERROR", "DB connection has failed! Propably wrong password or user name.", level=Qgis.Critical)
    return conn
    
def dbConnectPerName(dictDB,dbName,errorMsg):
    conn=""
    try:
        conn = psycopg2.connect(
            host=dictDB['host'],
            database=dbName,
            port=int(dictDB['port']),
            user=dictDB['user'],
            password=dictDB['pwd'])       
        conn.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
    except:
        print("DB connection has failed")
        if errorMsg:
            iface.messageBar().pushMessage("ERROR", "DB connection has failed! Propably wrong password or user name.", level=Qgis.Critical)
    return conn
    
def getAssettypeNames(cur,feature):
    sql="""SELECT assetgroup::text || '_' || assettype::text || '_' || assettype_name AS assettyp_names FROM {}_assettypes ORDER BY assetgroup,assettype;""".format(feature)
    cur.execute(sql)
    return [i['assettyp_names'] for i in cur.fetchall()]
    
def loadProjectNames(cur,dictDB):
    """load the project names into comboBox selectProject """
    print('Load project names')
    cur.execute('SELECT datname FROM pg_database WHERE datistemplate = false;')
    db_names =list(cur.fetchall())
    print(db_names)
    project_names=[]
    for db in db_names:
        conn=dbConnectPerName(dictDB,db['datname'],False)
        if conn:
            print(conn)
            cur = conn.cursor()
            cur.execute("""SELECT EXISTS (
                           SELECT * FROM information_schema.tables 
                           WHERE  table_schema = 'public'
                           AND    table_name   = 'customer_assettypes'
                           );""")
            if "True" in str(cur.fetchone()):
                project_names.append(db['datname'])
            conn.close()
    print(project_names)
    return project_names
        
def checkDBName(nameDb,cur,dictDB):
    """Check if the DB name already exists """
    projectNames=loadProjectNames(cur,dictDB)
    if nameDb not in projectNames:
        return True
    else:
        iface.messageBar().pushMessage("ERROR", "DB already exists!", level=Qgis.Critical)
        return False
        
def getFilteredDropDownItems(cur,dropdown):
    """dropdowns: [table,id,name,filter_column,filter_value]"""
    sql='SELECT {} AS key,{} AS name FROM public.{} WHERE {}={};'.format(dropdown[1],dropdown[2],dropdown[0],dropdown[3],dropdown[4])
    print(sql)
    cur.execute(sql) 
    dropdown_data = cur.fetchall()
    print(dropdown_data)
    dropdownItems=[str(i['key'])+':'+i['name'] for i in dropdown_data]
    return dropdownItems

def getFilteredNotInDropDownItems(cur,dropdowns):
    dropdownItems={}
    for id,version,table,column,name,filter in dropdowns:
        print(getFilteredNotInDropDownItems)
        filter="WHERE id NOT IN({}) ".format(','.join([str(i) for i in filter]))    
        sql='SELECT {} AS key,{} AS name FROM "{}".{} {};'.format(column,name,version,table,filter)
        print(sql)
        cur.execute(sql) 
        dropdown_data = cur.fetchall()
        dropdownItems[id]=[str(i['key'])+':'+i['name'] for i in dropdown_data]
    return dropdownItems
    
def getDropDownItems(cur,dropdowns):
    dropdownItems={}
    for id,version,table,column,name in dropdowns:         
        sql='SELECT {} AS key,{} AS name FROM "{}".{};'.format(column,name,version,table,column)
        print(sql)
        cur.execute(sql) 
        dropdown_data = cur.fetchall()
        dropdownItems[id]=[str(i['key'])+':'+i['name'] for i in dropdown_data]
    return dropdownItems
    
def getFilteredDropDownItemNames(cur,dropdowns):
    dropdownItems={}
    for id,version,table,name,filter in dropdowns:
        print(filter)
        if filter:
            filter="WHERE id IN({}) ".format(','.join([str(i) for i in filter]))
            sql='SELECT {} AS name FROM "{}".{} {}ORDER BY id;'.format(name,version,table,filter)
            print(sql)
            cur.execute(sql) 
            dropdown_data = cur.fetchall()
            dropdownItems[id]=[str(i['name']) for i in dropdown_data]
        else:
            dropdownItems[id]=[]
    return dropdownItems

def getFilteredNotInDropDownItemNames(cur,dropdowns):
    dropdownItems={}
    for id,version,table,name,filter in dropdowns:
        print(filter)
        if filter:
            filter="WHERE id NOT IN({}) ".format(','.join([str(i) for i in filter]))
            sql='SELECT {} AS name FROM "{}".{} {}ORDER BY id;'.format(name,version,table,filter)
            print(sql)
            cur.execute(sql) 
            dropdown_data = cur.fetchall()
            dropdownItems[id]=[str(i['name']) for i in dropdown_data]
        else:
            dropdownItems[id]=[]
    return dropdownItems
    
def getDropDownItemNames(cur,dropdowns):
    dropdownItems={}
    for id,version,table,name in dropdowns:         
        sql='SELECT {} AS name FROM "{}".{} ORDER BY id;'.format(name,version,table)
        print(sql)
        cur.execute(sql) 
        dropdown_data = cur.fetchall()
        dropdownItems[id]=[str(i['name']) for i in dropdown_data]
    return dropdownItems
    
def getConnValue(cur,bundle,sequence):
    """Sequence of connection_id"""
    sql="""SELECT b_t_conns.conn_bundle_type_id, b_t_conns.sequence, b_t_conns.conn_type_id, conn_t_conns.sequence, conns.temp,conns.p, conns.mdot,conns.type, b_t_conns.conn_type_id
	FROM connections conns, bundle_type_conns b_t_conns, connection_type_connections conn_t_conns
	WHERE b_t_conns.conn_bundle_type_id = {} AND conn_t_conns.sequence={} AND conn_t_conns.connection_id=conns.id AND b_t_conns.conn_type_id=conn_t_conns.connection_type_id
	ORDER BY b_t_conns.sequence, conn_t_conns.sequence;""".format(bundle, sequence)
    #print(sql)
    cur.execute(sql)
    return cur.fetchall()

def getPipeBundleTypesDB(cur):
    sql="""SELECT pipe_bundle_type_id,ARRAY_AGG (ARRAY[sequence::int,pipe_id::int,ambient::int] ORDER BY sequence) AS pipe
    FROM bundle_pipes 
    GROUP BY pipe_bundle_type_id 
    ORDER BY pipe_bundle_type_id ASC; """
    cur.execute(sql)
    return { bundle['pipe_bundle_type_id']: bundle['pipe'] for bundle in cur.fetchall()}

def getAssetgroupsInfo(feature,cur):
    sql="""SELECT id,assetgroup,id::text||':'||assetgroup::text AS name FROM public.{}_assetgroups;""".format(feature)
    cur.execute(sql)
    return cur.fetchall()   
    
def getAssettypesInfo(feature,assetgroup_id,cur):
    sql="""SELECT at.assettype, at.assettype_name, ag.id AS assetgroup,ag.assetgroup AS assetgroup_name, at.assettype::text||':'||at.assettype_name||'('||ag.assetgroup::text||')' AS name
    FROM {}_assettypes at, {}_assetgroups ag
    WHERE at.assetgroup=ag.id AND ag.id={}
    ORDER BY at.assettype; """.format(feature,feature,assetgroup_id)
    cur.execute(sql)
    return cur.fetchall()    
    
def getAssetgroups(type,cur):
    """ get all assetgroups of type """
    sql='SELECT id FROM public.{}_assetgroups;'.format(type)
    cur.execute(sql)
    return [str(i['id']) for i in cur.fetchall()]    
        
def getTableIds(cur,version,table,column):
    sql="""SELECT {} FROM "{}".{}""".format(column,version,table)
    cur.execute(sql)
    return cur.fetchall()
    
def clean_csv_value(value: Optional[Any]) -> str:
    if value is None:
        return r'\N'
    return str(value).replace('\n', '\\n')


class StringIteratorIO(io.TextIOBase):
    def __init__(self, iter: Iterator[str]):
        self._iter = iter
        self._buff = ''

    def readable(self) -> bool:
        return True

    def _read1(self, n: Optional[int] = None) -> str:
        while not self._buff:
            try:
                self._buff = next(self._iter)
            except StopIteration:
                break
        ret = self._buff[:n]
        self._buff = self._buff[len(ret):]
        return ret

    def read(self, n: Optional[int] = None) -> str:
        line = []
        if n is None or n < 0:
            while True:
                m = self._read1()
                if not m:
                    break
                line.append(m)
        else:
            while n > 0:
                m = self._read1(n)
                if not m:
                    break
                n -= len(m)
                line.append(m)
        return ''.join(line)
    
def getResultVars(cur,dictDB,feature,type):
    """type=='m' --> measurements; type=='s' --> simulation data"""
    if feature=='energy_plant':
        feature='energy'
        col=3
    else:
        col=2
    sql="""SELECT split_part(table_name,'_{}_',2) AS var
    FROM information_schema.tables 
    WHERE table_schema = '{}' AND split_part(table_name,'_',{})='{}' AND split_part(table_name,'_',1)='{}' AND NOT split_part(table_name,'_{}_',2) LIKE '%_vis';""".format(type,dictDB['versionName'],col,type,feature,type)
    print(sql)
    cur.execute(sql)
    return [var['var'] for var in cur.fetchall()]
    
def getTableAttr(cur,dictDB,feature):
    sql="""SELECT column_name 
    FROM information_schema.columns 
    WHERE table_name = '{}s' AND table_schema='{}';""".format(feature,dictDB['versionName'])
    print(sql)
    cur.execute(sql)
    return [attr['column_name'] for attr in cur.fetchall()]
