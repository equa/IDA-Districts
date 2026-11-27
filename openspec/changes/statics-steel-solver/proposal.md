## Why

The statics model (`statics-model`) describes the network mechanically, but nothing calculates it yet. The roadmap
(T1–T12 in the archived change `pipe-series-catalog`) asks for a pipe stress verification under EN 13941 / AGFW
FW 401 that is comparable to sisKMR, with the plugin's own solver (T5). Rigid steel pipes (single and twin) carry
the highest temperatures and forces in a network, so they come first; plastic and flexible pipes follow in
`statics-plastic-flexible`.

## What Changes

- New step "Calculate statics": an FE solver (3D beam elements on non-linear soil springs) calculates the rigid
  steel pipes of the current statics model in load steps (stress-free state → heat-up with pressure → cooling →
  second heat-up), each with an upper and a lower friction coefficient.
- Loads per pipe: the higher of the design value (project parameter, overridable per section) and the simulated
  maximum of temperature and pressure (`line_s_temp$<seq>`, `line_s_p$<seq>`); the source is reported.
- Twin pipes as one beam with two carrier pipes in a shared cross-section; a temperature difference between them
  bends the twin.
- Laying methods cold, conventional, thermal prestressing and one-time compensators through a stress-free
  temperature per section; prestressed legs with the fictitious preheating temperature; self-prestressing reported
  as not supported.
- Soil: axial friction per FW 401, lateral springs up to the passive earth pressure; expansion pads placed by the
  solver (isoplus pad curve, 40 mm layers, 1 m pieces, at most 120 mm).
- Checks with limits as project parameters that name their source: a verdict where the source is at hand (axial
  stress of the straight steel pipe, PUR shear stress, minimum and maximum cover, pad thickness, movement for
  prestressed legs, cold laying temperature, one-time compensator travel), utilisation only where the limit is not
  yet confirmed against EN 13941 (stress range at bends and tees, hoop stress, buckling).
- Results in version tables with the model's fingerprint; the calculation runs in the background with progress
  and cancel, then shows a report.
- New statics parameters, new columns of `statics_sections` and `statics_points`.
- Not in this change: fatigue (new change `statics-fatigue`), result maps (`statics-results`), plastic and flexible
  pipes (`statics-plastic-flexible`), elastoplastic steel.

## Capabilities

### New Capabilities
- `statics-steel-solver`: loads, FE model, soil, laying methods, load steps, pads, checks, results, run and report
  of the statics of rigid steel pipes.

### Modified Capabilities
- `statics-model`: new statics parameters (design values, soil, friction, limits, pads); new override columns in
  `statics_sections` (lower friction coefficient, design temperature, design pressure, preheating temperature;
  fixed values of the laying method) and `statics_points` (one-time compensator data), stored in the model rows
  and part of the fingerprint.

## Impact

- DB: new version tables `statics_result_run`, `statics_result_elements`, `statics_result_nodes`,
  `statics_result_findings` (`DB_versionTablesDefault.txt`, `statics_db.ensureStaticsTables`); new columns of the
  override and model tables, added to existing versions by `upgrade.upgradeVersionDB`; new rows in
  `public.statics_parameters` added by `upgrade.upgradeProjectDB`.
- Code: new `utility_functions/statics_fe.py`, `statics_checks.py`, `statics_catalog.py`, `statics_solve_db.py`,
  `statics_task.py`; button "Calculate statics" in the modeling group (`districts_dialog_base.ui`, `districts.py`).
- Dependencies: numpy and scipy of the QGIS Python (present in 3.44 and 4.2: numpy 2.4.6, scipy 1.18.1).
- Validation source: isoplus planning manual (6th edition, `IP_Planungshandbuch_DE.pdf`), cited by page, not
  committed.
- Templates: `heating_network` and `db_default_values` get σ_ax 190 N/mm² on the rigid isoplus series.
- Translations (de/en), README.md, CLAUDE.md, tests in `districts/test`.
- No change to the simulation, the pipe sizing or the cost optimization.
