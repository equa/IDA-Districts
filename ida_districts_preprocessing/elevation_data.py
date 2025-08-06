import sys
import psycopg2
from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT 
from plugins.utility_functions.db import *
from plugins.utility_functions.files import *    
from plugins.utility_functions.workers import *
import subprocess   
       
class WorkerImportElevationData(QRunnable):
    """Import elevation data"""
    def __init__(self,*args,**kwargs):
        super().__init__()
        #print("Import buildings from OSM")
        self.signals=APISignals()
        self.dictDB=kwargs['dictDB']
        self.clearOldTerrain=kwargs['clearOldTerrain']
        self.filePath=kwargs['filePath']
        self.configIDADistricts=kwargs['configIDADistricts']
        self.conn=""
        self.cur=""
        self.plugin_dir=kwargs['plugin_dir']
        self.conn = dbConnect(self.dictDB,True)
        if self.conn:
            self.cur=self.conn.cursor(cursor_factory = psycopg2.extras.RealDictCursor)        

            self.configProject=loadProjectConfig(self.plugin_dir,self.dictDB['projectName'],signals=self.signals)
            self.srid=self.configProject['srid']
            #print(self.srid)
                
    @pyqtSlot()
    def run(self):
        #print('Import building data')
        self.signals.progress.emit(1)
        try:
            self.cur.execute("""SELECT EXISTS (
                                SELECT * FROM information_schema.tables 
                                WHERE  table_schema = '{}'
                                AND    table_name   = 'terrain');""".format(self.dictDB['versionName']))
            if self.clearOldTerrain == True or not "True" in str(self.cur.fetchone()):
                self.cur.execute('DROP TABLE IF EXISTS "{}".terrain;'.format(self.dictDB['versionName']))
                self.cur.execute('DROP TABLE IF EXISTS "{}".terrain1;'.format(self.dictDB['versionName']))
                self.signals.progress.emit(5)
                cmd = ' "{}bin\\raster2pgsql" -I -C -M "{}" -F -t auto "{}".terrain | "{}\\bin\\psql" -h {} -d {} -U {} -p {}'.format(self.configIDADistricts['path_postgresql'],self.filePath.replace('\\','/'), self.dictDB['versionName'],self.configIDADistricts['path_postgresql'], self.dictDB['host'], self.dictDB['projectName'], self.dictDB['user'], self.dictDB['port'])
                #print(cmd)
                os.environ['PGPASSWORD'] = self.dictDB['pwd']
                subprocess.call(cmd, shell=True)
                self.signals.progress.emit(100)
            else:
                self.cur.execute('DROP TABLE IF EXISTS "{}".terrain1;'.format(self.dictDB['versionName']))
                self.cur.execute('DROP TABLE IF EXISTS "{}".terrain2;'.format(self.dictDB['versionName'])) 
                self.signals.progress.emit(5)
                cmd = ' "{}bin\\raster2pgsql" -I -C -M "{}" -F -t auto "{}".terrain1 | "{}\\bin\\psql" -h {} -d {} -U {} -p {}'.format(self.configIDADistricts['path_postgresql'],self.filePath.replace('\\','/'), self.dictDB['versionName'],self.configIDADistricts['path_postgresql'], self.dictDB['host'], self.dictDB['projectName'], self.dictDB['user'], self.dictDB['port'])
                #print(cmd)
                os.environ['PGPASSWORD'] = self.dictDB['pwd']
                subprocess.call(cmd, shell=True)
                self.signals.progress.emit(50)
                self.cur.execute('CREATE table "{}".terrain2 AS Select * FROM "{}".terrain;'.format(self.dictDB['versionName'],self.dictDB['versionName']))
                self.cur.execute('DROP TABLE IF EXISTS "{}".terrain'.format(self.dictDB['versionName']))
                self.cur.execute(""" Create table "{}".terrain as(
                                    Select * from "{}".terrain1
                                    union
                                    Select * from "{}".terrain2)""".format(self.dictDB['versionName'],self.dictDB['versionName'],self.dictDB['versionName']))
                self.signals.progress.emit(95)
                #self.cur.execute('DROP TABLE IF EXISTS "{}".terrain1'.format(self.dictDB['versionName']))
                #self.cur.execute('DROP TABLE IF EXISTS "{}".terrain2'.format(self.dictDB['versionName']))   
                self.signals.progress.emit(100)
        except Exception as e:
            self.signals.error.emit(str(e))
            self.signals.progress.emit(0)
            

            
            