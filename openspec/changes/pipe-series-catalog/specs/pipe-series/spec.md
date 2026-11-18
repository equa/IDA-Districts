## ADDED Requirements

### Requirement: Pipe series table
The project DB (schema `public`) SHALL have a table `pipe_series` with one row per product line: `name` (unique, equal to the text in `pipes.series`), `system_type` (one of `rigid_single`, `rigid_twin`, `bare_plastic`, `flexible_plastic`, `flexible_metal`, or empty for unknown), `standard`, maximum continuous temperature, maximum peak temperature, minimum temperature, maximum axial stress, safety factor and `description`. `pipes.series` SHALL stay a text column, and the pipe sizing SHALL keep choosing among the pipes with the same `pipes.series` text.

#### Scenario: Series of a pipe
- **WHEN** a pipe has `series` "isoplus isopex H" and `pipe_series` has a row with that name
- **THEN** the system type, standard and limits of that row are the pipe's product data

#### Scenario: Invalid system type
- **WHEN** a row of `pipe_series` is saved with the system type "rigid"
- **THEN** the database rejects it

#### Scenario: Sizing unchanged
- **WHEN** the pipe sizing chooses the next smaller pipe of a line with a pipe of series "Isoplus DRE Standard"
- **THEN** it chooses among the pipes with `series` "Isoplus DRE Standard", as before this change

### Requirement: Pressure ratings of a series
The project DB SHALL have a table `pipe_series_pressure_ratings` with the allowed pressure (bar) per series, operating time (years) and continuous temperature (°C). A rating SHALL belong to its series by the series id, so it follows a rename of the series and is deleted with it.

#### Scenario: Rename a series
- **WHEN** the user renames the series "isoplus isopex H" in the series dialog
- **THEN** its pressure ratings still belong to it

#### Scenario: Delete a series
- **WHEN** the user deletes a series
- **THEN** its pressure ratings are deleted too and no pipe is changed

### Requirement: Minimum bend radius
`pipes` SHALL have the column `min_bend_radius_m` (m), empty for rigid pipes and pipes delivered as straight bars.

#### Scenario: Flexible pipe
- **WHEN** the pipe "isoplus isopex H-63" of the template `heating_network` is read
- **THEN** its minimum bend radius is 1.0 m

### Requirement: Pressure limit on the pipe
The maximum operating pressure of a pipe SHALL be its `pipes.p_max_bar`; `pipe_series` SHALL NOT have a maximum pressure. For plastic pipes the pressure ratings of the series give the time- and temperature-dependent limit, capped by `p_max_bar`.

#### Scenario: Flexible pipe pressure
- **WHEN** the pipe "isoplus isopex S-40" of the template `heating_network` is read
- **THEN** its `p_max_bar` is 10 and its series has pressure ratings

### Requirement: Series dialog
The plugin SHALL offer a table dialog "Pipe series" that shows and edits the rows of `pipe_series`, with the system type as dropdown, and the pressure ratings of the selected series below it. The pipes dialog SHALL show and edit the minimum bend radius. Headings SHALL have German translations.

#### Scenario: Edit ratings of a series
- **WHEN** the user selects the series "isoplus isoclima" in the dialog and changes the pressure for 50 years at 40 °C to 11.0 bar
- **THEN** the rating is saved for that series only

### Requirement: Upgrade of existing projects
Loading a version of a project created before this change SHALL create `pipe_series` and `pipe_series_pressure_ratings` if missing, add `pipes.min_bend_radius_m` if missing, and add a `pipe_series` row with empty system type for every `pipes.series` text that has no row. No pipe SHALL be changed. The same SHALL happen when the pipes or series dialog is opened and before a resource import.

#### Scenario: Old project with series texts
- **WHEN** a project whose pipes have the series texts "A" and "B" but no `pipe_series` table is loaded
- **THEN** `pipe_series` has the rows "A" and "B" with empty system type, the pipes are unchanged and `min_bend_radius_m` exists empty

#### Scenario: Second load
- **WHEN** the same project is loaded again
- **THEN** no row is added and no table is altered

### Requirement: Resource export and import of series
The resource export SHALL write the series of the exported pipes with their pressure ratings. The resource import SHALL create a series that the target project does not have, with its ratings, and SHALL keep an existing series of the same name unchanged.

#### Scenario: Import into a project without the series
- **WHEN** pipes of series "isoplus isopex S" with its ratings are exported and imported into a project without that series
- **THEN** the project has the series with its system type, limits and ratings, and the imported pipes reference it by name

#### Scenario: Import into a project with the series
- **WHEN** the target project already has a series "isoplus isopex S" with other limits
- **THEN** its row and ratings are kept unchanged
