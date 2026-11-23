# coding=utf-8
"""HTML reports of the hydraulic balancing and the cost optimization (OpenSpec change cost-optimization, D22) on a project
from the template heating_network, with iteration files made from its lines and customers (no simulation):
sections, tables, maps and the cost analysis.

    python -m pytest test/test_iteration_report.py -v -s   (--keep-projects)
"""
import json
import os
from types import SimpleNamespace

import pytest

from districts.cost_optimization import npvRecord
from districts.utility_functions.cost_optimization_layers import iterationPath
from districts.utility_functions.economic_data import loadScenario
from districts.utility_functions.dynamic_sizing_results import saveIteration
from districts.utility_functions.economic_data import ensureEconomicTables
from districts.utility_functions.hydraulic_balancing import getPipeBundles, getPipeCatalog
from districts.utility_functions.iteration_report import (
    balancingReport, costReport, loadRunParameters, mapIterations, saveRunParameters, writeReport,
)

from districts.utility_functions.cost_optimization_layers import loadCostIterations
from districts.utility_functions.dynamic_sizing_results import loadIterations
from districts.utility_functions.set_pipes import SetPipes, applyPipes, balancingIterationPipes, costIterationPipes

from .conftest import wait_until
from .test_workflow import HEATING, create_project, delete_project, project_name_for

pytestmark = [pytest.mark.e2e]


@pytest.fixture(scope='class')
def rep(request, districts_plugin, errors):
    state = SimpleNamespace(plugin=districts_plugin, project_name=project_name_for('report'))
    yield state
    if not request.config.getoption('--keep-projects'):
        delete_project(districts_plugin, errors, state.project_name)


def lines_and_customers(plugin):
    v = plugin.config['versionName']
    plugin.cur.execute('SELECT id, pipe_bundle_type_id AS bid FROM "{}".lines WHERE pipe_bundle_type_id IS NOT NULL ORDER BY id;'.format(v))  # nosec B608
    lines = {row['id']: row['bid'] for row in plugin.cur.fetchall()}
    plugin.cur.execute('SELECT id FROM "{}".customers ORDER BY id;'.format(v))  # nosec B608
    return lines, [row['id'] for row in plugin.cur.fetchall()]


def larger_bundle(bundles, catalog, bid):
    """a bundle whose first pipe is larger than the one of bid, or None"""
    d = catalog[bundles[bid][min(bundles[bid])]]['d']
    larger = [(catalog[b[min(b)]]['d'], k) for k, b in bundles.items() if b and b[min(b)] in catalog and catalog[b[min(b)]]['d'] > d]
    return min(larger)[1] if larger else None


@pytest.mark.incremental
class TestIterationReport:
    def test_create_project(self, rep, errors):
        create_project(rep.plugin, errors, rep.project_name, HEATING)
        errors.check()
        assert rep.plugin.config['versionName']

    def test_balancing_report(self, rep):
        plugin = rep.plugin
        lines, customers = lines_and_customers(plugin)
        bundles, catalog = getPipeBundles(plugin.cur), getPipeCatalog(plugin.cur)
        changed = {lid: larger_bundle(bundles, catalog, bid) for lid, bid in list(lines.items())[:5]}
        changed = {lid: bid for lid, bid in changed.items() if bid}
        assert changed, 'no larger pipe bundle in the template'

        def pipe(bid):
            return catalog[bundles[bid][min(bundles[bid])]]

        for k, outcome in ((0, 'reference'), (1, 'changed'), (2, 'converged')):
            line_rows = {}
            for lid, bid in lines.items():
                new = changed.get(lid, bid) if k == 1 else bid
                old = bid if k <= 1 else changed.get(lid, bid)
                line_rows[str(lid)] = {'mdot': 1.0 + lid % 7, 'mdot_max': 2.0, 'dp_spez': 80.0, 'pipe': pipe(old)['name'], 'pipe_new': pipe(new)['name'],
                                       'd': round(pipe(old)['d'] * 1000, 1), 'd_new': round(pipe(new)['d'] * 1000, 1), 'changed': k == 1 and lid in changed,
                                       'protected': False}
            dps = {str(cid): {'dp': 50000.0 + 1000 * (i % 9) * (3 - k), 'dp_sized': 50000.0, 'dp_net': 20000.0, 'epid': 1, 'time': '2026-01-01 08:00:00'}
                   for i, cid in enumerate(customers)}
            pair = {'supply': 1, 'return': 2, 'temps': [70.0, 40.0], 'time': '2026-01-01 08:00:00', 'cid_weak': customers[0], 'epid_weak': 1,
                    'dp_net_weak': 20000.0, 'cid_target': customers[0], 'dp_target': 50000.0, 'quota': 0.9, 'spread_sized': 5000.0, 'n_presized': 0,
                    'n_balancing_steps': 2, 'n_changed': len(changed) if k == 1 else 0, 'n_customers_skipped': 0, 'n_protected': 0,
                    'customers': dps, 'lines': line_rows}
            saveIteration(plugin.config, {'iteration': k, 'started': '2026-11-17T10:00:00', 'outcome': outcome, 'n_changed': pair['n_changed'], 'pairs': [pair]})
        saveRunParameters(plugin.config, 'balancing', {'network': 1, 'submodel': 'default', 'max_iter': 5, 'pairs': [(1, 2, 70.0, 40.0)],
                                                       'periods': {'calc_time_from': '2026-01-01 00:00', 'calc_time_to': '2026-01-08 00:00'}, 'protected': [],
                                                       'reference_run': True, 'tol_above': 5000.0})
        assert loadRunParameters(plugin.config, 'balancing')['max_iter'] == 5
        page = balancingReport(plugin.cur, plugin.config).html()
        for text in ('Inputs', 'Outputs', 'Pipes in use', 'Trench lengths per surface', 'Pipe lengths per iteration [m]', 'Iteration 2',
                     'Lines with new pipes, pair 1/2', '2026-01-01 00:00 – 2026-01-08 00:00'):
            assert text in page, text
        assert page.count('<img src="data:image/png;base64,') >= 4  # diagram and a map per iteration
        assert 'Cost analysis' not in page

    def test_cost_report(self, rep):
        plugin = rep.plugin
        ensureEconomicTables(plugin.cur)
        plugin.cur.execute("SELECT id FROM public.economic_scenarios ORDER BY id LIMIT 1;")
        scenario = plugin.cur.fetchone()['id']
        lines, customers = lines_and_customers(plugin)
        bundles, catalog = getPipeBundles(plugin.cur), getPipeCatalog(plugin.cur)
        changed = {lid: larger_bundle(bundles, catalog, bid) for lid, bid in list(lines.items())[:5]}
        changed = {lid: bid for lid, bid in changed.items() if bid}
        steps = [{'line': lid, 'before': {str(s): p for s, p in bundles[lines[lid]].items()}, 'after': {str(s): p for s, p in bundles[bid].items()},
                  'dnpv': -1000.0, 'split': {}, 'larger': True} for lid, bid in changed.items()]
        split0 = {'investment': 500000.0, 'pump_energy': 40000.0, 'heat_losses': 90000.0, 'cold_losses': 0.0, 'maintenance': 30000.0, 'residual': -50000.0, 'penalties': 0.0}
        split1 = dict(split0, investment=520000.0, pump_energy=20000.0)
        rows = [{'iteration': 0, 'npv': sum(split0.values()), 'split': split0, 'npv_model': None, 'model_error': None, 'penalty_customers': [],
                 'outcome': 'changed', 'n_larger': len(steps), 'n_smaller': 0, 'n_rejected': 2, 'steps': steps,
                 'rejected': {str(list(lines)[-1]): ['p_max', 'no smaller pipe']}, 'state': {str(lid): bid for lid, bid in lines.items()}},
                {'iteration': 1, 'npv': sum(split1.values()), 'split': split1, 'npv_model': sum(split1.values()) + 3000, 'model_error': 0.005,
                 'penalty_customers': customers[:2], 'outcome': 'no improvement', 'steps': [], 'rejected': {},
                 'state': {str(lid): changed.get(lid, bid) for lid, bid in lines.items()}}]
        # iteration 0 with the terms of its NPV as a run saves them, iteration 1 without them (a run before)
        evaluation = {'scenario': loadScenario(plugin.cur, scenario), 'pump_kw': 25.0,
                      'items': {('pipe', 1): {'name': 'DN 50', 'cost': 400000.0, 'lifetime': 40.0, 'maintenance_pct': 1.0, 'length': 2000.0},
                                ('trench', 'paved'): {'name': 'paved', 'cost': 100000.0, 'lifetime': 40.0, 'maintenance_pct': 0.0, 'length': 1000.0}},
                      'pump_item': {'name': 'pumps', 'cost': 2500.0, 'lifetime': 15.0, 'maintenance_pct': 2.5},
                      'costs': {'pump_energy': 1500.0, 'heat_losses': 6000.0, 'cold_losses': 0.0},
                      'energy': {'pump_kwh': 7500.0, 'heat_kwh': 60000.0, 'cold_kwh': 0.0}}
        econ = npvRecord(evaluation, 0.0, 0.0)
        rows[0]['economics'] = econ
        rows[0]['split'] = {g: sum(t['value'] for t in econ['terms'] if t['group'] == g) for g in split0}
        rows[0]['npv'] = sum(rows[0]['split'].values())
        # iteration 1 on the energy basis (plant-energy-costs): a plant buying fuel, the customers' heat pumps for the whole system
        by_carrier = {'plant_energy': {'fuel': 8000.0}, 'customer_energy': {'electricity': 2500.0}}
        basis = {'costs': {'yearly': by_carrier, 'info': {}, 'kwh': {'plant_energy': {'fuel': 100000.0}, 'customer_energy': {'electricity': 10000.0}},
                           'features': [('energy_plant', 1, 'fuel', 100000.0, 8000.0), ('customer', 7, 'electricity', 10000.0, 2500.0)], 'no_price': [],
                           'delivered': {'heat': 60000.0, 'cold': 40000.0}},
                 'boundary': 'system', 'losses': {'heat': 1200.0, 'cold': 0.0}, 'marginal_hours': {1: 8000.0}, 'curve_hours': 760.0, 'threshold_pct': 5.0}
        econ1 = npvRecord(dict(evaluation, npv_yearly={'pump_energy': 1500.0}, by_carrier=by_carrier, energy_basis=basis), 0.0, 0.0)
        rows[1]['economics'] = econ1
        rows[1]['split'] = {g: sum(t['value'] for t in econ1['terms'] if t['group'] == g) for g in list(split0) + ['plant_energy', 'customer_energy']}
        rows[1]['npv'] = sum(rows[1]['split'].values())
        for row in rows:
            with open(iterationPath(plugin.config, row['iteration']), 'w', encoding='utf-8') as f:
                json.dump(row, f)
        saveRunParameters(plugin.config, 'cost', {'scenario': scenario, 'network': '1', 'submodel': 'default', 'pairs': [(1, 2)], 'max_iter': 3,
                                                  'periods': {'annual': True, 'periods': []}, 'price_kh': 0.5, 'protected': [lid for lid in list(lines)[:1]]})
        page = costReport(plugin.cur, plugin.config).html()
        for text in ('Economic scenario', 'Prices per cost group', 'Price curves heat and cold', 'Trench costs per surface', 'Pipes in use',
                     'Cost analysis', 'Investment per iteration [€]', 'Pipes: first iteration and least net present value',
                     'Trench: first iteration and least net present value', 'Rejected changes', 'pressure above p_max of the pipe',
                     'Lines changed for this iteration', 'Customers with a new deficit', 'a year', 'Net present value: equations',
                     'Present value factors of the scenario', 'Amounts of year 0 per iteration', 'Net present value: calculation per iteration',
                     '2000 m; n = 40 a, t = 0', '25.0 kW', '60000 kWh/a, 0.1000 €/kWh', 'Basis of the net present value',
                     'Energy use and costs of year 0', 'Hours per marginal plant', 'Plant 1', '100000 kWh/a, 0.0800 €/kWh',
                     'Energy delivered to the customers'):
            assert text in page.replace('&#x27;', '').replace("'", ''), text
        assert 'The sum of the terms differs' not in page
        assert page.count('<img src="data:image/png;base64,') >= 3  # NPV diagram, price curves, maps
        path = writeReport(plugin.cur, plugin.config, 'cost')
        assert os.path.exists(path) and os.path.dirname(path).endswith('reports')

    def test_set_pipes(self, rep):
        """'Set pipes' (D24): the pipes simulated in an iteration into this version, by bundles (cost optimization) or by
        the pipe names of an older balancing file, and into a child version without the run files of the parent"""
        plugin = rep.plugin
        v = plugin.config['versionName']
        before, _ = lines_and_customers(plugin)
        cost_rows = {row['iteration']: row for row in loadCostIterations(plugin.config)}
        target = costIterationPipes(cost_rows[1])
        n, _ = applyPipes(plugin.cur, v, target)
        after, _ = lines_and_customers(plugin)
        assert n == sum(1 for lid, bid in target['bundles'].items() if before.get(lid) != bid) > 0
        assert all(after[lid] == bid for lid, bid in target['bundles'].items())
        assert applyPipes(plugin.cur, v, target)[0] == 0

        # iteration 1 of the balancing simulated the original pipes; its file has no state, only the supply pipe names
        summary = {s['iteration']: s for s in loadIterations(plugin.config)}[1]
        target = balancingIterationPipes(plugin.cur, summary)
        assert target['by_name']
        applyPipes(plugin.cur, v, target)
        bundles = getPipeBundles(plugin.cur)
        restored, _ = lines_and_customers(plugin)
        assert all(bundles[restored[lid]] == bundles[bid] for lid, bid in before.items())

        log = []
        set_pipes = SetPipes(plugin.dlg, plugin, 'Cost optimization', log.append)
        set_pipes.run(1, costIterationPipes(cost_rows[1]), ask=False)
        wait_until(lambda: plugin.config['versionName'] == v + '_it1' and any('have the pipes of iteration 1' in m for m in log), 180,
                   lambda: 'child version: ' + ' | '.join(log))
        child, _ = lines_and_customers(plugin)
        assert all(child[lid] == bid for lid, bid in costIterationPipes(cost_rows[1])['bundles'].items())
        assert not loadCostIterations(plugin.config) and not loadIterations(plugin.config)
        plugin.cur.execute('SELECT id, pipe_bundle_type_id AS bid FROM "{}".lines;'.format(v))  # nosec B608
        assert {row['id']: row['bid'] for row in plugin.cur.fetchall()} == restored  # the parent keeps its pipes


def test_iteration_table_shows_the_step_into_an_iteration():
    """the counts of a step in the row of the iteration it leads to; iteration 0 has none; the outcome only in the
    last row"""
    from districts.utility_functions.iteration_report import iterationTableRows
    from districts.utility_functions.translations import tr_msg
    rows = [{'iteration': 0, 'n_larger': 2, 'n_smaller': 24, 'n_rejected': 2, 'outcome': tr_msg('changed')},
            {'iteration': 1, 'n_larger': 1, 'n_smaller': 0, 'n_rejected': 26, 'outcome': tr_msg('changed')},
            {'iteration': 2, 'outcome': tr_msg('max. iterations')}]
    table = iterationTableRows(rows)
    assert [steps for _, steps, _ in table] == [['', '', ''], [2, 24, 2], [1, 0, 26]]
    assert [outcome for _, _, outcome in table] == ['', '', tr_msg('max. iterations')]
    # during a run the newest row has made its step: nothing to say yet
    assert iterationTableRows(rows[:2])[-1][2] == ''


def test_map_iterations():
    assert mapIterations([0, 1, 2]) == [0, 1, 2]
    chosen = mapIterations(list(range(30)), best=17)
    assert len(chosen) == 10 and {0, 17, 29} <= set(chosen) and chosen == sorted(chosen)
