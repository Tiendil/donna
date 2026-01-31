from typing import TYPE_CHECKING, ClassVar

from donna.machine.artifacts import ArtifactSectionConfig
from donna.machine.primitives import Primitive
from donna.workspaces.sources.markdown import MarkdownSectionMixin

if TYPE_CHECKING:
    pass


class TextConfig(ArtifactSectionConfig):
    pass


class Text(MarkdownSectionMixin, Primitive):
    config_class: ClassVar[type[TextConfig]] = TextConfig


class Specification(MarkdownSectionMixin, Primitive):
    pass
