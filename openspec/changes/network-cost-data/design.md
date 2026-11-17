## Context

Foundation change 2 of 4 for `cost-optimization` (decision record `openspec/changes/cost-optimization/design.md`,
D3, D4, D5, D7).

Today: `public.pipes` (project DB) has `costs` (NULL everywhere), `series`, `casing_construction_id`; the pipe
bundles (`pipe_bundle_types`, `bundle_pipes` with x, y and `ambient` → `pipe_ambient`: ambient_air, ground, duct)
give the geometry; `pipe_layers`/`materials` give the insulation. `"<version>".streets` has `costs_eur7m`
(default 100), used by the pipe laying. The ground model is in the version's `modellingSettings.txt`
(`ground_temp`, Kusuda parameters). Results: `line_s_qamb` (`QAmbtotal` per bundle, all pipes summed),
`line_s_temp$<seq>`, `energy_plant_s_*`, and the pump tables of change `pump-power-outputs`. The network report
(`reports.networkReport`, layout/PDF) has a pipe table with costs. `upgrade.py` adds project columns through
`ensure…` functions (`upgradeProjectDB`) and version columns in `upgradeVersionDB`.

Example values (research of 2026-11-16): KWW-Technikkatalog Wärmeplanung 08/2026, Tab 36 (KMR, single pipes,
2026 €, per trench metre and pair): material ≈ 23 + 3.05·DN, civil works min unpaved ≈ 120 + 5.5·DN, paved
≈ 155 + 9.4·DN; lifetime pipes 30–40 a (VDI 2067-1: 40), pumps 10–15 a; maintenance ≈ 1 %/a pipes, 2–3 %/a pumps
(unconfirmed); EN 13941 up to PN25, 120 °C; pump 100 €/kW (a modelling assumption); large air heat pump SPF 2.5 at
70 °C, 1.8 at 95 °C (KWW Tab 24/25).

QGIS 3.44 (Qt5) and 4.2 (Qt6): new widgets in the report dialog (checkbox, combo); enums through `compat.py`.

## Goals / Non-Goals

**Goals:**
- Cost and price data per project, in scenarios, with cited example values.
- The NPV and the losses per pipe as reusable modules for `cost-optimization`.
- An economic evaluation of a simulated version in the network report.

**Non-Goals:**
- Representative periods and weights (change `representative-periods`); here every hour has weight 1 and the
  results must cover a full year.
- Optimization; comparing versions side by side in a dialog.
- A per-pipe loss output of `FDpipebundle` (follow-up if the check of D6 shows large deviations).

## Decisions

**D1 – Pipe columns.** `pipes.costs` = material and laying €/m **per pipe** (example: half the KWW pair material,
DN175/225 interpolated); new `maintenance_pct` (example 1.0), `lifetime_a` (40), `p_max_bar` (16), `example`
(boolean, true for example rows). The cost of a bundle is the sum of its pipes.

**D2 – Scenarios.** Project tables (public schema):
- `economic_scenarios` (id, name, interest_pct, period_a, residual_value, default_surface, el_profile_file,
  pump_costs_eur7kw, pump_maintenance_pct, pump_lifetime_a, example, description);
- `price_groups` (scenario_id, cost_group ∈ electricity, heat, cold, maintenance, investment; start_price,
  escalation_pct) and `price_levels` (scenario_id, cost_group, year, factor) overriding the escalation for a year;
- `price_curves` (scenario_id, mode ∈ heat, cold, t_supply, price_eur7kwh): c(T) of year 0, interpolated linearly,
  constant outside, one row = constant;
- `trench_costs` (scenario_id, surface, a_eur7m, b_eur7m_dn): civil works per trench metre = a + b·DN of the largest
  pipe of the bundle.
Scenario "base" with example values. The tables are defined once in `utility_functions/economic_data.py` and
created by the upgrade at every version load (`CREATE TABLE IF NOT EXISTS`, "base" only into an empty table), so plugin
templates, complete dumps (IDA samples) and old projects take the same path. Heat and cold use the price curves; the
`start_price` of their groups is not used; maintenance and investment groups carry only the escalation (of
maintenance and replacements). Edited through the existing table dialogs (`show_TableDialog`, the scenario as a
combo column), opened from a dialog "Economic scenarios" (button € next to the pipe bundles) that also copies a
scenario and sets its profile. *Alternatives:* version files (NPVs of versions not comparable); one set per project (no
sensitivity study).

**D3 – Electricity profile.** The file (.csv or .prn: one value per hour, 8760 or 8784 rows) is copied into
`<project>\prices\` and referenced by name; read, normalized to mean 1; missing → flat. Price(t, h) = start_price ·
level(t) · shape(h), level(t) = factor of `price_levels` or (1 + escalation)^t. A preview diagram in the scenario
dialog is part of `cost-optimization` (shared with its NPV diagram).

**D4 – Surfaces.** `"<version>".streets` gets `surface text` (NULL = the scenario's `default_surface`, example
"paved"). A line's trench length per surface comes from its overlap with the streets (flat-ended buffer of 1 m, so an overlap
ends where the street ends; crossing streets are scaled to the line length); the rest has the default surface. `costs_eur7m` stays for the pipe laying.

**D5 – NPV module** (`utility_functions/economics.py`, pure Python). Input: per cost group yearly quantities (or
hourly with weights, priced per hour), investments with lifetime, maintenance %/a, the scenario. Cash flows per
year t = 1…period: energy × price(t), maintenance, replacements at multiples of the lifetime; residual value at the
end (linear, if set); discounted with the interest rate; annuity = NPV × annuity factor. Signed: a ground gain in
heating mode lowers the cost.

**D6 – Loss module** (`utility_functions/pipe_losses.py`). Q per pipe and hour = U'(d)·(T_pipe − T_amb)·L, U' per
pipe from its layers and the bundle (single-pipe resistance plus ground resistance from depth y, soil conductivity
of the modelling settings; duct and air with their ambient). T_pipe from `line_s_temp$<seq>`; T_amb: ground from
the version's ground model (constant or Kusuda), air from the climate file, duct from its setting. The mode of a
pipe follows its pair (pair table of the sizing; heat for a supply temperature above the ground). Check: Σ pipes
per line vs `QAmbtotal`; deviation above 15 % → listed per line in the report.

**D7 – Report.** Network report dialog: checkbox "Economics" and a scenario combo. Section: investment (pipes in use
× costs, trench per surface, pumps from the peak of `ppump_*` × €/kW), yearly pump energy and cost, heat and cold
losses (D6) priced with c(T_sup) per plant and hour, maintenance, NPV split and annuity, the scenario name, and
"example values in use" if a pipe in use or the scenario has `example`. It needs results covering a full year
(8760/8784 hours) with `ppump_*`, `temp_lines`, `temp_ep`, `qamb_lines`; otherwise the section names what is
missing. The pipe table shows the per-pipe costs.

**D8 – Upgrade.** `upgradeProjectDB`: `ensurePipeCostColumns` (new columns, `example` false, existing costs kept),
`ensureEconomicTables` (tables and scenario "base" with example values). `upgradeVersionDB`: `streets.surface`.
Existing pipes get no example costs automatically; the report warns about pipes in use without costs.
`pipe_bundle_types.invest_costs` and `operation_costs` were never read (costs are per pipe and per scenario): removed
from new projects and the templates, dropped by the upgrade, skipped when resources of older projects are imported.

**D9 – Samples of IDA Districts.** The four samples (`dynamic_optimization`, `hc_network`, `low_temperature_network`,
`secondary_network`) are full dumps in the IDA Districts installation, not in this repository: their `db_tables.sql`
get the pipe columns (series, casing, cost columns) and example values, handed over as files and copied into
IDA Districts. Steel pipes as `heating_network`, series 'Isoplus DRE Standard'. PE100-RC pipes (GEROtec Anergie of
`low_temperature_network`, d = outside diameter): material ≈ 1160·d² €/m (SDR 17, PE-TEC price list 2023: d110
14.25, d225 58.70, d315 114.40 €/m), SDR 11 with 1.5 times the wall ≈ 1740·d²; PN 16 (SDR 11) / PN 10 (SDR 17),
50 a, 1 %/a; one series 'GEROtec Anergie PE100-RC', so the optimization steps from SDR 11 to SDR 17 (d125 is
cheaper than d110, as in the price lists).

## Risks / Trade-offs

- [Example values far from local prices (factor ~2)] → cited sources, `example` flag, warning in the report.
- [Loss model ignores heat exchange between pipes of a 4-pipe bundle] → check against `QAmbtotal` per line (D6).
- [Full-year results needed] → the section says what is missing; change `representative-periods` removes the limit.
- [Lines not on streets or crossing several surfaces] → overlap per surface, default surface for the rest.
- [Pump €/kW is a single modelling assumption] → marked as example, part of the scenario.

## Open Questions

None.
