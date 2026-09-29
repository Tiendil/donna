### Migration

- All environment errors now use the shared `EnvironmentErrorCell` from `llm_tool_cli.protocol.logic_cells`. Donna-specific error kinds become `error`; metadata uses `code` instead of `error_code` and includes `type = error`. Custom introductory prefixes disappear; typed diagnostic context is serialized through the shared contract, including optional null fields. Corrective guidance remains in content and is now also included for shared errors. Stream routing, exit categories, and journal behavior are unchanged.
- Remove `cell_kind`, `cell_media_type`, and `content_intro()` from custom Donna error classes. Error classes retain codes, messages, corrective guidance, and typed context. Use shared cell projection instead of the removed error-node and local error-cell `content` and `meta` helpers.

- Shared errors now use ordinary cell framing in human and LLM output. Automation gains a generated `id` and moves formatted diagnostic text from `message` to `content`. Codes, diagnostic context, stderr/stdout routing, and exit categories remain unchanged.

- Construct Donna domain-result logic cells or shared content logic cells for generic messages, and pass them to `CliEmitter` or shared `protocol.rendering.render_cells(cells, protocol=..., tool_label=...)`. All environment errors use the shared `protocol.cell_shortcuts.environment_error(error)` or `EnvironmentErrorCell(error=error)`. The separate `render_error` and `CliEmitter.emit_error` paths are removed; cell emission accepts `stderr=True` when needed. Journal formatters remain in `donna.protocol.journal_formatters` and use `get_journal_formatter` in `donna.protocol.modes`.
- Node views and runtime session operations return logic cells. Read domain fields such as `artifact_id` directly; obtain output content and metadata through `cell.render(protocol)` or shared sequence rendering. Import Donna's domain cell types from `donna.protocol`. Call node views, message shortcuts, and `runtime.sessions.clear` without `cell_type`. Emitters accept `Iterable[LogicCell]` through `emit_cells`; replace `emit_cell(cell)` with `emit_cells([cell])` in callers and custom emitters. Emitters no longer expose a `cell_type` property. `CliEmitter` retains the selected protocol for shared rendering.
- Artifact Markdown construction now belongs to artifact and section logic cells; use node views and cell projection instead of the removed machine `markdown_blocks` methods.
- Import `cell_shortcuts` from `llm_tool_cli.protocol`, or its helpers directly from `llm_tool_cli.protocol.cell_shortcuts`, instead of `donna.protocol`.
- Import `ContentCell` from `llm_tool_cli.protocol.logic_cells` and `LogicCell` from `llm_tool_cli.protocol.logic_cells.base` for application construction and emission. Metadata helpers and low-level `OutputCell` and `RenderContext` types live in `llm_tool_cli.protocol.output_cells.base`; `ContentWithoutMediaType` belongs to the shared protocol internal-error hierarchy in `llm_tool_cli.protocol.errors`.
- Import `Protocol` from `llm_tool_cli.protocol` instead of `donna.protocol.modes.Mode`. Replace `instant_output` with `write_output` and supply decoded text with explicit terminators; writing no longer adds newlines, forces UTF-8 bytes, or flushes each write. Use `to_jsonl(record.model_dump(mode="json"))` instead of `serialize_record` when a journal JSON line is needed.
- Import `UntrustedPath` directly from `llm_tool_cli.paths` instead of `donna.domain.paths`.
- Import `resolve_project_path` directly from `llm_tool_cli.paths` instead of `donna.workspaces.paths`; home-expansion failures now return `path_resolution_failed` diagnostics.
- Import `normalize_path` directly from `llm_tool_cli.paths` in Python integrations.
- Replace `donna.workspaces.paths.normalize_existing_path` with `llm_tool_cli.paths.project_path_id_from_filesystem` in Python integrations.
- Import `ProjectRootPath` and `resolve_project_root` from `llm_tool_cli.paths`; root resolution now returns `Result[ProjectRootPath]`. Expected root-resolution failures use `path_resolution_failed` diagnostics and exit with status `3` instead of escaping as raw filesystem exceptions.
- Project-path normalization and resolution now return shared `Result` values instead of `None` on failure. Import `ProjectPathId` from `llm_tool_cli.paths` and use `normalize_project_path` instead of the removed `normalize_artifact_path` alias.
- Invalid project paths now report the shared `invalid_project_path` diagnostic with a `path` field and exit with status `3`, replacing Donna identifier error cells with status `0`. Human and LLM diagnostics use stderr; automation uses shared JSON Lines records. Artifact extension and section validation remain Donna-specific.

- Import `BaseEntity` from `llm_tool_cli.core.entities` instead of `donna.core.entities`.
- Import `Result` and its helpers from `llm_tool_cli.core.result`, and `EnvironmentErrors` and `EnvironmentErrorsProxy` from `llm_tool_cli.core.errors`; Donna retains its environment-error root for application classification.
- Annotate results as `Result[T]` instead of `Result[T, EnvironmentErrors]`; the shared result now always carries environment-error lists on failure.
- Custom internal-error subclasses must define `message_template` instead of `message`. Read the formatted diagnostic from `message` and structured context from `details` instead of `error_message()` and `arguments`; exception strings now contain the formatted message without a class-name prefix.

- Configuration failures now use shared `llm-tool-cli` diagnostic codes and exit with status `2`; other expected shared errors exit with status `3`. Automation consumers must read `id`, `content`, `type`, `code`, `path`, and `reason` from shared error cells instead of Donna-specific error metadata. Human and LLM shared diagnostics now go to stderr. Donna-owned errors retain their existing result, stream, and exit behavior while adopting the shared error-cell payload.
- Missing configuration during upward discovery now reports `config_not_found` and exits with status `2` instead of returning a Donna error cell with status `0`.
- Python callers must use shared `load_config` followed by `construct_workspace` instead of `load_workspace`; `initialize_runtime` and shared configuration operations return `Result` values.

### Changes

- Include shared `type = operation_succeeded` metadata in initialization, validation, and session success cells across all output protocols.

- Use the shared skill-document cell shortcut. Skill output now includes `type = skill` metadata in every protocol, including a `type` field in automation JSON Lines.

- Standardize runtime, CLI, and test emitters on `emit_cells` and remove the single-cell convenience method while preserving output batches and routing.

- Delegate all environment-error cells to the shared typed implementation, remove local presentation hooks, and retain Donna graph, journal, stream, and exit policies.

- Keep artifact, section, action-request, and session-status data in typed Donna logic cells, and retain structured errors in error cells. Build domain Markdown and metadata during projection while preserving domain cell output and journal behavior. Generic messages continue to use shared content cells.
- Delegate cell rendering and shared-error cell construction to `llm_tool_cli` while keeping journal formatting in Donna and preserving stream routing and exit behavior.
- Use shared message cell shortcuts, preserving existing cell kinds, content, and metadata behavior.
- Use the complete shared cell implementation and metadata helpers while preserving all existing output formats and cell construction behavior.
- Use shared output modes, compact JSON Lines serialization, and direct text writing while preserving Donna cells, diagnostic records, CLI defaults, and exit policies. Journal formatters now include their newline so emitted output remains unchanged.
- Delegate empty project-path rejection to the shared normalizer, including artifact-relative inputs; root-resolution failures take precedence over empty-input diagnostics.
- Use the shared `UntrustedPath` semantic type for filesystem inputs, preserving runtime path behavior.
- Use the shared project-path resolver directly for absolute path directives, preserving project containment and resolution diagnostics.
- Use shared mixed path normalization directly, preserving artifact-relative behavior and returning `path_resolution_failed` diagnostics for home expansion failures during normalization.
- Share filesystem-to-identifier conversion through `llm-tool-cli`, preserving artifact lookup behavior and resolution diagnostics.
- Convert resolved filesystem paths to canonical identifiers through `llm-tool-cli` directly, preserving public path results and diagnostics.
- Resolve root-anchored identifiers through `llm-tool-cli` directly, preserving path results and shared failure diagnostics.
- Use shared filesystem containment and resolved-path types; target resolution failures now return `path_resolution_failed` diagnostics with private causes instead of escaping as raw exceptions.
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
