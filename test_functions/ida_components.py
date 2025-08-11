from plugins.utility_functions.ida_components import *
from plugins.utility_functions.files import *


plugin_dir="""C:\\Users\\Peter\\AppData\\Roaming\\QGIS\\QGIS3\\profiles\\default\\python\\plugins\\"""
dictDB={'pwd' : 'p3t3r' , 'host' : 'localhost','port':'5433', 'user' : 'postgres', 'projectName' : 'test00001', 'versionName' : 'base1'}

dir=plugin_dir+'ida_data\\{}\\customer_templates\\1_2_Simple heating substation\\'.format(dictDB['projectName'])
#fname=dir+'1_2_Simple heating substation.idm'
# fname="""\\\\?\\C:\\Users\\Peter\\AppData\\Roaming\\QGIS\\QGIS3\\profiles\\default\\python\\plugins\\ida_mosim\\models\\test00001\\base1\\invoked_customers\\customer_1\\Customer_1.idm"""
# #print(fname)
# data=readFileToString(fname)
# #print(data)
# #print(getIDAListComponents(data))

# #print(getIDAListComponents(data))
# data_idm=propertyListCompsIDM(getIDAListComponents(data))
# #print(data_idm)

        
def getIDAListComponents(data):
    data=data.replace('""','$empty_str$')
    string_list = re.findall(r"\"([^\"]+)\"", data)    
    string_list=set(string_list)
    #print(string_list)
    # value_str=re.findall(r"\:VALUE\s+\(([A-Za-z0-9_\s+\-\$\\\<\>\=\:\"\/\'\;\,]+)\)", data)
    
    value_list=[]
    #print('-----++---')
    for value in re.findall(r"\:VALUE\s+\(([^\)]+)*\)", data):
        #print('++')
        #print(value)
        #print(re.search('[a-zA-Z]', value))
        if ':DICT ' not in value and re.search('[a-zA-Z]', value):
            #print('***')
            #print(value)
            value_list.append(value)
            data=data.replace(' ('+value+')','')
            #print(data)
    #print('--------------')
    #print(data)
    
    def replace_func(x):
        if x.group(1):
            return x.group(1)
        elif x.group(2):
            return x.group(2)
        elif x.group(3):
            return ':VALUE\',"""'+value_list.pop()+' """'
            
    for i,s in enumerate(sorted(list(string_list),key=len,reverse=True)):
        #print(s)
        data=data.replace('"'+s+'"','"${}$"'.format(i))
    #print(data)

    data=data.replace('\n',',')
    data=re.sub(r"\s+", " ", data)

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

    data=re.sub(r"\#3A\(", parse_hashtag3dimArray, data)
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

    for i,s in enumerate(sorted(list(string_list),key=len,reverse=True)):
        data=data.replace('"${}$"'.format(i),'"'+s.replace('\n',' ')+'"')

    #print(data)
    data=data.replace('\\','\\\\')
    #print(data)
    i=0
    
    #print('*-*-')
    #print(value_list)
    value_list.reverse()
    #print(value_list)

    if value_list:
        #print(value_list)
        # Pattern to match `:VALUE` followed by a quoted string (Group 3)
        pattern = r"(:VALUE','\")|(:VALUE',\[':DICT)|(:VALUE')"
        data = re.sub(pattern, replace_func, data)
        



        
    #print(data)
    data=data.replace('$empty_str$','""')

    return eval(data)
    
fname="""\\\\?\\C:\\Users\\Peter\\AppData\\Roaming\\QGIS\\QGIS3\\profiles\\default\\python\\plugins\\ida_mosim\\models\\test00001\\base1\\invoked_customers\\customer_1\\Customer_1.idc"""
#print(fname)
data=readFileToString(fname)
#print(data)

#print(getIDAListComponents(data))
klö
data_idc=propertyListCompsIDC(getIDAListComponents(data))
#print(data_idc)
         
#print(fname)         
#writePropertyListIDMToFile(data_idm,dir,fname)


