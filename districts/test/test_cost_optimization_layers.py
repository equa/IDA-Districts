# coding=utf-8
"""Layer panel after a cost optimization run: a version loaded afterwards must not land in an iteration group,
and the hidden table layers must not hide other rows of the layer panel."""
from qgis.core import QgsLayerTreeModel, QgsLayerTreeRegistryBridge, QgsProject, QgsVectorLayer
from qgis.gui import QgsLayerTreeView

from districts.utility_functions import cost_optimization_layers, layer_visualization
from districts.utility_functions.cost_optimization_layers import costGroup, groupName, layerInsertionAtTop, removeCostLayers
from districts.utility_functions.translations import tr, tr_msg


def memoryLayer(name):
    return QgsVectorLayer('Point?crs=EPSG:2056', name, 'memory')


def iterationLayer():
    layer = memoryLayer('iteration layer')
    QgsProject.instance().addMapLayer(layer, False)
    costGroup(1).addLayer(layer)
    return layer


def test_layers_after_a_run_go_to_the_top(monkeypatch):
    project, root = QgsProject.instance(), QgsProject.instance().layerTreeRoot()
    monkeypatch.setattr(cost_optimization_layers, 'iface', None)
    try:
        iterationLayer()
        # as QGIS does with an iteration layer selected in the layer panel
        sub = root.findGroup(groupName()).findGroup(tr_msg('Iteration {}').format(1))
        project.layerTreeRegistryBridge().setLayerInsertionPoint(QgsLayerTreeRegistryBridge.InsertionPoint(sub, 0))
        layerInsertionAtTop()
        loaded = memoryLayer('version layer')
        project.addMapLayer(loaded)
        assert root.findLayer(loaded.id()).parent() is root
    finally:
        removeCostLayers()
        project.removeAllMapLayers()
    assert root.findGroup(groupName()) is None


def test_hidden_table_layers_hide_only_their_rows(monkeypatch):
    project, root = QgsProject.instance(), QgsProject.instance().layerTreeRoot()
    view = QgsLayerTreeView()
    model = QgsLayerTreeModel(root, view)  # the view's parent keeps the model alive
    view.setModel(model)

    class Iface:
        def layerTreeView(self):
            return view
    monkeypatch.setattr(layer_visualization, 'iface', Iface())
    try:
        top = memoryLayer('top layer')
        project.addMapLayer(top)
        group = root.insertGroup(0, 'a group')
        others = [memoryLayer('other {}'.format(k)) for k in range(3)]
        table = memoryLayer(tr('@default', 'pipe_bundle_types'))
        for layer in others + [table]:
            project.addMapLayer(layer, False)
            group.addLayer(layer)
        layer_visualization.setLayersHidden(['pipe_bundle_types'])
        assert view.isRowHidden(view.node2index(root.findLayer(table.id())).row(), view.node2index(group))
        for node in [group, root.findLayer(top.id())] + [root.findLayer(layer.id()) for layer in others]:
            index = view.node2index(node)
            assert not view.isRowHidden(index.row(), index.parent()), node.name()
    finally:
        project.removeAllMapLayers()
        root.removeAllChildren()
