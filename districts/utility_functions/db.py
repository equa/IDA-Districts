from qgis.core import QgsApplication, QgsAuthMethodConfig

import psycopg2
from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT  
import psycopg2.extras
 
from qgis.utils import iface
from qgis.core import Qgis, QgsMessageLog
from typing import Iterator, Optional,Dict, Any
import io
import subprocess
import os
from pathlib import Path
import tempfile

from .files import *
from .utility import *

#from .dialog import *
#from .layer_visualization import *

def getNetworkVolume(cur,config,networks=None):
    sql="""SELECT sum(innerpipediameter * innerpipediameter*3.1415/4*ST_length(l.geom)) as volume_m3
	FROM "{}".lines l, bundle_pipes bp, pipes p
	WHERE bp.pipe_bundle_type_id=l.pipe_bundle_type_id AND p.id=bp.pipe_id{};""".format(config['versionName'],' AND network IN ({})'.format(','.join(networks)) if networks else '') # nosec B608
    cur.execute(sql)
    return float(cur.fetchone()['volume_m3'])  
    
def getNetworkLength(cur,config,networks=None):
    sql="""SELECT sum(ST_length(geom)) AS length FROM "{}".lines{};""".format(config['versionName'],' WHERE network IN ({})'.format(','.join(networks)) if networks else '') # nosec B608
    cur.execute(sql)
    return float(cur.fetchone()['length'])
    
def getBuildingsEra(cur,config):
    sql="""SELECT sum(ST_area(b.geom)) AS era
	FROM "{}".buildings b, "{}".customers c 
	WHERE ST_dWithIn(b.geom,c.geom,0.001);""".format(config['versionName'],config['versionName']) # nosec B608
    cur.execute(sql)
    return float(cur.fetchone()['era'])
    
def getPipeInfo(cur,config,networks=None):
    sql="""SELECT p.name,sum(ST_length(l.geom)) AS length, innerpipediameter,sum(p.costs*ST_length(l.geom)) as costs
	FROM "{}".lines l, bundle_pipes bp, pipes p
	WHERE l.pipe_bundle_type_id=bp.pipe_bundle_type_id AND bp.pipe_id=p.id {}
	GROUP BY bp.pipe_id,p.name,innerpipediameter
	ORDER BY innerpipediameter;""".format(config['versionName'],' AND network IN ({})'.format(','.join(networks)) if networks else '') # nosec B608
    #print(sql)
    cur.execute(sql)
    return cur.fetchall()
    
def getNetworks(cur,config):
    sql="""SELECT id AS network FROM "{}".network ORDER BY id;""".format(config['versionName']) # nosec B608
    cur.execute(sql)
    networks=[str(i['network']) for i in cur.fetchall()]
    return networks
    
def setDistrictsModelerVersion2DB(cur,config):
    getDistrictsModelerVersion(config)
    try:
        sql="""INSERT INTO db_info (id,version) VALUES(1,'{}');""".format(getDistrictsModelerVersion(config)) # nosec B608
        cur.execute(sql)  
    except:
        pass
            
def get_pgrouting_major_version(cur):
    """
    Returns the major version of pgRouting as an integer.
    Example: 3 for 3.4.0, 4 for 4.0.0
    """
    cur.execute("SELECT split_part(pgr_version(), '.', 1)::int AS version;") # nosec B608
    version = cur.fetchone()['version']
    return version
    
def getDBIds(column,table,cur):
    """ load the ids from DB table"""
    sql='SELECT {} AS id FROM public.{} GROUP BY {} ORDER BY {};'.format(column,table,column,column) # nosec B608
    #print(sql)
    cur.execute(sql)
    return list([id['id'] for id in cur.fetchall()])           
        
def delIfNotInDBIds(table,openFnArg,cur):
    """delete entries in subtable, if filter and not listed in DB table """
    if openFnArg:
        filter=openFnArg[3]
        if filter:
            ids=getDBIds('id',table,cur)
            #print(ids)
            if ids:
                ids=','.join([str(i) for i in ids])
                sql="DELETE FROM public.{} {} NOT IN ({})".format(openFnArg[0],filter[:-1],ids) # nosec B608
            else:
                sql="TRUNCATE public.{} CASCADE;".format(str(openFnArg[0])) # nosec B608
            #print(sql)
            cur.execute(sql)
  
  
def rowCountDB(table,filter,cur):
    """ Count the rows of table with filter"""
    sql="SELECT count(*) AS count FROM {} {};".format(table,filter) # nosec B608
    cur.execute(sql)
    return cur.fetchone()['count']     

def get_folder_names(directory):
    return [p.name for p in Path(directory).iterdir() if p.is_dir()]

def loadProjectNames(config):
    """load the project names into comboBox selectProject """
    return get_folder_names(config['pathProjects'])
        
def updateProjectNamesList(dlg,config):
    projectNames=loadProjectNames(config)
    dlg.selectProject.blockSignals(True)
    dlg.selectProject.clear()
    dlg.selectProject.addItems(projectNames)
    if config['projectName']:
        dlg.selectProject.setCurrentText(config['projectName'])
    dlg.selectProject.blockSignals(False)
    return projectNames
      
def connectDBPostgres(config,dlg):
    #print('--connectDBPostgres--')
    conn_postgres=dbConnectPerName(config,"postgres",True)
    #print(conn_postgres)
    projectNames=None
    if conn_postgres:
        cur_postgres=conn_postgres.cursor(cursor_factory = psycopg2.extras.RealDictCursor)
        projectNames=updateProjectNamesList(dlg,config)
        return [conn_postgres,cur_postgres,projectNames]
    return [False,False,projectNames]
                
def dropDBTriggers(cur,config,lastLoad=False):
    sql=''
    no_trigger_table=['invoked_sf']
    if config['lastVersionName'] if lastLoad else config['versionName']:
        for table in getDBTableNames(cur,config):
            if table not in no_trigger_table:
                sql+="""DROP TRIGGER IF EXISTS my_insert_trigger ON "{}".{};\n""".format(config['lastVersionName'] if lastLoad else config['versionName'],table) # nosec B608
                sql+="""DROP TRIGGER IF EXISTS my_delete_trigger ON "{}".{};\n""".format(config['lastVersionName'] if lastLoad else config['versionName'],table) # nosec B608
                sql+="""DROP TRIGGER IF EXISTS my_truncate_trigger ON "{}".{};\n""".format(config['lastVersionName'] if lastLoad else config['versionName'],table) # nosec B608
                sql+="""DROP TRIGGER IF EXISTS column_update_trigger ON "{}".{};\n""".format(config['lastVersionName'] if lastLoad else config['versionName'],table) # nosec B608
        if sql:
            #print(sql)
            cur.execute(sql)

def insertDBTriggers(cur,config):
    sql=''
    no_trigger_table=['invoked_sf']
    if config['versionName']:
        for table in getDBTableNames(cur,config):
            if table not in no_trigger_table:
                sql+="""CREATE TRIGGER my_insert_trigger
AFTER INSERT ON "{}".{}
FOR EACH ROW
EXECUTE FUNCTION my_trigger_insert_function();\n""".format(config['versionName'],table) # nosec B608
                sql+="""CREATE TRIGGER my_delete_trigger
AFTER DELETE ON "{}".{}
FOR EACH ROW
EXECUTE FUNCTION my_trigger_delete_function();\n""".format(config['versionName'],table) # nosec B608
                sql+="""CREATE TRIGGER my_truncate_trigger
AFTER TRUNCATE ON "{}".{}
FOR EACH STATEMENT
EXECUTE FUNCTION my_trigger_truncate_function();\n""".format(config['versionName'],table) # nosec B608
                sql+="""CREATE TRIGGER column_update_trigger
AFTER UPDATE ON "{}".{}
FOR EACH ROW
EXECUTE FUNCTION my_trigger_update_function();\n""".format(config['versionName'],table) # nosec B608

        if sql:
            #print(sql)
            cur.execute(sql)
    
def getDBTableNames(cur,config):
    sql="""SELECT table_name
FROM information_schema.tables
WHERE table_schema = '{}'
    AND table_type = 'BASE TABLE';""".format(config['versionName']) # nosec B608
    cur.execute(sql)
    return [table['table_name'] for table in cur.fetchall()]
            
def getMaxIdAcrossSchemas(config,cur,table_name):
    sql="""SELECT * FROM get_highest_id_across_schemas('{}', (SELECT array_agg(name) FROM get_version_tree('{}'))) AS max_id;""".format(table_name,config['versionName']) # nosec B608
    cur.execute(sql)
    return cur.fetchone()['max_id']
    
def dbColumnDataType(cur,version,table,col):
    sql="""SELECT column_name, data_type 
    FROM information_schema.columns 
    WHERE table_schema = '{}' 
    AND table_name = '{}' 
    AND column_name = '{}';""".format(version,table,col) # nosec B608
    cur.execute(sql)
    return cur.fetchone()['data_type']
    
def dbColumnIsNumeric(cur,version,table,col):
    if dbColumnDataType(cur,version,table,col) in ['integer', 'numeric', 'decimal', 'double precision', 'real', 'smallint']:
        return True
    else:
        return False
    
def copy_schema(baseName,new_versionName,config,cur,plugin_dir,username,password):
    """copy schema"""
    env = os.environ.copy()
    env["PGPASSWORD"] = password
    
    schema = sanitize_pg_identifier(baseName)

    cmd = [
        f"{config['pathPostgresql']}bin\\pg_dump",
        "-U", username,
        "-h", config['host'],
        "-p", str(config['port']),
        "-d", config['projectName'],
        "-n", schema
    ]

    with open(os.path.join(tempfile.gettempdir(), "dump_schema.sql"), "w", encoding="utf-8") as f:
        subprocess.call(cmd, env=env, stdout=f)
    
    sql = 'ALTER SCHEMA "'+baseName+'" RENAME TO "'+new_versionName+'" ;' # nosec B608
    #print(sql)
    cur.execute(sql)           
    
    sql="DROP EVENT TRIGGER IF EXISTS prevent_column_alter;"
    #print(sql)
    cur.execute(sql)
    
    cmd = [
        f"{config['pathPostgresql']}bin\\psql",
        "-d", config['projectName'],
        "-h", config['host'],
        "-p", str(config['port']),
        "-U", username,
        "-f", f"{tempfile.gettempdir()}\\dump_schema.sql"
    ]

    subprocess.call(cmd, env=env)
    
    sql="""CREATE EVENT TRIGGER prevent_column_alter
ON ddl_command_start  -- Triggered before the DDL command is executed
WHEN TAG IN ('ALTER TABLE')
EXECUTE FUNCTION restrict_column_alterations();"""
    #print(sql)
    cur.execute(sql)
        
def setSeqIdToMax(seq,table,col,cur):
    sql="""SELECT setval('{}', (SELECT COALESCE(MAX({}), 0) FROM {}) + 1);""".format(seq,col,table) # nosec B608
    #print(sql)
    cur.execute(sql)

def getTimeDiff(cur,config,table,col,order_col):
    sql="""SELECT EXTRACT(EPOCH FROM (next_time.time-start_time.time)) AS diff 
    FROM (SELECT {} AS time FROM "{}".{} ORDER BY {},{}{} LIMIT 1) start_time,
        (SELECT {}  AS time FROM "{}".{} ORDER BY {},{}{} LIMIT 1 OFFSET 1) next_time;""".format(col,config['versionName'],table,order_col,'segment,' if 'line_' in table and col in ['p','temp'] else '',col,col,config['versionName'],table,order_col,'segment,' if 'line_' in table and col in ['p','temp'] else '',col) # nosec B608
    #print(sql)
    cur.execute(sql)
    return cur.fetchone()['diff']
    
def getAvergageByMode(mode,cur,config,table):
    """return value in seconds"""
    if mode=='Hourly average':
        return 'hour'
    elif mode=='Daily average':
        return 'day'
    elif mode=='Monthly average':
        return 'month'
    elif mode=='Values':
        return getTimeDiff(cur,config,table,'time','fid')/3600
        
def featureCount(cur,config,network,type):
    sql="""SELECT count(*) FROM "{}".{}s WHERE network=array[{}];""".format(config['versionName'],type,network) # nosec B608
    cur.execute(sql)
    return cur.fetchone()['count']

def streetsCount(cur,config):
    sql="""SELECT count(*) FROM "{}".streets;""".format(config['versionName'])# nosec B608
    cur.execute(sql)
    return cur.fetchone()['count']

def getDecoupledFeatureCompPerFeature(feature,cur,config):
    sql="""SELECT f_dec.comp_name
    FROM "{}".{}s f, "{}".feature_decoupling f_dec
    WHERE f.id={} AND f.template=f_dec.template AND f_dec.type='{}';""".format(config['versionName'],feature['feature'],config['versionName'],feature['id'],feature['feature']) # nosec B608
    #print(sql)
    cur.execute(sql)
    return [i['comp_name'] for i in cur.fetchall()]
    
def getDecoupledFeatureCompPerTemplate(config,cur,template):
    sql="""SELECT f_dec.comp_name
    FROM "{}".feature_decoupling f_dec
    WHERE {}=f_dec.template AND f_dec.type='customer';""".format(config['versionName'],template) # nosec B608
    #print(sql)
    cur.execute(sql)
    return [i['comp_name'] for i in cur.fetchall()]

def getUsedDecoupledFeatureTemplates(usedFeatureTemplates,cur,config,submodel,cosims):
    templates=[]
    for cosim in cosims:
        sql="""(SELECT 'customer' AS feature,f.template, CASE WHEN s_m.submodel::int={} THEN TRUE ELSE FALSE END AS network_side
    FROM "{}".customers f, "{}".lines l,"{}".submodels s_m
    WHERE ({} = f.submodel AND {} = ANY (l.submodel) OR {} = f.submodel AND {} = ANY (l.submodel)) AND ST_DWithin(l.geom,s_m.geom,0.001)
    GROUP BY feature,f.template, network_side)
UNION 
(SELECT 'energy_plant' AS feature,f.template, CASE WHEN s_m.submodel::int={} THEN TRUE ELSE FALSE END AS network_side
    FROM "{}".energy_plants f, "{}".lines l,"{}".submodels s_m
    WHERE ({} = f.submodel AND {} = ANY (l.submodel) OR {} = f.submodel AND {} = ANY (l.submodel)) AND ST_DWithin(l.geom,s_m.geom,0.001)
    GROUP BY feature,f.template, network_side)
ORDER BY feature,template;""".format(submodel,config['versionName'],config['versionName'],config['versionName'],cosim,submodel,submodel,cosim,# nosec B608
            submodel,config['versionName'],config['versionName'],config['versionName'],cosim,submodel,submodel,cosim) # nosec B608
        #print(sql)
        cur.execute(sql)
        decoupled_templates=[{'feature': i['feature'], 'template': i['template'], 'template_name':j['template_name'], 'network_side': i['network_side']} 
            for i in cur.fetchall() for j in usedFeatureTemplates if i['feature']==j['feature'] and i['template']==j['template']]
        templates.extend([at for at in decoupled_templates if at not in templates])
    #print(templates)
    return templates
    
def getFeatureDecIds(config,cur,submodel,cosims):
    fids=[]
    for cosim in cosims:
        sql="""(SELECT 'customer' AS feature, f.template, f.id, f.submodel, s_m.submodel AS cosim, CASE WHEN s_m.submodel::int={} THEN TRUE ELSE FALSE END AS network_side
    FROM "{}".customers f, "{}".customer_connections f_conns, "{}".lines l, "{}".submodels s_m
    WHERE ST_DWithin(l.geom,s_m.geom,0.001) AND f.id=f_conns.cid AND l.id=f_conns.lid AND ({} = f.submodel AND {} = ANY (l.submodel) OR {} = f.submodel AND {} = ANY (l.submodel)))
UNION 
(SELECT 'energy_plant' AS feature, f.template, f.id, f.submodel, s_m.submodel AS cosim, CASE WHEN s_m.submodel::int={} THEN TRUE ELSE FALSE END AS network_side
    FROM "{}".energy_plants f, "{}".energy_plant_connections f_conns, "{}".lines l, "{}".submodels s_m
    WHERE ST_DWithin(l.geom,s_m.geom,0.001) AND f.id=f_conns.epid AND l.id=f_conns.lid AND ({} = f.submodel AND {} = ANY (l.submodel) OR {} = f.submodel AND {} = ANY (l.submodel)))
ORDER BY feature,id;""".format(submodel,config['versionName'],config['versionName'],config['versionName'],config['versionName'],cosim,submodel,submodel,cosim,# nosec B608
            submodel,config['versionName'],config['versionName'],config['versionName'],config['versionName'],cosim,submodel,submodel,cosim) # nosec B608
        #print(sql)
        
        cur.execute(sql)
        fids.extend([i for i in cur.fetchall() if i not in fids])
    return fids

def getFeatureIdFromName(config,cur,feature):
    sql="""SELECT id FROM type WHERE replace(lower(name),' ','_')='{}';""".format(feature) # nosec B608
    #print(sql)
    cur.execute(sql)
    return cur.fetchone()['id']
    
def getUsedNetworks(cur,config):
    sql="""(
    SELECT network FROM "{}".lines GROUP BY network
    UNION
    SELECT unnest(network) AS network FROM "{}".customers GROUP BY network
    UNION
    SELECT unnest(network) AS network FROM "{}".energy_plants GROUP BY network
)
ORDER BY network;""".format(config['versionName'],config['versionName'],config['versionName']) # nosec B608
    cur.execute(sql)
    networks=[str(i['network']) for i in cur.fetchall()]
    return networks
    
def getLineNetworks(cur,config):
    sql="""SELECT network FROM "{}".lines GROUP BY network ORDER BY network;""".format(config['versionName']) # nosec B608
    cur.execute(sql)
    networks=[i['network'] for i in cur.fetchall()]
    return networks

def getLineSubmodels(cur,config):
    sql="""SELECT unnest(submodel) as submodels FROM "{}".lines GROUP BY submodels ORDER BY submodels;""".format(config['versionName']) # nosec B608
    cur.execute(sql)
    submodels=[i['submodels'] for i in cur.fetchall()]
    return submodels
    
def getFeatureSubmodels(cur,config,type):
    sql="""SELECT submodel FROM "{}".{}s GROUP BY submodel ORDER BY submodel;""".format(config['versionName'],type) # nosec B608
    cur.execute(sql)
    submodels=[i['submodel'] for i in cur.fetchall()]
    return submodels

def getUsedFeatureTemplates(cur,config):
    sql="""(SELECT 'customer' AS feature, f.template, f_t.template_name
    FROM "{}".customers f,customer_templates f_t 
    WHERE f.template=f_t.template
    GROUP BY f.template,f_t.template_name)
UNION
(SELECT 'energy_plant' AS feature,f.template,f_t.template_name
    FROM "{}".energy_plants f, energy_plant_templates f_t
     WHERE f.template=f_t.template
    GROUP BY f.template,f_t.template_name)
ORDER BY feature,template;""".format(config['versionName'],config['versionName']) # nosec B608
    cur.execute(sql)
    return cur.fetchall()
    
def getUsedFilteredFeatureTemplates(feature_type,cur,config):
    sql="""SELECT f.template, f_t.template_name
    FROM "{}".{}s f,{}_templates f_t 
    WHERE f.template=f_t.template
    GROUP BY f.template,f_t.template_name;""".format(config['versionName'],feature_type,feature_type,config['versionName']) # nosec B608
    cur.execute(sql)
    return cur.fetchall()
    
def getUsedSubmodels(cur,config):
    sql="""(
    SELECT unnest(submodel) AS submodel FROM "{}".lines GROUP BY submodel
    UNION
    SELECT submodel FROM "{}".customers GROUP BY submodel
    UNION
    SELECT submodel FROM "{}".energy_plants GROUP BY submodel
)
ORDER BY submodel;""".format(config['versionName'],config['versionName'],config['versionName']) # nosec B608
    cur.execute(sql)
    submodels=[str(i['submodel']) for i in cur.fetchall()]
    return submodels
    
def getUsedNetworkSubmodels(cur,config):
    sql="""(
    SELECT unnest(submodel) AS submodel FROM "{}".lines GROUP BY submodel
    UNION
    SELECT c.submodel
        FROM "{}".customers c, customer_templates c_t
        WHERE c_t.template=c.template AND c_t.conn_bundle_type NOT IN 
            (SELECT b_t_conns.conn_bundle_type_id
                FROM connections c, bundle_type_conns b_t_conns, connection_type_connections conn_t_conns
                WHERE b_t_conns.conn_type_id=conn_t_conns.connection_type_id AND conn_t_conns.connection_id=c.id AND c.type IN (3,4,5,6,7,8,9,10)
                GROUP BY b_t_conns.conn_bundle_type_id)
        GROUP BY c.submodel,conn_bundle_type
    UNION
    SELECT submodel FROM "{}".energy_plants GROUP BY submodel
)
ORDER BY submodel;""".format(config['versionName'],config['versionName'],config['versionName']) # nosec B608
    cur.execute(sql)
    submodels=[str(i['submodel']) for i in cur.fetchall()]
    return submodels

def getTemplateNamesFilteredByCustomerIds(cur,config,cids):
    sql="""SELECT c_t.template::text||'_'||c_t.template_name  AS template_name
    FROM {}.customers c, customer_templates c_t
    WHERE c.id IN ({}) AND c.template=c_t.template
    GROUP BY c_t.template::text||'_'||c_t.template_name;""".format(config['versionName'],','.join([str(i) for i in cids])) # nosec B608
    cur.execute(sql)
    template_names=[str(i['template_name']) for i in cur.fetchall()]
    return template_names

def getPlantIds(cur,config,network=None):
    sql="""SELECT id FROM {}.energy_plants{};""".format(config['versionName'],'' if network==None else ' WHERE {} = ANY (network)'.format(network)) # nosec B608
    cur.execute(sql)
    ids=[str(i['id']) for i in cur.fetchall()]
    return ids
    
def getLineIds(cur,config,network=None):
    sql="""SELECT id FROM {}.lines{};""".format(config['versionName'],'' if network==None else ' WHERE network IN ({})'.format(','.join(network))) # nosec B608
    cur.execute(sql)
    ids=[str(i['id']) for i in cur.fetchall()]
    return ids
 
def getUsedBuildingSubmodels(cur,config):
    sql="""SELECT submodel FROM "{}".buildings WHERE submodel IS NOT NULL GROUP BY submodel ORDER BY submodel;""".format(config['versionName']) # nosec B608
    cur.execute(sql)
    submodels=[str(i['submodel']) for i in cur.fetchall()]
    return submodels
    
def getFeatureIdsPerSubmodelAndTypename(submodel,type,cur,config):
    sql="""SELECT id FROM "{}".{}s WHERE submodel={};""".format(config['versionName'],submodel) # nosec B608
    cur.execute(sql)
    return [id['id'] for id in cur.fetchall()]

def getSubmodelPerFeatureIdTypename(id,feature,cur,config):
    sql="""SELECT submodel FROM "{}".{}s WHERE id={};""".format(config['versionName'],feature.replace(" ","_"),id) # nosec B608
    cur.execute(sql)
    return cur.fetchone()
    
def getDrawnSubmodels(cur,config):
    sql="""SELECT id FROM "{}".submodels;""".format(config['versionName']) # nosec B608
    cur.execute(sql)
    submodels=[i['id'] for i in cur.fetchall()]
    if len(submodels)==0:
        iface.messageBar().pushMessage("Info", "No simulation model has been build yet!", level=Qgis.Info)
        return False
    else:
        return submodels
        
def getSupervisorySubmodel(cur,config):
    sql="""SELECT submodel FROM supervisory_ctrl;"""
    cur.execute(sql)
    return cur.fetchone()
            
def getNetworkSubmodels(cur,config,networks):
    """Get submodels of a list of networks based on lines"""
    sql="""SELECT unnest(submodel) AS submodel FROM "{}".lines WHERE network IN ({}) GROUP BY submodel ORDER BY submodel;""".format(config['versionName'], ','.join([i for i in networks])) # nosec B608
    #print(sql)
    cur.execute(sql)
    submodels=[str(i['submodel']) for i in cur.fetchall()]
    return submodels
      
def checkTableNameExists(cur,config,table):
    sql="""SELECT EXISTS (
    SELECT FROM information_schema.tables 
    WHERE  table_schema = '{}'
    AND    table_name   = '{}'
    );""".format(config['versionName'],table)# nosec B608
    cur.execute(sql)
    return cur.fetchone()['exists']
   
def getProjectVersionNames(cur):
    sql="SELECT nspname FROM pg_catalog.pg_namespace WHERE nspname NOT IN ('topology','temp','streets_help_topo','public','pg_toast','pg_catalog','information_schema');"# nosec B608
    cur.execute(sql)
    versionNames=[]
    for version in cur.fetchall():
        versionNames.append(version['nspname'])
    return versionNames
    
def getClimateData(cur,config,errorMsg):
    """ get climate data from DB"""
    #print('get climate data')
    if checkDBVersionConnected(config,errorMsg):
        sql='SELECT name, longitude, latitude,file_name AS filename ,timezone,height FROM "{}".climate;'.format(config['versionName']) # nosec B608
        #print(sql)
        cur.execute(sql)
        return cur.fetchone()

def getMaxTableValue(cur,config,table,colmn):
    sql="""SELECT max("{}") AS value FROM "{}".{};""".format(colmn,config['versionName'],table) # nosec B608
    cur.execute(sql)
    return cur.fetchone()['value']
    
def getMinTableValue(cur,config,table,colmn):
    sql="""SELECT min("{}") AS value FROM "{}".{};""".format(colmn,config['versionName'],table) # nosec B608
    cur.execute(sql)
    return cur.fetchone()['value']
    
def getMinTimeTableValue(mode,cur,config,table,colmn,starttime,endtime):
    if mode=='Min':
        return getMinMinTimeValue(cur,config,table,colmn,starttime,endtime)
    elif mode=='Max':
        return getMinMaxTimeValue(cur,config,table,colmn,starttime,endtime)
    elif mode=='Average':
        return getMinValueAvgTimeValue(cur,config,table,colmn,starttime,endtime)
    elif mode=='Sum':
        return getMinSumTimeValue(cur,config,table,colmn,starttime,endtime)
    elif mode=='Last value':
        return getMinLastTimeValue(cur,config,table,colmn,endtime)
    elif mode=='First value':
        return getMinFirstTimeValue(cur,config,table,colmn,starttime)
    elif mode=='Hourly average':
        return getMinAvgTimeValue('hour',cur,config,table,colmn,starttime,endtime)
    elif mode=='Values':
        return getMinMinTimeValue(cur,config,table,colmn,starttime,endtime)
    elif mode=='Daily average':
        return getMinAvgTimeValue('day',cur,config,table,colmn,starttime,endtime)
    elif mode=='Monthly average':
        return getMinAvgTimeValue('month',cur,config,table,colmn,starttime,endtime)
        
def getMaxTimeTableValue(mode,cur,config,table,colmn,starttime,endtime):
    if mode=='Min':
        return getMaxMinTimeValue(cur,config,table,colmn,starttime,endtime)
    elif mode=='Max':
        return getMaxMaxTimeValue(cur,config,table,colmn,starttime,endtime)
    elif mode=='Average':
        return getMaxValueAvgTimeValue(cur,config,table,colmn,starttime,endtime)
    elif mode=='Sum':
        return getMaxSumTimeValue(cur,config,table,colmn,starttime,endtime)
    elif mode=='Last value':
        return getMaxLastTimeValue(cur,config,table,colmn,endtime)
    elif mode=='First value':
        return getMaxFirstTimeValue(cur,config,table,colmn,starttime)
    elif mode=='Values':
        return getMaxMaxTimeValue(cur,config,table,colmn,starttime,endtime)
    elif mode=='Hourly average':
        return getMaxAvgTimeValue('hour',cur,config,table,colmn,starttime,endtime)
    elif mode=='Daily average':
        return getMaxAvgTimeValue('day',cur,config,table,colmn,starttime,endtime)
    elif mode=='Monthly average':
        return getMaxAvgTimeValue('month',cur,config,table,colmn,starttime,endtime)
        
def getMinMinTimeValue(cur,config,table,colmn,starttime,endtime):
    sql="""WITH sub AS(
    SELECT fid,min("${}") AS value FROM "{}".{} WHERE time>='{}' AND time <='{}' GROUP BY fid{}
)
SELECT min(value) AS value FROM sub;""".format(colmn,config['versionName'],table,starttime,endtime,', segment' if 'line_' in table and colmn in ['p','temp'] else '') # nosec B608
    cur.execute(sql)
    return cur.fetchone()['value']

def getMinMaxTimeValue(cur,config,table,colmn,starttime,endtime):
    sql="""WITH sub AS(
    SELECT fid,max("${}") AS value FROM "{}".{} WHERE time>='{}' AND time <='{}' GROUP BY fid{}
)
SELECT min(value) AS value FROM sub;""".format(colmn,config['versionName'],table,starttime,endtime,', segment' if 'line_' in table and colmn in ['p','temp'] else '') # nosec B608
    cur.execute(sql)
    return cur.fetchone()['value']
    
def getMinValueAvgTimeValue(cur,config,table,colmn,starttime,endtime):
    sql="""WITH sub AS(
    SELECT fid,avg("${}") AS value FROM "{}".{} WHERE time>='{}' AND time <='{}' GROUP BY fid{}
)
SELECT min(value) AS value FROM sub;""".format(colmn,config['versionName'],table,starttime,endtime,', segment' if 'line_' in table and colmn in ['p','temp'] else '') # nosec B608
    cur.execute(sql)
    return cur.fetchone()['value']
    
def getMinSumTimeValue(cur,config,table,colmn,starttime,endtime):
    sql="""WITH sub AS(
    SELECT fid,sum("${}") AS value FROM "{}".{} WHERE time>='{}' AND time <='{}' GROUP BY fid{}
)
SELECT min(value) AS value FROM sub;""".format(colmn,config['versionName'],table,starttime,endtime,', segment' if 'line_' in table and colmn in ['p','temp'] else '') # nosec B608
    cur.execute(sql)
    return cur.fetchone()['value']
    
def getMinLastTimeValue(cur,config,table,colmn,endtime):
    sql="""WITH sub AS(
    SELECT DISTINCT ON (fid) 
        fid,"${}" AS value
    FROM "{}".{}
    WHERE time = '{}'
    ORDER BY fid,time DESC
)
SELECT min(value) AS value FROM sub;""".format(colmn,config['versionName'],table,endtime) # nosec B608
    cur.execute(sql)
    return cur.fetchone()['value']
    
def getMinFirstTimeValue(cur,config,table,colmn,starttime):
    sql="""WITH sub AS(
    SELECT DISTINCT ON (fid) 
        fid,"${}" AS value
    FROM "{}".{}
    WHERE time = '{}'
    ORDER BY fid,time ASC
)
SELECT min(value) AS value FROM sub;""".format(colmn,config['versionName'],table,starttime) # nosec B608
    cur.execute(sql)
    return cur.fetchone()['value']
    
def getMinAvgTimeValue(mode,cur,config,table,colmn,starttime,endtime):
    sql="""WITH sub AS(
    SELECT fid,date_trunc('{}', time) AS time, avg("${}") AS value
        FROM "{}".{}
        WHERE time BETWEEN '{}' AND '{}'
        GROUP BY date_trunc('{}', time),fid{}
        ORDER BY date_trunc('{}', time), fid
)
SELECT min(value) AS value FROM sub;""".format(mode,colmn,config['versionName'],table,starttime,endtime,mode,', segment' if 'line_' in table and colmn in ['p','temp'] else '',mode) # nosec B608
    #print(sql)
    cur.execute(sql)
    return cur.fetchone()['value']
    
def getMaxMinTimeValue(cur,config,table,colmn,starttime,endtime):
    sql="""WITH sub AS(
    SELECT fid,min("${}") AS value FROM "{}".{} WHERE time>='{}' AND time <='{}' GROUP BY fid{}
)
SELECT max(value) AS value FROM sub;""".format(colmn,config['versionName'],table,starttime,endtime,', segment' if 'line_' in table and colmn in ['p','temp'] else '') # nosec B608
    cur.execute(sql)
    return cur.fetchone()['value']

def getMaxMaxTimeValue(cur,config,table,colmn,starttime,endtime):
    sql="""WITH sub AS(
    SELECT fid,max("${}") AS value FROM "{}".{} WHERE time>='{}' AND time <='{}' GROUP BY fid{}
)
SELECT max(value) AS value FROM sub;""".format(colmn,config['versionName'],table,starttime,endtime,', segment' if 'line_' in table and colmn in ['p','temp'] else '') # nosec B608
    cur.execute(sql)
    return cur.fetchone()['value']
    
def getMaxValueAvgTimeValue(cur,config,table,colmn,starttime,endtime):
    sql="""WITH sub AS(
    SELECT fid,avg("${}") AS value FROM "{}".{} WHERE time>='{}' AND time <='{}' GROUP BY fid{}
)
SELECT max(value) AS value FROM sub;""".format(colmn,config['versionName'],table,starttime,endtime,', segment' if 'line_' in table and colmn in ['p','temp'] else '') # nosec B608
    cur.execute(sql)
    return cur.fetchone()['value']
    
def getMaxSumTimeValue(cur,config,table,colmn,starttime,endtime):
    sql="""WITH sub AS(
    SELECT fid,sum("${}") AS value FROM "{}".{} WHERE time>='{}' AND time <='{}' GROUP BY fid{}
)
SELECT max(value) AS value FROM sub;""".format(colmn,config['versionName'],table,starttime,endtime,', segment' if 'line_' in table and colmn in ['p','temp'] else '') # nosec B608
    cur.execute(sql)
    return cur.fetchone()['value']
    
def getMaxLastTimeValue(cur,config,table,colmn,endtime):
    sql="""WITH sub AS(
    SELECT DISTINCT ON (fid) 
        fid,"${}" AS value
    FROM "{}".{}
    WHERE time = '{}'
    ORDER BY fid,time DESC
)
SELECT max(value) AS value FROM sub;""".format(colmn,config['versionName'],table,endtime) # nosec B608
    cur.execute(sql)
    return cur.fetchone()['value']
    
def getMaxFirstTimeValue(cur,config,table,colmn,starttime):
    sql="""WITH sub AS(
    SELECT DISTINCT ON (fid) 
        fid,"${}" AS value
    FROM "{}".{}
    WHERE time = '{}'
    ORDER BY fid,time ASC
)
SELECT max(value) AS value FROM sub;""".format(colmn,config['versionName'],table,starttime) # nosec B608
    cur.execute(sql)
    return cur.fetchone()['value']

def getMaxAvgTimeValue(mode,cur,config,table,colmn,starttime,endtime):
    sql="""WITH sub AS(
    SELECT fid,date_trunc('{}', time) AS time, avg("${}") AS value
        FROM "{}".{}
        WHERE time BETWEEN '{}' AND '{}'
        GROUP BY date_trunc('{}', time),fid{}
        ORDER BY date_trunc('{}', time), fid
)
SELECT max(value) AS value FROM sub;""".format(mode,colmn,config['versionName'],table,starttime,endtime,mode,', segment' if 'line_' in table and colmn in ['p','temp'] else '',mode) # nosec B608
    #print(sql)
    cur.execute(sql)
    return cur.fetchone()['value']
    
def getMaxId(cur,table_name):
    """return highest connections id"""
    sql="SELECT max(id) AS max FROM public.{};".format(table_name) # nosec B608
    cur.execute(sql)
    id=cur.fetchone()
    if id['max']!=None:
        return id['max']
    else:
        return 0
        
def getMaxIdSchema(cur,table_name,schema):
    """return highest connections id"""
    sql="""SELECT max(id) AS max_id FROM "{}".{};""".format(schema,table_name) # nosec B608
    cur.execute(sql)
    id=cur.fetchone()
    if id['max_id']!=None:
        return id['max_id']
    else:
        return 0
        
def checkDBVersionConnected(config,errorMsg):
    """ Check if connected to DB version"""
    #print('check version connection')
    if config['versionName']:
        #print('connected to version!')
        return True
    else:
        #print('not connected to version!')
        if errorMsg:
            iface.messageBar().pushMessage("WARNING", tr('@default','no_db_connection'), level=Qgis.Warning)
        return False
        
def dbConnect(config,errorMsg):
    conn=None     
    try:
        auth_cfg = QgsAuthMethodConfig()
        QgsApplication.authManager().loadAuthenticationConfig(config["auth_id"], auth_cfg, True)
        conn = psycopg2.connect(
            host=config['host'],
            database=config['projectName'],
            port=int(config['port']),
            user=auth_cfg.config("username"),
            password=auth_cfg.config("password"),
            connect_timeout=5)       
        conn.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
    except:
        #print("DB connection has failed")
        if errorMsg:
            iface.messageBar().pushMessage("ERROR", "DB connection has failed! Propably wrong password, user name or project does not exists!", level=Qgis.Critical)
    return conn
    
def dbConnectProvidePwdUser(config,signals_error,pwd,user):
    conn=None      
    try:
        conn = psycopg2.connect(
            host=config['host'],
            database=config['projectName'],
            port=int(config['port']),
            user=user,
            password=pwd,
            connect_timeout=1)       
        conn.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
    except Exception as e:
        #print("DB connection has failed:",e)
        if signals_error:
            signals_error.emit(str(e))
    return conn
    
def dbConnectPerName(config,dbName,errorMsg):
    conn=""
    try:
        auth_cfg = QgsAuthMethodConfig()
        QgsApplication.authManager().loadAuthenticationConfig(config["auth_id"], auth_cfg, True)
        conn = psycopg2.connect(
            host=config['host'],
            database=dbName,
            port=int(config['port']),
            user=auth_cfg.config("username"),
            password=auth_cfg.config("password"),
            connect_timeout=1)       
        conn.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
    except:
        #print("DB connection has failed")
        if errorMsg:
            iface.messageBar().pushMessage("ERROR", "DB connection has failed! Propably wrong password or user name.", level=Qgis.Critical)
    return conn
    
def getTemplateNames(cur,feature,seperator=':'):
    sql="""SELECT template::text || '{}' || template_name AS template_names FROM {}_templates ORDER BY template;""".format(seperator,feature) # nosec B608
    cur.execute(sql)
    return [i['template_names'] for i in cur.fetchall()]
    
def getLineTypeNames(cur):
    sql="""SELECT type::text || ':' || type_name AS type_names FROM line_types ORDER BY type;"""
    cur.execute(sql)
    return [i['type_names'] for i in cur.fetchall()] 
    
def getPipeBundleNames(cur):
    sql="""SELECT id::text || ':' ||description AS pipe_bundle_names FROM pipe_bundle_types ORDER BY id; """
    cur.execute(sql)
    return [i['pipe_bundle_names'] for i in cur.fetchall()]
    
def getTemplateName(cur,template_name,template_id):
    sql="""SELECT template::text || '_' || template_name AS template_names FROM {} WHERE template={} ORDER BY template;""".format(template_name,template_id) # nosec B608
    cur.execute(sql)
    return [i['template_names'] for i in cur.fetchall()]
    
def getTemplateNameByTemplateId(cur,template_id,feature_type):
    sql="""SELECT template_name FROM {}_templates WHERE template={};""".format(feature_type,template_id) # nosec B608
    cur.execute(sql)
    try:
        return cur.fetchone()['template_name']
    except:
        return ''
    
def loadProjectNamesCheckDistricts(cur,config):
    """load the project names into comboBox selectProject """
    #print('--loadProjectNames--')
    project_names=[]
    if cur:
        cur.execute('SELECT datname FROM pg_database WHERE datistemplate = false;')
        db_names =list(cur.fetchall())
        #print(db_names)
        for db in db_names:
            conn=dbConnectPerName(config,db['datname'],False)
            if conn:
                #print(conn)
                cur = conn.cursor()
                cur.execute("""SELECT EXISTS (
                               SELECT * FROM information_schema.tables 
                               WHERE  table_schema = 'public'
                               AND    table_name   = 'customer_templates'
                               );""")
                if "True" in str(cur.fetchone()):
                    project_names.append(db['datname'])
                conn.close()
        #print(project_names)
    return project_names
        
def checkDBName(nameDb,projectNames):
    """Check if the DB name already exists """
    if nameDb not in projectNames:
        return True
    else:
        iface.messageBar().pushMessage("ERROR", "DB already exists!", level=Qgis.Critical)
        return False
        
def getFilteredDropDownItems(cur,dropdown):
    """dropdowns: [table,id,name,filter_column,filter_value]"""
    sql='SELECT {} AS key,{} AS name FROM public.{} WHERE {}={};'.format(dropdown[1],dropdown[2],dropdown[0],dropdown[3],dropdown[4]) # nosec B608
    #print(sql)
    cur.execute(sql) 
    dropdown_data = cur.fetchall()
    #print(dropdown_data)
    dropdownItems=[str(i['key'])+':'+i['name'] for i in dropdown_data]
    return dropdownItems

def getFilteredNotInDropDownItems(cur,dropdowns):
    dropdownItems={}
    for id,version,table,column,name,filter in dropdowns:
        #print(getFilteredNotInDropDownItems)
        filter="WHERE id NOT IN({}) ".format(','.join([str(i) for i in filter]))    
        sql='SELECT {} AS key,{} AS name FROM "{}".{} {};'.format(column,name,version,table,filter) # nosec B608
        #print(sql)
        cur.execute(sql) 
        dropdown_data = cur.fetchall()
        dropdownItems[id]=[str(i['key'])+':'+i['name'] for i in dropdown_data]
    return dropdownItems
    
def getDropDownItems(cur,dropdowns):
    dropdownItems={}
    for id,version,table,column,name in dropdowns:         
        sql='SELECT {} AS key,{} AS name FROM "{}".{};'.format(column,name,version,table,column) # nosec B608
        #print(sql)
        cur.execute(sql) 
        dropdown_data = cur.fetchall()
        dropdownItems[id]={i['key'] : str(i['key'])+':'+tr('@default',i['name']) for i in dropdown_data}
    return dropdownItems
    
def getFilteredDropDownItemNames(cur,dropdowns):
    dropdownItems={}
    for id,version,table,name,filter in dropdowns:
        #print(filter)
        if filter:
            filter="WHERE id IN({}) ".format(','.join([str(i) for i in filter]))
            sql='SELECT {} AS name FROM "{}".{} {}ORDER BY id;'.format(name,version,table,filter) # nosec B608
            #print(sql)
            cur.execute(sql) 
            dropdown_data = cur.fetchall()
            dropdownItems[id]={i['name'] : str(i['name']) for i in dropdown_data}
        else:
            dropdownItems[id]={}
    return dropdownItems

def getFilteredNotInDropDownItemNames(cur,dropdowns):
    dropdownItems={}
    for id,version,table,name,filter in dropdowns:
        #print(filter)
        if filter:
            filter="WHERE id NOT IN({}) ".format(','.join([str(i) for i in filter]))
            sql='SELECT {} AS name FROM "{}".{} {}ORDER BY id;'.format(name,version,table,filter) # nosec B608
            #print(sql)
            cur.execute(sql) 
            dropdown_data = cur.fetchall()
            dropdownItems[id]=[str(i['name']) for i in dropdown_data]
        else:
            dropdownItems[id]=[]
    return dropdownItems
    
def getDropDownItemNames(cur,dropdowns):
    dropdownItems={}
    for id,version,table,name in dropdowns:         
        sql='SELECT {} AS name FROM "{}".{} ORDER BY id;'.format(name,version,table) # nosec B608
        #print(sql)
        cur.execute(sql) 
        dropdown_data = cur.fetchall()
        dropdownItems[id]=[str(i['name']) for i in dropdown_data]
    return dropdownItems
    
def getConnValue(cur,bundle,sequence):
    """Sequence of connection_id"""
    sql="""SELECT b_t_conns.conn_bundle_type_id, b_t_conns.sequence, b_t_conns.conn_type_id, conn_t_conns.sequence, conns.temp,conns.p, conns.mdot,conns.type, b_t_conns.conn_type_id
	FROM connections conns, bundle_type_conns b_t_conns, connection_type_connections conn_t_conns
	WHERE b_t_conns.conn_bundle_type_id = {} AND conn_t_conns.sequence={} AND conn_t_conns.connection_id=conns.id AND b_t_conns.conn_type_id=conn_t_conns.connection_type_id
	ORDER BY b_t_conns.sequence, conn_t_conns.sequence;""".format(bundle, sequence) # nosec B608
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
    
def getTemplatesInfo(feature,cur):
    if feature in ['line','junction']:
        sql="""SELECT id, type, id::text||':'||type AS name
    FROM {}_types ORDER BY id; """.format(feature) # nosec B608
    else:
        sql="""SELECT template, template_name, template::text||':'||template_name AS name
    FROM {}_templates ORDER BY template; """.format(feature) # nosec B608
    cur.execute(sql)
    return cur.fetchall()    
    
def getTemplates(type,cur):
    """ get all templates of type """
    sql='SELECT template FROM public.{}_templates;'.format(type) # nosec B608
    cur.execute(sql)
    return [str(i['template']) for i in cur.fetchall()]    
        
def getTableIds(cur,version,table,column):
    sql="""SELECT {} FROM "{}".{}""".format(column,version,table) # nosec B608
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
    
def getResultVars(cur,config,feature,type):
    """type=='m' --> measurements; type=='s' --> simulation data"""
    if feature=='energy_plant':
        feature='energy'
        col=3
    else:
        col=2
    sql="""SELECT split_part(table_name,'_{}_',2) AS var
    FROM information_schema.tables 
    WHERE table_schema = '{}' AND split_part(table_name,'_',{})='{}' AND split_part(table_name,'_',1)='{}' AND NOT split_part(table_name,'_{}_',2) LIKE '%_vis';""".format(type,config['versionName'],col,type,feature,type) # nosec B608
    #print(sql)
    cur.execute(sql)
    return [var['var'] for var in cur.fetchall()]
    
def getTableAttr(cur,config,feature,withoutID=False):
    sql="""SELECT column_name 
    FROM information_schema.columns 
    WHERE table_name = '{}s' AND table_schema='{}';""".format(feature,config['versionName']) # nosec B608
    #print(sql)
    cur.execute(sql)
    return [attr['column_name'] for attr in cur.fetchall() if ((False if attr['column_name']=='id' else True) if withoutID else True)]


def getTableNumericAttr(cur,config,feature,withoutID=False):
    sql="""SELECT column_name 
    FROM information_schema.columns 
    WHERE table_name = '{}s' AND table_schema='{}' 
        AND data_type IN ('integer','numeric','double precision','real','smallint','bigint');""".format(feature,config['versionName']) # nosec B608
    #print(sql)
    cur.execute(sql)
    return [attr['column_name'] for attr in cur.fetchall() if ((False if attr['column_name']=='id' else True) if withoutID else True)]
