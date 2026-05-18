# Instructions for the AI Agents

This document provides instructions and guidelines for the AI agents working on `donna`.

Every agent MUST follow these instructions.

## Project Overview

`donna` is a CLI tool that helps agents run predefined workflows in deterministic way.

Workflow is a state-machine / non-linear graph of operations that guides the agent's work. Each operation can run code, output text, provide instructions for the agent (to execute them and report back to Donna), or do other things. The agent's task is to follow the instructions of the operations and report back to Donna about the next operation to run.

Donna maintains the state of the workflow and the stack of operations.

So, you may look at `donna` as a Virtual Machine for agents, where agent is just one of the possible execution contexts, and workflows are programs that run in this VM.

## Source Of Truth

Project behavior and architecture are specified in `./specs/`.

Agents MUST read the relevant specifications before making changes.

Start from `./specs/intro.md` to find the relevant specification documents.

When adding, deleting, or significantly changing a specification, agents MUST update `./specs/intro.md`.

Agents MUST NOT create new specifications without explicit instructions.

Agents MUST NOT delete or significantly change existing specifications without explicit instructions.

## Development Environment

All development-related operations MUST be performed in Docker containers.

Agents MUST NOT perform development-related operations directly on the host machine.

Allowed development commands:

- `./bin/dev-tests.sh` — run all Python tests inside the container.
- `./bin/dev.sh` — run development utilities inside the container, for example `./bin/dev.sh uv run pytest`.
- `./bin/dev-build-containers.sh` — build base Docker images for development; use only after approved Docker or dependency changes.

Searching, reading, and editing repository files MAY be done on the host machine.

## Restricted Changes And Operations

Agents MUST NOT perform these operations without explicit permission:

- Change `docker-compose.yml` or Docker-related configuration.
- Change Docker runtime parameters such as resources or volumes.
- Change running Docker services unrelated to this project.
- Install new dependencies.
- Update lock files.
- Install new tools, utilities, or software on the host machine or in development containers.
- Change project structure by moving files or creating new top-level directories.

If one of these operations seems necessary, agents MUST ask for explicit permission before doing it.

## Implementation Guidance

Follow existing specifications and local project patterns.

Keep changes scoped to the requested task.

Do not implement behavior that is only mentioned as future or possible functionality unless explicitly requested.

When code is added, tests SHOULD follow `./specs/architecture/tests.md`.

When entities, errors, warnings, or module layout are affected, agents MUST check the corresponding architecture specs.

## Top priority tools

These tools MUST have the highest priority when an agent is deciding which tool to use for a given task:

### `donna`

We use Donna to develop Donna. We use the current development version of Donna. For convinience, use shortcut `./bin/donna.sh` to run current development version of Donna.

Use Donna to run workflows.

You may need to read the usage intructions for `donna`: `./bin/donna.sh -p llm skill usage` in these cases:

- You need to run a workflow first time in the session.
- You need to list available workflows first time in the session.

You run workflows only when explicitly instructed to do so by a developer or Donna itself. You MUST run workflows in that cases.

Donna is configured to log significant operation steps via `task` tool.

### `depmesh`

`depmesh` — a tool for discovering dependencies between project artifacts.

Agents MUST use `depmesh` for dependency types supported by its configuration.

At the start of each work session, read the `depmesh` usage instructions for details:

```bash
depmesh skill usage
```

### `ast-grep`

`ast-grep` — a tool for searching and manipulating Abstract Syntax Trees in code. Use it when you work with particular code patterns, structures, or constructs in the codebase.

You MUST use it to:

- Search for specific code patterns or structures in the codebase.
- Extract information from code, such as function definitions, variable declarations, or specific code constructs.
- Analyze code for specific patterns or anti-patterns, such as code smells, security vulnerabilities, performance issues, specific usage of libraries or APIs, etc.
- Refactor particular code patterns or structures across the codebase.
- Introduce new small behaviors or features into existing code.

You MUST NOT use it for:

- Implementing huge features or behaviors that require adding massive blocks of code (like adding a new class, module, writing a huge function, etc.).

### `task`

`task` — Taskwarrior — is the project journal for significant agent-side work.

You MUST use it to write journal records with these exact command templates from the project root:

```bash
./bin/taskwarior.sh log +journal +agent kind:goal "<goal description>"
./bin/taskwarior.sh log +journal +agent kind:step "<phase progress or completion handoff>"
./bin/taskwarior.sh log +journal +agent kind:thought "<important thought>"
./bin/taskwarior.sh log +journal +agent kind:assumption "<important assumption>"
./bin/taskwarior.sh log +journal +agent kind:change "<what changed and where>"
```

Journal messages MUST be single-line strings.

You MUST log:

- Goals of long-running agent-side operations with `kind:goal`.
- Significant steps of long-running operations with `kind:step`.
- Significant thoughts during long-running operations with `kind:thought`.
- Significant assumptions during long-running operations with `kind:assumption`.
- Changes in project source code or project structure with `kind:change`.

You MAY add extra tags after `+agent` and before the message:

```bash
./bin/taskwarior.sh log +journal +agent kind:<message-kind> +<extra-tag>... "<single-line journal message>"
```

For each non-trivial Donna action request or long-running agent task:

1. Write exactly one `goal` record at action-request or task start.
2. Write `step` records at significant phase boundaries.
3. Write `change` records after each meaningful source update batch.
4. Write one final `step` record immediately before reporting completion or handing work back to the developer.

You MUST consider these cases significant phase boundaries:

- A work phase expected to take more than 10 seconds.
- Transition from analysis or research to implementation.
- Transition to a new step in a multi-step process.
- Start or completion of a multi-file or multi-artifact change batch.
- A decision that changes implementation direction.

You MUST NOT log:

- CLI commands you execute.
- Elementary or trivial steps.

You can read the logged journal with:

```bash
./bin/journal-tail.py --lines 20
```

### `rg`

Use `rg` for text and file searches unless a structural code query is needed.

`ast-grep` has a higher priority than `rg` whenever a structural code query is needed.
