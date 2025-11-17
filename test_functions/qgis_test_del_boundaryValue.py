from plugins.utility_functions.topology import *
from plugins.utility_functions.utility import *
from plugins.utility_functions.db import *
from plugins.utility_functions.ida_components import *
from plugins.utility_functions.files import *

import psycopg2.extras
import psycopg2
from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT

plugin_dir="""C:\\Users\\Peter\\AppData\\Roaming\\QGIS\\QGIS3\\profiles\\default\\python\\plugins\\"""
dictDB={'pwd' : 'p3t3r' , 'host' : 'localhost','port':'5433', 'user' : 'postgres', 'projectName' : 'test21', 'versionName' : 'a'}
#dictDB=getDBConnectionData(plugin_dir)
conn=dbConnect(dictDB,True)
cur=conn.cursor(cursor_factory = psycopg2.extras.RealDictCursor)
print(cur)

template_idm=plugin_dir+"ida_data\\test21\\customer_templates\\1_1_Heating 1 Supply & 1 Return.idm"
template_idc=plugin_dir+"ida_data\\test21\\customer_templates\\1_1_Heating 1 Supply & 1 Return.idc"

components_idm=propertyListCompsIDM(getIDAListComponents(readFileToString(template_idm)))
components_idc=propertyListCompsIDC(getIDAListComponents(readFileToString(template_idc)))

changedValues={}
changedValues[1]={'p': {'old': '5000','new': False},'m':{'old': False,'new':'45'},'T':'60','ctrl':True}
print(changedValues)
connsValues=getConnsValuesByTemplate('customer',1,1,cur,dictDB)
print(connsValues)

def updatePMT2CompBoundaries(comp,pmt2_update_dict):
    new_comp=[]
    print(comp)
    for i in comp:
        print("class: {}; name: {}".format(getCompClass(i),getCompName(i)))
        if getCompClass(i)==':VAR' and getCompName(i) in pmt2_update_dict[getCompName(comp)]['disconnect']:
            print('disconnect')
            pass
        elif getCompClass(i)=='CONNECTOR' and pmt2_update_dict[getCompName(comp)]['update']:
            new_connector=[]
            for j in i:
                if getCompName(j)=='|inStream(T)|':
                    j[':B']=pmt2_update_dict[getCompName(comp)]['update']
                new_connector.append(j)
            print(new_comp)
            new_comp.append(new_connector)
        else:
            new_comp.append(i)
    if pmt2_update_dict[getCompName(comp)]['connect']=='|M_var|':
        new_comp.append({':C': ':VAR', ':N': '|M_var|', ':B': '(-1 M 0)'})
    elif pmt2_update_dict[getCompName(comp)]['connect']=='|P_var|':
        new_comp.append({':C': ':VAR', ':N': '|P_var|', ':B': '(-1 P 0)'})
    print(new_comp)
    return new_comp

def getBoundaryUpdateData(connsValues,changedValues):
    pmt2_update_dict={}
    add_constants={}
    del_constants=[]
    for connValues in connsValues:
        if connValues['conn_id'] in changedValues:
            print(connValues)
            PMT2muxName='"{}_{}_{}_{}"'.format(connValues['conn_bundle_type_id'],connValues['conn_type_seq'],connValues['conn_type_id'],connValues['conn_seq'])
            print(PMT2muxName)
            if changedValues[connValues['conn_id']]['ctrl']=='unchanged':
                disconnect=''
                connect=''
            else:
                ident='"{}_{}_{}_{}_'.format(connValues['conn_bundle_type_id'],connValues['conn_type_seq'],connValues['conn_type_id'],connValues['conn_seq'])
                ctrl=changedValues[connValues['conn_id']]['ctrl']
                new_var='M' if ctrl else 'P'
                new_var_value=changedValues[connValues['conn_id']]['m' if ctrl else 'p']['new']
                disconnect='|P_var|' if ctrl else '|M_var|'
                del_constants.append('{}_{}"'.format(ident,'P' if ctrl else 'M'))
                connect='|M_var|' if ctrl else '|P_var|'
                add_constant_name='{}_{}"'.format(ident,'M' if ctrl else 'P')
                add_constants[add_constant_name]= {':V': new_var_value,
                                                    ':FIRST-LINK': [PMT2muxName,new_var],
                                                    ':LAST-LINK':['"'+ident+'_'+new_var+'"','LINK']}

            
            pmt2_update_dict[PMT2muxName]={'disconnect':disconnect,
                                            'connect':connect,
                                            'update': changedValues[connValues['conn_id']]['T']}
    return [pmt2_update_dict,add_constants,del_constants]

if [True for connValues in connsValues if connValues['conn_id'] in changedValues]:
    pmt2_update_dict,add_constants,del_constants=getBoundaryUpdateData(connsValues,changedValues)
    print(pmt2_update_dict)
    print(add_constants)
    print(del_constants)
    #idm    
    data_idm=[]
    for comp in components_idm:
        print(getCompClass(comp))
        if getCompName(comp)in pmt2_update_dict:
            data_idm.append(updatePMT2CompBoundaries(comp,pmt2_update_dict))
        elif getCompName(comp)in del_constants:
            print('delete comp')
            pass
        elif getCompClass(comp)=='CONNECTIONS':
            for constant in add_constants:
                print(constant)
                print(add_constants[constant])
                data_idm.append([{':C': 'SOURCE-CONSTANT', ':N': constant, ':T' :'CONSTANT'},{':C': ':PAR', ':N': 'X', ':V': add_constants[constant][':V']}])
                
            new_conns=[]
            for conn in comp[':CONNS']:
                print(conn)
                if [True for const in del_constants if const in flatten(conn)]:
                    print('---delete conn---')
                    pass
                else:
                    new_conns.append(conn)
            for const in add_constants:
                new_conns.append([add_constants[constant][':FIRST-LINK'],add_constants[constant][':LAST-LINK'], '0','0','NIL'])
            comp[':CONNS']=new_conns
            data_idm.append(comp)
        else:
            data_idm.append(comp)
        
    for i in data_idm:
        pass
        print(i)
        
    print('-----idc------')
    #idc
    data_idc=[]
    for comp in components_idc:
        print(getCompClass(comp))
        if getCompClass(comp)=='EQUATION-FRAME' and comp[':NAME'] in del_constants:
            print('--delete comp--')
            pass
        else:
            data_idc.append(comp)
    
    counter_p=0
    counter_mdot=0
    for const in add_constants:
        if add_constants[const][':LAST-LINK'][1]=='P':
            y=227+counter_p*40
            data_idc.append({':C': 'EQUATION-FRAME', ':AT': [['29', str(y)]], ':R': ['28', '10'], ':ICON': '"sys:constant.ids"', ':SLOT': [const], ':NAME': const, ':DATA': 'SOURCE-CONSTANT'})
            data_idc.append({':C': 'CONNECTION-LINE', ':AT': [['307/5', str(y)], ['87', str(y)]], ':FIRST-LINK': [add_constants[const][':LAST-LINK'][0], ['1', '0.5'], add_constants[const][':LAST-LINK'][1]], ':LAST-LINK': [add_constants[const][':FIRST-LINK'][0], ['0.0', '0.139'], add_constants[const][':FIRST-LINK'][1]], ':DIR': ':RIGHT', ':ARROW': ['19', '8', '8']})
            counter_p+=1
        else:
            y=240+counter_mdot*40
            data_idc.append({':C': 'EQUATION-FRAME', ':AT': [['29', str(y)]], ':R': ['28', str(y)], ':ICON': '"sys:constant.ids"', ':SLOT': [const], ':NAME': const, ':DATA': 'SOURCE-CONSTANT'})
            data_idc.append({':C': 'CONNECTION-LINE', ':AT': [['307/5', str(y)], ['87', str(y)]], ':FIRST-LINK': [add_constants[const][':LAST-LINK'][0], ['1', '0.5'], add_constants[const][':LAST-LINK'][1]], ':LAST-LINK': [add_constants[const][':FIRST-LINK'][0], ['0.0', '0.139'], add_constants[const][':FIRST-LINK'][1]], ':DIR': ':RIGHT', ':ARROW': ['19', '8', '8']})
            counter_mdot+=1
    for i in data_idc:
        pass
        print(i)
                
    writePropertyListIDMToFile(data_idm,plugin_dir+"ida_data\\test21\\customer_templates\\",plugin_dir+"ida_data\\test21\\customer_templates\\test.idm")
    writePropertyListIDCToFile(data_idc,plugin_dir+"ida_data\\test21\\customer_templates\\",plugin_dir+"ida_data\\test21\\customer_templates\\test.idc")
    