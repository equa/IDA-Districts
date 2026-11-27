## Context

Roadmap T1–T12 (archived change `pipe-series-catalog`): a full pipe stress verification under EN 13941 / AGFW
FW 401, comparable to sisKMR (T1), with the plugin's own FE solver (T5), on the stored statics model (T6, change
`statics-model`, decisions M1–M6). The decision session of 2026-11-20 to 2026-11-27 settled this change (S1–S10).

Inputs that exist:
- the statics model of the version: `statics_model_nodes` (bend class, radius, junction type, overrides),
  `statics_model_sections`, `statics_model_pipes` (per single pipe or twin: pipe ids, sequences, d_inner, d_outer,
  wall per carrier, casing, cover, x, y), `modelState` (missing | current | out of date);
- materials with Young's modulus, thermal expansion, yield strength, Poisson's ratio (`materials`);
- `pipe_series` (system type, σ_ax max); `pipes.p_max_bar`;
- simulated results per line and pipe sequence: `line_s_temp$<seq>`, `line_s_p$<seq>` (as read by
  `model_checks.lineSeries`), for period runs also `<table>_period<k>`;
- numpy 2.4.6 and scipy 1.18.1 in the QGIS Python of 3.44 and 4.2.

Sources at hand: the isoplus planning manual, 6th edition (`IP_Planungshandbuch_DE.pdf`, pages cited as "PHB
chapter/page"; not committed, copy only with isoplus' permission). Not at hand: EN 13941-1 and FW 401 Part 10
(sold by DIN Media and AGFW). Every value taken from neither is marked "to be confirmed" (D9).

QGIS versions: 3.44 (Qt5) and 4.2 (Qt6). The change uses `QgsTask`, `QgsApplication.taskManager()`, a message box
and the existing table dialog; enum access goes through the fully scoped names both accept or through
`utility_functions/compat.py` where one is missing.

## Goals / Non-Goals

**Goals:**
- Stresses, displacements, pads and findings for every rigid steel pipe (single and twin) of a version, stored with
  the model's fingerprint.
- Verdicts where the limit has a source; utilisation where it has not; never an invented limit.
- Validation against hand formulas and the isoplus planning manual in the test suite.

**Non-Goals:**
- Fatigue (rainflow, spectra, service life, period weights): change `statics-fatigue`; until then the report says
  "fatigue not checked".
- Result maps, copying pads into `statics_sections`: change `statics-results`.
- Plastic and flexible pipes: change `statics-plastic-flexible`; their lines are skipped and listed.
- Operational self-prestressing and elastoplastic steel.
- The bend radius rule of the statics model (1000 × Da); PHB 2/16 and 2/48 give minimum radii per DN, noted for
  a later change of `statics-model`.

## Decisions

### D1 Scope (S1)
FE solver and static checks of rigid steel pipes. Fatigue moves to a new change `statics-fatigue` (the roadmap
becomes six changes). Hand formulas are test oracles only, never a user-facing second path.

### D2 Loads per pipe (S2)
Per pipe (per carrier of a twin) and per quantity: the higher of the design value and the simulated maximum.
- Design values: parameters `design_temperature_c` 120, `design_pressure_bar` 16, `laying_temperature_c` 10,
  overridden per section by `statics_sections.design_temperature_c`, `design_pressure_bar`, `laying_temperature_c`.
- Simulated: the maximum over all times and segments of `line_s_temp$<seq>` and `line_s_p$<seq>` of the line and
  the pipe's sequence, including the `_period<k>` tables of a period run. Pressure as the plugin already compares it
  with `p_max_bar` (Pa / 1e5).
- The lowest temperature of the cycle is the laying temperature.
- Each pipe stores the source of each value: parameter, section override or simulation. Without results both
  carriers of a twin get the same temperature; the report says that the bending from their difference is missing.
- The design pressure is checked against 25 bar (PN 25 of the isoplus rigid system, PHB 12/4).

### D3 FE model (S10)
- 3D beam elements (Euler-Bernoulli, 6 degrees of freedom per node), at most `element_length_m` (1.0) long,
  subdivided further within 3 m of bends, tees and points.
- Pipe chains of the model (M1) joined at junctions by pipe sequence, as the network model connects them. A twin
  and a single pipe meet through a rigid offset link from the casing axis to the carrier.
- Prefabricated and elastic bends: curved elements with the flexibility factor k = 1.65 / h and the stress
  intensification factor i = 0.9 / h^(2/3), h = s · R / r_m² (EN 13480-3, public). Small-angle kinks: a corner node
  with the single-mitre factor of EN 13480-3.
- Tees: rigid joint, stress intensification factor of the welded tee of EN 13480-3. Reducers: step in the cross
  section. End caps: pressure thrust p · A_i. Valves: rigid piece.
- `statics_points`: fixed point locks all six degrees of freedom; compensator is free axially with its spring
  rate; one-time compensator per D6.
- Material values from the steel layer's material; σ_zul from `pipe_series.sigma_ax_max_n7mm2`, else the parameter.

### D4 Twin pipe (S3)
One chain per twin with the soil springs on the casing. Plane sections: both carriers deform with the casing; axial
and bending stiffness are the sums of both carriers about the casing axis, with the carrier offsets from
`statics_model_pipes`. A temperature difference becomes a thermal bending load. After solving, each carrier's
stress is axial strain plus curvature × its offset, plus its own pressure. Foam slip is not modelled. PHB 12/5
("axial expansion at the mean temperature") is the validation.

### D5 Soil (S5, S8)
- Axial friction per metre (FW 401, reproduced on PHB 12/4 with μ 0.40 within ±1 % for DN 20–500):
  F'_R = μ · [(1 + K0)/2 · γ · Z · π · Da + G], K0 = 1 − sin φ, Z = cover + Da/2, G = weight of steel, water,
  foam and casing. Below `groundwater_depth_m` γ is the effective weight γ − 10 kN/m³.
- Two friction coefficients: μ_max (`friction_max` 0.40, section column `friction_coefficient`) for stresses and
  forces, μ_min (`friction_min` 0.20, section column `friction_coefficient_min`) for displacements, legs and pads.
  The existing column `friction_coefficient` is kept with the meaning μ_max instead of being dropped from existing
  versions.
- Axial spring: elastic up to F'_R at `axial_slip_m` (0.5 mm), then sliding.
- Lateral spring: elastic up to the passive limit K_p · γ · Z · Da, K_p = tan²(45° + φ/2), reached at
  `lateral_slip_m`; constant beyond.
- Vertical: downwards elastic with the lateral stiffness; upwards limited by the weight of the soil above
  (γ · Z · Da) plus G.
- Soil values: parameters `soil_unit_weight_kn_m3` 19, `friction_angle_deg` 32.5 (PHB 9/12, 12/4), overridden per
  section by the existing columns.
- `axial_slip_m` and `lateral_slip_m` are marked "to be confirmed: EN 13941"; the bend stresses that depend on them
  are utilisation only (D9).

### D6 Laying methods (S6)
`statics_sections.laying_method`: `cold`, `conventional` (default), `thermal_prestress`, `one_time_compensator`,
`self_prestress`; flag `prestressed_legs`. Values are checked by the solver (unknown → finding), not by a CHECK
constraint, so existing rows never block an upgrade.
- cold, conventional: stress-free at the laying temperature.
- thermal_prestress: stress-free at the preheating temperature, default the mean of laying and design temperature
  (PHB 12/2), section column `preheat_temperature_c`.
- one_time_compensator: the section is stress-free at the preheating temperature; each one-time compensator of
  `statics_points` is a node whose sides slide against each other up to it, then locks. Its travel u_m, axial spring
  rate and bellows area come from the isoplus table (PHB 7/2, in `statics_catalog.py`) by DN, overridden by the
  point columns `max_travel_mm`, `spring_rate_n_mm`, `bellows_area_cm2`.
- prestressed_legs: the legs and pads are designed with VTf = T_E + (T_B − T_E)/3 (PHB 10/31).
- self_prestress: not calculated, finding "not supported".
- Checks: cold laying above 85 °C (single) or 70 °C (twin) (PHB 12/2); movement > 80 mm without prestressed legs
  (PHB 12/4); one-time compensator outside the restrained zone, with less than 6 m straight pipe on a side, in a bend,
  travel above u_m, or without an expansion leg or fixed point at both ends of its stretch (PHB 7/1, 10/18).

### D7 Load steps and solution (S10)
- Steps: (1) stress-free state, (2) heat-up to the maximum temperature with pressure, (3) cooling to the laying
  temperature, (4) second heat-up. Steps 3–4 reverse the friction and give the stress range. Each step in
  increments of at most `load_increment_k` (10 K).
- Each step runs with μ_max and with μ_min.
- Newton iteration on the sparse stiffness matrix (scipy.sparse, spsolve) with sticking/sliding springs by return
  mapping; tolerance on the residual force; at most `max_iterations` (50) per increment.
- Each connected part of the network is solved on its own. A part that does not converge gets a finding and no
  results; the other parts go on.

### D8 Pads placed by the solver (S8)
1. Solve with μ_min without pads.
2. Where the lateral movement at a leg exceeds `pad_trigger_mm` (the movement at which the soil without pad reaches
   its limit, i.e. `lateral_slip_m`), add pads along the leg in `pad_piece_m` (1.0) pieces until the movement drops
   below it, and in `pad_layer_mm` (40) layers until the pad compression stays at most `pad_max_compression` (0.5).
3. The pad is a spring in series with the soil, by the isoplus curve (0.045 N/mm² at 25 %, 0.110 N/mm² at 50 %
   compression, PHB 7/9), over the casing height.
4. Solve again; repeat until no pad changes (at most 5 rounds).
5. More than `pad_max_thickness_mm` (120, PHB 12/4: casing ≤ 60 °C) → finding "prestress the legs or lengthen the
   leg".

### D9 Checks and limits (S7)
Each limit is a parameter with a `source` text. A check gives a verdict only when its limit has a value and a
source; otherwise it reports utilisation against the yield strength Re and "limit not confirmed".

| Check | Value | Limit parameter | Default | Source |
|---|---|---|---|---|
| Axial stress, straight pipe, restrained zone | σ_ax | series σ_ax max, else `sigma_ax_allow_n7mm2` | 190 | PHB 2/12, 2/45, 12/4 |
| PUR shear stress | τ = F'_R / (π · Σ d_steel) | `tau_pur_max_n7mm2` | 0.04 | PHB 9/12, 12/4 |
| Minimum cover | cover | table by DN and traffic load | PHB 9/11 table | PHB 9/11 |
| Pad thickness | pad | `pad_max_thickness_mm` | 120 | PHB 12/4 |
| Movement without prestressed legs | axial movement at a leg | `movement_prestress_mm` | 80 | PHB 12/4 |
| Cold laying temperature | max temperature | `cold_laying_max_single_c`, `cold_laying_max_twin_c` | 85, 70 | PHB 12/2 |
| Design pressure | p | `pressure_max_bar` | 25 | PHB 12/4 |
| Stress range at bends, tees, kinks | i · σ range | `stress_range_allow_n7mm2` | empty | to be confirmed: EN 13941-1 |
| Hoop stress | p · d_i / (2 s) | `hoop_stress_allow_n7mm2` | empty | to be confirmed: EN 13941-1 |
| Upheaval buckling | axial force vs. upward resistance | `buckling_safety` | empty | to be confirmed: FW 401 |

The maximum cover follows from the PUR shear check; the PHB 9/12 table validates it. `traffic_load_kn_m2`
default 33.3 (SLW 60, PHB 9/11). σ_zul fills the empty value of D9 of `pipe-series-catalog`: the templates' rigid
series get 190.

### D10 Results (S9)
Version tables, created like the model tables (`DB_versionTablesDefault.txt`, `statics_db.ensureStaticsTables`):
- `statics_result_run` (one row: run_at, model fingerprint, parameters used jsonb, summary jsonb, status);
- `statics_result_elements` (element id, geom LINESTRINGZ, model pipe id, carrier, load step, friction case,
  σ_ax, σ_hoop, σ_bend, σ_eq, i, utilisation, governing check);
- `statics_result_nodes` (geom POINTZ, model node id, displacement x/y/z per step and friction case, axial force,
  pad thickness and length);
- `statics_result_findings` (rule, severity, model node or pipe id, values jsonb with limit and source, text).

The result state is missing, current (run fingerprint = model fingerprint and the model is current) or out of
date. A run writes all four tables in one transaction at the end; a cancelled or failed run keeps the old results.
A child version copies them with the schema.

### D11 Run and report (S9)
- Button "Calculate statics" in the modeling group, after "Build statics model".
- Refuses a model that is not current, with the reason.
- Runs as a `QgsTask` with progress and cancel, on its own DB connection; reads the model and the results first,
  solves without DB access, writes at the end. The task never touches widgets; the report opens in
  `finished()` in the main thread.
- The report: parameters and their sources, counts, skipped lines (not rigid, no material values), parts not
  converged, findings by rule, pads, "fatigue not checked". Texts translated (de/en).

### D12 DB changes and upgrade
- `statics_sections`: new columns `friction_coefficient_min`, `design_temperature_c`, `design_pressure_bar`,
  `preheat_temperature_c`, `prestressed_legs` boolean; `statics_points`: `max_travel_mm`, `spring_rate_n_mm`,
  `bellows_area_cm2`. `statics_model_sections` and `statics_model_nodes` get the same columns to store the applied
  overrides; `SECTION_OVERRIDE_COLUMNS` and the fingerprint inputs include them.
- `statics_parameters` gets a column `source` and the keys of D2, D5, D7, D8, D9; `ensureStaticsParameters` adds
  missing keys with their default and source and never overwrites a value.
- Existing versions: `upgrade.upgradeVersionDB` adds the columns (`db.addMissingColumns`, one ALTER TABLE per table
  because of the event trigger `restrict_column_alterations`) and creates the result tables. Existing projects:
  `upgradeProjectDB` adds the column and keys. Templates: σ_ax 190 on "Isoplus DRE Standard" and "Isoplus DRD
  Standard"; existing projects keep their series values and fall back to the parameter.
- The SQL in `statics_db` stays equal to `DB_versionTablesDefault.txt` (checked by `test_statics_model.py`).

### D13 Validation (S4)
- Hand formulas: straight run with friction length and fully restrained zone; L, Z and U legs; small-angle kink;
  tee; equilibrium (reactions sum to zero), symmetry, convergence with finer elements.
- PHB 12/4: a straight run between two L bends at Lmax, 130 °C, μ_max: σ_ax at its centre 190 N/mm² within ±2 %,
  DN 20–500, covers 0.8 / 1.2 / 1.6 m, standard insulation.
- PHB 12/5: twin pipes, the trend of Lmax with the spread K (20–60 K), DN 20, 100, 200, within 5 %. The level is
  not reproduced: at the table's Lmax the solver gives 146–173 N/mm² instead of 190, the table needs 7 % (DN 20) to
  35 % (DN 200) more friction than the single-pipe formula. Decided 2026-11-27: test the trend only, the friction
  of twins stays open until FW 401 is at hand (no fitted factor).
- PHB 12/2: a long straight single pipe at 85 °C stays below 190 N/mm², at 95 °C it does not.
- PHB 9/12: the PUR shear check reproduces the maximum cover within ±5 %.
- PHB 7/2, 7/9, 10/31: one-time compensator travel, pad curve, VTf.
- An open task in `tasks.md`: limits and stiffnesses from EN 13941-1 / FW 401 Part 10 once the texts are at hand;
  a sisKMR or ROHR2 network as a further reference if one becomes available.

### D14 Code
- `utility_functions/statics_fe.py`: elements, assembly, springs, Newton solver; numpy and scipy only.
- `utility_functions/statics_checks.py`: loads, checks, pads, findings; pure functions.
- `utility_functions/statics_catalog.py`: the isoplus tables (one-time compensators PHB 7/2, pad curve PHB 7/9,
  minimum cover PHB 9/11) with their source.
- `utility_functions/statics_solve_db.py`: read the model and results, write the result tables, result state.
- `utility_functions/statics_task.py`: the QgsTask.
- `districts.py`, `districts_dialog_base.ui`, `districts_dialog.py`: button and report.

### Decisions while applying
- D3 mesh: elements of `element_length_m` / 4 within 3 m of bends, kinks, tees, fixed points, compensators and
  free ends; the bending length of the soil reaction near a bend is about 1 m (DN 100: 1.3 m), with 1 m elements
  the bend stress was 6 % low. Lumped springs leave the centre element of a friction-limited run short of half its
  own friction: the axial stress is low by h / L (0.3 % on 148 m, 2.6 % on 38 m with 1 m elements).
- D3 kinks: the single-mitre factor of EN 13480-3 is 1 up to about 4° (a small kink is nearly straight pipe).
- D3 junctions: a twin and a single pipe meet at the route node without a rigid offset link (offsets of 0.1 m).
- D5 springs: only the axial friction spring has a history (elastoplastic with return mapping); the lateral and
  vertical springs are non-linear elastic. Pads are per element (runs along a member), not per member.
- D5 friction: with `axial_slip_m` 2 mm the solver gave 1.5–12 % less axial stress at Lmax than the rigid-plastic
  hand formula (the sticking zone at the centre), not on the safe side; with 0.01 mm it reproduces PHB 12/4 for
  DN 20–500 at three covers within the table's rounding. Decided 2026-11-27: default 0.5 mm (within 4 % of the
  table for DN 20, within 1.5 % from DN 100; displacements and the bend stress unchanged from 2 mm). The value
  stays "to be confirmed".
- D9 PUR shear: τ = F'_R / (π · Σ d_steel), at the steel pipe, not at the casing. With it the maximum cover of
  PHB 9/12 is reproduced within ±0.3 % for DN 20, 50, 100, 200, 300 and 1000; DN 500 (5.05 m against the trend of
  its neighbours) is +7 %. With the casing diameter the maximum cover would be about 7 m for DN 100 instead of 4 m.
- D7 convergence: on the template network (2 parts of 5747 nodes) the first cooling increment diverged: nodes that
  slid during the heat-up sit exactly on the friction limit and, by rounding, got the sliding tangent although they
  unload elastically. The limit has a margin of 1e-6, and each Newton step is halved (up to 8 times) while the
  residual grows. The template network takes about one minute per calculation.
- D10 result state: also out of date when the solver inputs the model does not cover change (statics parameters,
  material values, the series' allowed axial stress): `solverFingerprint` in `statics_result_run`.
- D11: the task's DB connection is opened in the main thread (`dbConnect` reads the QGIS authentication manager)
  and used only by the task.

## Parameters added to `statics_parameters`

| Key | Default | Unit | Source |
|---|---|---|---|
| design_temperature_c | 120 | °C | EN 253 continuous limit |
| design_pressure_bar | 16 | bar | project choice |
| laying_temperature_c | 10 | °C | PHB 10/31 example |
| soil_unit_weight_kn_m3 | 19 | kN/m³ | PHB 9/12, 12/4 |
| friction_angle_deg | 32.5 | deg | PHB 9/12, 12/4 |
| friction_max | 0.40 | - | fit to PHB 12/4 |
| friction_min | 0.20 | - | to be confirmed: FW 401 |
| axial_slip_m | 0.0005 | m | to be confirmed: EN 13941 |
| lateral_slip_m | 0.02 | m | to be confirmed: EN 13941 |
| traffic_load_kn_m2 | 33.3 | kN/m² | PHB 9/11 (SLW 60) |
| sigma_ax_allow_n7mm2 | 190 | N/mm² | PHB 12/4 |
| tau_pur_max_n7mm2 | 0.04 | N/mm² | PHB 9/12 |
| pressure_max_bar | 25 | bar | PHB 12/4 |
| stress_range_allow_n7mm2 | empty | N/mm² | to be confirmed: EN 13941-1 |
| hoop_stress_allow_n7mm2 | empty | N/mm² | to be confirmed: EN 13941-1 |
| buckling_safety | empty | - | to be confirmed: FW 401 |
| cold_laying_max_single_c | 85 | °C | PHB 12/2 |
| cold_laying_max_twin_c | 70 | °C | PHB 12/2 |
| movement_prestress_mm | 80 | mm | PHB 12/4 |
| pad_layer_mm | 40 | mm | PHB 7/8 |
| pad_piece_m | 1.0 | m | PHB 7/8 |
| pad_max_thickness_mm | 120 | mm | PHB 12/4 |
| pad_max_compression | 0.5 | - | PHB 7/9 (curve ends at 50 %) |
| element_length_m | 1.0 | m | solver |
| load_increment_k | 10 | K | solver |
| max_iterations | 50 | - | solver |

## Risks / Trade-offs

- [Limits and stiffnesses not confirmed against EN 13941 / FW 401] → marked by their source; checks without a
  confirmed limit give utilisation, never a verdict; the report says so; an open task fills them in.
- [μ_min 0.20 has no source at hand] → marked "to be confirmed"; it only affects displacements and pads, which the
  report names with the friction case.
- [The manual is from 2011–2020 and isoplus-specific] → its values are parameters with their page; other
  manufacturers' pipes use the same parameters, and the series σ_ax overrides σ_zul.
- [Run time on large networks] → sparse matrices, each connected part on its own, element length a parameter, the
  run in the background with cancel.
- [Non-convergence of the friction iteration] → increments of 10 K, a limited number of iterations, the part named
  in the report; the other parts are still calculated.
- [Simulated pressure: absolute or gauge] → the plugin's existing comparison with `p_max_bar` is followed; a test
  pins the unit; the design pressure is the floor anyway.
- [Results of a plastic or flexible line in a mixed network] → those lines are skipped; at a junction with a rigid
  line the rigid side gets a free end and a finding "connection to a non-rigid pipe not calculated".

## Migration Plan

The upgrade adds the columns, keys and result tables at the next version load (D12); no existing value is changed.
Old results do not exist. Rollback: the new tables and columns are ignored by older plugin versions.

## Open Questions

None. The values marked "to be confirmed" are parameters with an open task (D13).
