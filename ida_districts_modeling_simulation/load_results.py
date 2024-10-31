from plugins.utility_functions.files import *
from plugins.utility_functions.db import *
from plugins.utility_functions.dialog import *
from qgis.utils import iface
            
def loadResults(dlg,plugin_dir,dictDB,cur,conn):
    print('-***-')
    networkSimData=loadNetworkSimData(plugin_dir,dictDB)
    if len([i for i in range(dlg.combo_submodels.count()) if dlg.combo_submodels.itemText(i) != 'Check all items' and dlg.combo_submodels.itemChecked(i)])==0:
        iface.messageBar().pushMessage("Info", "Please select one or more submodels!", level=Qgis.Info)
        return False
    simulatedOutputs=loadSimulatedOutputs(plugin_dir,dictDB)
    if not simulatedOutputs:
        iface.messageBar().pushMessage("Info", "The project version is not yet simulated!", level=Qgis.Info)
        return False
    srid=loadProjectConfig(plugin_dir,dictDB['projectName'])['srid']
    modellingSettings=loadModellingSettings(plugin_dir,dictDB)

    #re-create table line_seg for temperature (according to the pipe distrectization) and pressure (2 segments per line), which holds the geometry of the simulated pipe segements
    sql='\n'.join(["""DROP TABLE IF EXISTS {}.line_seg_{};
CREATE TABLE IF NOT EXISTS {}.line_seg_{}
(
    id serial,
    lid integer NOT NULL,
    lid_seg integer NOT NULL,
    geom geometry(LineStringZ,{})
);
{}""".format(dictDB['versionName'],output.split('_')[0],dictDB['versionName'],output.split('_')[0],srid,
        "SELECT segmentize({},'{}','line_seg_temp');".format(modellingSettings['fd_meterPerNode'],dictDB['versionName']) if output=='temp_lines' else "SELECT halve_geom('{}','line_seg_p');".format(dictDB['versionName']))
        for output in simulatedOutputs if output in ['temp_lines','p_lines'] and simulatedOutputs[output]])
    if sql:
        cur.execute(sql)
    
    for i in range(dlg.combo_submodels.count()):
        if dlg.combo_submodels.itemText(i) != 'Check all items' and dlg.combo_submodels.itemChecked(i):        
            submodel=dlg.combo_submodels.itemText(i)
            print(submodel)
            dir_path=plugin_dir+'\\network_models\\{}\\{}\\network_{}\\'.format(dictDB['projectName'],dictDB['versionName'],submodel)
            
            connTypeValues=getConnTypeConnValues(cur,getLinesConnTypes(cur,dictDB))

            #-----update DB tables--------
            #-----------create tables----------------
            #customer tables: customer_s_troom, customer_s_balance, customer_s_conntype_[conn type seq]
            c_outputs=[output.split('_')[0] for output in simulatedOutputs if output.split('_')[1]=='c' and simulatedOutputs[output]]
            if c_outputs:
                used_b_types=getUsedConnBundleTypes('customer',cur,dictDB)
                c_conn_outputs=[output.split('_')[0] for output in simulatedOutputs if output.split('_')[1]=='c' and simulatedOutputs[output] and output.split('_')[0] not in['troom','heatbalance','power']]
                conn_names= [ident for connBundleType in used_b_types for ident in getPMT2muxIdents(cur,connBundleType)]
                conn_t_power_names= getUsedConnTypeIdents('customer',cur,dictDB)
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
);""".format(dictDB['versionName'],output,conn_name,dictDB['versionName'],output,conn_name,srid,output,output,conn_name) 
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
);""".format(dictDB['versionName'],ident,dictDB['versionName'],ident,srid,ident) 
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
);""".format(dictDB['versionName'],dictDB['versionName'],srid)
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
);""".format(dictDB['versionName'],dictDB['versionName'],srid)
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
);""".format(dictDB['versionName'],dictDB['versionName'],srid)
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
);""".format(dictDB['versionName'],dictDB['versionName'],srid)
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
);""".format(dictDB['versionName'],dictDB['versionName'],srid)
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
);""".format(dictDB['versionName'],dictDB['versionName'],srid)
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
);""".format(dictDB['versionName'],dictDB['versionName'],srid)
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
);""".format(dictDB['versionName'],dictDB['versionName'],srid)
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
);""".format(dictDB['versionName'],dictDB['versionName'],srid)
                    tables.append('customer_s_ventilation')
                    
                print(sql)
                if sql:
                    cur.execute(sql)
                
                #load data
                #get cid`s
                sql="""SELECT f.id , b_t_conns.conn_bundle_type_id
    FROM {}.dhc_customers f, bundle_type_conns b_t_conns, customer_assettypes at
    WHERE b_t_conns.conn_bundle_type_id = at.conn_bundle_type AND f.assettype=at.assettype AND f.assetgroup=at.assetgroup AND submodel={};""".format(dictDB['versionName'],submodel)
                cur.execute(sql)
                cids=cur.fetchall()
                
                b_t_connValues_dict={b_t: getConnsValues(b_t,cur) for b_t in used_b_types}
                print(b_t_connValues_dict)
                for id in cids:
                    if c_conn_outputs:
                        connValues=getConnsValues(id['conn_bundle_type_id'],cur)
                        conn_type_seq=set([x['conn_type_seq'] for x in b_t_connValues_dict[id['conn_bundle_type_id']]])
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

                                if dlg.checkbox_timestep.checkState() == Qt.Checked:
                                    #linear interpolation
                                    print(dlg.interpolation_dt.text())
                                    if is_number(dlg.interpolation_dt.text()):
                                        file_data=interpolateTimeData(float(dlg.interpolation_dt.text()),file_data)
                                    else:
                                        iface.messageBar().pushMessage("Info", "Please enter a numerical interpolation time!", level=Qgis.Info)
                                        return
                                #print(file_data)
                                start_datetime=getDatetimeFromString(networkSimData['calc_time_from'])
                                copy_string_iterator_feature_c_t_seq_sData(conn, file_data,id['id'],col_var_dict,start_datetime)
                    
                    if 'troom' in c_outputs :
                        fname=dir_path+'customer_'+str(id['id'])+'\\TRoom.prn'.format(seq)
                        print(fname)
                        if os.path.exists(fname):         
                            file_data = np.loadtxt(fname, skiprows=1,dtype=float)
                            if dlg.checkbox_timestep.checkState() == Qt.Checked:
                                #linear interpolation
                                print(dlg.interpolation_dt.text())
                                if is_number(dlg.interpolation_dt.text()):
                                    file_data=interpolateTimeData(float(dlg.interpolation_dt.text()),file_data)
                                else:
                                    iface.messageBar().pushMessage("Info", "Please enter a numerical interpolation time!", level=Qgis.Info)
                                    return
                            #print(file_data)
                            start_datetime=getDatetimeFromString(networkSimData['calc_time_from'])
                            col_var_dict={2: {'var': 'troom','name': '','table_name': 'customer_s_troom'}}
                            copy_string_iterator_feature_c_t_seq_sData(conn, file_data,id['id'],col_var_dict,start_datetime)
                        
                    if 'heatbalance' in c_outputs:
                        fname=dir_path+'customer_'+str(id['id'])+'\\Heatbalance.prn'.format(seq)
                        print(fname)
                        if os.path.exists(fname):                                              
                            file_data = np.loadtxt(fname, skiprows=1,dtype=float)
                            if dlg.checkbox_timestep.checkState() == Qt.Checked:
                                #linear interpolation
                                print(dlg.interpolation_dt.text())
                                if is_number(dlg.interpolation_dt.text()):
                                    file_data=interpolateTimeData(float(dlg.interpolation_dt.text()),file_data)
                                else:
                                    iface.messageBar().pushMessage("Info", "Please enter a numerical interpolation time!", level=Qgis.Info)
                                    return
                            #print(file_data)
                            start_datetime=getDatetimeFromString(networkSimData['calc_time_from'])
                            copy_string_iterator_c_heatbalance_sData(conn, file_data,id['id'],start_datetime)
                #update point geometry
                print(tables)
                if tables:
                    updateResultLayerGeometry(tables,'customer')
                            
                
            #energy plant tables: customer_s_conntype_[conn type seq]
            ep_outputs=[output.split('_')[0] for output in simulatedOutputs if output.split('_')[1]=='ep' and simulatedOutputs[output]]
            if ep_outputs:
                used_b_types=getUsedConnBundleTypes('energy_plant',cur,dictDB)
                ep_conn_outputs=[output.split('_')[0] for output in simulatedOutputs if output.split('_')[1]=='ep' and simulatedOutputs[output] and output.split('_')[0] not in ['power']]
                conn_names= [ident for connBundleType in used_b_types for ident in getPMT2muxIdents(cur,connBundleType)]
                conn_t_power_names= getUsedConnTypeIdents('energy_plant',cur,dictDB)
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
);""".format(dictDB['versionName'],output,conn_name,dictDB['versionName'],output,conn_name,srid,output,output,conn_name) 
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
);""".format(dictDB['versionName'],ident,dictDB['versionName'],ident,srid,ident) 
                        for ident in conn_t_power_names])
                    tables+=["energy_plant_s_power${}".format(ident) for ident in conn_t_power_names]
                
                print(sql)
                if sql:
                    cur.execute(sql)
                    
                #load data
                #get epid`s
                sql="""SELECT f.id , b_t_conns.conn_bundle_type_id
    FROM {}.dhc_energy_plants f, bundle_type_conns b_t_conns, energy_plant_assettypes at
    WHERE b_t_conns.conn_bundle_type_id = at.conn_bundle_type AND f.assettype=at.assettype AND f.assetgroup=at.assetgroup AND submodel={};""".format(dictDB['versionName'],submodel)
                print(sql)
                cur.execute(sql)
                epids=cur.fetchall()
                
                b_t_connValues_dict={b_t: getConnsValues(b_t,cur) for b_t in used_b_types}
                print(b_t_connValues_dict)
                for id in epids:
                    if ep_conn_outputs:
                        connValues=getConnsValues(id['conn_bundle_type_id'],cur)
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
                                                
                                        print(col_var_dict)
                                        break
                                        
                                file_data = np.loadtxt(fname, skiprows=1,dtype=float)

                                if dlg.checkbox_timestep.checkState() == Qt.Checked:
                                    #linear interpolation
                                    print(dlg.interpolation_dt.text())
                                    if is_number(dlg.interpolation_dt.text()):
                                        file_data=interpolateTimeData(float(dlg.interpolation_dt.text()),file_data)
                                    else:
                                        iface.messageBar().pushMessage("Info", "Please enter a numerical interpolation time!", level=Qgis.Info)
                                        return
                                #print(file_data)
                                start_datetime=getDatetimeFromString(networkSimData['calc_time_from'])
                                copy_string_iterator_feature_c_t_seq_sData(conn, file_data,id['id'],col_var_dict,start_datetime)
                #update point geometry
                print(tables)
                if tables:
                    updateResultLayerGeometry(tables,'energy_plant')
            
            #lines tables: line_s_t,line_s_v,nodes_s_mdot,nodes_s_p,nodes_s_t
            line_outputs=[output.split('_')[0] for output in simulatedOutputs if output.split('_')[1]=='lines' and simulatedOutputs[output]]
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
);""".format(dictDB['versionName'],output,connValue['connection_id'],dictDB['versionName'],output,connValue['connection_id'],srid,output,output,connValue['connection_id']) 
                    for output in line_outputs for connValue in connTypeValues])
                print(sql)
                cur.execute(sql)

                #load data
                #get lids
                sql="""SELECT id FROM {}.dhc_lines WHERE {}=ANY(submodel) ORDER BY id;""".format(dictDB['versionName'],submodel)
                cur.execute(sql)
                lids=cur.fetchall()
                
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
                                    
                            if dlg.checkbox_timestep.checkState() == Qt.Checked:
                                #linear interpolation
                                print(dlg.interpolation_dt.text())
                                if is_number(dlg.interpolation_dt.text()):
                                    file_data=interpolateTimeData(float(dlg.interpolation_dt.text()),file_data)
                                else:
                                    iface.messageBar().pushMessage("Info", "Please enter a numerical interpolation time!", level=Qgis.Info)
                                    return
                                    
                            table_names=['line_s_'+output+'$'+str(i['connection_id']) for i in connTypeValues]
                            print(table_names)
                            copy_string_iterator_sData(conn,file_data,id['id'],table_names,value_per_conn_seq,dlg,start_datetime,'linestring')
                    
                    #update line geometry
                    if ['line_s_'+output+'$'+str(i['connection_id']) for i in connTypeValues if output in ['p','temp']]:
                        updateResultLayerLineSegGeometry(['line_s_'+output+'$'+str(i['connection_id']) for i in connTypeValues if output in ['p','temp']])
                    if ['line_s_'+output+'$'+str(i['connection_id']) for i in connTypeValues if output not in ['p','temp']]:
                        updateResultLayerGeometry(['line_s_'+output+'$'+str(i['connection_id']) for i in connTypeValues if output not in ['p','temp']],'line')
    closeDialog(dlg)
                    

def copy_string_iterator_feature_c_t_seq_sData(connection, sdata,fid,col_dict,start_datetime) -> None:
    for col in col_dict:
        print(col)
        table_name=col_dict[col]['table_name']
        print(table_name)
        max_id=getMaxIdSchema(cur,table_name,dictDB['versionName'])+1
        print(max_id)
        with connection.cursor() as cursor:
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
            cursor.copy_expert("COPY {}.{} FROM STDIN WITH (FORMAT csv, DELIMITER '|')".format(dictDB['versionName'],table_name),mdata_string_iterator)
            
def copy_string_iterator_c_heatbalance_sData(connection, sdata,fid,start_datetime) -> None:
    table_names=['customer_s_electricity','customer_s_gains','customer_s_heating','customer_s_leakage','customer_s_occupancy','customer_s_solar','customer_s_transmission','customer_s_ventilation']
    with connection.cursor() as cursor:
        for col,table_name in enumerate(table_names,2):
            max_id=getMaxIdSchema(cur,table_name,dictDB['versionName'])+1
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
            cursor.copy_expert("COPY {}.{} FROM STDIN WITH (FORMAT csv, DELIMITER '|')".format(dictDB['versionName'],table_name),mdata_string_iterator)
           
def updateResultLayerGeometry(tables,type):
    for table_name in tables:
        sql="""UPDATE {}.{} r set geom = f.geom 
    FROM (SELECT id, geom FROM {}.dhc_{}s) f
    WHERE f.id=r.fid;""".format(dictDB['versionName'],table_name,dictDB['versionName'],type)
        print(sql)
        cur.execute(sql)
        
def updateResultLayerLineSegGeometry(tables):   
    for table_name in tables:
        var=table_name.split('_')[2].split('$')[0]
        sql="""UPDATE {}.{} r set geom = seg.geom 
    FROM (SELECT lid,lid_seg, geom FROM {}.line_seg_{}) seg
    WHERE seg.lid=r.fid AND r.segment=seg.lid_seg;""".format(dictDB['versionName'],table_name,dictDB['versionName'],var)
        print(sql)
        cur.execute(sql)
        
def copy_string_iterator_sData(connection, sdata,fid,table_names,value_per_conn_seq,dlg,start_datetime,mode) -> None:
    start_col_index=2
    end_col_index=2+value_per_conn_seq
    for table_name in table_names:
        max_id=getMaxIdSchema(cur,table_name,dictDB['versionName'])+1
        with connection.cursor() as cursor:
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
            cursor.copy_expert("COPY {}.{} FROM STDIN WITH (FORMAT csv, DELIMITER '|')".format(dictDB['versionName'],table_name),mdata_string_iterator)
        start_col_index=end_col_index
        end_col_index=start_col_index+value_per_conn_seq  