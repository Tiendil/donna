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

Define semantic tags in artifact metadata (likely in the primary section) and provide deterministic, tag-based discovery in the CLI without replacing existing identifier pattern matching. Agents MUST be able to assign one or more keywords to artifacts and search/list artifacts by repeated `--tag` options, and users MUST have a deterministic way to list all available tags with descriptions via a CLI command or a dedicated specification artifact.

## Goals

- Enable deterministic discovery of artifacts by semantic meaning independent of artifact hierarchy.
- Provide a shared, documented tagging vocabulary so agents and users can apply tags consistently.
- Preserve deterministic search behavior without introducing fuzzy or vector-based matching.

## Objectives

- Artifact primary section metadata supports a `tags` attribute (list of strings) that is persisted and available for search/filtering.
- Relevant CLI artifact discovery commands accept a repeatable `--tag` option that filters to artifacts containing all specified tags.
- Tag filtering works independently of artifact identifier hierarchy and can be combined with existing pattern matching.
- A canonical catalog of available tags with descriptions exists and is accessible via a CLI command or a dedicated specification artifact.
- User/agent documentation explains how to assign tags and how to discover available tags.
- Tag matching is exact and deterministic, and no fuzzy or vector search is introduced for tag discovery.
- Existing pattern-based search behavior remains unchanged when `--tag` is not provided.

## Constraints

- The solution MUST NOT introduce vector or fuzzy search and MUST keep tag matching deterministic.

## Requirements

- Artifact metadata MUST support zero or more semantic tags as keywords.
- Tags MUST be expressible in the artifact primary section metadata.
- Relevant CLI artifact discovery commands MUST accept a repeatable `--tag` option.
- When multiple `--tag` values are provided, results MUST include only artifacts that contain all specified tags.
- Tag filtering MUST be usable together with existing artifact identifier pattern filters.
- Tag matching MUST be deterministic and based on exact keyword comparison.
- The system MUST provide a deterministic, user-accessible list of available tags with descriptions.

## Acceptance criteria

- `donna -p llm artifacts list --help` includes a repeatable `--tag` option.
- `donna -p llm artifacts view --help` includes a repeatable `--tag` option.
- `donna -p llm artifacts list --tag workflow` returns only artifacts whose metadata includes the `workflow` tag.
- `donna -p llm artifacts list --tag workflow --tag specification` returns only artifacts whose metadata includes both tags.
- `donna -p llm artifacts list "world:pattern" --tag workflow` returns only artifacts that satisfy both the pattern and tag filters.
- The artifact `donna:specs:artifact_tags` exists and contains tag names with descriptions.

## Solution

- Artifact primary section configuration includes a `tags` list of keyword strings, and tags are available in artifact metadata for search and filtering.
- The CLI commands `donna -p llm artifacts list` and `donna -p llm artifacts view` accept a repeatable `--tag` option.
- When multiple `--tag` values are provided, the CLI filters to artifacts containing all specified tags.
- Tag filtering can be combined with existing artifact identifier pattern filters in the same command.
- Tag matching is exact and deterministic, with no fuzzy or vector search.
- The specification artifact `donna:specs:artifact_tags` exists and documents available tags with descriptions.
- User-facing documentation describes how to assign tags and how to discover and use tag-based search.

## Verification

- Verify Objective O1: Create a test artifact (e.g., `session:tag-test`) with `tags = ["workflow"]` in the primary section metadata and confirm it appears in `donna -p llm artifacts list --tag workflow`.
- Verify Objective O2: Run `donna -p llm artifacts list --help` and `donna -p llm artifacts view --help` and confirm both document a repeatable `--tag` option.
- Verify Objective O3: Run `donna -p llm artifacts list "session:**" --tag workflow` and confirm the results satisfy both the pattern and tag filter.
- Verify Objective O4: View `donna:specs:artifact_tags` and confirm it contains tag names with descriptions.
- Verify Objective O5: View `donna:usage:artifacts` and confirm it describes how to assign tags and discover available tags.
- Verify Objective O6: Inspect the tag filtering implementation and confirm it performs exact string comparison without fuzzy/vector search logic.
- Verify Objective O7: Run `donna -p llm artifacts list "session:**"` with no `--tag` and confirm it returns artifacts based on pattern matching.
- Verify Constraint C1: Inspect dependencies and tag filtering code to confirm no vector/fuzzy search libraries or algorithms are introduced.
- Verify Requirement R1: Add `tags` metadata to an artifact and ensure `donna -p llm artifacts validate <artifact-id>` succeeds.
- Verify Requirement R2: Inspect an artifact primary section config (or `donna:usage:artifacts`) and confirm tags are declared in the primary section metadata.
- Verify Requirement R3: Run `donna -p llm artifacts list --help` and confirm the `--tag` option is available and repeatable.
- Verify Requirement R4: Run `donna -p llm artifacts list --tag workflow --tag specification` and confirm only artifacts containing both tags are returned.
- Verify Requirement R5: Run `donna -p llm artifacts list "session:**" --tag workflow` and confirm results match both filters.
- Verify Requirement R6: Create artifacts tagged `work` and `workflow`, then run `donna -p llm artifacts list --tag work` and confirm only the exact `work` tag matches.
- Verify Requirement R7: View `donna:specs:artifact_tags` and confirm it lists tags with descriptions.
- Verify Acceptance Criterion A1: Run `donna -p llm artifacts list --help` and confirm the repeatable `--tag` option is documented.
- Verify Acceptance Criterion A2: Run `donna -p llm artifacts view --help` and confirm the repeatable `--tag` option is documented.
- Verify Acceptance Criterion A3: Run `donna -p llm artifacts list --tag workflow` and confirm only artifacts with the `workflow` tag are returned.
- Verify Acceptance Criterion A4: Run `donna -p llm artifacts list --tag workflow --tag specification` and confirm only artifacts with both tags are returned.
- Verify Acceptance Criterion A5: Run `donna -p llm artifacts list "world:pattern" --tag workflow` and confirm only artifacts that match both filters are returned.
- Verify Acceptance Criterion A6: View `donna:specs:artifact_tags` and confirm it exists with tag names and descriptions.

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
