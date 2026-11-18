## ADDED Requirements

### Requirement: Carrier prices and system boundary
Every economic scenario SHALL have the price groups `fuel` and `purchased_heat` (start price €/kWh, escalation, price levels) next to `electricity`, and a system boundary 'operator' or 'system'. Electricity SHALL follow the scenario's hourly price profile, the other carriers SHALL have a flat price within the year. A new scenario SHALL default to 'system' when a customer template has an electricity entry in the energy-use list, else to 'operator'. Upgrading an old project SHALL add the groups without a price and the system boundary.

#### Scenario: Old project
- **WHEN** a version of a project from before this change is loaded
- **THEN** each scenario has the groups fuel and purchased heat without a price and a system boundary

### Requirement: Net present value from the simulated energy
With energy results, the yearly cost of year 0 SHALL be, per carrier, the weighted sum over the simulated steps of energy × price (× the electricity profile for electricity), of the plants and, with the system boundary 'system', of the customers; the NPV SHALL contain them as the parts plant energy and customer energy with the present-value factor of the carrier's price group, instead of the priced pipe losses. A carrier in use without a price SHALL be named. Without energy results the evaluation SHALL use the price curves and the report SHALL name that basis.

#### Scenario: Boiler and heat pump plant
- **WHEN** a version's plants used 100 MWh fuel at 0.08 €/kWh and 50 MWh electricity at a flat 0.25 €/kWh in a simulated year
- **THEN** the plant energy cost of year 0 is 20 500 € and no heat-loss part is in the NPV

#### Scenario: Operator boundary
- **WHEN** the system boundary is 'operator' and the customers' heat pumps used 200 MWh electricity
- **THEN** the NPV contains no customer energy and the report shows the customers' energy as information

#### Scenario: No energy results
- **WHEN** a version has no `energy_plant_s_energy` table
- **THEN** the pipe losses are priced with the price curves and the report says so

### Requirement: Marginal price of a pipe loss
Per step and pair, the plants putting heat into the pair above a threshold (default 5 % of their peak heat flow, a scenario setting) SHALL be running; the running plant with the highest energy cost per kWh of heat delivered SHALL set the price of a kWh of pipe loss in that step. The cost model SHALL use it for the ΔNPV of a pipe change and the report for its table of the pipe heat flows; a pair without a running plant with energy entries SHALL use the price curves.

#### Scenario: Heat pump and peak boiler
- **WHEN** in an hour a heat pump plant delivers heat at 0.06 €/kWh and a boiler plant above 5 % of its peak at 0.11 €/kWh
- **THEN** a kWh of pipe loss in that hour costs 0.11 €

#### Scenario: Boiler below the threshold
- **WHEN** the boiler runs at 3 % of its peak in that hour
- **THEN** the heat pump's 0.06 €/kWh prices the loss

### Requirement: One evaluation in all reports
The cost optimization, its report and the network report's economics section SHALL use the same evaluation and show a table of energy and costs per plant, customer and carrier, and the hours per marginal plant.

#### Scenario: Network report
- **WHEN** the network report of a version with energy results is written
- **THEN** its economics section shows the energy and cost per plant and carrier and the same NPV as the cost optimization's evaluation of that version
