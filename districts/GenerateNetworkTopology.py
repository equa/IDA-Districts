from qgis.PyQt.QtCore import Qt, QCoreApplication, QObject, QRunnable, pyqtSignal, pyqtSlot
from qgis.core import QgsAuthMethodConfig,QgsProject,QgsVectorLayer,QgsDataSourceUri,QgsCategorizedSymbolRenderer,QgsSymbol,QgsRendererCategory

from .utility_functions.db import *
from .utility_functions.files import *
from .utility_functions.topology import *
from .utility_functions.error_handling import *
from .utility_functions.layer_visualization import *

import time
import os.path
import os
import sys
import psycopg2
import psycopg2.extras
from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT



class GenerateNetworkTopologySignals(QObject):
    progress=pyqtSignal(int)
    error=pyqtSignal(str)
    finished=pyqtSignal(str)

class WorkerGenerateNetworkTopology(QRunnable):
    """Worker thread
    Inherits from QRunnable to handle worker thread setup, signals and wrap-up."""
    def __init__(self,*args,**kwargs):
        super().__init__()
        #print(kwargs)
        self.signals=GenerateNetworkTopologySignals()
        self.config=kwargs['config']
        self.conn=""
        self.cur=""
        self.inserted_jids=[]
        self.plugin_dir=kwargs['plugin_dir']
        self.deleteUnconnectedCustomers=kwargs['deleteUnconnectedCustomers']
        self.showTempTables=kwargs['showTempTables']
        self.deleteUnconnectedLines=kwargs['deleteUnconnectedLines']
        self.connectCustomers=kwargs['connectCustomers']
        self.connectCustomers_template_pipeBundle=kwargs['connectCustomers_template_pipeBundle'].split(':')
        if self.connectCustomers_template_pipeBundle:
            self.connectCustomers_template_pipeBundle=self.connectCustomers_template_pipeBundle[0]
        else:
            self.signals.error.emit('No customer template available or set!')
        self.connectPlants=kwargs['connectPlants']
        self.connectPlants_template_pipeBundle=kwargs['connectPlants_template_pipeBundle'].split(':')
        if self.connectPlants_template_pipeBundle:
            self.connectPlants_template_pipeBundle=self.connectPlants_template_pipeBundle[0]
        else:
            self.signals.error.emit('No energy plant template available or set!')
        self.addCustomers=kwargs['addCustomers']
        self.addCustomers_template_customers=kwargs['addCustomers_template_customers'].split(':')
        if self.addCustomers_template_customers:
            self.addCustomers_template_customers=self.addCustomers_template_customers[0]
        else:
            self.signals.error.emit('No customer template available or set!')
        self.deleteUnconnectedNetworkEnds=kwargs['deleteUnconnectedNetworkEnds']
        self.keepTemplates=kwargs['keepTemplates']
        self.overrideTemplates=kwargs['overrideTemplates']
        self.overrideTemplates_customers=kwargs['overrideTemplates_customers'].split(':')
        if self.overrideTemplates_customers:
            self.overrideTemplates_customers=self.overrideTemplates_customers[0]
        else:
            self.signals.error.emit('No customer template available or set!')
        self.overrideTemplates_pipeBundle=kwargs['overrideTemplates_pipeBundle'].split(':')
        if self.overrideTemplates_pipeBundle:
            self.overrideTemplates_pipeBundle=self.overrideTemplates_pipeBundle[0]
        else:
            self.signals.error.emit('No pipe bundle available or set!')
        self.tolerance=kwargs['tolerance']
        self.redraw_submodels_polygons=kwargs['redraw_submodels_polygons']
        self.networks=kwargs['networks']
        if not self.networks:
            self.signals.error.emit("Please select one or more network id`s!")
        
        auth_cfg = QgsAuthMethodConfig()
        QgsApplication.authManager().loadAuthenticationConfig(self.config["auth_id"], auth_cfg, True)

        self.password=auth_cfg.config("password")
        self.username=auth_cfg.config("username")
        
        self.conn = dbConnect(self.config,True)
        if self.conn:
            self.cur=self.conn.cursor(cursor_factory = psycopg2.extras.RealDictCursor)
            self.networks=checkGenerateTopologyLayerData(self.config,self.cur,self.networks,self.connectPlants,self.connectCustomers)
          
    @pyqtSlot()
    def run(self):
        #print('Generate network topology')
        self.progress_value=1
        self.signals.progress.emit(self.progress_value)

        if self.networks and self.conn:
            srid=loadProjectConfig(self.config,signals=self.signals)['srid']
            
            setSubnetwork(self.cur,self.config,self.redraw_submodels_polygons,srid)
            self.prepareDB_pipeLaying_modeTables(self.config['versionName'],srid)
            
            #split lines per plant, junction and customer
            self.splitLinesPerPlantsJunctionsCustomers(self.config['versionName'],'energy_plants')
            self.splitLinesPerPlantsJunctionsCustomers(self.config['versionName'],'customers')
        
            #print(self.networks)
            progress_value=1
            n_networks=len(self.networks)
            #print(n_networks)
            for network in self.networks:
                #print('*************')
                #print(network)
                
                if self.generateTopology(self.config['versionName'],srid,network):
                    return
                progress_value+=20/n_networks
                #print(int(progress_value))
                self.signals.progress.emit(int(progress_value))
                if self.deleteUnconnectedNetworkEnds:
                    self.deleteNetworkEnds(network)
                progress_value+=4/n_networks
                #print(int(progress_value))
                self.signals.progress.emit(int(progress_value))
                if self.addCustomers:
                    self.insertCustomerToEnds(self.config['versionName'],network)
                progress_value+=10/n_networks
                #print(int(progress_value))
                self.signals.progress.emit(int(progress_value))
                #print(self.deleteUnconnectedCustomers)
                if self.deleteUnconnectedCustomers:
                    self.delUnconnCust()
                progress_value+=5/n_networks
                self.signals.progress.emit(int(progress_value))
                #print(self.deleteUnconnectedLines)
                if self.deleteUnconnectedLines:
                    self.delUnconnLines()
                progress_value+=5/n_networks
                self.signals.progress.emit(int(progress_value))
                checkLineDirectionTopology(self.cur,self.config['versionName'],self.tolerance,self.signals,network)
                progress_value+=20/n_networks
                self.signals.progress.emit(int(progress_value))
                self.insertLinesFromTopology(self.config['versionName'],network)
                progress_value+=5/n_networks
                self.signals.progress.emit(int(progress_value))
                self.insertJunctions(self.config['versionName'],network)
                progress_value+=5/n_networks
                self.signals.progress.emit(int(progress_value))
                #print(int(progress_value))
                progress_value=self.finishNetworkTopology(self.config['versionName'],network,progress_value,n_networks,srid)
            
            uri = QgsDataSourceUri()
            uri.setConnection(self.config['host'], self.config['port'], self.config['projectName'], self.username, self.password)
            #print(uri)
            self.signals.progress.emit(95)
            #print('finished pipe laying')
            try:
                if self.showTempTables:
                    showTempTables(uri,self.config,self.plugin_dir,self.signals,self.cur)
            except:
                #print('Show temp layers failed')
                pass
            self.signals.progress.emit(100)
            self.signals.finished.emit('finished')
            self.cur.close()
            self.conn.close()    

                    
    def delUnconnCust(self):
        """Delete unconnected customers """
        sql="""DELETE FROM temp.customers WHERE id NOT IN (SELECT c.id FROM temp.customers c, temp.streets_help sth WHERE ST_dWithIn(c.geom,sth.geom,{}));""".format(self.tolerance) # nosec B608
        #print(sql)
        self.cur.execute(sql)
        
    def delUnconnLines(self):
        """Delete unconnected lines """
        sql="""DELETE FROM temp.streets_help WHERE id NOT IN (
    SELECT sth1.id FROM temp.streets_help sth1, temp.streets_help sth2 
        WHERE ST_dWithIn(sth1.geom,sth2.geom,{}) AND sth1.id != sth2.id
        GROUP BY sth1.id);""".format(self.tolerance) # nosec B608
        #print(sql)
        self.cur.execute(sql)
        
    def insertLinesFromTopology(self,version,network):
        """ INSERT Lines from topology"""
        sql="INSERT INTO temp.lines (id,geom,type,pipe_bundle_type_id,network,zeta) SELECT id,ST_Force3D(geom),type,pipe_bundle_type_id,{},zeta FROM temp.streets_help;".format(network) # nosec B608
        #print(sql)
        self.cur.execute(sql)
    
    def deleteNetworkEnds(self,network):
        """Delete lines from network ends (1 connection in vertices table) if there is no customers or plant"""
        #print('delete unconnected network ends')
        sql="""WITH sub AS( --get vertices id`s and count it
    WITH sub AS( 
        SELECT source AS id,count(source) AS connections FROM temp.streets_help GROUP BY source
        UNION ALL   
        SELECT target AS id,count(target) AS connections FROM temp.streets_help GROUP BY target
    )SELECT id,sum(connections) AS conn_counter FROM sub GROUP BY id
)
SELECT sub.id FROM sub,temp.streets_help_vertices_pgr shv 
    WHERE sub.conn_counter=1 AND shv.id=sub.id AND sub.id NOT IN (
        SELECT shv.id FROM temp.streets_help_vertices_pgr shv,temp.customers c,temp.energy_plants ep
            WHERE ST_dWithIN(shv.the_geom,c.geom,{}) OR ST_dWithIN(shv.the_geom,ep.geom,{}) AND {} = ANY(c.network)
            GROUP BY shv.id);""".format(self.tolerance,self.tolerance,network)  # nosec B608
        #print(sql)
        self.cur.execute(sql)      
        vertex_ids=','.join([str(i['id']) for i in self.cur.fetchall()])
        #print(vertex_ids)
        if vertex_ids:
            #delete lines in street_help  
            sql="""DELETE FROM temp.streets_help WHERE source IN ({}) OR target IN ({});""".format(vertex_ids,vertex_ids)  # nosec B608
            #print(sql)
            self.cur.execute(sql)
            #delete vertixes in streets_help_vertices_pgr
            sql="""DELETE FROM temp.streets_help_vertices_pgr shv WHERE id IN ({});""".format(vertex_ids,vertex_ids)  # nosec B608
            #print(sql)
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
INSERT INTO temp.customers(geom,template,network) 
	SELECT ST_Force3D(shv.the_geom),{},array[{}] FROM sub,temp.streets_help_vertices_pgr shv 
		WHERE sub.conn=1 AND shv.id=sub.id AND sub.id NOT IN (
            SELECT shv.id FROM temp.streets_help_vertices_pgr shv,temp.customers c,temp.energy_plants ep 
                WHERE ST_dWithIN(shv.the_geom,c.geom,{}) OR ST_dWithIN(shv.the_geom,ep.geom,{})
                GROUP BY shv.id);""".format(self.addCustomers_template_customers,network,self.tolerance,self.tolerance)  # nosec B608
        #print(sql)
        self.cur.execute(sql)
        
    def finishNetworkTopology(self,version,network,progress_value,n_networks,srid):
        progress_value+=1/n_networks
        self.signals.progress.emit(int(progress_value))
        self.insertJunctionConnections(network)
        progress_value+=2/n_networks
        self.signals.progress.emit(int(progress_value))
        self.insertCustomerConnections(network)
        progress_value+=4/n_networks
        self.signals.progress.emit(int(progress_value))
        self.insertPlantConnections(version,network)
        progress_value+=4/n_networks
        self.signals.progress.emit(int(progress_value))
        self.updateJunctionConnections(network)
        progress_value+=4/n_networks
        self.signals.progress.emit(int(progress_value))
        self.mergeLines(version,network)
        progress_value+=5/n_networks
        self.signals.progress.emit(int(progress_value))
        self.updateHeight(version,srid)
        updateSubmodels(self.cur,self.config)
        return progress_value

    def removeLayers(self):
        layers = QgsProject.instance().mapLayers().values()
        for layer in layers:
            if layer.name() in [tr('@default','customers')+' temp.',tr('@default','lines')+' temp.',tr('@default','junctions')+' temp.',tr('@default','energy_plants')+' temp.']:
                QgsProject.instance().removeMapLayer(layer)     
        
    def updateHeight(self,version,srid):
        "update the height of the network, junctions and customers based on raster layer"
        sql = """SELECT EXISTS (
    SELECT 1
    FROM   information_schema.tables 
    WHERE  table_schema = '{}'
    AND    table_name = 'terrain'
    ) AS exists;""".format(version)  # nosec B608
        #print(sql) 
        self.cur.execute(sql)
        if self.cur.fetchone()['exists']==True:
            #print('Height layer exists')
            #print('Update point layers')
            for f in ['customers','energy_plants']:
                #Update customer height
                sql= """UPDATE temp.{} f set geom=ST_MakePoint(ST_X(geom),ST_Y(geom),a.height) FROM (
    WITH sub AS(
        WITH sub AS(
            SELECT ST_srid(rast) AS rast_srid FROM "{}".terrain LIMIT 1
        )
        SELECT id,geom, ST_Transform(geom,sub.rast_srid) AS geom_trans FROM sub,temp.{}
    )
    SELECT sub.id,ST_Value(rast, sub.geom_trans) As height
                FROM sub, "{}".terrain
                WHERE ST_dWithIn(ST_Envelope(rast),sub.geom_trans,10e-8)
                GROUP BY sub.id,height
                ORDER BY sub.id
    ) a
    WHERE f.id=a.id;""".format(f,version,f,version)  # nosec B608
                #print(sql) 
                self.cur.execute(sql)
            
            #Update network height
            sql="""WITH sub AS(
    SELECT a.id,ST_SetSrid(ST_MakeLine(ST_MakePoint(ST_X(a.geom),ST_Y(a.geom), ST_Value(t.rast, 1, a.geom_trans))),{}) As geom
            FROM 
                "{}".terrain t,
                (
                    WITH sub AS(
                        SELECT ST_srid(rast) AS rast_srid FROM "{}".terrain LIMIT 1
                    )
                    SELECT id,(ST_DumpPoints(geom)).geom AS geom,ST_Transform((ST_DumpPoints(geom)).geom,sub.rast_srid) AS geom_trans From temp.lines,sub ORDER BY id
                ) a
            WHERE ST_dWithIn(ST_Envelope(rast),a.geom_trans,10e-8)
            GROUP BY a.id
)
UPDATE temp.lines l SET geom=sub.geom
    FROM sub WHERE sub.id=l.id;""".format(srid,version,version)  # nosec B608
            #print(sql) 
            self.cur.execute(sql) 
        else:
            #Keep network height of previous topology
            sql="""Update temp.lines temp 
    SET geom=l.geom
    FROM (SELECT geom FROM {}.lines) l
    WHERE ST_Equals(ST_Force2D(l.geom),ST_Force2D(temp.geom));""".format(version)  # nosec B608
            #print(sql) 
            self.cur.execute(sql)  # nosec B608
            
    def insertJunctionConnections(self,network):
        "insert node connections into table junction_connections   "
        sql="""INSERT INTO temp.junction_connections (jid,lid) SELECT j.id ,l.id FROM temp.junctions j,temp.lines l WHERE St_DWithIn(j.geom,l.geom,{}) AND l.network={};""".format(self.tolerance,network) # nosec B608
        #print(sql) 
        self.cur.execute(sql)
        
    def insertCustomerConnections(self,network):
        "insert customer connections into table customer_connections"
        sql="""INSERT INTO temp.customer_connections (cid,c_seq,lid) SELECT c.id, {}, l.id FROM temp.customers c,temp.lines l WHERE St_DWithIn(c.geom,l.geom,{}) AND l.network={};""".format(1,self.tolerance,network) # nosec B608
        #print(sql) 
        self.cur.execute(sql)
        
    def insertPlantConnections(self,version,network):
        "insert energy_plant connections  into table energy_plant_connections"
        sql="""INSERT INTO temp.energy_plant_connections (epid,ep_seq,lid) SELECT ep.id,{},l.id FROM temp.energy_plants ep,temp.lines l WHERE St_DWithIn(ep.geom,l.geom,{}) AND l.network={};""".format(1,self.tolerance,network) # nosec B608
        #print(sql) 
        self.cur.execute(sql)
        
    def updateJunctionConnections(self,network):
        "UPDATE node connections: n_connections & conn_type"
        #print("UPDATE node connections: n_connections & conn_type")
        sql="""UPDATE temp.junctions SET n_connections=jc.connections FROM (SELECT count(*) AS connections,jid FROM temp.junction_connections GROUP BY jid) jc WHERE jc.jid=id;"""
        #print(sql) 
        self.cur.execute(sql)
        sql="""UPDATE temp.junctions SET type=4 WHERE n_connections=3;"""
        self.cur.execute(sql)
        sql="""UPDATE temp.junctions SET type=2 WHERE n_connections=1;"""
        self.cur.execute(sql)
        sql="""UPDATE temp.junctions a SET zeta=b.zeta FROM (SELECT zeta,geom FROM {}.junctions) b WHERE ST_dWithin(a.geom,b.geom,{});""".format(self.config['versionName'],self.tolerance) # nosec B608
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
        #print("merge lines")
        self.cur.execute("""SELECT setval('temp.lines_id_seq', (SELECT MAX(id) FROM temp.lines));""")
        self.cur.execute("SELECT last_value FROM temp.lines_id_seq;")
        i=self.cur.fetchone()['last_value']
        flag=True
        while flag==True:
            inserted_jids=','.join(str(j) for j in self.inserted_jids)
            if inserted_jids:
                inserted_jids="AND j.id NOT IN (SELECT jt.id FROM a.junctions j, temp.junctions jt WHERE st_dwithin(j.geom,jt.geom,"+self.tolerance+") AND j.id IN ("+inserted_jids+")) "  # nosec B608
            sql="""WITH sub AS(
    SELECT nc.jid, array_agg(nc.lid) AS a
        FROM temp.junctions j, temp.junction_connections nc
        WHERE j.n_connections=2 AND j.id=nc.jid
        GROUP BY nc.jid
        ORDER BY nc.jid
)
SELECT jid,a[1] AS lid1, a[2] AS lid2 FROM sub,temp.lines l1, temp.lines l2 
    WHERE l1.id=sub.a[1] AND l2.id=sub.a[2] AND l1.pipe_bundle_type_id=l2.pipe_bundle_type_id AND l1.network={} AND l2.network={} {}
    ORDER BY jid LIMIT 1;""".format(network, network, inserted_jids) # nosec B608
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
                sql="""INSERT INTO temp.lines (type,geom,pipe_bundle_type_id,network,zeta)
    SELECT l1.type ,
        ST_LineMerge(St_Union(l1.geom,l2.geom)) AS geom,
        l1.pipe_bundle_type_id,
        {},
        COALESCE(l1.zeta,0) + COALESCE(l2.zeta,0)
    FROM temp.lines l1, temp.lines l2
    WHERE l1.id={} and l2.id={}
    ORDER BY ST_Length((st_dump(st_split(l1.geom,l2.geom))).geom) DESC LIMIT 1;""".format(network,lid1,lid2) # nosec B608                                       
                #print(sql)
                self.cur.execute(sql) 
                sql="UPDATE temp.junction_connections SET lid="+str(i)+" WHERE lid IN ("+str(lid1)+","+str(lid2)+");" # nosec B608
                #print(sql)
                self.cur.execute(sql) 
                sql="UPDATE temp.customer_connections SET lid="+str(i)+", c_seq=1 WHERE lid IN ("+str(lid1)+","+str(lid2)+");" # nosec B608
                #print(sql)
                self.cur.execute(sql) 
                sql="UPDATE temp.energy_plant_connections SET lid="+str(i)+", ep_seq=1 WHERE lid IN ("+str(lid1)+","+str(lid2)+");" # nosec B608
                #print(sql)
                self.cur.execute(sql) 
                sql="DELETE FROM temp.lines WHERE id IN ("+str(lid1)+","+str(lid2)+");" # nosec B608
                #print(sql)
                self.cur.execute(sql) 
                sql="DELETE FROM temp.junctions WHERE id="+str(jid)+";" # nosec B608
                #print(sql)
                self.cur.execute(sql) 
                sql="DELETE FROM temp.junction_connections WHERE jid="+str(jid)+";" # nosec B608
                #print(sql)
                self.cur.execute(sql) 

            else:
                flag=False
        
    def insertJunctions(self,version,network):
        sql="""INSERT INTO temp.junctions (geom,type,network)
                SELECT ST_Force3D(v.the_geom),1,{}
                    FROM temp.lines l 
                    INNER JOIN temp.streets_help_vertices_pgr v ON St_DWithIn(v.the_geom,l.geom,{}) 
                    WHERE v.id NOT IN(
                            SELECT v.id FROM temp.streets_help_vertices_pgr v JOIN temp.customers c ON St_DWithIn(v.the_geom,c.geom,{})  
                            UNION 
                            SELECT v.id FROM temp.streets_help_vertices_pgr v JOIN temp.energy_plants ep ON St_DWithIn(v.the_geom,ep.geom,{}) 
                            )
                    GROUP BY v.id ORDER BY v.id;""".format(network,self.tolerance,self.tolerance,self.tolerance) # nosec B608
        #print(sql) 
        self.cur.execute(sql)         
    
    def prepareDB_pipeLaying_modeTables(self,version,srid):
        self.cur.execute('DROP TABLE IF EXISTS temp.network_help;')
        self.cur.execute("""CREATE TABLE IF NOT EXISTS temp.network_help
(
    id serial,
    geom geometry(LineString,{}),
    type integer,
    network integer,
    pipe_bundle_type_id integer,
    zeta numeric,
    length_m double precision,
    costs_eur7m numeric DEFAULT 100,
    source integer,
    target integer,
    CONSTRAINT network_help_pkey PRIMARY KEY (id)
);""".format(srid)) # nosec B608

        self.cur.execute("""DROP TABLE IF EXISTS temp.junctions;
DROP TABLE IF EXISTS temp.lines;
DROP TABLE IF EXISTS temp.customers;
DROP TABLE IF EXISTS temp.energy_plants;
CREATE TABLE temp.customers (LIKE "{}".customers INCLUDING constraints);
CREATE SEQUENCE temp.customers_id_seq OWNED BY temp.customers.id;
ALTER TABLE temp.customers ALTER COLUMN id SET DEFAULT nextval('temp.customers_id_seq');
CREATE TABLE temp.energy_plants (LIKE "{}".energy_plants INCLUDING constraints);
CREATE SEQUENCE temp.energy_plants_id_seq OWNED BY temp.energy_plants.id;
ALTER TABLE temp.energy_plants ALTER COLUMN id SET DEFAULT nextval('temp.energy_plants_id_seq');
CREATE TABLE temp.junctions (LIKE"{}".junctions INCLUDING constraints);
CREATE SEQUENCE temp.junctions_id_seq OWNED BY temp.junctions.id;
ALTER TABLE temp.junctions ALTER COLUMN id SET DEFAULT nextval('temp.junctions_id_seq');
CREATE TABLE temp.lines (LIKE "{}".lines INCLUDING constraints);
CREATE SEQUENCE temp.lines_id_seq OWNED BY temp.lines.id;
ALTER TABLE temp.lines ALTER COLUMN id SET DEFAULT nextval('temp.lines_id_seq');""".format(version,version,version,version,version,version)) # nosec B608
        self.cur.execute("""TRUNCATE temp.network_help, temp.streets_help, temp.junctions, temp.customers, temp.customer_connections, temp.junction_connections, temp.energy_plant_connections, temp.lines CASCADE;""")

        if self.keepTemplates:
            self.cur.execute("""INSERT INTO temp.customers SELECT * FROM "{}".customers WHERE network && ARRAY[{}]; """.format(version,','.join([i for i in self.networks]))) # nosec B608
            self.cur.execute("""INSERT INTO temp.network_help (id,geom,type,network,pipe_bundle_type_id,zeta) SELECT id,ST_Force2D(geom),type , network, pipe_bundle_type_id, zeta FROM "{}".lines WHERE ST_length(geom) > {} AND network IN ({}); """.format(version,self.tolerance,','.join([i for i in self.networks]))) # nosec B608
        else:
            self.cur.execute("""INSERT INTO temp.network_help (id,geom,type,network, pipe_bundle_type_id,zeta) SELECT id,ST_Force2D(geom),type,network , {}, zeta FROM "{}".lines WHERE ST_length(geom) > {} AND network IN ({}); """.format(self.overrideTemplates_pipeBundle,version,self.tolerance,','.join([i for i in self.networks]))) # nosec B608
            field_names=''.join([','+i for i in getLayerAttributesName(layerName=tr('@default','customers')) if i not in ['id','geom','template','network']])
            self.cur.execute("""INSERT INTO temp.customers (id,geom,template,network{}) SELECT id,geom,{},network{} FROM "{}".customers WHERE network && ARRAY[{}]; """.format(field_names,self.overrideTemplates_customers,field_names,version,','.join([i for i in self.networks]))) # nosec B608
        self.cur.execute("""INSERT INTO temp.energy_plants SELECT * FROM "{}".energy_plants WHERE network && ARRAY[{}]; """.format(version,','.join([i for i in self.networks]))) # nosec B608
        self.cur.execute("""SELECT setval('temp.customers_id_seq', (SELECT MAX(id) FROM temp.customers));""")
        self.cur.execute("""DROP TABLE IF EXISTS "{}".segment_lines_00;""".format(version)) # nosec B608
        self.cur.execute("""DROP TABLE IF EXISTS "{}".segment_lines_01;""".format(version)) # nosec B608
        
    def connectPlantsNetwork(self,version,network):            
        "insert energy plant connections into temp.network_help"  
        sql="""With sub AS(
    SELECT Min(ST_Length(ST_MakeLine(ST_ClosestPoint(l.geom,ST_Force2D(ep.geom)),ST_Force2D(ep.geom)))) AS min_dist 
        FROM "{}".lines l, temp.energy_plants ep 
        WHERE l.network={} AND {}=ANY(ep.network)
        GROUP BY ep.id
)
SELECT ST_MakeLine(ST_ClosestPoint(l.geom,ST_Force2D(ep.geom)),ST_Force2D(ep.geom)) as geom
    FROM sub, "{}".lines l, temp.energy_plants ep
    WHERE ST_Length(ST_MakeLine(ST_ClosestPoint(l.geom,ST_Force2D(ep.geom)),ST_Force2D(ep.geom)))=sub.min_dist and sub.min_dist>0 AND l.network={} AND {}=ANY(ep.network);""".format(version,network,network,version,network,network) # nosec B608
        #print("""insert energy plant connections: {}""".format(sql))
        self.cur.execute(sql)
        ep_lines=self.cur.fetchall()
        
        if ep_lines:
            sql='\n'.join(["""INSERT INTO temp.streets_help(geom) VALUES ('{}');""".format(i['geom']) for i in ep_lines]) # nosec B608
            self.cur.execute(sql)
        
        if checkLoopInConnections(self.cur,self.config['versionName'],'temp.streets_help','energy_plant'):
            self.signals.error.emit(''.join(['Energy plant :{} has a loop in connection! '.format(i['id']) for i in checkLoopInConnections(self.cur,'temp','temp.streets_help','energy_plant')]))
            return False
        return ep_lines
        
    def connectCustomersNetwork(self,version,network):            
        "insert customer connections into temp.network_help"   
        sql="""With sub AS(
    SELECT Min(ST_Length(ST_MakeLine(ST_ClosestPoint(l.geom,ST_Force2D(c.geom)),ST_Force2D(c.geom)))) AS min_dist 
        FROM "{}".lines l, temp.customers c 
        WHERE l.network={} AND {} =ANY(c.network)
        GROUP BY c.id
)
SELECT ST_MakeLine(ST_ClosestPoint(l.geom,ST_Force2D(c.geom)),ST_Force2D(c.geom)) as geom
    FROM sub, "{}".lines l, temp.customers c
    WHERE ST_Length(ST_MakeLine(ST_ClosestPoint(l.geom,ST_Force2D(c.geom)),ST_Force2D(c.geom)))=sub.min_dist AND sub.min_dist>0 AND l.network={} AND {} =ANY(c.network);""".format(version,network,network,version,network,network) # nosec B608
        #print("""insert customers connections: {}""".format(sql))
        self.cur.execute(sql)
        customer_lines=self.cur.fetchall()
        
        if customer_lines:
            sql='\n'.join(["""INSERT INTO temp.streets_help(geom) VALUES ('{}');""".format(i['geom']) for i in customer_lines]) # nosec B608
            self.cur.execute(sql)

        if checkLoopInConnections(self.cur,'temp','temp.streets_help','customer'):
            self.signals.error.emit(''.join(['Customer :{} has a loop in connection! '.format(i['id']) for i in checkLoopInConnections(self.cur,'temp','temp.streets_help','customer')]))
            return False
        return customer_lines

    def splitLinesPerPlantsJunctionsCustomers(self,version,mode):
        """ST_split does not work (don`t know why) that`s why: Split the lines per feature: 1) get list of features; 2) loop over features """
        sql="""SELECT nh.id AS nh_id,f.id AS f_id
    FROM "{}".{} f,temp.network_help nh
    WHERE ST_dWithIn(f.geom, nh.geom,{}) AND NOT ST_dWithIn(St_StartPoint(nh.geom), f.geom,{}) AND NOT ST_dWithIn(St_EndPoint(nh.geom), f.geom,{}) AND nh.network = ANY (f.network);""".format(version,mode,self.tolerance,self.tolerance,self.tolerance) # nosec B608
        #print(sql)
        self.cur.execute(sql)
        ids=self.cur.fetchall()
        #print(ids)
        setSeqIdToMax('temp.network_help_id_seq','temp.network_help','id',self.cur)
        for id in ids:
            if mode=="junctions":
                self.inserted_jids.append(d_id)
            sql="""WITH sub AS(
    WITH sub AS(
        SELECT (ST_DumpPoints((ST_DumpSegments(nh.geom)).geom)).geom AS line_seg,ST_dWithIn((ST_DumpSegments(nh.geom)).geom ,ST_ClosestPoint(nh.geom,d.geom),{}) AS intersects,ST_ClosestPoint(nh.geom,d.geom) AS point,nh.type, nh.network, nh.pipe_bundle_type_id
            FROM "{}".{} d,temp.network_help nh
            WHERE d.id={} AND nh.id={}
    )
    SELECT ST_MakeLine(line_seg,point) AS line ,ST_Length(ST_MakeLine(line_seg,point)) AS length,type, network ,pipe_bundle_type_id FROM sub WHERE intersects AND ST_Length(ST_MakeLine(line_seg,point)) > 0 ORDER BY length LIMIT 1
)
INSERT INTO temp.network_help(geom,type,network,pipe_bundle_type_id) SELECT sub.line,sub.type,sub.network,sub.pipe_bundle_type_id FROM sub;""".format(self.tolerance,version,mode,id['f_id'],id['nh_id']) # nosec B608
            #print(sql)
            self.cur.execute(sql)
    
    def generateTopology(self,version,srid,network):
        #fill layer with subset of streets_help based on attribut network
        #print('------------Network:{}-----------------'.format(network))
        self.cur.execute("""TRUNCATE temp.streets_help;""")
        
        sql="""INSERT INTO temp.streets_help (geom) 
    SELECT nh.geom FROM temp.network_help nh, "{}".lines l 
        WHERE ST_dWithIn(nh.geom,ST_Force2D(l.geom),{}) 
            AND nh.id NOT IN (SELECT nh.id FROM temp.network_help nh, "{}".lines l WHERE nh.geom=ST_Force2D(l.geom) AND l.network != {}) 
            AND l.network= {} 
            GROUP BY nh.geom;""".format(self.config['versionName'],self.tolerance,self.config['versionName'],network,network) # nosec B608
        #print(sql)
        self.cur.execute(sql) 

        if self.connectPlants:
            ep_lines=self.connectPlantsNetwork(self.config['versionName'],network)
        if self.connectCustomers:
            customer_lines=self.connectCustomersNetwork(self.config['versionName'],network)
                    
        sql="DROP SCHEMA IF EXISTS streets_help_topo CASCADE;"
        self.cur.execute(sql)    
        #print(sql)
        sql="CREATE EXTENSION IF NOT EXISTS postgis_topology;"
        self.cur.execute(sql)    
        #print(sql)
        sql="TRUNCATE topology.topology CASCADE;"
        self.cur.execute(sql)    
        #print(sql)
        sql="""SELECT topology.CreateTopology('streets_help_topo', {},{});""".format(srid,self.tolerance) # nosec B608
        self.cur.execute(sql)    
        #print(sql) 
        sql="ALTER TABLE temp.streets_help DROP COLUMN IF EXISTS topo_geom;"
        self.cur.execute(sql)    
        #print(sql) 
        sql="SELECT topology.AddTopoGeometryColumn('streets_help_topo','temp','streets_help','topo_geom','LINESTRING');"
        self.cur.execute(sql)    
        #print(sql)
        sql="UPDATE temp.streets_help SET topo_geom = topology.toTopoGeom(geom,'streets_help_topo',1,{});".format(self.tolerance) # nosec B608
        self.cur.execute(sql) 

        sql="TRUNCATE temp.streets_help;"
        #print(sql)
        self.cur.execute(sql)    
        sql="INSERT INTO temp.streets_help (geom,type) SELECT geom,{} FROM streets_help_topo.edge_data;".format(0) # nosec B608
        #print(sql)  
        self.cur.execute(sql) 
        
        if self.connectCustomers and customer_lines: 
            sql="""UPDATE temp.streets_help a 
    SET pipe_bundle_type_id={}
    FROM (SELECT * FROM (VALUES {}) AS temp(geom)) b
    WHERE st_dwithin(ST_LineSubstring(a.geom,0.1,0.9),b.geom::geometry,{});""".format(self.connectCustomers_template_pipeBundle,','.join(["('"+str(i['geom'])+"')" for i in customer_lines]),self.tolerance) # nosec B608
            #print(sql)
            self.cur.execute(sql) 
        
        if self.connectPlants and ep_lines: 
            sql="""UPDATE temp.streets_help a 
    SET pipe_bundle_type_id={}
    FROM (SELECT * FROM (VALUES {}) AS temp(geom)) b
    WHERE st_dwithin(ST_LineSubstring(a.geom,0.1,0.9),b.geom::geometry,{});""".format(self.connectPlants_template_pipeBundle,','.join(["('"+str(i['geom'])+"')" for i in ep_lines]),self.tolerance) # nosec B608
            #print(sql)
            self.cur.execute(sql) 
            
        sql="""UPDATE temp.streets_help a 
    SET type=b.type,pipe_bundle_type_id=b.pipe_bundle_type_id,zeta=b.zeta
    FROM (SELECT id,geom,type,pipe_bundle_type_id,zeta FROM temp.network_help) b 
    WHERE St_dWithIn(b.geom,ST_LineSubstring (a.geom,0.1,0.9),{});""".format(self.tolerance) # nosec B608
        #print(sql)
        self.cur.execute(sql) 
        
        sql="""WITH sub AS (
    SELECT a.id,b.id as new_id
        FROM temp.streets_help a ,(SELECT id,geom FROM temp.network_help) b 
        WHERE a.geom=b.geom
)
UPDATE temp.streets_help a SET id = sub.new_id 
    FROM sub
    WHERE a.id = sub.id AND NOT EXISTS (SELECT 1 FROM temp.streets_help a WHERE a.id = sub.new_id);"""
        #print(sql)
        self.cur.execute(sql) 
        
        sql="DROP TABLE IF EXISTS temp.streets_help_vertices_pgr CASCADE;"
        self.cur.execute(sql)    
        
        sql="SELECT pgr_createTopology('temp.streets_help',{},'geom','id',clean:='true');".format(self.tolerance) # nosec B608
        #print(sql)                 
        self.cur.execute(sql)    
        
        #graph analyze for gaps
        #sql="""SELECT pgr_analyzeGraph('temp.streets_help', {}, the_geom := 'geom', id := 'id');""".format(self.tolerance)
        #print(sql)
        self.cur.execute(sql)
        
        sql="""SELECT sh.id FROM temp.streets_help_vertices_pgr v,temp.streets_help sh WHERE v.chk!=0 AND (v.id=sh.source OR v.id=sh.target);""".format(self.tolerance) # nosec B608
        #print(sql)
        self.cur.execute(sql)
        sh_ids=self.cur.fetchall()
        #print(sh_ids)
        
        if sh_ids:
            sql="""DELETE FROM temp.streets_help WHERE id IN ({});""".format(",".join([str(i['id']) for i in sh_ids])) # nosec B608
            #print(sql)
            self.cur.execute(sql)
        
        #update geometry based on vertices table
        sql="""UPDATE temp.streets_help sh SET geom= a.geom 
    FROM (WITH sub AS(SELECT ST_SetPoint(sh.geom,0,v.the_geom) AS geom, sh.id,sh.target FROM temp.streets_help sh,temp.streets_help_vertices_pgr v WHERE sh.source=v.id)
        SELECT ST_SetPoint(sub.geom,-1,v.the_geom) AS geom, sub.id FROM sub,temp.streets_help_vertices_pgr v WHERE sub.target=v.id) a
    WHERE sh.id=a.id;"""
        #print(sql)
        self.cur.execute(sql)
        
        #drop table streets_help_vertices_pgr       
        sql="DROP TABLE IF EXISTS temp.streets_help_vertices_pgr CASCADE;"
        self.cur.execute(sql)    
        #print(sql)                     
        #create network topology
        sql="SELECT pgr_createTopology('temp.streets_help',{},'geom','id',clean:='true');".format(str(0.000000000000001)) # nosec B608
        self.cur.execute(sql)    
        #print(sql)  
        
       #graph analyze for short intersections
        sql="""SELECT pgr_analyzeGraph('temp.streets_help', {}, the_geom := 'geom', id := 'id');""".format(str(0.000000000000001)) # nosec B608
        #print(sql)
        self.cur.execute(sql)            
            
        sql="""DELETE FROM temp.streets_help sh WHERE id IN (
    SELECT sh.id FROM temp.streets_help_vertices_pgr v, temp.streets_help sh WHERE (sh.source=v.id OR sh.target=v.id) AND v.cnt=1 AND St_length(sh.geom) < {} AND v.id NOT IN(
            SELECT shv.id FROM temp.streets_help_vertices_pgr shv,temp.customers c,temp.energy_plants ep
                WHERE ST_dWithIN(shv.the_geom,c.geom,1e-15) OR ST_dWithIN(shv.the_geom,ep.geom,1e-15))
        GROUP BY sh.id
)""".format(self.tolerance) # nosec B608
        #print(sql)
        self.cur.execute(sql)     
        
        sql="""WITH sub AS(
    SELECT sth.id AS id, nh.type, nh.pipe_bundle_type_id 
        FROM temp.network_help nh, temp.streets_help sth, "{}".lines l
        WHERE ST_dWithIN(ST_LineSubString(sth.geom,0.45,0.55),nh.geom,{}) AND l.network={} AND ST_EQUALS(l.geom,nh.geom)
)    
UPDATE temp.streets_help sh SET type =sub.type, pipe_bundle_type_id=sub.pipe_bundle_type_id FROM sub WHERE sub.id =sh.id;""".format(self.config['versionName'],self.tolerance,network) # nosec B608
        #print(sql)
        self.cur.execute(sql) 
        
        sql="UPDATE temp.streets_help SET length_m=st_length(geom);"
        self.cur.execute(sql)    
        #print(sql)   
       