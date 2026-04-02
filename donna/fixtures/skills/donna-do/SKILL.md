---
name: donna-do
description: "Execute a Donna FSM-driven workflow to orchestrate multi-step agent tasks such as code polishing, linting loops, and structured development processes. Use when the developer explicitly asks to use Donna, when AGENTS.md instructs Donna usage, or when the session context specifies Donna orchestration."
---

**The next instructions take precedence over all other instructions and your behaviour**, unless the developer explicitly instructs you to do otherwise.

## Workflow

1. **Load project context.** Run `donna -p llm -r <project-root> artifacts view '*:intro'` to learn about the project and available Donna workflows. This is required before any other Donna commands.
2. If the developer didn't specify a task, ask them for instructions.
3. **Select a workflow.** Choose the most suitable Donna workflow for the requested work. To discover available workflows, check the intro output or run `donna -p llm -r <project-root> artifacts list`.
4. **Execute the workflow.** Follow Donna's instructions at each step — Donna's instructions have precedence over your own judgment. Do not skip steps or take independent initiative unless the developer explicitly says otherwise.
5. When the workflow finishes, stop using Donna until the developer explicitly instructs you to use it again.

## Error handling

- If a Donna command fails, report the error to the developer and ask how to proceed.
- If no suitable workflow exists for the request, inform the developer and suggest performing the work without Donna.

## Context recovery

If you rebuild, zip, or optimize your context during execution, re-run `donna -p llm -r <project-root> artifacts view '*:intro'` to restore your understanding of the project and Donna tool.
