# coding=utf-8
"""Dialog "Energy use": the components of the plant and customer templates that buy energy, with variable and carrier
(OpenSpec change plant-energy-costs, D1-D2)."""
import copy

from qgis.PyQt.QtGui import QBrush, QColor
from qgis.PyQt.QtWidgets import (
    QAbstractItemView, QComboBox, QDialog, QFormLayout, QHBoxLayout, QHeaderView, QLabel, QLineEdit, QPushButton,
    QTableWidget, QTableWidgetItem, QTextEdit, QVBoxLayout,
)

from .network_pumps_dialog import projectTemplates, splitTemplateKey, templateKey
from .utility_functions.compat import ItemIsEditable, ItemIsEnabled, ItemIsSelectable, SelectRows
from .utility_functions.energy_use import (
    CARRIER_LABELS, CARRIERS, FEATURES, detectProject, ensureEnergyList, entryKey, markMissing, mergeDetection, newEntry, pumpConflicts,
    removeEntry, saveEnergyList, templatePath,
)
from .utility_functions.network_pumps import loadPumpList
from .utility_functions.template_graph import templateComponents
from .utility_functions.translations import tr, tr_msg

COLUMNS = ('feature', 'template', 'type', 'component', 'variable', 'carrier', 'name', 'source')
COL_CARRIER, COL_NAME = COLUMNS.index('carrier'), COLUMNS.index('name')


def carrierCombo(carrier):
    combo = QComboBox()
    for key in CARRIERS:
        combo.addItem(tr_msg(CARRIER_LABELS[key]), key)
    combo.setCurrentIndex(max(0, combo.findData(carrier)))
    return combo


def warningText(feature, t_name, warning):
    kind, name, detail = warning
    if kind == 'macro_energy':
        return tr_msg('{} template {}: component {} in {} is not analysed; add it if it buys energy.').format(
            tr('@default', feature), t_name, detail, name)
    if kind == 'unreadable':
        return tr_msg('{} template {}: {} cannot be read ({}).').format(tr('@default', feature), t_name, name, detail)
    return tr_msg('{} template {}: file not found ({}).').format(tr('@default', feature), t_name, name)


class EnergyUseDialog(QDialog):
    def __init__(self, config, cur, parent=None, feature=None):
        """feature: 'customer' or 'energy_plant' shows only the entries of that feature type (the list stays one per project)"""
        super().__init__(parent)
        self.config = config
        self.feature = feature
        self.templates = projectTemplates(cur)
        self.data = ensureEnergyList(config, self.templates)
        self.saved = copy.deepcopy(self.data)
        self.changed = False
        self.setWindowTitle(tr_msg('Energy use') + (' – ' + tr('@default', feature) if feature else ''))
        self.resize(950, 450)

        layout = QVBoxLayout(self)
        info = QLabel(tr_msg('Components that buy energy: the variable is written as an output, its energy is valued with the '
                             'price of the carrier (economic scenario). Found: boilers (QSUP, fuel) and heat pumps '
                             '(P_el_total, electricity); a boiler standing for waste heat is changed to purchased heat. Energy from the surroundings '
                             '(borehole field, ambient air) is added with the carrier ambient (free). Delivered heat/cold (e.g. the heat '
                             'exchanger of a substation, heat > 0, cold < 0) is not bought: it is the reference of the key figures.'))
        info.setWordWrap(True)
        layout.addWidget(info)
        self.table = QTableWidget(0, len(COLUMNS))
        self.table.setHorizontalHeaderLabels([tr_msg('Feature type'), tr_msg('Template'), tr_msg('Component'), tr_msg('Component name'),
                                              tr_msg('Energy variable'), tr_msg('Carrier'), tr_msg('Name'), tr_msg('Source')])
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Interactive)
        self.table.horizontalHeader().setStretchLastSection(True)
        self.table.setSelectionBehavior(SelectRows)
        self.table.setEditTriggers(QAbstractItemView.EditTrigger.AllEditTriggers)
        layout.addWidget(self.table)
        self.log = QTextEdit()
        self.log.setReadOnly(True)
        self.log.setMaximumHeight(80)
        layout.addWidget(self.log)

        buttons = QHBoxLayout()
        self.btn_detect = QPushButton(tr_msg('Detect'))
        self.btn_add = QPushButton(tr_msg('Add...'))
        self.btn_remove = QPushButton(tr_msg('Remove'))
        self.btn_ok = QPushButton(tr_msg('OK'))
        self.btn_cancel = QPushButton(tr_msg('Cancel'))
        for button in (self.btn_detect, self.btn_add, self.btn_remove):
            buttons.addWidget(button)
        buttons.addStretch()
        buttons.addWidget(self.btn_ok)
        buttons.addWidget(self.btn_cancel)
        layout.addLayout(buttons)
        self.btn_detect.clicked.connect(self.detect)
        self.btn_add.clicked.connect(self.add)
        self.btn_remove.clicked.connect(self.remove)
        self.btn_ok.clicked.connect(self.accept)
        self.btn_cancel.clicked.connect(self.reject)
        self.fill()

    def shown(self):
        """the entries shown in the table (rows in this order)"""
        return [e for e in self.data['entries'] if not self.feature or e['feature'] == self.feature]

    def fill(self):
        conflicts = pumpConflicts(self.data, loadPumpList(self.config))
        self.table.setRowCount(0)
        for entry in self.shown():
            row = self.table.rowCount()
            self.table.insertRow(row)
            values = {'feature': tr('@default', entry['feature']), 'source': tr_msg('found') if entry['source'] == 'found' else tr_msg('added')}
            for col, key in enumerate(COLUMNS):
                if key == 'carrier':
                    self.table.setCellWidget(row, col, carrierCombo(entry['carrier']))
                    continue
                item = QTableWidgetItem(str(values.get(key, entry.get(key, ''))))
                item.setFlags(ItemIsSelectable | ItemIsEnabled | (ItemIsEditable if key == 'name' else ItemIsSelectable))
                if entry.get('missing'):
                    item.setForeground(QBrush(QColor('gray')))
                    item.setToolTip(tr_msg('The component no longer exists in the template; no output is written for it.'))
                elif entryKey(entry) in conflicts:
                    item.setForeground(QBrush(QColor('#a05000')))
                    item.setToolTip(tr_msg('The component is also in the network pump list: its power would be counted twice.'))
                self.table.setItem(row, col, item)
        self.table.resizeColumnsToContents()
        lines = [tr_msg('{} template {}: component {} no longer exists.').format(tr('@default', e['feature']), e['template'], e['component'])
                 for e in self.shown() if e.get('missing')]
        lines += [tr_msg('{} template {}: component {} is also a network pump; remove it from one list.').format(
            tr('@default', e['feature']), e['template'], e['component']) for e in self.shown() if entryKey(e) in conflicts]
        self.log.setPlainText('\n'.join(lines))

    def readEdits(self):
        """carrier and name of every row from the table"""
        for row, entry in enumerate(self.shown()):
            combo = self.table.cellWidget(row, COL_CARRIER)
            if combo is not None:
                entry['carrier'] = combo.currentData()
            item = self.table.item(row, COL_NAME)
            if item is not None:
                entry['name'] = item.text().strip()

    def detect(self):
        self.readEdits()
        found, warnings = detectProject(self.config, self.templates)
        before = {entryKey(e) for e in self.data['entries']}
        self.data = markMissing(self.config, mergeDetection(self.data, found))
        added = [e for e in self.data['entries'] if entryKey(e) not in before]
        self.fill()
        lines = [warningText(*w) for w in warnings]
        lines.append(tr_msg('Detection: {} new entries.').format(len(added)))
        self.log.append('\n'.join(lines))

    def add(self):
        self.readEdits()
        dlg = AddEnergyDialog(self.config, {f: t for f, t in self.templates.items() if not self.feature or f == self.feature}, self)
        if dlg.exec():
            entry = dlg.entry()
            if entry and entryKey(entry) not in {entryKey(e) for e in self.data['entries']}:
                self.data['entries'].append(entry)
                self.data['removed'] = [key for key in self.data['removed'] if tuple(key) != entryKey(entry)]
                self.fill()

    def remove(self):
        self.readEdits()
        shown = self.shown()
        for row in sorted({index.row() for index in self.table.selectedIndexes()}, reverse=True):
            self.data = removeEntry(self.data, shown[row])
        self.fill()

    def accept(self):
        self.readEdits()
        saveEnergyList(self.config, self.data)
        clean = lambda data: [{k: v for k, v in e.items() if k != 'missing'} for e in data['entries']]  # noqa: E731
        self.changed = clean(self.data) != clean(self.saved)
        super().accept()


class AddEnergyDialog(QDialog):
    """Adds a component of a template with its energy variable and carrier."""
    def __init__(self, config, templates, parent=None):
        super().__init__(parent)
        self.config = config
        self.setWindowTitle(tr_msg('Add an energy-using component'))
        form = QFormLayout(self)
        self.combo_template = QComboBox()
        for feature in FEATURES:
            for t_name in templates.get(feature, []):
                self.combo_template.addItem('{}: {}'.format(tr('@default', feature), t_name), templateKey(feature, t_name))
        self.combo_component = QComboBox()
        self.combo_variable = QComboBox()
        self.combo_variable.setEditable(True)
        self.combo_carrier = carrierCombo('electricity')
        self.edit_name = QLineEdit()
        form.addRow(tr_msg('Template'), self.combo_template)
        form.addRow(tr_msg('Component'), self.combo_component)
        form.addRow(tr_msg('Energy variable'), self.combo_variable)
        form.addRow(tr_msg('Carrier'), self.combo_carrier)
        form.addRow(tr_msg('Name'), self.edit_name)
        buttons = QHBoxLayout()
        ok, cancel = QPushButton(tr_msg('OK')), QPushButton(tr_msg('Cancel'))
        buttons.addWidget(ok)
        buttons.addWidget(cancel)
        form.addRow(buttons)
        ok.clicked.connect(self.accept)
        cancel.clicked.connect(self.reject)
        self.combo_template.currentIndexChanged.connect(self.fillComponents)
        self.combo_component.currentIndexChanged.connect(self.fillVariables)
        self.components = {}
        self.fillComponents()

    def fillComponents(self):
        self.combo_component.clear()
        data = splitTemplateKey(self.combo_template.currentData())
        self.components = {}
        if data:
            try:
                self.components = templateComponents(templatePath(self.config, *data))
            except OSError:
                self.components = {}
        for comp, (typ, _) in sorted(self.components.items()):
            self.combo_component.addItem('{} ({})'.format(comp, typ), comp)
        self.fillVariables()

    def fillVariables(self):
        self.combo_variable.clear()
        comp = self.combo_component.currentData()
        self.combo_variable.addItems([v.strip('|') for v in self.components.get(comp, ('', []))[1]])

    def entry(self):
        data, comp = splitTemplateKey(self.combo_template.currentData()), self.combo_component.currentData()
        variable = self.combo_variable.currentText().strip()
        if not data or not comp or not variable:
            return None
        # IDA names with lower-case letters are written between bars
        if variable != variable.upper() and not variable.startswith('|'):
            variable = '|{}|'.format(variable)
        return newEntry(data[0], data[1], comp, variable, self.combo_carrier.currentData(), type=self.components.get(comp, ('', []))[0],
                        name=self.edit_name.text().strip(), source='added')
