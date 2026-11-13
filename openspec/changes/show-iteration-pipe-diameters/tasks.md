## 1. Iteration file

- [x] 1.1 `pairSummary`: `d` and `d_new` per line (supply pipe, mm rounded to 0.1, from the run's catalog; reference run d_new = d); module doc of dynamic_sizing_results.py

## 2. Colors

- [x] 2.1 `diameterColors(diameters, ramp_name, invert)` and `diameterLabel(d_mm)` in layer_visualization.py; `stylePipeDiameter` uses them (unchanged result)

## 3. Layer

- [x] 3.1 `showPair`: layer "Lines – inner diameter after sizing [mm]" (reference: "Lines – inner diameter [mm]") with fields d, d_new, categorized on d_new over the diameters of the pair in all iterations, grey "no diameter", width 1.2 mm
- [x] 3.2 Order customers, diameters, new pipes, mass flow; mass flow layer switched off in the layer tree

## 4. Tests

- [x] 4.1 Unit tests: d/d_new in pairSummary (sizing and reference), diameterColors (order, single diameter, same as stylePipeDiameter), categories of a pair over several iterations, old file → "no diameter"
- [x] 4.2 Layer test (pytest-qgis, memory layers): names, order and visibility in the subgroup of a pair, reference run without new pipes layer
- [x] 4.3 test_dynamic_optimization.py: the diameter layer of every shown iteration and pair, d_new of the changed lines differs from d

## 5. Translations and documentation

- [x] 5.1 tr_msg with German translation for the layer names and "no diameter"; info text `dynamic_pipe_sizing_info` (en/de): diameter layer, mass flow layer switched off; translations de/en compiled
- [x] 5.2 README.md and CLAUDE.md updated if a command or file path changed

## 6. Validation

- [x] 6.1 From the plugin folder of the QGIS profile, the QGIS Python runs `-m pytest -m "not ida"` and it passes, including test_static_mypy.py and test_messages.py; test_dynamic_optimization.py passes with IDA Districts
- [x] 6.2 `npx openspec validate --all` passes
- [ ] 6.3 Commit code and artifacts, `git pull --rebase`, push to dev and watch the plugin-tests run (`gh run watch`) until both QGIS jobs pass
