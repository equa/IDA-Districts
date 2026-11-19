## ADDED Requirements

### Requirement: Key figures of a version
`version_kpis(version, scenario)` SHALL return, each with its unit: heat delivered, peak load, network length, linear heat density, losses in % and EUR, pump energy, energy and costs per plant and carrier, NPV and NPV per MWh delivered, comfort deficits, and the results basis `full_year`, `periods` or `none`. The figures SHALL be computed by the same functions that the network report and the cost optimization report use. Without results, the result figures SHALL be `null` with a reason, and the network figures SHALL be given.

#### Scenario: Same as the report
- **WHEN** the network report and `version_kpis` are produced for the same version and scenario
- **THEN** the NPV, the heat delivered and the losses are equal

#### Scenario: No results
- **WHEN** a version has lines but no results
- **THEN** the network length and the linear heat density are given and the NPV is `null` with the reason "no results"

### Requirement: Comparing versions
`compare_versions(a, b, scenario)` SHALL return the figures of both versions and their differences, and SHALL note when the results bases differ.

#### Scenario: Different bases
- **WHEN** version a has full-year results and version b representative periods
- **THEN** the comparison lists the differences and notes the different results bases
