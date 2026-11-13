# coding=utf-8
"""Simulation period, reference run (iteration 0) and the no-flow warning of the dynamic pipe sizing
(OpenSpec change sizing-simulation-period). No database, no IDA Districts."""
import json
import os

import pytest

from districts.utility_functions.dynamic_sizing_results import (
    ITERATION_FILE, deleteIterations, iterationRows, loadIterations, outcomeText, pairSummary,
)
from districts.utility_functions.pipe_pairs import targetFlow

PERIODS = {'calc_time_from': '2026-07-01 00:00:00', 'calc_time_to': '2026-07-08 00:00:00',
           'startup_time_from': '2026-06-24 00:00:00', 'startup_time_to': '2026-07-01 00:00:00'}


# ---------------------------------------------------------------- periods
def test_valid_periods():
    from districts.dynamic_pipe_sizing import periodErrors
    assert periodErrors(PERIODS) == []


@pytest.mark.parametrize('key, value, expected', [
    ('calc_time_to', '2026-06-30 00:00:00', 'calculation period'),
    ('calc_time_to', '2026-07-01 00:00:00', 'calculation period'),
    ('startup_time_from', '2026-07-02 00:00:00', 'start-up period'),
])
def test_invalid_periods(key, value, expected):
    from districts.dynamic_pipe_sizing import periodErrors
    errors = periodErrors(dict(PERIODS, **{key: value}))
    assert len(errors) == 1 and expected in errors[0]


@pytest.fixture
def sizing_dialog(qgis_app):
    from districts.dynamic_pipe_sizing import DynamicPipeSizingDialog
    dlg = DynamicPipeSizingDialog(main=None)
    yield dlg
    dlg.close()


def test_dialog_periods_and_reference_option(sizing_dialog):
    from qgis.PyQt.QtCore import QDateTime
    from districts.dynamic_pipe_sizing import DATE_FORMAT
    dlg = sizing_dialog
    for key, value in PERIODS.items():
        dlg.dateedit_period[key].setDateTime(QDateTime.fromString(value, DATE_FORMAT))
    assert dlg.periods() == PERIODS
    assert not dlg.checkBox_referenceRun.isChecked()  # default: no reference run


# ---------------------------------------------------------------- iteration files of the reference run
@pytest.fixture
def version_dir(tmp_path):
    config = {'pathProjects': str(tmp_path), 'projectName': 'p', 'versionName': 'v'}
    path = tmp_path / 'p' / 'versions' / 'v'
    path.mkdir(parents=True)
    for name in (ITERATION_FILE.format(0), ITERATION_FILE.format(1), ITERATION_FILE.format(10),
                 'dynamic_sizing_iter0_c_lid_1_3.json', 'dynamic_sizing_iter1_c_lid_1_3.json', 'networkSimData.txt'):
        (path / name).write_text('{}')
    return config, path


def test_delete_keeps_the_reference_run(version_dir):
    config, path = version_dir
    deleteIterations(config, keep_reference=True)
    assert sorted(os.listdir(path)) == ['dynamic_sizing_iter0.json', 'dynamic_sizing_iter0_c_lid_1_3.json', 'networkSimData.txt']


def test_delete_all(version_dir):
    config, path = version_dir
    deleteIterations(config)
    assert os.listdir(path) == ['networkSimData.txt']


def result(pipe_new):
    """result of getCustomerLinePressure / optimizePipeDiameters of a pair 1/3 with one line (pipe 5, sized: pipe_new)"""
    catalog = {4: {'name': 'DRE-40', 'd': 0.0372}, 5: {'name': 'DRE-50', 'd': 0.0431}}
    res = {'catalog': catalog, 'c_lid': {7: [1e5, {}]}, 'dvar': {7: (4e4, 1)}, 'times': {7: 't'}, 'time': 't', 'cid_dp': 7, 'epid_dp': 1, 'dp': 4e4,
           'dp_spez': {3: 50.0}, 'lines': {3: {'pipes': {1: {'pipe_id': 5, 'mdot': 1.0, 'mdot_max': 2.0}, 3: {'pipe_id': 5, 'mdot': 1.0}}}}}
    opt = {'c_lid': {7: [0.9e5, {}]}, 'pipes': {3: {1: pipe_new, 3: pipe_new}}, 'cid_weak': 7, 'dp_target': 0.9e5, 'quota': 1.0,
           'spread': 0.0, 'presize': [], 'history': [{}]}
    return res, opt


def test_reference_summary_changes_no_pipe():
    res, opt = result(4)
    pair = pairSummary((1, 3), (70.0, 30.0), res, opt, {3}, reference=True)
    assert pair['n_changed'] == 0 and pair['lines']['3']['pipe_new'] == 'DRE-50' and not pair['lines']['3']['changed']
    sized = pairSummary((1, 3), (70.0, 30.0), res, opt, {3})
    assert sized['n_changed'] == 1 and sized['lines']['3']['pipe_new'] == 'DRE-40'


def test_reference_row_in_the_table(tmp_path):
    res, opt = result(4)
    summary = {'iteration': 0, 'started': '', 'outcome': 'reference', 'n_changed': 0,
               'pairs': [pairSummary((1, 3), (70.0, 30.0), res, opt, set(), reference=True, target_no_flow=True)]}
    config = {'pathProjects': str(tmp_path), 'projectName': 'p', 'versionName': 'v'}
    path = tmp_path / 'p' / 'versions' / 'v'
    path.mkdir(parents=True)
    (path / ITERATION_FILE.format(0)).write_text(json.dumps(summary))
    loaded = loadIterations(config)
    assert loaded[0]['pairs'][0]['target_no_flow'] is True
    row = iterationRows(loaded[0])[0]
    assert (row[0], row[1], row[-2], row[-1]) == (0, '1/3', 0, outcomeText('reference'))


# ---------------------------------------------------------------- no-flow warning
@pytest.mark.parametrize('mdot, peak, no_flow', [
    (0.0, 0.4, True),       # short winter period of a cooling pair
    (0.003, 0.4, True),     # below 1 % of the own peak
    (0.004, 0.4, False),
    (0.3, 0.4, False),
    (0.0, 0.0, True),       # no flow in the whole period
])
def test_target_flow(mdot, peak, no_flow):
    res = {'mdot_customers': {7: -mdot}, 'mdot_peak_customers': {7: peak}}
    assert targetFlow(res, 7) == (mdot, peak, no_flow)
