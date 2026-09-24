### Migration

- Import `BaseEntity` from `llm_tool_cli.core.entities` instead of `donna.core.entities`.
- Import `Result` and its helpers from `llm_tool_cli.core.result`, and `EnvironmentErrors` and `EnvironmentErrorsProxy` from `llm_tool_cli.core.errors`; Donna retains its presentation-specific environment-error extension.
- Custom internal-error subclasses must define `message_template` instead of `message`. Read the formatted diagnostic from `message` and structured context from `details` instead of `error_message()` and `arguments`; exception strings now contain the formatted message without a class-name prefix.

- Configuration failures now use shared `llm-tool-cli` diagnostic codes and exit with status `2`; other expected shared errors exit with status `3`. Automation consumers must read `type`, `code`, `message`, `path`, and `reason` from the shared record instead of Donna error-cell fields. Human and LLM shared diagnostics now go to stderr. Donna-owned errors retain their existing result and cell behavior.
- Missing configuration during upward discovery now reports `config_not_found` and exits with status `2` instead of returning a Donna error cell with status `0`.
- Python callers must use shared `load_config` followed by `construct_workspace` instead of `load_workspace`; `initialize_runtime` and shared configuration operations return `Result` values.

### Changes

- Use the shared entity base for models and environment errors, preserving entity copying, JSON conversion, and string normalization.
- Adopt `Result`, the environment-error foundation, and the callback proxy from `llm-tool-cli`; expected shared failures propagate as values alongside Donna diagnostics.
- Derive Donna internal exceptions from the shared internal-error base so one hierarchy covers local failures and shared technical exceptions.

- Support TOML 1.1 in project configuration and workflow blocks through the shared `llm-tool-cli` dependency.
- Remove the unused direct `tomli-w` runtime dependency.
- Call shared configuration discovery, path resolution, TOML reading, and starter-file creation directly from workspace initialization.
- Load and validate configuration models through the shared library, which now provides the Pydantic dependency.
- Prevent configuration initialization from overwriting a file created concurrently.
- Propagate expected shared errors through results in workspace loading and initialization, preserving their shared diagnostic records at the CLI boundary.
- Select configuration paths and expand home-directory markers through the shared library before constructing workspaces.
