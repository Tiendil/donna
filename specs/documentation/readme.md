# README Documentation

## Goal of the document

This document describes the root README's content, structure, and tone.

## Scope

This specification covers the root `README.md`.
The following are out of scope:

- publishing.
- generated help.
- detailed CLI/configuration/workflow syntax.
- agent development rules.
- other documentation.

## Audience

The README MUST primarily address humans discovering Donna.
It MAY discuss coding agents but MUST NOT duplicate the full built-in agent skills.
It SHOULD quickly explain:

- the problem and Donna's role.
- how to try main commands.
- where to find detailed usage, configuration, and workflow documentation.
- how to develop the project.

## Source Material

The README MUST reflect current `./specs/` behavior and architecture.
It MAY use `pyproject.toml` for package identity, repository links, and installation context.
Existing prose MUST NOT override conflicting specs or metadata.

## Structure

The README MUST start with one project-name h1, followed by introductory paragraphs that SHOULD explain its value plainly.
These h2 sections MUST follow in order:

1. `Features`
2. `Example`
3. `Installation`
4. `Configuration`
5. `Quick Usage`
6. `Workflow Files`
7. `Specifications`
8. `Development`

`Features` MUST be the first h2 and use compact bullets with bold feature names and short descriptions.
Additional h2 sections MUST NOT appear without updating this specification.
Helpful lower-level subsections MAY appear; deep implementation details SHOULD be avoided.

## Content Requirements

The README MUST explain:

- Donna is a CLI for deterministic agent execution of predefined workflows, interpreted as state-machine-like operation graphs.
- It coordinates workflow execution by:

  - maintaining project-local session state.
  - discovering artifacts.
  - emitting agent action requests.
  - accepting next-operation reports.

- Projects use `donna.toml`; workflow artifacts are Markdown files ending in `.donna.md`.
- This repository uses Donna; its `donna.toml` and `./workflows` are real examples.
- `donna init` creates starter configuration that should be reviewed and edited.
- Coding agents can help create or adapt workflows.
- `human` is the terminal default; `--protocol llm` is for coding agents.
- Development uses Docker-backed `./bin/dev.sh` and `./bin/dev-tests.sh`.

It MUST include PyPI installation examples using both `uv` and `pip`, and an `AGENTS.md` snippet directing agents to use Donna only when instructed by a developer, project instructions, or Donna itself.

It MUST mention these workflows:

- project initialization.
- workflow discovery.
- new-session creation.
- workflow startup.
- session inspection.
- queued execution continuation.
- action-request completion.
- built-in skill reading.

It MUST show command examples for:

- `donna init`.
- `donna list`.
- `donna validate`.
- `donna render ...`.
- `donna run ...`.
- `donna continue`.
- `donna complete-action-request ...`.
- `donna skill usage`.

Human-facing examples SHOULD use command defaults.
Configuration and command descriptions MUST link to their behavior specs.
Detailed-documentation guidance MUST link to the skill fixture spec or mention built-in skills.
The README MUST identify `./specs/` as the behavior and architecture source.

## Style

The README SHOULD be:

- concise.
- practical.
- confident.
- accurate.

It SHOULD use short explanations, bullets, and commands.

It SHOULD avoid promises of unimplemented behavior and exhaustive manual content; detailed guidance belongs in skills and specs.
