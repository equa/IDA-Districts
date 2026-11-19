# coding=utf-8
"""Statics model (OpenSpec change statics-model) on a project from the template heating_network: tables and upgrade,
build, twin pipes, cover, skipped lines, failed build, overrides after a renumbered topology, model state, child
version, layer group.

    python -m pytest test/test_statics_build.py -v -s   (--keep-projects)
"""
from types import SimpleNamespace

import pytest

from districts.upgrade import upgradeVersionDB
from districts.utility_functions import statics_db
from districts.utility_functions.statics_model import BEND_PREFAB
from districts.utility_functions.translations import tr

from .test_workflow import HEATING, create_project, delete_project, project_name_for

pytestmark = [pytest.mark.e2e]

TABLES = ['statics_model_nodes', 'statics_model_sections', 'statics_model_pipes', 'statics_model_build', 'statics_points', 'statics_sections']


@pytest.fixture(scope='class')
def statics(request, districts_plugin, errors):
    state = SimpleNamespace(plugin=districts_plugin, project_name=project_name_for('statics_model'))
    yield state
    if not request.config.getoption('--keep-projects'):
        delete_project(districts_plugin, errors, state.project_name)


def rows(plugin, sql, args=None):
    plugin.cur.execute(sql, args)
    return plugin.cur.fetchall()


def one(plugin, sql, args=None):
    plugin.cur.execute(sql, args)
    return plugin.cur.fetchone()


def count(plugin, table):
    return one(plugin, 'SELECT count(*) AS n FROM "{}".{};'.format(plugin.config['versionName'], table))['n']  # nosec B608


def build(state):
    return statics_db.buildModel(state.plugin.cur, state.plugin.config['versionName'])


@pytest.mark.incremental
class TestStaticsModel:
    def test_create_project(self, statics, errors):
        create_project(statics.plugin, errors, statics.project_name, HEATING)
        statics.version = statics.plugin.config['versionName']
        assert count(statics.plugin, 'lines') > 0

    def test_old_version_upgraded(self, statics):
        plugin, v = statics.plugin, statics.version
        plugin.cur.execute(';'.join('DROP TABLE IF EXISTS "{}".{}'.format(v, t) for t in TABLES) + ';DROP TABLE IF EXISTS public.statics_parameters;')  # nosec B608
        upgradeVersionDB(plugin.cur, plugin.config)
        assert one(plugin, "SELECT count(*) AS n FROM information_schema.tables WHERE table_schema = %s AND table_name = ANY(%s);", (v, TABLES))['n'] == 6
        assert statics_db.readParameters(plugin.cur)['kink_max_deg'] == 5
        plugin.cur.execute("UPDATE public.statics_parameters SET value = 4 WHERE key = 'kink_max_deg';")
        upgradeVersionDB(plugin.cur, plugin.config)
        assert statics_db.readParameters(plugin.cur)['kink_max_deg'] == 4
        plugin.cur.execute("UPDATE public.statics_parameters SET value = 5 WHERE key = 'kink_max_deg';")

    def test_build(self, statics):
        plugin, v = statics.plugin, statics.version
        assert statics_db.modelState(plugin.cur, v) == statics_db.STATE_MISSING
        # a vertex with a bend in the longest line (the template lines may be straight)
        lid = one(plugin, 'SELECT id FROM "{}".lines ORDER BY ST_Length(geom) DESC LIMIT 1;'.format(v))['id']  # nosec B608
        # middle point moved sideways by 20 % of the end-to-end distance: about 44°
        plugin.cur.execute("""UPDATE "{}".lines SET geom = ST_MakeLine(ARRAY[ST_StartPoint(geom),
            ST_Translate(ST_LineInterpolatePoint(geom, 0.5), -0.2 * (ST_Y(ST_EndPoint(geom)) - ST_Y(ST_StartPoint(geom))),
                         0.2 * (ST_X(ST_EndPoint(geom)) - ST_X(ST_StartPoint(geom))), 0),
            ST_EndPoint(geom)]) WHERE id = %s;""".format(v), (lid,))  # nosec B608
        statics.bent_line = lid
        report = build(statics)
        assert statics_db.modelState(plugin.cur, v) == statics_db.STATE_CURRENT
        modelled = rows(plugin, """SELECT l.id, ST_NPoints(ST_RemoveRepeatedPoints(l.geom)) AS n,
            (SELECT count(*) FROM public.bundle_pipes bp WHERE bp.pipe_bundle_type_id = l.pipe_bundle_type_id) AS pipes
            FROM "{}".lines l WHERE l.pipe_bundle_type_id IS NOT NULL;""".format(v))  # nosec B608
        skipped = {s['line_id'] for s in report['skipped_lines']}
        modelled = [m for m in modelled if m['id'] not in skipped]
        assert count(plugin, 'statics_model_sections') == sum(m['n'] - 1 for m in modelled)
        assert report['counts']['sections'] == count(plugin, 'statics_model_sections')
        assert count(plugin, 'statics_model_pipes') == report['counts']['pipes']
        node = one(plugin, 'SELECT * FROM "{}".statics_model_nodes WHERE kind = %s AND vertex_index IS NOT NULL AND %s = ANY(line_ids);'.format(v), ('vertex', lid))  # nosec B608
        assert node['bend_class'] == BEND_PREFAB and node['source'] == 'rule' and float(node['angle_deg']) > 5

    def test_dimensions_and_cover(self, statics):
        plugin, v = statics.plugin, statics.version
        row = one(plugin, 'SELECT * FROM "{}".statics_model_pipes WHERE NOT twin LIMIT 1;'.format(v))  # nosec B608
        pipe = one(plugin, 'SELECT * FROM public.pipes WHERE id = %s;', (row['pipe_ids'][0],))
        layers = [float(r['thickness']) for r in rows(plugin, 'SELECT thickness FROM public.pipe_layers WHERE pipe_construction_id = %s ORDER BY sequence;',
                                                       (pipe['pipe_construction_id'],))]
        d = float(pipe['innerpipediameter'])
        assert float(row['d_inner_m'][0]) == pytest.approx(d)
        assert float(row['wall_m'][0]) == pytest.approx(layers[0])
        assert float(row['d_outer_m'][0]) == pytest.approx(d + 2 * layers[0])
        assert float(row['casing_d_m']) == pytest.approx(d + 2 * sum(layers))
        assert float(row['cover_m']) == pytest.approx(float(row['y_m']) - float(row['casing_d_m']) / 2)

    def test_twin_pipe(self, statics):
        plugin, v = statics.plugin, statics.version
        twin = one(plugin, """SELECT bp.pipe_bundle_type_id AS bid, p.casing_construction_id AS cid FROM public.bundle_pipes bp JOIN public.pipes p ON p.id = bp.pipe_id
            WHERE p.casing_construction_id IS NOT NULL GROUP BY 1, 2 HAVING count(*) = 2 AND
            (SELECT count(*) FROM public.bundle_pipes b2 WHERE b2.pipe_bundle_type_id = bp.pipe_bundle_type_id) = 2 LIMIT 1;""")
        assert twin is not None, 'the template has no twin pipe bundle'
        lid = one(plugin, 'SELECT min(id) AS id FROM "{}".lines WHERE id <> %s;'.format(v), (statics.bent_line,))['id']  # nosec B608
        plugin.cur.execute('UPDATE "{}".lines SET pipe_bundle_type_id = %s WHERE id = %s;'.format(v), (twin['bid'], lid))  # nosec B608
        assert statics_db.modelState(plugin.cur, v) == statics_db.STATE_OUT_OF_DATE
        build(statics)
        pipes = rows(plugin, 'SELECT * FROM "{}".statics_model_pipes WHERE line_id = %s;'.format(v), (lid,))  # nosec B608
        sections = one(plugin, 'SELECT count(*) AS n FROM "{}".statics_model_sections WHERE line_id = %s;'.format(v), (lid,))['n']  # nosec B608
        assert len(pipes) == sections and all(p['twin'] and len(p['pipe_ids']) == 2 for p in pipes)
        casing = sum(float(r['thickness']) for r in rows(plugin, 'SELECT thickness FROM public.pipe_layers WHERE pipe_construction_id = %s;', (twin['cid'],)))
        assert float(pipes[0]['casing_d_m']) == pytest.approx(2 * casing)

    def test_skipped_line_and_negative_cover(self, statics):
        plugin, v = statics.plugin, statics.version
        lid = one(plugin, 'SELECT max(id) AS id FROM "{}".lines WHERE id <> %s;'.format(v), (statics.bent_line,))['id']  # nosec B608
        plugin.cur.execute('UPDATE "{}".lines SET pipe_bundle_type_id = NULL WHERE id = %s;'.format(v), (lid,))  # nosec B608
        plugin.cur.execute("""INSERT INTO "{}".statics_sections (geom, cover_m) SELECT ST_Force2D(geom), -0.1 FROM "{}".lines WHERE id = %s;""".format(v, v),  # nosec B608
                           (statics.bent_line,))
        report = build(statics)
        assert {'line_id': lid, 'reason': 'no pipe bundle'} in report['skipped_lines']
        assert one(plugin, 'SELECT count(*) AS n FROM "{}".statics_model_pipes WHERE line_id = %s;'.format(v), (lid,))['n'] == 0  # nosec B608
        assert any(n['line_id'] == statics.bent_line and n['cover_m'] == pytest.approx(-0.1) for n in report['negative_cover'])
        plugin.cur.execute('DELETE FROM "{}".statics_sections;'.format(v))  # nosec B608

    def test_failed_build_keeps_the_old_model(self, statics, monkeypatch):
        plugin, v = statics.plugin, statics.version
        build(statics)
        before = [count(plugin, t) for t in statics_db.MODEL_TABLES]
        plugin.cur.execute('UPDATE "{}".lines SET pipe_bundle_type_id = 1 WHERE pipe_bundle_type_id IS NULL;'.format(v))  # nosec B608

        def fail(cur, schema):
            raise RuntimeError('fingerprint failed')
        monkeypatch.setattr(statics_db, 'fingerprint', fail)
        with pytest.raises(RuntimeError):
            build(statics)
        monkeypatch.undo()
        assert [count(plugin, t) for t in statics_db.MODEL_TABLES] == before

    def test_overrides_after_a_renumbered_topology(self, statics):
        plugin, v = statics.plugin, statics.version
        node = one(plugin, 'SELECT ST_X(geom) AS x, ST_Y(geom) AS y FROM "{}".statics_model_nodes WHERE kind = %s AND vertex_index IS NOT NULL AND %s = ANY(line_ids);'.format(v),  # nosec B608
                   ('vertex', statics.bent_line))
        plugin.cur.execute("""INSERT INTO "{}".statics_points (geom, kind, bend_class, radius_m)
            VALUES (ST_SetSRID(ST_MakePoint(%s, %s), %s), 'bend', 'elastic', 2) RETURNING id;""".format(v),  # nosec B608
                           (node['x'] + 0.2, node['y'], statics_db.versionSrid(plugin.cur, v)))
        point_id = plugin.cur.fetchone()['id']
        plugin.cur.execute("""INSERT INTO "{0}".statics_sections (geom, cover_m) SELECT ST_Translate(ST_Force2D(geom), 100000, 100000), 0.6
            FROM "{0}".lines WHERE id = %s RETURNING id;""".format(v), (statics.bent_line,))  # nosec B608
        unmatched = plugin.cur.fetchone()['id']
        plugin.cur.execute("""INSERT INTO "{0}".statics_sections (geom, cover_m) SELECT ST_Force2D(geom), 0.6
            FROM "{0}".lines WHERE id = %s RETURNING id;""".format(v), (statics.bent_line,))  # nosec B608
        cover = plugin.cur.fetchone()['id']
        # a regenerated topology numbers the lines anew
        plugin.cur.execute('UPDATE "{0}".lines SET id = id + 10000; UPDATE "{0}".junction_connections SET lid = lid + 10000;'.format(v))  # nosec B608
        new_line = statics.bent_line + 10000
        report = build(statics)
        moved = one(plugin, 'SELECT * FROM "{}".statics_model_nodes WHERE kind = %s AND vertex_index IS NOT NULL AND %s = ANY(line_ids);'.format(v), ('vertex', new_line))  # nosec B608
        assert (moved['source'], moved['bend_class'], moved['override_id'], float(moved['radius_m'])) == ('override', 'elastic', point_id, 2)
        assert report['points_applied'] == [point_id]
        assert report['sections_unmatched'] == [unmatched] and report['sections_applied'] == [cover]
        assert one(plugin, 'SELECT count(*) AS n FROM "{}".statics_sections WHERE id = %s;'.format(v), (unmatched,))['n'] == 1  # nosec B608
        covers = {float(r['cover_m']) for r in rows(plugin, 'SELECT cover_m FROM "{}".statics_model_pipes WHERE line_id = %s;'.format(v), (new_line,))}  # nosec B608
        assert covers == {0.6}

    def test_model_state(self, statics):
        plugin, v = statics.plugin, statics.version
        assert statics_db.modelState(plugin.cur, v) == statics_db.STATE_CURRENT
        plugin.cur.execute('UPDATE "{}".lines SET geom = ST_Translate(geom, 0.01, 0) WHERE id = %s;'.format(v), (statics.bent_line + 10000,))  # nosec B608
        assert statics_db.modelState(plugin.cur, v) == statics_db.STATE_OUT_OF_DATE
        build(statics)
        assert statics_db.modelState(plugin.cur, v) == statics_db.STATE_CURRENT
        plugin.cur.execute("""INSERT INTO "{}".statics_points (geom, kind) VALUES (ST_SetSRID(ST_MakePoint(0, 0), %s), 'valve');""".format(v),  # nosec B608
                           (statics_db.versionSrid(plugin.cur, v),))
        assert statics_db.modelState(plugin.cur, v) == statics_db.STATE_OUT_OF_DATE
        build(statics)
        assert statics_db.modelState(plugin.cur, v) == statics_db.STATE_CURRENT

    def test_child_version(self, statics):
        from districts.utility_functions.hydraulic_balancing import createChildVersion
        plugin, v = statics.plugin, statics.version
        child = v + '_c'
        createChildVersion(plugin.cur, plugin.config, plugin.plugin_dir, child, 'statics child')
        for table in TABLES:
            n = one(plugin, 'SELECT count(*) AS n FROM "{}".{};'.format(child, table))['n']  # nosec B608
            assert n == count(plugin, table), table

    def test_layer_group(self, statics, errors):
        from qgis.core import QgsCategorizedSymbolRenderer, QgsProject
        plugin = statics.plugin
        plugin.buildStaticsModel()
        errors.check()
        assert plugin.dlg_staticsReport.isVisible()
        plugin.dlg_staticsReport.close()
        plugin.buildStaticsModel()
        plugin.dlg_staticsReport.close()
        root = QgsProject.instance().layerTreeRoot()
        groups = [g for g in root.findGroups() if g.name() == tr('@default', 'statics_model')]
        assert len(groups) == 1
        layers = [child.layer() for child in groups[0].findLayers()]
        assert len(layers) == 4 and all(layer.isValid() for layer in layers)
        nodes = [layer for layer in layers if layer.customProperty('districts_statics_model') == 'statics_model_nodes'][0]
        assert isinstance(nodes.renderer(), QgsCategorizedSymbolRenderer) and nodes.renderer().classAttribute() == 'bend_class'
        from districts.utility_functions.statics_layers import removeStaticsLayers
        removeStaticsLayers()
