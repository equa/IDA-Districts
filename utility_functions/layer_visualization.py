from plugins.utility_functions.files import *
from plugins.utility_functions.db import *
from qgis.core import  QgsFieldConstraints, QgsExpression, QgsOptionalExpression,QgsAttributeEditorField,QgsAttributeEditorContainer, QgsEditFormConfig, QgsProject, QgsSvgMarkerSymbolLayer, QgsEditorWidgetSetup, QgsVectorLayer, QgsSymbol, QgsRendererCategory, QgsCategorizedSymbolRenderer

def zoomToLayer(layer_name):
    # Get the active QGIS map canvas
    canvas = iface.mapCanvas()

    # Get the layer you want to zoom to (replace with your layer name)
    layer = QgsProject.instance().mapLayersByName(layer_name)[0]

    # Get the extent of the layer
    layer_extent = layer.extent()

    # Set the canvas to zoom to the layer's extent
    canvas.setExtent(layer_extent)

    # Refresh the canvas to apply the change
    canvas.refresh()

def setEditorWidgetListType(list_type_dict):
    """{layer: [col_names]}"""
    config = {'EmptyIsEmptyArray': True, 'EmptyIsNull': False}
    editor_setup = QgsEditorWidgetSetup("List", config)

    for layer_name in list_type_dict:
        print(layer_name)
        layer=QgsProject.instance().mapLayersByName(layer_name)[0]
        for col in list_type_dict[layer_name]:
            field_index = layer.fields().indexOf(col)
            print(field_index)

            # Apply the widget setup to the field
            layer.setEditorWidgetSetup(field_index, editor_setup)

def setFieldConstraints(constraints_dict):
    """{layer: {col_names : constraint}}"""
    for layer_name in constraints_dict:
        print(layer_name)
        layer=QgsProject.instance().mapLayersByName(layer_name)
        if layer:
            layer=layer[0]
            for col in constraints_dict[layer_name]:
                field_index = layer.fields().indexOf(col)
                print(field_index)
                layer.setFieldConstraint(field_index, QgsFieldConstraints.ConstraintExpression)
                layer.setConstraintExpression(field_index, constraints_dict[layer_name][col])
            
def getDHCLayerNames():
    return ["lines","junctions","energy_plants","devices"]
    
def updateTableSrid(versions,cur,srid):
    """Updates the srid of geometry tables in each version"""
    sql="""SELECT UpdateGeometrySRID('%schema%', '%table%', 'geom', {});""".format(srid)
    print('+--+')
    for version in versions:
        sql_version=sql.replace("%schema%",version)
        #version tables
        for table in ['devices','lines','junctions','customers','energy_plants','buildings','streets','submodels','boreholes']:
            print(sql_version.replace("%table%",table))
            try:
                cur.execute(sql_version.replace("%table%",table))
            except:
                pass
            
    print('++')
    sql_temp=sql.replace("%schema%","temp")        
    #temp tables 
    print('++')
    print(sql_temp)
    for table in ['lines','lines_cooling','lines_heating','junctions','customers','streets_help']:
        print(sql_temp.replace("%table%",table))
        try:
            cur.execute(sql_temp.replace("%table%",table))
        except:
            pass

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
    for vlayerName in ['lines','devices','junctions','customers','energy_plants']:
        vlayer=QgsProject.instance().mapLayersByName(vlayerName)[0] 
        fields=vlayer.fields()
        fc = vlayer.editFormConfig()
        fc.clearTabs()
        fc.setLayout(QgsEditFormConfig.TabLayout)
        if vlayerName=='devices':
            attrNamesTabs= [['assetgroup','assettype'],
                            [],
                            ['submodel'],[]]
        elif vlayerName=='junctions':
            attrNamesTabs= [['assetgroup'],
                            ['n_connections','zeta'],
                            ['submodel'],[]]
        elif vlayerName=='lines':
            attrNamesTabs= [['id','assetgroup','assettype','pipe_bundle_type_id','network'],
                            ['length','zeta'],
                            ['submodel'],[]]
        elif vlayerName=='customers':
            attrNamesTabs= [['id','assetgroup','assettype','network'],
                            ['load_w'],
                            ['dhw_id','internal_load_id','submodel'],
                            []]
        elif vlayerName=='energy_plants':
            attrNamesTabs= [['id','assetgroup','assettype','network'],
                            ['main_plant'],
                            ['submodel'],[]]
        for tab, attrNamesTab in zip(['General', 'Physical data', 'Simulation data', 'Metadata'], attrNamesTabs):
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
            attrNames=['assetgroup','assettype','submodel']
            aliasNames=['Asset group','Asset type','Network','Co-sim']
        elif vlayerName=='lines':
            attrNames=['assetgroup','assettype','pipe_bundle_type_id','network','submodel','length']
            aliasNames=['Asset group','Asset type','Pipe bundle type','Network','Co-sim','Length, m']
        elif vlayerName=='customers':
            attrNames=['assetgroup','assettype','submodel','load_w','dhw_id','internal_load_id']
            aliasNames=['Asset group','Asset type','Co-sim','Load, W','Domestic hot water ID','Internal load ID']
        elif vlayerName=='energy_plants':
            attrNames=['assetgroup','assettype','submodel','main_plant']
            aliasNames=['Asset group','Asset type','Co-sim','Is this the main plant']
        elif vlayerName=='junctions':
            attrNames=['assetgroup','assettype','submodel','n_connections']
            aliasNames=['Asset group','Asset type','Co-sim','Number of connections']
        
        for attrName,alias in zip(attrNames,aliasNames):
            field_idx = fields.indexOf(attrName)
            vlayer.setFieldAlias(field_idx,alias)                      
       
def removeLayer(layer_name):
    if QgsProject.instance().mapLayersByName(layer_name):
        layer=QgsProject.instance().mapLayersByName(layer_name)[0]
        QgsProject.instance().removeMapLayer(layer)

def loadBoreholesLayer(version,uri,dictDB,plugin_dir,cur):
    dir=getProjectHandlingDir(plugin_dir)
    vlayerName='boreholes'
    uri.setDataSource(version, vlayerName, "geom")
    vlayer = QgsVectorLayer(uri.uri(False), vlayerName, dictDB['user'])
    QgsProject.instance().addMapLayer(vlayer)  
    target_layer = QgsProject.instance().mapLayersByName('energy_plants')[0]
    config = {'AllowMulti': False,
              'AllowNull': True,
              'FilterExpression': '',
              'Key': 'id',
              'Layer': target_layer.id(),
              'NofColumns': 1,
              'OrderByValue': False,
              'UseCompleter': False,
              'Value': 'id'}
    widget_setup = QgsEditorWidgetSetup('ValueRelation',config)
    fields=vlayer.fields()
    field_idx = fields.indexOf('plant_id')
    vlayer.setEditorWidgetSetup(field_idx, widget_setup) 
    
    form = vlayer.fields()
    field_idx = fields.indexOf('mir')

    widget_setup = QgsEditorWidgetSetup("CheckBox", {})  # Pass an empty dictionary for additional setup (optional)

    # Step 3: Set the widget for the field on the layer
    vlayer.setEditorWidgetSetup(field_idx, widget_setup)

    # Step 3: Refresh the layer and form view
    vlayer.triggerRepaint()  # Refresh the layer to apply the changes
    
def removeLayers():
    layers = QgsProject.instance().mapLayers().values()
    for layer in layers:
        if layer.name() in ['internal_loads_profiles','pipe_bundle_types','dhw_timeseries','submodels','energy_plants','customers','customer_assettypes','customer_assetgroups','energy_plant_assettypes','energy_plant_assetgroups',
            'junction_assetgroups','junction_assettypes','junctions',
            'streets', 'buildings','network','cosim',
            'devices','device_assettypes','device_assetgroups','lines','line_assettypes','line_assetgroups','boreholes','borehole_fields',
            'pipematerial','lines_results_supply_temperature','customer_results_load',
            'room_units','zone_templates','building_construction_standard']:
            QgsProject.instance().removeMapLayer(layer)
        
def removeTempLayers():
    layers = QgsProject.instance().mapLayers().values()
    for layer in layers:
        if layer.name() in ['customers_temp','lines_temp','lines_heating_temp','lines_cooling_temp','junctions_temp','energy_plants_temp']:
            QgsProject.instance().removeMapLayer(layer)

def showTempTables(uri,dictDB,plugin_dir,iface,cur):
    """Show temp tables (lines,customers,junctions,energy_plants)"""
    print('show temp tables')
    removeTempLayers()
    layerTreeRoot = QgsProject.instance().layerTreeRoot()  
    for layer in ['lines','junctions','customers','energy_plants']: #todo devices
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

def setLayersHidden(tableNames):
    for tableName in tableNames:
        layer=QgsProject.instance().mapLayersByName(tableName)
        if layer:
            layer=layer[0]
            model = iface.layerTreeView().layerTreeModel()
            ltv = iface.layerTreeView()
            root = QgsProject.instance().layerTreeRoot()
            node = root.findLayer( layer.id())
            index = model.node2index(node)
            ltv.setRowHidden( index.row(), index.parent(), True)
        
def loadTopologyLayers(version,uri,dictDB):
    #load tables without geometry and hide them in layers panel
    tableNames=['internal_loads_profiles','dhw_timeseries','pipe_bundle_types','customer_assettypes','customer_assetgroups','energy_plant_assettypes','energy_plant_assetgroups',
        'junction_assetgroups',
        'line_assetgroups','line_assettypes','device_assetgroups','device_assettypes','room_units','building_construction_standard','zone_templates']
    for tableName in tableNames:
        uri.setDataSource("public", tableName, "")
        layer = QgsVectorLayer(uri.uri(False), tableName, dictDB['user'])
        QgsProject.instance().addMapLayer(layer)
    
    setLayersHidden(tableNames) 

        
def getListTypeDict():
    return {'energy_plants':['network','main_plant'],'customers':['network'],'lines':['submodel'],'devices':['network']} 
    
def getConstraintExpressionDict(networks_array):
    return {'energy_plants': {'network': f'array_all({networks_array}, "network") AND array_length( "network" ) > 0','main_plant': f'array_all({networks_array}, "main_plant") OR array_length( "main_plant" ) =0'},
                                'customers': {'network': f'array_all({networks_array}, "network") AND array_length( "network" ) > 0'},
                                'devices': {'network': f'array_all({networks_array}, "network") AND array_length( "network" ) > 0'},
                                'lines': {'network': f'array_contains({networks_array},"network")'}} 
    
def loadProjectLayers(version,uri,dictDB,plugin_dir,cur):
    dir=getProjectHandlingDir(plugin_dir)
    for vlayerName in ['energy_plants','customers','lines','devices','junctions']:  
        categories=featureLayerAssetgroups(vlayerName,cur)
        ids=featureLayerAssetgroupIds(vlayerName,cur)
        if not (vlayerName in ['devices'] and version=='temp'):
            uri.setDataSource(version, vlayerName, "geom")
            if version =='temp':
                vlayer = QgsVectorLayer(uri.uri(False), vlayerName+'_temp', dictDB['user'])
            else:
                vlayer = QgsVectorLayer(uri.uri(False), vlayerName, dictDB['user'])
            QgsProject.instance().addMapLayer(vlayer)  
            #print(vlayerName[:-1] + '_assetgroups')
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
                symbol=QgsSymbol.defaultSymbol(vlayer.geometryType())
                if vlayerName in ['lines']:
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
            
    #set field widget type as list
    setEditorWidgetListType(getListTypeDict())
    updateNetworkDependingFields(cur,dictDB)        

def updateNetworkDependingFields(cur,dictDB):
    networks=getNetworks(cur,dictDB)
    networks_array='array({})'.format(','.join([i for i in networks]))
    constraint_expression_dict = getConstraintExpressionDict(networks_array)
    setFieldConstraints(constraint_expression_dict)
    
def featureLayerAssetgroups(vlayerName,cur):
    try:
        sql="""SELECT assetgroup FROM {}_assetgroups ORDER BY id;""".format(vlayerName[:-1])
        cur.execute(sql)
        return [i['assetgroup'] for i in cur.fetchall()]
    except:
        return []
    
def featureLayerAssetgroupIds(vlayerName,cur):
    try:
        sql="""SELECT id FROM {}_assetgroups ORDER BY id;""".format(vlayerName[:-1])
        cur.execute(sql)
        return [i['id'] for i in cur.fetchall()]    
    except:
        return []
        
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
        if vlayerName in ['lines']:
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