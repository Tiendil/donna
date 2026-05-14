# `donna` Configuration

Donna project configuration lives at:

```text
<project-root>/donna.toml
```

The file is created by `donna -p llm workspaces init`. Edit it when the project needs artifact visibility rules, default section settings, cache behavior, or journal forwarding.

## Minimal Configuration

A default project can use the generated configuration without manual edits. The effective defaults are:

```toml
session = ".session/donna"
default_section_kind = "donna.lib.text"
default_primary_section_id = "primary"
cache_lifetime = 1.0

[[file_filters]]
mode = "include"
pattern = "@/.session/donna/**/*.donna.md"

[[file_filters]]
mode = "include"
pattern = "@/.agents/**/*.donna.md"

[[file_filters]]
mode = "ignore"
pattern = ".*/**"

[[file_filters]]
mode = "include"
pattern = "**/*.donna.md"

[[file_filters]]
mode = "ignore"
pattern = "**"

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

## File Filters

`file_filters` control which project files Donna can see as artifacts. Filters are evaluated in order. The first matching rule decides whether a file is included, ignored, or required.

Modes:

- `include`: admit matching files when they exist.
- `ignore`: hide matching files.
- `required`: admit matching files and treat missing expected files as an error when relevant.

Patterns are Donna artifact patterns rooted at the project. Use `@/` for explicit project-root paths and `**` for recursive matching.

Example:

```toml
[[file_filters]]
mode = "include"
pattern = "@/specs/**/*.donna.md"

[[file_filters]]
mode = "ignore"
pattern = "@/specs/archive/**"

[[file_filters]]
mode = "ignore"
pattern = "**"
```

Put narrow rules before broad rules. Keep a final `ignore "**"` rule when you want an allow-list.

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
donna -p llm artifacts list '**'
donna -p llm artifacts validate '**'
```

If Donna cannot load the project config, inspect the reported configuration error and fix the TOML before continuing workflow work.
