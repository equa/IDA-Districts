# statics-steel-solver Specification

## Purpose
Statics of rigid steel pipes (single and twin) on the statics model under EN 13941 / AGFW FW 401: loads, FE model on non-linear soil springs, laying methods, one-time compensators, load steps with two friction coefficients, expansion pads, checks with limits that name their source, result tables and report. Created by archiving change statics-steel-solver.
## Requirements
### Requirement: Calculate statics
"Calculate statics" SHALL calculate the rigid steel pipes (single and twin) of the loaded version's statics model. It SHALL refuse a model whose state is not current and name the reason. The calculation SHALL run as a background task with progress and cancel on its own DB connection, and SHALL write its results in one transaction at the end. A cancelled or failed calculation SHALL leave the previous results unchanged. Pipes that are not rigid steel (flexible, bare plastic) SHALL be skipped and listed; a rigid pipe that meets a skipped pipe at a junction SHALL get a free end there and a finding.

#### Scenario: Model out of date
- **WHEN** a line is moved after the statics model was built and the user starts "Calculate statics"
- **THEN** nothing is calculated and the message says the statics model is out of date

#### Scenario: Cancelled run
- **WHEN** a version has results and the user cancels a new calculation
- **THEN** the previous results are still there and unchanged

#### Scenario: Flexible line skipped
- **WHEN** a network has rigid lines and one isopex service line on a tee
- **THEN** the rigid lines have results, the isopex line is listed as skipped and the tee has a finding for the connection

### Requirement: Loads per pipe
For each pipe (each carrier of a twin) the calculation SHALL use the higher of the design value and the simulated maximum for temperature and pressure. Design values SHALL be the parameters `design_temperature_c`, `design_pressure_bar` and `laying_temperature_c`, overridden by `statics_sections` values stored in the model. The simulated maximum SHALL be taken over all times and segments of `line_s_temp$<seq>` and `line_s_p$<seq>` of the pipe's line and sequence, including the `_period<k>` tables. The lowest temperature of the cycle SHALL be the laying temperature. The results SHALL name the source of each value (parameter, section override, simulation).

#### Scenario: Simulation above design
- **WHEN** the design temperature is 120 °C and the simulated maximum of a supply pipe is 125 °C
- **THEN** that pipe is calculated at 125 °C with source simulation

#### Scenario: No results
- **WHEN** a version has no simulation results
- **THEN** every pipe is calculated at the design values and the report says the twin bending from a temperature difference is not included

#### Scenario: Section override
- **WHEN** a section override sets the design temperature to 90 °C and no results exist
- **THEN** the pipes of that section are calculated at 90 °C with source section override

### Requirement: Twin pipe
A twin pipe SHALL be one beam with the soil acting on its casing; both carriers SHALL deform with the casing (plane sections), with their offsets from the casing axis. A temperature difference between the carriers SHALL bend the twin. Each carrier's stress SHALL be computed from the axial strain, the curvature times its offset, and its own pressure.

#### Scenario: Equal temperatures
- **WHEN** both carriers of a straight restrained twin have 80 °C
- **THEN** both carriers have the same axial stress and the twin has no bending

#### Scenario: Temperature difference
- **WHEN** the carriers of a twin have 80 °C and 50 °C
- **THEN** the twin's axial strain is that of the mean temperature and the hotter carrier has the higher compressive stress

### Requirement: Soil
The axial friction per metre SHALL be μ · [(1 + K0)/2 · γ · Z · π · Da + G] with K0 = 1 − sin φ, Z = cover + Da/2 and G the weight of steel, water, foam and casing; below the groundwater depth γ SHALL be reduced by 10 kN/m³. The lateral soil SHALL resist up to the passive limit K_p · γ · Z · Da, K_p = tan²(45° + φ/2), and stay at that limit beyond. Upward movement SHALL be limited by the weight of the soil above plus G. Each load step SHALL be calculated with the upper friction coefficient (stresses, forces) and with the lower one (displacements, legs, pads). Soil values SHALL come from the parameters, overridden by section.

#### Scenario: Lmax of the isoplus single pipe
- **WHEN** a straight DN 100 single pipe with standard insulation and 0.80 m cover runs 148 m between two expansion legs (free ends) at 130 °C, μ 0.40, γ 19 kN/m³, φ 32.5°, with rigid-plastic friction
- **THEN** its axial stress at the centre is 190 N/mm² within ±2 % (isoplus planning manual 12/4)

#### Scenario: Lower friction gives larger movement
- **WHEN** an L bend is calculated with μ 0.40 and μ 0.20
- **THEN** the leg's movement with 0.20 is larger and is the one used for the pads

### Requirement: Laying methods
The laying method of a section SHALL set its stress-free temperature: cold and conventional at the laying temperature; thermal prestressing and one-time compensators at the preheating temperature, by default the mean of laying and design temperature. Sections with prestressed legs SHALL design their legs and pads with VTf = T_E + (T_B − T_E)/3. Self-prestressing SHALL be reported as not supported and not calculated. An unknown method SHALL be a finding. Cold laying above `cold_laying_max_single_c` (single) or `cold_laying_max_twin_c` (twin) without length limitation SHALL be a finding, and a leg movement above `movement_prestress_mm` without prestressed legs SHALL be a finding.

#### Scenario: Thermal prestressing
- **WHEN** a section with laying temperature 10 °C and design temperature 130 °C is laid with thermal prestressing
- **THEN** it is stress-free at 70 °C and its restrained axial stress at 130 °C is that of a 60 K difference

#### Scenario: Prestressed legs
- **WHEN** a leg with laying temperature 10 °C and operating temperature 130 °C has prestressed legs
- **THEN** its pads are designed with VTf 50 °C

#### Scenario: Self-prestressing
- **WHEN** a section's laying method is self_prestress
- **THEN** it is not calculated and the report says the method is not supported

### Requirement: One-time compensators
A `statics_points` one-time compensator SHALL let the pipe on its two sides slide against each other up to the preheating temperature and then act as rigid pipe. Its travel, axial spring rate and bellows area SHALL come from the point's columns, else from the isoplus table by DN. A one-time compensator SHALL be a finding when its travel exceeds the maximum travel, when it lies outside the restrained zone, in a bend, with less than 6 m of straight pipe on a side, or without an expansion leg or fixed point at both ends of its stretch.

#### Scenario: Travel exceeded
- **WHEN** a DN 100 one-time compensator must take 95 mm and has no own travel value
- **THEN** a finding names the travel 95 mm against 80 mm (isoplus planning manual 7/2)

#### Scenario: Compensator in the sliding zone
- **WHEN** a one-time compensator lies in a stretch shorter than the friction length
- **THEN** a finding says it lies outside the restrained zone

### Requirement: Load steps and solution
Each calculation SHALL run the steps stress-free state, heat-up to the maximum temperature with pressure, cooling to the laying temperature and second heat-up, in temperature increments of at most `load_increment_k`, with sticking and sliding friction. Each connected part of the network SHALL be solved on its own; a part that does not converge within `max_iterations` per increment SHALL get a finding and no results, and the other parts SHALL still be calculated. The reactions of every part SHALL be in equilibrium with its loads.

#### Scenario: Stress range from reversal
- **WHEN** a straight pipe between two L bends is heated, cooled and heated again
- **THEN** the sliding zones reverse on cooling and the stress range is taken over the steps

#### Scenario: Equilibrium
- **WHEN** a part with one fixed point is calculated
- **THEN** the sum of the soil reactions and the fixed point force is zero within the tolerance

### Requirement: Expansion pads
The calculation SHALL place pads where the lateral movement of a leg with the lower friction exceeds the movement at which the soil reaches its limit: in pieces of `pad_piece_m` along the leg and layers of `pad_layer_mm`, until the pad compression stays at most `pad_max_compression` by the isoplus pad curve. It SHALL recalculate with the pads until they do not change. A pad thicker than `pad_max_thickness_mm` SHALL be a finding that names prestressed legs or a longer leg.

#### Scenario: Pads at an L bend
- **WHEN** an L bend's leg moves 50 mm sideways
- **THEN** the leg has pads in 40 mm layers and whole metres, and their compression is at most 50 %

#### Scenario: Pad too thick
- **WHEN** a leg needs a pad of 160 mm
- **THEN** a finding says to prestress the legs or lengthen the leg

### Requirement: Checks and limits
Each check SHALL compare its value with a limit parameter that has a source. A check SHALL give a verdict only when its limit has a value and a source; otherwise it SHALL report the utilisation against the yield strength and "limit not confirmed". The checks SHALL be: axial stress of the straight pipe in the restrained zone against the series' maximum axial stress, else `sigma_ax_allow_n7mm2`; PUR shear stress at the steel pipe F'_R / (π · Σ d_steel) against `tau_pur_max_n7mm2`; minimum cover against the isoplus table by DN and traffic load; pressure against `pressure_max_bar`; stress range at bends, tees and kinks with the stress intensification factor against `stress_range_allow_n7mm2`; hoop stress against `hoop_stress_allow_n7mm2`; upheaval buckling against `buckling_safety`.

#### Scenario: Cold laying at 85 °C
- **WHEN** a long straight single pipe laid at 10 °C is heated to 85 °C
- **THEN** its axial stress stays below 190 N/mm² and the check passes

#### Scenario: Cold laying at 95 °C
- **WHEN** the same pipe is heated to 95 °C
- **THEN** its axial stress exceeds 190 N/mm² and the check fails with the limit's source

#### Scenario: Limit not confirmed
- **WHEN** `stress_range_allow_n7mm2` is empty
- **THEN** the bends get their stress range and utilisation against Re with "limit not confirmed" and no verdict

#### Scenario: Maximum cover by shear
- **WHEN** a DN 100 single pipe with standard insulation lies 4.5 m deep
- **THEN** the PUR shear check fails (isoplus planning manual 9/12 allows 4.00 m)

### Requirement: Results and result state
A calculation SHALL store `statics_result_run` (time, model fingerprint, parameters used, summary, status), `statics_result_elements` (per element, carrier, load step and friction case: stresses, stress intensification factor, utilisation, governing check), `statics_result_nodes` (displacements, axial force, pads) and `statics_result_findings` (rule, severity, element or node, values with limit and source, text). The result state SHALL be missing without a run, out of date when the model is not current, its fingerprint differs from the run's, or the statics parameters, the material values or the series' allowed axial stress changed since the run, and current otherwise. New versions SHALL get the tables from `DB_versionTablesDefault.txt`, existing versions on load, child versions with their rows through the schema copy.

#### Scenario: Model rebuilt after a run
- **WHEN** the model is built again with a changed line after a calculation
- **THEN** the result state is out of date

#### Scenario: Old version loaded
- **WHEN** a version created before this change is loaded
- **THEN** the four result tables exist afterwards and are empty

### Requirement: Statics report
After a calculation the plugin SHALL show a report with the parameters used and their sources, the counts of pipes, elements and parts, the skipped lines, the parts not converged, the findings by rule, the pads, and the note "fatigue not checked". Report texts SHALL be translated (de/en).

#### Scenario: Report after a run
- **WHEN** a calculation finishes with two findings
- **THEN** the report lists both with their limits and sources and says fatigue was not checked

