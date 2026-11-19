## ADDED Requirements

### Requirement: Workflow map
`districts/mcp/wiki_map.json` SHALL list the workflow steps in order, each with an id, a title, its wiki pages (full page names in the XWiki space `IDA_Districts`) or `missing`, its check rule ids and the condition under which it is done. Every rule id in the map SHALL exist in the check rules. The steps SHALL be offered as MCP resources.

#### Scenario: Rules exist
- **WHEN** the map is loaded in a test
- **THEN** every rule id it names is a registered check rule

#### Scenario: Page exists (online)
- **WHEN** the online test reads every page of the map that is not marked `missing`
- **THEN** the wiki answers each with the page

### Requirement: Workflow state
`workflow_state(version)` SHALL return per step `done`, `missing` or `stale` with a reason from the database and the project files, where `stale` means the topology no longer matches the lines, for the topology and for loaded results.

#### Scenario: New version
- **WHEN** a version has streets and buildings but no lines
- **THEN** the import steps are `done` and pipe laying is `missing`

#### Scenario: Results out of date
- **WHEN** a line was moved after the topology was generated and the results were loaded
- **THEN** the results step is `stale` with that reason

### Requirement: Help from the wiki
`search_help(query)` SHALL search the XWiki space `IDA_Districts` through its public REST API and return titles, page names and URLs; `read_help_page(page)` SHALL return the title, URL and content of a page. Pages SHALL be cached for the session. Without network access the tools SHALL return an error saying the wiki is unreachable, and all other tools SHALL work. For a step marked `missing`, the guidance SHALL say that no wiki page exists yet.

#### Scenario: Offline
- **WHEN** the wiki cannot be reached
- **THEN** `search_help` returns the error "wiki unreachable" and `run_checks` still returns findings

#### Scenario: Missing page
- **WHEN** the guidance is asked for the step cost optimization, marked `missing`
- **THEN** the answer says that the wiki has no page for it yet and names its rules
