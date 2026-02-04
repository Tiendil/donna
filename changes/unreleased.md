## Changes

- Support relative filesystem world paths in workspace configs.
    - Default workspace configs emit relative filesystem world paths for project and session worlds.
    - Filesystem world resolution expands `~` and resolves relative paths against the workspace root.
- Updated instructions to make session starting/reseting process dependent on a developer, not an agent.
