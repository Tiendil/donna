import typer

from donna.cli.application import app
from donna.cli.utils import output_cells
from donna.world import navigator

artifacts_cli = typer.Typer()


@artifacts_cli.command()
def list(kind: str) -> None:
    artifacts = navigator.list_artifacts(kind)

    for artifact in artifacts:
        output_cells(artifact.info.cells())


@artifacts_cli.command()
def get(id: str) -> None:
    artifact = navigator.get_artifact(id)
    output_cells(artifact.cells())


app.add_typer(artifacts_cli, name="artifacts", help="Manage artifacts")
