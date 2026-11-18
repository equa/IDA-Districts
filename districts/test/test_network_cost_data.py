# coding=utf-8
"""Cost data and economic evaluation (OpenSpec change network-cost-data) on a project from the template db_default_values with the default
resources: example values of the pipes, the scenario 'base', street surfaces, trench lengths per surface, copying a
scenario, the electricity profile, the evaluation of synthetic full-year results, the upgrade of an old project.

    python -m pytest test/test_network_cost_data.py -v -s   (--keep-projects)
"""
from types import SimpleNamespace

import pytest

from districts.economic_scenarios_dialog import copyScenario, setProfile
from districts.ida_ph import addBaseVersion
from districts.ida_ph_dialog import IDA_Districts_NameDialog
from districts.upgrade import upgradeVersionDB
from districts.utility_functions.economic_data import loadScenario
from districts.utility_functions.files import loadProjectConfig
from districts.utility_functions.network_economics import evaluateVersion, trenchLengths
from districts.utility_functions.reports import economicsRows
from districts.utility_functions.translations import tr, tr_msg

from .conftest import wait
from .test_workflow import DB_DEFAULTS, create_project, delete_project, project_name_for

pytestmark = [pytest.mark.e2e]

SETTINGS = {'ground_lambda': '1.2', 'ground_model': 'Constant', 'ground_temp': '10', 'duct_temp': '20'}


@pytest.fixture(scope='class')
def cost(request, districts_plugin, errors):
    state = SimpleNamespace(plugin=districts_plugin, project_name=project_name_for('costs'))
    yield state
    if not request.config.getoption('--keep-projects'):
        delete_project(districts_plugin, errors, state.project_name)


def base_id(plugin):
    plugin.cur.execute("SELECT id FROM public.economic_scenarios WHERE name = 'base';")
    return plugin.cur.fetchone()['id']


def synthetic_results(plugin, hours, t_pipe=70.0, p_pump=500.0):
    """result tables of one line (id 1, sequences 1/2) and one pump, hourly from 1 January"""
    v = plugin.config['versionName']
    srid = loadProjectConfig(plugin.config)['srid']
    sql = """
DROP TABLE IF EXISTS "{v}".energy_plant_s_ppump, "{v}"."line_s_temp$1", "{v}"."line_s_temp$2", "{v}".line_s_qamb, "{v}"."energy_plant_s_temp$1_1_1_1";
CREATE TABLE "{v}".energy_plant_s_ppump (id serial, fid integer, pump text, kind text, time timestamp, geom geometry(PointZ,{srid}), "$ppump" numeric);
INSERT INTO "{v}".energy_plant_s_ppump (fid, pump, kind, time, "$ppump")
    SELECT 1, 'PUMP2', 'variable', timestamp '2026-01-01' + h * interval '1 hour', {p} FROM generate_series(0, {n}) h;
CREATE TABLE "{v}"."line_s_temp$1" (id serial, fid integer, time timestamp, geom geometry(LineStringZ,{srid}), segment integer, "$temp" numeric);
INSERT INTO "{v}"."line_s_temp$1" (fid, time, segment, "$temp") SELECT 1, timestamp '2026-01-01' + h * interval '1 hour', 1, {t} FROM generate_series(0, {n}) h;
CREATE TABLE "{v}"."line_s_temp$2" (LIKE "{v}"."line_s_temp$1" INCLUDING ALL);
INSERT INTO "{v}"."line_s_temp$2" (fid, time, segment, "$temp") SELECT 1, timestamp '2026-01-01' + h * interval '1 hour', 1, 40 FROM generate_series(0, {n}) h;
CREATE TABLE "{v}".line_s_qamb (id serial, fid integer, time timestamp, geom geometry(LineStringZ,{srid}), "$qamb" numeric);
INSERT INTO "{v}".line_s_qamb (fid, time, "$qamb") SELECT 1, timestamp '2026-01-01' + h * interval '1 hour', 1000 FROM generate_series(0, {n}) h;
CREATE TABLE "{v}"."energy_plant_s_temp$1_1_1_1" (id serial, fid integer, time timestamp, geom geometry(PointZ,{srid}), "$temp" numeric);
INSERT INTO "{v}"."energy_plant_s_temp$1_1_1_1" (fid, time, "$temp") SELECT 1, timestamp '2026-01-01' + h * interval '1 hour', 70 FROM generate_series(0, {n}) h;
""".format(v=v, srid=srid, n=hours - 1, t=t_pipe, p=p_pump)  # nosec B608
    plugin.cur.execute(sql)


@pytest.mark.incremental
class TestNetworkCostData:
    def test_create_project(self, cost, errors):
        plugin = cost.plugin
        create_project(plugin, errors, cost.project_name, DB_DEFAULTS)
        plugin.dlg_addBase = IDA_Districts_NameDialog(tr('@default', 'add_base_version'), tr('@default', 'add_base_version'), '', '')
        plugin.dlg_addBase.input.setText('base1')
        addBaseVersion(plugin.dlg_addBase, plugin)
        wait(500)
        errors.check()
        assert plugin.config['versionName'] == 'base1'

    def test_example_values(self, cost):
        plugin = cost.plugin
        plugin.cur.execute("SELECT count(*) AS n, count(*) FILTER (WHERE costs > 0 AND maintenance_pct = 1 AND lifetime_a = 40 AND p_max_bar = 16 AND example) AS ok "
                           "FROM public.pipes WHERE series IN ('Isoplus DRE Standard', 'Isoplus DRD Standard');")
        row = plugin.cur.fetchone()
        assert row['n'] > 0 and row['ok'] == row['n']
        # the flexible pipes of change pipe-series-catalog have no costs
        plugin.cur.execute("SELECT count(*) AS n FROM public.pipes WHERE name LIKE 'isoplus %' AND (costs IS NOT NULL OR example);")
        assert plugin.cur.fetchone()['n'] == 0
        scenario = loadScenario(plugin.cur, base_id(plugin))
        assert scenario['scenario']['example'] and set(scenario['trench']) == {'paved', 'unpaved'}
        assert set(scenario['groups']) == {'electricity', 'heat', 'cold', 'maintenance', 'investment', 'fuel', 'purchased_heat'}

    def test_trench_lengths_per_surface(self, cost):
        plugin = cost.plugin
        v = plugin.config['versionName']
        srid = loadProjectConfig(plugin.config)['srid']
        plugin.cur.execute("""DELETE FROM "{v}".lines; DELETE FROM "{v}".streets;
            INSERT INTO "{v}".lines (id, geom, pipe_bundle_type_id) VALUES (1, ST_SetSRID(ST_MakeLine(ST_MakePoint(0, 0, 0), ST_MakePoint(100, 0, 0)), {s}), 1);
            INSERT INTO "{v}".streets (geom, surface) VALUES (ST_SetSRID(ST_MakeLine(ST_MakePoint(0, 0), ST_MakePoint(60, 0)), {s}), 'unpaved');""".format(v=v, s=srid))  # nosec B608
        lengths = trenchLengths(plugin.cur, v, 'paved')
        assert lengths[1] == pytest.approx({'unpaved': 60.0, 'paved': 40.0})

    def test_copy_scenario_and_profile(self, cost, tmp_path):
        plugin = cost.plugin
        new_id = copyScenario(plugin.cur, base_id(plugin), 'high electricity')
        plugin.cur.execute("UPDATE public.price_groups SET start_price = start_price * 2 WHERE scenario_id = %s AND cost_group = 'electricity';", (new_id,))
        assert loadScenario(plugin.cur, base_id(plugin))['groups']['electricity']['start_price'] == pytest.approx(0.25)
        assert loadScenario(plugin.cur, new_id)['groups']['electricity']['start_price'] == pytest.approx(0.5)
        profile = tmp_path / 'tariff.csv'
        profile.write_text('\n'.join(str(1.0 + (h % 24 > 16)) for h in range(8760)), encoding='utf-8')
        assert setProfile(plugin.cur, plugin.config, new_id, str(profile)) == 'tariff.csv'
        short = tmp_path / 'short.csv'
        short.write_text('\n'.join('1' for _ in range(8000)), encoding='utf-8')
        with pytest.raises(ValueError):
            setProfile(plugin.cur, plugin.config, new_id, str(short))

    def test_missing_and_short_results(self, cost):
        plugin = cost.plugin
        evaluation = evaluateVersion(plugin.cur, plugin.config, base_id(plugin), SETTINGS)
        assert evaluation['missing']
        synthetic_results(plugin, 24)
        evaluation = evaluateVersion(plugin.cur, plugin.config, base_id(plugin), SETTINGS)
        assert 'short' in evaluation
        rows = economicsRows(evaluation)
        assert rows[-1][0] == tr_msg('Results needed')

    def test_full_year(self, cost):
        plugin = cost.plugin
        synthetic_results(plugin, 8760, t_pipe=70.0, p_pump=500.0)
        evaluation = evaluateVersion(plugin.cur, plugin.config, base_id(plugin), SETTINGS)
        assert 'missing' not in evaluation and 'short' not in evaluation
        # 500 W all year
        assert evaluation['energy']['pump_kwh'] == pytest.approx(4380, rel=1e-3)
        assert evaluation['costs']['pump_energy'] == pytest.approx(4380 * 0.25, rel=1e-3)
        # the supply pipe at 70 °C and the return at 40 °C lose heat into the ground at 10 °C
        assert evaluation['energy']['heat_kwh'] > 0 and evaluation['costs']['heat_losses'] > 0
        assert evaluation['example'] and evaluation['npv']['npv'] > 0
        labels = [row[0] for row in economicsRows(evaluation)]
        assert tr_msg('Net present value') in labels and tr_msg('Annuity') in labels
        # the simulated 1 kW per line does not match the calculated loss
        assert 1 in evaluation['loss_check']

    def test_heating_and_cooling_from_the_plants(self, cost, monkeypatch):
        """a low-temperature year: the plant puts heat into the network in the first half, takes it out in the second;
        the same pipe losses are a heat cost in the heating hours and a cold credit in the cooling hours (D23)"""
        plugin = cost.plugin
        # the template has no energy plant: one with the supply 1 and the return 2
        monkeypatch.setattr('districts.utility_functions.network_economics.plantConnections',
                            lambda cur, schema: [{'conn_seq': 1, 'type': 1, 'temp': 70}, {'conn_seq': 2, 'type': 2, 'temp': 40}])
        v = plugin.config['versionName']
        synthetic_results(plugin, 8760)
        heating_only = evaluateVersion(plugin.cur, plugin.config, base_id(plugin), SETTINGS)
        assert heating_only['modes']['1/2']['source'] == 'template' and heating_only['costs']['cold_losses'] == 0
        srid = loadProjectConfig(plugin.config)['srid']
        plugin.cur.execute("""
CREATE TABLE "{v}"."energy_plant_s_temp$1_1_1_2" (LIKE "{v}"."energy_plant_s_temp$1_1_1_1" INCLUDING ALL);
INSERT INTO "{v}"."energy_plant_s_temp$1_1_1_2" (fid, time, "$temp")
    SELECT 1, timestamp '2026-01-01' + h * interval '1 hour', CASE WHEN h < 4380 THEN 40 ELSE 90 END FROM generate_series(0, 8759) h;
CREATE TABLE "{v}"."energy_plant_s_mdot$1_1_1_1" (id serial, fid integer, time timestamp, geom geometry(PointZ,{srid}), "$mdot" numeric);
INSERT INTO "{v}"."energy_plant_s_mdot$1_1_1_1" (fid, time, "$mdot") SELECT 1, timestamp '2026-01-01' + h * interval '1 hour', 1 FROM generate_series(0, 8759) h;
CREATE TABLE "{v}"."energy_plant_s_mdot$1_1_1_2" (LIKE "{v}"."energy_plant_s_mdot$1_1_1_1" INCLUDING ALL);
INSERT INTO "{v}"."energy_plant_s_mdot$1_1_1_2" (fid, time, "$mdot") SELECT 1, timestamp '2026-01-01' + h * interval '1 hour', -1 FROM generate_series(0, 8759) h;
""".format(v=v, srid=srid))  # nosec B608
        try:
            both = evaluateVersion(plugin.cur, plugin.config, base_id(plugin), SETTINGS)
            modes = both['modes']['1/2']
            assert modes['source'] == 'plants'
            assert modes['heat_h'] == pytest.approx(4380, abs=2) and modes['cold_h'] == pytest.approx(4380, abs=2)
            assert both['energy']['heat_kwh'] == pytest.approx(heating_only['energy']['heat_kwh'] / 2, rel=0.2)
            assert both['costs']['heat_losses'] < heating_only['costs']['heat_losses']
            # losses of a cooling network are a gain for it: a credit at the cold price
            assert both['costs']['cold_losses'] < 0
            # both pipes (70 / 40 °C) are warmer than the ground: everything is given off, nothing taken up
            e = both['energy']
            assert e['heat_out_kwh'] == pytest.approx(e['heat_kwh']) and e['heat_in_kwh'] == pytest.approx(0, abs=1e-6)
            assert e['cold_out_kwh'] == pytest.approx(e['cold_kwh']) and e['cold_out_eur'] == pytest.approx(both['costs']['cold_losses'])
        finally:
            plugin.cur.execute('DROP TABLE IF EXISTS "{v}"."energy_plant_s_temp$1_1_1_2", "{v}"."energy_plant_s_mdot$1_1_1_1", '
                               '"{v}"."energy_plant_s_mdot$1_1_1_2";'.format(v=v))  # nosec B608

    def test_upgrade_of_an_old_project(self, cost):
        plugin = cost.plugin
        plugin.cur.execute("""UPDATE public.pipes SET costs = 77 WHERE id = 1;
            ALTER TABLE public.pipes DROP COLUMN maintenance_pct, DROP COLUMN lifetime_a, DROP COLUMN p_max_bar, DROP COLUMN example;
            DROP TABLE public.economic_scenarios, public.price_groups, public.price_levels, public.price_curves, public.trench_costs;
            ALTER TABLE "{}".streets DROP COLUMN surface;
            ALTER TABLE public.pipe_bundle_types ADD COLUMN invest_costs numeric, ADD COLUMN operation_costs numeric;""".format(plugin.config['versionName']))  # nosec B608
        upgradeVersionDB(plugin.cur, plugin.config)
        upgradeVersionDB(plugin.cur, plugin.config)  # a second load changes nothing
        plugin.cur.execute('SELECT costs, example, maintenance_pct FROM public.pipes WHERE id = 1;')
        row = plugin.cur.fetchone()
        assert (float(row['costs']), row['example'], row['maintenance_pct']) == (77.0, False, None)
        plugin.cur.execute("SELECT count(*) AS n FROM public.economic_scenarios WHERE name = 'base';")
        assert plugin.cur.fetchone()['n'] == 1
        plugin.cur.execute("SELECT count(*) AS n FROM information_schema.columns WHERE table_schema = %s AND table_name = 'streets' AND column_name = 'surface';",
                           (plugin.config['versionName'],))
        assert plugin.cur.fetchone()['n'] == 1
        # the unused costs of the pipe bundles are removed
        plugin.cur.execute("SELECT count(*) AS n FROM information_schema.columns WHERE table_schema = 'public' AND table_name = 'pipe_bundle_types' "
                           "AND column_name IN ('invest_costs', 'operation_costs');")
        assert plugin.cur.fetchone()['n'] == 0

    def test_npv_from_the_plant_energy(self, cost, monkeypatch):
        """with energy results the NPV contains the plant energy per carrier instead of the priced pipe losses; without
        them the price curves apply (plant-energy-costs D5)"""
        plugin = cost.plugin
        v = plugin.config['versionName']
        monkeypatch.setattr('districts.utility_functions.network_economics.plantConnections',
                            lambda cur, schema: [{'conn_seq': 1, 'type': 1, 'temp': 70}, {'conn_seq': 2, 'type': 2, 'temp': 40}])
        synthetic_results(plugin, 8760)
        plugin.cur.execute("UPDATE public.price_groups SET start_price = 0.08 WHERE cost_group = 'fuel';")
        srid = loadProjectConfig(plugin.config)['srid']
        plugin.cur.execute("""
DROP TABLE IF EXISTS "{v}".energy_plant_s_energy;
CREATE TABLE "{v}".energy_plant_s_energy (id serial, fid integer, component text, carrier text, time timestamp, geom geometry(PointZ,{srid}), "$energy" numeric);
INSERT INTO "{v}".energy_plant_s_energy (fid, component, carrier, time, "$energy")
    SELECT 1, 'BOIL1CIRC', 'fuel', timestamp '2026-01-01' + h * interval '1 hour', 100000 FROM generate_series(0, 8759) h;
""".format(v=v, srid=srid))  # nosec B608
        try:
            evaluation = evaluateVersion(plugin.cur, plugin.config, base_id(plugin), SETTINGS)
            basis = evaluation['energy_basis']
            assert basis and basis['costs']['kwh']['plant_energy']['fuel'] == pytest.approx(876000, rel=1e-3)
            assert evaluation['by_carrier']['plant_energy']['fuel'] == pytest.approx(876000 * 0.08, rel=1e-3)
            split = evaluation['npv']['split']
            assert split['plant_energy'] > 0 and split['heat_losses'] == 0 and split['cold_losses'] == 0
            # the losses are still priced for information (curves: no plant heat flows in these results)
            assert basis['losses']['heat'] > 0 and basis['curve_hours'] > 0
            # the network report names the basis and the plant's energy
            labels = [row[0] for row in economicsRows(evaluation)]
            assert tr_msg('Basis of the net present value') in labels and any(label.startswith(tr_msg('Plant') + ' 1') for label in labels)
        finally:
            plugin.cur.execute('DROP TABLE IF EXISTS "{}".energy_plant_s_energy;'.format(v))  # nosec B608
        fallback = evaluateVersion(plugin.cur, plugin.config, base_id(plugin), SETTINGS)
        assert fallback['energy_basis'] is None and fallback['npv']['split']['heat_losses'] > 0

    def test_upgrade_adds_carrier_groups_and_boundary(self, cost):
        """a scenario from before change plant-energy-costs gets fuel and purchased heat without a price, the columns
        system_boundary and marginal_threshold_pct (default 5)"""
        plugin = cost.plugin
        plugin.cur.execute("""DELETE FROM public.price_groups WHERE cost_group IN ('fuel', 'purchased_heat');
            ALTER TABLE public.economic_scenarios DROP COLUMN system_boundary, DROP COLUMN marginal_threshold_pct;""")
        upgradeVersionDB(plugin.cur, plugin.config)
        upgradeVersionDB(plugin.cur, plugin.config)
        plugin.cur.execute("""SELECT s.id, s.system_boundary, s.marginal_threshold_pct, g.cost_group, g.start_price FROM public.economic_scenarios s
            JOIN public.price_groups g ON g.scenario_id = s.id AND g.cost_group IN ('fuel', 'purchased_heat') ORDER BY s.id, g.cost_group;""")
        rows = plugin.cur.fetchall()
        scenarios = {row['id'] for row in rows}
        assert scenarios and len(rows) == 2 * len(scenarios)
        assert all(row['start_price'] is None and row['system_boundary'] is None and float(row['marginal_threshold_pct']) == 5 for row in rows)

    def test_report_page_and_dialog(self, cost):
        """the Economics page of the network report and the scenario selection in its dialog"""
        from qgis.core import QgsPrintLayout, QgsProject
        from qgis.PyQt.QtGui import QFont
        from districts.ida_rv_dialog import NetworkReportDialog
        from districts.utility_functions.reports import addTablePage, fillScenarioCombo
        plugin = cost.plugin
        layout = QgsPrintLayout(QgsProject.instance())
        layout.initializeDefaults()
        pages = layout.pageCollection().pageCount()
        rows = [[tr_msg('Scenario'), 'base'], [tr_msg('Net present value'), "1'000 €"]]
        assert addTablePage(layout, tr_msg('Economics'), rows, QFont('Arial', 18), QFont('Arial', 10), QFont('Arial', 10)) == pages + 1
        dlg = NetworkReportDialog(plugin.plugin_dir)
        assert not dlg.checkBox_economics.isChecked()
        fillScenarioCombo(plugin.cur, dlg.combo_scenario)
        assert dlg.combo_scenario.findText('base') >= 0
