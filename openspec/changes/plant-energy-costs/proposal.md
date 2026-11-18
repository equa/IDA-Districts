## Why

The NPV prices the heat and cold lost by the pipes with one price curve per scenario, c(T_supply), whatever produces
the heat. With several plants (heat pump and boiler, waste heat, borehole field) and in low-temperature networks with
decentral heat pumps, the cost of a kWh depends on the generator and the hour, and the decentral heat pumps' electricity,
often the largest operating cost, is not counted at all (review of 2026-11-18). The simulation knows the energy the
plants and customers use; the plugin does not request it yet.

## What Changes

- New requested output "energy use" of energy plants and customers: a list per project (`energyUse.json`, like
  `networkPumps.json`) of the components that buy energy, each with its variable and carrier (electricity, fuel,
  purchased heat, ambient: free energy from the surroundings) and an optional name; detection proposes entries (`BOIL1CIRC` → `QSUP` fuel, `HP_B2B*` →
  `P_el_total` electricity); a dialog adds, removes and changes entries; the variables are written as outputs into the
  templates; loading fills `energy_plant_s_energy` and `customer_s_energy`.
- Economic scenarios: price groups "fuel" and "purchased heat" (start price, escalation, price levels); a setting
  "system boundary" (network operator / whole system).
- **BREAKING** (NPV composition): with energy results the NPV contains the simulated energy costs per carrier of the
  plants and, for the whole system, of the customers, instead of the priced pipe losses (parts `plant_energy`,
  `customer_energy` replace `heat_losses`, `cold_losses`). Without energy results the price curves stay as fallback,
  named in the report. Iteration files of earlier runs keep their parts.
- Marginal price per hour and pair: energy cost / heat delivered of the most expensive plant running above a threshold
  (default 5 % of its peak); used by the cost model for the ΔNPV of a pipe change and by the report's table of the pipe
  heat flows.
- The cost optimization switches the output on with its other outputs; the period run keeps the new tables.
- One evaluation everywhere: cost optimization, its report and the network report's economics section, with a table of
  energy use and costs per plant, customer and carrier.

## Capabilities

### New Capabilities
- `energy-use-outputs`: the list of energy-using components per project (detection, carriers, dialog), the outputs
  written into the plant and customer templates and the result tables.
- `energy-costs`: carrier prices and system boundary of the scenario, the NPV from the simulated energy costs, the
  marginal price per hour and pair, the fallback and the report tables.

### Modified Capabilities
<!-- The economics (network-economics of change network-cost-data) and the cost model (cost-model of change
     cost-optimization) are not archived yet: their spec texts are updated in those changes when this one is applied. -->

## Impact

- New: `utility_functions/energy_use.py` (list, detection), a dialog like the network pump dialog, result loading in
  `load_results.py`, outputs in `utility_functions/templateFiles.py`, requested-output key `energy_ep` / `energy_c`.
- Changed: `economic_data.py` (price groups, system boundary column; `upgrade.py` for old projects),
  `network_economics.py` and `economics.py` (NPV parts), `cost_model.py` / `cost_model_data.py` (marginal price),
  `cost_optimization.py` (outputs, NPV parts), `iteration_report.py`, `reports.py`, `representative_periods.py`
  (kept tables), translations, tests.
- Runs on QGIS 3.44 and 4.2; no new dependency.
