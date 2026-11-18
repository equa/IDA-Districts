# coding=utf-8
"""Penalties of the cost optimization (OpenSpec change cost-optimization, D9): degree hours of the load models and
unmet load of source-file customers per customer, relative to the reference iteration."""
import numpy as np

from .economics import annuityFactor
from .required_load import TOLERANCE, customerSourceFiles, readRequired, requiredAt, unmetKwh


def degreeHours(troom, tset, hcmode, weights, tolerance=0.5):
    """Kh per year: heating needed and not reached (mode 1, TRoom < TSet - tol) or cooling (mode -1, TRoom > TSet + tol);
    a room temperature between the setpoints counts nothing."""
    troom, tset, hcmode, w = (np.asarray(a, dtype=float) for a in (troom, tset, hcmode, weights))
    heating = np.where(hcmode > 0.5, np.maximum(0, tset - tolerance - troom), 0.0)
    cooling = np.where(hcmode < -0.5, np.maximum(0, troom - tset - tolerance), 0.0)
    return float(np.sum(w * (heating + cooling)))


def penaltyCost(current, price_kh, price_kwh):
    """yearly penalty [€]: per customer price x Kh and unmet kWh, against the setpoint and the required load (not
    against iteration 0: deficits of the reference count as well, and an iteration that removes them gains)"""
    return sum(price_kh * max(0.0, kh) + price_kwh * max(0.0, kwh) for kh, kwh in current.values())


def deficitCustomers(values):
    """customers with degree hours or unmet load"""
    return sorted(cid for cid, (kh, kwh) in values.items() if kh > 1e-6 or kwh > 1e-6)


def penaltyNpv(yearly, interest_pct, period):
    """present value of a constant yearly penalty over the period"""
    factor = annuityFactor(interest_pct, period)
    return yearly / factor if factor else 0.0


def customerValues(series, hours, weights, required_entries, templates, config, submodel, tolerance=0.5, unmet_tolerance=TOLERANCE):
    """{cid: (Kh, unmet kWh)} per year from the series {'troom'|'tset'|'hcmode'|'power': {cid: array}};
    templates {cid: t_name}; required_entries of requiredLoads.json; unmet_tolerance: share of the required load."""
    by_template = {e['template']: e for e in required_entries or []}
    values = {}
    for cid in set(series.get('troom', {})) | set(series.get('power', {})):
        kh = 0.0
        if cid in series.get('troom', {}) and cid in series.get('tset', {}) and cid in series.get('hcmode', {}):
            kh = degreeHours(series['troom'][cid], series['tset'][cid], series['hcmode'][cid], weights, tolerance)
        kwh = 0.0
        entry = by_template.get(templates.get(cid))
        if entry and cid in series.get('power', {}):
            files = customerSourceFiles(config, submodel, cid)
            if files:
                file_hours, required = readRequired(files[0], int(entry.get('column', 2)), entry.get('unit', 'W'))
                kwh = unmetKwh(requiredAt(file_hours, required, hours), series['power'][cid], weights, entry.get('mode', 'heating'), unmet_tolerance)
        values[cid] = (kh, kwh)
    return values
