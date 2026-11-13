## ADDED Requirements

### Requirement: Inner diameters in the iteration file
The iteration file of the dynamic pipe sizing SHALL store for every line of a pair `d` and `d_new`: the inner diameter of the pair's supply pipe before and after the sizing of the iteration in mm, rounded to 0.1 mm. In a reference run (iteration 0) `d_new` SHALL equal `d`. Iteration files without these keys SHALL still be read, with `d` and `d_new` empty.

#### Scenario: Line with a new pipe
- **WHEN** an iteration changes the supply pipe of a line from an inner diameter of 37.2 mm to 28.5 mm
- **THEN** the line has `d` 37.2 and `d_new` 28.5 in the pair's results of the iteration file

#### Scenario: Reference run
- **WHEN** a reference run (iteration 0) is saved
- **THEN** every line has `d_new` equal to `d`

### Requirement: Diameter layer per iteration and pair
"Show selected iterations on the map" SHALL create per iteration and pair a line layer "Lines – inner diameter after sizing [mm]" ("Lines – inner diameter [mm]" for a reference run) categorized by `d_new`: one category per distinct inner diameter that occurs as `d` or `d_new` in the same pair in any saved iteration, labelled `d_i = <d> mm`, plus a grey category "no diameter" for lines without a diameter. The colors SHALL follow the Turbo ramp from the smallest to the largest of these diameters, computed by the same function as the pipe diameter style of the lines layer.

#### Scenario: Same color in every iteration
- **WHEN** a diameter of 28.5 mm occurs in iterations 1 and 3 of the pair 1/2 and both iterations are shown
- **THEN** the lines with `d_new` 28.5 mm have the same color in both iterations and both legends list the same categories

#### Scenario: Earlier iteration file
- **WHEN** an iteration file without `d` and `d_new` is shown
- **THEN** its diameter layer shows all lines in the category "no diameter"

### Requirement: Order and visibility of the line layers
In the subgroup of a pair the layers SHALL be ordered top to bottom: customers, diameter layer, "Lines – new pipes" (not in a reference run), "Lines – design mass flow [kg/s]". The diameter layer SHALL be switched on and the design mass flow layer switched off in the layer tree.

#### Scenario: Iteration shown on the map
- **WHEN** the user shows an iteration on the map
- **THEN** each pair's subgroup has the diameter layer checked above the layer of the new pipes, and the design mass flow layer unchecked at the bottom
