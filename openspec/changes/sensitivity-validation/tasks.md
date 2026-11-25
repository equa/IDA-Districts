## 1. Steps saved and written by one function (D3)

- [x] 1.1 `applySteps(cur, steps, versions, roots)` in `cost_optimization.py`: the write part of `modelStep` and `modelStepStages` (pipes of a line in every stage containing it, new bundles, line states); both call it
- [x] 1.2 `estimateVariant` saves `steps` ([{'line', 'stage', 'after': {seq: pipe_id}}]) in the variant's result
- [x] 1.3 Tests: `applySteps` through the cost optimization runs of one version and of two stages (ida), the saved steps written by the validation test (ida)

## 2. A run from given pipes without a step (D2)

- [x] 2.1 Run parameter `start_steps`: `begin()` writes them into the new child versions (all stage versions) with `applySteps` before the first check
- [x] 2.2 `max_iter = 0`: iteration 0 is simulated and the run ends with "max. iterations" without a model step
- [x] 2.3 `CostModel.limitLines()`: lines whose current pipes exceed `dp_spez_max` / `v_max` at the simulated peak flow, and the plant pressure above the least p_max; computed after the validation run (`sensitivity.validationLimits`), as a run of `max_iter = 0` builds no cost model
- [x] 2.4 Tests: `limitLines` on a small model; a run with `start_steps` and `max_iter = 0` holds the step's pipes in its child version (ida)

## 3. Validation sequence (D2, D6)

- [x] 3.1 `sensitivity.validationTargets(analysis, choice, selected, passing)`: the variants with a step for "all", "selected", "filtered"; the rest marked "not simulated"
- [x] 3.2 Refusal without saved steps and when the basis check (`estimateBasis`, `lineState`) fails
- [x] 3.3 `SensitivityRun.startValidation`: one run per target into `<version>_v<k>` (next free k) with `variantParameters` and `start_steps`; base version loaded again after each; stop keeps the finished ones
- [x] 3.4 Button "Validate…" next to "Reset the filter", enabled for an estimate with steps; a choice dialog with the number of simulations and the estimated duration
- [x] 3.5 Tests: targets per choice and the refusals (no IDA); the choice dialog in the test of 4.6

## 4. Comparison and results (D4, D5)

- [x] 4.1 `sensitivity.validationResult(variant, row)`: npv_basis, npv_forecast, npv_simulated, error_eur, error_pct, confirmed, penalty_change, limits, versions; saved as `variant['validation']`
- [x] 4.2 Validation table in the dialog under the variant table ("not simulated" / "not selected" rows)
- [x] 4.3 `sensitivity_plots.validationPlot(ax, analysis)`: forecast change against simulated change with a diagonal and the variant names
- [x] 4.4 Report section "Validation by simulation" after the variant table, with the table, the plot and a note on the method
- [x] 4.5 Tests: `validationResult` from a made-up row (forecast −2'500 €, simulated +2'600 €: not confirmed, error 5'100 €), the plot's points, the dialog table and the report section
- [x] 4.6 Test (ida): validation of the one variant with a step of an estimate over two stages, end to end, both versions kept with the step and the base version loaded again

## 5. Translations and documentation

- [x] 5.1 Every new text with `tr_msg` and a German translation, de compiled
- [x] 5.2 README.md and CLAUDE.md: the validation, `<version>_v<k>`, the new functions

## 6. Validation

- [x] 6.1 Local validation: from districts/, the QGIS Python runs `-m pytest` and it passes (with `-m "not ida"` without IDA Districts), including test_static_mypy.py and test_messages.py (QGIS 4.2: test_network_stages TestStagedRun with IDA, test_cost_optimization, test_sensitivity, test_iteration_report, test_messages, test_static_mypy; the whole suite in CI)
- [x] 6.2 CI: commit, push to dev and watch the plugin-tests run until both QGIS jobs pass (manual run 45577933059: QGIS 4.2 and 3.44 green)
