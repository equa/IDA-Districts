import psycopg2
from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT     
import numpy as np
import math
from scipy.optimize import fsolve,leastsq
import psycopg2.extras
from plugins.utility_functions.topology import *
from plugins.utility_functions.utility import *
from plugins.utility_functions.db import *
from plugins.utility_functions.layer_visualization import *
from .GenerateNetworkTopology import WorkerGenerateNetworkTopology 


from qgis.utils import iface
 
from qgis.PyQt.QtWidgets import QListWidgetItem
from PyQt5 import QtCore
from qgis.PyQt.QtCore import Qt,QThreadPool
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

def solvePipeSize(z,dp,epsilon,rho,Re,mdot):
    f = z[0]
    di= z[1]
    vel= z[2]

    F = np.empty((3))
    F[0] = 1.14+2*math.log(di/epsilon,10)-2*math.log(1+9.3/((Re) * epsilon/di*f**0.5),10) - 1/f**0.5
    F[1] = (8*f/(math.pi**2*rho*dp))**0.2*(mdot)**0.4 - di #per m pipe
    F[2] = 4* mdot / (math.pi*di**2*rho) - vel  

    return F
    
def setEnergyColLines(cur,version,network,energy_columns):
    """Update the number of customers and the peak power of each line, which are supplied by the main plant"""
    print(energy_columns)
    sql='\n'.join(["""DO $$
BEGIN
   IF NOT EXISTS (SELECT 1 FROM information_schema.columns 
                  WHERE table_schema = 'temp' 
                    AND table_name = 'lines' 
                    AND column_name = '{}') THEN
      ALTER TABLE temp.lines ADD COLUMN {} numeric;
   END IF;
END $$;""".format(i,i) for i in energy_columns+['no_customer']])
    print(sql)
    cur.execute(sql)
    
    sql="""UPDATE temp.lines l 
    SET no_customer=a.no_customer{}
    FROM (
        SELECT l.id AS lid,{} count(c.id) AS no_customer
            FROM pgr_dijkstra(
                'SELECT id,source, target, length_m*costs_eur7m AS cost FROM temp.streets_help',
                (SELECT sth_v.id FROM temp.streets_help_vertices_pgr sth_v, temp.energy_plants ep WHERE {} = ANY(ep.network) AND {} = ANY (ep.main_plant) AND ST_dWithIn(sth_v.the_geom,ep.geom,0.01)), 
                (SELECT ARRAY_AGG(sth_v.id) FROM temp.streets_help_vertices_pgr sth_v, temp.customers c WHERE {} = ANY(c.network) AND ST_dWithIn(sth_v.the_geom,c.geom,0.01))) di,
                temp.customers c, temp.streets_help_vertices_pgr sth_v,temp.streets_help sth, temp.lines l
            WHERE ST_dWithIn(sth_v.the_geom,c.geom,0.01) AND sth_v.id=di.end_vid AND edge>0 AND sth.id=di.edge AND ST_dWithIn(l.geom,ST_LineSubstring(sth.geom,0.000001,0.999999),0.00000001)
            GROUP BY lid) a
    WHERE a.lid=l.id;""".format(''.join([',\n        {}=a.{}'.format(i,i) for i in energy_columns]),''.join(['sum(c.{}) AS {}, '.format(i,i) for i in energy_columns]),network,network,network)
    print(sql)
    cur.execute(sql)    
        
def startPipeSizing(dictDB,conn,dlg,plugin_dir):
    """Start pipe sizing"""
    print('Start pipe sizing')
    cur=conn.cursor(cursor_factory = psycopg2.extras.RealDictCursor)

    #get checked pipes from list
    pipes=[dlg.pipes[dlg.pipes_list.item(i).text()] for i in range(dlg.pipes_list.count()) if dlg.pipes_list.item(i).checkState() == Qt.Checked]
    print(pipes)
    
    #get networks
    network=dlg.combo_network_models.currentText()                    
    print(network)
    
    #get pipe bundle in DB
    pipe_bundles=getPipeBundleTypesDB(cur)
    print(pipe_bundles)
    
    dp=dlg.dp.text()
    epsilon=dlg.epsilon.text()
    rho=dlg.rho.text()
    cp=dlg.cp.text()
    ambient=dlg.ambient.text()
    
    if checkListNumbers([dp,epsilon,rho,cp,ambient]) and (dbColumnIsNumeric(cur,dictDB['versionName'],'lines',dlg.combo_simultaneity.currentText()) if dlg.checkBoxSimultaneity.isChecked() and dlg.rbtn_lines.isChecked() else True) and all([isNumber(dlg.table_sequences.item(i,1).text()) and isNumber(dlg.table_sequences.item(i,4).text()) for i in range(dlg.table_sequences.rowCount())]):
        dp=float(dp) #pipe
        epsilon=float(epsilon)
        rho=float(rho)
        cp=float(cp)
    else:
        iface.messageBar().pushMessage("Error", "Please check your inputs! Only values are valid.", level=Qgis.Critical)
        return False
        
    for i in range(dlg.table_sequences.rowCount()): 
        if dlg.table_sequences.cellWidget(i,0).currentText()==dlg.table_sequences.cellWidget(i,3).currentText():
            iface.messageBar().pushMessage("Error", "Supply and return pipe could not be the same: sequence={}!".format(i+1), level=Qgis.Critical)
            return False
        
    kin_viscosity=0
    if dlg.kin_viscosity.text():
        kin_viscosity=dlg.kin_viscosity.text()
        if isFloat(kin_viscosity):
            kin_viscosity=float(kin_viscosity)
        else:
            iface.messageBar().pushMessage("Error", "The kinematic viscosity is not a number.", level=Qgis.Critical)
        
    #write pipes into temp.lines table
    sql="""DROP TABLE IF EXISTS temp.lines;
CREATE TABLE temp.lines (
    like "{}".lines
    including defaults
    including constraints
    including indexes
);
INSERT INTO temp.lines SELECT * FROM "{}".lines ORDER BY id;""".format(dictDB['versionName'],dictDB['versionName'])
    print(sql)
    cur.execute(sql)
    
    if dlg.rbtn_customers.isChecked():
        #create topology: add peak power columns (and) number of customers if consider simulaneity 
        if checkNetwork(cur,dictDB['versionName'],[network]):    
            threadpool = QThreadPool()
            worker = WorkerGenerateNetworkTopology(iface=iface,dictDB=dictDB,plugin_dir=plugin_dir, networks=[network] ,redraw_submodels_polygons=False, deleteUnconnectedCustomers=False, deleteUnconnectedLines=False,
                connectCustomers=False,connectCustomers_assettype_lines=0,connectCustomers_assettype_pipeBundle=0,
                addCustomers=False,addCustomers_assettype_customers=0,
                connectPlants=False,connectPlants_assettype_lines=0,connectPlants_assettype_pipeBundle=0,
                deleteUnconnectedNetworkEnds=False,
                keepAssettypes=True,
                overrideAssettypes=False,overrideAssettypes_customers=0, overrideAssettypes_lines=0,overrideAssettypes_pipeBundle=0,tolerance=0.001,
                showTempTables=False)
            worker.signals.finished.connect(lambda:doSizing(cur,dictDB,dlg,network,plugin_dir,dp,epsilon,rho,cp,kin_viscosity,ambient,pipes,pipe_bundles))
            task_topology=threadpool.start(worker)
    else:
        doSizing(cur,dictDB,dlg,network,plugin_dir,dp,epsilon,rho,cp,kin_viscosity,ambient,pipes,pipe_bundles)  
            
def doSizing(cur,dictDB,dlg,network,plugin_dir,dp,epsilon,rho,cp,kin_viscosity,ambient,pipes,pipe_bundles):
    energy_columns=[dlg.table_sequences.cellWidget(i, 5).currentText() for i in range(dlg.table_sequences.rowCount())]
    if dlg.rbtn_customers.isChecked():    
        setEnergyColLines(cur,dictDB['versionName'],network,energy_columns)
        sql="""SELECT l.id,{} l.no_customer FROM temp.lines l WHERE  l.network = {} ORDER BY l.id;""".format(''.join(['l.{}, '.format(i) for i in energy_columns]),network)
    else:
        sql="""SELECT l.id,{} {} AS no_customer FROM temp.lines l WHERE l.network = {} ORDER BY l.id;""".format(
            ''.join(['l.{}, '.format(i) for i in energy_columns]),'l.'+dlg.combo_simultaneity.currentText() if dlg.checkBoxSimultaneity.isChecked() and dlg.rbtn_lines.isChecked() else 1,network)

    print(sql)
    cur.execute(sql)
    lines=cur.fetchall()
    sql_lines=""
    new_pipe_bundles=[]
    
    pipe_boundary_dict={} #{seq: [[col_name,dT,T]]}
    for i in range(dlg.table_sequences.rowCount()):
        try:
            pipe_boundary_dict[dlg.table_sequences.cellWidget(i,0).currentText()]=pipe_boundary_dict[dlg.table_sequences.cellWidget(i,0).currentText()]+[[dlg.table_sequences.cellWidget(i,5).currentText(),abs(float(dlg.table_sequences.item(i,1).text())-float(dlg.table_sequences.item(i,4).text())),float(dlg.table_sequences.item(i,1).text())]]
        except:
            pipe_boundary_dict[dlg.table_sequences.cellWidget(i,0).currentText()]=[[dlg.table_sequences.cellWidget(i,5).currentText(),abs(float(dlg.table_sequences.item(i,1).text())-float(dlg.table_sequences.item(i,4).text())),float(dlg.table_sequences.item(i,1).text())]]
        try:
            pipe_boundary_dict[dlg.table_sequences.cellWidget(i,3).currentText()]=pipe_boundary_dict[dlg.table_sequences.cellWidget(i,3).currentText()]+[[dlg.table_sequences.cellWidget(i,5).currentText(),abs(float(dlg.table_sequences.item(i,1).text())-float(dlg.table_sequences.item(i,4).text())),float(dlg.table_sequences.item(i,4).text())]]
        except:
            pipe_boundary_dict[dlg.table_sequences.cellWidget(i,3).currentText()]=[[dlg.table_sequences.cellWidget(i,5).currentText(),abs(float(dlg.table_sequences.item(i,1).text())-float(dlg.table_sequences.item(i,4).text())),float(dlg.table_sequences.item(i,4).text())]]
    print(pipe_boundary_dict)
           
    for line in lines:
        print('line id: '+str(line['id']))
        pipe_bundle=[]
        Re=100000
        if dlg.checkBoxSimultaneity.isChecked():
            simulaneity=0.55*1.01**((float(line['no_customer'])-1)*-1)+0.45
        else:
            simulaneity=1
        print(simulaneity)
        zGuess = np.array([0.02,0.075,2])
        Re_old=0

        i=1
        for pipe_boundary in pipe_boundary_dict:
            print(pipe_boundary)
            print([simulaneity*float(line[i[0]])/(cp*i[1]) for i in pipe_boundary_dict[pipe_boundary]])
            mdot_pipe=sum([simulaneity*float(line[i[0]])/(cp*i[1]) for i in pipe_boundary_dict[pipe_boundary]])

            if not kin_viscosity:
                kin_viscosity=sum([1/((0.1*(273.15+i[2])**2-34.335*(273.15+i[2])+2472)*rho) for i in pipe_boundary_dict[pipe_boundary]])/len(pipe_boundary_dict[pipe_boundary])
                print(kin_viscosity)
            while abs(Re-Re_old)>100:
                z = fsolve(lambda zGuess: solvePipeSize(zGuess,dp,epsilon,rho,Re,mdot_pipe),zGuess) #z[0]--> f; z[1]--> di; z[2]--> vel 
                Re_old=Re
                Re=z[2]*z[1]/kin_viscosity
                zGuess = np.array([z[0],z[1],z[2]])
                
            print(z)
            #take next bigger inner pipe diamater of DB (pipes)
            pipe=[pipe for pipe in pipes if  pipe[1] > z[1]]
            if pipe:
                pipe_bundle.append([i,pipe[0][0],int(ambient)])
            else:
                iface.messageBar().pushMessage("Error", "No proper pipe available for inner diameter: "+str(z[1]), level=Qgis.Critical)
                return False
            i+=1
        print(pipe_bundle)  
        
        #check if pipe bundle type already exists in DB otherwise add to DB
        bundle_type_id,new_pipe_bundles=addMissingPipeBundleType(cur,pipe_bundles,pipe_bundle,new_pipe_bundles)
        
        #assign selected pipe bundle type to line
        sql_lines+="UPDATE temp.lines SET pipe_bundle_type_id = {} WHERE id={};\n".format(bundle_type_id, line['id'])
        
    print(sql_lines)
    if sql_lines:
        cur.execute(sql_lines)
    
    #show table temp.lines
    showLinesTempTable('temp',dictDB,plugin_dir)
    
    dlg.new_pipe_bundles=new_pipe_bundles

def showLinesTempTable(version,dictDB,plugin_dir):
    removeTempLayers()
    
    #deactivate version.lines
    layerTreeRoot = QgsProject.instance().layerTreeRoot()  
    if QgsProject.instance().mapLayersByName('lines'):
        vlayer= QgsProject.instance().mapLayersByName('lines')[0]
        layerTreeRoot.findLayer(vlayer).setItemVisibilityChecked(False)
    
    #render temp.lines
    uri = QgsDataSourceUri()
    uri.setConnection(dictDB['host'], dictDB['port'], dictDB['projectName'], dictDB['user'], dictDB['pwd'])    
    dir=getProjectHandlingDir(plugin_dir)
    vlayerName='lines'
    categories=['Unkown','Service Pipe','Distribution Pipe','Transmission Pipe','Station Pipe','Customer Pipe']
    ids=['0','1','2','3','5','6']

    uri.setDataSource(version, vlayerName, "geom")
    if version =='temp':
        vlayer = QgsVectorLayer(uri.uri(False), vlayerName+'_temp', dictDB['user'])
    else:
        vlayer = QgsVectorLayer(uri.uri(False), vlayerName, dictDB['user'])
    QgsProject.instance().addMapLayer(vlayer)  
    print(vlayerName[:-1] + '_assetgroups')
    target_layer = QgsProject.instance().mapLayersByName(vlayerName[:-1] + '_assetgroups')
    if target_layer:
        target_layer=target_layer[0]
    else:
        uri.setDataSource("public", 'line_assetgroups', "")
        target_layer = QgsVectorLayer(uri.uri(False), 'line_assetgroups', dictDB['user'])
        QgsProject.instance().addMapLayer(target_layer)
        setLayersHidden(['line_assetgroups']) 
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
    sql="""TRUNCATE "{}".lines CASCADE;""".format(dictDB['versionName'])
    print(sql) 
    cur.execute(sql)  
    
    #remove added load columns in temp.lines
    if dlg.rbtn_customers.isChecked():
        energy_columns=[dlg.table_sequences.cellWidget(i, 5).currentText() for i in range(dlg.table_sequences.rowCount())]+['no_customer']
        table_columns=getTableAttr(cur,dictDB,'line')
        energy_columns = [col for col in energy_columns if col not in table_columns]
        print(energy_columns)
        sql='\n'.join(["""DO $$
BEGIN
   IF EXISTS (SELECT 1 FROM information_schema.columns 
                  WHERE table_schema = 'temp' 
                    AND table_name = 'lines' 
                    AND column_name = '{}') THEN
      ALTER TABLE temp.lines DROP COLUMN {};
   END IF;
END $$;""".format(i,i) for i in energy_columns])
        print(sql)
        cur.execute(sql)
    
    sql="""INSERT INTO "{}".lines SELECT * FROM temp.lines;""".format(dictDB['versionName'])
    print(sql) 
    cur.execute(sql)

    dlg.new_pipe_bundles=[]   
    
    removeTempLayers()
    
    layerTreeRoot = QgsProject.instance().layerTreeRoot()  
    iface.mapCanvas().snappingUtils().setIndexingStrategy(iface.mapCanvas().snappingUtils().IndexingStrategy.IndexExtent)
    vlayer= QgsProject.instance().mapLayersByName('lines')
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
    if QgsProject.instance().mapLayersByName('lines'):
        vlayer= QgsProject.instance().mapLayersByName('lines')[0]
        layerTreeRoot.findLayer(vlayer).setItemVisibilityChecked(True)
    
    #remove new pipe bundles from DB
    print(dlg.new_pipe_bundles)
    sql=""
    for bundle_id in dlg.new_pipe_bundles:
        sql+="""DELETE FROM bundle_pipes WHERE pipe_bundle_type_id={};""".format(bundle_id)
        sql+="""DELETE FROM pipe_bundle_types WHERE id={};""".format(bundle_id)
    if sql:    
        cur.execute(sql)
    
                