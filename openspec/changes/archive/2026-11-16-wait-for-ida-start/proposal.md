## Why

The plugin starts IDA Districts, waits a fixed `districts_api_delay` (default 10 s, a setting) and then sends its
first API call. A call sent before IDA is ready gets no answer: it times out after 15 s and the connection stays
broken for the whole IDA session, so the simulation fails with "Failed to open the feature". IDA needs 8–9 s to
start on the CI runner's PC when it is idle, little margin to the 10 s; under the load of a test run some starts
take longer, and simulations fail at random (three in the CI run of 16.11.2026, while others in the same job
passed). The plugin ignores the result of the connect and reports neither the real error nor that IDA was not
ready.

## What Changes

- The plugin waits until the new IDA session has registered with the IDA message broker (its line
  `Registering...: <pid>` in the broker log) and then sends the first call, instead of sleeping a fixed time.
- Safety net: if the broker log is missing or the line does not appear, or the first call still times out, the
  first call (`openDocument`) is retried with a new `connect_to_ida` until it returns a document handle or a
  maximum wait has passed.
- **BREAKING** (setting): the setting `IDA_API_delay` (`districts_api_delay`) is removed from the settings dialog
  and the config; a value saved earlier is ignored.
- All four API workers (simulate one file, simulate several files, open a model, open a model and run a script)
  use the same opening and check that they got a document handle.
- A failure names the model and IDA's own text (or that IDA ended during the start), instead of the generic
  "Failed to open the feature".

## Capabilities

### New Capabilities
- `ida-session-start`: opening a model in a newly started IDA Districts session through the API: waiting for the
  broker registration, retrying after a timeout, the maximum wait and the error reported on failure.

### Modified Capabilities
<!-- none -->

## Impact

- `districts/utility_functions/util.py`: `Util_api` waits for the registration instead of sleeping, opening with
  retry.
- `districts/utility_functions/workers.py`: `WorkerSimulateFilesAPI`, `WorkerSimulateAPI`, `WorkerOpenAPI`,
  `WorkerOpenRunScriptAPI` use it; their error messages.
- Setting removed: `districts_settings_dialog.ui`, `districts_dialog.py`, `districts.py`, `utility_functions/utility.py`,
  `simulation_tests/run_simulation.py` (argument `api delay`), translations of the label.
- Translations (new messages); tests in `districts/test`.
- No DB schema change.
