# Instructions for the AI Agents

This document provides instructions and guidelines for the AI agents working on this project.

Every agent MUST follow the rules and guidelines outlined in this document when performing their work.

## Points of interests

- `./.agents/` — a directory containing project-specific agent instructions and templates.
- `./.agents/TOOLS.md` — a list of AI tools available specifically for this project.
- `./.agents/RULES.md` — extra rules and permissions for agents.
- `./specs/` — a directory containing project specifications and design documents.
- `./specs/README.md` — an overview of the project specifications.
- `./donna/` — a directory containing source code of `donna` tool for managing agent's work. It is developed in parallel with the project.
- `~/.my-local-agents/` — a directory containing global agent instructions, templates and tools that can be used in any project.
- `~/.my-local-agents/TOOLS.md` — a list of AI tools available globally on this system.

`.agents` directory MUST be only in the root of the project.

## Project Overview

The project — **Clio** — is a deterministic game logic engine designed specifically and only to implement game logic.

The core features (the goal of the development) of Clio include:

- Fully deterministic & idempotent behavior:
  - Uses only integers and fixed-point arithmetic.
  - All random values are generated from a seed.
- Fully configurable game rules/logic.

Note:

- Clio core functionality does not contain rendering, audio, input or any other non-game-logic related features.
- Clio side projects or examples may contain such features, but the core engine is strictly focused on game logic.

Currently, Clio top-level structure consists of the following components:

- `./clio` — the engine and related tools.
- `./clio/clio-engine` — library — the core deterministic game logic engine.
- `./clio/clio-cli` — executable — a command-line interface for running and testing Clio games.
- `./clio/clio-dev-server` — library — a development server implementation that is used by `clio-cli` and `overseer`.
- `./clio/clio-logic` — library — a test game logic implementation built on top of `clio-engine`, used by `clio-cli` for demonstration and testing.
- `./clio-data` — configuration and data for Clio game, implemented by `clio-logic`.
- `./overseer` — a web-based (frontend) debug tool for Clio games.

The primary idea behind components: we run the game via `clio-cli` and can connect to it via `overseer` for debugging and visualization.

There are some old components related to Godot, IGNORE them.

## Environment

- Clio is implemented in Rust.
- Overseer is implemented in TypeScript and Vue.js.

Clio is in the early stages of development => there are no tests and you do not need to write tests for now.

To test that Clio works correctly use the next commands from the root of the project:

```
cd ./clio
cargo run -p clio-cli -- --steps 10 --stop
```

If the CLI compiles and finishes without errors, Clio works correctly.

The deterministic behavior hasn't been fully implemented yet, so, in case of EXECUTION errors, run the above command multiple times to ensure that the same error occurs consistently. If some execution are successful, count errors as false positives.

## Development context

- When you are working on the specific part of the project, you take into account `AGENTS.md` from each level of the project hierarchy and the supplementary rules in `./.agents/RULES.md`.
- Example: when you are working on `./clio/clio-engine/src/some_module.rs`, you take into account `AGENTS.md` from:
  - `./AGENTS.md`
  - `./clio/AGENTS.md`
  - `./clio/clio-engine/AGENTS.md`
  - `./clio/clio-engine/src/AGENTS.md`
- If you need to create a document of any kind, you check for the template in the `./.agents/templates/` folder of the project root.
- You always work on the specific story assigned to you, that is managed by the `donna` tool.
- If developer asked you to do something and you have no story, you create a story with the `donna` tool.
- If you have a story, you MUST keep all the information about it in your memory. Ask `donna` tool for the story details when you forget something.

## Stories

Story is a semantically consistent unit of work assigned to you by the developer.

All work in the context of story is managed by the `donna` tool.

You create story by specifying:

- `SLUG` is a short ASCII string identifying the story with dash separators.
- `DESCRIPTION` is a short text describing what needs to be done, that the developer provides you.

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

- If the developer asked you to do something and specified a story ID and story slug, you MUST call `./bin/donna.sh story continue <story-id> <story-slug>` to get your instructions on what to do next.
- If the developer asked you to do something and did NOT specified a story ID and story slug, you MUST ask developer if you need to create a story for it first. If developer says YES, you MUST create a story. Then you MUST start working on the created story.

### Working with artifacts

Artifact is any file or document related and created specifically to a story:

- Story description is an artifact.
- List of work risks is an artifact.
- Files with source code of the project IS NOT an artifact.
- Compiled binaries of the project IS NOT an artifact.

Use the next commands to work with artifacts related to your story:

- `./bin/donna.sh artifacts list <story-id>` — list all artifacts related to the story.
- `./bin/donna.sh artifacts write <story-id> <artifact-id> <content-type> <description> <content>` — create or update a TEXT artifact related to the story.
- `./bin/donna.sh artifacts read <story-id> <artifact-id>` — outputs the content of the TEXT artifact related to the story.
- `./bin/donna.sh artifacts has <story-id> <artifact-id>` — checks if the artifact related to the story exists.
- `./bin/donna.sh artifacts copy-into-sotry <story-id> <artifact-id> <content-type> <description> <path>` — create or update a BINARY artifact related to the story from the specified file path.
- `./bin/donna.sh artifacts copy-from-story <story-id> <artifact-id> <path>` — copies the BINARY artifact related to the story into the specified file path.

Command parameters:

- `<story-id>` — the story id you got when you created or continued the story.
- `<artifact-id>` — a slug identifying the artifact within the story.
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
