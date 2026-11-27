## ADDED Requirements

### Requirement: NPV of the loaded version
The results tab SHALL offer, in the group "Reports", a button that opens a dialog computing the net present value (NPV) of the loaded version from its simulation results, without simulating. The NPV SHALL be computed by the same functions as an iteration of the cost optimization: the economic evaluation of the version (investment, maintenance, energy, residual value) plus the NPV of the comfort violations, and over stages the NPV of the stages.

#### Scenario: Same NPV as the cost optimization
- **WHEN** the user calculates the NPV of a simulated version with the same inputs as a cost optimization
- **THEN** the dialog shows the NPV that the cost optimization computes for that version as an iteration, with the same parts

#### Scenario: Version without comfort violations
- **WHEN** the version's results hold no comfort violation
- **THEN** the NPV equals the NPV of the economic evaluation and the part "comfort violations" is zero

#### Scenario: Nothing is simulated
- **WHEN** the user clicks "Calculate"
- **THEN** the results in the version are evaluated in a worker, no simulation is started and IDA Districts is not needed

### Requirement: Inputs of the version NPV
The dialog SHALL offer the inputs of the cost optimization's NPV, under the keys of its run parameters: economic scenario, submodel, price per degree hour and its tolerance, price per kWh of unmet load and its tolerance, deadband heating/cooling, the stages and the required loads of source-file customers. It SHALL fill them from the version's last calculation, else from the version's last cost optimization run, else with the defaults of the cost optimization dialog, and SHALL name the source. The required loads SHALL be the project's list shared with the cost optimization.

#### Scenario: Inputs from the last cost optimization
- **WHEN** the version has no saved calculation and was the start of a cost optimization with 1 €/Kh
- **THEN** the dialog opens with 1 €/Kh and states that the inputs come from the last cost optimization of the version

#### Scenario: Inputs from the last calculation
- **WHEN** the version has a saved calculation
- **THEN** the dialog opens with that calculation's inputs and shows its result with its date

#### Scenario: Stages that do not form a chain
- **WHEN** the stage table lists versions that are not a valid chain of child versions
- **THEN** "Calculate" refuses and the log names the problems

### Requirement: Results needed
The calculation SHALL evaluate a simulated year or a period run with its weeks kept in the version. When outputs are missing or the results are too short, the dialog SHALL name the missing outputs or the number of days in the log and SHALL save nothing.

#### Scenario: Missing outputs
- **WHEN** the version was simulated without the pump power
- **THEN** the log names the missing output, no NPV is shown and version_npv.json is not changed

### Requirement: Saved result and report
A calculation SHALL be saved with its inputs and the scenario name in `versions/<version>/version_npv.json`, replacing the previous one. "Report" SHALL write an HTML report of the saved calculation into the version's report folder (`net_present_value_<time>.html`) and open it; the report SHALL show the overview, the inputs and the economic scenario, the pipes and trenches, the NPV per part, investment per pipe and surface, the equations and terms, replacements and residual values, the stages and the customers with comfort violations, and SHALL say "Version" where the cost report says "Iteration".

#### Scenario: Report of the last calculation
- **WHEN** the user calculates the NPV and clicks "Report"
- **THEN** a file `net_present_value_<time>.html` is written in the version's report folder and opened, with the same NPV as the dialog

#### Scenario: No calculation yet
- **WHEN** the version has no saved calculation
- **THEN** the button "Report" is disabled
