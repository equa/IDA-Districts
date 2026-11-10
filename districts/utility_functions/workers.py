from qgis.PyQt.QtCore import QSettings, QTimer, QEventLoop, QEvent
import psycopg2
import shutil
from ..upgrade import upgradeVersionDB
from .compat import MessageCritical, MessageInfo, sip
from .db import dbConnect, dbConnectProvidePwdUser, dropDBTriggers, insertDBTriggers
from .files import (
    copyFile, createDir, districtsModelerTempDir, loadProjectConfig, readFileToList, readFileToString,
    replace_in_folder, writeToFile,
)
from .translations import tr
from .util import Util_api
from .utility import (
    copy_tree_filter_extensions_and_folders, getTemplateNameById, getTypeIdByName, getTypeNameById,
    rmtree_long_path, sanitize_pg_identifier, strToDict, write_plugin_settings,
)
import os
import numpy as np
from qgis.PyQt.QtCore import QObject, pyqtSlot, pyqtSignal, QRunnable, QThreadPool, QThread, QCoreApplication, Qt
import threading
import functools
from qgis.utils import iface
import subprocess
import time
from qgis.core import QgsProcessingUtils, Qgis, QgsMessageLog
import tempfile
import zipfile
from pathlib import Path
import traceback
from .debug_log import dprint, debug_enabled

def wait(ms):
    loop = QEventLoop()
    QTimer.singleShot(ms, loop.quit)
    loop.exec()
        
def process_wait(dlg,max_sec=60):
    counter=0
    while dlg.process_running and counter<max_sec:
        wait(1000)
        counter+=1
        dprint('-wait: '+str(counter)+'s')
    
def show_error_message(message):
    # Show the error message in a messageBar
    iface.messageBar().pushMessage("Error", message, level=MessageCritical)

def runPsqlFile(config,username,dbname,sql_file,env):
    """Execute sql_file with psql. Errors are logged in the message log 'Districts'.
    Returns an error summary for the message bar or None if psql reported no error."""
    cmd = [
        f"{config['pathPostgresql']}bin\\psql",
        f"--dbname=postgresql://{username}@{config['host']}:{config['port']}/{dbname}",
        "--quiet",
        "-f",
        sql_file
    ]
    try:
        result = subprocess.run(cmd, env=env, stdout=subprocess.DEVNULL, stderr=subprocess.PIPE) # nosec B603
    except OSError as e:
        QgsMessageLog.logMessage("psql could not be started ({}): {}".format(cmd[0], e), "Districts", MessageCritical)
        return "psql could not be started (PostgreSQL path in the plugin settings?)"
    stderr = result.stderr.decode('utf-8', errors='replace')
    errors = [line for line in stderr.splitlines() if 'ERROR:' in line or 'FATAL:' in line]
    if result.returncode != 0 or errors:
        QgsMessageLog.logMessage(
            "psql {} (exit code {}):\n{}".format(os.path.basename(sql_file), result.returncode, stderr.strip()),
            "Districts",
            MessageCritical
        )
        return "{} error(s) in {} (see message log 'Districts')".format(len(errors) or 1, os.path.basename(sql_file))
    return None

class _MainThreadInvoker(QObject):
    """Executes calls emitted from worker threads in the main (GUI) thread; the emitting thread waits until the call is done."""
    invoke=pyqtSignal(object)

    def __init__(self):
        super().__init__()
        blocking=getattr(getattr(Qt,'ConnectionType',Qt),'BlockingQueuedConnection',None) or Qt.BlockingQueuedConnection  # Qt6 / Qt5
        self.invoke.connect(self._call, blocking)

    # must be a real Qt slot: for an undecorated Python method PyQt creates a proxy in the thread that called connect,
    # which can be a blocked worker thread (deadlock)
    @pyqtSlot(object)
    def _call(self, call):
        call()

_main_thread_invoker=None
_main_thread_invoker_lock=threading.Lock()
# create the invoker in the main thread when the plugin is loaded (fallback in runInMainThread)
def _inMainThread():
    return sip.unwrapinstance(QThread.currentThread())==sip.unwrapinstance(QCoreApplication.instance().thread())

if QCoreApplication.instance() is not None and _inMainThread():
    _main_thread_invoker=_MainThreadInvoker()

def runInMainThread(fn, *args, **kwargs):
    """Run fn in the main thread and return its result (exceptions are raised in the calling thread).
    Use it in workers for QGIS layers and the layer tree: a layer created in a pool thread opens its own DB connection
    for that thread, which is never released (one more idle connection per run), and QgsProject must only be changed in the main thread.
    The main thread must not block while waiting for the worker (QEventLoop waits are fine)."""
    app_thread=QCoreApplication.instance().thread()
    if _inMainThread():
        return fn(*args, **kwargs)
    global _main_thread_invoker
    with _main_thread_invoker_lock:
        if _main_thread_invoker is None:
            invoker=_MainThreadInvoker()  # first call from a worker thread: move it to the main thread (the decorated slot then runs there)
            invoker.moveToThread(app_thread)
            _main_thread_invoker=invoker
    result={}

    def call():
        try:
            result['value']=fn(*args, **kwargs)
        except BaseException as e:
            result['error']=e

    _main_thread_invoker.invoke.emit(call)
    if 'error' in result:
        raise result['error']
    return result.get('value')

def closeConnection(conn):
    """Close a psycopg2 connection (ignores None/'' and already closed connections)"""
    try:
        if conn and not conn.closed:
            conn.close()
    except Exception:
        QgsMessageLog.logMessage(traceback.format_exc(),"Districts",MessageCritical)

class _CloseConnectionOnClose(QObject):
    """Event filter of closeConnectionOnFinish: a close event is also seen if the dialog overrides closeEvent
    without calling QDialog.closeEvent (then reject/finished are not emitted)."""
    def __init__(self, dialog, owner=None):
        super().__init__(dialog)
        self.dialog=dialog
        self.owner=owner if owner is not None else dialog

    def eventFilter(self, obj, event):
        if event.type()==getattr(QEvent,'Type',QEvent).Close:  # Qt6 / Qt5
            self.closeLater()
        return False

    def closeLater(self):
        # after the dialog's own closeEvent/reject handlers, which may still use the connection
        QTimer.singleShot(0, self.closeIfClosed)

    def closeIfClosed(self):
        try:
            if not self.dialog.isVisible():  # not if the close event was ignored
                closeConnection(getattr(self.owner,'conn',None))
        except RuntimeError:  # dialog already deleted
            pass

def closeConnectionOnFinish(dialog, owner=None):
    """Close the own DB connection of the dialog (owner.conn if owner is given, e.g. a controller object, otherwise dialog.conn;
    also if it was replaced later) when the dialog is closed/accepted/rejected.
    Only for dialogs that are created anew each time they are opened."""
    closer=_CloseConnectionOnClose(dialog, owner)
    dialog.installEventFilter(closer)
    dialog.finished.connect(lambda *_: closer.closeLater())

def closesOwnConnection(run):
    """Decorator for the run method of a worker that opened its own DB connection (self.conn) in __init__/run:
    close it when run ends, otherwise it stays idle on the server as long as the worker object is referenced
    (e.g. main.worker_x until the next run)."""
    @functools.wraps(run)
    def wrapper(self, *args, **kwargs):
        try:
            return run(self, *args, **kwargs)
        finally:
            closeConnection(getattr(self,'conn',None))
    return wrapper

class WorkerDoneSignals(QObject):
    done=pyqtSignal()

class WorkerDoneTracker(QRunnable):
    """Runs a worker and emits done when its run returns or raises, independent of the signals the worker emits itself."""
    def __init__(self, worker):
        super().__init__()
        self.worker=worker
        self.signals=WorkerDoneSignals()

    def run(self):
        try:
            self.worker.run()
        finally:
            self.signals.done.emit()

def startWorkers(workers, btn):
    """Starts the workers in the global thread pool; btn stays disabled until all of them are done
    (also workers started later with this function while others are still running, e.g. a follow-up step started from a finished signal)."""
    btn.setEnabled(False)
    btn.workers_running=getattr(btn,'workers_running',0)+len(workers)

    def onDone():
        btn.workers_running-=1
        if btn.workers_running==0:
            btn.setEnabled(True)

    for worker in workers:
        tracker=WorkerDoneTracker(worker)
        tracker.signals.done.connect(onDone)
        QThreadPool.globalInstance().start(tracker)

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
        dprint(args)
        self.signals=APISignals()
        self.config=kwargs['config']
        self.cur=kwargs['cur']
        self.dlg=kwargs['dlg']

    @pyqtSlot()
    def run(self):
        try:
            dprint('Load project version')
            self.signals.progress.emit(10)  
            if debug_enabled(): dprint(self.config['versionName'])
            
            #version handling           
            
            #update triggers: delete last loaded versions triggers if exists and create new triggers
            dropDBTriggers(self.cur,self.config,lastLoad=True)
            dropDBTriggers(self.cur,self.config)
            
            upgradeVersionDB(self.cur,self.config)
            
            insertDBTriggers(self.cur,self.config)
  
            self.config['lastVersionName']=self.config['versionName']            
            self.signals.progress.emit(100)            
        except Exception as e:
            dprint(f'error: {e}')
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
        dprint(kwargs)
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
        """Run the import; emit failed if it stops without emitting finished (early return or exception)"""
        try:
            result=self._run()
        except Exception as e:
            QgsMessageLog.logMessage(traceback.format_exc(),"Districts",MessageCritical)
            self.signals.error.emit("Project import failed: "+str(e))
            result=False
        if result is False:
            if self.dlg:
                self.dlg.process_running=False
            self.signals.failed.emit('failed')

    def _run(self):
        dprint('Import project')
        dprint(self.project_name)
        self.signals.progress.emit(1)

        if not os.path.exists(self.filename):
            QgsMessageLog.logMessage(
                tr('@default',"path_not_exists")+self.filename,
                "Districts",
                MessageCritical
            )
            self.signals.error.emit(tr('@default',"path_not_exists")+self.filename)
            return False

        if zipfile.is_zipfile(self.filename):
            dprint("Valid ZIP file")
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
        else:
            dprint("Not a ZIP file")
            name=self.filename.split('\\')[-1]
            src_dir='\\'.join(self.filename.split('\\')[0:-1])+'\\'

        src_dir=src_dir+name+'\\' 

        dprint(src_dir)
        dprint(self.config)
        dprint(name)
        
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
        dprint(db_info)
        
        #check if project already exists
        if db_info['projectName'] not in self.projectNames:
            dprint('project does not exist') 

            target_dir=self.config['pathProjects']+(self.project_name if self.project_name else name)
            dprint(target_dir)
            os.makedirs(target_dir, exist_ok=True)

            self.signals.progress.emit(20)
            try:
                copy_tree_filter_extensions_and_folders(src_dir+'customer_templates',target_dir+'\\customer_templates',signals=self.signals,exclude_extensions=self.filter_extensions)
                copy_tree_filter_extensions_and_folders(src_dir+'energy_plant_templates',target_dir+'\\energy_plant_templates',signals=self.signals,exclude_extensions=self.filter_extensions)
                copy_tree_filter_extensions_and_folders(src_dir+'climate',target_dir+'\\climate',signals=self.signals,exclude_extensions=self.filter_extensions)

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
                dprint(f'error: {e}')
                self.signals.error.emit("Data center copying failed: "+ str(e))
                return False
            try:
                dprint('--versions directory--')
                if os.path.exists(src_dir+'versions'):
                    copy_tree_filter_extensions_and_folders(src_dir+'versions',target_dir+'\\versions\\',signals=self.signals,exclude_extensions=self.filter_extensions,exclude_folders=self.filter_folders)
                self.signals.progress.emit(50)
            except Exception as e:
                dprint(f'error: {e}')
                self.signals.error.emit("Modelling data copying failed!")
                return False
                
            if not os.path.exists(target_dir+'\\versions'):
                createDir(target_dir,'versions')
                
            try:
                copyFile(src_dir+'configProject.txt',target_dir,target_dir+'\\configProject.txt')
                copyFile(src_dir+'requestedOutputs.txt',target_dir,target_dir+'\\requestedOutputs.txt')
                self.signals.progress.emit(70)
            except Exception as e:
                dprint(f'error: {e}')
                self.signals.error.emit("Copying data failed!")
                return False
            try:
                copyFile(src_dir+'layersConfig.txt',target_dir,target_dir+'\\layersConfig.txt')
            except Exception:
                QgsMessageLog.logMessage(
                    traceback.format_exc(),
                    "Districts",
                    MessageCritical
                )
            
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
            if self.project_name and name not in ['secondary_network','low_temperature_network','hc_network']:
                sql='\n'.join(["CREATE SCHEMA IF NOT EXISTS {};".format(version) for version in self.versionNames]) # nosec B608
                dprint(sql)
                if sql:
                    self.cur.execute(sql)
                self.signals.progress.emit(73)
                
                #create tables in new schema
                #project tables
                filedata=readFileToString(self.plugin_dir+"\\DB_projectTablesDefault.txt") # nosec B608
                dprint(filedata)
                self.cur.execute(filedata)
                
                dprint(self.versionNames)
                if self.versionNames:
                    #version tables
                    dprint(self.project_name)
                    self.projectConfig=loadProjectConfig(self.config,project_name=self.project_name,signals=self.signals) 
                    dprint(self.projectConfig)                    
                    filedata=readFileToString(self.plugin_dir+"\\DB_versionTablesDefault.txt")
                    filedata = filedata.replace("$srid$", self.projectConfig['srid'])
                    filedata = filedata.replace("$plugins_path$", self.plugin_dir)
                    for version in self.versionNames:
                        newdata = filedata.replace("$versionName$", self.config['versionName'])   
                        dprint(newdata)
                        self.cur.execute(newdata)
            
            self.signals.progress.emit(75)
            if name in ['heating_network']:
                dprint('-----heating_network------')
                sql="""ALTER TABLE "base1".customers ADD COLUMN load_w NUMERIC;
ALTER TABLE "base1".customers ADD COLUMN gfa_m2 NUMERIC;"""
                self.cur.execute(sql)
            self.signals.progress.emit(76)
                
            temp_dir = QgsProcessingUtils.tempFolder()+'\\'
            #create tables in new schema
            env = os.environ.copy()
            env["PGPASSWORD"] = self.password
            dbname = sanitize_pg_identifier(db_info['projectName'])

            def prepareSqlFile(src_file):
                """copy src_file to the temp folder with the paths replaced (None if src_file does not exist)"""
                if not os.path.exists(src_file):
                    return None
                with open(src_file, "r") as myfile:
                    filedata=myfile.read()
                filedata = filedata.replace("$plugins_path$", os.path.normpath(self.plugin_dir).replace('\\','\\\\'))
                filedata = filedata.replace("$districts_path$", os.path.normpath(self.config['pathDistricts']).replace('\\','\\\\'))
                temp_file=temp_dir+Path(src_file).stem+'_.sql'
                with open(temp_file,'w') as myfile:
                    myfile.write(filedata)
                return temp_file

            sql_file=prepareSqlFile(src_dir+('db_tables.sql' if self.project_name else name+'.sql'))
            self.signals.progress.emit(77)
            if sql_file:
                error=runPsqlFile(self.config,self.username,dbname,sql_file,env)
                if error:
                    self.signals.error.emit(error)
            else:
                self.signals.error.emit("No database tables found in "+src_dir)

            self.signals.progress.emit(79)
            filedata=readFileToString(self.plugin_dir+"\\SQL_scripts.txt") # nosec B608
            self.cur.execute(filedata)
            self.signals.progress.emit(80)
            if self.project_name and not self.no_db_results:
                sql_file=prepareSqlFile(src_dir+'db_results.sql')
                if sql_file:
                    error=runPsqlFile(self.config,self.username,dbname,sql_file,env)
                    if error:
                        self.signals.error.emit(error)
                else:
                    QgsMessageLog.logMessage(
                        "The template {} contains no database results (db_results.sql)".format(name),
                        "Districts",
                        MessageInfo
                    )
            self.conn.close()

        else:
            self.signals.error.emit("Project already exists in DB!")
            self.signals.progress.emit(0)           
            return False
            
        self.signals.progress.emit(100)
        self.signals.finished.emit(db_info['projectName'])
        
class WorkerExportProject(QRunnable):
    """Worker thread
    Inherits from QRunnable to handle worker thread setup, signals and wrap-up."""
    def __init__(self,*args,**kwargs):
        super().__init__()
        self.args=args
        dprint(args)
        self.signals=APISignals()
        self.config=kwargs['config']
        self.plugin_dir=kwargs['plugin_dir']
        self.password=kwargs['password']
        self.username=kwargs['username']
        self.filename=kwargs['filename']
        self.filter_folders=kwargs['filter_folders']
        self.filter_extensions=kwargs['filter_extensions']
        self.autosave=kwargs['autosave']
        dprint(self.filter_extensions)
        dprint(self.filter_folders)
        self.no_db_results=kwargs['no_db_results']
        self.conn=""
        self.cur=""
        self.conn = dbConnect(self.config,True)
        if self.conn:
            self.cur=self.conn.cursor(cursor_factory = psycopg2.extras.RealDictCursor)
            
    @pyqtSlot()
    def run(self):
        dprint('Export project worker')
        self.signals.progress.emit(1)
        
        dprint(self.filename)
        dir='\\'.join(self.filename.split('\\')[0:-1])+'\\'
        name=self.filename.split('\\')[-1].split('.')[0]
        dprint(name)
        if self.autosave:
            temp_folder=dir
            createDir(dir,'autosave')
            dir+='autosave\\'
        else:
            temp_folder=districtsModelerTempDir()
        createDir(dir,name)
        dir=dir+name
        dprint(dir)
        createDir(temp_folder,name,delete=True)
        temp_folder+=name+'\\'
        dprint(temp_folder)
                    
        # Ensure the directory exists, create it if necessary
        sql_path = temp_folder+f"\\{name}.sql"

        os.makedirs(os.path.dirname(sql_path), exist_ok=True)

        cmd = [
            os.path.join(self.config['pathPostgresql'],"bin\\pg_dump"),  # Path to pg_dump
            "--dbname=postgresql://{}:{}@{}:{}/{}".format(self.username,self.password ,self.config['host'],self.config['port'],self.config['projectName']),
            "--exclude-table=temp.result_vis_*",  # 'show data on map' results (dropped when the project/version is loaded)
        ]
        if self.no_db_results:
            cmd.append("--exclude-table=*.customer_s*")
            cmd.append("--exclude-table=*.line_s*")
            cmd.append("--exclude-table=*.energy_plant_s*")            
            cmd.append("--exclude-table=*.customer_m_*")
            cmd.append("--exclude-table=*.line_m*")
            cmd.append("--exclude-table=*.energy_plant_m*")
            cmd.append("--exclude-table=*.massbalance_*")
            cmd.append("--exclude-table=*.heatbalance_*")
            cmd.append("--exclude-table=*.kpi_*")
        dprint(cmd)
        # Output file redirection (using stdout to redirect the output to a file)
        with open(sql_path, "w") as output_file:
            subprocess.call(cmd, stdout=output_file) # nosec B603      
            
        self.signals.progress.emit(25)

        try:
            copy_tree_filter_extensions_and_folders(self.config['pathProjects']+self.config['projectName'], temp_folder,self.signals,self.filter_extensions,self.filter_folders)
        except Exception as e:
            dprint(f'error: {e}')
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
            dir,            # target folder without .zip
            "zip",          # format
            temp_folder     # source folder
        )
        
        # remove temp folder
        if os.path.exists(temp_folder) and os.path.isdir(temp_folder):
            rmtree_long_path(temp_folder) 

        self.signals.progress.emit(100)
        self.signals.finished.emit(self.filename)
    
class WorkerPlotInvokedFeatureLoad(QRunnable):
    """Worker thread
    Inherits from QRunnable to handle worker thread setup, signals and wrap-up."""
    def __init__(self,*args,**kwargs):
        super().__init__()
        self.args=args
        dprint('--WorkerPlotInvokedFeatureLoad--')
        self.signals=APIPlotinvokedFeatureSignals()
        self.config=kwargs['config']
        dprint(self.config)
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
        dprint(sql)
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
                    dprint(file_path)
                    if os.path.exists(file_path):
                        legend=self.type.capitalize()+':'+id

                        dprint(file_path)
                        filedata=readFileToList(file_path)

                        dprint(filedata)
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
                            dprint(f'error: {e}')
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
                            except Exception:
                                self.signals.error.emit("Different simulation periods are used!")

                        #plotting
                        self.signals.dataProcessed.emit([{'time':time,'data':valuesPowerInt,'label':'Customer ID='+str(id)},{'time':time,'data':valuesEnergyInt,'label':'Customer ID='+str(id)}])
                        count+=1
                        
                        self.progress_value=int(count/len(self.rows)*98)
                        self.signals.progress.emit(self.progress_value)
        except Exception:
            QgsMessageLog.logMessage(
                traceback.format_exc(),
                "Districts",
                MessageCritical
            )
                           
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

        dprint(self.util.pid)
        
        connectionTest = self.util.ida_lib.connect_to_ida(b"5945", self.util.pid.encode())
        dprint(connectionTest)
        file_path=""
        building=None
        try:
            for counter,file_path in enumerate(self.file_pathes,1):
                if os.path.exists(file_path):
                    dprint(file_path)
                    #open file
                    dprint('+++++++++opening+++++++++++')
                    building = self.util.call_ida_api_function(self.util.ida_lib.openDocument, file_path.encode('utf-8'))
                    dprint('+++++++++opened+++++++++++')
                    #run sim (IDA is closed after the last file, not here: the next files use the same session)
                    script="""((RUN-SIMULATION [@ :SYSTEM])
(save-document [@ :SYSTEM] "{}" nil)
(close (:call find-view [@ :SYSTEM] 'schema t)))""".format(file_path.replace('\\','\\\\'))
                    dprint(script)
                    self.result=self.util.call_ida_api_function(self.util.ida_lib.runIDAScript, building, script.encode('utf-8'))
                    dprint('save doc')
                    #self.util.call_ida_api_function(self.util.ida_lib.saveDocument, building, file_path.encode('utf-8'), 1)   
                    dprint('+++++++++saved++++++++++++++++')
                    self.progress_value=int(counter/len(self.file_pathes)*98)+1
                    dprint(self.progress_value)
                    self.signals.progress.emit(self.progress_value)
                    if self.result:
                        self.signals.status.emit('Simulation finished')
                    else:
                        self.signals.status.emit('Simulation failed')
                else:
                    self.signals.error.emit("Sim model does not exist!")
            self.signals.progress.emit(100)
            dprint('simulation-finished')
        except Exception:
            self.signals.progress.emit(0)
            self.signals.error.emit("Failed to open the feature: {}!".format(file_path))
        finally:
            #close IDA Districts whether the simulations finished or failed
            self.util.exit_ida(building)

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

        dprint(self.util.pid)
        
        connectionTest = self.util.ida_lib.connect_to_ida(b"5945", self.util.pid.encode())
        dprint(connectionTest)
        self.building={}
        try:
            if os.path.exists(self.file_path):
                dprint(self.file_path)
                #open file
                dprint('+++++++++opening+++++++++++')
                self.building = self.util.call_ida_api_function(self.util.ida_lib.openDocument, self.file_path.encode('utf-8'))
                dprint('+++++++++opened+++++++++++')
                #run sim
                script="""((RUN-SIMULATION [@ :SYSTEM])
(save-document [@ :SYSTEM] "{}" nil)
(close (:call find-view [@ :SYSTEM] 'schema t)))""".format(self.file_path.replace('\\','\\\\'))
                dprint(script)
                self.result=self.util.call_ida_api_function(self.util.ida_lib.runIDAScript, self.building, script.encode('utf-8'))
                dprint(self.result)
                if self.result:
                    self.signals.status.emit('Simulation finished')
                else:
                    self.signals.status.emit('Simulation failed')
            else:
                self.signals.error.emit("Sim model does not exist!")
            dprint('++++simulation-finished++++')
        except Exception:
            self.signals.error.emit("Failed to open the feature: {}!".format(self.file_path))
        finally:
            #close IDA Districts whether the simulation finished or failed
            self.util.exit_ida(self.building)
        self.signals.finished.emit("finished")

            
class APISignals(QObject):
    progress=pyqtSignal(int)
    error=pyqtSignal(str)
    status=pyqtSignal(str)
    finished =pyqtSignal(str)
    failed =pyqtSignal(str)
    
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
        dprint('+++++++++++++++++++open Doc++++++++++++++++')

        self.signals.progress.emit(1)
        self.util=Util_api(self.plugin_dir,self.config,submodel=self.submodel)

        dprint(self.util.pid)
        
        connectionTest = self.util.ida_lib.connect_to_ida(b"5945", self.util.pid.encode())
        dprint(connectionTest)
        try:
            result = self.util.call_ida_api_function(self.util.ida_lib.openDocument, self.file_path.encode('utf-8'))
            self.signals.progress.emit(100)
        except Exception:
            self.signals.progress.emit(0)
            self.signals.error.emit("Failed to open the feature!")  
            
class WorkerOpenModelCmd(QRunnable):
    """Worker thread
    Inherits from QRunnable to handle worker thread setup, signals and wrap-up."""
    def __init__(self,file_path,config,submodel='1',script=None,progress=True):
        super().__init__()
        self.file_path=file_path.replace('/','\\')
        self.signals=APISignals()
        self.submodel=submodel
        self.config=config
        self.script=script
        self.progress=progress
            
    @pyqtSlot()
    def run(self):
        #open file in IDA
        if self.progress:
            self.signals.progress.emit(1)

        try:
            cmd = [
                f'"{self.config['pathDistricts']}bin\\ida-districts.exe"',
                f'"{self.config['pathDistricts']}bin\\ida.img"',
                "-C",
                f"ida_{self.submodel}_{time.strftime('%m%d%H%M%S', time.localtime())}",
                "-G1"
            ]
            if self.script:
                cmd.append('-e')
                writeToFile(self.script,districtsModelerTempDir(),os.path.join(districtsModelerTempDir(),"script.txt"))
                cmd.append('"'+os.path.join(districtsModelerTempDir(),"script.txt").replace('\\','\\\\')+'"')
                cmd.append('-r')
            cmd.append('"'+self.file_path+'"')     
            cmd=' '.join(cmd)
            dprint(cmd)

            result = subprocess.run(cmd, 
                stdout=subprocess.PIPE, 
                stderr=subprocess.PIPE, 
                text=True)  # nosec B603
            dprint(result)

            if result.returncode==0:
                if self.progress:
                    self.signals.progress.emit(100)
                dprint('updated')
                self.signals.finished.emit(result.args)
            else:
                if self.progress:
                    self.signals.progress.emit(0)
                self.signals.finished.emit('IDA Districts model updated failed!')
        except Exception as e:
            if self.progress:
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

        dprint(self.util.pid)
        
        connectionTest = self.util.ida_lib.connect_to_ida(b"5945", self.util.pid.encode())
        dprint(connectionTest)
        try:
            self.building = self.util.call_ida_api_function(self.util.ida_lib.openDocument, self.file_path.encode('utf-8'))
            dprint(self.building)
            self.signals.progress.emit(50)
            if isinstance(self.script, list): 
                for ida_script in self.script:
                    result = self.util.call_ida_api_function(self.util.ida_lib.runIDAScript, self.building, ida_script.encode('utf-8'))
                    dprint(result)
            else:
                result = self.util.call_ida_api_function(self.util.ida_lib.runIDAScript, self.building, self.script.encode('utf-8'))
                dprint(result)

            if self.exit_ida:
                try:
                    self.signals.progress.emit(90)
                    dprint(self.finished_fn)
                    if callable(self.finished_fn):
                        self.finished_fn(self.finished_fn_args)
                    self.signals.progress.emit(100)
                    self.util.exit_ida(self.building)
                except Exception as e:
                    dprint(e)
                    self.signals.progress.emit(0)
                    self.signals.error.emit("Failed to exit ida!")  
            else:    
                self.signals.progress.emit(90)
                if callable(self.finished_fn):
                    self.finished_fn(self.finished_fn_args)
                self.signals.progress.emit(100)

        except Exception:
            self.signals.progress.emit(0)
            self.signals.error.emit("Failed to open the feature or run the script!")     