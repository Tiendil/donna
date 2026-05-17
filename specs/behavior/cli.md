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

The root command MUST be a command group.

Global options, when present, MUST be provided before the subcommand:

```bash
donna [GLOBAL_OPTIONS] COMMAND [COMMAND_OPTIONS]
```

The CLI MUST write requested command output to stdout.

Diagnostics that are not part of the requested output SHOULD be represented as Donna error cells when the selected protocol has already been installed.

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

## Output behavior

All output MUST use UTF-8.

Command output produced through Donna's protocol layer MUST be represented as Donna cells.

The `render` command MUST write rendered Markdown directly.

The `version` command MUST print a plain version line.

Help and command line parsing output MAY use Typer's standard rendering.

Commands MAY emit Donna journal records while executing. Journal records are command output when they are printed by the selected protocol formatter.

Output MUST NOT contain terminal color or styling escape sequences.

## Output protocols

The CLI MUST support three output protocols:

- `human` — default protocol for terminal users.
- `llm` — text protocol optimized for coding agents that invoke `donna` as a tool.
- `automation` — protocol optimized for programs; output is serialized as JSON Lines.

`human` and `llm` MUST be separate protocols.

For commands that support output protocols, the output protocol MUST be selected with the global option:

```bash
--protocol PROTOCOL
-p PROTOCOL
```

Allowed values MUST be:

- `human`
- `llm`
- `automation`

If no protocol is provided, the default protocol MUST be `human`.

### Human output

Human output SHOULD be compact terminal text.

Human cell output MUST include a visible cell boundary header with the generated cell id.

Human cell output MUST render cell metadata as `key = value` lines.

Human journal output SHOULD include the time, current task id when present, actor id, and message.

### LLM output

The `llm` protocol MUST be used when a coding agent invokes `donna` as a tool.

LLM cell output MUST use explicit machine-readable boundary lines:

```text
--DONNA-CELL <id> BEGIN--
--DONNA-CELL <id> END--
```

LLM cell output MUST render cell metadata as `key=value` lines.

LLM output SHOULD be stable and self-contained for coding agents that receive the output as a tool result.

LLM journal output SHOULD include the full timestamp, current task id, actor id, current work unit id, current operation id, and message.

### Automation output

Automation output MUST be serialized as JSON Lines.

Automation output MUST write one JSON object per line.

Automation output MUST use stable field names.

Automation cell output MUST include:

```json
{"id":"generated cell id","content":"cell content or null"}
```

Automation cell output MUST include cell metadata as top-level JSON object fields.

Automation output MUST sort JSON object keys.

Automation journal output MUST serialize the journal record as one JSON object per line.

Additional fields MAY be added in future versions. Consumers MUST ignore unknown fields.

## Donna cells

A Donna cell is the protocol-level output unit used by most CLI commands.

Each Donna cell MUST have:

- a generated `id`.
- a `kind`.
- optional `media_type`.
- optional `content`.
- metadata fields.

Cell ids MAY be generated at runtime. Consumers MUST NOT treat generated cell ids as deterministic identifiers.

Cell metadata fields MUST be rendered in deterministic order by metadata key when the selected formatter emits ordered metadata.

Cell content MUST have a media type when content is present.

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

### `-h`, `--help`

`-h` and `--help` MUST print help information and exit with status `0`.

Example:

```bash
donna --help
```

### `-p`, `--protocol PROTOCOL`

`-p` and `--protocol PROTOCOL` MUST be global options accepted before the subcommand.

The selected protocol MUST be available to every subcommand.

Subcommands that render Donna cells or journal records MUST use the selected protocol.

Allowed values MUST be:

- `human`
- `llm`
- `automation`

### `--config PATH`

`--config PATH` MUST be a global option accepted before the subcommand.

The config path MUST identify a local TOML configuration file for commands that load a workspace.

When provided to a command that loads a workspace, `PATH` MUST be used as the active Donna configuration file and Donna MUST NOT perform upward discovery.

When `PATH` is relative, it MUST be resolved relative to the current working directory.

The project root MUST be the directory containing the active configuration file.

When omitted, commands that load a workspace MUST discover `donna.toml` by searching from the current working directory toward the filesystem root.

Subcommands that do not load workspace configuration MAY use `PATH` to derive their target directory or target configuration file.

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

When no `--config` path is provided, the command MUST create `donna.toml` in the current working directory.

When `--config PATH` is provided, the command MUST create the configuration file at that path and use the directory containing the file as the project root.

When `--config PATH` is provided, the directory containing `PATH` MUST exist.

The command MUST NOT discover an existing configuration file in parent directories.

The command MUST NOT overwrite an existing configuration file.

The generated configuration MUST be valid TOML and use schema version `1`.

The command MUST render a success cell when initialization succeeds.

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

The rendered artifact output MUST be written as raw Markdown rather than wrapped in a Donna cell.

This command MAY still emit Donna journal records before the rendered Markdown when artifact rendering logs command activity.

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

The `skill` command MUST print built-in documentation for coding agents.

```bash
donna skill
donna skill usage
donna skill configuration
donna skill initialization
donna skill workflows
```

The command output SHOULD be suitable for coding agents that receive the output as a tool result.

The command MUST NOT load workspace configuration.

The `skill` command MUST accept an optional document argument.

Allowed document argument values MUST be:

- `usage` — print general command usage documentation.
- `configuration` — print configuration documentation.
- `initialization` — print initialization documentation.
- `workflows` — print workflow authoring and execution documentation.

When no document argument is provided, `donna skill` MUST behave like `donna skill usage`.

Unknown document argument values MUST fail as invalid command line arguments.

## `donna version` command

The `version` command MUST print the installed Donna package version and exit with status `0`.

Version output MUST be a single line containing only the version number.

```bash
donna version
```

The `version` command MUST NOT load workspace configuration.

The `version` command MAY ignore global options that do not affect version output.

## Help Examples

### Help

Command:

```bash
donna --help
```

Help output SHOULD be autogenerated from:

- command definitions.
- argument definitions.
- option definitions.

## Errors and exit codes

Typer command line parsing errors SHOULD use Typer's standard invalid-arguments behavior.

Workspace, artifact, validation, and environment errors SHOULD be rendered as Donna error cells when possible.

Environment errors rendered through Donna error cells currently exit with status `0`.

Human and LLM error cells SHOULD be written to stdout like other Donna cells.

For automation output, rendered fatal errors SHOULD be written to stdout as JSON Lines cell records when possible.

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
