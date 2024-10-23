from plugins.utility_functions.ida_components import *
from plugins.utility_functions.files import *
from plugins.utility_functions.topology import *

def updatePMT2CompBoundaries(comp,pmt2_update_dict):
    new_comp=[]
    #print(comp)
    for i in comp:
        #print("class: {}; name: {}".format(getCompClass(i),getCompName(i)))
        if getCompClass(i)==':VAR' and getCompName(i) in pmt2_update_dict[getCompName(comp)]['disconnect']:
            print('disconnect')
            pass
        elif getCompClass(i)=='CONNECTOR' and pmt2_update_dict[getCompName(comp)]['update']:
            new_connector=[]
            for j in i:
                if getCompName(j)=='|inStream(T)|':
                    j[':B']=pmt2_update_dict[getCompName(comp)]['update']
                new_connector.append(j)
            #print(new_comp)
            new_comp.append(new_connector)
        else:
            new_comp.append(i)
    if pmt2_update_dict[getCompName(comp)]['connect']=='|M_var|':
        new_comp.append({':C': ':VAR', ':N': '|M_var|', ':B': '(-1 M 0)'})
    elif pmt2_update_dict[getCompName(comp)]['connect']=='|P_var|':
        new_comp.append({':C': ':VAR', ':N': '|P_var|', ':B': '(-1 P 0)'})
    #print(new_comp)
    return new_comp

def getBoundaryUpdateData(connsValues,changedValues):
    pmt2_update_dict={}
    add_constants={}
    del_constants=[]
    for connValues in connsValues:
        if connValues['conn_id'] in changedValues:
            #print(connValues)
            PMT2muxName='"{}_{}_{}_{}_T{}"'.format(connValues['conn_bundle_type_id'],connValues['conn_type_seq'],connValues['conn_type_id'],connValues['conn_seq'],connValues['temp'])
            print(PMT2muxName)
            if changedValues[connValues['conn_id']]['ctrl']=='unchanged':
                disconnect=''
                connect=''
            else:
                ident='"{}_{}_{}_{}_'.format(connValues['conn_bundle_type_id'],connValues['conn_type_seq'],connValues['conn_type_id'],connValues['conn_seq'])
                ctrl=changedValues[connValues['conn_id']]['ctrl']
                new_var='M' if ctrl else 'P'
                new_var_value=changedValues[connValues['conn_id']]['m' if ctrl else 'p']['new']
                old_var_value=changedValues[connValues['conn_id']]['p']['old'] if ctrl else changedValues[connValues['conn_id']]['m']['old']
                disconnect='|P_var|' if ctrl else '|M_var|'
                del_constants.append('{}{}{}"'.format(ident,
                                                        'P' if ctrl else 'M',
                                                        old_var_value))
                connect='|M_var|' if ctrl else '|P_var|'
                add_constant_name='{}{}{}"'.format(ident,
                                                'M' if ctrl else 'P',
                                                new_var_value)
                add_constants[add_constant_name]= {':V': new_var_value,
                                                    ':FIRST-LINK': [PMT2muxName,new_var],
                                                    ':LAST-LINK':[ident+new_var+new_var_value+'"','LINK']}

            
            pmt2_update_dict[PMT2muxName]={'disconnect':disconnect,
                                            'connect':connect,
                                            'update': changedValues[connValues['conn_id']]['T']}
    return [pmt2_update_dict,add_constants,del_constants]
    
def updateAssettypeBoundaryValues(dlg,plugin_dir,dictDB,cur):
    """ 1) Loop over changed boundary values
        2) Check which templates are affected
        3) Update pmt2 connection template project file"""
    print('----update boundary values---')
    
    changedValues={}
    for b_value in dlg.traceTableValues:
        if dlg.traceTableValues[b_value][1] and dlg.traceTableValues[b_value][0]!=dlg.traceTableValues[b_value][1]:
            p=dlg.traceTableValues[b_value][1]
        else:
            p=False
        if dlg.traceTableValues[b_value][3] and dlg.traceTableValues[b_value][2]!=dlg.traceTableValues[b_value][3]:
            m=dlg.traceTableValues[b_value][3]
        else:
            m=False
        if dlg.traceTableValues[b_value][5] and dlg.traceTableValues[b_value][4]!=dlg.traceTableValues[b_value][5]:
            T=dlg.traceTableValues[b_value][5]
        else:
            T=False
        if isinstance(dlg.traceTableValues[b_value][7],bool) and dlg.traceTableValues[b_value][6]!=dlg.traceTableValues[b_value][7]:
            ctrl=dlg.traceTableValues[b_value][7]
        else:
            ctrl='unchanged'
        #print("""p= {}; m= {}; T={}; ctrl= {}""".format(p,m,T,ctrl))
        if p or m or T or ctrl !='unchanged':
            conn_id=dlg.tableWidget.item(b_value,0).text()
            changedValues[int(conn_id)]={'p':{'old': dlg.traceTableValues[b_value][0],'new':p},'m':{'old':dlg.traceTableValues[b_value][2],'new':m},'T':T,'ctrl':ctrl}
    print(changedValues)
 
    for feature in ['customer','energy_plant']:
        print('-----------------------------------')
        print(feature)
        at_dir=plugin_dir+'\\'+dictDB['projectName']+"\\{}_assettypes".format(feature)
        for assettype_name in getAssettypeNames(cur,feature):
            print('******************************************')
            print(assettype_name)
            connsValues=getConnsValuesByAssettype(feature,assettype_name.split('_')[1],assettype_name.split('_')[0],cur,dictDB)
            if [True for connValues in connsValues if connValues['conn_id'] in changedValues]:
                pmt2_update_dict,add_constants,del_constants=getBoundaryUpdateData(connsValues,changedValues)
                print(pmt2_update_dict)
                print(add_constants)
                print(del_constants)

                assettype_idm=at_dir+'\\{}.idm'.format(assettype_name)
                assettype_idc=at_dir+'\\{}.idc'.format(assettype_name)
                components_idm=propertyListCompsIDM(getIDAListComponents(readFileToString(assettype_idm)))
                components_idc=propertyListCompsIDC(getIDAListComponents(readFileToString(assettype_idc)))
                
                #idm
                data_idm=[]
                for comp in components_idm:
                    #print(getCompClass(comp))
                    if getCompName(comp)in pmt2_update_dict:
                        data_idm.append(updatePMT2CompBoundaries(comp,pmt2_update_dict))
                    elif getCompName(comp)in del_constants:
                        #print('delete comp')
                        pass
                    elif getCompClass(comp)=='CONNECTIONS':
                        for const in add_constants:
                            #print(const)
                            #print(add_constants[const])
                            data_idm.append([{':C': 'SOURCE-CONSTANT', ':N': const, ':T' :'CONSTANT'},{':C': ':PAR', ':N': 'X', ':V': add_constants[const][':V']}])
                            
                        new_conns=[]
                        for conn in comp[':CONNS']:
                            #print(conn)
                            if [True for const in del_constants if const in flatten(conn)]:
                                #print('---delete conn---')
                                pass
                            else:
                                new_conns.append(conn)
                        for const in add_constants:
                            new_conns.append([add_constants[const][':FIRST-LINK'],add_constants[const][':LAST-LINK'], '0','0','NIL'])
                        comp[':CONNS']=new_conns
                        data_idm.append(comp)
                    else:
                        data_idm.append(comp)
                    
                #idc
                print('-----idc------')
                data_idc=[]
                for comp in components_idc:
                    print(getCompClass(comp))
                    if getCompClass(comp)=='EQUATION-FRAME' and comp[':NAME'] in del_constants:
                        print('--delete comp--')
                        pass
                    elif getCompClass(comp)=='CONNECTION-LINE' and (comp[':FIRST-LINK'][0] in del_constants or comp[':LAST-LINK'][0] in del_constants):
                        print('-+-delete connection-+-')
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
                        data_idc.append({':C': 'EQUATION-FRAME', ':AT': [['29', str(y)]], ':R': ['28', '10'], ':ICON': '"sys:constant.ids"', ':SLOT': [const], ':NAME': const, ':DATA': 'SOURCE-CONSTANT'})
                        data_idc.append({':C': 'CONNECTION-LINE', ':AT': [['307/5', str(y)], ['87', str(y)]], ':FIRST-LINK': [add_constants[const][':LAST-LINK'][0], ['1', '0.5'], add_constants[const][':LAST-LINK'][1]], ':LAST-LINK': [add_constants[const][':FIRST-LINK'][0], ['0.0', '0.139'], add_constants[const][':FIRST-LINK'][1]], ':DIR': ':RIGHT', ':ARROW': ['19', '8', '8']})
                        counter_mdot+=1
                for i in data_idc:
                    pass
                    #print(i)
                            
                writePropertyListIDMToFile(data_idm,at_dir,assettype_idm)
                writePropertyListIDCToFile(data_idc,at_dir,assettype_idc)              
            
    print('----update boundary values finished---')