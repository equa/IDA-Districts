# coding=utf-8
"""Energy costs of the plants and customers from the energy-use results (OpenSpec change plant-energy-costs, D5, D6):
the yearly cost of year 0 per part and carrier, and per step and supply/return pair the marginal price of a kWh of
pipe loss: the most expensive plant putting heat into (heating) or taking heat from (cooling) the pair above a share
of its peak heat flow."""
import numpy as np

from .economics import electricityStartPrice
from .energy_use import DELIVERED, FREE_CARRIERS

ENERGY_TABLES = {'energy_plant': 'energy_plant_s_energy', 'customer': 'customer_s_energy'}
PARTS = {'energy_plant': 'plant_energy', 'customer': 'customer_energy'}


def _exists(cur, schema, table):
    cur.execute("SELECT to_regclass(%s) IS NOT NULL AS ok;", ('"{}"."{}"'.format(schema, table),))
    return cur.fetchone()['ok']


def energySeries(cur, schema, sources, index, n):
    """{(feature, fid, carrier): power [W] per step} of the energy tables; {} without energy results"""
    series: dict = {}
    for feature, table in ENERGY_TABLES.items():
        for source in sources(table):
            if not _exists(cur, schema, source):
                continue
            cur.execute('SELECT fid, carrier, time, sum("$energy") AS e FROM "{}"."{}" GROUP BY fid, carrier, time;'.format(schema, source))  # nosec B608
            for row in cur.fetchall():
                k = index.get(row['time'])
                if k is not None and row['e'] is not None:
                    arr = series.setdefault((feature, row['fid'], row['carrier']), np.zeros(n))
                    arr[k] += float(row['e'])
    return series


def carrierPrice(scenario, carrier):
    """start price [€/kWh] of the carrier's price group, None without a price; a free carrier (ambient) costs 0
    unless the scenario prices it"""
    if carrier == 'electricity':
        return electricityStartPrice(scenario) or None
    value = (scenario.get('groups', {}).get(carrier) or {}).get('start_price')
    if value is None:
        return 0.0 if carrier in FREE_CARRIERS else None
    return float(value)


def stepPrices(scenario, carrier, shape, n):
    """price per step [€/kWh]: electricity with the hourly profile (shape), the other carriers flat; zeros without a price"""
    price = carrierPrice(scenario, carrier)
    if price is None:
        return np.zeros(n)
    if carrier == 'electricity' and shape is not None:
        return price * np.asarray(shape, dtype=float)
    return np.full(n, price)


def energyCosts(series, scenario, weights, shape, boundary):
    """yearly costs of year 0 from the energy series: {'yearly': {part: {carrier: €}}, 'info': {part: {carrier: €}}
    (customers with the operator boundary), 'kwh': {part: {carrier: kWh}}, 'features': [(feature, fid, carrier, kWh, €)],
    'no_price': [carriers in use without a price]}; weights per step [h/a]"""
    w = np.asarray(weights, dtype=float)
    n = len(w)
    result: dict = {'yearly': {}, 'info': {}, 'kwh': {}, 'features': [], 'no_price': [], 'delivered': {'heat': 0.0, 'cold': 0.0}}
    for (feature, fid, carrier), power in sorted(series.items(), key=lambda item: (item[0][0], item[0][1], item[0][2])):
        if carrier == DELIVERED:
            # not bought: kWh of heat (> 0) and cold (< 0) delivered, for the key figures
            result['delivered']['heat'] += float(np.sum(w * np.maximum(power, 0)) / 1000)
            result['delivered']['cold'] += float(np.sum(w * np.maximum(-power, 0)) / 1000)
            continue
        kwh = float(np.sum(w * power) / 1000)
        eur = float(np.sum(w * power / 1000 * stepPrices(scenario, carrier, shape, n)))
        if carrierPrice(scenario, carrier) is None and carrier not in result['no_price'] and kwh:
            result['no_price'].append(carrier)
        part = PARTS[feature]
        target = 'info' if feature == 'customer' and boundary != 'system' else 'yearly'
        result[target].setdefault(part, {})
        result[target][part][carrier] = result[target][part].get(carrier, 0.0) + eur
        result['kwh'].setdefault(part, {})
        result['kwh'][part][carrier] = result['kwh'][part].get(carrier, 0.0) + kwh
        result['features'].append((feature, fid, carrier, kwh, eur))
    return result


def pairHeat(plant_flows, fid, s, r, n):
    """heat [W] a plant puts into the pair per step (cooling: negative); one connection's c_p * mdot * T alone is an
    enthalpy flow, only supply plus return is heat"""
    return plant_flows.get((fid, s), np.zeros(n)) + plant_flows.get((fid, r), np.zeros(n))


def plantSpecificCosts(series, scenario, shape, plant_flows, pairs, n):
    """{fid: (energy cost per step [€/h], |heat| per step [W] over all pairs)} of the plants with energy entries"""
    costs: dict = {}
    for (feature, fid, carrier), power in series.items():
        if feature != 'energy_plant' or carrier == DELIVERED:
            continue
        costs[fid] = costs.get(fid, np.zeros(n)) + power / 1000 * stepPrices(scenario, carrier, shape, n)
    return {fid: (cost, sum((np.abs(pairHeat(plant_flows, fid, s, r, n)) for s, r, _ in pairs), np.zeros(n))) for fid, cost in costs.items()}


def marginalPrices(pairs, plant_flows, specific, masks, threshold_pct, n):
    """{(supply, return): (price [€/kWh] per step or NaN, marginal plant fid per step or -1)}: per step the plants whose
    heat flow of the pair is in the direction of the pair's mode (into the network when heating, out when cooling) and
    above threshold_pct of its peak; the highest energy cost per kWh of heat among them"""
    result = {}
    for s, r, _ in pairs:
        price = np.full(n, np.nan)
        plant = np.full(n, -1)
        heat = masks.get(s)
        heat = np.full(n, heat == 'heat') if isinstance(heat, str) or heat is None else np.asarray(heat, dtype=bool)
        for fid, (cost, total) in specific.items():
            phi = pairHeat(plant_flows, fid, s, r, n)
            peak = float(np.max(np.abs(phi))) if n else 0.0
            if not peak:
                continue
            running = np.where(heat, phi, -phi) > threshold_pct / 100 * peak
            spec = np.divide(cost, total / 1000, out=np.full(n, np.nan), where=total > 0)
            better = running & ~np.isnan(spec) & (np.isnan(price) | (spec > price))
            price = np.where(better, spec, price)
            plant = np.where(better, fid, plant)
        result[(s, r)] = (price, plant)
    return result
