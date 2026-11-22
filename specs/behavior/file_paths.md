# Artifact paths

## Goal of the document

This document describes Donna artifact identifiers and how project paths apply to CLI inputs, artifact-relative references, and template names.

## Scope

This specification covers artifact and section identifiers, path input bases, and template paths.

The following topics are out of scope:

- workflow operation semantics.
- artifact source parsing details.
- output protocol formatting details, except for canonical path representation.

## Shared project paths

Donna MUST use the project-path contract in `specs/behavior/paths.md` in the `llm-tool-cli` repository for:

- CLI inputs.
- artifact lookup.
- artifact-relative references.

The project root MUST be the local directory containing the active configuration file, selected according to `specs/behavior/config.md`.
Artifact-relative filesystem inputs MUST use the source artifact's containing directory as their base.
Artifact lookup MAY treat a candidate rejected for project-root containment or symbolic-link traversal as unavailable.

## Artifact ids

An artifact id MUST be a canonical project path identifying a file with the `.donna.md` extension, such as `@/workflows/polish.donna.md`.

Unless demonstrating other accepted input forms, artifact ids SHOULD be written as root-anchored paths in:

- workflow instructions.
- agent notes.
- persisted session state.
- CLI examples.
- protocol output.

## Artifact section ids

An artifact section id MUST combine a valid artifact id and a local section id with `:`, as in `@/workflows/polish.donna.md:finish`.

Section id syntax MUST remain independent from artifact path segment syntax.
Section ids MUST contain only:

- ASCII letters.
- ASCII digits.
- `.`.
- `_`.
- `-`.

They MUST contain at least one character other than `.` or `-`.

Artifact section ids are used by `complete-action-request` to identify the next operation selected by an agent.

## CLI path inputs

CLI artifact inputs MUST follow the Mixed path normalization contract in `specs/behavior/paths.md` in `llm-tool-cli`, with the command's current working directory as the relative filesystem base.
Normalization MUST precede:

- artifact loading.
- artifact validation.
- workflow execution.
- action request completion.

## Exact template paths

A Jinja template name beginning with `@/` MUST be a canonical project path under a directory listed in `template_dirs`.
Template lookup MUST select that exact file from the project root.

## Directive paths

Project path arguments to directives MUST follow the Mixed path normalization contract in `specs/behavior/paths.md` in `llm-tool-cli`.
Relative filesystem inputs to directives are artifact-relative.
