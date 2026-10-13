# Artifact paths

## Goal of the document

This document describes Donna artifact identifiers and the application of shared project paths to CLI inputs and artifact-relative references.

## Scope

This specification covers artifact and section identifiers, path input bases, and template path output.

The following topics are out of scope:

- workflow operation semantics.
- artifact source parsing details.
- output protocol formatting details, except for canonical path representation.

## Shared project paths

Donna MUST use the project-path contract in `specs/behavior/paths.md` in the `llm-tool-cli` repository for CLI inputs, artifact lookup, artifact-relative references, and both template path directive modes.
The project root MUST be the local directory containing the active configuration file, selected according to `specs/behavior/config.md`.
Artifact-relative filesystem inputs MUST use the source artifact's containing directory as their base.
Artifact lookup MAY treat a candidate rejected for project-root containment or symbolic-link traversal as unavailable.

## Artifact ids

An artifact id MUST be a canonical project path identifying a file with the `.donna.md` extension, such as `@/workflows/polish.donna.md`.

Artifact ids SHOULD be written as root-anchored paths in workflow instructions, agent notes, persisted session state, CLI examples, and protocol output unless demonstrating other accepted input forms.

## Artifact section ids

An artifact section id MUST combine a valid artifact id and a local section id with `:`, as in `@/workflows/polish.donna.md:finish`.

Section id syntax MUST remain independent from artifact path segment syntax.
Section ids MUST contain only ASCII letters, ASCII digits, `.`, `_`, or `-`, and MUST contain at least one character other than `.` or `-`.

Artifact section ids are used by `complete-action-request` to identify the next operation selected by an agent.

## CLI path inputs

CLI artifact inputs MUST use shared mixed path normalization with the command's current working directory as the relative filesystem base.
Normalization MUST precede artifact loading, artifact validation, workflow execution, or action request completion.

## Template path directive

The `donna.lib.path("<path>", mode="project"|"absolute")` directive MUST use shared mixed path normalization with the rendered artifact's containing directory as the relative filesystem base.

The default mode MUST be `project`.
In `project` mode, the directive MUST render the canonical root-anchored path; in `absolute` mode, it MUST render the corresponding absolute filesystem path.
The directive MUST support references to files, directories, and locations that do not yet exist, without imposing an artifact suffix.

Workflow instructions SHOULD use this directive when they need to reference project files from rendered agent-facing text.
