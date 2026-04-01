### Migration

- Move project-specific specs from `.donna/project` to `specs`, or set an explicit `project` world path in your Donna workspace config before upgrading.
- Run `donna workspaces update` in existing projects so bundled Donna specs are installed into `.agents/donna` for the new filesystem-backed `donna` world.
- Update your scripts and specs to use external tools or direct file edits to create, update, move, copy, or delete world artifacts instead using removed Donna commands.

### Changes

- Changed the default location of project specs to `specs/`.
  - Updated the default `project` world path to load from `specs/` instead of `.donna/project/`.
  - Rewrote the moved project specs and repository docs to reference the new `specs/` location.
- `--tag` option is replaced with `--predicate` in all CLI commands that accept artifact patterns.
- Removed the Python donna world.
  - Added workspace spec dumping into `.agents/donna` on `donna workspaces init` and `donna workspaces update`.
  - Reconfigured the default `donna` world to load bundled specs from `.agents/donna` through the filesystem world and removed the Python world implementation.
- Removed world artifact mutation support.
  - Removed `donna artifacts` mutation commands and the supporting artifact-mutation code paths.
  - Removed `readonly` world-artifact mutability modeling from workspace config and world abstractions.
  - Updated artifact and world usage specs to state that developers and external tools mutate world artifacts while Donna validates them.
- Removed `donna artifacts fetch` and `donna artifacts tmp` commands and all related code.

### Breaking Changes

- Donna no longer exposes bundled specs through the Python-backed `donna` world; `donna workspaces init|update` now sync them into `.agents/donna`.
- `donna artifacts` no longer supports `update`, `copy`, `move`, or `remove`.
- Donna no longer mutates world artifacts through workspace APIs or world configuration.

### Removals

- Removed the Python world implementation and the `donna.artifacts` package-backed source of bundled Donna specs.
