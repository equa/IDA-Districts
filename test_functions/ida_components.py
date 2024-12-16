from plugins.utility_functions.ida_components import *
from plugins.utility_functions.files import *


plugin_dir="""C:\\Users\\Peter\\AppData\\Roaming\\QGIS\\QGIS3\\profiles\\default\\python\\plugins\\"""
dictDB={'pwd' : 'p3t3r' , 'host' : 'localhost','port':'5434', 'user' : 'postgres', 'projectName' : 'test17', 'versionName' : 'a'}

dir=plugin_dir+'ida_districts_data_center\\{}\\energy_plant_assettypes\\1_2_Low Temp Heating 1 Supply & 1 Return\\'.format(dictDB['projectName'])
fname=dir+'1_2_Low Temp Heating 1 Supply & 1 Return.idm'

print(fname)
data=readFileToString(fname)

#print(getIDAListComponents(data))

print(getIDAListComponents(data))
data_idm=propertyListCompsIDM(getIDAListComponents(data))
print(data_idm)

         
print(fname)         
writePropertyListIDMToFile(data_idm,dir,fname)


