## 1. Data model and upgrade

- [x] 1.1 `DB_projectTablesDefault.txt`: pipes columns maintenance_pct, lifetime_a, p_max_bar, example; tables economic_scenarios, price_groups, price_levels, price_curves, trench_costs in `utility_functions/economic_data.py`
- [x] 1.2 `DB_versionTablesDefault.txt`: streets.surface (text, NULL = default surface)
- [x] 1.3 `upgrade.py`: ensurePipeCostColumns and ensureEconomicTables (scenario "base" with example values) in upgradeProjectDB; streets.surface in upgradeVersionDB
- [x] 1.4 Example values per DN (KWW 2026 Tab 36 material / 2 per pipe, DN175/225 interpolated; maintenance 1 %, lifetime 40 a, p_max 16 bar) and scenario "base" (trench paved 155 + 9.4·DN, unpaved 120 + 5.5·DN; pumps 100 €/kW, 2.5 %/a, 15 a; heat curve from the KWW heat pump factors) with sources: pipes in db_default_values and heating_network, scenario "base" by the upgrade

## 2. Dialogs

- [x] 2.1 Pipes table dialog with the new columns (translated headings)
- [x] 2.2 Scenario dialogs: scenarios table, and price groups, levels, curves and trench costs filtered by scenario; copy a scenario
- [x] 2.3 Electricity profile: select a file, check 8760/8784 values, copy into `<project>\prices\`, store the name in the scenario

## 3. Modules

- [x] 3.1 `utility_functions/economics.py`: price(t, h) per cost group, c(T) interpolation, cash flows, replacements, residual value, NPV, annuity, split by cost group (pure Python)
- [x] 3.2 `utility_functions/pipe_losses.py`: U' per pipe from layers, bundle position and ambient; T_amb from the ground model / climate file / duct; Q per pipe and hour; assignment to heat or cold by pair; check against QAmbtotal (15 %)
- [x] 3.3 Trench lengths per surface of a line from its overlap with the streets (pipe laying tolerance), default surface for the rest

## 4. Report

- [x] 4.1 Network report dialog: checkbox "Economics" and scenario combo (enums through compat.py)
- [x] 4.2 `reports.networkReport`: section Economics (investment, pump energy, losses, maintenance, NPV split, annuity, scenario, example warning, pipes without costs, lines over the loss tolerance); message naming missing results or a period shorter than a year
- [x] 4.3 Pipe table of the report with the per-pipe costs

## 5. Tests

- [x] 5.1 Unit tests economics.py: escalation and level table, profile normalization, c(T) interpolation and constant outside, replacements and residual value, NPV with interest 0, annuity, signed gain
- [x] 5.2 Unit tests pipe_losses.py: U' of a single buried pipe against a hand calculation, assignment by pair, check tolerance
- [x] 5.3 Unit tests trench costs: paved line, line partly off the streets, largest pipe of the bundle
- [x] 5.4 e2e test upgrade: an old project gets the columns, tables, scenario "base" and streets.surface, existing costs kept
- [x] 5.5 e2e/ida test report: project from a template, full-year results present → section with NPV and "example values in use"; one-day results → missing-results message
- [x] 5.6 Local validation: from districts/, the QGIS Python runs `-m pytest` and it passes (with `-m "not ida"` when IDA Districts is not installed), including test_static_mypy.py and test_messages.py

## 6. Translations, documentation, CI

- [x] 6.1 tr_msg / tr with German translations for headings, dialogs, the report section and messages; translations de/en compiled
- [x] 6.2 README.md and CLAUDE.md: the scenario tables, `<project>\prices\`, economics.py and pipe_losses.py
- [x] 6.6 Dialog 'Economic scenarios': info text in a read-only text field (`economic_scenarios_info`, en/de) on the tables, the profile, copying and the pipe costs
- [x] 6.7 Samples of IDA Districts: invest_costs / operation_costs of the pipe bundles removed from the handed-over db_tables.sql as well
- [x] 6.8 Dialog 'Economic scenarios': small graphs of the price curves heat and cold of the selected scenario (constant outside the points, a hint without a curve)
- [x] 6.9 Streets of the templates (plugin heating_network, the four IDA Districts samples) with the surface 'paved'; trench parts off the streets keep the default surface of the scenario
- [x] 6.5 invest_costs / operation_costs of the pipe bundles removed (table definition, templates, pipe bundle dialog, upgrade, resource import)
- [x] 6.4 Samples of IDA Districts (D9): db_tables.sql of the four samples with the pipe columns and example values, loaded into a test DB, handed over to be copied into IDA Districts
- [ ] 6.3 `npx openspec validate --all`, commit the artifacts with the code (explicit paths), `git pull --rebase`, push to dev and watch the plugin-tests run until both QGIS jobs pass
