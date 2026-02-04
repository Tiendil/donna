# Default Text Artifacts Behavior

```toml donna
kind = "donna.lib.specification"
```

This document describes the default format and behavior of Donna's text artifacts.
This format and behavior is what should be expected by default from an artifact if not specified otherwise.

## Overview

An artifact is any text or binary document that Donna manages in its worlds. For example, via CLI commands `donna -p <protocol> artifacts …`.

The text artifact has a source and one or more rendered representations, produced in specific rendering modes.

— The source is the raw text content of the artifact as it is stored on disk or in remote storage.
- The representation is the rendered version of the artifact for a specific rendering mode. In practice, the same source is rendered in `view` mode for CLI display, `execute` mode for workflow execution, and `analysis` mode for internal parsing and validation (see "Rendering artifacts").

To change the artifact, developers and agents edit its source.

When you need a scratch file for artifact-related work, use `donna -p <protocol> artifacts tmp '<slug>.<extension>'` to create a temporary file in the workspace temp directory.

To get information from the artifact, developers, agents and Donna view one of its representations (typically via the view rendering mode).

**If you need an information from the artifact, you MUST view its representation**. Artifact sources are only for editing.

Read the specification `{{ donna.lib.view("donna:usage:cli") }}` to learn how to work with artifacts via Donna CLI.

## Source Format and Rendering

The source of the text artifact is a Jinja2-template of Markdown document.

When rendering the artifact, Donna processes the Jinja2 template with a predefined context (at minimum `render_mode` and `artifact_id`, and optionally `current_task`/`current_work_unit` during workflow execution), then renders the resulting Markdown content into the desired representation based on the selected rendering mode.

**Artifact source should not use Jinja2 inheritance features** like `{{ "{% extends %}" }}` and `{{ "{% block %}" }}`.

Donna provides a set of special directives that can and MUST be used in the artifact source to enhance its behavior. Some of these directives are valid for all artifacts, some are valid only for specific section kinds.

Here are some examples:

- `{{ "{{ donna.lib.view(<artifact-id-pattern>) }}" }}` — references another artifact (supports `*` and `**` wildcard patterns). In `view`/`execute` modes it renders an exact CLI command to view the artifact; in `analysis` mode it renders a `$$donna ... $$` marker used for internal parsing.
- `{{ "{{ donna.lib.list(<artifact-id-pattern>) }}" }}` — references artifact listing by pattern (supports `*` and `**` wildcard patterns). In `view`/`execute` modes it renders an exact CLI command to list artifacts; in `analysis` mode it renders a `$$donna ... $$` marker used for internal parsing.
- `{{ "{{ donna.lib.goto(<workflow-operation-id>) }}" }}` — references the next workflow operation to execute. In `view`/`execute` modes it renders an exact CLI command to advance the workflow; in `analysis` mode it renders a `$$donna goto ... $$` marker used to extract workflow transitions.

## Jinja2 rendering

Donna allows all of Jinja2 expressions in artifact sources, except inheritance-related once: `{{ "{% extends %}" }}` , `{{ "{% block %}" }}`, etc.

Donna intentionally hides some parts of the source in the rendered output, but they remain visible in source views (for example, in `artifacts fetch` output or on GitHub):

- fenced code blocks with the `donna` marker (they contain technical information for the Donna, not information for the agent).
- Jinja2 comments like `{{ "{# ... #}" }}`.

## Rendering artifacts

Donna renders the same artifact source into different representations depending on the rendering mode. The mode is internal to Donna (users do not select it directly) and controls how directives are expanded and which metadata is included.

- `view` — default representation used when the CLI loads artifacts for display (`artifacts view`, `artifacts list`, `artifacts validate`). This is the human/agent-facing output.
- `execute` — representation used when Donna executes workflow operations (`sessions run`). It renders directives with task/work-unit context so the resulting text is actionable for the agent.
- `analysis` — internal representation used during parsing and validation. It emits `$$donna ... $$` markers so Donna can extract workflow transitions and other structured signals.

## Structure of a Text Artifact

Technically, any valid Markdown document is a valid text artifact.

However, Donna assigns special meaning to some elements of the Markdown document to provide enhanced behavior and capabilities.

### Sections

Artifact is divided into multiple sections:

- H1 header and all text till the first H2 header is considered the `head section` of the artifact.
- Each H2 header and all text till the next H2 header (or end of document) is considered a `tail section` of the artifact.

Head section provides a description of the artifact and its purpose and MUST contain a configuration block of the artifact. The head section is also the artifact's `primary section` and is used when Donna needs to show a brief summary of the artifact, for example, when listing artifacts or when an operation targets the artifact without specifying a section.

Tail sections describes one of the components of the artifact and CAN contain configuration blocks as well. Configuration blocks placed in subsections (h3 and below) count as part of the parent tail section.

The content of the header (text after `#` or `##`) is considered the section title.

Donna always interprets the head section as a general description of the artifact and treats it as the primary section.

Donna interprets a tail section according to the primary section kind and configuration blocks in that section.

### Configuration Blocks

Configuration blocks are fenced code blocks with specified primary format, followed by the `donna` keyword and, optionally, list of properties.

The supported primary formats are: TOML, JSON, YAML. **You MUST prefer TOML for configuration blocks**.

The configuration block properties format is `property1 property2=value2 property3=value3"`, which will be parsed into a dictionary like:

```python
{
    "property1": True,
    "property2": "value2",
    "property3": "value3",
}
```

The content of the block is parsed according to the primary format and interpreted according its properties.

Configuration blocks are parsed by Donna and removed from rendered Markdown representations (see "Jinja2 rendering"); they remain in the source for editing and inspection (e.g., via `artifacts fetch` or the repository file).

Fences without `donna` keyword are considered regular code blocks and have no special meaning for Donna.

### Configuration Merging

When a section contains multiple configuration blocks, Donna merges them in document order.

- The merge is applied per section: the head section is merged independently, and each tail section has its own merged configuration.
- Config blocks are merged in the order they appear; later blocks override earlier keys.
- The merge is shallow: if a key maps to a nested object, a later block replaces the whole value (there is no deep merge).
- Config blocks in subsections (H3 and below) belong to their parent H2 tail section and are merged into that section's configuration.

### Artifact Tags

Artifacts can include semantic tags via a `tags` field in the section configuration. Tags are a list of strings and default to an empty list `[]` when omitted.

Tags are used for deterministic artifact filtering and discovery (for example, via `donna -p <protocol> artifacts list ... --tag <tag>`). Tags are typically attached to the primary section and describe the artifact as a whole.

The canonical list of standard tags is documented in `donna:intro`.

## Section Kinds, Their Formats and Behaviors

### Header section

Header section MUST contain a config block with a `kind` property. The `kind` MUST be a full Python import path pointing to the primary section kind instance.

Example (`donna` keyword skipped for examples):

```toml
kind = "donna.lib.specification"
```

Header section MUST also contain short human-readable description of the artifact outside of the config block.

### Kind: Specification

Specification artifacts describe various aspects of the project in a structured way.

Currently there is no additional structure or semantics for this kind of artifact.

### Kind: Workflow

Workflow artifacts describe a sequence of operations that Donna and agents can perform to achieve a specific goal.

Workflow is a Finite State Machine (FSM) where each tail section describes one operation in the workflow.

Donna validates workflows by ensuring the start operation exists, reachable sections are valid operations, final operations have no outgoing transitions, and non-final operations have at least one outgoing transition. It does not currently report unreachable sections.

Workflow start operation MUST be declared in the workflow head-section config via `start_operation_id`
and MUST reference an existing operation section.

Example (`donna` keyword skipped for examples):

```toml
kind = "donna.lib.workflow"
start_operation_id = "start_operation"
```

Each tail section MUST contain config block with `id` and `kind` properties that specifies the identifier and kind of the operation.

Example (`donna` keyword skipped for examples):

```toml
id = "operation_id"
kind = "donna.lib.request_action"
```

#### Kinds of Workflow Operations

1. `donna.lib.request_action` operation kind indicates that Donna will request the agent to perform some action.

The content of the tail section is the text instructions for the agent on what to do.

Example of the instructions:

```
1. Run `some cli command` to do something.
2. If no errors encountered `{{ '{{ donna.lib.goto("next_operation") }}' }}`
3. If errors encountered `{{ '{{ donna.lib.goto("error_handling_operation") }}' }}`

Here may be any additional instructions, requirements, notes, references, etc.
```

`donna.lib.goto` directive will be rendered in the direct instruction for agent of what to call after it completed the action.

**The body of the operation MUST contain a neat strictly defined algorithm for the agent to follow.**

2. `donna.lib.run_script` operation kind executes a script from the operation body without agent/user interaction.

The body of the operation MUST include exactly one fenced code block whose info string includes `<language> donna script`.
Any other text in the operation body is ignored.

Script example:

```bash donna script
#!/usr/bin/bash

echo "Hello, World!"
```

Configuration options:

```toml
id = "<operation_id>"
kind = "donna.lib.run_script"

save_stdout_to = "<variable_name>"  # optional
save_stderr_to = "<variable_name>"  # optional

goto_on_success = "<next_operation_id>"  # required
goto_on_failure = "<next_operation_id>"  # required
goto_on_code = {                         # optional
    "1" = "<next_operation_id_for_code_1>"
    "2" = "<next_operation_id_for_code_2>"
}

timeout = 60  # optional, in seconds
```

Routing rules:

- Exit code `0` routes to `goto_on_success`.
- Non-zero exit codes first check `goto_on_code`, then fall back to `goto_on_failure`.
- Timeouts are treated as exit code `124`.

When `save_stdout_to` and/or `save_stderr_to` are set, the operation stores captured output in the task context
under the specified variable names.

3. `donna.lib.output` operation kind emits its body as an output cell and then continues to the configured next step.

The body of the operation is rendered as an output cell during execution.

Configuration options:

```toml
id = "<operation_id>"
kind = "donna.lib.output"
next_operation_id = "<next_operation_id>"  # required
```

4. `donna.lib.finish` operation kind indicates that the workflow is finished.

The body of the operation is rendered as an output cell before the workflow completes.

Each possible path through the workflow MUST end with this operation kind.

## Directives

Donna provides multiple directives that MUST be used in the artifact source to enhance its behavior.

Here they are:

1. `{{ "{{ donna.lib.view(<artifact-id-pattern>) }}" }}` — references another artifact (supports `*` and `**` wildcard patterns). In `view`/`execute` modes it renders an exact CLI command to view the artifact; in `analysis` mode it renders a `$$donna ... $$` marker.
2. `{{ "{{ donna.lib.list(<artifact-id-pattern>) }}" }}` — references artifact listing by pattern (supports `*` and `**` wildcard patterns). In `view`/`execute` modes it renders an exact CLI command to list artifacts; in `analysis` mode it renders a `$$donna ... $$` marker.
3. `{{ "{{ donna.lib.goto(<workflow-operation-id>) }}" }}` — references the next workflow operation to execute. In `view`/`execute` modes it renders an exact CLI command to advance the workflow; in `analysis` mode it renders a `$$donna goto ... $$` marker used for transition extraction.
4. `{{ "{{ donna.lib.task_variable(<variable_name>) }}" }}` — in `view` mode renders a placeholder note about task-variable substitution, in `execute` mode renders the actual task-context value (or an explicit error marker if missing), and in `analysis` mode renders a `$$donna task_variable ... $$` marker.
