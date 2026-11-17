# coding=utf-8
"""Cost data of the network: pipe cost columns, economic scenarios and their example values
(OpenSpec change network-cost-data).

Example values (research of 2026-11-16, all labelled `example`):
- KWW-Technikkatalog Wärmeplanung 08/2026, Tab 36 (KMR steel bonded pipe, single pipes, 2026 €, per trench metre and
  pipe pair): material ≈ 23 + 3.05·DN, civil works (minimum) unpaved ≈ 120 + 5.5·DN, paved ≈ 155 + 9.4·DN;
  DN175 and DN225 interpolated. https://www.kww-halle.de/angebote/infothek/detail/kww-technikkatalog-waermeplanung-begleitdokument
- Service life of pipes 40 a (VDI 2067-1), pumps 15 a; maintenance about 1 %/a pipes, 2.5 %/a pumps (unconfirmed).
- EN 13941: up to PN25, 120 °C; the common series is PN16.
- Pump 100 €/kW: a modelling assumption (arXiv 2205.12019, Table 1).
- Large air-source heat pump: SPF 2.5 at 70 °C, 1.8 at 95 °C (KWW Tab 24/25) -> heat price = electricity / SPF.
"""
from .db import addMissingColumns

EXAMPLE_SOURCE = 'example values: KWW-Technikkatalog Wärmeplanung 08/2026 Tab 36, VDI 2067-1, EN 13941'

PIPE_COST_COLUMNS = {'maintenance_pct': 'numeric', 'lifetime_a': 'numeric', 'p_max_bar': 'numeric', 'example': 'boolean DEFAULT false'}

# KWW 2026 Tab 36: material per trench metre and pipe pair [€/m]
KWW_MATERIAL_PAIR = {20: 71, 25: 87, 32: 111, 40: 137, 50: 169, 65: 217, 80: 265, 100: 328, 125: 406, 150: 483,
                     175: 560, 200: 636, 225: 712, 250: 787, 300: 937, 350: 1086}
EXAMPLE_PIPE = {'maintenance_pct': 1.0, 'lifetime_a': 40, 'p_max_bar': 16}

# columns of public.pipe_bundle_types removed by the upgrade (and skipped when resources of older projects are imported)
BUNDLE_COST_COLUMNS = ('invest_costs', 'operation_costs')

COST_GROUPS = ('electricity', 'heat', 'cold', 'maintenance', 'investment')
SURFACES = ('paved', 'unpaved')

ECONOMIC_TABLES_SQL = """
CREATE TABLE IF NOT EXISTS public.economic_scenarios
(
  id serial,
  name text,
  interest_pct numeric, --discount rate, %/a
  period_a integer, --amortization period, years
  residual_value boolean DEFAULT true, --linear residual value of the items at the end of the period
  default_surface text, --surface of trench parts not on a street
  el_profile_file text, --hourly electricity price profile in <project>\\prices (normalized to mean 1); empty = flat
  pump_costs_eur7kw numeric, --pump investment per kW of peak electric pump power
  pump_maintenance_pct numeric, --%/a of the pump investment
  pump_lifetime_a numeric,
  example boolean DEFAULT false,
  description text,
  CONSTRAINT economic_scenarios_pkey PRIMARY KEY (id)
);
CREATE TABLE IF NOT EXISTS public.price_groups
(
  id serial,
  scenario_id integer,
  cost_group text, --electricity, heat, cold, maintenance, investment
  start_price numeric, --electricity €/kWh in year 0; heat and cold: price curves; maintenance and investment: escalation only
  escalation_pct numeric, --%/a, level(t) = (1 + escalation)^t unless price_levels has year t
  description text,
  CONSTRAINT price_groups_pkey PRIMARY KEY (id)
);
CREATE TABLE IF NOT EXISTS public.price_levels
(
  id serial,
  scenario_id integer,
  cost_group text,
  year integer,
  factor numeric, --level of the year relative to year 0
  CONSTRAINT price_levels_pkey PRIMARY KEY (id)
);
CREATE TABLE IF NOT EXISTS public.price_curves
(
  id serial,
  scenario_id integer,
  mode text, --heat, cold
  t_supply numeric, --supply temperature of the plant, °C
  price_eur7kwh numeric, --price of year 0; linear between the rows, constant outside
  CONSTRAINT price_curves_pkey PRIMARY KEY (id)
);
CREATE TABLE IF NOT EXISTS public.trench_costs
(
  id serial,
  scenario_id integer,
  surface text,
  a_eur7m numeric, --civil works per trench metre: a + b * DN of the largest pipe of the bundle
  b_eur7m_dn numeric,
  description text,
  CONSTRAINT trench_costs_pkey PRIMARY KEY (id)
);
"""

BASE_SCENARIO = {'name': 'base', 'interest_pct': 3.0, 'period_a': 40, 'residual_value': True, 'default_surface': 'paved',
                 'el_profile_file': '', 'pump_costs_eur7kw': 100, 'pump_maintenance_pct': 2.5, 'pump_lifetime_a': 15,
                 'example': True, 'description': EXAMPLE_SOURCE}
BASE_PRICE_GROUPS = [('electricity', 0.25, 2.0, 'example: 0.25 €/kWh, +2 %/a'), ('heat', None, 2.0, 'price curve heat'),
                     ('cold', None, 2.0, 'price curve cold'), ('maintenance', None, 2.0, 'escalation of maintenance'),
                     ('investment', None, 2.0, 'escalation of replacements')]
# electricity 0.25 €/kWh / SPF of a large air-source heat pump (KWW 2026); cold: chiller EER 4
BASE_PRICE_CURVES = [('heat', 70, 0.10), ('heat', 95, 0.139), ('cold', 6, 0.0625)]
BASE_TRENCH_COSTS = [('paved', 155, 9.4, 'KWW 2026 Tab 36, civil works minimum, paved'),
                     ('unpaved', 120, 5.5, 'KWW 2026 Tab 36, civil works minimum, unpaved')]


def examplePipeCosts(dn):
    """Material and laying per pipe [€/m]: half the KWW pair value, the fitted line outside the table."""
    pair = KWW_MATERIAL_PAIR.get(dn, 23 + 3.05 * dn)
    return round(pair / 2, 1)


def ensurePipeCostColumns(cur):
    """Adds maintenance, lifetime, p_max and example to public.pipes of projects created before (values stay empty)."""
    addMissingColumns(cur, 'pipes', PIPE_COST_COLUMNS)


def dropBundleCostColumns(cur):
    """Removes invest_costs and operation_costs of public.pipe_bundle_types: never used, the costs are per pipe
    (pipes.costs) and per scenario. One ALTER TABLE and only if a column exists (see addMissingColumns)."""
    cur.execute("""SELECT column_name FROM information_schema.columns WHERE table_schema = 'public' AND table_name = 'pipe_bundle_types'
                   AND column_name = ANY(%s);""", (list(BUNDLE_COST_COLUMNS),))
    existing = [row['column_name'] for row in cur.fetchall()]
    if existing:
        cur.execute('ALTER TABLE public.pipe_bundle_types {};'.format(', '.join('DROP COLUMN IF EXISTS {}'.format(col) for col in existing)))  # nosec B608


def ensureEconomicTables(cur):
    """Creates the scenario tables if missing and the scenario 'base' with example values if there is none."""
    cur.execute(ECONOMIC_TABLES_SQL)
    cur.execute('SELECT count(*) AS n FROM public.economic_scenarios;')
    if cur.fetchone()['n']:
        return
    cols = list(BASE_SCENARIO)
    cur.execute('INSERT INTO public.economic_scenarios ({}) VALUES ({}) RETURNING id;'.format(','.join(cols), ','.join(['%s'] * len(cols))),  # nosec B608
                [BASE_SCENARIO[c] for c in cols])
    sid = cur.fetchone()['id']
    for group, price, escalation, description in BASE_PRICE_GROUPS:
        cur.execute('INSERT INTO public.price_groups (scenario_id,cost_group,start_price,escalation_pct,description) VALUES (%s,%s,%s,%s,%s);',
                    (sid, group, price, escalation, description))
    for mode, t, price in BASE_PRICE_CURVES:
        cur.execute('INSERT INTO public.price_curves (scenario_id,mode,t_supply,price_eur7kwh) VALUES (%s,%s,%s,%s);', (sid, mode, t, price))
    for surface, a, b, description in BASE_TRENCH_COSTS:
        cur.execute('INSERT INTO public.trench_costs (scenario_id,surface,a_eur7m,b_eur7m_dn,description) VALUES (%s,%s,%s,%s,%s);',
                    (sid, surface, a, b, description))


def trenchSurfaces(cur, extra=()):
    """The surfaces with trench costs in any scenario, plus the given values (e.g. those already in use), sorted.
    The trench costs define the surfaces; the dropdowns of the streets and the default surface offer them."""
    cur.execute("SELECT to_regclass('public.trench_costs') IS NOT NULL AS ok;")
    surfaces = set()
    if cur.fetchone()['ok']:
        cur.execute("SELECT DISTINCT surface FROM public.trench_costs WHERE surface IS NOT NULL AND surface <> '';")
        surfaces = {row['surface'] for row in cur.fetchall()}
    return sorted(surfaces | {value for value in extra if value})


def loadScenario(cur, scenario_id):
    """{'scenario': row, 'groups': {group: row}, 'levels': {group: {year: factor}}, 'curves': {mode: [(t, price)]},
    'trench': {surface: (a, b)}} of one scenario."""
    cur.execute('SELECT * FROM public.economic_scenarios WHERE id = %s;', (scenario_id,))
    scenario = cur.fetchone()
    if not scenario:
        return None
    cur.execute('SELECT * FROM public.price_groups WHERE scenario_id = %s;', (scenario_id,))
    groups = {row['cost_group']: row for row in cur.fetchall()}
    cur.execute('SELECT cost_group, year, factor FROM public.price_levels WHERE scenario_id = %s;', (scenario_id,))
    levels = {}
    for row in cur.fetchall():
        levels.setdefault(row['cost_group'], {})[int(row['year'])] = float(row['factor'])
    cur.execute('SELECT mode, t_supply, price_eur7kwh FROM public.price_curves WHERE scenario_id = %s ORDER BY t_supply;', (scenario_id,))
    curves = {}
    for row in cur.fetchall():
        curves.setdefault(row['mode'], []).append((float(row['t_supply']), float(row['price_eur7kwh'])))
    cur.execute('SELECT surface, a_eur7m, b_eur7m_dn FROM public.trench_costs WHERE scenario_id = %s;', (scenario_id,))
    trench = {row['surface']: (float(row['a_eur7m'] or 0), float(row['b_eur7m_dn'] or 0)) for row in cur.fetchall()}
    return {'scenario': scenario, 'groups': groups, 'levels': levels, 'curves': curves, 'trench': trench}
