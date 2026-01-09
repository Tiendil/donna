import re
import shutil

import typer

from donna.cli.application import app
from donna.cli.types import ActionRequestIdArgument, SlugArgument, StoryIdArgument
from donna.cli.utils import output_cells
from donna.domain import types
from donna.domain.types import OperationResultId
from donna.machine import sessions
from donna.world.layout import layout
from donna.machine.plans import Plan, get_plan


sessions_cli = typer.Typer()


@sessions_cli.command()
def start() -> None:
    story = sessions.start()
    typer.echo(f"Started new story: {story.id}")


@sessions_cli.command(name="continue")
def _continue() -> None:
    plan = Plan.load()
    output_cells(plan.run())


@sessions_cli.command()
def action_request_completed(request_id: ActionRequestIdArgument, result_id: str) -> None:
    plan = Plan.load()

    plan.complete_action_request(request_id, OperationResultId(types.slug_parser(result_id)))

    output_cells(plan.run())


@sessions_cli.command()
def clear() -> None:
    shutil.rmtree(layout().session)


app.add_typer(sessions_cli, name="sessions", help="Manage current session")
