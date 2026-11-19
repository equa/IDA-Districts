## Why

The pipe statics (EN 13941 / AGFW FW 401, roadmap T1–T12 in the archived change `pipe-series-catalog`) need a
mechanical model of the network: where the bends, small-angle kinks, tees and ends are, which pipe with which
outer diameter, wall and casing lies in each section, and how deep. Today this exists only implicitly in the line
geometry, the junctions and the pipe bundles. Both solver changes (`statics-steel-solver`,
`statics-plastic-flexible`) and `statics-results` build on this model, so it comes first.

## What Changes

- New step "Build statics model": generates the model of the loaded version from the lines (LineStringZ), the
  junctions, the pipe bundles, the pipe constructions and the pipe series, and stores it in tables of the version.
- Route geometry built once per line and shared by the pipes of the bundle; one pipe chain per single pipe and
  one per twin pipe (one casing, two carrier pipes).
- Bends from the vertices by angle classes in 3D: ignored, small-angle kink, prefabricated bend, elastic bend;
  runs of small kinks close together merged into one elastic bend. Thresholds and radii are project parameters.
- Cover per pipe from `bundle_pipes.y` minus the casing radius.
- Override layers `statics_points` and `statics_sections` (version tables, never touched by a build), snapped to
  the model by location at every build, so they survive a regeneration of the topology.
- A fingerprint of the model's inputs; a model whose inputs changed is reported as out of date.
- A build report (applied, unmatched and ambiguous overrides, skipped lines, implausible values) and a layer group
  "Statics model" with the model and the override layers.
- No statics calculation: the solvers and the result maps are follow-up changes.

## Capabilities

### New Capabilities
- `statics-model`: generation, storage, overrides, fingerprint, report and map of the mechanical network model
  used by the pipe statics.

### Modified Capabilities
None.

## Impact

- DB: new version tables (model, overrides, build record) in `DB_versionTablesDefault.txt` and, for existing
  versions, in `upgrade.upgradeVersionDB`; new project table `public.statics_parameters` in
  `DB_projectTablesDefault.txt` and `upgrade.upgradeProjectDB`. Child versions get the tables through the schema
  copy.
- Code: new `utility_functions/statics_model.py` (geometry rules, pure functions), `utility_functions/statics_db.py`
  (tables, build, fingerprint), `utility_functions/statics_layers.py` (layer group); a button and the parameter
  table dialog in `districts.py` / `districts_dialog_base.ui`.
- Translations (de/en), README.md, CLAUDE.md, tests in `districts/test`.
- No change to the simulation, the pipe sizing or the cost optimization.
