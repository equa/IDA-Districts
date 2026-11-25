## Context

The sensitivity analysis (change cost-sensitivity, archived 2026-11-25) has two modes:
- **estimate:** `sensitivity.estimateVariant` values the best iteration of the last run with a variant's values and
  makes one step of the cost model (`cost_optimization.modelStep` / `modelStepStages`, `write=False`).
- **full:** `SensitivityRun.nextFull` runs a cost optimization per variant into `<version>_s<k>` and loads the base
  version again after each.

The estimate's step is a forecast. The third review of the cost report (2026-11-24, point 5.3) asked to check it by
simulation. Decision session of 2026-11-25, T1–T4.

Runs on QGIS 3.44 and 4.2. The button, the table and the plot use the widgets of `utility_functions/compat.py` and
matplotlib, as the sensitivity results already do; no other Qt5/Qt6 difference. No change to the project DB schema, so
old projects need no upgrade.

## Goals / Non-Goals

**Goals:**
- Show how far the cost model's forecast of a variant's step holds in a dynamic simulation: the NPV, the comfort
  violations and the technical limits.
- Spend simulations only where the step changes pipes, and only on the variants the user picks.

**Non-Goals:**
- More than one step per variant. The full mode covers that.
- A third mode in the mode selector (T4: the validation starts from an estimate).
- Simulating variants whose step changes no pipe (T1).

## Decisions

**D1 – What is simulated (T1).** Per validated variant, the pipes of the estimate's basis (the best iteration) plus the
variant's step, in one simulation, or one per stage version in a run over stages. A variant whose step changes no pipe
is marked "not simulated": its design is the basis design, whose NPV with the variant's values the estimate already
computed from simulated results.
*Alternatives:* a short optimization of k iterations (k times as long, and overlaps with the full mode); also
simulating unchanged variants (repeats the base run).

**D2 – The run is a cost optimization without a step (T2).** The validation reuses the cost optimization run, so
penalties, NPV parts, stage handling, the iteration file and the report come from one code path:
- the run parameters are `variantParameters(run parameters, variant values)`;
- the new keys are `max_iter = 0`, `new_version = '<version>_v<k>'` and `start_steps` (the variant's step);
- `begin()` writes `start_steps` into the new child versions before the first check, with the same function that
  writes a step (D3);
- the run simulates iteration 0 and ends with "max. iterations";
- in a run over stages, the stage versions are copied and linked as in a normal run (network-stages D11).

The sequence works like the full mode: one variant after another, the base version loaded again after each, a stop
keeps the finished variants. The child versions are kept; the user deletes them in the version handling.
*Alternatives:* temporary versions deleted after the evaluation (no inspection afterwards); a separate simulate-and-
evaluate path (duplicates the penalties, stages and NPV code).

**D3 – The step's pipes are saved and written by one function.** `estimateVariant` keeps its result keys and adds
`steps` with `[{'line', 'stage', 'after': {seq: pipe_id}}]`. The write part of `modelStep` / `modelStepStages`
becomes `applySteps(cur, steps, versions, roots)`; the step and the validation both call it. An analysis saved
before this change has no `steps`, so the validation refuses it with the reason "estimate again".

**D4 – The comparison (T1, T3).** Per validated variant, `sensitivity.validationResult(variant, row)` takes the
iteration 0 row of its run and gives:
- `npv_basis` (the estimate's NPV of the basis design), `npv_forecast` (`npv_after`) and `npv_simulated` (the run's
  NPV);
- `error_eur` = simulated − forecast, and `error_pct` relative to the simulated NPV;
- `confirmed`: whether the simulated NPV is below `npv_basis`;
- `penalty_change`: the present value of the comfort penalties of the run minus that of the basis design with the
  variant's prices (the part `penalties` of both splits; it covers every stage);
- `limits`: the lines over a limit;
- `versions`.

The limits are the ones the cost model checks for a smaller pipe, now applied to the simulated design: the specific
pressure loss and the velocity at the simulated peak flow above the run's `dp_spez_max` / `v_max`, and the plant
pressure above the least `p_max` of the pipes in use. This is a new function `CostModel.limitLines()` over the current
pipes, using the model the run builds anyway, through `limitViolation`.

The result is saved in the analysis as `variant['validation']`.

**D5 – Results (T3).**
- **Validation table**, in the dialog under the variant table and in the report as the section "Validation by
  simulation". One row per variant with a step: the columns of D4, or "not simulated" / "not selected".
- **Scatter plot:** x = forecast change (`npv_forecast − npv_basis`), y = simulated change (`npv_simulated −
  npv_basis`), with a diagonal and the variant names. A point below the diagonal means the step saved more than
  forecast.
- The parallel coordinates and the tornado keep the forecast, so each plot stays within one method.

**D6 – Start (T4).**
- The button "Validate…" sits next to "Reset the filter" on the results of an estimate, and is enabled when the
  analysis is an estimate with saved steps.
- A choice offers: all variants with a step, the selected variant, or the variants passing the filter. It shows how
  many simulations each choice needs and the estimated duration (`lastRunSeconds` × simulations ÷ iterations).
- Before the start, the validation runs the estimate's basis check (`estimateBasis`, `lineState`): if the pipes of the
  versions changed since the run, it refuses as the estimate does.
- Validating a variant again replaces its validation and creates the next free `_v<k>` name.

## Risks / Trade-offs

- [The child versions of many variants fill the version tree] → only variants with a step and only the chosen ones
  are simulated; the choice shows the number before the start.
- [The basis changes between the estimate and the validation, e.g. after another run] → the basis check of D6
  refuses, as the estimate does.
- [A run of `max_iter = 0` was not used before] → a test runs one validation end to end (marker `ida`) and checks that
  the child version holds the step's pipes and the row is iteration 0.
- [An IDA hang blocks the sequence] → as in the full mode, the stop button ends the current run and keeps the finished
  variants.

## Migration Plan

Nothing to migrate: analyses saved before this change keep working; only their validation is refused (D3).

## Open Questions

None.
