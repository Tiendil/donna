from collections.abc import Iterable

import typer

from donna.cli.application import app
from donna.cli.types import (
    ArtifactIdPatternArgument,
    PredicateOption,
    validate_supported_artifact_pattern,
)
from donna.cli.utils import cells_cli
from donna.context.context import context
from donna.domain.artifact_ids import ArtifactIdPattern
from donna.machine import journal as machine_journal
from donna.protocol.cell_shortcuts import operation_succeeded
from donna.protocol.cells import Cell
from donna.workspaces.artifacts import RENDER_CONTEXT_VIEW

artifacts_cli = typer.Typer()

DEFAULT_ARTIFACT_PATTERN = ArtifactIdPattern.parse("**").unwrap()


def _log_artifact_operation(message: str) -> None:
    machine_journal.add(message=message)


def _log_operation_on_artifacts(
    message: str,
    pattern: ArtifactIdPattern,
    predicate: PredicateOption | None,
) -> None:
    if predicate is None:
        return _log_artifact_operation(f"{message} `{pattern}`")

    return _log_artifact_operation(f"{message} `{pattern}` with predicate `{predicate.source}`")


@artifacts_cli.command(
    help=(
        "List artifacts matching a pattern with a supported source extension "
        "and show their status summaries. Lists all artifacts by default."
    )
)
@cells_cli
def list(
    pattern: ArtifactIdPatternArgument = DEFAULT_ARTIFACT_PATTERN,
    predicate: PredicateOption = None,
) -> Iterable[Cell]:
    validate_supported_artifact_pattern(pattern)
    _log_operation_on_artifacts("List artifacts", pattern, predicate)

    artifacts = context().artifacts.list(pattern, RENDER_CONTEXT_VIEW, predicate=predicate).unwrap()

    return [artifact.node().status() for artifact in artifacts]


@artifacts_cli.command(
    help="Display artifacts matching a pattern or specific id that uses a supported source extension."
)
@cells_cli
def view(
    pattern: ArtifactIdPatternArgument,
    predicate: PredicateOption = None,
) -> Iterable[Cell]:
    validate_supported_artifact_pattern(pattern)
    _log_operation_on_artifacts("View artifacts", pattern, predicate)

    artifacts = context().artifacts.list(pattern, RENDER_CONTEXT_VIEW, predicate=predicate).unwrap()
    return [artifact.node().info() for artifact in artifacts]


@artifacts_cli.command(
    help=(
        "Validate artifacts matching a pattern with a supported source extension "
        "(defaults to all artifacts) and return any errors."
    )
)
@cells_cli
def validate(
    pattern: ArtifactIdPatternArgument = DEFAULT_ARTIFACT_PATTERN,
    predicate: PredicateOption = None,
) -> Iterable[Cell]:  # noqa: CCR001
    validate_supported_artifact_pattern(pattern)
    _log_operation_on_artifacts("Validate artifacts", pattern, predicate)

    artifacts = context().artifacts.list(pattern, RENDER_CONTEXT_VIEW, predicate=predicate).unwrap()

    errors = []

    for artifact in artifacts:
        result = artifact.validate_artifact()
        if result.is_err():
            errors.extend(result.unwrap_err())

    if errors:
        return [error.node().info() for error in errors]

    return [operation_succeeded("All artifacts are valid")]


app.add_typer(
    artifacts_cli,
    name="artifacts",
    help="Inspect and validate stored artifacts in the project workspace.",
)
