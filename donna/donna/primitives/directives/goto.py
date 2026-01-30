from typing import Any

from jinja2.runtime import Context

from donna.core import errors as core_errors
from donna.core.errors import ErrorsList
from donna.core.result import Err, Ok, Result
from donna.domain.ids import FullArtifactSectionId
from donna.machine.templates import Directive
from donna.protocol.modes import mode
from donna.world.templates import RenderMode


class EnvironmentError(core_errors.EnvironmentError):
    cell_kind: str = "directive_error"


class InternalError(core_errors.InternalError):
    """Base class for internal errors in donna.primitives.directives.goto."""


class GoToInvalidArguments(EnvironmentError):
    code: str = "donna.directives.goto.invalid_arguments"
    message: str = "GoTo directive requires exactly one argument: next_operation_id (got {error.provided_count})."
    ways_to_fix: list[str] = ["Provide exactly one argument: next_operation_id."]
    provided_count: int


class GoToUnsupportedRenderMode(InternalError):
    message: str = "Render mode {render_mode} not implemented in GoTo directive."


class GoTo(Directive):
    def apply_directive(self, context: Context, *argv: Any, **kwargs: Any) -> Result[Any, ErrorsList]:
        render_mode: RenderMode = context["render_mode"]
        if argv is None or len(argv) != 1:
            return Err([GoToInvalidArguments(provided_count=0 if argv is None else len(argv))])

        artifact_id = context["artifact_id"]

        next_operation_id = artifact_id.to_full_local(argv[0])

        match render_mode:
            case RenderMode.view | RenderMode.execute:
                return Ok(self.render_view(context, next_operation_id))

            case RenderMode.analysis:
                return Ok(self.render_analyze(context, next_operation_id))

            case _:
                raise GoToUnsupportedRenderMode(render_mode=render_mode)

    def render_view(self, context: Context, next_operation_id: FullArtifactSectionId) -> str:
        protocol = mode().value
        return f"donna -p {protocol} sessions action-request-completed <action-request-id> '{next_operation_id}'"

    def render_analyze(self, context: Context, next_operation_id: FullArtifactSectionId) -> str:
        return f"$$donna {self.analyze_id} {next_operation_id.local_id} donna$$"
