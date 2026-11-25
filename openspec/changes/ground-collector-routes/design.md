## Context

Change `ground-collector-model` built the pure-function side: the parameter contract (`ground_collector_contract.py`,
contract version 2), geometry presets, the 2D reference, the RC fit (`ground_rc.fitRc`), the Python ground model and its
start state (`ground_rc.startState`), and the climate signals (`ground_climate.py`). The Modelica components
`GroundCollector` and `GroundSurface` live in the IDA Districts library GroundMo (outside this repository, built and
installed with `install_groundmo.py`). In IDA Districts they agree with the Python model within 0.3 % over a year,
tested by packed models in `C:\EQUA\Projekte\districts\testing\components\GroundMo` (simulation_tests). Lessons from
those runs that this design relies on:
- the IDA Modeler starts a state from the value stored with the variable (`:V`), not from its start parameter;
- a variable is logged only when it carries `:L "<file>" :AS "<column>"` itself;
- names in a model are compared without case.

Today a route (`lines`) has `type` (lookup `line_types`, not read by any code) and `pipe_bundle_type_id`. The model build
(`invoke_network.insertLines`) writes every line as one `FDpipebundle` whose ambient temperature is bound to the
climate macro (`TGround`, `TAIR2`, `TDuct`). Junctions, plants and customers connect to its `liq1[k]`/`liq2[k]` by the
bundle's pipe sequences (`insertJunctionConnections`, `insertJunctionPlugConnections`, `insertConnections`). The decision
session of 2026-11-25 settled T1–T18 below; the explore session's T1, T3, T9, T11, T12 are kept.

Runs on QGIS 3.44 and 4.2. New dialogs use `utility_functions/compat.py` for the Qt5/Qt6 differences (enums,
`exec`); nothing else here is Qt-version specific.

## Goals / Non-Goals

**Goals:**
- Collector resources in the resources tab (with export/import) and collector routes in the lines layer, chosen in
  the existing `lines.type` dropdown.
- A model build that writes collector lines as `GroundCollector` + `GroundSurface` with fitted ground and start values.
- The fit and the start state computed by the plugin, cached, and checked before a build.
- Collector lines left alone by sizing and the cost optimization, costed by their own items, and reported.

**Non-Goals:**
- The generated climate macro and its `IGlob` signal: change `climate-macro-build`, applied first (T16).
- Sizing collectors (number of loops, trench length) by the cost optimization (T9).
- New collector types beyond the four presets of change 1; a second loop pipe per trench.
- Changes to the Modelica model (beyond the contract version marker in R5).

## Decisions

### R1 Collector resources: `public.ground_collectors` (T4a, T17, T18)
One row per collector type, edited in the resources tab:
- `id`, `name` (unique; also the name of its line type);
- the preset (`horizontal_ring`, `vertical_ring`, `flat_meander`, `bare_pipe`) and its inputs as jsonb (the
  arguments of the preset function, e.g. ring diameter, pitch, depth, spacing), edited in one numeric column per input
  (decided 2026-11-25: no plain text); a column the preset does not use is empty and locked;
- the loop pipe: `pipe_id` (`public.pipes`, inner/outer diameter, wall conductivity, roughness) and `loop_sequence`,
  the pipe sequence of the line's bundle whose terminals the loop takes (T11);
- the liquid of the loop (`liquid_id`, `public.liquids`) and its freezing point (default 0 °C), as `liqType` and
  `TFreeze` of the model (decided 2026-11-25);
- soil at the collector: conductivity, volumetric capacity, water content, frozen/unfrozen conductivity ratio (T17);
  the freezing temperature (0 °C) and range (1 K) of the soil water are columns with defaults, not in the dialog;
- surface: albedo, emissivity, convection, layer thickness and capacity;
- default `t_mean_init`, start mode (`undisturbed` or `precalculated`) with its years, `n_sections`
  (default 3);
- costs: per trench meter, per loop meter, maintenance %, lifetime (T9);
- `fits` jsonb: fit results keyed by fingerprint (R6).

The loop pipe comes from the resource, not from the line's bundle: the fit depends on the pipe, and one resource then
has one fit. The bundle pipe at `loop_sequence` only fixes which hydraulic circuit the loop belongs to.
*Alternatives:* the loop pipe from the bundle (one fit per resource and bundle pipe; rejected: more fits, and sizing
could change it); columns per preset input (rejected: four presets, different inputs).

### R2 Route type through `line_types` (T4, T4a)
`public.line_types` gets `ground_collector_id` (FK to `ground_collectors`, ON DELETE RESTRICT). Saving a resource
creates or renames its line type (same name; the id is the next free one); deleting a resource used by a line is
refused, naming the lines; an unused one is deleted with its line type. The `lines.type` dropdown (ValueMap from
`line_types`, `layer_visualization.mapValueFeatureType`) lists it without change. `isCollectorLine` in one helper
(`utility_functions/ground_collectors.py`) answers for every reader: the line's type has a `ground_collector_id`.
*Alternatives:* collectors inside `line_types` (T4a b), id ranges (T4a c); both rejected in the session.

### R3 Per-line `n_loops` and `t_mean_init` (T2, T13, decision 7)
Two columns on the version table `lines`: `n_loops` (integer, default 1, NULL counts as 1; the loops belong to the
line, not to the resource, decided 2026-11-25) and `t_mean_init` (NULL = the resource's mean liquid temperature, used
only by the pre-calculated start state), shown at the end of the physical data of the lines form for every line, used
only for collector lines. `upgrade.upgradeVersionDB` adds them;
`DB_versionTablesDefault.txt` has them for new versions. The topology generator carries them like `zeta`:
`prepareDB_pipeLaying_modeTables` (`network_help`), `insertLinesFromTopology`, `splitLinesPerPlantsJunctionsCustomers`
and the attribute copy back by proximity. `mergeLines` merges two lines only if `type`, `pipe_bundle_type_id`,
`n_loops` and `t_mean_init` are equal, so a collector is never merged into a pipe.

### R4 Model build (T1, T3, T11, T14)
`insertLines` splits a collector line into:
- `GroundCollector` "Collector_<lid>" with the loop pipe of the resource, `nLoops` from R3, `lTrench` = line length,
  `nSections` and `nCellsSection` (10), the fitted ground values (R6), soil and freezing from the resource, `liqType` and
  `TFreeze` from the resource's liquid (R1), and the start values (R7);
- `GroundSurface` "CollectorSurface_<lid>" with the resource's surface, connected to `surface`, its inputs bound
  `(1 "Climate-macro" "climate_processor" TAIR2)`, `TSKY` and `(1 "Climate-macro" "IGlob" OUTSIGNAL)`, `albedo` bound to
  the climate macro's gain "albedo" when the climate file has an albedo column (change `climate-macro-build`),
  otherwise to the resource's constant;
- an `FDpipebundle` "Pipebundle_<lid>" with the other pipes of the bundle (none if the bundle has only the loop pipe).

A helper `lineTerminals(lid)` maps every pipe sequence of a line to (model name, connector, index): the loop sequence to
`Collector_<lid>` `liq1`/`liq2`, the others to `Pipebundle_<lid>` `liq1[k]`/`liq2[k]` renumbered without the loop
pipe. `insertJunctionConnections`, `insertJunctionPlugConnections` and `insertConnections` use it instead of the
sequence index. Junction models keep counting pipes from `bundle_pipes` (the loop pipe still is one pipe of the line).
*Alternatives:* a pass-through `FDpipebundle` for the whole bundle plus a collector beside it (rejected: the loop pipe
would exist twice).

### R5 Checks before a build
Before writing a model with collectors, `invoke_network` checks:
- GroundMo is installed in the configured IDA Districts (`lib/Components/GroundMo/GroundMo.eo` exists) with contract
  version 2. The Modelica model gets `final parameter Integer contractVersion = 2` in `GroundCollector` (a one-line
  change of GroundMo); the check reads its value from `GroundMo.eo`;
- the climate macro provides `IGlob` (change `climate-macro-build`);
- every used resource has an accepted fit (R6).
Each failure stops the build with a `tr_msg` naming what is missing. `model_checks` (MCP rules) gets the same checks.

### R6 Fit at the build, cached (T18)
`ground_collectors.fitFor(resource, project settings)` builds `CollectorGeometry`, `SoilProperties` (resource soil,
undisturbed wave from the project's Kusuda settings `kusuda_*`, T17) and `SurfaceProperties`, computes
`ground_rc.fingerprint`, and returns the cached fit from `fits[fingerprint]` or runs `fitRc` (1–3 s, about 20 s for a
meander) and stores it. Stale entries (another `FIT_VERSION`) are dropped on store. Not accepted → the build stops
naming the resource and its errors. The resources tab's "Fit" action runs the same function for the selected rows and
shows errors, steady error and acceptance; it runs in a worker thread (QRunnable, as the other long actions) with a
progress message.

### R7 Start values (T12, T13)
Per line: `startState(params, geometry, soil, undisturbed=True, start_day)` for the undisturbed mode; for
`precalculated` the weather year of the project's climate file (`weatherFromClimate`, with the resource's albedo) and
`t_mean_init` of the line (or the resource), `years` from the resource, `start_day` = day of year of the simulation
start. A pre-calculated state takes several seconds (hourly ground model over years), so it is cached in the resource's
fit entry, keyed by (t_mean, years, start_day, climate file and its modification time). The values are written as
`TStart*` parameters and as `:V` of `TTop` … `TFar2` and `TSurface` (the IDA Modeler starts states from `:V`). The
model check names the start mode in the results' header.
`t_mean_init` "from results": an action on selected collector lines sets it to the mean liquid temperature of the
last annual run (`(TIn + TOut)/2` over the year); a model check warns when it differs by more than 2 K.

### R8 Sizing and cost optimization skip collectors (T9)
- `hydraulic_balancing.getLineData` drops collector lines; `pipe_sizing` filters them in its line SQL;
  `set_pipes.applyPipes` leaves their `pipe_bundle_type_id`.
- `cost_model_data.buildModel` marks collector lines `protected` and `collector`, so `CostModel.change` never changes
  them and their investment is the collector item (R9).
- Pressure drop and flow of a collector line still come from the simulation; dynamic sizing's pressure balance sees
  them through the results like any line.

### R9 Costs (T9)
`network_economics.investments` and `CostModel.investmentItems` give a collector line one item "collector": trench
meters × cost per trench meter + loop meters × cost per loop meter, with trench meters = line length × `n_loops` (every
loop in its own trench) and loop meters = trench meters × `loopLengthPerM`. It replaces the pipe and trench items of the
loop pipe; the other pipes of the bundle keep their pipe items, without a second trench (they lie in the collector
trench). Maintenance % and lifetime from the resource (replacement and residual value as for the other items). Collector
lines stay out of the heat-loss items and of `pipe_losses.checkLines`: their heat into the liquid is a gain, reported
as such (R10).

### R10 Results and report
- Output requests (`invokedOutputs['lines']`): per collector line `Line_coll_<lid>.prn` with `TIn`, `TOut`,
  `QExtracted`, `QSurface`, `TLoc[j]`, `TNear[j]`, `iceFraction[j]`, logged by `:L` on the variables.
- The heat balance in `outputs.py` sums `QAmbtotal` of the `Pipebundle_*` only; a new adder "qcollectors" sums
  `QExtracted` of all `Collector_*` into its own meter.
- `load_results` stores them in `line_s_coll_<var>` with the sections as segments (the line split into `nSections`
  equal parts); `show_on_map` shows them like the other line results.
- Network report and `version_kpis`: trench and loop meters, extracted heat per year and per trench meter (kWh/(m a)),
  lowest outlet temperature, largest ice fraction, per collector type and in total.

### R11 Resources tab, export and import
A "Ground collectors" button opens the generic table dialog (`show_TableDialog`) with a dropdown for the preset and the
loop pipe, and a "Fit" button (R6). Export writes the resources keyed by name (like `exportPipeSeries`), including the
`fits` cache and the loop pipe by its name; import adds or replaces them by name and recreates their line types.
Dialogs `ExportResources`/`ImportResources` get a table widget for them.

### R12 Module layout
`utility_functions/ground_collectors.py`: DB access to the resource and the lines' collector columns, `isCollectorLine`,
`fitFor`, `startValues`, `lineTerminals`, the GroundMo check; no Qt. The ground modules of change 1 stay unchanged and
QGIS-free.

## Risks / Trade-offs

- [The junction terminal renumbering breaks connections of lines with several pipes] → one helper (`lineTerminals`)
  used by all three connection writers; e2e test with a bundle of four pipes where the loop is sequence 2.
- [A pre-calculated start state takes seconds per line] → cached per resource and start parameters; lines of the same
  resource and settings share it.
- [GroundMo is not installed on a user's IDA Districts] → the check before the build (R5) with a message pointing to
  the installation; projects without collectors are never affected.
- [`climate-macro-build` is not applied yet] → this change's tasks start after it; the check (R5) refuses a climate
  macro without `IGlob`.
- [A Kusuda settings change makes every fit stale] → refit at the next build (seconds per resource), shown in the
  progress.
- [Collector lines distort pipe loss key figures] → excluded from the loss items and the 15 % check (R9), reported apart
  (R10).
- [Two routes on the same geometry (a return drawn in the collector trench)] → not needed: the return runs as another
  pipe of the bundle (T11); the topology check warns about overlapping lines as today.
- [The heat model assumes one loop per trench (trench meters = length × n_loops)] → stated in the resource dialog; a
  multi-loop trench is a different preset (e.g. flat meander with its width).

## Migration Plan

`upgrade.upgradeProjectDB` creates `public.ground_collectors` and `line_types.ground_collector_id`
(`db.ensureGroundCollectorTables`); `upgradeVersionDB` adds `lines.n_loops` and `lines.t_mean_init`. All are empty for
old projects, whose models and results do not change. The resource export of an older plugin version has no collectors;
importing it changes nothing. No rollback beyond the usual project backup: the new columns are unused without collector
resources.

## Open Questions

None.
