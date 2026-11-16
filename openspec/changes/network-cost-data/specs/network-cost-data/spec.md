## ADDED Requirements

### Requirement: Pipe cost columns
The pipe catalog (`public.pipes`) SHALL have `costs` (material and laying in €/m per pipe), `maintenance_pct` (%/a of the investment), `lifetime_a` (years), `p_max_bar` (maximum operating pressure) and `example` (true for example values). The pipes table dialog SHALL show and edit them with translated headings. The cost of a pipe bundle SHALL be the sum of its pipes.

#### Scenario: Edit a pipe
- **WHEN** the user opens the pipes table and sets costs 120, maintenance 1.5, lifetime 50, p_max 25 and clears example for a pipe
- **THEN** the values are saved in `public.pipes` and the pipe is no longer an example value

### Requirement: Trench costs per surface
The trench (civil works) costs per metre of a line SHALL be a + b·DN, with a and b of the line's surface class in the scenario's trench cost curves and DN of the largest pipe of the line's bundle. Streets SHALL have a surface class (`surface`); a line's length per surface SHALL follow its overlap with the streets within the pipe laying tolerance, and the rest of the line SHALL have the scenario's default surface. `streets.costs_eur7m` SHALL stay unchanged for the pipe laying.

#### Scenario: Line on a paved street
- **WHEN** a 100 m line with a DN100 bundle lies completely on a street with surface "paved" and the scenario has paved a = 155, b = 9.4
- **THEN** its trench costs are 100 · (155 + 9.4 · 100) = 109 500 €

#### Scenario: Line partly off the streets
- **WHEN** 60 m of a 100 m line lie on an "unpaved" street and the scenario's default surface is "paved"
- **THEN** 60 m are costed with the unpaved curve and 40 m with the paved curve

### Requirement: Example values in the templates
The plugin templates with a pipe catalog (`db_default_values`, `heating_network`) SHALL contain example values for every pipe of the rigid series (costs, maintenance, lifetime, p_max, `example` true); pipes of other series (flexible pipes of change `pipe-series-catalog`) MAY have no costs, `example` false. Every project SHALL get a scenario "base" with example prices, price curves, trench cost curves and pump costs, each with its source in the description, when a version is loaded and the project has no scenario.

#### Scenario: New project from a template
- **WHEN** a project is created from the template `db_default_values` and its version is loaded
- **THEN** every pipe of the series "Isoplus DRE Standard" and "Isoplus DRD Standard" has costs, maintenance, lifetime and p_max, and the scenario "base" exists with trench costs for "paved" and "unpaved"

### Requirement: Upgrade of existing projects
Opening a project created before this change SHALL add the pipe columns (existing costs kept, `example` false), the scenario tables with the scenario "base" of example values, and `surface` (NULL) to the streets of every version, without changing other data.

#### Scenario: Old project
- **WHEN** a project without the new columns and tables is opened
- **THEN** the columns and tables exist, the pipes keep their costs, and the streets have `surface` NULL
