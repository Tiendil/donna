from __future__ import annotations

from abc import ABC, abstractmethod
from typing import TYPE_CHECKING

import pydantic

from donna.core.entities import BaseEntity
from donna.core.errors import ErrorsList
from donna.core.result import Result
from donna.machine.primitives import Primitive

if TYPE_CHECKING:
    from donna.domain.ids import FullArtifactId
    from donna.machine.artifacts import Artifact
    from donna.world.config import SourceConfig as SourceConfigModel


class SourceConfig(BaseEntity, ABC):
    kind: str
    supported_extensions: list[str] = pydantic.Field(default_factory=list)

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

    @pydantic.field_validator("supported_extensions")
    @classmethod
    def _normalize_supported_extensions(cls, values: list[str]) -> list[str]:
        normalized: list[str] = []

        for value in values:
            extension = cls.normalize_extension(value)
            if extension not in normalized:
                normalized.append(extension)

        return normalized

    def supports_extension(self, extension: str) -> bool:
        return self.normalize_extension(extension) in self.supported_extensions

    @abstractmethod
    def construct_artifact_from_bytes(  # noqa: E704
        self, full_id: "FullArtifactId", content: bytes
    ) -> Result["Artifact", ErrorsList]: ...  # noqa: E704


class SourceConstructor(Primitive, ABC):
    @abstractmethod
    def construct_source(self, config: SourceConfigModel) -> SourceConfig: ...  # noqa: E704
