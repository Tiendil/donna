# Research workflow

```toml donna
kind = "donna.lib.workflow"
start_operation_id = "start"
```

Workflow for performing research on a given question/problem/situation. Collects relevant information, analyzes it, synthesizes possible options, and produces an answer/solution/deliverables.

The purpose of this workflow is to provide an information for making decisions or producing solutions based on researched data. It can be used:

- When the developer explicitly asks to make a research.
- When other workflows need to perform research as a subtask.

## Start

```toml donna
id = "start"
kind = "donna.lib.request_action"
fsm_mode = "start"
```

1. Read the specification `{{ donna.lib.view("donna:usage:artifacts") }}` if you haven't done it yet.
{# 2. Read the specification `{{ donna.lib.view("donna:specs:research") }}` if you haven't done it yet. #}
3. `{{ donna.lib.goto("ensure_problem_description_exists") }}`

## Ensure problem description exists

```toml donna
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
3. `{{ donna.lib.goto("set_primary_section_of_the_research_artifact") }}`

## Set primary section of the research artifact

```toml donna
id = "set_primary_section_of_the_research_artifact"
kind = "donna.lib.request_action"
```

1. Based on the formalized problem description, update the primary (h1) section of the research artifact to reflect the problem being researched. So the agents can effectively find and understand the research artifact using Donna.
2. `{{ donna.lib.goto("formulate_goals") }}`

## Formulate Goals

```toml donna
id = "formulate_goals"
kind = "donna.lib.request_action"
```

1. Based on the formalized problem description, formulate a list of goals that the problem solution should achieve.
2. Update the artifact with the list of goals.
3. `{{ donna.lib.goto("fomalize_form_of_final_solution") }}`

## Formalize form of final solution

```toml donna
id = "fomalize_form_of_final_solution"
kind = "donna.lib.request_action"
```

1. Based on the formalized problem description and the list of goals, formulate the desired form of the final solution.
2. Update the artifact with the desired form of the final solution.
3. `{{ donna.lib.goto("describe_solution_space") }}`

## Describe solution space

```toml donna
id = "describe_solution_space"
kind = "donna.lib.request_action"
```

To produce solution we should understand how to analyze the data and how to synthesize results into the final solution.

For this we need to list the axes along which we will analyze the data and the dimensions along which we will synthesize the results.

1. List the analysis axes.
2. List the synthesis dimensions.
3. Update the artifact with the description of the solution space.
4. `{{ donna.lib.goto("describe_information_to_collect") }}`

## Describe information to collect

```toml donna
id = "describe_information_to_collect"
kind = "donna.lib.request_action"
```

1. Based on the formalized problem description and the list of goals, list the information to be collected to research the problem.
2. Update the artifact with the description of the information to collect.
3. `{{ donna.lib.goto("list_information_sources") }}`

## List information sources

```toml donna
id = "list_information_sources"
kind = "donna.lib.request_action"
```

1. Based on the formalized problem description and the list of goals, formulate a list of information sources that can help to research the problem.
2. Update the artifact with the list of information sources.
3. `{{ donna.lib.goto("collect_information") }}`

## Collect information

```toml donna
id = "collect_information"
kind = "donna.lib.request_action"
```

1. For each information source from the list:
   1. For each piece of required information from the description:
      1. If the source can not provide this piece of information, skip it.
      2. Access the source and collect the required information.
      3. Update the artifact with the collected information.
2. `{{ donna.lib.goto("analyze_information") }}`

## Analyze information

```toml donna
id = "analyze_information"
kind = "donna.lib.request_action"
```

1. Using the analysis axes from the solution space description, analyze the collected information. Choose the format that best represents the analysis results and suits the the required solution form.
2. Update the artifact with the analysis results.
3. `{{ donna.lib.goto("synthesize_solutions") }}`

## Synthesize solutions

```toml donna
id = "synthesize_solutions"
kind = "donna.lib.request_action"
```

1. Using the synthesis dimensions from the solution space description, synthesize possible solutions based on the analysis results. Choose the format that best represents the synthesized solutions and suits the the required solution form.
2. Update the artifact with the synthesized solutions.
3. `{{ donna.lib.goto("evaluate_solutions") }}`

## Evaluate solutions

```toml donna
id = "evaluate_solutions"
kind = "donna.lib.request_action"
```

1. Evaluate the synthesized solutions against the goals from the formalized problem description.
2. Update the artifact with the evaluation results.
3. `{{ donna.lib.goto("produce_final_solution") }}`

## Produce final solution

```toml donna
id = "produce_final_solution"
kind = "donna.lib.request_action"
```

1. Based on the evaluation results, produce the final solution in the desired form.
2. Update the artifact with the final solution.
3. `{{ donna.lib.goto("finish") }}`

## Finish

```toml donna
id = "finish"
kind = "donna.lib.finish"
```
