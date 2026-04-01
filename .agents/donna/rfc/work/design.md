# Create a Design document

```toml donna
kind = "donna.lib.workflow"
start_operation_id = "start"
```

This workflow creates a Design document artifact based on an RFC and aligned with `donna:rfc:specs:design`.

## Start Work

```toml donna
id = "start"
kind = "donna.lib.request_action"
fsm_mode = "start"
```

1. Read the specification `{{ donna.lib.view("donna:rfc:specs:design") }}` if you haven't done it yet.
2. Read the specification `{{ donna.lib.view("donna:usage:artifacts") }}` if you haven't done it yet.
3. `{{ donna.lib.goto("ensure_rfc_artifact_exists") }}`

## Ensure RFC artifact exists

```toml donna
id = "ensure_rfc_artifact_exists"
kind = "donna.lib.request_action"
```

At this point, you SHOULD have a clear RFC to design.

1. If you have an RFC artifact id in your context, view it and `{{ donna.lib.goto("prepare_design_artifact") }}`.
2. If you have no RFC artifact id in your context, but you know it is in one of `{{ donna.lib.list("session:**") }}` artifacts, find and view it. Then `{{ donna.lib.goto("prepare_design_artifact") }}`.
3. If you have no RFC artifact id in your context, and you don't know where it is, ask the developer to provide the RFC artifact id or to create a new RFC. After you get it and view the artifact, `{{ donna.lib.goto("prepare_design_artifact") }}`.

## Prepare Design artifact

```toml donna
id = "prepare_design_artifact"
kind = "donna.lib.request_action"
```

1. If the name of the artifact is not specified explicitly, assume it to be `session:design:<short-problem-related-identifier>`, where `<short-problem-related-identifier>` SHOULD correspond to the RFC slug.
2. Save the next template into the artifact, replace `<variables>` with appropriate values.

~~~
# <Title>

```toml donna
kind = "donna.lib.specification"
```

<short description of the proposed design>

## Inputs

- <RFC artifact id>

## Architecture changes

## High-level code changes

## Data structure changes

## Interface changes

## Tests changes

## Documentation changes

## Other changes

## Order of implementation
~~~

3. `{{ donna.lib.goto("initial_fill") }}`

## Initial Fill

```toml donna
id = "initial_fill"
kind = "donna.lib.request_action"
```

1. Read the specification `{{ donna.lib.view("donna:rfc:specs:design") }}` if you haven't done it yet.
2. Read the RFC artifact selected in the previous step if you haven't done it yet.
3. Analyze the project if needed to understand the requested change context.
4. Fill in all sections of the Design draft artifact.
5. Ensure the first item in `Inputs` section is the RFC artifact id.
6. `{{ donna.lib.goto("review_design_format") }}`

## Review Design Format

```toml donna
id = "review_design_format"
kind = "donna.lib.request_action"
```

1. List mismatches between the Design artifact and the Design specification `{{ donna.lib.view("donna:rfc:specs:design") }}`.
2. For each mismatch, make necessary edits to the Design draft artifact to ensure compliance.
3. `{{ donna.lib.goto("review_design_content") }}`

## Review Design Content

```toml donna
id = "review_design_content"
kind = "donna.lib.request_action"
```

1. Read the Design document and identify gaps, inconsistencies, or areas for improvement in accordance with the RFC and current project context. Use `{{ donna.lib.view("donna:research:work:research") }}` workflow if you need to make a complex decision.
2. Make necessary edits to the Design draft artifact to address identified issues.
3. If there were changes made on this step or the previous `review_design_format` step `{{ donna.lib.goto("review_design_format") }}`.
4. If no changes were made, `{{ donna.lib.goto("finish") }}`.

## Complete Draft

```toml donna
id = "finish"
kind = "donna.lib.finish"
```

Design draft is complete and ready for implementation planning.
