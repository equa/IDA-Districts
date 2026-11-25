## 1. Generator

- [x] 1.1 `utility_functions/climate_macro.py`: `climateColumns(path)` with header detection, the IDA layout and the checks of required quantities (C1)
- [x] 1.2 `writeClimateMacro(folder, climate, settings)`: objects and connections of C2 (`.idm`), layout (`.idc`), generator marker, returned signal list
- [x] 1.3 Wind variants (direction/speed, WindX/WindY with the √ chain), extra-column gains, `albedo`, SKYCOVER and PRECIPITATION bound, `IGlob` chain, `TGround` Kusuda or constant, `TDuct` from `duct_temp`
- [x] 1.4 Backup `climate-macro.idm.bak` once over a macro without the marker (C4)

## 2. Where the macro is written

- [x] 2.1 `updateClimateTemplate`: Kusuda values, then the generated macro into the project's climate folder and every customer and plant template folder; `updateClimateMacro`, `openClimateMacro` and `macros.updateClimateMacroIdm` removed (C3)
- [x] 2.2 `invoke_network`: copies the project macro generated at the start of the build
- [x] 2.3 `supervisory_control`: copies the project macro of the last build or climate dialog
- [x] 2.4 `openTemplate` runs `updateClimateTemplate` before `WriteTemplateFiles` and before IDA opens the template
- [x] 2.5 New projects: macros generated at the first build, template opening or climate dialog (no change to `WorkerImportProject`)

## 3. UI and shipped files

- [x] 3.1 Remove the "Define climate data" button (`btn_climateTemplate`, `show_manageClimateTemplate`) from the resources tab (C4)
- [x] 3.2 Remove the 32 shipped `climate-macro.idm/.idc` files under `climate/` and `templates/`; keep the `climate.idm` system files (C5)

## 4. Python climate functions

- [x] 4.1 `ground_climate.weatherFromFile` from a file path through `climateColumns`, with sky cover and albedo from the file (C6)
- [x] 4.2 `periods.readClimate` and `calculateKusudaSettings` use `climateColumns`

## 5. Tests

- [x] 5.1 `test/test_climate_macro.py` (no DB): columns of BROMMA.PRN and ABO_dry_NORMAL.prn (test data excerpts), missing quantity refused, generated objects for both layouts, constant ground and duct temperature, backup once
- [x] 5.2 Weather with sky cover and albedo from a header file (in `test_climate_macro.py`, next to the column tests)
- [x] 5.3 Project and template folders written (fake cursor, no DB), the shading data defined in every parent, no shipped macros; the network build runs in the e2e workflow tests
- [x] 5.4 ida: a network with the generated macro for both layouts simulates; `IGlob` over the year within 1 % of the Python radiation
- [x] 5.5 Simulation tests (`simulation_tests`): their packed models carry their own climate macros and are not touched by this change; references unchanged

## 6. Translations, documentation, validation

- [x] 6.1 German translations of the new messages (columns, missing quantities, backup); de compiled
- [x] 6.2 README.md and CLAUDE.md: generated climate macro, column detection, settings that replace hand edits, removed button
- [x] 6.3 Local validation: from `districts/` the QGIS Python runs `-m pytest` (with `-m "not ida"` without IDA Districts) and it passes, including `test_static_mypy.py` and `test_messages.py` (558 passed; 2 AI-tab tests fail only from the pydantic-core mismatch of this PC's QGIS 4.2.0 Python; IDA tests: test_climate_macro_ida 2 passed)
- [ ] 6.4 `npx openspec validate --all`; commit the change's artifacts with the code, push to dev and watch the plugin-tests run until both QGIS jobs pass
