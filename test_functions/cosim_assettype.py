from plugins.utility_functions.files import *
from plugins.utility_functions.db import *
import psycopg2.extras
import psycopg2
from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT
plugin_dir="""C:\\Users\\Peter\\AppData\\Roaming\\QGIS\\QGIS3\\profiles\\default\\python\\plugins"""
dictDB={'pwd' : 'p3t3r' , 'host' : 'localhost','port':'5433', 'user' : 'postgres', 'projectName' : 'cosim_test1', 'versionName' : 'b'}
#dictDB=getDBConnectionData(plugin_dir)
conn=dbConnect(dictDB,True)
cur=conn.cursor(cursor_factory = psycopg2.extras.RealDictCursor)
import math
import os

sql="""--customers
(SELECT f.id,'Customer' AS feature,
    array_agg('{''pmt2_name'': '''||b_t_conns.conn_bundle_type_id::text||'_'||b_t_conns.sequence::text||'_'||b_t_conns.conn_type_id::text||'_'||c_t_conns.sequence::text||'_T'||conns.temp::text||
            ''', ''mdot'': '||CASE WHEN conns.mdot IS NULL AND 2 = f.submodel THEN 'True' ELSE 'False' END||', ''conn_dir'': '''|| conn_dir.name::text||'''}' ORDER BY b_t_conns.sequence,c_t_conns.sequence) AS conns
    FROM b.customers f, b.customer_connections f_conns, b.lines l, customer_assettypes f_at, bundle_type_conns b_t_conns, connection_type_connections c_t_conns, connections conns, prefered_conn_dir conn_dir
    WHERE conn_dir.id=conns.type AND f.id=f_conns.cid AND l.id=f_conns.lid AND 2 = f.submodel AND 1 = ANY (l.submodel) AND 
        f_at.assettype=f.assettype AND f_at.assetgroup=f.assetgroup AND 
        f_at.conn_bundle_type=b_t_conns.conn_bundle_type_id AND c_t_conns.connection_type_id=b_t_conns.conn_type_id AND conns.id=c_t_conns.connection_id
    GROUP BY f.id)
UNION
--energy plants
(SELECT f.id, 'Energy_plant' AS feature,
    array_agg('{''pmt2_name'': '''||b_t_conns.conn_bundle_type_id::text||'_'||b_t_conns.sequence::text||'_'||b_t_conns.conn_type_id::text||'_'||c_t_conns.sequence::text||'_T'||conns.temp::text||
            ''', ''mdot'': '||CASE WHEN conns.mdot IS NULL AND 2 = f.submodel THEN 'True' ELSE 'False' END||', ''conn_dir'': '''|| conn_dir.name::text||'''}' ORDER BY b_t_conns.sequence,c_t_conns.sequence) AS conns
    FROM b.energy_plants f, b.energy_plant_connections f_conns, b.lines l, energy_plant_assettypes f_at, bundle_type_conns b_t_conns, connection_type_connections c_t_conns, connections conns, prefered_conn_dir conn_dir
    WHERE conn_dir.id=conns.type AND f.id=f_conns.epid AND l.id=f_conns.lid AND 2 = f.submodel AND 1 = ANY (l.submodel) AND 
        f_at.assettype=f.assettype AND f_at.assetgroup=f.assetgroup AND 
        f_at.conn_bundle_type=b_t_conns.conn_bundle_type_id AND c_t_conns.connection_type_id=b_t_conns.conn_type_id AND conns.id=c_t_conns.connection_id
    GROUP BY f.id)
ORDER BY feature,id;"""

submodel=1
cosim=2
cur.execute(sql)
conn_counter=0
for feature in cur.fetchall():
    print(feature)
    # print([eval(iref)['mdot'] for i,iref in enumerate(feature['conns'],0)])
 #    print(["""((MODEL :N "PMT2mux_{}" :T PMT2\\m\\u\\x)
 # (:VAR :N |P_var| :V 100000{})
 # (:VAR :N |M_var| :V -0.01655{})
 # (:VAR :N |T_var| :V 70.0)
 # ((CONNECTOR :N |term_a|)
 #  (:VAR :N |inStream(T)| :V 70.0{}))
 # ((CONNECTOR :N |term_b|)
 #  (:VAR :N |inStream(T)| :V 70.0))){}\n""".format(eval(iref)['pmt2_name'],
 #    """ :B (:SYSTEM "Co-simulation-macro" "{}<--{}" |data_var| {})""".format(submodel,cosim,conn_counter+i*2+1) if not eval(iref)['mdot'] else '',
 #    """ :B (:SYSTEM "Co-simulation-macro" "{}<--{}" |data_var| {})""".format(submodel,cosim,conn_counter+i*2+1) if eval(iref)['conn_dir']=='Supply' and eval(iref)['mdot'] else ' :B (-1 M 0)' if eval(iref)['mdot'] else '',
 #    """ :B (:SYSTEM "Co-simulation-macro" "{}<--{}" |data_var| {})""".format(submodel,cosim,conn_counter+i*2+2),
 #    """\n((:EO :N "mdot_sign_{}" :T ADDER)
 # (:PAR :N N_IN :V 1)
 # (:PAR :N COEFF :DIM (1) :V #(-1.0))
 # (:VAR :N INSIGNAL :DIM (1) :V #(0.02463) :IV #S(MS-SPARSE DEFAULT-VALUE 0.0 DIMENSION 1 VALUE NIL) :B #S(MS-SPARSE DEFAULT-VALUE NIL DIMENSION 1 VALUE ({}))))""".format(eval(iref)['pmt2_name'].split('_')[3],
 #    """(1 :SYSTEM "Co-simulation-macro" "{}<--{}" |data_var| {})""".format(submodel,cosim,conn_counter+i*2+1)) if eval(iref)['conn_dir']=='Return' else '') for i,iref in enumerate(feature['conns'],0)])
 #    conn_counter+=len([iref for iref in feature['conns']])*2
    print("""(CONNECTIONS {})\n""".format("".join(["{}{}".format("""\n (("PMT2mux_{}" |term_b|) "{}" 0 0 NIL)""".format(eval(iref)['pmt2_name'],eval(iref)['pmt2_name']),
                    """\n (("PMT2mux_{}" M) ("mdot_sign_{}" OUTSIGNALLINK) 0 0 NIL)""".format(eval(iref)['pmt2_name'],eval(iref)['pmt2_name'].split('_')[3]) if eval(iref)['conn_dir']=='Return' else '') 
                        for iref in feature['conns']])))
    