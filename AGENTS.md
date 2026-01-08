# Instructions for the AI Agents

This document provides instructions and guidelines for the AI agents working on this project.

Every agent MUST follow the rules and guidelines outlined in this document when performing their work.

## Points of interests

- `./donna/` — a directory containing source code of project — `donna` CLI tool.

## Project Overview

`Donna` is a CLI tool that helps manage the work of AI agents like Codex.

It is designed to to invert control flow: instead of agents deciding what to do next, the `donna` tells agents what to do next by following predefined workflows.

The core idea is that most of high-level workflows are more algorithmic than it may seem at first glance. For example, it may be difficult to fix a particular type issue in the codebase, but the overall process of polishing the codebase is quite linear:

1. Ensure all tests pass.
2. Ensure the code is formatted correctly.
3. Ensure there are no linting errors.
4. Go to the step 1 if you changed something in the process.
5. Finish.

We may need coding agents on the each step of the process, but there no reason for agents to manage the whole grooming loop by themselves — it take longer time, spends tokens and may lead to confusion of agents.

## Implementation details

- Donna is implemented in Python.

## IMPORTANT ON DONNA TOOL USAGE

**RUN `./bin/donna.sh` TO ACCESS THE `donna` TOOL**

Example: `./bin/donna.sh artifacts list`

**STRICTLY FOLLOW DESCRIBED COMMAND SYNTAX**

**PASS TEXT ARGUMENTS TO THE TOOL IN QUOTES WITH RESPECT TO ESCAPING.** The tool MUST receive the exact text you want to pass as an argument.

Use one of the next approaches to correctly escape text arguments:

```
# option 1
./bin/donna.sh records kind-set <...>  $'# Long text\n\nwith escape sequences...'

# option 2
./bin/donna.sh records kind-set <...> \
  "$(cat <<'EOF'
# Long text

with escape sequences...
EOF
)"

```
