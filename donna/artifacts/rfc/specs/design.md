# Format of the Design document

```toml donna
kind = "donna.lib.specification"
```

This document describes the format and structure of a Design document used to design changes to a project proposed in a Request for Change (RFC). This document is an input for planing and will be treated as strong recommendations for the implementation of the proposed change.

## Overview

Donna introduces a group of workflows located in `donna:rfc:*` namespace that organize the process of proposing, reviewing, and implementing changes to a project via RFC and Design documents.

You create a Design document to explicitly describe the exact changes you want to make to the project in order to implement the RFC.

If not otherwise specified, Design documents for the session MUST be stored as `session:design:<short-problem-related-identifier>` artifacts in the session world.

**The Design document MUST list exact changes to the project that will be implemented.** E.g. concrete function names and signatures, file paths, data structures, etc.

**The Design document MAY skip implementation details.** E.g. it may skip the exact implementation of a function body, but it should specify the function signature and its purpose; It may use pseudocode to describe the logic of a function, but it should not skip describing the logic at all.

The Design document MUST NOT be a high-level description of the problem and solution. High-level description of the problem and solution should be provided in the RFC document.

**Identifiers in this document MUST follow project-specific naming conventions.** Before working on a Design document, you should read the artifacts with project guidlines for naming and code style, if any exist.

## Design document structure

The RFC document is Donna artifact (check `{{ donna.lib.view("donna:usage:artifacts") }}`) with the next structure:

- **Primary section** — title and short description of the proposed change.
- **Inputs** — list of input documents that are relevant for the proposed change, starting from the RFC document.
- **Architecture changes** — list of high-level architectural changes that MUST be implemented.
- **Highlevel code changes** — list of high-level code changes that MUST be implemented: modules to add/modify, functions to add/modify, classes to add/modify, etc. This section should not include low-level implementation details, but it should include enough details to understand the scope of the change and its impact on the project.
- **Data structure changes** — list of changes to data structures that MUST be implemented.
- **Interface changes** — list of changes to interfaces (e.g. function signatures, API endpoints, etc.) that MUST be implemented.
- **Tests changes** — list of autotests that MUST be implemented/updated/removed. Only if the project already uses autotests. If the project does not use autotests, this section should be skipped.
- **Documentation changes** — list of changes in the documentation. Only if the project already has documentation. If the project does not have documentation, this section should be skipped.
- **Other changes** — list of other changes that do not fit into the previous sections, but are still relevant for the proposed change.
- **Order of implementation** — a proposed order of implementation of the changes listed in the previous sections. This section should be treated as a recommendation (from the author of the Design document), not a strict requirement.

## General language and format

- You MUST follow [RFC 2119](https://www.rfc-editor.org/rfc/rfc2119.txt) for keywords like MUST, SHOULD, MAY, etc.
- You MUST follow `{{ donna.lib.view("donna:usage:artifacts") }}`.
- You MUST follow the structure specified in this document.

### List format

- If a section is described as a list, it MUST contain only a single markdown list.
- Each list item MUST be concise and clear.
- Each list item SHOULD be atomic and focused on a single aspect.
- Reviewer MUST be able to tell whether the list item statement is true or false by inspecting the resulting artifacts and behavior.

Examples:

- Bad: `- Implement a new module`
- Bad: `- The interface MUST include button A, button B, and dropdown C.`
- Good: `- Implament a module "a.b.c" that is responsible for X, Y, and Z.`
- Good: `- Add a button class "ButtonA" to the module "a.b.c"`
- Good: `- "ButtonA" class MUST has a method "click()" that performs action X when called.`

Common approaches to improve list items:

- Split a single item with an enumeration into multiple items with a single focus.
- Transform an abstract item into a concrete one by specifying measurable criteria or user-visible behavior.

## `Primary` section

- Title MUST be concise and reflect the essence of the proposed change. Derive it from the RFC.
- Description MUST provide an essence of the proposed change.

## `Inputs` section

- The section MUST contain a list of documents that are relevant for the proposed change.
- The first item in the list MUST be the original RFC document that describes the problem and the proposed solution.
- Other items in the list MAY include other documentation, code files, external links, etc. that are relevant for the proposed change.

## `Architecture changes` section

- The section MUST contain a free-form but precise and grounded description of the high-level architectural changes that MUST be implemented.
- Along the text, you may add code snippets, diagrams, and other visual aids to make the description clearer and more precise.

## `Highlevel code changes` section

- The section MUST contain a list of high-level changes in the code.
- The level of abstraction: `add a module A`, `remove the class B`, `change the implementation of a function C`.
- The section MUST list only most important changes, that are significant cornerstones of the proposed change.
- The section MAY omit low-level details, such as the small or utilitarian functions, minor refactorings, etc.

## `Data structure changes` section

- The section MUST list an exact changes to data structures that MUST be implemented.
- Each change MUST be accompanied by a description of the purpose of the change and its impact on the project.

Examples of statements about structure changes:

- Bad: `- Change the data structure of the project.`
- Bad: `- Update the class A.`
- Good: `- Add a field "x" to the class "A".`
- Good: `- Change the type of the field "y" in the class "B" from "int" to "str".`
- Good: `- Add structure "C" with fields "a", "b", and "c".`

## `Interface changes` section

- The section MUST list an exact changes to interfaces that MUST be implemented.
- Each change MUST be accompanied by a description of the purpose of the change and its impact on the project.

Examples of statements about interface changes:

- Bad: `- Change the interface of functions in the project.`
- Bad: `- Update the API endpoints.`
- Good: `- Add a new API endpoint "/api/v1/resource" that accepts POST requests with JSON body containing fields "a", "b", and "c".`
- Good: `- Change the signature of the function "foo" from "foo(x: int) -> str" to "foo(x: int, y: str) -> str".`

## `Tests changes` section

- If the project does not use autotests, this section MUST contain a statement `No changes in tests are required, since the project does not use autotests.`
- If the project uses autotests, this section MUST contain a list of autotests that MUST be implemented/updated/removed.
- Each changes piece of logic MUST have at least one corresponding autotest that verifies its correctness and prevents regressions in the future.
- Each added/updated branch of logic MUST have at least one corresponding autotest that verifies its correctness and prevents regressions in the future.

Examples of statements about tests changes:

- Bad: `- Add tests for the new module.`
- Bad: `- Update tests for the changed function.`
- Good: `- Add a test "test_foo_with_valid_input" that verifies that the function "foo" returns the expected result when called with valid input.`
- Good: `- Add a test "test_foo_success_path" that verifies that the function "foo" returns the expected result when called with input that follows the success path.`

## `Documentation changes` section

- If the project does not have documentation, this section MUST contain a statement `No changes in documentation are required, since the project does not have documentation.`
- If the project has documentation, this section MUST contain a list of changes in the documentation that MUST be implemented.

## `Other changes` section

- The section MAY contain a list of other changes that do not fit into the previous sections, but are still relevant for the proposed change.
- The section MUST be a single statement `No other changes are required, since all relevant changes are covered in the previous sections.` if there are no other changes to mention.

## `Order of implementation` section

- The section MUST contain a proposed order of implementation of the changes listed in the previous sections.
- The section MUST refer only identifiers mentioned in the previous sections, and it MUST NOT introduce new identifiers or entities that are not mentioned in the previous sections.
