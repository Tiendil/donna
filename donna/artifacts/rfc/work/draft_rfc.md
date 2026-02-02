
# Draft an RFC Document

```toml donna
kind = "donna.lib.workflow"
start_operation_id = "start"
```

## Start Work

```toml donna
id = "start"
kind = "donna.lib.request_action"
fsm_mode = "start"
```

1. Read the specification `{{ donna.lib.view("donna:rfc:specs:request_for_change") }}` if you haven't done it yet.
2. Read the specification `{{ donna.lib.view("donna:usage:artifacts") }}` if you haven't done it yet.
3. `{{ donna.lib.goto("ensure_work_description_exists") }}`

## Ensure work description exists

```toml donna
id = "ensure_work_description_exists"
kind = "donna.lib.request_action"
```

At this point you SHOULD have a clear description of the problem in your context. I.e. you know what you need to do in this workflow.

1. If you have a problem description in your context, `{{ donna.lib.goto("prepare_rfc_artifact") }}`.
2. If you have no problem description in your context, but you know it is in one of `session:*` artifacts, find and view it. Then `{{ donna.lib.goto("prepare_rfc_artifact") }}`.
3. If you have no problem description in your context, and you don't know where it is, ask the developer to provide it. After you get the problem description, `{{ donna.lib.goto("prepare_rfc_artifact") }}`.

## Prepare RFC artifact

```toml donna
id = "prepare_rfc_artifact"
kind = "donna.lib.request_action"
```

1. If the name of artifact is not specified explicitly, assume it to be default for the session: `session:rfc`.
2. Save the next template into the artifact, replace `<variables>` with appropriate values.

```
# <Title>

<short description of the proposed change>

## Original description

<original description of the requested changes from the developer or parent workflow>

## Formal description

## Goals

## Objectives

## Constraints

## Requirements

## Acceptance criteria

## Solution

## Verification

## Deliverables

## Action items
```

3. `{{ donna.lib.goto("formalize_work_description") }}`

## Formalize work description

```toml donna
id = "formalize_work_description"
kind = "donna.lib.request_action"
```

1. Create a formal description of the requested changes. Use your knowledge of the project and the original problem description.
2. Update the artifact with the formal description.
3. `{{ donna.lib.goto("formulate_goals") }}`

## Formulate Goals

```toml donna
id = "formulate_goals"
kind = "donna.lib.request_action"
```

1. Formulate a list of goals that the requested changes should achieve. Use your knowledge of the project and the formalized work description.
2. Update the artifact with the list of goals.
3. `{{ donna.lib.goto("list_objectives") }}`

## List Objectives

```toml donna
id = "list_objectives"
kind = "donna.lib.request_action"
```

1. List objectives that need to be achieved to complete each goal. Use your knowledge of the project, formalized work description and the list of goals.
2. Ensure that each goals has 2-6 associated objectives, unless the goal is trivial and can be achieved with a single objective.
3. Update the artifact with the list of objectives.
4. `{{ donna.lib.goto("list_constraints") }}`

## List Constraints

```toml donna
id = "list_constraints"
kind = "donna.lib.request_action"
```

1. List all constraints that affect the requested changes. Use your knowledge of the project, list of goals and list of objectives.
2. Update the artifact with the list of constraints.
3. `{{ donna.lib.goto("list_requirements") }}`

## List Requirements

```toml donna
id = "list_requirements"
kind = "donna.lib.request_action"
```

1. List all requirements that need to be fulfilled to achieve the objectives. Use your knowledge of the project, list of goals, list of objectives and list of constraints.
2. Update the artifact with the list of requirements.
3. `{{ donna.lib.goto("define_acceptance_criteria") }}`

## Define Acceptance Criteria

```toml donna
id = "define_acceptance_criteria"
kind = "donna.lib.request_action"
```

1. Define acceptance criteria that will be used to verify that the requested changes achieve the objectives, fulfill the requirements, and respect the constraints. Use your knowledge of the project, list of objectives, list of requirements and list of constraints.
2. Update the artifact with the acceptance criteria.
3. `{{ donna.lib.goto("describe_solution") }}`

## Describe Solution

```toml donna
id = "describe_solution"
kind = "donna.lib.request_action"
```

1. Describe the solution that will sutisfy the all statements about the requested changes.
2. Update the artifact with the description of the solution.
3. `{{ donna.lib.goto("define_verification") }}`

## Define Verification

```toml donna
id = "define_verification"
kind = "donna.lib.request_action"
```

1. Define the verification steps that will be used to ensure that the solution meets the objectives, constraints, requirements, and acceptance criteria.
2. Update the artifact with the verification steps.
3. `{{ donna.lib.goto("list_deliverables") }}`

## List Deliverables

```toml donna
id = "list_deliverables"
kind = "donna.lib.request_action"
```

1. List all deliverables that will be produced as part of the requested changes.
2. Update the artifact with the list of deliverables.
3. `{{ donna.lib.goto("identify_action_items") }}`

## Identify Action Items

```toml donna
id = "identify_action_items"
kind = "donna.lib.request_action"
```

1. Identify all action items that need to be completed to implement the requested changes.
2. Update the artifact with the list of action items.
3. `{{ donna.lib.goto("complete_draft") }}`

## Complete Draft

```toml donna
id = "complete_draft"
kind = "donna.lib.finish"
```
