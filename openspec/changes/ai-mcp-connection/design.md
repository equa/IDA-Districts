## Context

The Districts Modeler is driven through dialogs. Only some steps are plain functions that work without a dialog:
`checkNetworkTopology`, `getUnconnectedFeatures`, `checkLineDirectionTopology` (`utility_functions/topology.py`),
`buildModel`/`runModel` (`ida_mosim.py`), `loadResults` and `network_economics.evaluateVersion`. Other checks report
only through dialogs or layers: the height check builds memory layers, and the energy-use and pump-list detection show
warnings in their dialogs (`warningText`). IDA runs write `runner.log` and `result.json` with `errors`
(`simulate_process.py`). The results are in `customer_s_*`, `energy_plant_s_*` and `line_s_*` tables. The user help is
the public XWiki space `IDA_Districts` (65 pages: getting started, help, model descriptions, changelogs). It can be read
through the REST API without an account, and its pages are xwiki/2.1. It has no pages yet for the features of the
latest changes.

The existing QGIS MCP plugin (jjsantos01/qgis_mcp and forks) runs a socket server in QGIS plus a separate MCP server.
It is tested on QGIS 3.22 only, has a fixed tool list, and exposes `execute_code` (`exec()` of any PyQGIS).

Decision session of 2026-11-18/19, decisions T1–T10. Runs on QGIS 3.44 (Qt5) and 4.2 (Qt6). The bridge uses
`qgis.PyQt.QtNetwork` (`QTcpServer`, `QTcpSocket`), which has the same API in Qt5 and Qt6. Enum access goes through
`utility_functions/compat.py` where the scoped Qt6 names differ.

## Goals / Non-Goals

**Goals:**
- An external MCP client can read the state of the open project and version, run model checks, read key figures and
  read the wiki, through tools named in Districts terms (T1, T2).
- Errors in the QGIS model, the IDA templates and the IDA results come back as structured findings, the same on every
  run and tested (T4, T7).
- Guidance based on the wiki and the version's state, without invented menu paths (T5).
- Nothing to install beyond QGIS and an MCP client (T6).

**Non-Goals:**
- Tools that change data or start jobs, and confirmation dialogs for them (T3; a later change).
- A chat panel inside the plugin (T1; later, on the same tool functions).
- Writing to the wiki (T9; its own change).
- Plausibility rules for template parameters (controller setpoints, heat pump sizing, storage). The AI can look at
  these through the raw-data tools and the wiki's model descriptions.
- Storing ideas or creating child versions from them (T8).

## Decisions

**D1 – Own bridge, not the QGIS MCP plugin (T2).** A `QTcpServer` on `127.0.0.1` runs in the QGIS main thread, so
tools may use the QGIS API and the plugin's database connection directly. It is switched on by an action in the
Districts menu, never by default. The protocol is newline-delimited JSON:
`{id, token, tool, args}` → `{id, ok, result | error}`. *Alternatives:* the QGIS MCP plugin (QGIS 3 only, no extension
point, arbitrary code); a thread with its own socket (the QGIS API and the DB connection are not thread-safe).

**D2 – Token and port file.** When it starts, the bridge picks a free port and a random token. It writes
`{port, token, pid, plugin_version}` to `<QGIS settings dir>/districts_mcp.json` and deletes the file when it stops.
The MCP server reads the file at every connection, so restarting QGIS needs no new client configuration. A request
with a wrong token is refused and logged. *Alternative:* a fixed port without a token: any local process could read
project data.

**D3 – Tool registry.** `districts/mcp/tools.py` holds one list of
`{name, description, input_schema, handler, needs_version}`. The bridge answers `list_tools` from it, and the MCP
server builds `tools/list` from that answer. A handler returns plain JSON data. Errors are text the AI can read
("no version loaded", "results missing: line_s_p"). A later chat panel calls the same handlers. *Alternative:* the
tool list hardcoded in the server, which would need changing for every new tool.

**D4 – MCP server with the standard library only (T6).** `districts/mcp/server.py` is a stand-alone script with no
`qgis` import, started by `python-qgis.bat`. It implements JSON-RPC 2.0 over stdio:
- `initialize`: negotiates the protocol version from a supported list, with the newest stable version first.
- `notifications/initialized`, `ping`, `tools/list`, `tools/call`.
- `resources/list` and `resources/read`: the step → wiki page map as resources.

Images (the map) are returned as MCP image content (base64 PNG). Clients list the tools once at their start, often
before QGIS runs: without a bridge, `tools/list` answers with `mcp/tools_snapshot.json`, a copy of the registry that a
test keeps equal to `tools.py` (decided while applying, 2026-11-19). When QGIS or the bridge is not running, the tool
call returns `isError` with a hint ("start QGIS and switch on the Districts AI connection"). The server never crashes.
"MCP configuration ..." (first "Copy MCP configuration") shows the Claude Code command and the Claude Desktop JSON with
the paths of the computer and whether `claude` is installed. The command is the QGIS `python.exe`, not
`python-qgis.bat`: MCP clients start a `.bat` only through a shell, and its output could mix into the protocol (found
2026-11-19 on a second computer: wrong user paths, no `claude` command). Claude Desktop runs its own copy of Claude
Code without a `claude` command; its Code tab and the VS Code extension read `.mcp.json` in the folder they open, so the
dialog writes that file into a chosen folder (keeping other entries; `.mcp.json` is in `.gitignore`, its paths belong to
one computer), and a `claude.exe` installed in `~/.local/bin` but not on the terminal's PATH is called with its full
path (2026-11-20, found on the second computer). *Alternative:* the official `mcp` SDK via `uv` (an install and a download for every
user); HTTP served directly from QGIS (Claude Desktop needs an extra bridge, and the connection drops when QGIS
restarts).

**D5 – Tools of this change (T3: read only).**
- **State:** `project_state` (project, versions, loaded version, templates, networks), `layers`, `features` (layer,
  filter, fields, limit), `render_map` (extent or layer, size).
- **Checks:** `run_checks` (D6).
- **Raw data:** `result_tables` (which exist, steps, results basis), `result_series` (table, feature ids, columns,
  time range, aggregation), `run_log` (last run: `result.json` errors, the tail of `runner.log`), `template_components`
  (the parsed components of a template, via `ida_components.py`).
- **Guidance:** `workflow_state`, `search_help`, `read_help_page` (D8).
- **Figures:** `version_kpis`, `compare_versions` (D9).

Outputs that may be large (`features`, `result_series`) have a limit and say when they were cut. Each tool gets its
own connection with the transaction always rolled back, not a read-only session: the height check needs a temporary
table, which PostgreSQL refuses in a read-only transaction (decided while applying, 2026-11-19). *Alternative:* one
generic SQL tool, which is open-ended, the AI would have to know the schema, and it is not testable.

**D6 – Checks and findings (T4).** A new module `utility_functions/model_checks.py` contains a list of rules
`{id, scope (qgis | templates | results), step, needs (tables/outputs), run(cur, config) → findings}`.
- A finding is `{rule, severity (error | warning | info), feature_type, feature_id | component, values, text}`. `text`
  comes from `tr_msg`, with a German translation.
- `run_checks(version, scope=all|qgis|templates|results)` runs the matching rules. When a rule's outputs are missing,
  it returns the finding `outputs_missing` (info, listing the outputs) instead of passing silently.
- The existing checks are wrapped. Where they only produce layers or dialog text (height check, energy-use and
  pump-list warnings), their logic is split so that it returns data, and the layer or dialog is built from that data.
  The energy-use and pump detection already returned data (`detectProject`); only the height check needed the split
  (`heightConsistencyRows`). The "line direction" check is not wrapped: it reverses lines (a repair, not a check).
  The unmet kWh of the cost optimization are not wrapped either: they need the source files of a submodel chosen in its
  dialog; the comfort rule reports the degree hours.
  (Decided while applying, 2026-11-19.)
- *Alternative:* the AI judges raw data only (not repeatable, not testable).

**D7 – New rules and thresholds (T7; defaults decided 2026-11-19).** The thresholds are taken from the project where
it holds them. The dynamic sizing does not store v_max and dp_spez_max (they live only in its open dialog), so
`run_checks` takes them, and every other threshold, as the optional argument `thresholds` (source `argument`), else the
default (decided while applying, 2026-11-19). Otherwise the
defaults below apply, and the finding names the default. The required supply temperature depends on the network type
(low-temperature and cold networks with decentral heat pumps), so it has no default: without a project value
`supply_temp_low` returns an `info` finding "no required supply temperature".

| rule | scope | condition | threshold source / default |
|---|---|---|---|
| `pipe_data_missing` | qgis | line without pipe, or pipe without diameter/roughness/u | — |
| `pipe_pressure_limit` | results | max p of a line > `pipes.p_max_bar` | pipe data; skipped when empty |
| `outputs_missing` | results | outputs a rule needs are not in the results | — |
| `supply_temp_low` | results | customer supply temperature < required supply temperature at load hours | template/customer value only; none → `info` |
| `delta_t_low` | results | mean ΔT of a customer at load hours < limit | default 15 K heating, 4 K cooling |
| `substation_dp_low` | results | Δp across the customer < minimum in any load hour | template/customer value; default 0.5 bar |
| `line_velocity_high` | results | velocity at peak > v_max | argument; default 3 m/s |
| `line_dp_spec_high` | results | Δp/m at peak > limit | argument; default 300 Pa/m (as `hydraulic_balancing`) |
| `plant_power_high` | results | plant power > nominal | plant data; skipped: the project has no nominal plant power yet |
| `plant_never_runs` | results | plant power ≤ 1 % of the peak over the whole results | — |

"Load hours" means steps with the customer's heat flow above 10 % of its peak, so that the standstill hours do not
produce false findings. Velocity and Δp/m reuse `hydraulic_balancing.specificPressureLoss`.

**D8 – Guidance from the wiki (T5, T10).** `districts/mcp/wiki_map.json` lists the workflow steps in order. Each
step is `{step, title, wiki: [page full names] | "missing", rules: [rule ids], done_when}`.
- `workflow_state(version)` evaluates `done_when` against the database: counts, the existence of tables, timestamps.
  The tables have no change timestamps, so "stale" means the topology no longer matches the lines (and the results
  were loaded before that change) (decided while applying, 2026-11-19).
- `search_help(query)` uses the XWiki REST search (Solr, limited to the space `IDA_Districts`).
- `read_help_page(page)` returns the title, the URL and the xwiki/2.1 content.

The pages are read with `urllib` (as `osm.py` does) and cached for the session. Without internet access, or for a
step marked `missing`, the tool says so, and the checks and figures still work. *Alternative:* a guide in the
repository, written twice and drifting apart from the wiki.

**D9 – Key figures (T8).** `version_kpis(version, scenario=None)` returns:
- heat delivered and peak load, linear heat density, losses in % and EUR, pump energy;
- energy and costs per plant and carrier, NPV and NPV per MWh delivered;
- comfort deficits, and the results basis (full year | periods | none).

The figures come from functions extracted from `utility_functions/reports.py` (`energyRows`, `economicsRows`, the
network report's figures) and from `network_economics.evaluateVersion`. The reports call the same functions.
`compare_versions(a, b)` returns both sets of figures and their differences, with a note when the results bases
differ. Without results, the result figures are `null` with a reason, and the network figures are still given.

**D11 – Data the cost optimization needs (added 2026-11-19 at the user's request).** `run_checks` gets the scope
`cost_optimization`, rules that tell before a run of hours whether it can start and what its NPV will miss:
- `mapping_expressions` (error/warning): every row of `public.model_parms` evaluated for every customer or energy
  plant exactly as the model build does (`invoke.substituteFields` + `safe_eval`, the substitution moved out of
  `invokeOneFeature` so both share it): unknown fields, an expression that fails (with examples), empty fields, rows
  with a direction but without macro, model or parameter name (the build ignores them).
- `cost_outputs` (warning): `cost_optimization.missingOutputs`.
- `economic_scenario` (error), `pipe_costs_missing`: pipes in use without costs (error), with example costs (info), a
  series in use with fewer than two priced pipes (warning: the size cannot change).
- `cost_pairs`: no supply/return pair from the plant connections (error), the warnings of `suggestPairs`.
- `required_load_missing` (warning): a customer template in use with a source file but no `requiredLoads.json` entry.
- `climate_file` (error): the climate file of the version for the representative periods.
- `pump_list` (warning), `energy_use_list` (info): `networkPumps.json` / `energyUse.json` without entries.

Error means the run cannot start or fails; warning means it runs with a gap in the NPV. *Alternative:* the same checks
in the dialog's start; possible later, the rules return data for it.

**D10 – Developer setting for code execution.** Not part of this change. If it is ever added, it is a separate tool
behind a setting that is off by default and never listed otherwise.

## Risks / Trade-offs

- [A tool blocks the QGIS main thread on a large network] → limits on rows and time steps, aggregation done in SQL,
  and a measured budget (checks on the test network < 5 s). Long checks report progress in a later change.
- [Tool calls during a running job (period run, cost optimization) read incomplete tables] → `result_tables` and
  `version_kpis` report a running job (the plugin's job state) and mark the figures as provisional. Tools never write.
- [Another local process talks to the bridge] → bound to 127.0.0.1, per-session token in the profile file, opt-in,
  stopped with QGIS.
- [The MCP protocol changes] → the supported versions are negotiated, and a protocol test in CI pins the answers. Only
  the server script would need changing, not the bridge or the tools.
- [Wiki pages are renamed or outdated, or pages for new features are missing] → an online test checks the pages in the
  map. Missing pages are marked, and the AI falls back to findings and figures. The wiki update skill (T9) closes the
  gap later.
- [Default thresholds give false findings in some projects] → each finding states its threshold and its source, and
  project values take precedence. The defaults are documented in the wiki.
- [The AI misreads findings or figures] → structured values next to the text, and every figure with its unit and
  results basis.

## Migration Plan

No database schema change, so `upgrade.py` is untouched. The bridge is off until the user switches it on. Rollback
means removing the menu action. The reports keep their output, which their existing tests check after the figure
functions are extracted.

## Open Questions

None. (The D7 defaults were decided on 2026-11-19.)
