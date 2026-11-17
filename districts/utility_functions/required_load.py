# coding=utf-8
"""Required load of source-file customers (OpenSpec change cost-optimization, D20): the column of the source file
per customer template, saved in the project as requiredLoads.json, and the unmet load of a customer."""
import json
import os
import re

import numpy as np

REQUIRED_FILE = 'requiredLoads.json'
TOLERANCE = 0.02  # unmet only above 2 % of the required load


def requiredFilePath(config):
    return os.path.join(config['pathProjects'] + config['projectName'], REQUIRED_FILE)


def templateHasSourceFile(config, t_name):
    path = os.path.join(config['pathProjects'] + config['projectName'], 'customer_templates', t_name, t_name + '.idm')
    if not os.path.exists(path):
        return False
    with open(path, encoding='utf-8-sig', errors='replace') as f:
        return 'SOURCE-FILE' in f.read()


def newEntry(t_name, column=2, unit='W', mode='heating'):
    return {'template': t_name, 'column': column, 'unit': unit, 'mode': mode}


def loadRequired(config):
    path = requiredFilePath(config)
    if not os.path.exists(path):
        return None
    with open(path, encoding='utf-8') as f:
        return json.load(f).get('entries', [])


def saveRequired(config, entries):
    with open(requiredFilePath(config), 'w', encoding='utf-8') as f:
        json.dump({'entries': entries}, f, indent=1)


def ensureRequired(config, t_names):
    """The project's list; the customer templates with a SOURCE-FILE with the defaults if there is no file yet."""
    entries = loadRequired(config)
    if entries is None:
        entries = [newEntry(t) for t in t_names if templateHasSourceFile(config, t)]
        saveRequired(config, entries)
    return entries


def customerSourceFiles(config, submodel, cid):
    """:SF paths of the invoked customer (sf-macro.idm of its folder in the version's network folder)."""
    path = os.path.join(config['pathProjects'] + config['projectName'], 'versions', config['versionName'],
                        'network_{}'.format(submodel), 'customer_{}'.format(cid), 'sf-macro.idm')
    if not os.path.exists(path):
        return []
    with open(path, encoding='utf-8-sig', errors='replace') as f:
        return [p.replace('\\\\', '\\') for p in re.findall(r':SF "([^"]+)"', f.read())]


def readRequired(path, column, unit='W'):
    """(hours, required load [W]) of a source file: hour column 1, the load in column `column` (1-based)."""
    hours, values = [], []
    with open(path, encoding='utf-8-sig', errors='replace') as f:
        for line in f:
            fields = line.split()
            try:
                hours.append(float(fields[0]))
                values.append(float(fields[column - 1]))
            except (IndexError, ValueError):
                continue
    factor = 1000.0 if str(unit).lower() == 'kw' else 1.0
    return np.array(hours), np.abs(np.array(values)) * factor


def requiredAt(file_hours, required, result_hours):
    """required load linearly interpolated to the result time steps (hours of the year)"""
    return np.interp(np.asarray(result_hours, dtype=float), file_hours, required)


def unmetKwh(required, supplied, weights, mode='heating', tolerance=TOLERANCE):
    """unmet load [kWh per year]: max(0, required - supplied) per step above the tolerance, weighted.
    supplied: the simulated customer power (heating > 0, cooling < 0)."""
    supplied = np.asarray(supplied, dtype=float)
    supplied = np.maximum(supplied, 0) if mode == 'heating' else np.maximum(-supplied, 0)
    deficit = np.asarray(required, dtype=float) - supplied
    deficit = np.where(deficit > tolerance * np.asarray(required, dtype=float), deficit, 0.0)
    return float(np.sum(np.asarray(weights, dtype=float) * deficit) / 1000)
