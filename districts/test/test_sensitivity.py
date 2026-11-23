# coding=utf-8
"""Sensitivity analysis of the cost optimization (OpenSpec change cost-sensitivity): parameter rows, variant designs,
overrides, statistics (unit tests)."""
import pytest

from districts.utility_functions.economics import netPresentValue
from districts.utility_functions.sensitivity import (
    applyOverrides, boundValue, correlations, designVariants, flips, parameterRows, robustness, spearman, tornado, variantCount,
    variantParameters, variedBounds,
)


def scenario():
    groups = {'electricity': {'cost_group': 'electricity', 'start_price': 0.25, 'escalation_pct': 2.0},
              'investment': {'cost_group': 'investment', 'start_price': None, 'escalation_pct': 2.0},
              'heat': {'cost_group': 'heat', 'start_price': None, 'escalation_pct': 2.0}}
    return {'scenario': {'interest_pct': 3.0, 'period_a': 40, 'residual_value': True, 'pump_costs_eur7kw': 100.0, 'default_surface': 'paved'},
            'groups': groups, 'levels': {}, 'curves': {'heat': [(70, 0.10), (95, 0.14)]}, 'trench': {'paved': (155.0, 9.4)}}


PARMS = {'price_kh': 1.0, 'price_kwh': 0.5, 'dp_spez_max': 300.0, 'v_max': 3.0}


def test_rows_with_base_values():
    rows = {r['key']: r for r in parameterRows(scenario(), PARMS)}
    assert rows['interest_pct']['base'] == 3.0 and rows['period_a']['base'] == 40
    assert rows['price:electricity']['base'] == 0.25 and rows['price:heat']['base'] == 1.0
    # no start price, no curve: not offered
    assert 'price:fuel' not in rows and 'price:cold' not in rows
    assert rows['escalation:investment']['base'] == 2.0 and rows['factor:pipe']['base'] == 1.0
    assert rows['dp_spez_max']['base'] == 300.0 and rows['v_max']['base'] == 3.0


def test_relative_and_absolute_bounds():
    assert boundValue(3.0, 'rel', -50) == pytest.approx(1.5) and boundValue(3.0, 'rel', 50) == pytest.approx(4.5)
    assert boundValue(3.0, 'abs', 5) == 5.0
    bounds = variedBounds([{'key': 'period_a', 'base': 40.0, 'mode': 'rel', 'minus': -33, 'plus': 10}])
    assert bounds['period_a'] == (40.0, 27.0, 44.0)  # whole years


def test_one_at_a_time_and_combinations():
    bounds = {'interest_pct': (3.0, 1.5, 4.5), 'price:electricity': (0.25, 0.2, 0.35)}
    variants = designVariants(bounds)
    assert len(variants) == 5 == variantCount(2, 'one_at_a_time', 0)
    assert variants[0] == {'name': 'base', 'values': {'interest_pct': 3.0, 'price:electricity': 0.25}}
    assert {'name': 'interest_pct +', 'values': {'interest_pct': 4.5, 'price:electricity': 0.25}} in variants
    combos = designVariants(bounds, 'combinations')
    assert len(combos) == 9 == variantCount(2, 'combinations', 0)
    assert len({tuple(sorted(v['values'].items())) for v in combos}) == 9


def test_sample_is_reproducible_and_stratified():
    bounds = {'interest_pct': (3.0, 1.0, 5.0), 'period_a': (40.0, 20.0, 50.0)}
    first, second = designVariants(bounds, 'sample', 20, seed=7), designVariants(bounds, 'sample', 20, seed=7)
    assert first == second and len(first) == 21 == variantCount(2, 'sample', 20)
    assert designVariants(bounds, 'sample', 20, seed=8) != first
    # one value in each fifth of the range per 5 strata
    values = sorted(v['values']['interest_pct'] for v in designVariants(bounds, 'sample', 5, seed=1)[1:])
    assert all(1.0 + 0.8 * k <= value <= 1.0 + 0.8 * (k + 1) for k, value in enumerate(values))
    assert all(float(v['values']['period_a']).is_integer() for v in first)


def test_overrides_leave_the_scenario_unchanged():
    base = scenario()
    changed = applyOverrides(base, {'interest_pct': 5.0, 'period_a': 30.0, 'price:electricity': 0.3, 'price:heat': 2.0,
                                    'escalation:investment': 0.0, 'factor:trench': 1.5, 'factor:pumps': 0.5, 'factor:pipe': 1.2})
    assert base == scenario()
    sc = changed['scenario']
    assert sc['interest_pct'] == 5.0 and sc['period_a'] == 30 and sc['pump_costs_eur7kw'] == 50.0
    assert changed['groups']['electricity']['start_price'] == 0.3 and changed['groups']['investment']['escalation_pct'] == 0.0
    assert changed['curves']['heat'] == [(70, pytest.approx(0.20)), (95, pytest.approx(0.28))]
    assert changed['trench']['paved'] == (pytest.approx(232.5), pytest.approx(14.1)) and changed['cost_factors']['pipe'] == 1.2
    # the NPV follows the overridden interest as netPresentValue does
    items = [{'cost': 1000.0, 'lifetime': 40, 'maintenance_pct': 0.0}]
    assert netPresentValue(changed, items, {})['npv'] == pytest.approx(netPresentValue(dict(base, scenario=dict(base['scenario'], interest_pct=5.0, period_a=30)), items, {})['npv'])
    assert applyOverrides(base, {}) is base


def test_variant_parameters_split_run_and_scenario_values():
    parms = variantParameters(dict(PARMS, scenario=1), {'interest_pct': 5.0, 'dp_spez_max': 200.0, 'price_kh': 2.0})
    assert parms['overrides'] == {'interest_pct': 5.0} and parms['dp_spez_max'] == 200.0 and parms['price_kh'] == 2.0
    assert parms['scenario'] == 1 and PARMS['dp_spez_max'] == 300.0


def test_spearman():
    assert spearman([1, 2, 3, 4], [10, 20, 30, 40]) == pytest.approx(1.0)
    assert spearman([1, 2, 3, 4], [4, 3, 2, 1]) == pytest.approx(-1.0)
    assert spearman([1, 1, 1], [1, 2, 3]) == 0.0
    assert spearman([1, 2, 2, 3], [1, 2, 2, 3]) == pytest.approx(1.0)  # ties


def analysis():
    change = {'version': 'v', 'line': 114, 'before': [5], 'after': [4], 'larger': False}
    variants = [{'name': 'base', 'values': {'interest_pct': 3.0, 'price:electricity': 0.25}, 'result': {'npv': 100.0, 'npv_after': 100.0, 'changes': []}},
                {'name': 'interest_pct -', 'values': {'interest_pct': 1.5, 'price:electricity': 0.25}, 'result': {'npv': 120.0, 'npv_after': 118.0, 'changes': []}},
                {'name': 'interest_pct +', 'values': {'interest_pct': 4.5, 'price:electricity': 0.25}, 'result': {'npv': 90.0, 'npv_after': 85.0, 'changes': [change]}},
                {'name': 'price:electricity -', 'values': {'interest_pct': 3.0, 'price:electricity': 0.2}, 'result': {'npv': 98.0, 'npv_after': 98.0, 'changes': []}},
                {'name': 'price:electricity +', 'values': {'interest_pct': 3.0, 'price:electricity': 0.35}, 'result': {'npv': 104.0, 'npv_after': 104.0, 'changes': []}}]
    return {'design': 'one_at_a_time', 'bounds': {'interest_pct': [3.0, 1.5, 4.5], 'price:electricity': [0.25, 0.2, 0.35]}, 'variants': variants}


def test_tornado_flips_and_robustness():
    result = analysis()
    assert tornado(result) == [('interest_pct', 118.0, 85.0), ('price:electricity', 98.0, 104.0)]
    assert flips(result) == {('v', 114): {'before': [5], 'after': {'interest_pct +': [4]}}}
    assert robustness(result) == {('v', 114): pytest.approx(0.25)}
    ranked = correlations(result)
    assert ranked[0][0] == 'interest_pct' and ranked[0][1] < 0
    assert tornado(dict(result, design='sample')) == []


def test_base_variant_changing_a_line():
    """the estimate's base variant makes a step too (a run stopped by its iteration limit): its change is listed like the
    others, and the robustness counts only the varied variants"""
    result = analysis()
    result['variants'][0]['result']['changes'] = [{'version': 'v', 'line': 114, 'before': [5], 'after': [6], 'larger': True}]
    assert flips(result)[('v', 114)] == {'before': [5], 'after': {'base': [6], 'interest_pct +': [4]}}
    assert robustness(result) == {('v', 114): pytest.approx(0.25)}
