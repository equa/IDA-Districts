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
from plugins.utility_functions.workers import APISignals
from .GenerateNetworkTopology import WorkerGenerateNetworkTopology 
from PyQt5.QtCore import QObject, pyqtSlot, pyqtSignal,QRunnable

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

        dlg.pipes_list.append(name)
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
    
def setEnergyColLines(cur,version,network,energy_columns,main_plant_id):
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
                (SELECT sth_v.id FROM temp.streets_help_vertices_pgr sth_v, temp.energy_plants ep WHERE {} = ANY(ep.network) AND ep.id={} AND ST_dWithIn(sth_v.the_geom,ep.geom,0.01)), 
                (SELECT ARRAY_AGG(sth_v.id) FROM temp.streets_help_vertices_pgr sth_v, temp.customers c WHERE {} = ANY(c.network) AND ST_dWithIn(sth_v.the_geom,c.geom,0.01))) di,
                temp.customers c, temp.streets_help_vertices_pgr sth_v,temp.streets_help sth, temp.lines l
            WHERE ST_dWithIn(sth_v.the_geom,c.geom,0.01) AND sth_v.id=di.end_vid AND edge>0 AND sth.id=di.edge AND sth.id=l.id
            GROUP BY lid) a
    WHERE a.lid=l.id;""".format(''.join([',\n        {}=a.{}'.format(i,i) for i in energy_columns]),''.join(['sum(c.{}) AS {}, '.format(i,i) for i in energy_columns]),network,main_plant_id,network)
    print(sql)
    cur.execute(sql)    

def getPipeDiameter(cur,id):
    sql="SELECT innerpipediameter FROM pipes WHERE id={};".format(id)
    cur.execute(sql)
    return float(cur.fetchone()['innerpipediameter'])

class WorkerPipeSizing(QRunnable):
    """Worker thread
    Inherits from QRunnable to handle worker thread setup, signals and wrap-up."""
    def __init__(self,*args,**kwargs):
        super().__init__()
        self.args=args
        print(args)
        self.signals=APISignals()
        self.cur=kwargs['cur']
        self.dictDB=kwargs['dictDB']
        self.dlg=kwargs['dlg']
        self.network=kwargs['network']
        self.plugin_dir=kwargs['plugin_dir']
        self.dp=kwargs['dp']
        self.epsilon=kwargs['epsilon']
        self.rho=kwargs['rho']
        self.cp=kwargs['cp']
        self.kin_viscosity=kwargs['kin_viscosity']
        self.ambient=kwargs['ambient']
        self.pipe_bundles=kwargs['pipe_bundles']
           
    @pyqtSlot()
    def run(self):
        try:
            print('***Start Worker pipe sizing***')
            self.signals.progress.emit(1)
            energy_columns=[self.dlg.table_circuits.cellWidget(i, 5).currentText() for i in range(self.dlg.table_circuits.rowCount())]
            if self.dlg.rbtn_customers.isChecked():    
                setEnergyColLines(self.cur,self.dictDB['versionName'],self.network,energy_columns,self.dlg.combo_main_plants.currentText())
                self.signals.progress.emit(2)
                sql="""SELECT l.id,{} l.no_customer FROM temp.lines l WHERE  l.network = {} ORDER BY l.id;""".format(''.join(['l.{}, '.format(i) for i in energy_columns]),self.network)
            else:
                sql="""SELECT l.id,{} {} AS no_customer FROM temp.lines l WHERE l.network = {} ORDER BY l.id;""".format(
                    ''.join(['l.{}, '.format(i) for i in energy_columns]),'l.'+self.dlg.combo_simultaneity.currentText() if self.dlg.checkBoxSimultaneity.isChecked() and self.dlg.rbtn_lines.isChecked() else 1,self.network)

            print(sql)
            self.signals.progress.emit(3)
            self.cur.execute(sql)
            lines=self.cur.fetchall()
            sql_lines=""
            new_pipe_bundles=[]
            self.signals.progress.emit(4)
            pipe_boundary_dict={} #{seq: [[col_name,dT,T]]}
            seq_pipes_dict={}
            for i in range(self.dlg.table_circuits.rowCount()):
                try:
                    pipe_boundary_dict[self.dlg.table_circuits.cellWidget(i,0).currentText()]=pipe_boundary_dict[self.dlg.table_circuits.cellWidget(i,0).currentText()]+[[self.dlg.table_circuits.cellWidget(i,5).currentText(),abs(float(self.dlg.table_circuits.item(i,1).text())-float(self.dlg.table_circuits.item(i,4).text())),float(self.dlg.table_circuits.item(i,1).text())]]
                except:
                    pipe_boundary_dict[self.dlg.table_circuits.cellWidget(i,0).currentText()]=[[self.dlg.table_circuits.cellWidget(i,5).currentText(),abs(float(self.dlg.table_circuits.item(i,1).text())-float(self.dlg.table_circuits.item(i,4).text())),float(self.dlg.table_circuits.item(i,1).text())]]
                try:
                    pipe_boundary_dict[self.dlg.table_circuits.cellWidget(i,3).currentText()]=pipe_boundary_dict[self.dlg.table_circuits.cellWidget(i,3).currentText()]+[[self.dlg.table_circuits.cellWidget(i,5).currentText(),abs(float(dlg.table_circuits.item(i,1).text())-float(self.dlg.table_circuits.item(i,4).text())),float(self.dlg.table_circuits.item(i,4).text())]]
                except:
                    pipe_boundary_dict[self.dlg.table_circuits.cellWidget(i,3).currentText()]=[[self.dlg.table_circuits.cellWidget(i,5).currentText(),abs(float(self.dlg.table_circuits.item(i,1).text())-float(self.dlg.table_circuits.item(i,4).text())),float(self.dlg.table_circuits.item(i,4).text())]]
            pipe_boundary_dict=dict(sorted(pipe_boundary_dict.items()))
            print(pipe_boundary_dict)
            
            for i in range(self.dlg.table_sequences.rowCount()):
                #get checked pipes from list
                dropDown=self.dlg.table_sequences.cellWidget(i,1)
                pipes=[int(dropDown.itemText(i).split(':')[0].split('(')[0]) for i in range(dropDown.count()) if dropDown.itemText(i) != 'Check all items' and dropDown.itemChecked(i)]
                print(pipes)
                seq_pipes_dict[int(self.dlg.table_sequences.item(i,0).text())]=[[id,getPipeDiameter(self.cur,id)] for id in pipes]
            print(seq_pipes_dict)
            seq_pipes_dict = {
                k: sorted(v, key=lambda x: x[1])
                for k, v in seq_pipes_dict.items()
            }
            print(seq_pipes_dict)
            
            self.signals.progress.emit(5)        
            for counter,line in enumerate(lines,1):
                print('line id: '+str(line['id']))
                pipe_bundle=[]
                Re=100000
                if self.dlg.checkBoxSimultaneity.isChecked():
                    simulaneity=0.55*1.01**((float(line['no_customer'])-1)*-1)+0.45
                else:
                    simulaneity=1
                print(simulaneity)
                zGuess = np.array([0.02,0.075,2])

                i=1
                for pipe_boundary in pipe_boundary_dict:
                    print(pipe_boundary)
                    print([simulaneity*float(line[i[0]])/(self.cp*i[1]) for i in pipe_boundary_dict[pipe_boundary]])
                    mdot_pipe=sum([simulaneity*float(line[i[0]])/(self.cp*i[1]) for i in pipe_boundary_dict[pipe_boundary]])
                    print(mdot_pipe)

                    if not self.kin_viscosity:
                        self.kin_viscosity=sum([1/((0.1*(273.15+i[2])**2-34.335*(273.15+i[2])+2472)*self.rho) for i in pipe_boundary_dict[pipe_boundary]])/len(pipe_boundary_dict[pipe_boundary])
                        print(self.kin_viscosity)
                    Re_old=0
                    while abs(Re-Re_old)>100:
                        z = fsolve(lambda zGuess: solvePipeSize(zGuess,self.dp,self.epsilon,self.rho,Re,mdot_pipe),zGuess) #z[0]--> f; z[1]--> di; z[2]--> vel 
                        Re_old=Re
                        Re=z[2]*z[1]/self.kin_viscosity
                        zGuess = np.array([z[0],z[1],z[2]])
                        
                    print(z)
                    #take next bigger inner pipe diamater of DB (pipes)
                    pipe=[pipe for pipe in seq_pipes_dict[int(pipe_boundary)] if  pipe[1] > z[1]]
                    if pipe:
                        pipe_bundle.append([i,pipe[0][0],int(self.ambient)])
                    else:
                        #iface.messageBar().pushMessage("Error", "No proper pipe available for inner diameter: "+str(z[1]), level=Qgis.Critical)
                        return False
                    i+=1
                print(pipe_bundle)  
                
                #check if pipe bundle type already exists in DB otherwise add to DB
                bundle_type_id,new_pipe_bundles=addMissingPipeBundleType(self.cur,self.pipe_bundles,pipe_bundle,new_pipe_bundles)
                
                #assign selected pipe bundle type to line
                sql_lines+="UPDATE temp.lines SET pipe_bundle_type_id = {} WHERE id={};\n".format(bundle_type_id, line['id'])
                #if counter % 25 == 0:
                self.signals.progress.emit(int(5+counter/len(lines)*85))
                
            self.signals.progress.emit(90)
            print(sql_lines)
            if sql_lines:
                self.cur.execute(sql_lines)
            
            #show table temp.lines
            self.signals.progress.emit(95)
            showLinesTempTable('temp',self.dictDB,self.plugin_dir)
            
            self.dlg.new_pipe_bundles=new_pipe_bundles
            self.signals.progress.emit(100)
        except Exception as e:
            self.signals.error.emit(str(e)) 
        
def startPipeSizing(dictDB,dlg,plugin_dir):
    """Start pipe sizing"""
    print('Start pipe sizing')
    conn=dbConnect(dictDB,True)
    if conn:
        cur=conn.cursor(cursor_factory = psycopg2.extras.RealDictCursor)
        
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
        
        if checkListNumbers([dp,epsilon,rho,cp,ambient]) and (dbColumnIsNumeric(cur,dictDB['versionName'],'lines',dlg.combo_simultaneity.currentText()) if dlg.checkBoxSimultaneity.isChecked() and dlg.rbtn_lines.isChecked() else True) and all([isNumber(dlg.table_circuits.item(i,1).text()) and isNumber(dlg.table_circuits.item(i,4).text()) for i in range(dlg.table_circuits.rowCount())]):
            dp=float(dp) #pipe
            epsilon=float(epsilon)
            rho=float(rho)
            cp=float(cp)
        else:
            iface.messageBar().pushMessage("Error", "Please check your inputs! Only values are valid.", level=Qgis.Critical)
            return False
            
        for i in range(dlg.table_circuits.rowCount()): 
            if dlg.table_circuits.cellWidget(i,0).currentText()==dlg.table_circuits.cellWidget(i,3).currentText():
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
            dlg.execute([network])    
            dlg.worker.signals.finished.connect(lambda: dlg.doSizing(cur,dictDB,dlg,network,plugin_dir,dp,epsilon,rho,cp,kin_viscosity,ambient,pipe_bundles))
        else:
            dlg.doSizing(cur,dictDB,dlg,network,plugin_dir,dp,epsilon,rho,cp,kin_viscosity,ambient,pipe_bundles)  

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
    print(vlayerName[:-1] + '_types')
    target_layer = QgsProject.instance().mapLayersByName(vlayerName[:-1] + '_types')
    if target_layer:
        target_layer=target_layer[0]
    else:
        uri.setDataSource("public", 'line_types', "")
        target_layer = QgsVectorLayer(uri.uri(False), 'line_types', dictDB['user'])
        QgsProject.instance().addMapLayer(target_layer)
        setLayersHidden(['line_types']) 
    config = {'AllowMulti': False,
              'AllowNull': True,
              'FilterExpression': '',
              'Key': 'id',
              'Layer': target_layer.id(),
              'NofColumns': 1,
              'OrderByValue': False,
              'UseCompleter': False,
              'Value': 'type'}
    widget_setup = QgsEditorWidgetSetup('ValueRelation',config)
    fields=vlayer.fields()
    field_idx = fields.indexOf('type')
    vlayer.setEditorWidgetSetup(field_idx, widget_setup)   

    categorized_renderer = QgsCategorizedSymbolRenderer()            
    categorized_renderer.setClassAttribute('type') 
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
        energy_columns=[dlg.table_circuits.cellWidget(i, 5).currentText() for i in range(dlg.table_circuits.rowCount())]+['no_customer']
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
    
                