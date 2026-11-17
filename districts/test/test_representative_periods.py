# coding=utf-8
"""Representative periods (OpenSpec change representative-periods) on a project from the template
dynamic_optimization (skipped without it): the periods widget with three one-day weeks, the period run (simulate, load and
keep three times), periods.json, the dates of the version restored, a second run, the economic evaluation from the
kept weeks.

    python -m pytest test/test_representative_periods.py -v -s   (DISTRICTS_TEST_DYNOPT_TIMEOUT=7200 [s], --keep-projects)
"""
import os
from types import SimpleNamespace

import pytest

from districts.ida_mosim import buildModel, setRequestedOutputs
from districts.representative_periods import PeriodRun, PeriodsWidget
from districts.utility_functions.db import getUsedNetworkSubmodels
from districts.utility_functions.dialog import closeDialog
from districts.utility_functions.files import loadModellingSettings, loadNetworkSimData
from districts.utility_functions.network_economics import evaluateVersion
from districts.utility_functions.periods import loadPeriods, periodsPath

from .conftest import wait, wait_for_process, wait_until
from .test_dynamic_optimization import TIMEOUT, create_dynopt_project, skip_without_template
from .test_workflow import delete_project, project_name_for

pytestmark = [pytest.mark.e2e, pytest.mark.ida]


@pytest.fixture(scope='class')
def rp(request, districts_plugin, errors):
    plugin = districts_plugin
    skip_without_template(plugin)
    state = SimpleNamespace(plugin=plugin, project_name=project_name_for('periods'))
    yield state
    if not request.config.getoption('--keep-projects'):
        delete_project(plugin, errors, state.project_name)


def period_tables(plugin):
    plugin.cur.execute("SELECT table_name FROM information_schema.tables WHERE table_schema = %s AND table_name ~ '_period[0-9]+$';",
                       (plugin.config['versionName'],))
    return sorted(row['table_name'] for row in plugin.cur.fetchall())


class PeriodHost:
    """what PeriodRun needs of a dialog, with the periods widget (the cost optimization is the only dialog with it)"""

    def __init__(self, plugin):
        self.periods = PeriodsWidget(plugin)
        self.lines, self.progress, self.done, self.ok = [], 0, False, None
        self.run = None

    year = property(lambda self: self.periods.year)
    t_year = property(lambda self: self.periods.t_year)
    climate = property(lambda self: self.periods.climate)

    def log(self, message):
        self.lines.append(message)

    def update_progress(self, value):
        self.progress = value

    def finished(self):
        self.done = True


def run_periods(plugin, errors, annual=False, build=False, days=1):
    """a period run with three weeks of `days` days (or a year) and one day start-up; returns the host"""
    host = PeriodHost(plugin)
    wait_until(lambda: host.periods.ready, 120, 'choosing the weeks')
    host.periods.check_annual.setChecked(annual)
    host.periods.spin_startup.setValue(1)
    if not annual:
        host.periods.spin_days.setValue(days)
        host.periods.chooseWeeks()
        wait_until(lambda: host.periods.ready, 120, 'choosing the weeks')
        assert len(host.periods.date_edits) == 3
    plugin.cur.execute('SELECT network FROM "{}".lines GROUP BY network ORDER BY network;'.format(plugin.config['versionName']))  # nosec B608
    parms = {'network': str(plugin.cur.fetchone()['network']), 'submodel': getUsedNetworkSubmodels(plugin.cur, plugin.config)[0],
             'build_first': build, **host.periods.parameters()}
    host.run = PeriodRun(host, plugin, parms, on_finished=lambda ok: setattr(host, 'ok', ok))
    host.run.start()
    wait_until(lambda: host.done, TIMEOUT, lambda: 'still running:\n' + '\n'.join(host.lines)[-3000:])
    wait(500)
    log = '\n'.join(host.lines)
    print('\n' + log)
    errors.check()
    assert host.ok and host.progress == 100, log
    return host


@pytest.mark.incremental
class TestRepresentativePeriods:
    def test_create_project_and_outputs(self, rp, errors):
        plugin = rp.plugin
        create_dynopt_project(plugin, errors, rp.project_name)
        plugin.showRequestedOutputs()
        dlg = plugin.dlg_outputs
        for checkbox in (dlg.checkBoxPlantPumpPower, dlg.checkBoxPlantConnTemp, dlg.checkBoxTempPipe, dlg.checkBoxQambPipe):
            checkbox.setChecked(True)
        setRequestedOutputs(plugin.config, plugin.plugin_dir, dlg, plugin.requestedOutputs)
        wait_for_process(dlg, timeout=120)
        plugin.showBuildModel()
        dlg = plugin.dlg_buildModel
        dlg.combo_network_models.setItemChecked(1, True)
        dlg.combo_submodels.setItemChecked(1, True)
        buildModel(dlg, plugin)
        wait_for_process(dlg, timeout=300)
        closeDialog(dlg)
        errors.check()

    def test_period_run(self, rp, errors):
        plugin = rp.plugin
        before = {k: v for k, v in loadNetworkSimData(plugin.plugin_dir, plugin.config).items()}
        host = run_periods(plugin, errors)
        tables = period_tables(plugin)
        for k in (1, 2, 3):
            assert 'line_s_qamb_period{}'.format(k) in tables and 'energy_plant_s_ppump_period{}'.format(k) in tables
        periods = loadPeriods(plugin.config)
        assert [w['role'] for w in periods['weeks']] == host.periods.roles and len(periods['hours']) == 3 * 24
        assert sum(w for _, _, w in periods['hours']) == pytest.approx(8760)
        assert loadNetworkSimData(plugin.plugin_dir, plugin.config) == before  # the dates of the version as before
        # the weeks ran in parallel in model copies: each kept its own results, no copy is left
        schema = plugin.config['versionName']
        contents = set()
        for k in (1, 2, 3):
            plugin.cur.execute("""SELECT md5(string_agg(t::text, '')) AS h FROM "{}"."line_s_qamb_period{}" t;""".format(schema, k))
            contents.add(plugin.cur.fetchone()['h'])
        assert len(contents) == 3
        version_dir = os.path.join(plugin.config['pathProjects'] + plugin.config['projectName'], 'versions', schema)
        assert not [name for name in os.listdir(version_dir) if name.startswith('period_')]
        rp.tables = tables

    def test_second_run(self, rp, errors):
        plugin = rp.plugin
        plugin.cur.execute('CREATE TABLE "{}".line_s_qamb_period4 (id integer);'.format(plugin.config['versionName']))  # nosec B608
        run_periods(plugin, errors)
        assert period_tables(plugin) == rp.tables  # nothing of the first run left
        assert os.path.exists(periodsPath(plugin.config))

    def test_economics_from_the_periods(self, rp):
        plugin = rp.plugin
        plugin.cur.execute("SELECT id FROM public.economic_scenarios WHERE name = 'base';")
        evaluation = evaluateVersion(plugin.cur, plugin.config, plugin.cur.fetchone()['id'], loadModellingSettings(plugin.plugin_dir, plugin.config))
        assert 'short' not in evaluation and 'missing' not in evaluation, evaluation
        assert len(evaluation['periods']['weeks']) == 3
        assert evaluation['energy']['pump_kwh'] > 0 and evaluation['npv']['npv'] > 0
