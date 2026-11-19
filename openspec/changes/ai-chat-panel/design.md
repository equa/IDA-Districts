## Context

The AI connection (change ai-mcp-connection) gives an external MCP client 14 read-only tools in a registry
(`districts/mcp/tools.py`: name, description, JSON schema, handler; each on its own rolled-back DB transaction), the
model checks (`utility_functions/model_checks.py`), the key figures (`utility_functions/version_kpis.py`) and the wiki
guidance (`districts/mcp/guidance.py`). This change adds a chat inside the plugin on the same registry. The main dialog
(`DistrictsDialog`) has six tabs, each detachable into a floating window (`FloatingTabDialog`); it is created once per
QGIS session. The QGIS Python (3.12 on 3.44 and 4.2) has no `anthropic` package; QGIS 4.2 has pydantic. The DB login is
stored in the QGIS authentication database (`auth_id` in the plugin settings). Per-project settings so far live in
`configProject.txt` in the user's own projects folder, which colleagues do not share.

Decision session of 2026-11-19, decisions T1–T6. Runs on QGIS 3.44 (Qt5) and 4.2 (Qt6); widgets use the scoped enums
of `utility_functions/compat.py`.

## Goals / Non-Goals

**Goals:**
- Ask about the loaded project inside the Districts Modeler, answered with the same tools as the AI connection (T4).
- Project data leaves the computer only in projects the team allowed, through tools the project allows (T3).
- Costs visible and bounded per session (T5); no key in plain text (T2).

**Non-Goals:**
- Tools that change data or start jobs (still read-only, as ai-mcp-connection T3).
- Continuing an earlier conversation; conversations end with the QGIS session (T6).
- A dock widget next to the map (T4: the tab can be detached).
- Claude on Bedrock, Vertex or Foundry; the Claude API only.

## Decisions

**D1 – SDK installed on demand (T1).** `importlib.util.find_spec('anthropic')` decides whether the tab shows the chat
or "Install AI support". The button runs `<QGIS python.exe> -m pip install --user --upgrade anthropic` as a
`QProcess` (no blocking, output in the tab); afterwards the tab asks for a QGIS restart if the import still fails. The
installed version is shown in the status line. *Alternatives:* bundling the SDK (a compiled dependency, our
maintenance); plain HTTPS (our own streaming parser, error handling and API drift).

**D2 – API key (T2).** A field "Anthropic API key" in the plugin settings dialog stores the key in the QGIS
authentication database (a Basic config with the key as password; setting `ai_auth_id`), like the DB login. The client
is `anthropic.Anthropic(api_key=key)` with the key from there, else `anthropic.Anthropic()`, which resolves
`ANTHROPIC_API_KEY`, `ANTHROPIC_AUTH_TOKEN` or an `ant auth login` profile. The status line names the source
("QGIS settings" / "environment or profile"); the key is never logged or shown. The tab says that the API is billed per
use, separately from a Claude subscription.

**D3 – Per-project permission (T3).** A table `public.ai_settings` in the project database (one row: `allowed boolean
DEFAULT false`, `disabled_tools text[]`, `changed_by text`, `changed_at timestamp`), in `DB_projectTablesDefault.txt` and
created by `upgrade.py` for old projects (`CREATE TABLE IF NOT EXISTS`, at every version load like the economic
tables). Being in the project database, it is the same for every colleague. The tab shows "AI assistant not allowed in
this project" with a button to allow it: a confirmation names what is sent (the tool table of the explanation of
2026-11-19) and lets tools be switched off. The tool registry gets `allowedTools(cur)`; the chat offers only those, a
call to another tool answers "not allowed in this project", and the MCP bridge applies the same check (a
`ToolError` "the AI assistant is not allowed in this project"). `search_help` and `read_help_page` read only the public
wiki and stay available. *Alternative:* `configProject.txt`, which colleagues do not share.

**D4 – The tab (T4).** `tab_ai_assistant` added in code in `DistrictsDialog` (no change to the .ui file). Top: a status
line (SDK version, key source, project allowed, model) and model and effort selectors. Middle: the conversation as a
`QTextBrowser` with HTML (user, assistant text as it streams, each tool call as a line with its arguments and a
collapsible result). Bottom: input, Send, Stop, New conversation, Export, and the cost line ("this answer 0.08 USD ·
session 0.41 USD of 2.00 USD, estimated"). Model and effort are remembered per user in `QSettings`. Changing the model
in a running conversation asks first and starts a new conversation (caches and thinking blocks are tied to the model).

**D5 – Conversation loop.** A manual loop over `client.beta.messages.stream(...)` with `get_final_message()`, not the
SDK tool runner: the tools must run in the QGIS main thread (QGIS API, layers), and the loop stops between steps for
the cost limit and the Stop button. The loop runs in a worker thread (`QThread`); for each `tool_use` it emits a signal
to the main thread, which runs `callTool` with the tool context and hands the result back (a `threading.Event`). Every
`tool_result` of one assistant turn goes back in one user message; errors as `is_error: true`. A map image becomes an
image block. Request: `model` (default `claude-opus-5-5`), `max_tokens=64000`, `output_config={'effort': ...}` (default
`medium`), thinking left to the model (adaptive on Opus 5.5; thinking blocks passed back unchanged),
`betas=['server-side-fallback-2026-07-01']`, `fallbacks='default'`, automatic prompt caching
(`cache_control={'type': 'ephemeral'}`), the tools sorted by name. The system prompt is fixed (no date, no project
name, for the cache): role, read-only tools, findings before guesses, answer in the user's language, name wiki pages
instead of inventing menu paths. The loaded project and version go into each user message. Stop reasons: `tool_use`
continues; `end_turn` ends; `max_tokens` ends with a note; `pause_turn` resends; `refusal` shows the category from
`stop_details` (after the fallback chain) and ends. API errors are caught most specific first
(`AuthenticationError` with the key source, `RateLimitError`, `APIStatusError`, `APIConnectionError`) and shown in the
chat. `eager_input_streaming` stays off: the tool inputs are a few short fields, and without it the API validates them.

**D6 – Costs (T5).** A price table per model in USD per million tokens (input, cache write 5 min, cache read, output)
with the date it was taken (2026-11-03: Opus 5.5 4 / 20, Sonnet 5.5 2 / 10, Haiku 5.5 0.10 / 0.50; cache write 1.25x,
cache read as published). The cost of a step comes from `usage` (`input_tokens`, `cache_creation_input_tokens`,
`cache_read_input_tokens`, `output_tokens`); a fallback step is priced with the model that served it
(`response.model`). Shown as an estimate. The limit (default 2 USD, setting) is checked before each request: above it
the loop waits for "Continue (+2 USD)" or "Stop".

**D7 – Export (T6).** "Export" writes the conversation as one HTML file (questions, answers, tool calls with arguments,
results in `<details>`, model, costs, date) to `versions/<version>/ai_chat_<date-time>.html` or a chosen path. Nothing
is saved without "Export".

**D8 – Tests.** The loop takes a backend object (`stream(**params) -> final message, text events`); the tests give it a
fake that returns scripted messages (text, tool_use, refusal, max_tokens, errors), so no test calls the API or needs a
key. The CI runner installs `anthropic` (`.github/RUNNER_SETUP.md`) so the import and the request shape are tested
against the real SDK types.

## Risks / Trade-offs

- [pip is blocked on a company computer] → the tab shows pip's message and the manual command; the MCP connection
  remains as the alternative.
- [The UI freezes during a request] → the API runs in the worker thread; only the tool handlers run in the main
  thread, with their row and time limits.
- [Costs run away in a tool loop] → the session limit asks before continuing; the cost line updates after every step.
- [Project data sent where it is not allowed] → off by default per project, a confirmation naming the data, tools that
  can be switched off; the MCP bridge applies the same rule.
- [The key leaks] → only in the QGIS authentication database or the user's environment; never logged or exported.
- [Prices change] → the table has its date and the cost is labelled as an estimate.
- [SDK or API changes] → the SDK is installed in its current version; the tests run against it in CI.

## Migration Plan

`upgrade.py` creates `public.ai_settings` in old projects at the next version load; the assistant is off until allowed.
Without the SDK the tab shows the install button; nothing else changes. Rollback: remove the tab; the table stays
unused.

## Open Questions

None.
