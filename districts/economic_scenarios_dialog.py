# coding=utf-8
"""Dialog "Economic scenarios": the scenario tables of the project, copying a scenario and its electricity profile
(OpenSpec change network-cost-data)."""
import os
import shutil

from qgis.PyQt.QtWidgets import (
    QComboBox, QDialog, QFileDialog, QHBoxLayout, QLabel, QLineEdit, QMessageBox, QPushButton, QVBoxLayout,
)

from .ida_resources import show_TableDialog
from .utility_functions.economic_data import ensureEconomicTables
from .utility_functions.economics import normalizedProfile, readProfile
from .utility_functions.translations import tr_msg

SCENARIO_DROPDOWN = [1, 'public', 'economic_scenarios', 'id', 'name']
TABLES = {
    'economic_scenarios': ('Scenarios', ['ID', 'Name', 'Interest [%/a]', 'Period [a]', 'Residual value', 'Default surface',
                                         'Electricity profile file', 'Pumps [€/kW]', 'Pump maintenance [%/a]', 'Pump lifetime [a]',
                                         'Example values', 'Description'],
                           '(id,name,interest_pct,period_a,residual_value,default_surface,el_profile_file,pump_costs_eur7kw,pump_maintenance_pct,pump_lifetime_a,example,description)', ''),
    'price_groups': ('Prices per cost group', ['ID', 'Scenario', 'Cost group', 'Start price [€/kWh]', 'Escalation [%/a]', 'Description'],
                     '(id,scenario_id,cost_group,start_price,escalation_pct,description)', [SCENARIO_DROPDOWN]),
    'price_levels': ('Price levels per year', ['ID', 'Scenario', 'Cost group', 'Year', 'Factor'],
                     '(id,scenario_id,cost_group,year,factor)', [SCENARIO_DROPDOWN]),
    'price_curves': ('Price curves heat and cold', ['ID', 'Scenario', 'Mode', 'Supply temperature [°C]', 'Price [€/kWh]'],
                     '(id,scenario_id,mode,t_supply,price_eur7kwh)', [SCENARIO_DROPDOWN]),
    'trench_costs': ('Trench costs per surface', ['ID', 'Scenario', 'Surface', 'a [€/m]', 'b [€/m per DN]', 'Description'],
                     '(id,scenario_id,surface,a_eur7m,b_eur7m_dn,description)', [SCENARIO_DROPDOWN]),
}
CHILD_TABLES = {'price_groups': 'cost_group,start_price,escalation_pct,description', 'price_levels': 'cost_group,year,factor',
                'price_curves': 'mode,t_supply,price_eur7kwh', 'trench_costs': 'surface,a_eur7m,b_eur7m_dn,description'}
SCENARIO_COLUMNS = 'interest_pct,period_a,residual_value,default_surface,el_profile_file,pump_costs_eur7kw,pump_maintenance_pct,pump_lifetime_a,example,description'


def pricesDir(config):
    return os.path.join(config['pathProjects'] + config['projectName'], 'prices')


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
        layout = QVBoxLayout(self)
        info = QLabel(tr_msg('Costs and prices of the economic evaluation. Electricity: start price × level of the year × '
                             'hourly profile; heat and cold: price curve of the supply temperature × level of the year; '
                             'trench: a + b × DN of the largest pipe per surface.'))
        info.setWordWrap(True)
        layout.addWidget(info)
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
        title, headers, columns, dropdowns = TABLES[table]
        show_TableDialog(main=self.main, title=tr_msg(title), table=table, headers=[tr_msg(h) for h in headers],
                         columns=columns, dropdowns=dropdowns)
        self.main.dlg_table.finished.connect(lambda *_: self.fillScenarios())

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
