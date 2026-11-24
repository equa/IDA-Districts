## 1. Variants and overrides

- [x] 1.1 `utility_functions/sensitivity.py`: parameter rows from the scenario and the run (base values), absolute and relative − / +
- [x] 1.2 Variant designs: one at a time, all combinations, Latin-hypercube sample with seed (numpy)
- [x] 1.3 `applyOverrides` (a copied scenario with the values, the pipe cost factor in the scenario dict) and `variantParameters` (run parameters with `overrides`)
- [x] 1.4 `evaluateVersion` and `buildModel` accept a scenario given as data; the cost factors applied where pipe, trench and pump costs are read

## 2. Estimate

- [x] 2.1 Basis: the best iteration of the last run, its pipes checked per stage (`lineState`), refusal with a reason
- [x] 2.2 Per variant: NPV of the design (stages summed), one cost-model step, changed lines per stage, NPV after the step, parts
- [x] 2.3 Worker task, cancellable between variants; `sensitivity.json` written

## 3. Full optimization per variant

- [x] 3.1 A run accepts overrides (scenario data, penalty prices, limits); child versions `<version>_s<k>` (stages with the same suffix)
- [x] 3.2 Sequence of runs: base version loaded again after each, stop after the current run, finished variants kept in the result
- [x] 3.3 Duration estimate from the last run's iteration files; confirmation above 10 minutes

## 4. Dialog and results

- [x] 4.1 Section "Sensitivity" in the cost optimization dialog: table, design, mode, count and duration, start
- [x] 4.2 Tab "Sensitivity": parallel coordinates (enlarged on a click), tornado chart or rank correlations, variant table, flip table
- [x] 4.3 Map layer "Sensitivity – robustness" (share of variants per line, a sub group per stage)
- [x] 4.4 Report section with the same plots and tables

## 5. Tests, translations, docs

- [x] 5.1 Unit tests: rows and relative values, designs and seed, overrides (scenario unchanged, NPV with the overridden interest), rank correlation, tornado, flips, robustness
- [x] 5.2 e2e test: the section's parameters and the refusals of the basis; ida test: the estimate on the run over two stages (base variant = best NPV, scenario unchanged, result file, tab, layers per stage, report section)
- [x] 5.3 ida test: a full optimization of three variants with one iteration each (only with DISTRICTS_TEST_SENSITIVITY_FULL=1, about 20 min)
- [x] 5.4 Translations: tr_msg with German texts, de compiled
- [x] 5.5 Docs: README.md and CLAUDE.md (sensitivity.json, the new modules)
- [x] 5.6 Local validation from districts/: `-m pytest` passes (with `-m "not ida"` when IDA is not installed), including test_static_mypy.py and test_messages.py
- [x] 5.7 CI: commit, push to dev and watch the plugin-tests run until both QGIS jobs pass (run 45195917375 green)

## 6. Interactive parallel coordinates (D9)

- [x] 6.1 Selection: click on a line or a table row, the line red, the flip rows of the variant highlighted
- [x] 6.2 Filter rectangles by dragging along an axis, the variants outside light and greyed, removed by a double click or the reset
- [x] 6.3 Plots and tables one above the other with titles; the enlarged view sharing selection and filter
- [x] 6.4 Tests: click, drag and double click on the plot (unit), table selection and filter in the dialog (ida)
- [x] 6.5 CI (run 45348436228 green)
- [x] 6.6 Plots undockable into a window of their own (docked back by the button or closing the window)
- [x] 6.7 Flip table as a matrix (a column per changing variant, ↑ / ↓), its source named in the title and the report
- [x] 6.8 Tornado chart: NPV ticks by the axis length, slanted
- [x] 6.10 Flips and robustness against the base variant's step; the base step named apart with the run's simulated and expected NPV change
- [ ] 6.9 CI

## 7. Second review of the report (D10)

- [x] 7.1 Fallback to the price curves when a counted carrier has no price (evaluation and cost model); start warning; named in both reports
- [x] 7.2 Example prices for fuel and purchased heat in the base scenario of new projects
- [x] 7.3 Cost analysis: the reason of a 0 € energy part; purchases per item and year with residual values; rounding note; model error in €; comfort units
- [x] 7.4 Sensitivity section titled by its method; NPV change by the step and lines different from the base per variant
- [x] 7.5 Tests: the fallback (e2e), unpriced carriers, example prices, part status and purchases
- [ ] 7.6 CI
