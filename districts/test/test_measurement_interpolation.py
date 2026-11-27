# coding=utf-8
"""Interpolation step of the measurement import: entered in seconds, as the dialog's label and load results say."""
import numpy as np
import pytest

from ..ida_rv import interpolationHours


def test_step_in_seconds():
    # quarter-hourly data over a day, interpolated to hourly values (3600 s)
    hours = interpolationHours(0.25, 23.75, 3600)
    assert np.allclose(hours, np.arange(0, 24, 1.0))


def test_start_on_full_steps():
    hours = interpolationHours(10.2, 12.9, 1800)
    assert hours[0] == pytest.approx(10.0) and hours[-1] == pytest.approx(12.5)
    assert np.allclose(np.diff(hours), 0.5)
