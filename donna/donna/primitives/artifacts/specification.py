from typing import TYPE_CHECKING, ClassVar, Iterable

from donna.machine.artifacts import ArtifactSection, ArtifactSectionConfig
from donna.machine.primitives import Primitive
from donna.world.sources.markdown import MarkdownSectionMixin

if TYPE_CHECKING:
    from donna.machine.changes import Change
    from donna.machine.tasks import Task, WorkUnit


class TextConfig(ArtifactSectionConfig):
    pass


class Text(MarkdownSectionMixin, Primitive):
    config_class: ClassVar[type[TextConfig]] = TextConfig

    def execute_section(self, task: "Task", unit: "WorkUnit", operation: ArtifactSection) -> Iterable["Change"]:
        raise NotImplementedError("Text sections cannot be executed.")


class Specification(MarkdownSectionMixin, Primitive):
    pass
