# CLI Interface

## Goal of the document

This document describes Donna's command-line interface.

## Scope

CLI behavior; the following are out of scope:

- workflow operation semantics.
- Markdown parsing.
- configuration fields.
- internal session representation.
- exact skill prose.

The following concepts appear only to specify input/output boundaries:

- project roots.
- ids.
- workflows.
- action requests.
- sessions.

## General behavior

Donna deterministically runs agent workflows by:

- maintaining project-local sessions.
- discovering artifacts.
- executing operations.
- exchanging action requests and next-operation reports.

The root MUST expose a command group, with global options before the subcommand:
`donna [GLOBAL_OPTIONS] COMMAND [COMMAND_OPTIONS]`.
It MUST NOT directly start or continue workflows.

All cells, including journals/warnings/errors, MUST use stdout.
Once a protocol is selected, environment errors MUST follow the Command error handling contract in `specs/behavior/cli.md` in `llm-tool-cli`.
Automation cell/journal output MUST contain only JSON Lines.
Output MUST be deterministic, subject to generated-id rules below, for the same:

- input.
- configuration.
- cwd.
- project state.

Workspace commands MUST select configuration before command behavior.
Skill, init, and version MUST NOT require existing configuration.
Session commands MUST load workspace configuration and operate under the configured session directory.

## Commands

The following forms MUST be supported, with optional global options before the command:

- `init` — Starter configuration.
- `list` — Discover workflows.
- `render [OPTIONS] ARTIFACT` — Render an artifact.
- `validate [OPTIONS] [ARTIFACT...]` — Validate selected/all artifacts.
- `new-session` — Fresh session.
- `continue` — Advance queued work.
- `status` — Concise session status.
- `details` — Detailed session state.
- `run WORKFLOW` — Start a workflow.
- `complete-action-request ACTION_REQUEST_ID NEXT_OPERATION` — Complete a request and continue.
- `skill [DOCUMENT]` — Built-in documentation.
- `version` — Tool version.
- `--help` — Root help.

## Application identity

Human and LLM cell framing MUST use `DONNA`, including error cells produced during argument parsing.
The default configuration filename MUST be `donna.toml`.

## Output behavior

Donna output MUST follow the cell formatting and delivery contracts in `specs/behavior/protocol.md` in `llm-tool-cli`.
Environment errors MUST follow that specification's Environment-error cells contract.
Render MUST deliver Markdown as ordinary output after successful completion.
Help and argument-parsing diagnostics MAY use plain text.
Output MUST NOT contain color or styling escapes.

Commands MAY emit journals during execution, with console delivery only after successful journal processing under the output delivery contract.
Omitted actors MUST default to `agent` for LLM and the protocol name otherwise; explicit actors, including absence, MUST win.
Task attribution MUST identify the task being processed according to consistent session state; work-unit/operation ids MUST identify the current execution.
Uncommitted state changes MUST NOT change that attribution.
Session-load environment failure MUST preserve the event, actor, and execution context without creating a session, using no task id.
Absent task id MUST mean no active task or unavailable session context.
Expected output-delivery failures MUST be reported as command failures; unexpected failures MUST propagate.
Messages MUST:

- strip surrounding whitespace.
- preserve internal whitespace/newlines.
- escape line breaks for compact text.
- retain normalized values in automation.

## Output protocols

Donna MUST support the `human`, `llm`, and `automation` protocols defined in `specs/behavior/protocol.md` in `llm-tool-cli`.

### Human output

Human output SHOULD be compact terminal text.
Journals SHOULD include:

- time.
- task id when present.
- actor.
- message.

### LLM output

Agents invoking Donna as a tool MUST use `llm`.
Output SHOULD be stable/self-contained.
Journals SHOULD include:

- full timestamp.
- task.
- actor.
- work-unit.
- operation.
- message.

### Automation output

Serialization MUST follow that protocol specification's JSON Lines contract, with stable fields and one record per journal event.
Future fields MAY be added; consumers MUST ignore unknown fields.

## Donna cells

Cells MUST use the selected protocol's framing, metadata order, and serialization under `specs/behavior/protocol.md` in `llm-tool-cli`.
Ordinary cells MUST appear only after successful command completion; successfully processed journals MUST appear immediately, and warnings MUST appear last.
Failure MUST suppress pending ordinary results and emit errors before warnings.
The following cells MUST remain ordinary output and MUST NOT be forwarded as journal events:

- artifact-status cells.
- rendered-artifact cells.
- action-request cells.
- session-state cells.

Journaling MUST use explicit events.

Commands MAY emit multiple cells.
Consumers MUST NOT treat generated ids as deterministic.

### Human cell example

Human output SHOULD follow this shape:

```text
----- DONNA CELL <cell-id> -----
kind = session_state_status
media_type = text/markdown
pending_action_requests = 0
queued_work_units = 0
tasks = 0

The session is IDLE.

```

### LLM cell example

LLM output SHOULD follow this shape:

```text
--DONNA-CELL <cell-id> BEGIN--
kind=session_state_status
media_type=text/markdown
pending_action_requests=0
queued_work_units=0
tasks=0

The session is IDLE.
--DONNA-CELL <cell-id> END--
```

### Automation cell example

Automation output SHOULD follow this shape:

```json
{"content":"The session is IDLE.","id":"<cell-id>","pending_action_requests":0,"queued_work_units":0,"tasks":0}
```

## Global options

Global options MUST follow the configuration-option and protocol-option contracts in `specs/behavior/cli.md` in `llm-tool-cli`.
Each command's output MUST honor its effective protocol and selected project without inheriting another command's pending output.

### Help and completion

Help aliases and completion MUST follow the Application setup contract in `specs/behavior/cli.md` in `llm-tool-cli`.

### `-p`, `--protocol PROTOCOL`

Parsing, defaults, and invalid-value diagnostics MUST follow the Protocol option and Protocol selection contracts in `specs/behavior/cli.md` in `llm-tool-cli`.
Cells/journals MUST honor the selected protocol.

### `--config PATH`

Parsing MUST defer filesystem validation as specified by the Configuration option contract in `specs/behavior/cli.md` in `llm-tool-cli`.
Workspace commands MUST select configuration using the option; filename/schema/root rules are in `specs/behavior/config.md`.

## Artifact id arguments

Arguments MUST accept root-anchored ids and contained relative/absolute filesystem paths, normalized before use.
Workflow artifact arguments MUST end in `.donna.md`; loading existing artifacts MUST require visibility through configured workflow directories.
Section arguments MUST use `@/path/workflow.donna.md:section_id`, normalizing the artifact part and validating the local section id.

## `donna init` command

Init MUST follow the Initialization command contract in `specs/behavior/cli.md` in `llm-tool-cli` and create a valid version-1 starter described by Donna's `specs/behavior/config.md`.
Success MUST emit the contract's creation acknowledgement with the created configuration path.
Artifact/session/skill-document arguments MUST NOT be accepted.
**Example:** `donna --config /path/to/project/donna.toml init` selects an explicit target.

## `donna list` command

List MUST load configuration and emit one status cell per discovered artifact, ordered by configured directory then traversal order.
Overlapping directories MUST emit each id once; missing directories MUST be ignored.
Artifact/session arguments MUST NOT be accepted.

## `donna render` command

Render MUST accept one normalized artifact and required `--mode MODE`, supporting `view`, `execute`, and `analysis`.
It MUST emit one `rendered_artifact` cell with `text/markdown`, `type = rendered_artifact`, and rendered Markdown content to stdout under the selected protocol.
Rendering MAY emit activity journals before that cell.

## `donna validate` command

Validate MUST require exactly one of explicit artifact arguments or `--all`, rejecting their combination or absence.
Explicit inputs MUST each normalize/validate; `--all` MUST validate every discovered artifact.
Errors MUST follow the command error reporting and exit rules defined below.
Success MUST emit a success cell.

## `donna new-session` command

New-session MUST create fresh state and emit resulting session cells.

## `donna status` command

Status MUST report concise session state, including idle versus pending action requests.

## `donna details` command

Details MUST report detailed session state, including action requests when present.

## `donna continue` command

Continue MUST advance queued work until finish, failure, or an agent action request, and emit resulting cells.

## `donna run` command

Run MUST normalize/load `WORKFLOW` before starting it in the current session and execute until finish, failure, or an agent action request.

## `donna complete-action-request` command

The command MUST:

- validate the request id.
- normalize `NEXT_OPERATION` as an artifact-section id.
- complete the request.
- queue the selected operation.
- immediately continue until finish, failure, or another action request.

## `donna skill` command

The command MUST follow the Skill command contract in `specs/behavior/cli.md` in `llm-tool-cli` and offer:

- `usage`: commands.
- `configuration`: configuration.
- `initialization`: project initialization.
- `workflows`: authoring/execution.

Document content MUST follow Donna's `specs/behavior/skill_fixtures.md`.

## `donna version` command

The command MUST report the installed version of distribution `donna` under the Version command contract in `specs/behavior/cli.md` in `llm-tool-cli`.

## Errors and exit codes

Commands MUST follow the Command error handling and Exit statuses contracts in `specs/behavior/cli.md` in `llm-tool-cli`.
Argument parsing SHOULD retain the parsing-error behavior defined by that specification and MAY emit plain-text diagnostics before protocol selection.
The following failures SHOULD render error cells when possible:

- workspace failures.
- artifact failures.
- validation failures.
- environment failures.

All environment errors MUST use the Environment-error cells contract in `specs/behavior/protocol.md` in `llm-tool-cli`, with:

- `type = error`.
- native `code`.
- guidance.
- diagnostic metadata including null context.

Custom kinds, `error_code`, and introductory prefixes MUST NOT replace that contract.
Configuration diagnostics MUST propagate without local translation.
Donna errors, including artifact validation, MUST use the default environment-error exit status defined by the referenced CLI contract.

Reporting terminal errors MUST NOT load or create a Donna session, including after failed initialization.

## Compatibility rules

Compatibility SHOULD preserve:

- command names.
- options.
- protocols.
- artifact/section-id syntax.
- automation field meanings.

The following MAY be compatible additions:

- commands.
- options.
- metadata fields.
- skill documents.

Breaking changes MUST be specified before implementation.
