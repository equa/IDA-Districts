from plugins.utility_functions.db import *
from plugins.utility_functions.topology import *
from plugins.utility_functions.error_handling import *
from plugins.utility_functions.layer_visualization import *
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
from qgis.utils import iface



class GenerateNetworkTopologySignals(QObject):
    progress=pyqtSignal(int)
    error=pyqtSignal(str)

class WorkerGenerateNetworkTopology(QRunnable):
    """Worker thread
    Inherits from QRunnable to handle worker thread setup, signals and wrap-up."""
    def __init__(self,*args,**kwargs):
        super().__init__()
        self.args=args
        print(args)
        self.signals=GenerateNetworkTopologySignals()
        self.dictDB=kwargs['dictDB']
        self.conn=""
        self.cur=""
        self.inserted_nids=[]
        self.iface=kwargs['iface']
        self.plugin_dir=kwargs['plugin_dir']
        self.deleteUnconnectedCustomers=kwargs['deleteUnconnectedCustomers']
        self.deleteUnconnectedLines=kwargs['deleteUnconnectedLines']
        self.connectCustomers=kwargs['connectCustomers']
        self.connectCustomers_assettype_lines=kwargs['connectCustomers_assettype_lines']
        self.connectCustomers_assettype_pipeBundle=kwargs['connectCustomers_assettype_pipeBundle']
        self.connectPlants=kwargs['connectPlants']
        self.connectPlants_assettype_lines=kwargs['connectPlants_assettype_lines']
        self.connectPlants_assettype_pipeBundle=kwargs['connectPlants_assettype_pipeBundle']
        self.addCustomers=kwargs['addCustomers']
        self.addCustomers_assettype_customers=kwargs['addCustomers_assettype_customers']
        self.deleteUnconnectedNetworkEnds=kwargs['deleteUnconnectedNetworkEnds']
        self.keepAssettypes=kwargs['keepAssettypes']
        self.overrideAssettypes=kwargs['overrideAssettypes']
        self.overrideAssettypes_customers=kwargs['overrideAssettypes_customers']
        self.overrideAssettypes_lines=kwargs['overrideAssettypes_lines']
        self.overrideAssettypes_pipeBundle=kwargs['overrideAssettypes_pipeBundle']
        self.tolerance=kwargs['tolerance']
        self.redraw_submodels_polygons=kwargs['redraw_submodels_polygons']
        self.networks=kwargs['networks']
        if not self.networks:
            iface.messageBar().pushMessage("Info", "Please select one or more network id`s!", level=Qgis.Info)
        self.conn = dbConnect(self.dictDB,True)
        if self.conn:
            self.cur=self.conn.cursor(cursor_factory = psycopg2.extras.RealDictCursor)
            self.networks=checkGenerateTopologyLayerData(self.dictDB,self.cur,self.networks,self.connectPlants,self.connectCustomers)
          
    @pyqtSlot()
    def run(self):
        print('Generate network topology')
        self.progress_value=1
        self.signals.progress.emit(self.progress_value)

        if self.networks and self.conn:
            srid=loadProjectConfig(self.plugin_dir,self.dictDB['projectName'])['srid']
            
            setSubnetwork(self.cur,self.dictDB,self.redraw_submodels_polygons,srid)
            self.prepareDB_pipeLaying_modeTables(self.dictDB['versionName'],srid)

            #split lines per device, plant, junction and customer
            self.splitLinesPerDevicesPlantsJunctionsCustomers(self.dictDB['versionName'],'dhc_devices')
            self.splitLinesPerDevicesPlantsJunctionsCustomers(self.dictDB['versionName'],'dhc_energy_plants')
            self.splitLinesPerDevicesPlantsJunctionsCustomers(self.dictDB['versionName'],'dhc_customers')
        
            print(self.networks)
            progress_value=1
            n_networks=len(self.networks)
            print(n_networks)
            for network in self.networks:
                print('*************')
                print(network)
                print(progress_value)
                
                if self.generateTopology(self.dictDB['versionName'],srid,network):
                    return
                progress_value+=20/n_networks
                print(int(progress_value))
                self.signals.progress.emit(int(progress_value))
                if self.deleteUnconnectedNetworkEnds:
                    self.deleteNetworkEnds(network)
                progress_value+=4/n_networks
                print(int(progress_value))
                self.signals.progress.emit(int(progress_value))
                if self.addCustomers:
                    self.insertCustomerToEnds(self.dictDB['versionName'],network)
                progress_value+=10/n_networks
                print(int(progress_value))
                self.signals.progress.emit(int(progress_value))
                print(self.deleteUnconnectedCustomers)
                if self.deleteUnconnectedCustomers:
                    self.delUnconnCust()
                progress_value+=5/n_networks
                self.signals.progress.emit(int(progress_value))
                print(self.deleteUnconnectedLines)
                if self.deleteUnconnectedLines:
                    self.delUnconnLines()
                progress_value+=5/n_networks
                self.signals.progress.emit(int(progress_value))
                checkLineDirectionTopology(self.cur,self.dictDB['versionName'],self.tolerance,self.iface,network)
                progress_value+=20/n_networks
                self.signals.progress.emit(int(progress_value))
                self.insertLinesFromTopology(self.dictDB['versionName'],network)
                progress_value+=5/n_networks
                self.signals.progress.emit(int(progress_value))
                self.insertJunctions(self.dictDB['versionName'],network)
                progress_value+=5/n_networks
                self.signals.progress.emit(int(progress_value))
                print(int(progress_value))
                progress_value=self.finishNetworkTopology(self.dictDB['versionName'],network,progress_value,n_networks,srid)
            
            uri = QgsDataSourceUri()
            uri.setConnection(self.dictDB['host'], self.dictDB['port'], self.dictDB['projectName'], self.dictDB['user'], self.dictDB['pwd'])
            print(uri)
            self.signals.progress.emit(95)
            print('finished pipe laying')
            try:
                showTempTables(uri,self.dictDB,self.plugin_dir,self.iface,self.cur)
            except:
                print('Show temp layers failed')
            self.signals.progress.emit(100)
            self.cur.close()
            self.conn.close()    

                    
    def delUnconnCust(self):
        """Delete unconnected customers """
        sql="""DELETE FROM temp.dhc_customers WHERE id NOT IN (SELECT c.id FROM temp.dhc_customers c, temp.streets_help sth WHERE ST_dWithIn(c.geom,sth.geom,{}));""".format(self.tolerance)
        print(sql)
        self.cur.execute(sql)
        
    def delUnconnLines(self):
        """Delete unconnected lines """
        sql="""DELETE FROM temp.streets_help WHERE id NOT IN (
    SELECT sth1.id FROM temp.streets_help sth1, temp.streets_help sth2 
        WHERE ST_dWithIn(sth1.geom,sth2.geom,{}) AND sth1.id != sth2.id
        GROUP BY sth1.id);""".format(self.tolerance)
        print(sql)
        self.cur.execute(sql)
        
    def insertLinesFromTopology(self,version,network):
        """ INSERT Lines from topology"""
        sql="INSERT INTO temp.dhc_lines (geom,assetgroup,assettype,pipe_bundle_type_id,network) SELECT ST_Force3D(geom),assetgroup,assettype,pipe_bundle_type_id,{} FROM temp.streets_help;".format(network)
        print(sql)
        self.cur.execute(sql)
    
    def deleteNetworkEnds(self,network):
        """Delete lines from network ends (1 connection in vertices table) if there is no customers or plant or device"""
        print('delete unconnected network ends')
        sql="""WITH sub AS( --get vertices id`s and count it
    WITH sub AS( 
        SELECT source AS id,count(source) AS connections FROM temp.streets_help GROUP BY source
        UNION ALL   
        SELECT target AS id,count(target) AS connections FROM temp.streets_help GROUP BY target
    )SELECT id,sum(connections) AS conn_counter FROM sub GROUP BY id
)
SELECT sub.id FROM sub,temp.streets_help_vertices_pgr shv 
    WHERE sub.conn_counter=1 AND shv.id=sub.id AND sub.id NOT IN (
        SELECT shv.id FROM temp.streets_help_vertices_pgr shv,temp.dhc_customers c,{}.dhc_energy_plants ep
            WHERE ST_dWithIN(shv.the_geom,c.geom,{}) OR ST_dWithIN(shv.the_geom,ep.geom,{}) AND {} = ANY(c.network)
            GROUP BY shv.id);""".format(self.dictDB['versionName'],self.tolerance,self.tolerance,network)
        print(sql)
        self.cur.execute(sql)      
        vertex_ids=','.join([str(i['id']) for i in self.cur.fetchall()])
        print(vertex_ids)
        if vertex_ids:
            #delete lines in street_help  
            sql="""DELETE FROM temp.streets_help WHERE source IN ({}) OR target IN ({});""".format(vertex_ids,vertex_ids)
            print(sql)
            self.cur.execute(sql)
            #delete vertixes in streets_help_vertices_pgr
            sql="""DELETE FROM temp.streets_help_vertices_pgr shv WHERE id IN ({});""".format(vertex_ids,vertex_ids)
            print(sql)
            self.cur.execute(sql)     

    def insertCustomerToEnds(self,version,network):
        """Insert customers at network ends (1 connection in vertices table) if there is no customers or plant"""
        sql="""WITH sub AS( --get vertices id`s and count it
	WITH sub AS( 
		SELECT source AS id,count(source) AS connections FROM temp.streets_help GROUP BY source 
		UNION ALL   
		SELECT target AS id,count(target) AS connections FROM temp.streets_help GROUP BY target 
	)SELECT id,sum(connections) AS conn FROM sub GROUP BY id
)
INSERT INTO temp.dhc_customers(geom,assetgroup,assettype,network) 
	SELECT ST_Force3D(shv.the_geom),1,{},{} FROM sub,temp.streets_help_vertices_pgr shv 
		WHERE sub.conn=1 AND shv.id=sub.id AND sub.id NOT IN (
            SELECT shv.id FROM temp.streets_help_vertices_pgr shv,temp.dhc_customers c,{}.dhc_energy_plants ep 
                WHERE ST_dWithIN(shv.the_geom,c.geom,{}) OR ST_dWithIN(shv.the_geom,ep.geom,{})
                GROUP BY shv.id);""".format(self.addCustomers_assettype_customers,network,version,self.tolerance,self.tolerance)
        print(sql)
        self.cur.execute(sql)
    
    def updateLength(self):
        """Update the length of temp.dhc_lines"""
        sql="UPDATE temp.dhc_lines set length= ST_Length(geom);"
        self.cur.execute(sql)
        
    def finishNetworkTopology(self,version,network,progress_value,n_networks,srid):
        progress_value+=1/n_networks
        self.signals.progress.emit(int(progress_value))
        self.insertJunctionConnections(network)
        progress_value+=2/n_networks
        self.signals.progress.emit(int(progress_value))
        self.insertCustomerConnections(network)
        progress_value+=2/n_networks
        self.signals.progress.emit(int(progress_value))
        self.insertPlantConnections(version,network)
        progress_value+=3/n_networks
        self.signals.progress.emit(int(progress_value))
        self.insertDeviceConnections(version,network)
        progress_value+=3/n_networks
        self.signals.progress.emit(int(progress_value))
        self.updateJunctionConnections(network)
        progress_value+=4/n_networks
        self.signals.progress.emit(int(progress_value))
        self.mergeLines(version,network)
        self.peakPowerNoCustLines(version,network)
        progress_value+=5/n_networks
        self.signals.progress.emit(int(progress_value))
        self.updateLength()
        self.updateHeight(version,srid)
        updateSubmodels(self.cur,self.dictDB)
        return progress_value

    def removeLayers(self):
        layers = QgsProject.instance().mapLayers().values()
        for layer in layers:
            if layer.name() in ['dhc_customers_temp','dhc_lines_temp','dhc_junctions_temp']:
                QgsProject.instance().removeMapLayer(layer)
                
    def peakPowerNoCustLines(self,version,network):
        """Update the number of customers and the peak power of each line, which are supplied by the main plant"""
        sql="""UPDATE temp.dhc_lines l 
    SET no_customer=a.no_customer,
        peak_power_kw=a.heat_p_kw
    FROM (
        SELECT l.id,sum(heat_p_kw) AS heat_p_kw, count(heat_p_kw) AS no_customer
            FROM pgr_dijkstra(
                'SELECT id,source, target, length_m*costs_eur7m AS cost FROM temp.streets_help',
                (SELECT sth_v.id FROM temp.streets_help_vertices_pgr sth_v, {}.dhc_energy_plants ep WHERE {} = ANY(ep.network) AND {} = ANY (ep.main_plant) AND ST_dWithIn(sth_v.the_geom,ep.geom,0.01)), 
                (SELECT ARRAY_AGG(sth_v.id) FROM temp.streets_help_vertices_pgr sth_v, temp.dhc_customers c WHERE {} = ANY(c.network) AND ST_dWithIn(sth_v.the_geom,c.geom,0.01))) di,
                temp.dhc_customers c, temp.streets_help_vertices_pgr sth_v,temp.streets_help sth, temp.dhc_lines l
            WHERE ST_dWithIn(sth_v.the_geom,c.geom,0.01) AND sth_v.id=di.end_vid AND edge>0 AND sth.id=di.edge AND ST_dWithIn(l.geom,ST_LineSubstring(sth.geom,0.000001,0.999999),0.00000001)
            GROUP BY l.id) a
    WHERE a.id=l.id;""".format(version,network,network,network)
        print(sql)
        self.cur.execute(sql)
        
    def updateHeight(self,version,srid):
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
        SELECT j.id, t.rast,ST_Value(t.rast, 1, ST_Centroid(j.geom)) As height
            FROM {}.terrain t,temp.dhc_junctions j
            WHERE ST_dWithIn(ST_Envelope(t.rast),j.geom,{})
    ) a
    WHERE a.id=j.id;""".format(version,self.tolerance)
            print(sql) 
            self.cur.execute(sql)
            
            #Update customer height
            sql= """UPDATE temp.dhc_customers c set asl_m=a.height FROM (
        SELECT c.id, ST_Value(t.rast, 1, ST_Centroid(c.geom)) As height
            FROM {}.terrain t,temp.dhc_customers c 
            WHERE ST_dWithIn(ST_Envelope(t.rast),c.geom,{})
    ) a
    WHERE a.id=c.id;""".format(version,self.tolerance)
            print(sql) 
            self.cur.execute(sql)
            
            #Update network height
            sql="""WITH sub AS(
    WITH sub AS(    
        Select (ST_DumpPoints(geom)).path AS path,(ST_DumpPoints(geom)).geom AS geom ,id from temp.dhc_lines ORDER BY id,path
    )
    SELECT sub.id,ST_SetSrid(ST_MakeLine(ST_MakePoint(ST_X(sub.geom),ST_Y(sub.geom), ST_Value(t.rast, 1, ST_Centroid(sub.geom)))),{}) As geom
            FROM {}.terrain t,sub
            WHERE ST_dWithIn(ST_Envelope(t.rast),sub.geom,{})
            GROUP BY sub.id
)
UPDATE temp.dhc_lines g SET geom=sub.geom,
    length=ST_3DLength(sub.geom)
    FROM sub WHERE sub.id=g.id;""".format(srid,version,self.tolerance)
            print(sql) 
            self.cur.execute(sql) 
        else:
            sql="UPDATE temp.dhc_lines set length=st_3dlength(geom);"
            self.cur.execute(sql)
            
    def insertJunctionConnections(self,network):
        "insert node connections into table junction_connections   "
        sql="""INSERT INTO temp.junction_connections (nid,lid) SELECT j.id ,l.id FROM temp.dhc_junctions j,temp.dhc_lines l WHERE St_DWithIn(j.geom,l.geom,{}) AND l.network={};""".format(self.tolerance,network)
        #print(sql) 
        self.cur.execute(sql)
        
    def insertCustomerConnections(self,network):
        "insert customer connections into table customer_connections"
        sql="""INSERT INTO temp.customer_connections (cid,c_seq,lid) SELECT c.id, {}, l.id FROM temp.dhc_customers c,temp.dhc_lines l WHERE St_DWithIn(c.geom,l.geom,{}) AND l.network={};""".format(1,self.tolerance,network)
        #print(sql) 
        self.cur.execute(sql)
        
    def insertPlantConnections(self,version,network):
        "insert energy_plant connections  into table energy_plant_connections"
        sql="""INSERT INTO temp.energy_plant_connections (epid,ep_seq,lid) SELECT ep.id,{},l.id FROM {}.dhc_energy_plants ep,temp.dhc_lines l WHERE St_DWithIn(ep.geom,l.geom,{}) AND l.network={};""".format(1,version,self.tolerance,network)
        #print(sql) 
        self.cur.execute(sql)
        
    def insertDeviceConnections(self,version, network):
        "insert device connections  into table device_connections"
        sql="""INSERT INTO temp.device_connections (did,d_seq,lid) SELECT d.id,{},l.id FROM {}.dhc_devices d,temp.dhc_lines l WHERE St_DWithIn(d.geom,l.geom,{}) AND l.network={};""".format(1,version,self.tolerance,network)
        #print(sql) 
        self.cur.execute(sql)
        
    def updateJunctionConnections(self,network):
        "UPDATE node connections: n_connections & conn_type"
        print("UPDATE node connections: n_connections & conn_type")
        sql="""UPDATE temp.dhc_junctions SET n_connections=jc.connections FROM (SELECT count(*) AS connections,nid FROM temp.junction_connections GROUP BY nid) jc WHERE jc.nid=id;"""
        #print(sql) 
        self.cur.execute(sql)
        sql="""UPDATE temp.dhc_junctions SET assetgroup=4 WHERE n_connections=3;"""
        self.cur.execute(sql)
        sql="""UPDATE temp.dhc_junctions SET assetgroup=2 WHERE n_connections=1;"""
        self.cur.execute(sql)
        
        sql="""WITH sub AS(
    WITH sub AS(
        SELECT jc.nid,conn_t_conns.connection_id AS id
            FROM temp.junction_connections jc, temp.dhc_lines l, public.line_assettypes la, public.connection_type_connections conn_t_conns
            WHERE l.network={} AND l.id=jc.lid AND la.assettype=l.assettype AND la.conn_type=conn_t_conns.connection_type_id 
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
    WHERE id=sub.nid AND conn_t_conns.ids=sub.ids;""".format(network)
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
       
    def mergeLines(self,version,network):
        "merge lines and delete nodes with 2 connections"
        print("merge lines")
        self.cur.execute("SELECT last_value FROM temp.dhc_lines_id_seq;")
        i=self.cur.fetchone()['last_value']
        flag=True
        while flag==True:
            inserted_nids=','.join(str(i) for i in self.inserted_nids)
            if inserted_nids:
                inserted_nids="AND j.id NOT IN (SELECT jt.id FROM a.dhc_junctions j, temp.dhc_junctions jt WHERE st_dwithin(j.geom,jt.geom,"+self.tolerance+") AND j.id IN ("+inserted_nids+")) "
            sql="""WITH sub AS(
    SELECT nc.nid, array_agg(nc.lid) AS a
        FROM temp.dhc_junctions j, temp.junction_connections nc
        WHERE j.n_connections=2 AND j.id=nc.nid
        GROUP BY nc.nid
        ORDER BY nc.nid
)
SELECT nid AS jid,a[1] AS lid1, a[2] AS lid2 FROM sub,temp.dhc_lines l1, temp.dhc_lines l2 
    WHERE l1.id=sub.a[1] AND l2.id=sub.a[2] AND l1.pipe_bundle_type_id=l2.pipe_bundle_type_id AND l1.network={} AND l2.network={} {}
    ORDER BY nid LIMIT 1;""".format(network, network, inserted_nids)
            #print(sql)
            self.cur.execute(sql) 
            junction_conn=self.cur.fetchall()
            if junction_conn:
                i+=1
                jid=junction_conn[0]['jid']
                lid1=junction_conn[0]['lid1']
                lid2=junction_conn[0]['lid2']
                #print(str(lid1)+";"+str(lid2))
                #snap line strings, because inaccurancies can occur in the topology
                sql="""INSERT INTO temp.dhc_lines (assetgroup,assettype,geom,length,pipe_bundle_type_id,network)
    SELECT l1.assetgroup ,l1.assettype,
        ST_LineMerge(St_Union((st_dump(st_split(st_snap(l1.geom,l2.geom,{}),l2.geom))).geom,l2.geom)) AS geom,
        ST_Length(ST_LineMerge(St_Union((st_dump(st_split(st_snap(l1.geom,l2.geom,{}),l2.geom))).geom,l2.geom))),
        l1.pipe_bundle_type_id,
        {}
    FROM temp.dhc_lines l1, temp.dhc_lines l2
    WHERE l1.id={} and l2.id={}
    ORDER BY ST_Length((st_dump(st_split(l1.geom,l2.geom))).geom) DESC LIMIT 1;""".format(self.tolerance,self.tolerance,network,lid1,lid2)                                              
                #print(sql)
                self.cur.execute(sql) 
                sql="UPDATE temp.junction_connections SET lid="+str(i)+" WHERE lid IN ("+str(lid1)+","+str(lid2)+");"
                #print(sql)
                self.cur.execute(sql) 
                sql="UPDATE temp.customer_connections SET lid="+str(i)+", c_seq=1 WHERE lid IN ("+str(lid1)+","+str(lid2)+");"
                #print(sql)
                self.cur.execute(sql) 
                sql="UPDATE temp.energy_plant_connections SET lid="+str(i)+", ep_seq=1 WHERE lid IN ("+str(lid1)+","+str(lid2)+");"
                #print(sql)
                self.cur.execute(sql) 
                sql="UPDATE temp.device_connections SET lid="+str(i)+", d_seq=1 WHERE lid IN ("+str(lid1)+","+str(lid2)+");"
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
        
    def insertJunctions(self,version,network):
        sql="""INSERT INTO temp.dhc_junctions (geom,assetgroup,network)
                SELECT ST_Force3D(v.the_geom),1,{}
                    FROM temp.dhc_lines l 
                    INNER JOIN temp.streets_help_vertices_pgr v ON St_DWithIn(v.the_geom,l.geom,{}) 
                    WHERE v.id NOT IN(
                            SELECT v.id FROM temp.streets_help_vertices_pgr v JOIN temp.dhc_customers c ON St_DWithIn(v.the_geom,c.geom,{})  
                            UNION 
                            SELECT v.id FROM temp.streets_help_vertices_pgr v JOIN {}.dhc_energy_plants ep ON St_DWithIn(v.the_geom,ep.geom,{}) 
                            UNION 
                            SELECT v.id FROM temp.streets_help_vertices_pgr v JOIN {}.dhc_devices d ON St_DWithIn(v.the_geom,d.geom,{}) 
                            )
                    GROUP BY v.id ORDER BY v.id;""".format(network,self.tolerance,self.tolerance,version,self.tolerance,version,self.tolerance)
        print(sql) 
        self.cur.execute(sql)         
    
    def prepareDB_pipeLaying_modeTables(self,version,srid):
        self.cur.execute('DROP TABLE IF EXISTS temp.network_help;')
        self.cur.execute("""CREATE TABLE IF NOT EXISTS temp.network_help
(
    id serial,
    geom geometry(LineString,{}),
    assetgroup integer,
    assettype integer,
    network integer,
    pipe_bundle_type_id integer,
    length_m double precision,
    costs_eur7m numeric DEFAULT 100,
    source integer,
    target integer,
    CONSTRAINT network_help_pkey PRIMARY KEY (id)
);""".format(srid))

        self.cur.execute("""DROP TABLE IF EXISTS temp.dhc_junctions;
DROP TABLE IF EXISTS temp.dhc_lines;
DROP TABLE IF EXISTS temp.dhc_customers;
CREATE TABLE temp.dhc_customers (LIKE {}.dhc_customers INCLUDING constraints);
CREATE SEQUENCE temp.dhc_customers_id_seq OWNED BY temp.dhc_customers.id;
ALTER TABLE temp.dhc_customers ALTER COLUMN id SET DEFAULT nextval('temp.dhc_customers_id_seq');
CREATE TABLE temp.dhc_junctions (LIKE {}.dhc_junctions INCLUDING constraints);
CREATE SEQUENCE temp.dhc_junctions_id_seq OWNED BY temp.dhc_junctions.id;
ALTER TABLE temp.dhc_junctions ALTER COLUMN id SET DEFAULT nextval('temp.dhc_junctions_id_seq');
CREATE TABLE temp.dhc_lines (LIKE {}.dhc_lines INCLUDING constraints);
CREATE SEQUENCE temp.dhc_lines_id_seq OWNED BY temp.dhc_lines.id;
ALTER TABLE temp.dhc_lines ALTER COLUMN id SET DEFAULT nextval('temp.dhc_lines_id_seq');""".format(version,version,version))
        self.cur.execute("""TRUNCATE temp.network_help, temp.streets_help, temp.dhc_junctions, temp.dhc_customers, temp.customer_connections, temp.junction_connections, temp.device_connections, temp.energy_plant_connections, temp.dhc_lines CASCADE;""")

        if self.keepAssettypes:
            self.cur.execute("""INSERT INTO temp.dhc_customers SELECT * FROM {}.dhc_customers WHERE network && ARRAY[{}]; """.format(version,','.join([i for i in self.networks])))
            self.cur.execute("""INSERT INTO temp.network_help (id,geom,assetgroup,assettype,network,pipe_bundle_type_id) SELECT id,ST_Force2D(geom), assetgroup, assettype, network, pipe_bundle_type_id FROM {}.dhc_lines WHERE ST_length(geom) > {} AND network IN ({}); """.format(version,self.tolerance,','.join([i for i in self.networks])))
        else:
            self.cur.execute("""INSERT INTO temp.network_help (id,geom,assetgroup,assettype,network, pipe_bundle_type_id) SELECT id,ST_Force2D(geom), {}, {},network , {} FROM {}.dhc_lines WHERE ST_length(geom) > {} AND nh.network IN ({}); """.format(0,self.overrideAssettypes_lines,self.overrideAssettypes_pipeBundle,version,self.tolerance,','.join([i for i in self.networks])))
            self.cur.execute("""INSERT INTO temp.dhc_customers (id,geom,assetgroup,assettype,network) SELECT id,geom,{},{},network FROM {}.dhc_customers WHERE network && ARRAY[{}]; """.format(1,self.overrideAssettypes_customers,version,','.join([i for i in self.networks])))
        self.cur.execute("""SELECT setval('temp.dhc_customers_id_seq', (SELECT MAX(id) FROM temp.dhc_customers));""")
        self.cur.execute("""DROP TABLE IF EXISTS {}.segment_lines_00;""".format(version))
        self.cur.execute("""DROP TABLE IF EXISTS {}.segment_lines_01;""".format(version))
        
    def connectPlantsNetwork(self,version,network):            
        "insert energy plant connections into temp.network_help"  
        sql="""With sub AS(
    SELECT Min(ST_Length(ST_MakeLine(ST_ClosestPoint(l.geom,ST_Force2D(ep.geom)),ST_Force2D(ep.geom)))) AS min_dist 
        FROM {}.dhc_lines l, {}.dhc_energy_plants ep 
        WHERE l.network={} AND {}=ANY(ep.network)
        GROUP BY ep.id
)
INSERT INTO temp.streets_help(geom,assetgroup,assettype,pipe_bundle_type_id) 
    SELECT ST_MakeLine(ST_ClosestPoint(l.geom,ST_Force2D(ep.geom)),ST_Force2D(ep.geom)),{},{},{}
    FROM sub, {}.dhc_lines l, {}.dhc_energy_plants ep
    WHERE ST_Length(ST_MakeLine(ST_ClosestPoint(l.geom,ST_Force2D(ep.geom)),ST_Force2D(ep.geom)))=sub.min_dist and sub.min_dist>0 AND l.network={} AND {}=ANY(ep.network);""".format(
    version,version,network,network,0,self.connectPlants_assettype_lines,self.connectPlants_assettype_pipeBundle,version,version,network,network)
        print("""insert energy plant connections: {}""".format(sql))
        self.cur.execute(sql)
        
        if checkLoopInConnections(self.cur,self.dictDB['versionName'],'temp.streets_help','energy_plant'):
            self.signals.error.emit(''.join(['Energy plant :{} and energy_plant: {} have a loop in connection! '.format(i['id1'],i['id2']) for i in checkLoopInConnections(self.cur,'temp','temp.streets_help','energy_plant')]))
            return True
        
    def connectCustomersNetwork(self,version,network):            
        "insert customer connections into temp.network_help"   
        sql="""With sub AS(
    SELECT Min(ST_Length(ST_MakeLine(ST_ClosestPoint(l.geom,ST_Force2D(c.geom)),ST_Force2D(c.geom)))) AS min_dist 
        FROM {}.dhc_lines l, temp.dhc_customers c 
        WHERE l.network={} AND {} =ANY(c.network)
        GROUP BY c.id
)
INSERT INTO temp.streets_help(geom,assetgroup,assettype,pipe_bundle_type_id) 
    SELECT ST_MakeLine(ST_ClosestPoint(l.geom,ST_Force2D(c.geom)),ST_Force2D(c.geom)),{},{},{}
    FROM sub, {}.dhc_lines l, temp.dhc_customers c
    WHERE ST_Length(ST_MakeLine(ST_ClosestPoint(l.geom,ST_Force2D(c.geom)),ST_Force2D(c.geom)))=sub.min_dist AND sub.min_dist>0 AND l.network={} AND {} =ANY(c.network);""".format(version,network,network,0,self.connectCustomers_assettype_lines,self.connectCustomers_assettype_pipeBundle,version,network,network)
        print("""insert customers connections: {}""".format(sql))
        self.cur.execute(sql)
        
        if checkLoopInConnections(self.cur,'temp','temp.streets_help','customer'):
            self.signals.error.emit(''.join(['Customer :{} and customer: {} have a loop in connection! '.format(i['id1'],i['id2']) for i in checkLoopInConnections(self.cur,'temp','temp.streets_help','customer')]))
            return True

    def splitLinesPerDevicesPlantsJunctionsCustomers(self,version,mode):
        """ST_split does not work (don`t know why) that`s why: Split the lines per feature: 1) get list of features; 2) loop over features """
        sql="""SELECT nh.id AS nh_id,f.id AS f_id
    FROM {}.{} f,temp.network_help nh
    WHERE ST_dWithIn(f.geom, nh.geom,{}) AND NOT ST_Equals(St_StartPoint(nh.geom), f.geom) AND NOT ST_Equals(St_EndPoint(nh.geom), f.geom) AND nh.network = ANY (f.network);""".format(version,mode,self.tolerance)
        print(sql)
        self.cur.execute(sql)
        ids=self.cur.fetchall()
        print(ids)
        for id in ids:
            if mode=="dhc_junctions":
                self.inserted_nids.append(d_id)
            sql="""WITH sub AS(
    WITH sub AS(
        SELECT (ST_DumpPoints((ST_DumpSegments(nh.geom)).geom)).geom AS line_seg,ST_dWithIn((ST_DumpSegments(nh.geom)).geom ,ST_ClosestPoint(nh.geom,d.geom),{}) AS intersects,ST_ClosestPoint(nh.geom,d.geom) AS point,nh.assetgroup,nh.assettype, nh.network, nh.submodel, nh.pipe_bundle_type_id
            FROM {}.{} d,temp.network_help nh
            WHERE d.id={} AND nh.id={}
    )
    SELECT ST_MakeLine(line_seg,point) AS line ,ST_Length(ST_MakeLine(line_seg,point)) AS length,assetgroup,assettype, network, submodel ,pipe_bundle_type_id FROM sub WHERE intersects AND ST_Length(ST_MakeLine(line_seg,point)) > 0 ORDER BY length LIMIT 1
)
INSERT INTO temp.network_help(geom,assetgroup,assettype,network,submodel,pipe_bundle_type_id) SELECT sub.line,sub.assetgroup,sub.assettype,sub.network,sub.submodel,sub.pipe_bundle_type_id FROM sub;""".format(self.tolerance,version,mode,id['f_id'],id['nh_id'])
            print(sql)
            self.cur.execute(sql)
    
    def generateTopology(self,version,srid,network):
        #fill layer with subset of streets_help based on attribut network
        print('------------Network:{}-----------------'.format(network))
        self.cur.execute("""TRUNCATE temp.streets_help;""")
        
        sql="""INSERT INTO temp.streets_help (geom) 
    SELECT nh.geom FROM temp.network_help nh, {}.dhc_lines l 
        WHERE ST_dWithIn(nh.geom,ST_Force2D(l.geom),{}) 
            AND nh.id NOT IN (SELECT nh.id FROM temp.network_help nh, {}.dhc_lines l WHERE nh.geom=ST_Force2D(l.geom) AND l.network != {}) 
            AND l.network= {} 
            GROUP BY nh.geom;""".format(self.dictDB['versionName'],self.tolerance,self.dictDB['versionName'],network,network)   
        print(sql)
        self.cur.execute(sql) 

        if self.connectPlants:
            if self.connectPlantsNetwork(self.dictDB['versionName'],network):
                return True
        if self.connectCustomers:
            if self.connectCustomersNetwork(self.dictDB['versionName'],network):
                return True
                    
        sql="DROP SCHEMA IF EXISTS streets_help_topo CASCADE;"
        self.cur.execute(sql)    
        #print(sql)
        sql="CREATE EXTENSION IF NOT EXISTS postgis_topology;"
        self.cur.execute(sql)    
        #print(sql)
        sql="TRUNCATE topology.topology CASCADE;"
        self.cur.execute(sql)    
        #print(sql)
        sql="""SELECT topology.CreateTopology('streets_help_topo', {},{});""".format(srid,self.tolerance)
        self.cur.execute(sql)    
        #print(sql) 
        sql="ALTER TABLE temp.streets_help DROP COLUMN IF EXISTS topo_geom;"
        self.cur.execute(sql)    
        #print(sql) 
        sql="SELECT topology.AddTopoGeometryColumn('streets_help_topo','temp','streets_help','topo_geom','LINESTRING');"
        self.cur.execute(sql)    
        #print(sql)
        sql="UPDATE temp.streets_help SET topo_geom = topology.toTopoGeom(geom,'streets_help_topo',1,{});".format(self.tolerance)
        self.cur.execute(sql) 

        sql="TRUNCATE temp.streets_help;"
        #print(sql)
        self.cur.execute(sql)    
        sql="INSERT INTO temp.streets_help (geom) SELECT geom FROM streets_help_topo.edge_data;"
        #print(sql)  
        self.cur.execute(sql) 
        
        sql="""UPDATE temp.streets_help a 
    SET assetgroup=b.assetgroup,assettype=b.assettype,pipe_bundle_type_id=b.pipe_bundle_type_id
    FROM (SELECT geom,assetgroup,assettype,pipe_bundle_type_id FROM temp.network_help) b 
    WHERE St_dWithIn(b.geom,a.geom,{});""".format(self.tolerance)
        self.cur.execute(sql) 
        
        
        sql="DROP TABLE IF EXISTS temp.streets_help_vertices_pgr CASCADE;"
        self.cur.execute(sql)    
        
        sql="SELECT pgr_createTopology('temp.streets_help',{},'geom','id',clean:='true');".format(self.tolerance)
        self.cur.execute(sql)    
        #print(sql)                 
        
        #graph analyze for gaps
        sql="""SELECT pgr_analyzeGraph('temp.streets_help', {}, the_geom := 'geom', id := 'id');""".format(self.tolerance)
        print(sql)
        self.cur.execute(sql)
        
        sql="""SELECT sh.id FROM temp.streets_help_vertices_pgr v,temp.streets_help sh WHERE v.chk!=0 AND (v.id=sh.source OR v.id=sh.target);""".format(self.tolerance)
        print(sql)
        self.cur.execute(sql)
        sh_ids=self.cur.fetchall()
        print(sh_ids)
        
        if sh_ids:
            sql="""DELETE FROM temp.streets_help WHERE id IN ({});""".format(",".join([str(i['id']) for i in sh_ids]))
            print(sql)
            self.cur.execute(sql)
        
        #update geometry based on vertices table
        sql="""UPDATE temp.streets_help sh SET geom= a.geom 
    FROM (WITH sub AS(SELECT ST_SetPoint(sh.geom,0,v.the_geom) AS geom, sh.id,sh.target FROM temp.streets_help sh,temp.streets_help_vertices_pgr v WHERE sh.source=v.id)
        SELECT ST_SetPoint(sub.geom,-1,v.the_geom) AS geom, sub.id FROM sub,temp.streets_help_vertices_pgr v WHERE sub.target=v.id) a
    WHERE sh.id=a.id;"""
        print(sql)
        self.cur.execute(sql)
        
        #drop table streets_help_vertices_pgr       
        sql="DROP TABLE IF EXISTS temp.streets_help_vertices_pgr CASCADE;"
        self.cur.execute(sql)    
        #print(sql)                     
        #create network topology
        sql="SELECT pgr_createTopology('temp.streets_help',{},'geom','id',clean:='true');".format(str(0.000000000000001))
        self.cur.execute(sql)    
        #print(sql)  
        
       #graph analyze for short intersections
        sql="""SELECT pgr_analyzeGraph('temp.streets_help', {}, the_geom := 'geom', id := 'id');""".format(str(0.000000000000001))
        print(sql)
        self.cur.execute(sql)            
            
        sql="""DELETE FROM temp.streets_help sh WHERE id IN (
    SELECT sh.id FROM temp.streets_help_vertices_pgr v, temp.streets_help sh WHERE (sh.source=v.id OR sh.target=v.id) AND v.cnt=1 AND St_length(sh.geom) < {} AND v.id NOT IN(
            SELECT shv.id FROM temp.streets_help_vertices_pgr shv,temp.dhc_customers c,{}.dhc_energy_plants ep
                WHERE ST_dWithIN(shv.the_geom,c.geom,1e-15) OR ST_dWithIN(shv.the_geom,ep.geom,1e-15))
        GROUP BY sh.id
)""".format(self.tolerance,version)
        print(sql)
        self.cur.execute(sql)     
        
        if self.keepAssettypes:
            sql="""WITH sub AS(
    SELECT sth.id AS id, nh.assetgroup, nh.assettype, nh.pipe_bundle_type_id 
        FROM temp.network_help nh, temp.streets_help sth, {}.dhc_lines l
        WHERE ST_dWithIN(ST_LineSubString(sth.geom,0.45,0.55),nh.geom,{}) AND l.network={} AND ST_EQUALS(l.geom,nh.geom)
)    
UPDATE temp.streets_help sh SET assetgroup =sub.assetgroup, assettype=sub.assettype, pipe_bundle_type_id=sub.pipe_bundle_type_id FROM sub WHERE sub.id =sh.id;""".format(self.dictDB['versionName'],self.tolerance,network)
        else:
            sql="""UPDATE temp.streets_help sh SET assetgroup ={}, assettype={}, pipe_bundle_type_id={}""".format(0,self.overrideAssettypes_lines,self.overrideAssettypes_pipeBundle)
        print(sql)
        self.cur.execute(sql) 
        
        sql="UPDATE temp.streets_help SET length_m=st_length(geom);"
        self.cur.execute(sql)    
        #print(sql)   
       