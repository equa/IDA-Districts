import numpy as np
import matplotlib.pyplot as plt

import datetime
import matplotlib.dates as mdates
from matplotlib.ticker import AutoMinorLocator


from plugins.utility_functions.files import *
from plugins.ida_mosim.invoke import *
import psycopg2.extras
import psycopg2
from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT
plugin_dir="""C:\\Users\\Peter\\AppData\\Roaming\\QGIS\\QGIS3\\profiles\\default\\python\\plugins"""
dictDB={'pwd' : 'p3t3r' , 'host' : 'localhost','port':'5433', 'user' : 'postgres', 'projectName' : 'schwarzenberg', 'versionName' : 'a'}
#dictDB=getDBConnectionData(plugin_dir)
conn=dbConnect(dictDB,True)
cur=conn.cursor(cursor_factory = psycopg2.extras.RealDictCursor)
#print(cur)

sql="""SELECT id from "{}".customers WHERE network=2 ORDER BY id;""".format(dictDB['versionName'])
cur.execute(sql)
ids=[id['id'] for id in cur.fetchall()]
#print(ids)

fig, ax = plt.subplots(layout='constrained')
power_sum=[]
count=0
for id in ids:
    #print(id)
    sql="""SELECT owner FROM "{}".customers WHERE id = {};""".format(dictDB['versionName'],id)
    cur.execute(sql)
    
    legend=cur.fetchone()['owner']
#    file=plugin_dir+'\\ida_mosim\\models\\{}\\{}\\invoked_customers\\Customer_{}\\Customer_{}\\Hx.prn'.format(dictDB['projectName'],dictDB['versionName'],id,id)
    file=plugin_dir+'\\ida_mosim\\models\\{}\\{}\\network_1\\Customer_{}\\Hx.prn'.format(dictDB['projectName'],dictDB['versionName'],id)

    #print(file)
    filedata=readFileToList(file)

    #print(filedata)
    i=0
    time=[]
    power=[]
    for line in filedata:
        if i>0:
            data=line.strip().split()
            power.append([float(data[0]),float(data[3])])
        i+=1    
    
    power=np.array(power)    
    #print(power)

    time=np.arange(0,8760,0.5)
    #print(time)


    #linear interpolation
    valuesInt = np.interp(time, power[:,0], power[:,1])
    if count==0:
        power_sum=valuesInt
    else:
        power_sum=np.add(power_sum,valuesInt)

    #plotting
    ax.plot(time, valuesInt, label=str(id))#legend)
    count+=1
    


ax.set_xlabel('Time, h')
ax.set_ylabel('Power, W')
ax.set_title('Load profiles customers Schwarzenberg')
#ax.set_title('Load profiles customers Fohrbach')
plt.xticks([0,744,1416,2160,2880,3624,4344,5088,5832,6552,7296,8016,8760])
plt.legend()
plt.show()

fig1, ax1 = plt.subplots(layout='constrained')
ax1.plot(time, power_sum, label='Total')
ax1.set_xlabel('Time, h')
ax1.set_ylabel('Power, W')
ax1.set_title('Total load profiles Schwarzenberg')
#ax1.set_title('Total load profiles Fohrbach')
plt.xticks([0,744,1416,2160,2880,3624,4344,5088,5832,6552,7296,8016,8760])
plt.legend()
plt.show()