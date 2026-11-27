# coding=utf-8
"""Pipe series and the isoplus flexible catalogue (OpenSpec change pipe-series-catalog) on a project from the template
heating_network: catalogue in the template, upgrade of an old project, series dialog with its pressure ratings, resource
export/import, a line with an unequal twin pipe in the network model.

    python -m pytest test/test_pipe_series.py -v -s   (--keep-projects)
"""
from types import SimpleNamespace

import pytest
from qgis.PyQt.QtWidgets import QComboBox

from districts.ida_mosim import buildModel
from districts.ida_resources import exportPipeSeries, pipeSeriesImportSql
from districts.upgrade import upgradeVersionDB
from districts.utility_functions.db import pipeSeriesNames
from districts.utility_functions.dialog import closeDialog

from .conftest import wait_for_process
from .test_workflow import HEATING, create_project, delete_project, new_dialog, project_name_for, save_dialog, select_row_by_id

pytestmark = [pytest.mark.e2e]


@pytest.fixture(scope='class')
def series(request, districts_plugin, errors):
    state = SimpleNamespace(plugin=districts_plugin, project_name=project_name_for('pipe_series'))
    yield state
    if not request.config.getoption('--keep-projects'):
        delete_project(districts_plugin, errors, state.project_name)


def one(plugin, sql, args=None):
    plugin.cur.execute(sql, args)
    return plugin.cur.fetchone()


def series_id(plugin, name):
    return one(plugin, 'SELECT id FROM public.pipe_series WHERE name = %s;', (name,))['id']


def rating(plugin, name, years, temperature):
    row = one(plugin, 'SELECT pressure_bar FROM public.pipe_series_pressure_ratings WHERE series_id = %s AND years = %s AND temperature_c = %s;',
              (series_id(plugin, name), years, temperature))
    return None if row is None else float(row['pressure_bar'])


def row_of(dlg, column, text):
    for row in range(dlg.tableWidget.rowCount()):
        item = dlg.tableWidget.item(row, column)
        if item is not None and item.text() == text:
            return row
    raise AssertionError('no row with {!r} in column {}'.format(text, column))


@pytest.mark.incremental
class TestPipeSeries:
    def test_create_project(self, series, errors):
        create_project(series.plugin, errors, series.project_name, HEATING)

    def test_catalogue_in_the_template(self, series):
        plugin = series.plugin
        h50 = one(plugin, "SELECT * FROM public.pipes WHERE name = 'isoplus isopex H-50';")
        assert float(h50['innerpipediameter']) == pytest.approx(0.0408) and float(h50['min_bend_radius_m']) == 0.9
        assert float(h50['p_max_bar']) == 6 and h50['series'] == 'isoplus isopex H' and h50['costs'] is None and not h50['example']
        assert float(one(plugin, 'SELECT 2 * sum(thickness) AS t FROM public.pipe_layers WHERE pipe_construction_id = %s;',
                         (h50['pipe_construction_id'],))['t']) == pytest.approx(0.110 - 0.050 + 2 * 0.0046)
        assert float(one(plugin, "SELECT p_max_bar FROM public.pipes WHERE name = 'isoplus isopex S-40';")['p_max_bar']) == 10
        assert one(plugin, "SELECT count(*) AS n FROM public.pipes WHERE name LIKE '%isowell%';")['n'] == 0
        dre = one(plugin, "SELECT * FROM public.pipe_series WHERE name = 'Isoplus DRE Standard';")
        assert (dre['system_type'], float(dre['t_max_continuous_c']), float(dre['t_max_peak_c']), float(dre['sigma_ax_max_n7mm2'])) == ('rigid_single', 120, 140, 190)
        assert rating(plugin, 'isoplus isopex H', 50, 70) == 8.5
        pexa = one(plugin, "SELECT * FROM public.materials WHERE name = 'PE-Xa';")
        assert (float(pexa['youngs_modulus_n7mm2']), float(pexa['yield_strength_n7mm2']), float(pexa['thermal_expansion_17kelvin'])) == (600, 17, 0.00015)
        # the carriers of an unequal twin are not resized: no series text
        assert one(plugin, "SELECT count(*) AS n FROM public.pipes WHERE name LIKE 'isoplus isopex S-%+%' AND series IS NULL;")['n'] == 10

    def test_invalid_system_type(self, series):
        plugin = series.plugin
        import psycopg2
        with pytest.raises(psycopg2.errors.CheckViolation):  # autocommit: the failed statement leaves nothing behind
            plugin.cur.execute("UPDATE public.pipe_series SET system_type = 'rigid' WHERE name = 'isoplus isocu';")

    def test_series_dialog(self, series, errors):
        """a rating of one series changed in the sub table, a series renamed (ratings and pipes follow), a series deleted"""
        plugin = series.plugin
        h_before = rating(plugin, 'isoplus isopex H', 50, 40)
        dlg = new_dialog(plugin.managePipeSeries)
        assert isinstance(dlg.tableWidget.cellWidget(0, 2), QComboBox)
        select_row_by_id(dlg, series_id(plugin, 'isoplus isoclima'))
        child = new_dialog(dlg.btn_open.click)
        row = next(r for r in range(child.tableWidget.rowCount())
                   if float(child.tableWidget.item(r, 0).text()) == 50 and float(child.tableWidget.item(r, 1).text()) == 40)
        child.tableWidget.item(row, 2).setText('11.0')
        save_dialog(child, errors)
        dlg.close()
        assert rating(plugin, 'isoplus isoclima', 50, 40) == 11.0 and rating(plugin, 'isoplus isopex H', 50, 40) == h_before

        cu = series_id(plugin, 'isoplus isocu')
        ratings = one(plugin, 'SELECT count(*) AS n FROM public.pipe_series_pressure_ratings;')['n']
        dlg = new_dialog(plugin.managePipeSeries)
        dlg.tableWidget.item(row_of(dlg, 1, 'isoplus isocu'), 1).setText('isoplus isocu 2016')
        dlg.tableWidget.removeRow(row_of(dlg, 1, 'isoplus isoclima u'))
        save_dialog(dlg, errors)
        assert pipeSeriesNames(plugin.cur)[cu] == 'isoplus isocu 2016'
        assert one(plugin, "SELECT count(*) AS n FROM public.pipes WHERE series = 'isoplus isocu 2016';")['n'] == 2
        # the ratings of the deleted series are gone, the others kept; the pipe of the deleted series is unchanged
        assert one(plugin, 'SELECT count(*) AS n FROM public.pipe_series_pressure_ratings;')['n'] == ratings - 20
        assert one(plugin, "SELECT series FROM public.pipes WHERE name = 'isoplus isoclima 110 u';")['series'] == 'isoplus isoclima u'
        upgradeVersionDB(plugin.cur, plugin.config)
        assert 'isoplus isocu' not in pipeSeriesNames(plugin.cur).values()

    def test_resource_export_and_import(self, series):
        """the series of exported pipes travel with their ratings; an existing series of the same name is kept"""
        plugin = series.plugin
        pid = one(plugin, "SELECT id FROM public.pipes WHERE name = 'isoplus isopex S-40';")['id']
        export: dict = {'pipes': {str(pid): {}}}
        exportPipeSeries(plugin.cur, export)
        assert list(export['pipe_series']) == ['isoplus isopex S'] and len(export['pipe_series_pressure_ratings']['isoplus isopex S']) == 43
        assert pipeSeriesImportSql(plugin.cur, export) == ''  # the project has the series: kept
        renamed = {'pipe_series': {'imported S': export['pipe_series']['isoplus isopex S'].replace("'isoplus isopex S'", "'imported S'")},
                   'pipe_series_pressure_ratings': {'imported S': export['pipe_series_pressure_ratings']['isoplus isopex S']}}
        plugin.cur.execute(pipeSeriesImportSql(plugin.cur, renamed))
        assert one(plugin, "SELECT system_type FROM public.pipe_series WHERE name = 'imported S';")['system_type'] == 'flexible_plastic'
        assert rating(plugin, 'imported S', 50, 70) == 13.4
        assert pipeSeriesImportSql(plugin.cur, {}) == ''  # an export of an older version has no series

    def test_twins_in_the_network_model(self, series, errors, monkeypatch):
        """a line with the unequal twin S-50+32 and one with H-50+50 are converted for FDpipebundle without error"""
        import districts.invoke_network as invoke_network
        plugin = series.plugin
        v = plugin.config['versionName']
        bundles = [one(plugin, "SELECT id FROM public.pipe_bundle_types WHERE description LIKE %s;", ('twin pipe isoplus isopex {}:%'.format(name),))['id']
                   for name in ('S-50+32', 'H-50+50')]
        plugin.cur.execute('SELECT id FROM "{}".lines WHERE pipe_bundle_type_id IS NOT NULL ORDER BY id LIMIT 2;'.format(v))  # nosec B608
        for row, bundle in zip(plugin.cur.fetchall(), bundles):
            plugin.cur.execute('UPDATE "{}".lines SET pipe_bundle_type_id = %s WHERE id = %s;'.format(v), (bundle, row['id']))  # nosec B608
        calls = []
        convert = invoke_network.twinPipeEquivalent

        def convert_and_record(pipes, *args, **kwargs):
            calls.append((pipes, convert(pipes, *args, **kwargs)))
            return calls[-1][1]

        monkeypatch.setattr(invoke_network, 'twinPipeEquivalent', convert_and_record)
        plugin.showBuildModel()
        dlg = plugin.dlg_buildModel
        dlg.combo_network_models.setItemChecked(1, True)
        dlg.combo_submodels.setItemChecked(1, True)
        buildModel(dlg, plugin)
        wait_for_process(dlg, timeout=60)
        closeDialog(dlg)
        errors.check()
        radii = sorted({tuple(sorted(round(r * 2000) for _, _, r in pipes)) for pipes, _ in calls})
        assert radii == [(32, 50), (50, 50)]
        assert all(min(thicknesses) > 0 and dx > 0 for _, (thicknesses, dx) in calls)

    def test_upgrade_of_an_old_project(self, series):
        plugin = series.plugin
        plugin.cur.execute("""DROP TABLE public.pipe_series, public.pipe_series_pressure_ratings;
            ALTER TABLE public.pipes DROP COLUMN min_bend_radius_m;
            UPDATE public.pipes SET series = 'old series A' WHERE name = 'Isoplus DRE-20';""")
        before = one(plugin, 'SELECT count(*) AS n, count(DISTINCT series) AS s FROM public.pipes;')
        upgradeVersionDB(plugin.cur, plugin.config)
        upgradeVersionDB(plugin.cur, plugin.config)  # a second load changes nothing
        rows = one(plugin, 'SELECT count(*) AS n, count(*) FILTER (WHERE system_type IS NULL) AS empty FROM public.pipe_series;')
        assert rows['n'] == before['s'] and rows['empty'] == rows['n']
        assert one(plugin, 'SELECT count(*) AS n, count(DISTINCT series) AS s FROM public.pipes;') == before
        assert one(plugin, "SELECT count(*) AS n FROM information_schema.columns WHERE table_schema = 'public' AND table_name = 'pipes' "
                           "AND column_name = 'min_bend_radius_m';")['n'] == 1
