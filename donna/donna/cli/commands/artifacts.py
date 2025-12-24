import pathlib

import typer

from donna.artifacts import domain as artifacts_domain
from donna.cli.application import app
from donna.cli.utils import output_cells
from donna.domain.types import ArtifactId, StoryId

artifacts_cli = typer.Typer()


# TODO: it is under a question if we need command to remove an artifact
#       since an artifact is a kind of history of a story
#       in most cases we may want to remove all the story


@artifacts_cli.command()
def list(story_id: str) -> None:
    index = artifacts_domain.ArtifactsIndex.load(StoryId(story_id))
    output_cells(index.cells())


@artifacts_cli.command()
def write(story_id: str, artifact_id: str, content_type: str, description: str, content: str) -> None:
    index = artifacts_domain.ArtifactsIndex.load(StoryId(story_id))

    index.add_text(
        id=ArtifactId(artifact_id),
        content_type=content_type,
        description=description,
        content=content,
        rewrite=True,
    )

    index.save()


@artifacts_cli.command()
def read(story_id: str, artifact_id: str) -> None:
    index = artifacts_domain.ArtifactsIndex.load(StoryId(story_id))

    artifact = index.get_artifact(ArtifactId(artifact_id))

    output_cells(artifact.cells())


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
    content_type: str,
    description: str,
    path: pathlib.Path,
) -> None:
    index = artifacts_domain.ArtifactsIndex.load(StoryId(story_id))

    index.add_artifact(
        id=ArtifactId(artifact_id),
        content_type=content_type,
        description=description,
        path=path,
        rewrite=True,
    )

    index.save()


@artifacts_cli.command()
def copy_from_story(story_id: str, artifact_id: str, path: pathlib.Path) -> None:
    index = artifacts_domain.ArtifactsIndex.load(StoryId(story_id))

    index.extract_to(artifact_id=ArtifactId(artifact_id), path=path, rewrite=True)


app.add_typer(artifacts_cli, name="artifacts", help="Manage artifacts")
