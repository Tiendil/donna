
# Introduction to the Donna development

```toml donna
kind = "donna.lib.specification"
```
This document provides an introduction to the Donna project for agents and developers who want to understand how to work with the Donna codebase.

## Project overview

`Donna` is a CLI tool that helps manage the work of AI agents like Codex.

It is designed to invert control flow: instead of agents deciding what to do next, the `donna` tells agents what to do next by following predefined workflows.

The core idea is that most high-level workflows are more algorithmic than it may seem at first glance. For example, it may be difficult to fix a particular type issue in the codebase, but the overall process of polishing the codebase is quite linear:

1. Ensure all tests pass.
2. Ensure the code is formatted correctly.
3. Ensure there are no linting errors.
4. Go to the step 1 if you changed something in the process.
5. Finish.

We may need coding agents on each step of the process, but there is no reason for agents to manage the whole grooming loop by themselves — it takes longer time, spends tokens and may lead to confusion of agents.

## Primary rules

1. If you need to perform a work with Donna, you **MUST** select an appropriate Donna workflow to perform the work and run it.
2. If there is no appropriate workflow, ask the developer for a precise instructions on what to do.
3. List all workflows: `{{ donna.lib.list("**", tags=["workflow"]) }}`
4. List all specifications: `{{ donna.lib.list("**", tags=["specification"]) }}`

## Dictionary

- **Action request** — an instruction to the agent (who runs Donna) to perform the specified operations. Action requests are created by operations, like `donna.lib.request_action`. After finishing following the instructions of an action request, the agent MUST report back to Donna specifying the next operation to continue with. The list of next operations is specified in the action request itself.
- **Artifact** — any text or binary document managed by Donna in a world; text artifacts are typically Markdown templates with metadata and are the primary units of knowledge and instructions.
- **Artifact Section** — a part of a text artifact separated by markdown headers, has its own configuration block and semantics depending on section kind.
- **Configuration block** — a fenced code block with the `donna` keyword (preferably TOML) that configures an artifact or its section.
- **Directive** — a Jinja2 helper like `donna.lib.view(...)` or `donna.lib.goto(...)` that adds meta information or special behavior to an artifact.
- **Environment error** — a structured, user-facing error describing problem in the environment Donna operates in (e.g., missing artifact, invalid config). These errors are expected to be handled by agents or users.
- **Head section** — the H1 section of a markdown artifact (before the first H2) that contains the primary description and mandatory config block.
- **Internal error** — an error caused by a bug or unexpected state in Donna itself. These errors are not expected to be handled by agents or users.
- **Protocol** — the output/interaction mode for Donna (e.g., `llm`) that governs CLI behavior and rendering.
- **Session** — the active unit of work tracked by Donna; its state and artifacts live in the `session` world and it always has exactly one active story.
- **Source** — the entity that implements logic of building an artifact from its raw data (text or binary).
- **Specification** — a text artifact of kind `donna.lib.specification` that documents behavior, rules, or project guidance.
- **Story** — a semantically consistent scope of work within a session; a conceptual unit not directly represented in the tool.
- **Tail section** — each H2 section of an artifact.
- **World** — a storage namespace (filesystem or other backends) that contains artifacts.
- **Workspace** — the `.donna` directory in a project root that stores Donna's configuration, worlds, and artifacts for that project.
- **Workflow** — a `donna.lib.workflow` artifact that encodes a finite-state machine of operations guiding the agent's work.
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
- `{{ donna.lib.view("project:core:error_handling") }}` when you need to implement any new feature in Donna that may produce, process or propagate errors.
