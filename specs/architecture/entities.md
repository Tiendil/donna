# Entity architecture

## Goal of the document

This document describes the architecture of project entities and data structures used to pass artifact, workflow, configuration, session, protocol, and command information between modules.

## Scope

The scope of this specification is limited to architectural requirements for Python data structures that represent project concepts.

The following topics are out of scope:

- exact class names.
- exact constructor signatures.
- serialization formats for CLI protocols.
- workflow execution algorithms.
- Markdown parsing algorithms.
- validation rules already specified by behavior specifications.

## Dictionary

- `entity` — a typed Python object that represents one project concept and can be passed across module boundaries.
- `value entity` — an entity whose equality is based on its data rather than object identity.
- `data entity` — an entity that primarily carries validated data across boundaries or into serialization.
- `domain entity` — an entity that owns behavior, invariants, or state transitions for a project concept.
- `boundary entity` — an entity that is passed between modules with different responsibilities.
- `serialized representation` — a plain data representation prepared for an external protocol such as JSON Lines, Markdown output, logs, or persistent storage.

## General principles

Project concepts MUST be represented as explicit typed entities before they cross module boundaries.

Boundary entities MUST NOT be represented as untyped dictionaries unless the data is already being prepared as a serialized representation.

Project entities SHOULD use Pydantic v2 for structured data models.

### Data entities

Data entities SHOULD limit behavior to validating, normalizing, copying, serializing, and deriving values from their
own fields.

Data entities MUST NOT access invocation-local context, load artifacts, execute primitives, mutate session state, or
perform low-level infrastructure work.

### Domain entities

Domain entities MAY be rich domain objects.

Domain entities SHOULD keep behavior close to the state, invariants, transitions, and domain operations they own.
They MAY:

- change their own state or apply state changes.
- derive facts from their own state.
- validate related project objects.
- coordinate behavior through typed collaborator or invocation-local context interfaces.

Domain entity methods SHOULD keep direct infrastructure details behind collaborator interfaces or module boundaries.

If an entity directly touches an external resource, the entity MUST be owned by the module responsible for that
resource and SHOULD represent that resource explicitly.

Entities MUST NOT directly perform low-level infrastructure work unrelated to their owned concept, such as:

- filesystem access.
- process execution.
- terminal output.
- configuration file discovery.
- workspace loading.

Entities MAY call typed collaborators or context objects that perform those operations when the behavior and
dependency are part of the module's public contract.

### Value entities

Value entities SHOULD be immutable after construction when practical.

Entities that can be used for de-duplication SHOULD be hashable when practical.

## Pydantic baseline

The project accepts Pydantic v2 as the default dependency for entity modeling.

The project SHOULD provide shared base entity infrastructure owned by the core module.

Project entities SHOULD inherit from the shared base entity unless they have a specific reason to use Pydantic directly.

Direct Pydantic usage MAY be used for:

- configuration objects that mirror external input shapes.
- external transfer objects that intentionally mirror boundary-facing data shapes.
- third-party interfaces that require a direct Pydantic model shape.

Shared entity defaults SHOULD:

- strip surrounding whitespace from string values.
- validate default values.
- reject unknown fields.
- prefer immutable value objects where practical.
- validate assignment when mutation is explicitly enabled.
- avoid attribute-based construction unless a boundary explicitly needs it.

Entities SHOULD use Pydantic field metadata and validators for local field constraints, default factories, discriminators, and model invariants.

Entities SHOULD use Pydantic serialization methods at boundaries that need model dumps or JSON.

The shared base entity MUST provide a copy-with-changes operation.

Very small internal helper values MAY use plain Python classes with `__slots__` when Pydantic would add no practical value.

Project data structures MUST NOT use `dataclasses.dataclass`.

## Enumeration conventions

Closed sets of named values MUST be represented as Python enum classes.

String-valued external protocols, render modes, record kinds, primitive modes, document names, and similar closed type sets SHOULD use `enum.StrEnum`.

Integer-valued closed sets SHOULD use `enum.IntEnum` when the integer value is part of the external contract or persisted state.

Enum classes MUST use `enum.StrEnum` or `enum.IntEnum` instead of `str, enum.Enum` or `int, enum.Enum`.

Plain strings MUST NOT be used as the primary internal representation for values that have a finite configured, persisted, or specified set of allowed names.

Enum values that cross external boundaries MUST preserve the specified serialized or persisted value exactly.

Output protocol values are a closed set of named string values and MUST be represented internally with an enum rather than raw strings or lists of strings.

## Semantic primitive types

Semantically specific primitive values MUST have semantically specific Python types before they cross module boundaries.

For example, an artifact id, artifact section id, section id, action request id, work unit id, task id, project path, or primitive path MUST NOT be represented as an unqualified primitive value in entities or public function signatures when the value has a distinct Donna meaning.

Semantic primitive types SHOULD use `typing.NewType` when runtime behavior is identical to the underlying primitive.

Semantic primitive types MAY use small custom classes when they need validation, normalization, ordering, immutability, Pydantic integration, or custom string rendering.

Raw primitive types MAY be used at parsing, rendering, storage, and serialization boundaries where external data is converted into or out of project types.

Raw primitive types MAY be used inside local helper code when the value has already been validated or when adding a semantic type would not improve module-boundary clarity.

Semantic primitive types SHOULD be owned by the module that owns the corresponding project concept.

Shared semantic primitive types SHOULD belong to the domain module.

Module-specific semantic primitive types SHOULD belong to the owning module.

## Entity ownership

Shared entity infrastructure MUST belong to the core module.

Shared domain primitive types and universal domain entities MUST belong to the domain module.

Module-specific entities MUST belong to the module that owns the corresponding responsibility.

Entity classes that are part of a top-level module's public cross-module API MUST be exported from the owning module's package initializer.

Top-level modules MUST import public entities owned by another top-level module from the owning module's package root.

Public re-exports MUST NOT hide ownership. The defining module MUST remain clear from the source tree.

## Core and domain entities

The core module MUST contain only shared entity infrastructure.

Core entity infrastructure MUST NOT contain domain-specific Donna concepts such as artifacts, workflows, sections, sessions, protocols, primitives, or workspace paths.

The domain layer MUST contain only universal entities and semantic primitive types for concepts shared by all or most other modules.

Domain entities MUST model universal Donna concepts independently from the concrete interface that created or renders them.

Domain entities MUST NOT depend on CLI option parsing, output protocol rendering, workspace loading, session storage, or concrete configuration file syntax.

Domain entities MUST NOT contain subsystem-specific entities when those entities are required only by one narrower module.

## Configuration entities

Configuration entities MAY represent parsed TOML data at the configuration loading boundary when their responsibility is to validate the configuration file shape.

Configuration entities SHOULD use Pydantic validation to reject malformed parsed data before it reaches lower layers.

Workspace entities MUST model validated configuration concepts independently from raw TOML table shapes before data reaches lower layers.

Workspace entities MUST expose shared project concepts as domain entities rather than configuration-specific entities.

Configuration entities MUST preserve enough information to report useful configuration errors.

Configuration entities MUST NOT execute workflow artifacts, run primitives, write session state, or forward journal records.

Configuration entities MAY reference domain entities when the referenced concept has already been validated as a domain concept.

## CLI and command entities

CLI entities MUST represent parsed user intent before the command is executed.

CLI entities MUST model command selection and parsed options independently from rendered output.

CLI entities MUST NOT contain rendered output.

CLI entities MUST NOT perform command execution.

CLI entities SHOULD use domain semantic primitive types for parsed ids and paths when the values have already been normalized or validated.

## Protocol and serialization entities

Serialized representations MUST be created at protocol boundaries and SHOULD be treated as write-only output data.

Serialized representations SHOULD be produced from entities through explicit boundary code, not by leaking Pydantic dump shapes into domain behavior.

Protocol entities MAY contain presentation-oriented metadata when their responsibility is output formatting.

Domain, machine, workspace, and CLI entities SHOULD NOT depend on concrete serialized protocol record shapes.

Entity methods that return dictionaries for protocol metadata, logging, or storage MUST return structured values with stable keys and MUST NOT contain terminal formatting.

## Data structure conventions

Ordered input from users, workflow artifacts, configuration files, and persisted session state SHOULD be represented with ordered collections.

Sets MAY be used internally for de-duplication, but externally visible output order MUST be produced explicitly according to the relevant behavior specification.

Mappings keyed by semantic ids SHOULD use the semantic id type when possible.

Optional values MUST be represented with `None` instead of sentinel strings.

Collections that represent stacks, queues, or ordered workflow state MUST preserve order explicitly.

## Validation boundaries

Parsing layers SHOULD validate external data before creating entities that are used by lower layers.

Pydantic model validation MAY validate local invariants that are always true for the entity, but MUST NOT perform
filesystem access, configuration discovery, workspace loading, artifact discovery, primitive execution, subprocess
execution, or command execution.

Validation that requires those operations MUST live in behavior methods, runtime orchestration, or functions that return Donna-specific errors.

Invalid external input MUST be reported through the error architecture instead of by returning partially valid entities.
