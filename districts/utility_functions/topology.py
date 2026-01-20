import psycopg2
from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT     
import psycopg2.extras
from plugins.utility_functions.utility import *
from plugins.utility_functions.db import *
from qgis.PyQt.QtWidgets import QMessageBox

def checkNetwork(cur,version,networks):
    sql="""SELECT count(*) FROM "{}".lines WHERE network IS NULL;""".format(version)
    cur.execute(sql)
    networkNullCount=cur.fetchone()['count']
    
    if networkNullCount>0:
        print('Network attribute not set!')

        dlg_question = QMessageBox()
        dlg_question.setWindowTitle('Network attribute value missing!')
        dlg_question.setText("""{} network attribute(s) in lines are not set. Should the attribute(s) be set to 1?""".format(networkNullCount))
        dlg_question.setStandardButtons(QMessageBox.Yes | QMessageBox.Cancel)
        dlg_question.setIcon(QMessageBox.Question)
        button = dlg_question.exec()

        if button == QMessageBox.Yes:
            sql="""UPDATE "{}".lines SET network=1 WHERE network IS NULL;""".format(version)
            print(sql)
            cur.execute(sql)
            return True
        else:
            print("Cancel!")
            return False
    return True
            
def getNetworkSequences(cur,dictDB,network):
    sql="""SELECT COALESCE(max(bp.sequence),0) AS number_of
    FROM "{}".lines f, bundle_pipes bp
    WHERE f.network = {} AND f.pipe_bundle_type_id=bp.pipe_bundle_type_id;""".format(dictDB['versionName'],network)
    print(sql)
    cur.execute(sql)
    return [str(i) for i in range(1,cur.fetchone()['number_of']+1)]
    
def redrawSubnetworkIncludingLines(table,cur,dictDB,srid):
    sql="""TRUNCATE "{}".submodels;

WITH sub AS(
    SELECT min(ST_XMin(geom)) AS x_min, min(ST_YMin(geom)) AS y_min, max(ST_XMax(geom)) AS x_max, max(ST_YMax(geom)) AS y_max FROM {}
)
INSERT INTO "{}".submodels (id,geom) 
    SELECT 1,ST_Multi(ST_Buffer(ST_SetSRID(ST_MakeBox2D(ST_Point(sub.x_min,sub.y_min),ST_Point(sub.x_max,sub.y_max)),{}),10)) FROM sub;""".format(dictDB['versionName'],table,dictDB['versionName'],srid)
    print(sql)
    cur.execute(sql)
    
def updateSubmodels(cur,dictDB):
    sql="""UPDATE temp.junctions j SET submodel = s_m.id FROM (SELECT * FROM "{}".submodels) s_m WHERE ST_dWithin(j.geom,s_m.geom,0.0001);
UPDATE "{}".energy_plants f SET submodel = s_m.id FROM (SELECT * FROM "{}".submodels) s_m WHERE ST_dWithin(f.geom,s_m.geom,0.0001);
UPDATE temp.customers f SET submodel = s_m.id FROM (SELECT * FROM "{}".submodels) s_m WHERE ST_dWithin(f.geom,s_m.geom,0.0001);
UPDATE temp.lines l SET submodel = a.sm_id 
    FROM (SELECT l.id AS lid, array_agg(s_m.id) AS sm_id
            FROM "{}".submodels s_m, "{}".lines l
            WHERE ST_dWithin(l.geom,s_m.geom,0.0001)
            GROUP BY l.id) a 
    WHERE a.lid=l.id;
UPDATE temp.lines l SET submodel = ARRAY[s_m.id] FROM (SELECT * FROM "{}".submodels) s_m WHERE ST_dWithin(l.geom,s_m.geom,0.0001);
UPDATE temp.lines SET submodel = ARRAY[1] WHERE submodel IS NULL;""".format(dictDB['versionName'],dictDB['versionName'],dictDB['versionName'],dictDB['versionName'],dictDB['versionName'],dictDB['versionName'],dictDB['versionName'])
    print(sql)
    cur.execute(sql)
        
def setSubnetwork(cur,dictDB,redraw_submodels_polygons,srid):
    """set the submodel to 1 if not set otherwise"""
    print('Set submodel if no submodels')
    if redraw_submodels_polygons:
        
        #draw rectangle around all customers
        sql='TRUNCATE "{}".submodels CASCADE;'.format(dictDB['versionName'])
        print(sql)
        cur.execute(sql)
            
        redrawSubnetworkIncludingLines('"{}".lines'.format(dictDB['versionName']),cur,dictDB,srid)
        
        #junctions
        sql='UPDATE "{}".junctions SET submodel = 1;'.format(dictDB['versionName'])
        print(sql)
        cur.execute(sql)
        #customers
        sql='UPDATE "{}".customers SET submodel = 1;'.format(dictDB['versionName'])
        print(sql)
        cur.execute(sql)
        #energy_plants
        sql='UPDATE "{}".energy_plants SET submodel = 1;'.format(dictDB['versionName'])
        print(sql)
        cur.execute(sql)
        #lines
        sql='UPDATE "{}".lines SET submodel = array[1];'.format(dictDB['versionName'])
        print(sql)
        cur.execute(sql)  

def getBundleValues(bundle,cur):
    sql="""SELECT b_t_conns.conn_bundle_type_id, b_t_conns.sequence, b_t_conns.conn_type_id, conn_t_conns.sequence, conns.temp,conns.p, conns.mdot,conns.type, conns.id AS conn_id
	FROM connections conns, bundle_type_conns b_t_conns, connection_type_connections conn_t_conns
	WHERE b_t_conns.conn_bundle_type_id = {} AND conn_t_conns.connection_id=conns.id AND b_t_conns.conn_type_id=conn_t_conns.connection_type_id
	ORDER BY b_t_conns.sequence, conn_t_conns.sequence;""".format(bundle)
    cur.execute(sql)
    return cur.fetchall()

def getConnTypesByFeature(cur,dictDB,feature,id):
    sql="""SELECT b_t_conns.conn_type_id 
    FROM {}.{}s f, {}_templates f_t, bundle_type_conns b_t_conns
    WHERE f_t.template=f.template AND b_t_conns.conn_bundle_type_id=f_t.conn_bundle_type AND f.id={}
    ORDER BY b_t_conns.sequence;""".format(dictDB['versionName'],feature,feature,id)
    print(sql)
    cur.execute(sql)
    return [str(i['conn_type_id']) for i in cur.fetchall()]
    
def getConnIdsByConnType(cur,conn_type):
    sql="""SELECT connection_id FROM connection_type_connections WHERE connection_type_id={} ORDER BY sequence;""".format(conn_type)
    print(sql)
    cur.execute(sql)
    return [str(i['connection_id']) for i in cur.fetchall()]
    
def getConnSequencesByConnType(cur,conn_type):
    sql="""SELECT sequence FROM connection_type_connections WHERE connection_type_id={} ORDER BY sequence;""".format(conn_type)
    print(sql)
    cur.execute(sql)
    return [str(i['sequence']) for i in cur.fetchall()]
    
def getConnTypeConnValues(cur,ids):
    sql="""SELECT conn_t_conns.connection_type_id, conn_t_conns.connection_id , conn_t_conns.sequence, conns.temp,conns.p, conns.mdot,conns.type, conns.id AS conn_id
	FROM connections conns, connection_type_connections conn_t_conns
	WHERE conn_t_conns.connection_id=conns.id AND conn_t_conns.connection_type_id IN ({})
	ORDER BY conn_t_conns.sequence;""".format(','.join([str(id) for id in ids]))
    cur.execute(sql)
    return cur.fetchall()
    
def getConnValues(bundle,conn_id,cur):
    sql="""SELECT b_t_conns.conn_bundle_type_id, b_t_conns.sequence, b_t_conns.conn_type_id, conn_t_conns.sequence, conns.temp,conns.p, conns.mdot,conns.type, conns.id AS conn_id
	FROM connections conns, bundle_type_conns b_t_conns, connection_type_connections conn_t_conns
	WHERE b_t_conns.conn_bundle_type_id = {} AND conn_t_conns.connection_id=conns.id AND b_t_conns.conn_type_id=conn_t_conns.connection_type_id {}
	ORDER BY b_t_conns.sequence, conn_t_conns.sequence;""".format(bundle,'AND conns.id='+conn_id if not conn_id=='X' else '')
    cur.execute(sql)
    return cur.fetchone()

def getConnsValuesByFeature(type_id,feature_id,cur,dictDB):
    return getConnsValues(getConnBundleByFeature(type_id,feature_id,cur,dictDB),cur)
    
def getConnsValues(bundle,cur):
    sql="""SELECT b_t_conns.conn_bundle_type_id, b_t_conns.sequence AS conn_type_seq, b_t_conns.conn_type_id, conn_t_conns.sequence AS conn_seq, conns.temp,conns.p, conns.mdot,conns.type, conns.id AS conn_id, conns.p_ctrl
	FROM connections conns, bundle_type_conns b_t_conns, connection_type_connections conn_t_conns
	WHERE b_t_conns.conn_bundle_type_id = {} AND conn_t_conns.connection_id=conns.id AND b_t_conns.conn_type_id=conn_t_conns.connection_type_id
	ORDER BY b_t_conns.sequence, conn_t_conns.sequence;""".format(bundle)
    cur.execute(sql)
    return cur.fetchall()
    
def getConnBundleByFeature(feature_type,feature_id,cur,dictDB):
    sql="""SELECT c_t.conn_bundle_type 
    FROM "{}".{} f, {} c_t 
    WHERE f.id={} AND c_t.template=f.template;""".format(dictDB['versionName'],feature_type+'s' if type(feature_type)==str else getTypeNameById(feature_type),getTemplateNameById(int(getTypeIdByName(feature_type))) if type(feature_type)==str else getTemplateNameById(feature_type),feature_id)
    cur.execute(sql)
    return cur.fetchone()['conn_bundle_type']

def getConnBundlesByType(cur,dictDB,type):
    sql="""SELECT f_t.conn_bundle_type
    FROM {}.{}s f, {}_templates f_t
    WHERE f.template=f_t.template
    GROUP BY f_t.conn_bundle_type;""".format(dictDB['versionName'],type,type)
    print(sql)
    cur.execute(sql)
    return [str(i['conn_bundle_type']) for i in cur.fetchall()]
    
def getConnTypesByConnBundleType(cur,dictDB,c_b_type):
    sql="""SELECT conn_type_id FROM bundle_type_conns WHERE conn_bundle_type_id={} ORDER BY sequence;""".format(c_b_type)
    cur.execute(sql)
    return [str(i['conn_type_id']) for i in cur.fetchall()]
    
def getBundleValuesByFeature(type_id,feature_id,cur,dictDB):
    return getConnValues(getConnBundleByFeature(type_id,feature_id,cur,dictDB),conn_id,cur)
    
def getConnTypeSeqFromBundle(cur,dictDB,c_b_type,conn_type):
    sql="""SELECT sequence FROM bundle_type_conns WHERE conn_bundle_type_id={} AND conn_type_id={};""".format(c_b_type,conn_type)
    print(sql)
    cur.execute(sql)
    return cur.fetchone()['sequence']
    
def getConnValuesByFeature(type_id,feature_id,conn_id,cur,dictDB):
    return getConnValues(getConnBundleByFeature(type_id,feature_id,cur,dictDB),conn_id,cur)

def getUsedConnBundleTypes(type_name,cur,dictDB):
    sql="""Select t.conn_bundle_type
    FROM "{}".{}s f, {}_templates t
    WHERE f.template=t.template
    GROUP BY t.conn_bundle_type
    ORDER BY t.conn_bundle_type;""".format(dictDB['versionName'],type_name,type_name)
    cur.execute(sql)
    return [i['conn_bundle_type'] for i in cur.fetchall()]
    
def getUsedConnTypes(type_name,cur,dictDB):
    sql="""Select b_t_conns.conn_type_id
    FROM "{}".{}s f, {}_templates t, bundle_type_conns b_t_conns 
    WHERE f.template=t.template AND b_t_conns.conn_bundle_type_id = t.conn_bundle_type
    GROUP BY b_t_conns.conn_type_id
    ORDER BY b_t_conns.conn_type_id;""".format(dictDB['versionName'],type_name,type_name)
    cur.execute(sql)
    return [i['conn_bundle_type'] for i in cur.fetchall()]
    
def getUsedConnTypeIdents(type_name,cur,dictDB):
    sql="""WITH sub AS(
    Select  b_t_conns.conn_bundle_type_id::text||'_'||b_t_conns.sequence::text as ident
        FROM "{}".{}s f, {}_templates t, bundle_type_conns b_t_conns 
        WHERE f.template=t.template AND b_t_conns.conn_bundle_type_id = t.conn_bundle_type
)
SELECT ident FROM sub GROUP BY ident;""".format(dictDB['versionName'],type_name,type_name)
    cur.execute(sql)
    return [i['ident'] for i in cur.fetchall()]
    
def getConnBundleByTemplate(feature,template,cur,dictDB):
    sql="""SELECT conn_bundle_type 
    FROM {}_templates 
    WHERE template={};""".format(feature,template)
    cur.execute(sql)
    return cur.fetchone()['conn_bundle_type']

def getLineConnType(cur,dictDB,id):
    sql="""SELECT t.conn_type
    FROM "{}".lines l, line_types t
    WHERE l.assettype=t.assettype AND l.id={};""".format(dictDB['versionName'],id)
    cur.execute(sql)
    return cur.fetchone()['conn_type']

def getUsedPipeBundleSequences(cur,dictDB):
    sql=f"""WITH sub AS(
    SELECT pipe_bundle_type_id FROM "{dictDB['versionName']}".lines GROUP BY pipe_bundle_type_id 
)
SELECT sequence 
    FROM bundle_pipes bp,sub 
    WHERE bp.pipe_bundle_type_id=sub.pipe_bundle_type_id
    GROUP BY sequence ORDER BY sequence;"""
    print(sql)
    cur.execute(sql)
    return [i['sequence'] for i in cur.fetchall()]

def getConnBundleTypesByConnType(cur,dictDB,conn_type_id):
    sql="""SELECT conn_bundle_type_id FROM bundle_type_conns WHERE conn_type_id={};""".format(conn_type_id)
    print(sql)
    cur.execute(sql)
    return cur.fetchall()
        
def getTemplatesByConnType(cur,dictDB,conn_type_id):
    sql="""SELECT 'customer' AS type,t.template, t.template::text||'_'||t.template_name AS t_name, bt_conns.conn_bundle_type_id 
    FROM bundle_type_conns bt_conns, customer_templates t 
    WHERE conn_type_id={} AND t.conn_bundle_type=bt_conns.conn_bundle_type_id
UNION
SELECT 'energy_plant' AS type,t.template, t.template::text||'_'||t.template_name AS t_name, bt_conns.conn_bundle_type_id 
    FROM bundle_type_conns bt_conns, energy_plant_templates t 
    WHERE conn_type_id={} AND t.conn_bundle_type=bt_conns.conn_bundle_type_id""".format(conn_type_id,conn_type_id)
    print(sql)
    cur.execute(sql)
    return cur.fetchall()
    
def getTemplatesByConnBundleType(cur,dictDB,conn_bundle_type_id):
    sql="""--getTemplatesByConnType
SELECT 'customer' AS type,template, template::text||'_'||template_name AS t_name, conn_bundle_type AS conn_bundle_type_id
    FROM customer_templates WHERE conn_bundle_type={}
UNION
SELECT 'energy_plant' AS type,template, template::text||'_'||template_name AS t_name, conn_bundle_type AS conn_bundle_type_id
    FROM energy_plant_templates WHERE conn_bundle_type={}""".format(conn_bundle_type_id,conn_bundle_type_id)
    print(sql)
    cur.execute(sql)
    return cur.fetchall()
    
def getConnsValuesByTemplate(feature,template,cur,dictDB):
    return getConnsValues(getConnBundleByTemplate(feature,template,cur,dictDB),cur)
    
def getMeterName(cur,conn_bundle_type,conn_type):
    sql="""SELECT conn_bundle_type_id, sequence
	FROM bundle_type_conns
	WHERE conn_bundle_type_id = {} AND conn_type_id={};""".format(conn_bundle_type,conn_type)
    cur.execute(sql)
    connValues=cur.fetchall()
    if connValues:
        connValues=connValues[0]
        return "{}_{}_Flowmeter2".format(str(connValues['conn_bundle_type_id']),str(connValues['sequence']))
    else:
        return ""

def getMeterNameByFeature(cur,feature_id,conn_type):
    return getMeterName(cur,getConnBundleByFeature(feature_id,cur))
        
def getPMT2muxName(cur,conn_bundle_type,connection_id):
    sql="""SELECT b_t_conns.conn_bundle_type_id, b_t_conns.sequence AS conn_t_seq, b_t_conns.conn_type_id, conn_t_conns.sequence AS conn_seq, conns.temp
	FROM connections conns, bundle_type_conns b_t_conns, connection_type_connections conn_t_conns
	WHERE b_t_conns.conn_bundle_type_id = {} AND conn_t_conns.connection_id={} AND conn_t_conns.connection_id=conns.id AND b_t_conns.conn_type_id=conn_t_conns.connection_type_id
	ORDER BY b_t_conns.sequence, conn_t_conns.sequence;""".format(conn_bundle_type,connection_id)
    cur.execute(sql)
    connValues=cur.fetchall()
    if connValues:
        connValues=connValues[0]
        return "PMT2mux_{}_{}_{}_{}".format(connValues['conn_bundle_type_id'],connValues['conn_t_seq'],connValues['conn_type_id'],connValues['conn_seq'])
    else:
        return ""
        
def getPMT2muxIdents(cur,conn_bundle_type):
    return ["{}_{}_{}_{}".format(str(connValue['conn_bundle_type_id']),str(connValue['conn_type_seq']),str(connValue['conn_type_id']),str(connValue['conn_seq'])) for connValue in getConnsValues(conn_bundle_type,cur)]
    
def getConnsValuesIdentTypeDict(cur,conn_bundle_type):
    return {"{}_{}_{}_{}".format(str(connValue['conn_bundle_type_id']),str(connValue['conn_type_seq']),str(connValue['conn_type_id']),str(connValue['conn_seq'])) : {':T' : connValue['type'], ':V-VAR' : connValue['mdot'] if connValue['p_ctrl'] else connValue['p'], ':VAR' : 'M' if connValue['p_ctrl'] else 'P', ':V-T': connValue['temp']} 
        for connValue in getConnsValues(conn_bundle_type,cur)}
    
def getPMT2muxIdentFromConnValues(connValues,conn_seq,conn_t_seq=1):
    try:
        return ["{}_{}_{}_{}".format(connValue['conn_bundle_type_id'],connValue['conn_type_seq'],connValue['conn_type_id'],connValue['conn_seq']) for connValue in connValues if conn_seq==connValue['conn_seq'] and connValue['conn_type_seq']==conn_t_seq][0]
    except:
        return ''
        
def checkLineDirectionTopology(cur,version,tolerance,iface,network):
    """Change the line direction if the end point is closer to the main plant. Important for modelleing and temperature wave visualization. """ 
    print('Check line direction')
    sql="""SELECT st_v.id::integer AS epid 
        FROM temp.energy_plants ep, temp.streets_help_vertices_pgr st_v 
        WHERE ST_dWithin(ep.geom,st_v.the_geom,{}) AND {} = ANY(ep.network)
        ORDER BY ep.id LIMIT 1;""".format(tolerance,network)
    print(sql)
    cur.execute(sql)
    epid=cur.fetchone()['epid'] 
    print(epid)
    sql = """SELECT id AS lid, ST_StartPoint(geom) AS l_start_point,ST_EndPoint(geom) AS l_end_point FROM temp.streets_help;"""
    print(sql) 
    cur.execute(sql) 
    lines=cur.fetchall()
    for line in lines:
        print('--------------------------')
        lid=line['lid']
        print(lid)
        start_point=line['l_start_point']
        end_point=line['l_end_point']
        
        #end_node
        sql="SELECT st_v.id::integer AS vid FROM temp.streets_help_vertices_pgr st_v WHERE ST_dWithin('{}',st_v.the_geom,{});".format(end_point,tolerance)
        print(sql)
        cur.execute(sql)
        jid_end_topo=cur.fetchone()['vid']     
        if jid_end_topo!=epid:               
            sql="""WITH sub As(
SELECT seq, node, edge, cost
            FROM pgr_dijkstra(
                'SELECT sh.id, sh.source, sh.target, sh.length_m as cost FROM temp.streets_help sh',
                {}, 
                {},
                false
            )
)
SELECT sum(cost) AS costs FROM sub;""".format(epid,jid_end_topo)
            print(sql)
            cur.execute(sql) 
            length_node_end=cur.fetchone()['costs']
        else:
            length_node_end=0
        print(length_node_end)
        
        #start_node
        sql="SELECT st_v.id::integer AS vid FROM temp.streets_help_vertices_pgr st_v WHERE ST_dWithin('{}',st_v.the_geom,{});".format(start_point,tolerance)
        print(sql)
        cur.execute(sql)
        jid_start_topo=cur.fetchone()['vid'] 
        if jid_start_topo!=epid:       
            sql="""WITH sub As(
SELECT seq, node, edge, cost
            FROM pgr_dijkstra(
                'SELECT sh.id, sh.source, sh.target, sh.length_m as cost FROM temp.streets_help sh',
                {}, 
                {},
                false
            )
)
SELECT sum(cost) AS costs FROM sub;""".format(epid,jid_start_topo)
            print(sql)
            cur.execute(sql) 
            length_node_start=cur.fetchone()['costs']
        else:
            length_node_start=0
        print(length_node_start)
        
        try:
            if length_node_end<length_node_start:
                print('change line direction')
                sql='UPDATE temp.streets_help SET geom = ST_Reverse(geom) WHERE id={};'.format(lid)
                print(sql)
                cur.execute(sql)
        except:
            #iface.messageBar().pushMessage("Error", "Check line direction has failed! Probably because of gaps in the topology. You could try to increase the tolerancy.", level=Qgis.Critical)   
            print('Check line ({}) direction has failed! Probably because of gaps in the topology. You could try to increase the tolerancy.'.format(lid))
            pass

#todo pipe laying of network 
def checkLineDirectionPipeLaying(cur,version,tolerance,network):
    """Change the line direction if the end point is closer to the main plant. Important for modelleing and temperature wave visualization. """ 
    print('Check line direction')
    sql="""SELECT st_v.id::integer AS v_ep 
    FROM temp.energy_plants ep, temp.streets_help_vertices_pgr st_v 
    WHERE ST_dWithin(ep.geom,st_v.the_geom,{}) AND {} = ANY(ep.network) ORDER BY ep.id LIMIT 1;""".format(tolerance,network)
    print(sql)
    cur.execute(sql)
    epid=cur.fetchone()['v_ep'] 
    sql = """SELECT id AS lid, ST_StartPoint(geom) AS l_start_point, ST_EndPoint(geom) AS l_end_point FROM temp.lines;"""
    print(sql) 
    cur.execute(sql) 
    lines=cur.fetchall()
    for counter,line in enumerate(lines,1):
        print(counter)
        print(line)
        lid=line['lid']
        start_point=line['l_start_point']
        end_point=line['l_end_point']
        
        #end_node
        sql="SELECT st_v.id::integer AS vid FROM temp.streets_help_vertices_pgr st_v WHERE ST_dWithin('{}',st_v.the_geom,{});".format(end_point,tolerance)
        print(sql)
        cur.execute(sql)
        jid_end_topo=cur.fetchone()['vid']       
        if jid_end_topo!=epid:               
            sql="""WITH sub As(
SELECT seq, node, edge, cost
            FROM pgr_dijkstra(
                'SELECT sh.id, sh.source, sh.target, sh.length_m as cost FROM temp.streets_help sh',
                {}, 
                {},
                false
            )
)
SELECT sum(cost) AS costs FROM sub;""".format(epid,jid_end_topo)
            print(sql)
            cur.execute(sql) 
            length_node_end=cur.fetchone()['costs']
        else:
            length_node_end=0
        print(length_node_end)
        
        #start_node
        sql="SELECT st_v.id::integer AS v_start FROM temp.streets_help_vertices_pgr st_v WHERE ST_dWithin('{}',st_v.the_geom,{});".format(start_point,tolerance)
        print(sql)
        cur.execute(sql)
        jid_start_topo=cur.fetchone()['v_start'] 
        print(jid_start_topo)
        if jid_start_topo!=epid:       
            sql="""WITH sub As(
SELECT seq, node, edge, cost
            FROM pgr_dijkstra(
                'SELECT sh.id, sh.source, sh.target, sh.length_m as cost FROM temp.streets_help sh',
                {}, 
                {},
                false
            )
)
SELECT sum(cost) AS sum_costs FROM sub;""".format(epid,jid_start_topo)
            print(sql)
            cur.execute(sql) 
            length_node_start=cur.fetchone()['sum_costs']
        else:
            length_node_start=0
        print(length_node_start)
        
        if length_node_end<length_node_start:
            print('change line direction')
            sql='UPDATE temp.lines SET geom = ST_Reverse(geom) WHERE id={};'.format(lid)
            print(sql)
            cur.execute(sql)