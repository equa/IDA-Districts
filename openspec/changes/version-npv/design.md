## Context

The cost optimization (`cost_optimization.py`) computes the NPV of each iteration in `CostOptimizationRun.evaluate`:
`network_economics.evaluateVersion` (investment, maintenance, energy, residual value) plus the NPV of the comfort
violations (`penaltyValues`, `penaltyCost`, `penaltyNpv`), over stages `network_stages.stagesNpv`. Its report
(`iteration_report.costReport`) shows the inputs, the parts and the terms. The network report has an "Economics" page
with `evaluateVersion` alone, without the comfort violations and without the terms.

Request of the user, 2026-11-27: the NPV of the loaded version in the results tab, same inputs as the cost
optimization, with a report. Implemented with the decisions below, confirmed by the user on 2026-11-27.

Runs on QGIS 3.44 and 4.2: plain widgets (`QDialog`, `QTableWidget`, `QgsCollapsibleGroupBox`), the enums as the
cost optimization dialog uses them; no other Qt5/Qt6 difference. No change to the project DB schema.

## Goals / Non-Goals

**Goals:**
- The NPV of a simulated version, equal to what the cost optimization would compute for it as iteration 0.
- A report that lets the user follow the number: inputs, parts, equations, terms.

**Non-Goals:**
- Simulating: the dialog evaluates the results that are in the version.
- Comparing several versions in one report.
- Replacing the "Economics" page of the network report.

## Decisions

**D1 – One calculation for the run and the version.** The NPV code of the run becomes module functions:
- `evaluateResults` (evaluation and penalty values of one version or of every stage version);
- `penaltySplit` (yearly penalty, parts with `penalties`, NPV);
- `stagedNpv` (stagesNpv and the stage entries with their terms);
- `versionNpvRow` (the row of a version, like an iteration row: `npv`, `split`, `economics` or `stages`, `state`,
  `deficits`).

The run calls the first three; the dialog calls `versionNpvRow`. So the numbers agree by construction.
*Alternatives:* a cost optimization with `max_iter = 0` (simulates again, needs IDA, takes minutes to hours); a copy of
the code in the dialog (two paths that drift apart).

**D2 – The inputs are those of the cost optimization's NPV.** Scenario, submodel, €/Kh with its tolerance, €/kWh
unmet with its tolerance, deadband, stages and required loads; the keys are those of the run parameters. Inputs the
NPV does not use (pairs, limits, iterations, periods, protected lines) are not shown. The required loads are the
project's list (`requiredLoads.json`), shared with the cost optimization and saved at "Calculate".

**D3 – Defaults.** In this order: the inputs of the version's last calculation (`version_npv.json`); the run parameters
of the version's last cost optimization (`cost_optimization_run.json`; its stages only when stage 1 is this version,
the run's result versions `stage_versions` first); the defaults of the cost optimization dialog. A label names the
source.

**D4 – Results are evaluated as found.** A year, or a period run with its weeks kept (`periods.json`), as
`evaluateVersion` reads them. Missing outputs or too short results are reported in the log with the missing outputs
or the days, and nothing is saved.

**D5 – Saved result.** `versions/<version>/version_npv.json` holds `saved`, `version`, `parms` (with the scenario name)
and `row`. The report reads this file, not the dialog, as the cost report reads the iteration files. A new calculation
overwrites it. The dialog shows the saved result with its date, so a stale one is visible.

**D6 – Report.** `iteration_report.versionNpvReport`, written by `writeReport(kind='npv')` into
`versions/<version>/reports/net_present_value_<time>.html`. It reuses the cost report's sections: `scenarioSections`
(moved out of `costReport`), `partStatus`, `stageSections`, `npvCalculation`, `investmentSections`. These take an
optional `words` (column header, title) so the version report says "Version" where the cost report says "Iteration";
without it they are unchanged. New sections: overview, parameters, NPV per part, investment per pipe and surface,
comfort violations per customer. No maps.

**D7 – Place in the UI.** A button under "Network report" in the group "Reports" of the results tab, with its own
icon `icons/VersionNpv.svg` (a € coin over the cost parts: flame for fuel, bolt for electricity, supply and return
pipe with a pump) and the tooltip "Calculate Net Present Value (NPV)" (key `tooltip_version_npv`, de/en). The dialog
starts with a collapsible "Description" (`infoTextEdit` of the key `version_npv_info`, de/en) like the cost
optimization dialog. The calculation runs in a worker
(`representative_periods.startTask`) on its own connection, as the run's evaluation.

## Risks / Trade-offs

- [The results were simulated with other pipes than the version now has] → the evaluation takes the pipes from the
  version and the temperatures and pumps from the results, as the cost optimization does after each check; the user
  simulates after a pipe change. The report states that the NPV is computed from the results of the version.
- [The scenario changes after a calculation] → the terms are saved with the calculation (`npvRecord`); the report
  shows the current scenario's inputs, as the cost report does.
- [Refactor of the run's evaluation] → `test_cost_optimization.py` (a run) and `test_network_stages.py` (a run over
  stages) cover the shared functions.

## Open Questions

None; D1–D7 confirmed 2026-11-27.
