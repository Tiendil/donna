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
  - Donna extensions of shared error base classes.
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
  - immutable invocation-local execution identifiers for the current work unit and operation, scoped through shared context management.
  - cache interfaces, the collection of active caches and its independent binding, and artifact-rendering context data shared with workspace implementations.
  - direct construction of protocol-independent logic cells by machine-owned entities through `./donna/protocol/`.
- `./donna/runtime/` — module responsible for command-independent runtime orchestration. Contains:
  - session lifecycle use cases.
  - workflow execution loop coordination.
  - invocation-local wiring between context, machine, workspaces, and protocol-facing results.
  - command-facing domain results submitted as logic cells to the shared output emitter.
  - no CLI argument parsing.
- `./donna/context/` — module responsible for runtime cache implementations. Contains:
  - artifact, primitive, and session-state cache implementations.
- `./donna/primitives/` — module responsible for built-in primitive implementations. Contains:
  - artifact primitives.
  - section primitives.
  - directive primitives.
  - primitive-specific validation, rendering, and execution logic.
- `./donna/lib/` — module responsible for stable public names of built-in primitive instances used by Donna artifact configuration.
- `./donna/protocol/` — module responsible for Donna output boundary values and protocol formatting. Contains:
  - Donna-specific output value definitions and projections into shared cells used to communicate Donna results between modules.
  - projections of Donna-owned logical cells into output values, using shared cells for environment errors.
  - domain journal cells extending shared journal projections with Donna execution identifiers.
  - Donna-specific serialized record construction for external output protocols.
  - low-level output boundary infrastructure that MAY be used by any top-level module.
- `./donna/skills/` — module responsible for built-in skill document definitions and packaged Markdown resources.
- `./donna/workspaces/` — module responsible for workspace management, including:
  - application configuration schema and packaged starter configuration.
  - using the project root owned by shared project configuration.
  - operations with project files and directories.
  - artifact discovery and loading.
  - session state storage.
- `./donna/cli/` — module responsible for argument parsing, runtime invocation, protocol and stream selection, error handling, and writing returned or emitted logic cells through shared rendering.

Domain entities and runtime operations MUST assemble domain-result cells before returning or submitting them to shared output.
Donna MUST NOT introduce node wrappers or a node hierarchy for cell construction or composition.
Session detail output MUST compose the session summary followed by pending action-request cells in their stored order.
The CLI MUST NOT build domain-result payloads from internal domain objects.
Internal domain and machine APIs MAY retain their own typed results; the logic-cell contract applies at the boundary used to present domain results to the CLI.

The CLI MUST use `llm_tool_cli.skills` directly for skill-document loading and propagate its returned errors without local adapters.

Donna MUST use frozen `StaticConfig` in `llm_tool_cli.core.settings` for application identity and the default `donna.toml` filename before parsing, `RuntimeConfig` in `llm_tool_cli.config.runtime` for the effective protocol, and `ProjectConfig` in `llm_tool_cli.config.project` for the active config path and derived project directory.
The three shared context bindings MUST remain independent; project settings MUST be complete when bound after successful preparation and restored when the command context closes.
The `donna.workspaces.config.config` binding MUST use shared `ContextValue[Config]` for loaded Donna-specific settings.
The CLI MUST scope loaded settings around workspace-dependent execution, restoring the previous binding before shared terminal-error reporting.
Donna's project-command context MUST compose `llm_tool_cli.cli.context.command_context` with its runtime preparation and journal factory, without a local `CommandContext` subclass or error-journaling catch.
The CLI MUST use shared `load_project` with Donna's `Config` schema, retaining it through the framework command context's resource lifecycle.
The application MUST register initialization through `llm_tool_cli.cli.commands.initialization.register_init_command`, supplying Donna's `Config` schema and its initialization help text.
Shared initialization MUST retain its project context through the framework command context's resource lifecycle.
Discovery, loading, starter creation and validation, `ProjectConfig` construction, and project binding and restoration MUST belong to the shared library; Donna MUST NOT keep local preparation wrappers.
Initialization MUST supply the `donna.workspaces` resource package and `base_config.toml` template.
Donna MUST NOT maintain a parallel `GlobalConfig` implementation or a workspace wrapper duplicating runtime paths.

The machine module MUST own a frozen execution-context value containing the optional current work unit and operation identifiers, bound independently through shared `ContextValue`.
The CLI MUST bind an empty execution context for successfully prepared workspace commands, retaining it through command execution and restoring the previous binding before shared terminal-error reporting.
Work-unit and operation execution MUST use nested scopes that replace their respective identifier, preserve the other identifier, and restore the previous value after success or failure.
Journaling MUST obtain execution identifiers exclusively from this binding, which reflects the active execution scope.
The journal task identifier MUST always come from cached consistent session state, which identifies the task being processed until changes are saved.

The machine's public cache boundary MUST expose one collection of artifact, primitive, and session-state caches through a shared `ContextValue` binding.
Cache implementations MUST remain owned by the context module; machine code MUST access them through typed interfaces without importing context or workspace implementations.
Artifact-rendering context data used in cache interfaces MUST belong to the machine module.
The CLI MUST directly construct and bind fresh caches after successful workspace preparation, retain them through command execution, and restore the previous collection before shared terminal-error reporting.
Commands that do not load a workspace MUST NOT require cache construction.
Cache construction MUST NOT require a workspace argument or perform workspace I/O; artifact refresh and render-mode behavior, primitive lookup caching, and session-state external-change detection MUST be preserved.

The public `donna.machine.journal.journal_cell(*, message, actor_id) -> JournalCell` factory MUST construct Donna journal cells without submitting them.
Journal call sites MUST use `output.get().journal(...)`, supplying an explicit actor when needed; default actor selection MUST belong to the shared emitter.
The factory MUST obtain execution identifiers from the active execution context and the task identifier through the machine's state-cache interface on each call.
If session loading returns an environment failure or there is no active task, the factory MUST construct the event without a task identifier, preserving actor and execution context.
It MUST NOT accept task, work-unit, or operation identifier overrides because these must agree with the consistent state and active execution scopes.
The factory MUST preserve the supplied actor, including `None`, and leave processing, rendering, buffering, and stream delivery to the shared emitter.
Journal cells MUST NOT read context or load session state during construction or projection.
Donna MUST NOT maintain a journal service or journal context binding.
Failed preparation and project-independent commands MUST NOT journal errors through outer runtime services.
The emitter MUST own external processing before console delivery.
Execution identifiers, caches, and shared output MUST remain independently scoped; Donna MUST NOT maintain an aggregate application or machine service context that duplicates these bindings.

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

Shared result types, the common environment-error model, and the environment-error callback proxy MUST be provided by `llm_tool_cli` and imported directly from their owning modules.

The common entity base MUST be provided by `llm_tool_cli.core.entities` and imported directly by higher-level modules.

The `OutputCell` model, construction helpers, metadata conversion, and cell errors MUST be provided by `llm_tool_cli` and imported directly from their owning modules.
Donna's domain entities MUST produce logic cells with typed domain fields without accepting an output-cell type; their view selection remains Donna-owned.
Error presentation MUST use the shared environment-error logic cell directly.
The `donna.protocol.logic_cells` package MUST own domain-result cells and their projections into shared output cells.
Its public cell entities MUST be exported from `donna.protocol` for use by other top-level modules.
Artifact summaries, action-request instructions, and session-status messages MUST be constructed by those cells during projection.
Generic messages and already prepared documents MAY use shared content logic cells.
Logic-cell protocol dispatch, protocol-specific output-cell types, rendering contexts, and shared-error cell construction MUST be provided by `llm_tool_cli.protocol` and used directly.
Batch-rendering orchestration and stream writing MUST belong to the shared emitter in `llm_tool_cli.output`; individual projections and cell formatting MUST remain in the protocol layer.
Donna MUST retain ownership of its domain cell projections and journal context.
The public `donna.protocol.journal.JournalCell` MUST extend the shared journal cell with task, work-unit, and operation identifiers.
Its human and LLM projections MUST retain Donna's compact layouts, using shared escaping and automation journal serialization.
Donna MUST use shared journal records and MUST NOT maintain a separate record implementation, formatter family, output interface, output binding, or external command processor.
Journal-cell conversion MUST preserve Donna's captured execution identifiers as shared record attributes without consulting runtime state.
Workflow primitives, runtime operations, and journal construction MUST submit cells directly through `llm_tool_cli.output.output`.
Shared command setup MUST bind the emitter independently of project preparation.
After runtime preparation, Donna MUST configure the shared emitter with its journal-cell factory and the processor produced by shared journal configuration.
Donna MUST use the shared `JournalConfig` directly for command validation and processor construction, without a local subclass or field registry.
The configured emitter MUST remain available for shared finalization, but terminal-error conversion MUST bypass its Donna factory and MUST NOT access restored runtime bindings.
Programmatic callers MUST explicitly bind an emitter for output-producing behavior.
Session command operations without another useful result MUST submit their result cells and return `Result[None]`.
The `render` command MUST submit its prepared Markdown document as a Donna-owned `RenderedArtifactCell` through the emitter.
Artifact-status, rendered-artifact, action-request, and session-state cells MUST prohibit journaling with `is_journal: Literal[False]` and MUST NOT implement journal-record conversion.
Generic content cells MUST retain the shared prohibition on journaling.

Lexical project-path normalization, filesystem resolution and containment, symlink rejection, and file enumeration MUST be provided by `llm_tool_cli` and used directly.
Donna MUST retain artifact-specific path behavior, workflow-directory selection and ordering, and artifact-extension filtering.
Fallible artifact discovery MUST return shared results and propagate enumeration failures through the artifact cache.

### Submodule nuances

#### `errors`

The `errors` submodule owns module-specific exception classes and error values.

Errors SHOULD express project-level failure modes that callers can handle, not low-level library details.

#### `entities`

The `entities` submodule owns module-specific types, semantic ids, enums, and entities that represent the module's concepts.

Entities SHOULD describe domain data and boundary data, not storage implementation details unless storage metadata is itself part of the project concept.

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

### Import boundaries

Top-level modules MUST expose stable cross-module APIs through declared public import boundaries.

A public import boundary MAY be:

- the top-level module package root, such as `donna.domain`.
- a declared public submodule, such as `donna.domain.artifact_ids`.

Public import boundaries MUST be explicit enough for maintainers to distinguish stable cross-module API from implementation detail.

A public submodule SHOULD expose cohesive concepts owned by its top-level module.

A public submodule MUST NOT expose low-level helper functions, temporary implementation details, storage-only helpers, or compatibility shims unless those names are intentionally stable.

Top-level module package initializers SHOULD export common public names when doing so improves ergonomics.

Top-level module package initializers MUST NOT be required to re-export every public name from declared public submodules.

When a top-level module owns an `errors` submodule, the package initializer MUST include the `errors` submodule in the public cross-module API.

The package initializer SHOULD define `__all__` to list the names that are intended as the module root public cross-module API.

If a top-level module has no useful module-root public cross-module API, its package initializer MAY be empty or define an empty `__all__`.

Top-level modules MUST import another top-level module only through that module's declared public import boundaries.

For example, `donna.cli` MAY import from `donna.workspaces` and from public submodules declared by `donna.workspaces`, but MUST NOT import from undeclared implementation submodules.

Top-level modules MUST NOT import undeclared implementation submodules from another top-level module.

Submodules inside the same top-level module MAY import each other directly.

The `utils` submodule is not a public import boundary unless a top-level module explicitly declares it as one.

Top-level modules MAY import protocol-owned boundary values and generic projection helpers from `donna.protocol` when they need to expose their owned concepts as Donna output units.

Constructing logic cells from typed domain data is not protocol-specific rendering and MUST NOT be treated as a module-boundary violation.

Top-level modules outside `./donna/protocol/` and `./donna/cli/` MUST NOT depend on protocol-specific formatter implementation submodules.

Top-level modules outside `./donna/protocol/` SHOULD NOT own protocol-specific serialization details.

Protocol-specific rendering means selecting or implementing concrete external serialization for a protocol, such as terminal text framing, LLM-oriented boundary syntax, automation JSON Lines records, byte output, or formatter-specific ordering rules.

Constructing logic cells with typed domain fields is not protocol-specific rendering.

## Data structures

Project data structures SHOULD inherit from `llm_tool_cli.core.entities.BaseEntity` unless a third-party interface or standard-library protocol requires another type.

Project data structures MUST NOT use `dataclass` for domain entities.
