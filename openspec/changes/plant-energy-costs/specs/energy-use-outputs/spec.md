## ADDED Requirements

### Requirement: Energy-use list per project
The plugin SHALL keep a list of the components of the plant and customer templates that buy energy in `<project>\energyUse.json`, each entry with feature, template, component, component type, variable, carrier (electricity, fuel, purchased heat), an optional name and its source (found, user). Detection SHALL propose entries by component type: `BOIL1CIRC` with `QSUP` and carrier fuel, `HP_B2B` and `HP_B2B_` with `P_el_total` and carrier electricity. Entries the user removed SHALL not be proposed again.

#### Scenario: Detection in a plant and a customer template
- **WHEN** a project has a plant template with a `BOIL1CIRC` and a customer template with an `HP_B2B`
- **THEN** the list proposes `BOIL1CIRC` / `QSUP` / fuel and `HP_B2B` / `P_el_total` / electricity

#### Scenario: Removed entry
- **WHEN** the user removes a proposed entry and detection runs again
- **THEN** the entry stays removed

### Requirement: Energy-use dialog
A dialog SHALL show the list with every entry's template, component, variable, carrier and name, let the user change the carrier and the name, remove entries and add an entry from the components and variables of a template. An entry whose component is also an entry of the network pump list SHALL be shown with a warning.

#### Scenario: Waste heat
- **WHEN** the user sets the carrier of a proposed `BOIL1CIRC` entry to purchased heat
- **THEN** the list saves the entry with carrier purchased heat

#### Scenario: Component in both lists
- **WHEN** an entry's component is also in the network pump list
- **THEN** the dialog marks the entry with a warning about double counting

### Requirement: Energy-use outputs and result tables
The requested outputs `energy_ep` and `energy_c` SHALL write the variables of the list's entries into the output files of the templates; loading the results SHALL fill `energy_plant_s_energy` and `customer_s_energy` with feature id, component, carrier, time and power [W]. The cost optimization SHALL switch both outputs on with its other outputs, and a period run SHALL keep both tables per week.

#### Scenario: Simulated energy
- **WHEN** a version with the output `energy_ep` on and a list entry for its plant's boiler is simulated and loaded
- **THEN** `energy_plant_s_energy` has a row per time step with the boiler's `QSUP` and carrier fuel
