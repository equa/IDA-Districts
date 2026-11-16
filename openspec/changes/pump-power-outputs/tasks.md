## 1. Template graph and detection

- [x] 1.1 Module `utility_functions/template_graph.py`: read a template `.idm` into components, fluid sides and links; only links between fluid ports; sides liqA/liqB, evap/cond, tank IN/OUT vs. coil HXIN/HXOUT; other components one side
- [x] 1.2 Detection: start nodes Flowmeter2 / PMT2mux of the template, reachable PUMP/PUMPMCTRL/PUMPCIRC → entry kind `variable` with `PPUMP` (estimate entries only by the user); warning for a pump in a macro file of the folder
- [x] 1.3 Pump list `<project>\networkPumps.json` (feature type, template, component, kind, variable, η, Δp_int, source, removed found entries): read, write, merge a new detection without bringing back removed entries, mark entries whose component is missing

## 2. Network pumps dialog

- [x] 2.1 Dialog "Network pumps" (QTableWidget, enums through compat.py) opened by a button in the requested outputs dialog: detect, add (component and variable combos of the template, or kind estimate), remove, edit η (default 0.5) and Δp_int (default 20 kPa), missing components greyed with a warning
- [x] 2.2 Project without `networkPumps.json`: detection when the dialog opens or when pump power outputs are first written

## 3. Requested outputs

- [x] 3.1 Keys `ppump_c` and `ppump_ep` in `config/requestedOutputs_template.txt`, the `requestedOutputs.txt` of the plugin templates, and checkboxes "pump power" in RequestedOutputs_dialog.ui / ida_mosim_dialog.py
- [x] 3.2 `loadRequestedOutputs` fills missing keys with False from the template; `checkSimOutputs` treats a missing key as False
- [x] 3.3 `updateTemplatesOutputs`: power variable of each `variable` entry to output file `PumpPower` (:AS component), removal when cleared; mdot/p of the connections switched on for templates with `estimate` entries
- [x] 3.4 `updateTemplatesOutputs`: `TSet_var` and `HCMode_var` of the load models into the `TRoom` file with `troom_c`, removed with it

## 4. Result loading

- [x] 4.1 `load_results.py`: tables `customer_s_ppump` and `energy_plant_s_ppump` (fid, pump, kind, time, geom, $ppump [W]), one row per feature, entry and time step from `PumpPower.prn`
- [x] 4.2 Estimate rows: P = ṁ/ρ · max(0, p_out − p_in + Δp_int) / η from the connection results of the same time step
- [x] 4.3 `customer_s_troom` with `$tset` and `$hcmode`; empty when the `TRoom` file of an earlier simulation has only the room temperature

## 5. Tests

- [x] 5.1 Unit tests template_graph / detection on every template `.idm` of `templates/db_default_values` (plant pumps found, building-circuit PUMP of 1_simplified_consumer not found, PUMP/PUMP1 of 4_simplified_consumer_hp found) and on the installed IDA samples `low_temperature_network` (waste heat source pump not found) and `dynamic_optimization` (pressure-holding pump found; skipped without IDA Districts)
- [x] 5.2 Unit tests pump list: merge with removed entries, missing component, defaults η and Δp_int, saved in the project folder
- [x] 5.3 Unit tests requested outputs: missing keys False, checkSimOutputs with an old file; estimate formula (0.2 kg/s, 30 kPa, Δp_int 20 kPa, η 0.5 → 20 W)
- [x] 5.4 e2e/ida test on a project from `dynamic_optimization` (skipped without it): request ppump_ep, ppump_c and troom_c, simulate 1 January, load results; energy_plant_s_ppump rows with kind variable, customer_s_troom with $tset 21 and $hcmode 1
- [x] 5.5 Local validation: from districts/, the QGIS Python runs `-m pytest` and it passes (with `-m "not ida"` when IDA Districts is not installed), including test_static_mypy.py (baseline updated only for unavoidable findings) and test_messages.py

## 6. Translations, documentation, CI

- [x] 6.1 tr_msg / tr with German translations for the dialog, the checkboxes, the warnings and the column labels; translations de/en compiled
- [x] 6.2 README.md and CLAUDE.md: the file `networkPumps.json`, the new outputs and the module template_graph.py; .github/RUNNER_SETUP.md only if the runner needs something new
- [ ] 6.3 `npx openspec validate --all`, commit the change's artifacts with the code (`*requested outputs: …` message, explicit paths), `git pull --rebase`, push to dev and watch the plugin-tests run until both QGIS jobs pass
