
# Intoduction to the Donna development

```toml donna
kind = "donna.lib.specification"
```

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

## Points of interest

- `./donna/` — a directory containing source code of project — `donna` CLI tool.
- `./.donna/` — a directory containing project-specific donna artifacts that is used to manage the work of AI agents on this project.

## Specifications of interest

Since this is the repository that contains the Donna project itself, you MUST pay additional attention to from which world you are viewing specifications.

- `donna:` world contains specifications and artifacts related to the Donna tool behavior. You access them when you need to use `donna` tool itself. You change them when you make changes to the Donna behavior.
- `project:` world contains specifications and artifacts related to the Donna project as a software project. You access them when you need to understand how to introduce changes to the Donna codebase. You change them when you change the development processes or documentation of the Donna project as a software project.

Check the next specifications:

- `{{ donna.lib.view("project:core:top_level_architecture") }}` when you need to introduce any changes in Donna or to research its code.
- `{{ donna.lib.view("donna:core:error_handling") }}` when you need to implement any new feature in Donna that may produce, process or propagate errors.
