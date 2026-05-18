# Naming architecture

## Goal of the document

This document describes architectural naming conventions for project code symbols and modules.

## Scope

The scope of this specification is limited to stable naming rules that help keep project code understandable across modules.

The following topics are out of scope:

- exact names for private helpers.
- complete lists of symbol names.
- generated names in external protocols.
- formatting rules covered by language tools.

## General principles

Names SHOULD describe the project concept represented by the symbol.

Names SHOULD be specific enough to avoid ambiguity at module boundaries.

Names SHOULD NOT use generic words when a more precise project term is available.

Names SHOULD avoid confusion with common Python standard library, typing, or framework concepts when a clearer project-specific name is available.

Names SHOULD be consistent with the responsibility of the module that owns the symbol.

Public names SHOULD remain stable unless the underlying project concept changes.

## Type names

Class, enum, and type alias names SHOULD use singular nouns when each instance or member represents one concept.

Collection-like plural names SHOULD be used only when the type itself represents a collection or registry.

Enum type names SHOULD describe what one enum member represents, not the set of all possible members.

Enum member names SHOULD use the serialized value name when the enum crosses an external boundary and the serialized names are stable.

Type names SHOULD avoid names that collide with common typing abstractions when the project concept is narrower than the abstraction.

## Module names

Module names SHOULD describe the responsibility owned by the module.

Module names SHOULD be plural only when the module primarily contains a group of closely related definitions with no single narrower responsibility.

Module names SHOULD NOT mention implementation techniques unless the technique is the module's stable responsibility.
