## 0. Prerequisites

- [x] 0.1 Change `climate-macro-build` applied (generated climate macro with `IGlob`)
- [ ] 0.2 GroundMo: `final parameter Integer contractVersion = 2` in `GroundCollector`, rebuilt, installed, the GroundMo simulation tests pass (design R5)

## 1. Data model and upgrade

- [x] 1.1 `DB_projectTablesDefault.txt`: `public.ground_collectors` (design R1) and `line_types.ground_collector_id` (FK, ON DELETE RESTRICT)
- [x] 1.2 `ground_collectors.ensureGroundCollectorTables`, called from `upgrade.upgradeProjectDB` (the module holds the SQL; `DB_projectTablesDefault.txt` has the same text)
- [x] 1.3 `DB_versionTablesDefault.txt` and `upgrade.upgradeVersionDB`: `lines.n_loops` (integer) and `lines.t_mean_init` (real)
- [x] 1.4 `layersConfig` templates and `addMissingFormFields`: `n_loops`, `t_mean_init` in the lines form

## 2. Resource module

- [x] 2.1 `utility_functions/ground_collectors.py`: read and save resources, keep `line_types` in sync (create, rename, delete unused, refuse used), `isCollectorLine`, `collectorLines(version)` with the defaults applied (R2, R3)
- [x] 2.2 `fitFor`: geometry, soil (Kusuda wave from the project) and surface from a resource, fingerprint, cached fit or `fitRc`, store, drop stale entries (R6)
- [x] 2.3 `startValues`: undisturbed or pre-calculated per line, cached per fingerprint, mean temperature, years, start day and climate file (R7)
- [x] 2.4 `lineTerminals(lid)`: model name, connector and index per pipe sequence of a line (R4)
- [x] 2.5 GroundMo check: `GroundMo.eo` present, `contractVersion` equal to `CONTRACT_VERSION` (R5)

## 3. Resources tab, export and import

- [x] 3.1 Button "Ground collectors" in the resources tab, table dialog with preset and loop-pipe dropdowns (R11)
- [x] 3.2 "Fit" action in a worker thread with errors, steady error and acceptance shown
- [x] 3.3 Export and import of the resources by name with their fits and loop pipe; line types recreated; table widgets in both resource dialogs

## 4. Topology

- [x] 4.1 `GenerateNetworkTopology`: `n_loops`, `t_mean_init` in `network_help`, the line split, `insertLinesFromTopology` and the attribute copy back
- [x] 4.2 `mergeLines`: a collector only with a line of equal type, bundle, loops and mean temperature (ordinary lines merge as before)

## 5. Model build

- [x] 5.1 `insertLines`: collector lines as `Collector_<lid>`, `CollectorSurface_<lid>` and `Pipebundle_<lid>` with the other pipes (R4)
- [x] 5.2 Junction, plug-junction and customer/plant connections through `lineTerminals`
- [x] 5.3 Start values as `TStart*` parameters and `:V` of the node and surface temperatures (R7)
- [x] 5.4 Checks before the build (GroundMo, `IGlob`, accepted fits) with `tr_msg` messages; the same rules in `model_checks` (R5)
- [x] 5.5 Output requests `Line_coll_<lid>` with `:L` logging; adder "qcollectors" in `outputs.py`, collectors out of the `QAmbtotal` sum (R10)

## 6. Sizing, cost optimization, economics

- [x] 6.1 `hydraulic_balancing.getLineData`, `pipe_sizing` line SQL and `set_pipes.applyPipes` skip collector lines (R8)
- [x] 6.2 `cost_model_data.buildModel`: collector lines protected, item "collector" in `CostModel.investmentItems` (R8, R9)
- [x] 6.3 `network_economics.investments`: collector item, other pipes without trench, maintenance and lifetime from the resource; collectors out of the loss items and `pipe_losses.checkLines` (R9)

## 7. Results and report

- [x] 7.1 `load_results`: `line_s_coll_<var>` with the sections as segments (R10)
- [x] 7.2 `show_on_map`: collector results on the map
- [x] 7.3 Network report and `version_kpis`: trench and loop meters, kWh/(m a), lowest outlet temperature, largest ice fraction
- [x] 7.4 Action "mean temperature from results" for selected collector lines; model check warning above 2 K difference (R7)

## 8. Tests

- [x] 8.1 `test/test_ground_collectors.py` (no DB): fit cache and fingerprint, start values and cache, `lineTerminals` for a four-pipe bundle with loop sequence 2, collector costs (17024 EUR case), GroundMo check against a sample `.eo`
- [ ] 8.2 e2e: upgrade of an old project, line type sync (create, rename, refuse used, delete unused), defaults per line, topology regeneration keeping and not merging a collector, export/import round trip
- [ ] 8.3 e2e: model build of a collector line (models, connections, start values, outputs) and an unchanged build without collectors; sizing and cost optimization leave the collector
- [ ] 8.4 ida: simulate a small network with one collector line; results loaded per section, report key figures, energy balance of the extracted heat

## 9. Translations, documentation, validation

- [x] 9.1 German translations (`tr_msg`, UI texts) of the resources tab, the Fit dialog, the checks and the report; de compiled
- [x] 9.2 README.md and CLAUDE.md: collector resources, routes, build, costs, results; GroundMo requirement
- [ ] 9.3 Local validation: from `districts/` the QGIS Python runs `-m pytest` (with `-m "not ida"` without IDA Districts) and it passes, including `test_static_mypy.py` and `test_messages.py`
- [ ] 9.4 `npx openspec validate --all`; commit the change's artifacts with the code, push to dev and watch the plugin-tests run until both QGIS jobs pass
