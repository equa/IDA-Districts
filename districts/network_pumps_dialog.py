# coding=utf-8
"""Dialog "Network pumps": the pumps that move network water, per template of the project
(OpenSpec change pump-power-outputs)."""
import copy

from qgis.PyQt.QtGui import QBrush, QColor
from qgis.PyQt.QtWidgets import (
    QAbstractItemView, QComboBox, QDialog, QDoubleSpinBox, QFormLayout, QHBoxLayout, QHeaderView, QLabel,
    QPushButton, QTableWidget, QTableWidgetItem, QTextEdit, QVBoxLayout,
)

from .utility_functions.compat import ItemIsEditable, ItemIsEnabled, ItemIsSelectable, SelectRows
from .utility_functions.db import getTemplateNames
from .utility_functions.network_pumps import (
    DEFAULT_DP_INT, DEFAULT_ETA, FEATURES, detectProject, ensurePumpList, entryKey, markMissing, mergeDetection,
    newEntry, removeEntry, savePumpList, templatePath,
)
from .utility_functions.template_graph import templateComponents
from .utility_functions.translations import tr, tr_msg

COLUMNS = ('feature', 'template', 'type', 'component', 'kind', 'variable', 'eta', 'dp_int', 'source')
COL_ETA, COL_DP = COLUMNS.index('eta'), COLUMNS.index('dp_int')


def templateKey(feature, t_name):
    return '{}\t{}'.format(feature, t_name)


def splitTemplateKey(key):
    return tuple(key.split('\t', 1)) if key else None


def projectTemplates(cur):
    return {feature: getTemplateNames(cur, feature, seperator='_') for feature in FEATURES}


def warningText(feature, t_name, warning):
    kind, name, detail = warning
    if kind == 'macro_pump':
        return tr_msg('{} template {}: pump {} in {} is not analysed; add it if it moves network water.').format(
            tr('@default', feature), t_name, detail, name)
    if kind == 'unreadable':
        return tr_msg('{} template {}: {} cannot be read ({}).').format(tr('@default', feature), t_name, name, detail)
    return tr_msg('{} template {}: file not found ({}).').format(tr('@default', feature), t_name, name)


class NetworkPumpsDialog(QDialog):
    def __init__(self, config, cur, parent=None):
        super().__init__(parent)
        self.config = config
        self.templates = projectTemplates(cur)
        self.data = ensurePumpList(config, self.templates)
        self.saved = copy.deepcopy(self.data)
        self.changed = False
        self.setWindowTitle(tr_msg('Network pumps'))
        self.resize(900, 450)

        layout = QVBoxLayout(self)
        info = QLabel(tr_msg('Pumps that move network water. Found: in the flow path between the network connections of '
                             'the template without a heat exchanger in between. Estimate: power from the connection mass '
                             'flow and pressures, Δp int. and η.'))
        info.setWordWrap(True)
        layout.addWidget(info)
        self.table = QTableWidget(0, len(COLUMNS))
        self.table.setHorizontalHeaderLabels([tr_msg('Feature type'), tr_msg('Template'), tr_msg('Component'), tr_msg('Component name'),
                                              tr_msg('Kind'), tr_msg('Power variable'), tr_msg('η'), tr_msg('Δp int. [kPa]'), tr_msg('Source')])
        # the widths start at the contents and can be changed with the mouse
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Interactive)
        self.table.horizontalHeader().setStretchLastSection(True)
        self.types = {}
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

    def fill(self):
        self.table.setRowCount(0)
        for entry in self.data['entries']:
            row = self.table.rowCount()
            self.table.insertRow(row)
            values = {'feature': tr('@default', entry['feature']), 'type': self.componentType(entry),
                      'kind': tr_msg('estimate') if entry['kind'] == 'estimate' else tr_msg('variable'),
                      'source': tr_msg('found') if entry['source'] == 'found' else tr_msg('added'),
                      'eta': '{:g}'.format(entry['eta']), 'dp_int': '{:g}'.format(entry['dp_int'] / 1000)}
            for col, key in enumerate(COLUMNS):
                item = QTableWidgetItem(str(values.get(key, entry.get(key, ''))))
                editable = entry['kind'] == 'estimate' and key in ('eta', 'dp_int')
                item.setFlags(ItemIsSelectable | ItemIsEnabled | (ItemIsEditable if editable else ItemIsSelectable))
                if entry.get('missing'):
                    item.setForeground(QBrush(QColor('gray')))
                    item.setToolTip(tr_msg('The component no longer exists in the template; no output is written for it.'))
                self.table.setItem(row, col, item)
        self.table.resizeColumnsToContents()
        self.log.setPlainText('\n'.join(tr_msg('{} template {}: component {} no longer exists.').format(
            tr('@default', e['feature']), e['template'], e['component']) for e in self.data['entries'] if e.get('missing')))

    def componentType(self, entry):
        """IDA type of the entry's component (e.g. PUMP, HP_B2B); entries saved without it are looked up in the template"""
        if entry.get('type'):
            return entry['type']
        key = (entry['feature'], entry['template'])
        if key not in self.types:
            try:
                self.types[key] = {comp: typ for comp, (typ, _) in templateComponents(templatePath(self.config, *key)).items()}
            except OSError:
                self.types[key] = {}
        return self.types[key].get(entry['component'], '')

    def readEdits(self):
        """η and Δp int. of the estimate rows from the table"""
        for row, entry in enumerate(self.data['entries']):
            if entry['kind'] != 'estimate':
                continue
            for key, col, factor, default in (('eta', COL_ETA, 1, DEFAULT_ETA), ('dp_int', COL_DP, 1000, DEFAULT_DP_INT)):
                try:
                    value = float(self.table.item(row, col).text().replace(',', '.')) * factor
                    entry[key] = value if value > 0 or key == 'dp_int' else default
                except (ValueError, AttributeError):
                    pass

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
        dlg = AddPumpDialog(self.config, self.templates, self)
        if dlg.exec():
            entry = dlg.entry()
            if entry and entryKey(entry) not in {entryKey(e) for e in self.data['entries']}:
                self.data['entries'].append(entry)
                self.data['removed'] = [key for key in self.data['removed'] if tuple(key) != entryKey(entry)]
                self.fill()

    def remove(self):
        self.readEdits()
        rows = sorted({index.row() for index in self.table.selectedIndexes()}, reverse=True)
        for row in rows:
            self.data = removeEntry(self.data, self.data['entries'][row])
        self.fill()

    def accept(self):
        self.readEdits()
        savePumpList(self.config, self.data)
        clean = lambda data: [{k: v for k, v in e.items() if k != 'missing'} for e in data['entries']]  # noqa: E731
        self.changed = clean(self.data) != clean(self.saved)
        super().accept()


class AddPumpDialog(QDialog):
    """Adds a component of a template: its power variable, or kind estimate (a component containing a pump)."""
    def __init__(self, config, templates, parent=None):
        super().__init__(parent)
        self.config = config
        self.setWindowTitle(tr_msg('Add a network pump'))
        form = QFormLayout(self)
        self.combo_template = QComboBox()
        for feature in FEATURES:
            for t_name in templates.get(feature, []):
                # a string: Qt returns a stored tuple as a list
                self.combo_template.addItem('{}: {}'.format(tr('@default', feature), t_name), templateKey(feature, t_name))
        self.combo_component = QComboBox()
        self.combo_kind = QComboBox()
        self.combo_kind.addItem(tr_msg('variable'), 'variable')
        self.combo_kind.addItem(tr_msg('estimate'), 'estimate')
        self.combo_variable = QComboBox()
        self.combo_variable.setEditable(True)
        self.spin_eta = QDoubleSpinBox()
        self.spin_eta.setRange(0.05, 1.0)
        self.spin_eta.setSingleStep(0.05)
        self.spin_eta.setValue(DEFAULT_ETA)
        self.spin_dp = QDoubleSpinBox()
        self.spin_dp.setRange(0, 1000)
        self.spin_dp.setValue(DEFAULT_DP_INT / 1000)
        form.addRow(tr_msg('Template'), self.combo_template)
        form.addRow(tr_msg('Component'), self.combo_component)
        form.addRow(tr_msg('Kind'), self.combo_kind)
        form.addRow(tr_msg('Power variable'), self.combo_variable)
        form.addRow(tr_msg('η'), self.spin_eta)
        form.addRow(tr_msg('Δp int. [kPa]'), self.spin_dp)
        buttons = QHBoxLayout()
        ok, cancel = QPushButton(tr_msg('OK')), QPushButton(tr_msg('Cancel'))
        buttons.addWidget(ok)
        buttons.addWidget(cancel)
        form.addRow(buttons)
        ok.clicked.connect(self.accept)
        cancel.clicked.connect(self.reject)
        self.combo_template.currentIndexChanged.connect(self.fillComponents)
        self.combo_component.currentIndexChanged.connect(self.fillVariables)
        self.combo_kind.currentIndexChanged.connect(self.updateEnabled)
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
        variables = [v.strip('|') for v in self.components.get(comp, ('', []))[1]]
        if 'PPUMP' not in variables:
            variables.insert(0, 'PPUMP')
        self.combo_variable.addItems(variables)
        self.updateEnabled()

    def updateEnabled(self):
        estimate = self.combo_kind.currentData() == 'estimate'
        self.combo_variable.setEnabled(not estimate)
        self.spin_eta.setEnabled(estimate)
        self.spin_dp.setEnabled(estimate)

    def entry(self):
        data, comp = splitTemplateKey(self.combo_template.currentData()), self.combo_component.currentData()
        if not data or not comp:
            return None
        variable = self.combo_variable.currentText().strip()
        # IDA names with lower-case letters are written between bars
        if variable and variable != variable.upper() and not variable.startswith('|'):
            variable = '|{}|'.format(variable)
        return newEntry(data[0], data[1], comp, kind=self.combo_kind.currentData(), variable=variable or 'PPUMP',
                        source='added', eta=self.spin_eta.value(), dp_int=self.spin_dp.value() * 1000,
                        type=self.components.get(comp, ('', []))[0])
