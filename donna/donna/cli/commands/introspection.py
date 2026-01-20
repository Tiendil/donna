import typer

from donna.cli.application import app
from donna.cli.utils import output_cells
from donna.domain.ids import FullArtifactLocalId
from donna.machine.artifacts import resolve_artifact_kind

introspection_cli = typer.Typer()


@introspection_cli.command()
def show(id: str) -> None:
    primitive_id = FullArtifactLocalId.parse(id)
    primitive = resolve_artifact_kind(primitive_id)
    output_cells(primitive.cells())


app.add_typer(introspection_cli, name="introspection", help="Introspection commands")
