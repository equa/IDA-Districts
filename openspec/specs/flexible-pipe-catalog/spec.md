# flexible-pipe-catalog Specification

## Purpose
TBD - created by archiving change pipe-series-catalog. Update Purpose after archive.
## Requirements
### Requirement: Flexible pipes in the templates
The templates `heating_network` and `db_default_values` SHALL contain the flexible pipes of the isoplus planning manual chapter 3 (as of 2015/2016): isoflex 20, 28, 28 v, 28+28; isocu 22, 28, 22+22, 28+28; isopex heating H-25 … H-140 with the variants v and u and the 12 m bars H-125/140/160 Stg., heating twins H-20+20 … H-75+75 with the variants v; isopex sanitary S-25 … S-63 and twins S-25+20 … S-63+32; isoclima 20 … 110 with 110 u. isowell SHALL NOT be included. Each pipe SHALL have the catalogue's carrier outer diameter and wall, casing diameter, minimum bend radius (none for bars) and `p_max_bar`, its series (except the carriers of the unequal sanitary twins), and a description naming the source and the assumed values.

#### Scenario: New project from a template
- **WHEN** a project is created from the template `heating_network`
- **THEN** the pipe "isoplus isopex H-50" exists with inner diameter 40.8 mm, minimum bend radius 0.9 m, `p_max_bar` 6, series "isoplus isopex H", and a construction whose outer diameter is 110 mm

#### Scenario: isowell left out
- **WHEN** the pipes of the template are listed
- **THEN** no pipe of isowell exists

### Requirement: Flexible series in the templates
The templates SHALL contain one `pipe_series` row per catalogue variant, so that the inner diameters within a series are unique: isoflex, isoflex v, isoflex twin, isocu, isocu twin, isopex H, H u, H v, H bar, H twin, H twin v, isopex S, S twin, isoclima, isoclima u. Each row SHALL have its system type (`flexible_metal` for isoflex and isocu, `flexible_plastic` for isopex and isoclima), standard, temperature limits, the allowed axial stress where the catalogue gives it (isoflex 150, isocu 110 N/mm²), and the safety factor 1.25 for isopex and isoclima. The isopex heating series SHALL have the catalogue's heating pressure ratings, the isopex sanitary series the sanitary ratings, the isoclima series the PE 100 ratings.

The carrier pipes of the unequal sanitary twins S-25+20 … S-63+32 SHALL have no series text, so that the pipe sizing does not resize them; the series row "isoplus isopex S twin" SHALL hold their limits and ratings.

#### Scenario: Unequal twin not resized
- **WHEN** the pipe sizing looks for the next smaller pipe of the 50 mm carrier of "isoplus isopex S-50+32"
- **THEN** there is none

#### Scenario: Unique diameters
- **WHEN** the inner diameters of the pipes of any series of the template are compared
- **THEN** no two pipes of one series have the same inner diameter

#### Scenario: Pressure rating
- **WHEN** the pressure ratings of "isoplus isopex H" are read for 50 years at 70 °C
- **THEN** the allowed pressure is 8.5 bar

### Requirement: Rigid series in the templates
The templates SHALL have the series rows "Isoplus DRE Standard" (`rigid_single`, EN 253) and "Isoplus DRD Standard" (`rigid_twin`, EN 15698-1) with 120 °C continuous and 140 °C peak temperature and without allowed axial stress.

#### Scenario: Rigid series
- **WHEN** the series "Isoplus DRE Standard" of the template is read
- **THEN** its system type is `rigid_single`, its temperatures are 120 and 140 °C and its axial stress is empty

### Requirement: Materials of the flexible pipes
The templates SHALL contain the materials P195GH, Cu-DHP, PE-Xa, PE 100 with the catalogue's density, thermal conductivity, specific heat, Young's modulus, yield strength and thermal expansion at 20 °C, the casing material PE-LLD (λ 0.33 W/(m·K)) and the PUR foam of flexible pipes (λ 0.0221 W/(m·K)) as a material of its own.

#### Scenario: PE-Xa
- **WHEN** the material PE-Xa of the template is read
- **THEN** its Young's modulus is 600 N/mm², its yield strength 17 N/mm² and its thermal expansion 1.5e-4 1/K

### Requirement: Layers and twin geometry checked against the catalogue's heat loss
The layers of a flexible pipe SHALL be the carrier wall, the PUR foam and a PE-LLD casing wall of `max(2 mm, 0.02·Da)`. A twin pipe SHALL have one pipe bundle with both carrier pipes in one casing construction, one above the other with the smaller pipe on top and equal clearance between the pipes and to the foam body. No value SHALL be fitted to u. The u computed with the plugin's resistance model (cover 0.80 m, ground 1.0 W/(m·K); single pipes with a neighbour at 100 mm) SHALL be within 0 … +13 % of the catalogue's u for every single pipe except the 12 m bars, within −8 … +13 % for the bars H-125/140/160 Stg., and within 0 … +23 % for every twin pipe.

#### Scenario: Single pipe
- **WHEN** the u of "isoplus isopex H-63" is computed from its layers under the catalogue's conditions
- **THEN** it is between 0.1712 and 0.1935 W/(m·K) (0 … +13 %)

#### Scenario: Twin pipe with unequal carriers
- **WHEN** a network with a line of the twin "isoplus isopex S-50+32" is built for the simulation
- **THEN** the twin is converted without error and its u is between 0.1960 and 0.2411 W/(m·K) (0 … +23 %)

### Requirement: No costs for flexible pipes
Flexible pipes in the templates SHALL have no costs, maintenance and lifetime and `example` false.

#### Scenario: Costs of a flexible pipe
- **WHEN** the pipe "isoplus isocu 22" of the template is read
- **THEN** its costs are empty and `example` is false

