from plugins.utility_functions.util import *
from plugins.utility_functions.topology import *
from plugins.utility_functions.files import *
import os
import numpy as np
from PyQt5.QtCore import QObject, pyqtSlot, pyqtSignal,QRunnable
from qgis.utils import iface
    
def show_error_message(message):
    # Show the error message in a messageBar
    iface.messageBar().pushMessage("Error", message, level=Qgis.Critical)

class APIPlotinvokedFeatureSignals(QObject):
    progress=pyqtSignal(int)
    error=pyqtSignal(str)
    dataProcessed=pyqtSignal(list)
    plot=pyqtSignal(bool)
    plot_total=pyqtSignal(list)
    
class WorkerPlotInvokedFeatureLoad(QRunnable):
    """Worker thread
    Inherits from QRunnable to handle worker thread setup, signals and wrap-up."""
    def __init__(self,*args,**kwargs):
        super().__init__()
        self.args=args
        print(args)
        self.signals=APIPlotinvokedFeatureSignals()
        self.dictDB=kwargs['dictDB']
        self.dlg=kwargs['dlg']
        self.type=kwargs['type']
        self.conn=""
        self.cur=""
        self.plugin_dir=kwargs['plugin_dir']
        self.conn = dbConnect(self.dictDB,True)
        self.rows=kwargs['rows']
        if self.conn:
            self.cur=self.conn.cursor(cursor_factory = psycopg2.extras.RealDictCursor)
            
    @pyqtSlot()
    def run(self):
        print('Generate network topology')
        self.progress_value=1
        self.signals.progress.emit(self.progress_value)
       
        count=0
        for idx in self.rows:
            id=self.dlg.tableWidget_customer.item(idx,0).text()
            connValues=getConnsValues(getConnBundleByFeature(self.type,id,self.cur,self.dictDB),self.cur)
            print(connValues)
            conn_type_seq=set([x['conn_type_seq'] for x in connValues])
            print(conn_type_seq)
            for seq in conn_type_seq:
                file_path=self.plugin_dir+"\\network_models\\{}\\{}\\invoked_{}s\\{}_{}\\{}_{}\\Connection type sequence_{}.prn".format(self.dictDB['projectName'],self.dictDB['versionName'],self.type,self.type.capitalize(),id,self.type,id,seq)  
                print(file_path)
                if os.path.exists(file_path):
                    legend=self.type.capitalize()+':'+id

                    print(file_path)
                    filedata=readFileToList(file_path)

                    #print(filedata)
                    i=0
                    time=[]
                    power=[]
                    try:
                        for line in filedata:
                            data=line.strip().split()
                            if i==0:
                                power_col=data.index('power')-1
                            else:
                                power.append([float(data[0]),float(data[power_col])])
                                if i==1:
                                    energy=[[float(data[0]),0]]
                                else:
                                    energy.append([float(data[0]),energy[-1][1]+(float(data[0])-energy[-1][0])*float(data[power_col])/1000]) #kWh
                            i+=1    
                    except Exception as e:
                        print(f'error: {e}')
                        self.signals.error.emit("Load in {}:{} is not found!".format(self.type.capitalize(),id))
                    
                    power=np.array(power)  
                    energy=np.array(energy)  
                    time=np.arange(0,power[-1,0],0.1)


                    #linear interpolation
                    valuesPowerInt = np.interp(time, power[:,0], power[:,1])
                    valuesEnergyInt = np.interp(time, power[:,0], energy[:,1])
                    
                    if count==0:
                        power_sum=valuesPowerInt
                        energy_sum=valuesEnergyInt
                    else:
                        try:
                            power_sum=np.add(power_sum,valuesPowerInt)
                            energy_sum=np.add(energy_sum,valuesEnergyInt)
                        except:
                            self.signals.error.emit("Different simulation periods are used!")

                    #plotting
                    self.signals.dataProcessed.emit([{'time':time,'data':valuesPowerInt,'label':'Customer ID='+str(id)},{'time':time,'data':valuesEnergyInt,'label':'Customer ID='+str(id)}])
                    count+=1
                    
                    self.progress_value=int(count/len(self.rows)*98)
                    self.signals.progress.emit(self.progress_value)
                           
        self.signals.plot.emit(True) 
        if count>1:
            self.signals.plot_total.emit([{'time':time,'data':power_sum},{'time':time,'data':energy_sum}]) 
                
        self.signals.progress.emit(100)
        
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
                    print('+++++++++opening+++++++++++')
                    building = self.util.call_ida_api_function(self.util.ida_lib.openDocument, file_path.encode('ascii'))
                    print('+++++++++opened+++++++++++')
                    #run sim
                    script="""((ICE-RUN-BUILDING-EX [@ :SYSTEM])
(save-document [@ :SYSTEM] "{}" nil)
(close (:call find-view [@ :SYSTEM] 'schema t)))""".format(file_path.replace('\\','\\\\'))
                    print(script)
                    self.result=self.util.call_ida_api_function(self.util.ida_lib.runIDAScript, building, script.encode('ascii'))
                    #print('save doc')
                    #self.util.call_ida_api_function(self.util.ida_lib.saveDocument, building, file_path.encode('ascii'), 1)   
                    print('+++++++++saved++++++++++++++++')
                    self.progress_value=int(counter/len(self.file_pathes)*98)+1
                    print(self.progress_value)
                    self.signals.progress.emit(self.progress_value)
                    if self.result:
                        self.signals.status.emit('Simulation finished')
                    else:
                        self.signals.status.emit('Simulation failed')
                else:
                    self.signals.error.emit("Sim model does not exist!")
            self.signals.progress.emit(100)
            print('simulation-finished')
        except:
            self.signals.progress.emit(0)
            self.signals.error.emit("Failed to open the feature: {}!".format(file_path))

class WorkerSimulateAPI(QRunnable):
    """ Class to open,simulate, IDA Doc with API """            
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
        self.building={}
        try:
            if os.path.exists(self.file_path):
                print(self.file_path)
                #open file
                print('+++++++++opening+++++++++++')
                self.building = self.util.call_ida_api_function(self.util.ida_lib.openDocument, self.file_path.encode('ascii'))
                print('+++++++++opened+++++++++++')
                #run sim
                script="""((ICE-RUN-BUILDING-EX [@ :SYSTEM])
(save-document [@ :SYSTEM] "{}" nil)
(close (:call find-view [@ :SYSTEM] 'schema t)))""".format(self.file_path.replace('\\','\\\\'))
                print(script)
                self.result=self.util.call_ida_api_function(self.util.ida_lib.runIDAScript, self.building, script.encode('ascii'))
                print(self.result)
                if self.result:
                    self.signals.status.emit('Simulation finished')
                else:
                    self.signals.status.emit('Simulation failed')
            else:
                self.signals.error.emit("Sim model does not exist!")
            print('++++simulation-finished++++')
        except:
            self.signals.error.emit("Failed to open the feature: {}!".format(self.file_path))
            
class APISignals(QObject):
    progress=pyqtSignal(int)
    error=pyqtSignal(str)
    status=pyqtSignal(str)
    finished =pyqtSignal(str)
    
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
        
            
