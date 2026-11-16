# coding=utf-8
"""Required load and penalties of the cost optimization (OpenSpec change cost-optimization). No database."""
import os

import numpy as np
import pytest

from districts.utility_functions.penalties import customerValues, degreeHours, penaltyCost, penaltyNpv
from districts.utility_functions.required_load import (
    customerSourceFiles, ensureRequired, readRequired, requiredAt, requiredFilePath, unmetKwh,
)


def test_degree_hours_only_when_needed():
    w = [1.0, 1.0, 1.0, 1.0]
    troom = [23.0, 19.0, 27.0, 23.0]
    tset = [21.0, 21.0, 26.0, 26.0]
    hcmode = [1, 1, -1, -1]
    # 23 °C in heating mode and 23 °C in cooling mode count nothing; 19 vs 21 - 0.5 -> 1.5 K; 27 vs 26 + 0.5 -> 0.5 K
    assert degreeHours(troom, tset, hcmode, w, tolerance=0.5) == pytest.approx(2.0)
    assert degreeHours([23.0], [21.0], [0], [1.0]) == 0.0


def test_penalty_relative_to_the_reference():
    assert penaltyCost({1: (25.0, 0.0)}, {1: (10.0, 0.0)}, 2.0, 0.5) == pytest.approx(30.0)
    assert penaltyCost({1: (5.0, 3.0)}, {1: (10.0, 1.0)}, 2.0, 0.5) == pytest.approx(1.0)
    assert penaltyNpv(100.0, 0.0, 40) == pytest.approx(4000.0)


def test_unmet_load():
    w = [1.0, 1.0]
    assert unmetKwh([10000.0, 10000.0], [9000.0, 9900.0], w) == pytest.approx(1.0)  # 9.9 kW within the 2 %
    assert unmetKwh([5000.0], [-4000.0], [1.0], mode='cooling') == pytest.approx(1.0)


def test_source_file_and_interpolation(tmp_path):
    path = tmp_path / 'load.prn'
    path.write_text('# hour load\n0 10\n1 20\n2 30\n', encoding='utf-8')
    hours, required = readRequired(str(path), 2, 'kW')
    assert list(required) == [10000.0, 20000.0, 30000.0]
    assert list(requiredAt(hours, required, [0.5, 1.5])) == [15000.0, 25000.0]


def test_required_list_and_customer_values(tmp_path):
    config = {'pathProjects': str(tmp_path) + os.sep, 'projectName': 'p', 'versionName': 'v'}
    template = tmp_path / 'p' / 'customer_templates' / '5_sf' / '5_sf.idm'
    template.parent.mkdir(parents=True)
    template.write_text('((SOURCE-FILE :N "load" :T SOURCE-FILE))', encoding='utf-8')
    (tmp_path / 'p' / 'customer_templates' / '1_lm' / '1_lm.idm').parent.mkdir(parents=True)
    (tmp_path / 'p' / 'customer_templates' / '1_lm' / '1_lm.idm').write_text('((MODEL :N "loadmodel"))', encoding='utf-8')
    entries = ensureRequired(config, ['1_lm', '5_sf'])
    assert entries == [{'template': '5_sf', 'column': 2, 'unit': 'W', 'mode': 'heating'}] and os.path.exists(requiredFilePath(config))
    load = tmp_path / 'load.prn'
    load.write_text('0 10000\n8760 10000\n', encoding='utf-8')
    folder = tmp_path / 'p' / 'versions' / 'v' / 'network_1' / 'customer_7'
    folder.mkdir(parents=True)
    (folder / 'sf-macro.idm').write_text('((SOURCE-FILE :N "SOURCE-FILE-1" :SF "{}"))'.format(str(load).replace('\\', '\\\\')), encoding='utf-8')
    assert customerSourceFiles(config, 1, 7) == [str(load)]
    series = {'power': {7: np.array([9000.0, 10000.0])}, 'troom': {7: np.array([20.0, 21.0])}, 'tset': {7: np.array([21.0, 21.0])},
              'hcmode': {7: np.array([1, 1])}}
    values = customerValues(series, [0, 1], [1.0, 1.0], entries, {7: '5_sf'}, config, 1)
    assert values[7] == (pytest.approx(0.5), pytest.approx(1.0))
