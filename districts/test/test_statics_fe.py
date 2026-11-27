"""FE solver of the pipe statics (change statics-steel-solver): hand formulas and the isoplus planning manual
(PHB chapter/page). No DB, no QGIS."""
import math

import numpy as np
import pytest

from districts.utility_functions import statics_catalog as cat
from districts.utility_functions import statics_fe as fe

E, ALPHA = 211800e6, 11.3e-6
RIGID_PLASTIC = 1e-5   # axial slip of the hand formulas and of the isoplus tables (rigid-plastic friction)


def steel(d_o, wall, z=0.0):
    return {'E': E, 'alpha': ALPHA, 'nu': 0.3, 'd_o': d_o, 'wall': wall, 'y': 0.0, 'z': z}


def run(points, members_spec, carriers, casing, cover=0.8, mu=0.4, slip=0.002, states=None, fixed=(), pads=None,
        element_length=1.0):
    sec = fe.section(carriers)
    soil = fe.soil(cover, casing, fe.pipeWeight(carriers, casing), mu, 19.0, 32.5, axial_slip=slip)
    members = [{'id': i, 'from': a, 'to': b, 'section': sec, 'casing_d': casing, 'soil': soil,
                't0': [10.0] * len(carriers), 'pad': (pads or {}).get(i, 0.0)} for i, (a, b) in enumerate(members_spec)]
    model = fe.Model(fe.Mesh(points, members, element_length), fixed_points=fixed, pad_strain=cat.padStrain)
    res = model.solve(states(len(members)) if states else [heat(len(members), 130.0)])
    assert res['converged'], res['message']
    return model, res, sec, soil


def heat(n, T, p=0.0, carriers=1):
    return {'temps': {i: [T] * carriers if not isinstance(T, list) else T for i in range(n)}, 'p': {i: p for i in range(n)}}


def straight(L, n=2):
    return {i: {'xyz': (L * i / n, 0.0, 0.0)} for i in range(n + 1)}, [(i, i + 1) for i in range(n)]


def maxAxial(res, state=0):
    return max(max(abs(c['sigma_ax']) for c in e['carriers']) for e in res['states'][state]['elements']) / 1e6


DN100 = (0.1143, 0.0036, 0.200)


# ---------------------------------------------------------------- hand formulas
def test_free_end_movement():
    pts, mem = straight(148.0)
    model, res, sec, soil = run(pts, mem, [steel(*DN100[:2])], DN100[2])
    half = 74.0
    hand = ALPHA * 120 * half - soil['f_ax'] * half ** 2 / (2 * sec['EA'])
    assert res['states'][0]['u'][:, 0].max() == pytest.approx(hand, rel=0.01)


def test_friction_length_rigid_plastic():
    pts, mem = straight(100.0)
    model, res, sec, soil = run(pts, mem, [steel(*DN100[:2])], DN100[2], slip=RIGID_PLASTIC)
    A = sec['props'][0]['A']
    assert maxAxial(res) == pytest.approx(soil['f_ax'] * 50.0 / A / 1e6, rel=0.02)


def test_fully_restrained():
    pts, mem = straight(600.0, 3)
    model, res, sec, soil = run(pts, mem, [steel(*DN100[:2])], DN100[2], states=lambda n: [heat(n, 85.0)])
    assert maxAxial(res) == pytest.approx(E * ALPHA * 75 / 1e6, rel=0.005)


def test_restrained_with_pressure():
    """Closed pipe, restrained: sigma_ax = nu * sigma_hoop - E alpha dT."""
    pts, mem = straight(600.0, 3)
    p = 16e5
    model, res, sec, soil = run(pts, mem, [steel(*DN100[:2])], DN100[2], states=lambda n: [heat(n, 85.0, p)])
    hoop = p * (DN100[0] - 2 * DN100[1]) / (2 * DN100[1])
    centre = res['states'][0]['elements'][300]['carriers'][0]['sigma_ax']
    assert centre / 1e6 == pytest.approx((0.3 * hoop - E * ALPHA * 75) / 1e6, rel=0.01)


def test_equilibrium_with_fixed_point():
    pts = {'a': {'xyz': (0, 0, 0)}, 'b': {'xyz': (40, 0, 0)}, 'c': {'xyz': (40, 15, 0)}}
    model, res, sec, soil = run(pts, [('a', 'b'), ('b', 'c')], [steel(*DN100[:2])], DN100[2], fixed=['a'])
    u = res['states'][0]['u_full']
    st = heat(2, 130.0)
    F = model.loadVector(*model.elementLoads(st['temps'], st['p']))
    beam = (model.K @ u - F).reshape(-1, 6)
    #thermal loads and beam forces are self-equilibrated
    assert np.abs(beam[:, :3].sum(axis=0)).max() < 1e-6 * np.abs(F).max()
    fs, _ = model.springs.evaluate(u.reshape(-1, 6)[:, :3])
    residual = beam[:, :3] + fs
    nd = model.mesh.node_of_point['a']
    free = np.ones(model.n, bool)
    free[nd] = False
    assert np.abs(residual[free]).max() < 1e-3 * np.abs(fs).max()
    #the fixed point's reaction balances the sum of all soil forces
    reaction = -residual[nd]
    assert np.linalg.norm(reaction) > 1000.0
    assert np.abs(reaction + fs.sum(axis=0)).max() < 1e-3 * np.abs(fs).max() * model.n


def test_symmetry_of_a_straight_pipe():
    pts, mem = straight(80.0, 2)
    model, res, sec, soil = run(pts, mem, [steel(*DN100[:2])], DN100[2])
    u = res['states'][0]['u'][:, 0]
    x = model.mesh.xyz[:, 0]
    left = u[np.argmin(x)]
    right = u[np.argmax(x)]
    assert left == pytest.approx(-right, rel=1e-6)


def test_finer_elements_converge():
    pts = {'a': {'xyz': (-40, 0, 0)}, 'b': {'xyz': (0, 0, 0), 'bend': {'class': 'bend', 'radius': 1.5 * DN100[0]}},
           'c': {'xyz': (0, 15, 0)}}

    def bendStress(length):
        model, res, sec, soil = run(pts, [('a', 'b'), ('b', 'c')], [steel(*DN100[:2])], DN100[2], element_length=length)
        return max(res['states'][0]['elements'][e]['carriers'][0]['sigma_b'] for e, k in enumerate(model.mesh.el_kind) if k == 'bend')
    assert bendStress(0.5) == pytest.approx(bendStress(1.0), rel=0.05)


# ---------------------------------------------------------------- bends, kinks, tees
def test_bend_factors():
    k, i = fe.bendFactors(0.1143, 0.0036, 1.5 * 0.1143)
    h = 0.0036 * 1.5 * 0.1143 / ((0.1143 - 0.0036) / 2) ** 2
    assert k == pytest.approx(1.65 / h) and i == pytest.approx(0.9 / h ** (2 / 3))
    #a small kink is nearly straight pipe (i = 1); a large one intensifies
    assert fe.mitreFactor(0.1143, 0.0036, 4.0) == 1.0
    assert fe.mitreFactor(0.1143, 0.0036, 30.0) > 2.0
    assert fe.teeFactor(0.1143, 0.0036) > 1.0


def test_l_bend_arc_and_stress_intensification():
    pts = {'a': {'xyz': (-60, 0, 0)}, 'b': {'xyz': (0, 0, 0), 'bend': {'class': 'bend', 'radius': 1.5 * DN100[0]}},
           'c': {'xyz': (0, 20, 0)}}
    model, res, sec, soil = run(pts, [('a', 'b'), ('b', 'c')], [steel(*DN100[:2])], DN100[2])
    bends = [e for e, k in enumerate(model.mesh.el_kind) if k == 'bend']
    assert len(bends) >= 8
    assert all(model.mesh.el_i[e] > 2 for e in bends)
    corner = res['states'][0]['u'][model.mesh.node_of_point['b']]
    assert corner[0] > 0.02 and corner[1] < 0     # the long run pushes into the leg, the leg into the run


def test_pad_lowers_the_bend_stress():
    pts = {'a': {'xyz': (-60, 0, 0)}, 'b': {'xyz': (0, 0, 0), 'bend': {'class': 'bend', 'radius': 1.5 * DN100[0]}},
           'c': {'xyz': (0, 20, 0)}}

    def bendStress(pad):
        model, res, sec, soil = run(pts, [('a', 'b'), ('b', 'c')], [steel(*DN100[:2])], DN100[2], pads={1: pad})
        return max(res['states'][0]['elements'][e]['carriers'][0]['sigma_b'] for e, k in enumerate(model.mesh.el_kind) if k == 'bend')
    assert bendStress(0.08) < bendStress(0.04) < bendStress(0.0)


def test_stress_range_from_reversal():
    pts = {'a': {'xyz': (-60, 0, 0)}, 'b': {'xyz': (0, 0, 0), 'bend': {'class': 'bend', 'radius': 1.5 * DN100[0]}},
           'c': {'xyz': (0, 20, 0)}}
    model, res, sec, soil = run(pts, [('a', 'b'), ('b', 'c')], [steel(*DN100[:2])], DN100[2],
                                states=lambda n: [heat(n, 130.0), heat(n, 10.0), heat(n, 130.0)])
    heat_u = res['states'][0]['u'][model.mesh.node_of_point['b']][0]
    cool_u = res['states'][1]['u'][model.mesh.node_of_point['b']][0]
    reheat_u = res['states'][2]['u'][model.mesh.node_of_point['b']][0]
    #friction reverses on cooling: the bend does not return to zero, the reheat repeats the heat-up
    assert cool_u < heat_u and cool_u != pytest.approx(0.0, abs=1e-4)
    assert reheat_u == pytest.approx(heat_u, rel=0.02)


# ---------------------------------------------------------------- isoplus planning manual
SINGLE_LMAX = {  # DN: (da mm, s mm, Da mm, Lmax at cover 0.8 / 1.2 / 1.6 m), PHB 12/4, standard insulation
    20: (26.9, 2.6, 90, (56, 38, 29)), 50: (60.3, 3.2, 125, (114, 78, 59)), 100: (114.3, 3.6, 200, (148, 103, 79)),
    200: (219.1, 4.5, 315, (210, 150, 116)), 500: (508.0, 6.3, 710, (244, 185, 149))}


@pytest.mark.parametrize('dn', sorted(SINGLE_LMAX))
def test_lmax_single_pipe(dn):
    """PHB 12/4: at Lmax a straight run with free ends (expansion legs) reaches 190 N/mm2 at its centre, 130 degC,
    gamma 19 kN/m3, phi 32.5 deg, mu 0.40; tolerance 2 % plus the rounding of Lmax to whole metres. Elements of
    0.25 m: lumped springs leave the centre element short of half its own friction (error h / L)."""
    da, s, Da, lengths = SINGLE_LMAX[dn]
    for L, cover in zip(lengths, (0.8, 1.2, 1.6)):
        pts, mem = straight(float(L))
        model, res, sec, soil = run(pts, mem, [steel(da / 1000, s / 1000)], Da / 1000, cover=cover, slip=RIGID_PLASTIC,
                                    element_length=0.25)
        assert maxAxial(res) == pytest.approx(190.0, rel=0.02 + 0.5 / L), (dn, cover)


@pytest.mark.parametrize('T, below', [(85.0, True), (95.0, False)])
def test_cold_laying_limit(T, below):
    """PHB 12/2: cold laying of single pipes without length limit up to 85 degC (190 N/mm2 restrained)."""
    pts, mem = straight(600.0, 3)
    model, res, sec, soil = run(pts, mem, [steel(*DN100[:2])], DN100[2], states=lambda n: [heat(n, T)])
    assert (maxAxial(res) < 190.0) == below


# ---------------------------------------------------------------- twin pipe
def twinCarriers(da=0.1143, s=0.0036, Da=0.315):
    off = ((Da - 2 * da) / 3.0 + da) / 2.0      # clearance rule of the twin geometry (pipe-series-catalog D7)
    return [steel(da, s, off), steel(da, s, -off)]


def test_twin_equal_temperatures():
    pts, mem = straight(600.0, 3)
    model, res, sec, soil = run(pts, mem, twinCarriers(), 0.315, states=lambda n: [heat(n, [80.0, 80.0])])
    c = res['states'][0]['elements'][300]['carriers']
    assert c[0]['sigma_ax'] == pytest.approx(c[1]['sigma_ax'], rel=1e-6)
    assert c[0]['sigma_b'] == pytest.approx(0.0, abs=1e3)


def test_twin_temperature_difference():
    """The mean strain is that of the mean temperature; the hotter carrier is more compressed."""
    pts, mem = straight(600.0, 3)
    model, res, sec, soil = run(pts, mem, twinCarriers(), 0.315, states=lambda n: [heat(n, [80.0, 50.0])])
    hot, cold = res['states'][0]['elements'][300]['carriers']
    assert hot['sigma_ax'] < cold['sigma_ax'] < 0
    mean = (hot['sigma_ax'] + cold['sigma_ax']) / 2
    assert mean / 1e6 == pytest.approx(-E * ALPHA * 55 / 1e6, rel=0.01)


TWIN_LMAX = {  # DN: (da mm, s mm, Da mm, Lmax at cover 0.8 m for a spread K of 20 / 40 / 60 K), PHB 12/5
    20: (26.9, 2.6, 125, (63, 53, 43)), 100: (114.3, 3.6, 315, (119, 100, 81)), 200: (219.1, 4.5, 560, (134, 113, 92))}


@pytest.mark.parametrize('dn', sorted(TWIN_LMAX))
def test_twin_lmax_trend(dn):
    """PHB 12/5, trend only: the hotter carrier carries E alpha K / 2 more than the mean, so Lmax falls with the
    spread K as (190 - d(K)); the ratios Lmax(40 K) / Lmax(20 K) and Lmax(60 K) / Lmax(20 K) match the table within
    5 %. The level does not: the table needs 7-35 % more friction than the single-pipe formula (open until FW 401)."""
    da, s, Da, lengths = TWIN_LMAX[dn]
    sigma = {}
    for K in (0, 20, 40, 60):
        pts, mem = straight(float(lengths[0]))
        model, res, sec, soil = run(pts, mem, twinCarriers(da / 1000, s / 1000, Da / 1000), Da / 1000, slip=RIGID_PLASTIC,
                                    element_length=0.25, states=lambda n: [heat(n, [130.0 - K, 130.0])])
        sigma[K] = maxAxial(res)
    d = {K: sigma[K] - sigma[0] for K in sigma}
    assert d[20] == pytest.approx(E * ALPHA * 10 / 1e6, rel=0.02)
    for K, L in zip((40, 60), lengths[1:]):
        assert (190 - d[K]) / (190 - d[20]) == pytest.approx(L / lengths[0], rel=0.05), (dn, K)


def test_twin_free_curvature_sign():
    """A free twin heated on one carrier curves away from it."""
    s = fe.section(twinCarriers())
    pts, mem = straight(10.0, 1)
    members = [{'id': 0, 'from': 0, 'to': 1, 'section': s, 'casing_d': 0.315, 't0': [10.0, 10.0],
                'soil': {'f_ax': 0.0, 'k_ax': 0.0, 'p_lat': 0.0, 'k_lat': 0.0, 'p_up': 0.0, 'k_v': 0.0}}]
    model = fe.Model(fe.Mesh(pts, members, 1.0), fixed_points=[0])
    eps, kz, ky = model.elementLoads({0: [60.0, 10.0]}, {0: 0.0})
    #the hotter carrier is at +z: free curvature w'' < 0 (the ends bend down, away from it)
    assert ky[0] < 0
