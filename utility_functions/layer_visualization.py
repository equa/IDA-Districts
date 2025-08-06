from plugins.utility_functions.files import *
from plugins.utility_functions.db import *
from qgis.core import  QgsCredentials, QgsDataSourceUri, QgsFieldConstraints, QgsExpression, QgsOptionalExpression,QgsAttributeEditorField,QgsAttributeEditorContainer, QgsEditFormConfig, QgsProject, QgsSvgMarkerSymbolLayer, QgsEditorWidgetSetup, QgsVectorLayer, QgsSymbol, QgsRendererCategory, QgsCategorizedSymbolRenderer

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
        #print(layer_name)
        layer=QgsProject.instance().mapLayersByName(layer_name)[0]
        for col in list_type_dict[layer_name]:
            field_index = layer.fields().indexOf(col)
            #print(field_index)

            # Apply the widget setup to the field
            layer.setEditorWidgetSetup(field_index, editor_setup)

def setFieldConstraints(constraints_dict):
    """{layer: {col_names : constraint}}"""
    for layer_name in constraints_dict:
        #print(layer_name)
        layer=QgsProject.instance().mapLayersByName(layer_name)
        if layer:
            layer=layer[0]
            for col in constraints_dict[layer_name]:
                field_index = layer.fields().indexOf(col)
                #print(field_index)
                layer.setFieldConstraint(field_index, QgsFieldConstraints.ConstraintExpression)
                layer.setConstraintExpression(field_index, constraints_dict[layer_name][col])
            
def getDHCLayerNames():
    return ["lines","junctions","energy_plants"]
    
def updateTableSrid(versions,cur,srid):
    """Updates the srid of geometry tables in each version"""
    sql="""SELECT UpdateGeometrySRID('%schema%', '%table%', 'geom', {});""".format(srid)
    #print('+--+')
    for version in versions:
        sql_version=sql.replace("%schema%",version)
        #version tables
        for table in ['lines','junctions','customers','energy_plants','buildings','streets','submodels','boreholes']:
            #print(sql_version.replace("%table%",table))
            try:
                cur.execute(sql_version.replace("%table%",table))
            except:
                pass
            
    #print('++')
    sql_temp=sql.replace("%schema%","temp")        
    #temp tables 
    #print('++')
    #print(sql_temp)
    for table in ['lines','lines_cooling','lines_heating','junctions','customers','streets_help']:
        #print(sql_temp.replace("%table%",table))
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
    for vlayerName in ['lines','junctions','customers','energy_plants']:
        vlayer=QgsProject.instance().mapLayersByName(vlayerName)[0] 
        fields=vlayer.fields()
        fc = vlayer.editFormConfig()
        fc.clearTabs()
        fc.setLayout(QgsEditFormConfig.TabLayout)
        if vlayerName=='junctions':
            attrNamesTabs= [['type'],
                            ['n_connections','zeta'],
                            ['submodel'],[]]
        elif vlayerName=='lines':
            attrNamesTabs= [['id','type','pipe_bundle_type_id','network'],
                            ['length','zeta'],
                            ['submodel'],[]]
        elif vlayerName=='customers':
            attrNamesTabs= [['id','template','network'],
                            ['load_w'],
                            ['dhw_id','internal_load_id','submodel'],
                            []]
        elif vlayerName=='energy_plants':
            attrNamesTabs= [['id','template','network'],
                            [],
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
    for vlayerName in ['lines','customers','energy_plants','junctions']:
        vlayer=QgsProject.instance().mapLayersByName(vlayerName)[0] 
        fields=vlayer.fields()
        if vlayerName=='lines':
            attrNames=['type','pipe_bundle_type_id','network','submodel','length']
            aliasNames=['Type','Pipe bundle type','Network','Co-sim','Length, m']
        elif vlayerName=='customers':
            attrNames=['template','submodel','load_w','dhw_id','internal_load_id']
            aliasNames=['Template','Co-sim','Load, W','Domestic hot water ID','Internal load ID']
        elif vlayerName=='energy_plants':
            attrNames=['template','submodel']
            aliasNames=['Template','Co-sim']
        elif vlayerName=='junctions':
            attrNames=['type','submodel','n_connections']
            aliasNames=['Type','Co-sim','Number of connections']
        
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
        if layer.name() in ['internal_loads_profiles','pipe_bundle_types','dhw_timeseries','submodels','energy_plants','customers','customer_templates','energy_plant_templates',
            'junction_types','junction_templates','junctions',
            'streets', 'buildings','network','cosim',
            'lines','line_types','boreholes','borehole_fields',
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
    #print('show temp tables')
    removeTempLayers()
    layerTreeRoot = QgsProject.instance().layerTreeRoot()  
    for layer in ['lines','junctions','customers','energy_plants']:
        if QgsProject.instance().mapLayersByName(layer):
            vlayer= QgsProject.instance().mapLayersByName(layer)[0]
            layerTreeRoot.findLayer(vlayer).setItemVisibilityChecked(False)
        else:
            #iface.messageBar().pushMessage("Warning", "No project tables loaded", level=Qgis.Warning)
            #print("No project tables loaded")
            return False
    try:
        loadProjectLayers('temp',uri,dictDB,plugin_dir,cur)  
    except:
        #print('Load project layers failed')
        pass

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
    tableNames=['internal_loads_profiles','dhw_timeseries','pipe_bundle_types','customer_templates','energy_plant_templates',
        'junction_types',
        'line_types','room_units','building_construction_standard','zone_templates']
    for tableName in tableNames:
        uri.setDataSource("public", tableName, "")
        layer = QgsVectorLayer(uri.uri(False), tableName, dictDB['user'])
        QgsProject.instance().addMapLayer(layer)
    
    setLayersHidden(tableNames) 

        
def getListTypeDict():
    return {'energy_plants':['network'],'customers':['network'],'lines':['submodel']} 
    
def getConstraintExpressionDict(networks_array):
    return {'energy_plants': {'network': f'array_all({networks_array}, "network") AND array_length( "network" ) > 0'},
                                'customers': {'network': f'array_all({networks_array}, "network") AND array_length( "network" ) > 0'},
                                'lines': {'network': f'array_contains({networks_array},"network")'}} 
    
def loadProjectLayers(version,uri,dictDB,plugin_dir,cur):
    dir=getProjectHandlingDir(plugin_dir)
    #print('load project layers')
    for vlayerName in ['energy_plants','customers','lines','junctions']:  
        #print('------')
        #print(vlayerName)
        categories=featureLayerGroups(vlayerName,cur)
        #print(categories)
        ids=featureLayerGroupIds(vlayerName,cur)
        #print(ids)

        uri.setDataSource(version, vlayerName, "geom")
        if version =='temp':
            vlayer = QgsVectorLayer(uri.uri(False), vlayerName+'_temp', dictDB['user'])
        else:
            vlayer = QgsVectorLayer(uri.uri(False), vlayerName, dictDB['user'])
        QgsProject.instance().addMapLayer(vlayer)  
        #print(vlayerName[:-1])
        target_layer_name=vlayerName[:-1] + ('_templates' if vlayerName in ['energy_plants','customers'] else '_types')
        cat_colmn_name='template' if vlayerName in ['energy_plants','customers'] else 'type'
        #print(target_layer_name)
        #print(cat_colmn_name)
        config = {'AllowMulti': False,
                  'AllowNull': True,
                  'FilterExpression': '',
                  'Key': '',
                  'Layer': '',
                  'NofColumns': 1,
                  'OrderByValue': False,
                  'UseCompleter': False,
                  'Value': ''}
        fields=vlayer.fields()

        if vlayerName in ['customers','energy_plants']:     
            config['Key'] = 'template'
            config['Value'] = 'template_name'
        else:
            config['Key'] = 'id'
            config['Value'] = 'type'
        target_layer = QgsProject.instance().mapLayersByName(target_layer_name)[0]             
        config['Layer'] = target_layer.id()
        config['FilterExpression']=""
        widget_setup = QgsEditorWidgetSetup('ValueRelation',config)
        field_idx = fields.indexOf(cat_colmn_name)
        vlayer.setEditorWidgetSetup(field_idx, widget_setup)

        categorized_renderer = QgsCategorizedSymbolRenderer()            
        categorized_renderer.setClassAttribute(cat_colmn_name) 
        for category,id in zip(categories,ids):      
            symbol=QgsSymbol.defaultSymbol(vlayer.geometryType())
            if vlayerName in ['lines']:
                symbol.setWidth(0.75) 
            else:
                symbol.setSize(2)
                svgStyle = {}
                dir_icon=dir+'/icons/{}/'.format(vlayerName)
                svg_fname=dir_icon+ category+'.svg'
                if os.path.exists(svg_fname):
                    svgStyle['name'] = svg_fname
                else:
                    svgStyle['name'] = dir_icon+vlayerName+'.svg'
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
    
def featureLayerGroups(vlayerName,cur):
    try:
        colmn='template_name' if vlayerName in ['customers','energy_plants'] else 'type'
        table='template' if vlayerName in ['customers','energy_plants'] else 'type'
        sql="""SELECT {} FROM {}_{}s ORDER BY id;""".format(colmn,vlayerName[:-1],table)
        #print(sql)
        cur.execute(sql)
        return [i[colmn] for i in cur.fetchall()]
    except:
        return []
    
def featureLayerGroupIds(vlayerName,cur):
    try:
        colmn='template' if vlayerName in ['customers','energy_plants'] else 'id'
        table='template' if vlayerName in ['customers','energy_plants'] else 'type'
        sql="""SELECT {} FROM {}_{}s ORDER BY id;""".format(colmn,vlayerName[:-1],table)
        #print(sql)
        cur.execute(sql)
        return [i[colmn] for i in cur.fetchall()]    
    except:
        return []
        
def loadFeatureLayer(version,dictDB,plugin_dir,vlayerName,cur):
    #print('load feature layer')
    dir=getProjectHandlingDir(plugin_dir)
    categories=featureLayerGroups(vlayerName,cur)
    ids=featureLayerGroupIds(vlayerName,cur)
    
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
    target_layer_name=vlayerName[:-1] + ('_templates' if vlayerName in ['energy_plants','customers'] else '_types')
    cat_colmn_name='template' if vlayerName in ['energy_plants','customers'] else 'type'
    config = {'AllowMulti': False,
              'AllowNull': True,
              'FilterExpression': '',
              'Key': '',
              'Layer': '',
              'NofColumns': 1,
              'OrderByValue': False,
              'UseCompleter': False,
              'Value': ''}
    fields=vlayer.fields()

    if vlayerName in ['customers','energy_plants']:     
        config['Key'] = 'template'
        config['Value'] = 'template_name'
    else:
        config['Key'] = 'id'
        config['Value'] = 'type'
    target_layer = QgsProject.instance().mapLayersByName(target_layer_name)[0]             
    config['Layer'] = target_layer.id()
    config['FilterExpression']=""
    widget_setup = QgsEditorWidgetSetup('ValueRelation',config)
    field_idx = fields.indexOf(cat_colmn_name)
    vlayer.setEditorWidgetSetup(field_idx, widget_setup)

    categorized_renderer = QgsCategorizedSymbolRenderer()            
    categorized_renderer.setClassAttribute(cat_colmn_name) 
    for category,id in zip(categories,ids):      
        symbol=QgsSymbol.defaultSymbol(vlayer.geometryType())
        if vlayerName in ['lines']:
            symbol.setWidth(0.75) 
        else:
            symbol.setSize(2)
            svgStyle = {}
            dir_icon=dir+'/icons/{}/'.format(vlayerName)
            svg_fname=dir_icon+ category+'.svg'
            if os.path.exists(svg_fname):
                svgStyle['name'] = svg_fname
            else:
                svgStyle['name'] = dir_icon+vlayerName+'.svg'
            svgStyle['outline'] = '#000000'
            svgStyle['size'] = '8'
            symbolLayer = QgsSvgMarkerSymbolLayer.create(svgStyle)
            symbol = QgsSymbol.defaultSymbol(vlayer.geometryType()) 
            symbol.changeSymbolLayer(0, symbolLayer)
            
        cat = QgsRendererCategory(id, symbol, category)
        categorized_renderer.addCategory(cat)    
    vlayer.setRenderer(categorized_renderer)
    if vlayerName in ['lines']:
        valueRelationPipeBundleType()  
    if vlayerName in ['customers']:
        valueRelationDhwId()    
        valueRelationInternalLoadId() 
      
    setupVersionForm(cur,dictDB)  
        