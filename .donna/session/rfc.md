# Add semantic tags to artifacts and CLI search

```toml donna
kind = "donna.lib.specification"
```

Introduce first-class semantic tags for artifacts so agents can deterministically search by meaning (e.g., workflow, specification, grooming) without relying on hierarchy placement. Add CLI support for filtering by tag and provide a discoverable list of available tags with descriptions.

## Original description

Currently, one can search for Donna's artifact by pattern-matching the artifact identifier, such as `world:part_1:*:part_3`. It is helpful, but this approach has issues with searching artifacts by their semantics: you can not search for artifacts with specific properties until you reflect those properties in the hierarchy (like `world:workflows:*`, `world:specifications:*`).

That is not very convenient, since it may be preferable to group artifacts by domain area rather than by their semantics.

Also, we strive to keep Donna's logic as deterministic as possible, so vector/fuzzy search is not our first choice.

To improve search, we could tag each artifact with semantically valuable keywords, like `workflow`, `specification`, `grooming`. By providing agents with a description of those tags, we'll allow them to deterministically search artifacts by their semantics.

Expected scope of work:

- Add tags as an attribute of artifact metadata. Most likely, as metadata of the artifact's primary section.
- Add `--tag` attribute to relevant CLI commands. The tag attribute must allow repeated usage to specify multiple tags.
- We should provide a way to list all available tags with their descriptions. Either via a dedicated CLI command, just create a separate specification artifact with the list of tags.

## Formal description

Donna SHOULD support deterministic, semantic search for artifacts by introducing first-class tags in artifact metadata, exposing tag-based filters in CLI commands that list or view artifacts, and providing a canonical, discoverable registry of available tags and their meanings. After these changes, agents can request artifacts by tag (optionally combined with existing identifier patterns) and can reliably learn which tags exist and how to use them.

## Goals

- Enable deterministic semantic discovery of artifacts without forcing hierarchy changes.
- Make tag usage discoverable and consistent across the project.

## Objectives

- Artifact primary metadata supports a tag list that can be parsed and surfaced by Donna.
- CLI can filter artifact listings by one or more tags without requiring hierarchy changes.
- A canonical, version-controlled registry of tags and descriptions exists as a Donna artifact or CLI output.
- Agents can retrieve tag descriptions without guessing (via a documented command or referenced specification artifact).
## Constraints

- The solution MUST use deterministic search behavior and MUST NOT depend on vector or fuzzy search.
## Requirements

- Artifact primary section metadata MUST support a `tags` field containing a list of tag identifiers.
- `donna -p llm artifacts list` MUST accept a repeatable `--tag <tag>` option that filters results to artifacts containing all specified tags.
- `donna -p llm artifacts view` MUST accept a repeatable `--tag <tag>` option that filters rendered artifacts to those containing all specified tags.
- When multiple `--tag` options are provided, matching MUST require every specified tag to be present.
- The system MUST provide a discoverable list of all available tags with their descriptions via either a dedicated CLI command or a dedicated specification artifact.
## Acceptance criteria

- `donna -p llm artifacts list --help` shows a repeatable `--tag` option with a description indicating tag-based filtering.
- `donna -p llm artifacts view --help` shows a repeatable `--tag` option with a description indicating tag-based filtering.
- Running `donna -p llm artifacts list --tag <tag>` returns only artifacts whose primary metadata includes `<tag>` in `tags`.
- Running `donna -p llm artifacts view --tag <tag>` renders only artifacts whose primary metadata includes `<tag>` in `tags`.
- Running `donna -p llm artifacts list --tag <tag-a> --tag <tag-b>` returns only artifacts whose primary metadata includes both tags.
- A specification artifact `donna:usage:tags` exists and lists each supported tag with a description.
## Solution

- Artifact primary section configuration includes a `tags` list that is parsed into artifact metadata.
- Artifact listing and viewing operations can filter by tags, requiring all specified tags to be present.
- CLI help for `artifacts list` and `artifacts view` documents the `--tag` option and its repeatable usage.
- A new specification artifact `donna:usage:tags` documents the available tags and their descriptions.
## Verification

- (O1) Create a test artifact whose primary config includes `tags = ["workflow"]`; run `donna -p llm artifacts list --tag workflow`; the artifact MUST appear in the output.  
- (O2) Create a second test artifact without the `workflow` tag; run `donna -p llm artifacts view --tag workflow`; only the artifact with `workflow` MUST be rendered.  
- (O3) Run `donna -p llm artifacts list "donna:usage:tags"`; the artifact MUST exist.  
- (O4) Run `donna -p llm artifacts view "donna:usage:tags"`; the artifact MUST explain how agents find tag descriptions.  
- (C1) Review tag-filtering implementation or documentation; tag matching MUST be exact and must not use vector or fuzzy search.  
- (R1) Create a test artifact whose primary config includes `tags = ["workflow"]`; run `donna -p llm artifacts validate <artifact-id>`; validation MUST succeed.  
- (R2) Run `donna -p llm artifacts list --tag workflow --tag grooming`; only artifacts whose primary metadata includes both tags MUST be returned.  
- (R3) Run `donna -p llm artifacts view --tag workflow --tag grooming`; only artifacts whose primary metadata includes both tags MUST be rendered.  
- (R4) Create an artifact with `tags = ["workflow"]` and another with `tags = ["workflow", "grooming"]`; run `donna -p llm artifacts list --tag workflow --tag grooming`; only the two-tag artifact MUST appear.  
- (R5) Run `donna -p llm artifacts view "donna:usage:tags"`; the tag registry MUST be accessible via Donna.  
- (AC1) Run `donna -p llm artifacts list --help`; the help text MUST document a repeatable `--tag` option.  
- (AC2) Run `donna -p llm artifacts view --help`; the help text MUST document a repeatable `--tag` option.  
- (AC3) Create a test artifact with `tags = ["specification"]`; run `donna -p llm artifacts list --tag specification`; only artifacts with `specification` MUST be returned.  
- (AC4) Create a test artifact with `tags = ["specification"]`; run `donna -p llm artifacts view --tag specification`; only artifacts with `specification` MUST be rendered.  
- (AC5) Create a test artifact with `tags = ["alpha", "beta"]` and another with `tags = ["alpha"]`; run `donna -p llm artifacts list --tag alpha --tag beta`; only the two-tag artifact MUST appear.  
- (AC6) Run `donna -p llm artifacts view "donna:usage:tags"`; the artifact MUST list each supported tag with a description.  
## Deliverables

- Donna specification artifact `donna:usage:tags` exists.
- Donna specification artifact `donna:usage:artifacts` documents the `tags` metadata field for primary sections.
## Action items

- Add `tags` metadata parsing and storage for artifact primary sections in the artifact model/index.
- Extend `donna -p llm artifacts list` to accept repeatable `--tag` filters and enforce all-tag matching.
- Extend `donna -p llm artifacts view` to accept repeatable `--tag` filters and enforce all-tag matching.
- Update CLI help text for `artifacts list` and `artifacts view` to document `--tag` usage.
- Create specification artifact `donna:usage:tags` listing supported tags and descriptions.
- Update `donna:usage:artifacts` to document the `tags` field in primary metadata.
