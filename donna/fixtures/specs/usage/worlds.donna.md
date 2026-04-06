# Donna Artifact Filesystem Layout

```toml donna
kind = "donna.lib.specification"
```

This document describes how Donna discovers and manages its project artifacts on the filesystem.
Including usage docs, work workflows, operations, current work state and additional code.

## Overview

In order to function properly and to perform in a full potential, Donna relies on a set of artifacts
that guide its behavior and provide necessary capabilities.

These artifacts are represented as text files, primary in Markdown format, however other text-based
formats can be used as well, if explicitly requested by the developer or by the workflows.

Donna discovers these artifacts directly in the project filesystem rooted at `<project-root>`.

The primary artifact areas are:

- Artifacts under `<project-root>/specs`, owned by the project itself.
- Synced Donna usage specs and workflows under `<project-root>/.agents/donna`.
- Session artifacts under `<project-root>/.donna/session`.

The project filesystem has a free layout, defined by the developers who own the project.

## Artifact Access

Donna has read access to artifacts stored in the project filesystem. It discovers, fetches, renders, and validates project artifacts, but it does not create, update, move, copy, or delete them.

Developers and external tools are responsible for mutating project artifacts before Donna reads or validates them.

Donna still writes its own session state and journal data under `<project-root>/.donna/session`, but that internal state storage is separate from project-artifact mutation.

## Intro Artifacts

It is a recommended practice to provide short introductory artifacts such as `../intro.donna.md` and `../../../specs/intro.donna.md` at meaningful roots inside the project filesystem.

So, the agent can load the relevant introductions in commands such as `donna -p llm artifacts view '**/intro.donna.md'`.
