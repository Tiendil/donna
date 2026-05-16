# `donna` Workflows

Donna workflows are project files that Donna can discover, render, validate, and execute. They are usually Markdown files with the `.donna.md` extension.

Donna reads workflows from the project filesystem. It does not mutate project workflow files through workflow commands. Developers and agents edit files directly, then ask Donna to list workflows or validate them.

## Workflow Locations

The common workflow areas are:

- `<project-root>/workflows`: project-owned workflows.
- `<project-root>/.session/donna`: session workflows and active workflow state.

Project-local Donna documentation may also live under `<project-root>/.agents/donna` when present.

Example:

```text
workflows/polish.donna.md
workflows/rfc/request.donna.md
.session/donna/current_task.donna.md
```

Donna sees only `.donna.md` files under directories listed in `donna.toml:workflow_dirs`.

## List Workflows

List workflows:

```bash
donna -p llm list
```

Read workflow source files directly when you need details beyond the workflow introduction.

## Validate Workflows

Validate one workflow:

```bash
donna -p llm validate '@/workflows/polish.donna.md'
```

Validate all visible workflows:

```bash
donna -p llm validate --all
```

Run validation after creating or editing Donna workflows.

## Workflow IDs

Use `@/` for project-root workflow ids:

```bash
donna -p llm validate '@/workflows/polish.donna.md'
```

Validate multiple specific workflows by passing multiple ids:

```bash
donna -p llm validate '@/workflows/polish.donna.md' './workflows/rfc/request.donna.md'
```

Workflow path arguments accept root-anchored paths such as `@/workflows/polish.donna.md`, relative paths such as `./workflows/polish.donna.md`, and absolute paths inside the project root.

## Creating Workflows

A workflow defines a finite-state machine. The H1 section is a workflow by default. Each H2 section declares one operation. When the H1 config omits `start_operation_id`, Donna starts from the first H2 section.

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

## Managing Workflows

Use direct file edits to create, update, move, or delete workflow files. Then use Donna to inspect the result.

Recommended loop:

1. Edit the workflow source file.
2. Validate the workflow:

```bash
donna -p llm validate '@/workflows/example.donna.md'
```

3. List it:

```bash
donna -p llm list
```

Keep workflow files concise. Put project-wide explanations in specifications and operational step-by-step instructions in workflows.
