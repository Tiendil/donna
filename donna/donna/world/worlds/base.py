from __future__ import annotations

from typing import TYPE_CHECKING

from donna.core.entities import BaseEntity
from donna.domain.ids import ArtifactId, WorldId
from donna.machine.artifacts import Artifact
from donna.machine.primitives import Primitive

if TYPE_CHECKING:
    from donna.world.config import WorldConfig


class World(BaseEntity):
    id: WorldId
    readonly: bool = True
    session: bool = False

    def has(self, artifact_id: ArtifactId) -> bool:
        raise NotImplementedError("You must implement this method in subclasses")

    def fetch(self, artifact_id: ArtifactId) -> Artifact:
        raise NotImplementedError("You must implement this method in subclasses")

    def fetch_source(self, artifact_id: ArtifactId) -> bytes:
        raise NotImplementedError("You must implement this method in subclasses")

    def update(self, artifact_id: ArtifactId, content: bytes) -> None:
        raise NotImplementedError("You must implement this method in subclasses")

    def file_extension_for(self, artifact_id: ArtifactId) -> str | None:
        if not self.has(artifact_id):
            return None

        # TODO: remove that hardcoding
        return 'md'

    def list_artifacts(self, artifact_prefix: ArtifactId) -> list[ArtifactId]:
        raise NotImplementedError("You must implement this method in subclasses")

    # These two methods are intended for storing world state (e.g., session data)
    # It is an open question if the world state is an artifact itself or something else
    # For the artifact: uniform API for storing/loading data
    # Against the artifact:
    # - session data MUST be accessible only by Donna => no one should be able to read/write/list it
    # - session data will require an additonal kind(s) of artifact(s) just for that purpose
    # - session data may change more frequently than regular artifacts

    def read_state(self, name: str) -> bytes | None:
        raise NotImplementedError("You must implement this method in subclasses")

    def write_state(self, name: str, content: bytes) -> None:
        raise NotImplementedError("You must implement this method in subclasses")

    def initialize(self, reset: bool = False) -> None:
        pass

    def is_initialized(self) -> bool:
        raise NotImplementedError("You must implement this method in subclasses")


class WorldConstructor(Primitive):
    def construct_world(self, config: WorldConfig) -> World:
        raise NotImplementedError("You must implement this method in subclasses")
