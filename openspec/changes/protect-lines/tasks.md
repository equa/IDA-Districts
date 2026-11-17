## 1. Sizing and balancing

- [x] 1.1 `optimizePipeDiameters(protected=...)`: protected lines left out of both `presizePipes` calls and skipped in the reduction like `lids_weak`; result keys `protected` and `protected_over_max`
- [x] 1.2 `evaluatePair`: pass the run's protected set; log per pair the number of protected lines and the IDs above `dp_spez_max`

## 2. Dialog

- [x] 2.1 `list_protectedLines` with "+", "−" and "Add selected lines" in `formLayout_balancing` (editable items via `qt_item_flag`, selection of the active or the project's `lines` layer, no duplicates, info without selection)
- [x] 2.2 Read `dynamic_sizing_protected_lines.json` of the loaded version in `fillCombos` (missing/unreadable → empty, error in the QGIS log)
- [x] 2.3 Start: entries that are not positive integers stop with a message naming them; IDs not in the selected network logged and dropped from the run; valid IDs saved to the file before a child version is created; `protected` in `parameters()`

## 3. Iteration results

- [x] 3.1 `pairSummary`: `n_protected` per pair and `protected` per line; older files read as 0 / false

## 4. Tests

- [x] 4.1 Unit tests (test_protected_lines.py): optimizer keeps protected lines with balancing, pre-sizing and dp_spez_max; `protected_over_max`; dp of the customers includes the protected lines; entry check; JSON save/load; pairSummary keys and earlier files
- [x] 4.2 Dialog test: "+", "−", add selected lines from a lines layer without duplicates, list filled from the version file
- [x] 4.3 test_dynamic_pipe_sizing.py (e2e/ida): one protected line keeps its pipe bundle over the run

## 5. Translations and documentation

- [x] 5.1 tr_msg with German translation for the new labels and messages, info text `dynamic_pipe_sizing_info` (en/de) mentions the protected lines; translations de/en compiled
- [x] 5.2 README.md and CLAUDE.md: the new file `dynamic_sizing_protected_lines.json` in the version folder if the docs list version files; otherwise note that no change is needed (they list no version files: no change)

## 6. Validation

- [x] 6.1 Local: from districts/, the QGIS Python runs `-m pytest` (with `-m "not ida"` without IDA Districts) and it passes, including test_static_mypy.py and test_messages.py (3 test_workflow failures on the pipe columns come from the uncommitted network-cost-data work in the tree, not from this change)
- [ ] 6.2 CI: commit, push to dev, watch the plugin-tests run (`gh run watch`) until both QGIS jobs pass
