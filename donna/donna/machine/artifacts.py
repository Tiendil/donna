import pathlib
import shutil
from tempfile import NamedTemporaryFile

import typer
import pydantic

from donna.core.entities import BaseEntity
from donna.domain.types import ArtifactId, StoryId, ArtifactKindId
from donna.machine.cells import AgentArtifact, AgentCellHistory
from donna.world.layout import layout


class ArtifactKind(BaseEntity):
    id: ArtifactKindId

    def load(self, story_id: StoryId, artifact_id: ArtifactId) -> 'Artifact':
        raise NotImplementedError("You must implement this method in subclasses")

    def create_cli_commands(self) -> typer.Typer:
        raise NotImplementedError("You must implement this method in subclasses")


class ArtifactIndexItem(BaseEntity):
    id: ArtifactId
    kind: ArtifactKindId
    content_type: str
    description: str


class Artifact(BaseEntity):
    story_id: StoryId
    item: ArtifactIndexItem

    def cells(self) -> list[AgentCellHistory]:
        raise NotImplementedError("You must implement this method in subclasses")


class ArtifactsIndex(BaseEntity):
    story_id: StoryId
    artifacts: list[ArtifactIndexItem]

    # TODO: we may want to make queue items frozen later
    model_config = pydantic.ConfigDict(frozen=False)

    def cells(self) -> list[AgentCellHistory]:
        return [AgentCellHistory(work_unit_id=None, body=self.to_toml())]

    @classmethod
    def load(cls, story_id: StoryId) -> "ArtifactsIndex":
        return cls.from_toml(layout().story_artifacts_index(story_id).read_text())

    def save(self) -> None:
        layout().story_artifacts_index(self.story_id).write_text(self.to_toml())

    def has(self, artifact_id: ArtifactId) -> bool:
        return any(artifact.id == artifact_id for artifact in self.artifacts)

    def get(self, artifact_id: ArtifactId) -> ArtifactIndexItem | None:
        for artifact in self.artifacts:
            if artifact.id == artifact_id:
                return artifact

        return None

    def add(
        self,
        id: ArtifactId,
        content_type: str,
        description: str,
    ) -> None:
        if self.has(id):
            raise NotImplementedError(f"Artifact with id '{id}' already exists in story '{self.story_id}'")

        item = ArtifactIndexItem(id=id, content_type=content_type, description=description)

        self.artifacts.append(item)

        self.artifact_path(id).touch()

    def artifact_path(self, artifact_id: ArtifactId) -> pathlib.Path:
        if not self.has(artifact_id):
            raise NotImplementedError(f"Artifact with id '{artifact_id}' does not exist in story '{self.story_id}'")

        return layout().story_artifact(self.story_id, artifact_id)

    def _remove_artifact(self, artifact_id: ArtifactId) -> None:
        path = self.artifact_path(artifact_id)
        self.artifacts = [artifact for artifact in self.artifacts if artifact.id != artifact_id]
        path.unlink()

    def get_artifact(self, artifact_id: ArtifactId) -> Artifact:
        from donna.world.primitives_register import register

        item = self.get(artifact_id)

        if item is None:
            raise NotImplementedError(f"Artifact with id '{artifact_id}' does not exist in story '{self.story_id}'")

        return register().artifacts.get(item.kind).load(self.story_id, artifact_id)

    def copy_from_story(self, artifact_id: ArtifactId, path: pathlib.Path) -> None:
        if not self.has(artifact_id):
            raise NotImplementedError(f"Artifact with id '{artifact_id}' does not exist in story '{self.story_id}'")

        shutil.copy2(self.artifact_path(artifact_id), path)

    def copy_to_story(self, artifact_id: ArtifactId, path: pathlib.Path) -> None:
        if not self.has(artifact_id):
            raise NotImplementedError(f"Artifact with id '{artifact_id}' does not exist in story '{self.story_id}'")

        shutil.copy2(path, self.artifact_path(artifact_id))
