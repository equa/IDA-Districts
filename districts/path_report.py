from .utility_functions.db import *
from .utility_functions.topology import *

from .utility_functions.workers import *

class WorkerPathReport(QRunnable):
    """Worker thread
    Inherits from QRunnable to handle worker thread setup, signals and wrap-up."""
    def __init__(self,*args,**kwargs):
        super().__init__()
        self.args=args
        #print('WorkerPathReport')
        #print(kwargs)
        self.signals=APISignals()
        self.config=kwargs['config']
        self.dlg=kwargs['dlg']
        if self.dlg:
            self.dlg.process_running=True

        self.cur=""
        self.plugin_dir=kwargs['plugin_dir']
        self.conn = dbConnect(self.config,True)
        if self.conn:
            self.cur=self.conn.cursor(cursor_factory = psycopg2.extras.RealDictCursor)
            
    def getLineendFeatureId(self,lid,conn_type_seq):
        sql="""SELECT c.id, ST_Z(ST_EndPoint(l.geom)) AS height, 'customer' AS type
    FROM "{}".customers c, "{}".lines l, "{}".customer_connections c_conns
    WHERE c_conns.c_seq={} AND c_conns.cid=c.id AND l.id=c_conns.lid AND l.id={}
    GROUP BY c.id,l.geom
UNION
SELECT ep.id, ST_Z(ST_EndPoint(l.geom)) AS height, 'energy_plant' AS type
    FROM "{}".energy_plants ep, "{}".lines l, "{}".energy_plant_connections ep_conns
    WHERE ep_conns.ep_seq={} AND ep_conns.epid=ep.id AND l.id=ep_conns.lid AND l.id={}
    GROUP BY ep.id,l.geom;""".format(self.config['versionName'],self.config['versionName'],self.config['versionName'],conn_type_seq,lid,# nosec B608
    self.config['versionName'],self.config['versionName'],self.config['versionName'],conn_type_seq,lid) # nosec B608
        #print(sql)
        self.cur.execute(sql)
        data=self.cur.fetchone()
        if data:
            return [[str(data['id'])],data['type']]
        else:
            return [None,None]
        
    def getEnergyPlantLid(self,epid,conn_type_seq):
        sql="""SELECT ep.id AS epid, l.id AS lid, ST_length(l.geom) AS length, ST_Z(ST_StartPoint(l.geom)) AS height
    FROM "{}".energy_plants ep, "{}".lines l, "{}".energy_plant_connections ep_conns
    WHERE  ep.id = {} AND ep_conns.ep_seq = {} AND ep_conns.epid=ep.id AND l.id=ep_conns.lid 
    GROUP BY ep.id,l.id, height,l.geom;""".format(self.config['versionName'],self.config['versionName'],self.config['versionName'],epid,conn_type_seq) # nosec B608
        #print(sql)
        self.cur.execute(sql)
        data=self.cur.fetchone()
        epid=[str(data['epid']),data['height']]
        lid=[data['lid'],data['length']]
        return [epid,lid]

    def getMainEnergyPlantData(self,network,epid):
        sql="""SELECT ep.id AS epid, l.id AS lid, ST_length(l.geom) AS length, ST_Z(ST_StartPoint(l.geom)) AS height,ep.submodel, b_t_conns.conn_type_id
    FROM "{}".energy_plants ep, "{}".lines l,energy_plant_templates ep_t, bundle_type_conns b_t_conns, "{}".energy_plant_connections ep_conns
    WHERE {} = ANY (ep.network) AND l.network={} AND ep_t.template=ep.template AND
        ep_conns.ep_seq=b_t_conns.sequence AND b_t_conns.conn_bundle_type_id=ep_t.conn_bundle_type AND ep_conns.epid=ep.id AND l.id=ep_conns.lid AND ep.id={}
    GROUP BY ep.id,l.id, height,l.geom, b_t_conns.conn_type_id;""".format(self.config['versionName'],self.config['versionName'],self.config['versionName'],network,network,epid) # nosec B608
        #print(sql)
        self.cur.execute(sql)
        data=self.cur.fetchone()
        epid=[str(data['epid']),data['height']]
        lid=[str(data['lid']),data['length']]
        return [epid,lid,data['submodel'],data['conn_type_id']]
        
    def orderLids(self,lids,lid_start):
        """returns [[str(id),length]]"""
        #print('order lids')
        path=[0]
        lids_new=[lid_start]
        #print(lid_start[1])
        for i in range(len(lids)-1):
            sql="""SELECT l2.id,ST_3DLength(l2.geom) AS length
    FROM "{}".lines l1, "{}".lines l2
    WHERE l1.id!=l2.id AND l1.id={} AND l2.id IN ({}) AND ST_dWithIn(ST_EndPoint(l1.geom),l2.geom,0.0001) """.format(self.config['versionName'],self.config['versionName'],lids_new[-1][0],",".join([str(lid) for lid in lids])) # nosec B608
            #print(sql)
            self.cur.execute(sql)
            data=self.cur.fetchone()
            lids_new.append([data['id'],data['length']])
        #print(lids_new)
        return lids_new
        
    def generatePathReport(self):
        """Just fo supply and return line. Todo update to all connection types"""
        #print('generate path diagram')
        self.conn=dbConnect(self.config,False)
        if self.dlg.rbtn_pathTemp.isChecked():
            quantity='temperature'
            quantity_var='temp'
        elif self.dlg.rbtn_pathPressure.isChecked():
            quantity='pressure'  
            quantity_var='p'
           
        col_sup=''
        col_ret=''
        if self.conn:
            self.cur=self.conn.cursor(cursor_factory = psycopg2.extras.RealDictCursor)
                            
            submodels=getNetworkSubmodels(self.cur,self.config,[self.dlg.network.currentText()])
            
            ep_c_b_type=getConnBundleByFeature('energy_plant',self.dlg.main_plant.currentText(),self.cur,self.config)
            ep_connValues=getConnsValues(ep_c_b_type,self.cur)
            #print(ep_connValues)
            ep_c_type_seq=getConnTypeSeqFromBundle(self.cur,self.config,ep_c_b_type,self.dlg.conn_type.currentText())
            #print(ep_c_type_seq)
            p_ep_sup_ident=getPMT2muxIdentFromConnValues(ep_connValues,int(self.dlg.sup_sequence.currentText()),conn_t_seq=ep_c_type_seq)
            p_ep_ret_ident=getPMT2muxIdentFromConnValues(ep_connValues,int(self.dlg.ret_sequence.currentText()),conn_t_seq=ep_c_type_seq)
            #print(p_ep_sup_ident)
            #print(p_ep_ret_ident)
            f_connValues=getConnsValues(self.dlg.f_conn_bundle_type.currentText(),self.cur)
            p_f_sup_ident=getPMT2muxIdentFromConnValues(f_connValues,int(self.dlg.sup_sequence.currentText()))
            p_f_ret_ident=getPMT2muxIdentFromConnValues(f_connValues,int(self.dlg.ret_sequence.currentText()))
            #print(p_f_sup_ident)
            #print(p_f_ret_ident)
            
            self.signals.progress.emit(10)  
            
            if self.dlg.rbtn_lineIds.isChecked():   
                self.dlg.lids=[int(self.dlg.listWidget_ids.item(i).text()) for i in range(self.dlg.listWidget_ids.count())]
                #print(self.dlg.lids)
                
                #ep id
                epid,lid_start=self.getEnergyPlantLid(self.dlg.main_plant.currentText(),ep_c_type_seq)
                if lid_start[0] not in self.dlg.lids:
                    self.signals.error.emit("Energy plant not connected to selected line ID`s!")
                    return None

                self.dlg.lids=self.orderLids(self.dlg.lids,lid_start)
                
                #feature id
                fids,f_type=self.getLineendFeatureId(self.dlg.lids[-1][0],[i['conn_type_seq'] for i in f_connValues if str(i['conn_type_id'])==self.dlg.f_conn_type.currentText()][0])  
                if not fids:
                    self.signals.error.emit("No line with the selected ID`s is connected to a feature!")
                    return None
                #print(fids)
                
            elif self.dlg.rbtn_weakPoint.isChecked() or self.dlg.rbtn_customer.isChecked() or self.dlg.rbtn_energy_plant.isChecked():              
                #set up topology
                sql="""TRUNCATE temp.streets_help;
INSERT INTO temp.streets_help (geom,length_m) SELECT ST_Force2D(geom),ST_3Dlength(geom) FROM "{}".lines;
SELECT pgr_createTopology('temp.streets_help',0.0001,'geom','id',clean:='true');""".format(self.config['versionName']) # nosec B608
                self.cur.execute(sql)
                
                sql="""SELECT st_v.id::integer AS vid FROM temp.streets_help_vertices_pgr st_v,"{}".energy_plants ep WHERE ST_dWithin(ep.geom,st_v.the_geom,0.0001) AND ep.id={};""".format(self.config['versionName'],self.dlg.main_plant.currentText()) # nosec B608
                #print(sql)
                self.cur.execute(sql)
                v_epid=self.cur.fetchone()['vid']
                #print(v_epid)
                
                f_type='customer' if self.dlg.rbtn_weakPoint.isChecked() or self.dlg.rbtn_customer.isChecked() else 'energy_plant'
                fids=[self.dlg.listWidget_ids.item(i).text() for i in range(self.dlg.listWidget_ids.count())]
            
            self.signals.progress.emit(20)  
            
            if self.dlg.rbtn_maxValue.isChecked():
                sql="""WITH sub AS(
    SELECT var_f.fid,max(var_ep."${}"-var_f."${}") as dvar FROM {}.{}_s_{}${} var_f, {}.energy_plant_s_{}${} var_ep 
        WHERE var_f.time=var_ep.time AND var_ep.fid={}{}
        GROUP BY var_f.fid
        ORDER BY dvar DESC
        LIMIT 1
)
SELECT sub.fid, sub.dvar, var_f1.time, var_f1."${}" as sup_f, var_f2."${}" as ret_f, ST_Z(var_f1.geom) AS height_f, var_ep1."${}" as sup_ep, var_ep2."${}" as ret_ep, ST_Z(var_ep1.geom) AS height_ep 
    FROM sub, {}.{}_s_{}${} var_f1, {}.{}_s_{}${} var_f2, {}.energy_plant_s_{}${} var_ep1, {}.energy_plant_s_{}${} var_ep2
    WHERE var_f1.time=var_ep1.time AND var_ep2.time=var_ep1.time AND var_f2.time=var_ep1.time AND var_ep1.fid={} AND var_ep1.fid=var_ep2.fid AND var_ep1."${}"-var_f1."${}" = sub.dvar AND sub.fid=var_f1.fid AND sub.fid=var_f2.fid{};""".format( # nosec B608
        quantity_var,quantity_var,self.config['versionName'],f_type,quantity_var,p_f_sup_ident,self.config['versionName'],quantity_var,p_ep_sup_ident,# nosec B608
        self.dlg.main_plant.currentText(),' AND var_f.fid IN({})'.format(','.join(fids)) if self.dlg.rbtn_customer.isChecked() or self.dlg.rbtn_energy_plant.isChecked() or self.dlg.rbtn_lineIds.isChecked() else '', # nosec B608
        quantity_var,quantity_var,quantity_var,quantity_var, # nosec B608
        self.config['versionName'],f_type, quantity_var, p_f_sup_ident,self.config['versionName'],f_type,quantity_var,p_f_ret_ident,self.config['versionName'],quantity_var, p_ep_sup_ident,self.config['versionName'],quantity_var, p_ep_ret_ident, # nosec B608
        self.dlg.main_plant.currentText(), quantity_var, quantity_var, ' AND var_f1.fid IN({})'.format(','.join(fids)) if self.dlg.rbtn_customer.isChecked() or self.dlg.rbtn_energy_plant.isChecked() or self.dlg.rbtn_lineIds.isChecked() else '') # nosec B608
            else:
                sql="""SELECT var_f1.fid, var_ep1."${}" - var_f1."${}" AS dvar, var_f1.time, var_f1."${}" as sup_f, var_f2."${}" as ret_f, ST_Z(var_f1.geom) AS height_f, var_ep1."${}" as sup_ep, var_ep2."${}" as ret_ep, ST_Z(var_ep1.geom) AS height_ep 
    FROM {}.{}_s_{}${} var_f1, {}.{}_s_{}${} var_f2, {}.energy_plant_s_{}${} var_ep1, {}.energy_plant_s_{}${} var_ep2
    WHERE var_f1.time='{}' AND var_f1.time=var_ep1.time AND var_ep2.time=var_ep1.time AND var_f2.time=var_ep1.time AND var_ep1.fid={} AND var_ep1.fid=var_ep2.fid AND var_f1.fid = var_f2.fid {}
    ORDER BY dvar DESC
    LIMIT 1;""".format(quantity_var,quantity_var,quantity_var,quantity_var,quantity_var,quantity_var, # nosec B608
        self.config['versionName'],f_type, quantity_var, p_f_sup_ident,self.config['versionName'],f_type, quantity_var, p_f_ret_ident,self.config['versionName'], quantity_var, p_ep_sup_ident,self.config['versionName'], quantity_var, p_ep_ret_ident, # nosec B608
        self.dlg.date_input.text(),self.dlg.main_plant.currentText(), ' AND var_f1.fid IN({})'.format(','.join(fids)) if self.dlg.rbtn_customer.isChecked() or self.dlg.rbtn_energy_plant.isChecked() or self.dlg.rbtn_lineIds.isChecked() else '') # nosec B608
    
            #print(sql)
            self.cur.execute(sql)
            
            self.dlg.weak_point=self.cur.fetchone()
            #print(self.dlg.weak_point)  
            if not self.dlg.weak_point:
                self.signals.error.emit("No data found! Please check if results are loaded or within the selected period.")
                return None
                
            self.signals.progress.emit(30)  
            
            if not self.dlg.rbtn_lineIds.isChecked():
                #get line with shortest path
                sql="""SELECT st_v.id::integer AS vid FROM temp.streets_help_vertices_pgr st_v,"{}".customers f WHERE ST_dWithin(f.geom,st_v.the_geom,0.0001) AND f.id={};""".format(self.config['versionName'],self.dlg.weak_point['fid']) # nosec B608
                #print(sql)
                self.cur.execute(sql)
                v_id=self.cur.fetchone()['vid']
                #print(v_id)
                
                sql="""WITH sub As(
    SELECT seq, node, edge, cost
            FROM pgr_dijkstra(
                'SELECT sh.id, sh.source, sh.target, sh.length_m as cost FROM temp.streets_help sh',
                {}, 
                {},
                false
            )
)
SELECT l.id,ST_3DLength(l.geom) AS length FROM sub,temp.streets_help st_h, "{}".lines l WHERE sub.edge=st_h.id AND st_h.geom=st_force2D(l.geom);""".format(v_epid,v_id,self.config['versionName']) # nosec B608
                self.cur.execute(sql)
                self.dlg.lids=[[lid['id'],lid['length']] for lid in self.cur.fetchall()]
                            
            self.signals.progress.emit(50)  
            
            sql="""WITH max_seg AS (
    SELECT lid, MAX(lid_seg) AS max_seg
    FROM {}.line_seg_{}
    GROUP BY lid
)
SELECT var1.fid,var1."${}" AS var1, var2."${}" AS var2, ABS(var1."${}" - var2."${}") AS dvar, ST_Z(ST_EndPoint(var1.geom)) AS height_j
    FROM {}.line_s_{}${} var1, {}.line_s_{}${} var2, max_seg
    WHERE var1.fid=var2.fid AND var1.time=var2.time AND var1.segment= var2.segment AND var1.segment=max_seg.max_seg AND var1.time = '{}' AND var1.fid IN ({}) AND max_seg.lid=var1.fid
    ORDER BY var1.fid;""".format( # nosec B608
    self.config['versionName'],quantity_var, # nosec B608
    quantity_var,quantity_var,quantity_var,quantity_var, # nosec B608
    self.config['versionName'], quantity_var, self.dlg.sup_sequence.currentText(),self.config['versionName'],quantity_var, self.dlg.ret_sequence.currentText(),  # nosec B608
    self.dlg.weak_point['time'],','.join([str(i[0]) for i in self.dlg.lids[:-1]])) # nosec B608
            #print(sql)
            self.cur.execute(sql)
            self.dlg.line_data=self.cur.fetchall()
            self.signals.progress.emit(70)  
            #print(self.dlg.lids)
            #print(self.dlg.line_data)
            line_data_map= {row['fid']: row for row in self.dlg.line_data}
            #print(line_data_map)
            self.dlg.line_data = [line_data_map[fid] for fid, _ in self.dlg.lids if fid in line_data_map]
            #print(self.dlg.line_data)
            
            self.signals.progress.emit(80)  
            self.dlg.path=[0]
            path_sum=0
            for lid in self.dlg.lids:
                path_sum+=lid[1]
                self.dlg.path.append(path_sum)
            #print(self.dlg.path)

            if self.dlg.rbtn_pathTemp.isChecked():
                dt=self.dlg.weak_point['sup_f'] - self.dlg.weak_point['ret_f']
                self.dlg.title='Simulationszeit='+str(self.dlg.weak_point['time'])+' h ; Kunden ID='+str(self.dlg.weak_point['fid'])+ ' ; Temperaturdifferenz Übergabestation: ' +str(round(dt,2))+' °C'
                #print(self.dlg.title)
                #title='Weakpoint; Time='+str(data_j[0])+'h ; '+weak_point_id[2].capitalize().replace('_',' ')+' ID='+weak_point_id[0]+'; Main energy plant ID='+epid[0]+'; Line Ids='+','.join([str(lid[0]) for lid in lids])
            elif self.dlg.rbtn_pathPressure.isChecked(): 
                dp=self.dlg.weak_point['dvar']*2
                self.dlg.title='Netzschlechtpunkt; Simulationszeit='+str(self.dlg.weak_point['time'])+'; Kunden ID='+str(self.dlg.weak_point['fid'])+ ' ; Druckverlust: ' +str(dp)+' Pa'
                #title='Simulationszeit='+str(data_j[0])+' h ; Kunden ID='+weak_point_id[0]+ ' ; Druckdifferenz: ' +str(dp)+' Pa'
            
            return True
        
    @pyqtSlot()
    def run(self):
        #print('generate pah report')
        self.progress_value=1
        self.signals.progress.emit(self.progress_value)
        try:
            result=self.generatePathReport()
            #print(result)
            if result:
                self.signals.finished.emit('finished')
                self.signals.progress.emit(100)  
            else:
                self.signals.finished.emit('failed')
                self.signals.progress.emit(0)  
        except Exception as e:
            self.signals.error.emit(str(e))  
            self.signals.progress.emit(0) 
            self.signals.finished.emit('failed')  
        