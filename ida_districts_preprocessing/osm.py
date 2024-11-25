import sys
import psycopg2
from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT 
from plugins.utility_functions.db import *
from plugins.utility_functions.files import *    
from plugins.utility_functions.workers import *
       
class WorkerOSMBuildingsImport(QRunnable):
    """Import buildings from OSM"""
    def __init__(self,*args,**kwargs):
        super().__init__()
        print("Import buildings from OSM")
        self.signals=APISignals()
        self.dictDB=kwargs['dictDB']
        self.clearOldFeatures=kwargs['clearOldFeatures']
        self.filePath=kwargs['filePath']
        self.conn=""
        self.cur=""
        self.plugin_dir=kwargs['plugin_dir']
        self.conn = dbConnect(self.dictDB,True)
        self.assetgroup="4"
        if self.conn:
            self.cur=self.conn.cursor(cursor_factory = psycopg2.extras.RealDictCursor)        

            configProject=loadProjectConfig(self.plugin_dir,self.dictDB['projectName'])
            self.srid=configProject['srid']
            print(self.srid)
                
    @pyqtSlot()
    def run(self):
        print('Import building data')
        self.signals.progress.emit(1)
        
        nodes=readOSMNodes(self.filePath)
        self.signals.progress.emit(20)
        buildings=self.readOSMBuildings(nodes)
        self.signals.progress.emit(50)
        if self.clearOldFeatures:
            sql='TRUNCATE "'+self.dictDB['versionName']+'".customers,"'+self.dictDB['versionName']+'".structure_boundarys;'
            self.cur.execute(sql)
        for counter,b in enumerate(buildings,1):
            if len(b.geom.split(","))>2:
                #insert structure_boundarys
                try:
                    sql='INSERT INTO "'+self.dictDB['versionName']+'".structure_boundarys(assetgroup,geom,f_vexp_m) VALUES ('+self.assetgroup+",ST_Multi(ST_Transform(ST_GeomFromText('"+b.geom+"',4326),"+self.srid+")),"+b.height+");"
                    print(sql)
                    self.cur.execute(sql)
                    
                    #insert customers
                    sql='INSERT INTO "'+self.dictDB['versionName']+"""".customers(assetgroup,assettype,geom) VALUES (1,1,ST_Transform(ST_Force3D(ST_Centroid(ST_GeomFromText('"""+b.geom+"',4326))),"+self.srid+"));"
                    print(sql)
                    self.cur.execute(sql)  
                except Exception as e:
                    self.signals.error.emit(str(e))
            self.signals.progress.emit(int(49*counter/len(buildings)))
                    
        refreshMap()
        zoomToLayer("customers")
        
        self.signals.progress.emit(100)  
                 
    def readOSMBuildings(self,nodes):
        print("read OSM buildings")
        buildings=[]
        latitudes=[]
        longitudes=[]
        height="0"
        bid=0
        data=readFileToList(self.filePath)
        for i in range(len(data)):
            try:
                if "k=\"building\" v=\"yes" in data[i] or "k=\"building\" v=\"house" in data[i] or "k=\"building\" v=\"construction" in data[i] or "k=\"building\" v=\"hospital" in data[i] or "k=\"building\" v=\"church" in data[i] or "k=\"building\" v=\"apartments" in data[i] or "k=\"building\" v=\"terrace" in data[i] or "k=\"building\" v=\"residential" in data[i] or "k=\"building\" v=\"university" in data[i] or "k=\"building\" v=\"school" in data[i] or "k=\"building\" v=\"office" in data[i] or "k=\"building\" v=\"commercial" in data[i] or "k=\"building\" v=\"industrial" in data[i] or "k=\"building\" v=\"kindergarden" in data[i] or "k=\"building\" v=\"public" in data[i] or "k=\"building\" v=\"supermarket" in data[i] or "k=\"building\" v=\"civic" in data[i] or "k=\"building\" v=\"retail" in data[i] or "k=\"building\" v=\"hotel" in data[i] or "k=\"building\" v=\"dormitory" in data[i] or "building:height" in data[i]:
                    bid+=1
                    j=i
                    add=True
                    if "height" in data[i]:
                        height=data[i].split("v=\"")[1].split("\"")[0]
                    else:
                        height="0"
                    while not "<way" in data[j] and not "<node" in data[j]:
                        j-=1
                        if "<node" in data[j]:
                            add=False
                        if "<nd ref=" in data[j]:
                            data_split=data[j].split("\"")
                            id=data_split[1]
                            for node in nodes:
                                if node.id==id:
                                    latitudes.append(node.latitude) 
                                    longitudes.append(node.longitude) 
                    if add:
                        buildings.append(OSMBuilding(bid,latitudes,longitudes,height))
                    latitudes=[]
                    longitudes=[]
            except Exception as e:
                self.signals.error.emit(str(e))
        return buildings
                    
class WorkerOSMStreetsImport(QRunnable):
    """Import streets from OSM"""
    def __init__(self,*args,**kwargs):
        super().__init__()
        print("Import streets from OSM")
        self.signals=APISignals()
        self.dictDB=kwargs['dictDB']
        self.clearOldFeatures=kwargs['clearOldFeatures']
        self.filePath=kwargs['filePath']
        self.conn=""
        self.cur=""
        self.plugin_dir=kwargs['plugin_dir']
        self.conn = dbConnect(self.dictDB,True)
        if self.conn:
            self.cur=self.conn.cursor(cursor_factory = psycopg2.extras.RealDictCursor)        

            configProject=loadProjectConfig(self.plugin_dir,self.dictDB['projectName'])
            self.srid=configProject['srid']
            print(self.srid)
                
    @pyqtSlot()
    def run(self):
        print('Import building data')
        self.signals.progress.emit(1)
        
        nodes=readOSMNodes(self.filePath)
        self.signals.progress.emit(20)  
        streets=self.readOSMStreets(nodes)
        self.signals.progress.emit(50)  

        if self.clearOldFeatures:
            sql='TRUNCATE "'+self.dictDB['versionName']+'".streets;'
            self.cur.execute(sql)
        for counter,street in enumerate(streets,1):
            sql='INSERT INTO "'+self.dictDB['versionName']+"""".streets(geom) VALUES (ST_Transform(ST_GeomFromText('"""+street.geom+"',4326),"+self.srid+"));"
            print(sql)
            self.cur.execute(sql)
            self.signals.progress.emit(int(49*counter/len(streets)))
                    
        refreshMap()
        zoomToLayer("streets")
        self.signals.progress.emit(100)  

    def readOSMStreets(self,nodes):
        print("read OSM streets")
        streets=[]
        latitudes=[]
        longitudes=[]
        sid=0
        data=readFileToList(self.filePath)
        for i in range(len(data)):
            try:
                if """k="highway" v="track\"""" in data[i] or "k=\"highway\" v=\"residential\"" in data[i] or "k=\"highway\" v=\"service\"" in data[i] or "k=\"highway\" v=\"primary\"" in data[i] or """k="highway" v="path\""""  in data[i] or "k=\"highway\" v=\"secondary\"" in data[i] or "k=\"highway\" v=\"tertiary\"" in data[i] or "k=\"highway\" v=\"unclassified\"" in data[i] or "k=\"highway\" v=\"living_street\"" in data[i]:
                    sid+=1
                    j=i
                    while not "<way" in data[j]:
                        j-=1
                        if "<nd ref=" in data[j]:
                            data_split=data[j].split("\"")
                            id=data_split[1]
                            for node in nodes:
                                if node.id==id:
                                    latitudes.append(node.latitude) 
                                    longitudes.append(node.longitude) 
                    streets.append(OSMStreet(sid,latitudes,longitudes))
                    latitudes=[]
                    longitudes=[]
            except Exception as e:
                self.signals.error.emit(e)
        return streets
        
def readOSMNodes(osmStreetFileName):
    print("read OSM Nodes")
    nodes=[]
    if os.path.exists(osmStreetFileName):
        with open(osmStreetFileName, "r") as myfile:   
            for line in myfile: 
                if " lat=" in line and " lon=" in line:
                    data=line.split("\"")
                    id=data[1]
                    latitude=data[15]
                    longitude=data[17]
                    nodes.append(OSMNode(id,latitude,longitude))
    return nodes
        
    
class OSMNode(object):
    """A node of a OSM street with latitude and longitude"""
    def __init__(self,id,latitude,longitude):
        self.id=id
        self.latitude=latitude
        self.longitude=longitude
        
class OSMStreet(object):
    """A OSM street with id and geometry"""
    def __init__(self,id,list_latitudes,list_longitudes):
        self.geom="LINESTRING("      
        self.geom+=",".join(j+" "+i for i,j in zip(list_latitudes,list_longitudes))
        self.geom+=")"  
        self.id=id
            
class OSMBuilding(object):
    """A OSM building with id and geometry"""
    def __init__(self,id,list_latitudes,list_longitudes,height):
        self.geom="POLYGON(("      
        self.geom+=",".join(j+" "+i for i,j in zip(list_latitudes,list_longitudes))
        if list_latitudes[0]==list_latitudes[-1] and list_longitudes[0]==list_longitudes[-1]:
            self.geom+="))"  
        else:
            self.geom+=","+ list_longitudes[0]+ " " +list_latitudes[0] +"))"
        self.id=id
        self.height=height