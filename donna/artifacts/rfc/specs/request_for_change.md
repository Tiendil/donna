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

## RFC Document Structure

The RFC document is Donna artifact (check `{{ donna.lib.view("donna:usage:artifacts") }}`) with the next structure:

```
# <Title>

Short description of the proposed change.

## Original description

Original description of the requested changes from the developer or parent workflow.

## Formal description

Formal description of the requested changes in 1-2 paragraphs.

## Goals

List of goals that the proposed change aims to achieve.

## Objectives

List of objectives that need to be accomplished to achieve the goals.

## Constraints

List of constraints that must be considered while implementing the proposed change.

## Requirements

List of requirements that the proposed change must fulfill.

## Acceptance criteria

List of criteria that define when the proposed change is considered complete and successful.

## Final solution

List of statements about how the final result should look like.

## Verification

List of statements about how to verify each objective, constraint, requirement, and acceptance criterion.

## Deliverables

List of deliverables that should be produced as part of the proposed change.

## Action items

Unordered list of atomic actions/changes that must be performed to implement the proposed change.
```



----------

TODO: each action shoudld produce an artifact?
