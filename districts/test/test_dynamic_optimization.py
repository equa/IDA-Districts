# coding=utf-8
"""Dynamic pipe sizing on the template dynamic_optimization (an IDA Districts sample, <pathDistricts>\\Samples\\districts;
skipped without it): one water circuit (pair 1/2), two energy plants
(a flow-controlled heat source and a pressure-holding top-up plant). Create the project from the template, then a
reference run (iteration 0) of 1 January in a new child version, then the sizing as a second start
in the same child version (OpenSpec changes balance-pipe-pairs and sizing-simulation-period). The reference run
builds, simulates and loads the results itself.

    python -m pytest test/test_dynamic_optimization.py -v -s
    (DISTRICTS_TEST_DYNOPT_MAX_ITER=2, DISTRICTS_TEST_DYNOPT_TIMEOUT=7200 [s], --keep-projects)
"""
import os
import time
from types import SimpleNamespace

import pytest
from qgis.core import QgsProject
from qgis.PyQt.QtCore import QDateTime
from qgis.PyQt.QtWidgets import QMessageBox

from districts.dynamic_pipe_sizing import DATE_FORMAT
from districts.ida_ph import createNewProject
from districts.utility_functions.dialog import checkState, uncheckState
from districts.utility_functions.dynamic_sizing_results import PAIR_PROPERTY, SIZING_PROPERTY, iterationRows, loadIterations
from districts.utility_functions.files import loadNetworkSimData
from districts.utility_functions.translations import tr_msg

from .conftest import wait, wait_for_process, wait_until
from .test_workflow import delete_project, project_name_for

pytestmark = [pytest.mark.e2e, pytest.mark.ida]

TEMPLATE = 'dynamic_optimization'
PAIRS = [(1, 2, 70.0, 30.0)]
MAX_ITER = int(os.environ.get('DISTRICTS_TEST_DYNOPT_MAX_ITER', '2'))
TIMEOUT = int(os.environ.get('DISTRICTS_TEST_DYNOPT_TIMEOUT', '7200'))
PERIODS = {'calc_time_from': '2026-01-01 00:00:00', 'calc_time_to': '2026-01-02 00:00:00',
           'startup_time_from': '2026-01-01 00:00:00', 'startup_time_to': '2026-01-02 00:00:00'}


@pytest.fixture(scope='class')
def dynopt(request, districts_plugin, errors):
    plugin = districts_plugin
    if not os.path.exists(os.path.join(plugin.config['pathDistricts'], 'bin', 'ida-districts.exe')):
        pytest.skip('IDA Districts not installed in {}'.format(plugin.config['pathDistricts']))
    # delivered as an IDA Districts sample; a copy in the plugin's templates folder is used first
    if not any(os.path.isdir(os.path.join(folder, TEMPLATE)) for folder in
               (os.path.join(plugin.plugin_dir, 'templates'), os.path.join(plugin.config['pathDistricts'], 'Samples', 'districts'))):
        pytest.skip('template {} not found'.format(TEMPLATE))
    state = SimpleNamespace(plugin=plugin, project_name=project_name_for(TEMPLATE), sized_version=None, base_bundles=None)
    yield state
    if not request.config.getoption('--keep-projects'):
        delete_project(plugin, errors, state.project_name)


@pytest.mark.incremental
class TestDynamicOptimization:
    def test_create_project(self, dynopt, errors):
        plugin = dynopt.plugin
        plugin.showCreateNewProject()
        dlg = plugin.dlg_createNewProject
        dlg.project_name.setText(dynopt.project_name)
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
        assert plugin.config['projectName'] == dynopt.project_name
        assert plugin.config['versionName'] == 'base1'
        plugin.cur.execute('SELECT count(*) AS n FROM base1.energy_plants;')
        assert plugin.cur.fetchone()['n'] == 2
        # every junction and plant has its height above sea level (the z of its line ends, 22 to 29 m)
        plugin.cur.execute('SELECT min(ST_Z(geom)) AS z FROM (SELECT geom FROM base1.junctions UNION ALL SELECT geom FROM base1.energy_plants) p;')
        assert plugin.cur.fetchone()['z'] >= 20
        dynopt.base_bundles = bundles(plugin, 'base1')

    def test_reference_run(self, dynopt, errors, monkeypatch):
        """Reference run (iteration 0) of 1 January in a new child version: no pipe changes, then the run stops."""
        plugin = dynopt.plugin
        plugin.showDynamicPipeSizing()
        dlg = plugin.dlg_dynamicPipeSizing
        assert dlg.pairs() == (PAIRS, [])  # suggested from the connections of both energy plants
        for key, value in PERIODS.items():
            dlg.dateedit_period[key].setDateTime(QDateTime.fromString(value, DATE_FORMAT))
        dynopt.sized_version = 'base1_hb_{}'.format(time.strftime('%H%M%S'))
        dlg.rbtn_newVersion.setChecked(True)
        dlg.lineEdit_versionName.setText(dynopt.sized_version)
        dlg.checkBox_referenceRun.setChecked(True)
        monkeypatch.setattr(QMessageBox, 'question', lambda *args, **kwargs: QMessageBox.StandardButton.Yes)
        log = run(dlg)
        assert plugin.config['versionName'] == dynopt.sized_version

        summaries = loadIterations(plugin.config)
        assert [(s['iteration'], s['outcome']) for s in summaries] == [(0, 'reference')], log
        pair = summaries[0]['pairs'][0]
        assert (pair['supply'], pair['return']) == (1, 2)
        assert pair['n_changed'] == 0 and not any(line['changed'] for line in pair['lines'].values())
        # the top-up plant holds the pressure: the target customer has flow at its critical time
        assert not pair['target_no_flow'], log
        assert bundles(plugin, dynopt.sized_version) == dynopt.base_bundles  # no pipe changed
        sim_data = loadNetworkSimData(plugin.plugin_dir, plugin.config)
        assert {key: sim_data[key] for key in PERIODS} == PERIODS  # the simulated period is saved with the version
        # the sizing is the second start, in the same child version
        assert dlg.rbtn_overrideVersion.isChecked() and not dlg.checkBox_referenceRun.isChecked()
        assert dlg.table_iterations.rowCount() == 1
        errors.check()

    def test_dynamic_pipe_sizing(self, dynopt, errors, monkeypatch):
        """Second start: the sizing in the version of the reference run, iteration 0 is kept."""
        plugin = dynopt.plugin
        dlg = plugin.dlg_dynamicPipeSizing
        dlg.spin_maxIter.setValue(MAX_ITER)
        monkeypatch.setattr(QMessageBox, 'question', lambda *args, **kwargs: QMessageBox.StandardButton.Yes)
        log = run(dlg)
        assert plugin.config['versionName'] == dynopt.sized_version

        summaries = loadIterations(plugin.config)
        assert summaries[0]['outcome'] == 'reference' and summaries[-1]['outcome'] in ('converged', 'max_iter'), log
        assert [s['iteration'] for s in summaries] == list(range(len(summaries))) and len(summaries) > 1
        warning = tr_msg('  Warning: pair {}: target customer {} has almost no flow at its critical time ({:.3g} of {:.3g} kg/s); check the simulation period.')
        assert warning[:warning.index('{}', warning.index('{}') + 2)].format('1/2').strip() not in log, log
        for summary in summaries:
            print('iteration {}: {}'.format(summary['iteration'], iterationRows(summary)))
            (pair,) = summary['pairs']
            assert (pair['supply'], pair['return']) == (1, 2) and str(pair['cid_weak']) in pair['customers']
        path = os.path.join(plugin.config['pathProjects'], dynopt.project_name, 'versions', dynopt.sized_version)
        assert os.path.isfile(os.path.join(path, 'dynamic_sizing_iter1_c_lid_1_2.json'))
        assert dlg.table_iterations.rowCount() == len(summaries)
        # the parent version keeps its pipes
        assert bundles(plugin, 'base1') == dynopt.base_bundles

        shown = {(int(layer.customProperty(SIZING_PROPERTY)), layer.customProperty(PAIR_PROPERTY))
                 for layer in QgsProject.instance().mapLayers().values() if layer.customProperty(SIZING_PROPERTY) is not None}
        assert shown == {(s['iteration'], '1/2') for s in summaries}  # iteration 0 is still shown from the reference run
        # inner diameters: the changed lines got another diameter; one diameter layer per shown iteration
        changed = [line for s in summaries for line in s['pairs'][0]['lines'].values() if line['changed']]
        assert changed and all(line['d'] > 0 and line['d_new'] != line['d'] for line in changed)
        diameter_layers = [layer for layer in QgsProject.instance().mapLayers().values() if layer.customProperty(SIZING_PROPERTY) is not None
                           and layer.name() in (tr_msg('Lines – inner diameter after sizing [mm]'), tr_msg('Lines – inner diameter [mm]'))]
        assert sorted(int(layer.customProperty(SIZING_PROPERTY)) for layer in diameter_layers) == [s['iteration'] for s in summaries]
        dlg.close()
        errors.check()


def run(dlg):
    """Starts the dialog's run and waits for its end without error; returns the log."""
    dlg.btn_start.click()
    assert dlg.process_running, dlg.textEdit_log.toPlainText()
    wait_until(lambda: not dlg.process_running, TIMEOUT, lambda: 'still running:\n' + dlg.textEdit_log.toPlainText()[-3000:])
    wait(500)
    log = dlg.textEdit_log.toPlainText()
    print('\n' + log)
    assert dlg.progress.value() == 100, log
    return log


def bundles(plugin, version):
    """{line id: pipe bundle type} of the version"""
    plugin.cur.execute('SELECT id, pipe_bundle_type_id FROM "{}".lines;'.format(version))  # nosec B608
    return {row['id']: row['pipe_bundle_type_id'] for row in plugin.cur.fetchall()}
