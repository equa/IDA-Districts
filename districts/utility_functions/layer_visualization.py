from .files import *
from .translations import *
from .db import *
from .reports import *
from qgis.core import  QgsDefaultValue, QgsCredentials, QgsDataSourceUri, QgsFieldConstraints, QgsExpression, QgsOptionalExpression,QgsAttributeEditorField,QgsAttributeEditorContainer, QgsEditFormConfig, QgsProject, QgsSvgMarkerSymbolLayer, QgsEditorWidgetSetup, QgsVectorLayer, QgsSymbol, QgsRendererCategory, QgsCategorizedSymbolRenderer
from qgis.utils import iface
from qgis.PyQt.QtGui import QColor

def setupCustomerLoadValue(config,plugin_dir,projectConfig):
    """Setup of the customer data sheet (RMB project) including button which generates a print layout and exports a pdf"""
    
    feature_layer=QgsProject.instance().mapLayersByName(tr('@default','customers'))[0] 
    #print(feature_layer)
    
    action_text="""from districts.ida_ph import *
ShowLoadAttributeDialog([%id%])"""

    helpAction = QgsAction(Qgis.AttributeActionType.GenericPython, tr('@default','set_load_attribute'), action_text, None, capture=False, shortTitle=tr('@default','set_load_attribute'), actionScopes={'Feature'})
    feature_layer.actions().addAction(helpAction)

    form_config = feature_layer.editFormConfig()

    rootContainer = form_config.invisibleRootContainer()
    #print(rootContainer)
    editorAction = QgsAttributeEditorAction(helpAction, rootContainer)
    rootContainer.addChildElement(editorAction)

    feature_layer.setEditFormConfig(form_config)
    
def setupFeatureLayerDialog(layer_name,cur,config,plugin_dir):
    removeLayer(layer_name)
    loadFeatureLayer(config['versionName'],config,plugin_dir,layer_name,cur)
    setupVersionForm(cur,plugin_dir,config)
    versionLayersAliasNames()
    setupCustomerDataSheet(config,plugin_dir,loadProjectConfig(config))
    setupCustomerLoadValue(config,plugin_dir,loadProjectConfig(config))
    if layer_name=='lines':
        valueRelationPipeBundleType() 
        
def loadLayersConfig(config,plugin_dir,project_name):
    layers_config=''
    if project_name:
        config_f="{}{}\\layersConfig.txt".format(config['pathProjects'],project_name)
        #print(config_f)
        if os.path.exists(config_f):
            #print(config_f)
            with open(config_f, "r") as myfile:   
                for line in myfile:        
                    layers_config+=line
        else:
            file_template=plugin_dir+"\\config\\layersConfig_template.txt"
            if os.path.exists(file_template):
                #print(file_template)
                with open(file_template, "r") as myfile:   
                    for line in myfile:        
                        layers_config+=line
        layers_config=strToDict(layers_config)
    else:
        #print('No project name')
        pass
    #print(layers_config)    
    return layers_config
    
def writeLayersConfig(config,project_name,layersConfig):
    config_path=config_f="{}{}".format(config['pathProjects'],project_name)
    config_f=config_path+"\\layersConfig.txt"
    if os.path.exists(config_path):
        with open(config_f, "w") as myfile:   
            myfile.write(str(layersConfig))
           
def zoomToLayer(layer_name):
    # Get the active QGIS map canvas
    canvas = iface.mapCanvas()

    # Get the layer you want to zoom to (replace with your layer name)
    layer = QgsProject.instance().mapLayersByName(tr('@default',layer_name))[0]

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
        layer=QgsProject.instance().mapLayersByName(tr('@default',layer_name))[0]
        for col in list_type_dict[layer_name]:
            field_index = layer.fields().indexOf(col)
            #print(field_index)

            # Apply the widget setup to the field
            layer.setEditorWidgetSetup(field_index, editor_setup)

def setFieldConstraints(constraints_dict):
    """{layer: {col_names : constraint}}"""
    for layer_name in constraints_dict:
        #print(layer_name)
        layer=QgsProject.instance().mapLayersByName(tr('@default',layer_name))
        if layer:
            layer=layer[0]
            for col in constraints_dict[layer_name]:
                field_index = layer.fields().indexOf(col)
                #print(field_index)
                layer.setFieldConstraint(field_index, QgsFieldConstraints.ConstraintExpression)
                layer.setConstraintExpression(field_index, constraints_dict[layer_name][col])
                
def setFieldDefaultValues(getDefaultValueDict):
    """{layer: {col_names : constraint}}"""
    for layer_name in getDefaultValueDict:
        #print(layer_name)
        layer=QgsProject.instance().mapLayersByName(tr('@default',layer_name))
        if layer:
            layer=layer[0]
            for col in getDefaultValueDict[layer_name]:
                field_index = layer.fields().indexOf(col)
                #print(field_index)
                default_val = QgsDefaultValue(getDefaultValueDict[layer_name][col], True)
                layer.setDefaultValueDefinition(field_index, default_val)

            
def getDHCLayerNames():
    return ["lines","junctions","energy_plants","customers","boreholes"]
    
def updateTableSrid(versions,cur,srid):
    """Updates the srid of geometry tables in each version"""
    sql="""SELECT UpdateGeometrySRID('%schema%', '%table%', 'geom', {});""".format(srid) # nosec B608
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
            
def mapValueLinesNetwork(cur,config):
    layer=QgsProject.instance().mapLayersByName(tr('@default','lines'))[0]
    field_index = layer.fields().indexOf('network')
    networks=getNetworks(cur,config)
    val_map = {tr('@default','network')+': '+str(i) : i for i in networks}
    config_map = {'map': val_map}
    layer.setEditorWidgetSetup(field_index, QgsEditorWidgetSetup('ValueMap', config_map))

def getFeatureTypes(cur,feature):
    sql="""SELECT id, type FROM {}_types ORDER BY id;""".format(feature) # nosec B608
    cur.execute(sql)
    return cur.fetchall()
    
def mapValueFeatureType(layer,feature,cur,config):
    field_index = layer.fields().indexOf('type')
    types=getFeatureTypes(cur,feature)
    val_map = { "\u200B" * i + tr('@default',type['type']) : type['id'] for i,type in enumerate(types)}
    config_map = {'map': val_map}
    layer.setEditorWidgetSetup(field_index, QgsEditorWidgetSetup('ValueMap', config_map))
        
    default_val = QgsDefaultValue("0", False)
    layer.setDefaultValueDefinition(field_index, default_val)
    
def mapValueFeatureTemplate(layer,layer_name,cur,config):
    field_index = layer.fields().indexOf('template')
    templates=getTemplatesInfo(layer_name,cur)
    val_map = { "\u200B" * i + tr('@default',template['template_name']) : template['template'] for i,template in enumerate(templates)}
    config_map = {'map': val_map}
    layer.setEditorWidgetSetup(field_index, QgsEditorWidgetSetup('ValueMap', config_map))
        
    default_val = QgsDefaultValue("0", False)
    layer.setDefaultValueDefinition(field_index, default_val)
    
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
              'Value': 'description',
              # AKTIVIERE DIE ÜBERSETZUNG DER WERTE:
              'UseComplexExpression': True, 
              'DisplayExpression': 'tr("description")' # Hier passiert die Linguist-Übersetzung
    }
    widget_setup = QgsEditorWidgetSetup('ValueRelation',config)
    fields = QgsProject.instance().mapLayersByName(tr('@default','lines'))[0].fields()
    field_idx = fields.indexOf('pipe_bundle_type_id')
    QgsProject.instance().mapLayersByName(tr('@default','lines'))[0].setEditorWidgetSetup(field_idx, widget_setup)   

def extract_group_fields(layer):
    """
    Returns:
        {group_name: [field1, field2, ...]}
    """

    config = layer.editFormConfig()
    root = config.invisibleRootContainer()

    result = {}

    def walk(container, current_group="general"):

        # ensure group exists
        if current_group not in result:
            result[current_group] = []

        for child in container.children():

            cls = child.__class__.__name__

            # FIELD NODE ONLY
            if cls == "QgsAttributeEditorField":
                result[current_group].append(child.name())

            # GROUP CONTAINER
            elif cls == "QgsAttributeEditorContainer":
                group_name = child.name() or current_group
                walk(child, group_name)

    walk(root)

    # clean duplicates + sort
    for k in result:
        result[k] = sorted(set(result[k]))

    return result


def on_form_changed(config,plugin_dir,project_name):
    layersConfig=loadLayersConfig(config,plugin_dir,project_name)
    layer = iface.activeLayer()
    data = extract_group_fields(layer)
    #print(data)
    layersConfig[layer.name()]=data
    #print(layersConfig)
    writeLayersConfig(config,project_name,layersConfig)


def setupVersionForm(cur,plugin_dir,config):  
    """ setup form for version layers"""
    layersConfig=loadLayersConfig(config,plugin_dir,config['projectName'])
    #print(layersConfig)
    for vlayerName in layersConfig:
        vlayer=QgsProject.instance().mapLayersByName(tr('@default',vlayerName))[0] 
        fields=vlayer.fields()
        fc = vlayer.editFormConfig()
        fc.clearTabs()
        fc.setLayout(QgsEditFormConfig.TabLayout)

        for tab, attrNamesTab in layersConfig[vlayerName].items():
            c = QgsAttributeEditorContainer(tr('@default',tab), fc.invisibleRootContainer())
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
    for vlayerName in ['lines','customers','energy_plants','junctions','buildings','streets']:
        vlayer=QgsProject.instance().mapLayersByName(tr('@default',vlayerName))[0] 
        fields=vlayer.fields()
        for field in fields:
            field_idx = fields.indexOf(field.name())
            vlayer.setFieldAlias(field_idx,tr('@default',field.name()))                      
       
def removeLayer(layer_name):
    if QgsProject.instance().mapLayersByName(tr('@default',layer_name)):
        layer=QgsProject.instance().mapLayersByName(tr('@default',layer_name))[0]
        QgsProject.instance().removeMapLayer(layer)

def loadBoreholesLayer(version,uri,config,plugin_dir,cur,username):
    vlayerName='boreholes'
    uri.setDataSource(version, vlayerName, "geom")
    vlayer = QgsVectorLayer(uri.uri(False), vlayerName, username)
    QgsProject.instance().addMapLayer(vlayer)  
    target_layer = QgsProject.instance().mapLayersByName(tr('@default','energy_plants'))[0]
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
        if layer.name() in ['pipe_bundle_types','submodels',tr('@default','energy_plants'),tr('@default','customers'),'customer_templates','energy_plant_templates',
            'junction_types','junction_templates',tr('@default','junctions'),
            tr('@default','streets'), tr('@default','buildings'),'network','cosim',
            tr('@default','lines'),'line_types','boreholes','borehole_fields',
            'pipematerial','lines_results_supply_temperature','customer_results_load']:
            QgsProject.instance().removeMapLayer(layer)
    iface.mapCanvas().refresh()

        
def removeTempLayers():
    layers = QgsProject.instance().mapLayers().values()
    for layer in layers:
        if layer.name() in [tr('@default','customers')+' temp.',tr('@default','lines')+' temp.',tr('@default','lines')+' heating temp.',tr('@default','lines')+' cooling temp.',tr('@default','junctions')+' temp.',tr('@default','energy_plants')+' temp.']:
            QgsProject.instance().removeMapLayer(layer)

def showTempTables(uri,config,plugin_dir,signals,cur):
    """Show temp tables (lines,customers,junctions,energy_plants)"""
    #print('show temp tables')
    removeTempLayers()
    layerTreeRoot = QgsProject.instance().layerTreeRoot()  
    for layer in ['lines','junctions','customers','energy_plants']:
        if QgsProject.instance().mapLayersByName(tr('@default',layer)):
            vlayer= QgsProject.instance().mapLayersByName(tr('@default',layer))[0]
            layerTreeRoot.findLayer(vlayer).setItemVisibilityChecked(False)
        else:
            signals.error.emit("No project tables loaded")
            #print("No project tables loaded")
            return False
    try:
        auth_cfg = QgsAuthMethodConfig()
        QgsApplication.authManager().loadAuthenticationConfig(config["auth_id"], auth_cfg, True)

        loadProjectLayers('temp',uri,config,plugin_dir,cur,auth_cfg.config("username"))  
    except:
        #print('Load project layers failed')
        pass

def setLayersHidden(tableNames):
    for tableName in tableNames:
        layer=QgsProject.instance().mapLayersByName(tr('@default',tableName))
        if layer:
            layer=layer[0]
            model = iface.layerTreeView().layerTreeModel()
            ltv = iface.layerTreeView()
            root = QgsProject.instance().layerTreeRoot()
            node = root.findLayer( layer.id())
            index = model.node2index(node)
            ltv.setRowHidden( index.row(), index.parent(), True)
        
def loadTopologyLayers(version,uri,config,username):
    #load tables without geometry and hide them in layers panel
    tableNames=['pipe_bundle_types','customer_templates','energy_plant_templates',
        'junction_types',
        'line_types']
    for tableName in tableNames:
        uri.setDataSource("public", tableName, "")
        layer = QgsVectorLayer(uri.uri(False), tableName, username)
        QgsProject.instance().addMapLayer(layer)
    
    setLayersHidden(tableNames) 

        
def getListTypeDict():
    return {'energy_plants':['network'],'customers':['network'],'lines':[]} 
    
def getConstraintExpressionDict(networks_array):
    return {'energy_plants': {'network': f'array_all({networks_array}, "network") AND array_length( "network" ) > 0'},
            'customers': {'network': f'array_all({networks_array}, "network") AND array_length( "network" ) > 0'},
            'lines': {}} 

def getDefaultValueDict(network, energy_plant_template,customer_template,line_type):
    network_array='array({})'.format(network)
    return {'energy_plants': {'network': network_array,'template':energy_plant_template},
            'customers': {'network': network_array,'template':customer_template},
            'lines': {'network': network,'type':line_type}} 
    
def loadProjectLayers(version,uri,config,plugin_dir,cur,username):
    #print('load project layers')
    if version:
        for vlayerName in ['energy_plants','customers','lines','junctions']:  
            #print('------')
            #print(vlayerName)
            categories=featureLayerGroups(vlayerName,cur)
            #print(categories)
            ids=featureLayerGroupIds(vlayerName,cur)
            #print(ids)

            uri.setDataSource(version, vlayerName, "geom")
            if version =='temp':
                vlayer = QgsVectorLayer(uri.uri(False), tr('@default',vlayerName)+' temp.', username)
            else:
                vlayer = QgsVectorLayer(uri.uri(False), tr('@default',vlayerName), username)
            QgsProject.instance().addMapLayer(vlayer)  
            #print(vlayerName[:-1])

            if vlayerName in ['customers','energy_plants']:     
                mapValueFeatureTemplate(vlayer,vlayerName[:-1],cur,config)
            else:
                mapValueFeatureType(vlayer,vlayerName[:-1],cur,config)


            categorized_renderer = QgsCategorizedSymbolRenderer()            
            cat_colmn_name='template' if vlayerName in ['energy_plants','customers'] else 'type'
            categorized_renderer.setClassAttribute(cat_colmn_name) 
            colors = [
                "#e31a1c",  # red
                "#1f78b4",  # blue
                "#000000",  # black
                "#33a02c",  # green
                "#ff7f00",  # orange
                "#6a3d9a"   # magenta/purple
            ]
            for category,id,color in zip(categories,ids,colors):      
                symbol=QgsSymbol.defaultSymbol(vlayer.geometryType())
                if vlayerName in ['lines']:
                    symbol.setWidth(0.75) 
                    symbol.setColor(QColor(color)) 
                else:
                    if symbol is not None:
                        symbol.setSize(2)
                    svgStyle = {}
                    dir_icon=plugin_dir+'/icons/{}/'.format(vlayerName)
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
            vlayer.editFormConfigChanged.connect(lambda: on_form_changed(config,plugin_dir,config['projectName']))
            
        #set map values
        mapValueLinesNetwork(cur,config)
                
        #set field widget type as list
        setEditorWidgetListType(getListTypeDict())
        updateNetworkDependingFields(cur,config)
    
def getDefaults(table,cur,config):
    """get the default values of a table """
    sql="""SELECT column_name, column_default
FROM information_schema.columns
WHERE (table_schema, table_name) = ('{}', '{}')
ORDER BY ordinal_position;""".format(config['versionName'],table) # nosec B608
    #print(sql)
    cur.execute(sql)
    defaults=cur.fetchall()
    return defaults
    
def updateNetworkDependingFields(cur,config):
    #print('--updateNetworkDependingFields--')
    networks=getNetworks(cur,config)
    networks_array_constraint='array({})'.format(','.join([i for i in networks]))
    network_default=[i['column_default'] for i in getDefaults('lines',cur,config) if i['column_name']=='network'][0]
    energy_plant_template=[i['column_default'] for i in getDefaults('energy_plants',cur,config) if i['column_name']=='template'][0]
    customer_template=[i['column_default'] for i in getDefaults('customers',cur,config) if i['column_name']=='template'][0]
    line_type=[i['column_default'] for i in getDefaults('lines',cur,config) if i['column_name']=='type'][0]
    try:
        constraint_expression_dict = getConstraintExpressionDict(networks_array_constraint)
        setFieldConstraints(constraint_expression_dict)
        setFieldDefaultValues(getDefaultValueDict(network_default, energy_plant_template,customer_template,line_type))
    except:
        pass
    
def featureLayerGroups(vlayerName,cur):
    try:
        colmn='template_name' if vlayerName in ['customers','energy_plants'] else 'type'
        table='template' if vlayerName in ['customers','energy_plants'] else 'type'
        sql="""SELECT {} FROM {}_{}s ORDER BY id;""".format(colmn,vlayerName[:-1],table) # nosec B608
        #print(sql)
        cur.execute(sql)
        return [tr('@default',i[colmn]) for i in cur.fetchall()]
    except:
        return []
    
def featureLayerGroupIds(vlayerName,cur):
    try:
        colmn='template' if vlayerName in ['customers','energy_plants'] else 'id'
        table='template' if vlayerName in ['customers','energy_plants'] else 'type'
        sql="""SELECT {} FROM {}_{}s ORDER BY id;""".format(colmn,vlayerName[:-1],table) # nosec B608
        #print(sql)
        cur.execute(sql)
        return [i[colmn] for i in cur.fetchall()]    
    except:
        return []
        
def loadFeatureLayer(version,config,plugin_dir,vlayerName,cur):
    #print('load feature layer')
    #print(vlayerName)
    categories=featureLayerGroups(vlayerName,cur)
    ids=featureLayerGroupIds(vlayerName,cur)
    
    uri = QgsDataSourceUri()
    auth_cfg = QgsAuthMethodConfig()
    QgsApplication.authManager().loadAuthenticationConfig(config["auth_id"], auth_cfg, True)

    uri.setConnection(config['host'], config['port'], config['projectName'], None, None)
    connInfo = uri.connectionInfo()
    QgsCredentials.instance().put( connInfo, auth_cfg.config("username"), auth_cfg.config("password"))  
    uri.setDataSource(version, vlayerName, "geom")
 
    if version =='temp':
        vlayer = QgsVectorLayer(uri.uri(False), tr('@default',vlayerName)+'_temp', auth_cfg.config("username"))
    else:
        vlayer = QgsVectorLayer(uri.uri(False), tr('@default',vlayerName), auth_cfg.config("username"))
    QgsProject.instance().addMapLayer(vlayer)  

    if vlayerName in ['customers','energy_plants']:     
        mapValueFeatureTemplate(vlayer,vlayerName[:-1],cur,config)
    else:
        mapValueFeatureType(vlayer,vlayerName[:-1],cur,config)
    
    categorized_renderer = QgsCategorizedSymbolRenderer()            
    cat_colmn_name='template' if vlayerName in ['energy_plants','customers'] else 'type'
    categorized_renderer.setClassAttribute(cat_colmn_name) 
    colors = [
        "#e31a1c",  # red
        "#1f78b4",  # blue
        "#000000",  # black
        "#33a02c",  # green
        "#ff7f00",  # orange
        "#6a3d9a"   # magenta/purple
    ]
    for category,id,color in zip(categories,ids,colors):      
        symbol=QgsSymbol.defaultSymbol(vlayer.geometryType())
        if vlayerName in ['lines']:
            symbol.setWidth(0.75) 
            symbol.setColor(QColor(color)) 
        else:
            if symbol is not None:
                symbol.setSize(2)
            svgStyle = {}
            dir_icon=plugin_dir+'/icons/{}/'.format(vlayerName)
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
    vlayer.editFormConfigChanged.connect(lambda: on_form_changed(config,plugin_dir,config['projectName']))
        
    #set map values
    if vlayerName=='lines':
        mapValueLinesNetwork(cur,config)
            
    #set field widget type as list
    setEditorWidgetListType(getListTypeDict())
    updateNetworkDependingFields(cur,config)
        