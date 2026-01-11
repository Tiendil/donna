import shutil

import typer

from donna.cli.application import app
from donna.cli.types import ActionRequestIdArgument, FullArtifactIdArgument, FullArtifactLocalIdArgument
from donna.cli.utils import output_cells
from donna.machine import sessions
from donna.machine.plans import Plan
from donna.world.config import config


sessions_cli = typer.Typer()


@sessions_cli.command()
def start() -> None:
    sessions.start()
    typer.echo(f"Started new session")


@sessions_cli.command(name="continue")
def _continue() -> None:
    sessions.start()

    plan = Plan.load()
    output_cells(plan.run())


@sessions_cli.command()
def status() -> None:
    sessions.start()

    plan = Plan.load()
    output_cells(plan.status_cells())


@sessions_cli.command()
def run(workflow_id: FullArtifactIdArgument) -> None:
    sessions.start_workflow(workflow_id)

    plan = Plan.load()

    output_cells(plan.run())


@sessions_cli.command()
def action_request_completed(
    request_id: ActionRequestIdArgument, next_operation_id: FullArtifactLocalIdArgument
) -> None:
    plan = Plan.load()

    plan.complete_action_request(request_id, next_operation_id)

    output_cells(plan.run())


@sessions_cli.command()
def clear() -> None:
    config().get_world("session").initialize(reset=True)


app.add_typer(sessions_cli, name="sessions", help="Manage current session")
