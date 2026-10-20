# Error architecture

## Goal of the document

This document describes the architecture of failure handling.

## Scope

This specification covers Python error/warning architecture.
The following are out of scope:

- exact messages.
- code inventories.
- terminal formatting.
- workflow behavior.
- coverage requirements.

## Dictionary

- `internal error` — one of the following:

  - a bug.
  - an impossible state.
  - an unsupported internal operation.
  - an invariant violation.

- `environment error` — an expected project/environment problem potentially fixable by a user or agent.
- `warning` — a non-fatal problem during a request.
- `error code` — a machine-readable environment-error identifier.
- `module root error` — a module's internal/environment-error base.
- `exception boundary` — converts expected low-level exceptions to environment-error values.

## General principles

Expected failures MUST cross boundaries as shared `Result[T]` environment-error values, except temporary external-callback bridges.
Internal errors MUST be raised.
Donna MUST use `llm_tool_cli` results/error foundations and preserve shared errors unless translation adds domain meaning or recovery.
Package ownership alone MUST NOT trigger translation; raised shared exceptions MUST NOT become expected failures.

Lower layers MUST NOT print errors, write protocol records, or terminate.
The CLI MUST delegate reporting/termination to `llm_tool_cli`.
Codes MUST identify failure kinds without message parsing.
Project codes MUST use lowercase ASCII letters, ASCII digits, and `_`; adopted shared codes MUST retain native spelling.
Messages SHOULD diagnose failures without stack details.

## Error kinds

`InternalError` is a raised bug/invariant exception, not user-handled.
`EnvironmentError` is a structured Pydantic entity describing an expected failure and, when practical, its correction.

## Error ownership

Donna bases MUST belong to `donna.core.errors`.
Shared errors MUST retain their:

- hierarchy.
- codes.
- messages.
- records.

Top-level error owners SHOULD define `errors` hierarchies with an `InternalError` root inheriting Donna's core internal base and an `EnvironmentError` root inheriting Donna's core environment base.
Category roots MUST explicitly use `EnvironmentError`/`InternalError`, not an ambiguous `Error` or boundary-only name.
Unique cases SHOULD have subclasses.
Owners MUST export `errors` from their package initializer.
Production errors MUST NOT live in tests; test-only errors MAY verify handling.
Self-contained primitive submodules MAY colocate errors with implementations.
`donna.lib` MUST NOT define `errors`: it contains constructed primitive instances.

## Internal errors

Donna's internal base MUST inherit `llm_tool_cli.core.errors.InternalError` and use shared `message`/`details`.
Subclasses MAY declare templates/defaults; shared code MUST own formatting.
Internal errors SHOULD use `raise` and SHOULD NOT become cells in normal CLI handling.
They SHOULD represent:

- impossible states.
- unsupported internal methods.
- missing process context.
- result-unwrapping misuse.
- violated previously validated assumptions.

## Environment errors

Donna's shared-model extension MUST identify Donna-owned failures for policy and inherit the shared default exit status without overriding it.
Errors MUST remain presentation-independent, define `code`/`message`, and MUST NOT inherit `Exception`.
They MAY add `ways_to_fix`, structured context, and `{error.<field>}` message/guidance formatting.
Leaf classes SHOULD declare messages/guidance; call sites SHOULD supply only varying context.
Diagnostic data MUST follow the shared contract in `specs/architecture/errors.md` in `llm-tool-cli`.

All errors, including artifact-view errors, MUST use directly constructed typed error cells from `llm_tool_cli` without node wrappers.
For these cells, the library MUST own:

- content.
- guidance.
- codes.
- context.
- rendering.

Journal conversion MUST use formatted messages/structured fields, preserving internal line breaks without prefixes or duplicate console journal lines.
Core error bases MUST NOT depend on cells, formatters, or CLI output.

## Results

Fallible functions SHOULD return `Result[T]`; failures MUST use shared `EnvironmentErrors`, which MAY mix shared/Donna values.
Success MUST use `Ok(value)`; failure MUST use `Err(errors)`.
Independent validation failures SHOULD be collected in one result.
Compatible propagation SHOULD preserve the original result/list without rewrapping.
Functions SHOULD NOT be duplicated solely by handling strategy.
Changing a function to return errors MUST update callers to handle/propagate/render according to their layer.

## `unwrap_to_error`

For simpler composition of result-returning functions, `unwrap_to_error` SHOULD be preferred over repeated manual failure checks, particularly for functions mainly composing other results.
Decorated functions MAY unwrap intermediate values.
The decorator MUST convert `UnwrapError` back to `Err` with its payload and MUST NOT hide internal/arbitrary exceptions.
Propagation unwraps MUST execute inside a recovery scope, including those in deferred iterators and callbacks.
Creating an iterator or callback inside that scope MUST NOT substitute for executing its fallible work there.
An unguarded failed unwrap is an internal error.

## Temporary environment error bridges

External callbacks unable to return results MAY use shared `EnvironmentErrorsProxy`.
The nearest Donna-controlled boundary MUST recover it to `Result[T]`; it MUST NOT reach CLI rendering as an internal error.

## Exception boundaries

External boundaries MUST convert relevant expected low-level failures while useful context remains.
Shared returned errors already satisfy this obligation.
Examples include:

- filesystem access.
- TOML parsing.
- external-input Pydantic validation.
- Markdown/template parsing.
- configured Python imports.
- subprocesses/journal commands.

Raw external-input Pydantic failures MUST NOT cross high-level boundaries.
Donna-owned boundaries MUST convert `ValidationError`, `ValueError`, and similar expected validation failures into Donna errors; shared error results MUST propagate unchanged.
Unexpected bugs MUST remain exceptions.
Converted details SHOULD support diagnosis without user-facing stack traces.

## CLI mapping

`llm_tool_cli` MUST own skill failures and protocol-option validation/diagnostics.
Before result-based execution, Typer parsing MAY use standard invalid-argument behavior, including `typer.BadParameter`, `click.UsageError`, or `typer.Exit`.

After protocol installation, command handling provided by `llm_tool_cli` MUST own every environment error's:

- order.
- presentation.
- stdout delivery.
- exit.

Donna MUST NOT maintain another error-rendering/exit path.
Local context MUST retain workspace/runtime setup and restoration on success/failure without an error-journaling catch.

Shared terminal-error journals MUST bypass Donna's factory/session loading and MUST NOT require execution ids, including after failed initialization or cleanup.
Processor failures MUST NOT recursively journal themselves.
Non-CLI errors MAY declare shared-core exit overrides; termination MUST remain at the shared CLI boundary.

## Warnings

Warnings MUST represent only non-fatal problems allowing useful output.
They MUST NOT represent:

- invalid arguments.
- unloadable configuration.
- artifacts preventing requested validation.
- workflow execution failures.

They MUST use warning cells and scoped delivery provided by `llm_tool_cli`, buffered until finalization after results or reported errors.

## Naming error classes

Names SHOULD be short/descriptive.
When clear, leaf names SHOULD omit these redundant suffixes:

- `Error`.
- `Exception`.
- `Failure`.
- `Internal`.
- `Environment`.

Roots MUST retain the explicit categories required above.

## Asserts

Assertions MAY aid typing/lint when prior flow guarantees invariants.
They MUST NOT validate user/environment/artifact input or handle recoverable workflow failures, which MUST use environment errors.
Impossible states needing explicit handling SHOULD use internal errors.

## Other exception types

Production SHOULD use `InternalError` unless Python/third-party protocols require alternatives.
Such interfaces, Pydantic validators, and Typer/click parsing MAY use required exception types.
Shared technical result exceptions MAY implement controlled propagation but MUST NOT be mistaken for environment-error values.
Temporary `NotImplementedError` MAY appear during implementation and SHOULD be replaced before completion with implemented behavior or Donna errors.
