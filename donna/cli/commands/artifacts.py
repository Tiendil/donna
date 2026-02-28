import builtins
import pathlib
import sys
from collections.abc import Iterable

import typer

from donna.cli import errors as cli_errors
from donna.cli.application import app
from donna.cli.types import (
    ExtensionOption,
    FullArtifactIdArgument,
    FullArtifactIdPatternArgument,
    InputPathArgument,
    OutputPathOption,
    TagOption,
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


def _log_operation_on_artifacts(message: str, pattern: FullArtifactIdPattern, tags: TagOption | None) -> None:
    if not tags:
        return _log_artifact_operation(f"{message} `{pattern}`")

    tags_list = ", ".join(f"'{tag}'" for tag in tags)

    return _log_artifact_operation(f"{message} `{pattern}` with tags {tags_list}")


@artifacts_cli.command(
    help="List artifacts matching a pattern and show their status summaries. Lists all all artifacts by default."
)
@cells_cli
def list(
    pattern: FullArtifactIdPatternArgument = DEFAULT_ARTIFACT_PATTERN,
    tags: TagOption = None,
) -> Iterable[Cell]:
    _log_operation_on_artifacts("List artifacts", pattern, tags)

    artifacts = context().artifacts.list(pattern, tags=tags).unwrap()

    return [artifact.node().status() for artifact in artifacts]


@artifacts_cli.command(help="Displays artifacts matching a pattern or a specific id")
@cells_cli
def view(
    pattern: FullArtifactIdPatternArgument,
    tags: TagOption = None,
) -> Iterable[Cell]:
    _log_operation_on_artifacts("View artifacts", pattern, tags)

    artifacts = context().artifacts.list(pattern, tags=tags).unwrap()
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


@artifacts_cli.command(
    help="Create a temporary file for artifact-related work and print its path. Use it to create new artifacts"
)
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


@artifacts_cli.command(help="Create or replace an artifact from a file path or stdin.")
@cells_cli
def update(
    id: FullArtifactIdArgument,
    input: InputPathArgument,
    extension: ExtensionOption = None,
) -> Iterable[Cell]:
    if input == pathlib.Path("-"):
        tmp_extension = extension or "tmp"
        input_path = world_tmp.file_for_artifact(id, tmp_extension)
        input_path.write_bytes(sys.stdin.buffer.read())
        input_display = "stdin"
    else:
        input_path = input
        input_display = str(input)

    _log_artifact_operation(f"Update artifact `{id}` from '{input_display}'")

    context().artifacts.update(id, input_path, extension=extension).unwrap()
    return [
        operation_succeeded(
            f"Artifact `{id}` updated from '{input_display}'",
            artifact_id=str(id),
            input_path=str(input_path),
        )
    ]


@artifacts_cli.command(help="Copy an artifact to another artifact ID (possibly across worlds).")
@cells_cli
def copy(source_id: FullArtifactIdArgument, target_id: FullArtifactIdArgument) -> Iterable[Cell]:
    _log_artifact_operation(f"Copy artifact from `{source_id}` to `{target_id}`")

    context().artifacts.copy(source_id, target_id).unwrap()
    return [
        operation_succeeded(
            f"Artifact `{source_id}` copied to `{target_id}`",
            source_id=str(source_id),
            target_id=str(target_id),
        )
    ]


@artifacts_cli.command(help="Move an artifact to another artifact ID (possibly across worlds).")
@cells_cli
def move(source_id: FullArtifactIdArgument, target_id: FullArtifactIdArgument) -> Iterable[Cell]:
    _log_artifact_operation(f"Move artifact from `{source_id}` to `{target_id}`")

    context().artifacts.move(source_id, target_id).unwrap()
    return [
        operation_succeeded(
            f"Artifact `{source_id}` moved to `{target_id}`",
            source_id=str(source_id),
            target_id=str(target_id),
        )
    ]


@artifacts_cli.command(help="Remove artifacts matching a pattern.")
@cells_cli
def remove(
    pattern: FullArtifactIdPatternArgument,
    tags: TagOption = None,
) -> Iterable[Cell]:
    _log_operation_on_artifacts("Remove artifacts", pattern, tags)

    artifacts = context().artifacts.list(pattern, tags=tags).unwrap()

    cells: builtins.list[Cell] = []
    for artifact in artifacts:
        context().artifacts.remove(artifact.id).unwrap()
        cells.append(operation_succeeded(f"Artifact `{artifact.id}` removed", artifact_id=str(artifact.id)))

    return cells


@artifacts_cli.command(help="Validate artifacts matching a pattern (defaults to all artifacts) and return any errors.")
@cells_cli
def validate(
    pattern: FullArtifactIdPatternArgument = DEFAULT_ARTIFACT_PATTERN,
    tags: TagOption = None,
) -> Iterable[Cell]:  # noqa: CCR001
    _log_operation_on_artifacts("Validate artifacts", pattern, tags)

    artifacts = context().artifacts.list(pattern, tags=tags).unwrap()

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
    help="Inspect, fetch, update, and validate stored artifacts across all Donna worlds.",
)
