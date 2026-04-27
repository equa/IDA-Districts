from .files import *
from .utility import *
import os

def updateClimateMacroIdm(dir,name,config):
    pass
    
def writeSensorMacroIdm(dir,name,config):
    """Create a sensor macro"""
    if not os.path.exists(dir+"""\\{}\\Sensor-macro.idm""".format(name)):
        data=""";IDA {} Data UTF-8
(DOCUMENT-HEADER :TYPE DISTRICTS-MACRO :D "Districts macro" :APP (DISTRICTS :VER {})) """.format(getIDAVersion(config),getIDADistrictsVersion(config))
        writeToFile(data,dir,dir+"""\\{}\\Sensor-macro.idm""".format(name))  

def writeSensorMacroIdc(dir,name,config):
    """Create a sensor macro"""
    if not os.path.exists(dir+"""\\{}\\Sensor-macro.idc""".format(name)):
        data=""";IDA {} Form UTF-8
(DOCUMENT-HEADER :TYPE SCHEMA :PAGE-WIDTH 178 :PAGE-HEIGHT 97) 
(SELF-FRAME :AT ((352 190)) :R (342 176) :SLOT (:SELF) :DATA MACRO-OBJECT) """.format(getIDAVersion(config))
        writeToFile(data,dir,dir+"""\\{}\\Sensor-macro.idc""".format(name)) 
