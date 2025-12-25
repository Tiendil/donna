import pathlib
import shutil
from tempfile import NamedTemporaryFile

import pydantic

from donna.machine.cells import AgentArtifact, AgentCellHistory
from donna.core.entities import BaseEntity
from donna.world.layout import layout
from donna.domain.types import ArtifactId, StoryId


class ArtifactIndexItem(BaseEntity):
    id: ArtifactId
    content_type: str
    description: str


class Artifact(BaseEntity):
    story_id: StoryId
    item: ArtifactIndexItem
    content: str

    @classmethod
    def build(cls, story_id: StoryId, item: ArtifactIndexItem) -> "Artifact":
        content = layout().story_artifact(story_id, item.id).read_text()

        return Artifact(story_id=story_id, item=item, content=content)

    def cells(self) -> list[AgentCellHistory]:
        return [
            AgentArtifact(
                artifact_id=self.item.id,
                story_id=self.story_id,
                task_id=None,
                work_unit_id=None,
                content_type=self.item.content_type,
                description=self.item.description,
                content=self.content,
            ).render()
        ]


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

    def artifact_path(self, artifact_id: ArtifactId) -> pathlib.Path:
        if not self.has(artifact_id):
            raise NotImplementedError(f"Artifact with id '{artifact_id}' does not exist in story '{self.story_id}'")

        return layout().story_artifact(self.story_id, artifact_id)

    def _remove_artifact(self, artifact_id: ArtifactId) -> None:
        path = self.artifact_path(artifact_id)
        self.artifacts = [artifact for artifact in self.artifacts if artifact.id != artifact_id]
        path.unlink()

    def add_text(
        self,
        id: ArtifactId,
        content_type: str,
        description: str,
        content: str,
        rewrite: bool,
    ) -> None:
        with NamedTemporaryFile("w+", delete=True) as temp_f:
            temp_f.write(content)
            temp_f.flush()

            self.add_artifact(
                id=id,
                content_type=content_type,
                description=description,
                path=pathlib.Path(temp_f.name),
                rewrite=rewrite,
            )

    def add_artifact(
        self,
        id: ArtifactId,
        content_type: str,
        description: str,
        path: pathlib.Path,
        rewrite: bool,
    ) -> None:
        if not path.exists():
            raise NotImplementedError(f"Path '{path}' does not exist")

        if self.has(id):
            if not rewrite:
                raise NotImplementedError(f"Artifact with id '{id}' already exists in story '{self.story_id}'")

            self._remove_artifact(id)

        item = ArtifactIndexItem(id=id, content_type=content_type, description=description)

        self.artifacts.append(item)

        layout().story_artifact(self.story_id, id).write_bytes(path.read_bytes())

    def get_artifact(self, artifact_id: ArtifactId) -> Artifact:
        item = self.get(artifact_id)

        if item is None:
            raise NotImplementedError(f"Artifact with id '{artifact_id}' does not exist in story '{self.story_id}'")

        return Artifact.build(self.story_id, item)

    def extract_to(self, artifact_id: ArtifactId, path: pathlib.Path, rewrite: bool) -> None:
        if not self.has(artifact_id):
            raise NotImplementedError(f"Artifact with id '{artifact_id}' does not exist in story '{self.story_id}'")

        if path.exists() and not rewrite:
            raise NotImplementedError(f"Path '{path}' already exists")

        shutil.copy2(layout().story_artifact(self.story_id, artifact_id), path)
