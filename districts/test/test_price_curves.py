# coding=utf-8
"""Dialog of the price curves (graph and table) and the fixed-value dropdowns of the table dialog, without a DB."""
import pytest

from districts.utility_functions.db import getDropDownItems


class FakeCursor:
    """the queries of the price curves dialog on rows in memory"""

    def __init__(self, curves):
        self.curves = curves  # [(scenario_id, mode, t, price)]
        self.result = []

    def execute(self, sql, args=()):
        if sql.startswith('SELECT id, name FROM public.economic_scenarios'):
            self.result = [{'id': 1, 'name': 'base'}, {'id': 2, 'name': 'high'}]
        elif sql.startswith('SELECT mode, t_supply, price_eur7kwh'):
            self.result = [{'mode': m, 't_supply': t, 'price_eur7kwh': p} for s, m, t, p in sorted(self.curves, key=lambda r: r[2]) if s == args[0]]
        elif sql.startswith('DELETE FROM public.price_curves'):
            self.curves = [row for row in self.curves if row[0] != args[0]]
        elif sql.startswith('INSERT INTO public.price_curves'):
            self.curves.append(tuple(args))

    def fetchall(self):
        return self.result


class Main:
    def __init__(self, cur):
        self.cur = cur


@pytest.fixture
def curves_dialog(qgis_app):
    from districts.price_curves_dialog import PriceCurvesDialog
    cur = FakeCursor([(1, 'heat', 95.0, 0.139), (1, 'heat', 70.0, 0.10), (1, 'cold', 6.0, 0.0625)])
    dlg = PriceCurvesDialog(Main(cur), scenario_id=1)
    yield dlg, cur
    dlg.dirty = False
    dlg.close()


def test_curves_of_the_scenario_in_table_and_graph(curves_dialog):
    dlg, cur = curves_dialog
    assert dlg.points() == [[70.0, 0.10], [95.0, 0.139]]
    assert dlg.table.rowCount() == 2 and dlg.table.item(1, 0).text() == '95'
    dlg.rbtn_cold.setChecked(True)
    assert dlg.points() == [[6.0, 0.0625]] and dlg.table.rowCount() == 1


def test_table_edits_are_saved(curves_dialog):
    dlg, cur = curves_dialog
    dlg.table.item(0, 1).setText('0,12')  # decimal comma
    assert dlg.points()[0] == [70.0, 0.12] and dlg.dirty
    dlg.addPoint()
    assert dlg.points()[-1] == [105.0, 0.139]
    dlg.table.selectRow(2)
    dlg.removePoints()
    dlg.save()
    assert sorted((m, t, p) for s, m, t, p in cur.curves if s == 1) == [('cold', 6.0, 0.0625), ('heat', 70.0, 0.12), ('heat', 95.0, 0.139)]
    assert not dlg.dirty


def test_graph_drag_and_points(curves_dialog):
    dlg, cur = curves_dialog

    class Event:
        def __init__(self, t, price, button=1, dblclick=False):
            self.inaxes, self.button, self.dblclick = dlg.ax, button, dblclick
            self.xdata, self.ydata = t, price
            self.x, self.y = dlg.ax.transData.transform((t, price))
    dlg.onPress(Event(70.0, 0.10))
    dlg.onMotion(Event(75.0, 0.11))
    dlg.onRelease(Event(75.0, 0.11))
    assert dlg.points()[0] == [75.0, 0.11]
    dlg.onPress(Event(85.0, 0.05, dblclick=True))  # a new point, sorted by temperature
    assert [p[0] for p in dlg.points()] == [75.0, 85.0, 95.0]
    dlg.onPress(Event(95.0, 0.139, button=3))  # right-click removes
    assert [p[0] for p in dlg.points()] == [75.0, 85.0]


def test_fixed_values_of_a_dropdown():
    items = getDropDownItems(None, [[2, None, ('electricity', 'heat')]])
    assert list(items[2]) == ['electricity', 'heat']
