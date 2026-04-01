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

- `donna` — `<project-root>/.agents/donna` — the project-local bundled Donna specs installed from `donna/fixtures/specs` by workspace init/update.
- `home` — `~/.donna/home` — the user-level donna artifacts, i.e. those that should be visible for all workspaces on this machine.
- `project` — `<project-root>/specs` — the project-level donna artifacts, i.e. those that are specific to this project.
- `session` — `<project-root>/.donna/session` — the session world that contains the current state of work performed by Donna.

All worlds have a free layout, defined by developers who own the particular world.

## Artifact Access

Donna has read access to artifacts stored in worlds. It discovers, fetches, renders, and validates world artifacts, but it does not create, update, move, copy, or delete them.

Developers and external tools are responsible for mutating world artifacts before Donna reads or validates them.

Donna still writes its own session state and journal data in the `session` world, but that internal state storage is separate from world-artifact mutation.

## `<world>:intro` artifact

It is a recommended practice to provide a short introductory artifact `intro.md` at the root of each world.

So, the agent can load descriptions of all worlds in a single command like `donna -p llm artifacts view "*:intro"`.
