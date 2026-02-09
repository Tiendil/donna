### Changes

- Improved template for RFC draft artifact — added the `kind` config to the header section.
- Added `donna workspaces update` command to update project workspace after Donna is updated.
- Added workspace skill synchronization for `donna workspaces init` and `donna workspaces update`.
  - Both commands now install donna skills `donna-do`, `donna-start` and `donna-stop` into `.agents/skills/` directory.
  - Added `--no-skilks` option for `init` and `update` to skip skill updates.
- Added stdin and extension-aware updates for `donna artifacts update`.
  - Added `--extension` option to explicitly select artifact source extension.
  - Added `-` stdin input support.
