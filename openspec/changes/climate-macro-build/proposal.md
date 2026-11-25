## Why

The IDA climate macro (`Climate-macro`) is a hand-made file that the plugin copies into every project, network,
supervisory model and customer and plant template, and patches only partly (site, file path, Kusuda). Its climate-file
columns are hard-coded, so files with wind as dx/dy or with extra columns (sky cover, precipitation, albedo) are not
used as they are; two diverging variants are shipped (WINDX/WINDY in the plugin root, WINDDIR/WINDVEL in the
templates); the constant ground and the duct temperature of the modelling settings never reach IDA; and the ground
collectors (change `ground-collector-routes`) need a global radiation signal `IGlob` that the macro does not have.
Users edit the macro in IDA from the resources tab, which confuses more than it helps.

## What Changes

- The plugin generates the climate macro from the version's climate settings (file, site) and the modelling settings,
  wherever it copies it today: the project's `climate\climate`, network builds, the supervisory model, and writing and
  opening a customer or plant template.
- The climate file's columns are read from its header row by name (case-insensitive); a file without a header has the
  IDA layout Time, TAir, RelHum, WindDir, WindVel, IDirNorm, IDiffHor. Wind as direction and speed or as `WindX`/`WindY`
  (velocity √(dx²+dy²)).
- The macro always contains the source file, the climate processor (`ENVIRONMENT`), the wind velocity `vel`, the air
  temperature, the vertical irradiation `ISolar` (as today, with the shading schedule), the ground temperature `TGround`
  (Kusuda or constant), the duct temperature `TDuct` (from the modelling settings) and the global horizontal radiation
  `IGlob` = IDIRNORM·sin(ELEVSUN) + IDIFFHOR.
- Extra columns: `SkyCover` and `PRECIPITATION` are bound to the climate processor, `ALBEDO` becomes a gain "albedo"
  (from % to a fraction), and every extra column is also a gain named after it.
- **BREAKING** The macro is always generated; a hand-edited project macro is replaced at the next build (kept once as
  `climate-macro.idm.bak`). The "Define climate data" button leaves the resources tab; the per-version climate dialog
  (file, site) stays.
- The shipped climate macro files are removed from the plugin root and the project templates.
- The Python climate functions take the sky cover from the file like the macro (`ground_climate.weatherFromClimate`).

## Capabilities

### New Capabilities
- `climate-macro`: generation of the IDA climate macro from the climate file and the settings, its contents and
  signals, column detection, and where it is written.

### Modified Capabilities
None.

## Impact

- Code: `ida_resources.py` (`updateClimateTemplate`, `updateClimateMacro`, `openClimateMacro` replaced by the
  generator), `invoke_network.py`, `supervisory_control.py`, `utility_functions/templateFiles.py`, `ida_resources.py`
  `openTemplate`, `districts.py` and `districts_dialog_base.ui` (button removed), `utility_functions/periods.py`,
  `utility_functions/ground_climate.py`; new module `utility_functions/climate_macro.py`.
- Files: 32 shipped `climate-macro.idm/.idc` copies removed from `climate/` and `templates/`.
- Simulation results: change where a project's macro differed from the generated one (constant ground, duct
  temperature, sky cover from the file); the simulation tests' references are checked and updated where expected.
- No DB schema change. Translations, README.md, CLAUDE.md.
