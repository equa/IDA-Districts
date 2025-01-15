from qgis.core import QgsFieldConstraints
from plugins.utility_functions.db import *

import psycopg2.extras
import psycopg2
from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT
plugin_dir="""C:\\Users\\Peter\\AppData\\Roaming\\QGIS\\QGIS3\\profiles\\default\\python\\plugins\\"""
dictDB={'pwd' : 'p3t3r' , 'host' : 'localhost','port':'5434', 'user' : 'postgres', 'projectName' : 'test12', 'versionName' : '4'}

conn=dbConnect(dictDB,True)
cur=conn.cursor(cursor_factory = psycopg2.extras.RealDictCursor)
print(cur)

layer=iface.layerTreeView().selectedLayers()[0]
print(layer)


def getNetworks(cur,dictDB):
    sql="""SELECT id AS network FROM "{}".network;""".format(dictDB['versionName'])
    cur.execute(sql)
    networks=[str(i['network']) for i in cur.fetchall()]
    return networks
    
def setEditorWidgetListType(list_type_dict):
    """{layer: [col_names]}"""
    config = {'EmptyIsEmptyArray': False, 'EmptyIsNull': True}
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
        layer=QgsProject.instance().mapLayersByName(layer_name)[0]
        for col in constraints_dict[layer_name]:
            field_index = layer.fields().indexOf(col)
            print(field_index)
            layer.setFieldConstraint(field_index, QgsFieldConstraints.ConstraintExpression)
            layer.setConstraintExpression(field_index, constraints_dict[layer_name][col])

list_type_dict={'energy_plants':['network','main_plant'],'customers':['network'],'lines':['submodel'],'devices':['network']}

networks=getNetworks(cur,dictDB)
print(networks)
networks_array='array({})'.format(','.join([i for i in networks]))
print(networks_array)

constraint_expression_dict = {'energy_plants': {'network': f'array_all({networks_array}, "network")','main_plant': f'array_all({networks_array}, "main_plant")'},
                            'customers': {'network': f'array_all({networks_array}, "network")'},
                            'devices': {'network': f'array_all({networks_array}, "network")'},
                            'lines': {'network': f'array_contains({networks_array},"network")'}}
    
setEditorWidgetListType(list_type_dict)
setFieldConstraints(constraint_expression_dict)

layer=iface.layerTreeView().selectedLayers()[0]


