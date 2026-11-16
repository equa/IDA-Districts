## Why

The dynamic pipe sizing sizes and balances a network against pressure targets. Whether larger or smaller pipes pay
off over the amortization period – investment, trench, pumps and maintenance against pump electricity, heat and
cold losses and comfort – is not decided by it. Changes `pump-power-outputs`, `network-cost-data` and
`representative-periods` provide the pump power, the cost data, the net present value and fast checks with three
weeks; this change uses them to find the pipe sizes with the least net present value.

## What Changes

- A dialog **Cost optimization**: scenario, supply/return pairs, periods (three weeks or a year), penalty prices,
  max. iterations, new child version or the loaded one; iteration table, NPV diagram and map layers of the changed
  lines.
- A **cost model** (pure Python) on the kept results of a check: pressure drops, pump head (critical path for
  central pumps, own path for decentral pumps), pump power with η calibrated per pump, heat losses per pipe,
  investment and maintenance, all valued with the scenario and the weights of the periods.
- The **run**: iteration 0 simulates the user's pipes as reference; each iteration changes every line with a
  negative ΔNPV by one size of its series, balances the pairs in the model, checks the limits (p_max, a guard
  against starving a customer) and simulates the periods; it ends without improvement, on oscillation or at max.
  iterations, restores the pipes of the best simulated iteration and simulates them again if needed.
- **Penalties** relative to the reference: degree hours of the load models (heating or cooling needed and not
  reached, with a tolerance band) and unmet load of source-file customers (required load from a column of the
  source file, per template).
- A list of the required-load columns per template, saved in the project (`requiredLoads.json`).
- A handover list for the IDA Districts sample `dynamic_optimization` (low-temperature version).

## Capabilities

### New Capabilities
- `cost-model`: the model of a pipe change (ΔNPV per line, pump head, losses, limits and guard, balancing).
- `cost-optimization-run`: the dialog, the iterations with checks, penalties, tracking, versions and end of a run.
- `required-load`: the required-load columns of source-file customers and the unmet load.

### Modified Capabilities
<!-- none: the foundation changes are not archived yet; protected lines of protect-lines are honoured if present -->

## Impact

- New `districts/cost_optimization.py`, `utility_functions/cost_model.py`, `utility_functions/required_load.py`, a
  button in the main dialog, translations.
- Reuses `representative_periods.PeriodRun`, `network_economics`, `economics`, `pipe_losses`, `network_pumps`,
  `pipe_pairs`, `hydraulic_balancing`, `flow_tracing`, `dynamic_sizing_results` (iteration files and layers).
- Tests: unit tests of the model, e2e/ida on `dynamic_optimization` (short weeks), `simulation_tests` for the
  annual optimization and the comparison of weeks against a year.
- QGIS 3.44 and 4.2; no DB schema change.
