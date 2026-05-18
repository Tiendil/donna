# Test architecture

## Goal of the document

This document describes the architecture of project tests, including where tests live, how they relate to modules, and how they cover entities, errors, behavior, and CLI boundaries.

## Scope

The scope of this specification is limited to test organization and architectural testing expectations for Python code.

The following topics are out of scope:

- exact test framework configuration.
- exact fixture names.
- continuous integration configuration.
- package publishing checks.
- performance benchmarks.

## Dictionary

- `unit test` — a test focused on one module or one small group of closely related functions or entities.
- `integration test` — a test that checks multiple modules through a public boundary such as configuration loading, artifact loading, workflow execution, or CLI command execution.
- `fixture` — test data or setup used by one or more tests.
- `architecture test` — a test that verifies a project-wide convention from an architecture specification.
- `behavior example test` — a test that verifies an example or rule from a behavior specification.

## General principles

Tests MUST be written as part of the Python project.

Development-related test execution MUST happen through the project development container commands.

The preferred command form for running tests is:

```bash
./bin/dev.sh poetry run pytest
```

The preferred command form for running targeted tests is:

```bash
./bin/dev.sh poetry run pytest <path>
```

Tests SHOULD be deterministic for the same repository state and filesystem state.

Tests that require specific shared state MUST prepare that state at the start of the relevant test or with an autouse fixture at the test class or test module level.

Tests SHOULD prefer end-to-end coverage through public boundaries when that is practical for the behavior under test.

Tests SHOULD use mocks, stubs, and monkeypatching as little as possible.

Tests SHOULD prefer real project code, temporary files, explicit fixtures, and small fakes over mocked collaborators.

Tests MUST NOT depend on external network access.

Tests MUST NOT depend on user-specific files outside test-created temporary directories.

Tests MUST NOT modify Docker configuration or runtime parameters.

Tests SHOULD verify observable behavior and locally owned validation instead of implementation declarations such as annotations, imports, or exact helper types.

Tests SHOULD prefer separate tests for orthogonal execution paths or validation cases instead of one combined test that verifies all cases at once.

Static typing requirements SHOULD be enforced by static analysis, code review, or dedicated architecture checks, not by ordinary unit tests that inspect runtime annotations.

Tests MAY inspect annotations only in dedicated architecture tests that validate a broad project-wide convention.

Per-entity unit tests MUST NOT inspect annotations only to restate the entity declaration.

Tests MUST NOT use identity assertions except for `None` checks.

Tests MUST NOT use identity assertions for boolean values. Use `assert condition` instead of `assert condition is True`, and `assert not condition` instead of `assert condition is False`.

## Mocking

Tests SHOULD prefer real project code, explicit fixtures, test constructors, temporary files, and small fakes over mocks.

When a test must replace a Python collaborator, setting, method, or attribute, it SHOULD use the project-standard pytest mocking tool.

Patches SHOULD be scoped to the test that needs them and SHOULD patch the name as it is looked up by the code under test.

Use `mocker.patch("<import.path>", ...)` for imported module-level collaborators and settings when `pytest-mock` is available.

Use `mocker.patch.object(...)` when replacing an attribute on an object or class already available in the test.

Use direct `unittest.mock.MagicMock` only for local fake objects or callables that are passed into the code under test.

Tests SHOULD NOT use pytest `monkeypatch` for ordinary Python attribute replacement when the project-standard mocking fixture is available.

## Test module layout

Each implementation module or submodule SHOULD have corresponding tests under a `tests` submodule owned by the same parent module.

The name of a test file MUST be built from the name of the tested module by adding the `test_` prefix.

The structure of tests SHOULD mirror the implementation structure when that makes ownership clear.

Examples:

- `./donna/core/utils.py` -> `./donna/core/tests/test_utils.py`
- `./donna/domain/ids.py` -> `./donna/domain/tests/test_ids.py`
- `./donna/workspaces/config.py` -> `./donna/workspaces/tests/test_config.py`

Cross-module integration tests MAY live under the module that owns the public boundary being exercised.

CLI integration tests SHOULD live under `./donna/cli/tests/`.

Test data constructors reused by multiple test modules in the same package SHOULD live in `tests/make`.

`tests.make` SHOULD contain small factory functions that create valid entities, value objects, workflow artifacts, session state, and other project data for tests.

`tests.make` MUST NOT contain assertions or behavior-verification helpers.

Tests MAY reuse constructors, fixtures, and helpers from another module's `tests` package when that avoids duplicating
non-owned setup data or supports cross-module integration coverage.

Cross-module test helper reuse MUST remain test-only and MUST NOT make production modules depend on `tests` packages.

Test helper functions reused by multiple test modules in the same package SHOULD live in `tests/helpers`.

`tests.helpers` SHOULD contain assertion helpers, setup helpers, cleanup helpers, and test workflow utilities.

`tests.helpers` MUST NOT contain ordinary project data constructors when those constructors fit `tests.make`.

## Test organization

Tests SHOULD be organized around the tested function or tested class.

Each production module-level function MUST have a corresponding test class when the function owns non-trivial behavior.

Each class SHOULD have a corresponding test class when the class owns non-trivial behavior.

Test classes MUST use `Test<SubjectName>` naming, where `<SubjectName>` is the tested function or class name converted to PascalCase.

Examples:

- function `load_workspace` -> `class TestLoadWorkspace`.
- class `Artifact` -> `class TestArtifact`.
- class `ActionRequest` -> `class TestActionRequest`.

Tests for a class MUST group method tests inside the class's test class.

Tests for a class method MUST use this method name format:

```text
test_<method_name>__<test_name>
```

`<method_name>` MUST be the tested method name in snake case.

`<test_name>` MUST describe the execution path or behavior being verified in snake case.

Examples:

- `test_parse__invalid_value`.
- `test_validate_artifact__multiple_primary_sections`.
- `test_complete_action_request__invalid_transition`.

When a test class tests one module-level function, test methods MAY omit the function name and use this format:

```text
test_<test_name>
```

Examples:

- `TestLoadWorkspace.test_success`.
- `TestLoadWorkspace.test_config_not_found`.
- `TestNormalizePath.test_escapes_project_root`.

Test-only helper functions do not need corresponding test classes.

Standalone test functions SHOULD be used only for module-level invariants or file-level checks that do not naturally belong to one tested function or class.

Every meaningful execution path of a tested function or method MUST have a corresponding test method or parametrized test case.

Execution paths include:

- successful path.
- default-value path.
- empty-input path.
- invalid-input path.
- handled error path.
- warning-producing path.
- branch-specific path.

Tests MUST cover corner cases for each tested function or method.

Corner cases include:

- boundary values.
- empty collections and empty strings.
- missing optional values.
- duplicate values.
- unsupported values.
- malformed input.
- paths that do not exist.
- values that require normalization.
- repeated calls that may reveal state leaks.

## Entity tests

Entity tests SHOULD verify local invariants of entities.

Entity tests MUST verify behavior or invariants owned by the entity.

Entity tests SHOULD cover:

- entity-specific Pydantic field validation.
- entity-specific Pydantic model validation.
- non-trivial defaults or default factories.
- normalization behavior owned by the entity.
- entity-specific methods and properties.
- serialization or deserialization behavior owned by the entity.
- rejection of invalid values that the entity is responsible for rejecting.

Entity tests MUST NOT be added only to satisfy file-to-module layout symmetry.

Entity tests MUST NOT verify that constructor arguments are assigned to fields unchanged.

Entity tests MUST NOT verify simple Pydantic model construction when the entity has no custom validators, constrained fields, non-trivial defaults, normalization, serialization, computed properties, or entity-specific methods.

Entity tests MUST NOT verify plain `NewType`, enum member existence, or passive data-container fields unless the module owns non-trivial conversion, validation, serialization, persistence compatibility, protocol compatibility, or external-input compatibility behavior for them.

For entity-only modules that contain only passive entities, the absence of a matching `tests/test_<module>.py` file is acceptable and SHOULD be preferred over meaningless tests.

Entity tests SHOULD NOT test behavior inherited unchanged from the shared base entity.

Entity tests SHOULD NOT test trivial Pydantic behavior unless the entity customizes that behavior.

Entity tests MUST NOT require filesystem access unless the entity itself explicitly owns path normalization that depends on filesystem semantics.

Entity tests MUST NOT verify CLI rendering.

Entity tests MAY assert `pydantic.ValidationError` for invalid low-level model construction.

## Error tests

Error tests SHOULD verify behavior customized by concrete error classes.

### Testing `errors.py` modules

Error modules that contain only declarative error subclasses SHOULD NOT have unit tests solely for file-to-module layout symmetry.

Error class unit tests SHOULD be added only when the error class owns behavior beyond inherited construction and static class attributes.

Error class unit tests MAY cover:

- custom constructor logic.
- custom `content_intro()` behavior.
- custom validation or normalization.
- non-trivial structured metadata derivation.
- behavior added by an intermediate error class.

Leaf error tests MUST NOT assert only that class-level `code`, `message`, `ways_to_fix`, `cell_kind`, or constructor fields are present unchanged.

Exact production error message text MUST NOT be asserted in ordinary unit tests unless a behavior specification declares the text as a stable external contract.

Error tests SHOULD NOT test unchanged inheritance from project or module root error classes.

Error tests SHOULD NOT test behavior inherited unchanged from the shared base error class.

A module-level `tests/test_errors.py` file is optional.

A module-level `tests/test_errors.py` file SHOULD be omitted when all meaningful error behavior is already covered by tests for the functions or entities that produce those errors.

### Testing error-producing behavior

Tests for exception boundaries SHOULD verify that expected low-level failures are converted into Donna environment errors.

Tests for exception boundaries SHOULD verify that `pydantic.ValidationError` from external input is converted into Donna environment errors.

Tests for `Result`-returning functions SHOULD verify error values through `Result` state rather than by expecting environment errors to be raised.

Tests that verify produced environment errors SHOULD assert the expected error type, stable error code, and relevant structured fields through the behavior boundary that returns the error.

Internal error tests MAY assert raised `InternalError` subclasses when the tested behavior is an internal invariant.

CLI tests SHOULD verify that rendered environment errors use the expected Donna cell shape when command execution has entered Donna's protocol layer.

## Behavior coverage

Behavior specifications are the source of expected externally visible behavior.

Tests SHOULD cover examples and rules in behavior specifications when the corresponding behavior is implemented and runtime-testable.

Configuration tests SHOULD cover:

- configuration discovery.
- `--config` behavior.
- supported TOML structure.
- default values.
- path normalization.
- invalid configuration failures.
- journal command configuration.

Artifact and workflow tests SHOULD cover:

- artifact id normalization.
- artifact section id normalization.
- Markdown artifact parsing.
- workflow artifact validation.
- primitive resolution.
- workflow execution until finish, failure, or action request.
- action request completion and transition validation.

CLI tests SHOULD cover:

- command forms.
- option parsing.
- output protocol selection.
- command output cell shape.
- artifact listing and ordering.
- artifact rendering modes.
- validation selection with explicit artifact ids and `--all`.
- session status and details.
- errors and exit behavior.

Architecture specifications are the source of expected project-wide conventions.

Architecture tests SHOULD cover examples and rules in architecture specifications when the corresponding behavior is implemented and runtime-testable.

## Fixtures and temporary data

Tests that need files SHOULD create those files in temporary directories.

Tests SHOULD keep fixture data as small as possible while preserving the behavior being verified.

Inline fixture data SHOULD be preferred for short configuration files, short workflow artifacts, short Markdown inputs, and short expected outputs.

Reusable fixture files MAY be added when inline data would obscure the test.

Fixture paths SHOULD use forward slashes in expected normalized identifiers.

Tests that change the current working directory MUST restore it before the test ends.

Tests that modify process-level global state, context variables, protocol mode, installed workspace configuration, or mocks MUST restore them before the test ends.

## Assertions

Tests SHOULD assert structured values before rendered text when structured values are available.

Rendered output tests SHOULD assert exact output only for stable protocol, CLI, or persisted-state contracts.

Rendered output tests MAY assert selected lines, fields, or records when exact text is intentionally outside the relevant specification.

Automation protocol tests SHOULD parse JSON Lines output before asserting record contents.

Tests SHOULD assert both positive and negative outcomes when a branch is expected to exclude another branch.
