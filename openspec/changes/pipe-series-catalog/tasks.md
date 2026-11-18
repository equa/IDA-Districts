## 0. Prerequisite

- [ ] 0.1 Commit the open template and upgrade work of `network-cost-data` first (this change adds rows to the same `db_tables.sql` files and a call in `upgrade.py`)

## 1. Data model and upgrade

- [ ] 1.1 `DB_projectTablesDefault.txt`: tables `pipe_series` (D1, CHECK on system_type, name UNIQUE) and `pipe_series_pressure_ratings` (D3, series_id REFERENCES pipe_series ON DELETE CASCADE), column `pipes.min_bend_radius_m`
- [ ] 1.2 `utility_functions/db.py`: `ensurePipeSeriesTables` (CREATE TABLE IF NOT EXISTS, `addMissingColumns(pipes, min_bend_radius_m)`, one series row per series text without row), called in `upgrade.upgradeProjectDB`, in the pipes/series dialogs and before a resource import
- [ ] 1.3 Templates `empty_project`, `db_default_values`, `heating_network`: the two tables (empty in `empty_project`)

## 2. Catalogue

- [ ] 2.1 Materials P195GH, Cu-DHP, PE-Xa, PE 100, PE-LLD, PUR flexible (D8) in `db_default_values` and `heating_network`
- [ ] 2.2 Derivation script (kept under `districts/test/` as data of the u test): layers per type from da, s, Da and the casing wall max(2 mm, 0.02·Da); twin distance fitted with `pipe_resistances.py` to the catalogue's u (cover 0.80 m, ground 1.0 W/(m·K))
- [ ] 2.3 Pipe constructions, pipe layers, pipes (inner diameter, roughness of the catalogue, series, bend radius, p_max_bar, no costs, example false, description with source and assumed/fitted values) and one pipe bundle per twin, for all types of D5, in both templates
- [ ] 2.4 Series rows of D5 with limits and the pressure ratings isopex heating, isopex sanitary and isoclima PE 100; series rows DRE/DRD (D9)

## 3. Dialogs and resources

- [ ] 3.1 Series dialog: table `pipe_series` (system type as dropdown) with the pressure ratings of the selected series below; menu entry next to the pipes dialog; Qt enums through `compat.py`
- [ ] 3.2 Pipes dialog: column minimum bend radius
- [ ] 3.3 `ida_resources.py`: export the series of the exported pipes with their ratings; import creates a missing series by name with its ratings and keeps an existing one; new columns in `NULLABLE_COLUMNS`

## 4. Tests

- [ ] 4.1 Unit test u: every flexible single pipe within ±5 % and every twin within ±1 % of the catalogue's u; unique inner diameters per series
- [ ] 4.2 e2e test template: project from `heating_network` has the flexible pipes, series, ratings (isopex H 50 a / 70 °C = 8.5 bar), DRE/DRD series, materials, no costs on flexible pipes
- [ ] 4.3 e2e test upgrade: an old project gets the tables, the column and one series row per series text, pipes unchanged; a second load changes nothing; invalid system type rejected
- [ ] 4.4 e2e test series dialog: edit a rating of one series, rename a series (ratings kept), delete a series (ratings deleted, pipes unchanged)
- [ ] 4.5 e2e test resource export/import: series with ratings created in a project without it, kept in a project with it
- [ ] 4.6 e2e test network model: a line with the unequal twin S-50+32 is converted for the simulation without error
- [ ] 4.7 Test of the pipe sizing: next smaller pipe within a flexible series
- [ ] 4.8 Local validation: from districts/, the QGIS Python runs `-m pytest` and it passes (with `-m "not ida"` when IDA Districts is not installed), including test_static_mypy.py and test_messages.py

## 5. Translations, documentation, CI

- [ ] 5.1 tr / tr_msg with German translations for the series dialog, its headings, the system types and the bend radius; translations de/en compiled
- [ ] 5.2 README.md and CLAUDE.md: tables `pipe_series` / `pipe_series_pressure_ratings`, the flexible catalogue in the templates and its source
- [ ] 5.3 `npx openspec validate --all`, commit the artifacts with the code (explicit paths), `git pull --rebase`, push to dev and watch the plugin-tests run until both QGIS jobs pass
