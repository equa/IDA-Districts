# coding=utf-8
"""Cost optimization (OpenSpec change cost-optimization) on a project from the template dynamic_optimization (skipped
without it): example pipe costs, the outputs, the dialog with three one-day weeks and max. 2 iterations in a new child
version; iteration 0 as reference, rows with NPV and model error, the child version with the pipes of the best
iteration, the parent unchanged.

    python -m pytest test/test_cost_optimization.py -v -s   (DISTRICTS_TEST_DYNOPT_TIMEOUT=7200 [s], --keep-projects)
"""
import json
import os
from types import SimpleNamespace

import pytest

from districts.cost_optimization import iterationPath
from districts.ida_mosim import setRequestedOutputs
from districts.utility_functions.economic_data import examplePipeCosts

from .conftest import wait, wait_for_process, wait_until
from .test_dynamic_optimization import TIMEOUT, bundles, create_dynopt_project, skip_without_template
from .test_workflow import delete_project, project_name_for

pytestmark = [pytest.mark.e2e, pytest.mark.ida]


@pytest.fixture(scope='class')
def co(request, districts_plugin, errors):
    plugin = districts_plugin
    skip_without_template(plugin)
    state = SimpleNamespace(plugin=plugin, project_name=project_name_for('costopt'))
    yield state
    if not request.config.getoption('--keep-projects'):
        delete_project(plugin, errors, state.project_name)


@pytest.mark.incremental
class TestCostOptimization:
    def test_project_costs_and_outputs(self, co, errors):
        plugin = co.plugin
        create_dynopt_project(plugin, errors, co.project_name)
        plugin.cur.execute('SELECT id, innerpipediameter FROM public.pipes;')
        for row in plugin.cur.fetchall():
            plugin.cur.execute('UPDATE public.pipes SET costs = %s, maintenance_pct = 1, lifetime_a = 40, p_max_bar = 16 WHERE id = %s;',
                               (examplePipeCosts(round(float(row['innerpipediameter']) * 1000)), row['id']))
        plugin.showRequestedOutputs()
        dlg = plugin.dlg_outputs
        for checkbox in (dlg.checkBoxPlantPumpPower, dlg.checkBoxPlantConnTemp, dlg.checkBoxTempPipe, dlg.checkBoxQambPipe,
                         dlg.checkBoxMdotNode, dlg.checkBoxSubstationTair, dlg.checkBoxSubstationPower):
            checkbox.setChecked(True)
        setRequestedOutputs(plugin.config, plugin.plugin_dir, dlg, plugin.requestedOutputs)
        wait_for_process(dlg, timeout=120)
        errors.check()
        co.parent = plugin.config['versionName']
        co.parent_bundles = bundles(plugin, co.parent)

    def test_run(self, co, errors):
        plugin = co.plugin
        plugin.showCostOptimization()
        dlg = plugin.dlg_costOptimization
        assert dlg.pairs() == [(1, 2)]
        periods = dlg.periods
        # the annual option hides the weeks with their diagram; the weeks shown are the weeks of the checks
        periods.check_annual.setChecked(True)
        assert not periods.weeks_box.isVisibleTo(dlg)
        periods.check_annual.setChecked(False)
        assert periods.weeks_box.isVisibleTo(dlg)
        periods.spin_days.setValue(1)
        periods.spin_startup.setValue(1)
        periods.chooseWeeks()
        weeks = [str(d[0].date()) for d in periods.parameters()['periods']]
        dlg.spin_iter.setValue(2)
        dlg.edit_version.setText(co.parent + '_co')
        dlg.btn_start.click()
        assert dlg.process_running
        wait_until(lambda: not dlg.process_running, TIMEOUT, lambda: 'still running:\n' + dlg.log_edit.toPlainText()[-3000:])
        wait(500)
        log = dlg.log_edit.toPlainText()
        print('\n' + log)
        errors.check()
        assert dlg.progress.value() == 100, log
        assert plugin.config['versionName'] == co.parent + '_co'
        assert 'Weeks from {}'.format(', '.join(weeks)) in log
        rows = []
        k = 0
        while os.path.exists(iterationPath(plugin.config, k)):
            with open(iterationPath(plugin.config, k), encoding='utf-8') as f:
                rows.append(json.load(f))
            k += 1
        for r in rows:
            print('iteration {iteration}: NPV {npv:.0f}, model {m}, error {e}, larger {l}, smaller {s}, rejected {x}, {o}, split {split}'.format(
                m=r.get('npv_model'), e=r.get('model_error'), l=r.get('n_larger'), s=r.get('n_smaller'), x=r.get('n_rejected'), o=r.get('outcome'),
                **{k: r[k] for k in ('iteration', 'npv')}, split={k: round(v) for k, v in r['split'].items()}))
        assert rows and rows[0]['iteration'] == 0 and rows[0]['npv_model'] is None
        assert all('split' in r and 'penalties' in r['split'] for r in rows)
        if len(rows) > 1:
            assert rows[1]['npv_model'] is not None and rows[1]['model_error'] is not None
        best = min(rows, key=lambda r: r['npv'])
        assert {str(k): v for k, v in bundles(plugin, plugin.config['versionName']).items()} == best['state']
        assert bundles(plugin, co.parent) == co.parent_bundles  # the parent version is unchanged
        assert dlg.table_iterations.rowCount() == len(rows)
