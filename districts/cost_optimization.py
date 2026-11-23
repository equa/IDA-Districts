# coding=utf-8
"""Dialog "Cost optimization" and its run (OpenSpec change cost-optimization): iteration 0 simulates the version's
pipes as reference; each iteration changes every line with a negative model ΔNPV by one size of its series, writes
the pipes, builds the network model and simulates the periods (PeriodRun); the run ends without improvement, on
oscillation, without an improving step or at max. iterations and restores the best simulated iteration."""
import glob
import html
import json
import os
import traceback

import psycopg2.extras

from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg
from matplotlib.figure import Figure
from qgis.PyQt.QtCore import QObject, QSize, Qt, QThreadPool, QTimer, pyqtSlot
from qgis.PyQt.QtGui import QColor, QGuiApplication
from qgis.PyQt.QtWidgets import (
    QAbstractItemView, QCheckBox, QComboBox, QDialog, QDoubleSpinBox, QFormLayout, QFrame, QHBoxLayout, QHeaderView, QLabel, QLineEdit,
    QProgressBar, QPushButton, QRadioButton, QScrollArea, QSpinBox, QTableWidget, QTableWidgetItem, QTabWidget, QTextEdit, QVBoxLayout,
    QWidget,
)
from qgis.core import QgsMessageLog
from qgis.gui import QgsCollapsibleGroupBox
from qgis.utils import iface

from .representative_periods import NEEDED_OUTPUTS, PeriodRun, PeriodsWidget, startTask
from .utility_functions.compat import MessageCritical, MessageInfo, MessageWarning
from .utility_functions.cost_model import DP_SPEZ_MAX, V_MAX
from .utility_functions.cost_model_data import buildModel, checkSources, series
from .utility_functions.cost_optimization_layers import iterationPath, loadCostIterations, removeCostLayers, showCostIterations
from .utility_functions.db import getUsedNetworkSubmodels
from .utility_functions.dialog import infoTextEdit
from .utility_functions.dynamic_sizing_results import loadIterations
from .utility_functions.files import loadModellingSettings, loadRequestedOutputs
from .utility_functions.iteration_report import ITERATION_HEADERS, iterationTableRows, loadRunParameters, npvBars, openReport, saveRunParameters
from .utility_functions.hydraulic_balancing import createChildVersion, getOrCreatePipeBundles, getPipeBundles
from .utility_functions.network_economics import evaluateVersion, resultTables
from .utility_functions.economics import npvTerms, presentValueFactor, stageYears
from .utility_functions.network_modes import DEFAULT_DEADBAND_PCT
from .utility_functions.cost_model import stagedStep
from .utility_functions.economic_data import loadScenario
from .utility_functions.model_checks import SEVERITIES, checkVersions, findingLine
from .utility_functions.network_stages import inheritPipes, linkStages, stageLinks, stageProblems, stageRoots, stagesNpv, versionTriggers, writeBundles
from .utility_functions.periods import climateFile, readClimate
from .utility_functions.set_pipes import SetPipes, costIterationPipes
from .utility_functions.stage_table import StageTable, problemText
from .utility_functions.penalties import customerValues, deficitCustomers, penaltyCost, penaltyNpv
from .utility_functions.pair_widgets import PairTable
from .utility_functions.pipe_pairs import getPlantConnections, networkSequences, suggestPairs
from .utility_functions.protected_lines import loadProtectedLines, networkLineIds, saveProtectedLines
from .utility_functions.protected_lines_widget import ProtectedLinesWidget
from .utility_functions.reports import fillScenarioCombo
from .utility_functions.required_load import TOLERANCE, ensureRequired, saveRequired
from .utility_functions.translations import tr_msg
from .utility_functions.utility import write_plugin_settings
from .utility_functions.workers import WorkerLoadVersion

NO_IMPROVEMENT = 2
# mdot_ep: the heat flows of the plants give the heating or cooling mode per step (network_modes)
# energy_ep / energy_c: the energy the plants and customers buy (OpenSpec plant-energy-costs)
OPTIMIZATION_OUTPUTS = NEEDED_OUTPUTS + ('ppump_c', 'troom_c', 'power_c', 'mdot_lines', 'mdot_ep', 'energy_ep', 'energy_c')
# the checkbox of each output in the requested outputs dialog
OUTPUT_CHECKBOXES = {'ppump_ep': 'checkBoxPlantPumpPower', 'ppump_c': 'checkBoxSubstationPumpPower', 'temp_lines': 'checkBoxTempPipe',
                     'qamb_lines': 'checkBoxQambPipe', 'temp_ep': 'checkBoxPlantConnTemp', 'troom_c': 'checkBoxSubstationTair',
                     'power_c': 'checkBoxSubstationPower', 'mdot_lines': 'checkBoxMdotNode', 'mdot_ep': 'checkBoxPlantMassflow',
                     'energy_ep': 'checkBoxPlantEnergy', 'energy_c': 'checkBoxSubstationEnergy'}
BALANCING_LINK = 'balancing'


def missingOutputs(plugin_dir, config):
    outputs = loadRequestedOutputs(plugin_dir, config) or {}
    return [key for key in OPTIMIZATION_OUTPUTS if not outputs.get(key)]


def idList(ids, n=20):
    return ', '.join(str(i) for i in ids[:n]) + (' ...' if len(ids) > n else '')


def skippedRules(parms):
    """rules of the input check the dialog does itself (pairs, scenario) or the run fixes (outputs switched on)"""
    skip = {'cost_pairs', 'economic_scenario'}
    if parms.get('set_outputs'):
        skip.add('cost_outputs')
    return skip


def inputDataMessages(result):
    """(errors, warnings and infos) as log lines of checkVersions"""
    lines = {severity: [] for severity in SEVERITIES}
    for f in result['findings']:
        lines[f['severity']].append(findingLine(f, result['versions']))
    for version, errors in result['errors'].items():
        for rule, text in errors.items():
            lines['warning'].append(tr_msg('Check {} of version {} failed: {}').format(rule, version, text))
    return lines['error'], lines['warning'] + lines['info']


def deleteIterationFiles(config):
    for path in glob.glob(iterationPath(config, '*')):
        os.remove(path)


def lineState(cur, schema):
    cur.execute('SELECT id, pipe_bundle_type_id AS bid FROM "{}".lines;'.format(schema))  # nosec B608
    return {row['id']: row['bid'] for row in cur.fetchall()}


def penaltyValues(cur, config, required, submodel, tolerance, unmet_tolerance):
    """{cid: (Kh, unmet kWh)} per year of the checked iteration (worker thread: only the given cursor)"""
    check = checkSources(cur, config)
    if not check:
        return {}
    sources, times, w, hours, _ = check
    index = {t: k for k, t in enumerate(times)}
    schema = config['versionName']
    data = {var: series(cur, schema, sources('customer_s_' + var), '$' + var, times, index) for var in ('troom', 'tset', 'hcmode')}
    power = {}
    for table in resultTables(cur, schema, 'customer_s_power$'):
        for cid, arr in series(cur, schema, sources(table), '$power', times, index).items():
            power[cid] = power.get(cid, 0) + arr
    data['power'] = power
    cur.execute("""SELECT c.id, t.template::text || '_' || t.template_name AS t_name FROM "{}".customers c, customer_templates t
        WHERE c.template = t.template;""".format(schema))  # nosec B608
    templates = {row['id']: row['t_name'] for row in cur.fetchall()}
    return customerValues(data, hours, w, required, templates, config, submodel, tolerance, unmet_tolerance)


def npvRecord(evaluation, yearly_penalty, penalty_npv):
    """the terms of the NPV of an iteration for its report, saved at run time: the scenario may change afterwards"""
    scenario = evaluation['scenario']
    sc = scenario['scenario']
    items = [dict(item, kind=key[0]) for key, item in evaluation['items'].items()]
    items.append(dict(evaluation['pump_item'], kind='pumps', power_kw=evaluation['pump_kw']))
    years = range(1, int(sc.get('period_a') or 0) + 1)
    factors = {group: presentValueFactor(scenario, group, years) for group in ('electricity', 'heat', 'cold', 'maintenance', 'fuel', 'purchased_heat')}
    factors['penalties'] = penaltyNpv(1.0, float(sc.get('interest_pct') or 0), len(years))
    basis = evaluation.get('energy_basis')
    energy_basis = None
    if basis:
        # the energy the plants and customers bought, for the report (plant-energy-costs D7)
        energy_basis = {key: basis[key] for key in ('boundary', 'losses', 'curve_hours', 'threshold_pct')}
        energy_basis.update({'kwh': basis['costs']['kwh'], 'info': basis['costs']['info'], 'no_price': basis['costs']['no_price'],
                             'delivered': basis['costs'].get('delivered', {}),
                             'features': basis['costs']['features'], 'marginal_hours': {str(k): v for k, v in basis['marginal_hours'].items()}})
    return {'terms': npvTerms(scenario, items, evaluation.get('npv_yearly', evaluation['costs']), evaluation.get('by_carrier')),
            'energy': evaluation['energy'], 'yearly_penalty': yearly_penalty, 'energy_basis': energy_basis,
            'penalties': penalty_npv, 'factors': factors, 'interest_pct': float(sc.get('interest_pct') or 0), 'period_a': len(years),
            'residual_value': bool(sc.get('residual_value')), 'el_price': float((scenario.get('groups', {}).get('electricity') or {}).get('start_price') or 0),
            'modes': evaluation.get('modes') or {}}


def modelStep(cur, config, parms, settings, prices, no_smaller, stages=None):
    """the cost model of the checked iteration, its step and the new pipes written into the version (worker thread):
    {'steps', 'rejected', 'state', 'n_changed'}, or None without a model. stages: [{'version', 'start'}] of a network
    built in stages (network-stages D2, D4): a model per stage, the step over all, written into every stage containing
    the line; the state is the last stage's (it holds every line)."""
    stages = stages or [{'version': config['versionName'], 'start': 0}]
    if len(stages) > 1:
        return modelStepStages(cur, config, parms, settings, prices, no_smaller, stages)
    period = int((loadScenario(cur, parms['scenario']) or {'scenario': {}})['scenario'].get('period_a') or 0)
    ranges = stageYears([int(s['start']) for s in stages], period) if len(stages) > 1 else [None]
    models = []
    for stage, operating in zip(stages, ranges):
        model = buildModel(cur, dict(config, versionName=stage['version']), parms['scenario'], parms['pairs'], settings, profile_dir=prices)
        if model is None:
            return None
        model.dp_spez_max, model.v_max = parms['dp_spez_max'], parms['v_max']
        model.start_year, model.operating = int(stage['start']), operating
        for lid in no_smaller:
            if lid in model.lines:
                model.lines[lid]['no_smaller'] = True
        models.append(model)
    model = models[-1]
    chosen, rejected = stagedStep(models)
    steps = []
    for lid, c in sorted(chosen.items()):
        before = {seq: model.lines[lid]['pipes'][seq] for seq in c['pipes']}
        seq, pid = next(iter(c['pipes'].items()))
        steps.append({'line': lid, 'before': before, 'after': c['pipes'], 'dnpv': c['dnpv'], 'split': c['split'],
                      'larger': model.catalog[pid]['d'] > model.catalog[before[seq]]['d']})
    result = {'steps': steps, 'rejected': rejected, 'state': None, 'n_changed': 0}
    if not chosen:
        return result
    schema = stages[-1]['version']
    current = lineState(cur, schema)
    bundles = getPipeBundles(cur)
    pipes = {lid: {**bundles.get(current[lid], {}), **c['pipes']} for lid, c in chosen.items()}
    new_bundles, _ = getOrCreatePipeBundles(cur, {lid: current[lid] for lid in chosen}, pipes)
    for stage in stages:
        # a line keeps the same pipes in every stage containing it
        psycopg2.extras.execute_values(cur, 'UPDATE "{}".lines l SET pipe_bundle_type_id = v.bid FROM (VALUES %s) AS v(id, bid) WHERE l.id = v.id;'.format(  # nosec B608
            stage['version']), sorted(new_bundles.items()))
    result['state'] = tuple(sorted(lineState(cur, schema).items()))
    result['n_changed'] = len(new_bundles)
    return result


def modelStepStages(cur, config, parms, settings, prices, no_smaller, stages):
    """the step of a network built in stages (network-stages D2, D7, D8): a model per stage with the roots of its lines,
    the step over the line groups, the new pipes written into the root and all its segments of every stage (the update
    trigger of the version handling disabled); the state and the state of each stage"""
    versions = [s['version'] for s in stages]
    roots = stageRoots(cur, versions)
    period = int((loadScenario(cur, parms['scenario']) or {'scenario': {}})['scenario'].get('period_a') or 0)
    models = []
    for k, (stage, operating) in enumerate(zip(stages, stageYears([int(s['start']) for s in stages], period))):
        model = buildModel(cur, dict(config, versionName=stage['version']), parms['scenario'], parms['pairs'], settings, profile_dir=prices)
        if model is None:
            return None
        model.dp_spez_max, model.v_max = parms['dp_spez_max'], parms['v_max']
        model.start_year, model.operating, model.root = int(stage['start']), operating, roots[k]
        for lid in model.lines:
            # no_smaller holds the roots' line IDs of the stage they first appear in (stage 1: the loaded version)
            if roots[k][lid][1] in no_smaller and roots[k][lid][0] == 0:
                model.lines[lid]['no_smaller'] = True
        models.append(model)
    chosen, rejected = stagedStep(models)
    steps = []
    for root, c in sorted(chosen.items()):
        line = models[root[0]].lines[root[1]]
        before = {seq: line['pipes'][seq] for seq in c['pipes']}
        seq, pid = next(iter(c['pipes'].items()))
        steps.append({'line': root[1], 'stage': root[0] + 1, 'before': before, 'after': c['pipes'], 'dnpv': c['dnpv'], 'split': c['split'],
                      'larger': models[0].catalog[pid]['d'] > models[0].catalog[before[seq]]['d']})
    result: dict = {'steps': steps, 'rejected': {root[1] if root[0] == 0 else '{}:{}'.format(root[0] + 1, root[1]): reasons for root, reasons in rejected.items()},
              'state': None, 'n_changed': 0}
    if not chosen:
        return result
    bundles = getPipeBundles(cur)
    stage_states = {}
    for k, version in enumerate(versions):
        current = lineState(cur, version)
        lids = [lid for lid, root in roots[k].items() if root in chosen]
        pipes = {lid: {**bundles.get(current[lid], {}), **chosen[roots[k][lid]]['pipes']} for lid in lids}
        new_bundles, _ = getOrCreatePipeBundles(cur, {lid: current[lid] for lid in lids}, pipes)
        writeBundles(cur, version, new_bundles)
        bundles = getPipeBundles(cur)
        result['n_changed'] += len(new_bundles)
        stage_states[version] = lineState(cur, version)
    result['stage_states'] = stage_states
    result['state'] = tuple((version, tuple(sorted(state.items()))) for version, state in stage_states.items())
    return result


class CostOptimizationDialog(QDialog):
    def __init__(self, main):
        super().__init__()
        self.main = main
        self.process_running = False
        self.run = None
        cur, config = main.cur, main.config
        self.setWindowTitle(tr_msg('Cost optimization'))
        self.resize(1100, 850)
        layout = QVBoxLayout(self)
        form = QFormLayout()
        self.combo_scenario = QComboBox()
        fillScenarioCombo(cur, self.combo_scenario)
        self.combo_network = QComboBox()
        cur.execute('SELECT network FROM "{}".lines GROUP BY network ORDER BY network;'.format(config['versionName']))  # nosec B608
        self.combo_network.addItems([str(row['network']) for row in cur.fetchall()])
        self.combo_submodel = QComboBox()
        self.combo_submodel.addItems(getUsedNetworkSubmodels(cur, config))
        self.pair_table = PairTable(tr_msg('Supply and return pipe sequence of every circuit, suggested from the connections of the energy plants; '
                                           'heating and cooling in the same trench are two rows'))
        self.spin_price_kh = QDoubleSpinBox()
        self.spin_price_kh.setRange(0, 1000)
        self.spin_price_kh.setValue(0.5)
        self.spin_tolerance = QDoubleSpinBox()
        self.spin_tolerance.setRange(0, 5)
        self.spin_tolerance.setValue(0.5)
        self.spin_price_kwh = QDoubleSpinBox()
        self.spin_price_kwh.setRange(0, 1000)
        self.spin_price_kwh.setValue(1.0)
        self.spin_tolerance_kwh = QDoubleSpinBox()
        self.spin_tolerance_kwh.setRange(0, 50)
        self.spin_tolerance_kwh.setValue(TOLERANCE * 100)
        self.spin_tolerance_kwh.setToolTip(tr_msg('Unmet load counts only above this share of the required load'))
        self.spin_dp_max = QDoubleSpinBox()
        self.spin_dp_max.setRange(10, 5000)
        self.spin_dp_max.setDecimals(0)
        self.spin_dp_max.setSingleStep(50)
        self.spin_dp_max.setValue(DP_SPEZ_MAX)
        self.spin_v_max = QDoubleSpinBox()
        self.spin_v_max.setRange(0.1, 10)
        self.spin_v_max.setSingleStep(0.1)
        self.spin_v_max.setValue(V_MAX)
        self.spin_iter = QSpinBox()
        self.spin_iter.setRange(1, 100)
        self.spin_iter.setValue(10)
        self.spin_deadband = QDoubleSpinBox()
        self.spin_deadband.setRange(0, 50)
        self.spin_deadband.setSingleStep(1)
        self.spin_deadband.setValue(DEFAULT_DEADBAND_PCT)
        self.spin_deadband.setSuffix(' %')
        self.spin_deadband.setToolTip(tr_msg('Heating or cooling per hour and supply/return pair from the heat the plants put into the network '
                                             '(results mdot_ep, temp_ep): the mode changes only outside a band of this share of the range '
                                             'between the largest heating and the largest cooling flow. Losses are priced with the heat price '
                                             'when heating, with the cold price when cooling.'))
        self.rbtn_new = QRadioButton(tr_msg('New child version'))
        self.rbtn_override = QRadioButton(tr_msg('Override the pipes of the loaded version'))
        self.rbtn_new.setChecked(True)
        self.edit_version = QLineEdit(config['versionName'] + '_costopt')
        self.check_outputs = QCheckBox(tr_msg('Switch on the requested outputs the optimization needs at the start'))
        self.check_outputs.setToolTip(tr_msg('Pump power of the customers and energy plants, temperatures and losses of the lines, plant temperatures, '
                                             'room temperatures and power of the customers; written into the templates of the project, '
                                             'the first run invokes the features again'))
        self.check_outputs.setChecked(True)
        penalties = QHBoxLayout()
        for widget in (QLabel(tr_msg('€/Kh')), self.spin_price_kh, QLabel(tr_msg('tolerance [K]')), self.spin_tolerance, QLabel(tr_msg('€/kWh unmet')), self.spin_price_kwh,
                       QLabel(tr_msg('tolerance [%]')), self.spin_tolerance_kwh):
            penalties.addWidget(widget)
        limits = QHBoxLayout()
        for widget in (QLabel(tr_msg('max. specific pressure loss [Pa/m]')), self.spin_dp_max, QLabel(tr_msg('max. velocity [m/s]')), self.spin_v_max):
            limits.addWidget(widget)
        limits.addStretch()
        version = QHBoxLayout()
        for widget in (self.rbtn_new, self.edit_version, self.rbtn_override):
            version.addWidget(widget)
        # the cost data of the run: scenarios and the pipe catalog are edited in their own dialogs
        self.label_costLinks = QLabel('<a href="scenarios">{}</a> &nbsp; <a href="pipes">{}</a>'.format(
            html.escape(tr_msg('Economic scenarios')), html.escape(tr_msg('Pipe costs'))))
        self.label_costLinks.setTextFormat(Qt.TextFormat.RichText)
        self.label_costLinks.setToolTip(tr_msg('Prices, interest, period, electricity profile and trench costs of the scenarios; '
                                               'costs, maintenance, lifetime and max. pressure of the pipes'))
        self.label_costLinks.linkActivated.connect(self.onCostLink)
        scenario = QHBoxLayout()
        scenario.addWidget(self.combo_scenario, 1)
        scenario.addWidget(self.label_costLinks)
        form.addRow(tr_msg('Scenario'), scenario)
        form.addRow(tr_msg('Network'), self.combo_network)
        form.addRow(tr_msg('Submodel'), self.combo_submodel)
        form.addRow(tr_msg('Pairs'), self.pair_table)
        form.addRow(tr_msg('Smaller pipe at peak flow'), limits)
        form.addRow(tr_msg('Comfort violations'), penalties)
        form.addRow(tr_msg('Deadband heating/cooling'), self.spin_deadband)
        form.addRow(tr_msg('Max. iterations'), self.spin_iter)
        form.addRow(tr_msg('Outputs'), self.check_outputs)
        form.addRow(tr_msg('Version'), version)
        self.groupBox_info = QgsCollapsibleGroupBox(tr_msg('Description'))
        self.groupBox_info.setObjectName('groupBox_costOptimizationInfo')
        self.text_info = infoTextEdit(['cost_optimization_info'], 260)
        QVBoxLayout(self.groupBox_info).addWidget(self.text_info)
        self.groupBox_info.setCollapsed(True)  # default before the first use, afterwards the saved state
        layout.addWidget(self.groupBox_info)
        self.label_hints = QLabel()
        self.label_hints.setWordWrap(True)
        self.label_hints.setTextFormat(Qt.TextFormat.RichText)
        self.label_hints.linkActivated.connect(self.onHintLink)
        layout.addWidget(self.label_hints)
        # the sections scroll, so the progress bar and the buttons stay visible on any screen
        sections = QWidget()
        outer = layout
        layout = QVBoxLayout(sections)
        layout.setContentsMargins(0, 0, 0, 0)
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.Shape.NoFrame)
        scroll.setWidget(sections)
        outer.addWidget(scroll, 1)
        self.box_settings = self.section(tr_msg('Settings'), form)
        layout.addWidget(self.box_settings)
        self.log_edit = QTextEdit()
        self.log_edit.setReadOnly(True)
        # the weeks shown here are the weeks every check simulates
        self.periods = PeriodsWidget(main, self.log)
        self.box_periods = self.section(tr_msg('Periods'), self.periods)
        layout.addWidget(self.box_periods)
        self.protected_lines = ProtectedLinesWidget(tr_msg('Line IDs whose pipes the optimization never changes; their costs and pressure losses still count. '
                                                           'The same list as in the hydraulic balancing, saved with the version at the start.'))
        try:
            self.protected_lines.setLines(loadProtectedLines(config))
        except Exception:
            QgsMessageLog.logMessage(traceback.format_exc(), 'Districts', MessageCritical)
        self.box_protected = self.section(tr_msg('Protected lines'), self.protected_lines, collapsed=not self.protected_lines.texts())
        layout.addWidget(self.box_protected)
        try:
            main.cur.execute('SELECT name FROM public.versionhandling ORDER BY id;')
            versions = [row['name'] for row in main.cur.fetchall()]
        except Exception:
            versions = [config['versionName']]
        self.stage_table = StageTable(versions, config['versionName'], tr_msg(
            'A network built in stages: the loaded version is stage 1 (year 0), each further stage a child version with more customers, '
            'plants and lines, from its start year. The pipes of a line are sized for all stages it exists in. One row: this version only.'))
        self.box_stages = self.section(tr_msg('Stages'), self.stage_table, collapsed=True)
        layout.addWidget(self.box_stages)
        self.table_required = QTableWidget(0, 4)
        self.table_required.setHorizontalHeaderLabels([tr_msg('Template'), tr_msg('Column'), tr_msg('Unit'), tr_msg('Mode')])
        self.table_required.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Interactive)
        self.table_required.setMaximumHeight(120)
        self.box_required = self.section(tr_msg('Required load of source-file customers (column of the source file)'), self.table_required, collapsed=True)
        layout.addWidget(self.box_required)
        self.table_iterations = QTableWidget(0, 9)
        self.table_iterations.setHorizontalHeaderLabels([tr_msg(h) for h in ITERATION_HEADERS])
        self.table_iterations.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Interactive)
        self.table_iterations.verticalHeader().setVisible(False)
        self.table_iterations.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.table_iterations.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.table_iterations.setToolTip(tr_msg('Iterations of the last run in the loaded version. Select one or more iterations and show them on the map '
                                                '(inner diameters, lines changed for the iteration, customers with a new deficit).'))
        self.table_iterations.itemDoubleClicked.connect(lambda item: self.showSelectedIterations())
        self.btn_showIterations = QPushButton(tr_msg('Show selected iterations on the map'))
        self.btn_removeLayers = QPushButton(tr_msg('Remove the iteration layers'))
        self.btn_reload = QPushButton(tr_msg('Reload'))
        self.btn_report = QPushButton(tr_msg('Report'))
        self.btn_report.setToolTip(tr_msg('HTML report of the iterations of the loaded version: inputs incl. the economic scenario, iteration '
                                          'tables, maps and the cost analysis, opened in the browser.'))
        self.btn_report.clicked.connect(lambda: openReport(self, self.main.cur, self.main.config, 'cost'))
        self.btn_setPipes = QPushButton(tr_msg('Set pipes'))
        self.btn_setPipes.setToolTip(tr_msg('The pipes simulated in the selected iteration into a new child version or into this version; '
                                            'nothing is simulated.'))
        self.btn_setPipes.clicked.connect(self.setSelectedPipes)
        self.btn_showIterations.clicked.connect(self.showSelectedIterations)
        self.btn_removeLayers.clicked.connect(lambda: removeCostLayers())
        self.btn_reload.clicked.connect(self.loadIterationTable)
        tab_iterations = QWidget()
        inner = QVBoxLayout(tab_iterations)
        inner.addWidget(self.table_iterations)
        row_buttons = QHBoxLayout()
        for button in (self.btn_showIterations, self.btn_removeLayers, self.btn_reload, self.btn_report, self.btn_setPipes):
            row_buttons.addWidget(button)
        inner.addLayout(row_buttons)
        self.figure = Figure(figsize=(9, 4))
        self.canvas = _Canvas(self.figure)
        self.canvas.setMinimumHeight(250)
        results = QTabWidget()
        self.results_tabs = results
        results.addTab(tab_iterations, tr_msg('Iterations'))
        results.addTab(self.canvas, tr_msg('Net present value'))
        results.addTab(self.log_edit, tr_msg('Log'))
        results.setMinimumHeight(330)
        self.tabs_results = results
        # opened when a run starts; before, the settings and periods have the room
        self.box_results = self.section(tr_msg('Results'), results, collapsed=True)
        layout.addWidget(self.box_results, 1)
        layout.addStretch()
        self.progress = QProgressBar()
        outer.addWidget(self.progress)
        buttons = QHBoxLayout()
        self.btn_start, self.btn_stop, self.btn_close = QPushButton(tr_msg('Start')), QPushButton(tr_msg('Stop')), QPushButton(tr_msg('Close'))
        for button in (self.btn_start, self.btn_stop, self.btn_close):
            buttons.addWidget(button)
        outer.addLayout(buttons)
        screen = QGuiApplication.primaryScreen()
        if screen:
            available = screen.availableGeometry()
            self.resize(min(1100, available.width() - 40), min(850, available.height() - 80))
        self.btn_start.clicked.connect(self.start)
        self.btn_stop.clicked.connect(self.stop)
        self.btn_close.clicked.connect(self.close)
        self.combo_network.currentIndexChanged.connect(self.suggestPairs)
        self.suggestPairs()
        self.check_outputs.toggled.connect(self.updateHints)
        self.fillRequired()
        self.updateHints()
        self.updateEnabled()
        self.loadIterationTable()

    # ---------------------------------------------------------------- settings
    def section(self, title, content, collapsed=False):
        """a collapsible section with a layout or a widget"""
        box = QgsCollapsibleGroupBox(title)
        box.setSaveCollapsedState(False)
        if isinstance(content, QWidget):
            inner = QVBoxLayout()
            inner.setContentsMargins(4, 4, 4, 4)
            inner.addWidget(content)
            box.setLayout(inner)
        else:
            box.setLayout(content)
        box.setCollapsed(collapsed)
        return box

    def log(self, message):
        self.log_edit.append(message)

    def refuse(self, messages):
        """why the run does not start: in the log (the results open on it) and the first message in the message bar"""
        self.box_results.setCollapsed(False)
        self.results_tabs.setCurrentWidget(self.log_edit)
        for message in messages:
            self.log(message)
        if messages:
            iface.messageBar().pushMessage(tr_msg('Cost optimization'), messages[0] + (' ' + tr_msg('(more in the log)') if len(messages) > 1 else ''),
                                           level=MessageWarning)

    def update_progress(self, value):
        self.progress.setValue(int(value))

    def suggestPairs(self):
        try:
            network = int(self.combo_network.currentText() or 1)
            pairs, _ = suggestPairs(getPlantConnections(self.main.cur, self.main.config, network))
            self.pair_table.setPairs(networkSequences(self.main.cur, self.main.config, network), pairs)
        except Exception:
            QgsMessageLog.logMessage(traceback.format_exc(), 'Districts', MessageCritical)

    def pairs(self):
        return self.pair_table.pairs()

    def fillRequired(self):
        from .utility_functions.db import getTemplateNames
        entries = ensureRequired(self.main.config, getTemplateNames(self.main.cur, 'customer', seperator='_'))
        self.table_required.setRowCount(0)
        for entry in entries:
            row = self.table_required.rowCount()
            self.table_required.insertRow(row)
            for col, key in enumerate(('template', 'column', 'unit', 'mode')):
                self.table_required.setItem(row, col, QTableWidgetItem(str(entry[key])))

    def saveProtected(self, p):
        """checks and saves the protected lines (the run reads them from the version folder; a child version copies it)"""
        protected, invalid = self.protected_lines.entries()
        if invalid:
            self.log(tr_msg('Protected lines: not a line ID: {}').format(', '.join(invalid)))
            return False
        try:
            network_lids = networkLineIds(self.main.cur, self.main.config, int(p['network']))
            saveProtectedLines(self.main.config, protected)
        except Exception:
            QgsMessageLog.logMessage(traceback.format_exc(), 'Districts', MessageCritical)
            self.log(tr_msg('The protected lines could not be saved: ') + traceback.format_exc().splitlines()[-1])
            return False
        foreign = [lid for lid in protected if lid not in network_lids]
        if foreign:
            self.log(tr_msg('Protected lines not in network {}, not protected in this run: {}').format(p['network'], ', '.join(str(lid) for lid in foreign)))
        if len(protected) > len(foreign):
            self.log(tr_msg('{} protected lines keep their pipes').format(len(protected) - len(foreign)))
        return True

    def requiredEntries(self):
        entries = []
        for row in range(self.table_required.rowCount()):
            text = [self.table_required.item(row, col).text() if self.table_required.item(row, col) else '' for col in range(4)]
            try:
                entries.append({'template': text[0], 'column': int(text[1]), 'unit': text[2] or 'W', 'mode': text[3] or 'heating'})
            except ValueError:
                continue
        return entries

    def updateHints(self):
        hints = []
        if not loadIterations(self.main.config):
            hints.append('<a href="{}">{}</a>'.format(BALANCING_LINK, html.escape(
                tr_msg('The version has no iterations of the hydraulic balancing; run it first for a balanced start.'))))
        missing = missingOutputs(self.main.plugin_dir, self.main.config)
        if missing:
            state = tr_msg('switched on at the start') if self.check_outputs.isChecked() else tr_msg('switched off')
            hints.append(html.escape(tr_msg('Requested outputs the optimization needs ({}): {}').format(state, ', '.join(missing))))
        self.label_hints.setText('<br>'.join(hints))

    def onCostLink(self, link):
        if link == 'scenarios':
            self.main.manageEconomicScenarios()
            dialog = getattr(self.main, 'dlg_economicScenarios', None)
            if dialog is not None:
                # new or renamed scenarios are offered when the dialog is closed
                dialog.finished.connect(lambda _: self.refreshScenarios())
        elif link == 'pipes':
            self.main.managePipes()

    def refreshScenarios(self):
        current = self.combo_scenario.currentData()
        fillScenarioCombo(self.main.cur, self.combo_scenario)
        index = self.combo_scenario.findData(current)
        if index >= 0:
            self.combo_scenario.setCurrentIndex(index)

    def onHintLink(self, link):
        if link == BALANCING_LINK:
            self.main.showDynamicPipeSizing()

    def updateEnabled(self):
        self.periods.setRunning(self.process_running)
        self.btn_start.setEnabled(not self.process_running)
        self.btn_stop.setEnabled(self.process_running)
        # while running the run adds and shows the iterations itself
        for button in (self.btn_showIterations, self.btn_reload, self.btn_setPipes):
            button.setEnabled(not self.process_running)

    def parameters(self):
        return {'scenario': self.combo_scenario.currentData(), 'network': self.combo_network.currentText(), 'submodel': self.combo_submodel.currentText(),
                'pairs': self.pairs(), 'periods': self.periods.parameters(),
                'price_kh': self.spin_price_kh.value(), 'tolerance': self.spin_tolerance.value(), 'price_kwh': self.spin_price_kwh.value(),
                'unmet_tolerance': self.spin_tolerance_kwh.value(), 'dp_spez_max': self.spin_dp_max.value(), 'v_max': self.spin_v_max.value(),
                'max_iter': self.spin_iter.value(), 'new_version': self.edit_version.text().strip() if self.rbtn_new.isChecked() else None,
                'set_outputs': self.check_outputs.isChecked(), 'mode_deadband_pct': self.spin_deadband.value(),
                'stages': self.stage_table.stages()}

    # ---------------------------------------------------------------- run
    def start(self):
        if not self.periods.ready and not self.periods.check_annual.isChecked():
            self.refuse([tr_msg('The weeks are still being chosen; start again in a moment.')])
            return
        p = self.parameters()
        if self.pair_table.incomplete():
            self.refuse([tr_msg('Choose the supply and the return sequence of every pair, or remove the row.')])
            return
        if p['scenario'] is None or not p['pairs'] or not p['submodel']:
            self.refuse([tr_msg('Choose a scenario, a submodel and at least one pair.')])
            return
        if not self.saveProtected(p):
            self.refuse([tr_msg('The protected lines could not be saved (see the log).')])
            return
        if len(p['stages']) > 1:
            try:
                problems = stageProblems(self.main.cur, p['stages'])
            except Exception:
                QgsMessageLog.logMessage(traceback.format_exc(), 'Districts', MessageCritical)
                self.refuse([tr_msg('The stages could not be checked: ') + traceback.format_exc().splitlines()[-1]])
                return
            if problems:
                self.refuse([problemText(problem) for problem in problems])
                return
        saveRequired(self.main.config, self.requiredEntries())
        errors, notes = self.checkInputData(p)
        if errors:
            self.refuse([tr_msg('The input data of the versions has errors, the run does not start:')] + errors + notes)
            return
        self.process_running = True
        self.updateEnabled()
        self.table_iterations.setRowCount(0)
        self.log_edit.clear()
        # during the run the results need the room
        for box in (self.box_settings, self.box_periods, self.box_required):
            box.setCollapsed(True)
        self.box_results.setCollapsed(False)
        if notes:
            self.log(tr_msg('Check of the input data:'))
            for note in notes:
                self.log('  ' + note)
        self.log(tr_msg('Starting ...'))
        self.run = CostOptimizationRun(self, self.main, p)
        # the start (child version, first simulation) blocks for a moment: first let the dialog show the greyed button
        QTimer.singleShot(50, self.run.start)

    def checkInputData(self, p):
        """(errors, notes) of the model checks over every stage version: each is built and simulated in every
        iteration, so a failing mapping expression is found before the hours of simulation"""
        versions = [s['version'] for s in p['stages']] or [self.main.config['versionName']]
        try:
            result = checkVersions(self.main.cur, self.main.config, versions, plugin_dir=self.main.plugin_dir, skip=skippedRules(p))
        except Exception:
            # a failing check must not block a run that may well work
            QgsMessageLog.logMessage(traceback.format_exc(), 'Districts', MessageCritical)
            return [], [tr_msg('The input data could not be checked: ') + traceback.format_exc().splitlines()[-1]]
        return inputDataMessages(result)

    def stop(self):
        if self.run:
            self.run.stop_requested = True
            self.log(tr_msg('Stopping after the current step ...'))

    def finished(self):
        self.process_running = False
        self.updateEnabled()
        self.updateHints()

    def loadIterationTable(self):
        """the iterations saved in the loaded version"""
        self.table_iterations.setRowCount(0)
        try:
            rows = loadCostIterations(self.main.config)
        except Exception:
            QgsMessageLog.logMessage(traceback.format_exc(), 'Districts', MessageCritical)
            rows = []
        self.showRows(rows)
        if rows:
            self.plot(rows)
            self.markBest(min(rows, key=lambda r: r['npv'])['iteration'])
            self.box_results.setCollapsed(False)

    def selectedIterations(self):
        return sorted({int(self.table_iterations.item(index.row(), 0).text()) for index in self.table_iterations.selectedIndexes()})

    def setSelectedPipes(self):
        selected = self.selectedIterations()
        if len(selected) != 1:
            self.log(tr_msg('Select one iteration in the table.'))
            return
        rows = {row['iteration']: row for row in loadCostIterations(self.main.config)}
        self.set_pipes = SetPipes(self, self.main, tr_msg('Cost optimization'), self.log, self.loadIterationTable)
        row = rows.get(selected[0], {})
        stage_states = row.get('stage_states') or {}
        loaded = self.main.config['versionName']
        target = {'bundles': {int(lid): bid for lid, bid in stage_states[loaded].items()}} if loaded in stage_states else costIterationPipes(row)
        stages = [(version, {'bundles': {int(lid): bid for lid, bid in state.items()}}) for version, state in stage_states.items() if version != loaded]
        self.set_pipes.run(selected[0], target, stages=stages)

    def showSelectedIterations(self):
        selected = self.selectedIterations()
        if not selected:
            iface.messageBar().pushMessage(tr_msg('Info'), tr_msg('Please select one or more iterations in the table.'), level=MessageInfo)
            return
        try:
            showCostIterations(self.main.cur, self.main.config, selected, loadCostIterations(self.main.config))
            iface.mapCanvas().refresh()
        except Exception:
            QgsMessageLog.logMessage(traceback.format_exc(), 'Districts', MessageCritical)
            iface.messageBar().pushMessage(tr_msg('Error'), tr_msg('The iterations could not be shown: ') + traceback.format_exc().splitlines()[-1],
                                           level=MessageCritical)

    def showRows(self, rows):
        """the whole table: a row shows the step of the row before it (iterationTableRows)"""
        self.table_iterations.setRowCount(0)
        for row, steps, outcome in iterationTableRows(rows):
            r = self.table_iterations.rowCount()
            self.table_iterations.insertRow(r)
            values = [row['iteration'], '{:,.0f}'.format(row['npv']).replace(',', "'"),
                      '' if row.get('npv_model') is None else '{:,.0f}'.format(row['npv_model']).replace(',', "'"),
                      '' if row.get('model_error') is None else '{:.1%}'.format(row['model_error'])] + steps + [len(row.get('penalty_customers') or []), outcome]
            for col, value in enumerate(values):
                self.table_iterations.setItem(r, col, QTableWidgetItem(str(value)))

    def markBest(self, iteration):
        for r in range(self.table_iterations.rowCount()):
            best = self.table_iterations.item(r, 0).text() == str(iteration)
            for col in range(self.table_iterations.columnCount()):
                item = self.table_iterations.item(r, col)
                if item:
                    item.setBackground(QColor('#c8e6c9') if best else QColor(0, 0, 0, 0))

    def plot(self, rows):
        self.figure.clear()
        npvBars(self.figure.add_subplot(111), rows)
        self.figure.tight_layout()
        self.canvas.draw()


class _Canvas(FigureCanvasQTAgg):
    # matplotlib's hint is the canvas's current size: in the scroll area it then only grows (each layout pass
    # keeps what it got, a DPI change scales it up)
    def sizeHint(self):
        return QSize(600, 300)

    def minimumSizeHint(self):
        return QSize(200, 250)


class _CheckDialog:
    """what PeriodRun needs of a dialog, for a check inside the optimization"""

    def __init__(self, dlg, year, t_year, climate):
        self.dlg, self.year, self.t_year, self.climate = dlg, year, t_year, climate

    def log(self, message):
        self.dlg.log('  ' + message)

    def update_progress(self, value):
        pass

    def finished(self):
        pass


class CostOptimizationRun(QObject):
    def __init__(self, dlg, main, parms):
        super().__init__()
        self.dlg, self.main, self.parms = dlg, main, parms
        self.plugin_dir = main.plugin_dir
        self.iteration = 0
        self.rows, self.states, self.line_states = [], [], {}
        self.reference = None
        self.no_smaller = set()
        self.done = False
        self.stop_requested = False
        self.final_check = False
        # a network built in stages (network-stages): the stage versions the run works on, filled at the start
        self.stages = parms.get('stages') if len(parms.get('stages') or []) > 1 else []
        self.stage_versions: list = []
        self.triggers_off = None
        self.stage_climates: dict = {}
        self.stage_references: list = []

    @property
    def config(self):
        return self.main.config

    def stageList(self):
        """[{'version', 'start'}] of the versions the run works on (the result versions), None without stages"""
        if not self.stages:
            return None
        return [{'version': v, 'start': int(s['start'])} for v, s in zip(self.stage_versions, self.stages)]

    @property
    def cur(self):
        return self.main.cur

    # ---------------------------------------------------------------- start
    def start(self):
        try:
            self.settings = dict(loadModellingSettings(self.plugin_dir, self.config), mode_deadband_pct=self.parms.get('mode_deadband_pct', DEFAULT_DEADBAND_PCT))
            self.prices = os.path.join(self.config['pathProjects'] + self.config['projectName'], 'prices')
            self.year, self.t_year, self.climate = self.dlg.periods.year, self.dlg.periods.t_year, self.dlg.periods.climate
            missing = missingOutputs(self.plugin_dir, self.config) if self.parms.get('set_outputs') else []
        except Exception:
            self.onException()
            return
        if missing:
            self.setOutputs(missing)
        else:
            self.afterOutputs()

    def setOutputs(self, missing):
        """the missing outputs switched on as in the requested outputs dialog (written into the project's templates)"""
        from .ida_mosim_dialog import RequestedOutputsDialog
        from .outputs import WorkerSetRequestedOutputs
        self.dlg.log(tr_msg('Switching on the requested outputs: {} ...').format(', '.join(missing)))
        try:
            requested = loadRequestedOutputs(self.plugin_dir, self.config)
            self.dlg_outputs = RequestedOutputsDialog(requested, self.config, self.cur)
            for key in missing:
                getattr(self.dlg_outputs, OUTPUT_CHECKBOXES[key]).setChecked(True)
            self.worker_outputs = WorkerSetRequestedOutputs(config=self.config, plugin_dir=self.plugin_dir, dlg=self.dlg_outputs, requestedOutputs=requested)
            self.worker_outputs.signals.error.connect(self.onOutputsError)
            self.worker_outputs.signals.finished.connect(self.onOutputsSet)
            QThreadPool.globalInstance().start(self.worker_outputs)
        except Exception:
            self.onException()

    @pyqtSlot(str)
    def onOutputsError(self, message):
        self.dlg.log('  ' + message)

    @pyqtSlot(str)
    def onOutputsSet(self, message):
        if self.done:
            return
        self.main.requestedOutputs = loadRequestedOutputs(self.plugin_dir, self.config)
        still = missingOutputs(self.plugin_dir, self.config)
        if still:
            self.finish(tr_msg('The requested outputs could not be switched on: {}').format(', '.join(still)), error=True)
            return
        self.dlg.updateHints()
        self.afterOutputs()

    def afterOutputs(self):
        if self.stopCheck():
            return
        if self.stages:
            self.stage_versions = [s['version'] for s in self.stages]
            if self.parms['new_version']:
                loaded, name = self.config['versionName'], self.parms['new_version']
                suffix = name[len(loaded):] if name.startswith(loaded) and len(name) > len(loaded) else '_co'
                self.stage_versions = [name] + [s['version'] + suffix for s in self.stages[1:]]
                self.createStageVersion(1)
                return
        if self.parms['new_version']:
            self.createVersion()
        else:
            self.begin()

    def createStageVersion(self, k):
        """the child versions of the later stages, one after another; then the child of stage 1, which is loaded"""
        if self.stopCheck():
            return
        if k >= len(self.stages):
            self.createVersion()
            return
        base, name = self.stages[k]['version'], self.stage_versions[k]
        self.dlg.log(tr_msg('Creating the child version {} of {} ...').format(name, base))
        config, plugin_dir = dict(self.config, versionName=base), self.plugin_dir
        description = 'Cost optimization of version {} (stage {})'.format(base, k + 1)
        startTask(self, self.config, lambda cur: createChildVersion(cur, config, plugin_dir, name, description),
                  lambda _: self.createStageVersion(k + 1), self.onTaskFailed)

    def createVersion(self):
        name = self.parms['new_version']
        self.dlg.log(tr_msg('Creating the child version {} of {} ...').format(name, self.config['versionName']))
        config, plugin_dir, description = dict(self.config), self.plugin_dir, 'Cost optimization of version {}'.format(self.config['versionName'])
        startTask(self, self.config, lambda cur: createChildVersion(cur, config, plugin_dir, name, description), self.onVersionCreated, self.onTaskFailed)

    @pyqtSlot(object)
    def onVersionCreated(self, _):
        from .ida_ph import getVersionData, importData
        if self.done:
            return
        name = self.parms['new_version']
        try:
            importData(self.main.model, getVersionData(self.cur))
            self.main.config['versionName'] = name
            write_plugin_settings(self.main.config)
            from .ida_ph import loadVersionLayers
            loadVersionLayers(self.config, self.cur, self.plugin_dir)
            self.worker_version = WorkerLoadVersion(config=self.config, cur=self.cur, dlg=self.main.dlg)
            self.worker_version.signals.error.connect(lambda m: self.dlg.log(m))
            self.worker_version.signals.finished.connect(self.onVersionLoaded)
            QThreadPool.globalInstance().start(self.worker_version)
        except Exception:
            self.onException()

    @pyqtSlot(str)
    def onVersionLoaded(self, message):
        from .ida_ph import finishedLoadVersion
        if self.done:
            return
        finishedLoadVersion(self.main)
        self.begin()

    def begin(self):
        deleteIterationFiles(self.config)
        try:
            saveRunParameters(self.config, 'cost', dict(self.parms, protected=loadProtectedLines(self.config), stage_versions=self.stage_versions))
        except Exception:
            QgsMessageLog.logMessage(traceback.format_exc(), 'Districts', MessageCritical)
        removeCostLayers()
        if self.stages:
            try:
                # each stage is written by itself; switched on again by finish (a version load re-creates them as well)
                self.triggers_off = self.config['versionName']
                versionTriggers(self.cur, self.triggers_off, False)
                if self.parms['new_version']:
                    linkStages(self.cur, self.stage_versions)
                    self.dlg.log(tr_msg('Version tree: {}').format(' → '.join(self.stage_versions)))
                n = inheritPipes(self.cur, self.stage_versions, stageRoots(self.cur, self.stage_versions))
                if n:
                    self.dlg.log(tr_msg('{} lines of the later stages got the pipes of the same line in the earlier stage.').format(n))
            except Exception:
                self.onException()
                return
        self.periods = self.parms['periods']
        if not self.periods['annual']:
            self.dlg.log(tr_msg('Weeks from {}').format(', '.join(str(d[0].date()) for d in self.periods['periods'])))
        self.check(build=True)

    # ---------------------------------------------------------------- checks
    def check(self, build):
        if self.stopCheck():
            return
        if self.stages:
            self.checkStage(0, build)
            return
        self.dlg.log(tr_msg('Iteration {}: simulating the periods ...').format(self.iteration))
        parms = {'network': self.parms['network'], 'submodel': self.parms['submodel'], 'build_first': build,
                 # the first run invokes the customers and plants again, so their outputs match the requested ones
                 'reinvoke': self.iteration == 0 and not self.final_check, **self.periods}
        self.period_run = PeriodRun(_CheckDialog(self.dlg, self.year, self.t_year, self.climate), self.main, parms, on_finished=self.onChecked)
        self.period_run.start()

    def checkStage(self, k, build):
        """the periods of stage k with its version and its climate (network-stages D4, D5); the loaded version (stage 1)
        is set again after the last stage"""
        if self.stopCheck():
            return
        version = self.stage_versions[k]
        self.dlg.log(tr_msg('Iteration {}: simulating the periods of stage {} ({}) ...').format(self.iteration, k + 1, version))
        try:
            if version not in self.stage_climates:
                climate = climateFile(dict(self.config, versionName=version), self.cur)
                self.stage_climates[version] = (climate, readClimate(climate))
            climate, t_year = self.stage_climates[version]
            self.main.config['versionName'] = version
        except Exception:
            self.main.config['versionName'] = self.stage_versions[0]
            self.onException()
            return
        parms = {'network': self.parms['network'], 'submodel': self.parms['submodel'], 'build_first': build,
                 'reinvoke': self.iteration == 0 and not self.final_check, **self.periods}
        self.period_run = PeriodRun(_CheckDialog(self.dlg, self.year, t_year, climate), self.main, parms,
                                    on_finished=lambda ok: self.onStageChecked(k, build, ok))
        self.period_run.start()

    def onStageChecked(self, k, build, ok):
        if not ok or k + 1 >= len(self.stages):
            self.main.config['versionName'] = self.stage_versions[0]
            self.onChecked(ok)
            return
        self.checkStage(k + 1, build)

    def onChecked(self, ok):
        if self.done:
            return
        if not ok:
            self.finish(tr_msg('The check of iteration {} failed.').format(self.iteration), error=True)
            return
        try:
            if self.final_check:
                self.finish(tr_msg('Finished: the pipes of iteration {} are in the version and simulated.').format(self.best()['iteration']))
                return
            self.evaluate()
        except Exception:
            self.onException()

    def onTaskFailed(self, message):
        self.finish(tr_msg('Error in iteration {}: {}').format(self.iteration, message), error=True)

    def evaluate(self):
        """the NPV and the penalties of the checked iteration, in a worker thread"""
        self.dlg.log(tr_msg('Iteration {}: evaluating the results ...').format(self.iteration))
        config, p, settings, prices, required = dict(self.config), dict(self.parms), self.settings, self.prices, self.dlg.requiredEntries()

        def work(cur):
            evaluation = evaluateVersion(cur, config, p['scenario'], settings, profile_dir=prices)
            if 'npv' not in evaluation:
                return evaluation, None, None
            return evaluation, penaltyValues(cur, config, required, p['submodel'], p['tolerance'], p['unmet_tolerance'] / 100), lineState(cur, config['versionName'])

        stages = self.stageList()
        if stages:
            def staged(cur):
                evaluations, values = [], []
                for stage in stages:
                    cfg = dict(config, versionName=stage['version'])
                    evaluation = evaluateVersion(cur, cfg, p['scenario'], settings, profile_dir=prices)
                    if 'npv' not in evaluation:
                        return evaluation, None, None
                    evaluations.append(evaluation)
                    values.append(penaltyValues(cur, cfg, required, p['submodel'], p['tolerance'], p['unmet_tolerance'] / 100))
                return evaluations, values, {s['version']: lineState(cur, s['version']) for s in stages}
            startTask(self, self.config, staged, self.onEvaluated, self.onTaskFailed)
            return
        startTask(self, self.config, work, self.onEvaluated, self.onTaskFailed)

    @pyqtSlot(object)
    def onEvaluated(self, result):
        if self.done:
            return
        try:
            if self.stages and isinstance(result[0], list):
                self.evaluatedStages(*result)
            else:
                self.evaluated(*result)
        except Exception:
            self.onException()

    def evaluatedStages(self, evaluations, values, states):
        """the NPV of all stages (network-stages D3): stagesNpv over the stage versions, the penalty of each stage in its
        years; a new deficit in any stage blocks the lines made smaller in the last step"""
        p = self.parms
        if not self.stage_references:
            self.stage_references = values
        yearly = [penaltyCost(v, p['price_kh'], p['price_kwh']) for v in values]
        result = stagesNpv(evaluations[0]['scenario'], self.stageList(), evaluations, yearly)
        # per stage: the customer IDs of the stages are their own (the map shows each stage's)
        stage_penalty = {s['version']: sorted(cid for cid, (kh, kwh) in v.items() if kh > ref.get(cid, (0, 0))[0] + 1e-6 or kwh > ref.get(cid, (0, 0))[1] + 1e-6)
                         for s, v, ref in zip(self.stageList(), values, self.stage_references)}
        new_deficits = sorted({cid for cids in stage_penalty.values() for cid in cids})
        previous = self.rows[-1] if self.rows else None
        npv_model = previous.get('npv_next') if previous else None
        npv = result['npv']
        row = {'iteration': self.iteration, 'npv': npv, 'split': result['split'], 'npv_model': npv_model,
               'model_error': None if npv_model is None or not npv else (npv_model - npv) / abs(npv),
               'penalty_customers': new_deficits, 'stage_penalty': stage_penalty, 'state': states[self.stage_versions[-1]], 'economics': None,
               # the line IDs differ between the stages (pipe laying of the extension): the pipes of each stage
               'stage_states': {version: {str(lid): bid for lid, bid in state.items()} for version, state in states.items()},
               'stages': [{'version': s['version'], 'start': s['start'], 'npv': r['npv'], 'split': r['split'],
                           'climate': (self.stage_climates.get(s['version']) or ('',))[0]}
                          for s, r in zip(self.stageList(), result['stages'])]}
        if previous:
            row['penalty_reverted'] = [lid for lid in previous.get('smaller', []) if new_deficits]
            self.no_smaller.update(row['penalty_reverted'])
        self.dlg.log(tr_msg('Iteration {}: NPV of the stages {} €').format(self.iteration, ', '.join(
            '{:,.0f}'.format(r['npv']).replace(',', "'") for r in result['stages'])))
        self.rows.append(row)
        self.nextStep(row)

    def evaluated(self, evaluation, values, state):
        p = self.parms
        if 'npv' not in evaluation:
            self.finish(tr_msg('The results of iteration {} cannot be evaluated: {}').format(self.iteration, evaluation.get('missing') or evaluation.get('short')), error=True)
            return
        if self.reference is None:
            self.reference = values
            deficits = deficitCustomers(values)
            if deficits:
                self.dlg.log(tr_msg('Iteration {} has comfort violations already: {} customers ({:.0f} Kh, {:.0f} kWh unmet per year: {}). '
                                    'Mostly hydraulic: balance the network first (hydraulic balancing). They count in the NPV of every iteration.').format(
                    self.iteration, len(deficits), sum(values[c][0] for c in deficits), sum(values[c][1] for c in deficits),
                    ', '.join(str(c) for c in deficits[:20]) + (' ...' if len(deficits) > 20 else '')))
        sc = evaluation['scenario']['scenario']
        yearly_penalty = penaltyCost(values, p['price_kh'], p['price_kwh'])
        split = dict(evaluation['npv']['split'])
        split['penalties'] = penaltyNpv(yearly_penalty, float(sc.get('interest_pct') or 0), int(sc.get('period_a') or 0))
        npv = sum(split.values())
        previous = self.rows[-1] if self.rows else None
        npv_model = previous.get('npv_next') if previous else None
        row = {'iteration': self.iteration, 'npv': npv, 'split': split, 'npv_model': npv_model,
               'model_error': None if npv_model is None or not npv else (npv_model - npv) / abs(npv),
               'penalty_customers': sorted(cid for cid, v in values.items() if v[0] > self.reference.get(cid, (0, 0))[0] + 1e-6 or v[1] > self.reference.get(cid, (0, 0))[1] + 1e-6),
               'state': state, 'economics': npvRecord(evaluation, yearly_penalty, split['penalties']),
               'deficit_customers': deficitCustomers(values),
               'deficits': {str(cid): [round(v[0], 1), round(v[1], 1)] for cid, v in values.items() if v[0] > 1e-6 or v[1] > 1e-6}}
        if previous:
            # a new deficit: the lines made smaller in the last step stay as they are now
            row['penalty_reverted'] = [lid for lid in previous.get('smaller', []) if row['penalty_customers']]
            self.no_smaller.update(row['penalty_reverted'])
        self.rows.append(row)
        self.nextStep(row)

    # ---------------------------------------------------------------- steps
    def nextStep(self, row):
        p = self.parms
        best = self.best()
        if self.iteration >= p['max_iter']:
            row['outcome'] = tr_msg('max. iterations')
            self.saveRow(row, [], {})
            return self.end(tr_msg('Maximal number of iterations reached.'))
        if len(self.rows) > NO_IMPROVEMENT and all(r['npv'] >= best['npv'] for r in self.rows[-NO_IMPROVEMENT:]) and best is not self.rows[-1]:
            row['outcome'] = tr_msg('no improvement')
            self.saveRow(row, [], {})
            return self.end(tr_msg('No improvement of the simulated NPV for {} iterations.').format(NO_IMPROVEMENT))
        self.dlg.log(tr_msg('Iteration {}: cost model and step ...').format(self.iteration))
        config, settings, prices, no_smaller, stages = dict(self.config), self.settings, self.prices, set(self.no_smaller), self.stageList()
        startTask(self, self.config, lambda cur: modelStep(cur, config, p, settings, prices, no_smaller, stages), self.onStep, self.onTaskFailed)

    @pyqtSlot(object)
    def onStep(self, result):
        if self.done:
            return
        try:
            self.stepped(result)
        except Exception:
            self.onException()

    def stepped(self, result):
        row = self.rows[-1]
        if result is None:
            return self.finish(tr_msg('The cost model could not be built from the results.'), error=True)
        row['n_rejected'] = sum(len(v) for v in result['rejected'].values())
        if not result['steps']:
            row['outcome'] = tr_msg('no improving change')
            self.saveRow(row, [], result['rejected'])
            return self.end(tr_msg('No change improves the costs.'))
        row['npv_next'] = row['npv'] + sum(s['dnpv'] for s in result['steps'])
        row['larger'] = sorted(s['line'] for s in result['steps'] if s['larger'])
        row['smaller'] = sorted(s['line'] for s in result['steps'] if not s['larger'])
        row['n_larger'], row['n_smaller'] = len(row['larger']), len(row['smaller'])
        self.dlg.log(tr_msg('  {} lines changed').format(result['n_changed']))
        iface.mapCanvas().refreshAllLayers()
        state = result['state']
        if state in self.states:
            row['outcome'] = tr_msg('oscillation')
            self.saveRow(row, result['steps'], result['rejected'])
            return self.end(tr_msg('The pipes repeat an earlier iteration (oscillation).'))
        self.states.append(state)
        row['outcome'] = tr_msg('changed')
        self.saveRow(row, result['steps'], result['rejected'])
        self.iteration += 1
        self.check(build=True)

    def saveRow(self, row, steps, rejected):
        data = {k: v for k, v in row.items() if k != 'state'}
        data.update({'steps': steps, 'rejected': {str(lid): reasons for lid, reasons in rejected.items()}, 'state': {str(k): v for k, v in row['state'].items()}})
        with open(iterationPath(self.config, row['iteration']), 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=1, default=str)
        self.dlg.showRows(self.rows)
        self.dlg.plot(self.rows)
        self.dlg.update_progress(min(99, (row['iteration'] + 1) / (self.parms['max_iter'] + 1) * 100))
        try:
            showCostIterations(self.cur, self.config, [row['iteration']], loadCostIterations(self.config))
        except Exception:
            QgsMessageLog.logMessage(traceback.format_exc(), 'Districts', MessageCritical)

    # ---------------------------------------------------------------- end
    def best(self):
        return min(self.rows, key=lambda r: r['npv']) if self.rows else None

    def end(self, message):
        best = self.best()
        self.dlg.log(message)
        self.dlg.markBest(best['iteration'])
        schema = self.config['versionName']
        if self.stages:
            # every stage from its own state (the line IDs differ); the version handling trigger off
            for version in self.stage_versions:
                writeBundles(self.cur, version, {int(lid): bid for lid, bid in best['stage_states'][version].items()})
        elif best['state']:
            # one statement: a row per line would block the dialog on large networks
            psycopg2.extras.execute_values(self.cur, 'UPDATE "{}".lines l SET pipe_bundle_type_id = v.bid FROM (VALUES %s) AS v(id, bid) WHERE l.id = v.id;'.format(schema),  # nosec B608
                                           [(int(lid), bid) for lid, bid in best['state'].items()])
        last = (self.stage_versions or [schema])[-1]
        expected = {int(lid): bid for lid, bid in best['stage_states'][last].items()} if self.stages else best['state']
        if best is self.rows[-1] and lineState(self.cur, last) == expected:
            self.finish(tr_msg('Finished: iteration {} has the least NPV ({:,.0f} €).').format(best['iteration'], best['npv']).replace(',', "'"))
            return
        self.dlg.log(tr_msg('The pipes of iteration {} are restored and simulated again.').format(best['iteration']))
        self.final_check = True
        self.check(build=True)

    def stopCheck(self):
        if self.done:
            return True
        if self.stop_requested:
            self.finish(tr_msg('Stopped by the user after iteration {}.').format(self.iteration), error=True)
            return True
        return False

    def finish(self, message, error=False):
        if self.done:
            return
        self.done = True
        self.restoreVersionHandling()
        self.dlg.log(message)
        self.dlg.update_progress(0 if error else 100)
        iface.messageBar().pushMessage(tr_msg('Error') if error else tr_msg('Info'), tr_msg('Cost optimization: ') + message,
                                       level=MessageCritical if error else MessageInfo)
        self.dlg.finished()

    def restoreVersionHandling(self):
        """the triggers on again, then the lines the version handling would copy wrongly by ID between the stages
        (network-stages D11): in the log and in the run parameters for the report"""
        if not self.triggers_off:
            return
        try:
            versionTriggers(self.cur, self.triggers_off, True)
            self.triggers_off = None
            links = []
            for before, after in zip(self.stage_versions, self.stage_versions[1:]):
                found = stageLinks(self.cur, before, after)
                links.append(dict(found, before=before, after=after))
                if found['other']:
                    self.dlg.log(tr_msg('{}: {} lines have the ID of another or a longer line of {} (split); a change of that line in {} is '
                                        'copied into them by ID: {}').format(after, len(found['other']), before, before, idList(found['other'])))
                if found['not_reached']:
                    self.dlg.log(tr_msg('{}: {} lines lie on a line of {} under another ID; a change of that line in {} does not reach '
                                        'them: {}').format(after, len(found['not_reached']), before, before, idList(found['not_reached'])))
            # the run parameters lie in stage 1, the loaded version (config switches to a stage while it is checked)
            config = dict(self.config, versionName=self.stage_versions[0])
            parms = loadRunParameters(config, 'cost')
            if parms:
                saveRunParameters(config, 'cost', dict(parms, stage_links=links))
        except Exception:
            QgsMessageLog.logMessage(traceback.format_exc(), 'Districts', MessageCritical)
            self.dlg.log(tr_msg('The version handling of {} could not be switched on again; load the version again.').format(self.triggers_off or ''))

    def onException(self):
        QgsMessageLog.logMessage(traceback.format_exc(), 'Districts', MessageCritical)
        self.finish(tr_msg('Error in iteration {}: {}').format(self.iteration, traceback.format_exc().splitlines()[-1]), error=True)
