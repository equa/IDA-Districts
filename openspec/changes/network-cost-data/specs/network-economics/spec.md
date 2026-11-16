## ADDED Requirements

### Requirement: Net present value
The economics module SHALL calculate for a scenario the yearly cash flows of years 1 to period (energy × price of the year, maintenance as % of the investment, replacements at each multiple of an item's lifetime within the period), the residual value at the end of the period (linear over the lifetime, if the scenario sets it), the net present value discounted with the interest rate (investment in year 0) and the annuity (NPV × annuity factor), split by cost group (investment, pump energy, heat losses, cold losses, maintenance). Quantities SHALL be signed: a gain lowers the cost.

#### Scenario: Pump replacement
- **WHEN** the period is 40 years and the pumps have a lifetime of 15 years
- **THEN** the pumps are bought in year 0 and replaced in years 15 and 30, and with residual value the year-30 pumps keep 5/15 of their cost at the end

#### Scenario: No interest
- **WHEN** the interest rate is 0 and all levels are 1
- **THEN** the NPV equals investment + period × yearly operating and maintenance costs + replacements − residual value

#### Scenario: Ground gain
- **WHEN** a heating pipe gains heat from the ground over the year
- **THEN** its heat-loss cost is negative

### Requirement: Heat flow per pipe
The loss module SHALL calculate per pipe and hour Q = U'·L·(T_pipe − T_amb) with U' from the pipe's layers and its position in the bundle, T_pipe from the simulated line temperature of its sequence and T_amb from its ambient (ground from the version's ground model, air from the climate file, duct from its setting), and SHALL assign Q to heat or cold by the pipe's pair. Per line, the sum over its pipes SHALL be compared with the simulated `QAmbtotal`; a deviation of more than 15 % of the yearly total SHALL be listed.

#### Scenario: Two-pipe line
- **WHEN** a two-pipe heating line has been simulated for a year
- **THEN** both pipes have hourly heat flows assigned to heat, and their yearly sum is within 15 % of `QAmbtotal` or the line is listed

### Requirement: Economics section of the network report
The network report dialog SHALL have an option "Economics" and a scenario selection. The section SHALL show for the loaded version: investment (pipes in use × costs, trench per surface, pumps from the peak of the simulated pump power × €/kW), yearly pump energy and its cost, yearly heat and cold losses priced with c(T_supply) of the plant per hour, maintenance, the NPV split by cost group, the annuity and the scenario name, and "example values in use" if a pipe in use or the scenario is an example. Without results covering a full year, or without pump power, line temperature, plant temperature or line loss results, the section SHALL name what is missing instead of values. Pipes in use without costs SHALL be listed.

#### Scenario: Full year simulated
- **WHEN** a version simulated for a full year with pump power, line temperature, plant temperature and line loss outputs is reported with scenario "base"
- **THEN** the section shows the NPV split, the annuity, "base" and "example values in use"

#### Scenario: One day simulated
- **WHEN** the version's results cover one day
- **THEN** the section says that results covering a full year are needed and shows no NPV
