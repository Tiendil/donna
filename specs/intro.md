# List of specifications

## Goal of the document

This document indexes the project's specifications and their purposes.

## Scope

The specification index and its maintenance; detailed product requirements are out of scope.

## Index requirements

The index MUST list every specification with its path and a brief description.
Each description MUST identify the specification's stable subject or purpose rather than enumerate its contents.
Descriptions MUST NOT list individual requirements or current implementation details.
Descriptions SHOULD remain accurate when details change within the specification's existing scope.
The index MUST be kept complete and accurate when specifications are added, removed, or change scope.

**Example:** Describe a configuration specification as “The project configuration contract,” without listing its current configuration fields.

## Specification directories

- `./specs/` — all specifications.
- `./specs/architecture/` — system architecture.
- `./specs/behavior/` — observable tool behavior.
- `./specs/documentation/` — documentation artifacts.
- `./specs/meta/` — specification-writing requirements.

## Specification documents

- `./specs/intro.md` — Index of project specifications.
- `./specs/dictionary.md` — Shared project terminology.
- `./specs/architecture/entities.md` — Conventions for modeling project data.
- `./specs/architecture/errors.md` — Conventions for representing and propagating diagnostics.
- `./specs/architecture/modules_layout.md` — Ownership boundaries between project modules.
- `./specs/architecture/naming.md` — Code naming conventions.
- `./specs/architecture/tests.md` — Requirements for verifying project behavior.
- `./specs/behavior/cli.md` — The tool's command-line interface contract.
- `./specs/behavior/config.md` — The project configuration contract.
- `./specs/behavior/file_paths.md` — The contract for addressing workflow artifacts.
- `./specs/behavior/skill_fixtures.md` — Requirements for built-in skill documentation.
- `./specs/documentation/changelog.md` — Requirements for maintaining the project changelog.
- `./specs/documentation/readme.md` — Requirements for the root README.
- `./specs/meta/general.md` — Requirements for specification content and presentation.
- `./specs/meta/behavior.md` — Rules for expressing observable behavior in specifications.

The corresponding specifications in `llm-tool-cli` own the generic contracts for:

- configuration.
- paths.
- globs.
- output.

Donna's specs define their application and tool-specific behavior.
