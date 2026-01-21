import pathlib

import typer

from donna.cli.application import app
from donna.cli.types import ArtifactPrefixArgument, FullArtifactIdArgument
from donna.cli.utils import output_cells
from donna.machine.artifacts import ArtifactKindSectionMeta, resolve
from donna.world import artifacts as world_artifacts

artifacts_cli = typer.Typer()


@artifacts_cli.command()
def list(prefix: ArtifactPrefixArgument) -> None:
    artifacts = world_artifacts.list_artifacts(prefix)

    for artifact in artifacts:
        output_cells(artifact.cells())


@artifacts_cli.command()
def view(id: FullArtifactIdArgument) -> None:
    artifact = world_artifacts.load_artifact(id)
    output_cells(artifact.cells())


@artifacts_cli.command()
def fetch(id: FullArtifactIdArgument, output: pathlib.Path) -> None:
    world_artifacts.fetch_artifact(id, output)
    typer.echo(f"Artifact `{id}` fetched to '{output}'")


@artifacts_cli.command()
def update(id: FullArtifactIdArgument, input: pathlib.Path) -> None:
    world_artifacts.update_artifact(id, input)
    typer.echo(f"Artifact `{id}` updated from '{input}'")


@artifacts_cli.command()
def validate(id: FullArtifactIdArgument) -> None:
    artifact = world_artifacts.load_artifact(id)

    section = resolve(artifact.kind)
    if not isinstance(section.meta, ArtifactKindSectionMeta):
        raise NotImplementedError(f"Artifact kind '{artifact.kind}' is not available")
    artifact_kind = section.meta.artifact_kind

    _is_valid, cells = artifact_kind.validate_artifact(artifact)

    output_cells(cells)


@artifacts_cli.command()
def validate_all(prefix: ArtifactPrefixArgument) -> None:
    artifacts = world_artifacts.list_artifacts(prefix)

    for artifact in artifacts:
        section = resolve(artifact.kind)
        if not isinstance(section.meta, ArtifactKindSectionMeta):
            raise NotImplementedError(f"Artifact kind '{artifact.kind}' is not available")
        artifact_kind = section.meta.artifact_kind

        _is_valid, cells = artifact_kind.validate_artifact(artifact)

        output_cells(cells)


app.add_typer(artifacts_cli, name="artifacts", help="Manage artifacts")
