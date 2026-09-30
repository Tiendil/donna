# Error architecture

## Goal of the document

This document describes how project modules represent internal errors, environment errors, and non-fatal problems, and how those values move from lower layers to the CLI.

## Scope

The scope of this specification is limited to error and warning architecture inside the Python implementation.

The following topics are out of scope:

- exact wording of user-facing messages.
- complete lists of future error codes.
- terminal formatting.
- workflow execution behavior.
- test coverage requirements.

## Dictionary

- `internal error` — a programming error, impossible state, unsupported internal operation, or violated invariant inside Donna.
- `environment error` — an expected (user, project, artifact, configuration, filesystem, session, external-tool, etc.) problem that an agent or user may be able to fix.
- `warning` — a non-fatal problem discovered while processing a request.
- `error code` — a stable machine-readable identifier for an environment error.
- `module root error` — a module-owned base class for internal errors or environment errors.
- `exception boundary` — a module boundary where expected low-level exceptions are converted into environment-error values.

## General principles

Expected project failures MUST be represented as environment-error values before they cross module boundaries.

Internal errors MUST be raised as exceptions.

Environment errors MUST be returned as shared `Result[T]` values unless a temporary exception bridge is required by an external callback boundary.

Donna MUST use the result implementation and environment-error foundation provided by `llm_tool_cli`. Shared environment errors MUST propagate as values without translation when no application-specific recovery or additional domain meaning is required. Raised shared exceptions MUST NOT be treated as expected environment failures.

Package ownership alone MUST NOT require translating an environment error into another error value or exception.

Lower-level modules MUST NOT print errors, write protocol records, or terminate the process.

The CLI layer MUST delegate environment-error reporting and process termination to `llm_tool_cli`.

Environment error codes MUST be stable enough for automation and tests.

Error codes MUST use lowercase ASCII letters, ASCII digits, `_`, and `.`.

User-facing messages SHOULD be clear enough to diagnose the problem without exposing implementation stack details.

## Error kinds

Donna has two primary error kinds:

- `InternalError` — raised exception type for bugs and internal invariant failures.
- `EnvironmentError` — structured Pydantic entity for recoverable project or environment problems.

Internal errors are not expected to be handled by agents or users.

Environment errors are expected to describe what failed and, when practical, how to fix it.

## Error ownership

Donna-owned base error classes MUST be owned by `donna.core.errors`.

Shared environment errors MUST retain their shared error hierarchy, code, message, and record fields.

Each top-level module that owns errors SHOULD define its own error hierarchy in its `errors` submodule.

A top-level module's internal error root SHOULD be named `InternalError` and inherit from `donna.core.errors.InternalError`.

A top-level module's environment error root SHOULD inherit from `donna.core.errors.EnvironmentError`.

The environment root MAY have a more specific name when that name communicates the module boundary, such as `WorkspaceError` or `CliError`.

Each unique error case SHOULD be represented by its own subclass.

Each top-level module that owns an `errors` submodule MUST export it from the module package initializer.

Production errors MUST NOT be defined in test modules.

Test-only error classes MAY be defined in test modules when they are required to verify error handling behavior.

`donna.primitives` submodules MAY define primitive-specific errors close to the primitive implementation when the primitive is a self-contained unit.

`donna.lib` MUST NOT define an `errors` submodule because it is a collection of constructed primitive instances.

## Internal errors

`donna.core.errors.InternalError` MUST inherit from `llm_tool_cli.core.errors.InternalError`.

Internal error subclasses MAY define a parametrized message template.

Template formatting MUST be owned by the shared internal-error base. Donna extensions MAY provide project-specific default templates.

Internal error instances MUST use the shared `message` and `details` contract for their formatted diagnostic and constructor context.

Internal errors SHOULD be raised with the standard `raise` statement.

Internal errors SHOULD NOT be converted into Donna cells during normal CLI command handling.

Internal errors SHOULD be used for:

- impossible states.
- unsupported internal methods.
- missing process-local context.
- misuse of `Result.unwrap()` and `Result.unwrap_err()`.
- violations of assumptions already guaranteed by prior validation.

## Environment errors

Donna's environment-error extension MUST inherit entity behavior through the shared environment-error model and identify Donna-owned failures for application policy.
Its root MUST inherit the default environment-error exit status managed by `llm_tool_cli` without overriding it.
Error models MUST remain independent of cell presentation; `llm_tool_cli` MUST own environment-error cells and their rendering.

Environment errors MUST NOT inherit from `Exception`.

Environment errors MUST define `code` and `message`.

Environment errors MAY define:

- `ways_to_fix`.
- structured fields with context needed for rendering, logging, or tests.

Environment error messages and ways to fix MAY use `{error.<field>}` formatting.

Leaf environment errors SHOULD define their message and fix guidance in the class body, not at construction sites.

Construction sites SHOULD pass only the structured fields that vary for that error instance.

All environment errors, including errors embedded in artifact views, MUST use the shared typed environment-error cell and its common presentation contract.
Donna's error nodes MUST retain graph and journal responsibilities while delegating cell construction to the shared library.

The core error base classes MUST NOT depend on protocol cells, protocol nodes, protocol formatters, or CLI output.

The shared library MUST manage error content, corrective guidance, native codes, and diagnostic context in cell output.

## Results

Functions that can fail with environment errors SHOULD return `Result[T]`, where `T` is the successful value type and failures always contain `EnvironmentErrors`.

`EnvironmentErrors` MUST use the shared list type and MAY contain both shared and Donna-owned environment-error instances.

Successful results MUST be returned with `Ok(value)`.

Environment failures MUST be returned with `Err(errors)`.

When multiple validation errors can be discovered in one pass, code SHOULD collect them and return one `Err(errors)` value.

Code that propagates an existing compatible error result SHOULD return the original result or original error list instead of unwrapping and wrapping it again.

Code SHOULD NOT define duplicate functions that differ only by error handling strategy.

If a function is changed to return environment errors, callers up the call stack MUST be updated to process, propagate, or render those errors according to their layer.

## `unwrap_to_error`

The `unwrap_to_error` decorator SHOULD be the preferred way to compose calls to functions that return `Result` objects when it makes unwrapping and propagation simpler.

The decorator SHOULD be used on functions that return `Result[T]` and primarily call other `Result`-returning functions.

Decorated functions MAY call `.unwrap()` on intermediate `Result` values to keep straight-line code readable.

This style SHOULD be preferred over repeated manual checks like `if result.is_err(): return Err(result.unwrap_err())`.

When `.unwrap()` raises `UnwrapError`, `unwrap_to_error` MUST convert the unwrapped error value back into `Err(...)`.

`unwrap_to_error` MUST NOT be used to hide internal errors or arbitrary exceptions.

## Temporary environment error bridges

Some external callback boundaries cannot return `Result` directly.

At those boundaries, Donna MAY use the shared `EnvironmentErrorsProxy` technical exception to carry environment errors through the callback stack.

The proxy MUST be caught at the nearest Donna-controlled boundary and converted back into `Result[T]`.

The proxy MUST NOT cross into CLI rendering as an internal error.

## Exception boundaries

Modules that call external systems MUST convert relevant raw low-level failures into environment errors at the boundary where useful context is still available. When `llm_tool_cli` owns that boundary, its returned environment errors already satisfy this requirement.

External systems include:

- filesystem operations.
- TOML parsing.
- Pydantic model validation for external input.
- Markdown and template parsing.
- Python import loading for configured primitives or directives.
- subprocess execution.
- external journal commands.

Pydantic validation errors MUST NOT be exposed directly across high-level module boundaries for user-provided data.

Donna-owned validation boundaries that create Pydantic entities from external input MUST convert raw `pydantic.ValidationError`, `ValueError`, and similar low-level validation failures into Donna environment errors at the nearest useful boundary. Shared validation errors MUST propagate unchanged as result values.

Unexpected programming errors MUST remain exceptions rather than being converted into expected failures. Code that handles expected user or environment failures MUST represent them as environment-error values.

When converting an exception, details SHOULD preserve enough information for diagnosis without requiring stack traces in user-facing output.

## CLI mapping

Skill-command failure handling MUST be managed by `llm_tool_cli`.
Protocol-option validation and its shared invalid-argument diagnostic MUST also be managed by `llm_tool_cli`.
The remaining mapping rules apply to Donna-owned command execution.

Typer command line parsing errors MAY use Typer's standard invalid-argument behavior.

CLI argument parsing MAY raise `typer.BadParameter`, `click.UsageError`, or `typer.Exit` before command execution has fully entered Donna's result-based flow.

After the selected protocol is installed, the CLI MUST use command error handling and explicit error reporting managed by `llm_tool_cli`, including its diagnostic order, cell presentation, stream routing, and exit behavior for all environment errors.
Donna MUST NOT maintain a separate rendering or exit path for errors owned by Donna.
The local command context MUST retain workspace and runtime setup, observe and re-raise unwrapped errors for journaling, and restore runtime contexts after success or failure.

The CLI SHOULD write environment error journal records when workspace configuration is loaded and journal forwarding is available.

Error classes outside the CLI module MAY declare exit-code overrides through the shared core contract; process termination MUST be delegated to the shared CLI boundary.

## Warnings

Warnings represent non-fatal problems discovered while processing a request.

Warnings MUST be used only when processing can continue and the command can still produce useful requested output.

Warnings MUST NOT be used for invalid command line arguments, invalid configuration that prevents workspace loading, invalid artifacts that prevent requested validation, or workflow execution failures.

Donna currently has no shared warning storage or warning protocol record architecture.

Until such architecture is specified and implemented, modules MUST NOT invent ad hoc warning channels.

## Naming error classes

Error class names SHOULD be short and descriptive.

Leaf error class names SHOULD avoid `Error`, `Exception`, `Failure`, `Internal`, and `Environment` suffixes when the shorter name remains clear.

Root classification classes MAY use `InternalError`, `EnvironmentError`, or a module-specific boundary name such as `WorkspaceError`.

## Asserts

`assert` statements MAY be used as hints for type checkers and linters when the invariant is guaranteed by earlier control flow.

`assert` statements MUST NOT be used for user input validation, environment validation, artifact validation, or recoverable workflow failures.

Recoverable failures MUST use environment-error values.

Impossible runtime states SHOULD use internal errors when they need explicit handling.

## Other exception types

Production Donna code SHOULD use `InternalError` for internal exceptions unless a third-party interface or Python protocol requires another exception type.

Other exception types MAY be used when required by third-party libraries, Pydantic validators, Typer/click command parsing, or Python protocols. Shared technical result exceptions MAY implement controlled unwrapping and propagation. They MUST NOT be mistaken for expected environment-error values.

`NotImplementedError` MAY be used as a temporary placeholder only while implementation is still in progress.

Before a change is considered complete, temporary `NotImplementedError` usages SHOULD be replaced with Donna-specific errors or implemented behavior.
