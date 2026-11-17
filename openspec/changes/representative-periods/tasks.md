## 1. Periods module

- [x] 1.1 `utility_functions/periods.py`: resolve the project's climate SOURCE-FILE (clim: → IDA Districts climate folder), read hour and T_air (the first 8760 of the hour points), message naming an unreadable file
- [x] 1.2 Dominant mode from the pair table / plants; anchor week (coldest or warmest), option fourth week (warmest) for combined networks; a tooltip says why the option is greyed out for networks that only heat or only cool
- [x] 1.3 Weights per simulated hour (hour of day, linear split between nearest below and above, nearest otherwise), profile sums, coverage (> 1 K) with warning above 40 %
- [x] 1.4 Coverage search: candidate weeks from every midnight, coordinate descent from the 50 % / 85 % quantile weeks, no overlap

## 2. Period run

- [x] 2.1 Class `PeriodRun` (QObject, signals as DynamicPipeSizingRun): delete `_period*` and periods.json, optional build (re-invoke only when asked), the weeks simulated in parallel in model copies `period_<k>` with their own dates, then per week copy the saved model with its results back, load, copy tables with suffix `_period<k>`; copies removed at the end
- [x] 2.2 Name the outputs the kept tables need if they are off; restore the version's simulation dates after the run; annual option without copies, weights 1
- [x] 2.3 Write `versions/<version>/periods.json` (run time, climate file, weeks with role, per simulated hour period/hour/weight, coverage, annual flag; profile sums at evaluation)

## 3. Periods widget

- [x] 3.1 PeriodsWidget (in the cost optimization dialog; the own dialog and its button were removed after the review in QGIS): matplotlib T_air diagram (backend_qtagg) with week bands and anchor, length, start-up, options, coverage; move a week by date field or click; enums through compat.py
- [x] 3.2 Weeks chosen in the thread pool; the annual option hides the week settings, the diagram and the coverage

## 4. Report

- [x] 4.1 Economics section of the network report: use periods.json and the `_period*` tables when the normal results do not cover a full year, weights and profile sums in economics.py, show weeks, coverage and run time

## 5. Tests

- [x] 5.1 Unit tests periods.py on BROMMA.PRN (skipped without IDA Districts): anchor coldest, weights sum 8760, linear split (5 °C between 4 and 8 °C → 0.75/0.25), proxies heat and cube within 2 %, coverage warning above 40 %, unreadable file message
- [x] 5.2 Unit tests dominant mode and fourth week; no overlap of weeks
- [x] 5.3 e2e/ida test on a project from `dynamic_optimization` (skipped without it): period run with three 1-day weeks and 1-day start-up, `_period1..3` tables, periods.json, simulation dates restored, second run leaves no tables of the first; report Economics from the periods
- [x] 5.4 Local validation: from districts/, the QGIS Python runs `-m pytest` and it passes (with `-m "not ida"` when IDA Districts is not installed), including test_static_mypy.py and test_messages.py

## 6. Translations, documentation, CI

- [x] 6.1 tr_msg / tr with German translations for the dialog, the warning and the messages; translations de/en compiled
- [x] 6.2 README.md and CLAUDE.md: the dialog, periods.py, PeriodRun, periods.json and the `_period<k>` tables
- [ ] 6.3 `npx openspec validate --all`, commit the artifacts with the code (explicit paths), `git pull --rebase`, push to dev and watch the plugin-tests run until both QGIS jobs pass
