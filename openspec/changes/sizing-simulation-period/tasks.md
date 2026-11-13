## 1. Periods

- [x] 1.1 Dialog: calculation and start-up period (QDateTimeEdit, yyyy-MM-dd hh:mm:ss) filled from loadNetworkSimData of the loaded version
- [x] 1.2 Check before the start: from < to for both periods, warning naming the period
- [x] 1.3 simulate(): set the four dates of the hidden RunNetworkModelDialog before runModel

## 2. Reference run

- [x] 2.1 Checkbox "Reference run before the sizing (iteration 0)" in the group Iteration
- [x] 2.2 Run from iteration 0: evaluate every pair without applying the sizing, iteration file with outcome "reference", finish with the hint to start the sizing
- [x] 2.3 Iteration 0 not in the oscillation states; map without new-pipes layer; outcome text "reference"
- [x] 2.4 With "new child version": after the reference run select "override the pipes of the loaded version", log message naming the version
- [x] 2.5 `deleteIterations(config, keep_reference)`: keep iteration 0 for an override run without reference run, delete all otherwise

## 3. No-flow warning

- [x] 3.1 Flow tracing: peak absolute mass flow per customer over all time steps (`mdot_peak_customers`, also in the time mode global)
- [x] 3.2 Warning per pair when the target customer's mass flow at its critical time is below 1 % of its peak; `target_no_flow` in the pair summary

## 4. Tests

- [x] 4.1 Unit tests: period check, deletion keeping iteration 0, reference summary (no changes, outcome reference), no-flow check, table rows of iteration 0
- [x] 4.2 Template `dynamic_optimization`, delivered as an IDA Districts sample, not in this repository (from the project dyn_opt: one water circuit 1/2, a flow-controlled heat source and a pressure-holding top-up plant; full dump without results, climate file `clim:`; heights above sea level of the junctions and the top-up plant from the z of their line ends), offered in "Create project" and loading base1
- [x] 4.4 test_dynamic_optimization.py (skipped without the template): project from the template, period 1 January (one day), reference run in a new child version (pair 1/2 suggested from both plants, no no-flow warning), then the sizing in the same child (iteration 0 kept, parent unchanged)
- [x] 4.5 test_hc_network_sizing.py becomes test_hc_network.py: create, build, simulate 1 January, load results; no sizing (the sample has no pressure-holding plant, its network pressure loss is negative at every time step)
- [x] 4.3 test_dynamic_pipe_sizing.py runs with the new options at their defaults

## 5. Translations and documentation

- [x] 5.1 tr_msg with German translation for the new labels and messages; translations de/en compiled
- [x] 5.2 Info text `dynamic_pipe_sizing_info` (en/de): periods, reference run and the second start, no-flow warning
- [x] 5.3 README.md and CLAUDE.md updated if a command or file path changed

## 6. Validation

- [x] 6.1 From the plugin folder of the QGIS profile, the QGIS Python runs `-m pytest -m "not ida"` and it passes, including test_static_mypy.py and test_messages.py; test_dynamic_optimization.py and test_hc_network.py pass with IDA Districts
- [x] 6.2 `npx openspec validate --all` passes
- [ ] 6.3 Commit code and artifacts, `git pull --rebase`, push to dev and watch the plugin-tests run (`gh run watch`) until both QGIS jobs pass
