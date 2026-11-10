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
from qgis.core import (
    Qgis, QgsCategorizedSymbolRenderer, QgsFeature, QgsGeometry, QgsGraduatedSymbolRenderer, QgsPointXY, QgsProject,
    QgsRuleBasedRenderer,
)
from qgis.PyQt import sip
from qgis.PyQt.QtCore import QSettings, Qt
from qgis.PyQt.QtWidgets import QApplication, QCheckBox, QComboBox, QDialog, QMessageBox, QTableWidgetItem

from districts.ida_mosim import buildModel, checkTopologyBeforeBuild, runModel, setRequestedOutputs
from districts.ida_ph import (
    HeightCheckDialog, ShowLoadAttributeDialog, ZetaDialog, addBaseVersion, createNewProject, deleteProject, loadVersion,
    runHeightCheck, runZetaVisualization, setLoadAttribute,
)
from districts.ida_ph_dialog import ApproveDialog, IDA_Districts_NameDialog
from districts.ida_rv import loadResults, runPathReports, showOnMap
from districts.pipe_sizing import savePipeSizingResults
from districts.utility_functions import reports
from districts.utility_functions.dialog import addParmTableRow, checkState, closeDialog, uncheckState
from districts.utility_functions.files import districtsModelerTempDir
from districts.utility_functions.height_check import HEIGHT_CHECK_PROPERTY
from districts.utility_functions.zeta import ZETA_DEFAULTS, ZETA_PROPERTY, loadZetaValues, saveZetaValues, zetaTables
from districts.utility_functions.invoke import setFeatureParm
from districts.utility_functions.sensor_signals import getSensorData
from districts.utility_functions.show_on_map import RESULT_VIS_PROPERTY
from districts.utility_functions.topology import checkNetworkTopology, getUnconnectedFeatures
from districts.utility_functions.translations import tr

from .conftest import wait, wait_for_process, wait_until

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
# simulatable templates imported from a project of the template 'DB default values'
IMPORTED_TEMPLATES = {'customer': 'simplified_consumer', 'energy_plant': 'ideal_heat_source'}


def only_for(wf, *templates):
    if wf.template not in templates:
        pytest.skip("not part of the template '{}'".format(wf.template))


def count(plugin, table, where=""):
    plugin.cur.execute('SELECT count(*) AS n FROM "{}".{} {};'.format(plugin.config['versionName'], table, where))  # nosec B608
    return plugin.cur.fetchone()['n']


def assert_junction_zeta(plugin, values=None):
    """all junction connections have a calculated zeta: tees 2x run/2 + branch (+ reducer), network ends 0
    (values: tee/cross values of the dialog, default values if None)"""
    zeta_run, zeta_branch = zetaTables(values)
    plugin.cur.execute("""SELECT jc.jid, count(*) AS n, count(jc.zeta) AS n_zeta, coalesce(sum(jc.zeta), 0) AS zeta_sum,
       coalesce(max(jc.zeta), 0) AS zeta_max
FROM "{v}".junction_connections jc GROUP BY jc.jid;""".format(v=plugin.config['versionName']))  # nosec B608
    rows = plugin.cur.fetchall()
    assert rows, "no junction connections"
    assert all(r['n_zeta'] == r['n'] for r in rows), [r['jid'] for r in rows if r['n_zeta'] != r['n']]
    for r in rows:
        if r['n'] == 1:
            assert r['zeta_sum'] == 0, dict(r)
        elif r['n'] == 3:
            assert float(r['zeta_sum']) >= zeta_run[3] + zeta_branch[3] - zeta_run[3] / 2 - 1e-4, dict(r)
            assert float(r['zeta_max']) >= zeta_branch[3] - zeta_run[3] / 2 - 1e-4, dict(r)
            if values:  # without a reducer exactly the values of the dialog
                assert float(r['zeta_sum']) <= zeta_run[3] + zeta_branch[3] - zeta_run[3] / 2 + 1.0, dict(r)
    print('junction zeta: {} junctions, connections per junction {}'.format(
        len(rows), sorted({r['n'] for r in rows})))


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


def plugin_state(plugin):
    """diagnostics for a dialog that did not open (no DB connection / no version loaded)"""
    bar = plugin.iface.messageBar()
    messages = []
    if hasattr(bar, 'get_messages'):  # pytest-qgis mock message bar
        for level in (Qgis.MessageLevel.Info, Qgis.MessageLevel.Warning):
            messages += [str(m) for m in bar.get_messages(level)]
    return "conn={!r}, projectName={!r}, versionName={!r}, settings versionName={!r}, messages={}".format(
        plugin.conn, plugin.config.get('projectName'), plugin.config.get('versionName'),
        QSettings().value('districts/versionName'), messages)


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


def project_name_for(suffix):
    return "autotest_" + time.strftime("%m%d%H%M%S", time.localtime()) + "_" + suffix.replace(" ", "_").lower()


def create_project(plugin, errors, project_name, template):
    """Create a project with the 'new project' dialog (the project is loaded afterwards)."""
    plugin.showCreateNewProject()
    dlg = plugin.dlg_createNewProject
    dlg.project_name.setText(project_name)
    dlg.selectTemplate.setCurrentText(tr('@default', TEMPLATE_KEYS[template]))
    assert dlg.selectTemplate.currentData() == TEMPLATE_KEYS[template]

    heating = template == HEATING
    dlg.checkbox_db_defaultValues.setCheckState(uncheckState() if heating else checkState())
    dlg.checkbox_invokedFeatures.setCheckState(checkState() if heating else uncheckState())
    dlg.checkbox_prn.setCheckState(checkState() if heating else uncheckState())
    dlg.checkbox_DBResults.setCheckState(checkState() if heating else uncheckState())

    createNewProject(dlg, plugin)
    assert not dlg.btn_ok.isEnabled()  # no second project creation while the first is running
    wait_for_process(dlg, timeout=60)
    errors.check()
    assert plugin.config['projectName'] == project_name
    assert project_name in plugin.dlg.projectNames


def delete_project(plugin, errors, project_name):
    errors.clear()
    if project_name in (plugin.dlg.projectNames or []):
        dlg = ApproveDialog(tr('@default', 'delete_project'), project_name)
        dlg.show()
        deleteProject(project_name, plugin.dlg, plugin.cur_postgres, plugin.plugin_dir, plugin.config, plugin.model, dlg=dlg)
        assert not dlg.btn_ok.isEnabled()  # no second delete while the first is running
        assert not dlg.isVisible()
        wait(500)
    # DB and project folder of an aborted project creation
    plugin.cur_postgres.execute('DROP DATABASE IF EXISTS "{}" WITH (FORCE);'.format(project_name))  # nosec B608
    shutil.rmtree(os.path.join(plugin.config['pathProjects'], project_name), ignore_errors=True)
    # errors while deleting the project must not fail the first step of the next template
    cleanup_errors = errors.all()
    errors.clear()
    if cleanup_errors:
        warnings.warn("critical messages while deleting {}:\n{}".format(project_name, "\n".join(cleanup_errors)))


@pytest.fixture(scope="session")
def resource_source_project(request, districts_plugin, errors):
    """Project (template 'DB default values') whose customer and energy plant templates are imported
    into the empty project, like a user takes over resources from an existing project."""
    project_name = project_name_for("resources")
    create_project(districts_plugin, errors, project_name, DB_DEFAULTS)
    yield project_name
    if not request.config.getoption("--keep-projects"):
        delete_project(districts_plugin, errors, project_name)


@pytest.fixture(scope="class", params=[HEATING, EMPTY, DB_DEFAULTS], ids=["heating", "empty", "db_defaults"])
def wf(request, districts_plugin, errors):
    """State of one workflow run (one project per template)."""
    template = request.param
    if template == EMPTY:
        # created before the empty project, which is then the loaded project
        request.getfixturevalue("resource_source_project")
    state = SimpleNamespace(
        template=template,
        plugin=districts_plugin,
        project_name=project_name_for(template),
        simulated=False,
        imported_templates={},  # template type: template id (empty project)
    )
    yield state

    if not request.config.getoption("--keep-projects"):
        delete_project(districts_plugin, errors, state.project_name)


@pytest.mark.incremental
class TestWorkflow:

    # ---------------- project handling ----------------
    def test_create_project(self, wf, errors):
        create_project(wf.plugin, errors, wf.project_name, wf.template)

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

    def test_import_templates(self, wf, errors, request):
        """The generated templates are skeletons to be completed in IDA: import simulatable templates
        (with their connection bundles, types and connections) from another project."""
        only_for(wf, EMPTY)
        # not as a test argument: pytest sets up argument fixtures before only_for skips the test, i.e. the
        # session fixture would create (and load!) the resources project in the middle of the heating run.
        # For the empty project wf has already created it (before the empty project was created and loaded).
        resource_source_project = request.getfixturevalue('resource_source_project')
        plugin = wf.plugin
        plugin.show_importResources()
        dlg = plugin.dlg_importResources
        dlg.rbtn_db.setChecked(True)
        dlg.comboBox_db.setCurrentText(resource_source_project)
        wait(200)
        assert dlg.comboBox_db.currentText() == resource_source_project
        for template_type, name in IMPORTED_TEMPLATES.items():
            table = getattr(dlg, 'tableWidget_{}_templates'.format(template_type))
            rows = [r for r in range(table.rowCount()) if table.item(r, 2).data(Qt.ItemDataRole.UserRole) == name]
            assert rows, "template '{}' not found in {}".format(name, resource_source_project)
            table.cellWidget(rows[0], 0).setChecked(True)
        dlg.btn_import_selection.click()
        wait(500)
        errors.check()
        assert not dlg.isVisible(), "import dialog still open"

        for template_type, name in IMPORTED_TEMPLATES.items():
            plugin.cur.execute('SELECT template FROM public.{}_templates WHERE template_name=%s;'.format(template_type),  # nosec B608
                               (name,))
            row = plugin.cur.fetchone()
            assert row, "template '{}' not imported".format(name)
            wf.imported_templates[template_type] = row['template']
            model = os.path.join(plugin.config['pathProjects'], plugin.config['projectName'],
                                 template_type + '_templates', '{}_{}.idm'.format(row['template'], name))
            assert os.path.exists(model), "template model not imported: " + model

    def test_assign_imported_energy_plant_template(self, wf, errors):
        """like a user: change the template of the main energy plant in the attribute form"""
        only_for(wf, EMPTY)
        plugin = wf.plugin
        layer = QgsProject.instance().mapLayersByName(tr('@default', 'energy_plants'))[0]
        template = wf.imported_templates['energy_plant']
        idx = layer.fields().indexOf('template')
        layer.startEditing()
        for feature in layer.getFeatures():
            layer.changeAttributeValue(feature.id(), idx, template)
        assert layer.commitChanges(), layer.commitErrors()
        errors.check()
        assert count(plugin, 'energy_plants', 'WHERE template<>{}'.format(template)) == 0

    def test_pipe_laying_algorithm(self, wf, errors):
        only_for(wf, EMPTY, DB_DEFAULTS)
        plugin = wf.plugin
        plugin.pipeLayingAlgorithm()
        dlg = plugin.dlg_pipeLayingAlgorithm
        dlg.check_heating_network.setCheckState(checkState())
        dlg.check_calc_junction_zeta.setChecked(True)
        assert 'Idelchik' in dlg.text_info.toPlainText() and 'Dijkstra' in dlg.text_info.toPlainText()
        customer_template = wf.imported_templates.get('customer')
        if customer_template:
            # the connected customers get the imported template
            select_id(dlg.heating_template_customer, customer_template)
        dlg.execute()
        wait_for_process(dlg, timeout=120)
        dlg.saveResults()
        wait(500)
        closeDialog(dlg)
        errors.check()
        assert count(plugin, 'lines') > 0
        if customer_template:
            assert count(plugin, 'customers', 'WHERE template<>{}'.format(customer_template)) == 0
        assert_junction_zeta(plugin)

    def test_generate_network_topology(self, wf, errors):
        only_for(wf, HEATING)
        plugin = wf.plugin
        plugin.generateNetworkTopology()
        assert hasattr(plugin, 'window_topology'), "topology dialog not opened: {}".format(plugin_state(plugin))
        dlg = plugin.window_topology
        dlg.rbtn_override_templates.setChecked(True)
        assert 'Idelchik' in dlg.text_info.toPlainText() and 'terrain' in dlg.text_info.toPlainText()
        for checkbox in [dlg.check_del_network_ends, dlg.check_connectCustomers, dlg.check_connectPlants,
                         dlg.check_deleteUnconnectedCustomers, dlg.check_deleteUnconnectedLines, dlg.check_calc_junction_zeta]:
            checkbox.setCheckState(checkState())
        # own values of the tee and cross (spin boxes), the values used last are restored afterwards
        assert not dlg.junction_zeta.values_widget.isHidden()
        dlg.check_calc_junction_zeta.setChecked(False)
        assert dlg.junction_zeta.values_widget.isHidden()
        dlg.check_calc_junction_zeta.setChecked(True)
        assert not dlg.junction_zeta.values_widget.isHidden()
        saved_values = loadZetaValues()
        custom = {'tee_run': 0.6, 'tee_branch': 2.0, 'cross_run': 0.8, 'cross_branch': 2.2}
        for key, value in custom.items():
            dlg.junction_zeta.spinboxes[key].setValue(value)
        dlg.combo_network_models.setItemChecked(1, True)
        try:
            dlg.execute()
            wait_for_process(dlg, timeout=60)
            dlg.saveResults()
            wait(500)
            closeDialog(dlg)
            errors.check()
            assert loadZetaValues() == custom  # kept for the next time
        finally:
            saveZetaValues(saved_values)
        assert count(plugin, 'lines') > 0
        assert count(plugin, 'junctions') > 0
        assert_junction_zeta(plugin, custom)
        dlg.junction_zeta.setDefaults()
        assert {k: s.value() for k, s in dlg.junction_zeta.spinboxes.items()} == ZETA_DEFAULTS

    def test_height_check(self, wf, errors):
        """height check action (lines, customers, energy plants): graduated colors and consistency check as memory layers
        in the group 'height check', removed when the version is loaded again"""
        only_for(wf, *NETWORK_TEMPLATES)
        plugin = wf.plugin
        for layer_name in ['lines', 'customers', 'energy_plants']:
            layer = QgsProject.instance().mapLayersByName(tr('@default', layer_name))[0]
            names = [a.name() for a in layer.actions().actions()]
            assert names.count(tr('@default', 'height_check')) == 1, (layer_name, names)

        def height_layers(mode):
            return [l for l in QgsProject.instance().mapLayers().values() if l.customProperty(HEIGHT_CHECK_PROPERTY) == mode]

        dlg = HeightCheckDialog()
        dlg.checkBox_junctions.setChecked(True)
        dlg.radioButton_graduated.setChecked(True)
        dlg.comboBox_colorRamp.setCurrentText('Spectral')
        runHeightCheck(dlg)
        errors.check()
        layers = height_layers('graduated')
        assert len(layers) == 4, [l.name() for l in layers]
        for layer in layers:
            assert isinstance(layer.renderer(), QgsRuleBasedRenderer), layer.name()
        # lines split into their segments, with the attributes of the line
        lines_layer = [l for l in layers if l.geometryType() == Qgis.GeometryType.Line][0]
        assert len({f['id'] for f in lines_layer.getFeatures()}) == count(plugin, 'lines')
        plugin.cur.execute('SELECT sum(ST_NPoints(geom) - 1) AS n FROM "{}".lines;'.format(plugin.config['versionName']))
        assert lines_layer.featureCount() == plugin.cur.fetchone()['n']
        assert {'z_mean', 'dz', 'seg', 'z_seg', 'seg_slope_pct'} <= set(lines_layer.fields().names())
        missing = {l.name(): sum(1 for f in l.getFeatures() if f['z_missing']) for l in layers}
        print('height check (graduated), missing heights:', missing)
        # junctions get their height from the lines (pipe laying / network topology)
        if missing['{} – {}'.format(tr('@default', 'lines'), tr('@default', 'height'))] == 0:
            assert missing['{} – {}'.format(tr('@default', 'junctions'), tr('@default', 'height'))] == 0, missing

        dlg = HeightCheckDialog()
        dlg.radioButton_consistency.setChecked(True)
        runHeightCheck(dlg)
        errors.check()
        issues = {}
        for layer in height_layers('consistency'):
            assert isinstance(layer.renderer(), QgsCategorizedSymbolRenderer), layer.name()
            for f in layer.getFeatures():
                issues[f['issue']] = issues.get(f['issue'], 0) + 1
        print('height check (consistency):', issues)
        assert len(height_layers('graduated')) == 4, "the consistency check must keep the graduated layers"

        loadVersion(main=plugin)
        wait(3000)
        assert not [l for l in QgsProject.instance().mapLayers().values() if l.customProperty(HEIGHT_CHECK_PROPERTY)]

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
        dlg.check_calc_junction_zeta.setChecked(True)
        assert 'Idelchik' in dlg.text_info.toPlainText() and 'Δp′' in dlg.text_info.toPlainText()
        # old project: junction_connections without zeta (added again when the results are saved)
        version = plugin.config['versionName']
        plugin.cur.execute('ALTER TABLE "{}".junction_connections DROP COLUMN IF EXISTS zeta;'.format(version))
        plugin.cur.execute('ALTER TABLE temp.junction_connections DROP COLUMN IF EXISTS zeta;')
        dlg.btn_start.pressed.emit()  # like the user: startPipeSizing via runWithButtonDisabled
        assert not dlg.btn_start.isEnabled()  # no second sizing run while the first is running
        wait_for_process(dlg, timeout=60)
        wait_until(lambda: dlg.btn_start.isEnabled(), 10, "start button not enabled again after pipe sizing")
        savePipeSizingResults(plugin.config, plugin.conn, dlg)
        wait(500)
        closeDialog(dlg)
        errors.check()
        assert count(plugin, 'lines', 'WHERE pipe_bundle_type_id IS NULL') == 0
        assert_junction_zeta(plugin)
        # the sized pipes have different diameters: reducers and tees with a smaller branch
        plugin.cur.execute('SELECT count(DISTINCT pipe_bundle_type_id) AS n FROM "{}".lines;'.format(version))  # nosec B608
        print('pipe sizing: pipe bundle types', plugin.cur.fetchone()['n'])

    def test_zeta_values(self, wf, errors):
        """zeta action (lines, junctions): memory layers in the group 'zeta values' with the zeta used in the network model,
        removed when the version is loaded again"""
        only_for(wf, *NETWORK_TEMPLATES)
        plugin = wf.plugin
        version = plugin.config['versionName']
        for layer_name in ['lines', 'junctions']:
            layer = QgsProject.instance().mapLayersByName(tr('@default', layer_name))[0]
            names = [a.name() for a in layer.actions().actions()]
            assert names.count(tr('@default', 'zeta_values')) == 1, (layer_name, names)

        # a user value in lines.zeta and junctions.zeta is added to the calculated values
        plugin.cur.execute('SELECT min(id) AS id FROM "{}".lines;'.format(version))  # nosec B608
        lid = plugin.cur.fetchone()['id']
        plugin.cur.execute('UPDATE "{}".lines SET zeta=2 WHERE id={};'.format(version, lid))  # nosec B608
        plugin.cur.execute('SELECT min(jid) AS jid FROM "{}".junction_connections WHERE lid={};'.format(version, lid))  # nosec B608
        jid = plugin.cur.fetchone()['jid']
        if jid:
            plugin.cur.execute('UPDATE "{}".junctions SET zeta=1 WHERE id={};'.format(version, jid))  # nosec B608

        dlg = ZetaDialog()
        assert not hasattr(dlg, 'checkBox_junctions')
        # equations and references of the textbook values (translated html, not the key)
        reference = dlg.text_info.toPlainText()
        assert 'Swamee' in reference and 'Idelchik' in reference and '2300' in reference, reference[:200]
        dlg.comboBox_colorRamp.setCurrentText('Spectral')
        runZetaVisualization(dlg)
        errors.check()
        layers = {l.name(): l for l in QgsProject.instance().mapLayers().values() if l.customProperty(ZETA_PROPERTY)}
        assert len(layers) == 2, list(layers)
        for layer in layers.values():
            assert isinstance(layer.renderer(), QgsRuleBasedRenderer), layer.name()
        lines_layer = layers['{} – {}'.format(tr('@default', 'lines'), tr('@default', 'zeta'))]
        conn_layer = layers['{} – {}'.format(tr('@default', 'junction_connections'), tr('@default', 'zeta'))]
        assert lines_layer.featureCount() == count(plugin, 'lines')
        assert conn_layer.featureCount() == count(plugin, 'junction_connections')
        assert conn_layer.labelsEnabled()
        plugin.cur.execute("""SELECT jc.lid, sum(coalesce(jc.zeta, 0) + coalesce(j.zeta, 0) / 2) AS z
FROM "{v}".junction_connections jc JOIN "{v}".junctions j ON j.id = jc.jid GROUP BY jc.lid;""".format(v=version))  # nosec B608
        zeta_j = {r['lid']: float(r['z']) for r in plugin.cur.fetchall()}
        plugin.cur.execute('SELECT id, coalesce(zeta, 0) AS zeta FROM "{}".lines;'.format(version))  # nosec B608
        expected = {r['id']: float(r['zeta']) + zeta_j.get(r['id'], 0.0) for r in plugin.cur.fetchall()}
        for f in lines_layer.getFeatures():
            assert abs(f['zeta_total'] - expected[f['id']]) < 1e-6, (f['id'], f['zeta_total'], expected[f['id']])
        assert lines_layer.getFeature(next(f.id() for f in lines_layer.getFeatures() if f['id'] == lid))['zeta_line'] == 2

        # compared with the pipe friction (lambda * L / d), lines colored by the share of the local losses
        dlg = ZetaDialog()
        dlg.checkBox_connections.setChecked(False)
        dlg.groupBox_friction.setChecked(True)
        dlg.checkBox_colorByShare.setChecked(True)
        runZetaVisualization(dlg)
        errors.check()
        layers = [l for l in QgsProject.instance().mapLayers().values() if l.customProperty(ZETA_PROPERTY)]
        assert len(layers) == 1, [l.name() for l in layers]
        lines_layer = layers[0]
        assert {'length_m', 'd_m', 'lambda', 'zeta_friction', 'local_share_pct'} <= set(lines_layer.fields().names())
        shares = []
        for f in lines_layer.getFeatures():
            assert 0.008 < f['lambda'] < 0.08, (f['id'], f['lambda'])
            assert f['zeta_friction'] == pytest.approx(f['lambda'] * f['length_m'] / f['d_m'])
            assert f['local_share_pct'] == pytest.approx(f['zeta_total'] / f['zeta_friction'] * 100)
            shares.append(f['local_share_pct'])
        assert any('local_share_pct' in r.filterExpression() for r in lines_layer.renderer().rootRule().children())
        shares.sort()
        print('zeta: share of the local losses in the pipe friction (%): median {:.1f}, max {:.1f}'.format(
            shares[len(shares) // 2], shares[-1]))

        plugin.cur.execute('UPDATE "{}".lines SET zeta=0 WHERE id={};'.format(version, lid))  # nosec B608
        if jid:
            plugin.cur.execute('UPDATE "{}".junctions SET zeta=0 WHERE id={};'.format(version, jid))  # nosec B608
        loadVersion(main=plugin)
        wait(3000)
        assert not [l for l in QgsProject.instance().mapLayers().values() if l.customProperty(ZETA_PROPERTY)]

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
        setFeatureParm(dlg, plugin.conn, plugin.config, plugin.plugin_dir)
        closeDialog(dlg)
        errors.check()

    def test_topology_check_before_build(self, wf, errors, monkeypatch):
        """The build checks the network topology first: an edited customer makes it invalid and the user is
        asked to update the topology (opens the topology dialog with the network selected) or to cancel."""
        only_for(wf, *NETWORK_TEMPLATES)
        plugin = wf.plugin
        version = plugin.config['versionName']
        assert checkNetworkTopology(plugin.cur, version, ['1']) == []

        def answer(button_text):
            def fake_exec(box, *args):
                questions.append(box.text())
                [b for b in box.buttons() if b.text().replace('&', '') == button_text][0].click()
                return 0
            monkeypatch.setattr(QMessageBox, "exec", fake_exec)

        plugin.cur.execute('SELECT min(id) AS id FROM "{}".customers;'.format(version))  # nosec B608
        cid = plugin.cur.fetchone()['id']
        move = 'UPDATE "{}".customers SET geom=ST_Translate(geom,{},0) WHERE id={};'  # nosec B608
        plugin.cur.execute(move.format(version, 5, cid))
        try:
            problems = checkNetworkTopology(plugin.cur, version, ['1'])
            assert problems and problems[0]['ids'], problems

            questions = []
            answer('Cancel')
            assert checkTopologyBeforeBuild(plugin, ['1']) is None
            assert len(questions) == 1 and 'not match' in questions[0]

            answer('Update topology')
            assert checkTopologyBeforeBuild(plugin, ['1']) is None
            dlg = plugin.window_topology
            combo = dlg.combo_network_models
            assert [combo.itemText(i) for i in range(combo.count()) if combo.itemChecked(i)] == ['1']
            closeDialog(dlg)
        finally:
            plugin.cur.execute(move.format(version, -5, cid))
        assert checkNetworkTopology(plugin.cur, version, ['1']) == []

        # valid topology with an unconnected customer (far away from the lines): warning, the customer can be
        # neglected in the model or the model can be built anyway
        assert getUnconnectedFeatures(plugin.cur, version, ['1']) == []
        plugin.cur.execute("""INSERT INTO "{0}".customers (geom,template,network,submodel)
            SELECT ST_Translate(geom,5000,5000),template,network,submodel FROM "{0}".customers WHERE id={1}
            RETURNING id;""".format(version, cid))  # nosec B608
        new_cid = plugin.cur.fetchone()['id']
        try:
            unconnected = getUnconnectedFeatures(plugin.cur, version, ['1'])
            assert unconnected == [{'text': unconnected[0]['text'], 'count': 1, 'ids': [new_cid], 'table': 'customers'}]
            assert checkNetworkTopology(plugin.cur, version, ['1']) == []
            questions = []
            answer('Neglect in model')
            exclude = checkTopologyBeforeBuild(plugin, ['1'])
            assert exclude == {'customers': [new_cid]}
            assert 'not connected' in questions[0] and str(new_cid) in questions[0]
            # neglected customers are removed from the sensor signals
            for sensor in getSensorData(plugin.cur, plugin.config, networks=['1'], exclude_features=exclude):
                for iref in list(sensor['irefs_source'] or []) + list(sensor['irefs_target'] or []):
                    parts = str(iref).split('_')
                    assert not (len(parts) > 1 and parts[1] == str(new_cid) and 1 in (sensor['source_type'], sensor['target_type'])), sensor
            answer('Build anyway')
            assert checkTopologyBeforeBuild(plugin, ['1']) == {}
            answer('Cancel')
            assert checkTopologyBeforeBuild(plugin, ['1']) is None
        finally:
            plugin.cur.execute('DELETE FROM "{}".customers WHERE id={};'.format(version, new_cid))  # nosec B608
        assert getUnconnectedFeatures(plugin.cur, version, ['1']) == []
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
        dlg.rbtn_lines.setChecked(True)
        dlg.checkbox_varColor.setChecked(True)
        dlg.featureGroupChanged(dlg.rbtn_lines)
        dlg.color_var.setCurrentText('temp$1')
        dlg.color_function.setCurrentText('Values')
        dlg.layer_name.setText('lines_results_supply_temperature_values')
        wait(1000)
        statuses = []
        update_status = dlg.update_status
        dlg.update_status = lambda text: (statuses.append(text), update_status(text))
        showOnMap(dlg, plugin)
        wait_for_process(dlg, timeout=30)
        wait(500)
        # progress: steps with status text (segments of the lines), 100% and 'done' after styling the layer
        assert dlg.progress.value() == 100
        assert dlg.progress.format().endswith('done'), dlg.progress.format()
        assert any('segments' in s for s in statuses), statuses
        closeDialog(dlg)
        errors.check()
        assert QgsProject.instance().mapLayersByName('lines_results_supply_temperature_values')

    @pytest.mark.ida
    def test_show_line_mdot_on_map(self, wf, errors):
        """mdot with flow arrows: indexed PostGIS result table in temp, dropped when the version is loaded again"""
        self._require_simulation(wf)
        plugin = wf.plugin
        plugin.showDataOnMap()
        dlg = plugin.dlg_showOnMap
        dlg.rbtn_lines.setChecked(True)
        dlg.checkbox_varColor.setChecked(True)
        dlg.featureGroupChanged(dlg.rbtn_lines)
        dlg.color_var.setCurrentText('mdot$1')
        dlg.color_function.setCurrentText('Values')
        dlg.layer_name.setText('lines_results_mdot_values')
        wait(1000)
        showOnMap(dlg, plugin)
        wait_for_process(dlg, timeout=30)
        closeDialog(dlg)
        errors.check()
        layers = QgsProject.instance().mapLayersByName('lines_results_mdot_values')
        assert len(layers) == 1, "the result layer was added {} times".format(len(layers))
        layer = layers[0]
        assert layer.providerType() == 'postgres'
        assert layer.temporalProperties().isActive()
        assert layer.featureCount() > 0
        assert isinstance(layer.renderer(), QgsGraduatedSymbolRenderer)
        table = layer.customProperty(RESULT_VIS_PROPERTY)
        plugin.cur.execute("SELECT indexdef FROM pg_indexes WHERE schemaname='temp' AND tablename=%s;", (table,))
        indexes = [row['indexdef'] for row in plugin.cur.fetchall()]
        assert any('(\"time\")' in i or '(time)' in i for i in indexes), indexes
        assert any('gist' in i for i in indexes), indexes

        loadVersion(main=plugin)
        wait(3000)
        assert not QgsProject.instance().mapLayersByName('lines_results_mdot_values')
        plugin.cur.execute("SELECT count(*) AS n FROM information_schema.tables WHERE table_schema='temp' AND table_name LIKE 'result\\_vis\\_%';")
        assert plugin.cur.fetchone()['n'] == 0

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

    def _add_report_plot(self, plugin, report, rbtn, variable, function, name):
        """'+' in the network report dialog: the show-on-map dialog stores the plot data in the report"""
        report.btn_addPlot.click()
        dlg = plugin.dlg_showOnMap
        assert dlg.networkReportDlg is report
        getattr(dlg, rbtn).setChecked(True)
        dlg.featureGroupChanged(getattr(dlg, rbtn))
        dlg.checkbox_varColor.setChecked(True)
        if variable.endswith('$'):
            # e.g. 'power$': the connection index depends on the templates (power$1_1, power$2_1, ...)
            available = [dlg.color_var.itemText(i) for i in range(dlg.color_var.count())]
            matches = sorted(v for v in available if v.startswith(variable))
            assert matches, "no variable '{}*' available: {}".format(variable, available)
            variable = matches[0]
        dlg.color_var.setCurrentText(variable)
        assert dlg.color_var.currentText() == variable, "variable '{}' not available".format(variable)
        dlg.color_function.setCurrentText(function)
        assert dlg.color_function.currentText() == function
        dlg.layer_name.setText(name)
        wait(1000)
        showOnMap(dlg, plugin, report)
        wait_for_process(dlg, timeout=60)
        closeDialog(dlg)

    @pytest.mark.ida
    def test_network_report(self, wf, errors, monkeypatch):
        self._require_simulation(wf)
        plugin = wf.plugin
        # the report is opened in the PDF viewer
        opened = []
        monkeypatch.setattr(reports.os, 'startfile', opened.append, raising=False)

        plugin.showNetworkReport()
        report = plugin.dlg_networkReport
        report.checkBox_kpi.setChecked(True)
        report.checkBox_pipeTable.setChecked(True)
        self._add_report_plot(plugin, report, 'rbtn_customers', 'power$', 'Max', 'report_customer_power_max')
        self._add_report_plot(plugin, report, 'rbtn_lines', 'temp$1', 'Min', 'report_line_temperature_min')
        errors.check()
        assert [report.tableWidget_diagrams.item(r, 0).text() for r in range(report.tableWidget_diagrams.rowCount())] == \
            ['report_line_temperature_min', 'report_customer_power_max']
        assert [plot['name'] for plot in report.data] == ['report_customer_power_max', 'report_line_temperature_min']

        pdf = os.path.join(districtsModelerTempDir(), 'network_report.pdf')
        if os.path.exists(pdf):
            os.remove(pdf)
        report.btn_ok.click()
        wait(500)
        errors.check()
        assert os.path.exists(pdf) and os.path.getsize(pdf) > 0, "no report PDF: " + pdf
        assert opened == [pdf]
        layouts = [layout.name() for layout in QgsProject.instance().layoutManager().printLayouts()]
        assert 'Network Report' in layouts
        # the plot layers stay in the project: the layout 'Network Report' shows them
        for name in ['report_customer_power_max', 'report_line_temperature_min']:
            assert QgsProject.instance().mapLayersByName(name), name
        closeDialog(report)
