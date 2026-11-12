## 1. Savable run result in the dialogs

- [x] 1.1 Add `runResultSavable(dlg, message)` in `districts/ida_pp_dialog.py`: True if `dlg.run_result == 'finished'`, otherwise a `MessageWarning` in the message bar and False (D3)
- [x] 1.2 `PipeLayingDialog`: `run_result = None` in `__init__` and when `execute` starts a worker; `update_finished` stores the worker's message (D1)
- [x] 1.3 `PipeLayingDialog.rejectResults` sets `run_result = None`; `saveResults` returns at once if `runResultSavable` is False, before connecting to the DB (D2, D3)
- [x] 1.4 `NetworkTopologyDialog`: the same as 1.2 and 1.3 with its own message (D1-D3)

## 2. Messages

- [x] 2.1 Both messages through `tr_msg`, German translations in `districts/i18n/districts_de.ts` in the wording of the dialogs' existing translations (D4)
- [x] 2.2 Compile the translations de/en (`districts_de.qm`, `districts_en.qm`)

## 3. Incremental test steps

- [x] 3.1 `districts/test/conftest.py`: `pytest_runtest_makereport` records a setup-phase skip of an incremental step with its reason; failures stay as they are (D5)
- [x] 3.2 `pytest_runtest_setup` skips with "previous step skipped (<step>: <reason>)" for a recorded skip and "previous step failed (<step>)" for a failure; a short comment states that a fixture skips only for a missing prerequisite
- [x] 3.3 Marker `templates` (registered in `pytest.ini`): `pytest_runtest_setup` skips a step whose workflow template (`item.callspec.params['wf']`) is not listed, before its fixtures, without recording it; the three import steps use it instead of `only_for` (D6)

## 4. Tests

- [x] 4.1 e2e test (pipe laying dialog): Save before any run, after a refused start without streets (no `temp.lines`), after a run ending with `error` and after Reject leaves the version unchanged and shows the warning, no critical message
- [x] 4.2 e2e test (network topology dialog): Save before any run and after Reject leave the version unchanged and show the warning
- [x] 4.3 e2e test: a finished run followed by a failed run is not savable (stored result reset by `execute`)
- [x] 4.4 Test of the incremental hooks (pytester or a small test class): a fixture skip skips the later steps with its reason, an `only_for`-style skip in the call phase does not, a failure skips with "previous step failed"
- [x] 4.5 Run the `db_defaults` workflow without sample data (`DISTRICTS_TEST_SAMPLES` pointing to a missing folder): the steps after the imports are skipped with the reason, no failure

## 5. Local validation

- [x] 5.1 From `districts/` (through the profile junction), the QGIS 4.2.3 Python runs `-m pytest -m "not ida"` and it passes, including `test_static_mypy.py` and `test_messages.py`
- [x] 5.2 With IDA Districts installed, the full `-m pytest` run passes

## 6. Documentation

- [x] 6.1 Check README.md, CLAUDE.md and `.github/RUNNER_SETUP.md`: no command, file path or runner need changes; update them only if the implementation adds one

## 7. CI validation

- [x] 7.1 Commit (explicit paths, with the change's artifacts), `git pull --rebase`, push to `dev`
- [ ] 7.2 Watch the plugin-tests run (`gh run watch` or the Actions tab) until both QGIS jobs pass
