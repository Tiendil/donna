# Show Workflow Spec + Schema

<!-- This is a temporary worflow, later Donna should have a specialized command to display the spec -->

This workflow guides an agent through loading a workflow artifact source, choosing the correct FSM graph DSL, and producing a concise schema summary with a graph and per-operation descriptions.

## Read workflow source

```toml donna
id = "read_workflow_source"
kind = "donna.python.ops:request_action"
fsm_mode = "start"
```

1. Identify the full workflow artifact id to summarize from the developer request (for example: `project.workflows.grooming`).
2. If the workflow id is missing or ambiguous, ask the developer to provide the exact id, then repeat this operation.
3. Fetch the workflow artifact source with:
   - `./bin/donna.sh artifacts fetch '<workflow-id>' /tmp/workflow_source.md`
4. Read the fetched source to capture:
   - Workflow name (H1 title) and short description.
   - `start_operation_id` from the head config.
   - Each operation `id`, `kind`, and any {% raw %}`{{ goto(...) }}`{% endraw %} transitions in its body.
5. Continue to {{ goto("select_fsm_dsl") }}.

## Select FSM graph DSL

```toml donna
id = "select_fsm_dsl"
kind = "donna.python.ops:request_action"
```

1. Determine whether the developer requested a specific FSM graph DSL (from the original request or provided inputs).
2. If a DSL is specified, record it verbatim for rendering.
3. If no DSL is specified, select Mermaid DSL.
4. Continue to {{ goto("render_schema") }}.

## Render short schema

```toml donna
id = "render_schema"
kind = "donna.python.ops:request_action"
```

1. Produce the schema output in the exact meta format below, using the selected DSL for the FSM graph:

```
# <workflow name>

<very short one sentence description of what it does>

<FSM graph description in some DSL>

<list of operations: `<id>` — <short one sentence description of what it does>
```

2. Ensure the FSM graph includes all operations and transitions, and clearly marks the start and finish operations.
3. For Mermaid, use a `stateDiagram-v2` or `flowchart` representation and keep node ids aligned with operation ids.
4. For each operation list entry, write a single concise sentence that is clean, complete, and faithful to the operation body.
5. Continue to {{ goto("refine_schema") }}.

## Refine schema output

```toml donna
id = "refine_schema"
kind = "donna.python.ops:request_action"
```

1. Re-read the produced schema and improve clarity and correctness without changing the required format.
2. Tighten wording to keep each description to a single clean sentence while still being thorough and accurate.
3. Ensure the DSL selection rule is reflected in the graph and described output.
4. Continue to {{ goto("validate_schema") }}.

## Validate schema output

```toml donna
id = "validate_schema"
kind = "donna.python.ops:request_action"
```

1. Verify the output contains the title, one-sentence description, FSM graph, and operation list in the required order.
2. Confirm the chosen DSL is correct (developer-specified or Mermaid by default).
3. Confirm each operation description is a single sentence and matches the operation purpose.
4. If any check fails, return to {{ goto("refine_schema") }}.
5. If all checks pass, proceed to {{ goto("finish") }}.

## Finish

```toml donna
id = "finish"
kind = "donna.python.ops:finish_workflow"
```

Workflow complete.
