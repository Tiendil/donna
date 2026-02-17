# Introduction to the Donna tool

```toml donna
kind = "donna.lib.specification"
```
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

## Artifact Tags

To simplify searching for artifacts by their semantics, Donna allows tagging artifacts with semantically valuable keywords. Artifacts in `donna:*` world use the next set of tags.

Artifact type tags:

- `workflow` — workflow artifact — is set automatically by Donna.
- `specification` — specification artifact — is set automatically by Donna.

## Instructions

1. On start of the YOUR session you **MUST** read and understand instruction on using the Donna tool `{{ donna.lib.view("donna:usage:cli") }}`. It **MUST** be a one time operation. Do not repeat it unless you forget how to use the tool.
2. If you need to perform a work with Donna, you **MUST** select an appropriate Donna workflow to perform the work and run it.
3. If there is no appropriate workflow, ask the developer for a precise instructions on what to do.
4. If you are executing a workflow operation and need to perform a complex action or changes, you SHOULD search for an appropriate workflow and run it as a child workflow — it is the intended way to use Donna.
5. Run to list all workflows: `{{ donna.lib.list("**", tags=["workflow"]) }}`
6. Run to list all specifications: `{{ donna.lib.list("**", tags=["specification"]) }}`

## Journaling

You MUST use `donna journal write` to track you actions and thoughts, according the description in `{{ donna.lib.view("donna:usage:cli") }}`.

If you perform a long operation (e.g., exploring the codebase, designing a solution) that takes more than 30 seconds, you MUST split it into parts/steps and write a journal entry between each step.

You MUST use `donna journal view --lines 100` to read the last records after you compress your context.
