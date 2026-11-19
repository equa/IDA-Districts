"""Boreholes left out of the borehole fields: the warnings of checkBoreholes (at the network build) and
getTransformedBoreholeInfo reading only boreholes with a point."""
from districts.boreholes import checkBoreholes, getTransformedBoreholeInfo


class FakeCursor:
    def __init__(self, rows):
        self.rows = rows
        self.sql = []

    def execute(self, sql):
        self.sql.append(sql)

    def fetchall(self):
        return self.rows


def test_check_boreholes_groups_the_ids_by_problem():
    cur = FakeCursor([{'id': 3, 'problem': 'point'}, {'id': 7, 'problem': 'plant'}, {'id': 9, 'problem': 'point'},
                      {'id': 12, 'problem': 'plant_id'}])
    warnings = checkBoreholes(cur, 'v1')
    assert warnings == [
        'Boreholes without a point (layer boreholes), not part of a borehole field: ID 3, 9',
        'Boreholes without plant_id (layer boreholes), not part of a borehole field: ID 12',
        'Boreholes whose plant_id is no energy plant (layer boreholes), not part of a borehole field: ID 7',
    ]
    assert '"v1".boreholes' in cur.sql[0] and '"v1".energy_plants' in cur.sql[0]


def test_check_boreholes_without_problems():
    assert checkBoreholes(FakeCursor([]), 'v1') == []


def test_borehole_field_query_skips_boreholes_without_a_point():
    cur = FakeCursor([{'id': 1, 'x': 10.0, 'y': 0.0, 'z': 0.0, 'group': 1, 'mir': False},
                      {'id': 2, 'x': 20.0, 'y': 0.0, 'z': 0.0, 'group': 1, 'mir': False}])
    result = getTransformedBoreholeInfo(cur, 1, {'versionName': 'v1'})
    assert 'geom IS NOT NULL AND NOT ST_IsEmpty(geom)' in cur.sql[0]
    assert [(p['id'], p['x']) for p in result] == [(1, -5.0), (2, 5.0)]
