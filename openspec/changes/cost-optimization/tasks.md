## 1. Cost model

- [x] 1.1 `utility_functions/cost_model.py`: model state from the kept results of a check (line mass flows and temperatures per simulated hour, weights, pump power, customer paths from traceCustomerSupply), pipe catalog with series
- [x] 1.2 Pressure drops per line and hour (specificPressureLoss), pump head: central over the critical path of the customers it supplies, decentral over the customer's own path (signed flows); η_eff per pump calibrated from its simulated power
- [x] 1.3 ΔNPV of a one-size change per line (pipes of the pairs in its bundle): investment and maintenance of pipes and trench, pump energy, heat and cold losses (pipe_losses), valued with the scenario and the period weights (economics, network_economics)
- [x] 1.4 Limits and guard: p_max per pipe and hour, a smaller pipe limited at the peak flow (300 Pa/m, 3 m/s); rejected changes with reason
- [x] 1.5 Step of an iteration: best one-size change of every line with negative ΔNPV, skipping protected lines and lines of no pair; balancing of the pairs in the model; predicted NPV

## 2. Required load and penalties

- [x] 2.1 `utility_functions/required_load.py`: requiredLoads.json in the project (template, column, unit, mode), detection of templates with SOURCE-FILE (defaults column 2, W, heating)
- [x] 2.2 Reading a customer's source file (invoked_sf, sf-macro), interpolation to the result time steps, unmet load per time step with the 2 % tolerance, kWh per year with the weights
- [x] 2.3 Degree hours per customer and time step from customer_s_troom / tset / hcmode with the tolerance band; penalties relative to the reference

## 3. Run and dialog

- [x] 3.1 Dialog "Cost optimization" (cost_optimization.py, button in the main dialog): scenario, pair table (suggestPairs), periods (weeks or annual, from representative_periods), penalty prices, max. iterations, version; hint without sizing iterations; needed outputs named; enums through compat.py
- [x] 3.2 Run: optional child version, iteration 0 as reference (PeriodRun, build with the features invoked again), iterations: step, write the pipes (getOrCreatePipeBundles), PeriodRun, evaluation (network_economics with penalties), model error
- [x] 3.3 End: no improvement for 2 iterations, oscillation, no improving step, max. iterations; restore the best iteration and simulate it again if it was not the last
- [x] 3.4 Iteration files (row, steps, rejected changes) in the version folder, iteration table, NPV diagram (matplotlib, stacked, model line), map layers of the changed lines; files of earlier runs removed at the start
- [x] 3.6 Option to switch on the needed requested outputs at the start (requested outputs worker); hint about missing balancing iterations as a link to the hydraulic balancing dialog
- [x] 3.7 Results in tabs (iterations, NPV, log); per iteration a map group (`cost_optimization_layers.py`: inner diameters, lines changed for the iteration, customers with a new deficit); saved iterations listed at the opening, selected rows shown on the map
- [x] 3.5 Protected lines of protect-lines honoured if the version has them

## 4. Tests

- [x] 4.1 Unit tests cost_model: pressure drop and head (central critical path, decentral own path), η_eff calibration (2 kW, 0.01 m³/s, 100 kPa → 0.5), ΔNPV on and off the critical path, p_max rejection, guard, step with two improving lines and one size at most
- [x] 4.2 Unit tests required_load and penalties: detection defaults, interpolation, 10 vs 9 kW → 1 kWh, 9.9 kW within the tolerance, degree hours only when needed, penalty relative to the reference
- [x] 4.3 e2e/ida test on a project from dynamic_optimization (skipped without it): run with three one-day weeks and max. 2 iterations in a child version; iteration 0 reference, rows with NPV and model error, the version's pipes of the best iteration, the parent unchanged
- [x] 4.4 test/test_cost_optimization_annual.py (marker annual, only with DISTRICTS_TEST_ANNUAL=1; simulation_tests runs bare IDA models without QGIS): annual optimization of base1 and of the low-temperature version (skipped until the IDA sample has it), NPV of the weeks against the annual NPV reported
- [x] 4.5 Local validation: from districts/, the QGIS Python runs `-m pytest` and it passes (with `-m "not ida"` when IDA Districts is not installed), including test_static_mypy.py and test_messages.py

## 5. Sample handover, translations, documentation, CI

- [x] 5.1 Handover list for the IDA Districts sample dynamic_optimization (D12): customer template 4_simplified_consumer_hp and the plants of low_temperature_network, a new version using them, low-temperature plant setpoints, network pumps, default costs and price curves; skip conditions of the tests
- [x] 5.2 tr_msg / tr with German translations for the dialog, the table, the diagram and the messages; translations de/en compiled
- [x] 5.3 README.md and CLAUDE.md: the dialog, cost_model.py, required_load.py, requiredLoads.json and the iteration files
- [ ] 5.4 `npx openspec validate --all`, commit the artifacts with the code (explicit paths), `git pull --rebase`, push to dev and watch the plugin-tests run until both QGIS jobs pass
