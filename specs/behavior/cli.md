# CLI Interface

## Goal of the document

This document describes how `donna` behaves as a command line interface, including:

- how agents, users, and tools invoke it.
- which commands and arguments are accepted.
- which output protocols are supported.
- what each command does at the CLI boundary.

## Scope

The scope of this specification is limited to CLI behavior.

The following topics are out of scope:

- workflow operation semantics.
- Markdown artifact parsing rules.
- configuration file field semantics.
- internal session state representation.
- exact prose emitted by built-in skill documents.

This specification may refer to the following concepts only to describe how the CLI accepts arguments and renders output:

- Donna project roots.
- Donna artifact ids.
- artifact section ids.
- workflow artifacts.
- action requests.
- session state.

## General behavior

`donna` is a command line tool that helps agents run predefined workflows in a deterministic way. It maintains project-local session state, discovers workflow artifacts, runs workflow operations, emits action requests for agents, and accepts agent reports about the next operation to run.

The CLI has four primary command areas:

- `donna run ...` — start a workflow artifact in the current session.
- `donna continue` and `donna complete-action-request ...` — advance existing session work.
- `donna list`, `donna render ...`, and `donna validate ...` — inspect and validate workflow artifacts.
- `donna skill [DOCUMENT]` — print built-in agent-oriented documentation.

The root command MUST be a command group constructed through the application setup managed by `llm_tool_cli`.

Global options, when present, MUST be provided before the subcommand:

```bash
donna [GLOBAL_OPTIONS] COMMAND [COMMAND_OPTIONS]
```

The CLI MUST write all cells, including results, journal events, warnings, and environment errors, to stdout in every protocol.

Environment-error diagnostics MUST use the command error handling managed by `llm_tool_cli` when the selected protocol has already been installed.

For `automation` output, stdout MUST contain only JSON Lines records when command output is produced through Donna cells or journal records.

The CLI MUST produce deterministic output for the same:

- input.
- configuration.
- working directory.
- project state.

Commands that load a workspace MUST discover or use a Donna configuration file before executing command-specific behavior.

`donna skill ...`, `donna init`, and `donna version` MUST NOT require an existing Donna project configuration.

## Commands

The CLI MUST support these commands and command forms:

- `donna [GLOBAL_OPTIONS] init` — create a starter `donna.toml`.
- `donna [GLOBAL_OPTIONS] list` — list discovered workflow artifacts.
- `donna [GLOBAL_OPTIONS] render [OPTIONS] ARTIFACT` — render one artifact.
- `donna [GLOBAL_OPTIONS] validate [OPTIONS] [ARTIFACT...]` — validate selected artifacts or every discovered artifact.
- `donna [GLOBAL_OPTIONS] new-session` — create fresh session state.
- `donna [GLOBAL_OPTIONS] continue` — continue queued workflow execution in the current session.
- `donna [GLOBAL_OPTIONS] status` — show concise session status.
- `donna [GLOBAL_OPTIONS] details` — show detailed session state.
- `donna [GLOBAL_OPTIONS] run WORKFLOW` — start a workflow artifact in the current session.
- `donna [GLOBAL_OPTIONS] complete-action-request ACTION_REQUEST_ID NEXT_OPERATION` — complete an action request and continue with the selected operation.
- `donna [GLOBAL_OPTIONS] skill [DOCUMENT]` — print built-in agent-oriented documentation for using `donna`.
- `donna [GLOBAL_OPTIONS] version` — print the tool version.
- `donna --help` — print root help information.

The root command MUST NOT start or continue workflow execution directly.

## Application identity

The CLI MUST initialize static settings with the tool label `DONNA` and default configuration filename `donna.toml` through `llm_tool_cli` at application startup before command-line parsing.
Label storage, initialization checks, and label selection for cell rendering MUST be managed by `llm_tool_cli`.

## Output behavior

The CLI MUST submit cells directly to the active emitter in `llm_tool_cli.output`, which owns batch rendering and text writing.

Command output produced through Donna's protocol layer MUST be represented as Donna cells.

All environment errors MUST use the typed environment-error logic cell and ordinary output cells provided by `llm_tool_cli`.

The `render` command MUST deliver rendered Markdown in an ordinary cell through shared buffered output.

Help and command line parsing output MAY use Typer's standard rendering.

Commands MAY emit Donna journal cells while executing.
Their console output MUST follow successful shared journal processing.
An omitted journal actor MUST default to `agent` in the LLM protocol and the protocol name otherwise.
Journal task context MUST always use the cached consistent session's current task, including an absent task; callers MUST NOT override it from mutable state or other objects.
Journal work-unit and operation identifiers MUST always use the active execution context, including absent identifiers; callers MUST NOT override them.
An explicit actor, including an absent actor, MUST take precedence over the default actor.
When loading cached session context returns an environment failure, journaling MUST continue with an absent task identifier, preserving actor and execution context without creating a session.
An absent journal task identifier MUST mean no task attribution is available, either because no task is active or because session context could not be loaded.
Shared emitter failures MUST remain failed results for the caller to handle; unexpected failures MUST propagate.
Multiline messages MUST use shared logical-cell normalization, stripping surrounding whitespace while retaining internal line breaks. Compact text MUST escape those line breaks; automation records MUST retain the normalized cell values.

Output MUST NOT contain terminal color or styling escape sequences.

## Output protocols

The CLI MUST support the output modes defined by `llm_tool_cli.protocol`.

Donna interprets these modes as follows:

- `human` — text protocol for terminal users.
- `llm` — text protocol optimized for coding agents that invoke `donna` as a tool.
- `automation` — protocol optimized for programs; output is serialized as JSON Lines.

### Human output

Human output SHOULD be compact terminal text.

Human journal output SHOULD include the time, current task id when present, actor id, and message.

### LLM output

The `llm` protocol MUST be used when a coding agent invokes `donna` as a tool.

LLM output SHOULD be stable and self-contained for coding agents that receive the output as a tool result.

LLM journal output SHOULD include the full timestamp, current task id, actor id, current work unit id, current operation id, and message.

### Automation output

Automation JSON Lines serialization MUST be provided by `llm_tool_cli.protocol`.

Automation output MUST use stable field names.

Each journal record MUST produce one automation record.

Additional fields MAY be added in future versions. Consumers MUST ignore unknown fields.

## Donna cells

A Donna cell is the protocol-level output unit used by most CLI commands.

Donna MUST use the cell model, construction helpers, and cell formatting provided by `llm_tool_cli`.
Donna MUST construct protocol-independent logic cells; the shared emitter MUST select the active protocol when rendering each emitted sequence.
The library owns logic-cell protocol dispatch, cell layouts, sequence rendering contexts, metadata ordering, and automation cell records.

Donna owns the projection of its results and journal context into cells.
Shared output delivery MUST buffer ordinary results, emit successfully processed journal cells immediately, and place collected warnings last.
On command failure, buffered ordinary results MUST be discarded; error diagnostics MUST precede collected warnings.

Artifact-status, rendered-artifact, action-request, and session-state cells MUST reject construction with journal delivery enabled.
They MUST remain ordinary buffered output; operation journaling MUST use separate explicit journal events.

Consumers MUST NOT treat generated cell ids as deterministic identifiers.

Commands MAY emit multiple cells for one invocation.

### Human cell example

Human protocol cell output SHOULD follow this shape:

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

LLM protocol cell output SHOULD follow this shape:

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

Automation protocol cell output SHOULD follow this shape:

```json
{"content":"The session is IDLE.","id":"<cell-id>","pending_action_requests":0,"queued_work_units":0,"tasks":0}
```

## Global options

The CLI MUST use global-option registration and parsing, context-scoped runtime configuration, command-context protocol selection and output scope setup, and shared emitter delivery managed by `llm_tool_cli`.
Donna MUST register its commands on the application provided by `llm_tool_cli`.
Application-specific runtime setup, journal-cell construction, and runtime cleanup MUST remain Donna-owned; project loading and output delivery MUST be shared.
Workspace commands MUST compose the shared command execution scope with Donna's runtime setup and journal-cell factory.
Commands without Donna runtime requirements MUST use shared command setup directly.
The effective protocol MUST be read from shared runtime configuration; the active config path and derived project directory MUST be read from independent shared project configuration.
These configurations and the static application identity MUST be immutable and complete when bound.
Donna MUST NOT retain separate protocol or workspace-path globals.

### Help and completion

The CLI MUST use help aliases and shell completion options managed by `llm_tool_cli`.

### `-p`, `--protocol PROTOCOL`

The CLI MUST use protocol-option parsing and invalid-value diagnostics managed by `llm_tool_cli`.

Subcommands that render Donna cells or journal records MUST use the selected protocol.

### `--config PATH`

The CLI MUST use the configuration-option parsing managed by `llm_tool_cli`, including its deferred filesystem validation.

Workspace-loading commands MUST pass this option to the configuration selection managed by `llm_tool_cli`.
Donna's configuration filename, schema, and project-root rules are defined in `specs/behavior/config.md`.

## Artifact id arguments

CLI arguments that identify Donna artifacts MUST be accepted as:

- root-anchored artifact ids.
- relative filesystem paths that resolve inside the Donna project root.
- absolute filesystem paths that resolve inside the Donna project root.

Accepted artifact arguments MUST normalize to canonical root-anchored artifact ids before command-specific behavior uses them.

Artifact arguments used by workflow artifact commands MUST identify files with the Donna artifact extension:

```text
.donna.md
```

Artifact arguments that load existing workflow artifacts MUST identify artifacts visible through configured workflow directories.

Artifact section arguments MUST use artifact section id syntax:

```text
@/path/to/workflow.donna.md:section_id
```

Artifact section arguments MUST normalize the artifact part as an artifact id and validate the section id part as a Donna section id.

## `donna init` command

The `init` command MUST create a starter Donna configuration file.

```bash
donna init
donna --config /path/to/project/donna.toml init
```

The application MUST register the initialization command managed by `llm_tool_cli`, supplying Donna's schema, packaged starter location, and initialization help text.
The library owns command setup, invocation working directory and optional `--config` handling, target selection and resolution, template reading, exclusive creation, subsequent loading and validation, project scope management, success output, and diagnostics; the default filename MUST come from static settings.
Donna owns the starter contents and schema described in `specs/behavior/config.md`.

The generated configuration MUST be valid TOML and use schema version `1`.

After project initialization succeeds, the command MUST emit the configuration-creation success cell managed by `llm_tool_cli` within the shared project scope, supplying the active configuration path from its settings.

The command MUST NOT accept artifact arguments, session arguments, or skill document arguments.

## `donna list` command

The `list` command MUST list workflow artifacts discovered under configured workflow directories.

```bash
donna list
```

The command MUST load workspace configuration.

The command MUST render one status cell per discovered artifact.

Discovered artifacts MUST be ordered deterministically by configured workflow directory order and filesystem traversal order.

Duplicate artifact ids discovered through multiple workflow directories MUST be emitted once.

Missing workflow directories MUST be ignored.

The command MUST NOT accept artifact arguments or session arguments.

## `donna render` command

The `render` command MUST render one artifact with the selected render mode and write rendered Markdown to stdout.

```bash
donna render --mode MODE ARTIFACT
```

`ARTIFACT` MUST be an artifact id or path accepted by Donna artifact id normalization.

The `--mode MODE` option MUST be required.

Allowed render modes MUST include:

- `view`
- `execute`
- `analysis`

The rendered artifact output MUST be one ordinary cell of kind `rendered_artifact`, with media type `text/markdown`, `type = rendered_artifact` metadata, and the rendered Markdown as content.
It MUST honor the selected output protocol, including JSON Lines serialization for automation.

This command MAY emit Donna journal cells before the rendered artifact cell when artifact rendering logs command activity.

## `donna validate` command

The `validate` command MUST validate selected workflow artifacts or every discovered workflow artifact.

```bash
donna validate ARTIFACT...
donna validate --all
```

The command MUST require exactly one of:

- one or more artifact arguments.
- `--all`.

The command MUST fail when `--all` is used together with one or more artifact arguments.

When artifact arguments are provided, the command MUST normalize and validate each artifact id.

When `--all` is provided, the command MUST validate every discovered workflow artifact.

If validation finds errors, the command MUST render error cells.
Collected validation errors MUST pass through the command context's error handling, including its journal policy, before shared reporting and termination.

If validation succeeds, the command MUST render a success cell.

## `donna new-session` command

The `new-session` command MUST create fresh session state.

```bash
donna new-session
```

The command MUST load workspace configuration.

The command MUST operate on the session stored under the configured session directory.

The command MUST render resulting session cells.

## `donna status` command

The `status` command MUST show concise session status.

```bash
donna status
```

The command MUST load workspace configuration.

The command MUST operate on the session stored under the configured session directory.

The output MUST include whether Donna is idle or has pending action requests.

## `donna details` command

The `details` command MUST show detailed session state.

```bash
donna details
```

The command MUST load workspace configuration.

The command MUST operate on the session stored under the configured session directory.

The output MUST include action requests when they are present in the session state.

## `donna continue` command

The `continue` command MUST continue queued workflow execution.

```bash
donna continue
```

The command MUST load workspace configuration.

The command MUST operate on the session stored under the configured session directory.

The command MUST advance queued workflow execution until the workflow finishes, workflow execution fails, or Donna emits an action request for the agent.

The command MUST emit resulting cells.

## `donna run` command

The `run` command MUST start a workflow artifact in the current session.

```bash
donna run WORKFLOW
```

The command MUST load workspace configuration.

The command MUST operate on the session stored under the configured session directory.

The command MUST normalize `WORKFLOW` as an artifact id.

The command MUST load the workflow artifact before starting it.

The command MUST execute the started workflow until the workflow finishes, workflow execution fails, or Donna emits an action request for the agent.

## `donna complete-action-request` command

The `complete-action-request` command MUST complete an action request and continue workflow execution.

```bash
donna complete-action-request ACTION_REQUEST_ID NEXT_OPERATION
```

The command MUST load workspace configuration.

The command MUST operate on the session stored under the configured session directory.

The command MUST:

- validate the action request id format.
- normalize `NEXT_OPERATION` as an artifact section id.
- mark the action request as completed.
- queue the selected next operation.
- continue workflow execution immediately.

After the selected next operation is queued, the command MUST advance workflow execution until the workflow finishes, workflow execution fails, or Donna emits an action request for the agent.

## `donna skill` command

The CLI MUST register the skill command managed by `llm_tool_cli`, supplying the `donna.skills` resource package and Donna's document definitions.
The library owns argument selection and validation, defaults, help and completion, configuration independence, cell output, and failure delivery and exit statuses.

Donna MUST provide these documents:

- `usage` — general command usage documentation.
- `configuration` — configuration documentation.
- `initialization` — project initialization documentation.
- `workflows` — workflow authoring and execution documentation.

## `donna version` command

The CLI MUST register the version command managed by `llm_tool_cli`, supplying the distribution name `donna`.
The library owns installed version lookup, help, configuration independence, protocol selection, version-cell output, and exit and failure behavior.

## Errors and exit codes

Skill-, version-, and initialization-command failure handling MUST be managed by `llm_tool_cli`.
The remaining execution policies apply to tool-owned commands.

Typer command line parsing errors SHOULD use Typer's standard invalid-arguments behavior.

Workspace, artifact, validation, and environment errors SHOULD be rendered as Donna error cells when possible.

Donna-owned and shared environment-error values MUST use the common error-cell contract provided by `llm_tool_cli`, including corrective guidance and native diagnostic context.
This replaces Donna's custom error-cell kinds and `error_code` field with the shared `error` kind, `type = error`, and `code` metadata.
Custom introductory prefixes MUST be removed; artifact, section, and configuration context MUST remain available through shared metadata conversion, including optional null fields.

The CLI MUST use command error handling and explicit error reporting managed by `llm_tool_cli`, including error cells on stdout, diagnostic ordering, exit statuses, and exception propagation.
Donna MUST retain application-specific runtime setup and runtime context cleanup.
Terminal error journaling MUST be managed by the shared library through error cells, without separate console journal lines or calls to Donna's journal-cell factory.
Those journal records MUST NOT load Donna session state or require task, work-unit, or operation attribution.
Donna runtime resources MUST retain their existing execution scope rather than remaining active for shared error reporting.

Configuration selection, loading, and creation MUST propagate the diagnostics provided by `llm_tool_cli` without local translation.

Donna-owned environment errors MUST use the shared default environment-error exit status, including artifact validation failures.

If command line parsing fails before Donna installs an output protocol, diagnostics MAY be written by Typer using its standard behavior.

## Compatibility rules

The CLI SHOULD preserve backward compatibility for:

- command names.
- option names.
- output protocol names.
- artifact id syntax.
- artifact section id syntax.
- automation JSONL field meanings.

Backward-compatible additions MAY include:

- new commands.
- new options.
- new output cell metadata fields.
- new skill documents.

Backward-incompatible changes MUST be documented in this specification before implementation.
