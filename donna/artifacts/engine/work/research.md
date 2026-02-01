# Research workflow

```toml donna
kind = "donna.lib.workflow"
start_operation_id = "start"
```

Workflow for performing research on a given question/problem/situation. Collects relevant information, analyzes it, synthesizes possible options, and produces a list of requested deliverables.

## Start

```toml donna
id = "start"
kind = "donna.lib.request_action"
fsm_mode = "start"
```

1. Read the specification `{{ donna.lib.view("donna:usage:artifacts") }}` if you haven't done it yet.
2. Read the specification `{{ donna.lib.view("donna:specs:research") }}` if you haven't done it yet.
3. `{{ donna.lib.goto("ensure_problem_description_exists") }}`

## Ensure problem description exists

```toml
id = "ensure_problem_description_exists"
kind = "donna.lib.request_action"
```

At this point you SHOULD have a clear description of the problem in your context. I.e. you know what you need to do in this workflow.

1. If you have a problem description in your context, `{{ donna.lib.goto("prepare_artifact") }}`.
2. If you have no problem description in your context, but you know it is in one of `session:*` artifacts, find and view it. Then `{{ donna.lib.goto("prepare_artifact") }}`.
3. If you have no problem description in your context, and you don't know where it is, ask the developer to provide it. After you get the problem description, `{{ donna.lib.goto("prepare_artifact") }}`.

## Prepare research artifact

```toml donna
id = "prepare_artifact"
kind = "donna.lib.request_action"
```

1. Based on the problem description you have, suggest an artifact name `session:research:<short-problem-related-identifier>`.
2. Create the artifact, by specifying an original problem description in it.
3. `{{ donna.lib.goto("collect_information") }}`
