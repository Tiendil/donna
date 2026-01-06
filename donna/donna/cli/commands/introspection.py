import typer

from donna.cli.application import app
from donna.cli.utils import output_cells
from donna.world.primitives_register import register

introspection_cli = typer.Typer()


@introspection_cli.command()
def show(id: str) -> None:
    primitive = register().find_primitive(id)

    if primitive is None:
        typer.echo(f'Primitive with id "{id}" not found.', err=True)
        raise typer.Exit(code=1)

    output_cells(primitive.cells())


app.add_typer(introspection_cli, name="introspection", help="Introspection commands")
