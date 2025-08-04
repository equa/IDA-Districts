from qgis.core import Qgis, QgsMessageLog, QgsProject
from qgis.utils import iface
from datetime import datetime 
#from plugins.utility_functions.db import *
from scipy.interpolate import interp1d
import numpy as np
import shutil
import time
import os

def rmtree_long_path(dir):
    if os.path.exists(dir) and os.path.isdir(dir):
        if os.name == 'nt':
            dir='\\\\?\\'+dir
        shutil.rmtree(dir)
        
def copy_tree_filter_extensions_and_folders(src, dst, signals=None,exclude_extensions=None, exclude_folders=None):
    # Set default values if no extensions or folders are provided
    if exclude_extensions is None:
        exclude_extensions = []
    if exclude_folders is None:
        exclude_folders = []
    if exclude_folders is None:
        signals = False

    # Ensure the extensions and folder names are in lowercase for case-insensitive comparison
    exclude_extensions = [ext.lower() for ext in exclude_extensions]
    exclude_folders = [folder.lower() for folder in exclude_folders]

    # Walk through the source directory
    for root, dirs, files in os.walk(src):
        # Filter out files with the specified extensions
        files_to_copy = [f for f in files if not any(f.lower().endswith(ext) for ext in exclude_extensions)]
        
        # Copy each file to the destination, skipping excluded extensions
        for file in files_to_copy:
            full_file_path = os.path.join(root, file)
            relative_path = os.path.relpath(full_file_path, src)
            destination_file_path = os.path.join(dst, relative_path)
            try:
                if os.name == 'nt' and '\\\\?\\' not in destination_file_path:  # Windows OS
                    destination_file_path = '\\\\?\\' + os.path.abspath(destination_file_path)
                if os.name == 'nt' and '\\\\?\\' not in full_file_path:  # Windows OS
                    full_file_path = '\\\\?\\' + os.path.abspath(full_file_path)
                # Make sure the destination directory exists
                os.makedirs(os.path.dirname(destination_file_path), exist_ok=True)
                
                # Copy the file to the destination
                shutil.copy2(full_file_path, destination_file_path)
            except:
                if signals:
                    signals.error.emit("Failed to copy file (file path probably to long):"+destination_file_path)
        
        # Prevent os.walk from traversing excluded directories
        for dir_name in dirs[:]:
            if dir_name.lower() in exclude_folders:
                dirs.remove(dir_name)  # Remove directory from traversal list
                
def flatten(nested_list):
    return [item for sublist in nested_list for item in sublist]
    
def flatten_nestedList(nested_list):
    flat_list = []
    for item in nested_list:
        if isinstance(item, list):
            flat_list.extend(flatten_nestedList(item))  # Recursively flatten the sublist
        else:
            flat_list.append(item)
    return flat_list 

def isNumber(input):
    try:
        if float(input) or float(input)==0.0:
            return True
        else:
            return False
    except:
        return False
        
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

    
def checkString(my_string):
    """Check if String contains upper cases, white spaces or spacial characters """

    #checking empty string
    if len(my_string)==0:
        iface.messageBar().pushMessage("Error", "Please enter a name!", level=Qgis.Critical)
        return False

    #start with a character
    if not my_string[0].isalpha():
        iface.messageBar().pushMessage("Error", "Please start with an alphabetic character!", level=Qgis.Critical)
        return False
        
    ok=True
    for char in my_string:
        # checking for uppercase character and flagging
        if char.isupper():
            ok = False
            break
      
    #checking for white spaces
    if ' ' in my_string:
        ok = False
        
    #checking for spacial characters
    special_characters="!@#$%^&*()-+?=,<>/\""
    if any(c in special_characters for c in my_string):   
        ok = False
        
    if not ok:
        iface.messageBar().pushMessage("Info", "Please don`t use upper cases, white spaces or special characters in your name!", level=Qgis.Info)
    
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
        
def getTemplateNameById(type_id):
    typeName=""
    if type_id==1:
        typeName="customer_templates"
    elif type_id==2:
        typeName="energy_plant_templates"
    return typeName

def getTypeNameById(type_id):
    typeName=""
    if type_id==1:
        typeName="customers"
    elif type_id==2:
        typeName="energy_plants"
    return typeName
    
def getTypeIdByName(type_name):
    if type_name=='customer' or type_name=='Customer':
        type_id='1'
    elif type_name=='energy_plant' or type_name=='Energy plant' or type_name=='Energy_plant':
        type_id='2'
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
    
            
    
    