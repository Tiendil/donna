# Changelog Documentation

## Goal of the document

This document describes requirements for maintaining the project changelog.

## Scope

This specification covers changelog artifacts.
The following are out of scope:

- release versioning.
- publishing.
- tagging.
- automation implementation.
- other documentation.

## Dictionary

- `changelog artifact` — a Changy source in `changes/` or generated root `CHANGELOG.md`.
- `version record` — Markdown changes for one released or unreleased version.

## Tooling

The project MUST:

- use [Changy](https://github.com/Tiendil/changy/).
- keep sources in `changes/`.
- generate root `CHANGELOG.md` from those sources.
- record unreleased changes in `changes/unreleased.md`.

## Version Record Structure

A record MAY contain these parts, in order:

1. A short introduction for large coordinated changes benefiting from context.
2. `Migration` instructions for breaking changes or manual upgrades.
3. `Changes`, listing all notable changes.
4. `Deprecations`, listing deprecated features or behavior.

Named sections MUST use h3 headings.
`Changes` SHOULD appear for notable user-visible, developer-visible, or maintenance changes.
`Migration` MUST appear for required manual steps before, during, or after upgrading.
`Deprecations` MUST appear when any of the following is deprecated:

- features.
- behavior.
- APIs.
- commands.
- configuration fields.
- documented workflows.

Additional h3 sections MAY cover distinct categories.

## Entry Format

Entries SHOULD be short bullet descriptions linked to existing tasks, issues, or pull requests.
GitHub issues SHOULD use `gh-<number>`; references to pull requests or other trackers SHOULD use the shortest stable project convention.
Nested details MAY explain impact or required action.

## Example

```markdown
<intro>

### Migration

- gh-xxx - <short migration instruction>
- gh-yyy - <short migration instruction>
  - <additional details if needed>
  - <additional details if needed>

### Changes

- gh-zzz - <short description of the change>

### Deprecations

- gh-www - <short description of the deprecation>
```
