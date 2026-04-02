---
name: donna-start
description: "Initialize a new Donna session for FSM-driven workflow orchestration, enabling structured multi-step task execution such as code polishing, linting, and development loops. Use when the developer explicitly asks to start a Donna session or begin Donna-managed work."
---

## Workflow

1. **Load project context.** Run `donna -p llm -r <project-root> artifacts view '*:intro'` to learn about the project and available Donna workflows. This is required before starting a session.
2. **Start the session.** Run `donna -p llm -r <project-root> sessions start` to initialize a new Donna session.
3. Confirm to the developer: "I have started a new Donna session".
4. If the developer didn't specify a task, ask them for instructions.
5. **Select and run a workflow.** Choose the most suitable Donna workflow for the requested work. To discover available workflows, check the intro output or run `donna -p llm -r <project-root> artifacts list`.
6. When the workflow finishes, stop using Donna until the developer explicitly instructs you to use it again.

## Error handling

- If `sessions start` fails, report the error to the developer and ask how to proceed.
- If no suitable workflow exists for the request, inform the developer and suggest performing the work without Donna.
