from abc import ABC, abstractmethod
from typing import TYPE_CHECKING, Any

from jinja2.runtime import Context

from donna.core.errors import ErrorsList
from donna.core.result import Result
from donna.machine.primitives import Primitive

if TYPE_CHECKING:
    pass


class Directive(Primitive, ABC):
    analyze_id: str

    @abstractmethod
    def apply_directive(  # noqa: E704
        self,
        context: Context,
        *argv: Any,
        **kwargs: Any,
    ) -> Result[Any, ErrorsList]: ...
