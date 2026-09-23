### Migration

- Configuration failures now use shared `llm-tool-cli` diagnostic codes and exit with status `2`; other expected shared errors exit with status `3`. Automation consumers must read `type`, `code`, `message`, `path`, and `reason` from the shared record instead of Donna error-cell fields. Human and LLM shared diagnostics now go to stderr. Donna-owned errors retain their existing result and cell behavior.
- Missing configuration during upward discovery now reports `config_not_found` and exits with status `2` instead of returning a Donna error cell with status `0`.
- Python callers must use shared `load_config` followed by `construct_workspace` instead of `load_workspace`; `initialize_runtime` now returns a workspace directly instead of a `Result`.

### Changes

- Support TOML 1.1 in project configuration and workflow blocks through the shared `llm-tool-cli` dependency.
- Remove the unused direct `tomli-w` runtime dependency.
- Call shared configuration discovery, path resolution, TOML reading, and starter-file creation directly from workspace initialization.
- Load and validate configuration models through the shared library, which now provides the Pydantic dependency.
- Prevent configuration initialization from overwriting a file created concurrently.
- Propagate expected shared errors directly through workspace loading and initialization, preserving their shared diagnostic records at the CLI boundary.
- Select configuration paths and expand home-directory markers through the shared library before constructing workspaces.
