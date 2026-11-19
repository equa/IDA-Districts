## ADDED Requirements

### Requirement: SDK installed on demand
The tab "AI assistant" SHALL show the chat only when the `anthropic` package can be imported, and otherwise a button "Install AI support" that runs `pip install --user --upgrade anthropic` with the QGIS Python without blocking QGIS and shows pip's output. The rest of the plugin and the MCP connection SHALL work without the package. The installed SDK version SHALL be shown in the tab.

#### Scenario: SDK missing
- **WHEN** the tab opens and `anthropic` cannot be imported
- **THEN** the tab shows the install button with the command it runs, and no chat input

#### Scenario: Install fails
- **WHEN** pip ends with an error
- **THEN** the tab shows pip's output and the command to run by hand

### Requirement: API key and its source
The plugin settings SHALL have a field for the Anthropic API key, stored in the QGIS authentication database with only its `auth_id` in the settings. The chat SHALL use that key when set, else the SDK's own credential sources, and SHALL show which source is in use; the key SHALL never be logged, shown or exported. Without any key, the tab SHALL say where to enter one and that the API is billed separately from a Claude subscription.

#### Scenario: Key from the settings
- **WHEN** a key is stored in the settings
- **THEN** the client is created with it and the status line says "QGIS settings"

#### Scenario: Rejected key
- **WHEN** the API answers with an authentication error
- **THEN** the chat shows the error naming the key source, and nothing else is retried

### Requirement: Per-project permission
A project SHALL allow the AI assistant only when its table `public.ai_settings` has `allowed` true; old projects SHALL get the table with `allowed` false at the next version load. Allowing SHALL need a confirmation that names the data sent to Anthropic and lets tools be switched off (`disabled_tools`). The chat SHALL offer only the allowed tools and answer a call to another tool with "not allowed in this project"; the MCP bridge SHALL refuse every tool except `search_help` and `read_help_page` in a project that is not allowed, and the switched-off tools in an allowed one.

#### Scenario: New or old project
- **WHEN** a version of a project without the table is loaded
- **THEN** the table exists afterwards with `allowed` false and the tab shows "AI assistant not allowed in this project"

#### Scenario: Map image switched off
- **WHEN** a project allows the assistant with `render_map` switched off
- **THEN** the tool list of the request has no `render_map`, and the MCP bridge refuses `render_map` in this project

#### Scenario: Same decision for colleagues
- **WHEN** one user allows the assistant in a project
- **THEN** another user of the same project database sees it allowed, with the same switched-off tools
