from typing import List

import typer

from donna.cli.application import app
from donna.cli.types import RecordIdArgument, StoryIdArgument
from donna.cli.utils import output_cells
from donna.domain import types
from donna.domain.ids import next_id
from donna.domain.types import RecordId, RecordKindId, StoryId
from donna.machine import records as r_domain
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
