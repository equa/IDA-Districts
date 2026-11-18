# coding=utf-8
"""Representative periods (OpenSpec change representative-periods): reading the climate, the choice of the weeks, the
weights and the coverage. No database; BROMMA.PRN of the IDA Districts installation if installed."""
import os

import numpy as np
import pytest

from districts.utility_functions.periods import (
    COVERAGE_WARNING, HOURS, chooseWeeks, readClimate, weekDates, weekHours, weights,
)

CLIMATE = os.path.join(os.environ.get('DISTRICTS_TEST_PATH_DISTRICTS', 'C:\\Program Files (x86)\\IDA Districts\\'), 'climate', 'BROMMA.PRN')


@pytest.fixture(scope='module')
def bromma():
    if not os.path.exists(CLIMATE):
        pytest.skip('climate file {} not found'.format(CLIMATE))
    return readClimate(CLIMATE)


def sim_hours(weeks, days=7):
    return [h for s, _ in weeks for h in weekHours(s, days)]


def test_climate_file(bromma, tmp_path):
    assert len(bromma) == HOURS and bromma.min() < -10 and bromma.max() > 25
    short = tmp_path / 'short.prn'
    short.write_text('\n'.join('{} 5.0'.format(h) for h in range(100)))
    with pytest.raises(ValueError) as error:
        readClimate(str(short))
    assert error.value.args == (100,)


def test_weeks_and_weights(bromma):
    weeks = chooseWeeks(bromma, 2026)
    starts = [s for s, _ in weeks]
    means = [bromma[s * 24:(s + 7) * 24].mean() for s in range(359)]
    assert weeks[0] == (int(np.argmin(means)), 'anchor')  # the coldest week
    assert len(weeks) == 3 and all(abs(a - b) >= 7 for a in starts for b in starts if a != b)
    w, coverage = weights(bromma, 2026, sim_hours(weeks))
    assert sum(v[0] for v in w.values()) == pytest.approx(HOURS)
    assert coverage < COVERAGE_WARNING
    load = np.clip(15 - bromma, 0, None)
    heat = sum(w[h][0] * load[h] for h in w) / load.sum() - 1
    pump = sum(w[h][0] * load[h] ** 3 for h in w) / (load ** 3).sum() - 1
    assert abs(heat) < 0.01 and abs(pump) < 0.025


def test_warmest_week_and_cooling(bromma):
    weeks = chooseWeeks(bromma, 2026, warmest=True)
    assert [role for _, role in weeks] == ['anchor', 'warmest', 'coverage', 'coverage']
    means = [bromma[s * 24:(s + 7) * 24].mean() for s in range(359)]
    assert chooseWeeks(bromma, 2026, mode='cold')[0] == (int(np.argmax(means)), 'anchor')
    # a cooling network adds the opposite extreme: the coldest week
    cooling = chooseWeeks(bromma, 2026, mode='cold', warmest=True)
    assert cooling[1] == (int(np.argmin(means)), 'coldest') and len(cooling) == 4


def test_linear_split_between_two_simulated_hours():
    # the same hour of day on three days at 4, 8 and 5 °C; only the first two days are simulated
    t = np.full(HOURS, 30.0)
    t[0], t[24], t[48] = 4.0, 8.0, 5.0
    w, _ = weights(t, 2026, list(range(48)))
    assert w[0][0] == pytest.approx(1 + 0.75) and w[24][0] == pytest.approx(1 + 0.25 + (365 - 3))


def test_one_week_represents_the_year_poorly(bromma):
    _, coverage = weights(bromma, 2026, weekHours(30, 7))
    assert coverage > COVERAGE_WARNING


def test_profile_sum(bromma):
    shape = np.ones(HOURS)
    shape[:24] = 2.0
    w, _ = weights(bromma, 2026, sim_hours(chooseWeeks(bromma, 2026)), shape)
    assert sum(s for _, s in w.values()) == pytest.approx(HOURS + 24)


def test_week_dates_keep_the_start_up_in_the_year():
    calc_from, calc_to, startup_from, startup_to = weekDates(2026, 1, 7, 3)
    assert (calc_from.day, calc_to.day, startup_from.day, startup_from.month) == (2, 9, 1, 1)
    calc_from, _, startup_from, startup_to = weekDates(2026, 100, 7, 3)
    assert (calc_from - startup_from).days == 3 and startup_to == calc_from
