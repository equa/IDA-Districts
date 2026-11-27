"""Loads, laying methods, checks, pads and the isoplus tables of the pipe statics (change statics-steel-solver).
No DB, no QGIS."""
import pytest

from districts.utility_functions import statics_catalog as cat
from districts.utility_functions import statics_checks as sc
from districts.utility_functions import statics_fe as fe


def params():
    return {k: v[0] for k, v in sc.SOLVER_PARAMETERS.items()}


def sources():
    return {k: v[3] for k, v in sc.SOLVER_PARAMETERS.items()}


# ---------------------------------------------------------------- loads
def test_simulation_above_design():
    loads = sc.pipeLoads(params(), {}, [1, 2], {(7, 1): 125.0, (7, 2): 60.0}, {}, 7)
    assert loads['temps'] == [125.0, 120.0]
    assert loads['temp_sources'] == ['simulation', 'parameter']
    assert loads['pressure'] == 16e5 and loads['pressure_source'] == 'parameter'


def test_no_results_and_section_override():
    loads = sc.pipeLoads(params(), {'design_temperature_c': 90, 'design_pressure_bar': None}, [1], {}, {}, 7)
    assert loads['temps'] == [90.0] and loads['temp_sources'] == ['section'] and not loads['simulated']


def test_simulated_pressure():
    loads = sc.pipeLoads(params(), {}, [1, 2], {}, {(3, 1): 18e5, (3, 2): 9e5}, 3)
    assert loads['pressure'] == 18e5 and loads['pressure_source'] == 'simulation'


# ---------------------------------------------------------------- laying methods
def test_stress_free_temperature():
    assert sc.stressFreeTemperature('conventional', 10, 130) == 10
    assert sc.stressFreeTemperature('cold', 10, 130) == 10
    assert sc.stressFreeTemperature('thermal_prestress', 10, 130) == 70           # PHB 12/2: mean temperature
    assert sc.stressFreeTemperature('one_time_compensator', 10, 130, 80) == 80
    assert sc.stressFreeTemperature('self_prestress', 10, 130) is None


def test_fictitious_preheat():
    assert sc.fictitiousPreheat(10, 130) == pytest.approx(50.0)                   # PHB 10/31


def test_laying_findings():
    p = params()
    rules = [r for r, _, _ in sc.layingFindings('cold', 90, False, p, None, False)]
    assert rules == ['cold_laying_too_hot']
    assert not sc.layingFindings('cold', 80, False, p, None, False)
    assert [r for r, _, _ in sc.layingFindings('cold', 75, True, p, None, False)] == ['cold_laying_too_hot']
    assert [r for r, _, _ in sc.layingFindings(None, 130, False, p, 95, False)] == ['legs_need_prestress']
    assert not sc.layingFindings(None, 130, False, p, 95, True)
    assert [r for r, _, _ in sc.layingFindings('self_prestress', 130, False, p, None, False)] == ['laying_method_unsupported']
    assert [r for r, _, _ in sc.layingFindings('warm', 130, False, p, None, False)] == ['laying_method_unknown']


def test_one_time_compensator():
    #DN 100 of PHB 7/2: 80 mm travel, 212 N/mm, 109.9 cm2
    travel, rate, area = cat.oneTimeCompensator(100)
    assert (travel, rate, area) == pytest.approx((0.080, 212000.0, 0.01099))
    #95 mm needed: half of 2 x 70 m restrained pipe from 10 to 106 degC
    needed = sc.compensatorTravel(11.3e-6, 98.0, 10.0, 95.5, 95.5)
    assert needed == pytest.approx(0.095, rel=0.01)
    rules = [r for r, _, _ in sc.compensatorFindings(needed, travel, True, 20, 20, False, True)]
    assert rules == ['compensator_travel']
    rules = [r for r, _, _ in sc.compensatorFindings(0.05, travel, False, 4, 20, True, False)]
    assert rules == ['compensator_not_restrained', 'compensator_straight_length', 'compensator_in_bend', 'compensator_stretch_ends']


# ---------------------------------------------------------------- checks
def test_verdict_only_with_a_confirmed_limit():
    p, s = params(), sources()
    ok = sc.check('axial_stress', 180.0, p, s, 'sigma_ax_allow_n7mm2', 235.0)
    assert ok['verdict'] == 'pass' and ok['source'] == 'isoplus PHB 12/4'
    bad = sc.check('axial_stress', 200.0, p, s, 'sigma_ax_allow_n7mm2', 235.0)
    assert bad['verdict'] == 'fail'
    open_ = sc.check('stress_range', 300.0, p, s, 'stress_range_allow_n7mm2', 235.0)
    assert open_['verdict'] == 'not confirmed' and open_['utilisation'] == pytest.approx(300 / 235)
    #a value set by the user but still marked 'to be confirmed' gives no verdict either
    p['stress_range_allow_n7mm2'] = 400.0
    assert sc.check('stress_range', 300.0, p, s, 'stress_range_allow_n7mm2', 235.0)['verdict'] == 'not confirmed'
    s['stress_range_allow_n7mm2'] = 'EN 13941-1 table 7'
    assert sc.check('stress_range', 300.0, p, s, 'stress_range_allow_n7mm2', 235.0)['verdict'] == 'pass'


def test_series_limit_overrides_the_parameter():
    p, s = params(), sources()
    r = sc.check('axial_stress', 160.0, p, s, 'sigma_ax_allow_n7mm2', 235.0, limit=150.0, limit_source='pipe series')
    assert r['verdict'] == 'fail' and r['limit'] == 150.0


MAX_COVER = {  # DN: (da mm, s mm, Da standard mm, maximum cover m), PHB 9/12
    20: (26.9, 2.6, 90, 2.10), 50: (60.3, 3.2, 125, 3.40), 100: (114.3, 3.6, 200, 4.00), 200: (219.1, 4.5, 315, 4.80),
    300: (323.9, 5.6, 450, 4.90), 1000: (1016.0, 11.0, 1200, 5.30)}


def _shearAtCover(da, s, Da, cover):
    carriers = [{'E': 211800e6, 'alpha': 11.3e-6, 'd_o': da / 1000, 'wall': s / 1000}]
    soil = fe.soil(cover, Da / 1000, fe.pipeWeight(carriers, Da / 1000), 0.40, 19.0, 32.5)
    return sc.purShear(soil['f_ax'], [da / 1000])


@pytest.mark.parametrize('dn', sorted(MAX_COVER))
def test_maximum_cover_by_pur_shear(dn):
    """PHB 9/12: the PUR shear at the steel pipe reaches 0.04 N/mm2 at the maximum cover (mu 0.40, 19 kN/m3,
    32.5 deg) within 1 %."""
    assert _shearAtCover(*MAX_COVER[dn]) == pytest.approx(0.04, rel=0.01)


def test_maximum_cover_dn500_outlier():
    """DN 500 is the one row of PHB 9/12 the shear check does not reproduce (5.05 m, against the trend of DN 450
    with 4.85 m): +7 %. Kept so a change of the formula shows up here."""
    assert _shearAtCover(508.0, 6.3, 710, 5.05) == pytest.approx(0.0427, rel=0.01)


def test_minimum_cover():
    #PHB 9/11: DN 200 single pipe under SLW 60: 0.50 m; DN 100 under SLW 12: 0.40 m; twin Dr-150 SLW 60: 0.60 m
    assert cat.minimumCover(200, False, 33.3) == 0.50
    assert cat.minimumCover(100, False, 6.7) == 0.40
    assert cat.minimumCover(150, True, 33.3) == 0.60
    assert cat.minimumCover(250, True, 33.3) is None
    r = sc.minimumCoverCheck(0.45, 0.2191, False, 33.3)
    assert r['verdict'] == 'fail' and r['limit'] == 0.50 and r['source'] == cat.SOURCE_MIN_COVER


def test_nominal_diameter():
    assert cat.nominalDiameter(0.1143) == 100
    assert cat.nominalDiameter(0.1150) == 100
    assert cat.nominalDiameter(0.120) is None


# ---------------------------------------------------------------- pads
def test_pad_curve():
    assert cat.padStrain(0.045) == pytest.approx(0.25)
    assert cat.padStrain(0.110) == pytest.approx(0.50)
    assert cat.padStrain(0.0775) == pytest.approx(0.375)


def test_pad_thickness_and_pieces():
    p = params()
    assert sc.padThickness(0.019, p) == pytest.approx(0.040)       # 50 % of 40 mm
    assert sc.padThickness(0.050, p) == pytest.approx(0.120)       # 100 mm needed -> three layers
    run = sc.padRuns([0.0, 0.5, 1.0, 1.5, 2.0, 2.5], [0.05, 0.04, 0.03, 0.025, 0.01, 0.0], 0.02, p)
    assert run == pytest.approx((0.0, 2.0, 0.120))
    assert sc.padRuns([0.0, 1.0], [0.01, 0.0], 0.02, p) is None
