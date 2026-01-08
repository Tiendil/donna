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
from donna.world import navigator

artifacts_cli = typer.Typer()


# TODO: implement
# @artifacts_cli.command()
# def list(story_id: StoryIdArgument) -> None:
#     index = r_domain.RecordsIndex.load(StoryId(story_id))
#     output_cells(index.cells())


@artifacts_cli.command()
def get(id: str) -> None:
    artifact = navigator.get(id)

    print(artifact)


app.add_typer(artifacts_cli, name="artifacts", help="Manage artifacts")
