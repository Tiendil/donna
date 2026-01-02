from donna.domain.types import SpecificationId, SpecificationSourceId
from donna.machine.specifications import Specification, SpecificationIndexItem
from donna.primitives.specifications.static import StaticSpecificationSource

spec_planning = Specification(
    item=SpecificationIndexItem(
        id=SpecificationId("donna/workflows/story-planning"),
        name="Story Planning Guidelines",
        description=(
            "This document describes how Donna MUST plan work on a story with the help of "
            "workflows. The document describes the process of planning, kinds of involved "
            "entities and requirements for them."
        ),
    ),
    content="""
# Story Planning Guidelines

This document describes how Donna MUST plan work on a story with the help of workflows. The
document describes the process of planning, kinds of involved entities and requirements for them.

## Overview

Donna's workflows create a plan of work on a story by iteratively polishing the set of records
associated with the story.

The kinds of records involved are outside the scope of this document, the agent will get full
details on the required workflow steps.

The final plan contains the next sections, in order:

1. `Developer request` — a copy of the original description of the work from the developer.
2. `Detailed work description` — a high-level description of the work to be done, created by Donna
   based on the developer request.
3. `Goals` — a list of goals that work strives to achieve.
4. `Objectives` — a list of specific objectives that need to be completed to achieve the goals.
5. `Known constraints` — a list of constraints for the story.
6. `Acceptance criteria` — a list of acceptance criteria for the resulted work.

Sections `Developer request` and `Detailed work description` are single-record sections.
Sections `Goals`, `Objectives` are multi-record sections — a single record per a list item.

## "Developer Request" section requirements

- This record MUST contain the original request from the developer. It MUST NOT be modified by Donna.

## Detailed Work Description

- The record MUST contain a clear professional high-level description of the work to be done based
  on the developer's request.
- The record MUST be limited to a single paragraph with a few sentences.
- The record MUST explain what someone gains after these changes and how they can see it working.
  State the user-visible behavior the task will enable.

## "Goals" section requirements

- A goal describes a desired end state, outcome or result.
- A goal defines what should ultimately be true, not how to achieve it.
- A goal must not be defined via listing cases, states, outcomes, etc. Instead, use one of the next
  approaches:
  a) summarize top-layer items into a single goal;
  b) split the goal into multiple more specific goals;
  c) reformulate to a list of second-layer items as required properties of the top-level goal.
- Each goal must has clear scope and boundaries.

## "Objectives" section requirements

- An objective MUST describe an achieved state or capability not the act of describing it.
- An objective MUST be phrased as "X exists / is implemented / is defined / is executable /
  is enforced / …"
- An objective MUST be atomic: it MUST result in exactly one concrete deliverable: one artifact,
  one executable, one schema, one test suite, etc.
- An objective is a single clear, externally observable condition of the system (not a description,
  explanation, or analysis) that, when met, moves you closer to achieving a specific goal.
- An objective is a top-level unit of work whose completion results in a concrete artifact,
  behavior, or state change that can be independently verified without reading prose.
- Each goal MUST have a set of objectives that, when all achieved, ensure the goal is met.
- Each goal MUST have 2–6 objectives, unless the goal is demonstrably trivial (≤1 artifact, no dependencies).

## "Known Constraints" section requirements

- A known constraint describes a non-negotiable limitation or requirement that the work MUST
  respect (technical, organizational, legal, temporal, compatibility, security, operational).
- Each constraint MUST be derived from explicitly available inputs (the developer request, existed
  specifications, existed code, information provided by workflows). Donna MUST NOT invent
  constraints.
- Each constraint MUST be phrased as a verifiable rule using normative language: “MUST / MUST NOT /
  SHOULD / SHOULD NOT”.
- Each constraint MUST be atomic: one rule per record (no "and/or" bundles). If multiple rules
  exist, split into multiple constraint records.
- Each constraint MUST be externally binding (something the plan must accommodate), not an
  internal preference.
- Constraints MUST NOT restate goals/objectives in different words. They are bounds, not outcomes.
- Constraints MUST NOT contain implementation steps, designs, or proposed solutions.
- Constraints MUST NOT include risks, unknowns, or speculative issues.
- Constraints MUST be written so a reviewer can answer true/false for compliance by inspecting
  artifacts, behavior, or configuration (not by reading explanatory prose).
- The section MAY be empty only if no constraints are explicitly known.

Examples:

- Good: `MUST remain compatible with Python 3.10`
- Good: `MUST not change public CLI flags`
- Good: `MUST avoid network access`
- Good: `MUST run on Windows + Linux`
- Bad: `We should do it cleanly`
- Bad: `Prefer elegant code`
- Bad: `Try to keep it simple`

## "Acceptance criteria" section requirements

- An acceptance criterion describes a pass/fail condition that determines whether the story's
  results are acceptable to a reviewer, user, or automated gate.
- Each criterion MUST be derived from explicitly available inputs (developer request, previous
  sections of the plan). Donna MUST NOT invent new scope, features, constraints, or assumptions.
- Each criterion MUST be phrased as an externally observable, verifiable rule, using normative
  language ("MUST / MUST NOT / SHOULD / SHOULD NOT") or an equivalent test form such as
  Given/When/Then (Gherkin-style).
- Each criterion MUST be independently checkable by inspecting artifacts, running a command,
  executing tests, or observing runtime behavior/output — not by reading explanatory prose.
- Each criterion MUST be atomic: one condition per record (no "and/or" bundles). If multiple
  conditions exist, split into multiple criteria records.
- Criteria MUST NOT describe implementation steps, internal design decisions, or "how" to achieve the result.
- Criteria MUST NOT restate goals/objectives verbatim. Instead, they must state how success is
  demonstrated (e.g., observable behavior, produced files, enforced rules, test outcomes).

Coverage rules:

- Each objective MUST have ≥1 acceptance criterion that validates it.
- Each acceptance criterion MUST map to at least one objective (directly or via a goal that the objective serves).
- Where relevant, criteria SHOULD specify concrete evaluation conditions, such as:
  - exact CLI output/exit codes, produced artifacts and their locations;
  - supported platforms/versions, configuration prerequisites;
  - measurable thresholds (latency, memory, size limits), if such requirements are explicitly implied or stated.
  - etc.

Regression rules:

- If the developer request or known constraints imply preserving existing behavior, acceptance
  criteria SHOULD include explicit non-regression checks (what must remain unchanged).
- The section MUST NOT be empty.

""",
)


donna_workflows = StaticSpecificationSource(
    id=SpecificationSourceId("donna-workflows"),
    specifications=[spec_planning],
)
