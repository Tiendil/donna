import enum
from abc import ABC, abstractmethod
from typing import TYPE_CHECKING, ClassVar, TypeAlias

from llm_tool_cli.core.errors import EnvironmentErrors
from llm_tool_cli.core.result import Ok, Result

from donna.machine import errors as machine_errors
from donna.machine.primitives import Primitive
from donna.machine.templates_context import DirectiveContext

if TYPE_CHECKING:
    pass

PreparedDirectiveArguments: TypeAlias = tuple[object, ...]
PreparedDirectiveResult: TypeAlias = Result[PreparedDirectiveArguments, EnvironmentErrors]


class RenderMode(enum.StrEnum):
    """Modes for rendering artifacts.

    Donna can render artifacts for different purposes, for example:

    - to be displayed to the agent when Donna is used via CLI.
    - to be used for execution by Donna itself.
    - to be used for analysis by Donna itself.

    In each mode Donna can produce different outputs.

    For example, it can output CLI commands in view/execute mode,
    tool specifications in tool mode, special markup in analyze mode, etc.
    """

    view = "view"
    execute = "execute"
    analysis = "analysis"


class DirectiveUnsupportedRenderMode(machine_errors.InternalError):
    message_template: ClassVar[str] = "Render mode {render_mode} not implemented in directive {directive_name}."


class Directive(Primitive, ABC):
    analyze_id: str

    def apply_directive(  # noqa: E704
        self,
        context: DirectiveContext,
        *argv: object,
        **kwargs: object,
    ) -> Result[object, EnvironmentErrors]:
        render_mode = context["render_mode"]
        arguments_result = self._prepare_arguments(context, *argv, **kwargs)
        if arguments_result.is_err():
            return arguments_result

        argv = arguments_result.unwrap()

        match render_mode:
            case RenderMode.view:
                return self.render_view(context, *argv)
            case RenderMode.execute:
                return self.render_execute(context, *argv)
            case RenderMode.analysis:
                return self.render_analyze(context, *argv)
            case _:
                raise DirectiveUnsupportedRenderMode(
                    details={"render_mode": render_mode, "directive_name": self.__class__.__name__}
                )

    def _prepare_arguments(
        self,
        context: DirectiveContext,
        *argv: object,
        **kwargs: object,
    ) -> PreparedDirectiveResult:
        return Ok(argv)

    @abstractmethod
    def render_view(  # noqa: E704
        self,
        context: DirectiveContext,
        *argv: object,
    ) -> Result[object, EnvironmentErrors]: ...

    def render_execute(
        self,
        context: DirectiveContext,
        *argv: object,
    ) -> Result[object, EnvironmentErrors]:
        return self.render_view(context, *argv)

    def render_analyze(
        self,
        context: DirectiveContext,
        *argv: object,
    ) -> Result[object, EnvironmentErrors]:
        parts = [str(arg) for arg in argv]
        arguments = " ".join(parts)

        if arguments:
            return Ok(f"$$donna {self.analyze_id} {arguments} donna$$")

        return Ok(f"$$donna {self.analyze_id} donna$$")
