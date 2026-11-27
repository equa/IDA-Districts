## MODIFIED Requirements

### Requirement: Statics parameters
The project DB SHALL have a table `public.statics_parameters` (key, value, unit, description, source), created by `upgrade.upgradeProjectDB` with the defaults `bend_ignore_deg` 1, `kink_max_deg` 5, `bend_radius_factor` 1.5, `elastic_radius_factor` 1000, `merge_distance_m` 5 and `snap_tolerance_m` 0.5, and the solver keys of change statics-steel-solver (design values, soil, friction, limits, pads, solver settings) with their defaults and sources. A missing key SHALL be added with its default and source; an existing value SHALL NOT be overwritten. A key whose source is "to be confirmed" SHALL keep that text until the user changes it. The user SHALL edit the values in a table dialog.

#### Scenario: Defaults created
- **WHEN** a project without `statics_parameters` is loaded
- **THEN** the table holds the six model keys and the solver keys with their default values and sources

#### Scenario: User value kept
- **WHEN** the user has set `kink_max_deg` to 4 and the project is loaded again
- **THEN** `kink_max_deg` is still 4

#### Scenario: Project from before the solver
- **WHEN** a project with the six model keys and no `source` column is loaded
- **THEN** the table has the column `source` and the solver keys, and the six model keys keep their values

### Requirement: Overrides by location
`statics_points` (kind fixed_point, compensator, one_time_compensator, valve or bend; bend class, radius, maximum travel, spring rate, bellows area, note) and `statics_sections` (cover, soil unit weight, friction angle, friction coefficient as the upper value, lower friction coefficient, groundwater depth, traffic load, laying temperature, laying method, prestressed legs, preheating temperature, design temperature, design pressure, note) SHALL be matched at every build by location: a point to the only model node within `snap_tolerance_m`, a section to every model section whose midpoint lies within `snap_tolerance_m` of it. An override with a bend class SHALL replace the rule's class (source override); the values of a matched override SHALL be stored in the model rows. A point with two or more nodes within the tolerance SHALL NOT be applied. Unmatched and ambiguous overrides SHALL be kept and listed in the report. Loading an existing version SHALL add the new columns without changing existing rows.

#### Scenario: Override survives a new topology
- **WHEN** a bend override lies 0.2 m from a vertex and the network topology is generated again with new line ids
- **THEN** the next build applies it to the vertex at the same place

#### Scenario: Ambiguous point
- **WHEN** a point override has two vertices within 0.5 m
- **THEN** it is not applied and the report lists it as ambiguous

#### Scenario: Unmatched override
- **WHEN** a section override lies 3 m away from every line
- **THEN** it is not applied, it is still in `statics_sections` and the report lists it

#### Scenario: Cover override
- **WHEN** a section override with cover 0.6 m covers a section
- **THEN** the pipe rows of that section have cover 0.6 m

#### Scenario: Solver values stored in the model
- **WHEN** a section override with design temperature 90 °C and laying method thermal_prestress covers a section
- **THEN** that model section holds 90 °C and thermal_prestress, and editing the override afterwards makes the model state out of date

#### Scenario: Old override table
- **WHEN** a version whose `statics_sections` has one row from before this change is loaded
- **THEN** the table has the new columns, empty for that row, and the row's other values are unchanged
