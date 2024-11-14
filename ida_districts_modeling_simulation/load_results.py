from plugins.utility_functions.files import *
from plugins.utility_functions.db import *
from plugins.utility_functions.dialog import *
from plugins.utility_functions.topology import *

from PyQt5.QtCore import QObject, pyqtSlot, pyqtSignal,QRunnable

import datetime
from plugins.utility_functions.workers import APISignals

class WorkerLoadResults(QRunnable):      
    """Worker thread
    Inherits from QRunnable to handle worker thread setup, signals and wrap-up."""
    def __init__(self,*args,**kwargs):
        super().__init__()
        self.args=args
        print(args)
        self.signals=APISignals()
        self.dictDB=kwargs['dictDB']
        self.dlg=kwargs['dlg']
        self.conn=""
        self.cur=""
        self.plugin_dir=kwargs['plugin_dir']
        self.submodels=kwargs['submodels']
        self.simulatedOutputs=kwargs['simulatedOutputs']
        self.conn = dbConnect(self.dictDB,True)
        if self.conn:
            self.cur=self.conn.cursor(cursor_factory = psycopg2.extras.RealDictCursor)
            
    @pyqtSlot()
    def run(self):
        print('run worker invoke network')
        self.progress_value=1
        self.signals.progress.emit(self.progress_value)
        self.loadResults()
        self.signals.progress.emit(100)  
        
    def loadResults(self):
        print('-***-')
        networkSimData=loadNetworkSimData(self.plugin_dir,self.dictDB)

        srid=loadProjectConfig(self.plugin_dir,self.dictDB['projectName'])['srid']
        modellingSettings=loadModellingSettings(self.plugin_dir,self.dictDB)

        #re-create table line_seg for temperature (according to the pipe distrectization) and pressure (2 segments per line), which holds the geometry of the simulated pipe segements
        sql='\n'.join(["""DROP TABLE IF EXISTS {}.line_seg_{};
CREATE TABLE IF NOT EXISTS {}.line_seg_{}
(
    id serial,
    lid integer NOT NULL,
    lid_seg integer NOT NULL,
    geom geometry(LineStringZ,{})
);
{}""".format(self.dictDB['versionName'],output.split('_')[0],self.dictDB['versionName'],output.split('_')[0],srid,
            "SELECT segmentize({},'{}','line_seg_temp');".format(modellingSettings['fd_meterPerNode'],self.dictDB['versionName']) if output=='temp_lines' else "SELECT halve_geom('{}','line_seg_p');".format(self.dictDB['versionName']))
            for output in self.simulatedOutputs if output in ['temp_lines','p_lines'] and self.simulatedOutputs[output]])
        if sql:
            self.cur.execute(sql)
        
        for i in range(self.dlg.combo_submodels.count()):
            if self.dlg.combo_submodels.itemText(i) != 'Check all items' and self.dlg.combo_submodels.itemChecked(i):        
                submodel=self.dlg.combo_submodels.itemText(i)
                print(submodel)
                dir_path=self.plugin_dir+'\\network_models\\{}\\{}\\network_{}\\'.format(self.dictDB['projectName'],self.dictDB['versionName'],submodel)
                pipe_sequences=getUsedPipeBundleSequences(self.cur,self.dictDB)
                #-----update DB tables--------
                #-----------create tables----------------
                #customer tables: customer_s_troom, customer_s_balance, customer_s_conntype_[conn type seq]
                c_outputs=[output.split('_')[0] for output in self.simulatedOutputs if output.split('_')[1]=='c' and self.simulatedOutputs[output]]
                if c_outputs:
                    used_b_types=getUsedConnBundleTypes('customer',self.cur,self.dictDB)
                    c_conn_outputs=[output.split('_')[0] for output in self.simulatedOutputs if output.split('_')[1]=='c' and self.simulatedOutputs[output] and output.split('_')[0] not in['troom','heatbalance','power']]
                    conn_names= [ident for connBundleType in used_b_types for ident in getPMT2muxIdents(self.cur,connBundleType)]
                    conn_t_power_names= getUsedConnTypeIdents('customer',self.cur,self.dictDB)
                    tables=[]
                    
                    print(conn_names)
                    print(conn_t_power_names)
                    #connection tables (p,m,T)
                    sql='\n'.join(["""DROP TABLE IF EXISTS {}.customer_s_{}${} CASCADE;
CREATE TABLE {}.customer_s_{}${}
(
	id serial,
    fid integer,
    time timestamp,
	geom geometry(PointZ,{}),
	"${}" numeric,
	CONSTRAINT customer_s_{}${}_pkey PRIMARY KEY (id)
);""".format(self.dictDB['versionName'],output,conn_name,self.dictDB['versionName'],output,conn_name,srid,output,output,conn_name) 
                        for output in c_conn_outputs for conn_name in conn_names])
                    tables+=["customer_s_{}${}".format(output,conn_name) for output in c_conn_outputs for conn_name in conn_names]
                    
                    #connection type tables (power)
                    if 'power' in c_outputs:
                        sql+='\n'.join(["""DROP TABLE IF EXISTS {}.customer_s_power${} CASCADE;
CREATE TABLE {}.customer_s_power${}
(
	id serial,
    fid integer,
    time timestamp,
	geom geometry(PointZ,{}),
	"$power" numeric,
	CONSTRAINT customer_s_power${}_pkey PRIMARY KEY (id)
);""".format(self.dictDB['versionName'],ident,self.dictDB['versionName'],ident,srid,ident) 
                            for ident in conn_t_power_names])
                        tables+=["customer_s_power${}".format(ident) for ident in conn_t_power_names]

                    #room air temperature table
                    if 'troom' in c_outputs:
                        sql+="""\nDROP TABLE IF EXISTS {}.customer_s_troom CASCADE;
CREATE TABLE {}.customer_s_troom
(
	id serial,
    fid integer,
    time timestamp,
	geom geometry(PointZ,{}),
	"$troom" numeric,
	CONSTRAINT customer_s_troom_pkey PRIMARY KEY (id)
);""".format(self.dictDB['versionName'],self.dictDB['versionName'],srid)
                        tables.append('customer_s_troom')   

                    #heat balance table
                    if 'heatbalance' in c_outputs:
                        sql+="""\nDROP TABLE IF EXISTS {}.customer_s_electricity CASCADE;
CREATE TABLE {}.customer_s_electricity
(
	id serial,
    fid integer,
    time timestamp,
	geom geometry(PointZ,{}),
	"$electricity" numeric,
	CONSTRAINT customer_s_electricity_pkey PRIMARY KEY (id)
);""".format(self.dictDB['versionName'],self.dictDB['versionName'],srid)
                        tables.append('customer_s_electricity')

                        sql+="""\nDROP TABLE IF EXISTS {}.customer_s_transmission CASCADE;
CREATE TABLE {}.customer_s_transmission
(
	id serial,
    fid integer,
    time timestamp,
	geom geometry(PointZ,{}),
	"$transmission" numeric,
	CONSTRAINT customer_s_transmission_pkey PRIMARY KEY (id)
);""".format(self.dictDB['versionName'],self.dictDB['versionName'],srid)
                        tables.append('customer_s_transmission')
                        sql+="""\nDROP TABLE IF EXISTS {}.customer_s_heating CASCADE;
CREATE TABLE {}.customer_s_heating
(
	id serial,
    fid integer,
    time timestamp,
	geom geometry(PointZ,{}),
	"$heating" numeric,
	CONSTRAINT customer_s_heating_pkey PRIMARY KEY (id)
);""".format(self.dictDB['versionName'],self.dictDB['versionName'],srid)
                        tables.append('customer_s_heating')
                        sql+="""\nDROP TABLE IF EXISTS {}.customer_s_gains CASCADE;
CREATE TABLE {}.customer_s_gains
(
	id serial,
    fid integer,
    time timestamp,
	geom geometry(PointZ,{}),
	"$gains" numeric,
	CONSTRAINT customer_s_gains_pkey PRIMARY KEY (id)
);""".format(self.dictDB['versionName'],self.dictDB['versionName'],srid)
                        tables.append('customer_s_gains')
                        sql+="""\nDROP TABLE IF EXISTS {}.customer_s_leakage CASCADE;
CREATE TABLE {}.customer_s_leakage
(
	id serial,
    fid integer,
    time timestamp,
	geom geometry(PointZ,{}),
	"$leakage" numeric,
	CONSTRAINT customer_s_leakage_pkey PRIMARY KEY (id)
);""".format(self.dictDB['versionName'],self.dictDB['versionName'],srid)
                        tables.append('customer_s_leakage')
                        sql+="""\nDROP TABLE IF EXISTS {}.customer_s_occupancy CASCADE;
CREATE TABLE {}.customer_s_occupancy
(
	id serial,
    fid integer,
    time timestamp,
	geom geometry(PointZ,{}),
	"$occupancy" numeric,
	CONSTRAINT customer_s_occupancy_pkey PRIMARY KEY (id)
);""".format(self.dictDB['versionName'],self.dictDB['versionName'],srid)
                        tables.append('customer_s_occupancy')
                        sql+="""\nDROP TABLE IF EXISTS {}.customer_s_solar CASCADE;
CREATE TABLE {}.customer_s_solar
(
	id serial,
    fid integer,
    time timestamp,
	geom geometry(PointZ,{}),
	"$solar" numeric,
	CONSTRAINT customer_s_solar_pkey PRIMARY KEY (id)
);""".format(self.dictDB['versionName'],self.dictDB['versionName'],srid)
                        tables.append('customer_s_solar')
                        sql+="""\nDROP TABLE IF EXISTS {}.customer_s_ventilation CASCADE;
CREATE TABLE {}.customer_s_ventilation
(
	id serial,
    fid integer,
    time timestamp,
	geom geometry(PointZ,{}),
	"$ventilation" numeric,
	CONSTRAINT customer_s_ventilation_pkey PRIMARY KEY (id)
);""".format(self.dictDB['versionName'],self.dictDB['versionName'],srid)
                        tables.append('customer_s_ventilation')
                        
                    print(sql)
                    if sql:
                        self.cur.execute(sql)
                    
                    #load data
                    #get cid`s
                    sql="""SELECT f.id , b_t_conns.conn_bundle_type_id
    FROM {}.dhc_customers f, bundle_type_conns b_t_conns, customer_assettypes at
    WHERE b_t_conns.conn_bundle_type_id = at.conn_bundle_type AND f.assettype=at.assettype AND f.assetgroup=at.assetgroup AND submodel={}
    ORDER BY f.id;""".format(self.dictDB['versionName'],submodel)
                    self.cur.execute(sql)
                    cids=self.cur.fetchall()
                    
                    self.signals.progress.emit(5)
                    
                    b_t_connValues_dict={b_t: getConnsValues(b_t,self.cur) for b_t in used_b_types}
                    print(b_t_connValues_dict)
                    for id in cids:
                        print(id)
                        print(c_conn_outputs)
                        if c_conn_outputs or conn_t_power_names:
                            connValues=getConnsValues(id['conn_bundle_type_id'],self.cur)
                            conn_type_seq=set([x['conn_type_seq'] for x in b_t_connValues_dict[id['conn_bundle_type_id']]])
                            print(f"conn_type_seq:{conn_type_seq}")
                            for seq in conn_type_seq:
                                fname=dir_path+'customer_'+str(id['id'])+'\\Connection type sequence_{}.prn'.format(seq)
                                print(fname)
                                if os.path.exists(fname):
                                    with open(fname, "r") as myfile:
                                        col_var_dict={}
                                        for line in myfile:
                                            header=line.split()
                                            print(header)
                                            for col,var in enumerate(header,-1):
                                                if len(var.split('_'))==2:
                                                    col_var_dict[col]={'var': var.split('_')[0],'name': var.split('_')[0]+'$'+getPMT2muxIdentFromConnValues(connValues,int(var.split('_')[1])),
                                                        'table_name': 'customer_s_'+var.split('_')[0]+'$'+getPMT2muxIdentFromConnValues(connValues,int(var.split('_')[1]))}
                                                elif var=='power':
                                                    col_var_dict[col]={'var': 'power','name': 'power$'+str(id['conn_bundle_type_id'])+'_'+str(seq),'table_name': 'customer_s_power$'+str(id['conn_bundle_type_id'])+'_'+str(seq)}
                                                    
                                            print(col_var_dict)
                                            break
                                            
                                    file_data = np.loadtxt(fname, skiprows=1,dtype=float)

                                    if self.dlg.checkbox_timestep.checkState() == Qt.Checked:
                                        #linear interpolation
                                        print(self.dlg.interpolation_dt.text())
                                        file_data=interpolateTimeData(float(self.dlg.interpolation_dt.text()),file_data)

                                    #print(file_data)
                                    start_datetime=getDatetimeFromString(networkSimData['calc_time_from'])
                                    self.copy_string_iterator_feature_c_t_seq_sData(file_data,id['id'],col_var_dict,start_datetime)
                        
                        if 'troom' in c_outputs:
                            fname=dir_path+'customer_'+str(id['id'])+'\\TRoom.prn'
                            print(fname)
                            if os.path.exists(fname):         
                                file_data = np.loadtxt(fname, skiprows=1,dtype=float)
                                if self.dlg.checkbox_timestep.checkState() == Qt.Checked:
                                    #linear interpolation
                                    print(self.dlg.interpolation_dt.text())
                                    file_data=interpolateTimeData(float(self.dlg.interpolation_dt.text()),file_data)

                                #print(file_data)
                                start_datetime=getDatetimeFromString(networkSimData['calc_time_from'])
                                col_var_dict={2: {'var': 'troom','name': '','table_name': 'customer_s_troom'}}
                                self.copy_string_iterator_feature_c_t_seq_sData(file_data,id['id'],col_var_dict,start_datetime)
                            
                        if 'heatbalance' in c_outputs:
                            fname=dir_path+'customer_'+str(id['id'])+'\\Heatbalance.prn'.format(seq)
                            print(fname)
                            if os.path.exists(fname):                                              
                                file_data = np.loadtxt(fname, skiprows=1,dtype=float)
                                if self.dlg.checkbox_timestep.checkState() == Qt.Checked:
                                    #linear interpolation
                                    print(self.dlg.interpolation_dt.text())
                                    file_data=interpolateTimeData(float(self.dlg.interpolation_dt.text()),file_data)
                                #print(file_data)
                                start_datetime=getDatetimeFromString(networkSimData['calc_time_from'])
                                self.copy_string_iterator_c_heatbalance_sData(file_data,id['id'],start_datetime)
                    #update point geometry
                    print(tables)
                    if tables:
                        self.updateResultLayerGeometry(tables,'customer')
                        
                self.signals.progress.emit(33)
                                
                    
                #energy plant tables: customer_s_conntype_[conn type seq]
                ep_outputs=[output.split('_')[0] for output in self.simulatedOutputs if output.split('_')[1]=='ep' and self.simulatedOutputs[output]]
                if ep_outputs:
                    used_b_types=getUsedConnBundleTypes('energy_plant',self.cur,self.dictDB)
                    ep_conn_outputs=[output.split('_')[0] for output in self.simulatedOutputs if output.split('_')[1]=='ep' and self.simulatedOutputs[output] and output.split('_')[0] not in ['power']]
                    conn_names= [ident for connBundleType in used_b_types for ident in getPMT2muxIdents(self.cur,connBundleType)]
                    conn_t_power_names= getUsedConnTypeIdents('energy_plant',self.cur,self.dictDB)
                    tables=[]
                    print(conn_names)
                    print(conn_t_power_names)
                    #connection tables (p,m,T)
                    sql='\n'.join(["""DROP TABLE IF EXISTS {}.energy_plant_s_{}${} CASCADE;
CREATE TABLE {}.energy_plant_s_{}${}
(
	id serial,
    fid integer,
    time timestamp,
	geom geometry(PointZ,{}),
	"${}" numeric,
	CONSTRAINT energy_plant_s_{}${}_pkey PRIMARY KEY (id)
);""".format(self.dictDB['versionName'],output,conn_name,self.dictDB['versionName'],output,conn_name,srid,output,output,conn_name) 
                        for output in ep_conn_outputs for conn_name in conn_names])
                    tables+=["energy_plant_s_{}${}".format(output,conn_name) for output in ep_conn_outputs for conn_name in conn_names]
                        
                    #connection type tables (power)
                    if 'power' in ep_outputs:
                        sql+='\n'.join(["""DROP TABLE IF EXISTS {}.energy_plant_s_power${} CASCADE;
CREATE TABLE {}.energy_plant_s_power${}
(
	id serial,
    fid integer,
    time timestamp,
	geom geometry(PointZ,{}),
	"$power" numeric,
	CONSTRAINT energy_plant_s_power${}_pkey PRIMARY KEY (id)
);""".format(self.dictDB['versionName'],ident,self.dictDB['versionName'],ident,srid,ident) 
                            for ident in conn_t_power_names])
                        tables+=["energy_plant_s_power${}".format(ident) for ident in conn_t_power_names]
                    
                    print(sql)
                    if sql:
                        self.cur.execute(sql)
                        
                    #load data
                    #get epid`s
                    sql="""SELECT f.id , b_t_conns.conn_bundle_type_id
    FROM {}.dhc_energy_plants f, bundle_type_conns b_t_conns, energy_plant_assettypes at
    WHERE b_t_conns.conn_bundle_type_id = at.conn_bundle_type AND f.assettype=at.assettype AND f.assetgroup=at.assetgroup AND submodel={};""".format(self.dictDB['versionName'],submodel)
                    print(sql)
                    self.cur.execute(sql)
                    epids=self.cur.fetchall()
                    
                    b_t_connValues_dict={b_t: getConnsValues(b_t,self.cur) for b_t in used_b_types}
                    print(b_t_connValues_dict)
                    for id in epids:
                        print(id)
                        if ep_conn_outputs or conn_t_power_names:
                            connValues=getConnsValues(id['conn_bundle_type_id'],self.cur)
                            conn_type_seq=set([x['conn_type_seq'] for x in b_t_connValues_dict[id['conn_bundle_type_id']]])
                            for seq in conn_type_seq:
                                fname=dir_path+'energy_plant_'+str(id['id'])+'\\Connection type sequence_{}.prn'.format(seq)
                                print(fname)
                                if os.path.exists(fname):
                                    with open(fname, "r") as myfile:
                                        col_var_dict={}
                                        for line in myfile:
                                            header=line.split()
                                            print(header)
                                            for col,var in enumerate(header,-1):
                                                if len(var.split('_'))==2:
                                                    col_var_dict[col]={'var': var.split('_')[0],'name': var.split('_')[0]+'$'+getPMT2muxIdentFromConnValues(connValues,int(var.split('_')[1])),
                                                        'table_name': 'energy_plant_s_'+var.split('_')[0]+'$'+getPMT2muxIdentFromConnValues(connValues,int(var.split('_')[1]))}
                                                elif var=='power':
                                                    col_var_dict[col]={'var': 'power','name': 'power$'+str(id['conn_bundle_type_id'])+'_'+str(seq),'table_name': 'energy_plant_s_power$'+str(id['conn_bundle_type_id'])+'_'+str(seq)}
                                                    
                                            print(col_var_dict)
                                            break
                                            
                                    file_data = np.loadtxt(fname, skiprows=1,dtype=float)

                                    if self.dlg.checkbox_timestep.checkState() == Qt.Checked:
                                        #linear interpolation
                                        print(self.dlg.interpolation_dt.text())
                                        file_data=interpolateTimeData(float(self.dlg.interpolation_dt.text()),file_data)
                                    #print(file_data)
                                    start_datetime=getDatetimeFromString(networkSimData['calc_time_from'])
                                    self.copy_string_iterator_feature_c_t_seq_sData(file_data,id['id'],col_var_dict,start_datetime)
                    #update point geometry
                    print(tables)
                    if tables:
                        self.updateResultLayerGeometry(tables,'energy_plant')
                        
                self.signals.progress.emit(66)
                #lines tables: line_s_t,line_s_v,nodes_s_mdot,nodes_s_p,nodes_s_t
                line_outputs=[output.split('_')[0] for output in self.simulatedOutputs if output.split('_')[1]=='lines' and self.simulatedOutputs[output]]
                if line_outputs:
                    sql='\n'.join(["""DROP TABLE IF EXISTS {}.line_s_{}${} CASCADE;
CREATE TABLE {}.line_s_{}${}
(
	id serial,
    fid integer,
    time timestamp,
	geom geometry(LineStringZ,{}),
	segment integer,
	"${}" numeric,
	CONSTRAINT line_s_{}${}_pkey PRIMARY KEY (id)
);""".format(self.dictDB['versionName'],output,seq,self.dictDB['versionName'],output,seq,srid,output,output,seq) 
                        for output in line_outputs for seq in pipe_sequences])
                    print(sql)
                    self.cur.execute(sql)

                    #load data
                    #get lids
                    sql="""SELECT id FROM {}.dhc_lines WHERE {}=ANY(submodel) ORDER BY id;""".format(self.dictDB['versionName'],submodel)
                    self.cur.execute(sql)
                    lids=self.cur.fetchall()
                    
                    for output in line_outputs:
                        print('+++++++++'+output+'++++++++++++')
                        #get connection sequence
                        for id in lids:
                            fname=dir_path+'Line_{}_{}.prn'.format(output,id['id'])
                            print(fname)
                            if os.path.exists(fname):
                                data=[]
                                if output=='temp': #get number of temp segments per line; just read first line
                                    with open(fname, "r") as myfile:
                                        for line in myfile:
                                            values_len=len(line.split())-3
                                            conn_seq_len=len(set([int(i.split('_')[1]) for i in line.split()[3:]]))
                                            value_per_conn_seq=values_len/conn_seq_len
                                            print(value_per_conn_seq)
                                            break
                                elif output=='p':
                                    with open(fname, "r") as myfile:
                                        for line in myfile:
                                            values_len=len(line.split())-3
                                            break
                                    value_per_conn_seq=2
                                    conn_seq_len=values_len/value_per_conn_seq
                                    print(value_per_conn_seq)
                                    print(conn_seq_len)
                                else:
                                    value_per_conn_seq=1
                                    print(value_per_conn_seq)

                                file_data = np.loadtxt(fname, skiprows=1,dtype=float)
                                if output=='p':
                                    new_order=[0,1]+[int(i+2 + conn_seq_len*j) for i in range(int(conn_seq_len)) for j in range(value_per_conn_seq)]
                                    print(new_order)
                                    file_data=file_data[:,new_order]
                                print(file_data)
                                
                                start_datetime=getDatetimeFromString(networkSimData['calc_time_from'])
                                        
                                if self.dlg.checkbox_timestep.checkState() == Qt.Checked:
                                    #linear interpolation
                                    print(self.dlg.interpolation_dt.text())
                                    file_data=interpolateTimeData(float(self.dlg.interpolation_dt.text()),file_data)
                                        
                                table_names=['line_s_'+output+'$'+str(i) for i in pipe_sequences]
                                print(table_names)
                                self.copy_string_iterator_sData(file_data,id['id'],table_names,value_per_conn_seq,start_datetime,'linestring')
                        
                        #update line geometry
                        if ['line_s_'+output+'$'+str(i) for i in pipe_sequences if output in ['p','temp']]:
                            self.updateResultLayerLineSegGeometry(['line_s_'+output+'$'+str(i) for i in pipe_sequences if output in ['p','temp']])
                        if ['line_s_'+output+'$'+str(i) for i in pipe_sequences if output not in ['p','temp']]:
                            self.updateResultLayerGeometry(['line_s_'+output+'$'+str(i) for i in pipe_sequences if output not in ['p','temp']],'line')
                    self.signals.progress.emit(99)
                        

    def copy_string_iterator_feature_c_t_seq_sData(self,sdata,fid,col_dict,start_datetime) -> None:
        for col in col_dict:
            print(col)
            table_name=col_dict[col]['table_name']
            print(table_name)
            max_id=getMaxIdSchema(self.cur,table_name,self.dictDB['versionName'])+1
            print(max_id)
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
                cursor.copy_expert("COPY {}.{} FROM STDIN WITH (FORMAT csv, DELIMITER '|')".format(self.dictDB['versionName'],table_name),mdata_string_iterator)
                
    def copy_string_iterator_c_heatbalance_sData(self, sdata,fid,start_datetime) -> None:
        table_names=['customer_s_electricity','customer_s_gains','customer_s_heating','customer_s_leakage','customer_s_occupancy','customer_s_solar','customer_s_transmission','customer_s_ventilation']
        with self.conn.cursor() as cursor:
            for col,table_name in enumerate(table_names,2):
                max_id=getMaxIdSchema(self.cur,table_name,self.dictDB['versionName'])+1
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
                cursor.copy_expert("COPY {}.{} FROM STDIN WITH (FORMAT csv, DELIMITER '|')".format(self.dictDB['versionName'],table_name),mdata_string_iterator)
               
    def updateResultLayerGeometry(self,tables,type):
        for table_name in tables:
            sql="""UPDATE {}.{} r set geom = f.geom 
    FROM (SELECT id, geom FROM {}.dhc_{}s) f
    WHERE f.id=r.fid;""".format(self.dictDB['versionName'],table_name,self.dictDB['versionName'],type)
            print(sql)
            self.cur.execute(sql)
            
    def updateResultLayerLineSegGeometry(self,tables):   
        for table_name in tables:
            var=table_name.split('_')[2].split('$')[0]
            sql="""UPDATE {}.{} r set geom = seg.geom 
    FROM (SELECT lid,lid_seg, geom FROM {}.line_seg_{}) seg
    WHERE seg.lid=r.fid AND r.segment=seg.lid_seg;""".format(self.dictDB['versionName'],table_name,self.dictDB['versionName'],var)
            print(sql)
            self.cur.execute(sql)
            
    def copy_string_iterator_sData(self, sdata,fid,table_names,value_per_conn_seq,start_datetime,mode) -> None:
        start_col_index=2
        end_col_index=2+value_per_conn_seq
        for table_name in table_names:
            max_id=getMaxIdSchema(self.cur,table_name,self.dictDB['versionName'])+1
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
                cursor.copy_expert("COPY {}.{} FROM STDIN WITH (FORMAT csv, DELIMITER '|')".format(self.dictDB['versionName'],table_name),mdata_string_iterator)
            start_col_index=end_col_index
            end_col_index=start_col_index+value_per_conn_seq  