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
- [ ] 6.4 CI: commit, push to dev and watch the plugin-tests run until both QGIS jobs pass
