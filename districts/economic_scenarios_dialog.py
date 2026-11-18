# coding=utf-8
"""Dialog "Economic scenarios": the scenario tables of the project, copying a scenario and its electricity profile
(OpenSpec change network-cost-data)."""
import os
import shutil

from qgis.PyQt.QtGui import QGuiApplication
from qgis.PyQt.QtWidgets import (
    QComboBox, QDialog, QFileDialog, QHBoxLayout, QLabel, QLineEdit, QMessageBox, QPushButton, QVBoxLayout,
)

from .ida_resources import show_TableDialog
from .utility_functions.dialog import infoTextEdit
from .price_curves_dialog import PriceCurvesDialog
from .utility_functions.economic_data import COST_GROUPS, ensureEconomicTables, trenchSurfaces
from .utility_functions.economics import normalizedProfile, readProfile
from .utility_functions.translations import tr_msg

SCENARIO_DROPDOWN = [1, 'public', 'economic_scenarios', 'id', 'name']
TABLES = {
    'economic_scenarios': ('Scenarios', ['ID', 'Name', 'Interest [%/a]', 'Period [a]', 'Residual value', 'Default surface',
                                         'Electricity profile file', 'Pumps [€/kW]', 'Pump maintenance [%/a]', 'Pump lifetime [a]',
                                         'Example values', 'Description', 'System boundary', 'Marginal plant above [% of peak]'],
                           '(id,name,interest_pct,period_a,residual_value,default_surface,el_profile_file,pump_costs_eur7kw,pump_maintenance_pct,pump_lifetime_a,example,description,'
                           'system_boundary,marginal_threshold_pct)', ''),
    'price_groups': ('Prices per cost group', ['ID', 'Scenario', 'Cost group', 'Start price [€/kWh]', 'Escalation [%/a]', 'Description'],
                     '(id,scenario_id,cost_group,start_price,escalation_pct,description)', [SCENARIO_DROPDOWN, [2, None, COST_GROUPS]]),
    'price_levels': ('Price levels per year', ['ID', 'Scenario', 'Cost group', 'Year', 'Factor'],
                     '(id,scenario_id,cost_group,year,factor)', [SCENARIO_DROPDOWN, [2, None, COST_GROUPS]]),
    'price_curves': ('Price curves heat and cold', ['ID', 'Scenario', 'Mode', 'Supply temperature [°C]', 'Price [€/kWh]'],
                     '(id,scenario_id,mode,t_supply,price_eur7kwh)', [SCENARIO_DROPDOWN]),
    'trench_costs': ('Trench costs per surface', ['ID', 'Scenario', 'Surface', 'a [€/m]', 'b [€/m per DN]', 'Description'],
                     '(id,scenario_id,surface,a_eur7m,b_eur7m_dn,description)', [SCENARIO_DROPDOWN]),
}
CHILD_TABLES = {'price_groups': 'cost_group,start_price,escalation_pct,description', 'price_levels': 'cost_group,year,factor',
                'price_curves': 'mode,t_supply,price_eur7kwh', 'trench_costs': 'surface,a_eur7m,b_eur7m_dn,description'}
SCENARIO_COLUMNS = ('interest_pct,period_a,residual_value,default_surface,el_profile_file,pump_costs_eur7kw,pump_maintenance_pct,pump_lifetime_a,example,description,'
                    'system_boundary,marginal_threshold_pct')
# 'automatic': the whole system when a customer template has an electricity entry in the energy-use list
SYSTEM_BOUNDARY_DROPDOWN = [12, None, ('automatic', 'operator', 'system')]


def pricesDir(config):
    return os.path.join(config['pathProjects'] + config['projectName'], 'prices')


def defaultSurfaceDropdown(cur):
    """the surfaces of the trench costs (and those already set) for the column default_surface"""
    cur.execute('SELECT DISTINCT default_surface FROM public.economic_scenarios;')
    return [5, None, tuple(trenchSurfaces(cur, [row['default_surface'] for row in cur.fetchall()]))]


def copyScenario(cur, scenario_id, name):
    """Copies a scenario with all its rows; returns the new id."""
    cur.execute('INSERT INTO public.economic_scenarios (name,{cols}) SELECT %s,{cols} FROM public.economic_scenarios WHERE id = %s RETURNING id;'.format(cols=SCENARIO_COLUMNS),  # nosec B608
                (name, scenario_id))
    new_id = cur.fetchone()['id']
    for table, cols in CHILD_TABLES.items():
        cur.execute('INSERT INTO public.{t} (scenario_id,{c}) SELECT %s,{c} FROM public.{t} WHERE scenario_id = %s;'.format(t=table, c=cols),  # nosec B608
                    (new_id, scenario_id))
    return new_id


def setProfile(cur, config, scenario_id, path):
    """Checks the profile (8760 or 8784 values), copies it into <project>\\prices and sets it on the scenario.
    Raises ValueError(number of values)."""
    normalizedProfile(readProfile(path))
    os.makedirs(pricesDir(config), exist_ok=True)
    name = os.path.basename(path)
    target = os.path.join(pricesDir(config), name)
    if os.path.normcase(os.path.abspath(path)) != os.path.normcase(os.path.abspath(target)):
        shutil.copyfile(path, target)
    cur.execute('UPDATE public.economic_scenarios SET el_profile_file = %s WHERE id = %s;', (name, scenario_id))
    return name


class EconomicScenariosDialog(QDialog):
    def __init__(self, main):
        super().__init__()
        self.main = main
        ensureEconomicTables(main.cur)
        self.setWindowTitle(tr_msg('Economic scenarios'))
        screen = QGuiApplication.primaryScreen()
        available = screen.availableGeometry() if screen else None
        self.resize(720, min(640, available.height() - 80) if available else 640)
        layout = QVBoxLayout(self)
        self.text_info = infoTextEdit(['economic_scenarios_info'], 330)
        self.text_info.setMinimumHeight(200)
        layout.addWidget(self.text_info)
        for table, (title, _, _, _) in TABLES.items():
            button = QPushButton(tr_msg(title))
            button.clicked.connect(lambda checked=False, t=table: self.openTable(t))
            layout.addWidget(button)
        row = QHBoxLayout()
        self.combo_scenario = QComboBox()
        row.addWidget(QLabel(tr_msg('Scenario')))
        row.addWidget(self.combo_scenario)
        layout.addLayout(row)
        row = QHBoxLayout()
        self.edit_name = QLineEdit()
        self.edit_name.setPlaceholderText(tr_msg('Name of the copy'))
        self.btn_copy = QPushButton(tr_msg('Copy scenario'))
        row.addWidget(self.edit_name)
        row.addWidget(self.btn_copy)
        layout.addLayout(row)
        self.btn_profile = QPushButton(tr_msg('Electricity profile...'))
        layout.addWidget(self.btn_profile)
        self.btn_close = QPushButton(tr_msg('Close'))
        layout.addWidget(self.btn_close)
        self.btn_copy.clicked.connect(self.copy)
        self.btn_profile.clicked.connect(self.profile)
        self.btn_close.clicked.connect(self.close)
        self.fillScenarios()

    def fillScenarios(self):
        self.combo_scenario.clear()
        self.main.cur.execute('SELECT id, name FROM public.economic_scenarios ORDER BY id;')
        for row in self.main.cur.fetchall():
            self.combo_scenario.addItem(row['name'], row['id'])

    def openTable(self, table):
        if table == 'price_curves':
            # a graph edited with the mouse and a table, per scenario and mode
            self.dlg_curves = PriceCurvesDialog(self.main, self.combo_scenario.currentData())
            self.dlg_curves.show()
            return
        title, headers, columns, dropdowns = TABLES[table]
        if table == 'economic_scenarios':
            dropdowns = [defaultSurfaceDropdown(self.main.cur), SYSTEM_BOUNDARY_DROPDOWN]
        show_TableDialog(main=self.main, title=tr_msg(title), table=table, headers=[tr_msg(h) for h in headers],
                         columns=columns, dropdowns=dropdowns)
        self.main.dlg_table.finished.connect(lambda *_: self.refresh())

    def refresh(self):
        current = self.combo_scenario.currentData()
        self.fillScenarios()
        index = self.combo_scenario.findData(current)
        if index >= 0:
            self.combo_scenario.setCurrentIndex(index)

    def copy(self):
        name = self.edit_name.text().strip()
        if self.combo_scenario.currentData() is None or not name:
            QMessageBox.information(self, tr_msg('Economic scenarios'), tr_msg('Select a scenario and enter a name for the copy.'))
            return
        copyScenario(self.main.cur, self.combo_scenario.currentData(), name)
        self.fillScenarios()
        self.combo_scenario.setCurrentIndex(self.combo_scenario.count() - 1)

    def profile(self):
        if self.combo_scenario.currentData() is None:
            return
        path, _ = QFileDialog.getOpenFileName(self, tr_msg('Electricity profile'), '', 'Profile (*.csv *.prn *.txt)')
        if not path:
            return
        try:
            name = setProfile(self.main.cur, self.main.config, self.combo_scenario.currentData(), path)
        except ValueError as error:
            QMessageBox.warning(self, tr_msg('Electricity profile'),
                                tr_msg('The profile must have 8760 or 8784 hourly values, the file has {}.').format(error.args[0]))
            return
        QMessageBox.information(self, tr_msg('Electricity profile'), tr_msg('Profile {} set for scenario {}.').format(name, self.combo_scenario.currentText()))
