# Donna Usage Instructions

```toml donna
kind = "donna.lib.specification"
```

This document describes how agents MUST use Donna CLI to manage and perform their workflows.

**Agents MUST follow the instructions and guidelines outlined in this document precisely.**

## Overview

`donna` is a CLI tool that helps manage the work of AI agents like OpenAI Codex.

It is designed to invert control flow: instead of agents deciding what to do next, the Donna tells agents what to do. The tool achieves this by following predefined workflows that describe how to perform various tasks. One may look at workflows as hierarchical state machines (HSM) that guide agents through complex processes step by step.

The core idea is that most high-level workflows are more algorithmic than it may seem at first glance. For example, it may be difficult to fix a particular problem in the codebase, but the overall process of polishing it is quite linear:

1. Run tests, if they fail, fix the problems.
2. Format the code.
3. Run linters, if there are issues, fix them.
4. Go to the step 1 if you changed something in the process.
5. Finish.

We may need coding agents on the each step of the process, but there no reason for agents to manage the whole loop by themselves — it takes longer time, spends tokens and confuses agents because they need to reason over long contexts.

## Primary rules for agents

- Donna stores all project-related data in `.donna` directory in the project root.
- All work is always done in the context of a session. There is only one active session at a time.
- You MUST always work on one task assigned to you.
- You MUST keep all the information about the session in your memory.
- You always can ask the `donna` tool for the session details if you forget something.

## CLI

### Protocol

Protocol selects the output formatting and behavior of Donna's CLI for different consumers (humans, LLMs, automation).
When an agent invokes Donna, it SHOULD use the `llm` protocol (pass an `-p llm` argument) unless the developer explicitly instructs otherwise.

### Project root

`-r <project-root>` sets the project root explicitly for any command (long form: `--root`).
If it is omitted, Donna discovers the project root by searching from the current working directory upwards for the `.donna` workspace directory.
Use this option when you run Donna from outside the project tree or when you want to target a specific project.

### Protocol cells

Donna communicates its progress and requests by outputting inrofmation organized in "cells". There are two kinds of cells output:

- Log cells — `DONNA LOG: <log-message>` — one line messages describing what Donna is doing. Mostly it is an information about the next operation being executed.
- Info cells — multiline cells with structured header and freeform body.

An example of an info cell:

```
--DONNA-CELL eZVkOwNPTHmadXpaHDUBNA BEGIN--
kind=action_request
media_type=text/markdown
action_request_id=AR-65-bd

<here goes the multiline markdown content of the action request>

--DONNA-CELL eZVkOwNPTHmadXpaHDUBNA END--
```

Donna can omit log cell start and end markers if a command produces only a single cell.

Donna renders cells differently, depending on the protocol used.

### Commands

There are three sets of commands:

- `donna -p <protocol> workspaces …` — manages workspaces. Most-likely it will be used once per your project to initialize it.
- `donna -p <protocol> sessions …` — manages sessions. You will use these commands to start, push forward, and manage your work.
- `donna -p <protocol> artifacts …` — manages artifacts. You will use these commands to read and update artifacts you are working with.

Use:

- `donna -p <protocol> <command> --help` to get the list of available subcommands.
- `donna -p <protocol> <command> <subcommand> --help` to get the help on specific subcommand.

### Workspaces

Run `donna -p <protocol> workspaces init [<directory-path>]` to initialize Donna workspace in the given directory. If `<directory-path>` is omitted, Donna will initialize workspace in the current working directory.

It is a one time operation you need to perform once per project to create a place where Donna will store all its data.

### Starting sessions

The developer is responsible for starting a new session.

You are allowed to start a new session in the next cases:

1. There is no active session.
2. The developer explicitly instructed you to start a new session.

You start session by calling `donna -p <protocol> sessions start`.

### Session flow

After the session starts you MUST follow the next workflow to perform your work:

1. List all possible workflows with command `donna -p <protocol> artifacts list`.
2. Choose the most appropriate workflow for the task you are going to work on or ask the developer if you are not sure which workflow to choose.
3. Start chosen workflow by calling `donna -p <protocol> sessions run <workflow-id>`.
4. Donna will output descriptions of all operations it performs to complete the work.
5. Donna will output **action requests** that you MUST perform. You MUST follow these instructions precisely.
6. When you done processing an action request, call `donna -p <protocol> sessions action-request-completed <action-request-id> <next-full-operation-id>` to report request completion. `<next-full-operation-id>` MUST contain full identifier of the next operation, like `<world>:<artifact>:<operation-id>`.
7. After you complete an action request, Donna will continue workflow execution and output what you need to do next.

You MUST continue following Donna's instructions until the workflow is completed.

### Session state

- `donna -p <protocol> sessions status` — get the status of the current session.
- `donna -p <protocol> sessions details` — get detailed information about the current session, including list of active action requests.
- `donna -p <protocol> sessions start` — start a new session. This command resets session state AND removes all session-level artifacts.
- Run `donna -p <protocol> sessions reset` to reset the current session. This command resets session state BUT keeps all session-level artifacts. Use this command when you need to restart the worklow but keep all the artifacts you created during the session.

### Starting work

If the developer asked you to do something new:

- Run `donna -p <protocol> sessions status` to get the status of the current session.
- If there is no active session, start a new session by calling `donna -p <protocol> sessions start`.
- If the session is active and there are unfinished work in it, you MUST ask the developer whether to continue the work in the current session or start a new one.
- If the session is active and there are no unfinished work in it, follow the instructions in the `Session flow` section to choose and start a new workflow.

### Continuing work

If the developer asked you to continue your work, you MUST call `donna -p <protocol> sessions continue` to get your instructions on what to do next.

If Donna tells you there is no work left, you MUST inform the developer that there is no work left in the current session.

### Working with artifacts

An artifact is a markdown document with extra metadata stored in one of the Donna's worlds.

Use the next commands to work with artifacts:

- `donna -p <protocol> artifacts list [<artifact-pattern>]` — list all artifacts corresponding to the given pattern. If `<artifact-pattern>` is omitted, list all artifacts in all worlds. Use this command when you need to find an artifact or see what artifacts are available.
- `donna -p <protocol> artifacts view <artifact-pattern>` — get the meaningful (rendered) content of all matching artifacts. This command shows the rendered information about each artifact. Use this command when you need to read artifact content.
- `donna -p <protocol> artifacts fetch <world>:<artifact>` — download the original source of the artifact content, outputs the file path to the artifact's copy, you can change. Use this command when you need to change the content of the artifact.
- `donna -p <protocol> artifacts tmp <slug>.<extension>` — create a temporary file for artifact-related work and output its path.
- `donna -p <protocol> artifacts update <world>:<artifact> <file-path>` — upload the given file as the artifact. Use this command when you finished changing the content of the artifact.
- `donna -p <protocol> artifacts copy <artifact-id-from> <artifact-id-to>` — copy an artifact source to another artifact ID (can be in a different world). This overwrites the destination if it exists.
- `donna -p <protocol> artifacts move <artifact-id-from> <artifact-id-to>` — copy an artifact source to another artifact ID and remove the original. This overwrites the destination if it exists.
- `donna -p <protocol> artifacts remove <artifact-pattern>` — remove artifacts matching a pattern. Use this command when you need to delete artifacts.
- `donna -p <protocol> artifacts validate <world>:<artifact>` — validate the given artifact to ensure it is correct and has no issues.
- `donna -p <protocol> artifacts validate-all [<artifact-pattern>]` — validate all artifacts corresponding to the given pattern. If `<artifact-pattern>` is omitted, validate all artifacts in all worlds.

Commands that accept an artifact pattern (`artifacts list`, `artifacts view`, `artifacts remove`, `artifacts validate-all`) also accept a repeatable `--tag <tag>` option to filter by artifact tags. When multiple tags are provided, only artifacts that include **all** specified tags are matched.

The format of `<artifact-pattern>` is as follows:

- full artifact identifier: `<world>:<artifact>`
- `*` — single wildcard matches a single level in the artifact path. Examples:
  - `*:artifact:name` — matches all artifacts named `artifact:name` in all worlds.
  - `world:*:name` — matches all artifacts with id `something:name` in the `world` world.
- `**` — double wildcard matches multiple levels in the artifact path. Examples:
  - `**:name` — matches all artifacts with id ending with `:name` in all worlds.
  - `world:**` — matches all artifacts in the `world` world.
  - `world:**:name` — matches all artifacts with id ending with `:name` in the `world` world.

## IMPORTANT ON DONNA TOOL USAGE

**Strictly follow described command syntax**

**You MUST follow `donna` call conventions specified in**, by priority:

  1. Direct instructions from the developer.
  2. `AGENTS.md` document.
  3. Specifications in `project:` world.
  4. This document.

**All Donna CLI commands MUST include an explicit protocol selection using `-p <protocol>`.** Like `donna -p llm <command>`.

**All Donna CLI commands MUST be run from the project root or its subdirectories unless you pass `-r <project-root>`.**

If you are not running from the project root or its subdirectories, add `-r <project-root>` to point Donna to the correct project.

**Pass text arguments to the tool in quotes with respect to escaping.** The tool MUST receive the exact text you want to pass as an argument.

Use one of the next approaches to correctly escape text arguments:

```
# option 1
donna -p <protocol> <command> <...>  $'# Long text\n\nwith escape sequences...'

# option 2
donna -p <protocol> <command> <...> \
  "$(cat <<'EOF'
# Long text

with escape sequences...
EOF
)"

```
