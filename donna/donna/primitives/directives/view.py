from typing import Any

from jinja2.runtime import Context

from donna.core import errors as core_errors
from donna.domain import errors as domain_errors
from donna.domain.ids import FullArtifactId
from donna.machine.templates import Directive
from donna.protocol.modes import mode
from donna.world.templates import RenderMode


class InternalError(core_errors.InternalError):
    """Base class for internal errors in donna.primitives.directives.view."""


class UnsupportedRenderMode(InternalError):
    message: str = "Render mode {render_mode} not implemented in View directive."


class View(Directive):
    def apply_directive(self, context: Context, *argv: Any, **kwargs: Any) -> Any:
        render_mode: RenderMode = context["render_mode"]
        if argv is None or len(argv) != 1:
            raise ValueError("View directive requires exactly one argument: specificatin_id")

        artifact_id_result = FullArtifactId.parse(str(argv[0]))
        if artifact_id_result.is_err():
            raise domain_errors.InvalidIdPath(id_type=FullArtifactId.__name__, value=str(argv[0]))

        artifact_id = artifact_id_result.unwrap()

        match render_mode:
            case RenderMode.cli:
                return self.render_cli(context, artifact_id)

            case RenderMode.analysis:
                return self.render_analyze(context, artifact_id)

            case _:
                raise UnsupportedRenderMode(render_mode=render_mode)

    def render_cli(self, context: Context, specification_id: FullArtifactId) -> str:
        protocol = mode().value
        return f"donna -p {protocol} artifacts view '{specification_id}'"

    def render_analyze(self, context: Context, specification_id: FullArtifactId) -> str:
        return f"$$donna {self.analyze_id} {specification_id} donna$$"
