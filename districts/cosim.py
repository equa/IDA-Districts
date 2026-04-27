from .utility_functions.utility import *
from .utility_functions.files import *
from .utility_functions.db import *
from .utility_functions.sensor_signals import *
from .utility_functions.topology import *

import psycopg2.extras

def writeCosimMacroIdm(config,cur,submodel,dir,sensor_data,sensor_dec_data,mode='network'):
    """check if features are decoupled 
    --> import/export components
    --> collect pmt2 signals
    --> collect sensor signals"""
    data=[""";IDA {} Data UTF-8
(DOCUMENT-HEADER :TYPE DISTRICTS-MACRO :D "Districts macro" :APP (DISTRICTS :VER 0.9)) \n""".format(getIDAVersion(config))]

    submodels=getUsedSubmodels(cur,config)
    submodels.remove(str(submodel))
    #print(submodels)
    
    #get feature template connections from .idc
    usedFeatureTemplates=getUsedFeatureTemplates(cur,config)
    #print(usedFeatureTemplates)
    usedDecoupledFeatureTemplates=getUsedDecoupledFeatureTemplates(usedFeatureTemplates,cur,config,submodel,submodels)
    #print(usedDecoupledFeatureTemplates)
    

    template_data_ex=[]
    resources=[]
    for template in usedDecoupledFeatureTemplates:
        #print(template)
        #collect resources
        resource_f=config['pathProjects']+'{}\\{}_templates\\{}_{}.idm'.format(config['projectName'],template['feature'],template['template'],template['template_name'])
        file_data=readFileToList(resource_f)
        resource=getResourcesFromFileDataList(file_data)
        if resource not in resources:
            resources+=resource
            
        template_dir=config['pathProjects']+'{}\\{}_templates\\{}_{}\\'.format(config['projectName'],template['feature'],template['template'],template['template_name'])
        template_idm=template_dir+'{}_{}.idm'.format(template['template'],template['template_name'])
        template_idc=template_dir+'{}_{}.idc'.format(template['template'],template['template_name'])
        #print(template_idm)
        components_idm=propertyListCompsIDM(getIDAListComponents(readFileToString(template_idm)))
        components_idc=propertyListCompsIDC(getIDAListComponents(readFileToString(template_idc)))

           
        conns_idm=[comp[':CONNS'] for comp in components_idm if getCompClass(comp)=='CONNECTIONS'][0]
        #print(conns_idm)
        
        conns_idc=[comp for comp in components_idc if comp[':C']=='CONNECTION-LINE']
        #print(conns_idc)
        
        dec_models=getDecoupledFeatureCompPerTemplate(config,cur,template['template'])
        pmtmux_names=[getPMT2muxName(cur,i['conn_bundle_type_id'],i['conn_id']) for i in getConnsValuesByTemplate(template['feature'],template['template'],cur,config)]
        dec_models.extend(pmtmux_names)
        dec_models.extend([i.split('PMT2mux_')[1] for i in pmtmux_names])
        for emeter in [getMeterName(cur,i['conn_bundle_type_id'],i['conn_type_id']) for i in getConnsValuesByTemplate(template['feature'],template['template'],cur,config)]:
            if emeter not in dec_models:
                dec_models.append(emeter)
        dec_models.append(':SELF')
        dec_models=['"'+i+'"' if i != ':SELF' else i for i in dec_models]
        #print('++dec-models:++')
        #print(dec_models)
        data_ex=getDataExTemplate(conns_idc,dec_models,components_idm,template['network_side'],sensor_dec_data,submodel,cur,config)
        #print(data_ex)
        
        #print(dec_conns)
        template_data_ex.append({'feature':template['feature'],'template':template['template'],'data_ex':data_ex})
        
    #print('+++++++++++++++++--finished---+++++++++++++++++++++')
    #print(template_data_ex)


    for cosim in submodels:
        f_ids=getFeatureDecIds(config,cur,submodel,[cosim])
        #print(f_ids)
        if [True for f_id in f_ids if str(submodel)==str(f_id['submodel']) and str(cosim)==str(f_id['cosim']) or str(submodel)==str(f_id['cosim']) and str(f_id['submodel'])==str(cosim)]:
            #print(template_data_ex)
            #print('-*-*')
            importVars=getImportVars(f_ids,template_data_ex,sensor_dec_data)
            #print('------importVars-----')
            #print(importVars)
            exportVars=getExportVars(f_ids,template_data_ex,sensor_dec_data,mode)
            #print('------exportVars-----')
            #print(exportVars)
            
            cosimNetworkSideImportSignals=getCosimImportSourceSignals(sensor_dec_data,submodel,cur,config,cosim)
            #print('------cosimNetworkSideImportSignals-----')
            #print(cosimNetworkSideImportSignals)
            cosimNetworkSideExportSignals=getCosimExportSignals(sensor_dec_data,submodel,len(exportVars),cosim,str(getSupervisorySubmodel(cur,config)['submodel']))
            #print('------cosimNetworkSideExportSignals-----')
            #print(cosimNetworkSideExportSignals)
                        
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
    
def writeCosimMacroIdc(config,cur,submodel,dir,mode='network'):
    data=[""";IDA {} Form UTF-8
(DOCUMENT-HEADER :TYPE SCHEMA :PAGE-WIDTH 178 :PAGE-HEIGHT 97) 
(SELF-FRAME :AT ((352 190)) :R (342 176) :SLOT (:SELF) :DATA MACRO-OBJECT) \n""".format(getIDAVersion(config))]

    submodels=getUsedSubmodels(cur,config)
    submodels.remove(str(submodel))
    f_ids=getFeatureDecIds(config,cur,submodel,submodels)

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
    
