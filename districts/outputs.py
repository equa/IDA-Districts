import psycopg2
import psycopg2.extras
from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT

from .utility_functions.files import *
from .utility_functions.db import *
from .utility_functions.dialog import *
from .utility_functions.topology import *
from .utility_functions.workers import APISignals
from .update_sensors import *

from qgis.PyQt.QtCore import QObject, pyqtSlot, pyqtSignal,QRunnable

def writeMacroResultsIdm(config,cur,dir,requestedOutputs,sensor_dec_data,added_sensor_info):
    #print(added_sensor_info)
    filedata=[""";IDA {} Data UTF-8
(DOCUMENT-HEADER :TYPE DISTRICTS-MACRO :D "Districts macro" :APP (DISTRICTS :VER {}))\n""".format(getIDAVersion(config),getIDADistrictsVersion(config))]

    #add irefs targets if target type==results (4)
    filedata.append(''.join(["""(:IREF :N "Int_Ref_Sensor_Target_{}" :T IN :F 209)\n""".format(j['iref']) 
                        for i in sensor_dec_data  if i['target_type'] ==4 
                        for j in i['irefs_target']]))
    connections=[]
    
    #----------customers-----------
    #-------tsup
    #Tsup mean c
    if requestedOutputs['tsup_mean_c_kpi'] or requestedOutputs['tsup_mean_c_system']:
        filedata.append("""((MODEL :N "Tsup_mean_c" :T |Gain|){}){}\n""".format(
            """ (:VAR :N |y_var| :L "Tsup_mean_c_outputfile" :AS "Tsup mean customers")""" if requestedOutputs['tsup_mean_c_system'] else "",
            """\n(OUTPUT-FILE :N "Tsup_mean_c_outputfile" :T OUTPUT-FILE :COL T :STM 1)"""if requestedOutputs['tsup_mean_c_system'] else ""))
        connections.append(""" (("Tsup_mean_c" |u|) "Int_Ref_Sensor_Target_{}_X_X_X" 0 0 NIL)""".format(added_sensor_info['tsup_mean_c_system']))
    if requestedOutputs['tsup_mean_c_kpi']:
        filedata.append("""((MODEL :N "Tsup_mean_c_kpi" :T |SlidingAverage|)
 (:VAR :N |u_var| :IV #S(MS-SPARSE DEFAULT-VALUE 0.0 DIMENSION 1 VALUE NIL) :B #S(MS-SPARSE DEFAULT-VALUE NIL DIMENSION 1 VALUE ((1 -1 (|u| 1) 0))))
 (:VAR :N |uMean_var| :V 37.78 :L "Tsup_mean_c_kpi_outputfile")
 (:PAR :N |interval| :V 1.0E12)
 (:PAR :N |n| :V 2))
(OUTPUT-FILE :N "Tsup_mean_c_kpi_outputfile" :T OUTPUT-FILE :COL T :STM 1)\n""")
        connections.append(""" (("Tsup_mean_c_kpi" (|u| 1)) ("Tsup_mean_c" |y|) 0 0 NIL)""")
    #Tsup min c
    if requestedOutputs['tsup_min_c_kpi'] or requestedOutputs['tsup_min_c_system']:
        filedata.append("""((MODEL :N "Tsup_min_c" :T |Gain|){}){}\n""".format(
            """\n (:VAR :N |y_var| :L "Tsup_min_c_outputfile" :AS "Tsup min customers")""" if requestedOutputs['tsup_min_c_system'] else "",
            """\n(OUTPUT-FILE :N "Tsup_min_c_outputfile" :T OUTPUT-FILE :COL T :STM 1)"""if requestedOutputs['tsup_min_c_system'] else ""))
        connections.append(""" (("Tsup_min_c" |u|) "Int_Ref_Sensor_Target_{}_X_X_X" 0 0 NIL)""".format(added_sensor_info['tsup_min_c_system']))
    if requestedOutputs['tsup_min_c_kpi']:
        filedata.append("""((MODEL :N "Tsup_min_c_kpi" :T |SnapMinMax|)
 (:VAR :N |u_var| :IV #S(MS-SPARSE DEFAULT-VALUE 0.0 DIMENSION 1 VALUE NIL) :B #S(MS-SPARSE DEFAULT-VALUE NIL DIMENSION 1 VALUE ((1 -1 (|u| 1) 0))))
 (:VAR :N |uMin| :IV #S(MS-SPARSE DEFAULT-VALUE 0.0 DIMENSION 1 VALUE NIL) :L #S(MS-SPARSE DEFAULT-VALUE OFF DIMENSION 1 VALUE ((1 . "Tsup_min_c_kpi_outputfile"))) :AS #S(MS-SPARSE DEFAULT-VALUE NIL DIMENSION 1 VALUE ((1 . "Tsup_min_c_kpi")))))
(OUTPUT-FILE :N "Tsup_min_c_kpi_outputfile" :T OUTPUT-FILE :COL T :STM 1)\n""")
        connections.append(""" (("Tsup_min_c_kpi" (|u| 1)) ("Tsup_min_c" |y|) 0 0 NIL)""")
    #Tsup max c
    if requestedOutputs['tsup_max_c_kpi'] or requestedOutputs['tsup_max_c_system']:
        filedata.append("""((MODEL :N "Tsup_max_c" :T |Gain|){}){}\n""".format(
            """\n (:VAR :N |y_var| :L "Tsup_max_c_outputfile" :AS "Tsup max customers")""" if requestedOutputs['tsup_max_c_system'] else "",
            """\n(OUTPUT-FILE :N "Tsup_max_c_outputfile" :T OUTPUT-FILE :COL T :STM 1)"""if requestedOutputs['tsup_max_c_system'] else ""))
        connections.append(""" (("Tsup_max_c" |u|) "Int_Ref_Sensor_Target_{}_X_X_X" 0 0 NIL)""".format(added_sensor_info['tsup_max_c_system']))
    if requestedOutputs['tsup_max_c_kpi']:
        filedata.append("""((MODEL :N "Tsup_max_c_kpi" :T |SnapMinMax|)
 (:VAR :N |u_var| :IV #S(MS-SPARSE DEFAULT-VALUE 0.0 DIMENSION 1 VALUE NIL) :B #S(MS-SPARSE DEFAULT-VALUE NIL DIMENSION 1 VALUE ((1 -1 (|u| 1) 0))))
 (:VAR :N |uMax| :IV #S(MS-SPARSE DEFAULT-VALUE 0.0 DIMENSION 1 VALUE NIL) :L #S(MS-SPARSE DEFAULT-VALUE OFF DIMENSION 1 VALUE ((1 . "Tsup_max_c_kpi_outputfile"))) :AS #S(MS-SPARSE DEFAULT-VALUE NIL DIMENSION 1 VALUE ((1 . "Tsup_max_c_kpi")))))
(OUTPUT-FILE :N "Tsup_max_c_kpi_outputfile" :T OUTPUT-FILE :COL T :STM 1)\n""")
        connections.append(""" (("Tsup_max_c_kpi" (|u| 1)) ("Tsup_max_c" |y|) 0 0 NIL)""")
        
    #-------Tret
        #Tret mean c
    if requestedOutputs['tret_mean_c_kpi'] or requestedOutputs['tret_mean_c_system']:
        filedata.append("""((MODEL :N "Tret_mean_c" :T |Gain|){}){}\n""".format(
            """\n (:VAR :N |y_var| :L "Tret_mean_c_outputfile" :AS "Tret mean customers")""" if requestedOutputs['tret_mean_c_system'] else "",
            """\n(OUTPUT-FILE :N "Tret_mean_c_outputfile" :T OUTPUT-FILE :COL T :STM 1)"""if requestedOutputs['tret_mean_c_system'] else ""))
        connections.append(""" (("Tret_mean_c" |u|) "Int_Ref_Sensor_Target_{}_X_X_X" 0 0 NIL)""".format(added_sensor_info['tret_mean_c_system']))
    if requestedOutputs['tret_mean_c_kpi']:
        filedata.append("""((MODEL :N "Tret_mean_c_kpi" :T |SlidingAverage|)
 (:VAR :N |u_var| :IV #S(MS-SPARSE DEFAULT-VALUE 0.0 DIMENSION 1 VALUE NIL) :B #S(MS-SPARSE DEFAULT-VALUE NIL DIMENSION 1 VALUE ((1 -1 (|u| 1) 0))))
 (:VAR :N |uMean_var| :V 37.78 :L "Tret_mean_c_kpi_outputfile")
 (:PAR :N |interval| :V 1.0E12)
 (:PAR :N |n| :V 2))
(OUTPUT-FILE :N "Tret_mean_c_kpi_outputfile" :T OUTPUT-FILE :COL T :STM 1)\n""")
        connections.append(""" (("Tret_mean_c_kpi" (|u| 1)) ("Tret_mean_c" |y|) 0 0 NIL)""")
    #Tret min c
    if requestedOutputs['tret_min_c_kpi'] or requestedOutputs['tret_min_c_system']:
        filedata.append("""((MODEL :N "Tret_min_c" :T |Gain|){}){}\n""".format(
            """\n (:VAR :N |y_var| :L "Tret_min_c_outputfile" :AS "Tret min customers")""" if requestedOutputs['tret_min_c_system'] else "",
            """\n(OUTPUT-FILE :N "Tret_min_c_outputfile" :T OUTPUT-FILE :COL T :STM 1)"""if requestedOutputs['tret_min_c_system'] else ""))
        connections.append(""" (("Tret_min_c" |u|) "Int_Ref_Sensor_Target_{}_X_X_X" 0 0 NIL)""".format(added_sensor_info['tret_min_c_system']))
    if requestedOutputs['tret_min_c_kpi']:
        filedata.append("""((MODEL :N "Tret_min_c_kpi" :T |SnapMinMax|)
 (:VAR :N |u_var| :IV #S(MS-SPARSE DEFAULT-VALUE 0.0 DIMENSION 1 VALUE NIL) :B #S(MS-SPARSE DEFAULT-VALUE NIL DIMENSION 1 VALUE ((1 -1 (|u| 1) 0))))
 (:VAR :N |uMin| :IV #S(MS-SPARSE DEFAULT-VALUE 0.0 DIMENSION 1 VALUE NIL) :L #S(MS-SPARSE DEFAULT-VALUE OFF DIMENSION 1 VALUE ((1 . "Tret_min_c_kpi_outputfile"))) :AS #S(MS-SPARSE DEFAULT-VALUE NIL DIMENSION 1 VALUE ((1 . "Tret_min_c_kpi")))))
(OUTPUT-FILE :N "Tret_min_c_kpi_outputfile" :T OUTPUT-FILE :COL T :STM 1)\n""")
        connections.append(""" (("Tret_min_c_kpi" (|u| 1)) ("Tret_min_c" |y|) 0 0 NIL)""")
    #Tret max c
    if requestedOutputs['tret_max_c_kpi'] or requestedOutputs['tret_max_c_system']:
        filedata.append("""((MODEL :N "Tret_max_c" :T |Gain|){}){}\n""".format(
            """\n (:VAR :N |y_var| :L "Tret_max_c_outputfile" :AS "Tret max customers")""" if requestedOutputs['tret_max_c_system'] else "",
            """\n(OUTPUT-FILE :N "Tret_max_c_outputfile" :T OUTPUT-FILE :COL T :STM 1)"""if requestedOutputs['tret_max_c_system'] else ""))
        connections.append(""" (("Tret_max_c" |u|) "Int_Ref_Sensor_Target_{}_X_X_X" 0 0 NIL)""".format(added_sensor_info['tret_max_c_system']))
    if requestedOutputs['tret_max_c_kpi']:
        filedata.append("""((MODEL :N "Tret_max_c_kpi" :T |SnapMinMax|)
 (:VAR :N |u_var| :IV #S(MS-SPARSE DEFAULT-VALUE 0.0 DIMENSION 1 VALUE NIL) :B #S(MS-SPARSE DEFAULT-VALUE NIL DIMENSION 1 VALUE ((1 -1 (|u| 1) 0))))
 (:VAR :N |uMax| :IV #S(MS-SPARSE DEFAULT-VALUE 0.0 DIMENSION 1 VALUE NIL) :L #S(MS-SPARSE DEFAULT-VALUE OFF DIMENSION 1 VALUE ((1 . "Tret_max_c_kpi_outputfile"))) :AS #S(MS-SPARSE DEFAULT-VALUE NIL DIMENSION 1 VALUE ((1 . "Tret_max_c_kpi")))))
(OUTPUT-FILE :N "Tret_max_c_kpi_outputfile" :T OUTPUT-FILE :COL T :STM 1)\n""")
        connections.append(""" (("Tret_max_c_kpi" (|u| 1)) ("Tret_max_c" |y|) 0 0 NIL)""")
    #qsup c
    try:    
        sensor_id=added_sensor_info['qsup_c']
        filedata.append("""((MODEL :N "Qsup_c" :T |Gain|))
(:EO :N "Qsup_c_sepsign" :T SEPSIGN)\n""")
        connections.append(""" (("Qsup_c" |u|) "Int_Ref_Sensor_Target_{}_X_X_X" 0 0 NIL)
 (("Qsup_c_sepsign" INSIGNALLINK) ("Qsup_c" |y|) 0 0 NIL)""".format(sensor_id))  
        
        if requestedOutputs['qsup_heat_c_kpi'] or requestedOutputs['qsup_heat_spec_c_kpi'] or requestedOutputs['qsup_heat_density_c_kpi'] or requestedOutputs['qsup_heat_linedensity_c_kpi']:
            filedata.append("""((:CEO :N "Qsup_c_pos" :T EMETER)
 (:PAR :N N_IN :V 1)
 (:PAR :N MULT :DIM (1))
 (:VAR :N TOTENERGY :L "Qsup_heat_c_kpi_outputfile" :AS "Qsup_heat_c")
 (:VAR :N INPOWER :DIM (1) :IV #S(MS-SPARSE DEFAULT-VALUE 0.0 DIMENSION 1 VALUE NIL) :B #S(MS-SPARSE DEFAULT-VALUE NIL DIMENSION 1 VALUE ((1 -1 (INCONSUMLINK 1) 0)))))\n""")
            filedata.append("""(OUTPUT-FILE :N "Qsup_heat_c_kpi_outputfile" :T OUTPUT-FILE :COL T :STM 1)\n""")
            connections.append(""" (("Qsup_c_pos" (INCONSUMLINK 1)) ("Qsup_c_sepsign" POSSIGNALLINK) 0 0 NIL)""")
        if requestedOutputs['qsup_cold_c_kpi'] or requestedOutputs['qsup_cold_spec_c_kpi'] or requestedOutputs['qsup_cold_density_c_kpi'] or requestedOutputs['qsup_cold_linedensity_c_kpi']:
            filedata.append("""((:CEO :N "Qsup_c_neg" :T EMETER)
 (:PAR :N N_IN :V 1)
 (:PAR :N MULT :DIM (1))
 (:VAR :N TOTENERGY :L "Qsup_cold_c_kpi_outputfile" :AS "Qsup_cold_c")
 (:VAR :N INPOWER :DIM (1) :IV #S(MS-SPARSE DEFAULT-VALUE 0.0 DIMENSION 1 VALUE NIL) :B #S(MS-SPARSE DEFAULT-VALUE NIL DIMENSION 1 VALUE ((1 -1 (INCONSUMLINK 1) 0)))))\n""")
            connections.append(""" (("Qsup_c_neg" (INCONSUMLINK 1)) ("Qsup_c_sepsign" NEGSIGNALLINK) 0 0 NIL)""")
            filedata.append("""(OUTPUT-FILE :N "Qsup_cold_c_kpi_outputfile" :T OUTPUT-FILE :COL T :STM 1)\n""")
        if requestedOutputs['qsup_c_kpi'] or requestedOutputs['qsup_spec_c_kpi'] or requestedOutputs['qsup_density_c_kpi'] or requestedOutputs['qsup_linedensity_c_kpi']:
            filedata.append("""((:EO :N "Qsup_c_sum" :T ADDER)
 (:PAR :N (COEFF 2) :V -1.0)
 (:VAR :N OUTSIGNAL :L "Qsup_c_kpi_outputfile" :AS "Qsup_c")
 (:VAR :N INSIGNAL :IV #S(MS-SPARSE DEFAULT-VALUE 0.0 DIMENSION 1 VALUE NIL) :B #S(MS-SPARSE DEFAULT-VALUE NIL DIMENSION 1 VALUE ((1 :MACRO "Qsup_c_pos" TOTENERGY) (2 :MACRO "Qsup_c_neg" TOTENERGY)))))\n""")
            filedata.append("""(OUTPUT-FILE :N "Qsup_c_kpi_outputfile" :T OUTPUT-FILE :COL T :STM 1)\n""")
    except:
        pass
        
    #----------energy plants----------
    #-------Tsup
    #Tsup mean ep
    if requestedOutputs['tsup_mean_ep_kpi'] or requestedOutputs['tsup_mean_ep_system']:
        filedata.append("""((MODEL :N "Tsup_mean_ep" :T |Gain|){}){}\n""".format(
            """\n (:VAR :N |y_var| :L "Tsup_mean_ep_outputfile" :AS "Tsup mean energy plants")""" if requestedOutputs['tsup_mean_ep_system'] else "",
            """\n(OUTPUT-FILE :N "Tsup_mean_ep_outputfile" :T OUTPUT-FILE :COL T :STM 1)"""if requestedOutputs['tsup_mean_ep_system'] else ""))
        connections.append(""" (("Tsup_mean_ep" |u|) "Int_Ref_Sensor_Target_{}_X_X_X" 0 0 NIL)""".format(added_sensor_info['tsup_mean_ep_system']))
    if requestedOutputs['tsup_mean_ep_kpi']:
        filedata.append("""((MODEL :N "Tsup_mean_ep_kpi" :T |SlidingAverage|)
 (:VAR :N |u_var| :IV #S(MS-SPARSE DEFAULT-VALUE 0.0 DIMENSION 1 VALUE NIL) :B #S(MS-SPARSE DEFAULT-VALUE NIL DIMENSION 1 VALUE ((1 -1 (|u| 1) 0))))
 (:VAR :N |uMean_var| :V 37.78 :L "Tsup_mean_ep_kpi_outputfile")
 (:PAR :N |interval| :V 1.0E12)
 (:PAR :N |n| :V 2))
(OUTPUT-FILE :N "Tsup_mean_ep_kpi_outputfile" :T OUTPUT-FILE :COL T :STM 1)\n""")
        connections.append(""" (("Tsup_mean_ep_kpi" (|u| 1)) ("Tsup_mean_ep" |y|) 0 0 NIL)""")
    #Tsup min c
    if requestedOutputs['tsup_min_ep_kpi'] or requestedOutputs['tsup_min_ep_system']:
        filedata.append("""((MODEL :N "Tsup_min_ep" :T |Gain|){}){}\n""".format(
            """\n (:VAR :N |y_var| :L "Tsup_min_ep_outputfile" :AS "Tsup min energy plants")""" if requestedOutputs['tsup_min_ep_system'] else "",
            """\n(OUTPUT-FILE :N "Tsup_min_ep_outputfile" :T OUTPUT-FILE :COL T :STM 1)"""if requestedOutputs['tsup_min_ep_system'] else ""))
        connections.append(""" (("Tsup_min_ep" |u|) "Int_Ref_Sensor_Target_{}_X_X_X" 0 0 NIL)""".format(added_sensor_info['tsup_min_ep_system']))
    if requestedOutputs['tsup_min_ep_kpi']:
        filedata.append("""((MODEL :N "Tsup_min_ep_kpi" :T |SnapMinMax|)
 (:VAR :N |u_var| :IV #S(MS-SPARSE DEFAULT-VALUE 0.0 DIMENSION 1 VALUE NIL) :B #S(MS-SPARSE DEFAULT-VALUE NIL DIMENSION 1 VALUE ((1 -1 (|u| 1) 0))))
 (:VAR :N |uMin| :IV #S(MS-SPARSE DEFAULT-VALUE 0.0 DIMENSION 1 VALUE NIL) :L #S(MS-SPARSE DEFAULT-VALUE OFF DIMENSION 1 VALUE ((1 . "Tsup_min_ep_kpi_outputfile"))) :AS #S(MS-SPARSE DEFAULT-VALUE NIL DIMENSION 1 VALUE ((1 . "Tsup_min_ep_kpi")))))
(OUTPUT-FILE :N "Tsup_min_ep_kpi_outputfile" :T OUTPUT-FILE :COL T :STM 1)\n""")
        connections.append(""" (("Tsup_min_ep_kpi" (|u| 1)) ("Tsup_min_ep" |y|) 0 0 NIL)""")
    #Tsup max c
    if requestedOutputs['tsup_max_ep_kpi'] or requestedOutputs['tsup_max_ep_system']:
        filedata.append("""((MODEL :N "Tsup_max_ep" :T |Gain|){}){}\n""".format(
            """\n (:VAR :N |y_var| :L "Tsup_max_ep_outputfile" :AS "Tsup max energy plants")""" if requestedOutputs['tsup_max_ep_system'] else "",
            """\n(OUTPUT-FILE :N "Tsup_max_ep_outputfile" :T OUTPUT-FILE :COL T :STM 1)"""if requestedOutputs['tsup_max_ep_system'] else ""))
        connections.append(""" (("Tsup_max_ep" |u|) "Int_Ref_Sensor_Target_{}_X_X_X" 0 0 NIL)""".format(added_sensor_info['tsup_max_ep_system']))
    if requestedOutputs['tsup_max_ep_kpi']:
        filedata.append("""((MODEL :N "Tsup_max_ep_kpi" :T |SnapMinMax|)
 (:VAR :N |u_var| :IV #S(MS-SPARSE DEFAULT-VALUE 0.0 DIMENSION 1 VALUE NIL) :B #S(MS-SPARSE DEFAULT-VALUE NIL DIMENSION 1 VALUE ((1 -1 (|u| 1) 0))))
 (:VAR :N |uMax| :IV #S(MS-SPARSE DEFAULT-VALUE 0.0 DIMENSION 1 VALUE NIL) :L #S(MS-SPARSE DEFAULT-VALUE OFF DIMENSION 1 VALUE ((1 . "Tsup_max_ep_kpi_outputfile"))) :AS #S(MS-SPARSE DEFAULT-VALUE NIL DIMENSION 1 VALUE ((1 . "Tsup_max_ep_kpi")))))
(OUTPUT-FILE :N "Tsup_max_ep_kpi_outputfile" :T OUTPUT-FILE :COL T :STM 1)\n""")
        connections.append(""" (("Tsup_max_ep_kpi" (|u| 1)) ("Tsup_max_ep" |y|) 0 0 NIL)""")
        
    #-------Tret
    #Tret mean ep
    if requestedOutputs['tret_mean_ep_kpi'] or requestedOutputs['tret_mean_ep_system']:
        filedata.append("""((MODEL :N "Tret_mean_ep" :T |Gain|){}){}\n""".format(
            """\n (:VAR :N |y_var| :L "Tret_mean_ep_outputfile" :AS "Tret mean energy plants")""" if requestedOutputs['tret_mean_ep_system'] else "",
            """\n(OUTPUT-FILE :N "Tret_mean_ep_outputfile" :T OUTPUT-FILE :COL T :STM 1)"""if requestedOutputs['tret_mean_ep_system'] else ""))
        connections.append(""" (("Tret_mean_ep" |u|) "Int_Ref_Sensor_Target_{}_X_X_X" 0 0 NIL)""".format(added_sensor_info['tret_mean_ep_system']))
    if requestedOutputs['tret_mean_ep_kpi']:
        filedata.append("""((MODEL :N "Tret_mean_ep_kpi" :T |SlidingAverage|)
 (:VAR :N |u_var| :IV #S(MS-SPARSE DEFAULT-VALUE 0.0 DIMENSION 1 VALUE NIL) :B #S(MS-SPARSE DEFAULT-VALUE NIL DIMENSION 1 VALUE ((1 -1 (|u| 1) 0))))
 (:VAR :N |uMean_var| :V 37.78 :L "Tret_mean_ep_kpi_outputfile")
 (:PAR :N |interval| :V 1.0E12)
 (:PAR :N |n| :V 2))
(OUTPUT-FILE :N "Tret_mean_ep_kpi_outputfile" :T OUTPUT-FILE :COL T :STM 1)\n""")
        connections.append(""" (("Tret_mean_ep_kpi" (|u| 1)) ("Tret_mean_ep" |y|) 0 0 NIL)""")
    #Tret min c
    if requestedOutputs['tret_min_ep_kpi'] or requestedOutputs['tret_min_ep_system']:
        filedata.append("""((MODEL :N "Tret_min_ep" :T |Gain|){}){}\n""".format(
            """\n (:VAR :N |y_var| :L "Tret_min_ep_outputfile" :AS "Tret min energy plants")""" if requestedOutputs['tret_min_ep_system'] else "",
            """\n(OUTPUT-FILE :N "Tret_min_ep_outputfile" :T OUTPUT-FILE :COL T :STM 1)"""if requestedOutputs['tret_min_ep_system'] else ""))
        connections.append(""" (("Tret_min_ep" |u|) "Int_Ref_Sensor_Target_{}_X_X_X" 0 0 NIL)""".format(added_sensor_info['tret_min_ep_system']))
    if requestedOutputs['tret_min_ep_kpi']:
        filedata.append("""((MODEL :N "Tret_min_ep_kpi" :T |SnapMinMax|)
 (:VAR :N |u_var| :IV #S(MS-SPARSE DEFAULT-VALUE 0.0 DIMENSION 1 VALUE NIL) :B #S(MS-SPARSE DEFAULT-VALUE NIL DIMENSION 1 VALUE ((1 -1 (|u| 1) 0))))
 (:VAR :N |uMin| :IV #S(MS-SPARSE DEFAULT-VALUE 0.0 DIMENSION 1 VALUE NIL) :L #S(MS-SPARSE DEFAULT-VALUE OFF DIMENSION 1 VALUE ((1 . "Tret_min_ep_kpi_outputfile"))) :AS #S(MS-SPARSE DEFAULT-VALUE NIL DIMENSION 1 VALUE ((1 . "Tret_min_ep_kpi")))))
(OUTPUT-FILE :N "Tret_min_ep_kpi_outputfile" :T OUTPUT-FILE :COL T :STM 1)\n""")
        connections.append(""" (("Tret_min_ep_kpi" (|u| 1)) ("Tret_min_ep" |y|) 0 0 NIL)""")
    #Tret max c
    if requestedOutputs['tret_max_ep_kpi'] or requestedOutputs['tret_max_ep_system']:
        filedata.append("""((MODEL :N "Tret_max_ep" :T |Gain|){}){}\n""".format(
            """\n (:VAR :N |y_var| :L "Tret_max_ep_outputfile" :AS "Tret max energy plants")""" if requestedOutputs['tret_max_ep_system'] else "",
            """\n(OUTPUT-FILE :N "Tret_max_ep_outputfile" :T OUTPUT-FILE :COL T :STM 1)"""if requestedOutputs['tret_max_ep_system'] else ""))
        connections.append(""" (("Tret_max_ep" |u|) "Int_Ref_Sensor_Target_{}_X_X_X" 0 0 NIL)""".format(added_sensor_info['tret_max_ep_system']))
    if requestedOutputs['tret_max_ep_kpi']:
        filedata.append("""((MODEL :N "Tret_max_ep_kpi" :T |SnapMinMax|)
 (:VAR :N |u_var| :IV #S(MS-SPARSE DEFAULT-VALUE 0.0 DIMENSION 1 VALUE NIL) :B #S(MS-SPARSE DEFAULT-VALUE NIL DIMENSION 1 VALUE ((1 -1 (|u| 1) 0))))
 (:VAR :N |uMax| :IV #S(MS-SPARSE DEFAULT-VALUE 0.0 DIMENSION 1 VALUE NIL) :L #S(MS-SPARSE DEFAULT-VALUE OFF DIMENSION 1 VALUE ((1 . "Tret_max_ep_kpi_outputfile"))) :AS #S(MS-SPARSE DEFAULT-VALUE NIL DIMENSION 1 VALUE ((1 . "Tret_max_ep_kpi")))))
(OUTPUT-FILE :N "Tret_max_ep_kpi_outputfile" :T OUTPUT-FILE :COL T :STM 1)\n""")
        connections.append(""" (("Tret_max_ep_kpi" (|u| 1)) ("Tret_max_ep" |y|) 0 0 NIL)""")
    #qsup ep
    try:    
        sensor_id=added_sensor_info['qsup_ep']
        filedata.append("""((MODEL :N "Qsup_ep" :T |Gain|))
(:EO :N "Qsup_ep_sepsign" :T SEPSIGN)\n""")
        connections.append(""" (("Qsup_ep" |u|) "Int_Ref_Sensor_Target_{}_X_X_X" 0 0 NIL)
 (("Qsup_ep_sepsign" INSIGNALLINK) ("Qsup_ep" |y|) 0 0 NIL)""".format(sensor_id))  
        
        if requestedOutputs['qsup_heat_ep_kpi']:
            filedata.append("""((:CEO :N "Qsup_ep_pos" :T EMETER)
 (:PAR :N N_IN :V 1)
 (:PAR :N MULT :DIM (1))
 (:VAR :N TOTENERGY :L "Qsup_heat_ep_kpi_outputfile" :AS "Qsup_heat_ep")
 (:VAR :N INPOWER :DIM (1) :IV #S(MS-SPARSE DEFAULT-VALUE 0.0 DIMENSION 1 VALUE NIL) :B #S(MS-SPARSE DEFAULT-VALUE NIL DIMENSION 1 VALUE ((1 -1 (INCONSUMLINK 1) 0)))))\n""")
            filedata.append("""(OUTPUT-FILE :N "Qsup_heat_ep_kpi_outputfile" :T OUTPUT-FILE :COL T :STM 1)\n""")
            connections.append(""" (("Qsup_ep_pos" (INCONSUMLINK 1)) ("Qsup_ep_sepsign" POSSIGNALLINK) 0 0 NIL)""")
        if requestedOutputs['qsup_cold_ep_kpi']:
            filedata.append("""((:CEO :N "Qsup_ep_neg" :T EMETER)
 (:PAR :N N_IN :V 1)
 (:PAR :N MULT :DIM (1))
 (:VAR :N TOTENERGY :L "Qsup_cold_ep_kpi_outputfile" :AS "Qsup_cold_ep")
 (:VAR :N INPOWER :DIM (1) :IV #S(MS-SPARSE DEFAULT-VALUE 0.0 DIMENSION 1 VALUE NIL) :B #S(MS-SPARSE DEFAULT-VALUE NIL DIMENSION 1 VALUE ((1 -1 (INCONSUMLINK 1) 0)))))\n""")
            connections.append(""" (("Qsup_ep_neg" (INCONSUMLINK 1)) ("Qsup_ep_sepsign" NEGSIGNALLINK) 0 0 NIL)""")
            filedata.append("""(OUTPUT-FILE :N "Qsup_cold_ep_kpi_outputfile" :T OUTPUT-FILE :COL T :STM 1)\n""")
        if requestedOutputs['qsup_ep_kpi']:
            filedata.append("""((:EO :N "Qsup_ep_sum" :T ADDER)
 (:PAR :N (COEFF 2) :V -1.0)
 (:VAR :N OUTSIGNAL :L "Qsup_ep_kpi_outputfile" :AS "Qsup_ep")
 (:VAR :N INSIGNAL :IV #S(MS-SPARSE DEFAULT-VALUE 0.0 DIMENSION 1 VALUE NIL) :B #S(MS-SPARSE DEFAULT-VALUE NIL DIMENSION 1 VALUE ((1 :MACRO "Qsup_ep_pos" TOTENERGY) (2 :MACRO "Qsup_ep_neg" TOTENERGY)))))\n""")
            filedata.append("""(OUTPUT-FILE :N "Qsup_ep_kpi_outputfile" :T OUTPUT-FILE :COL T :STM 1)\n""")
    except:
        pass

    #qamb
    if requestedOutputs['heatbalance_system'] or requestedOutputs['qamb_kpi']:
        line_conns=["""({} :SYSTEM "Pipebundle_{}" |QAmbtotal|)""".format(counter,lid) for counter,lid in enumerate(getLineIds(cur,config),1)]
        n_lines=len(line_conns)
        filedata.append("""((:EO :N "qamb" :T ADDER)
 (:PAR :N N_IN :V {})
 (:PAR :N COEFF :DIM ({}) :V #({}))
 (:VAR :N OUTSIGNAL :L "heatbalance_outputfile" :AS "Qamb")
 (:VAR :N INSIGNAL :IV #S(MS-SPARSE DEFAULT-VALUE 0.0 DIMENSION 1 VALUE NIL) :B #S(MS-SPARSE DEFAULT-VALUE NIL DIMENSION 1 VALUE ({}))))\n""".format(n_lines,n_lines,' '.join(['-1' for i in line_conns]),''.join(line_conns)))
        if requestedOutputs['qamb_kpi']:
            filedata.append("""((:CEO :N "Qamb_emeter" :T EMETER)
 (:PAR :N N_IN :V 1)
 (:PAR :N MULT :DIM (1))
 (:VAR :N TOTENERGY :L "Qamb_kpi_outputfile" :AS "Qamb total")
 (:VAR :N INPOWER :DIM (1) :IV #S(MS-SPARSE DEFAULT-VALUE 0.0 DIMENSION 1 VALUE NIL) :B #S(MS-SPARSE DEFAULT-VALUE NIL DIMENSION 1 VALUE ((1 -1 (INCONSUMLINK 1) 0)))))\n""")
            filedata.append("""(OUTPUT-FILE :N "Qamb_kpi_outputfile" :T OUTPUT-FILE :COL T :STM 1)\n""")
            connections.append(""" (("Qamb_emeter" (INCONSUMLINK 1)) ("qamb" OUTSIGNALLINK) 0 0 NIL)""")

    #----------system-----------
    #heat balance
    if requestedOutputs['heatbalance_system']:
        filedata.append("""(OUTPUT-FILE :N "heatbalance_outputfile" :T OUTPUT-FILE :COL T :STM 1)\n""")
        for i in added_sensor_info['heatbalance_system']:
            name= 'hb_'+('customer' if i['type']==1 else 'energy_plant')+'_' + i['template_name']
            filedata.append("""((MODEL :N "{}" :T |Gain|)
 (:PAR :N |k| :V -1)
 (:VAR :N |y_var| :L "heatbalance_outputfile" :AS "{}"))\n""".format(name,i['template_name']))
            connections.append(""" (("{}" |u|) "Int_Ref_Sensor_Target_{}_X_X_X" 0 0 NIL)""".format(name,i['id']))
    #mass balance
    if requestedOutputs['massbalance_system']:
        filedata.append("""(OUTPUT-FILE :N "massbalance_outputfile" :T OUTPUT-FILE :COL T :STM 1)\n""")
        for i in added_sensor_info['massbalance_system']:
            #print(i)
            name= 'mdotb_'+('customer' if i['type']==1 else 'energy_plant')+'_' + i['template_name']
            filedata.append("""((MODEL :N "{}" :T |Gain|)
 (:VAR :N |y_var| :L "massbalance_outputfile" :AS "{}"))\n""".format(name,i['template_name']))
            connections.append(""" (("{}" |u|) "Int_Ref_Sensor_Target_{}_X_X_X" 0 0 NIL)""".format(name,i['id']))

    if connections:
        filedata.append("(CONNECTIONS\n{})".format('\n'.join(connections)))
    writeToFileFromList(filedata,dir,dir+'\\Results-macro.idm') 
                
def writeMacroResultsIdc(config,cur,dir,requestedOutputs,sensor_dec_data,added_sensor_info):
        
    filedata=[""";IDA {} Data UTF-8
(DOCUMENT-HEADER :TYPE SCHEMA :PAGE-WIDTH 250 :PAGE-HEIGHT 123.2) 
(SELF-FRAME :AT ((482 238)) :R (472 224) :SLOT (:SELF) :DATA MACRO-OBJECT) 
(TEXT-OBJECT :VALUE "Results" :AT ((675 225) (736 239)) :STYLE LABEL) 
(LIST-FIELD :AT ((675 248) (933 449)) :SLOT (:RESULTS) :TEXT-COLOR #S(RGB RED 0 GREEN 0 BLUE 0)) 
(TEXT-OBJECT :VALUE (ENGLISH "Customers") :AT ((30 25) (101 46)) :STYLE NOTE)
(TEXT-OBJECT :VALUE (ENGLISH "Energy plants") :AT ((30 117) (101 138)) :STYLE NOTE) 
(TEXT-OBJECT :VALUE (ENGLISH "System") :AT ((30 209) (101 230)) :STYLE NOTE) """.format(getIDAVersion(config))]

    #----------customers-----------
    x_coord=46
    dx_coord=120
    #Tsup mean c
    if requestedOutputs['tsup_mean_c_kpi'] or requestedOutputs['tsup_mean_c_system']:
        filedata.append("""\n(EQUATION-FRAME :AT (({} 75)) :R (18 18) :ICON "lib:gain.ids" :SLOT ("Tsup_mean_c") :NAME "Tsup_mean_c" :DATA MODEL) """.format(x_coord))
        filedata.append("""\n(CONNECTION-LINE :AT ((10 40) ({} 40) ({} 75) ({} 75)) :FIRST-LINK (:SELF (0.0 0.074) "Int_Ref_Sensor_Target_{}_X_X_X") :LAST-LINK ("Tsup_mean_c" (0 0.5) |u|) :DIR :RIGHT :ARROW (19 8 8)) """.format(x_coord-31,x_coord-31,x_coord-21.5,added_sensor_info['tsup_mean_c_system']))
        x_coord+=dx_coord
    #Tsup mean c kpi
    if requestedOutputs['tsup_mean_c_kpi']:
        filedata.append("""\n(EQUATION-FRAME :AT (({} 75)) :R (16 16) :ICON "lib:slidingaverage.ids" :SLOT ("Tsup_mean_c_kpi") :NAME "Tsup_mean_c_kpi" :DATA MODEL) """.format(x_coord-67))
        filedata.append("""\n(CONNECTION-LINE :AT (({} 75) ({} 75)) :FIRST-LINK ("Tsup_mean_c" (1 0.5) |y|) :LAST-LINK ("Tsup_mean_c_kpi" (0 0.5) (|u| 1)) :DIR :RIGHT :ARROW (19 8 8)) """.format(x_coord-100,x_coord-86))
    #Tsup min c
    if requestedOutputs['tsup_min_c_kpi'] or requestedOutputs['tsup_min_c_system']:
        filedata.append("""\n(EQUATION-FRAME :AT (({} 75)) :R (18 18) :ICON "lib:gain.ids" :SLOT ("min") :NAME "Tsup_min_c" :DATA MODEL) """.format(x_coord))
        filedata.append("""\n(CONNECTION-LINE :AT ((10 40) ({} 40) ({} 75) ({} 75)) :FIRST-LINK (:SELF (0.0 0.074) "Int_Ref_Sensor_Target_{}_X_X_X") :LAST-LINK ("Tsup_min_c" (0 0.5) |u|) :DIR :RIGHT :ARROW (19 8 8)) """.format(x_coord-31,x_coord-31,x_coord-21.5,added_sensor_info['tsup_min_c_system']))
        x_coord+=dx_coord
    #Tsup min c kpi
    if requestedOutputs['tsup_min_c_kpi']:
        filedata.append("""\n(EQUATION-FRAME :AT (({} 75)) :R (16 16) :ICON "lib:snapminmax.ids" :SLOT ("Tsup_min_c_kpi") :NAME "Tsup_min_c_kpi" :DATA MODEL) """.format(x_coord-67))
        filedata.append("""\n(CONNECTION-LINE :AT (({} 75) ({} 75)) :FIRST-LINK ("Tsup_min_c" (1 0.5) |y|) :LAST-LINK ("Tsup_min_c_kpi" (0 0.5) (|u| 1)) :DIR :RIGHT :ARROW (19 8 8)) """.format(x_coord-100,x_coord-86))
    #Tsup max c
    if requestedOutputs['tsup_max_c_kpi'] or requestedOutputs['tsup_max_c_system']:
        filedata.append("""\n(EQUATION-FRAME :AT (({} 75)) :R (18 18) :ICON "lib:gain.ids" :SLOT ("min") :NAME "Tsup_max_c" :DATA MODEL) """.format(x_coord))
        filedata.append("""\n(CONNECTION-LINE :AT ((10 40) ({} 40) ({} 75) ({} 75)) :FIRST-LINK (:SELF (0.0 0.074) "Int_Ref_Sensor_Target_{}_X_X_X") :LAST-LINK ("Tsup_max_c" (0 0.5) |u|) :DIR :RIGHT :ARROW (19 8 8)) """.format(x_coord-31,x_coord-31,x_coord-21.5,added_sensor_info['tsup_max_c_system']))
        x_coord+=dx_coord
    #Tsup max c kpi
    if requestedOutputs['tsup_max_c_kpi']:
        filedata.append("""\n(EQUATION-FRAME :AT (({} 75)) :R (16 16) :ICON "lib:snapminmax.ids" :SLOT ("Tsup_max_c_kpi") :NAME "Tsup_max_c_kpi" :DATA MODEL) """.format(x_coord-67))
        filedata.append("""\n(CONNECTION-LINE :AT (({} 75) ({} 75)) :FIRST-LINK ("Tsup_max_c" (1 0.5) |y|) :LAST-LINK ("Tsup_max_c_kpi" (0 0.5) (|u| 1)) :DIR :RIGHT :ARROW (19 8 8)) """.format(x_coord-100,x_coord-86))
    #Tret mean c
    if requestedOutputs['tret_mean_c_kpi'] or requestedOutputs['tret_mean_c_system']:
        filedata.append("""\n(EQUATION-FRAME :AT (({} 75)) :R (18 18) :ICON "lib:gain.ids" :SLOT ("Tret_mean_c") :NAME "Tret_mean_c" :DATA MODEL) """.format(x_coord))
        filedata.append("""\n(CONNECTION-LINE :AT ((10 40) ({} 40) ({} 75) ({} 75)) :FIRST-LINK (:SELF (0.0 0.074) "Int_Ref_Sensor_Target_{}_X_X_X") :LAST-LINK ("Tret_mean_c" (0 0.5) |u|) :DIR :RIGHT :ARROW (19 8 8)) """.format(x_coord-31,x_coord-31,x_coord-21.5,added_sensor_info['tret_mean_c_system']))
        x_coord+=dx_coord
    #Tret mean c kpi
    if requestedOutputs['tret_mean_c_kpi']:
        filedata.append("""\n(EQUATION-FRAME :AT (({} 75)) :R (16 16) :ICON "lib:slidingaverage.ids" :SLOT ("Tret_mean_c_kpi") :NAME "Tret_mean_c_kpi" :DATA MODEL) """.format(x_coord-67))
        filedata.append("""\n(CONNECTION-LINE :AT (({} 75) ({} 75)) :FIRST-LINK ("Tret_mean_c" (1 0.5) |y|) :LAST-LINK ("Tret_mean_c_kpi" (0 0.5) (|u| 1)) :DIR :RIGHT :ARROW (19 8 8)) """.format(x_coord-100,x_coord-86))
    #Tret min c
    if requestedOutputs['tret_min_c_kpi'] or requestedOutputs['tret_min_c_system']:
        filedata.append("""\n(EQUATION-FRAME :AT (({} 75)) :R (18 18) :ICON "lib:gain.ids" :SLOT ("min") :NAME "Tret_min_c" :DATA MODEL) """.format(x_coord))
        filedata.append("""\n(CONNECTION-LINE :AT ((10 40) ({} 40) ({} 75) ({} 75)) :FIRST-LINK (:SELF (0.0 0.074) "Int_Ref_Sensor_Target_{}_X_X_X") :LAST-LINK ("Tret_min_c" (0 0.5) |u|) :DIR :RIGHT :ARROW (19 8 8)) """.format(x_coord-31,x_coord-31,x_coord-21.5,added_sensor_info['tret_min_c_system']))
        x_coord+=dx_coord
    #Tret min c kpi
    if requestedOutputs['tret_min_c_kpi']:
        filedata.append("""\n(EQUATION-FRAME :AT (({} 75)) :R (16 16) :ICON "lib:snapminmax.ids" :SLOT ("Tret_min_c_kpi") :NAME "Tret_min_c_kpi" :DATA MODEL) """.format(x_coord-67))
        filedata.append("""\n(CONNECTION-LINE :AT (({} 75) ({} 75)) :FIRST-LINK ("Tret_min_c" (1 0.5) |y|) :LAST-LINK ("Tret_min_c_kpi" (0 0.5) (|u| 1)) :DIR :RIGHT :ARROW (19 8 8)) """.format(x_coord-100,x_coord-86))
    #Tret max c
    if requestedOutputs['tret_max_c_kpi'] or requestedOutputs['tret_max_c_system']:
        filedata.append("""\n(EQUATION-FRAME :AT (({} 75)) :R (18 18) :ICON "lib:gain.ids" :SLOT ("min") :NAME "Tret_max_c" :DATA MODEL) """.format(x_coord))
        filedata.append("""\n(CONNECTION-LINE :AT ((10 40) ({} 40) ({} 75) ({} 75)) :FIRST-LINK (:SELF (0.0 0.074) "Int_Ref_Sensor_Target_{}_X_X_X") :LAST-LINK ("Tret_max_c" (0 0.5) |u|) :DIR :RIGHT :ARROW (19 8 8)) """.format(x_coord-31,x_coord-31,x_coord-21.5,added_sensor_info['tret_max_c_system']))
        x_coord+=dx_coord
    #Tret max c kpi
    if requestedOutputs['tret_max_c_kpi']:
        filedata.append("""\n(EQUATION-FRAME :AT (({} 75)) :R (16 16) :ICON "lib:snapminmax.ids" :SLOT ("Tret_max_c_kpi") :NAME "Tret_max_c_kpi" :DATA MODEL) """.format(x_coord-67))
        filedata.append("""\n(CONNECTION-LINE :AT (({} 75) ({} 75)) :FIRST-LINK ("Tret_max_c" (1 0.5) |y|) :LAST-LINK ("Tret_max_c_kpi" (0 0.5) (|u| 1)) :DIR :RIGHT :ARROW (19 8 8)) """.format(x_coord-100,x_coord-86))
    #Qsup c
    try:  
        sensor_id=added_sensor_info['qsup_c']
        filedata.append("""\n(EQUATION-FRAME :AT (({} 75)) :R (18 18) :ICON "lib:gain.ids" :SLOT ("min") :NAME "Qsup_c" :DATA MODEL) """.format(x_coord))
        filedata.append("""\n(CONNECTION-LINE :AT ((10 40) ({} 40) ({} 75) ({} 75)) :FIRST-LINK (:SELF (0.0 0.074) "Int_Ref_Sensor_Target_{}_X_X_X") :LAST-LINK ("Qsup_c" (0 0.5) |u|) :DIR :RIGHT :ARROW (19 8 8)) """.format(x_coord-31,x_coord-31,x_coord-21.5,sensor_id))
        x_coord+=dx_coord
        filedata.append("""\n(EQUATION-FRAME :AT (({} 75)) :R (16 16) :ICON "lib:sepsign.ids" :SLOT ("Qsup_c_sepsign") :NAME "Qsup_c_sepsign" :DATA MODEL) """.format(x_coord-67))
        filedata.append("""\n(CONNECTION-LINE :AT (({} 75) ({} 75)) :FIRST-LINK ("Qsup_c" (1 0.5) |y|) :LAST-LINK ("Qsup_c_sepsign" (0 0.5) INSIGNALLINK) :DIR :RIGHT :ARROW (19 8 8)) """.format(x_coord-100,x_coord-86))
        if requestedOutputs['qsup_heat_c_kpi'] or requestedOutputs['qsup_heat_spec_c_kpi'] or requestedOutputs['qsup_heat_density_c_kpi'] or requestedOutputs['qsup_heat_linedensity_c_kpi']:
            filedata.append("""\n(EQUATION-FRAME :AT (({} 57)) :R (14 16) :ICON "lib:emeter.ids" :SLOT ("Qsup_c_pos") :NAME "Qsup_c_pos" :PADDING 3 :DATA :CEO :D (:DICT (ICE DESCRIPTIONS EMETER))) """.format(x_coord-21))
            filedata.append("""\n(CONNECTION-LINE :AT (({} 66) ({} 66) ({} 58) ({} 58)) :FIRST-LINK ("Qsup_c_sepsign" (1.0 0.219) POSSIGNALLINK) :LAST-LINK ("Qsup_c_pos" (0.0 0.531) (INCONSUMLINK 1)) :DIR :RIGHT :ARROW (19 8 8)) """.format(x_coord-50,x_coord-44,x_coord-44,x_coord-35))
        if requestedOutputs['qsup_cold_c_kpi'] or requestedOutputs['qsup_cold_spec_c_kpi'] or requestedOutputs['qsup_cold_density_c_kpi'] or requestedOutputs['qsup_cold_linedensity_c_kpi']:
            filedata.append("""\n(EQUATION-FRAME :AT (({} 95)) :R (14 16) :ICON "lib:emeter.ids" :SLOT ("Qsup_c_neg") :NAME "Qsup_c_neg" :PADDING 3 :DATA :CEO :D (:DICT (ICE DESCRIPTIONS EMETER))) """.format(x_coord-19))
            filedata.append("""\n(CONNECTION-LINE :AT (({} 84) ({} 84) ({} 96) ({} 96)) :FIRST-LINK ("Qsup_c_sepsign" (1 0.781) NEGSIGNALLINK) :LAST-LINK ("Qsup_c_neg" (0.0 0.531) (INCONSUMLINK 1)) :DIR :RIGHT :ARROW (19 8 8)) """.format(x_coord-50,x_coord-44,x_coord-44,x_coord-33))
        if requestedOutputs['qsup_c_kpi'] or requestedOutputs['qsup_spec_c_kpi'] or requestedOutputs['qsup_density_c_kpi'] or requestedOutputs['qsup_linedensity_c_kpi']:
            filedata.append("""\n(EQUATION-FRAME :AT (({} 75)) :R (16 16) :ICON "lib:adder.ids" :SLOT ("Qsup_c_sum") :NAME "Qsup_c_sum" :PADDING 3 :DATA :EO :D (:DICT (ICE DESCRIPTIONS ADDER))) """.format(x_coord+23))
    except:
        pass

    #----------energy plants-----------
    x_coord=46
    #Tsup mean ep
    if requestedOutputs['tsup_mean_ep_kpi'] or requestedOutputs['tsup_mean_ep_system']:
        filedata.append("""\n(EQUATION-FRAME :AT (({} 175)) :R (18 18) :ICON "lib:gain.ids" :SLOT ("Tsup_mean_ep") :NAME "Tsup_mean_ep" :DATA MODEL) """.format(x_coord))
        filedata.append("""\n(CONNECTION-LINE :AT ((10 140) ({} 140) ({} 175) ({} 175)) :FIRST-LINK (:SELF (0.0 0.074) "Int_Ref_Sensor_Target_{}_X_X_X") :LAST-LINK ("Tsup_mean_ep" (0 0.5) |u|) :DIR :RIGHT :ARROW (19 8 8)) """.format(x_coord-31,x_coord-31,x_coord-21.5,added_sensor_info['tsup_mean_ep_system']))
        x_coord+=dx_coord
    #Tsup mean ep kpi
    if requestedOutputs['tsup_mean_ep_kpi']:
        filedata.append("""\n(EQUATION-FRAME :AT (({} 175)) :R (16 16) :ICON "lib:slidingaverage.ids" :SLOT ("Tsup_mean_ep_kpi") :NAME "Tsup_mean_ep_kpi" :DATA MODEL) """.format(x_coord-67))
        filedata.append("""\n(CONNECTION-LINE :AT (({} 175) ({} 175)) :FIRST-LINK ("Tsup_mean_ep" (1 0.5) |y|) :LAST-LINK ("Tsup_mean_ep_kpi" (0 0.5) (|u| 1)) :DIR :RIGHT :ARROW (19 8 8)) """.format(x_coord-100,x_coord-86))
    #Tsup min ep
    if requestedOutputs['tsup_min_ep_kpi'] or requestedOutputs['tsup_min_ep_system']:
        filedata.append("""\n(EQUATION-FRAME :AT (({} 175)) :R (18 18) :ICON "lib:gain.ids" :SLOT ("min") :NAME "Tsup_min_ep" :DATA MODEL) """.format(x_coord))
        filedata.append("""\n(CONNECTION-LINE :AT ((10 140) ({} 140) ({} 175) ({} 175)) :FIRST-LINK (:SELF (0.0 0.074) "Int_Ref_Sensor_Target_{}_X_X_X") :LAST-LINK ("Tsup_min_ep" (0 0.5) |u|) :DIR :RIGHT :ARROW (19 8 8)) """.format(x_coord-31,x_coord-31,x_coord-21.5,added_sensor_info['tsup_min_ep_system']))
        x_coord+=dx_coord
    #Tsup min c kpi
    if requestedOutputs['tsup_min_ep_kpi']:
        filedata.append("""\n(EQUATION-FRAME :AT (({} 175)) :R (16 16) :ICON "lib:snapminmax.ids" :SLOT ("Tsup_min_ep_kpi") :NAME "Tsup_min_ep_kpi" :DATA MODEL) """.format(x_coord-67))
        filedata.append("""\n(CONNECTION-LINE :AT (({} 175) ({} 175)) :FIRST-LINK ("Tsup_min_ep" (1 0.5) |y|) :LAST-LINK ("Tsup_min_ep_kpi" (0 0.5) (|u| 1)) :DIR :RIGHT :ARROW (19 8 8)) """.format(x_coord-100,x_coord-86))
    #Tsup max c
    if requestedOutputs['tsup_max_ep_kpi'] or requestedOutputs['tsup_max_ep_system']:
        filedata.append("""\n(EQUATION-FRAME :AT (({} 175)) :R (18 18) :ICON "lib:gain.ids" :SLOT ("min") :NAME "Tsup_max_ep" :DATA MODEL) """.format(x_coord))
        filedata.append("""\n(CONNECTION-LINE :AT ((10 140) ({} 140) ({} 175) ({} 175)) :FIRST-LINK (:SELF (0.0 0.074) "Int_Ref_Sensor_Target_{}_X_X_X") :LAST-LINK ("Tsup_max_ep" (0 0.5) |u|) :DIR :RIGHT :ARROW (19 8 8)) """.format(x_coord-31,x_coord-31,x_coord-21.5,added_sensor_info['tsup_max_ep_system']))
        x_coord+=dx_coord
    #Tsup max c kpi
    if requestedOutputs['tsup_max_ep_kpi']:
        filedata.append("""\n(EQUATION-FRAME :AT (({} 175)) :R (16 16) :ICON "lib:snapminmax.ids" :SLOT ("Tsup_max_ep_kpi") :NAME "Tsup_max_ep_kpi" :DATA MODEL) """.format(x_coord-67))
        filedata.append("""\n(CONNECTION-LINE :AT (({} 175) ({} 175)) :FIRST-LINK ("Tsup_max_ep" (1 0.5) |y|) :LAST-LINK ("Tsup_max_ep_kpi" (0 0.5) (|u| 1)) :DIR :RIGHT :ARROW (19 8 8)) """.format(x_coord-100,x_coord-86))
    #Tret mean ep
    if requestedOutputs['tret_mean_ep_kpi'] or requestedOutputs['tret_mean_ep_system']:
        filedata.append("""\n(EQUATION-FRAME :AT (({} 175)) :R (18 18) :ICON "lib:gain.ids" :SLOT ("Tret_mean_ep") :NAME "Tret_mean_ep" :DATA MODEL) """.format(x_coord))
        filedata.append("""\n(CONNECTION-LINE :AT ((10 140) ({} 140) ({} 175) ({} 175)) :FIRST-LINK (:SELF (0.0 0.074) "Int_Ref_Sensor_Target_{}_X_X_X") :LAST-LINK ("Tret_mean_ep" (0 0.5) |u|) :DIR :RIGHT :ARROW (19 8 8)) """.format(x_coord-31,x_coord-31,x_coord-21.5,added_sensor_info['tret_mean_ep_system']))
        x_coord+=dx_coord
    #Tret mean ep kpi
    if requestedOutputs['tret_mean_ep_kpi']:
        filedata.append("""\n(EQUATION-FRAME :AT (({} 175)) :R (16 16) :ICON "lib:slidingaverage.ids" :SLOT ("Tret_mean_ep_kpi") :NAME "Tret_mean_ep_kpi" :DATA MODEL) """.format(x_coord-67))
        filedata.append("""\n(CONNECTION-LINE :AT (({} 175) ({} 175)) :FIRST-LINK ("Tret_mean_ep" (1 0.5) |y|) :LAST-LINK ("Tret_mean_ep_kpi" (0 0.5) (|u| 1)) :DIR :RIGHT :ARROW (19 8 8)) """.format(x_coord-100,x_coord-86))
    #Tret min ep
    if requestedOutputs['tret_min_ep_kpi'] or requestedOutputs['tret_min_ep_system']:
        filedata.append("""\n(EQUATION-FRAME :AT (({} 175)) :R (18 18) :ICON "lib:gain.ids" :SLOT ("min") :NAME "Tret_min_ep" :DATA MODEL) """.format(x_coord))
        filedata.append("""\n(CONNECTION-LINE :AT ((10 140) ({} 140) ({} 175) ({} 175)) :FIRST-LINK (:SELF (0.0 0.074) "Int_Ref_Sensor_Target_{}_X_X_X") :LAST-LINK ("Tret_min_ep" (0 0.5) |u|) :DIR :RIGHT :ARROW (19 8 8)) """.format(x_coord-31,x_coord-31,x_coord-21.5,added_sensor_info['tret_min_ep_system']))
        x_coord+=dx_coord
    #Tret min c kpi
    if requestedOutputs['tret_min_ep_kpi']:
        filedata.append("""\n(EQUATION-FRAME :AT (({} 175)) :R (16 16) :ICON "lib:snapminmax.ids" :SLOT ("Tret_min_ep_kpi") :NAME "Tret_min_ep_kpi" :DATA MODEL) """.format(x_coord-67))
        filedata.append("""\n(CONNECTION-LINE :AT (({} 175) ({} 175)) :FIRST-LINK ("Tret_min_ep" (1 0.5) |y|) :LAST-LINK ("Tret_min_ep_kpi" (0 0.5) (|u| 1)) :DIR :RIGHT :ARROW (19 8 8)) """.format(x_coord-100,x_coord-86))
    #Tret max c
    if requestedOutputs['tret_max_ep_kpi'] or requestedOutputs['tret_max_ep_system']:
        filedata.append("""\n(EQUATION-FRAME :AT (({} 175)) :R (18 18) :ICON "lib:gain.ids" :SLOT ("min") :NAME "Tret_max_ep" :DATA MODEL) """.format(x_coord))
        filedata.append("""\n(CONNECTION-LINE :AT ((10 140) ({} 140) ({} 175) ({} 175)) :FIRST-LINK (:SELF (0.0 0.074) "Int_Ref_Sensor_Target_{}_X_X_X") :LAST-LINK ("Tret_max_ep" (0 0.5) |u|) :DIR :RIGHT :ARROW (19 8 8)) """.format(x_coord-31,x_coord-31,x_coord-21.5,added_sensor_info['tret_max_ep_system']))
        x_coord+=dx_coord
    #Tret max c kpi
    if requestedOutputs['tret_max_ep_kpi']:
        filedata.append("""\n(EQUATION-FRAME :AT (({} 175)) :R (16 16) :ICON "lib:snapminmax.ids" :SLOT ("Tret_max_ep_kpi") :NAME "Tret_max_ep_kpi" :DATA MODEL) """.format(x_coord-67))
        filedata.append("""\n(CONNECTION-LINE :AT (({} 175) ({} 175)) :FIRST-LINK ("Tret_max_ep" (1 0.5) |y|) :LAST-LINK ("Tret_max_ep_kpi" (0 0.5) (|u| 1)) :DIR :RIGHT :ARROW (19 8 8)) """.format(x_coord-100,x_coord-86))
    #qsup ep
    try:  
        sensor_id=added_sensor_info['qsup_ep']
        filedata.append("""\n(EQUATION-FRAME :AT (({} 175)) :R (18 18) :ICON "lib:gain.ids" :SLOT ("min") :NAME "Qsup_ep" :DATA MODEL) """.format(x_coord))
        filedata.append("""\n(CONNECTION-LINE :AT ((10 140) ({} 140) ({} 175) ({} 175)) :FIRST-LINK (:SELF (0.0 0.074) "Int_Ref_Sensor_Target_{}_X_X_X") :LAST-LINK ("Qsup_ep" (0 0.5) |u|) :DIR :RIGHT :ARROW (19 8 8)) """.format(x_coord-31,x_coord-31,x_coord-21.5,sensor_id))
        x_coord+=dx_coord
        filedata.append("""\n(EQUATION-FRAME :AT (({} 175)) :R (16 16) :ICON "lib:sepsign.ids" :SLOT ("Qsup_ep_sepsign") :NAME "Qsup_ep_sepsign" :DATA MODEL) """.format(x_coord-67))
        filedata.append("""\n(CONNECTION-LINE :AT (({} 175) ({} 175)) :FIRST-LINK ("Qsup_ep" (1 0.5) |y|) :LAST-LINK ("Qsup_ep_sepsign" (0 0.5) INSIGNALLINK) :DIR :RIGHT :ARROW (19 8 8)) """.format(x_coord-100,x_coord-86))
        if requestedOutputs['qsup_heat_ep_kpi'] or requestedOutputs['qsup_heat_spec_ep_kpi'] or requestedOutputs['qsup_heat_density_ep_kpi'] or requestedOutputs['qsup_heat_linedensity_ep_kpi']:
            filedata.append("""\n(EQUATION-FRAME :AT (({} 157)) :R (14 16) :ICON "lib:emeter.ids" :SLOT ("Qsup_ep_pos") :NAME "Qsup_ep_pos" :PADDING 3 :DATA :CEO :D (:DICT (ICE DESCRIPTIONS EMETER))) """.format(x_coord-21))
            filedata.append("""\n(CONNECTION-LINE :AT (({} 166) ({} 166) ({} 158) ({} 158)) :FIRST-LINK ("Qsup_ep_sepsign" (1.0 0.219) POSSIGNALLINK) :LAST-LINK ("Qsup_ep_pos" (0.0 0.531) (INCONSUMLINK 1)) :DIR :RIGHT :ARROW (19 8 8)) """.format(x_coord-50,x_coord-44,x_coord-44,x_coord-35))
        if requestedOutputs['qsup_cold_ep_kpi'] or requestedOutputs['qsup_cold_spec_ep_kpi'] or requestedOutputs['qsup_cold_density_ep_kpi'] or requestedOutputs['qsup_cold_linedensity_ep_kpi']:
            filedata.append("""\n(EQUATION-FRAME :AT (({} 195)) :R (14 16) :ICON "lib:emeter.ids" :SLOT ("Qsup_ep_neg") :NAME "Qsup_ep_neg" :PADDING 3 :DATA :CEO :D (:DICT (ICE DESCRIPTIONS EMETER))) """.format(x_coord-19))
            filedata.append("""\n(CONNECTION-LINE :AT (({} 184) ({} 184) ({} 196) ({} 196)) :FIRST-LINK ("Qsup_ep_sepsign" (1 0.781) NEGSIGNALLINK) :LAST-LINK ("Qsup_ep_neg" (0.0 0.531) (INCONSUMLINK 1)) :DIR :RIGHT :ARROW (19 8 8)) """.format(x_coord-50,x_coord-44,x_coord-44,x_coord-33))
        if requestedOutputs['qsup_ep_kpi'] or requestedOutputs['qsup_spec_ep_kpi'] or requestedOutputs['qsup_density_ep_kpi'] or requestedOutputs['qsup_linedensity_ep_kpi']:
            filedata.append("""\n(EQUATION-FRAME :AT (({} 175)) :R (16 16) :ICON "lib:adder.ids" :SLOT ("Qsup_ep_sum") :NAME "Qsup_ep_sum" :PADDING 3 :DATA :EO :D (:DICT (ICE DESCRIPTIONS ADDER))) """.format(x_coord+23))
    except:
        pass
        
    #qamb
    x_coord=46
    if requestedOutputs['heatbalance_system'] or requestedOutputs['qamb_kpi']:
        filedata.append("""\n(EQUATION-FRAME :AT (({} 275)):R (16 16) :ICON "lib:adder.ids" :SLOT ("qamb") :NAME "qamb" :PADDING 3 :DATA :EO :D (:DICT (ICE DESCRIPTIONS ADDER))) """.format(x_coord))     
        if requestedOutputs['qamb_kpi']:
            x_coord=46+dx_coord
            filedata.append("""\n(EQUATION-FRAME :AT (({} 275)) :R (14 16) :ICON "lib:emeter.ids" :SLOT ("Qamb_emeter") :NAME "Qamb_emeter" :PADDING 3 :DATA :CEO :D (:DICT (ICE DESCRIPTIONS EMETER))) """.format(x_coord-67))
            filedata.append("""\n(CONNECTION-LINE :AT (({} 275) ({} 275)) :FIRST-LINK ("Qsup_ep_sepsign" (1.0 0.219) POSSIGNALLINK) :LAST-LINK ("Qamb_emeter" (0.0 0.531) (INCONSUMLINK 1)) :DIR :RIGHT :ARROW (19 8 8)) """.format(x_coord-100,x_coord-86))

    #----------system-----------
    x_coord=46+dx_coord
    #heat balance
    if requestedOutputs['heatbalance_system']:
        for i in added_sensor_info['heatbalance_system']:
            name= 'hb_'+('customer' if i['type']==1 else 'energy_plant')+'_' + i['template_name']
            filedata.append("""\n(EQUATION-FRAME :AT (({} 275)) :R (16 16) :ICON "lib:gain.ids" :SLOT ("") :NAME "{}" :DATA MODEL) """.format(x_coord,name,name))
            filedata.append("""\n(CONNECTION-LINE :AT ((10 240) ({} 240) ({} 275) ({} 275)) :FIRST-LINK (:SELF (0.0 0.074) "Int_Ref_Sensor_Target_{}_X_X_X") :LAST-LINK ("{}" (0 0.5) |u|) :DIR :RIGHT :ARROW (19 8 8)) """.format(x_coord-31,x_coord-31,x_coord-21.5,i['id'],name))
            x_coord+=dx_coord  
    x_coord=46
    #mass balance
    if requestedOutputs['massbalance_system']:
        for i in added_sensor_info['massbalance_system']:
            name= 'mdotb_'+('customer' if i['type']==1 else 'energy_plant')+'_' + i['template_name']
            filedata.append("""\n(EQUATION-FRAME :AT (({} 375)) :R (18 18) :ICON "lib:gain.ids" :SLOT ("") :NAME "{}" :DATA MODEL) """.format(x_coord,name,name))
            filedata.append("""\n(CONNECTION-LINE :AT ((10 340) ({} 340) ({} 375) ({} 375)) :FIRST-LINK (:SELF (0.0 0.074) "Int_Ref_Sensor_Target_{}_X_X_X") :LAST-LINK ("{}" (0 0.5) |u|) :DIR :RIGHT :ARROW (19 8 8)) """.format(x_coord-31,x_coord-31,x_coord-21.5,i['id'],name))
            x_coord+=dx_coord    
            
    writeToFileFromList(filedata,dir,dir+'\\Results-macro.idc')

def addRequestedOutputsSensors(cur,config,requestedOutputs):
    #print('--addRequestedOutputsSensors--')
    loadedSensorData=getStoredSensorTableValues(cur)
    #print(loadedSensorData)
    if loadedSensorData:
        sensor_data=loadedSensorData.copy()
    else:
        sensor_data={}
    
    max_sensor_id=getMaxId(cur,'sensors')
    added_sensor_info={}
    
    c_templates={i['template'] : True for i in getUsedFilteredFeatureTemplates('customer',cur,config)}
    c_connTypes={i : True for i in getUsedConnTypes('customer',cur,config)}
    c_conns_sup={i : True for i in getUsedConnectionsFilteredByDirection('customer',cur,config,['1'])}
    c_conns_ret={i : True for i in getUsedConnectionsFilteredByDirection('customer',cur,config,['2'])}
    
    ep_templates={i['template'] : True for i in getUsedFilteredFeatureTemplates('energy_plant',cur,config)}
    ep_connTypes={i : True for i in getUsedConnTypes('energy_plant',cur,config)}
    ep_conns_sup={i : True for i in getUsedConnectionsFilteredByDirection('energy_plant',cur,config,['1'])}
    ep_conns_ret={i : True for i in getUsedConnectionsFilteredByDirection('energy_plant',cur,config,['2'])}
    

    #---------customers-------------
    #Tsup
    if requestedOutputs['tsup_mean_c_kpi'] or requestedOutputs['tsup_mean_c_system']:
        max_sensor_id+=1
        sensor_data[max_sensor_id]={'source' : {'type' : 1,'templates' : c_templates,'conn_types' : c_connTypes,'conns' : c_conns_sup,'measure' : 1,'function' : 3,'test_value' : 1,'description' : ''}, 
                'target': {'type' : 4,'templates' : {},'description' : ''}}
        added_sensor_info['tsup_mean_c_system']=max_sensor_id
    if requestedOutputs['tsup_max_c_kpi'] or requestedOutputs['tsup_max_c_system']:
        max_sensor_id+=1
        sensor_data[max_sensor_id]={'source' : {'type' : 1,'templates' : c_templates,'conn_types' : c_connTypes,'conns' : c_conns_sup,'measure' : 1,'function' : 2,'test_value' : 1,'description' : ''}, 
                'target': {'type' : 4,'templates' : {},'description' : ''}}
        added_sensor_info['tsup_max_c_system']=max_sensor_id
    if requestedOutputs['tsup_min_c_kpi'] or requestedOutputs['tsup_min_c_system']:
        max_sensor_id+=1
        sensor_data[max_sensor_id]={'source' : {'type' : 1,'templates' : c_templates,'conn_types' : c_connTypes,'conns' : c_conns_sup,'measure' : 1,'function' : 1,'test_value' : 1,'description' : ''}, 
                'target': {'type' : 4,'templates' : {},'description' : ''}}
        added_sensor_info['tsup_min_c_system']=max_sensor_id
    #Tret  
    if requestedOutputs['tret_mean_c_kpi'] or requestedOutputs['tret_mean_c_system']:
        max_sensor_id+=1
        sensor_data[max_sensor_id]={'source' : {'type' : 1,'templates' : c_templates,'conn_types' : c_connTypes,'conns' : c_conns_ret,'measure' : 1,'function' : 3,'test_value' : 1,'description' : ''}, 
                'target': {'type' : 4,'templates' : {},'description' : ''}}
        added_sensor_info['tret_mean_c_system']=max_sensor_id
    if requestedOutputs['tret_max_c_kpi'] or requestedOutputs['tret_max_c_system']:
        max_sensor_id+=1
        sensor_data[max_sensor_id]={'source' : {'type' : 1,'templates' : c_templates,'conn_types' : c_connTypes,'conns' : c_conns_ret,'measure' : 1,'function' : 2,'test_value' : 1,'description' : ''}, 
                'target': {'type' : 4,'templates' : {},'description' : ''}}
        added_sensor_info['tret_max_c_system']=max_sensor_id
    if requestedOutputs['tret_min_c_kpi'] or requestedOutputs['tret_min_c_system']:
        max_sensor_id+=1
        sensor_data[max_sensor_id]={'source' : {'type' : 1,'templates' : c_templates,'conn_types' : c_connTypes,'conns' : c_conns_ret,'measure' : 1,'function' : 1,'test_value' : 1,'description' : ''}, 
                'target': {'type' : 4,'templates' : {},'description' : ''}}
        added_sensor_info['tret_min_c_system']=max_sensor_id
        
    #energy plants
    #Tsup
    if requestedOutputs['tsup_mean_ep_kpi'] or requestedOutputs['tsup_mean_ep_system']:
        max_sensor_id+=1
        sensor_data[max_sensor_id]={'source' : {'type' : 2,'templates' : ep_templates,'conn_types' : ep_connTypes,'conns' : ep_conns_sup,'measure' : 1,'function' : 3,'test_value' : 1,'description' : ''}, 
                'target': {'type' : 4,'templates' : {},'description' : ''}}
        added_sensor_info['tsup_mean_ep_system']=max_sensor_id
    if requestedOutputs['tsup_max_ep_kpi'] or requestedOutputs['tsup_max_ep_system']:
        max_sensor_id+=1
        sensor_data[max_sensor_id]={'source' : {'type' : 2,'templates' : ep_templates,'conn_types' : ep_connTypes,'conns' : ep_conns_sup,'measure' : 1,'function' : 2,'test_value' : 1,'description' : ''}, 
                'target': {'type' : 4,'templates' : {},'description' : ''}}
        added_sensor_info['tsup_max_ep_system']=max_sensor_id
    if requestedOutputs['tsup_min_ep_kpi'] or requestedOutputs['tsup_min_ep_system']:
        max_sensor_id+=1
        sensor_data[max_sensor_id]={'source' : {'type' : 2,'templates' : ep_templates,'conn_types' : ep_connTypes,'conns' : ep_conns_sup,'measure' : 1,'function' : 1,'test_value' : 1,'description' : ''}, 
                'target': {'type' : 4,'templates' : {},'description' : ''}}
        added_sensor_info['tsup_min_ep_system']=max_sensor_id
    #Tret  
    if requestedOutputs['tret_mean_ep_kpi'] or requestedOutputs['tret_mean_ep_system']:
        max_sensor_id+=1
        sensor_data[max_sensor_id]={'source' : {'type' : 2,'templates' : ep_templates,'conn_types' : ep_connTypes,'conns' : ep_conns_ret,'measure' : 1,'function' : 3,'test_value' : 1,'description' : ''}, 
                'target': {'type' : 4,'templates' : {},'description' : ''}}
        added_sensor_info['tret_mean_ep_system']=max_sensor_id
    if requestedOutputs['tret_max_ep_kpi'] or requestedOutputs['tret_max_ep_system']:
        max_sensor_id+=1
        sensor_data[max_sensor_id]={'source' : {'type' : 2,'templates' : ep_templates,'conn_types' : ep_connTypes,'conns' : ep_conns_ret,'measure' : 1,'function' : 2,'test_value' : 1,'description' : ''}, 
                'target': {'type' : 4,'templates' : {},'description' : ''}}
        added_sensor_info['tret_max_ep_system']=max_sensor_id
    if requestedOutputs['tret_min_ep_kpi'] or requestedOutputs['tret_min_ep_system']:
        max_sensor_id+=1
        sensor_data[max_sensor_id]={'source' : {'type' : 2,'templates' : ep_templates,'conn_types' : ep_connTypes,'conns' : ep_conns_ret,'measure' : 1,'function' : 1,'test_value' : 1,'description' : ''}, 
                'target': {'type' : 4,'templates' : {},'description' : ''}}
        added_sensor_info['tret_min_ep_system']=max_sensor_id
        
    #System
    #Heat balance
    if requestedOutputs['heatbalance_system']:
        #energy plants
        sensor_info=[]
        for template in ep_templates:
            max_sensor_id+=1
            connTypes=getConntypesByTemplate('energy_plant',template,cur)
            sensor_data[max_sensor_id]={'source' : {'type' : 2,'templates' : {template : True},'conn_types' : {i : True for i in connTypes},'conns' : {},'measure' : 4,'function' : 4,'test_value' : 1,'description' : ''}, 
                    'target': {'type' : 4,'templates' : {},'description' : ''}}
            sensor_info.append({'id': max_sensor_id, 'type': 2, 'template': template,'template_name':getTemplateNameByTemplateId(cur,template,'energy_plant')})
        #customers
        for template in c_templates:
            max_sensor_id+=1
            connTypes=getConntypesByTemplate('customer',template,cur)
            sensor_data[max_sensor_id]={'source' : {'type' : 1,'templates' : {template : True},'conn_types' : {i : True for i in connTypes},'conns' : {},'measure' : 4,'function' : 4,'test_value' : 1,'description' : ''}, 
                    'target': {'type' : 4,'templates' : {},'description' : ''}}
            sensor_info.append({'id': max_sensor_id, 'type': 1, 'template': template,'template_name':getTemplateNameByTemplateId(cur,template,'customer')})
        #print('--------')
        #print(sensor_info)
        added_sensor_info['heatbalance_system']=sensor_info
    #Mass balance
    if requestedOutputs['massbalance_system']:
        #energy plants
        sensor_info=[]
        for template in ep_templates:
            max_sensor_id+=1
            connTypes=getConntypesByTemplate('energy_plant',template,cur)
            conns_sup=getConnsByConntype(connTypes,cur)
            sensor_data[max_sensor_id]={'source' : {'type' : 2,'templates' : {template : True},'conn_types' : {i : True for i in connTypes},'conns' : {i : True for i in conns_sup},'measure' : 3,'function' : 4,'test_value' : 1,'description' : ''}, 
                    'target': {'type' : 4,'templates' : {},'description' : ''}}
            sensor_info.append({'id': max_sensor_id, 'type': 2, 'template': template,'template_name':getTemplateNameByTemplateId(cur,template,'energy_plant')})
        #customers
        for template in c_templates:
            max_sensor_id+=1
            connTypes=getConntypesByTemplate('customer',template,cur)
            conns_sup=getConnsByConntype(connTypes,cur)
            sensor_data[max_sensor_id]={'source' : {'type' : 1,'templates' : {template : True},'conn_types' : {i : True for i in connTypes},'conns' : {i : True for i in conns_sup},'measure' : 3,'function' : 4,'test_value' : 1,'description' : ''}, 
                    'target': {'type' : 4,'templates' : {},'description' : ''}}
            sensor_info.append({'id': max_sensor_id, 'type': 1, 'template': template,'template_name':getTemplateNameByTemplateId(cur,template,'customer')})
        #print('--------')
        #print(sensor_info)
        added_sensor_info['massbalance_system']=sensor_info
        
    #KPI`s
    #customers
    if requestedOutputs['qsup_heat_c_kpi'] or requestedOutputs['qsup_cold_c_kpi'] or requestedOutputs['qsup_c_kpi'] or requestedOutputs['qsup_heat_spec_c_kpi'] or requestedOutputs['qsup_cold_spec_c_kpi'] or requestedOutputs['qsup_spec_c_kpi'] or requestedOutputs['qsup_heat_density_c_kpi'] or requestedOutputs['qsup_cold_density_c_kpi'] or requestedOutputs['qsup_density_c_kpi'] or requestedOutputs['qsup_heat_linedensity_c_kpi'] or requestedOutputs['qsup_cold_linedensity_c_kpi'] or requestedOutputs['qsup_linedensity_c_kpi']:
        max_sensor_id+=1
        sensor_data[max_sensor_id]={'source' : {'type' : 1,'templates' : c_templates,'conn_types' : c_connTypes,'conns' : {},'measure' : 4,'function' : 4,'test_value' : 1,'description' : ''}, 
                'target': {'type' : 4,'templates' : {},'description' : ''}}
        added_sensor_info['qsup_c']=max_sensor_id
    
    #energy plants
    if requestedOutputs['qsup_heat_ep_kpi'] or requestedOutputs['qsup_cold_ep_kpi'] or requestedOutputs['qsup_ep_kpi']:
        max_sensor_id+=1
        sensor_data[max_sensor_id]={'source' : {'type' : 2,'templates' : ep_templates,'conn_types' : ep_connTypes,'conns' : {},'measure' : 4,'function' : 4,'test_value' : 1,'description' : ''}, 
                'target': {'type' : 4,'templates' : {},'description' : ''}}
        added_sensor_info['qsup_ep']=max_sensor_id

        
    #print(added_sensor_info)
    #print(sensor_data)
    writeSensorsToDB(cur,config,sensorData=sensor_data,loadedSensorData=loadedSensorData)
    #print('--finished addRequestedOutputsSensors--')
    return added_sensor_info

class WorkerSetRequestedOutputs(QRunnable):      
    """Worker thread
    Inherits from QRunnable to handle worker thread setup, signals and wrap-up."""
    def __init__(self,*args,**kwargs):
        super().__init__()
        
        self.signals=APISignals()
        self.config=kwargs['config']
        self.dlg=kwargs['dlg']
        self.plugin_dir=kwargs['plugin_dir']
        self.requestedOutputs=kwargs['requestedOutputs']
        self.dlg.process_running=True
        self.conn=""
        self.cur=""
        self.conn = dbConnect(self.config,True)
        if self.conn:
            self.cur=self.conn.cursor(cursor_factory = psycopg2.extras.RealDictCursor)
            
    @pyqtSlot()
    def run(self):
        self.progress_value=1
        self.signals.progress.emit(self.progress_value)
        self.setOutputs()
        self.signals.progress.emit(100)  
        self.signals.finished.emit('finished')  

    def setOutputs(self):
        #-------------temporal results---------------------------
        #-----------customers------------
        #-----------power----------
        if self.dlg.checkBoxSubstationPower.isChecked():
            self.requestedOutputs['power_c']=True
        else:
            self.requestedOutputs['power_c']=False
        #-----------temperature----------
        if self.dlg.checkBoxSubstationConnTemp.isChecked():
            self.requestedOutputs['temp_c']=True
        else:
            self.requestedOutputs['temp_c']=False
        #-----------pressure----------
        if self.dlg.checkBoxSubstationPressure.isChecked():
            self.requestedOutputs['p_c']=True
        else:
            self.requestedOutputs['p_c']=False
        #-----------mdot----------
        if self.dlg.checkBoxSubstationMassflow.isChecked():
            self.requestedOutputs['mdot_c']=True
        else:
            self.requestedOutputs['mdot_c']=False
        #-----------heat balance----------
        if self.dlg.checkBoxSubstationHeatbalance.isChecked():
            self.requestedOutputs['heatbalance_c']=True
        else:
            self.requestedOutputs['heatbalance_c']=False
        #-----------tair----------
        if self.dlg.checkBoxSubstationTair.isChecked():
            self.requestedOutputs['troom_c']=True
        else:
            self.requestedOutputs['troom_c']=False
        
        #-------------network------------
        #+++lines+++
        #temp
        if self.dlg.checkBoxTempPipe.isChecked():
            self.requestedOutputs['temp_lines']=True
        else:
            self.requestedOutputs['temp_lines']=False
        #v
        if self.dlg.checkBoxVPipe.isChecked():
            self.requestedOutputs['v_lines']=True
        else:
            self.requestedOutputs['v_lines']=False
        #qamb
        if self.dlg.checkBoxQambPipe.isChecked():
            self.requestedOutputs['qamb_lines']=True
        else:
            self.requestedOutputs['qamb_lines']=False
            
        #+++nodes+++
        #mdot
        if self.dlg.checkBoxMdotNode.isChecked():
            self.requestedOutputs['mdot_lines']=True
        else:
            self.requestedOutputs['mdot_lines']=False
        #pressure
        if self.dlg.checkBoxPressureDistribution.isChecked():
            self.requestedOutputs['p_lines']=True
        else:
            self.requestedOutputs['p_lines']=False
            
        #-------------system------------
        #heatbalance_system
        if self.dlg.heatbalance_system.isChecked():
            self.requestedOutputs['heatbalance_system']=True
        else:
            self.requestedOutputs['heatbalance_system']=False
        #massbalance_system
        if self.dlg.massbalance_system.isChecked():
            self.requestedOutputs['massbalance_system']=True
        else:
            self.requestedOutputs['massbalance_system']=False

        #tsup_mean_c_system
        if self.dlg.checkBoxMeanSupplyTempCSystem.isChecked():
            self.requestedOutputs['tsup_mean_c_system']=True
        else:
            self.requestedOutputs['tsup_mean_c_system']=False
        #tsup_max_c_system
        if self.dlg.checkBoxMaxSupplyTempCSystem.isChecked():
            self.requestedOutputs['tsup_max_c_system']=True
        else:
            self.requestedOutputs['tsup_max_c_system']=False
        #tsup_min_c_system
        if self.dlg.checkBoxMinSupplyTempCSystem.isChecked():
            self.requestedOutputs['tsup_min_c_system']=True
        else:
            self.requestedOutputs['tsup_min_c_system']=False

        #tsup_mean_ep_system
        if self.dlg.checkBoxMeanSupplyTempEpSystem.isChecked():
            self.requestedOutputs['tsup_mean_ep_system']=True
        else:
            self.requestedOutputs['tsup_mean_ep_system']=False
        #tsup_max_ep_system
        if self.dlg.checkBoxMaxSupplyTempEpSystem.isChecked():
            self.requestedOutputs['tsup_max_ep_system']=True
        else:
            self.requestedOutputs['tsup_max_ep_system']=False
        #tsup_min_ep_system
        if self.dlg.checkBoxMinSupplyTempEpSystem.isChecked():
            self.requestedOutputs['tsup_min_ep_system']=True
        else:
            self.requestedOutputs['tsup_min_ep_system']=False

        #tret_mean_c_system
        if self.dlg.checkBoxMeanReturnTempCSystem.isChecked():
            self.requestedOutputs['tret_mean_c_system']=True
        else:
            self.requestedOutputs['tret_mean_c_system']=False
        #tret_max_c_system
        if self.dlg.checkBoxMaxReturnTempCSystem.isChecked():
            self.requestedOutputs['tret_max_c_system']=True
        else:
            self.requestedOutputs['tret_max_c_system']=False
        #tret_min_c_system
        if self.dlg.checkBoxMinReturnTempCSystem.isChecked():
            self.requestedOutputs['tret_min_c_system']=True
        else:
            self.requestedOutputs['tret_min_c_system']=False

        #tret_mean_ep_system
        if self.dlg.checkBoxMeanReturnTempEpSystem.isChecked():
            self.requestedOutputs['tret_mean_ep_system']=True
        else:
            self.requestedOutputs['tret_mean_ep_system']=False
        #tret_max_ep_system
        if self.dlg.checkBoxMaxReturnTempEpSystem.isChecked():
            self.requestedOutputs['tret_max_ep_system']=True
        else:
            self.requestedOutputs['tret_max_ep_system']=False
        #tret_min_ep_system
        if self.dlg.checkBoxMinReturnTempEpSystem.isChecked():
            self.requestedOutputs['tret_min_ep_system']=True
        else:
            self.requestedOutputs['tret_min_ep_system']=False
        
        #-----------energy plants------------
        #-----------power----------
        if self.dlg.checkBoxPlantPower.isChecked():
            self.requestedOutputs['power_ep']=True
        else:
            self.requestedOutputs['power_ep']=False
        #-----------temperature----------
        if self.dlg.checkBoxPlantConnTemp.isChecked():
            self.requestedOutputs['temp_ep']=True
        else:
            self.requestedOutputs['temp_ep']=False
        #-----------pressure----------
        if self.dlg.checkBoxPlantPressure.isChecked():
            self.requestedOutputs['p_ep']=True
        else:
            self.requestedOutputs['p_ep']=False
        #-----------massflow----------
        if self.dlg.checkBoxPlantMassflow.isChecked():
            self.requestedOutputs['mdot_ep']=True
        else:
            self.requestedOutputs['mdot_ep']=False
            
        #-------------KPI`S---------------------------
        #-----------customers------------
        #tsup_mean_c_kpi
        if self.dlg.checkBoxMeanSupplyTempC.isChecked():
            self.requestedOutputs['tsup_mean_c_kpi']=True
        else:
            self.requestedOutputs['tsup_mean_c_kpi']=False
        #tsup_max_c_kpi
        if self.dlg.checkBoxMaxSupplyTempC.isChecked():
            self.requestedOutputs['tsup_max_c_kpi']=True
        else:
            self.requestedOutputs['tsup_max_c_kpi']=False
        #tsup_min_c_kpi
        if self.dlg.checkBoxMinSupplyTempC.isChecked():
            self.requestedOutputs['tsup_min_c_kpi']=True
        else:
            self.requestedOutputs['tsup_min_c_kpi']=False
        #tret_mean_c_kpi
        if self.dlg.checkBoxMeanRetTempC.isChecked():
            self.requestedOutputs['tret_mean_c_kpi']=True
        else:
            self.requestedOutputs['tret_mean_c_kpi']=False
        #tret_max_c_kpi
        if self.dlg.checkBoxMaxRetTempC.isChecked():
            self.requestedOutputs['tret_max_c_kpi']=True
        else:
            self.requestedOutputs['tret_max_c_kpi']=False
        #tret_min_c_kpi
        if self.dlg.checkBoxMinRetTempC.isChecked():
            self.requestedOutputs['tret_min_c_kpi']=True
        else:
            self.requestedOutputs['tret_min_c_kpi']=False

        #qsup_heat
        if self.dlg.checkBoxQsupHeatC.isChecked():
            self.requestedOutputs['qsup_heat_c_kpi']=True
        else:
            self.requestedOutputs['qsup_heat_c_kpi']=False
        #qsup_cold
        if self.dlg.checkBoxQsupColdC.isChecked():
            self.requestedOutputs['qsup_cold_c_kpi']=True
        else:
            self.requestedOutputs['qsup_cold_c_kpi']=False
        #qsup_energy
        if self.dlg.checkBoxQsupEnergyC.isChecked():
            self.requestedOutputs['qsup_c_kpi']=True
        else:
            self.requestedOutputs['qsup_c_kpi']=False
        
            
        #-----------energy plants------------
        #tsup_mean_ep_kpi
        if self.dlg.checkBoxMeanSupplyTempEp.isChecked():
            self.requestedOutputs['tsup_mean_ep_kpi']=True
        else:
            self.requestedOutputs['tsup_mean_ep_kpi']=False
        #tsup_max_ep_kpi
        if self.dlg.checkBoxMaxSupplyTempEp.isChecked():
            self.requestedOutputs['tsup_max_ep_kpi']=True
        else:
            self.requestedOutputs['tsup_max_ep_kpi']=False
        #tsup_min_ep_kpi
        if self.dlg.checkBoxMinSupplyTempEp.isChecked():
            self.requestedOutputs['tsup_min_ep_kpi']=True
        else:
            self.requestedOutputs['tsup_min_ep_kpi']=False
        #tret_mean_ep_kpi
        if self.dlg.checkBoxMeanRetTempEp.isChecked():
            self.requestedOutputs['tret_mean_ep_kpi']=True
        else:
            self.requestedOutputs['tret_mean_ep_kpi']=False
        #tret_max_ep_kpi
        if self.dlg.checkBoxMaxRetTempEp.isChecked():
            self.requestedOutputs['tret_max_ep_kpi']=True
        else:
            self.requestedOutputs['tret_max_ep_kpi']=False
        #tret_min_ep_kpi
        if self.dlg.checkBoxMinRetTempEp.isChecked():
            self.requestedOutputs['tret_min_ep_kpi']=True
        else:
            self.requestedOutputs['tret_min_ep_kpi']=False

        #qsup_heat
        if self.dlg.checkBoxQsupHeatEp.isChecked():
            self.requestedOutputs['qsup_heat_ep_kpi']=True
        else:
            self.requestedOutputs['qsup_heat_ep_kpi']=False
        #qsup_cold
        if self.dlg.checkBoxQsupColdEp.isChecked():
            self.requestedOutputs['qsup_cold_ep_kpi']=True
        else:
            self.requestedOutputs['qsup_cold_ep_kpi']=False
        #qsup_energy
        if self.dlg.checkBoxQsupEnergyEp.isChecked():
            self.requestedOutputs['qsup_ep_kpi']=True
        else:
            self.requestedOutputs['qsup_ep_kpi']=False
            
        #-----------lines------------
        #qamb_kpi
        if self.dlg.checkBoxQambLines.isChecked():
            self.requestedOutputs['qamb_kpi']=True
        else:
            self.requestedOutputs['qamb_kpi']=False
        #volume_kpi
        if self.dlg.checkBoxVolumeLines.isChecked():
            self.requestedOutputs['volume_kpi']=True
        else:
            self.requestedOutputs['volume_kpi']=False

        #-----------system------------
        #qsup_heat_spec_c_kpi
        if self.dlg.checkBoxQsupHeatSpec.isChecked():
            self.requestedOutputs['qsup_heat_spec_c_kpi']=True
        else:
            self.requestedOutputs['qsup_heat_spec_c_kpi']=False
        #qsup_cold_spec_c_kpi
        if self.dlg.checkBoxQsupColdSpec.isChecked():
            self.requestedOutputs['qsup_cold_spec_c_kpi']=True
        else:
            self.requestedOutputs['qsup_cold_spec_c_kpi']=False
        #qsup_spec_c_kpi
        if self.dlg.checkBoxQsupEnergySpec.isChecked():
            self.requestedOutputs['qsup_spec_c_kpi']=True
        else:
            self.requestedOutputs['qsup_spec_c_kpi']=False        
            
        #qsup_heat_density_c_kpi
        if self.dlg.checkBoxQsupHeatDensity.isChecked():
            self.requestedOutputs['qsup_heat_density_c_kpi']=True
        else:
            self.requestedOutputs['qsup_heat_density_c_kpi']=False
        #qsup_cold_density_c_kpi
        if self.dlg.checkBoxQsupColdDensity.isChecked():
            self.requestedOutputs['qsup_cold_density_c_kpi']=True
        else:
            self.requestedOutputs['qsup_cold_density_c_kpi']=False
        #qsup_density_c_kpi
        if self.dlg.checkBoxQsupEnergyDensity.isChecked():
            self.requestedOutputs['qsup_density_c_kpi']=True
        else:
            self.requestedOutputs['qsup_density_c_kpi']=False

        #qsup_heat_linedensity_c_kpi
        if self.dlg.checkBoxQsupHeatLineDensity.isChecked():
            self.requestedOutputs['qsup_heat_linedensity_c_kpi']=True
        else:
            self.requestedOutputs['qsup_heat_linedensity_c_kpi']=False
        #qsup_cold_linedensity_c_kpi
        if self.dlg.checkBoxQsupColdLineDensity.isChecked():
            self.requestedOutputs['qsup_cold_linedensity_c_kpi']=True
        else:
            self.requestedOutputs['qsup_cold_linedensity_c_kpi']=False
        #qsup_linedensity_c_kpi
        if self.dlg.checkBoxQsupEnergyLineDensity.isChecked():
            self.requestedOutputs['qsup_linedensity_c_kpi']=True
        else:
            self.requestedOutputs['qsup_linedensity_c_kpi']=False

        #effWidth
        if self.dlg.checkBoxQEffWidth.isChecked():
            self.requestedOutputs['eff_width']=True
        else:
            self.requestedOutputs['eff_width']=False
            
        #-------------------timestep for outputs----------------------
        if is_number(self.dlg.outputTimestep.text()):
            self.requestedOutputs['dt_outputs']=self.dlg.outputTimestep.text()
        else:
            self.signals.error.emit("Timestep for Output is not a number!")
            
        writeRequestedOutputs(self.config,self.requestedOutputs)
        #print(self.requestedOutputs)
        #print(self.dlg.requestedOutputs_old)

        #check difference between new and old requested outputs
        outputs_c={}
        outputs_ep={}
        new_outputTimestep=False
        for out in self.requestedOutputs:
            if self.requestedOutputs[out]!=self.dlg.requestedOutputs_old[out]:
                #print('missmatch')
                if '_c' == out[-2:]:
                    outputs_c[out]=self.requestedOutputs[out]
                if '_ep' == out[-3:]:
                    outputs_ep[out]=self.requestedOutputs[out]
                if 'dt_outputs'==out:
                    new_outputTimestep=self.requestedOutputs[out]
                    
        #print(outputs_c)
        #print(outputs_ep)
        self.signals.progress.emit(5)
        both_featureType_update=(outputs_c or new_outputTimestep) and (outputs_ep or new_outputTimestep)
        if outputs_c or new_outputTimestep:
            self.updateTemplatesOutputs('customer',outputs_c,new_outputTimestep,both_featureType_update)
        if outputs_ep or new_outputTimestep:
            self.updateTemplatesOutputs('energy_plant',outputs_ep,new_outputTimestep,both_featureType_update)
            
    def updateTemplatesOutputs(self,feature,outputs,new_outputTimestep,both_featureType_update):           
        dir = self.config['pathProjects']+self.config['projectName']+"\\"+feature+"_templates\\"
                   
        t_names=getTemplateNames(self.cur,feature,seperator='_')
        for counter,t_name in enumerate(t_names):
            try:
                #print(t_name)
                templ=t_name.split('_')[0]
                if new_outputTimestep:
                    #print('----update timestep for outputs----')
                    fname=dir+t_name+'.idm'
                    #print(fname)
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
                    #print(data_idm)        
                    writePropertyListIDMToFile(data_idm,dir+t_name,fname,self.config)
                #print('----update outputs----')

                if outputs:
                    fname=dir+t_name+'\\'+t_name+'.idm'
                    #print(fname)
                    components_idm=propertyListCompsIDM(getIDAListComponents(readFileToString(fname)))
                    data_idm=[]
                    conn_bundle_type_id=getConnBundleByTemplate(feature,templ,self.cur,self.config)
                    connValues=getConnsValues(conn_bundle_type_id,self.cur)
                    #print(connValues)
                    conn_type_seq=set([x['conn_type_seq'] for x in connValues])
                    #print(conn_type_seq)
                    flowmeters=['"'+str(conn_bundle_type_id)+'_'+str(seq)+'_Flowmeter2"' for seq in conn_type_seq]
                    #print(flowmeters)   
                    pmtmuxs={'"PMT2mux_{}_{}_{}_{}"'.format(value['conn_bundle_type_id'],value['conn_type_seq'],value['conn_type_id'],value['conn_seq']) : {'seq':seq,'conn_bundle_type_id':value['conn_bundle_type_id'],'conn_seq':value['conn_seq']} for seq in conn_type_seq for value in connValues if seq==value['conn_type_seq']}
                    #print(pmtmuxs)            
                    for comp in components_idm:
                        #print(getCompName(comp))
                        if getCompTemplate(comp) in ['|lM_H_G_L|','|lM_HC_G_L_MCTRL|','|lm_h_g_t_hx|','FLOWMETER2','PMT2\\m\\u\\x'] or getCompClass(comp) in 'OUTPUT-FILE':
                            if not isinstance(comp, list):
                                comp=[comp]
                            new_comp=[]
                            if getCompTemplate(comp) in ['|lM_H_G_L|','|lM_HC_G_L_MCTRL|','|lm_h_g_t_hx|'] and 'troom_c' in [i for i in outputs if outputs[i]]:
                                #print('---add tair output----')
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
                            if getCompTemplate(comp) in ['|lM_H_G_L|','|lM_HC_G_L_MCTRL|','|lm_h_g_t_hx|'] and 'heatbalance_c' in [i for i in outputs if outputs[i]]:
                                #print('---add heatbalance output----')
                                #print(comp)
                                new_comp=[]
                                outputs_to_set={'|PhiSolar|':'Solar','|Occupancy|':'Occupancy','|Electricity|':'Electricty','|PhiInt|':'Gains','|PhiRoomUnit|':'Heating','|PhiOut|':'Transmission','|PhiLeakage|': 'Leakage','|PhiVent|':'Ventilation'}
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
                            if getCompTemplate(comp) in ['|lM_H_G_L|','|lM_HC_G_L_MCTRL|','|lm_h_g_t_hx|'] and 'heatbalance_c' in [i for i in outputs if not outputs[i]]:
                                #print('---remove heatbalance_c output----')
                                outputs_to_del={'|PhiSolar|':'Solar','|Occupancy|':'Occupancy','|Electricity|':'Electricty','|PhiInt|':'Gains','|PhiRoomUnit|':'Heating','|PhiOut|':'Transmission','|PhiLeakage|': 'Leakage','|PhiVent|':'Ventilation'}
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
                            if getCompTemplate(comp) in ['|lM_H_G_L|','|lM_HC_G_L_MCTRL|','|lm_h_g_t_hx|'] and 'troom_c' in [i for i in outputs if not outputs[i]]:
                                #print('---remove tair output----')
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
                                #print('-------pmtmux-----')
                                #print(comp)
                                new_comp=[]
                                outputs_to_set=[]
                                outputs_to_del=[]
                                if 'p_c' in [i for i in outputs if outputs[i]] or 'p_ep' in [i for i in outputs if outputs[i]]:
                                    outputs_to_set.append('|P_var|')
                                #print(outputs_to_set)
                                if 'p_c' in [i for i in outputs if not outputs[i]] or 'p_ep' in [i for i in outputs if not outputs[i]]:
                                    outputs_to_del.append('|P_var|')
                                #print(outputs_to_del)
                                if outputs_to_set and not getCompPerName(data_idm,'"Connection type sequence_{}"'.format(pmtmuxs[getCompName(comp)]['seq'])):
                                    data_idm.append([{':C': 'OUTPUT-FILE', ':N': '"Connection type sequence_{}"'.format(pmtmuxs[getCompName(comp)]['seq']), ':T': 'OUTPUT-FILE'}])
                                if outputs_to_set or outputs_to_del:
                                    for i in comp:
                                        if getCompName(i)=='|P_var|' and '|P_var|' in outputs_to_set:
                                            #print('++++add p+++++')
                                            i[':L']='"Connection type sequence_{}"'.format(pmtmuxs[getCompName(comp)]['seq'])
                                            i[':AS']='"p_{}"'.format(pmtmuxs[getCompName(comp)]['conn_seq'])
                                            new_comp.append(i)
                                            outputs_to_set.remove('|P_var|')
                                        else:
                                            #print('***rest***')
                                            #print(getCompName(comp))
                                            if getCompName(i)=='|P_var|' and '|P_var|' in outputs_to_del:
                                                #print('del :L and :AS')
                                                new_comp.append({j:i[j] for j in i if j not in [':L',':AS']})
                                            else:
                                                new_comp.append(i)
                                    for i in outputs_to_set:
                                        new_comp.append({':C': ':VAR', ':N': i, ':L': '"Connection type sequence_{}"'.format(pmtmuxs[getCompName(comp)]['seq']),':AS':'"p_{}"'.format(pmtmuxs[getCompName(comp)]['conn_seq'])})
                                    comp=new_comp
                                
                            if getCompName(comp) in flowmeters:
                                #print('-------flow meter-----')
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
                                #print(outputs_to_set)
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
                                #print(outputs_to_del)
                                if outputs_to_set or outputs_to_del:
                                    sup_conn=[connValue['conn_seq'] for connValue in connValues if connValue['type']==1]
                                    ret_conn=[connValue['conn_seq'] for connValue in connValues if connValue['type']==2]
                                    for i in comp: 
                                        if getCompName(i)=='P' and 'P' in outputs_to_set:
                                            #print('++++add power+++++')
                                            i[':L']='"Connection type sequence_{}"'.format(conn_type_seq)
                                            i[':AS']='"power"'
                                            new_comp.append(i)
                                            outputs_to_set.remove('P')
                                        elif getCompName(i)=='FLOW_SUP' and 'FLOW_SUP' in outputs_to_set:
                                            #print('++++add flow sup+++++')
                                            i[':L']="""#S(MS-SPARSE DEFAULT-VALUE OFF DIMENSION 1 VALUE ({}))""".format(' '.join(['('+str(i[0])+ ' . '+'"Connection type sequence_{}"'.format(conn_type_seq)+')' for i in enumerate(sup_conn,1)]))
                                            i[':AS']="""#S(MS-SPARSE DEFAULT-VALUE NIL DIMENSION 1 VALUE ({}))""".format(' '.join(['('+str(i[0])+ ' . '+'"mdot_{}"'.format(i[1])+')' for i in enumerate(sup_conn,1)]))
                                            new_comp.append(i)
                                            outputs_to_set.remove('FLOW_SUP')
                                        elif getCompName(i)=='FLOW_RET' and 'FLOW_RET' in outputs_to_set:
                                            #print('++++add flow ret+++++')
                                            i[':L']="""#S(MS-SPARSE DEFAULT-VALUE OFF DIMENSION 1 VALUE ({}))""".format(' '.join(['('+str(i[0])+ ' . '+'"Connection type sequence_{}"'.format(conn_type_seq)+')' for i in enumerate(ret_conn,1)]))
                                            i[':AS']="""#S(MS-SPARSE DEFAULT-VALUE NIL DIMENSION 1 VALUE ({}))""".format(' '.join(['('+str(i[0])+ ' . '+'"mdot_{}"'.format(i[1])+')' for i in enumerate(ret_conn,1)]))
                                            new_comp.append(i)
                                            outputs_to_set.remove('FLOW_RET')
                                        elif getCompName(i)=='TSUP' and 'TSUP' in outputs_to_set:
                                            #print('++++add T sup+++++')
                                            i[':L']="""#S(MS-SPARSE DEFAULT-VALUE OFF DIMENSION 1 VALUE ({}))""".format(' '.join(['('+str(i[0])+ ' . '+'"Connection type sequence_{}"'.format(conn_type_seq)+')' for i in enumerate(sup_conn,1)]))
                                            i[':AS']="""#S(MS-SPARSE DEFAULT-VALUE NIL DIMENSION 1 VALUE ({}))""".format(' '.join(['('+str(i[0])+ ' . '+'"temp_{}"'.format(i[1])+')' for i in enumerate(sup_conn,1)]))
                                            new_comp.append(i)
                                            outputs_to_set.remove('TSUP')
                                        elif getCompName(i)=='TRET' and 'TRET' in outputs_to_set:
                                            #print('++++add T ret+++++')
                                            i[':L']="""#S(MS-SPARSE DEFAULT-VALUE OFF DIMENSION 1 VALUE ({}))""".format(' '.join(['('+str(i[0])+ ' . '+'"Connection type sequence_{}"'.format(conn_type_seq)+')' for i in enumerate(ret_conn,1)]))
                                            i[':AS']="""#S(MS-SPARSE DEFAULT-VALUE NIL DIMENSION 1 VALUE ({}))""".format(' '.join(['('+str(i[0])+ ' . '+'"temp_{}"'.format(i[1])+')' for i in enumerate(ret_conn,1)]))
                                            new_comp.append(i)
                                            outputs_to_set.remove('TRET')
                                        else:
                                            #print('***rest***')
                                            #print(getCompName(i))
                                            if getCompName(i) in outputs_to_del:
                                                #print('del :L and :AS')
                                                new_comp.append({j:i[j] for j in i if j not in [':L',':AS']})
                                            else:
                                                new_comp.append(i)
                                    for i in outputs_to_set:
                                        new_comp.append({':C': ':VAR', ':N': i, ':L': '"Connection type sequence_{}"'.format(conn_type_seq)})
                                    comp=new_comp
                            if getCompClass(comp) in 'OUTPUT-FILE':
                                if (getCompName(comp)=='"TRoom"' and 'troom_c' in [i for i in outputs if not outputs[i]] or
                                    getCompName(comp)=='"Heatbalance"' and 'heatbalance_c' in [i for i in outputs if not outputs[i]] or
                                    "Connection type sequence_" in getCompName(comp) and not [True for i in self.requestedOutputs if i in ['power_c','temp_c','p_c','mdot_c'] and self.requestedOutputs[i]]):
                                    #print('++++not outputfile++++')
                                    pass
                                else:
                                    data_idm.append(comp)
                            else:
                                data_idm.append(comp)    
                        else:
                            data_idm.append(comp)
                        writePropertyListIDMToFile(data_idm,dir+t_name,fname,self.config)
            except Exception as e:
                self.signals.error.emit(str(e))
            self.signals.progress.emit(int((45 if both_featureType_update and feature == 'energy_plant' else 0)+counter/len(t_names)*(45 if both_featureType_update and feature == 'customer' else 90)))  