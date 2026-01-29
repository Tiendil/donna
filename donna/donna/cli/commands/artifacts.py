import pathlib
from collections.abc import Iterable

import typer

from donna.cli.application import app
from donna.cli.types import FullArtifactIdArgument, FullArtifactIdPatternOption
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


@artifacts_cli.command()
@cells_cli
def list(pattern: FullArtifactIdPatternOption = None) -> Iterable[Cell]:
    if pattern is None:
        pattern_result = FullArtifactIdPattern.parse("**")
        if pattern_result.is_err():
            errors = pattern_result.unwrap_err()
            return [error.node().info() for error in errors]

        pattern = pattern_result.unwrap()

    artifacts_result = world_artifacts.list_artifacts(pattern)
    if artifacts_result.is_err():
        errors = artifacts_result.unwrap_err()
        return [error.node().info() for error in errors]

    return [artifact.node().status() for artifact in artifacts_result.unwrap()]


@artifacts_cli.command()
@cells_cli
def view(id: FullArtifactIdArgument) -> Iterable[Cell]:
    artifact_result = world_artifacts.load_artifact(id)
    if artifact_result.is_err():
        errors = artifact_result.unwrap_err()
        return [error.node().info() for error in errors]

    return [artifact_result.unwrap().node().info()]


@artifacts_cli.command()
@cells_cli
def fetch(id: FullArtifactIdArgument, output: pathlib.Path | None = None) -> Iterable[Cell]:
    if output is None:
        extension_result = world_artifacts.artifact_file_extension(id)
        if extension_result.is_err():
            errors = extension_result.unwrap_err()
            return [error.node().info() for error in errors]

        output = world_tmp.file_for_artifact(id, extension_result.unwrap())

    fetch_result = world_artifacts.fetch_artifact(id, output)
    if fetch_result.is_err():
        errors = fetch_result.unwrap_err()
        return [error.node().info() for error in errors]

    return [
        operation_succeeded(f"Artifact `{id}` fetched to '{output}'", artifact_id=str(id), output_path=str(output))
    ]


@artifacts_cli.command()
@cells_cli
def update(id: FullArtifactIdArgument, input: pathlib.Path) -> Iterable[Cell]:
    result = world_artifacts.update_artifact(id, input)
    if result.is_err():
        errors = result.unwrap_err()
        return [error.node().info() for error in errors]

    return [operation_succeeded(f"Artifact `{id}` updated from '{input}'", artifact_id=str(id), input_path=str(input))]


@artifacts_cli.command()
@cells_cli
def validate(id: FullArtifactIdArgument) -> Iterable[Cell]:
    artifact_result = world_artifacts.load_artifact(id)
    if artifact_result.is_err():
        errors = artifact_result.unwrap_err()
        return [error.node().info() for error in errors]

    result = artifact_result.unwrap().validate_artifact()

    if result.is_err():
        errors = result.unwrap_err()
        return [error.node().info() for error in errors]

    return [operation_succeeded(f"Artifact `{id}` is valid", artifact_id=str(id))]


@artifacts_cli.command()
@cells_cli
def validate_all(pattern: FullArtifactIdPatternOption = None) -> Iterable[Cell]:  # noqa: CCR001
    if pattern is None:
        pattern_result = FullArtifactIdPattern.parse("**")
        if pattern_result.is_err():
            errors = pattern_result.unwrap_err()
            return [error.node().info() for error in errors]

        pattern = pattern_result.unwrap()

    artifacts_result = world_artifacts.list_artifacts(pattern)
    if artifacts_result.is_err():
        errors = artifacts_result.unwrap_err()
        return [error.node().info() for error in errors]

    errors = []

    for artifact in artifacts_result.unwrap():
        result = artifact.validate_artifact()
        if result.is_err():
            errors.extend(result.unwrap_err())

    if errors:
        return [error.node().info() for error in errors]

    return [operation_succeeded("All artifacts are valid")]


app.add_typer(artifacts_cli, name="artifacts", help="Manage artifacts")
