## ADDED Requirements

### Requirement: Iteration file per pair
Every iteration of the dynamic pipe sizing SHALL be saved as `dynamic_sizing_iter<n>.json` in the version folder with the fields `iteration`, `started`, `outcome`, `n_changed` and a list `pairs`, one entry per pair with `supply`, `return`, `temps`, the pair's critical time, weak point, target, quota, spread after the sizing, number of pre-sized lines, balancing steps, changed lines, skipped customers, and its `customers` and `lines` (pipe before and after the sizing of the supply sequence). The c_lid of every pair SHALL be saved as `dynamic_sizing_iter<n>_c_lid_<s>_<r>.json` and `dynamic_sizing_iter<n>_c_lid_sized_<s>_<r>.json`. A new run SHALL delete all these files of the version first.

#### Scenario: Two pairs
- **WHEN** an iteration of a run with the pairs 1 → 3 and 2 → 4 ends
- **THEN** its file holds two entries in `pairs` (1/3 and 2/4) with their own weak points, and the version folder holds the c_lid files of both pairs

### Requirement: Iteration files of earlier runs are read as pair 1/2
An iteration file without `pairs` SHALL be read as one pair with supply 1 and return 2 whose results are the file's top-level fields.

#### Scenario: File of an earlier version
- **WHEN** the loaded version contains an iteration file written before this change
- **THEN** the iteration table shows it as one row with the pair 1/2 and it can be shown on the map

### Requirement: Iteration table per iteration and pair
The iteration table SHALL show one row per iteration and pair, with a column "Pair" (`s/r`) after the column "Iteration"; the outcome SHALL be shown in every row of the iteration. Showing the selected rows on the map SHALL show the selected combinations of iteration and pair.

#### Scenario: Rows of two pairs
- **WHEN** a run with the pairs 1 → 3 and 2 → 4 has finished two iterations
- **THEN** the table has four rows: 1 – 1/3, 1 – 2/4, 2 – 1/3, 2 – 2/4

### Requirement: Map layers per iteration and pair
The group "Dynamic pipe sizing" SHALL contain one subgroup per iteration and in it one subgroup "Pair s/r" per shown pair with the customer, line and new-pipe layers. The class bounds of the customers' dp and the lines' mass flow SHALL be computed per pair over all iterations of the run. Removing the layers of an iteration SHALL remove the layers of all its pairs. The subgroup name SHALL have a German translation.

#### Scenario: Heating and cooling on the map
- **WHEN** the user shows the iteration 2 of a run with the pairs 1 → 3 and 2 → 4
- **THEN** the subgroup "Iteration 2" contains the subgroups "Pair 1/3" and "Pair 2/4", each with three layers, and the classes of the pair 2/4 are those of the cooling circuit
