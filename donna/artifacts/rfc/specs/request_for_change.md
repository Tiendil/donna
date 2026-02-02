# Format of the Request for Change document

```toml donna
kind = "donna.lib.specification"
```

This document describes the format and structure of a Request for Change (RFC) document used to propose changes to a project by Donna workflows from `donna:rfc:*` namespace.

## Overview

Donna introduces a group of workflows located in `donna:rfc:*` namespace that organize the process of proposing, reviewing, and implementing changes to a project via RFC documents.

If there is not specified otherwise, active session have a single artifact `session:rfc`.

Agent (via workflows) creates that artifact and polishes it iteratively as the RFC process goes on.

After the RFC is completed, agent (via workflows) MAY implement changes directly or by creating and executing a workflow based on the RFC content.

## RFC structure

The RFC document is Donna artifact (check `{{ donna.lib.view("donna:usage:artifacts") }}`) with the next structure:

- **Primary section** — title and short description of the proposed change.
- **Original description** — original description of the requested changes from the developer or parent workflow.
- **Formal description** — formal description of the requested changes.
- **Goals** — list of goals that the proposed change aims to achieve.
- **Objectives** — list of objectives that need to be accomplished to achieve the goals.
- **Constraints** — list of constraints that must be considered while implementing the proposed change.
- **Requirements** — list of requirements that the proposed change must fulfill.
- **Acceptance criteria** — list of criteria that define when the proposed change is considered complete and successful.
- **Final solution** — list of statements about how the final result should look like.
- **Verification** — list of statements about how to verify each objective, constraint, requirement, and acceptance criterion.
- **Deliverables** — list of deliverables that should be produced as part of the proposed change.
- **Action items** — unordered list of atomic actions/changes that must be performed to implement the proposed change.

## General language and format

- You MUST follow [RFC 2119](https://www.rfc-editor.org/rfc/rfc2119.txt) for keywords like MUST, SHOULD, MAY, etc.
- You MUST follow `{{ donna.lib.view("donna:usage:artifacts") }}`.
- You MUST follow the structure specified in this document.

### List format

- If a section described as a list, it MUST contain only a single markdown list.
- Each list item MUST be concise and clear.
- Each list item SHOULD be atomic and focused on a single aspect.
- Reviewer MUST be able to tell is the list item statement true or false by inspecting resulting artifacts and behavior.

Examples:

- Bad: `- Improve performance and fix bugs.`
- Bad: `- The interface MUST include button A, button B, and dropdown C.`
- Good: `- Performance test MUST show at least 20% improvement in response time under load.`
- Good: `- Fix bug A causing crash when input is empty.`
- Good: `- The interface MUST include button A that triggers action X.`
- Good: `- The interface MUST include button B that triggers action Y.`

Common approaches to improve list items:

- Split a single item with an enumeration into multiple items with single focus.
- Transform an abstract item into a concrete one by specifying measurable criteria or user-visible behavior.

### Trusted inputs

Some sections of the RFC document MUST be based on trusted inputs. Trusted inputs are:

- Original description from the developer or parent workflow.
- Statements from the RFC document itself.
- Existing project documentation, code, and artifacts.
- External standards when they define constraints or best practices for the project domain.
- Documentation of third-party libraries, frameworks, or tools when it describes constraints or best practices.

## `Primary` section

- Title MUST be concise and reflect the essence of the proposed change.
- Description MUST provide a brief overview of the proposed change, its purpose, and its expected impact.

## `Original description` section

- This section MUST contain the original request from the developer or from the parent workflow.
- The request MUST NOT be modified by agents.

## `Formal description` section

- The section MUST contain a clear professional high-level description of the work to be done based
  on the developer's request.
- The section MUST be limited to a single paragraph with a few sentences.
- The sectino MUST explain what someone gains after these changes and how they can see it working.
  State the user-visible behavior the change will enable.

## `Goals` section

- This section MUST contain a list of goals that the proposed change aims to achieve.

The goal quality criteria:

- A goal describes a desired end state, outcome or result.
- A goal defines what should ultimately be true, not how to achieve it.

Examples:

- Bad: `- Implement authentication system.`
- Good: `- Protect user data from unauthorized access.`

## `Objectives` section

- The section MUST contain a list of objectives that need to be completed to achieve the goals.
- Each goal MUST have a set of objectives that, when all achieved, ensure the goal is met.
- Each goal MUST have 2–6 objectives, unless the goal is demonstrably trivial (≤1 artifact, no dependencies).

Objective quality criteria:

- An objective is a specific, measurable condition that must be true for a goal to be satisfied.
- An objective MUST describe an achieved state, capability, artifact, or behavior.

Examples:

- Bad: `- Create user authentication and authorization system.`
- Bad: `- Design user authentication flow.`
- Good: `- Specification for user authentication flow exists.`
- Good: `- User is able to log in using email and password.`

## `Constraints` section

- The section MUST contain a list of constraints that the changes MUST respect.
- The section MAY be empty only if no constraints are explicitly known.
- A constraint MUST be derived from trusted inputs. Agents MUST NOT invent constraints.

Constraint quality criteria:

- A constraint defines a hard limit on the solution space.
- A constraint MUST be externally imposed by technology, policy, compatibility, time, budget, etc.
- A constraint MUST NOT describe desired behavior or outcomes.
- A constraint MUST be non-negotiable within the scope of the RFC.

Examples:

- Bad: `- The system should be easy to maintain.`
- Bad: `- Use clean architecture.`
- Good: `- The solution MUST be compatible with Python 3.12.`
- Good: `- The solution MUST NOT introduce new runtime dependencies.`
- Good: `- The solution MUST follow specification project:specs:abc`
- Good: `MUST not change public CLI flags`

## `Requirements` section

- The section MUST contain a list of requirements that the proposed change MUST fulfill.

Requirement quality criteria:

- A requirement defines a single atomic condition, capability, or feature that the system MUST meet, provide, or exhibit after the change is implemented.
- A requirement MUST be directly testable.
- A requirement MUST be stated independently of implementation details.
- A requirement MUST NOT restate goals or objectives verbatim.

Examples:

- Bad: `- Improve security.`
- Bad: `- Implement OAuth.`
- Good: `- The system MUST reject authentication attempts with invalid credentials.`
- Good: `- The system MUST log all failed authentication attempts with timestamp and user identifier.`

## `Acceptance criteria` section

- The section MUST contain a list of acceptance criteria used to determine whether the proposed change is complete and successful.
- An acceptance criterion MUST be derived explictily from statements in the RFC document. Agents MUST NOT invent acceptance criteria.

Acceptance criteria quality criteria:

- An acceptance criterion MUST define a single atomic check that results in a pass/fail outcome.
- An acceptance criterion check MUST be about a single artifact: single file exists, single test passes, single behavior observed, etc.
- An acceptance criterion MUST NOT describe implementation steps, internal design decisions, or "how" to achieve the result.

Examples:

- Bad: `- All requirements are implemented.`
- Bad: `- The feature works as expected.`
- Good: `- The artifact with documentation for X exists.`
- Good: `- The autotest for requirement Y exists.`
- Good: `- All autotests pass without errors.`
- Good: `- The tool can run on Python 3.12 without errors.`

## `Final solution` section

## `Verification` section

## `Deliverables` section

## `Action items` section


----------

TODO: each action should produce an artifact?
TODO: h3 instead list items?
TODO: define what statements derived from what?
