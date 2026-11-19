## ADDED Requirements

### Requirement: Tab AI assistant
The main dialog SHALL have a seventh tab "AI assistant", detachable like the other tabs, with a status line (SDK version, key source, project allowed, model), model and effort selectors remembered per user, the conversation, an input with Send and Stop, "New conversation", "Export" and a cost line. The conversation SHALL survive closing and reopening the main dialog within the QGIS session.

#### Scenario: Reopened dialog
- **WHEN** the user closes the main dialog during a conversation and opens it again
- **THEN** the conversation is still shown and can be continued

### Requirement: Conversation with tools
A question SHALL be sent with the allowed tools of the registry and the loaded project and version; the chat SHALL run each requested tool in the QGIS main thread, show it with its arguments and a collapsible result, return all results of one assistant turn in one message (failures with `is_error`), and continue until the answer ends. Assistant text SHALL appear while it is generated. Stop SHALL end the conversation step after the current request.

#### Scenario: Question with two tool calls
- **WHEN** the scripted model asks for `run_checks` and then `result_series` before answering
- **THEN** the chat shows both tool lines with their arguments and the answer, and the second request contains both results

#### Scenario: Failing tool
- **WHEN** a tool raises "no version loaded"
- **THEN** the model receives a tool result with `is_error` true and that text, and the conversation continues

### Requirement: Model, effort and refusals
The default model SHALL be Claude Opus 5.5 with effort `medium`; Sonnet 5.5 and Haiku 5.5 and the efforts low, medium and high SHALL be selectable. Requests SHALL use the server-side refusal fallback (`fallbacks` default). A refusal that remains SHALL be shown with its category and end the turn; `max_tokens` SHALL end the turn with a note; `pause_turn` SHALL be resent. Changing the model during a conversation SHALL ask and start a new conversation.

#### Scenario: Refusal
- **WHEN** the final message has `stop_reason` refusal with a category
- **THEN** the chat shows the category and sends no further request for that question

### Requirement: Costs and limit
The chat SHALL estimate the cost of each step from its token usage (input, cache write, cache read, output) and the price table of the served model, show the cost of the answer and of the session marked as an estimate, and before each request above the session limit (default 2 USD) SHALL wait for "Continue" (which raises the limit by the same amount) or "Stop".

#### Scenario: Limit reached
- **WHEN** the session cost reaches 2.05 USD with the limit 2 USD and the model asks for another tool
- **THEN** no request is sent until the user chooses Continue, and Stop ends the turn

#### Scenario: Cost of a step
- **WHEN** an Opus 5.5 step uses 10 000 input, 50 000 cache-read and 1 000 output tokens
- **THEN** its cost is 10 000 × 4 + 50 000 × cache-read price + 1 000 × 20 per million tokens

### Requirement: Export
"Export" SHALL write the conversation as one HTML file (questions, answers, tool calls with arguments, results collapsed, model, costs, date) into the version folder or a chosen path; nothing SHALL be written without it.

#### Scenario: Export
- **WHEN** the user exports a conversation with one tool call
- **THEN** the HTML file contains the question, the answer, the tool name with its arguments and the result in a collapsed section, and no API key
