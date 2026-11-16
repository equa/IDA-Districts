## Context

`Util_api.__init__` (util.py) starts `ida-districts.exe … -G1 -C <name>`, sleeps `districts_api_delay` (setting
`IDA_API_delay`, default 10 s) and loads `idaapi2.dll`. Each API worker in workers.py then calls
`connect_to_ida(b"5945", pid)` (result ignored), `openDocument(path)` and, for a simulation, `runIDAScript` with
RUN-SIMULATION and save-document. `call_ida_api_function` returns the document handle (int) or a text (error, or
"Timeout..."); the workers pass that text on as a handle, `runIDAScript` raises a ctypes error and the worker
reports "Failed to open the feature: <path>!".

The IDA API help (IDA_SE/IDA_Help/advanced_features/scripts/IDA_API) documents no ready check and no timeout.
Probes on the CI runner's PC (16.11.2026, IDA Districts as installed, a sample customer model, nothing else running):

| Probe | Result |
|---|---|
| `connect_to_ida` right after the start | True after 0.05 s: the connect does not wait for IDA |
| `openDocument` sent at 0 s or 5 s | "Timeout..." after 15 s; every later call too, without a new connect |
| `openDocument` sent at 8, 11, 13 s | handle after 0.5 s |
| after a timeout: new `connect_to_ida`, `openDocument` | handle after < 1 s |
| `getIDAStatus` (not queued) sent at once | blocks 15 s, returns -1, connection broken like above |
| `WaitForInputIdle`, IDA's main window | after 0.1–0.4 s, long before IDA answers |
| `Registering...: <pid>` in `C:\ProgramData\equa\ida_message_broker_log.txt` | after 7.8, 9.1, 7.8 s; `openDocument` right after: handle in < 0.6 s |

So a call sent before IDA is ready costs 15 s (timeout inside `idaapi2.dll`, not configurable), any call can only
test readiness at that price, and the broker's registration line marks readiness exactly. The broker log is small
(28 KB, 945 lines since the service started on 11.11.) and only grows.

QGIS 3.44 (Qt5) and 4.2 (Qt6): no Qt or QGIS API is touched apart from removing a QLineEdit and its label from
the settings dialog (.ui); utility_functions/compat.py is not touched. No DB schema change.

## Goals / Non-Goals

**Goals:**
- A slow IDA start no longer fails a simulation; a normal start is faster than now (8–9 s instead of 10 s).
- No setting to tune.
- A failure says which model and what IDA answered.

**Non-Goals:**
- Running simulations from the command line (`WorkerOpenModelCmd`), which loses the status and the error text.
- Retrying a failed simulation (`runIDAScript` with RUN-SIMULATION) or later API calls.
- Reading the broker's ports from `ida_ports.txt` (the port 5945 stays as now).
- The intermittent "layer missing" errors after `loadVersion` on QGIS 4.2 (a separate item).

## Decisions

**D1 – Wait for the broker registration.** Before starting IDA, `Util_api` notes the size of the broker log
(`%ProgramData%\equa\ida_message_broker_log.txt`). After the start it reads the log from that offset every 0.2 s
(from 0 if the file got shorter) until a line equals `Registering...: <pid>` (whole line, so pid 845 does not
match 8450), the IDA process has ended (fails at once: "IDA Districts ended during the start"), or
`REGISTER_MAX_WAIT = 60` s have passed. If the log does not exist or cannot be read, or the line does not come,
it goes on to D2 without waiting further and writes an info message to the Districts message log.
*Alternatives:* a fixed first wait (10 s in the code) – every start pays it, a slower start pays a 15 s timeout;
no wait – every start pays the 15 s timeout; a dummy call (`getIDAStatus`) – blocks 15 s like any call (probe).

**D2 – Open with retry.** `Util_api.open_document(path)`: repeat `connect_to_ida(b"5945", pid)` and
`openDocument(path)` until the result is an int > 0 (returned), a text other than a timeout (raises
`IdaOpenError(path, text)` at once), or `OPEN_MAX_WAIT = 180` s since the IDA start have passed (raises with the
last text). After a registration found in D1 this is one call; it only retries when D1 found nothing or the start
is slower than the registration suggests. Each retry writes an info message ("IDA Districts not ready after {} s,
retrying") to the Districts message log – info, so the test's ErrorCollector (critical only) does not fail on it.

**D3 – Workers.** `WorkerSimulateFilesAPI`, `WorkerSimulateAPI`, `WorkerOpenAPI` and `WorkerOpenRunScriptAPI` drop
their own `connect_to_ida` and call `open_document`. On `IdaOpenError` they emit
`tr_msg("IDA Districts could not open {}: {}")` with the path and IDA's text, set the status "Simulation failed"
where they set a status now, and still close IDA in `finally`. In `WorkerSimulateFilesAPI` the files after the
first are opened in the running session with a plain `openDocument`, as now.

**D4 – Setting removed (T2).** The label `IDA_API_delay` and `lineEdit_districts_api_delay` go from
`districts_settings_dialog.ui`; `districts_dialog.py`, `districts.py` and `utility.py` stop reading and writing
`districts_api_delay`; `run_simulation.py` drops its optional argument `api delay`. A value saved earlier stays in
the QGIS settings unused. The label's entries in districts_de.ts / districts_en.ts are removed.

## Risks / Trade-offs

- [The broker log line is undocumented and may change in another IDA version] → D2 still opens the model: the
  first call then costs a 15 s timeout and the retry, the start does not fail; the info message in the log shows
  that the registration was not found.
- [The broker log is not on `%ProgramData%\equa` on another installation] → same fallback as above.
- [The timed-out `openDocument` is still queued in IDA and opens the model a second time] → in the probes the
  retry returned handle 1, the same document; the simulation script works on `[@ :SYSTEM]` of the returned handle.
- [A start that never finishes costs up to 180 s instead of failing after about 45 s] → only in that case; the
  error then names the timeout.
- [Unit tests cannot start IDA] → registration wait and `open_document` are tested with a fake `ida_lib`, a
  temporary log file and a fake process state; the existing `ida` tests and CI cover the real start.
