# `donna` Artifacts

Donna artifacts are project files that Donna can discover, render, validate, and execute as workflow input. They are usually Markdown files with the `.donna.md` extension.

Donna reads artifacts from the project filesystem. It does not mutate project artifacts through `artifacts` commands. Developers and agents edit files directly, then ask Donna to list, view, or validate them.

## Artifact Locations

The common artifact areas are:

- `<project-root>/workflows`: project-owned workflows.
- `<project-root>/.agents/donna`: project-local Donna documentation, when present.
- `<project-root>/.session/donna`: session artifacts and active workflow state.

Example:

```text
workflows/polish.donna.md
workflows/rfc/request.donna.md
.session/donna/current_task.donna.md
```

Donna sees only `.donna.md` files under directories listed in `donna.toml:workflow_dirs`.

## List Artifacts

List all visible artifacts:

```bash
donna -p llm artifacts list '**'
```

List Donna Markdown artifacts:

```bash
donna -p llm artifacts list '**/*.donna.md'
```

List workflow artifacts:

```bash
donna -p llm artifacts list '**' --predicate '"workflow" in section.tags'
```

## View Artifacts

View rendered artifact content when you need information from an artifact:

```bash
donna -p llm artifacts view '@/workflows/polish.donna.md'
```

View all matching artifacts:

```bash
donna -p llm artifacts view '**/*.donna.md'
```

Agents should prefer rendered views for reading Donna artifacts. Read plain `.md` documentation files directly.

## Validate Artifacts

Validate one artifact:

```bash
donna -p llm artifacts validate '@/workflows/polish.donna.md'
```

Validate all visible artifacts:

```bash
donna -p llm artifacts validate '**'
```

Run validation after creating or editing Donna artifacts.

## Artifact Patterns

Use `@/` for project-root paths:

```bash
donna -p llm artifacts view '@/workflows/polish.donna.md'
```

Use recursive wildcards when the exact location is unknown:

```bash
donna -p llm artifacts list '**/*.donna.md'
```

Pattern examples:

- `@/*.donna.md`: Donna Markdown artifacts directly under the project root.
- `@/**/polish.donna.md`: any artifact named `polish.donna.md`.
- `@/workflows/**`: project workflow artifacts.
- `@/.session/donna/**`: session artifacts.

Do not pass relative filesystem paths such as `./workflows/polish.donna.md`. Use `@/workflows/polish.donna.md`.

## Creating Artifacts

Create normal documentation as plain Markdown files. A minimal documentation file:

````markdown
# Example Specification

This document describes one stable project rule.
````

Documentation files are not Donna artifacts and do not need artifact validation.

## Creating Workflows

A workflow artifact defines a finite-state machine. The head section declares workflow metadata and the start operation. Each H2 section declares one operation.

Minimal workflow:

````markdown
# Example Workflow

```toml donna
kind = "donna.lib.workflow"
tags = ["workflow"]
start_operation_id = "ask_agent"
```

This workflow asks the agent to do one thing and finish.

## Do The Work

```toml donna
id = "ask_agent"
kind = "donna.lib.request_action"
```

Perform the requested change.

When done, continue with `{{ donna.lib.goto("finish") }}`.

## Finish

```toml donna
id = "finish"
kind = "donna.lib.finish"
```

The workflow is complete.
````

Validate the workflow before running it:

```bash
donna -p llm artifacts validate '@/workflows/example.donna.md'
```

Run it:

```bash
donna -p llm sessions run '@/workflows/example.donna.md'
```

## Managing Artifacts

Use direct file edits to create, update, move, or delete artifact files. Then use Donna to inspect the result.

Recommended loop:

1. Edit the artifact source file.
2. View the rendered artifact:

```bash
donna -p llm artifacts view '@/specs/example.donna.md'
```

3. Validate the artifact:

```bash
donna -p llm artifacts validate '@/specs/example.donna.md'
```

4. If it is a workflow, list it with the workflow predicate:

```bash
donna -p llm artifacts list '**' --predicate '"workflow" in section.tags'
```

Keep artifact files concise. Put project-wide explanations in specifications and operational step-by-step instructions in workflows.
