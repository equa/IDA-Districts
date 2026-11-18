# coding=utf-8
"""Heating or cooling per step from the plants' heat flows with a deadband (OpenSpec change cost-optimization, D23)."""
import datetime

import numpy as np

from districts.utility_functions.network_modes import deadbandModes, heatMask, plantPairs, segmentStarts, sequenceModes


def test_pairs_from_the_plant_connections():
    rows = [{'conn_seq': 1, 'type': 1, 'temp': 70}, {'conn_seq': 2, 'type': 1, 'temp': 10},
            {'conn_seq': 3, 'type': 2, 'temp': 30}, {'conn_seq': 4, 'type': 2, 'temp': 18}]
    assert plantPairs(rows) == [(1, 3, 'heat'), (2, 4, 'cold')]


def test_deadband_keeps_the_mode():
    # range 100 - (-100) = 200 W, band 10 % = 20 W: the small flows inside keep the previous mode
    q = [100, 10, -10, -50, -15, 15, 50]
    assert deadbandModes(q, 10).tolist() == [True, True, True, False, False, False, True]
    # without a band every sign change switches
    assert deadbandModes(q, 0).tolist() == [True, True, False, False, False, True, True]


def test_start_inside_the_band_and_fallback():
    # the first steps take the mode of the first step outside the band
    assert deadbandModes([1, -1, -100, 100], 10).tolist() == [False, False, False, True]
    assert deadbandModes([0, 0, 0], 5, fallback='cold').tolist() == [False, False, False]


def test_each_week_starts_again():
    t0 = datetime.datetime(2026, 1, 1)
    times = [t0 + datetime.timedelta(hours=h) for h in (0, 1, 2)] + [t0 + datetime.timedelta(days=180, hours=h) for h in (0, 1, 2)]
    starts = segmentStarts(times, 1.0)
    assert starts == [0, 3]
    # the second week begins inside the band: its own first flow outside decides, not the end of the first week
    assert deadbandModes([100, 100, 100, 1, -100, -100], 5, starts=starts).tolist() == [True, True, True, False, False, False]


def test_sequence_modes_and_summary():
    flows = {1: np.array([500.0, 500.0, 100.0, 100.0]), 3: np.array([-300.0, -300.0, -400.0, -400.0])}
    masks, summary = sequenceModes([(1, 3, 'heat'), (2, 4, 'cold')], flows, 5, [0], weights=[2190] * 4)
    assert masks[1].tolist() == masks[3].tolist() == [True, True, False, False]
    assert summary['1/3']['heat_h'] == 4380 and summary['1/3']['cold_h'] == 4380 and summary['1/3']['source'] == 'plants'
    # a pair without plant results keeps its template mode
    assert masks[2] == 'cold' and summary['2/4']['source'] == 'template' and summary['2/4']['heat_h'] is None
    assert heatMask(masks, 2, 3).tolist() == [False] * 3 and heatMask(masks, 9, 2).tolist() == [True, True]
