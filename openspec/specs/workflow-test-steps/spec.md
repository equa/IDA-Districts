# workflow-test-steps Specification

## Purpose
TBD - created by archiving change guard-save-of-run-results. Update Purpose after archive.
## Requirements
### Requirement: A failed step skips the later steps of its workflow
In a test class marked `@pytest.mark.incremental`, a step that fails SHALL skip the later steps of the same workflow (same class and parameter) with the reason "previous step failed (<step>)".

#### Scenario: Failure in a step
- **WHEN** `test_create_project[db_defaults]` fails
- **THEN** every later step of the `db_defaults` workflow is skipped with "previous step failed (test_create_project)", and the steps of the other workflows still run

### Requirement: A missing prerequisite skips the later steps of its workflow
In a test class marked `@pytest.mark.incremental`, a step that is skipped while its fixtures are set up SHALL skip the later steps of the same workflow with the reason "previous step skipped (<step>: <skip reason>)".

#### Scenario: Sample data missing
- **WHEN** the sample data is not found, so `test_import_streets[db_defaults]` is skipped by the fixture `samples_dir`
- **THEN** the steps after it in the `db_defaults` workflow, including `test_pipe_laying_algorithm[db_defaults]`, are skipped with "previous step skipped (test_import_streets: sample data not found: …)", and the steps before it ran normally

### Requirement: A step that does not apply to a template keeps the workflow running
A step skipped because it does not apply to the workflow's template (`only_for` in the test, or the marker `templates` before the fixtures) SHALL NOT skip the later steps. A step with a prerequisite fixture SHALL be checked against its templates before that fixture is set up.

#### Scenario: Step for another template
- **WHEN** `test_create_materials[db_defaults]` is skipped with "not part of the template 'DB default values'"
- **THEN** the later steps of the `db_defaults` workflow still run

#### Scenario: Import step of another template without sample data
- **WHEN** the sample data is not found and the workflow `heating` reaches `test_import_streets[heating]`
- **THEN** the step is skipped with "not part of the template 'Heating network'" without setting up `osm_offline`, and the later steps of the `heating` workflow still run

