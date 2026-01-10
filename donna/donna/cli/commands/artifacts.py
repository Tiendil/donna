import typer

from donna.cli.application import app
from donna.cli.types import FullArtifactIdArgument, NamespaceIdArgument
from donna.cli.utils import output_cells
from donna.world import navigator
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
    artifact = navigator.get_artifact(id)

    artifact_kind = register().artifacts.get(artifact.info.kind)

    if artifact_kind is None:
        raise RuntimeError(f"Artifact kind '{artifact.info.kind}' is not registered.")

    output_cells(artifact_kind.validate_artifact(artifact))


@artifacts_cli.command()
def validate_all(namespace: NamespaceIdArgument) -> None:
    artifacts = navigator.list_artifacts(namespace)

    for artifact in artifacts:
        artifact_kind = register().artifacts.get(artifact.info.kind)
        if artifact_kind is None:
            raise RuntimeError(f"Artifact kind '{artifact.info.kind}' is not registered.")

        output_cells(artifact_kind.validate_artifact(artifact))


app.add_typer(artifacts_cli, name="artifacts", help="Manage artifacts")
