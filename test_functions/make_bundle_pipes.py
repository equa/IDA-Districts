import psycopg2.extras
import psycopg2
import copy
from plugins.utility_functions.db import *

from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT
plugin_dir="""C:\\Users\\Peter\\AppData\\Roaming\\QGIS\\QGIS3\\profiles\\default\\python\\plugins\\"""
dictDB={'pwd' : 'p3t3r' , 'host' : 'localhost','port':'5433', 'user' : 'postgres', 'projectName' : 'owa24062025', 'versionName' : 'd_opt_v5'}
#dictDB=getDBConnectionData(plugin_dir)
conn=dbConnect(dictDB,True)
cur=conn.cursor(cursor_factory = psycopg2.extras.RealDictCursor)
print(cur)

sql="""Select a.pipe_bundle_type_id, di_a, di_w
    from 
    (Select pipe_bundle_type_id,innerpipediameter as di_w,sequence from pipes p, bundle_pipes bp where p.id=bp.pipe_id and sequence=1) w,
    (Select pipe_bundle_type_id,innerpipediameter as di_a,sequence from pipes p, bundle_pipes bp where p.id=bp.pipe_id and sequence=2) a
    where a.pipe_bundle_type_id=w.pipe_bundle_type_id
    order by pipe_bundle_type_id;"""
cur.execute(sql)

db_bp={int(i['pipe_bundle_type_id']): [float(i['di_a']),float(i['di_w'])]for i in cur.fetchall()}
print(db_bp)
print(db_bp.values())

sql="SELECT di_a_m,di_warm_m FROM d_opt_v7.lines GROUP BY di_a_m,di_warm_m"
cur.execute(sql)

di_pairs=[[float(i['di_a_m']),float(i['di_warm_m'])] for i in cur.fetchall()]
print(di_pairs)

sql = ""
for item in di_pairs:
    print('---')
    print(item)
    found=False
    for key, value in db_bp.items():
        if item == value:
            found=True
            print(key)
            sql+="UPDATE d_opt_v7.lines set pipe_bundle_type_id={} WHERE di_a_m={} AND di_warm_m={};\n".format(
                key,value[0],value[1])
    print(found)

print(sql)
cur.execute(sql)
    
    
    