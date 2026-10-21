# Skill Fixtures

## Goal of the document

This document describes packaged Markdown documentation printed by `donna skill`.

## Scope

This specification covers built-in skill fixtures.
The following are out of scope:

- exact prose.
- CLI parsing.
- rendering.
- configuration semantics beyond examples.
- external agent-skill installation.

## Availability

Built-in skill documentation MUST be included in the installed distribution and be available without project configuration.

## Fixture set

Every document offered by the skill command MUST have packaged Markdown content.
Required document names MUST follow `specs/behavior/cli.md`; their content requirements follow below.
Each fixture MUST start with one h1 identifying Donna and the document's subject.

## Usage fixture

Usage MUST describe:

- command invocation/output and protocols.
- root discovery and `--config`.
- root-anchored artifact/section ids.
- access to other skills.
- existing-session safety.
- workflow lifecycle:

  - startup.
  - continuation.
  - action completion.
  - nesting.
  - creation/editing when instructed.

- session and artifact commands.

It SHOULD keep configuration syntax brief and refer details to the configuration fixture.
Concise examples MAY clarify command output or agent usage, such as forwarding journals.
It MUST NOT direct agents to run workflows without developer, project, or Donna instructions.

## Configuration fixture

Configuration MUST describe `donna.toml`, its project-root meaning, and journal placeholders, using schema-compatible examples.
It SHOULD illustrate:

- minimal and generated starter configurations.
- `session_dir`.
- `workflow_dirs`.
- `defaults`.
- `journal.cmd`.

It SHOULD recommend project-owned workflow/session directories consistent with defaults and explain command-based validation.

## Initialization fixture

Initialization MUST explain:

- `donna init`.
- no overwrite.
- `--config` target/root selection.
- configuration-only creation without workflow files.
- lazy runtime session-directory creation.

It SHOULD guide starter review/filling, first workflows only when explicitly requested, and validation using current commands.

## Workflows fixture

Workflows MUST describe:

- `.donna.md` Markdown format and H1/H2 structure.
- artifact, section, and artifact-section ids.
- configuration and script fences.
- standard operations in `donna.lib`:

  - `request_action`.
  - `run_script`.
  - `output`.
  - `finish`.

- `donna.lib.text` as a text section, not an operation.
- `donna.lib.goto` action transitions.
- `donna.lib.task_variable` rendering.
- `donna.lib.path` normalized root-anchored/absolute paths.
- validation expectations.

It MUST include a complete minimal workflow.

## Style

Fixtures MUST be self-contained tool documentation, without requiring source/spec inspection for usage.
They SHOULD use concise Markdown, prefer implemented stable behavior, and use `donna -p llm ...` for agent-facing commands.
Examples SHOULD cover:

- commands.
- TOML.
- workflows.
- output.
