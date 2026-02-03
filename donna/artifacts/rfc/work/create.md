
# Create a Request for Change

```toml donna
kind = "donna.lib.workflow"
start_operation_id = "start"
```

This workflow creates a Request for Change (RFC) document based on a description of a problem or changes required.

## Start Work

```toml donna
id = "start"
kind = "donna.lib.request_action"
fsm_mode = "start"
```

1. Read the specification `{{ donna.lib.view("donna:rfc:specs:request_for_change") }}` if you haven't done it yet.
2. Read the specification `{{ donna.lib.view("donna:usage:artifacts") }}` if you haven't done it yet.
3. `{{ donna.lib.goto("ensure_work_description_exists") }}`

## Ensure work description exists

```toml donna
id = "ensure_work_description_exists"
kind = "donna.lib.request_action"
```

At this point you SHOULD have a clear description of the problem in your context. I.e. you know what you need to do in this workflow.

1. If you have a problem description in your context, `{{ donna.lib.goto("prepare_rfc_artifact") }}`.
2. If you have no problem description in your context, but you know it is in one of `session:*` artifacts, find and view it. Then `{{ donna.lib.goto("prepare_rfc_artifact") }}`.
3. If you have no problem description in your context, and you don't know where it is, ask the developer to provide it. After you get the problem description, `{{ donna.lib.goto("prepare_rfc_artifact") }}`.

## Prepare RFC artifact

```toml donna
id = "prepare_rfc_artifact"
kind = "donna.lib.request_action"
```

1. If the name of artifact is not specified explicitly, assume it to be default for the session: `session:rfc`.:
2. Save the next template into the artifact, replace `<variables>` with appropriate values.

```
# <Title>

<short description of the proposed change>

## Original description

<original description of the requested changes from the developer or parent workflow>

## Formal description

## Goals

## Objectives

## Constraints

## Requirements

## Acceptance criteria

## Solution

## Verification

## Deliverables

## Action items
```

3. `{{ donna.lib.goto("initial_fill") }}`

## Initial Fill

```toml donna
id = "initial_fill"
kind = "donna.lib.request_action"
```

1. Read the specification `{{ donna.lib.view("donna:rfc:specs:request_for_change") }}` if you haven't done it yet.
2. Analyze the project if needed to understand the context of the requested change.
3. Based on the problem description you have, fill in all sections of the RFC draft artifact.
4. `{{ donna.lib.goto("review_rfc_format") }}`

## Review RFC Format

```toml donna
id = "review_rfc_format"
kind = "donna.lib.request_action"
```

1. List mismatches between the RFC artifact and the RFC specification `{{ donna.lib.view("donna:rfc:specs:request_for_change") }}`.
2. For each mismatch, make necessary edits to the RFC draft artifact to ensure compliance with the RFC specification.
3. `{{ donna.lib.goto("review_rfc_content") }}`

## Review RFC Content

```toml donna
id = "review_rfc_content"
kind = "donna.lib.request_action"
```

1. Read the RFC document and identify any gaps, inconsistencies, or areas for improvement in the content in accordance with the current project context. Use `{{ donna.lib.view("donna:research:work:research") }}` workflow if you need to take a complex decision.
2. Make necessary edits to the RFC draft artifact to address identified issues.
3. If there were changes made on this step or the previous `review_rfc_format` step `{{ donna.lib.goto("review_rfc_format") }}`.
4. If no changes were made, `{{ donna.lib.goto("finish") }}`.

## Complete Draft

```toml donna
id = "finish"
kind = "donna.lib.finish"
```

RFC draft is complete and ready for planning or review.
