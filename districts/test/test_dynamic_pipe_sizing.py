# coding=utf-8
"""Dynamic pipe sizing and hydraulic balancing (dynamic_pipe_sizing.py) on an existing project with simulation results.

Only runs with a project given (it is not created by the test); the pipes are sized in a new child version
of the version, which is kept for inspection:

    DISTRICTS_TEST_PATH_PROJECTS=C:\\projects  DISTRICTS_TEST_DB_PORT=5433
    DISTRICTS_TEST_DYNAMIC_SIZING_PROJECT=dyn_opt  (DISTRICTS_TEST_DYNAMIC_SIZING_VERSION=base1)
    (DISTRICTS_TEST_DYNAMIC_SIZING_MAX_ITER=3, DISTRICTS_TEST_DYNAMIC_SIZING_TIMEOUT=7200 [s])
    python -m pytest test/test_dynamic_pipe_sizing.py -v -s
"""
import os
import time

import pytest
from qgis.core import Qgis, QgsProject
from qgis.PyQt.QtWidgets import QMessageBox

from districts.ida_ph import loadVersion
from districts.utility_functions.dynamic_sizing_results import SIZING_PROPERTY, iterationRow, loadIterations, removeSizingLayers
from districts.utility_functions.hydraulic_balancing import loadCLidPressure
from districts.utility_functions.translations import tr, tr_msg
from districts.utility_functions.utility import write_plugin_settings

from .conftest import wait, wait_for_process, wait_until

pytestmark = [pytest.mark.e2e, pytest.mark.ida]

PROJECT = os.environ.get("DISTRICTS_TEST_DYNAMIC_SIZING_PROJECT")
VERSION = os.environ.get("DISTRICTS_TEST_DYNAMIC_SIZING_VERSION", "base1")
MAX_ITER = int(os.environ.get("DISTRICTS_TEST_DYNAMIC_SIZING_MAX_ITER", "3"))
TIMEOUT = int(os.environ.get("DISTRICTS_TEST_DYNAMIC_SIZING_TIMEOUT", "7200"))


@pytest.mark.skipif(not PROJECT, reason="DISTRICTS_TEST_DYNAMIC_SIZING_PROJECT not set")
def test_dynamic_pipe_sizing(districts_plugin, errors, monkeypatch):
    plugin = districts_plugin
    assert PROJECT in plugin.dlg.projectNames, "project {} not found on the server".format(PROJECT)
    plugin.config['projectName'] = PROJECT
    plugin.config['versionName'] = VERSION
    write_plugin_settings(plugin.config)
    plugin.loadProject()
    loadVersion(main=plugin)
    wait_for_process(plugin.dlg, timeout=120)
    errors.check()
    assert plugin.config['versionName'] == VERSION

    plugin.showDynamicPipeSizing()
    dlg = plugin.dlg_dynamicPipeSizing
    new_version = '{}_hb_{}'.format(VERSION, time.strftime('%m%d%H%M'))
    assert dlg.text_info.toHtml() and 'dynamic_pipe_sizing_info' not in dlg.text_info.toPlainText()
    assert dlg.combo_network.count() and dlg.combo_submodel.count()
    dlg.rbtn_newVersion.setChecked(True)
    dlg.lineEdit_versionName.setText(new_version)
    dlg.spin_maxIter.setValue(MAX_ITER)
    # the confirmation question of start()
    monkeypatch.setattr(QMessageBox, "question", lambda *args, **kwargs: QMessageBox.StandardButton.Yes)

    dlg.btn_start.click()
    assert dlg.process_running
    wait_until(lambda: not dlg.process_running, TIMEOUT, lambda: "still running:\n" + dlg.textEdit_log.toPlainText()[-3000:])
    wait(500)
    log = dlg.textEdit_log.toPlainText()
    print('\n' + log)
    path = os.path.join(plugin.config['pathProjects'], PROJECT, 'versions', new_version)
    with open(os.path.join(path, 'dynamic_sizing_test.log'), 'w', encoding='utf-8') as f:
        f.write(log)

    assert plugin.config['versionName'] == new_version
    assert dlg.progress.value() == 100, log  # finished without error (converged or max. number of iterations)
    assert os.path.isfile(os.path.join(path, 'dynamic_sizing_iter1_c_lid.json')), log
    c_lid = loadCLidPressure(os.path.join(path, 'dynamic_sizing_iter1_c_lid_sized.json'))
    assert c_lid and all(lids for _, lids in c_lid.values())
    # the loaded base version keeps its pipes
    plugin.cur.execute('SELECT count(*) AS n FROM "{}".lines l JOIN "{}".lines b USING (id) WHERE l.pipe_bundle_type_id <> b.pipe_bundle_type_id;'.format(new_version, VERSION))  # nosec B608
    print('lines with other pipe bundles than {}: {}'.format(VERSION, plugin.cur.fetchone()['n']))
    assert tr('@default', 'dynamic_pipe_sizing_info') != 'dynamic_pipe_sizing_info'

    # iterations: one file and table row each, shown on the map while running (option, default on)
    summaries = loadIterations(plugin.config)
    n = len(summaries)
    assert n >= 1 and [s['iteration'] for s in summaries] == list(range(1, n + 1))
    assert summaries[-1]['outcome'] in ('converged', 'max_iter'), summaries[-1]['outcome']
    assert dlg.table_iterations.rowCount() == n
    for s in summaries:
        print('iteration {}: {}'.format(s['iteration'], iterationRow(s)))
        assert str(s['cid_weak']) in s['customers'] and s['lines']
    assert set(sizingLayers()) == set(range(1, n + 1))
    for layers in sizingLayers().values():
        assert len(layers) == 3
        customers = [l for l in layers if l.geometryType() == Qgis.GeometryType.Point][0]
        assert customers.featureCount() == len(summaries[0]['customers'])
        assert sum(1 for f in customers.getFeatures() if f['weak']) == 1
    group = QgsProject.instance().layerTreeRoot().findGroup(tr_msg('Dynamic pipe sizing'))
    assert [c.isVisible() for c in group.children()] == [False] * (n - 1) + [True]

    # afterwards: reopen the dialog, the table is filled from the version folder; show the first iteration only
    removeSizingLayers()
    dlg.close()
    plugin.showDynamicPipeSizing()
    dlg = plugin.dlg_dynamicPipeSizing
    assert dlg.table_iterations.rowCount() == n
    dlg.table_iterations.selectRow(0)
    dlg.btn_showIterations.click()
    errors.check()
    assert set(sizingLayers()) == {1}

    # loading a version removes the layers
    loadVersion(main=plugin)
    wait_for_process(plugin.dlg, timeout=120)
    assert not sizingLayers()


def sizingLayers():
    """{iteration: [layers]} of the dynamic pipe sizing layers"""
    result = {}
    for layer in QgsProject.instance().mapLayers().values():
        iteration = layer.customProperty(SIZING_PROPERTY)
        if iteration is not None:
            result.setdefault(int(iteration), []).append(layer)
    return result
