# Entity architecture

## Goal of the document

This document describes project entities and cross-module data.

## Scope

Python data structures representing project concepts; the following are out of scope:

- exact class names and constructor signatures.
- CLI serialization formats.
- workflow execution and Markdown parsing algorithms.
- behavioral validation rules.

## Dictionary

- `entity` — a typed object representing one project concept across modules.
- `value entity` — an entity compared by data rather than identity.
- `data entity` — validated data carried across boundaries or into serialization.
- `domain entity` — an entity owning concept behavior, invariants, or transitions.
- `boundary entity` — an entity crossing responsibility boundaries.
- `serialized representation` — plain data for:

  - protocols.
  - Markdown output.
  - logs.
  - storage.

## General principles

Project concepts MUST cross boundaries as explicit typed entities, not untyped dictionaries except for serialized data.
Structured entities SHOULD use Pydantic v2.

### Data entities

Data entities SHOULD limit behavior to:

- validation.
- normalization.
- copying.
- serialization.
- derivation from their fields.

They MUST NOT:

- access invocation context.
- load artifacts.
- execute primitives.
- mutate sessions.
- perform low-level infrastructure work.

### Domain entities

Introducing a domain entity or converting a data entity into a domain entity MUST have explicit developer approval before implementation.

Domain entities MAY be rich objects and SHOULD keep behavior with their owned:

- state.
- invariants.
- transitions.
- operations.

They MAY:

- change their state or apply changes.
- derive state facts.
- validate related objects.
- coordinate through typed collaborators or invocation context.

Methods SHOULD hide infrastructure behind collaborators or module boundaries.
An entity directly touching an external resource MUST belong to that resource's module and SHOULD represent it explicitly.
Entities MUST NOT directly perform unrelated low-level infrastructure work, such as:

- filesystem access.
- process execution.
- terminal output.
- configuration discovery.
- workspace loading.

Typed collaborators or contexts MAY perform these operations when behavior and dependency are public module contracts.

### Value entities

Value entities SHOULD be immutable when practical; deduplicatable entities SHOULD be hashable when practical.

## Pydantic baseline

Pydantic v2 is the default modeling dependency.
The project MUST use `llm_tool_cli.core.entities` infrastructure.
Entities SHOULD inherit its base unless direct Pydantic use has a specific reason, such as external configuration/transfer shapes or third-party model contracts.

Shared defaults SHOULD:

- strip surrounding string whitespace.
- validate defaults.
- reject unknown fields.
- prefer immutable values.
- validate assignment when mutation is enabled.
- avoid attribute-based construction unless a boundary needs it.

Entities SHOULD use Pydantic fields/validators for:

- local constraints.
- defaults.
- discriminators.
- invariants.

They SHOULD use Pydantic serialization for dumps/JSON.

The shared base MUST provide copy-with-changes.
Small internal helpers MAY use plain slotted classes when Pydantic adds no value.
Data structures MUST NOT use `dataclasses.dataclass`.

## Enumeration conventions

Closed named sets, including output protocols, MUST use enums rather than primarily raw strings or string lists.
String sets MUST use `enum.StrEnum`; integer sets MUST use `enum.IntEnum` when externally contracted or persisted.
Enums MUST use these standard bases instead of `str, enum.Enum` or `int, enum.Enum`.
External and persisted values MUST remain exact.

## Semantic primitive types

Distinct Donna primitive meanings MUST use semantic Python types across boundaries, in entities, and in public signatures.
Examples include:

- artifact/section ids.
- execution ids.
- project paths.
- primitive paths.

`typing.NewType` SHOULD be used when runtime behavior matches the primitive.
Small custom classes MAY add:

- validation.
- normalization.
- ordering.
- immutability.
- Pydantic integration.
- rendering.

Raw primitives MAY appear at these boundaries:

- parsing.
- rendering.
- storage.
- serialization.

They MAY also appear in local helpers after validation or when semantic typing adds no boundary clarity.

Shared semantic types SHOULD belong to the domain module; others SHOULD belong to their concept's owner.

## Static typing suppressions

For semantic relationships guaranteed by validation or construction at the same boundary, code SHOULD prefer local `# type: ignore[...]` over `typing.cast(...)` or runtime no-ops such as `str(...)`.
Suppressions MUST be as narrow as practical, include available checker error codes, and MUST NOT bypass validation, unsafe input conversion, or actual type mismatches.
Runtime constructors and validators SHOULD remain preferred for untrusted primitive conversion.

## Entity ownership

Reusable entity infrastructure MUST belong to `llm_tool_cli.core`; universal Donna entities and primitives shared across Donna modules MUST belong to `donna.domain`; other entities MUST belong to their responsibility's module.
Public cross-module entity classes MUST be exported from, and imported through, the owning top-level package root.
Re-exports MUST keep the defining owner clear.

## Core and domain entities

Entity infrastructure from `llm_tool_cli.core` MUST NOT be duplicated in Donna or contain Donna-specific concepts.
The domain layer MUST contain only universal concepts shared by all or most modules, independent of creating/rendering interfaces.
It MUST NOT contain narrower subsystem entities or depend on:

- CLI option parsing.
- protocol rendering.
- workspace loading.
- session storage.
- concrete configuration syntax.

## Configuration entities

Configuration entities MAY validate parsed TOML shape or reference validated domain entities.
They SHOULD reject malformed input with Pydantic before lower layers and MUST preserve useful error context.
Workspace entities MUST expose validated, file-shape-independent configuration concepts and shared concepts as domain entities.
Configuration entities MUST NOT:

- execute artifacts.
- execute primitives.
- write session state.
- forward journals.

## CLI and command entities

CLI entities MUST represent parsed selection/options before execution, independently of output, and MUST NOT contain rendered output or execute commands.
Normalized or validated ids/paths SHOULD use domain semantic types.

## Protocol and serialization entities

Logic cells MUST be the primary successful domain-to-CLI interface.
Command-facing operations MAY submit cells to the scoped emitter provided by `llm_tool_cli` and return `Result[None]` when no other result is useful.
Reusable computations MAY return typed values, including cells and ordered collections; internal domain operations MAY retain ordinary entities.
Cells MAY hold typed projection data, but the CLI MUST NOT inspect it or assemble domain payloads.

Cells MUST carry projection data without runtime reads or output writes.
CLI initialization MUST establish delivery and protocol; the shared emitter MUST buffer and deliver cells.
Expected failures MUST remain structured failed-result errors until the CLI error boundary.
Acknowledgements, journals, and rendered Markdown MUST use logical cells with their specified representations.

Serialized representations MUST originate at protocol boundaries and SHOULD be write-only, produced through explicit boundary code rather than leaking Pydantic dump shapes into domain behavior.
Protocol entities MAY contain formatting metadata.
The following entities SHOULD NOT depend on concrete record shapes:

- domain entities.
- machine entities.
- workspace entities.
- CLI entities.

Metadata/logging/storage dictionaries MUST contain stable structured keys and MUST NOT format terminal output.

## Data structure conventions

The following ordered input SHOULD use ordered collections:

- user input.
- artifact input.
- configuration input.
- persisted input.

Sets MAY deduplicate internally, but observable order MUST follow behavior specs explicitly.
Semantic-id mappings SHOULD use semantic key types when possible.
Optional values MUST use `None`, not sentinel strings.
Stacks, queues, and ordered workflow state MUST preserve order explicitly.

## Validation boundaries

Parsing layers SHOULD validate external input before constructing lower-layer entities.
Model validation MAY enforce local invariants but MUST NOT perform:

- filesystem access.
- configuration or artifact discovery.
- workspace loading.
- primitive execution.
- subprocess or command execution.

Such validation MUST live in behavior methods, runtime orchestration, or functions returning Donna-specific errors.
Invalid input MUST follow the error architecture, never produce partially valid entities.
