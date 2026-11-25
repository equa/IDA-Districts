# cost-sensitivity Specification

## Purpose
Sensitivity analysis of the cost optimization: varied economic and run parameters, variant designs (one at a time, combinations, sample), a model-based estimate or a full optimization per variant, results as plots, tables and a map layer; and the pricing of the pipe losses when a bought carrier has no price. Created by archiving change cost-sensitivity.
## Requirements
### Requirement: Parameter table
The cost optimization dialog SHALL offer a table of sensitivity parameters (interest rate, period, start price and escalation per cost group, cost factors for pipes, trench and pumps, penalty prices, limits of a smaller pipe), each with its base value from the scenario and the run, a mode (absolute or relative) and a − and a + value; a row not marked as varied SHALL keep its base value in every variant.

#### Scenario: Relative interest variation
- **WHEN** the interest rate of 3 % is varied relatively with −50 % and +50 %
- **THEN** its variants use 1.5 % and 4.5 %

### Requirement: Variant designs
The analysis SHALL form the variants one at a time by default (the base and each varied parameter at its − and its + value), and optionally as all combinations of −, base and + or as a Latin-hypercube sample of a given size with a saved seed, and SHALL show the number of variants and the estimated duration before the start.

#### Scenario: Two parameters one at a time
- **WHEN** interest and electricity price are varied one at a time
- **THEN** the analysis has five variants: the base and four with one parameter changed

#### Scenario: Reproducible sample
- **WHEN** a sample of 20 variants is drawn twice with the same seed
- **THEN** both draws give the same variants

### Requirement: Scenario unchanged
A variant SHALL apply its values in memory; the economic scenario stored in the project SHALL stay unchanged.

#### Scenario: After an analysis
- **WHEN** an analysis with a varied interest rate has finished
- **THEN** the scenario in the project has its original interest rate

### Requirement: Estimate per variant
In the estimate mode the analysis SHALL start from the best iteration of the last run in the loaded version (every stage version for a run over stages), refuse with a reason when the versions no longer carry its pipes, and compute per variant the NPV of that design with the variant's values and one step of the cost model with them, giving the lines whose pipe changes and the estimated NPV after the step; the base variant SHALL reproduce the NPV of the best iteration.

#### Scenario: Base variant
- **WHEN** the estimate runs the base variant
- **THEN** its NPV equals the NPV of the best iteration of the run

#### Scenario: Pipes changed after the run
- **WHEN** a line's pipe was changed after the run and the estimate is started
- **THEN** the dialog refuses and names the reason

### Requirement: Full optimization per variant
In the full mode the analysis SHALL run a cost optimization per variant with the dialog's settings and the variant's values into new child versions, one after another, load the base version again after each run, and keep the finished variants when stopped.

#### Scenario: Stop during the third variant
- **WHEN** the user stops the analysis during the third of five full optimizations
- **THEN** the third run ends after its current step, the base version is loaded again and the result holds the finished variants

### Requirement: Results
The analysis SHALL save its inputs and results in `sensitivity.json` of the version and show, in the dialog and the report, a parallel-coordinates plot of the varied parameters and the results, a tornado chart of the NPV swing per parameter (rank correlations for combinations and samples), a table of the variants, a table of the lines whose pipe changes and a map layer of the share of variants changing each line's pipe (per stage for a run over stages).

#### Scenario: One line flips at high interest
- **WHEN** at the + interest the step makes line 114 smaller and no other variant changes it
- **THEN** the flip table lists line 114 with its base pipe and the smaller pipe at + interest, and the map layer shows line 114 with the share 1 / number of variants

### Requirement: Carrier without a price
When the plants (or, for the whole system, the customers) buy a carrier that has no price in the scenario, the evaluation SHALL price the pipe losses with the price curves instead of counting the bought energy as free, the start of the cost optimization SHALL warn, and the reports SHALL name the reason.

#### Scenario: Boilers without a fuel price
- **WHEN** the plants buy fuel and the scenario has no fuel price
- **THEN** the NPV contains the pipe losses priced with the curves, the plant energy is shown for information and the start log names fuel

