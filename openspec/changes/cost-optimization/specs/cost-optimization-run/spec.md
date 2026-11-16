## ADDED Requirements

### Requirement: Cost optimization dialog
A dialog "Cost optimization" SHALL have the scenario, the supply/return pairs (suggested from the plant connections), the periods (the weeks of the representative periods or an annual simulation), the penalty prices (€/Kh with a tolerance band in K, €/kWh unmet), the max. number of iterations and the version (new child version, default, or the loaded version). It SHALL name the needed outputs that are switched off (pump power, line and plant temperatures, line losses, room temperature, customer power) and point to the dynamic pipe sizing when the version has no sizing iterations.

#### Scenario: Unsized version
- **WHEN** the dialog opens on a version without iteration files of the dynamic pipe sizing
- **THEN** it shows a hint to run the dynamic pipe sizing first

### Requirement: Reference iteration
The run SHALL start with iteration 0: the periods simulated with the pipes of the version, the simulated NPV and per customer the degree hours and unmet load saved as the reference of the penalties.

#### Scenario: Reference saved
- **WHEN** a run starts
- **THEN** iteration 0 has the simulated NPV split and per customer Kh and kWh, and no pipe is changed

### Requirement: Penalties
Degree hours SHALL count per hour only when heating is needed (`HCMode` 1, TRoom below TSet minus the tolerance) or cooling is needed (`HCMode` −1, TRoom above TSet plus the tolerance); a room temperature between the setpoints SHALL count nothing. The penalty of an iteration SHALL be €/Kh × max(0, Kh − Kh_ref) plus €/kWh × max(0, kWh_unmet − kWh_unmet,ref) per customer, weighted to the year, in every year of the period. The deviations of the reference SHALL be shown as their own value.

#### Scenario: Warmer than the setpoint in heating mode
- **WHEN** a room is at 23 °C with TSet 21 °C in heating mode
- **THEN** that hour counts no degree hours

#### Scenario: New deficit
- **WHEN** a customer had 10 Kh in the reference and 25 Kh in an iteration
- **THEN** the penalty of that customer is the price × 15 Kh per year

### Requirement: Iterations, tracking and end
Each iteration SHALL apply the step of the cost model, write the pipes into the version, simulate the periods and save a row with the simulated NPV split, the model NPV, the model error, the lines changed larger and smaller and the rejected changes, and the steps (line, pipe before and after, ΔNPV and its split, limit or guard). The dialog SHALL show the rows, a diagram of the NPV over the iterations stacked by cost group with the model NPV as a line, and map layers of the changed lines, updated after each iteration. The run SHALL end when the simulated NPV has not improved for 2 iterations, a state repeats, no change improves the model NPV, or the max. iterations are reached; then the pipes of the iteration with the best simulated NPV SHALL be written into the version and, if it was not the last iteration, simulated again.

#### Scenario: Best iteration is not the last
- **WHEN** iteration 3 has the best simulated NPV and iterations 4 and 5 are worse
- **THEN** the run ends after iteration 5, the version gets the pipes of iteration 3, its periods are simulated again and the table marks iteration 3

#### Scenario: No improving step
- **WHEN** no line has a negative ΔNPV in an iteration
- **THEN** the run ends with the message that no change improves the costs, and the version keeps the best iteration

### Requirement: Protected lines
Lines protected by the dynamic pipe sizing (change protect-lines), if the version has any, SHALL never be changed.

#### Scenario: Protected line
- **WHEN** a protected line has a negative ΔNPV
- **THEN** it keeps its pipe and the step lists it as protected
