from typing import ClassVar

from donna.machine.artifacts import ArtifactSectionConfig
from donna.machine.primitives import Primitive
from donna.workspaces.markdown_parser import MarkdownSectionMixin


class TextConfig(ArtifactSectionConfig):
    pass


class Text(MarkdownSectionMixin, Primitive):
    config_class: ClassVar[type[TextConfig]] = TextConfig
