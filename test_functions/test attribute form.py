def setupVersionForm_light():  
    """ setup form for version layers"""
    for vlayerName in ['lines','devices','junctions','customers','energy_plants','structure_boundarys','structure_junctions','structure_lines']:
        vlayer=QgsProject.instance().mapLayersByName(vlayerName)[0] 
        fields=vlayer.fields()
        fc = vlayer.editFormConfig()
        fc.clearTabs()
        fc.setLayout(QgsEditFormConfig.TabLayout)
        if vlayerName=='devices':
            attrNamesTabs= [['assetgroup','assettype','submodel'],
                            ['asl_m'],
                            [],[]]
        elif vlayerName=='junctions':
            attrNamesTabs= [['assetgroup','submodel'],
                            ['asl_m','n_connections'],
                            [],[]]
        elif vlayerName=='lines':
            attrNamesTabs= [['assetgroup','assettype','pipe_bundle_type_id','network','submodel'],
                            ['length','nominaltemperature','maximumtemperature','nominaloppressure','maximumoppressure'],
                            [],[]]
        elif vlayerName=='customers':
            attrNamesTabs= [['assetgroup','assettype','submodel'],
                            ['dhw_id','heat_e_kwh','heat_p_kw','tsup_h_deg','cool_e_kwh','cool_p_kw','tsup_c_deg','asl_m'],
                            ['sim_model',
                                [1],
                                [2,"FloorArea","U","tau","MHs","PhiRadH_nom","SolarAperture","WinIntShading","ela","ACH","TSetH","SystemStartTime","SystemOffTime","TBalance","PBand","dP0","dP0Air","N_value","KV_max","KV_small","dPNom","HBuoyancy","m0"],
                                [3,"FloorArea","U","tau","MHs","PhiRadH_nom","SolarAperture","WinIntShading","ela","ACH","TSetH","SystemStartTime","SystemOffTime","TBalance","PBand","dP0","dP0Air","N_value","KV_max","KV_small","dPNom","HBuoyancy","m0","TSetC","PhiRadC_nom"],
                                [4,"FloorArea","U","tau","MHs","PhiRadH_nom","SolarAperture","WinIntShading","ela","ACH","TSetH","SystemStartTime","SystemOffTime","TBalance","PBand","dP0","dP0Air","N_value","KV_max","KV_small","dPNom","HBuoyancy","m0","TSetC","PhiRadC_nom","N_value_C","MCoolDev"],
                                [5,"FloorArea","U","tau","MHs","PhiRadH_nom","SolarAperture","WinIntShading","ela","ACH","TSetH","SystemStartTime","SystemOffTime","TBalance","PBand","dP0","dP0Air","N_value","KV_max","KV_small","dPNom","HBuoyancy","m0","TSetC","PhiRadC_nom","N_value_C","MCoolDev","hx_eff","TSetDhw","TSupNomH","TSupNomC","TimeConst"],
                                [6,"FloorArea","U","tau","MHs","PhiRadH_nom","SolarAperture","WinIntShading","ela","ACH","TSetH","SystemStartTime","SystemOffTime","TBalance","PBand","dP0","dP0Air","N_value","KV_max","KV_small","dPNom","HBuoyancy","m0","TSetC","PhiRadC_nom","N_value_C","MCoolDev","hx_eff","TSetDhw","TSupNomH","TSupNomC","TimeConst","mNomTank","mTank"]],
#                           []]    
                            ['owner','building_nr','street','street_nr','zip','location','usage','energy_carrier','qdot_heat_kw','heat_kwh7a','full_load_hours_h7a','Tsup_max_deg','Tret_max_deg','connection','connection_since']]
        elif vlayerName=='energy_plants':
            attrNamesTabs= [['assetgroup','assettype','submodel'],
                            ['main_plant','heat_e_kwh','heat_p_kw','tsup_h_deg','cool_e_kwh','cool_p_kw','tsup_c_deg','asl_m'],
                            [],[]]
        elif vlayerName=='structure_boundarys':
            attrNamesTabs= [['assetgroup','assettype','submodel'],
                            ['f_vexp_m'],
                            [],[]]
        elif vlayerName=='structure_junctions':
            attrNamesTabs= [['assetgroup','assettype','submodel'],
                            [],
                            [],[]]
        elif vlayerName=='structure_lines':
            attrNamesTabs= [['assetgroup','assettype','submodel'],
                            [],
                            [],[]]
        for tab,attrNamesTab in zip(['General','Physical data','Simulation data','Metadata'],attrNamesTabs):
            if attrNamesTab:
                c = QgsAttributeEditorContainer(tab, fc.invisibleRootContainer())
                c.setIsGroupBox(False) # a tab
                for attrName in attrNamesTab:
                    #print (attrName)
                    if type(attrName) is list:
                        c1 = QgsAttributeEditorContainer("Modelparameter", fc.invisibleRootContainer())
                        c1.setIsGroupBox(True)
                        c1.setVisibilityExpression(QgsOptionalExpression(QgsExpression("sim_model={}".format(attrName[0]))))
                        print(len(attrName))
                        for i in range(1,len(attrName)):
                            print(i)
                            field_idx = fields.indexOf(attrName[i])
                            c1.addChildElement(QgsAttributeEditorField(attrName[i], field_idx, c1))
                        c.addChildElement(c1)
                    else:    
                        field_idx = fields.indexOf(attrName)
                        c.addChildElement(QgsAttributeEditorField(attrName, field_idx, c))
                fc.addTab(c)
        vlayer.setEditFormConfig(fc)
        
def valueRelationSimModel():
    """value relation pipe bundle types in lines"""
    config = {'AllowMulti': False,
              'AllowNull': True,
              'FilterExpression': '',
              'Key': 'id',
              'Layer': QgsProject.instance().mapLayersByName('sim_models')[0].id(),
              'NofColumns': 1,
              'OrderByValue': False,
              'UseCompleter': False,
              'Value': 'description'}
    widget_setup = QgsEditorWidgetSetup('ValueRelation',config)
    fields = QgsProject.instance().mapLayersByName('customers')[0].fields()
    field_idx = fields.indexOf('sim_model')
    QgsProject.instance().mapLayersByName('customers')[0].setEditorWidgetSetup(field_idx, widget_setup)  
    

        
setupVersionForm_light()

valueRelationSimModel()