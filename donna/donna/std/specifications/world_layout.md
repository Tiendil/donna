# Donna World Layout

```toml donna
description = """
This document describes how Donna discovers and manages its dynamic and/or external artifacts.
Including specifications, workflows, operations, current work state and additional code.
"""
```

This document describes how Donna discovers and manages its dynamic and/or external artifacts.
Including specifications, workflows, operations, current work state and additional code.

## Overview

In order to function properly and to perform in a full potential, Donna relies on a set of artifacts
that guide its behavior and provide necessary capabilities.

These artifacts are represented as text files, primary in Markdown format, however other text-based
formats can be used as well, if explicitly requested by the developer or by the workflows.

Donna discovers these artifacts by scanning the "worlds" specified in `<project-root>/.donna/donna.toml`
as `worlds` list. Most of worlds are filesystem folders, however other world types can be implemented such as:
s3 buckets, git repositories, databases, etc.

Default worlds are filesystem folders: `<donna-package-code>/std`, `~/.donna`, `<project-root>/.donna`

All worlds have a strict layout that Donna MUST follow in order to discover and manage its artifacts properly.

## World Layout

```
.donna/
├── code/ — a folder containing additional Python code that Donna can load and use during its operation.
├── specifications/ — a folder containing specification files that define various aspects of the current project.
├── workflows/ — a folder containing workflow definitions that Donna can use to perform complex tasks.
├── session/ — a folder containing the current state of work being performed by Donna. Exists only in the project world.
```

By default, worlds are read-only. Besides the next exceptions:

- `session` in the project world is read-write, Donna stores its current state of work here.
- `<project-root>/.donna` is read-write when the developer explicitly asks Donna to change it. For example, to add the result of performed work into project specifications.
