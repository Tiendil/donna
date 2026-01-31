# Donna World Layout

```toml donna
kind = "donna.lib.specification"
```

This document describes how Donna discovers and manages its dynamic and/or external artifacts.
Including usage docs, work workflows, operations, current work state and additional code.

## Overview

In order to function properly and to perform in a full potential, Donna relies on a set of artifacts
that guide its behavior and provide necessary capabilities.

These artifacts are represented as text files, primary in Markdown format, however other text-based
formats can be used as well, if explicitly requested by the developer or by the workflows.

Donna discovers these artifacts by scanning the "worlds" specified in `<project-root>/.donna/config.toml`
as `worlds` list. Most of worlds are filesystem folders, however other world types can be implemented such as:
s3 buckets, git repositories, databases, etc.

Default worlds and there locations are:

- `donna` — `donna.artifacts` — the subpackage with artifacts provided by Donna itself.
- `home` — `~/.donna/home` — the user-level donna artifacts, i.e. those that should be visible for all workspaces on this machine.
- `project` — `<project-root>/.donna/project` — the project-level donna artifacts, i.e. those that are specific to this project.
- `session` — `<project-root>/.donna/session` — the session world that contains the current state of work performed by Donna.

All worlds have a free layout, defined by developers who own the particular world.

## Write Access

By default, worlds are read-only. Besides the next exceptions:

- `session` in the project world is read-write, Donna stores its current state of work here.
- `project` is read-write when the developer explicitly asks Donna to change it. For example, to add the result of performed work into docs.
