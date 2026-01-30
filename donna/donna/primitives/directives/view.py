from typing import Any

from jinja2.runtime import Context

from donna.core import errors as core_errors
from donna.core.errors import ErrorsList
from donna.core.result import Err, Ok, Result
from donna.domain.ids import FullArtifactId
from donna.machine.templates import Directive
from donna.protocol.modes import mode
from donna.world.templates import RenderMode


class EnvironmentError(core_errors.EnvironmentError):
    cell_kind: str = "directive_error"


class InternalError(core_errors.InternalError):
    """Base class for internal errors in donna.primitives.directives.view."""


class ViewInvalidArguments(EnvironmentError):
    code: str = "donna.directives.view.invalid_arguments"
    message: str = "View directive requires exactly one argument: specification_id (got {error.provided_count})."
    ways_to_fix: list[str] = ["Provide exactly one argument: specification_id."]
    provided_count: int


class ViewUnsupportedRenderMode(InternalError):
    message: str = "Render mode {render_mode} not implemented in View directive."


class View(Directive):
    def apply_directive(self, context: Context, *argv: Any, **kwargs: Any) -> Result[Any, ErrorsList]:
        render_mode: RenderMode = context["render_mode"]
        if argv is None or len(argv) != 1:
            return Err([ViewInvalidArguments(provided_count=0 if argv is None else len(argv))])

        artifact_id_result = FullArtifactId.parse(str(argv[0]))
        if artifact_id_result.is_err():
            return artifact_id_result

        artifact_id = artifact_id_result.unwrap()

        match render_mode:
            case RenderMode.view | RenderMode.execute:
                return Ok(self.render_view(context, artifact_id))

            case RenderMode.analysis:
                return Ok(self.render_analyze(context, artifact_id))

            case _:
                raise ViewUnsupportedRenderMode(render_mode=render_mode)

    def render_view(self, context: Context, specification_id: FullArtifactId) -> str:
        protocol = mode().value
        return f"donna -p {protocol} artifacts view '{specification_id}'"

    def render_analyze(self, context: Context, specification_id: FullArtifactId) -> str:
        return f"$$donna {self.analyze_id} {specification_id} donna$$"
