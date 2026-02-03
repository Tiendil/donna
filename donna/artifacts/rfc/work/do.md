
# Do Request For Change work

```toml donna
kind = "donna.lib.workflow"
start_operation_id = "estimate_complexity"
```

This workflow uses a description of a problem or changes required from the developer or parent workflow to:

1. Create a Request for Change (RFC) artifact.
2. Plan the work required to implement the RFC.
3. Execute the planned work.

## Estimate complexity

```toml donna
id = "estimate_complexity"
kind = "donna.lib.request_action"
```

1. If the developer or parent workflow explicitly specified that the work is complex, `{{ donna.lib.goto("create_rfc") }}`.
2. If the developer or parent workflow explicitly specified that the work is simple, `{{ donna.lib.goto("fast_planing") }}`.
3. Make a rough estimate of the complexity of the requested changes.
4. If the complexity is small, `{{ donna.lib.goto("fast_planing") }}`.
5. Otherwise, `{{ donna.lib.goto("create_rfc") }}`.

Examles of changes with small complexity:

- A single file edit with clear instructions.
- A small addition to an existing function or class.
- A minor configuration change.
- A small documentation update.
- A simple bug fix with a known solution.

## Fast planing

```toml donna
id = "fast_planing"
kind = "donna.lib.request_action"
```

1. Draft a simple plan to implement the requested changes directly, without creating a formal RFC artifact.
2. `{{ donna.lib.goto("plan_rfc_work") }}`.

## Create RFC

```toml donna
id = "create_rfc"
kind = "donna.lib.request_action"
fsm_mode = "start"
```

1. Choose a workflow to create an RFC artifact.
2. Run the chosen workflow.
2. After completing the workflow `{{ donna.lib.goto("plan_rfc_work") }}`.

## Plan RFC work

```toml donna
id = "plan_rfc_work"
kind = "donna.lib.request_action"
```

1. Choose the workflow to plan the work required to implement the RFC created on the previous step.
2. Run the chosen workflow.
3. Ensure you know the workflow id created in the previous step (default is `session:exectute_rfc` if not specified).
4. After completing the workflow `{{ donna.lib.goto("execute_rfc_work") }}`.

## Execute RFC work

```toml donna
id = "execute_rfc_work"
kind = "donna.lib.request_action"
```

1. Run the workflow created by the plan step (default: `session:exectute_rfc`) and complete it.
2. After completing the workflow `{{ donna.lib.goto("polish_changes") }}`.

## Polish changes

```toml donna
id = "polish_changes"
kind = "donna.lib.request_action"
```

1. Find the workflow to polish the changes made.
2. Run the chosen workflow if you found one.
3. `{{ donna.lib.goto("log_changes") }}`.

## Log changes

```toml donna
id = "log_changes"
kind = "donna.lib.request_action"
```

1. Find the workflow to log the changes made in the scope of this RFC.
2. Run the chosen workflow if you found one.
3. `{{ donna.lib.goto("finish") }}`.

## Finish

```toml donna
id = "finish"
kind = "donna.lib.finish"
```

RFC workflow execution completed. Report the outcome to the developer.
