file_data=['hi',"""((SOURCE-FILE :DOCUMENT-PATH "$plugins_path$\\ida_data\\Samples\\DHW\\dhw_150_l7day.prn" :SF "$plugins_path$\\ida_data\\Samples\\DHW\\dhw_150_l7day.prn" :N "SOURCE-FILE_DHW" :T SOURCE-FILE :COL T)""",
    """((MODEL :N "load model" :T |lM_H_G_L|)""",
    """ (:VAR :N |PhiSolar| :L "Heat Balance")""",
    """(:VAR :N |PhiSolar| :L "Heat Balance"))""",
    'ho']

replaceDict={"SOURCE-FILE_DHW": 'test.prn', """((MODEL :N "load model\"""": {"|FloorArea|": 111,"|U|": 1}}

def replaceKeywordsInFiledata(file_data,replaceDict):
    data=[]
    counter=0
    while counter < len(file_data):
        replace=[key for key in replaceDict if key in file_data[counter]]
        if replace:
            if replace[0]=="SOURCE-FILE_DHW":
                #print('DWH')
                data.append("""((SOURCE-FILE :DOCUMENT-PATH "{}" :SF "{}" :N "SOURCE-FILE_DHW" :T SOURCE-FILE :COL T)""".format(replaceDict[replace[0]],replaceDict[replace[0]]))
            if replace[0]=="((MODEL :N \"load model\"":
                #print('load model')
                openCloseBracktesCounter=file_data[counter].count('(')-file_data[counter].count(')')
                if openCloseBracktesCounter>0:
                    data.append(file_data[counter])
                    counter+=1
                    parms=[]
                    while openCloseBracktesCounter>0:
                        openCloseBracktesCounter+=file_data[counter].count('(')-file_data[counter].count(')')
                        if "(:PAR :N " in file_data[counter]:
                            #print('par')
                            par_name=file_data[counter].split(':N "')[1].split('" :V')[0]
                            #print(par_name)
                            #print(replaceDict["""((MODEL :N "load model\""""])
                            replace_value=[replaceDict["""((MODEL :N "load model\""""][i] for i in replaceDict["""((MODEL :N "load model\""""] if i == par_name]
                            if replace_value:
                                replace_value=str(replace_value[0])
                                data.append('(:PAR :N'+par_name+' :V '+replace_value+('))' if openCloseBracktesCounter==0 else ')'))
                            else:   
                                data.append(file_data[counter])
                            parms.append(par_name)
                        if " (:VAR :N " in file_data[counter]:
                            #print('var')
                            #print(file_data[counter])
                            #print(parms)
                            #print(["(:PAR :N {} :V {})".format(i,replaceDict["""((MODEL :N "load model\""""][i]) for i in replaceDict["""((MODEL :N "load model\""""] if i not in parms])
                            data+=["(:PAR :N {} :V {})".format(i,replaceDict["""((MODEL :N "load model\""""][i]) for i in replaceDict["""((MODEL :N "load model\""""] if i not in parms]
                            data.append(file_data[counter])
                            break
                        if openCloseBracktesCounter!=0:
                            counter+=1
                        if counter>=len(file_data):
                            break 
                else:
                    data.append(file_data[counter].strip()[:-1])
                    #print('fd')
                    data+=["(:PAR :N {} :V {})".format(i,replaceDict["""((MODEL :N "load model\""""][i]) for i in replaceDict["""((MODEL :N "load model\""""]]
                    data[-1]=data[-1]+")"
                    
  
        else:
            data.append(file_data[counter])
        counter+=1
    return data
    
#print(replaceKeywordsInFiledata(file_data,replaceDict))