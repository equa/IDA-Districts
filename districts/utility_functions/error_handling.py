from .db import *

import psycopg2
import psycopg2.extras
from qgis.utils import iface 


def checkIntersectingFeatures(cur,dictDB):
    for f1 in ['customer','energy_plant','junction']:
        for f2 in ['customer','energy_plant','junction']:
            sql="""SELECT a.id AS id1, b.id AS id2
    FROM "{}".{}s a
    JOIN "{}".{}s b ON ST_DWithin(a.geom, b.geom, 0.01)
    WHERE a.id <> b.id;  -- Exclude the same row""".format(dictDB['versionName'],f1,dictDB['versionName'],f2) # nosec B608
            cur.execute(sql)
            overlaying_features=cur.fetchall()
            if overlaying_features:
                for error in overlaying_features:
                    iface.messageBar().pushMessage("Error", "{}: {} and {}: {} intersect.".format(f1.capitalize(),error['id1'],f2,error['id2']), level=Qgis.Critical)
                return True
    return False
    
def checkLoopInConnections(cur,version,table,type):
    sql="""SELECT f1.id
    FROM {} sh, "{}".{}s f1,"{}".energy_plants f2, "{}".customers f3
    WHERE ST_dWithIn(ST_StartPoint(sh.geom),f1.geom,0.001) AND (ST_dWithIn(ST_EndPoint(sh.geom),f2.geom,0.001) OR ST_dWithIn(ST_EndPoint(sh.geom),f3.geom,0.001)) OR 
        ST_dWithIn(ST_EndPoint(sh.geom),f1.geom,0.001) AND (ST_dWithIn(ST_StartPoint(sh.geom),f2.geom,0.001) OR ST_dWithIn(ST_StartPoint(sh.geom),f3.geom,0.001))
    GROUP BY f1.id;""".format(table,version,type,version,version) # nosec B608
    cur.execute(sql)
    return cur.fetchall()
    
def checkGenerateTopologyLayerData(dictDB,cur,networks,connectPlants,connectCustomers):
    checked_networks=[]
    #print('checkGenerateTopologyLayerData')
    for network in networks:
        network_check=True
        #check numer of features (customers and plants) > 0 
        if featureCount(cur,dictDB,network,'customer')>0 and featureCount(cur,dictDB,network,'energy_plant')>0:
            #check if features plants are connected to network if not connectPlants 
            sql="""SELECT count(*) AS count FROM "{}".energy_plants f, "{}".lines l WHERE ST_dWithin(f.geom,l.geom,0.0001);""".format(dictDB['versionName'],dictDB['versionName']) # nosec B608
            cur.execute(sql)
            ep_conn_count=cur.fetchone()['count']
            if ep_conn_count==0 and not connectPlants:
                iface.messageBar().pushMessage("Info", "Please check your layer data, if there is at least one energy plant connected to network {}!".format(network), level=Qgis.Info)
                network_check=False
            
            #check if features customers are connected to network if not connectCustomers 
            sql="""SELECT count(*) AS count FROM "{}".customers f, "{}".lines l WHERE ST_dWithin(f.geom,l.geom,0.0001);""".format(dictDB['versionName'],dictDB['versionName']) # nosec B608
            cur.execute(sql)
            customer_conn_count=cur.fetchone()['count']
            if customer_conn_count==0 and not connectCustomers:
                iface.messageBar().pushMessage("Info", "Please check your layer data, if there is at least one customer connected to network {}!".format(network), level=Qgis.Info)
                network_check=False        
        else:
            iface.messageBar().pushMessage("Info", "Please check your layer data, if there is at least one entry of network {} in the layers: energy_plants and customers!".format(network), level=Qgis.Info)
        
        #check overlapping features
        if checkIntersectingFeatures(cur,dictDB):
            network_check=False
            
        if network_check:
            checked_networks.append(network)
        
    return checked_networks
    