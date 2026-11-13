# coding=utf-8
"""Dynamic pipe sizing with supply/return pairs on the IDA Districts sample hc_network (heating 1/3 on all lines,
cooling 2/4 on the lines with four pipes): create the project from the template, build the network model, simulate,
load the results and run the dynamic pipe sizing in a child version (OpenSpec change balance-pipe-pairs).

The template is taken from the IDA Districts installation (<pathDistricts>\\Samples\\districts\\hc_network).
    python -m pytest test/test_hc_network_sizing.py -v -s
    (DISTRICTS_TEST_HC_MAX_ITER=2, DISTRICTS_TEST_HC_TIMEOUT=7200 [s], --keep-projects)
"""
import os
import time
from types import SimpleNamespace

import pytest
from qgis.core import QgsProject
from qgis.PyQt.QtWidgets import QMessageBox

from districts.ida_mosim import buildModel, runModel
from districts.ida_ph import createNewProject
from districts.ida_rv import loadResults
from districts.utility_functions.dialog import checkState, closeDialog, uncheckState
from districts.utility_functions.dynamic_sizing_results import PAIR_PROPERTY, SIZING_PROPERTY, iterationRows, loadIterations
from districts.utility_functions.translations import tr_msg

from .conftest import wait, wait_for_process, wait_until
from .test_workflow import delete_project, project_name_for, table_names

pytestmark = [pytest.mark.e2e, pytest.mark.ida]

TEMPLATE = 'hc_network'
PAIRS = [(1, 3, 70.0, 30.0), (2, 4, 10.0, 18.0)]
MAX_ITER = int(os.environ.get('DISTRICTS_TEST_HC_MAX_ITER', '2'))
TIMEOUT = int(os.environ.get('DISTRICTS_TEST_HC_TIMEOUT', '7200'))


@pytest.fixture(scope='class')
def hc(request, districts_plugin, errors):
    plugin = districts_plugin
    if not os.path.exists(os.path.join(plugin.config['pathDistricts'], 'bin', 'ida-districts.exe')):
        pytest.skip('IDA Districts not installed in {}'.format(plugin.config['pathDistricts']))
    if not os.path.isdir(os.path.join(plugin.config['pathDistricts'], 'Samples', 'districts', TEMPLATE)):
        pytest.skip('IDA Districts sample {} not found'.format(TEMPLATE))
    state = SimpleNamespace(plugin=plugin, project_name=project_name_for(TEMPLATE), sized_version=None)
    yield state
    if not request.config.getoption('--keep-projects'):
        delete_project(plugin, errors, state.project_name)


def bundle_sizes(plugin, version):
    """{line id: number of pipes of its bundle} of the version"""
    plugin.cur.execute("""SELECT l.id, count(bp.id) AS n FROM "{}".lines l
    LEFT JOIN public.bundle_pipes bp ON bp.pipe_bundle_type_id = l.pipe_bundle_type_id GROUP BY l.id;""".format(version))  # nosec B608
    return {row['id']: row['n'] for row in plugin.cur.fetchall()}


@pytest.mark.incremental
class TestHcNetworkSizing:
    def test_create_project(self, hc, errors):
        plugin = hc.plugin
        plugin.showCreateNewProject()
        dlg = plugin.dlg_createNewProject
        dlg.project_name.setText(hc.project_name)
        index = dlg.selectTemplate.findData(TEMPLATE)
        assert index >= 0, 'template {} not offered'.format(TEMPLATE)
        dlg.selectTemplate.setCurrentIndex(index)
        dlg.checkbox_db_defaultValues.setCheckState(uncheckState())
        dlg.checkbox_invokedFeatures.setCheckState(checkState())
        dlg.checkbox_prn.setCheckState(checkState())
        dlg.checkbox_DBResults.setCheckState(uncheckState())
        createNewProject(dlg, plugin)
        wait_for_process(dlg, timeout=180)
        wait_for_process(plugin.dlg, timeout=180)  # loading the version base1
        errors.check()
        assert plugin.config['projectName'] == hc.project_name
        assert plugin.config['versionName'] == 'base1'
        sizes = bundle_sizes(plugin, 'base1')
        assert set(sizes.values()) == {2, 4}, sizes

    def test_build_network_model(self, hc, errors):
        plugin = hc.plugin
        plugin.showBuildModel()
        dlg = plugin.dlg_buildModel
        dlg.combo_network_models.setItemChecked(1, True)
        dlg.combo_submodels.setItemChecked(1, True)
        buildModel(dlg, plugin)
        wait_for_process(dlg, timeout=300)
        closeDialog(dlg)
        errors.check()

    def test_run_simulation(self, hc, errors):
        plugin = hc.plugin
        plugin.showRunModel()
        dlg = plugin.dlg_runModel
        dlg.combo_submodels.setItemChecked(1, checked=True)
        runModel(dlg, plugin.plugin_dir, plugin.config)
        wait_for_process(dlg, timeout=TIMEOUT)
        errors.check()
        assert dlg.status_bar.currentMessage() == tr_msg('Simulation finished'), \
            "simulation status: '{}'".format(dlg.status_bar.currentMessage())

    def test_load_results(self, hc, errors):
        plugin = hc.plugin
        plugin.showLoadResults()
        dlg = plugin.dlg_loadResults
        dlg.combo_submodels.setItemChecked(1, True)
        loadResults(dlg, plugin)
        wait_for_process(dlg, timeout=600)
        closeDialog(dlg)
        errors.check()
        tables = set(table_names(plugin, 'line\\_s\\_%'))
        # the sizing needs the mass flows of the supply pipes and the temperatures of all pipes of both pairs
        missing = {'line_s_mdot$1', 'line_s_mdot$2'} | {'line_s_temp${}'.format(seq) for seq in (1, 2, 3, 4)}
        assert not missing - tables, sorted(missing - tables)

    def test_dynamic_pipe_sizing(self, hc, errors, monkeypatch):
        plugin = hc.plugin
        plugin.showDynamicPipeSizing()
        dlg = plugin.dlg_dynamicPipeSizing
        pairs, problems = dlg.pairs()
        assert (pairs, problems) == (PAIRS, [])  # suggested from the connections of the energy plant
        hc.sized_version = 'base1_hb_{}'.format(time.strftime('%H%M%S'))
        dlg.rbtn_newVersion.setChecked(True)
        dlg.lineEdit_versionName.setText(hc.sized_version)
        dlg.spin_maxIter.setValue(MAX_ITER)
        monkeypatch.setattr(QMessageBox, 'question', lambda *args, **kwargs: QMessageBox.StandardButton.Yes)

        dlg.btn_start.click()
        assert dlg.process_running, dlg.textEdit_log.toPlainText()
        wait_until(lambda: not dlg.process_running, TIMEOUT, lambda: 'still running:\n' + dlg.textEdit_log.toPlainText()[-3000:])
        wait(500)
        log = dlg.textEdit_log.toPlainText()
        print('\n' + log)
        assert dlg.progress.value() == 100, log  # converged or max. number of iterations, no error
        assert plugin.config['versionName'] == hc.sized_version

        summaries = loadIterations(plugin.config)
        assert summaries and summaries[-1]['outcome'] in ('converged', 'max_iter'), log
        for summary in summaries:
            print('iteration {}: {}'.format(summary['iteration'], iterationRows(summary)))
            assert [(p['supply'], p['return']) for p in summary['pairs']] == [(1, 3), (2, 4)]
            heating, cooling = summary['pairs']
            # the cooling pair is balanced on the four-pipe lines only, the heating-only customers are skipped
            assert 0 < len(cooling['lines']) < len(heating['lines'])
            assert cooling['n_customers_skipped'] > 0 and heating['n_customers_skipped'] == 0
            for pair in summary['pairs']:
                assert str(pair['cid_weak']) in pair['customers']
        path = os.path.join(plugin.config['pathProjects'], hc.project_name, 'versions', hc.sized_version)
        assert all(os.path.isfile(os.path.join(path, 'dynamic_sizing_iter1_c_lid_{}.json'.format(pair))) for pair in ('1_3', '2_4'))
        assert dlg.table_iterations.rowCount() == 2 * len(summaries)

        # a changed line keeps all its pipes (the four-pipe lines were cut to two pipes before the pairs)
        assert bundle_sizes(plugin, hc.sized_version) == bundle_sizes(plugin, 'base1')

        # map: one subgroup per pair in every iteration
        shown = {(int(layer.customProperty(SIZING_PROPERTY)), layer.customProperty(PAIR_PROPERTY))
                 for layer in QgsProject.instance().mapLayers().values() if layer.customProperty(SIZING_PROPERTY) is not None}
        assert shown == {(s['iteration'], label) for s in summaries for label in ('1/3', '2/4')}
        dlg.close()
        errors.check()
