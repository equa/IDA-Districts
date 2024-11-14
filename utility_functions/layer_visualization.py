from plugins.utility_functions.files import *
from qgis.core import  QgsExpression, QgsOptionalExpression,QgsAttributeEditorField,QgsAttributeEditorContainer, QgsEditFormConfig, QgsProject, QgsSvgMarkerSymbolLayer, QgsEditorWidgetSetup, QgsVectorLayer, QgsSymbol, QgsRendererCategory, QgsCategorizedSymbolRenderer
    
def getDHCLayerNames():
    return ["lines","junctions","energy_plants","devices","structure_lines","structure_junctions","structure_boundarys"]
    
def updateTableSrid(versions,cur,srid):
    """Updates the srid of geometry tables in each version"""
    sql="""SELECT UpdateGeometrySRID('%schema%', '%table%', 'geom', {});""".format(srid)
    print('+--+')
    for version in versions:
        sql_version=sql.replace("%schema%",version)
        #version tables
        for table in ['devices','lines','junctions','customers','energy_plants','structure_boundarys','structure_junctions','structure_lines','buildings','streets','submodels']:
            print(sql_version.replace("%table%",table))
            cur.execute(sql_version.replace("%table%",table))
            
    print('++')
    sql_temp=sql.replace("%schema%","temp")        
    #temp tables 
    print('++')
    print(sql_temp)
    for table in ['lines','lines_cooling','lines_heating','junctions','customers','streets_help']:
        print(sql_temp.replace("%table%",table))
        cur.execute(sql_temp.replace("%table%",table))

def valueRelationPipeBundleType():
    """value relation pipe bundle types in lines"""
    config = {'AllowMulti': False,
              'AllowNull': True,
              'FilterExpression': '',
              'Key': 'id',
              'Layer': QgsProject.instance().mapLayersByName('pipe_bundle_types')[0].id(),
              'NofColumns': 1,
              'OrderByValue': False,
              'UseCompleter': False,
              'Value': 'description'}
    widget_setup = QgsEditorWidgetSetup('ValueRelation',config)
    fields = QgsProject.instance().mapLayersByName('lines')[0].fields()
    field_idx = fields.indexOf('pipe_bundle_type_id')
    QgsProject.instance().mapLayersByName('lines')[0].setEditorWidgetSetup(field_idx, widget_setup)   

def valueRelationDhwId():
    """value relation DHW ID in table dhw_timeseries"""
    config = {'AllowMulti': False,
              'AllowNull': True,
              'FilterExpression': '',
              'Key': 'id',
              'Layer': QgsProject.instance().mapLayersByName('dhw_timeseries')[0].id(),
              'NofColumns': 1,
              'OrderByValue': False,
              'UseCompleter': False,
              'Value': 'description'}
    widget_setup = QgsEditorWidgetSetup('ValueRelation',config)
    fields = QgsProject.instance().mapLayersByName('customers')[0].fields()
    field_idx = fields.indexOf('dhw_id')
    QgsProject.instance().mapLayersByName('customers')[0].setEditorWidgetSetup(field_idx, widget_setup)  

def valueRelationInternalLoadId():
    """value relation internal load ID in table internal_loads_profiles"""
    config = {'AllowMulti': False,
              'AllowNull': True,
              'FilterExpression': '',
              'Key': 'id',
              'Layer': QgsProject.instance().mapLayersByName('internal_loads_profiles')[0].id(),
              'NofColumns': 1,
              'OrderByValue': False,
              'UseCompleter': False,
              'Value': 'description'}
    widget_setup = QgsEditorWidgetSetup('ValueRelation',config)
    fields = QgsProject.instance().mapLayersByName('customers')[0].fields()
    field_idx = fields.indexOf('internal_load_id')
    QgsProject.instance().mapLayersByName('customers')[0].setEditorWidgetSetup(field_idx, widget_setup)  
 
def setupVersionForm(cur,dictDB):  
    """ setup form for version layers"""
    for vlayerName in ['lines','devices','junctions','customers','energy_plants','structure_boundarys','structure_junctions','structure_lines']:
        vlayer=QgsProject.instance().mapLayersByName(vlayerName)[0] 
        fields=vlayer.fields()
        fc = vlayer.editFormConfig()
        fc.clearTabs()
        fc.setLayout(QgsEditFormConfig.TabLayout)
        if vlayerName=='devices':
            attrNamesTabs= [['assetgroup','assettype'],
                            ['asl_m'],
                            ['submodel'],[]]
        elif vlayerName=='junctions':
            attrNamesTabs= [['assetgroup'],
                            ['asl_m','n_connections','zeta'],
                            ['submodel'],[]]
        elif vlayerName=='lines':
            attrNamesTabs= [['id','assetgroup','assettype','pipe_bundle_type_id','network'],
                            ['length','nominaltemperature','maximumtemperature','nominaloppressure','maximumoppressure','zeta','no_customer','peak_power_kw'],
                            ['submodel'],[]]
        elif vlayerName=='customers':
            attrNamesTabs= [['id','assetgroup','assettype','network'],
                            ['heat_e_kwh','heat_p_kw','tsup_h_deg','cool_e_kwh','cool_p_kw','tsup_c_deg','asl_m'],
                            ['dhw_id', 'dhw_scale','internal_load_id','submodel'],
                            ['owner','building_nr','street','street_nr','zip','location','usage','energy_carrier','qdot_heat_kw','heat_kwh7a','full_load_hours_h7a','Tsup_max_deg','Tret_max_deg','connection','connection_since']]
        elif vlayerName=='energy_plants':
            attrNamesTabs= [['id','assetgroup','assettype','network'],
                            ['main_plant','heat_e_kwh','heat_p_kw','tsup_h_deg','cool_e_kwh','cool_p_kw','tsup_c_deg','asl_m'],
                            ['submodel'],[]]
        elif vlayerName=='structure_boundarys':
            attrNamesTabs= [['assetgroup','assettype'],
                            ['f_vexp_m'],
                            ['submodel'],[]]
        elif vlayerName=='structure_junctions':
            attrNamesTabs= [['assetgroup','assettype'],
                            [],
                            ['submodel'],[]]
        elif vlayerName=='structure_lines':
            attrNamesTabs= [['assetgroup','assettype'],
                            [],
                            ['submodel'],[]]
        for tab, attrNamesTab in zip(['General', 'Physical data', 'Simulation data', 'Metadata'], attrNamesTabs):
            if attrNamesTab:
                c = QgsAttributeEditorContainer(tab, fc.invisibleRootContainer())
                # Instead of setIsGroupBox, we directly use the container for tabs
                for attrName in attrNamesTab:
                    if isinstance(attrName, list):
                        c1 = QgsAttributeEditorContainer("Modelparameter", c)  # Set parent as 'c'
                        # Adding child elements as part of a new container
                        for param_name in attrName:
                            field_idx = fields.indexOf(param_name)
                            c1.addChildElement(QgsAttributeEditorField(param_name, field_idx, c1))
                        c.addChildElement(c1)  # Add the container to the tab
                    else:
                        field_idx = fields.indexOf(attrName)
                        c.addChildElement(QgsAttributeEditorField(attrName, field_idx, c))
                fc.addTab(c)  # Add the tab to the form configuration
        
        vlayer.setEditFormConfig(fc)
            
def versionLayersAliasNames():
    """ alias names for version layers"""
    for vlayerName in ['lines','devices','customers','energy_plants','junctions']:
        vlayer=QgsProject.instance().mapLayersByName(vlayerName)[0] 
        fields=vlayer.fields()
        if vlayerName=='devices':
            attrNames=['assetgroup','assettype','submodel','asl_m']
            aliasNames=['Asset group','Asset type','Network','Co-sim','Above sea level, m']
        elif vlayerName=='lines':
            attrNames=['assetgroup','assettype','pipe_bundle_type_id','network','submodel','length']
            aliasNames=['Asset group','Asset type','Pipe bundle type','Network','Co-sim','Length, m']
        elif vlayerName=='customers':
            attrNames=['assetgroup','assettype','submodel','dhw_id','heat_e_kwh','heat_p_kw','tsup_h_deg','cool_e_kwh','cool_p_kw','tsup_c_deg','asl_m,','dhw_scale','internal_load_id']
            aliasNames=['Asset group','Asset type','Co-sim','Domestic hot water ID','Heating demand, kWh','Heating load, kW','Supply setpoint temp. heating, °C','Cooling demand, kWh','Cooling load, kW','Supply setpoint temp. cooling, °C','Above sea level, m','DHW scale factor','Internal load ID']
        elif vlayerName=='energy_plants':
            attrNames=['assetgroup','assettype','submodel','main_plant','heat_e_kwh','heat_p_kw','tsup_h_deg','cool_e_kwh','cool_p_kw','tsup_c_deg','asl_m']
            aliasNames=['Asset group','Asset type','Co-sim','Is this the main plant','Heating demand, kWh','Heating load, kW','Setpoint temp. heating, °C','Cooling demand, kWh','Cooling load, kW','Setpoint temp. cooling, °C','Above sea level, m']
        elif vlayerName=='junctions':
            attrNames=['assetgroup','assettype','submodel','n_connections','asl_m']
            aliasNames=['Asset group','Asset type','Co-sim','Number of connections','Above sea level, m']
        
        for attrName,alias in zip(attrNames,aliasNames):
            field_idx = fields.indexOf(attrName)
            vlayer.setFieldAlias(field_idx,alias)                      
       
def removeLayer(layer_name):
    if QgsProject.instance().mapLayersByName(layer_name):
        layer=QgsProject.instance().mapLayersByName(layer_name)[0]
        QgsProject.instance().removeMapLayer(layer)

def removeLayers():
    layers = QgsProject.instance().mapLayers().values()
    for layer in layers:
        if layer.name() in ['internal_loads_profiles','pipe_bundle_types','dhw_timeseries','submodels','energy_plants','customers','customer_assettypes','customer_assetgroups','energy_plant_assettypes','energy_plant_assetgroups','structure_junction_assetgroups',
            'structure_junction_assettypes','structure_boundary_assetgroups','structure_boundary_assettypes','junction_assetgroups','junction_assettypes','junctions',
            'structure_line_assetgroups','structure_line_assettypes','structure_boundarys','structure_junctions','structure_lines',
            'units','streets', 'buildings','results velocity','results return temperature','results supply temperature','results pressure','results massflow','network','cosim',
            'owner','maintby','lifecyclestatus','devices','device_assettypes','device_assetgroups','lines','line_assettypes','line_assetgroups',
            'pipematerial','insulatingmaterial','installlocation','installationmethod','manufacturer',
            'spatialsource']:
            QgsProject.instance().removeMapLayer(layer)
        
def removeTempLayers():
    layers = QgsProject.instance().mapLayers().values()
    for layer in layers:
        if layer.name() in ['customers_temp','lines_temp','lines_heating_temp','lines_cooling_temp','junctions_temp']:
            QgsProject.instance().removeMapLayer(layer)

def showTempTables(uri,dictDB,plugin_dir,iface,cur):
    """Show temp tables (lines,customers,junctions)"""
    print('show temp tables')
    removeTempLayers()
    layerTreeRoot = QgsProject.instance().layerTreeRoot()  
    for layer in ['lines','junctions','customers']:
        if QgsProject.instance().mapLayersByName(layer):
            vlayer= QgsProject.instance().mapLayersByName(layer)[0]
            layerTreeRoot.findLayer(vlayer).setItemVisibilityChecked(False)
        else:
            #iface.messageBar().pushMessage("Warning", "No project tables loaded", level=Qgis.Warning)
            print("No project tables loaded")
            return False
    try:
        loadProjectLayers('temp',uri,dictDB,plugin_dir,cur)  
    except:
        print('Load project layers failed')
   
def loadTopologyLayers(version,uri,layerTreeRoot,dictDB):
    #load tables without geometry and hide them in layers panel
    model = iface.layerTreeView().layerTreeModel()
    ltv = iface.layerTreeView()
    root = QgsProject.instance().layerTreeRoot()
    for tableName in ['internal_loads_profiles','dhw_timeseries','pipe_bundle_types','customer_assettypes','customer_assetgroups','energy_plant_assettypes','energy_plant_assetgroups','structure_boundary_assetgroups','structure_junction_assetgroups','structure_junction_assettypes',
        'structure_boundary_assettypes','junction_assetgroups','structure_line_assetgroups','structure_line_assettypes',
        'line_assetgroups','line_assettypes','device_assetgroups','device_assettypes']:
        uri.setDataSource("public", tableName, "")
        vlayer = QgsVectorLayer(uri.uri(False), tableName, dictDB['user'])
        QgsProject.instance().addMapLayer(vlayer)
        node = root.findLayer( vlayer.id())
        index = model.node2index( node )
        ltv.setRowHidden( index.row(), index.parent(), True) 
            
def loadProjectLayers(version,uri,dictDB,plugin_dir,cur):
    dir=getProjectHandlingDir(plugin_dir)
    for vlayerName in ['energy_plants','customers','lines','devices','junctions','structure_boundarys','structure_junctions','structure_lines']:  
        categories=featureLayerAssetgroups(vlayerName,cur)
        ids=featureLayerAssetgroupIds(vlayerName,cur)
        if not (vlayerName in ['energy_plants','devices','structure_boundarys','structure_junctions','structure_lines'] and version=='temp'):
            uri.setDataSource(version, vlayerName, "geom")
            if version =='temp':
                vlayer = QgsVectorLayer(uri.uri(False), vlayerName+'_temp', dictDB['user'])
            else:
                vlayer = QgsVectorLayer(uri.uri(False), vlayerName, dictDB['user'])
            QgsProject.instance().addMapLayer(vlayer)  
            print(vlayerName[:-1] + '_assetgroups')
            target_layer = QgsProject.instance().mapLayersByName(vlayerName[:-1] + '_assetgroups')[0] 
            config = {'AllowMulti': False,
                      'AllowNull': True,
                      'FilterExpression': '',
                      'Key': 'id',
                      'Layer': target_layer.id(),
                      'NofColumns': 1,
                      'OrderByValue': False,
                      'UseCompleter': False,
                      'Value': 'assetgroup'}
            widget_setup = QgsEditorWidgetSetup('ValueRelation',config)
            fields=vlayer.fields()
            field_idx = fields.indexOf('assetgroup')
            vlayer.setEditorWidgetSetup(field_idx, widget_setup)   
            if vlayerName!='junctions':     
                target_layer = QgsProject.instance().mapLayersByName(vlayerName[:-1] + '_assettypes')[0]             
                config['Layer'] = target_layer.id()
                config['Key'] = 'assettype'
                config['Value'] = 'assettype_name'
                config['FilterExpression']=""""assetgroup" = current_value('assetgroup')"""
                widget_setup = QgsEditorWidgetSetup('ValueRelation',config)
                field_idx = fields.indexOf('assettype')
                vlayer.setEditorWidgetSetup(field_idx, widget_setup)

            categorized_renderer = QgsCategorizedSymbolRenderer()            
            categorized_renderer.setClassAttribute('assetgroup') 
            for category,id in zip(categories,ids):      
                print(vlayerName)
                print(vlayer)
                symbol=QgsSymbol.defaultSymbol(vlayer.geometryType())
                if vlayerName in ['lines','structure_lines']:
                    symbol.setWidth(0.75) 
                elif vlayerName in ['structure_boundarys']:
                    #print(vlayerName)
                    pass
                else:
                    symbol.setSize(2)
                    svgStyle = {}
                    svgStyle['name'] = dir+'/icons/'+ category+'.svg'
                    svgStyle['outline'] = '#000000'
                    svgStyle['size'] = '8'
                    symbolLayer = QgsSvgMarkerSymbolLayer.create(svgStyle)
                    symbol = QgsSymbol.defaultSymbol(vlayer.geometryType()) 
                    symbol.changeSymbolLayer(0, symbolLayer)
                    
                cat = QgsRendererCategory(id, symbol, category)
                categorized_renderer.addCategory(cat)       
            vlayer.setRenderer(categorized_renderer)
   
def featureLayerAssetgroups(vlayerName,cur):
    sql="""SELECT assetgroup FROM {}_assetgroups ORDER BY id;""".format(vlayerName[:-1])
    cur.execute(sql)
    return [i['assetgroup'] for i in cur.fetchall()]
    
def featureLayerAssetgroupIds(vlayerName,cur):
    sql="""SELECT id FROM {}_assetgroups ORDER BY id;""".format(vlayerName[:-1])
    cur.execute(sql)
    return [i['id'] for i in cur.fetchall()]    
        
def loadFeatureLayer(version,dictDB,plugin_dir,vlayerName,cur):
    dir=getProjectHandlingDir(plugin_dir)
    categories=featureLayerAssetgroups(vlayerName,cur)
    ids=featureLayerAssetgroupIds(vlayerName,cur)
    
    uri = QgsDataSourceUri()
    uri.setConnection(dictDB['host'], dictDB['port'], dictDB['projectName'], None, None)
    connInfo = uri.connectionInfo()
    QgsCredentials.instance().put( connInfo, dictDB['user'], dictDB['pwd'])  
    uri.setDataSource(version, vlayerName, "geom")
 
    if version =='temp':
        vlayer = QgsVectorLayer(uri.uri(False), vlayerName+'_temp', dictDB['user'])
    else:
        vlayer = QgsVectorLayer(uri.uri(False), vlayerName, dictDB['user'])
    QgsProject.instance().addMapLayer(vlayer)  
    print(vlayerName[:-1] + '_assetgroups')
    target_layer = QgsProject.instance().mapLayersByName(vlayerName[:-1] + '_assetgroups')[0] 
    config = {'AllowMulti': False,
              'AllowNull': True,
              'FilterExpression': '',
              'Key': 'id',
              'Layer': target_layer.id(),
              'NofColumns': 1,
              'OrderByValue': False,
              'UseCompleter': False,
              'Value': 'assetgroup'}
    widget_setup = QgsEditorWidgetSetup('ValueRelation',config)
    fields=vlayer.fields()
    field_idx = fields.indexOf('assetgroup')
    vlayer.setEditorWidgetSetup(field_idx, widget_setup)   
    if vlayerName!='junctions':     
        target_layer = QgsProject.instance().mapLayersByName(vlayerName[:-1] + '_assettypes')[0]             
        config['Layer'] = target_layer.id()
        config['Key'] = 'assettype'
        config['Value'] = 'assettype_name'
        config['FilterExpression']=""""assetgroup" = current_value('assetgroup')"""
        widget_setup = QgsEditorWidgetSetup('ValueRelation',config)
        field_idx = fields.indexOf('assettype')
        vlayer.setEditorWidgetSetup(field_idx, widget_setup)

    categorized_renderer = QgsCategorizedSymbolRenderer()            
    categorized_renderer.setClassAttribute('assetgroup') 
    for category,id in zip(categories,ids):      
        print(vlayerName)
        print(vlayer)
        symbol=QgsSymbol.defaultSymbol(vlayer.geometryType())
        print(symbol)
        if vlayerName in ['lines','structure_lines']:
            symbol.setWidth(0.75) 
        else:
            symbol.setSize(2)
            svgStyle = {}
            svgStyle['name'] = dir+'/icons/'+ category+'.svg'
            svgStyle['outline'] = '#000000'
            svgStyle['size'] = '8'
            symbolLayer = QgsSvgMarkerSymbolLayer.create(svgStyle)
            symbol = QgsSymbol.defaultSymbol(vlayer.geometryType()) 
            symbol.changeSymbolLayer(0, symbolLayer)
            
        cat = QgsRendererCategory(id, symbol, category)
        categorized_renderer.addCategory(cat)       
    vlayer.setRenderer(categorized_renderer)