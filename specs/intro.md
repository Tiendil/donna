# List of specifications

## Goal of the document

This document lists all specification documents and specification directories in the project and briefly describes their purpose.

## Scope

The scope of this specification is limited to the specification index.

Detailed requirements for individual specifications are out of scope except for brief descriptions needed to keep the index useful.

## Specification directories

- `./specs/` — directory with all specifications.
- `./specs/architecture/` — specifications related to the architecture of the system.
- `./specs/behavior/` — specifications related to the behavior of the system.
- `./specs/documentation/` — specifications related to project documentation artifacts.
- `./specs/meta/` — specifications related to requirements for specification documents.

## Specification documents

- `./specs/intro.md` — this file, contains a list of all specifications and their brief descriptions.
- `./specs/dictionary.md` — shared project-specific terminology used by multiple specifications.
- `./specs/architecture/entities.md` — specification of project entity and data structure architecture, including typed domain fields in logic cells.
- `./specs/architecture/errors.md` — specification of project error handling architecture, including shared typed environment-error cells for all expected failures with Donna-owned stream and exit policies and shared internal-error template formatting.
- `./specs/architecture/modules_layout.md` — specification of the intended project module structure and ownership boundaries, including shared logic-cell emission through the iterable `emit_cells` interface, batch projection and rendering contexts, and Donna-owned typed domain logic cells, shared error logic cells, and node views supplying domain data without selecting an output-cell type.
- `./specs/architecture/naming.md` — specification of project code naming conventions.
- `./specs/architecture/tests.md` — specification of project test organization and testing expectations, including shared exception propagation, shared automation payload extraction and error-cell assertions, and local output parsing and journal filtering.
- `./specs/behavior/cli.md` — specification of the `donna` command line interface, Donna-owned result projections with shared protocol dispatch and rendering, and unified environment-error cells and preserved exit policies.
- `./specs/behavior/config.md` — specification of the `donna.toml` configuration file behavior, including shared path selection, home expansion, and missing-config diagnostics.
- `./specs/behavior/file_paths.md` — specification of Donna local project path, artifact id, and artifact section id syntax and resolution behavior.
- `./specs/behavior/skill_fixtures.md` — specification of built-in skill documentation fixture behavior.
- `./specs/documentation/changelog.md` — specification of changelog tooling, source files, version record structure, and entry format.
- `./specs/documentation/readme.md` — specification of the root `README.md` content, structure, source material, and tone.
- `./specs/meta/general.md` — general requirements for specification documents.
