from .translations import tr_msg
from .compat import MessageCritical, MessageInfo
from .db import featureCount

import psycopg2
import psycopg2.extras
from qgis.utils import iface 
from .debug_log import dprint


def checkIntersectingFeatures(cur,config):
    for f1 in ['customer','energy_plant','junction']:
        for f2 in ['customer','energy_plant','junction']:
            sql="""SELECT a.id AS id1, b.id AS id2
    FROM "{}".{}s a
    JOIN "{}".{}s b ON ST_DWithin(a.geom, b.geom, 0.01)
    WHERE a.id <> b.id;  -- Exclude the same row""".format(config['versionName'],f1,config['versionName'],f2) # nosec B608
            cur.execute(sql)
            overlaying_features=cur.fetchall()
            if overlaying_features:
                for error in overlaying_features:
                    iface.messageBar().pushMessage(tr_msg("Error"), tr_msg("{}: {} and {}: {} intersect.").format(tr_msg(f1.capitalize()),error['id1'],tr_msg(f2),error['id2']), level=MessageCritical)
                return True
    return False
    
def checkLoopInConnections(cur,version,table,type):
    """features (customers or energy plants) with a line of table which connects them directly to an energy plant or a customer
    (the line ends are searched with the spatial index of table; nothing is found if there are no energy plants or no customers)"""
    sql="""SELECT f1.id
    FROM "{v}".{t}s f1 JOIN {table} sh ON sh.geom && ST_Expand(f1.geom,0.001)
    WHERE EXISTS (SELECT 1 FROM "{v}".energy_plants) AND EXISTS (SELECT 1 FROM "{v}".customers) AND (
        ST_dWithIn(ST_StartPoint(sh.geom),f1.geom,0.001) AND (
            EXISTS (SELECT 1 FROM "{v}".energy_plants f2 WHERE ST_dWithIn(ST_EndPoint(sh.geom),f2.geom,0.001)) OR
            EXISTS (SELECT 1 FROM "{v}".customers f3 WHERE ST_dWithIn(ST_EndPoint(sh.geom),f3.geom,0.001))) OR
        ST_dWithIn(ST_EndPoint(sh.geom),f1.geom,0.001) AND (
            EXISTS (SELECT 1 FROM "{v}".energy_plants f2 WHERE ST_dWithIn(ST_StartPoint(sh.geom),f2.geom,0.001)) OR
            EXISTS (SELECT 1 FROM "{v}".customers f3 WHERE ST_dWithIn(ST_StartPoint(sh.geom),f3.geom,0.001))))
    GROUP BY f1.id;""".format(table=table,v=version,t=type) # nosec B608
    cur.execute(sql)
    return cur.fetchall()
    
def checkGenerateTopologyLayerData(config,cur,networks,connectPlants,connectCustomers):
    checked_networks=[]
    dprint('checkGenerateTopologyLayerData')
    for network in networks:
        network_check=True
        #check numer of features (customers and plants) > 0 
        if featureCount(cur,config,network,'customer')>0 and featureCount(cur,config,network,'energy_plant')>0:
            #check if features plants are connected to network if not connectPlants 
            sql="""SELECT count(*) AS count FROM "{}".energy_plants f, "{}".lines l WHERE ST_dWithin(f.geom,l.geom,0.0001);""".format(config['versionName'],config['versionName']) # nosec B608
            cur.execute(sql)
            ep_conn_count=cur.fetchone()['count']
            if ep_conn_count==0 and not connectPlants:
                iface.messageBar().pushMessage(tr_msg("Info"), tr_msg("Please check your layer data, if there is at least one energy plant connected to network {}!").format(network), level=MessageInfo)
                network_check=False
            
            #check if features customers are connected to network if not connectCustomers 
            sql="""SELECT count(*) AS count FROM "{}".customers f, "{}".lines l WHERE ST_dWithin(f.geom,l.geom,0.0001);""".format(config['versionName'],config['versionName']) # nosec B608
            cur.execute(sql)
            customer_conn_count=cur.fetchone()['count']
            if customer_conn_count==0 and not connectCustomers:
                iface.messageBar().pushMessage(tr_msg("Info"), tr_msg("Please check your layer data, if there is at least one customer connected to network {}!").format(network), level=MessageInfo)
                network_check=False        
        else:
            iface.messageBar().pushMessage(tr_msg("Info"), tr_msg("Please check your layer data, if there is at least one entry of network {} in the layers: energy_plants and customers!").format(network), level=MessageInfo)
        
        #check overlapping features
        if checkIntersectingFeatures(cur,config):
            network_check=False
            
        if network_check:
            checked_networks.append(network)
        
    return checked_networks
    