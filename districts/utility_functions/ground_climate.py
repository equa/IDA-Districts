#sky temperature, sun elevation and global radiation as IDA's ENVIRONMENT model (ClimateNmf/climate.nmf) computes them,
#so the start state of a ground collector sees the sky of the simulation (change ground-collector-model, design G4);
#plain Python with numpy/scipy, no QGIS
import math

import numpy as np
from scipy.optimize import brentq

ABS_ZERO = -273.15
SIGMA = 5.670374419e-8

#SATPRES of PsycfuncNmf/psychro3.for (ASHRAE 1989): over ice below 0 degC, over water above, blended over 0.15 K
_C1, _C2, _C3, _C4, _C5, _C6, _C7 = -5674.5359, 6.3925247, -0.9677843e-2, 0.62215701e-6, 0.20747825e-8, -0.9484024e-12, 4.1635019
_C8, _C9, _C10, _C11, _C12, _C13 = -5800.2206, 1.3914993, -0.048640239, 0.41764768e-4, -0.14452093e-7, 6.5459673
_DT = 0.15
_PI_F77 = 3.1415927


def _overIce(tk):
    return _C1 / tk + _C2 + _C3 * tk + _C4 * tk ** 2 + _C5 * tk ** 3 + _C6 * tk ** 4 + _C7 * math.log(tk)


def _overWater(tk):
    return _C8 / tk + _C9 + _C10 * tk + _C11 * tk ** 2 + _C12 * tk ** 3 + _C13 * math.log(tk)


def satPres(t):
    """Saturation pressure of water vapour [Pa] at t [degC] (IDA SATPRES)."""
    if -_DT / 2 < t < _DT / 2:
        tk = _DT / 2 - ABS_ZERO
        pp = math.exp(_overWater(tk))
        ppd = pp * (-_C8 / tk ** 2 + _C10 + 2 * _C11 * tk + 3 * _C12 * tk ** 2 + _C13 / tk)
        pm = math.exp(_overIce(-_DT / 2 - ABS_ZERO))
        a, b, c = pp - pm - ppd * _DT, ppd, pm + ppd * _DT / 2
        return a * 0.5 * (1 + math.sin(_PI_F77 / _DT * t)) + b * t + c
    tc = min(max(t, -200.0), 200.0)
    tk = tc - ABS_ZERO
    return math.exp(_overIce(tk) if tc < -_DT / 2 else _overWater(tk))


def satTemp(p):
    """Saturation temperature [degC] at the vapour pressure p [Pa] (IDA SATTEMP, the inverse of SATPRES)."""
    if p <= 0:
        raise ValueError('vapour pressure must be positive, not {}'.format(p))
    return brentq(lambda t: satPres(t) - p, -150.0, 199.0, xtol=1e-9)


def skyTemperature(t_air, rel_hum, sky_cover=None, d_t_air_sky=5.0):
    """TSky [degC] of IDA's ENVIRONMENT model (TSkyModel WCA, its default). Without a valid sky cover [%] (missing,
    below 0 or above 100) IDA falls back to TAir - dTAirSky, which is what climate files without cloudiness get."""
    t_air = np.asarray(t_air, dtype=float)
    rel_hum = np.asarray(rel_hum, dtype=float)
    if sky_cover is None:
        return t_air - d_t_air_sky
    cover = np.broadcast_to(np.asarray(sky_cover, dtype=float), t_air.shape)
    result = t_air - d_t_air_sky
    for i in np.flatnonzero((cover >= 0) & (cover <= 100)):
        pvap = satPres(float(t_air.flat[i])) * float(rel_hum.flat[i]) / 100
        n = float(cover.flat[i]) / 100
        emissivity = (0.787 + 0.764 * math.log(1 + satTemp(pvap) / 273.15)) * (1 + 0.224 * n - 0.35 * n ** 2 + 0.28 * n ** 3)
        result.flat[i] = ABS_ZERO + (float(t_air.flat[i]) - ABS_ZERO) * emissivity ** 0.25
    return result


def sunElevation(time_h, lat, long, long_timezone):
    """Elevation of the sun [deg] at time_h hours from the start of the year (standard time; IDA's generic year 0,
    365 days). long and long_timezone in IDA's convention (east negative, e.g. Kalmar -16.3, CET -15)."""
    time_h = np.asarray(time_h, dtype=float)
    day_in_year = np.mod(time_h / 24.0, 365.0)
    day_nr = np.floor(day_in_year) + 1
    hour = day_in_year * 24 - 24 * (day_nr - 1)
    declination = math.radians(23.45) * np.sin(2 * math.pi * (284.5 + day_in_year) / 365)
    b = 2 * math.pi * (day_nr - 81) / 364
    e = 9.87 * np.sin(2 * b) - 7.53 * np.cos(b) - 1.5 * np.sin(b)
    sol_time = hour + 4 * (long_timezone - long) / 60 + e / 60
    solar_time = np.where(sol_time < 0, sol_time + 24, np.where(sol_time > 24, sol_time - 24, sol_time))
    omega = np.radians((solar_time - 12) * 15)
    sin_elev = (math.cos(math.radians(lat)) * np.cos(declination) * np.cos(omega)
                + math.sin(math.radians(lat)) * np.sin(declination))
    return np.degrees(np.arcsin(np.clip(sin_elev, -1.0, 1.0)))


def globalHorizontal(i_dir_norm, i_diff_hor, elevation_deg):
    """Global radiation on the horizontal [W/m2]: direct normal on the horizontal while the sun is up, plus diffuse."""
    sin_elev = np.sin(np.radians(np.asarray(elevation_deg, dtype=float)))
    return np.maximum(np.asarray(i_dir_norm, dtype=float) * np.maximum(sin_elev, 0.0), 0.0) \
        + np.maximum(np.asarray(i_diff_hor, dtype=float), 0.0)


def weatherFromFile(path, site, albedo=0.25, d_t_air_sky=5.0, hours=None):
    """The GroundSurface inputs from a climate file, its columns read as the generated climate macro reads them
    (climate_macro.climateColumns): the sky temperature with the file's sky cover and the albedo from its ALBEDO
    column [%] when they exist, otherwise the given albedo. hours: only the first rows (e.g. 8760)."""
    from .climate_macro import climateColumns
    columns = climateColumns(path)
    data = np.loadtxt(path, comments='#', ndmin=2)
    if hours is not None:
        data = data[:hours]
    col = lambda key: data[:, columns.number(key) - 1] if columns.number(key) else None
    cover = col('skycover')
    weather = weatherFromClimate(col('time'), col('tair'), col('relhum'), col('idirnorm'), col('idiffhor'), site,
                                 sky_cover=cover, d_t_air_sky=d_t_air_sky, albedo=albedo)
    albedo_column = col('albedo')
    if albedo_column is not None:
        weather['albedo'] = albedo_column / 100.0
    return weather


def weatherFromClimate(time_h, t_air, rel_hum, i_dir_norm, i_diff_hor, site, sky_cover=None, d_t_air_sky=5.0,
                       albedo=0.25):
    """The inputs of GroundSurface (TAir, IGlob, TSky, albedo) from climate-file columns; site = dict(lat, long,
    long_timezone); albedo one value or a column."""
    elevation = sunElevation(time_h, site['lat'], site['long'], site['long_timezone'])
    t_air = np.asarray(t_air, dtype=float)
    return {
        'TAir': t_air,
        'IGlob': globalHorizontal(i_dir_norm, i_diff_hor, elevation),
        'TSky': skyTemperature(t_air, rel_hum, sky_cover, d_t_air_sky),
        'albedo': np.broadcast_to(np.asarray(albedo, dtype=float), t_air.shape).copy(),
    }
