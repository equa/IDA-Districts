## ADDED Requirements

### Requirement: Pair table filled from the plant connections
The dynamic pipe sizing dialog SHALL have a table of supply/return sequence pairs with the columns supply, return and the design temperatures of supply and return, all editable, whose column widths can be changed with the mouse. When the dialog opens and when the network changes, the table SHALL be filled from the connections (`conn_type_seq` 1) of the templates of the network's energy plants: in `conn_seq` order, the k-th supply connection (`connections.type` 1) SHALL be paired with the k-th return connection (`type` 2), with the connections' design temperatures. The pairs of all plants SHALL be united; a sequence paired differently by two plants, or a plant with unequal numbers of supply and return connections, SHALL be reported in the log and give no pair for those connections. The table SHALL NOT be saved.

#### Scenario: Heating and cooling network
- **WHEN** the network's energy plant has the connections 1: supply 70 °C, 2: supply 10 °C, 3: return 30 °C, 4: return 18 °C
- **THEN** the table holds the pairs 1 → 3 (70/30 °C) and 2 → 4 (10/18 °C)

#### Scenario: Single circuit
- **WHEN** the network's energy plant has the connections 1: supply, 2: return
- **THEN** the table holds the single pair 1 → 2

#### Scenario: Contradicting plants
- **WHEN** one plant pairs supply 1 with return 3 and another plant pairs supply 1 with return 4
- **THEN** the log names the contradiction and neither pairing of sequence 1 is suggested

#### Scenario: Edited sequences
- **WHEN** the user changes the supply or return sequence of a row
- **THEN** the row's design temperatures are cleared and the fallback 70/40 °C applies to it

#### Scenario: Edited temperature
- **WHEN** the user enters 65,5 as the supply temperature of a row
- **THEN** the pair uses 65.5 °C for its lines without a temperature result; a text that is not a number stops the start with a message naming the row

### Requirement: Pairs are checked before the first simulation
Before the first simulation the dynamic pipe sizing SHALL stop with a message naming the pair, and without changing the version, if a sequence is not a positive integer, a sequence is used in more than one place of the table, a pair has supply = return, or a pair has no line whose pipe bundle contains both sequences, no energy plant of the network with the connections s and r, or no customer of the network with the connections s and r. Customers of the network without the connections s and r SHALL be skipped for that pair, and the log SHALL state their number per pair. The messages SHALL have a German translation.

#### Scenario: Pair without a plant
- **WHEN** the table holds the pair 5 → 6 and no energy plant of the network has the connections 5 and 6
- **THEN** the run stops before the first simulation with a message naming the pair 5/6

#### Scenario: Customers of one circuit only
- **WHEN** 30 customers of the network have only the connections 1 and 3 and the table holds the pairs 1 → 3 and 2 → 4
- **THEN** the run starts, the 30 customers are balanced in the pair 1/3 only, and the log reports 30 customers skipped for the pair 2/4

#### Scenario: Sequence used twice
- **WHEN** the table holds the pairs 1 → 3 and 3 → 4
- **THEN** the run stops before the first simulation with a message naming the sequence 3

### Requirement: Each pair is balanced as its own circuit
In every iteration the dynamic pipe sizing SHALL, for every pair (s, r), run the flow tracing on the line results `line_s_mdot$s` over the lines whose pipe bundle contains both s and r, with the connections s and r (`conn_type_seq` 1) of the customers and energy plants, and size the pipes s and r of these lines with the pair's own critical time, weak point and target. Lines whose bundle lacks s or r SHALL be neither part of the pair's flow tracing nor sized in the pair.

#### Scenario: Cooling pair on part of the network
- **WHEN** the pair 2 → 4 exists only on the 32 lines with four pipes of a network whose other 53 lines have only the pipes 1 and 3
- **THEN** the pair 2/4 is traced and sized on the 32 lines only, and the pipes of the 53 lines are not touched by it

#### Scenario: Single pair as before
- **WHEN** the network has one pair 1 → 2 and its line temperature results exist
- **THEN** weak point, target and new pipes are the same as before this change

### Requirement: Line temperatures are required
After loading the results of an iteration, the dynamic pipe sizing SHALL stop with a message naming the missing tables, and without changing the pipes, if `line_s_mdot$s`, `line_s_temp$s` or `line_s_temp$r` of a pair does not exist in the version. A line without a temperature value at the critical time SHALL use the design temperature of the pair's row (70 °C supply / 40 °C return if the row has none), and the log SHALL state the number of such lines per pair.

#### Scenario: Temperature outputs not requested
- **WHEN** the simulation results contain `line_s_mdot$1` but no `line_s_temp$3`, and the table holds the pair 1 → 3
- **THEN** the run stops with a message naming `line_s_temp$3` and asking to request the line temperature outputs

#### Scenario: Single line without a value
- **WHEN** the temperature tables exist and 2 lines of the pair 1/3 have no value at the critical time
- **THEN** these lines use the row's design temperatures and the log reports 2 lines for the pair 1/3

### Requirement: Changed lines keep all their other pipes
When the pipes of a line change, the line SHALL get a pipe bundle with the new pipes of every pair and the unchanged pipes of all other sequences of its current bundle; an existing bundle with exactly these pipes SHALL be reused, otherwise a new bundle SHALL be created with the positions (x, y, ambient) of the current bundle for every sequence.

#### Scenario: Four-pipe line, heating changed
- **WHEN** a line has the bundle 1: DRE-50, 2: DRE-65, 3: DRE-50, 4: DRE-65 and the pair 1/3 reduces to DRE-40 while the pair 2/4 keeps its pipes
- **THEN** the line gets a bundle 1: DRE-40, 2: DRE-65, 3: DRE-40, 4: DRE-65

#### Scenario: Unpaired sequence
- **WHEN** a line's bundle has the sequences 1, 2 and 3, the table holds only the pair 1 → 2, and the pair changes its pipes
- **THEN** the new bundle still contains the pipe of sequence 3 with its position

### Requirement: One decision per iteration over all pairs
The outcome of an iteration SHALL be decided from the merged pipes of all pairs: converged if no pair changes a pipe, oscillation if the merged pipes of all lines repeat an earlier iteration, otherwise changed (or max. iterations reached).

#### Scenario: Only one pair changes
- **WHEN** in an iteration the pair 1/3 changes no pipe and the pair 2/4 changes two lines
- **THEN** the iteration's outcome is "pipes changed" and the next iteration is built and simulated
