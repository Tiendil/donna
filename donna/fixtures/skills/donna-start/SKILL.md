---
name: donna-start
description: Start a new Donna session, do nothing else. Use this skill when the developer explicitly told you to use it.
---

1. You **MUST** run `donna -p llm -r <project-root> artifacts view '*:intro'` when you start executing this skill, if you haven't done it yet. This command provides an introduction to the project and the Donna tool.
2. Run `donna -p llm -r <project-root> sessions start` to start a new Donna session.
3. Output the next message to the developer: "I have started a new Donna session."
4. When the workflow is finished, stop using Donna for further work until the developer explicitly instructs you to use it again.
