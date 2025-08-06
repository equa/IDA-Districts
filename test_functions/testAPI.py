#from plugins.utility_functions.workerOpenAPI import *
from multiprocessing import Process
plugin_dir='C:\\Users\\Peter\\AppData\\Roaming\\QGIS\\QGIS3\\profiles\\default\\python\\plugins\\ida_districts_modeling_simulation'

from plugins.utility_functions.util import *
import os

class WorkerRunAutoMooAPI():
    """ Class to open IDA Doc with API """
    def __init__(self,file_path,plugin_dir):
        #open file in IDA
        self.util=Util_api(plugin_dir)
        self.file_path=file_path.replace('/','\\')
        #print(self.file_path)
        #print(self.util.pid)
        # IDA ICE connection test
        connectionTest = self.util.ida_lib.connect_to_ida(b"5945", self.util.pid.encode())
        #print(connectionTest)
        try:
            #print('**************ParmRunSkopt*****************')
            self.building = self.util.call_ida_api_function(self.util.ida_lib.openDocument, self.file_path.encode('utf-8'))

                
            #print('--script---')
            #execute AutoMOO
            script="""(PARMRUN-SKOPT [@ :SYSTEM "ParmRun_annualCallib"])"""
            #print(script)
            #self.util.call_ida_api_function(self.util.ida_lib.runIDAScript, self.building, script.encode('utf-8'))   
      
            #print('save doc')
            self.util.call_ida_api_function(self.util.ida_lib.saveDocument, self.building, self.file_path.encode(), 1)

            #print('exit')
            #self.util.call_ida_api_function(self.util.ida_lib.runIDAScript, self.building, """(exit-ida)""".encode('utf-8'))
            os.system("taskkill /f /im ida-ice.exe")
            #Disconnect
            #print('disconnect')
            #end = self.util.ida_lib.ida_disconnect()
            #print('finish')
        except:
            pass
        
        
            


process = Process(target=WorkerRunAutoMooAPI(plugin_dir+'\\network_models\\test1007\\a\\invoked_customers\\Customer_1.idm',plugin_dir))

