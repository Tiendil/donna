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
as `worlds` list. Most worlds are filesystem folders, however other world types can be implemented such as:
s3 buckets, git repositories, databases, etc.

The default world and its primary project-relative artifact areas are:

- `project` — `<project-root>` — the single default filesystem world.
- `project:specs:*` — artifacts under `<project-root>/specs`, owned by the project itself.
- `project:.agents:donna:*` — synced Donna usage specs and workflows under `<project-root>/.agents/donna`.
- `project:.donna:session:*` — session artifacts under `<project-root>/.donna/session`.

The project world has a free layout, defined by the developers who own the project.

## Artifact Access

Donna has read access to artifacts stored in worlds. It discovers, fetches, renders, and validates world artifacts, but it does not create, update, move, copy, or delete them.

Developers and external tools are responsible for mutating world artifacts before Donna reads or validates them.

Donna still writes its own session state and journal data under `<project-root>/.donna/session`, but that internal state storage is separate from world-artifact mutation.

## Intro Artifacts

It is a recommended practice to provide short introductory artifacts such as `project:.agents:donna:intro` and `project:specs:intro` at meaningful roots inside the project world.

So, the agent can load the relevant introductions in commands such as `donna -p llm artifacts view 'project:**:intro'`.
