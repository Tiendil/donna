from __future__ import annotations

from abc import ABC, abstractmethod
from typing import TYPE_CHECKING

from donna.core.entities import BaseEntity
from donna.core.errors import ErrorsList
from donna.core.result import Ok, Result
from donna.domain.ids import ArtifactId, FullArtifactId, FullArtifactIdPattern, WorldId
from donna.domain.types import Milliseconds
from donna.machine.artifacts import Artifact
from donna.machine.primitives import Primitive

if TYPE_CHECKING:
    from donna.workspaces.artifacts import ArtifactRenderContext
    from donna.workspaces.config import WorldConfig


class RawArtifact(BaseEntity, ABC):
    source_id: str

    @abstractmethod
    def get_bytes(self) -> bytes: ...  # noqa: E704

    @abstractmethod
    def render(self, full_id: FullArtifactId, render_context: "ArtifactRenderContext") -> Result[Artifact, ErrorsList]:
        pass


class World(BaseEntity, ABC):
    id: WorldId

    @abstractmethod
    def has(self, artifact_id: ArtifactId) -> bool: ...  # noqa: E704

    @abstractmethod
    def fetch(self, artifact_id: ArtifactId) -> Result[RawArtifact, ErrorsList]: ...  # noqa: E704

    @abstractmethod
    def has_artifact_changed(self, artifact_id: ArtifactId, since: Milliseconds) -> Result[bool, ErrorsList]:
        pass

    @abstractmethod
    def list_artifacts(self, pattern: FullArtifactIdPattern) -> list[ArtifactId]: ...  # noqa: E704

    def initialize(self, reset: bool = False) -> Result[None, ErrorsList]:
        return Ok(None)

    @abstractmethod
    def is_initialized(self) -> bool: ...  # noqa: E704


class WorldConstructor(Primitive, ABC):
    @abstractmethod
    def construct_world(self, config: WorldConfig) -> World: ...  # noqa: E704
