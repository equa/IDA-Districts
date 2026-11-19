## Why

Users of the Districts Modeler need guidance through a long workflow (project, version, import, pipe laying, topology,
IDA model, run, results, economics). Modelling errors often show up late: in the QGIS model, or after an IDA run as
poor substations, too little Δp or overloaded pipes and plants. An AI assistant connected to the plugin could explain
the next step, find these errors and suggest variants. The checks and figures it needs exist today only behind
dialogs and reports. The existing QGIS MCP plugin runs on QGIS 3 only, cannot host plugin-specific tools, and gives
the AI arbitrary code execution next to the database credentials. Decision session of 2026-11-18/19, decisions T1–T10.

## What Changes

- A **bridge** inside the Districts Modeler, switched on by the user. It is a localhost socket server on the QGIS main
  thread, checks a per-session token, and calls registered tools. No `execute_code`. The database credentials never
  cross it.
- An **MCP server** (`districts/mcp/server.py`), written with the Python standard library only and started with QGIS's
  Python (`python-qgis.bat`). It speaks MCP over stdio to an external client (Claude Desktop, Claude Code) and forwards
  tool calls to the bridge. The plugin gets a button "Copy MCP configuration".
- **Read-only tools**: project and version state, layers and features, a rendered map image, the raw result tables and
  IDA run logs. No tool changes data or starts a job.
- **Model checks**: `run_checks(version, scope)` returns findings {rule, severity, feature/component, values, text}.
  - Wrapped existing checks: topology, unconnected features, heights, energy-use and pump-list warnings, run
    errors, comfort deficits.
  - About ten new rules on pipe data, substations, lines and plants. Thresholds come from the project, otherwise from
    documented defaults.
- **Guidance**: `workflow_state(version)` reports each workflow step as done, missing or stale. `search_help` and
  `read_help_page` read the public XWiki `IDA_Districts` live. A map in the plugin links each step to its wiki pages
  and check rules. Steps without a wiki page yet are marked `missing`.
- **Key figures**: `version_kpis(version)` and `compare_versions(a, b)` return the figures of the network report and
  the economics, from shared functions that the reports also use. The AI uses them to back up its suggested ideas.

## Capabilities

### New Capabilities
- `ai-bridge`: switching the bridge on, the socket protocol, the token and port file, the tool registry, the MCP
  server process (initialize, tools, resources) and the "Copy MCP configuration" button.
- `model-checks`: `run_checks` and its rules, finding format, severities, thresholds and their defaults.
- `ai-guidance`: `workflow_state`, the step → wiki page → rule map, `search_help` and `read_help_page`.
- `version-kpis`: `version_kpis` and `compare_versions`, the figures and their results basis.

### Modified Capabilities
<!-- None: the existing specs (ida-session-start, sizing, pipe-pair balancing, ...) keep their requirements; the
     reports keep their content, only their figure calculation becomes a shared function. -->

## Impact

- New: `districts/mcp/` (bridge, tool registry, tools, stand-alone server, wiki map) and a check module with the rules.
- Changed: `districts.py` (bridge switch, "Copy MCP configuration" button), `utility_functions/height_check.py`,
  `topology.py`, `energy_use.py` and `network_pumps.py` (checks also return data), `utility_functions/reports.py` and
  `network_economics.py` (figures as shared functions), translations, tests, README.md and CLAUDE.md.
- External: read access to `https://equa.cloud.xwiki.com` (public, no account). The MCP client is configured by the
  user.
- Runs on QGIS 3.44 and 4.2. No new Python dependency, and no change to the project database schema.
- Later changes: the wiki update skill (T9), and jobs with user confirmation, ideas as child versions and a chat panel
  inside the plugin.
