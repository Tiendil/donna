# Instructions for the AI Agents

This document provides instructions and guidelines for the AI agents working on this project.

Every agent MUST follow the rules and guidelines outlined in this document when performing their work.

## First actions

**ALWAYS** perform the next steps when you start working.

1. Read specification of how to use Donna: `./bin/donna.sh artifacts view donna:specifications:donna_usage`.
2. Remember that for the needs of Donna, value if the `<DONNA_CMD>` placeholder is is `./bin/donna.sh`.

## Points of interests

- `./donna/` — a directory containing source code of project — `donna` CLI tool.
- `./.donna/` — a directory containing project-specific donna artifacts that is used to manage the work of AI agents on this project.

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
