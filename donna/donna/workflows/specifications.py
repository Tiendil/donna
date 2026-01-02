
from donna.machine.specifications import SpecificationSource, Specification, SpecificationIndexItem
from donna.primitives.specifications.static import StaticSpecificationSource


spec_planning = Specification(
    item=SpecificationIndexItem(
        id="donna/workflows/story-planning",
        name="Story Planning Guidelines",
        description="This document describes how Donna MUST plan work on a story with the help of workflows. The document describes the process of planning, kinds of involved entities and requirements for them."
    ),
    content="""
# Story Planning Guidelines

This document describes how Donna MUST plan work on a story with the help of workflows. The document describes the process of planning, kinds of involved entities and requirements for them.

## Overview

Donna's workflows create a plan of work on a story by iteratively polishing the set of records associated with the story.

The kinds of records involved are outside the scope of this document, the agent will get full details on the required workflow steps.

The final plan contains the next sections, in order:

1. `Developer request` — a copy of the original description of the work from the developer.
2. `Detailed work description` — a high-level description of the work to be done, created by Donna based on the developer request.
3. `Goals` — a list of goals that work strives to achieve.
4. `Objectives` — a list of specific objectives that need to be completed to achieve the goals.

Sections `Developer request` and `Detailed work description` are single-record sections.
Sections `Goals`, `Objectives` are multi-record sections — a single record per a list item.

## Developer Request

- This record MUST contain the original request from the developer. It MUST NOT be modified by Donna.

## Detailed Work Description

- This record MUST contain a clear professional high-level description of the work to be done based on the developer's request.
- The section MUST be limited to a single paragraph with a few sentences.

## Goals

- A goal describes a desired end state, outcome or result.
- A goal defines what should ultimately be true, not how to achieve it.
- A goal must not be defined via listing cases, states, outcomes, etc. Instead, use one of the next approaches:
  a) summarize top-layer items into a single goal;
  b) split the goal into multiple more specific goals;
  c) reformulate to a list of second-layer items as required properties of the top-level goal.
- Each goal must has clear scope and boundaries.

## Objectives

- An objective MUST describe an achieved state or capability not the act of describing it.
- An objective MUST be phrased as "X exists / is implemented / is defined / is executable / is enforced / …"
- An objective MUST be atomic: it MUST result in exactly one concrete deliverable: one artifact, one executable, one schema, one test suite, etc.
- An objective is a single clear, externally observable condition of the system (not a description, explanation, or analysis) that, when met, moves you closer to achieving a specific goal.
- An objective is a top-level unit of work whose completion results in a concrete artifact, behavior, or state change that can be independently verified without reading prose.
- Each goal MUST have a set of objectives that, when all achieved, ensure the goal is met.
- Each goal MUST have 2–6 objectives, unless the goal is demonstrably trivial (≤1 artifact, no dependencies).

"""
)


donna_workflows = StaticSpecificationSource(
    id="donna-workflows",
    specifications=[
        spec_planning
    ])
