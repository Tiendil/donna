# Configuration

## Goal of the document

This document describes Donna's project configuration contract.

## Scope

Configuration-file behavior; the following are out of scope:

- CLI invocation.
- output formatting.
- workflow operations.
- artifact syntax.
- session schemas.
- module ownership.

Requirements govern semantics without prescribing implementation strategy.

## Dictionary

- `configuration file` — one project's TOML configuration, canonically `donna.toml`.
- `project root` — active configuration's containing directory.
- `session directory` — runtime state and session-created artifacts.
- `workflow directory` — recursively scanned project directory.
- `section default` — fallback for omitted artifact-section configuration.
- `journal command` — optional external journal destination.

## Configuration file discovery

Donna MUST follow the contract in `specs/behavior/config.md` in `llm-tool-cli`, with default filename `donna.toml`, for:

- discovery.
- resolution.
- loading.
- initialization.

Workspace commands MUST select and validate Donna configuration using invocation cwd and optional `--config` under that contract.
The selected file's parent MUST be project root; configuration failures MUST preserve the contract's diagnostic information.

## Active configuration

Workspace commands MUST validate the selected configuration before performing their requested work.
The selected configuration file and project root MUST remain consistent through execution and output.
Project-independent commands MUST NOT require or load workspace configuration.

## TOML structure

Only these top-level fields MAY appear; unknown fields MUST fail:

- `version` — Schema version.
- `session_dir` — Runtime storage.
- `workflow_dirs` — Discovery directories.
- `defaults` — Artifact-section fallbacks.
- `journal` — External forwarding.

The supported schema version and omitted-value default MUST be `1`.
Version values and diagnostics MUST follow the Version contract in `specs/behavior/config.md` in `llm-tool-cli`; non-integer or unsupported versions MUST fail.
A minimal file is `version = 1`; a starter includes:

```toml
version = 1
session_dir = ".session/donna"
workflow_dirs = ["./workflows", "./.session/donna"]
```

## Session directory

Optional `session_dir` MUST default to `.session/donna` and follow the Session directory contract in `specs/behavior/config.md` in `llm-tool-cli`.
Its path MUST resolve from project root; session commands MUST store runtime state there.
Runtime MAY create the directory lazily.

## Workflow directories

Optional `workflow_dirs` MUST default to `["./workflows", "./.session/donna"]`.
Provided values MUST be project-relative path lists without absolute paths or parent references.
Duplicates MUST be removed preserving first occurrence.
Paths MUST resolve from project root under the project-path contract applied in `specs/behavior/file_paths.md`.
Examples SHOULD use readable `./` prefixes.

Discovery MUST ignore missing directories, recursively enumerate files in configured directory order under the File enumeration contract in `specs/behavior/paths.md` in `llm-tool-cli`, and select only `.donna.md` files.
Directory names MUST remain literal, not globs.
Enumeration failures MUST propagate, not become empty success.

## Defaults

Optional `defaults` MUST be a table with only these optional fields and effective defaults:

```toml
[defaults]
tail_section_kind = "donna.lib.text"
primary_section_kind = "donna.lib.workflow"
primary_section_id = "primary"
```

These respectively configure H2 kind, H1 kind, and H1 id.
Unknown fields MUST fail; primitive paths MUST be valid Python-path-like Donna identifiers and the id MUST be a valid section id.
Explicit section configuration MUST override defaults.
Projects SHOULD change them only for intentional custom primitives/artifact conventions.

## Journal

Optional `journal` MUST be a table with only optional `cmd`; unknown fields MUST fail.
Absent/null `cmd` MUST disable external execution while retaining console journals.
A present command MUST be a nonempty string-argument list.
External journal delivery MUST follow the Output delivery contract in `specs/behavior/protocol.md` in `llm-tool-cli`, processing each journal event once and executing argument lists directly without a shell.
Execution failures MUST preserve that contract's diagnostics.
Message arguments MUST retain normalized internal line breaks independently of compact console escaping.

### Journal placeholders

Whole arguments enclosed in braces MUST substitute the corresponding journal-event value.
Donna workflow journal events MUST provide:

- `{timestamp}` — ISO-8601 creation time.
- `{actor_id}` — Actor or empty string.
- `{message}` — Message.
- `{current_task_id}` — Task or empty string.
- `{current_work_unit_id}` — Work unit or empty string.
- `{current_operation_id}` — Operation artifact-section id or empty string.

Missing/null fields MUST become position-preserving empty arguments, including absent error-record execution ids or entirely unknown names.
Unknown placeholders MUST NOT fail configuration or argument construction.
Embedded text MUST remain literal: `{message}` substitutes, `message:{message}` does not.

```toml
[journal]
cmd = ["./bin/journal-tool.sh", "record", "{timestamp}", "{actor_id}", "{current_task_id}", "{current_operation_id}", "{message}"]
```

## Starter configuration

Init MUST select its target using invocation cwd, optional `--config`, and default filename `donna.toml` under the initialization contract in `specs/behavior/config.md` in `llm-tool-cli`.
The created file MUST pass Donna configuration validation before success is reported.
A file created before subsequent validation failure MUST remain on disk.

The starter MUST be valid TOML after ignoring comments and contain:

- version `1`.
- `session_dir = ".session/donna"`.
- `workflow_dirs = ["./workflows", "./.session/donna"]`.
- commented `defaults` examples.
- commented `journal.cmd` examples.

## Invalid configuration

Loading MUST reject:

- unsupported versions.
- unknown top-level/nested fields.
- invalid session/workflow directories.
- invalid default primitive paths or primary id.
- empty journal commands.

## Compatibility rules

Compatibility SHOULD preserve:

- filename.
- version semantics.
- top-level/nested field names.
- session/workflow directory defaults.
- journal placeholder meanings.

New optional fields, versions, and placeholders MAY be compatible additions.
Breaking changes MUST be specified before implementation.
