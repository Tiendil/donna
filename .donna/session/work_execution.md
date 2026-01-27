# Session Work Execution
```toml donna
kind = "donna.lib.workflow"
start_operation_id = "inspect_current_behavior"
```

Workflow to update update_artifact to return Result and adjust usages/tests.

## Inspect current behavior
```toml donna
id = "inspect_current_behavior"
kind = "donna.lib.request_action"
fsm_mode = "start"
```
1. Open `donna/world/artifacts.py` and `donna/world/machine/artifacts.py` to compare the current update_artifact implementation with the example Result usage.
2. Identify all call sites that rely on update_artifact return value.
3. {{ donna.lib.goto("implement_result_return") }}

## Implement Result return
```toml donna
id = "implement_result_return"
kind = "donna.lib.request_action"
```
1. Update `donna/world/artifacts.py:update_artifact` to return a Result value aligned with the example in `donna/world/machine/artifacts.py` for success and failure paths.
2. Preserve existing validation and update behavior.
3. {{ donna.lib.goto("update_usages_tests") }}

## Update usages and tests
```toml donna
id = "update_usages_tests"
kind = "donna.lib.request_action"
```
1. Adjust any call sites or tests to handle the new Result return type.
2. Ensure failure paths propagate Result error details where applicable.
3. {{ donna.lib.goto("run_checks") }}

## Run checks
```toml donna
id = "run_checks"
kind = "donna.lib.request_action"
```
1. Run relevant tests or checks (start with the narrowest available test target, then broaden if needed).
2. If checks fail, capture the errors and {{ donna.lib.goto("refine_fix") }}.
3. If checks pass, {{ donna.lib.goto("finish") }}.

## Refine fixes
```toml donna
id = "refine_fix"
kind = "donna.lib.request_action"
```
1. Fix issues discovered by the checks, keeping the Result return contract consistent.
2. {{ donna.lib.goto("run_checks") }}

## Finish
```toml donna
id = "finish"
kind = "donna.lib.finish"
```
Work completed.
