# Behavior specification requirements

## Goal of the document

This document describes the content and abstraction level of behavior specifications.

## Scope

This specification applies to behavior specification documents under `specs/behavior/`.
General specification conventions and architecture specification content are out of scope.

## Abstraction level

Behavior specifications MUST identify the boundary whose observable contract they describe.
Requirements MUST be assessable through that boundary without inspecting implementation structure.
Observable behavior includes guarantees available to library callers as well as tool users.

Requirements MUST describe the applicable:

- accepted inputs.
- results.
- state changes.
- external effects and their ordering.
- failure semantics.

They MUST NOT prescribe internal mechanisms merely because the current implementation uses them, including:

- call sequences.
- algorithms.
- object arrangements.
- resource-management mechanisms.

**Example:** A requirement that failed preparation leaves the caller's active project unchanged describes behavior.
Requiring a particular context-manager implementation describes a mechanism.

## External contracts

Externally visible names and representations MAY be prescribed when independently required by the behavior contract, under `specs/meta/general.md`.
Visibility in current output alone MUST NOT establish such a requirement.
An identifier that forms part of command, configuration, or workflow syntax remains an external contract even when it also names a Python symbol.

Behavior specifications MUST NOT prescribe implementation function or type names or Python signatures, including those exposed through public Python interfaces.
They MUST describe operation semantics instead.
API documentation MAY describe those implementation interfaces.

## Contract references

Behavior specifications MAY adopt another specification's behavior by identifying the contract and where it applies.
Such references MUST NOT implicitly require using that contract's current implementation.
References MUST identify the owning specification rather than use unexplained terms such as “shared behavior.”

## Separation from architecture

Dependency selection, module ownership, and responsibility allocation between implementation components MUST belong to architecture specifications.
Architecture specifications MAY prescribe concrete interfaces only when required by an independently established architectural constraint.
Incidental implementation details MUST be omitted rather than relocated automatically.

When a statement combines behavior and implementation constraints, its observable guarantees MUST remain in the behavior specification.
Independently required architectural constraints MUST remain in the appropriate architecture specification without duplicating existing requirements.
