## Context

Foundation change 3 of 4 for `cost-optimization` (decision record `openspec/changes/cost-optimization/design.md`,
D13–D15).

A simulation covers one start-up and one calculation period (`networkSimData.txt` of the version: dates,
`calc_type`, `numb_of_periods` – the number of repetitions of a periodic start-up, not several date windows), so
three weeks are three simulations. Loading results replaces the version's result tables. The sizing run
(`DynamicPipeSizingRun`) shows how a sequence build → simulate → load is driven: the dates are set on a hidden
`RunNetworkModelDialog` before `runModel`, which saves them with the version. The climate of a version is a
`SOURCE-FILE` in `climate-macro.idm` (e.g. `clim:BROMMA.PRN`, columns hour, T_air, …, 8760 rows). matplotlib 3.11
and numpy are in QGIS 3.44 and 4.2; `utility_functions/plots.py` already uses them. Qt5/Qt6: the canvas is
matplotlib's Qt backend (`backend_qtagg`, which supports both); dialog enums through `compat.py`.

Proxy test (explore session, `BROMMA.PRN`, heat ~ max(0, 15 − T), pump ~ heat³): coldest + two coverage weeks gave
heat +0.7 %, pump −0.3 %; three coverage weeks −2.0 % / −12.2 % (cold tail missed); coldest/mean/warmest +3.3 % /
−0.1 % with 49 % of the hours more than 1 K off.

## Goals / Non-Goals

**Goals:**
- Yearly quantities from three weekly simulations, with known coverage.
- A run that keeps the results of every week, reusable by `cost-optimization`.
- The Economics section of the network report without an annual simulation.

**Non-Goals:**
- A ground-temperature correction of the losses; load growth; holidays as a day class.
- Changing the simulation dialog or the result loading.

## Decisions

**D1 – Climate reading.** `periods.py` resolves the version's climate `SOURCE-FILE` (`clim:` → the IDA Districts
climate folder, otherwise relative to the project) and reads hour and T_air (8760 values; 8784 accepted, day 366
dropped). A file it cannot read stops with a message naming it.

**D2 – Week choice.** The climate file is the loaded version's (table climate; versions of a project can have
different climate files, the project's climate-macro.idm holds only the one built last). Candidate weeks start at midnight of every day. Dominant mode: heating if a pair of the
version is a heating pair (supply above return temperature in the pair table, or the plants' modes), cooling if
only cooling pairs; combined networks: heating, with the option "add the warmest week" (four weeks). The option is
available for every network, as a low-temperature network heats and cools through one pair; a cooling network gets
"add the coldest week" instead (the opposite extreme of its anchor). Anchor = the
week with the lowest (heating) or highest (cooling) mean T_air. The other weeks are chosen by coordinate descent
over the candidates (start: the weeks closest to the 50 % and 85 % quantiles of T_air) minimizing the mean |ΔT| of
D3; a few seconds with numpy. The weeks must not overlap.

**D3 – Weights.** For every hour h of the year: the candidates are the simulated hours of the same hour of day (no
weekday/weekend class: on `BROMMA.PRN` it halved the candidates per class and raised the error of pump ~ load³ from
2.0 % to 4.4 %, with 38 % instead of 20 % of the hours more than 1 K away; decided during the implementation). If simulated hours below and above T_air(h) exist, h is split between the nearest
below and above, linearly by temperature; otherwise it goes to the nearest. Weight w_i = sum of the shares of hour
i; Σ w = 8760. For each simulated hour the module also keeps Σ share × shape(h) of the electricity profile (change
`network-cost-data`), so hourly prices are carried. Coverage = share of year hours whose nearest simulated hour is
more than 1 K away; a warning above 40 % (the recommended choice on `BROMMA.PRN` has 39 %, three extreme weeks 49 %).
*Alternative:* nearest only (coarser); regression curves per quantity (loses per-line states).

**D4 – Periods widget (first a dialog "Representative periods"; after the review in QGIS the dialog and its
button were removed, the widget lives in the dialog of the cost optimization).** The periods part is a widget (`PeriodsWidget`) shared with the dialog of
the cost optimization; with "annual simulation" it hides the week length, the warmest week, the diagram, the weeks and
the coverage (the start-up stays, it applies to the year too). Menu entry next to the simulation. Shows the year's T_air (matplotlib),
the weeks as bands (anchor marked), length (default 7 days), start-up (default 3 days, before each week),
"add the warmest week", "annual simulation", coverage and its warning; a week is moved by a date field or by
clicking the diagram. Start, Stop, log and progress as in the sizing dialog; "build the network model first" as
option.

**D5 – Period run.** Class `PeriodRun` (QObject, signals as `DynamicPipeSizingRun`): optional build (the customers
and plants invoked again only when the caller asks, e.g. the first check of the cost optimization); the weeks are
simulated in parallel, each in its own copy of the network model (`versions/<version>/period_<k>/network_<sub>.idm`
and its folder, no absolute paths inside) with the week's start-up and calculation dates in its SIMULATION_DATA and
its own process (`simulate_process.py`, own TEMP folder: idaapi2.dll holds one IDA connection per process, so
threads in the QGIS process would switch each other's connection), one after another: the next week starts when
the solver of the previous one runs (line `Service subscriber connected` in `tmp/ida_log_*.txt` of the week,
undocumented like the broker log), when that week has ended, or after at most 120 s. IDA sessions starting at the
same moment fail with a session lock or a solver without its modules ("Unknown module type", seen at 0.3 s apart);
a fixed gap between the process starts does not prevent it, the start of a week's process (QGIS in the child) varies
by several seconds. The next week also needs free memory: free commit (RAM + page file, `GlobalMemoryStatusEx`)
at least one week's need + 1 GB for QGIS and the others, unless no week runs. A week (IDA + solver) commits about
3.4 GB, mostly a fixed solver block ("Requested by Solver 1634 MB", "used effectively" 50 MB) that low_temperature_network
and dynamic_optimization share, so three weeks do not fit an 8 GB PC (`SUPERLU_MALLOC fails`). The solver commits it
at once, before its start line is written: the drop of the free commit from the start of a week to its solver line is
taken × 1.1 as the need of the next one (3.5 GB before the first measurement). Free commit, not free RAM: the solver
touches little of its block, RAM would serialise also where the weeks fit. A week that failed is simulated again
after the others, the failed weeks one at a time; a second failure fails the run. A week whose IDA ended without answering fails instead of hanging: the answer polling in
`util.py` stops when the IDA process has ended, and a watchdog in `simulate_process.py` ends the process 60 s after
IDA ended if the call into idaapi2.dll has not returned; a failed week names the last lines of the solver output
(`SCREEN.TXT`). An IDA that hangs at its start stays alive without an answer (CI, 2026-11-18: an IDA started in
the user's QGIS 23 s before a week's IDA; the week's IDA wrote no log for 39 min): a week whose solver has not
started after 600 s is stopped with its process tree (`taskkill /T`) and fails, so the retry above simulates it again.
When all are done, week by week the model as IDA saved it (results and the rewritten macros the loading parses) is copied
back into the version's model folder, loaded, and the tables of D6 copied with suffix `_period<k>` (loading stays sequential: it writes the same
result tables); the copies are removed at the end. A failed week fails the run after all have finished; the outputs the evaluation needs (pump power, line and plant temperatures, line
losses) are named in the log if they are off – switching outputs rewrites the project's templates, which stays the
requested outputs dialog's job; then write `periods.json`. Before the first
week the old `_period*` tables and `periods.json` are deleted. After the run the version's dates are set back to
those before the run. Annual option: one simulation of the whole year, no copies, weights 1. `cost-optimization`
reuses the class for its checks.

**D6 – Kept results.** Copies (`CREATE TABLE … AS SELECT`) in the version schema of: `line_s_temp$*`,
`line_s_mdot$*`, `line_s_p$*`, `line_s_qamb`, `energy_plant_s_*` (temp, mdot, p, ppump), `customer_s_ppump`,
`customer_s_troom`, `customer_s_power$*`, if present. `periods.json`: run time, climate file, year, weeks (start, end,
start-up, role), the kept tables, per simulated hour (period, hour of the year, weight), coverage, annual flag. The
price-shape sums depend on the scenario's profile, so the evaluation calculates them from the climate file.

**D7 – Report.** The Economics section (change `network-cost-data`) uses `periods.json` and the `_period*` tables
when the normal results do not cover a full year, prices every simulated hour with its weight, and shows the weeks,
the coverage and the run time. With neither, it names what is missing.

## Risks / Trade-offs

- [Weeks do not represent the year (solar, hot water, inertia)] → coverage and warning; the annual option; the
  comparison periods vs annual in `simulation_tests` (`cost-optimization` D11).
- [Copies from an earlier pipe state are mixed in] → deleted at the start of a run; the run time is shown.
- [Start-up of 3 days too short for heavy buildings] → settable; the default can be raised after the comparison.
- [Climate file not found (`clim:` path)] → message naming the file; no run.

## Open Questions

None.
