from typing import TYPE_CHECKING, ClassVar, Iterable

from donna.core import errors as core_errors
from donna.machine.artifacts import ArtifactSection, ArtifactSectionConfig
from donna.machine.primitives import Primitive
from donna.world.sources.markdown import MarkdownSectionMixin

if TYPE_CHECKING:
    from donna.machine.changes import Change
    from donna.machine.tasks import Task, WorkUnit


class TextConfig(ArtifactSectionConfig):
    pass


class InternalError(core_errors.InternalError):
    """Base class for internal errors in donna.primitives.artifacts.specification."""


class TextSectionExecutionUnsupported(InternalError):
    message: str = "Text sections cannot be executed."


class Text(MarkdownSectionMixin, Primitive):
    config_class: ClassVar[type[TextConfig]] = TextConfig

    def execute_section(self, task: "Task", unit: "WorkUnit", operation: ArtifactSection) -> Iterable["Change"]:
        raise TextSectionExecutionUnsupported()


class Specification(MarkdownSectionMixin, Primitive):
    pass
