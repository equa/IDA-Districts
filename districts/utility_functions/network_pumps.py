# coding=utf-8
"""List of the pumps that move network water, per template of the project (OpenSpec change pump-power-outputs).

Saved as <project>\\networkPumps.json: the list describes the project's templates and the outputs written into them,
so it is the same for every version. Entries of kind 'variable' are written as outputs; entries of kind 'estimate'
(a component containing a pump without a power variable of its own) are calculated when results are loaded."""
import json
import os

from .template_graph import detectPumps, templateComponents

PUMP_FILE = 'networkPumps.json'
FEATURES = ('customer', 'energy_plant')
DEFAULT_ETA = 0.5
DEFAULT_DP_INT = 20000.0  # Pa
RHO_WATER = 1000.0  # kg/m3


def pumpFilePath(config):
    return os.path.join(config['pathProjects'] + config['projectName'], PUMP_FILE)


def templatePath(config, feature, t_name):
    return os.path.join(config['pathProjects'] + config['projectName'], feature + '_templates', t_name, t_name + '.idm')


def entryKey(entry):
    return (entry['feature'], entry['template'], entry['component'])


def newEntry(feature, template, component, kind='variable', variable='PPUMP', source='found',
             eta=DEFAULT_ETA, dp_int=DEFAULT_DP_INT, type=''):
    return {'feature': feature, 'template': template, 'component': component, 'type': type, 'kind': kind,
            'variable': variable if kind == 'variable' else '', 'eta': eta, 'dp_int': dp_int, 'source': source}


def loadPumpList(config):
    """{'entries': [...], 'removed': [[feature, template, component], ...]}, or None without the file."""
    path = pumpFilePath(config)
    if not os.path.exists(path):
        return None
    with open(path, encoding='utf-8') as f:
        data = json.load(f)
    data.setdefault('entries', [])
    data.setdefault('removed', [])
    for entry in data['entries']:
        entry.setdefault('eta', DEFAULT_ETA)
        entry.setdefault('dp_int', DEFAULT_DP_INT)
    return data


def savePumpList(config, data):
    clean = {'entries': [{k: v for k, v in e.items() if k != 'missing'} for e in data['entries']],
             'removed': [list(key) for key in data['removed']]}
    with open(pumpFilePath(config), 'w', encoding='utf-8') as f:
        json.dump(clean, f, indent=1)


def detectProject(config, templates):
    """Detection on the project's templates {feature: [t_name]}: ({key: entry}, [(feature, t_name, warning)])."""
    found, warnings = {}, []
    for feature, t_names in templates.items():
        for t_name in t_names:
            path = templatePath(config, feature, t_name)
            if not os.path.exists(path):
                warnings.append((feature, t_name, ('missing_template', path, '')))
                continue
            pumps, template_warnings = detectPumps(path)
            warnings += [(feature, t_name, w) for w in template_warnings]
            for pump in pumps:
                entry = newEntry(feature, t_name, pump['component'], variable=pump['variable'], type=pump['type'])
                found[entryKey(entry)] = entry
    return found, warnings


def mergeDetection(data, found):
    """Adds detected entries that are neither listed nor removed by the user; listed entries keep their settings."""
    data = data or {'entries': [], 'removed': []}
    listed = {entryKey(e) for e in data['entries']}
    removed = {tuple(key) for key in data['removed']}
    data['entries'] += [entry for key, entry in sorted(found.items()) if key not in listed and key not in removed]
    return data


def removeEntry(data, entry):
    data['entries'] = [e for e in data['entries'] if entryKey(e) != entryKey(entry)]
    if entry.get('source') == 'found' and list(entryKey(entry)) not in data['removed']:
        data['removed'].append(list(entryKey(entry)))
    return data


def markMissing(config, data):
    """Sets 'missing' on entries whose template or component no longer exists."""
    components = {}
    for entry in data['entries']:
        key = (entry['feature'], entry['template'])
        if key not in components:
            path = templatePath(config, *key)
            components[key] = set(templateComponents(path)) if os.path.exists(path) else set()
        entry['missing'] = entry['component'] not in components[key]
    return data


def templateEntries(data, feature, t_name, kind=None):
    """Entries of one template that are written or loaded (missing ones skipped)."""
    if not data:
        return []
    return [e for e in data['entries'] if e['feature'] == feature and e['template'] == t_name
            and not e.get('missing') and (kind is None or e['kind'] == kind)]


def ensurePumpList(config, templates):
    """The project's pump list; detected and saved if the project has none yet."""
    data = loadPumpList(config)
    if data is None:
        found, _ = detectProject(config, templates)
        data = mergeDetection(None, found)
        savePumpList(config, data)
    return markMissing(config, data)


def estimatePumpPower(mdot, p_in, p_out, dp_int=DEFAULT_DP_INT, eta=DEFAULT_ETA, rho=RHO_WATER):
    """Electric power [W] of a pump inside a component: P = mdot/rho * max(0, p_out - p_in + dp_int) / eta."""
    return abs(mdot) / rho * max(0.0, p_out - p_in + dp_int) / eta


def prnColumns(header_line):
    """{lower-case column name: index} of an IDA output file header ('#  time  order  name ...')."""
    names = header_line.split()
    if names and names[0] == '#':
        names = names[1:]
    return {name.lower(): col for col, name in enumerate(names)}


def variableSeries(columns, data, entries):
    """[(entry, values)] of the 'variable' entries found in a PumpPower file (column = component, lower case)."""
    return [(e, data[:, columns[e['component'].lower()]]) for e in entries
            if e['kind'] == 'variable' and e['component'].lower() in columns]


def estimateSeries(conn_files, entry):
    """Estimated power per time step from the connection files of a feature [(columns, data)] with mdot_<conn> and
    p_<conn>; all files of a simulation share the time column of the first one."""
    mdots, pressures = {}, {}
    for columns, data in conn_files:
        for name, col in columns.items():
            kind, _, conn = name.partition('_')
            if conn.isdigit() and kind in ('mdot', 'p'):
                (mdots if kind == 'mdot' else pressures)[conn] = data[:, col]
    if not mdots:
        return None
    n = len(next(iter(mdots.values())))
    return [estimateFromConnections({c: v[i] for c, v in mdots.items()}, {c: v[i] for c, v in pressures.items()},
                                    entry.get('dp_int', DEFAULT_DP_INT), entry.get('eta', DEFAULT_ETA)) for i in range(n)]


def estimateFromConnections(mdots, pressures, dp_int=DEFAULT_DP_INT, eta=DEFAULT_ETA):
    """Estimate for one time step from the connections of a feature ({conn: mdot}, {conn: p}).
    mdot > 0 flows out of the feature into the network: the inflow connection is p_in, the outflow connection p_out."""
    inflow = [c for c in mdots if mdots[c] < 0 and c in pressures]
    outflow = [c for c in mdots if mdots[c] > 0 and c in pressures]
    if not inflow or not outflow:
        return 0.0
    c_in = min(inflow, key=lambda c: mdots[c])
    c_out = max(outflow, key=lambda c: mdots[c])
    return estimatePumpPower(-mdots[c_in], pressures[c_in], pressures[c_out], dp_int, eta)
