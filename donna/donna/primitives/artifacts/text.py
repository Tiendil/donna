import typer
from tempfile import NamedTemporaryFile
from donna.domain.types import ArtifactId, StoryId, ArtifactKindId
from donna.machine.artifacts import ArtifactsIndex, Artifact, ArtifactKind
from donna.machine.cells import AgentArtifact, AgentCellHistory
from donna.cli.utils import output_cells


class TextArtifact(ArtifactKind):

    def load(self, story_id: StoryId, artifact_id: ArtifactId) -> Artifact:
        index = ArtifactsIndex.load(story_id)

        if not index.has(artifact_id):
            raise NotImplementedError(f'Artifact "{artifact_id}" does not exist in story "{story_id}"')

        item = index.get(artifact_id)

        path = index.artifact_path(artifact_id)

        return ArtifactContent(story_id=story_id, item=item, content=path.read_text())

    def create_cli_commands(self) -> None:
        cli = typer.Typer()

        @cli.command()
        def write(story_id: StoryId, artifact_id: ArtifactId, content: str) -> None:
            index = ArtifactsIndex.load(story_id)

            if not index.has(artifact_id):
                raise NotImplementedError(f'Artifact "{artifact_id}" does not exist in story "{story_id}"')

            path = index.artifact_path(artifact_id)

            with path.open("r") as f:
                f.write(content)
                f.flush()

            typer.echo(f'Wrote content to artifact "{artifact_id}" in story "{story_id}"')

        @cli.command()
        def read(story_id: StoryId, artifact_id: ArtifactId) -> None:
            index = ArtifactsIndex.load(story_id)

            if not index.has(artifact_id):
                raise NotImplementedError(f'Artifact "{artifact_id}" does not exist in story "{story_id}"')

            artifact = index.get_artifact(ArtifactId(artifact_id))

            output_cells(artifact.cells())

        return cli


class ArtifactContent(Artifact):
    content: str

    def cells(self) -> list[AgentCellHistory]:
        return [
            AgentArtifact(
                artifact_id=self.item.id,
                artifact_kind=self.item.kind,
                story_id=self.story_id,
                task_id=None,
                work_unit_id=None,
                content_type=self.item.content_type,
                description=self.item.description,
                content=self.content,
            ).render()
        ]
