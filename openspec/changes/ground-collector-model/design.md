## Context

The explore session of 2026-11-20 decided how ground collectors enter the Districts Modeler (T1–T15, summarised in
"Outlook" below). This change is the first of two (T15): everything that can be built and tested without IDA
Districts. It is the reference the Modelica model is developed against (T8) and the input of the second change
`ground-collector-routes`.

What exists today:
- A route becomes one IDA `FDpipebundle` (Modelica, `invoke_network.py`), with ambient `Air`, `Ground` (boundary
  `TGround` of the Climate macro, no storage) or `Duct`, discretised by `fd_meterPerNode`.
- Vertical boreholes (`boreholes`, `borehole_fields`) belong to an energy plant and are written into its template.
- numpy and scipy are in the QGIS Python of 3.44 (numpy 2.4.2, scipy 1.17.0) and 4.2 (numpy 2.4.6, scipy 1.17.1);
  `pipe_sizing.py` already uses scipy.optimize.

QGIS versions: 3.44 (Qt5) and 4.2 (Qt6). The change is pure Python with numpy/scipy, with no Qt, QGIS API or
database, so there is no Qt5/Qt6 difference and no `compat.py` helper. No DB schema change, so no `upgrade.py` step.

## Goals / Non-Goals

**Goals:**
- A versioned parameter contract that the Modelica components and the plugin's model build (change 2) both follow.
- One generic geometry for all collector types, with presets.
- RC values fitted automatically, with a measured error against the 2D reference.
- A Python ground model with the contract's ground and surface equations: start state for the simulation, and
  reference for validating the
  Modelica model.
- Everything testable in `districts/test` without the test DB and without IDA Districts.

**Non-Goals:**
- The Modelica model itself (IDA Districts library, outside this repository).
- DB tables, the resources tab, the route type, the model build, costs, outputs, model checks (change 2).
- Sizing collectors in the cost optimization; coupling the other pipes of a bundle to the collector ground; a
  generator for collector fields (later changes).
- Evaporation, snow and moisture transport in the ground.

## Decisions

### G1 One trench cell per loop, per trench meter
A collector route of length l with n loops stands for n parallel trenches of length l, each with one loop, at the
trench spacing s (T2). The model simulates one loop in one trench; flows and heat flows are multiplied by n. All values
of the ground are per meter of trench, over a cell of width s (the trench and half of the gap on each side). The
ground is uniform along the trench, so the RC values are the same in every section.
*Alternatives:* one trench with n loops side by side (n is then a geometry, not a multiplier); coupling neighbouring
trenches explicitly (T6 chose the symmetry boundary).

### G2 Generic geometry, presets fill it (T14)
`utility_functions/ground_collector_geometry.py`, pure functions. The generic description (dataclass
`CollectorGeometry`):

| Field | Unit | Meaning |
|---|---|---|
| `spacing_m` | m | trench spacing s = width of the cell |
| `source_width_m`, `source_height_m` | m | heat source region in the cross-section |
| `source_depth_m` | m | depth of the region's centre below the surface |
| `loop_length_per_m` | m/m | loop pipe length per trench meter |
| `pipe_d_inner_m`, `pipe_d_outer_m` | m | loop pipe (from `pipes`, change 2) |
| `pipe_lambda_w7mk` | W/(m K) | wall conductivity |
| `local_spacing_m` | m | distance between neighbouring pipe passes inside the region (for G6) |

Presets (`PRESETS`, each a function from its inputs to `CollectorGeometry`, inputs kept for display):

| Preset | Inputs | Region (w × h) | Loop length per m |
|---|---|---|---|
| horizontal ring | ring diameter D, pitch p, depth z, spacing s | D × d_o | π·D/p |
| vertical ring | D, p, depth of the ring centre z, spacing s | d_o × D | π·D/p |
| flat meander | layer width b, pipe spacing a, depth z, spacing s | b × d_o | b/a |
| bare pipe | depth z, spacing s | square of side r_o/0.5902 (the pipe itself, resolved) | 1 |

The bare pipe's region is the pipe: a square with the steady conduction resistance of the circle, resolved in the
reference with 1 cm cells (`pipe_resolved`), the wall temperature acting directly on its cells. A single coarse cell
would make its temperature depend on the grid (found while testing: up to 5 K after an extraction step).

The loop runs from one end of the route to the other (pass-through, T3). A return pipe is never part of the
collector: it is a route of its own on the map (or the other pipe of the bundle, T11), an ordinary pipe that is not
coupled to the collector's ground. A region dimension smaller than one grid cell is widened to one
cell. Each preset checks its inputs (positive, region inside the cell and below the surface); invalid inputs raise
`ValueError`. The source is spread evenly over the region. For a ring, the pipe is really concentrated at the ring's
top and bottom; the validation (G9) measures this simplification.
*Alternatives:* only the two ring types (T14 chose generic); a fixed list of types without generic values.

### G3 Soil and freezing parameters
Dataclass `SoilProperties`: `lambda_w7mk` (unfrozen), `rho_c_j7m3k` (unfrozen, volumetric), `water_content`
(volume fraction θ), `t_freeze_c` (T_f, default 0 °C), `freeze_range_k` (ΔT_f, default 1 K), `lambda_frozen_ratio`
(λ_frozen/λ_unfrozen, default 1 = switch off), `t_mean_surface_c`, `amplitude_surface_k`, `phase_day`
(undisturbed annual wave, Kusuda), `geothermal_gradient_k7m`, `depth_deep_m` (lower boundary, default 15 m).
Latent heat of water L = 334 kJ/kg, ρ_w = 1000 kg/m³. Apparent capacity over [T_f − ΔT_f, T_f]: ρc + θ·ρ_w·L/ΔT_f.
Ice fraction: linear over the same range.

Numerics (2D reference and Python ground model alike): implicit Euler; the liquid fraction is iterated directly
(Swaminathan and Voller): its slope 1/ΔT_f goes into the matrix for cells inside the freezing range, cells outside it
take the fraction of their new temperature. Converged when the temperatures change by less than 0.01 K and the
fraction by less than the equivalent; damped by half after 5 iterations, at most 50; a step that still does not
converge is split in halves, up to 64 parts, then an error. Energy is conserved to rounding. A secant apparent
capacity, tried first, did not converge on a −4 °C wall at the first frost step.

### G4 Surface: own component, same equations in Python (T10)
`GroundSurface` per meter of trench (area = s × 1 m): a surface layer of thickness `d_layer_m` (default 0.05 m) with
capacity ρc·d·s, balance
`C_s dT_s/dt = s·[h_conv·(T_air − T_s) + (1 − albedo)·I_glob + ε·σ·((T_sky+273.15)⁴ − (T_s+273.15)⁴)] − Q_port`.
Parameters `epsilon`, `h_conv_w7m2k` (default 10), `d_layer_m`, `rho_c_j7m3k`, `spacing_m`; inputs `TAir`,
`IGlob` (W/m² on the horizontal), `TSky` and `albedo` (contract version 2: an input, so a climate-file column can
carry snow or the season; otherwise bound to a constant, `SurfaceProperties.albedo` in Python). `Q_port` is the heat
into the ground through the port. The fit sees the
surface linearized (G7), so its properties are part of the fit and a different surface type means a refit (5–12 s);
this loosens T10, whose aim (the surface as a component of its own, with a clean interface) holds.

What the balance does matters more than the RC accuracy: with the Kalmar climate the surface averages 11.1 °C against
6.9 °C for the air (+4.2 K). A surface at the air temperature instead gives 49–65 % less heat into the fluid over the
year (2–38 % less in winter), a sol-air temperature prescribed as the surface +3.5 to +7.9 %. Without evaporation the
balance is probably too warm (measured surfaces are mostly 1–3 K above the air), see Risks. The RC model's hourly
surface temperature differs from the 2D model's by 1.5–3 K RMS (mean within 0.1 K): the daily response of the top
soil is lumped into `T_top`; the heat into the fluid is hardly affected (G9).

In IDA the inputs come from the Climate macro's `climate_processor` (the `ENVIRONMENT` model): `TAir` ← `TAIR2`,
`TSky` ← `TSKY` (computed by IDA from air temperature, humidity and `SKYCOVER`; the climate files have no sky
temperature), `IGlob` = `IDIRNORM`·sin(`ELEVSUN`) + `IDIFFHOR`. The Python ground model computes the same three
signals from the climate file's columns (`TAIR`, `RELHUM`, `IDIRNORM`, `IDIFFHOR`) and the site (latitude,
longitude, time zone, height) with the equations of IDA's `ENVIRONMENT` model: sky temperature and sun elevation
reproduced in `utility_functions/ground_climate.py` (T18), so the start state and the simulation see the same sky.
Source: `ClimateNmf/climate.nmf` of the IDA Modeler library (TSky: `TAir − dTAirSky` when the sky cover is missing or
outside 0–100 %, otherwise Walton-Clark-Allen with the dew point `SATTEMP(PVap)`; sun position after ASHRAE) and
`PsycfuncNmf/psychro3.for` (`SATPRES`, `SATTEMP`). Climate files without cloudiness (e.g. KALMAR.PRN) get
`TAir − 5 K`.

### G5 Fixed RC node structure, six nodes (T6)
Per section, per meter of trench, six ground nodes and nine resistances, all fitted:

```
 surface port T_s ──R_st── T_top ──R_tt── T_top2 ──R_tn── T_near ──R_ln── T_loc ──R_loc── loop wall (pipe)
                            │                              │
                            └──────────R_tf──────┐       R_nf
                                                 T_far ─────┘
                                                   │ R_ff
                                                 T_far2 ──R_fd── T_deep (fixed)
```

Each node stands for one time scale: `T_loc` the coil region (hours), `T_near` the soil around it (a day), `T_top` the
shallow layer and `T_top2` the layer just above the coil (weeks, months), `T_far` beside and below (months), `T_far2`
the deep soil (a year and longer). Fitted: `C_top`, `C_top2`, `C_loc`, `C_near`, `C_far`, `C_far2` [J/(K m)], `R_st`,
`R_tt`, `R_tn`, `R_tf`, `R_ln`, `R_nf`, `R_ff`, `R_fd`, `R_loc` [K m/W]. Computed: `T_deep` = undisturbed temperature at
`depth_deep_m`. `T_loc`, `T_near`, `T_top2` and `T_far` carry the latent heat (G3) of their volumes C/ρc; with only
`T_loc` and `T_near` freezing the frozen winter heat was 16–29 % low, the soil that freezes in the 2D reference lies
also in the layer above the coil. With `lambda_frozen_ratio` ≠ 1 a conductance between two nodes is multiplied by
1 + (ratio − 1)·(mean ice of the two), `R_loc` with the loc ice.

How the structure was found (frequency fit, G7; Swiss and Kalmar climate, year 3 against the 2D model):
- four nodes (top, loc, near, far): the meander 14–21 % low in winter. Its response to the fluid at periods from
  3 months to 2 years was 11 % too weak, while the steady state was right: one time constant too few;
- splitting `T_far` alone did not change that; a link from `T_loc` to `T_top` was not used by the fit;
- splitting `T_top` (two layers above the coil) halved it (−7 %), splitting `T_far` on top of it closed it.
Six nodes: annual −1.3 to −0.7 %, winter −6.2 to +0.6 % unfrozen and −5.9 to −0.9 % frozen, hourly RMS 0.3–0.7 W/m
(four nodes: 0.9–2.3 W/m), for all presets on both climates. The fitted values are not unique in themselves, but the
regularization (G7) picks one solution reproducibly; only the behaviour is checked, never the values.
*Alternatives:* three to five nodes (above); a radial node chain at the pipe; a variable number of nodes from a
vector fit (later, would make the contract's node count variable).

### G6 Local resistance: coupling of the reference and fit start
R_loc = ln(r_eq / r_o) / (2π·λ·loop_length_per_m), with r_eq = max(local_spacing / π, 1.5·r_o), couples the wall to
the source region's cells in the 2D reference of a region preset and starts the fit; the fitted `rLoc` replaces it in
the model. The local spacing, the distance between neighbouring pipe passes, follows from the pipe density:
region extent / loop length per trench meter. Taken from the pitch at first, it made `R_loc` of sparse coils far too
large: the 2D model was 31–34 % below the validated 3D model of Wu et al. (G7), with the pipe density 11–20 %. A resolved pipe (bare pipe) has no R_loc in the reference (1e-5 K m/W). The wall resistance
ln(r_o/r_i)/(2π·λ_wall·loop_length_per_m) and the flow-dependent convection are computed in the Modelica model
(contract, G8), not here.

### G7 2D reference and fit
`utility_functions/ground_reference.py`: finite volumes over the cell's half (width s/2, symmetry at both sides),
from the surface down to `depth_deep_m`, a non-uniform grid (finer near the source region; about 400 cells for a
region, about 3000 with 1 cm cells for a resolved pipe), implicit Euler with scipy.sparse, time step 1 h, freezing as
in G3. Boundaries: the surface either prescribed (`T_s(t)`) or through the G4 balance; bottom `T_deep`; the source
either a prescribed heat flow `q(t)` [W/m] spread evenly over the region's cells, or a wall temperature `T_wall(t)`
behind R_loc (G6). The steady state is one implicit step of 10⁹ h.

`utility_functions/ground_rc.py`, fit **in the frequency domain** to the **heat flow into the fluid**. The unfrozen
reference is linear (`linearSystem`: capacities, conductances, inputs outside, deep and wall temperature, outputs heat
into the fluid and from the surface), with the surface as the simulation has it but linearized: the `GroundSurface`
layer with a heat transfer h_conv + 4εσT̄³ (T̄ the mean surface temperature) to an outside temperature
(`linearSurface`). For 24 periods from 2 h to 2 years and the steady state, `frequencyResponse` gives amplitude and
phase of the heat into the fluid as a response to the outside and to the wall temperature (one complex sparse solve
per period, no time stepping). The RC network's responses are analytic. Residuals: the complex differences of both
responses, each scaled by its largest value, weighted 3× from 3 days to a year (where the winter heat is decided) and
10× in the steady state; for the deep boundary its steady split between the fluid and the surface (without the
surface part the meander's 2-year response came out 6 % weak and its winter 10 % low); plus a regularization
0.01·(log value − log geometric guess).
`scipy.optimize.least_squares` over the logarithms of the 15 values, 9 starts (`C_near`, `C_loc` scaled by 0.1, 1,
10), the best kept; 1–3 s per preset, about 20 s for the meander. The heat flow through the surface is not fitted:
four or six nodes cannot follow both, and with it the heat into the fluid got worse (winter −9 to −13 %).

Why not in the time domain, as first built: fitted to series (an outside wave, wall steps of 60 days, the steady
state), equally good fits put the heat over the year alike (±2 %) but scattered by +1 to −27 % in winter with a soil
0.02 K warmer; the 60-day steps left the time scales of a winter free. The frequency fit pins every time scale and,
with the regularization, is unique: soil variants differ by less than one point.

Result: `RcFit` (values, the largest error of each response relative to its largest value over all periods, the
steady error, fingerprint). Acceptance, to catch a failed fit: response errors ≤ 15 %, steady error ≤ 1 %; measured on
the four presets: 2–9 %, steady ≤ 0.2 %. Otherwise `fitRc` returns the fit flagged `accepted=False`, and the caller
decides (change 2 refuses the model build). The accuracy itself is claimed by the validation (G9).

Fingerprint: md5 over the generic geometry, the soil and surface properties, the fit settings and `FIT_VERSION` (a
constant raised whenever the fit or the reference changes its results; 4 since the six-node frequency fit).
*Alternatives:* shape-factor values without a fit (T4 b, rejected: unknown error); fitting with freezing (T5 c,
rejected: nonlinear fit); the time-domain fit (above); fitting the region temperature (left the long-term
resistance 12 % off); the surface prescribed in the fit (hourly surface temperatures 3–5 K off); a coarse 2D grid in
Modelica instead of the RC network (tested: 100 cells −2.6 % annually, −4.6 % frozen winter; robust but about 15
times the states).

Verification of the 2D reference: against analytic solutions, a pipe after a wall step (Jaeger) within ±1 %, a
freezing front (Neumann) within ±3 %, the steady buried pipe (half-space) −2 to −6 % (coarse far-field cells), the
undisturbed annual wave within 0.2 K. Against literature on slinky collectors: the field measurement of Ali, Kariya,
Miyara (Resources 6, 56, 2017; UA of a reclined slinky, 12–96 h) +1 % and +19 % (two flow rates); the validated 3D
model of Wu et al. (Appl. Therm. Eng. 30, 2574, 2010; heat per trench meter after 140 h at pitches 1.2–3.0 m)
−11 to −20 %. The 2D band smears the coil: sparse coils and early times come out low. Grid study (ring, Kalmar): 400
cells −1.4 % against a fine grid, monotonic and conservative toward coarser grids.

### G8 Parameter contract
`utility_functions/ground_collector_contract.py` holds `CONTRACT_VERSION = 2` and, per component, the parameters,
inputs, outputs and ports with name, unit, shape and meaning. The Python ground model (G9) reads the ground and surface
parameters and the GroundSurface inputs (its weather) through it, and a test checks that they agree. The pipe and
discretization parameters (`dInner`, `dOuter`, `lambdaWall`, `roughness`, `liqType`, `TFreeze`, `NusseltMin`,
`nCellsSection`) are in the contract for the Modelica model and change 2, without a Python counterpart. Version 2
(from building the Modelica model): one surface port for all sections, `albedo` an input, `nCellsSection` and
`NusseltMin` added. The Modelica names are the contract names (IDA `|name|` quoting, as for
`FDpipebundle`). Change 2 writes exactly these names and checks the contract version of the installed model.

`GroundCollector` (one instance per collector route):
- Fluid connectors `liq1`, `liq2` as `FDpipebundle` (flow in both directions; upwind cells: the mean transport delay
  is the loop volume / flow, a front is smeared over the cells, which was accepted instead of plug flow).
- Parameters: `nLoops`, `lTrench` [m], `nSections` (M, default 3), `nCellsSection` (default 10), `loopLengthPerM`,
  `dInner`, `dOuter`, `lambdaWall`, `roughness`, `liqType`, `TFreeze`, `NusseltMin` (fluid); `cTop`, `cTop2`, `cLoc`, `cNear`, `cFar`, `cFar2`
  [J/(K m)]; `rSt`, `rTt`, `rTn`, `rTf`, `rLn`, `rNf`, `rFf`, `rFd`, `rLoc` [K m/W]; `TDeep`; `rhoCSoil`,
  `waterContent`, `TFreezeSoil`, `freezeRange`, `lambdaFrozenRatio`; start values `TStartTop[M]`, `TStartTop2[M]`,
  `TStartLoc[M]`, `TStartNear[M]`, `TStartFar[M]`, `TStartFar2[M]` (the ice of the freezing nodes follows).
- One heat port `surface` to a `GroundSurface`, shared by all sections: every section sees its temperature, the port
  carries the mean heat of the sections per trench meter.
- Outputs: `TIn`, `TOut` [°C], `QExtracted` [W, all loops, positive = heat from the ground into the fluid],
  `QSurface` [W, all loops], `TLoc[M]`, `TNear[M]`, `iceFraction[M]` (the freezing nodes weighted by their latent
  volumes).
- The loop's pipe cells are assigned to the sections by their position along the unrolled loop (section j holds the
  loop length of trench part j). Convection: Gnielinski (turbulent), Nu = 3.66 (laminar), as in `FDpipebundle`.

`GroundSurface` (one instance per route): G4.

Start values in IDA: the IDA Modeler writes a state's start from the value stored with the variable in the model file,
not from the `TStart<node>` parameter, so change 2 writes the start values twice: as the parameters and as the values
of `TTop`, `TTop2`, `TLoc`, `TNear`, `TFar`, `TFar2` (and `TSurface` of GroundSurface). The freezing nodes are
temperature states with the latent heat as an apparent capacity (states with a computed start, as enthalpies, start
at 0 in IDA).

### G9 Python ground model, start state, validation cases (T17)
`ground_rc.py` also holds the Python ground model (`runGroundModel`): one section's six nodes with freezing (G3, G5)
and the `GroundSurface` node (G4, full balance with radiation) or a prescribed surface temperature, driven at the
pipe wall either by a heat flow `q_wall(t)` [W/m] or by a wall temperature `T_wall(t)` through `rLoc`. Time step 1 h
with sub-steps where the RC time constants are shorter. No pipe, no plug flow, no convection: the fluid side exists
only in the Modelica model.

Start state (T12): `startState(params, geometry, soil, weather_year, t_mean_fluid, years=5, start_day,
r_conv_nominal)` holds the wall at the fluid temperature `t_mean_fluid` behind the wall resistance and a nominal
convection resistance `r_conv_nominal` (a parameter, not a flow simulation). It runs the ground model over the
given number of years of the repeated climate year and returns `T_top`, `T_loc`, `T_near`, `T_far` and the surface
at `start_day`, the same in every section. `startState(..., undisturbed=True)` returns the analytic undisturbed
profile at the node depths instead (T12 option a). The result depends only on its inputs: reproducible.

Validation against the 2D reference (`test_ground_rc.py`, surface with sun but linear, 3 years, the third compared):
heat into the fluid within ±3 % over the year (measured −0.6 to +0.6 %) and ±7 % in winter (−5.8 to +2.4 %, the
meander lowest) for all four presets; hourly RMS ≤ 10 % of the mean heat flow in seasonal operation (up to 4 %) and
≤ 40 % with daily cycling (2 h ramps; up to 36 %, the bare pipe: its fast near-pipe response is weighted least in
the fit); the frozen winter within ±7 % (−3.2 % ring). With the full surface balance, year 3: Kalmar −1.2 to −0.7 %
over the year, winter −6.2 % (meander) to +0.6 %; Swiss SMA climate −1.3 to −0.8 %, winter −4.3 to −0.1 %; frozen
−5.9 to −0.9 %.

Validation cases in `districts/test/data/ground_collector_cases/`, one folder per case with `case.json` (preset and
inputs, soil, surface, site, fitted parameters, start state, contract and fit version) and `series.csv.gz` (gzip,
written reproducibly). The csv holds per hour the wall temperature and the weather (`T_wall`, `TAir`, `IGlob`, `TSky`,
so a Modelica test feeds the same sky), the Python ground model's outputs (heat at the wall, `T_loc`, `T_near`, surface
temperature, ice fraction) and the 2D reference's (heat at the wall, surface temperature, ice). The weather is the real
Kalmar year (KALMAR.PRN of IDA 5.2, sky and radiation as IDA computes them), run three times; the third year is
stored, and the case's start state is the Python model's state at its start, so a case starts settled. Generated by
`districts/test/make_ground_collector_cases.py` (about 15 minutes, needs the climate file; the tests need only the
stored cases). Cases: the four presets in seasonal operation, the horizontal ring with −4 °C in winter (freezing),
and a wall temperature step. Tests: the stored model columns are what the model computes now (a model change needs
new cases), and the model stays within ±3 % of the reference over the year and ±7 % in winter. The Modelica ground
part is validated against the Python ground model (same equations, tight) and the 2D reference (loose).

Pipe cases for the Modelica model, documented here (no Python code), with expected values:
- Transport delay: an inlet temperature step reaches the outlet after V_loop / V̇ (loop volume / volume flow per
  loop), with the step's shape kept (plug flow), for flow in both directions.
- Constant wall temperature: T_out = T_wall + (T_in − T_wall)·exp(−L_loop / (ṁ·c_p·R')), with R' the convection and
  wall resistance per meter of loop.
- Zero flow: no outflow, the loop's fluid relaxes to the ground temperature.
- Energy balance of the coupled model over a year: extracted heat = Σ ṁ·c_p·(T_out − T_in)·Δt within 0.5 %.

### G10 Module layout and errors
Five modules in `utility_functions/`: `ground_collector_geometry.py`, `ground_collector_contract.py`,
`ground_climate.py`, `ground_reference.py`, `ground_rc.py` (fit, ground model, start state). No import from QGIS,
Qt or the DB, so they run in a plain Python with numpy/scipy, also for the Modelica developer. Errors are `ValueError`
with English text. They do not reach the user in this change; change 2 shows them through `tr_msg`.

## Risks / Trade-offs

- [The fixed node structure misses a preset's dynamics] → happened with three and four nodes; six nodes (G5). The
  validation limits per preset stay in the tests; a preset that fails needs a structure change and a new contract
  version. A new geometry type is checked the same way before it is offered.
- [Freezing breaks the linear fit] → the frozen case and test compare the winter heat with the frozen 2D reference
  (±7 %); measured −5.9 to −0.9 % (two climates).
- [The latent volumes come from fitted capacities, not from geometry] → only the frozen behaviour is checked (winter
  heat); a frozen volume of its own (`vLatent`, fitted to a frozen run) is the fallback if a geometry misses.
- [The 2D band approximation of a 3D coil] → verified analytically (±1–3 % transient, −2 to −6 % steady) and against
  the literature (−20 to +19 %, G7); the 2D model is the reference the RC model is fitted to, so its uncertainty is
  the model's. Sparse coils and early hours come out low. A later refinement: 3D shape factors for the local
  resistance, or a calibration on measurements.
- [The surface balance has no evaporation: the surface comes out about 4 K warmer than the air (Kalmar), measured
  surfaces mostly 1–3 K, so the summer recovery is optimistic] → stated with the results; an evaporation term (or a
  calibrated offset) is a later refinement; the opposite simplification, the air temperature as surface, gives
  49–65 % less heat over the year.
- [The hourly surface temperature of the RC model differs by 2–4 K from the 2D] → not an output change 2 uses for
  decisions; the heat into the fluid is validated.
- [Daily cycling: the hourly heat flow deviates by up to 36 % of its mean (bare pipe), 3–13 % for the coils] → the
  annual and winter heat stay within ±3 % and ±7 %; the limit (40 %) documents it.
- [Even source distribution in ring regions] → measured indirectly by the ring cases against the reference. A later
  refinement can weight the region's cells without changing the contract.
- [IDA's `ENVIRONMENT` equations (sky temperature, sun elevation) are not in this repository] → taken from
  `climate.nmf` and `psychro3.for` (G4); a test compares Python `TSKY` with an IDA run on KALMAR.PRN (stored as test
  data) within 0.1 K. `ELEVSUN` of the same run agrees within 0.0005°.
- [The contract changes while the Modelica model is being built] → `CONTRACT_VERSION`; change 2 refuses a model of
  another version.
- [The 2D reference is slow in the tests] → coarse default grid, 1 h steps, a linear surface in the tests; the fits
  run once per test module (fixture); the full surface balance only in the case generator, the tests read its output.

## Migration Plan

None. New modules and test data only; nothing existing changes.

## Open Questions

None.

## Outlook: change 2 `ground-collector-routes`

Decisions from the explore session that change 2 implements:
- T1, T3: a collector is a route in `lines`, always pass-through between two nodes; the topology is unchanged.
- T2: `lines.n_loops` (default from the resource).
- T4: the route type dropdown lists the pipe classes plus the collector resources (a new resource table, for example
  `public.ground_collectors`, with export and import in the resources tab); the pipe bundle stays on the route.
- T11: one pipe of the bundle (sequence in the resource) runs through the loops as `GroundCollector`; the others stay
  an `FDpipebundle` with `TGround`. Pipe sizing never changes the loop pipe.
- T9: costs per trench meter and per loop meter, operation and lifetime in the resource, in the NPV in place of the
  ordinary pipe costs; no sizing by the cost optimization.
- Return pipes: a return drawn as its own route in a collector trench must not pay the trench a second time, and
  two routes on the same geometry must survive the topology generator (an offset, or a check). A field with a supply
  header at one end and a return header at the other needs no return in the trench.
- T12, T13: start-state setting (undisturbed or pre-calculated); `lines.t_mean_init` (default from the resource) with
  an action "take from results" and a model check that warns when it differs from the last annual run; the start
  state is named in the results.
- Outputs per line (inlet and outlet temperature, extracted heat, surface heat, `TNear`, ice fraction) and key
  figures in the network report and `version_kpis` (trench and loop meters, kWh/(m a), lowest outlet temperature,
  maximum ice fraction).
- Before a build: the installed IDA Districts has `GroundCollector`/`GroundSurface` of the expected contract version,
  and the fit of every used resource is current and accepted.
