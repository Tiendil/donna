
# Do Request For Change work

```toml donna
kind = "donna.lib.workflow"
start_operation_id = "create_rfc"
```

This workflow uses a description of a problem or changes required from the developer or parent workflow to:

1. Create a Request for Change (RFC) artifact.
2. Plan the work required to implement the RFC.
3. Execute the planned work.

## Create RFC

```toml donna
id = "create_rfc"
kind = "donna.lib.request_action"
fsm_mode = "start"
```

1. Run the workflow `donna:rfc:work:create` to create or update the RFC artifact.
2. After completing the workflow, return here and `{{ donna.lib.goto("plan_rfc_work") }}`.

## Plan RFC work

```toml donna
id = "plan_rfc_work"
kind = "donna.lib.request_action"
```

1. Run the workflow `donna:rfc:work:plan` to create the execution workflow for the RFC.
2. Ensure you know the workflow id created in the previous step (default is `session:exectute_rfc` if not specified).
3. After completing the workflow, return here and `{{ donna.lib.goto("execute_rfc_work") }}`.

## Execute RFC work

```toml donna
id = "execute_rfc_work"
kind = "donna.lib.request_action"
```

1. Run the workflow created by the plan step (default: `session:exectute_rfc`) and complete it.
2. After completing the workflow, return here and `{{ donna.lib.goto("finish") }}`.

## Finish

```toml donna
id = "finish"
kind = "donna.lib.finish"
```
