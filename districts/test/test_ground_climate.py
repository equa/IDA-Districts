"""Sky temperature, sun elevation and radiation as IDA's ENVIRONMENT model (change ground-collector-model): no DB, no IDA.
Test data: KALMAR.PRN with TSKY exported from an IDA run (test/data/ground_climate_ida.csv)."""
import os

import numpy as np
import pytest

from districts.utility_functions import ground_climate as gc

DATA = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'data', 'ground_climate_ida.csv')
KALMAR = {'lat': 56.73, 'long': -16.3, 'long_timezone': -15}


def _idaData():
    rows = [line.strip().split(',') for line in open(DATA, encoding='utf-8') if line.strip() and not line.startswith('#')]
    header, rows = rows[0], rows[1:]
    col = {name: i for i, name in enumerate(header)}
    climate = [r for r in rows if r[col['kind']] == 'c']
    samples = [r for r in rows if r[col['kind']] == 's']
    c = {name: np.array([float(r[col[name]]) for r in climate]) for name in ('time_h', 'TAIR', 'RELHUM', 'IDIRNORM', 'IDIFFHOR')}
    s = {name: np.array([float(r[col[name]]) for r in samples]) for name in ('time_h', 'TSKY', 'ELEVSUN')}
    return c, s, header


def test_saturation_pressure():
    assert gc.satPres(0.0) == pytest.approx(611.2, rel=2e-3)
    assert gc.satPres(20.0) == pytest.approx(2339.0, rel=2e-3)
    assert gc.satPres(-10.0) == pytest.approx(259.9, rel=5e-3)
    for t in (-25.0, -0.05, 0.05, 12.3, 35.0):
        assert gc.satTemp(gc.satPres(t)) == pytest.approx(t, abs=1e-6)


def test_sky_temperature_as_ida():
    """KALMAR.PRN has no cloudiness: IDA computes TAir - 5 K; its output times lie between the climate hours."""
    c, s, _ = _idaData()
    t_sky = gc.skyTemperature(c['TAIR'], c['RELHUM'])
    for start in (0.0, 4344.0):
        window = (s['time_h'] >= start) & (s['time_h'] <= start + 504)
        hours = (c['time_h'] >= start) & (c['time_h'] <= start + 504)
        python = np.interp(s['time_h'][window], c['time_h'][hours], t_sky[hours])
        assert np.max(np.abs(python - s['TSKY'][window])) <= 0.1


def test_sky_temperature_with_cloud_cover():
    t_air, rh = np.full(3, 5.0), np.full(3, 70.0)
    t_sky = gc.skyTemperature(t_air, rh, sky_cover=np.array([0.0, 50.0, 100.0]))
    assert t_sky[0] < t_sky[1] < t_sky[2] < 5.0 + 1e-9
    assert t_sky[0] < -5.0
    # out of range: IDA's fallback
    assert gc.skyTemperature([5.0], [70.0], sky_cover=[120.0])[0] == pytest.approx(0.0)


def test_sun_elevation():
    """Solar noon at the summer solstice: 90 - latitude + declination, within the equation of time."""
    lat = 47.4
    hours = np.arange(171 * 24, 172 * 24, 0.25)
    elevation = gc.sunElevation(hours, lat, -8.5, -15)
    assert elevation.max() == pytest.approx(90 - lat + 23.45, abs=0.3)
    assert elevation.min() < -15


def test_sun_elevation_as_ida():
    """ELEVSUN of the same IDA run, at its output times: a January and a July week."""
    _, s, _ = _idaData()
    python = gc.sunElevation(s['time_h'], KALMAR['lat'], KALMAR['long'], KALMAR['long_timezone'])
    assert np.max(np.abs(python - s['ELEVSUN'])) <= 0.1


def test_global_radiation():
    rad = gc.globalHorizontal([800.0, 800.0, -5.0], [100.0, 50.0, -1.0], [30.0, -10.0, 20.0])
    assert rad[0] == pytest.approx(800 * 0.5 + 100)
    assert rad[1] == pytest.approx(50.0)
    assert rad[2] >= 0.0


def test_weather_from_climate():
    c, _, _ = _idaData()
    w = gc.weatherFromClimate(c['time_h'], c['TAIR'], c['RELHUM'], c['IDIRNORM'], c['IDIFFHOR'], KALMAR)
    assert set(w) == {'TAir', 'IGlob', 'TSky', 'albedo'}
    assert np.all(w['IGlob'] >= 0)
    np.testing.assert_allclose(w['TSky'], c['TAIR'] - 5.0)
