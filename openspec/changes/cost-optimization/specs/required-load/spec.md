## ADDED Requirements

### Requirement: Required-load columns per template
The plugin SHALL keep a list per customer template with a source file: column of the source file with the required load, unit (W or kW) and mode (heating or cooling), saved in the project as `requiredLoads.json`. Templates with a `SOURCE-FILE` SHALL be detected with column 2, unit W and mode heating as defaults; the user SHALL be able to change and remove entries in the cost optimization dialog.

#### Scenario: Detected template
- **WHEN** the project has a customer template with a `SOURCE-FILE` and no `requiredLoads.json`
- **THEN** the list has an entry for it with column 2, unit W and mode heating, and the file is written

### Requirement: Unmet load
For a customer of a listed template, the required load SHALL be read from its source file, interpolated linearly to the result time steps with the hour column of the file, converted to W; the unmet load of a time step SHALL be max(0, required − supplied power of the customer) if it exceeds 2 % of the required load, else 0, and summed with the weights of the periods to kWh per year.

#### Scenario: Partly supplied
- **WHEN** a customer requires 10 kW in an hour and is supplied 9 kW
- **THEN** that hour counts 1 kWh unmet

#### Scenario: Within the tolerance
- **WHEN** a customer requires 10 kW and is supplied 9.9 kW
- **THEN** that hour counts no unmet load
