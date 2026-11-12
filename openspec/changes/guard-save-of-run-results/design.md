## Context

The pipe laying dialog (`PipeLayingDialog`) and the network topology dialog (`NetworkTopologyDialog`), both in `districts/ida_pp_dialog.py`, start a worker that writes its result into the `temp` schema of the project DB. The user then accepts the result with "Save" (`saveResults`) or rejects it.

`saveResults` truncates the version's lines, customers, junctions, energy plants and connections. It then copies the `temp` tables in: directly in `PipeLayingDialog`, and through `saveTempTables` (`utility_functions/topology.py`) in `NetworkTopologyDialog`. It never checks whether the dialog has a result:

- If no run started (for example, `execute` stopped at "Please insert streets"), the copy fails with `UndefinedTable` when `temp.lines` doesn't exist. If it does exist, the copy silently writes old content.
- The `temp` tables stay in the project DB between runs and are shared by both dialogs. So a stopped or failed run, an earlier session, or the other dialog can leave content that Save then writes into the version.

The workers already report how a run ended. They emit `finished` with `'finished'`, `'stopped'` or `'error'` (`PipeLayingAlgorithm.py`, `GenerateNetworkTopology.py`). The dialogs' `update_finished` receives this, but only resets `process_running`.

The workflow tests (`test/test_workflow.py`, class marked `@pytest.mark.incremental`) chain their steps through `pytest_runtest_makereport` / `pytest_runtest_setup` in `test/conftest.py`. A failed step skips the later steps. A skipped step doesn't: `only_for` skips are expected and must not stop the workflow. The same applies, though, to a skip raised by a missing prerequisite in a fixture (`samples_dir` → "sample data not found"). So pipe laying ran without streets.

The change must run on QGIS 3.44 (Qt5) and QGIS 4.2 (Qt6). It uses no Qt API that differs between them. The message level comes from `utility_functions/compat.py` (`MessageWarning`), which already maps both versions. There's no change to the project DB schema, so `upgrade.py` isn't involved.

## Goals / Non-Goals

**Goals:**
- Save in both dialogs writes only the result of that dialog's own last run, and only if that run ended with `'finished'`.
- Otherwise Save changes nothing in the version and tells the user why.
- In the workflow tests, a missing prerequisite skips the later steps of the workflow with a reason that names the cause.

**Non-Goals:**
- The pipe sizing dialog: its Save only writes pipe bundles back from its own run, and it isn't part of this change.
- Cleaning or versioning the `temp` schema, or detecting stale `temp` tables in the DB.
- Disabling the Save button (decided against: a message tells the user why Save does nothing; a greyed-out button doesn't).
- Changes to `only_for` skips or to how a failed step is reported.

## Decisions

**D1: The dialog stores the result of its last run in memory.**
`update_finished(message)` stores the worker's message in an attribute, e.g. `self.run_result`. `execute` sets it to `None` when it starts a worker, and so does `__init__`. Save is allowed only when it's `'finished'`.
- Alternatives: checking that `temp.lines` exists (fixes the crash, but still saves stale or foreign results); a marker in the DB (survives a QGIS restart, but a result from an earlier session is exactly what shouldn't be saved without a look, and the schema would need a change).
- A pipe laying run that the user stops after pipes were laid ends with `'finished'` (the worker finishes the topology with the laid pipes). It stays savable, as now. A run stopped before any pipe ends with `'stopped'` and isn't savable.

**D2: Reject and closing the dialog clear the stored result.**
`rejectResults` (also called by `closeEvent`) sets the result to `None`. After a rejected result, Save shows the message instead of writing what the user just rejected.
- Alternative: keep the result until the next run. But "reject, then save by mistake" would then write the rejected result.

**D3: One shared check in `ida_pp_dialog.py`.**
A small module-level function, e.g. `runResultSavable(dlg, message)`, returns `True` if `dlg.run_result == 'finished'`. Otherwise it pushes `message` to the message bar with `MessageWarning` and returns `False`. Each `saveResults` calls it first and returns at once on `False`, before connecting to the DB.
- It's a function in the existing module, not a mixin or a new module, because two dialogs in the same file don't justify more structure.
- Level `MessageWarning`, not `MessageCritical`: nothing failed, the user only has to run first. This also keeps the test `ErrorCollector`, which fails a test on critical messages, out of the expected case.

**D4: Two messages, one per dialog, through `tr_msg` with a German translation.**
- "No pipe laying result to save. Run the pipe laying first." / "Kein Ergebnis der Leitungsverlegung zum Speichern. Bitte zuerst die Leitungsverlegung ausführen."
- "No network topology result to save. Generate the network topology first." / "Kein Ergebnis der Netztopologie zum Speichern. Bitte zuerst die Netztopologie erzeugen."
- The final German wording follows the existing translations of the two dialogs in `i18n`.

**D5: A skip during fixture setup counts as a missing prerequisite of the incremental workflow.**
In `pytest_runtest_makereport`, a report of phase `setup` whose exception is a skip is recorded for the workflow, like a failure, together with its reason. `pytest_runtest_setup` then skips the later steps with "previous step skipped (test_import_streets: sample data not found: …)". Failures keep "previous step failed (…)".
- `only_for` skips run in the `call` phase and stay unrecorded, so the later steps still run.
- The skip raised by `pytest_runtest_setup` itself ("previous step …") is also a setup-phase skip. Recording it again is harmless, because the first entry per workflow is kept (`setdefault`).
- Alternatives: skipping the whole workflow when samples are missing (loses the early steps such as project creation), or a per-test check for streets (hides the cause, repeats for every step).

**D6: Steps with a prerequisite fixture declare their templates with a marker checked before the fixtures.**
The fixtures of a step are set up before its body calls `only_for`. So without sample data, `test_import_streets[heating]` would be skipped by `osm_offline` during setup, and D5 would stop the `heating` workflow although the imports don't apply to it. The import steps (`test_import_streets`, `test_import_buildings`, `test_import_elevation_data`) therefore carry `@pytest.mark.templates(EMPTY, DB_DEFAULTS)`. `pytest_runtest_setup` reads the template of the workflow from `item.callspec.params['wf']` and skips with "not part of the template '…'" before any fixture runs. That skip isn't recorded. `only_for` stays in all other steps.
- Alternatives: the marker for all steps instead of `only_for` (one consistent way, but a large diff with no change in behaviour); fetching the prerequisite fixtures inside the test after `only_for` with a dedicated skip type (changes D5's mechanism and makes the steps harder to read).

## Risks / Trade-offs

- [A savable result is lost when the dialog object is recreated, e.g. the user closes and reopens the dialog after a run] → Intended: closing already calls `rejectResults` and removes the temp layers, so the user can't see that result any more.
- [The plugin keeps a dialog open across a version switch, and Save would then write a run from the old version into the new one] → Not a new risk: the dialogs read `config['versionName']` at Save today. This change doesn't widen it, and it stays out of scope.
- [Another setup-phase skip, for example a future fixture that skips for an optional feature, would now stop the rest of the workflow] → Intended for prerequisites. A fixture for something optional should skip inside the test instead. A comment at the hook states this rule.
- [Tests that call `saveResults` directly without a run] → Only `test_pipe_laying_algorithm` and `test_generate_network_topology` call it, both after a run that ends with `'finished'`. They keep passing. New tests cover Save without a run, after a failed or stopped run, and after Reject.
