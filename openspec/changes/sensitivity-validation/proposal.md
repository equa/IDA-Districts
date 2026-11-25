## Why

The estimate of the sensitivity analysis (change cost-sensitivity) values the best design of a run with each variant's
prices and parameters and lets the cost model make one step. The step is a forecast of the linearized cost model, not a
simulated result. The third review of the cost optimization report (2026-11-24, point 5.3) asked for an optional check
of that forecast by a dynamic simulation, covering the NPV and also the comfort violations and the technical limits.
The full optimization per variant does not answer this: it runs a complete optimization for hours and no longer tests
the forecast itself.

## What Changes

- A button "Validate…" on the results of an estimate. It validates the variants whose step changes pipes: all of them,
  the selected variant, or those passing the filter of the parallel coordinates.
- Per validated variant, one cost optimization run without a step (iteration 0 only), into kept child versions
  `<version>_v<k>`. These hold the pipes of the best iteration plus that variant's step, and the run uses the variant's
  prices and parameters. In a run over stages, there is one child version per stage version, linked like the run's
  versions. The variants run one after another, the base version is loaded again after each, and a stop keeps the
  finished ones.
- Variants whose step changes no pipe are not simulated; they are marked "not simulated".
- Results in the dialog and in the report:
  - a validation table with these columns per variant: the NPV of the basis design, the forecast after the step, the
    simulated NPV, the error in € and %, whether the simulation confirms the step, the change of the comfort
    violations, the lines over a limit, and the version;
  - a scatter plot of forecast change against simulated change, with a diagonal.
- The parallel coordinates and the tornado keep the forecast values.
- The estimate saves the pipes of each variant's step, so that the validation can write them. The validation is
  refused for an analysis saved before this change.

## Capabilities

### New Capabilities
<!-- None -->

### Modified Capabilities
- `cost-sensitivity`: validation of an estimate by simulation (start, child versions, comparison, results).

## Impact

- `sensitivity_widget.py`: the button, the selection, the run sequence, the validation table and plot.
- `utility_functions/sensitivity.py`: the steps saved by the estimate, the validation result, the comparison.
- `utility_functions/sensitivity_plots.py`: the scatter plot.
- `cost_optimization.py`:
  - a run can start from given pipes and stop after iteration 0;
  - the code writing a step into the versions becomes one function, used by the step and by the validation.
- `iteration_report.py`: the report section. Also translations and tests.
- No change to the project DB schema; old projects need no upgrade.
- Run time: one simulation per validated variant (one per stage version in a run over stages).
