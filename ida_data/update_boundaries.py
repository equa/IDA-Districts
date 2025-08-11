from plugins.utility_functions.ida_components import *
from plugins.utility_functions.files import *
from plugins.utility_functions.topology import *

def updatePMT2CompBoundaries(comp,pmt2_update_dict):
    new_comp=[]
    #print(comp)
    for i in comp:
        #print("class: {}; name: {}".format(getCompClass(i),getCompName(i)))
        if getCompClass(i)==':VAR' and getCompName(i) in pmt2_update_dict[getCompName(comp)]['disconnect']:
            #print('disconnect')
            pass
        elif getCompClass(i)=='CONNECTOR' and pmt2_update_dict[getCompName(comp)]['update_T']:
            new_connector=[]
            for j in i:
                if getCompName(j)=='|inStream(T)|':
                    j[':B']=pmt2_update_dict[getCompName(comp)]['update_T']
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
    update_constants={}
    del_constants=[]
    for connValues in connsValues:
        if connValues['conn_id'] in changedValues:
            #print(connValues)
            ident='{}_{}_{}_{}'.format(connValues['conn_bundle_type_id'],connValues['conn_type_seq'],connValues['conn_type_id'],connValues['conn_seq'])
            PMT2muxName='"'+ident+'"'
            #print(PMT2muxName)
            ctrl=changedValues[connValues['conn_id']]['ctrl']
            #print(ctrl)
            if ctrl=='unchanged':
                disconnect=''
                connect=''
                update_constant_name=False
                if changedValues[connValues['conn_id']]['m']['new'] and changedValues[connValues['conn_id']]['m']['new']!=changedValues[connValues['conn_id']]['m']['old']:
                    update_constant_name='"'+ident+'_M"'
                    value=changedValues[connValues['conn_id']]['m']['new']
                elif changedValues[connValues['conn_id']]['p']['new'] and changedValues[connValues['conn_id']]['p']['new']!=changedValues[connValues['conn_id']]['p']['old']:
                    update_constant_name='"'+ident+'_P"'
                    value=changedValues[connValues['conn_id']]['p']['new']
                #print('update_constant_name: '+str(update_constant_name))
                if update_constant_name:
                    update_constants[update_constant_name]={':V': value}
            else:
                #print('change')
                old_var='M' if not ctrl else 'P'
                new_var='M' if ctrl else 'P'
                #print(new_var)
                new_var_value=changedValues[connValues['conn_id']]['m' if ctrl else 'p']['new']
                #print(new_var_value)
                disconnect='|P_var|' if ctrl else '|M_var|'
                del_constants.append('"{}_{}"'.format(ident,old_var))
                connect='|M_var|' if ctrl else '|P_var|'
                add_constant_name='"{}_{}"'.format(ident,new_var)
                add_constants[add_constant_name]= {':V': new_var_value,
                                                    ':FIRST-LINK': [PMT2muxName,new_var],
                                                    ':LAST-LINK':['"'+ident+'_'+new_var+'"','LINK']}

            
            pmt2_update_dict[PMT2muxName]={'disconnect':disconnect,
                                            'connect':connect,
                                            'update_T': changedValues[connValues['conn_id']]['T']}
    return [pmt2_update_dict,add_constants,del_constants,update_constants]
    
def updateTemplateBoundaryValues(dlg,plugin_dir,dictDB,cur):
    """ 1) Loop over changed boundary values
        2) Check which templates are affected
        3) Update pmt2 connection template project file"""
    #print('----update boundary values---')
    #print(dlg.traceTableValues)
    changedValues={}
    for b_value in dlg.traceTableValues:
        if dlg.traceTableValues[b_value][1] and dlg.traceTableValues[b_value][0]!=dlg.traceTableValues[b_value][1]:
            p=dlg.traceTableValues[b_value][1]
        else:
            p=False
        if dlg.traceTableValues[b_value][9] and dlg.traceTableValues[b_value][8]!=dlg.traceTableValues[b_value][9]:
            inverse=True
        else:
            inverse=False
        if inverse or dlg.traceTableValues[b_value][3] and dlg.traceTableValues[b_value][2]!=dlg.traceTableValues[b_value][3]:
            #print(inverse)
            inverse_value=-1 if dlg.traceTableValues[b_value][9]=='1' and dlg.traceTableValues[b_value][1]!='1' else 1
            if dlg.traceTableValues[b_value][3]:
                m=str(float(dlg.traceTableValues[b_value][3])*inverse_value)
            else:
                m=str(float(dlg.traceTableValues[b_value][2])*inverse_value)
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
        if p or m or T or inverse or ctrl !='unchanged':
            conn_id=dlg.tableWidget.item(b_value,0).text()
            changedValues[int(conn_id)]={'p':{'old': dlg.traceTableValues[b_value][0],'new':p},'m':{'old':dlg.traceTableValues[b_value][2],'new':m},'T':T,'ctrl':ctrl}
    #print(changedValues)
 
    for feature in ['customer','energy_plant']:
        #print('-----------------------------------')
        #print(feature)
        at_dir=plugin_dir+'\\'+dictDB['projectName']+"\\{}_templates".format(feature)
        for template_name in getTemplateNames(cur,feature):
            #print('******************************************')
            #print(template_name)
            connsValues=getConnsValuesByTemplate(feature,template_name.split('_')[1],template_name.split('_')[0],cur,dictDB)
            #print('connsValues')
            #print(connsValues)
            if [True for connValues in connsValues if connValues['conn_id'] in changedValues]:
                #print('update template_name: {}'.format(template_name))
                pmt2_update_dict,add_constants,del_constants,update_constants=getBoundaryUpdateData(connsValues,changedValues)
                #print(pmt2_update_dict)
                #print(add_constants)
                #print(del_constants)
                #print(update_constants)

                template_idm=at_dir+'\\{}.idm'.format(template_name)
                template_idc=at_dir+'\\{}.idc'.format(template_name)
                #print(readFileToString(template_idm))
                #print(getIDAListComponents(readFileToString(template_idm)))
                components_idm=propertyListCompsIDM(getIDAListComponents(readFileToString(template_idm)))
                components_idc=propertyListCompsIDC(getIDAListComponents(readFileToString(template_idc)))
                
                #idm
                data_idm=[]
                for comp in components_idm:
                    #print(getCompClass(comp))
                    if getCompName(comp) in pmt2_update_dict:
                        data_idm.append(updatePMT2CompBoundaries(comp,pmt2_update_dict))
                    elif getCompName(comp) in del_constants:
                        #print('delete comp')
                        pass
                    elif getCompName(comp) in update_constants:
                        #print('update comp')
                        const=getCompName(comp) 
                        #print(const)
                        data_idm.append([{':C': 'SOURCE-CONSTANT', ':N': const , ':T' :'CONSTANT'},{':C': ':PAR', ':N': 'X', ':V': update_constants[const][':V']}])  
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
                #print('-----idc------')
                data_idc=[]
                deletedEquationFrame_dict={}
                deletedConnectionLine_dict={}
                for comp in components_idc:
                    #print(getCompClass(comp))
                    if getCompClass(comp)=='EQUATION-FRAME' and comp[':NAME'] in del_constants:
                        #print('--delete comp--')
                        deletedEquationFrame_dict[comp[':NAME'][:-3]+'"'] = comp[':AT']
                    elif getCompClass(comp)=='CONNECTION-LINE' and comp[':FIRST-LINK'][0] in del_constants:
                        #print('-+-delete connection-+-')
                        deletedConnectionLine_dict[comp[':FIRST-LINK'][0][:-3]+'"'] = comp
                    elif getCompClass(comp)=='CONNECTION-LINE' and comp[':LAST-LINK'][0] in del_constants:
                        #print('-+-delete connection-+-')
                        deletedConnectionLine_dict[comp[':LAST-LINK'][0][:-3]+'"'] = comp
                    else:
                        data_idc.append(comp)
                #print(deletedEquationFrame_dict)
                #print(deletedConnectionLine_dict)
                
                for const in add_constants:
                    #print('-*-*--*-*-*-*-*-*')
                    #print([i for i in connsValues if i['p']])
                    #print([i for i in connsValues if i['mdot']])
                    #print(add_constants[const][':FIRST-LINK'])
                    if add_constants[const][':FIRST-LINK'][1]=='P':
                        y_equation_frame = deletedEquationFrame_dict[const[:-3]+'"'][0][1]
                        y_conn_line = deletedConnectionLine_dict[const[:-3]+'"'][':AT'][0][1]
                        #print(y_equation_frame)
                        #print(y_conn_line)
                        data_idc.append({':C': 'EQUATION-FRAME', ':AT': [['29', y_equation_frame]], ':R': ['28', '10'], ':ICON': '"sys:constant.ids"', ':SLOT': [const], ':NAME': const, ':DATA': 'SOURCE-CONSTANT'})
                        data_idc.append({':C': 'CONNECTION-LINE', ':AT': [['307/5', y_conn_line], ['87', y_conn_line]], ':FIRST-LINK': [add_constants[const][':LAST-LINK'][0], ['1', '0.5'], add_constants[const][':LAST-LINK'][1]], ':LAST-LINK': [add_constants[const][':FIRST-LINK'][0], ['0.0', '0.139'], add_constants[const][':FIRST-LINK'][1]], ':DIR': ':RIGHT', ':ARROW': ['19', '8', '8']})
                    else:
                        y_equation_frame = deletedEquationFrame_dict[const[:-3]+'"'][0][1]
                        y_conn_line = deletedConnectionLine_dict[const[:-3]+'"'][':AT'][0][1]
                        #print(y_equation_frame)
                        #print(y_conn_line)
                        data_idc.append({':C': 'EQUATION-FRAME', ':AT': [['29', y_equation_frame]], ':R': ['28', '10'], ':ICON': '"sys:constant.ids"', ':SLOT': [const], ':NAME': const, ':DATA': 'SOURCE-CONSTANT'})
                        data_idc.append({':C': 'CONNECTION-LINE', ':AT': [['307/5', y_conn_line], ['87', y_conn_line]], ':FIRST-LINK': [add_constants[const][':LAST-LINK'][0], ['1', '0.5'], add_constants[const][':LAST-LINK'][1]], ':LAST-LINK': [add_constants[const][':FIRST-LINK'][0], ['0.0', '0.139'], add_constants[const][':FIRST-LINK'][1]], ':DIR': ':RIGHT', ':ARROW': ['19', '8', '8']})
                for i in data_idc:
                    pass
                    #print(i)
                            
                writePropertyListIDMToFile(data_idm,at_dir,template_idm)
                writePropertyListIDCToFile(data_idc,at_dir,template_idc)              
            
    #print('----update boundary values finished---')