# coding=utf-8
"""Cost model of a pipe change (OpenSpec change cost-optimization): from the results of a check (all simulated hours
with their weights) it estimates the change of the net present value when a line gets the next larger or smaller
pipe of its series, without simulating.

Vectorized over the simulated hours (numpy): pressure drop with Darcy and the explicit Swamee-Jain friction factor;
a customer's path = the lines upstream of it along the flow direction of the hour (one path matrix per direction
pattern); central pumps lift the largest path pressure drop of the customers without a pump of their own, a
decentral pump the drop of its own path; P = V * head / eta, eta calibrated per pump group from the simulated power.
A longer path is covered by a higher head, so a customer is only starved through the pressure limit; smaller pipes
are also limited by the specific pressure loss and velocity at peak flow (the defaults of the dynamic sizing)."""
import math
from collections import defaultdict

import numpy as np

from .economics import curvePrice, electricityStartPrice, level, netPresentValue
from .pipe_losses import uPrime

RHO = 990.0  # kg/m3, water at network temperatures (the model compares sizes, not absolute heads)
MU = 5.5e-4  # Pa s
DP_SPEZ_MAX = 300.0  # Pa/m at peak flow, as the dynamic sizing
V_MAX = 3.0  # m/s


# ---------------------------------------------------------------- hydraulics
def pressureLoss(mdot, d, k):
    """Specific pressure loss [Pa/m] of a pipe for an array of mass flows (Swamee-Jain, laminar 64/Re)."""
    mdot = np.abs(np.asarray(mdot, dtype=float))
    area = math.pi * d ** 2 / 4
    v = mdot / (RHO * area)
    re = np.maximum(RHO * v * d / MU, 1e-9)
    turbulent = 0.25 / np.log10(k / d / 3.7 + 5.74 / re ** 0.9) ** 2
    f = np.where(re < 2300, 64 / re, turbulent)
    return np.where(mdot > 0, f / d * RHO * v ** 2 / 2, 0.0)


def velocity(mdot, d):
    return np.abs(np.asarray(mdot, dtype=float)) / (RHO * math.pi * d ** 2 / 4)


def nextPipe(pipe_id, catalog, larger):
    """Next larger or smaller inner diameter of the same series, or None."""
    pipe = catalog[pipe_id]
    same = [(p['d'], pid) for pid, p in catalog.items() if p['series'] == pipe['series'] and (p['d'] > pipe['d'] if larger else p['d'] < pipe['d'])]
    if not same:
        return None
    return min(same)[1] if larger else max(same)[1]


def upstreamPaths(graph, signs, customers):
    """{cid: set of lids} upstream of every customer node along the flow directions signs {lid: +1 start->end, -1}."""
    inflow = defaultdict(list)
    for lid, (start, end) in graph.items():
        s = signs.get(lid, 0)
        if s > 0:
            inflow[end].append((lid, start))
        elif s < 0:
            inflow[start].append((lid, end))
    paths = {}
    for cid in customers:
        seen, lids, todo = {('c', cid)}, set(), [('c', cid)]
        while todo:
            node = todo.pop()
            for lid, up in inflow.get(node, ()):
                lids.add(lid)
                if up not in seen and up[0] != 'ep':
                    seen.add(up)
                    todo.append(up)
        paths[cid] = lids
    return paths


# ---------------------------------------------------------------- model
class CostModel:
    """state of a check:
    hours: weights [h/a per simulated time step] (n), shape (electricity profile per step), t_amb per ambient
    lines: {lid: {'length', 'pipes': {seq: pipe_id}, 'surface': {surface: m}, 'protected': bool}}
    pairs: [(s, r)]; mdot[(lid, seq)], temp[(lid, seq)]: arrays (n); graph {lid: (start, end)}
    central: simulated central pump power (n) or None; decentral: {cid: power (n)}; v_plant[pair]: m3/s (n)
    v_customer: {cid: m3/s (n)}; p_plant: plant supply pressure (n) [Pa]; settings (ground lambda), modes {seq: mode}
    t_supply: {'heat': (n), 'cold': (n)}"""

    # limits of a smaller pipe at the line's peak flow, set from the dialog
    dp_spez_max = DP_SPEZ_MAX
    v_max = V_MAX

    def __init__(self, scenario, catalog, layers, lines, pairs, weights, mdot, temp, graph, customers, central=None,
                 decentral=None, v_plant=None, v_customer=None, p_plant=None, t_amb=None, t_supply=None, modes=None,
                 shape=None, lambda_soil=1.2, p_max=None):
        self.scenario, self.catalog, self.layers = scenario, catalog, layers
        self.lines, self.pairs, self.w = lines, pairs, np.asarray(weights, dtype=float)
        self.mdot, self.temp, self.graph, self.customers = mdot, temp, graph, list(customers)
        self.central = None if central is None else np.asarray(central, dtype=float)
        self.decentral = {c: np.asarray(p, dtype=float) for c, p in (decentral or {}).items()}
        self.v_plant = {pair: np.asarray(v, dtype=float) for pair, v in (v_plant or {}).items()}
        self.v_customer = {c: np.asarray(v, dtype=float) for c, v in (v_customer or {}).items()}
        self.p_plant = None if p_plant is None else np.asarray(p_plant, dtype=float)
        self.t_amb = t_amb or {}
        self.t_supply = t_supply or {}
        self.modes = modes or {}
        self.shape = np.ones(len(self.w)) if shape is None else np.asarray(shape, dtype=float)
        self.lambda_soil = lambda_soil
        self.p_max = p_max or {}  # {pipe_id: bar}
        self.n = len(self.w)
        self._paths()
        self._calibrate()

    # -------------------------------------------------------- paths and heads
    def lineDp(self, lid, pair, pipes=None):
        """pressure drop of the line for the pair (supply + return) per step [Pa]"""
        line = self.lines[lid]
        dp = np.zeros(self.n)
        for seq in pair:
            pid = (pipes or line['pipes'])[seq]
            p = self.catalog[pid]
            dp += pressureLoss(self.mdot.get((lid, seq), np.zeros(self.n)), p['d'], p['k']) * line['length']
        return dp

    def _paths(self):
        """per pair: the line drops (n x L), the path matrices per direction pattern and the path drops (n x C)"""
        self.pair_lines, self.dp, self.incidence, self.path_dp = {}, {}, {}, {}
        for pair in self.pairs:
            lids = sorted(lid for lid, line in self.lines.items() if all(seq in line['pipes'] for seq in pair))
            self.pair_lines[pair] = lids
            if not lids:
                continue
            index = {lid: k for k, lid in enumerate(lids)}
            dp = np.stack([self.lineDp(lid, pair) for lid in lids], axis=1)
            signs = np.stack([np.sign(self.mdot.get((lid, pair[0]), np.zeros(self.n))) for lid in lids], axis=1)
            pattern_of = np.zeros(self.n, dtype=int)
            patterns, matrices = {}, []
            for h in range(self.n):
                key = signs[h].tobytes()
                if key not in patterns:
                    paths = upstreamPaths({lid: self.graph[lid] for lid in lids if lid in self.graph},
                                          {lid: signs[h, index[lid]] for lid in lids}, self.customers)
                    m = np.zeros((len(self.customers), len(lids)), dtype=bool)
                    for c, cid in enumerate(self.customers):
                        for lid in paths.get(cid, ()):
                            m[c, index[lid]] = True
                    patterns[key] = len(matrices)
                    matrices.append(m)
                pattern_of[h] = patterns[key]
            # one path matrix per direction pattern (customers x lines), the pattern per step
            self.dp[pair], self.incidence[pair] = dp, (np.stack(matrices), pattern_of)
            path_dp = np.zeros((self.n, len(self.customers)))
            for k, m in enumerate(matrices):
                hours = pattern_of == k
                path_dp[hours] = dp[hours] @ m.T
            self.path_dp[pair] = path_dp
            self.index = getattr(self, 'index', {})
            self.index[pair] = index

    def centralMask(self):
        return np.array([c not in self.decentral for c in self.customers], dtype=bool)

    def heads(self, pair, path_dp=None):
        path_dp = self.path_dp[pair] if path_dp is None else path_dp
        mask = self.centralMask()
        if not mask.any():
            return np.zeros(self.n)
        return path_dp[:, mask].max(axis=1)

    def _calibrate(self):
        """eta of the central pumps (all plants together) and of every decentral pump from the simulated power"""
        self.eta_central = None
        if self.central is not None and self.pairs:
            hydraulic = sum(self.v_plant.get(pair, np.zeros(self.n)) * self.heads(pair) for pair in self.pairs if pair in self.path_dp)
            power = float(np.sum(self.w * self.central))
            self.eta_central = float(np.sum(self.w * hydraulic)) / power if power > 0 else None
        self.eta_decentral = {}
        for c, cid in enumerate(self.customers):
            if cid in self.decentral:
                own = sum(self.path_dp[pair][:, c] for pair in self.path_dp)
                hydraulic = self.v_customer.get(cid, np.zeros(self.n)) * own
                power = float(np.sum(self.w * self.decentral[cid]))
                self.eta_decentral[cid] = float(np.sum(self.w * hydraulic)) / power if power > 0 else None

    # -------------------------------------------------------- one change
    def pumpPowerChange(self, lid, pair, pipes):
        """change of the pump power per step [W] and of the plant head (n) if the line gets pipes {seq: pipe_id}"""
        k = self.index[pair][lid]
        delta = self.lineDp(lid, pair, pipes) - self.dp[pair][:, k]
        matrices, pattern_of = self.incidence[pair]
        on_path = matrices[:, :, k][pattern_of]  # steps x customers
        path = self.path_dp[pair] + on_path * delta[:, None]
        d_head = self.heads(pair, path) - self.heads(pair)
        power = np.zeros(self.n)
        if self.eta_central:
            power += self.v_plant.get(pair, np.zeros(self.n)) * d_head / self.eta_central
        for c, cid in enumerate(self.customers):
            eta = self.eta_decentral.get(cid)
            if eta:
                power += self.v_customer.get(cid, np.zeros(self.n)) * on_path[:, c] * delta / eta
        return power, d_head

    def lossChange(self, lid, pipes):
        """change of the heat flow leaving the pipes per step [W] by mode"""
        line = self.lines[lid]
        change = {'heat': np.zeros(self.n), 'cold': np.zeros(self.n)}
        for seq, new in pipes.items():
            old = line['pipes'][seq]
            if new == old or (lid, seq) not in self.temp:
                continue
            ambient = line.get('ambient', {}).get(seq, 2)
            depth = line.get('depth', {}).get(seq, 1.0)
            u = [uPrime(self.catalog[p]['d'], self.layers.get(self.catalog[p]['construction'], []), depth, ambient, self.lambda_soil) for p in (old, new)]
            t_amb = self.t_amb.get(ambient, np.full(self.n, 10.0))
            change[self.modes.get(seq, 'heat')] += (u[1] - u[0]) * line['length'] * (self.temp[(lid, seq)] - t_amb)
        return change

    def investmentItems(self, lid, pipes):
        """investment items of the line with pipes {seq: pipe_id} (pipes and trench by the largest DN)"""
        line = self.lines[lid]
        items = []
        for seq, pid in pipes.items():
            p = self.catalog[pid]
            items.append({'cost': float(p.get('costs') or 0) * line['length'], 'lifetime': float(p.get('lifetime_a') or 0),
                          'maintenance_pct': float(p.get('maintenance_pct') or 0)})
        dn = max(self.catalog[pid].get('dn', 0) for pid in pipes.values())
        trench = self.scenario.get('trench', {})
        default = self.scenario['scenario'].get('default_surface')
        for surface, length in line.get('surface', {}).items():
            a, b = trench.get(surface) or trench.get(default) or (0.0, 0.0)
            items.append({'cost': (a + b * dn) * length, 'lifetime': max([float(self.catalog[p].get('lifetime_a') or 0) for p in pipes.values()] or [0]),
                          'maintenance_pct': 0.0})
        return items

    def yearlyCosts(self, d_power, d_loss):
        """year-0 costs of a change of pump power and losses per step"""
        el = electricityStartPrice(self.scenario)
        curves = self.scenario.get('curves', {})
        heat_price = np.array([curvePrice(curves.get('heat'), t) or 0.0 for t in self.t_supply.get('heat', np.zeros(self.n))])
        cold_price = np.array([curvePrice(curves.get('cold'), t) or 0.0 for t in self.t_supply.get('cold', np.zeros(self.n))])
        return {'pump_energy': float(np.sum(self.w * d_power / 1000 * el * self.shape)),
                'heat_losses': float(np.sum(self.w * d_loss['heat'] / 1000 * heat_price)),
                'cold_losses': float(-np.sum(self.w * d_loss['cold'] / 1000 * cold_price))}

    def change(self, lid, larger):
        """{'pipes', 'dnpv', 'split', 'reason'} of a one-size change of the line, or None without a next pipe"""
        line = self.lines[lid]
        if line.get('protected'):
            return {'reason': 'protected'}
        if not larger and line.get('no_smaller'):
            return {'reason': 'penalty'}
        pairs = [pair for pair in self.pairs if lid in self.index.get(pair, {})]
        if not pairs:
            return {'reason': 'no pair'}
        new = dict(line['pipes'])
        for pair in pairs:
            for seq in pair:
                nxt = nextPipe(line['pipes'][seq], self.catalog, larger)
                if nxt is None:
                    return {'reason': 'no {} pipe'.format('larger' if larger else 'smaller')}
                new[seq] = nxt
        changed = {seq: pid for seq, pid in new.items() if pid != line['pipes'][seq]}
        d_power, d_head = np.zeros(self.n), np.zeros(self.n)
        for pair in pairs:
            p, h = self.pumpPowerChange(lid, pair, new)
            d_power += p
            d_head = np.maximum(d_head, h)
        reason = self.limitViolation(lid, changed, d_head, larger)
        if reason:
            return {'pipes': changed, 'reason': reason}
        d_loss = self.lossChange(lid, changed)
        yearly = self.yearlyCosts(d_power, d_loss)
        old = netPresentValue(self.scenario, self.investmentItems(lid, line['pipes']), {})
        result = netPresentValue(self.scenario, self.investmentItems(lid, new), yearly)
        split = {key: result['split'][key] - old['split'][key] for key in result['split']}
        return {'pipes': changed, 'dnpv': sum(split.values()), 'split': split, 'reason': None,
                'yearly': yearly}

    def limitViolation(self, lid, pipes, d_head, larger):
        if self.p_plant is not None and self.p_max:
            p_new = float(np.max(self.p_plant + np.maximum(d_head, 0)))
            limits = [self.p_max[pid] for line in self.lines.values() for pid in line['pipes'].values() if self.p_max.get(pid)]
            if limits and p_new > min(limits) * 1e5:
                return 'p_max'
        if not larger:
            for seq, pid in pipes.items():
                mdot = self.mdot.get((lid, seq))
                if mdot is None or not len(mdot):
                    continue
                peak = float(np.max(np.abs(mdot)))
                d, k = self.catalog[pid]['d'], self.catalog[pid]['k']
                if float(pressureLoss([peak], d, k)[0]) > self.dp_spez_max or float(velocity([peak], d)[0]) > self.v_max:
                    return 'peak'
        return None

    # -------------------------------------------------------- one iteration
    def step(self):
        """best one-size change of every line with a negative ΔNPV: ({lid: change}, {lid: rejected reasons})"""
        chosen, rejected = {}, {}
        for lid in sorted(self.lines):
            options = []
            for larger in (True, False):
                option = self.change(lid, larger)
                if option is None:
                    continue
                if option.get('reason'):
                    rejected.setdefault(lid, []).append(option['reason'])
                elif option['dnpv'] < 0:
                    options.append(option)
            if options:
                chosen[lid] = min(options, key=lambda o: o['dnpv'])
        return chosen, rejected


def catalogWithCosts(rows):
    """pipe catalog of the model from public.pipes rows (series as the dynamic sizing, DN, costs, layers)"""
    import re
    catalog = {}
    for row in rows:
        match = re.match(r'\s*DN\s*(\d+)', row.get('description') or '')
        catalog[int(row['id'])] = {'d': float(row['innerpipediameter']), 'k': float(row['piperoughnessfactor'] or 0.0),
                                   'construction': row['pipe_construction_id'], 'series': row.get('series') or ('construction', row['pipe_construction_id']),
                                   'name': row['name'], 'costs': row.get('costs'), 'lifetime_a': row.get('lifetime_a'),
                                   'maintenance_pct': row.get('maintenance_pct'), 'dn': int(match.group(1)) if match else round(float(row['innerpipediameter']) * 1000)}
    return catalog


def priceShape(levelled, n):
    return np.ones(n) if levelled is None else np.asarray(levelled, dtype=float)


__all__ = ['CostModel', 'catalogWithCosts', 'nextPipe', 'pressureLoss', 'upstreamPaths', 'level']
