## Why

An annual simulation of a district network takes long, and the cost optimization (change `cost-optimization`, D13–D15)
needs a simulation for every check. Three representative weeks, extended to the year with the ambient air
temperature, give the yearly energy quantities at a fraction of the computing time; a proxy test on `BROMMA.PRN`
gave errors below 1 % for heat and pump energy when the coldest week is kept. The network report's "Economics"
section (change `network-cost-data`) needs full-year results until this exists.

## What Changes

- Automatic choice of three weeks from the version's climate file: the extreme week of the dominant mode (heating →
  coldest, cooling → warmest) fixed, the other two chosen for the best coverage of the year's air temperatures.
- Weights per simulated hour: every hour of the year is assigned to the simulated hour of the same hour of day
  with the most similar air temperature, in gaps interpolated between the two nearest; coverage = share
  of the year's hours without a simulated hour within 1 K.
- A dialog **Representative periods**: diagram of the year's air temperature with the weeks (movable), length and
  start-up (default 7 + 3 days), coverage, the option "annual simulation"; start runs build (option), and per week
  simulate, load and keep the results.
- The results of each week are kept as copies of the needed result tables (suffix `_period<k>`), the weeks,
  weights and coverage in `versions/<version>/periods.json`.
- The network report's "Economics" section uses the kept weeks and their weights when there are no full-year
  results.

## Capabilities

### New Capabilities
- `representative-periods`: choice of the weeks, weights and coverage, the dialog and the period run, the kept
  results.

### Modified Capabilities
<!-- network-economics (change network-cost-data, not yet archived): the Economics section accepts representative
     periods; specified here as an addition -->

## Impact

- New modules `utility_functions/periods.py` (choice, weights, coverage; numpy) and a run class `PeriodRun`
  (reused by `cost-optimization`), a new dialog with a matplotlib diagram (as in `utility_functions/plots.py`).
- Reads the climate `.prn` of the version (`climate-macro` → `SOURCE-FILE`, `clim:` = IDA Districts climate folder).
- `utility_functions/reports.py` (Economics section), `utility_functions/economics.py` (weights as input).
- Translations, unit tests on `BROMMA.PRN`, an e2e/ida test with short weeks.
- Depends on `network-cost-data` for the report part; no DB schema change of the project tables.
