# coding=utf-8
"""Key figures of a version (OpenSpec change ai-mcp-connection, D9), computed by the functions the network report and
its Economics section use, so the AI connection and the reports show the same numbers."""
import os

from .db import getBuildingsEra, getNetworkLength, getNetworkVolume
from .network_economics import evaluateVersion, resultTables, tableExists

# derived KPIs of the network report: name -> (kpi_<network> column, divisor)
DERIVED = [('qsup_heat_spec_c', 'qsup_heat_c', 'era'), ('qsup_cold_spec_c', 'qsup_cold_c', 'era'), ('qsup_spec_c', 'qsup_c', 'era'),
           ('qsup_heat_density_c', 'qsup_heat_c', 'area'), ('qsup_cold_density_c', 'qsup_cold_c', 'area'), ('qsup_density_c', 'qsup_c', 'area'),
           ('qsup_heat_linedensity_c', 'qsup_heat_c', 'length'), ('qsup_cold_linedensity_c', 'qsup_cold_c', 'length'),
           ('qsup_linedensity_c', 'qsup_c', 'length')]


def networkKpis(cur, config, network, simulated_outputs, area):
    """[{name: value}] of the network report's KPI table: the columns of kpi_<network> and the derived values the
    simulated outputs ask for; area = plot area of the network extent [m2]"""
    cur.execute('SELECT * FROM "{}".kpi_{};'.format(config['versionName'], network))  # nosec B608
    kpi_table = cur.fetchone()
    kpis = [{i: float(kpi_table[i])} for i in kpi_table if kpi_table[i] is not None and i != 'id']
    divisors = {}
    for name, column, divisor in DERIVED:
        if simulated_outputs.get(name + '_kpi') and kpi_table.get(column) is not None:
            if divisor not in divisors:
                divisors[divisor] = {'era': lambda: getBuildingsEra(cur, config), 'area': lambda: area,
                                     'length': lambda: getNetworkLength(cur, config)}[divisor]()
            kpis.append({name: float(kpi_table[column]) / divisors[divisor]})
    if simulated_outputs.get('eff_width'):
        kpis.append({'eff_width': area / getNetworkLength(cur, config)})
    if simulated_outputs.get('volume_kpi'):
        kpis.append({'volume': getNetworkVolume(cur, config)})
    return kpis


def resultsBasis(cur, config):
    """'full_year', 'periods' or 'none' (and the simulated days) of the version's results"""
    from .network_economics import FULL_YEAR_DAYS, periodSources, timeSteps
    schema = config['versionName']
    temp_tables = resultTables(cur, schema, 'line_s_temp$')
    if not temp_tables:
        return {'basis': 'none', 'days': 0.0}
    times = timeSteps(cur, schema, temp_tables[0])
    days = (times[-1] - times[0]).total_seconds() / 86400 if len(times) > 1 else 0.0
    if days >= FULL_YEAR_DAYS:
        return {'basis': 'full_year', 'days': round(days, 1)}
    return {'basis': 'periods' if periodSources(cur, config) else 'simulated_period', 'days': round(days, 1)}


def _value(value, unit, reason=None):
    return {'value': value, 'unit': unit} if reason is None else {'value': None, 'unit': unit, 'reason': reason}


def versionKpis(cur, config, scenario_id=None, settings=None, profile_dir=None):
    """Key figures of the version config['versionName'] (D9); result figures are None with a reason without results."""
    from .files import loadSimulatedOutputs
    schema = config['versionName']
    cur.execute('SELECT network, sum(ST_Length(geom)) AS length, ST_XMax(ST_Extent(geom)) - ST_XMin(ST_Extent(geom)) AS w, '
                'ST_YMax(ST_Extent(geom)) - ST_YMin(ST_Extent(geom)) AS h FROM "{}".lines GROUP BY network ORDER BY network;'.format(schema))  # nosec B608
    rows = cur.fetchall()
    basis = resultsBasis(cur, config)
    try:
        simulated = loadSimulatedOutputs(config) or {}
    except Exception:
        simulated = {}
    networks = {}
    heat_total = 0.0
    for row in rows:
        network = row['network']
        length = float(row['length'] or 0)
        entry = {'length': _value(round(length, 1), 'm')}
        if tableExists(cur, schema, 'kpi_{}'.format(network)):
            kpis = {k: v for d in networkKpis(cur, config, network, simulated, float(row['w'] or 0) * float(row['h'] or 0)) for k, v in d.items()}
            entry['kpi'] = kpis
            heat = kpis.get('qsup_heat_c')
            if heat is not None:
                heat_total += heat
                entry['heat_delivered'] = _value(round(heat, 1), 'kWh')
                entry['linear_heat_density'] = _value(round(heat / length / 1000, 4) if length else None, 'MWh/m')
        else:
            entry['heat_delivered'] = _value(None, 'kWh', 'no KPI results (output kpi)')
        networks[str(network)] = entry
    out = {'version': schema, 'results_basis': basis, 'networks': networks,
           'network_length': _value(round(sum(float(r['length'] or 0) for r in rows), 1), 'm')}
    out.update(peakAndDeficits(cur, config))
    out['comfort_deficits'] = comfortDeficits(cur, config)
    if scenario_id is None:
        cur.execute('SELECT id FROM public.economic_scenarios ORDER BY id LIMIT 1;')
        row = cur.fetchone()
        scenario_id = row['id'] if row else None
    out['economics'] = economics(cur, config, scenario_id, settings or {}, profile_dir, heat_total)
    return out


def peakAndDeficits(cur, config):
    schema = config['versionName']
    tables = resultTables(cur, schema, 'customer_s_power$')
    if not tables:
        return {'peak_load': _value(None, 'kW', 'no customer power results (output power_c)')}
    union = ' UNION ALL '.join('SELECT time, "$power" AS p FROM "{}"."{}"'.format(schema, t) for t in tables)  # nosec B608
    cur.execute('SELECT max(s) AS peak FROM (SELECT time, sum(p) AS s FROM ({}) u GROUP BY time) x;'.format(union))  # nosec B608
    peak = cur.fetchone()['peak']
    return {'peak_load': _value(round(float(peak) / 1000, 1) if peak is not None else None, 'kW')}


def comfortDeficits(cur, config):
    """customers whose room temperature misses the setpoint, from the comfort rule of the model checks"""
    from .model_checks import CheckContext, ruleComfort
    findings = ruleComfort(CheckContext(cur, config))
    if findings and findings[0]['rule'] == 'outputs_missing':
        return {'value': None, 'unit': 'customers', 'reason': 'no room temperature results (output troom_c)'}
    return {'value': len(findings), 'unit': 'customers', 'degree_hours': round(sum(f['values']['value'] for f in findings), 1),
            'customers': [f['feature_id'] for f in findings][:50]}


def economics(cur, config, scenario_id, settings, profile_dir, heat_total):
    if scenario_id is None:
        return {'reason': 'no economic scenario'}
    evaluation = evaluateVersion(cur, config, scenario_id, settings, profile_dir=profile_dir)
    scenario = ((evaluation.get('scenario') or {}).get('scenario') or {}).get('name')
    if evaluation.get('missing'):
        return {'scenario': scenario, 'reason': 'results needed: ' + ', '.join(evaluation['missing'])}
    if 'short' in evaluation:
        return {'scenario': scenario, 'reason': 'the results cover {:.0f} days; a full year or a period run is needed'.format(evaluation['short'])}
    energy, costs, npv = evaluation['energy'], evaluation['costs'], evaluation['npv']
    out = {'scenario': scenario,
           'npv': _value(round(npv['npv'], 0), 'EUR'), 'annuity': _value(round(npv['annuity'], 0), 'EUR/a'),
           'npv_split': {k: round(v, 0) for k, v in npv['split'].items()},
           'pump_energy': _value(round(energy['pump_kwh'], 0), 'kWh/a'), 'pump_peak': _value(round(evaluation['pump_kw'], 2), 'kW'),
           'heat_losses': _value(round(energy['heat_kwh'], 0), 'kWh/a'), 'heat_losses_cost': _value(round(costs['heat_losses'], 0), 'EUR/a'),
           'cold_losses': _value(round(energy['cold_kwh'], 0), 'kWh/a'), 'cold_losses_cost': _value(round(costs['cold_losses'], 0), 'EUR/a')}
    if heat_total:
        out['heat_losses_share'] = _value(round(100 * energy['heat_kwh'] / heat_total, 2), '%')
    basis = evaluation.get('energy_basis')
    if basis:
        out['energy_per_carrier'] = [{'feature': f, 'id': fid, 'carrier': c, 'kwh': round(kwh, 0), 'eur': round(eur, 0)}
                                     for f, fid, c, kwh, eur in basis['costs']['features']]
        delivered = basis['costs'].get('delivered') or {}
        total = delivered.get('heat', 0.0) + delivered.get('cold', 0.0)
        out['delivered'] = {k: round(v, 0) for k, v in delivered.items()}
        if total:
            out['npv_per_mwh_delivered'] = _value(round(npv['npv'] / (total / 1000), 2), 'EUR/MWh')
        out['system_boundary'] = basis['boundary']
    else:
        out['energy_basis'] = 'price curves of the pipe losses (no energy-use results)'
    return out


def compareVersions(kpis_a, kpis_b):
    """both figure sets and the differences b - a of the numeric values with the same path"""
    diffs = {}

    def walk(a, b, path):
        if isinstance(a, dict) and isinstance(b, dict):
            if 'value' in a and 'value' in b:
                if isinstance(a['value'], (int, float)) and isinstance(b['value'], (int, float)):
                    diffs[path] = {'a': a['value'], 'b': b['value'], 'diff': round(b['value'] - a['value'], 4), 'unit': a.get('unit')}
                return
            for key in set(a) & set(b):
                walk(a[key], b[key], '{}.{}'.format(path, key) if path else key)
        elif isinstance(a, (int, float)) and isinstance(b, (int, float)) and not isinstance(a, bool):
            diffs[path] = {'a': a, 'b': b, 'diff': round(b - a, 4)}

    walk(kpis_a, kpis_b, '')
    out = {'a': kpis_a, 'b': kpis_b, 'differences': dict(sorted(diffs.items()))}
    if kpis_a['results_basis']['basis'] != kpis_b['results_basis']['basis']:
        out['note'] = 'the results bases differ ({} / {}): the result figures are not directly comparable'.format(
            kpis_a['results_basis']['basis'], kpis_b['results_basis']['basis'])
    return out


def pricesDir(config):
    return os.path.join(config['pathProjects'] + config['projectName'], 'prices')
