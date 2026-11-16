# coding=utf-8
"""Representative periods (OpenSpec change representative-periods): the choice of the weeks from the climate file,
the weights of the simulated hours and the coverage of the year.

Every hour of the year is assigned to the simulated hours of the same hour of day: split linearly by air temperature between the nearest simulated hour below and above, else to the nearest. The weight
of a simulated hour is the number of year hours it stands for (all weights add up to 8760)."""
import datetime
import json
import os
import re

import numpy as np

HOURS = 8760
COVERAGE_K = 1.0  # a year hour is covered if a simulated hour is within 1 K
COVERAGE_WARNING = 0.40  # share of the year not covered
PERIODS_FILE = 'periods.json'


# ---------------------------------------------------------------- climate
def climateFile(config):
    """Path of the climate file of the project (SOURCE-FILE of climate-macro.idm; clim: = IDA Districts climate folder)."""
    macro = os.path.join(config['pathProjects'] + config['projectName'], 'climate', 'climate', 'climate-macro.idm')
    with open(macro, encoding='utf-8-sig', errors='replace') as f:
        match = re.search(r':SF "([^"]+)"', f.read())
    if not match:
        raise FileNotFoundError(macro)
    path = match.group(1).replace('\\\\', '\\')
    if path.lower().startswith('clim:'):
        path = os.path.join(config['pathDistricts'], 'climate', path[5:])
    return path


def readClimate(path):
    """Hourly air temperature (second column) of an IDA climate file: the first 8760 values (the files hold the hour
    points 0 ... 8760, leap years up to 8784)."""
    values = []
    with open(path, encoding='utf-8-sig', errors='replace') as f:
        for line in f:
            fields = line.split()
            try:
                values.append(float(fields[1]))
            except (IndexError, ValueError):
                continue
    if not HOURS <= len(values) <= 8785:
        raise ValueError(len(values))
    return np.array(values[:HOURS])


# ---------------------------------------------------------------- classes of the hours
def hourClasses(year):
    """Hour of day of every hour of the year. No weekday/weekend classes: they halve the candidates per class and
    doubled the error of a convex quantity (pump power ~ load^3: 4.4 % instead of 2.0 % on BROMMA.PRN)."""
    return np.arange(HOURS) % 24


def assign(t_year, classes, sim_hours):
    """For every year hour: (lower sim hour, upper sim hour, share of the lower) and the distance to the nearest [K]."""
    lower = np.zeros(HOURS, dtype=int)
    upper = np.zeros(HOURS, dtype=int)
    share = np.ones(HOURS)
    distance = np.zeros(HOURS)
    sim_hours = np.asarray(sim_hours)
    for c in range(24):
        year_idx = np.nonzero(classes == c)[0]
        sim = sim_hours[classes[sim_hours] == c]
        if len(sim) == 0:
            sim = sim_hours  # no simulated hour of this class: any hour
        order = np.argsort(t_year[sim])
        sim, t_sim = sim[order], t_year[sim][order]
        t = t_year[year_idx]
        pos = np.searchsorted(t_sim, t)
        lo = np.clip(pos - 1, 0, len(sim) - 1)
        hi = np.clip(pos, 0, len(sim) - 1)
        t_lo, t_hi = t_sim[lo], t_sim[hi]
        span = t_hi - t_lo
        w_lo = np.where(span > 0, (t_hi - t) / np.where(span > 0, span, 1), 1.0)
        w_lo = np.clip(w_lo, 0, 1)
        # outside the simulated range: the nearest only
        w_lo = np.where(t <= t_sim[0], 1.0, np.where(t >= t_sim[-1], 0.0, w_lo))
        lower[year_idx], upper[year_idx], share[year_idx] = sim[lo], sim[hi], w_lo
        distance[year_idx] = np.minimum(np.abs(t - t_lo), np.abs(t - t_hi))
    return lower, upper, share, distance


def weights(t_year, year, sim_hours, shape=None):
    """{sim hour: (weight, profile sum)} and the coverage (share of the year farther than 1 K from a simulated hour)."""
    classes = hourClasses(year)
    lower, upper, share, distance = assign(t_year, classes, sim_hours)
    shape = np.ones(HOURS) if shape is None else np.asarray(shape[:HOURS])
    np_w = np.zeros(HOURS)
    np_s = np.zeros(HOURS)
    np.add.at(np_w, lower, share)
    np.add.at(np_w, upper, 1 - share)
    np.add.at(np_s, lower, share * shape)
    np.add.at(np_s, upper, (1 - share) * shape)
    w = {int(h): (float(np_w[h]), float(np_s[h])) for h in sim_hours}
    return w, float(np.mean(distance > COVERAGE_K))


def meanDistance(t_year, classes, sim_hours):
    return float(np.mean(assign(t_year, classes, sim_hours)[3]))


# ---------------------------------------------------------------- choice of the weeks
def weekHours(start_day, days):
    return list(range(start_day * 24, (start_day + days) * 24))


def chooseWeeks(t_year, year, days=7, mode='heat', warmest=False):
    """Start days and roles of the weeks: the anchor (coldest week for heating, warmest for cooling) fixed, two weeks
    for the best coverage (coordinate descent from the weeks around the 50 % and 85 % quantiles), optionally the
    warmest week as well. The weeks do not overlap."""
    starts = np.arange(0, 365 - days + 1)
    means = np.array([t_year[s * 24:(s + days) * 24].mean() for s in starts])
    anchor = int(starts[means.argmin() if mode == 'heat' else means.argmax()])
    weeks = [(anchor, 'anchor')]
    if warmest and mode == 'heat':
        weeks.append((int(starts[means.argmax()]), 'warmest'))
    fixed = [s for s, _ in weeks]

    def overlaps(s, others):
        return any(abs(s - o) < days for o in others)

    free = []
    for q in (50, 85) if mode == 'heat' else (50, 15):
        target = np.percentile(t_year, q)
        for s in starts[np.argsort(np.abs(means - target))]:
            if not overlaps(int(s), fixed + free):
                free.append(int(s))
                break
    classes = hourClasses(year)

    def score(free_weeks):
        return meanDistance(t_year, classes, [h for s in fixed + free_weeks for h in weekHours(s, days)])

    best = score(free)
    for _ in range(2):
        for k in range(len(free)):
            for s in starts[::2]:
                s = int(s)
                if overlaps(s, fixed + free[:k] + free[k + 1:]):
                    continue
                trial = free[:k] + [s] + free[k + 1:]
                value = score(trial)
                if value < best:
                    best, free = value, trial
    return weeks + [(s, 'coverage') for s in free]


# ---------------------------------------------------------------- dates and the periods file
def weekDates(year, start_day, days, startup_days):
    """(calc from, calc to, start-up from, start-up to) of a week; the start-up stays within the year."""
    start = datetime.datetime(year, 1, 1) + datetime.timedelta(days=start_day)
    end = start + datetime.timedelta(days=days)
    startup = max(datetime.datetime(year, 1, 1), start - datetime.timedelta(days=startup_days))
    return start, end, startup, max(start, startup + datetime.timedelta(hours=1))


def periodsPath(config):
    return os.path.join(config['pathProjects'] + config['projectName'], 'versions', config['versionName'], PERIODS_FILE)


def savePeriods(config, data):
    with open(periodsPath(config), 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=1)


def loadPeriods(config):
    path = periodsPath(config)
    if not os.path.exists(path):
        return None
    with open(path, encoding='utf-8') as f:
        return json.load(f)


def deletePeriods(config):
    path = periodsPath(config)
    if os.path.exists(path):
        os.remove(path)
