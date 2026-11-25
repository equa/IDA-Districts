## ADDED Requirements

### Requirement: Parameter contract
`utility_functions/ground_collector_contract.py` SHALL define `CONTRACT_VERSION` (2) and, for the components `GroundCollector` and `GroundSurface`, every parameter, input, output and port with name, unit, shape and meaning as in design G8 and G4, among them the six ground nodes' capacities `cTop`, `cTop2`, `cLoc`, `cNear`, `cFar`, `cFar2`, the resistances `rSt`, `rTt`, `rTn`, `rTf`, `rLn`, `rNf`, `rFf`, `rFd`, `rLoc`, the start values `TStartTop`, `TStartTop2`, `TStartLoc`, `TStartNear`, `TStartFar`, `TStartFar2`, one surface port `surface` shared by all sections, and the GroundSurface inputs `TAir`, `IGlob`, `TSky` and `albedo`. The Python ground model SHALL take its ground and surface parameters by the contract's names and refuse missing, unknown or non-finite ones, and take the GroundSurface inputs as its weather and refuse weather without one of them. The module SHALL NOT import QGIS, Qt or the database.

#### Scenario: Ground model follows the contract
- **WHEN** the test compares the parameters the Python ground model is given with the ground and surface parameters of the contract
- **THEN** both name the same parameters, each a scalar with a unit

#### Scenario: Weather is the GroundSurface inputs
- **WHEN** the test compares the keys of `weatherFromClimate` with the inputs of GroundSurface in the contract, and runs the ground model with weather without `albedo`
- **THEN** the keys are `TAir`, `IGlob`, `TSky` and `albedo`, `albedo` is not a parameter, and the run raises `ValueError` naming `albedo`

#### Scenario: One surface port
- **WHEN** the test reads the port `surface` of GroundCollector
- **THEN** it is a scalar, and the contract version is 2

#### Scenario: Plain Python
- **WHEN** the contract, geometry, climate, reference and RC modules are imported in a Python where QGIS, Qt and psycopg2 cannot be imported
- **THEN** the import succeeds

### Requirement: Generic geometry and presets
A collector SHALL be described per trench meter by a `CollectorGeometry` (trench spacing, source region width, height and depth, loop length per trench meter, loop pipe inner and outer diameter and wall conductivity, local pipe spacing, whether the region is the resolved pipe). The presets horizontal ring, vertical ring, flat meander and bare pipe SHALL compute it from their inputs as in design G2: the rings with loop length π·D/p and no return pipe, the flat meander with b/a, the bare pipe with 1 and its region the pipe itself (a square of side r_o/0.5902, resolved). The local pipe spacing (for `R_loc`, design G6) SHALL be the region's larger extent divided by the loop length per trench meter. A region dimension below one grid cell SHALL be widened to one cell. Invalid inputs (not positive, region wider than the cell, reaching the surface or the lower boundary, inner diameter not below the outer) SHALL raise `ValueError`.

#### Scenario: Horizontal ring
- **WHEN** the horizontal-ring preset gets D = 1.0 m, p = 0.5 m, depth 1.5 m, spacing 3 m and a pipe of outer diameter 0.032 m
- **THEN** the geometry has loop length 2π ≈ 6.283 m per trench meter, a source region 1.0 m wide and one grid cell high at depth 1.5 m, and spacing 3 m

#### Scenario: Bare pipe
- **WHEN** the bare-pipe preset gets a pipe of outer diameter 0.11 m at 1 m depth
- **THEN** the region is resolved, a square of side 0.055/0.5902 m, and the loop length is 1 m per trench meter

#### Scenario: Region at the surface
- **WHEN** a vertical ring of D = 2.0 m has its centre at 0.8 m depth
- **THEN** the preset raises `ValueError` naming the source region

### Requirement: Climate signals as in IDA
`utility_functions/ground_climate.py` SHALL compute the sky temperature, the sun elevation and the global horizontal radiation (`IDIRNORM`·sin(elevation) + `IDIFFHOR`, never negative) from hourly climate-file columns (`TAIR`, `RELHUM`, `IDIRNORM`, `IDIFFHOR`, optionally the sky cover) and the site (latitude, longitude, time zone) with the equations of IDA's `ENVIRONMENT` model (`climate.nmf`, `SATPRES`/`SATTEMP` of `psychro3.for`): without a valid sky cover the sky temperature is `TAIR − dTAirSky`.

#### Scenario: Same sky as IDA
- **WHEN** the test computes the sky temperature for KALMAR.PRN and compares it, interpolated like IDA's climate input, with the `TSKY` an IDA run wrote at its output times
- **THEN** they agree within 0.1 K

#### Scenario: Same sun as IDA
- **WHEN** the test computes the sun elevation for Kalmar at the output times of the same IDA run
- **THEN** it agrees with the `ELEVSUN` IDA wrote within 0.1°

#### Scenario: Sun at noon
- **WHEN** the sun elevation is computed over the day of the summer solstice at latitude 47.4°
- **THEN** its maximum is 90° − 47.4° + 23.45° within 0.3°

#### Scenario: Night
- **WHEN** the sun elevation is below zero
- **THEN** the global horizontal radiation is the diffuse radiation only, and never negative

### Requirement: 2D reference
`utility_functions/ground_reference.py` SHALL compute a finite-volume cross-section of half a trench cell (symmetry on both sides) from the surface down to `depth_deep_m`, with a fixed undisturbed temperature at the bottom; the surface either prescribed or through the surface balance of design G4 (linear and fast when the surface has no long-wave term); the source driven by a heat flow per trench meter or by a wall temperature behind `R_loc` (a resolved pipe without it); freezing with the liquid fraction iterated per time step (design G3: 0.01 K, damped after 5 iterations, at most 50, a step split in halves up to 64 parts, then an error). Energy SHALL be conserved.

#### Scenario: Undisturbed ground
- **WHEN** the reference runs with a prescribed annual surface wave and no source for 3 years
- **THEN** the region at 2 m depth matches the analytic undisturbed wave within 0.2 K in the third year

#### Scenario: Energy balance
- **WHEN** the reference runs one year with a heat flow series at the source, with and without freezing
- **THEN** the change of stored energy equals the heat through the source, the surface and the bottom within 0.5 % of the source's heat

#### Scenario: Freezing releases latent heat
- **WHEN** two runs extract the same heat until the region freezes, one with water content 0.25 and one with 0
- **THEN** the region with water is never colder, reaches −0.5 °C more than twice as late, and has ice

#### Scenario: Not converging
- **WHEN** a freezing step cannot converge within the allowed iterations and splits
- **THEN** the reference raises an error naming the step

#### Scenario: Linear system for the frequency fit
- **WHEN** the unfrozen reference with a linear surface is written as a linear system (`linearSystem`) and its response is taken at frequency 0 (`frequencyResponse`)
- **THEN** the heat into the fluid and from the surface equal those of a steady run within 1e-5, and the response to the wall grows with the frequency

### Requirement: RC fit
`utility_functions/ground_rc.py` SHALL fit the fifteen values of the six-node structure (design G5) in the frequency domain to the heat flow into the fluid of the unfrozen 2D reference (`linearSystem`, `frequencyResponse`), as a response to the outside and to the wall temperature over periods from 2 hours to 2 years and the steady state, with the given surface linearized and a regularization toward the geometric guess (design G7), and return them with the largest error of each response relative to its largest value, the steady error, a fingerprint and the flag `accepted` (response errors ≤ 15 %, steady error ≤ 1 %). The fingerprint SHALL change when the geometry, the soil, the surface, the fit settings or `FIT_VERSION` change, and only then.

#### Scenario: Presets accepted
- **WHEN** each of the four presets is fitted with default soil
- **THEN** every fit is accepted and all fitted values are positive

#### Scenario: Robust
- **WHEN** the horizontal ring is fitted twice, once with a soil 0.3 K warmer
- **THEN** both fits' responses to the wall temperature differ by less than 2 % of their largest value

#### Scenario: Not accepted
- **WHEN** a fit's error exceeds the limits
- **THEN** the result is returned with `accepted` false and its errors, not raised

#### Scenario: Fingerprint
- **WHEN** the same geometry, soil and surface are fitted twice, and then once with another trench spacing, another soil or another surface heat transfer
- **THEN** the first two fingerprints are equal and the others differ

### Requirement: Python ground model and start state
`ground_rc.py` SHALL hold a ground model of one section (the six fitted nodes with freezing on the loc, near, top2 and far nodes, and the `GroundSurface` balance of design G4 or a prescribed surface temperature) driven at the pipe wall by a heat flow or a wall temperature, with the contract's equations. `startState` SHALL return the start values of the six nodes and the surface: either the analytic undisturbed profile at the node depths, or the state after the given number of years (default 5) of the repeated climate year with the wall at the mean fluid temperature behind the wall and a nominal convection resistance. The result SHALL depend only on its inputs.

#### Scenario: Reproducible
- **WHEN** `startState` is called twice with the same inputs
- **THEN** both results are identical

#### Scenario: Cold fluid lowers the start state
- **WHEN** the pre-calculated start state is computed with a mean fluid temperature of 2 °C and with the undisturbed option
- **THEN** the loc node of the pre-calculated state is colder than the undisturbed one

#### Scenario: Close to the reference
- **WHEN** the ground model and the 2D reference run three years with the same surface and the same wall temperature, for each preset in seasonal operation and with daily cycling
- **THEN** the heat into the fluid of the third year is within ±3 %, its winter heat within ±7 %, and its hourly RMS deviation within 10 % (seasonal) and 40 % (daily cycling) of the mean heat flow

#### Scenario: Frozen winter
- **WHEN** both run two years with −4 °C at the wall from November to March, the soil with water
- **THEN** both freeze, and the winter heat of the second year is within ±7 %

### Requirement: Validation cases
`districts/test/make_ground_collector_cases.py` SHALL write the validation cases of design G9 to `districts/test/data/ground_collector_cases/`, one folder per case with `case.json` (inputs, fitted parameters, start state, site, contract and fit version) and `series.csv.gz` (per hour the wall temperature and weather including `TSky`, the outputs of the Python ground model and of the 2D reference with the full surface balance), for a real climate year run three times with the third stored. The cases SHALL cover the four presets in seasonal operation, the horizontal ring with freezing and a wall temperature step. The design SHALL document the analytic pipe cases (delay, constant wall temperature, zero flow, energy balance) for the Modelica model.

#### Scenario: Cases current
- **WHEN** the test recomputes the Python model's columns of each case from its stored inputs and start state
- **THEN** they equal the stored columns within 0.002, and each case names the current contract and fit version and an accepted fit

#### Scenario: Close to the reference with the full balance
- **WHEN** the test compares the stored model and reference heat flows of each case
- **THEN** they agree within ±3 % over the year and, except for the wall step, within ±7 % in winter
