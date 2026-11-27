## 1. Database and upgrade

- [x] 1.1 Add the columns of D12 to `statics_sections`, `statics_points`, `statics_model_sections` and `statics_model_nodes` in `STATICS_TABLES_SQL` and `DB_versionTablesDefault.txt`; extend `SECTION_OVERRIDE_COLUMNS`, the point override columns and `FINGERPRINT_INPUTS`
- [x] 1.2 Add the four result tables of D10 to `STATICS_TABLES_SQL` and `DB_versionTablesDefault.txt`
- [x] 1.3 `upgradeVersionDB`: add the new columns to existing versions with `db.addMissingColumns` (one ALTER TABLE per table) and create the result tables
- [x] 1.4 `statics_parameters`: column `source`, the keys and sources of the design's parameter table; `ensureStaticsParameters` adds missing keys and the column without overwriting values; `DB_projectTablesDefault.txt` updated
- [x] 1.5 The parameter dialog shows the column `source` (read-only)
- [x] 1.6 Templates `heating_network` and `db_default_values`: σ_ax max 190 N/mm² on "Isoplus DRE Standard" and "Isoplus DRD Standard"
- [x] 1.7 The model build stores the new override values in the model rows

## 2. Catalogue and loads

- [x] 2.1 `statics_catalog.py`: isoplus one-time compensator table (PHB 7/2), pad curve (PHB 7/9), minimum cover table (PHB 9/11), each with its source
- [x] 2.2 `statics_checks.py`: design and simulated loads per pipe and carrier with their source (D2), including the `_period<k>` tables
- [x] 2.3 `statics_solve_db.py`: read the current model, the parameters, the materials and the simulated maxima; refuse a model that is not current

## 3. FE solver

- [x] 3.1 `statics_fe.py`: 3D beam element, curved bend element with flexibility factor, kink corner, rigid offset link, assembly on scipy.sparse
- [x] 3.2 Twin cross-section with two carriers and the thermal bending load (D4); stress per carrier after solving
- [x] 3.3 Soil springs: axial friction, lateral passive limit, vertical up and down, groundwater (D5)
- [x] 3.4 Fixed points, compensators, end caps, valves, tees, reducers; junctions joined by sequence; free end at a skipped pipe
- [x] 3.5 Load steps with increments, Newton iteration with sticking and sliding by return mapping, both friction cases (D7)
- [x] 3.6 Laying methods: stress-free temperature per section, one-time compensators, prestressed legs with VTf, self-prestressing refused (D6)
- [x] 3.7 Solve each connected part on its own; non-convergence as a finding

## 4. Pads and checks

- [x] 4.1 Pad placement loop with the pad curve and the maximum thickness finding (D8)
- [x] 4.2 Checks of D9 with verdict only for limits with a value and a source, utilisation against Re otherwise
- [x] 4.3 Laying and one-time compensator findings (D6)

## 5. Results, run and report

- [x] 5.1 Write the result tables in one transaction; result state missing, current or out of date (D10)
- [x] 5.2 `statics_task.py`: QgsTask on its own DB connection with progress and cancel; cancelled or failed runs keep the old results (D11)
- [x] 5.3 Button "Calculate statics" in the modeling group after "Build statics model" (`districts_dialog_base.ui`, `districts_dialog.py`, `districts.py`)
- [x] 5.4 Report dialog with parameters and sources, counts, skipped lines, parts not converged, findings, pads and "fatigue not checked"

## 6. Tests

- [x] 6.1 `test_statics_fe.py` (no DB): hand formulas for the straight run, L, Z and U legs, kink and tee; equilibrium, symmetry, convergence with finer elements
- [x] 6.2 `test_statics_fe.py`: Lmax of PHB 12/4 for DN 20–500 at three covers within ±2 %, and the 85 °C / 95 °C cold laying cases of PHB 12/2
- [x] 6.3 `test_statics_fe.py`: trend of the twin Lmax of PHB 12/5 with the spread 20–60 K, and the bending of a twin with a temperature difference
- [x] 6.4 `test_statics_checks.py` (no DB): loads and their sources, maximum cover by PUR shear against PHB 9/12 within ±5 %, pads, one-time compensator travel, VTf, limits without source
- [ ] 6.5 `test_statics_solve.py` (e2e): upgrade of an old version and project, run on the template network, results and result state, refusal of an out-of-date model, cancel keeps the old results, skipped flexible line, child version
- [x] 6.6 `test_statics_model.py`: the SQL in `statics_db` still equals `DB_versionTablesDefault.txt` and the new override columns reach the model rows

## 7. Translations and documentation

- [x] 7.1 German translations of every new `tr_msg` text, the button, its tooltip and the report; de/en compiled
- [x] 7.2 README.md and CLAUDE.md: the statics solver, its files and the parameters with their sources

## 8. Validation

- [x] 8.1 Local: from `districts/` the QGIS Python runs `-m pytest -m "not ida"` and it passes, including `test_static_mypy.py` and `test_messages.py`
- [ ] 8.2 CI: commit, push to dev and watch the plugin-tests run (`gh run watch`) until both QGIS jobs pass
- [ ] 8.3 Open: limits and soil stiffnesses from EN 13941-1 / FW 401 Part 10 once the texts are at hand (`friction_min`, `axial_slip_m`, `lateral_slip_m`, `stress_range_allow_n7mm2`, `hoop_stress_allow_n7mm2`, `buckling_safety`)
- [ ] 8.4 Open: comparison with a network calculated in sisKMR or ROHR2 once one is available
- [ ] 8.5 Open: friction of twin pipes from FW 401 Part 10 (the level of PHB 12/5 is not reproduced, see D13)
