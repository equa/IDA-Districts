# coding=utf-8
"""Cost data and economics of the network (OpenSpec change network-cost-data): price levels, price curves, the
electricity profile, net present value and annuity, heat flow per pipe, example values. No database."""
import math

import pytest

from districts.utility_functions.economic_data import (
    BASE_PRICE_CURVES, BASE_TRENCH_COSTS, KWW_MATERIAL_PAIR, examplePipeCosts,
)
from districts.utility_functions.economics import (
    annuityFactor, curvePrice, level, netPresentValue, normalizedProfile, npvTerms, purchaseYears, readProfile,
    trenchCostPerMetre, yearlyEnergyCosts,
)
from districts.utility_functions.pipe_losses import (
    AMBIENT_AIR, AMBIENT_DUCT, AMBIENT_GROUND, ambientTemperature, checkLines, kusuda, sequenceModes, uPrime,
)


def scenario(interest=0.0, period=40, residual=True, escalation=0.0, levels=None, el=0.25):
    groups = {g: {'cost_group': g, 'start_price': el if g == 'electricity' else None, 'escalation_pct': escalation}
              for g in ('electricity', 'heat', 'cold', 'maintenance', 'investment')}
    return {'scenario': {'interest_pct': interest, 'period_a': period, 'residual_value': residual, 'default_surface': 'paved',
                         'pump_costs_eur7kw': 100, 'example': True},
            'groups': groups, 'levels': levels or {}, 'curves': {'heat': [(70, 0.10), (95, 0.139)], 'cold': [(6, 0.0625)]},
            'trench': {'paved': (155, 9.4), 'unpaved': (120, 5.5)}}


# ---------------------------------------------------------------- prices
def test_escalation_and_level_table():
    sc = scenario(escalation=2.0, levels={'electricity': {5: 1.5}})
    assert level(sc, 'electricity', 10) == pytest.approx(1.02 ** 10)
    assert level(sc, 'electricity', 5) == 1.5
    assert level(sc, 'electricity', 4) == pytest.approx(1.02 ** 4)


def test_price_curve():
    points = [(70, 0.08), (95, 0.11)]
    assert curvePrice(points, 80) == pytest.approx(0.092)
    assert curvePrice(points, 60) == 0.08 and curvePrice(points, 120) == 0.11
    assert curvePrice([(6, 0.05)], 30) == 0.05
    assert curvePrice([], 30) is None


def test_profile(tmp_path):
    values = [2.0] * 876 + [8.0 / 9] * 7884  # 10 % of the hours at twice the mean
    shape = normalizedProfile(values)
    assert sum(shape) / len(shape) == pytest.approx(1.0)
    assert shape[0] == pytest.approx(2 * shape[-1] * 9 / 8)
    with pytest.raises(ValueError) as error:
        normalizedProfile([1.0] * 8000)
    assert error.value.args == (8000,)
    path = tmp_path / 'profile.csv'
    path.write_text('hour;price\n' + '\n'.join('{};{}'.format(h, 0.2) for h in range(8760)), encoding='utf-8')
    assert len(readProfile(str(path))) == 8760


def test_profile_prices_the_expensive_hours():
    sc = scenario(el=0.2)
    shape = [2.0] + [1.0] * 8759
    costs, energy = yearlyEnergyCosts(sc, [{'weight': 1.0, 'hour': 0, 'p_pump': 1000.0}, {'weight': 1.0, 'hour': 1, 'p_pump': 1000.0}], shape)
    assert energy['pump_kwh'] == pytest.approx(2.0)
    assert costs['pump_energy'] == pytest.approx(0.2 * 2 + 0.2 * 1)


# ---------------------------------------------------------------- net present value
def test_purchase_years():
    assert purchaseYears(15, 40) == [0, 15, 30]
    assert purchaseYears(40, 40) == [0]
    assert purchaseYears(0, 40) == [0]


def test_pump_replacement_and_residual_value():
    sc = scenario(period=40)
    result = netPresentValue(sc, [{'cost': 1500.0, 'lifetime': 15, 'maintenance_pct': 0}], {})
    assert result['split']['investment'] == pytest.approx(3 * 1500)
    # the pumps of year 30 keep 5/15 of their cost at the end
    assert result['split']['residual'] == pytest.approx(-1500 * 5 / 15)


def test_npv_without_interest():
    sc = scenario(period=40)
    pipes = {'cost': 100000.0, 'lifetime': 40, 'maintenance_pct': 1.0}
    pumps = {'cost': 2000.0, 'lifetime': 15, 'maintenance_pct': 2.5}
    yearly = {'pump_energy': 500.0, 'heat_losses': 3000.0, 'cold_losses': 0.0}
    result = netPresentValue(sc, [pipes, pumps], yearly)
    expected = (100000 + 2000) + 40 * (500 + 3000 + 1000 + 50) + 2 * 2000 - 2000 * 5 / 15
    assert result['npv'] == pytest.approx(expected)
    assert result['annuity'] == pytest.approx(expected / 40)


def test_discounting_and_annuity():
    sc = scenario(interest=3.0, period=20, residual=False)
    result = netPresentValue(sc, [], {'pump_energy': 1000.0})
    assert result['npv'] == pytest.approx(sum(1000 / 1.03 ** t for t in range(1, 21)))
    assert annuityFactor(3.0, 20) == pytest.approx(0.03 * 1.03 ** 20 / (1.03 ** 20 - 1))
    assert result['annuity'] == pytest.approx(1000.0)


def test_npv_terms_add_up_to_the_split():
    """the report's terms base x factor give the parts of netPresentValue, with interest, escalation, a level table and residual value"""
    sc = scenario(interest=2.5, period=30, escalation=1.5, levels={'electricity': {1: 1.2, 2: 1.1}})
    items = [{'kind': 'pipe', 'name': 'DN 50', 'cost': 80000.0, 'lifetime': 40, 'maintenance_pct': 1.0, 'length': 400.0},
             {'kind': 'trench', 'name': 'paved', 'cost': 120000.0, 'lifetime': 40, 'maintenance_pct': 0.0, 'length': 200.0},
             {'kind': 'pumps', 'name': 'pumps', 'cost': 3000.0, 'lifetime': 15, 'maintenance_pct': 2.5, 'power_kw': 30.0}]
    yearly = {'pump_energy': 700.0, 'heat_losses': 4000.0, 'cold_losses': -50.0}
    split = netPresentValue(sc, items, yearly)['split']
    terms = npvTerms(sc, items, yearly)
    for group, value in split.items():
        assert sum(t['value'] for t in terms if t['group'] == group) == pytest.approx(value), group
    assert all(t['value'] == pytest.approx(t['base'] * t['factor']) for t in terms)
    pumps = [t for t in terms if t.get('kind') == 'pumps' and t['group'] == 'investment'][0]
    assert pumps['years'] == [0, 15] and pumps['power_kw'] == 30.0


def test_ground_gain_lowers_the_cost():
    sc = scenario()
    costs, _ = yearlyEnergyCosts(sc, [{'weight': 1.0, 'q_heat': -1000.0, 't_heat': 70}])
    assert costs['heat_losses'] < 0
    # heat entering a cooling pipe is a load
    costs, _ = yearlyEnergyCosts(sc, [{'weight': 1.0, 'q_cold': -1000.0, 't_cold': 6}])
    assert costs['cold_losses'] == pytest.approx(0.0625)
    # a warm and a cold pipe of a low-temperature pair in one hour: given off and taken up shown apart, the net prices
    costs, energy = yearlyEnergyCosts(sc, [{'weight': 1.0, 'q_heat': 200.0, 'q_heat_out': 1000.0, 't_heat': 70}])
    assert energy['heat_out_kwh'] == pytest.approx(1.0) and energy['heat_in_kwh'] == pytest.approx(-0.8)
    assert energy['heat_out_eur'] + energy['heat_in_eur'] == pytest.approx(costs['heat_losses']) == pytest.approx(0.02)


def test_trench_costs():
    sc = scenario()
    assert 100 * trenchCostPerMetre(sc, 'paved', 100) == pytest.approx(109500)
    assert trenchCostPerMetre(sc, 'gravel', 100) == trenchCostPerMetre(sc, 'paved', 100)  # unknown -> default surface


# ---------------------------------------------------------------- heat flow per pipe
def test_u_prime_of_a_buried_pipe():
    # DN100 KMR: steel 3.6 mm (55.2), PUR 40 mm (0.027), PE 3 mm (0.4), 1 m deep, soil 1.2 W/(m K)
    layers = [(0.0036, 55.2), (0.04, 0.027), (0.003, 0.4)]
    r = [0.1071 / 2]
    for thickness, _ in layers:
        r.append(r[-1] + thickness)
    resistance = sum(math.log(r[k + 1] / r[k]) / (2 * math.pi * lam) for k, (_, lam) in enumerate(layers))
    resistance += math.log(4 * 1.0 / (2 * r[-1])) / (2 * math.pi * 1.2)
    u = uPrime(0.1071, layers, 1.0, AMBIENT_GROUND, 1.2)
    assert u == pytest.approx(1 / resistance)
    assert 0.2 < u < 0.4
    assert uPrime(0.1071, layers, 1.0, AMBIENT_AIR, 1.2) > u * 0.9  # in air the outer resistance is smaller


def test_ambient_temperatures():
    settings = {'ground_model': 'Kusuda', 'kusuda_tsurfmean': '6.17', 'kusuda_tsurfampl': '3.31', 'kusuda_theta': '62.42',
                'kusuda_rho': '1387', 'kusuda_cp': '1344', 'kusuda_lambda': '1.18', 'kusuda_depth': '1', 'duct_temp': '20', 'ground_temp': '10'}
    year = [kusuda(day, settings) for day in range(365)]
    assert min(year) > 6.17 - 3.31 and max(year) < 6.17 + 3.31 and sum(year) / 365 == pytest.approx(6.17, abs=0.01)
    assert ambientTemperature(AMBIENT_DUCT, 10, settings) == 20
    assert ambientTemperature(AMBIENT_GROUND, 10, {'ground_model': 'Constant', 'ground_temp': '12'}) == 12


def test_modes_by_pair():
    connections = [{'conn_seq': 1, 'type': 1, 'temp': 70}, {'conn_seq': 2, 'type': 1, 'temp': 10},
                   {'conn_seq': 3, 'type': 2, 'temp': 30}, {'conn_seq': 4, 'type': 2, 'temp': 18}]
    assert sequenceModes(connections) == {1: 'heat', 3: 'heat', 2: 'cold', 4: 'cold'}


def test_check_against_the_simulated_loss():
    assert checkLines({1: 100.0, 2: 100.0}, {1: 110.0, 2: 130.0}) == {2: (100.0, 130.0)}


# ---------------------------------------------------------------- example values
def test_example_values():
    assert examplePipeCosts(100) == KWW_MATERIAL_PAIR[100] / 2
    assert examplePipeCosts(400) == pytest.approx((23 + 3.05 * 400) / 2, abs=0.1)
    assert {s for s, *_ in BASE_TRENCH_COSTS} == {'paved', 'unpaved'}
    assert {m for m, *_ in BASE_PRICE_CURVES} == {'heat', 'cold'}


# ---------------------------------------------------------------- pipe bundles of older projects
def test_import_of_bundles_without_their_costs():
    # resources exported from a project before the removal of invest_costs / operation_costs
    from districts.ida_resources import withoutBundleCostColumns
    old = "INSERT INTO pipe_bundle_types (invest_costs,operation_costs,description) VALUES (NULL,12.5,'2 pipes: 1, 2; 0.8 m depth');"
    assert withoutBundleCostColumns(old) == "INSERT INTO pipe_bundle_types (description) VALUES ('2 pipes: 1, 2; 0.8 m depth');"
    new = "INSERT INTO pipe_bundle_types (description) VALUES ('it''s new');"
    assert withoutBundleCostColumns(new) == new
