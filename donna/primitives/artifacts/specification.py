from typing import TYPE_CHECKING, ClassVar

import pydantic

from donna.machine.artifacts import ArtifactSectionConfig
from donna.machine.primitives import Primitive
from donna.workspaces.sources.markdown import MarkdownSectionMixin

if TYPE_CHECKING:
    pass


class TextConfig(ArtifactSectionConfig):
    pass


class Text(MarkdownSectionMixin, Primitive):
    config_class: ClassVar[type[TextConfig]] = TextConfig


class SpecificationConfig(ArtifactSectionConfig):
    @pydantic.field_validator("tags", mode="after")
    @classmethod
    def ensure_specification_tag(cls, value: list[str]) -> list[str]:
        if "specification" in value:
            return value
        return [*value, "specification"]


class Specification(MarkdownSectionMixin, Primitive):
    config_class: ClassVar[type[SpecificationConfig]] = SpecificationConfig
