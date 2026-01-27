import pathlib

import typer

from donna.cli.application import app
from donna.cli.types import FullArtifactIdArgument, FullArtifactIdPatternOption
from donna.cli.utils import output_cells
from donna.domain.ids import FullArtifactIdPattern
from donna.protocol.cell_shortcuts import operation_succeeded
from donna.world import artifacts as world_artifacts
from donna.world import tmp as world_tmp

artifacts_cli = typer.Typer()


@artifacts_cli.command()
def list(pattern: FullArtifactIdPatternOption = None) -> None:
    if pattern is None:
        pattern = FullArtifactIdPattern.parse("**")

    artifacts = world_artifacts.list_artifacts(pattern)

    for artifact in artifacts:
        output_cells(artifact.cells_info())


@artifacts_cli.command()
def view(id: FullArtifactIdArgument) -> None:
    artifact = world_artifacts.load_artifact(id)
    output_cells(artifact.cells())


@artifacts_cli.command()
def fetch(id: FullArtifactIdArgument, output: pathlib.Path | None = None) -> None:
    if output is None:
        output = world_tmp.file_for_artifact(id, world_artifacts.artifact_file_extension(id))

    world_artifacts.fetch_artifact(id, output)

    output_cells(
        [operation_succeeded(f"Artifact `{id}` fetched to '{output}'", artifact_id=str(id), output_path=str(output))]
    )


@artifacts_cli.command()
def update(id: FullArtifactIdArgument, input: pathlib.Path) -> None:
    world_artifacts.update_artifact(id, input)
    output_cells(
        [operation_succeeded(f"Artifact `{id}` updated from '{input}'", artifact_id=str(id), input_path=str(input))]
    )


@artifacts_cli.command()
def validate(id: FullArtifactIdArgument) -> None:
    artifact = world_artifacts.load_artifact(id)

    result = artifact.validate_artifact()

    if result.is_err():
        errors = result.unwrap_err()
        output_cells([error.cell() for error in errors])
        return

    output_cells([operation_succeeded(f"Artifact `{id}` is valid", artifact_id=str(id))])


@artifacts_cli.command()
def validate_all(pattern: FullArtifactIdPatternOption = None) -> None:
    if pattern is None:
        pattern = FullArtifactIdPattern.parse("**")

    artifacts = world_artifacts.list_artifacts(pattern)

    errors = []

    for artifact in artifacts:
        result = artifact.validate_artifact()
        if result.is_err():
            errors.extend(result.unwrap_err())

    if errors:
        output_cells([error.cell() for error in errors])
        return

    output_cells([operation_succeeded("All artifacts are valid")])


app.add_typer(artifacts_cli, name="artifacts", help="Manage artifacts")
