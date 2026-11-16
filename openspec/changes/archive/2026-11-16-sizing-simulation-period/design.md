## Context

`DynamicPipeSizingRun.simulate()` creates a hidden `RunNetworkModelDialog` and calls `runModel`, which reads the
dialog's widgets (`setNetworkSimData`) and writes them to `versions/<version>/networkSimData.txt`. The widgets are
filled from that file (`loadNetworkSimData`), dates as `yyyy-MM-dd hh:mm:ss` in `dateedit_startupFrom/To` and
`dateedit_calcFrom/To`. So the period of every sizing simulation is the one last saved by the simulation dialog.

Iteration 1 always simulates (after an optional build) and sizes in the same step. The iteration files of a
previous run are deleted at the start (`deleteIterations`); a new child version is created before the first
iteration (`createVersion`).

The flow tracing (`scanNetworkPressureLoss`) loads the customer mass flows of all time steps but keeps only the
value at the customer's critical time.

QGIS 3.44 (Qt5) and 4.2 (Qt6): the new widgets are `QDateTimeEdit` and `QCheckBox` in the existing dialog; no
enum beyond those already used. No DB schema change.

## Goals / Non-Goals

**Goals:**
- Set the simulation and start-up period of the sizing in its dialog, consistent with the simulation dialog.
- Look at the simulated state of all pairs (iteration 0) before any pipe changes.
- Point the user to an unsuitable period when a target customer has no flow.

**Non-Goals:**
- An evaluation window inside the simulated period, or a period per pair.
- Changing the balancing algorithm (excluding customers without flow): a separate change if the warning also
  appears with a suitable period.
- Calculation type, start-up type, number of periods and max. time step in the sizing dialog.

## Decisions

**D1 – Periods through the simulation dialog's widgets.** The sizing dialog gets `dateedit_calcFrom/To` and
`dateedit_startupFrom/To` (same format), filled from `loadNetworkSimData` of the loaded version when the dialog
opens. Before `runModel`, `simulate()` sets the four dates of the hidden `RunNetworkModelDialog`, so
`setNetworkSimData` writes them with the other settings unchanged into the version being simulated (the child
version after `createVersion`).
*Alternative:* writing `networkSimData.txt` directly – a second writer of the same file whose keys can drift.

**D2 – Checks.** Before the start: calculation from < to and start-up from < to; otherwise a warning naming the
period and no run.

**D3 – Reference run as iteration 0.** Checkbox `checkBox_referenceRun` (default off). With it the run starts at
iteration 0: [build] → simulate → load → `evaluatePair` for every pair, but the sizing results are not applied:
the iteration file `dynamic_sizing_iter0.json` has outcome `reference`, `n_changed` 0 and per pair the simulated
customers and lines (`pipe_new` = `pipe`, `changed` false); then the run finishes with "Reference run finished:
check the iterations, then start the sizing without the reference run." (progress 100). The oscillation states
do not contain iteration 0. On the map iteration 0 has the customer and line layers and an empty "new pipes"
layer is not created.

**D4 – Version of the reference run.** With "new child version" the reference run creates and loads the child as
today, runs iteration 0 there, and at the end sets `rbtn_override` (log: "The sizing continues in version <child>:
'override the pipes of the loaded version' is selected."). Deleting iteration files at the start of a run:
- reference run, or a new child version: all iteration files (as today; a child gets the parent's files copied);
- otherwise (override the loaded version): the files of iterations ≥ 1, iteration 0 is kept.
`deleteIterations(config, keep_reference=False)` gets the parameter.

**D5 – No-flow warning.** `scanNetworkPressureLoss` also records the peak absolute mass flow of every customer over
all time steps (`mdot_peak`, from the series it already loads); `getCustomerLineMdot` returns it as
`mdot_peak_customers` (in the 'global' time mode it is loaded with `getTimeSeries` of the whole period). After
`optimizePipeDiameters` of a pair, if `|mdot of cid_target| < 0.01 · mdot_peak(cid_target)` the log shows "Pair
{}: target customer {} has almost no flow at its critical time ({:.3g} of {:.3g} kg/s); check the simulation
period." and the pair summary gets `target_no_flow: true`. Also in iteration 0.
*Alternative:* a threshold in kg/s – depends on the network size; the share of the own peak does not.

## Risks / Trade-offs

- [Setting the period in the sizing overwrites the simulation dialog's period of the version] → it is the same
  file on purpose (one truth); the fields are pre-filled from it, so an unchanged dialog changes nothing.
- [A kept iteration 0 belongs to other pipes or another period than the second start] → it is kept only when the
  second start overrides the loaded version (where the reference was simulated); the info text says iteration 0
  is the state before the sizing of the latest reference run.
- [The automatic switch to "override the pipes of the loaded version" surprises the user] → log message and
  message bar name the version; the radio button is visibly changed.
- [1 % threshold flags customers with a legitimately tiny load] → only a warning, no change of the result.
- [In the sample hc_network the network pressure loss is negative at every time step (probably decentral pumps), so the
  critical time is the first time step, without flow, whatever the period (a run of 1 January to 30 June warned
  for both pairs)] → the sizing is tested on the template `dynamic_optimization` (an IDA Districts sample) instead: one circuit with a
  pressure-holding top-up plant beside the heat source, as in the project dyn_opt. The hc_network test stops after
  loading the results.

## Migration Plan

No data migration; existing `networkSimData.txt` files are read as before. Iteration files without
`target_no_flow` read as false. Rollback: revert the commit; an iteration 0 file would be listed as an iteration
by the old code.

## Open Questions

None.
