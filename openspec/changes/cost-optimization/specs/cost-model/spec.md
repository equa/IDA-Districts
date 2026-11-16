## ADDED Requirements

### Requirement: Net present value change of a pipe change
The cost model SHALL estimate, from the kept results of a check (mass flows and temperatures per line, pump power, customer results) and their weights, the change of the net present value of the scenario when one line gets the next larger or the next smaller pipe of its series for the pipes of the pairs in its bundle: investment and maintenance of the pipes and of the trench (its DN), pump energy, heat and cold losses, with the prices, levels and profile of the scenario. Lines whose pipe has no larger or smaller pipe in its series, protected lines and lines of no pair SHALL NOT be changed.

#### Scenario: Larger pipe on the critical path
- **WHEN** a line on the critical path of a central pump gets the next larger pipe
- **THEN** the estimated pump energy falls, the investment rises, and the ΔNPV is their discounted difference

#### Scenario: Larger pipe off the critical path
- **WHEN** a line that is on no critical path in any simulated hour gets the next larger pipe
- **THEN** the estimated pump energy does not fall and the ΔNPV is positive

### Requirement: Pump head of central and decentral pumps
For a central pump the model SHALL take the head per hour as the largest pressure drop over the supply paths of the customers it supplies plus the smallest substation pressure difference; for a decentral pump (a network pump of a customer) the head SHALL be the pressure drop over the customer's own path, the direction from the signed mass flows of the hour. The pump power SHALL be V̇ × head / η_eff, η_eff of each pump calibrated from its simulated power in the check.

#### Scenario: Calibration
- **WHEN** a pump had 2 kW at a volume flow of 0.01 m³/s and a modelled head of 100 kPa in an hour of the check
- **THEN** its η_eff is 0.5 and the model gives 2 kW for that hour with unchanged pipes

#### Scenario: Decentral pump
- **WHEN** a customer with a network pump lies at the end of a branch and a line of its path gets a smaller pipe
- **THEN** the estimated power of that customer's pump rises and the pumps of customers not using the line are unchanged

### Requirement: Limits and guard
The model SHALL reject a change after which the plant pressure plus the head increase exceeds the smallest `p_max_bar` of the pipes in any simulated hour, and a smaller pipe whose specific pressure loss at the peak flow of the line exceeds 300 Pa/m or whose velocity exceeds 3 m/s (the defaults of the dynamic pipe sizing). Because the model raises the pump head to cover a longer path, a customer is only starved through the pressure limit. Rejected changes SHALL be saved with their reason.

#### Scenario: Peak flow in a smaller pipe
- **WHEN** a line carries 2 kg/s at its peak and its next smaller pipe is DN40
- **THEN** the change is rejected with the reason peak

#### Scenario: Pressure limit
- **WHEN** the next smaller pipe of a line raises the plant pressure above the 16 bar of a pipe in one hour
- **THEN** the change is rejected with the reason p_max

### Requirement: Step of an iteration
In one iteration every line with a negative ΔNPV SHALL get its best one-size change; afterwards the pairs SHALL be balanced in the model and the predicted NPV of the new state saved.

#### Scenario: Two improving lines
- **WHEN** two lines each have a negative ΔNPV for a larger pipe and a third line has none
- **THEN** the two lines get the next larger pipe, the third keeps its pipe, and no line changes by more than one size
