from collections.abc import Iterable

import typer

from donna.cli.application import app
from donna.cli.types import FullArtifactIdArgument, FullArtifactIdPatternOption, InputPathArgument, OutputPathOption
from donna.cli.utils import cells_cli, try_initialize_donna
from donna.domain.ids import FullArtifactIdPattern
from donna.protocol.cell_shortcuts import operation_succeeded
from donna.protocol.cells import Cell
from donna.world import artifacts as world_artifacts
from donna.world import tmp as world_tmp

artifacts_cli = typer.Typer()


@artifacts_cli.callback(invoke_without_command=True)
def initialize(ctx: typer.Context) -> None:
    cmd = ctx.invoked_subcommand

    if cmd is None:
        return

    try_initialize_donna()


@artifacts_cli.command(
    help="List artifacts matching a pattern and show their status summaries. Lists all all artifacts by default."
)
@cells_cli
def list(pattern: FullArtifactIdPatternOption = None) -> Iterable[Cell]:
    if pattern is None:
        pattern = FullArtifactIdPattern.parse("**").unwrap()

    artifacts = world_artifacts.list_artifacts(pattern).unwrap()

    return [artifact.node().status() for artifact in artifacts]


@artifacts_cli.command(help="Displays a single artifact.")
@cells_cli
def view(id: FullArtifactIdArgument) -> Iterable[Cell]:
    artifact = world_artifacts.load_artifact(id).unwrap()
    return [artifact.node().info()]


@artifacts_cli.command(
    help=(
        "Fetch an artifact source into a local file. When --output is omitted, "
        "a temporary file will be created in the project's temp directory."
    )
)
@cells_cli
def fetch(id: FullArtifactIdArgument, output: OutputPathOption = None) -> Iterable[Cell]:
    if output is None:
        extension = world_artifacts.artifact_file_extension(id).unwrap()
        output = world_tmp.file_for_artifact(id, extension)

    world_artifacts.fetch_artifact(id, output).unwrap()

    return [
        operation_succeeded(f"Artifact `{id}` fetched to '{output}'", artifact_id=str(id), output_path=str(output))
    ]


@artifacts_cli.command(help="Create or replace the artifact with the contents of a file.")
@cells_cli
def update(id: FullArtifactIdArgument, input: InputPathArgument) -> Iterable[Cell]:
    world_artifacts.update_artifact(id, input).unwrap()
    return [operation_succeeded(f"Artifact `{id}` updated from '{input}'", artifact_id=str(id), input_path=str(input))]


@artifacts_cli.command(help="Validate an artifact and return any validation errors.")
@cells_cli
def validate(id: FullArtifactIdArgument) -> Iterable[Cell]:
    artifact = world_artifacts.load_artifact(id).unwrap()

    artifact.validate_artifact().unwrap()

    return [operation_succeeded(f"Artifact `{id}` is valid", artifact_id=str(id))]


@artifacts_cli.command(
    help="Validate all artifacts matching a pattern (defaults to all artifacts) and return any errors."
)
@cells_cli
def validate_all(pattern: FullArtifactIdPatternOption = None) -> Iterable[Cell]:  # noqa: CCR001
    if pattern is None:
        pattern = FullArtifactIdPattern.parse("**").unwrap()

    artifacts = world_artifacts.list_artifacts(pattern).unwrap()

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
