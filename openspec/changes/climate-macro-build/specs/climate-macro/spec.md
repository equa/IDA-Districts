## ADDED Requirements

### Requirement: Climate file columns
The plugin SHALL read the columns of a climate file from its header row by name, without case: a first line starting
with `#` or holding non-numeric tokens is a header. A file without a header SHALL have the IDA layout Time, TAir,
RelHum, WindDir, WindVel, IDirNorm, IDiffHor. The wind SHALL be given either as direction and speed or as `WindX` and
`WindY`. A file without time, air temperature, relative humidity, direct normal or diffuse horizontal radiation, or
without one of the two wind forms, SHALL be refused with a message naming the missing quantities and the file's
columns. Columns with other names SHALL be extra columns under their own name.

#### Scenario: File without a header
- **WHEN** the columns of BROMMA.PRN are read
- **THEN** they are Time, TAir, RelHum, WindDir, WindVel, IDirNorm, IDiffHor at positions 1 to 7, with no extra column

#### Scenario: File with a header
- **WHEN** the columns of ABO_dry_NORMAL.prn are read
- **THEN** the wind is `WindX`/`WindY` at positions 4 and 5, and SkyCover, PRECIPITATION and ALBEDO are extra columns at 8 to 10

#### Scenario: Required quantity missing
- **WHEN** a file's header has no air temperature
- **THEN** reading it raises an error naming the air temperature and listing the file's columns

### Requirement: Generated climate macro
The plugin SHALL generate the climate macro `Climate-macro` (`.idm` and `.idc`) from the version's climate settings
(file, site, time zone, height) and the modelling settings. It SHALL contain the source file with all columns, the
climate processor with site and the file's air temperature, humidity, radiation and wind (direction and speed, or
`WindX`/`WindY`), the wind velocity `vel` (the speed column, or √(dx²+dy²)), the vertical irradiation `ISolar` with its
shading schedule, the global horizontal radiation `IGlob` = IDIRNORM·sin(ELEVSUN) + IDIFFHOR, the ground temperature
`TGround` (Kusuda, or the constant ground temperature with the constant ground model) and the duct temperature `TDuct`
from the modelling settings. `SkyCover` and `PRECIPITATION` columns SHALL be bound to the climate processor, an `ALBEDO`
column SHALL give a gain `albedo` of 0.01 × ALBEDO (its only gain: IDA compares names without case), and every other
extra column SHALL give a gain named after it. The names
read by networks, supervisory models and templates (`climate_processor`, `vel`, `ISolar`, `TGround`, `TDuct`) SHALL stay.

#### Scenario: IDA layout
- **WHEN** the macro is generated for BROMMA.PRN
- **THEN** the processor takes WINDDIR and WINDVELREF from the file, `vel` is the speed column, `IGlob` exists, and there are no extra gains

#### Scenario: Header with wind components and extra columns
- **WHEN** the macro is generated for ABO_dry_NORMAL.prn
- **THEN** the processor takes WINDX and WINDY, `vel` is √(dx²+dy²), SKYCOVER and PRECIPITATION are bound to the file, and gains `albedo` (0.01 × ALBEDO), `SkyCover` and `PRECIPITATION` exist

#### Scenario: Constant ground and duct temperature
- **WHEN** the modelling settings have the constant ground model with 9 °C and a duct temperature of 18 °C
- **THEN** `TGround` gives 9 °C and `TDuct` 18 °C, and the macro has no Kusuda model

#### Scenario: IDA accepts the macro
- **WHEN** a network with the generated macro for BROMMA.PRN and for ABO_dry_NORMAL.prn is simulated in IDA Districts
- **THEN** both simulations finish, and `IGlob` over the year equals the Python global horizontal radiation within 1 %

### Requirement: Where the macro is written
The generated macro SHALL be written into the project's `climate\climate` folder and into every customer and plant
template folder of the project by the per-version climate dialog, at every network build and before a template is
opened in IDA; networks, the supervisory model and new templates SHALL take the project's generated macro. The plugin
SHALL not ship climate macro files; a new project SHALL get its macros generated at its first build, template opening
or climate dialog.

#### Scenario: Existing template refreshed
- **WHEN** a customer template whose macro was written for another climate file is opened
- **THEN** its macro is generated for the version's current climate file before IDA opens it

#### Scenario: New project
- **WHEN** a project created from a project template is built for the first time
- **THEN** its `climate\climate\climate-macro.idm` and the macros of its customer and plant templates are generated for the version's climate file

### Requirement: Hand-edited macros and the resources tab
A climate macro that the generator did not write SHALL be replaced and kept once as `climate-macro.idm.bak` next to it.
The resources tab SHALL have no action to edit the climate macro; the per-version climate dialog SHALL stay.

#### Scenario: Backup once
- **WHEN** a project macro without the generator's marker is replaced, and then replaced again
- **THEN** `climate-macro.idm.bak` holds the hand-made macro, and the second replacement does not overwrite it

### Requirement: Python climate signals follow the file
`ground_climate.weatherFromClimate`, the period selection and the Kusuda calculation SHALL read the columns as the
generator does; the sky temperature SHALL use the file's sky cover when present, and the albedo SHALL be the file's
albedo (as a fraction) when present, otherwise the given constant.

#### Scenario: Sky cover and albedo from the file
- **WHEN** the weather is computed from ABO_dry_NORMAL.prn
- **THEN** the sky temperature uses its SkyCover column and the albedo is 0.5 where ALBEDO is 50
