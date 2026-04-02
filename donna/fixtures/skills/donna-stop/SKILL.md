---
name: donna-stop
description: "Stop Donna workflow orchestration and disable FSM-driven task execution. Use when the developer explicitly asks to stop, disable, or turn off Donna-managed workflows."
---

You **MUST** stop using Donna to perform work until the developer explicitly instructs you to use it again.

When Donna is stopped:

- Do not invoke any `donna` CLI commands.
- If a task would normally involve a Donna workflow, perform it directly using your own judgment instead.
- Resume Donna usage only when the developer explicitly instructs you to do so (e.g., via the `donna-start` or `donna-do` skills).
