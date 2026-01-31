from abc import ABC, abstractmethod
from typing import TYPE_CHECKING, Any, TypeAlias

from jinja2.runtime import Context

from donna.core.errors import ErrorsList
from donna.core.result import Ok, Result
from donna.machine import errors as machine_errors
from donna.machine.primitives import Primitive

if TYPE_CHECKING:
    pass

PreparedDirectiveArguments: TypeAlias = tuple[Any, ...]
PreparedDirectiveResult: TypeAlias = Result[PreparedDirectiveArguments, ErrorsList]


class DirectiveUnsupportedRenderMode(machine_errors.InternalError):
    message: str = "Render mode {render_mode} not implemented in directive {directive_name}."
    render_mode: Any
    directive_name: str


class Directive(Primitive, ABC):
    analyze_id: str

    def apply_directive(  # noqa: E704
        self,
        context: Context,
        *argv: Any,
    ) -> Result[Any, ErrorsList]:
        from donna.world import templates as world_templates

        render_mode = context["render_mode"]
        arguments_result = self._prepare_arguments(context, *argv)
        if arguments_result.is_err():
            return arguments_result

        argv = arguments_result.unwrap()

        match render_mode:
            case world_templates.RenderMode.view:
                return self.render_view(context, *argv)
            case world_templates.RenderMode.execute:
                return self.render_execute(context, *argv)
            case world_templates.RenderMode.analysis:
                return self.render_analyze(context, *argv)
            case _:
                raise DirectiveUnsupportedRenderMode(render_mode=render_mode, directive_name=self.__class__.__name__)

    def _prepare_arguments(
        self,
        context: Context,
        *argv: Any,
    ) -> PreparedDirectiveResult:
        return Ok(argv)

    @abstractmethod
    def render_view(  # noqa: E704
        self,
        context: Context,
        *argv: Any,
    ) -> Result[Any, ErrorsList]: ...

    def render_execute(
        self,
        context: Context,
        *argv: Any,
    ) -> Result[Any, ErrorsList]:
        return self.render_view(context, *argv)

    def render_analyze(
        self,
        context: Context,
        *argv: Any,
    ) -> Result[str, ErrorsList]:
        parts = [str(arg) for arg in argv]
        arguments = " ".join(parts)

        if arguments:
            return Ok(f"$$donna {self.analyze_id} {arguments} donna$$")

        return Ok(f"$$donna {self.analyze_id} donna$$")
