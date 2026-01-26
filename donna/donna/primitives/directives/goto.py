from typing import Any

from jinja2.runtime import Context

from donna.domain.ids import FullArtifactLocalId
from donna.machine.templates import Directive
from donna.world.templates import RenderMode


class GoTo(Directive):
    def apply_directive(self, context: Context, *argv: Any, **kwargs: Any) -> Any:
        render_mode: RenderMode = context["render_mode"]
        if argv is None or len(argv) != 1:
            raise ValueError("GoTo directive requires exactly one argument: next_operation_id")

        artifact_id = context["artifact_id"]

        next_operation_id = artifact_id.to_full_local(argv[0])

        match render_mode:
            case RenderMode.cli:
                return self.render_cli(context, next_operation_id)

            case RenderMode.analysis:
                return self.render_analyze(context, next_operation_id)

            case _:
                raise NotImplementedError(f"Render mode {render_mode} not implemented in GoTo directive.")

    def render_cli(self, context: Context, next_operation_id: FullArtifactLocalId) -> str:
        return f"donna sessions action-request-completed <action-request-id> '{next_operation_id}'"

    def render_analyze(self, context: Context, next_operation_id: FullArtifactLocalId) -> str:
        return f"$$donna {self.analyze_id} {next_operation_id} donna$$"
