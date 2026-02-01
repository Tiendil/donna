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

1. Based on the problem description you have, suggest an artifact name in the format `session:research:<short-problem-related-identifier>`.
2. Create the artifact and specify an original problem description in it.
3. `{{ donna.lib.goto("formalize_research") }}`

## Formalize Research

```toml donna
id = "formalize_research"
kind = "donna.lib.request_action"
```

1. Using your knowledge about the project and the original problem description, formulate a format description of the problem
2. Update the artifact with the formalized problem description.
3. `{{ donna.lib.goto("formulate_goals") }}`

## Formulate Goals

```toml donna
id = "formulate_goals"
kind = "donna.lib.request_action"
```

1. Based on the formalized problem description, formulate a list of goals that the problem solution should achieve.
2. Update the artifact with the list of goals.
3. `{{ donna.lib.goto("describe_information_to_collect") }}`

## Describe information to collect

```toml donna
id = "describe_information_to_collect"
kind = "donna.lib.request_action"
```

1. Based on the formalized problem description and the list of goals, formulate a description of the information that needs to be collected to research the problem.
2. Update the artifact with the description of the information to collect.
3. `{{ donna.lib.goto("list_information_sources") }}`

## List Information Sources

```toml donna
id = "list_information_sources"
kind = "donna.lib.request_action"
```

1. Based on the formalized problem description and the list of goals, formulate a list of information sources that can help to research the problem.
2. Update the artifact with the list of information sources.
3. `{{ donna.lib.goto("collect_information") }}`

## Collect Information

```toml donna
id = "collect_information"
kind = "donna.lib.request_action"
```

1. For each information source from the list:
   1. For each piece of required information from the description:
      1. Access the source and collect the required information.
      2. Update the artifact with the collected information.
2. `{{ donna.lib.goto("analyze_information") }}`

## Analyze Information

```toml donna
id = "analyze_information"
kind = "donna.lib.request_action"
```
