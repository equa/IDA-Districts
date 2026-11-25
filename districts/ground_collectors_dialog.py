# coding=utf-8
"""Resource dialog of the ground collectors (change ground-collector-routes, design R11): one row per collector type,
saved row by row (the generic table dialog truncates its table, which would cascade to the line types), the fit of a
type in the background and the mean liquid temperature of selected collector lines from their results."""
import json
import traceback

from qgis.core import QgsMessageLog, QgsProject
from qgis.PyQt.QtWidgets import (
    QAbstractItemView, QComboBox, QDialog, QHBoxLayout, QLabel, QMessageBox, QPushButton, QTableWidget, QTableWidgetItem,
    QVBoxLayout,
)

from .utility_functions.compat import MessageCritical
from .utility_functions.dialog import qt_item_flag
from .utility_functions.files import loadModellingSettings
from .utility_functions.ground_collectors import (
    PRESET_DEFAULTS, CollectorInUse, cachedFit, deleteCollector, ensureGroundCollectorTables, fitFor, liquidNames,
    readCollectors, saveCollector, setMeanFromResults, usedBy,
)
from .utility_functions.protected_lines_widget import linesLayer
from .utility_functions.translations import tr_msg

PRESETS = tuple(PRESET_DEFAULTS)
START_MODES = ('undisturbed', 'precalculated')


#the inputs of all presets, one column each; a column the row's preset does not use is empty and locked
INPUTS = ('ring_diameter_m', 'pitch_m', 'layer_width_m', 'pipe_spacing_m', 'depth_m', 'spacing_m')


def columns():
    """(key, label, kind) of the table; kind: text, float, int, preset, input, pipe, liquid, start, fit"""
    labels = {'ring_diameter_m': tr_msg('Ring diameter [m]'), 'pitch_m': tr_msg('Ring pitch [m]'),
              'layer_width_m': tr_msg('Layer width [m]'), 'pipe_spacing_m': tr_msg('Pipe spacing [m]'),
              'depth_m': tr_msg('Depth [m]'), 'spacing_m': tr_msg('Trench spacing [m]')}
    return [
        ('name', tr_msg('Name'), 'text'), ('description', tr_msg('Description'), 'text'),
        ('preset', tr_msg('Geometry'), 'preset')] + [(key, labels[key], 'input') for key in INPUTS] + [
        ('pipe_id', tr_msg('Loop pipe'), 'pipe'), ('loop_sequence', tr_msg('Loop pipe sequence in the bundle'), 'int'),
        ('liquid_id', tr_msg('Liquid'), 'liquid'), ('t_freeze_liquid_c', tr_msg('Liquid freezing point [°C]'), 'float'),
        ('lambda_w7mk', tr_msg('Soil conductivity [W/(m K)]'), 'float'), ('rho_c_j7m3k', tr_msg('Soil capacity [J/(m³ K)]'), 'float'),
        ('water_content', tr_msg('Water content [-]'), 'float'), ('lambda_frozen_ratio', tr_msg('Conductivity frozen/unfrozen [-]'), 'float'),
        ('albedo', tr_msg('Albedo [-]'), 'float'), ('epsilon', tr_msg('Emissivity [-]'), 'float'),
        ('h_conv_w7m2k', tr_msg('Convection [W/(m² K)]'), 'float'), ('d_layer_m', tr_msg('Surface layer [m]'), 'float'),
        ('rho_c_layer_j7m3k', tr_msg('Surface layer capacity [J/(m³ K)]'), 'float'),
        ('t_mean_init', tr_msg('Mean liquid temperature [°C]'), 'float'),
        ('start_mode', tr_msg('Start state'), 'start'), ('start_years', tr_msg('Pre-calculated years'), 'int'),
        ('n_sections', tr_msg('Sections'), 'int'),
        ('cost_trench_eur7m', tr_msg('Costs per trench meter [EUR/m]'), 'float'), ('cost_loop_eur7m', tr_msg('Costs per loop meter [EUR/m]'), 'float'),
        ('maintenance_pct', tr_msg('Maintenance [%/a]'), 'float'), ('lifetime_a', tr_msg('Lifetime [a]'), 'float'),
        ('fit', tr_msg('Fit'), 'fit'),
    ]


def fitText(entry):
    if entry is None:
        return tr_msg('not fitted')
    errors = ', '.join('{} {:.1%}'.format(k, v) for k, v in entry['errors'].items())
    return (tr_msg('accepted ({})') if entry['accepted'] else tr_msg('not accepted ({})')).format(errors)


class GroundCollectorsDialog(QDialog):
    def __init__(self, main):
        super().__init__(main.iface.mainWindow() if getattr(main, 'iface', None) else None)
        self.main = main
        self.cur = main.cur
        ensureGroundCollectorTables(self.cur)
        self.setWindowTitle(tr_msg('Ground collectors'))
        self.cols = columns()
        self.keys = [c[0] for c in self.cols]
        self.settings = loadModellingSettings(main.plugin_dir, main.config) or {}
        self.cur.execute('SELECT id, name FROM public.pipes ORDER BY name;')
        self.pipes = [(r['id'], r['name']) for r in self.cur.fetchall()]
        self.liquids = liquidNames(self.cur)

        self.table = QTableWidget(0, len(self.cols))
        self.table.setHorizontalHeaderLabels([c[1] for c in self.cols])
        self.table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.table.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)
        top = QHBoxLayout()
        for label, slot in ((tr_msg('Add'), lambda: self.addRow()), (tr_msg('Copy'), self.copyRow), (tr_msg('Delete'), self.deleteRow),
                            (tr_msg('Fit'), self.fitSelected), (tr_msg('Mean temperature from results'), self.meanFromResults)):
            button = QPushButton(label)
            button.clicked.connect(slot)
            top.addWidget(button)
        top.addStretch()
        self.status = QLabel(tr_msg('Each collector type is a route type of the lines; every loop lies in its own trench.'))
        self.status.setWordWrap(True)
        bottom = QHBoxLayout()
        bottom.addStretch()
        for label, slot in ((tr_msg('Save'), self.saveAndClose), (tr_msg('Cancel'), self.reject)):
            button = QPushButton(label)
            button.clicked.connect(slot)
            bottom.addWidget(button)
        layout = QVBoxLayout(self)
        layout.addLayout(top)
        layout.addWidget(self.table, 1)
        layout.addWidget(self.status)
        layout.addLayout(bottom)
        self.resize(1300, 450)
        self.deleted = []
        self.load()

    # ---------------------------------------------------------------- table
    def load(self):
        self.table.setRowCount(0)
        self.deleted = []
        for resource in readCollectors(self.cur).values():
            self.addRow(resource)
        self.table.resizeColumnsToContents()

    def addRow(self, resource=None):
        resource = dict(resource or {})
        if not resource:
            resource = {'name': self.uniqueName(tr_msg('Collector')), 'preset': PRESETS[0], 'preset_inputs': PRESET_DEFAULTS[PRESETS[0]],
                        'loop_sequence': 1, 'liquid_id': min(self.liquids, default=None), 't_freeze_liquid_c': 0,
                        'lambda_w7mk': 1.5, 'rho_c_j7m3k': 2200000, 'water_content': 0.25, 'lambda_frozen_ratio': 1, 'albedo': 0.25, 'epsilon': 0.95, 'h_conv_w7m2k': 10,
                        'd_layer_m': 0.05, 'rho_c_layer_j7m3k': 2200000, 't_mean_init': 5, 'start_mode': START_MODES[0],
                        'start_years': 5, 'n_sections': 3, 'cost_trench_eur7m': 0, 'cost_loop_eur7m': 0, 'maintenance_pct': 1,
                        'lifetime_a': 50}
        inputs = resource.get('preset_inputs')
        inputs = json.loads(inputs) if isinstance(inputs, str) else dict(inputs or {})
        row = self.table.rowCount()
        self.table.insertRow(row)
        for col, (key, _, kind) in enumerate(self.cols):
            value = inputs.get(key) if kind == 'input' else resource.get(key)
            if kind in ('preset', 'pipe', 'start', 'liquid'):
                combo = QComboBox()
                options = {'preset': [(p, tr_msg(p)) for p in PRESETS], 'start': [(m, tr_msg(m)) for m in START_MODES],
                           'liquid': list(self.liquids.items()),
                           'pipe': [(None, '')] + [(pid, '{}: {}'.format(pid, name)) for pid, name in self.pipes]}[kind]
                for data, text in options:
                    combo.addItem(text, data)
                index = combo.findData(value)
                combo.setCurrentIndex(max(index, 0))
                if kind == 'preset':
                    combo.currentIndexChanged.connect(lambda _, c=combo: self.presetChanged(c))
                self.table.setCellWidget(row, col, combo)
                continue
            if kind == 'fit':
                text = self.fitStatus(resource) if resource.get('id') is not None else tr_msg('not fitted')
            else:
                text = '' if value is None else str(value)
            item = QTableWidgetItem(text)
            if kind == 'fit':
                item.setFlags(item.flags() & ~qt_item_flag('ItemIsEditable'))
            self.table.setItem(row, col, item)
        self.table.item(row, 0).setData(256, resource.get('id'))  # Qt.UserRole: the resource id of a saved row
        self.lockInputs(row, fill=False)
        return row

    def uniqueName(self, base):
        names = {self.cellText(r, 'name') for r in range(self.table.rowCount())}
        k, name = 1, base
        while name in names:
            k += 1
            name = '{} {}'.format(base, k)
        return name

    def fitStatus(self, resource):
        try:
            return fitText(cachedFit(self.cur, resource, self.settings)) if 'kusuda_tsurfmean' in self.settings else tr_msg('no Kusuda settings')
        except (ValueError, KeyError, TypeError) as e:
            return str(e)

    def presetChanged(self, combo):
        for row in range(self.table.rowCount()):
            if self.table.cellWidget(row, self.keys.index('preset')) is combo:
                self.lockInputs(row, fill=True)

    def lockInputs(self, row, fill):
        """the input columns of the row's preset editable (empty ones filled with the defaults when fill), the others
        empty and locked"""
        defaults = PRESET_DEFAULTS[self.table.cellWidget(row, self.keys.index('preset')).currentData()]
        for key in INPUTS:
            item = self.table.item(row, self.keys.index(key))
            if key in defaults:
                item.setFlags(item.flags() | qt_item_flag('ItemIsEditable') | qt_item_flag('ItemIsEnabled'))
                if fill and not item.text().strip():
                    item.setText('{:g}'.format(defaults[key]))
            else:
                item.setText('')
                item.setFlags(item.flags() & ~qt_item_flag('ItemIsEditable') & ~qt_item_flag('ItemIsEnabled'))

    def cellText(self, row, key):
        item = self.table.item(row, self.keys.index(key))
        return item.text().strip() if item else ''

    def rowId(self, row):
        return self.table.item(row, 0).data(256)

    def rowValues(self, row):
        """the resource of a table row; raises ValueError naming the row and the column"""
        values = {'id': self.rowId(row)}
        for col, (key, label, kind) in enumerate(self.cols):
            try:
                if kind in ('preset', 'pipe', 'start', 'liquid'):
                    values[key] = self.table.cellWidget(row, col).currentData()
                elif kind == 'input':
                    if key in PRESET_DEFAULTS[values['preset']]:
                        text = self.cellText(row, key).replace(',', '.')
                        if not text:
                            raise ValueError(tr_msg('a value is needed'))
                        if float(text) <= 0:
                            raise ValueError(tr_msg('the value must be positive'))
                        values.setdefault('preset_inputs', {})[key] = float(text)
                elif kind == 'fit':
                    continue
                elif kind == 'text':
                    values[key] = self.cellText(row, key) or None
                else:
                    text = self.cellText(row, key).replace(',', '.')
                    values[key] = None if not text else (int(text) if kind == 'int' else float(text))
            except ValueError as e:
                raise ValueError(tr_msg('Row {}, {}: {}').format(row + 1, label, e))
        if not values['name']:
            raise ValueError(tr_msg('Row {}: a name is needed.').format(row + 1))
        return values

    def copyRow(self):
        """a new row with the cells of the selected one (also cells that do not parse yet)"""
        row = self.table.currentRow()
        if row < 0:
            return
        new = self.addRow()
        for col in range(len(self.cols)):
            combo = self.table.cellWidget(row, col)
            if combo is not None:
                self.table.cellWidget(new, col).setCurrentIndex(combo.currentIndex())
            elif self.cols[col][2] != 'fit':
                self.table.item(new, col).setText(self.table.item(row, col).text())
        self.table.item(new, 0).setText(self.uniqueName(self.cellText(row, 'name') or tr_msg('Collector')))
        self.lockInputs(new, fill=False)
        self.table.selectRow(new)

    def deleteRow(self):
        row = self.table.currentRow()
        if row < 0:
            return
        if self.rowId(row) is not None:
            self.deleted.append(self.rowId(row))
        self.table.removeRow(row)

    # ---------------------------------------------------------------- save
    def versions(self):
        self.cur.execute('SELECT name FROM public.versionhandling ORDER BY name;')
        return [r['name'] for r in self.cur.fetchall()]

    def save(self):
        """saves all rows; False (with a message) when a row is invalid or a deleted type is used by lines"""
        try:
            rows = [self.rowValues(row) for row in range(self.table.rowCount())]
        except ValueError as e:
            QMessageBox.warning(self, self.windowTitle(), str(e))
            return False
        names = [r['name'] for r in rows]
        if len(set(names)) != len(names):
            QMessageBox.warning(self, self.windowTitle(), tr_msg('The names of the collector types must differ.'))
            return False
        versions = self.versions()
        for collector_id in self.deleted:
            used = usedBy(self.cur, collector_id, versions)
            if used:
                QMessageBox.warning(self, self.windowTitle(), tr_msg('A deleted collector type is used by lines ({}); change their type first.').format(
                    '; '.join('{}: {}'.format(v, ', '.join(str(i) for i in ids[:20])) for v, ids in used.items())))
                return False
        try:
            for collector_id in self.deleted:
                deleteCollector(self.cur, collector_id, versions)
            for row, values in enumerate(rows):
                self.table.item(row, 0).setData(256, saveCollector(self.cur, values))
        except CollectorInUse as e:
            QMessageBox.warning(self, self.windowTitle(), tr_msg('The collector type {} is used by lines.').format(e.name))
            return False
        self.deleted = []
        if not self.cur.connection.autocommit:
            self.cur.connection.commit()
        # the type dropdown of the lines form reads the layer line_types
        for layer in QgsProject.instance().mapLayersByName('line_types'):
            layer.reload()
        return True

    def saveAndClose(self):
        if self.save():
            self.accept()

    # ---------------------------------------------------------------- actions
    def fitSelected(self):
        row = self.table.currentRow()
        if row < 0:
            QMessageBox.information(self, self.windowTitle(), tr_msg('Please select a collector type.'))
            return
        if 'kusuda_tsurfmean' not in self.settings:
            QMessageBox.information(self, self.windowTitle(), tr_msg('The fit needs the Kusuda ground temperature settings (modelling settings).'))
            return
        if not self.save():
            return
        collector_id, settings = self.rowId(row), dict(self.settings)
        self.status.setText(tr_msg('Fitting the ground collector {} (up to a minute) ...').format(self.cellText(row, 'name')))

        def fit(cur):
            entry = fitFor(cur, readCollectors(cur)[collector_id], settings)[0]
            cur.connection.commit()
            return entry

        from .representative_periods import startTask
        startTask(self, self.main.config, fit, lambda entry: self.fitted(collector_id, entry), self.fitFailed)

    def fitted(self, collector_id, entry):
        for row in range(self.table.rowCount()):
            if self.rowId(row) == collector_id:
                self.table.item(row, self.keys.index('fit')).setText(fitText(entry))
        self.status.setText(tr_msg('Fitted: {}').format(fitText(entry)))

    def fitFailed(self, message):
        self.status.setText(tr_msg('The fit failed: {}').format(message))

    def meanFromResults(self):
        layer = linesLayer()
        features = layer.selectedFeatures() if layer is not None else []
        if not features:
            QMessageBox.information(self, self.windowTitle(), tr_msg('Please select collector lines in the layer lines.'))
            return
        try:
            values = setMeanFromResults(self.cur, self.main.config['versionName'], sorted(f['id'] for f in features))
        except Exception:
            QgsMessageLog.logMessage(traceback.format_exc(), 'Districts', MessageCritical)
            self.status.setText(traceback.format_exc().splitlines()[-1])
            return
        if not values:
            self.status.setText(tr_msg('None of the selected lines is a collector line with results (outputs of a simulation loaded).'))
            return
        if not self.cur.connection.autocommit:
            self.cur.connection.commit()
        layer.triggerRepaint()
        self.status.setText(tr_msg('Mean liquid temperature set: {}').format(', '.join('{}: {:.1f} °C'.format(k, v) for k, v in values.items())))
