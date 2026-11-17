## ADDED Requirements

### Requirement: Protected line list in the dialog
The group "Hydraulic balancing of the customers" of the dynamic pipe sizing dialog SHALL have a list "Protected lines" of line IDs with editable entries and the buttons "+" (adds an empty entry), "−" (removes the selected entries) and "Add selected lines". "Add selected lines" SHALL add the IDs of the selected features of the active layer if it is the `lines` layer, otherwise of the project's `lines` layer, without adding an ID already in the list; without such a layer or without a selection it SHALL show an info in the message bar. The texts SHALL have a German translation.

#### Scenario: Lines selected on the map
- **WHEN** the lines 12 and 15 are selected in the `lines` layer and the list holds 12
- **THEN** "Add selected lines" adds 15 only

#### Scenario: No selection
- **WHEN** no feature of the `lines` layer is selected
- **THEN** "Add selected lines" adds nothing and an info in the message bar asks to select lines

### Requirement: The list is saved per version
At every start of the dynamic pipe sizing the valid IDs of the list SHALL be saved in `dynamic_sizing_protected_lines.json` in the folder of the loaded version, before a child version is created. When the dialog opens, the list SHALL be filled from this file of the loaded version; a missing or unreadable file SHALL give an empty list.

#### Scenario: Child version
- **WHEN** the list holds 12 and 15 and the sizing starts with a new child version
- **THEN** the child version's folder holds the file with 12 and 15, and the dialog opened in the child version shows them

#### Scenario: Version without a file
- **WHEN** the loaded version has no `dynamic_sizing_protected_lines.json`
- **THEN** the list is empty

### Requirement: Entries are checked at the start
Before the first simulation the dynamic pipe sizing SHALL stop with a message naming the entries, and without changing the version, if an entry of the list is not a positive integer. IDs that are no line of the selected network SHALL be named in the log and not protected in this run; they SHALL stay in the list and the file.

#### Scenario: Text entry
- **WHEN** the list holds "12a"
- **THEN** the run does not start and the message names "12a"

#### Scenario: Line of another network
- **WHEN** the list holds 900 and line 900 belongs to network 2 while network 1 is sized
- **THEN** the run starts, the log names 900 as not a line of network 1, and 900 stays in the list

### Requirement: Protected lines keep their pipes
In every pair and every iteration a protected line SHALL keep all its pipes: it SHALL NOT be changed by the pre-sizing, by the enlargement for the max. specific pressure loss or by the reduction of the hydraulic balancing. Its pressure loss SHALL still count for the customers it supplies. Per pair the log SHALL state the number of protected lines and the IDs of protected lines whose pipes exceed the max. specific pressure loss at their peak mass flow.

#### Scenario: Line that would be reduced
- **WHEN** line 12 would be reduced by the balancing and is protected
- **THEN** line 12 keeps its pipe bundle and the balancing reduces other lines of the same customers

#### Scenario: Undersized protected line
- **WHEN** protected line 15 exceeds the max. specific pressure loss of 300 Pa/m
- **THEN** line 15 is not enlarged and the log names line 15 for the pair

#### Scenario: Pre-sizing
- **WHEN** pre-sizing is on and line 12 is protected
- **THEN** line 12 keeps its pipes and all other lines are pre-sized as before

### Requirement: Protected lines in the iteration results
The iteration file SHALL state per pair the number of protected lines (`n_protected`) and mark each protected line (`protected: true`). Iteration files without these keys SHALL be read as 0 protected lines.

#### Scenario: Earlier iteration file
- **WHEN** an iteration file of an earlier run without `n_protected` is loaded
- **THEN** the iteration table and the map show it as before
