## Why

The dynamic pipe sizing simulates whatever period the simulation dialog last saved for the version. The run of
the IDA Districts sample hc_network (test_hc_network_sizing.py) simulated a few minutes of January: the cooling
pair 2/4 had no demand (dp 1 Pa everywhere) and the target of the heating pair 1/3 was a customer without flow,
so the balancing aimed at about 0 Pa (quota 25-39 %). The user cannot set the period in the sizing dialog and
cannot check the simulated state before pipes are changed.

## What Changes

- The dialog gets the calculation period and the start-up period (from/to, as in the simulation dialog),
  pre-filled from the version's `networkSimData.txt`; every simulation of the run uses them, so they are written
  to the version's `networkSimData.txt` like the simulation dialog does. The other simulation settings
  (calculation/start-up type, number of periods, max. time step) stay as set in the simulation dialog.
- A checkbox "Reference run before the sizing (iteration 0)": build (option), simulate with the current pipes,
  load the results and evaluate every pair without sizing; saved and shown as iteration 0 with the outcome
  "reference". The run stops after iteration 0; the sizing is a second start.
- With "new child version" the reference run creates and loads the child and the dialog switches to "override
  the pipes of the loaded version", so the second start sizes in the same child. A start without the reference
  run in the loaded version keeps iteration 0; a start in a new child version deletes all iteration files.
- A warning in the log and in the iteration file when the target customer of a pair has less than 1 % of its
  peak mass flow at its critical time ("check the simulation period"). The balancing algorithm is unchanged.
- Checks before the start: from ≤ to for both periods.

## Capabilities

### New Capabilities
- `sizing-run-settings`: the simulation and start-up period of the sizing run, the reference run (iteration 0)
  with its version handling and the no-flow warning of a target customer.

### Modified Capabilities
<!-- none: the iteration files and layers per pair (sizing-iteration-results) are in the change balance-pipe-pairs,
     which is not archived yet; iteration 0 is specified here as an addition -->

## Impact

- `districts/dynamic_pipe_sizing.py` / `.ui`: period fields, reference checkbox, run start and stop, version switch.
- `districts/utility_functions/dynamic_sizing_results.py`: iteration 0 (outcome "reference", no new-pipe layer),
  deletion of the iteration files keeping iteration 0.
- `districts/utility_functions/flow_tracing.py`: peak mass flow of every customer for the warning.
- A template `dynamic_optimization` (one water circuit, a heat source and a pressure-holding top-up plant),
  delivered as an IDA Districts sample, and its test `test_dynamic_optimization.py` (1 January, reference run
  and sizing as two starts); `test_hc_network_sizing.py` becomes `test_hc_network.py` without the sizing.
- `districts/ida_ph.py`, `districts/utility_functions/workers.py`: the template is created like the other
  complete templates; a template folder in the plugin's `templates` is used before the IDA Districts samples.
- Translations (messages, info text, template name) and unit tests.
- Builds on the change balance-pipe-pairs (per-pair results); no DB schema change.
