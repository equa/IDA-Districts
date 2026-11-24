## Context

The cost optimization (changes cost-optimization, plant-energy-costs, network-stages) sizes the pipes of a version, or
of the stage versions of a network built in stages, for one economic scenario (`public.economic_scenarios` with its
price groups, levels, curves and trench costs, loaded by `economic_data.loadScenario`) and the run's settings (penalty
prices, limits of a smaller pipe at peak flow). Each iteration's NPV comes from `network_economics.evaluateVersion`
(per stage summed by `network_stages.stagesNpv`); the step from the cost model (`cost_model_data.buildModel`,
`CostModel.step`, `cost_model.stagedStep`). At the end of a run the best iteration's pipes are in the versions and, if
needed, simulated again, so the result tables hold the best iteration. Review of the report (2026-11-23), point 8.1;
decision session of 2026-11-23, T1–T12. Runs on QGIS 3.44 and 4.2; the section and the tab use the widgets of
`utility_functions/compat.py` and matplotlib (already used for the NPV plot), no Qt5/Qt6 difference beyond them. No
change to the project DB schema: old projects need no upgrade.

## Goals / Non-Goals

**Goals:**
- Show how the NPV and the chosen pipes depend on uncertain inputs, cheaply by default, exactly on demand.
- One input table, one result file, the same plots and tables in the dialog and the report.

**Non-Goals:**
- Optimizing the pumps (review 8.3, later), upgrading pipes between stages (8.2, not wanted), constraints instead of
  penalties (8.4, not wanted).
- Varying categorical settings (system boundary, marginal threshold, deadband): compared with two normal runs (T12).
- A base other than the best iteration of the last run (T11; another iteration would need a new simulation).

## Decisions

**D1 – Parameters and their − / + values (T7, T12).** The table "Sensitivity" has one row per parameter: interest
rate, period, per cost group (electricity, fuel, purchased heat, heat, cold, maintenance, investment) the start price
and the escalation, cost factors for pipes, trench and pumps (multipliers, base 1), the penalty prices (€/Kh, €/kWh)
and the limits (Pa/m, m/s). Columns: varied (check), base (from the scenario and the run, read-only), mode (absolute or
relative %), −, +. A heat or cold "start price" is a factor on its price curve. *Alternative:* a free list of any
scenario column (harder to read, invalid combinations).

**D2 – A variant is an override, the scenario stays (T10).** `sensitivity.applyOverrides(scenario, overrides)` returns
a copied scenario with the values applied, `variantParameters(parms, values)` the run parameters (penalty prices and
limits set, the scenario values as `overrides`, which a run applies through `cost_optimization.runScenario`). `evaluateVersion` and `buildModel` accept a
scenario given as data instead of an id; the cost factors are a key `cost_factors` of the scenario dict, used where the
pipe costs, the trench costs and the pump costs are read (default 1). Penalty prices and limits are run parameters.
*Alternative:* temporary scenario rows in the DB (left over after a crash, visible in the scenario dialog).

**D3 – Variant designs (T8).** One at a time: the base and, per varied parameter, its − and its + value (2n + 1).
Combinations: every combination of −, base, + (3ⁿ). Sample: a Latin hypercube of N variants over [−, +] per parameter
(numpy, seed saved; the base added). The dialog shows the number of variants and the estimated duration (estimate:
about a second per variant and stage; full: the duration of the last run per variant, from its iteration files) and
asks before a run longer than 10 minutes.

**D4 – Estimate (T5, T11).** Basis: the best iteration of the last run in the loaded version; the dialog refuses when
there is none or when the lines no longer carry its pipes (`lineState` against the saved state, per stage), and says
why. Per variant: every stage version re-evaluated with the overrides (`evaluateVersion`, `stagesNpv` with the variant's
penalty prices; the marginal-plant prices follow the variant's prices), giving the NPV of the base design; the cost
models built with the overrides and one step (`stagedStep`, or `step` without stages), the same step an iteration of
the optimization makes, giving the lines that change and the estimated NPV after the step. The base variant reproduces
the best iteration's NPV (tested). A run in a worker task (`startTask`), cancellable between variants.

**D5 – Full optimization (T5).** Per variant a cost optimization with the dialog's settings and the overrides, into new
child versions `<version>_s<k>` (stage versions with the same suffix, D11 of network-stages). The variants run one after
another: after each run the dialog loads the base version again and starts the next. The run's iteration files and run
parameters stay in the variant's version; the sensitivity result file keeps per variant its version, the best NPV and
the best pipes per stage. Stop ends the sequence after the current run; the finished variants stay in the result.
*Alternative:* override mode in the stage versions (each variant would overwrite the previous one's pipes).

**D6 – Result file (T10).** `versions/<version>/sensitivity.json`: the table, the design, the seed, the mode, the base
(iteration, NPV, pipes per stage) and per variant its values, the NPV of the base design, the NPV after the step (or of
the run), the parts (investment, maintenance, energy, residual, penalties), the changed lines per stage with pipe before
and after. A new analysis replaces it (the full runs keep their versions).

**D7 – Results (T6, T9).** In the tab "Sensitivity" and the report, from the result file:
- parallel coordinates (matplotlib, each axis scaled to its range): the varied parameters, then NPV, investment,
  operating costs, number of changed lines; a line per variant, the base highlighted; a click opens it enlarged;
- tornado chart: per parameter the NPV at − and at + against the base, sorted by the swing (one at a time); for
  combinations and samples the Spearman rank correlation of each parameter with the NPV instead;
- table of the variants: values, NPV, parts, changed lines;
- table of the lines that flip: line (and stage), pipe in the base, pipe per variant where it differs;
- map layer "Sensitivity – robustness": the lines coloured by the share of variants that change their pipe (a sub group
  per stage for a run over stages, as D10 of network-stages), labelled with the share.

**D8 – Limits act on the step only.** The limits of a smaller pipe do not change the NPV of a design; in an estimate they
change which lines the step may make smaller, in a full optimization the whole path. The report says so next to the
tornado chart. *Consequence:* a limit row shows no NPV swing for the base design, only in the NPV after the step.

**D9 – Interactive parallel coordinates (2026-11-24, at the user's request).** In the tab 'Sensitivity' a click on a
line selects its variant (drawn red, its row selected in the variant table, the rows of the lines it changes
highlighted in the flip table); a row selected in the table selects its line. A drag along an axis draws a filter
rectangle; the variants outside every rectangle are drawn light and greyed in the table, the count is shown; a double
click on an axis removes its rectangle, 'Reset the filter' all. The enlarged view shares the selection and the filter.
The plots, the variant table and the flip table stand one above the other in a splitter, each table with a title that
says what it holds. The report keeps the static plots. Each plot can be undocked into a window of its own (resized,
maximized) and docked back by its button or by closing that window; this replaces a separate enlarged view. The flip
table is a matrix: a row per line a variant changes, the base pipe, a column per variant changing a line with its new
pipe and ↑ / ↓; its title names the source (the cost model's step from the simulated best iteration, or the simulated
runs). The tornado chart chooses its number of NPV ticks from the axis length, slanted.
The flips and the robustness are measured against the base variant, not against the run's pipes (2026-11-24): the base
variant's own step (the cost model with the run's values) is the reference. A step the run already simulated after its
best iteration and found worse (the cost model's error, e.g. one line made larger in every variant) would otherwise
show as a change in every variant. The base step is named apart, with the simulated and the expected NPV change when
the run tested it.

**D10 – Second review of the report (2026-11-24).** A run on a project whose plants buy fuel, with no fuel price in
the scenario, valued the bought energy with 0 € and, because that energy replaces the priced pipe losses
(plant-energy-costs D5), left the losses out of the NPV and the cost model (marginal price 0): about 12 k€/a in the
example. Now a carrier counted in the NPV without a price makes the evaluation price the pipe losses with the curves
(`energy_basis['fallback']`, `by_carrier` None) and the cost model use the curves (no marginal prices); the start check
of the dialog warns, the reports name it. The base scenario of a new project gets example prices for fuel (0.10 €/kWh)
and purchased heat (0.04 €/kWh); existing scenarios keep theirs (the warning names a missing one). The cost analysis
says why an energy part is 0 € (not available, not counted, in plant energy, no price, really 0, or the basis not
saved). Further: the purchases per item and year with the residual values, a note on rounding, the model error in €,
the units of the comfort violations, the sensitivity section titled as model-based estimate or full optimization with
its method, and per variant the NPV change by the step and the lines different from the base.

## Risks / Trade-offs

- [The estimate is one cost-model step, not a new optimum] → It is the same step the optimization takes; the table
  marks it "estimated", and the full optimization is one choice away for a variant with many changes.
- [Full optimizations take hours and switch the loaded version] → The duration is shown and confirmed; the sequence
  loads the base version again after each run and at a stop; each variant's versions stay for inspection.
- [A combination design explodes (3ⁿ)] → The count is shown before the start; the sample gives variety at a fixed
  size; for full optimizations the confirmation names the total duration.
- [Overrides missed in a code path that reads the scenario by id] → `evaluateVersion` and `buildModel` are the only
  readers in a run (`loadScenario` calls listed); a test checks that the base variant reproduces the NPV and that a
  changed interest changes it as `netPresentValue` does.

## Migration Plan

Nothing to migrate: no DB change, the scenario is untouched, older runs have no `sensitivity.json` and the tab says so.

## Open Questions

None.
