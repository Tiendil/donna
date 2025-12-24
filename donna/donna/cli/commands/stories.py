import re

import typer
import shutil
from donna.cli.application import app
from donna.cli.types import ActionRequestIdArgument
from donna.cli.utils import output_cells
from donna.domain.types import OperationId, OperationResultId, Slug, StoryId
from donna.stories import domain
from donna.workflows.operations import storage
from donna.domain.layout import layout

SLUG_PATTERN = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")


stories_cli = typer.Typer()


@stories_cli.command()
def create(slug: str) -> None:
    if not SLUG_PATTERN.match(slug):
        typer.echo(
            "Error: Slug must consist of lowercase letters, numbers, and hyphens only.",
            err=True,
        )
        raise typer.Exit(code=1)

    story = domain.create_story(Slug(slug))

    output_cells([cell.render() for cell in story.cells()])


@stories_cli.command(name="continue")
def _continue(story_id: str) -> None:
    story = domain.get_story(StoryId(story_id))

    plan = domain.Plan.load(story.id)

    output_cells(plan.run())


@stories_cli.command()
def action_request_completed(request_id: ActionRequestIdArgument, result_id: str) -> None:
    story_id = domain.find_action_request_story(request_id)

    plan = domain.Plan.load(story_id)

    plan.complete_action_request(request_id, OperationResultId(result_id))

    output_cells(plan.run())


@stories_cli.command()
def list_workflows() -> None:
    cells = [cell.render() for cell in storage().workflow_cells()]
    output_cells(cells)


@stories_cli.command()
def start_workflow(story_id: str, workflow_id: str) -> None:
    domain.start_workflow(StoryId(story_id), OperationId(workflow_id))

    plan = domain.Plan.load(StoryId(story_id))

    output_cells(plan.run())


@stories_cli.command()
def remove_all() -> None:
    shutil.rmtree(layout().stories)


app.add_typer(stories_cli, name="stories", help="Manage stories")
