## Why

The pipe statics (planned as four follow-up changes, see design "Pipe statics roadmap") needs to know per pipe which
pipe system it is and which limits the manufacturer allows: temperatures, pressure over the service life, axial
stress, bend radius. None of this exists today: `pipes.series` is free text, and the templates only contain rigid
bonded pipes (isoplus DRE/DRD). Flexible pre-insulated pipes, which are common for house connections and small
low-temperature networks, are missing from the catalogue altogether, so they can be neither simulated nor sized.

## What Changes

- New project DB table `pipe_series`: one row per product line, named by the existing `pipes.series` text; system
  type (rigid single, rigid twin, bare plastic, flexible plastic, flexible metal), standard, maximum continuous and
  peak temperature, maximum pressure, maximum axial stress, safety factor.
- New project DB table `pipe_series_pressure_ratings`: allowed pressure per series over operating time and
  temperature (the curves of DIN 16893 / ISO 13760 for plastic pipes).
- `pipes` gets the minimum bend radius.
- Upgrade of existing projects: the tables are created and every existing series text gets a row with an empty
  system type.
- A series dialog with the pressure ratings as sub-table; the pipes dialog shows the bend radius; the resource
  export/import carries series and ratings.
- Materials P195GH, Cu-DHP, PE-Xa, PE 100, PE-LLD and the PUR foam of flexible pipes in the templates.
- The isoplus flexible catalogue (chapter 3: isoflex, isocu, isopex heating and sanitary including twins,
  isoclima) in the templates `heating_network` and `db_default_values`, with series rows and pressure ratings.
  Values the catalogue does not give (casing wall, distance of twin carrier pipes) are derived so that the plugin's
  thermal model reproduces the catalogue's heat loss coefficient u.
- Series rows with limits for the existing series "Isoplus DRE Standard" and "Isoplus DRD Standard".

## Capabilities

### New Capabilities
- `pipe-series`: the series table, the pressure ratings, the bend radius, the dialogs, resource export/import and
  the upgrade of existing projects.
- `flexible-pipe-catalog`: the isoplus flexible pipes, their materials and series in the templates, and the
  derivation of the values the catalogue does not give, checked against the catalogue's u.

### Modified Capabilities
<!-- none: the pipe catalogue has no spec yet -->

## Impact

- `districts/DB_projectTablesDefault.txt`, `upgrade.py`, `utility_functions/db.py`, templates `db_default_values`,
  `heating_network` (and `empty_project` for the empty tables).
- `districts.py` (pipes dialog, new series dialog), `ida_resources.py` (resource export/import).
- `utility_functions/pipe_resistances.py`, `twin_pipe.py` are used for the derivation; no change to the simulation.
- The pipe sizing keeps choosing within `pipes.series`; it does not use the new limits yet.
- Overlaps with the open change `network-cost-data` (`pipes.p_max_bar`, templates, `upgrade.py`).
- Translations, unit tests, an e2e test of the upgrade and of the resource export/import.
