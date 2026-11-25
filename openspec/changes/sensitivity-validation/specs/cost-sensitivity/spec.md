## ADDED Requirements

### Requirement: Validation of an estimate by simulation
The results of an estimate SHALL offer a validation that simulates, for each chosen variant whose step changes pipes, the pipes of the estimate's basis plus that variant's step with the variant's values. The user SHALL choose all variants with a step, the selected variant or the variants passing the filter, and SHALL see the number of simulations and the estimated duration before the start. Variants whose step changes no pipe SHALL NOT be simulated and SHALL be marked "not simulated".

#### Scenario: Only variants with a step are simulated
- **WHEN** an estimate of five variants changes pipes in three of them and the user validates all variants
- **THEN** three simulations run and the other two variants are marked "not simulated"

#### Scenario: Validation of the selected variant
- **WHEN** the user selects one variant in the parallel coordinates and validates the selected variant
- **THEN** only that variant is simulated

#### Scenario: Analysis without saved steps
- **WHEN** the user validates an estimate saved before the steps were saved
- **THEN** the dialog refuses and asks to run the estimate again

### Requirement: Validation versions
Each validated variant SHALL be simulated in kept child versions `<version>_v<k>`, one per stage version in a run over stages, linked in the version handling like the versions of a cost optimization over stages. The variants SHALL run one after another, the base version SHALL be loaded again after each, and a stop SHALL keep the finished variants. The validation SHALL refuse when the pipes of the versions no longer match the estimate's basis.

#### Scenario: Child version holds the step
- **WHEN** variant 2 of an estimate makes line 114 smaller and is validated
- **THEN** version `<version>_v2` holds the smaller pipe on line 114, the other lines keep the pipes of the best iteration, and the base version is loaded again afterwards

#### Scenario: Pipes changed after the run
- **WHEN** a line's pipe was changed after the run and the user starts the validation
- **THEN** the dialog refuses and names the reason

### Requirement: Validation results
For each validated variant the analysis SHALL save and show, in the dialog and the report, the NPV of the basis design, the forecast NPV after the step, the simulated NPV, the error in € and %, whether the simulation confirms the step (simulated NPV below the NPV of the basis design), the change of the present value of the comfort penalties against the basis design, the lines over a limit (specific pressure loss or velocity at the simulated peak flow above the run's limits, plant pressure above the least p_max of the pipes in use) and its versions, together with a plot of the forecast change against the simulated change with a diagonal. The parallel coordinates and the tornado chart SHALL keep the forecast values.

#### Scenario: Forecast too optimistic
- **WHEN** the forecast of a variant's step is −2'500 € and the simulation gives +2'600 €
- **THEN** the validation table shows the error of 5'100 €, the step as not confirmed, and the plot shows the variant's point above the diagonal

#### Scenario: Step with a new comfort violation
- **WHEN** a validated step lowers the NPV but a customer gets a new comfort violation
- **THEN** the step is shown as confirmed and the comfort penalty change is positive
