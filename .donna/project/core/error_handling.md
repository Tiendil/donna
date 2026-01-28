
# Error handling

```toml donna
kind = "donna.lib.specification"
```

This document describes how Donna handles errors that may occur during its operation, including error propagation, logging, and recovery strategies.

## Error kinds

There are two different kinds of errors in Donna:

- **Internal errors** — represented by the base class `InternalError(Exception)` — these errors indicate that something went wrong inside Donna itself, such as bugs in the code, unexpected states, or violations of internal invariants. These errors are not expected to be handled by agents or users, and usually indicate a need for fixing Donna's code.
- **Environment errors** — represented by the base class `EnvironmentError` (not an `Exception`) — these errors indicate that something went wrong in the external environment where Donna operates, such as missing artifacts, invalid artifacts formats, network issues, etc. These errors are expected to be handled by agents or users, and may have recovery strategies.

Environment errors has functionality to describe themselves in a user-friendly way, according to `donna.protocol`.

## Defining errors

Base error classes are defined in the `donna.core.errors` module.

Each top-level submodule of Donna MUST define its own error hierarchy by subclassing from `InternalError` and `EnvironmentError`. By convention, all error definitions MUST be located in the `donna.<submodule>.errors` module.

The exceptions for this rule are:

- `donna.primitives` — each submodule of primitives should be treated as self-contained unit, so error definitions SHOULD be located in the same module as primitive's code itself.
- `donna.lib` MUST not contain `errors` module, as it is just a collection of constructed  primitives — no new errors should be defined there.

Here is an example of defining a hierarchy of errors in `donna.xxx.errors`:

```python
from donna.core import errors as core_errors

#################
# Internal errors
#################

class InternalError(core_errors.InternalError):
    """Base class for internal errors in donna.xxx submodule."""
    pass

class SomethingGoneWrong(InternalError):
    """Indicates that something went wrong in donna.xxx submodule in a single specifc case."""
    pass

class DomainOrEntityError(InternalError):
    """Base class for domain-specific or entity-specific internal errors."""
    pass

class EntityGoneWrongCaseA(DomainOrEntityError):
    """Indicates that something went wrong with an entity in a single case."""
    pass

class EntityGoneWrongCaseB(DomainOrEntityError):
    """Indicates that something else went wrong with an entity in another case."""
    pass

####################
# Environment errors
####################

class EnvironmentError(core_errors.EnvironmentError):
    """Base class for environment errors in donna.xxx submodule."""
    pass

# The logic of defining subclasses is similar to internal errors.

```

## Internal errors behavior

Subclasses of internal errors can define parametrized error message:

```
...

class MyInternalError(InternalError):
    message = "Something gone wrong with entity {entity_id} due to {reason}."
```

**Internal errors are raised** using standard `raise` statement:

```
def produce_error(entity_id: str, reason: str):
    raise MyInternalError(entity_id=entity_id, reason=reason)
```

## Environment errors behavior

Environment errors are subclasses of Pydantic models and allow specifying structured data about the error.

Domain specific environment errors MUST redefine `cell_kind` and domain-level attributes. For example:

```python
class ArtifactValidationError(EnvironmentError):
    cell_kind: str = "artifact_validation_error"
    artifact_id: FullArtifactId
    section_id: ArtifactSectionId | None = None

    def content_intro(self) -> str:
        if self.section_id:
            return f"Error in artifact '{self.artifact_id}', section '{self.section_id}'"

        return f"Error in artifact '{self.artifact_id}'"
```

Leaf/case environment errors must provide explicit information about the error and how the user can fix it. For example:

```python
class FinalOperationHasTransitions(ArtifactValidationError):
    code: str = "donna.workflows.final_operation_has_transitions"
    message: str = "Final operation `{error.workflow_section_id}` should not have outgoing transitions."
    ways_to_fix: list[str] = [
        "Approach A: Remove all outgoing transitions from this operation.",
        "Approach B: Change the `fsm_mode` of this operation from `final` to `normal`",
        "Approach C: Remove the `fsm_mode` setting from this operation, as `normal` is the default.",
    ]
    workflow_section_id: ArtifactSectionId
```

**Environment errors are returned** from functions as part of `Result` type:

```python
...
from donna.core.errors import ErrorsList
from donna.core.result import Err, Ok, Result
...

def validate_artifact(self) -> Result[None, ErrorsList]:
    ...

    errors: ErrorsList = []

    ...

    errors.append(
        FinalOperationHasTransitions(
            artifact_id=artifact.id, section_id=section_id, workflow_section_id=workflow_section.id
        )
    )
    ...

    if errors:
        return Err(errors)

    return Ok(None)
```

## Naming error classes

Follow this guidelines when naming error classes:

- Try to keep names short but descriptive.
- Prefere not to use `Error`, `Exception`, `Failure` suffixes if possible.
- Prefere not to use `Internal` or `Environment` in the class names.

## Exceptions besides `InternalError`

- **Use only `InternalError` for all Donna's internal exceptions, untill the developer or the specification explicitly requires otherwise.**
- You MAY use other exception types if the third-party library you are working with requires it. For example, Pydantic models require `ValidationError` exceptions.
- You MUST use `NotImplementedError` when implementing abstract methods.
- You MAY use `NotImplementedError` as temporary code when:
  - You need a temporary placeholder for the code that is not implemented yet, but will be in the scope of the current task.
  - You need to raise an exception, but you have no established error hierarchy yet.

You are encouraged to follow the next strategy when implementing new code:

1. Use `NotImplementedError` as a temporary placeholders whenever you need to raise an exception.
2. When the code is ready, you review all `NotImplementedError` usages implement proper error hierarchy by defining new error classes as needed.
3. Replace all `NotImplementedError` usages with proper error classes.

## Asserts

Use `assert` statements as a hint for type checkers and linters to confirm invariants that are guaranteed by the code logic but type checkers cannot infer them automatically.

Don't use `assert` statements for any other purpose, replace them with proper error handling code.

## Do and Don'ts

**DO NOT** define multiple functions with the same logic but different error handling strategies (e.g., one function raises exceptions, another returns `Result`). Instead define a single function with one error handling strategy that are explicitly specified by the developer or logically deduced from the context.

Use `.unwrap` or similar methods that cause exception on `Result` objects only when the context is guarantees that there will be no exceptions. For example, after a check like `if result.is_ok():`.

If modify funtion to return environment errors, you **MUST** update all functions up the call stack that call this function to handle the returned errors properly: process, propagate or output (accoring to the context).

Define all possible environment error parameters in the body of subclass, not in the place where you construct the error object. It simplifies writing unit tests and shorten the code.

Good example:

```python
class FinalOperationHasTransitions(ArtifactValidationError):
    code: str = "donna.workflows.final_operation_has_transitions"
    message: str = "Final operation `{error.workflow_section_id}` should not have outgoing transitions."
    ways_to_fix: list[str] = [
        "Approach A: Remove all outgoing transitions from this operation.",
        "Approach B: Change the `fsm_mode` of this operation from `final` to `normal`",
        "Approach C: Remove the `fsm_mode` setting from this operation, as `normal` is the default.",
    ]
    workflow_section_id: ArtifactSectionId

...

error = FinalOperationHasTransitions(
  artifact_id=artifact.id, section_id=section_id, workflow_section_id=workflow_section.id
)
```

Bad Example:

```python

class FinalOperationHasTransitions(ArtifactValidationError):
    workflow_section_id: ArtifactSectionId

...

error = FinalOperationHasTransitions(
  artifact_id=artifact.id,
  section_id=section_id,
  workflow_section_id=workflow_section.id,
  message="Final operation `{error.workflow_section_id}` should not have outgoing transitions.",
  ways_to_fix=[
      "Approach A: Remove all outgoing transitions from this operation.",
      "Approach B: Change the `fsm_mode` of this operation from `final` to `normal`",
      "Approach C: Remove the `fsm_mode` setting from this operation, as `normal` is the default.",
  ],
)
```

If you need to propagate errors and the function expected to return the same result type, do not unwrap it and wrap again, just return the original result.

```python

def some_function_a() -> Result[SomeType, SomeErrorType]:
    ...

def some_function_b() -> Result[SomeType, SomeErrorType]:
    result = some_function_a()

    if result.is_err():
        return result  # good: propagate the original errors

def bad_example() -> Result[SomeType, SomeErrorType]:
    result = some_function_a()

    if result.is_err():
        return Err(result.unwrap_err())  # Bad: unwrapping and wrapping again is unnecessary
```
