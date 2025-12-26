import pathlib

import typer
from donna.world.primitives_register import register
from donna.cli.application import app
from donna.cli.utils import output_cells
from donna.domain.types import ArtifactId, StoryId, ArtifactKindId
from donna.machine import artifacts as artifacts_domain

artifacts_cli = typer.Typer()


# TODO: it is under a question if we need command to remove an artifact
#       since an artifact is a kind of history of a story
#       in most cases we may want to remove all the story


@artifacts_cli.callback()
def artifacts_callback() -> None:
    for artifact in register().artifacts.values():
        kind_cli = artifact.create_cli_commands()
        artifacts_cli.add_typer(
            kind_cli,
            name=artifact.id,
            help=f'Commands to manage "{artifact.id}" artifacts',
        )


@artifacts_cli.command()
def list(story_id: str) -> None:
    index = artifacts_domain.ArtifactsIndex.load(StoryId(story_id))
    output_cells(index.cells())


@artifacts_cli.command()
def create(story_id: str, artifact_kind: str, artifact_id: str, content_type: str, description: str) -> None:
    index = artifacts_domain.ArtifactsIndex.load(StoryId(story_id))

    index.add(
        id=ArtifactId(artifact_id),
        kind=ArtifactKindId(artifact_kind),
        content_type=content_type,
        description=description
    )

    index.save()

    typer.echo(f'artifact "{artifact_id}" created')


@artifacts_cli.command()
def has(story_id: str, artifact_id: str) -> None:
    index = artifacts_domain.ArtifactsIndex.load(StoryId(story_id))

    # TODO: output cell?
    if index.has(ArtifactId(artifact_id)):
        typer.echo(f'artifact "{artifact_id}" exists')

    else:
        typer.echo(f'artifact "{artifact_id}" does not exist')


@artifacts_cli.command()
def copy_into_story(
    story_id: str,
    artifact_id: str,
    path: pathlib.Path,
) -> None:
    index = artifacts_domain.ArtifactsIndex.load(StoryId(story_id))

    index.copy_to_story(artifact_id=ArtifactId(artifact_id), path=path, rewrite=True)


@artifacts_cli.command()
def copy_from_story(story_id: str, artifact_id: str, path: pathlib.Path) -> None:
    index = artifacts_domain.ArtifactsIndex.load(StoryId(story_id))

    index.copy_from_story(artifact_id=ArtifactId(artifact_id), path=path, rewrite=True)


app.add_typer(artifacts_cli, name="artifacts", help="Manage artifacts")
