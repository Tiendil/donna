# Introduction to the Donna tool
This document provides an introduction to the Donna — a CLI tool that helps manage the work of AI agents like Codex.

## Overview

Donna is designed to to invert control flow: instead of agents deciding what to do next, the `donna` tells agents what to do next by following predefined workflows.

The core idea is that most of high-level workflows are more algorithmic than it may seem at first glance. For example, it may be difficult to fix a particular type issue in the codebase, but the overall process of polishing the codebase is quite linear:

1. Ensure all tests pass.
2. Ensure the code is formatted correctly.
3. Ensure there are no linting errors.
4. Go to the step 1 if you changed something in the process.
5. Finish.

We may need coding agents on the each step of the process, but there no reason for agents to manage the whole grooming loop by themselves — it take longer time, spends tokens and may lead to confusion of agents.

## Instructions

1. On start of the YOUR session you **MUST** read and understand instruction on using the Donna tool by running `donna skill usage`. It **MUST** be a one time operation. Do not repeat it unless you forget how to use the tool.
2. If you need to perform a work with Donna, you **MUST** select an appropriate Donna workflow to perform the work and run it.
3. If there is no appropriate workflow, ask the developer for a precise instructions on what to do.
4. If you are executing a workflow operation and need to perform a complex action or changes, you SHOULD search for an appropriate workflow and run it as a child workflow — it is the intended way to use Donna.
5. To find workflows, read the following files: `**/*.donna.md`.
6. To find documentation, read the following files: `**/*.md`.

## Journaling

Donna creates internal journal records for important workflow events, according to the description in `donna skill usage`.

Journal records can be forwarded to a third-party tool by configuring `[journal].cmd` in `<project-root>/donna.toml`.

The configured command is a list of command arguments. Arguments whose first and last characters are `{` and `}` are replaced with attributes of `JournalRecord`.

If `[journal].cmd` is omitted, Donna treats it as `None` and performs no journal writing.
