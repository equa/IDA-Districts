import sys
import psycopg2
from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT 
from .utility_functions.db import *
from .utility_functions.workers import *
import subprocess   
       
class WorkerImportElevationData(QRunnable):
    """Import elevation data"""
    def __init__(self,*args,**kwargs):
        super().__init__()
        print("Import buildings from OSM")
        self.signals=APISignals()
        self.config=kwargs['config']
        self.clearOldTerrain=kwargs['clearOldTerrain']
        self.filePath=kwargs['filePath']

        self.conn=""
        self.cur=""
        self.plugin_dir=kwargs['plugin_dir']
        self.conn = dbConnect(self.config,True)
        if self.conn:
            self.cur=self.conn.cursor(cursor_factory = psycopg2.extras.RealDictCursor)        

            self.configProject=loadProjectConfig(self.plugin_dir,self.config['projectName'],signals=self.signals)
            self.srid=self.configProject['srid']
            print(self.srid)
            
            auth_cfg = QgsAuthMethodConfig()
            QgsApplication.authManager().loadAuthenticationConfig(self.config["auth_id"], auth_cfg, True)  
 
            self.password=auth_cfg.config("password")
            self.username=auth_cfg.config("username")
                
    @pyqtSlot()
    def run(self):
        print('Import elevation data')
        self.signals.progress.emit(1)
        try:
            self.cur.execute("""SELECT EXISTS (
                                SELECT * FROM information_schema.tables 
                                WHERE  table_schema = '{}'
                                AND    table_name   = 'terrain');""".format(self.config['versionName']))
            if self.clearOldTerrain == True or not "True" in str(self.cur.fetchone()):
                self.cur.execute('DROP TABLE IF EXISTS "{}".terrain;'.format(self.config['versionName']))
                self.cur.execute('DROP TABLE IF EXISTS "{}".terrain1;'.format(self.config['versionName']))
                self.signals.progress.emit(5)
                cmd = ' "{}bin\\raster2pgsql" -I -C -M "{}" -F -t auto "{}".terrain | "{}\\bin\\psql" -h {} -d {} -U {} -p {}'.format(self.config['pathPostgres'],self.filePath.replace('\\','/'), self.config['versionName'],self.config['pathPostgres'], self.config['host'], self.config['projectName'], self.username, self.config['port'])
                print(cmd)
                os.environ['PGPASSWORD'] = self.password
                subprocess.call(cmd, shell=True)
                self.signals.progress.emit(100)
            else:
                self.cur.execute('DROP TABLE IF EXISTS "{}".terrain1;'.format(self.config['versionName']))
                self.cur.execute('DROP TABLE IF EXISTS "{}".terrain2;'.format(self.config['versionName'])) 
                self.signals.progress.emit(5)
                cmd = ' "{}bin\\raster2pgsql" -I -C -M "{}" -F -t auto "{}".terrain1 | "{}\\bin\\psql" -h {} -d {} -U {} -p {}'.format(self.config['pathPostgres'],self.filePath.replace('\\','/'), self.config['versionName'],self.config['pathPostgres'], self.config['host'], self.config['projectName'], self.username, self.config['port'])
                print(cmd)
                os.environ['PGPASSWORD'] = self.password
                subprocess.call(cmd, shell=True)
                self.signals.progress.emit(50)
                self.cur.execute('CREATE table "{}".terrain2 AS Select * FROM "{}".terrain;'.format(self.config['versionName'],self.config['versionName']))
                self.cur.execute('DROP TABLE IF EXISTS "{}".terrain'.format(self.config['versionName']))
                self.cur.execute(""" Create table "{}".terrain as(
                                    Select * from "{}".terrain1
                                    union
                                    Select * from "{}".terrain2)""".format(self.config['versionName'],self.config['versionName'],self.config['versionName']))
                self.signals.progress.emit(95)
                #self.cur.execute('DROP TABLE IF EXISTS "{}".terrain1'.format(self.config['versionName']))
                #self.cur.execute('DROP TABLE IF EXISTS "{}".terrain2'.format(self.config['versionName']))   
            self.signals.progress.emit(100)
            self.signals.finished.emit('Import elevation data completed!')
        except Exception as e:
            self.signals.error.emit(str(e))
            self.signals.progress.emit(0)
            self.signals.finished.emit('Import elevation data failed!')
            

            
            