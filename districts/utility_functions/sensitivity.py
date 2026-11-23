# coding=utf-8
"""Sensitivity analysis of the cost optimization (OpenSpec change cost-sensitivity): the parameter table, the variant
designs, the overrides of a variant (the stored scenario stays unchanged), the estimate per variant from the best
iteration of the last run, the statistics and the result file versions/<version>/sensitivity.json."""
import copy
import itertools
import json
import os

import numpy as np

from .translations import tr_msg

PRICE_GROUPS = ('electricity', 'fuel', 'purchased_heat')
CURVE_GROUPS = ('heat', 'cold')
ESCALATION_GROUPS = ('electricity', 'fuel', 'purchased_heat', 'heat', 'cold', 'maintenance', 'investment')
RUN_KEYS = ('price_kh', 'price_kwh', 'dp_spez_max', 'v_max')
DESIGNS = ('one_at_a_time', 'combinations', 'sample')
MODES = ('estimate', 'full')
DESIGN_LABELS = {'one_at_a_time': 'One at a time', 'combinations': 'All combinations', 'sample': 'Latin-hypercube sample'}
MODE_LABELS = {'estimate': 'Estimate (no simulation)', 'full': 'Full optimization per variant'}
RESULT_FILE = 'sensitivity.json'
# confirmation before a longer analysis (design D3)
CONFIRM_SECONDS = 600
ESTIMATE_SECONDS_PER_STAGE = 2.0


def parameterRows(scenario, parms):
    """[{'key', 'label', 'unit', 'base'}] of the parameters a variant can change (design D1); a parameter without a base
    value in the scenario (e.g. a cost group without start price) is left out"""
    sc = scenario['scenario']
    groups = scenario.get('groups', {})
    rows = [{'key': 'interest_pct', 'label': tr_msg('Interest rate'), 'unit': '%/a', 'base': float(sc.get('interest_pct') or 0)},
            {'key': 'period_a', 'label': tr_msg('Period'), 'unit': 'a', 'base': float(sc.get('period_a') or 0)}]
    for g in PRICE_GROUPS:
        price = (groups.get(g) or {}).get('start_price')
        if price is not None:
            rows.append({'key': 'price:' + g, 'label': tr_msg('Start price {}').format(tr_msg(g)), 'unit': '€/kWh', 'base': float(price)})
    for g in CURVE_GROUPS:
        if scenario.get('curves', {}).get(g):
            rows.append({'key': 'price:' + g, 'label': tr_msg('Price curve {} (factor)').format(tr_msg(g)), 'unit': '×', 'base': 1.0})
    for g in ESCALATION_GROUPS:
        if g in groups:
            rows.append({'key': 'escalation:' + g, 'label': tr_msg('Escalation {}').format(tr_msg(g)), 'unit': '%/a',
                         'base': float(groups[g].get('escalation_pct') or 0)})
    for key, label in (('factor:pipe', 'Pipe costs (factor)'), ('factor:trench', 'Trench costs (factor)'), ('factor:pumps', 'Pump costs (factor)')):
        rows.append({'key': key, 'label': tr_msg(label), 'unit': '×', 'base': 1.0})
    for key, label, unit in (('price_kh', 'Penalty per degree hour', '€/Kh'), ('price_kwh', 'Penalty per unmet kWh', '€/kWh'),
                             ('dp_spez_max', 'Limit specific pressure loss', 'Pa/m'), ('v_max', 'Limit velocity', 'm/s')):
        if parms.get(key) is not None:
            rows.append({'key': key, 'label': tr_msg(label), 'unit': unit, 'base': float(parms[key])})
    return rows


def boundValue(base, mode, value):
    """a − or + value of the table: absolute, or relative in % of the base"""
    return float(value) if mode == 'abs' else base * (1 + float(value) / 100)


def variedBounds(varied):
    """{key: (base, low, high)} of the varied rows [{'key', 'base', 'mode', 'minus', 'plus'}]; the period as whole years"""
    bounds = {}
    for row in varied:
        low, high = boundValue(row['base'], row['mode'], row['minus']), boundValue(row['base'], row['mode'], row['plus'])
        if row['key'] == 'period_a':
            low, high = float(round(low)), float(round(high))
        bounds[row['key']] = (row['base'], low, high)
    return bounds


def designVariants(bounds, design='one_at_a_time', size=20, seed=0):
    """[{'name', 'values': {key: value}}] of a design (design D3), the base first; every variant names every varied key"""
    base = {key: b for key, (b, _, _) in bounds.items()}
    variants = [{'name': 'base', 'values': dict(base)}]
    keys = list(bounds)
    if design == 'one_at_a_time':
        for key in keys:
            for sign, index in (('-', 1), ('+', 2)):
                variants.append({'name': '{} {}'.format(key, sign), 'values': dict(base, **{key: bounds[key][index]})})
    elif design == 'combinations':
        for k, combo in enumerate(itertools.product((0, 1, 2), repeat=len(keys))):
            if all(c == 0 for c in combo):
                continue
            variants.append({'name': 'c{}'.format(k), 'values': {key: bounds[key][c] for key, c in zip(keys, combo)}})
    elif design == 'sample':
        rng = np.random.default_rng(int(seed))
        # Latin hypercube: each parameter's range cut into size strata, each stratum used once
        strata = {key: (rng.permutation(size) + rng.random(size)) / size for key in keys}
        for k in range(size):
            values = {}
            for key in keys:
                _, low, high = bounds[key]
                value = low + strata[key][k] * (high - low)
                values[key] = float(round(value)) if key == 'period_a' else float(value)
            variants.append({'name': 's{}'.format(k + 1), 'values': values})
    else:
        raise ValueError(design)
    return variants


def variantCount(n_varied, design, size):
    if design == 'one_at_a_time':
        return 2 * n_varied + 1
    if design == 'combinations':
        return 3 ** n_varied
    return size + 1


def applyOverrides(scenario, overrides):
    """a copy of the scenario with the variant's scenario values (design D2); the cost factor of the pipes as
    scenario['cost_factors']['pipe'], read where the pipe costs are"""
    if not overrides:
        return scenario
    result = copy.deepcopy(scenario)
    sc, groups = result['scenario'], result.setdefault('groups', {})
    for key, value in overrides.items():
        kind, _, name = key.partition(':')
        if key in ('interest_pct', 'period_a'):
            sc[key] = int(round(value)) if key == 'period_a' else value
        elif kind == 'price' and name in CURVE_GROUPS:
            result['curves'][name] = [(t, price * value) for t, price in result.get('curves', {}).get(name, [])]
        elif kind == 'price':
            groups.setdefault(name, {'cost_group': name, 'start_price': None, 'escalation_pct': 0.0})['start_price'] = value
        elif kind == 'escalation':
            groups.setdefault(name, {'cost_group': name, 'start_price': None, 'escalation_pct': 0.0})['escalation_pct'] = value
        elif key == 'factor:trench':
            result['trench'] = {surface: (a * value, b * value) for surface, (a, b) in result.get('trench', {}).items()}
        elif key == 'factor:pumps':
            sc['pump_costs_eur7kw'] = float(sc.get('pump_costs_eur7kw') or 0) * value
        elif key == 'factor:pipe':
            result.setdefault('cost_factors', {})['pipe'] = value
        else:
            raise KeyError(key)
    return result


def variantParameters(parms, values):
    """the run parameters of a variant: the penalty prices and limits set, the scenario values as 'overrides'"""
    result = dict(parms)
    result['overrides'] = {key: value for key, value in values.items() if key not in RUN_KEYS}
    for key in RUN_KEYS:
        if key in values:
            result[key] = values[key]
    return result


def pipeCostFactor(scenario):
    return float((scenario.get('cost_factors') or {}).get('pipe', 1.0))


# ---------------------------------------------------------------- estimate (design D4)
def estimateBasis(cur, rows, run_parms):
    """the best iteration of the last run: {'iteration', 'npv', 'versions', 'stages', 'states', 'no_smaller'}; raises
    ValueError with the reason when there is none or the versions no longer carry its pipes"""
    from ..cost_optimization import lineState
    if not rows:
        raise ValueError(tr_msg('The loaded version has no cost optimization run.'))
    best = min(rows, key=lambda r: r['npv'])
    stage_versions = run_parms.get('stage_versions') or []
    if best.get('stage_states'):
        states = {version: {int(lid): bid for lid, bid in state.items()} for version, state in best['stage_states'].items()}
    else:
        states = {run_parms.get('version'): {int(lid): bid for lid, bid in (best.get('state') or {}).items()}}
    for version, state in states.items():
        cur.execute('SELECT nspname FROM pg_namespace WHERE nspname = %s;', (version,))
        if cur.fetchone() is None:
            raise ValueError(tr_msg('The version {} of the run does not exist anymore.').format(version))
        if lineState(cur, version) != state:
            raise ValueError(tr_msg('The pipes of version {} differ from the best iteration {} of the run: set its pipes again or run the '
                                    'optimization again.').format(version, best['iteration']))
    starts = [int(s['start']) for s in (run_parms.get('stages') or [])]
    stages = [{'version': v, 'start': s} for v, s in zip(stage_versions, starts)] if len(stage_versions) > 1 else None
    no_smaller = sorted({lid for r in rows for lid in (r.get('penalty_reverted') or [])})
    return {'iteration': best['iteration'], 'npv': best['npv'], 'versions': list(states), 'stages': stages, 'states': states, 'no_smaller': no_smaller}


def estimateVariant(cur, config, parms, settings, prices, basis, penalty_values, roots=None):
    """one variant of the estimate (worker thread): the NPV of the basis design with the variant's values and one step
    of the cost model with them. penalty_values: {version: {cid: (Kh, kWh)}} of the basis (they do not depend on
    prices). roots: stageRoots of the stage versions (a step names a line group's root)."""
    from ..cost_optimization import modelStep
    from .economic_data import loadScenario
    from .network_economics import evaluateVersion
    from .network_stages import stagesNpv
    from .penalties import penaltyCost, penaltyNpv
    scenario = applyOverrides(loadScenario(cur, parms['scenario']), parms.get('overrides'))
    sc = scenario['scenario']
    versions = basis['versions']
    evaluations = []
    for version in versions:
        evaluation = evaluateVersion(cur, dict(config, versionName=version), scenario, settings, profile_dir=prices)
        if 'npv' not in evaluation:
            raise ValueError(tr_msg('The results of version {} cannot be evaluated: {}').format(version, evaluation.get('missing') or evaluation.get('short')))
        evaluations.append(evaluation)
    yearly = [penaltyCost(penalty_values.get(v, {}), parms['price_kh'], parms['price_kwh']) for v in versions]
    if basis['stages']:
        result = stagesNpv(scenario, basis['stages'], evaluations, yearly)
        split, npv = dict(result['split']), result['npv']
    else:
        split = dict(evaluations[0]['npv']['split'])
        split['penalties'] = penaltyNpv(yearly[0], float(sc.get('interest_pct') or 0), int(sc.get('period_a') or 0))
        npv = sum(split.values())
    step = modelStep(cur, dict(config, versionName=versions[0]), parms, settings, prices, set(basis['no_smaller']), basis['stages'], write=False)
    steps = (step or {}).get('steps') or []
    after = dict(split)
    for s in steps:
        for key, value in (s.get('split') or {}).items():
            after[key] = after.get(key, 0.0) + value
    changes = []
    for s in steps:
        if basis['stages'] and roots is not None:
            root = (int(s['stage']) - 1, int(s['line']))
            targets = [(version, lid) for version, per in zip(versions, roots) for lid, r in per.items() if r == root]
        else:
            targets = [(versions[0], int(s['line']))]
        for version, lid in targets:
            changes.append({'version': version, 'line': lid, 'before': sorted(s['before'].values()), 'after': sorted(s['after'].values()),
                            'larger': bool(s.get('larger'))})
    return {'npv': npv, 'npv_after': npv + sum(float(s['dnpv']) for s in steps), 'split': split, 'split_after': after,
            'changes': changes, 'n_changed': len(steps)}


# ---------------------------------------------------------------- statistics (design D7)
def ranks(values):
    """ranks with ties averaged (1-based)"""
    values = np.asarray(values, dtype=float)
    order = np.argsort(values, kind='mergesort')
    result = np.empty(len(values))
    result[order] = np.arange(1, len(values) + 1)
    for value in np.unique(values):
        tie = values == value
        result[tie] = result[tie].mean()
    return result


def spearman(x, y):
    """Spearman rank correlation; 0 when one of them does not vary"""
    rx, ry = ranks(x), ranks(y)
    if np.std(rx) == 0 or np.std(ry) == 0:
        return 0.0
    return float(np.corrcoef(rx, ry)[0, 1])


def resultNpv(variant):
    """the NPV a variant's results are compared by: after the step (estimate) or of the run (full)"""
    result = variant.get('result') or {}
    return result.get('npv_after', result.get('npv'))


def tornado(analysis):
    """[(key, npv at −, npv at +)] sorted by the swing, of a one-at-a-time design; [] otherwise"""
    if analysis.get('design') != 'one_at_a_time':
        return []
    by_name = {v['name']: v for v in analysis['variants'] if v.get('result')}
    rows = []
    for key in analysis['bounds']:
        low, high = by_name.get('{} -'.format(key)), by_name.get('{} +'.format(key))
        if low and high:
            rows.append((key, resultNpv(low), resultNpv(high)))
    return sorted(rows, key=lambda r: -abs(r[2] - r[1]))


def correlations(analysis):
    """[(key, Spearman rank correlation with the NPV)] sorted by magnitude"""
    done = [v for v in analysis['variants'] if v.get('result')]
    npv = [resultNpv(v) for v in done]
    rows = [(key, spearman([v['values'][key] for v in done], npv)) for key in analysis['bounds']]
    return sorted(rows, key=lambda r: -abs(r[1]))


def flips(analysis):
    """{(version, line): {'before': pipes of the basis, 'after': {variant name: pipes}}} of the lines a variant
    changes (the base variant too: its step shows a run that stopped before the cost model found no change)"""
    result: dict = {}
    for v in analysis['variants']:
        for c in (v.get('result') or {}).get('changes', []):
            entry = result.setdefault((c['version'], int(c['line'])), {'before': c['before'], 'after': {}})
            entry['after'][v['name']] = c['after']
    return result


def robustness(analysis):
    """{(version, line): share of the variants (without the base) changing the line's pipe}"""
    done = [v for v in analysis['variants'] if v.get('result') and v['name'] != 'base']
    if not done:
        return {}
    counts: dict = {}
    for v in done:
        for key in {(c['version'], int(c['line'])) for c in v['result'].get('changes', [])}:
            counts[key] = counts.get(key, 0) + 1
    return {key: n / len(done) for key, n in counts.items()}


# ---------------------------------------------------------------- result file (design D6)
def sensitivityPath(config):
    return os.path.join(config['pathProjects'] + config['projectName'], 'versions', config['versionName'], RESULT_FILE)


def saveAnalysis(config, analysis):
    with open(sensitivityPath(config), 'w', encoding='utf-8') as f:
        json.dump(analysis, f, indent=1, default=str)


def loadAnalysis(config):
    path = sensitivityPath(config)
    if not os.path.exists(path):
        return None
    with open(path, encoding='utf-8') as f:
        return json.load(f)
