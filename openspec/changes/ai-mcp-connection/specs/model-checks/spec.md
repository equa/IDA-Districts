## ADDED Requirements

### Requirement: Findings
`run_checks(version, scope)` with scope `all`, `qgis`, `templates` or `results` SHALL run the rules of that scope and return a list of findings `{rule, severity, feature_type, feature_id or component, values, text}` with severity `error`, `warning` or `info`. `text` SHALL come from `tr_msg` and have a German translation; `values` SHALL hold the measured value, the threshold, its unit and its source (project, setting or default). The same version and data SHALL give the same findings.

#### Scenario: Scope
- **WHEN** `run_checks` is called with scope `qgis`
- **THEN** only rules of the scope qgis run

#### Scenario: Threshold named
- **WHEN** a line exceeds the default velocity limit
- **THEN** the finding's values hold the velocity, 3 m/s, the unit and the source `default`

### Requirement: Wrapped existing checks
The rules SHALL include the existing checks: network topology, unconnected features, missing heights, the energy-use and pump-list detection warnings, the errors of the IDA runs (`result.json`) and the comfort deficits (degree hours against the setpoint). A check that today only builds layers or dialog text SHALL return its result as data, and its layer or dialog SHALL be built from that data with unchanged content.

#### Scenario: Unconnected customer
- **WHEN** a customer is not connected to the network
- **THEN** a finding of the topology rule names the customer's id

#### Scenario: Height check unchanged
- **WHEN** the height check runs from its dialog after the change
- **THEN** it builds the same layers as before

### Requirement: Missing outputs
A result rule whose result tables or columns are missing SHALL NOT pass silently: it SHALL return one `info` finding `outputs_missing` naming the requested outputs to switch on.

#### Scenario: No line pressures
- **WHEN** a version has results but no `line_s_p` table
- **THEN** `run_checks` returns `outputs_missing` naming the line pressure output and no `pipe_pressure_limit` finding

### Requirement: Pipe and line rules
The rules SHALL report: a line without pipe or a pipe without diameter, roughness or u-value (`pipe_data_missing`, error); a line whose maximum pressure exceeds `pipes.p_max_bar` (`pipe_pressure_limit`, error; skipped when empty); a line whose velocity at peak exceeds v_max (`line_velocity_high`, warning) or whose pressure loss per metre at peak exceeds the limit (`line_dp_spec_high`, warning). v_max and the limit SHALL be the values given to `run_checks` as thresholds, else 3 m/s and 300 Pa/m.

#### Scenario: Pressure above rating
- **WHEN** a line's simulated pressure reaches 17 bar and its pipe has `p_max_bar` 16
- **THEN** `pipe_pressure_limit` reports the line with 17 bar against 16 bar

#### Scenario: Velocity limit given
- **WHEN** `run_checks` gets the threshold v_max 2 m/s and a line reaches 2.4 m/s at peak
- **THEN** `line_velocity_high` reports it with the source `argument`

### Requirement: Substation rules
At a customer's load hours (heat flow above 10 % of its peak), the rules SHALL report: a mean ΔT below 15 K for heating or 4 K for cooling (`delta_t_low`, warning); a Δp across the customer below the template or customer value, else 0.5 bar (`substation_dp_low`, warning); a supply temperature below the required supply temperature of the template or customer (`supply_temp_low`, warning). Without a required supply temperature, `supply_temp_low` SHALL return one `info` finding "no required supply temperature" and no warning.

#### Scenario: Poor substation
- **WHEN** a heating customer's mean ΔT at load hours is 9 K
- **THEN** `delta_t_low` reports the customer with 9 K against 15 K

#### Scenario: Standstill ignored
- **WHEN** a customer's ΔT is 2 K only in steps below 10 % of its peak heat flow
- **THEN** no `delta_t_low` finding is reported for it

#### Scenario: No required supply temperature
- **WHEN** neither the template nor the customer holds a required supply temperature
- **THEN** `supply_temp_low` returns one info finding and no warning

### Requirement: Plant rules
The rules SHALL report a plant whose power exceeds its nominal power (`plant_power_high`, warning; skipped without nominal power) and a plant whose power never exceeds 1 % of the peak over the results (`plant_never_runs`, warning).

#### Scenario: Idle plant
- **WHEN** a second plant delivers no heat in any step
- **THEN** `plant_never_runs` reports it
