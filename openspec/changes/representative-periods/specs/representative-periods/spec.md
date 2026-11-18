## ADDED Requirements

### Requirement: Choice of the representative weeks
From the version's climate file (8760 hourly air temperatures; 8784 with day 366 dropped), the plugin SHALL choose three non-overlapping weeks starting at midnight: the anchor week with the lowest mean air temperature for a network with a heating pair (the highest for a network with only cooling pairs), and two weeks that minimize the mean temperature distance of the weights. With the option "add the warmest week", available for every network, a heating network SHALL get the warmest week as a fourth week and a cooling network the coldest week. A climate file that cannot be read SHALL stop the choice with a message naming the file.

#### Scenario: Heating network on Bromma
- **WHEN** the weeks are chosen for a heating network with the climate `BROMMA.PRN`
- **THEN** the anchor is the coldest week, and the yearly sums of the proxies max(0, 15 − T) and its cube estimated with the weights deviate by less than 1 % and 2.5 % from the full year

#### Scenario: Missing climate file
- **WHEN** the climate file of the version does not exist
- **THEN** no weeks are chosen and a message names the file

### Requirement: Weights and coverage
Every hour of the year SHALL be assigned to the simulated hours of the same hour of day: split linearly by temperature between the nearest simulated hours below and above its air temperature, or to the nearest if only one side exists. The weight of a simulated hour SHALL be the sum of its shares (all weights add up to the hours of the year), together with the sum of the shares times the electricity profile. The coverage SHALL be the share of the year's hours whose nearest simulated hour is more than 1 K away; above 40 % a warning SHALL be shown.

#### Scenario: Weights add up
- **WHEN** weights are calculated for any three weeks
- **THEN** their sum is 8760

#### Scenario: Hour between two simulated hours
- **WHEN** a year hour at 5 °C has simulated hours of its hour of day at 4 °C and 8 °C
- **THEN** 0.75 of it goes to the 4 °C hour and 0.25 to the 8 °C hour

### Requirement: Periods widget
A periods widget, shown in the dialog of the cost optimization, SHALL show the year's air temperature with the chosen weeks (anchor marked), the length (default 7 days), the start-up before each period (default 3 days), the options "add the warmest week" and "annual simulation", and the coverage; the user SHALL be able to move a week by its start date or by clicking the diagram, after which the coverage is recalculated. The climate file SHALL be read and the weeks chosen outside the main thread, the widget showing that the weeks are being chosen. With "annual simulation" the week length, the warmest week, the diagram, the weeks and the coverage SHALL be hidden.

#### Scenario: Move a week
- **WHEN** the user moves the second week to another start date
- **THEN** the diagram shows the new week and the coverage is recalculated

#### Scenario: Annual simulation
- **WHEN** the user selects "annual simulation"
- **THEN** the diagram, the weeks and the coverage are hidden and only the start-up remains

### Requirement: Period run and kept results
Starting SHALL delete the version's `_period*` tables and `periods.json`, optionally build the network model, simulate the weeks in parallel, each in its own copy of the network model with the week's start-up and calculation dates (a week SHALL start only when the solver of the previous week runs, that week has ended, or at most 120 s after the previous start, and only when the free memory holds one more week, unless no week runs; a failed week SHALL be simulated once more after the others, one at a time), and for each week load the results and copy the result tables of lines, energy plants and customers needed for the economics (temperatures, mass flows, pressures, losses, pump power, room temperature, power) with the suffix `_period<k>`; then it SHALL write `versions/<version>/periods.json` (run time, climate file, weeks with role, per simulated hour period, time, weight and profile sum, coverage). After the run the version's simulation dates SHALL be those before the run. With "annual simulation" one simulation of the whole year SHALL run, without copies, all weights 1.

#### Scenario: Three weeks
- **WHEN** the user starts a period run with three weeks
- **THEN** three simulations run at the same time, the version has the result tables of each week with suffixes `_period1` to `_period3`, `periods.json` lists the weeks and weights, and the simulation dialog shows the dates from before the run

#### Scenario: Failed week
- **WHEN** the simulation of one week fails
- **THEN** the run waits for the other weeks, ends with an error naming the week, and no model copy is left

#### Scenario: IDA of a week ends without an answer
- **WHEN** the IDA Districts session of one week crashes or is closed during the simulation
- **THEN** that week fails within about a minute instead of keeping the run waiting, and its error names the last lines of the solver output

#### Scenario: Not enough memory for all weeks
- **WHEN** a period run with three weeks starts on a computer whose free memory holds two weeks
- **THEN** the third week starts when one of the first two has finished, and the log says it waits for free memory

#### Scenario: Week failed for lack of memory
- **WHEN** the simulation of one week fails while others run
- **THEN** that week is simulated again alone after the others, and the run goes on when it succeeds

#### Scenario: Weeks start one after another
- **WHEN** a period run with three weeks starts
- **THEN** the second week's IDA Districts starts only after the first week's solver runs, and the third only after the second's

#### Scenario: Second run
- **WHEN** a second period run is started in the same version
- **THEN** no table of the first run is left

### Requirement: Economics from representative periods
The Economics section of the network report SHALL, when the normal results do not cover a full year, use `periods.json` and the `_period*` tables, weighting every simulated hour with its weight and pricing electricity with its profile sum, and SHALL show the weeks, the coverage and the run time.

#### Scenario: Report after a period run
- **WHEN** the network report with Economics is made after a period run
- **THEN** the section shows the NPV with the weeks, the coverage and the run time
