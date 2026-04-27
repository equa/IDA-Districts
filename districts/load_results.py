from qgis.PyQt.QtCore import QObject, pyqtSlot, pyqtSignal,QRunnable

from .utility_functions.files import *
from .utility_functions.db import *
from .utility_functions.dialog import *
from .utility_functions.topology import *
from .utility_functions.workers import APISignals

import datetime
import re


class WorkerLoadResults(QRunnable):      
    """Worker thread
    Inherits from QRunnable to handle worker thread setup, signals and wrap-up."""
    def __init__(self,*args,**kwargs):
        super().__init__()
        self.args=args
        #print(args)
        self.signals=APISignals()
        self.config=kwargs['config']
        self.dlg=kwargs['dlg']
        self.dlg.process_running=True
        self.conn=""
        self.cur=""
        self.plugin_dir=kwargs['plugin_dir']
        self.submodels=kwargs['submodels']
        self.simulatedOutputs=kwargs['simulatedOutputs']
        self.conn = dbConnect(self.config,True)
        if self.conn:
            self.cur=self.conn.cursor(cursor_factory = psycopg2.extras.RealDictCursor)
            
    @pyqtSlot()
    def run(self):
        #print('run worker load results')
        self.progress_value=1
        self.signals.progress.emit(self.progress_value)
        self.loadResults()
        self.signals.progress.emit(100)  
        self.signals.finished.emit('Loading results has been successfully completed!')  
        
    def loadResults(self):
        #print('-***-')
        networkSimData=loadNetworkSimData(self.plugin_dir,self.config)

        srid=loadProjectConfig(self.config)['srid']
        modellingSettings=loadModellingSettings(self.plugin_dir,self.config)

        #re-create table line_seg for temperature (according to the pipe distrectization) and pressure (2 segments per line), which holds the geometry of the simulated pipe segements
        sql='\n'.join(["""DROP TABLE IF EXISTS "{}".line_seg_{};
CREATE TABLE IF NOT EXISTS "{}".line_seg_{}
(
    id serial,
    lid integer NOT NULL,
    lid_seg integer NOT NULL,
    geom geometry(LineStringZ,{})
);
{}""".format(self.config['versionName'],output.split('_')[0],self.config['versionName'],output.split('_')[0],srid,
            "SELECT segmentize({},'{}','line_seg_temp');".format(modellingSettings['fd_meterPerNode'],self.config['versionName']) if output=='temp_lines' else "SELECT halve_geom('{}','line_seg_p');".format(self.config['versionName']))
            for output in self.simulatedOutputs if output in ['temp_lines','p_lines'] and self.simulatedOutputs[output]])
        if sql:
            #print(sql)
            self.cur.execute(sql)
        
        for i in range(self.dlg.combo_submodels.count()):
            if self.dlg.combo_submodels.itemText(i) != 'Check all items' and self.dlg.combo_submodels.itemChecked(i):
                try:
                    submodel=self.dlg.combo_submodels.itemText(i)
                    #print(submodel)
                    match = re.match(r'\d+', submodel)
                    if match:
                        submodel_id = match.group()
                        #print(submodel_id)
                    else:
                        self.signals.error.emit('Please select a model, which starts with an Integer and belongs to one of your modeled networks.')
                        return False
                    
                    dir_path=self.config['pathProjects']+'{}\\versions\\{}\\network_{}\\'.format(self.config['projectName'],self.config['versionName'],submodel)
                    pipe_sequences=getUsedPipeBundleSequences(self.cur,self.config)
                    #-----update DB tables--------
                    #-----------create tables----------------
                    #customer tables: customer_s_troom, customer_s_balance, customer_s_conntype_[conn type seq]
                    c_outputs=[output.split('_')[0] for output in self.simulatedOutputs if output.split('_')[1]=='c' and self.simulatedOutputs[output]]
                    if c_outputs:
                        used_b_types=getUsedConnBundleTypes('customer',self.cur,self.config)
                        c_conn_outputs=[output.split('_')[0] for output in self.simulatedOutputs if output.split('_')[1]=='c' and self.simulatedOutputs[output] and output.split('_')[0] not in['troom','heatbalance','power','qsup']]
                        c_power_outputs=[output.split('_')[0] for output in self.simulatedOutputs if output.split('_')[1]=='c' and self.simulatedOutputs[output] and output.split('_')[0] in ['power']]
                        conn_names= [ident for connBundleType in used_b_types for ident in getPMT2muxIdents(self.cur,connBundleType)]
                        conn_t_power_names= getUsedConnTypeIdents('customer',self.cur,self.config)
                        tables=[]
                        
                        #print(conn_names)
                        #print(conn_t_power_names)
                        #connection tables (p,m,T)
                        sql='\n'.join(["""DROP TABLE IF EXISTS "{}".customer_s_{}${} CASCADE;
CREATE TABLE "{}".customer_s_{}${}
(
	id serial,
    fid integer,
    time timestamp,
	geom geometry(PointZ,{}),
	"${}" numeric,
	CONSTRAINT customer_s_{}${}_pkey PRIMARY KEY (id)
);""".format(self.config['versionName'],output,conn_name,self.config['versionName'],output,conn_name,srid,output,output,conn_name) 
                            for output in c_conn_outputs for conn_name in conn_names])
                        tables+=["customer_s_{}${}".format(output,conn_name) for output in c_conn_outputs for conn_name in conn_names]
                        
                        #connection type tables (power)
                        sql+='\n'.join(["""DROP TABLE IF EXISTS "{}".customer_s_{}${} CASCADE;
CREATE TABLE "{}".customer_s_{}${}
(
	id serial,
    fid integer,
    time timestamp,
	geom geometry(PointZ,{}),
	"${}" numeric,
	CONSTRAINT customer_s_{}${}_pkey PRIMARY KEY (id)
);""".format(self.config['versionName'],i,ident,self.config['versionName'],i,ident,srid,i,i,ident) 
                            for i in c_power_outputs for ident in conn_t_power_names])
                        tables+=["customer_s_{}${}".format(i,ident) for i in c_power_outputs for ident in conn_t_power_names]

                        #room air temperature table
                        if 'troom' in c_outputs:
                            sql+="""\nDROP TABLE IF EXISTS "{}".customer_s_troom CASCADE;
CREATE TABLE "{}".customer_s_troom
(
	id serial,
    fid integer,
    time timestamp,
	geom geometry(PointZ,{}),
	"$troom" numeric,
	CONSTRAINT customer_s_troom_pkey PRIMARY KEY (id)
);""".format(self.config['versionName'],self.config['versionName'],srid)
                            tables.append('customer_s_troom')   

                        #heat balance table
                        if 'heatbalance' in c_outputs:
                            sql+="""\nDROP TABLE IF EXISTS "{}".customer_s_electricity CASCADE;
CREATE TABLE "{}".customer_s_electricity
(
	id serial,
    fid integer,
    time timestamp,
	geom geometry(PointZ,{}),
	"$electricity" numeric,
	CONSTRAINT customer_s_electricity_pkey PRIMARY KEY (id)
);""".format(self.config['versionName'],self.config['versionName'],srid)
                            tables.append('customer_s_electricity')

                            sql+="""\nDROP TABLE IF EXISTS "{}".customer_s_transmission CASCADE;
CREATE TABLE "{}".customer_s_transmission
(
	id serial,
    fid integer,
    time timestamp,
	geom geometry(PointZ,{}),
	"$transmission" numeric,
	CONSTRAINT customer_s_transmission_pkey PRIMARY KEY (id)
);""".format(self.config['versionName'],self.config['versionName'],srid)
                            tables.append('customer_s_transmission')
                            sql+="""\nDROP TABLE IF EXISTS "{}".customer_s_heating CASCADE;
CREATE TABLE "{}".customer_s_heating
(
	id serial,
    fid integer,
    time timestamp,
	geom geometry(PointZ,{}),
	"$heating" numeric,
	CONSTRAINT customer_s_heating_pkey PRIMARY KEY (id)
);""".format(self.config['versionName'],self.config['versionName'],srid)
                            tables.append('customer_s_heating')
                            sql+="""\nDROP TABLE IF EXISTS "{}".customer_s_gains CASCADE;
CREATE TABLE "{}".customer_s_gains
(
	id serial,
    fid integer,
    time timestamp,
	geom geometry(PointZ,{}),
	"$gains" numeric,
	CONSTRAINT customer_s_gains_pkey PRIMARY KEY (id)
);""".format(self.config['versionName'],self.config['versionName'],srid)
                            tables.append('customer_s_gains')
                            sql+="""\nDROP TABLE IF EXISTS "{}".customer_s_leakage CASCADE;
CREATE TABLE "{}".customer_s_leakage
(
	id serial,
    fid integer,
    time timestamp,
	geom geometry(PointZ,{}),
	"$leakage" numeric,
	CONSTRAINT customer_s_leakage_pkey PRIMARY KEY (id)
);""".format(self.config['versionName'],self.config['versionName'],srid)
                            tables.append('customer_s_leakage')
                            sql+="""\nDROP TABLE IF EXISTS "{}".customer_s_occupancy CASCADE;
CREATE TABLE "{}".customer_s_occupancy
(
	id serial,
    fid integer,
    time timestamp,
	geom geometry(PointZ,{}),
	"$occupancy" numeric,
	CONSTRAINT customer_s_occupancy_pkey PRIMARY KEY (id)
);""".format(self.config['versionName'],self.config['versionName'],srid)
                            tables.append('customer_s_occupancy')
                            sql+="""\nDROP TABLE IF EXISTS "{}".customer_s_solar CASCADE;
CREATE TABLE "{}".customer_s_solar
(
	id serial,
    fid integer,
    time timestamp,
	geom geometry(PointZ,{}),
	"$solar" numeric,
	CONSTRAINT customer_s_solar_pkey PRIMARY KEY (id)
);""".format(self.config['versionName'],self.config['versionName'],srid)
                            tables.append('customer_s_solar')
                            sql+="""\nDROP TABLE IF EXISTS "{}".customer_s_ventilation CASCADE;
CREATE TABLE "{}".customer_s_ventilation
(
	id serial,
    fid integer,
    time timestamp,
	geom geometry(PointZ,{}),
	"$ventilation" numeric,
	CONSTRAINT customer_s_ventilation_pkey PRIMARY KEY (id)
);""".format(self.config['versionName'],self.config['versionName'],srid)
                            tables.append('customer_s_ventilation')
                            
                        #print(sql)
                        if sql:
                            self.cur.execute(sql)
                        
                        #load data
                        #get cid`s
                        sql="""SELECT f.id , b_t_conns.conn_bundle_type_id
    FROM "{}".customers f, bundle_type_conns b_t_conns, customer_templates t
    WHERE b_t_conns.conn_bundle_type_id = t.conn_bundle_type AND f.template=t.template AND submodel={}
    ORDER BY f.id;""".format(self.config['versionName'],submodel_id)
                        self.cur.execute(sql)
                        cids=self.cur.fetchall()
                        
                        self.signals.progress.emit(5)
                        
                        b_t_connValues_dict={b_t: getConnsValues(b_t,self.cur) for b_t in used_b_types}
                        #print(b_t_connValues_dict)
                        for counter,id in enumerate(cids,1):
                            #print(id)
                            #print(c_conn_outputs)
                            if c_conn_outputs or conn_t_power_names:
                                connValues=getConnsValues(id['conn_bundle_type_id'],self.cur)
                                conn_type_seq=set([x['conn_type_seq'] for x in b_t_connValues_dict[id['conn_bundle_type_id']]])
                                #print(f"conn_type_seq:{conn_type_seq}")
                                for seq in conn_type_seq:
                                    fname=dir_path+'customer_'+str(id['id'])+'\\Connection type sequence_{}.prn'.format(seq)
                                    #print(fname)
                                    if os.path.exists(fname):
                                        with open(fname, "r") as myfile:
                                            col_var_dict={}
                                            for line in myfile:
                                                header=line.split()
                                                #print(header)
                                                for col,var in enumerate(header,-1):
                                                    if len(var.split('_'))==2:
                                                        col_var_dict[col]={'var': var.split('_')[0],'name': var.split('_')[0]+'$'+getPMT2muxIdentFromConnValues(connValues,int(var.split('_')[1])),
                                                            'table_name': 'customer_s_'+var.split('_')[0]+'$'+getPMT2muxIdentFromConnValues(connValues,int(var.split('_')[1]))}
                                                    elif var=='power':
                                                        col_var_dict[col]={'var': 'power','name': 'power$'+str(id['conn_bundle_type_id'])+'_'+str(seq),'table_name': 'customer_s_power$'+str(id['conn_bundle_type_id'])+'_'+str(seq)}
                                                        
                                                #print(col_var_dict)
                                                break
                                                
                                        file_data = np.loadtxt(fname, skiprows=1,dtype=float)

                                        if self.dlg.checkbox_timestep.checkState() == checkState():
                                            #linear interpolation
                                            #print(self.dlg.interpolation_dt.text())
                                            file_data=interpolateTimeData(float(self.dlg.interpolation_dt.text()),file_data)

                                        #print(file_data)
                                        start_datetime=getDatetimeFromString(networkSimData['calc_time_from'])
                                        self.copy_string_iterator_feature_c_t_seq_sData(file_data,id['id'],col_var_dict,start_datetime)
                            
                            if 'troom' in c_outputs:
                                fname=dir_path+'customer_'+str(id['id'])+'\\TRoom.prn'
                                #print(fname)
                                if os.path.exists(fname):         
                                    file_data = np.loadtxt(fname, skiprows=1,dtype=float)
                                    if self.dlg.checkbox_timestep.checkState() == checkState():
                                        #linear interpolation
                                        #print(self.dlg.interpolation_dt.text())
                                        file_data=interpolateTimeData(float(self.dlg.interpolation_dt.text()),file_data)

                                    #print(file_data)
                                    start_datetime=getDatetimeFromString(networkSimData['calc_time_from'])
                                    col_var_dict={2: {'var': 'troom','name': '','table_name': 'customer_s_troom'}}
                                    self.copy_string_iterator_feature_c_t_seq_sData(file_data,id['id'],col_var_dict,start_datetime)
                                
                            if 'heatbalance' in c_outputs:
                                fname=dir_path+'customer_'+str(id['id'])+'\\Heatbalance.prn'.format(seq)
                                #print(fname)
                                if os.path.exists(fname):                                              
                                    file_data = np.loadtxt(fname, skiprows=1,dtype=float)
                                    if self.dlg.checkbox_timestep.checkState() == checkState():
                                        #linear interpolation
                                        #print(self.dlg.interpolation_dt.text())
                                        file_data=interpolateTimeData(float(self.dlg.interpolation_dt.text()),file_data)
                                    #print(file_data)
                                    start_datetime=getDatetimeFromString(networkSimData['calc_time_from'])
                                    self.copy_string_iterator_c_heatbalance_sData(file_data,id['id'],start_datetime)
                            self.signals.progress.emit(int(5+counter / len(cids) *28))
                        #update point geometry
                        #print(tables)
                        if tables:
                            self.createResultLayerIndex(tables,'customer')
                            self.updateResultLayerGeometry(tables,'customer')
                            
                    self.signals.progress.emit(33)
                                    
                        
                    #energy plant tables: customer_s_conntype_[conn type seq]
                    ep_outputs=[output.split('_')[0] for output in self.simulatedOutputs if output.split('_')[1]=='ep' and self.simulatedOutputs[output]]
                    if ep_outputs:
                        used_b_types=getUsedConnBundleTypes('energy_plant',self.cur,self.config)
                        ep_conn_outputs=[output.split('_')[0] for output in self.simulatedOutputs if output.split('_')[1]=='ep' and self.simulatedOutputs[output] and output.split('_')[0] not in ['power']]
                        conn_names= [ident for connBundleType in used_b_types for ident in getPMT2muxIdents(self.cur,connBundleType)]
                        conn_t_power_names= getUsedConnTypeIdents('energy_plant',self.cur,self.config)
                        tables=[]
                        #print(conn_names)
                        #print(conn_t_power_names)
                        #connection tables (p,m,T)
                        sql='\n'.join(["""DROP TABLE IF EXISTS "{}".energy_plant_s_{}${} CASCADE;
CREATE TABLE "{}".energy_plant_s_{}${}
(
	id serial,
    fid integer,
    time timestamp,
	geom geometry(PointZ,{}),
	"${}" numeric,
	CONSTRAINT energy_plant_s_{}${}_pkey PRIMARY KEY (id)
);""".format(self.config['versionName'],output,conn_name,self.config['versionName'],output,conn_name,srid,output,output,conn_name) 
                            for output in ep_conn_outputs for conn_name in conn_names])
                        tables+=["energy_plant_s_{}${}".format(output,conn_name) for output in ep_conn_outputs for conn_name in conn_names]
                            
                        #connection type tables (power)
                        if 'power' in ep_outputs:
                            sql+='\n'.join(["""DROP TABLE IF EXISTS "{}".energy_plant_s_power${} CASCADE;
CREATE TABLE "{}".energy_plant_s_power${}
(
	id serial,
    fid integer,
    time timestamp,
	geom geometry(PointZ,{}),
	"$power" numeric,
	CONSTRAINT energy_plant_s_power${}_pkey PRIMARY KEY (id)
);""".format(self.config['versionName'],ident,self.config['versionName'],ident,srid,ident) 
                                for ident in conn_t_power_names])
                            tables+=["energy_plant_s_power${}".format(ident) for ident in conn_t_power_names]
                        
                        #print(sql)
                        if sql:
                            self.cur.execute(sql)
                            
                        #load data
                        #get epid`s
                        sql="""SELECT f.id , b_t_conns.conn_bundle_type_id
    FROM "{}".energy_plants f, bundle_type_conns b_t_conns, energy_plant_templates t
    WHERE b_t_conns.conn_bundle_type_id = t.conn_bundle_type AND f.template=t.template AND submodel={};""".format(self.config['versionName'],submodel_id)
                        #print(sql)
                        self.cur.execute(sql)
                        epids=self.cur.fetchall()
                        
                        b_t_connValues_dict={b_t: getConnsValues(b_t,self.cur) for b_t in used_b_types}
                        #print(b_t_connValues_dict)
                        for counter,id in enumerate(epids,1):
                            #print(id)
                            if ep_conn_outputs or conn_t_power_names:
                                connValues=getConnsValues(id['conn_bundle_type_id'],self.cur)
                                conn_type_seq=set([x['conn_type_seq'] for x in b_t_connValues_dict[id['conn_bundle_type_id']]])
                                for seq in conn_type_seq:
                                    fname=dir_path+'energy_plant_'+str(id['id'])+'\\Connection type sequence_{}.prn'.format(seq)
                                    #print(fname)
                                    if os.path.exists(fname):
                                        with open(fname, "r") as myfile:
                                            col_var_dict={}
                                            for line in myfile:
                                                header=line.split()
                                                #print(header)
                                                for col,var in enumerate(header,-1):
                                                    if len(var.split('_'))==2:
                                                        col_var_dict[col]={'var': var.split('_')[0],'name': var.split('_')[0]+'$'+getPMT2muxIdentFromConnValues(connValues,int(var.split('_')[1])),
                                                            'table_name': 'energy_plant_s_'+var.split('_')[0]+'$'+getPMT2muxIdentFromConnValues(connValues,int(var.split('_')[1]))}
                                                    elif var=='power':
                                                        col_var_dict[col]={'var': 'power','name': 'power$'+str(id['conn_bundle_type_id'])+'_'+str(seq),'table_name': 'energy_plant_s_power$'+str(id['conn_bundle_type_id'])+'_'+str(seq)}
                                                        
                                                #print(col_var_dict)
                                                break
                                                
                                        file_data = np.loadtxt(fname, skiprows=1,dtype=float)

                                        if self.dlg.checkbox_timestep.checkState() == checkState():
                                            #linear interpolation
                                            #print(self.dlg.interpolation_dt.text())
                                            file_data=interpolateTimeData(float(self.dlg.interpolation_dt.text()),file_data)
                                        #print(file_data)
                                        start_datetime=getDatetimeFromString(networkSimData['calc_time_from'])
                                        self.copy_string_iterator_feature_c_t_seq_sData(file_data,id['id'],col_var_dict,start_datetime)
                            self.signals.progress.emit(int(33+counter / len(epids) *33))
                        #update point geometry
                        #print(tables)
                        if tables:
                            self.createResultLayerIndex(tables,'energy_plant')
                            self.updateResultLayerGeometry(tables,'energy_plant')
                            
                    self.signals.progress.emit(66)
                    #lines
                    line_outputs=[output.split('_')[0] for output in self.simulatedOutputs if output.split('_')[1]=='lines' and self.simulatedOutputs[output]]
                    if line_outputs:
                        sql='\n'.join(["""DROP TABLE IF EXISTS "{}".line_s_{}${} CASCADE;
CREATE TABLE "{}".line_s_{}${}
(
	id serial,
    fid integer,
    time timestamp,
	geom geometry(LineStringZ,{}),
	segment integer,
	"${}" numeric,
	CONSTRAINT line_s_{}${}_pkey PRIMARY KEY (id)
);""".format(self.config['versionName'],output,seq,self.config['versionName'],output,seq,srid,output,output,seq) 
                            for output in line_outputs for seq in pipe_sequences if output!='qamb'])
                        if 'qamb' in line_outputs:
                            sql+="""\nDROP TABLE IF EXISTS "{}".line_s_qamb CASCADE;
CREATE TABLE "{}".line_s_qamb
(
	id serial,
    fid integer,
    time timestamp,
	geom geometry(LineStringZ,{}),
	segment integer,
	"$qamb" numeric,
	CONSTRAINT line_s_qamb_pkey PRIMARY KEY (id)
);""".format(self.config['versionName'],self.config['versionName'],srid)

                        #print(sql)
                        self.cur.execute(sql)

                        #load data
                        #get lids
                        sql="""SELECT id FROM "{}".lines WHERE {}=ANY(submodel) ORDER BY id;""".format(self.config['versionName'],submodel_id)
                        self.cur.execute(sql)
                        lids=self.cur.fetchall()
                        
                        for counter_of,output in enumerate(line_outputs,1):
                            #print('+++++++++'+output+'++++++++++++')
                            #get connection sequence
                            for counter_l,id in enumerate(lids,1):
                                fname=dir_path+'Line_{}_{}.prn'.format(output,id['id'])
                                #print(fname)
                                if os.path.exists(fname):
                                    data=[]
                                    if output=='temp': #get number of temp segments per line; just read first line
                                        with open(fname, "r") as myfile:
                                            for line in myfile:
                                                values_len=len(line.split())-3
                                                conn_seq_len=len(set([int(i.split('_')[1]) for i in line.split()[3:]]))
                                                value_per_conn_seq=values_len/conn_seq_len
                                                #print(value_per_conn_seq)
                                                break
                                    elif output=='p':
                                        with open(fname, "r") as myfile:
                                            for line in myfile:
                                                values_len=len(line.split())-3
                                                break
                                        value_per_conn_seq=2
                                        conn_seq_len=values_len/value_per_conn_seq
                                        #print(value_per_conn_seq)
                                        #print(conn_seq_len)
                                    else:
                                        value_per_conn_seq=1
                                        #print(value_per_conn_seq)

                                    file_data = np.loadtxt(fname, skiprows=1,dtype=float)
                                    if output=='p':
                                        new_order=[0,1]+[int(i+2 + conn_seq_len*j) for i in range(int(conn_seq_len)) for j in range(value_per_conn_seq)]
                                        #print(new_order)
                                        file_data=file_data[:,new_order]
                                        
                                    if output=='v': #only positive values for v are needed
                                        file_data[:, 2:]=np.abs(file_data[:, 2:])
                                        #print(file_data)
                                    
                                    start_datetime=getDatetimeFromString(networkSimData['calc_time_from'])
                                            
                                    if self.dlg.checkbox_timestep.checkState() == checkState():
                                        #linear interpolation
                                        #print(self.dlg.interpolation_dt.text())
                                        file_data=interpolateTimeData(float(self.dlg.interpolation_dt.text()),file_data)
                                            
                                    if output=='qamb':
                                        table_names=['line_s_qamb']
                                    else:
                                        table_names=['line_s_'+output+'$'+str(i) for i in pipe_sequences]
                                    #print(table_names)
                                    self.copy_string_iterator_sData(file_data,id['id'],table_names,value_per_conn_seq,start_datetime,'linestring')
                                self.signals.progress.emit(int(66+counter_l / len(lids)*32/len(line_outputs)+counter_of/len(line_outputs)*32))
                            
                            self.createResultLayerIndex(table_names,'line')

                            #update line geometry
                            if ['line_s_'+output+'$'+str(i) for i in pipe_sequences if output in ['p','temp']]:
                                self.updateResultLayerLineSegGeometry(['line_s_'+output+'$'+str(i) for i in pipe_sequences if output in ['p','temp']])
                            elif ['line_s_'+output+'$'+str(i) for i in pipe_sequences if output in ['mdot','v']]:
                                self.updateResultLayerGeometry(['line_s_'+output+'$'+str(i) for i in pipe_sequences if output not in ['p','temp']],'line')
                            elif output=='qamb':
                                self.updateResultLayerGeometry(['line_s_qamb'],'line')


                        self.signals.progress.emit(99)
                        
                    #--------KPI`s------
                    #print('------kpi----------')
                    kpis={}
                    if self.simulatedOutputs['tsup_mean_ep_kpi']: 
                        kpis['tsup_mean_ep']=''
                    if self.simulatedOutputs['tsup_max_ep_kpi']: 
                        kpis['tsup_max_ep']=''
                    if self.simulatedOutputs['tsup_min_ep_kpi']: 
                        kpis['tsup_min_ep']=''
                    if self.simulatedOutputs['tret_mean_ep_kpi']: 
                        kpis['tret_mean_ep']=''
                    if self.simulatedOutputs['tret_max_ep_kpi']: 
                        kpis['tret_max_ep']=''
                    if self.simulatedOutputs['tret_min_ep_kpi']: 
                        kpis['tret_min_ep']=''
                    if self.simulatedOutputs['qsup_heat_ep_kpi']: 
                        kpis['qsup_heat_ep']=''
                    if self.simulatedOutputs['qsup_cold_ep_kpi']: 
                        kpis['qsup_cold_ep']=''
                    if self.simulatedOutputs['qsup_ep_kpi']: 
                        kpis['qsup_ep']=''                    
                    
                    if self.simulatedOutputs['tsup_mean_c_kpi']: 
                        kpis['tsup_mean_c']=''
                    if self.simulatedOutputs['tsup_max_c_kpi']: 
                        kpis['tsup_max_c']=''
                    if self.simulatedOutputs['tsup_min_c_kpi']: 
                        kpis['tsup_min_c']=''
                    if self.simulatedOutputs['tret_mean_c_kpi']: 
                        kpis['tret_mean_c']=''
                    if self.simulatedOutputs['tret_max_c_kpi']: 
                        kpis['tret_max_c']=''
                    if self.simulatedOutputs['tret_min_c_kpi']: 
                        kpis['tret_min_c']=''
                    if self.simulatedOutputs['qsup_heat_c_kpi']: 
                        kpis['qsup_heat_c']=''
                    if self.simulatedOutputs['qsup_cold_c_kpi']: 
                        kpis['qsup_cold_c']=''
                    if self.simulatedOutputs['qsup_c_kpi']: 
                        kpis['qsup_c']=''

                    if self.simulatedOutputs['qamb_kpi']: 
                        kpis['qamb']=''
                    for counter_of,kpi in enumerate(kpis,1):
                        #print('+++++++++'+kpi+'++++++++++++')

                        fname=dir_path+'Results-macro\\{}_kpi_outputfile.prn'.format(kpi.capitalize())
                        #print(fname)
                        if os.path.exists(fname):
                            with open(fname, "r") as f:
                                for line in f:
                                    last_line = line
                                
                            try:
                                kpis[kpi]=last_line.split()[-1]
                            except:
                                pass
                    #print(kpis)
                    sql="""TRUNCATE "{}".kpi;\n""".format(self.config['versionName'])
                    sql+="""INSERT INTO "{}".kpi ({}) SELECT {};""".format(self.config['versionName'],
                        "id"+''.join([",{}".format(kpi) for kpi in kpis]),
                        "1"+''.join([",{}".format(kpis[kpi]) for kpi in kpis]))
                    #print(sql)
                    self.cur.execute(sql)
                except Exception as e:
                    self.signals.error.emit(str(e))
                        

    def copy_string_iterator_feature_c_t_seq_sData(self,sdata,fid,col_dict,start_datetime) -> None:
        for col in col_dict:
            #print(col)
            table_name=col_dict[col]['table_name']
            #print(table_name)
            max_id=getMaxIdSchema(self.cur,table_name,self.config['versionName'])+1
            #print(max_id)
            with self.conn.cursor() as cursor:
                mdata_string_iterator = StringIteratorIO((
                    '|'.join(map(clean_csv_value, (
                        int(row_counter+max_id),
                        fid,
                        start_datetime+datetime.timedelta(hours=float(data[0])),
                        '',
                        data[1]
                    ))) + '\n'
                    for row_counter,data in enumerate(zip(sdata[:,0],sdata[:,col]))
                ))
                cursor.copy_expert("""COPY "{}".{} FROM STDIN WITH (FORMAT csv, DELIMITER '|')""".format(self.config['versionName'],table_name),mdata_string_iterator)
                
    def copy_string_iterator_c_heatbalance_sData(self, sdata,fid,start_datetime) -> None:
        table_names=['customer_s_electricity','customer_s_gains','customer_s_heating','customer_s_leakage','customer_s_occupancy','customer_s_solar','customer_s_transmission','customer_s_ventilation']
        with self.conn.cursor() as cursor:
            for col,table_name in enumerate(table_names,2):
                max_id=getMaxIdSchema(self.cur,table_name,self.config['versionName'])+1
                mdata_string_iterator = StringIteratorIO((
                    '|'.join(map(clean_csv_value, (
                        int(row_counter+max_id),
                        fid,
                        start_datetime+datetime.timedelta(hours=float(data[0])),
                        '',
                        data[col]
                    ))) + '\n'
                    for row_counter,data in enumerate(sdata)
                ))
                cursor.copy_expert("""COPY "{}".{} FROM STDIN WITH (FORMAT csv, DELIMITER '|');""".format(self.config['versionName'],table_name),mdata_string_iterator)
               
    def updateResultLayerGeometry(self,tables,type):
        for table_name in tables:
            sql="""UPDATE "{}".{} r set geom = f.geom 
    FROM (SELECT id, geom FROM "{}".{}s) f
    WHERE f.id=r.fid;""".format(self.config['versionName'],table_name,self.config['versionName'],type)
            #print(sql)
            self.cur.execute(sql)
            
    def createResultLayerIndex(self,tables,type):
        for counter,table_name in enumerate(tables,1):
            #print('-------------**---**-'+table_name.split('_')[1].split('$')[0])
            if type=='line' and table_name.split('$')[0].split('_')[-1] in ['temp','p']:
                sql="""CREATE INDEX "idx_{}_fid_time_segment" ON {}."{}" (fid, time, segment);""".format(table_name,self.config['versionName'],table_name)
            else:
                sql="""CREATE INDEX "idx_{}_fid_time" ON {}."{}" (fid, time);""".format(table_name,self.config['versionName'],table_name)
            #print(sql)
            self.cur.execute(sql)
            
    def updateResultLayerLineSegGeometry(self,tables):   
        for table_name in tables:
            var=table_name.split('_')[2].split('$')[0]
            sql="""UPDATE "{}".{} r set geom = seg.geom 
    FROM (SELECT lid,lid_seg, geom FROM "{}".line_seg_{}) seg
    WHERE seg.lid=r.fid AND r.segment=seg.lid_seg;""".format(self.config['versionName'],table_name,self.config['versionName'],var)
            #print(sql)
            self.cur.execute(sql)
            
    def copy_string_iterator_sData(self, sdata,fid,table_names,value_per_conn_seq,start_datetime,mode) -> None:
        start_col_index=2
        end_col_index=2+value_per_conn_seq
        for table_name in table_names:
            max_id=getMaxIdSchema(self.cur,table_name,self.config['versionName'])+1
            with self.conn.cursor() as cursor:
                mdata_string_iterator = StringIteratorIO((
                    '|'.join(map(clean_csv_value, (
                        int(row_counter*value_per_conn_seq+col_counter+max_id),
                        fid,
                        start_datetime+datetime.timedelta(hours=float(data[0])),
                        '',
                        int(col_counter+1),
                        cell
                    ))) + '\n'
                    for row_counter,data in enumerate(zip(sdata[:,0],sdata[:,int(start_col_index):int(end_col_index)])) for col_counter,cell in enumerate(data[1])
                ))
                cursor.copy_expert("""COPY "{}".{} FROM STDIN WITH (FORMAT csv, DELIMITER '|');""".format(self.config['versionName'],table_name),mdata_string_iterator)
            start_col_index=end_col_index
            end_col_index=start_col_index+value_per_conn_seq  