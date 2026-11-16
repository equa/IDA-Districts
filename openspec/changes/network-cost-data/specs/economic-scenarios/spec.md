## ADDED Requirements

### Requirement: Named economic scenarios
A project SHALL have one or more economic scenarios (`economic_scenarios`), each with a name, interest rate, period, residual value yes/no, default surface, electricity profile file (optional), pump costs (€/kW, %/a, lifetime), `example` and a description. The scenario tables SHALL be edited through table dialogs filtered by scenario. Every evaluation SHALL name the scenario it used.

#### Scenario: Second scenario
- **WHEN** the user copies "base" to "high electricity" and doubles the electricity start price there
- **THEN** both scenarios exist, and an evaluation with "base" is unchanged

### Requirement: Price per cost group and year
For each cost group (electricity, heat, cold, maintenance, investment) a scenario SHALL have a start price and an escalation rate; the level of year t SHALL be the factor of `price_levels` for that year if present, otherwise (1 + escalation)^t.

#### Scenario: Escalation
- **WHEN** electricity has escalation 2 %/a and no level table
- **THEN** the level of year 10 is 1.02^10

#### Scenario: Level table
- **WHEN** `price_levels` has electricity factor 1.5 for year 5
- **THEN** the level of year 5 is 1.5 and the other years follow the escalation

### Requirement: Electricity profile
A scenario MAY reference an hourly electricity profile file (.csv or .prn, 8760 or 8784 values), which SHALL be copied into `<project>\prices\` and normalized to mean 1; the electricity price of year t and hour h SHALL be start price × level(t) × shape(h). Without a file the shape SHALL be 1. A file with another number of values SHALL be rejected with a message naming the count.

#### Scenario: Profile with peaks
- **WHEN** the profile has values 2 in the 10 % most expensive hours and the rest such that the mean is 1
- **THEN** the price in those hours is twice the start price × level

#### Scenario: Wrong length
- **WHEN** the user selects a file with 8000 values
- **THEN** it is rejected with a message naming 8000

### Requirement: Price curves for heat and cold
A scenario SHALL have price curves c(T_supply) for heat and for cold (€/kWh at year 0), interpolated linearly between the rows and constant outside them; one row SHALL give a constant price. The price of year t SHALL be c(T) × level(t) of the cost group heat or cold.

#### Scenario: Interpolation
- **WHEN** the heat curve has 0.08 €/kWh at 70 °C and 0.11 €/kWh at 95 °C
- **THEN** the price at 80 °C is 0.092 €/kWh, at 60 °C 0.08 €/kWh
