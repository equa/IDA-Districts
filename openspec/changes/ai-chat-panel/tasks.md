## 1. Access

- [x] 1.1 SDK check and "Install AI support" (`QProcess` with the QGIS python.exe, `pip install --user --upgrade anthropic`, output in the tab, restart hint, SDK version shown) (D1)
- [x] 1.2 API key field in the plugin settings dialog, stored in the QGIS authentication database (`ai_auth_id`); client from it, else the SDK's own sources; key source in the status line, never logged (D2)
- [x] 1.3 Table `public.ai_settings` (`DB_projectTablesDefault.txt`, `upgrade.py` for old projects), load/save, confirmation dialog naming the data with the tool switches (D3)
- [x] 1.4 `allowedTools(cur)` in the tool registry; the MCP bridge refuses tools of a project that is not allowed or switched off (`search_help`, `read_help_page` always) (D3)

## 2. Chat

- [x] 2.1 Backend around `client.beta.messages.stream` (fallbacks default, beta header, automatic caching, effort, max_tokens 64000), injectable for tests (D5, D8)
- [x] 2.2 Conversation loop in a worker thread: text events, tool calls handed to the main thread and back, all results of a turn in one message, stop reasons tool_use / end_turn / max_tokens / pause_turn / refusal, typed API errors (D5)
- [x] 2.3 Fixed system prompt; project and version in each user message; tools sorted (D5)
- [x] 2.4 Price table with its date, cost per step from usage, session cost, limit with Continue / Stop (D6)

## 3. Tab

- [x] 3.1 `tab_ai_assistant` in `DistrictsDialog` (detachable): status line, model and effort (QSettings), conversation view with tool lines and collapsible results, input, Send, Stop, New conversation, cost line; model change asks and starts anew (D4)
- [x] 3.2 Export as HTML into the version folder or a chosen path (D7)

## 4. Tests

- [x] 4.1 Unit: cost of a step and the limit, the loop with a fake backend (text, two tool calls, failing tool, refusal, max_tokens, pause_turn, Stop, authentication error), request shape (tools sorted, fallbacks, effort), export without key
- [x] 4.2 pytest-qgis: the tab with and without SDK, model change, conversation kept when the dialog reopens, the settings field stores in the authentication database
- [x] 4.3 e2e: `public.ai_settings` created for an old project, permission and switched-off tools in the chat tool list and in the MCP bridge, same decision for a second connection

## 5. Translations, documentation, validation

- [x] 5.1 tr_msg texts with German translations, de/en compiled
- [x] 5.2 README.md (AI assistant tab, key, permission, costs), CLAUDE.md (`districts/ai/`, `public.ai_settings`), `.github/RUNNER_SETUP.md` (the runner installs `anthropic`)
- [x] 5.3 Local validation: from districts/, the QGIS Python runs `-m pytest` and it passes on 3.44 and 4.2 (with `-m "not ida"` without IDA Districts), including test_static_mypy.py and test_messages.py
- [ ] 5.4 CI: commit, push to dev and watch the plugin-tests run until both QGIS jobs pass
