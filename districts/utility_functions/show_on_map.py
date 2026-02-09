from .db import *
from .workers import *
import psycopg2
from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT
import psycopg2.extras
from qgis.utils import iface

from qgis.PyQt.QtCore import QSettings, QTranslator, QCoreApplication,Qt,QThreadPool
from qgis.core import QgsTemplatedLineSymbolLayerBase,QgsMarkerSymbol,QgsSimpleMarkerSymbolLayer,QgsMarkerLineSymbolLayer,QgsRuleBasedRenderer,QgsLineSymbol,QgsClassificationQuantile,QgsGeometry,QgsVectorLayer,QgsFeature,QgsClassificationEqualInterval,QgsRendererRangeLabelFormat,QgsStyle,QgsGraduatedSymbolRenderer, QgsSingleSymbolRenderer,QgsSymbol,QgsFilledMarkerSymbolLayer,QgsSymbolLayer,QgsProperty,Qgis
from qgis.PyQt.QtWidgets import QShortcut,QAction,QListWidgetItem,QFileDialog,QStackedWidget,QListView,QLineEdit,QDialog,QTableWidgetItem



class WorkerShowOnMap(QRunnable):
    """Worker thread
    Inherits from QRunnable to handle worker thread setup, signals and wrap-up."""
    def __init__(self,*args,**kwargs):
        super().__init__()
        self.args=args
        print('WorkerShowOnMap')
        print(kwargs)
        self.signals=APISignals2()
        self.config=kwargs['config']
        self.dlg=kwargs['dlg']
        if self.dlg:
            self.dlg.process_running=True
        self.vars=kwargs['vars']
        self.feature= kwargs['feature']
        self.layer_name= kwargs['layer_name']
        self.lineSegVisLength= kwargs['lineSegVis']
        self.enable= kwargs['enable']
        self.conn=""
        self.cur=""
        self.plugin_dir=kwargs['plugin_dir']
        self.simData=kwargs['simData']
        self.time_values=['Values','Hourly average','Daily average','Monthly average']
        self.conn = dbConnect(self.config,True)
        self.vars=None
        if self.conn:
            self.cur=self.conn.cursor(cursor_factory = psycopg2.extras.RealDictCursor)

    def getShowOnMapVarsDict(self):
        """{'color'/'size'/'rotation':{'mode':'var'/'par'/False, 'name': var_name/par_name, 'var_function': function_items, 'table_name': DB table},time:{starttime,endtime},data}"""
        vars={'color': {'mode':False, 'name': '', 'var_function': '', 'table_name': ''},
            'size': {'mode':False, 'name': '', 'var_function': '', 'table_name': ''},
            'rotation': {'mode':False, 'name': '', 'var_function': '', 'table_name': ''},
            'time': {'starttime': '', 'endtime':'', 'dt':False, 'first_time_var': ''},
            'data': ''}
            
        if self.dlg:
            if self.dlg.checkbox_varColor.isChecked():
                if self.dlg.rbtn_colorVar.isChecked():
                    vars['color']['mode']='var'
                    vars['color']['var_function']=self.dlg.color_function.currentText()
                    vars['time']['starttime']=self.dlg.starttime.text()
                    vars['time']['endtime']=self.dlg.endtime.text()
                    name=self.dlg.color_var.currentText()
                    vars['color']['table_name']=self.dlg.color_table_name
                else:
                    vars['color']['mode']='par'
                    name=self.dlg.color_par.currentText()
                    vars['color']['table_name']=self.dlg.feature+'s'
                if name:
                    vars['color']['name']=name
            if self.dlg.checkbox_varSize.isChecked():
                if self.dlg.rbtn_sizeVar.isChecked():
                    vars['size']['mode']='var'
                    vars['size']['var_function']=self.dlg.size_function.currentText()
                    vars['time']['starttime']=self.dlg.starttime.text()
                    vars['time']['endtime']=self.dlg.endtime.text()
                    name=self.dlg.size_var.currentText()
                    vars['size']['table_name']=self.dlg.size_table_name    
                else:
                    vars['size']['mode']='par'
                    name=self.dlg.size_par.currentText()
                    vars['size']['table_name']=self.dlg.feature+'s'
                if name:
                    vars['size']['name']=name
            if self.dlg.checkbox_varRotation.isChecked():
                if self.dlg.rbtn_rotationVar.isChecked():
                    vars['rotation']['mode']='var'
                    vars['rotation']['var_function']=self.dlg.rotation_function.currentText()
                    vars['time']['starttime']=self.dlg.starttime.text()
                    vars['time']['endtime']=self.dlg.endtime.text()
                    name=self.dlg.rotation_var.currentText()
                    vars['rotation']['table_name']=self.dlg.rotation_table_name
                else:
                    vars['rotation']['mode']='par'
                    name=self.dlg.rotation_par.currentText()
                    vars['rotation']['table_name']=self.dlg.feature+'s'
                if name:
                    vars['rotation']['name']=name
        else:
            print('kwargs vars')
            vars=self.vars
            
        self.signals.progress.emit(5)  
        vars=self.getShowOnMapData(vars)
        return vars
    
    def getShowOnMapData(self,vars):
        print(vars)
        #drop old line_seg_%_vis tables
        sql="""WITH tables_to_drop AS (
    SELECT table_name
    FROM information_schema.tables
    WHERE table_schema = '{}'
      AND table_name LIKE 'line_s_%_vis'
)
SELECT execute_dynamic_sql(format('DROP TABLE "{}".%I;', table_name))
    FROM tables_to_drop;""".format(self.config['versionName'],self.config['versionName'])
        self.cur.execute(sql)
        
        if vars['color']['var_function'] in self.time_values:
            time_color=True
        else:
            time_color=False
        if vars['size']['var_function'] in self.time_values:
            time_size=True
        else:
            time_size=False  
        if vars['rotation']['var_function'] in self.time_values:
            time_rotation=True
        else:
            time_rotation=False
            
        self.first_time_var='color' if time_color else ('size' if time_size else ('rotation' if time_rotation else False))
        print('++first-time-var: '+str(self.first_time_var))
        if self.first_time_var:
            dt=getAvergageByMode(vars[self.first_time_var]['var_function'],self.cur,self.config,vars[self.first_time_var]['table_name']) #hours
        else:
            dt=False
        print(dt)
        first_par_var='color' if vars['color']['mode'] else ('size' if vars['size']['mode'] else ('rotation' if vars['rotation']['mode'] else False))
        print(self.first_time_var)
        print(first_par_var)
        first_group=self.first_time_var if self.first_time_var else first_par_var
        
        #if simulation results and line feature
        if self.simData and self.feature=='line':
            print('update DB with visualization tables')
            #re-create table line_seg_vis, which holds the geometry of the visualized pipe segements
            #check if > calculated segments
                
            srid=loadProjectConfig(self.plugin_dir,self.config['projectName'])['srid']
            
            #store cumulate simulation results in _vis table if lineSegVis!=0 and var
            if vars['color']['mode']=='var' and vars['color']['name'].split('$')[0] in ('temp','p') or vars['size']['mode']=='var' and vars['size']['name'].split('$')[0] in ('temp','p'):
                sql="""DROP TABLE IF EXISTS "{}".line_seg_vis;
CREATE TABLE IF NOT EXISTS "{}".line_seg_vis
(
    id serial,
    lid integer NOT NULL,
    lid_seg integer NOT NULL,
    geom geometry(LineStringZ,{})
);
SELECT segmentize({},'{}','line_seg_vis');""".format(self.config['versionName'],self.config['versionName'],srid,1000000 if vars['color']['var_function']=='specific dp' else self.lineSegVisLength,self.config['versionName'])
                print(sql)
                self.cur.execute(sql)
            
                #load var data to the coresponding visualization table using averaged values for merged segments
                if vars['color']['mode']=='var' and vars['color']['var_function']!='specific dp' :
                    sql="""DROP TABLE IF EXISTS "{}".line_s_{}_vis CASCADE;
CREATE TABLE "{}".line_s_{}_vis
(
	id serial,
    fid integer,
    time timestamp,
	geom geometry(LineStringZ,{}),
	segment integer,
	"${}" numeric,
	CONSTRAINT line_s_{}_vis_pkey PRIMARY KEY (id)
);""".format(self.config['versionName'],vars['color']['name'],self.config['versionName'],vars['color']['name'],srid,vars['color']['name'].split('$')[0],vars['color']['name'])
                    
                    if vars['color']['name'].split('$')[0]=='p': #linear interpolation using pressure values at start and end of the line
                        print('++++interpoation++++')
                        sql+="""\nINSERT INTO "{}".line_s_{}_vis (fid,time,"${}",geom,segment)
    SELECT s.fid,time,s.seg1_v+CASE WHEN seg_counter.count=1 THEN (s.seg2_v-s.seg1_v)/2 ELSE (s.seg2_v-s.seg1_v)/(seg_counter.count-1)*(seg.lid_seg-1) END AS value,seg.geom,seg.lid_seg
        FROM 
            (Select a.fid,a."$p" AS seg1_v,b."$p" AS seg2_v,a.time
                FROM (SELECT fid,"$p",time FROM "{}".line_s_{} WHERE segment =1 ORDER BY fid,time) a,
                    (SELECT fid,"$p",time FROM "{}".line_s_{} WHERE segment =2 ORDER BY fid,time) b
                WHERE a.fid=b.fid AND a.time=b.time
                ORDER BY a.fid,a.time) s, 
            "{}".line_seg_vis seg,
            (SELECT lid, count(*) AS count FROM "{}".line_seg_vis GROUP BY lid ORDER BY lid) seg_counter
        WHERE  seg_counter.lid=s.fid AND s.fid=seg.lid AND time BETWEEN '{}' AND '{}'
        ORDER BY s.fid,seg.lid_seg,time;""".format(self.config['versionName'],vars['color']['name'],vars['color']['name'].split('$')[0],self.config['versionName'],vars['color']['name'],self.config['versionName'],vars['color']['name'],self.config['versionName'],self.config['versionName'],vars['time']['starttime'],vars['time']['endtime'])    
                    else:
                        sql+="""\nINSERT INTO "{}".line_s_{}_vis (fid,time,"${}",geom,segment)
    SELECT s.fid,time,avg(s."${}") AS value,seg.geom,seg.lid_seg
        FROM "{}".line_s_{} s, "{}".line_seg_vis seg
        WHERE ST_dwithin(ST_LineSubstring(seg.geom,0.01,0.99),s.geom,0.001) AND s.fid=seg.lid AND time BETWEEN '{}' AND '{}'
        GROUP BY time,s.fid,seg.geom,seg.lid_seg
        ORDER BY fid,lid_seg,time;""".format(self.config['versionName'],vars['color']['name'],vars['color']['name'].split('$')[0],vars['color']['name'].split('$')[0],self.config['versionName'],vars['color']['name'],self.config['versionName'],vars['time']['starttime'],vars['time']['endtime'])
                    sql+="""CREATE INDEX "idx_line_s_{}_vis_fid_time_segment" ON {}."line_s_{}_vis" (fid, time, segment);""".format(vars['color']['name'],self.config['versionName'],vars['color']['name'])
                    print(sql)
                    self.cur.execute(sql)
                    
                    vars['color']['table_name']=vars['color']['table_name']+'_vis'
                
                if vars['size']['mode']=='var':
                    if vars['color']['name'] !=  vars['size']['name']: #if color and size car name is same --> do not twice
                        sql="""DROP TABLE IF EXISTS "{}".line_s_{}_vis CASCADE;
CREATE TABLE "{}".line_s_{}_vis
(
	id serial,
    fid integer,
    time timestamp,
	geom geometry(LineStringZ,{}),
	segment integer,
	"${}" numeric, -- use $ in order not to have a conflict the var column with oder columns
	CONSTRAINT line_s_{}_vis_pkey PRIMARY KEY (id)
);""".format(self.config['versionName'],vars['size']['name'],self.config['versionName'],vars['size']['name'],srid,vars['size']['name'].split('$')[0],vars['size']['name'])
                        sql+="""\nINSERT INTO "{}".line_s_{}_vis (fid,time,"${}",geom,segment)
    SELECT s.fid,time,avg(s."${}") AS value,seg.geom,seg.lid_seg
        FROM "{}".line_s_{} s, "{}".line_seg_vis seg
        WHERE ST_dwithin(ST_LineSubstring(seg.geom,0.01,0.99),s.geom,0.001) AND s.fid=seg.lid AND time BETWEEN '{}' AND '{}'
        GROUP BY time,s.fid,seg.geom,seg.lid_seg
        ORDER BY fid,lid_seg,time;""".format(self.config['versionName'],vars['size']['name'],vars['size']['name'].split('$')[0],vars['size']['name'].split('$')[0],self.config['versionName'],vars['size']['name'],self.config['versionName'],vars['time']['starttime'],vars['time']['endtime'])
                        sql+="""CREATE INDEX "idx_line_s_{}_vis_fid_time_segment" ON {}."line_s_{}_vis" (fid, time, segment);""".format(vars['size']['name'],self.config['versionName'],vars['size']['name'])
                        print(sql)
                        self.cur.execute(sql)
                        
                    
                    vars['size']['table_name']=vars['size']['table_name']+'_vis'
                    
        self.signals.progress.emit(10)
        print('get-data')
        if self.first_time_var or first_par_var:
            sql="""SELECT {}.{} AS fid, ST_AsText({}.geom) AS geom {}, {}
    FROM {}{}{}
    GROUP BY {}
    ORDER BY {} {}.{};""".format(first_group,'fid' if vars[first_group]['mode']=='var' else 'id',first_group,
                """,date_trunc('{}', {}.time) AS time""".format(dt,self.first_time_var) if self.first_time_var and dt in ['hour','day','month'] else (',{}.time'.format(self.first_time_var) if self.first_time_var else ''),
                ','.join([i for i in
                [('avg(color."${}") AS color'.format(vars['color']['name'].split('$')[0]) if dt else 'color."${}" AS color'.format(vars['color']['name'].split('$')[0])) if time_color else ('color.color' if vars['color']['mode']=='var' else ('color."{}"'.format(vars['color']['name']) +' AS color' if vars['color']['mode'] else '')),
                'avg(size."${}") AS size'.format(vars['size']['name'].split('$')[0]) if time_size else ('size.size' if vars['size']['mode']=='var' else ('size."{}"'.format(vars['size']['name']) +' AS size' if vars['size']['mode'] else '')),
                'avg(rotation."${}") AS rotation'.format(vars['rotation']['name'].split('$')[0]) if time_rotation else ('rotation.rotation' if vars['rotation']['mode']=='var' else ('rotation."{}"'.format(vars['rotation']['name']) +' AS rotation' if vars['rotation']['mode'] else '') )] 
                if i]),
                ','.join([i for i in  #from
                    [""""{}".{} color""".format(self.config['versionName'],vars['color']['table_name']) if time_color else (
                    """({}) color""".format(self.getNonTimeVarFunctionValue(vars['color'],'color',vars['time'])) 
                    if vars['color']['mode']=='var' else ('"{}".{} AS color'.format(self.config['versionName'],vars['color']['table_name']) if vars['color']['mode']=='par' else '')),
                    """"{}".{} size""".format(self.config['versionName'],vars['size']['table_name']) if time_size else (
                    """({}) size""".format(self.getNonTimeVarFunctionValue(vars['size'],'size',vars['time']))  
                    if vars['size']['mode']=='var'else ('"{}".{} AS size'.format(self.config['versionName'],vars['size']['table_name']) if vars['size']['mode']=='par' else '')),
                    """"{}".{} rotation""".format(self.config['versionName'],vars['rotation']['table_name']) if time_rotation else (
                    """({}) rotation""".format(self.getNonTimeVarFunctionValue(vars['rotation'],'rotation',vars['time'])) 
                    if vars['rotation']['mode']=='var' else ('"{}".{} AS rotation'.format(self.config['versionName'],vars['rotation']['table_name']) if vars['rotation']['mode']=='par' else ''))] 
                    if i]),
                '\n    WHERE ' if len([var for var in vars if var not in ['time','data']and vars[var]['mode']])>=2  or self.first_time_var else '',
                ' AND '.join([i for i in #where
                    [' AND '.join([first_group+('.fid=' if vars[first_group]['mode']=='var' else '.id=')+var+('.fid' if vars[var]['mode']=='var' else '.id') 
                        for var in vars if var not in ['time','data']+[first_group] and vars[var]['mode']]),
                        
                    ' AND '.join([first_group+'.geom='+var+'.geom' 
                        for var in vars if self.first_time_var and var not in ['time','data']+[self.first_time_var] and vars[var]['mode']=='var']),    
                        
                    ' AND '.join([self.first_time_var+'.time='+var+'.time' for var in vars if var not in ['time','data']+[self.first_time_var] and vars[var]['var_function'] in self.time_values]),
                    """{}.time <= '{}' AND {}.time >= '{}'""".format(self.first_time_var,vars['time']['endtime'],self.first_time_var,vars['time']['starttime']) if self.first_time_var else ''] if i]),
                ','.join([i for i in #group by
                    ["ST_asText({}.geom)".format(first_group),
                    """date_trunc('{}', {}.time)""".format(dt,self.first_time_var) if self.first_time_var and dt in ['hour','day','month'] else ('{}.time'.format(self.first_time_var) if self.first_time_var else ''),
                    '{}.{}'.format(first_group,'fid' if vars[first_group]['mode']=='var' else 'id'),
                    ','.join([var+'.'+(var if vars[var]['mode']=='var' and vars[var]['var_function']!='Values' else '"'+('$' if vars[var]['mode']=='var' else '')+vars[var]['name'].split('$')[0]+'"') for var in vars if var not in ['time','data'] and (vars[var]['mode'] and vars[var]['var_function'] not in self.time_values or vars[var]['var_function']=='Values')])] if i]),
                """date_trunc('{}', {}.time),""".format(dt,self.first_time_var) if self.first_time_var and dt in ['hour','day','month'] else ('{}.time,'.format(self.first_time_var) if self.first_time_var else ''), #order by
                first_group,'fid' if vars[first_group]['mode']=='var' else 'id')
            print(sql)
        self.cur.execute(sql)
        data=self.cur.fetchall()
        self.signals.progress.emit(60)  
        #get dt if not averaged
        if not dt and self.first_time_var:
            sql="""WITH sub AS(
    SELECT a.time-LAG(a.time, 1) OVER () as dt
        FROM (SELECT time FROM "{}".{} GROUP BY time) a
        GROUP BY time 
        ORDER BY time
)
SELECT EXTRACT(epoch FROM dt)/3600 AS dt FROM sub WHERE dt IS NOT NULL LIMIT 1;""".format(self.config['versionName'],vars[self.first_time_var]['table_name'])
            print(sql)
            self.cur.execute(sql)
            dt=self.cur.fetchone()['dt']
            print(dt)

        vars['data']=data
        vars['time']['dt']=dt
        vars['time']['first_time_var']=self.first_time_var
        return vars
    
    def getNonTimeVarFunctionValue(self,var,type,time):
        if var['var_function']=='Max':
            sql="""SELECT fid,geom AS geom,max("${}") AS {} FROM "{}".{} WHERE time BETWEEN '{}' AND '{}' GROUP BY fid,geom ORDER BY fid""".format(var['name'].split('$')[0],type,self.config['versionName'],var['table_name'],time['starttime'],time['endtime'])
        elif var['var_function']=='Min':
            sql="""SELECT fid,geom AS geom,min("${}") AS {} FROM "{}".{} WHERE time BETWEEN '{}' AND '{}' GROUP BY fid,geom ORDER BY fid""".format(var['name'].split('$')[0],type,self.config['versionName'],var['table_name'],time['starttime'],time['endtime'])
        elif var['var_function']=='Average':
            sql="""SELECT fid,geom AS geom,avg("${}") AS {} FROM "{}".{} WHERE time BETWEEN '{}' AND '{}' GROUP BY fid,geom ORDER BY fid""".format(var['name'].split('$')[0],type,self.config['versionName'],var['table_name'],time['starttime'],time['endtime'])
        elif var['var_function']=='Last value':
            sql="""SELECT DISTINCT ON (fid{}) 
    fid,geom,"${}" AS {},time
FROM "{}".{}
WHERE time <= '{}'
ORDER BY fid{},time DESC""".format(',segment' if var['name'].split('$')[0] in ['p','temp'] and 'line_' in var['table_name'] else '' ,var['name'].split('$')[0],type,self.config['versionName'],var['table_name'],time['endtime'],',segment' if var['name'].split('$')[0] in ['p','temp'] and 'line_' in var['table_name'] else '')
        elif var['var_function']=='Sum':
             sql="""SELECT fid,geom AS geom,sum("${}") AS {} FROM "{}".{} WHERE time BETWEEN '{}' AND '{}' GROUP BY fid,geom ORDER BY fid""".format(var['name'].split('$')[0],type,self.config['versionName'],var['table_name'],time['starttime'],time['endtime'])
        elif var['var_function']=='First value':
            sql="""SELECT DISTINCT ON (fid{}) 
    fid,geom AS geom,"${}" AS {},time
FROM "{}".{}
WHERE time >= '{}'
ORDER BY fid{},time ASC""".format(',segment' if var['name'].split('$')[0] in ['p','temp'] and 'line_' in var['table_name'] else '',var['name'].split('$')[0],type,self.config['versionName'],var['table_name'],time['starttime'],',segment' if var['name'].split('$')[0] in ['p','temp'] and 'line_' in var['table_name'] else '')
        elif var['var_function']=='specific dp':
            sql="""WITH length_per_fid AS (
    SELECT lid AS fid, st_length(geom) AS len, geom
    FROM {}.line_seg_vis
)
SELECT 
    a.fid,lp.geom,
    MAX(ABS(a."$p" - b."$p") / lp.len) AS {}
FROM {}.{} a
JOIN {}.{} b
    ON a.fid = b.fid
   AND a.time = b.time
   AND a.segment = 1
   AND b.segment = 2
JOIN length_per_fid lp
    ON lp.fid = a.fid
WHERE a.time between '{}' and '{}'
GROUP BY a.fid, lp.geom""".format(
                self.config['versionName'],type,self.config['versionName'],var['table_name'],self.config['versionName'],var['table_name'],time['starttime'],time['endtime'])
        return sql

            
    def showOnMap(self):
        self.vars=self.getShowOnMapVarsDict()      
        self.signals.progress.emit(65)  
        self.showOnMapMemoryLayer()

    def showOnMapMemoryLayer(self):   
        print('showOnMapMemoryLayer')
        column_names=[self.vars[var]['name'].split('$')[0] for var in self.vars if var not in ['time','data'] and self.vars[var]['mode']]
        column_types=[var for var in self.vars if var not in ['time','data'] and self.vars[var]['mode']]
        print(column_names)
        print(column_types)
        
        # make new memory layer
        self.temp_layer = QgsVectorLayer("{}?crs=epsg:{}&field=id:integer&{}{}".format(
            'LineStringZ' if self.feature=='line' else 'PointZ',
            loadProjectConfig(self.plugin_dir,self.config['projectName'],signals=self.signals)['srid'],
            'field=time:datetime&' if self.vars['time']['first_time_var'] else '',
            '&'.join(['field={}:numeric'.format(type+'_'+name) for type,name in zip(column_types,column_names)])),self.layer_name, "memory")
        self.temp_layer.startEditing()
        print('temp_layer generated')

        #make new features
        for i in self.vars['data']:
            feat = QgsFeature(self.temp_layer.fields())
            feat["id"] = i['fid']
            if self.vars['time']['first_time_var']:
                feat["time"] = str(i['time'])
            feat.setGeometry(QgsGeometry.fromWkt(i['geom']))
            for type,name in zip(column_types,column_names):
                feat[type+'_'+name]=float(i[type])
            self.temp_layer.addFeature(feat)
        print('features added')

                
        self.signals.progress.emit(98)     
                
        self.signals.finished.emit('',self)
        
    @pyqtSlot()
    def run(self):
        print('Show data on map')
        self.progress_value=1
        self.signals.progress.emit(self.progress_value)
        try:
            self.showOnMap()
        except Exception as e:
            self.signals.error.emit(str(e))  
            self.signals.progress.emit(0) 
        self.signals.progress.emit(100)  
        self.signals.finished.emit('finished',self)  
