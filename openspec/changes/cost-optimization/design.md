> Decision record of the explore session of 2026-11-16 (T1–T16, D1–D16) and of the proposal session (O1–O5, D17–D21).
> The foundation changes `pump-power-outputs`, `network-cost-data` and `representative-periods` are implemented.

## Context

The dynamic pipe sizing (`dynamic_pipe_sizing.py`, specs `pipe-pair-balancing`, `sizing-run-settings`,
`sizing-iteration-results`, `iteration-pipe-diameters`) sizes and balances each supply/return pair against
pressure targets (`dp_spez_setpoint`, `v_max`, tolerances) in a loop build → simulate → load → evaluate, with an
iteration file, table and map layers per iteration and a reference run as iteration 0.

This change replaces the pressure targets by costs over an amortization period: investment (pipes, the
diameter-dependent part of the trench, pumps), operation (pump electricity, heat/cold losses), maintenance and
replacements, validated by simulations.

What exists: `pipes.costs` (NULL in every template), `pipe_bundle_types.invest_costs/operation_costs` (unused),
`streets.costs_eur7m` (trench per street, used by the pipe laying), the pipe laying's
`heat_loss × heat_costs × amortization_period`, the outputs `qamb_lines`, `mdot_lines`, `temp_lines`, `p_*`,
`troom_c`, `power_c`/`power_ep` (thermal). Not measured: pump electricity (`PPUMP` of the IDA `PUMP`), room
setpoints, unmet load.

QGIS 3.44 (Qt5) and 4.2 (Qt6); the diagrams and dialogs must use `utility_functions/compat.py` for any Qt5/Qt6
difference. The DB schema changes belong to `network-cost-data` (upgrade through `upgrade.py`).

## Goals / Non-Goals

**Goals:**
- Pipe sizes with the least net present value over the amortization period, for central and decentral pumps.
- Hard pressure limit in the pipes; comfort and unmet load as penalties.
- Progress visible during the run, every decision traceable afterwards.

**Non-Goals:**
- Optimizing supply temperatures, plant or substation sizes, or the network layout (pipe laying).
- Counting the COP effect of the network temperature on customer heat pumps (`P_el_total` is reported only).
- A ground-temperature correction of the losses (later refinement of D14).
- Load growth over the period (the simulated year repeats).

## Decisions

**D1 – Method: cost model with checks (T1).** One check simulation provides per simulated hour the mass flows and
temperatures of every line, the pump powers and the customer pressures. A cost model evaluates any pipe choice
without simulating: Darcy pressure drops, pump head (D8), heat losses U(d)·ΔT·L (U from `pipe_layers`),
investment. A greedy step changes the line with the largest ΔNPV (larger or smaller pipe of its series) and
re-balances the pairs inside the model (implemented as: the head follows the largest path drop, so balancing is the
head adapting to the critical path). Then build → check simulation → recalibrate (η_eff, losses) and repeat
until the simulated NPV no longer falls. Start: the balanced result of the dynamic sizing.
*Alternatives:* a sweep of one global pressure gradient (uniform R for all lines); a simulation per changed pipe
(hundreds of simulations).

**D2 – Limits (T2).** p_max of every pipe (`pipes.p_max_bar`) is hard: the model rejects a step that exceeds it in
any hour, a check that exceeds it rejects the iteration. The guard against starving a customer is implemented as limits of a smaller pipe at the line's
peak flow (300 Pa/m, 3 m/s, as the sizing): the model covers a longer path with a higher head. Room temperature outside the setpoints (load models) and
unmet required load (source-file customers) are penalties (D9). A guard in the model: no smaller pipe that lowers a
customer's available pressure difference below its need at its critical hour.

**D3 – Cost data (T3, change `network-cost-data`).** `pipes.costs` = material and laying €/m per pipe; civil works
from trench cost curves per surface class in the scenario (a + b·DN of the bundle's largest pipe, e.g. unpaved
120 + 5.5·DN, paved 155 + 9.4·DN €/m, KWW 2026), the surface of a line from the street it lies on; new `pipes.maintenance_pct` (%/a of invest), `lifetime_a`, `p_max_bar`. Pump costs (€/kW of peak
pump power, %/a, lifetime) and all economic and price settings (D4, D5, D7) are project DB tables with named
scenarios (default "base"); a run and the NPV report name the scenario they used (change `network-cost-data`). `streets.costs_eur7m` (location-dependent,
not diameter-dependent) is reported only: it does not change a decision. Default values per DN in all templates.
*Alternatives:* a separate cost catalog table; costs per `pipe_bundle_types` (the optimizer creates bundles).

**D4 – Economics (T4).** Yearly cash flows discounted to an NPV, also shown as annuity: interest rate, period,
price per year per cost group (escalation rate or table), replacements at the end of `lifetime_a`, residual value
at the end of the period (option). VDI 2067's annuity is the special case with constant rates. The greedy step
measures ΔNPV.

**D5 – Electricity price (T5).** price(year t, hour h) = level(t) × shape(h): level from a table per year or start
price + escalation; shape from an optional hourly profile file (.csv/.prn, 8760 values, normalized to mean 1),
flat if missing. Preview diagram in the dialog (profile and levels).

**D6 – Pump power (T6, change `pump-power-outputs`).** New requested outputs `ppump_ep`/`ppump_c`: the power
variable of every network pump (D8), hourly, in result tables like `power_ep`. The model calibrates η_eff per
pump from them; the NPV counts only network pumps. The optimizer switches its outputs on itself.

**D7 – Heat/cold losses (T7).** Price table c(T_supply) per mode (heat, cold), interpolated linearly with the
simulated supply temperature of the plant each hour, times the level per year (D5 structure); one row = constant.
`qamb` is counted signed: a ground gain is a benefit in heating mode, a load in cooling mode.

**D8 – Network pumps (T8, change `pump-power-outputs`).** Detected automatically from the IDA templates: a pump
in the flow path between the network connections of a plant or customer without a heat exchanger in between.
The dialog lists all found entries (template, component, power variable; default `PPUMP`) with add and remove,
including components that contain a pump (added by hand as "estimate": V̇·Δp/η from the connection results); in the
low-temperature sample the decentral `PUMP`/`PUMP1` of the heat pump customer are found as network pumps. Saved with the project, next to its templates (change `pump-power-outputs`). Head in the model: central pumps over the critical path per hour (max over
customers of path Δp + Δp_sub,min); decentral pumps over the customer's own path, direction from the signed
hourly mass flows (bidirectional networks).

**D9 – Penalties (T9).** Degree hours count only when heating or cooling is needed and not reached: per hour,
heating mode (`HCMode` 1) max(0, TSet − tol − TRoom), cooling mode (−1) max(0, TRoom − TSet − tol), otherwise 0; a
room temperature between the heating and the cooling setpoint counts nothing. Linear, relative to the reference run
per customer: €/Kh × max(0, Kh − Kh_ref), €/kWh × max(0, kWh_unmet − kWh_unmet,ref). The deviations that exist anyway are their own KPI.
Required load of source-file customers from their source file, supplied load from `power_c`; setpoints as a new
output. A new penalty in a check blocks further reductions of the lines made smaller in the last step (approximating "that
customer's path").

**D10 – Tracking (T10).** The iteration machinery of the sizing: a row per check with NPV split (invest, pump
energy, losses, maintenance, penalties), model NPV vs simulated NPV, lines larger/smaller; map layers per
iteration. Plus a step trace in the iteration file (line, pipe before → after, ΔNPV and split, the limit or guard
that applied), written while the model runs, and an NPV diagram in the dialog (stacked by cost group, model
prediction as a line), updated after each check. Earlier iteration files stay readable.

**D11 – Tests (T11).** Unit tests without DB/IDA (NPV, prices, c(T), signed losses, penalties, head models, greedy
step with limits and guard, pump detection on the `.idm` files, weights and period choice); e2e (`ida`) on a
project from `dynamic_optimization` with short periods; `simulation_tests` (only when named): annual optimization
of `base1` and of the low-temperature version, and NPV of the periods vs the annual NPV.

**D12 – Test project (T12).** The IDA Districts sample `dynamic_optimization` is extended in IDA Districts itself
with the customer template (`4_simplified_consumer_hp`) and the plant templates of `low_temperature_network` and a
new version using them; no copy in the plugin. Tests skip until it is installed (the skip checks the version and
its templates). Handover list for the sample: templates, version, low-temperature plant setpoints, pumps.

**D13 – Simulation periods (T13, change `representative-periods`).** Every check simulates three representative
periods (winter, summer, transition); option: one annual simulation.

**D14 – Filling the year (T14).** Weights per simulated hour: every year hour is assigned to the simulated hour with
the most similar T_amb (climate file) of the same hour of day (the weekday/weekend class was dropped in
`representative-periods`: it doubled the error of pump energy); in gaps linearly
between the two nearest. The weight carries the sum of the prices of its hours. The cost model works on the
simulated hours only. Coverage warning: the share of the year only interpolated. Annual option: all weights 1.
*Alternative:* regression curves per total (loses the per-line states the greedy step changes).

**D15 – Choice of the periods (T15).** The extreme week of the dominant mode is fixed (heating → coldest,
cooling → warmest); the other two weeks are chosen to maximize coverage. Shown in a T_amb diagram, movable; length
and start-up settable (default 7 + 3 days). Proxy test on `BROMMA.PRN` (8760 h, heat ~ max(0, 15 − T_amb),
pump ~ heat³):

| choice | hours > 1 K off | mean \|ΔT\| | heat error | pump error |
|---|---|---|---|---|
| coldest / mean / warmest | 49 % | 1.8 K | +3.3 % | −0.1 % |
| all three for coverage | 28 % | 1.0 K | −2.0 % | −12.2 % (misses the cold tail) |
| coldest fixed + two for coverage | 39 % | 1.2 K | +0.7 % | −0.3 % |

**D16 – Scope (T16).** Four changes: `pump-power-outputs` (D6, D8, setpoint output of D9), `network-cost-data` (D3,
D4, D5, D7), `representative-periods` (D13–D15), and this change (D1, D2, D9, D10, D11, D12) built on the three.

**D17 – Trust region (O1).** In each iteration the model evaluates, for every line, the next larger and the next
smaller pipe of its series (both pipes of the pair in the bundle) and its ΔNPV: investment and maintenance of pipe and
trench (`network_economics`), pump energy (head of D8 with the new pipe, Δp × V̇ / η_eff per pump, η_eff calibrated
from the kept `ppump` results), heat/cold losses (U′ of `pipe_losses`), all valued with the weights of the periods.
Every line with a negative ΔNPV gets its best one-size change; then the pairs are balanced in the model and the
limits of D2 checked (p_max, the guard against starving a customer). One check (`PeriodRun`) per iteration. The
model error (model NPV against simulated NPV) is saved per iteration.
*Alternatives:* no limit (large jumps, unclear causes); an adaptive step (later, if iterations are the bottleneck).

**D18 – Dialog "Cost optimization" (O2).** Its own dialog and run (`cost_optimization.py`), the model pure Python
(`utility_functions/cost_model.py`). Settings: scenario, pair table (suggested by `suggestPairs`, as in the sizing),
periods (the shared periods widget of `representative-periods`: diagram with the movable weeks, coverage, or the
annual option, which hides them; every check simulates exactly the weeks shown), penalty prices (€/Kh with tolerance band, €/kWh unmet), max.
iterations, version (new child version or override). Results: iteration table (NPV split, model vs simulation, lines
larger/smaller, best iteration marked), NPV diagram (stacked by cost group, model prediction as a line), map layers
of the changed lines. The sizing's machinery is reused as functions, not its dialog.
*Alternative:* a mode of the dynamic pipe sizing dialog (collides with its parameters and the `protect-lines` work).

**D19 – Start (O3).** The pipes of the loaded version. Iteration 0 is the reference check: the periods simulated
with the current pipes, the NPV, and per customer Kh and unmet kWh as reference of the penalties (D9). The dialog
hints at the dynamic pipe sizing when the version has no sizing iterations.
*Alternatives:* the sizing as stage 1 (couples two runs and their settings); pre-sizing in the model (the penalty
reference would be a network the user never had).

**D20 – Required load of source-file customers (O4).** A list per template saved in the project
(`requiredLoads.json`): template, column of the source file, unit (W/kW), sign (heating/cooling); templates with a
`SOURCE-FILE` are detected, default column 2. The plugin reads the customer's source file (`invoked_sf`, sf-macro),
interpolates it linearly to the result time steps with the file's hour column, and counts unmet load per hour as
max(0, required − supplied `power_c`) above a tolerance of 2 % of the required load. The penalty is relative to the
reference (D9), so a systematic offset between the plugin's and IDA's reading cancels.
*Alternative:* a simulation output of the required load per template (exact time base, more machinery).

**D21 – Versions and end (O5).** A new child version (default) or the loaded version. Each iteration writes its pipes
into it. The run ends when the simulated NPV has not improved for 2 iterations, the state repeats (oscillation), no
step improves the model NPV, or the max. iterations are reached. Then the pipes of the iteration with the best
simulated NPV are restored and, if that was not the last iteration, checked once more, so that pipes and results of
the version match. Protected lines of `protect-lines` (if present) are never changed.

## Risks / Trade-offs

- [The model assumes the hourly mass flows stay about the same when pipes change; less true when ΔT changes] →
  every iteration is checked by simulation, the model error is shown (D10), η_eff and losses recalibrated.
- [Greedy steps can circle] → oscillation detection as in the sizing; stop at the best simulated NPV (D21).
- [False unmet load from reading the source file differently than IDA] → tolerance 2 %, penalty relative to the
  reference (D20).
- [The model and the check disagree strongly] → one size per iteration (D17), the model error shown per iteration.
- [Automatic pump detection classifies wrongly] → the list is shown and editable (D8).
- [Representative periods bias the NPV] → D15 anchor, coverage warning, annual option, comparison in
  `simulation_tests`.
- [The low-temperature tests depend on an IDA release] → they skip; unit tests cover D8 on the installed
  `low_temperature_network` sample meanwhile.

## Open Questions

None.
