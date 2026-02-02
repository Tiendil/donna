# Artifact Tags for Deterministic Semantic Search

```toml donna
kind = "donna.lib.specification"
```

Add first-class artifact tags and CLI support for deterministic semantic search, including tag discovery, without relying on vector search.

## Original description

Draft an RFC for the next task:

Currently, one can search for Donna's artifact by pattern-matching the artifact identifier, such as `world:part_1:*:part_3`. It is helpful, but this approach has issues with searching artifacts by their semantics: you can not search for artifacts with specific properties until you reflect those properties in the hierarchy (like `world:workflows:*`, `world:specifications:*`).

That is not very convenient, since it may be preferable to group artifacts by domain area rather than by their semantics.

Also, we strive to keep Donna's logic as deterministic as possible, so vector/fuzzy search is not our first choice.

To improve search, we could tag each artifact with semantically valuable keywords, like `workflow`, `specification`, `grooming`. By providing agents with a description of those tags, we'll allow them to deterministically search artifacts by their semantics.

Expected scope of work:

- Add tags as an attribute of artifact metadata. Most likely, as metadata of the artifact's primary section.
- Add `--tag` attribute to relevant CLI commands. The tag attribute must allow repeated usage to specify multiple tags.
- We should provide a way to list all available tags with their descriptions. Either via a dedicated CLI command, just create a separate specification artifact with the list of tags.

## Formal description

Introduce artifact-level tags stored in primary section metadata and expose deterministic tag-based filtering in the CLI so agents can locate artifacts by semantic keywords without restructuring artifact identifiers. Provide a canonical tag registry with descriptions so users can consistently assign and search tags and verify behavior via explicit CLI commands.

## Goals

- G1: Enable deterministic semantic search for artifacts by tags without encoding semantics into the artifact identifier hierarchy.
- G2: Make the tag vocabulary discoverable and consistent for agents and developers.

## Objectives

- O1 (G1): Primary section configuration supports tags and exposes them as artifact metadata for filtering.
- O2 (G1): CLI artifact search supports tag filtering via repeatable `--tag` options with deterministic matching rules.
- O3 (G2): A canonical tag registry exists and lists each tag with a human-readable description.
- O4 (G2): The tag registry is accessible through a deterministic CLI view command.

## Constraints

- C1: The solution MUST NOT rely on vector or fuzzy search; tag matching MUST be deterministic and exact.
- C2: Tagging MUST allow semantic classification without requiring changes to artifact identifier hierarchy.

## Requirements

- R1: The artifact primary section configuration MUST accept a `tags` field containing a list of tag strings.
- R2: `donna -p llm artifacts list` and `donna -p llm artifacts view` MUST accept a repeatable `--tag` option and filter results to artifacts containing all specified tags.
- R3: Tag normalization and matching rules MUST be explicit and deterministic (for example, compare lowercase tag strings exactly).
- R4: A tag registry MUST be provided as a Donna specification artifact in the `donna:` world, listing each tag with a description.

## Acceptance criteria

- A1: An artifact with primary config `tags = ["workflow", "specification"]` validates successfully via `donna -p llm artifacts validate <artifact>`.
- A2: Running `donna -p llm artifacts list --tag workflow` returns only artifacts whose primary-section tags include `workflow`.
- A3: Running `donna -p llm artifacts view --tag workflow --tag grooming` returns only artifacts whose primary-section tags include both `workflow` and `grooming`.
- A4: Artifact `donna:specs:artifact_tags` exists and lists at least the tags `workflow`, `specification`, and `grooming` with descriptions.

## Solution

- S1: Artifact primary section config supports `tags = ["..."]`, and the parsed tags are stored in primary-section metadata for downstream filtering.
- S2: CLI `artifacts list` and `artifacts view` accept repeatable `--tag` options and filter to artifacts whose tag set contains all requested tags.
- S3: Tags are normalized to lowercase ASCII on read, and matching uses exact string equality against the normalized tag list.
- S4: The canonical tag registry is the specification artifact `donna:specs:artifact_tags`, which lists tag names, descriptions, and usage guidance.

## Verification

- V1 (O1): Inspect an artifact with `tags = ["workflow"]`; primary-section metadata exposes `workflow` in its tag list during filtering.
- V2 (O2): Run `donna -p llm artifacts list --tag workflow --tag grooming`; results include only artifacts tagged with both.
- V3 (O3): View `donna:specs:artifact_tags`; it contains a list of tag names and descriptions.
- V4 (O4): Execute `donna -p llm artifacts view "donna:specs:artifact_tags"`; the registry renders in CLI output.
- V5 (C1): Code review confirms no vector or fuzzy search libraries or algorithms are used for tag matching.
- V6 (C2): Tag filtering works without changing artifact identifiers; artifacts remain searchable by existing id patterns.
- V7 (R1): Add `tags` to a primary config block and validate the artifact; validation succeeds.
- V8 (R2): `donna -p llm artifacts list --tag workflow` and `donna -p llm artifacts view --tag workflow` both accept the flag and apply filtering.
- V9 (R3): Documentation in `donna:specs:artifact_tags` states the normalization rules; behavior matches exact lowercase comparison.
- V10 (R4): `donna:specs:artifact_tags` exists in the `donna:` world and is viewable via the CLI.
- V11 (A1): Run `donna -p llm artifacts validate <artifact>` on a tagged artifact; it succeeds.
- V12 (A2): Run `donna -p llm artifacts list --tag workflow`; verify only tagged artifacts appear.
- V13 (A3): Run `donna -p llm artifacts view --tag workflow --tag grooming`; verify only dual-tagged artifacts appear.
- V14 (A4): View `donna:specs:artifact_tags`; confirm the example tags and descriptions are present.

## Deliverables

- D1: Specification artifact `donna:specs:artifact_tags` exists and includes tag names with descriptions.
- D2: Source file `donna/cli/commands/artifacts.py` includes repeatable `--tag` options for `list` and `view`.
- D3: Artifact primary-section configuration schema supports a `tags` list and exposes it for filtering.

## Action items

- Add a `tags` field to the primary section configuration model and store it in primary-section metadata.
- Implement tag filtering in artifact listing and viewing paths using repeatable `--tag` CLI options.
- Define and document tag normalization rules in `donna:specs:artifact_tags`.
- Create `donna:specs:artifact_tags` with tag names, descriptions, and usage guidance.
