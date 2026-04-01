### Migration

- Update your scripts and specs to use external tools or direct file edits to create, update, move, copy, or delete world artifacts instead using removed Donna commands.

### Changes

- `--tag` option is replaced with `--predicate` in all CLI commands that accept artifact patterns.
- Removed world artifact mutation support.
  - Removed `donna artifacts` mutation commands and the supporting artifact-mutation code paths.
  - Removed `readonly` world-artifact mutability modeling from workspace config and world abstractions.
  - Updated artifact and world usage specs to state that developers and external tools mutate world artifacts while Donna validates them.
- Removed `donna artifacts fetch` and `donna artifacts tmp` commands and all related code.

### Breaking Changes

- `donna artifacts` no longer supports `update`, `copy`, `move`, or `remove`.
- Donna no longer mutates world artifacts through workspace APIs or world configuration.
