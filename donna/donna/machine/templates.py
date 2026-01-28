from abc import ABC, abstractmethod
from typing import TYPE_CHECKING, Any, Iterable

from jinja2.runtime import Context

from donna.machine import errors as machine_errors
from donna.machine.primitives import Primitive

if TYPE_CHECKING:
    from donna.machine.artifacts import ArtifactSection
    from donna.machine.changes import Change
    from donna.machine.tasks import Task, WorkUnit


class Directive(Primitive, ABC):
    analyze_id: str

    @abstractmethod
    def apply_directive(self, context: Context, *argv: Any, **kwargs: Any) -> Any: ...  # noqa: E704
