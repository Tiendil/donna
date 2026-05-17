# `donna` Workflows

Donna workflows are Markdown artifacts that describe finite-state machines for agent work.

Use this document when you need to create, review, debug, or change a `*.donna.md` workflow file.

A workflow does not do the agent's job. It defines control flow:

- which operation starts the work;
- which deterministic steps Donna can run by itself;
- where Donna must stop and ask the agent to act;
- which next operations are valid after each stop;
- when the workflow is complete.

The agent still reads project instructions, edits files, runs tools, uses judgment, and reports results. Donna keeps the process explicit, resumable, and validated.

## Workflow Files

Donna discovers workflow artifacts under the directories configured in `donna.toml:workflow_dirs`. For configuration details, defaults, and directory selection guidance, read `donna -p llm skill configuration`.

Only files ending with `.donna.md` are workflow artifacts.

Relative and absolute paths are accepted by Donna CLI commands when they resolve inside the Donna project root, but `@/` paths are stable from any current working directory.

## File Shape

A workflow file is one Markdown document with exactly one H1 section followed by zero or more H2 sections.

The H1 section is the workflow section. Each H2 section is usually one workflow operation.

## IDs

Donna uses three related ids when working with workflows.

A workflow artifact id identifies the workflow file. Use project-root anchored artifact ids in workflow instructions and notes:

```text
@/workflows/do-work.donna.md
@/.session/donna/plans/implement-feature.donna.md
```

A section id identifies one section inside a workflow artifact. For workflow operations, it is the `id` field in the operation's config block:

```toml
id = "finish"
```

A full artifact section id identifies one section in one artifact by appending `:<section_id>` to the artifact id:

```text
@/workflows/do-work.donna.md:finish
```

Use full artifact section ids when completing action requests. Use local section ids in workflow config fields and `goto` directives inside the same workflow.

## Minimal Workflow

````markdown
# Example Workflow

This workflow checks the current time, asks the agent whether it is tea time, and branches on the answer.

## Get Current Time

```toml donna
id = "get_current_time"
kind = "donna.lib.run_script"
save_stdout_to = "current_time"
goto_on_success = "ask_about_tea"
goto_on_failure = "finish"
```

```bash donna script
#!/usr/bin/env bash
date +%H:%M
```

## Ask About Tea

```toml donna
id = "ask_about_tea"
kind = "donna.lib.request_action"
```

The current time is:

```text
{{ donna.lib.task_variable("current_time") }}
```

Is it time to drink tea?

1. If yes, `{{ donna.lib.goto("turn_on_kettle") }}`.
2. If no, `{{ donna.lib.goto("finish") }}`.

## Turn On Kettle

```toml donna
id = "turn_on_kettle"
kind = "donna.lib.request_action"
```

Turn on the kettle, then `{{ donna.lib.goto("finish") }}`.

## Finish

```toml donna
id = "finish"
kind = "donna.lib.finish"
```

The workflow is complete. Report the result to the developer.
````

## Markdown Parsing Rules

Donna's Markdown parser uses only H1 and H2 headings as section boundaries.

- The first heading must be H1.
- There can be only one H1.
- H2 starts a tail section.
- H3 and deeper headings stay inside the current H1 or H2 section body.
- Text before the first H1 is invalid.

Donna removes `donna` config and script code fences from the rendered section description. Ordinary code fences remain visible to the agent.

Each section may have at most one config block. A config block is a fenced code block marked with `donna`; `toml donna` is treated as `toml donna config`.

````markdown
```toml donna
id = "operation_id"
kind = "donna.lib.request_action"
```
````

The parser supports TOML, JSON, YAML, and YML config formats, but write workflow config as TOML unless the project has a clear reason to do otherwise.

Script blocks are fenced code blocks marked with both `donna` and `script`:

````markdown
```bash donna script
#!/usr/bin/env bash
echo "hello"
```
````

A `donna.lib.run_script` operation must have exactly one script block.

## Section Config

All section config is strict. Unknown fields are invalid.

Common fields:

- `id`: local section id. The H1 defaults to `primary`; H2 sections without `id` get generated unstable ids. Set explicit ids for all operation sections.
- `kind`: primitive path that tells Donna how to interpret the section. The H1 defaults to `donna.lib.workflow`; H2 sections default to `donna.lib.text`.
- `fsm_mode`: optional operation mode. Valid values are `start`, `normal`, and `final`. The default is `normal`.

Section ids may contain ASCII letters, digits, underscores, hyphens, and dots. Use lowercase snake case for readability:

```toml
id = "review_changes"
```

Do not rely on `fsm_mode = "start"` to choose the start operation. Donna starts from the H1 `start_operation_id` when it is set, otherwise from the first H2 section. `fsm_mode = "start"` is metadata.

## Workflow Section

The H1 section is normally a `donna.lib.workflow` section. It describes the whole workflow and optionally chooses the first operation.

````markdown
```toml donna
id = "primary"
kind = "donna.lib.workflow"
start_operation_id = "start"
```
````

Fields:

- `id`: optional, defaults to `primary`.
- `kind`: optional, defaults to `donna.lib.workflow`.
- `start_operation_id`: optional local id of the operation to run first.

If `start_operation_id` is omitted, Donna uses the first H2 section. If the workflow has no H2 section and no explicit start operation, validation fails.

Write the H1 body as a concise summary. It is what `donna -p llm list` shows for the workflow.

## Operation Sections

Each operation is an H2 section with a config block. The H2 title becomes the operation title. The body becomes the operation instructions, output text, or script host depending on `kind`.

Standard operation kinds are:

- `donna.lib.request_action`: stop and ask the agent to do work.
- `donna.lib.run_script`: run a deterministic shell script from the project root.
- `donna.lib.output`: print information, then continue automatically.
- `donna.lib.finish`: print final information and finish the workflow task.

`donna.lib.text` is not an operation. It can be used for unreachable notes in an artifact, but a reachable workflow section must be an operation or validation fails.

### `request_action`

Use `donna.lib.request_action` when the next step needs agent judgment, file edits, research, tool use, or communication with the developer.

````markdown
```toml donna
id = "review_changes"
kind = "donna.lib.request_action"
```
````

Donna emits the section body as an action request and waits. The agent must complete the request by choosing one of the transitions declared in the action request body.

Declare transitions with `{{ donna.lib.goto("<next_operation_id>") }}`:

```markdown
1. Review the changes.
2. If fixes are needed, `{{ donna.lib.goto("fix_changes") }}`.
3. If no fixes are needed, `{{ donna.lib.goto("finish") }}`.
```

Each `goto` declares an allowed transition from the current request action to the target operation.

Rules:

- A reachable `request_action` operation must contain at least one `goto`.
- `request_action` cannot use `fsm_mode = "final"`.
- The next operation passed to `complete-action-request` must be one of the operation's declared `goto` targets.
- Use explicit result-based choices in the text so the agent knows which transition to select.

### `run_script`

Use `donna.lib.run_script` for deterministic checks or commands that Donna can run without agent judgment.

````markdown
## Run Tests

```toml donna
id = "run_tests"
kind = "donna.lib.run_script"
save_stdout_to = "test_stdout"
save_stderr_to = "test_stderr"
goto_on_success = "finish"
goto_on_failure = "fix_tests"
timeout = 120
```

```bash donna script
#!/usr/bin/env bash
./bin/test.sh
```
````

Fields:

- `goto_on_success`: required operation id for exit code `0`.
- `goto_on_failure`: required fallback operation id for non-zero exit codes.
- `goto_on_code`: optional TOML table mapping specific non-zero exit codes to operation ids.
- `save_stdout_to`: optional task-context key for stdout.
- `save_stderr_to`: optional task-context key for stderr.
- `timeout`: optional timeout in seconds, default `60`.
- `fsm_mode`: optional, default `normal`.

Example with exit-code-specific routing:

```toml
goto_on_success = "finish"
goto_on_failure = "fix_failure"

[goto_on_code]
"124" = "fix_timeout"
"2" = "fix_usage"
```

Exit code `0` must not be placed in `goto_on_code`; use `goto_on_success`.

Execution behavior:

- Donna writes the script to a temporary executable file.
- The script runs from the Donna project root.
- The process inherits the environment.
- Stdin is closed.
- Stdout and stderr are captured.
- A timeout returns exit code `124`.
- Donna queues the selected next operation automatically.

Script output is not automatically shown to the agent. Save it to task context and read it with `donna.lib.task_variable` in a later request action.

### `output`

Use `donna.lib.output` when Donna should print information and then continue automatically.

````markdown
```toml donna
id = "show_context"
kind = "donna.lib.output"
next_operation_id = "next_step"
```
````

Fields:

- `next_operation_id`: required operation id to queue after printing the section body.
- `fsm_mode`: optional, default `normal`.

A reachable `output` operation must have `next_operation_id`.

### `finish`

Use `donna.lib.finish` for the terminal operation.

````markdown
```toml donna
id = "finish"
kind = "donna.lib.finish"
```
````

`finish` is always final. It prints the section body and completes the active workflow task. It must not have outgoing transitions.

There may be multiple `finish` operations.

Use the finish body to tell the agent what to report:

```markdown
Workflow completed. Report the files changed, verification performed, and remaining risks.
```

## Transitions And Validation

Donna validates the reachable operation graph starting from the workflow start operation.

An operation is reachable when it is the start operation or it can be reached through outgoing transitions from another reachable operation.

Outgoing transitions come from operation metadata:

- `request_action`: every `{{ donna.lib.goto("...") }}` in the analyzed request body.
- `run_script`: `goto_on_success`, `goto_on_failure`, and all `goto_on_code` values.
- `output`: `next_operation_id`.
- `finish`: no transitions.

Validation rules for the reachable graph:

- Every reachable section must exist.
- Every reachable non-workflow section must be an operation.
- Every reachable non-final operation must have at least one outgoing transition.
- Every reachable final operation must have no outgoing transitions.

Primitive-specific validation also runs for all sections.

Run validation after every workflow edit:

```bash
donna -p llm validate @/workflows/example.donna.md
```

Render the workflow when transitions or directives look wrong:

```bash
donna -p llm render @/workflows/example.donna.md --mode analysis
```

## Execution Notes

`donna -p llm run @/path/to/workflow.donna.md` starts the workflow in the current session.

Execution loop:

1. Donna loads the artifact and starts at the primary workflow section.
2. The workflow section queues the start operation.
3. Donna executes queued work units for the current task.
4. Deterministic operations can queue the next operation immediately.
5. `request_action` creates an action request and pauses.
6. The agent performs the request and calls `complete-action-request` with the chosen next operation id.
7. Donna validates that the transition is allowed, queues the next operation, and continues.
8. `finish` completes the task.

## Directives And Rendering

Donna renders workflow Markdown with Jinja directives.

Directives have two author-facing uses:

- Structural directives define workflow structure that is not convenient to express with static config alone.
- Informational directives insert meaningful runtime information into text shown to the agent.

Donna normally renders text for the agent in `view` mode. Other render modes exist, but they are implementation details and should not affect how you write normal workflows.

Workflow authors may use regular Jinja2 constructs such as variables, conditionals, loops, and macros to produce complex agent-facing text.

Use view rendering when debugging what an agent will see:

```bash
donna -p llm render @/workflows/example.donna.md --mode view
```

Do not use templates that add or remove headings, config blocks, or operation ids depending on render context. Workflow structure should stay stable after rendering.

### `goto`

`{{ donna.lib.goto("next_operation") }}` declares an allowed transition from a `request_action` operation to another operation in the same workflow.

Use `goto` only in `request_action` instructions. The visible rendered text tells the agent how to complete the action request with that next operation.

Example:

```markdown
1. If the check passed, `{{ donna.lib.goto("finish") }}`.
2. If the check failed, `{{ donna.lib.goto("fix_issue") }}`.
```

The argument is a local section id, not a full artifact section id.

### `task_variable`

`{{ donna.lib.task_variable("name") }}` inserts a value saved in the current task context.

Use it to show the agent output captured by earlier automated operations, especially `run_script` operations with `save_stdout_to` or `save_stderr_to`.

Example:

````markdown
```text
{{ donna.lib.task_variable("test_stdout") }}
```
````

Use the same key that the earlier operation saved:

```toml
save_stdout_to = "test_stdout"
```

## Creating Workflows

Start with the workflow's control-flow shape, then fill operation instructions.

Recommended process:

1. Name the workflow by its outcome, not by a generic process label.
2. Write the H1 summary that `donna list` should show.
3. Add one operation per meaningful state or decision point.
4. Prefer `run_script` for deterministic checks and `request_action` for agent judgment.
5. Add a `finish` operation(s) with clear reporting instructions.
6. Validate the workflow.

Good operation titles stand alone:

- `Run Unit Tests`
- `Fix Formatter Output`
- `Review Deliverables`
- `Check Migration File`

Avoid titles that only make sense by order:

- `Step 1`
- `Part Two`
- `Continue`
- `Do It`

Keep request actions specific. Each request should have enough context for the agent to act and enough transition choices to continue correctly.

Split large request actions when they mix unrelated work. A good split is usually:

- research or inspect;
- implement one bounded change;
- verify the changed behavior;
- decide where to go next.

Remember, you can add references to project-specific specifications in the action request text — no need to repeat all documentation there. Keep action requests short and concise.

## Workflow Design Patterns

Linear workflow:

```text
start -> do_work -> verify -> finish
```

Retry loop:

```text
run_check -> fix_check -> run_check
run_check -> finish
```

Review gate:

```text
implement -> review
review -> implement
review -> finish
```

Decision tree:

```text
classify_request -> simple_path
classify_request -> complex_path
classify_request -> ask_for_clarification
simple_path -> finish
complex_path -> plan_work
ask_for_clarification -> classify_request
```

Classification tree:

```text
check_outlook -> class_play_tennis
check_outlook -> check_humidity
check_outlook -> check_wind
check_humidity -> class_stay_home
check_humidity -> class_play_tennis
check_wind -> class_stay_home
check_wind -> class_play_tennis
class_play_tennis -> finish
class_stay_home -> finish
```

Script with manual repair:

```text
run_script success -> next_step
run_script failure -> fix_failure
fix_failure -> run_script
```

Use loops deliberately. The operation that loops back should say what changed and why rerunning the earlier operation is necessary.

## Debugging Workflows

If a workflow is not listed:

1. Check that the file ends with `.donna.md`.
2. Check that it is under one of `workflow_dirs`.
3. Check that the workflow directory exists.
4. Run `donna -p llm list` from the intended Donna project root or pass `--root`.

If validation says a start operation is missing:

1. Check `start_operation_id` in the H1 config.
2. Check the target H2 `id`.
3. If no explicit start is set, check that the workflow has at least one H2 section.

If validation says an operation has no outgoing transitions:

1. For `request_action`, add `{{ donna.lib.goto("next") }}` in the request body.
2. For `run_script`, set `goto_on_success` and `goto_on_failure`.
3. For `output`, set `next_operation_id`.
4. For terminal operations, use `kind = "donna.lib.finish"`.

If an action request cannot transition to the chosen operation:

1. Use one of the next operation ids shown in the action request.
2. Check that the `goto` target is local to the same workflow artifact.
3. Re-render in `analysis` mode to confirm Donna detected the transition.

If a script failure output is missing from a later request action:

1. Check `save_stdout_to` and `save_stderr_to` keys.
2. Check that `task_variable` uses the exact same key.
3. Check that the operation reading the variable runs after the script operation.

## Authoring Checklist

Before considering a workflow ready:

1. The file is under a configured workflow directory and ends with `.donna.md`.
2. The H1 summary explains the workflow outcome.
3. Every operation H2 has a stable `id` and explicit `kind`.
4. The start operation is intentional.
5. Every non-final reachable operation has an outgoing transition.
6. Every final operation is `donna.lib.finish` or has `fsm_mode = "final"` with no transitions.
7. Every `request_action` gives the agent clear completion choices.
8. Every `run_script` has success and failure routing.
9. Script output needed by the agent is saved and later read from task context.
10. `donna -p llm validate <workflow-id>` succeeds.
11. `donna -p llm render <workflow-id> --mode view` is readable by an agent.
