# coding=utf-8
"""Long tests of the cost optimization (OpenSpec change cost-optimization, D11), only with DISTRICTS_TEST_ANNUAL=1:
the NPV of three representative weeks against the NPV of an annual simulation (reported, no bound yet), and an
annual optimization of base1 of the template dynamic_optimization. The low-temperature version of the sample is
skipped until the IDA Districts sample contains it.

    set DISTRICTS_TEST_ANNUAL=1
    python -m pytest test/test_cost_optimization_annual.py -v -s   (hours; --keep-projects)
"""
import os
from types import SimpleNamespace

import pytest

from districts.utility_functions.files import loadModellingSettings
from districts.utility_functions.network_economics import evaluateVersion

from .conftest import wait, wait_until
from .test_cost_optimization import TestCostOptimization
from .test_dynamic_optimization import skip_without_template
from .test_representative_periods import run_periods
from .test_workflow import delete_project, project_name_for

pytestmark = [pytest.mark.e2e, pytest.mark.ida, pytest.mark.annual,
              pytest.mark.skipif(os.environ.get('DISTRICTS_TEST_ANNUAL') != '1', reason='long test: set DISTRICTS_TEST_ANNUAL=1')]
TIMEOUT = int(os.environ.get('DISTRICTS_TEST_ANNUAL_TIMEOUT', '36000'))
LT_VERSION = os.environ.get('DISTRICTS_TEST_LT_VERSION', 'lt1')


@pytest.fixture(scope='class')
def co(request, districts_plugin, errors):
    skip_without_template(districts_plugin)
    state = SimpleNamespace(plugin=districts_plugin, project_name=project_name_for('costopt_annual'))
    yield state
    if not request.config.getoption('--keep-projects'):
        delete_project(districts_plugin, errors, state.project_name)


def base_scenario(plugin):
    plugin.cur.execute("SELECT id FROM public.economic_scenarios WHERE name = 'base';")
    return plugin.cur.fetchone()['id']


def periods_run(plugin, errors, annual):
    run_periods(plugin, errors, annual=annual, build=True, days=7)
    return evaluateVersion(plugin.cur, plugin.config, base_scenario(plugin), loadModellingSettings(plugin.plugin_dir, plugin.config))


@pytest.mark.incremental
class TestCostOptimizationAnnual:
    def test_project(self, co, errors):
        TestCostOptimization().test_project_costs_and_outputs(co, errors)

    def test_weeks_against_a_year(self, co, errors):
        plugin = co.plugin
        weeks = periods_run(plugin, errors, annual=False)
        year = periods_run(plugin, errors, annual=True)
        for key in ('pump_kwh', 'heat_kwh'):
            print('{}: weeks {:.0f}, year {:.0f}, difference {:+.1%}'.format(key, weeks['energy'][key], year['energy'][key],
                                                                             weeks['energy'][key] / year['energy'][key] - 1 if year['energy'][key] else 0))
        print('NPV: weeks {:.0f}, year {:.0f}'.format(weeks['npv']['npv'], year['npv']['npv']))
        assert weeks['npv']['npv'] > 0 and year['npv']['npv'] > 0

    def test_annual_optimization(self, co, errors):
        plugin = co.plugin
        plugin.showCostOptimization()
        dlg = plugin.dlg_costOptimization
        dlg.periods.check_annual.setChecked(True)
        dlg.spin_iter.setValue(3)
        dlg.btn_start.click()
        wait_until(lambda: not dlg.process_running, TIMEOUT, lambda: dlg.log_edit.toPlainText()[-3000:])
        wait(500)
        print('\n' + dlg.log_edit.toPlainText())
        errors.check()
        assert dlg.progress.value() == 100

    def test_low_temperature_version(self, co):
        plugin = co.plugin
        plugin.cur.execute("SELECT 1 FROM information_schema.schemata WHERE schema_name = %s;", (LT_VERSION,))
        if not plugin.cur.fetchone():
            pytest.skip('the IDA Districts sample dynamic_optimization has no low-temperature version {} yet'.format(LT_VERSION))
