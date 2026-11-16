## Why

The cost optimization (change `cost-optimization`, design D3, D4, D5, D7) needs cost and price data and a net
present value calculation. Today `pipes.costs` is NULL in every template, maintenance, lifetime and pressure rating
of pipes do not exist, trench costs are a constant per street, and there are no electricity or heat prices. A
simulated version cannot be valued economically at all, so versions cannot be compared by cost.

## What Changes

- `pipes` gets `maintenance_pct`, `lifetime_a`, `p_max_bar` and `example`; `pipes.costs` is defined as material
  and laying €/m per pipe.
- Project DB tables with named **economic scenarios** (default "base"): interest rate, period, residual value, pump
  costs (€/kW, %/a, lifetime), price per cost group (start price, escalation, optional level per year), an optional
  hourly electricity profile file, price curves c(T_supply) for heat and cold, and **trench cost curves per surface
  class** (a + b·DN).
- Streets get a surface class; a line's trench costs follow the surfaces of the streets it lies on.
- Example values from public sources (KWW-Technikkatalog Wärmeplanung 2026 and others, cited in the rows) in the
  plugin templates and for existing projects; a warning while example values are in use.
- A pure-Python module for the **net present value** (yearly cash flows, replacements, residual value, annuity) and
  a **loss module** (heat flow per pipe from U'(d), simulated pipe temperatures and the ambient).
- A section **Economics** in the network report: investment, yearly pump energy, heat and cold losses,
  maintenance, NPV split and annuity of the loaded version for a chosen scenario, from full-year results.

## Capabilities

### New Capabilities
- `network-cost-data`: pipe cost columns, trench cost curves per surface, street surfaces, example values,
  upgrade of existing projects.
- `economic-scenarios`: scenario tables, prices per cost group and year, electricity profile, price curves c(T).
- `network-economics`: the loss module, the NPV module and the Economics section of the network report.

### Modified Capabilities
<!-- none: the network report and the pipe catalog have no spec yet -->

## Impact

- `districts/DB_projectTablesDefault.txt`, `DB_versionTablesDefault.txt`, `upgrade.py`, templates
  `db_default_values`, `empty_project`, `heating_network` (and the IDA sample through the handover of
  `cost-optimization`).
- `districts.py` (table dialogs of pipes and scenarios), `utility_functions/reports.py` and the network report
  dialog (`ida_rv_dialog.py`).
- New modules for losses and economics under `utility_functions/`.
- Reads the results of change `pump-power-outputs` (`ppump_*`); without them the report names what is missing.
- Translations, unit tests, an e2e test of the report.
