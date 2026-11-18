# coding=utf-8
"""Net present value of a network over the amortization period of an economic scenario
(OpenSpec change network-cost-data). Pure Python: the scenario as returned by economic_data.loadScenario.

Cost groups of the result: investment (year 0 and replacements), pump_energy, heat_losses, cold_losses, maintenance,
residual (negative). Yearly energy costs are given for year 0 and scaled with the level of their price group."""
import math

ENERGY_GROUPS = {'pump_energy': 'electricity', 'heat_losses': 'heat', 'cold_losses': 'cold'}
SPLIT = ('investment', 'pump_energy', 'heat_losses', 'cold_losses', 'maintenance', 'residual', 'plant_energy', 'customer_energy')
PROFILE_LENGTHS = (8760, 8784)


def level(scenario, group, year):
    """Price level of a cost group in a year relative to year 0: the price_levels factor, else (1 + escalation)^year."""
    factors = scenario.get('levels', {}).get(group, {})
    if year in factors:
        return factors[year]
    escalation = float((scenario.get('groups', {}).get(group) or {}).get('escalation_pct') or 0)
    return (1 + escalation / 100) ** year


def curvePrice(points, t):
    """Price of a curve [(t_supply, price)] at t: linear between the points, constant outside; None without points."""
    if not points:
        return None
    points = sorted(points)
    if t <= points[0][0]:
        return points[0][1]
    for (t0, p0), (t1, p1) in zip(points, points[1:]):
        if t <= t1:
            return p0 + (p1 - p0) * (t - t0) / (t1 - t0) if t1 > t0 else p1
    return points[-1][1]


def normalizedProfile(values):
    """Hourly profile scaled to mean 1; a profile of another length raises ValueError(number of values)."""
    if len(values) not in PROFILE_LENGTHS:
        raise ValueError(len(values))
    mean = sum(values) / len(values)
    if mean <= 0:
        raise ValueError(len(values))
    return [v / mean for v in values[:8760]]


def readProfile(path):
    """Values of a profile file (.csv or .prn): the last number of every line that has one."""
    values = []
    with open(path, encoding='utf-8-sig', errors='replace') as f:
        for line in f:
            fields = line.replace(';', ' ').replace(',', ' ').replace('\t', ' ').split()
            numbers = []
            for field in fields:
                try:
                    numbers.append(float(field))
                except ValueError:
                    pass
            if numbers:
                values.append(numbers[-1])
    return values


def electricityStartPrice(scenario):
    return float((scenario.get('groups', {}).get('electricity') or {}).get('start_price') or 0)


def annuityFactor(interest_pct, years):
    i = interest_pct / 100
    if years <= 0:
        return 0.0
    if i == 0:
        return 1 / years
    q = (1 + i) ** years
    return i * q / (q - 1)


def purchaseYears(lifetime, period):
    """Years in which an item is bought: 0 and every multiple of its lifetime within the period."""
    if not lifetime or lifetime <= 0:
        return [0]
    return [k * lifetime for k in range(int(math.ceil(period / lifetime))) if k * lifetime < period] or [0]


def netPresentValue(scenario, investments, yearly, by_carrier=None):
    """investments: [{'cost': €, 'lifetime': a, 'maintenance_pct': %/a}] bought in year 0 and replaced at the end of their
    lifetime; yearly: {'pump_energy'|'heat_losses'|'cold_losses': € of year 0} (signed); by_carrier: {'plant_energy'|
    'customer_energy': {carrier: € of year 0}}, each carrier with the level of its price group (plant-energy-costs D5).
    Returns {'npv', 'annuity', 'split': {group: €}, 'years': [{year: €}] undiscounted per year}."""
    sc = scenario['scenario']
    i = float(sc.get('interest_pct') or 0) / 100
    period = int(sc.get('period_a') or 0)
    residual = bool(sc.get('residual_value'))
    split = {key: 0.0 for key in SPLIT}
    years = [0.0] * (period + 1)

    def add(group, year, amount):
        split[group] += amount / (1 + i) ** year
        years[year] += amount

    for item in investments:
        cost, lifetime = float(item.get('cost') or 0), float(item.get('lifetime') or 0)
        buys = purchaseYears(lifetime, period)
        for year in buys:
            add('investment', int(year), cost * level(scenario, 'investment', int(year)))
        maintenance = cost * float(item.get('maintenance_pct') or 0) / 100
        for year in range(1, period + 1):
            add('maintenance', year, maintenance * level(scenario, 'maintenance', year))
        if residual and lifetime > 0:
            last = int(buys[-1])
            remaining = (last + lifetime - period) / lifetime
            if remaining > 0:
                add('residual', period, -cost * level(scenario, 'investment', last) * remaining)
    for group, price_group in ENERGY_GROUPS.items():
        amount = float(yearly.get(group) or 0)
        for year in range(1, period + 1):
            add(group, year, amount * level(scenario, price_group, year))
    for part, carriers in (by_carrier or {}).items():
        for carrier, amount in carriers.items():
            for year in range(1, period + 1):
                add(part, year, float(amount or 0) * level(scenario, carrier, year))
    npv = sum(split.values())
    return {'npv': npv, 'annuity': npv * annuityFactor(i * 100, period), 'split': split, 'years': years}


def presentValueFactor(scenario, group, years):
    """sum over the years of the group's price level, discounted: sum L_g(t) / (1 + i)^t"""
    i = float(scenario['scenario'].get('interest_pct') or 0) / 100
    return sum(level(scenario, group, int(t)) / (1 + i) ** t for t in years)


def npvTerms(scenario, investments, yearly, by_carrier=None):
    """the parts of netPresentValue as terms base x factor = value, for the report: [{'group', 'kind', 'name', 'base',
    'factor', 'value', ...}]; their sum per group is the split of netPresentValue"""
    sc = scenario['scenario']
    i = float(sc.get('interest_pct') or 0) / 100
    period = int(sc.get('period_a') or 0)
    years = range(1, period + 1)
    terms = []
    for item in investments:
        cost, lifetime = float(item.get('cost') or 0), float(item.get('lifetime') or 0)
        info = {k: item[k] for k in ('kind', 'name', 'length', 'power_kw') if k in item}
        buys = [int(t) for t in purchaseYears(lifetime, period)]
        terms.append(dict(info, group='investment', base=cost, factor=presentValueFactor(scenario, 'investment', buys), years=buys, lifetime=lifetime))
        maintenance_pct = float(item.get('maintenance_pct') or 0)
        if maintenance_pct:
            terms.append(dict(info, group='maintenance', base=cost * maintenance_pct / 100, factor=presentValueFactor(scenario, 'maintenance', years),
                              maintenance_pct=maintenance_pct))
        if sc.get('residual_value') and lifetime > 0:
            remaining = (buys[-1] + lifetime - period) / lifetime
            if remaining > 0:
                terms.append(dict(info, group='residual', base=cost, remaining=remaining, last=buys[-1],
                                  factor=-level(scenario, 'investment', buys[-1]) * remaining / (1 + i) ** period))
    for group, price_group in ENERGY_GROUPS.items():
        if by_carrier is not None and group != 'pump_energy':
            continue  # the energy of the plants replaces the priced pipe losses
        terms.append({'group': group, 'kind': price_group, 'name': price_group, 'base': float(yearly.get(group) or 0),
                      'factor': presentValueFactor(scenario, price_group, years)})
    for part, carriers in (by_carrier or {}).items():
        for carrier, amount in sorted(carriers.items()):
            terms.append({'group': part, 'kind': carrier, 'name': carrier, 'base': float(amount or 0),
                          'factor': presentValueFactor(scenario, carrier, years)})
    for term in terms:
        term['value'] = term['base'] * term['factor']
    return terms


def yearlyEnergyCosts(scenario, hours, shape=None):
    """Costs of year 0 of the simulated hours [{'weight', 'hour', 'p_pump' W, 'q_heat' W, 'q_cold' W,
    't_heat' °C, 't_cold' °C}]: q_heat = heat leaving the heating pipes, q_cold = heat leaving the cooling pipes
    (a gain of a cooling pipe is a load). shape: hourly electricity profile (mean 1), indexed by hour of the year;
    an hour with its own 'shape' (representative periods) uses that.
    Returns ({'pump_energy', 'heat_losses', 'cold_losses'} €, {'pump_kwh', 'heat_kwh', 'cold_kwh'})."""
    el = electricityStartPrice(scenario)
    curves = scenario.get('curves', {})
    costs = {'pump_energy': 0.0, 'heat_losses': 0.0, 'cold_losses': 0.0}
    energy = {'pump_kwh': 0.0, 'heat_kwh': 0.0, 'cold_kwh': 0.0}
    # the part given off by the pipes (q_<mode>_out >= 0) and the part taken up (the rest), with the same prices
    parts = {key: 0.0 for key in ('heat_out_kwh', 'heat_out_eur', 'cold_out_kwh', 'cold_out_eur')}
    for h in hours:
        w = h.get('weight', 1.0)
        if 'shape' in h:
            s = h['shape']
        else:
            s = shape[h['hour'] % len(shape)] if shape and h.get('hour') is not None else 1.0
        pump = w * h.get('p_pump', 0.0) / 1000
        costs['pump_energy'] += pump * el * s
        energy['pump_kwh'] += pump
        heat = w * h.get('q_heat', 0.0) / 1000
        energy['heat_kwh'] += heat
        heat_out = w * h.get('q_heat_out', max(h.get('q_heat', 0.0), 0.0)) / 1000
        price = curvePrice(curves.get('heat'), h.get('t_heat', 0.0)) or 0.0
        costs['heat_losses'] += heat * price
        parts['heat_out_kwh'] += heat_out
        parts['heat_out_eur'] += heat_out * price
        cold = w * h.get('q_cold', 0.0) / 1000
        energy['cold_kwh'] += cold
        cold_out = w * h.get('q_cold_out', max(h.get('q_cold', 0.0), 0.0)) / 1000
        price = curvePrice(curves.get('cold'), h.get('t_cold', 0.0)) or 0.0
        costs['cold_losses'] -= cold * price
        parts['cold_out_kwh'] += cold_out
        parts['cold_out_eur'] -= cold_out * price
    energy['heat_out_kwh'], energy['cold_out_kwh'] = parts['heat_out_kwh'], parts['cold_out_kwh']
    energy['heat_in_kwh'] = energy['heat_kwh'] - parts['heat_out_kwh']
    energy['cold_in_kwh'] = energy['cold_kwh'] - parts['cold_out_kwh']
    energy['heat_out_eur'], energy['cold_out_eur'] = parts['heat_out_eur'], parts['cold_out_eur']
    energy['heat_in_eur'] = costs['heat_losses'] - parts['heat_out_eur']
    energy['cold_in_eur'] = costs['cold_losses'] - parts['cold_out_eur']
    return costs, energy


def trenchCostPerMetre(scenario, surface, dn):
    """Civil works per trench metre: a + b * DN of the surface; the scenario's default surface if unknown."""
    trench = scenario.get('trench', {})
    a, b = trench.get(surface) or trench.get(scenario['scenario'].get('default_surface')) or (0.0, 0.0)
    return a + b * dn
