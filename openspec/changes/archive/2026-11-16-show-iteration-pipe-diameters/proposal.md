## Why

"Show selected iterations on the map" of the dynamic pipe sizing shows per pair the customers (dp at the
substation), the design mass flow of the lines and the lines with new pipes, labelled with the pipe names. The
result of the sizing, the inner diameter of every line, is not on the map: the user has to read pipe names or
style the lines layer of the version, which shows only the current state and not an iteration.

## What Changes

- The iteration file stores per pair and line the inner diameter of the supply pipe before and after the sizing
  (`d`, `d_new` [mm]) next to the pipe names.
- Per iteration and pair a new layer "Lines – inner diameter after sizing [mm]" (iteration 0 of a reference run:
  "Lines – inner diameter [mm]") with one category per diameter on the Turbo ramp. The categories of a pair are
  the same in all iterations, so a color means the same diameter in every iteration. The color of a diameter is
  computed by the same helper as in the pipe diameter style of the lines layer (`stylePipeDiameter`).
- The diameter layer is on top of the line layers and switched on; the design mass flow layer stays in the group
  but is switched off.
- Iteration files of earlier runs (without diameters) are shown with the category "no diameter".

## Capabilities

### New Capabilities
- `iteration-pipe-diameters`: the inner diameters per line in the iteration file and their layer per iteration and
  pair (categories, colors, layer order and visibility).

### Modified Capabilities
<!-- none: the iteration files and layers per pair (sizing-iteration-results) are in the change balance-pipe-pairs,
     which is not archived yet; the diameter layer is specified here as an addition -->

## Impact

- `districts/utility_functions/dynamic_sizing_results.py`: `pairSummary` (d, d_new), `showPair` (diameter layer,
  order, visibility of the mass flow layer), module doc.
- `districts/utility_functions/layer_visualization.py`: the color of a diameter as a helper shared by
  `stylePipeDiameter` and the iteration layer.
- Translations (layer names, "no diameter"), info text `dynamic_pipe_sizing_info`; tests in `districts/test`.
- No DB schema change; builds on the changes balance-pipe-pairs and sizing-simulation-period.
