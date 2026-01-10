# Donna Usage Instructions

```toml donna
description = """
This document describes how agents MUST use Donna to manage and perform their workflows.
"""
```

This document describes how agents MUST use Donna to manage and perform their workflows.

**Agents MUST follow the instructions and guidelines outlined in this document precisely.**

## Overview

`donna` is a CLI tool that helps manage the work of AI agents like Codex.

It is designed to to invert control flow: instead of agents deciding what to do next, the `donna` tells agents what to do next by following predefined workflows.

The core idea is that most of high-level workflows are more algorithmic than it may seem at first glance. For example, it may be difficult to fix a particular type issue in the codebase, but the overall process of polishing the codebase is quite linear:

1. Ensure all tests pass.
2. Ensure the code is formatted correctly.
3. Ensure there are no linting errors.
4. Go to the step 1 if you changed something in the process.
5. Finish.

We may need coding agents on the each step of the process, but there no reason for agents to manage the whole grooming loop by themselves — it take longer time, spends tokens and may lead to confusion of agents.

## Development

- All work is always done in the context of a session. There is only one active session at a time.
- You MUST always work on the specific story assigned to you, that is managed by the `donna` tool.
- If developer asked you to do something and you have no session, you create one with the `donna` tool.
- If you have a session, you MUST keep all the information about it in your memory. Ask `donna` tool for the session details when you forget something.
- Donna may work from different environments. You MUST substitute correct `donna` command from the `AGENTS.md` for `<DONNA_CMD>` placeholder in this document when you work with the tool.

## Stories

Story is a semantically consistent unit of work assigned to you by the developer.

Story has no direct representation in donna tool, it it just a convenient way to refer to a particular scope of work.

The session always has exactly one active story at a time.

All work in the context of session/story is managed by the `donna` tool.

### Story workflow

- Yoy start session by calling `<DONNA_CMD> sessions start`.
- After you started a session:
  2. List all possible workflows with command `<DONNA_CMD> artifacts list workflows`.
  3. Choose the most appropriate workflow for the story you are going to work on or ask the developer if you are not sure which workflow to choose.
  4. Start working by calling `<DONNA_CMD> workflows start <workflow-id>`.
  5. The `donna` tool will output descriptions of all operations it performs to complete the story.
  6. The `donna` tool will output **action requests** that you MUST perform. You MUST follow these instructions precisely.
- When you done doing your part, you call `<DONNA_CMD> sessions action-request-completed <action-request-id> <next-full-operation-id>` to report that you completed the action request. `<next-full-operation-id>` MUST contain full identifier of the next operation, like `<world>.<namespace>.<artifact>.<operation-id>`.
- After you report the result:
  1. The `donna` tool will output what you need to do next.
  2. You repeat the process until the story is completed.

### Starting work on a story

- If the developer asked you to do something:
  - run `<DONNA_CMD> sessions status` to get the status of the current session.
  - if the work in completed, run `<DONNA_CMD> sessions start` to start a new session.
  - if there are still a work to do, ask developer if you need to resume the current session or start a new one.
- If the developer asked you to continue your work, you MUST call `<DONNA_CMD> session continue` to get your instructions on what to do next.

### Working with records

A record is a named collection of structured data of different kinds.

- There can be multiple kinds of data attached to a single record.
- Records are exist only in the context of a session.
- Kinds of records are preconfigured in the `donna` tool.
- You generally will get a specification of a scheme for a particular kind of record when you are asked to create or update it.

Donna can ask you to create and manage records related to your session.

Examples of record kinds:

- Plain text record with media type is a kind of record.
- A fixed set of fields with specific types, like "issue tracker ticket" is a kind of record.
- Files with source code of the project IS NOT a kind of record.
- Compiled binaries of the project IS NOT a kind of record.

Use the next commands to work with records related to your session:

- `<DONNA_CMD> records list` — list all records related to the session.
- `<DONNA_CMD> records create <description>` — create a new record without any kinds of data attached.
- `<DONNA_CMD> records delete <record-id>` — delete the record and all its data.
- `<DONNA_CMD> records kind-set <record-id> <record-kind> <json-data>` — set data of a particular kind for the record. Data is passed as JSON string.
- `<DONNA_CMD> records kind-get <record-id> <record-kind>*` — get data of a particular kind(s) for the record.
- `<DONNA_CMD> records kind-delete <record-id> <record-kind>*` — delete data of a particular kind(s) for the record.

Command parameters:

- `<record-id>` — a short ASCII string identifying the record with dash separators. May be a unique slug like `work-description-from-developer` or a parameterized string like `issue-{uid}` where `{uid}` will be replaced with a unique identifier generated by the `donna` tool. Parametrized strings are allowed only when you create a new record.
- `<record-kind>` — a short ASCII string identifying the kind of record with dash separators.
- `<description>` — a short text description of the record.
- `<json-data>` — a JSON string with data of the particular kind. Record kinds have strict JSON schemas that you MUST follow exactly. You can get the schema of the record kind by using the introspection commands described below.

### Working with artifacts

An artifact is a markdown document with some extra metadata stored in one of the Donna's worlds.

Use the next commands to work with artifacts

- `<DONNA_CMD> artifacts list <namespace>` — list all artifacts
- `<DONNA_CMD> artifacts view <world>/<namespace>/<artifact-id>` — get the meaningful (rendered) content of the artifact. This command shows the rendered information about the artifact. Use this command when you need to read the artifact content.
- `<DONNA_CMD> artifacts fetch <world>/<namespace>/<artifact-id> <file-path>` — download the original source of the artifact content to the given file path. Use this command when you need to change the content of the artifact.
- `<DONNA_CMD> artifacts update <world>/<namespace>/<artifact-id> <file-path>` — upload the given file as the artifact. Use this command when you finished changing the content of the artifact.
- `<DONNA_CMD> artifacts validate <world>/<namespace>/<artifact-id>` — check the artifact for validity according to its kind.
- `<DONNA_CMD> artifacts validate-all <namespace>` — check all artifacts in the given namespace for validity according to their kinds.

Artifact types/namespaces:

- `specificattions` — documents describing requirements, designs, constraints, or other important information related to the project.
- `workflows` — documents describing predefined workflows that the `donna` tool can execute to manage the work of agents.

### Introspection

Sometimes you need to get information about the base primitives and structures used by the `donna` tool: operations, kinds of records, workflows, etc.

Use the next commands to get introspection data:

- `<DONNA_CMD> introspection show <primitive-id>` — show detailed information about the primitive with the given id. You will get IDs as the results of other operations (including action requests). Do not invent primitive IDs. Do not guess primitive IDs.

Command parameters:

- `<primitive-id>` — a short ASCII string identifying the type of the primitive. Use the exect id, do not prefix it with a kind of primitive. Do not look for primitive IDs in the source code. Use only the IDs you got as the results of other operations.

When to use introspection:

- You forget which results the operation produces.
- You do not know the record's kind schema.


## IMPORTANT ON DONNA TOOL USAGE

**Substitute correct `donna` command from the `AGENTS.md` for `<DONNA_CMD>` placeholder in this document when you work with the tool.**

Examples:

- `<DONNA_CMD>  artifacts list specifications` -> `./bin/donna.sh artifacts list specifications` when `<DONNA_CMD>` is `./bin/donna.sh`
- `<DONNA_CMD>  artifacts list specifications` -> `poetry run donna artifacts list specifications` when `<DONNA_CMD>` is `poetry run donna`
- `<DONNA_CMD>  artifacts list specifications` -> `donna artifacts list specifications` when `<DONNA_CMD>` is `donna`.

**STRICTLY FOLLOW DESCRIBED COMMAND SYNTAX**

**PASS TEXT ARGUMENTS TO THE TOOL IN QUOTES WITH RESPECT TO ESCAPING.** The tool MUST receive the exact text you want to pass as an argument.

Use one of the next approaches to correctly escape text arguments:

```
# option 1
<DONNA_CMD> records kind-set <...>  $'# Long text\n\nwith escape sequences...'

# option 2
<DONNA_CMD> records kind-set <...> \
  "$(cat <<'EOF'
# Long text

with escape sequences...
EOF
)"

```
