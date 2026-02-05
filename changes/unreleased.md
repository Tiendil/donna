## Changes

- Add codespell to the polishing workflow.
    - Add `codespell` as a dev dependency.
    - Run codespell after Black with a fix step on failures.
- Support relative filesystem world paths in workspace configs.
    - Default workspace configs emit relative filesystem world paths for project and session worlds.
    - Filesystem world resolution expands `~` and resolves relative paths against the workspace root.
- Updated instructions to make session starting/resetting process dependent on a developer, not an agent.
- Filled README.md with detailed docs.
