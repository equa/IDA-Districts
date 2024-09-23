import psycopg2
from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT     
import numpy as np
import math
from scipy.optimize import fsolve,leastsq
import psycopg2.extras
from plugins.utility_functions.utility import *
from plugins.utility_functions.db import *
from plugins.utility_functions.layer_visualization import *


from qgis.utils import iface
 
from qgis.PyQt.QtWidgets import QListWidgetItem
from PyQt5 import QtCore
from qgis.PyQt.QtCore import Qt
from qgis.core import QgsVectorLayer, QgsDataSourceUri, QgsSymbol, QgsRendererCategory, QgsCategorizedSymbolRenderer

 
def loadPipes(dictDB,cur,dlg):
    sql="""SELECT id, name, innerpipediameter FROM pipes ORDER BY innerpipediameter;"""
    cur.execute(sql)
    for pipe in cur.fetchall():
        name = str(pipe['id'])+':'+pipe['name']

        item = QListWidgetItem(name)
        item.setFlags(item.flags() | QtCore.Qt.ItemIsUserCheckable)
        item.setCheckState(QtCore.Qt.Checked)
        dlg.pipes_list.addItem(item)
        dlg.pipes[name]= [pipe['id'],float(pipe['innerpipediameter'])]

def solvePipeSize(z,T,dT,dp,epsilon,rho,cp,Re,Qmax):
    f = z[0]
    di= z[1]
    vel= z[2]

    F = np.empty((3))
    F[0] = 1.14+2*math.log(di/epsilon,10)-2*math.log(1+9.3/((Re) * epsilon/di*f**0.5),10) - 1/f**0.5
    F[1] = (8*f/(math.pi**2*rho*cp**2*dp))**0.2*(Qmax/dT)**0.4 - di #per m pipe
    F[2] = 4* Qmax / (math.pi*di**2*rho*cp*dT) - vel  

    return F
            
def startPipeSizing(dictDB,conn,dlg,plugin_dir):
    """Start pipe sizing"""
    print('Start')
    cur=conn.cursor(cursor_factory = psycopg2.extras.RealDictCursor)

    #get checked pipes from list
    pipes=[dlg.pipes[dlg.pipes_list.item(i).text()] for i in range(dlg.pipes_list.count()) if dlg.pipes_list.item(i).checkState() == Qt.Checked]
    print(pipes)
    
    #get networks
    networks=[]
    for i in range(dlg.combo_network_models.count()):
        if dlg.combo_network_models.itemText(i) != 'Check all items' and dlg.combo_network_models.itemChecked(i):        
            networks.append(dlg.combo_network_models.itemText(i))
                    
    print(networks)
    
    #get pipe bundle in DB
    pipe_bundles=getPipeBundleTypesDB(cur)
    print(pipe_bundles)
    
    dp=dlg.dp.text()
    epsilon=dlg.epsilon.text()
    rho=dlg.rho.text()
    cp=dlg.cp.text()
    ambient=dlg.ambient.text()
    
    if checkListNumbers([dp,epsilon,rho,cp,ambient]):
        dp=float(dp) #pipe
        epsilon=float(epsilon)
        rho=float(rho)
        cp=float(cp)
    else:
        iface.messageBar().pushMessage("Error", "Please check your inputs! Only values are valid.", level=Qgis.Critical)
        return False
        
    kin_viscosity=0
    if dlg.kin_viscosity.text():
        kin_viscosity=dlg.kin_viscosity.text()
        if isFloat(kin_viscosity):
            kin_viscosity=float(kin_viscosity)
        else:
            iface.messageBar().pushMessage("Error", "The kinematic viscosity is not a number.", level=Qgis.Critical)
        
    #write pipes into temp.dhc_lines table
    sql="""DROP TABLE IF EXISTS temp.dhc_lines;
CREATE TABLE temp.dhc_lines (
    like {}.dhc_lines
    including defaults
    including constraints
    including indexes
);
INSERT INTO temp.dhc_lines SELECT * FROM a.dhc_lines ORDER BY id;
""".format(dictDB['versionName'])
    print(sql)
    cur.execute(sql)
    #get pipes from version.dhc_lines table
    sql="""SELECT l.id,l.peak_power_kw, l.no_customer,la.conn_type FROM {}.dhc_lines l, line_assettypes la WHERE l.assetgroup=la.assetgroup AND l.assettype=la.assettype AND l.network IN ({}) ORDER BY l.id;""".format(dictDB['versionName'],','.join([i for i in networks]))
    cur.execute(sql)
    sql_lines=""
    new_pipe_bundles=[]
    for line in cur.fetchall():
        print('line id: '+str(line['id']))
        conn_type_pipes=[]
        Re=100000
        simulaneity=0.55*1.01**((line['no_customer']-1)*-1)+0.45
        #print(simulaneity)
        Qmax=simulaneity*float(line['peak_power_kw'])*1000
        #print(Qmax)
        zGuess = np.array([0.02,0.075,2])
        Re_old=0
        
        #create a list of connection temperature and dT pairs of each connection : [[T1 dT1],[T2 dT2],...]
        sql="""SELECT conn_t_conns.sequence, conns.temp, conns.type FROM connection_type_connections conn_t_conns,connections conns 
        WHERE conns.id=conn_t_conns.connection_id AND connection_type_id={}
        ORDER BY conn_t_conns.sequence;""".format(line['conn_type'])
        #print(sql)
        cur.execute(sql)
        conns=cur.fetchall()
        conns_dict={1: [], 2: []} #1--> Supply; 2 --> Return
        for conn in conns:
            conns_dict[conn['type']].append(float(conn['temp']))
        
        conn_temp_list=[]        
        i=0
        for conn in conns_dict[1]:
            try:
                tret=conns_dict[2][i]
            except:
                tret=conns_dict[2][-1]
            conn_temp_list.append({'T': conn,'dT': abs(conn-tret)})
            i+=1
            
        for conn in conns_dict[2]:
            try:
                tsup=conns_dict[1][i]
            except:
                tsup=conns_dict[1][-1]
            conn_temp_list.append({'T': conn,'dT': abs(conn-tsup)})
            i+=1
        #print(conn_temp_list)
        
        #print(conns_dict)
        i=1
        for conn in conn_temp_list:
            #print(conn)
            if not kin_viscosity:
                kin_viscosity=1/((0.1*(273.15+conn['T'])**2-34.335*(273.15+conn['T'])+2472)*rho)
            while abs(Re-Re_old)>100:
                z = fsolve(lambda zGuess: solvePipeSize(zGuess,conn['T'],conn['dT'],dp,epsilon,rho,cp,Re,Qmax),zGuess) #z[0]--> f; z[1]--> di; z[2]--> vel 
                Re_old=Re
                Re=z[2]*z[1]/kin_viscosity
                zGuess = np.array([z[0],z[1],z[2]])
                
            print(z)
            #take next bigger inner pipe diamater of DB (pipes)
            pipe=[pipe for pipe in pipes if  pipe[1] > z[1]]
            if pipe:
                conn_type_pipes.append([i,pipe[0][0],int(ambient)])
            else:
                iface.messageBar().pushMessage("Error", "No proper pipe available for inner diameter: "+str(z[1]), level=Qgis.Critical)
                return False
            i+=1
        print(conn_type_pipes)  
        
        #check if pipe bundle type already exists in DB otherwise add to DB
        bundle_type_id,new_pipe_bundles=addMissingPipeBundleType(cur,pipe_bundles,conn_type_pipes,new_pipe_bundles)
        
        #assign selected pipe bundle type to line
        sql_lines+="UPDATE temp.dhc_lines SET pipe_bundle_type_id = {} WHERE id={};\n".format(bundle_type_id, line['id'])
        
    print(sql_lines)
    cur.execute(sql_lines)
    
    #show table temp.dhc_lines
    showLinesTempTable('temp',dictDB,plugin_dir)
    
    dlg.new_pipe_bundles=new_pipe_bundles

def showLinesTempTable(version,dictDB,plugin_dir):
    removeTempLayers()
    
    #deactivate version.dhc_lines
    layerTreeRoot = QgsProject.instance().layerTreeRoot()  
    if QgsProject.instance().mapLayersByName('dhc_lines'):
        vlayer= QgsProject.instance().mapLayersByName('dhc_lines')[0]
        layerTreeRoot.findLayer(vlayer).setItemVisibilityChecked(False)
    
    #render temp.dhc_lines
    uri = QgsDataSourceUri()
    uri.setConnection(dictDB['host'], dictDB['port'], dictDB['projectName'], dictDB['user'], dictDB['pwd'])    
    dir=getProjectHandlingDir(plugin_dir)
    vlayerName='dhc_lines'
    categories=['Unkown','Service Pipe','Distribution Pipe','Transmission Pipe','Station Pipe','Customer Pipe']
    ids=['0','1','2','3','5','6']

    uri.setDataSource(version, vlayerName, "geom")
    if version =='temp':
        vlayer = QgsVectorLayer(uri.uri(False), vlayerName+'_temp', dictDB['user'])
    else:
        vlayer = QgsVectorLayer(uri.uri(False), vlayerName, dictDB['user'])
    QgsProject.instance().addMapLayer(vlayer)  
    print(vlayerName[4:-1] + '_assetgroups')
    target_layer = QgsProject.instance().mapLayersByName(vlayerName[4:-1] + '_assetgroups')[0] 
    config = {'AllowMulti': False,
              'AllowNull': True,
              'FilterExpression': '',
              'Key': 'id',
              'Layer': target_layer.id(),
              'NofColumns': 1,
              'OrderByValue': False,
              'UseCompleter': False,
              'Value': 'assetgroup'}
    widget_setup = QgsEditorWidgetSetup('ValueRelation',config)
    fields=vlayer.fields()
    field_idx = fields.indexOf('assetgroup')
    vlayer.setEditorWidgetSetup(field_idx, widget_setup)   

    categorized_renderer = QgsCategorizedSymbolRenderer()            
    categorized_renderer.setClassAttribute('assetgroup') 
    for category,id in zip(categories,ids):      
        print(vlayerName)
        print(vlayer)
        symbol=QgsSymbol.defaultSymbol(vlayer.geometryType())
        symbol.setWidth(0.75) 
            
        cat = QgsRendererCategory(id, symbol, category)
        categorized_renderer.addCategory(cat)       
    vlayer.setRenderer(categorized_renderer)
            
def getPipeBundleTypesDB(cur):
    sql="""SELECT pipe_bundle_type_id,ARRAY_AGG (ARRAY[sequence::int,pipe_id::int,ambient::int] ORDER BY sequence) AS pipe
    FROM bundle_pipes 
    GROUP BY pipe_bundle_type_id 
    ORDER BY pipe_bundle_type_id ASC; """
    cur.execute(sql)
    return { bundle['pipe_bundle_type_id']: bundle['pipe'] for bundle in cur.fetchall()}
    
def addMissingPipeBundleType(cur,pipe_bundles,conn_type_pipes,new_pipe_bundles):
    print(pipe_bundles)
    
    print([True for i in pipe_bundles if pipe_bundles[i]==conn_type_pipes])
    bundle_type_id=[i for i in pipe_bundles if pipe_bundles[i]==conn_type_pipes]
    if bundle_type_id:
        bundle_type_id=bundle_type_id[0]
    else:
        print('*****--*****Add bundle*****---****')
        bundle_type_id=getMaxId(cur,'pipe_bundle_types')+1
        bundle_pipes_max_id=getMaxId(cur,'bundle_pipes')+1
        pipe_bundles[bundle_type_id]=conn_type_pipes

        #Add to pipe bundle types
        sql="""INSERT INTO pipe_bundle_types (id,description) VALUES ({},'pipes: {}');\n""".format(bundle_type_id,','.join(str(i[1]) for i in conn_type_pipes))
        new_pipe_bundles.append(bundle_type_id)
        
        #Add to bundle_pipes
        for pipe in conn_type_pipes:
            x=0.5*((2*pipe[0]-1-pipe[0])/2)
            sql+="""INSERT INTO bundle_pipes (id,pipe_bundle_type_id,sequence,pipe_id,x,y,ambient) VALUES ({},{},{},{},{},{},{});\n""".format(
                bundle_pipes_max_id,bundle_type_id,pipe[0],pipe[1],x,1,pipe[2])
            bundle_pipes_max_id+=1
        print(sql)
        cur.execute(sql)
    return bundle_type_id, new_pipe_bundles
    
def savePipeSizingResults(dictDB,conn,dlg):
    """save pipe sizing results"""
    print('save pipe sizing results')
    cur=conn.cursor(cursor_factory = psycopg2.extras.RealDictCursor)
    sql="""TRUNCATE {}.dhc_lines CASCADE;""".format(dictDB['versionName'])
    print(sql) 
    cur.execute(sql)  
    sql="""INSERT INTO {}.dhc_lines SELECT * FROM temp.dhc_lines;""".format(dictDB['versionName'])
    print(sql) 
    cur.execute(sql)  
    
    removeTempLayers()
    
    layerTreeRoot = QgsProject.instance().layerTreeRoot()  
    iface.mapCanvas().snappingUtils().setIndexingStrategy(iface.mapCanvas().snappingUtils().IndexingStrategy.IndexExtent)
    vlayer= QgsProject.instance().mapLayersByName('dhc_lines')
    if vlayer:
        vlayer=vlayer[0]
        layerTreeRoot.findLayer(vlayer).setItemVisibilityChecked(True)
        vlayer.emitDataChanged()
    refreshMap()
    
    
def rejectPipeSizingResults(dictDB,conn,dlg):
    """reject pipe sizing results"""
    print('reject pipe sizing results')
    removeTempLayers()
    
    cur=conn.cursor(cursor_factory = psycopg2.extras.RealDictCursor)
    layerTreeRoot = QgsProject.instance().layerTreeRoot()  
    if QgsProject.instance().mapLayersByName('dhc_lines'):
        vlayer= QgsProject.instance().mapLayersByName('dhc_lines')[0]
        layerTreeRoot.findLayer(vlayer).setItemVisibilityChecked(True)
    
    #remove new pipe bundles from DB
    print(dlg.new_pipe_bundles)
    sql=""
    for bundle_id in dlg.new_pipe_bundles:
        sql+="""DELETE FROM bundle_pipes WHERE pipe_bundle_type_id={};""".format(bundle_id)
        sql+="""DELETE FROM pipe_bundle_types WHERE id={};""".format(bundle_id)
    if sql:    
        cur.execute(sql)
    
                