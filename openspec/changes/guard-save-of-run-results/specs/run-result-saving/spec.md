## ADDED Requirements

### Requirement: Save writes only a finished run of the same dialog
The pipe laying dialog and the network topology dialog SHALL write the `temp` tables into the project version on "Save" only if that dialog's own last run ended with the result `finished`. A run the user stops after pipes were laid ends with `finished` and SHALL be savable.

#### Scenario: Save after a finished run
- **WHEN** the user runs the pipe laying or the network topology, the run ends with `finished`, and the user clicks "Save"
- **THEN** the version's lines, customers, junctions, energy plants and connections are replaced by the run's result, as before this change

#### Scenario: Pipe laying stopped after pipes were laid
- **WHEN** the user stops a pipe laying run after at least one network's pipes were laid, the run finishes the topology with these pipes, and the user clicks "Save"
- **THEN** the laid pipes are written into the version

### Requirement: Save without a savable result changes nothing
If the dialog has no savable result, "Save" SHALL leave the project version unchanged, SHALL NOT raise a database error, and SHALL show a warning in the message bar telling the user to run the dialog first. The pipe laying dialog shows "No pipe laying result to save. Run the pipe laying first."; the network topology dialog shows "No network topology result to save. Generate the network topology first." Both messages SHALL have a German translation.

#### Scenario: Save before any run
- **WHEN** the user opens the dialog and clicks "Save" without starting a run
- **THEN** the version is unchanged and the dialog's warning is shown

#### Scenario: Run refused before it started
- **WHEN** the pipe laying refuses to start (e.g. "Please insert streets into the streets layer.") and the user clicks "Save"
- **THEN** the version is unchanged and the pipe laying warning is shown, also if `temp.lines` does not exist

#### Scenario: Failed or stopped run
- **WHEN** the dialog's last run ended with `error`, or with `stopped` before any pipe was laid, and the user clicks "Save"
- **THEN** the version is unchanged and the dialog's warning is shown

#### Scenario: Temp tables left by another run
- **WHEN** the `temp` tables hold the result of the other dialog or of an earlier session, this dialog has no finished run, and the user clicks "Save"
- **THEN** the version is unchanged and the dialog's warning is shown

### Requirement: A new run, Reject and closing clear the savable result
Starting a run, "Reject" and closing the dialog SHALL clear the dialog's savable result. A later "Save" SHALL then behave as without a savable result until a run ends with `finished` again.

#### Scenario: Failed run after a finished one
- **WHEN** a first run ends with `finished`, a second run ends with `error`, and the user clicks "Save"
- **THEN** the version is unchanged and the dialog's warning is shown

#### Scenario: Save after Reject
- **WHEN** a run ends with `finished`, the user clicks "Reject" and then "Save"
- **THEN** the version is unchanged and the dialog's warning is shown
