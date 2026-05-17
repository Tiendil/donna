# Dictionary

## Goal of the document

This document defines terms that are specific to the `donna` project and are shared by multiple specifications.

## Scope

The scope of this specification is limited to project-specific terminology.

The following topics are out of scope:

- detailed behavior.
- implementation requirements.
- configuration schemas.

## Terms

- `artifact` — a Markdown document interpreted by `donna`; currently expected to be a local file with the `.donna.md` extension.
- `workflow` — a state-machine-like graph of operations that guides an agent's work.
- `operation` — a workflow step that Donna can execute, render, or present as an action request.
- `action request` — a request emitted by Donna when workflow execution needs the agent to perform work or choose the next operation.
- `session` — project-local runtime state that Donna uses to continue workflow execution across CLI invocations.
- `protocol` — a CLI output contract selected by `--protocol`.
- `human protocol` — output protocol optimized for terminal users.
- `llm protocol` — output protocol optimized for coding agents that invoke `donna` as a tool.
- `automation protocol` — output protocol optimized for programs; output is serialized as JSON Lines.
- `warning` — a non-fatal problem discovered while processing a request.
