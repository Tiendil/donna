# Default Text Artifacts Behavior

```toml donna
kind = "donna.artifacts:specification"
```

This document describes the default format and behavior of Donna's text artifacts.
This format and behavior is what should be expected by default from an artifact if not specified otherwise.

## Overview

An artifact is any text or binary document that Donna manages in its worlds. For example, via CLI commands `donna artifacts …`.

The text artifact has a source and a representation.

— The source is the raw text content of the artifact as it is stored on disk or in remote storage.
- The representation is the rendered version of the artifact. The artifact can have multiple representations for different purposes. For example, a markdown artifact can have agent-centric representation with extra metadata, a human-centric representation with more content formatting, a DSL representation for artifacts validation, structured representation that renders semantic schema of the artifact, a specialized representation for other tools, etc.

To change the artifact, developers and agents edit its source.

To get information from the artifact, developers, agents and Donna view one of its representation.

**If you need an information from the artifact, you MUST view its representation**. Artifact sources are only for editing.

Read the specification `{{ donna.directives.view("donna.specifications.donna_usage") }}` to learn how to work with artifacts via Donna CLI.

## Source Format and Rendering

The source of the text artifact is a Jinja2-template of Markdown document.

When rendering the artifact, Donna processes the Jinja2 template with a predefined set of variables and filters, and then renders the resulting Markdown content into the desired representation.

**Artifact source should not use Jinja2 inheretance features** like `{{ "{% extends %}" }}` and `{{ "{% block %}" }}`.

Donna provides a set of special directives that can and MUST be used in the artifact source to enhance its behavior. Some of these directives are valid for all artifacts, some are valid only for specific artifact kinds.

Here are some examples:

- `{{ "{{ donna.directives.view(<artifact-id>) }}" }}` — references another artifact. Depending of the rendering mode can be: exect CLI command to view the artifact, specially formatted reference link to the artifact to easier track dependencies.
- `{{ "{{ donna.directives.goto(<workflow-operation-id>) }}" }}` — references the next workflow operation to execute. Depending of the rendering mode can be: exect CLI command to push workflow forward, specially formatted reference link to the operation to enable FSM validation of the workflow.

## Structure of a Text Artifact

Technically, any valid Markdown document is a valid text artifact.

However, Donna assignes special meaning to some elements of the Markdown document to provide enhanced behavior and capabilities.

### Sections

Artifact is devided into multiple sections:

- H1 header and all text till the first H2 header is considered the `head section` of the artifact.
- Each H2 header and all text till the next H2 header (or end of document) is considered a `tail section` of the artifact.

Head section provides a description of the artifact and its purpose and MUST contain a configuration block of the artifact. Also, header section is used when Donna needs to show a brief summary of the artifact, for example, when listing artifacts.

Tail sections describes one of the components of the artifact and CAN contain configuration blocks as well. Configuration blocks placed in subsections (h3 and below) count as part of the parent tail section.

The content of the header (text after `#` or `##`) is considered the section title.

Donna always interprets the head section as a general description of the artifact.

Donna interprets a tail section according to the artifact kind and configuration blocks in that section.

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

Configuration blocks are intended to be used by Donna and viewed by developers, so Donna does not render them into most artifact representations.

Fences without `donna` keyword are considered regular code blocks and have no special meaning for Donna.

### Configuration Merging

When a section contains multiple configuration blocks, Donna merges them in document order.

- The merge is applied per section: the head section is merged independently, and each tail section has its own merged configuration.
- Config blocks are merged in the order they appear; later blocks override earlier keys.
- The merge is shallow: if a key maps to a nested object, a later block replaces the whole value (there is no deep merge).
- Config blocks in subsections (H3 and below) belong to their parent H2 tail section and are merged into that section's configuration.

## Artifact Kinds, Their Formats and Behaviors

### Header section

Header section MUST contain a config block with a `kind` property. The `kind` MUST be a full artifact-local id pointing to the artifact kind section.

Example (`donna` keyword skipped for examples):

```toml
kind = "donna.artifacts:specification"
```

Header section MUST also contain short human-readable description of the artifact outside of the config block.

### Kind: Specification

Specification artifacts describe various aspects of the project in a structured way.

Currently there is no additional structure or semantics for this kind of artifact.

### Kind: Workflow

Workflow artifacts describe a sequence of operations that Donna and agents can perform to achieve a specific goal.

Workflow is a Finite State Machine (FSM) where each tail section describes one operation in the workflow.

Donna do additional work to validate that FSM is correct and that there are no unreachable operations, no dead ends, etc. In case of problems Donna notifies the agent about the issues.

Workflow head config MUST contain `start_operation_id` property that specifies the identifier of the operation where the workflow starts.

Example (`donna` keyword skipped for examples):

```toml
start_operation_id = "operation_id"
kind = "donna.artifacts:workflow"
```

Each tail section MUST contain config block with `id` and `kind` properties that specifies the identifier and kind of the operation.

Example (`donna` keyword skipped for examples):

```toml
id = "operation_id"
kind = "donna.operations:request_action"
```

#### Kinds of Workflow Operations

1. `donna.operations:request_action` operation kind indicates that Donna will request the agent to perform some action.

The content of the tail section is the text instructions for the agent on what to do.

Example of the instructions:

```
1. Run `some cli command` to do something.
2. If no errors encountered `{{ '{{ donna.directives.goto("next_operation") }}' }}`
3. If errors encountered `{{ '{{ donna.directives.goto("error_handling_operation") }}' }}`

Here may be any additional instructions, requirements, notes, references, etc.
```

`donna.directives.goto` directive will be rendered in the direct instruction for agent of what to call after it completed the action.

**The body of the operation MUST contain a neat strictly defined algorithm for the agent to follow.**

2. `donna.operations:finish_workflow` operation kind indicates that the workflow is finished.

Each possible path through the workflow MUST end with this operation kind.

## Directives

Donna provides multiple directives that MUST be used in the artifact source to enhance its behavior.

Here they are:

1. `{{ "{{ donna.directives.view(<full-artifact-id>) }}" }}` — references another artifact. Depending of the rendering mode can be: exect CLI command to view the artifact, specially formatted reference link to the artifact to easier track dependencies.
2. `{{ "{{ donna.directives.goto(<workflow-operation-id>) }}" }}` — references the next workflow operation to execute. Depending of the rendering mode can be: exect CLI command to push workflow forward, specially formatted reference link to the operation to enable FSM validation of the workflow.
