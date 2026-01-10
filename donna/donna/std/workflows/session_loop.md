# Story Loop Workflow

```toml donna
start_operation_id = "start"
description = """
End-to-end session processing: from work description through planning to execution and grooming.
"""
```

End-to-end session processing: from work description through planning to execution and grooming.

## Start Work

```toml donna
id = "start"
kind = "request_action"
```

1. Read the specification `donna.specifications.planning` if you haven't done it yet.
2. If the developer hasn't provided you a description of the work for this session, ask them to provide it.
3. Add the description as `<record kind: session_developer_description>` to the session.
4. `{{ goto("create_work_description") }}`

## Create Work Description

```toml donna
id = "create_work_description"
kind = "request_action"
```

Here is current state of the session specification.

```
{{partial_description()}}
```

You MUST produce a high-level description of the work to be done based on the developer's description.

1. Read the specification `donna.specifications.planning` if you haven't done it yet.
2. Add the description as `<record kind: session_work_description>` to the session.
3. `{{ goto("list_primary_goals") }}`

## List Primary Goals

```toml donna
id = "list_primary_goals"
kind = "request_action"
```

Here is current state of the session specification.

```
{{partial_description()}}
```

You MUST list the goals of this session.

1. Read the specification `donna.specifications.planning` if you haven't done it yet.
2. If you can identify one more goal:
2.1. add it as a `<record kind: session_goal>` to the session;
2.2. `{{ goto("list_primary_goals") }}`;
3. Otherwise, `{{ goto("list_objectives") }}`

## List Objectives

```toml donna
id = "list_objectives"
kind = "request_action"
```

Here is current state of the session specification.

```
{{partial_description()}}
```

You MUST list objectives that need to be achieved to complete each goal.

1. Read the specification `donna.specifications.planning` if you haven't done it yet.
2. If you can identify one more objective:
2.1. add it as a `<record kind: session_objective>` to the session;
2.2. `{{ goto("list_objectives") }}`;
3. Otherwise, `{{ goto("list_constraints") }}`

## List Constraints

```toml donna
id = "list_constraints"
kind = "request_action"
```

Here is current state of the session specification.

```
{{partial_description()}}
```

You MUST list the known constraints for this session.

1. Read the specification `donna.specifications.planning` if you haven't done it yet.
2. If you can identify one more constraint:
2.1. add it as a `<record kind: session_constraint>` to the session;
2.2. `{{ goto("list_constraints") }}`;
3. Otherwise, `{{ goto("list_acceptance_criteria") }}`

## List Acceptance Criteria

```toml donna
id = "list_acceptance_criteria"
kind = "request_action"
```

Here is current state of the session specification.

```
{{partial_description()}}
```

You MUST list the acceptance criteria for this session.

1. Read the specification `donna.specifications.planning` if you haven't done it yet.
2. If you can identify one more acceptance criterion:
2.1. add it as a `<record kind: session_acceptance_criterion>` to the session;
2.2. `{{ goto("list_acceptance_criteria") }}`;
3. Otherwise, `{{ goto("list_deliverables") }}`

## List Deliverables

```toml donna
id = "list_deliverables"
kind = "request_action"
```

Here is current state of the session specification.

```
{{partial_description()}}
```

You MUST list the deliverables / artifacts for this session.

1. Read the specification `donna.specifications.planning` if you haven't done it yet.
2. If you can identify one more deliverable:
2.1. add it as a `<record kind: session_deliverable>` to the session;
2.2. `{{ goto("list_deliverables") }}`;
2. Otherwise, `{{ goto("prepare_plan") }}`

## Prepare Work Plan

```toml donna
id = "prepare_plan"
kind = "request_action"
```

Here is current state of the session specification.

```
{{partial_description()}}
```

You MUST prepare a detailed work plan for this session.

1. Read the specification `donna.specifications.planning` if you haven't done it yet.
2. If you can identify one more plan item:
2.1. add it as a `<record kind: session_plan_item>` to the session;
2.2. `{{ goto("prepare_plan") }}`;
3. Otherwise, `{{ goto("execute_plan") }}`

## Execute Plan

```toml donna
id = "execute_plan"
kind = "request_action"
```

Here is the work plan for the session.

```
{{partial_description()}}
```

You MUST thoroughly execute the plan step by step to finish the work.

1. Follow the plan carefully and implement the necessary changes to complete the session.
2. When you finish executing the plan, `{{ goto("groom_work") }}`

## Groom Work

```toml donna
id = "groom_work"
kind = "request_action"
```

You have completed the work according to the plan.

1. Run the grooming workflow to ensure that the result is polished, clean, and ready for review.
2. When you finish grooming workflow, `{{ goto("finish") }}`

## Finish

```toml donna
id = "finish"
kind = "finish_workflow"
```
