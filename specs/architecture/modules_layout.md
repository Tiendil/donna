# Module structure

## Goal of the document

This document describes the intended module structure of the project.

## Scope

The scope of this specification is limited to the list of project modules and their intended responsibilities.

The following topics are out of scope:

- detailed implementation design.
- runtime behavior.
- migration planning.
- entity, error, and test conventions beyond module placement.

## Dictionary

- `module` — a Python package or module that owns a coherent area of project functionality.
- `submodule` — a Python package or module inside another module that owns a narrower part of its parent module's functionality.
- `test submodule` — a module or file containing tests for a corresponding parent module or submodule.

## Modules

- `./donna/` — root module of the project, contains all code related to the `donna` tool.
- `./donna/core/` — module responsible for the core functionality not related to domain logic. Contains:
  - shared entity base classes.
  - shared error base classes.
  - shared result types.
  - domain-independent utilities.
- `./donna/domain/` — module responsible only for universal domain entities and logic required by all or most other modules. Contains:
  - shared domain-specific types.
  - shared domain data structures.
  - pure domain logic that is independent of more specific subsystems.
  - no subsystem-specific rule evaluation, protocol rendering, workspace loading, or CLI behavior.
- `./donna/machine/` — module responsible for Donna workflow execution logic. Contains:
  - session state entities.
  - task, work unit, and action request entities.
  - state changes.
  - operation and primitive interfaces.
  - workflow execution orchestration that is independent of CLI argument parsing and protocol-specific formatting.
  - protocol-facing views of machine-owned concepts expressed as protocol-neutral output values from `./donna/protocol/`.
- `./donna/runtime/` — module responsible for command-independent runtime orchestration. Contains:
  - session lifecycle use cases.
  - workflow execution loop coordination.
  - invocation-local wiring between context, machine, workspaces, and protocol-facing results.
  - journal event forwarding orchestration.
  - no CLI argument parsing.
- `./donna/context/` — module responsible for invocation-local runtime context. Contains:
  - context-local caches.
  - context-local execution scopes.
  - glue that gives machine and primitive logic access to loaded artifacts, primitive registries, and session state.
- `./donna/primitives/` — module responsible for built-in primitive implementations. Contains:
  - artifact primitives.
  - section primitives.
  - directive primitives.
  - primitive-specific validation, rendering, and execution logic.
- `./donna/lib/` — module responsible for stable public names of built-in primitive instances used by Donna artifact configuration.
- `./donna/protocol/` — module responsible for Donna output boundary values and protocol formatting. Contains:
  - protocol-neutral output value definitions used to communicate Donna results between modules.
  - generic helpers for projecting Donna-owned data and errors into output values.
  - protocol enums.
  - formatter selection.
  - protocol-specific formatters that serialize output values for human, llm, and automation output.
  - serialized record construction for external output protocols.
  - low-level output boundary infrastructure that MAY be used by any top-level module.
- `./donna/skills/` — module responsible for built-in skill text loaded by the CLI and renderers.
- `./donna/workspaces/` — module responsible for workspace management, including:
  - finding and parsing config.
  - detecting current project root.
  - operations with project files and directories.
  - artifact discovery and loading.
  - session state storage.
  - journal forwarding.
- `./donna/cli/` — module responsible for the CLI interface of the `donna` tool.

## Submodules

Modules can have submodules that are responsible for more specific parts of the functionality.

When a module contains a small closed family of interchangeable components, and each component has meaningful component-specific behavior, the module SHOULD prefer one implementation submodule per component.

Shared package-level code for such component families SHOULD be limited to common types, public unions, selection helpers, and iteration glue.

Submodules are optional implementation details unless another specification explicitly requires them.

Some optional submodules have specific names that reflect their responsibilities and SHOULD be similar across different modules when those submodules exist.

List of specific submodules:

- `utils` — submodule responsible for utility functions that are not related to domain logic.
- `errors` — submodule responsible for defining custom exception types.
- `entities` — submodule responsible for defining types and entities related to the module's responsibilities.
- `fixtures` — submodule containing reusable configuration, documentation, or data fixtures owned by the module.
- `tests` — submodule containing module tests.
- `tests.make` — test-only submodule containing constructors for test objects related to the parent module.
- `tests.helpers` — test-only submodule containing reusable test setup, mutation, and workflow helpers.

The `errors`, `entities`, and `tests` submodules MUST follow the corresponding architecture specifications when they are present.

The shared `entities` submodule in `./donna/core/` MUST define the common entity base used by higher-level modules.

### Submodule nuances

#### `errors`

The `errors` submodule owns module-specific exception classes and error values.

Errors SHOULD express project-level failure modes that callers can handle, not low-level library details.

Error classes and error values that are part of a top-level module's public API MUST be exported from that module's package initializer.

When a top-level module owns an `errors` submodule, its package initializer MUST export that submodule under the name `errors`.

Top-level modules MAY import another top-level module's exported `errors` submodule from the owning module's package root.

#### `entities`

The `entities` submodule owns module-specific types, semantic ids, enums, and entities that represent the module's concepts.

Entities SHOULD describe domain data and boundary data, not storage implementation details unless storage metadata is itself part of the project concept.

Entity classes and other shared boundary types that are part of a top-level module's public API MUST be exported from that module's package initializer.

#### `utils`

The `utils` submodule owns small helpers that do not naturally belong to entities, settings, integration boundaries, or a more specific submodule.

Utility functions SHOULD be pure or locally technical when practical. If a helper starts to encode module behavior, it SHOULD move to a more specific submodule.

Top-level modules SHOULD avoid depending on another top-level module's `utils` submodule because utilities are not a stable cross-module boundary.

#### `tests`

The `tests` submodule owns colocated tests for the parent module and its submodules.

Tests SHOULD exercise behavior through public boundaries when practical, while storage-focused tests MAY verify storage-specific behavior owned by the module.

Test files SHOULD mirror implementation module names with the `test_` prefix and organize test classes around the tested function or class.

#### `make`

The `make` submodule MAY appear only inside tests packages, as `<module>.tests.make`.

`tests.make` owns constructors and factory helpers for test objects related to the parent module.

Tests SHOULD put reusable object construction in `tests.make` instead of duplicating constructors across test files.

Production modules MUST NOT import `tests.make`.

#### `helpers`

The `helpers` submodule MAY appear inside tests packages, as `<module>.tests.helpers`.

`tests.helpers` owns reusable test helpers that perform setup, mutate persisted test state, call module behavior, or wrap common test workflows.

Object constructors and pure fake data factories SHOULD live in `tests.make`; helpers that perform actions or coordinate multiple calls SHOULD live in `tests.helpers`.

Production modules MUST NOT import `tests.helpers`.

## Cross-module dependencies

Each top-level module MUST define its public cross-module API in its package initializer, `__init__.py`.

The package initializer MUST explicitly import or define every type, function, constant, and object that another top-level module may import from the module.

When a top-level module owns an `errors` submodule, the package initializer MUST include the `errors` submodule in the public cross-module API.

The package initializer SHOULD define `__all__` to list the names that are intended as the module's public cross-module API.

If a top-level module has no public cross-module API, its package initializer SHOULD be empty or define an empty `__all__`.

Top-level modules MUST import another top-level module's public API only from that module's package root.

For example, `donna.cli` MAY import from `donna.workspaces`, including `from donna.workspaces import errors as workspace_errors` when `donna.workspaces` exports `errors`, but MUST NOT import from `donna.workspaces.config`, `donna.workspaces.entities`, `donna.workspaces.errors`, or any other `donna.workspaces` submodule.

Top-level modules MUST NOT import implementation submodules from another top-level module.

Top-level modules MAY import protocol-owned boundary values and generic projection helpers from `donna.protocol` when they need to expose their owned concepts as Donna output units.

Constructing protocol-neutral output values is not protocol-specific rendering and MUST NOT be treated as a module-boundary violation.

Top-level modules outside `./donna/protocol/` and `./donna/cli/` MUST NOT depend on protocol-specific formatter implementation submodules.

Top-level modules outside `./donna/protocol/` SHOULD NOT own protocol-specific serialization details.

Protocol-specific rendering means selecting or implementing concrete external serialization for a protocol, such as terminal text framing, LLM-oriented boundary syntax, automation JSON Lines records, byte output, or formatter-specific ordering rules.

Constructing protocol-neutral output values with kind, content, media type, and metadata is not protocol-specific rendering.

## Data structures

Project data structures SHOULD inherit from `donna.core.entities.BaseEntity` unless a third-party interface or standard-library protocol requires another type.

Project data structures MUST NOT use `dataclass` for domain entities.
