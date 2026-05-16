# `donna` Configuration

`donna.toml` tells `donna` where a project's workflow virtual machine stores state, where it discovers workflow artifacts, which default section primitives to use, and how to forward workflow journal records.

Donna is a CLI tool for agents. It keeps high-level control flow in explicit workflows so an agent can focus on the concrete work requested by each operation. A workflow is a state machine stored in a project-local `.donna.md` artifact. Donna maintains the active session state, the workflow stack, queued work units, and action requests.

The configuration file has two main parts:

- Top-level workspace settings configure session storage, artifact discovery, and default artifact section behavior.
- `journal` configures optional forwarding of Donna journal records to an external command.

The configuration file is TOML with schema version `1`. The presence of `donna.toml` marks a Donna project root.

Minimal file:

```toml
version = 1
```

If `version` is omitted, Donna treats the configuration as schema version `1`.

The generated file includes comments around this shape:

```toml
version = 1

session_dir = ".session/donna"

workflow_dirs = [
    "./workflows",
    "./.session/donna",
]

[journal]
```

Effective defaults:

```toml
version = 1
session_dir = ".session/donna"
default_section_kind = "donna.lib.text"
default_primary_section_kind = "donna.lib.workflow"
default_primary_section_id = "primary"
workflow_dirs = ["./workflows", "./.session/donna"]

[journal]
```

Top-level fields:

- `version`: optional integer, currently `1`.
- `session_dir`: optional relative path to Donna's session directory.
- `default_section_kind`: optional Python path to the primitive used for non-primary sections without an explicit `kind`.
- `default_primary_section_kind`: optional Python path to the primitive used for the primary H1 section without an explicit `kind`.
- `default_primary_section_id`: optional section id assigned to the primary H1 section when it omits `id`.
- `workflow_dirs`: optional list of relative directories scanned for `.donna.md` workflow artifacts.
- `journal`: optional journal forwarding config.

Unknown top-level fields are invalid.

## Version

`version` declares the Donna configuration schema version.

```toml
version = 1
```

Fields:

- `version`: optional integer, currently `1`.

If `version` is omitted, Donna treats the configuration as schema version `1`.

If `version` is present, it must be an integer.

If `version` is not supported, configuration loading fails.

## Session Directory

`session_dir` points to Donna's temporary session directory. Donna stores runtime state, action requests, and session-created artifacts there.

```toml
session_dir = ".session/donna"
```

Fields:

- `session_dir`: optional relative project path, default `.session/donna`.

The path is resolved from the Donna project root. It must be relative and must not contain `..`.

Use a directory ignored by version control unless the project intentionally tracks session artifacts.

## Workflow Directories

`workflow_dirs` controls where Donna searches for workflow artifacts. Donna recursively scans each configured directory and recognizes only files ending with `.donna.md`.

```toml
workflow_dirs = [
    "./workflows",
    "./.session/donna",
]
```

Fields:

- `workflow_dirs`: optional list of relative project paths, default `["./workflows", "./.session/donna"]`.

Each path is resolved from the Donna project root. Paths must be relative and must not contain `..`.

Missing directories are ignored. Duplicate directories are deduplicated when configuration is loaded.

Use narrower directories when you want Donna to ignore unrelated `.donna.md` files elsewhere in the project.

## Default Sections

Donna artifacts are Markdown files ending with `.donna.md`. Each artifact is split into sections. A fenced `toml donna` block configures the artifact or section that contains it.

The default section fields let a project omit repetitive config in common artifacts:

```toml
default_section_kind = "donna.lib.text"
default_primary_section_kind = "donna.lib.workflow"
default_primary_section_id = "primary"
```

Fields:

- `default_section_kind`: optional Python import path, default `donna.lib.text`.
- `default_primary_section_kind`: optional Python import path, default `donna.lib.workflow`.
- `default_primary_section_id`: optional section id, default `primary`.

When a non-primary section omits `kind`, Donna uses `default_section_kind`.

When the primary H1 section omits `kind`, Donna uses `default_primary_section_kind`.

When the primary H1 section omits `id`, Donna uses `default_primary_section_id`.

Most projects should not change these fields. Change them only when a project intentionally uses custom Donna primitives or a different artifact convention.

## Journal

`journal.cmd` forwards Donna journal records to an external command. Omit `cmd` to disable forwarding.

```toml
[journal]
cmd = ["./bin/taskwarior.sh", "log", "+journal", "+donna", "{message}"]
```

Fields:

- `cmd`: optional non-empty list of command arguments.

Donna does not run a shell implicitly. If shell behavior is required, call a shell explicitly:

```toml
[journal]
cmd = [
    "/bin/sh",
    "-c",
    "printf '%s [%s] %s\n' \"$1\" \"$2\" \"$3\" >> donna.log",
    "journal",
    "{timestamp}",
    "{actor_id}",
    "{message}",
]
```

Supported whole-argument placeholders:

- `{timestamp}`: ISO-8601 record timestamp.
- `{actor_id}`: actor that created the record.
- `{message}`: journal message.
- `{current_task_id}`: current task id, if any.
- `{current_work_unit_id}`: current work unit id, if any.
- `{current_operation_id}`: current operation artifact section id, if any.

Invalid placeholder names make configuration loading fail.

Placeholders are recognized only when the whole argument starts with `{` and ends with `}`. For example, `{message}` is a placeholder, but `message:{message}` is a literal argument.

Donna still prints newly created journal records through the selected output protocol even when `journal.cmd` is omitted.

## Paths

Paths in `donna.toml` are stable from the Donna project root, which is the directory containing the active `donna.toml`.

Configuration paths should use `/`.

Project paths in `session_dir` and `workflow_dirs` must be relative:

```toml
session_dir = ".session/donna"
workflow_dirs = ["./workflows", "./.session/donna"]
```

Absolute paths are invalid:

```toml
session_dir = "/tmp/donna"
```

Parent-directory references are invalid:

```toml
workflow_dirs = ["../workflows"]
```

Workflow artifact ids use canonical root-anchored paths:

```text
@/workflows/polish.donna.md
@/.session/donna/execute_rfc.donna.md
```

Artifact section ids append `:section_id`:

```text
@/workflows/polish.donna.md:finish
```

## Recommendations

Keep project-owned workflows in a dedicated workflow directory such as `./workflows`.

Keep temporary or generated workflows under the configured `session_dir` and include that directory in `workflow_dirs` when those workflows should be executable.

Do not broaden `workflow_dirs` to the whole repository unless the project intentionally treats every `.donna.md` file as an executable Donna artifact.

Keep default section settings unchanged unless the project has custom primitives and a clear convention for using them.

Configure `journal.cmd` only when the project has a stable journal tool. A failing journal command can make Donna report environment errors during workflow execution.

## Validation

After editing `donna.toml`, run:

```bash
donna -p llm list
donna -p llm validate --all
```

If Donna cannot load the project config, inspect the reported configuration error and fix the TOML before continuing workflow work.

After creating or editing a workflow, validate that workflow directly:

```bash
donna -p llm validate @/workflows/example.donna.md
```

If the workflow should be discoverable, confirm it appears in:

```bash
donna -p llm list
```
