
# Top-level architecture

```toml donna
kind = "donna.lib.specification"
```

This document describes the top-level architecture of the Donna project, providing an overview of its main components and their interactions.

## Basic statements

- Donna is a CLI tool (`donna`) implemented in Python.

## Code organization

All the Donna's code is located in the `./donna/` directory.

The code is separated by layers/subsystems into subpackages:

- `donna.core` — code that not in the Donna's domain, but required to its functioning: domain-independent utils, basic classes for errors, exceptions and other entities, etc.
- `donna.domain` — code that is required by all Donna'specific logic: ID classes, common types, etc.
- `donna.machine` — code that implements the core Donna's logic — how Donna works regardless of external environments, i.e. pure domain behavior.
- `donna.context` — code that stores and provides execution-scoped runtime context for Donna's domain logic: artifact/state/primitive caches and scoped values like current actor/work unit/operation identifiers.
- `donna.workspaces` — code that integrates Donna with the project workspace and filesystem: runtime configuration, artifact discovery/loading, session storage, source parsing, and workspace initialization.
- `donna.protocol` — code that implements protocol via which Donna's core domain logic interacts with external environments: CLI, API, etc. Includes basic classes for information representing (for the external environments) and its formatting.
- `donna.cli` — code that implements the `donna` CLI tool, its commands, arguments parsing, etc.
- `donna.primitives` — code that implements basic building blocks for Donna's behavior: concrete implementations of various classes from the `donna.machine`.
- `donna.lib` — module that contains constructed primitives to be used in donna artifacts by referencing them by python import path. Like `donna.lib.workflow`, `donna.lib.goto`, etc.
- `donna.fixtures.skills` — bundled skills that are distributed with Donna and synced into project workspaces under `.agents/skills`.
- `donna.fixtures.specs` — bundled Donna specifications and workflows that are distributed with Donna and synced into project workspaces under `.agents/donna`, where they are addressed as `@/.agents/donna/**` artifacts.

## Data structures

- Do not use `dataclass` for data structures. Use `donna.core.entities.BaseEntity` (subclass of the `pydantic.BaseModel`) for complex data structures and Python classes with `__slots__` for very simple ones (like cache keys).

## Autotests

- No autotests in the project for now.
