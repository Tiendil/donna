# `donna` Configuration

Donna project configuration lives at:

```text
<project-root>/donna.toml
```

The file is created by `donna -p llm workspaces init`. Edit it when the project needs workflow source directories, default section settings, cache behavior, or journal forwarding.

## Minimal Configuration

A default project can use the generated configuration without manual edits. The effective defaults are:

```toml
session = ".session/donna"
default_section_kind = "donna.lib.text"
default_primary_section_id = "primary"
cache_lifetime = 1.0
workflow_dirs = ["./workflows", "./.session/donna"]

[journal]
```

## Session Directory

`session` points to Donna's temporary session directory.
Donna stores runtime state, action requests, and session-created artifacts there.

Default:

```toml
session = ".session/donna"
```

Relative paths are resolved from the project root; absolute paths are used as configured. Use a directory ignored by version control unless a project intentionally tracks session artifacts.

## Default Sections

Donna loads artifacts only from `*.donna.md` Markdown files.

When a non-primary section omits `kind`, Donna uses `default_section_kind`. When the primary section omits `id`, Donna uses `default_primary_section_id`.

```toml
default_section_kind = "donna.lib.text"
default_primary_section_id = "primary"
```

Fields:

- `default_section_kind`: full Python path to the primitive used for sections without an explicit `kind`.
- `default_primary_section_id`: section id assigned to the primary H1 section when it omits `id`.

## Workflow Directories

`workflow_dirs` controls where Donna searches for workflow artifacts. Donna recursively scans each configured directory and recognizes only files ending with `.donna.md`.

Default:

```toml
workflow_dirs = ["./workflows", "./.session/donna"]
```

Paths are relative to the Donna project root. Missing directories are ignored, so a project can keep the default list before all of those directories exist.

Example:

```toml
workflow_dirs = [
  "./workflows",
  "./.session/donna",
  "./team-workflows",
]
```

Use narrower directories when you want Donna to ignore unrelated `.donna.md` files elsewhere in the project.

## Journal Forwarding

`journal.cmd` forwards Donna journal records to an external command. Omit it or set it to `null` to disable forwarding.

Example:

```toml
[journal]
cmd = ["./bin/taskwarior.sh", "log", "+journal", "+donna", "{message}"]
```

The command is configured as a list of arguments. Donna does not run a shell for this command.

Supported placeholders:

- `{timestamp}`: ISO-8601 record timestamp.
- `{actor_id}`: actor that created the record.
- `{message}`: journal message.
- `{current_task_id}`: current task id, if any.
- `{current_work_unit_id}`: current work unit id, if any.
- `{current_operation_id}`: current operation artifact section id, if any.

Invalid placeholder names make configuration loading fail.

Example with explicit fields:

```toml
[journal]
cmd = [
  "./bin/taskwarior.sh",
  "log",
  "+journal",
  "+donna",
  "actor:{actor_id}",
  "operation:{current_operation_id}",
  "{message}",
]
```

## Cache Lifetime

`cache_lifetime` controls how long Donna may reuse cached project data, in seconds.

Example:

```toml
cache_lifetime = 0.25
```

Use a smaller value when artifacts are edited rapidly by external tools. Use the default unless stale reads are observed.

## Validation Workflow

After editing `donna.toml`, run:

```bash
donna -p llm artifacts list
donna -p llm artifacts validate '**'
```

If Donna cannot load the project config, inspect the reported configuration error and fix the TOML before continuing workflow work.
