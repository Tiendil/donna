# `donna` Usage

Donna is a CLI tool for orchestrating AI-agent work with project-local workflows, artifacts, and session state.

Use this document as the first reference for command usage. For narrower topics, use:

- `donna skill configuration` for `donna.toml`.
- `donna skill initialization` for creating or checking Donna project files.
- `donna skill artifacts` for artifact layout, discovery, and authoring rules.
- `donna skill usage` for this command overview.

## Project Root

Donna works inside a project root. If `--root/-r` is omitted, commands that load a project discover the project root by searching upward from the current directory for `donna.toml`.

Use `--root PATH` when running Donna from outside the project tree or when targeting a specific project:

```bash
donna -p llm --root /path/to/project sessions status
```

`donna skill ...` does not load a project config and can run from any directory.

## Output Protocols

Donna supports three protocol modes:

- `llm`: structured cells optimized for agents.
- `human`: compact terminal output for people.
- `automation`: output intended for programs.

Agents should use `-p llm` for normal Donna workflow commands:

```bash
donna -p llm sessions status
```

The root option goes before the command:

```bash
donna -p llm --root /path/to/project artifacts list
```

## Skill Documents

The `skill` command prints built-in agent documentation as plain Markdown. It does not require an initialized Donna project.

Examples:

```bash
donna skill usage
donna skill configuration
donna skill initialization
donna skill artifacts
```

Use these documents when an agent needs stable instructions before `donna.toml` exists or when synced artifacts are not available.

## Project Commands

Workspace commands create or check Donna project configuration.

Initialize Donna in the current directory:

```bash
donna -p llm workspaces init
```

Initialize Donna in an explicit existing directory:

```bash
donna -p llm --root /path/to/project workspaces init
```

## Session Commands

All workflow execution happens in the active session. Session state lives under the configured session directory, `.session/donna` by default.

Start a new session:

```bash
donna -p llm sessions start
```

Starting a session resets session state and removes session artifacts. Only start a new session when the developer asks for it or when no active session exists.

Show concise status:

```bash
donna -p llm sessions status
```

Show detailed session state and action requests:

```bash
donna -p llm sessions details
```

Continue queued workflow execution:

```bash
donna -p llm sessions continue
```

Run a workflow artifact:

```bash
donna -p llm sessions run @/workflows/polish.donna.md
```

Complete an action request by passing its id and the next operation id exactly as Donna instructed:

```bash
donna -p llm sessions action-request-completed AR-12-x @/.session/donna/workflow.donna.md:next_step
```

## Artifact Commands

Artifacts are `*.donna.md` project files under Donna's configured `workflow_dirs`. Agents use artifacts to discover workflows, read documentation, and validate Donna-readable files.

List workflows:

```bash
donna -p llm artifacts list
```

Validate all visible artifacts:

```bash
donna -p llm artifacts validate --all
```

Validate specific artifacts by absolute project-root id:

```bash
donna -p llm artifacts validate '@/workflows/polish.donna.md'
```

## Normal Agent Flow

1. Read project instructions and `donna skill usage`.
2. Check session state:

```bash
donna -p llm sessions status
```

3. If there is no active work and a workflow is needed, list workflows:

```bash
donna -p llm artifacts list
```

4. Start the selected workflow:

```bash
donna -p llm sessions run @/workflows/polish.donna.md
```

5. Execute Donna action requests exactly.
6. Report completion with `sessions action-request-completed`.
7. Continue until Donna finishes the workflow.

## Journal Forwarding

Donna creates internal journal records for workflow events. To forward them to another tool, configure `[journal].cmd` in `<project-root>/donna.toml`.

Example:

```toml
[journal]
cmd = ["./bin/taskwarior.sh", "log", "+journal", "+donna", "{message}"]
```

Supported placeholders are `timestamp`, `actor_id`, `message`, `current_task_id`, `current_work_unit_id`, and `current_operation_id`.
