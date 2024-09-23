from plugins.utility_functions.util import *
import os

class WorkerOpenAPI():
    """ Class to open IDA Doc with API """
    def __init__(self,file_path,plugin_dir):
        #open file in IDA
        self.util=Util_api(plugin_dir)
        self.file_path=file_path.replace('/','\\')
        print(self.util.pid)
        
        connectionTest = self.util.ida_lib.connect_to_ida(b"5945", self.util.pid.encode())
        print(connectionTest)
        try:
            result = self.util.call_ida_api_function(self.util.ida_lib.openDocument, self.file_path.encode('ascii'))
        except:
            print('failed open doc')
            pass
            
class WorkerOpenParRunAPI():
    """ Class to open IDA Doc with API """
    def __init__(self,file_path,plugin_dir,parmRun):
        #open file in IDA
        self.util=Util_api(plugin_dir)
        self.file_path=file_path.replace('/','\\')
        print(self.util.pid)
        
        connectionTest = self.util.ida_lib.connect_to_ida(b"5945", self.util.pid.encode())
        print(connectionTest)
        try:
            building = self.util.call_ida_api_function(self.util.ida_lib.openDocument, self.file_path.encode('ascii'))
            if parmRun=='New Parametric Run':
                script="""((:set name (:call get-unique-component-name "ParmRun_1" [@ :SYSTEM]))
(:set value (:call make-component [@ :SYSTEM] '(macro-object :t parmrun-info :n (:eval name))))
(on-add-component value)
(log-add-object value [@ :SYSTEM])
(if (:call object-p value)
  (:call open-as value 'form)))"""
            else:
                script="""((:set parm_name (:call find "{}" (:call :parmruns [@ :SYSTEM]) :key 'name :test 'equalp))
(open-as parm_name 'form))""".format(parmRun)
            
            print(script)
            script_result=self.util.call_ida_api_function(self.util.ida_lib.runIDAScript, building, script.encode('ascii'))
            print(script_result)
        except:
            pass
            
class WorkerSimulateAPI():
    """ Class to open,simulate, IDA Doc with API """
    def __init__(self,file_path,plugin_dir):
        #open file in IDA
        self.util=Util_api(plugin_dir)
        self.file_path=file_path.replace('/','\\')
        print(self.util.pid)
        
        connectionTest = self.util.ida_lib.connect_to_ida(b"5945", self.util.pid.encode())
        print(connectionTest)
        try:
            #open file
            building = self.util.call_ida_api_function(self.util.ida_lib.openDocument, self.file_path.encode('ascii'))
            
            #run sim
            script="""(ICE-RUN-BUILDING-EX [@ :SYSTEM])"""
            print(script)
            self.util.call_ida_api_function(self.util.ida_lib.runIDAScript, building, script.encode('ascii'))
            print('save doc')
            self.util.call_ida_api_function(self.util.ida_lib.saveDocument, building, self.file_path.encode(), 1)   
        except:
            pass
       

class WorkerRunAutoMooAPI():
    """ Class to open IDA Doc with API """
    def __init__(self,file_path,plugin_dir,parmRun):
        #open file in IDA
        self.util=Util_api(plugin_dir)
        self.file_path=file_path.replace('/','\\')
        print(self.file_path)
        print(self.util.pid)
        # IDA ICE connection test
        connectionTest = self.util.ida_lib.connect_to_ida(b"5945", self.util.pid.encode())
        print(connectionTest)
        try:
            print('**************ParmRunSkopt*****************')
            self.building = self.util.call_ida_api_function(self.util.ida_lib.openDocument, self.file_path.encode('ascii'))
            print(self.building)

            print('save doc')
            self.util.call_ida_api_function(self.util.ida_lib.saveDocument, self.building, self.file_path.encode(), 1)
            
            print('--script---')
            #execute AutoMOO
            script="""((:set parmrun_ [@ "{}"])
(:set parm_name (:call find "{}" (:call :parmruns [@ :SYSTEM]) :key 'name :test 'equalp))
(open-as parm_name 'form)
(parmrun-init-summary parmrun_)
(parmrun-common-check parmrun_ t)
(PARMRUN-SKOPT parmrun_)
)""".format(parmRun,parmRun)
            print(script)
            self.util.call_ida_api_function(self.util.ida_lib.runIDAScript, self.building, script.encode('ascii'))   
      
            print('save doc')
            self.util.call_ida_api_function(self.util.ida_lib.saveDocument, self.building, self.file_path.encode(), 1)

            print('exit')
            #self.util.call_ida_api_function(self.util.ida_lib.runIDAScript, self.building, """(exit-ida)""".encode('ascii'))
            os.system("taskkill /f /im ida-ice.exe")
            #Disconnect
            #print('disconnect')
            #end = self.util.ida_lib.ida_disconnect()
            print('finish')
        except:
            pass
        
            
