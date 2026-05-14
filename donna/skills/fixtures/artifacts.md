# `donna` Artifacts

Donna artifacts are project files that Donna can discover, render, validate, and execute as workflow input. They are usually Markdown files with the `.donna.md` extension.

Donna reads artifacts from the project filesystem. It does not mutate project artifacts through `artifacts` commands. Developers and agents edit files directly, then ask Donna to list, view, or validate them.

## Artifact Locations

The common artifact areas are:

- `<project-root>/specs`: project-owned specifications and workflows.
- `<project-root>/.agents/donna`: synced built-in Donna specs and workflows.
- `<project-root>/.session/donna`: session artifacts and active workflow state.

Example:

```text
specs/intro.donna.md
.agents/donna/work/polish.donna.md
.session/donna/current_task.donna.md
```

Donna sees only files allowed by `donna.toml:file_filters`.

## List Artifacts

List all visible artifacts:

```bash
donna -p llm artifacts list '**'
```

List introductions:

```bash
donna -p llm artifacts list '**/intro.donna.md'
```

List workflow artifacts:

```bash
donna -p llm artifacts list '**' --predicate '"workflow" in section.tags'
```

## View Artifacts

View rendered artifact content when you need information from an artifact:

```bash
donna -p llm artifacts view '@/specs/intro.donna.md'
```

View all matching introductions:

```bash
donna -p llm artifacts view '**/intro.donna.md'
```

Agents should prefer rendered views for reading. Read source files directly only when editing the artifact or investigating rendering problems.

## Validate Artifacts

Validate one artifact:

```bash
donna -p llm artifacts validate '@/specs/intro.donna.md'
```

Validate all visible artifacts:

```bash
donna -p llm artifacts validate '**'
```

Run validation after creating or editing Donna artifacts.

## Artifact Patterns

Use `@/` for project-root paths:

```bash
donna -p llm artifacts view '@/specs/core/top_level_architecture.donna.md'
```

Use recursive wildcards when the exact location is unknown:

```bash
donna -p llm artifacts list '**/*.donna.md'
```

Pattern examples:

- `@/*.donna.md`: Donna Markdown artifacts directly under the project root.
- `@/**/intro.donna.md`: any introduction artifact.
- `@/.agents/donna/**`: synced Donna artifacts.
- `@/.session/donna/**`: session artifacts.

Do not pass relative filesystem paths such as `./specs/intro.donna.md`. Use `@/specs/intro.donna.md`.

## Creating Artifacts

Create artifacts as source files in an included location. A minimal specification artifact:

````markdown
# Example Specification

```toml donna
kind = "donna.lib.specification"
tags = ["specification"]
```

This artifact documents one stable project rule.
````

After creating it, validate:

```bash
donna -p llm artifacts validate '@/specs/example.donna.md'
```

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
donna -p llm artifacts validate '@/specs/work/example.donna.md'
```

Run it:

```bash
donna -p llm sessions run '@/specs/work/example.donna.md'
```

## Managing Artifacts

Use direct file edits to create, update, move, or delete artifact sources. Then use Donna to inspect the result.

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
