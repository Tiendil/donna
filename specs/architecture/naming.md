# Naming architecture

## Goal of the document

This document describes naming conventions for project symbols and modules.

## Scope

This specification covers stable code naming rules.
The following are out of scope:

- private helper names.
- exhaustive symbol lists.
- external generated names.
- tool-managed formatting.

## General principles

Names SHOULD describe their project concept and owning module's responsibility, remain unambiguous across modules, and prefer precise project terms over generic names or confusing Python/framework terminology.
Public names SHOULD remain stable unless their concept changes.

## Type names

Class, enum, and type-alias names SHOULD be singular when instances or members represent one concept; plurals SHOULD identify only collections or registries.
Enum names SHOULD describe one member's meaning, and externally serialized members SHOULD use their stable serialized names.
Type names SHOULD avoid collisions with broader typing abstractions.

## Module names

Module names SHOULD describe their responsibility, use plurals only for groups of related definitions without a narrower responsibility, and mention implementation techniques only when those are the module's stable responsibility.
