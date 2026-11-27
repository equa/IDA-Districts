## 1. One calculation for the run and the version (D1)

- [x] 1.1 `cost_optimization.py`: `evaluateResults`, `penaltySplit`, `stagedNpv` and `carrierPriceNotes` as module functions; `CostOptimizationRun` calls them
- [x] 1.2 `versionNpvRow(cur, config, parms, settings, prices, required, stages, climates)`: the row of a version like an iteration row (`npv`, `split`, `economics` or `stages`, `state`, deficits)

## 2. Dialog (D2, D3, D4, D7)

- [x] 2.1 `version_npv_dialog.py`: collapsible description (`version_npv_info`), inputs with links to the scenarios and pipe costs, stage table, required loads, result table, log, buttons Calculate/Report/Close
- [x] 2.2 Defaults from version_npv.json, else the last cost optimization run of the version (its stages only when stage 1 is this version), else the cost optimization's defaults; a label names the source
- [x] 2.3 Calculation in a worker (`representative_periods.startTask`); refusal without scenario or submodel and for invalid stages; missing outputs or short results in the log, nothing saved
- [x] 2.4 Button `btn_versionNpv` with icon `icons/VersionNpv.svg` and tooltip under "Network report" in the results tab (`districts_dialog_base.ui`, `districts_dialog.py`, `districts.py`)

## 3. Saved result and report (D5, D6)

- [x] 3.1 `iteration_report.saveVersionNpv` / `loadVersionNpv`: `versions/<version>/version_npv.json` with saved, version, parms (with scenario name) and row
- [x] 3.2 `scenarioSections` moved out of `costReport`; the shared sections take an optional `words` ("Version" instead of "Iteration")
- [x] 3.3 `versionNpvReport` and `writeReport(kind='npv')` into `reports/net_present_value_<time>.html`

## 4. Tests

- [x] 4.1 `test_network_cost_data.py::test_version_npv` (e2e): NPV equal to `penaltySplit` of the evaluation, without comfort violations equal to the evaluation's NPV, with violations higher; saved file; report text and file name; the dialog's defaults, description, calculation and saved result
- [x] 4.2 The shared run functions through `test_cost_optimization.py` and `test_network_stages.py` (ida)

## 5. Translations and documentation

- [x] 5.1 Every new text with `tr_msg` and a German translation, `version_npv_info` and `tooltip_version_npv` de/en, de and en compiled
- [x] 5.2 README.md and CLAUDE.md: the NPV of a version, `version_npv_dialog.py`, `version_npv.json`, the report

## 6. Validation

- [x] 6.1 Local validation: from districts/, the QGIS Python runs `-m pytest` and it passes (with `-m "not ida"` without IDA Districts), including test_static_mypy.py and test_messages.py
- [ ] 6.2 CI: commit, push to dev and watch the plugin-tests run until both QGIS jobs pass
