# coding=utf-8
"""Model checks of a version (OpenSpec change ai-mcp-connection, D6/D7): rules over the QGIS model, the IDA templates
and the results, each returning findings {rule, severity, feature_type, feature_id, component, values, text}.
The rules only read; run them on a cursor whose transaction is rolled back (the height rule uses a temp table)."""
import json
import os
from collections import defaultdict

from .flow_tracing import getFeatureConnTables, getTimeSeries
from .hydraulic_balancing import specificPressureLoss
from .network_economics import resultTables, tableExists
from .translations import tr_msg

SEVERITIES = ('error', 'warning', 'info')
SCOPES = ('qgis', 'templates', 'results')
# D7 (decided 2026-11-19): defaults only where they hold for every network type
DEFAULTS = {'delta_t_heating_k': 15.0, 'delta_t_cooling_k': 4.0, 'substation_dp_min_bar': 0.5,
            'v_max_m_s': 3.0, 'dp_spec_max_pa_m': 300.0}
# a step counts as a load hour of a customer above this share of its peak heat flow (no findings from standstill)
LOAD_SHARE = 0.10
PLANT_IDLE_SHARE = 0.01
MAX_IDS = 50


def finding(rule, severity, text, feature_type=None, feature_id=None, component=None, values=None):
    return {'rule': rule, 'severity': severity, 'feature_type': feature_type, 'feature_id': feature_id,
            'component': component, 'values': values or {}, 'text': text}


def threshold(value, unit, source):
    return {'threshold': value, 'unit': unit, 'source': source}


class CheckContext:
    """cursor, config of the checked version, thresholds {key: value} given by the caller and cached result series"""

    def __init__(self, cur, config, thresholds=None):
        self.cur = cur
        self.config = config
        self.schema = config['versionName']
        self.thresholds = {k: v for k, v in (thresholds or {}).items() if v is not None}
        self._cache = {}

    def limit(self, key):
        if key in self.thresholds:
            return float(self.thresholds[key]), 'argument'
        return DEFAULTS[key], 'default'

    def exists(self, table):
        return tableExists(self.cur, self.schema, table)

    def networks(self):
        if 'networks' not in self._cache:
            self.cur.execute('SELECT DISTINCT network FROM "{}".lines WHERE network IS NOT NULL ORDER BY network;'.format(self.schema))  # nosec B608
            self._cache['networks'] = [int(r['network']) for r in self.cur.fetchall()]
        return self._cache['networks']

    def connSeries(self, feature, var):
        """{fid: (supply {time: value}, return {time: value})} over all networks"""
        key = ('conn', feature, var)
        if key not in self._cache:
            out = {}
            for network in self.networks():
                tables = getFeatureConnTables(self.cur, self.config, feature, var, network)
                sup = getTimeSeries(self.cur, self.config, {fid: t[0] for fid, t in tables.items()}, '$' + var)
                ret = getTimeSeries(self.cur, self.config, {fid: t[1] for fid, t in tables.items()}, '$' + var)
                for fid in tables:
                    out[fid] = ({t: v[fid] for t, v in sup.items() if fid in v}, {t: v[fid] for t, v in ret.items() if fid in v})
            self._cache[key] = out
        return self._cache[key]

    def powerSeries(self, feature):
        """{fid: {time: summed power}} of the tables <feature>_s_power$*"""
        key = ('power', feature)
        if key not in self._cache:
            out = defaultdict(dict)
            for table in resultTables(self.cur, self.schema, '{}_s_power$'.format(feature)):
                self.cur.execute('SELECT fid, time, sum("$power") AS v FROM "{}"."{}" GROUP BY fid, time;'.format(self.schema, table))  # nosec B608
                for r in self.cur.fetchall():
                    if r['v'] is not None:
                        out[r['fid']][r['time']] = out[r['fid']].get(r['time'], 0.0) + float(r['v'])
            self._cache[key] = dict(out)
        return self._cache[key]


def outputsMissing(rule, outputs):
    return [finding('outputs_missing', 'info', tr_msg('Rule {}: switch on the outputs {} and simulate again.').format(rule, ', '.join(outputs)),
                    values={'rule_checked': rule, 'outputs': outputs})]


# ---------------- qgis ----------------
def ruleTopology(ctx):
    from .topology import checkNetworkTopology, getUnconnectedFeatures
    networks = ctx.networks()
    if not networks:
        return []
    out = []
    for problem in checkNetworkTopology(ctx.cur, ctx.schema, networks) + getUnconnectedFeatures(ctx.cur, ctx.schema, networks):
        ids = problem['ids'][:MAX_IDS]
        rule = 'unconnected_features' if 'table' in problem else 'topology'
        out.append(finding(rule, 'error', '{}: {}'.format(tr_msg(problem['text']), problem['count']),
                           feature_type=problem.get('table'), values={'count': problem['count'], 'ids': ids}))
    return out


def ruleHeights(ctx):
    from .height_check import HEIGHT_CHECK_LAYERS, heightConsistencyRows
    point_rows, line_rows = heightConsistencyRows(ctx.cur, ctx.schema, HEIGHT_CHECK_LAYERS)
    out = []
    for issue in sorted({r['issue'] for r in point_rows + line_rows}):
        rows = [r for r in point_rows + line_rows if r['issue'] == issue]
        ids = sorted({'{}:{}'.format(r.get('layer', 'lines'), r.get('feature_id', r.get('line_id'))) for r in rows})
        out.append(finding('heights', 'warning', tr_msg('Height check: {} ({} features)').format(issue, len(rows)),
                           values={'issue': issue, 'count': len(rows), 'features': ids[:MAX_IDS]}))
    return out


def rulePipeData(ctx):
    ctx.cur.execute("""SELECT l.id AS lid, l.pipe_bundle_type_id AS bundle, bp.sequence AS seq, p.id AS pipe_id, p.name,
        p.innerpipediameter AS d, p.piperoughnessfactor AS k, p.pipe_construction_id AS construction,
        (SELECT count(*) FROM public.pipe_layers pl WHERE pl.pipe_construction_id = p.pipe_construction_id) AS layers
        FROM "{}".lines l LEFT JOIN public.bundle_pipes bp ON bp.pipe_bundle_type_id = l.pipe_bundle_type_id
        LEFT JOIN public.pipes p ON p.id = bp.pipe_id ORDER BY l.id, bp.sequence;""".format(ctx.schema))  # nosec B608
    out = []
    for r in ctx.cur.fetchall():
        if r['pipe_id'] is None:
            missing = ['pipe']
        else:
            missing = [name for name, bad in (('diameter', not r['d'] or float(r['d']) <= 0), ('roughness', r['k'] is None),
                                              ('u-value (pipe construction layers)', not r['construction'] or not r['layers'])) if bad]
        if missing:
            out.append(finding('pipe_data_missing', 'error', tr_msg('Line {}: pipe data missing ({}).').format(r['lid'], ', '.join(missing)),
                               'lines', r['lid'], values={'bundle': r['bundle'], 'sequence': r['seq'], 'pipe': r['name'], 'missing': missing}))
    return out


# ---------------- templates ----------------
def ruleTemplateWarnings(ctx):
    from ..energy_use_dialog import warningText as energyText
    from ..network_pumps_dialog import projectTemplates, warningText as pumpText
    from . import energy_use, network_pumps
    templates = projectTemplates(ctx.cur)
    out = []
    for module, text, rule in ((energy_use, energyText, 'energy_use_detection'), (network_pumps, pumpText, 'pump_detection')):
        for feature, t_name, warning in module.detectProject(ctx.config, templates)[1]:
            out.append(finding(rule, 'warning', text(feature, t_name, warning), feature, component=warning[2] or warning[1],
                               values={'template': t_name, 'kind': warning[0]}))
    return out


# ---------------- results ----------------
def resultsPresent(ctx):
    return bool(resultTables(ctx.cur, ctx.schema, 'line_s_') or resultTables(ctx.cur, ctx.schema, 'customer_s_'))


def ruleRunErrors(ctx):
    out = []
    for folder, _, files in os.walk(versionDir(ctx.config)):
        if 'result.json' not in files:
            continue
        try:
            with open(os.path.join(folder, 'result.json')) as f:
                result = json.load(f)
        except (OSError, ValueError):
            continue
        for error in result.get('errors') or []:
            out.append(finding('run_errors', 'error', tr_msg('IDA run error: {}').format(str(error)[:500]),
                               values={'folder': os.path.relpath(folder, versionDir(ctx.config))}))
    return out


def versionDir(config):
    return os.path.join(config['pathProjects'] + config['projectName'], 'versions', config['versionName'])


def ruleComfort(ctx):
    from .cost_model_data import checkSources, series
    from .penalties import degreeHours
    if not ctx.exists('customer_s_troom') or not ctx.exists('customer_s_tset') or not ctx.exists('customer_s_hcmode'):
        return outputsMissing('comfort_deficit', ['troom_c'])
    check = checkSources(ctx.cur, ctx.config)
    if check:
        sources, times, weights, _, _ = check
    else:
        times = sorted(_times(ctx, 'customer_s_troom'))
        sources, weights = (lambda t: [t]), [_dt(times)] * len(times)
    index = {t: k for k, t in enumerate(times)}
    data = {var: series(ctx.cur, ctx.schema, sources('customer_s_' + var), '$' + var, times, index) for var in ('troom', 'tset', 'hcmode')}
    out = []
    for cid in sorted(data['troom']):
        if cid not in data['tset'] or cid not in data['hcmode']:
            continue
        kh = degreeHours(data['troom'][cid], data['tset'][cid], data['hcmode'][cid], weights)
        if kh > 1e-6:
            out.append(finding('comfort_deficit', 'warning', tr_msg('Customer {}: room temperature misses the setpoint ({:.0f} Kh).').format(cid, kh),
                               'customers', cid, values={'value': round(kh, 1), 'unit': 'Kh', 'basis': 'per year' if check else 'simulated period'}))
    return out


def _times(ctx, table):
    ctx.cur.execute('SELECT DISTINCT time FROM "{}"."{}";'.format(ctx.schema, table))  # nosec B608
    return [r['time'] for r in ctx.cur.fetchall()]


def _dt(times):
    return (times[1] - times[0]).total_seconds() / 3600 if len(times) > 1 else 1.0


def loadSteps(power):
    """{fid: set of times} with |power| above LOAD_SHARE of the feature's peak"""
    steps = {}
    for fid, values in power.items():
        peak = max((abs(v) for v in values.values()), default=0.0)
        steps[fid] = {t for t, v in values.items() if peak > 0 and abs(v) > LOAD_SHARE * peak}
    return steps


def ruleDeltaT(ctx):
    temps = ctx.connSeries('customer', 'temp')
    power = ctx.powerSeries('customer')
    if not temps or not power:
        return outputsMissing('delta_t_low', [o for o, ok in (('temp_c', temps), ('power_c', power)) if not ok])
    heat_limit, heat_source = ctx.limit('delta_t_heating_k')
    cold_limit, cold_source = ctx.limit('delta_t_cooling_k')
    out = []
    steps = loadSteps(power)
    for cid, (sup, ret) in sorted(temps.items()):
        times = [t for t in steps.get(cid, ()) if t in sup and t in ret]
        if not times:
            continue
        heating = [sup[t] - ret[t] for t in times if sup[t] >= ret[t]]
        cooling = [ret[t] - sup[t] for t in times if sup[t] < ret[t]]
        for mode, values, limit, source in (('heating', heating, heat_limit, heat_source), ('cooling', cooling, cold_limit, cold_source)):
            if values and sum(values) / len(values) < limit:
                mean = sum(values) / len(values)
                out.append(finding('delta_t_low', 'warning', tr_msg('Customer {}: mean temperature difference {:.1f} K below {:.1f} K ({}).').format(
                    cid, mean, limit, tr_msg('heating') if mode == 'heating' else tr_msg('cooling')), 'customers', cid,
                    values=dict(threshold(limit, 'K', source), value=round(mean, 2), mode=mode, load_hours=len(values))))
    return out


def ruleSubstationDp(ctx):
    pressures = ctx.connSeries('customer', 'p')
    power = ctx.powerSeries('customer')
    if not pressures or not power:
        return outputsMissing('substation_dp_low', [o for o, ok in (('p_c', pressures), ('power_c', power)) if not ok])
    limit, source = ctx.limit('substation_dp_min_bar')
    out = []
    steps = loadSteps(power)
    for cid, (sup, ret) in sorted(pressures.items()):
        dps = [(sup[t] - ret[t]) / 1e5 for t in steps.get(cid, ()) if t in sup and t in ret]
        if dps and min(dps) < limit:
            out.append(finding('substation_dp_low', 'warning', tr_msg('Customer {}: pressure difference {:.2f} bar below {:.2f} bar.').format(
                cid, min(dps), limit), 'customers', cid,
                values=dict(threshold(limit, 'bar', source), value=round(min(dps), 3), hours_below=sum(1 for d in dps if d < limit))))
    return out


def ruleSupplyTemp(ctx):
    # D7/T11: no default, the required supply temperature depends on the network type; the project has no field yet
    return [finding('supply_temp_low', 'info', tr_msg('No required supply temperature in the project: the supply temperature of the customers is not checked.'))]


def lineSeries(ctx, var, aggregate='max'):
    """{(lid, seq): value over all times and segments} of line_s_<var>$<seq>"""
    out = {}
    for table in resultTables(ctx.cur, ctx.schema, 'line_s_{}$'.format(var)):
        seq = int(table.split('$')[1])
        ctx.cur.execute('SELECT fid, {a}(abs("${v}")) AS v FROM "{s}"."{t}" GROUP BY fid;'.format(a=aggregate, v=var, s=ctx.schema, t=table))  # nosec B608
        for r in ctx.cur.fetchall():
            if r['v'] is not None:
                out[(r['fid'], seq)] = float(r['v'])
    return out


def linePipeRows(ctx):
    ctx.cur.execute("""SELECT l.id AS lid, bp.sequence AS seq, p.name, p.innerpipediameter AS d, p.piperoughnessfactor AS k, p.p_max_bar
        FROM "{}".lines l JOIN public.bundle_pipes bp ON bp.pipe_bundle_type_id = l.pipe_bundle_type_id
        JOIN public.pipes p ON p.id = bp.pipe_id;""".format(ctx.schema))  # nosec B608
    return {(r['lid'], r['seq']): r for r in ctx.cur.fetchall()}


def rulePipePressure(ctx):
    pressure = lineSeries(ctx, 'p')
    if not pressure:
        return outputsMissing('pipe_pressure_limit', ['p_lines'])
    out = []
    for key, pipe in sorted(linePipeRows(ctx).items()):
        if pipe['p_max_bar'] and key in pressure and pressure[key] / 1e5 > float(pipe['p_max_bar']):
            out.append(finding('pipe_pressure_limit', 'error', tr_msg('Line {}: pressure {:.1f} bar above the rating {:.1f} bar of {}.').format(
                key[0], pressure[key] / 1e5, float(pipe['p_max_bar']), pipe['name']), 'lines', key[0],
                values=dict(threshold(float(pipe['p_max_bar']), 'bar', 'project'), value=round(pressure[key] / 1e5, 2), sequence=key[1])))
    return out


def ruleLineHydraulics(ctx):
    mdot = lineSeries(ctx, 'mdot')
    if not mdot:
        return outputsMissing('line_velocity_high', ['mdot_lines'])
    temp = lineSeries(ctx, 'temp', 'avg')
    v_max, v_source = ctx.limit('v_max_m_s')
    r_max, r_source = ctx.limit('dp_spec_max_pa_m')
    out = []
    for key, pipe in sorted(linePipeRows(ctx).items()):
        if key not in mdot or not pipe['d']:
            continue
        r, v = specificPressureLoss(mdot[key], float(pipe['d']), float(pipe['k'] or 0.0), temp.get(key, 60.0))
        if v > v_max:
            out.append(finding('line_velocity_high', 'warning', tr_msg('Line {}: velocity {:.2f} m/s above {:.2f} m/s.').format(key[0], v, v_max),
                               'lines', key[0], values=dict(threshold(v_max, 'm/s', v_source), value=round(v, 3), sequence=key[1], pipe=pipe['name'])))
        if r > r_max:
            out.append(finding('line_dp_spec_high', 'warning', tr_msg('Line {}: pressure loss {:.0f} Pa/m above {:.0f} Pa/m.').format(key[0], r, r_max),
                               'lines', key[0], values=dict(threshold(r_max, 'Pa/m', r_source), value=round(r, 1), sequence=key[1], pipe=pipe['name'])))
    return out


def rulePlants(ctx):
    power = ctx.powerSeries('energy_plant')
    if not power:
        return outputsMissing('plant_never_runs', ['power_ep'])
    peak_all = max((abs(v) for values in power.values() for v in values.values()), default=0.0)
    out = []
    for epid, values in sorted(power.items()):
        peak = max((abs(v) for v in values.values()), default=0.0)
        if peak <= PLANT_IDLE_SHARE * peak_all:
            out.append(finding('plant_never_runs', 'warning', tr_msg('Energy plant {} never runs (peak {:.1f} kW).').format(epid, peak / 1000),
                               'energy_plants', epid, values={'value': round(peak / 1000, 2), 'unit': 'kW', 'threshold': PLANT_IDLE_SHARE,
                                                              'source': 'share of the largest plant peak'}))
    # plant_power_high: no nominal plant power in the project yet (D7: skipped without nominal power)
    return out


# rule id(s) -> (scope, workflow step, function)
RULES = [
    (('topology', 'unconnected_features'), 'qgis', 'topology', ruleTopology),
    (('heights',), 'qgis', 'elevation', ruleHeights),
    (('pipe_data_missing',), 'qgis', 'pipe_data', rulePipeData),
    (('energy_use_detection', 'pump_detection'), 'templates', 'templates', ruleTemplateWarnings),
    (('run_errors',), 'results', 'run', ruleRunErrors),
    (('comfort_deficit',), 'results', 'results', ruleComfort),
    (('delta_t_low',), 'results', 'results', ruleDeltaT),
    (('substation_dp_low',), 'results', 'results', ruleSubstationDp),
    (('supply_temp_low',), 'results', 'results', ruleSupplyTemp),
    (('pipe_pressure_limit',), 'results', 'results', rulePipePressure),
    (('line_velocity_high', 'line_dp_spec_high'), 'results', 'results', ruleLineHydraulics),
    (('plant_never_runs', 'plant_power_high'), 'results', 'results', rulePlants),
]
RULE_IDS = sorted({rule for ids, _, _, _ in RULES for rule in ids} | {'outputs_missing'})
SKIPPED = {'plant_power_high': 'no nominal power of the energy plants in the project'}


def runChecks(cur, config, scope='all', thresholds=None):
    """{'findings': [...], 'rules_run': [...], 'rules_skipped': {rule: reason}, 'errors': {rule: text}} of the version
    config['versionName']; scope 'all' or one of SCOPES; thresholds overrides DEFAULTS (source 'argument')."""
    if scope != 'all' and scope not in SCOPES:
        raise ValueError('scope must be all, ' + ', '.join(SCOPES))
    ctx = CheckContext(cur, config, thresholds)
    has_results = resultsPresent(ctx)
    findings, run, skipped, errors = [], [], dict(SKIPPED), {}
    for ids, rule_scope, _, function in RULES:
        if scope not in ('all', rule_scope):
            continue
        if rule_scope == 'results' and not has_results and function is not ruleRunErrors:
            skipped.update({i: 'no results' for i in ids if i not in SKIPPED})
            continue
        savepoint = not cur.connection.autocommit
        if savepoint:
            cur.execute('SAVEPOINT model_check;')
        try:
            findings += function(ctx)
            run += [i for i in ids if i not in SKIPPED]
        except Exception as e:  # one failing rule must not hide the others
            if savepoint:
                cur.execute('ROLLBACK TO SAVEPOINT model_check;')
            errors.update({i: '{}: {}'.format(type(e).__name__, e) for i in ids})
    order = {s: k for k, s in enumerate(SEVERITIES)}
    findings.sort(key=lambda f: (order[f['severity']], f['rule'], str(f['feature_id'])))
    return {'version': config['versionName'], 'scope': scope, 'findings': findings, 'rules_run': run,
            'rules_skipped': skipped, 'errors': errors}
