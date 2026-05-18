# File paths

## Goal of the document

This document describes the syntax, semantics, and resolution rules for local project paths and artifact identifiers used by `donna`.

## Scope

The scope of this specification is limited to path identifiers that refer to files and artifact sections inside the active Donna project.

The following topics are out of scope:

- workflow operation semantics.
- artifact source parsing details.
- filesystem discovery algorithms, except for canonical path representation.
- output protocol formatting details, except for canonical path representation.

## Dictionary

- `project root` — the root directory of the active Donna project.
- `project path` — a file-like path identifier that addresses a non-root location inside the project root and can be represented as a canonical root-anchored id.
- `artifact id` — a canonical project-root-anchored identifier for a Donna artifact file.
- `artifact section id` — an artifact id plus a section id separated by `:`.
- `root-anchored path` — a project path that starts with `@/` and is resolved from the project root.
- `relative path` — a path that does not start with `@/` and is resolved against an explicit base path or the command current working directory.
- `canonical path` — the normalized root-anchored representation of a project path.
- `base path` — a project file or directory used by a context to resolve relative paths.

## Project root

The project root MUST be a local filesystem directory.

For commands that load `donna.toml`, the project root MUST be the directory that contains the active configuration file.

When `--config PATH` is provided, the directory containing `PATH` MUST be treated as the project root by commands that load workspace configuration.

A project path MUST identify a non-root location inside the project root.

A project path MUST NOT identify a location outside the project root after path normalization.

A project path MUST NOT use an absolute host filesystem path as its canonical representation.

A canonical project path MUST satisfy Donna artifact id path syntax, including a suffixed final path segment.

## Root-anchored syntax

The canonical syntax for a project path MUST be:

```text
@/path/inside/project.ext
```

The `@/` marker MUST represent the project root.

The `/` character MUST separate path segments.

The path after `@/` MUST contain at least one path segment.

The canonical representation MUST NOT contain:

- empty path segments.
- `.` path segments.
- `..` path segments.
- a trailing `/`.

Examples of valid canonical paths:

```text
@/README.md
@/workflows/polish.donna.md
@/.session/donna/plans/implement-feature.donna.md
```

Examples of invalid canonical paths:

```text
@
@/
@/workflows/../README.md
@/workflows//polish.donna.md
@/workflows/
/home/user/project/workflows/polish.donna.md
```

## Path semantics

A project path identifies a local project location by its normalized position under the project root.

Path identity MUST be based on the canonical path, not on the textual form originally provided by a user, command source, or other input.

Two path inputs that normalize to the same canonical path MUST identify the same project path.

The existence of a project path MUST be checked by the context that uses it.

A field that declares existing-file semantics MUST reject or skip canonical paths that do not correspond to an existing regular file, according to that field's behavior.

A field that declares reference semantics MAY accept canonical paths that do not exist yet.

## Path normalization

Path normalization MUST produce a canonical root-anchored path.

Normalization MUST:

- resolve the input against the project root, command current working directory, or an explicit base path.
- remove redundant `.` path segments.
- process `..` path segments.
- reject the path if processing `..` escapes the project root.
- use `/` as the path separator in the canonical representation.
- preserve meaningful path segment case.

Normalization MUST NOT require the referenced file to exist unless the calling context requires an existing file.

Implementations MUST reject inputs that cannot be normalized to a project path inside the project root.

## Artifact ids

An artifact id MUST be a canonical root-anchored project path.

Artifact ids accepted by workflow commands MUST identify files with the Donna artifact extension:

```text
.donna.md
```

Artifact id path segments MUST contain only:

- ASCII letters.
- ASCII digits.
- `.`.
- `_`.
- `-`.

Each artifact id path segment MUST contain at least one character that is not `.` or `-`.

The last path segment MUST have a file suffix.

Artifact ids SHOULD be written as root-anchored paths in workflow instructions, agent notes, and persisted session state.

Examples:

```text
@/workflows/polish.donna.md
@/workflows/rfc/do.donna.md
@/.session/donna/plans/feature.donna.md
```

## Artifact section ids

An artifact section id MUST combine an artifact id and a local section id with `:`.

The canonical syntax MUST be:

```text
@/path/to/artifact.donna.md:section_id
```

The artifact part MUST be a valid artifact id.

The section id part MUST be a valid Donna section id.

Section ids MUST contain only:

- ASCII letters.
- ASCII digits.
- `.`.
- `_`.
- `-`.

The section id MUST contain at least one character that is not `.` or `-`.

Artifact section ids are used by `complete-action-request` to identify the next operation selected by an agent.

## Root-anchored resolution

A root-anchored path MUST be resolved from the project root.

For example, in a project rooted at `/project`, the input:

```text
@/workflows/polish.donna.md
```

resolves to:

```text
/project/workflows/polish.donna.md
```

The normalized canonical representation remains:

```text
@/workflows/polish.donna.md
```

Root-anchored inputs MAY contain redundant `.` or `..` segments before normalization, but the canonical representation MUST NOT contain them.

For example:

```text
@/workflows/rfc/../polish.donna.md
```

normalizes to:

```text
@/workflows/polish.donna.md
```

If a root-anchored input attempts to escape the project root, normalization MUST fail.

## Relative path resolution

Relative paths MUST be accepted only by contexts that explicitly define a base path.

CLI artifact path arguments MUST resolve relative paths from the command's current working directory.

Artifact-local relative paths MAY be resolved relative to the directory that contains the source artifact.

When the base path is a file, the relative path MUST be resolved against the directory that contains the base file.

When the base path is a directory, the relative path MUST be resolved against that directory.

After resolving a relative path, Donna MUST normalize the result to a canonical root-anchored path.

For example, with base file:

```text
@/workflows/rfc/do.donna.md
```

the relative input:

```text
../polish.donna.md
```

normalizes to:

```text
@/workflows/polish.donna.md
```

With the same base file, the relative input:

```text
../../../outside.donna.md
```

MUST fail if it escapes the project root.

New CLI examples and workflow instructions SHOULD prefer root-anchored paths unless relative addressing is central to the example.

## CLI path inputs

CLI input parameters that accept artifact paths MUST accept:

- root-anchored paths.
- classical relative filesystem paths.
- classical absolute filesystem paths.

CLI logic MUST normalize every accepted path input to a canonical root-anchored path before artifact loading, artifact validation, workflow execution, or action request completion.

When a CLI input parameter receives a root-anchored path, the path MUST be resolved from the project root and normalized to the canonical root-anchored form.

When a CLI input parameter receives a classical absolute filesystem path, the path MUST be normalized to a canonical root-anchored path if it points inside the project root.

If a classical absolute filesystem path points outside the project root, the CLI MUST reject it.

When a CLI input parameter receives a classical relative filesystem path, the path MUST first be resolved to an absolute filesystem path relative to the command's current working directory.

The resolved absolute filesystem path MUST then be normalized to a canonical root-anchored path if it points inside the project root.

If a classical relative filesystem path resolves outside the project root, the CLI MUST reject it.

New CLI examples and protocol output SHOULD use canonical root-anchored paths unless demonstrating classical relative or absolute filesystem input compatibility.

## Configuration paths

Configuration paths such as `session_dir` and `workflow_dirs` MUST be project-relative paths.

Configuration paths MUST be resolved from the Donna project root.

Configuration paths MUST NOT be absolute host filesystem paths.

Configuration paths MUST NOT contain parent-directory references.

Configuration examples SHOULD use `./` prefixes for directory paths when doing so improves readability.

## Host filesystem paths

Absolute host filesystem paths MUST NOT be canonical project path identifiers.

Implementations MAY accept an absolute host filesystem path as input only when the accepting context explicitly supports host path input.

CLI artifact path parameters are one such context.

When accepted, an absolute host filesystem path MUST resolve to a location inside the project root and MUST normalize to a canonical root-anchored path.
