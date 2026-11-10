"""zeta values of the junction connections from textbook values (utility_functions/zeta.py)"""
import math

import pytest

from districts.utility_functions.zeta import (
    ZETA_BRANCH, ZETA_DEFAULTS, ZETA_RUN, classBounds, connectionZetas, frictionFactor, reducerZeta, zetaTables,
)


def test_friction_factor():
    # DN100, 1 m/s, water 70 degC: Re ~ 2.6e5, Colebrook-White 0.01795
    assert frictionFactor(0.1071, 0.000045, 1.0, 0.41e-6) == pytest.approx(0.01795, rel=0.02)
    # smooth pipe, Re 1e5: Blasius 0.316/Re^0.25 = 0.0178
    assert frictionFactor(0.1, 0.0, 1.0, 1e-6) == pytest.approx(0.0178, rel=0.03)
    assert frictionFactor(0.01, 0.000045, 0.1, 1e-6) == pytest.approx(64 / 1000)  # laminar
    assert frictionFactor(None, 0.000045, 1.0, 1e-6) is None


def test_class_bounds_quantile():
    values = [1, 2, 3, 4, 5, 6, 7, 8, 9, 300]  # one short line with a very high share
    equal = classBounds(values, 5)
    assert sum(1 for v in values if v < equal[0][1]) == 9  # equal intervals: all but one in the first class
    quantile = classBounds(values, 5, quantile=True)
    assert quantile[0][0] == 1 and quantile[-1][1] == 300 and len(quantile) == 5
    assert classBounds([0.4] * 5, 5, quantile=True) == [(0.4, 0.4)]


def conn(cid, d, az_deg):
    return {'id': cid, 'd': d, 'az': math.radians(az_deg) if az_deg is not None else None}


def test_reducer_zeta():
    assert reducerZeta(0.1, 0.1) == 0
    assert reducerZeta(0.2, 0.1) == 0  # not smaller
    # beta = 0.5: area ratio 0.25, contraction 0.375, expansion 0.5625
    assert reducerZeta(0.05, 0.1) == pytest.approx((0.375 + 0.5625) / 2)
    assert reducerZeta(None, 0.1) == 0


def test_end_and_equal_pipes():
    assert connectionZetas([conn(1, 0.1, 0)]) == {1: (0.0, 'end')}
    assert connectionZetas([conn(1, 0.1, 0), conn(2, 0.1, 180)]) == {1: (0.0, 'none'), 2: (0.0, 'none')}


def test_reducer():
    result = connectionZetas([conn(1, 0.1, 0), conn(2, 0.05, 180)])
    assert result[1] == (0.0, 'reducer_large')
    assert result[2] == (pytest.approx(reducerZeta(0.05, 0.1)), 'reducer_small')


def test_tee_equal_diameters_run_by_geometry():
    # 1 and 3 are in line, 2 leaves at 90 degrees
    result = connectionZetas([conn(1, 0.1, 0), conn(2, 0.1, 90), conn(3, 0.1, 180)])
    assert result[1] == (pytest.approx(ZETA_RUN[3] / 2), 'run')
    assert result[3] == (pytest.approx(ZETA_RUN[3] / 2), 'run')
    assert result[2] == (pytest.approx(ZETA_BRANCH[3] - ZETA_RUN[3] / 2), 'branch')
    # flow straight through: ZETA_RUN, into the branch: ZETA_BRANCH
    assert result[1][0] + result[3][0] == pytest.approx(ZETA_RUN[3])
    assert result[1][0] + result[2][0] == pytest.approx(ZETA_BRANCH[3])


def test_tee_house_connection_is_branch():
    # the small pipe is the branch even if it is in line with one of the main pipes
    result = connectionZetas([conn(1, 0.1, 0), conn(2, 0.1, 90), conn(3, 0.025, 180)])
    assert result[3][1] == 'branch'
    assert result[1][1] == result[2][1] == 'run'


def test_tee_run_with_reducer():
    result = connectionZetas([conn(1, 0.1, 0), conn(2, 0.08, 180), conn(3, 0.025, 90)])
    assert result[1] == (pytest.approx(ZETA_RUN[3] / 2), 'run')
    assert result[2] == (pytest.approx(ZETA_RUN[3] / 2 + reducerZeta(0.08, 0.1)), 'run')
    assert result[3][1] == 'branch'


def test_cross_and_more():
    result = connectionZetas([conn(1, 0.1, 0), conn(2, 0.1, 90), conn(3, 0.1, 180), conn(4, 0.1, 270)])
    roles = sorted(r for _, r in result.values())
    assert roles == ['branch', 'branch', 'run', 'run']
    assert [z for z, r in result.values() if r == 'run'] == pytest.approx([ZETA_RUN[4] / 2] * 2)
    assert [z for z, r in result.values() if r == 'branch'] == pytest.approx([ZETA_BRANCH[4] - ZETA_RUN[4] / 2] * 2)
    five = connectionZetas([conn(i, 0.1, 72 * i) for i in range(5)])
    assert sorted(r for _, r in five.values()) == ['branch'] * 3 + ['run'] * 2


def test_user_values():
    values = {'tee_run': 0.6, 'tee_branch': 2.0, 'cross_run': 0.8, 'cross_branch': 2.2}
    tee = connectionZetas([conn(1, 0.1, 0), conn(2, 0.1, 90), conn(3, 0.1, 180)], values)
    assert tee[1][0] + tee[3][0] == pytest.approx(0.6)  # straight run
    assert tee[1][0] + tee[2][0] == pytest.approx(2.0)  # into the branch
    cross = connectionZetas([conn(i, 0.1, 90 * i) for i in range(4)], values)
    assert sorted(z for z, _ in cross.values()) == pytest.approx([0.4, 0.4, 1.8, 1.8])
    # missing keys: default values; a branch smaller than half of the run: 0, never negative
    assert zetaTables({'tee_run': 1.0}) == ({3: 1.0, 4: ZETA_RUN[4]}, {3: ZETA_BRANCH[3], 4: ZETA_BRANCH[4]})
    low = connectionZetas([conn(1, 0.1, 0), conn(2, 0.1, 90), conn(3, 0.1, 180)], {'tee_run': 1.0, 'tee_branch': 0.2})
    assert low[2] == (0.0, 'branch')
    # default values unchanged
    assert connectionZetas([conn(1, 0.1, 0), conn(2, 0.1, 90), conn(3, 0.1, 180)]) == \
        connectionZetas([conn(1, 0.1, 0), conn(2, 0.1, 90), conn(3, 0.1, 180)], ZETA_DEFAULTS)


def test_unknown_diameters():
    result = connectionZetas([conn(1, None, 0), conn(2, None, 90), conn(3, None, None)])
    assert sorted(r for _, r in result.values()) == ['branch', 'run', 'run']
