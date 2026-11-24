"""Validation cases of the ground collector model (change ground-collector-model, design G9): the stored Python model
columns are what the model computes now, and the model stays within the limits of the stored 2D reference with the
full surface balance (Kalmar climate, third year). No DB, no IDA. Regenerate with make_ground_collector_cases.py."""
import os

import numpy as np
import pytest

from districts.test import make_ground_collector_cases as mk
from districts.utility_functions import ground_rc as rc
from districts.utility_functions.ground_collector_contract import CONTRACT_VERSION

CASES = ('horizontal_ring', 'vertical_ring', 'flat_meander', 'bare_pipe', 'horizontal_ring_frozen',
         'horizontal_ring_wall_step')
#design G9: the six-node model against the 2D reference with the full surface balance
ANNUAL_LIMIT = 0.03
WINTER_LIMIT = 0.07


def _read(name):
    return mk.readCase(os.path.join(mk.CASES_DIR, name))


def test_all_cases_present():
    assert sorted(os.listdir(mk.CASES_DIR)) == sorted(CASES)


@pytest.mark.parametrize('name', CASES)
def test_case_is_current(name):
    """The model columns are reproduced from the stored inputs: a change of the model needs new cases."""
    case, series = _read(name)
    assert case['contract_version'] == CONTRACT_VERSION
    assert case['fit_version'] == rc.FIT_VERSION
    assert case['fit']['accepted']
    model = mk.runModel(case, series)
    for column, values in model.items():
        np.testing.assert_allclose(values, series[column], atol=2e-3, err_msg='{} {}'.format(name, column))


@pytest.mark.parametrize('name', CASES)
def test_model_close_to_the_reference(name):
    """Heat into the fluid against the 2D reference with the full surface balance."""
    _, series = _read(name)
    q, q_ref = -series['model_q_wall'], -series['ref_q_wall']
    day = (series['hour'] / 24) % 365
    winter = (day < 90) | (day >= 305)
    assert abs(q.sum() / q_ref.sum() - 1) <= ANNUAL_LIMIT
    if name != 'horizontal_ring_wall_step':
        # the step lies in Jan-Mar only: its winter sum is mostly the step's transient
        assert abs(q[winter].sum() / q_ref[winter].sum() - 1) <= WINTER_LIMIT
