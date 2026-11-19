## 1. Tables and parameters

- [x] 1.1 Add the six version tables (`statics_model_nodes`, `statics_model_sections`, `statics_model_pipes`, `statics_model_build`, `statics_points`, `statics_sections`) to `DB_versionTablesDefault.txt`
- [x] 1.2 `statics_db.ensureStaticsTables(cur, schema)` with the same SQL (IF NOT EXISTS), called from `upgrade.upgradeVersionDB`
- [x] 1.3 `public.statics_parameters` with the six defaults in `DB_projectTablesDefault.txt` and `statics_db.ensureStaticsParameters(cur)` (adds missing keys, keeps values), called from `upgrade.upgradeProjectDB`

## 2. Geometry rules (pure functions)

- [x] 2.1 `statics_model.py`: 3D vertex angles of a LineStringZ coordinate list
- [x] 2.2 Bend classification per system type with the parameters (none, small-angle kink, prefabricated bend, elastic bend)
- [x] 2.3 Merge of small-kink runs (spacing, total deflection, radius = mean spacing / mean angle, steel limit `elastic_radius_factor` × Da)
- [x] 2.4 Snapping of override points (unique node within tolerance, ambiguous) and sections (section midpoints within tolerance)

## 3. Build

- [x] 3.1 `statics_db.py`: read lines, junctions, bundles, pipes, constructions, layers, series and parameters of the loaded version
- [x] 3.2 Pipe dimensions per pipe (inner, steel outer, wall, casing) from the construction; twin rows for two sequences with one casing construction; cover from `bundle_pipes.y`
- [x] 3.3 Build nodes, sections and pipe rows; apply overrides; write all in one explicit transaction that leaves the old model on failure
- [x] 3.4 Fingerprint in SQL (`md5(string_agg(...))`) over the inputs of D-M2, stored in `statics_model_build` with the report as jsonb; `modelState(cur, schema)` returning missing / current / out of date
- [x] 3.5 Report content: parameters, counts, skipped lines, applied / unmatched / ambiguous overrides, negative covers, runs not merged, bends below `min_bend_radius_m`, pipes without series

## 4. UI and map

- [x] 4.1 `statics_layers.py`: layer group "Statics model" (nodes categorised by bend class, model pipes, editable `statics_points` and `statics_sections`), replaced on rebuild, renderers in code for QGIS 3.44 and 4.2
- [x] 4.2 Buttons "Build statics model" and "Statics parameters" in `districts_dialog_base.ui` / `districts_dialog.py`; handlers in `districts.py` (build, report dialog, layer group; parameter table dialog)
- [x] 4.3 Translations: `tr_msg` texts and UI strings with German translations, `districts_de.ts`/`districts_en.ts` updated and compiled

## 5. Tests

- [x] 5.1 `test/test_statics_model.py` (no DB): angles incl. height, classes, merge (digitised curve, run too tight for steel), snapping (unique, ambiguous, unmatched)
- [x] 5.2 `test/test_statics_build.py` (e2e): old version upgraded, parameters kept, single and twin pipe rows, dimensions, cover and negative cover, skipped line, failed build keeps the old model, overrides after a regenerated topology, model state (line edited, override added, unchanged), child version copies the tables
- [x] 5.3 e2e test of the layer group: four layers, nodes categorised, one group after two builds

## 6. Documentation and validation

- [x] 6.1 README.md and CLAUDE.md: statics model, its tables, parameters and modules
- [x] 6.2 Local validation: from `districts/` the QGIS Python runs `-m pytest -m "not ida"` and it passes, including `test_static_mypy.py` and `test_messages.py` (only while no CI job runs on this PC)
- [x] 6.3 `npx openspec validate --all`; commit the change's artifacts with the code, push to dev and watch the plugin-tests run until both QGIS jobs pass
