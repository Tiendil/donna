from __future__ import annotations

from abc import ABC, abstractmethod
from typing import TYPE_CHECKING

import pydantic

from donna.core.entities import BaseEntity
from donna.core.errors import ErrorsList
from donna.core.result import Result
from donna.machine.primitives import Primitive

if TYPE_CHECKING:
    from donna.domain.artifact_ids import ArtifactId
    from donna.machine.artifacts import Artifact
    from donna.workspaces.artifacts import ArtifactRenderContext
    from donna.workspaces.config import SourceConfig as SourceConfigModel


class SourceConfig(BaseEntity, ABC):
    kind: str
    extension: str

    @classmethod
    def normalize_extension(cls, extension: str) -> str:
        normalized = str(extension).strip().lower()

        if not normalized:
            raise ValueError("Extension must not be empty")

        if not normalized.startswith("."):
            normalized = f".{normalized}"

        if normalized == ".":
            raise ValueError("Extension must include characters after '.'")

        return normalized

    @pydantic.field_validator("extension")
    @classmethod
    def _normalize_extension(cls, value: str) -> str:
        return cls.normalize_extension(value)

    def supports_extension(self, extension: str) -> bool:
        return self.normalize_extension(extension) == self.extension

    @abstractmethod
    def construct_artifact_from_bytes(  # noqa: E704
        self, artifact_id: "ArtifactId", content: bytes, render_context: "ArtifactRenderContext"
    ) -> Result["Artifact", ErrorsList]: ...  # noqa: E704


class SourceConstructor(Primitive, ABC):
    @abstractmethod
    def construct_source(self, config: SourceConfigModel) -> SourceConfig: ...  # noqa: E704
