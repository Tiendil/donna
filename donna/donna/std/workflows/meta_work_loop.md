# Meta Work Loop

General purpose work planning and execution workflow. Use it when you need to do complex work and there is no more specific workflow available.

## Start Work

```toml donna
id = "start"
kind = "request_action"
fsm_mode = "start"
```

1. Read the specification `{{ view("donna.specifications.planning") }}` if you haven't done it yet.
2. Read the specification `{{ view("donna.specifications.default_text_artifacts_behavior") }}` if you haven't done it yet.
3. If the developer hasn't provided you a description of the work for this session, ask them to provide it.
4. Create new session-level specification `session.specification.work_scope` with developer-provided description of the work to be done.
5. `{{ goto("create_work_description") }}`

## Create Work Description

```toml donna
id = "create_work_description"
kind = "request_action"
```

1. Read the specification `{{ view("donna.specifications.planning") }}` if you haven't done it yet.
2. Read the specification `{{ view("donna.specifications.default_text_artifacts_behavior") }}` if you haven't done it yet.
3. Formulate a concise high-level description of the work to be done, based on the developer-provided description.
4. Add this description to the `session.specification.work_scope`.
5. `{{ goto("list_primary_goals") }}`

## List Primary Goals

```toml donna
id = "list_primary_goals"
kind = "request_action"
```

1. Read the specification `{{ view("donna.specifications.planning") }}` if you haven't done it yet.
2. Read the specification `{{ view("donna.specifications.default_text_artifacts_behavior") }}` if you haven't done it yet.
3. If you can add more goals based on existing `{{ view("session.specification.work_scope") }}` add them to the specification.
4. If you can polish the existing goals according to the quality criteria in the `{{ view("donna.specifications.planning") }}` do it.
5. `{{ goto("list_objectives") }}`

## List Objectives

```toml donna
id = "list_objectives"
kind = "request_action"
```

You MUST list objectives that need to be achieved to complete each goal.

1. Read the specification `{{ view("donna.specifications.planning") }}` if you haven't done it yet.
2. Read the specification `{{ view("donna.specifications.default_text_artifacts_behavior") }}` if you haven't done it yet.
3. If you can add more objectives based on existing `{{ view("session.specification.work_scope") }}` add them to the specification.
4. If you can polish the existing objectives according to the quality criteria in the `{{ view("donna.specifications.planning") }}` do it.
5. `{{ goto("list_constraints") }}`

## List Constraints

```toml donna
id = "list_constraints"
kind = "request_action"
```

1. Read the specification `{{ view("donna.specifications.planning") }}` if you haven't done it yet.
2. Read the specification `{{ view("donna.specifications.default_text_artifacts_behavior") }}` if you haven't done it yet.
3. If you can add more constraints based on existing `{{ view("session.specification.work_scope") }}` add them to the specification.
4. If you can polish the existing constraints according to the quality criteria in the `{{ view("donna.specifications.planning") }}` do it.
5. `{{ goto("list_acceptance_criteria") }}`

## List Acceptance Criteria

```toml donna
id = "list_acceptance_criteria"
kind = "request_action"
```

1. Read the specification `{{ view("donna.specifications.planning") }}` if you haven't done it yet.
2. Read the specification `{{ view("donna.specifications.default_text_artifacts_behavior") }}` if you haven't done it yet.
3. If you can add more acceptance criteria based on existing `{{ view("session.specification.work_scope") }}` add them to the specification.
4. If you can polish the existing acceptance criteria according to the quality criteria in the `{{ view("donna.specifications.planning") }}` do it.
5. `{{ goto("list_deliverables") }}`

## List Deliverables

```toml donna
id = "list_deliverables"
kind = "request_action"
```

1. Read the specification `{{ view("donna.specifications.planning") }}` if you haven't done it yet.
2. Read the specification `{{ view("donna.specifications.default_text_artifacts_behavior") }}` if you haven't done it yet.
3. If you can list more deliverables based on existing `{{ view("session.specification.work_scope") }}` add them to the specification.
4. If you can polish the existing deliverables according to the quality criteria in the `{{ view("donna.specifications.planning") }}` do it.
5. `{{ goto("prepare_plan") }}`

## Prepare Work Plan

```toml donna
id = "prepare_plan"
kind = "request_action"
```

1. Read the specification `{{ view("donna.specifications.planning") }}` if you haven't done it yet.
2. Read the specification `{{ view("donna.specifications.default_text_artifacts_behavior") }}` if you haven't done it yet.
3. Read the specification `{{ view("session.specification.work_scope") }}` if you haven't done it yet.
4. Create new session-level workflow `session.workflows.work_execution` according to the scope of work you have defined.
5. `{{ goto("execute_plan") }}`

## Execute Plan

```toml donna
id = "execute_plan"
kind = "request_action"
```

1. Run workflow `session.workflows.work_execution` to execute the work according to the plan.
2. `{{ goto("groom_work") }}`

## Groom Work

```toml donna
id = "groom_work"
kind = "request_action"
```

1. Run the grooming workflow to ensure that the result is polished, clean, and ready for review.
2. `{{ goto("finish") }}`

## Finish

```toml donna
id = "finish"
kind = "finish_workflow"
```
