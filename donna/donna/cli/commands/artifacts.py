import typer

from donna.cli.application import app
from donna.cli.types import FullArtifactIdArgument, NamespaceIdArgument
from donna.cli.utils import output_cells
from donna.world import navigator
from donna.world.templates import render_mode, RenderMode
from donna.world.primitives_register import register

artifacts_cli = typer.Typer()


@artifacts_cli.command()
def list(namespace: NamespaceIdArgument) -> None:
    artifacts = navigator.list_artifacts(namespace)

    for artifact in artifacts:
        output_cells(artifact.info.cells())


@artifacts_cli.command()
def get(id: FullArtifactIdArgument) -> None:
    artifact = navigator.get_artifact(id)
    output_cells(artifact.cells())


@artifacts_cli.command()
def validate(id: FullArtifactIdArgument) -> None:
    with render_mode(RenderMode.analysis):
        artifact = navigator.get_artifact(id)

        artifact_kind = register().artifacts.get(artifact.info.kind)

        output_cells(artifact_kind.validate(artifact))


@artifacts_cli.command()
def validate_all(namespace: NamespaceIdArgument) -> None:
    with render_mode(RenderMode.analysis):
        artifacts = navigator.list_artifacts(namespace)

        for artifact in artifacts:
            artifact_kind = register().artifacts.get(artifact.info.kind)
            output_cells(artifact_kind.validate(artifact))


app.add_typer(artifacts_cli, name="artifacts", help="Manage artifacts")
