## 1. Energy-use output

- [x] 1.1 `utility_functions/energy_use.py`: list `energyUse.json` (load, save, entry key, removed keys), detection by component type (`BOIL1CIRC` → `QSUP` fuel, `HP_B2B*` → `P_el_total` electricity) with `template_graph.parseTemplate`, macro warning
- [x] 1.2 Dialog 'Energy use' like the network pump dialog: table with carrier dropdown and name, remove, add from a template's components and variables, warning for components in the pump list; button next to the network pumps
- [x] 1.3 Requested outputs `energy_ep`, `energy_c` (files.py FEATURE_OUTPUTS, requested-output dialog), variables written into the template output files (`templateFiles.py`)
- [x] 1.4 Loading: `energy_plant_s_energy`, `customer_s_energy` (fid, component, carrier, time, $energy, geom) in `load_results.py`; kept by the period run; switched on by the cost optimization
- [x] 1.5 Carrier `ambient` (free energy from the surroundings; free unless priced, never named as unpriced), labels shared in `energy_use.CARRIER_LABELS`
- [x] 1.6 Delivered heat and cold (D8): kind `delivered`, customer heat exchangers (`|hx|`, `|PhiHx|`) detected as delivered (e.g. the direct cooling of low_temperature_network), not priced, report table with the NPV per MWh delivered

## 2. Scenario

- [x] 2.1 `economic_data.py`: price groups `fuel`, `purchased_heat` in new scenarios, `system_boundary` column with its default, marginal threshold setting; `upgrade.py` for old projects; scenario dialog fields

## 3. Evaluation and cost model

- [x] 3.1 `network_economics.py`: energy per carrier and step from the tables (sources of a period run), C_c,0 per carrier with the electricity profile, NPV parts `plant_energy`, `customer_energy` replacing the loss parts, fallback to the price curves, carriers without a price named
- [x] 3.2 Marginal plant per step and pair (heat flow per plant from `mdot_ep`/`temp_ep` grouped by plant, threshold, specific cost) in `network_modes.py` or a new module; used for the loss table
- [x] 3.3 `cost_model.py` / `cost_model_data.py`: ΔNPV of the loss change with the marginal price per step instead of the price curves (fallback per pair)
- [x] 3.4 `cost_optimization.py`: NPV parts and the record of the iteration (`npvRecord`, `economics.npvTerms` with carriers), the outputs switched on

## 4. Reports

- [x] 4.1 `iteration_report.py`: equations (C_c,0, marginal price), energy and costs per plant, customer and carrier, hours per marginal plant, basis named; earlier iteration files shown with their parts
- [x] 4.2 Network report (`reports.py`): energy table and the same NPV basis

## 5. Tests

- [x] 5.1 Unit tests: detection and list (synthetic templates), carrier cost of year 0 with the profile, marginal plant with threshold, NPV parts and fallback
- [x] 5.2 e2e: upgrade of an old project (groups, column), synthetic energy tables in the evaluation (plant and system boundary), report sections
- [x] 5.3 ida: a run with `energy_ep` on (dynamic_optimization template), `energy_plant_s_energy` filled and the NPV from the energy

## 6. Translations, documentation, validation

- [x] 6.1 tr_msg texts with German translations, de/en compiled
- [x] 6.2 README.md and CLAUDE.md: energyUse.json, the energy outputs and tables, the NPV basis; the requirements of network-cost-data (network-economics) and cost-optimization (cost-model) updated in their changes
- [ ] 6.3 Local validation: from districts/, the QGIS Python runs `-m pytest` and it passes on 3.44 and 4.2 (with `-m "not ida"` without IDA Districts), including test_static_mypy.py and test_messages.py
- [ ] 6.4 CI: commit, push to dev and watch the plugin-tests run until both QGIS jobs pass
