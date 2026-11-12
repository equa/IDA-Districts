# Automatic plugin tests (dev → main)

The workflow `.github/workflows/plugin-tests.yml` runs the pytest suite of the Districts Modeler plugin
(`districts/test`) for every push to `dev`, once with QGIS 4.2 and once with QGIS 3.44.
The checks belong to the pushed commit, so a pull request `dev` → `main` shows the result of the latest
`dev` commit; GitHub only allows the merge when both checks are green (branch protection, step 5).

The tests need QGIS, a PostgreSQL/PostGIS/pgRouting server and IDA Districts (with license), so they run on
a **self-hosted runner**: a Windows PC of ours, not a GitHub cloud machine.

## 1. Prepare the runner PC

The PC needs, like for running the tests manually:

- QGIS 4.2.3 and QGIS 3.44.8 in `C:\Program Files\QGIS ...` (other paths: change `matrix.python` in the workflow)
- IDA Districts in `C:\Program Files (x86)\IDA Districts\` with a valid license for the runner's Windows user
- PostgreSQL 18 (`C:\Program Files\PostgreSQL\18\`, used for `psql`) and the test server on port 5433
- the sample data in `C:\EQUA\Projekte\districts\samples` (other path: repository variable `DISTRICTS_TEST_SAMPLES`)
- pytest for the QGIS Python, installed **as the runner's Windows user** (QGIS 4.2 and 3.44 share the user site):

  ```powershell
  & "C:\Program Files\QGIS 4.2.3\bin\python-qgis.bat" -m pip install --user pytest==9.2.0 pytest-qgis==5.0.2
  ```

## 2. Test server as Windows service

The test server must run without anyone being logged in. Register it once as a service
(PowerShell **as administrator**; stop a running instance first):

```powershell
& "C:\Program Files\PostgreSQL\18\bin\pg_ctl.exe" -D "C:\PostgreSQL\18\districts_test" stop
& "C:\Program Files\PostgreSQL\18\bin\pg_ctl.exe" register -N "postgresql-districts-test" -D "C:\PostgreSQL\18\districts_test" -S auto
Start-Service postgresql-districts-test
```

The service account (default: Network Service) needs full access to `C:\PostgreSQL\18\districts_test`.

## 3. Install the runner

GitHub → repository `equa/IDA-Districts` → Settings → Actions → Runners → **New self-hosted runner** → Windows.
Follow the commands shown there (download to `C:\actions-runner`, `config.cmd` with the token shown).
Keep the runner folder that short: the checkout lands in `<runner>\_work\IDA-Districts\IDA-Districts\profile\python\plugins`
and the longest plugin file adds 140 characters (Windows path limit: 260).
When `config.cmd` asks:

- labels: add **`districts`** (the workflow uses `runs-on: [self-hosted, windows, districts]`)
- run as service: **No**. Start it with `C:\actions-runner\run.cmd` in the session of the Windows user that owns
  the IDA license and the pytest installation (e.g. via autostart / task scheduler "at log on").
  A runner service running as Network Service would neither have the IDA license nor pytest.

Only one runner should have the label `districts`: the tests use one test DB and one IDA installation.

## 4. Secrets and variables

GitHub → Settings → Secrets and variables → Actions:

| Name | Kind | Value |
|---|---|---|
| `DISTRICTS_TEST_DB_USER` | secret | DB user of the test server (superuser, creates and drops the test DBs) |
| `DISTRICTS_TEST_DB_PASSWORD` | secret | its password |
| `DISTRICTS_TEST_DB_HOST` | variable (optional) | default `localhost` |
| `DISTRICTS_TEST_DB_PORT` | variable (optional) | default `5433` |
| `DISTRICTS_TEST_SAMPLES` | variable (optional) | default `C:\EQUA\Projekte\districts\samples` |
| `DISTRICTS_SIM_CASES` | variable (optional) | simulation test cases, default `C:\EQUA\Projekte\districts\testing` |

## 5. Require the tests for main

GitHub → Settings → Branches → branch protection rule (or ruleset) for `main`:

- "Require a pull request before merging"
- "Require status checks to pass" → add `plugin-tests (QGIS 4.2)` and `plugin-tests (QGIS 3.44)`
  (they appear in the list after the workflow ran once)

From then on dev is merged into main via a pull request (`dev` → `main`); the merge button is enabled when
both checks are green. Pushing directly to main is blocked.

## Running it

- **Push to dev:** both QGIS versions, all templates incl. IDA simulation (~5 min each). A newer push to dev
  cancels a running test. Push the final state to dev and wait for the green checks before merging into main.
- **Manually** (Actions → plugin-tests → Run workflow, any branch):
  - `with_simulation` off: only the steps without IDA (`-m "not ida"`)
  - `simulation_tests` on: afterwards also the simulation test suite `districts/simulation_tests` (takes long)
- The JUnit reports are attached to each run (artifacts `test-report-qgis-*`).
- After each job the IDA Districts processes started by the job are ended (`.github/scripts/cleanup-ida.ps1`);
  test projects (`autotest_*` DBs and folders) are removed by the tests themselves, except after a cancelled run.

## Security

The runner executes the code of the tested commit on this PC, as the Windows user running `run.cmd`.
The repository is public, so the workflow has **no `pull_request` trigger**: for a pull request from a fork,
GitHub would use the workflow file of that pull request, and an outsider could run their own code here.
A push to `dev` and a manual run need write access to the repository.

- Never add a `pull_request` or `pull_request_target` trigger to a workflow that uses this runner.
- Settings → Actions → General:
  - Actions permissions: "Allow equa, and select non-equa, actions and reusable workflows" with
    "Allow actions created by GitHub" (the workflow uses only `actions/checkout` and `actions/upload-artifact`)
  - Fork pull request approval: "Require approval for all external contributors"
  - Workflow permissions: "Read repository contents and packages permissions";
    "Allow GitHub Actions to create and approve pull requests" off
- The DB secrets are only for the local test server (port 5433), never for a production database.
