
# Plan work on Request For Change

```toml donna
kind = "donna.lib.workflow"
start_operation_id = "start"
```

This workflow plans the work required to implement a specified Request for Change (RFC). The result of this workflow is a new workflow in the `session:*` world with detailed steps to implement the RFC.

## Start Work

```toml donna
id = "start"
kind = "donna.lib.request_action"
fsm_mode = "start"
```

1. Read the RFC the developer or parent workflow want you to implement.
2. Read the specification `{{ donna.lib.view("donna:usage:artifacts") }}` if you haven't done it yet.
2. `{{ donna.lib.goto("prepare_workflow_artifact") }}`

## Prepare workflow artifact

```toml donna
id = "prepare_workflow_artifact"
kind = "donna.lib.request_action"
```

1. If the name of artifact is not specified explicitly, assume it to `session:exectute_rfc`.
2. Create a workflow with the next operations:
   - Start
   - A step for each action point in the RFC, ordered to minimize dependencies between steps and introduce changes incrementally.
   - (`id="review_changes"`) A gate step to start review the changes.
   - A gate step to start review the deliverables.
   - A step per deliverable to check if it exists and is correct. If the deliverable is missing or incorrect, step MUST specify how to fix it an goto to `review_changes` step.
   - A gate step to start verification.
   - A step for each verification statement to check it. If the statement is not satisfied, step MUST specify how to fix it and goto to the `review_changes` step.
   - A finish step.
3. `{{ donna.lib.goto("review_workflow") }}`

## Review workflow

```toml donna
id = "review_workflow"
kind = "donna.lib.request_action"
```

For each of steps in the workflow you created:

1. If the step can fail, add instructions on how to fix the issue and goto to appropriate step.
2. If the step requires both research and implementation, split it into two steps: research step and implementation step.
3. If the step required editing multiple artifacts (multiple files, multiple functions, etc.), split it into multiple steps, one per change required.
4. If the step is too big or complex, split it into multiple smaller steps.

After all steps are reviewed:

1. If the changes where introduced, `{{ donna.lib.goto("review_workflow") }}`.
2. If no changes were introduced, `{{ donna.lib.goto("finish") }}`.

## Finish

```toml donna
id = "finish"
kind = "donna.lib.finish"
```

RFC work plan finalized. Ready to execute the planned workflow.
