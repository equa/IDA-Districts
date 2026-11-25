## Why

A district network is rarely built at once: customers and plants are added in stages (e.g. years 0–10, 11–20,
21–40), and the lines of an earlier stage keep their pipes. The cost optimization sizes one network for one year of
operation, valued over the whole period, so a line that a later stage loads more is sized too small, and investments
of later stages are valued as if made in year 0 (review of 2026-11-18, point 4).

## What Changes

- A stage table in the cost optimization dialog: the stage versions in order with their start year (stage 1 in year
  0). The plugin checks that each stage descends from the previous one and that every line of a stage exists with the
  same ID in the later stages.
- The optimization is coupled over the stages: a line is sized for the flows of every stage it exists in; its ΔNPV is
  its investment in the stage it first appears in plus the operating costs of every stage; the peak-flow limits use the
  maximum over the stages; each iteration applies the same change to all stage versions and simulates every stage.
- The NPV by stage years: the yearly costs of a stage (energy, pumps, penalties) with the present-value factor of its
  years; investment, maintenance, replacements and residual value from the year an item first appears; pumps sized for
  stage 1 at year 0 and the increase bought when a later stage needs more.
- The same representative weeks for all stages, chosen on stage 1's climate (the opposite extreme week added when a
  stage cools); each stage simulates them with its own climate file, its weights and coverage from that climate.
- The dialog's choice "new child version" (default) or "override" applies to every stage; 'Set pipes' sets all stages.
- The report shows the stages, the NPV per stage and the terms with their years.

## Capabilities

### New Capabilities
- `network-stages`: the stage table and its checks, the coupled optimization over the stage versions, the NPV by stage
  years, the periods and climates per stage, the result versions and the report per stage.

### Modified Capabilities
<!-- The cost-optimization requirements are in the active change cost-optimization; its spec texts are adjusted there
     when this change is applied. -->

## Impact

- `cost_optimization.py` (stage table, run over the stages), `utility_functions/cost_model_data.py` /
  `cost_model.py` (one model per stage, ΔNPV summed), `network_economics.py` / `economics.py` (NPV by stage years,
  start years of items), `representative_periods.py` (weeks shared, weights per stage), `set_pipes.py`,
  `iteration_report.py`, translations, tests.
- Run time: every iteration simulates every stage (stages × weeks).
- Runs on QGIS 3.44 and 4.2; no new dependency, no change of the project DB schema.
