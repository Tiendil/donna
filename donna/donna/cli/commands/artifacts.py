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
