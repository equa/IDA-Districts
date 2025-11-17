import numpy as np
from plugins.utility_functions.files import *
from plugins.utility_functions.sensor_signals import *
from plugins.utility_functions.topology import *
import psycopg2.extras
import psycopg2
from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT
from scipy.interpolate import interp1d
import datetime

plugin_dir="""C:\\Users\\Peter\\AppData\\Roaming\\QGIS\\QGIS3\\profiles\\default\\python\\plugins\\ida_mosim"""
dictDB={'pwd' : 'p3t3r' , 'host' : 'localhost','port':'5433', 'user' : 'postgres', 'projectName' : 'test18', 'versionName' : 'a'}
#dictDB=getDBConnectionData(plugin_dir)
conn=dbConnect(dictDB,True)
cur=conn.cursor(cursor_factory = psycopg2.extras.RealDictCursor)
print(cur)

networkSimData=loadNetworkSimData(plugin_dir,dictDB)
print(networkSimData)

def getPMT2muxIdentFromConnValues(connValues,conn_seq):
    try:
        return ["{}_{}_{}_{}".format(connValue['conn_bundle_type_id'],connValue['conn_type_seq'],connValue['conn_type_id'],connValue['conn_seq']) for connValue in connValues if conn_seq==connValue['conn_seq']][0]
    except:
        return ''
     
def interpolateTimeData(dt,file_data):
    start_hour=file_data[0,0]
    start_hour=start_hour-start_hour%(dt/3600)
    print(start_hour)
    end_hour=file_data[-1,0]
    end_hour=end_hour-end_hour%(dt/3600)+dt/3600
    print(end_hour)

    time=np.arange(start_hour, end_hour+dt/3600, dt/3600)

    # apply the interpolation to each column
    f = interp1d(file_data[:,0], file_data[:,1:], axis=0, fill_value="extrapolate")

    # get final result
    file_data=np.column_stack((time,f(time)))
    return file_data
                                        
def copy_string_iterator_customer_sData(connection, sdata,fid,col_dict,start_datetime) -> None:
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
            cursor.copy_expert("""COPY "{}".{} FROM STDIN WITH (FORMAT csv, DELIMITER '|')""".format(dictDB['versionName'],table_name),mdata_string_iterator)

        sql="""UPDATE "{}".{} r set geom = f.geom 
    FROM (SELECT id, geom FROM "{}".customers) f
    WHERE f.id=r.fid;""".format(dictDB['versionName'],table_name,dictDB['versionName'])
        print(sql)
        cur.execute(sql)
                
#header="""#      time         order        m_1          m_2          p_1          p_2          power        t_1          t_2 """

col_var_dict={}
connValues=getConnsValues(1,cur)
print(connValues)
dir_path=plugin_dir+'\\models\\{}\\{}\\network_{}\\'.format(dictDB['projectName'],dictDB['versionName'],1)
id={'id': 1,'conn_bundle_type_id':1}
seq=1
fname=dir_path+'customer_'+str(id['id'])+'\\Connection type sequence_{}.prn'.format(seq)
print(fname)
interpolate_dt=True
if os.path.exists(fname):
    data=[]
    with open(fname, "r") as myfile:
        for line in myfile:
            header=line.split()
            print(header)
            for col,var in enumerate(header,-1):
                if len(var.split('_'))==2:
                    col_var_dict[col]={'var': var.split('_')[0],'name': var.split('_')[0]+'$'+getPMT2muxIdentFromConnValues(connValues,int(var.split('_')[1])),
                        'table_name': 'customer_s_'+var.split('_')[0]+'$'+getPMT2muxIdentFromConnValues(connValues,int(var.split('_')[1]))}
                    
            print(col_var_dict)
            break
            
        file_data = np.loadtxt(fname, skiprows=1,dtype=float)
        
        if interpolate_dt:
            file_data=interpolateTimeData(1800,file_data)
        print(file_data)
        start_datetime=getDatetimeFromString(networkSimData['calc_time_from'])
        copy_string_iterator_customer_sData(conn, file_data,id['id'],col_var_dict,start_datetime)
        
                                            

    