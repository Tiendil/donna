from typing import Any

import pydantic

from donna.world.artifact_source import ArtifactSource
from donna.core.entities import BaseEntity
from donna.domain.types import RecordId, RecordKindId, StoryId
from donna.machine.cells import Cell
from donna.world.layout import layout


class ArtifactKind(BaseEntity):
    id: str
    description: str
    namespace: str

    def cells(self) -> list[Cell]:
        return [Cell.build_meta(kind="artifact_kind",
                                id=self.id,
                                namespace=self.namespace,
                                description=self.description)]

    def construct(self, source: ArtifactSource) -> 'Artifact':
        raise NotImplementedError("You must implement this method in subclasses")


class ArtifactInfo(BaseEntity):
    kind: str
    world_id: str
    id: str
    title: str
    description: str

    def cells(self) -> list[Cell]:
        return [Cell.build_meta(kind="artifact_info",
                                id=self.id,
                                world_id=self.world_id,
                                title=self.title,
                                description=self.description)]


class Artifact(BaseEntity):
    info: ArtifactInfo

    def cells(self) -> list[Cell]:
        raise NotImplementedError("You must implement this method in subclasses")
