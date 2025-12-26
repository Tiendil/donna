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
  2. List all possible workflows with command `./bin/donna.sh stories list-workflows`.
  3. Choose the most appropriate workflow for the story you are going to work on or ask the developer if you are not sure which workflow to choose.
  4. Start working on the story by calling `./bin/donna.sh stories start-workflow <story-id> <workflow-id>`.
  5. The `donna` tool will output descriptions of all operations it performs to complete the story.
  6. The `donna` tool will output **action requests** that you MUST perform. You MUST follow these instructions precisely.
- When you done doing your part, you call `./bin/donna.sh stories action-request-completed <action-request-id> <action-request-result>` to report that you completed the action request. List of values `<action-request-result>` will be in the **action request** description.
- After you report the result:
  1. The `donna` tool will output what you need to do next.
  2. You repeat the process until the story is completed.

### Starting work on a story

- If the developer asked you to do something and specified a story slug, you MUST call `./bin/donna.sh story continue <story-id>` to get your instructions on what to do next.
- If the developer asked you to do something and did NOT specified a story ID and story slug, you MUST ask developer if you need to create a story for it first. If developer says YES, you MUST create a story. Then you MUST start working on the created story.

### Working with artifacts

Artifact is any file or document related and created specifically for a story:

- Story description is an artifact.
- List of work risks is an artifact.
- Files with source code of the project IS NOT an artifact.
- Compiled binaries of the project IS NOT an artifact.

Use the next commands to work with artifacts related to your story:

- `./bin/donna.sh artifacts list <story-id>` — list all artifacts related to the story.
- `./bin/dinna.sh artifacts create <story-id> <artifact-kind> <artifact-id> <content-type> <description>` — create a new artifact related to the story. The new artifact will be empty.
- `./bin/donna.sh artifacts text write <story-id> <artifact-id> <content>` — create or update a `text` artifact related to the story.
- `./bin/donna.sh artifacts text read <story-id> <artifact-id>` — outputs the content of the `text` artifact related to the story.
- `./bin/donna.sh artifacts has <story-id> <artifact-id>` — checks if the artifact related to the story exists.
- `./bin/donna.sh artifacts copy-into-sotry <story-id> <artifact-id> <path>` — create or update a BINARY artifact related to the story from the specified file path.
- `./bin/donna.sh artifacts copy-from-story <story-id> <artifact-id> <path>` — copies the BINARY artifact related to the story into the specified file path.

Supported artifact kinds:

- `text` — text-based artifact. You can read and write its content as text.

Command parameters:

- `<story-id>` — the story id you got when you created or continued the story.
- `<artifact-kind>` — the kind of the artifact. Supported kinds are listed above.
- `<artifact-id>` — a identifier for the artifact within the story. **ALWAYS USE THE EXECT FULL ID WHEN REFERENCING AN ARTIFACT.** Including file extension if any.
- `<content-type>` — classic MIME type of the artifact content, e.g. `text/markdown`, `text/plain`, `application/json`, etc.
- `<description>` — a short text describing what the artifact is about / what it contains.
- `<content>` — the actual TEXT content of the artifact.
- `<path>` — the file path to read from or write to.

## IMPORTANT ON DONNA TOOL USAGE

**RUN `./bin/donna.sh` TO ACCESS THE `donna` TOOL**

**PASS TEXT ARGUMENTS TO THE TOOL IN QUOTES WITH RESPECT TO ESCAPING.** The tool MUST receive the exact text you want to pass as an argument.

Use one of the next approaches to correctly escape text arguments:

```
# option 1
./bin/donna.sh artifacts write <...>  $'# Long text\n\nwith escape sequences...'

# option 2
./bin/donna.sh artifacts write <...> \
  "$(cat <<'EOF'
# Long text

with escape sequences...
EOF
)"

```
