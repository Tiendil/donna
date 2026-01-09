from typing import List

import typer

from donna.cli.application import app
from donna.cli.types import FullArtifactIdArgument
from donna.cli.utils import output_cells
from donna.machine import sessions
from donna.machine.cells import Cell
from donna.machine.plans import Plan
from donna.world.primitives_register import register

workflows_cli = typer.Typer()


@workflows_cli.command()
def start(artifact_id: FullArtifactIdArgument) -> None:
    sessions.start_workflow(artifact_id)

    plan = Plan.load()

    output_cells(plan.run())


app.add_typer(workflows_cli, name="workflows", help="Run workflows")
