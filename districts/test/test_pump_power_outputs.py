# coding=utf-8
"""Pump power and room setpoint outputs (OpenSpec change pump-power-outputs) on a project from the template
dynamic_optimization (skipped without it): request the outputs, the pump list of the project, the outputs in the
templates, build, simulate 1 January, load the results.

    python -m pytest test/test_pump_power_outputs.py -v -s
    (DISTRICTS_TEST_DYNOPT_TIMEOUT=7200 [s], --keep-projects)
"""
import os
from types import SimpleNamespace

import pytest
from qgis.PyQt.QtCore import QDateTime

from districts.dynamic_pipe_sizing import DATE_FORMAT
from districts.ida_mosim import buildModel, runModel, setRequestedOutputs
from districts.ida_rv import loadResults
from districts.utility_functions.dialog import closeDialog
from districts.utility_functions.files import loadRequestedOutputs
from districts.utility_functions.network_pumps import loadPumpList, pumpFilePath, templatePath
from districts.utility_functions.translations import tr_msg

from .conftest import wait_for_process
from .test_dynamic_optimization import TEMPLATE, TIMEOUT, create_dynopt_project, skip_without_template
from .test_workflow import delete_project, project_name_for

pytestmark = [pytest.mark.e2e, pytest.mark.ida]

PERIOD = ('2026-01-01 00:00:00', '2026-01-02 00:00:00')  # calculation and start-up period


@pytest.fixture(scope='class')
def pumps(request, districts_plugin, errors):
    plugin = districts_plugin
    skip_without_template(plugin)
    state = SimpleNamespace(plugin=plugin, project_name=project_name_for('pumps'))
    yield state
    if not request.config.getoption('--keep-projects'):
        delete_project(plugin, errors, state.project_name)


def template_text(plugin, feature, t_name):
    with open(templatePath(plugin.config, feature, t_name), encoding='utf-8-sig') as f:
        return f.read()


@pytest.mark.incremental
class TestPumpPowerOutputs:
    def test_create_project(self, pumps, errors):
        create_dynopt_project(pumps.plugin, errors, pumps.project_name)

    def test_request_outputs(self, pumps, errors):
        plugin = pumps.plugin
        plugin.showRequestedOutputs()
        dlg = plugin.dlg_outputs
        assert dlg.btn_network_pumps_c.isEnabled() and dlg.btn_network_pumps_ep.isEnabled()
        for checkbox in (dlg.checkBoxSubstationPumpPower, dlg.checkBoxPlantPumpPower, dlg.checkBoxSubstationTair,
                         dlg.checkBoxSubstationMassflow, dlg.checkBoxSubstationPressure):
            checkbox.setChecked(True)
        setRequestedOutputs(plugin.config, plugin.plugin_dir, dlg, plugin.requestedOutputs)
        wait_for_process(dlg, timeout=120)
        errors.check()
        outputs = loadRequestedOutputs(plugin.plugin_dir, plugin.config)
        assert outputs['ppump_c'] and outputs['ppump_ep'] and outputs['troom_c']

        # the pump list of the project: the heat source pump and the pressure-holding pump, no customer pump
        assert os.path.exists(pumpFilePath(plugin.config))
        entries = loadPumpList(plugin.config)['entries']
        assert sorted((e['feature'], e['template'], e['component']) for e in entries) == [
            ('energy_plant', '1_ideal_heat_source', 'PUMP2'), ('energy_plant', '2_topup', 'PUMP')]
        # the outputs in the templates
        assert ':L "PumpPower"' in template_text(plugin, 'energy_plant', '1_ideal_heat_source')
        assert '(OUTPUT-FILE :N "PumpPower"' in template_text(plugin, 'energy_plant', '2_topup')
        customer = template_text(plugin, 'customer', '1_simplified_consumer')
        assert '"PumpPower"' not in customer
        assert '|TSet_var|' in customer and ':AS "tset"' in customer and ':AS "hcmode"' in customer

    def test_request_outputs_again(self, pumps, errors):
        """OK without changes writes the templates again without duplicate output files."""
        plugin = pumps.plugin
        plugin.showRequestedOutputs()
        dlg = plugin.dlg_outputs
        setRequestedOutputs(plugin.config, plugin.plugin_dir, dlg, plugin.requestedOutputs)
        wait_for_process(dlg, timeout=120)
        errors.check()
        assert template_text(plugin, 'energy_plant', '1_ideal_heat_source').count('(OUTPUT-FILE :N "PumpPower"') == 1
        assert template_text(plugin, 'customer', '1_simplified_consumer').count('(OUTPUT-FILE :N "TRoom"') == 1

    def test_build_and_simulate(self, pumps, errors):
        plugin = pumps.plugin
        plugin.showBuildModel()
        dlg = plugin.dlg_buildModel
        dlg.combo_network_models.setItemChecked(1, True)
        dlg.combo_submodels.setItemChecked(1, True)
        buildModel(dlg, plugin)
        wait_for_process(dlg, timeout=300)
        closeDialog(dlg)
        errors.check()
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

    def test_load_results(self, pumps, errors):
        plugin = pumps.plugin
        plugin.showLoadResults()
        dlg = plugin.dlg_loadResults
        dlg.combo_submodels.setItemChecked(1, True)
        loadResults(dlg, plugin)
        wait_for_process(dlg, timeout=600)
        closeDialog(dlg)
        errors.check()
        version = plugin.config['versionName']
        plugin.cur.execute("""SELECT pump, kind, count(*) AS n, max("$ppump") AS p_max
            FROM "{}".energy_plant_s_ppump GROUP BY pump, kind ORDER BY pump;""".format(version))  # nosec B608
        rows = plugin.cur.fetchall()
        assert [(r['pump'], r['kind']) for r in rows] == [('PUMP', 'variable'), ('PUMP2', 'variable')]
        assert all(r['n'] > 1 for r in rows)
        # the heat source pump drives the circulation
        assert [r['p_max'] for r in rows if r['pump'] == 'PUMP2'][0] > 0
        plugin.cur.execute("""SELECT min("$tset") AS t_min, max("$tset") AS t_max, count(*) AS n FROM "{}".customer_s_tset;""".format(version))  # nosec B608
        tset = plugin.cur.fetchone()
        assert tset['n'] > 0 and tset['t_min'] == tset['t_max'] == 21
        plugin.cur.execute("""SELECT DISTINCT "$hcmode" AS mode FROM "{}".customer_s_hcmode;""".format(version))  # nosec B608
        assert [r['mode'] for r in plugin.cur.fetchall()] == [1]
        plugin.cur.execute("""SELECT count(*) AS n FROM "{}".customer_s_ppump;""".format(version))  # nosec B608
        assert plugin.cur.fetchone()['n'] == 0  # the customers of the sample have no network pump
