# Add Semantic Tags to Artifact Metadata and CLI Search

```toml donna
kind = "donna.lib.specification"
```

Introduce deterministic semantic tagging for artifacts and enable tag-based discovery in the CLI while preserving existing pattern-based search.

## Original description

Currently, one can search for Donna's artifact by pattern-matching the artifact identifier, such as `world:part_1:*:part_3`. It is helpful, but this approach has issues with searching artifacts by their semantics: you can not search for artifacts with specific properties until you reflect those properties in the hierarchy (like `world:workflows:*`, `world:specifications:*`).

That is not very convenient, since it may be preferable to group artifacts by domain area rather than by their semantics.

Also, we strive to keep Donna's logic as deterministic as possible, so vector/fuzzy search is not our first choice.

To improve search, we could tag each artifact with semantically valuable keywords, like `workflow`, `specification`, `grooming`. By providing agents with a description of those tags, we'll allow them to deterministically search artifacts by their semantics.

Expected scope of work:

- Add tags as an attribute of artifact metadata. Most likely, as metadata of the artifact's primary section.
- Add `--tag` attribute to relevant CLI commands. The tag attribute must allow repeated usage to specify multiple tags.
- We should provide a way to list all available tags with their descriptions. Either via a dedicated CLI command, just create a separate specification artifact with the list of tags.


Use `donna:rfc:work:draft_rfc` workflow

## Formal description

Define semantic tags in artifact metadata (in the primary section) and provide deterministic, tag-based discovery in the CLI without replacing existing identifier pattern matching. Agents MUST be able to assign one or more keywords to artifacts and search/list artifacts by repeated `--tag` options, and users MUST have a deterministic way to list all available tags with descriptions via a dedicated specification artifact (`donna:specs:artifact_tags`).

## Goals

- Enable deterministic discovery of artifacts by semantic meaning independent of artifact hierarchy.
- Provide a shared, documented tagging vocabulary so agents and users can apply tags consistently.
- Preserve deterministic search behavior without introducing fuzzy or vector-based matching.

## Objectives

- O1: Artifact primary section metadata supports a `tags` attribute (list of strings) that is persisted and available for search/filtering.
- O2: `donna -p llm artifacts list` and `donna -p llm artifacts view` accept a repeatable `--tag` option that filters to artifacts containing all specified tags.
- O3: Tag filtering works independently of artifact identifier hierarchy and can be combined with existing pattern matching.
- O4: A canonical catalog of available tags with descriptions exists in the specification artifact `donna:specs:artifact_tags`.
- O5: User/agent documentation explains how to assign tags and how to discover available tags.
- O6: Tag matching is exact and deterministic, and no fuzzy or vector search is introduced for tag discovery.
- O7: Existing pattern-based search behavior remains unchanged when `--tag` is not provided.

## Constraints

- The solution MUST NOT introduce vector or fuzzy search and MUST keep tag matching deterministic.

## Requirements

- R1: Artifact metadata MUST support zero or more semantic tags as keywords.
- R2: Tags MUST be expressible in the artifact primary section metadata.
- R3: `donna -p llm artifacts list` MUST accept a repeatable `--tag` option.
- R4: `donna -p llm artifacts view` MUST accept a repeatable `--tag` option.
- R5: When multiple `--tag` values are provided, results MUST include only artifacts that contain all specified tags.
- R6: Tag filtering MUST be usable together with existing artifact identifier pattern filters.
- R7: Tag matching MUST be deterministic and based on exact keyword comparison.
- R8: When `--tag` is not provided, tag filtering MUST NOT be applied.
- R9: The system MUST provide a deterministic, user-accessible list of available tags with descriptions via `donna:specs:artifact_tags`.
- R10: The artifact `donna:usage:artifacts` MUST document `tags` metadata and tag-based search.

## Acceptance criteria

- A1: `donna -p llm artifacts list --help` includes a repeatable `--tag` option.
- A2: `donna -p llm artifacts view --help` includes a repeatable `--tag` option.
- A3: `donna -p llm artifacts list --tag workflow` returns only artifacts whose metadata includes the `workflow` tag.
- A4: `donna -p llm artifacts list --tag workflow --tag specification` returns only artifacts whose metadata includes both tags.
- A5: `donna -p llm artifacts list "session:**" --tag workflow` returns only artifacts that satisfy both the pattern and tag filters.
- A6: `donna -p llm artifacts list "session:**"` returns artifacts based only on the pattern (no tag filtering).
- A7: The artifact `donna:specs:artifact_tags` exists and contains tag names with descriptions.
- A8: The artifact `donna:usage:artifacts` documents `tags` metadata and tag-based search.

## Solution

- Artifact primary section configuration includes a `tags` list of keyword strings, and tags are available in artifact metadata for search and filtering.
- The CLI commands `donna -p llm artifacts list` and `donna -p llm artifacts view` accept a repeatable `--tag` option.
- When multiple `--tag` values are provided, the CLI filters to artifacts containing all specified tags.
- Tag filtering can be combined with existing artifact identifier pattern filters in the same command.
- Tag matching is exact and deterministic, with no fuzzy or vector search.
- When `--tag` is not provided, tag filtering is not applied and pattern-only search behavior is preserved.
- The specification artifact `donna:specs:artifact_tags` exists and documents available tags with descriptions.
- User-facing documentation in `donna:usage:artifacts` describes how to assign tags and how to discover and use tag-based search.

## Verification

- Verify O1: Create a test artifact (e.g., `session:tag-test`) with `tags = ["workflow"]` in the primary section metadata and confirm it appears in `donna -p llm artifacts list --tag workflow`.
- Verify O2: Run `donna -p llm artifacts list --tag workflow` and `donna -p llm artifacts view "session:**" --tag workflow` to confirm both commands accept repeatable `--tag` options.
- Verify O3: Run `donna -p llm artifacts list "session:**" --tag workflow` and confirm each result matches both the pattern and tag filters.
- Verify O4: View `donna:specs:artifact_tags` and confirm it lists tag names with descriptions.
- Verify O5: View `donna:usage:artifacts` and confirm it documents how to assign tags and discover available tags.
- Verify O6: Inspect tag filtering code and confirm it uses exact keyword comparison without fuzzy/vector search logic.
- Verify O7: Run `donna -p llm artifacts list "session:**"` and confirm results are not filtered by tags.
- Verify C1: Inspect dependencies and search logic to confirm no vector/fuzzy search libraries or algorithms are introduced.
- Verify R1: Add `tags` metadata to an artifact and ensure `donna -p llm artifacts validate <artifact-id>` succeeds.
- Verify R2: Inspect an artifact primary section config and confirm tags are declared in the primary section metadata.
- Verify R3: Run `donna -p llm artifacts list --help` and confirm the `--tag` option is available and repeatable.
- Verify R4: Run `donna -p llm artifacts view --help` and confirm the `--tag` option is available and repeatable.
- Verify R5: Run `donna -p llm artifacts list --tag workflow --tag specification` and confirm only artifacts containing both tags are returned.
- Verify R6: Run `donna -p llm artifacts list "session:**" --tag workflow` and confirm results match both filters.
- Verify R7: Create artifacts tagged `work` and `workflow`, then run `donna -p llm artifacts list --tag work` and confirm only the exact `work` tag matches.
- Verify R8: Run `donna -p llm artifacts list "session:**"` and confirm results are based only on the pattern.
- Verify R9: View `donna:specs:artifact_tags` and confirm it exists with tag names and descriptions.
- Verify R10: View `donna:usage:artifacts` and confirm it documents `tags` metadata and tag-based search.
- Verify A1: Run `donna -p llm artifacts list --help` and confirm the repeatable `--tag` option is documented.
- Verify A2: Run `donna -p llm artifacts view --help` and confirm the repeatable `--tag` option is documented.
- Verify A3: Run `donna -p llm artifacts list --tag workflow` and confirm only artifacts with the `workflow` tag are returned.
- Verify A4: Run `donna -p llm artifacts list --tag workflow --tag specification` and confirm only artifacts with both tags are returned.
- Verify A5: Run `donna -p llm artifacts list "session:**" --tag workflow` and confirm only artifacts that match both filters are returned.
- Verify A6: Run `donna -p llm artifacts list "session:**"` and confirm results are based only on the pattern.
- Verify A7: View `donna:specs:artifact_tags` and confirm it exists with tag names and descriptions.
- Verify A8: View `donna:usage:artifacts` and confirm it documents `tags` metadata and tag-based search.

## Deliverables

- Donna artifact `donna:specs:artifact_tags` exists and lists tag names with descriptions.
- Donna artifact `donna:usage:artifacts` includes documentation for `tags` metadata and tag-based search.

## Action items

- Extend artifact metadata parsing to accept a `tags` list in primary section config (e.g., `donna/workspaces/sources/markdown.py` and related artifact metadata models).
- Store parsed tags in artifact metadata so they are available to filtering and listing logic.
- Add a repeatable `--tag` option to `donna -p llm artifacts list` and `donna -p llm artifacts view` CLI commands (e.g., `donna/cli/commands/artifacts.py`).
- Implement tag filtering with exact string matching and AND semantics, combining `--tag` with existing pattern filters.
- Add tests covering tag parsing, tag filtering, multiple `--tag` usage, and pattern+tag combinations.
- Create the specification artifact `donna:specs:artifact_tags` with tag names and descriptions.
- Update the artifact `donna:usage:artifacts` to document `tags` metadata and tag-based search.
