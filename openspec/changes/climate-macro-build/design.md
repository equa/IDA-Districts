## Context

The climate macro is a DISTRICTS-MACRO named `Climate-macro`; every network, supervisory model and customer or plant
template has a `MACRO-OBJECT "Climate-macro"` whose content is a copy of `<project>\climate\climate\climate-macro.idm`
(created from `templates\<template>\climate` with a new project). `updateClimateTemplate` (run at every network build
and by the per-version climate dialog) recomputes the Kusuda values and `updateClimateMacro` patches site, file path and
Kusuda parameters into the project copy, which `invoke_network`, `supervisory_control` and `WriteTemplateFiles` copy on.
An existing template's copy is refreshed only by "Define climate data" (`openClimateMacro`), which also opens the macro in
IDA for hand edits. Readers of the macro, whose names must stay:
- pipes: `(1 "Climate-macro" "climate_processor" TAIR2)`, `"TGround" OUTSIGNAL`, `"TDuct" OUTSIGNAL`;
- the output file "climate" in networks, supervisory models and templates (TAIR, IDIRNORM, IDIFFHOR, IDir, IDiff,
  IDir_vert, ITot, velocity);
- template references `(:SYSTEM "Climate-macro" "climate_processor" TAIR2)`, `"vel" |y_var|`, `"ISolar" OUTSIGNAL`;
- the coming ground collectors: TAIR2, TSKY, `"IGlob" OUTSIGNAL`, `"albedo"`.

Shipped climate files (BROMMA, KALMAR, SAVE.PRN) have no header and the IDA layout; Swiss files (e.g.
`ABO_dry_NORMAL.prn`) have a header `#Time TAir RelHum WindX WindY IDirNorm IDiffHor SkyCover PRECIPITATION ALBEDO`.
The decision session of 2026-11-25 settled T14–T16, T19–T21. Runs on QGIS 3.44 and 4.2; no Qt code beyond removing a
button.

## Goals / Non-Goals

**Goals:**
- One generator that writes the complete climate macro (`.idm` and `.idc`) from the climate file and the settings.
- Every place that copies the macro today writes the generated one; no shipped macro files.
- Column detection by header, wind in both forms, extra columns used.
- `IGlob` and `albedo` for the ground collectors; constant ground and duct temperature reaching IDA.

**Non-Goals:**
- Editing the macro in IDA (removed); a climate file editor or converter.
- Ground temperature time series (`ground_timeseries`, commented out in the settings dialog today).
- Changes to the per-version climate dialog beyond what the generator needs.

## Decisions

### C1 Generator `utility_functions/climate_macro.py` (T15)
`climateColumns(path)` reads the first line: a line starting with `#` or with non-numeric tokens is a header, matched to
the known quantities without case (`time`, `tair`, `relhum`, `winddir`, `windvel`, `windx`, `windy`, `idirnorm`,
`idiffhor`, `skycover`, `precipitation`, `albedo`; other names are extra columns with their own name). Without a header
the IDA layout (T19). Missing time, air temperature, humidity, direct or diffuse radiation, or both wind forms, raises a
`ValueError` naming them; the build shows it with `tr_msg`.
`writeClimateMacro(folder, climate, settings)` writes `climate-macro.idm` and `.idc` from:
- `climate`: the version's climate row (file, site, time zone, height) as today (`getClimateData`);
- `settings`: modelling settings (ground model and its values, duct temperature, Kusuda values computed by
  `calculateKusudaSettings`).
It returns the list of signals it provides (used by checks, e.g. `IGlob`, `albedo`). No Qt, no DB; the caller reads
the DB.
*Alternatives:* patching a template file (today's approach; rejected: columns and objects vary with the file).

### C2 Contents of the macro (T14, T15, T20)
Objects, with the names the readers use:
- `climate_file` (SOURCE-FILE): the file path and one variable per column (`:AS <column>`).
- `climate_processor` (`:CEO ENVIRONMENT`): LAT, LONG, LONGTIMEZONE, HEIGHT; TAIR, RELHUM, IDIRNORM, IDIFFHOR from the
  file; wind as WINDDIR/WINDVELREF (direction and speed) or WINDX/WINDY (dx/dy); SKYCOVER and PRECIPITATION from the
  file when present, otherwise unbound as today (`:IV`).
- `vel` (`|Gain|`): the wind speed column, or √(dx²+dy²) via the multiplier/adder/`|Sqrt|` chain of the WINDX/WINDY
  variant.
- Air temperature: the processor's `TAIR2` (unchanged name).
- `ISolar` and its chain (`Idif`, `Idir`, `sunAngle`, `Cos`, `Max`, `minSunAngle`, `IdirToNorm`, `Schedule1` with the
  shading data "Shading"): the vertical irradiation as today.
- `IGlob` (ADDER) with `IdirHor` (MULTIPLIER) and `SinElev` (`|Sin|`): IDIRNORM·sin(ELEVSUN) + IDIFFHOR; the chain tested
  in IDA by the GroundMo test model `gc_climate`.
- `TGround` (ADDER): from `Kusuda` (`|kusuda|`, values as today) or, with the constant ground model, from a
  SOURCE-CONSTANT with `ground_temp`.
- `TDuct` (ADDER) from `TDuct-Const` = `duct_temp` (was fixed 20).
- Extra columns: one `|Gain|` per extra column named after it (factor 1); an albedo column gives only the gain
  `albedo` = 0.01 × ALBEDO (a second gain `ALBEDO` would clash: IDA compares names without case); a name that clashes
  with an object of the macro gets the suffix `_col`; `SkyCover` and `PRECIPITATION` also bound to the processor (T20).
The shading schedule data "Shading" is defined by the parent documents today; the generator writes the schedule as it
is, and every parent written by the plugin keeps defining it.

### C3 Where the macro is written (T15)
`updateClimateTemplate` (per-version climate dialog, every network build, and `openTemplate` before IDA opens a
template) computes the Kusuda values, writes them to the modelling settings, and generates the macro into the
project's `climate\climate` and into every customer and plant template folder of the project (`public.*_templates`),
as the removed "Define climate data" action used to copy it. Networks (`invoke_network`), the supervisory model and new
templates (`WriteTemplateFiles`) keep copying the project's macro, which is generated just before (the supervisory
model, written outside a build, takes the macro of the last build or climate dialog). A new project has no macro until
its first build, template opening or climate dialog. `updateClimateMacro`, `openClimateMacro` and the unused stub
`macros.updateClimateMacroIdm` are removed.

### C4 Hand-edited macros and the button (T21)
The first generation over a macro that the generator did not write (no marker `:D "Generated by Districts Modeler"` in
its header) keeps it once as `climate-macro.idm.bak` next to it. The resources tab's "Define climate data" button
(`btn_climateTemplate`, `show_manageClimateTemplate`) is removed; "Set climate data per project variant" stays.

### C5 Shipped files removed (T21)
The 32 `climate-macro.idm/.idc` files under `climate/` and `templates/` are removed; the project template's
`climate\climate.idm` system file stays (it holds the output file "climate").

### C6 Python side (T20)
`ground_climate.weatherFromClimate` reads the file through `climateColumns`, takes `SkyCover` when present (as IDA does)
and the albedo column when present (fraction), and otherwise the given constant. `periods.readClimate` and
`calculateKusudaSettings` use `climateColumns` for the air temperature instead of guessing.

## Risks / Trade-offs

- [Results of existing projects change] → where the old macro differed (constant ground model, duct 20 °C fixed, sky
  cover in the file); the change notes say so; the simulation tests' references are re-checked, and only expected
  differences updated.
- [A header name that is not recognised] → it becomes an extra gain; a missing required quantity stops the build with
  the column list of the file in the message.
- [Hand edits lost] → one backup per project macro (C4); README documents which settings replace them.
- [The shading data "Shading" missing in a parent] → every parent written by the plugin defines it (as today); a test
  checks the generated network and template files for it.
- [IDA rejects a generated macro] → the generator's output for both file layouts (BROMMA, ABO) is simulated in an IDA
  test (`ida` marker), and the existing simulation tests run on generated macros.

## Migration Plan

No DB change. At the next network build or template opening, each project gets the generated macro (the old one kept as
`.bak`). Rollback: restore `climate-macro.idm.bak` and use an older plugin version.

## Open Questions

None.
