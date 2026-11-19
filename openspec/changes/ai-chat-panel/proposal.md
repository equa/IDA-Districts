## Why

The AI connection (change ai-mcp-connection) needs an external MCP client: Claude Desktop or Claude Code, installed and
configured on each computer (on a second computer this failed on paths and on a missing `claude` command). A chat
inside the Districts Modeler lets every user ask about the loaded project with the same read-only tools, checks and
key figures, without a second application. Decision T1 of ai-mcp-connection planned it ("a chat panel inside the plugin
may follow later and calls the same tools"). Decision session of 2026-11-19, decisions T1–T6.

## What Changes

- A seventh tab **"AI assistant"** in the main dialog, detachable like the other tabs: chat view, input, send and stop,
  model and effort, the cost of each answer and of the session, "New conversation" and "Export".
- Claude is called through the official **`anthropic` Python SDK**. When it is missing, the tab offers "Install AI
  support" (`pip install --user anthropic` with the QGIS Python); without it only the tab is unavailable.
- **API key**: a new field in the plugin settings, stored in the QGIS authentication database like the DB password;
  when empty, the SDK's own sources (`ANTHROPIC_API_KEY`, an `ant auth login` profile). The tab names the source.
- **Per-project permission**: the assistant works only in projects with "AI assistant allowed" (off by default), set
  with a confirmation that names what is sent to Anthropic, together with tools switched off for the project; stored
  in the project database for the whole team. The MCP bridge applies the same switch and tool list.
- The assistant uses the tools of the AI connection (`districts/mcp/tools.py`) directly, in the QGIS main thread; every
  tool call is shown in the chat with its arguments and, collapsed, the result that was sent.
- Claude Opus 5.5 by default (Sonnet 5.5 and Haiku 5.5 selectable), effort selectable, server-side refusal fallback;
  the estimated cost per answer and per session, and a cost limit per session (default 2 USD) after which the chat asks
  before continuing.
- Conversations live for the QGIS session; "Export" writes one as HTML.

## Capabilities

### New Capabilities
- `ai-chat`: the tab, the conversation loop with tools, model, effort, refusal fallback, costs and limit, export.
- `ai-access`: the SDK install, the API key and its source, the per-project permission and tool list (for the chat and
  the MCP bridge).

### Modified Capabilities
<!-- ai-bridge (change ai-mcp-connection, not archived yet): the bridge applies the project's permission; its spec text
     is updated in that change when this one is applied. -->

## Impact

- New: `districts/ai/` (chat widget, conversation loop, backend around the SDK, costs, export, permission store),
  table `public.ai_settings` (`DB_projectTablesDefault.txt`, `upgrade.py`).
- Changed: `districts_dialog_base.ui` / `districts_dialog.py` (tab), the settings dialog (API key), `districts.py`,
  `mcp/bridge.py` (permission), translations, tests, README.md, CLAUDE.md, `.github/RUNNER_SETUP.md` (the runner
  installs `anthropic`).
- External: the Claude API (billed per use through an Anthropic Console account, not covered by a Claude subscription);
  project data returned by the tools is sent to Anthropic in allowed projects only.
- New dependency, optional: `anthropic` in the user site of the QGIS Python. Runs on QGIS 3.44 and 4.2.
