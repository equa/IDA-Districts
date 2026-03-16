from .files import *
import os

def writeSensorMacroIdm(dir,name):
    """Create a sensor macro"""
    if not os.path.exists(dir+"""\\{}\\Sensor-macro.idm""".format(name)):
        data=""";IDA 5.19001 Data UTF-8
(DOCUMENT-HEADER :TYPE ICE-MACRO :D "ICE macro" :ETM 3857463573 :APP (ICE :VER 5.19001)) """
        writeToFile(data,dir,dir+"""\\{}\\Sensor-macro.idm""".format(name))  

def writeSensorMacroIdc(dir,name):
    """Create a sensor macro"""
    if not os.path.exists(dir+"""\\{}\\Sensor-macro.idc""".format(name)):
        data=""";IDA 5.19001 Form UTF-8
(DOCUMENT-HEADER :TYPE SCHEMA :PAGE-WIDTH 178 :PAGE-HEIGHT 97) 
(SELF-FRAME :AT ((352 190)) :R (342 176) :SLOT (:SELF) :DATA MACRO-OBJECT) """
        writeToFile(data,dir,dir+"""\\{}\\Sensor-macro.idc""".format(name)) 

def writeMacroClimateIdm(dictDB,cur,name,dir,plugin_dir,modellingSettings,climatedata):
    if modellingSettings['ground_model']=='Kusuda':
        groundModel="""((MODEL :N \"Kusuda\" :T |kusuda|)
 (:PAR :N |TSurfMean| :V {})
 (:PAR :N |TSurfAmpl| :V {})
 (:PAR :N |Theta| :V {})
 (:PAR :N |Rho| :V {})
 (:PAR :N |cp| :V {})
 (:PAR :N |lambda| :V {})
 (:PAR :N |Depth| :V {}))""".format(modellingSettings['kusuda_tsurfmean'],modellingSettings['kusuda_tsurfampl'],modellingSettings['kusuda_theta'],modellingSettings['kusuda_rho'],modellingSettings['kusuda_cp'],modellingSettings['kusuda_lambda'],modellingSettings['kusuda_depth'])
        groundConnection=""" (("TGround" (INSIGNALLINK 1)) ("Kusuda" TEMPLINK) 0 0 NIL)"""
    elif modellingSettings['ground_model']=='Timeseries':
        dir=plugin_dir+'\\models'+'\\'+dictDB['projectName']+'\\'+dictDB['versionName']
        id=modellingSettings['ground_timeseries']
        file_name=writeTempTimeseries(dir,id,'TGround',cur)
        groundModel="""((SOURCE-FILE :DOCUMENT-PATH "{}" :SF "{}" :N "Src-TGround" :T SOURCE-FILE :COL T)
 (:VAR :N T :T GENERIC :U || :AS 2)
 (:INT :N "TGround" :F 32 :V (T)))""".format(file_name,file_name)
        groundConnection=""" (("TGround" (INSIGNALLINK 1)) ("Src-TGround" "TGround") 0 0 NIL)"""
    elif modellingSettings['ground_model']=='Constant':
        groundModel="""((SOURCE-CONSTANT :N "TGround-Const" :T CONSTANT)
 (:PAR :N X :V {}))""".format(modellingSettings['ground_temp'])
        groundConnection=""" (("TGround" (INSIGNALLINK 1)) ("TGround-Const" LINK) 0 0 NIL)"""
    
    if modellingSettings['duct_model']=='Timeseries':
        dir=plugin_dir+'\\models'+'\\'+dictDB['projectName']+'\\'+dictDB['versionName']
        id=modellingSettings['duct_timeseries']
        file_name=writeTempTimeseries(dir,id,'TDuct',cur)
        ductModel="""((SOURCE-FILE :DOCUMENT-PATH "{}" :SF "{}" :N "Src-TDuct" :T SOURCE-FILE :COL T)
 (:VAR :N T :T GENERIC :U || :AS 2)
 (:INT :N "TDuct" :F 32 :V (T)))""".format(file_name,file_name)
        ductConnection=""" (("TDuct" (INSIGNALLINK 1)) ("Src-TDuct" "TDuct") 0 0 NIL)"""
    elif modellingSettings['duct_model']=='Constant':
        ductModel="""((SOURCE-CONSTANT :N "TDuct-Const" :T CONSTANT)
 (:PAR :N X :V {}))""".format(modellingSettings['duct_temp'])
        ductConnection=""" (("TDuct" (INSIGNALLINK 1)) ("TDuct-Const" LINK) 0 0 NIL)"""
        
    data=""";IDA 5.19001 Data UTF-8
(DOCUMENT-HEADER :TYPE ICE-MACRO :D "Climate macro" :ETM 3857463573 :APP (ICE :VER 5.19001)) 
((:EO :N \"TDuct\" :T ADDER)
 (:PAR :N N_IN :V 1)
 (:VAR :N INSIGNAL :DIM (1) :V #(7.919) :IV #S(MS-SPARSE DEFAULT-VALUE 0.0 DIMENSION 1 VALUE NIL) :B #S(MS-SPARSE DEFAULT-VALUE NIL DIMENSION 1 VALUE ((1 -1 (INSIGNALLINK 1) 0))))) 
((:EO :N \"TGround\" :T ADDER)
 (:PAR :N N_IN :V 1)
 (:VAR :N INSIGNAL :DIM (1) :V #(7.919) :IV #S(MS-SPARSE DEFAULT-VALUE 0.0 DIMENSION 1 VALUE NIL) :B #S(MS-SPARSE DEFAULT-VALUE NIL DIMENSION 1 VALUE ((1 -1 (INSIGNALLINK 1) 0))))) 
{}
{}
((SCHEDULE :N "Schedule1" :T SCHEDULE)
 (:VAR :N OUT_VAR :V 1.0)
 (:RES :N SCHEDULE-DATA :V "Shading"))
((MODEL :N "vel" :T |Sqrt|)
 (:VAR :N |u_var| :V 2.572 :B (-1 |u| 0))
 (:VAR :N |y_var| :V 1.604 :L "climate" :AS "velocity"))
((:EO :N "v_dy2" :T MULTIPLIER)
 (:VAR :N OUTSIGNAL :V 0.64)
 (:VAR :N INSIGNAL :V #(0.8 0.8) :IV #S(MS-SPARSE DEFAULT-VALUE 0.0 DIMENSION 1 VALUE NIL) :B #S(MS-SPARSE DEFAULT-VALUE NIL DIMENSION 1 VALUE ((1 :MACRO "climate_file" WINDY) (2 :MACRO "climate_file" WINDY))))
 (:VAR :N TEMP :V #(0.8 0.64) :IV #S(MS-SPARSE DEFAULT-VALUE 0.0 DIMENSION 1 VALUE NIL)))
((:EO :N "v_dx2" :T MULTIPLIER)
 (:VAR :N OUTSIGNAL :V 1.932)
 (:VAR :N INSIGNAL :V #(-1.39 -1.39) :IV #S(MS-SPARSE DEFAULT-VALUE 0.0 DIMENSION 1 VALUE NIL) :B #S(MS-SPARSE DEFAULT-VALUE NIL DIMENSION 1 VALUE ((1 :MACRO "climate_file" WINDX) (2 :MACRO "climate_file" WINDX))))
 (:VAR :N TEMP :V #(-1.39 1.932) :IV #S(MS-SPARSE DEFAULT-VALUE 0.0 DIMENSION 1 VALUE NIL)))
((:EO :N "vel2" :T ADDER)
 (:VAR :N OUTSIGNAL :V 2.572)
 (:VAR :N INSIGNAL :V #(1.932 0.64) :IV #S(MS-SPARSE DEFAULT-VALUE 0.0 DIMENSION 1 VALUE NIL) :B #S(MS-SPARSE DEFAULT-VALUE NIL DIMENSION 1 VALUE ((1 -1 (INSIGNALLINK 1) 0) (2 -1 (INSIGNALLINK 2) 0)))))""".format(
    groundModel,ductModel)
    filename=climatedata['filename'].replace('\\','\\\\')
    data+="""\n((SOURCE-FILE :DOCUMENT-PATH \"{}\" :SF \"{}\" :N \"climate_file\" :T SOURCE-FILE :COL T)
 (:VAR :N TAIR :T GENERIC :U || :S (:DEFAULT T 2) :AS 2)
 (:VAR :N RELHUM :T GENERIC :U || :S (:DEFAULT T 2) :AS 3)
 (:VAR :N WINDX :T GENERIC :U || :S (:DEFAULT T 2) :AS 4)
 (:VAR :N WINDY :T GENERIC :U || :S (:DEFAULT T 2) :AS 5)
 (:VAR :N IDIRNORM :T GENERIC :U || :S (:DEFAULT T 2) :AS 6)
 (:VAR :N IDIFFHOR :T GENERIC :U || :S (:DEFAULT T 2) :AS 7))
((:CEO :N \"climate_processor\" :T ENVIRONMENT)
 (:PAR :N LAT :V {})
 (:PAR :N LONG :V {})
 (:PAR :N LONGTIMEZONE :V {})
 (:PAR :N HEIGHT :V {})
 (:VAR :N TAIR :V -6.6 :B (:MACRO \"climate_file\" TAIR) :L \"climate\"  :AS \"Tair\")
 (:VAR :N XAIR :V 608.0 :B 608)
 (:VAR :N RELHUM :V 100.0 :B (:MACRO \"climate_file\" RELHUM))
 (:VAR :N WINDDIR :B 0.0)
 (:VAR :N WINDVELREF :V 0.0 :B 0.0)
 (:VAR :N WINDX :V -0.15 :B (:MACRO \"climate_file\" WINDX))
 (:VAR :N WINDY :V -0.15 :B (:MACRO \"climate_file\" WINDY))
 (:VAR :N IDIRNORM :B (:MACRO \"climate_file\" IDIRNORM) :L \"climate\" :AS \"directNormalRad\")
 (:VAR :N IDIFFHOR :B (:MACRO \"climate_file\" IDIFFHOR) :L \"climate\" :AS \"diffuseHorRad\")
 (:VAR :N SKYCOVER :B :IV)) 
((:EO :N \"sunAngle\" :T MULTIPLIER)
 (:VAR :N OUTSIGNAL :V -1.055)
 (:VAR :N INSIGNAL :V #(-60.47 0.01745) :IV #S(MS-SPARSE DEFAULT-VALUE 0.0 DIMENSION 1 VALUE NIL) :B #S(MS-SPARSE DEFAULT-VALUE NIL DIMENSION 1 VALUE ((1 :MACRO \"climate_processor\" ELEVSUN) (2 -1 (INSIGNALLINK 2) 0))))
 (:VAR :N TEMP :V #(-60.47 -1.055) :IV #S(MS-SPARSE DEFAULT-VALUE 0.0 DIMENSION 1 VALUE NIL)))
(SOURCE-CONSTANT :N \"minSunAngle\" :T CONSTANT)
((MODEL :N \"Max\" :T |Max|)
 (:PAR :N |nin| :V 2)
 (:VAR :N |u_var| :DIM (2) :V #(0.4929 0.0) :IV #S(MS-SPARSE DEFAULT-VALUE 0.0 DIMENSION 1 VALUE NIL) :B #S(MS-SPARSE DEFAULT-VALUE NIL DIMENSION 1 VALUE ((1 -1 (|u| 1) 0) (2 -1 (|u| 2) 0))))
 (:VAR :N |y_var| :V 0.4929)
 (:VAR :N |nextIndex| :V 2.0))
((:EO :N \"IdirToNorm\" :T MULTIPLIER)
 (:VAR :N INSIGNAL :V #(0.4929 0.0) :IV #S(MS-SPARSE DEFAULT-VALUE 0.0 DIMENSION 1 VALUE NIL) :B #S(MS-SPARSE DEFAULT-VALUE NIL DIMENSION 1 VALUE ((1 -1 (INSIGNALLINK 1) 0) (2 -1 (INSIGNALLINK 2) 0))))
 (:VAR :N TEMP :V #(0.4929 0.0) :IV #S(MS-SPARSE DEFAULT-VALUE 0.0 DIMENSION 1 VALUE NIL)))
((MODEL :N \"Cos\" :T |Cos|)
 (:VAR :N |u_var| :V -1.055 :B (-1 |u| 0))
 (:VAR :N |y_var| :V 0.4929))
((:EO :N \"Idif\" :T ADDER)
 (:PAR :N N_IN :V 1)
 (:PAR :N COEFF :DIM (1))
 (:VAR :N OUTSIGNAL :AS \"Tair\")
 (:VAR :N INSIGNAL :DIM (1) :IV #S(MS-SPARSE DEFAULT-VALUE 0.0 DIMENSION 1 VALUE NIL) :B #S(MS-SPARSE DEFAULT-VALUE NIL DIMENSION 1 VALUE ((1 :MACRO \"climate_file\" IDIFFHOR)))))
((:EO :N \"Idir\" :T ADDER)
 (:PAR :N N_IN :V 1)
 (:PAR :N COEFF :DIM (1))
 (:VAR :N OUTSIGNAL :AS \"Tair\")
 (:VAR :N INSIGNAL :DIM (1) :IV #S(MS-SPARSE DEFAULT-VALUE 0.0 DIMENSION 1 VALUE NIL) :B #S(MS-SPARSE DEFAULT-VALUE NIL DIMENSION 1 VALUE ((1 :MACRO \"climate_file\" IDIRNORM))) :L #S(MS-SPARSE DEFAULT-VALUE OFF DIMENSION 1 VALUE ((1 . \"climate\"))) :AS #S(MS-SPARSE DEFAULT-VALUE NIL DIMENSION 1 VALUE ((1 . \"IDir\")))))
((:EO :N \"ISolar\" :T ADDER)
 (:VAR :N OUTSIGNAL :L \"climate\" :AS \"ITot\")
 (:VAR :N INSIGNAL :IV #S(MS-SPARSE DEFAULT-VALUE 0.0 DIMENSION 1 VALUE NIL) :B #S(MS-SPARSE DEFAULT-VALUE NIL DIMENSION 1 VALUE ((1 -1 (INSIGNALLINK 1) 0) (2 -1 (INSIGNALLINK 2) 0))) :L #S(MS-SPARSE DEFAULT-VALUE OFF DIMENSION 1 VALUE ((1 . \"climate\") (2 . \"climate\"))) :AS #S(MS-SPARSE DEFAULT-VALUE NIL DIMENSION 1 VALUE ((1 . \"IDiff\") (2 . \"IDir_vert\")))))
((SOURCE-CONSTANT :N \"convertDegreeRad\" :T CONSTANT)
 (:PAR :N X :V 0.017453293))
""".format(filename,filename,climatedata['latitude'],climatedata['longitude'],str(int(climatedata['timezone'])*15),climatedata['height'])
    data+="""(CONNECTIONS
{}
{}
 (("sunAngle" (INSIGNALLINK 2)) ("convertDegreeRad" LINK) 0 0 NIL)
 (("Max" (|u| 2)) ("minSunAngle" LINK) 0 0 NIL)
 (("Max" (|u| 1)) ("Cos" |y|) 0 0 NIL)
 (("IdirToNorm" (INSIGNALLINK 3)) ("Schedule1" OUTSIGNALLINK) 0 0 NIL)
 (("IdirToNorm" (INSIGNALLINK 2)) ("Max" |y|) 0 0 NIL)
 (("IdirToNorm" (INSIGNALLINK 1)) ("Idir" OUTSIGNALLINK) 0 0 NIL)
 (("Cos" |u|) ("sunAngle" OUTSIGNALLINK) 0 0 NIL)
 (("ISolar" (INSIGNALLINK 2)) ("IdirToNorm" OUTSIGNALLINK) 0 0 NIL)
 (("ISolar" (INSIGNALLINK 1)) ("Idif" OUTSIGNALLINK) 0 0 NIL)
 (("vel2" (INSIGNALLINK 2)) ("v_dy2" OUTSIGNALLINK) 0 0 NIL)
 (("vel2" (INSIGNALLINK 1)) ("v_dx2" OUTSIGNALLINK) 0 0 NIL)
 (("vel" |u|) ("vel2" OUTSIGNALLINK) 0 0 NIL))  """.format(groundConnection,ductConnection)
    writeToFile(data,dir,dir+"""\\{}\\Climate-macro.idm""".format(name))  

def writeMacroClimateIdc(name,dir,modellingSettings):
    if modellingSettings['ground_model']=='Kusuda':
        groundModel="""(EQUATION-FRAME :AT ((231 46)) :R (18.5 20.0) :ICON "sys:eo.ids" :SLOT ("Kusuda") :NAME "Kusuda" :DATA MODEL) 
(CONNECTION-LINE :AT ((1294/5 228/5) (1248/5 228/5)) :FIRST-LINK ("TGround" (0 0.49) (INSIGNALLINK 1)) :LAST-LINK ("Kusuda" (1.0 0.49) TEMPLINK) :DIR :LEFT :ARROW (4864 8 8)) """.format()
    elif modellingSettings['ground_model']=='Timeseries':
        groundModel="""(CONNECTION-LINE :AT ((243 46) (258 46)) :FIRST-LINK ("Src-TGround" (1.0 0.45) "TGround") :LAST-LINK ("TGround" (0 0.469) (INSIGNALLINK 1)) :DIR :RIGHT :ARROW (19 8 8)) 
(EQUATION-FRAME :AT ((223 46)) :R (20 20) :ICON "sys:source-file.ids" :SYMMETRY (90.0) :SLOT ("Src-TGround") :NAME "Src-TGround" :DATA SOURCE-FILE) """.format()
    elif modellingSettings['ground_model']=='Constant':
        groundModel="""(CONNECTION-LINE :AT ((243 46)(259 46)) :FIRST-LINK ("TGround-Const" (1 0.5) LINK) :LAST-LINK ("TGround" (0 0.479) (INSIGNALLINK 1)) :DIR :RIGHT :ARROW (19 8 8)) 
(EQUATION-FRAME :AT ((221.2 46)) :R (18.2 10) :ICON "sys:constant.ids" :SLOT ("TGround-Const") :NAME "TGround-Const" :DATA SOURCE-CONSTANT) """.format()

    if modellingSettings['duct_model']=='Timeseries':
        ductModel="""(EQUATION-FRAME :AT ((353 46)) :R (20 20) :ICON "sys:source-file.ids" :SYMMETRY (90.0) :SLOT ("Src-TDuct") :NAME "Src-TDuct" :DATA SOURCE-FILE)
(CONNECTION-LINE :AT ((373 46) (387 46)) :FIRST-LINK ("Src-TDuct" (1.0 0.45) "TDuct") :LAST-LINK ("TDuct" (0 0.479) (INSIGNALLINK 1)) :DIR :RIGHT :ARROW (19 8 8)) """.format()
    elif modellingSettings['duct_model']=='Constant':
        ductModel="""(CONNECTION-LINE :AT ((1882/5 46) (1934/5 46)) :FIRST-LINK ("TDuct-Const" (1 0.5) LINK) :LAST-LINK ("TDuct" (0 0.491) (INSIGNALLINK 1)) :DIR :RIGHT :ARROW (19 8 8)) 
(EQUATION-FRAME :AT ((348.6 46)) :R (18.2 10) :ICON "sys:constant.ids" :SLOT ("TDuct-Const") :NAME "TDuct-Const" :DATA SOURCE-CONSTANT) """.format()
        
    data=""";IDA 5.19001 Form UTF-8
(DOCUMENT-HEADER :TYPE SCHEMA :PAGE-WIDTH 178 :PAGE-HEIGHT 97) 
{}
{}
(EQUATION-FRAME :AT ((404 46)) :R (16 16) :ICON "lib:adder.ids" :SLOT ("TDuct") :NAME "TDuct" :PADDING 3 :DATA :EO) 
(EQUATION-FRAME :AT ((276 46)) :R (16 20) :ICON "lib:adder.ids" :SLOT ("TGround") :NAME "TGround" :PADDING 3 :DATA :EO) 
(CONNECTION-LINE :AT ((177 130) (202 130) (202 110)) :FIRST-LINK ("IdirToNorm" (1.0 0.531) OUTSIGNALLINK) :LAST-LINK ("ISolar" (0.094 1.0) (INSIGNALLINK 2)) :DIR :RIGHT :ARROW (19 8 8)) 
(CONNECTION-LINE :AT ((193 176) (203 176) (203 154) (158 154) (158 145)) :FIRST-LINK ("Max" (1.0 0.5) |y|) :LAST-LINK ("IdirToNorm" (0.406 1.0) (INSIGNALLINK 2)) :DIR :RIGHT :ARROW (19 8 8)) 
(CONNECTION-LINE :AT ((127 130) (135 130) (135 128) (144 128)) :FIRST-LINK ("Idir" (1.0 0.531) OUTSIGNALLINK) :LAST-LINK ("IdirToNorm" (0 0.469) (INSIGNALLINK 1)) :DIR :RIGHT :ARROW (19 8 8)) 
(CONNECTION-LINE :AT ((127 94) (151 94) (198 94)) :FIRST-LINK ("Idif" (1.0 0.5) OUTSIGNALLINK) :LAST-LINK ("ISolar" (0 0.5) (INSIGNALLINK 1)) :DIR :RIGHT :ARROW (19 8 8)) 
(CONNECTION-LINE :AT ((139 175) (155 175) (155 176) (160 176)) :FIRST-LINK ("Cos" (1 0.5) |y|) :LAST-LINK ("Max" (0 0.5) (|u| 1)) :DIR :RIGHT :ARROW (19 8 8)) 
(CONNECTION-LINE :AT ((101 178) (110 178) (110 175) (118 175)) :FIRST-LINK ("sunAngle" (1.0 0.5) OUTSIGNALLINK) :LAST-LINK ("Cos" (0 0.5) |u|) :DIR :RIGHT :ARROW (19 8 8)) 
(CONNECTION-LINE :AT ((69 216) (74 216) (74 194)) :FIRST-LINK ("convertDegreeRad" (1 0.5) LINK) :LAST-LINK ("sunAngle" (0.156 1.0) (INSIGNALLINK 2)) :DIR :RIGHT :ARROW (19 8 8)) 
(CONNECTION-LINE :AT ((165 216) (168 216) (168 192)) :FIRST-LINK ("minSunAngle" (1 0.5) LINK) :LAST-LINK ("Max" (0.219 1.0) (|u| 2)) :DIR :RIGHT :ARROW (19 8 8)) 
(CONNECTION-LINE :AT ((62 261) (69 261) (69 259) (76 259)) :FIRST-LINK ("v_dx2" (1 0.531) OUTSIGNALLINK) :LAST-LINK ("vel2" (0 0.469) (INSIGNALLINK 1)) :DIR :RIGHT :ARROW (19 8 8)) 
(CONNECTION-LINE :AT ((61 303) (68 303) (68 259) (76 259)) :FIRST-LINK ("v_dy2" (1.0 0.531) OUTSIGNALLINK) :LAST-LINK ("vel2" (0 0.469) (INSIGNALLINK 2)) :DIR :RIGHT :ARROW (19 8 8)) 
(CONNECTION-LINE :AT ((110 261) (119 261) (119 262) (128 262)) :FIRST-LINK ("vel2" (1 0.531) OUTSIGNALLINK) :LAST-LINK ("vel" (0 0.5) |u|) :DIR :RIGHT :ARROW (19 8 8)) 
(CONNECTION-LINE :AT ((229 217) (239 217) (239 147) (162 147) (162 145)) :FIRST-LINK ("Schedule1" (1.0 0.531) OUTSIGNALLINK) :LAST-LINK ("IdirToNorm" (0.406 1.0) (INSIGNALLINK 3)) :DIR :RIGHT :ARROW (19 8 8)) 
(EQUATION-FRAME :AT ((89 178)) :R (16 16) :ICON "lib:multiplier.ids" :SLOT ("sunAngle") :NAME "sunAngle" :PADDING 3 :DATA :EO) 
(EQUATION-FRAME :AT ((141 216)) :R (23.875 10) :ICON "sys:constant.ids" :SLOT ("minSunAngle") :NAME "minSunAngle" :DATA SOURCE-CONSTANT) 
(EQUATION-FRAME :AT ((181 176)) :R (16 16.0) :ICON "lib:max.ids" :SLOT ("Max") :NAME "Max" :DATA MODEL) 
(EQUATION-FRAME :AT ((165 129)) :R (16 16) :ICON "lib:multiplier.ids" :SLOT ("IdirToNorm") :NAME "IdirToNorm" :PADDING 3 :DATA :EO) 
(EQUATION-FRAME :AT ((133 175)) :R (16 19) :ICON "lib:cos.ids" :SLOT ("Cos") :NAME "Cos" :DATA MODEL) 
(EQUATION-FRAME :AT ((115 94)) :R (16 16) :ICON "lib:adder.ids" :SLOT ("Idif") :NAME "Idif" :PADDING 3 :DATA :EO) 
(EQUATION-FRAME :AT ((115 129)) :R (16 16) :ICON "lib:adder.ids" :SLOT ("Idir") :NAME "Idir" :PADDING 3 :DATA :EO) 
(EQUATION-FRAME :AT ((219 94)) :R (16 16) :ICON "lib:adder.ids" :SLOT ("ISolar") :NAME "ISolar" :PADDING 3 :DATA :EO) 
(EQUATION-FRAME :AT ((45 216)) :R (23.875 10) :ICON "sys:constant.ids" :SLOT ("convertDegreeRad") :NAME "convertDegreeRad" :DATA SOURCE-CONSTANT) 
(EQUATION-FRAME :AT ((41 46)) :R (15 15) :ICON "lib:climate.ids" :SLOT ("climate_processor") :NAME "climate_processor" :PADDING 3 :DATA :CEO :D "Process CLIMATE data from file; calc sun pos; send data to facade.") 
(EQUATION-FRAME :AT ((140 46)) :R (56.5 20) :ICON "sys:source-file.ids" :SLOT ("climate_file") :NAME "climate_file" :DATA SOURCE-FILE :D "SOURCE-FILE") 
(EQUATION-FRAME :AT ((93 260)) :R (16 16) :ICON "lib:adder.ids" :SLOT ("vel2") :NAME "vel2" :PADDING 3 :DATA :EO) 
(EQUATION-FRAME :AT ((45 260)) :R (16 16) :ICON "lib:multiplier.ids" :SLOT ("v_dx2") :NAME "v_dx2" :PADDING 3 :DATA :EO) 
(EQUATION-FRAME :AT ((45 302)) :R (16 16) :ICON "lib:multiplier.ids" :SLOT ("v_dy2") :NAME "v_dy2" :PADDING 3 :DATA :EO) 
(EQUATION-FRAME :AT ((157 262)) :R (24 24) :ICON "lib:sqrt.ids" :SLOT ("vel") :NAME "vel" :DATA MODEL) 
(EQUATION-FRAME :AT ((205 216)) :R (24 16) :ICON "lib:schedule.ids" :SLOT ("Schedule1") :NAME "Schedule1" :PADDING 3 :DATA SCHEDULE) 
(SELF-FRAME :AT ((352 190)) :R (342 176) :SLOT (:SELF) :DATA MACRO-OBJECT)  """.format(groundModel,ductModel)
    writeToFile(data,dir,dir+"""\\{}\\Climate-macro.idc""".format(name))  