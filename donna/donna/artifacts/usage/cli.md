# Donna Usage Instructions

```toml donna
kind = "donna.lib.specification"
```

This document describes how agents MUST use Donna to manage and perform their workflows.

**Agents MUST follow the instructions and guidelines outlined in this document precisely.**

## Overview

`donna` is a CLI tool that helps manage the work of AI agents like OpenAI Codex.

It is designed to invert control flow: instead of agents deciding what to do next, the `donna` tells agents what to do next by following predefined workflows.

The core idea is that most high-level workflows are more algorithmic than it may seem at first glance. For example, it may be difficult to fix a particular type issue in the codebase, but the overall process of polishing the codebase is quite linear:

1. Ensure all tests pass.
2. Ensure the code is formatted correctly.
3. Ensure there are no linting errors.
4. Go to the step 1 if you changed something in the process.
5. Finish.

We may need coding agents on the each step of the process, but there no reason for agents to manage the whole loop by themselves — it takes longer time, spends tokens and confuses agents.

## Primary Rules

- All work is always done in the context of a session. There is only one active session at a time.
- You MUST always work on one task assigned to you.
- If developer asked you to do something and you have no session, you create one with the `donna` tool.
- If you have a session, you MUST keep all the information about it in your memory. Ask `donna` tool for the session details when you forget something.

## Protocol

Protocol selects the output formatting and behavior of Donna's CLI for different consumers (humans, LLMs, automation).
When an agent invokes Donna, it SHOULD use the `llm` protocol (`-p llm`) unless the workflow explicitly requires another protocol.

### Session workflow

- You start session by calling `donna -p <protocol> sessions start`.
- After you started a session:
  1. List all possible workflows with command `donna -p <protocol> artifacts list`.
  2. Choose the most appropriate workflow for the task you are going to work on or ask the developer if you are not sure which workflow to choose.
  3. Start working by calling `donna -p <protocol> sessions run <workflow-id>`.
  4. The `donna` tool will output descriptions of all operations it performs to complete the story.
  5. The `donna` tool will output **action requests** that you MUST perform. You MUST follow these instructions precisely.
- When you done doing your part, you call `donna -p <protocol> sessions action-request-completed <action-request-id> <next-full-operation-id>` to report that you completed the action request. `<next-full-operation-id>` MUST contain full identifier of the next operation, like `<world>:<artifact>:<operation-id>`.
- After you report the result:
  1. The `donna` tool will output what you need to do next.
  2. You repeat the process until the story is completed.

### Starting work

- If the developer asked you to do something:
  - run `donna -p <protocol> sessions status` to get the status of the current session.
  - or run `donna -p <protocol> sessions details` to get detailed information about the current session, including list of active action requests.
  - If there is no active session, start a new session by calling `donna -p <protocol> sessions start`.
  - If the session is already active and there are no unfinished work in it, start a new session by calling `donna -p <protocol> sessions start`.
  - If the session is already active and there are unfinished work in it, you MUST ask the developer whether to continue the work in the current session or start a new one.
- If the developer asked you to continue your work, you MUST call `donna -p <protocol> sessions continue` to get your instructions on what to do next.

### Working with artifacts

An artifact is a markdown document with extra metadata stored in one of the Donna's worlds.

Use the next commands to work with artifacts

- `donna -p <protocol> artifacts list [--pattern <artifact-pattern>]` — list all artifacts corresponding to the given pattern. If `<artifact-pattern>` is omitted, list all artifacts in all worlds. Use this command when you need to find an artifact or see what artifacts are available.
- `donna -p <protocol> artifacts view <world>:<artifact>` — get the meaningful (rendered) content of the artifact. This command shows the rendered information about the artifact. Use this command when you need to read the artifact content.
- `donna -p <protocol> artifacts fetch <world>:<artifact>` — download the original source of the artifact content, outputs the file path to the artifact's copy you can change. Use this command when you need to change the content of the artifact.
- `donna -p <protocol> artifacts update <world>:<artifact> <file-path>` — upload the given file as the artifact. Use this command when you finished changing the content of the artifact.
- `donna -p <protocol> artifacts validate <world>:<artifact>` — validate the given artifact to ensure it is correct and has no issues.
- `donna -p <protocol> artifacts validate-all [--pattern <artifact-pattern>]` — validate all artifacts corresponding to the given pattern.

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

**All Donna CLI commands MUST include an explicit protocol selection using `-p <mode>`.** Like `donna -p llm <command>`.

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
