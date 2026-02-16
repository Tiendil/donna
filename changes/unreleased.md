
### Changes

- gh-35 Moved session environment error rendering to the CLI boundary.
  - Updated `donna.machine.sessions` command-facing functions to return `Result[list[Cell], ErrorsList]`
    instead of rendering environment errors to cells in the machine layer.
  - Updated `donna.cli.commands.sessions` to unwrap session results at the CLI boundary.
  - Updated `donna.cli.utils.cells_cli` to process environment errors from unwrap failures and write
    single-line error records to the session journal.
  - Fixed typo in `donna/artifacts/intro.md` (`thoughs` -> `thoughts`) found during polish.

- gh-35 Removed `single_mode` from protocol formatter APIs.
  - Removed `single_mode` from `Formatter.format_cell(...)` in base and all formatter implementations.
  - Moved single-vs-multi-cell framing decisions into formatter internals (`format_cells(...)`) for `human` and `llm`.
  - Updated protocol output utility call sites to use the simplified `format_cell(cell)` signature.

- gh-35 Moved action-request/workflow journal writes into state transitions.
  - Moved `machine_journal.add(...)` for `complete_action_request` from `donna/machine/sessions.py` to
    `donna/machine/state.py`.
  - Moved `machine_journal.add(...)` for `start_workflow` from `donna/machine/sessions.py` to
    `donna/machine/state.py`.
  - Wrapped `MutableState.complete_action_request` and `MutableState.start_workflow` with `@unwrap_to_error` and
    updated session callers to handle `Result`.
  - Added a new `machine_journal.add(...)` call in `MutableState.finish_workflow`.
- gh-35 Updated artifacts validation command naming.
  - Removed the single-artifact `donna artifacts validate <world>:<artifact>` command behavior.
  - Renamed `donna artifacts validate-all [<artifact-pattern>]` to `donna artifacts validate [<artifact-pattern>]`.
  - Updated CLI usage documentation to reflect the new command surface.
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
- gh-35 Fixed journal follow behavior after journal file recreation.
  - Updated filesystem journal follow logic to detect file removal/recreation by file identity.
  - Reopened the journal stream automatically when the backing file changed, so `donna journal view --follow`
    continues after session restart/recreate flows.
- gh-35 Updated protocol formatters to use journal records for log output.
  - Renamed formatter API `format_log` to `format_journal` in base class, child classes, and call sites.
  - Updated `format_journal` to accept `JournalRecord` instead of `Cell`.
  - Updated automation formatter to output serialized journal JSON via `serialize_record(record)`.
  - Updated human and llm formatters to output `<timestamp> [<actor_id>] [<current_task_id>/<current_work_unit_id>] <message>`.
- gh-35 Updated workflow operation execution to propagate `execute_section` errors explicitly.
  - Changed `Primitive.execute_section` and all implementations to return `Result[list[Change], ErrorsList]`.
  - Updated all `execute_section` implementations to use `@unwrap_to_error` and removed direct fallback
    `machine_journal.JournalRecord` construction in error paths.
  - Updated work-unit execution to propagate `execute_section` `ErrorsList` and keep failed work units uncompleted.
- gh-35 Updated journal context handling for manual journal entries.
  - Removed default values from `machine_journal.add(...)` context parameters and made call sites pass values explicitly.
  - Updated `donna journal write` to resolve and store current task/work-unit/operation ids from session state when available.
  - Added explicit `current_operation_id` for `output` and `finish` workflow journal records.
- gh-35 Restricted journal messages to single-line values.
  - Updated `JournalRecord` validation to reject message values containing newline characters.
  - Updated `machine_journal.add(...)` to return a structured environment error for multiline messages.
  - Updated CLI/help/spec documentation to explicitly state `journal write` messages must be single-line.

### Breaking Changes

- gh-35 `donna.machine.sessions` command-facing APIs now return `Result[list[Cell], ErrorsList]` instead of `list[Cell]`.
- gh-35 `format_cell` in formatter implementations now accepts only `cell` (the `single_mode` parameter was removed).
- gh-35 `donna artifacts validate-all` was removed; use `donna artifacts validate [<artifact-pattern>]` instead.
- gh-35 Formatter protocol implementations must now implement `format_journal(record: JournalRecord, ...)` instead of
  `format_log(cell: Cell, ...)`.
- gh-35 Primitive and operation `execute_section` implementations must now return `Result[list[Change], ErrorsList]`
  instead of yielding changes directly.
- gh-35 `machine_journal.add(...)` now requires explicit `current_task_id`, `current_work_unit_id`,
  and `current_operation_id` arguments.
- gh-35 Journal messages now must be single-line; `journal write` and `machine_journal.add(...)` reject newline
  characters in `message`.

### Removals

- gh-35 Removed `single_mode` support from formatter `format_cell(...)` APIs.
- gh-35 Removed single-artifact `donna artifacts validate <world>:<artifact>` command behavior.

### Migration

- gh-35 Updated integrations that call `donna.machine.sessions` command-facing functions to handle `Result` values.
- gh-35 Removed `single_mode` argument from custom formatter `format_cell(...)` implementations and call sites.
- gh-35 Replaced `donna artifacts validate-all [<artifact-pattern>]` calls with `donna artifacts validate [<artifact-pattern>]`.
- gh-35 Renamed custom formatter hooks from `format_log` to `format_journal` and switched parameter type from `Cell`
  to `JournalRecord`.
- gh-35 Updated custom primitives and operations to return `Ok([Change...])`/`Err(ErrorsList)` from `execute_section`
  and use `@unwrap_to_error` for unwrap-based propagation.
- gh-35 Updated direct calls to `machine_journal.add(...)` to pass explicit task/work-unit/operation ids
  (or `None` when unavailable).
- gh-35 Updated journal writers to pass single-line messages only (replace newline characters or split into multiple
  records).
