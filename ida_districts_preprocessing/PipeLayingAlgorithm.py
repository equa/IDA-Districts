from plugins.utility_functions.layer_visualization import *
from plugins.utility_functions.db import *
from plugins.utility_functions.utility import *
from plugins.utility_functions.topology import *
import time
from qgis.PyQt.QtCore import Qt, QSettings, QTranslator, QCoreApplication, QObject, QRunnable, pyqtSignal, pyqtSlot
from qgis.core import QgsProject,QgsVectorLayer,QgsDataSourceUri,QgsCategorizedSymbolRenderer,QgsSymbol,QgsRendererCategory
from qgis.PyQt.QtGui import QIcon
from qgis.PyQt import QtGui 
from qgis.PyQt.QtWidgets import QAction,QMainWindow,QWidget,QPushButton,QHBoxLayout,QVBoxLayout,QLabel,QLineEdit,QCheckBox,QComboBox, QProgressBar

# Initialize Qt resources from file resources.py
from .resources import *
# Import the code for the dialog
import os.path
import os
import sys
import psycopg2
import psycopg2.extras
from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT

        
class WorkerPipeLayingSignals(QObject):
    progress=pyqtSignal(int)

class WorkerPipeLaying(QRunnable):
    """Worker thread
    Inherits from QRunnable to handle worker thread setup, signals and wrap-up."""
    def __init__(self,*args,**kwargs):
        super().__init__()
        self.args=args
        print(args)
        self.iface=kwargs['iface']
        self.check_heating_network=kwargs['check_heating_network']
        self.tsup_max=kwargs['tsup_max']
        self.heat_demand_min=kwargs['heat_demand_min']
        self.heating_load_min=kwargs['heating_load_min']
        print('++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++')
        self.heating_lines_assettype=kwargs['heating_assettype_lines']
        print(self.heating_lines_assettype)
        self.heating_customer_assettype=kwargs['heating_assettype_customer']
        self.linearHeatDensity_min=kwargs['linearHeatDensity_min']
        self.check_heating_network_costs=kwargs['check_heating_network_costs']
        self.heat_loss=kwargs['heat_loss']
        self.heat_costs=kwargs['heat_costs']
        self.amortization_period_heat=kwargs['amortization_period_heat']
        
        self.check_cooling_network=kwargs['check_cooling_network']
        self.tsup_min=kwargs['tsup_min']
        self.cold_demand_min=kwargs['cold_demand_min']
        self.cooling_load_min=kwargs['cooling_load_min']
        self.cooling_lines_assettype=kwargs['cooling_assettype_lines']
        print(self.cooling_lines_assettype)
        self.cooling_customer_assettype=kwargs['cooling_assettype_customer']
        self.linearColdDensity_min=kwargs['linearColdDensity_min']
        self.check_cooling_network_costs=kwargs['check_cooling_network_costs']
        self.cold_loss=kwargs['cold_loss']
        self.cold_costs=kwargs['cold_costs']
        self.amortization_period_cold=kwargs['amortization_period_cold']
        
        self.hc_lines_assettype=kwargs['hc_assettype_lines']
        self.hc_customer_assettype=kwargs['hc_assettype_customer']
        self.customer_connection_mode=kwargs['customer_connection_mode']
        self.keep_unconnected_customers=kwargs['keep_unconnected_customers']
        self.signals=WorkerPipeLayingSignals()
        self.is_killed = False
        self.is_paused = False
        self.dictDB=kwargs['dictDB']
        self.plugin_dir=kwargs['plugin_dir']
        self.conn=""
        self.cur=""
        self.network=kwargs['network']
        self.redraw_submodels_polygons=kwargs['redraw_submodels_polygons']
        self.srid=0
        
    @pyqtSlot()
    def run(self):
        print('start pipe laying')
        self.progress_value=1
        self.signals.progress.emit(self.progress_value)
        os.environ['PGPASSWORD'] = self.dictDB['pwd']
        self.conn = dbConnect(self.dictDB,True)
        if self.conn:
            self.cur=self.conn.cursor(cursor_factory = psycopg2.extras.RealDictCursor)
      
            connectionModes=[]
            if self.check_heating_network:
                connectionModes.append('heating')
            if self.check_cooling_network:
                connectionModes.append('cooling')
            print(connectionModes)
            self.srid=loadProjectConfig(self.plugin_dir,self.dictDB['projectName'])['srid']
            self.prepareDB_pipeLaying(self.dictDB['versionName'])
            for mode in connectionModes:
                self.prepareDB_pipeLaying_modeTables(self.dictDB['versionName'])
                self.connectPlantsStreet(self.dictDB['versionName'],mode)
                self.connectCustomersStreet(self.dictDB['versionName'],mode)        
                self.generateTopology(self.dictDB['versionName'])
                plants=self.getPlants(self.dictDB['versionName'])
                self.networkHelp(self.dictDB['versionName'],plants,mode)
                self.connectPlantsNetwork(self.dictDB['versionName'],plants,mode)
                self.connectCustomersNetwork(self.dictDB['versionName'],mode,connectionModes)
            self.finishNetworkTopology(self.dictDB['versionName'])
                
    def pauseResume(self):
        if self.is_paused==False:
            self.is_paused = True
        else:
            self.is_paused = False
        print(self.is_paused)
        
    def kill(self):
        self.is_killed = True        

    def updateTempCustomerConnType(self):
        """ update assettypes of temp.dhc_customers"""
        sql="""UPDATE temp.dhc_customers c SET assettype=a.assettype FROM (
		SELECT {} AS assettype,cc.cid  FROM temp.dhc_lines l, temp.customer_connections cc, temp.dhc_lines_heating lh LEFT JOIN temp.dhc_lines_cooling lc ON lh.geom=lc.geom WHERE lc.geom IS NULL AND cc.lid=l.id AND l.geom=lh.geom
		UNION ALL
		SELECT {} AS assettype,cc.cid  FROM temp.dhc_lines l, temp.customer_connections cc, temp.dhc_lines_heating lh INNER JOIN temp.dhc_lines_cooling lc ON lh.geom=lc.geom WHERE cc.lid=l.id AND l.geom=lh.geom
                UNION ALL
		SELECT {} AS assettype,cc.cid  FROM temp.dhc_lines l, temp.customer_connections cc, temp.dhc_lines_heating lh RIGHT JOIN temp.dhc_lines_cooling lc ON lh.geom=lc.geom WHERE lh.geom IS NULL AND cc.lid=l.id AND l.geom=lc.geom
) a WHERE a.cid=c.id; """.format(self.heating_customer_assettype,self.hc_customer_assettype,self.cooling_customer_assettype)
        print(sql)
        self.cur.execute(sql)
    
    def finishNetworkTopology(self,version):
        self.transformNetworksIntoHC()
        self.insertNodes(version)
        if not self.keep_unconnected_customers:
            self.deleteUnconnectedCustomers(version)
        self.insertJunctionConnections()
        self.insertCustomerConnections()
        self.insertPlantConnections(version)
        self.updateJunctionConnections()
        self.updateTempCustomerConnType()
        self.mergeLines()
        #self.updateHeight(version)
        if self.redraw_submodels_polygons:
            redrawSubnetworkIncludingLines('temp.dhc_lines',self.cur,self.dictDB,self.srid)
        updateSubmodels(self.cur,self.dictDB)
               
        uri = QgsDataSourceUri()
        uri.setConnection(self.dictDB['host'], self.dictDB['port'], self.dictDB['projectName'], self.dictDB['user'], self.dictDB['pwd'])
        print(uri)
        checkLineDirectionPipeLaying(self.cur,version,0.01)
        showTempTables(uri,self.dictDB,self.plugin_dir, self.iface,self.cur)
        self.conn.close()
        print('finished pipe laying')
        self.signals.progress.emit(100)
        
    def updateHeight(self,version):
        "update the height of the network, junctions and customers based on raster layer"
        sql = """SELECT EXISTS (
   SELECT 1
   FROM   information_schema.tables 
   WHERE  table_schema = '{}'
   AND    table_name = 'terrain'
   ) AS exists;""".format(version)
        print(sql) 
        self.cur.execute(sql)
        if self.cur.fetchone()['exists']==True:
            print('Height layer exists')
            #Update dhc_junctions
            sql = """UPDATE temp.dhc_junctions j set asl_m=a.height FROM (
        SELECT j.id, ST_Value(t.rast, 1, st_transform(ST_Centroid(j.geom),4326)) As height
            FROM {}.terrain t,temp.dhc_junctions j
            WHERE ST_Intersects(t.rast,st_transform(j.geom,4326))
    ) a
    WHERE a.id=j.id;""".format(version)
            #print(sql) 
            self.cur.execute(sql)
            
            #Update customer height
            sql= """UPDATE temp.dhc_customers c set asl_m=a.height FROM (
        SELECT c.id, ST_Value(t.rast, 1, st_transform(ST_Centroid(c.geom),4326)) As height
            FROM {}.terrain t,temp.dhc_customers c 
            WHERE ST_Intersects(t.rast,st_transform(c.geom,4326))
    ) a
    WHERE a.id=c.id;""".format(version)
            #print(sql) 
            self.cur.execute(sql)
            
            #Update network height
            sql="""WITH sub AS(
    WITH sub AS(
        SELECT
           ST_PointN(
              geom,
              generate_series(1, ST_NPoints(geom))
           ) AS geom,id
        FROM (Select geom,id from temp.dhc_lines) AS foo
    )
    SELECT sub.id,ST_SetSrid(ST_MakeLine(ST_MakePoint(ST_X(sub.geom),ST_Y(sub.geom), ST_Value(t.rast, 1, ST_Transform(ST_Centroid(sub.geom),4326)))),{}) As geom
        FROM {}.terrain t,sub
        WHERE ST_Intersects(t.rast,st_transform(sub.geom,4326)) GROUP BY sub.id
)
UPDATE temp.dhc_lines g SET geom=sub.geom,
    length=ST_Length(sub.geom)
    FROM sub WHERE sub.id=g.id;""".format(self.srid,version)
            print(sql) 
            self.cur.execute(sql) 

            #Update pipe length 
            sql="UPDATE temp.dhc_lines set length=ST_Length(geom);"
            print(sql) 
            self.cur.execute(sql) 
            
    def insertJunctionConnections(self):
        "insert node connections into table junction_connections   "
        sql="""INSERT INTO temp.junction_connections (nid,lid) SELECT j.id ,l.id FROM temp.dhc_junctions j,temp.dhc_lines l WHERE St_DWithIn(j.geom,l.geom,0.001);"""
        #print(sql) 
        self.cur.execute(sql)
        
    def insertCustomerConnections(self):
        "insert customer connections into table customer_connections"
        sql="""INSERT INTO temp.customer_connections (cid,lid,c_seq) SELECT c.id, l.id, 1 FROM temp.dhc_customers c,temp.dhc_lines l WHERE St_DWithIn(c.geom,l.geom,0.001);"""
        #print(sql) 
        self.cur.execute(sql)
        
    def insertPlantConnections(self,version):
        "insert energy_plant connections  into table energy_plant_connections"
        sql="""INSERT INTO temp.energy_plant_connections (epid,lid,ep_seq) SELECT ep.id,l.id, 1 FROM {}.dhc_energy_plants ep,temp.dhc_lines l WHERE St_DWithIn(ep.geom,l.geom,0.001);""".format(version)
        #print(sql) 
        self.cur.execute(sql)
        
    def updateJunctionConnections(self):
        "UPDATE node connections: n_connections & conn_type"
        print("UPDATE node connections: n_connections & conn_type")
        sql="""UPDATE temp.dhc_junctions SET n_connections=jc.connections FROM (SELECT count(*) AS connections,nid FROM temp.junction_connections GROUP BY nid) jc WHERE jc.nid=id;"""
        #print(sql) 
        self.cur.execute(sql)
        sql="""UPDATE temp.dhc_junctions SET assetgroup=4 WHERE n_connections=3;"""
        self.cur.execute(sql)
        
        sql="""WITH sub AS(
    WITH sub AS(
        SELECT jc.nid,conn_t_conns.connection_id AS id
            FROM temp.junction_connections jc, temp.dhc_lines l, public.line_assettypes la, public.connection_type_connections conn_t_conns
            WHERE l.id=jc.lid AND la.assettype=l.assettype AND la.conn_type=conn_t_conns.connection_type_id 
            GROUP BY jc.nid,conn_t_conns.connection_id 
            ORDER BY jc.nid,conn_t_conns.connection_id
    )
    SELECT nid, array_agg(id) AS ids FROM sub GROUP BY nid
)
UPDATE temp.dhc_junctions SET conn_type = conn_t_conns.connection_type_id
    FROM sub, (SELECT conn_t_conns.connection_type_id, array_agg(c.id ORDER BY c.id) AS ids
                    FROM public.connections c, public.connection_type_connections conn_t_conns
                    WHERE conn_t_conns.connection_id=c.id 
                    GROUP BY conn_t_conns.connection_type_id
                    ORDER BY conn_t_conns.connection_type_id) conn_t_conns
    WHERE id=sub.nid AND conn_t_conns.ids=sub.ids;"""
        print(sql)
        self.cur.execute(sql)
    
    def getAndCheckConnType(self,conn_types):
        counter=0
        conn_type=[]
        for i in conn_types:
            if counter==0:
                conn_type=conn_types[i]
            else:
                for c_t in conn_type:
                   if c_t not in conn_types[i]:
                        conn_type.remove(c_t)
            counter+=1
        if conn_type:
           return conn_type[0]
        else:
           return []
       
    def mergeLines(self):
        "merge lines and delete nodes with 2 connections"
        print("merge lines")
        i=10000000
        flag=True
        while flag==True:
            sql="SELECT nc.nid AS jid, nc.lid FROM temp.dhc_junctions j, temp.junction_connections nc WHERE j.n_connections=2 AND j.id=nc.nid ORDER BY j.id LIMIT 2;"
            #print(sql)
            self.cur.execute(sql) 
            junction_conn=self.cur.fetchall()
            if junction_conn:
                i+=1
                jid=junction_conn[0]['jid']
                lid1=junction_conn[0]['lid']
                lid2=junction_conn[1]['lid']
                #print(str(lid1)+";"+str(lid2))
                #snap line strings, because inaccurancies can occur in the topology
                sql="""INSERT INTO temp.dhc_lines (id,assetgroup,assettype,geom,length,pipe_bundle_type_id,network)
                        SELECT {},0,l1.assettype,
                            ST_LineMerge(St_Union((st_dump(st_split(st_snap(l1.geom,l2.geom,st_distance(l1.geom,l2.geom)*1.001),l2.geom))).geom,l2.geom)) AS geom,
                            ST_Length(ST_LineMerge(St_Union((st_dump(st_split(st_snap(l1.geom,l2.geom,st_distance(l1.geom,l2.geom)*1.001),l2.geom))).geom,l2.geom))),
                            l1.pipe_bundle_type_id,l1.network
                        FROM temp.dhc_lines l1, temp.dhc_lines l2
                        WHERE l1.id={} and l2.id={}
                        ORDER BY ST_Length((st_dump(st_split(l1.geom,l2.geom))).geom)DESC LIMIT 1;""".format(i,lid1,lid2)                                              
                #print(sql)
                self.cur.execute(sql) 
                sql="UPDATE temp.junction_connections SET lid="+str(i)+" WHERE lid IN ("+str(lid1)+","+str(lid2)+");"
                #print(sql)
                self.cur.execute(sql) 
                sql="UPDATE temp.customer_connections SET lid="+str(i)+" WHERE lid IN ("+str(lid1)+","+str(lid2)+");"
                #print(sql)
                self.cur.execute(sql) 
                sql="UPDATE temp.energy_plant_connections SET lid="+str(i)+" WHERE lid IN ("+str(lid1)+","+str(lid2)+");"
                #print(sql)
                self.cur.execute(sql) 
                sql="DELETE FROM temp.dhc_lines WHERE id IN ("+str(lid1)+","+str(lid2)+");"
                #print(sql)
                self.cur.execute(sql) 
                sql="DELETE FROM temp.dhc_junctions WHERE id="+str(jid)+";"
                #print(sql)
                self.cur.execute(sql) 
                sql="DELETE FROM temp.junction_connections WHERE nid="+str(jid)+";"
                #print(sql)
                self.cur.execute(sql) 
            else:
                flag=False
        
    def deleteUnconnectedCustomers(self,version):
        sql="""DELETE FROM temp.dhc_customers c WHERE id NOT IN (SELECT c.id FROM temp.dhc_customers c, temp.dhc_lines l WHERE St_DWithIn(c.geom,l.geom,0.001));"""
        #print(sql) 
        self.cur.execute(sql)
        
    def insertNodes(self,version):
        sql="""INSERT INTO temp.dhc_junctions (geom,assetgroup,network)
                SELECT ST_Force3D(v.the_geom),1,{}
                    FROM temp.dhc_lines l 
                    INNER JOIN temp.streets_help_vertices_pgr v ON St_DWithIn(v.the_geom,l.geom,0.001) 
                    WHERE v.id not in(
                            SELECT v.id FROM temp.streets_help_vertices_pgr v JOIN temp.dhc_customers c ON St_DWithIn(v.the_geom,c.geom,0.001)  
                            UNION 
                            SELECT v.id FROM temp.streets_help_vertices_pgr v JOIN {}.dhc_energy_plants ep ON St_DWithIn(v.the_geom,ep.geom,0.001) 
                            )
                    GROUP BY v.id ORDER BY v.id;""".format(self.network,version)
        #print(sql) 
        self.cur.execute(sql)        
        
    def getPlants(self,version):
        sql="""SELECT ep.id epid, st_v.id::integer AS v_ep FROM {}.dhc_energy_plants ep, temp.streets_help_vertices_pgr st_v WHERE ST_dwithin(ep.geom,st_v.the_geom,0.01);""".format(version)
        #print(sql) 
        self.cur.execute(sql)   
        return self.cur.fetchall()   
        
    def prepareDB_pipeLaying(self,version):
        self.cur.execute("""DROP TABLE IF EXISTS temp.dhc_junctions;
DROP TABLE IF EXISTS temp.dhc_lines;
DROP TABLE IF EXISTS temp.dhc_lines_cooling;
DROP TABLE IF EXISTS temp.dhc_lines_heating;
DROP TABLE IF EXISTS temp.dhc_customers;
CREATE TABLE temp.dhc_customers (LIKE {}.dhc_customers INCLUDING constraints);
CREATE SEQUENCE temp.dhc_customers_id_seq OWNED BY temp.dhc_customers.id;
ALTER TABLE temp.dhc_customers ALTER COLUMN id SET DEFAULT nextval('temp.dhc_customers_id_seq');
CREATE TABLE temp.dhc_junctions (LIKE {}.dhc_junctions INCLUDING constraints);
CREATE SEQUENCE temp.dhc_junctions_id_seq OWNED BY temp.dhc_junctions.id;
ALTER TABLE temp.dhc_junctions ALTER COLUMN id SET DEFAULT nextval('temp.dhc_junctions_id_seq');
CREATE TABLE temp.dhc_lines (LIKE {}.dhc_lines INCLUDING constraints);
CREATE SEQUENCE temp.dhc_lines_id_seq OWNED BY temp.dhc_lines.id;
ALTER TABLE temp.dhc_lines ALTER COLUMN id SET DEFAULT nextval('temp.dhc_lines_id_seq');
CREATE TABLE temp.dhc_lines_heating (LIKE {}.dhc_lines INCLUDING constraints);
CREATE SEQUENCE temp.dhc_lines_heating_id_seq OWNED BY temp.dhc_lines_heating.id;
ALTER TABLE temp.dhc_lines_heating ALTER COLUMN id SET DEFAULT nextval('temp.dhc_lines_heating_id_seq');
CREATE TABLE temp.dhc_lines_cooling (LIKE {}.dhc_lines INCLUDING constraints);
CREATE SEQUENCE temp.dhc_lines_cooling_id_seq OWNED BY temp.dhc_lines_cooling.id;
ALTER TABLE temp.dhc_lines_cooling ALTER COLUMN id SET DEFAULT nextval('temp.dhc_lines_cooling_id_seq');""".format(version,version,version,version,version))
        self.cur.execute("""TRUNCATE temp.dhc_customers, temp.dhc_lines_cooling, temp.dhc_lines_heating, temp.dhc_lines CASCADE;""")
        self.cur.execute("""INSERT INTO temp.dhc_customers SELECT * FROM {}.dhc_customers; """.format(version))
    
    def prepareDB_pipeLaying_modeTables(self,version):
        self.cur.execute("""TRUNCATE temp.streets_help, temp.dhc_junctions, temp.customer_connections, temp.junction_connections, temp.energy_plant_connections, temp.device_connections CASCADE;""")
        self.cur.execute("""INSERT INTO temp.streets_help (geom) SELECT geom FROM {}.streets; """.format(version))
        self.cur.execute("""DROP TABLE IF EXISTS {}.segment_lines_00;""".format(version))
        self.cur.execute("""DROP TABLE IF EXISTS {}.segment_lines_01;""".format(version))
        
    def connectPlantsStreet(self,version,mode):            
        "insert energy plant connections into streets_help"
        #add plant connection restrictions
        plantConnConstr="" 
        if mode=='heating':
            plantConnConstr=plantConnConstr+" AND ep.tsup_h_deg >= " + self.tsup_max
        if mode=='cooling':
            plantConnConstr=plantConnConstr+" AND ep.tsup_c_deg <= " + self.tsup_min
            
        sql="""With sub AS(
            	SELECT Min(ST_Length(ST_MakeLine(ST_ClosestPoint(st.geom,ST_Force2D(ep.geom)),ST_Force2D(ep.geom)))) AS min_dist FROM temp.streets_help st, {}.dhc_energy_plants ep WHERE {}=ANY(ep.network) GROUP BY ep.id
            )
            INSERT INTO temp.streets_help(geom) 
            	SELECT ST_MakeLine(ST_ClosestPoint(st.geom,ST_Force2D(ep.geom)),ST_Force2D(ep.geom))
            	FROM sub, temp.streets_help st, {}.dhc_energy_plants ep
            	WHERE ST_Length(ST_MakeLine(ST_ClosestPoint(st.geom,ST_Force2D(ep.geom)),ST_Force2D(ep.geom)))=sub.min_dist {};""".format(version,self.network,version,plantConnConstr)
        #print("""insert energy plant connections: {}""".format(sql));
        self.cur.execute(sql);

    def customerConnConstr(self,mode):
        customerConnConstr="" 
        if mode=='heating':
            customerConnConstr=customerConnConstr+" AND c.tsup_h_deg <= "+self.tsup_max + " AND c.heat_e_kwh >= "+self.heat_demand_min+" AND c.heat_p_kw >= "+self.heating_load_min
        if mode=='cooling':
            customerConnConstr=customerConnConstr+" AND c.tsup_c_deg >= "+self.tsup_min + " AND c.heat_e_kwh >= "+self.cold_demand_min+" AND c.heat_p_kw >= "+self.cooling_load_min
        return customerConnConstr

    def connectCustomersStreet(self,version,mode):            
        "insert customer plant connections into streets_help"
        #add customer connection restrictions
        customerConnConstr=self.customerConnConstr(mode)
        
        if self.customer_connection_mode=='shortest-way-connection': 
            #print('shortest-way-connection')
            sql="""With sub AS(
                    SELECT Min(ST_Length(ST_MakeLine(ST_ClosestPoint(st.geom,ST_Force2D(c.geom)),ST_Force2D(c.geom)))) AS min_dist FROM temp.streets_help st, temp.dhc_customers c WHERE {}=ANY(c.network)GROUP BY c.id 
                )
                INSERT INTO temp.streets_help(geom) 
                    SELECT ST_MakeLine(ST_ClosestPoint(st.geom,ST_Force2D(c.geom)),ST_Force2D(c.geom))
                    FROM sub, temp.streets_help st, temp.dhc_customers c
                    WHERE ST_Length(ST_MakeLine(ST_ClosestPoint(st.geom,ST_Force2D(c.geom)),ST_Force2D(c.geom)))=sub.min_dist {};""".format(self.network,customerConnConstr)
            #print("""insert customer connections: {}""".format(sql))
            self.cur.execute(sql)
        if self.customer_connection_mode=='loop-in-connection':  
            sql="""SELECT count(id) AS numberofid FROM temp.dhc_customers;""";
            #print("""insert customer connections: {}""".format(sql))
            self.cur.execute(sql)
            numberofid =self.cur.fetchone()['numberofid']
            #print(numberofid)
            for i in range(0,numberofid):
                sql="""With sub AS(
                        With sub AS(
                            		SELECT c.id AS id, Max(heat_e_kwh / ST_Length(ST_MakeLine(ST_ClosestPoint(st.geom,ST_Force2D(c.geom)),ST_Force2D(c.geom)))) AS min_dist FROM temp.streets_help st, temp.dhc_customers c WHERE c.id NOT IN (SELECT c.id FROM temp.streets_help st,temp.dhc_customers c WHERE st_dwithin(c.geom,st.geom,0.001)) GROUP BY c.id ORDER BY min_dist DESC LIMIT 1
                            	)
                            	SELECT min(st_length(ST_MakeLine(ST_ClosestPoint(st.geom,ST_Force2D(c.geom)),ST_Force2D(c.geom)))) AS length,sub.id FROM temp.streets_help st, temp.dhc_customers c, sub WHERE c.id=sub.id GROUP BY sub.id
                            )
                            INSERT INTO temp.streets_help(geom) 
                            	SELECT ST_MakeLine(ST_ClosestPoint(st.geom,ST_Force2D(c.geom)),ST_Force2D(c.geom)) AS line
                            		FROM sub, temp.dhc_customers c, temp.streets_help st
                            		WHERE ST_length(ST_MakeLine(ST_ClosestPoint(st.geom,ST_Force2D(c.geom)),ST_Force2D(c.geom)))=sub.length AND c.id=sub.id {};""".format(customerConnConstr)
                #print("""insert customer connections: {}""".format(sql))
                self.cur.execute(sql)
                
    def generateTopology(self,version):
        sql="DROP SCHEMA IF EXISTS streets_help_topo CASCADE;"
        self.cur.execute(sql)    
        #print(sql)
        sql="CREATE EXTENSION IF NOT EXISTS postgis_topology;"
        self.cur.execute(sql)    
        #print(sql)
        sql="TRUNCATE topology.topology CASCADE;"
        self.cur.execute(sql)    
        #print(sql)
        sql="""SELECT topology.CreateTopology('streets_help_topo', {});""".format(self.srid)
        self.cur.execute(sql)    
        #print(sql) 
        sql="ALTER TABLE temp.streets_help DROP COLUMN IF EXISTS topo_geom;"
        self.cur.execute(sql)    
        #print(sql) 
        sql="SELECT topology.AddTopoGeometryColumn('streets_help_topo','temp','streets_help','topo_geom','LINESTRING');"
        self.cur.execute(sql)    
        #print(sql)
        sql="UPDATE temp.streets_help SET topo_geom = topology.toTopoGeom(geom,'streets_help_topo',1,0.001);"
        self.cur.execute(sql)    
        #print(sql)
        sql="TRUNCATE temp.streets_help;"
        #print(sql)
        self.cur.execute(sql)    
        sql="INSERT INTO temp.streets_help (geom) SELECT geom FROM streets_help_topo.edge_data;"
        #print(sql)  
        self.cur.execute(sql)    
        sql="""WITH sub AS(
                SELECT geom, costs_eur7m as costs FROM {}.streets
            )
            UPDATE temp.streets_help sh SET costs_eur7m=sub.costs FROM sub WHERE St_dWithin(ST_LineSubString(sh.geom,0.001,0.999),sub.geom,0.0001);""".format(version)
        print(sql)  
        self.cur.execute(sql)   
        #drop table streets_help_vertices_pgr       
        sql="DROP TABLE IF EXISTS temp.streets_help_vertices_pgr CASCADE;"
        self.cur.execute(sql)    
        #print(sql)                     
        #create network topology
        sql="select pgr_createTopology('temp.streets_help',.001,'geom','id',clean:='true');"
        self.cur.execute(sql)    
        print(sql)   
            
        sql="UPDATE temp.streets_help SET length_m=st_length(geom);"
        self.cur.execute(sql)    
        #print(sql)   
               
    def networkHelp(self,version,plants,mode):
        #reate table network_help-> contains all shortest path customer connections to the energy plant network (shortet way connections of the plants), which doesn`t depend on heating demand;
        sql="DROP TABLE IF EXISTS temp.network_help;"
        self.cur.execute(sql)    
        #print(sql)  
            
        sql="""CREATE TABLE temp.network_help
                (
                    id serial NOT NULL,
                    lid integer,
                    cid integer,
                    epid integer,
                    geom geometry(LineString,{}),
                    pipe_length numeric,
                    hull_id integer DEFAULT 144,
                    nominalpipediameter numeric DEFAULT 0.1,
                    CONSTRAINT network_help_pkey PRIMARY KEY (id)
                )
                WITH (
                    OIDS=FALSE
                );
                ALTER TABLE temp.network_help
                    OWNER TO postgres;""".format(self.srid)
        self.cur.execute(sql)    
        #print(sql) 
              
        for plant in plants:
            v_ep=plant['v_ep']
            epid=plant['epid']
            sql="""SELECT c.id AS cid,st_v.id::integer as v_c FROM temp.dhc_customers c, temp.streets_help_vertices_pgr st_v WHERE st_dwithin(c.geom,st_v.the_geom,0.01) AND {}=ANY(c.network);""".format(self.network)
            #print(sql) 
            self.cur.execute(sql)
            if mode=='heating':
                if self.check_heating_network_costs:
                    costs="""length_m*(costs_eur7m + {}*{}*{})""".format(self.heat_loss,self.heat_costs,self.amortization_period_heat) 
                else:
                    costs='length_m'
            if mode=='cooling':
                if self.check_cooling_network_costs:
                    costs="""length_m*(costs_eur7m + {}*{}*{})""".format(self.cold_loss,self.cold_costs,self.amortization_period_cold) 
                else:
                    costs='length_m'
            for customer in self.cur.fetchall():
                v_c=customer['v_c']
                cid=customer['cid']
                sql="""WITH sub As(
                    	SELECT seq, node, edge, cost
                    				FROM pgr_dijkstra(
                    					'SELECT id, source, target, {} as cost FROM temp.streets_help',
                    					{},
                    					{},
                    					false
                    			       )
                    )
                    INSERT INTO temp.network_help (lid,cid,epid,geom ,pipe_length) SELECT st.id,{},{}, st.geom,st_length(geom) FROM sub,temp.streets_help st  WHERE sub.edge>0 AND st.id=sub.edge;""".format(costs,v_ep,v_c,cid,epid)
                #print(sql) 
                self.cur.execute(sql)  
            
    def connectPlantsNetwork(self,version,plants,mode):
        "connect energy plants"
        sid_count=0
        isid_first=0
        if mode=='heating':
            assettype= self.heating_lines_assettype
        if mode=='cooling':
            assettype= self.cooling_lines_assettype
            
        for plant in plants:
            sid=plant['v_ep']
            sid_count=sid_count+1
            if sid_count==1:
                sid_first=sid;
            else:
                sql="""WITH sub AS(
                    	SELECT seq, node, edge, cost
                    				FROM pgr_dijkstra(
                    					'SELECT id, source, target, length_m as cost FROM temp.streets_help',
                    					{},
                    					{},
                    					false
                    			       )
                    )
                    INSERT INTO temp.dhc_lines_{} (id,assetgroup,assettype,geom,length)
                    	SELECT st.id,0,{},ST_Force3D(st.geom),St_Length(st.geom)
                    		FROM sub, temp.streets_help st WHERE st.id=sub.edge AND st.id NOT IN (SELECT id FROM temp.dhc_lines_{});""".format(sid_first,sid,mode,assettype,mode)
                #print(sql) 
                self.cur.execute(sql)   
        
    def connectCustomersNetwork(self,version,mode,connectionModes):
        """connect customers to the energy plants regarding the shortest way; 
        consider constraints; 
        connect one customer after another ranked by linear heat density;
        look first if the connection of a single customer is enough; 
        otherwise look for combined connections;
        look only in the tree with most propability (highest heat density)"""
        print('Connect customers')

        if mode=='heating':
            pathConstrColumn='heat_e_kwh'
            customerConnConstrPath=" AND sub.energydensity >= "+self.linearHeatDensity_min
            linearEnergyDensity=float(self.linearHeatDensity_min)
            assettype= self.heating_lines_assettype
        if mode=='cooling':    
            pathConstrColumn='cool_e_kwh'
            customerConnConstrPath=" AND sub.energydensity >= "+self.linearColdDensity_min
            linearEnergyDensity=float(self.linearColdDensity_min)
            assettype= self.cooling_lines_assettype
            
        customerConnConstr=self.customerConnConstr(mode)
        
        count_old=0
        flag=True
        sql="""SELECT count(*) AS count_customers FROM temp.dhc_customers;"""
        self.cur.execute(sql)  
        customer_sum=self.cur.fetchone()['count_customers']
        if len(connectionModes)==2 and mode=='heating':
            progress_mode=2
            customer_count=0
        else:
            progress_mode=1
            customer_count=customer_sum
            customer_sum *=2
            
        while flag==True:
            flag=False
            #prove single connection
            while flag==False:
                while self.is_paused: #pause algorithm
                    time.sleep(0.1)
                    if self.is_killed: #abort algorithm, but finish network topology with existing pipes
                        print('abort pipe laying')
                        self.finishNetworkTopology(version)
                if self.is_killed: #abort algorithm, but finish network topology with existing pipes
                    print('abort pipe laying')
                    self.finishNetworkTopology(version)
                    
                sql="""SELECT count(*) AS count_pipes FROM temp.dhc_lines_{};""".format(mode)
                #print(sql) 
                self.cur.execute(sql)  
                count_old=self.cur.fetchone()['count_pipes']
                pipe_bundle_type_id=2
                #insert pipes into dhc_lines with the highest energydensity
                sql="""With sub AS(
                    	SELECT c.id AS cid, nh.epid, c.{},sum(st_length(nh.geom)) as length, c.{}/sum(st_length(nh.geom)) as energydensity
                    		FROM temp.dhc_customers c, temp.network_help nh 
                    		WHERE c.id NOT IN (SELECT c.id FROM temp.dhc_lines_{} l,temp.dhc_customers c WHERE st_dwithin(c.geom,l.geom,0.001)) {} AND nh.cid=c.id AND nh.lid NOT IN (SELECT id FROM temp.dhc_lines_{})
                    		GROUP BY c.id, c.{}, nh.epid
                    		ORDER BY energydensity DESC LIMIT 1 
                    )
                    INSERT INTO temp.dhc_lines_{} (id,assetgroup,assettype,geom,length,pipe_bundle_type_id)
                    	SELECT nh.lid,0,{},ST_Force3D(nh.geom),St_Length(nh.geom),{}
                    		FROM sub, temp.network_help nh
                    		WHERE nh.cid=sub.cid AND nh.lid NOT IN (SELECT id FROM temp.dhc_lines_{}) AND nh.epid=sub.epid {}
                    		GROUP BY nh.lid,nh.geom;""".format(pathConstrColumn,pathConstrColumn,mode,customerConnConstr,mode,pathConstrColumn,mode,assettype,pipe_bundle_type_id,mode,customerConnConstrPath)
                print(sql) 
                self.cur.execute(sql) 
                sql="""SELECT count(*) AS count_pipes FROM temp.dhc_lines_{};""".format(mode)
                #print(sql) 
                self.cur.execute(sql)  
                count=self.cur.fetchone()['count_pipes']
                if count==count_old:
                    flag=True
                    #print("""single connection not successful ; count={}""".format(count))
                else:
                    customer_count += 1
                    self.progress_value= int(customer_count / customer_sum / progress_mode * 100)
                    self.signals.progress.emit(self.progress_value)
                    print("""single connection successful ; count={}""".format(count))
                count_old=count
            flag=False
            
            #look for combined connections with two or more customer
            #print("look for combined connections with two or more customer")
            count=0
            #cid with the highest linear energy density per tree!!!
            #loop over connected trees
            sql="""	SELECT nh.lid
                		FROM temp.network_help nh, temp.dhc_lines_{} l
                		WHERE nh.lid NOT IN (SELECT id FROM temp.dhc_lines_{}) AND St_dWithIn(nh.geom,l.geom,0.001)
                		GROUP BY nh.lid;""".format(mode,mode)
            #print(sql) 
            self.cur.execute(sql)  
            trees=self.cur.fetchall()
            counter_tree=0
            while counter_tree<len(trees) and flag==False:
                tree=trees[counter_tree]
                counter_tree += 1
                lid=tree['lid']
                #print(lid) 
                #Select customer with highest energy density from customers in tree
                sql="""WITH sub AS(
                    	SELECT nh.cid FROM temp.network_help nh 
                    		WHERE nh.lid = {}
                    		GROUP BY nh.cid
                    )
                    SELECT c.id AS cid, c.{} AS energy
                    	FROM temp.dhc_customers c, sub, temp.network_help nh
                    	WHERE sub.cid=c.id AND nh.cid = sub.cid AND nh.lid NOT IN (SELECT id FROM temp.dhc_lines_{}) AND nh.epid IN (SELECT epid FROM temp.network_help WHERE lid = {} GROUP BY epid)
                    	GROUP BY c.id,c.{},nh.epid
                    	ORDER BY c.{}/sum(st_length(nh.geom)) DESC
                    	LIMIT 1;""".format(lid,pathConstrColumn,mode,lid,pathConstrColumn,pathConstrColumn)
                #print(sql) 
                self.cur.execute(sql)  
                
                energy=0
                length=0
                customer=self.cur.fetchone()
                cid=customer['cid']
                #print("----------cid = "+str(cid));
                cids=str(cid)
                energy=customer['energy']
                #get combined customers ordered by energy density
                sql="""WITH sub AS(
                    	SELECT nh1.cid,nh.epid
                    		FROM temp.network_help nh, temp.network_help nh1 
                    		WHERE nh.epid IN (SELECT nh.epid FROM temp.network_help nh WHERE nh.cid={} AND nh.id NOT IN (SELECT id FROM temp.dhc_lines_{}) GROUP BY nh.epid ORDER BY sum(St_length(nh.geom)) LIMIT 1) AND 
                    			nh.cid={} AND nh1.geom=nh.geom AND nh1.cid!=nh.cid AND nh1.lid NOT IN (SELECT id FROM temp.dhc_lines_{}) AND nh1.cid NOT IN (SELECT c.id AS cid FROM temp.dhc_lines_{} l, temp.dhc_customers c WHERE St_dWithIn(c.geom,l.geom,0.001))
                    		GROUP BY nh1.cid,nh.epid
                    )
                    SELECT sub.cid, c.{} AS energy, nh.epid
                    	FROM sub, temp.network_help nh, temp.dhc_customers c 
                    	WHERE c.id=nh.cid AND 
                    		nh.cid=sub.cid AND 
                    		nh.id NOT IN(SELECT id FROM temp.network_help WHERE cid={}) AND
                    		nh.epid=sub.epid AND
                    		nh.lid NOT IN (SELECT id FROM temp.dhc_lines_{})
                    	GROUP BY sub.cid,c.{}, nh.epid\
                    	ORDER BY c.{}/Sum(St_Length(nh.geom)) DESC;""".format(cid,mode,cid,mode,mode,pathConstrColumn,cid,mode,pathConstrColumn,pathConstrColumn)
                #print(sql) 
                self.cur.execute(sql)  
                customers=self.cur.fetchall()
                counter_customers=0
                # sum up energy and calculate total length of all customers
                while counter_customers<len(customers) and flag==False:
                    customer=customers[counter_customers]
                    counter_customers += 1
                    cid=customer['cid']
                    cids += ","+str(cid)
                    epid=customer['epid']
                    energy += customer['energy']
                    sql="""WITH sub AS(
                        	SELECT St_length(nh.geom) AS length
                        		FROM temp.network_help nh
                        		WHERE nh.cid in ({}) AND 
                        			nh.lid NOT IN (SELECT id FROM temp.dhc_lines_{}) AND
                        			nh.epid={}
                        		GROUP BY nh.geom,nh.lid
                        )
                        SELECT sum(length) AS length FROM sub;""".format(cids,mode,epid)
                    #print(sql) 
                    self.cur.execute(sql)  
                    length=self.cur.fetchone()['length']
                    #print(energy)
                    #print(length)
                    #print(float(energy)/float(length))
                    if float(energy)/float(length) >= linearEnergyDensity:
                        flag=True
                        print("    flag combined="+str(flag)+" ; cid="+str(cid))
                        sql="INSERT INTO temp.dhc_lines_"+mode+" (id,assetgroup,assettype,geom,length) SELECT nh.lid,0,"+self.heating_lines_assettype+", ST_Force3D(nh.geom),St_Length(nh.geom) FROM temp.network_help nh WHERE nh.epid="+str(epid)+" AND nh.cid IN ("+cids+") AND nh.lid NOT IN (SELECT id FROM temp.dhc_lines_"+mode+") GROUP BY nh.lid,nh.geom;";
                        #print(sql) 
                        self.cur.execute(sql) 
                        customer_count += 1
                        self.progress_value= int(customer_count / customer_sum / progress_mode * 100)
                        self.signals.progress.emit(self.progress_value)
                        
    def transformNetworksIntoHC(self):
        sql="""INSERT INTO temp.dhc_lines (geom, assetgroup, assettype,pipe_bundle_type_id,length,network)
                SELECT lh.geom, 0, {} AS assettype,1,lh.length,{} FROM temp.dhc_lines_heating lh LEFT JOIN temp.dhc_lines_cooling lc ON lh.geom=lc.geom WHERE lc.geom IS NULL
                UNION ALL
                SELECT lh.geom, 0, {} AS assettype,2,lh.length,{} FROM temp.dhc_lines_heating lh INNER JOIN temp.dhc_lines_cooling lc ON lh.geom=lc.geom 
                UNION ALL
                SELECT lc.geom, 0, {} AS assettype,1,lc.length,{} FROM temp.dhc_lines_heating lh RIGHT JOIN temp.dhc_lines_cooling lc ON lh.geom=lc.geom WHERE lh.geom IS NULL;""".format(self.heating_lines_assettype,self.network,self.hc_lines_assettype,self.network,self.cooling_lines_assettype,self.network)
        #print(sql) 
        self.cur.execute(sql)    