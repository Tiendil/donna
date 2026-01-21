import typer

from donna.cli.application import app
from donna.cli.utils import output_cells
from donna.domain.ids import FullArtifactLocalId
from donna.world import artifacts as world_artifacts

introspection_cli = typer.Typer()


@introspection_cli.command()
def show(id: str) -> None:
    primitive_id = FullArtifactLocalId.parse(id)
    artifact = world_artifacts.load_artifact(primitive_id.full_artifact_id)
    section = artifact.get_section(primitive_id)

    if section is None:
        raise NotImplementedError(f"Primitive '{primitive_id}' is not available")

    output_cells(section.cells())


app.add_typer(introspection_cli, name="introspection", help="Introspection commands")
