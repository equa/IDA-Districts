# coding=utf-8
"""Net present value of the loaded version (results tab): the NPV of its simulation results with the inputs of the cost
optimization (scenario, comfort violations, deadband, required loads, stages), computed by the same functions as an
iteration of the cost optimization, saved in versions/<version>/version_npv.json and shown in a report."""
import html
import os
import traceback

from qgis.core import QgsMessageLog
from qgis.PyQt.QtCore import Qt, pyqtSlot
from qgis.PyQt.QtWidgets import (
    QAbstractItemView, QComboBox, QDialog, QDoubleSpinBox, QFormLayout, QHBoxLayout, QHeaderView, QLabel, QPushButton, QTableWidget,
    QTableWidgetItem, QTextEdit, QVBoxLayout,
)
from qgis.gui import QgsCollapsibleGroupBox

from .cost_optimization import carrierPriceNotes, versionNpvRow
from .representative_periods import startTask
from .utility_functions.compat import MessageCritical
from .utility_functions.db import getTemplateNames, getUsedNetworkSubmodels
from .utility_functions.dialog import infoTextEdit
from .utility_functions.files import loadModellingSettings
from .utility_functions.iteration_report import NPV_GROUPS, groupLabel, loadRunParameters, loadVersionNpv, number, openReport, saveVersionNpv
from .utility_functions.network_modes import DEFAULT_DEADBAND_PCT
from .utility_functions.network_stages import stageProblems
from .utility_functions.periods import climateFile
from .utility_functions.reports import fillScenarioCombo
from .utility_functions.required_load import TOLERANCE, ensureRequired, saveRequired
from .utility_functions.stage_table import StageTable, problemText
from .utility_functions.translations import tr_msg

# the defaults of the cost optimization dialog
DEFAULTS = {'price_kh': 0.5, 'tolerance': 0.5, 'price_kwh': 1.0, 'unmet_tolerance': TOLERANCE * 100, 'mode_deadband_pct': DEFAULT_DEADBAND_PCT}


def defaultInputs(config):
    """(inputs, source text): the last calculation of the version, else the last cost optimization run that wrote it"""
    saved = loadVersionNpv(config).get('parms')
    if saved:
        return saved, tr_msg('the last calculation')
    run = loadRunParameters(config, 'cost')
    if run:
        inputs = dict(run)
        # the run's stages name the versions it started from; its result versions are the stages of this version
        versions = run.get('stage_versions') or []
        if len(versions) > 1 and versions[0] == config['versionName']:
            inputs['stages'] = [{'version': v, 'start': s['start']} for v, s in zip(versions, run.get('stages') or [])]
        elif (run.get('stages') or [{}])[0].get('version') != config['versionName']:
            inputs['stages'] = []
        return inputs, tr_msg('the last cost optimization of the version')
    return {}, ''


def notEvaluated(evaluation):
    if evaluation.get('missing'):
        return tr_msg('The results of the version are missing: {}. Simulate the network with these outputs (or run a cost optimization).').format(
            ', '.join(tr_msg(m) for m in evaluation['missing']))
    return tr_msg('The results cover {:.0f} days: neither a year nor a period run with its weeks kept.').format(evaluation.get('short') or 0)


class VersionNpvDialog(QDialog):
    def __init__(self, main):
        super().__init__()
        self.main = main
        self.task = None
        cur, config = main.cur, main.config
        self.setWindowTitle(tr_msg('Net present value of the version') + ' ' + config['versionName'])
        self.resize(760, 760)
        layout = QVBoxLayout(self)
        inputs, source = defaultInputs(config)
        values = dict(DEFAULTS, **{k: v for k, v in inputs.items() if v is not None})
        self.groupBox_info = QgsCollapsibleGroupBox(tr_msg('Description'))
        self.groupBox_info.setObjectName('groupBox_versionNpvInfo')
        self.text_info = infoTextEdit(['version_npv_info'], 220)
        QVBoxLayout(self.groupBox_info).addWidget(self.text_info)
        self.groupBox_info.setCollapsed(True)  # default before the first use, afterwards the saved state
        layout.addWidget(self.groupBox_info)

        form = QFormLayout()
        self.combo_scenario = QComboBox()
        fillScenarioCombo(cur, self.combo_scenario)
        index = self.combo_scenario.findData(values.get('scenario'))
        if index >= 0:
            self.combo_scenario.setCurrentIndex(index)
        self.label_costLinks = QLabel('<a href="scenarios">{}</a> &nbsp; <a href="pipes">{}</a>'.format(
            html.escape(tr_msg('Economic scenarios')), html.escape(tr_msg('Pipe costs'))))
        self.label_costLinks.setTextFormat(Qt.TextFormat.RichText)
        self.label_costLinks.linkActivated.connect(self.onCostLink)
        scenario = QHBoxLayout()
        scenario.addWidget(self.combo_scenario, 1)
        scenario.addWidget(self.label_costLinks)
        form.addRow(tr_msg('Scenario'), scenario)
        self.combo_submodel = QComboBox()
        self.combo_submodel.addItems(getUsedNetworkSubmodels(cur, config))
        if values.get('submodel'):
            self.combo_submodel.setCurrentText(values['submodel'])
        form.addRow(tr_msg('Submodel'), self.combo_submodel)
        self.spin_price_kh = self.spin(0, 1000, values['price_kh'])
        self.spin_tolerance = self.spin(0, 5, values['tolerance'])
        self.spin_price_kwh = self.spin(0, 1000, values['price_kwh'])
        self.spin_tolerance_kwh = self.spin(0, 50, values['unmet_tolerance'])
        self.spin_tolerance_kwh.setToolTip(tr_msg('Unmet load counts only above this share of the required load'))
        penalties = QHBoxLayout()
        for widget in (QLabel(tr_msg('€/Kh')), self.spin_price_kh, QLabel(tr_msg('tolerance [K]')), self.spin_tolerance, QLabel(tr_msg('€/kWh unmet')),
                       self.spin_price_kwh, QLabel(tr_msg('tolerance [%]')), self.spin_tolerance_kwh):
            penalties.addWidget(widget)
        form.addRow(tr_msg('Comfort violations'), penalties)
        self.spin_deadband = self.spin(0, 50, values['mode_deadband_pct'])
        self.spin_deadband.setSingleStep(1)
        self.spin_deadband.setSuffix(' %')
        self.spin_deadband.setToolTip(tr_msg('Heating or cooling per hour and supply/return pair from the heat the plants put into the network: '
                                             'losses are priced with the heat price when heating, with the cold price when cooling.'))
        form.addRow(tr_msg('Deadband heating/cooling'), self.spin_deadband)
        box_settings = QgsCollapsibleGroupBox(tr_msg('Inputs'))
        box_settings.setLayout(form)
        layout.addWidget(box_settings)
        label_source = QLabel(tr_msg('Inputs as the cost optimization takes them; filled from {}.').format(source) if source else
                              tr_msg('Inputs as the cost optimization takes them (its defaults).'))
        label_source.setWordWrap(True)
        layout.addWidget(label_source)

        try:
            cur.execute('SELECT name FROM public.versionhandling ORDER BY id;')
            versions = [row['name'] for row in cur.fetchall()]
        except Exception:
            versions = [config['versionName']]
        self.stage_table = StageTable(versions, config['versionName'], tr_msg(
            'A network built in stages: the loaded version is stage 1 (year 0), each further stage a child version with its own results, '
            'from its start year. One row: this version only.'))
        stages = inputs.get('stages') or []
        if len(stages) > 1 and stages[0]['version'] == config['versionName']:
            self.stage_table.setStages(stages)
        layout.addWidget(self.section(tr_msg('Stages'), self.stage_table, collapsed=len(self.stage_table.stages()) < 2))
        self.table_required = QTableWidget(0, 4)
        self.table_required.setHorizontalHeaderLabels([tr_msg('Template'), tr_msg('Column'), tr_msg('Unit'), tr_msg('Mode')])
        self.table_required.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Interactive)
        self.table_required.setMaximumHeight(120)
        self.fillRequired()
        layout.addWidget(self.section(tr_msg('Required load of source-file customers (column of the source file)'), self.table_required, collapsed=True))

        self.table_result = QTableWidget(0, 2)
        self.table_result.verticalHeader().setVisible(False)
        self.table_result.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.table_result.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.ResizeToContents)
        layout.addWidget(self.table_result, 1)
        self.log_edit = QTextEdit()
        self.log_edit.setReadOnly(True)
        self.log_edit.setMaximumHeight(110)
        layout.addWidget(self.log_edit)
        buttons = QHBoxLayout()
        self.btn_calculate = QPushButton(tr_msg('Calculate'))
        self.btn_calculate.setToolTip(tr_msg('The net present value of the simulation results of the version with these inputs; nothing is simulated.'))
        self.btn_report = QPushButton(tr_msg('Report'))
        self.btn_report.setToolTip(tr_msg('HTML report of the last calculation: inputs incl. the economic scenario, the parts and the terms of the '
                                          'net present value, opened in the browser.'))
        self.btn_close = QPushButton(tr_msg('Close'))
        for button in (self.btn_calculate, self.btn_report, self.btn_close):
            buttons.addWidget(button)
        layout.addLayout(buttons)
        self.btn_calculate.clicked.connect(self.calculate)
        self.btn_report.clicked.connect(lambda: openReport(self, self.main.cur, self.main.config, 'npv'))
        self.btn_close.clicked.connect(self.close)
        saved = loadVersionNpv(config)
        if saved:
            self.showRow(saved['row'])
            self.log(tr_msg('Calculated {}.').format(saved.get('saved', '')))
        self.btn_report.setEnabled(bool(saved))

    @staticmethod
    def spin(low, high, value):
        spin = QDoubleSpinBox()
        spin.setRange(low, high)
        spin.setValue(float(value))
        return spin

    @staticmethod
    def section(title, widget, collapsed=False):
        box = QgsCollapsibleGroupBox(title)
        box.setSaveCollapsedState(False)
        inner = QVBoxLayout(box)
        inner.setContentsMargins(4, 4, 4, 4)
        inner.addWidget(widget)
        box.setCollapsed(collapsed)
        return box

    def log(self, message):
        self.log_edit.append(message)

    def onCostLink(self, link):
        if link == 'scenarios':
            self.main.manageEconomicScenarios()
            dialog = getattr(self.main, 'dlg_economicScenarios', None)
            if dialog is not None:
                dialog.finished.connect(lambda _: self.refreshScenarios())
        elif link == 'pipes':
            self.main.managePipes()

    def refreshScenarios(self):
        current = self.combo_scenario.currentData()
        fillScenarioCombo(self.main.cur, self.combo_scenario)
        index = self.combo_scenario.findData(current)
        if index >= 0:
            self.combo_scenario.setCurrentIndex(index)

    def fillRequired(self):
        entries = ensureRequired(self.main.config, getTemplateNames(self.main.cur, 'customer', seperator='_'))
        self.table_required.setRowCount(0)
        for entry in entries:
            row = self.table_required.rowCount()
            self.table_required.insertRow(row)
            for col, key in enumerate(('template', 'column', 'unit', 'mode')):
                self.table_required.setItem(row, col, QTableWidgetItem(str(entry[key])))

    def requiredEntries(self):
        entries = []
        for row in range(self.table_required.rowCount()):
            text = [self.table_required.item(row, col).text() if self.table_required.item(row, col) else '' for col in range(4)]
            try:
                entries.append({'template': text[0], 'column': int(text[1]), 'unit': text[2] or 'W', 'mode': text[3] or 'heating'})
            except ValueError:
                continue
        return entries

    def parameters(self):
        """the inputs under the keys of the cost optimization's run parameters"""
        return {'scenario': self.combo_scenario.currentData(), 'submodel': self.combo_submodel.currentText(),
                'price_kh': self.spin_price_kh.value(), 'tolerance': self.spin_tolerance.value(), 'price_kwh': self.spin_price_kwh.value(),
                'unmet_tolerance': self.spin_tolerance_kwh.value(), 'mode_deadband_pct': self.spin_deadband.value(),
                'stages': self.stage_table.stages()}

    # ---------------------------------------------------------------- calculation
    def calculate(self):
        """False when refused"""
        p = self.parameters()
        config = dict(self.main.config)
        self.log_edit.clear()
        if p['scenario'] is None or not p['submodel']:
            self.log(tr_msg('Choose a scenario and a submodel.'))
            return False
        stages = [{'version': s['version'], 'start': int(s['start'])} for s in p['stages']] if len(p['stages']) > 1 else None
        if stages:
            try:
                problems = stageProblems(self.main.cur, stages)
            except Exception:
                QgsMessageLog.logMessage(traceback.format_exc(), 'Districts', MessageCritical)
                problems = [('error', traceback.format_exc().splitlines()[-1])]
            if problems:
                for problem in problems:
                    self.log(problemText(problem))
                return False
        required = self.requiredEntries()
        try:
            saveRequired(config, required)
            settings = dict(loadModellingSettings(self.main.plugin_dir, config), mode_deadband_pct=p['mode_deadband_pct'])
        except Exception:
            QgsMessageLog.logMessage(traceback.format_exc(), 'Districts', MessageCritical)
            self.log(tr_msg('Error') + ': ' + traceback.format_exc().splitlines()[-1])
            return False
        for note in carrierPriceNotes(self.main.cur, config, p):
            self.log(note)
        prices = os.path.join(config['pathProjects'] + config['projectName'], 'prices')

        def work(cur):
            climates = {}
            for stage in stages or []:
                try:
                    climates[stage['version']] = climateFile(dict(config, versionName=stage['version']), cur)
                except Exception:
                    # only shown in the report's stage table
                    climates[stage['version']] = ''
            return versionNpvRow(cur, config, p, settings, prices, required, stages, climates)

        self.parms = dict(p, scenario_name=self.combo_scenario.currentText())
        self.config = config
        self.btn_calculate.setEnabled(False)
        self.log(tr_msg('Evaluating the results ...'))
        startTask(self, config, work, self.onCalculated, self.onFailed)
        return True

    @pyqtSlot(object)
    def onCalculated(self, row):
        self.btn_calculate.setEnabled(True)
        if 'npv' not in row:
            self.log(notEvaluated(row))
            return
        try:
            saveVersionNpv(self.config, self.parms, row)
        except Exception:
            QgsMessageLog.logMessage(traceback.format_exc(), 'Districts', MessageCritical)
            self.log(tr_msg('The result could not be saved: ') + traceback.format_exc().splitlines()[-1])
        self.showRow(row)
        self.btn_report.setEnabled(True)
        self.log(tr_msg('Net present value: {}').format(number(row['npv']) + ' €'))
        if row.get('deficit_customers'):
            self.log(tr_msg('{} customers with comfort violations: {}').format(len(row['deficit_customers']), ', '.join(
                str(c) for c in row['deficit_customers'][:20]) + (' ...' if len(row['deficit_customers']) > 20 else '')))

    @pyqtSlot(str)
    def onFailed(self, message):
        self.btn_calculate.setEnabled(True)
        self.log(tr_msg('Error') + ': ' + message)

    def showRow(self, row):
        """the parts of the NPV, one column per stage and the total"""
        stages = row.get('stages') or []
        headers = [tr_msg('Part')] + [tr_msg('Stage {}').format(k) for k in range(1, len(stages) + 1)] + [tr_msg('Value [€]') if not stages else tr_msg('Total')]
        groups = [g for g in NPV_GROUPS if row['split'].get(g)]
        lines = [(groupLabel(g), [s['split'].get(g, 0.0) for s in stages] + [row['split'][g]]) for g in groups]
        lines.append((tr_msg('Net present value'), [s['npv'] for s in stages] + [row['npv']]))
        self.table_result.clear()
        self.table_result.setColumnCount(len(headers))
        self.table_result.setHorizontalHeaderLabels(headers)
        self.table_result.setRowCount(len(lines))
        for r, (label, values) in enumerate(lines):
            self.table_result.setItem(r, 0, QTableWidgetItem(label))
            for c, value in enumerate(values, 1):
                item = QTableWidgetItem(number(value))
                item.setTextAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
                if r == len(lines) - 1:
                    font = item.font()
                    font.setBold(True)
                    item.setFont(font)
                self.table_result.setItem(r, c, item)
