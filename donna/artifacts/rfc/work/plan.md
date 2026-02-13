
# Plan work on base of Design & Request for Change documents

```toml donna
kind = "donna.lib.workflow"
start_operation_id = "start"
```

This workflow plans the work required to implement a specified Design document. The RFC document SHOULD be used as a helper context. The result of this workflow is a new workflow in the `session:*` world with detailed steps to implement the designed changes.

## Start Work

```toml donna
id = "start"
kind = "donna.lib.request_action"
fsm_mode = "start"
```

1. Read the Design document that the developer or parent workflow wants you to implement.
2. Read the RFC document that the developer or parent workflow wants you to implement, if it exists.
3. Read the specification `{{ donna.lib.view("donna:usage:artifacts") }}` if you haven't done it yet.
4. `{{ donna.lib.goto("prepare_workflow_artifact") }}`

## Prepare workflow artifact

```toml donna
id = "prepare_workflow_artifact"
kind = "donna.lib.request_action"
```

1. If the name of the artifact is not specified explicitly, assume it to `session:plans:<short-id-equal-to-design-slug>`.
2. Create a workflow with the next operations:
   - Start
   - A step for each action point in the RFC document and each item in the `Order of implementation` in Design document with the goal to minimize dependencies between steps and introduce changes incrementally.
   - Add additional steps if the design requires it.
   - (`id="review_changes"`) A gate step to start reviewing the changes.
   - A gate step to start reviewing the deliverables.
   - A step per deliverable to check if it exists and is correct. If the deliverable is missing or incorrect, the step MUST specify how to fix it and `goto` to the `review_changes` step.
   - A gate step to start verification.
   - A step for each verification statement to check it. If the statement is not satisfied, the step MUST specify how to fix it and `goto` to the `review_changes` step.
   - A finish step.
3. `{{ donna.lib.goto("review_workflow") }}`

## Review workflow

```toml donna
id = "review_workflow"
kind = "donna.lib.request_action"
```

For each of the steps in the workflow you created:

1. If the step can fail, add instructions on how to fix the issue and `goto` to the appropriate step.
2. If the step requires both research and implementation, split it into two steps: research step and implementation step.
3. If the step required editing multiple artifacts (multiple files, multiple functions, etc.), split it into multiple steps, one per change required.
4. If the step is too big or complex, split it into multiple smaller steps.

After all steps are reviewed:

1. If the changes were introduced, `{{ donna.lib.goto("review_workflow") }}`.
2. If no changes were introduced, `{{ donna.lib.goto("finish") }}`.

## Finish

```toml donna
id = "finish"
kind = "donna.lib.finish"
```

Work plan finalized. Ready to execute the planned workflow.
