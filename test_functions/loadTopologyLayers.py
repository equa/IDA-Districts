from plugins.utility_functions.db import *


plugin_dir="""C:\\Users\\Peter\\AppData\\Roaming\\QGIS\\QGIS3\\profiles\\default\\python\\plugins\\"""
dictDB={'pwd' : 'p3t3r' , 'host' : 'localhost','port':'5434', 'user' : 'postgres', 'projectName' : 'test1000', 'versionName' : 'a'}

#dictDB=getDBConnectionData(plugin_dir)
conn=dbConnect(dictDB,True)
cur=conn.cursor(cursor_factory = psycopg2.extras.RealDictCursor)

def setLayersHidden(tableNames):

    for tableName in tableNames:
        print(tableName)
        layer=QgsProject.instance().mapLayersByName(tableName)
        if layer:
            layer=layer[0]
            model = iface.layerTreeView().layerTreeModel()
            ltv = iface.layerTreeView()
            root = QgsProject.instance().layerTreeRoot()
            node = root.findLayer( layer.id())
            index = model.node2index(node)
            print(index)
            print(index.row())
            ltv.setRowHidden( index.row(), index.parent(), True)
        
def loadTopologyLayers(version,uri,dictDB):
    #load tables without geometry and hide them in layers panel
    tableNames=['internal_loads_profiles','dhw_timeseries','pipe_bundle_types','customer_templates','energy_plant_templates',
        'line_types','room_units','building_constructions','building_templates']
    for tableName in tableNames:
        uri.setDataSource("public", tableName, "")
        layer = QgsVectorLayer(uri.uri(False), tableName, dictDB['user'])
        QgsProject.instance().addMapLayer(layer)
    
    setLayersHidden(tableNames) 
    
def removeLayers():
    layers = QgsProject.instance().mapLayers().values()
    for layer in layers:
        if layer.name() in ['internal_loads_profiles','pipe_bundle_types','dhw_timeseries','submodels','energy_plants','customers','customer_templates','energy_plant_templates',
            'junction_templates','junctions','streets', 'buildings','network','cosim',
            'lines','line_types','boreholes','borehole_fields',
            'pipematerial']:
            QgsProject.instance().removeMapLayer(layer)
            
uri = QgsDataSourceUri()
uri.setConnection(dictDB['host'], dictDB['port'], dictDB['projectName'], dictDB['user'], dictDB['pwd'])
print(uri)
removeLayers()
loadTopologyLayers('a',uri,dictDB)

