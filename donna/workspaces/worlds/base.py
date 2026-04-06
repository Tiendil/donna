from __future__ import annotations

from abc import ABC, abstractmethod
from typing import TYPE_CHECKING

from donna.core.entities import BaseEntity
from donna.core.errors import ErrorsList
from donna.core.result import Ok, Result
from donna.domain.artifact_ids import ArtifactId, ArtifactIdPattern
from donna.domain.ids import WorldId
from donna.domain.types import Milliseconds
from donna.machine.artifacts import Artifact

if TYPE_CHECKING:
    from donna.workspaces.artifacts import ArtifactRenderContext


class RawArtifact(BaseEntity, ABC):
    source_id: str

    @abstractmethod
    def get_bytes(self) -> bytes: ...  # noqa: E704

    @abstractmethod
    def render(self, artifact_id: ArtifactId, render_context: "ArtifactRenderContext") -> Result[Artifact, ErrorsList]:
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
    def list_artifacts(self, pattern: ArtifactIdPattern) -> list[ArtifactId]: ...  # noqa: E704

    def initialize(self, reset: bool = False) -> Result[None, ErrorsList]:
        return Ok(None)

    @abstractmethod
    def is_initialized(self) -> bool: ...  # noqa: E704
