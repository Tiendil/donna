
### Changes

- gh-35 Added workflow for creating Design documents.
  - Added `donna:rfs:work:design` workflow by analogy to `donna:rfc:work:request`.
  - Added instructions to use `donna:rfc:specs:design` and default output artifact `session:design:<short-problem-related-identifier>`.
  - Fixed typo in `donna:rfc:specs:design` (`guidlines` -> `guidelines`).
- gh-35 Renamed RFC request workflow id.
  - Renamed the RFC request workflow id to `donna:rfc:work:request`.
  - Updated references to point to `donna:rfc:work:request`.
- gh-35 Updated RFC orchestration to include design-first planning.
  - Added `design` step to `donna:rfc:work:do` between RFC creation and planning.
  - Updated `donna:rfc:work:plan` to use Design documents as the primary planning input, with RFC as optional helper context.
- gh-35 Added session actions journal and CLI journal commands.
  - Added JSONL session journal storage with world-level APIs and reset-on-session-start behavior.
  - Added `donna journal write` and `donna journal view [--lines N] [--follow]` commands.
  - Added automatic journal records for `donna_log` instant output with task/work-unit context metadata.
  - Updated `donna:usage:cli` documentation with journal command usage.
- gh-35 Updated protocol formatters to use journal records for log output.
  - Renamed formatter API `format_log` to `format_journal` in base class, child classes, and call sites.
  - Updated `format_journal` to accept `JournalRecord` instead of `Cell`.
  - Updated automation formatter to output serialized journal JSON via `serialize_record(record)`.
  - Updated human and llm formatters to output `<timestamp> [<actor_id>] [<current_task_id>/<current_work_unit_id>] <message>`.

### Breaking Changes

- gh-35 Formatter protocol implementations must now implement `format_journal(record: JournalRecord, ...)` instead of
  `format_log(cell: Cell, ...)`.

### Migration

- gh-35 Renamed custom formatter hooks from `format_log` to `format_journal` and switched parameter type from `Cell`
  to `JournalRecord`.
