# `donna` Initialization

Initialization creates the Donna project config and session directory.

Use this document when a project has no `donna.toml`.

## What Initialization Creates

`donna -p llm workspaces init` creates:

```text
<project-root>/donna.toml
<project-root>/.session/donna/
```

`donna.toml` stores configuration. The configured session directory stores Donna runtime state and session artifacts.

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

## First Checks After Initialization

Verify the project config can load:

```bash
donna -p llm sessions status
```

List available workflows:

```bash
donna -p llm artifacts list
```

Validate artifacts:

```bash
donna -p llm artifacts validate --all
```

## Agent Guidance

Initialize Donna only when the developer asks for it or when the task explicitly requires Donna and no `donna.toml` exists.

Edit project-owned artifacts directly when the developer asks for project-specific behavior changes.
