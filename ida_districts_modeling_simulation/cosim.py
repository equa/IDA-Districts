from plugins.utility_functions.files import *
from plugins.utility_functions.db import *
from plugins.utility_functions.sensor_signals import *
from plugins.utility_functions.topology import *
import psycopg2.extras

def writeCosimMacroIdm(dictDB,cur,submodel,dir,plugin_dir,sensor_data,sensor_dec_data,mode='network'):
    """check if features are decoupled 
    --> import/export components
    --> collect pmt2 signals
    --> collect sensor signals"""
    data=[""";IDA 5.11 Data UTF-8
(DOCUMENT-HEADER :TYPE ICE-MACRO :D "ICE macro" :APP (ICE :VER 5.11)) \n"""]

    submodels=getUsedSubmodels(cur,dictDB)
    submodels.remove(str(submodel))
    print(submodels)
    
    #get feature template connections from .idc
    usedFeatureTemplates=getUsedFeatureTemplates(cur,dictDB)
    print(usedFeatureTemplates)
    usedDecoupledFeatureTemplates=getUsedDecoupledFeatureTemplates(usedFeatureTemplates,cur,dictDB,submodel,submodels)
    print(usedDecoupledFeatureTemplates)
    
    datacenter_dir=getDataCenterDir(plugin_dir)

    template_data_ex=[]
    resources=[]
    for template in usedDecoupledFeatureTemplates:
        print(template)
        #collect resources
        resource_f=datacenter_dir+'\\{}\\{}_templates\\{}_{}.idm'.format(dictDB['projectName'],template['feature'],template['template'],template['template_name'])
        file_data=readFileToList(resource_f)
        resource=getResourcesFromFileDataList(file_data)
        if resource not in resources:
            resources+=resource
            
        template_dir=datacenter_dir+'\\{}\\{}_templates\\{}_{}\\'.format(dictDB['projectName'],template['feature'],template['template'],template['template_name'])
        template_idm=template_dir+'{}_{}.idm'.format(template['template'],template['template_name'])
        template_idc=template_dir+'{}_{}.idc'.format(template['template'],template['template_name'])
        #print(template_idm)
        components_idm=propertyListCompsIDM(getIDAListComponents(readFileToString(template_idm)))
        components_idc=propertyListCompsIDC(getIDAListComponents(readFileToString(template_idc)))

           
        conns_idm=[comp[':CONNS'] for comp in components_idm if getCompClass(comp)=='CONNECTIONS'][0]
        #print(conns_idm)
        
        conns_idc=[comp for comp in components_idc if comp[':C']=='CONNECTION-LINE']
        #print(conns_idc)
        
        dec_models=getDecoupledFeatureCompPerTemplate(dictDB,cur,template['template'])
        pmtmux_names=[getPMT2muxName(cur,i['conn_bundle_type_id'],i['conn_id']) for i in getConnsValuesByTemplate(template['feature'],template['template'],cur,dictDB)]
        dec_models.extend(pmtmux_names)
        dec_models.extend([i.split('PMT2mux_')[1] for i in pmtmux_names])
        for emeter in [getMeterName(cur,i['conn_bundle_type_id'],i['conn_type_id']) for i in getConnsValuesByTemplate(template['feature'],template['template'],cur,dictDB)]:
            if emeter not in dec_models:
                dec_models.append(emeter)
        dec_models.append(':SELF')
        dec_models=['"'+i+'"' if i != ':SELF' else i for i in dec_models]
        print('++dec-models:++')
        print(dec_models)
        data_ex=getDataExTemplate(conns_idc,dec_models,components_idm,template['network_side'],sensor_dec_data,submodel,cur,dictDB)
        print(data_ex)
        
        #print(dec_conns)
        template_data_ex.append({'feature':template['feature'],'template':template['template'],'data_ex':data_ex})
        
    print('+++++++++++++++++--finished---+++++++++++++++++++++')
    print(template_data_ex)


    for cosim in submodels:
        f_ids=getFeatureDecIds(dictDB,cur,submodel,[cosim])
        print(f_ids)
        if [True for f_id in f_ids if str(submodel)==str(f_id['submodel']) and str(cosim)==str(f_id['cosim']) or str(submodel)==str(f_id['cosim']) and str(f_id['submodel'])==str(cosim)]:
            print(template_data_ex)
            print('-*-*')
            importVars=getImportVars(f_ids,template_data_ex,sensor_dec_data)
            print('------importVars-----')
            print(importVars)
            exportVars=getExportVars(f_ids,template_data_ex,sensor_dec_data,mode)
            print('------exportVars-----')
            print(exportVars)
            
            cosimNetworkSideImportSignals=getCosimImportSourceSignals(sensor_dec_data,submodel,cur,dictDB,cosim)
            print('------cosimNetworkSideImportSignals-----')
            print(cosimNetworkSideImportSignals)
            cosimNetworkSideExportSignals=getCosimExportSignals(sensor_dec_data,submodel,len(exportVars),cosim,str(getSupervisorySubmodel(cur,dictDB)['submodel']))
            print('------cosimNetworkSideExportSignals-----')
            print(cosimNetworkSideExportSignals)
                        
            #cosimExportTargetSignals=getCosimExportTargetSignals(sensor_dec_data,submodel,len(exportVars),cosim)

            submodel_ids=[int(submodel),int(cosim)]
            submodel_ids.sort(reverse=True if int(submodel)>int(cosim) else False)

            import_counter=len(importVars+cosimNetworkSideImportSignals)
            data.append("""((MODEL :N "{}<--{}" :T |Import|)
 (:PAR :N |data_1dim| :V {})
 (:PAR :N |channel| :V "{}")
 (:PAR :N |extrapolationLimit| :V 7200)
 (:PAR :N |order| :DIM ({}) :V #({}))
 (:PAR :N |vars| :DIM ({}))
 (:PAR :N |deadBand| :V 0)
 (:VAR :N |data_var| :DIM ({}) :L "{}<--{}_data"))\n""".format(
                submodel,cosim,import_counter,'-'.join([str(i) for i in submodel_ids]),import_counter, " ".join(['0' for i in range(import_counter)]),
                import_counter,import_counter,submodel,cosim))

            submodel_ids.sort(reverse=True if int(submodel)<int(cosim) else False)    
            data.append("""((MODEL :N "{}-->{}" :T |Export|)
 (:PAR :N |data_1dim| :V {})
 (:PAR :N |channel| :V "{}")
 (:VAR :N |data_var| :DIM ({}) :B #S(MS-SPARSE DEFAULT-VALUE NIL DIMENSION 1 VALUE ({})){})
 (:PAR :N |extrapolationLimit| :V 7200)
 (:PAR :N |order| :DIM ({}) :V #({}))
 (:PAR :N |vars| :DIM ({}))
 (:PAR :N |deadBand| :V 0))\n""".format(submodel,cosim,len(exportVars+cosimNetworkSideExportSignals),'-'.join([str(i) for i in submodel_ids]),len(exportVars+cosimNetworkSideExportSignals), 
                   ' '.join([var for var in exportVars+cosimNetworkSideExportSignals]),
                            """ :L "{}-->{}_data\"""".format(submodel,cosim),
                            len(exportVars+cosimNetworkSideExportSignals)," ".join(['0' for i in range(len(exportVars+cosimNetworkSideExportSignals))]),len(exportVars+cosimNetworkSideExportSignals)))


            data.append("""(OUTPUT-FILE :N "{}<--{}_data" :T OUTPUT-FILE :COL T :STM 1)
(OUTPUT-FILE :N "{}-->{}_data" :T OUTPUT-FILE :COL T :STM 1)\n""".format(submodel,cosim,submodel,cosim))
    

    file=dir+"\\{}_{}\\{}Co-simulation-macro.idm".format(mode,submodel,("" if mode=='network' else "plant\\"))
    writeToFileFromList(data,dir+"\\{}_{}\\{}".format(mode,submodel,("" if mode=='network' else "plant\\")),file)
    return '\n'.join(resources)
    
def writeCosimMacroIdc(dictDB,cur,submodel,dir,plugin_dir,mode='network'):
    data=[""";IDA 5.11 Form UTF-8
(DOCUMENT-HEADER :TYPE SCHEMA :PAGE-WIDTH 178 :PAGE-HEIGHT 97) 
(SELF-FRAME :AT ((352 190)) :R (342 176) :SLOT (:SELF) :DATA MACRO-OBJECT) \n"""]

    submodels=getUsedSubmodels(cur,dictDB)
    submodels.remove(str(submodel))
    f_ids=getFeatureDecIds(dictDB,cur,submodel,submodels)

    y=51
    i=0
    for cosim in submodels:
        if [True for f_id in f_ids if submodel==str(f_id['submodel']) and cosim==f_id['cosim'] or submodel==f_id['cosim'] and str(f_id['submodel'])==cosim]:
            y+=i*50
            data.append("""(EQUATION-FRAME :AT ((131 {})) :R (24 24) :ICON "sys:eo.ids" :SLOT ("{}-->{}") :NAME "{}-->{}" :DATA MODEL) \n""".format(y,submodel,cosim,submodel,cosim)) 
            data.append("""(EQUATION-FRAME :AT ((61 {})) :R (24 24) :ICON "sys:eo.ids" :SLOT ("{}<--{}") :NAME "{}<--{}" :DATA MODEL) \n""".format(y,submodel,cosim,submodel,cosim))
            data.append("""(EQUATION-FRAME :AT ((201 {})) :R (24 24) :ICON "sys:eo.ids" :SLOT ("{}-->{}_data") :NAME "{}-->{}_data" :DATA OUTPUT-FILE) \n""".format(y,submodel,cosim,submodel,cosim))
            data.append("""(EQUATION-FRAME :AT ((271 {})) :R (24 24) :ICON "sys:eo.ids" :SLOT ("{}<--{}_data") :NAME "{}<--{}_data" :DATA OUTPUT-FILE) \n""".format(y,submodel,cosim,submodel,cosim))
            i+=1
    
    file=dir+"\\{}_{}\\{}Co-simulation-macro.idc".format(mode,submodel,("" if mode=='network' else "plant\\"))
    writeToFileFromList(data,dir+"\\{}_{}\\{}".format(mode,submodel,("" if mode=='network' else "plant\\")),file)
    
