"""The plugin must not leave DB connections open: workers/dialogs close their own connections, layers of workers
are created in the main thread (a layer created in a pool thread keeps one QGIS connection per run), plugin
connections are labelled with DISTRICTS_APPLICATION_NAME and idle ones can be ended with closeIdleDistrictsConnections.

Runs on its own 'Heating network' project (see test_workflow.py for the DB settings)."""
import gc
import re
import subprocess

import qgis
import qgis.utils

from qgis.core import QgsProject, QgsVectorLayer

from districts.ida_ph import loadVersion
from districts.pipe_sizing import rejectPipeSizingResults
from districts.utility_functions.db import DISTRICTS_APPLICATION_NAME, closeIdleDistrictsConnections, dbConnect
from districts.utility_functions.dialog import closeDialog
from districts.utility_functions.translations import tr

from .conftest import wait, wait_for_process, wait_until
from .test_workflow import HEATING, create_project, delete_project, project_name_for

QGIS_APP = 'QGIS'  # application_name of the QGIS postgres provider starts with QGIS (e.g. 'QGIS4 ')


def connections(plugin, db_name):
    """{'plugin': n, 'qgis': n, 'unlabelled': n} client connections to db_name (not counted: cur_postgres, server processes
    like autovacuum, other applications)"""
    wait(500)
    gc.collect()
    wait(200)
    plugin.cur_postgres.execute(
        "SELECT application_name AS app, count(*) AS n FROM pg_stat_activity "
        "WHERE datname = %s AND backend_type = 'client backend' AND pid <> pg_backend_pid() GROUP BY 1;", (db_name,))
    rows = plugin.cur_postgres.fetchall()
    result = {'plugin': 0, 'qgis': 0, 'unlabelled': 0}  # other applications (pgAdmin, psql) are not counted
    for row in rows:
        if row['app'] == DISTRICTS_APPLICATION_NAME:
            result['plugin'] += row['n']
        elif row['app'].startswith(QGIS_APP):
            result['qgis'] += row['n']
        elif not row['app']:
            result['unlabelled'] += row['n']
    return result


def last_queries(plugin, db_name):
    plugin.cur_postgres.execute(
        "SELECT left(regexp_replace(query, '\\s+', ' ', 'g'), 120) AS q FROM pg_stat_activity "
        "WHERE datname = %s AND application_name = %s;", (db_name, DISTRICTS_APPLICATION_NAME))
    return [r['q'] for r in plugin.cur_postgres.fetchall()]


def assert_no_growth(plugin, db_name, baseline, step):
    now = connections(plugin, db_name)
    assert now['plugin'] <= baseline['plugin'] and now['qgis'] <= baseline['qgis'], \
        "{}: open connections {} > {} (plugin connections: {})".format(step, now, baseline, last_queries(plugin, db_name))


def run_pipe_sizing(plugin):
    plugin.pipeSizing()
    dlg = plugin.dlg_pipeSizing
    dlg.addRow()
    dlg.table_circuits.item(0, 1).setText('70')
    dlg.table_circuits.item(0, 4).setText('40')
    dlg.table_circuits.selectRow(0)
    dlg.table_circuits.selectColumn(3)
    dlg.table_circuits.cellWidget(0, 3).setCurrentText('2')
    dlg.table_circuits.cellWidget(0, 5).setCurrentText('load_w')
    for row in range(dlg.table_sequences.rowCount()):
        dlg.table_sequences.cellWidget(row, 1).setAllItemsChecked(checked=True)
    dlg.btn_start.pressed.emit()
    assert not dlg.btn_start.isEnabled()
    wait_for_process(dlg, timeout=120)
    wait_until(lambda: dlg.btn_start.isEnabled(), 10, "pipe sizing start button not enabled again")
    rejectPipeSizingResults(plugin.config, plugin.conn, dlg)
    wait(500)
    closeDialog(dlg)


def run_customer_data_sheet(plugin, monkeypatch):
    """Run the 'customer data sheet' action of the customers layer like QGIS does (expressions substituted, exec)."""
    customers = QgsProject.instance().mapLayersByName(tr('@default', 'customers'))[0]
    action = [a for a in customers.actions().actions() if a.name() == tr('@default', 'customer_data_sheet')][0]
    feature = next(customers.getFeatures())
    point = feature.geometry().centroid().asPoint()
    code = action.command().replace('[% $x %]', repr(point.x())).replace('[% $y %]', repr(point.y()))
    code = code.replace('[%id%]', str(feature['id']))
    assert not re.search(r'\[%.*?%\]', code), "unsubstituted expression in the customer data sheet action"
    # no PDF viewer and no OpenStreetMap tiles in the test
    monkeypatch.setattr(subprocess, 'Popen', lambda *args, **kwargs: None)
    osm = QgsVectorLayer('Point?crs=epsg:4326', 'OpenStreetMap', 'memory')
    QgsProject.instance().addMapLayer(osm)
    try:
        # QGIS runs actions in its python namespace, which already contains qgis and iface
        namespace = {'__name__': '__main__', 'qgis': qgis, 'iface': qgis.utils.iface}
        exec(compile(code, 'customer_data_sheet_action', 'exec'), namespace)  # nosec B102
    finally:
        QgsProject.instance().removeMapLayer(osm.id())
        layout = QgsProject.instance().layoutManager().layoutByName('CustomerDataSheet')
        if layout:
            QgsProject.instance().layoutManager().removeLayout(layout)


def test_db_connections_are_released(districts_plugin, errors, monkeypatch):
    plugin = districts_plugin
    name = project_name_for("connections")
    try:
        create_project(plugin, errors, name, HEATING)
        wait(3000)
        if plugin.config['versionName'] != 'base1':
            plugin.config['versionName'] = 'base1'
            loadVersion(main=plugin)
            wait(3000)
        assert plugin.config['versionName'] == 'base1'
        baseline = connections(plugin, name)
        assert baseline['plugin'] >= 1, "the plugin connections are not labelled with {!r}".format(DISTRICTS_APPLICATION_NAME)
        if baseline['unlabelled']:
            plugin.cur_postgres.execute(
                "SELECT state, backend_start, state_change, client_port, left(query, 150) AS q FROM pg_stat_activity "
                "WHERE datname = %s AND backend_type = 'client backend' AND application_name = '';", (name,))
            details = plugin.cur_postgres.fetchall()
        assert baseline['unlabelled'] == 0, "connections without application_name: {} {}".format(
            baseline, details if baseline['unlabelled'] else '')

        loadVersion(main=plugin)
        wait(3000)
        assert_no_growth(plugin, name, baseline, 'reload version')

        # temp layers of the pipe sizing/topology workers are created in the main thread
        for i in range(2):
            run_pipe_sizing(plugin)
            assert_no_growth(plugin, name, baseline, 'pipe sizing run {}'.format(i + 1))

        # dialogs close their own connections (also those overriding closeEvent)
        for open_fn, attr in ((plugin.pipeLayingAlgorithm, 'dlg_pipeLayingAlgorithm'),
                              (plugin.generateNetworkTopology, 'window_topology'),
                              (plugin.mapFeatures, 'window_mapPlants'),
                              (plugin.pipeSizing, 'dlg_pipeSizing'),
                              (plugin.showFeatureModels, None)):
            open_fn()
            wait(300)
            dlg = plugin.invoke_features.dlg_invokeFeatures if attr is None else getattr(plugin, attr)
            closeDialog(dlg)
            assert_no_growth(plugin, name, baseline, 'open/close {}'.format(type(dlg).__name__))

        # sensor signals: OK disabled while the worker runs, the worker closes its connection
        plugin.sensorSignals()
        sdlg = plugin.updateSensor.dlg
        sdlg.btn_ok.click()
        assert not sdlg.btn_ok.isEnabled()
        wait_for_process(sdlg, timeout=120)
        assert_no_growth(plugin, name, baseline, 'sensor signals')

        # customer data sheet action: the connection for the plots is closed again
        run_customer_data_sheet(plugin, monkeypatch)
        assert connections(plugin, name)['plugin'] <= baseline['plugin'], "customer data sheet: plugin connection not closed"
        # the PDF export renders the map layers in a render thread: QGIS takes a connection of its connection pool,
        # which it releases after ~60 s idle
        wait_until(lambda: connections(plugin, name)['qgis'] <= baseline['qgis'], 120,
                   lambda: "customer data sheet: QGIS connections not released: {}".format(connections(plugin, name)))
        errors.check()

        # safety net: an idle connection left open is ended
        leaked = dbConnect(plugin.config, True)
        leaked.cursor().execute('SELECT 1;')
        assert connections(plugin, name)['plugin'] == baseline['plugin'] + 1
        ended = closeIdleDistrictsConnections(plugin.cur_postgres, dbName=name)
        assert ended >= 1  # also the idle main connection (only used for the previous project when switching)
        assert connections(plugin, name)['plugin'] == 0
        plugin.loadProject()  # reconnect
        errors.clear()
    finally:
        delete_project(plugin, errors, name)
