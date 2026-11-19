"""Geometry rules of the statics model (change statics-model): no DB, no IDA."""
import math

import pytest

from districts.utility_functions import statics_model as sm


def curve(n, spacing, angle_deg):
    """Polyline with n interior vertices, each turning angle_deg (left), segments of the given length."""
    coords, heading, p = [(0.0, 0.0, 0.0)], 0.0, (0.0, 0.0)
    for _ in range(n + 1):
        p = (p[0] + spacing * math.cos(heading), p[1] + spacing * math.sin(heading))
        coords.append((p[0], p[1], 0.0))
        heading += math.radians(angle_deg)
    return coords


def test_height_difference_counts():
    coords = [(0, 0, 0), (10, 0, 0), (20, 0, 1)]
    vertices, _ = sm.classifyVertices(coords, True, 0.0761, sm.defaultParameters())
    assert vertices[0]['angle_deg'] == pytest.approx(5.71, abs=0.01)
    assert vertices[0]['bend_class'] == sm.BEND_PREFAB
    assert vertices[0]['radius_m'] == pytest.approx(1.5 * 0.0761)


@pytest.mark.parametrize('angle, rigid, expected', [
    (3.0, True, sm.BEND_KINK),
    (0.5, True, sm.BEND_NONE),
    (20.0, True, sm.BEND_PREFAB),
    (20.0, False, sm.BEND_ELASTIC),
    (0.5, False, sm.BEND_NONE),
])
def test_classes(angle, rigid, expected):
    vertices, _ = sm.classifyVertices(curve(1, 10.0, angle), rigid, 0.1143, sm.defaultParameters())
    assert vertices[0]['bend_class'] == expected
    assert vertices[0]['source'] == 'rule'


def test_flexible_radius_from_geometry():
    vertices, _ = sm.classifyVertices(curve(1, 10.0, 20.0), False, None, sm.defaultParameters())
    assert vertices[0]['radius_m'] == pytest.approx(10.0 / math.radians(20.0))


def test_digitised_curve_merged():
    vertices, not_merged = sm.classifyVertices(curve(10, 2.0, 0.5), True, 0.0603, sm.defaultParameters())
    assert not not_merged
    assert {v['bend_class'] for v in vertices} == {sm.BEND_ELASTIC}
    assert {v['source'] for v in vertices} == {'merge'}
    assert {v['bend_id'] for v in vertices} == {1}
    assert vertices[0]['radius_m'] == pytest.approx(2.0 / math.radians(0.5), rel=1e-6)


def test_run_too_tight_for_steel():
    vertices, not_merged = sm.classifyVertices(curve(4, 1.0, 4.0), True, 0.2191, sm.defaultParameters())
    assert [v['bend_class'] for v in vertices] == [sm.BEND_KINK] * 4
    assert not_merged[0]['vertex_indexes'] == [1, 2, 3, 4]
    assert not_merged[0]['radius_m'] == pytest.approx(1.0 / math.radians(4.0))


def test_run_too_tight_merged_for_flexible():
    vertices, not_merged = sm.classifyVertices(curve(4, 1.0, 4.0), False, None, sm.defaultParameters())
    assert not not_merged
    assert {v['source'] for v in vertices} == {'merge'}


def test_zigzag_not_merged():
    coords = [(0, 0, 0), (2, 0, 0), (4, 0.05, 0), (6, 0, 0), (8, 0.05, 0), (10, 0, 0)]
    vertices, _ = sm.classifyVertices(coords, True, 0.0603, sm.defaultParameters())
    assert all(v['source'] == 'rule' for v in vertices)


def test_spacing_breaks_run():
    coords = curve(2, 2.0, 0.8) + []
    params = dict(sm.defaultParameters(), merge_distance_m=1.0)
    vertices, _ = sm.classifyVertices(coords, True, 0.0603, params)
    assert all(v['source'] == 'rule' for v in vertices)


def test_clean_coordinates():
    assert sm.cleanCoordinates([(0, 0), (0, 0, 0), (1, 0, None)]) == [(0.0, 0.0, 0.0), (1.0, 0.0, 0.0)]


def test_snap_points():
    nodes = {1: (0.0, 0.0), 2: (10.0, 0.0), 3: (10.3, 0.0)}
    applied, ambiguous, unmatched = sm.snapPoints({7: (0.2, 0.0), 8: (10.15, 0.0), 9: (50.0, 0.0)}, nodes, 0.5)
    assert applied == {7: 1}
    assert ambiguous == [8]
    assert unmatched == [9]


def test_snap_sections():
    midpoints = {1: (5.0, 0.0), 2: (15.0, 0.0), 3: (5.0, 10.0)}
    applied, unmatched = sm.snapSections({4: [(0.0, 0.2), (20.0, 0.2)], 5: [(0.0, 30.0), (1.0, 30.0)]}, midpoints, 0.5)
    assert applied == {1: 4, 2: 4}
    assert unmatched == [5]


def test_default_sql_files_match_the_code():
    import os
    from districts.utility_functions import statics_db
    plugin_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    with open(os.path.join(plugin_dir, 'DB_versionTablesDefault.txt'), encoding='utf-8') as f:
        assert statics_db.STATICS_TABLES_SQL.replace('\r\n', '\n') in f.read().replace('\r\n', '\n')
    with open(os.path.join(plugin_dir, 'DB_projectTablesDefault.txt'), encoding='utf-8') as f:
        project = f.read().replace('\r\n', '\n')
    assert statics_db.STATICS_PARAMETERS_SQL.replace('\r\n', '\n') in project
    assert all("VALUES ('{}', {}".format(key, value) in project for key, (value, _, _) in sm.PARAMETER_DEFAULTS.items())


def test_network_build_not_shadowed():
    """districts.py imports two functions named buildModel; the network dialog must get the network one."""
    from districts import districts as plugin, ida_mosim
    from districts.utility_functions import statics_db
    assert plugin.buildModel is ida_mosim.buildModel
    assert plugin.buildStaticsModelTables is statics_db.buildModel
