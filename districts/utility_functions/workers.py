from qgis.PyQt.QtCore import QSettings
from .util import *
from .topology import *
from .files import *
from .utility import *
from .db import *
import os
import numpy as np
from qgis.PyQt.QtCore import QObject, pyqtSlot, pyqtSignal,QRunnable
from qgis.utils import iface
import subprocess
import time
from qgis.core import QgsProcessingUtils
import tempfile
import zipfile
from pathlib import Path



    
def show_error_message(message):
    # Show the error message in a messageBar
    iface.messageBar().pushMessage("Error", message, level=Qgis.Critical)

class APIPlotinvokedFeatureSignals(QObject):
    progress=pyqtSignal(int)
    error=pyqtSignal(str)
    dataProcessed=pyqtSignal(list)
    plot=pyqtSignal(bool)
    plot_total=pyqtSignal(list)

class WorkerLoadVersion(QRunnable):
    """Worker thread
    Inherits from QRunnable to handle worker thread setup, signals and wrap-up."""
    def __init__(self,*args,**kwargs):
        super().__init__()
        self.args=args
        #print(args)
        self.signals=APISignals()
        self.config=kwargs['config']
        self.cur=kwargs['cur']
        self.dlg=kwargs['dlg']

    @pyqtSlot()
    def run(self):
        try:
            #print('Load project version')
            self.signals.progress.emit(10)  
            #print(self.config['versionName'])
            
            #version handling            
            
            #update triggers: delete last loaded versions triggers if exists and create new triggers
            dropDBTriggers(self.cur,self.config,lastLoad=True)
            dropDBTriggers(self.cur,self.config)
            insertDBTriggers(self.cur,self.config)
  
            self.config['lastVersionName']=self.config['versionName']            
            self.signals.progress.emit(100)            
        except Exception as e:
            #print(f'error: {e}')
            self.signals.error.emit("Loading version failed!") 
        finally:
            write_plugin_settings(self.config)
            self.signals.finished.emit('Finished worker load version')     

            
class WorkerImportProject(QRunnable):
    """Worker thread
    Inherits from QRunnable to handle worker thread setup, signals and wrap-up."""
    def __init__(self,*args,**kwargs):
        super().__init__()
        self.args=args
        #print(kwargs)
        self.signals=APISignals()
        self.config=kwargs['config']
        self.password=kwargs['password']
        self.username=kwargs['username']
        self.filename=kwargs['filename']
        self.cur_postgres=kwargs['cur']
        self.plugin_dir=kwargs['plugin_dir']
        self.dlg=kwargs['dlg']
        self.filter_folders=kwargs['filter_folders']
        self.filter_extensions=kwargs['filter_extensions']
        self.no_db_results=kwargs['no_db_results']
        self.project_name=kwargs['project_name']
        self.projectNames=kwargs['projectNames']
        self.versionNames=kwargs['versionNames']
        if self.dlg:
            self.dlg.process_running=True
        
    @pyqtSlot()
    def run(self):
        #print('Import project')
        #print(self.project_name)
        self.signals.progress.emit(1)            

        if zipfile.is_zipfile(self.filename):
            #print("Valid ZIP file")
            name = Path(self.filename).stem
            #unzip
            temp_folder=districtsModelerTempDir()
            src_dir=temp_folder
            if os.path.exists(temp_folder+name):
                rmtree_long_path(temp_folder+name)
            createDir(temp_folder,name)
            temp_folder+=name+'\\'
            
            with zipfile.ZipFile(self.filename, 'r') as zip_ref:
                zip_ref.extractall(temp_folder)
        elif self.filename.split('\\')[-1]=='low_temperature_network' and os.path.exists(self.config['pathDistricts']+'Samples\districts\low_temperature_network\low_temperature_network'):
            #print("Not a ZIP file")
            name=self.filename.split('\\')[-1]
            src_dir='\\'.join(self.filename.split('\\')[0:-1])+'\\'
            src_dir=src_dir+name+'\\'+name+'\\'
        else:
            #print("Not a ZIP file")
            name=self.filename.split('\\')[-1]
            src_dir='\\'.join(self.filename.split('\\')[0:-1])+'\\'

        src_dir=src_dir+name+'\\' 

        #print(src_dir)
        #print(self.config)
        #print(name)
        
        self.signals.progress.emit(15)            

        #get project name
        db_info=''
        if os.path.exists(src_dir+'\\DB_info.txt'):
            with open(src_dir+'\\DB_info.txt', "r") as myfile:   
                for line in myfile:        
                    db_info+=line
            db_info=strToDict(db_info)
        else:
            db_info={'projectName': self.project_name}                
        #print(db_info)
        
        #check if project already exists
        if db_info['projectName'] not in self.projectNames:
            #print('project does not exist') 

            target_dir=self.config['pathProjects']+(self.project_name if self.project_name else name)
            #print(target_dir)
            os.makedirs(target_dir, exist_ok=True)

            self.signals.progress.emit(20)
            try:
                copy_tree_filter_extensions_and_folders(src_dir+'customer_templates',target_dir+'\\customer_templates',signals=self.signals,exclude_extensions=self.filter_extensions)
                copy_tree_filter_extensions_and_folders(src_dir+'energy_plant_templates',target_dir+'\\energy_plant_templates',signals=self.signals,exclude_extensions=self.filter_extensions)
                copy_tree_filter_extensions_and_folders(src_dir+'climate',target_dir+'\\climate',signals=self.signals,exclude_extensions=self.filter_extensions)
                copy_tree_filter_extensions_and_folders(src_dir+'supervisory_control',target_dir+'\\supervisory_control',signals=self.signals,exclude_extensions=self.filter_extensions)

                replace_in_folder(
                    root_folder=target_dir,
                    old_string='$plugins_path$',
                    new_string=self.plugin_dir.replace('\\','\\\\'),
                    file_extensions=['.idm'],
                    exclude_filenames=[]
                )

                replace_in_folder(
                    root_folder=target_dir,
                    old_string='$districts_path$',
                    new_string=self.config['pathDistricts'].replace('\\','\\\\'),
                    file_extensions=['.idm'],
                    exclude_filenames=[]
                )
                self.signals.progress.emit(30)
            except Exception as e:
                #print(f'error: {e}')
                self.signals.error.emit("Data center copying failed: "+ str(e))
                return False
            try:
                #print('--versions directory--')
                if os.path.exists(src_dir+'versions'):
                    copy_tree_filter_extensions_and_folders(src_dir+'versions',target_dir+'\\versions\\',signals=self.signals,exclude_extensions=self.filter_extensions,exclude_folders=self.filter_folders)
                self.signals.progress.emit(50)
            except Exception as e:
                #print(f'error: {e}')
                self.signals.error.emit("Modelling data copying failed!")
                return False
                
            if not os.path.exists(target_dir+'\\versions'):
                createDir(target_dir,'versions')
                
            try:
                copyFile(src_dir+'configProject.txt',target_dir,target_dir+'\\configProject.txt')
                copyFile(src_dir+'requestedOutputs.txt',target_dir,target_dir+'\\requestedOutputs.txt')
                self.signals.progress.emit(70)
            except Exception as e:
                #print(f'error: {e}')
                self.signals.error.emit("Copying data failed!")
                return False
            try:
                copyFile(src_dir+'layersConfig.txt',target_dir,target_dir+'\\layersConfig.txt')
            except Exception as e:
                pass
            
            sql = """CREATE database {};""".format(db_info['projectName']) # nosec B608
            self.cur_postgres.execute(sql)
            self.config['projectName']=db_info['projectName']
            self.conn=dbConnectProvidePwdUser(self.config,self.signals.error,self.password,self.username)
            if not self.conn:
                return False
            self.cur = self.conn.cursor(cursor_factory = psycopg2.extras.RealDictCursor)   
            sql="""CREATE SCHEMA IF NOT EXISTS temp;
CREATE SCHEMA IF NOT EXISTS topology;
CREATE EXTENSION IF NOT EXISTS dblink WITH SCHEMA public;
CREATE EXTENSION IF NOT EXISTS postgis WITH SCHEMA public;
CREATE EXTENSION IF NOT EXISTS pgrouting WITH SCHEMA public;
CREATE EXTENSION IF NOT EXISTS postgis_raster WITH SCHEMA public;
CREATE EXTENSION IF NOT EXISTS postgis_topology WITH SCHEMA topology;"""
            self.cur.execute(sql)
            self.signals.progress.emit(71)
            if self.project_name:
                sql='\n'.join(["CREATE SCHEMA IF NOT EXISTS {};".format(version) for version in self.versionNames]) # nosec B608
                #print(sql)
                if sql:
                    self.cur.execute(sql)
                self.signals.progress.emit(73)
                
                #create tables in new schema
                #project tables
                filedata=readFileToString(self.plugin_dir+"\\DB_projectTablesDefault.txt") # nosec B608
                #print(filedata)
                self.cur.execute(filedata)
                
                if self.versionNames:
                    #version tables
                    self.projectConfig=loadProjectConfig(self.config,project_name=self.project_name,signals=self.signals)  
                    filedata=readFileToString(self.plugin_dir+"\\DB_versionTablesDefault.txt")
                    filedata = filedata.replace("$srid$", self.projectConfig['srid'])
                    filedata = filedata.replace("$plugins_path$", self.plugin_dir)
                    for version in self.versionNames:
                        newdata = filedata.replace("$versionName$", self.config['versionName'])   
                        #print(newdata)
                        self.cur.execute(newdata)
            
            self.signals.progress.emit(75)
            if name =='heating_network':
                #print('-----heating_network------')
                sql="""ALTER TABLE "base1".customers ADD COLUMN load_w NUMERIC;
ALTER TABLE "base1".customers ADD COLUMN gfa_m2 NUMERIC;"""
                self.cur.execute(sql)
            self.signals.progress.emit(76)
                
            temp_dir = QgsProcessingUtils.tempFolder()+'\\'
            #create tables in new schema
            if name=='low_temperature_network' and os.path.exists(self.config['pathDistricts']+'Samples\districts\low_temperature_network\low_temperature_network'):
                src_dir='\\'.join([i for i in src_dir.split('\\') if i][:-1])+'\\'
            filedata=""
            if os.path.exists(src_dir+('db_tables.sql' if self.project_name else name+'.sql')):
                with open(src_dir+('db_tables.sql' if self.project_name else name+'.sql'), "r") as myfile:
                    for line in myfile:
                        filedata=filedata+line
                newdata = filedata.replace("$plugins_path$", os.path.normpath(self.plugin_dir).replace('\\','\\\\'))
                newdata = filedata.replace("$districts_path$", os.path.normpath(self.config['pathDistricts']).replace('\\','\\\\'))
                
                with open(temp_dir+('db_tables_.sql' if self.project_name else name+'_.sql'),'w') as myfile:
                    myfile.write(newdata)   
            
            self.signals.progress.emit(77)
            env = os.environ.copy()
            env["PGPASSWORD"] = self.password

            dbname = sanitize_pg_identifier(db_info['projectName'])
            
            cmd = [
                f"{self.config['pathPostgresql']}bin\\psql",
                f"--dbname=postgresql://{self.username}@{self.config['host']}:{self.config['port']}/{dbname}",
                "-f",
                temp_dir + ('db_tables_.sql' if self.project_name else name + '_.sql')
            ]

            #print(cmd)
            subprocess.call(cmd, env=env)
            
            self.signals.progress.emit(79)
            filedata=readFileToString(self.plugin_dir+"\\SQL_scripts.txt") # nosec B608
            self.cur.execute(filedata)
            self.signals.progress.emit(80)            
            if self.project_name and not self.no_db_results:
                cmd = [
                    f"{self.config['pathPostgresql']}bin\\psql",
                    f"--dbname=postgresql://{self.username}@{self.config['host']}:{self.config['port']}/{dbname}",
                    "-f",
                    temp_dir + "db_results.sql"
                ]

                #print(cmd)  # optional zum Debuggen

                subprocess.call(cmd, env=env)
            self.conn.close()

        else:
            self.signals.error.emit("Project already exists in DB!")
            self.signals.progress.emit(0)           
            return False
            
        try:
            pass
        except Exception as e:
            pass
            #print(e)
        self.signals.progress.emit(100)
        self.signals.finished.emit(db_info['projectName'])
        
class WorkerExportProject(QRunnable):
    """Worker thread
    Inherits from QRunnable to handle worker thread setup, signals and wrap-up."""
    def __init__(self,*args,**kwargs):
        super().__init__()
        self.args=args
        #print(args)
        self.signals=APISignals()
        self.config=kwargs['config']
        self.plugin_dir=kwargs['plugin_dir']
        self.password=kwargs['password']
        self.username=kwargs['username']
        self.filename=kwargs['filename']
        self.filter_folders=kwargs['filter_folders']
        self.filter_extensions=kwargs['filter_extensions']
        #print(self.filter_extensions)
        #print(self.filter_folders)
        self.no_db_results=kwargs['no_db_results']
        self.conn=""
        self.cur=""
        self.conn = dbConnect(self.config,True)
        if self.conn:
            self.cur=self.conn.cursor(cursor_factory = psycopg2.extras.RealDictCursor)
            
    @pyqtSlot()
    def run(self):
        #print('Export project worker')
        self.signals.progress.emit(1)
        
        #print(self.filename)
        dir='\\'.join(self.filename.split('\\')[0:-1])+'\\'
        name=self.filename.split('\\')[-1].split('.')[0]
        #print(dir)
        #print(name)
        createDir(dir,name)
        dir=dir+name

        temp_folder=districtsModelerTempDir()
        createDir(temp_folder,name,delete=True)
        temp_folder+=name+'\\'
        #print(temp_folder)
                    
        # Ensure the directory exists, create it if necessary
        sql_path = temp_folder+f"\\{name}.sql"

        os.makedirs(os.path.dirname(sql_path), exist_ok=True)

        cmd = [
            os.path.join(self.config['pathPostgresql'],"bin\\pg_dump"),  # Path to pg_dump
            "--dbname=postgresql://{}:{}@{}:{}/{}".format(self.username,self.password ,self.config['host'],self.config['port'],self.config['projectName'])
        ]
        if self.no_db_results:
            cmd.append("--exclude-table-data=*.customer_s*")
            cmd.append("--exclude-table-data=*.line_s*")
            cmd.append("--exclude-table-data=*.energy_plant_s*")            
            cmd.append("--exclude-table-data=*.customer_m_*")
            cmd.append("--exclude-table-data=*.line_m*")
            cmd.append("--exclude-table-data=*.energy_plant_m*")
        #print(cmd)
        # Output file redirection (using stdout to redirect the output to a file)
        with open(sql_path, "w") as output_file:
            subprocess.call(cmd, stdout=output_file)        
            
        self.signals.progress.emit(25)

        try:
            copy_tree_filter_extensions_and_folders(self.config['pathProjects']+self.config['projectName'], temp_folder,self.signals,self.filter_extensions,self.filter_folders)
        except Exception as e:
            #print(f'error: {e}')
            self.signals.error.emit("Project handling files export failed!") 
        self.signals.progress.emit(50)  

        db_info={'projectName': name}
        if os.path.exists(temp_folder):
            with open(temp_folder+'\\DB_info.txt', "w") as myfile:   
                myfile.write(str(db_info))
                
        # Check if the folder exists and delete it
        if os.path.exists(dir) and os.path.isdir(dir):
            rmtree_long_path(dir) 
            
        #write zip to target folder
        shutil.make_archive(
            dir,            # source folder without .zip
            "zip",          # format
            temp_folder     # source folder
        )

        self.signals.progress.emit(100)
        self.signals.finished.emit(self.filename)
    
class WorkerPlotInvokedFeatureLoad(QRunnable):
    """Worker thread
    Inherits from QRunnable to handle worker thread setup, signals and wrap-up."""
    def __init__(self,*args,**kwargs):
        super().__init__()
        self.args=args
        #print('--WorkerPlotInvokedFeatureLoad--')
        self.signals=APIPlotinvokedFeatureSignals()
        self.config=kwargs['config']
        #print(self.config)
        self.dlg=kwargs['dlg']
        self.type=kwargs['type']
        self.conn=""
        self.cur=""
        self.conn = dbConnect(self.config,True)
        self.rows=kwargs['rows']
        if self.conn:
            self.cur=self.conn.cursor(cursor_factory = psycopg2.extras.RealDictCursor)
            
    #dublicate code
    def getConnBundleByFeature(self,feature_type,feature_id,cur,config):
        sql="""SELECT c_t.conn_bundle_type 
        FROM "{}".{} f, {} c_t 
        WHERE f.id={} AND c_t.template=f.template;""".format(config['versionName'],feature_type+'s' if type(feature_type)==str else getTypeNameById(feature_type),getTemplateNameById(int(getTypeIdByName(feature_type))) if type(feature_type)==str else getTemplateNameById(feature_type),feature_id) # nosec B608
        #print(sql)
        cur.execute(sql)
        return cur.fetchone()['conn_bundle_type']
        
    #dublicate code
    def getConnsValues(self,bundle,cur):
        sql="""SELECT b_t_conns.conn_bundle_type_id, b_t_conns.sequence AS conn_type_seq, b_t_conns.conn_type_id, conn_t_conns.sequence AS conn_seq, conns.temp,conns.p, conns.mdot,conns.type, conns.id AS conn_id, conns.p_ctrl
        FROM connections conns, bundle_type_conns b_t_conns, connection_type_connections conn_t_conns
        WHERE b_t_conns.conn_bundle_type_id = {} AND conn_t_conns.connection_id=conns.id AND b_t_conns.conn_type_id=conn_t_conns.connection_type_id
        ORDER BY b_t_conns.sequence, conn_t_conns.sequence;""".format(bundle) # nosec B608
        cur.execute(sql)
        return cur.fetchall()
            
    @pyqtSlot()
    def run(self):
        self.progress_value=1
        self.signals.progress.emit(self.progress_value)
        try:
            count=0
            for idx in self.rows:
                id=self.dlg.tableWidget_customer.item(idx,0).text()
                connValues=self.getConnsValues(self.getConnBundleByFeature(self.type,id,self.cur,self.config),self.cur)
                conn_type_seq=set([x['conn_type_seq'] for x in connValues])
                for seq in conn_type_seq:
                    file_path=self.config['pathProjects']+"{}\\versions\\{}\\invoked_{}s\\{}_{}\\{}_{}\\Connection type sequence_{}.prn".format(self.config['projectName'],self.config['versionName'],self.type,self.type.capitalize(),id,self.type,id,seq)  
                    #print(file_path)
                    if os.path.exists(file_path):
                        legend=self.type.capitalize()+':'+id

                        #print(file_path)
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
                            #print(f'error: {e}')
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
        except Exception as e:
            #print(e)
            pass
                           
        self.signals.plot.emit(True) 
        if count>1:
            self.signals.plot_total.emit([{'time':time,'data':power_sum},{'time':time,'data':energy_sum}]) 
                
        self.signals.progress.emit(100)
        
class WorkerSimulateFilesAPI(QRunnable):
    """ Class to open,simulate, IDA Doc with API """            
    def __init__(self,file_pathes,plugin_dir,config):
        super().__init__()
        self.file_pathes=file_pathes
        self.plugin_dir=plugin_dir
        self.config=config
        self.signals=APISignals()
            
    @pyqtSlot()
    def run(self):
        #open file in IDA
        self.signals.progress.emit(1)
        self.util=Util_api(self.plugin_dir,self.config)

        #print(self.util.pid)
        
        connectionTest = self.util.ida_lib.connect_to_ida(b"5945", self.util.pid.encode())
        #print(connectionTest)
        file_path=""
        try:
            for counter,file_path in enumerate(self.file_pathes,1):
                if os.path.exists(file_path):
                    #print(file_path)
                    #open file
                    #print('+++++++++opening+++++++++++')
                    building = self.util.call_ida_api_function(self.util.ida_lib.openDocument, file_path.encode('utf-8'))
                    #print('+++++++++opened+++++++++++')
                    #run sim
                    script="""((RUN-SIMULATION [@ :SYSTEM])
(save-document [@ :SYSTEM] "{}" nil)
(close (:call find-view [@ :SYSTEM] 'schema t)))""".format(file_path.replace('\\','\\\\'))
                    #print(script)
                    self.result=self.util.call_ida_api_function(self.util.ida_lib.runIDAScript, building, script.encode('utf-8'))
                    #print('save doc')
                    #self.util.call_ida_api_function(self.util.ida_lib.saveDocument, building, file_path.encode('utf-8'), 1)   
                    #print('+++++++++saved++++++++++++++++')
                    self.progress_value=int(counter/len(self.file_pathes)*98)+1
                    #print(self.progress_value)
                    self.signals.progress.emit(self.progress_value)
                    if self.result:
                        self.signals.status.emit('Simulation finished')
                    else:
                        self.signals.status.emit('Simulation failed')
                else:
                    self.signals.error.emit("Sim model does not exist!")
            self.signals.progress.emit(100)
            #print('simulation-finished')
        except:
            self.signals.progress.emit(0)
            self.signals.error.emit("Failed to open the feature: {}!".format(file_path))

class WorkerSimulateAPI(QRunnable):
    """ Class to open,simulate, IDA Doc with API """            
    def __init__(self,file_path,plugin_dir,config):
        super().__init__()
        self.file_path=file_path.replace('/','\\')
        self.plugin_dir=plugin_dir
        self.config=config
        self.signals=APISignals()
            
    @pyqtSlot()
    def run(self):
        #open file in IDA
        self.signals.progress.emit(1)
        self.util=Util_api(self.plugin_dir,self.config)

        #print(self.util.pid)
        
        connectionTest = self.util.ida_lib.connect_to_ida(b"5945", self.util.pid.encode())
        #print(connectionTest)
        self.building={}
        try:
            if os.path.exists(self.file_path):
                #print(self.file_path)
                #open file
                #print('+++++++++opening+++++++++++')
                self.building = self.util.call_ida_api_function(self.util.ida_lib.openDocument, self.file_path.encode('utf-8'))
                #print('+++++++++opened+++++++++++')
                #run sim
                script="""((RUN-SIMULATION [@ :SYSTEM])
(save-document [@ :SYSTEM] "{}" nil)
(close (:call find-view [@ :SYSTEM] 'schema t)))""".format(self.file_path.replace('\\','\\\\'))
                #print(script)
                self.result=self.util.call_ida_api_function(self.util.ida_lib.runIDAScript, self.building, script.encode('utf-8'))
                #print(self.result)
                if self.result:
                    self.signals.status.emit('Simulation finished')
                else:
                    self.signals.status.emit('Simulation failed')
            else:
                self.signals.error.emit("Sim model does not exist!")
            #print('++++simulation-finished++++')
        except:
            self.signals.error.emit("Failed to open the feature: {}!".format(self.file_path))
        self.signals.finished.emit("finished")

            
class APISignals(QObject):
    progress=pyqtSignal(int)
    error=pyqtSignal(str)
    status=pyqtSignal(str)
    finished =pyqtSignal(str)
    
class APISignals2(QObject):
    progress=pyqtSignal(int)
    error=pyqtSignal(str)
    status=pyqtSignal(str)
    finished =pyqtSignal(str,object)

class APISignals3Args(QObject):
    progress=pyqtSignal(int)
    error=pyqtSignal(str)
    status=pyqtSignal(str)
    finished =pyqtSignal(str,object,object)
    
class WorkerOpenAPI(QRunnable):
    """Worker thread
    Inherits from QRunnable to handle worker thread setup, signals and wrap-up."""
    def __init__(self,file_path,plugin_dir,config,submodel='1'):
        super().__init__()
        self.file_path=file_path.replace('/','\\')
        self.plugin_dir=plugin_dir
        self.config=config
        self.signals=APISignals()
        self.submodel=submodel
            
    @pyqtSlot()
    def run(self):
        #open file in IDA
        #print('+++++++++++++++++++open Doc++++++++++++++++')

        self.signals.progress.emit(1)
        self.util=Util_api(self.plugin_dir,self.config,submodel=self.submodel)

        #print(self.util.pid)
        
        connectionTest = self.util.ida_lib.connect_to_ida(b"5945", self.util.pid.encode())
        #print(connectionTest)
        try:
            result = self.util.call_ida_api_function(self.util.ida_lib.openDocument, self.file_path.encode('utf-8'))
            #print('++finished++')
            self.signals.progress.emit(100)
        except:
            self.signals.progress.emit(0)
            self.signals.error.emit("Failed to open the feature!")  
            
class WorkerOpenModelCmd(QRunnable):
    """Worker thread
    Inherits from QRunnable to handle worker thread setup, signals and wrap-up."""
    def __init__(self,file_path,config,submodel='1'):
        super().__init__()
        self.file_path=file_path.replace('/','\\')
        self.signals=APISignals()
        self.submodel=submodel
        self.config=config
            
    @pyqtSlot()
    def run(self):
        #open file in IDA
        self.signals.progress.emit(1)

        try:
            cmd = [
                f"{self.config['pathDistricts']}bin\\ida-districts.exe",
                f"{self.config['pathDistricts']}bin\\ida.img",
                "-C",
                f"ida_{self.submodel}_{time.strftime('%m%d%H%M%S', time.localtime())}",
                "-G1",
                "-O",
                self.file_path
            ]

            result = subprocess.run(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True
            )

            if result.returncode==0:
                self.signals.progress.emit(100)
                self.signals.finished.emit('IDA Districts model updated successfully!')
            else:
                self.signals.progress.emit(0)
        except Exception as e:
            self.signals.progress.emit(0)
            self.signals.error.emit("Failed to open the feature!: "+ str(e))  
            
class WorkerOpenRunScriptAPI(QRunnable):
    """Worker thread
    Inherits from QRunnable to handle worker thread setup, signals and wrap-up."""
    def __init__(self,file_path,plugin_dir,config,script,exit_ida=False,finished_fn=False,finished_fn_args=None):
        super().__init__()
        self.file_path=file_path.replace('/','\\')
        self.plugin_dir=plugin_dir
        self.config=config
        self.signals=APISignals()
        self.script=script
        self.exit_ida=exit_ida
        self.finished_fn=finished_fn
        self.finished_fn_args=finished_fn_args
            
    @pyqtSlot()
    def run(self):
        #open file in IDA
        self.signals.progress.emit(1)
        self.util=Util_api(self.plugin_dir,self.config)

        #print(self.util.pid)
        
        connectionTest = self.util.ida_lib.connect_to_ida(b"5945", self.util.pid.encode())
        #print(connectionTest)
        try:
            self.building = self.util.call_ida_api_function(self.util.ida_lib.openDocument, self.file_path.encode('utf-8'))
            #print('+++++++++')
            #print(self.building)
            self.signals.progress.emit(50)
            if isinstance(self.script, list): 
                for ida_script in self.script:
                    result = self.util.call_ida_api_function(self.util.ida_lib.runIDAScript, self.building, ida_script.encode('utf-8'))
                    #print(result)
            else:
                result = self.util.call_ida_api_function(self.util.ida_lib.runIDAScript, self.building, ida_script.encode('utf-8'))
                #print(result)
            
            if self.exit_ida:
                try:
                    #print('exit-ida')
                    self.script="(exit-ida)"
                    #print(self.script.encode('utf-8'))
                    self.signals.progress.emit(90)
                    #print(self.finished_fn)
                    if callable(self.finished_fn):
                        self.finished_fn(self.finished_fn_args)
                    self.signals.progress.emit(100)
                    self.util.call_ida_api_function(self.util.ida_lib.runIDAScript, self.building, self.script.encode('utf-8'))
                except Exception as e:
                    #print(e)
                    self.signals.progress.emit(0)
                    self.signals.error.emit("Failed to exit ida!")  
            else:    
                self.signals.progress.emit(90)
                if callable(self.finished_fn):
                    self.finished_fn(self.finished_fn_args)
                self.signals.progress.emit(100)

        except:
            self.signals.progress.emit(0)
            self.signals.error.emit("Failed to open the feature or run the script!")     
            
class WorkerOpenParRunAPI():
    """ Class to open IDA Doc with API """
    def __init__(self,file_path,plugin_dir,config,parmRun):
        #open file in IDA
        self.util=Util_api(plugin_dir,config)
        self.file_path=file_path.replace('/','\\')
        #print(self.util.pid)
        
        connectionTest = self.util.ida_lib.connect_to_ida(b"5945", self.util.pid.encode())
        #print(connectionTest)
        try:
            building = self.util.call_ida_api_function(self.util.ida_lib.openDocument, self.file_path.encode('utf-8'))
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
            
            #print(script)
            script_result=self.util.call_ida_api_function(self.util.ida_lib.runIDAScript, building, script.encode('utf-8'))
            #print(script_result)
        except:
            pass
            
class WorkerRunAutoMooAPI():
    """ Class to open IDA Doc with API """
    def __init__(self,file_path,plugin_dir,config,parmRun):
        #open file in IDA
        self.util=Util_api(plugin_dir,config)
        self.file_path=file_path.replace('/','\\')
        #print(self.file_path)
        #print(self.util.pid)
        # IDA Districts connection test
        connectionTest = self.util.ida_lib.connect_to_ida(b"5945", self.util.pid.encode())
        #print(connectionTest)
        try:
            #print('**************ParmRunSkopt*****************')
            self.building = self.util.call_ida_api_function(self.util.ida_lib.openDocument, self.file_path.encode('utf-8'))
            #print(self.building)

            #print('save doc')
            self.util.call_ida_api_function(self.util.ida_lib.saveDocument, self.building, self.file_path.encode(), 1)
            
            #print('--script---')
            #execute AutoMOO
            script="""((:set parmrun_ [@ "{}"])
(:set parm_name (:call find "{}" (:call :parmruns [@ :SYSTEM]) :key 'name :test 'equalp))
(open-as parm_name 'form)
(parmrun-init-summary parmrun_)
(parmrun-common-check parmrun_ t)
(PARMRUN-SKOPT parmrun_)
)""".format(parmRun,parmRun)
            #print(script)
            self.util.call_ida_api_function(self.util.ida_lib.runIDAScript, self.building, script.encode('utf-8'))   
      
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
        
            
