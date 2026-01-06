# Instructions for the AI Agents

This document provides instructions and guidelines for the AI agents working on this project.

Every agent MUST follow the rules and guidelines outlined in this document when performing their work.

## Points of interests

- `./.agents/` — a directory containing project-specific agent instructions and templates.
- `./donna/` — a directory containing source code of project — `donna` CLI tool.

`.agents` directory exists only in the root of the project.

## Project Overview

`Donna` is a CLI tool that helps manage the work of AI agents like Codex.

It is designed to to invert control flow: instead of agents deciding what to do next, the `donna` tells agents what to do next by following predefined workflows.

The core idea is that most of high-level workflows are more algorithmic than it may seem at first glance. For example, it may be difficult to fix a particular type issue in the codebase, but the overall process of polishing the codebase is quite linear:

1. Ensure all tests pass.
2. Ensure the code is formatted correctly.
3. Ensure there are no linting errors.
4. Go to the step 1 if you changed something in the process.
5. Finish.

We may need coding agents on the each step of the process, but there no reason for agents to manage the whole grooming loop by themselves — it take longer time, spends tokens and may lead to confusion of agents.

## Implementation details

- Donna is implemented in Python.

## Development

- You always work on the specific story assigned to you, that is managed by the `donna` tool.
- If developer asked you to do something and you have no story, you create a story with the `donna` tool.
- If you have a story, you MUST keep all the information about it in your memory. Ask `donna` tool for the story details when you forget something.

## Stories

Story is a semantically consistent unit of work assigned to you by the developer.

All work in the context of story is managed by the `donna` tool.

You create story by specifying `story-slug` — a short ASCII string identifying the story with dash separators.

### Story workflow

- You create stories by calling `./bin/donna.sh stories create <story-slug>`.
- After you create a story:
  1. The `donna` tool will output a story id, use it to interact with the tool in the future.
  2. List all possible workflows with command `./bin/donna.sh workflows list`.
  3. Choose the most appropriate workflow for the story you are going to work on or ask the developer if you are not sure which workflow to choose.
  4. Start working on the story by calling `./bin/donna.sh workflows start <story-id> <workflow-id>`.
  5. The `donna` tool will output descriptions of all operations it performs to complete the story.
  6. The `donna` tool will output **action requests** that you MUST perform. You MUST follow these instructions precisely.
- When you done doing your part, you call `./bin/donna.sh stories action-request-completed <action-request-id> <action-request-result>` to report that you completed the action request. List of values `<action-request-result>` will be in the **action request** description.
- After you report the result:
  1. The `donna` tool will output what you need to do next.
  2. You repeat the process until the story is completed.

### Starting work on a story

- If the developer asked you to do something and specified a story slug, you MUST call `./bin/donna.sh story continue <story-id>` to get your instructions on what to do next.
- If the developer asked you to do something and did NOT specified a story ID and story slug, you MUST ask developer if you need to create a story for it first. If developer says YES, you MUST create a story. Then you MUST start working on the created story.

### Working with records

A record is a named collection of structured data of different kinds.

- There can be multiple kinds of data attached to a single record.
- Records are exist only in the context of a story.
- Kinds of records are preconfigured in the `donna` tool.
- You generally will get a specification of a scheme for a particular kind of record when you are asked to create or update it.

Donna can ask you to create and manage records related to your story.

Examples of record kinds:

- Plain text record with media type is a kind of record.
- A fixed set of fields with specific types, like "issue tracker ticket" is a kind of record.
- Files with source code of the project IS NOT a kind of record.
- Compiled binaries of the project IS NOT a kind of record.

Use the next commands to work with records related to your story:

- `./bin/donna.sh records list <story-id>` — list all records related to the story.
- `./bin/donna.sh records create <story-id> <description>` — create a new record without any kinds of data attached.
- `./bin/donna.sh records delete <story-id> <record-id>` — delete the record and all its data.
- `./bin/donna.sh records kind-set <story-id> <record-id> <record-kind> <json-data>` — set data of a particular kind for the record. Data is passed as JSON string.
- `./bin/donna.sh records kind-get <story-id> <record-id> <record-kind>*` — get data of a particular kind(s) for the record.
- `./bin/donna.sh records kind-delete <story-id> <record-id> <record-kind>*` — delete data of a particular kind(s) for the record.

Command parameters:

- `<story-id>` — the story id you got when you created or continued the story.
- `<record-id>` — a short ASCII string identifying the record with dash separators. May be a unique slug like `story-description-from-developer` or a parameterized string like `issue-{uid}` where `{uid}` will be replaced with a unique identifier generated by the `donna` tool. Parametrized strings are allowed only when you create a new record.
- `<record-kind>` — a short ASCII string identifying the kind of record with dash separators.
- `<description>` — a short text description of the record.
- `<json-data>` — a JSON string with data of the particular kind.

### Working with specifications

A specification is a document describing requirements, designs, constraints, or other important information related to the project.

Use the next commands to work with specifications:

- `./bin/donna.sh specifications list` — list all specifications.
- `./bin/donna.sh specifications get <specification-id>` — get the content of the specification.

Command parameters:

- `<specification-id>` — a short ASCII string identifying the specification with `/` separators between sections and dash separators between words, e.g. `name/space/specification-id`.

### Introspection

Sometimes you need to get information about the base primitives and structures used by the `donna` tool: operations, kinds of records, workflows, etc.

Use the next commands to get introspection data:

- `./bin/donna.sh introspection show <primitive-id>` — show detailed information about the primitive with the given id. **USE IT ONLY WHEN YOU HAVE NO REQUIRED INFO ON THE PRIVITIVE**.

## IMPORTANT ON DONNA TOOL USAGE

**RUN `./bin/donna.sh` TO ACCESS THE `donna` TOOL**

**STRICTLY FOLLOW DESCRIBED COMMAND SYNTAX**

**PASS TEXT ARGUMENTS TO THE TOOL IN QUOTES WITH RESPECT TO ESCAPING.** The tool MUST receive the exact text you want to pass as an argument.

Use one of the next approaches to correctly escape text arguments:

```
# option 1
./bin/donna.sh records kind-set <...>  $'# Long text\n\nwith escape sequences...'

# option 2
./bin/donna.sh records kind-set <...> \
  "$(cat <<'EOF'
# Long text

with escape sequences...
EOF
)"

```
