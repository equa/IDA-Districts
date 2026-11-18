# coding=utf-8
"""Components of the plant and customer templates that buy energy, per project (OpenSpec change plant-energy-costs,
D1-D3): <project>\\energyUse.json with each component's variable and carrier. Written into the templates as the output
file "EnergyUse"; loaded into energy_plant_s_energy / customer_s_energy. The list functions of the network pump list
work on it as well (entries, removed keys)."""
import json
import os

from .network_pumps import FEATURES, entryKey, markMissing, mergeDetection, removeEntry, templateEntries, templatePath
from .template_graph import parseTemplate

ENERGY_FILE = 'energyUse.json'
OUTPUT_FILE = 'EnergyUse'
CARRIERS = ('electricity', 'fuel', 'purchased_heat', 'ambient', 'delivered')
# ambient: energy from the surroundings (borehole field, ambient air, solar thermal, free cooling), free unless the
# scenario has a price group 'ambient'; counted in the energy tables
CARRIER_LABELS = {'electricity': 'electricity', 'fuel': 'fuel', 'purchased_heat': 'purchased heat', 'ambient': 'ambient (free)',
                  'delivered': 'delivered heat/cold'}
FREE_CARRIERS = ('ambient',)
# delivered: heat (> 0) or cold (< 0) the network delivers to a customer, e.g. through the heat exchanger of a substation;
# not bought, never priced: its cost is in the energy of the plants and customers; the reference of the key figures
DELIVERED = 'delivered'
# component type -> (variable, carrier); QSUP of a boiler is its energy input (Q / BOILEFF); a BOIL1CIRC standing for
# waste heat is changed to purchased heat by the user
# (variable, carrier, features or None for all, absolute value); the heat exchanger of a customer (e.g. direct cooling of the
# low_temperature_network substation, |PhiHx| < 0 while cooling) delivers energy; a plant's heat exchanger (waste heat) is
# left out: its energy is counted through the plant's boiler
DETECTED_TYPES = {'BOIL1CIRC': ('QSUP', 'fuel', None, False), 'HP_B2B': ('|P_el_total|', 'electricity', None, False),
                  'HP_B2B_': ('|P_el_total|', 'electricity', None, False), '|hx|': ('|PhiHx|', DELIVERED, ('customer',), False)}

__all__ = ['CARRIERS', 'CARRIER_LABELS', 'DELIVERED', 'DETECTED_TYPES', 'FREE_CARRIERS', 'ENERGY_FILE', 'FEATURES', 'OUTPUT_FILE', 'detectEnergy', 'detectProject', 'ensureEnergyList',
           'entryKey', 'loadEnergyList', 'markMissing', 'mergeDetection', 'newEntry', 'outputAlias', 'outputColumns', 'outputVariables', 'pumpConflicts', 'removeEntry',
           'saveEnergyList', 'templateEntries', 'templatePath']


def energyFilePath(config):
    return os.path.join(config['pathProjects'] + config['projectName'], ENERGY_FILE)


def newEntry(feature, template, component, variable, carrier, type='', name='', source='found', absolute=False):
    """absolute: the variable is signed by the flow direction (a heat exchanger); its amount is the energy"""
    return {'feature': feature, 'template': template, 'component': component, 'type': type, 'variable': variable,
            'carrier': carrier if carrier in CARRIERS else CARRIERS[0], 'name': name, 'source': source, 'absolute': absolute}


def loadEnergyList(config):
    """{'entries': [...], 'removed': [[feature, template, component], ...]}, or None without the file."""
    path = energyFilePath(config)
    if not os.path.exists(path):
        return None
    with open(path, encoding='utf-8') as f:
        data = json.load(f)
    data.setdefault('entries', [])
    data.setdefault('removed', [])
    for entry in data['entries']:
        entry.setdefault('name', '')
        if entry.get('carrier') not in CARRIERS:
            entry['carrier'] = CARRIERS[0]
    return data


def saveEnergyList(config, data):
    clean = {'entries': [{k: v for k, v in e.items() if k != 'missing'} for e in data['entries']],
             'removed': [list(key) for key in data['removed']]}
    with open(energyFilePath(config), 'w', encoding='utf-8') as f:
        json.dump(clean, f, indent=1)


def detectEnergy(path, feature=None):
    """[{'component', 'type', 'variable', 'carrier', 'absolute'}] of the template file `path` of the feature type, and
    [warnings] for the detected component types in its macros (other .idm files of the folder), which are not analysed."""
    with open(path, encoding='utf-8-sig', errors='replace') as f:
        types, variables, _ = parseTemplate(f.read())
    found = []
    for comp, typ in sorted(types.items()):
        if typ not in DETECTED_TYPES:
            continue
        variable, carrier, features, absolute = DETECTED_TYPES[typ]
        if features and feature not in features:
            continue
        # the name as written in the template (with or without bars)
        listed = [v for v in variables.get(comp, []) if v.strip('|').lower() == variable.strip('|').lower()]
        found.append({'component': comp, 'type': typ, 'variable': listed[0] if listed else variable, 'carrier': carrier, 'absolute': absolute})
    warnings = []
    folder = os.path.dirname(path)
    for name in sorted(os.listdir(folder)):
        other = os.path.join(folder, name)
        if name.lower().endswith('.idm') and os.path.normcase(other) != os.path.normcase(path):
            try:
                with open(other, encoding='utf-8-sig', errors='replace') as f:
                    macro_types, _, _ = parseTemplate(f.read())
            except OSError as e:
                warnings.append(('unreadable', name, str(e)))
                continue
            warnings += [('macro_energy', name, comp) for comp, typ in sorted(macro_types.items())
                         if typ in DETECTED_TYPES and (not DETECTED_TYPES[typ][2] or feature in (DETECTED_TYPES[typ][2] or ()))]
    return found, warnings


def detectProject(config, templates):
    """Detection on the project's templates {feature: [t_name]}: ({key: entry}, [(feature, t_name, warning)])."""
    found, warnings = {}, []
    for feature, t_names in templates.items():
        for t_name in t_names:
            path = templatePath(config, feature, t_name)
            if not os.path.exists(path):
                warnings.append((feature, t_name, ('missing_template', path, '')))
                continue
            components, template_warnings = detectEnergy(path, feature)
            warnings += [(feature, t_name, w) for w in template_warnings]
            for c in components:
                entry = newEntry(feature, t_name, c['component'], c['variable'], c['carrier'], type=c['type'], absolute=c['absolute'])
                found[entryKey(entry)] = entry
    return found, warnings


def ensureEnergyList(config, templates):
    """The project's energy-use list; detected and saved if the project has none yet."""
    data = loadEnergyList(config)
    if data is None:
        found, _ = detectProject(config, templates)
        data = mergeDetection(None, found)
        saveEnergyList(config, data)
    return markMissing(config, data)


def pumpConflicts(data, pump_data):
    """keys of the entries whose component is also a network pump entry (its power would be counted twice)"""
    pumps = {entryKey(e) for e in (pump_data or {}).get('entries', [])}
    return {entryKey(e) for e in (data or {}).get('entries', []) if entryKey(e) in pumps}


def outputAlias(k):
    """column name of the k-th entry of a template in the output file: IDA cuts column names to 10 characters, so a
    component name (e.g. hx_substation) cannot name its column"""
    return 'E{}'.format(k)


def outputColumns(data, feature, t_name):
    """[(entry, column name)] of a template's entries, in the order the outputs are written"""
    return [(e, outputAlias(k)) for k, e in enumerate(templateEntries(data, feature, t_name), 1)]


def outputVariables(data, feature, t_name):
    """{'"<component>"': (variable, '"<column>"')} of a template's entries, for the output file EnergyUse"""
    return {'"{}"'.format(e['component']): (e['variable'], '"{}"'.format(alias)) for e, alias in outputColumns(data, feature, t_name)}
