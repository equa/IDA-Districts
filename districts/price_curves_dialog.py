# coding=utf-8
"""Dialog "Price curves heat and cold" of an economic scenario (OpenSpec change network-cost-data): the points
(supply temperature, price) of a mode edited in a graph with the mouse or in a table; saved into public.price_curves."""
from typing import Any

from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg
from matplotlib.figure import Figure
from qgis.PyQt.QtCore import Qt
from qgis.PyQt.QtGui import QGuiApplication
from qgis.PyQt.QtWidgets import (
    QAbstractItemView, QComboBox, QDialog, QHBoxLayout, QHeaderView, QLabel, QMessageBox, QPushButton, QRadioButton, QTableWidget,
    QTableWidgetItem, QTabWidget, QVBoxLayout, QWidget,
)

from .utility_functions.translations import tr_msg

MODES = (('heat', '#d7301f'), ('cold', '#2171b5'))
PICK_PX = 8  # a click within this distance of a point grabs it


def loadCurves(cur, scenario_id):
    """{mode: [[t, price]]} of the scenario, sorted by temperature"""
    cur.execute('SELECT mode, t_supply, price_eur7kwh FROM public.price_curves WHERE scenario_id = %s ORDER BY t_supply;', (scenario_id,))
    curves = {mode: [] for mode, _ in MODES}
    for row in cur.fetchall():
        if row['t_supply'] is not None and row['price_eur7kwh'] is not None:
            curves.setdefault(row['mode'], []).append([float(row['t_supply']), float(row['price_eur7kwh'])])
    return curves


def saveCurves(cur, scenario_id, curves):
    cur.execute('DELETE FROM public.price_curves WHERE scenario_id = %s;', (scenario_id,))
    for mode, points in curves.items():
        for t, price in sorted(points):
            cur.execute('INSERT INTO public.price_curves (scenario_id, mode, t_supply, price_eur7kwh) VALUES (%s, %s, %s, %s);',
                        (scenario_id, mode, round(t, 2), round(price, 5)))


class PriceCurvesDialog(QDialog):
    def __init__(self, main, scenario_id=None):
        super().__init__()
        self.main = main
        self.curves, self.scenario_id, self.dirty = {}, None, False
        self.drag = None  # index of the point moved with the mouse
        self.ax: Any = None  # the axes of the graph, set by plot
        self.setWindowTitle(tr_msg('Price curves heat and cold'))
        layout = QVBoxLayout(self)
        info = QLabel(tr_msg('Price of the heat and cold losses over the supply temperature of the plant, linear between the points and '
                             'constant outside. Graph: drag a point, double-click to add one, right-click to remove one.'))
        info.setWordWrap(True)
        layout.addWidget(info)
        row = QHBoxLayout()
        self.combo_scenario = QComboBox()
        row.addWidget(QLabel(tr_msg('Scenario')))
        row.addWidget(self.combo_scenario, 1)
        self.rbtn_heat = QRadioButton(tr_msg('Heating'))
        self.rbtn_cold = QRadioButton(tr_msg('Cooling'))
        self.rbtn_heat.setChecked(True)
        row.addWidget(self.rbtn_heat)
        row.addWidget(self.rbtn_cold)
        layout.addLayout(row)
        self.tabs = QTabWidget()
        self.figure = Figure(figsize=(6, 3.4))
        self.canvas = FigureCanvasQTAgg(self.figure)
        self.canvas.setMinimumHeight(260)
        self.tabs.addTab(self.canvas, tr_msg('Graph'))
        table_tab = QWidget()
        inner = QVBoxLayout(table_tab)
        self.table = QTableWidget(0, 2)
        self.table.setHorizontalHeaderLabels([tr_msg('supply temperature [°C]'), tr_msg('Price [€/kWh]')])
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.table.verticalHeader().setVisible(False)
        self.table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        inner.addWidget(self.table)
        buttons = QHBoxLayout()
        self.btn_add = QPushButton('+')
        self.btn_add.setToolTip(tr_msg('Add a point'))
        self.btn_remove = QPushButton('−')
        self.btn_remove.setToolTip(tr_msg('Remove the selected points'))
        buttons.addWidget(self.btn_add)
        buttons.addWidget(self.btn_remove)
        buttons.addStretch()
        inner.addLayout(buttons)
        self.tabs.addTab(table_tab, tr_msg('Table'))
        layout.addWidget(self.tabs, 1)
        buttons = QHBoxLayout()
        self.btn_save = QPushButton(tr_msg('Save'))
        self.btn_close = QPushButton(tr_msg('Close'))
        buttons.addStretch()
        buttons.addWidget(self.btn_save)
        buttons.addWidget(self.btn_close)
        layout.addLayout(buttons)
        screen = QGuiApplication.primaryScreen()
        available = screen.availableGeometry() if screen else None
        self.resize(680, min(560, available.height() - 80) if available else 560)

        self.main.cur.execute('SELECT id, name FROM public.economic_scenarios ORDER BY id;')
        for scenario in self.main.cur.fetchall():
            self.combo_scenario.addItem(scenario['name'], scenario['id'])
        index = self.combo_scenario.findData(scenario_id)
        self.combo_scenario.setCurrentIndex(index if index >= 0 else 0)
        self.loadScenario()
        self.combo_scenario.currentIndexChanged.connect(lambda _: self.onScenarioChanged())
        self.rbtn_heat.toggled.connect(lambda _: self.refresh())
        self.table.itemChanged.connect(self.onTableEdited)
        self.btn_add.clicked.connect(self.addPoint)
        self.btn_remove.clicked.connect(self.removePoints)
        self.btn_save.clicked.connect(self.save)
        self.btn_close.clicked.connect(self.close)
        self.canvas.mpl_connect('button_press_event', self.onPress)
        self.canvas.mpl_connect('motion_notify_event', self.onMotion)
        self.canvas.mpl_connect('button_release_event', self.onRelease)

    # ---------------------------------------------------------------- data
    def mode(self):
        return 'heat' if self.rbtn_heat.isChecked() else 'cold'

    def points(self):
        return self.curves.setdefault(self.mode(), [])

    def loadScenario(self):
        self.scenario_id = self.combo_scenario.currentData()
        self.curves = loadCurves(self.main.cur, self.scenario_id) if self.scenario_id is not None else {}
        self.dirty = False
        self.refresh()

    def onScenarioChanged(self):
        if self.dirty and self.askSave():
            saveCurves(self.main.cur, self.scenario_id, self.curves)
        self.loadScenario()

    def askSave(self):
        answer = QMessageBox.question(self, self.windowTitle(), tr_msg('Save the changed price curves?'),
                                      QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
        return answer == QMessageBox.StandardButton.Yes

    def changed(self):
        self.points().sort()
        self.dirty = True
        self.refresh()

    def save(self):
        if self.scenario_id is None:
            return
        saveCurves(self.main.cur, self.scenario_id, self.curves)
        self.dirty = False

    def closeEvent(self, event):
        if self.dirty and self.askSave():
            self.save()
        super().closeEvent(event)

    # ---------------------------------------------------------------- views
    def refresh(self):
        self.fillTable()
        self.plot()

    def fillTable(self):
        self.table.blockSignals(True)
        self.table.setRowCount(0)
        for t, price in self.points():
            row = self.table.rowCount()
            self.table.insertRow(row)
            self.table.setItem(row, 0, QTableWidgetItem('{:g}'.format(t)))
            self.table.setItem(row, 1, QTableWidgetItem('{:g}'.format(price)))
        self.table.blockSignals(False)

    def plot(self, keep_limits=False):
        limits = (self.ax.get_xlim(), self.ax.get_ylim()) if keep_limits and self.ax is not None else None
        self.figure.clear()
        ax = self.figure.add_subplot(111)
        color = dict(MODES)[self.mode()]
        points = self.points()
        if points:
            t, price = zip(*points)
            span = max(5.0, (max(t) - min(t)) * 0.2)
            # constant outside the points, as the evaluation reads the curve
            ax.plot([min(t) - span] + list(t) + [max(t) + span], [price[0]] + list(price) + [price[-1]], color=color, linewidth=1.2)
            ax.plot(t, price, 'o', color=color, markersize=6)
            top = max(price) * 1.3 or 0.1
            ax.set_xlim(min(t) - span, max(t) + span)
        else:
            top = 0.2
            ax.set_xlim(0, 100) if self.mode() == 'heat' else ax.set_xlim(0, 30)
            ax.text(0.5, 0.5, tr_msg('no curve: the losses cost nothing') + '\n' + tr_msg('double-click to add a point'),
                    ha='center', va='center', fontsize=8, transform=ax.transAxes)
        ax.set_ylim(0, top)
        if limits:
            ax.set_xlim(*limits[0])
            ax.set_ylim(*limits[1])
        ax.set_xlabel(tr_msg('supply temperature [°C]'), fontsize=8)
        ax.set_ylabel('€/kWh', fontsize=8)
        ax.tick_params(labelsize=8)
        ax.grid(True, linewidth=0.3)
        self.ax = ax
        self.figure.tight_layout()
        self.canvas.draw()

    # ---------------------------------------------------------------- table
    def onTableEdited(self, item):
        points = self.points()
        try:
            value = float(item.text().replace(',', '.'))
        except ValueError:
            self.fillTable()
            return
        if item.row() < len(points):
            points[item.row()][item.column()] = value
            self.changed()

    def addPoint(self):
        points = self.points()
        t = points[-1][0] + 10 if points else (70.0 if self.mode() == 'heat' else 10.0)
        points.append([t, points[-1][1] if points else 0.1])
        self.changed()

    def removePoints(self):
        rows = sorted({index.row() for index in self.table.selectedIndexes()}, reverse=True)
        for row in rows:
            del self.points()[row]
        if rows:
            self.changed()

    # ---------------------------------------------------------------- mouse
    def nearest(self, event):
        """index of the point within PICK_PX of the mouse, or None"""
        best, distance = None, PICK_PX
        for k, (t, price) in enumerate(self.points()):
            x, y = self.ax.transData.transform((t, price))
            d = ((x - event.x) ** 2 + (y - event.y) ** 2) ** 0.5
            if d <= distance:
                best, distance = k, d
        return best

    def onPress(self, event):
        if event.inaxes is not self.ax or event.xdata is None:
            return
        k = self.nearest(event)
        if event.button == 3 and k is not None:
            del self.points()[k]
            self.changed()
        elif event.button == 1 and event.dblclick and k is None:
            self.points().append([round(event.xdata, 1), round(max(event.ydata, 0.0), 4)])
            self.changed()
        elif event.button == 1 and k is not None:
            self.drag = k

    def onMotion(self, event):
        if self.drag is None or event.inaxes is not self.ax or event.xdata is None:
            return
        self.points()[self.drag] = [round(event.xdata, 1), round(max(event.ydata, 0.0), 4)]
        self.dirty = True
        self.plot(keep_limits=True)  # the order is kept while dragging, sorted on release

    def onRelease(self, event):
        if self.drag is not None:
            self.drag = None
            self.changed()

    def keyPressEvent(self, event):
        # Enter in the table must not close the dialog
        if event.key() in (Qt.Key.Key_Return, Qt.Key.Key_Enter):
            return
        super().keyPressEvent(event)
