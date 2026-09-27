### Migration

- Import `ProjectRootPath` and `resolve_project_root` from `llm_tool_cli.paths`; root resolution now returns `Result[ProjectRootPath]`. Expected root-resolution failures use `path_resolution_failed` diagnostics and exit with status `3` instead of escaping as raw filesystem exceptions.
- Project-path normalization and resolution now return shared `Result` values instead of `None` on failure. Import `ProjectPathId` from `llm_tool_cli.paths` and use `normalize_project_path` instead of the removed `normalize_artifact_path` alias.
- Invalid project paths now report the shared `invalid_project_path` diagnostic with a `path` field and exit with status `3`, replacing Donna identifier error cells with status `0`. Human and LLM diagnostics use stderr; automation uses shared JSON Lines records. Artifact extension and section validation remain Donna-specific.

- Import `BaseEntity` from `llm_tool_cli.core.entities` instead of `donna.core.entities`.
- Import `Result` and its helpers from `llm_tool_cli.core.result`, and `EnvironmentErrors` and `EnvironmentErrorsProxy` from `llm_tool_cli.core.errors`; Donna retains its presentation-specific environment-error extension.
- Annotate results as `Result[T]` instead of `Result[T, EnvironmentErrors]`; the shared result now always carries environment-error lists on failure.
- Custom internal-error subclasses must define `message_template` instead of `message`. Read the formatted diagnostic from `message` and structured context from `details` instead of `error_message()` and `arguments`; exception strings now contain the formatted message without a class-name prefix.

- Configuration failures now use shared `llm-tool-cli` diagnostic codes and exit with status `2`; other expected shared errors exit with status `3`. Automation consumers must read `type`, `code`, `message`, `path`, and `reason` from the shared record instead of Donna error-cell fields. Human and LLM shared diagnostics now go to stderr. Donna-owned errors retain their existing result and cell behavior.
- Missing configuration during upward discovery now reports `config_not_found` and exits with status `2` instead of returning a Donna error cell with status `0`.
- Python callers must use shared `load_config` followed by `construct_workspace` instead of `load_workspace`; `initialize_runtime` and shared configuration operations return `Result` values.

### Changes

- Use shared filesystem project-root resolution directly, preserving successful path behavior and propagating structured failures through path operations and CLI commands.
- Share lexical `@/` path normalization with `llm-tool-cli`, including artifact-relative paths, and propagate shared errors through CLI arguments and path directives. Filesystem resolution and symlink containment retain their existing behavior.
- Use the shared typed result predicate when treating invalid artifact paths as unavailable.

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
