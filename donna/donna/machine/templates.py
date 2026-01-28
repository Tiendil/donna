from abc import ABC, abstractmethod
from typing import TYPE_CHECKING, Any

from jinja2.runtime import Context

from donna.machine.primitives import Primitive

if TYPE_CHECKING:
    pass


class Directive(Primitive, ABC):
    analyze_id: str

    @abstractmethod
    def apply_directive(self, context: Context, *argv: Any, **kwargs: Any) -> Any: ...  # noqa: E704
