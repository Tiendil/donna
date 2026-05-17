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
  - protocol-facing views of machine-owned entities expressed through protocol-neutral boundary entities.
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
- `./donna/protocol/` — module responsible for Donna output boundary entities and rendering. Contains:
  - protocol-neutral output entities such as cells, nodes, and journal records.
  - protocol enums.
  - formatter selection.
  - protocol-specific formatters.
  - serialized record construction for external output protocols.
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

Some submodules have specific names that reflect their responsibilities and SHOULD be similar across different modules.

List of specific submodules:

- `utils` — submodule responsible for utility functions that are not related to domain logic.
- `errors` — submodule responsible for defining custom exception types.
- `domain` — submodule responsible for internal business logic related to the module's responsibilities.
- `entities` — submodule responsible for defining types and entities related to the module's responsibilities.
- `operations` — submodule responsible for low-level communication with storage, local files, external tools, or other systems owned by the module.
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

Top-level modules MAY import another top-level module's `errors` submodule when they need to catch or raise errors owned by that module.

#### `entities`

The `entities` submodule owns module-specific types, semantic ids, enums, and entities that represent the module's concepts.

Entities SHOULD describe domain data and boundary data, not storage implementation details unless storage metadata is itself part of the project concept.

Top-level modules MAY import another top-level module's `entities` submodule for shared boundary types.

#### `domain`

The `domain` submodule owns the parent module's internal business logic and is the public behavior boundary for other top-level modules.

Domain functions SHOULD compose lower-level operation functions and other module boundaries into meaningful workflows, own business decisions, convert or raise module-owned errors, and shape results for callers.

Domain functions SHOULD hide low-level communication details from callers.

Top-level input layers such as `./donna/cli/` SHOULD call domain boundaries instead of low-level operation helpers when invoking business behavior.

When a domain-level function only exposes an operation function without adding behavior, the `domain` submodule SHOULD prefer a direct assignment alias instead of a trivial wrapper.

Domain wrappers SHOULD be used when they add real behavior, such as orchestration, validation, persistence boundary ownership, fallback logic, caching, error conversion, or result shaping.

#### `operations`

The `operations` submodule owns low-level communication with systems outside the module's internal logic.

Operation functions MAY communicate with local files, subprocesses, external tools, or other infrastructure owned by the module's responsibility.

Operation functions SHOULD contain communication protocol details, low-level error translation, raw response handling, storage idempotency, and technical maintenance helpers owned by the module.

Operation functions SHOULD NOT own high-level business workflows. They SHOULD provide small communication primitives that the module's `domain` submodule can compose.

Operation functions SHOULD NOT be imported by other top-level modules. Cross-module callers SHOULD use the owning module's `domain`, `entities`, or `errors` boundary instead.

#### `utils`

The `utils` submodule owns small helpers that are not domain workflows and do not naturally belong to entities, operations, settings, or integration boundaries.

Utility functions SHOULD be pure or locally technical when practical. If a helper starts to encode module behavior, it SHOULD move to `domain`, `operations`, or a more specific submodule.

Top-level modules SHOULD avoid depending on another top-level module's `utils` submodule because utilities are not a stable cross-module boundary.

#### `tests`

The `tests` submodule owns colocated tests for the parent module and its submodules.

Tests SHOULD exercise behavior through public boundaries when practical, while operation tests MAY verify storage-specific behavior owned by the module.

Test files SHOULD mirror implementation module names with the `test_` prefix and organize test classes around the tested function or class.

#### `make`

The `make` submodule MAY appear only inside tests packages, as `<module>.tests.make`.

`tests.make` owns constructors and factory helpers for test objects related to the parent module.

Tests SHOULD put reusable object construction in `tests.make` instead of duplicating constructors across test files.

Production modules MUST NOT import `tests.make`.

#### `helpers`

The `helpers` submodule MAY appear inside tests packages, as `<module>.tests.helpers`.

`tests.helpers` owns reusable test helpers that perform setup, mutate persisted test state, call module operations, or wrap common test workflows.

Object constructors and pure fake data factories SHOULD live in `tests.make`; helpers that perform actions or coordinate multiple calls SHOULD live in `tests.helpers`.

Production modules MUST NOT import `tests.helpers`.

## Cross-module dependencies

Top-level modules that need types or values from another top-level module SHOULD use only that module's `domain`, `entities`, and `errors` submodules when those submodules exist.

Top-level modules MAY import another module's `errors` submodule when they need to catch or raise errors owned by that module.

Top-level modules MUST NOT import implementation submodules from another top-level module when a public boundary exists.

Top-level modules MUST NOT import another top-level module's `operations` submodule.

Top-level modules MAY import protocol-neutral boundary entities from `./donna/protocol/` when they need to expose their owned concepts as Donna output units.

Top-level modules outside `./donna/protocol/` and `./donna/cli/` SHOULD NOT depend on protocol-specific formatter implementation submodules.

## Data structures

Project data structures SHOULD inherit from `donna.core.entities.BaseEntity` unless a third-party interface or standard-library protocol requires another type.

Project data structures MUST NOT use `dataclass` for domain entities.
