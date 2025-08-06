from pyparsing import OneOrMore, nestedExpr
from plugins.utility_functions.files import *
from plugins.utility_functions.ida_components import *
from plugins.utility_functions.db import *
import psycopg2.extras
import psycopg2
from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT
dictDB={'pwd' : 'p3t3r' , 'host' : 'localhost','port':'5433', 'user' : 'postgres', 'projectName' : 'cosim_test1', 'versionName' : 'b'}
conn=dbConnect(dictDB,True)
cur=conn.cursor(cursor_factory = psycopg2.extras.RealDictCursor)
import math
import os
import re

plugin_dir="""C:\\Users\\Peter\\AppData\\Roaming\\QGIS\\QGIS3\\profiles\\default\\python\\plugins\\"""
source_dir=plugin_dir+"ida_districts_modeling_simulation\\network_models\\cosim_test1\\b\\invoked_customers"

submodel=1
submodels=getUsedSubmodels(cur,dictDB)
submodels.remove(str(submodel))
features=getFeatureIds(dictDB,cur,submodel,submodels)
#print(features)
import_counter=0

def parse_bracketsBetweenAlphanumericCharAndOpenBracket(match_obj):
    return match_obj[0][0]+"',("
    
def parse_hashtagS(match_obj):
    return "#S',("
    
def parse_hashtag(match_obj):
    return "#',("
    
def parse_hashtag2dimArray(match_obj):
    return "#2A',("
 
def parse_closingBracketsConnectedToDigit(match_obj):
    return "),'"+match_obj[0][-1]

def parse_AlphanumericCharSeparatedOpeningBrackets(match_obj):
    return match_obj[0][0]+"',("
    
def parse_ClosingBracketsConnectedToAlphanumericChar(match_obj):
    return "),'" +match_obj[0][-1]

def getIDAListComponents(data):
    whitespace_string_list = re.findall(r"\"([A-Za-z0-9_\s+\-\$\\]+)\"", data)
    # value_str=re.findall(r"\:VALUE\s+\(([A-Za-z0-9_\s+\-\$\\\<\>\=\:\"\/\'\;\,]+)\)", data)

    
    re.findall(r"\:VALUE\s+\(([^\)]+)*\)", data)
    #print(re.findall(r"\:VALUE\s+\(([^\)]+)*\)", data))
    value_list=[]
    for value in re.findall(r"\:VALUE\s+\(([^\)]+)*\)", data):
        #print(value)
        if ':DICT ' not in value:
            value_list.append(value)
            data=data.replace(' ('+value+')','')
            #print(data)

    #print(data)

    #print(whitespace_strings)

    data=data.replace('\n',',')
    #print(data)
    #data=re.sub(r"\w\s+\(", parse_bracketsBetweenAlphanumericCharAndOpenBracket, data)
    data=re.sub(r'(\w\s+\()|(\"\s+\()|(\|\s+\()', parse_bracketsBetweenAlphanumericCharAndOpenBracket, data)
    #print(data)

    data=re.sub(r"\w,\s+\(", parse_AlphanumericCharSeparatedOpeningBrackets, data)
    #print(data)
    
    data=re.sub(r"(\)\s+\w)|(\)\s+\")|(\)\s+\|)", parse_ClosingBracketsConnectedToAlphanumericChar, data)
    #print(data)

    data=re.sub(r"\#\(", parse_hashtag, data)
    #print(data)
    
    data=re.sub(r"\#2A\(", parse_hashtag2dimArray, data)
    #print(data)

    data=re.sub(r"\#S\(", parse_hashtagS, data)
    #print(data)

    data=re.sub(r"\)\s+\:", "),':", data)
    #print(data)

    data=re.sub(r"\)\s+\d", parse_closingBracketsConnectedToDigit, data)

    data=re.sub(r"\)\s+", ")", data)
    #print(file)

    data=re.sub(r"\s+\(", '(', data)
    #print(data)

    data=data.replace("(((","[[[\'").replace("((","[[\'").replace("(","[\'").replace(")))))","\']]]]]").replace("))))","\']]]]").replace(")))","\']]]").replace("))","\']]").replace(")","\']").replace(" ","\',\'")
    data=data.replace("|inStream['","|inStream(").replace("']|",")|").replace('][','],[')

    for s in whitespace_string_list:
        if re.findall(r'\s+',s):
            data=data.replace(re.sub(r'\s+',"','",s),s)

    #print(data)
    data=data.replace('\\','\\\\')
    #print(data)
    i=0
    
    value_list.reverse()
    if value_list:
        #print(value_list)
        data=re.sub(r"(:VALUE',\[':DICT)|(\:VALUE')",lambda x: x.group(1) if x.group(1) is not None else ':VALUE\',"""'+value_list.pop()+' """',data)
    #print(data)
    
    return eval(data)
    
    
def propertyListCompsIDM(comps):
    return [propertyListIDM(comp) for comp in comps]
    
def propertyListCompsIDC(comps):
    return [propertyListIDC(comp) for comp in comps]

file="""(FRAME-BOX :VALUE (ENGLISH "Zone hot water" GERMAN "Heizkreis zu Zonen" FINNISH "Tilat lämmitys" FRENCH "Eau chaude vers les zones" SPANISH "Agua caliente hacia las zonas" SWEDISH "Värmebärare till zon" RUSSIAN "Горячая вода зоны" POLISH "Ciepła woda dla strefy") :HORIZONTAL :RIGHT :AT ((886 242) (1214 562)) :STYLE SECTION) 
(FRAME-BOX :VALUE (:DICT (GENERAL DOMESTIC-WATER)) :HORIZONTAL :RIGHT :AT ((886 107) (1102 219)) :STYLE SECTION) 
(TEXT-OBJECT :VALUE (ENGLISH "<meta name=\"sensor-description\"><b>Sensor descriptions:</b><br><b>Int_Ref_Sensor_Source_1</b> --> Source description=''; Target description=''; Sensor ID='1'; Source function='Individual signals for each target'; Source measure='Custom'; Target type='Supervisory control'; Target='Feature: 11, Connection type: X, Connection: X;Feature: 9, Connection type: X, Connection: X'<br>") :AT ((8 380) (694 430)) :STYLE NOTE :MARKUP HTML) """
#file=readFileToString(source_dir+'\\Customer_9.idc')
file_idm=readFileToString("C:\\Users/Peter/AppData/Roaming/QGIS/QGIS3\\profiles\\default/python/plugins\\ida_districts_modeling_simulation\\network_models\\cosim_test1\\b\\invoked_customers\\customer_9\\Customer_9.idm")
file_idc=readFileToString("C:\\Users/Peter/AppData/Roaming/QGIS/QGIS3\\profiles\\default/python/plugins\\ida_districts_modeling_simulation\\network_models\\cosim_test1\\b\\invoked_customers\\customer_9\\Customer_9.idc")


data=getIDAListComponents(file)
#print(data)
#print(propertyListCompsIDC(data))

#pData_idm=propertyListCompsIDM(getIDAListComponents(file_idm))
#print(pData_idm)

#print(getIDAListComponents(file_idc))
pData_idc=propertyListCompsIDC(getIDAListComponents(file_idc))
#print(pData_idc)