# coding=utf-8
"""End-to-end test of the Districts Modeler workflow (formerly test_functions/automated_testing.py).

Each step is its own test. The steps of a template build on each other: after
the first failing step the remaining steps of that template are skipped.

    python -m pytest test/test_workflow.py -v                 # all templates
    python -m pytest test/test_workflow.py -v -k heating      # one template
    python -m pytest test/test_workflow.py -v -m "not ida"    # without simulation
"""
import os
import shutil
import time
import warnings
from datetime import timedelta
from types import SimpleNamespace
from xml.etree import ElementTree

import pytest
from qgis.core import Qgis, QgsFeature, QgsGeometry, QgsPointXY, QgsProject
from qgis.PyQt import sip
from qgis.PyQt.QtWidgets import QApplication, QCheckBox, QComboBox, QDialog, QTableWidgetItem

from districts.ida_mosim import buildModel, runModel, setRequestedOutputs
from districts.ida_ph import ShowLoadAttributeDialog, addBaseVersion, createNewProject, deleteProject, setLoadAttribute
from districts.ida_ph_dialog import IDA_Districts_NameDialog
from districts.ida_rv import loadResults, runPathReports, showOnMap
from districts.pipe_sizing import savePipeSizingResults, startPipeSizing
from districts.utility_functions.dialog import addParmTableRow, checkState, closeDialog, uncheckState
from districts.utility_functions.invoke import setFeatureParm
from districts.utility_functions.translations import tr

from .conftest import wait, wait_for_process

pytestmark = [pytest.mark.e2e]

HEATING = "Heating network"
EMPTY = "Empty project"
DB_DEFAULTS = "DB default values"
TEMPLATE_KEYS = {HEATING: "heating_network", EMPTY: "empty_project", DB_DEFAULTS: "db_default_values"}
# the empty project gets its resources (pipes, pipe bundles, connections, templates) in the resource steps
NETWORK_TEMPLATES = (HEATING, EMPTY, DB_DEFAULTS)

# minimal resources of a heating network (like the template 'DB default values')
MATERIALS = [(1, 'P235TR1', 55.2, 460, 7850), (2, 'Polyurethan foam', 0.027, 130, 60)]
PIPE_CONSTRUCTION = (1, '0.01 m P235TR1 0.08 m Polyurethan foam')
PIPE_LAYERS = [(1, 1, 0.01), (2, 2, 0.08)]  # sequence, material, thickness
PIPES = [(i + 1, 'DN{}'.format(dn), d, 0.000045, 1, '', 'DN{}'.format(dn)) for i, (dn, d) in enumerate([
    (20, 0.0217), (25, 0.0273), (32, 0.036), (40, 0.0419), (50, 0.0539), (65, 0.0697), (80, 0.0825),
    (100, 0.1071), (125, 0.1325), (150, 0.1603), (200, 0.2101), (250, 0.263), (300, 0.3127)])]
PIPE_BUNDLE = (1, '', '', '2 pipes; 1m depth; 0.5m distance')
BUNDLE_PIPES = [(1, 1, -0.25, 1, 2), (2, 1, 0.25, 1, 2)]  # sequence, pipe, x, y, ambient (2: ground)
# id, direction (1: supply, 2: return), mass flow as boundary, temperature, pressure, mass flow, description
CONNECTIONS = [(1, 1, False, 70, 100000, '', 'Supply: 70 °C;100000Pa'),
               (2, 2, False, 30, 0, '', 'Return: 30 °C;0Pa'),
               (3, 1, True, 70, '', -0.1, 'Supply: 70 °C;-0.1kg/s'),
               (4, 2, True, 30, '', 0.1, 'Return: 30 °C;0.1kg/s')]
CONNECTION_TYPES = {1: ('1 sup temp 70; 1 ret temp 30', [(1, 1), (2, 2)]),  # id: description, [(sequence, connection)]
                    2: ('1 sup temp 70; 1 ret temp 30; mdot', [(1, 3), (2, 4)])}
CONNECTION_BUNDLES = {1: ('1 type: type 1', [(1, 1, 'customer')]),  # id: description, [(sequence, type, description)]
                      2: ('1 type: type 2', [(1, 2, 'energy plant')])}
TEMPLATES = {'customer': (1, 'simple_consumer', 1), 'energy_plant': (1, 'heat_source', 2)}  # id, name, connection bundle


def only_for(wf, *templates):
    if wf.template not in templates:
        pytest.skip("not part of the template '{}'".format(wf.template))


def count(plugin, table, where=""):
    plugin.cur.execute('SELECT count(*) AS n FROM "{}".{} {};'.format(plugin.config['versionName'], table, where))  # nosec B608
    return plugin.cur.fetchone()['n']


def table_names(plugin, like):
    plugin.cur.execute("SELECT table_name FROM information_schema.tables WHERE table_schema=%s AND table_name LIKE %s;",
                       (plugin.config['versionName'], like))
    return [row['table_name'] for row in plugin.cur.fetchall()]


def read_osm_file(path):
    """Ways of an .osm (XML) file in the format of an Overpass 'out body geom' response."""
    root = ElementTree.parse(path).getroot()
    nodes = {n.get('id'): {'lat': float(n.get('lat')), 'lon': float(n.get('lon'))} for n in root.iter('node')}
    ways = []
    for way in root.iter('way'):
        ways.append({
            'type': 'way',
            'id': int(way.get('id')),
            'tags': {tag.get('k'): tag.get('v') for tag in way.iter('tag')},
            'geometry': [nodes[nd.get('ref')] for nd in way.iter('nd') if nd.get('ref') in nodes],
        })
    bounds = root.find('bounds')
    bbox = tuple(float(bounds.get(k)) for k in ['minlat', 'minlon', 'maxlat', 'maxlon'])
    return ways, bbox


def new_dialog(action):
    """Run action and return the dialog it opened."""
    before = {sip.unwrapinstance(w) for w in QApplication.topLevelWidgets()}
    action()
    wait(100)
    dialogs = [w for w in QApplication.topLevelWidgets()
               if isinstance(w, QDialog) and w.isVisible() and sip.unwrapinstance(w) not in before]
    assert dialogs, "no dialog opened"
    return dialogs[-1]


def select_id(combo, value):
    """select the entry 'id:name' of a table dropdown"""
    for i in range(combo.count()):
        if combo.itemText(i).split(':')[0] == str(value):
            combo.setCurrentIndex(i)
            return
    raise AssertionError("no entry with id {} in the dropdown ({})".format(
        value, [combo.itemText(i) for i in range(combo.count())]))


def add_table_row(dlg, values):
    """Add a row with the + button of a table dialog and fill it like a user.

    Dropdowns and checkboxes are set first with blocked signals (their slots locate the cell by the
    widget position, which is not laid out in the test); the text items are set afterwards and
    their itemChanged slots read the dropdowns (trace of the changed values)."""
    dlg.btn_add.click()
    table = dlg.tableWidget
    texts = []
    for col, value in enumerate(values):
        widget = table.cellWidget(0, col)
        if isinstance(widget, QComboBox):
            widget.blockSignals(True)
            select_id(widget, value)
            widget.blockSignals(False)
        elif isinstance(widget, QCheckBox):
            widget.blockSignals(True)
            widget.setChecked(bool(value))
            widget.blockSignals(False)
        else:
            texts.append((col, value))
    for col, value in texts:
        if table.item(0, col) is None:
            table.setItem(0, col, QTableWidgetItem(''))
        table.item(0, col).setText(str(value))


def save_dialog(dlg, errors):
    dlg.btn_ok.click()
    wait(200)
    errors.check()
    assert not dlg.isVisible(), "'{}' was not saved (invalid input?)".format(dlg.windowTitle())


def select_row_by_id(dlg, value):
    for row in range(dlg.tableWidget.rowCount()):
        if dlg.tableWidget.item(row, 0).text() == str(value):
            dlg.tableWidget.setCurrentCell(row, 1)
            return
    raise AssertionError("no row with id {} in '{}'".format(value, dlg.windowTitle()))


def public_rows(plugin, table):
    plugin.cur.execute('SELECT * FROM public.{} ORDER BY id;'.format(table))  # nosec B608
    return plugin.cur.fetchall()


@pytest.fixture
def osm_offline(monkeypatch, samples_dir):
    """OSM import from samples/OSM/map_1.osm instead of the Overpass API (no network, fixed data)."""
    import districts.districts
    from districts.osm import WorkerOSMImport

    ways, bbox = read_osm_file(os.path.join(samples_dir, 'OSM', 'map_1.osm'))

    def download_osm(self, south, west, north, east, feature_type, retries=3):
        key = {'buildings': 'building', 'streets': 'highway'}[feature_type]
        return [way for way in ways if key in way['tags']]

    monkeypatch.setattr(WorkerOSMImport, 'download_osm', download_osm)
    monkeypatch.setattr(districts.districts, 'get_overpass_bbox', lambda: bbox)


@pytest.fixture(scope="class", params=[HEATING, EMPTY, DB_DEFAULTS], ids=["heating", "empty", "db_defaults"])
def wf(request, districts_plugin, errors):
    """State of one workflow run (one project per template)."""
    template = request.param
    state = SimpleNamespace(
        template=template,
        plugin=districts_plugin,
        project_name="autotest_" + time.strftime("%m%d%H%M%S", time.localtime()) + "_" + template.replace(" ", "_").lower(),
        simulated=False,
    )
    yield state

    if request.config.getoption("--keep-projects"):
        return
    plugin = districts_plugin
    errors.clear()
    if state.project_name in (plugin.dlg.projectNames or []):
        deleteProject(state.project_name, plugin.dlg, plugin.cur_postgres, plugin.plugin_dir, plugin.config, plugin.model)
        wait(500)
    # DB and project folder of an aborted project creation
    plugin.cur_postgres.execute('DROP DATABASE IF EXISTS "{}" WITH (FORCE);'.format(state.project_name))  # nosec B608
    shutil.rmtree(os.path.join(plugin.config['pathProjects'], state.project_name), ignore_errors=True)
    # errors while deleting the project must not fail the first step of the next template
    cleanup_errors = errors.all()
    errors.clear()
    if cleanup_errors:
        warnings.warn("critical messages while deleting {}:\n{}".format(state.project_name, "\n".join(cleanup_errors)))


@pytest.mark.incremental
class TestWorkflow:

    # ---------------- project handling ----------------
    def test_create_project(self, wf, errors):
        plugin = wf.plugin
        plugin.showCreateNewProject()
        dlg = plugin.dlg_createNewProject
        dlg.project_name.setText(wf.project_name)
        dlg.selectTemplate.setCurrentText(tr('@default', TEMPLATE_KEYS[wf.template]))
        assert dlg.selectTemplate.currentData() == TEMPLATE_KEYS[wf.template]

        heating = wf.template == HEATING
        dlg.checkbox_db_defaultValues.setCheckState(uncheckState() if heating else checkState())
        dlg.checkbox_invokedFeatures.setCheckState(checkState() if heating else uncheckState())
        dlg.checkbox_prn.setCheckState(checkState() if heating else uncheckState())
        dlg.checkbox_DBResults.setCheckState(checkState() if heating else uncheckState())

        createNewProject(dlg, plugin)
        wait_for_process(dlg, timeout=60)
        errors.check()
        assert plugin.config['projectName'] == wf.project_name
        assert wf.project_name in plugin.dlg.projectNames

    def test_add_base_version(self, wf, errors):
        only_for(wf, EMPTY, DB_DEFAULTS)
        plugin = wf.plugin
        plugin.dlg_addBase = IDA_Districts_NameDialog(tr('@default', 'add_base_version'), tr('@default', 'add_base_version'), '', '')
        plugin.dlg_addBase.input.setText('base1')
        addBaseVersion(plugin.dlg_addBase, plugin)
        wait(500)
        errors.check()
        assert plugin.config['versionName'] == 'base1'

    # ---------------- import ----------------
    def _import(self, plugin, title, ok_fn, path, extensions, clear_old, timeout):
        plugin.openImportDlg(default_path=path, title=title, ok_fn=ok_fn, extensions=extensions)
        plugin.dlg_import.checkBoxClearOldFeatures.setCheckState(checkState() if clear_old else uncheckState())
        ok_fn(plugin.dlg_import)
        wait_for_process(plugin.dlg_import, timeout=timeout)

    def _import_osm(self, plugin, streets, buildings, timeout):
        plugin.openImportOSMDlg()
        dlg = plugin.dlg_osm_import
        dlg.checkBox_streets.setChecked(streets)
        dlg.checkBox_buildings.setChecked(buildings)
        dlg.checkBoxClearOldFeatures.setCheckState(checkState())
        plugin.importFromOSM(dlg)
        wait_for_process(dlg, timeout=timeout)
        closeDialog(dlg)

    def test_import_streets(self, wf, errors, osm_offline):
        only_for(wf, EMPTY, DB_DEFAULTS)
        plugin = wf.plugin
        self._import_osm(plugin, streets=True, buildings=False, timeout=60)
        errors.check()
        assert count(plugin, 'streets') > 0

    def test_import_buildings(self, wf, errors, osm_offline):
        only_for(wf, EMPTY, DB_DEFAULTS)
        plugin = wf.plugin
        self._import_osm(plugin, streets=False, buildings=True, timeout=60)
        errors.check()
        assert count(plugin, 'buildings') > 0

    def test_import_elevation_data(self, wf, errors, samples_dir):
        only_for(wf, EMPTY, DB_DEFAULTS)
        plugin = wf.plugin
        for i, tile in enumerate(['N59E017.hgt', 'N59E018.hgt']):
            self._import(plugin, 'Elevation data', plugin.importElevationData,
                         os.path.join(samples_dir, 'elevation_data', tile), '*.hgt;*.tif;*.tiff',
                         clear_old=(i == 0), timeout=60)
        closeDialog(plugin.dlg_import)
        errors.check()
        assert count(plugin, 'terrain') > 0

    # ---------------- preprocessing ----------------
    def test_place_main_energy_plant(self, wf, errors):
        only_for(wf, EMPTY, DB_DEFAULTS)
        plugin = wf.plugin
        layers = QgsProject.instance().mapLayersByName(tr('@default', 'energy_plants'))
        assert layers, "layer 'energy_plants' not found"
        layer = layers[0]
        assert layer.geometryType() == Qgis.GeometryType.Point

        n_before = count(plugin, 'energy_plants')
        feature = QgsFeature(layer.fields())
        feature.setGeometry(QgsGeometry.fromPointXY(QgsPointXY(1010365, 6615369)))
        feature['template'] = 1
        feature['network'] = [1]
        feature['submodel'] = 1
        layer.startEditing()
        res, _ = layer.dataProvider().addFeatures([feature])
        if res:
            layer.commitChanges()
        else:
            layer.rollBack()
        errors.check()
        assert res, "failed to add the energy plant"
        assert count(plugin, 'energy_plants') == n_before + 1

    def test_pipe_laying_without_pipe_bundles(self, wf, errors):
        """The empty project has no pipe bundles: the pipe laying must report it and finish (not hang)."""
        only_for(wf, EMPTY)
        plugin = wf.plugin
        plugin.pipeLayingAlgorithm()
        dlg = plugin.dlg_pipeLayingAlgorithm
        dlg.check_heating_network.setCheckState(checkState())
        dlg.execute()
        wait(500)
        messages = errors.all()
        errors.clear()
        wait_for_process(dlg, timeout=30)
        closeDialog(dlg)
        assert any("No pipe bundle selected or available (heating network)" in m for m in messages), messages
        assert not getattr(dlg, "process_running", False)

    # ---------------- resources (empty project: create everything with the resource dialogs) ----------------
    def _table_with_rows(self, plugin, errors, open_fn, rows):
        dlg = new_dialog(open_fn)
        for row in rows:
            add_table_row(dlg, row)
        save_dialog(dlg, errors)

    def _child_rows(self, plugin, errors, open_fn, parent_id, rows):
        """open the sub table of a row (e.g. the layers of a pipe construction) and fill it"""
        dlg = new_dialog(open_fn)
        select_row_by_id(dlg, parent_id)
        child = new_dialog(dlg.btn_open.click)
        for row in rows:
            add_table_row(child, row)
        save_dialog(child, errors)
        closeDialog(dlg)

    def test_create_materials(self, wf, errors):
        only_for(wf, EMPTY)
        plugin = wf.plugin
        self._table_with_rows(plugin, errors, plugin.manageMaterials, MATERIALS)
        assert [r['name'] for r in public_rows(plugin, 'materials')] == [m[1] for m in MATERIALS]

    def test_create_pipe_constructions(self, wf, errors):
        only_for(wf, EMPTY)
        plugin = wf.plugin
        self._table_with_rows(plugin, errors, plugin.managePipeConstructions, [PIPE_CONSTRUCTION])
        self._child_rows(plugin, errors, plugin.managePipeConstructions, PIPE_CONSTRUCTION[0], PIPE_LAYERS)
        assert len(public_rows(plugin, 'pipe_constructions')) == 1
        assert len(public_rows(plugin, 'pipe_layers')) == len(PIPE_LAYERS)

    def test_create_pipes(self, wf, errors):
        only_for(wf, EMPTY)
        plugin = wf.plugin
        self._table_with_rows(plugin, errors, plugin.managePipes, PIPES)
        assert len(public_rows(plugin, 'pipes')) == len(PIPES)

    def test_create_pipe_bundles(self, wf, errors):
        only_for(wf, EMPTY)
        plugin = wf.plugin
        self._table_with_rows(plugin, errors, plugin.managePipeBundlesTypes, [PIPE_BUNDLE])
        self._child_rows(plugin, errors, plugin.managePipeBundlesTypes, PIPE_BUNDLE[0], BUNDLE_PIPES)
        assert len(public_rows(plugin, 'pipe_bundle_types')) == 1
        assert len(public_rows(plugin, 'bundle_pipes')) == len(BUNDLE_PIPES)

    def test_create_connections(self, wf, errors):
        only_for(wf, EMPTY)
        plugin = wf.plugin
        self._table_with_rows(plugin, errors, plugin.manageConnections, CONNECTIONS)
        rows = public_rows(plugin, 'connections')
        assert [(r['id'], r['p_ctrl']) for r in rows] == [(c[0], c[2]) for c in CONNECTIONS]

    def test_create_connection_types(self, wf, errors):
        only_for(wf, EMPTY)
        plugin = wf.plugin
        self._table_with_rows(plugin, errors, plugin.manageConnectionTypes,
                              [(i, description) for i, (description, _) in CONNECTION_TYPES.items()])
        for type_id, (_, connections) in CONNECTION_TYPES.items():
            self._child_rows(plugin, errors, plugin.manageConnectionTypes, type_id, connections)
        assert len(public_rows(plugin, 'connection_type_connections')) == sum(
            len(c) for _, c in CONNECTION_TYPES.values())

    def test_create_connection_bundles(self, wf, errors):
        only_for(wf, EMPTY)
        plugin = wf.plugin
        self._table_with_rows(plugin, errors, plugin.manageConnBundleTypes,
                              [(i, description) for i, (description, _) in CONNECTION_BUNDLES.items()])
        for bundle_id, (_, types) in CONNECTION_BUNDLES.items():
            self._child_rows(plugin, errors, plugin.manageConnBundleTypes, bundle_id, types)
        assert len(public_rows(plugin, 'bundle_type_conns')) == len(CONNECTION_BUNDLES)

    def test_create_customer_templates(self, wf, errors):
        self._create_template(wf, errors, 'customer')

    def test_create_energy_plant_templates(self, wf, errors):
        self._create_template(wf, errors, 'energy_plant')

    def _create_template(self, wf, errors, template_type):
        only_for(wf, EMPTY)
        plugin = wf.plugin
        template_id, name, bundle = TEMPLATES[template_type]
        self._table_with_rows(plugin, errors, lambda: plugin.manageTemplates(template_type),
                              [(template_id, name, bundle, '')])
        rows = public_rows(plugin, template_type + '_templates')
        assert [(r['template'], r['template_name'], r['conn_bundle_type']) for r in rows] == [(template_id, name, bundle)]
        model = os.path.join(plugin.config['pathProjects'], plugin.config['projectName'],
                             template_type + '_templates', '{}_{}.idm'.format(template_id, name))
        assert os.path.exists(model), "template model not written: " + model

    def test_pipe_laying_algorithm(self, wf, errors):
        only_for(wf, EMPTY, DB_DEFAULTS)
        plugin = wf.plugin
        plugin.pipeLayingAlgorithm()
        dlg = plugin.dlg_pipeLayingAlgorithm
        dlg.check_heating_network.setCheckState(checkState())
        dlg.execute()
        wait_for_process(dlg, timeout=120)
        dlg.saveResults()
        wait(500)
        closeDialog(dlg)
        errors.check()
        assert count(plugin, 'lines') > 0

    def test_generate_network_topology(self, wf, errors):
        only_for(wf, HEATING)
        plugin = wf.plugin
        plugin.generateNetworkTopology()
        dlg = plugin.window_topology
        dlg.rbtn_override_templates.setChecked(True)
        for checkbox in [dlg.check_del_network_ends, dlg.check_connectCustomers, dlg.check_connectPlants,
                         dlg.check_deleteUnconnectedCustomers, dlg.check_deleteUnconnectedLines]:
            checkbox.setCheckState(checkState())
        dlg.combo_network_models.setItemChecked(1, True)
        dlg.execute()
        wait_for_process(dlg, timeout=60)
        dlg.saveResults()
        wait(500)
        closeDialog(dlg)
        errors.check()
        assert count(plugin, 'lines') > 0
        assert count(plugin, 'junctions') > 0

    def test_pipe_sizing(self, wf, errors):
        plugin = wf.plugin
        only_for(wf, *NETWORK_TEMPLATES)
        if wf.template in (EMPTY, DB_DEFAULTS):
            fid = 1
            load_attribute = ShowLoadAttributeDialog(fid)
            load_attribute.dlg.radioButton_newAttribute.setChecked(True)
            load_attribute.dlg.lineEdit_newAttribute.setText('load_w')
            load_attribute.dlg.checkBox_allCustomers.setChecked(True)
            setLoadAttribute(load_attribute.dlg, fid)
            errors.check()

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
        startPipeSizing(plugin.config, dlg, plugin.plugin_dir)
        wait_for_process(dlg, timeout=60)
        savePipeSizingResults(plugin.config, plugin.conn, dlg)
        wait(500)
        closeDialog(dlg)
        errors.check()
        assert count(plugin, 'lines', 'WHERE pipe_bundle_type_id IS NULL') == 0

    # ---------------- modelling and simulation ----------------
    def test_requested_outputs(self, wf, errors):
        only_for(wf, EMPTY, DB_DEFAULTS)
        plugin = wf.plugin
        plugin.showRequestedOutputs()
        dlg = plugin.dlg_outputs
        for checkbox in [dlg.checkBoxSubstationPower, dlg.checkBoxSubstationConnTemp, dlg.checkBoxSubstationPressure,
                         dlg.checkBoxSubstationMassflow, dlg.checkBoxSubstationHeatbalance, dlg.checkBoxSubstationTair,
                         dlg.checkBoxPressureDistribution, dlg.checkBoxMdotNode, dlg.checkBoxVPipe, dlg.checkBoxTempPipe,
                         dlg.checkBoxPlantPower, dlg.checkBoxPlantConnTemp, dlg.checkBoxPlantPressure,
                         dlg.checkBoxPlantMassflow]:
            checkbox.setChecked(True)
        dlg.outputTimestep.setValue(0.25)
        setRequestedOutputs(plugin.config, plugin.plugin_dir, dlg, plugin.requestedOutputs)
        wait_for_process(dlg, timeout=30)
        closeDialog(dlg)
        errors.check()

    def test_feature_parameter_mapping(self, wf, errors):
        only_for(wf, HEATING)
        plugin = wf.plugin
        plugin.showParmMapping()
        dlg = plugin.dlg_featureParm
        table = dlg.tableWidget_parameters
        table.setRowCount(0)
        setFeatureParm(dlg, plugin.conn, plugin.config, plugin.plugin_dir)
        for attribute, model_parm, model, scope in [('"load_w"', 'FloorArea', 'Lm_H_G_L_Mctrl', ':FEATURE'),
                                                    ('"gfa"', 'X', 'Load limit', ':FEATURE')]:
            addParmTableRow(dlg, plugin.cur, plugin.config)
            table.item(0, 1).setText(attribute)
            table.item(0, 3).setText(model_parm)
            table.item(0, 4).setText(model)
            table.item(0, 5).setText(scope)
        setFeatureParm(dlg, plugin.conn, plugin.config, plugin.plugin_dir)
        closeDialog(dlg)
        errors.check()

    def test_build_network_model(self, wf, errors):
        only_for(wf, *NETWORK_TEMPLATES)
        plugin = wf.plugin
        plugin.showBuildModel()
        dlg = plugin.dlg_buildModel
        dlg.combo_network_models.setItemChecked(1, True)
        dlg.combo_submodels.setItemChecked(1, True)
        buildModel(dlg, plugin)
        wait_for_process(dlg, timeout=60)
        closeDialog(dlg)
        errors.check()

    @pytest.mark.ida
    def test_run_simulation(self, wf, errors):
        only_for(wf, *NETWORK_TEMPLATES)
        plugin = wf.plugin
        if not os.path.exists(os.path.join(plugin.config['pathDistricts'], 'bin', 'ida-districts.exe')):
            pytest.skip("IDA Districts not installed in {}".format(plugin.config['pathDistricts']))
        plugin.showRunModel()
        dlg = plugin.dlg_runModel
        dlg.combo_submodels.setItemChecked(1, checked=True)
        runModel(dlg, plugin.plugin_dir, plugin.config)
        wait_for_process(dlg, timeout=300)
        errors.check()
        # a failed IDA simulation is only shown in the status bar of the dialog
        assert dlg.status_bar.currentMessage() == 'Simulation finished', \
            "simulation status: '{}'".format(dlg.status_bar.currentMessage())
        wf.simulated = True

    # ---------------- results and visualization ----------------
    def _require_simulation(self, wf):
        if not wf.simulated:
            pytest.skip("no simulation results")

    @pytest.mark.ida
    def test_load_results(self, wf, errors):
        self._require_simulation(wf)
        plugin = wf.plugin
        plugin.showLoadResults()
        dlg = plugin.dlg_loadResults
        dlg.combo_submodels.setItemChecked(1, True)
        loadResults(dlg, plugin)
        wait_for_process(dlg, timeout=120)
        closeDialog(dlg)
        errors.check()
        assert table_names(plugin, 'customer\\_s\\_%'), "no customer result tables"
        assert table_names(plugin, 'line\\_s\\_%'), "no line result tables"

    @pytest.mark.ida
    def test_show_customer_load_on_map(self, wf, errors):
        self._require_simulation(wf)
        plugin = wf.plugin
        plugin.showDataOnMap()
        dlg = plugin.dlg_showOnMap
        dlg.rbtn_customers.setChecked(True)
        dlg.checkbox_varColor.setChecked(True)
        dlg.color_var.setCurrentText('power$1_1')
        dlg.color_function.setCurrentText('Values')
        dlg.checkbox_varSize.setChecked(True)
        dlg.rbtn_sizePar.setChecked(True)
        dlg.size_par.setCurrentText('gfa')
        dlg.layer_name.setText('customer_results_load_values')
        wait(1000)
        showOnMap(dlg, plugin)
        wait_for_process(dlg, timeout=30)
        closeDialog(dlg)
        errors.check()
        assert QgsProject.instance().mapLayersByName('customer_results_load_values')

    @pytest.mark.ida
    def test_show_line_temperature_on_map(self, wf, errors):
        self._require_simulation(wf)
        plugin = wf.plugin
        plugin.showDataOnMap()
        dlg = plugin.dlg_showOnMap
        customer_ids = [int(table.item(row, 0).text()) for row in range(table.rowCount())]
        assert len(set(customer_ids)) == 2, "new rows got the same id: {}".format(customer_ids)
        # unsaved customer rows are kept when switching to energy plants and back, new ids stay unique
        dlg.rbtn_plants.setChecked(True)
        plant_rows = table.rowCount()
        addParmTableRow(dlg, plugin.cur, plugin.config)
        assert int(table.item(0, 0).text()) > max(customer_ids)
        dlg.rbtn_customers.setChecked(True)
        assert sorted(int(table.item(row, 0).text()) for row in range(table.rowCount())) == sorted(customer_ids)
        dlg.rbtn_plants.setChecked(True)
        assert table.rowCount() == plant_rows + 1
        table.removeRow(0)  # don't save the empty energy plant mapping
        dlg.rbtn_customers.setChecked(True)
        dlg.rbtn_lines.setChecked(True)
        dlg.checkbox_varColor.setChecked(True)
        dlg.featureGroupChanged(dlg.rbtn_lines)
        dlg.color_var.setCurrentText('temp$1')
        dlg.color_function.setCurrentText('Values')
        dlg.layer_name.setText('lines_results_supply_temperature_values')
        wait(1000)
        showOnMap(dlg, plugin)
        wait_for_process(dlg, timeout=30)
        closeDialog(dlg)
        errors.check()
        assert QgsProject.instance().mapLayersByName('lines_results_supply_temperature_values')

    @pytest.mark.ida
    def test_path_report(self, wf, errors):
        self._require_simulation(wf)
        plugin = wf.plugin
        plugin.showPathReports()
        dlg = plugin.dlg_pathReports
        dlg.rbtn_pathPressure.setChecked(True)
        dlg.rbtn_weakPoint.setChecked(True)
        dlg.rbtn_Date.setChecked(True)
        # the simulation year depends on the template: 7 o'clock of the first result day
        plugin.cur.execute('SELECT min(time) AS t0 FROM "{}"."line_s_p$1";'.format(plugin.config['versionName']))  # nosec B608
        dlg.date_input.setText((plugin.cur.fetchone()['t0'] + timedelta(hours=7)).strftime('%Y-%m-%d %H:%M:%S'))
        dlg.dp_recalc.setChecked(True)
        dlg.dp_min_recalc.setText('0.8')
        dlg.sup_sequence.setCurrentIndex(0)
        dlg.ret_sequence.setCurrentIndex(1)
        runPathReports(dlg, plugin)
        wait_for_process(dlg, timeout=30)
        errors.check()
