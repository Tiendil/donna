### Migration

- Donna-owned command error cells now use stderr for human and LLM output; automation error cells remain on stdout. Error batches preserve diagnostic order and use shared batch framing. Python callers inside `command_context` must replace `CommandContext.write_errors` with `Err(errors).unwrap()` for nonempty error lists, allowing the context to journal, report, and terminate through the shared handler.

- Donna-owned environment errors now exit with the shared default status `3` instead of `0`, including artifact and workflow validation failures. Update scripts that previously treated these error cells as successful commands; diagnostic content and stream routing are unchanged.

- Shared `InvalidArguments` errors returned during command execution now exit with status `1` instead of the generic shared-error status `3`. Exit status comes from each error class; lists use the highest declared code.

- Successful `donna init` output now uses `Configuration created.` and includes the resolved configuration file path in `path` metadata in every protocol. Update integrations that match the previous success text; automation consumers can read `path` directly.

- Python integrations must register version commands through `llm_tool_cli.cli.commands.version.register_version_command`; `donna.cli.commands.version` is removed. Application setup registers Donna's version command directly.

- Python integrations must register skill commands through `llm_tool_cli.cli.commands.skills.register_skill_command`; `donna.cli.commands.skills` is removed. Application setup registers Donna's skill command directly.

- Python integrations that bypass CLI `main()` must initialize `llm_tool_cli.core.settings` with `ToolLabel("DONNA")` before cell output or argument parsing. Tests can request `isolated_settings` from `llm_tool_cli.core.tests.fixtures` before initializing the label; pytest-mock restores prior settings afterward. Remove `tool_label` arguments from shared sequence rendering and writing.

- Invalid `--protocol` values now produce an LLM `invalid_arguments` error cell on stderr and exit with status `1`, replacing Typer text and exit status `2`. Update scripts that depend on the previous diagnostic or exit status.

- Replace `donna.cli.utils.global_options` with `llm_tool_cli.cli.context.get_global_options`. Store options through `set_global_options` instead of the removed `GLOBAL_OPTIONS_CONTEXT_KEY`.

- Pass `llm_tool_cli.paths.ProjectConfigPath` to `initialize_workspace` in Python integrations. Omitting the path now selects `donna.toml` in the current working directory.

- `donna skill` now defaults to LLM cell output. Use `donna -p human skill` for human output. Python callers must import `GlobalOptions` from `llm_tool_cli.cli.entities`, use `ProjectConfigPath` for its `config_path`, and call `protocol_for(command_name)` to resolve an unspecified protocol.

- Result-unwrapping payloads must be lists of environment errors. Standalone errors and non-list iterables are no longer normalized by the CLI; malformed payloads propagate as the original `UnwrapError` without diagnostic output.

- Starter-template read failures now use shared `config_template_unreadable` diagnostics and exit with status `2` instead of `0`. Human and LLM diagnostics move to stderr; automation remains on stdout. Context uses `path`, `template`, and `reason` instead of `config_path` and `details`. Import `llm_tool_cli.config.errors.TemplateUnreadable` instead of the removed `donna.workspaces.errors.ConfigCreateFailed` and `WorkspaceConfigError`.

- Replace local `donna.skills.load_skill_text(document)` calls with `llm_tool_cli.skills.load_skill_text(package="donna.skills", document=document.value)` and handle its `Result[str]`. The local loader module and re-export are removed. Skill read failures now emit `skill_unreadable` error cells and exit with status `3`; human/LLM diagnostics use stderr and automation uses stdout.

- `donna version` now emits a version cell in the selected protocol instead of a bare version line. Scripts should use `donna -p automation version` and read the JSON record's `version` field; `id` is generated and `content` is null.

- All environment errors now use the shared `EnvironmentErrorCell` from `llm_tool_cli.protocol.logic_cells`. Donna-specific error kinds become `error`; metadata uses `code` instead of `error_code` and includes `type = error`. Custom introductory prefixes disappear; typed diagnostic context is serialized through the shared contract, including optional null fields. Corrective guidance remains in content and is now also included for shared errors. Stream routing, exit categories, and journal behavior are unchanged.
- Remove `cell_kind`, `cell_media_type`, and `content_intro()` from custom Donna error classes. Error classes retain codes, messages, corrective guidance, and typed context. Use shared cell projection instead of the removed error-node and local error-cell `content` and `meta` helpers.

- Shared errors now use ordinary cell framing in human and LLM output. Automation gains a generated `id` and moves formatted diagnostic text from `message` to `content`. Codes, diagnostic context, stderr/stdout routing, and exit categories remain unchanged.

- Construct Donna domain-result logic cells or shared content logic cells for generic messages, and pass them to `CliEmitter` or shared `protocol.rendering.render_cells(cells, protocol=...)`. All environment errors use the shared `protocol.cell_shortcuts.environment_error(error)` or `EnvironmentErrorCell(error=error)`. The separate `render_error` and `CliEmitter.emit_error` paths are removed; cell emission accepts `stderr=True` when needed. Journal formatters remain in `donna.protocol.journal_formatters` and use `get_journal_formatter` in `donna.protocol.modes`.
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

- Use shared automation payload extraction in the version test, validating generated UUID4 cell IDs and preserving parsed records.

- Use the shared automation error-cell assertion in CLI tests, retaining local output parsing, journal filtering, and application-specific checks.

- Delegate root global-option registration and storage to `llm_tool_cli.cli.application.create_app`, removing the local callback while preserving application startup, CLI options, defaults, help, and completions.

- Inherit invocation-option retrieval, protocol selection, and command cell writing from `llm_tool_cli.cli.context.CommandContext`, retaining Donna's workspace setup, runtime emitter, journaling, and cleanup.

- Route collected artifact validation errors through the command context so every diagnostic follows its journal policy before shared reporting and termination.

- Use the shared command error context manager and explicit reporter, retaining local workspace setup, error journaling, and runtime cleanup while unifying diagnostic streams.

- Delegate error exit-code selection to `llm_tool_cli` and inherit its default on Donna's environment-error root, preserving diagnostic order, streams, journaling, and cleanup.

- Emit the shared configuration-creation success cell after workspace initialization completes.

- Delegate complete configuration-file initialization to `llm_tool_cli`, preserving starter contents, subsequent workspace loading and installation, and CLI output and failures.

- Adopt the shared `InvalidArguments` diagnostic through protocol-option parsing, preserving LLM error cells, diagnostic fields, stderr routing, and exit status `1`.

- Delegate the complete version command to `llm_tool_cli`, preserving installed package lookup, output protocols, configuration independence, and exit behavior. Use common version help text.

- Use shared application construction with `-h` and `--help` at the root and subcommand levels, retaining shell completion options. Delegate the entire skill command to `llm_tool_cli`, preserving Donna's documents, output protocols, and read-failure behavior.

- Use the shared `core.tests.fixtures.isolated_settings` pytest fixture for test isolation; production settings no longer provide a scoped override.

- Initialize the shared `DONNA` tool label once at CLI startup and use it for all cell output, including early argument diagnostics. Use the shared `ProtocolOption` annotation without repeating labels.

- Delegate protocol option parsing and help to `llm_tool_cli`, preserving shared defaults and accepted values.

- Use shared `--config` parsing from `llm_tool_cli`. Directory and unreadable paths now reach configuration operations and their shared error cells; `skill` and `version` ignore unusable configuration paths.

- Obtain Typer through `llm_tool_cli` and upgrade the locked version from 0.20.1 to the shared 0.25.1 version.

- Delegate Typer context storage and retrieval of global options to `llm_tool_cli`, preserving CLI behavior and invocation isolation.

- Delegate initialization target selection and resolution to `llm_tool_cli`, preserving explicit paths, current-directory defaults, and the rule against upward discovery.

- Delegate global CLI options and protocol-default selection to `llm_tool_cli`, preserving explicit protocol overrides and configuration path handling.

- Recover unwrapped errors through the shared `UnwrapError.errors` accessor and remove local payload extraction, preserving error ordering, streams, exit categories, journaling, and context cleanup for valid failures.

- Delegate starter-template reading and exclusive configuration creation to the shared library, preserving templates, target selection, workspace loading, and successful output.

- Load skill documents directly through the shared library, preserving packaged content, document selection, and successful output while unifying read-failure diagnostics.

- Use the shared version-cell shortcut for every output protocol, preserving configuration-free execution and exit status zero on success.

- Delegate cell emission to the shared writer, preserving cell framing, batch context, Unicode, stream routing, and separate journal formatting.

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
