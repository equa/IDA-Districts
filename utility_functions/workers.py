from plugins.utility_functions.util import *
import os
from PyQt5.QtCore import QObject, pyqtSlot, pyqtSignal,QRunnable
    
class WorkerSimulateFilesAPI(QRunnable):
    """ Class to open,simulate, IDA Doc with API """            
    def __init__(self,file_pathes,plugin_dir):
        super().__init__()
        self.file_pathes=file_pathes
        self.plugin_dir=plugin_dir
        self.signals=APISignals()
            
    @pyqtSlot()
    def run(self):
        #open file in IDA
        self.signals.progress.emit(1)
        self.util=Util_api(self.plugin_dir)

        print(self.util.pid)
        
        connectionTest = self.util.ida_lib.connect_to_ida(b"5945", self.util.pid.encode())
        print(connectionTest)
        file_path=""
        try:
            for counter,file_path in enumerate(self.file_pathes,1):
                if os.path.exists(file_path):
                    print(file_path)
                    #open file
                    building = self.util.call_ida_api_function(self.util.ida_lib.openDocument, file_path.encode('ascii'))
                    print('opened')
                    #run sim
                    script="""((ICE-RUN-BUILDING-EX [@ :SYSTEM])
(save-document [@ :SYSTEM] "{}" nil)
(close (:call find-view [@ :SYSTEM] 'schema t)))""".format(file_path.replace('\\','\\\\'))
                    print(script)
                    self.util.call_ida_api_function(self.util.ida_lib.runIDAScript, building, script.encode('ascii'))
                    #print('save doc')
                    #self.util.call_ida_api_function(self.util.ida_lib.saveDocument, building, file_path.encode('ascii'), 1)   
                    print('saved')
                    self.progress_value=int(counter/len(self.file_pathes)*98)+1
                    print(self.progress_value)
                    self.signals.progress.emit(self.progress_value)
                else:
                    self.signals.error.emit("Sim model does not exist!")
            self.signals.progress.emit(100)
            print('simulation-finished')
        except:
            self.signals.progress.emit(0)
            self.signals.error.emit("Failed to open the feature: {}!".format(file_path))
            
class APISignals(QObject):
    progress=pyqtSignal(int)
    error=pyqtSignal(str)
    
class WorkerOpenAPI(QRunnable):
    """Worker thread
    Inherits from QRunnable to handle worker thread setup, signals and wrap-up."""
    def __init__(self,file_path,plugin_dir):
        super().__init__()
        self.file_path=file_path.replace('/','\\')
        self.plugin_dir=plugin_dir
        self.signals=APISignals()
            
    @pyqtSlot()
    def run(self):
        #open file in IDA
        self.signals.progress.emit(1)
        self.util=Util_api(self.plugin_dir)

        print(self.util.pid)
        
        connectionTest = self.util.ida_lib.connect_to_ida(b"5945", self.util.pid.encode())
        print(connectionTest)
        try:
            result = self.util.call_ida_api_function(self.util.ida_lib.openDocument, self.file_path.encode('ascii'))
            self.signals.progress.emit(100)
        except:
            self.signals.progress.emit(0)
            self.signals.error.emit("Failed to open the feature!")     
            
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
        
            
