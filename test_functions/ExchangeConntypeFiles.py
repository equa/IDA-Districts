from plugins.utility_functions.files import *
from plugins.utility_functions.db import *
from plugins.utility_functions.sensor_signals import *
from plugins.utility_functions.topology import *
from plugins.utility_functions.ida_components import *

import psycopg2.extras
import psycopg2
from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT
plugin_dir="""C:\\Users\\Peter\\AppData\\Roaming\\QGIS\\QGIS3\\profiles\\default\\python\\plugins\\"""
dictDB={'pwd' : 'p3t3r' , 'host' : 'localhost','port':'5434', 'user' : 'postgres', 'projectName' : 'test22', 'versionName' : 'a'}

#dictDB=getDBConnectionData(plugin_dir)
conn=dbConnect(dictDB,True)
cur=conn.cursor(cursor_factory = psycopg2.extras.RealDictCursor)
#print(cur)
test_file='test'
class ExchangeConntypeFiles:
    """ Exchanges connection types: 1) Removes the old connection type; 2) add the new connection type !!!!To do!!!!"""
    def __init__(self,plugin_dir,name,type,b_conn_t,b_conn_t_old,cur,oldConnValues=[]):
        #print('*********ExchangeConntypeFiles********')
        self.plugin_dir=plugin_dir
        self.dictDB=getDBConnectionData(self.plugin_dir)
        dir=self.plugin_dir+"\\"+self.dictDB['projectName']+"\\{}_templates".format(type)
        
        if not oldConnValues:
            oldConnValues=getConnsValues(b_conn_t_old,cur)
        connValues=getConnsValues(b_conn_t,cur)
        #print(oldConnValues)
        
        file_data=readFileToList(dir+'\\'+name+'.idm')
        file_data=self.delPMT2Comp(file_data,oldConnValues)      
        file_data=self.delConnection(file_data,oldConnValues)
        
        writeToFileFromList(file_data,dir,dir+'\\'+test_file+'.idm') 
        data=[]
        connections=False
        for line in file_data:
            data.append(line)
            if """(MACRO-OBJECT :N "{}\"""".format(name) in line:
                idx=file_data.index(line)
                if file_data[idx].count('(')-file_data[idx].count(')')==0:
                    data[-1]=data[-1].replace('\n','').rstrip()[:-1]+'\n'
                    data.append('\n'.join([""" (:IREF :N "{}_{}_{}_{}" :F 192)""".format(conn['conn_bundle_type_id'],conn['conn_type_seq'],conn['conn_type_id'],conn['conn_seq']) for conn in connValues]))
                    data[-1]+=")\n"
                else:
                    data.append(''.join([""" (:IREF :N "{}_{}_{}_{}" :F 192)\n""".format(conn['conn_bundle_type_id'],conn['conn_type_seq'],conn['conn_type_id'],conn['conn_seq']) for conn in connValues]))
            if """(CONNECTIONS""" in line:
                #print('***Connections***')
                openCloseBracktesCounter=line.count('(')-line.count(')')
                connections=True
                del data[-1]
                for conn in connValues:
                    name_pmtmux="{}_{}_{}_{}".format(conn['conn_bundle_type_id'],conn['conn_type_seq'],conn['conn_type_id'],conn['conn_seq'])
                    if conn['p']!=None:
                        variable="P"
                        var_value=conn['p']
                        
                    if conn['mdot']!=None:
                        variable="M"
                        var_value=conn['mdot']
                    data.append("""((MODEL :N "{}" :T PMT2\\m\\u\\x)
 (:VAR :N |{}_var| :B (-1 {} 0))
 ((CONNECTOR :N |term_a|)
  (:VAR :N |inStream(T)| :B {})))\n""".format(name_pmtmux,variable,variable,conn['temp']))
                    name_const="{}_{}_{}_{}_{}{}".format(conn['conn_bundle_type_id'],conn['conn_type_seq'],conn['conn_type_id'],conn['conn_seq'],variable,var_value)
                    data.append("""((SOURCE-CONSTANT :N "{}" :T CONSTANT)
 (:PAR :N X :V {}))  \n""".format(name_const,var_value))
 
                data.append("(CONNECTIONS\n")
                for value in connValues:
                    name_pmtmux="{}_{}_{}_{}".format(value['conn_bundle_type_id'],value['conn_type_seq'],value['conn_type_id'],value['conn_seq'])
                    if value['p']!=None:
                        name_const="{}_{}_{}_{}_P{}".format(value['conn_bundle_type_id'],value['conn_type_seq'],value['conn_type_id'],value['conn_seq'],value['p'])
                        variable="P"
                    else:
                        name_const="{}_{}_{}_{}_M{}".format(value['conn_bundle_type_id'],value['conn_type_seq'],value['conn_type_id'],value['conn_seq'],value['mdot'])
                        variable="M"
                    data.append(""" (("{}" "{}") ("{}" |term_b|) 0 2 NIL)
 (("{}" {}) ("{}" LINK) 0 0 NIL)\n""".format(name,name_pmtmux,name_pmtmux,name_pmtmux,variable,name_const))
                if openCloseBracktesCounter==0:
                    data[-1]=data[-1].rstrip()+")"

        if not connections:  
            for conn in connValues:
                name_pmtmux="{}_{}_{}_{}".format(conn['conn_bundle_type_id'],conn['conn_type_seq'],conn['conn_type_id'],conn['conn_seq'])
                if conn['p']!=None:
                    variable="P"
                    var_value=conn['p']
                    
                if conn['mdot']!=None:
                    variable="M"
                    var_value=conn['mdot']
                data.append("""((MODEL :N "{}" :T PMT2\\m\\u\\x)
 (:VAR :N |{}_var| :B (-1 {} 0))
 ((CONNECTOR :N |term_a|)
  (:VAR :N |inStream(T)| :B {})))\n""".format(name_pmtmux,variable,variable,conn['temp']))
                name_const="{}_{}_{}_{}_{}{}".format(conn['conn_bundle_type_id'],conn['conn_type_seq'],conn['conn_type_id'],conn['conn_seq'],variable,var_value)
                data.append("""((SOURCE-CONSTANT :N "{}" :T CONSTANT)
 (:PAR :N X :V {}))  \n""".format(name_const,var_value))        
            data.append("(CONNECTIONS\n")
            for value in connValues:
                name_pmtmux="{}_{}_{}_{}".format(value['conn_bundle_type_id'],value['conn_type_seq'],value['conn_type_id'],value['conn_seq'])
                if value['p']!=None:
                    name_const="{}_{}_{}_{}_P{}".format(value['conn_bundle_type_id'],value['conn_type_seq'],value['conn_type_id'],value['conn_seq'],value['p'])
                    variable="P"
                else:
                    name_const="{}_{}_{}_{}_M{}".format(value['conn_bundle_type_id'],value['conn_type_seq'],value['conn_type_id'],value['conn_seq'],value['mdot'])
                    variable="M"
                data.append(""" (("{}" "{}") ("{}" |term_b|) 0 2 NIL)
 (("{}" {}) ("{}" LINK) 0 0 NIL)\n""".format(name,name_pmtmux,name_pmtmux,name_pmtmux,variable,name_const))
            data[-1]=data[-1].rstrip()+")"
        writeToFileFromList(data,dir,dir+'\\'+name+'_test.idm')    
        

        
        filedata=readFileToList(dir+'\\'+name+'.idc')
        filedata=self.delConnection(filedata,oldConnValues)
        counter_p=0
        counter_mdot=0
        for value in connValues:
            name_pmtmux="{}_{}_{}_{}".format(value['conn_bundle_type_id'],value['conn_type_seq'],value['conn_type_id'],value['conn_seq'])
            if value['p']!=None:
                name_const="{}_{}_{}_{}_P{}".format(value['conn_bundle_type_id'],value['conn_type_seq'],value['conn_type_id'],value['conn_seq'],value['p'])
                variable="p"
                y=240+counter_p*40
                filedata.append("""(EQUATION-FRAME :AT ((96 {})) :R (9 18.5) :ICON "lib:pmt2mux.ids" :SYMMETRY (180.0) :SLOT ("{}") :NAME "{}" :DATA :EO)\n""".format(y,name_pmtmux,name_pmtmux))
                y=227+counter_p*40
                filedata.append("""(EQUATION-FRAME :AT ((29 {})) :R (28 10) :ICON "sys:constant.ids" :SLOT ("{}") :NAME "{}" :DATA SOURCE-CONSTANT)\n""".format(y,name_const,name_const))
                y=232+counter_p*40
                filedata.append("""(CONNECTION-LINE :AT ((106 {}) (148 {})) :LINE-COLOR (:CALL PMT-COLOR [@ 1] [@ 2]) :LINE-STYLE 3 :FIRST-LINK ("{}" (1 0.278) |term_b|) :LAST-LINK ("{}" (0.0 0.04) "{}"))\n""".format(y,y,name_pmtmux,name,name_pmtmux))
                y=227+counter_p*40
                filedata.append("""(CONNECTION-LINE :AT ((307/5 {}) (87 {})) :FIRST-LINK ("{}" (1 0.5) LINK) :LAST-LINK ("{}" (0.0 0.139) {}) :DIR :RIGHT :ARROW (19 8 8))\n""".format(y,y,name_const,name_pmtmux,variable))
                counter_p+=1
            else:
                name_const="{}_{}_{}_{}_M{}".format(value['conn_bundle_type_id'],value['conn_type_seq'],value['conn_type_id'],value['conn_seq'],value['mdot'])
                variable="M"
                y=240+counter_mdot*40
                filedata.append("""(EQUATION-FRAME :AT ((597 {})) :R (9 18.5) :ICON "lib:pmt2mux.ids" :SLOT ("{}") :NAME "{}" :DATA :EO)\n""".format(y,name_pmtmux,name_pmtmux))
                filedata.append("""(EQUATION-FRAME :AT ((667 {})) :R (28 10) :ICON "sys:constant.ids" :SYMMETRY (180.0) :SLOT ("{}") :NAME "{}" :DATA SOURCE-CONSTANT)\n""".format(y,name_const,name_const))
                filedata.append("""(CONNECTION-LINE :AT ((635 {}) (606 {})) :FIRST-LINK ("{}" (1.0 0.5) {}) :LAST-LINK ("{}" (0 0.5) LINK) :DIR :LEFT :ARROW (19 8 8))\n""".format(y,y,name_pmtmux,variable,name_const))
                y=232+counter_mdot*40
                filedata.append("""(CONNECTION-LINE :AT ((587 {}) (556 {})) :LINE-COLOR (:CALL PMT-COLOR [@ 1] [@ 2]) :LINE-STYLE 3 :FIRST-LINK ("{}" (1 0.278) |term_b|) :LAST-LINK ("{}" (0.0 0.04) "{}"))\n""".format(y,y,name_pmtmux,name,name_pmtmux))
                counter_mdot+=1
        writeToFileFromList(filedata,dir,dir+'\\'+name+'_test.idc') 

        #template macro
        dir=dir+'\\'+name
        filedata=readFileToList(dir+'\\'+name+'.idm')
        filedata=self.delPMT2Comp(filedata,oldConnValues)
        filedata=self.delConnection(filedata,oldConnValues)
        
        meters=[]
        meter={'name':'','n_sup':0,'n_ret':0,'sup_conn':[],'ret_conn':[],'p':True}
        conn_type_old=0        
        i=0
        p_old=True
        p_old_old=True
        for value in connValues:
            name_pmtmux="{}_{}_{}_{}".format(value['conn_bundle_type_id'],value['conn_type_seq'],value['conn_type_id'],value['conn_seq'])
            filedata.insert(2,"""(:IREF :N "{}" :F 192)\n""".format(name_pmtmux))
            filedata.insert(2,"""(MODEL :N "PMT2mux_{}" :T PMT2\\m\\u\\x)\n""".format(name_pmtmux))
            if value['mdot']!=None:
                meter['p']=False
            if value['type']==1:
                meter['n_sup']+=1
                meter['sup_conn'].append('PMT2mux_{}'.format(name_pmtmux))
            elif value['type']==2:
                meter['n_ret']+=1
                meter['ret_conn'].append('PMT2mux_{}'.format(name_pmtmux))
            meter['name']=str(value['conn_bundle_type_id'])+'_'+str(value['conn_type_seq'])
            if value['conn_type_id']!=conn_type_old and i!=0:
                if value['type']==1:
                    meters.append({'name': meter_name_old_old,'n_sup':meter['n_sup']-1,'n_ret':meter['n_ret'],'sup_conn':meter['sup_conn'][:-1],'ret_conn':meter['sup_conn'],'p': p_old_old})
                    meter={'name':'','n_sup':1,'n_ret':0,'sup_conn':[meter['sup_conn'][-1]],'ret_conn':[],'p':True}
                elif value['type']==2:
                    meters.append({'name': meter_name_old_old,'n_sup':meter['n_sup'],'n_ret':meter['n_ret']-1,'sup_conn':meter['sup_conn'],'ret_conn':meter['sup_conn'][:-1],'p': p_old_old})
                    meter={'name':'','n_sup':0,'n_ret':1,'sup_conn':[],'ret_conn': [meter['ret_conn'][-1]],'p':True}
                if value['mdot']!=None:
                    meter['p']=False
            i+=1
            conn_type_old=value['conn_type_id']
            p_old=meter['p']
            p_old_old=p_old
            meter_name_old=meter['name']
            meter_name_old_old=meter_name_old
        meters.append(meter)   
        #print(meters)
        for meter in meters:
            sup_m_conn=' '.join(['('+str(meter['sup_conn'].index(i)+1)+' :MACRO "'+i+'" |M_var|)' for i in meter['sup_conn']])
            sup_t_conn=sup_m_conn.replace('|M_var|','|T_var|')
            ret_m_conn=' '.join(['('+str(meter['ret_conn'].index(i)+1)+' :MACRO "'+i+'" |M_var|)' for i in meter['ret_conn']])
            ret_t_conn=ret_m_conn.replace('|M_var|','|T_var|')
            filedata.insert(2,"""((:EO :N "{}_Flowmeter2" :T FLOWMETER2)
 (:PAR :N N_SUP :V {})
 (:PAR :N N_RET :V {})
 (:VAR :N FLOW_SUP :DIM ({}) :B #S(MS-SPARSE DEFAULT-VALUE NIL DIMENSION 1 VALUE ({})))
 (:VAR :N TSUP :DIM ({}) :B #S(MS-SPARSE DEFAULT-VALUE NIL DIMENSION 1 VALUE ({})))
 (:VAR :N FLOW_RET :DIM ({}) :B #S(MS-SPARSE DEFAULT-VALUE NIL DIMENSION 1 VALUE ({})))
 (:VAR :N TRET :DIM ({}) :B #S(MS-SPARSE DEFAULT-VALUE NIL DIMENSION 1 VALUE ({}))))\n""".format(meter['name'],meter['n_sup'],meter['n_ret'],meter['n_sup'],sup_m_conn,meter['n_sup'],sup_t_conn,meter['n_ret'],ret_m_conn,meter['n_ret'],ret_t_conn))
        
        data=[]
        connections=False
        for line in filedata:
            data.append(line)
            if """(CONNECTIONS""" in line:
                openCloseBracktesCounter=line.count('(')-line.count(')')
                connections=True
                del data[-1]
                data.append('(CONNECTIONS\n')
                for value in connValues:
                    name_pmtmux="{}_{}_{}_{}".format(value['conn_bundle_type_id'],value['conn_type_seq'],value['conn_type_id'],value['conn_seq'])
                    data+="""(("PMT2mux_{}" |term_b|) "{}" 0 0 NIL)\n""".format(name_pmtmux,name_pmtmux)
                if openCloseBracktesCounter==0:
                    data[-1]=data[-1].rstrip()+")"
        if not connections: 
            data.append('(CONNECTIONS\n')
            for value in connValues:
                name_pmtmux="{}_{}_{}_{}".format(value['conn_bundle_type_id'],value['conn_type_seq'],value['conn_type_id'],value['conn_seq'])
                data+="""(("PMT2mux_{}" |term_b|) "{}" 0 0 NIL)\n""".format(name_pmtmux,name_pmtmux)
            data[-1]=data[-1].rstrip()+")"    
        
        writeToFileFromList(data,dir,dir+'\\'+name+'test_.idm')     
        
        filedata=readFileToList(dir+'\\'+name+'.idc')
        filedata=self.delPMT2Comp(filedata,oldConnValues)
        filedata=self.delConnection(filedata,oldConnValues)
        counter_p=0
        counter_mdot=0
        for value in connValues:
            name_pmtmux="{}_{}_{}_{}".format(value['conn_bundle_type_id'],value['conn_type_seq'],value['conn_type_id'],value['conn_seq'])
            if value['p']!=None:
                name_const="{}_{}_{}_{}_P{}".format(value['conn_bundle_type_id'],value['conn_type_seq'],value['conn_type_id'],value['conn_seq'],value['p'])
                variable="P"
                y=37+counter_p*45
                filedata.append("""(CONNECTION-LINE :AT ((10 {}) (50 {})) :LINE-COLOR (:CALL PMT-COLOR [@ 1] [@ 2]) :LINE-STYLE 3 :FIRST-LINK (:SELF (0.0 0.094) "{}") :LAST-LINK ("PMT2mux_{}" (0 0.278) |term_b|))\n""".format(y,y,name_pmtmux,name_pmtmux))
                y=45+counter_p*45
                filedata.append("""(EQUATION-FRAME :AT ((59 {})) :R (8 18) :ICON "lib:pmt2mux.ids" :SLOT ("PMT2mux_{}") :NAME "PMT2mux_{}" :DATA :EO)\n""".format(y,name_pmtmux,name_pmtmux))
                counter_p+=1
            else:
                name_const="{}_{}_{}_{}_M{}".format(value['conn_bundle_type_id'],value['conn_type_seq'],value['conn_type_id'],value['conn_seq'],value['mdot'])
                variable="M"
                y=37+counter_mdot*45
                filedata.append("""(CONNECTION-LINE :AT ((694 {}) (641 {})) :LINE-COLOR (:CALL PMT-COLOR [@ 1] [@ 2]) :LINE-STYLE 3 :FIRST-LINK (:SELF (0.0 0.094) "{}") :LAST-LINK ("PMT2mux_{}" (0 0.278) |term_b|))\n""".format(y,y,name_pmtmux,name_pmtmux))
                y=45+counter_mdot*45
                filedata.append("""(EQUATION-FRAME :AT ((636 {})) :R (8 18) :ICON "lib:pmt2mux.ids" :SYMMETRY (180) :SLOT ("PMT2mux_{}") :NAME "PMT2mux_{}" :DATA :EO)\n""".format(y,name_pmtmux,name_pmtmux))
                counter_mdot+=1
                
        counter_emeter=0
        for meter in meters:
            x=29+counter_emeter*35
            filedata.append("""\n(EQUATION-FRAME :AT (({} 346)) :R (13.5 13.0) :ICON "sys:eo.ids" :SLOT ("{}_Flowmeter2") :NAME "{}_Flowmeter2" :DATA :EO) """.format(x,meter['name'],meter['name']))    
            counter_emeter+=1                
        writeToFileFromList(filedata,dir,dir+'\\'+name+'_test.idc') 
        #print('exchange conn bundle type finished')
        
    def delConnection(self,file_data,oldConnValues):
        data=[]
        #print('del Connection')
        for line in file_data:
            if [True for conn in 
                ["""\"{}_{}_{}_{}_M{}\"""".format(conn['conn_bundle_type_id'],conn['conn_type_seq'],conn['conn_type_id'],conn['conn_seq'],conn['mdot']) for conn in oldConnValues]+
                ["""\"{}_{}_{}_{}_P{}\"""".format(conn['conn_bundle_type_id'],conn['conn_type_seq'],conn['conn_type_id'],conn['conn_seq'],conn['p']) for conn in oldConnValues]+
                ["""\"{}_{}_{}_{}\"""".format(conn['conn_bundle_type_id'],conn['conn_type_seq'],conn['conn_type_id'],conn['conn_seq']) for conn in oldConnValues]+
                ["""\"PMT2mux_{}_{}_{}_{}\"""".format(conn['conn_bundle_type_id'],conn['conn_type_seq'],conn['conn_type_id'],conn['conn_seq']) for conn in oldConnValues]+ 
                ["""\"{}_{}_Flowmeter2\"""".format(conn['conn_bundle_type_id'],conn['conn_type_seq']) for conn in oldConnValues]
                if conn in line]:
                #print('del connection')
                #print(line)
                data[-1]=data[-1].replace('\n','')+''.join([')' for i in range(line.count(')')-line.count('('))])+'\n'
            else:
                data.append(line)
        return data
    
    def delPMT2Comp(self,file_data,oldConnValues):
        data=[]
        del_index=[]
        counter=0
        #print('-------------del comp----------')
        while counter < len(file_data):
            while [True for conn in 
                ["""SOURCE-CONSTANT :N "{}_{}_{}_{}_M{}\"""".format(conn['conn_bundle_type_id'],conn['conn_type_seq'],conn['conn_type_id'],conn['conn_seq'],conn['mdot']) for conn in oldConnValues]+
                ["""SOURCE-CONSTANT :N "{}_{}_{}_{}_P{}\"""".format(conn['conn_bundle_type_id'],conn['conn_type_seq'],conn['conn_type_id'],conn['conn_seq'],conn['p']) for conn in oldConnValues]+
                ["""(MODEL :N "{}_{}_{}_{}\"""".format(conn['conn_bundle_type_id'],conn['conn_type_seq'],conn['conn_type_id'],conn['conn_seq']) for conn in oldConnValues]+
                ["""(MODEL :N "PMT2mux_{}_{}_{}_{}\"""".format(conn['conn_bundle_type_id'],conn['conn_type_seq'],conn['conn_type_id'],conn['conn_seq']) for conn in oldConnValues]+
                ["""(:EO :N "{}_{}_Flowmeter2" :T FLOWMETER2)""".format(conn['conn_bundle_type_id'],conn['conn_type_seq']) for conn in oldConnValues]
                if conn in file_data[counter]]:
                data[-1]=data[-1].replace('\n','')+''.join([')' for i in range(file_data[counter].count(')')-file_data[counter].count('('))])+'\n'
                openCloseBracktesCounter=file_data[counter].count('(')-file_data[counter].count(')')
                #print(openCloseBracktesCounter)
                counter+=1
                while openCloseBracktesCounter>0:
                    #print(file_data[counter])
                    openCloseBracktesCounter+=file_data[counter].count('(')-file_data[counter].count(')')
                    counter+=1
                    if counter>=len(file_data):
                        break
                if counter>=len(file_data):
                    break
            if counter>=len(file_data):
                break
            data.append(file_data[counter])
            counter+=1
        return data

def delPMT2Comp(file_data,oldConnValues):
    data=[]
    del_index=[]
    counter=0
    #print('-------------del comp----------')
    while counter < len(file_data):
        while [True for conn in 
            ["""SOURCE-CONSTANT :N "{}_{}_{}_{}_M{}\"""".format(conn['conn_bundle_type_id'],conn['conn_type_seq'],conn['conn_type_id'],conn['conn_seq'],conn['mdot']) for conn in oldConnValues]+
            ["""SOURCE-CONSTANT :N "{}_{}_{}_{}_P{}\"""".format(conn['conn_bundle_type_id'],conn['conn_type_seq'],conn['conn_type_id'],conn['conn_seq'],conn['p']) for conn in oldConnValues]+
            ["""(MODEL :N "{}_{}_{}_{}\"""".format(conn['conn_bundle_type_id'],conn['conn_type_seq'],conn['conn_type_id'],conn['conn_seq']) for conn in oldConnValues]+
            ["""(MODEL :N "PMT2mux_{}_{}_{}_{}\"""".format(conn['conn_bundle_type_id'],conn['conn_type_seq'],conn['conn_type_id'],conn['conn_seq']) for conn in oldConnValues]+
            ["""(:EO :N "{}_{}_Flowmeter2" :T FLOWMETER2)""".format(conn['conn_bundle_type_id'],conn['conn_type_seq']) for conn in oldConnValues]
            if conn in file_data[counter]]:
            data[-1]=data[-1].replace('\n','')+''.join([')' for i in range(file_data[counter].count(')')-file_data[counter].count('('))])+'\n'
            openCloseBracktesCounter=file_data[counter].count('(')-file_data[counter].count(')')
            #print(openCloseBracktesCounter)
            counter+=1
            while openCloseBracktesCounter>0:
                #print(file_data[counter])
                openCloseBracktesCounter+=file_data[counter].count('(')-file_data[counter].count(')')
                counter+=1
                if counter>=len(file_data):
                    break
            if counter>=len(file_data):
                break
        if counter>=len(file_data):
            break
        data.append(file_data[counter])
        counter+=1
    return data
        
#print(getConnsValues(1,cur))

ats=getTemplatesByConnBundleType(cur,dictDB,1)
        
oldConnValues_dict={'1_4_Heating and Cooling 1 Supply & 1 Return': [{'conn_bundle_type_id': 1, 'conn_type_seq': 1, 'conn_type_id': 3, 'conn_seq': 1, 'temp': 18, 'p': 100000, 'mdot': None, 'type': 1, 'conn_id': 5}, {'conn_bundle_type_id': 1, 'conn_type_seq': 1, 'conn_type_id': 3, 'conn_seq': 2, 'temp': 10, 'p': 0, 'mdot': None, 'type': 2, 'conn_id': 6}]}

name='1_4_Heating and Cooling 1 Supply & 1 Return'
type='customer'
b_conn_t=1
b_conn_t_old=1
ExchangeConntypeFiles(plugin_dir+'ida_districts_data_center',name,type,b_conn_t,b_conn_t_old,cur,oldConnValues=oldConnValues_dict['1_4_Heating and Cooling 1 Supply & 1 Return'])