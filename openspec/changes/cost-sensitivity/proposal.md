## Why

The cost optimization finds the pipes with the least net present value for one set of prices, interest rate, period
and limits. These inputs are uncertain over 40 years, and the review of the cost optimization report (2026-11-23,
point 8.1) asked whether the chosen pipe sizes are robust: would DN 80 still be best at 5 % interest, or DN 65? Today
that can only be answered by editing the scenario and running the whole optimization again, by hand, per case.

## What Changes

- A section "Sensitivity" in the cost optimization dialog with a table of parameters, each with a base value, a − value
  and a + value (absolute or relative); a row left empty is not varied. Parameters: interest rate, period, start price
  and escalation per cost group, cost factors for pipes, trench and pumps, the penalty prices of comfort violations and
  the hydraulic limits (specific pressure loss, velocity).
- Variants one at a time (2n + 1 with the base) by default; optionally all combinations (3ⁿ) or a Latin-hypercube
  sample of a chosen size with a saved seed. The dialog shows the number of variants and the estimated duration and
  asks before a long run.
- Per analysis the user chooses what a variant computes:
  - estimate: the best iteration of the last run (all stage versions for a run over stages) re-evaluated with the
    variant's parameters, and one step of the cost model with them; no simulation, seconds per variant;
  - full optimization: a cost optimization per variant with its own child versions, run one after another.
- Results in a new results tab "Sensitivity" and a section of the report: a parallel-coordinates plot (parameters and
  results as axes), a tornado chart of the NPV swing per parameter (rank correlations for combinations and samples), a
  table of the variants, a table of the lines whose pipe changes, and a map layer of robustness (share of variants that
  change a line's pipe, a sub group per stage).
- The saved scenario is never changed: a variant's parameters are applied in memory.

## Capabilities

### New Capabilities
- `cost-sensitivity`: the parameter table, the variant designs, the estimate and the full optimization per variant,
  the result file, the plots, tables and map layer, the report section.

### Modified Capabilities
<!-- None: the cost optimization's requirements stay; a run accepts parameter overrides as an implementation detail. -->

## Impact

- `cost_optimization.py` (section, results tab, the sequence of variant runs, parameter overrides of a run),
  new `utility_functions/sensitivity.py` (variants, overrides, estimate, result file, statistics) and
  `utility_functions/sensitivity_plots.py` (parallel coordinates, tornado), `cost_optimization_layers.py` (robustness
  layer), `network_economics.py` / `cost_model_data.py` (a scenario given as data, cost factors), `iteration_report.py`
  (section), translations, tests.
- No change to the project DB schema; old projects need no upgrade.
- Run time: an estimate takes seconds per variant; a full optimization per variant takes as long as a normal run.
