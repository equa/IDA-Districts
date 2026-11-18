## Context

The economic evaluation (`network_economics.evaluateVersion`, change network-cost-data) values the pipe losses with
one price curve per scenario, c(T_supply) for heat and cold, since change cost-optimization D23 per step and pair in
the mode the plants' heat flows give. Pumps are counted from the output `ppump_*` (change pump-power-outputs), which
introduced the pattern this change repeats: a list per project of components found in the templates, written as
outputs and loaded into result tables. The plants' and customers' energy use is not requested: the plant templates of
the local projects contain `BOIL1CIRC` (heat `Q`, energy input `QSUP` = Q / `BOILEFF`; used for boilers and for
purchased waste heat), `GHX_SLIN` (borehole field, no purchased energy) and, mostly in customer templates, `HP_B2B` /
`HP_B2B_` (heat pumps, `P_el_total`). Decision session of 2026-11-18, decisions T1–T6.

The change runs on QGIS 3.44 (Qt5) and 4.2 (Qt6); the new dialog uses the enums of `utility_functions/compat.py`
like the network pump dialog.

## Goals / Non-Goals

**Goals:**
- The energy the plants and customers buy, per component, hour and carrier, as a requested output (T2).
- The NPV from the simulated energy costs, for the network operator or the whole system (T4, T5).
- A price per kWh of pipe loss from the marginal plant of the hour, for the cost model and the report (T1, T5).
- One evaluation in the cost optimization, its report and the network report (T6).

**Non-Goals:**
- Development stages of a network (separate change, review point 4).
- Estimating in the cost model how a pipe change alters the customers' energy (only the simulated evaluation sees it).
- Free carrier names or several fuels with different prices (T3: three fixed carriers).
- Components inside macros of a template (`.idm` files other than the template file): warned, as for the pumps.

## Decisions

**D1 – Energy-use list per project (T2).** `<project>\energyUse.json` with entries {feature (customer,
energy_plant), template, component, type, variable, carrier, name, source (found, user)} and the removed keys, like
`networkPumps.json` (`network_pumps.py`, `template_graph.py`). Detection by component type: `BOIL1CIRC` → `QSUP`,
carrier fuel; `HP_B2B`, `HP_B2B_` → `P_el_total`, carrier electricity; the type table is one constant. Per project, not
per version, like the pump list: it describes the project's templates. *Alternative:* columns in the template tables:
the entries are per component, and the pump list already shows the shape.

**D2 – Carriers (T3).** Fixed: `electricity`, `fuel`, `purchased_heat`. Detection proposes one; the dialog changes it
(a `BOIL1CIRC` that stands for waste heat becomes purchased heat). The optional name is shown in the report only.

**D3 – Outputs and tables.** Requested-output keys `energy_ep`, `energy_c`; the template writer adds the variables of
the list's entries to the output file of the template, as for `ppump` (`templateFiles.py`); loading writes
`energy_plant_s_energy` / `customer_s_energy` (fid, component, carrier, time, "$energy" W, geom), like
`*_s_ppump`. Components already in the pump list keep their pump output; an entry whose component is also a pump
entry is shown with a warning in the dialog (double counting). The period run keeps the tables (`KEPT_PREFIXES`);
the cost optimization adds both keys to its outputs.

**D4 – Scenario (T3, T4).** `price_groups` gets the groups `fuel` and `purchased_heat` (start price €/kWh, escalation,
price levels as the other groups); electricity keeps its hourly profile. `economic_scenarios.system_boundary` text
('operator' | 'system'); default 'system' when a customer template has an `HP_B2B*` entry, else 'operator'. Old
projects: `upgrade.py` (at every version load, `ensureEconomicTables`) adds the column and the two groups to each
scenario without a price, the evaluation names a carrier without a price.

**D5 – NPV from the energy (T5).** Yearly cost of year 0 per carrier c: C_c,0 = Σ_h w_h · E_c,h · p_c · s_h (s_h the
electricity profile, 1 for the other carriers), E_c,h the energy of all entries of carrier c of the plants (and of the
customers for 'system'). NPV parts `plant_energy`, `customer_energy` with the present-value factor of the carrier's
price group; they replace `heat_losses` and `cold_losses`, which stay as information. With energy results missing for
a version, the evaluation falls back to the price curves and the report says so. Iteration files of earlier runs keep
their parts; the report shows them as saved and notes the different basis when the runs are compared.
*Alternatives:* keep the loss pricing and show energy as KPI (system boundary ineffective); both in the NPV with the
losses taken out of the energy (an estimate that can count twice).

**D6 – Marginal price (T1, T5).** Per hour and pair: the plants putting heat into the pair above a threshold (default
5 % of each plant's peak heat flow, a setting of the scenario) are running; each has the specific cost
Σ_c E_c,h · p_c · s_h / Φ_plant,h; the most expensive is marginal. A kWh of pipe loss in that hour costs that price
(heating), a kWh taken up in a cooling hour likewise with the cooling plant. Used by the cost model's ΔNPV (instead
of the price curves) and by the report's table of the pipe heat flows. A pair without a running plant with energy
entries falls back to the curves. *Alternatives:* heat-weighted average (underestimates peak hours); merit order set
by the user (must match the IDA control).

**D7 – Report (T6).** The evaluation is one function: the network report's economics section and the cost
optimization's report show a table of energy and costs per plant, customer (whole system) and carrier, the hours per
marginal plant, and in the equations C_c,0 and the marginal price.

## Risks / Trade-offs

- [The cost model ignores the customers' energy] → the simulated evaluation of each iteration counts it; the report
  states it; a later change may estimate it from the source temperature.
- [A carrier or component wrongly assigned (waste heat counted as fuel)] → detection proposes, the dialog shows every
  entry with its carrier before the first run, the report lists the energy per entry.
- [Double counting of a heat pump's internal pump] → warning when a component is in both lists; the user removes one.
- [NPV of existing versions changes once energy results are loaded] → the report names the basis (energy or curves).
- [Variables of a component type unknown to detection] → added by hand with component and variable, as for pumps.

## Migration Plan

`upgrade.py` adds the scenario column and price groups on version load; projects without `energyUse.json` get it from
detection when the dialog opens or the cost optimization switches the outputs on. No rollback beyond reverting the
commit; the new tables are result tables, recreated on loading.

## Open Questions

None.
