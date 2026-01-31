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

## Instructions

On start of the session you **MUST** read and understand instruction on using the Donna tool `{{ donna.lib.view("donna:usage:cli") }}`.
