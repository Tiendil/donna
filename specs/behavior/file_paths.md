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
- `project path` — a path identifier that addresses a non-root filesystem location inside the project root and can be represented as a canonical root-anchored id.
- `artifact id` — a canonical project-root-anchored identifier for a Donna artifact file.
- `artifact section id` — an artifact id plus a section id separated by `:`.
- `root-anchored path` — a project path that starts with `@/` and is resolved from the project root.
- `relative path` — a path that does not start with `@/` and is resolved against an explicit base path or the command current working directory.
- `canonical path` — the normalized root-anchored representation of a project path.
- `base path` — a project file or directory used by a context to resolve relative paths.

## Project root

The project root MUST be a local filesystem directory. For commands that load `donna.toml`, it MUST be the directory containing the active configuration file, including when `--config PATH` selects that file.

## Project paths

A canonical project path MUST use `@/path/inside/project`, where `@/` denotes the project root and `/` separates segments. It MUST identify a non-root location and contain no empty, `.` or `..` segments or trailing `/`.

Root-anchored inputs MAY contain `.` and `..` segments before normalization. Normalization MUST remove `.` and resolve `..`, rejecting traversal above the project root and a root-only result. It MUST preserve meaningful segment case. For example, `@/workflows/rfc/../polish.donna.md` normalizes to `@/workflows/polish.donna.md`.

Project path segments MAY contain any characters accepted by the local filesystem in a single path component, including spaces and Unicode.

Path identity MUST be based on the canonical path. Inputs that normalize to the same canonical path MUST identify the same project path.

Root-anchored identifier normalization MUST NOT depend on filesystem existence or symlink targets.

## Resolution and availability

A root-anchored path MUST be resolved from the project root.

Relative paths MUST be accepted only by contexts that explicitly define a base path. A directory base MUST be used directly; a file base MUST use its containing directory. Artifact-local relative paths MAY use the directory containing the source artifact.

Absolute host filesystem paths MAY be accepted only by contexts that explicitly support them. Accepted relative and absolute inputs MUST normalize to canonical root-anchored paths inside the project root. Absolute host paths MUST NOT be canonical project identifiers.

Filesystem resolution MUST enforce project-root containment after resolving symlinks and MUST reject the project root itself.

A project path MAY refer to a file, directory, or not-yet-existing location. Existence and suffix requirements MUST be enforced only by contexts that require them. Existing-file contexts MUST reject or skip paths that do not identify existing regular files, according to the context's behavior; reference contexts MAY accept locations that do not yet exist.

Invalid project paths MUST use the `invalid_project_path` diagnostic rather than a Donna-specific path or identifier diagnostic. Artifact lookup MAY treat a candidate rejected for project-root containment as unavailable.

## Artifact ids

An artifact id MUST be a canonical project path identifying a file with the `.donna.md` extension, such as `@/workflows/polish.donna.md`.

Artifact ids SHOULD be written as root-anchored paths in workflow instructions, agent notes, and persisted session state.

## Artifact section ids

An artifact section id MUST combine a valid artifact id and a local section id with `:`, as in `@/workflows/polish.donna.md:finish`.

Section id syntax MUST remain independent from artifact path segment syntax. Section ids MUST contain only ASCII letters, ASCII digits, `.`, `_`, or `-`, and MUST contain at least one character other than `.` or `-`.

Artifact section ids are used by `complete-action-request` to identify the next operation selected by an agent.

## CLI path inputs

CLI input parameters that accept artifact paths MUST accept root-anchored, relative filesystem, and absolute filesystem paths. Relative paths MUST resolve from the command's current working directory.

Accepted inputs MUST be normalized to canonical root-anchored paths before artifact loading, artifact validation, workflow execution, or action request completion. Inputs resolving outside the project root MUST be rejected.

New CLI examples and protocol output SHOULD use canonical root-anchored paths unless demonstrating relative or absolute filesystem input compatibility. Workflow instructions SHOULD also prefer root-anchored paths unless relative addressing is central to the example.

## Template path directive

The `donna.lib.path("<path>", mode="project"|"absolute")` directive MUST normalize local project paths in workflow text.

The directive MUST accept:

- root-anchored paths.
- relative paths resolved from the directory containing the workflow artifact being rendered.
- absolute filesystem paths that resolve inside the Donna project root.

The default mode MUST be `project`. In `project` mode, the directive MUST render the canonical root-anchored path; in `absolute` mode, it MUST render the corresponding absolute filesystem path.

The directive MUST reject paths that cannot be normalized to a non-root location inside the Donna project root.

Workflow instructions SHOULD use this directive when they need to reference project files from rendered agent-facing text.

## Configuration paths

Configuration paths such as `session_dir` and `workflow_dirs` MUST be project-relative paths resolved from the Donna project root. They MUST NOT be absolute host paths or contain parent-directory references.

Configuration examples SHOULD use `./` prefixes for directory paths when doing so improves readability.
