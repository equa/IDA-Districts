from plugins.utility_functions.util import *
from plugins.utility_functions.sensor_signals import *
from plugins.utility_functions.topology import *

import psycopg2.extras

def sensorMacroIdmData(submodel,supervisory_submodel,sensor_dec_data,sensor_data,cur,dictDB,dir,import_counter):
    #----------------------sensor idm macro file------------------------
    file=dir+"""\\Sensor-macro.idm"""
    data=[""";IDA 5.11 Data UTF-8\n""","""(DOCUMENT-HEADER :TYPE ICE-MACRO :D "ICE macro" :ETM 3879491673 :APP (ICE :VER 5.11))\n"""]
    #add irefs source if measure ==custom (5) and function != Individual signals for each target(6)
    data.append(''.join(["""(:IREF :N "Int_Ref_Sensor_Source_{}" :T IN :F 208)\n""".format(j['iref']) 
        for i in sensor_dec_data if i['measure']==5 and i['function']!=6 for j in i['irefs_source'] if 
            j['submodel']==submodel and not j['network_side'] or j['cosim']==submodel and j['network_side']]))              
    #add iref targets if not (function == Individual signals for each target (6) and meaure==custom(5) and target==Custom (1))       
    data.append(''.join(["""(:IREF :N "Int_Ref_Sensor_Target_{}" :T OUT :F 224)\n""".format(j['iref']) 
        for i in sensor_dec_data if not (i['function']==6 and i['measure']==5 and i['target']==1) for j in i['irefs_target'] if
        j['submodel']==submodel and not j['network_side'] or j['cosim']==submodel and j['network_side']]))
    #add irefs Source/targets if source type==supervisory ctrl (3) and function == Individual signals for each target and target submodel != supervisory submodel
    data.append(''.join(["""(:IREF :N "Int_Ref_Sensor_{}_{}" :T {})\n""".format('Source' if submodel==supervisory_submodel else 'Target',j['iref'],'IN :F 208' if submodel==supervisory_submodel else 'OUT :F 224') 
                        for i in sensor_dec_data if i['target']==1 and i['function']==6 and i['source_type']==3 for j in i['irefs_target'] if
                        j['submodel']==submodel and not j['network_side'] and supervisory_submodel!=j['submodel'] or 
                        supervisory_submodel==submodel and supervisory_submodel!=j['submodel'] and not j['network_side']]))   
    #add irefs targets if target type==supervisory ctrl (3) and function == Individual signals for each target (6) for decoupling at supervisory side
    data.append(''.join(["""(:IREF :N "Int_Ref_Sensor_Target_{}" :T OUT :F 208)\n""".format(j['iref']) 
                        for i in sensor_dec_data  if i['target_type'] ==3 and i['source_type'] in(1,2) and i['function']==6 and i['target']==1 and i['measure'] ==5 
                        for j in i['irefs_source'] if supervisory_submodel==submodel and submodel!=j['submodel'] and not j['network_side']]))
    #add irefs targets if target type==supervisory ctrl (3) and function == Individual signals for each target (6) for decoupling at feature side
    data.append(''.join(["""(:IREF :N "Int_Ref_Sensor_Source_{}" :T IN :F 208)\n""".format(j['iref']) 
                        for i in sensor_dec_data if i['target_type'] ==3 and i['source_type'] in(1,2) and i['function']==6 and i['target']==1 and i['measure'] ==5 
                        for j in i['irefs_source'] if submodel==j['submodel'] and not j['network_side'] and not supervisory_submodel==submodel]))     
                        
                        
    print('***************************')

    
    #add Adder comp for function Average (3), Add (4), Same signal for all targets (5) if measure in (1,2,3,4) and source type in (1,2)
    data.append("".join(["""((:EO :N "Sensor_{}" :T ADDER_CONT)
 (:VAR :N INSIGNAL :B #S(MS-SPARSE DEFAULT-VALUE NIL DIMENSION 1 VALUE ({}{})))
 (:PAR :N COEFF :DIM ({}) :V #({}{}))
 (:PAR :N N_IN :V {}))\n""".format(str(i['sensor_id']),
                        " ".join(["""({} :SYSTEM "{}" "{}" {})""".format(conn[0], getMacroTypeName(i['source_type'])+'_'+conn[1][0].split('_')[1], getPMT2muxName(cur,conn[1][1]['conn_bundle_type_id'],conn[1][0].split('_')[3]), returnVarName(i['measure'])) 
                            for conn in enumerate([[j['iref'],getConnValuesByFeature(i['source_type'],j['iref'].split('_')[1],j['iref'].split('_')[3],cur,dictDB)] for j in i['irefs_source']],1) if i['measure'] in (1,2,3)]),
                        " ".join(["""({} :SYSTEM "{}" "{}" P)""".format(conn[0], getMacroTypeName(i['source_type'])+'_'+conn[1][0].split('_')[1], getMeterName(cur,conn[1][1]['conn_bundle_type_id'],conn[1][1]['conn_type_id'])) 
                            for conn in enumerate([[j['iref'],getConnValuesByFeature(i['source_type'],j['iref'].split('_')[1],j['iref'].split('_')[3],cur,dictDB)] for j in i['irefs_source']],1) if i['measure']==4]),
                        str(max(1,len([j for j in i['irefs_source']]))),
                        ' '.join(['1' for j in range(max(1,len([j for j in i['irefs_source']]))) if i['function']==4]),
                        ' '.join([str(round(1/max(1,len([j for j in i['irefs_source']])),5)) for z in range(max(1,len([j for j in i['irefs_source']]))) if i['function']==3]),
                        str(max(1,len([j for j in i['irefs_source']])))) 
                        for i in sensor_dec_data if i['function'] in (3,4,5) and i['measure'] in (1,2,3,4) and i['source_type'] in (1,2)]))
    print('**********----*****************')

    #Add Adder if source type in 1,2,3 and function Average, Add (3,4) and measure==Custom (5)        
    data.append("".join(["""((:EO :N "Sensor_{}" :T ADDER_CONT)
 (:VAR :N INSIGNAL :B #S(MS-SPARSE DEFAULT-VALUE NIL DIMENSION 1 VALUE ({})))
 (:PAR :N COEFF :DIM ({}) :V #({}))
 (:PAR :N N_IN :V {}))\n""".format(str(i['sensor_id']),
                        ''.join(["""({} -1 (INSIGNALLINK {}) 0)""".format(j[0],j[0]) 
                                if j[1]['submodel']==submodel and not j[1]['network_side'] or j[1]['cosim']==submodel and j[1]['network_side'] 
                                else """({} :SYSTEM "Co-simulation-macro" "{}<--{}" |data_var| {})""".format(j[0],submodel,j[1]['submodel'],import_counter[j[1]['submodel'] if j[1]['cosim'] else submodel]+getCosimCounter(sensor_dec_data,j[1]['iref'],submodel,cur,dictDB)) 
                            for j in enumerate([j for j in i['irefs_source'] 
                                if [True for j in i['irefs_target'] if j['submodel']==submodel and not j['network_side'] or submodel==j['cosim'] and j['network_side']]
                                or j['submodel']==submodel and not j['network_side'] or j['cosim']==submodel and j['network_side']],1)]),
                        getLength(i,submodel),
                        ' '.join(["1" if i['function'] in (4,5) else str(1/getLength(i,submodel)) 
                            for j in i['irefs_source'] 
                                if [True for j in i['irefs_target'] if j['submodel']==submodel and not j['network_side'] or submodel==j['cosim'] and j['network_side']]
                                or j['submodel']==submodel and not j['network_side'] or j['cosim']==submodel and j['network_side']]),
                        getLength(i,submodel)) 
        for i in sensor_dec_data if i['source_type'] in (1,2) and i['measure']==5 and i['function'] in (3,4,5) and 
            ([True for j in i['irefs_source'] if submodel==j['submodel'] and submodel!=j['cosim'] and not j['network_side']] or [True for j in i['irefs_target'] if submodel==j['submodel'] or submodel==j['cosim']])]))

    print('-------------')
    #add Min/Max comp for function Min(1) or Max(2) if measure in (1,2,3,4) and source type in (1,2)                    
    data.append("".join(["""((:EO :N "Sensor_{}" :T MINMAXD_CONT)
 (:VAR :N INSIGNAL :B #S(MS-SPARSE DEFAULT-VALUE NIL DIMENSION 1 VALUE ({}{})))
 (:PAR :N SELECTOR :V {}{})
 (:PAR :N N_IN :V {}))\n""".format(str(i['sensor_id']),
                        " ".join(["""({} :SYSTEM "{}" "{}" {})""".format(conn[0], getMacroTypeName(i['source_type'])+'_'+conn[1][0].split('_')[1], getPMT2muxName(cur,conn[1][1]['conn_bundle_type_id'],conn[1][0].split('_')[3]), returnVarName(i['measure'])) 
                            for conn in enumerate([[j['iref'],getConnValuesByFeature(i['source_type'],j['iref'].split('_')[1],j['iref'].split('_')[3],cur,dictDB)] for j in i['irefs_source']],1) if i['measure'] in (1,2,3)]),
                        " ".join(["""({} :SYSTEM "{}" "{}" P)""".format(conn[0], getMacroTypeName(i['source_type'])+'_'+conn[1][0].split('_')[1], getMeterName(cur,conn[1][1]['conn_bundle_type_id'],conn[1][1]['conn_type_id'])) 
                            for conn in enumerate([[j['iref'],getConnValuesByFeature(i['source_type'],j['iref'].split('_')[1],j['iref'].split('_')[3],cur,dictDB)] for j in i['irefs_source']],1) if i['measure']==4]),
                        "".join([j for j in ['1'] if i['function']==2]),"".join([j for j in ['0'] if i['function']==1]),
                        str(max(1,len([j for j in i['irefs_source']])))) 
                        for i in sensor_dec_data if i['function'] in (1,2) and i['measure'] in (1,2,3,4) and i['source_type'] in (1,2)]))  
                        
    print('------++-------')
    
    #Add Min/Max if source type in 1,2,3 and function is Min or Max (1,2) and measure==Custom (5)
    data.append("".join(["""((:EO :N "Sensor_{}" :T MINMAXD_CONT)
 (:VAR :N INSIGNAL :B #S(MS-SPARSE DEFAULT-VALUE NIL DIMENSION 1 VALUE ({})))
 (:PAR :N SELECTOR :V {}{})
 (:PAR :N N_IN :V {}))\n""".format(str(i['sensor_id']),
                        ''.join(["""({} -1 (INSIGNALLINK {}) 0)""".format(j[0],j[0]) 
                                if j[1]['submodel']==submodel and not j[1]['network_side'] or j[1]['cosim']==submodel and j[1]['network_side'] or not j[1]['cosim'] and not j[1]['network_side'] #todo update other sensors
                                else """({} :SYSTEM "Co-simulation-macro" "{}<--{}" |data_var| {})""".format(j[0],submodel,j[1]['submodel'],import_counter[j[1]['submodel'] if j[1]['cosim'] else submodel]+getCosimCounter(sensor_dec_data,j[1]['iref'],submodel,cur,dictDB))                                           
                            for j in enumerate([j for j in i['irefs_source'] 
                                if [True for j in i['irefs_target'] if j['submodel']==submodel and not j['network_side'] or submodel==j['cosim'] and j['network_side']]
                                or j['submodel']==submodel and not j['network_side'] or j['cosim']==submodel and j['network_side']],1)]),
                        "".join([j for j in ['1'] if i['function']==2]),"".join([j for j in ['0'] if i['function']==1]),
                        getLength(i,submodel)) 
        for i in sensor_dec_data if i['source_type'] in (1,2) and i['measure']==5 and i['function'] in (1,2) and 
            [True for j in i['irefs_source'] 
                if [True for j in i['irefs_target'] if j['submodel']==submodel and not j['network_side'] or submodel==j['cosim'] and j['network_side']]
                or j['submodel']==submodel and not j['network_side'] or j['cosim']==submodel and j['network_side']]]))                    
    print('------+++-------')       
                
    #add Adder comp for function  Individual signals for each target (6) if measure in (1,2,3,4)
    data.append("".join(["""((:EO :N "Sensor_{}" :T ADDER)
 (:VAR :N INSIGNAL :B #S(MS-SPARSE DEFAULT-VALUE NIL DIMENSION 1 VALUE ({}{})))
 (:PAR :N COEFF :DIM (1) :V #(1))
 (:PAR :N N_IN :V 1))\n""".format(j['iref'],
                        " ".join(["""(1 :SYSTEM "{}" "{}" {})""".format(getMacroTypeName(i['source_type'])+'_'+j['iref'].split('_')[1], getPMT2muxName(cur,getConnValuesByFeature(i['source_type'],j['iref'].split('_')[1],j['iref'].split('_')[3],cur,dictDB)['conn_bundle_type_id'],j['iref'].split('_')[3]), returnVarName(i['measure']))]),
                        " ".join(["""(1 :SYSTEM "{}" "{}" P)""".format(getMacroTypeName(i['source_type'])+'_'+j['iref'].split('_')[1], getMeterName(cur,getConnValuesByFeature(i['source_type'],j['iref'].split('_')[1],j['iref'].split('_')[3],cur,dictDB)['conn_bundle_type_id'],getConnValuesByFeature(i['source_type'],j['iref'].split('_')[1],j['iref'].split('_')[3],cur,dictDB)['conn_type_id']))])) 
                        for i in sensor_dec_data if i['function'] ==6 and i['measure'] in (1,2,3,4) for j in i['irefs_source']]))
    print('add Adder comp for function  Individual signals for each target (6) if measure in (1,2,3,4) finished')
                        
    #add Adder comp if function  Individual signals for each target (6) and target!=Custom(1) and source type in (3)
    data.append("".join(["""((:EO :N "Sensor_{}" :T ADDER_CONT)
 (:VAR :N INSIGNAL :B #S(MS-SPARSE DEFAULT-VALUE NIL DIMENSION 1 VALUE ({}))
 (:PAR :N COEFF :DIM (1) :V #(1))
 (:PAR :N N_IN :V 1))\n""".format(j['iref'],"(1 -1 (INSIGNALLINK 1) 0))" if submodel==j['submodel'] else 
 """(1 :SYSTEM "Co-simulation-macro" "{}<--{}" |data_var| {})""".format(submodel,j['submodel'],(import_counter[j['cosim']] if j['cosim'] else import_counter[submodel])+getCosimCounter(sensor_dec_data,j['iref'],submodel,cur,dictDB)))
                        for i in sensor_data if i['target']!=1 and i['function']==6 and i['source_type']==3 for j in i['irefs_source'] if
                        ([True for j in i['irefs_source'] if submodel==j['submodel'] and submodel!=j['cosim']] or [True for j in i['irefs_target'] if submodel==j['submodel'] or submodel==j['cosim']])]))

    #add Adder comp if function  Individual signals for each target (6) and target=Custom(1) and source type in (3) for decoupling option
    data.append("".join(["""((:EO :N "Sensor_{}" :T ADDER_CONT)
 (:VAR :N INSIGNAL :B #S(MS-SPARSE DEFAULT-VALUE NIL DIMENSION 1 VALUE ({})))
 (:PAR :N COEFF :DIM (1) :V #(1))
 (:PAR :N N_IN :V 1))\n""".format(j['iref'],"(1 -1 (INSIGNALLINK 1) 0)" if submodel==supervisory_submodel else 
    """(1 :SYSTEM "Co-simulation-macro" "{}<--{}" |data_var| {})""".format(j['submodel'],supervisory_submodel,import_counter[j['submodel'] if j['network_side'] else submodel]+getCosimCounter(sensor_dec_data,j['iref'],submodel,cur,dictDB)))
                        for i in sensor_dec_data if i['target']==1 and i['function']==6 and i['source_type']==3 for j in i['irefs_target'] if
                        j['submodel']==submodel and not j['network_side'] and supervisory_submodel!=j['submodel'] or 
                        supervisory_submodel==submodel and supervisory_submodel!=j['submodel'] and not j['network_side']]))

    #add Adder comp if function  Individual signals for each target (6) and target=Custom(1) and target type in (3) for decoupling option at network_side
    data.append("".join(["""((:EO :N "Sensor_{}" :T ADDER_CONT)
 (:VAR :N INSIGNAL :B #S(MS-SPARSE DEFAULT-VALUE NIL DIMENSION 1 VALUE ({})))
 (:PAR :N COEFF :DIM (1) :V #(1))
 (:PAR :N N_IN :V 1))\n""".format(j['iref'],"""(1 :SYSTEM "Co-simulation-macro" "{}<--{}" |data_var| {})""".format(supervisory_submodel,j['submodel'],import_counter[j['submodel']] + getCosimCounter(sensor_dec_data,j['iref'],submodel,cur,dictDB)))
                        for i in sensor_dec_data if i['target_type'] ==3 and i['source_type'] in(1,2) and i['function']==6 and i['target']==1 and i['measure'] ==5 
                        for j in i['irefs_source'] if submodel==supervisory_submodel and submodel!=j['submodel'] and not j['network_side']]))

    #add Adder comp if function  Individual signals for each target (6) and target=Custom(1) and target type in (3) for decoupling option at feature side
    data.append("".join(["""((:EO :N "Sensor_{}" :T ADDER_CONT)
 (:VAR :N INSIGNAL :B #S(MS-SPARSE DEFAULT-VALUE NIL DIMENSION 1 VALUE ((1 -1 (INSIGNALLINK 1) 0))))
 (:PAR :N COEFF :DIM (1) :V #(1))
 (:PAR :N N_IN :V 1))\n""".format(j['iref'])
                        for i in sensor_dec_data if i['target_type'] ==3 and i['source_type'] in(1,2) and i['function']==6 and i['target']==1 and i['measure'] ==5 
                        for j in i['irefs_source'] if submodel==j['submodel'] and not j['network_side'] and not supervisory_submodel==submodel]))  
                        
    #add Adder comp if function  Same signal for all targets (5) and source type in (3)                   
    data.append("".join(["""((:EO :N "Sensor_{}" :T ADDER_CONT)
 (:VAR :N INSIGNAL :B #S(MS-SPARSE DEFAULT-VALUE NIL DIMENSION 1 VALUE ({})))
 (:PAR :N COEFF :DIM (1) :V #(1))
 (:PAR :N N_IN :V 1))\n""".format(str(i['sensor_id']),
                        ''.join(["(1 -1 (INSIGNALLINK 1) 0)" if submodel==j['submodel'] else 
                        """(1 :SYSTEM "Co-simulation-macro" "{}<--{}" |data_var| {})""".format(submodel,j['submodel'],(import_counter[j['cosim']] if j['cosim'] else import_counter[submodel])+getCosimCounter(sensor_dec_data,j['iref'],submodel,cur,dictDB))
                        for j in i['irefs_source']]))
                        for i in sensor_dec_data if i['function']==5 and i['source_type']==3 and 
                        ([True for j in i['irefs_source'] if submodel==j['submodel'] and submodel!=j['cosim']] or [True for j in i['irefs_target'] if submodel==j['submodel'] or submodel==j['cosim']])]))
    print('+-----------*****------------')
    print(data)
    data.append('(CONNECTIONS\n')
    #Source connections to sensor if measure==Custom and not Individual signals for each target and source type in (1,2) and target type!=3
    data.append(''.join([""" (("Sensor_{}" (INSIGNALLINK {})) "Int_Ref_Sensor_Source_{}" 0 0 NIL)\n""".format(
        str(i['sensor_id']),str(j[0]),j[1]['iref']) 
        for i in sensor_dec_data if i['measure']==5 and i['function']!=6 and i['source_type'] in (1,2) and i['target_type']!=3 
        for j in enumerate([j for j in i['irefs_source'] 
                                if [True for j in i['irefs_target'] if j['submodel']==submodel and not j['network_side'] or submodel==j['cosim'] and j['network_side']]
                                or j['submodel']==submodel and not j['network_side'] or j['cosim']==submodel and j['network_side']],1)
            if j[1]['submodel']==submodel and not j[1]['network_side'] or j[1]['cosim']==submodel and j[1]['network_side']]))
    #Source connections to sensor if source type==supervisory ctrl (3) and ((traget!=Custom (1) and function == Individual signals for each target) or function==Same signal for all targets (5))
    data.append(''.join([""" (("Sensor_{}" (INSIGNALLINK 1)) "Int_Ref_Sensor_Source_{}" 0 0 NIL)\n""".format(
        j['iref'].split('_')[0] if i['function']==5 else j['iref'],j['iref']) 
        for i in sensor_dec_data if ((i['target']!=1 and i['function']==6) or i['function']==5) and i['source_type']==3 
        for j in i['irefs_source'] if submodel==j['submodel']]))
    #Source/target connections to sensor if source type==supervisory ctrl (3) and function == Individual signals for each target and target submodel != supervisory submodel
    data.append(''.join([""" (("Sensor_{}" {}) "Int_Ref_Sensor_{}_{}" 0 0 NIL)\n""".format(
                        j['iref'],
                        '(INSIGNALLINK 1)' if submodel==supervisory_submodel else 'OUTSIGNALLINK',
                        'Source' if submodel==supervisory_submodel else 'Target',j['iref']) 
                        for i in sensor_dec_data if i['target']==1 and i['function']==6 and i['source_type']==3 for j in i['irefs_target'] if
                        j['submodel']==submodel and not j['network_side'] and supervisory_submodel!=j['submodel'] or 
                        supervisory_submodel==submodel and supervisory_submodel!=j['submodel'] and not j['network_side']]))                                       
    #Source connections to sensor if measure==Custom and not Individual signals for each target and source type in (1,2) and target type==3
    data.append(''.join([""" (("Sensor_{}" (INSIGNALLINK {})) "Int_Ref_Sensor_Source_{}" 0 0 NIL)\n""".format(
        str(i['sensor_id']),str(j[0]),j[1]['iref']) 
        for i in sensor_dec_data if i['measure']==5 and i['function']!=6 and i['source_type'] in (1,2) and i['target_type']==3 
        for j in enumerate([j for j in i['irefs_source'] 
                                if [True for j in i['irefs_target'] if j['submodel']==submodel and not j['network_side'] or submodel==j['cosim'] and j['network_side']]
                                or j['submodel']==submodel and not j['network_side'] or j['cosim']==submodel and j['network_side']],1)
            if j[1]['submodel']==submodel and not j[1]['network_side'] or j[1]['cosim']==submodel and j[1]['network_side']]))
        
    #Target connections if not (function == Individual signals for each target (6) and meaure==custom(5) and target==Custom (1)
    data.append(''.join([""" (("Sensor_{}" OUTSIGNALLINK) "Int_Ref_Sensor_Target_{}" 0 0 NIL)\n""".format(str(i['sensor_id']) if i['function'] in (1,2,3,4,5) else j['iref'] ,j['iref']) 
        for i in sensor_dec_data  if not (i['function']==6 and i['measure']==5 and i['target']==1) for j in i['irefs_target'] if submodel==j['submodel'] and not j['network_side'] or submodel==j['cosim'] and j['network_side']]))      

    #Target connections if target type == supervisory and function ==Individual signals for each target (6) and meaure==custom(5) and target==Custom (1) for decoupling mode at network side
    data.append(''.join([""" (("Sensor_{}" OUTSIGNALLINK) "Int_Ref_Sensor_Target_{}" 0 0 NIL)\n""".format(j['iref'] ,j['iref']) 
        for i in sensor_dec_data if i['target_type'] ==3 and i['source_type'] in(1,2) and i['function']==6 and i['target']==1 and i['measure'] ==5 
        for j in i['irefs_source'] if supervisory_submodel==submodel and submodel!=j['submodel'] and not j['network_side']]))    

    #Target connections if target type == supervisory and function ==Individual signals for each target (6) and meaure==custom(5) and target==Custom (1) for decoupling mode at feature side
    data.append(''.join([""" (("Sensor_{}" (INSIGNALLINK 1)) "Int_Ref_Sensor_Source_{}" 0 0 NIL)\n""".format(j['iref'] ,j['iref']) 
        for i in sensor_dec_data if i['target_type'] ==3 and i['source_type'] in(1,2) and i['function']==6 and i['target']==1 and i['measure'] ==5 
        for j in i['irefs_source'] if submodel==j['submodel'] and not j['network_side'] and not supervisory_submodel==submodel]))                 

  
    data[-1]=data[-1].rstrip()+')'
    writeToFileFromList(data,dir,file)
    print('sensor macro idm finished')
    
def sensorMacroIdcData(submodel,supervisory_submodel,sensor_dec_data,sensor_data,cur,dictDB,dir,plugin_dir):
    #---------------------------sensor idc macro file--------------------------------
    file=dir+"""\\Sensor-macro.idc"""
    data=[""";IDA 5.11 Form UTF-8\n""","""(DOCUMENT-HEADER :TYPE SCHEMA :PAGE-WIDTH 178 :PAGE-HEIGHT 97)\n""","""(SELF-FRAME :AT ((352 190)) :R (342 176) :SLOT (:SELF) :DATA MACRO-OBJECT)\n"""]
    count_sensors=0                                      

    #add Adder comp if function  Individual signals for each target (6) and target=Custom(1) and source type in (3) for decoupling option
    data.append(''.join(["""(EQUATION-FRAME :AT ((41 {})) :R (16 16) :ICON "lib:adder.ids" :SLOT ("Sensor_{}") :NAME "Sensor_{}" :PADDING 3 :DATA :EO)\n""".format(
        str(50+35*i[0]),i[1],i[1]) 
                        for i in enumerate([j['iref'] for i in sensor_dec_data if i['target']==1 and i['function']==6 and i['source_type']==3 for j in i['irefs_target'] if
                        j['submodel']==submodel and not j['network_side'] and supervisory_submodel!=j['submodel'] or 
                        supervisory_submodel==submodel and supervisory_submodel!=j['submodel'] and not j['network_side']],1+count_sensors)]))
    data.append(''.join(["""(CONNECTION-LINE :AT ({}) :FIRST-LINK ("Sensor_{}" (1 0.531) {}) :LAST-LINK (:SELF (1.0 0.205) "Int_Ref_Sensor_{}_{}") :DIR {})\n""".format(
                        ('(237/10 {}) (10 {})' if submodel==supervisory_submodel else '(58 {}) (694 {})').format(str(50+35*i[0]),str(50+35*i[0])),
                        i[1],
                        '(INSIGNAL 1)' if submodel==supervisory_submodel else 'OUTSIGNALLINK',
                        'Source' if submodel==supervisory_submodel else 'Target',i[1],
                        ':LEFT :ARROW (4864 8 8)' if submodel==supervisory_submodel else ':RIGHT :ARROW (19 8 8)') 
                        for i in enumerate([j['iref']for i in sensor_dec_data if i['target']==1 and i['function']==6 and i['source_type']==3 for j in i['irefs_target'] if
                        j['submodel']==submodel and not j['network_side'] and supervisory_submodel!=j['submodel'] or 
                        supervisory_submodel==submodel and supervisory_submodel!=j['submodel'] and not j['network_side']],1+count_sensors)]))
    count_sensors+=len([j['iref'] for i in sensor_dec_data if i['target']==1 and i['function']==6 and i['source_type']==3 for j in i['irefs_target'] if
                        j['submodel']==submodel and not j['network_side'] and supervisory_submodel!=j['submodel'] or 
                        supervisory_submodel==submodel and supervisory_submodel!=j['submodel'] and not j['network_side']])

                        
    #add Adder comp for target type == supervisory contrl (3) if function (6)  measure in (5) and source type in (1,2) for decoupling mode
    data.append(''.join(["""(EQUATION-FRAME :AT ((41 {})) :R (16 16) :ICON "lib:adder.ids" :SLOT ("Sensor_{}") :NAME "Sensor_{}" :PADDING 3 :DATA :EO)\n""".format(
        str(50+35*i[0]),i[1],i[1]) 
        for i in enumerate([j['iref'] for i in sensor_dec_data if i['target_type'] ==3 and i['source_type'] in(1,2) and i['function']==6 and i['target']==1 and i['measure'] ==5 
                                for j in i['irefs_source'] if supervisory_submodel==submodel and submodel!=j['submodel'] and not j['network_side']],1+count_sensors)]))
    data.append(''.join(["""(CONNECTION-LINE :AT ((58 {}) (694 {})) :FIRST-LINK ("Sensor_{}" (1 0.531) OUTSIGNALLINK) :LAST-LINK (:SELF (1.0 0.205) "Int_Ref_Sensor_Target_{}") :DIR :RIGHT :ARROW (19 8 8))\n""".format(
        str(50+35*i[0]),str(50+35*i[0]),i[1],i[1]) 
        for i in enumerate([j['iref'] for i in sensor_dec_data if i['target_type'] ==3 and i['source_type'] in(1,2) and i['function']==6 and i['target']==1 and i['measure'] ==5 
                                for j in i['irefs_source'] if supervisory_submodel==submodel and submodel!=j['submodel'] and not j['network_side']],1+count_sensors)]))
    count_sensors+=len([j['iref'] for i in sensor_dec_data if i['target_type'] ==3 and i['source_type'] in(1,2) and i['function']==6 and i['target']==1 and i['measure'] ==5 
                                for j in i['irefs_source'] if supervisory_submodel==submodel and submodel!=j['submodel'] and not j['network_side']])

    #add Adder comp for function Average (3), Add (4), Same signal for all targets (5) if measure in (1,2,3,4) and source type in (1,2)
    data.append(''.join(["""(EQUATION-FRAME :AT ((41 {})) :R (16 16) :ICON "lib:adder.ids" :SLOT ("Sensor_{}") :NAME "Sensor_{}" :PADDING 3 :DATA :EO)\n""".format(
        str(50+35*i[0]),i[1]['sensor_id'],i[1]['sensor_id']) 
        for i in enumerate([i for i in sensor_data if i['function'] in (3,4,5) and i['measure'] in (1,2,3,4) and i['source_type'] in (1,2)],1+count_sensors)]))
    data.append(''.join(["""(CONNECTION-LINE :AT ((58 {}) (58 {}) (694 {})) :FIRST-LINK ("Sensor_{}" (1 0.531) OUTSIGNALLINK) :LAST-LINK (:SELF (1.0 0.205) "Int_Ref_Sensor_Target_{}") :DIR :RIGHT :ARROW (19 8 8))\n""".format(
        str(50+35*i[0]),str(50+35*i[0]+j[0]),str(50+35*i[0]+j[0]),j[1].split('_')[0],j[1]) 
        for i in enumerate([i for i in sensor_data if i['function'] in (3,4,5) and i['measure'] in (1,2,3,4) and i['source_type'] in (1,2)],1+count_sensors) for j in enumerate(i[1]['irefs_target'],0)]))
    count_sensors+=len([i for i in sensor_data if i['function'] in (3,4,5) and i['measure'] in (1,2,3,4) and i['source_type'] in (1,2)])

    print('add min/max comp for function Min(1),Max(2)) if measure in (1,2,3,4) and source type in (1,2)')   
    #add min/max comp for function Min(1),Max(2)) if measure in (1,2,3,4) and source type in (1,2)
    data.append(''.join(["""(EQUATION-FRAME :AT ((41 {})) :R (16 16) :ICON "lib:minmaxd.ids" :SLOT ("Sensor_{}") :NAME "Sensor_{}" :PADDING 3 :DATA :EO)\n""".format(
        str(50+35*i[0]),i[1]['sensor_id'],i[1]['sensor_id']) 
        for i in enumerate([i for i in sensor_data if i['function'] in (1,2) and i['measure'] in (1,2,3,4) and i['source_type'] in (1,2)],1+count_sensors)]))
    data.append(''.join(["""(CONNECTION-LINE :AT ((58 {}) (58 {}) (694 {})) :FIRST-LINK ("Sensor_{}" (1 0.531) OUTSIGNALLINK) :LAST-LINK (:SELF (1.0 0.205) "Int_Ref_Sensor_Target_{}") :DIR :RIGHT :ARROW (19 8 8))\n""".format(
        str(50+35*i[0]),str(50+35*i[0]+j[0]),str(50+35*i[0]+j[0]),j[1].split('_')[0],j[1]) 
        for i in enumerate([i for i in sensor_data if i['function'] in (1,2) and i['measure'] in (1,2,3,4) and i['source_type'] in (1,2)],1+count_sensors) for j in enumerate(i[1]['irefs_target'],0)]))
    count_sensors+=len([i for i in sensor_data if i['function'] in (1,2) and i['measure'] in (1,2,3,4) and i['source_type'] in (1,2)])
    print('add min/max comp for function Min(1),Max(2)) if measure in (1,2,3,4) and source type in (1,2) finished')       

    #add Adder comp for function Individual signals for each target (6) if measure in (1,2,3,4) and source type in (1,2) for decoupling mode if network_side
    data.append(''.join(["""(EQUATION-FRAME :AT ((41 {})) :R (16 16) :ICON "lib:adder.ids" :SLOT ("Sensor_{}") :NAME "Sensor_{}" :PADDING 3 :DATA :EO)\n""".format(
        str(50+35*i[0]),i[1],i[1]) 
        for i in enumerate([j for i in sensor_data if i['function']==6 and i['measure'] in (1,2,3,4) and i['source_type'] in (1,2) for j in i['irefs_source']],1+count_sensors)]))
    data.append(''.join(["""(CONNECTION-LINE :AT ((58 {}) (694 {})) :FIRST-LINK ("Sensor_{}" (1 0.531) OUTSIGNALLINK) :LAST-LINK (:SELF (1.0 0.205) "Int_Ref_Sensor_Target_{}") :DIR :RIGHT :ARROW (19 8 8))\n""".format(
        str(50+35*sensor[0]),str(50+35*sensor[0]),sensor[1],sensor[1]) 
        for sensor in enumerate([j for i in sensor_data if i['function']==6 and i['measure'] in (1,2,3,4) and i['source_type'] in (1,2) for j in i['irefs_source']],1+count_sensors)]))
    count_sensors+=len([j for i in sensor_data if i['function']==6 and i['measure'] in (1,2,3,4) and i['source_type'] in (1,2) for j in i['irefs_source']])  
    
    #add Adder comp for function Individual signals for each target (6) if measure==5 and source type in (1,2) for decoupling mode if feature side
    data.append(''.join(["""(EQUATION-FRAME :AT ((41 {})) :R (16 16) :ICON "lib:adder.ids" :SLOT ("Sensor_{}") :NAME "Sensor_{}" :PADDING 3 :DATA :EO)\n""".format(
        str(50+35*i[0]),i[1]['iref'],i[1]['iref']) 
        for i in enumerate([j for i in sensor_dec_data if i['target_type'] ==3 and i['source_type'] in(1,2) and i['function']==6 and i['target']==1 and i['measure'] ==5 
        for j in i['irefs_source'] if submodel==j['submodel'] and not j['network_side'] and not supervisory_submodel==submodel],1+count_sensors)]))                                    
    data.append(''.join(["""(CONNECTION-LINE :AT ((237/10 {}) (10 {})) :FIRST-LINK ("Sensor_{}" (1 0.531) OUTSIGNALLINK) :LAST-LINK (:SELF (1.0 0.205) "Int_Ref_Sensor_Source_{}") :DIR :LEFT :ARROW (4864 8 8))\n""".format(
        str(50+35*sensor[0]),str(50+35*sensor[0]),sensor[1]['iref'],sensor[1]['iref']) 
        for sensor in enumerate([j for i in sensor_dec_data if i['target_type'] ==3 and i['source_type'] in(1,2) and i['function']==6 and i['target']==1 and i['measure'] ==5 
        for j in i['irefs_source'] if submodel==j['submodel'] and not j['network_side'] and not supervisory_submodel==submodel],1+count_sensors)]))
    count_sensors+=len([j for i in sensor_dec_data if i['target_type'] ==3 and i['source_type'] in(1,2) and i['function']==6 and i['target']==1 and i['measure'] ==5 
                        for j in i['irefs_source'] if submodel==j['submodel'] and not j['network_side'] and not supervisory_submodel==submodel])                
    
    #add Min/Max comp if function (1,2) and measure== Custom(5) and source type in (1,2)
    data.append(''.join(["""(EQUATION-FRAME :AT ((41 {})) :R (16 16) :ICON "lib:minmaxd.ids" :SLOT ("Sensor_{}") :NAME "Sensor_{}" :PADDING 3 :DATA :EO)\n""".format(
        str(50+35*i[0]),i[1]['sensor_id'],i[1]['sensor_id'])
        for i in enumerate([i for i in sensor_dec_data if i['source_type'] in (1,2) and i['measure']==5 and i['function'] in (1,2) and 
           [True for j in i['irefs_source'] 
            if [True for j in i['irefs_target'] if j['submodel']==submodel and not j['network_side'] or submodel==j['cosim'] and j['network_side']]
            or j['submodel']==submodel and not j['network_side'] or j['cosim']==submodel and j['network_side']]],1+count_sensors)]))          
    data.append(''.join(["""(CONNECTION-LINE :AT ((58 {}) (58 {}) (694 {})) :FIRST-LINK ("Sensor_{}" (1 0.531) OUTSIGNALLINK) :LAST-LINK (:SELF (1.0 0.205) "Int_Ref_Sensor_Target_{}") :DIR :RIGHT :ARROW (19 8 8))\n""".format(
        str(50+35*i[0]),str(50+35*i[0]+j[0]),str(50+35*i[0]+j[0]),i[1]['sensor_id'],j[1])
        for i in enumerate([i for i in sensor_dec_data if i['source_type'] in (1,2) and i['measure']==5 and i['function'] in (1,2) and
            [True for j in i['irefs_source'] 
                if [True for j in i['irefs_target'] if j['submodel']==submodel and not j['network_side'] or submodel==j['cosim'] and j['network_side']]
                or j['submodel']==submodel and not j['network_side'] or j['cosim']==submodel and j['network_side']]],1+count_sensors) 
        for j in enumerate([j['iref'] for j in i[1]['irefs_target'] if submodel==j['submodel']],0)]))
    data.append(''.join(["""(CONNECTION-LINE :AT ((237/10 {}) (10 {})) :FIRST-LINK ("Sensor_{}" (1 0.491) (INSIGNALLINK {})) :LAST-LINK (:SELF (0.0 0.144) "Int_Ref_Sensor_Source_{}") :DIR :LEFT :ARROW (4864 8 8))\n""".format(
        str(50+35*i[0]+j[0]),str(50+35*i[0]+j[0]),i[1]['sensor_id'],str(j[0]+1),j[1])
        for i in enumerate([i for i in sensor_dec_data if i['source_type'] in (1,2) and i['measure']==5 and i['function'] in (1,2) and
            [True for j in i['irefs_source'] 
                if [True for j in i['irefs_target'] if j['submodel']==submodel and not j['network_side'] or submodel==j['cosim'] and j['network_side']]
                or j['submodel']==submodel and not j['network_side'] or j['cosim']==submodel and j['network_side']]],1+count_sensors) 
        for j in enumerate([j['iref'] for j in i[1]['irefs_source'] if submodel==j['submodel']],0)]))
    count_sensors+=len([i for i in sensor_dec_data if i['source_type'] in (1,2) and i['measure']==5 and i['function'] in (1,2) and 
            [True for j in i['irefs_source'] 
                if [True for j in i['irefs_target'] if j['submodel']==submodel and not j['network_side'] or submodel==j['cosim'] and j['network_side']]
                or j['submodel']==submodel and not j['network_side'] or j['cosim']==submodel and j['network_side']]])      
    
    #Adder comp if function (3,4,5) and measure== Custom(5) and source type in (1,2)
    data.append(''.join(["""(EQUATION-FRAME :AT ((41 {})) :R (16 16) :ICON "lib:adder.ids" :SLOT ("Sensor_{}") :NAME "Sensor_{}" :PADDING 3 :DATA :EO)\n""".format(
        str(50+35*i[0]),i[1]['sensor_id'],i[1]['sensor_id'])
        for i in enumerate([i for i in sensor_dec_data if i['source_type'] in (1,2) and i['measure']==5 and i['function'] in (3,4,5) and 
            ([True for j in i['irefs_source'] if submodel==j['submodel'] and submodel!=j['cosim'] and not j['network_side']] or [True for j in i['irefs_target'] if submodel==j['submodel'] or submodel==j['cosim']])],1+count_sensors)]))
    data.append(''.join(["""(CONNECTION-LINE :AT ((58 {}) (58 {}) (694 {})) :FIRST-LINK ("Sensor_{}" (1 0.531) OUTSIGNALLINK) :LAST-LINK (:SELF (1.0 0.205) "Int_Ref_Sensor_Target_{}") :DIR :RIGHT :ARROW (19 8 8))\n""".format(
        str(50+35*i[0]),str(50+35*i[0]+j[0]),str(50+35*i[0]+j[0]),i[1]['sensor_id'],str(j[1]['iref']))
        for i in enumerate([i for i in sensor_dec_data if i['source_type'] in (1,2) and i['measure']==5 and i['function'] in (3,4,5)],1+count_sensors) for j in enumerate([j for j in i[1]['irefs_target'] if j['submodel']==submodel and not j['network_side'] or j['cosim']==submodel and j['network_side']],0)]))
    data.append(''.join(["""(CONNECTION-LINE :AT ((237/10 {}) (10 {})) :FIRST-LINK ("Sensor_{}" (1 0.491) (INSIGNALLINK {})) :LAST-LINK (:SELF (0.0 0.144) "Int_Ref_Sensor_Source_{}") :DIR :LEFT :ARROW (4864 8 8))\n""".format(
        str(50+35*i[0]+j[0]),str(50+35*i[0]+j[0]),str(i[1]['sensor_id']),str(j[0]+1),str(j[1]['iref']))
        for i in enumerate([i for i in sensor_dec_data if i['source_type'] in (1,2) and i['measure']==5 and i['function'] in (3,4,5)],1+count_sensors) for j in enumerate([j for j in i[1]['irefs_source'] if j['submodel']==submodel and not j['network_side'] or j['cosim']==submodel and j['network_side']],0)]))
    count_sensors+=len([i for i in sensor_dec_data if i['source_type'] in (1,2) and i['measure']==5 and i['function'] in (3,4,5) and ([True for j in i['irefs_source'] if submodel==j['submodel'] and submodel!=j['cosim'] and not j['network_side']] or [True for j in i['irefs_target'] if submodel==j['submodel'] or submodel==j['cosim']])])  
    
    #add Adder comp if function Same signal for all targets (5) and source type in (3)
    data.append(''.join(["""(EQUATION-FRAME :AT ((41 {})) :R (16 16) :ICON "lib:adder.ids" :SLOT ("Sensor_{}") :NAME "Sensor_{}" :PADDING 3 :DATA :EO)\n""".format(
        str(50+35*i[0]),i[1]['sensor_id'],i[1]['sensor_id'])
        for i in enumerate([i for i in sensor_data if i['function']==5 and i['source_type']==3],1+count_sensors)]))
    data.append(''.join(["""(CONNECTION-LINE :AT ((58 {}) (58 {}) (694 {})) :FIRST-LINK ("Sensor_{}" (1 0.531) OUTSIGNALLINK) :LAST-LINK (:SELF (1.0 0.205) "Int_Ref_Sensor_Target_{}") :DIR :RIGHT :ARROW (19 8 8))\n""".format(
        str(50+35*i[0]),str(50+35*i[0]+j[0]),str(50+35*i[0]+j[0]),i[1]['sensor_id'],j[1])
        for i in enumerate([i for i in sensor_dec_data if i['function']==5 and i['source_type']==3 and 
        ([True for j in i['irefs_source'] if submodel==j['submodel'] and submodel!=j['cosim']] or [True for j in i['irefs_target'] if submodel==j['submodel'] or submodel==j['cosim']])],1+count_sensors) 
        for j in enumerate([j['iref'] for j in i[1]['irefs_target'] if submodel==j['submodel']],0)]))
    data.append(''.join(["""(CONNECTION-LINE :AT ((237/10 {}) (10 {})) :FIRST-LINK ("Sensor_{}" (1 0.491) (INSIGNALLINK 1)) :LAST-LINK (:SELF (0.0 0.144) "Int_Ref_Sensor_Source_{}") :DIR :LEFT :ARROW (4864 8 8))\n""".format(
        str(50+35*i[0]),str(50+35*i[0]),i[1]['sensor_id'],j['iref'])
        for i in enumerate([i for i in sensor_dec_data if i['function']==5 and i['source_type']==3 and
        ([True for j in i['irefs_source'] if submodel==j['submodel'] and submodel!=j['cosim']] or [True for j in i['irefs_target'] if submodel==j['submodel'] or submodel==j['cosim']])],1+count_sensors) 
        for j in i[1]['irefs_source'] if submodel==j['submodel']]))
    count_sensors+=len([i for i in sensor_data if i['function']==5 and i['source_type']==3])   

    #add Adder comp if (function  Individual signals for each target (6) and target!=Custom(1))) and source type in (3)
    data.append(''.join(["""(EQUATION-FRAME :AT ((41 {})) :R (16 16) :ICON "lib:adder.ids" :SLOT ("Sensor_{}") :NAME "Sensor_{}" :PADDING 3 :DATA :EO)\n""".format(
        str(50+35*sensor[0]),sensor[1],sensor[1])
        for sensor in enumerate([j for i in sensor_dec_data if i['function']==6 and i['target']!=1 and i['source_type']==3 
        for j in i['irefs_source'] if ([True for j in i['irefs_source'] if submodel==j['submodel'] and submodel!=j['cosim']] or [True for j in i['irefs_target'] if submodel==j['submodel'] or submodel==j['cosim']])],count_sensors+1)]))
    data.append(''.join(["""(CONNECTION-LINE :AT ((237/10 {}) (10 {})) :FIRST-LINK ("Sensor_{}" (1 0.491) (INSIGNALLINK 1)) :LAST-LINK (:SELF (0.0 0.144) "Int_Ref_Sensor_Source_{}") :DIR :LEFT :ARROW (4864 8 8))\n""".format(
        str(50+35*sensor[0]),sensor[1],sensor[1])
        for sensor in enumerate([j for i in sensor_data if i['function']==5 and i['target_type']==3],1+count_sensors) for j in enumerate(i['irefs_target'],0)]))
    count_sensors+=len([j for i in sensor_data if i['function']==6 and i['target']!=1 and i['source_type']==3 for j in i['irefs_source']])                 

    
    dir=plugin_dir+"""\\models\\{}\\{}""".format(dictDB['projectName'],dictDB['versionName'])
    writeToFileFromList(data,dir,file)
    
def sensorProjectIdmConns(submodel,supervisory_submodel,sensor_dec_data,idm_conn):
    #------------------idm project--------------------------
    #target connections from Sensor to feature if target==Custom (1) and not (function == Individual signals for each target (6) and measure==custom (5))
    idm_conn+=''.join(["""\n (("Sensor-macro" "Int_Ref_Sensor_Target_{}") ("{}{}" "Int_Ref_Sensor_Target_{}") 0 0 NIL)""".format(
        j['iref'],getMacroTypeName(i['target_type']),'_'+j['iref'].split('_')[1] if i['target_type']!=3 else '',j['iref'].split('_')[0] if i['target_type'] in (1,2) else j['iref']) 
        for i in sensor_dec_data if i['target']==1 and not (i['function']==6 and i['measure']==5) for j in i['irefs_target'] if submodel==j['submodel'] and not j['network_side'] or submodel==j['cosim'] and j['network_side']])
        
    #source connections from Sensor to feature if not (function == Individual signals for each target (6) and target ==custom (1))
    idm_conn+=''.join(["""\n (("Sensor-macro" "Int_Ref_Sensor_Source_{}") ("{}{}" "Int_Ref_Sensor_Source_{}") 0 0 NIL)""".format(
        j['iref'],getMacroTypeName(i['source_type']),'_'+j['iref'].split('_')[1] if i['source_type']!=3 else '',j['iref'].split('_')[0] if i['source_type']!=3 else j['iref'])
        for i in sensor_dec_data if i['measure']==5 and not (i['function']==6 and i['target']==1) for j in i['irefs_source'] if submodel==j['submodel'] and not j['network_side'] or submodel==j['cosim'] and j['network_side']])

    #source connections from type supervisory ctrl to sensor if target type ==Customer, Plant (1,2) and function== Individual signals for each target (6) and target [5]==custom (1)
#    idm_conn+=''.join(["""\n (("Supervisory_control" "Int_Ref_Sensor_Source_{}") ("Sensor-macro" "Int_Ref_Sensor_Source_{}") 0 0 NIL)""".format(j['iref'],j['iref'])
#        for i in sensor_dec_data if i['target']==1 and i['function']==6 and i['source_type']==3 for j in i['irefs_target'] if
#        supervisory_submodel==submodel and supervisory_submodel==j['submodel'] or supervisory_submodel==submodel and submodel==j['cosim'] and j['network_side']])
    #source connections from type supervisory ctrl to sensor if target type ==Customer, Plant (1,2) and function== Same signal for each target (5) ==custom (1)
    idm_conn+=''.join(["""\n (("Supervisory_control" "Int_Ref_Sensor_Source_{}") ("Sensor-macro" "Int_Ref_Sensor_Source_{}") 0 0 NIL)""".format(j['iref'],j['iref'])
        for i in sensor_dec_data if i['target']==1 and i['function']==5 and i['source_type']==3 for j in i['irefs_source'] if
        supervisory_submodel==submodel and supervisory_submodel==j['submodel'] or supervisory_submodel==submodel and submodel==j['cosim'] and j['network_side']])
    #target connections from type supervisory ctrl to sensor if target type ==Customer, Plant (1,2) and function== Individual signals for each target (6) and target [5]==custom (1)
    idm_conn+=''.join(["""\n (("Sensor-macro" "Int_Ref_Sensor_Target_{}") ("{}{}" "Int_Ref_Sensor_Target_{}") 0 0 NIL)""".format(j['iref'],getMacroTypeName(i['target_type']),'_'+j['iref'].split('_')[1] if i['target_type']!=3 else '',j['iref'].split('_')[0])
        for i in sensor_dec_data if i['target']==1 and i['function']==6 and i['source_type']==3 for j in i['irefs_target'] if
        j['submodel']==submodel and not j['network_side'] and supervisory_submodel!=j['submodel']])
                        
    #source connections from type supervisory ctrl to feature if target type Customer, Plant (1,2) and function== Individual signals for each target (6) and target [5]==custom (1)
    idm_conn+=''.join(["""\n (("Supervisory_control" "Int_Ref_Sensor_Source_{}") ("{}_{}" "Int_Ref_Sensor_Target_{}") 0 0 NIL)""".format(
        j['iref'],getMacroTypeName(i['target_type']),j['iref'].split('_')[1],j['iref'].split('_')[0]) 
        for i in sensor_dec_data if i['source_type']==3 and i['target_type'] in (1,2) and i['function']==6 and i['target']==1 for j in i['irefs_target'] if 
        supervisory_submodel==submodel and supervisory_submodel==j['submodel'] or supervisory_submodel==submodel and submodel==j['cosim'] and j['network_side']])
    #connections from feature to supervisory if target type ==3 and source type in (1,2) supervisory ctrl (3) and function == Individual signals for each target (6) and target==Custom (1) and measure = Custom (5)
    idm_conn+=''.join(["""\n (("{}_{}" "Int_Ref_Sensor_Source_{}") ("Supervisory_control" "Int_Ref_Sensor_Target_{}") 0 0 NIL)""".format(
        getMacroTypeName(i['source_type']),j['iref'].split('_')[1],j['iref'].split('_')[0],j['iref']) 
        for i in sensor_dec_data if i['target_type'] ==3 and i['source_type'] in(1,2) and i['function']==6 and i['target']==1 and i['measure'] ==5 
        for j in i['irefs_source'] if supervisory_submodel==submodel and (submodel==j['submodel'] or submodel==j['cosim'] and j['network_side'])])
    #connections from Sensor to supervisory if target type == supervisory ctrl (3) and source type in (1,2) and function == Individual signals for each target (6) and target==Custom (1) and measure = Custom (5) for decoupling mode if network side
    idm_conn+=''.join(["""\n (("Sensor-macro" "Int_Ref_Sensor_Target_{}") ("Supervisory_control" "Int_Ref_Sensor_Target_{}") 0 0 NIL)""".format(
       j['iref'],j['iref']) 
        for i in sensor_dec_data if i['target_type'] ==3 and i['source_type'] in(1,2) and i['function']==6 and i['target']==1 and i['measure'] ==5 
        for j in i['irefs_source'] if supervisory_submodel==submodel and submodel!=j['submodel'] and not j['network_side']])
    #connections from Sensor to supervisory if target type == supervisory ctrl (3) and source type in (1,2) and function == Individual signals for each target (6) and target==Custom (1) and measure = Custom (5) for decoupling at feature side
    idm_conn+=''.join(["""\n (("{}_{}" "Int_Ref_Sensor_Source_{}")("Sensor-macro" "Int_Ref_Sensor_Source_{}") 0 0 NIL)""".format(getMacroTypeName(i['source_type']),j['iref'].split('_')[1],j['iref'].split('_')[0],j['iref']) 
        for i in sensor_dec_data if i['target_type'] ==3 and i['source_type'] in(1,2) and i['function']==6 and i['target']==1 and i['measure'] ==5 
        for j in i['irefs_source'] if submodel==j['submodel'] and not j['network_side'] and not supervisory_submodel==submodel])
        
    return idm_conn
    
def sensorProjectIdmMacro(submodel,supervisory_submodel,sensor_dec_data,idm):
    #----------sensor macro------------------
    idm+="""\n((MACRO-OBJECT :N "Sensor-macro" :T ICE-MACRO :ETM 3857526820 :STM 3857526845){}{}{}{}{}{}{}{})""".format(
        #iref sources if source type Customer, Plant (1,2) and measure==Custom (5) and not (function == Individual signals for each target (6) and target [5]==custom (1))
        ''.join(["""\n (:IREF :N "Int_Ref_Sensor_Source_{}" :T IN :F 208)""".format(j['iref']) 
            for i in sensor_dec_data if i['measure']==5 and i['source_type'] in (1,2) and not (i['function']==6 and i['target']==1) for j in i['irefs_source'] if submodel==j['submodel'] and not j['network_side'] or submodel==j['cosim'] and j['network_side']]),
        #iref sources if type is supervisory ctrl (3) and function == Same signal for all targets (5)
        ''.join(["""\n (:IREF :N "Int_Ref_Sensor_Source_{}" :T IN :F 208)""".format(j['iref'])                   
            for i in sensor_dec_data if i['source_type']==3 and i['function']==5 for j in i['irefs_source'] if supervisory_submodel==submodel]),
        #iref sources if type is supervisory ctrl (3) and function== Individual signals for each target (6)
        ''.join(["""\n (:IREF :N "Int_Ref_Sensor_Source_{}" :T IN :F 208)""".format(j['iref']) 
            for i in sensor_dec_data if i['source_type']==3 and i['function']==6 for j in i['irefs_target'] if supervisory_submodel==submodel and supervisory_submodel!=j['submodel'] and not j['network_side']]),
        #iref targets if source type is supervisory ctrl (3) and function== Individual signals for each target (6)
        ''.join(["""\n (:IREF :N "Int_Ref_Sensor_Target_{}" :T OUT :F 224)""".format(j['iref']) 
            for i in sensor_dec_data if i['source_type']==3 and i['function']==6 for j in i['irefs_target'] if j['submodel']==submodel and not j['network_side'] and supervisory_submodel!=j['submodel']]),
        #iref targets if target type Customer, Plant (1,2) and target ==Custom (1) and not (function == Individual signals for each target (6) and measure==custom (5))
        ''.join(["""\n (:IREF :N "Int_Ref_Sensor_Target_{}" :T OUT :F 224)""".format(j['iref']) 
            for i in sensor_dec_data if i['target']==1 and i['target_type'] in (1,2) and not (i['function']==6 and i['measure']==5) for j in i['irefs_target'] if submodel==j['submodel'] and not j['network_side'] or submodel==j['cosim'] and j['network_side']]),
        #iref targets if target type supervisory ctrl (3) and not (function== Individual signals for each target (6) and measure==custom)
        ''.join(["""\n (:IREF :N "Int_Ref_Sensor_Target_{}" :T OUT :F 224)""".format(j['iref']) 
            for i in sensor_dec_data if i['target_type']==3 and not (i['function']==6 and i['measure']==5) 
            for j in i['irefs_target'] if submodel==j['submodel'] and not j['network_side'] or submodel==j['cosim'] and j['network_side']]),
        #iref targets if target type supervisory ctrl (3) and function== Individual signals for each target (6) for decoupling at network side
        ''.join(["""\n (:IREF :N "Int_Ref_Sensor_Target_{}" :T OUT :F 224)""".format(j['iref']) 
            for i in sensor_dec_data if i['target_type']==3 and i['function']==6
            for j in i['irefs_source'] if supervisory_submodel==submodel and submodel!=j['submodel'] and not j['network_side']]),
        #irefs targets if target type==supervisory ctrl (3) and function == Individual signals for each target (6) for decoupling at feature side
        ''.join(["""\n (:IREF :N "Int_Ref_Sensor_Source_{}" :T IN :F 208)""".format(j['iref']) 
            for i in sensor_dec_data if i['target_type'] ==3 and i['source_type'] in(1,2) and i['function']==6 and i['target']==1 and i['measure'] ==5 
            for j in i['irefs_source'] if submodel==j['submodel'] and not j['network_side'] and not supervisory_submodel==submodel]))
    return idm