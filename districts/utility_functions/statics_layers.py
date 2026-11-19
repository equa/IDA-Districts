"""Layer group 'statics model' (change statics-model): the stored model tables of the version and the editable override
layers statics_points / statics_sections, loaded from the DB (no copies), replaced at every build."""
from qgis.core import (
    Qgis, QgsApplication, QgsAuthMethodConfig, QgsCategorizedSymbolRenderer, QgsDataSourceUri, QgsProject,
    QgsRendererCategory, QgsSymbol, QgsVectorLayer,
)
from qgis.PyQt.QtGui import QColor

from .statics_model import BEND_CLASSES, BEND_ELASTIC, BEND_KINK, BEND_NONE, BEND_PREFAB
from .translations import tr

STATICS_PROPERTY = 'districts_statics_model'
STATICS_GROUP = 'statics_model'
#(table, translation key of the layer name)
STATICS_LAYERS = [
    ('statics_model_nodes', 'statics_model_nodes'),
    ('statics_model_pipes', 'statics_model_pipes'),
    ('statics_points', 'statics_points'),
    ('statics_sections', 'statics_sections'),
]
BEND_COLORS = {BEND_NONE: '#bdbdbd', BEND_KINK: '#fdae61', BEND_PREFAB: '#d7191c', BEND_ELASTIC: '#2b83ba'}


def removeStaticsLayers():
    project = QgsProject.instance()
    for layer in list(project.mapLayers().values()):
        if layer.customProperty(STATICS_PROPERTY):
            project.removeMapLayer(layer.id())
    group = project.layerTreeRoot().findGroup(tr('@default', STATICS_GROUP))
    if group is not None:
        group.parent().removeChildNode(group)


def staticsGroup():
    root = QgsProject.instance().layerTreeRoot()
    group = root.findGroup(tr('@default', STATICS_GROUP))
    if group is None:
        group = root.insertGroup(0, tr('@default', STATICS_GROUP))
    return group


def bendRenderer():
    categories = []
    for cls in BEND_CLASSES:
        symbol = QgsSymbol.defaultSymbol(Qgis.GeometryType.Point)
        symbol.setColor(QColor(BEND_COLORS[cls]))
        symbol.setSize(2 if cls == BEND_NONE else 3.5)
        categories.append(QgsRendererCategory(cls, symbol, tr('@default', 'bend_class_' + cls)))
    junction = QgsSymbol.defaultSymbol(Qgis.GeometryType.Point)
    junction.setColor(QColor('#000000'))
    junction.setSize(2.5)
    categories.append(QgsRendererCategory(None, junction, tr('@default', 'junctions')))
    return QgsCategorizedSymbolRenderer('bend_class', categories)


def loadStaticsLayers(config, username=None, password=None):
    """Loads (or reloads) the layer group of the loaded version; returns {table: layer}."""
    if username is None or password is None:
        auth_cfg = QgsAuthMethodConfig()
        QgsApplication.authManager().loadAuthenticationConfig(config['auth_id'], auth_cfg, True)
        username, password = auth_cfg.config('username'), auth_cfg.config('password')
    removeStaticsLayers()
    group = staticsGroup()
    layers = {}
    for table, name_key in STATICS_LAYERS:
        uri = QgsDataSourceUri()
        uri.setConnection(config['host'], config['port'], config['projectName'], username, password)
        uri.setDataSource(config['versionName'], table, 'geom', '', 'id')
        layer = QgsVectorLayer(uri.uri(False), tr('@default', name_key), 'postgres')
        if not layer.isValid():
            continue
        layer.setCustomProperty(STATICS_PROPERTY, table)
        if table == 'statics_model_nodes':
            layer.setRenderer(bendRenderer())
        if table.startswith('statics_model'):
            #generated rows: a build replaces them, edits would be lost
            layer.setReadOnly(True)
        QgsProject.instance().addMapLayer(layer, False)
        group.addLayer(layer)
        layers[table] = layer
    return layers
