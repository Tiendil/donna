# `donna` Initialization

Initialization creates the Donna project config and optionally installs built-in Donna skills and specs into the project.

Use this document when a project has no `donna.toml`, when built-in Donna fixtures are missing, or when synced fixture files need to be refreshed.

## What Initialization Creates

`donna -p llm workspaces init` creates:

```text
<project-root>/donna.toml
<project-root>/.session/donna/
<project-root>/.agents/skills/
<project-root>/.agents/donna/
```

`donna.toml` stores configuration. The configured session directory stores Donna runtime state and session artifacts. The `.agents/skills` and `.agents/donna` directories contain built-in agent-facing Donna skills, workflows, and specifications.

## Initialize The Current Directory

Run from the directory that should become the project root:

```bash
donna -p llm workspaces init
```

This command fails if `donna.toml` already exists.

## Initialize Another Directory

Pass an explicit root directory:

```bash
donna -p llm --root /path/to/project workspaces init
```

The target directory must already exist. Donna creates `donna.toml` and the configured session directory inside it.

## Install Only Part Of The Fixtures

Skip built-in skills:

```bash
donna -p llm workspaces init --no-skills
```

Skip synced Donna specs and workflows:

```bash
donna -p llm workspaces init --no-specs
```

Use these options only when the project deliberately manages those files another way.

## Refresh Existing Fixtures

Use `update`, not `init`, for an existing Donna project:

```bash
donna -p llm workspaces update
```

Refresh only built-in skills:

```bash
donna -p llm workspaces update --no-specs
```

Refresh only synced Donna specs and workflows:

```bash
donna -p llm workspaces update --no-skills
```

`update` requires an existing `donna.toml`.

## First Checks After Initialization

Verify the project config can load:

```bash
donna -p llm sessions status
```

List available artifacts:

```bash
donna -p llm artifacts list '**'
```

List available workflows:

```bash
donna -p llm artifacts list '**' --predicate '"workflow" in section.tags'
```

Validate artifacts:

```bash
donna -p llm artifacts validate '**'
```

## Agent Guidance

Initialize Donna only when the developer asks for it or when the task explicitly requires Donna and no `donna.toml` exists.

Do not overwrite project-owned workflows or specifications by hand. Use `workspaces update` for built-in fixtures, and edit project-owned artifacts directly when the developer asks for project-specific behavior changes.
