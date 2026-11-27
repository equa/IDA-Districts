## Why

The net present value (NPV) of a design is only computed inside a cost optimization run, for its iterations. A version
whose pipes were set by hand, by the pipe sizing or by "Set pipes", and that was simulated, has no NPV with the same
inputs. To compare such a version with a run, or one version with another, the user has to start a cost optimization
just to get iteration 0. The user asked (2026-11-27) for the NPV of the loaded version in the results tab, with the
same inputs as the cost optimization and with a report.

## What Changes

- A button "Net present value of the version" in the group "Reports" of the results tab. It opens a dialog:
  - the inputs of the cost optimization's NPV: scenario (with the links to the scenarios and pipe costs), submodel,
    the prices and tolerances of the comfort violations, the deadband heating/cooling, the stages and the required
    loads of source-file customers;
  - filled from the last calculation of the version, else from the version's last cost optimization run, else with
    the cost optimization's defaults;
  - "Calculate" evaluates the simulation results of the version (a year or the kept weeks of a period run) in a
    worker; nothing is simulated;
  - the parts of the NPV in a table (one column per stage over stages), messages in a log;
  - "Report" writes an HTML report and opens it.
- The calculation is the cost optimization's: the evaluation of the results, the NPV of the comfort violations, over
  stages the NPV of the stages. The run and the dialog call the same functions.
- The result and its inputs are saved in `versions/<version>/version_npv.json`.
- The report: overview, inputs (parameters, economic scenario, pipes in use, trench lengths), the NPV per part,
  investment per pipe and surface, the equations and the terms of the calculation, investment/replacements/residual
  value, the stages, the comfort violations per customer.

## Capabilities

### New Capabilities
- `version-npv`: the NPV of the loaded version with the inputs of the cost optimization, its dialog, file and report.

### Modified Capabilities
<!-- None: the cost optimization computes as before; its code is shared, not changed. -->

## Impact

- `version_npv_dialog.py` (new): the dialog.
- `cost_optimization.py`: the evaluation of results with the penalties (`evaluateResults`), the NPV parts with the
  comfort violations (`penaltySplit`), the NPV over stages (`stagedNpv`), the row of a version (`versionNpvRow`) and
  the carrier price warning (`carrierPriceNotes`) become functions, used by the run and the dialog.
- `utility_functions/iteration_report.py`: the scenario sections become a function; the sections per iteration take
  an optional wording ("Version" instead of "Iteration"); save/load of the result; the report `versionNpvReport`;
  `writeReport` kind `npv`.
- `districts_dialog_base.ui`, `districts_dialog.py`, `districts.py`: the button, its icon and its slot.
- Translations de/en; tests in `test_network_cost_data.py`.
- No change to the project DB schema; old projects need no upgrade. No IDA Districts needed.
