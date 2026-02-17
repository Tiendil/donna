
### Changes

- gh-35 — Implemented `donna journal` CLI subcommands for writing and viewing session journal.
  - Added journaling of all significant actions and events.
  - Removed `single_mode` formatting option from protocol formatter APIs.
  - Command `donna artifacts validate` now accepts an artifact pattern instead of a single artifact id.
  - Removed `donna artifacts validate-all` command.
- gh-41 — Added `Design` step into RFC workflow.
  - Added `donna:rfc:specs:design` and `donna:rfs:work:design`.
  - Updated `donna:rfc:work:do` to include `design` step between `create` and `plan`.
  - Renamed `donna:rfc:work:create` to `donna:rfc:work:request`.
- gh-58 — Unified error handling in `donna.machine.sessions` and `donna.cli.*` modules.
