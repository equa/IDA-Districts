## 1. Start and opening

- [x] 1.1 `Util_api`: note the broker log's size before the start, no sleep; `wait_for_registration()` (0.2 s polling, whole-line match `Registering...: <pid>`, process ended → `IdaOpenError`, 60 s or no log → info message)
- [x] 1.2 `Util_api.open_document(path)`: connect + `openDocument`, retry after "Timeout..." up to 180 s since the start, other text → `IdaOpenError` at once, info message per retry

## 2. Workers

- [x] 2.1 `WorkerSimulateFilesAPI`, `WorkerSimulateAPI`, `WorkerOpenAPI`, `WorkerOpenRunScriptAPI`: use `open_document`, drop their own `connect_to_ida`; on `IdaOpenError` the message "IDA Districts could not open {}: {}", status "Simulation failed" where a status is set, IDA closed in `finally`

## 3. Setting removed

- [x] 3.1 Remove `IDA_API_delay` / `lineEdit_districts_api_delay` from districts_settings_dialog.ui, districts_dialog.py, districts.py, utility.py; `run_simulation.py` without the argument `api delay`

## 4. Tests

- [x] 4.1 Unit tests with a fake `ida_lib`, a temporary broker log and a fake process state: registration found (one open), longer pid not matched, process ended, no log, timeout then handle, error text without retry, maximum wait
- [x] 4.2 Worker test with the fake: failed opening → error text with path, status "Simulation failed", IDA closed
- [x] 4.3 Settings: the dialog has no API delay field, the config has no `districts_api_delay`

## 5. Translations and documentation

- [x] 5.1 tr_msg with German translation for the new messages; `IDA_API_delay` entries removed from districts_de.ts / districts_en.ts; translations de/en compiled
- [x] 5.2 README.md, CLAUDE.md and .github/RUNNER_SETUP.md updated if a command, file path or runner need changed (run_simulation.py arguments)

## 6. Validation

- [x] 6.1 From the plugin folder of the QGIS profile, the QGIS Python runs `-m pytest` with IDA Districts and it passes, including test_static_mypy.py, test_messages.py and the `ida` tests
- [x] 6.2 `npx openspec validate --all` passes
- [ ] 6.3 Commit code and artifacts, `git pull --rebase`, push to dev and watch the plugin-tests run (`gh run watch`) until both QGIS jobs pass; this run also closes task 6.3 of show-iteration-pipe-diameters
