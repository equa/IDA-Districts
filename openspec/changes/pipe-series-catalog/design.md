## Context

The pipe catalogue of a project lives in its schema `public`: `pipes` (inner diameter, roughness, construction,
costs, `series`, `casing_construction_id`; from the open change `network-cost-data` also `maintenance_pct`,
`lifetime_a`, `p_max_bar`, `example`), `pipe_constructions` + `pipe_layers` (layers from the axis outwards, each
with a material) and `materials` (thermal values; since 52e8d5c also Young's modulus, thermal expansion, yield
strength, Poisson's ratio). `pipes.series` is free text; the pipe sizing (`hydraulic_balancing.getPipeCatalog`)
chooses among the pipes of a series, or of the same construction without a series. A twin pipe is two pipes of one
bundle with the same `casing_construction_id` (casing layers: foam body, casing wall); `twin_pipe.py` converts it
for the simulation, `pipe_resistances.py` computes its resistance matrix.

The templates `heating_network` and `db_default_values` hold the isoplus rigid catalogue (chapter 2: DRE single
pipes, DRD twins, series "Isoplus DRE Standard" / "Isoplus DRD Standard"). Flexible pipes do not exist in any
template. Source of the new catalogue: isoplus planning manual chapter 3 "Flexible Verbundsysteme" (as of
2015-03-25 / 2016-12-30), provided by the user; the PDF is not committed (copy only with isoplus' permission), the
rows cite it.

The project DB is upgraded by `upgrade.upgradeProjectDB` at every version load (`ensure…` functions, columns added
by `db.addMissingColumns` in one ALTER TABLE because of the event trigger `restrict_column_alterations`).

Runs on QGIS 3.44 (Qt5) and 4.2 (Qt6). The new dialog uses the existing table dialog (`show_TableDialog`); any Qt
enum it needs goes through `utility_functions/compat.py`.

## Goals / Non-Goals

**Goals:**
- Product data per series that the statics changes need: system type, limits, pressure ratings over time and
  temperature; minimum bend radius per pipe.
- The isoplus flexible catalogue in the templates, usable at once for simulation and sizing.
- Existing projects keep working and get the new tables on the next version load.

**Non-Goals:**
- Any statics calculation (follow-up changes, see roadmap).
- The pipe sizing using the new limits (e.g. no PE-Xa above 80 °C); it keeps choosing within `pipes.series`.
- Flexible pipes in the IDA sample `low_temperature_network` (outside this repository).
- Fittings and moulded parts of chapter 3.7.

## Decisions

**D1 – `pipe_series` keyed by the existing series text.** `pipe_series (id serial, name text UNIQUE, system_type
text, standard text, t_max_continuous_c, t_max_peak_c, t_min_c, sigma_ax_max_n7mm2, safety_factor numeric,
description text)`. `pipes.series` stays a text column without foreign key, so the sizing and the resource import
are unchanged; a series name without a row means "no product data". *Alternatives:* `pipes.series_id` (breaks the
sizing and every existing export); limits as columns on `pipes` (the catalogue gives them per product line, ~25
copies per series).

**D2 – System types** (text, checked by a CHECK constraint): `rigid_single`, `rigid_twin`, `bare_plastic`,
`flexible_plastic`, `flexible_metal`. They pick the statics path of the follow-up changes. Empty = unknown.

**D3 – `pipe_series_pressure_ratings (id serial, series_id integer REFERENCES pipe_series ON DELETE CASCADE,
years numeric, temperature_c numeric, pressure_bar numeric)`.** One row per cell of the catalogue tables (operating
time × continuous temperature → allowed pressure, water, with the catalogue's safety factor). The curve follows a
renamed series because it references the id.

**D4 – `pipes.min_bend_radius_m`** (numeric, NULL for rigid pipes and the 12 m bars). Added by
`addMissingColumns`.

**D5 – One series per catalogue variant, unique inner diameters within a series.** The sizing takes the next
smaller inner diameter of the series, so two pipes with the same diameter in one series would be ambiguous. Series:

| Series | Type | Standard | Pipes | T cont./peak | Limit |
|---|---|---|---|---|---|
| isoplus isoflex | flexible_metal | EN 15632-4 | 20, 28 | 120/140 °C | 25 bar, σ_ax 150 |
| isoplus isoflex v | flexible_metal | EN 15632-4 | 28 v | 120/140 °C | 25 bar, σ_ax 150 |
| isoplus isoflex twin | flexible_metal | EN 15632-4 | 28+28 | 120/140 °C | 25 bar, σ_ax 150 |
| isoplus isocu | flexible_metal | EN 15632-4 | 22, 28 | 120/140 °C | 25 bar, σ_ax 110 |
| isoplus isocu twin | flexible_metal | EN 15632-4 | 22+22, 28+28 | 120/140 °C | 25 bar, σ_ax 110 |
| isoplus isopex H | flexible_plastic | EN 15632-2 | H-25 … H-140, H-110 | 80/95 °C | 6 bar, ratings H |
| isoplus isopex H u | flexible_plastic | EN 15632-2 | H-110 u | 80/95 °C | 6 bar, ratings H |
| isoplus isopex H v | flexible_plastic | EN 15632-2 | H-25 v … H-125 v | 80/95 °C | 6 bar, ratings H |
| isoplus isopex H bar | flexible_plastic | EN 15632-2 | H-125/140/160 Stg. (12 m bars, no bend radius) | 80/95 °C | 6 bar, ratings H |
| isoplus isopex H twin | flexible_plastic | EN 15632-2 | H-20+20 … H-75+75 | 80/95 °C | 6 bar, ratings H |
| isoplus isopex H twin v | flexible_plastic | EN 15632-2 | H-20+20 v … H-63+63 v | 80/95 °C | 6 bar, ratings H |
| isoplus isopex S | flexible_plastic | EN 15632-2 | S-25 … S-63 | 80/95 °C | 10 bar, ratings S |
| isoplus isopex S twin | flexible_plastic | EN 15632-2 | S-25+20 … S-63+32 (unequal) | 80/95 °C | 10 bar, ratings S |
| isoplus isoclima | flexible_plastic | EN 12201-2 | 20 … 110 | 40 °C, min −40 °C | 11.6 bar (50 a, 40 °C), ratings PE 100 |
| isoplus isoclima u | flexible_plastic | EN 12201-2 | 110 u | 40 °C, min −40 °C | as isoclima |

isowell is left out (no longer available). Safety factor 1.25 (DIN 16893 / "c = 1.25") for isopex and isoclima.
The pressure in the column "Limit" is not a series column but the `p_max_bar` of each pipe of the series (D12).

**D12 – Pressure limit on the pipe.** `pipes.p_max_bar` (from `network-cost-data`, hard limit of the cost
optimization) is the only maximum pressure; `pipe_series` has none. Every flexible pipe gets its catalogue value
(isopex H 6, isopex S 10, isoflex/isocu 25, isoclima 11.6 bar). For plastic pipes the pressure ratings (D3) carry
the temperature- and time-dependent limit; `p_max_bar` is their cap. *Alternatives:* series value with a per-pipe
override (two places that can disagree, `cost-optimization` would have to change its reading); both independently
(two maximum pressures with different meanings).

**D6 – Layers of a flexible pipe.** Carrier pipe: inner diameter `da − 2s`, wall `s` of the carrier material.
Casing wall: assumed `e = max(2 mm, 0.02·Da)` (PE-LLD, λ 0.33); the catalogue gives no casing wall and the
EN 15632-1 table is not at hand. The wall has little effect on u (1 mm shifts u by about 1–2 %) and none on the
statics of flexible pipes, which use `Da`; the u check of D7 (±5 %) guards it. *Alternatives:* the EN 15632-1
minimum (not available); the wall fitted to u (badly conditioned: 1 % in u moves the wall by about 1 mm and hides
errors of λ or the ground model). Foam: the
rest, `(Da − da)/2 − casing wall`, PUR λ50 0.0221 (a material of its own; the rigid foam stays at 0.027). One
construction per pipe, as for DRE. Twins: the carrier pipe is the construction of each pipe, the casing (foam body
radius, casing wall) is the `casing_construction_id`, one pipe bundle per twin, as for DRD.

**D7 – Twin distance fitted to u.** The catalogue gives no distance between the carrier pipes of a twin. It is
fitted (one parameter, symmetric about the casing axis, carriers side by side) so that `pipe_resistances.py`
reproduces the catalogue's u under the catalogue's conditions: cover 0.80 m, λ ground 1.0 W/(m·K), ground 10 °C.
Single pipes are not fitted; their computed u is checked against the catalogue (two single pipes at 100 mm
distance, as the catalogue assumes) with a tolerance of ±5 %; twins must meet their u after the fit. Assumed and
fitted values are named in the pipe description ("casing wall assumed, twin distance fitted to u").

**D8 – Materials.** New rows: P195GH (E 211800, Re 195, α 11.3e-6, λ 55.2, cp 430, ρ 7850), Cu-DHP (E 132000,
Re 65, α 16.8e-6, λ 305, cp 386, ρ 8940), PE-Xa (E 600, Re 17, α 1.5e-4, λ 0.38, cp 2300, ρ 938), PE 100 (E 1000,
Re 23, α 1.8e-4, λ 0.40, cp 2350, ρ 960), PE-LLD casing (λ 0.33), PUR flexible (λ 0.0221). Values at 20 °C from
the catalogue; Poisson's ratio stays empty where the catalogue does not give it.

**D9 – Rigid series.** "Isoplus DRE Standard" → `rigid_single`, standard EN 253; "Isoplus DRD Standard" →
`rigid_twin`, standard EN 15698-1. Temperatures as EN 253 sets them for bonded pipes: 120 °C continuous, 140 °C
peak; the description names EN 253 as source (to be checked against the standard or catalogue chapter 2). The
allowed axial stress stays empty: for rigid pipes it is no product value but follows under EN 13941 from Re of the
steel (`materials`) and the design class, computed by `statics-steel-solver`. `p_max_bar` of the pipes is left as
`network-cost-data` sets it. *Alternatives:* limits from catalogue chapter 2 (not at hand); limits left empty
(empty dialog for the only existing series).

**D10 – Upgrade.** `upgradeProjectDB` gets `ensurePipeSeriesTables`: `CREATE TABLE IF NOT EXISTS` for both tables,
`addMissingColumns(pipes, min_bend_radius_m)`, then `INSERT INTO pipe_series (name) SELECT DISTINCT series FROM
pipes WHERE series IS NOT NULL AND NOT EXISTS (…)`: every existing series gets a row with empty system type. No
existing pipe is changed. The catalogue rows reach existing projects only through the resource import, as before.

**D11 – Dialogs and resources.** A table dialog "Pipe series" (columns of D1, system type as dropdown) with the
pressure ratings of the selected series below; the pipes dialog gains the bend radius. The resource export writes
the series of the exported pipes with their ratings; the import creates a missing series by name and keeps an
existing one.

**D13 – No costs for flexible pipes.** Flexible pipes get `costs`, `maintenance_pct`, `lifetime_a` empty, the
manufacturer `p_max_bar` and `example` false: there is no solid public cost source for them, and the single
`example` flag of `network-cost-data` would otherwise mark the manufacturer pressure as an example. The
requirement "Example values in the templates" of `network-cost-data` is narrowed to the rigid series (edited in
that change's spec); the network report already warns about pipes in use without costs. *Alternatives:* example
costs from a public source (uncertain source, ambiguous flag); costs of the rigid pipe of the nearest diameter
(wrong data).

## Risks / Trade-offs

- [The catalogue is from 2015/2016; current isoplus data may differ] → the source and date are in every series
  description; a newer catalogue replaces rows without schema change.
- [Casing wall assumed, without source] → u is checked per type (D7, ±5 %); the casing wall has little effect on
  u (thin PE layer, λ 0.33) and none on the statics of flexible pipes, which use `Da` only; the EN 15632-1 values
  replace the assumption later without schema change.
- [Twin fit has no solution, e.g. u unreachable within the casing] → the test fails for that type; it is then left
  out and named in the design, not forced.
- [Unequal twins (S-50+32) in `twin_pipe.py`] → the conversion handles pipes of different radii per pipe; a test
  covers one unequal twin in the network model.
- [Overlapping edits with `network-cost-data` in the templates and `upgrade.py`] → implement after its template
  rows are committed; this change adds rows and one `ensure…` call only.

## Migration Plan

Tables and column are created on the next version load (D10), in the materials/pipes dialogs and before a resource
import, like the columns of 52e8d5c. Rollback: the new tables and the column are ignored by older plugin versions.

## Open Questions

1. ~~Source of the pressure limit~~ → `pipes.p_max_bar` (D12).
2. ~~Limits of the rigid series~~ → EN 253 temperatures, no axial stress (D9).
3. ~~Casing wall thickness~~ → assumed max(2 mm, 0.02·Da), guarded by the u check (D6, D7).
4. ~~Costs of the flexible pipes~~ → none, requirement of `network-cost-data` narrowed (D13).

No question is open.

## Pipe statics roadmap

Decisions of the explore session of 2026-11-16 (T1–T12) for the pipe statics, carried by this change for the
follow-up changes:

- T1 Full pipe stress verification under EN 13941 / AGFW FW 401, comparable to sisKMR (not a pre-statics only).
- T2 Pipe dimensions from `pipe_constructions` + `pipe_layers`; no dimension columns on `pipes`.
- T3 Mechanical properties in `materials` (done in 52e8d5c); per-DN catalogue in the plugin templates.
- T4 → T6 Soil values and laying temperature are dialog defaults, overridden per section.
- T5 Own solver in the plugin (Python, numpy/scipy): 3D pipe elements on non-linear soil springs (friction
  sticking/sliding, lateral bedding, expansion pads), load steps laying → heat-up → cycles → cooling; no export to
  sisKMR/ROHR2.
- T6 Statics model generated automatically: bends from the vertices by rule (prefabricated bend with catalogue
  radius, elastic bend, small-angle bend), cover from `bundle_pipes.y` minus casing radius, compensation-free
  laying without fixed points, expansion pads placed by the solver as a result; layers `statics_points` (fixed
  point, compensator, one-time compensator, valve, bend) and `statics_sections` (soil, cover, traffic, groundwater,
  pads) only override.
- T7 Load cases: stress checks with the higher of design value and simulated maximum per line; fatigue from
  rainflow counting of the simulated temperatures (`temp_lines`), scaled to the service life, else the standard
  spectrum of the line class; the source is reported per line. Plastic pipes: Miner's rule over temperature
  classes (ISO 13760) from the simulation.
- T8 Scope: rigid single, rigid twin, bare plastic pressure pipes (buried-pipe check ATV-DVWK-A 127 / DWA-A 127 and
  pressure rating from MRS/SDR/temperature), flexible pipes (bend radius, pressure/temperature, EN 15632).
- T9 Flexible catalogue: isoplus chapter 3 (this change).
- T10 Casing wall assumed (max(2 mm, 0.02·Da), instead of the EN 15632-1 minimum, which is not at hand), twin
  distance fitted to u (this change).
- T11 Product data in `pipe_series` + ratings, bend radius on `pipes` (this change).
- T12 Five changes: `pipe-series-catalog` → `statics-model` → `statics-steel-solver` ∥ `statics-plastic-flexible`
  → `statics-results`.

Open for the follow-up changes:
- `statics-model`: bend rules and their defaults (angle thresholds, radius per DN); overrides that survive a
  regeneration of the topology (tied to the route geometry, not to line ids); map of the generated model.
- `statics-steel-solver`: validation references (FW 401 / EN 13941 hand formulas, published cases, networks with
  sisKMR results); twin pipes as one element with two carrier pipes; mapping of `line_types` to the line classes of
  the standard spectra; service life and scaling of the simulated period (weights of `representative-periods`).
- `statics-plastic-flexible`: long-term values of PE (long-term E-modulus, MRS, temperature reduction factors);
  soil and traffic inputs shared with `statics_sections`; bare PE pipes of the IDA sample `low_temperature_network`
  (GEROtec, PE100-RC) need their material values there.
- `statics-results`: utilisation map, problem spots, report form.
