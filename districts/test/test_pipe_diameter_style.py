# coding=utf-8
"""Style of the lines by the inner pipe diameter (stylePipeDiameter) and by the difference to the parent version,
on a memory layer with a fake DB cursor (no DB needed)."""
import pytest
from qgis.core import (
    QgsExpression, QgsExpressionContext, QgsExpressionContextUtils, QgsFeature, QgsProject, QgsVectorLayer,
)

from districts.utility_functions import layer_visualization
from districts.utility_functions.layer_visualization import roundLikeExpression, stylePipeDiameter
from districts.utility_functions.translations import tr

# pipe_bundle_type_id -> inner diameter [m] (sequence 1), bundle 3 has no pipe in sequence 1
BUNDLES = {1: 0.05, 2: 0.08}
# line id -> (pipe bundle of the version, inner diameter in the parent version)
LINES = {1: (1, 0.05), 2: (2, 0.05), 3: (1, 0.0703), 4: (1, None), 5: (None, 0.05), 6: (3, 0.05), 7: (2, 0.0703)}
EXPECTED = {1: 0, 2: 300, 3: -203, 4: 'no_parent', 5: 'no_pipe', 6: 'no_pipe', 7: 97}


class FakeCursor:
    """returns the pipe bundles or the lines of the parent version, depending on the query"""
    def execute(self, sql, args=None):
        self.sql = sql

    def fetchall(self):
        if '.lines' in self.sql:
            assert '"parent1".lines' in self.sql
            return [{'id': i, 'd': d} for i, (_, d) in LINES.items() if d is not None]
        return [{'pipe_bundle_type_id': b, 'd': d} for b, d in BUNDLES.items()]


class FakeIface:
    def layerTreeView(self):
        return self

    def refreshLayerSymbology(self, layer_id):
        pass


@pytest.fixture
def lines_layer(qgis_app, monkeypatch):
    monkeypatch.setattr(layer_visualization, 'iface', FakeIface())
    layer = QgsVectorLayer('LineString?crs=EPSG:2056&field=id:integer&field=pipe_bundle_type_id:integer',
                           tr('@default', 'lines'), 'memory')
    features = []
    for i, (bundle, _) in LINES.items():
        f = QgsFeature(layer.fields())
        f.setAttributes([i, bundle])
        features.append(f)
    layer.dataProvider().addFeatures(features)
    QgsProject.instance().addMapLayer(layer)
    yield layer
    QgsProject.instance().removeMapLayer(layer.id())


def evaluate(layer, expression):
    exp = QgsExpression(expression)
    context = QgsExpressionContext(QgsExpressionContextUtils.globalProjectLayerScopes(layer))
    result = {}
    for f in layer.getFeatures():
        context.setFeature(f)
        value = exp.evaluate(context)
        assert not exp.hasEvalError(), exp.evalErrorString()
        result[f['id']] = None if value is None or str(value) == 'NULL' else value
    return result


def test_round_like_expression():
    assert [roundLikeExpression(x) for x in (0.4, 0.5, 1.5, 2.5, -0.5, -2.5, -2.4)] == [0, 1, 2, 3, -1, -3, -2]


def test_diameter(lines_layer):
    assert stylePipeDiameter(FakeCursor(), show_labels=True)
    renderer = lines_layer.renderer()
    assert [c.label() for c in renderer.categories()][:2] == ['d_i = 50 mm', 'd_i = 80 mm']
    values = evaluate(lines_layer, renderer.classAttribute())
    assert values == {1: 0.05, 2: 0.08, 3: 0.05, 4: 0.05, 5: None, 6: None, 7: 0.08}


def test_difference_to_parent_version(lines_layer):
    assert stylePipeDiameter(FakeCursor(), show_labels=True, ramp_name='RdBu', invert_ramp=True, compare_version='parent1')
    renderer = lines_layer.renderer()
    values = evaluate(lines_layer, renderer.classAttribute())
    assert values == EXPECTED

    categories = {str(c.value()): c for c in renderer.categories()}
    # every line has a category, the differences are sorted in the legend
    assert {str(v) for v in EXPECTED.values()} == set(categories)
    assert [c.label() for c in renderer.categories()][:4] == ['Δd_i = -20.3 mm', 'Δd_i = ±0 mm', 'Δd_i = +9.7 mm', 'Δd_i = +30 mm']
    assert 'parent1' in categories['no_parent'].label()
    # smaller blue, larger red (inverted RdBu, centered at 0), changed lines wider than unchanged ones
    smaller, larger = categories['-203'].symbol().color(), categories['300'].symbol().color()
    assert smaller.blue() > smaller.red() and larger.red() > larger.blue()
    assert categories['300'].symbol().width() > categories['0'].symbol().width()

    # labels: only the changed lines, with sign
    assert lines_layer.labelsEnabled()
    labels = evaluate(lines_layer, lines_layer.labeling().settings().fieldName)
    assert {i: l for i, l in labels.items() if l is not None} == {
        2: '+' + QgsExpression("format_number(30, 1)").evaluate(), 3: QgsExpression("format_number(-20.3, 1)").evaluate(),
        7: '+' + QgsExpression("format_number(9.7, 1)").evaluate()}


def test_parent_version_without_pipes(lines_layer, monkeypatch):
    for i in list(LINES):
        monkeypatch.setitem(LINES, i, (LINES[i][0], None))
    assert stylePipeDiameter(FakeCursor(), compare_version='parent1')
    values = evaluate(lines_layer, lines_layer.renderer().classAttribute())
    assert set(values.values()) == {'no_parent', 'no_pipe'}
