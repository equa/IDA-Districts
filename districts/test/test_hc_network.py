# coding=utf-8
"""The IDA Districts sample hc_network (heating 1/3 on all lines, cooling 2/4 on the lines with four pipes): create the
project from the template, build the network model, simulate and load the results. The dynamic pipe sizing is tested
on the template dynamic_optimization (test_dynamic_optimization.py): this sample has only a flow-controlled plant and
no pressure-holding one, so its network pressure loss is negative at every time step.

The template is taken from the IDA Districts installation (<pathDistricts>\\Samples\\districts\\hc_network).
    python -m pytest test/test_hc_network.py -v -s
    (DISTRICTS_TEST_HC_TIMEOUT=7200 [s], --keep-projects)
"""
import os
from types import SimpleNamespace

import pytest
from qgis.PyQt.QtCore import QDateTime

from districts.dynamic_pipe_sizing import DATE_FORMAT
from districts.ida_mosim import buildModel, runModel
from districts.ida_ph import createNewProject
from districts.ida_rv import loadResults
from districts.utility_functions.dialog import checkState, closeDialog, uncheckState
from districts.utility_functions.translations import tr_msg

from .conftest import wait_for_process
from .test_workflow import delete_project, project_name_for, table_names

pytestmark = [pytest.mark.e2e, pytest.mark.ida]

TEMPLATE = 'hc_network'
TIMEOUT = int(os.environ.get('DISTRICTS_TEST_HC_TIMEOUT', '7200'))
PERIOD = ('2026-01-01 00:00:00', '2026-01-02 00:00:00')  # calculation and start-up period


@pytest.fixture(scope='class')
def hc(request, districts_plugin, errors):
    plugin = districts_plugin
    if not os.path.exists(os.path.join(plugin.config['pathDistricts'], 'bin', 'ida-districts.exe')):
        pytest.skip('IDA Districts not installed in {}'.format(plugin.config['pathDistricts']))
    if not os.path.isdir(os.path.join(plugin.config['pathDistricts'], 'Samples', 'districts', TEMPLATE)):
        pytest.skip('IDA Districts sample {} not found'.format(TEMPLATE))
    state = SimpleNamespace(plugin=plugin, project_name=project_name_for(TEMPLATE))
    yield state
    if not request.config.getoption('--keep-projects'):
        delete_project(plugin, errors, state.project_name)


def bundle_sizes(plugin, version):
    """{line id: number of pipes of its bundle} of the version"""
    plugin.cur.execute("""SELECT l.id, count(bp.id) AS n FROM "{}".lines l
    LEFT JOIN public.bundle_pipes bp ON bp.pipe_bundle_type_id = l.pipe_bundle_type_id GROUP BY l.id;""".format(version))  # nosec B608
    return {row['id']: row['n'] for row in plugin.cur.fetchall()}


@pytest.mark.incremental
class TestHcNetwork:
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
        assert set(bundle_sizes(plugin, 'base1').values()) == {2, 4}

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
        for edit in (dlg.dateedit_calcFrom, dlg.dateedit_startupFrom):
            edit.setDateTime(QDateTime.fromString(PERIOD[0], DATE_FORMAT))
        for edit in (dlg.dateedit_calcTo, dlg.dateedit_startupTo):
            edit.setDateTime(QDateTime.fromString(PERIOD[1], DATE_FORMAT))
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
        # mass flows of the supply pipes and temperatures of all pipes of both circuits
        missing = {'line_s_mdot$1', 'line_s_mdot$2'} | {'line_s_temp${}'.format(seq) for seq in (1, 2, 3, 4)}
        assert not missing - tables, sorted(missing - tables)
