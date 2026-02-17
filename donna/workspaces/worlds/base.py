from __future__ import annotations

from abc import ABC, abstractmethod
from collections.abc import Iterable
from typing import TYPE_CHECKING

from donna.core.entities import BaseEntity
from donna.core.errors import ErrorsList
from donna.core.result import Result
from donna.domain.ids import ArtifactId, FullArtifactIdPattern, WorldId
from donna.machine.artifacts import Artifact
from donna.machine.primitives import Primitive

if TYPE_CHECKING:
    from donna.workspaces.artifacts import ArtifactRenderContext
    from donna.workspaces.config import WorldConfig


class World(BaseEntity, ABC):
    id: WorldId
    readonly: bool = True
    session: bool = False

    @abstractmethod
    def has(self, artifact_id: ArtifactId) -> bool: ...  # noqa: E704

    @abstractmethod
    def fetch(  # noqa: E704
        self, artifact_id: ArtifactId, render_context: "ArtifactRenderContext"
    ) -> Result[Artifact, ErrorsList]: ...

    @abstractmethod
    def fetch_source(self, artifact_id: ArtifactId) -> Result[bytes, ErrorsList]: ...  # noqa: E704

    @abstractmethod
    def update(  # noqa: E704
        self, artifact_id: ArtifactId, content: bytes, extension: str
    ) -> Result[None, ErrorsList]: ...  # noqa: E704

    @abstractmethod
    def remove(self, artifact_id: ArtifactId) -> Result[None, ErrorsList]: ...  # noqa: E704

    @abstractmethod
    def file_extension_for(self, artifact_id: ArtifactId) -> Result[str, ErrorsList]: ...  # noqa: E704

    @abstractmethod
    def list_artifacts(self, pattern: FullArtifactIdPattern) -> list[ArtifactId]: ...  # noqa: E704

    # These two methods are intended for storing world state (e.g., session data)
    # It is an open question if the world state is an artifact itself or something else
    # For the artifact: uniform API for storing/loading data
    # Against the artifact:
    # - session data MUST be accessible only by Donna => no one should be able to read/write/list it
    # - session data will require an additional kind(s) of artifact(s) just for that purpose
    # - session data may change more frequently than regular artifacts

    @abstractmethod
    def read_state(self, name: str) -> Result[bytes | None, ErrorsList]: ...  # noqa: E704

    @abstractmethod
    def write_state(self, name: str, content: bytes) -> Result[None, ErrorsList]: ...  # noqa: E704

    @abstractmethod
    def journal_reset(self) -> Result[None, ErrorsList]: ...  # noqa: E704

    @abstractmethod
    def journal_add(self, content: bytes) -> Result[None, ErrorsList]: ...  # noqa: E704

    @abstractmethod
    def journal_read(self, lines: int | None = None, follow: bool = False) -> Iterable[Result[bytes, ErrorsList]]:
        pass

    def initialize(self, reset: bool = False) -> None:
        pass

    @abstractmethod
    def is_initialized(self) -> bool: ...  # noqa: E704


class WorldConstructor(Primitive, ABC):
    @abstractmethod
    def construct_world(self, config: WorldConfig) -> World: ...  # noqa: E704
