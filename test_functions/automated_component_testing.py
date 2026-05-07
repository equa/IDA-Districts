"""automated IDA Districts component testing
Simulation models are started in parallel depending on the number of parallel processes.
After simulation the footprint is screened and the results are stored in the DB component_testing"""

from districts.utility_functions.workers import *
from districts.utility_functions.db import *
from districts.utility_functions.files import *
from districts.utility_functions.utility import *

from qgis.PyQt.QtCore import QTimer,QEventLoop
from qgis.core import QgsApplication

from datetime import datetime
import shutil
import subprocess
import os
import psycopg2.extras
import psycopg2

class Auttest_components:
    def __init__(self):
        self.components_dir="""C:\\EQUA\\Projekte\\districts\\testing\\"""
        self.temp_dir="""C:\\Users\\peter.nageler\\AppData\\Local\\Temp\\idamod52\\"""
        self.parallel_processes=1
        self.plugin_dir = QgsApplication.qgisSettingsDirPath() + "python/plugins/districts/"
        self.config=load_plugin_settings()
        conn=dbConnectPerName(self.config,"component_testing",True)
        if conn:
            self.cur=conn.cursor(cursor_factory = psycopg2.extras.RealDictCursor)

        self.files = collect_files_by_extension(self.components_dir, "idm")

        self.used_processes=0
        self.sim_workers={}

    def finished(self,s):
        print(s)
        self.used_processes-=1
        
    def error_message(self,s):
        print(s)
        
    def process_wait(self,case):
        counter=0
        while self.used_processes>=self.parallel_processes:
            self.wait(1000)
            counter+=1
            print(f'-wait for next sim case({case});used process{self.used_processes}): {counter}s')
    
    def wait(self,ms):
        loop = QEventLoop()
        QTimer.singleShot(ms, loop.quit)
        loop.exec()
        
    def readFootprint(self,file):
        data=readFileToString(self.temp_dir+'footprint.txt',skipFirstLine=False)
        
        result = {}
        for line in data.strip().splitlines():
            if "=" in line:
                key, value = line.split("=", 1)
                result[key.strip()] = float(value.strip())
                
        return result
        
    def dbQuoting(self,entry):
        quoted=str(entry) if isNumber(entry) else "'"+str(entry)+"'"
        return quoted
    
    def writeResult2DB(self,file,result):
        result['sim_case']=file.split('\\')[-1].split('.idm')[0]
        
        print(result)
        
        sql="""INSERT INTO test_results ({},test_date) VALUES ({},CURRENT_TIMESTAMP);""".format(','.join(['"'+key+'"' for key,value in result.items()]),','.join([self.dbQuoting(value) for key,value in result.items()]))
        print(sql)
        self.cur.execute(sql)
        
        

    def run(self):
        for counter,file in enumerate(self.files,1):
            print(f'{counter}: Simulation case:{file}')
            print(self.used_processes)    
            self.sim_workers[counter] = WorkerSimulateAPI(file,self.plugin_dir,self.config)
            #if self.used_processes>=self.parallel_processes:
            #    self.process_wait()
            QThreadPool.globalInstance().start(self.sim_workers[counter]) 
            self.sim_workers[counter].signals.error.connect(self.error_message)
            self.sim_workers[counter].signals.finished.connect(self.finished) 
            self.used_processes+=1
            self.process_wait(counter)
            result=self.readFootprint(file)
            self.writeResult2DB(file,result)
            

Auttest_components().run()

print('--finieshed test--')

