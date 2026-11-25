# coding=utf-8
"""Ground collector routes (OpenSpec change ground-collector-routes, tasks 8.2-8.4) on a project from the template
heating_network: upgrade of an old project, resources and their line types, defaults per line, export/import, the
network model of a collector line, sizing and cost optimization leaving it, and with IDA Districts its simulation,
results and key figures.

    python -m pytest test/test_ground_collector_routes.py -v -s   (--keep-projects)
"""
import os
import re
from types import SimpleNamespace

import psycopg2
import pytest

from districts.ida_mosim import buildModel
from districts.upgrade import upgradeVersionDB
from districts.utility_functions import ground_collectors as gc
from districts.utility_functions.dialog import closeDialog
from districts.utility_functions.ground_collector_contract import CONTRACT_VERSION
from districts.utility_functions.hydraulic_balancing import getLineData
from districts.utility_functions.set_pipes import applyPipes

from .conftest import wait_for_process
from .test_workflow import HEATING, create_project, delete_project, project_name_for

pytestmark = [pytest.mark.e2e]


@pytest.fixture(scope='class')
def routes(request, districts_plugin, errors):
    state = SimpleNamespace(plugin=districts_plugin, project_name=project_name_for('ground_collectors'), simulated=False)
    yield state
    if not request.config.getoption('--keep-projects'):
        delete_project(districts_plugin, errors, state.project_name)


def one(plugin, sql, args=None):
    plugin.cur.execute(sql, args)
    return plugin.cur.fetchone()


def versionOf(plugin):
    return plugin.config['versionName']


def builtModel(plugin):
    path = os.path.join(plugin.config['pathProjects'] + plugin.config['projectName'], 'versions', versionOf(plugin), 'network_1.idm')
    with open(path, encoding='utf-8', errors='replace') as f:
        return f.read()


def build(plugin, errors):
    plugin.showBuildModel()
    dlg = plugin.dlg_buildModel
    dlg.combo_network_models.setItemChecked(1, True)
    dlg.combo_submodels.setItemChecked(1, True)
    buildModel(dlg, plugin)
    wait_for_process(dlg, timeout=180)
    closeDialog(dlg)
    errors.check()


@pytest.mark.incremental
class TestGroundCollectorRoutes:
    def test_create_project(self, routes, errors):
        create_project(routes.plugin, errors, routes.project_name, HEATING)

    def test_upgrade_of_an_old_project(self, routes):
        plugin = routes.plugin
        v = versionOf(plugin)
        plugin.cur.execute('ALTER TABLE public.line_types DROP COLUMN ground_collector_id; DROP TABLE public.ground_collectors;'
                           'ALTER TABLE "{v}".lines DROP COLUMN n_loops, DROP COLUMN t_mean_init;'.format(v=v))  # nosec B608
        upgradeVersionDB(plugin.cur, plugin.config)
        upgradeVersionDB(plugin.cur, plugin.config)  # a second load changes nothing
        assert one(plugin, "SELECT to_regclass('public.ground_collectors') IS NOT NULL AS ok;")['ok']
        plugin.cur.execute("SELECT column_name FROM information_schema.columns WHERE table_schema = %s AND table_name = 'lines';", (v,))
        assert {'n_loops', 't_mean_init'} <= {r['column_name'] for r in plugin.cur.fetchall()}
        assert gc.collectorLines(plugin.cur, v) == {}

    def test_resources_and_line_types(self, routes):
        plugin = routes.plugin
        v = versionOf(plugin)
        line = one(plugin, """SELECT l.id, l.type, l.pipe_bundle_type_id AS bundle FROM "{}".lines l
            WHERE (SELECT count(*) FROM public.bundle_pipes bp WHERE bp.pipe_bundle_type_id = l.pipe_bundle_type_id) >= 2
            ORDER BY l.id LIMIT 1;""".format(v))  # nosec B608
        pipe = one(plugin, 'SELECT pipe_id FROM public.bundle_pipes WHERE pipe_bundle_type_id = %s ORDER BY sequence LIMIT 1;', (line['bundle'],))
        row = {'name': 'ring test', 'preset': 'horizontal_ring', 'preset_inputs': gc.PRESET_DEFAULTS['horizontal_ring'],
               'pipe_id': pipe['pipe_id'], 'loop_sequence': 1, 't_mean_init': 4.0, 'cost_trench_eur7m': 30,
               'cost_loop_eur7m': 2, 'n_sections': 2}
        collector_id = gc.saveCollector(plugin.cur, row)
        type_id = one(plugin, 'SELECT id FROM public.line_types WHERE ground_collector_id = %s;', (collector_id,))['id']
        assert one(plugin, 'SELECT type FROM public.line_types WHERE id = %s;', (type_id,))['type'] == 'ring test'
        gc.saveCollector(plugin.cur, dict(row, id=collector_id, name='ring'))  # renamed: the type keeps its id
        assert one(plugin, 'SELECT type FROM public.line_types WHERE id = %s;', (type_id,))['type'] == 'ring'
        assert float(one(plugin, 'SELECT lambda_w7mk FROM public.ground_collectors WHERE id = %s;', (collector_id,))['lambda_w7mk']) == 1.5
        plugin.cur.execute('UPDATE "{}".lines SET type = %s WHERE id = %s;'.format(v), (type_id, line['id']))  # nosec B608
        assert gc.isCollectorLine(plugin.cur, v, line['id'])
        with pytest.raises(gc.CollectorInUse) as used:
            gc.deleteCollector(plugin.cur, collector_id, [v])
        assert used.value.line_ids == {v: [line['id']]}
        with pytest.raises(psycopg2.errors.ForeignKeyViolation):  # also the database refuses
            plugin.cur.execute('DELETE FROM public.ground_collectors WHERE id = %s;', (collector_id,))
        spare = gc.saveCollector(plugin.cur, dict(row, name='spare'))
        gc.deleteCollector(plugin.cur, spare, [v])
        assert one(plugin, 'SELECT count(*) AS n FROM public.line_types WHERE ground_collector_id = %s;', (spare,))['n'] == 0
        routes.lid, routes.collector_id, routes.loop_pipe = line['id'], collector_id, pipe['pipe_id']

    def test_defaults_per_line(self, routes):
        plugin = routes.plugin
        v = versionOf(plugin)
        line = gc.collectorLines(plugin.cur, v)[routes.lid]
        assert (line['n_loops'], line['t_mean_init'], line['loop_sequence'], line['n_sections']) == (1, 4.0, 1, 2)
        plugin.cur.execute('UPDATE "{}".lines SET n_loops = 3 WHERE id = %s;'.format(v), (routes.lid,))  # nosec B608
        assert gc.collectorLines(plugin.cur, v)[routes.lid]['n_loops'] == 3
        plugin.cur.execute('UPDATE "{}".lines SET n_loops = NULL WHERE id = %s;'.format(v), (routes.lid,))  # nosec B608
        assert gc.collectorLines(plugin.cur, v)[routes.lid]['n_loops'] == 1  # empty: one loop
        plugin.cur.execute('UPDATE "{}".lines SET n_loops = 2 WHERE id = %s;'.format(v), (routes.lid,))  # nosec B608

    def test_export_and_import(self, routes):
        plugin = routes.plugin
        exported = gc.exportCollectors(plugin.cur, ['ring'])
        assert list(exported) == ['ring'] and exported['ring']['pipe_name'] and exported['ring']['liquid_name'] == 'Water'
        assert gc.importCollectors(plugin.cur, {'ring copy': dict(exported['ring'], fits={'x': {'fit_version': 0}})}) == []
        copy = one(plugin, "SELECT * FROM public.ground_collectors WHERE name = 'ring copy';")
        assert copy['pipe_id'] == routes.loop_pipe and copy['fits'] == {'x': {'fit_version': 0}} and copy['n_sections'] == 2
        assert one(plugin, "SELECT count(*) AS n FROM public.line_types WHERE type = 'ring copy' AND ground_collector_id = %s;", (copy['id'],))['n'] == 1
        # importing again replaces by name; a missing loop pipe is reported
        missing = gc.importCollectors(plugin.cur, {'ring copy': dict(exported['ring'], pipe_name='no such pipe', n_sections=4)})
        assert missing == ['ring copy']
        again = one(plugin, "SELECT id, pipe_id, n_sections FROM public.ground_collectors WHERE name = 'ring copy';")
        assert (again['id'], again['pipe_id'], again['n_sections']) == (copy['id'], None, 4)
        gc.deleteCollector(plugin.cur, copy['id'], [versionOf(plugin)])

    def test_model_checks(self, routes, monkeypatch):
        from districts.utility_functions.model_checks import runChecks
        plugin = routes.plugin
        monkeypatch.setattr(gc, 'groundMoContractVersion', lambda path: None)
        result = runChecks(plugin.cur, plugin.config, 'qgis', plugin_dir=plugin.plugin_dir)
        rules = {f['rule']: f for f in result['findings']}
        assert rules['ground_collector_library']['severity'] == 'error'
        assert rules['ground_collector_fit']['severity'] == 'info'  # fitted at the first build
        assert 'ground_collector_line' not in rules

    def test_model_build(self, routes, errors, monkeypatch):
        """the collector line as GroundCollector + GroundSurface, the other pipe of its bundle as FDpipebundle"""
        import districts.invoke_network as invoke_network
        plugin = routes.plugin
        if gc.groundMoContractVersion(plugin.config['pathDistricts']) != CONTRACT_VERSION:
            monkeypatch.setattr(invoke_network, 'groundMoContractVersion', lambda path: CONTRACT_VERSION)
        build(plugin, errors)
        idm, lid = builtModel(plugin), routes.lid
        assert re.search(r'\(MODEL :N "Collector_{}" :T \|GroundCollector\|\)'.format(lid), idm)
        assert re.search(r'\(MODEL :N "CollectorSurface_{}" :T \|GroundSurface\|\)'.format(lid), idm)
        assert '(("Collector_{0}" |surface|) ("CollectorSurface_{0}" |ground|) 0 0 NIL)'.format(lid) in idm
        assert re.search(r'\("Collector_{}" \|liq[12]\|\)'.format(lid), idm)
        bundle = idm[idm.index('(MODEL :N "Pipebundle_{}"'.format(lid)):]
        assert bundle.split('\n')[1].strip() == '(:PAR :N |npipes| :V 1)'
        collector = idm[idm.index('(MODEL :N "Collector_{}"'.format(lid)):]
        assert re.search(r'\(:PAR :N \|TStartLoc\| :V #\([-\d.e ]+\)\)', collector)
        assert re.search(r'\(:VAR :N \|TLoc\| :V #\([-\d.e ]+\) :L', collector)
        assert '(:PAR :N |nSections| :V 2)' in collector and '(:PAR :N |nLoops| :V 2)' in collector
        # the liquid of the collector type (default water, freezing point 0 degC), not the network's
        assert '(:PAR :N |liqType| :V |Water|)' in collector and '(:PAR :N |TFreeze| :V 0)' in collector
        assert 'Line_coll_{}'.format(lid) in idm  # requested output coll_lines (on in the template)
        # results macro: the extracted heat in the heat balance and its own meter (heatbalance_system, qcoll_kpi)
        folder = os.path.join(plugin.config['pathProjects'] + plugin.config['projectName'], 'versions', versionOf(plugin), 'network_1')
        macro = open(os.path.join(folder, 'results-macro_1.idm'), encoding='utf-8', errors='replace').read()
        assert '(:EO :N "qcollectors" :T ADDER)' in macro and '(1 :SYSTEM "Collector_{}" |QExtracted|)'.format(lid) in macro
        assert ':L "heatbalance_outputfile" :AS "Qcollectors"' in macro and '"Qcoll_kpi_outputfile"' in macro
        assert ':SLOT ("qcollectors")' in open(os.path.join(folder, 'results-macro_1.idc'), encoding='utf-8', errors='replace').read()
        assert gc.cachedFit(plugin.cur, gc.readCollectors(plugin.cur)[routes.collector_id],
                            invoke_network.loadModellingSettings(plugin.plugin_dir, plugin.config))['accepted']

    def test_sizing_leaves_the_collector(self, routes):
        plugin = routes.plugin
        v = versionOf(plugin)
        assert routes.lid not in getLineData(plugin.cur, plugin.config, None, sequences=(1, 2))
        bundle = one(plugin, 'SELECT pipe_bundle_type_id AS b FROM "{}".lines WHERE id = %s;'.format(v), (routes.lid,))['b']  # nosec B608
        other = one(plugin, 'SELECT id FROM public.pipe_bundle_types WHERE id <> %s ORDER BY id LIMIT 1;', (bundle,))['id']
        assert applyPipes(plugin.cur, v, {'bundles': {routes.lid: other}}) == (0, [])
        assert one(plugin, 'SELECT pipe_bundle_type_id AS b FROM "{}".lines WHERE id = %s;'.format(v), (routes.lid,))['b'] == bundle  # nosec B608

    @pytest.mark.ida
    def test_simulation_results_and_key_figures(self, routes, errors):
        """a short simulation: collector results per section, the heat balance adder, the key figures"""
        from districts.ida_mosim import runModel
        from districts.ida_rv import loadResults
        from districts.utility_functions.version_kpis import collectorKpis
        from districts.utility_functions.translations import tr_msg
        plugin = routes.plugin
        if not os.path.exists(os.path.join(plugin.config['pathDistricts'], 'bin', 'ida-districts.exe')):
            pytest.skip('IDA Districts not installed in {}'.format(plugin.config['pathDistricts']))
        if gc.groundMoContractVersion(plugin.config['pathDistricts']) != CONTRACT_VERSION:
            pytest.skip('GroundMo with contract version {} not installed'.format(CONTRACT_VERSION))
        build(plugin, errors)
        plugin.showRunModel()
        dlg = plugin.dlg_runModel
        dlg.combo_submodels.setItemChecked(1, checked=True)
        runModel(dlg, plugin.plugin_dir, plugin.config)
        wait_for_process(dlg, timeout=600)
        errors.check()
        assert dlg.status_bar.currentMessage() == tr_msg('Simulation finished'), dlg.status_bar.currentMessage()
        plugin.showLoadResults()
        dlg = plugin.dlg_loadResults
        dlg.combo_submodels.setItemChecked(1, True)
        loadResults(dlg, plugin)
        wait_for_process(dlg, timeout=300)
        closeDialog(dlg)
        errors.check()
        v, lid = versionOf(plugin), routes.lid
        sections = one(plugin, 'SELECT count(DISTINCT segment) AS n, count(DISTINCT time) AS t FROM "{}".line_s_coll_tloc WHERE fid = %s;'.format(v), (lid,))  # nosec B608
        assert sections['n'] == 2 and sections['t'] > 1
        extracted = one(plugin, 'SELECT avg("$coll_qextracted") AS q FROM "{}".line_s_coll_qextracted WHERE fid = %s;'.format(v), (lid,))['q']  # nosec B608
        assert extracted is not None
        assert one(plugin, 'SELECT qcoll FROM "{}".kpi_1;'.format(v))['qcoll'] is not None  # nosec B608
        kpis = collectorKpis(plugin.cur, plugin.config)
        assert kpis['ring']['trench_length']['value'] > 0 and kpis['ring']['t_out_min']['value'] is not None
        assert kpis['total']['lines'] == 1
