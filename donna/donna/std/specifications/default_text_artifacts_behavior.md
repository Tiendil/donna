# Default Text Artifacts Behavior

```toml donna
description = """
This document describes the default format and behavior of Donna's text artifacts. This format and behavior is what should be expected by default from an artifact if not specified otherwise.
"""
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

Read the specification `{{ view("donna.specifications.donna_usage") }}` to learn how to work with artifacts via Donna CLI.

## Source Format and Rendering

The source of the text artifact is a Jinja2-template of Markdown document.

When rendering the artifact, Donna processes the Jinja2 template with a predefined set of variables and filters, and then renders the resulting Markdown content into the desired representation.

**Artifact source should not use Jinja2 inheretance features** like `{% extends %}` and `{% block %}`.

Donna provides a set of special callbacks that can and MUST be used in the artifact source to enhance its behavior. Some of these callbacks are valid for all artifacts, some are valid only for specific artifact kinds.

Here are some examples:

- `{{ view("<artifact-id>") }}` — references another artifact. Depending of the rendering mode can be: exect CLI command to view the artifact, specially formatted reference link to the artifact to easier track dependencies.
- `{{ goto("<workflow-operation-id>") }}` — references the next workflow operation to execute. Depending of the rendering mode can be: exect CLI command to push workflow forward, specially formatted reference link to the operation to enable FSM validation of the workflow.

## Structure of a Text Artifact

Technically, any valid Markdown document is a valid text artifact.

However, Donna assignes special meaning to some elements of the Markdown document to provide enhanced behavior and capabilities.

### Sections

Artifact is devided into multiple sections:

- H1 header and all text till the first H2 header is considered the `head section` of the artifact.
- Each H2 header and all text till the next H2 header (or end of document) is considered a `tail section` of the artifact.

Head section provides a description of the artifact and its purpose and MUST contain a configuration block of the artifact. Also, header section is used when Donna needs to show a brief summary of the artifact, for example, when listing artifacts.

Tail sections describes one of the components of the artifact and CAN contain configuration blocks as well.

### Configuration Blocks

Configuration blocks are fenced code blocks with specified primary format, followed by the `donna` keyword and, optionally, list of properties.

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
