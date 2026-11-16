## ADDED Requirements

### Requirement: Detection of network pumps in a template
The plugin SHALL detect the network pumps of every energy plant and customer template of the project by reading the template's `.idm` file into a graph of components and their fluid sides; only links between fluid ports (inlet/outlet, liq…, term…, evap…, cond…, IN/OUT, HXIN/HXOUT) count. Heat exchangers (liqA…/liqB…), heat pumps (evap…/cond…) and tanks (IN/OUT vs. HXIN/HXOUT) SHALL have separate sides; any other component SHALL be one side. A component of type `PUMP`, `PUMPMCTRL` or `PUMPCIRC` reachable from the template's network connection components (`<bundle>_<seq>_Flowmeter2`, `PMT2mux_<bundle>_<seq>_<type>_<conn>`) SHALL be an entry of kind `variable` with the power variable `PPUMP`. A pump in another `.idm` file of the template folder (a macro) SHALL NOT be analysed and SHALL give a warning naming it. Entries of kind `estimate` SHALL only be added by the user.

#### Scenario: Plant pump found
- **WHEN** the detection runs on the energy plant template `1_ideal_heat_source`
- **THEN** its `PUMP` components on the network side are entries of kind `variable` with `PPUMP`

#### Scenario: Building-circuit pump not found
- **WHEN** the detection runs on the customer template `1_simplified_consumer`
- **THEN** its `PUMP` between the load model and side B of `hx_substation` is not an entry

#### Scenario: Decentral pumps of the low-temperature sample
- **WHEN** the detection runs on the customer template `4_simplified_consumer_hp` of the IDA sample `low_temperature_network`
- **THEN** `PUMP` (network water through the evaporator of `HP_B2B_substation`) and `PUMP1` (side A of `hx_cooling_substation`) are entries of kind `variable`, and `dhw_pump_sub` behind the condenser is not an entry

#### Scenario: Pump on the source side of a plant heat exchanger
- **WHEN** the detection runs on the energy plant template `3_waste heat source` of `low_temperature_network`
- **THEN** its `PUMP` on side B of the heat exchanger is not an entry

#### Scenario: Pump in a macro
- **WHEN** another `.idm` file of a template folder contains a pump
- **THEN** the detection shows a warning naming the template, the file and the pump, and the other templates are detected

### Requirement: Editable pump list
The requested outputs dialog SHALL open a dialog "Network pumps" that lists the entries of all templates (feature type, template, component, kind, power variable, η and Δp_int for kind `estimate`, source `found`/`added`). The user SHALL be able to run the detection again, add an entry (a component of the template and one of its variables, or kind `estimate`), remove an entry and edit η (default 0.5) and Δp_int (default 20 kPa). A removed found entry SHALL NOT come back from a new detection. An entry whose component no longer exists in its template SHALL be shown greyed with a warning and SHALL be skipped when outputs are written.

#### Scenario: Add a component that contains a pump
- **WHEN** the user adds the component `HP_B2B_substation` of a customer template with kind `estimate` and η 0.4
- **THEN** the list contains the entry with source `added`, η 0.4 and Δp_int 20 kPa

#### Scenario: Removed entry stays removed
- **WHEN** the user removes a found entry, closes the dialog and runs the detection again
- **THEN** the entry is not in the list

#### Scenario: Component deleted in IDA
- **WHEN** a listed component no longer exists in its template
- **THEN** the dialog shows the entry greyed with a warning, and no output is written for it

### Requirement: Pump list saved in the project
The pump list SHALL be saved in the project folder as `networkPumps.json`, next to `requestedOutputs.txt` and the template folders, and SHALL be the same for every version of the project. A project without the file SHALL get the detected list when the dialog opens or when pump power outputs are first written.

#### Scenario: Child version
- **WHEN** a child version is created and loaded
- **THEN** the dialog shows the same pump list as in the parent version

#### Scenario: Existing project
- **WHEN** a project created before this change is opened and pump power outputs are requested
- **THEN** the detection runs, `networkPumps.json` is written, and the outputs follow its entries
