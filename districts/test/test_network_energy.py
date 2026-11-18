# coding=utf-8
"""Energy costs per carrier and the marginal price of a pipe loss (OpenSpec change plant-energy-costs, D5, D6)."""
import numpy as np
import pytest

from districts.utility_functions.network_energy import energyCosts, marginalPrices, plantSpecificCosts


def scenario(fuel=0.08, el=0.25):
    groups = {'electricity': {'start_price': el}, 'fuel': {'start_price': fuel}, 'purchased_heat': {'start_price': None}}
    return {'scenario': {}, 'groups': groups, 'levels': {}, 'curves': {}, 'trench': {}}


def test_plant_energy_cost_of_year_0():
    # one step weighted 1000 h: 100 kW fuel = 100 MWh at 0.08 €/kWh, 50 kW electricity = 50 MWh at 0.25 €/kWh
    series = {('energy_plant', 1, 'fuel'): np.array([100000.0]), ('energy_plant', 2, 'electricity'): np.array([50000.0])}
    costs = energyCosts(series, scenario(), [1000.0], None, 'operator')
    assert sum(costs['yearly']['plant_energy'].values()) == pytest.approx(20500.0)
    assert costs['kwh']['plant_energy'] == {'fuel': pytest.approx(100000.0), 'electricity': pytest.approx(50000.0)}
    assert not costs['no_price']


def test_customers_by_system_boundary_and_missing_price():
    series = {('customer', 7, 'electricity'): np.array([1000.0, 3000.0]), ('energy_plant', 1, 'purchased_heat'): np.array([500.0, 500.0])}
    shape = [0.5, 1.5]  # the electricity profile of the two steps
    operator = energyCosts(series, scenario(), [1.0, 1.0], shape, 'operator')
    assert 'customer_energy' not in operator['yearly'] and operator['info']['customer_energy']['electricity'] == pytest.approx((0.5 + 4.5) * 0.25)
    system = energyCosts(series, scenario(), [1.0, 1.0], shape, 'system')
    assert system['yearly']['customer_energy']['electricity'] == pytest.approx(1.25)
    assert system['no_price'] == ['purchased_heat']


def flows(values):
    """plant heat flows: all on the supply connection 1 of the pair (1, 2)"""
    return {(fid, 1): np.array(v) for fid, v in values.items()}


def test_marginal_plant_above_the_threshold():
    # heat pump (fid 1): 100 kW of heat for 24 kW electricity = 6 €/h -> 0.06 €/kWh; boiler (fid 2): 0.11 €/kWh,
    # 50 kW in step 0, 1.5 kW (3 % of its peak) in step 1
    series = {('energy_plant', 1, 'electricity'): np.array([24000.0, 24000.0]),
              ('energy_plant', 2, 'fuel'): np.array([68750.0, 2062.5])}
    plant_flows = flows({1: [100000.0, 100000.0], 2: [50000.0, 1500.0]})
    pairs = [(1, 2, 'heat')]
    specific = plantSpecificCosts(series, scenario(), None, plant_flows, pairs, 2)
    price, plant = marginalPrices(pairs, plant_flows, specific, {1: 'heat', 2: 'heat'}, 5.0, 2)[(1, 2)]
    assert price.tolist() == pytest.approx([0.11, 0.06]) and plant.tolist() == [2, 1]


def test_cooling_step_takes_the_plant_extracting_heat():
    series = {('energy_plant', 3, 'electricity'): np.array([10000.0])}
    plant_flows = flows({3: [-40000.0]})  # a chiller takes 40 kW out of the network for 10 kW electricity
    pairs = [(1, 2, 'cold')]
    specific = plantSpecificCosts(series, scenario(), None, plant_flows, pairs, 1)
    price, plant = marginalPrices(pairs, plant_flows, specific, {1: np.array([False]), 2: np.array([False])}, 5.0, 1)[(1, 2)]
    assert price[0] == pytest.approx(10 * 0.25 / 40) and plant[0] == 3
    # in a heating step the chiller is not running for the pair: no marginal plant
    price, plant = marginalPrices(pairs, plant_flows, specific, {1: 'heat', 2: 'heat'}, 5.0, 1)[(1, 2)]
    assert np.isnan(price[0]) and plant[0] == -1


def test_ambient_energy_is_free_unless_priced():
    series = {('energy_plant', 4, 'ambient'): np.array([200000.0])}  # a borehole field: 200 kW from the ground for 1000 h
    costs = energyCosts(series, scenario(), [1000.0], None, 'operator')
    assert costs['kwh']['plant_energy']['ambient'] == pytest.approx(200000.0)
    assert costs['yearly']['plant_energy']['ambient'] == 0 and not costs['no_price']
    priced = scenario()
    priced['groups']['ambient'] = {'start_price': 0.01}  # e.g. a fee for the ground water
    assert energyCosts(series, priced, [1000.0], None, 'operator')['yearly']['plant_energy']['ambient'] == pytest.approx(2000.0)


def test_delivered_energy_is_neither_bought_nor_priced():
    # a substation's heat exchanger: 30 kW of heat in step 0, 20 kW of cooling (negative) in step 1, 1000 h each
    series = {('customer', 7, 'delivered'): np.array([30000.0, -20000.0]), ('energy_plant', 1, 'fuel'): np.array([10000.0, 10000.0])}
    costs = energyCosts(series, scenario(), [1000.0, 1000.0], None, 'system')
    assert costs['delivered'] == {'heat': pytest.approx(30000.0), 'cold': pytest.approx(20000.0)}
    assert 'customer_energy' not in costs['yearly'] and 'delivered' not in costs['no_price']
    assert all(carrier != 'delivered' for _, _, carrier, _, _ in costs['features'])
    # a plant entry of kind delivered does not make the plant marginal
    specific = plantSpecificCosts({('energy_plant', 2, 'delivered'): np.array([5000.0])}, scenario(), None, {}, [], 1)
    assert specific == {}
