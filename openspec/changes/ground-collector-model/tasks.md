## 1. Inputs from IDA

- [x] 1.1 Get the equations of IDA's `ENVIRONMENT` model for `TSKY` and `ELEVSUN` (user) and note their source in design G4
- [x] 1.2 Export a short hourly series (`TAIR`, `RELHUM`, `IDIRNORM`, `IDIFFHOR`, `TSKY`, `ELEVSUN`, site) from an IDA run's `climate_processor` into `districts/test/data/ground_climate_ida.csv` (KALMAR.PRN; ELEVSUN within 0.0005°)

## 2. Contract and geometry

- [x] 2.1 `utility_functions/ground_collector_contract.py`: `CONTRACT_VERSION = 1`, parameters (six nodes, 15 fitted values, start values, freezing nodes), inputs, outputs and ports of `GroundCollector` and `GroundSurface` (design G4, G8)
- [x] 2.2 `utility_functions/ground_collector_geometry.py`: `CollectorGeometry` (with `pipe_resolved`), `SoilProperties`, `SurfaceProperties`, input checks (design G2, G3)
- [x] 2.3 Presets horizontal ring, vertical ring, flat meander, bare pipe (no return pipe; regions widened to one cell; the bare pipe resolved)

## 3. Climate signals

- [x] 3.1 `utility_functions/ground_climate.py`: sun elevation, sky temperature with IDA's equations (`SATPRES`/`SATTEMP`), global horizontal radiation from climate columns and site

## 4. 2D reference

- [x] 4.1 `utility_functions/ground_reference.py`: non-uniform grid of half a trench cell (1 cm cells at a resolved pipe), implicit Euler with scipy.sparse, bottom at the undisturbed temperature
- [x] 4.2 Surface prescribed or through the G4 balance (linear path without the long-wave term); source by heat flow or by wall temperature behind `R_loc`; steady state as one long step
- [x] 4.3 Freezing with the liquid fraction iterated (Swaminathan and Voller), damping, step splitting, error after 64 parts; ice fraction output

## 5. RC fit, ground model, start state

- [x] 5.1 `utility_functions/ground_rc.py`: six nodes with freezing on loc, near, top2 and far, the surface node with the G4 balance, driven by wall heat flow or wall temperature (G5, G9)
- [x] 5.2 Frequency fit of the fifteen values to the heat into the fluid with the linearized surface (`linearSystem`, `frequencyResponse`), regularization, 9 starts; response and steady errors, `accepted`, fingerprint with surface and `FIT_VERSION` (G7)
- [x] 5.3 `startState`: undisturbed profile, or k years with the wall at the mean fluid temperature and a nominal convection resistance (G9)

## 6. Validation cases and pipe cases

- [x] 6.1 `districts/test/make_ground_collector_cases.py` writing `case.json` and `series.csv.gz` per case on the Kalmar year (two years run-in, the third stored) to `districts/test/data/ground_collector_cases/`
- [x] 6.2 Generate and commit the cases; check that the analytic pipe cases in design G9 have their expected values written out for the Modelica developer

## 7. Tests

- [x] 7.1 `test/test_ground_collector_geometry.py`: presets (loop lengths, regions, widening, resolved pipe, local spacing from the pipe density, invalid inputs), the contract against the ground model's parameters, import without QGIS
- [x] 7.2 `test/test_ground_climate.py`: saturation pressure, sky temperature against the IDA series (0.1 K), cloud cover, sun at noon, ELEVSUN against IDA (skipped until exported), radiation at night
- [x] 7.3 `test/test_ground_reference.py`: undisturbed wave at 2 m, energy balance with and without freezing, latent heat slows the cooling, wall source, non-converging freezing raises, inputs checked, linear system and frequency response against a steady run
- [x] 7.4 `test/test_ground_rc.py`: four presets accepted, robust against a soil change, not-accepted result, fingerprint, linear surface, model against the reference per preset (annual ±3 %, winter ±7 %, RMS 10 % / 40 %), frozen winter ±7 %, start state, inputs checked
- [x] 7.5 `test/test_ground_collector_cases.py`: all cases present, model columns current, contract and fit version, model against the reference with the full balance (annual ±3 %, winter ±7 %)

## 8. Documentation and validation

- [x] 8.1 README.md and CLAUDE.md: the ground collector modules, the contract, the validation cases and the generator script
- [x] 8.2 Local validation: from `districts/` the QGIS Python runs `-m pytest -m "not ida"` and it passes, including `test_static_mypy.py` (new modules clean) and `test_messages.py` (528 passed; 2 AI-tab tests failed only from a pydantic-core mismatch in this PC's QGIS 4.2.0 Python, green on the runner)
- [x] 8.3 `npx openspec validate --all`; commit the change's artifacts with the code, push to dev and watch the plugin-tests run (`gh run watch`) until both QGIS jobs pass (validate: 21 passed, 0 failed; fd44687 run #49 green on QGIS 4.2)
