from collections.abc import Iterable

import typer

from donna.cli import errors as cli_errors
from donna.cli.application import app
from donna.cli.types import (
    FullArtifactIdArgument,
    FullArtifactIdPatternArgument,
    OutputPathOption,
    PredicateOption,
)
from donna.cli.utils import cells_cli
from donna.context.context import context
from donna.core.errors import ErrorsList
from donna.core.result import Err, Ok, Result
from donna.domain.ids import FullArtifactIdPattern
from donna.machine import journal as machine_journal
from donna.protocol.cell_shortcuts import operation_succeeded
from donna.protocol.cells import Cell
from donna.workspaces import tmp as world_tmp
from donna.workspaces.artifacts import RENDER_CONTEXT_VIEW

artifacts_cli = typer.Typer()

DEFAULT_ARTIFACT_PATTERN = FullArtifactIdPattern.parse("**").unwrap()


def _parse_slug_with_extension(value: str) -> Result[tuple[str, str], ErrorsList]:
    normalized = value.strip()
    if "." not in normalized:
        return Err([cli_errors.InvalidSlugWithExtension(value=normalized)])

    slug, extension = normalized.rsplit(".", 1)
    if not slug or not extension:
        return Err([cli_errors.InvalidSlugWithExtension(value=normalized)])

    return Ok((slug, extension))


def _log_artifact_operation(message: str) -> None:
    machine_journal.add(message=message)


def _log_operation_on_artifacts(
    message: str,
    pattern: FullArtifactIdPattern,
    predicate: PredicateOption | None,
) -> None:
    if predicate is None:
        return _log_artifact_operation(f"{message} `{pattern}`")

    return _log_artifact_operation(f"{message} `{pattern}` with predicate `{predicate.source}`")


@artifacts_cli.command(
    help="List artifacts matching a pattern and show their status summaries. Lists all all artifacts by default."
)
@cells_cli
def list(
    pattern: FullArtifactIdPatternArgument = DEFAULT_ARTIFACT_PATTERN,
    predicate: PredicateOption = None,
) -> Iterable[Cell]:
    _log_operation_on_artifacts("List artifacts", pattern, predicate)

    artifacts = context().artifacts.list(pattern, RENDER_CONTEXT_VIEW, predicate=predicate).unwrap()

    return [artifact.node().status() for artifact in artifacts]


@artifacts_cli.command(help="Displays artifacts matching a pattern or a specific id")
@cells_cli
def view(
    pattern: FullArtifactIdPatternArgument,
    predicate: PredicateOption = None,
) -> Iterable[Cell]:
    _log_operation_on_artifacts("View artifacts", pattern, predicate)

    artifacts = context().artifacts.list(pattern, RENDER_CONTEXT_VIEW, predicate=predicate).unwrap()
    return [artifact.node().info() for artifact in artifacts]


@artifacts_cli.command(
    help=(
        "Fetch an artifact source into a local file. When --output is omitted, "
        "a temporary file will be created in the project's temp directory."
    )
)
@cells_cli
def fetch(id: FullArtifactIdArgument, output: OutputPathOption = None) -> Iterable[Cell]:
    if output is None:
        extension = context().artifacts.file_extension(id).unwrap()
        output = world_tmp.file_for_artifact(id, extension)

    _log_artifact_operation(f"Fetch artifact `{id}` to '{output}'")

    context().artifacts.fetch(id, output).unwrap()

    return [
        operation_succeeded(f"Artifact `{id}` fetched to '{output}'", artifact_id=str(id), output_path=str(output))
    ]


@artifacts_cli.command(help="Create a temporary file for artifact-related work and print its path.")
@cells_cli
def tmp(
    slug_with_extension: str = typer.Argument(..., help="Temporary file slug with extension (example: 'draft.md').")
) -> Iterable[Cell]:
    slug, extension = _parse_slug_with_extension(slug_with_extension).unwrap()
    output = world_tmp.create_file_for_slug(slug, extension)

    _log_artifact_operation(f"Created temporary file {output}")

    return [
        operation_succeeded(
            f"Temporary file created at '{output}'",
            output_path=str(output),
        )
    ]


@artifacts_cli.command(help="Validate artifacts matching a pattern (defaults to all artifacts) and return any errors.")
@cells_cli
def validate(
    pattern: FullArtifactIdPatternArgument = DEFAULT_ARTIFACT_PATTERN,
    predicate: PredicateOption = None,
) -> Iterable[Cell]:  # noqa: CCR001
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
    help="Inspect, fetch, and validate stored artifacts across all Donna worlds.",
)
