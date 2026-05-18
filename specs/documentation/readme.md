# README Documentation

## Goal of the document

This document describes the expected content, structure, and tone of the project `README.md`.

## Scope

The scope of this specification is limited to the repository root `README.md`.

The following topics are out of scope:

- package publishing.
- generated command help.
- detailed CLI behavior.
- detailed configuration syntax.
- detailed workflow artifact syntax.
- development environment rules for agents.
- documentation files other than the root `README.md`.

## Audience

`README.md` MUST be written primarily for humans who are discovering the project.

`README.md` MAY mention coding agents because Donna is designed for agent workflows, but it MUST NOT duplicate the full built-in agent skill documentation.

`README.md` SHOULD help readers quickly understand:

- what problem Donna solves.
- what Donna does.
- how to try the main commands.
- where to find detailed usage, configuration, and workflow documentation.
- how to work on the project.

## Source Material

`README.md` MUST reflect the current behavior and architecture described in `./specs/`.

`README.md` MAY use project metadata from `pyproject.toml` for stable package identity, repository links, and installation context.

Existing `README.md` prose MUST NOT be treated as a source of truth when it conflicts with `./specs/` or package metadata.

## Structure

`README.md` MUST start with a single h1 heading containing the project name.

The first paragraphs after the h1 heading SHOULD explain the core value proposition in plain language.

`README.md` MUST use the following h2 sections in this order:

1. `Example`
2. `Rationale`
3. `Features`
4. `Quick Usage`
5. `Installation`
6. `Configuration`
7. `Workflow Files`
8. `Specifications`
9. `Development`

The `Example` section MUST be the first h2 section after the introductory paragraphs.

Additional h2 sections MUST NOT be added without updating this specification first. Lower-level subsections MAY be added under the required h2 sections when they help human readers.

`README.md` SHOULD avoid deep implementation details.

## Content Requirements

`README.md` MUST mention that Donna is a CLI tool.

`README.md` MUST explain that Donna helps agents run predefined workflows in a deterministic way.

`README.md` MUST explain that Donna interprets workflows as state-machine-like graphs of operations.

`README.md` MUST explain that Donna maintains project-local session state, discovers workflow artifacts, emits action requests for agents, and accepts agent reports about the next operation to run.

`README.md` MUST explain that a Donna project is configured by `donna.toml`.

`README.md` MUST explain that workflow artifacts are Markdown files ending with `.donna.md`.

`README.md` MUST link to the configuration behavior specification when describing configuration.

`README.md` MUST link to the CLI behavior specification when describing command behavior.

`README.md` MUST link to the skill fixture specification or mention built-in skill documentation when describing detailed user documentation.

`README.md` MUST mention that this repository uses Donna and that its `donna.toml` and `workflows/` directory can be used as real project examples.

`README.md` MUST explain how to create a starter configuration with `donna init`.

`README.md` MUST include installation examples for installing Donna from PyPI with `uv` and `pip`.

`README.md` MUST explain that the generated starter configuration should be reviewed and edited for the project.

`README.md` MUST mention that a user can ask a coding agent to help create or adapt workflow files.

`README.md` MUST include a short `AGENTS.md` instruction snippet that tells agents to use Donna only when instructed by a developer, project instructions, or Donna itself.

`README.md` MUST mention the primary workflows:

- initializing a Donna project.
- listing discovered workflow artifacts.
- validating workflow artifacts.
- rendering workflow artifacts.
- starting a workflow.
- continuing queued workflow execution.
- completing an action request.
- reading built-in skill-style documentation.

`README.md` MUST include command examples for:

- `donna init`.
- `donna list`.
- `donna validate`.
- `donna render ...`.
- `donna run ...`.
- `donna continue`.
- `donna complete-action-request ...`.
- `donna skill usage`.

Human-facing command examples SHOULD use command defaults.

`README.md` MUST mention that `--protocol llm` is intended for coding agents and that `human` is the default protocol for terminal users.

`README.md` MUST point readers to `./specs/` as the source of project behavior and architecture.

`README.md` MUST describe development commands through `./bin/dev.sh` and `./bin/dev-tests.sh`.

`README.md` MUST state that development commands are run through Docker-backed project scripts.

## Style

`README.md` SHOULD be concise and practical.

`README.md` SHOULD prefer short explanations, bullet lists, and command examples.

`README.md` SHOULD use a confident but accurate tone.

`README.md` SHOULD avoid promising behavior that is only planned or not implemented.

`README.md` SHOULD not be an exhaustive user manual; detailed command, configuration, and workflow guidance belongs in built-in skill documentation and specifications.
