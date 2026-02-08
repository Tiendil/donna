### Changes

- Improved template for RFC draft artifact — added the `kind` config to the header section.
- Added workspace skill synchronization for `donna workspaces init` and `donna workspaces update`.
  - Added `donna workspaces update` command.
  - Added `--no-skills` and `--no-skils` options for `init` and `update` to skip skill updates.
  - Added Donna skill fixture copy from `donna/fixtures/skills/donna` to `<project-root>/.agents/skills/donna`.
