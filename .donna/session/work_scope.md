# Session Work Scope
```toml donna
kind = "donna.lib.specification"
```

Brief plan for updating update_artifact return type.

## Developer request
make ./donna/world/artifacts.py:update_artifact return Result, check donna/world/machine/artifacts.py for example what I want

## Work description
Update the update_artifact function in donna/world/artifacts.py so it returns a Result object consistent with the example in donna/world/machine/artifacts.py, enabling callers to receive structured success/failure information and confirm behavior via the returned value.

## Goals
- Ensure update_artifact returns a Result object matching project conventions.
- Preserve expected behavior while exposing structured outcome data to callers.

## Objectives
- update_artifact returns a Result instance on success paths with the updated artifact outcome.
- update_artifact returns a Result instance on validation or update failure paths with error details.
- Any related call sites or tests reflect the new Result return type behavior.
- Artifact update behavior (validation and write) remains consistent aside from the return value.

## Known constraints
- MUST follow the example behavior in donna/world/machine/artifacts.py.
- MUST keep the function located at donna/world/artifacts.py:update_artifact.

## Acceptance criteria
- update_artifact returns a Result object in all execution paths.
- The returned Result matches the pattern used in donna/world/machine/artifacts.py.
- Failure paths return a Result that contains the validation/update error details.
- Artifact write and validation behavior remain unchanged aside from the return value.
- Any impacted usages or tests pass after the change.

## Deliverables / Artifacts
- MUST update the implementation of donna/world/artifacts.py:update_artifact to return Result.
