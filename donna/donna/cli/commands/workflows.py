import re
import shutil

import typer

from donna.cli.application import app
from donna.cli.types import ActionRequestIdArgument, SlugArgument, StoryIdArgument, WorkflowIdArgument
from donna.cli.utils import output_cells
from donna.domain import types
from donna.domain.types import OperationId, OperationResultId
from donna.machine import stories
from donna.world.layout import layout
from donna.world.primitives_register import register


workflows_cli = typer.Typer()


@workflows_cli.command()
def list() -> None:
    cells = []

    for workflow in register().workflows.values():
        cells.extend(workflow.cells())

    output_cells(cells)


@workflows_cli.command()
def start(story_id: StoryIdArgument, workflow_id: WorkflowIdArgument) -> None:
    stories.start_workflow(story_id, workflow_id)

    plan = stories.Plan.load(story_id)

    output_cells(plan.run())


app.add_typer(workflows_cli, name="workflows", help="Run workflows")
