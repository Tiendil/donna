
# Intoduction to the Donna development

```toml donna
kind = "donna.lib.specification"
```
This document provides an introduction to the Donna project for agents and developers who want to understand how to work with the Donna codebase.

## Project overview

`Donna` is a CLI tool that helps manage the work of AI agents like Codex.

It is designed to to invert control flow: instead of agents deciding what to do next, the `donna` tells agents what to do next by following predefined workflows.

The core idea is that most of high-level workflows are more algorithmic than it may seem at first glance. For example, it may be difficult to fix a particular type issue in the codebase, but the overall process of polishing the codebase is quite linear:

1. Ensure all tests pass.
2. Ensure the code is formatted correctly.
3. Ensure there are no linting errors.
4. Go to the step 1 if you changed something in the process.
5. Finish.

We may need coding agents on the each step of the process, but there no reason for agents to manage the whole grooming loop by themselves — it take longer time, spends tokens and may lead to confusion of agents.

## Dictionary

- **Action request** — a workflow operation of kind `donna.lib.request_action` that produces instructions an agent must execute and then report completion for, including the next operation id.
- **Artifact** — any text or binary document managed by Donna in a world; text artifacts are typically Markdown templates with metadata and are the primary units of knowledge and workflow.
- **Configuration block** — a fenced code block with the `donna` keyword (preferably TOML) that configures an artifact or section (e.g., kind, workflow ids).
- **Directive** — a Jinja2 helper like `donna.lib.view(...)` or `donna.lib.goto(...)` that adds references and workflow transitions in artifact sources.
- **Environment error** — a structured, user-facing error (Pydantic model) describing external problems; returned via `Result` rather than raised.
- **Head section** — the H1 section of an artifact (before the first H2) that contains the primary description and mandatory config block.
- **Internal error** — an exception derived from `InternalError` indicating a bug or invariant violation inside Donna.
- **Protocol** — the output/interaction mode for Donna (e.g., `llm`) that governs CLI behavior and rendering and is required via `-p`.
- **Representation** — a rendered view of an artifact (e.g., CLI output) produced from its source using a render mode.
- **Result** — the Ok/Err return type used for functions that can yield environment errors.
- **Session** — the active unit of work tracked by Donna; its state and artifacts live in the `session` world and it always has exactly one active story.
- **Source** — the raw artifact text (typically a Jinja2 Markdown template) edited by developers/agents.
- **Specification** — a text artifact of kind `donna.lib.specification` that documents behavior, rules, or project guidance.
- **Story** — a semantically consistent scope of work within a session; a conceptual unit not directly represented in the tool.
- **Tail section** — each H2 section of an artifact; in workflows, each tail section defines one operation.
- **World** — a storage namespace (filesystem or other backends) that contains artifacts (e.g., `donna`, `home`, `project`, `session`).
- **Workflow** — a `donna.lib.workflow` artifact that encodes a finite-state machine of operations guiding the agent’s work.
- **Workflow operation** — a single step in a workflow, defined by a tail section with an `id`, `kind`, and instructions.

## Points of interest

- `./donna/` — a directory containing source code of project — `donna` CLI tool.
- `./.donna/` — a directory containing project-specific donna artifacts that is used to manage the work of AI agents on this project.

## Specifications of interest

Since this is the repository that contains the Donna project itself, you MUST pay additional attention to from which world you are viewing specifications.

- `donna:` world contains specifications and artifacts related to the Donna tool behavior. You access them when you need to use `donna` tool itself. You change them when you make changes to the Donna behavior.
- `project:` world contains specifications and artifacts related to the Donna project as a software project. You access them when you need to understand how to introduce changes to the Donna codebase. You change them when you change the development processes or documentation of the Donna project as a software project.

Check the next specifications:

- `{{ donna.lib.view("project:core:top_level_architecture") }}` when you need to introduce any changes in Donna or to research its code.
- `{{ donna.lib.view("donna:core:error_handling") }}` when you need to implement any new feature in Donna that may produce, process or propagate errors.
