## ADDED Requirements

### Requirement: Requested outputs for pump power
The requested outputs dialog SHALL have the outputs "pump power" of customers (`ppump_c`) and of energy plants (`ppump_ep`). When one is set, writing the outputs SHALL add, in every template of that feature type, the power variable of each `variable` entry of the pump list to an output file `PumpPower` (column name = component) and SHALL switch on the connection mass flow and pressure outputs of that feature type for templates with an `estimate` entry. When it is cleared, the `PumpPower` entries and file SHALL be removed from the templates.

#### Scenario: Plant pump power requested
- **WHEN** the user sets "pump power" of energy plants and writes the outputs
- **THEN** each energy plant template with a `variable` entry has the output file `PumpPower` with the entry's `PPUMP`

#### Scenario: Output cleared
- **WHEN** the user clears "pump power" of customers and writes the outputs
- **THEN** no customer template has a `PumpPower` output file

### Requirement: Pump power result tables
Loading the results SHALL create the tables `customer_s_ppump` and `energy_plant_s_ppump` (fid, pump, kind, time, geom, `$ppump` in W) with one row per feature, pump entry and time step. Rows of `variable` entries SHALL hold the simulated value. Rows of `estimate` entries SHALL hold P = ṁ/ρ · max(0, p_out − p_in + Δp_int) / η from the connection's mass flow and pressures of the same time step and the entry's η and Δp_int.

#### Scenario: Measured pump
- **WHEN** an energy plant with one `PUMP` entry was simulated with `ppump_ep`
- **THEN** `energy_plant_s_ppump` has one row per time step for that plant and pump with kind `variable` and the simulated `PPUMP`

#### Scenario: Estimated heat pump primary pump
- **WHEN** a customer with an `estimate` entry (η 0.5, Δp_int 20 kPa) has a mass flow of 0.2 kg/s and p_out − p_in = 30 kPa in a time step (ρ 1000 kg/m³)
- **THEN** its row in `customer_s_ppump` for that time step has kind `estimate` and `$ppump` 20 W

#### Scenario: Changed efficiency
- **WHEN** the user changes η of an `estimate` entry and loads the results again
- **THEN** the rows of that entry are calculated with the new η

### Requirement: Requested outputs of existing projects
Reading a project's `requestedOutputs.txt` SHALL fill keys missing in the file with `False` from the plugin's template, and the check of simulated outputs SHALL treat a missing key as `False`.

#### Scenario: Project from before this change
- **WHEN** a project whose `requestedOutputs.txt` has no `ppump_c` or `ppump_ep` is loaded, simulated and its results loaded
- **THEN** no error occurs and no pump power is written or loaded
