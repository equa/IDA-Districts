from plugins.utility_functions.files import *
from plugins.utility_functions.db import *
from plugins.utility_functions.sensor_signals import *
from plugins.utility_functions.topology import *
from plugins.utility_functions.ida_components import *

import psycopg2.extras
import psycopg2
from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT
plugin_dir="""C:\\Users\\Peter\\AppData\\Roaming\\QGIS\\QGIS3\\profiles\\default\\python\\plugins\\"""
dictDB={'pwd' : 'p3t3r' , 'host' : 'localhost','port':'5434', 'user' : 'postgres', 'projectName' : 'test19', 'versionName' : 'a'}

#dictDB=getDBConnectionData(plugin_dir)
conn=dbConnect(dictDB,True)
cur=conn.cursor(cursor_factory = psycopg2.extras.RealDictCursor)
print(cur)

