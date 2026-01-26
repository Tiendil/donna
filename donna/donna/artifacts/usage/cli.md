# Donna Usage Instructions

```toml donna
kind = "donna.lib.specification"
```

This document describes how agents MUST use Donna to manage and perform their workflows.

**Agents MUST follow the instructions and guidelines outlined in this document precisely.**

## Overview

`donna` is a CLI tool that helps manage the work of AI agents like Codex.

It is designed to to invert control flow: instead of agents deciding what to do next, the `donna` tells agents what to do next by following predefined workflows.

The core idea is that most of high-level workflows are more algorithmic than it may seem at first glance. For example, it may be difficult to fix a particular type issue in the codebase, but the overall process of polishing the codebase is quite linear:

1. Ensure all tests pass.
2. Ensure the code is formatted correctly.
3. Ensure there are no linting errors.
4. Go to the step 1 if you changed something in the process.
5. Finish.

We may need coding agents on the each step of the process, but there no reason for agents to manage the whole grooming loop by themselves — it take longer time, spends tokens and may lead to confusion of agents.

## Development

- All work is always done in the context of a session. There is only one active session at a time.
- You MUST always work on the specific story assigned to you, that is managed by the `donna` tool.
- If developer asked you to do something and you have no session, you create one with the `donna` tool.
- If you have a session, you MUST keep all the information about it in your memory. Ask `donna` tool for the session details when you forget something.
- Donna may work from different environments. You MUST substitute correct `donna` command from the `AGENTS.md` for `<DONNA_CMD>` placeholder in this document when you work with the tool.
- All Donna CLI commands MUST include an explicit protocol selection using `-p <mode>` immediately after `<DONNA_CMD>`.

## Stories

Story is a semantically consistent unit of work assigned to you by the developer.

Story has no direct representation in donna tool, it is just a convenient way to refer to a particular scope of work.

The session always has exactly one active story at a time.

All work in the context of session/story is managed by the `donna` tool.

## Protocol

Protocol selects the output formatting and behavior of Donna's CLI for different consumers (humans, LLMs, automation).
When an agent invokes Donna, it SHOULD use the `llm` protocol (for example `-p llm`) unless the workflow explicitly requires another protocol.

### Story workflow

- You start session by calling `<DONNA_CMD> -p <protocol> sessions start`.
- After you started a session:
  2. List all possible workflows with command `<DONNA_CMD> -p <protocol> artifacts list`.
  3. Choose the most appropriate workflow for the story you are going to work on or ask the developer if you are not sure which workflow to choose.
  4. Start working by calling `<DONNA_CMD> -p <protocol> sessions run <workflow-id>`.
  5. The `donna` tool will output descriptions of all operations it performs to complete the story.
  6. The `donna` tool will output **action requests** that you MUST perform. You MUST follow these instructions precisely.
- When you done doing your part, you call `<DONNA_CMD> -p <protocol> sessions action-request-completed <action-request-id> <next-full-operation-id>` to report that you completed the action request. `<next-full-operation-id>` MUST contain full identifier of the next operation, like `<world>:<artifact>:<operation-id>`.
- After you report the result:
  1. The `donna` tool will output what you need to do next.
  2. You repeat the process until the story is completed.

### Starting work on a story

- If the developer asked you to do something:
  - run `<DONNA_CMD> -p <protocol> sessions status` to get the status of the current session.
  - if the work in completed, run `<DONNA_CMD> -p <protocol> sessions start` to start a new session.
  - if there are still a work to do, ask developer if you need to resume the current session or start a new one.
- If the developer asked you to continue your work, you MUST call `<DONNA_CMD> -p <protocol> sessions continue` to get your instructions on what to do next.

### Working with artifacts

An artifact is a markdown document with some extra metadata stored in one of the Donna's worlds.

Use the next commands to work with artifacts

- `<DONNA_CMD> -p <protocol> artifacts list [--pattern <artifact-pattern>]` — list all artifacts corresponding to the given pattern. If `<artifact-pattern>` is omitted, list all artifacts in all worlds. Use this command when you need to find an artifact or see what artifacts are available.
- `<DONNA_CMD> -p <protocol> artifacts view <world>:<artifact>` — get the meaningful (rendered) content of the artifact. This command shows the rendered information about the artifact. Use this command when you need to read the artifact content.
- `<DONNA_CMD> -p <protocol> artifacts fetch <world>:<artifact>` — download the original source of the artifact content, outputs the file path to the artifact you can change. Use this command when you need to change the content of the artifact.
- `<DONNA_CMD> -p <protocol> artifacts update <world>:<artifact> <file-path>` — upload the given file as the artifact. Use this command when you finished changing the content of the artifact.
- `<DONNA_CMD> -p <protocol> artifacts validate <world>:<artifact>` — check the artifact for validity according to its kind.
- `<DONNA_CMD> -p <protocol> artifacts validate-all [--pattern <artifact-pattern>]` — check all artifacts corresponding to the given pattern for validity according to their kinds.

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

**Substitute correct `donna` command from the `AGENTS.md` for `<DONNA_CMD>` placeholder in this document when you work with the tool.**
**All commands MUST include `-p <mode>` right after `<DONNA_CMD>`.**

Examples:

- `<DONNA_CMD> -p llm artifacts list --pattern "*:usage:**"` -> `./bin/donna.sh -p llm artifacts list --pattern "*:usage:**"` when `<DONNA_CMD>` is `./bin/donna.sh`
- `<DONNA_CMD> -p llm artifacts list --pattern "*:usage:**"` -> `poetry run donna -p llm artifacts list --pattern "*:usage:**"` when `<DONNA_CMD>` is `poetry run donna`
- `<DONNA_CMD> -p llm artifacts list --pattern "*:usage:**"` -> `donna -p llm artifacts list --pattern "*:usage:**"` when `<DONNA_CMD>` is `donna`.

**STRICTLY FOLLOW DESCRIBED COMMAND SYNTAX**

**PASS TEXT ARGUMENTS TO THE TOOL IN QUOTES WITH RESPECT TO ESCAPING.** The tool MUST receive the exact text you want to pass as an argument.

Use one of the next approaches to correctly escape text arguments:

```
# option 1
<DONNA_CMD> -p <protocol> artifacts update <...>  $'# Long text\n\nwith escape sequences...'

# option 2
<DONNA_CMD> -p <protocol> artifacts update <...> \
  "$(cat <<'EOF'
# Long text

with escape sequences...
EOF
)"

```
