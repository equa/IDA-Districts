## ADDED Requirements

### Requirement: Wait for the IDA session to register
After starting IDA Districts for an API session, the plugin SHALL wait until the IDA message broker log (`%ProgramData%\equa\ida_message_broker_log.txt`) has a new line `Registering...: <pid>` for the started process, read from the end the log had before the start, and only then send the first API call. It SHALL NOT wait a fixed time. If the IDA process ends before the line appears, the start SHALL fail at once with a message that IDA Districts ended during the start. If the log does not exist, cannot be read, or the line does not appear within 60 s, the plugin SHALL send the first call anyway and write an info message to the Districts message log.

#### Scenario: Normal start
- **WHEN** IDA Districts is started and the broker log gets the line `Registering...: 7180` for its pid 7180 after 8 s
- **THEN** the plugin sends `openDocument` right after that line, not before

#### Scenario: Another process with a longer pid
- **WHEN** the broker log gets the line `Registering...: 71801` while the started process has the pid 7180
- **THEN** the plugin keeps waiting

#### Scenario: No broker log
- **WHEN** the broker log does not exist
- **THEN** the plugin sends the first call without waiting and writes an info message, and the retry of the opening applies

### Requirement: Open the model with retry
The first `openDocument` of an API session SHALL be retried, each time after a new `connect_to_ida`, as long as it answers with a timeout and less than 180 s have passed since the IDA start. It SHALL return the document handle when one comes. Any answer other than a handle or a timeout SHALL fail at once. Each retry SHALL write an info message (not critical) to the Districts message log.

#### Scenario: Slow start
- **WHEN** the first `openDocument` answers "Timeout..." and the second returns the handle 1
- **THEN** the model is opened with the handle 1 and one info message notes the retry

#### Scenario: IDA never answers
- **WHEN** every `openDocument` answers "Timeout..." until 180 s after the IDA start
- **THEN** the opening fails with the model's path and the text "Timeout..."

#### Scenario: Model cannot be opened
- **WHEN** `openDocument` answers with an error text other than a timeout
- **THEN** the opening fails at once, without a retry, with the model's path and that text

### Requirement: Error reported by the API workers
The API workers (simulate one model, simulate several models, open a model, open a model and run a script) SHALL open their first model through this waiting and retry. When the opening fails they SHALL report "IDA Districts could not open <path>: <IDA's text>", set the status "Simulation failed" where they report a simulation status, and close the IDA session.

#### Scenario: Simulation of a model that cannot be opened
- **WHEN** a simulation is started and the opening fails with a timeout
- **THEN** the error names the model and "Timeout...", the status is "Simulation failed", and the IDA process is closed

### Requirement: No API delay setting
The settings dialog SHALL NOT offer an API delay (`IDA_API_delay`), and the plugin SHALL NOT read `districts_api_delay` from the settings. A value saved by an earlier version SHALL be ignored.

#### Scenario: Settings saved by an earlier version
- **WHEN** the QGIS settings hold `districts_api_delay` = 30 from an earlier version
- **THEN** the plugin does not wait 30 s before the first call; it waits for the registration as above
