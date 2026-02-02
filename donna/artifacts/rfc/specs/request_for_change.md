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
- **Formal description** — formal description of the requested changes in 1-2 paragraphs.
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

Examples:

- Bad: `- Improve performance and fix bugs.`
- Bad: `- The interface MUST include button A, button B, and dropdown C.`
- Good: `- Performance test MUST show at least 20% improvement in response time under load.`
- Good: `- Fix bug A causing crash when input is empty.`
- Good: `- The interface MUST include button A that triggers action X.`
- Good: `- The interface MUST include button B that triggers action Y.`


----------

TODO: each action shoudld produce an artifact?
