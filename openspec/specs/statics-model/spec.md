# statics-model Specification

## Purpose
Mechanical network model of a version for the pipe statics (EN 13941 / AGFW FW 401): route nodes, sections, bends, pipe rows with dimensions and cover, overrides by location, model state, report and map. Created by archiving change statics-model.
## Requirements
### Requirement: Model tables of a version
Every version SHALL have the tables `statics_model_nodes`, `statics_model_sections`, `statics_model_pipes`, `statics_model_build`, `statics_points` and `statics_sections`. New versions SHALL get them from `DB_versionTablesDefault.txt`; loading an existing version SHALL create the missing ones (`upgrade.upgradeVersionDB`) without changing existing rows. A child version SHALL get them, with their rows, through the schema copy.

#### Scenario: Old version loaded
- **WHEN** a version created before this change is loaded
- **THEN** the six tables exist afterwards and the version's other tables are unchanged

#### Scenario: Child version
- **WHEN** a child version is created from a version with a built model and two overrides
- **THEN** the child version has the same model rows, the same build row and the same two overrides

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

### Requirement: Build the model
"Build statics model" SHALL replace the rows of `statics_model_nodes`, `statics_model_sections` and `statics_model_pipes` of the loaded version in one transaction. Every line with a pipe bundle SHALL give one node per vertex and end and one section per segment between two nodes; a line end at a junction SHALL be the junction's node, with its junction type. Each pipe of the bundle SHALL get one pipe row per section with its pipe id, system type, inner diameter, steel outer diameter, wall thickness, casing diameter, offset x and cover; two sequences with the same `casing_construction_id` SHALL be one twin row with both pipe ids and one casing. A failed build SHALL leave the previous model unchanged. `statics_points` and `statics_sections` SHALL NOT be changed by a build.

#### Scenario: Single pipes
- **WHEN** a line with three vertices has a bundle of two single pipes (supply and return)
- **THEN** the model has 2 sections for the line and 4 pipe rows, two per section

#### Scenario: Twin pipe
- **WHEN** a line has a bundle whose two sequences share one casing construction
- **THEN** each section of the line has one pipe row marked twin with both pipe ids and the casing diameter of that construction

#### Scenario: Dimensions from the construction
- **WHEN** a pipe has inner diameter 0.0703 m and a construction whose first layer is 2.9 mm steel and whose layers end at a casing of 0.140 m
- **THEN** its pipe rows have the steel outer diameter 0.0761 m, wall 0.0029 m and casing diameter 0.140 m

#### Scenario: Line skipped
- **WHEN** a line has no pipe bundle, or a pipe of its bundle has no construction
- **THEN** the line has no pipe rows and the report names it with the reason

#### Scenario: Failed build
- **WHEN** a build fails after the old model rows were deleted
- **THEN** the old model rows are still there

### Requirement: Cover
The cover of a pipe row SHALL be `bundle_pipes.y` minus half the casing diameter (for a twin: from the midpoint of its two pipes), unless a `statics_sections` override with a cover applies. A cover below zero SHALL be listed in the report.

#### Scenario: Cover from the bundle
- **WHEN** a single pipe has y = 1.0 m and a casing of 0.200 m
- **THEN** its cover is 0.9 m

#### Scenario: Negative cover
- **WHEN** a pipe has y = 0.1 m and a casing of 0.250 m
- **THEN** its cover is −0.025 m and the report lists the line

### Requirement: Bend classification
Each vertex node that is not at a junction SHALL get its 3D angle between the adjacent segments and a bend class by the parameters: below `bend_ignore_deg` none; for rigid pipes up to `kink_max_deg` a small-angle kink, above it a prefabricated bend with radius `bend_radius_factor` × steel outer diameter; for flexible and bare plastic pipes an elastic bend. A pipe without a series SHALL count as rigid and SHALL be named in the report. Each node SHALL record the source of its class: rule, merge or override.

#### Scenario: Height difference counts
- **WHEN** a vertex is straight in plan but the segments rise 0 % and 10 % to it and from it
- **THEN** its angle is about 5.7° and, for a rigid pipe with defaults, its class is prefabricated bend

#### Scenario: Small angle
- **WHEN** a vertex of a rigid line has an angle of 3°
- **THEN** its class is small-angle kink with source rule

#### Scenario: Ignored angle
- **WHEN** a vertex has an angle of 0.5°
- **THEN** its class is none

#### Scenario: Plastic pipe
- **WHEN** a vertex of a line with a flexible pipe has an angle of 20°
- **THEN** its class is elastic bend

### Requirement: Merge of small kinks
A run of consecutive vertices of a line, each with an angle up to `kink_max_deg` and spaced at most `merge_distance_m`, with a total deflection of at least `bend_ignore_deg`, SHALL become one elastic bend with radius = mean spacing of its vertices / mean angle per vertex (in rad), source merge. For rigid pipes the run SHALL be merged only if that radius is at least `elastic_radius_factor` × steel outer diameter; otherwise its vertices SHALL keep their own classes and the report SHALL name the run. A bend radius below `min_bend_radius_m` of a pipe SHALL be listed in the report.

#### Scenario: Digitised curve
- **WHEN** a rigid DN 50 line has 10 vertices 2 m apart, each turning 0.5°
- **THEN** they form one elastic bend with radius about 229 m and source merge

#### Scenario: Run too tight for steel
- **WHEN** a rigid DN 200 line has 4 vertices 1 m apart, each turning 4°
- **THEN** they stay four small-angle kinks and the report names the run

#### Scenario: Flexible pipe bent too tightly
- **WHEN** a flexible pipe with `min_bend_radius_m` 0.8 lies in a bend with radius 0.5 m
- **THEN** the report lists the pipe and the bend

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

### Requirement: Model state
The build SHALL store a fingerprint of its inputs (lines, junctions, the bundle rows and pipe data used, the parameters and both override tables) in `statics_model_build`. The model state SHALL be missing when no build exists, out of date when the fingerprint of the current inputs differs, and current otherwise. Code that uses the model SHALL refuse a model that is not current.

#### Scenario: Line edited
- **WHEN** a vertex of a line is moved after a build
- **THEN** the model state is out of date

#### Scenario: Override edited
- **WHEN** an override is added after a build
- **THEN** the model state is out of date

#### Scenario: Nothing changed
- **WHEN** the version is reloaded without edits after a build
- **THEN** the model state is current

### Requirement: Report and map
After a build the plugin SHALL show a report with the parameter values used, the counts of nodes by class, sections and pipe rows, and the lists of skipped lines, applied, unmatched and ambiguous overrides, negative covers, runs not merged and bends below the minimum radius. It SHALL load or refresh a layer group "Statics model" with the model nodes styled by bend class, the model pipes, and the editable layers `statics_points` and `statics_sections`. Report texts SHALL be translated (de/en).

#### Scenario: Map after a build
- **WHEN** the user builds the model of a version with lines
- **THEN** the layer group "Statics model" holds four layers and the nodes layer is categorised by bend class

#### Scenario: Rebuild
- **WHEN** the user builds the model twice
- **THEN** the project has one layer group "Statics model", not two

