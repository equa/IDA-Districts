from qgis.core import Qgis, QgsMessageLog, QgsProject
from qgis.utils import iface
from datetime import datetime 
from plugins.utility_functions.db import *
from scipy.interpolate import interp1d
import numpy as np

import time

def interpolateTimeData(dt,file_data):
    start_hour=file_data[0,0]
    start_hour=start_hour-start_hour%(dt/3600)
    end_hour=file_data[-1,0]
    end_hour=end_hour-end_hour%(dt/3600)+dt/3600

    time=np.arange(start_hour, end_hour+dt/3600, dt/3600)

    # apply the interpolation to each column
    f = interp1d(file_data[:,0], file_data[:,1:], axis=0, fill_value="extrapolate")

    # get final result
    file_data=np.column_stack((time,f(time)))
    return file_data
    
def getDateTime(y=2024,m=1,d=1,h=0,min=0,s=0):
    return datetime(y, m, d, h, min,s)
    
def getDatetimeFromString(date_string):
    time_split=date_string.split()
    return getDateTime(int(time_split[0].split('-')[0]), int(time_split[0].split('-')[1]), int(time_split[0].split('-')[2]), int(time_split[1].split(':')[0]), int(time_split[1].split(':')[1]),int(time_split[1].split(':')[2]))

def getAvergageByMode(mode,cur,dictDB,table):
    """return value in seconds"""
    if mode=='Hourly average':
        return 'hour'
    elif mode=='Daily average':
        return 'day'
    elif mode=='Monthly average':
        return 'month'
    elif mode=='Values':
        return getTimeDiff(cur,dictDB,table,'time','fid')/3600

def getNTPTime(year,month,day,hour,minute,second):
    diff = datetime(year, month, day, hour, minute, second) - datetime(1900, 1, 1, 0, 0, 0)
    timestamp = diff.days*24*60*60+diff.seconds
    return timestamp

def getNTPTimeFromString(date_string):
    return getNTPTime(int(date_string.split('-')[0]),int(date_string.split('-')[1]),int(date_string.split()[0].split('-')[2]),int(date_string.split()[1].split(':')[0]),int(date_string.split(':')[1]),int(date_string.split(':')[2]))
    
def getNTPTimeFromDatetime(datetime):
    return getNTPTime(datetime.year,datetime.month,datetime.day,datetime.hour,datetime.minute,datetime.second)
                                    
def getTimeFromNTP(ntp):
    t = time.ctime(ntp-2208992400)
    return datetime.strptime(t, '%a %b %d %H:%M:%S %Y')

class alt_count:
    def __init__(self, start=0, step=1):
        self.current = start - step
        self.step = step

    def __next__(self):
        self.current = self.current + self.step
        return self.current
        
def listToBracketsString(A):
    r = ''
    i=0
    for item in A:
        if isinstance(item,list): 
            r+= ('(' if i==0 else ' ')+listToBracketsString(item)+(')' if i==len(A)-1 else '')
        else: 
            r+=('(' if i==0 else ' ') +item+(')' if i==len(A)-1 else '')
        i+=1
    return r
                
def isInt(str):
    try:
        int(str)
        return True
    except:
        return False

def isFloat(str):
    try:
        float(str)
        return True
    except:
        return False
        
def strToDict(str):
    str=str.replace('"','').replace("'",'')
    dict={}
    try:
        for i in str[1:-1].split(","):
            entry=i.split(": ")[1].strip()
            if entry == "True" or entry == "False":
                if entry == "True":
                    dict[i.split(": ")[0].strip()]=True
                else:
                    dict[i.split(": ")[0].strip()]=False
            else:
                dict[i.split(": ")[0].strip()]=entry
    except:
        pass
    return dict

    
def checkString(str):
    """Check if String contains upper cases, white spaces or spacial characters """
    ok=True
    
    for char in str:
        # checking for uppercase character and flagging
        if char.isupper():
            ok = False
            break
      
    #checking for white spaces
    if ' ' in str:
        ok = False
        
    #checking for spacial characters
    special_characters="!@#$%^&*()-+?=,<>/\""
    if any(c in special_characters for c in str):   
        ok = False
        
    if not ok:
        iface.messageBar().pushMessage("Error", "Please don`t use upper cases, white spaces or special characters in your name!", level=Qgis.Critical)
    
    return ok
    
def refreshMap():
    """ Refresh the canvas map"""
    iface.mapCanvas().refreshAllLayers()
    
def zoomToLayer(layerName):
    """Zoom extends to layer with layerName"""
    vLayer = QgsProject.instance().mapLayersByName(layerName)[0]
    canvas = iface.mapCanvas()
    extent = vLayer.extent()
    canvas.setExtent(extent)
    refreshMap()
    
def checkStringSize(str,limit):
    """check if the string size is within the limit """
    if len(str)<limit:
        return True
    else:
        return False
        
def getAssettypeNameById(type_id):
    typeName=""
    if type_id==1:
        typeName="customer_assettypes"
    elif type_id==2:
        typeName="energy_plant_assettypes"
    elif type_id==3:
        typeName="device_assettypes"
    return typeName

def getTypeNameById(type_id):
    typeName=""
    if type_id==1:
        typeName="customers"
    elif type_id==2:
        typeName="energy_plants"
    elif type_id==3:
        typeName="devices"
    return typeName
    
def getTypeIdByName(type_name):
    if type_name=='customer' or type_name=='Customer':
        type_id='1'
    elif type_name=='energy_plant' or type_name=='Energy plant' or type_name=='Energy_plant':
        type_id='2'
    elif type_name=='device' or type_name=='Device':
        type_id='3'
    else:
        type_id='4'
    return type_id
    
def returnVarName(measure):
    varName=""
    if measure==1:
        varName="|T_var|"
    elif measure==2:
        varName="|P_var|"
    elif measure==3:
        varName="|M_var|"
    elif measure==4:
        varName="P"
    return varName
    
def getMacroTypeName(type):
    type_name=""
    if type==1:
        type_name='Customer'
    elif type==2:
        type_name='Energy_plant'
    elif type==3:
        type_name='Device'
    elif type==4:
        type_name='Supervisory_control'
    return type_name
    
def checkListNumbers(list_numb):
    """check if entries in list are numbers"""
    for numb in list_numb:
        if not isFloat(numb):
            return False
    return True
  
def is_number(s):
    try:
        float(s)
        return True
    except:
        return False
        
def is_date(date):
    try:
        time_split=date.split()
        time={'year':int(time_split[0].split('-')[0]),'month':int(time_split[0].split('-')[1]),'day':int(time_split[0].split('-')[2]),'hour':int(time_split[1].split(':')[0]),'minute':int(time_split[1].split(':')[1]),'second':int(time_split[1].split(':')[2])}
        if len(str(time['year']))==4 and len(str(time['month'])) in [1,2] and len(str(time['day'])) in [1,2] and len(str(time['hour'])) in [1,2] and len(str(time['minute'])) in [1,2] and len(str(time['second']))in [1,2]:
            return True
        else:
            return False
    except:
        return False
    
            
    
    