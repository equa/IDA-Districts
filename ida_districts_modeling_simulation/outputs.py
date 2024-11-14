import psycopg2
import psycopg2.extras
from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT

from qgis.utils import iface

from plugins.utility_functions.files import *
from plugins.utility_functions.db import *
from plugins.utility_functions.dialog import *
from plugins.utility_functions.topology import *

def setRequestedOutputs(dlg,requestedOutputs,iface,plugin_dir,dictDB,cur):
    """set requested outputs"""
    print ("set requested outputs")
    
    #-----------customers------------
    #-----------power----------
    if dlg.checkBoxSubstationPower.isChecked():
        requestedOutputs['power_c']=True
    else:
        requestedOutputs['power_c']=False
    #-----------temperature----------
    if dlg.checkBoxSubstationConnTemp.isChecked():
        requestedOutputs['temp_c']=True
    else:
        requestedOutputs['temp_c']=False
    #-----------pressure----------
    if dlg.checkBoxSubstationPressure.isChecked():
        requestedOutputs['p_c']=True
    else:
        requestedOutputs['p_c']=False
    #-----------mdot----------
    if dlg.checkBoxSubstationMassflow.isChecked():
        requestedOutputs['mdot_c']=True
    else:
        requestedOutputs['mdot_c']=False
    #-----------heat balance----------
    if dlg.checkBoxSubstationHeatbalance.isChecked():
        requestedOutputs['heatbalance_c']=True
    else:
        requestedOutputs['heatbalance_c']=False
    #-----------tair----------
    if dlg.checkBoxSubstationTair.isChecked():
        requestedOutputs['troom_c']=True
    else:
        requestedOutputs['troom_c']=False
    
    #-------------network------------
    #+++lines+++
    #temp
    if dlg.checkBoxTempPipe.isChecked():
        requestedOutputs['temp_lines']=True
    else:
        requestedOutputs['temp_lines']=False
    #v
    if dlg.checkBoxVPipe.isChecked():
        requestedOutputs['v_lines']=True
    else:
        requestedOutputs['v_lines']=False
        
    #+++nodes+++
    #mdot
    if dlg.checkBoxMdotNode.isChecked():
        requestedOutputs['mdot_lines']=True
    else:
        requestedOutputs['mdot_lines']=False
    #pressure
    if dlg.checkBoxPressureDistribution.isChecked():
        requestedOutputs['p_lines']=True
    else:
        requestedOutputs['p_lines']=False
    
    #-----------energy plants------------
    #-----------power----------
    if dlg.checkBoxPlantPower.isChecked():
        requestedOutputs['power_ep']=True
    else:
        requestedOutputs['power_ep']=False
    #-----------temperature----------
    if dlg.checkBoxPlantConnTemp.isChecked():
        requestedOutputs['temp_ep']=True
    else:
        requestedOutputs['temp_ep']=False
    #-----------pressure----------
    if dlg.checkBoxPlantPressure.isChecked():
        requestedOutputs['p_ep']=True
    else:
        requestedOutputs['p_ep']=False
    #-----------massflow----------
    if dlg.checkBoxPlantMassflow.isChecked():
        requestedOutputs['mdot_ep']=True
    else:
        requestedOutputs['mdot_ep']=False
        
    #timestep for outputs
    if is_number(dlg.outputTimestep.text()):
        requestedOutputs['dt_outputs']=dlg.outputTimestep.text()
    else:
        iface.messageBar().pushMessage("Info", "Timestep for Output is not a number!", level=Qgis.Info)
        
    writeRequestedOutputs(plugin_dir,dictDB,requestedOutputs)
    
    #check difference between new and old requested outputs
    outputs_c={}
    outputs_ep={}
    new_outputTimestep=False
    for out in requestedOutputs:
        if requestedOutputs[out]!=dlg.requestedOutputs_old[out]:
            print('missmatch')
            if '_c' in out:
                outputs_c[out]=requestedOutputs[out]
            if '_ep' in out:
                outputs_ep[out]=requestedOutputs[out]
            if 'dt_outputs'==out:
                new_outputTimestep=requestedOutputs[out]
    print('----')
    print(outputs_c)
    print(outputs_ep)
    
    if outputs_c or new_outputTimestep:
        updateAssettypesOutputs('customer',outputs_c,new_outputTimestep,dictDB,cur,plugin_dir,requestedOutputs)
    if outputs_ep or new_outputTimestep:
        updateAssettypesOutputs('energy_plant',outputs_ep,new_outputTimestep,dictDB,cur,plugin_dir,requestedOutputs)
    
    closeDialog(dlg)
    
def updateAssettypesOutputs(feature,outputs,new_outputTimestep,dictDB,cur,plugin_dir,requestedOutputs):           
    dir = getDataCenterDir(plugin_dir)+"\\"+dictDB['projectName']+"\\"+feature+"_assettypes\\"
    print(dir)
               
    for at_name in getAssettypeNames(cur,feature):
        print(at_name)
        assetgroup=at_name.split('_')[0]
        at=at_name.split('_')[1]
        if new_outputTimestep:
            print('----update timestep for outputs----')
            fname=dir+at_name+'.idm'
            print(fname)
            components_idm=propertyListCompsIDM(getIDAListComponents(readFileToString(fname)))
            data_idm=[]
            output_step=False
            for comp in components_idm:
                new_comp=[]
                if getCompClass(comp)=='SIMULATION_DATA':
                    #print('++++++++simulation data+++++++')
                    for i in comp:
                        if getCompName(i)=='CALCULATION-PHASE':
                            i_new=[]
                            #print('++++++++CALCULATION-PHASE+++++++')
                            for j in i:
                                if getCompName(j)=='OUTPUT-STEP':
                                    #print('++++++++OUTPUT-STEP+++++++')
                                    output_step=True
                                    j[':V']=new_outputTimestep
                                i_new.append(j)
                            if not output_step:
                                i_new.append({':C': ':PAR', ':N': 'OUTPUT-STEP', ':V': new_outputTimestep})
                            new_comp.append(i_new)
                        else:
                            new_comp.append(i)
                    data_idm.append(new_comp)              
                else:
                    data_idm.append(comp) 
            print(data_idm)        
            writePropertyListIDMToFile(data_idm,dir+at_name,fname)
        print('----update outputs----')

        if outputs:
            fname=dir+at_name+'\\'+at_name+'.idm'
            print(fname)
            components_idm=propertyListCompsIDM(getIDAListComponents(readFileToString(fname)))
            data_idm=[]
            conn_bundle_type_id=getConnBundleByAssettype(feature,at,assetgroup,cur,dictDB)
            connValues=getConnsValues(conn_bundle_type_id,cur)
            print(connValues)
            conn_type_seq=set([x['conn_type_seq'] for x in connValues])
            print(conn_type_seq)
            flowmeters=['"'+str(conn_bundle_type_id)+'_'+str(seq)+'_Flowmeter2"' for seq in conn_type_seq]
            print(flowmeters)   
            pmtmuxs={'"PMT2mux_{}_{}_{}_{}"'.format(value['conn_bundle_type_id'],value['conn_type_seq'],value['conn_type_id'],value['conn_seq']) : {'seq':seq,'conn_bundle_type_id':value['conn_bundle_type_id'],'conn_seq':value['conn_seq']} for seq in conn_type_seq for value in connValues if seq==value['conn_type_seq']}
            print(pmtmuxs)            
            for comp in components_idm:
                print(getCompName(comp))
                if getCompTemplate(comp) in ['|lM_H_G_L|','FLOWMETER2','PMT2\\m\\u\\x'] or getCompClass(comp) in 'OUTPUT-FILE':
                    if not isinstance(comp, list):
                        comp=[comp]
                    new_comp=[]
                    if getCompTemplate(comp) in ['|lM_H_G_L|'] and 'troom_c' in [i for i in outputs if outputs[i]]:
                        print('---add tair output----')
                        #print(comp)
                        new_comp=[]
                        outputs_to_set=['|TRoom|']
                        for i in comp:
                            if getCompName(i)=='|TRoom|':
                                i[':L']='"TRoom"'
                                new_comp.append(i)
                                outputs_to_set.remove('|TRoom|')
                            else:
                                new_comp.append(i)
                        for i in outputs_to_set:
                            new_comp.append({':C': ':VAR', ':N': i, ':L': '"TRoom"'})
                        comp=new_comp
                        data_idm.append([{':C': 'OUTPUT-FILE', ':N': '"TRoom"', ':T': 'OUTPUT-FILE'}])
                    if getCompTemplate(comp) in ['|lM_H_G_L|'] and 'heatbalance_c' in [i for i in outputs if outputs[i]]:
                        print('---add heatbalance output----')
                        #print(comp)
                        new_comp=[]
                        outputs_to_set={'|PhiSolar|':'Solar','|Occupancy|':'Occupancy','|Electricity|':'Electricty','|PhiInt|':'Gains','|PhiRad|':'Heating','|PhiOut|':'Transmission','|PhiLeakage|': 'Leakage','|PhiVent|':'Ventilation'}
                        for i in comp:
                            if getCompName(i) in outputs_to_set:
                                i[':L']='"Heatbalance"'
                                i[':AS']='"{}"'.format(outputs_to_set[getCompName(i)])
                                new_comp.append(i)
                                del outputs_to_set[getCompName(i)]
                            else:
                                new_comp.append(i)
                        for i in outputs_to_set:
                            new_comp.append({':C': ':VAR', ':N': i, ':L': '"Heatbalance"',':AS':'"{}"'.format(outputs_to_set[i])})
                        comp=new_comp
                        data_idm.append([{':C': 'OUTPUT-FILE', ':N': '"Heatbalance"', ':T': 'OUTPUT-FILE'}])
                    if getCompTemplate(comp) in ['|lM_H_G_L|'] and 'heatbalance_c' in [i for i in outputs if not outputs[i]]:
                        print('---remove heatbalance_c output----')
                        outputs_to_del={'|PhiSolar|':'Solar','|Occupancy|':'Occupancy','|Electricity|':'Electricty','|PhiInt|':'Gains','|PhiRad|':'Heating','|PhiOut|':'Transmission','|PhiLeakage|': 'Leakage','|PhiVent|':'Ventilation'}
                        new_comp=[]
                        for i in comp:
                            if getCompName(i) in outputs_to_del:
                                try:
                                    del i[':L']
                                    del i[':AS']
                                except:
                                    pass
                                new_comp.append(i)
                            else:
                                new_comp.append(i)
                        comp=new_comp
                    if getCompTemplate(comp) in ['|lM_H_G_L|'] and 'troom_c' in [i for i in outputs if not outputs[i]]:
                        print('---remove tair output----')
                        new_comp=[]
                        for i in comp:
                            if getCompName(i)=='|TRoom|':
                                try:
                                    del i[':L']
                                except:
                                    pass
                                new_comp.append(i)
                            else:
                                new_comp.append(i)
                        comp=new_comp
                    if getCompName(comp) in pmtmuxs:
                        print('-------pmtmux-----')
                        #print(comp)
                        new_comp=[]
                        outputs_to_set=[]
                        outputs_to_del=[]
                        if 'p_c' in [i for i in outputs if outputs[i]] or 'p_ep' in [i for i in outputs if outputs[i]]:
                            outputs_to_set.append('|P_var|')
                        print(outputs_to_set)
                        if 'p_c' in [i for i in outputs if not outputs[i]] or 'p_ep' in [i for i in outputs if not outputs[i]]:
                            outputs_to_del.append('|P_var|')
                        print(outputs_to_del)
                        if outputs_to_set and not getCompPerName(data_idm,'"Connection type sequence_{}"'.format(pmtmuxs[getCompName(comp)]['seq'])):
                            data_idm.append([{':C': 'OUTPUT-FILE', ':N': '"Connection type sequence_{}"'.format(pmtmuxs[getCompName(comp)]['seq']), ':T': 'OUTPUT-FILE'}])
                        if outputs_to_set or outputs_to_del:
                            for i in comp:
                                if getCompName(i)=='|P_var|' and '|P_var|' in outputs_to_set:
                                    print('++++add p+++++')
                                    i[':L']='"Connection type sequence_{}"'.format(pmtmuxs[getCompName(comp)]['seq'])
                                    i[':AS']='"p_{}"'.format(pmtmuxs[getCompName(comp)]['conn_seq'])
                                    new_comp.append(i)
                                    outputs_to_set.remove('|P_var|')
                                else:
                                    print('***rest***')
                                    print(getCompName(comp))
                                    if getCompName(i)=='|P_var|' and '|P_var|' in outputs_to_del:
                                        print('del :L and :AS')
                                        new_comp.append({j:i[j] for j in i if j not in [':L',':AS']})
                                    else:
                                        new_comp.append(i)
                            for i in outputs_to_set:
                                new_comp.append({':C': ':VAR', ':N': i, ':L': '"Connection type sequence_{}"'.format(pmtmuxs[getCompName(comp)]['seq']),':AS':'"p_{}"'.format(pmtmuxs[getCompName(comp)]['conn_seq'])})
                            comp=new_comp
                        
                    if getCompName(comp) in flowmeters:
                        print('-------flow meter-----')
                        #print(comp)
                        new_comp=[]
                        n_sup=1
                        n_ret=1
                        conn_type_seq=getCompName(comp).split('_')[1]
                        outputs_to_set=[]
                        if 'power_c' in [i for i in outputs if outputs[i]] or 'power_ep' in [i for i in outputs if outputs[i]]:
                            outputs_to_set.append('P')
                        if 'temp_c' in [i for i in outputs if outputs[i]] or 'temp_ep' in [i for i in outputs if outputs[i]]:
                            outputs_to_set.append('TSUP')
                            outputs_to_set.append('TRET')
                        if 'mdot_c' in [i for i in outputs if outputs[i]] or 'mdot_ep' in [i for i in outputs if outputs[i]]:
                            outputs_to_set.append('FLOW_SUP')
                            outputs_to_set.append('FLOW_RET')
                        print(outputs_to_set)
                        if outputs_to_set and not getCompPerName(data_idm,'"Connection type sequence_{}"'.format(conn_type_seq)):
                            data_idm.append([{':C': 'OUTPUT-FILE', ':N': '"Connection type sequence_{}"'.format(conn_type_seq), ':T': 'OUTPUT-FILE'}])
                        outputs_to_del=[]
                        if 'power_c' in [i for i in outputs if not outputs[i]] or 'power_ep' in [i for i in outputs if not outputs[i]]:
                            outputs_to_del.append('P')
                        if 'temp_c' in [i for i in outputs if not outputs[i]] or 'temp_ep' in [i for i in outputs if not outputs[i]]:
                            outputs_to_del.append('TSUP')
                            outputs_to_del.append('TRET')
                        if 'mdot_c' in [i for i in outputs if not outputs[i]] or 'mdot_ep' in [i for i in outputs if not outputs[i]]:
                            outputs_to_del.append('FLOW_SUP')
                            outputs_to_del.append('FLOW_RET')
                        print(outputs_to_del)
                        if outputs_to_set or outputs_to_del:
                            sup_conn=[connValue['conn_seq'] for connValue in connValues if connValue['type']==1]
                            ret_conn=[connValue['conn_seq'] for connValue in connValues if connValue['type']==2]
                            for i in comp:

                                    
                                if getCompName(i)=='P' and 'P' in outputs_to_set:
                                    print('++++add power+++++')
                                    i[':L']='"Connection type sequence_{}"'.format(conn_type_seq)
                                    i[':AS']='"power"'
                                    new_comp.append(i)
                                    outputs_to_set.remove('P')
                                elif getCompName(i)=='FLOW_SUP' and 'FLOW_SUP' in outputs_to_set:
                                    print('++++add flow sup+++++')
                                    i[':L']="""#S(MS-SPARSE DEFAULT-VALUE OFF DIMENSION 1 VALUE ({}))""".format(' '.join(['('+str(i[0])+ ' . '+'"Connection type sequence_{}"'.format(conn_type_seq)+')' for i in enumerate(sup_conn,1)]))
                                    i[':AS']="""#S(MS-SPARSE DEFAULT-VALUE NIL DIMENSION 1 VALUE ({}))""".format(' '.join(['('+str(i[0])+ ' . '+'"mdot_{}"'.format(i[1])+')' for i in enumerate(sup_conn,1)]))
                                    new_comp.append(i)
                                    outputs_to_set.remove('FLOW_SUP')
                                elif getCompName(i)=='FLOW_RET' and 'FLOW_RET' in outputs_to_set:
                                    print('++++add flow ret+++++')
                                    i[':L']="""#S(MS-SPARSE DEFAULT-VALUE OFF DIMENSION 1 VALUE ({}))""".format(' '.join(['('+str(i[0])+ ' . '+'"Connection type sequence_{}"'.format(conn_type_seq)+')' for i in enumerate(ret_conn,1)]))
                                    i[':AS']="""#S(MS-SPARSE DEFAULT-VALUE NIL DIMENSION 1 VALUE ({}))""".format(' '.join(['('+str(i[0])+ ' . '+'"mdot_{}"'.format(i[1])+')' for i in enumerate(ret_conn,1)]))
                                    new_comp.append(i)
                                    outputs_to_set.remove('FLOW_RET')
                                elif getCompName(i)=='TSUP' and 'TSUP' in outputs_to_set:
                                    print('++++add T sup+++++')
                                    i[':L']="""#S(MS-SPARSE DEFAULT-VALUE OFF DIMENSION 1 VALUE ({}))""".format(' '.join(['('+str(i[0])+ ' . '+'"Connection type sequence_{}"'.format(conn_type_seq)+')' for i in enumerate(sup_conn,1)]))
                                    i[':AS']="""#S(MS-SPARSE DEFAULT-VALUE NIL DIMENSION 1 VALUE ({}))""".format(' '.join(['('+str(i[0])+ ' . '+'"temp_{}"'.format(i[1])+')' for i in enumerate(sup_conn,1)]))
                                    new_comp.append(i)
                                    outputs_to_set.remove('TSUP')
                                elif getCompName(i)=='TRET' and 'TRET' in outputs_to_set:
                                    print('++++add T ret+++++')
                                    i[':L']="""#S(MS-SPARSE DEFAULT-VALUE OFF DIMENSION 1 VALUE ({}))""".format(' '.join(['('+str(i[0])+ ' . '+'"Connection type sequence_{}"'.format(conn_type_seq)+')' for i in enumerate(ret_conn,1)]))
                                    i[':AS']="""#S(MS-SPARSE DEFAULT-VALUE NIL DIMENSION 1 VALUE ({}))""".format(' '.join(['('+str(i[0])+ ' . '+'"temp_{}"'.format(i[1])+')' for i in enumerate(ret_conn,1)]))
                                    new_comp.append(i)
                                    outputs_to_set.remove('TRET')
                                else:
                                    print('***rest***')
                                    print(getCompName(i))
                                    if getCompName(i) in outputs_to_del:
                                        print('del :L and :AS')
                                        new_comp.append({j:i[j] for j in i if j not in [':L',':AS']})
                                    else:
                                        new_comp.append(i)
                            for i in outputs_to_set:
                                new_comp.append({':C': ':VAR', ':N': i, ':L': '"Connection type sequence_{}"'.format(conn_type_seq)})
                            comp=new_comp
                    if getCompClass(comp) in 'OUTPUT-FILE':
                        if (getCompName(comp)=='"TAir"' and 'troom_c' in [i for i in outputs if not outputs[i]] or
                            getCompName(comp)=='"Heatbalance"' and 'heatbalance_c' in [i for i in outputs if not outputs[i]] or
                            "Connection type sequence_" in getCompName(comp) and not [True for i in requestedOutputs if i in ['power_c','temp_c','p_c','mdot_c'] and requestedOutputs[i]]):
                            print('++++not outputfile++++')
                        else:
                            data_idm.append(comp)
                    else:
                        data_idm.append(comp)    
                else:
                    data_idm.append(comp)
            #print('*************************')
            #for i in data_idm:
            #    print(i)
                writePropertyListIDMToFile(data_idm,dir+at_name,fname)