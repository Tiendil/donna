# `donna` Usage

`donna` is a command line tool that helps agents run predefined workflows in a deterministic way.

Treat Donna as a small workflow virtual machine for agents. A workflow is a state machine stored in project-local Donna artifacts. Donna maintains the active session state, runs workflow operations, asks the agent to apply judgment or perform work when fully deterministic execution is not enough, and waits for the agent to report which operation to run next.

Donna does not replace the agent. The agent is still responsible for reading project instructions, doing the requested work, running tools, making code changes, and reporting results. Donna serves the control-flow role: it keeps the workflow path explicit, validated, resumable, and less dependent on the agent remembering every process step.

## This Documentation

This output is built-in skill-style documentation printed by:

```bash
donna -p llm skill usage
```

Use it as the first reference for agent-side command usage in a session. Use the other built-in skill documents for narrower tasks:

- `donna -p llm skill configuration` explains `donna.toml`.
- `donna -p llm skill initialization` explains project initialization.
- `donna -p llm skill workflows` explains Donna workflow format, layout, execution and creation best practices.
- `donna -p llm skill usage` prints this document.

## Output Protocols

Donna supports three protocol modes:

- `llm`: structured cell output intended for agents.
- `human`: compact terminal output intended for people.
- `automation`: JSON Lines output intended for programs.

Use `llm` when invoking `donna` as a coding agent. It is the normal choice for this documentation's examples.

Use `human` for compact terminal inspection by a person.

Use `automation` when an agent or another program needs automatic processing of Donna output. Automation output is JSON Lines: each stdout line is one JSON object representing one Donna output cell or journal record.

Example automation command:

```bash
donna -p automation list
```

Example automation output:

```jsonl
{"artifact_id":"@/workflows/polish.donna.md","artifact_kind":"donna.lib.workflow","artifact_title":"Polishing Workflow","content":"Initiate operations to polish and refine the codebase.","id":"WxVlGyfwTs-vnaTh6c46ww"}
{"artifact_id":"@/workflows/rfc/request.donna.md","artifact_kind":"donna.lib.workflow","artifact_title":"Create a Request for Change","content":"This workflow creates a Request for Change document.","id":"gPY_FHlISKu7HOphsyj-kQ"}
```

Global options go before the subcommand:

```bash
donna -p llm --root /path/to/project status
```

## Project Root

Most commands need a Donna project. If `--root/-r` is omitted, Donna discovers the project root by searching upward from the current working directory for `donna.toml`.

Use `--root PATH` when running from outside the intended project tree or when there is any ambiguity:

```bash
donna -p llm --root /path/to/project list
```

Donna uses project-root anchored ids for workflow artifacts. The `@/` prefix means "from the Donna project root":

```bash
donna -p llm run @/workflows/some-workflow.donna.md
```

Relative artifact paths passed to CLI commands are resolved from the process current working directory, then normalized to project-root anchored ids. Absolute artifact paths are accepted only when they point inside the Donna project root. Prefer `@/` paths in agent notes and workflow instructions because they are independent of the current working directory.

Artifact section ids append `:section_id` to an artifact id:

```bash
donna -p llm complete-action-request AR-12-x @/.session/donna/workflow.donna.md:next_step
```

`donna skill ...` and `donna init` do not require an existing Donna project config.

## Agent Safety Rules

1. Read the project's own agent instructions before using Donna.
2. Use `-p llm` unless a human explicitly asks for human output or a program needs automation output.
3. Run `status` before deciding what to do with a session.
4. If Donna says the session is awaiting your action, address the pending action requests before unrelated work.
5. If the developer asks for new work while Donna has pending work units or action requests, ask whether to continue the current session or start a new one.
6. Run workflows only when explicitly instructed by the developer, project instructions, or Donna.
7. Use the action request id and next operation id exactly as Donna provides them. Do not invent operation ids.
8. Do not run `new-session` unless you understand the consequence and the developer or project instructions allow it.

## Usage Patterns

### Workflow Execution

Workflow execution means Donna drives operations until the workflow finishes, reports an error, or asks the agent to perform work. The command that starts workflow execution is:

```bash
donna -p llm run @/path/to/workflows/<workflow>.donna.md
```

`run` starts the workflow in the current session. Donna then executes workflow operations until it needs agent work, finishes, or reports an error. Some operations may take time because they run scripts, validators, formatters, tests, or other tools. Wait for the command to finish and read all emitted cells before deciding what to do next.

When Donna emits an action request, perform the requested work exactly. Action requests include an id and allowed next operation choices. After finishing the requested work, report the action request completion with the id and next operation that matches the result:

```bash
donna -p llm complete-action-request AR-12-x @/.session/donna/workflow.donna.md:next_step
```

`complete-action-request` removes the action request, queues the selected next operation, and continues workflow execution immediately. It may finish the workflow, emit another action request, or run more deterministic operations before returning.

The workflow is finished when Donna emits the workflow's finish message, when `status` says the session is idle with no active tasks, or when Donna explicitly tells you to report back:

```bash
donna -p llm status
```

When the workflow is finished, report the result to the developer before starting unrelated work.

### Nested Workflows

Donna can have multiple active workflows in one session. Treat them as a call stack: starting a workflow while another workflow is active makes the new workflow current; finishing it returns control to the parent workflow.

A parent action request may instruct you to run a child workflow. In that case:

1. Start the child workflow with `donna -p llm run ...`.
2. Complete the child workflow before completing the parent action request.
3. Do not report the parent action request as complete just because the child workflow started.
4. After the child finishes, return to the parent action request and choose one of its declared transitions.
5. Keep child workflow outputs explicit: write files, update notes, or summarize results before completing the parent request.

### Start Workflow

A developer or project instruction explicitly asks you to run a Donna workflow, and Donna has no active work that must be continued first.

Read project instructions and this usage document if you have not already:

```bash
donna -p llm skill usage
```

Inspect the current session before starting anything:

```bash
donna -p llm status
```

If Donna reports pending work units or action requests, do not start unrelated work silently. Ask whether to continue the current session or start a new one.

List available workflows if you have not been given a specific workflow to run:

```bash
donna -p llm list
```

Run the selected workflow, then follow the workflow execution rules above:

```bash
donna -p llm run @/path/to/workflows/<workflow>.donna.md
```

### Continue Workflow

Donna has queued work units, pending action requests, a workflow command tells you to continue, or the developer asks you to continue the current Donna workflow.

Inspect the current session:

```bash
donna -p llm status
```

Continue queued workflow execution:

```bash
donna -p llm continue
```

Strictly follow every instruction Donna gives you after that. If Donna finishes the workflow or tells you to report back, do so before doing anything else.

### Creating New Workflow

A developer or an active Donna workflow asks you to create or modify a workflow.

Read the workflow creation instructions if you have not already:

```bash
donna -p llm skill workflows
```

Create or edit the workflow source file directly. Choose the target location by this priority:

1. Use the explicitly specified filepath when the developer, project instructions, or parent workflow provides one.
2. For a temporary workflow, use a directory configured for temporary files or session artifacts.
3. For a temporary workflow if no directory for temporary files or session artifacts is configured, use the donna session directory, you can find it in `donna.toml`.
4. For a permanent workflow, use one of the directories where project-owned workflows are stored. Check `donna.toml` when the project-owned workflow directories are not obvious.

Validate the workflow:

```bash
donna -p llm validate @/workflows/example.donna.md
```

If the workflow should be discoverable, list workflows and confirm it appears with the expected summary:

```bash
donna -p llm list
```

## Session Commands

All workflow execution happens in the active session. Session state and session-created artifacts live under the configured session directory.

Donna automatically creates empty session state when a session-aware command needs it and no session state exists.

Create a fresh session:

```bash
donna -p llm new-session
```

`new-session` creates or **resets** Donna session state. Use it only when starting fresh work is intended.

Show concise session status, including whether Donna is idle, has queued work units, or is awaiting action:

```bash
donna -p llm status
```

Show detailed session state and pending action requests:

```bash
donna -p llm details
```

Continue queued workflow execution and emit the next action request if a workflow reaches one:

```bash
donna -p llm continue
```

Run a workflow artifact in the current session:

```bash
donna -p llm run @/workflows/polish.donna.md
```

Complete an action request:

```bash
donna -p llm complete-action-request AR-12-x @/.session/donna/workflow.donna.md:next_step
```

The first argument is the action request id. The second argument is an artifact section id in `artifact:section` form. Prefer copying the exact completion command or next operation id from Donna's action request output.

## Workflow Commands

Donna workflows are `*.donna.md` files discovered under the configured `workflow_dirs`. Workflow ids are project-root anchored paths such as `@/workflows/polish.donna.md`. Section ids append `:section_id`, for example `@/workflows/polish.donna.md:finish`.

List available workflows and their summaries:

```bash
donna -p llm list
```

Render a workflow to debug how Donna sees it:

```bash
donna -p llm render @/workflows/polish.donna.md --mode view
```

Use `render` when a workflow does not validate, an operation displays unexpected instructions, or a directive does not behave as expected.

Render modes:

- `view`: Use to see how Donna will render workflow instructions to the agent. This is the safest mode for inspecting the workflow text and generated agent-facing instructions.
- `execute`: Use when debugging the exact operation text Donna would execute in the current session context. This mode may fail when the workflow references data that is expected to exist on the current session stack.
- `analysis`: Use when inspecting machine-readable directive behavior, workflow transitions, and validation-related rendering.

Validate all discovered workflows:

```bash
donna -p llm validate --all
```

Validate specific workflows:

```bash
donna -p llm validate @/workflows/polish.donna.md
```

Workflow arguments accept root-anchored ids, relative paths, and absolute paths inside the project root. Prefer root-anchored ids in notes and agent instructions because they remain stable when the current directory changes.

## Project Commands

Initialize Donna in the current directory:

```bash
donna -p llm init
```

Initialize Donna in an explicit directory:

```bash
donna -p llm --root /path/to/project init
```

`init` creates or refreshes Donna project configuration. Read `donna -p llm skill initialization` and project instructions before using it in an existing repository.

Print the installed Donna package version:

```bash
donna version
```

## Journal Forwarding

Donna creates internal journal records for significant workflow events. Projects can forward those records to another tool by configuring `journal.cmd` in `donna.toml`.

Example:

```toml
[journal]
cmd = ["./bin/taskwarior.sh", "log", "+journal", "+donna", "{message}"]
```

Supported placeholders are `timestamp`, `actor_id`, `message`, `current_task_id`, `current_work_unit_id`, and `current_operation_id`.

When no journal command is configured, Donna still prints newly created internal journal records through the selected protocol formatter.
