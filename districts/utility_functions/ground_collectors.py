#ground collector resources and routes (change ground-collector-routes, design R1-R3): the table
#public.ground_collectors, its line types, the collector lines of a version with the resource's defaults, the fit
#and start values cached in the resource, helpers of the model build; no Qt
import json
from typing import Callable, Optional
import os
import re

#the resource's columns besides id, name and fits; (column, SQL type and default)
COLUMNS = (
    ('description', 'text'),
    ('preset', "text NOT NULL DEFAULT 'horizontal_ring' CHECK (preset IN ('horizontal_ring','vertical_ring','flat_meander','bare_pipe'))"),
    ('preset_inputs', "jsonb NOT NULL DEFAULT '{}'"),  # arguments of the preset function besides the pipe
    ('pipe_id', 'integer'),                             # loop pipe (public.pipes; no foreign key: pipes are saved by TRUNCATE)
    ('loop_sequence', 'integer NOT NULL DEFAULT 1'),     # pipe of the line's bundle whose terminals the loop takes
    ('liquid_id', 'integer NOT NULL DEFAULT 1'),         # liquid of the loop (public.liquids), as liqType of the model
    ('t_freeze_liquid_c', 'numeric NOT NULL DEFAULT 0'), # freezing point of that liquid, TFreeze of the model
    ('lambda_w7mk', 'numeric NOT NULL DEFAULT 1.5'),
    ('rho_c_j7m3k', 'numeric NOT NULL DEFAULT 2200000'),
    ('water_content', 'numeric NOT NULL DEFAULT 0.25'),
    ('t_freeze_c', 'numeric NOT NULL DEFAULT 0'),       # soil water: not in the dialog, 0 degC and 1 K
    ('freeze_range_k', 'numeric NOT NULL DEFAULT 1'),
    ('lambda_frozen_ratio', 'numeric NOT NULL DEFAULT 1'),
    ('albedo', 'numeric NOT NULL DEFAULT 0.25'),
    ('epsilon', 'numeric NOT NULL DEFAULT 0.95'),
    ('h_conv_w7m2k', 'numeric NOT NULL DEFAULT 10'),
    ('d_layer_m', 'numeric NOT NULL DEFAULT 0.05'),
    ('rho_c_layer_j7m3k', 'numeric NOT NULL DEFAULT 2200000'),
    ('t_mean_init', 'numeric NOT NULL DEFAULT 5'),
    ('start_mode', "text NOT NULL DEFAULT 'undisturbed' CHECK (start_mode IN ('undisturbed','precalculated'))"),
    ('start_years', 'integer NOT NULL DEFAULT 5'),
    ('n_sections', 'integer NOT NULL DEFAULT 3'),
    ('cost_trench_eur7m', 'numeric NOT NULL DEFAULT 0'),
    ('cost_loop_eur7m', 'numeric NOT NULL DEFAULT 0'),
    ('maintenance_pct', 'numeric NOT NULL DEFAULT 1'),
    ('lifetime_a', 'numeric NOT NULL DEFAULT 50'),
)
EDITABLE = tuple(c for c, _ in COLUMNS)
NULLABLE = {'description', 'pipe_id'}

TABLES_SQL = """CREATE TABLE IF NOT EXISTS public.ground_collectors
(
  id serial,
  name text NOT NULL UNIQUE,
{columns},
  fits jsonb NOT NULL DEFAULT '{{}}', --RC fits and start states keyed by fingerprint (cache)
  CONSTRAINT ground_collectors_pkey PRIMARY KEY (id)
);
ALTER TABLE public.line_types ADD COLUMN IF NOT EXISTS ground_collector_id integer
  REFERENCES public.ground_collectors(id) ON DELETE RESTRICT;
""".format(columns=',\n'.join('  {} {}'.format(c, t) for c, t in COLUMNS))

#columns of the version table lines (design R3): loops per line (default 1); empty t_mean_init = the resource's
LINE_COLUMNS = {'n_loops': 'integer DEFAULT 1', 't_mean_init': 'numeric'}


#inputs of the preset functions (ground_collector_geometry.PRESETS) besides the pipe, with the values a new resource gets
PRESET_DEFAULTS = {
    'horizontal_ring': {'ring_diameter_m': 1.0, 'pitch_m': 0.3, 'depth_m': 1.5, 'spacing_m': 3.0},
    'vertical_ring': {'ring_diameter_m': 1.0, 'pitch_m': 0.3, 'depth_m': 1.8, 'spacing_m': 3.0},
    'flat_meander': {'layer_width_m': 1.0, 'pipe_spacing_m': 0.5, 'depth_m': 1.5, 'spacing_m': 3.0},
    'bare_pipe': {'depth_m': 1.5, 'spacing_m': 3.0},
}


def ensureGroundCollectorTables(cur):
    """Creates public.ground_collectors and line_types.ground_collector_id in projects created before, and the
    columns a table of an earlier build lacks."""
    cur.execute(TABLES_SQL)
    for column, sql_type in COLUMNS:
        cur.execute('ALTER TABLE public.ground_collectors ADD COLUMN IF NOT EXISTS {} {};'.format(column, sql_type))  # nosec B608


def liquidNames(cur):
    """{id: name} of public.liquids (the liqType names of IDA Districts)."""
    cur.execute('SELECT id, liquid FROM public.liquids ORDER BY id;')
    return {r['id']: r['liquid'] for r in cur.fetchall()}


def ensureLineColumns(cur, version):
    """lines.n_loops and lines.t_mean_init in versions created before (appended, as in new versions)."""
    for column, sql_type in LINE_COLUMNS.items():
        cur.execute('ALTER TABLE "{}".lines ADD COLUMN IF NOT EXISTS {} {};'.format(version, column, sql_type))  # nosec B608
    # a version of a development build has the column without its default
    cur.execute('ALTER TABLE "{}".lines ALTER COLUMN n_loops SET DEFAULT 1;'.format(version))  # nosec B608


def readCollectors(cur):
    """{id: row} of the resources (jsonb as dicts)."""
    cur.execute('SELECT * FROM public.ground_collectors ORDER BY id;')
    return {row['id']: dict(row) for row in cur.fetchall()}


class CollectorInUse(ValueError):
    """A resource whose line type is used by lines cannot be deleted."""

    def __init__(self, name, line_ids):
        super().__init__(name, line_ids)
        self.name = name
        self.line_ids = line_ids


def usedBy(cur, collector_id, versions):
    """{version: [line ids]} of the lines whose type is the resource's line type."""
    cur.execute('SELECT id FROM public.line_types WHERE ground_collector_id = %s;', (collector_id,))
    types = [r['id'] for r in cur.fetchall()]
    used = {}
    for version in versions if types else ():
        cur.execute('SELECT id FROM "{}".lines WHERE type = ANY(%s) ORDER BY id;'.format(version), (types,))  # nosec B608
        ids = [r['id'] for r in cur.fetchall()]
        if ids:
            used[version] = ids
    return used


def saveCollector(cur, row):
    """Inserts (no id) or updates a resource and creates or renames its line type; returns the resource id."""
    # an empty value of a NOT NULL column keeps the default (insert) or the stored value (update)
    columns = [c for c in EDITABLE if row.get(c) is not None or c in NULLABLE]
    values = [json.dumps(row[c]) if c == 'preset_inputs' and not isinstance(row.get(c), str) else row.get(c)
              for c in columns]
    if row.get('id') is None:
        cur.execute('INSERT INTO public.ground_collectors (name{}) VALUES (%s{}) RETURNING id;'.format(  # nosec B608
            ''.join(', ' + c for c in columns), ', %s' * len(columns)), [row['name']] + values)
        collector_id = cur.fetchone()['id']
    else:
        collector_id = row['id']
        # the fits stay: an entry of other inputs no longer matches the fingerprint and is dropped on the next store
        cur.execute('UPDATE public.ground_collectors SET name = %s{} WHERE id = %s;'.format(  # nosec B608
            ''.join(', {} = %s'.format(c) for c in columns)), [row['name']] + values + [collector_id])
    syncLineType(cur, collector_id, row['name'], row.get('description'))
    return collector_id


def syncLineType(cur, collector_id, name, description=None):
    """The line type of a resource: created with the next free id, or renamed (its id stays, lines keep it)."""
    cur.execute('SELECT id FROM public.line_types WHERE ground_collector_id = %s;', (collector_id,))
    row = cur.fetchone()
    if row:
        cur.execute('UPDATE public.line_types SET type = %s, description = %s WHERE id = %s;', (name, description, row['id']))
        return row['id']
    cur.execute('SELECT COALESCE(MAX(id), 0) + 1 AS id FROM public.line_types;')
    type_id = cur.fetchone()['id']
    cur.execute('INSERT INTO public.line_types (id, type, description, ground_collector_id) VALUES (%s, %s, %s, %s);',
                (type_id, name, description, collector_id))
    cur.execute("SELECT setval(pg_get_serial_sequence('public.line_types', 'id'), (SELECT MAX(id) FROM public.line_types));")
    return type_id


def deleteCollector(cur, collector_id, versions):
    """Deletes a resource and its line type; raises CollectorInUse naming the lines that use it."""
    used = usedBy(cur, collector_id, versions)
    if used:
        cur.execute('SELECT name FROM public.ground_collectors WHERE id = %s;', (collector_id,))
        raise CollectorInUse(cur.fetchone()['name'], used)
    cur.execute('DELETE FROM public.line_types WHERE ground_collector_id = %s;', (collector_id,))
    cur.execute('DELETE FROM public.ground_collectors WHERE id = %s;', (collector_id,))


def _plain(value):
    """A value the resource export can write with str() and read back with literal_eval (no Decimal)."""
    from decimal import Decimal
    if isinstance(value, Decimal):
        return float(value)
    if isinstance(value, dict):
        return {k: _plain(v) for k, v in value.items()}
    if isinstance(value, list):
        return [_plain(v) for v in value]
    return value


def exportCollectors(cur, names=None):
    """{name: resource} for the resource export (design R11): the columns, the loop pipe by its name and the fits."""
    liquids = liquidNames(cur)
    cur.execute('SELECT g.*, p.name AS pipe_name FROM public.ground_collectors g LEFT JOIN public.pipes p ON p.id = g.pipe_id ORDER BY g.id;')
    out = {}
    for row in cur.fetchall():
        if names is not None and row['name'] not in names:
            continue
        data = {c: _plain(row[c]) for c in EDITABLE if c not in ('pipe_id', 'liquid_id')}
        data['liquid_name'] = liquids.get(row['liquid_id'])
        data['preset_inputs'] = _plain(json.loads(row['preset_inputs']) if isinstance(row['preset_inputs'], str) else dict(row['preset_inputs'] or {}))
        data['pipe_name'] = row['pipe_name']
        data['fits'] = _plain(_fits(row))
        out[row['name']] = data
    return out


def importCollectors(cur, collectors):
    """Adds or replaces the exported resources by name, their line types with them; the loop pipe by its name.
    Returns the names whose loop pipe the project does not have (pipe left empty)."""
    ensureGroundCollectorTables(cur)
    cur.execute('SELECT id, name FROM public.ground_collectors;')
    existing = {r['name']: r['id'] for r in cur.fetchall()}
    liquid_ids = {name: lid for lid, name in liquidNames(cur).items()}
    no_pipe = []
    for name, data in (collectors or {}).items():
        pipe_id = None
        if data.get('pipe_name'):
            cur.execute('SELECT id FROM public.pipes WHERE name = %s ORDER BY id LIMIT 1;', (data['pipe_name'],))
            row = cur.fetchone()
            pipe_id = row['id'] if row else None
        if pipe_id is None:
            no_pipe.append(name)
        row = {c: data.get(c) for c in EDITABLE}
        # an unknown liquid keeps the default (water)
        row.update(id=existing.get(name), name=name, pipe_id=pipe_id, liquid_id=liquid_ids.get(data.get('liquid_name')))
        collector_id = saveCollector(cur, row)
        cur.execute('UPDATE public.ground_collectors SET fits = %s WHERE id = %s;', (json.dumps(data.get('fits') or {}), collector_id))
    return no_pipe


def collectorLines(cur, version):
    """{line id: {collector_id, n_loops, t_mean_init, length, loop_sequence, n_sections}} of the collector lines of a
    version: an empty n_loops is 1, an empty t_mean_init the resource's (design R3)."""
    cur.execute("""SELECT l.id, t.ground_collector_id, COALESCE(l.n_loops, 1) AS n_loops,
        COALESCE(l.t_mean_init, g.t_mean_init) AS t_mean_init, ST_Length(l.geom) AS length, g.loop_sequence, g.n_sections
        FROM "{}".lines l JOIN public.line_types t ON t.id = l.type
        JOIN public.ground_collectors g ON g.id = t.ground_collector_id ORDER BY l.id;""".format(version))  # nosec B608
    return {r['id']: {'collector_id': r['ground_collector_id'], 'n_loops': int(r['n_loops']),
                      't_mean_init': float(r['t_mean_init']), 'length': float(r['length']),
                      'loop_sequence': r['loop_sequence'], 'n_sections': int(r['n_sections'])} for r in cur.fetchall()}


#Line_coll_<lid>.prn: the logged names (lower case, as IDA writes the header) -> result variable (table line_s_<var>,
#column "$<var>" as show_on_map expects); per section or not
COLLECTOR_RESULTS = (('tin', 'coll_tin', False), ('tout', 'coll_tout', False), ('qextracted', 'coll_qextracted', False),
                     ('qsurface', 'coll_qsurface', False), ('tloc', 'coll_tloc', True), ('tnear', 'coll_tnear', True),
                     ('ice', 'coll_ice', True))


#a start state from a mean liquid temperature this far from the simulated one is stale (design R7)
T_MEAN_TOLERANCE_K = 2.0


def resultMeanTemperatures(cur, version):
    """{line id: mean liquid temperature (TIn + TOut)/2 over the loaded results} of the collector lines."""
    cur.execute("""SELECT to_regclass(%s) IS NOT NULL AND to_regclass(%s) IS NOT NULL AS ok;""",
                ('"{}".line_s_coll_tin'.format(version), '"{}".line_s_coll_tout'.format(version)))
    if not cur.fetchone()['ok']:
        return {}
    cur.execute("""SELECT i.fid, avg((i."$coll_tin" + o."$coll_tout") / 2) AS t FROM "{v}".line_s_coll_tin i
        JOIN "{v}".line_s_coll_tout o ON o.fid = i.fid AND o.time = i.time GROUP BY i.fid;""".format(v=version))  # nosec B608
    return {r['fid']: float(r['t']) for r in cur.fetchall() if r['t'] is not None}


def setMeanFromResults(cur, version, line_ids):
    """lines.t_mean_init of the given collector lines from their results; {line id: value} of the lines set."""
    means = resultMeanTemperatures(cur, version)
    lines = collectorLines(cur, version)
    values = {lid: round(means[lid], 2) for lid in line_ids if lid in means and lid in lines}
    for lid, value in values.items():
        cur.execute('UPDATE "{}".lines SET t_mean_init = %s WHERE id = %s;'.format(version), (value, lid))  # nosec B608
    return values


def collectorResultColumns(header, n_sections):
    """{var: [data column per segment]} of a Line_coll file from its header line ('#', time, order, names...); the data
    columns count from 0 = time. A variable missing in the file is left out."""
    names = header.lstrip('#').split()
    index = {name.lower(): k for k, name in enumerate(names)}
    out = {}
    for name, var, per_section in COLLECTOR_RESULTS:
        keys = ['{}_{}'.format(name, j) for j in range(1, n_sections + 1)] if per_section else [name]
        if all(k in index for k in keys):
            out[var] = [index[k] for k in keys]
    return out


def collectorsWithoutBundle(cur, version):
    """Collector lines whose bundle has only the loop pipe: the model has no Pipebundle_<lid> for them."""
    cur.execute("""SELECT l.id FROM "{}".lines l JOIN public.line_types t ON t.id = l.type AND t.ground_collector_id IS NOT NULL
        WHERE (SELECT count(*) FROM public.bundle_pipes bp WHERE bp.pipe_bundle_type_id = l.pipe_bundle_type_id) <= 1;""".format(version))  # nosec B608
    return {r['id'] for r in cur.fetchall()}


def notCollector(alias='l'):
    """SQL condition: the line <alias> is no collector (sizing and the cost optimization leave collectors, R8)."""
    return ('NOT EXISTS (SELECT 1 FROM public.line_types gc_t WHERE gc_t.id = {}.type '
            'AND gc_t.ground_collector_id IS NOT NULL)'.format(alias))


#the loop length per trench meter depends on the geometry only; any undisturbed wave gives it
_WAVE = {'kusuda_tsurfmean': 10.0, 'kusuda_tsurfampl': 10.0, 'kusuda_theta': 0.0}


def collectorCosts(cur, version):
    """{line id: cost data} of the collector lines of a version: resource name, loops, loop sequence, loop length per
    trench meter and the resource's costs, maintenance and lifetime (design R9)."""
    lines = collectorLines(cur, version)
    if not lines:
        return {}
    resources = readCollectors(cur)
    per_m = {}
    out = {}
    for lid, line in lines.items():
        resource = resources[line['collector_id']]
        if resource['id'] not in per_m:
            try:
                per_m[resource['id']] = collectorModel(resource, loopPipe(cur, resource['pipe_id']), _WAVE)[0].loop_length_per_m
            except (ValueError, KeyError, TypeError):
                per_m[resource['id']] = 0.0  # the model checks report the missing loop pipe
        out[lid] = {'name': resource['name'], 'n_loops': line['n_loops'], 'loop_sequence': resource['loop_sequence'],
                    'loop_length_per_m': per_m[resource['id']], 'cost_trench_eur7m': float(resource['cost_trench_eur7m']),
                    'cost_loop_eur7m': float(resource['cost_loop_eur7m']), 'maintenance_pct': float(resource['maintenance_pct']),
                    'lifetime_a': float(resource['lifetime_a'])}
    return out


def collectorItem(info, length):
    """Investment item of a collector line: every loop in its own trench (trench meters = length x loops), the loop
    meters from the geometry."""
    trench_m = length * info['n_loops']
    loop_m = trench_m * info['loop_length_per_m']
    return {'cost': trench_m * info['cost_trench_eur7m'] + loop_m * info['cost_loop_eur7m'], 'lifetime': info['lifetime_a'],
            'maintenance_pct': info['maintenance_pct'], 'name': info['name'], 'length': trench_m, 'loop_m': loop_m}


def collectorTypeIds(cur):
    """ids of the line types that are collectors (a line is a collector exactly when its type is one of them)."""
    cur.execute('SELECT id FROM public.line_types WHERE ground_collector_id IS NOT NULL;')
    return {r['id'] for r in cur.fetchall()}


def isCollectorLine(cur, version, line_id):
    cur.execute('SELECT type FROM "{}".lines WHERE id = %s;'.format(version), (line_id,))  # nosec B608
    row = cur.fetchone()
    return bool(row) and row['type'] in collectorTypeIds(cur)


# ---------------------------------------------------------------- loop pipe, fit, start values (design R6, R7)
def loopPipe(cur, pipe_id):
    """{d_inner, d_outer, lambda_wall, roughness} of the loop pipe: inner diameter and roughness of the pipe, wall of
    its first construction layer (as the model build reads the FDpipebundle's pipe)."""
    cur.execute("""SELECT p.innerpipediameter, p.piperoughnessfactor, pl.thickness, m.thermal_conductivity_w7mkelvin
        FROM public.pipes p JOIN public.pipe_layers pl ON pl.pipe_construction_id = p.pipe_construction_id
        JOIN public.materials m ON m.id = pl.materialid WHERE p.id = %s ORDER BY pl.sequence LIMIT 1;""", (pipe_id,))
    row = cur.fetchone()
    if not row:
        raise ValueError('loop pipe {} not found or without construction layers'.format(pipe_id))
    d_inner = float(row['innerpipediameter'])
    return {'d_inner': d_inner, 'd_outer': d_inner + 2 * float(row['thickness']),
            'lambda_wall': float(row['thermal_conductivity_w7mkelvin']), 'roughness': float(row['piperoughnessfactor'] or 0)}


def collectorModel(resource, pipe, settings):
    """CollectorGeometry, SoilProperties and SurfaceProperties of a resource: soil at the collector, the undisturbed
    annual wave from the project's Kusuda settings (decision T17)."""
    from . import ground_collector_geometry as gg
    soil = gg.SoilProperties(
        lambda_w7mk=float(resource['lambda_w7mk']), rho_c_j7m3k=float(resource['rho_c_j7m3k']),
        water_content=float(resource['water_content']), t_freeze_c=float(resource['t_freeze_c']),
        freeze_range_k=float(resource['freeze_range_k']), lambda_frozen_ratio=float(resource['lambda_frozen_ratio']),
        t_mean_surface_c=float(settings['kusuda_tsurfmean']), amplitude_surface_k=float(settings['kusuda_tsurfampl']),
        phase_day=float(settings['kusuda_theta']))
    surface = gg.SurfaceProperties(
        albedo=float(resource['albedo']), epsilon=float(resource['epsilon']), h_conv_w7m2k=float(resource['h_conv_w7m2k']),
        d_layer_m=float(resource['d_layer_m']), rho_c_j7m3k=float(resource['rho_c_layer_j7m3k']))
    inputs = resource['preset_inputs']
    inputs = json.loads(inputs) if isinstance(inputs, str) else dict(inputs or {})
    preset = gg.PRESETS[resource['preset']]
    geometry = preset(**{k: float(v) for k, v in inputs.items()}, pipe_d_inner_m=pipe['d_inner'],
                          pipe_d_outer_m=pipe['d_outer'], pipe_lambda_w7mk=pipe['lambda_wall'], soil=soil)
    return geometry, soil, surface


def _fits(resource):
    fits = resource.get('fits') or {}
    return json.loads(fits) if isinstance(fits, str) else dict(fits)


def fitKey(cur, resource, settings):
    """(fingerprint, geometry, soil, surface) of a resource for the project's settings."""
    import dataclasses
    from . import ground_rc as rc
    pipe = loopPipe(cur, resource['pipe_id'])
    geometry, soil, surface = collectorModel(resource, pipe, settings)
    #the fit is linear: unfrozen soil, the freezing comes with the parameters (as the validation cases)
    dry = dataclasses.replace(soil, water_content=0.0)
    return rc.fingerprint(geometry, dry, surface, rc.FitSettings()), geometry, soil, surface


def cachedFit(cur, resource, settings):
    """The cached fit entry of a resource for the settings, None when the next build has to fit it."""
    key = fitKey(cur, resource, settings)[0]
    return _fits(resource).get(key)


def fitFor(cur, resource, settings, progress: Optional[Callable[[str], None]] = None):
    """The fit of a resource for the project's settings: the cached entry of its fingerprint, otherwise fitRc (1-20 s),
    stored in the resource; entries of another FIT_VERSION are dropped. Returns (fit entry, geometry, soil, surface)
    with the entry {values, t_deep, errors, steady_error, accepted, fit_version, starts}."""
    import dataclasses
    from . import ground_rc as rc
    key, geometry, soil, surface = fitKey(cur, resource, settings)
    fits = _fits(resource)
    if key not in fits:
        if progress:
            progress(resource['name'])
        fit = rc.fitRc(geometry, dataclasses.replace(soil, water_content=0.0), surface)
        fits = {k: v for k, v in fits.items() if v.get('fit_version') == rc.FIT_VERSION}
        fits[key] = {'values': fit.values, 't_deep': fit.t_deep, 'errors': fit.errors,
                     'steady_error': fit.steady_error, 'accepted': fit.accepted, 'fit_version': rc.FIT_VERSION,
                     'starts': {}}
        storeFits(cur, resource, fits)
    entry = fits[key]
    entry['fingerprint'] = key
    return entry, geometry, soil, surface


def storeFits(cur, resource, fits):
    cur.execute('UPDATE public.ground_collectors SET fits = %s WHERE id = %s;', (json.dumps(fits), resource['id']))
    resource['fits'] = fits


def groundParameters(entry, geometry, soil, surface):
    """The contract's ground and surface parameters from a fit entry (ground_rc.groundParameters)."""
    from . import ground_rc as rc
    fit = rc.RcFit(entry['values'], entry['t_deep'], entry['errors'], entry['steady_error'], entry['accepted'],
                   entry.get('fingerprint', ''))
    return rc.groundParameters(fit, soil, surface, geometry)


def startValues(cur, resource, entry, geometry, soil, params, t_mean, climate_file, site, start_day):
    """Start values (TStart* and TStartSurface) of a collector: the undisturbed profile, or the pre-calculated state
    after the resource's years of the climate year with the wall at t_mean (design R7), cached in the fit entry."""
    from . import ground_rc as rc
    if resource['start_mode'] != 'precalculated':
        return rc.startState(params, geometry, soil, undisturbed=True, start_day=start_day)
    stamp = os.path.getmtime(climate_file) if os.path.exists(climate_file) else 0
    key = '{:.3f}|{}|{:.3f}|{}|{:.0f}'.format(float(t_mean), int(resource['start_years']), float(start_day),
                                              os.path.normcase(climate_file), stamp)
    starts = entry.setdefault('starts', {})
    if key not in starts:
        from .ground_climate import weatherFromFile
        year = weatherFromFile(climate_file, site, albedo=float(resource['albedo']), hours=8760)
        starts[key] = rc.startState(params, geometry, soil, year, float(t_mean), years=int(resource['start_years']),
                                    start_day=start_day)
        fits = _fits(resource)
        fits[entry['fingerprint']] = {k: v for k, v in entry.items() if k != 'fingerprint'}
        storeFits(cur, resource, fits)
    return starts[key]


# ---------------------------------------------------------------- model build helpers (design R4, R5)
def lineTerminals(lid, sequences, loop_sequence):
    """{pipe sequence: (model name, index or None)} of a line: the loop sequence goes to the collector's liq1/liq2
    (scalar connectors), the others to the remaining FDpipebundle, renumbered without the loop pipe."""
    terminals: dict = {}
    k = 0
    for seq in sorted(sequences):
        if seq == loop_sequence:
            terminals[seq] = ('Collector_{}'.format(lid), None)
        else:
            k += 1
            terminals[seq] = ('Pipebundle_{}'.format(lid), k)
    return terminals


def groundMoContractVersion(path_districts):
    """contractVersion of GroundCollector in the installed GroundMo library, None if not installed or not marked."""
    eo = os.path.join(path_districts, 'lib', 'Components', 'GroundMo', 'GroundMo.eo')
    if not os.path.exists(eo):
        return None
    with open(eo, encoding='utf-8', errors='replace') as f:
        match = re.search(r':n \|contractVersion\|[^)]*?:v (\d+)', f.read())
    return int(match.group(1)) if match else None
