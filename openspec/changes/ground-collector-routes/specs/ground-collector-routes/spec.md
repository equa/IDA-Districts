## ADDED Requirements

### Requirement: Collector resources
The project DB SHALL hold collector resources in `public.ground_collectors` (name, preset and its inputs, loop pipe and
loop sequence, soil, surface, default loops, default mean fluid temperature, start mode and years, sections, costs per
trench and per loop meter, maintenance, lifetime, cached fits), edited in the resources tab. Each resource SHALL have
exactly one line type in `public.line_types` with the same name and `ground_collector_id` pointing to it: saving a
resource creates or renames its line type, deleting an unused resource deletes it, deleting a resource used by a line
SHALL be refused naming the lines. `upgrade.py` SHALL create the table and the column in existing projects.

#### Scenario: New resource appears as a line type
- **WHEN** a collector resource "Ring 1 m" is saved in the resources tab
- **THEN** `line_types` has a row "Ring 1 m" with `ground_collector_id` of the resource, and the `lines.type` dropdown lists it

#### Scenario: Rename keeps the link
- **WHEN** the resource is renamed to "Ring 1.2 m"
- **THEN** its line type has the new name and the same id, and lines of that type keep it

#### Scenario: Used resource is not deleted
- **WHEN** a resource whose line type is used by a line is deleted
- **THEN** the deletion is refused with a message naming the line, and resource and line type stay

#### Scenario: Old project upgraded
- **WHEN** a project without the table is opened
- **THEN** `ground_collectors` and `line_types.ground_collector_id` exist afterwards, and no line has a collector type

### Requirement: Collector routes
A line SHALL be a collector exactly when its `type` is a line type with a `ground_collector_id`. The version table
`lines` SHALL have `n_loops` and `t_mean_init`; an empty value means the resource's default. The topology generator
SHALL carry `type`, `n_loops` and `t_mean_init` to the generated lines and SHALL merge two lines only if both, their
bundle and these values are equal.

#### Scenario: Defaults from the resource
- **WHEN** a collector line has no `n_loops` and its resource has 6 loops
- **THEN** the model build and the costs use 6 loops

#### Scenario: Topology keeps the collector
- **WHEN** the topology is regenerated with a collector route between two junctions and an ordinary pipe continuing it
- **THEN** the collector line keeps its type, loops and mean temperature and is not merged with the pipe

### Requirement: RC fit cached in the resource
Before a model build the plugin SHALL fit every used collector resource whose cached fit for the current fingerprint
(resource, the project's Kusuda settings, `FIT_VERSION`) is missing, store it in the resource, and reuse it otherwise.
A fit that is not accepted SHALL stop the build with a message naming the resource and its errors. The resources tab
SHALL have a "Fit" action that fits the selected resources and shows the response errors, the steady error and the
acceptance.

#### Scenario: Fit reused
- **WHEN** a model is built twice without a change of the resource or the Kusuda settings
- **THEN** the second build runs no fit

#### Scenario: Kusuda change refits
- **WHEN** the Kusuda mean surface temperature of the project is changed and the model is built
- **THEN** the used resources are fitted again and the new fits are stored under the new fingerprint

#### Scenario: Not accepted
- **WHEN** a resource's fit is not accepted
- **THEN** the build stops with a message naming the resource and its errors, and no model is written

### Requirement: Model build of collector lines
The model build SHALL write a collector line as a `GroundCollector` "Collector_<lid>" with the resource's loop pipe,
the line's loops and length, the fitted ground values, soil and the line's liquid, a `GroundSurface`
"CollectorSurface_<lid>" connected to its `surface` port with `TAir`, `TSky` and `IGlob` bound to the climate macro and
`albedo` to the resource, and an `FDpipebundle` "Pipebundle_<lid>" with the other pipes of the bundle (none when the
bundle has only the loop pipe). Junctions, plants and customers SHALL connect the loop sequence to the collector's
`liq1`/`liq2` and the other sequences to the bundle's terminals renumbered without the loop pipe. Lines without a
collector type SHALL be written exactly as before.

#### Scenario: Collector with a four-pipe bundle
- **WHEN** a collector line has a bundle of four pipes and the resource's loop sequence is 2
- **THEN** the model has `Collector_<lid>` connected at both ends where sequence 2 connects, and `Pipebundle_<lid>` with three pipes connected where sequences 1, 3 and 4 connect

#### Scenario: Only the loop pipe
- **WHEN** the bundle of a collector line has one pipe
- **THEN** the model has `Collector_<lid>` and `CollectorSurface_<lid>` and no `Pipebundle_<lid>`

#### Scenario: Ordinary lines unchanged
- **WHEN** a project without collector lines is built
- **THEN** the written network model is the same as before this change

### Requirement: Start values
The start values of a collector SHALL be the undisturbed profile at the simulation start, or, in the pre-calculated
mode, the state after the resource's number of years of the project's climate year with the wall at the line's mean
fluid temperature. They SHALL be written as the `TStart*` parameters and as the values of the node temperatures and of
the surface temperature. A pre-calculated state SHALL be cached in the resource for its fingerprint, mean
temperature, years, start day and climate file. An action SHALL set `t_mean_init` of selected collector lines from the
mean liquid temperature of the last annual run, and a model check SHALL warn when they differ by more than 2 K.

#### Scenario: Undisturbed start
- **WHEN** a collector in the undisturbed mode is built for a simulation starting on 1 January
- **THEN** its `TStartLoc` and the value of `TLoc` equal `startState(..., undisturbed=True, start_day=0)` at the loc node

#### Scenario: Pre-calculated start reused
- **WHEN** two lines of the same resource and mean temperature are built
- **THEN** the pre-calculated state is computed once

#### Scenario: Mean temperature from results
- **WHEN** the action runs on a collector line whose last annual run had a mean liquid temperature of 3.4 degC
- **THEN** its `t_mean_init` is 3.4

### Requirement: Checks before a build
A model build with collector lines SHALL check that the configured IDA Districts has GroundMo with
`contractVersion` equal to `CONTRACT_VERSION`, that the climate macro provides `IGlob`, and that every used resource has
an accepted fit; a failed check SHALL stop the build with a message naming what is missing. Builds without collector
lines SHALL not check GroundMo.

#### Scenario: GroundMo missing
- **WHEN** a project with a collector line is built and IDA Districts has no GroundMo
- **THEN** the build stops with a message that GroundMo with contract version 2 is needed

#### Scenario: No collectors, no check
- **WHEN** a project without collector lines is built on an IDA Districts without GroundMo
- **THEN** the build runs as before

### Requirement: Sizing and cost optimization leave collectors
Dynamic and static pipe sizing SHALL not change the bundle of a collector line, and the cost optimization SHALL treat
collector lines as protected.

#### Scenario: Sizing
- **WHEN** a version with a collector line is sized
- **THEN** the collector line keeps its `pipe_bundle_type_id`

#### Scenario: Cost optimization
- **WHEN** the cost optimization proposes changes
- **THEN** no change concerns a collector line

### Requirement: Collector costs
The investment of a collector line SHALL be trench meters × the resource's cost per trench meter plus loop meters ×
its cost per loop meter, with trench meters = line length × loops and loop meters = trench meters × loop length per
trench meter, in place of the pipe and trench items of the loop pipe; the other pipes of the bundle keep their pipe
items without a trench. Maintenance and lifetime SHALL come from the resource. Collector lines SHALL be excluded from
the heat-loss items and the heat-loss check.

#### Scenario: Investment
- **WHEN** a collector line of 100 m with 4 loops, 6.28 m loop per trench meter, 30 EUR per trench meter and 2 EUR per loop meter is evaluated
- **THEN** its collector item is 400 × 30 + 2512 × 2 = 17024 EUR

#### Scenario: No heat-loss item
- **WHEN** the economics of a version with a collector line are evaluated
- **THEN** the heat losses and the loss check contain no collector line

### Requirement: Collector results
The model build SHALL request per collector line its inlet and outlet temperature, extracted heat, surface heat and per
section the loc and near temperature and the ice fraction, logged on the variables. The results SHALL be loaded per
line with the sections as segments and shown on the map; the extracted heat SHALL be summed into a meter of its own,
not into the pipes' ambient losses. The network report and `version_kpis` SHALL give trench and loop meters, the
extracted heat per year and per trench meter, the lowest outlet temperature and the largest ice fraction, per collector
type and in total.

#### Scenario: Results loaded
- **WHEN** a simulated version with a 3-section collector line is loaded
- **THEN** the line has three segments with `TLoc`, `TNear` and ice fraction, and `QExtracted` over the year

#### Scenario: Report
- **WHEN** the network report of that version is opened
- **THEN** it shows the collector's trench meters, extracted kWh/(m a), lowest outlet temperature and largest ice fraction
