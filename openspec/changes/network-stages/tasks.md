## 1. Stage table

- [x] 1.1 Table 'Stages' in the cost optimization dialog (version dropdown, start year; stage 1 in year 0), saved with the run parameters; one row = today's run
- [x] 1.2 Stage check: each stage a descendant of the previous one (`id_base` chain), every line ID with the same geometry in the later stages, increasing start years; messages per problem

## 2. Cost model and NPV

- [x] 2.1 Cost model per stage (`cost_model_data.buildModel` for each stage version); ΔNPV of a change summed over the stages containing the line, investment discounted to the line's first stage
- [x] 2.2 Limits (peak flow, p_max) as the maximum over the stages; protected lines in all stages
- [x] 2.3 NPV by stage years (`economics.py`, `network_economics.py`): operating costs per stage with the factor of its years, purchase years from the item's first stage, pump increase at a stage's start year; NPV terms with stage and years

## 3. Run

- [x] 3.1 Iteration over all stages: step written into every stage (or its child version, the dialog's choice for all stages), build and simulate each stage, summed evaluation; iteration files with the state per stage
- [x] 3.2 Shared weeks (the run's weeks); per stage its own climate file, weights and `periods.json` (a stage with a poor coverage is not yet named separately)
- [x] 3.3 'Set pipes' sets all stages of the iteration

## 4. Report

- [x] 4.1 Stages (versions of the run, stage versions, start and operating years, climate files), the NPV per stage and iteration, the NPV per stage and part of the iteration with the least NPV; maps, pipe and trench lengths of the last stage (staged iterations save no single NPV terms)

## 5. Tests

- [x] 5.1 Unit tests: NPV by stage years (factors per range, purchase years from a later start, pump increase), coupled ΔNPV of a line in two stages, limits as the maximum
- [x] 5.2 e2e: stage check (valid chain, missing line, not a descendant) on a project with child versions; report of a staged run with fabricated iteration files
- [x] 5.3 ida: a run with two stages of the dynamic_optimization template (stage 2 an unchanged child version), both stages simulated per iteration, the NPV per stage, the same pipes in both stages

## 6. Translations, documentation, validation

- [x] 6.1 tr_msg texts with German translations, de/en compiled
- [x] 6.2 README.md and CLAUDE.md: stages of the cost optimization; the requirements of cost-optimization adjusted in that change
- [x] 6.3 Local validation: from districts/, the QGIS Python runs `-m pytest` and it passes on 3.44 and 4.2 (with `-m "not ida"` without IDA Districts), including test_static_mypy.py and test_messages.py
- [x] 6.4 CI: commit, push to dev and watch the plugin-tests run until both QGIS jobs pass

## 7. Lines matched by geometry and the version handling (D7, D8)

- [x] 7.1 Matching of the lines of consecutive stages by geometry (99 % within 0.5 m), roots over all stages; the stage check by coverage instead of IDs
- [x] 7.2 At the start the segments of later stages get the pipes of their root
- [x] 7.3 Step over roots (all segments, ΔNPV summed); writes per stage version with the update trigger of the version handling disabled; state per stage saved, restored at the end and by 'Set pipes'
- [x] 7.4 Tests: matching and coverage (unit, synthetic geometries), a stage 2 with split and renumbered lines (e2e), the trigger disabled during the writes
- [x] 7.5 Local validation and CI

## 8. Input data of every stage version (D9)

- [x] 8.1 `model_checks.checkVersions` (findings merged over the versions) and `findingLine`; the dialog checks the stage versions at the start, refuses on errors, logs warnings and infos
- [x] 8.2 Tests: merging, version prefix, skipped rules, messages (unit); a mapping failing in both stages and one failing only for a stage-2 customer, the start refused naming stage 2 (e2e)
- [x] 8.3 CI (run 44528358176 green)

## 9. Results per stage on the map and the step into an iteration in the table (D10)

- [x] 9.1 Map and report: a sub group per stage version with its lines, pipes, changed segments (by root) and new deficits (`stage_penalty`)
- [x] 9.2 Table of the iterations (dialog and report): the step counts in the row of the iteration they lead to, the outcome in the last row
- [x] 9.3 Tests: the map of each stage with a split line (e2e), the table rows (unit)
- [x] 9.4 CI (run 45161101678 green)

## 10. The versions of a run in one chain (D11)

- [x] 10.1 `linkStages`: each run version a child of the previous stage's run version
- [x] 10.2 `versionTriggers`: the triggers of the loaded version off during a run over stages, on again at its end, stop or failure
- [x] 10.3 `stageLinks` after the run: lines with an ID of another or longer line, lines under another ID; log, run parameters, report
- [x] 10.4 Tests: triggers off/on with an update kept in stage 1, the link, the split and the renumbered line (e2e); the chain and the triggers after a run (ida)
- [x] 10.5 CI (run 45165190643 green)

## 11. Report of a run over stages traceable (D12)

- [x] 11.1 NPV terms per stage saved (`npvRecord` with the stage inputs of `stagesNpv`); `npvTerms` with start year, operating years, first purchase and replacements
- [x] 11.2 Report: calculation, energy basis and factors per stage; investment table; parts per stage and iteration; changed lines per stage; losses in plant energy
- [x] 11.3 Report: equations with s_k and a…b, investment year, notes (nominal, model error, unmet energy, limits, signs), electricity profile
- [x] 11.4 Tests: the terms of each stage add up to its NPV, pumps from the stage start with replacement and residual value; the report sections of a staged run
- [x] 11.5 CI (run 45179943764 green)
