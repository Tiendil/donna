import typer

from donna.cli.application import app
from donna.cli.utils import output_cells
from donna.domain import types
from donna.domain.types import SpecificationId
from donna.world.primitives_register import register

specifications_cli = typer.Typer()


# TODO: we may add filter by specification's namespace here
@specifications_cli.command()
def list() -> None:
    for source in register().specifications.values():
        for item in source.list_specifications():
            output_cells(item.cells())


@specifications_cli.command()
def get(
    specification_id: str,
) -> None:
    for source in register().specifications.values():
        specification = source.get_specification(
            SpecificationId(types.NestedId(specification_id)),
        )
        if specification is not None:
            output_cells(specification.cells())
            return

    typer.echo(f"Specification '{specification_id}' not found.", err=True)
    raise typer.Exit(code=1)


app.add_typer(specifications_cli, name="specifications", help="Manage specifications")
