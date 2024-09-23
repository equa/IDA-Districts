from plugins.utility_functions.ida_components import *
from plugins.utility_functions.files import *


plugin_dir="""C:\\Users\\Peter\\AppData\\Roaming\\QGIS\\QGIS3\\profiles\\default\\python\\plugins\\"""
dictDB={'pwd' : 'p3t3r' , 'host' : 'localhost','port':'5433', 'user' : 'postgres', 'projectName' : 'test15', 'versionName' : 'a'}


def getIDAListComponents(data):
    data=data.replace('""','$empty_str$')
    string_list = re.findall(r"\"([^\"]+)\"", data)    
    print(string_list)
    #string_list=[i.replace('\n','$new_line$') for i in string_list]
    #print(string_list)
    #string_list=set(['"'+i+'"' for i in string_list])
    string_list=set(string_list)
    print(string_list)
    # value_str=re.findall(r"\:VALUE\s+\(([A-Za-z0-9_\s+\-\$\\\<\>\=\:\"\/\'\;\,]+)\)", data)
    
    value_list=[]
    for value in re.findall(r"\:VALUE\s+\(([^\)]+)*\)", data):
        #print(value)
        if ':DICT ' not in value and re.search('[a-zA-Z]', value):
            value_list.append(value)
            data=data.replace(' ('+value+')','')
            #print(data)

    #print(data)

    for i,s in enumerate(sorted(list(string_list),key=len,reverse=True)):
        #print(i)
        #print(s)
        data=data.replace('"'+s+'"','"${}$"'.format(i))
    print(data)
    data=data.replace('\n',',')
    data=re.sub(r"\s+", " ", data)
    #print(data)
    #data=re.sub(r"\w\s+\(", parse_bracketsBetweenAlphanumericCharAndOpenBracket, data)
    data=re.sub(r'(\w\s+\()|(\"\s+\()|(\|\s+\()', parse_bracketsBetweenAlphanumericCharAndOpenBracket, data)
    print(data)

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

    data=data.replace("(((","[[[\'").replace("((","[[\'").replace("(","[\'").replace("))))))","\']]]]]]").replace(")))))","\']]]]]").replace("))))","\']]]]").replace(")))","\']]]").replace("))","\']]").replace(")","\']").replace(" ","\',\'")
    data=data.replace("|inStream['","|inStream(").replace("']|",")|").replace('][','],[')
    print(data)

    for i,s in enumerate(sorted(list(string_list),key=len,reverse=True)):
        data=data.replace('"${}$"'.format(i),'"'+s.replace('\n',' ')+'"')

    print(data)

    data=data.replace('\\','\\\\')
    #print(data)
    i=0
    
    value_list.reverse()
    if value_list:
        #print(value_list)
        data=re.sub(r"(:VALUE',\[':DICT)|(\:VALUE')",lambda x: x.group(1) if x.group(1) is not None else ':VALUE\',"""'+value_list.pop()+' """',data)
        #data=re.sub(r":VALUE'",lambda x: x[0],data)
    data=data.replace('$empty_str$','""')
    print(data)

    return eval(data)
    
data="""(DOCUMENT-HEADER :TYPE ICE-SYSTEM :N "network_1" :ETM 3928487395 :MS 6 :PARENT ICE :APP (ICE :VER 5.09002)) 
((SCHEDULE-DATA :N "Shading" :T SCHEDULE-DATA :QT GENERIC)
 (SCHEDULE-RULE :N "rule-2" :D "rule-2" :START-DATE (NIL 5 1) :END-DATE (NIL 9 30) :VALUE ((24.0 0.86)))
 (SCHEDULE-RULE :N "default" :VALUE ((24 1)) :INDEX 1))"""

dir=plugin_dir+'ida_districts_modeling_simulation\\network_models\\{}\\{}\\'.format(dictDB['projectName'],dictDB['versionName'])
fname=dir+'network_1.idm'

data=readFileToString(fname)
#print(getIDAListComponents(data))

data_idm=propertyListCompsIDM(getIDAListComponents(data))
print(data_idm)

         
print(fname)         
writePropertyListIDMToFile(data_idm,dir,fname)


