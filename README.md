# Donna

**A CLI tool that helps agents keep long-running work on a predefined path.**

Donna exists because agent work has a control-flow problem:

1. Most development work is repetitive on the meta level: "run this tool, do something with the output, run another tool" or "implement function A, implement tests for function A, implement function B, …".
2. Some parts of that work require advanced reasoning, others do not.
3. Agents are ~~almost~~ good at reasoning, but not so good at keeping the whole process in mind, remembering what they did, etc.
4. Therefore, we should separate the reasoning part from the control flow part — let agents focus on what they are good at, and keep the control flow to traditional automation tools.

**Donna runs predefined workflows as deterministic state machines, so the agent can focus on reasoning, code generation, and other agentic work.**

You define a workflow in a single readable Markdown file. The agent asks Donna to guide it through the workflow, and Donna keeps the session state, chooses the next operation, and tells the agent what to do or report next.

Workflows can start child workflows, be generated on the fly, or be modified while executing. For example, you can have a workflow that guides the agent through the planning process, and at the final step, the agent can generate a new workflow with a detailed plan to execute and run it immediately.

As a bonus, **Donna saves tokens** because the agent does not need to reason about control flow or how to execute particular CLI commands and other automation tools.

## Features

- **Pure CLI tool** — No API keys, hosted services, or separate agent instances required.
- **Deterministic control flow** — Donna follows explicit workflow transitions instead of relying on the agent's memory.
- **Agent-aware automation** — Scripted steps run automatically; agent work is requested when needed.
- **Nested workflows** — Workflows can start child workflows, generate new ones, or delegate workflow selection to the agent.
- **Readable workflow sources** — Each workflow is a single Markdown file with a clear structure.
- **Built-in help for agents** — Your agent can run `donna skill` to get detailed docs written for agents.
- **Local session state** — Workflow progress stays inspectable and resumable inside the project.
- **Progress journaling** — Workflow progress can be logged through a configured external command.

## Example

I use Donna to develop Donna itself — you can find real examples of workflows in the [./workflows](./workflows) folder of this repository. You can start with [./workflows/polish.donna.md](./workflows/polish.donna.md) that loops over fixing issues found by formatters, linters, type checkers and tests until the codebase is polished.

Below you'll find a simplified workflow that checks the current time, asks the agent whether it is time to drink tea, and branches according to the agent's answer.

Here is its schema:

```
[Get Current Time]
          |
          v
   [Ask About Tea]
          |
     +----+----+
     |         |
    yes        no
     |         |
     v         |
  [Turn On     |
   Kettle]     |
     |         |
     +----+----+
          |
          v
       [Finish]

```

Actual workflow code:

````markdown
# Is it time to drink tea?

This workflow checks the current time, asks the agent whether it is tea time,
and branches on the answer.

## Get Current Time

```toml donna
id = "get_current_time"
kind = "donna.lib.run_script"
save_stdout_to = "current_time"
goto_on_success = "ask_about_tea"
goto_on_failure = "finish"
```

```bash donna script
#!/usr/bin/env bash
date +%H:%M
```

## Ask About Tea

```toml donna
id = "ask_about_tea"
kind = "donna.lib.request_action"
```

The current time is:

```text
{{ donna.lib.task_variable("current_time") }}
```

Is it time to drink tea?

1. If yes, `{{ donna.lib.goto("turn_on_kettle") }}`.
2. If no, `{{ donna.lib.goto("finish") }}`.

## Turn On Kettle

```toml donna
id = "turn_on_kettle"
kind = "donna.lib.request_action"
```

Turn on the kettle, then `{{ donna.lib.goto("finish") }}`.

## Finish

```toml donna
id = "finish"
kind = "donna.lib.finish"
```

The workflow is complete. You are a good butler.
````

<details>
  <summary>How it works</summary>

How to read workflow's source:

- The H1 section is the workflow section. It gives Donna the workflow title and summary that appear in `donna list`.
- Each H2 section is an operation section. Donna runs operations in the order selected by the workflow state machine.
- `toml donna` blocks configure section id, type and behavior. Here, the operation types are `donna.lib.run_script`, `donna.lib.request_action`, and `donna.lib.finish`.
- `Get Current Time` is a `run_script` operation. Donna runs the shell script from the project root, saves stdout as `current_time`, and moves to `ask_about_tea` on success. No agent interaction required here, because it is pure deterministic work.
- `Ask About Tea` is a `request_action` operation. The agent will see a request for action with the rendered current time, the question, and the two allowed transitions: `turn_on_kettle` or `finish`.
- `donna.lib.task_variable("current_time")` is rendered as the value captured from the script output.
- `donna.lib.goto(...)` is rendered as a concrete CLI command to execute.
- `Turn On Kettle` is another `request_action` operation. The agent will see the instruction to turn on the kettle and then complete the action request with the `finish` transition.
- `Finish` is a `finish` operation. The agent will see the final workflow message, and Donna will complete the workflow task.

Here is an example of action request for the `Get Current Time` operation:

````markdown
--DONNA-CELL OuP2T9brQYmvESMHsbrDlw BEGIN--
kind=session_state_status
media_type=text/markdown
pending_action_requests=1
queued_work_units=0
tasks=1

The session is AWAITING YOUR ACTION. You have pending action requests to address.

- If the developer asked you to start working on a new task, you MUST ask if you should start a new session
  or continue working on the current action requests.
- Otherwise, you MUST address the pending action requests before proceeding.
--DONNA-CELL OuP2T9brQYmvESMHsbrDlw END--

--DONNA-CELL fxh3PDZ1Qy-c3zvai_T5Qw BEGIN--
kind=action_request
media_type=text/markdown
action_request_id=AR-11-l

**This is an action request for the agent. You MUST follow the instructions below.**

The current time is:

```text
19:31

```

Is it time to drink tea?

1. If yes, `donna -p llm --config '/home/tiendil/repos/mine/donna/.session/readme-example-test/donna.toml' complete-action-request <action-request-id> '@/workflows/tea.donna.md:turn_on_kettle'`.
1. If no, `donna -p llm --config '/home/tiendil/repos/mine/donna/.session/readme-example-test/donna.toml' complete-action-request <action-request-id> '@/workflows/tea.donna.md:finish'`.
--DONNA-CELL fxh3PDZ1Qy-c3zvai_T5Qw END--

````

</details>

Since Donna is a CLI tool, you can run the workflow manually in the terminal.

```bash
uv tool install donna

# Example workflow is a part of Donna repository
# git clone git@github.com:Tiendil/donna.git
# cd donna

donna run @/workflows/examples/time_to_drink_tea.donna.md

# Follow Donna commands to finish the workflow.
```

## Installation

```bash
uv tool install donna

# or
# python -m pip install donna
```

Ask your agent to initialize Donna in the project:

```
1. Run `donna skill`
2. Initialize Donna in this project.
3. Add instructions on when and how to use Donna to the AGENTS.md file.
```

Or install Donna manually:

```bash
# from the root of your project
donna init
```

`donna init` will create a configuration file `donna.toml`, review it and edit if needed.

## Configuration

You can get detailed documentation by running `donna skill configuration` or asking your agent to do that.

A Donna project is configured by a TOML file named `donna.toml`. If `--config` is omitted, Donna searches upward from the current working directory until it finds `donna.toml`; the directory containing that file is the project root.

Minimal configuration:

```toml
version = 1
```

The starter configuration generated by `donna init` includes the default session directory and workflow discovery directories:

```toml
version = 1

session_dir = ".session/donna"

workflow_dirs = [
    "./workflows",
    "./.session/donna",
]
```

A coding agent can help create or adapt workflow files after the project layout and desired workflows are clear.

The session directory stores Donna runtime state. Workflow directories are scanned recursively for `.donna.md` files; missing workflow directories are ignored.

Detailed configuration behavior is specified in [./specs/behavior/config.md](./specs/behavior/config.md). Command behavior is specified in [./specs/behavior/cli.md](./specs/behavior/cli.md).

Project agent instructions can include a short Donna rule like this:

```markdown
Use Donna only when explicitly instructed by a developer, by project instructions, or by Donna itself.
Before using Donna in a session, read `donna -p llm skill usage`.
Use `donna -p llm ...` for agent-facing command output.
```

## Quick Usage

**In most cases your agent should be capable of using Donna by itself without your intervention.**

You can get detailed documentation by running `donna skill usage` or asking your agent to do that.

Detailed CLI interface is described in [./specs/behavior/cli.md](./specs/behavior/cli.md).

Create a starter configuration:

```bash
donna init
```

List discovered workflow artifacts:

```bash
donna list
```

Start a new session:

```bash
donna new-session
```

Start a workflow in the current session:

```bash
donna run @/workflows/polish.donna.md
```

Inspect the current session:

```bash
donna status
```

Continue queued workflow execution:

```bash
donna continue
```

Complete an action request with the id and next operation printed by Donna:

```bash
donna complete-action-request <action-request-id> @/workflows/example.donna.md:next_operation
```

Read the built-in usage documentation:

```bash
donna skill usage
```

## Workflow Files

**In most cases your agent should be capable of creating and managing workflows by itself without your intervention.**

You can get detailed documentation by running `donna skill workflows` or asking your agent to do that.

Donna workflow artifacts are Markdown files ending with `.donna.md`. Donna discovers them by recursively scanning the configured `workflow_dirs`.

A workflow file has one H1 section for the workflow and H2 sections for operations. Section config is written in fenced `toml donna` code blocks. Transitions are declared in operation config or request text, depending on the operation kind, and validated before execution.

Common built-in operation kinds:

- `donna.lib.request_action` pauses and asks the agent to perform work.
- `donna.lib.run_script` runs a deterministic shell script from the project root.
- `donna.lib.output` prints information and continues.
- `donna.lib.finish` finishes the workflow task.

## Specifications

Project behavior and architecture are specified in [./specs](./specs/). Start with [./specs/intro.md](./specs/intro.md) for the index.

## Development

Development commands are run through Docker-backed project scripts.

Run the full test suite:

```bash
./bin/dev-tests.sh
```

Run a specific development command inside the project container:

```bash
./bin/dev.sh uv run pytest
```

Run Donna from the current development checkout:

```bash
./bin/dev.sh uv run donna --help
```

The repository also uses Donna itself. Its local workflows live in [./workflows](./workflows/), and the current project configuration is [donna.toml](./donna.toml).

### Agent Harness

Check [AGENTS.md](./AGENTS.md) for the list of additional tools that agents will expect to be installed.
