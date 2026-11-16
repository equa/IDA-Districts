## ADDED Requirements

### Requirement: Simulation and start-up period in the sizing dialog
The dynamic pipe sizing dialog SHALL have the calculation period and the start-up period (from/to, `yyyy-MM-dd hh:mm:ss`), filled from the `networkSimData.txt` of the loaded version when the dialog opens. Every simulation of a sizing run SHALL use these periods, and they SHALL be saved in the `networkSimData.txt` of the simulated version with its other simulation settings unchanged. The run SHALL NOT start, and SHALL show a warning naming the period, if a period's "from" is not before its "to".

#### Scenario: Summer period
- **WHEN** the user sets the calculation period 2026-07-01 00:00:00 to 2026-07-08 00:00:00 and starts the sizing
- **THEN** every simulation of the run covers this period, and the simulation dialog of the version shows it afterwards

#### Scenario: Unchanged dialog
- **WHEN** the user starts the sizing without changing the periods
- **THEN** the simulations use the periods saved for the version, as before this change

#### Scenario: Invalid period
- **WHEN** the start-up period ends before it begins
- **THEN** the run does not start and a warning names the start-up period

### Requirement: Reference run as iteration 0
With the option "Reference run before the sizing (iteration 0)", the run SHALL build the network model (if that option is set), simulate with the current pipes, load the results and evaluate every pair without changing any pipe, save the result as iteration 0 with the outcome "reference", list it in the iteration table and show it on the map without a new-pipes layer, and then finish with a message that the sizing is started without the reference run. Iteration 0 SHALL NOT take part in the oscillation check.

#### Scenario: Check the period before sizing
- **WHEN** the user starts with the reference run
- **THEN** one simulation runs, the table shows a row per pair with iteration 0 and the outcome "reference", no line of the version changes its pipe bundle, and the run stops

### Requirement: Reference run and sizing in the same version
With "new child version", the reference run SHALL create and load the child version, run iteration 0 there and then select "override the pipes of the loaded version" with a log message naming the version. At the start of a run, a reference run or a run in a new child version SHALL delete all iteration files of the version; a run that overrides the loaded version without the reference run SHALL delete the iteration files from iteration 1 on and keep iteration 0.

#### Scenario: Two starts
- **WHEN** the user starts with "new child version" and the reference run, and then starts again without the reference run
- **THEN** both runs work in the same child version, the parent version is unchanged, and the table lists iteration 0 followed by the sizing iterations 1, 2, ...

#### Scenario: New child version without reference run
- **WHEN** the parent version has iteration files and the user starts the sizing in a new child version without the reference run
- **THEN** the child version has no iteration files of the parent, iteration 0 included

### Requirement: Warning for a target customer without flow
After the evaluation of a pair (also in iteration 0), if the mass flow of the pair's target customer at its critical time is below 1 % of the customer's peak mass flow over the simulated period, the log SHALL show a warning naming the pair, the customer and both mass flows and advising to check the simulation period, and the pair's entry in the iteration file SHALL have `target_no_flow` true. The sizing SHALL proceed unchanged. The message SHALL have a German translation.

#### Scenario: Short winter period of a cooling pair
- **WHEN** the target customer of the pair 2/4 has a mass flow of 0 kg/s at its critical time and a peak of 0.4 kg/s
- **THEN** the log warns for the pair 2/4 and that customer, and the sizing continues
