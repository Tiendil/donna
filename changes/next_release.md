
### Changes

- Added the `donna.lib.path(...)` workflow directive for rendering project file references in agent-facing instructions.
  - Relative paths are resolved from the workflow file that contains the directive.
  - By default, paths render as root-anchored project paths such as `@/specs/behavior/file_paths.md`.
  - Use `mode="absolute"` when an instruction needs a host filesystem path.
- Generalized Donna's project path handling so root-anchored paths can point to any file or directory inside the project, not only workflow artifacts.
- Updated the built-in workflow documentation and RFC workflows to use `donna.lib.path(...)` for stable project file references.
