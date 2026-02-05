### Changes
- Set default CLI protocol to be `human` when omitted.
- Refactored protocol and CLI initialization to use global config.
  - Moved protocol mode storage to workspaces config and update directives/formatting to read from global config.
  - Centralized runtime initialization in CLI application, remove subcommand callbacks and Typer context usage.
  - Workspace init now relies on global project root and tolerates pre-set project_dir during initialization.
