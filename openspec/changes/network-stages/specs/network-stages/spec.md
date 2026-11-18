## ADDED Requirements

### Requirement: Stage table
The cost optimization dialog SHALL have a table of stages with a version and a start year per row, stage 1 starting in year 0 and the start years increasing. Before a run the plugin SHALL check that each stage is a descendant of the previous one and that every line of a stage exists with the same ID and geometry in the later stages, and SHALL refuse to start with a message naming each problem. A table with one row SHALL run as the optimization of a single version.

#### Scenario: Valid chain
- **WHEN** the table holds base1 (year 0), its child base1_s2 (year 10) and base1_s2's child base1_s3 (year 20), each keeping the lines of the previous one
- **THEN** the run starts

#### Scenario: Missing line
- **WHEN** a line of base1 does not exist in base1_s2
- **THEN** the run does not start and the message names the line and the stage

### Requirement: Coupled sizing over the stages
The cost model SHALL be built per stage. The NPV change of a pipe change of a line SHALL be its investment change, discounted to the start year of the first stage containing the line, plus the change of the operating costs of every stage containing the line valued with that stage's years. The peak-flow and pressure limits SHALL use the maximum over the stages, and a protected line SHALL be protected in all stages.

#### Scenario: Line loaded by a later stage
- **WHEN** a line of stage 1 carries twice its stage-1 flow in stage 3
- **THEN** its smaller pipe is rejected if the peak flow of stage 3 exceeds the limit, even if stage 1 alone allows it

### Requirement: NPV by stage years
The yearly operating costs of each stage SHALL be valued with the present-value factor of the years from its start year to the next stage's start year (the last stage to the end of the period). An item's investment, maintenance, replacements and residual value SHALL count from the start year of the stage it first appears in. Pumps SHALL be sized for stage 1's peak at year 0, with the increase of the peak of a later stage bought at its start year.

#### Scenario: Line built in a later stage
- **WHEN** a line first appears in the stage starting in year 10 and the interest is 3 %
- **THEN** its investment counts with the factor 1/1.03^10 and its replacements from year 10 on

### Requirement: Iterations over all stages
Each iteration SHALL apply the same pipe change to every stage version (or to their new child versions, after the dialog's choice for all stages), build and simulate every stage and evaluate the summed NPV. 'Set pipes' of an iteration SHALL set the pipes in all stages.

#### Scenario: Three stages
- **WHEN** an iteration changes line 7, which exists in all three stages
- **THEN** line 7 has the new pipe in all three stage versions and all three are simulated before the next iteration

### Requirement: Periods and climates per stage
All stages SHALL simulate the same representative weeks, chosen on the climate of stage 1, with the opposite extreme week added when a stage has a cooling pair. Each stage SHALL simulate them with its own climate file and SHALL compute its weights and coverage from that climate; a stage above the coverage warning SHALL be named.

#### Scenario: Future climate in a later stage
- **WHEN** stage 3 has a warmer climate file than stage 1
- **THEN** stage 3 simulates the same weeks with its climate file and its weights come from its climate

### Requirement: Report of the stages
The report SHALL list the stages with version, years and climate file, the NPV per stage and in total, and the NPV terms with their stage and years.

#### Scenario: Report of a staged run
- **WHEN** the report of a run with three stages is written
- **THEN** it shows the three stages, their NPV and the total
