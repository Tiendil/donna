# `donna` Artifacts

Donna artifacts are project files that Donna can discover, render, validate, and execute as workflow input. They are usually Markdown files with the `.donna.md` extension.

Donna reads artifacts from the project filesystem. It does not mutate project artifacts through artifact commands. Developers and agents edit files directly, then ask Donna to list workflows or validate artifacts.

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

## List Workflows

List workflow artifacts:

```bash
donna -p llm list
```

Read artifact source files directly when you need details beyond the workflow introduction.

## Validate Artifacts

Validate one artifact:

```bash
donna -p llm validate '@/workflows/polish.donna.md'
```

Validate all visible artifacts:

```bash
donna -p llm validate --all
```

Run validation after creating or editing Donna artifacts.

## Artifact IDs

Use `@/` for project-root artifact ids:

```bash
donna -p llm validate '@/workflows/polish.donna.md'
```

Validate multiple specific artifacts by passing multiple ids:

```bash
donna -p llm validate '@/workflows/polish.donna.md' './workflows/rfc/request.donna.md'
```

Artifact path arguments accept root-anchored paths such as `@/workflows/polish.donna.md`, relative paths such as `./workflows/polish.donna.md`, and absolute paths inside the project root.

## Creating Artifacts

Create normal documentation as plain Markdown files. A minimal documentation file:

````markdown
# Example Specification

This document describes one stable project rule.
````

Documentation files are not Donna artifacts and do not need artifact validation.

## Creating Workflows

A workflow artifact defines a finite-state machine. The H1 section is a workflow by default. Each H2 section declares one operation. When the H1 config omits `start_operation_id`, Donna starts from the first H2 section.

Minimal workflow:

````markdown
# Example Workflow

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
donna -p llm validate '@/workflows/example.donna.md'
```

Run it:

```bash
donna -p llm run '@/workflows/example.donna.md'
```

## Managing Artifacts

Use direct file edits to create, update, move, or delete artifact files. Then use Donna to inspect the result.

Recommended loop:

1. Edit the artifact source file.
2. Validate the artifact:

```bash
donna -p llm validate '@/specs/example.donna.md'
```

3. If it is a workflow, list it:

```bash
donna -p llm list
```

Keep artifact files concise. Put project-wide explanations in specifications and operational step-by-step instructions in workflows.
