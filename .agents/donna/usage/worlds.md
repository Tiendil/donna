# Donna World Layout

This document describes how Donna discovers and manages its project artifacts.
Including usage docs, work workflows, operations, current work state and additional code.

## Overview

In order to function properly and to perform in a full potential, Donna relies on a set of artifacts
that guide its behavior and provide necessary capabilities.

These artifacts are represented as text files, primary in Markdown format, however other text-based
formats can be used as well, if explicitly requested by the developer or by the workflows.

Donna discovers these artifacts in a single built-in project world rooted at `<project-root>`.
The project world is a singleton object configured in code and backed by the project's filesystem.
Donna does not read world definitions from `<project-root>/donna.toml`.

The project world and its primary artifact areas are:

- `../../../specs/**` — artifacts under `<project-root>/specs`, owned by the project itself.
- `../**` — synced Donna usage specs and workflows under `<project-root>/.agents/donna`.
- `@/.session/donna/**` — session artifacts under `<project-root>/.session/donna`.

The project world has a free layout, defined by the developers who own the project.

## Artifact Access

Donna has read access to artifacts stored in the project world. It discovers, fetches, renders, and validates project artifacts, but it does not create, update, move, copy, or delete them.

Developers and external tools are responsible for mutating project artifacts before Donna reads or validates them.

Donna still writes its own session state under `<project-root>/.session/donna`, but that internal state storage is separate from world-artifact mutation.

## Intro Artifacts

It is a recommended practice to provide short introductory files such as `../intro.md` and `../../../specs/intro.md` at meaningful roots inside the project world.

So, the agent can read relevant introduction files such as `../intro.md` or `../../../specs/intro.md`.
