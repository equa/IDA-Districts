## Context

`pairSummary` (dynamic_sizing_results.py) writes per line of a pair `pipe` and `pipe_new`, the names of the supply
pipe before and after the sizing; the inner diameters are in the pipe catalog of the run (`res['catalog'][pipe_id]['d']`
[m]) but not in the file. `showPair` creates per pair, top to bottom: customers, "Lines – new pipes" (red halo,
label pipe → pipe_new; not in a reference run), "Lines – design mass flow [kg/s]" (blue, graduated). The class
bounds of a pair are taken from the same pair in all iterations (`all_pairs`).

`stylePipeDiameter` (layer_visualization.py) styles the lines layer of the version: a categorized renderer with one
category per inner diameter, color `ramp.color(t)` with `t = (d - d_min) / (d_max - d_min)` on the Turbo ramp
(`turboColor` without the ramp), legend `d_i = <d> mm`, grey for lines without a pipe.

QGIS 3.44 (Qt5) and 4.2 (Qt6): `QgsCategorizedSymbolRenderer`, `QgsRendererCategory`, `QgsLayerTreeLayer.
setItemVisibilityChecked` exist in both; no Qt enum beyond those already used (utility_functions/compat.py is not
touched). No DB schema change.

## Goals / Non-Goals

**Goals:**
- See the inner diameter of every line after the sizing of an iteration, per pair, comparable across iterations.
- The same color for the same diameter as in the pipe diameter style of the lines layer, as far as the diameter
  range allows.

**Non-Goals:**
- Diameters of the return pipe or of other sequences of the bundle (the pair sizes supply and return together).
- A difference layer (d_new − d): the layer "Lines – new pipes" already marks the changed lines.
- Reconstructing the diameters of earlier iteration files from the pipe names.

## Decisions

**D1 – Diameters in the iteration file.** `pairSummary` adds per line `d` and `d_new`: the inner diameter of the
supply pipe before and after the sizing in mm, rounded to 0.1 mm (`round(catalog[id]['d'] * 1000, 1)`). In a
reference run `d_new = d`. Files without the keys read as `None`.
*Alternative:* looking up the diameters by pipe name when the layer is shown – a second source that can differ
from the catalog of the run.

**D2 – Shared color helper.** `diameterColors(diameters, ramp_name='Turbo', invert=False)` in
layer_visualization.py returns `{d: QColor}` for the sorted distinct diameters with the `t` of `stylePipeDiameter`
(0.5 for a single diameter); `stylePipeDiameter` uses it for its categories. The legend text `d_i = <d> mm` is a
second helper `diameterLabel(d_mm)` used by both.

**D3 – Diameter layer.** `showPair` creates "Lines – inner diameter after sizing [mm]" (reference run: "Lines –
inner diameter [mm]") with the fields of the mass flow layer plus `d`, `d_new`, and a `QgsCategorizedSymbolRenderer`
on `"d_new"`: one category per distinct diameter of `d` and `d_new` over the same pair in all iterations
(`all_pairs`), colors from `diameterColors`, line width 1.2 mm, plus a grey category "no diameter" for `NULL`.
No labels (the changed lines keep their label in "Lines – new pipes").

**D4 – Order and visibility (T4: b).** Top to bottom in the pair's subgroup: customers, diameter layer,
"Lines – new pipes" (its halo stays visible around the diameter lines), "Lines – design mass flow [kg/s]". The
mass flow layer is switched off in the layer tree (`setItemVisibilityChecked(False)`); all other layers are on.

## Risks / Trade-offs

- [The colors of the iteration layer and of the styled lines layer differ when their diameter ranges differ] →
  the same helper and ramp; identical when the iterations use the same smallest and largest diameter as the
  version; the legend names every diameter.
- [Many distinct diameters give similar neighbouring colors] → as in `stylePipeDiameter`; the legend and the
  identify tool give the value.
- [The mass flow layer is switched off and overlooked] → it stays in the subgroup right below; the info text says so.

## Migration Plan

No data migration. Iteration files without `d`/`d_new` are shown with the category "no diameter". Rollback:
revert the commit; files with the new keys are read by the old code (extra keys are ignored).

## Open Questions

None.
