Part of Donna functionality moved to the shared `llm_tool_cli` library to unify behavior among a family of LLM-oriented CLI tools (currently `donna` and `depmesh`). As a result, we introduced some behavior changes.

No changes are required in configuration files.

### Migration

Due to massive refactoring, it is difficult to list all changes that may affect existing scripts and integrations. The following list highlights the most important directions for migration:

- Some exit codes for errors have changed. You may need to validate scripts that check exit codes.
- Some error ids have changed. You may need to validate scripts that check error ids.
- All output now follows cell framing conventions. Use `automation` protocol if you need to parse output programmatically.

### Changes

- `llm_tool_cli` added as a dependency, part of Donna's functionality moved to this library. As the result, a lot of small behavior changes were introduced.
- Exit codes for expected command failures now: `1` for invalid arguments, `2` for configuration errors, and `3` for other environment errors.
- All output now follows cell framing conventions.
- All output now goes to stdout.
- Added support for TOML 1.1.
