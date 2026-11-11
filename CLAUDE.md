# CLAUDE.md

Instructions for an agent in this repository. Its users may be new to git:
say what each git command does before you run it.

## What it is

- The QGIS plugin **Districts Modeler** (`districts/`, `metadata.txt`) for
  district energy systems: projects and versions in PostgreSQL/PostGIS, pipe
  laying, network topology, pipe sizing, result maps, and the coupling to IDA
  Districts simulations. It runs on QGIS 3.44 and 4.2.
- The repository root stands in for a QGIS `python/plugins` folder: CI checks
  it out into `profile/python/plugins`, and the plugin finds its own files
  through `qgisSettingsDirPath()` + `python/plugins/districts`. Locally,
  `districts` in the QGIS profile's plugin folder is a junction to
  `districts/` here; never uninstall or update the plugin from QGIS's Plugin
  Manager, that deletes the repository's folder.
- `openspec/`, `.claude/`, `package.json` and `node_modules/` sit at the root,
  outside `districts/`: QGIS never loads them.

## Build and test

- Tests: pytest with pytest-qgis in `districts/test` (`districts/pytest.ini`),
  run from `districts/` with the QGIS Python, e.g.
  `& "C:\Program Files\QGIS 4.2.0\bin\python-qgis.bat" -m pytest`.
  Marker `e2e` needs the test DB (`DISTRICTS_TEST_DB_*`), `ida` needs IDA
  Districts; `-m "not ida"` skips the simulations. `test/run_in_qgis.py` runs
  them inside a running QGIS.
- `districts/simulation_tests` runs only when named; it takes long.
- `test_static_mypy.py` runs mypy (`districts/mypy.ini`) against the known
  findings in `test/mypy_baseline.txt`; `test_messages.py` checks that every
  `tr_msg` text has a German translation.
- CI: `.github/workflows/plugin-tests.yml` runs on every push to `dev`, on a
  self-hosted Windows runner (`.github/RUNNER_SETUP.md`). Never write a DB
  credential into a file, a commit or a command line you print.

## Changes (OpenSpec)

- A change's proposal, design, tasks and spec deltas live in this repository,
  in `openspec/changes/<name>/`; specs in `openspec/specs/`; an archived change
  in `openspec/changes/archive/`. `openspec/config.yaml` holds the
  per-artifact rules.
- Skills: `/opsx:explore`, `/opsx:propose`, `/opsx:apply`, `/opsx:archive`.
  The CLI is `npx openspec` after `npm ci`; use it where a skill names
  `openspec`. Run `npx openspec validate --all` before committing a change to
  `openspec/`.
- Commit a change's artifacts with its code.

## Decision sessions

`/opsx:explore`, and every question `/opsx:propose` asks, run as a decision
session; this overrides the skills' own question style.

- One question per turn, in plain text; never the AskUserQuestion tool.
- Each turn has the sections `## TLDR` (where the session stands, a few
  lines), `## Decisions taken` (T1, T2, ...), `## Implications` (each tied to
  a decision) and `## Questions` (answered ones struck through), then the
  question.
- The question offers lettered options (a, b, c), each with its trade-off,
  and names one as the recommendation with its reason. The user answers with
  a letter or in their own words.
- Write no artifact while a question that changes it is open.

## Git

- Work happens on `dev`; `main` takes `dev` through a pull request once both
  plugin-tests checks are green. `release/<version>` branches hold releases.
- Commit messages follow the history: `*topic: what changed`, several topics
  in one message each starting with `*`.
- Stage explicit paths (`git add <path>`); never `git add -A` or `git add .`.
- `git pull --rebase` before a push; never force-push `dev` or `main`.
- After a push to `dev`, watch the run (`gh run watch` or the Actions tab) and
  fix until both jobs pass.

## Code comments

Comment the *why*, never the *what*: a non-obvious reason, a caveat or an
invariant. Never restate the code. Keep a comment short; reasoning belongs in
the change's `design.md`.
