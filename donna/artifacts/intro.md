# Intoduction to the Donna tool

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

To simplicity searching of artifacts by their semantics, Donna allows tagging artifacts with semantically valuable keywords. Artifacts in `donna:*` world use the next set of tags.

Artifact type tags:

- `workflow` — workflow artifact — is set automatically by Donna.
- `specification` — specification artifact — is set automatically by Donna.

Stage tags:

- `stage-research` — research stage artifacts.
- `stage-design` — design stage artifacts.
- `stage-plan` — planning stage artifacts.
- `stage-polish` — polishing stage artifacts.
- `stage-document` — documentation stage artifacts.

Extra tags:

- `meta-workflow` — workflows that orchestrate other workflows.
- `meta-specification` — specifications that describe or aggregate other specifications.

We recommend using those tags in `project:` and `session:` worlds as well to keep consistency.

## Instructions

1. On start of the YOUR session you **MUST** read and understand instruction on using the Donna tool `{{ donna.lib.view("donna:usage:cli") }}`. It **MUST** be a one time operation. Do not repeat it unless you forget how to use the tool.
2. If the developer asks you to perform a work with Donna, you **MUST** select an appropriate Donna workflow to perform the work and run it. If there is no appropriate workflow, ask the developer for a precise instructions on what to do.
