## 1. Bridge and MCP server

- [x] 1.1 `districts/mcp/bridge.py`: `QTcpServer` on 127.0.0.1 (free port), newline-delimited JSON, token check, error answers, `districts_mcp.json` written on start and deleted on stop/unload (D1, D2)
- [x] 1.2 `districts/mcp/tools.py`: tool registry {name, description, input_schema, handler, needs_version}, `list_tools`, no code-execution tool (D3)
- [x] 1.3 `districts/mcp/server.py`: stdlib-only JSON-RPC 2.0 over stdio (initialize with version negotiation, initialized, ping, tools/list, tools/call, resources/list, resources/read), reads `districts_mcp.json` per connection, `isError` hint when QGIS/bridge is absent, image content for PNG (D4)
- [x] 1.4 `districts.py`: menu action to switch the AI connection on/off (off at start), "Copy MCP configuration" with the paths of the QGIS Python and `server.py`; QGIS 3.44 and 4.2 (enums via `compat.py`)

## 2. Read-only tools

- [x] 2.1 State tools: `project_state`, `layers`, `features` (filter, fields, limit, cut note), `render_map` (extent or layer, size, PNG)
- [x] 2.2 Raw-data tools: `result_tables` (tables, steps, results basis, running job), `result_series` (SQL aggregation, limits), `run_log` (`result.json` errors, `runner.log` tail), `template_components` (`ida_components.py`)

## 3. Model checks

- [x] 3.1 `utility_functions/model_checks.py`: rule list {id, scope, step, needs, run}, finding format, `run_checks(version, scope)`, `outputs_missing`, threshold resolution (project, setting, default) (D6)
- [x] 3.2 Split the height check (`heightConsistencyRows`) so its logic returns data, layers built from it unchanged; energy-use and pump-list detection already return data
- [x] 3.3 Wrapped rules: topology, unconnected features, heights, energy-use and pump-list warnings, run errors, comfort deficits (`penalties.py`); line directions (a repair) and unmet kWh (a submodel of the dialog) not wrapped, see design D6
- [x] 3.4 New rules (D7): `pipe_data_missing`, `pipe_pressure_limit`, `line_velocity_high`, `line_dp_spec_high` (via `hydraulic_balancing.specificPressureLoss`, thresholds as `run_checks` argument)
- [x] 3.5 New rules (D7): `delta_t_low`, `substation_dp_low`, `supply_temp_low` (project value only, else info) at load hours (> 10 % of peak), `plant_power_high`, `plant_never_runs`
- [x] 3.6 Register `run_checks` as a tool

## 4. Guidance

- [x] 4.1 `districts/mcp/wiki_map.json`: workflow steps with wiki pages (from the 65 pages of `IDA_Districts`), `missing` for cost optimization, representative periods, economics, energy use, network pumps, pipe series, dynamic sizing; rule ids; done conditions
- [x] 4.2 `workflow_state(version)`: done/missing/stale with reasons from the database
- [x] 4.3 `search_help`, `read_help_page` via the XWiki REST API with `urllib`, session cache, offline error; the map as MCP resources

## 5. Key figures

- [x] 5.1 Extract the figures of the network report and `energyRows`/`economicsRows` (`reports.py`) into shared functions on top of `network_economics.evaluateVersion`; reports call them with unchanged output
- [x] 5.2 `version_kpis(version, scenario)` (results basis, `null` with reason without results) and `compare_versions(a, b, scenario)`

## 6. Tests

- [x] 6.1 Protocol test without QGIS: JSON-RPC lines to `server.py` (initialize, tools/list via a fake bridge, isError without `districts_mcp.json`, ping after an error)
- [x] 6.2 Bridge test (pytest-qgis): on/off and file, wrong token refused, failing tool answered, `list_tools` without code execution, every tool leaves a test version unchanged (e2e)
- [x] 6.3 Rule tests (e2e): each rule on a broken test version (synthetic result tables), `outputs_missing`, thresholds from setting and default, standstill hours ignored, supply-temperature info without value
- [x] 6.4 Unchanged reports and checks: height-check layers, energy-use/pump dialogs and the network report figures equal before and after the extraction; `version_kpis` equals the report (e2e)
- [x] 6.5 Guidance tests: map rule ids exist, `workflow_state` on new/partial/stale versions (e2e), offline error with a failing URL; online test of the map pages marked so it can be skipped without network

## 7. Translations, documentation, validation

- [x] 7.1 tr_msg texts of the findings, the menu action and the button with German translations, de/en compiled
- [x] 7.2 README.md (AI connection: switch on, Copy MCP configuration, client setup, tools, read-only) and CLAUDE.md (`districts/mcp/`, `model_checks.py`, `wiki_map.json`, `districts_mcp.json`)
- [x] 7.3 Local validation: from districts/, the QGIS Python runs `-m pytest` and it passes on 3.44 and 4.2 (with `-m "not ida"` without IDA Districts), including test_static_mypy.py and test_messages.py
- [ ] 7.4 CI: commit, push to dev and watch the plugin-tests run until both QGIS jobs pass
