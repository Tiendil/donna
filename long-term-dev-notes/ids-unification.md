
# IDs Unification

It will be nice to have shorter IDs for all entities, like `<type>-<int>-<control-sum>` instead of full UUIDs and simple ints. It should help both humans and agents to work with them.

Where:

- `<type>` is a short string identifying the entity type, like `story`, `artifact`, `workunit`, `change`, `cell`, etc.
- `<int>` is a consecutive integer identifying the specific entity of that type.
- `<control-sum>` is the same integer but zipped to an ASCII string from characters `[a-zA-Z0-9]`.

It should be not problem to use integer ids in the case of parallel execution, since we rarely create entities => locking the counter should be fine.

## Questions about implementation

1. It would be easier to track them gloally for the project, but it may be confusing when ids of local entities will jump around.

Thus, there may be various scopes for ids: world, story, artifact.

2. We may want to use some global, or locally-global counters for various entities to generate integer parts of the ids.

However, most of the entities can be counted on the fly => for them we may skip storing the counters.

But we may want to use counters becaue of uniformity.

3. Some entities, like artifacts, may be intended to be unique named in some context. For example, it is easy to mention `risks.md` artifact in the story operations, rather than `artifact-<random-int>-<random-string>-risks.md` — no need to pass the id around.

4. We do not need to work with ids of some entities (like work units, changes, cells) => they may use simpler approach to ids, like UUIDs. However, we may want to unify all ids to the same format.
