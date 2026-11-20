## ADDED Requirements

### Requirement: Opt-in bridge on localhost
The Districts Modeler SHALL offer an action that switches the AI connection on and off; it SHALL be off when QGIS starts. Switched on, the bridge SHALL listen on 127.0.0.1 only, on a free port, in the QGIS main thread, and SHALL write `{port, token, pid, plugin_version}` with a random per-session token to `districts_mcp.json` in the QGIS settings folder; switched off or when QGIS closes, it SHALL stop listening and delete the file.

#### Scenario: Switched on
- **WHEN** the user switches the AI connection on
- **THEN** a socket listens on 127.0.0.1 and `districts_mcp.json` holds its port and a new token

#### Scenario: Switched off
- **WHEN** the user switches the AI connection off
- **THEN** the socket is closed and `districts_mcp.json` no longer exists

#### Scenario: Default after start
- **WHEN** QGIS starts with the plugin loaded
- **THEN** no bridge socket listens

### Requirement: Token-checked requests
The bridge SHALL accept newline-delimited JSON requests `{id, token, tool, args}` and answer `{id, ok, result}` or `{id, ok: false, error}`. A request with a wrong or missing token SHALL be refused without running a tool. An exception in a tool SHALL become an error answer and SHALL NOT stop the bridge. No answer SHALL contain database credentials.

#### Scenario: Wrong token
- **WHEN** a request carries a token other than the one in `districts_mcp.json`
- **THEN** the answer is an error "invalid token" and no tool runs

#### Scenario: Failing tool
- **WHEN** a tool raises an exception
- **THEN** the answer is `ok: false` with the error text and the next request is served

### Requirement: Tool registry
All tools SHALL be registered in one list with name, description, JSON input schema and handler; the bridge SHALL answer the request `list_tools` from that list. No tool SHALL execute code passed by the client. Every tool of this change SHALL leave the project database, the project files and the QGIS project unchanged.

#### Scenario: Listing tools
- **WHEN** the client requests `list_tools`
- **THEN** it receives every registered tool with its description and input schema, and no tool for code execution

#### Scenario: Read only
- **WHEN** every tool is called once on a test version
- **THEN** the row counts and the files of the version are unchanged

### Requirement: Standard-library MCP server
`districts/mcp/server.py` SHALL import only the Python standard library and SHALL speak MCP (JSON-RPC 2.0 over stdio): `initialize` with version negotiation from its supported protocol versions, `notifications/initialized`, `ping`, `tools/list`, `tools/call`, `resources/list` and `resources/read`. It SHALL read `districts_mcp.json` at each connection to the bridge. When the file is missing or the bridge does not answer, `tools/call` SHALL return a result with `isError` and a hint to start QGIS and switch the AI connection on, `tools/list` SHALL return the tool snapshot shipped with the plugin (equal to the registry), and the server SHALL keep running. A map image SHALL be returned as image content (base64 PNG).

#### Scenario: Initialize
- **WHEN** a client sends `initialize` with a supported protocol version
- **THEN** the server answers with that version, its name and the capabilities tools and resources

#### Scenario: QGIS not running
- **WHEN** a client calls a tool and `districts_mcp.json` does not exist
- **THEN** the result has `isError` true with the hint, and a following `ping` is answered

#### Scenario: QGIS restarted
- **WHEN** QGIS restarts and the bridge is switched on again with a new port and token
- **THEN** the next tool call of the running server reaches the new bridge without a change to the client configuration

### Requirement: MCP configuration
The plugin SHALL offer "MCP configuration ...", a dialog with the paths of this computer: the command registering the server in Claude Code (`claude mcp add districts --scope user -- <python> <server.py> --state <state file>`) and the JSON entry for the Chat tab of Claude Desktop, each with a copy button, a button writing the entry into `.mcp.json` of a chosen folder for the Code tab of Claude Desktop and the VS Code extension (other entries of the file kept, an invalid file not overwritten), and whether the `claude` command is found (installed but not on the PATH: the command calls it with its full path; not installed: Claude Desktop needs no command, and how to install it). The command SHALL be the QGIS Python interpreter itself (`python.exe`), not the `python-qgis.bat` launcher, which MCP clients cannot reliably start.

#### Scenario: Configured command starts the server
- **WHEN** the configured command and arguments are started and receive `initialize`
- **THEN** the server answers with its name

#### Scenario: Claude Code not installed
- **WHEN** no `claude` command is installed
- **THEN** the dialog says that Claude Desktop (also its Code tab) and the VS Code extension do not need it, and names the installation command

#### Scenario: Installed but not on the PATH
- **WHEN** `claude.exe` is in `~/.local/bin` but not on the PATH
- **THEN** the command starts with `& "<full path>" mcp add districts`

#### Scenario: .mcp.json with another server
- **WHEN** the chosen folder has a `.mcp.json` with another server
- **THEN** the file afterwards has both servers, `districts` with the paths of this computer

### Requirement: Project permission
The bridge SHALL run a tool only when the project allows it (OpenSpec change ai-chat-panel, `public.ai_settings`): in a project that does not allow the AI assistant every tool except `search_help` and `read_help_page` SHALL answer with an error saying so, and in an allowed project a switched-off tool SHALL answer that it is switched off.

#### Scenario: Project not allowed
- **WHEN** an MCP client calls `run_checks` in a project whose AI assistant is not allowed
- **THEN** the answer is an error naming the project and the tab AI assistant, and no check runs
