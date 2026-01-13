import typer

from donna.cli.application import app
from donna.cli.types import ActionRequestIdArgument, FullArtifactIdArgument, FullArtifactLocalIdArgument
from donna.cli.utils import output_cells
from donna.domain.ids import WorldId
from donna.machine import sessions
from donna.machine.state import State
from donna.world.config import config

sessions_cli = typer.Typer()


@sessions_cli.command()
def start() -> None:
    output_cells(sessions.start())


@sessions_cli.command(name="continue")
def continue_() -> None:
    output_cells(sessions.continue_())


@sessions_cli.command()
def status() -> None:
    output_cells(sessions.status())


@sessions_cli.command()
def run(workflow_id: FullArtifactIdArgument) -> None:
    sessions.start_workflow(workflow_id)

    state = State.load()

    output_cells(state.run())


@sessions_cli.command()
def action_request_completed(
    request_id: ActionRequestIdArgument, next_operation_id: FullArtifactLocalIdArgument
) -> None:
    state = State.load()

    state.complete_action_request(request_id, next_operation_id)

    output_cells(state.run())


@sessions_cli.command()
def clear() -> None:
    config().get_world(WorldId("session")).initialize(reset=True)


app.add_typer(sessions_cli, name="sessions", help="Manage current session")
