
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
- `donna.world` — code that implements various worlds where Donna can find and manage artifacts: from artifacts discovery to their loading, parsing, updating. Also contains code related to configuration of Donna.
- `donna.protocol` — code that implements protocol via which Donna's core domain logic interacts with external environments: CLI, API, etc. Includes basic classes for information representing (for the external environments) and its formatting.
- `donna.cli` — code that implements the `donna` CLI tool, its commands, arguments parsing, etc.
- `donna.primitives` — code that implements basic building blocks for Donna's behavior: concrete implementations of various classes from the `donna.machine`.
- `donna.lib` — module that contains constructed primitives to be used in donna artifacts by referencing them by python import path. Like `donna.lib.workflow`, `donna.lib.goto`, etc.
- `donna.artifacts` — artifacts that are distributed with Donna itself: specifications of how it works, predefined workflows, etc.

## Data structures

- Do not use `dataclass` for data structures. Use `donna.core.entities.BaseEntity` (subclass of the `pydantic.BaseModel`) instead.
