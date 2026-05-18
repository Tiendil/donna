# Configuration

## Goal of the document

This document describes the behavior and semantics of the `donna.toml` configuration file, including:

- where it is found.
- how it is interpreted.
- how session storage is configured.
- how workflow artifact discovery is configured.
- how Markdown section defaults and journal forwarding are configured.

## Scope

The scope of this specification is limited to configuration file behavior.

The following topics are out of scope:

- CLI invocation details.
- output protocol formatting.
- workflow operation semantics.
- Markdown artifact source format.
- internal session state schema.
- project module ownership.

This specification defines configuration semantics that the implementation MUST honor, but it does not require any particular implementation strategy.

## Dictionary

- `configuration file` — a TOML file named `donna.toml` that configures one Donna project.
- `project root` — the directory that contains the active configuration file.
- `session directory` — the project directory where Donna stores runtime session state and session-created artifacts.
- `workflow directory` — a project directory recursively scanned for Donna workflow artifacts.
- `section default` — a fallback Markdown section configuration value used when an artifact section omits the value.
- `journal command` — an optional external command invoked for Donna journal records.

## Configuration file discovery

The canonical configuration file name MUST be `donna.toml`.

When a workspace-loading command is invoked without `--config`, `donna` MUST discover the configuration file by searching from the current working directory toward the filesystem root.

Discovery MUST stop at the first directory that contains `donna.toml`.

The directory containing the discovered file MUST be the project root.

When `--config PATH` is provided to a workspace-loading command, `donna` MUST use that file as the configuration file and MUST NOT perform upward discovery.

If `PATH` is relative, it MUST be resolved relative to the current working directory.

When `--config PATH` is provided, the directory containing the resolved file MUST be the project root.

When `--config PATH` is provided to a workspace-loading command, the resolved file MUST exist.

If no configuration file can be found or the configured path cannot be loaded, workspace loading MUST fail.

Configuration loading MUST be deterministic for the same:

- configuration file content.
- current working directory.
- filesystem state.

## TOML structure

The configuration file MUST be valid TOML.

The top-level configuration MAY contain these fields:

- `version` — configuration schema version.
- `session_dir` — path to Donna runtime session storage.
- `workflow_dirs` — list of directories scanned for workflow artifacts.
- `defaults` — fallback configuration for Markdown artifact sections.
- `journal` — optional external journal forwarding configuration.

Unknown top-level fields MUST cause configuration loading to fail.

The initial schema version MUST be `1`.

If `version` is omitted, `donna` MUST treat the configuration as schema version `1`.

If `version` is present, it MUST be an integer.

If `version` is not supported, configuration loading MUST fail.

Minimal example:

```toml
version = 1
```

Starter example:

```toml
version = 1

session_dir = ".session/donna"

workflow_dirs = [
    "./workflows",
    "./.session/donna",
]
```

## Session directory

The `session_dir` field MAY be omitted.

If omitted, `session_dir` MUST default to:

```toml
session_dir = ".session/donna"
```

The `session_dir` field MUST be a project-relative path.

The `session_dir` field MUST NOT be an absolute host filesystem path.

The `session_dir` field MUST NOT contain parent-directory references.

The path MUST be resolved from the Donna project root.

Donna commands that use session state MUST store runtime state under this directory.

Session directories MAY be created lazily by runtime commands.

## Workflow directories

The `workflow_dirs` field MAY be omitted.

If omitted, `workflow_dirs` MUST default to:

```toml
workflow_dirs = [
    "./workflows",
    "./.session/donna",
]
```

If present, `workflow_dirs` MUST be a list of project-relative paths.

Each workflow directory MUST NOT be an absolute host filesystem path.

Each workflow directory MUST NOT contain parent-directory references.

Duplicate workflow directory entries MUST be removed while preserving the first occurrence.

Workflow directory paths MUST be resolved from the Donna project root.

Missing workflow directories MUST be ignored during artifact discovery.

Donna MUST recursively scan workflow directories for files ending with `.donna.md`.

Donna MUST ignore files without the `.donna.md` suffix when discovering workflow artifacts.

Artifact discovery MUST be deterministic for the same `workflow_dirs` order and filesystem state.

## Defaults

The `defaults` field MAY be omitted.

If present, `defaults` MUST be a TOML table.

The `defaults` table MAY contain these fields:

- `tail_section_kind` — default primitive path for H2 sections.
- `primary_section_kind` — default primitive path for the H1 section.
- `primary_section_id` — default id for the H1 section.

Unknown `defaults` fields MUST cause configuration loading to fail.

If omitted, the effective defaults MUST be:

```toml
[defaults]
tail_section_kind = "donna.lib.text"
primary_section_kind = "donna.lib.workflow"
primary_section_id = "primary"
```

Default primitive paths MUST be valid Python-path-like Donna primitive identifiers.

`primary_section_id` MUST be a valid Donna section id.

Explicit section config in a Markdown artifact MUST override configuration defaults.

Projects SHOULD NOT change section defaults unless they intentionally use custom Donna primitives or a different artifact convention.

## Journal

The `journal` field MAY be omitted.

If present, `journal` MUST be a TOML table.

The `journal` table MAY contain:

- `cmd` — optional command argument list used to forward Donna journal records to an external command.

Unknown `journal` fields MUST cause configuration loading to fail.

If `journal.cmd` is omitted or `None`, Donna MUST NOT execute an external journal command.

If present, `journal.cmd` MUST be a non-empty list of command arguments.

Each argument MUST be a string.

Donna MUST execute the configured journal command once per journal record.

Donna MUST execute the command directly as an argument list, not through a shell.

Donna MUST treat a journal command execution failure as an environment error.

### Journal placeholders

Donna MUST recognize placeholders only when the whole command argument starts with `{` and ends with `}`.

The supported placeholders MUST be:

- `{timestamp}` — record creation time formatted as ISO-8601.
- `{actor_id}` — actor that created the record, or an empty string.
- `{message}` — journal message.
- `{current_task_id}` — current task id, or an empty string.
- `{current_work_unit_id}` — current work unit id, or an empty string.
- `{current_operation_id}` — current operation artifact section id, or an empty string.

Unsupported placeholder names MUST cause configuration loading or journal command argument construction to fail.

Arguments that contain placeholder-like text as only part of the value MUST be treated as literal arguments.

For example, `{message}` is a placeholder, but `message:{message}` is a literal argument.

Example:

```toml
[journal]
cmd = [
    "./bin/journal-tool.sh",
    "record",
    "{timestamp}",
    "{actor_id}",
    "{current_task_id}",
    "{current_operation_id}",
    "{message}",
]
```

Donna MUST still print newly created journal records through the selected output protocol when `journal.cmd` is omitted.

## Starter configuration

The `donna init` command MUST create a starter configuration based on the packaged base config fixture.

The starter configuration MUST:

- use schema version `1`.
- set `session_dir` to `.session/donna`.
- set `workflow_dirs` to `./workflows` and `./.session/donna`.
- include commented examples for `defaults`.
- include commented examples for `journal.cmd`.

The starter configuration MUST be valid TOML after comments are ignored.

## Invalid configuration

Configuration loading MUST fail for:

- invalid TOML.
- unsupported schema version.
- unknown top-level fields.
- unknown fields in known nested tables.
- invalid `session_dir`.
- invalid `workflow_dirs`.
- invalid default primitive paths.
- invalid default primary section id.
- empty `journal.cmd`.
- unsupported journal placeholders.

## Compatibility rules

The configuration schema SHOULD preserve backward compatibility for:

- the `donna.toml` file name.
- schema version semantics.
- existing top-level field names.
- existing nested field names.
- default `session_dir`.
- default `workflow_dirs`.
- supported journal placeholder meanings.

Backward-compatible additions MAY include:

- new optional fields.
- new supported schema versions.
- new journal placeholders.

Backward-incompatible changes MUST be documented in this specification before implementation.
