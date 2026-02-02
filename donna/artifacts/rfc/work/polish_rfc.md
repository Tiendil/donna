
# Polish an RFC Document

```toml donna
kind = "donna.lib.workflow"
start_operation_id = "start"
```

## Start Work

```toml donna
id = "start"
kind = "donna.lib.request_action"
fsm_mode = "start"
```

1. Read the specification `{{ donna.lib.view("donna:rfc:specs:request_for_change") }}` if you haven't done it yet.
2. Read the specification `{{ donna.lib.view("donna:usage:artifacts") }}` if you haven't done it yet.
3. Determine the artifact with an RFC draft and read it.
4. `{{ donna.lib.goto("review_rfc_draft") }}`

## Review the RFC Draft

```toml donna
id = "review_rfc_draft"
kind = "donna.lib.request_action"
```

1. Run a research workflow `donna:engine:work:research` to review the draft, identify gaps, inconsistencies, and areas for improvement.
2. `{{ donna.lib.goto("implement_improvements") }}`

## Implement Improvements

```toml donna
id = "implement_improvements"
kind = "donna.lib.request_action"
```

1. Read the specification `{{ donna.lib.view("donna:rfc:specs:request_for_change") }}` if you haven't done it yet.
2. Based on the research findings, make necessary improvements to the RFC draft artifact.
3. Ensure that the document adheres to the RFC standards and guidelines.
4. `{{ donna.lib.goto("finish") }}`

## Finish

```toml donna
id = "finish"
kind = "donna.lib.finish"
```
