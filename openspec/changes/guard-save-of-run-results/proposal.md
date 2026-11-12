## Why

"Save" in the pipe laying and network topology dialogs copies the `temp` schema into the version without checking whether a run of that dialog produced it. Without a run, it fails with a database error (`relation "temp.lines" does not exist`). Worse, if earlier or failed runs, or the other dialog, left `temp` tables behind, it silently overwrites the version's lines, customers and junctions with them. A test run without sample data hit the error. The workflow tests also hid the cause: they ran pipe laying after the import steps had been skipped.

## What Changes

- The pipe laying dialog and the network topology dialog remember the result of their own last run (finished, stopped, error, or no run yet).
- "Save" writes the `temp` tables into the version only if the dialog's last run finished successfully. Otherwise it writes nothing and tells the user to run the pipe laying or the network topology first.
- A new run clears the stored result, so a failed run can't save the results of an earlier one.
- Workflow tests (`@pytest.mark.incremental`): a step skipped while its fixtures are set up (a missing prerequisite, e.g. "sample data not found") skips the later steps of that workflow, with the step and the reason. Skips of steps that don't apply to a template (`only_for`) keep the later steps running, as now.

## Capabilities

### New Capabilities
- `run-result-saving`: when the pipe laying and network topology dialogs may write their run results into the project version, and what the user sees otherwise.
- `workflow-test-steps`: how the steps of an e2e workflow test depend on each other when a step fails or misses a prerequisite.

### Modified Capabilities

(none, `openspec/specs/` has no specs yet)

## Impact

- `districts/ida_pp_dialog.py`: `PipeLayingDialog` and `NetworkTopologyDialog` (`execute`, `update_finished`, `saveResults`), plus a small shared helper.
- `districts/utility_functions/translations.py` / `i18n`: two new user messages with German translations.
- `districts/test/conftest.py`: hooks of the incremental steps.
- `districts/test/`: new e2e tests for Save without a successful run, for both dialogs.
- No change to the project DB schema, the `temp` tables or a successful run followed by Save.
