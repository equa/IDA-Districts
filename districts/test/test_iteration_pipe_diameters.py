# coding=utf-8
"""Inner diameters of the lines in the iterations of the dynamic pipe sizing: d / d_new in the iteration file, the
diameter layer per iteration and pair, its colors and the order of the line layers
(OpenSpec change show-iteration-pipe-diameters). Memory layers and a fake DB cursor, no database."""
import pytest
from qgis.core import QgsProject

from districts.utility_functions.dynamic_sizing_results import (
    PAIR_PROPERTY, SIZING_PROPERTY, diameterRenderer, pairSummary, removeSizingLayers, showIteration, sizingGroup,
)
from districts.utility_functions.layer_visualization import diameterColors, diameterLabel, turboColor
from districts.utility_functions.translations import tr_msg


# ---------------------------------------------------------------- iteration file
def result(pipe_new):
    """result of getCustomerLinePressure / optimizePipeDiameters of a pair 1/2 with one line (pipe 5, sized: pipe_new)"""
    catalog = {4: {'name': 'DRE-40', 'd': 0.0372}, 5: {'name': 'DRE-50', 'd': 0.04306}}
    res = {'catalog': catalog, 'c_lid': {7: [1e5, {}]}, 'dvar': {7: (4e4, 1)}, 'times': {7: 't'}, 'time': 't', 'cid_dp': 7, 'epid_dp': 1,
           'dp': 4e4, 'dp_spez': {3: 50.0}, 'lines': {3: {'pipes': {1: {'pipe_id': 5, 'mdot': 1.0}, 2: {'pipe_id': 5, 'mdot': 1.0}}}}}
    opt = {'c_lid': {7: [0.9e5, {}]}, 'pipes': {3: {1: pipe_new, 2: pipe_new}}, 'cid_weak': 7, 'dp_target': 0.9e5, 'quota': 1.0,
           'spread': 0.0, 'presize': [], 'history': [{}]}
    return res, opt


def test_diameters_in_the_iteration_file():
    res, opt = result(4)
    line = pairSummary((1, 2), (70.0, 30.0), res, opt, {3})['lines']['3']
    assert (line['d'], line['d_new']) == (43.1, 37.2)  # mm, rounded to 0.1 mm
    line = pairSummary((1, 2), (70.0, 30.0), res, opt, {3}, reference=True)['lines']['3']
    assert line['d_new'] == line['d'] == 43.1


# ---------------------------------------------------------------- colors
def test_diameter_colors_follow_the_ramp():
    colors = diameterColors([80.0, 50.0, 50.0, 65.0], ramp_name='no such ramp')  # without the ramp: turboColor
    assert list(colors) == [50.0, 65.0, 80.0]
    assert [c.name() for c in colors.values()] == [turboColor(t).name() for t in (0.0, 0.5, 1.0)]
    # the unit does not matter: the same colors for [m] as in stylePipeDiameter and [mm] as in the iteration layer
    assert [c.name() for c in diameterColors([0.08, 0.05, 0.065]).values()] == [c.name() for c in diameterColors([80.0, 50.0, 65.0]).values()]
    assert [c.name() for c in diameterColors([40.0], ramp_name='no such ramp').values()] == [turboColor(0.5).name()]
    assert diameterColors([]) == {}
    assert diameterLabel(37.2) == 'd_i = 37.2 mm' and diameterLabel(50.0) == 'd_i = 50 mm'


def test_categories_cover_all_iterations_of_the_pair(qgis_app):
    renderer = diameterRenderer([43.1, 37.2, None, 43.1, 28.5])
    assert renderer.classAttribute() == 'd_new'
    labels = [c.label() for c in renderer.categories()]
    assert labels == ['d_i = 28.5 mm', 'd_i = 37.2 mm', 'd_i = 43.1 mm', tr_msg('no diameter')]
    assert renderer.categories()[-1].value() in ('', None)  # all other values, NULL of earlier files


# ---------------------------------------------------------------- layers
WKT = {'3': 'LineString (0 0, 10 0)', '4': 'LineString (10 0, 20 0)', '7': 'Point (20 1)'}


class FakeCursor:
    """geometries and SRID of the customers / lines of the loaded version"""
    def execute(self, sql, args=None):
        self.sql = sql

    def fetchall(self):
        return [{'id': int(i), 'wkt': w} for i, w in WKT.items() if ('Point' in w) == ('.customers' in self.sql)]

    def fetchone(self):
        return {'srid': 2056}


def pair(lines):
    return {'supply': 1, 'return': 2, 'cid_weak': 7, 'customers': {'7': {'dp': 1e5, 'dp_sized': 0.9e5, 'dp_net': 4e4, 'epid': 1, 'time': 't'}},
            'lines': {lid: dict({'mdot': 1.0, 'mdot_max': 2.0, 'dp_spez': 50.0, 'pipe': 'DRE-50', 'pipe_new': 'DRE-50', 'changed': False}, **line)
                      for lid, line in lines.items()}}


SIZED = {'iteration': 1, 'outcome': 'changed', 'pairs': [pair({'3': {'d': 43.1, 'd_new': 37.2, 'pipe_new': 'DRE-40', 'changed': True},
                                                            '4': {'d': 43.1, 'd_new': 43.1}})]}
REFERENCE = {'iteration': 0, 'outcome': 'reference', 'pairs': [pair({'3': {'d': 43.1, 'd_new': 43.1}, '4': {'d': 43.1, 'd_new': 43.1}})]}
EARLIER = {'iteration': 2, 'outcome': 'converged', 'pairs': [pair({'3': {}, '4': {}})]}  # file without diameters


@pytest.fixture
def shown(qgis_app):
    yield
    removeSizingLayers()


def tree(iteration):
    """[(layer name, checked)] of the pair 1/2 of the iteration, top to bottom"""
    return [(node.layer().name(), node.itemVisibilityChecked()) for node in sizingGroup(iteration, '1/2').findLayers()]


def test_order_and_visibility(shown):
    layers = showIteration(FakeCursor(), {'versionName': 'v'}, SIZED, [REFERENCE, SIZED])
    assert {(layer.customProperty(SIZING_PROPERTY), layer.customProperty(PAIR_PROPERTY)) for layer in layers} == {(1, '1/2')}
    assert tree(1) == [(tr_msg('Customers – dp substation [bar]'), True), (tr_msg('Lines – inner diameter after sizing [mm]'), True),
                       (tr_msg('Lines – new pipes'), True), (tr_msg('Lines – design mass flow [kg/s]'), False)]
    diameters = QgsProject.instance().mapLayersByName(tr_msg('Lines – inner diameter after sizing [mm]'))[0]
    assert {f['id']: f['d_new'] for f in diameters.getFeatures()} == {3: 37.2, 4: 43.1}
    assert [c.label() for c in diameters.renderer().categories()][:2] == ['d_i = 37.2 mm', 'd_i = 43.1 mm']


def test_same_categories_in_every_iteration(shown):
    showIteration(FakeCursor(), {'versionName': 'v'}, REFERENCE, [REFERENCE, SIZED])
    showIteration(FakeCursor(), {'versionName': 'v'}, SIZED, [REFERENCE, SIZED])
    renderers = [layer.renderer() for layer in QgsProject.instance().mapLayers().values()
                 if layer.customProperty(SIZING_PROPERTY) is not None and 'd_new' == getattr(layer.renderer(), 'classAttribute', lambda: None)()]
    assert len(renderers) == 2
    reference, sized = ([(c.label(), c.symbol().color().name()) for c in r.categories()] for r in renderers)
    assert reference == sized


def test_reference_run_layers(shown):
    showIteration(FakeCursor(), {'versionName': 'v'}, REFERENCE)
    assert [name for name, _ in tree(0)] == [tr_msg('Customers – dp substation [bar]'), tr_msg('Lines – inner diameter [mm]'),
                                              tr_msg('Lines – design mass flow [kg/s]')]


def test_earlier_file_without_diameters(shown):
    showIteration(FakeCursor(), {'versionName': 'v'}, EARLIER)
    layer = QgsProject.instance().mapLayersByName(tr_msg('Lines – inner diameter after sizing [mm]'))[0]
    assert [c.label() for c in layer.renderer().categories()] == [tr_msg('no diameter')]
    assert all(f['d_new'] is None or str(f['d_new']) == 'NULL' for f in layer.getFeatures())
