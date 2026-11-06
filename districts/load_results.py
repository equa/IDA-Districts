from qgis.PyQt.QtCore import QObject, pyqtSlot, pyqtSignal,QRunnable
from qgis.core import QgsMessageLog, Qgis

import io
import os
import psycopg2
import numpy as np
from .utility_functions.compat import MessageCritical
from .utility_functions.db import (
    StringIteratorIO, clean_csv_value, dbConnect, getMaxIdSchema, getNetworkBySubmodel,
)
from .utility_functions.dialog import checkState
from .utility_functions.files import (
    loadModellingSettings, loadNetworkSimData, loadProjectConfig, readFileToString,
)
from .utility_functions.ida_components import (
    getCompClass, getCompName, getIDAListComponents, propertyListCompsIDM,
)
from .utility_functions.topology import (
    getConnsValues, getPMT2muxIdentFromConnValues, getPMT2muxIdents, getUsedConnBundleTypes,
    getUsedConnTypeIdents, getUsedPipeBundleSequences,
)
from .utility_functions.translations import tr
from .utility_functions.utility import getDatetimeFromString, interpolateTimeData
from .utility_functions.workers import closesOwnConnection, APISignals

import datetime
import re
import traceback



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
    @closesOwnConnection
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
        #the time column of the IDA .prn files holds the hours since Jan 1 of the simulated year (not since calc_time_from)
        start_datetime=getDatetimeFromString(networkSimData['calc_time_from']).replace(month=1,day=1,hour=0,minute=0,second=0)
        self.reported_errors=set()
        self.time_strings_cache={}

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
            "SELECT segmentize({},'{}','line_seg_temp');".format(modellingSettings['fd_meterPerNode'],self.config['versionName']) if output=='temp_lines' else "SELECT halve_geom('{}','line_seg_p');".format(self.config['versionName'])) # nosec B608
            for output in self.simulatedOutputs if output in ['temp_lines','p_lines'] and self.simulatedOutputs[output]])
        if sql:
            #print(sql)
            self.cur.execute(sql)
        
        for submodel_idx in range(self.dlg.combo_submodels.count()):
            if self.dlg.combo_submodels.itemText(submodel_idx) != tr('@default','check_all_items') and self.dlg.combo_submodels.itemChecked(submodel_idx):
                try:
                    submodel=self.dlg.combo_submodels.itemText(submodel_idx)
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
);""".format(self.config['versionName'],output,conn_name,self.config['versionName'],output,conn_name,srid,output,output,conn_name)  # nosec B608
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
);""".format(self.config['versionName'],i,ident,self.config['versionName'],i,ident,srid,i,i,ident)  # nosec B608
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
);""".format(self.config['versionName'],self.config['versionName'],srid) # nosec B608
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
);""".format(self.config['versionName'],self.config['versionName'],srid) # nosec B608
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
);""".format(self.config['versionName'],self.config['versionName'],srid) # nosec B608
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
);""".format(self.config['versionName'],self.config['versionName'],srid) # nosec B608
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
);""".format(self.config['versionName'],self.config['versionName'],srid) # nosec B608
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
);""".format(self.config['versionName'],self.config['versionName'],srid) # nosec B608
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
);""".format(self.config['versionName'],self.config['versionName'],srid) # nosec B608
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
);""".format(self.config['versionName'],self.config['versionName'],srid) # nosec B608
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
);""".format(self.config['versionName'],self.config['versionName'],srid) # nosec B608
                            tables.append('customer_s_ventilation')
                            
                        #print(sql)
                        if sql:
                            self.cur.execute(sql)
                        
                        #load data
                        #get cid`s
                        sql="""SELECT f.id , b_t_conns.conn_bundle_type_id, t.template::text || '_' || t.template_name AS template_name
    FROM "{}".customers f, bundle_type_conns b_t_conns, customer_templates t
    WHERE b_t_conns.conn_bundle_type_id = t.conn_bundle_type AND f.template=t.template AND submodel={}
    GROUP BY f.id , b_t_conns.conn_bundle_type_id, t.template, t.template_name
    ORDER BY f.id;""".format(self.config['versionName'],submodel_id) # nosec B608
                        self.cur.execute(sql)
                        cids=self.cur.fetchall()
                        
                        self.signals.progress.emit(5)

                        b_t_connValues_dict={b_t: getConnsValues(b_t,self.cur) for b_t in used_b_types}
                        geoms=self.featureGeometries('customers')
                        copy_buffer=ResultCopyBuffer(self.conn,self.cur,self.config['versionName'])
                        #print(b_t_connValues_dict)
                        for counter,id in enumerate(cids,1):
                            #print(id)
                            #print(c_conn_outputs)
                            geom=geoms.get(id['id'],'')
                            if c_conn_outputs or conn_t_power_names:
                                connValues=b_t_connValues_dict[id['conn_bundle_type_id']]
                                conn_type_seq=set([x['conn_type_seq'] for x in b_t_connValues_dict[id['conn_bundle_type_id']]])
                                #print(f"conn_type_seq:{conn_type_seq}")
                                for seq in conn_type_seq:
                                    fname=dir_path+'customer_'+str(id['id'])+'\\Connection type sequence_{}.prn'.format(seq)
                                    #print(fname)
                                    self.checkConnTypeSeqOutputFile(fname,'customer',id,seq,b_t_connValues_dict[id['conn_bundle_type_id']],c_conn_outputs,bool(c_power_outputs))
                                    if os.path.exists(fname):
                                        with open(fname, "r") as myfile:
                                            col_var_dict={}
                                            for line in myfile:
                                                header=line.split()
                                                #print(header)
                                                for col,var in enumerate(header,-1):
                                                    if len(var.split('_'))==2:
                                                        col_var_dict[col]={'var': var.split('_')[0],'name': var.split('_')[0]+'$'+getPMT2muxIdentFromConnValues(connValues,int(var.split('_')[1]),conn_t_seq=seq),
                                                            'table_name': 'customer_s_'+var.split('_')[0]+'$'+getPMT2muxIdentFromConnValues(connValues,int(var.split('_')[1]),conn_t_seq=seq)}
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
                                        self.copy_feature_sData(copy_buffer,file_data,id['id'],geom,col_var_dict,start_datetime)

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
                                    col_var_dict={2: {'var': 'troom','name': '','table_name': 'customer_s_troom'}}
                                    self.copy_feature_sData(copy_buffer,file_data,id['id'],geom,col_var_dict,start_datetime)
                                
                            if 'heatbalance' in c_outputs:
                                fname=dir_path+'customer_'+str(id['id'])+'\\Heatbalance.prn'
                                #print(fname)
                                if os.path.exists(fname):                                              
                                    file_data = np.loadtxt(fname, skiprows=1,dtype=float)
                                    if self.dlg.checkbox_timestep.checkState() == checkState():
                                        #linear interpolation
                                        #print(self.dlg.interpolation_dt.text())
                                        file_data=interpolateTimeData(float(self.dlg.interpolation_dt.text()),file_data)
                                    #print(file_data)
                                    heatbalance_tables=['customer_s_electricity','customer_s_gains','customer_s_heating','customer_s_leakage','customer_s_occupancy','customer_s_solar','customer_s_transmission','customer_s_ventilation']
                                    self.copy_feature_sData(copy_buffer,file_data,id['id'],geom,{col: {'table_name': table_name} for col,table_name in enumerate(heatbalance_tables,2)},start_datetime)
                            self.signals.progress.emit(int(5+counter / len(cids) *28))
                        copy_buffer.flush()
                        #index after loading the data
                        #print(tables)
                        if tables:
                            self.createResultLayerIndex(tables,'customer')
                            
                    self.signals.progress.emit(33)
                                    
                        
                    #energy plant tables: customer_s_conntype_[conn type seq]
                    ep_outputs=[output.split('_')[0] for output in self.simulatedOutputs if output.split('_')[1]=='ep' and self.simulatedOutputs[output]]
                    if ep_outputs:
                        used_b_types=getUsedConnBundleTypes('energy_plant',self.cur,self.config)
                        ep_conn_outputs=[output.split('_')[0] for output in self.simulatedOutputs if output.split('_')[1]=='ep' and self.simulatedOutputs[output] and output.split('_')[0] not in ['power','qsup']]
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
);""".format(self.config['versionName'],output,conn_name,self.config['versionName'],output,conn_name,srid,output,output,conn_name)  # nosec B608
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
);""".format(self.config['versionName'],ident,self.config['versionName'],ident,srid,ident)  # nosec B608
                                for ident in conn_t_power_names])
                            tables+=["energy_plant_s_power${}".format(ident) for ident in conn_t_power_names]
                        
                        #print(sql)
                        if sql:
                            self.cur.execute(sql)
                            
                        #load data
                        #get epid`s
                        sql="""SELECT f.id , b_t_conns.conn_bundle_type_id, t.template::text || '_' || t.template_name AS template_name
    FROM "{}".energy_plants f, bundle_type_conns b_t_conns, energy_plant_templates t
    WHERE b_t_conns.conn_bundle_type_id = t.conn_bundle_type AND f.template=t.template AND submodel={}
    GROUP BY f.id , b_t_conns.conn_bundle_type_id, t.template, t.template_name;""".format(self.config['versionName'],submodel_id) # nosec B608
                        #print(sql)
                        self.cur.execute(sql)
                        epids=self.cur.fetchall()
                        
                        b_t_connValues_dict={b_t: getConnsValues(b_t,self.cur) for b_t in used_b_types}
                        geoms=self.featureGeometries('energy_plants')
                        copy_buffer=ResultCopyBuffer(self.conn,self.cur,self.config['versionName'])
                        #print(b_t_connValues_dict)
                        for counter,id in enumerate(epids,1):
                            #print(id)
                            if ep_conn_outputs or conn_t_power_names:
                                connValues=b_t_connValues_dict[id['conn_bundle_type_id']]
                                #print(connValues)
                                conn_type_seq=set([x['conn_type_seq'] for x in b_t_connValues_dict[id['conn_bundle_type_id']]])
                                #print(conn_type_seq)
                                for seq in conn_type_seq:
                                    fname=dir_path+'energy_plant_'+str(id['id'])+'\\Connection type sequence_{}.prn'.format(seq)
                                    #print(fname)
                                    self.checkConnTypeSeqOutputFile(fname,'energy_plant',id,seq,b_t_connValues_dict[id['conn_bundle_type_id']],ep_conn_outputs,'power' in ep_outputs)
                                    if os.path.exists(fname):
                                        with open(fname, "r") as myfile:
                                            col_var_dict={}
                                            for line in myfile:
                                                header=line.split()
                                                #print(header)
                                                for col,var in enumerate(header,-1):
                                                    if len(var.split('_'))==2:
                                                        col_var_dict[col]={'var': var.split('_')[0],'name': var.split('_')[0]+'$'+getPMT2muxIdentFromConnValues(connValues,int(var.split('_')[1]),conn_t_seq=seq),
                                                            'table_name': 'energy_plant_s_'+var.split('_')[0]+'$'+getPMT2muxIdentFromConnValues(connValues,int(var.split('_')[1]),conn_t_seq=seq)}
                                                    elif var=='power':
                                                        col_var_dict[col]={'var': 'power','name': 'power$'+str(id['conn_bundle_type_id'])+'_'+str(seq),'table_name': 'energy_plant_s_power$'+str(id['conn_bundle_type_id'])+'_'+str(seq)}
                                                        
                                                #print(col_var_dict)
                                                break
                                                
                                        file_data = np.loadtxt(fname, skiprows=1,dtype=float)
                                        #print(file_data)

                                        if self.dlg.checkbox_timestep.checkState() == checkState():
                                            #linear interpolation
                                            #print(self.dlg.interpolation_dt.text())
                                            file_data=interpolateTimeData(float(self.dlg.interpolation_dt.text()),file_data)
                                        #print(file_data)
                                        self.copy_feature_sData(copy_buffer,file_data,id['id'],geoms.get(id['id'],''),col_var_dict,start_datetime)
                            self.signals.progress.emit(int(33+counter / len(epids) *33))
                        copy_buffer.flush()
                        #index after loading the data
                        #print(tables)
                        if tables:
                            self.createResultLayerIndex(tables,'energy_plant')
                            
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
);""".format(self.config['versionName'],output,seq,self.config['versionName'],output,seq,srid,output,output,seq)  # nosec B608
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
);""".format(self.config['versionName'],self.config['versionName'],srid) # nosec B608

                        #print(sql)
                        self.cur.execute(sql)

                        #load data
                        #get lids with the pipe sequences of their pipe bundle (the columns of the IDA output files are ordered by bundle pipe sequence)
                        sql="""SELECT l.id, ARRAY_AGG(bp.sequence ORDER BY bp.sequence) AS sequences
    FROM "{}".lines l, bundle_pipes bp
    WHERE {}=ANY(l.submodel) AND bp.pipe_bundle_type_id=l.pipe_bundle_type_id
    GROUP BY l.id ORDER BY l.id;""".format(self.config['versionName'],submodel_id) # nosec B608
                        self.cur.execute(sql)
                        lids=self.cur.fetchall()
                        line_geoms=self.featureGeometries('lines')

                        for counter_of,output in enumerate(line_outputs,1):
                            #print('+++++++++'+output+'++++++++++++')
                            #geometry: simulated pipe segments for temp and p, the line for the other outputs
                            seg_geoms=self.lineSegGeometries(output) if output in ['p','temp'] else None
                            copy_buffer=ResultCopyBuffer(self.conn,self.cur,self.config['versionName'])
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
                                    
                                            
                                    if self.dlg.checkbox_timestep.checkState() == checkState():
                                        #linear interpolation
                                        #print(self.dlg.interpolation_dt.text())
                                        file_data=interpolateTimeData(float(self.dlg.interpolation_dt.text()),file_data)
                                            
                                    if output=='qamb':
                                        line_table_names=['line_s_qamb']
                                    else:
                                        #only the pipes of this bundle, the number of pipes per bundle may vary over the network (e.g. heating and cooling network with different extension)
                                        line_table_names=['line_s_'+output+'$'+str(i) for i in id['sequences']]
                                    #print(line_table_names)
                                    if seg_geoms is not None:
                                        segment_geoms=[seg_geoms.get((id['id'],segment),'') for segment in range(1,int(value_per_conn_seq)+1)]
                                    else:
                                        segment_geoms=[line_geoms.get(id['id'],'')]*int(value_per_conn_seq)
                                    self.copy_line_sData(copy_buffer,file_data,id['id'],line_table_names,value_per_conn_seq,start_datetime,segment_geoms)
                                self.signals.progress.emit(int(66+counter_l / len(lids)*30/len(line_outputs)+counter_of/len(line_outputs)*30))
                            copy_buffer.flush()

                            #index after loading the data
                            table_names=['line_s_qamb'] if output=='qamb' else ['line_s_'+output+'$'+str(i) for i in pipe_sequences]
                            self.createResultLayerIndex(table_names,'line')


                        self.signals.progress.emit(99)
                        
                    for network in getNetworkBySubmodel(self.cur,self.config,submodel):
                        #print(network)
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

                            fname=dir_path+'results-macro_{}\\{}_kpi_outputfile.prn'.format(network,kpi.capitalize())
                            #print(fname)
                            if os.path.exists(fname):
                                with open(fname, "r") as f:
                                    for line in f:
                                        last_line = line
                                    
                                try:
                                    kpis[kpi]=last_line.split()[-1]
                                except Exception:
                                    QgsMessageLog.logMessage(
                                        traceback.format_exc(),
                                        "Districts",
                                        MessageCritical
                                    )
                        #print(kpis)
                        sql="""DROP TABLE IF EXISTS "{}".kpi_{} CASCADE;
CREATE TABLE IF NOT EXISTS "{}".kpi_{}
(
    id serial,
    tsup_mean_ep numeric,
    tsup_max_ep numeric,
    tsup_min_ep numeric,
    tret_mean_ep numeric,
    tret_max_ep numeric,
    tret_min_ep numeric,
    qsup_heat_ep numeric,
    qsup_cold_ep numeric,
    qsup_ep numeric,
    tsup_mean_c numeric,
    tsup_max_c numeric,
    tsup_min_c numeric,
    tret_mean_c numeric,
    tret_max_c numeric,
    tret_min_c numeric,
    qsup_heat_c numeric,
    qsup_cold_c numeric,
    qsup_c numeric,
    qamb numeric,
    CONSTRAINT kpi_{}_pkey PRIMARY KEY (id)
);\n""".format(self.config['versionName'],network,self.config['versionName'],network,network)  # nosec B608
                        sql+="""INSERT INTO "{}".kpi_{} ({}) SELECT {};""".format(self.config['versionName'],network,  # nosec B608
                            "id"+''.join([",{}".format(kpi) for kpi in kpis]),  # nosec B608
                            "1"+''.join([",{}".format(kpis[kpi]) for kpi in kpis]))  # nosec B608
                        #print(sql)
                        self.cur.execute(sql)
                        
                        self.signals.progress.emit(97)
                        
                        #--------heat balance------
                        if self.simulatedOutputs['heatbalance_system']: 
                            #print('------heat balance----------')

                            fname=dir_path+'results-macro_{}\\heatbalance_outputfile.prn'.format(network)
                            #print(fname)

                            if os.path.exists(fname):
                                #get output headers
                                components_idm=propertyListCompsIDM(getIDAListComponents(readFileToString(dir_path+'results-macro_{}.idm'.format(network))))
                                for comp in components_idm:
                                    if getCompName(comp)=='"heatbalance_outputfile"': 
                                        as_dict={}
                                        for subcomp in comp:
                                            if getCompClass(subcomp)=='OUTPUT-FILE':                     
                                                names = re.findall(r'([A-Z_]+)\s+#S', subcomp[':DF'])
                                                as_dict={name.lower() : '' for name in names}  
                                            elif getCompClass(subcomp)==':VAR':   
                                                as_dict[subcomp[':N'].lower()]=tr('@default',subcomp[':D'].replace('"',''))       
                                #print(as_dict)
                                col_dict={}
                                with open(fname, "r") as myfile:
                                    for line in myfile:
                                        if line[0]=='#':
                                            line=line[1:]
                                        col_dict={counter: as_dict[col.lower()] for counter,col in enumerate(line.split(),0) if counter>1}
                                        break
                                #print(col_dict)
                                file_data = np.loadtxt(fname, skiprows=1,dtype=float)
                                
                                        
                                if self.dlg.checkbox_timestep.checkState() == checkState():
                                    #linear interpolation
                                    file_data=interpolateTimeData(float(self.dlg.interpolation_dt.text()),file_data)
                                        
                                #print(file_data)
                                
                                sql="""\nDROP TABLE IF EXISTS "{}".heatbalance_{}_s CASCADE;
CREATE TABLE "{}".heatbalance_{}_s
(
    id serial,
    time timestamp,{}
    CONSTRAINT heatbalance_{}_s_pkey PRIMARY KEY (id)
);""".format(self.config['versionName'],network,self.config['versionName'],network,''.join(['\n   "{}" numeric,'.format(col_name) for col_name in col_dict.values()]),network) # nosec B608
                                #print(sql)
                                self.cur.execute(sql)
                            
                                self.copy_string_iterator_system_balance_sData(file_data,start_datetime,col_dict.values(),'heatbalance_{}_s'.format(network))
                            
                        self.signals.progress.emit(98)
                        
                        #--------mass balance------
                        if self.simulatedOutputs['massbalance_system']: 
                            #print('------mass balance----------')

                            fname=dir_path+'results-macro_{}\\massbalance_outputfile.prn'.format(network)
                            #print(fname)

                            if os.path.exists(fname):
                                #get output headers
                                components_idm=propertyListCompsIDM(getIDAListComponents(readFileToString(dir_path+'results-macro_{}.idm'.format(network))))
                                for comp in components_idm:
                                    if getCompName(comp)=='"massbalance_outputfile"': 
                                        as_dict={}
                                        for subcomp in comp:
                                            if getCompClass(subcomp)=='OUTPUT-FILE':                     
                                                names = re.findall(r'([A-Z_]+)\s+#S', subcomp[':DF'])
                                                as_dict={name.lower() : '' for name in names}
                                                
                                            elif getCompClass(subcomp)==':VAR':   
                                                as_dict[subcomp[':N'].lower()]=tr('@default',subcomp[':D'].replace('"',''))       
                                #print(as_dict)
                                
                                col_dict={}
                                with open(fname, "r") as myfile:
                                    for line in myfile:
                                        if line[0]=='#':
                                            line=line[1:]
                                        col_dict={counter: as_dict[col.lower()] for counter,col in enumerate(line.split(),0) if counter>1}
                                        break

                                file_data = np.loadtxt(fname, skiprows=1,dtype=float)
                                
                                        
                                if self.dlg.checkbox_timestep.checkState() == checkState():
                                    #linear interpolation
                                    file_data=interpolateTimeData(float(self.dlg.interpolation_dt.text()),file_data)
                                        
                                #print(file_data)
                                
                                sql="""\nDROP TABLE IF EXISTS "{}".massbalance_{}_s CASCADE;
CREATE TABLE "{}".massbalance_{}_s
(
    id serial,
    time timestamp,{}
    CONSTRAINT massbalance_s_{}_pkey PRIMARY KEY (id)
);""".format(self.config['versionName'],network,self.config['versionName'],network,''.join(['\n   "{}" numeric,'.format(col_name) for col_name in col_dict.values()]),network) # nosec B608
                                #print(sql)
                                self.cur.execute(sql)
                            
                                self.copy_string_iterator_system_balance_sData(file_data,start_datetime,col_dict.values(),'massbalance_{}_s'.format(network))
                            
                        self.signals.progress.emit(99)
                        
                        
                except Exception:
                    QgsMessageLog.logMessage(
                        traceback.format_exc(),
                        "Districts",
                        MessageCritical
                    )
                        
    def checkConnTypeSeqOutputFile(self,fname,feature_type,feature,seq,connValues,conn_outputs,power_output):
        """Log a QGIS error, if the connection type output file is missing or does not contain all requested variables"""
        expected_vars=['{}_{}'.format(output,connValue['conn_seq']) for connValue in connValues if connValue['conn_type_seq']==seq for output in conn_outputs]
        if power_output:
            expected_vars.append('power')
        if not expected_vars:
            return
        #only one message per template, connection type sequence and error
        feature_name='{} template {} (e.g. {} {})'.format(tr('@default',feature_type),feature['template_name'],tr('@default',feature_type),feature['id'])
        if not os.path.exists(fname):
            error_key=(feature_type,feature['template_name'],seq,'file')
            if error_key in self.reported_errors:
                return
            self.reported_errors.add(error_key)
            QgsMessageLog.logMessage(
                "{}: output file 'Connection type sequence_{}.prn' not found ({})".format(feature_name,seq,fname),
                "Districts",
                MessageCritical
            )
            return
        with open(fname, "r") as myfile:
            header=[var.lstrip('#') for var in myfile.readline().split()]
        missing_vars=[var for var in expected_vars if var not in header]
        error_key=(feature_type,feature['template_name'],seq,tuple(missing_vars))
        if missing_vars and error_key not in self.reported_errors:
            self.reported_errors.add(error_key)
            QgsMessageLog.logMessage(
                "{}: variables missing in output file 'Connection type sequence_{}.prn': {}".format(feature_name,seq,', '.join(missing_vars)),
                "Districts",
                MessageCritical
            )

    def copy_string_iterator_system_balance_sData(self, sdata,start_datetime,col_names,table_name) -> None:
        with self.conn.cursor() as cursor:
            max_id=getMaxIdSchema(self.cur,table_name,self.config['versionName'])+1
            mdata_string_iterator = StringIteratorIO((
                '|'.join(map(clean_csv_value, (
                    int(row_counter+max_id),
                    start_datetime+datetime.timedelta(hours=float(data[0])),
                    * [data[col] for col,col_name in enumerate(col_names,2)]
                ))) + '\n'
                for row_counter,data in enumerate(sdata)
            ))
            cursor.copy_expert("""COPY "{}".{} FROM STDIN WITH (FORMAT csv, DELIMITER '|');""".format(self.config['versionName'],table_name),mdata_string_iterator) # nosec B608

    def timeStrings(self,times,start_datetime):
        """timestamps (as COPY text) of the time column of an output file (hours since start_datetime); cached, since
        all files of a simulation usually have the same time column"""
        key=times.tobytes()
        time_strings=self.time_strings_cache.get(key)
        if time_strings is None:
            time_strings=[str(start_datetime+datetime.timedelta(hours=float(h))) for h in times]
            if len(self.time_strings_cache)>16:
                self.time_strings_cache.clear()
            self.time_strings_cache[key]=time_strings
        return time_strings

    def featureGeometries(self,feature_table):
        """{id: geometry as hex EWKB} of a feature table (customers, energy_plants, lines), written directly by COPY
        (an UPDATE of the geometry after loading rewrote every row of the result tables)"""
        self.cur.execute("""SELECT id, geom::text AS geom FROM "{}".{};""".format(self.config['versionName'],feature_table)) # nosec B608
        return {row['id']: row['geom'] or '' for row in self.cur.fetchall()}

    def lineSegGeometries(self,var):
        """{(line id, segment): geometry as hex EWKB} of the simulated pipe segments (line_seg_temp, line_seg_p)"""
        self.cur.execute("""SELECT lid, lid_seg, geom::text AS geom FROM "{}".line_seg_{};""".format(self.config['versionName'],var)) # nosec B608
        return {(row['lid'],row['lid_seg']): row['geom'] or '' for row in self.cur.fetchall()}

    def copy_feature_sData(self,copy_buffer,sdata,fid,geom,col_dict,start_datetime) -> None:
        """add the columns of an output file of a feature (col_dict: {column: {'table_name': ...}}) to the result tables
        (columns id, fid, time, geom, value)"""
        time_strings=self.timeStrings(sdata[:,0],start_datetime)
        n=len(time_strings)
        middle='|{}|'.format(fid)
        suffix='|{}|'.format(geom)
        for col in col_dict:
            table_name=col_dict[col]['table_name']
            first_id=copy_buffer.nextId(table_name,n)
            copy_buffer.add(table_name,''.join([
                '{}{}{}{}{}\n'.format(row_id,middle,t,suffix,value)
                for row_id,t,value in zip(range(first_id,first_id+n),time_strings,sdata[:,col].tolist())]))

    def createResultLayerIndex(self,tables,type):
        for counter,table_name in enumerate(tables,1):
            #print('-------------**---**-'+table_name.split('_')[1].split('$')[0])
            if type=='line' and table_name.split('$')[0].split('_')[-1] in ['temp','p']:
                sql="""CREATE INDEX "idx_{}_fid_time_segment" ON {}."{}" (fid, time, segment);""".format(table_name,self.config['versionName'],table_name) # nosec B608
            else:
                sql="""CREATE INDEX "idx_{}_fid_time" ON {}."{}" (fid, time);""".format(table_name,self.config['versionName'],table_name) # nosec B608
            #print(sql)
            self.cur.execute(sql)
            
    def copy_line_sData(self,copy_buffer,sdata,fid,table_names,value_per_conn_seq,start_datetime,segment_geoms) -> None:
        """add the output of a line to the result tables (one table per pipe of the bundle, value_per_conn_seq columns
        (segments) per pipe; columns id, fid, time, geom, segment, value); segment_geoms: geometry per segment"""
        value_per_conn_seq=int(value_per_conn_seq)
        time_strings=self.timeStrings(sdata[:,0],start_datetime)
        n=len(time_strings)*value_per_conn_seq
        prefixes=['|{}|'.format(fid)]*value_per_conn_seq
        suffixes=['|{}|{}|'.format(geom,segment) for segment,geom in enumerate(segment_geoms,1)]
        start_col_index=2
        for table_name in table_names:
            first_id=copy_buffer.nextId(table_name,n)
            ids=iter(range(first_id,first_id+n))
            copy_buffer.add(table_name,''.join([
                '{}{}{}{}{}\n'.format(next(ids),prefix,t,suffix,value)
                for t,row in zip(time_strings,sdata[:,start_col_index:start_col_index+value_per_conn_seq].tolist())
                for prefix,suffix,value in zip(prefixes,suffixes,row)]))
            start_col_index+=value_per_conn_seq


class ResultCopyBuffer:
    """Collects the rows of the result tables and loads them with one COPY per table and chunk (max_chars)
    instead of one COPY per feature and table. The ids are counted here (highest id of the table + 1 at the first use)."""
    def __init__(self,conn,cur,schema,max_chars=16*1024*1024):
        self.conn=conn
        self.cur=cur
        self.schema=schema
        self.max_chars=max_chars
        self.rows={}
        self.chars={}
        self.next_id={}

    def nextId(self,table_name,count):
        """first id of the next count rows of table_name"""
        if table_name not in self.next_id:
            self.next_id[table_name]=getMaxIdSchema(self.cur,table_name,self.schema)+1
        first_id=self.next_id[table_name]
        self.next_id[table_name]+=count
        return first_id

    def add(self,table_name,text):
        self.rows.setdefault(table_name,[]).append(text)
        self.chars[table_name]=self.chars.get(table_name,0)+len(text)
        if self.chars[table_name]>=self.max_chars:
            self.flush(table_name)

    def flush(self,table_name=None):
        """COPY the collected rows (of table_name or all tables)"""
        for name in [table_name] if table_name else list(self.rows):
            data=''.join(self.rows.pop(name,[]))
            self.chars.pop(name,None)
            if data:
                with self.conn.cursor() as cursor:
                    #the rows are ASCII only (numbers, timestamps, hex geometries): send bytes, the client encoding (e.g. WIN1252) is much slower
                    cursor.copy_expert("""COPY "{}".{} FROM STDIN WITH (FORMAT csv, DELIMITER '|');""".format(self.schema,name),io.BytesIO(data.encode('ascii'))) # nosec B608