# Donna

**A CLI tool that helps agents keep long-running work on a predefined path.**

Donna allows agents to execute deterministic workflows regardless of the complexity of the algorithm.

You can look at Donna as a co-processor for your agent that takes care of the control flow, so the agent can focus on the actual agentic work such as reasoning, code generation, etc.

You define a workflow in a single readable Markdown file, after that your agent may ask Donna to guide it through the workflow, and Donna will take care of the rest by given instructions to the agent on what to do at each step.

**Workflow is a state machine and Donna its interpreter.** That means agent can start child workflows from the parent workflow, write workflows on the fly, modify them while executing, etc.

For example, you can have a workflow that guides the agent through the planing process, and at the final step, the agent can generate a new workflow with a detailed plan to execute and run it immediately.

## Example

I use Donna to develop Donna itself — you can find real examples of workflows in the [./workflows](./workflows) folder of this repository. You can start with [./workflows/polish.donna.md](./workflows/polish.donna.md) that goes in loop over fixing issues found by formatters, linters, type checkers and tests until the codebase is polished.

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

How this example works:

- The H1 section is the workflow section. It gives Donna the workflow title and summary that appear in `donna list`.
- Each H2 section is an operation section. Donna runs operations in the order selected by the workflow state machine.
- `toml donna` blocks configure section type and behavior. Here, the operation types are `donna.lib.run_script`, `donna.lib.request_action`, and `donna.lib.finish`.
- `Get Current Time` is a `run_script` operation. Donna runs the shell script from the project root, saves stdout as `current_time`, and moves to `ask_about_tea` on success. No agent interaction required here, because it is pure deterministic work.
- `Ask About Tea` is a `request_action` operation. The agent will see the rendered current time, the question, and the two allowed transitions: `turn_on_kettle` or `finish`.
- `donna.lib.task_variable("current_time")` is rendered for the agent as the value captured from the script output.
- `donna.lib.goto(...)` is rendered for the agent as a concrete CLI command to exectute.
- `Turn On Kettle` is another `request_action` operation. The agent will see the instruction to turn on the kettle and then complete the action request with the `finish` transition.
- `Finish` is a `finish` operation. The agent will see the final workflow message, and Donna will complete the workflow task.

For example, here what the agent will see on the `Get Current Time` step of the tea workflow:

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

## Rationale

Many project workflows are partly deterministic and partly judgment-based. Running formatters, validators, tests, or small scripts is deterministic. Deciding how to fix a failed check, adjust a design, or judge whether a result satisfies a requirement needs an agent.

Donna separates those concerns without requiring an API key, a hosted service, or a separate orchestrator:

- workflow files define the allowed control flow.
- Donna runs deterministic operations and preserves session state.
- action requests pause execution and ask the agent to do the non-deterministic work.
- the agent completes each request by choosing one of the workflow's declared next operations.

This keeps long-running work explicit, resumable, and easier to validate, while leaving judgment and file edits with the agent.

## Features

- CLI workflow runner for coding agents and humans supervising them.
- Project-local configuration with `donna.toml`.
- Markdown workflow artifacts ending with `.donna.md`.
- Session state stored under the configured `session_dir`.
- Workflow discovery from configured `workflow_dirs`.
- Built-in operation kinds for requesting agent action, running shell scripts, printing output, and finishing workflow tasks.
- Artifact listing, rendering, and validation commands.
- Human, LLM, and JSON Lines automation output protocols.
- Built-in skill-style documentation through `donna skill ...`.
- Optional journal forwarding through `donna.toml`.

## Quick Usage

Create a starter configuration:

```bash
donna init
```

List discovered workflow artifacts:

```bash
donna list
```

Validate every discovered workflow artifact:

```bash
donna validate --all
```

Render a workflow as Donna sees it:

```bash
donna render @/workflows/polish.donna.md --mode view
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
donna complete-action-request AR-12-x @/workflows/example.donna.md:next_operation
```

Read the built-in usage documentation:

```bash
donna skill usage
```

Useful related commands:

```bash
donna status
donna details
donna new-session
donna version
```

For coding agents, put global options before the subcommand:

```bash
donna -p llm --config /path/to/project/donna.toml status
```

## Installation

Install Donna from PyPI with `uv`:

```bash
uv tool install donna
```

Install Donna from PyPI with `pip`:

```bash
python -m pip install donna
```

Donna requires Python 3.12 or newer.

After installation, initialize a project from the directory that should contain `donna.toml`:

```bash
donna init
```

Review the generated configuration before relying on it. The starter file is intentionally small and may need project-specific workflow directories or journal forwarding.

## Configuration

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

Review and edit the starter configuration for the project. A coding agent can help create or adapt workflow files after the project layout and desired workflows are clear.

The session directory stores Donna runtime state. Workflow directories are scanned recursively for `.donna.md` files; missing workflow directories are ignored.

Detailed configuration behavior is specified in [specs/behavior/config.md](./specs/behavior/config.md). Command behavior is specified in [specs/behavior/cli.md](./specs/behavior/cli.md).

Project agent instructions can include a short Donna rule like this:

```markdown
Use Donna only when explicitly instructed by a developer, by project instructions, or by Donna itself.
Before using Donna in a session, read `donna -p llm skill usage`.
Use `donna -p llm ...` for agent-facing command output.
```

## Workflow Files

Donna workflow artifacts are Markdown files ending with `.donna.md`. Donna discovers them by recursively scanning the configured `workflow_dirs`.

A workflow file has one H1 section for the workflow and H2 sections for operations. Section config is written in fenced `toml donna` code blocks. Transitions are declared in operation config or request text, depending on the operation kind, and validated before execution.

Common built-in operation kinds:

- `donna.lib.request_action` pauses and asks the agent to perform work.
- `donna.lib.run_script` runs a deterministic shell script from the project root.
- `donna.lib.output` prints information and continues.
- `donna.lib.finish` finishes the workflow task.

Artifact ids are project-root anchored paths such as:

```text
@/workflows/polish.donna.md
```

Artifact section ids append a section id:

```text
@/workflows/polish.donna.md:finish
```

Read the detailed workflow documentation with:

```bash
donna skill workflows
```

The built-in skill documentation set is specified in [specs/behavior/skill_fixtures.md](./specs/behavior/skill_fixtures.md).

## Specifications

Project behavior and architecture are specified in [specs/](./specs/). Start with [specs/intro.md](./specs/intro.md) for the index.

Important references:

- [specs/behavior/cli.md](./specs/behavior/cli.md) describes CLI commands, output protocols, and command behavior.
- [specs/behavior/config.md](./specs/behavior/config.md) describes `donna.toml`.
- [specs/behavior/file_paths.md](./specs/behavior/file_paths.md) describes project paths, artifact ids, and artifact section ids.
- [specs/behavior/skill_fixtures.md](./specs/behavior/skill_fixtures.md) describes built-in documentation fixtures.
- [specs/documentation/readme.md](./specs/documentation/readme.md) describes this README's required structure and content.

The root README is an introduction, not the source of truth for detailed behavior.

## Development

Development commands are run through Docker-backed project scripts.

Run the full test suite:

```bash
./bin/dev-tests.sh
```

Run a specific development command inside the project container:

```bash
./bin/dev.sh poetry run pytest
```

Run Donna from the current development checkout:

```bash
./bin/dev.sh poetry run donna --help
```

The repository also uses Donna itself. Its local workflows live in [workflows/](./workflows/), and the current project configuration is [donna.toml](./donna.toml).
