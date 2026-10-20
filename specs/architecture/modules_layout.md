# Module structure

## Goal of the document

This document describes module ownership and public boundaries.

## Scope

This specification covers project modules and responsibilities.
The following are out of scope:

- detailed implementation.
- runtime behavior.
- migrations.
- entity/error/test conventions beyond placement.

## Dictionary

- `module` — a Python package/module owning coherent functionality.
- `submodule` — a narrower responsibility within a module.
- `test submodule` — tests of a parent module/submodule.

## Modules

All Donna code belongs under `donna/`:

- `core` — Donna error-base extensions and domain-independent utilities.
- `domain` — Universal types, structures, and pure logic used by all/most modules; excludes:

  - Subsystem rules.
  - Rendering.
  - Workspace loading.
  - CLI behavior.

- `machine`:

  - Entities and changes for:

    - Sessions.
    - Tasks.
    - Work units.
    - Action requests.

  - Operation/primitive interfaces.
  - Execution independent of CLI parsing/formatting.
  - Scoped execution ids.
  - Cache interfaces/binding.
  - Shared artifact-rendering context.
  - Direct logic-cell construction.

- `runtime` — No CLI parsing; owns:

  - Command-independent session lifecycle.
  - Execution loop.
  - Invocation wiring among context/machine/workspaces and results.
  - Result submission.

- `context` — Artifact, primitive, and session-state cache implementations.
- `primitives` — Built-in artifact/section/directive primitives with validation, rendering, and execution.
- `lib` — Stable configured names of constructed built-in primitives.
- `protocol`:

  - Donna output values.
  - Typed logic-cell projections.
  - Execution-aware journal cells.
  - Serialized records.
  - Boundary infrastructure available to all modules.

- `skills` — Document definitions and packaged Markdown.
- `workspaces`:

  - Application schema/starter.
  - File operations.
  - Discovery/loading.
  - Session storage using the project root provided by `llm_tool_cli`.

- `cli`:

  - Parsing.
  - Runtime invocation.
  - Protocol/stream selection.
  - Error handling.
  - Cell delivery through `llm_tool_cli`.

Domain/runtime MUST assemble cells before returning/submitting them; CLI MUST NOT assemble payloads from internal objects.
Donna MUST NOT introduce node wrappers/hierarchies.
Session details MUST compose summary then pending requests in stored order.
Internal domain/machine APIs MAY retain typed results.
Skill loading MUST directly use `llm_tool_cli.skills`, preserving errors without adapters.
Skill fixtures MUST live in `donna/skills/fixtures/` under the library's resource-loading convention; Donna MUST own document definitions and contents.
CLI MUST use application construction and shared skill/version command registration from `llm_tool_cli`, supplying `donna.skills`, its document definitions, and distribution identity `donna`.

Donna MUST use independent frozen settings from `llm_tool_cli` for static application identity, invocation protocol, and selected project.
Static settings MUST supply the default configuration filename before parsing; project settings MUST own the active path and derived root.

Donna-owned context bindings MUST use the context-management infrastructure provided by `llm_tool_cli`.
Complete project settings MUST be bound only after successful preparation and restored at command closure.
Loaded application settings MUST have an independent typed context binding owned by workspaces, scoped through workspace execution and restored before shared terminal-error reporting.
Root version and session-directory fields MUST use validation provided by `llm_tool_cli`.
Donna MUST own supported versions/defaults; shared validation MUST apply its constraint.
Workflow directories MUST reuse relative-path validation provided by `llm_tool_cli` while Donna owns ordering, deduplication, and serialization.
Donna MUST NOT retain aggregate global configuration or workspace wrappers duplicating runtime paths.

Project-command context MUST compose command scope from `llm_tool_cli` with Donna runtime preparation/journal factory, without a local command-context subclass or error-journaling catch.
CLI MUST register project-loading scope from `llm_tool_cli` in framework resources.
Initialization MUST use the command provided by `llm_tool_cli` with Donna schema/help and the workspace-owned starter template, retaining project scope through framework resources.
`llm_tool_cli` MUST own:

- discovery.
- loading.
- starter creation and validation.
- project setting construction, binding, and restoration.

Local preparation wrappers MUST NOT remain.

Machine MUST own a frozen, independently bound execution value with optional current work-unit/operation ids.
CLI MUST bind empty execution context and fresh caches after successful workspace preparation, retain both through execution, and restore prior bindings before shared error reporting.
Nested work-unit/operation scopes MUST replace only their own id and restore it on success/failure.
Journals MUST obtain execution ids exclusively from that scope and task ids from cached consistent state, which identifies the processed task until changes are saved.

The machine's public cache boundary MUST expose one bound collection of artifact/primitive/session-state caches through typed interfaces, without importing context/workspace implementations.
Context MUST own implementations; machine MUST own shared rendering-context data.
CLI MUST construct caches directly; projectless commands MUST NOT require them.
Construction MUST NOT require a workspace argument or do workspace I/O.
The following MUST remain intact:

- artifact refresh.
- artifact render modes.
- primitive caching.
- session external-change detection.

The machine-owned journal-cell factory MUST construct without submission, reading execution scope and cached task on each call.
Session-load environment errors or no active task MUST still produce events without task ids, preserving actor/execution context.
The factory MUST preserve explicit actor, including `None`, and MUST NOT accept execution/task overrides.
Call sites MUST use the active emitter's journal operation provided by `llm_tool_cli`.
The emitter MUST choose omitted actors and own:

- processing.
- rendering.
- buffering.
- delivery.

Journal cells MUST NOT read context or load state during construction/projection.
Donna MUST NOT maintain journal services/bindings or aggregate contexts duplicating execution/cache/output scopes.
Failed preparation and projectless commands MUST NOT journal errors through outer runtime services.
External processing MUST precede console delivery.

## Submodules

Submodules are optional unless required elsewhere.
Small closed interchangeable-component families SHOULD use one implementation submodule per meaningfully distinct component.
Shared family code SHOULD contain only:

- common types.
- public unions.
- selection.
- iteration glue.

Existing conventional names SHOULD stay consistent:

- `utils` — Non-domain technical helpers.
- `errors` — Module exceptions/errors.
- `entities` — Owned types/entities.
- `fixtures` — Reusable configuration/docs/data.
- `tests` — Colocated tests.
- `tests.make` — Test-object construction.
- `tests.helpers` — Setup, mutation, workflows.

Errors/entities/tests MUST follow their architecture specs.
The following MUST be imported directly from their owning modules in `llm_tool_cli`:

- shared result types.
- error bases/proxies.
- `BaseEntity`.
- `OutputCell`.
- construction/metadata helpers.
- cell errors.

Donna domain entities MUST construct typed logic cells without accepting output-cell types; view selection remains Donna-owned.
Public domain-result cells MUST belong to `donna.protocol.logic_cells` and be exported from `donna.protocol`.
They MUST construct artifact summaries, action instructions, and session messages during projection.
Generic messages/prepared documents MAY use content cells from `llm_tool_cli`.
Donna MUST directly use the following from `llm_tool_cli`:

- error presentation.
- protocol dispatch.
- output types.
- rendering contexts.

Batch rendering/writing MUST belong to `llm_tool_cli` output; individual projection/formatting MUST stay in Donna protocol.

Donna MUST own domain projections and journal attribution.
Donna journal cells MUST belong to `donna.protocol.journal` and extend the journal cell provided by `llm_tool_cli` with task/work-unit/operation ids, preserving compact human/LLM layouts and the library's escaping/automation serialization.
Conversion MUST carry captured ids as record attributes without runtime reads.
Donna MUST NOT duplicate the following from `llm_tool_cli`:

- journal records.
- formatters.
- output interfaces/bindings.
- command processors.

Primitives/runtime/journal output MUST use the active emitter provided by `llm_tool_cli`.
Setup provided by `llm_tool_cli` MUST bind output independently of projects.
After runtime preparation, Donna MUST configure its factory and the processor from directly used journal configuration provided by `llm_tool_cli`, without subclasses/field registries.
Output MUST survive shared finalization; terminal errors MUST bypass Donna factories/restored bindings.
Programmatic output callers MUST bind emitters explicitly.
Session commands without useful return values MUST emit cells and return `Result[None]`.
Render MUST emit a Donna artifact-content logic cell.
The following cells MUST prohibit journal delivery in their types and construction, without record conversion:

- artifact-status cells.
- rendered-artifact cells.
- action-request cells.
- session-state cells.

Generic content MUST retain shared journal prohibition.

Paths MUST directly use the following from `llm_tool_cli.paths`:

- normalization.
- resolution.
- containment.
- symlink rejection.
- enumeration.

Donna MUST retain artifact semantics, workflow-directory selection/order, and suffix filtering.
Fallible discovery MUST return results provided by `llm_tool_cli` and propagate enumeration errors through caches.

### Submodule nuances

#### `errors`

Owns errors/exceptions, which SHOULD express actionable project failures rather than low-level details.

#### `entities`

Owns semantic ids, enums, and entities, which SHOULD model domain/boundary data rather than incidental storage details.

#### `utils`

Owns helpers without a more specific entity/settings/integration owner.
Helpers SHOULD be pure or locally technical and move when they begin encoding module behavior.
Top-level modules SHOULD avoid other modules' unstable utilities.

#### `tests`

Owns colocated tests.
Tests SHOULD use public boundaries, mirror implementation names with `test_`, and group by function/class.
Storage tests MAY verify owned storage behavior.

#### `make`

MAY exist only as `<module>.tests.make` for test factories.
Reusable construction SHOULD live here; production MUST NOT import it.

#### `helpers`

MAY exist as `<module>.tests.helpers` for:

- setup.
- persisted mutation.
- behavior calls.
- workflows.

Actions/coordinated calls SHOULD live here; pure factories SHOULD live in `make`.
Production MUST NOT import helpers.

## Cross-module dependencies

### Import boundaries

Top-level modules MUST expose explicit stable boundaries through package roots or declared public submodules.
Public submodules SHOULD be cohesive and MUST NOT expose incidental helpers, storage details, or compatibility shims unless intentionally stable.
Initializers SHOULD export ergonomic common names and define `__all__`, but MUST NOT be required to re-export every submodule name.
Owned `errors` MUST be public.
Roots without useful APIs MAY be empty or have empty `__all__`.

Cross-module imports MUST use declared boundaries, never undeclared internals; same-owner submodules MAY import directly.
Configured dependency checks MUST enforce the specified ownership and dependency direction.
Check configuration MUST NOT permit undeclared dependencies merely to silence a finding.
`utils` is public only if explicitly declared.
**Example:** CLI may import `donna.workspaces` or its declared public submodules, not its private implementation.

Modules MAY import protocol boundary values/helpers to expose owned concepts.
Typed-cell construction MUST NOT count as a boundary violation or protocol-specific rendering.
Only protocol/CLI modules MAY depend on protocol-specific formatter implementations; non-protocol modules SHOULD NOT own serialization details.
Protocol rendering means concrete external serialization, such as:

- text framing.
- LLM boundaries.
- JSON Lines.
- bytes.
- formatter ordering.

## Data structures

Structures SHOULD inherit `BaseEntity` from `llm_tool_cli.core.entities` unless an external/Python protocol requires otherwise.
Domain entities MUST NOT use `dataclass`.
